"""The worker process: one libazhost instance, driven over a pipe (docs/plans/phase-d.md 4.3).

Started by ``_client.py`` as ``python -I -c ... main(fd)``. Every request is one ctypes call (except ``start``).
"""
from __future__ import annotations

import ctypes
import faulthandler
import os
import sys
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from . import _abi, _host
from .errors import HostCallError, LibAzaharError

__all__ = ["main", "option_plan"]

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
    core, sysdir, log, mapfile, options, app, state, lazpy_options = args
    _host.call(lib, "azh_open", _c_str(core), _c_str(sysdir), _c_str(log), _c_str(mapfile))
    for key, value in option_plan(_stats(lib)["is_lazpy_core"], lazpy_options, options):
        _host.call(lib, "azh_set_option", _c_str(key), _c_str(value))
    _host.call(lib, "azh_boot", _c_str(app), _c_str(state) if state else None)
    return _stats(lib)


def _stats(lib: ctypes.CDLL) -> Dict[str, Any]:
    out = _abi.Stats()
    _host.call(lib, "azh_stats", ctypes.byref(out))
    return {"frames": out.frames, "wall_s": out.wall_s, "user_s": out.user_s, "sys_s": out.sys_s,
            "peak_rss": out.peak_rss, "core_name": out.core_name.decode("utf-8", "replace"),
            "core_version": out.core_version.decode("utf-8", "replace"), "is_lazpy_core": bool(out.is_lazpy_core)}


def _op_run(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> bytes:
    records, batch_bytes = args
    count = len(records) // _REC_BYTES
    buf = ctypes.create_string_buffer(bytes(records), max(len(records), 1))
    batch = _abi.Batch.from_buffer_copy(batch_bytes)
    result = _abi.Result()
    _host.call(lib, "azh_run", ctypes.cast(buf, ctypes.c_void_p) if count else None, count, ctypes.byref(batch),
               ctypes.byref(result))
    return bytes(result)


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


def _serve(conn: Connection, lib: ctypes.CDLL) -> int:
    """The bounded request loop; ends on ``close`` or on EOF."""
    for _ in range(MAX_REQUESTS):
        try:
            op, args = conn.recv()
        except EOFError:
            return 0
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
        conn.send(tuple(reply))
        if op == "close":
            return 0
    return 1


def raise_nice_floor(floor: int = 10) -> int:
    """At least nice 10: raise only when the parent is nicer. getpriority/setpriority, because os.nice(0) raises EPERM at nice 20 on macOS."""
    now = os.getpriority(os.PRIO_PROCESS, 0)
    if now < floor:
        os.setpriority(os.PRIO_PROCESS, 0, floor)
        now = floor
    return now


def main(fd: int) -> int:
    """Worker entry: nice at least 10, faulthandler, hello (or fatal), then the request loop. Returns the exit code."""
    faulthandler.enable()
    if len(sys.argv) > 3:               # the slot's lock fd (argv[3]): keep it here, never hand it to a child
        os.set_inheritable(int(sys.argv[3]), False)
    conn = Connection(fd)
    try:
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
