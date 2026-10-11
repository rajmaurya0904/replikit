"""Command-line interface for RepliKit."""

import argparse
from collections.abc import Sequence
from typing import Any

from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replikit",
        description="Expose PostgreSQL logical replication changes as SSE events.",
    )
    parser.add_argument("--host", help="bind address (overrides REPLIKIT_HOST)")
    parser.add_argument("--port", type=int, help="port (overrides REPLIKIT_PORT)")
    parser.add_argument("--dsn", help="PostgreSQL DSN (overrides REPLIKIT_PG_DSN)")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config: dict[str, Any] = load_config()
    overrides = {"host": args.host, "port": args.port, "pg_dsn": args.dsn}
    config.update({key: value for key, value in overrides.items() if value is not None})

    from .server import main as server_main

    server_main(config)


if __name__ == "__main__":
    main()
