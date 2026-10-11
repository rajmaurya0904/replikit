"""In-process event broker that fans replication changes out to every subscriber."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

Event = dict[str, Any]

#: Events buffered per subscriber before the broker starts dropping.
DEFAULT_MAX_QUEUE_SIZE = 1000


class Subscription:
    """One subscriber's view of the broker: an async iterator over its own queue.

    The queue is registered with the broker as soon as the subscription is
    created, so events published after ``broker.subscribe()`` returns are never
    missed. Call ``aclose()`` (or use it as an async context manager) when the
    stream ends so the broker stops feeding a queue nobody reads.
    """

    def __init__(self, broker: "EventBroker") -> None:
        self._broker = broker
        self._queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=broker.max_queue_size)
        self._closed = False
        broker._register(self._queue)

    @property
    def pending(self) -> int:
        """Events buffered for this subscriber and not yet read."""
        return self._queue.qsize()

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

    Each queue is bounded at ``max_queue_size``. The policy when a subscriber's
    queue is full is **drop-oldest**: the stalest buffered event is discarded to
    make room for the new one, and ``dropped_events`` counts the discards. The
    reasoning is that a replication stream is most useful at its head -- a slow
    client that has fallen a thousand events behind wants the latest changes,
    not the ones it already missed -- and publish() never blocks or grows
    without limit because of one client that stopped reading.
    """

    def __init__(self, max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE) -> None:
        if max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        self.max_queue_size = max_queue_size
        self.dropped_events = 0
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
        """Deliver a copy of the event to each subscriber's queue.

        Never blocks: a full queue drops its oldest event to make room.
        """
        for queue in list(self._queues):
            try:
                queue.put_nowait(dict(event))
            except asyncio.QueueFull:
                self._drop_oldest(queue)
                queue.put_nowait(dict(event))

    def _drop_oldest(self, queue: "asyncio.Queue[Event]") -> None:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:  # pragma: no cover - drained concurrently
            return
        self.dropped_events += 1

    def subscribe(self) -> Subscription:
        """Register a new subscriber and return its event stream."""
        return Subscription(self)
