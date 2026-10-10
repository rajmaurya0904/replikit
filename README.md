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

TODO.

## License

MIT -- see [LICENSE](LICENSE).
