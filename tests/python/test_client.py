"""WorkerClient against the fake worker (no emulator)."""
import os
import signal
import sys
import time
from pathlib import Path

import pytest

from libazahar import _map
from libazahar._client import Wait, WorkerClient, worker_python
from libazahar.errors import GuestError, HostCrashed, HostError, HostTimeout
from proc_helpers import WIN, pid_alive

FAKE = Path(__file__).resolve().parent / "fakeworker.py"
PKG = Path(__file__).resolve().parents[2] / "python"
RUN = Wait(heartbeat=5.0, first_heartbeat=5.0)


def make(workdir, mode):
    def argv(fd):
        return [worker_python(), "-I", str(FAKE), mode, str(fd), str(workdir / "host.map"), str(PKG)]
    client = WorkerClient(workdir, workdir / "host.map", workdir / "host.log", dict(os.environ), argv=argv)
    return client


def started(tmp_path, mode):
    client = make(tmp_path, mode)
    client.spawn(10.0)
    return client


def alive(pid):
    return pid_alive(pid)


def test_round_trip_times(tmp_path):
    client = started(tmp_path, "ok")
    begin = time.perf_counter()
    for _ in range(200):
        assert client.request("echo", ("x",), Wait(total=5.0)) == ("ok", ("x",))
    per_call = (time.perf_counter() - begin) / 200
    hostmap = client.host_map()
    begin = time.perf_counter()
    for _ in range(20):
        data = bytes(hostmap.pixels(1)) + bytes(hostmap.pixels(2))
    per_copy = (time.perf_counter() - begin) / 20
    print(f"\nfake round trip mean {per_call * 1e3:.3f} ms; 691,200-byte map copy mean {per_copy * 1e3:.3f} ms",
          file=sys.stderr)
    assert len(data) == 691200
    client.close()
    client.close()
    assert client.closed and not alive(client.pid)


def test_exit10_during_run_gives_frames_from_the_map(tmp_path):
    client = started(tmp_path, "exit10")
    kind, info = client.request("run", (), RUN, frame_before=0)
    assert kind == "exited" and info["frames"] == 7 and info["message"] == "boom" and client.closed


def test_exit10_during_save_state_is_a_host_error(tmp_path):
    client = started(tmp_path, "exit10")
    with pytest.raises(HostError, match="exited during save_state"):
        client.request("save_state", ("p",), Wait(total=5.0))
    assert client.closed


def test_exit11_is_guest_error(tmp_path):
    client = started(tmp_path, "exit11")
    with pytest.raises(GuestError, match="Fatal Error"):
        client.request("run", (), RUN)
    assert client.closed


def test_segv_is_host_crashed_within_a_second(tmp_path):
    client = started(tmp_path, "segv")
    with pytest.raises(HostCrashed) as caught:
        client.request("run", (), RUN)
    raised = time.time()
    died = float(Path(str(tmp_path / "host.map") + ".died").read_text())
    print(f"\nsegv: death to raise {raised - died:.3f} s", file=sys.stderr)
    if WIN:                                             # no signals: the NTSTATUS is the exit code
        assert caught.value.signal is None and caught.value.returncode == 0xC0000005
    else:
        assert caught.value.signal == signal.SIGSEGV
    assert raised - died < 1.0 and not alive(client.pid)


def test_hang_times_out_and_reaps(tmp_path):
    client = started(tmp_path, "hang")
    pid = client.pid
    with pytest.raises(HostTimeout):
        client.request("run", (), Wait(heartbeat=1.0, first_heartbeat=1.0))
    raised = time.time()
    stopped = float(Path(str(tmp_path / "host.map") + ".stopped").read_text())
    print(f"\nhang: heartbeat stop to raise {raised - stopped:.2f} s", file=sys.stderr)
    assert 0.8 <= raised - stopped <= 4.0
    assert not alive(pid)


def test_die_at_start(tmp_path):
    client = make(tmp_path, "die_at_start")
    with pytest.raises(HostCrashed) as caught:
        client.spawn(10.0)
    assert caught.value.message is None and caught.value.returncode == 3


def test_eof_goes_to_death_mapping(tmp_path):
    client = started(tmp_path, "eof")
    with pytest.raises(HostCrashed) as caught:
        client.request("run", (), RUN)
    assert caught.value.returncode == 0 and client.closed


def test_closed_client_refuses(tmp_path):
    client = started(tmp_path, "ok")
    client.close()
    with pytest.raises(HostError, match="closed"):
        client.request("echo", (), Wait(total=1.0))


@pytest.mark.skipif(not WIN, reason="the Windows priority class")
def test_windows_worker_runs_below_normal(tmp_path):
    """The Windows twin of the worker's nice 10: the parent starts it BELOW_NORMAL (0x4000)."""
    import ctypes
    client = started(tmp_path, "ok")
    try:
        kernel32 = ctypes.WinDLL("kernel32")
        kernel32.GetPriorityClass.argtypes = [ctypes.c_void_p]
        assert kernel32.GetPriorityClass(int(client.proc._handle)) == 0x4000
    finally:
        client.close()
