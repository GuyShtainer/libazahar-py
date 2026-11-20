"""What repeats (docs/USING.md section 10a): same seed, inputs and fresh workdirs give the same run."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pytest

import d_helpers as dh
from libazahar import Buttons, Emulator, images
from test_threads_live import needs_rev2

pytestmark = pytest.mark.slow

INPUTS = [(40, Buttons.A), (90, Buttons(0)), (150, Buttons.X | Buttons.L), (200, Buttons(0))]
SAME = ("v", "s", "k", "t", "tx", "ty", "td", "cx", "cy")   # every record field; t is the app's osGetTime reading
CHECKPOINTS = (300, 600)
MS_1900_TO_2000 = 3155673600000   # 100 years in ms, the offset of osGetTime's epoch


def record_rows(emu: Emulator) -> List[tuple]:
    """The log's frame rows as tuples of the fields that must repeat."""
    frames, _ = dh.log_of(emu)
    return [tuple(row[key] for key in SAME) for row in frames]


def field_index(name: str) -> int:
    return SAME.index(name)


def one_run(paths, core, folder: Path, ticks: str) -> Tuple[Dict[int, str], Dict[int, tuple], List[tuple]]:
    """Boot fresh in ``folder``, run to frame 300 and 600: (digest at each, last record row at each, all rows)."""
    digests: Dict[int, str] = {}
    last: Dict[int, tuple] = {}
    with dh.boot(paths, folder, core=core, options={"citra_init_ticks_override": ticks}) as emu:
        done = 0
        for stop in CHECKPOINTS:
            emu.run(stop - done, inputs=INPUTS if done == 0 else ())
            done = stop
            digests[stop] = images.digest(emu.screens())
            last[stop] = record_rows(emu)[-1]
        return digests, last, record_rows(emu)


def test_same_inputs_same_run(host_paths, lazpy_core, workdir):
    needs_rev2(lazpy_core)
    first = one_run(host_paths, lazpy_core, workdir / "one", "0")
    second = one_run(host_paths, lazpy_core, workdir / "two", "0")
    assert first[0] == second[0], "screen digests differ between two fresh runs"
    assert first[1] == second[1], "the record differs at frame 300 or 600"
    assert first[2] == second[2], "the whole log differs"
    assert len(set(first[0].values())) == 2, "the screen should change between frames 300 and 600"
    assert first[1][300][1] == second[1][300][1]            # the tick field (s) itself
    assert first[1][300][field_index("t")] == second[1][300][field_index("t")]      # and the clock reading (t)


def test_two_tick_seeds_differ(host_paths, lazpy_core, workdir):
    needs_rev2(lazpy_core)
    zero = one_run(host_paths, lazpy_core, workdir / "zero", "0")
    big = one_run(host_paths, lazpy_core, workdir / "big", "1000000")
    for stop in CHECKPOINTS:
        assert zero[1][stop][1] != big[1][stop][1], f"tick field s is equal at frame {stop}"
    assert big[1][300][1] - zero[1][300][1] == 1000000
    t = field_index("t")
    shift = big[1][300][t] - zero[1][300][t]
    assert 3 <= shift <= 4, f"1000000 ticks should move the clock by about 3.7 ms, t moved by {shift}"
    for stop in CHECKPOINTS:
        assert big[1][stop][t] - zero[1][stop][t] == shift, f"the clock shift is not steady at frame {stop}"
    again = one_run(host_paths, lazpy_core, workdir / "again", "1000000")
    assert again[1] == big[1] and again[0] == big[0]


def test_host_time_zone_does_not_reach_the_guest(host_paths, lazpy_core, workdir, monkeypatch):
    """The core measures its start time against 2000-01-01 in local time; the worker runs in UTC (USING 10a)."""
    needs_rev2(lazpy_core)
    runs = {}
    for zone in ("GMT0", "EST5EDT", "IST-2"):
        monkeypatch.setenv("TZ", zone)
        runs[zone] = one_run(host_paths, lazpy_core, workdir / zone.replace("-", "m"), "1000000")
    assert runs["GMT0"] == runs["EST5EDT"] == runs["IST-2"], "the host's time zone reached the guest"
    seconds = (runs["GMT0"][1][300][field_index("t")] - MS_1900_TO_2000) // 1000    # osGetTime counts from 1900
    assert 3677 <= seconds <= 3707, f"the guest clock should start at 2000-01-01 01:01:17, it reads {seconds} s past 2000"
    zero = one_run(host_paths, lazpy_core, workdir / "zero", "0")        # still under IST-2
    t = field_index("t")
    shift = runs["GMT0"][1][300][t] - zero[1][300][t]
    assert 3 <= shift <= 4, f"under a UTC parent the seed should still move the clock, t moved by {shift}"


def last_keys(emu: Emulator) -> int:
    frames, _ = dh.log_of(emu)
    return frames[-1]["k"]


def test_held_input_across_load_state(host_paths, workdir):
    """Save with nothing held, press A, load: A must stay down (kept, not restored from the state)."""
    state = workdir / "st" / "state"
    a_down = int(Buttons.A)
    with dh.boot(host_paths, workdir / "a") as emu:
        emu.run(100)
        assert not last_keys(emu) & a_down
        emu.save_state(state)
        emu.set_input(buttons=Buttons.A)
        emu.run(20)
        assert last_keys(emu) & a_down
        emu.load_state(state)
        emu.run(20)
        assert last_keys(emu) & a_down, "A should still be held after load_state"
        emu.set_input(buttons=Buttons(0))
        emu.run(10)
        assert not last_keys(emu) & a_down
    with Emulator(host_paths.app, workdir / "b", state=state) as emu:
        emu.run(20)
        assert not last_keys(emu) & a_down, "a booted state starts with nothing held"
