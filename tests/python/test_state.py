"""State boot (PLAN Phase D gate): boot once, save, start from the state in a second instance."""
from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

import pytest

import d_helpers as dh
from libazahar import _slots, _abi, Buttons, Circle, Emulator, StateError, Touch, _map

pytestmark = pytest.mark.slow

FIELDS = ("k", "tx", "ty", "td", "cx", "cy")
INPUTS = [(50, Buttons.A), (60, Buttons(0)), (100, Touch(100, 100)), (150, Touch.up), (200, Circle(20000, 0)),
          (250, Circle(0, 0)), (300, Buttons.X | Buttons.L), (320, Buttons(0)), (400, Touch(5, 200)),
          (450, Touch.up), (500, Buttons.START)]
SHOTS = [100, 300, 600]


def keyed(frames, floor, shift=0):
    return {row["v"] + shift: tuple(row[k] for k in FIELDS) for row in frames if row["v"] > floor}


def test_state_boot(host_paths, workdir, seed):
    plant = os.environ.get("LAZ_TEST_PLANT_RED") == "1"
    wd_a, wd_b = workdir / "a", workdir / "b"
    state = workdir / "st" / "state"
    start = time.monotonic()
    emu_a = Emulator(host_paths.app, wd_a, sd_seed=seed(boot_frames=6000))
    wait_a = _slots.waited_in(wd_a)
    t_core_start = time.monotonic() - start - wait_a
    try:
        emu_a.run_until(dh.LOG, "booted f=", 12_000)
        t_boot = time.monotonic() - start - wait_a
        frames_before, _ = dh.log_of(emu_a)
        info = emu_a.save_state(state)
        result_a = emu_a.run(600, inputs=INPUTS, shots=SHOTS)
        lines_a, _ = dh.log_of(emu_a)
    finally:
        emu_a.close()
    snap_frames, _ = dh.tl.parse_log(Path(f"{state}.sd") / dh.LOG)
    v_save = snap_frames[-1]["v"]
    sys_b = wd_b / "sys"
    shutil.copytree(wd_a / "sys", sys_b, ignore=shutil.ignore_patterns("sdmc"))
    copied = sorted(str(p.relative_to(sys_b)) for p in sys_b.glob("*")) + sorted(
        str(p.relative_to(sys_b)) for p in (sys_b / "Azahar").glob("*"))
    start = time.monotonic()
    emu_b = Emulator(host_paths.app, wd_b, state=state)
    wait_b = _slots.waited_in(wd_b)
    t_state = time.monotonic() - start - wait_b
    try:
        assert (emu_b.sd / dh.LOG).read_bytes() == (Path(f"{state}.sd") / dh.LOG).read_bytes()
        assert emu_b.frame_total == info.frame_total
        result_b = emu_b.run(600, inputs=INPUTS, shots=SHOTS)
        lines_b, _ = dh.log_of(emu_b)
    finally:
        emu_b.close()
    load_line = next((x for x in (wd_b / "host.log").read_text().splitlines() if "state load" in x), "")
    ratio = t_state / t_boot
    fixed = (t_state - t_core_start) / (t_boot - t_core_start)
    report = (f"t_core_start={t_core_start:.2f} t_boot={t_boot:.2f} t_state={t_state:.2f} wait_a={wait_a:.2f} wait_b={wait_b:.2f} ratio={ratio:.3f} "
              f"fixed_ratio={fixed:.3f} k={info.k} frame_total={info.frame_total} v_save={v_save}\n{load_line}\n"
              f"copied into b/sys: {copied}\n")
    print(report, file=sys.stderr)
    out = Path(workdir.parent) / "state-times.txt"
    out.write_text(report)
    for frame in SHOTS:
        shot = result_b.shots[frame]
        assert "markers ok" in dh.markers_ok(shot.top, shot.bottom), frame
    expected = keyed(lines_a, v_save)
    got = keyed(lines_b, v_save, shift=1 if plant else 0)       # the planted red compares one v later
    window = {v: x for v, x in expected.items() if v <= v_save + 600}
    assert len(window) >= 590
    mismatches = [(v, x, got.get(v)) for v, x in window.items() if got.get(v) != x]
    assert not mismatches, f"{len(mismatches)} lines differ, first {mismatches[:2]}"
    assert result_a.frames == result_b.frames == 600 and frames_before
    assert t_state < 2.5, f"state boot {t_state:.2f} s, Guy's bound 2.5 s on the test app"


def quick_state(host_paths, workdir):
    state = workdir / "st" / "state"
    with Emulator(host_paths.app, workdir / "a") as emu:
        emu.run(100)
        emu.save_state(state)
    return state


def test_other_app(host_paths, workdir, monkeypatch):
    state = quick_state(host_paths, workdir)
    other = workdir / "other.3dsx"
    other.write_bytes(host_paths.app.read_bytes() + b"\x00")
    wd_c = workdir / "c"
    monkeypatch.delenv("LAZ_STATE_ANY_APP", raising=False)
    with pytest.raises(StateError, match="another app") as caught:
        Emulator(other, wd_c, state=state)
    assert str(host_paths.app) in str(caught.value)
    hostmap = _map.HostMap(wd_c / "host.map")
    assert hostmap.valid() and hostmap.frame_total() == 0
    hostmap.close()
    monkeypatch.setenv("LAZ_STATE_ANY_APP", "1")
    with Emulator(other, workdir / "d", state=state) as emu:
        assert emu.run(10).stopped_by == "frames"


def test_abi_outside_range_refused(host_paths, workdir):
    """A state whose meta names a state abi above this host's (AZH_STATE_META_ABI), or below 2, is refused."""
    state = quick_state(host_paths, workdir)
    meta = Path(f"{state}.meta")
    text = meta.read_bytes().decode()
    line = f"abi={_abi.AZH_STATE_META_ABI}\n"
    assert line in text
    for number, bad in enumerate((_abi.AZH_STATE_META_ABI + 1, 1)):
        meta.write_bytes(text.replace(line, f"abi={bad}\n", 1).encode())
        with pytest.raises(StateError, match="abi"):
            Emulator(host_paths.app, workdir / f"n{number}", state=state)
