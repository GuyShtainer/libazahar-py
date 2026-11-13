"""The machine-wide slot cap, the slot-holding worker spawn and tools/hold_slot.py (no emulator)."""
import os
import signal
import subprocess
import sys
import time
import warnings
from pathlib import Path

import pytest

from libazahar import LoadWarning, SlotTimeout, _slots
from libazahar.errors import HostTimeout
from test_client import make

REPO = Path(__file__).resolve().parents[2]
HOLD = REPO / "tools" / "hold_slot.py"
SLEEPER = [sys.executable, "-I", "-c", "import time; time.sleep(60)"]


@pytest.fixture
def slots_env(tmp_path, monkeypatch):
    """A private slot folder with cap 3."""
    folder = tmp_path / "slots"
    monkeypatch.setenv("LAZ_SLOT_DIR", str(folder))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "3")
    return folder


def test_s1_cap_three_and_timeout(slots_env):
    held = [_slots.acquire() for _ in range(3)]
    assert sorted(slot.index for slot in held) == [0, 1, 2]
    begin = time.monotonic()
    with pytest.raises(SlotTimeout) as info:
        _slots.acquire(timeout=0.3)
    took = time.monotonic() - begin
    assert 0.3 <= took <= 1.0
    assert isinstance(info.value, HostTimeout) and info.value.op == "slot"
    assert str(slots_env) in str(info.value) and "all 3" in str(info.value)
    freed = held[1].index
    held[1].release()
    again = _slots.acquire(timeout=0.3)
    assert again.index == freed
    for slot in (held[0], held[2], again):
        slot.release()
    held[1].release()                   # idempotent


def test_s2_kill_frees_the_slot(tmp_path, monkeypatch):
    monkeypatch.setenv("LAZ_SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "1")
    slot = _slots.acquire()
    child = subprocess.Popen(SLEEPER, pass_fds=(slot.fd,))
    try:
        slot.release()
        with pytest.raises(SlotTimeout):
            _slots.acquire(timeout=0.3)
        begin = time.monotonic()
        os.kill(child.pid, signal.SIGKILL)
        child.wait()
        again = _slots.acquire(timeout=2)
        took = time.monotonic() - begin
        print(f"\nslot free {took:.3f} s after the kill", file=sys.stderr)
        assert took < 1.0
        again.release()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_s3_cap_from_the_environment(monkeypatch):
    for bad in ("0", "65", "x"):
        monkeypatch.setenv("LAZ_MAX_INSTANCES", bad)
        with pytest.raises(ValueError, match="LAZ_MAX_INSTANCES"):
            _slots.cap()
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "5")
    assert _slots.cap() == 5
    monkeypatch.delenv("LAZ_MAX_INSTANCES")
    assert _slots.cap() == _slots.DEFAULT_CAP
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "2")        # set after import: the next call sees it
    assert _slots.cap() == 2


def test_s4_modes(slots_env):
    slot = _slots.acquire()
    assert (slots_env.stat().st_mode & 0o777) == 0o700
    assert (slot.path.stat().st_mode & 0o777) == 0o600
    assert slot.path.stat().st_size == 0                # the lock is the state; nothing is written into it
    slot.release()


def test_s5_load_warning(slots_env, monkeypatch):
    monkeypatch.setattr(os, "getloadavg", lambda: (1000.0, 0.0, 0.0))
    with pytest.warns(LoadWarning, match="above 2 x"):
        _slots.acquire().release()
    monkeypatch.setattr(os, "getloadavg", lambda: (0.0, 0.0, 0.0))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _slots.acquire().release()


def test_s6_fake_worker_holds_the_slot(tmp_path, monkeypatch):
    monkeypatch.setenv("LAZ_SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "1")
    work = tmp_path / "w"
    client = make(work, "ok")
    plain = tmp_path / "plain"
    no_slot = make(plain, "ok")
    no_slot.spawn(10.0)                                  # no keyword: no slot, no slot.txt
    assert not (plain / "slot.txt").exists()
    _slots.acquire(timeout=0.3).release()                # the lock files are free
    no_slot.close()
    client = _with_slot(work)
    client.spawn(10.0)
    try:
        keys = dict(part.split("=") for part in (work / "slot.txt").read_text().split())
        assert set(keys) == {"slot", "pid", "acquired", "waited_s"} and int(keys["pid"]) == client.pid
        with pytest.raises(SlotTimeout):
            _slots.acquire(timeout=0.3)
    finally:
        client.close()
    _slots.acquire(timeout=2).release()                  # freed when the fake exited


def _with_slot(work):
    """The ``make`` client of test_client with ``slot=True``."""
    from libazahar._client import WorkerClient
    base = make(work, "ok")
    return WorkerClient(work, work / "host.map", work / "host.log", dict(os.environ), argv=base._argv, slot=True)


def test_s7_hold_slot_tool(tmp_path):
    env = dict(os.environ, LAZ_SLOT_DIR=str(tmp_path / "slots"), LAZ_MAX_INSTANCES="1")
    held = subprocess.Popen([sys.executable, "-I", str(HOLD), "--", *SLEEPER], env=env, stderr=subprocess.PIPE)
    try:
        lines = []
        for _ in range(6):                                      # a LoadWarning (2 lines) may come first
            lines.append(held.stderr.readline())
            if b"hold_slot:" in lines[-1]:
                break
        assert b"hold_slot: slot=0" in lines[-1], lines
        os.environ.update(LAZ_SLOT_DIR=env["LAZ_SLOT_DIR"], LAZ_MAX_INSTANCES="1")
        try:
            with pytest.raises(SlotTimeout):
                _slots.acquire(timeout=0.3)
            os.kill(held.pid, signal.SIGKILL)
            held.wait()
            _slots.acquire(timeout=2).release()
        finally:
            os.environ.pop("LAZ_SLOT_DIR"), os.environ.pop("LAZ_MAX_INSTANCES")
    finally:
        if held.poll() is None:
            held.kill()
            held.wait()
        held.stderr.close()
    bare = subprocess.run([sys.executable, "-I", str(HOLD), "--"], env=env, capture_output=True)
    assert bare.returncode == 2 and b"usage" in bare.stderr


def _rule(*totals_loads, ok=True):
    """Cap-core rows from (total fps, end load) pairs for n = 1, 2, ..."""
    return [{"n": i + 1, "total_host_fps": fps, "load_end": load, "check_ok": ok}
            for i, (fps, load) in enumerate(totals_loads)]


def test_speed_rule_cap_rule():
    import importlib.util
    spec = importlib.util.spec_from_file_location("speed_table", REPO / "tools" / "speed_table.py")
    table = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(table)
    assert table.cap_rule(_rule((100, 5), (180, 8), (260, 12), (340, 16)), 12)[0] == 4        # a clean climb
    assert table.cap_rule(_rule((100, 5), (110, 8), (130, 9), (140, 9)), 12)[0] == 1          # throughput stops at 1
    assert table.cap_rule(_rule((100, 5), (180, 8), (190, 9), (200, 9)), 12)[0] == 2          # throughput stops at 2
    assert table.cap_rule(_rule((100, 5), (180, 8), (260, 24), (340, 16)), 12)[0] == 2        # load stops the step to 3
    cap_now, reasons = table.cap_rule(_rule((100, 5), (180, 8), (260, 12), (340, 16), ok=False), 12)
    assert cap_now == 3 and "CHECK FAIL" in reasons[0]                                          # a failed check


def test_s7_pipe_failure_releases_the_slot(tmp_path, monkeypatch):
    """A failure between the acquire and the worker start (here Pipe, as with EMFILE) must free the slot."""
    monkeypatch.setenv("LAZ_SLOT_DIR", str(tmp_path / "slots"))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "1")

    def boom(*args, **kwargs):
        raise OSError("too many open files")

    monkeypatch.setattr("libazahar._client.multiprocessing.Pipe", boom)
    client = _with_slot(tmp_path / "w")
    with pytest.raises(OSError, match="too many open files"):
        client.spawn(10.0)
    _slots.acquire(timeout=0.3).release()                # the only slot is free again
