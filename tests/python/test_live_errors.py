"""Crash, stall and long-batch behaviour against a live worker (signals go only to our own worker's pid)."""
from __future__ import annotations

import os
import signal
import sys
import threading
import time

import pytest

import d_helpers as dh
from libazahar import HostCrashed, HostTimeout

pytestmark = pytest.mark.slow


def test_sigsegv_raises_host_crashed_fast(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        killed = []

        def hit() -> None:
            killed.append(time.monotonic())
            os.kill(emu.pid, signal.SIGSEGV)

        timer = threading.Timer(3.0, hit)
        timer.start()
        try:
            with pytest.raises(HostCrashed) as caught:
                emu.run(10_000_000)
        finally:
            timer.cancel()
        delay = time.monotonic() - killed[0]
        print(f"SIGSEGV: kill to raise {delay:.3f} s", file=sys.stderr)
        assert caught.value.signal == signal.SIGSEGV and delay < 1.0 and emu.closed


def test_sigstop_raises_host_timeout(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        emu.run(300)
        pid = emu.pid
        stopped = []

        def hit() -> None:
            stopped.append(time.monotonic())
            os.kill(pid, signal.SIGSTOP)

        timer = threading.Timer(2.0, hit)
        timer.start()
        try:
            with pytest.raises(HostTimeout):
                emu.run(10_000_000, timeout=3)
        finally:
            timer.cancel()
        delay = time.monotonic() - stopped[0]
        print(f"SIGSTOP: stop to raise {delay:.2f} s", file=sys.stderr)
        assert 2.8 <= delay <= 6.0
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def test_long_batch(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        result = emu.run(200_000)
        print(f"long batch: {result.frames} frames in {result.wall_s:.1f} s", file=sys.stderr)
        assert result.stopped_by == "frames" and result.frames == 200_000
