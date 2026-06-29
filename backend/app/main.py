from __future__ import annotations
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import get_transactions_router
from app.api.websocket import ConnectionManager, WebSocketMessageParser
from app.core.config import load_config, load_secrets
from app.core.events import EventType, Event
from app.core.state_machine import StateMachine
from app.core.exceptions import PaymentError, PaymentTimeout, HopperError
from app.database.sqlite import Database
from app.drivers.hopper.moneycontrols import MoneyControlsHopper
from app.drivers.hopper.simulator import SimulatorHopper
from app.drivers.payment.simulator import SimulatorPayment
from app.drivers.payment.sumup import SumUpPayment
from app.services.hopper_service import HopperService
from app.services.payment_service import PaymentService
from app.services.transaction_service import TransactionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("muntautomaat")

config = load_config()
secrets = load_secrets()

database = Database(config.database_path)
transaction_service = TransactionService(database)

payment_driver = SimulatorPayment() if config.use_simulator else SumUpPayment(secrets, config.sumup_api_base, config.sumup_currency)
hopper_driver = SimulatorHopper() if config.use_simulator else MoneyControlsHopper(port="/dev/ttyUSB0")

payment_service = PaymentService(payment_driver)
hopper_service = HopperService(hopper_driver)

state_machine = StateMachine()
manager = ConnectionManager()

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
    await payment_service.connect()
    await hopper_service.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await payment_service.disconnect()
    await hopper_service.disconnect()


def format_state_event() -> Event:
    return Event(
        EventType.STATE_CHANGED,
        {
            "state": state_machine.state.value,
            "amount": state_machine.context.amount,
            "price": state_machine.context.price,
            "transaction_id": state_machine.context.transaction_id,
            "error": state_machine.context.error,
        },
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await websocket.send_json(format_state_event().to_dict())

    try:
        while True:
            raw = await websocket.receive_json()
            message = WebSocketMessageParser.parse(raw)
            message_type = message.get("type")
            payload = message.get("payload", {})

            if message_type == "select_amount":
                amount = int(payload.get("amount", 0))
                state_machine.select_amount(amount, config.price_per_coin)
                await manager.broadcast(format_state_event())
            elif message_type == "start_payment":
                state_machine.awaiting_payment()
                await manager.broadcast(format_state_event())
                await process_payment_flow()
            elif message_type == "cancel_payment":
                transaction_id = payload.get("transaction_id")
                if transaction_id:
                    await cancel_payment(transaction_id)
                else:
                    await websocket.send_json({"type": "error", "payload": {"message": "transaction_id is required to cancel payment"}})
            elif message_type == "reset":
                state_machine.reset()
                await manager.broadcast(format_state_event())
            else:
                await websocket.send_json({"type": "error", "payload": {"message": "Unknown message type"}})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def process_payment_flow() -> None:
    try:
        result = await payment_service.start_payment(state_machine.context.amount)
        transaction_id = result["transaction_id"]
        state_machine.payment_authorized(transaction_id)
        await manager.broadcast(Event(EventType.PAYMENT_STARTED, {"transaction_id": transaction_id}))

        status = str(result.get("status", "pending")).lower()
        if status != "authorized":
            status_payload = await payment_service.wait_for_authorization(transaction_id, timeout_seconds=30)
            status = status_payload["status"].lower()

        transaction_service.record_transaction(
            amount=state_machine.context.amount,
            price=state_machine.context.price,
            status=status,
            transaction_id=transaction_id,
            raw_payload=result,
        )
        await manager.broadcast(format_state_event())

        if status != "authorized":
            raise PaymentError(f"Payment not authorized: {status}")

        state_machine.dispense()
        await manager.broadcast(Event(EventType.HOPPER_STARTED, {"amount": state_machine.context.amount}))
        await hopper_service.dispense(state_machine.context.amount)
        state_machine.complete()
        await manager.broadcast(Event(EventType.HOPPER_COMPLETED, {"amount": state_machine.context.amount}))
        await manager.broadcast(format_state_event())
    except PaymentTimeout as exc:
        logger.exception("Payment timeout")
        if state_machine.context.transaction_id:
            await payment_service.cancel_payment(state_machine.context.transaction_id)
        state_machine.fail(str(exc))
        await manager.broadcast(Event(EventType.ERROR, {"message": str(exc)}))
        await manager.broadcast(format_state_event())
    except (PaymentError, HopperError) as exc:
        logger.exception("Flow failed")
        if state_machine.context.transaction_id:
            await payment_service.cancel_payment(state_machine.context.transaction_id)
        state_machine.fail(str(exc))
        await manager.broadcast(Event(EventType.ERROR, {"message": str(exc)}))
        await manager.broadcast(format_state_event())
    except Exception as exc:
        logger.exception("Unexpected error")
        if state_machine.context.transaction_id:
            await payment_service.cancel_payment(state_machine.context.transaction_id)
        state_machine.fail("Unexpected error")
        await manager.broadcast(Event(EventType.ERROR, {"message": "Unexpected internal error"}))
        await manager.broadcast(format_state_event())


async def cancel_payment(transaction_id: str) -> None:
    try:
        await payment_service.cancel_payment(transaction_id)
        state_machine.fail("Payment cancelled")
        await manager.broadcast(Event(EventType.ERROR, {"message": "Payment cancelled"}))
        await manager.broadcast(format_state_event())
    except PaymentError as exc:
        logger.exception("Cancel payment failed")
        await manager.broadcast(Event(EventType.ERROR, {"message": str(exc)}))
