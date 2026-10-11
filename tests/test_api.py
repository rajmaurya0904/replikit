"""Tests for the SSE /events endpoint."""

import asyncio

from aiohttp.test_utils import TestClient, TestServer

from replikit.api import format_sse
from replikit.events import EventBroker
from replikit.server import start_server


def test_format_sse_wraps_json_in_data_field():
    assert format_sse({"change": "INSERT"}) == 'data: {"change": "INSERT"}\n\n'


async def test_events_endpoint_streams_published_event():
    broker = EventBroker()
    app = await start_server("127.0.0.1", 0, broker=broker)
    async with TestClient(TestServer(app)) as client:
        await broker.publish({"change": "INSERT", "table": "users"})
        resp = await client.get("/events")
        assert resp.headers["Content-Type"].startswith("text/event-stream")
        chunk = await asyncio.wait_for(resp.content.readuntil(b"\n\n"), timeout=2)
        resp.close()

    assert chunk.decode() == 'data: {"change": "INSERT", "table": "users"}\n\n'
