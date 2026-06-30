from __future__ import annotations
import asyncio
from typing import Any

from app.drivers.hopper.base import HopperDriver
from app.core.exceptions import HopperError


class MoneyControlsHopper(HopperDriver):
    def __init__(self, port: str) -> None:
        self.port = port
        self.connected = False
        self._progress_callback = None

    async def connect(self) -> None:
        await asyncio.sleep(0.1)
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def dispense(self, amount: int) -> None:
        if not self.connected:
            raise HopperError("MoneyControls hopper is not connected")
        for _ in range(amount):
            await asyncio.sleep(0.08)

    async def stop(self) -> None:
        if not self.connected:
            raise HopperError("MoneyControls hopper is not connected")

    async def get_status(self) -> dict[str, str]:
        return {"status": "connected" if self.connected else "disconnected"}
