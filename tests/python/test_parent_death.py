"""A caller that dies leaves no worker and no held slot (B5): Windows Job object, EOF, macOS kqueue.

The parent is a subprocess that this test ends with a hard kill (TerminateProcess on Windows, SIGKILL elsewhere): the way
a crashed or killed script ends. Fake-worker cases are fast; the live cases (marked slow) use the real emulator.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import List

import pytest

from libazahar import _slots, _worker
from libazahar._client import worker_python
from proc_helpers import WIN, hard_kill, pid_alive

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "python"
FAKE = Path(__file__).resolve().parent / "fakeworker.py"
GONE_S = 5.0
MID_BATCH_OK = WIN or sys.platform == "darwin"      # elsewhere a worker inside a batch cannot see EOF (no job, no kqueue)

FAKE_PARENT = textwrap.dedent('''
    import os, sys, time
    sys.path.insert(0, sys.argv[1])
    from pathlib import Path
    from libazahar._client import Wait, WorkerClient, worker_python
    work, fake, pkg, mode = Path(sys.argv[2]), sys.argv[3], sys.argv[1], sys.argv[4]
    def argv(fd):
        return [worker_python(), "-I", fake, "hang" if mode == "mid" else "ok", str(fd), str(work / "host.map"), pkg]
    client = WorkerClient(work, work / "host.map", work / "host.log", dict(os.environ), argv=argv)
    client.spawn(30.0)
    print("PID", client.pid, flush=True)
    if mode == "mid":
        client.request("run", (), Wait(total=3600.0))
    time.sleep(3600)
''')


def start_parent(code: str, *args: str, env: dict | None = None) -> subprocess.Popen:
    """A parent process on the base interpreter (no venv launcher between us and it, so its pid is the parent's)."""
    return subprocess.Popen([worker_python(), "-I", "-c", code, str(PKG), *args], stdout=subprocess.PIPE, text=True,
                            env={**os.environ, **(env or {})})


def read_pid(parent: subprocess.Popen) -> int:
    line = parent.stdout.readline()                     # type: ignore[union-attr]
    assert line.startswith("PID "), f"parent said {line!r}"
    return int(line.split()[1])


def wait_gone(pid: int, seconds: float = GONE_S) -> float:
    begin = time.monotonic()
    while pid_alive(pid):
        assert time.monotonic() - begin < seconds, f"worker {pid} still alive {seconds} s after the parent died"
        time.sleep(0.05)
    return time.monotonic() - begin


def kill_and_check(parent: subprocess.Popen, worker: int, settle: float) -> None:
    try:
        time.sleep(settle)
        assert pid_alive(worker)
        hard_kill(parent.pid)
        parent.wait(timeout=10)
        took = wait_gone(worker)
        print(f"worker gone {took:.2f} s after the parent died", file=sys.stderr)
    finally:
        if pid_alive(worker):                           # our own test worker only
            hard_kill(worker)
        if parent.poll() is None:
            hard_kill(parent.pid)
            parent.wait(timeout=10)
        parent.stdout.close()                           # type: ignore[union-attr]


def test_fake_worker_ends_when_the_parent_dies_between_batches(tmp_path):
    parent = start_parent(FAKE_PARENT, str(tmp_path), str(FAKE), "idle")
    kill_and_check(parent, read_pid(parent), 0.5)


@pytest.mark.skipif(not MID_BATCH_OK, reason="mid-batch parent death needs the Windows job or the macOS kqueue thread")
def test_fake_worker_ends_when_the_parent_dies_mid_batch(tmp_path):
    parent = start_parent(FAKE_PARENT, str(tmp_path), str(FAKE), "mid")
    kill_and_check(parent, read_pid(parent), 1.0)


# ---- the pieces, without a parent death ----
@pytest.mark.skipif(not WIN, reason="the Job object")
def test_worker_is_in_a_job_with_kill_on_close(tmp_path):
    import ctypes
    from test_client import started
    client = started(tmp_path, "ok")
    try:
        kernel32 = ctypes.WinDLL("kernel32")
        kernel32.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        inside = ctypes.c_int(0)
        assert kernel32.IsProcessInJob(int(client.proc._handle), None, ctypes.byref(inside))
        assert inside.value == 1
    finally:
        client.close()


def test_job_failure_warns_once_and_falls_back(monkeypatch):
    from libazahar import _job
    monkeypatch.setattr(_job, "sys", type("S", (), {"platform": "win32"}))
    monkeypatch.setattr(_job, "_failed", False)
    monkeypatch.setattr(_job, "_job", None)

    def boom() -> None:
        raise OSError(5, "denied")

    monkeypatch.setattr(_job, "_kernel32", boom)
    proc = type("P", (), {"pid": 1})()
    with pytest.warns(RuntimeWarning, match="kill-on-close"):
        assert _job.assign(proc) is False
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _job.assign(proc) is False               # the second failure is silent


class FakeSelect:
    """A stand-in for ``select`` with a scripted kqueue."""

    KQ_FILTER_PROC, KQ_EV_ADD, KQ_EV_ONESHOT, KQ_NOTE_EXIT = -5, 1, 0x10, 0x80000000

    def __init__(self, register_error: Exception | None = None) -> None:
        self.calls: List[tuple] = []
        self.register_error = register_error

    def kevent(self, ident, **kwargs):
        self.calls.append(("kevent", ident, kwargs))
        return ("event", ident)

    def kqueue(self):
        outer = self

        class Queue:
            def control(self, changes, count, timeout):
                outer.calls.append(("control", changes, count, timeout))
                if changes and outer.register_error is not None:
                    raise outer.register_error
                return []
        return Queue()


def test_wait_for_parent_registers_then_blocks_then_exits():
    sel, exits = FakeSelect(), []
    assert _worker.wait_for_parent(os.getppid(), exits.append, sel) is True
    kinds = [call[0] for call in sel.calls]
    assert kinds == ["kevent", "control", "control"]
    assert sel.calls[0][2]["fflags"] == FakeSelect.KQ_NOTE_EXIT and sel.calls[1][2] == 0
    assert sel.calls[2][1] is None and sel.calls[2][3] is None      # the blocking wait
    assert exits == [0]


def test_wait_for_parent_exits_at_once_when_the_parent_is_gone_before_registering():
    sel, exits = FakeSelect(ProcessLookupError()), []
    _worker.wait_for_parent(os.getppid(), exits.append, sel)
    assert exits == [0] and [c[0] for c in sel.calls] == ["kevent", "control"]


def test_wait_for_parent_rechecks_getppid_after_registering():
    sel, exits = FakeSelect(), []
    _worker.wait_for_parent(os.getppid() + 1, exits.append, sel)     # the real parent is not the one we were told
    assert exits == [0] and [c[0] for c in sel.calls] == ["kevent", "control"]     # no blocking wait


def test_wait_for_parent_exits_at_once_when_already_reparented():
    sel, exits = FakeSelect(), []
    assert _worker.wait_for_parent(1, exits.append, sel) is True        # the parent died before the worker started
    assert exits == [0] and sel.calls == []                             # nothing registered, no wait


def test_no_kqueue_means_no_watch():
    assert _worker.wait_for_parent(1, lambda code: None, object()) is False
    assert _worker.start_parent_watch(1, lambda code: None, object()) is None


def test_the_watch_thread_is_a_daemon_that_calls_exit():
    sel, exits = FakeSelect(), []
    thread = _worker.start_parent_watch(os.getppid(), exits.append, sel)
    assert thread is not None and thread.daemon
    thread.join(5)
    assert exits == [0]


# ---- live: the real emulator (PC) ----
LIVE_PARENT = textwrap.dedent('''
    import sys, time
    sys.path.insert(0, sys.argv[1])
    from libazahar import Emulator
    mode = sys.argv[4]
    emu = Emulator(sys.argv[2], sys.argv[3])
    print("PID", emu.pid, flush=True)
    if mode == "mid":
        emu.run(1_000_000)
    time.sleep(3600)
''')

def slot_is_free(folder: Path) -> bool:
    """The single slot can be taken again (LAZ_MAX_INSTANCES=1 in the test)."""
    try:
        _slots.acquire(timeout=3.0).release()
        return True
    except Exception:
        return False


@pytest.fixture
def one_slot(tmp_path, monkeypatch):
    folder = tmp_path / "slots"
    monkeypatch.setenv("LAZ_SLOT_DIR", str(folder))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "1")
    return folder


def live_case(host_paths, workdir, one_slot, mode: str, settle: float) -> None:
    parent = start_parent(LIVE_PARENT, str(host_paths.app), str(workdir), mode)
    if mode == "boot":                       # the worker's pid is in slot.txt as soon as it is spawned: kill mid-boot
        text = ""
        begin = time.monotonic()
        while "pid=" not in text:
            assert time.monotonic() - begin < 30, "no slot.txt"
            time.sleep(0.05)
            text = (workdir / "slot.txt").read_text() if (workdir / "slot.txt").is_file() else ""
        worker = int(text.split("pid=")[1].split()[0])
    else:
        worker = read_pid(parent)
    kill_and_check(parent, worker, settle)
    assert slot_is_free(one_slot)


@pytest.mark.slow
def test_live_parent_death_between_batches(host_paths, workdir, one_slot):
    live_case(host_paths, workdir, one_slot, "idle", 1.0)


@pytest.mark.slow
def test_live_parent_death_mid_batch(host_paths, workdir, one_slot):
    live_case(host_paths, workdir, one_slot, "mid", 2.0)


@pytest.mark.slow
def test_live_parent_death_during_boot(host_paths, workdir, one_slot):
    live_case(host_paths, workdir, one_slot, "boot", 0.3)
