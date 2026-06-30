from __future__ import annotations
from dataclasses import replace
from enum import Enum
from typing import Callable

from app.core.events import Event, EventType, MachineContext


class State(str, Enum):
    IDLE = "idle"
    SELECTED = "selected"
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_AUTHORIZED = "payment_authorized"
    DISPENSING = "dispensing"
    COMPLETE = "complete"
    ERROR = "error"


StateChangeHandler = Callable[[State, MachineContext], None]


class StateMachine:
    def __init__(self, on_change: StateChangeHandler | None = None) -> None:
        self.state = State.IDLE
        self.context = MachineContext()
        self.on_change = on_change

    def _state_payload(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "context": self.context.to_dict(),
        }

    def state_event(self) -> Event:
        return Event(EventType.MACHINE_STATE_CHANGED, self._state_payload())

    def _transition(self, new_state: State) -> Event:
        self.state = new_state
        if self.on_change:
            self.on_change(self.state, self.context)
        return self.state_event()

    def _ensure(self, expected: set[State], action: str) -> None:
        if self.state not in expected:
            expected_states = ", ".join(sorted(state.value for state in expected))
            raise RuntimeError(
                f"Cannot {action} from {self.state.value}; expected {expected_states}"
            )

    def select_amount(
        self,
        amount: int,
        price_per_coin: float,
        inventory: int | None = None,
    ) -> Event:
        self._ensure({State.IDLE, State.SELECTED}, "select amount")
        if amount < 1:
            raise ValueError("Amount must be at least 1")
        if inventory is not None and inventory <= 0:
            raise ValueError("Hopper empty")
        if inventory is not None and amount > inventory:
            raise ValueError("Not enough inventory for selected amount")
        self.context = MachineContext(
            amount=amount,
            price=round(amount * price_per_coin, 2),
            inventory=inventory,
        )
        return self._transition(State.SELECTED)

    def confirm_selection(self, inventory: int | None = None) -> Event:
        self._ensure({State.SELECTED}, "confirm selection")
        if inventory is not None and inventory <= 0:
            raise ValueError("Hopper empty")
        if inventory is not None and self.context.amount > inventory:
            raise ValueError("Not enough inventory for selected amount")
        self.context = replace(self.context, inventory=inventory)
        return self._transition(State.AWAITING_PAYMENT)

    def start_payment(self) -> Event:
        self._ensure({State.AWAITING_PAYMENT}, "start payment")
        return Event(
            EventType.PAYMENT_STARTED,
            {
                "amount": self.context.amount,
                "price": self.context.price,
            },
        )

    def payment_succeeded(self, transaction_id: str) -> Event:
        self._ensure({State.AWAITING_PAYMENT}, "authorize payment")
        self.context = replace(self.context, transaction_id=transaction_id, error=None)
        return self._transition(State.PAYMENT_AUTHORIZED)

    def payment_failed(self, error: str) -> Event:
        self._ensure({State.AWAITING_PAYMENT}, "fail payment")
        self.context = replace(self.context, error=error)
        return self._transition(State.ERROR)

    def start_dispensing(self) -> Event:
        self._ensure({State.PAYMENT_AUTHORIZED}, "start dispensing")
        self.context = replace(self.context, dispensed=0)
        return self._transition(State.DISPENSING)

    def dispensing_progress(self, current: int, total: int, inventory: int) -> Event:
        self._ensure({State.DISPENSING}, "record dispensing progress")
        self.context = replace(self.context, dispensed=current, inventory=inventory)
        return Event(
            EventType.DISPENSING_PROGRESS,
            {
                "current": current,
                "total": total,
                "inventory": inventory,
            },
        )

    def dispensing_finished(self, inventory: int) -> Event:
        self._ensure({State.DISPENSING}, "finish dispensing")
        self.context = replace(
            self.context,
            dispensed=self.context.amount,
            inventory=inventory,
        )
        return self._transition(State.COMPLETE)

    def fail(self, error: str) -> Event:
        self.context = replace(self.context, error=error)
        return self._transition(State.ERROR)

    def reset_machine(self, inventory: int | None = None) -> Event:
        self.context = MachineContext(inventory=inventory)
        return self._transition(State.IDLE)

    # Backwards-compatible wrappers for existing tests and scripts.
    def awaiting_payment(self) -> Event:
        return self.confirm_selection()

    def payment_authorized(self, transaction_id: str) -> Event:
        return self.payment_succeeded(transaction_id)

    def dispense(self) -> Event:
        return self.start_dispensing()

    def complete(self) -> Event:
        return self.dispensing_finished(self.context.inventory or 0)

    def reset(self) -> Event:
        return self.reset_machine()
