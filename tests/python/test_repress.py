"""B4 (docs/plans/phase-8.md): a release held for a short gap, then a second press, reaches the guest as two presses.

Covers A (the HID path), ZL and ZR (the irrst service) and a touch release and re-tap. The test app logs the held
mask ``k`` and the touch flag ``td`` every frame; a press is a rising edge in those columns.

Run: LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python/test_repress.py
"""
from __future__ import annotations

import sys
from typing import Callable, List

import pytest

import d_helpers as dh
from libazahar import Buttons, Emulator, Touch

pytestmark = pytest.mark.slow

FIRST_PRESS = 20
HOLD = 6
TOTAL = 90
GAPS = (1, 2, 3)          # frames between the release and the second press
ZL, ZR = int(Buttons.ZL), int(Buttons.ZR)


def edges(values: List[int]) -> int:
    """The number of rising edges (0 to nonzero) in a sequence."""
    return sum(1 for before, after in zip([0, *values], values) if after and not before)


def key_presses(frames: List[dict], mask: int) -> int:
    """Rising edges of ``mask`` in the held keys of the log's frame lines."""
    return edges([row["k"] & mask for row in frames])


def run_movie(emu: Emulator, items: list) -> List[dict]:
    emu.run(TOTAL, inputs=items)
    frames, _ = dh.log_of(emu)
    assert frames, "the test app wrote no frame lines"
    return frames


@pytest.fixture
def boot(host_paths, workdir, seed) -> Callable[[], Emulator]:
    return lambda: dh.boot(host_paths, workdir, seed(ready_at=0))


@pytest.mark.parametrize("gap", GAPS)
@pytest.mark.parametrize("button", [Buttons.A, Buttons.ZL, Buttons.ZR], ids=["A", "ZL", "ZR"])
def test_button_repress(boot, button, gap):
    """Press, release, press again after ``gap`` empty frames: the log shows two presses of that button."""
    release = FIRST_PRESS + HOLD
    items = [(FIRST_PRESS, button), (release, Buttons(0)), (release + gap, button), (release + gap + HOLD, Buttons(0))]
    with boot() as emu:
        frames = run_movie(emu, items)
    count = key_presses(frames, int(button))
    print(f"repress {button.name} gap {gap}: {count} presses", file=sys.stderr)
    assert count == 2


@pytest.mark.parametrize("gap", GAPS)
def test_touch_retap(boot, gap):
    """Touch, lift, touch again after ``gap`` frames: the log shows two touches."""
    lift = FIRST_PRESS + HOLD
    items = [(FIRST_PRESS, Touch(100, 100)), (lift, Touch.up), (lift + gap, Touch(100, 100)),
             (lift + gap + HOLD, Touch.up)]
    with boot() as emu:
        frames = run_movie(emu, items)
    count = edges([1 if row["td"] else 0 for row in frames])
    print(f"retap touch gap {gap}: {count} touches", file=sys.stderr)
    assert count == 2
