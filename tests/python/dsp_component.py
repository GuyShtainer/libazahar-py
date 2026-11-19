# SPDX-License-Identifier: GPL-3.0-or-later
"""A made-up component file for the app's audio library to find on the SD card.

Our own bytes: an ASCII tag and a fixed pattern. Azahar's high-level DSP only logs a hash of the file."""
from __future__ import annotations

from pathlib import Path

TAG = b"LAZPY-MADE-UP-DSP-COMPONENT\0"


def write_component(seed: Path, size: int = 0x8000) -> Path:
    """Write the made-up file into the seed folder, where the app looks for it, and return its path."""
    if size < len(TAG):
        raise ValueError(f"size must be at least {len(TAG)}")
    buf = bytearray((i * 7 + 0x5A) & 0xFF for i in range(size))
    buf[0:len(TAG)] = TAG
    out = seed / "3ds" / "dspfirm.cdc"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(buf))
    return out
