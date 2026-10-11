"""Tests for the SSE /events endpoint."""

import asyncio

from aiohttp.test_utils import TestClient, TestServer

from replikit.api import format_sse
from replikit.events import EventBroker
from replikit.server import start_server


async def wait_for_subscribers(broker: EventBroker, count: int) -> None:
    """Wait until the broker has registered `count` subscribers."""
    async with asyncio.timeout(2):
        while broker.subscriber_count < count:
            await asyncio.sleep(0.01)


def test_format_sse_wraps_json_in_data_field():
    assert format_sse({"change": "INSERT"}) == 'data: {"change": "INSERT"}\n\n'


async def test_events_endpoint_streams_published_event():
    broker = EventBroker()
    app = await start_server("127.0.0.1", 0, broker=broker)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/events")
        assert resp.headers["Content-Type"].startswith("text/event-stream")
        await wait_for_subscribers(broker, 1)
        await broker.publish({"change": "INSERT", "table": "users"})
        chunk = await asyncio.wait_for(resp.content.readuntil(b"\n\n"), timeout=2)
        resp.close()

    assert chunk.decode() == 'data: {"change": "INSERT", "table": "users"}\n\n'


async def test_two_sse_clients_both_receive_the_event():
    broker = EventBroker()
    app = await start_server("127.0.0.1", 0, broker=broker)
    async with TestClient(TestServer(app)) as client:
        first = await client.get("/events")
        second = await client.get("/events")
        await wait_for_subscribers(broker, 2)
        await broker.publish({"change": "UPDATE", "table": "orders"})

        chunks = await asyncio.gather(
            asyncio.wait_for(first.content.readuntil(b"\n\n"), timeout=2),
            asyncio.wait_for(second.content.readuntil(b"\n\n"), timeout=2),
        )
        first.close()
        second.close()

    expected = 'data: {"change": "UPDATE", "table": "orders"}\n\n'
    assert [chunk.decode() for chunk in chunks] == [expected, expected]


async def test_broker_drops_the_subscriber_when_the_stream_ends():
    broker = EventBroker()
    app = await start_server("127.0.0.1", 0, broker=broker)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/events")
        await wait_for_subscribers(broker, 1)
        resp.close()
        # The handler only notices the dead client on the next write, so keep
        # publishing until its queue is unregistered.
        async with asyncio.timeout(2):
            while broker.subscriber_count:
                await broker.publish({"change": "INSERT"})
                await asyncio.sleep(0.01)

    assert broker.subscriber_count == 0
