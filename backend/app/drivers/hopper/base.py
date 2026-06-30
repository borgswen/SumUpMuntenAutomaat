from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable


ProgressCallback = Callable[[int, int, int], Any]


class HopperDriver(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def dispense(self, amount: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_status(self) -> dict[str, Any]:
        raise NotImplementedError

    def set_progress_callback(self, callback: ProgressCallback | None) -> None:
        """Optional progress callback for simulators."""
        self._progress_callback = callback
