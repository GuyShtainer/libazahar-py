"""Step C's gate (docs/plans/phase-c.md section 8): headless, stock core, test app, 2D. Prints PASS/FAIL per check."""
import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from libazahar import _slots  # noqa: E402
import checks_c as cc  # noqa: E402
import testapp_log as tl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "c-gate"
RC_FILE = ROOT / "runs" / "c-gate.rc"
APP = "build/testapp.3dsx"
LOG = "testapp/log.txt"
BITS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15]
COMBOS = [(1 << 0) | (1 << 1), (1 << 8) | (1 << 9) | (1 << 14) | (1 << 15), (1 << 3) | (1 << 2) | (1 << 6)]
CIRCLES = [(32767, 0), (0, 32767), (-32767, -32767), (16384, -16384), (0, 0)]
TOUCHES = [(0, 0), (319, 0), (0, 239), (319, 239), (160, 120), (10, 63), (20, 125), (30, 126), (40, 127), (1, 1),
           (318, 238), (100, 62), (200, 64), (50, 200), (250, 30), (10, 128), (300, 124), (159, 159), (160, 63), (80, 126)]
CORE_FLAGS: list[str] = []      # --core PATH when main() was given one; run_azhost appends it
KIND = "stock"                  # "stock" or "lazpy": which expectations the scenarios use
NM = "/usr/bin/nm"
EXIT_PATH_LINE = "the guest stopped the host; the host process exits now"     # host/env.c exit_path()
passed = failed = 0


def report(ident: str, ok: bool, detail: str, slow: bool = False) -> None:
    """Print one PASS/FAIL line and count it."""
    global passed, failed
    passed += ok
    failed += not ok
    print(f"{'PASS' if ok else ('FAIL slow' if slow else 'FAIL')} {ident} {detail}", flush=True)


def run_azhost(ident: str, flags: list[str], control: dict, timeout: int = 600) -> dict:
    """Fresh runs/c-gate/<ident>/, one azhost run (nice, own child only); returns rc, summaries, last lines, paths."""
    base = RUNS / ident
    shutil.rmtree(base, ignore_errors=True)
    for name in ("sys", "out"):
        (base / name).mkdir(parents=True)
    tl.write_control(base / "seed", **control)
    cmd = ["nice", "-n", "10", "build/azhost", "run", APP, "--sys", str(base / "sys"), "--out", str(base / "out"),
           "--sd-seed", str(base / "seed")] + CORE_FLAGS + flags
    slot = _slots.acquire()         # the wait is outside communicate(timeout=...); the child keeps the lock
    try:
        child = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 pass_fds=(slot.fd,))
    finally:
        slot.release()
    try:
        out, err = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        child.kill()
        out, err = child.communicate()
        report(ident, False, "timeout")
        return {"rc": -9, "summaries": [], "last": {}, "waited_s": slot.waited_s, "stderr": err, "out": base / "out", "log": base / "sys/Azahar/sdmc" / LOG}
    except BaseException:
        child.kill()
        child.wait()
        raise
    sums = [cc.parse_summary(x) for x in out.splitlines() if x.startswith("frames=")]
    last = {}
    for x in out.splitlines():
        if x.startswith("last "):
            head, _, text = x.partition(": ")
            last[int(head.split()[1])] = tl.parse_line(text)
    return {"rc": child.returncode, "summaries": sums, "last": last, "waited_s": slot.waited_s, "stderr": err, "out": base / "out",
            "log": base / "sys/Azahar/sdmc" / LOG}


def get_log(res: dict) -> tuple[list[dict], list[dict]]:
    return tl.parse_log(res["log"]) if res["log"].exists() else ([], [])


def c_values(ident: str, res: dict) -> tuple[list[int], int]:
    cs = cc.boot_offsets(res["summaries"], res["last"])
    print(f"INFO {ident} c values {cs}", flush=True)
    return cs, (min(cs) if cs else 0)


def write_inputs(path: Path, states: list[tuple]) -> None:
    """states: (frame, buttons, touch_down, x, y, cx, cy) -> one record per line."""
    rows = [f"{f} {b} {x} {y} {d} {cx} {cy}" for f, b, d, x, y, cx, cy in states]
    path.write_text("\n".join(rows) + "\n")


def plan_a() -> tuple[list[tuple], list[tuple], int, list[tuple]]:
    """Scenario a: record states, (frame, buttons) list, the last frame, circle (frame, cx, cy)."""
    states, buttons, frame = [], [], 300
    for mask in [1 << b for b in BITS] + COMBOS:
        for f, m in ((frame, mask), (frame + 6, 0)):
            states.append((f, m, 0, 0, 0, 0, 0))
            buttons.append((f, m))
        frame += 12
    circles = []
    for cx, cy in CIRCLES:
        states.append((frame, 0, 0, 0, 0, cx, cy))
        circles.append((frame, cx, cy))
        frame += 10
    return states, buttons, frame, circles


def check_runs(rid: str, lines: list[dict], buttons: list[tuple], c_min: int, shift: int) -> None:
    """a1: per bit every planned rise is found 0..3 host frames late and held for its frames plus or minus one."""
    bad = []
    for bit in BITS:
        planned = [(f + shift, buttons[i + 1][0] - f) for i, (f, m) in enumerate(buttons) if m >> bit & 1]
        runs = cc.bit_runs(lines, bit, c_min)
        if len(runs) != len(planned):
            bad.append(f"bit {bit}: {len(runs)} runs, want {len(planned)}")
            continue
        for (first, count), (p, length) in zip(runs, planned):
            if not (0 <= first - p <= 3 and abs(count - length) <= 1):
                bad.append(f"bit {bit}: run at {first} x{count}, planned {p} x{length}")
    for mask in COMBOS:
        starts = [cc.bit_runs(lines, b, c_min)[-1][0] for b in BITS if mask >> b & 1 and cc.bit_runs(lines, b, c_min)]
        if starts and max(starts) - min(starts) > 1:
            bad.append(f"combo {mask:#x} rises spread over {min(starts)}..{max(starts)}")
    report(rid, not bad, "every planned rise and hold found" if not bad else "; ".join(bad[:4]))


def scenario_a(n: int, plant: bool) -> None:
    states, buttons, last_frame, circles = plan_a()
    shift = 2 if plant else 0
    ident = f"a.{n}"
    write_inputs(RUNS.parent / "c-a-inputs.txt", states)
    res = run_azhost(ident, ["--frames", "900,1,1,1,1,1,1,1,1", "--inputs", str(RUNS.parent / "c-a-inputs.txt"),
                             "--shot", "600", "--print-last-line", LOG], {})
    lines, _ = get_log(res)
    cs, c_min = c_values(ident, res)
    check_runs(f"a1.{n}", lines, buttons, c_min, shift)
    for kind, mask in (("hid", cc.HID_MASK), ("irrst", cc.IRRST_MASK)):
        plan, prev = [], 0
        for f, m in buttons:
            if m & mask != prev:
                plan.append((f + shift, (m & mask,)))
                prev = m & mask
        offs = cc.change_offsets(lines, plan, kind, c_min)
        ok, m, counts = cc.offsets_ok(offs)
        report(f"a2.{n}.{kind}", ok, f"m={m} counts={counts}")
        if ok and m != 0:
            print(f"NOTE a2.{n} m={m} ({kind})", flush=True)
    plan = [(f, (cc.circle_expected(cx), cc.circle_expected(cy))) for f, cx, cy in circles]
    offs = cc.change_offsets(lines, plan, "circle", c_min)
    ok, m, counts = cc.offsets_ok(offs)
    report(f"a3.{n}", ok, f"m={m} counts={counts}")
    s0 = res["summaries"][0] if res["summaries"] else {}
    shot = res["out"] / "shot_000600"
    mk = subprocess.run([sys.executable, "-I", "tests/check_testapp.py", "markers", "--top", f"{shot}_top.png", "--bottom",
                         f"{shot}_bottom.png", "--mode", "2d"], cwd=ROOT, capture_output=True, text=True)
    report(f"a4.{n}", s0.get("stop") == "frames" and s0.get("vblanks") == 900 and "markers ok" in mk.stdout,
           f"stop={s0.get('stop')} vblanks={s0.get('vblanks')} {mk.stdout.strip()}")


def scenario_b() -> None:
    states, plan, frame = [], [], 300
    for x, y in TOUCHES:
        states += [(frame, 0, 1, x, y, 0, 0), (frame + 6, 0, 0, 0, 0, 0, 0)]
        plan += [(frame, (*cc.touch_expected(x, y), 1)), (frame + 6, (-1, -1, 0))]
        frame += 12
    states += [(690, 0, 1, 160, 120, 0, 0), (720, 0, 0, 0, 0, 0, 0)]
    write_inputs(RUNS.parent / "c-b-inputs.txt", states)
    res = run_azhost("b", ["--frames", "800,1,1,1,1,1,1,1,1", "--inputs", str(RUNS.parent / "c-b-inputs.txt"), "--shot",
                           "700,780", "--print-last-line", LOG], {})
    lines, _ = get_log(res)
    _, c_min = c_values("b", res)
    offs = cc.change_offsets(lines, plan, "touch", c_min)
    report("b1", all(o is not None for o in offs), f"{sum(o is not None for o in offs)} of {len(plan)} changes found")
    ok, m, counts = cc.offsets_ok(offs)
    report("b2", ok and m in (1, 2), f"m={m} counts={counts}")
    if ok and m != 1:
        print(f"NOTE b2 m={m}", flush=True)
    boxes = []
    for frame_no in (700, 780):
        w, h, px = tl.read_png(res["out"] / f"shot_{frame_no:06d}_bottom.png")
        boxes.append(b"".join(px[((112 + r) * w + 152) * 4:((112 + r) * w + 169) * 4] for r in range(17)))
    report("b3", boxes[0] == boxes[1] and set(boxes[0][i:i + 4] for i in range(0, len(boxes[0]), 4)) == {bytes([32, 32, 32, 255])},
           "17x17 box identical and #202020")


def delay(frames: list[dict], events: list[dict], name: str) -> int | None:
    ev = [e for e in events if e["kind"] == name]
    return frames[-1]["v"] - ev[0]["v"] if ev and frames else None


def scenario_c() -> None:
    for ident, every, lo, hi in (("c1", 30, 0, 30), ("c2", 1, 0, 1)):
        res = run_azhost(ident, ["--frames", "3000", "--stop-file", LOG, "--stop-text", "ready f=", "--stop-every", str(every)],
                         {"ready_at": 200})
        lines, events = get_log(res)
        d = delay(lines, events, "ready")
        stop = res["summaries"][0]["stop"] if res["summaries"] else None
        report(ident, stop == "sd_text" and d is not None and lo <= d <= hi, f"stop={stop} delay={d} frames")
    res = run_azhost("c3", ["--frames", "300,10000000", "--wall-limit-ms", "3000"], {})
    s = res["summaries"]
    bound = 3.0 + max(1.0, 5.0 * (s[0]["wall_ms_mean"] / 1000.0 if s else 0.0))
    ok_stop = len(s) == 2 and s[1]["stop"] == "wall_limit"
    report("c3", ok_stop and s[1]["wall"] <= bound, f"wall={s[1]['wall'] if len(s) == 2 else None} bound={bound:.2f}",
           slow=ok_stop)
    res = run_azhost("c4", ["--frames", "600", "--debug-stop", "ready f="], {"ready_at": 200})
    if KIND == "lazpy":     # our core honours the debug-text stop (instant_debug_log); the batch ends before frame 600
        s0 = res["summaries"][0] if res["summaries"] else {}
        report("c4", res["rc"] == 0 and s0.get("stop") == "debug_text" and s0.get("last", 600) < 600,
               f"rc={res['rc']} stop={s0.get('stop')} last={s0.get('last')}")
        return
    report("c4", res["rc"] == 7 and res["stderr"].startswith("NeedsLazpyCore:"), f"rc={res['rc']} stderr={res['stderr'][:60]!r}")


def layout_rows() -> dict:
    out = subprocess.run(["build/azhost", "layout"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return cc.parse_layout(out)[1]


def scenario_d() -> None:
    res = run_azhost("d", ["--frames", "300,600,1200,1,1,1,1,1", "--print-last-line", LOG, "--shot", "300", "--raw-shot", "300"], {})
    s = res["summaries"]
    report("d1", len(s) == 8 and all(x["vblanks"] == x["frames"] for x in s), f"vblanks {[x['vblanks'] for x in s]}")
    lines, _ = get_log(res)
    report("d2", all(b["v"] == a["v"] + 1 and b["f"] == a["f"] + 1 for a, b in zip(lines, lines[1:])), f"{len(lines)} lines")
    cs, c_min = c_values("d", res)
    report("d3", all(c in (c_min, c_min + 1) for c in cs), f"c_min={c_min}")
    m = cc.read_map(res["out"] / "host.map", layout_rows())
    w, h, top = tl.read_png(res["out"] / "shot_000300_top.png")
    _, _, bottom = tl.read_png(res["out"] / "shot_000300_bottom.png")
    ok = m["px_frame"] == 300 and m["dims"] == (400, 240, 320, 240) and m["pixels"] == top + bottom
    report("d4", ok, f"px_frame={m['px_frame']} dims={m['dims']} pixels equal={m['pixels'] == top + bottom}")


def scenario_e() -> None:
    res = run_azhost("e", ["--frames", "600,120", "--print-last-line", LOG], {"break_at": 120})
    s = res["summaries"]
    lines, events = get_log(res)
    _, c_min = c_values("e", {**res, "summaries": s[1:], "last": {1: res["last"].get(2)}})
    brk = [e for e in events if e["kind"] == "break"]
    ok = len(s) == 2 and s[0]["stop"] == "guest_break" and "(14)" in s[0]["msg"] and "Exception Type: Break" in s[0]["msg"]
    report("e1", ok and bool(brk) and s[0]["last"] <= brk[0]["v"] + c_min + 2, f"stop={s[0]['stop'] if s else None} last={s[0]['last'] if s else None} break v={brk[0]['v'] if brk else None}")
    report("e2", len(s) == 2 and s[1]["stop"] == "frames" and s[1]["vblanks"] == 120, f"{s[1:]}")
    after = [x for x in lines if brk and x["f"] == brk[0]["f"] + 1]
    report("e3", bool(after), f"line f={brk[0]['f'] + 1 if brk else None} present={bool(after)}")


def scenario_f() -> None:
    res = run_azhost("f", ["--frames", "100,1,1,1,1,1,1,1,600", "--print-last-line", LOG], {"exit_at": 200})
    ours = KIND == "lazpy"
    sums = res["summaries"]
    cs, c_min = c_values("f", {**res, "summaries": sums[:8]} if ours else res)     # batch 9 stops at the exit
    m = cc.read_map(res["out"] / "host.map", layout_rows())
    lines, events = get_log(res)
    ev = [e for e in events if e["kind"] == "exit"]
    host_log = (res["out"] / "host.log").read_text(errors="replace") if (res["out"] / "host.log").exists() else ""
    if ours:    # status 16 does not _exit: a summary with stop=guest_exited, then azhost exits 10; no exit-path line
        report("f1", res["rc"] == 10 and len(sums) == 9 and sums[8]["stop"] == "guest_exited" and "(16)" in sums[8]["msg"],
               f"rc={res['rc']} summaries={len(sums)} stop={sums[8]['stop'] if len(sums) == 9 else None}")
        report("f2", EXIT_PATH_LINE not in host_log and m["stop_code"] == 4 and m["exit_code"] == 0 and "(16)" in sums[-1]["msg"] if sums else False,
               f"stop={m['stop_code']} exit={m['exit_code']} no exit-path line={EXIT_PATH_LINE not in host_log}")
        d = (sums[8]["last"] - (ev[0]["v"] + c_min)) if len(sums) == 9 and ev else None
        report("f3", d is not None and 0 <= d <= 10, f"summary last={sums[8]['last'] if len(sums) == 9 else None} exit delay={d}")
    else:
        report("f1", res["rc"] == 10, f"rc={res['rc']}")
        report("f2", m["stop_code"] == 4 and m["exit_code"] == 10 and "(16)" in m["message"], f"stop={m['stop_code']} exit={m['exit_code']} msg={m['message'][:50]!r}")
        d = m["frame_total"] - (ev[0]["v"] + c_min) if ev else None
        report("f3", d is not None and 0 <= d <= 10, f"frame_total={m['frame_total']} exit delay={d}")
    text = res["log"].read_text().strip().splitlines() if res["log"].exists() else [""]
    report("f4", text[-1].startswith("exit f=200 "), f"last line {text[-1][:40]!r}")


def core_kind(core: str, want: str) -> str:
    """auto: ``nm -gU`` lists _lazpy_read_memory -> lazpy, else stock."""
    if want != "auto":
        return want
    out = subprocess.run([NM, "-gU", core], capture_output=True, text=True, check=False).stdout
    return "lazpy" if "_lazpy_read_memory" in out else "stock"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default="a,b,c,d,e,f")
    ap.add_argument("--core", default=None, help="core to run (default: azhost's own: LAZ_CORE, else the stock core)")
    ap.add_argument("--core-kind", choices=("auto", "stock", "lazpy"), default="auto")
    ap.add_argument("--plant-red", action="store_true", help="shift the expected button frames by 2 (must FAIL a2)")
    args = ap.parse_args()
    only = set(args.only.split(","))
    global KIND
    core = args.core or os.environ.get("LAZ_CORE") or "dl/azahar/azahar_libretro.dylib"
    KIND = core_kind(core, args.core_kind)
    if args.core:
        CORE_FLAGS[:] = ["--core", args.core]
    print(f"core={core} kind={KIND}", flush=True)
    RC_FILE.parent.mkdir(parents=True, exist_ok=True)
    RC_FILE.unlink(missing_ok=True)
    rc = 1
    try:
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
        RUNS.mkdir(parents=True, exist_ok=True)
        jobs = [("a1", "a", lambda: scenario_a(1, args.plant_red)), ("a2", "a", lambda: scenario_a(2, args.plant_red)),
                ("b", "b", scenario_b), ("c", "c", scenario_c), ("d", "d", scenario_d), ("e", "e", scenario_e),
                ("f", "f", scenario_f)]
        for label, key, fn in jobs:
            if key not in only:
                continue
            try:
                fn()
            except (OSError, KeyError, IndexError, ValueError) as exc:     # a missing file must show as FAIL, not a traceback
                report(label, False, f"scenario error {type(exc).__name__}: {exc}")
        print(f"gate_c: {passed} passed, {failed} failed", flush=True)
        rc = 0 if failed == 0 and passed > 0 else 1
        return rc
    finally:
        RC_FILE.write_text(f"{rc}\n")


if __name__ == "__main__":
    sys.exit(main())
