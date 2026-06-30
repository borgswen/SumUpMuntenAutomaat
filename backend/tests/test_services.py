import pytest

from app.core.exceptions import PaymentError, HopperError
from app.drivers.hopper.simulator import SimulatorHopper
from app.drivers.payment.simulator import SimulatorPayment
from app.services.hopper_service import HopperService
from app.services.payment_service import PaymentService


@pytest.mark.asyncio
async def test_payment_service_simulator_accepts():
    driver = SimulatorPayment(payment_mode="success", delay_ms=1)
    service = PaymentService(driver)

    await service.connect()
    result = await service.start_payment(2)
    assert result["transaction_id"].startswith("sim-2-")
    assert result["status"] == "pending"

    status = await service.wait_for_authorization(result["transaction_id"], timeout_seconds=1)
    assert status["status"] == "authorized"

    await service.disconnect()


@pytest.mark.asyncio
async def test_payment_service_simulator_times_out():
    driver = SimulatorPayment(payment_mode="timeout", delay_ms=1)
    service = PaymentService(driver)

    await service.connect()
    result = await service.start_payment(1)
    assert result["status"] == "pending"

    with pytest.raises(PaymentError):
        await service.wait_for_authorization(result["transaction_id"], timeout_seconds=1)

    await service.disconnect()


@pytest.mark.asyncio
async def test_hopper_service_simulator_dispense():
    progress: list[tuple[int, int, int]] = []
    driver = SimulatorHopper(speed=100, start_amount=5)
    service = HopperService(driver)
    service.set_progress_callback(lambda current, total, inventory: progress.append((current, total, inventory)))

    await service.connect()
    await service.dispense(3)
    assert progress == [(1, 3, 4), (2, 3, 3), (3, 3, 2)]
    assert await service.get_inventory() == 2
    await service.disconnect()


@pytest.mark.asyncio
async def test_hopper_service_simulator_error():
    driver = SimulatorHopper(start_amount=0)
    service = HopperService(driver)

    await service.connect()
    with pytest.raises(HopperError):
        await service.dispense(1)
    await service.disconnect()
