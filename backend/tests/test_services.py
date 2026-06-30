import pytest

from app.core.exceptions import PaymentError, HopperError
from app.drivers.hopper.simulator import SimulatorHopper
from app.drivers.payment.simulator import SimulatorPayment
from app.services.hopper_service import HopperService
from app.services.payment_service import PaymentService


@pytest.mark.asyncio
def test_payment_service_simulator_accepts():
    driver = SimulatorPayment(payment_behavior="accepted")
    service = PaymentService(driver)

    await service.connect()
    result = await service.start_payment(2)
    assert result["transaction_id"].startswith("sim-2-")
    assert result["status"] == "authorized"

    status = await service.get_status(result["transaction_id"])
    assert status["status"] == "authorized"

    await service.disconnect()


@pytest.mark.asyncio
def test_payment_service_simulator_times_out():
    driver = SimulatorPayment(payment_behavior="timeout", timeout_seconds=1)
    service = PaymentService(driver)

    await service.connect()
    result = await service.start_payment(1)
    assert result["status"] == "pending"

    with pytest.raises(PaymentError):
        await service.wait_for_authorization(result["transaction_id"], timeout_seconds=1)

    await service.disconnect()


@pytest.mark.asyncio
def test_hopper_service_simulator_dispense():
    driver = SimulatorHopper(behavior="fast")
    service = HopperService(driver)

    await service.connect()
    await service.dispense(3)
    await service.disconnect()


@pytest.mark.asyncio
def test_hopper_service_simulator_error():
    driver = SimulatorHopper(behavior="error")
    service = HopperService(driver)

    await service.connect()
    with pytest.raises(HopperError):
        await service.dispense(1)
    await service.disconnect()
