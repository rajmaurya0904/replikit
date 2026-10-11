"""Command-line interface for RepliKit."""

import argparse
from collections.abc import Sequence
from typing import Any

from .config import load_config

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replikit",
        description="Expose PostgreSQL logical replication changes as SSE events.",
    )
    parser.add_argument("--config", metavar="FILE", help="TOML config file")
    parser.add_argument("--host", help="bind address (overrides REPLIKIT_HOST)")
    parser.add_argument("--port", type=int, help="port (overrides REPLIKIT_PORT)")
    parser.add_argument("--dsn", help="PostgreSQL DSN (overrides REPLIKIT_PG_DSN)")
    return parser


def load_toml(path: str) -> dict[str, Any]:
    """Read a TOML config file into a dict."""
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    file_values = None
    if args.config:
        try:
            file_values = load_toml(args.config)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            parser.error(f"cannot read config file {args.config}: {exc}")
    config: dict[str, Any] = load_config(file_values)
    overrides = {"host": args.host, "port": args.port, "pg_dsn": args.dsn}
    config.update({key: value for key, value in overrides.items() if value is not None})

    from .server import main as server_main

    server_main(config)


if __name__ == "__main__":
    main()
