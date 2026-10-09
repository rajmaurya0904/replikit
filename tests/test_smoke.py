"""Smoke test: package imports cleanly. Replace/extend as modules land."""

import replikit


def test_version_is_set() -> None:
    assert replikit.__version__
