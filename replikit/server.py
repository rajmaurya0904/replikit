"""HTTP server for RepliKit.

TODO: register real tools/resources here. This stub exists so the project
has something importable and testable from the first commit -- the build
loop fills in the actual server logic one task at a time.
"""

import asyncio
import logging
from typing import Any

import asyncpg
from aiohttp import web

from .api import BROKER_KEY, sse_events
from .config import load_config
from .events import EventBroker
from .replication import DEFAULT_SLOT_NAME, ReplicationManager

log = logging.getLogger(__name__)

HOST_KEY = web.AppKey("host", str)
PORT_KEY = web.AppKey("port", int)
REPLICATION_KEY = web.AppKey("replication", ReplicationManager)


async def _status(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def start_server(
    host: str,
    port: int,
    broker: EventBroker | None = None,
    replication: ReplicationManager | None = None,
) -> web.Application:
    """Build the aiohttp application with the status and SSE routes registered."""
    app = web.Application()
    app[HOST_KEY] = host
    app[PORT_KEY] = port
    app[BROKER_KEY] = broker if broker is not None else EventBroker()
    if replication is not None:
        app[REPLICATION_KEY] = replication
    app.router.add_get("/", _status)
    app.router.add_get("/events", sse_events)
    return app


async def _setup(
    cfg: dict[str, Any], slot_name: str = DEFAULT_SLOT_NAME
) -> web.Application:
    """Create the replication slot, then build the app."""
    broker = EventBroker()
    replication = ReplicationManager(cfg["pg_dsn"])
    try:
        await replication.start_slot(slot_name)
        log.info("replication slot %r ready", slot_name)
    except (OSError, asyncpg.PostgresError) as exc:
        # Serving the HTTP endpoints is still useful, and the operator gets a
        # loud reason rather than a traceback at import time.
        log.warning("could not create replication slot %r: %s", slot_name, exc)
    return await start_server(
        cfg["host"], cfg["port"], broker=broker, replication=replication
    )


def main(config: dict[str, Any] | None = None) -> None:
    """Create the slot, build the broker and app, then serve until interrupted."""
    cfg = config if config is not None else load_config()
    app = asyncio.run(_setup(cfg))
    web.run_app(app, host=cfg["host"], port=cfg["port"])


if __name__ == "__main__":
    main()
