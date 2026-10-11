"""Tests for ReplicationManager using mocked asyncpg connections."""

from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest

from replikit.replication import (
    CREATE_SLOT_SQL,
    DEFAULT_SLOT_NAME,
    ReplicationManager,
)


def test_init_stores_dsn():
    manager = ReplicationManager("postgresql://user:pw@host/db")
    assert manager.dsn == "postgresql://user:pw@host/db"


async def test_start_slot_executes_create_slot_sql():
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)) as connect:
        manager = ReplicationManager("postgresql://postgres@localhost/db")
        await manager.start_slot("replikit_slot")

    connect.assert_awaited_once_with("postgresql://postgres@localhost/db")
    conn.execute.assert_awaited_once_with(CREATE_SLOT_SQL, "replikit_slot")
    conn.close.assert_awaited_once()


async def test_start_slot_ignores_an_already_existing_slot():
    conn = MagicMock()
    conn.execute = AsyncMock(
        side_effect=asyncpg.exceptions.DuplicateObjectError("already exists")
    )
    conn.close = AsyncMock()
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)):
        manager = ReplicationManager("postgresql://postgres@localhost/db")
        await manager.start_slot("replikit_slot")
    conn.close.assert_awaited_once()


async def test_start_slot_defaults_to_the_replikit_slot_name():
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)):
        await ReplicationManager("postgresql://postgres@localhost/db").start_slot()
    conn.execute.assert_awaited_once_with(CREATE_SLOT_SQL, DEFAULT_SLOT_NAME)


async def test_start_slot_closes_connection_on_error():
    conn = MagicMock()
    conn.execute = AsyncMock(side_effect=RuntimeError("boom"))
    conn.close = AsyncMock()
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)):
        manager = ReplicationManager("postgresql://postgres@localhost/db")
        with pytest.raises(RuntimeError):
            await manager.start_slot("replikit_slot")
    conn.close.assert_awaited_once()
