"""Windows: one Job object with kill-on-close that holds every worker, so a dead parent takes its workers with it.

The job is made at the first spawn and its handle lives until this process ends; when the process dies, however it
dies, Windows closes the handle and ends every worker in the job (docs/USING.md section 8). Where the job cannot be
made or the worker cannot be assigned, one warning is given and today's behaviour stays: the worker ends on the
pipe's EOF between batches only.
"""
from __future__ import annotations

import ctypes
import subprocess
import sys
import threading
import warnings
from typing import Optional

__all__ = ["assign"]

JobObjectExtendedLimitInformation = 9
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0001

_lock = threading.Lock()
_job: Optional[int] = None          # the job's HANDLE, kept open for the life of this process
_failed = False                     # one warning only


class _Basic(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes",
                                                     "OtherBytes")]


class _Extended(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _Basic), ("IoInfo", _IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


def _kernel32() -> ctypes.WinDLL:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    return kernel32


def _make_job(kernel32: "ctypes.WinDLL") -> int:
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    info = _Extended()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel32.SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ctypes.byref(info),
                                            ctypes.sizeof(info)):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "SetInformationJobObject failed")
    return int(handle)


def _warn(reason: str) -> None:
    global _failed
    if not _failed:
        _failed = True
        warnings.warn(f"libazahar: cannot put the worker in a kill-on-close job ({reason}); if this process is killed "
                      "mid-batch the worker may keep running until the batch ends", RuntimeWarning, stacklevel=3)


def assign(proc: subprocess.Popen) -> bool:
    """Put ``proc`` (a worker we just started) in the kill-on-close job. True when done; False after one warning. A
    no-op that returns False off Windows."""
    global _job
    if sys.platform != "win32":
        return False
    try:
        kernel32 = _kernel32()
        with _lock:
            if _job is None:
                _job = _make_job(kernel32)
            job = _job
        process = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, proc.pid)
        if not process:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")
        try:
            if not kernel32.AssignProcessToJobObject(job, process):
                raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
        finally:
            kernel32.CloseHandle(process)
    except OSError as exc:
        _warn(str(exc))
        return False
    return True
