import os
from typing import Any


def load_config() -> dict[str, Any]:
    """
    Load configuration from environment variables with sensible defaults.

    Returns:
        dict: Configuration dictionary with keys 'pg_dsn', 'host', 'port'.
    """
    config = {
        "pg_dsn": os.getenv("REPLIKIT_PG_DSN", "postgresql://postgres@localhost:5432/postgres"),
        "host": os.getenv("REPLIKIT_HOST", "0.0.0.0"),
        "port": int(os.getenv("REPLIKIT_PORT", "8000")),
    }
    return config