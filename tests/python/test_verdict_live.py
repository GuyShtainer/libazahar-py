"""examples/verdict.py exits by the table of docs/USING.md section 3: the pass and the failure codes 1, 12 and 13."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.slow


def run_example(host_paths, repo_root, **env: str) -> subprocess.CompletedProcess:
    """Run the example from the repo root with the test hooks in ``env``; the call is bounded to 3 minutes."""
    full = dict(os.environ, **env)
    return subprocess.run([sys.executable, "-I", str(repo_root / "examples" / "verdict.py"), str(host_paths.app)],
                          cwd=repo_root, env=full, capture_output=True, text=True, timeout=180, check=False)


def test_verdict_pass(host_paths, repo_root):
    done = run_example(host_paths, repo_root)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "verdict ok"


def test_verdict_exit_1_when_the_pass_line_never_comes(host_paths, repo_root):
    done = run_example(host_paths, repo_root, LAZ_VERDICT_PASS_TEXT="no such line", LAZ_VERDICT_FRAMES="120")
    assert done.returncode == 1, done.stderr
    assert "no 'no such line' line" in done.stderr


def test_verdict_exit_12_when_the_worker_stops_answering(host_paths, repo_root):
    """The heartbeat timeout fires only when the worker stops: freeze it after a second."""
    done = run_example(host_paths, repo_root, LAZ_VERDICT_PASS_TEXT="no such line", LAZ_VERDICT_FRAMES="1000000",
                       LAZ_VERDICT_TIMEOUT="3", LAZ_VERDICT_STOP_AFTER="1")
    assert done.returncode == 12, done.stderr
    assert "timed out" in done.stderr


def test_verdict_exit_13_when_the_worker_is_killed(host_paths, repo_root):
    done = run_example(host_paths, repo_root, LAZ_VERDICT_PASS_TEXT="no such line", LAZ_VERDICT_FRAMES="1000000",
                       LAZ_VERDICT_KILL_AFTER="3")
    assert done.returncode == 13, done.stderr
    assert "crashed" in done.stderr
