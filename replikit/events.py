"""In-process event broker that fans replication changes out to every subscriber."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

Event = dict[str, Any]


class Subscription:
    """One subscriber's view of the broker: an async iterator over its own queue.

    The queue is registered with the broker as soon as the subscription is
    created, so events published after ``broker.subscribe()`` returns are never
    missed. Call ``aclose()`` (or use it as an async context manager) when the
    stream ends so the broker stops feeding a queue nobody reads.
    """

    def __init__(self, broker: "EventBroker") -> None:
        self._broker = broker
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._closed = False
        broker._register(self._queue)

    def __aiter__(self) -> AsyncIterator[Event]:
        return self

    async def __anext__(self) -> Event:
        if self._closed:
            raise StopAsyncIteration
        return await self._queue.get()

    async def aclose(self) -> None:
        """Unregister this subscriber's queue. Idempotent."""
        self._closed = True
        self._broker._unregister(self._queue)

    async def __aenter__(self) -> "Subscription":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()


class EventBroker:
    """Fan-out broker: publish() copies each event to every live subscriber.

    Each subscriber gets its own queue, so two SSE clients both receive every
    event instead of racing each other for a single shared queue.
    """

    def __init__(self) -> None:
        self._queues: set[asyncio.Queue[Event]] = set()

    @property
    def subscriber_count(self) -> int:
        """How many subscriptions are currently registered."""
        return len(self._queues)

    def _register(self, queue: "asyncio.Queue[Event]") -> None:
        self._queues.add(queue)

    def _unregister(self, queue: "asyncio.Queue[Event]") -> None:
        self._queues.discard(queue)

    async def publish(self, event: Event) -> None:
        """Deliver a copy of the event to each subscriber's queue."""
        for queue in list(self._queues):
            await queue.put(dict(event))

    def subscribe(self) -> Subscription:
        """Register a new subscriber and return its event stream."""
        return Subscription(self)
