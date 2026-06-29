from __future__ import annotations
from abc import ABC, abstractmethod


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
    async def get_status(self) -> dict[str, str]:
        raise NotImplementedError
