"""Tests for EventBroker publish/subscribe fan-out."""

import asyncio

from replikit.events import EventBroker


async def test_subscribe_receives_published_event():
    broker = EventBroker()
    event = {"change": "INSERT", "table": "users"}

    stream = broker.subscribe()
    await broker.publish(event)
    received = await asyncio.wait_for(stream.__anext__(), timeout=1)
    await stream.aclose()

    assert received == event


async def test_subscribe_preserves_publish_order():
    broker = EventBroker()
    stream = broker.subscribe()
    for i in range(3):
        await broker.publish({"seq": i})

    received = [await asyncio.wait_for(stream.__anext__(), timeout=1) for _ in range(3)]
    await stream.aclose()

    assert received == [{"seq": 0}, {"seq": 1}, {"seq": 2}]


async def test_two_subscribers_both_receive_the_same_event():
    broker = EventBroker()
    event = {"change": "UPDATE", "table": "orders"}

    first = broker.subscribe()
    second = broker.subscribe()
    await broker.publish(event)

    received = await asyncio.gather(
        asyncio.wait_for(first.__anext__(), timeout=1),
        asyncio.wait_for(second.__anext__(), timeout=1),
    )
    await first.aclose()
    await second.aclose()

    assert received == [event, event]


async def test_each_subscriber_gets_its_own_copy():
    broker = EventBroker()
    first = broker.subscribe()
    second = broker.subscribe()

    await broker.publish({"table": "users"})
    one = await asyncio.wait_for(first.__anext__(), timeout=1)
    two = await asyncio.wait_for(second.__anext__(), timeout=1)
    one["table"] = "mutated"

    assert two == {"table": "users"}
    await first.aclose()
    await second.aclose()


async def test_closing_a_subscription_removes_its_queue():
    broker = EventBroker()
    stream = broker.subscribe()
    assert broker.subscriber_count == 1

    await stream.aclose()
    assert broker.subscriber_count == 0

    # Publishing with no subscribers left is a no-op, not an error.
    await broker.publish({"change": "DELETE"})
    assert broker.subscriber_count == 0


async def test_subscription_context_manager_unregisters_on_exit():
    broker = EventBroker()
    async with broker.subscribe() as stream:
        await broker.publish({"seq": 1})
        assert await asyncio.wait_for(stream.__anext__(), timeout=1) == {"seq": 1}
        assert broker.subscriber_count == 1
    assert broker.subscriber_count == 0


async def test_an_idle_subscriber_does_not_block_delivery_to_others():
    broker = EventBroker()
    idle = broker.subscribe()
    active = broker.subscribe()

    for i in range(5):
        await broker.publish({"seq": i})

    received = [await asyncio.wait_for(active.__anext__(), timeout=1) for _ in range(5)]
    assert received == [{"seq": i} for i in range(5)]

    await idle.aclose()
    await active.aclose()
