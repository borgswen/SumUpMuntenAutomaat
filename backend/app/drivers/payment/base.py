from __future__ import annotations
from abc import ABC, abstractmethod


class PaymentDriver(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_payment(self, amount: int, price: float | None = None) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def cancel_payment(self, transaction_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_status(self, transaction_id: str) -> dict[str, str]:
        raise NotImplementedError
