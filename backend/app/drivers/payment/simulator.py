from __future__ import annotations
import asyncio
from typing import Any

from app.drivers.payment.base import PaymentDriver
from app.core.exceptions import PaymentError


class SimulatorPayment(PaymentDriver):
    def __init__(self) -> None:
        self.connected = False
        self.transactions: dict[str, str] = {}

    async def connect(self) -> None:
        await asyncio.sleep(0.1)
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def start_payment(self, amount: int) -> dict[str, str]:
        if not self.connected:
            raise PaymentError("Simulator payment driver is not connected")
        transaction_id = f"sim-{amount}-{int(asyncio.get_running_loop().time())}"
        self.transactions[transaction_id] = "pending"
        await asyncio.sleep(0.5)
        self.transactions[transaction_id] = "authorized"
        return {"transaction_id": transaction_id, "status": "authorized"}

    async def cancel_payment(self, transaction_id: str) -> None:
        if transaction_id not in self.transactions:
            raise PaymentError("Transaction not found")
        self.transactions[transaction_id] = "cancelled"

    async def get_status(self, transaction_id: str) -> dict[str, str]:
        if transaction_id not in self.transactions:
            raise PaymentError("Transaction not found")
        return {"transaction_id": transaction_id, "status": self.transactions[transaction_id]}
