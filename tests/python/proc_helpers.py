"""Process helpers that behave the same on POSIX and Windows (``os.kill(pid, 0)`` TERMINATES a process on Windows)."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
from typing import List, Sequence

WIN = sys.platform == "win32"
STILL_ACTIVE = 259
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_TERMINATE = 0x0001


def pid_alive(pid: int) -> bool:
    """True while the process runs (a zombie reaped by nobody still counts on POSIX, as with ``os.kill(pid, 0)``)."""
    if not WIN:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_uint()
        return bool(kernel32.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code))) and code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def hard_kill(pid: int) -> None:
    """SIGKILL on POSIX; TerminateProcess with exit code 1 on Windows (a pid of ours only). Never ``os.kill`` there:
    signals 0 and 1 are CTRL_C_EVENT and CTRL_BREAK_EVENT, which hit a whole console group."""
    if not WIN:
        os.kill(pid, signal.SIGKILL)
        return
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not handle:
        raise OSError(f"OpenProcess({pid}) failed: {ctypes.get_last_error()}")
    try:
        kernel32.TerminateProcess(ctypes.c_void_p(handle), 1)
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def suspend(pid: int) -> None:
    """SIGSTOP on POSIX; ``NtSuspendProcess`` on Windows (a pid of ours only)."""
    if not WIN:
        os.kill(pid, signal.SIGSTOP)
        return
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if not handle:
        raise OSError(f"OpenProcess({pid}) failed: {ctypes.get_last_error()}")
    try:
        ctypes.WinDLL("ntdll").NtSuspendProcess(ctypes.c_void_p(handle))
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def popen_holding(argv: Sequence[str], handle: int, **kwargs) -> subprocess.Popen:
    """Start ``argv`` so that only ``handle`` (a slot's fd, a HANDLE number on Windows) reaches it."""
    if not WIN:
        return subprocess.Popen(list(argv), pass_fds=(handle,), **kwargs)
    os.set_handle_inheritable(handle, True)
    try:
        info = subprocess.STARTUPINFO(lpAttributeList={"handle_list": [handle]})
        return subprocess.Popen(list(argv), close_fds=True, startupinfo=info, **kwargs)
    finally:
        os.set_handle_inheritable(handle, False)


def base_python() -> str:
    """The interpreter a spawned worker runs on (the base ``python.exe`` on Windows, never a venv launcher)."""
    from libazahar._client import worker_python
    return worker_python()


def sleeper() -> List[str]:
    """A command that sleeps 60 s."""
    return [base_python(), "-I", "-c", "import time; time.sleep(60)"]
