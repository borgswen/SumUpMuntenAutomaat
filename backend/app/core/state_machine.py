from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from app.core.events import Event, EventType


class State(str, Enum):
    IDLE = "idle"
    SELECTED = "selected"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_AUTHORIZED = "payment_authorized"
    DISPENSING = "dispensing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class Context:
    amount: int = 0
    price: float = 0.0
    transaction_id: str | None = None
    error: str | None = None


StateChangeHandler = Callable[[State, Context], None]


class StateMachine:
    def __init__(self, on_change: StateChangeHandler | None = None) -> None:
        self.state = State.IDLE
        self.context = Context()
        self.on_change = on_change

    def _transition(self, new_state: State) -> Event:
        self.state = new_state
        if self.on_change:
            self.on_change(self.state, self.context)
        return Event(EventType.STATE_CHANGED, {"state": self.state.value, "context": self.context})

    def select_amount(self, amount: int, price_per_coin: float) -> Event:
        if amount < 1:
            raise ValueError("Amount must be at least 1")
        self.context.amount = amount
        self.context.price = round(amount * price_per_coin, 2)
        self.context.transaction_id = None
        self.context.error = None
        return self._transition(State.SELECTED)

    def awaiting_payment(self) -> Event:
        if self.state != State.SELECTED:
            raise RuntimeError("Cannot start payment from current state")
        return self._transition(State.AWAITING_PAYMENT)

    def payment_authorized(self, transaction_id: str) -> Event:
        if self.state != State.AWAITING_PAYMENT:
            raise RuntimeError("Cannot authorize payment from current state")
        self.context.transaction_id = transaction_id
        return self._transition(State.PAYMENT_AUTHORIZED)

    def dispense(self) -> Event:
        if self.state != State.PAYMENT_AUTHORIZED:
            raise RuntimeError("Cannot dispense from current state")
        return self._transition(State.DISPENSING)

    def complete(self) -> Event:
        if self.state != State.DISPENSING:
            raise RuntimeError("Cannot complete from current state")
        return self._transition(State.COMPLETE)

    def fail(self, error: str) -> Event:
        self.context.error = error
        return self._transition(State.ERROR)

    def reset(self) -> Event:
        self.context = Context()
        return self._transition(State.IDLE)
