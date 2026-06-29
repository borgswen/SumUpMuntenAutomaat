import asyncio
from typing import Any, Callable


class Simulator:
    async def start_payment(self, amount: int) -> dict[str, Any]:
        await asyncio.sleep(1.8)
        return {
            "status": "authorized",
            "transaction_id": f"sim-{amount}-{int(asyncio.get_running_loop().time())}",
        }

    async def dispense(self, amount: int, progress_callback: Callable[[int, int], None] | None = None) -> None:
        await asyncio.sleep(0.3)
        for index in range(1, amount + 1):
            await asyncio.sleep(0.06)
            if progress_callback:
                progress_callback(index, amount)
