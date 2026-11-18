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
SAME = ("v", "s", "k", "tx", "ty", "td", "cx", "cy")        # every record field but t, the app's own clock reading
CHECKPOINTS = (300, 600)


def record_rows(emu: Emulator) -> List[tuple]:
    """The log's frame rows as tuples of the fields that must repeat."""
    frames, _ = dh.log_of(emu)
    return [tuple(row[key] for key in SAME) for row in frames]


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


def test_two_tick_seeds_differ(host_paths, lazpy_core, workdir):
    needs_rev2(lazpy_core)
    zero = one_run(host_paths, lazpy_core, workdir / "zero", "0")
    big = one_run(host_paths, lazpy_core, workdir / "big", "1000000")
    for stop in CHECKPOINTS:
        assert zero[1][stop][1] != big[1][stop][1], f"tick field s is equal at frame {stop}"
    assert big[1][300][1] - zero[1][300][1] == 1000000
    again = one_run(host_paths, lazpy_core, workdir / "again", "1000000")
    assert again[1] == big[1] and again[0] == big[0]


def last_keys(emu: Emulator) -> int:
    frames, _ = dh.log_of(emu)
    return frames[-1]["k"]


def test_held_input_across_load_state(host_paths, workdir):
    state = workdir / "st" / "state"
    with dh.boot(host_paths, workdir / "a") as emu:
        emu.run(100, inputs=[(10, Buttons.A)])
        assert last_keys(emu) & 1
        emu.save_state(state)
        emu.run(20)                                          # A stays down across batches
        assert last_keys(emu) & 1
        emu.load_state(state)
        emu.run(20)
        assert last_keys(emu) & 1, "A should still be held after load_state"
        emu.set_input(buttons=Buttons(0))
        emu.run(10)
        assert not last_keys(emu) & 1
    with Emulator(host_paths.app, workdir / "b", state=state) as emu:
        emu.run(20)
        assert not last_keys(emu) & 1, "a booted state starts with nothing held"
