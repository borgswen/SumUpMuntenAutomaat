from __future__ import annotations

import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from app.core.config import SecretConfig
from app.core.exceptions import ConfigurationError, PaymentError
from app.drivers.payment.base import PaymentDriver


logger = logging.getLogger(__name__)


class SumUpApiError(PaymentError):
    def __init__(self, message: str, status_code: int, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SumUpHttpClient(Protocol):
    async def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    async def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class SumUpSoloApiClient:
    def __init__(self, api_base: str, api_key: str, timeout_seconds: int) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = max(1, timeout_seconds)
        self._client: httpx.AsyncClient | None = None

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json=json)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        url = f"{self.api_base}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = await client.request(method, url, params=params, json=json, headers=headers)
        except httpx.HTTPError as exc:
            raise PaymentError(f"SumUp request failed: {exc}") from exc

        payload = self._parse_payload(response)
        if response.status_code >= 400:
            detail = self._extract_error_message(payload)
            raise SumUpApiError(f"SumUp API returned {response.status_code}: {detail}", response.status_code, payload)
        return payload

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=float(self.timeout_seconds))
        return self._client

    @staticmethod
    def _parse_payload(response: httpx.Response) -> dict[str, Any]:
        if not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError:
            return {"raw": response.text}
        return payload if isinstance(payload, dict) else {"data": payload}

    @staticmethod
    def _extract_error_message(payload: dict[str, Any]) -> str:
        for key in ("message", "error_description", "error"):
            value = payload.get(key)
            if value:
                return str(value)
        errors = payload.get("errors")
        if errors:
            return str(errors)
        return "unknown error"


class SumUpSoloPaymentDriver(PaymentDriver):
    def __init__(
        self,
        *,
        secret_config: SecretConfig,
        api_base: str,
        merchant_code: str | None,
        reader_id: str | None,
        reader_code: str | None,
        affiliate_key: str | None,
        affiliate_app_id: str,
        currency: str,
        timeout_seconds: int,
        http_client: SumUpHttpClient | None = None,
    ) -> None:
        self.secret_config = secret_config
        self.api_base = api_base
        self.merchant_code = merchant_code
        self.reader_id = reader_id
        self.reader_code = reader_code
        self.affiliate_key = affiliate_key
        self.affiliate_app_id = affiliate_app_id
        self.currency = currency.upper()
        self.timeout_seconds = timeout_seconds
        self._owns_http_client = http_client is None
        self.http_client = http_client or SumUpSoloApiClient(
            api_base=api_base,
            api_key=secret_config.sumup_api_key or "",
            timeout_seconds=timeout_seconds,
        )

    async def connect(self) -> None:
        self._require_config()
        if not self.reader_id:
            await self._pair_reader()

    async def disconnect(self) -> None:
        if self._owns_http_client:
            await self.http_client.close()

    async def start_payment(self, amount: int, price: float | None = None) -> dict[str, str]:
        self._require_config()
        if amount < 1:
            raise PaymentError("Amount must be greater than zero")
        if price is None or price <= 0:
            raise PaymentError("Payment price must be greater than zero")

        payload, foreign_transaction_id = self._build_checkout_payload(amount, price)
        data = await self.http_client.post(self._reader_checkout_path(), json=payload)
        checkout = self._unwrap_data(data)
        transaction_id = checkout.get("client_transaction_id")
        if not transaction_id:
            raise PaymentError("No client_transaction_id received from SumUp Solo")

        logger.info(
            "Started SumUp Solo checkout %s for %s tokens using foreign transaction %s",
            transaction_id,
            amount,
            foreign_transaction_id,
        )
        return {"transaction_id": str(transaction_id), "status": "pending"}

    async def cancel_payment(self, transaction_id: str) -> None:
        self._require_config()
        await self.http_client.post(self._reader_terminate_path(), json={})
        logger.info("Terminated active SumUp Solo checkout for transaction %s", transaction_id)

    async def get_status(self, transaction_id: str) -> dict[str, str]:
        self._require_config()
        try:
            data = await self.http_client.get(
                self._transactions_path(),
                params={"client_transaction_id": transaction_id},
            )
        except SumUpApiError as exc:
            if exc.status_code != 404:
                raise
            return await self._pending_status_from_reader(transaction_id)

        transaction = self._unwrap_data(data)
        raw_status = str(transaction.get("simple_status") or transaction.get("status") or "PENDING")
        return {
            "transaction_id": transaction_id,
            "status": self._normalize_transaction_status(raw_status),
            "raw_status": raw_status,
        }

    async def _pair_reader(self) -> None:
        if not self.reader_code:
            raise ConfigurationError("sumup_reader_id or sumup_reader_code is required")

        payload = {
            "pairing_code": self.reader_code,
            "name": "SumUpMuntenAutomaat Solo",
        }
        data = await self.http_client.post(self._readers_path(), json=payload)
        reader = self._unwrap_data(data)
        reader_id = reader.get("id")
        if not reader_id:
            raise PaymentError("SumUp Solo pairing succeeded without returning a reader id")
        self.reader_id = str(reader_id)
        logger.info("Paired SumUp Solo reader %s. Store this value as sumup_reader_id.", self.reader_id)

    async def _pending_status_from_reader(self, transaction_id: str) -> dict[str, str]:
        data = await self.http_client.get(self._reader_path())
        reader = self._unwrap_data(data)
        reader_status = self._reader_status(reader)
        return {
            "transaction_id": transaction_id,
            "status": reader_status,
            "raw_status": str(reader.get("status") or reader.get("state") or "unknown"),
        }

    def _build_checkout_payload(self, amount: int, price: float) -> tuple[dict[str, Any], str]:
        foreign_transaction_id = f"muntauto-{int(time.time() * 1000)}-{amount}"
        payload: dict[str, Any] = {
            "description": f"{amount} consumptiemunten",
            "total_amount": {
                "currency": self.currency,
                "minor_unit": self._minor_unit_for_currency(self.currency),
                "value": self._to_minor_units(price),
            },
        }

        if self.affiliate_key:
            payload["affiliate"] = {
                "app_id": self.affiliate_app_id,
                "key": self.affiliate_key,
                "foreign_transaction_id": foreign_transaction_id,
                "tags": {
                    "tokens": str(amount),
                },
            }

        return payload, foreign_transaction_id

    def _reader_checkout_path(self) -> str:
        return f"{self._reader_path()}/checkout"

    def _reader_terminate_path(self) -> str:
        return f"{self._reader_path()}/terminate"

    def _reader_path(self) -> str:
        reader_id = self.reader_id
        if not reader_id:
            raise ConfigurationError("sumup_reader_id is required after pairing")
        return f"{self._readers_path()}/{quote(reader_id, safe='')}"

    def _readers_path(self) -> str:
        merchant_code = self._merchant_code()
        return f"/v0.1/merchants/{quote(merchant_code, safe='')}/readers"

    def _transactions_path(self) -> str:
        merchant_code = self._merchant_code()
        return f"/v2.1/merchants/{quote(merchant_code, safe='')}/transactions"

    def _merchant_code(self) -> str:
        if not self.merchant_code:
            raise ConfigurationError("sumup_merchant_code is required")
        return self.merchant_code

    def _require_config(self) -> None:
        if not self.secret_config.sumup_api_key:
            raise ConfigurationError("sumup_api_key is required in backend/secret.yaml")
        if not self.merchant_code:
            raise ConfigurationError("sumup_merchant_code is required")
        if not self.reader_id and not self.reader_code:
            raise ConfigurationError("sumup_reader_id or sumup_reader_code is required")

    def _to_minor_units(self, price: float) -> int:
        minor_unit = self._minor_unit_for_currency(self.currency)
        quant = Decimal("1").scaleb(-minor_unit)
        value = Decimal(str(price)).quantize(quant, rounding=ROUND_HALF_UP)
        multiplier = Decimal(10) ** minor_unit
        return int((value * multiplier).to_integral_value(rounding=ROUND_HALF_UP))

    @staticmethod
    def _minor_unit_for_currency(currency: str) -> int:
        zero_decimal_currencies = {"BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW", "PYG", "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF"}
        return 0 if currency.upper() in zero_decimal_currencies else 2

    @staticmethod
    def _normalize_transaction_status(status: str) -> str:
        normalized = status.strip().upper().replace("-", "_")
        if normalized in {"SUCCESSFUL", "SUCCESS", "PAID_OUT", "AUTHORIZED"}:
            return "authorized"
        failed_statuses = {
            "FAILED",
            "DECLINED",
            "ERROR",
            "ABORTED",
            "REFUNDED",
            "REFUND_FAILED",
            "CHARGEBACK",
            "NON_COLLECTION",
            "CANCEL_FAILED",
        }
        if normalized in failed_statuses:
            return "failed"
        if normalized in {"CANCELED", "CANCELLED", "TERMINATED"}:
            return "cancelled"
        if normalized in {"EXPIRED", "TIMEOUT", "TIMED_OUT"}:
            return "expired"
        return "pending"

    @staticmethod
    def _reader_status(reader: dict[str, Any]) -> str:
        status_payload = reader.get("status")
        status_code = ""
        if isinstance(status_payload, dict):
            status_code = str(status_payload.get("code") or status_payload.get("message") or "")
        elif status_payload:
            status_code = str(status_payload)

        state = str(reader.get("state") or "")
        combined = f"{status_code} {state}".strip().upper()
        if "FAILED" in combined or "DECLINED" in combined or "ERROR" in combined or "OFFLINE" in combined:
            return "failed"
        if "CANCEL" in combined or "TERMINATED" in combined:
            return "cancelled"
        if "EXPIRED" in combined or "TIMEOUT" in combined:
            return "expired"
        return "pending"

    @staticmethod
    def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data", payload)
        return data if isinstance(data, dict) else {}


SumUpPayment = SumUpSoloPaymentDriver
