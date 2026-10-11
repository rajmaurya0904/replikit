"""Tests for EventBroker publish/subscribe."""

import asyncio

from replikit.events import EventBroker


async def test_subscribe_receives_published_event():
    broker = EventBroker()
    event = {"change": "INSERT", "table": "users"}

    await broker.publish(event)
    stream = broker.subscribe()
    received = await asyncio.wait_for(stream.__anext__(), timeout=1)
    await stream.aclose()

    assert received == event


async def test_subscribe_preserves_publish_order():
    broker = EventBroker()
    for i in range(3):
        await broker.publish({"seq": i})

    stream = broker.subscribe()
    received = [await asyncio.wait_for(stream.__anext__(), timeout=1) for _ in range(3)]
    await stream.aclose()

    assert received == [{"seq": 0}, {"seq": 1}, {"seq": 2}]
