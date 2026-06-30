from __future__ import annotations
import asyncio
import random
from typing import Any

from app.drivers.hopper.base import HopperDriver
from app.core.exceptions import EmergencyStop, HopperEmpty, HopperError, HopperJam


class SimulatorHopper(HopperDriver):
    def __init__(
        self,
        speed: float = 6.0,
        capacity: int = 2500,
        start_amount: int = 1732,
        jam_probability: float = 0.0,
        random_failures: bool = False,
    ) -> None:
        self.connected = False
        self.speed = max(0.1, speed)
        self.capacity = max(1, capacity)
        self.inventory = min(max(0, start_amount), self.capacity)
        self.jam_probability = min(max(0.0, jam_probability), 1.0)
        self.random_failures = random_failures
        self._progress_callback = None
        self._stop_requested = False

    async def connect(self) -> None:
        await asyncio.sleep(0.1)
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    def set_progress_callback(self, callback: Any) -> None:
        self._progress_callback = callback

    async def dispense(self, amount: int) -> None:
        if not self.connected:
            raise HopperError("Simulator hopper is not connected")
        if amount < 1:
            raise HopperError("Dispense amount must be at least 1")
        if self.inventory <= 0:
            raise HopperEmpty("Hopper empty")
        if amount > self.inventory:
            raise HopperEmpty("Not enough coins in hopper")

        self._stop_requested = False
        dispensed = 0
        total = amount
        interval = 1.0 / self.speed

        while dispensed < total:
            if self._stop_requested:
                raise EmergencyStop("Emergency stop requested")

            if self.inventory <= 0:
                raise HopperEmpty("Hopper empty")

            if self.random_failures and random.random() < self.jam_probability:
                raise HopperJam("Hopper jammed")

            await asyncio.sleep(interval)
            self.inventory -= 1
            dispensed += 1

            if self._progress_callback:
                maybe = self._progress_callback(dispensed, total, self.inventory)
                if asyncio.iscoroutine(maybe):
                    await maybe

        return None

    async def stop(self) -> None:
        self._stop_requested = True

    async def get_status(self) -> dict[str, Any]:
        return {
            "status": "connected" if self.connected else "disconnected",
            "inventory": self.inventory,
            "capacity": self.capacity,
        }
