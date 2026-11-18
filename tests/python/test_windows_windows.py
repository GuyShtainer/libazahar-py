"""B6 (docs/plans/phase-8.md): during a live run on Windows, no top-level window belongs to the worker.

Every top-level window of the desktop is listed, hidden ones included. A positive control makes a hidden window of the
test's own first and requires the list to hold it, so the check cannot pass on an empty list.

Run: LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python/test_windows_windows.py
"""
from __future__ import annotations

import os
import sys
from typing import Dict, Iterator, List, Set

import pytest

import d_helpers as dh

pytestmark = [pytest.mark.slow,
              pytest.mark.skipif(sys.platform != "win32", reason="Windows only: top-level windows are a Windows idea")]

RUN_FRAMES = 60
TH32CS_SNAPPROCESS = 2
WS_POPUP = 0x80000000
UOI_NAME = 2
INTERACTIVE_STATION = "WinSta0"


def _api():
    """ctypes handles for user32 and kernel32 with the argument types the calls here need."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                      ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
                                      wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    return ctypes, wintypes, user32, kernel32, enum_proc


def top_level_windows() -> List[Dict[str, int]]:
    """Every top-level window of this window station, hidden ones included, as ``{"hwnd", "pid", "visible"}``."""
    ctypes, wintypes, user32, _, enum_proc = _api()
    found: List[Dict[str, int]] = []

    def collect(hwnd, _lparam):
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        found.append({"hwnd": int(hwnd or 0), "pid": pid.value, "visible": int(bool(user32.IsWindowVisible(hwnd)))})
        return True

    assert user32.EnumWindows(enum_proc(collect), 0), f"EnumWindows failed: {ctypes.get_last_error()}"
    return found


def process_table() -> Dict[int, tuple]:
    """``{pid: (parent pid, exe name)}`` for every process (a toolhelp snapshot)."""
    ctypes, wintypes, _, kernel32, _ = _api()

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Process32FirstW.argtypes = kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    assert snap not in (None, wintypes.HANDLE(-1).value), "CreateToolhelp32Snapshot failed"
    table: Dict[int, tuple] = {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(ProcessEntry)
        more = kernel32.Process32FirstW(snap, ctypes.byref(entry))
        while more:
            table[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile)
            more = kernel32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snap)
    return table


def worker_pids(worker: int) -> Set[int]:
    """The worker, its descendants, and every azhost.exe that is a child of this test process."""
    table = process_table()
    family = {worker}
    grew = True
    while grew:
        grew = False
        for pid, (parent, _) in table.items():
            if parent in family and pid not in family:
                family.add(pid)
                grew = True
    family |= {pid for pid, (parent, exe) in table.items() if exe.lower() == "azhost.exe" and parent == os.getpid()}
    return family


class HiddenWindow:
    """A window of this process that is never shown: the positive control."""

    def __enter__(self) -> "HiddenWindow":
        ctypes, _, user32, _, _ = _api()
        self.hwnd = user32.CreateWindowExW(0, "STATIC", "lazpy-positive-control", WS_POPUP, 0, 0, 10, 10, None, None,
                                           None, None)
        assert self.hwnd, f"CreateWindowExW failed: {ctypes.get_last_error()}"
        return self

    def __exit__(self, *exc: object) -> None:
        _api()[2].DestroyWindow(self.hwnd)


def interactive_session() -> bool:
    """True when this process runs on the interactive window station (a logged-in desktop), not over SSH."""
    ctypes, wintypes, user32, _, _ = _api()
    user32.GetProcessWindowStation.restype = wintypes.HANDLE
    user32.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
                                                  ctypes.POINTER(wintypes.DWORD)]
    name = ctypes.create_unicode_buffer(256)
    need = wintypes.DWORD(0)
    if not user32.GetUserObjectInformationW(user32.GetProcessWindowStation(), UOI_NAME, name, 512, ctypes.byref(need)):
        return False
    return name.value == INTERACTIVE_STATION and "SSH_CONNECTION" not in os.environ


def foreground() -> int:
    return int(_api()[2].GetForegroundWindow() or 0)


def test_positive_control_is_found():
    """The listing sees a hidden window of ours, so an empty result cannot pass the real test."""
    with HiddenWindow() as hidden:
        mine = [w for w in top_level_windows() if w["hwnd"] == int(hidden.hwnd)]
    assert len(mine) == 1 and mine[0]["pid"] == os.getpid() and mine[0]["visible"] == 0


def test_no_window_belongs_to_the_worker(host_paths, workdir, seed):
    """During a live run (before, mid-run and after a batch) no top-level window, hidden or not, is the worker's."""
    with HiddenWindow() as hidden, dh.boot(host_paths, workdir, seed(ready_at=0)) as emu:
        emu.run(RUN_FRAMES)
        owners = worker_pids(emu.pid)
        assert emu.pid in owners
        assert emu.pid in process_table(), "the worker is not a running process"
        for _ in range(2):
            windows = top_level_windows()
            assert int(hidden.hwnd) in {w["hwnd"] for w in windows}, "the positive control was not listed"
            theirs = [w for w in windows if w["pid"] in owners]
            assert not theirs, f"windows owned by the worker {sorted(owners)}: {theirs}"
            emu.run(RUN_FRAMES)


def test_focus_is_not_taken(host_paths, workdir, seed):
    """The foreground window is the same before the boot and after a run (meaningful on a logged-in desktop only)."""
    if not interactive_session():
        pytest.skip("not an interactive desktop session (SSH or a service): the foreground window means nothing here")
    before = foreground()
    with dh.boot(host_paths, workdir, seed(ready_at=0)) as emu:
        emu.run(RUN_FRAMES)
        during = foreground()
    assert (before, during) == (before, before) and foreground() == before
