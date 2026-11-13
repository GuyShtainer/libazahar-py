"""Step M (item laz-660): a state restore followed by programmable-shader draws (the test app's 3D mode).

Loading a state re-inits the core, so the Vulkan renderer is new and has no shader cache selected; a .3dsx has
program id 0, which equals the renderer's default id, and the upstream cache switch returned early. The first
3D draw after the restore then read through a null cache pointer (signal 11). Core patch 0011 fixes the switch.
The 2D state tests miss it: the test app's 2D mode draws no programmable-shader frame."""
from __future__ import annotations

import pytest

from libazahar import Emulator

pytestmark = pytest.mark.slow


@pytest.mark.parametrize("trial", range(2))
def test_state_restore_then_3d_draws(host_paths, workdir, seed, trial):
    state = workdir / "st" / "state"
    with Emulator(host_paths.app, workdir / "a", sd_seed=seed(draw="3d")) as emu:
        emu.run(300)
        emu.save_state(state)
    with Emulator(host_paths.app, workdir / "b", state=state) as emu:
        result = emu.run(300)
    assert result.frames == 300
