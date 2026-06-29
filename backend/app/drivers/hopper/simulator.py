from __future__ import annotations
import asyncio
from typing import Any

from app.drivers.hopper.base import HopperDriver
from app.core.exceptions import HopperError


class SimulatorHopper(HopperDriver):
    def __init__(self) -> None:
        self.connected = False
        self.current_amount = 0

    async def connect(self) -> None:
        await asyncio.sleep(0.1)
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def dispense(self, amount: int) -> None:
        if not self.connected:
            raise HopperError("Simulator hopper is not connected")
        self.current_amount = amount
        for _ in range(amount):
            await asyncio.sleep(0.05)

    async def stop(self) -> None:
        self.current_amount = 0

    async def get_status(self) -> dict[str, str]:
        return {"status": "connected" if self.connected else "disconnected"}
