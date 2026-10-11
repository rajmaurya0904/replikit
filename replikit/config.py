import os
from collections.abc import Mapping
from typing import Any

DEFAULTS: dict[str, Any] = {
    "pg_dsn": "postgresql://postgres@localhost:5432/postgres",
    "host": "0.0.0.0",
    "port": 8000,
}
ENV_VARS = {"pg_dsn": "REPLIKIT_PG_DSN", "host": "REPLIKIT_HOST", "port": "REPLIKIT_PORT"}


def load_config(file_values: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """
    Load configuration with sensible defaults.

    Precedence (highest first): environment variables, values from file_values
    (e.g. a TOML config file), built-in defaults.

    Returns:
        dict: Configuration dictionary with keys 'pg_dsn', 'host', 'port'.
    """
    config = dict(DEFAULTS)
    if file_values:
        config.update({key: file_values[key] for key in DEFAULTS if key in file_values})
    for key, var in ENV_VARS.items():
        if var in os.environ:
            config[key] = os.environ[var]
    config["port"] = int(config["port"])
    return config
