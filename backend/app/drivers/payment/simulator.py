from __future__ import annotations
import asyncio
import time
from typing import Any

from app.drivers.payment.base import PaymentDriver
from app.core.exceptions import PaymentError


class SimulatorPayment(PaymentDriver):
    def __init__(self, payment_mode: str = "success", delay_ms: int = 2500) -> None:
        self.connected = False
        self.transactions: dict[str, dict[str, Any]] = {}
        self.payment_mode = payment_mode
        self.delay_ms = delay_ms

    async def connect(self) -> None:
        await asyncio.sleep(0.1)
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def start_payment(self, amount: int) -> dict[str, str]:
        if not self.connected:
            raise PaymentError("Simulator payment driver is not connected")

        transaction_id = f"sim-{amount}-{int(time.time() * 1000)}"
        self.transactions[transaction_id] = {
            "status": "pending",
            "created_at": time.monotonic(),
            "amount": amount,
        }

        if self.payment_mode == "network_error":
            raise PaymentError("Simulated network error")

        return {"transaction_id": transaction_id, "status": "pending"}

    async def cancel_payment(self, transaction_id: str) -> None:
        if transaction_id not in self.transactions:
            raise PaymentError("Transaction not found")
        self.transactions[transaction_id]["status"] = "cancelled"

    async def get_status(self, transaction_id: str) -> dict[str, str]:
        if transaction_id not in self.transactions:
            raise PaymentError("Transaction not found")

        transaction = self.transactions[transaction_id]
        status = transaction["status"]

        if status == "pending" and transaction["amount"] >= 0:
            elapsed = time.monotonic() - transaction["created_at"]
            delay_seconds = self.delay_ms / 1000
            if self.payment_mode == "success" and elapsed >= delay_seconds:
                status = "authorized"
                transaction["status"] = status
            elif self.payment_mode == "reject" and elapsed >= delay_seconds:
                status = "failed"
                transaction["status"] = status
            elif self.payment_mode == "timeout":
                if elapsed >= (self.delay_ms / 1000):
                    status = "expired"
                    transaction["status"] = status
            elif self.payment_mode == "cancel":
                status = "pending"
            elif self.payment_mode == "network_error":
                raise PaymentError("Simulated network error")

        return {"transaction_id": transaction_id, "status": status}
