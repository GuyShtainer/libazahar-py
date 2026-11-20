"""The state-boot bound (test_state.py): a gate off hosted runners, record-only on them. Fast; no emulator."""
from __future__ import annotations

import pytest

from test_state import check_state_bound


def test_state_bound_branches(monkeypatch):
    """The bound fails off a hosted runner and only records on one (the env is patched; no emulator)."""
    seen = []
    record = lambda name, value: seen.append((name, value))
    for var in ("GITHUB_ACTIONS", "CI"):
        monkeypatch.delenv(var, raising=False)
    check_state_bound(2.4, record)
    with pytest.raises(AssertionError, match="state boot 2.60 s"):
        check_state_bound(2.6, record)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")                 # one variable alone is not a hosted runner
    with pytest.raises(AssertionError):
        check_state_bound(2.6, record)
    monkeypatch.setenv("CI", "true")
    check_state_bound(9.0, record)                               # hosted: recorded, no failure
    monkeypatch.setenv("GITHUB_ACTIONS", "false")
    with pytest.raises(AssertionError):
        check_state_bound(9.0, record)
    assert seen[-1] == ("state_boot_seconds", "9.00") and len(seen) == 5
