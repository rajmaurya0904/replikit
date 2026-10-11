"""Tests for the HTTP server skeleton."""

from unittest.mock import patch

from aiohttp.test_utils import TestClient, TestServer

from replikit.server import HOST_KEY, PORT_KEY, main, start_server


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


def test_main_builds_app_and_runs_it_with_config():
    config = {"pg_dsn": "postgresql://u@h/db", "host": "127.0.0.1", "port": 9001}
    with patch("replikit.server.web.run_app") as run_app:
        main(config)
    app = run_app.call_args.args[0]
    assert app[HOST_KEY] == "127.0.0.1"
    assert app[PORT_KEY] == 9001
    assert run_app.call_args.kwargs == {"host": "127.0.0.1", "port": 9001}
