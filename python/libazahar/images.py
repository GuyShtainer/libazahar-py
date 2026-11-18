"""Pictures: a stable digest of the two screens, and a compare of two pictures with a diff image.

Needs nothing but the standard library for ``digest``. ``compare`` needs numpy (``pip install 'libazahar-py[numpy]'``),
which is imported only when it is called. The PNG reader accepts only the host's own files (8-bit RGBA, filter 0 on
every row, one IDAT chunk) and refuses every other PNG with an ``ArgumentError``.
"""
from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence, Union

from .errors import ArgumentError

__all__ = ["digest", "compare", "CompareResult"]

Picture = Union[str, Path, Any]         # a PNG path, or an (H, W, 4) uint8 array
_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_DIGEST_TAG = b"libazahar.digest.1"


def _numpy() -> Any:
    try:
        import numpy
    except ImportError:
        raise ImportError("libazahar.images.compare needs numpy: install the extra with "
                          "pip install 'libazahar-py[numpy]'") from None
    return numpy


def digest(screens: Sequence[Any]) -> str:
    """A SHA-256 hex digest of the top and bottom screens, as returned by ``Emulator.screens()``.

    ``screens`` is ``(top, bottom)``: numpy arrays or ``bytes``. The digest covers each screen's byte length and pixel
    bytes in order, so equal pixels give an equal digest in any run, on any machine. Raises ``ArgumentError`` for
    anything but two buffers.
    """
    try:
        top, bottom = screens
        views = [memoryview(screen).cast("B") for screen in (top, bottom)]
    except (TypeError, ValueError):
        raise ArgumentError("digest takes (top, bottom): two contiguous byte buffers or arrays") from None
    hasher = hashlib.sha256(_DIGEST_TAG)
    for view in views:
        hasher.update(struct.pack("<Q", len(view)))
        hasher.update(view)
    return hasher.hexdigest()


def _chunks(data: bytes) -> list:
    """The (type, body) chunks of a PNG, CRCs checked."""
    chunks, pos = [], len(_SIGNATURE)
    while pos < len(data):
        if pos + 12 > len(data):
            raise ArgumentError("PNG: truncated chunk header")
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + length
        if end > len(data):
            raise ArgumentError("PNG: a chunk runs past the end of the file")
        body = data[pos + 8:pos + 8 + length]
        if struct.unpack(">I", data[end - 4:end])[0] != zlib.crc32(kind + body):
            raise ArgumentError(f"PNG: bad CRC in the {kind.decode('latin-1')} chunk")
        chunks.append((kind, body))
        pos = end
    return chunks


def read_png(path: Union[str, Path]) -> Any:
    """Read a PNG written by the host as an ``(H, W, 4)`` uint8 array. Any other PNG raises ``ArgumentError``."""
    numpy = _numpy()
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise ArgumentError(f"cannot read {path}: {exc.strerror or exc}") from exc
    if data[:8] != _SIGNATURE:
        raise ArgumentError(f"{path} is not a PNG")
    chunks = _chunks(data)
    kinds = [kind for kind, _ in chunks]
    if kinds != [b"IHDR", b"IDAT", b"IEND"]:
        raise ArgumentError(f"{path}: not the host's PNG layout (IHDR, one IDAT, IEND), chunks are {kinds}")
    if len(chunks[0][1]) != 13:
        raise ArgumentError(f"{path}: bad IHDR")
    width, height, depth, colour, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    if (depth, colour, compression, filtering, interlace) != (8, 6, 0, 0, 0):
        raise ArgumentError(f"{path}: only 8-bit RGBA, not interlaced, is accepted")
    if width == 0 or height == 0:
        raise ArgumentError(f"{path}: empty picture")
    row = width * 4 + 1
    try:
        raw = zlib.decompress(chunks[1][1])
    except zlib.error as exc:
        raise ArgumentError(f"{path}: damaged pixel data ({exc})") from exc
    if len(raw) != row * height:
        raise ArgumentError(f"{path}: pixel data has the wrong size")
    rows = numpy.frombuffer(raw, dtype=numpy.uint8).reshape(height, row)
    if rows[:, 0].any():
        raise ArgumentError(f"{path}: only filter 0 on every row is accepted")
    return rows[:, 1:].reshape(height, width, 4)


def _write_png(path: Path, pixels: Any) -> None:
    """Write an (H, W, 4) uint8 array in the host's own PNG layout."""
    height, width = pixels.shape[:2]
    raw = b"".join(b"\x00" + pixels[y].tobytes() for y in range(height))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 1)) + chunk(b"IEND", b""))


def _picture(item: Picture, name: str) -> Any:
    numpy = _numpy()
    if isinstance(item, (str, Path)):
        return read_png(item)
    array = numpy.asarray(item)
    if array.dtype != numpy.uint8 or array.ndim != 3 or array.shape[2] != 4:
        raise ArgumentError(f"{name} must be a PNG path or an (H, W, 4) uint8 array, not {array.dtype} {array.shape}")
    return array


@dataclass(frozen=True)
class CompareResult:
    """What ``compare`` found. ``max_delta``: the largest difference in any one channel (0 to 255). ``pixels``: how
    many pixels differ at all. ``over``: how many pixels have a channel off by more than the ``max_delta`` limit given
    to ``compare``. ``within``: ``over <= max_pixels``. ``write_diff(path)`` saves the difference picture."""

    max_delta: int
    pixels: int
    over: int
    within: bool
    _differs: Any = field(repr=False, compare=False, default=None)

    def write_diff(self, path: Union[str, Path]) -> Path:
        """Write a PNG of the compared size: white (full brightness) for every differing pixel, black elsewhere.
        Returns the path. Raises ``ArgumentError`` when the folder is missing."""
        numpy = _numpy()
        out = Path(path)
        pixels = numpy.zeros(self._differs.shape + (4,), dtype=numpy.uint8)
        pixels[..., 3] = 255
        pixels[self._differs, :3] = 255
        try:
            _write_png(out, pixels)
        except OSError as exc:
            raise ArgumentError(f"cannot write {out}: {exc.strerror or exc}") from exc
        return out


def compare(a: Picture, b: Picture, *, max_delta: int = 0, max_pixels: int = 0) -> CompareResult:
    """Compare two pictures of the same size: arrays from ``screens()`` or PNG paths written by the host.

    A pixel is over the limit when any channel (alpha too) differs by more than ``max_delta``; the pictures are
    ``within`` when at most ``max_pixels`` pixels are over. The defaults demand identical pictures. Raises
    ``ArgumentError`` for a different size, a bad limit or a PNG the host did not write, and ``ImportError`` naming
    the ``numpy`` extra when numpy is missing.
    """
    numpy = _numpy()
    for name, value, high in (("max_delta", max_delta, 255), ("max_pixels", max_pixels, None)):
        if isinstance(value, bool) or not isinstance(value, (int, numpy.integer)) or value < 0 or (
                high is not None and value > high):
            raise ArgumentError(f"{name} must be a whole number from 0{f' to {high}' if high else ''}, not {value!r}")
    first, second = _picture(a, "a"), _picture(b, "b")
    if first.shape != second.shape:
        raise ArgumentError(f"the pictures differ in size: {first.shape[1]}x{first.shape[0]} and "
                            f"{second.shape[1]}x{second.shape[0]}")
    delta = numpy.abs(first.astype(numpy.int16) - second.astype(numpy.int16)).max(axis=2)
    over = int((delta > max_delta).sum())
    return CompareResult(max_delta=int(delta.max()), pixels=int((delta > 0).sum()), over=over,
                         within=over <= max_pixels, _differs=delta > 0)
