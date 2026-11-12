"""Step C's gate scenarios (phase-c.md section 8) through the Python API, on the stock core and the test app."""
from __future__ import annotations

import sys

import pytest

import checks_c as cc
import d_helpers as dh
import gate_c
import testapp_log as tl
from libazahar import Buttons, Circle, NeedsLazpyCore, Touch

pytestmark = pytest.mark.slow


def info(text: str) -> None:
    print(text, file=sys.stderr)


def movie(states):
    """gate_c's (frame, buttons, down, x, y, cx, cy) states as Emulator inputs."""
    items = []
    for frame, buttons, down, x, y, cx, cy in states:
        items += [(frame, Buttons(buttons)), (frame, Touch(x, y) if down else Touch.up), (frame, Circle(cx, cy))]
    return items


def check_runs(lines, buttons, c_min):
    """a1: per bit every planned rise is found 0..3 host frames late and held for its frames plus or minus one."""
    bad = []
    for bit in gate_c.BITS:
        planned = [(f, buttons[i + 1][0] - f) for i, (f, m) in enumerate(buttons) if m >> bit & 1]
        runs = cc.bit_runs(lines, bit, c_min)
        if len(runs) != len(planned):
            bad.append(f"bit {bit}: {len(runs)} runs, want {len(planned)}")
            continue
        for (first, count), (p, length) in zip(runs, planned):
            if not (0 <= first - p <= 3 and abs(count - length) <= 1):
                bad.append(f"bit {bit}: run at {first} x{count}, planned {p} x{length}")
    for mask in gate_c.COMBOS:
        starts = [cc.bit_runs(lines, b, c_min)[-1][0] for b in gate_c.BITS if mask >> b & 1 and cc.bit_runs(lines, b, c_min)]
        if starts and max(starts) - min(starts) > 1:
            bad.append(f"combo {mask:#x} spread {min(starts)}..{max(starts)}")
    assert not bad, "; ".join(bad[:4])


def test_a_buttons_and_circle(host_paths, workdir):
    states, buttons, _, circles = gate_c.plan_a()
    with dh.boot(host_paths, workdir) as emu:
        results, offsets, c_min = dh.run_batches(emu, [900] + [1] * 8, movie(states), [600])
        lines, _ = dh.log_of(emu)
        info(f"a: c values {offsets}")
        check_runs(lines, buttons, c_min)
        for kind, mask in (("hid", cc.HID_MASK), ("irrst", cc.IRRST_MASK)):
            plan, prev = [], 0
            for f, m in buttons:
                if m & mask != prev:
                    plan.append((f, (m & mask,)))
                    prev = m & mask
            ok, m, counts = cc.offsets_ok(cc.change_offsets(lines, plan, kind, c_min))
            info(f"a2 {kind}: m={m} counts={counts}")
            assert ok, f"{kind} m={m} counts={counts}"
        plan = [(f, (cc.circle_expected(cx), cc.circle_expected(cy))) for f, cx, cy in circles]
        ok, m, counts = cc.offsets_ok(cc.change_offsets(lines, plan, "circle", c_min))
        info(f"a3 circle: m={m} counts={counts}")
        assert ok
        first = results[0]
        assert first.stopped_by == "frames" and first.vblanks == 900 and first.frames == 900
        shot = first.shots[600]
        assert "markers ok" in dh.markers_ok(shot.top, shot.bottom)


def test_b_touch(host_paths, workdir):
    states, plan, frame = [], [], 300
    for x, y in gate_c.TOUCHES:
        states += [(frame, 0, 1, x, y, 0, 0), (frame + 6, 0, 0, 0, 0, 0, 0)]
        plan += [(frame, (*cc.touch_expected(x, y), 1)), (frame + 6, (-1, -1, 0))]
        frame += 12
    states += [(690, 0, 1, 160, 120, 0, 0), (720, 0, 0, 0, 0, 0, 0)]
    with dh.boot(host_paths, workdir) as emu:
        results, _, c_min = dh.run_batches(emu, [800] + [1] * 8, movie(states), [700, 780])
        lines, _ = dh.log_of(emu)
        offsets = cc.change_offsets(lines, plan, "touch", c_min)
        assert all(o is not None for o in offsets)
        ok, m, counts = cc.offsets_ok(offsets)
        info(f"b touch: m={m} counts={counts}")
        assert ok and m in (1, 2)
        boxes = []
        for frame_no in (700, 780):
            w, _, px = tl.read_png(results[0].shots[frame_no].bottom)
            boxes.append(b"".join(px[((112 + r) * w + 152) * 4:((112 + r) * w + 169) * 4] for r in range(17)))
        assert boxes[0] == boxes[1]
        assert {boxes[0][i:i + 4] for i in range(0, len(boxes[0]), 4)} == {bytes([32, 32, 32, 255])}


def run_sd_stop(host_paths, workdir, seed, every, lo, hi):
    with dh.boot(host_paths, workdir, seed(ready_at=200)) as emu:
        result = emu.run_until(dh.LOG, "ready f=", 3000, every=every)
        frames, events = dh.log_of(emu)
        ready = [e for e in events if e["kind"] == "ready"]
        delay = frames[-1]["v"] - ready[0]["v"]
        assert result.stopped_by == "sd_text" and lo <= delay <= hi, f"stop={result.stopped_by} delay={delay}"


def test_c1_sd_every_30(host_paths, workdir, seed):
    run_sd_stop(host_paths, workdir, seed, 30, 0, 30)


def test_c2_sd_every_1(host_paths, workdir, seed):
    run_sd_stop(host_paths, workdir, seed, 1, 0, 1)


def test_c_stop_new(host_paths, workdir, seed):
    """N6: with new_only the text already in the file does not stop the batch; without it, it does at once."""
    with dh.boot(host_paths, workdir, seed(ready_at=100)) as emu:
        first = emu.run_until(dh.LOG, "ready f=", 3000, every=1)
        assert first.stopped_by == "sd_text"
        fresh = emu.run_until(dh.LOG, "ready f=", 90, every=1, new_only=True)
        assert fresh.stopped_by == "frames" and fresh.frames == 90
        old = emu.run_until(dh.LOG, "ready f=", 90, every=1)
        assert old.stopped_by == "sd_text" and old.frames == 1


def test_c3_wall_limit(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        first = emu.run(300)
        second = emu.run(10_000_000, wall_limit=3.0)
        bound = 3.0 + max(1.0, 5.0 * first.wall_s / first.frames)
        info(f"c3: wall {second.wall_s:.2f} bound {bound:.2f}")
        assert second.stopped_by == "wall_limit" and second.wall_s <= bound


def test_c4_debug_text_needs_our_core(host_paths, stock_core, workdir, seed):
    """Debug text is refused on the stock core, so this test names it whatever ``LAZ_CORE`` says."""
    with dh.boot(host_paths, workdir, seed(ready_at=200), core=stock_core) as emu:
        with pytest.raises(NeedsLazpyCore):
            emu.run(600, debug_text="ready f=")


def test_d_counters_and_raw_screens(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        first = emu.run(300, shots=[300])
        top, bottom = emu.screens()
        png_top = tl.read_png(first.shots[300].top)
        png_bottom = tl.read_png(first.shots[300].bottom)
        assert top.tobytes() == png_top[2] and bottom.tobytes() == png_bottom[2]
        assert emu._client.host_map().px_frame() == 300 == emu.frame_total
        assert emu._client.host_map().pixels(1).readonly
        assert top.shape == (240, 400, 4) and bottom.shape == (240, 320, 4)
        results = [first] + [emu.run(n) for n in (600, 1200, 1, 1, 1, 1, 1)]
        assert all(r.vblanks == r.frames for r in results)
        frames, _ = dh.log_of(emu)
        assert all(b["v"] == a["v"] + 1 and b["f"] == a["f"] + 1 for a, b in zip(frames, frames[1:]))
        assert emu.frame_total == sum(r.frames for r in results)


def test_e_break_is_a_stop_not_an_error(host_paths, workdir, seed):
    with dh.boot(host_paths, workdir, seed(break_at=120)) as emu:
        first = emu.run(600)
        assert first.stopped_by == "guest_break"
        assert "(14)" in first.message and "Exception Type: Break" in first.message
        second = emu.run(120)
        frames, events = dh.log_of(emu)
        c_min = second.last_frame - frames[-1]["v"]
        brk = [e for e in events if e["kind"] == "break"]
        assert brk and first.last_frame <= brk[0]["v"] + c_min + 2
        assert second.stopped_by == "frames" and second.vblanks == 120
        assert any(x["f"] == brk[0]["f"] + 1 for x in frames)


def test_f_guest_exit(host_paths, workdir, seed):
    with dh.boot(host_paths, workdir, seed(exit_at=200)) as emu:
        offsets = []
        for size in [100] + [1] * 7:
            result = emu.run(size)
            frames, _ = dh.log_of(emu)
            offsets.append(result.last_frame - frames[-1]["v"])
        c_min = min(offsets)
        result = emu.run(600)
        frames, events = dh.log_of(emu)
        exits = [e for e in events if e["kind"] == "exit"]
        assert result.stopped_by == "guest_exited" and emu.closed and "(16)" in result.message
        delay = result.frame_total - (exits[0]["v"] + c_min)
        assert 0 <= delay <= 10, f"frame_total {result.frame_total} delay {delay}"
        assert result.frames == result.last_frame - result.first_frame + 1
        text = (emu.sd / dh.LOG).read_text().strip().splitlines()
        assert text[-1].startswith("exit f=200 ")

