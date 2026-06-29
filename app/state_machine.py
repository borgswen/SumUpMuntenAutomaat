from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


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


class StateMachine:
    def __init__(self, on_state_change: Callable[[State, Context], None] | None = None) -> None:
        self.state = State.IDLE
        self.context = Context()
        self.on_state_change = on_state_change

    def _transition(self, new_state: State) -> None:
        self.state = new_state
        if self.on_state_change:
            self.on_state_change(self.state, self.context)

    def select_amount(self, amount: int, price_per_coin: float) -> None:
        if amount < 1:
            raise ValueError("Amount must be at least 1")
        self.context.amount = amount
        self.context.price = round(amount * price_per_coin, 2)
        self.context.transaction_id = None
        self.context.error = None
        self._transition(State.SELECTED)

    def awaiting_payment(self) -> None:
        if self.state != State.SELECTED:
            raise RuntimeError("Cannot start payment from current state")
        self._transition(State.AWAITING_PAYMENT)

    def payment_authorized(self, transaction_id: str) -> None:
        if self.state != State.AWAITING_PAYMENT:
            raise RuntimeError("Cannot authorize payment from current state")
        self.context.transaction_id = transaction_id
        self._transition(State.PAYMENT_AUTHORIZED)

    def dispense(self) -> None:
        if self.state != State.PAYMENT_AUTHORIZED:
            raise RuntimeError("Cannot dispense from current state")
        self._transition(State.DISPENSING)

    def complete(self) -> None:
        if self.state != State.DISPENSING:
            raise RuntimeError("Cannot complete from current state")
        self._transition(State.COMPLETE)

    def fail(self, error: str) -> None:
        self.context.error = error
        self._transition(State.ERROR)

    def reset(self) -> None:
        self.context = Context()
        self._transition(State.IDLE)

