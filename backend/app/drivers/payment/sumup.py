from __future__ import annotations
import time
from typing import Any

import httpx

from app.core.exceptions import PaymentError, PaymentTimeout
from app.core.config import SecretConfig
from app.drivers.payment.base import PaymentDriver


class SumUpPayment(PaymentDriver):
    def __init__(self, secret_config: SecretConfig, api_base: str, currency: str) -> None:
        if not secret_config.sumup_client_id or not secret_config.sumup_client_secret or not secret_config.sumup_refresh_token:
            raise PaymentError("SumUp credentials are required")
        self.api_base = api_base.rstrip("/")
        self.client_id = secret_config.sumup_client_id
        self.client_secret = secret_config.sumup_client_secret
        self.refresh_token = secret_config.sumup_refresh_token
        self.merchant_email = secret_config.sumup_merchant_email
        self.currency = currency
        self.access_token: str | None = None
        self.access_expires_at: float = 0

    async def connect(self) -> None:
        await self._refresh_access_token()

    async def disconnect(self) -> None:
        self.access_token = None

    async def _refresh_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code != 200:
                raise PaymentError("Failed to refresh SumUp access token")
            payload = response.json()

        self.access_token = payload.get("access_token")
        self.refresh_token = payload.get("refresh_token", self.refresh_token)
        expires_in = int(payload.get("expires_in", 3600))
        self.access_expires_at = time.time() + expires_in - 30
        if not self.access_token:
            raise PaymentError("No access_token returned from SumUp")
        return self.access_token

    async def _get_headers(self) -> dict[str, str]:
        if not self.access_token or time.time() >= self.access_expires_at:
            await self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def start_payment(self, amount: int) -> dict[str, str]:
        if amount < 1:
            raise PaymentError("Amount must be greater than zero")

        payload: dict[str, Any] = {
            "amount": f"{float(amount):.2f}",
            "currency": self.currency,
            "checkout_reference": f"muntauto-{int(time.time())}-{amount}",
            "description": "Consumptiemunten",
        }
        if self.merchant_email:
            payload["pay_to_email"] = self.merchant_email

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = await self._get_headers()
            response = await client.post(f"{self.api_base}/v1/checkouts", json=payload, headers=headers)
            if response.status_code != 200:
                raise PaymentError("Failed to create SumUp checkout")
            data = response.json()

        transaction_id = data.get("transaction_code") or data.get("id")
        if not transaction_id:
            raise PaymentError("No transaction_id received from SumUp")

        return {"transaction_id": transaction_id, "status": data.get("status", "pending")}

    async def cancel_payment(self, transaction_id: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = await self._get_headers()
            response = await client.post(f"{self.api_base}/v1/checkouts/{transaction_id}/cancel", headers=headers)
            if response.status_code not in {200, 204}:
                raise PaymentError("Failed to cancel SumUp payment")

    async def get_status(self, transaction_id: str) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = await self._get_headers()
            response = await client.get(f"{self.api_base}/v1/checkouts/{transaction_id}", headers=headers)
            if response.status_code != 200:
                raise PaymentError("Failed to retrieve SumUp payment status")
            data = response.json()

        return {"transaction_id": transaction_id, "status": data.get("status", "unknown")}
