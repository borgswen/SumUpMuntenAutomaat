from __future__ import annotations
from typing import Any

from app.database.sqlite import Database


class TransactionService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def record_transaction(
        self,
        amount: int,
        price: float,
        status: str,
        transaction_id: str | None = None,
        raw_payload: Any | None = None,
    ) -> Any:
        return self.database.add_payment(
            amount=amount,
            price=price,
            status=status,
            transaction_id=transaction_id,
            raw_payload=raw_payload,
        )

    def list_transactions(self) -> list[Any]:
        return self.database.list_payments()
