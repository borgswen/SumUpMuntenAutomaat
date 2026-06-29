from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    id: int
    amount: int
    price: float
    status: str
    transaction_id: str | None
    timestamp: datetime
