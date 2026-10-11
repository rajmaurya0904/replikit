"""HTTP server for RepliKit.

TODO: register real tools/resources here. This stub exists so the project
has something importable and testable from the first commit -- the build
loop fills in the actual server logic one task at a time.
"""

from aiohttp import web

from .api import BROKER_KEY, sse_events
from .events import EventBroker

HOST_KEY = web.AppKey("host", str)
PORT_KEY = web.AppKey("port", int)


async def _status(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def start_server(
    host: str, port: int, broker: EventBroker | None = None
) -> web.Application:
    """Build the aiohttp application with the status and SSE routes registered."""
    app = web.Application()
    app[HOST_KEY] = host
    app[PORT_KEY] = port
    app[BROKER_KEY] = broker if broker is not None else EventBroker()
    app.router.add_get("/", _status)
    app.router.add_get("/events", sse_events)
    return app


def main() -> None:
    raise NotImplementedError("TODO: wire up the MCP server and register its tools")


if __name__ == "__main__":
    main()
