"""HTTP server for RepliKit.

TODO: register real tools/resources here. This stub exists so the project
has something importable and testable from the first commit -- the build
loop fills in the actual server logic one task at a time.
"""

import asyncio
from typing import Any

from aiohttp import web

from .api import BROKER_KEY, sse_events
from .config import load_config
from .events import EventBroker
from .replication import ReplicationManager

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


def main(config: dict[str, Any] | None = None) -> None:
    """Build the replication manager, broker and app, then serve until interrupted."""
    cfg = config if config is not None else load_config()
    broker = EventBroker()
    replication = ReplicationManager(cfg["pg_dsn"])
    app = asyncio.run(
        start_server(cfg["host"], cfg["port"], broker=broker, replication=replication)
    )
    web.run_app(app, host=cfg["host"], port=cfg["port"])


if __name__ == "__main__":
    main()
