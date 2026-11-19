"""Worker side only: load libazhost with ctypes, set the prototypes, check the layout, turn failures into errors."""
from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any, Tuple

from . import _abi
from .errors import HostCallError, HostError

__all__ = ["load", "call", "last_error"]

_C = ctypes
_PROTOTYPES = {
    "azh_open": (_C.c_int, [_C.c_char_p, _C.c_char_p, _C.c_char_p, _C.c_char_p]),
    "azh_close": (_C.c_int, []),
    "azh_set_option": (_C.c_int, [_C.c_char_p, _C.c_char_p]),
    "azh_boot": (_C.c_int, [_C.c_char_p, _C.c_char_p]),
    "azh_run": (_C.c_int, [_C.c_void_p, _C.c_int32, _C.POINTER(_abi.Batch), _C.POINTER(_abi.Result)]),
    "azh_shot": (_C.c_int, [_C.c_int32, _C.c_int32, _C.c_char_p]),
    "azh_save_state": (_C.c_int, [_C.c_char_p, _C.POINTER(_C.c_int32)]),
    "azh_load_state": (_C.c_int, [_C.c_char_p]),
    "azh_read": (_C.c_int, [_C.c_uint32, _C.c_uint32, _C.c_void_p]),
    "azh_write": (_C.c_int, [_C.c_uint32, _C.c_uint32, _C.c_void_p]),
    "azh_threads": (_C.c_int, [_C.c_void_p, _C.c_int32, _C.POINTER(_C.c_int32)]),
    "azh_set_input": (_C.c_int, [_C.POINTER(_C.c_int32)]),
    "azh_audio_capture": (_C.c_int, [_C.c_char_p]),
    "azh_audio_info": (_C.c_int, [_C.POINTER(_C.c_int64), _C.POINTER(_C.c_int32)]),
    "azh_movie_play": (_C.c_int, [_C.c_char_p]),
    "azh_stats": (_C.c_int, [_C.POINTER(_abi.Stats)]),
    "azh_abi_layout": (_C.c_int, [_C.POINTER(_abi.Layout)]),
    "azh_error": (_C.c_char_p, []),
}


def load(path: Path) -> Tuple[ctypes.CDLL, _abi.Layout]:
    """Load the host, set every prototype and check the ABI layout; raises HostError on any mismatch."""
    lib = ctypes.CDLL(str(path))
    for name, (restype, argtypes) in _PROTOTYPES.items():
        try:
            fn = getattr(lib, name)
        except AttributeError:
            raise HostError(f"host {path} lacks {name}: an older libazhost (the audio and movie calls need ABI 5)") \
                from None
        fn.restype = restype
        fn.argtypes = argtypes
    layout = _abi.Layout()
    rc = lib.azh_abi_layout(ctypes.byref(layout))
    if rc != 0:
        raise HostCallError(rc, last_error(lib))
    _abi.check_layout(layout)
    return lib, layout


def last_error(lib: ctypes.CDLL) -> str:
    """The host's last error text."""
    raw = lib.azh_error()
    return raw.decode("utf-8", "replace") if raw else ""


def call(lib: ctypes.CDLL, name: str, *args: Any) -> int:
    """Call ``azh_<name>``; a negative return raises HostCallError(code, host text). Returns the code otherwise."""
    rc = getattr(lib, name)(*args)
    if rc < 0:
        raise HostCallError(rc, last_error(lib))
    return rc
