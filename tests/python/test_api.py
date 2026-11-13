"""Emulator API details on a live instance: screens, keys, single frames, save and load on one instance."""
from __future__ import annotations

import numpy as np
import pytest

import d_helpers as dh
from libazahar import Buttons, HostError, Touch

pytestmark = pytest.mark.slow

FIELDS = ("v", "k", "tx", "ty", "td", "cx", "cy")


def test_screens_shapes_and_red_marker(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        emu.run(300)
        top, bottom = emu.screens()
        assert top.shape == (240, 400, 4) and top.dtype == np.uint8
        assert bottom.shape == (240, 320, 4) and bottom.dtype == np.uint8
        assert tuple(top[0, 0, :3]) == (255, 0, 0) and tuple(bottom[0, 0, :3]) == (255, 255, 0)
        assert not top.flags.writeable
        with pytest.raises(ValueError):
            top[0, 0, 0] = 1


def test_set_keys_and_run_frame(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        emu.run(300)
        emu.set_keys(raw=Buttons.A)
        emu.run(10)
        frames, _ = dh.log_of(emu)
        assert frames[-1]["k"] == 1
        emu.set_input(touch=Touch(10, 20))
        emu.set_input(buttons=0)
        before = emu.frame_total
        assert emu.run_frame().frames == 1 and emu.frame_total == before + 1


def test_closed_emulator_raises(host_paths, workdir):
    emu = dh.boot(host_paths, workdir)
    emu.close()
    emu.close()
    with pytest.raises(HostError):
        emu.run(1)


def test_save_and_load_on_one_instance(host_paths, workdir, seed):
    inputs = [(1, Buttons(0)), (1, Touch.up), (30, Buttons.A), (60, Touch(100, 100)), (90, Touch.up),
              (120, Buttons(0)), (150, Buttons.X | Buttons.L)]
    with dh.boot(host_paths, workdir, seed(boot_frames=300)) as emu:
        emu.run(600)
        info = emu.save_state(workdir / "st" / "state")
        assert info.k >= 0
        emu.run(300, inputs)
        first, _ = dh.log_of(emu)                      # read now: the load replaces the SD folder
        emu.load_state(info.path)
        assert emu.frame_total == info.frame_total
        emu.run(300, inputs)
        second, _ = dh.log_of(emu)
    snap_frames, _ = dh.tl.parse_log(workdir / "st" / "state.sd" / dh.LOG)
    v_save = snap_frames[-1]["v"]
    one = {row["v"]: tuple(row[k] for k in FIELDS[1:]) for row in first if row["v"] > v_save}
    two = {row["v"]: tuple(row[k] for k in FIELDS[1:]) for row in second if row["v"] > v_save}
    assert len(one) >= 290 and one == two


def test_fresh_sd_clears_the_card_and_keeps_sys(host_paths, workdir, seed):
    folder = seed(boot_frames=300)
    with dh.boot(host_paths, workdir, folder) as emu:
        emu.run(60)
        (emu.sd / "old_run.txt").write_text("from the run before")
    marker = workdir / "sys" / "keep_me.txt"
    marker.write_text("stands in for the shader cache")
    with dh.boot(host_paths, workdir, folder, fresh_sd=True) as emu:
        assert not (emu.sd / "old_run.txt").exists()
        assert marker.is_file()
        assert any(emu.sd.rglob("*")), "the seed is copied after the clear"
        emu.run(60)


def test_shot_names_and_frame_total(host_paths, workdir):
    with dh.boot(host_paths, workdir) as emu:
        emu.run(300)
        result = emu.run(20, shots=[5])
        shot = result.shots[5]
        assert shot.frame == 5 and shot.frame_total == 305 == result.first_frame + 4
        assert "shot_000305_top" in shot.top


def test_long_batch_outlives_a_short_timeout(host_paths, workdir):
    """``timeout`` is a no-progress limit: a batch far longer than it ends normally while frames keep coming."""
    with dh.boot(host_paths, workdir) as emu:
        emu.run(300)
        result = emu.run(8000, timeout=1.0)
        assert result.stopped_by == "frames" and result.frames == 8000
        if result.wall_s <= 1.0:
            pytest.skip(f"the batch took {result.wall_s:.2f} s, not longer than the timeout")
