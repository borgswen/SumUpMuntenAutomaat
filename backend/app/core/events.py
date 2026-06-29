from __future__ import annotations
from enum import Enum
from typing import Any


class EventType(str, Enum):
    STATE_CHANGED = "state_changed"
    PAYMENT_STARTED = "payment_started"
    PAYMENT_UPDATED = "payment_updated"
    HOPPER_STARTED = "hopper_started"
    HOPPER_PROGRESS = "hopper_progress"
    HOPPER_COMPLETED = "hopper_completed"
    ERROR = "error"


class Event:
    def __init__(self, event_type: EventType, payload: dict[str, Any] | None = None) -> None:
        self.type = event_type
        self.payload = payload or {}

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "payload": self.payload}
