from app.core.events import EventType
from app.core.state_machine import StateMachine, State


def test_state_machine_transitions():
    machine = StateMachine()

    event = machine.select_amount(3, 1.5)
    assert event.type == EventType.STATE_CHANGED
    assert machine.state == State.SELECTED
    assert machine.context.amount == 3
    assert machine.context.price == 4.5

    event = machine.awaiting_payment()
    assert machine.state == State.AWAITING_PAYMENT

    event = machine.payment_authorized("txn-123")
    assert machine.state == State.PAYMENT_AUTHORIZED
    assert machine.context.transaction_id == "txn-123"

    event = machine.dispense()
    assert machine.state == State.DISPENSING

    event = machine.complete()
    assert machine.state == State.COMPLETE

    event = machine.reset()
    assert machine.state == State.IDLE
    assert machine.context.amount == 0
    assert machine.context.transaction_id is None
