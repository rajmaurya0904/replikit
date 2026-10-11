"""HTTP server for RepliKit.

TODO: register real tools/resources here. This stub exists so the project
has something importable and testable from the first commit -- the build
loop fills in the actual server logic one task at a time.
"""

from aiohttp import web

HOST_KEY = web.AppKey("host", str)
PORT_KEY = web.AppKey("port", int)


async def _status(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def start_server(host: str, port: int) -> web.Application:
    """Build the aiohttp application with the status route registered."""
    app = web.Application()
    app[HOST_KEY] = host
    app[PORT_KEY] = port
    app.router.add_get("/", _status)
    return app


def main() -> None:
    raise NotImplementedError("TODO: wire up the MCP server and register its tools")


if __name__ == "__main__":
    main()
