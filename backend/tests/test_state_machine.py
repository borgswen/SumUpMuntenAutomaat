from app.core.events import EventType
from app.core.state_machine import StateMachine, State


def test_state_machine_transitions():
    machine = StateMachine()

    event = machine.select_amount(3, 1.5, inventory=10)
    assert event.type == EventType.MACHINE_STATE_CHANGED
    assert machine.state == State.SELECTED
    assert machine.context.amount == 3
    assert machine.context.price == 4.5
    assert machine.context.inventory == 10

    event = machine.confirm_selection(inventory=10)
    assert machine.state == State.AWAITING_PAYMENT

    event = machine.start_payment()
    assert event.type == EventType.PAYMENT_STARTED

    event = machine.payment_succeeded("txn-123")
    assert machine.state == State.PAYMENT_AUTHORIZED
    assert machine.context.transaction_id == "txn-123"

    event = machine.start_dispensing()
    assert machine.state == State.DISPENSING

    event = machine.dispensing_progress(1, 3, 9)
    assert event.type == EventType.DISPENSING_PROGRESS
    assert machine.context.dispensed == 1
    assert machine.context.inventory == 9

    event = machine.dispensing_finished(7)
    assert machine.state == State.COMPLETE

    event = machine.reset_machine(inventory=7)
    assert machine.state == State.IDLE
    assert machine.context.amount == 0
    assert machine.context.transaction_id is None
    assert machine.context.inventory == 7


def test_invalid_transition_raises():
    machine = StateMachine()

    try:
        machine.start_payment()
    except RuntimeError as exc:
        assert "Cannot start payment" in str(exc)
    else:
        raise AssertionError("Expected invalid transition to raise")
