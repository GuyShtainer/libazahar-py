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

from libazahar import SlotTimeout, _slots, _worker
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
    if os.environ.get("LAZ_TEST_NO_JOB"):                  # the job assignment fails: today's behaviour must still work
        from libazahar import _job
        _job.assign = lambda proc: False
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
def test_fake_worker_still_ends_between_batches_when_the_job_assignment_fails(tmp_path):
    """The fallback: no job, so the worker ends on the pipe's EOF (``_worker._leave``). Windows is where it matters."""
    parent = start_parent(FAKE_PARENT, str(tmp_path), str(FAKE), "idle", env={"LAZ_TEST_NO_JOB": "1"})
    kill_and_check(parent, read_pid(parent), 0.5)


# ---- the pieces, without a parent death ----
def _job_calls():
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    kernel32.QueryInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32,
                                                   ctypes.c_void_p]
    return kernel32


@pytest.mark.skipif(not WIN, reason="the Job object")
def test_two_workers_are_both_in_our_kill_on_close_job(tmp_path):
    """Our own job (``_job._job``), not 'any job': under SSH or a CI runner every child is already in the session's job,
    and the second worker must be moved down into ours (a nested job). No RuntimeWarning may come out of either spawn."""
    import ctypes
    import warnings
    from libazahar import _job
    from test_client import started
    kernel32 = _job_calls()
    (first_dir, second_dir) = (tmp_path / "one", tmp_path / "two")
    first_dir.mkdir()
    second_dir.mkdir()
    clients = []
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            clients.append(started(first_dir, "ok"))
            clients.append(started(second_dir, "ok"))
        assert _job._job is not None and not _job._warned
        for client in clients:
            inside = ctypes.c_int(0)
            assert kernel32.IsProcessInJob(int(client.proc._handle), _job._job, ctypes.byref(inside))
            assert inside.value == 1, f"worker {client.pid} is not in our job"
        info = _job._Extended()
        assert kernel32.QueryInformationJobObject(_job._job, _job.JobObjectExtendedLimitInformation, ctypes.byref(info),
                                                  ctypes.sizeof(info), None)
        assert info.BasicLimitInformation.LimitFlags & _job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    finally:
        for client in clients:
            client.close()


@pytest.mark.skipif(not WIN, reason="the Job object")
def test_a_process_outside_our_job_is_reported_outside(tmp_path):
    """Negative control for the test above: this test process is not in our job, so the query can say no."""
    import ctypes
    from libazahar import _job
    from test_client import started
    client = started(tmp_path, "ok")             # makes sure the job exists
    try:
        inside = ctypes.c_int(1)
        assert _job_calls().IsProcessInJob(ctypes.c_void_p(-1), _job._job, ctypes.byref(inside))   # -1: this process
        assert inside.value == 0
    finally:
        client.close()


def test_job_failure_warns_once_and_falls_back(monkeypatch):
    from libazahar import _job
    monkeypatch.setattr(_job, "sys", type("S", (), {"platform": "win32"}))
    monkeypatch.setattr(_job, "_warned", False)
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


@pytest.mark.parametrize("make", [lambda: AttributeError("no such function"),
                                  lambda: __import__("ctypes").ArgumentError("bad argument")])
def test_job_failure_of_any_kind_warns_and_falls_back(monkeypatch, make):
    from libazahar import _job
    monkeypatch.setattr(_job, "sys", type("S", (), {"platform": "win32"}))
    monkeypatch.setattr(_job, "_warned", False)
    monkeypatch.setattr(_job, "_job", None)

    def boom() -> None:
        raise make()

    monkeypatch.setattr(_job, "_kernel32", boom)
    with pytest.warns(RuntimeWarning, match="kill-on-close"):
        assert _job.assign(type("P", (), {"pid": 1})()) is False


def test_an_assign_that_raises_leaves_no_worker_running(tmp_path, monkeypatch):
    """Whatever ``_job.assign`` raises after ``Popen`` succeeded, the started worker must not outlive the spawn.
    Off Windows ``_popen_windows`` is the only place that calls it, so call that path directly."""
    from libazahar import _client
    if not WIN:
        pytest.skip("the Windows spawn path")
    monkeypatch.setattr(_client._job, "assign", lambda proc: (_ for _ in ()).throw(RuntimeError("planted")))
    client = _client.WorkerClient(tmp_path, tmp_path / "host.map", tmp_path / "host.log", dict(os.environ),
                                  argv=lambda fd: [worker_python(), "-I", str(FAKE), "hang", str(fd),
                                                   str(tmp_path / "host.map"), str(PKG)])
    seen = []
    real_popen = subprocess.Popen

    def watching(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        seen.append(proc)
        return proc

    monkeypatch.setattr(subprocess, "Popen", watching)
    with pytest.raises(RuntimeError, match="planted"):
        client.spawn(10.0)
    assert seen and seen[0].poll() is not None and not pid_alive(seen[0].pid)


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


def test_main_starts_the_parent_watch_off_windows(monkeypatch):
    """The wiring in ``_worker.main`` (the fake worker starts its own watch, so only this test would notice a deleted
    line): ``main`` must start the watch once with the parent's pid. It stops at the missing host library, as a fatal."""
    import multiprocessing
    watched = []
    monkeypatch.delenv("LAZ_HOST", raising=False)
    monkeypatch.setattr(_worker, "start_parent_watch", lambda parent, *rest: watched.append(parent))
    monkeypatch.setattr(_worker, "raise_nice_floor", lambda *a: 10)
    monkeypatch.setattr(_worker, "set_error_mode", lambda: None)
    monkeypatch.setattr(_worker.faulthandler, "enable", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["worker"])
    ours, theirs = multiprocessing.Pipe(duplex=True)
    monkeypatch.setattr(_worker, "Connection", lambda fd: theirs, raising=False)
    monkeypatch.setattr(_worker, "PipeConnection", lambda fd: theirs, raising=False)
    try:
        assert _worker.main(theirs.fileno()) == 1
        kind, text = ours.recv()
        assert kind == "fatal" and "cannot load the host" in text
    finally:
        ours.close()
        theirs.close()
    assert watched == ([] if WIN else [os.getppid()])


# ---- live: the real emulator (PC) ----
LIVE_PARENT = textwrap.dedent('''
    import os, sys, time
    sys.path.insert(0, sys.argv[1])
    from libazahar import Emulator
    mode = sys.argv[4]
    if os.environ.get("LAZ_TEST_NO_JOB"):
        from libazahar import _job
        _job.assign = lambda proc: False
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
    except SlotTimeout:
        return False


@pytest.fixture
def one_slot(tmp_path, monkeypatch):
    folder = tmp_path / "slots"
    monkeypatch.setenv("LAZ_SLOT_DIR", str(folder))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "1")
    return folder


def live_case(host_paths, workdir, one_slot, mode: str, settle: float) -> None:
    parent = start_parent(LIVE_PARENT, str(host_paths.app), str(workdir), mode)
    if mode == "boot":          # kill after the host has begun its start (host.log exists), not during Python start-up
        text = ""
        begin = time.monotonic()
        while "pid=" not in text or not (workdir / "host.log").is_file():
            assert time.monotonic() - begin < 60, "no slot.txt or no host.log"
            time.sleep(0.05)
            text = (workdir / "slot.txt").read_text() if (workdir / "slot.txt").is_file() else ""
        worker = int(text.split("pid=")[1].split()[0])
    else:
        worker = read_pid(parent)
    with pytest.raises(SlotTimeout):            # the worker really holds the one slot before the kill
        _slots.acquire(timeout=0.5)
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


@pytest.mark.slow
@pytest.mark.skipif(not WIN, reason="the fallback matters where the job is the mid-batch guard")
def test_live_parent_death_between_batches_without_the_job(host_paths, workdir, one_slot, monkeypatch):
    monkeypatch.setenv("LAZ_TEST_NO_JOB", "1")
    live_case(host_paths, workdir, one_slot, "idle", 1.0)


def test_a_failing_kqueue_is_said_and_the_worker_goes_on(capsys):
    class Broken(FakeSelect):
        def kqueue(self):
            raise OSError(24, "Too many open files")

    exits = []
    assert _worker.wait_for_parent(os.getppid(), exits.append, Broken()) is False
    assert exits == [] and "no parent watch" in capsys.readouterr().err


def test_the_watch_says_why_it_exits(capsys):
    _worker.wait_for_parent(os.getppid(), lambda code: None, FakeSelect())
    assert "gone: exiting" in capsys.readouterr().err
