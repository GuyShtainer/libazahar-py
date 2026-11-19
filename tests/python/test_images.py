"""libazahar.images: digest, compare and write_diff. Fast, no emulator."""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest

from libazahar import ArgumentError, images


def pic(value: int = 0, width: int = 8, height: int = 4) -> np.ndarray:
    array = np.full((height, width, 4), value, dtype=np.uint8)
    array[..., 3] = 255
    return array


def png_bytes(pixels: np.ndarray, *, depth: int = 8, colour: int = 6, filt: int = 0, idat_parts: int = 1,
              interlace: int = 0) -> bytes:
    height, width = pixels.shape[:2]
    raw = b"".join(bytes([filt]) + pixels[y].tobytes() for y in range(height))
    packed = zlib.compress(raw, 1)

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    size = -(-len(packed) // idat_parts)
    idats = b"".join(chunk(b"IDAT", packed[i:i + size]) for i in range(0, len(packed), size))
    header = struct.pack(">IIBBBBB", width, height, depth, colour, 0, 0, interlace)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + idats + chunk(b"IEND", b"")


def write(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def test_digest_is_stable_and_pixel_sensitive():
    top, bottom = pic(1, 400, 240), pic(2, 320, 240)
    first = images.digest((top, bottom))
    assert first == images.digest((top.copy(), bottom.copy()))
    assert first == images.digest((top.tobytes(), bottom.tobytes()))
    assert len(first) == 64 and int(first, 16) >= 0
    changed = top.copy()
    changed[239, 399, 0] ^= 1
    assert images.digest((changed, bottom)) != first
    assert images.digest((bottom, top)) != first


def test_digest_known_value():
    """A pinned value: a digest that changes between releases breaks every stored one."""
    assert images.digest((b"\x01\x02\x03\x04", b"\x05\x06\x07\x08")) == (
        "f0b0d294f2a0d6fcfbd1f90768383618d5558be1aff121accb5da80fb724021f"
    )


def test_digest_splits_the_boundary():
    """Moving bytes from one screen to the other changes the digest (the lengths are covered)."""
    assert images.digest((b"ab", b"cd")) != images.digest((b"abc", b"d"))


@pytest.mark.parametrize("bad", [None, b"abcd", (b"a",), (1, 2), (b"a", b"b", b"c")])
def test_digest_refuses_bad_input(bad):
    with pytest.raises(ArgumentError):
        images.digest(bad)


def test_compare_equal_and_limits():
    a = pic(10)
    b = a.copy()
    result = images.compare(a, b)
    assert (result.largest_delta, result.pixels, result.over, result.within) == (0, 0, 0, True)
    b[0, 0, 1] = 15
    b[1, 1, 2] = 12
    result = images.compare(a, b)
    assert (result.largest_delta, result.pixels, result.over, result.within) == (5, 2, 2, False)
    assert images.compare(a, b, max_pixels=2).within
    assert not images.compare(a, b, max_pixels=1).within
    result = images.compare(a, b, max_delta=4)
    assert (result.over, result.within) == (1, False)
    assert images.compare(a, b, max_delta=5).within and images.compare(a, b, max_delta=5).pixels == 2
    assert images.compare(a, b, max_delta=4, max_pixels=1).within


def test_compare_alpha_and_extremes():
    a, b = pic(0), pic(255)
    b[..., 3] = 0
    result = images.compare(a, b)
    assert result.largest_delta == 255 and result.pixels == a.shape[0] * a.shape[1]


def test_compare_size_and_argument_errors():
    with pytest.raises(ArgumentError, match="size"):
        images.compare(pic(0, 8, 4), pic(0, 4, 8))
    with pytest.raises(ArgumentError, match="uint8"):
        images.compare(pic(0).astype(np.int16), pic(0))
    with pytest.raises(ArgumentError, match="uint8"):
        images.compare(pic(0)[..., :3], pic(0))
    for kwargs in ({"max_delta": -1}, {"max_delta": 256}, {"max_delta": 1.5}, {"max_pixels": -1}, {"max_pixels": True}):
        with pytest.raises(ArgumentError):
            images.compare(pic(0), pic(0), **kwargs)


def test_compare_png_paths_and_write_diff(tmp_path):
    a, b = pic(40), pic(40)
    b[2, 3, :3] = (1, 2, 3)
    pa, pb = write(tmp_path, "a.png", png_bytes(a)), write(tmp_path, "b.png", png_bytes(b))
    result = images.compare(pa, pb)
    assert (result.largest_delta, result.pixels) == (39, 1)
    assert images.compare(str(pa), b).pixels == 1                    # a path and an array mix
    out = result.write_diff(tmp_path / "diff.png")
    diff = images._read_png(out)
    assert diff.shape == a.shape
    assert tuple(diff[2, 3]) == (255, 255, 255, 255)
    assert (diff[..., :3].sum(axis=2) > 0).sum() == 1
    assert (diff[..., 3] == 255).all()
    assert images.compare(out, out).within


def test_write_diff_over_only_and_hand_built(tmp_path):
    a, b = pic(10), pic(10)
    b[0, 0, 0] += 9                                                  # over a limit of 4
    b[1, 1, 0] += 2                                                  # differs, but within the limit
    result = images.compare(a, b, max_delta=4)
    every = images._read_png(result.write_diff(tmp_path / "all.png"))
    over = images._read_png(result.write_diff(tmp_path / "over.png", over_only=True))
    assert (every[..., 0] == 255).sum() == 2 and (over[..., 0] == 255).sum() == 1
    assert tuple(over[0, 0, :3]) == (255, 255, 255) and tuple(over[1, 1, :3]) == (0, 0, 0)
    with pytest.raises(ArgumentError, match="not made by compare"):
        images.CompareResult(1, 1, 1, False).write_diff(tmp_path / "x.png")
    with pytest.raises(TypeError):
        images.CompareResult(1, 1, 1, False, None)                   # type: ignore[call-arg]


def test_png_reader_bounds_the_inflate(tmp_path):
    """A pixel stream far longer than the header says is refused as the wrong size, not inflated in full."""
    a = pic(0, 8, 4)
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(4)) + bytes(10_000_000)
    body = zlib.compress(raw, 9)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", 8, 4, 8, 6, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", body) + chunk(b"IEND", b"")
    with pytest.raises(ArgumentError, match="wrong size"):
        images.compare(write(tmp_path, "big.png", data), a)


def test_png_reader_refuses_other_formats(tmp_path):
    a = pic(7)
    cases = {
        "rgb": png_bytes(a, colour=2),
        "depth16": png_bytes(a, depth=16),
        "filter1": png_bytes(a, filt=1),
        "two_idat": png_bytes(a, idat_parts=2),
        "interlaced": png_bytes(a, interlace=1),
        "not_png": b"GIF89a" + bytes(40),
        "truncated": png_bytes(a)[:-20],
    }
    for name, data in cases.items():
        path = write(tmp_path, f"{name}.png", data)
        with pytest.raises(ArgumentError):
            images.compare(path, a)
    good = png_bytes(a)
    bad_crc = bytearray(good)
    bad_crc[29] ^= 0xFF                                              # inside the IHDR body
    with pytest.raises(ArgumentError, match="CRC"):
        images.compare(write(tmp_path, "crc.png", bytes(bad_crc)), a)
    with pytest.raises(ArgumentError, match="cannot read"):
        images.compare(tmp_path / "missing.png", a)
    assert images.compare(write(tmp_path, "good.png", good), a).within


def test_write_diff_into_missing_folder(tmp_path):
    result = images.compare(pic(0), pic(1))
    with pytest.raises(ArgumentError, match="cannot write"):
        result.write_diff(tmp_path / "nope" / "diff.png")


def test_missing_numpy_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    with pytest.raises(ImportError, match=r"libazahar-py\[numpy\]"):
        images.compare(pic(0), pic(0))
    assert len(images.digest((b"a", b"b"))) == 64                    # digest needs no numpy


def test_result_is_frozen_and_small():
    result = images.compare(pic(0), pic(0))
    assert "_differs" not in repr(result)
    with pytest.raises(AttributeError):
        result.within = False                                        # type: ignore[misc]
