"""The worker process: one libazhost instance, driven over a pipe (docs/plans/phase-d.md 4.3).

Started by ``_client.py`` as ``python -I -c ... main(fd)``. Every request is one ctypes call (except ``start``).
"""
from __future__ import annotations

import ctypes
import faulthandler
import os
import select
import sys
import threading
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import _abi, _host
from .errors import HostCallError, LibAzaharError

__all__ = ["main", "option_plan"]

_WIN = sys.platform == "win32"
if _WIN:
    from multiprocessing.connection import PipeConnection
MAX_REQUESTS = 1 << 40
_REC_BYTES = 4 * _abi.AZH_INPUT_INTS


def _c_str(text: str) -> bytes:
    return text.encode("utf-8")


def option_plan(is_lazpy: bool, lazpy_options: Sequence[Tuple[str, str]],
                options: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """The order options are set in: our core's own lines first (only on our core, the stock core refuses them), then
    the profile and the caller's options (later wins)."""
    return (list(lazpy_options) if is_lazpy else []) + list(options)


def _op_start(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> Any:
    core, sysdir, log, mapfile, options, app, state, lazpy_options = args[:8]
    movie = args[8] if len(args) > 8 else None
    _host.call(lib, "azh_open", _c_str(core), _c_str(sysdir), _c_str(log), _c_str(mapfile))
    for key, value in option_plan(_stats(lib)["is_lazpy_core"], lazpy_options, options):
        _host.call(lib, "azh_set_option", _c_str(key), _c_str(value))
    if movie:
        _host.call(lib, "azh_movie_play", _c_str(movie))
    _host.call(lib, "azh_boot", _c_str(app), _c_str(state) if state else None)
    return _stats(lib)


def _stats(lib: ctypes.CDLL) -> Dict[str, Any]:
    out = _abi.Stats()
    _host.call(lib, "azh_stats", ctypes.byref(out))
    return {"frames": out.frames, "wall_s": out.wall_s, "user_s": out.user_s, "sys_s": out.sys_s,
            "peak_rss": out.peak_rss, "core_name": out.core_name.decode("utf-8", "replace"),
            "core_version": out.core_version.decode("utf-8", "replace"), "is_lazpy_core": bool(out.is_lazpy_core)}


def _op_run(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> Any:
    """One batch. With a third argument (a file path) the batch's audio is captured there and the reply is
    ``(result bytes, stereo frames, rate)``; without it the reply is the result bytes alone."""
    records, batch_bytes = args[0], args[1]
    audio_path = args[2] if len(args) > 2 else None
    count = len(records) // _REC_BYTES
    buf = ctypes.create_string_buffer(bytes(records), max(len(records), 1))
    batch = _abi.Batch.from_buffer_copy(batch_bytes)
    result = _abi.Result()
    if audio_path:
        _host.call(lib, "azh_audio_capture", _c_str(audio_path))
    try:
        _host.call(lib, "azh_run", ctypes.cast(buf, ctypes.c_void_p) if count else None, count, ctypes.byref(batch),
                   ctypes.byref(result))
        if not audio_path:
            return bytes(result)
        frames, rate = ctypes.c_int64(0), ctypes.c_int32(0)
        _host.call(lib, "azh_audio_info", ctypes.byref(frames), ctypes.byref(rate))
        return bytes(result), int(frames.value), int(rate.value)
    finally:
        if audio_path:
            lib.azh_audio_capture(None)     # stop and close the file; a failure here must not hide the real error


def _op_set_input(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> None:
    (record,) = args
    rec = (ctypes.c_int32 * _abi.AZH_INPUT_INTS)(*record)
    _host.call(lib, "azh_set_input", rec)


def _op_shot(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> None:
    screens, fmt, prefix = args
    _host.call(lib, "azh_shot", screens, fmt, _c_str(prefix) if prefix else None)


def _op_save_state(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> int:
    k = ctypes.c_int32(0)
    _host.call(lib, "azh_save_state", _c_str(args[0]), ctypes.byref(k))
    return int(k.value)


def _op_load_state(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> None:
    _host.call(lib, "azh_load_state", _c_str(args[0]))


def _op_read(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> bytes:
    addr, length = args
    buf = ctypes.create_string_buffer(length)
    _host.call(lib, "azh_read", addr, length, ctypes.cast(buf, ctypes.c_void_p))
    return buf.raw


def _op_write(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> None:
    addr, data = args
    buf = ctypes.create_string_buffer(bytes(data), max(len(data), 1))
    _host.call(lib, "azh_write", addr, len(data), ctypes.cast(buf, ctypes.c_void_p))


def _op_threads(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> bytes:
    """Every guest thread as packed azh_thread records; retries with the host's count when the buffer was short."""
    cap = 64
    for _ in range(4):
        buf = (_abi.Thread * cap)()
        count = ctypes.c_int32(0)
        _host.call(lib, "azh_threads", ctypes.cast(buf, ctypes.c_void_p), cap, ctypes.byref(count))
        if 0 <= count.value <= cap:
            return bytes(buf)[: count.value * ctypes.sizeof(_abi.Thread)]
        cap = count.value
    raise ValueError("the guest's thread count kept growing between calls")


def _op_stats(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> Dict[str, Any]:
    return _stats(lib)


def _op_close(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> None:
    _host.call(lib, "azh_close")


_OPS = {"start": _op_start, "run": _op_run, "set_input": _op_set_input, "shot": _op_shot,
        "save_state": _op_save_state, "load_state": _op_load_state, "read": _op_read, "write": _op_write,
        "threads": _op_threads, "stats": _op_stats, "close": _op_close}


def _leave(code: int = 0) -> int:
    """End on the parent's death (EOF or a broken pipe). Windows: ``hard_exit``, as after ``close``, because the DLL
    detach of the core and the GPU driver can hang; elsewhere return so ``main`` ends normally."""
    if _WIN:
        hard_exit(code)
    return code


def _serve(conn: Connection, lib: ctypes.CDLL) -> int:
    """The bounded request loop; ends on ``close`` or on EOF."""
    for _ in range(MAX_REQUESTS):
        try:
            op, args = conn.recv()
        except (EOFError, OSError):
            return _leave()
        handler = _OPS.get(op)
        if handler is None:
            conn.send(("err", _abi.AZH_E_ARG, f"unknown op {op!r}"))
            continue
        try:
            reply: List[Any] = ["ok", handler(lib, tuple(args))]
        except HostCallError as exc:
            reply = ["err", exc.code, exc.text]
        except (ctypes.ArgumentError, TypeError, ValueError) as exc:
            reply = ["err", _abi.AZH_E_ARG, f"{op}: {exc}"]
        try:
            conn.send(tuple(reply))
        except (BrokenPipeError, OSError):
            return _leave()
        if op == "close":
            if _WIN:
                hard_exit()             # only now: azh_close has run and its reply is in the pipe
            return 0
    return 1


def _say(text: str) -> None:
    """One line to stderr (it lands in ``worker.err``)."""
    try:
        print(f"libazahar worker: {text}", file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass


def wait_for_parent(parent: int, exit_now: Callable[[int], Any] = os._exit, sel: Any = select) -> bool:
    """macOS and the BSDs: block until process ``parent`` exits (``kqueue``, ``EVFILT_PROC`` with ``NOTE_EXIT``), then
    call ``exit_now(0)``. The parent is rechecked with ``getppid`` after the registration, so an exit between the start
    and the registration is not missed. Returns False at once, without waiting, where there is no ``kqueue``, or when
    the queue cannot be made (said on stderr; the worker then ends on the pipe's EOF between batches only)."""
    if not hasattr(sel, "kqueue"):
        return False
    if parent <= 1:                             # the parent died before the worker started: it was reparented
        _say(f"parent {parent} gone: exiting")
        exit_now(0)
        return True
    try:
        queue = sel.kqueue()
    except OSError as exc:                      # for example EMFILE
        _say(f"no parent watch ({exc}); the worker will end on EOF between batches only")
        return False
    event = sel.kevent(parent, filter=sel.KQ_FILTER_PROC, flags=sel.KQ_EV_ADD | sel.KQ_EV_ONESHOT,
                       fflags=sel.KQ_NOTE_EXIT)
    try:
        queue.control([event], 0, 0)            # register only
    except ProcessLookupError:                  # the parent is already gone
        _say(f"parent {parent} gone: exiting")
        exit_now(0)
        return True
    if os.getppid() != parent:
        _say(f"parent {parent} gone: exiting")
        exit_now(0)
        return True
    queue.control(None, 1, None)                # blocks until the exit (the GIL is free while it waits)
    _say(f"parent {parent} gone: exiting")
    exit_now(0)
    return True


def start_parent_watch(parent: int, exit_now: Callable[[int], Any] = os._exit,
                       sel: Any = select) -> Optional[threading.Thread]:
    """Start the daemon thread that runs ``wait_for_parent``; None where there is no ``kqueue``. ctypes releases the
    GIL during a batch, so the thread fires mid-batch."""
    if not hasattr(sel, "kqueue"):
        return None
    thread = threading.Thread(target=wait_for_parent, args=(parent, exit_now, sel), name="parent-watch", daemon=True)
    thread.start()
    return thread


def hard_exit(code: int = 0) -> None:
    """Windows: ``TerminateProcess(GetCurrentProcess(), code)``. It skips the DLL detach of the core and the GPU driver,
    which can hang on exit. Call it only after the ``close`` reply has been written to the pipe (``azh_close`` ran
    first). The slot HANDLE closes with the process."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (OSError, ValueError, AttributeError):
            pass
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel32.TerminateProcess(kernel32.GetCurrentProcess(), code)


def set_error_mode() -> None:
    """Windows: no crash dialog, no error box (FAILCRITICALERRORS | NOGPFAULTERRORBOX | NOOPENFILEERRORBOX)."""
    ctypes.WinDLL("kernel32").SetErrorMode(0x0001 | 0x0002 | 0x8000)


def raise_nice_floor(floor: int = 10) -> int:
    """At least nice 10: raise only when the parent is nicer. getpriority/setpriority, because os.nice(0) raises EPERM at nice 20 on macOS."""
    now = os.getpriority(os.PRIO_PROCESS, 0)
    if now < floor:
        os.setpriority(os.PRIO_PROCESS, 0, floor)
        now = floor
    return now


def main(fd: int) -> int:
    """Worker entry: nice at least 10, faulthandler, hello (or fatal), then the request loop. Returns the exit code."""
    if _WIN:
        set_error_mode()
    faulthandler.enable()
    if not _WIN:
        start_parent_watch(os.getppid())
    if len(sys.argv) > 3:               # the slot's lock fd (argv[3]): keep it here, never hand it to a child
        if _WIN:
            os.set_handle_inheritable(int(sys.argv[3]), False)
        else:
            os.set_inheritable(int(sys.argv[3]), False)
    conn = PipeConnection(fd) if _WIN else Connection(fd)      # Windows: fd is the pipe's HANDLE
    try:
        if not _WIN:                    # Windows: the priority class comes from the parent's creationflags
            raise_nice_floor()
    except OSError as exc:
        conn.send(("fatal", f"cannot set the worker's nice value: {exc}"))
        return 1
    try:
        lib, layout = _host.load(Path(os.environ["LAZ_HOST"]))
    except (OSError, KeyError, HostCallError, LibAzaharError) as exc:
        conn.send(("fatal", f"cannot load the host: {exc}"))
        return 1
    conn.send(("hello", int(layout.n_fields)))
    return _serve(conn, lib)
