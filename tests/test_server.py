"""Tests for the HTTP server skeleton."""

from aiohttp.test_utils import TestClient, TestServer

from replikit.server import HOST_KEY, PORT_KEY, start_server


async def test_root_returns_ok_json():
    app = await start_server("127.0.0.1", 0)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/")
        assert resp.status == 200
        assert await resp.json() == {"status": "ok"}


async def test_start_server_stores_host_and_port():
    app = await start_server("127.0.0.1", 9123)
    assert app[HOST_KEY] == "127.0.0.1"
    assert app[PORT_KEY] == 9123
