from __future__ import annotations

from app.core.exceptions import HopperError
from app.drivers.hopper.base import HopperDriver


class HopperService:
    def __init__(self, driver: HopperDriver) -> None:
        self.driver = driver

    async def connect(self) -> None:
        await self.driver.connect()

    async def disconnect(self) -> None:
        await self.driver.disconnect()

    async def dispense(self, amount: int) -> None:
        if amount < 1:
            raise HopperError("Dispense amount must be at least 1")
        await self.driver.dispense(amount)

    async def stop(self) -> None:
        await self.driver.stop()

    async def get_status(self) -> dict[str, str]:
        return await self.driver.get_status()
