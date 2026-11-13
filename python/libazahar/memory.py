"""Guest memory of the running app, by guest virtual address (our patched core only; docs/USING.md "Guest memory").

Reads and writes happen between batches. The guest may be part-way into a frame when a call lands, so a record of
several fields can be torn (some fields from the frame before); the watch list of ``Emulator.run`` has the same
property. Names follow libmgba-py: ``memory.u32(addr)``, ``memory.u32.raw_read(addr)``, ``memory.read(addr, 64)``.
"""
from __future__ import annotations

import struct
from typing import Callable, Dict, Union

from . import _abi
from .errors import GuestMemoryError

__all__ = ["Memory"]

_Bytes = Union[bytes, bytearray, memoryview]
_TOP = 1 << 32


class _Width:
    """One integer width: callable like ``memory.u32(addr)``, with ``raw_read`` and ``raw_write``."""

    def __init__(self, memory: "Memory", name: str, fmt: str) -> None:
        self._memory = memory
        self.name = name
        self.fmt = "<" + fmt
        self.size = struct.calcsize(self.fmt)
        bits = 8 * self.size
        self.low, self.high = ((-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if name[0] == "s" else (0, (1 << bits) - 1))

    def raw_read(self, addr: int) -> int:
        """The little-endian value at guest address ``addr``."""
        return int(struct.unpack(self.fmt, self._memory.read(addr, self.size))[0])

    def raw_write(self, addr: int, value: int) -> None:
        """Write ``value`` (range-checked for the width) at ``addr``."""
        if isinstance(value, bool) or not isinstance(value, int) or not self.low <= value <= self.high:
            raise ValueError(f"{self.name}: value {value!r} is outside {self.low}..{self.high}")
        self._memory.write(addr, struct.pack(self.fmt, value))

    __call__ = raw_read


class Memory:
    """Guest memory of one Emulator (``emu.memory``). ``send`` is the Emulator's request function."""

    def __init__(self, send: Callable[[str, tuple], object]) -> None:
        self._send = send
        self.widths: Dict[str, _Width] = {}
        for name, fmt in (("u8", "B"), ("u16", "H"), ("u32", "I"), ("u64", "Q"),
                          ("s8", "b"), ("s16", "h"), ("s32", "i"), ("s64", "q")):
            width = _Width(self, name, fmt)
            self.widths[name] = width
            setattr(self, name, width)

    @staticmethod
    def _check_range(addr: int, length: int) -> None:
        if isinstance(addr, bool) or not isinstance(addr, int) or not 0 <= addr < _TOP:
            raise ValueError(f"addr {addr!r} must be an integer 0..0xFFFFFFFF")
        if isinstance(length, bool) or not isinstance(length, int) or not 1 <= length <= _abi.AZH_MEM_MAX_LEN:
            raise ValueError(f"length {length!r} must be an integer 1..{_abi.AZH_MEM_MAX_LEN}")
        if addr + length > _TOP:
            raise ValueError(f"0x{addr:08x}+{length} passes the end of the 4 GiB address space")

    def _call(self, op: str, args: tuple, addr: int, length: int) -> object:
        try:
            return self._send(op, args)
        except GuestMemoryError as exc:
            exc.addr, exc.length = addr, length
            raise

    def read(self, addr: int, length: int) -> bytes:
        """``length`` bytes at ``addr``. Raises GuestMemoryError when a page of the range is unmapped (nothing is
        returned then), NeedsLazpyCore on the stock core, ValueError for a bad range."""
        self._check_range(addr, length)
        data = self._call("read", (addr, length), addr, length)
        assert isinstance(data, bytes) and len(data) == length
        return data

    def write(self, addr: int, data: _Bytes) -> None:
        """Write ``data`` at ``addr``. All or nothing: a range with an unmapped page raises GuestMemoryError and changes
        nothing."""
        payload = bytes(data)
        self._check_range(addr, len(payload) if payload else 0)
        self._call("write", (addr, payload), addr, len(payload))

    def write_u8(self, addr: int, value: int) -> None:
        """Write one byte."""
        self.u8.raw_write(addr, value)

    def write_u16(self, addr: int, value: int) -> None:
        """Write a little-endian u16."""
        self.u16.raw_write(addr, value)

    def write_u32(self, addr: int, value: int) -> None:
        """Write a little-endian u32."""
        self.u32.raw_write(addr, value)

    def write_u64(self, addr: int, value: int) -> None:
        """Write a little-endian u64."""
        self.u64.raw_write(addr, value)
