#!/usr/bin/env python3
"""The 1-2-3-4 instance speed table with the guest-time check and the cap rule (docs/plans/phase-e.md section 7).

    nice -n 10 python3 -I tools/speed_table.py --app build/testapp.3dsx --core <path> [--core <path2>]
        [--cap-core <path>] [--instances 1,2,3,4] [--seconds 60] [--extra-rows | --only-extra] --out runs/e-speed

Test-app numbers are a light scene (docs/map/rules.md 7), not a game's. 4-instance rows run only on the cap core.
Instances go through the real slot folder with ``LAZ_MAX_INSTANCES`` set to 4 for this process.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _folder in (REPO / "python", REPO / "tests"):
    sys.path.insert(0, str(_folder))
import testapp_log  # noqa: E402
from libazahar import Emulator, _slots  # noqa: E402

TICKS_PER_FRAME = 4_481_136
CLOCK_HZ = 268_111_856
VBLANK_HZ = 59.831
WARMUP_FRAMES = 300
BOOT_TIMEOUT = 300.0
TICK_TOLERANCE = 0.01
XREAL_TOLERANCE = 0.02
STEP_UP_GAIN = 1.25
ROUND_TRIP_FRAMES = 600
SHOT_COUNT = 20
SHOT_LEVELS = (1, 6)
BATCH_RE = re.compile(r"batch frames=(\d+) wall_ms=([\d.]+) core_ms=([\d.]+) host_ms=([\d.]+) shot_ms=([\d.]+) "
                      r"stop=(\w+)")


def cap_rule(rows, cpu_count):
    """The default cap from the cap core's rows (``n``, ``total_host_fps``, ``load_end``, ``check_ok``).

    Any failed check: cap 3 unchanged. Else start at 1 and step up to n (2, 3, 4 in order) only if total fps at n is
    at least 1.25 x the total at n-1 and the load at the end of the n row is under 2 x cpu_count; stop at the first
    n that fails. Returns ``(cap, reasons)``.
    """
    by_n = {row["n"]: row for row in rows}
    if any(not row["check_ok"] for row in rows):
        return 3, ["a cap-core row is CHECK FAIL: the table is not used, the cap stays 3"]
    cap_now, reasons = 1, []
    for n in (2, 3, 4):
        if n not in by_n or n - 1 not in by_n:
            reasons.append(f"no row for n={n}: stop at {cap_now}")
            break
        gain = by_n[n]["total_host_fps"] / by_n[n - 1]["total_host_fps"]
        if gain < STEP_UP_GAIN:
            reasons.append(f"n={n}: total fps x{gain:.2f} of n={n - 1} is under x{STEP_UP_GAIN}: stop at {cap_now}")
            break
        if by_n[n]["load_end"] >= 2 * cpu_count:
            reasons.append(f"n={n}: load {by_n[n]['load_end']:.1f} is not under 2 x {cpu_count}: stop at {cap_now}")
            break
        cap_now = n
        reasons.append(f"n={n}: total fps x{gain:.2f} and load {by_n[n]['load_end']:.1f}: step up")
    return cap_now, reasons


def nice_of(pid):
    """The worker's nice value, or None."""
    done = subprocess.run(["ps", "-o", "nice=", "-p", str(pid)], capture_output=True, text=True, check=False)
    text = done.stdout.strip()
    return int(text) if text.lstrip("-").isdigit() else None


def last_frame_line(emu):
    """(f, s) of the app's last complete per-frame log line."""
    frames, _ = testapp_log.parse_log(emu.sd / "testapp" / "log.txt")
    return (frames[-1]["f"], frames[-1]["s"]) if frames else (0, 0)


def batch_line(workdir):
    """The last host.log timing line of a wall_limit batch as a dict (ms floats), or None."""
    found = None
    for line in (Path(workdir) / "host.log").read_text(errors="replace").splitlines():
        match = BATCH_RE.search(line)
        if match and match.group(6) == "wall_limit":
            found = {"frames": int(match.group(1)), "wall_ms": float(match.group(2)),
                     "core_ms": float(match.group(3)), "host_ms": float(match.group(4)),
                     "shot_ms": float(match.group(5))}
    return found


OPTION_RE = re.compile(r"\] option (\w+=.*)$")


def option_lines(workdir):
    """The ``option key=value`` lines of a host.log (the effective option set), without the log prefix."""
    out = []
    for line in (Path(workdir) / "host.log").read_text(errors="replace").splitlines():
        match = OPTION_RE.search(line)
        if match:
            out.append(match.group(1).strip())
    return out


def make_seed(folder):
    """An SD seed folder whose control file draws in 3D."""
    testapp_log.write_control(folder, draw="3d")
    return folder


def measure(emu, workdir, seconds):
    """One instance's measured batch: the numbers of section 7 step 2-3 plus its guest-time check."""
    load0 = os.getloadavg()[0]
    s0_stats = emu.stats()
    f0, t0 = last_frame_line(emu)
    result = emu.run(10_000_000, wall_limit=seconds)
    s1_stats = emu.stats()
    f1, t1 = last_frame_line(emu)
    nice = nice_of(emu.pid)
    timing = batch_line(workdir)
    wall = result.wall_s
    host_fps = result.frames / wall
    ticks_per_vblank = (t1 - t0) / result.vblanks if result.vblanks else 0.0
    x_real = (t1 - t0) / CLOCK_HZ / wall
    cpu_s = (s1_stats.user_s + s1_stats.sys_s) - (s0_stats.user_s + s0_stats.sys_s)
    tick_ok = abs(ticks_per_vblank / TICKS_PER_FRAME - 1.0) <= TICK_TOLERANCE
    x_ok = abs(x_real / (host_fps / VBLANK_HZ) - 1.0) <= XREAL_TOLERANCE
    return {"frames": result.frames, "wall_s": wall, "stopped_by": result.stopped_by, "host_fps": host_fps,
            "app_fps": (f1 - f0) / wall, "x_real": x_real, "ticks_per_vblank": ticks_per_vblank,
            "cpu_ms": cpu_s * 1000.0 / result.frames, "wall_ms": wall * 1000.0 / result.frames,
            "peak_rss": s1_stats.peak_rss, "nice": nice, "load_start": load0, "load_end": os.getloadavg()[0],
            "host_share": (timing["host_ms"] / timing["wall_ms"]) if timing else None, "timing": timing,
            "check_ok": bool(tick_ok and x_ok and result.stopped_by == "wall_limit"),
            "tick_ok": tick_ok, "x_ok": x_ok, "pid": emu.pid, "core_version": s1_stats.core_version}


def instance(args, core, folder, barrier, out, index):
    """One thread: boot, warm up, wait at the barrier, measure; the result or the error goes in ``out[index]``."""
    emu = None
    try:
        begin = time.time()
        emu = Emulator(args.app, folder, sd_seed=make_seed(folder.parent / f"seed{index}"), core=core,
                       boot_timeout=BOOT_TIMEOUT)
        emu.run(WARMUP_FRAMES)
        wait = time.time() - begin
        barrier.wait()
        out[index] = measure(emu, folder, args.seconds)
        out[index]["boot_s"] = wait
        out[index]["slot_wait_s"] = float((folder / "slot.txt").read_text().split("waited_s=")[1])
    except threading.BrokenBarrierError:
        out[index] = {"error": "barrier broken", "check_ok": False}
    except Exception as error:  # noqa: BLE001  (recorded in the row, never hidden; the row is CHECK FAIL)
        barrier.abort()
        out[index] = {"error": f"{type(error).__name__}: {error}", "check_ok": False}
    finally:
        if emu is not None:
            emu.close()


def run_row(args, core, n):
    """n instances at once on one core; the row dict."""
    tag = f"{Path(core).stem}-n{n}"
    base = Path(args.out) / tag
    base.mkdir(parents=True, exist_ok=True)
    barrier = threading.Barrier(n, timeout=1800 + BOOT_TIMEOUT)
    out = [None] * n
    threads = [threading.Thread(target=instance, args=(args, core, base / f"i{k}", barrier, out, k)) for k in range(n)]
    load_start = os.getloadavg()[0]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    good = [o for o in out if o and "error" not in o]
    row = {"core": str(core), "n": n, "instances": out, "load_start": load_start, "load_end": os.getloadavg()[0],
           "date": datetime.datetime.now().isoformat(timespec="seconds"),
           "check_ok": len(good) == n and all(o["check_ok"] for o in good),
           "total_host_fps": sum(o["host_fps"] for o in good), "total_app_fps": sum(o["app_fps"] for o in good)}
    if len(good) != n:
        row["check_fail"] = "slot: " + "; ".join(o["error"] for o in out if o and "error" in o)
    print(f"row {tag}: total host fps {row['total_host_fps']:.1f} check_ok={row['check_ok']}", flush=True)
    return row


def extra_round_trip(args, core):
    """600 x run(1) against one run(600) on a single instance."""
    folder = Path(args.out) / "extra-roundtrip"
    with Emulator(args.app, folder, sd_seed=make_seed(folder.parent / "seed-rt"), core=core,
                  boot_timeout=BOOT_TIMEOUT) as emu:
        emu.run(WARMUP_FRAMES)
        begin = time.perf_counter()
        for _ in range(ROUND_TRIP_FRAMES):
            emu.run(1)
        single = (time.perf_counter() - begin) * 1000.0 / ROUND_TRIP_FRAMES
        begin = time.perf_counter()
        emu.run(ROUND_TRIP_FRAMES)
        batched = (time.perf_counter() - begin) * 1000.0 / ROUND_TRIP_FRAMES
    return {"run1_ms_per_frame": single, "run600_ms_per_frame": batched, "per_call_ms": single - batched}


def extra_shots(args, core):
    """20 shots at LAZ_PNG_LEVEL 1 and 6, a fresh Emulator for each level."""
    rows = []
    for level in SHOT_LEVELS:
        os.environ["LAZ_PNG_LEVEL"] = str(level)
        folder = Path(args.out) / f"extra-shots-l{level}"
        with Emulator(args.app, folder, sd_seed=make_seed(folder.parent / f"seed-sh{level}"), core=core,
                      boot_timeout=BOOT_TIMEOUT) as emu:
            emu.run(WARMUP_FRAMES)
            begin = time.perf_counter()
            for k in range(SHOT_COUNT):
                top, _ = emu.shot(folder / "shots" / f"x{k}")
            ms = (time.perf_counter() - begin) * 1000.0 / SHOT_COUNT
            size = Path(top).stat().st_size
            emu.run(1)
        png_line = next((ln.split("] ")[-1] for ln in (folder / "host.log").read_text().splitlines()
                         if "png level=" in ln), "")
        rows.append({"level": level, "ms_per_shot": ms, "top_png_bytes": size, "log_line": png_line})
    os.environ.pop("LAZ_PNG_LEVEL", None)
    return rows


def md_core_table(core, rows):
    """One Markdown table for a core."""
    head = ["| n | total host fps | per-instance host fps | app fps | x real | cpu ms/frame | wall ms/frame | host share "
            "| peak RSS MB | nice | load start/end | slot wait s | check |", "|" + "---|" * 13]
    for row in rows:
        good = [o for o in row["instances"] if o and "error" not in o]
        if not good:
            head.append(f"| {row['n']} | CHECK FAIL {row.get('check_fail', '')} |" + " |" * 11)
            continue
        join = lambda key, fmt: " / ".join(format(o[key], fmt) for o in good)  # noqa: E731
        share = [o["host_share"] for o in good if o["host_share"] is not None]
        head.append("| {n} | {tot:.1f} | {fps} | {app} | {x} | {cpu} | {wall} | {share} | {rss} | {nice} | {l0:.1f}/{l1:.1f} "
                    "| {wait} | {chk} |".format(
                        n=row["n"], tot=row["total_host_fps"], fps=join("host_fps", ".1f"), app=join("app_fps", ".1f"),
                        x=join("x_real", ".2f"), cpu=join("cpu_ms", ".1f"), wall=join("wall_ms", ".1f"),
                        share=" / ".join(f"{100 * v:.1f}%" for v in share) or "n/a",
                        rss=" / ".join(f"{o['peak_rss'] / 1e6:.0f}" for o in good),
                        nice=" / ".join(str(o["nice"]) for o in good), l0=row["load_start"], l1=row["load_end"],
                        wait=" / ".join(f"{o.get('slot_wait_s', 0):.1f}" for o in good),
                        chk="ok" if row["check_ok"] else "CHECK FAIL"))
    return f"### {core}\n\n" + "\n".join(head) + "\n"


def write_outputs(args, data):
    """table.json and table.md."""
    out = Path(args.out)
    (out / "table.json").write_text(json.dumps(data, indent=1, default=str))
    parts = [f"# Speed table (light scene: the test app, rules.md 7), {data['date']}\n"]
    for core, rows in data["cores"].items():
        parts.append(md_core_table(core, rows))
    if data.get("cap"):
        parts.append(f"Cap rule on {data['cap_core']}: cap {data['cap']['cap']} (provisional, light scene). "
                     + "; ".join(data["cap"]["reasons"]) + "\n")
    if data.get("round_trip"):
        parts.append(f"Round trip: {json.dumps(data['round_trip'])}\n")
    if data.get("shots"):
        parts.append(f"Shots: {json.dumps(data['shots'])}\n")
    for core, options in data.get("options", {}).items():
        parts.append(f"Effective options of {core}:\n\n```\n" + "\n".join(options) + "\n```\n")
    (out / "table.md").write_text("\n".join(parts))


def parse_args(argv):
    """The command line."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", required=True)
    ap.add_argument("--core", action="append", required=True)
    ap.add_argument("--cap-core")
    ap.add_argument("--instances", default="1,2,3,4")
    ap.add_argument("--seconds", type=float, default=60.0)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--extra-rows", action="store_true")
    group.add_argument("--only-extra", action="store_true")
    ap.add_argument("--out", required=True)
    return ap.parse_args(argv)


def main(argv):
    """Run the rows; write table.json and table.md; print the cap."""
    args = parse_args(argv)
    os.environ["LAZ_MAX_INSTANCES"] = "4"          # before any acquisition: the n=4 row holds slots 0-3
    args.app = str(Path(args.app).resolve())
    args.out = str(Path(args.out).resolve())
    cores = [str(Path(c).resolve()) for c in args.core]
    cap_core = str(Path(args.cap_core).resolve()) if args.cap_core else next(
        (c for c in cores if "lazpy" in Path(c).name), cores[0])
    counts = [int(v) for v in args.instances.split(",")]
    Path(args.out).mkdir(parents=True, exist_ok=True)
    data = {"date": datetime.datetime.now().isoformat(timespec="seconds"), "cores": {}, "options": {},
            "cap_core": cap_core, "cpu_count": os.cpu_count(), "args": vars(args)}
    if not args.only_extra:
        for core in cores:
            rows = []
            for n in counts:
                if n > 3 and core != cap_core:
                    continue
                rows.append(run_row(args, core, n))
                data["cores"][core] = rows
                if n == 1 and rows[-1]["instances"][0] and "error" not in rows[-1]["instances"][0]:
                    data["options"][core] = option_lines(Path(args.out) / f"{Path(core).stem}-n1" / "i0")
                write_outputs(args, data)
        cap_rows = [r for r in data["cores"].get(cap_core, [])]
        cap, reasons = cap_rule(cap_rows, os.cpu_count() or 1)
        data["cap"] = {"cap": cap, "reasons": reasons}
        print(f"cap rule on {cap_core}: {cap} {reasons}", flush=True)
    if args.extra_rows or args.only_extra:
        data["round_trip"] = extra_round_trip(args, cap_core)
        data["shots"] = extra_shots(args, cap_core)
    write_outputs(args, data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
