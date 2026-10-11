from replikit.config import load_config


def test_load_config_defaults(monkeypatch):
    # Ensure environment variables are not set
    monkeypatch.delenv("REPLIKIT_PG_DSN", raising=False)
    monkeypatch.delenv("REPLIKIT_HOST", raising=False)
    monkeypatch.delenv("REPLIKIT_PORT", raising=False)

    config = load_config()
    assert config["pg_dsn"] == "postgresql://postgres@localhost:5432/postgres"
    assert config["host"] == "0.0.0.0"
    assert config["port"] == 8000


def test_load_config_with_env(monkeypatch):
    monkeypatch.setenv("REPLIKIT_PG_DSN", "postgresql://user:pass@host:5432/db")
    monkeypatch.setenv("REPLIKIT_HOST", "127.0.0.1")
    monkeypatch.setenv("REPLIKIT_PORT", "9000")

    config = load_config()
    assert config["pg_dsn"] == "postgresql://user:pass@host:5432/db"
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 9000
