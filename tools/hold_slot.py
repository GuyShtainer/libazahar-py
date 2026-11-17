#!/usr/bin/env python3
"""Hold one libazahar slot of the machine-wide cap, then exec a command (docs/plans/phase-e.md 3.5).

    python3 -I tools/hold_slot.py [--timeout S] -- CMD [ARG...]

The lock lives on in the command's process and dies with it. Exit 2 with a usage line when no command follows
``--``. Step G's gate and the phase-end suite run azhost commands under it.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from libazahar import _slots  # noqa: E402

USAGE = "usage: hold_slot.py [--timeout S] -- CMD [ARG...]"


def parse(argv):
    """(timeout or None, command list), or None for a usage error."""
    args = list(argv)
    timeout = None
    if len(args) >= 2 and args[0] == "--timeout":
        try:
            timeout = float(args[1])
        except ValueError:
            return None
        args = args[2:]
    if not args or args[0] != "--" or len(args) < 2:
        return None
    return timeout, args[1:]


def run_windows(command, slot):
    """Windows has no exec: start the command with ONLY the slot handle inherited (PROC_THREAD_ATTRIBUTE_HANDLE_LIST),
    close our copy at once, and wait. A kill-on-close Job Object ties the command to this process, so killing
    hold_slot kills the command and the slot comes back, as when an exec'd command dies. Returns its exit code."""
    import ctypes
    import ctypes.wintypes as wt
    import subprocess

    class Counters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("rd_ops", "wr_ops", "other_ops", "rd_bytes", "wr_bytes", "other_bytes")]

    class Basic(ctypes.Structure):
        _fields_ = [("per_process_time", ctypes.c_int64), ("per_job_time", ctypes.c_int64), ("flags", wt.DWORD),
                    ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t), ("active_limit", wt.DWORD),
                    ("affinity", ctypes.c_size_t), ("priority", wt.DWORD), ("sched", wt.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", Counters), ("process_mem", ctypes.c_size_t), ("job_mem", ctypes.c_size_t),
                    ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wt.HANDLE
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
    kernel32.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
    kernel32.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    job = kernel32.CreateJobObjectW(None, None)
    limits = Extended()
    limits.basic.flags = 0x2000                         # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not job or not kernel32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        raise ctypes.WinError(ctypes.get_last_error())
    os.set_handle_inheritable(slot.fd, True)
    try:
        info = subprocess.STARTUPINFO(lpAttributeList={"handle_list": [slot.fd]})
        child = subprocess.Popen(command, close_fds=True, startupinfo=info)
    finally:
        os.set_handle_inheritable(slot.fd, False)
    # The slot goes first: the parent never holds the lock after the spawn, and a failed assign below must not keep it.
    slot.release()
    if not kernel32.AssignProcessToJobObject(job, int(child._handle)):
        error = ctypes.WinError(ctypes.get_last_error())
        child.kill()                                    # without the job it could outlive us, with its own children
        child.wait()
        raise error
    return child.wait()


def main(argv):
    """Acquire a slot, make only its fd inheritable, exec the command (does not return on success)."""
    parsed = parse(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2
    timeout, command = parsed
    slot = _slots.acquire(timeout)
    print(f"hold_slot: slot={slot.index} waited_s={slot.waited_s:.3f}", file=sys.stderr, flush=True)
    if sys.platform == "win32":
        return run_windows(command, slot)
    os.set_inheritable(slot.fd, True)
    os.execvp(command[0], command)
    return 127


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
