from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import get_transactions_router
from app.api.websocket import CommandType, ConnectionManager, WebSocketMessageParser
from app.core.config import load_config, load_secrets
from app.core.events import Event, EventType
from app.core.exceptions import EmergencyStop, HopperEmpty, HopperError, PaymentError, PaymentTimeout
from app.core.state_machine import StateMachine
from app.database.sqlite import Database
from app.drivers.hopper.moneycontrols import MoneyControlsHopper
from app.drivers.hopper.simulator import SimulatorHopper
from app.drivers.payment.simulator import SimulatorPayment
from app.drivers.payment.sumup import SumUpPayment
from app.services.hopper_service import HopperService
from app.services.payment_service import PaymentService
from app.services.transaction_service import TransactionService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("muntautomaat")

config = load_config()
secrets = load_secrets()

database = Database(config.database_path)
transaction_service = TransactionService(database)

payment_driver = (
    SimulatorPayment(
        payment_mode=config.simulation.payment.mode,
        delay_ms=config.simulation.payment.delay_ms,
    )
    if config.use_simulator and config.simulation.enabled
    else SumUpPayment(secrets, config.sumup_api_base, config.sumup_currency)
)
hopper_driver = (
    SimulatorHopper(
        speed=config.simulation.hopper.speed,
        capacity=config.simulation.hopper.capacity,
        start_amount=config.simulation.hopper.start_amount,
        jam_probability=config.simulation.hopper.jam_probability,
        random_failures=config.simulation.hopper.random_failures,
    )
    if config.use_simulator and config.simulation.enabled
    else MoneyControlsHopper(port="/dev/ttyUSB0")
)

payment_service = PaymentService(payment_driver)
hopper_service = HopperService(hopper_driver)

state_machine = StateMachine()
manager = ConnectionManager()
flow_task: asyncio.Task[None] | None = None

app = FastAPI(title="SumUp Muntenautomaat Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(get_transactions_router(transaction_service))


@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting services")
    await payment_service.connect()
    await hopper_service.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("Stopping services")
    await stop_active_flow(reset_machine=False)
    await payment_service.disconnect()
    await hopper_service.disconnect()


async def broadcast(event: Event) -> None:
    logger.info("Event %s %s", event.type.value, event.payload or {})
    await manager.broadcast(event)


async def broadcast_state() -> None:
    await broadcast(state_machine.state_event())


async def broadcast_inventory() -> int | None:
    status = await hopper_service.get_status()
    inventory = status.get("inventory")
    capacity = status.get("capacity")
    await broadcast(
        Event(
            EventType.INVENTORY_CHANGED,
            {
                "inventory": inventory,
                "capacity": capacity,
            },
        )
    )
    return int(inventory) if inventory is not None else None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await broadcast_state()
    await broadcast_inventory()

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                await handle_command(raw)
            except Exception as exc:
                logger.exception("Command failed")
                await stop_active_flow(reset_machine=False)
                await recover_to_idle(str(exc))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_command(raw: Any) -> None:
    global flow_task

    message = WebSocketMessageParser.parse(raw)
    payload = message.payload or {}
    command = CommandType(message.type)
    logger.info("Command %s %s", command.value, payload)

    if command is CommandType.SELECT_AMOUNT:
        amount = int(payload.get("amount", 0))
        inventory = await hopper_service.get_inventory()
        state_machine.select_amount(amount, config.price_per_coin, inventory)
        await broadcast_state()
        return

    if command is CommandType.CONFIRM_SELECTION:
        inventory = await hopper_service.get_inventory()
        state_machine.confirm_selection(inventory)
        await broadcast_state()
        return

    if command is CommandType.START_PAYMENT:
        if flow_task and not flow_task.done():
            raise RuntimeError("Purchase flow already running")
        state_machine.start_payment()
        await broadcast_state()
        flow_task = asyncio.create_task(process_purchase_flow())
        return

    if command is CommandType.CANCEL_PAYMENT:
        await cancel_current_payment()
        return

    if command is CommandType.RESET_MACHINE:
        await stop_active_flow(reset_machine=True)
        return

    raise RuntimeError(f"Unhandled command: {command.value}")


async def process_purchase_flow() -> None:
    global flow_task

    transaction_id: str | None = None
    try:
        logger.info("Starting payment for %s tokens", state_machine.context.amount)
        result = await payment_service.start_payment(state_machine.context.amount)
        transaction_id = result["transaction_id"]
        await broadcast(
            Event(
                EventType.PAYMENT_STARTED,
                {
                    "transaction_id": transaction_id,
                    "amount": state_machine.context.amount,
                    "price": state_machine.context.price,
                },
            )
        )

        status_payload = await payment_service.wait_for_authorization(
            transaction_id,
            timeout_seconds=30,
        )
        status = status_payload["status"].lower()
        if status != "authorized":
            raise PaymentError(f"Payment not authorized: {status}")

        state_machine.payment_succeeded(transaction_id)
        transaction_service.record_transaction(
            amount=state_machine.context.amount,
            price=state_machine.context.price,
            status=status,
            transaction_id=transaction_id,
            raw_payload=status_payload,
        )
        await broadcast(Event(EventType.PAYMENT_SUCCEEDED, {"transaction_id": transaction_id}))
        await broadcast_state()

        state_machine.start_dispensing()
        await broadcast(
            Event(
                EventType.DISPENSING_STARTED,
                {"amount": state_machine.context.amount},
            )
        )
        await broadcast_state()
        await dispense_tokens()

        inventory = await hopper_service.get_inventory()
        state_machine.dispensing_finished(inventory or 0)
        await broadcast(
            Event(
                EventType.DISPENSING_FINISHED,
                {
                    "amount": state_machine.context.amount,
                    "inventory": inventory,
                },
            )
        )
        if inventory == 0:
            await broadcast(Event(EventType.HOPPER_EMPTY, {"inventory": 0}))
        await broadcast_state()
        await asyncio.sleep(5)
        await reset_machine("completed")
    except asyncio.CancelledError:
        logger.info("Purchase flow cancelled")
        raise
    except PaymentTimeout as exc:
        if transaction_id:
            with suppress(PaymentError):
                await payment_service.cancel_payment(transaction_id)
            record_failed_transaction(transaction_id, "timeout")
        await broadcast(Event(EventType.PAYMENT_FAILED, {"message": str(exc)}))
        await recover_to_idle(str(exc))
    except PaymentError as exc:
        if transaction_id:
            with suppress(PaymentError):
                await payment_service.cancel_payment(transaction_id)
            record_failed_transaction(transaction_id, "failed")
        await broadcast(Event(EventType.PAYMENT_FAILED, {"message": str(exc)}))
        await recover_to_idle(str(exc))
    except HopperEmpty as exc:
        await broadcast(Event(EventType.HOPPER_EMPTY, {"message": str(exc)}))
        await recover_to_idle(str(exc))
    except EmergencyStop as exc:
        await recover_to_idle(str(exc))
    except HopperError as exc:
        await recover_to_idle(str(exc))
    except Exception as exc:
        logger.exception("Unexpected purchase flow failure")
        await recover_to_idle("Unexpected internal error")
    finally:
        hopper_service.set_progress_callback(None)
        flow_task = None


async def dispense_tokens() -> None:
    async def on_progress(current: int, total: int, inventory: int) -> None:
        state_machine.dispensing_progress(current, total, inventory)
        await broadcast(
            Event(
                EventType.DISPENSING_PROGRESS,
                {
                    "current": current,
                    "total": total,
                    "inventory": inventory,
                },
            )
        )
        await broadcast(
            Event(
                EventType.INVENTORY_CHANGED,
                {
                    "inventory": inventory,
                    "capacity": getattr(hopper_driver, "capacity", None),
                },
            )
        )
        if inventory == 0:
            await broadcast(Event(EventType.HOPPER_EMPTY, {"inventory": 0}))

    hopper_service.set_progress_callback(on_progress)
    await hopper_service.dispense(state_machine.context.amount)


async def cancel_current_payment() -> None:
    await stop_active_flow(reset_machine=False)
    transaction_id = state_machine.context.transaction_id
    if transaction_id:
        with suppress(PaymentError):
            await payment_service.cancel_payment(transaction_id)
    await broadcast(Event(EventType.PAYMENT_CANCELLED, {"transaction_id": transaction_id}))
    await recover_to_idle("Payment cancelled")


async def stop_active_flow(reset_machine: bool) -> None:
    global flow_task

    if flow_task and not flow_task.done():
        logger.info("Stopping active flow")
        await hopper_service.stop()
        flow_task.cancel()
        with suppress(asyncio.CancelledError):
            await flow_task
    flow_task = None

    if reset_machine:
        await reset_machine_state("manual reset")


async def recover_to_idle(message: str) -> None:
    logger.info("Recovering to idle: %s", message)
    state_machine.fail(message)
    await broadcast(Event(EventType.ERROR_OCCURRED, {"message": message}))
    await broadcast_state()
    await asyncio.sleep(1)
    await reset_machine_state("recovery")


async def reset_machine(reason: str) -> None:
    await reset_machine_state(reason)


async def reset_machine_state(reason: str) -> None:
    inventory = await hopper_service.get_inventory()
    state_machine.reset_machine(inventory)
    await broadcast(Event(EventType.MACHINE_RESET, {"reason": reason}))
    await broadcast_state()
    await broadcast_inventory()


def record_failed_transaction(transaction_id: str, status: str) -> None:
    with suppress(Exception):
        transaction_service.record_transaction(
            amount=state_machine.context.amount,
            price=state_machine.context.price,
            status=status,
            transaction_id=transaction_id,
            raw_payload={"status": status},
        )
