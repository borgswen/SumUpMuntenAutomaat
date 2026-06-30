from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventType(str, Enum):
    STATE_CHANGED = "state_changed"
    PAYMENT_STARTED = "payment_started"
    PAYMENT_UPDATED = "payment_updated"
    PAYMENT_CANCELLED = "payment_cancelled"
    HOPPER_STARTED = "hopper_started"
    HOPPER_PROGRESS = "dispensing_progress"
    HOPPER_COMPLETED = "hopper_completed"
    HOPPER_EMPTY = "hopper_empty"
    ERROR = "error"


@dataclass(frozen=True)
class MachineContext:
    amount: int = 0
    price: float = 0.0
    transaction_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "price": self.price,
            "transaction_id": self.transaction_id,
            "error": self.error,
        }


@dataclass(frozen=True)
class Event:
    type: EventType
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "payload": self.payload or {}}
