"""B9 (item 829): the worker's open handles (Windows) or file descriptors (macOS, Linux) stay flat over many state
loads. Phase A measured about 2 extra Windows handles per load; the probe in LEAK-NOTES.md traced them to the core
(Semaphore objects made while it restores a state), so the Windows test is an expected failure until a core patch."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from libazahar import Emulator

pytestmark = pytest.mark.slow

LOADS = 60                     # about 130 leaked handles at today's rate, far over 5 % of the ~430 baseline
WARM = 10                      # loads before the baseline, so one-time allocations are not counted
TOLERANCE = 0.05


def open_handles(pid: int) -> int:
    """Open handles of the process ``pid`` (Windows), or its open file descriptors (macOS, Linux)."""
    if sys.platform == "win32":
        import ctypes
        import ctypes.wintypes as wt
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wt.HANDLE
        k32.GetProcessHandleCount.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
        k32.CloseHandle.argtypes = [wt.HANDLE]
        handle = k32.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")
        try:
            count = wt.DWORD()
            if not k32.GetProcessHandleCount(handle, ctypes.byref(count)):
                raise OSError(ctypes.get_last_error(), "GetProcessHandleCount failed")
            return int(count.value)
        finally:
            k32.CloseHandle(handle)
    if Path(f"/proc/{pid}/fd").is_dir():
        return len(os.listdir(f"/proc/{pid}/fd"))
    lsof = shutil.which("lsof")
    if lsof is None:
        pytest.skip("needs_core: no /proc and no lsof to count the worker's descriptors")
    out = subprocess.run([lsof, "-n", "-P", "-p", str(pid)], capture_output=True, text=True, check=False).stdout
    return max(0, len(out.splitlines()) - 1)


@pytest.mark.skipif(sys.platform != "win32", reason="the leak was measured on Windows; macOS runs the test below")
@pytest.mark.xfail(strict=True, reason="item 829: the core leaves about 2 Semaphore handles per state load "
                                       "(LEAK-NOTES.md); fixed only by a core patch, rebuilt in C6a")
def test_handles_flat_over_loads_windows(host_paths, workdir):
    check_flat(host_paths, workdir)


@pytest.mark.skipif(sys.platform == "win32", reason="the Windows variant is the one above")
def test_descriptors_flat_over_loads(host_paths, workdir):
    check_flat(host_paths, workdir)


def check_flat(host_paths, workdir: Path) -> None:
    with Emulator(host_paths.app, workdir / "leak") as emu:
        emu.run(60)
        state = workdir / "leak.state"
        emu.save_state(state)
        for _ in range(WARM):
            emu.load_state(state)
        emu.run(1)
        before = open_handles(emu.pid)
        for _ in range(LOADS):
            emu.load_state(state)
        emu.run(1)
        after = open_handles(emu.pid)
    assert after <= before * (1 + TOLERANCE), f"worker handles {before} -> {after} over {LOADS} loads"
