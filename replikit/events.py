"""In-process event broker that carries replication changes to subscribers."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any


class EventBroker:
    """Queue-backed broker: publish() enqueues events and subscribe() yields them."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def publish(self, event: dict[str, Any]) -> None:
        """Enqueue an event for subscribers."""
        await self._queue.put(event)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """Yield events in publish order, waiting when the queue is empty."""
        while True:
            yield await self._queue.get()
