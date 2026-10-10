# RepliKit

MCP server that exposes PostgreSQL logical replication changes as real-time events for AI agents to react to database updates.

## Installation

Basic installation:
```bash
pip install replikit
```

For development (includes testing and linting dependencies):
```bash
pip install replikit[dev]
```

## Usage

Run the RepliKit server from the command line:

```bash
replikit
```

Configure the server using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `REPLIKIT_PG_DSN` | PostgreSQL connection string | `postgresql://postgres@localhost:5432/postgres` |
| `REPLIKIT_HOST` | Server bind address | `0.0.0.0` |
| `REPLIKIT_PORT` | Server port | `8000` |

Example with custom configuration:

```bash
REPLIKIT_PG_DSN="postgresql://user:pass@db.example.com:5432/mydb" \
REPLIKIT_HOST="127.0.0.1" \
REPLIKIT_PORT=9000 \
replikit
```

## Examples

Below is a minimal example of a Python client using `aiohttp` to consume Server-Sent Events (SSE) from RepliKit:

```python
import asyncio
import aiohttp

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/events") as resp:
            async for line in resp.content:
                # SSE lines are UTF‑8 encoded
                text = line.decode().strip()
                if text.startswith("data:"):
                    payload = text[5:].strip()
                    print("Received event:", payload)

asyncio.run(main())
```

The server exposes the events at the `/events` endpoint. The client connects, reads the stream line by line, and prints each event payload.


## FAQ

**How do I create a replication slot?**
The server automatically creates a replication slot named `replikit_slot` when it starts. If the slot already exists, it will be reused. To manually create a slot, you can use the PostgreSQL command: `SELECT pg_create_logical_replication_slot('replikit_slot', 'pgoutput');`.

**What permissions does the PostgreSQL user need?**
The user specified in `REPLIKIT_PG_DSN` must have the `REPLICATION` privilege and sufficient rights to read the tables you want to monitor. Typically, granting `REPLICATION` and `SELECT` on the relevant tables (or using a superuser) is sufficient.

**What is the format of the events?**
Events are sent as Server-Sent Events (SSE) with the `data` field containing a JSON payload. Each payload includes the change type (`INSERT`, `UPDATE`, `DELETE`), the schema, table, column names, and the old and new values (for UPDATE). Example: `{"change": "INSERT", "schema": "public", "table": "users", "column_names": ["id", "name"], "column_values": [1, "Alice"]}`.

## License

MIT -- see [LICENSE](LICENSE).
