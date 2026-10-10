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

## Example

TODO.

## FAQ

TODO.

## License

MIT -- see [LICENSE](LICENSE).
