"""PostgreSQL logical replication slot management for RepliKit."""

import asyncpg

CREATE_SLOT_SQL = (
    "SELECT pg_create_logical_replication_slot($1, 'pgoutput') "
    "WHERE NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = $1)"
)


class ReplicationManager:
    """Owns the connection settings used to create and read a replication slot."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    async def start_slot(self, slot_name: str) -> None:
        """Create the logical replication slot if it does not already exist."""
        conn = await asyncpg.connect(self.dsn)
        try:
            await conn.execute(CREATE_SLOT_SQL, slot_name)
        finally:
            await conn.close()
