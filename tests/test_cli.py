"""Test CLI invocation."""

from unittest.mock import patch

import replikit.cli


def test_main_calls_server_main(capsys):
    """CLI main should call server main and exit cleanly."""
    with patch('replikit.server.main') as mock_server_main:
        replikit.cli.main()
        mock_server_main.assert_called_once()
    # Ensure no unexpected output
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''
