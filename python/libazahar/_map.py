"""The mapped file ``host.map``: offsets (checked against the host by ``_abi.check_layout``) and a read-only reader."""
from __future__ import annotations

import mmap
import struct
from pathlib import Path
from typing import Dict, Optional, Tuple

__all__ = ["HostMap", "rows"]

MAGIC = b"LAZMAP1\x00"
VERSION_OFF = 8
HEADER_SIZE_OFF = 12
HEARTBEAT = 16
STOP_CODE = 24
MSG_LEN = 28
MSG = 32
MSG_MAX = 1024
DIMS = 1056
PX_FRAME = 1072
FRAME_TOTAL = 1080
VBLANKS_TOTAL = 1088
MSG_SEQ = 1096
PID = 1100
EXIT_CODE = 1104
PIXELS = 4096
PIXELS_SIZE = 400 * 240 * 4 + 320 * 240 * 4
SIZE = PIXELS + PIXELS_SIZE
TOP_BYTES = 400 * 240 * 4
BOTTOM_BYTES = 320 * 240 * 4


def rows() -> Dict[str, Tuple[int, int]]:
    """The ``map.*`` rows as (offset, size), built from the constants at call time."""
    return {
        "map.magic": (0, 8), "map.version": (VERSION_OFF, 4), "map.header_size": (HEADER_SIZE_OFF, 4),
        "map.heartbeat": (HEARTBEAT, 8), "map.stop_code": (STOP_CODE, 4), "map.msg_len": (MSG_LEN, 4),
        "map.message": (MSG, MSG_MAX), "map.dims": (DIMS, 16), "map.px_frame": (PX_FRAME, 8),
        "map.frame_total": (FRAME_TOTAL, 8), "map.vblanks_total": (VBLANKS_TOTAL, 8),
        "map.msg_seq": (MSG_SEQ, 4), "map.pid": (PID, 4), "map.exit_code": (EXIT_CODE, 4),
        "map.pixels": (PIXELS, PIXELS_SIZE), "map.__size__": (0, SIZE),
    }


class HostMap:
    """Read-only view of one instance's ``host.map``. Reads need no round trip to the worker."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._file = open(self.path, "rb")
        try:
            self._mm: Optional[mmap.mmap] = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        except (ValueError, OSError):
            self._file.close()
            raise
        self._view = memoryview(self._mm)

    def _u(self, fmt: str, offset: int) -> int:
        assert self._mm is not None, "map is closed"
        if offset + struct.calcsize(fmt) > len(self._mm):
            return 0
        return int(struct.unpack_from(fmt, self._mm, offset)[0])

    def valid(self) -> bool:
        """True when the file is full size and starts with the host's magic."""
        return self._mm is not None and len(self._mm) >= SIZE and bytes(self._mm[:8]) == MAGIC

    def heartbeat(self) -> int:
        """Counter the host bumps every frame."""
        return self._u("<Q", HEARTBEAT)

    def stop_code(self) -> int:
        """Stop code of the last batch."""
        return self._u("<i", STOP_CODE)

    def message(self) -> str:
        """The last guest message (empty when none)."""
        assert self._mm is not None
        length = min(self._u("<I", MSG_LEN), MSG_MAX - 1)
        return bytes(self._mm[MSG:MSG + length]).decode("utf-8", "replace")

    def msg_seq(self) -> int:
        """Counter of messages written."""
        return self._u("<I", MSG_SEQ)

    def frame_total(self) -> int:
        """retro_run calls since boot (plus a state's k)."""
        return self._u("<q", FRAME_TOTAL)

    def vblanks_total(self) -> int:
        """Guest VBlanks since boot."""
        return self._u("<q", VBLANKS_TOTAL)

    def exit_code(self) -> int:
        """Exit code the host wrote before exiting itself (0 until then)."""
        return self._u("<i", EXIT_CODE)

    def pid(self) -> int:
        """The worker's pid."""
        return self._u("<I", PID)

    def px_frame(self) -> int:
        """Frame number of the raw pixels in the map (-1 none, or one being written)."""
        return self._u("<q", PX_FRAME)

    def pixels(self, screen: int) -> memoryview:
        """Read-only slice of the pixel area: screen 1 = top (400x240 RGBA), 2 = bottom (320x240 RGBA)."""
        if screen == 1:
            return self._view[PIXELS:PIXELS + TOP_BYTES]
        if screen == 2:
            return self._view[PIXELS + TOP_BYTES:PIXELS + TOP_BYTES + BOTTOM_BYTES]
        raise ValueError("screen must be 1 (top) or 2 (bottom)")

    def close(self) -> None:
        """Release the map; with live views (numpy arrays) the mapping stays until they die."""
        if self._mm is None:
            return
        mapping, self._mm = self._mm, None
        try:
            self._view.release()
        except BufferError:
            pass                         # a live export of the view keeps it
        try:
            mapping.close()
        except BufferError:
            pass                         # live views keep the mapping; it is freed when they die
        self._file.close()
