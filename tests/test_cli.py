"""Test CLI invocation."""

from unittest.mock import patch

import replikit.cli


def test_main_calls_server_main(capsys):
    """CLI main should call server main and exit cleanly."""
    with patch('replikit.server.main') as mock_server_main:
        replikit.cli.main([])
        mock_server_main.assert_called_once()
    # Ensure no unexpected output
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''


def test_flags_override_config_passed_to_server():
    args = ["--host", "127.0.0.1", "--port", "9001", "--dsn", "postgresql://u@h/db"]
    with patch('replikit.server.main') as mock_server_main:
        replikit.cli.main(args)
    config = mock_server_main.call_args.args[0]
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 9001
    assert config["pg_dsn"] == "postgresql://u@h/db"
