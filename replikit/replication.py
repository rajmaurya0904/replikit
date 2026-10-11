"""PostgreSQL logical replication slot management for RepliKit."""

import asyncio

import asyncpg

CREATE_SLOT_SQL = (
    "SELECT pg_create_logical_replication_slot($1, 'pgoutput') "
    "WHERE NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = $1)"
)
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5
DEFAULT_SLOT_NAME = "replikit_slot"


class ReplicationManager:
    """Owns the connection settings used to create and read a replication slot."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    async def _connect(self, max_retries: int = MAX_RETRIES) -> asyncpg.Connection:
        """Open a connection, retrying with exponential backoff on failure."""
        for attempt in range(max_retries + 1):
            try:
                return await asyncpg.connect(self.dsn)
            except (OSError, asyncpg.PostgresError):
                if attempt == max_retries:
                    raise
                await asyncio.sleep(RETRY_BASE_DELAY * 2**attempt)
        raise RuntimeError("unreachable: retry loop always returns or raises")

    async def start_slot(self, slot_name: str = DEFAULT_SLOT_NAME) -> None:
        """Create the logical replication slot if it does not already exist.

        Idempotent: the SQL skips creation when the slot is there, and a
        concurrent creator racing us raises DuplicateObjectError, which is
        the same "already exists" outcome and is ignored.
        """
        conn = await self._connect()
        try:
            await conn.execute(CREATE_SLOT_SQL, slot_name)
        except asyncpg.exceptions.DuplicateObjectError:
            pass
        finally:
            await conn.close()
