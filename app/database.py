from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class PaymentRecord:
    amount: int
    price: float
    status: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    transaction_id: str | None = None


class Database:
    def __init__(self) -> None:
        self.records: List[PaymentRecord] = []

    def add_payment(self, amount: int, price: float, status: str, transaction_id: str | None = None) -> PaymentRecord:
        record = PaymentRecord(amount=amount, price=price, status=status, transaction_id=transaction_id)
        self.records.append(record)
        return record

    def list_payments(self) -> List[PaymentRecord]:
        return list(self.records)
