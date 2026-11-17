"""Our core's option profile: the plan order, where the file is found, and that the two files never share a key."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from libazahar import _paths, _worker
from libazahar.errors import HostError


def keys_of(path: Path) -> list[str]:
    return [line.partition("=")[0].strip() for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def test_plan_puts_lazpy_lines_first_on_our_core():
    lazpy, rest = [("a", "1"), ("b", "2")], [("c", "3"), ("a", "4")]
    assert _worker.option_plan(True, lazpy, rest) == lazpy + rest


def test_plan_skips_lazpy_lines_on_the_stock_core():
    assert _worker.option_plan(False, [("a", "1")], [("c", "3")]) == [("c", "3")]
    assert _worker.option_plan(False, [], []) == []


def test_lazpy_profile_variable_wins(tmp_path, monkeypatch):
    mine = tmp_path / "mine.txt"
    mine.write_text("citra_init_time=1\n")
    monkeypatch.setenv("LAZ_LAZPY_PROFILE", str(mine))
    assert _paths.lazpy_profile() == mine.resolve()


def test_lazpy_profile_none_and_missing_variable_file(tmp_path, monkeypatch):
    monkeypatch.setenv("LAZ_LAZPY_PROFILE", "none")
    assert _paths.lazpy_profile() is None
    monkeypatch.setenv("LAZ_LAZPY_PROFILE", str(tmp_path / "nope.txt"))
    with pytest.raises(HostError):
        _paths.lazpy_profile()


def test_lazpy_profile_default_with_and_without_the_file(tmp_path, monkeypatch):
    monkeypatch.delenv("LAZ_LAZPY_PROFILE", raising=False)
    monkeypatch.setenv("LAZ_ROOT", str(tmp_path))
    assert _paths.lazpy_profile() is None
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "options-lazpy.txt").write_text("citra_init_time=1\n")
    assert _paths.lazpy_profile() == (tmp_path / "core" / "options-lazpy.txt").resolve()


def test_no_key_is_in_both_profile_files(repo_root):
    lazpy = keys_of(repo_root / "core" / "options-lazpy.txt")
    default = keys_of(repo_root / "host" / "options-default.txt")
    assert len(lazpy) == 6 and not set(lazpy) & set(default)


@pytest.mark.skipif(sys.platform == "win32", reason="no nice values on Windows: the worker starts BELOW_NORMAL "
                    "(test_client.test_windows_worker_runs_below_normal)")
@pytest.mark.parametrize("start, want", [(5, 10), (10, 10), (15, 15), (20, 20)])
def test_worker_nice_floor(start: int, want: int) -> None:
    """raise_nice_floor raises a nicer process to 10 and never lowers one; at nice 20 it must not fail
    (os.nice(0) raised EPERM there). Each case runs in a child set to `start` first."""
    import os
    import subprocess
    import sys
    if os.getpriority(os.PRIO_PROCESS, 0) > start:
        pytest.skip(f"this process is already nicer than {start}")
    pkg = str(Path(_worker.__file__).resolve().parent.parent)
    code = ("import os, sys; sys.path.insert(0, sys.argv[1]); os.setpriority(os.PRIO_PROCESS, 0, int(sys.argv[2])); "
            "from libazahar import _worker; got = _worker.raise_nice_floor(); "
            "print(got, os.getpriority(os.PRIO_PROCESS, 0))")
    out = subprocess.run([sys.executable, "-I", "-c", code, pkg, str(start)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr[-300:]
    assert out.stdout.split() == [str(want), str(want)]
