"""The worker process: one libazhost instance, driven over a pipe (docs/plans/phase-d.md 4.3).

Started by ``_client.py`` as ``python -I -c ... main(fd)``. Every request is one ctypes call (except ``start``).
"""
from __future__ import annotations

import ctypes
import faulthandler
import os
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import _abi, _host
from .errors import HostCallError, LibAzaharError

__all__ = ["main"]

MAX_REQUESTS = 1 << 40
_REC_BYTES = 4 * _abi.AZH_INPUT_INTS


def _c_str(text: str) -> bytes:
    return text.encode("utf-8")


def _op_start(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> Any:
    core, sysdir, log, mapfile, options, app, state = args
    _host.call(lib, "azh_open", _c_str(core), _c_str(sysdir), _c_str(log), _c_str(mapfile))
    for key, value in options:
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


def _op_stats(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> Dict[str, Any]:
    return _stats(lib)


def _op_close(lib: ctypes.CDLL, args: Tuple[Any, ...]) -> None:
    _host.call(lib, "azh_close")


_OPS = {"start": _op_start, "run": _op_run, "set_input": _op_set_input, "shot": _op_shot,
        "save_state": _op_save_state, "load_state": _op_load_state, "stats": _op_stats, "close": _op_close}


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


def main(fd: int) -> int:
    """Worker entry: nice at least 10, faulthandler, hello (or fatal), then the request loop. Returns the exit code."""
    if os.nice(0) < 10:                 # at least nice 10: raise only when the parent is nicer
        os.nice(10 - os.nice(0))
    faulthandler.enable()
    conn = Connection(fd)
    try:
        lib, layout = _host.load(Path(os.environ["LAZ_HOST"]))
    except (OSError, KeyError, HostCallError, LibAzaharError) as exc:
        conn.send(("fatal", f"cannot load the host: {exc}"))
        return 1
    conn.send(("hello", int(layout.n_fields)))
    return _serve(conn, lib)
