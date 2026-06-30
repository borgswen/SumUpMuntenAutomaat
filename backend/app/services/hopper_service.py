from __future__ import annotations
from typing import Any

from app.core.exceptions import HopperEmpty, HopperError
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
        status = await self.get_status()
        inventory = int(status.get("inventory", 0))
        if inventory <= 0:
            raise HopperEmpty("Hopper empty")
        if amount > inventory:
            raise HopperEmpty("Not enough coins in hopper")
        await self.driver.dispense(amount)

    async def stop(self) -> None:
        await self.driver.stop()

    async def get_status(self) -> dict[str, Any]:
        return await self.driver.get_status()

    async def get_inventory(self) -> int | None:
        status = await self.get_status()
        inventory = status.get("inventory")
        if inventory is None:
            return None
        return int(inventory)

    def set_progress_callback(self, callback: Any) -> None:
        self.driver.set_progress_callback(callback)
