from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    MACHINE_STATE_CHANGED = "MachineStateChanged"
    PAYMENT_STARTED = "PaymentStarted"
    PAYMENT_SUCCEEDED = "PaymentSucceeded"
    PAYMENT_FAILED = "PaymentFailed"
    PAYMENT_CANCELLED = "PaymentCancelled"
    DISPENSING_STARTED = "DispensingStarted"
    DISPENSING_PROGRESS = "DispensingProgress"
    DISPENSING_FINISHED = "DispensingFinished"
    INVENTORY_CHANGED = "InventoryChanged"
    HOPPER_EMPTY = "HopperEmpty"
    MACHINE_RESET = "MachineReset"
    ERROR_OCCURRED = "ErrorOccurred"


@dataclass(frozen=True)
class MachineContext:
    amount: int = 0
    price: float = 0.0
    transaction_id: str | None = None
    error: str | None = None
    inventory: int | None = None
    dispensed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "price": self.price,
            "transaction_id": self.transaction_id,
            "error": self.error,
            "inventory": self.inventory,
            "dispensed": self.dispensed,
        }


@dataclass(frozen=True)
class Event:
    type: EventType
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": self.payload or {},
        }
