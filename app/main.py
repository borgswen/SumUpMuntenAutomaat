from __future__ import annotations
import asyncio
import logging
import os
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import PRICE_PER_COIN, USE_SIMULATOR
from app.database import Database
from app.hopper_driver import HopperDriver
from app.state_machine import StateMachine, State
from app.simulator import Simulator
from app.sumup_driver import SumUpDriver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("muntautomaat")

app = FastAPI(title="SumUp Muntenautomaat Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager: list[WebSocket] = []
state_machine = StateMachine()
database = Database()

sumup_driver = Simulator() if USE_SIMULATOR else SumUpDriver()
hopper_driver = HopperDriver()


async def broadcast(message: dict[str, Any]) -> None:
    if not manager:
        return
    alive: list[WebSocket] = []
    for connection in manager:
        try:
            await connection.send_json(message)
            alive.append(connection)
        except RuntimeError:
            continue
    manager.clear()
    manager.extend(alive)


def format_state_payload() -> dict[str, Any]:
    return {
        "type": "state",
        "payload": {
            "state": state_machine.state,
            "amount": state_machine.context.amount,
            "price": state_machine.context.price,
            "transaction_id": state_machine.context.transaction_id,
            "error": state_machine.context.error,
        },
    }


async def run_payment_flow() -> None:
    try:
        if state_machine.state != State.AWAITING_PAYMENT:
            raise RuntimeError("Payment flow started in wrong state")

        await broadcast({"type": "status", "payload": {"message": "Start betaling..."}})
        payment = await sumup_driver.start_payment(state_machine.context.amount)
        transaction_id = payment.get("transaction_id")
        checkout_url = payment.get("checkout_url")
        status = str(payment.get("status", "pending")).lower()

        if checkout_url:
            await broadcast({"type": "status", "payload": {"message": "Open de betaling op de terminal..."}})
            await broadcast({"type": "checkout_url", "payload": {"url": checkout_url}})

        if not transaction_id:
            raise RuntimeError("Geen transactie-id ontvangen van SumUp")

        if status != "authorized":
            await broadcast({"type": "status", "payload": {"message": "Wachten op betaling..."}})
            for attempt in range(12):
                await asyncio.sleep(2)
                check = await sumup_driver.check_payment(transaction_id)
                current_status = str(check.get("status", "pending")).lower()
                await broadcast({"type": "status", "payload": {"message": f"Betaling status: {current_status}"}})
                if current_status == "authorized":
                    status = current_status
                    break
                if current_status in {"failed", "expired", "canceled", "cancelled"}:
                    raise RuntimeError(f"Betaling mislukt: {current_status}")

        if status != "authorized":
            raise RuntimeError(f"Betaling kon niet worden voltooid: {status}")

        state_machine.payment_authorized(transaction_id)
        database.add_payment(
            amount=state_machine.context.amount,
            price=state_machine.context.price,
            status="authorized",
            transaction_id=transaction_id,
        )
        await broadcast({"type": "payment_authorized", "payload": {"transaction_id": transaction_id}})

        state_machine.dispense()
        await broadcast({"type": "dispense_started", "payload": {"amount": state_machine.context.amount}})

        def progress_callback(current: int, total: int) -> None:
            asyncio.create_task(
                broadcast({
                    "type": "dispense_progress",
                    "payload": {"current": current, "total": total},
                })
            )

        await hopper_driver.dispense(state_machine.context.amount, progress_callback)
        state_machine.complete()
        await broadcast({"type": "dispense_complete", "payload": {"amount": state_machine.context.amount}})
        await broadcast(format_state_payload())
    except Exception as exc:
        logger.exception("Payment flow failed")
        state_machine.fail(str(exc))
        await broadcast({"type": "error", "payload": {"message": str(exc)}})
        await broadcast(format_state_payload())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    manager.append(websocket)
    logger.info("Client connected")
    await websocket.send_json(format_state_payload())

    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            payload = message.get("payload", {})

            if message_type == "select_amount":
                amount = int(payload.get("amount", 0))
                state_machine.select_amount(amount, PRICE_PER_COIN)
                await broadcast(format_state_payload())
            elif message_type == "start_payment":
                state_machine.awaiting_payment()
                await broadcast(format_state_payload())
                asyncio.create_task(run_payment_flow())
            elif message_type == "reset":
                state_machine.reset()
                await broadcast(format_state_payload())
            else:
                await websocket.send_json({"type": "error", "payload": {"message": "Onbekend berichttype"}})
    except WebSocketDisconnect:
        manager.remove(websocket)
        logger.info("Client disconnected")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

