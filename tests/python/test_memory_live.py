"""Step G's gate: guest memory reads and writes and the watch list against the test app (docs/plans/phase-g.md).

Every test names its core (``lazpy_core`` or ``stock_core``), so one run covers both whatever LAZ_CORE says.
Numbers worth reporting go to runs/g/live-numbers.txt (and stderr)."""
from __future__ import annotations

import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pytest

import d_helpers as dh
import testapp_log as tl
from libazahar import Buttons, Circle, Emulator, GuestMemoryError, NeedsLazpyCore, Touch

pytestmark = pytest.mark.slow

MAGIC = 0x4C415A52
RECORD = struct.Struct("<IIIIHHhhQ")       # magic, frame, vblank, keys, tx, ty, cx, cy, tick (32 bytes)
FIELDS = ("magic", "frame", "vblank", "keys", "tx", "ty", "cx", "cy", "tick")
LINE_KEY = {"frame": "f", "vblank": "v", "keys": "k", "tx": "tx", "ty": "ty", "cx": "cx", "cy": "cy", "tick": "s"}
NUMBERS = Path(__file__).resolve().parents[2] / "runs" / "g" / "live-numbers.txt"


def note(line: str) -> None:
    print(line, file=sys.stderr)
    NUMBERS.parent.mkdir(parents=True, exist_ok=True)
    with open(NUMBERS, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def varied_inputs(frames: int) -> List[Tuple[int, object]]:
    """Inputs that change keys, touch and circle every few frames, so the record's fields all vary."""
    items: List[Tuple[int, object]] = []
    for index, frame in enumerate(range(1, frames + 1, 5)):
        kind = index % 4
        if kind == 0:
            items.append((frame, Buttons.A | (Buttons.X if index % 8 == 0 else Buttons(0))))
        elif kind == 1:
            items.append((frame, Touch(10 + index % 300, 20 + index % 200)))
        elif kind == 2:
            items.append((frame, Circle((index * 997) % 30000 - 15000, (index * 577) % 30000 - 15000)))
        else:
            items.append((frame, Touch.up))
    return items


START_RE = re.compile(r"^start addr_global=0x([0-9a-f]+) addr_heap=0x([0-9a-f]+)", re.M)


def start_addrs(emu: Emulator) -> Tuple[int, int]:
    """(addr_global, addr_heap) from the test app's ``start`` log line (testapp_log does not expose it: a regex)."""
    log = emu.sd / dh.LOG
    match = START_RE.search(log.read_text(errors="replace")) if log.is_file() else None
    assert match, "no start line in the app's log"
    return int(match.group(1), 16), int(match.group(2), 16)


def decode(raw: bytes) -> Dict[str, int]:
    return dict(zip(FIELDS, RECORD.unpack(raw)))


def verify(records: Sequence[Dict[str, int]], frames_by_f: Dict[int, dict], label: str) -> Dict[str, object]:
    """Compare each record with the log line of its own frame. A record whose fields all match is clean; one whose
    fields each match line f or line f - 1 is torn (counted per field); anything else is a failure."""
    torn, torn_fields, clean, unverified, bad = 0, {}, 0, 0, []
    for rec in records:
        if rec["magic"] != MAGIC:
            bad.append((rec, "magic"))
            continue
        line = frames_by_f.get(rec["frame"])
        if line is None:
            unverified += 1
            continue
        prev = frames_by_f.get(rec["frame"] - 1)
        mismatched = [name for name in LINE_KEY if rec[name] != line[LINE_KEY[name]]]
        if not mismatched:
            clean += 1
            continue
        if prev is not None and all(rec[name] == prev[LINE_KEY[name]] for name in mismatched):
            torn += 1
            for name in mismatched:
                torn_fields[name] = torn_fields.get(name, 0) + 1
        else:
            bad.append((rec, mismatched))
    note(f"{label}: records={len(records)} clean={clean} torn={torn} torn_fields={torn_fields} "
         f"unverified={unverified} bad={len(bad)}")
    assert not bad, f"{label}: {len(bad)} records match no line, first {bad[:2]}"
    assert torn <= max(1, len(records) // 100), f"{label}: {torn} torn records (over 1 %)"
    assert unverified <= 3, f"{label}: {unverified} records have no log line"
    return {"torn": torn, "fields": torn_fields}


def lines_by_frame(emu: Emulator) -> Dict[int, dict]:
    frames, _ = dh.log_of(emu)
    return {row["f"]: row for row in frames}


def boot(paths, core: Path, workdir: Path, seed, **control) -> Tuple[Emulator, int, int]:
    """An Emulator on ``core`` once the app's start line is in its log (30 frames, up to 600: the stock core has no
    tick seed, and on a loaded Windows PC 30 frames once fell short, and
    300 once in a full gate), with the app's two record addresses."""
    emu = dh.boot(paths, workdir, seed(**control), core=core)
    log = emu.sd / dh.LOG
    for _ in range(20):
        emu.run(30)
        if log.is_file() and START_RE.search(log.read_text(errors="replace")):
            break
    glob, heap = start_addrs(emu)
    return emu, glob, heap


def test_m1_reads_match_the_log(host_paths, lazpy_core, workdir, seed):
    emu, glob, heap = boot(host_paths, lazpy_core, workdir, seed)
    with emu:
        inputs = dict(varied_inputs(700))
        recs: Dict[str, List[Dict[str, int]]] = {"global": [], "heap": []}
        for index in range(600):
            item = inputs.get(index + 1)
            emu.run(1, inputs=[(1, item)] if item is not None else ())
            recs["global"].append(decode(emu.memory.read(glob, 32)))
            recs["heap"].append(decode(emu.memory.read(heap, 32)))
        by_f = lines_by_frame(emu)
        for name in ("global", "heap"):
            frames = [r["frame"] for r in recs[name]]
            assert all(b >= a for a, b in zip(frames, frames[1:])), f"{name}: frames go backwards"
            assert len(set(frames)) >= 590, f"{name}: only {len(set(frames))} distinct frames"
            verify(recs[name], by_f, f"m1 {name}")
        lag = sum(1 for g, h in zip(recs["global"], recs["heap"]) if h["frame"] == g["frame"] - 1)
        note(f"m1 lag: heap one frame behind global in {lag} of 600 reads")


def test_m2_m6_watch_rows_and_footprint(host_paths, lazpy_core, workdir, seed):
    emu, glob, heap = boot(host_paths, lazpy_core, workdir, seed)
    with emu:
        res = emu.run(600, inputs=varied_inputs(600), watch=[(glob, 8), (heap, 8)])
        assert len(res.watch) == 600
        first = res.first_frame - 1
        assert [r.frame for r in res.watch] == [first + i + 1 for i in range(600)]
        assert all(r.status == 0 and len(r.data) == 2 and len(r.data[0]) == 32 for r in res.watch)
        res10 = emu.run(600, watch=[(glob, 8), (heap, 8)], watch_every=10)
        assert len(res10.watch) == 60
        first10 = res10.first_frame - 1
        assert [r.frame for r in res10.watch] == [first10 + 10 * (i + 1) for i in range(60)]
        by_f = lines_by_frame(emu)
        for name, entry in (("global", 0), ("heap", 1)):
            g1 = [decode(r.data[entry])["frame"] for r in res.watch]
            assert all(b >= a for a, b in zip(g1, g1[1:])) and len(set(g1)) >= 590, f"m2 every1 {name}: stale rows"
            g10 = [decode(r.data[entry])["frame"] for r in res10.watch]
            assert all(b > a for a, b in zip(g10, g10[1:])) and len(set(g10)) >= 59, f"m2 every10 {name}: stale rows"
            verify([decode(r.data[entry]) for r in res.watch], by_f, f"m2 every1 {name}")
            verify([decode(r.data[entry]) for r in res10.watch], by_f, f"m2 every10 {name}")
        # m6: the footprint after m2
        note(f"m6: du -k host.map = {footprint_kib(workdir / 'host.map')} KiB; peak_rss = {emu.stats().peak_rss} bytes")
        # a batch whose rows do not fit says the largest that does
        with pytest.raises(ValueError, match="largest batch"):
            emu.run(60000, watch=[(glob, 256)] * 2)


def footprint_kib(path: Path) -> int:
    """``du -k``: the disk blocks a file takes (Windows: GetCompressedFileSizeW, rounded up to KiB)."""
    if sys.platform != "win32":
        done = subprocess.run(["du", "-k", str(path)], capture_output=True, text=True, check=True)
        return int(done.stdout.split()[0])
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCompressedFileSizeW.restype = ctypes.c_uint32
    kernel32.GetCompressedFileSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    high = ctypes.c_uint32(0)
    low = kernel32.GetCompressedFileSizeW(str(path), ctypes.byref(high))
    return ((high.value << 32 | low) + 1023) // 1024


def test_m3_write_the_control_struct(host_paths, lazpy_core, workdir, seed):
    emu, glob, _ = boot(host_paths, lazpy_core, workdir, seed, exit_at=999001, ready_at=999002)
    with emu:
        page = glob & ~0xFFF
        needle = struct.pack("<II", 999001, 999002)
        hits: List[int] = []
        for base in range(page - 0x10000, page + 0x10000, 0x1000):
            try:
                data = emu.memory.read(base, 4096)
            except GuestMemoryError:
                continue
            start = data.find(needle)
            while start >= 0:
                hits.append(base + start)
                start = data.find(needle, start + 1)
        assert len(hits) == 1, f"m3: {len(hits)} hits for the control values"
        x = hits[0]
        assert [emu.memory.u32(x - 8), emu.memory.u32(x - 4), emu.memory.u32(x + 8)] == [0, 0, 0]
        ready = x + 4
        frame = emu.memory.u32(glob + 4)
        emu.memory.write_u32(ready, frame + 2)
        assert emu.memory.u32(ready) == frame + 2
        emu.run(10)
        _, events = dh.log_of(emu)
        readies = [e for e in events if e["kind"] == "ready"]
        note(f"m3: X=0x{x:08x} (addr_global {x - glob:+d}), wrote ready_at={frame + 2}, "
             f"ready events {[e['f'] for e in readies]}")
        assert readies and readies[0]["f"] == frame + 2


def test_m4_unmapped_memory(host_paths, lazpy_core, workdir, seed):
    emu, glob, _ = boot(host_paths, lazpy_core, workdir, seed)
    with emu:
        page = glob & ~0xFFF
        edge = None
        for k in range(1, 4097):
            try:
                emu.memory.read(page + k * 0x1000, 4)
            except GuestMemoryError:
                edge = page + k * 0x1000
                break
        assert edge is not None, "m4: no unmapped page within 16 MiB above the globals"
        note(f"m4: P=0x{edge:08x} (addr_global {edge - glob:+d})")
        with pytest.raises(GuestMemoryError) as info:
            emu.memory.read(edge - 8, 16)
        assert info.value.addr == edge - 8 and info.value.length == 16
        assert len(emu.memory.read(edge - 8, 8)) == 8
        for addr in (edge, 0):
            with pytest.raises(GuestMemoryError):
                emu.memory.read(addr, 4)
        before = emu.memory.read(edge - 4, 4)
        with pytest.raises(GuestMemoryError):
            emu.memory.write(edge - 4, bytes(8))
        assert emu.memory.read(edge - 4, 4) == before
        with pytest.raises(ValueError):
            emu.memory.read(0xFFFFFFFC, 8)
        assert emu.run(1).stopped_by == "frames"


def test_m5_stock_core_refuses(host_paths, stock_core, workdir, seed):
    emu, glob, _ = boot(host_paths, stock_core, workdir, seed)
    with emu:
        mem = emu.memory
        calls = [lambda: mem.read(glob, 4), lambda: mem.write(glob, b"abcd"),
                 lambda: emu.run(1, watch=[(glob, 1)])]
        for name, width in mem.widths.items():
            calls.append(lambda width=width: width.raw_read(glob))
            calls.append(lambda width=width: width(glob))
        calls += [lambda: mem.write_u8(glob, 1), lambda: mem.write_u16(glob, 1), lambda: mem.write_u32(glob, 1),
                  lambda: mem.write_u64(glob, 1)]
        for call in calls:
            with pytest.raises(NeedsLazpyCore):
                call()
        assert emu.run(1).stopped_by == "frames"


def test_m7_abi_2_state_loads(host_paths, lazpy_core, workdir, seed):
    state = workdir / "st" / "state"
    with dh.boot(host_paths, workdir / "a", seed(), core=lazpy_core) as emu:
        emu.run(60)
        emu.save_state(state)
    meta = Path(f"{state}.meta")
    text = meta.read_bytes().decode()
    assert "abi=3\n" in text
    meta.write_bytes(text.replace("abi=3\n", "abi=2\n", 1).encode())
    with Emulator(host_paths.app, workdir / "b", state=state, core=lazpy_core) as emu:
        assert emu.run(10).stopped_by == "frames"
        note("m7: a state with abi=2 in its meta loaded under ABI 3 and ran 10 frames")
