"""Tests for the CLI --config flag (TOML config file)."""

from unittest.mock import patch

import pytest

import replikit.cli

TOML_BODY = 'pg_dsn = "postgresql://u@db/app"\nhost = "127.0.0.1"\nport = 7001\n'


@pytest.fixture(autouse=True)
def _clear_replikit_env(monkeypatch):
    for var in ("REPLIKIT_PG_DSN", "REPLIKIT_HOST", "REPLIKIT_PORT"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "replikit.toml"
    path.write_text(TOML_BODY, encoding="utf-8")
    return str(path)


def test_config_file_values_are_passed_to_server(config_file):
    with patch("replikit.server.main") as server_main:
        replikit.cli.main(["--config", config_file])
    config = server_main.call_args.args[0]
    assert config == {
        "pg_dsn": "postgresql://u@db/app",
        "host": "127.0.0.1",
        "port": 7001,
    }


def test_cli_flag_overrides_config_file(config_file):
    with patch("replikit.server.main") as server_main:
        replikit.cli.main(["--config", config_file, "--port", "7002"])
    assert server_main.call_args.args[0]["port"] == 7002


def test_missing_config_file_exits_with_code_2(tmp_path, capsys):
    with patch("replikit.server.main") as server_main:
        with pytest.raises(SystemExit) as exc:
            replikit.cli.main(["--config", str(tmp_path / "missing.toml")])
    assert exc.value.code == 2
    server_main.assert_not_called()
    assert "cannot read config file" in capsys.readouterr().err
