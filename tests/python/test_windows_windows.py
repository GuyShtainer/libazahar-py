"""B6 (docs/plans/phase-8.md): during a live run on Windows, no top-level window belongs to the worker or azhost.exe.

Every top-level window of the desktop is listed, hidden ones included. A positive control makes a hidden window of the
test's own first and requires the list to hold it, so the check cannot pass on an empty list.

Run: LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python/test_windows_windows.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Iterator, List, Set

import pytest

import d_helpers as dh

pytestmark = [pytest.mark.slow,
              pytest.mark.skipif(sys.platform != "win32", reason="Windows only: top-level windows are a Windows idea")]

RUN_FRAMES = 60
LONG_RUN_FRAMES = 600
AZHOST_FRAMES = 300
REPO = Path(__file__).resolve().parents[2]
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


def family_of(root: int) -> Set[int]:
    """``root`` and all its descendants, from one process snapshot."""
    table = process_table()
    family = {root}
    grew = True
    while grew:
        grew = False
        for pid, (parent, _) in table.items():
            if parent in family and pid not in family:
                family.add(pid)
                grew = True
    return family


class WindowWatch:
    """A thread that lists every top-level window over and over while a long call runs in the test's main thread."""

    def __init__(self, hwnd: int, root: int) -> None:
        self.hwnd, self.root = hwnd, root
        self.lists = 0
        self.control_missing = 0
        self.theirs: List[Dict[str, int]] = []
        self.error: List[BaseException] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        try:
            while not self._stop.is_set():
                owners = family_of(self.root)
                windows = top_level_windows()
                self.lists += 1
                if self.hwnd not in {w["hwnd"] for w in windows}:
                    self.control_missing += 1
                self.theirs += [w for w in windows if w["pid"] in owners]
                self._stop.wait(0.05)
        except BaseException as error:  # reported by check(), never lost in the thread
            self.error.append(error)

    def __enter__(self) -> "WindowWatch":
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(10)

    def check(self, what: str) -> None:
        assert not self.error, f"the window watch failed: {self.error[0]!r}"
        assert self.lists >= 3, f"{what}: the window list ran only {self.lists} times"
        assert self.control_missing == 0, f"{what}: the positive control was missing from {self.control_missing} lists"
        assert not self.theirs, f"{what}: windows owned by it: {self.theirs[:5]}"


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
    """Before a batch, during one long batch (listed from a thread) and after it, no top-level window, hidden or not,
    is the worker's or its descendants'."""
    with HiddenWindow() as hidden, dh.boot(host_paths, workdir, seed(ready_at=0)) as emu:
        emu.run(RUN_FRAMES)
        assert emu.pid in process_table(), "the worker is not a running process"
        owners = family_of(emu.pid)
        assert emu.pid in owners
        with WindowWatch(int(hidden.hwnd), emu.pid) as watch:
            emu.run(LONG_RUN_FRAMES)
        watch.check("worker, during a batch")
        windows = top_level_windows()
        assert int(hidden.hwnd) in {w["hwnd"] for w in windows}, "the positive control was not listed"
        assert not [w for w in windows if w["pid"] in owners]


def test_no_window_belongs_to_azhost(host_paths, tmp_path):
    """The real azhost.exe runs the test app for a short time; neither it nor its children own a window."""
    exe = REPO / "build" / "azhost.exe"
    if not exe.is_file():
        pytest.skip("needs_core: build/azhost.exe is missing (run make)")
    cmd = [str(exe), "run", str(host_paths.app), "--core", str(host_paths.core), "--sys", str(tmp_path / "sys"),
           "--out", str(tmp_path / "out"), "--frames", str(AZHOST_FRAMES)]
    with HiddenWindow() as hidden:
        proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            with WindowWatch(int(hidden.hwnd), proc.pid) as watch:
                deadline = time.monotonic() + 240
                while proc.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait(30)
    assert proc.returncode == 0, f"azhost.exe exited {proc.returncode}"
    watch.check("azhost.exe")


def test_focus_is_not_taken(host_paths, workdir, seed):
    """The foreground window is the same before the boot and after a run (meaningful on a logged-in desktop only)."""
    if not interactive_session():
        pytest.skip("not an interactive desktop session (SSH or a service): the foreground window means nothing here")
    before = foreground()
    with dh.boot(host_paths, workdir, seed(ready_at=0)) as emu:
        emu.run(RUN_FRAMES)
        during = foreground()
    assert (before, during) == (before, before) and foreground() == before
