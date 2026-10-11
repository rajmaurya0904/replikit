# RepliKit

**An HTTP server that turns PostgreSQL logical replication changes into a
Server-Sent Events stream, so every connected agent sees every row change.**

Polling a table for "what changed?" is wasteful and always a little bit late,
and the usual fix -- one process tailing the WAL -- means whoever wires up a
second consumer quietly steals half the events. RepliKit owns the replication
slot and the fan-out: each subscriber gets its own bounded queue, so two agents
watching the same database both see the same INSERT.

## It really runs

```console
$ replikit --port 8765
could not create replication slot 'replikit_slot': [WinError 1225] The remote computer refused the network connection
======== Running on http://0.0.0.0:8765 ========
(Press CTRL+C to quit)
```

That first line is the honest case with no PostgreSQL listening on the DSN: the
slot is not created, the warning says why, and the HTTP endpoints come up
anyway. From another shell:

```console
$ curl -s localhost:8765/
{"status": "ok"}

$ curl -s -i -m 2 localhost:8765/events
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Transfer-Encoding: chunked
Date: Sun, 11 Oct 2026 08:52:03 GMT
Server: Python/3.14 aiohttp/3.14.5
```

The fan-out is the part worth proving. Save this as `fanout.py` and run it:

```python
import asyncio

from replikit.events import EventBroker


async def main():
    broker = EventBroker(max_queue_size=100)
    agent_a = broker.subscribe()
    agent_b = broker.subscribe()

    await broker.publish({"change": "INSERT", "table": "orders", "id": 42})

    print("agent A:", await agent_a.__anext__())
    print("agent B:", await agent_b.__anext__())
    print("subscribers:", broker.subscriber_count, "dropped:", broker.dropped_events)

    await agent_a.aclose()
    await agent_b.aclose()


asyncio.run(main())
```

```console
$ python fanout.py
agent A: {'change': 'INSERT', 'table': 'orders', 'id': 42}
agent B: {'change': 'INSERT', 'table': 'orders', 'id': 42}
subscribers: 2 dropped: 0
```

## Install

Not on PyPI. Clone it and install from the checkout:

```bash
pip install -e .
```

## Usage

```console
$ replikit --help
usage: replikit [-h] [--config FILE] [--host HOST] [--port PORT] [--dsn DSN]

Expose PostgreSQL logical replication changes as SSE events.

options:
  -h, --help     show this help message and exit
  --config FILE  TOML config file
  --host HOST    bind address (overrides REPLIKIT_HOST)
  --port PORT    port (overrides REPLIKIT_PORT)
  --dsn DSN      PostgreSQL DSN (overrides REPLIKIT_PG_DSN)
```

```bash
replikit                                            # defaults: 0.0.0.0:8000, local postgres
replikit --dsn postgresql://u:pw@db:5432/app        # point at a real database
replikit --config replikit.toml --port 9000         # TOML file, one flag wins over it
curl -N localhost:8000/events                       # watch the SSE stream
```

Settings resolve highest-first: CLI flag, environment variable, TOML file,
built-in default.

| Variable | Description | Default |
|----------|-------------|---------|
| `REPLIKIT_PG_DSN` | PostgreSQL connection string | `postgresql://postgres@localhost:5432/postgres` |
| `REPLIKIT_HOST` | Bind address | `0.0.0.0` |
| `REPLIKIT_PORT` | Port | `8000` |

The TOML file uses the same keys as the config dict: `pg_dsn`, `host`, `port`.

## How it works

- On startup the server creates the logical replication slot `replikit_slot`
  with the `pgoutput` plugin, skipping creation when it already exists. A
  connection failure retries three times with exponential backoff (0.5s, 1s,
  2s) and then logs a warning instead of refusing to serve.
- `EventBroker.publish()` writes a copy of each event into one `asyncio.Queue`
  per subscriber, so N connected clients get N deliveries, not one race.
- Each queue is bounded (1000 events by default). When a subscriber's queue is
  full the policy is **drop-oldest**: the stalest event is discarded, the
  `dropped_events` counter goes up, and `publish()` never blocks on a client
  that stopped reading.
- `GET /events` subscribes, streams `data: {...}\n\n` lines, and unregisters
  the queue when the client disconnects. `GET /` returns `{"status": "ok"}`.

The SQL the server runs for the slot, if you would rather create it yourself:

```sql
SELECT pg_create_logical_replication_slot('replikit_slot', 'pgoutput');
```

## Limitations

- **The WAL reader is not implemented.** RepliKit creates the slot and owns the
  broker and the SSE endpoint, but nothing yet decodes `pgoutput` messages into
  events, so `/events` stays open and silent until something calls
  `broker.publish()` in-process. The fan-out, bounding and HTTP plumbing are
  real; the "PostgreSQL changes arrive by themselves" part is not there yet.
- **Needs PostgreSQL with `wal_level = logical`** and a role holding the
  `REPLICATION` privilege. Without it, slot creation fails and you get the
  warning shown above rather than a stream.
- **Untested against a real PostgreSQL.** Every test mocks `asyncpg.connect`;
  slot creation, privileges and `wal_level` have never been exercised against a
  live server, on any version. The Docker build test skips unless Docker is
  installed.
- **Drop-oldest loses events** under a slow consumer, by design. If you need
  at-least-once delivery, this is the wrong tool.
- The broker is in-process only: restarting the server loses buffered events,
  and two RepliKit processes do not share subscribers.
- No authentication, no TLS, no per-table filtering on `/events`.
- Despite the `mcp` dependency in `pyproject.toml`, there is no MCP server here
  yet -- the interface is plain HTTP plus SSE.

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

## License

MIT -- see [LICENSE](LICENSE).
