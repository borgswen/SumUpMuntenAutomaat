from __future__ import annotations
from fastapi import APIRouter

from app.services.transaction_service import TransactionService

router = APIRouter()


def get_transactions_router(transaction_service: TransactionService) -> APIRouter:
    @router.get("/transactions")
    async def list_transactions() -> list[dict[str, str | int | float | None]]:
        records = transaction_service.list_transactions()
        return [
            {
                "id": record.id,
                "amount": record.amount,
                "price": record.price,
                "status": record.status,
                "transaction_id": record.transaction_id,
                "timestamp": record.timestamp.isoformat(),
            }
            for record in records
        ]

    return router
