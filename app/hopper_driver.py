import asyncio
from typing import Callable


class HopperDriver:
    async def dispense(self, amount: int, progress_callback: Callable[[int, int], None] | None = None) -> None:
        """Dispense coins through the hopper. Replace with GPIO/relais code later."""
        for index in range(1, amount + 1):
            await asyncio.sleep(0.08)
            if progress_callback:
                progress_callback(index, amount)
