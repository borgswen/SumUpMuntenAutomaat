from __future__ import annotations

from typing import Any

import pytest

from app.core.config import SecretConfig
from app.drivers.payment.sumup import SumUpApiError, SumUpSoloPaymentDriver


class FakeSumUpHttpClient:
    def __init__(
        self,
        *,
        post_responses: list[dict[str, Any] | Exception] | None = None,
        get_responses: list[dict[str, Any] | Exception] | None = None,
    ) -> None:
        self.post_responses = post_responses or []
        self.get_responses = get_responses or []
        self.posts: list[dict[str, Any]] = []
        self.gets: list[dict[str, Any]] = []

    async def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        self.posts.append({"path": path, "json": json})
        response = self.post_responses.pop(0) if self.post_responses else {}
        if isinstance(response, Exception):
            raise response
        return response

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        self.gets.append({"path": path, "params": params})
        response = self.get_responses.pop(0) if self.get_responses else {}
        if isinstance(response, Exception):
            raise response
        return response


def build_driver(
    fake_client: FakeSumUpHttpClient,
    *,
    reader_id: str | None = "reader-123",
    reader_code: str | None = None,
) -> SumUpSoloPaymentDriver:
    return SumUpSoloPaymentDriver(
        secret_config=SecretConfig(sumup_api_key="test-api-key"),
        api_base="https://api.sumup.test",
        merchant_code="MERCHANT123",
        reader_id=reader_id,
        reader_code=reader_code,
        affiliate_key="affiliate-key",
        affiliate_app_id="sumup-muntenautomaat",
        currency="EUR",
        timeout_seconds=30,
        http_client=fake_client,
    )


@pytest.mark.asyncio
async def test_sumup_solo_creates_reader_checkout_with_minor_units() -> None:
    fake = FakeSumUpHttpClient(post_responses=[{"data": {"client_transaction_id": "client-123"}}])
    driver = build_driver(fake)

    await driver.connect()
    result = await driver.start_payment(20, price=31.0)

    assert result == {"transaction_id": "client-123", "status": "pending"}
    assert fake.posts[0]["path"] == "/v0.1/merchants/MERCHANT123/readers/reader-123/checkout"

    body = fake.posts[0]["json"]
    assert body["description"] == "20 consumptiemunten"
    assert body["total_amount"] == {"currency": "EUR", "minor_unit": 2, "value": 3100}
    assert body["affiliate"]["app_id"] == "sumup-muntenautomaat"
    assert body["affiliate"]["key"] == "affiliate-key"
    assert body["affiliate"]["foreign_transaction_id"].startswith("muntauto-")
    assert body["affiliate"]["tags"] == {"tokens": "20"}


@pytest.mark.asyncio
async def test_sumup_solo_can_pair_reader_with_pairing_code() -> None:
    fake = FakeSumUpHttpClient(post_responses=[{"data": {"id": "paired-reader"}}])
    driver = build_driver(fake, reader_id=None, reader_code="123456")

    await driver.connect()

    assert driver.reader_id == "paired-reader"
    assert fake.posts[0] == {
        "path": "/v0.1/merchants/MERCHANT123/readers",
        "json": {
            "pairing_code": "123456",
            "name": "SumUpMuntenAutomaat Solo",
        },
    }


@pytest.mark.asyncio
async def test_sumup_solo_reads_transaction_status() -> None:
    fake = FakeSumUpHttpClient(get_responses=[{"data": {"simple_status": "SUCCESSFUL"}}])
    driver = build_driver(fake)

    status = await driver.get_status("client-123")

    assert status["status"] == "authorized"
    assert status["raw_status"] == "SUCCESSFUL"
    assert fake.gets[0] == {
        "path": "/v2.1/merchants/MERCHANT123/transactions",
        "params": {"client_transaction_id": "client-123"},
    }


@pytest.mark.asyncio
async def test_sumup_solo_falls_back_to_reader_status_while_transaction_is_pending() -> None:
    fake = FakeSumUpHttpClient(
        get_responses=[
            SumUpApiError("not found", 404),
            {"data": {"status": {"code": "PROCESSING_CHECKOUT"}}},
        ]
    )
    driver = build_driver(fake)

    status = await driver.get_status("client-123")

    assert status["status"] == "pending"
    assert fake.gets[1]["path"] == "/v0.1/merchants/MERCHANT123/readers/reader-123"


@pytest.mark.asyncio
async def test_sumup_solo_terminates_active_checkout() -> None:
    fake = FakeSumUpHttpClient(post_responses=[{}])
    driver = build_driver(fake)

    await driver.cancel_payment("client-123")

    assert fake.posts[0] == {
        "path": "/v0.1/merchants/MERCHANT123/readers/reader-123/terminate",
        "json": {},
    }
