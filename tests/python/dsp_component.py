# SPDX-License-Identifier: GPL-3.0-or-later
"""A made-up component file for the app's audio library to find on the SD card.

Our own bytes: an ASCII tag, a size word at 0x104, a fixed pattern elsewhere. Azahar's high-level DSP only logs a hash of
the file and never rejects it."""
from __future__ import annotations

import struct
from pathlib import Path

TAG = b"LAZPY-MADE-UP-DSP-COMPONENT\0"


def write_component(seed: Path, size: int = 0x8000) -> Path:
    """Write the made-up file into the seed folder, where the app looks for it, and return its path."""
    if size < 0x400:
        raise ValueError("size must be at least 0x400")
    buf = bytearray((i * 7 + 0x5A) & 0xFF for i in range(size))
    buf[0:len(TAG)] = TAG
    buf[0x104:0x108] = struct.pack("<I", size)
    out = seed / "3ds" / "dspfirm.cdc"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(buf))
    return out
