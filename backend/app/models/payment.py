from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PaymentResult:
    transaction_id: str
    status: str
