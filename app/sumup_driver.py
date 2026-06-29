import asyncio
import time
from typing import Any

import httpx

from app.config import (
    SUMUP_API_BASE,
    SUMUP_CLIENT_ID,
    SUMUP_CLIENT_SECRET,
    SUMUP_CURRENCY,
    SUMUP_MERCHANT_EMAIL,
    SUMUP_REFRESH_TOKEN,
)


class SumUpDriver:
    def __init__(self) -> None:
        if not SUMUP_CLIENT_ID or not SUMUP_CLIENT_SECRET or not SUMUP_REFRESH_TOKEN:
            raise RuntimeError(
                "SumUp credentials are verplicht. Stel SUMUP_CLIENT_ID, SUMUP_CLIENT_SECRET en SUMUP_REFRESH_TOKEN in."
            )
        self.api_base = SUMUP_API_BASE.rstrip("/")
        self.client_id = SUMUP_CLIENT_ID
        self.client_secret = SUMUP_CLIENT_SECRET
        self.refresh_token = SUMUP_REFRESH_TOKEN
        self.currency = SUMUP_CURRENCY
        self.merchant_email = SUMUP_MERCHANT_EMAIL
        self.access_token: str | None = None
        self.access_expires_at: float = 0

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
            response.raise_for_status()
            payload = response.json()

        self.access_token = payload.get("access_token")
        self.refresh_token = payload.get("refresh_token", self.refresh_token)
        expires_in = payload.get("expires_in", 3600)
        self.access_expires_at = time.time() + int(expires_in) - 30

        if not self.access_token:
            raise RuntimeError("SumUp token refresh mislukte: geen access_token ontvangen")

        return self.access_token

    async def _get_access_token(self) -> str:
        if not self.access_token or time.time() >= self.access_expires_at:
            return await self._refresh_access_token()
        return self.access_token

    async def _get_headers(self) -> dict[str, str]:
        access_token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def start_payment(self, amount: int, description: str = "Consumptiemunten") -> dict[str, Any]:
        if amount < 1:
            raise ValueError("Amount moet groter zijn dan 0 zijn")

        payload: dict[str, Any] = {
            "amount": f"{float(amount):.2f}",
            "currency": self.currency,
            "checkout_reference": f"muntauto-{int(time.time())}-{amount}",
            "description": description,
        }

        if self.merchant_email:
            payload["pay_to_email"] = self.merchant_email

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = await self._get_headers()
            response = await client.post(f"{self.api_base}/v1/checkouts", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        transaction_id = data.get("transaction_code") or data.get("id") or data.get("checkout_reference")
        status = data.get("status") or data.get("checkout_status") or "pending"
        checkout_url = data.get("checkout_url") or data.get("redirect_url")

        return {
            "status": status,
            "transaction_id": transaction_id,
            "checkout_url": checkout_url,
            "raw": data,
        }

    async def check_payment(self, transaction_id: str) -> dict[str, Any]:
        if not transaction_id:
            raise ValueError("transaction_id is verplicht")

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = await self._get_headers()
            response = await client.get(f"{self.api_base}/v1/checkouts/{transaction_id}", headers=headers)
            response.raise_for_status()
            data = response.json()

        status = data.get("status") or data.get("checkout_status") or data.get("payment_status")
        return {
            "status": status,
            "transaction_id": transaction_id,
            "raw": data,
        }
