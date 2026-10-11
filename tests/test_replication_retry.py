"""Tests for connection retry in ReplicationManager.start_slot."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from replikit.replication import CREATE_SLOT_SQL, MAX_RETRIES, ReplicationManager


async def test_start_slot_retries_then_succeeds():
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    connect = AsyncMock(side_effect=[OSError("refused"), OSError("refused"), conn])
    with (
        patch("asyncpg.connect", new=connect),
        patch("replikit.replication.asyncio.sleep", new=AsyncMock()) as sleep,
    ):
        manager = ReplicationManager("postgresql://postgres@localhost/db")
        await manager.start_slot("replikit_slot")

    assert connect.await_count == 3
    conn.execute.assert_awaited_once_with(CREATE_SLOT_SQL, "replikit_slot")
    assert [c.args[0] for c in sleep.await_args_list] == [0.5, 1.0]


async def test_start_slot_gives_up_after_max_retries():
    connect = AsyncMock(side_effect=OSError("refused"))
    with (
        patch("asyncpg.connect", new=connect),
        patch("replikit.replication.asyncio.sleep", new=AsyncMock()),
    ):
        manager = ReplicationManager("postgresql://postgres@localhost/db")
        with pytest.raises(OSError):
            await manager.start_slot("replikit_slot")

    assert connect.await_count == MAX_RETRIES + 1
