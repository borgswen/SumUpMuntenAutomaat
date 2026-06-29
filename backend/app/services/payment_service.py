from __future__ import annotations
import asyncio
from typing import Any

from app.core.exceptions import PaymentError, PaymentTimeout
from app.drivers.payment.base import PaymentDriver


class PaymentService:
    def __init__(self, driver: PaymentDriver) -> None:
        self.driver = driver

    async def connect(self) -> None:
        await self.driver.connect()

    async def disconnect(self) -> None:
        await self.driver.disconnect()

    async def start_payment(self, amount: int) -> dict[str, Any]:
        try:
            payment = await self.driver.start_payment(amount)
            return payment
        except Exception as exc:
            raise PaymentError(str(exc)) from exc

    async def cancel_payment(self, transaction_id: str) -> None:
        try:
            await self.driver.cancel_payment(transaction_id)
        except Exception as exc:
            raise PaymentError(str(exc)) from exc

    async def get_status(self, transaction_id: str) -> dict[str, str]:
        try:
            return await self.driver.get_status(transaction_id)
        except Exception as exc:
            raise PaymentError(str(exc)) from exc

    async def wait_for_authorization(self, transaction_id: str, timeout_seconds: int = 30) -> dict[str, str]:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            status = await self.get_status(transaction_id)
            if status["status"].lower() == "authorized":
                return status
            if status["status"].lower() in {"failed", "expired", "cancelled", "canceled"}:
                raise PaymentError(f"Payment failed with status {status['status']}")
            await asyncio.sleep(1.0)
        raise PaymentTimeout("Payment did not authorize before timeout")
