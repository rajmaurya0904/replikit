"""PostgreSQL logical replication slot management for RepliKit."""


class ReplicationManager:
    """Owns the connection settings used to create and read a replication slot."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
