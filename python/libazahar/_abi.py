"""ctypes mirrors of host/azhost.h (ABI 2) and the layout check against ``azh_abi_layout()``.

The constants below are plain module integers on purpose: ``check_layout`` reads them by name at call time, so a
changed value is caught by its ``const.<NAME>`` row of the host's table.
"""
from __future__ import annotations

import ctypes
from typing import Callable, Dict, Optional, Tuple

__all__ = ["ShotReq", "Batch", "Result", "Stats", "Field", "Layout", "check_layout", "STOP_NAMES"]

# ---- error codes, exit codes, screens, formats, stop reasons ----
AZH_OK = 0
AZH_E_ARG = -1
AZH_E_ORDER = -2
AZH_E_CORE = -3
AZH_E_BOOT = -4
AZH_E_VULKAN = -5
AZH_E_IO = -6
AZH_E_NOMEM = -7
AZH_E_UNSUPPORTED = -8
AZH_E_NEEDS_LAZPY_CORE = -9
AZH_E_SAVESTATE = -10
AZH_EXIT_OK = 0
AZH_EXIT_USAGE = 2
AZH_EXIT_BOOT = 3
AZH_EXIT_CORE = 4
AZH_EXIT_VULKAN = 5
AZH_EXIT_IO = 6
AZH_EXIT_NEEDS_LAZPY = 7
AZH_EXIT_UNSUPPORTED = 8
AZH_EXIT_GUEST_EXITED = 10
AZH_EXIT_GUEST_ERROR = 11
AZH_SCREEN_TOP = 1
AZH_SCREEN_BOTTOM = 2
AZH_SCREEN_BOTH = 3
AZH_FMT_PNG = 0
AZH_FMT_RAW = 1
AZH_STOP_FRAMES = 0
AZH_STOP_SD_TEXT = 1
AZH_STOP_DEBUG_TEXT = 2
AZH_STOP_GUEST_BREAK = 3
AZH_STOP_GUEST_EXITED = 4
AZH_STOP_GUEST_ERROR = 5
AZH_STOP_WALL_LIMIT = 6
AZH_ABI_VERSION = 2
AZH_MAX_SHOTS = 64
AZH_PATH_MAX = 1024
AZH_INPUT_INTS = 7
AZH_IN_FRAME = 0
AZH_IN_BUTTONS = 1
AZH_IN_TOUCH_X = 2
AZH_IN_TOUCH_Y = 3
AZH_IN_TOUCH_DOWN = 4
AZH_IN_CIRCLE_X = 5
AZH_IN_CIRCLE_Y = 6
AZH_MAX_INPUTS = 1000000
AZH_BUTTONS_MASK = 0x0000CFFF
AZH_CIRCLE_MAX = 32767
AZH_SD_EVERY_DEFAULT = 30
AZH_MSG_MAX = 256
AZH_MAX_FIELDS = 160

STOP_NAMES: Dict[int, str] = {
    AZH_STOP_FRAMES: "frames", AZH_STOP_SD_TEXT: "sd_text", AZH_STOP_DEBUG_TEXT: "debug_text",
    AZH_STOP_GUEST_BREAK: "guest_break", AZH_STOP_GUEST_EXITED: "guest_exited",
    AZH_STOP_GUEST_ERROR: "guest_error", AZH_STOP_WALL_LIMIT: "wall_limit",
}


class ShotReq(ctypes.Structure):
    """azh_shot_req."""

    _fields_ = [("frame", ctypes.c_int32), ("screens", ctypes.c_int32), ("format", ctypes.c_int32)]


class Batch(ctypes.Structure):
    """azh_batch."""

    _fields_ = [("frames", ctypes.c_int32), ("n_shots", ctypes.c_int32), ("shots", ShotReq * AZH_MAX_SHOTS),
                ("shot_dir", ctypes.c_char * AZH_PATH_MAX), ("sd_file", ctypes.c_char * AZH_PATH_MAX),
                ("sd_text", ctypes.c_char * 256), ("sd_every", ctypes.c_int32),
                ("debug_text", ctypes.c_char * 256), ("wall_limit_ms", ctypes.c_int32),
                ("sd_from_end", ctypes.c_int32)]


class Result(ctypes.Structure):
    """azh_result."""

    _fields_ = [("frames_run", ctypes.c_int64), ("first_frame", ctypes.c_int64), ("last_frame", ctypes.c_int64),
                ("stop_reason", ctypes.c_int32), ("shots_done", ctypes.c_int32), ("wall_s", ctypes.c_double),
                ("vblanks", ctypes.c_int64), ("message", ctypes.c_char * AZH_MSG_MAX)]


class Stats(ctypes.Structure):
    """struct azh_stats."""

    _fields_ = [("frames", ctypes.c_int64), ("wall_s", ctypes.c_double), ("user_s", ctypes.c_double),
                ("sys_s", ctypes.c_double), ("peak_rss", ctypes.c_int64), ("core_name", ctypes.c_char * 64),
                ("core_version", ctypes.c_char * 128), ("is_lazpy_core", ctypes.c_int32)]


class Field(ctypes.Structure):
    """azh_field."""

    _fields_ = [("name", ctypes.c_char * 32), ("offset", ctypes.c_int32), ("size", ctypes.c_int32)]


class Layout(ctypes.Structure):
    """azh_layout."""

    _fields_ = [("abi", ctypes.c_uint32), ("size_batch", ctypes.c_uint32), ("size_result", ctypes.c_uint32),
                ("size_stats", ctypes.c_uint32), ("size_layout", ctypes.c_uint32), ("map_size", ctypes.c_uint32),
                ("map_px_off", ctypes.c_uint32), ("map_px_size", ctypes.c_uint32),
                ("off_heartbeat", ctypes.c_uint32), ("off_stop", ctypes.c_uint32), ("off_msg", ctypes.c_uint32),
                ("off_px_frame", ctypes.c_uint32), ("n_fields", ctypes.c_int32),
                ("fields", Field * AZH_MAX_FIELDS)]


_STRUCTS: Dict[str, type] = {"shot": ShotReq, "batch": Batch, "result": Result, "stats": Stats, "layout": Layout}


def _fail(text: str) -> Exception:
    from .errors import HostError  # late: errors imports this module's constants
    return HostError(f"ABI mismatch: {text}")


def _check_struct_row(cls: type, name: str, field: str, offset: int, size: int) -> None:
    if field == "__size__":
        if ctypes.sizeof(cls) != size:
            raise _fail(f"{name}: host size {size}, ctypes size {ctypes.sizeof(cls)}")
        return
    member = getattr(cls, field, None)
    if member is None or not hasattr(member, "offset"):
        raise _fail(f"{name}: no such field on the Python side")
    if member.offset != offset or member.size != size:
        raise _fail(f"{name}: host offset {offset} size {size}, ctypes offset {member.offset} size {member.size}")


def _check_map_row(name: str, offset: int, size: int, rows: Dict[str, Tuple[int, int]]) -> None:
    if name not in rows:
        raise _fail(f"{name}: unknown to _map.py")
    if rows[name] != (offset, size):
        raise _fail(f"{name}: host offset {offset} size {size}, _map.py {rows[name]}")


def _check_const_row(name: str, value: int) -> None:
    python_name = name.split(".", 1)[1]
    mine = globals().get(python_name)
    if not isinstance(mine, int):
        raise _fail(f"{name}: unknown to _abi.py")
    if mine != value:
        raise _fail(f"{name}: host {value}, _abi.py {mine}")


def check_layout(layout: Layout, structs: Optional[Dict[str, type]] = None,
                 map_rows: Optional[Callable[[], Dict[str, Tuple[int, int]]]] = None) -> None:
    """Compare the host's ``azh_layout`` with this module and ``_map.py``; raises HostError("ABI mismatch: ...").

    Order: ``size_layout`` and ``abi`` first (so ``fields[]`` is read from the right place), then every row.
    ``structs`` (merged over the defaults) and ``map_rows`` exist so tests can pass altered copies.
    """
    classes = dict(_STRUCTS)
    classes.update(structs or {})
    if map_rows is None:
        from . import _map
        map_rows = _map.rows
    if layout.size_layout != ctypes.sizeof(Layout):
        raise _fail(f"size_layout {layout.size_layout}, ctypes {ctypes.sizeof(Layout)}")
    if layout.abi != AZH_ABI_VERSION:
        raise _fail(f"host abi {layout.abi}, Python abi {AZH_ABI_VERSION}")
    n_fields = layout.n_fields
    if not 0 < n_fields <= AZH_MAX_FIELDS:
        raise _fail(f"n_fields {n_fields}")
    mapping = map_rows()
    for index in range(n_fields):
        row = layout.fields[index]
        name = row.name.decode("ascii", "replace")
        prefix, _, rest = name.partition(".")
        if prefix in classes:
            _check_struct_row(classes[prefix], name, rest, row.offset, row.size)
        elif prefix == "map":
            _check_map_row(name, row.offset, row.size, mapping)
        elif prefix == "const":
            _check_const_row(name, row.offset)
        else:
            raise _fail(f"{name}: unknown row")

