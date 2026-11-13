# SPDX-License-Identifier: GPL-3.0-or-later
"""Checker for the libazahar-py test app: marker pixels, the per-frame log, and event lines.

Run with python3 -I. Subcommands: markers, log, event. Phase 2 imports read_png_rgba.
"""
import argparse
import re
import struct
import sys
import zlib

BG = (0x20, 0x20, 0x20)
# (x, y, colour) of the four 8x8 markers per screen; the layout is fixed by the test app.
TOP = [(0, 0, (255, 0, 0)), (392, 0, (0, 255, 0)), (0, 232, (0, 0, 255)), (392, 232, (255, 255, 255))]
BOTTOM = [(0, 0, (255, 255, 0)), (312, 0, (0, 255, 255)), (0, 232, (255, 0, 255)), (312, 232, (255, 128, 0))]


def read_png_rgba(path: str) -> tuple[int, int, bytes]:
    """Decode an 8-bit RGB/RGBA PNG whose rows all use filter 0.

    Returns (width, height, RGBA bytes, row-major, alpha 255 for RGB input).
    Raises ValueError on any other filter, colour type, bit depth or interlace.
    """
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, ihdr = 8, [], None
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk header")
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if pos + 12 + length > len(data):
            raise ValueError("PNG chunk runs past the end of the file")
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            if length != 13:
                raise ValueError("bad IHDR length")
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.append(body)
    if ihdr is None:
        raise ValueError("no IHDR")
    width, height, depth, ctype, comp, filt, interlace = ihdr
    if depth != 8 or ctype not in (2, 6) or interlace != 0 or comp != 0 or filt != 0:
        raise ValueError(f"unsupported PNG: depth={depth} colour={ctype} interlace={interlace} "
                         f"compression={comp} filter-method={filt}")
    bpp = 3 if ctype == 2 else 4
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as exc:
        raise ValueError(f"bad PNG data: {exc}") from exc
    stride = width * bpp
    if len(raw) != height * (stride + 1):
        raise ValueError("PNG size mismatch")
    out = bytearray()
    for row in range(height):
        start = row * (stride + 1)
        if raw[start] != 0:
            raise ValueError(f"unsupported PNG filter {raw[start]}")
        line = raw[start + 1:start + 1 + stride]
        if bpp == 4:
            out += line
        else:
            for i in range(0, stride, 3):
                out += line[i:i + 3] + b"\xff"
    return width, height, bytes(out)


class Screen:
    """A view of one screen inside an RGBA image, at an offset."""

    def __init__(self, image: tuple[int, int, bytes], ox: int, oy: int, w: int, h: int):
        self.img, self.ox, self.oy, self.w, self.h = image, ox, oy, w, h

    def px(self, x: int, y: int) -> tuple[int, int, int]:
        if not (0 <= x < self.w and 0 <= y < self.h):
            return (-1, -1, -1)
        iw, _ih, data = self.img
        i = ((self.oy + y) * iw + self.ox + x) * 4
        return (data[i], data[i + 1], data[i + 2])


def check_screen(scr: Screen, markers, shift: int, name: str) -> tuple[int, list]:
    """Return (markers that pass, error strings)."""
    good, errors = 0, []
    for mx, my, col in markers:
        mx += shift
        probes = [(mx, my), (mx + 7, my), (mx, my + 7), (mx + 7, my + 7), (mx + 3, my + 3)]
        # the pixel diagonally just outside the inner corner (the corner nearest the screen centre)
        left = mx + 4 < scr.w // 2
        low = my + 4 >= scr.h // 2
        ix, iy = (mx + 7 if left else mx), (my if low else my + 7)
        out = (ix + (1 if left else -1), iy + (-1 if low else 1))
        bad = [(p, scr.px(*p)) for p in probes if scr.px(*p) != col]
        if scr.px(*out) != BG:
            bad.append((out, scr.px(*out)))
        if bad:
            errors.append(f"{name} marker {col}: {bad[0]} ({len(bad)} bad probes)")
        else:
            good += 1
    return good, errors


def cmd_markers(args) -> int:
    errors: list = []
    if args.png:
        img = read_png_rgba(args.png)
        if img[:2] != (400, 480):
            print(f"FAIL markers: frame is {img[0]}x{img[1]}, want 400x480")
            return 1
        top, bottom = Screen(img, 0, 0, 400, 240), Screen(img, 40, 240, 320, 240)
        for x, y in ((39, 240), (360, 240)):
            if Screen(img, 0, 0, 400, 480).px(x, y) != (0, 0, 0):
                errors.append(f"layout pixel ({x},{y}) is not black")
    else:
        ti, bi = read_png_rgba(args.top), read_png_rgba(args.bottom)
        if ti[:2] != (400, 240) or bi[:2] != (320, 240):
            print("FAIL markers: split shots must be 400x240 and 320x240")
            return 1
        top, bottom = Screen(ti, 0, 0, 400, 240), Screen(bi, 0, 0, 320, 240)
    nt, top_errors = check_screen(top, TOP, args.expect_shift, "top")
    nb, bottom_errors = check_screen(bottom, BOTTOM, args.expect_shift, "bottom")
    errors += top_errors + bottom_errors
    if errors:
        print(f"FAIL markers ({args.mode}): " + "; ".join(errors))
        return 1
    print(f"markers ok top={nt} bottom={nb}")
    return 0


def parse_log(path: str):
    """Return (all lines, [(f, v) per-frame pairs])."""
    with open(path, encoding="ascii", errors="replace") as fh:
        lines = fh.read().splitlines()
    frames = []
    for line in lines:
        m = re.match(r"f=(\d+) v=(\d+) ", line)
        if m:
            frames.append((int(m.group(1)), int(m.group(2))))
    return lines, frames


def cmd_log(args) -> int:
    lines, frames = parse_log(args.path)
    if not lines or not lines[0].startswith("start "):
        print("FAIL log: first line is not the start line")
        return 1
    if not frames:
        print("FAIL log: no per-frame lines")
        return 1
    for (a, _), (b, _) in zip(frames, frames[1:]):
        if b != a + 1:
            print(f"FAIL log: f jumps from {a} to {b}")
            return 1
    offset = args.runs - frames[-1][0]
    if not 0 <= offset <= 120:
        print(f"FAIL log: boot offset {offset} (runs {args.runs}, last f {frames[-1][0]}) outside 0..120")
        return 1
    vjumps = sum(1 for (_, a), (_, b) in zip(frames, frames[1:]) if b != a + 1)
    print(f"log ok lines={len(frames)} first_v={frames[0][1]} last_v={frames[-1][1]} offset={offset} vjumps={vjumps}")
    return 0


def cmd_event(args) -> int:
    lines, frames = parse_log(args.path)
    n, kind = args.n, args.kind
    idx = [i for i, ln in enumerate(lines) if ln.startswith(f"{kind} f={n} ")]
    fs = [f for f, _ in frames]
    ok = bool(idx) and bool(fs)
    if ok and kind == "exit":
        ok = idx[0] == len(lines) - 1
    elif ok and kind == "break" and args.stopped:
        # the runner stops at the break (azhost on our core, stop=guest_break): the break line is the log's last
        ok = idx[0] == len(lines) - 1 and fs[-1] == n
    elif ok and kind == "break":
        ok = fs[-1] > n and (n + 1) in fs
    elif ok and kind == "ready":
        ok = fs[-1] > n
    elif ok and kind == "booted":
        ok = fs[0] == n + 1
    if ok and kind != "exit" and not args.stopped:
        # still running at the end: the last frame line is within 0..120 of the runner's frame count
        ok = args.runs is not None and 0 <= args.runs - fs[-1] <= 120
    if not ok:
        print(f"FAIL event {kind} {n}: lines={len(lines)} frames={len(fs)} first_f={fs[:1]} last_f={fs[-1:]}")
        return 1
    print("event ok")
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("markers")
    m.add_argument("png", nargs="?")
    m.add_argument("--top")
    m.add_argument("--bottom")
    m.add_argument("--mode", choices=("2d", "3d"), default="2d")
    m.add_argument("--expect-shift", type=int, default=0)
    lg = sub.add_parser("log")
    lg.add_argument("path")
    lg.add_argument("--runs", type=int, required=True)
    ev = sub.add_parser("event")
    ev.add_argument("path")
    ev.add_argument("kind", choices=("break", "exit", "ready", "booted"))
    ev.add_argument("n", type=int)
    ev.add_argument("--runs", type=int, help="runner frame count; required except for exit")
    ev.add_argument("--stopped", action="store_true", help="break only: the runner stopped at the break")
    args = ap.parse_args(argv)
    if args.cmd == "markers" and not (args.png or (args.top and args.bottom)):
        ap.error("markers needs a PNG or --top and --bottom")
    try:
        return {"markers": cmd_markers, "log": cmd_log, "event": cmd_event}[args.cmd](args)
    except (ValueError, OSError) as exc:
        print(f"FAIL {args.cmd}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
