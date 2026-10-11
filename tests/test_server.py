"""Tests for the HTTP server skeleton."""

from unittest.mock import AsyncMock, patch

import asyncpg
import pytest
from aiohttp.test_utils import TestClient, TestServer

from replikit.replication import DEFAULT_SLOT_NAME
from replikit.server import HOST_KEY, PORT_KEY, REPLICATION_KEY, main, start_server

CONFIG = {"pg_dsn": "postgresql://u@h/db", "host": "127.0.0.1", "port": 9001}


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


def run_main(start_slot):
    """Run main() with run_app and ReplicationManager.start_slot patched."""
    with (
        patch("replikit.server.web.run_app") as run_app,
        patch("replikit.replication.ReplicationManager.start_slot", new=start_slot),
    ):
        main(dict(CONFIG))
    return run_app


def test_main_builds_app_and_runs_it_with_config():
    run_app = run_main(AsyncMock())
    app = run_app.call_args.args[0]
    assert app[HOST_KEY] == "127.0.0.1"
    assert app[PORT_KEY] == 9001
    assert app[REPLICATION_KEY].dsn == "postgresql://u@h/db"
    assert run_app.call_args.kwargs == {"host": "127.0.0.1", "port": 9001}


def test_main_creates_the_replication_slot_at_startup():
    start_slot = AsyncMock()
    run_main(start_slot)
    start_slot.assert_awaited_once_with(DEFAULT_SLOT_NAME)


@pytest.mark.parametrize(
    "error",
    [
        OSError("connection refused"),
        asyncpg.exceptions.InsufficientPrivilegeError("must be superuser"),
    ],
)
def test_main_still_serves_when_the_slot_cannot_be_created(error):
    run_app = run_main(AsyncMock(side_effect=error))
    assert run_app.call_args.args[0][PORT_KEY] == 9001
