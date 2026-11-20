"""The state-boot bound (test_state.py): a gate off hosted runners, record-only on them. Fast; no emulator."""
from __future__ import annotations

import pytest

from test_state import check_state_bound


def test_state_bound_branches(monkeypatch):
    """The bound fails off a hosted runner and only records on one (the env is patched; no emulator)."""
    seen = []
    record = lambda name, value: seen.append((name, value))
    for var in ("GITHUB_ACTIONS", "CI", "RUNNER_ENVIRONMENT"):
        monkeypatch.delenv(var, raising=False)
    check_state_bound(2.4, record)
    with pytest.raises(AssertionError, match="state boot 2.60 s"):
        check_state_bound(2.6, record)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")                 # these two are set on self-hosted runners too
    monkeypatch.setenv("CI", "true")
    with pytest.raises(AssertionError):
        check_state_bound(2.6, record)
    monkeypatch.setenv("RUNNER_ENVIRONMENT", "self-hosted")
    with pytest.raises(AssertionError):
        check_state_bound(2.6, record)
    monkeypatch.setenv("RUNNER_ENVIRONMENT", "github-hosted")
    check_state_bound(9.0, record)                               # hosted: recorded, no failure
    monkeypatch.setenv("RUNNER_ENVIRONMENT", "self-hosted")
    with pytest.raises(AssertionError):
        check_state_bound(9.0, record)
    assert seen[-1] == ("state_boot_seconds", "9.00") and len(seen) == 6
