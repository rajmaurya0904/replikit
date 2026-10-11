"""SSE API endpoint that streams replication events to clients."""

import json
from typing import Any

from aiohttp import web

from .events import EventBroker

BROKER_KEY = web.AppKey("broker", EventBroker)


def format_sse(event: dict[str, Any]) -> str:
    """Encode one event as a Server-Sent Events message."""
    return f"data: {json.dumps(event)}\n\n"


async def sse_events(request: web.Request) -> web.StreamResponse:
    """Stream broker events to the client as text/event-stream."""
    broker: EventBroker = request.app[BROKER_KEY]
    response = web.StreamResponse()
    response.content_type = "text/event-stream"
    response.headers["Cache-Control"] = "no-cache"
    await response.prepare(request)

    stream = broker.subscribe()
    try:
        async for event in stream:
            await response.write(format_sse(event).encode("utf-8"))
    except ConnectionResetError:
        return response
    finally:
        await stream.aclose()
    return response
