"""Every release's state fixture loads and runs on this host (docs/plans/phase-v1.md section 1, "States").

A fixture is made once per release by tools/mkfixture.py under runs/release-fixtures/<tag>/ (outside git). With no
fixture folder the test skips; V7 of each 1.x release makes the folder before it runs the full pass.

A state does not carry across operating systems: Azahar's boost archives refuse a state whose `long` size differs
(8 bytes on macOS, 4 on Windows), the documented limit in docs/USING.md section 15a. A fixture made on the other
system must be refused with exactly that error. fixture.json names its system ("platform", sys.platform); fixtures
older than the key are macOS (1.0 shipped macOS only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from libazahar import Emulator, StateError

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2] / "runs" / "release-fixtures"
FIXTURES = sorted(p for p in ROOT.glob("*") if (p / "fixture.json").is_file()) if ROOT.is_dir() else []
LOG = "testapp/log.txt"


@pytest.mark.skipif(not FIXTURES, reason="no release fixture under runs/release-fixtures/ (tools/mkfixture.py)")
@pytest.mark.parametrize("folder", FIXTURES, ids=[p.name for p in FIXTURES])
def test_release_fixture_loads(folder, workdir):
    import testapp_log
    record = json.loads((folder / "fixture.json").read_text())
    if record.get("platform", "darwin") != sys.platform:
        with pytest.raises(StateError, match="size of long"):
            with Emulator(folder / "testapp.3dsx", workdir / "b", state=folder / "state"):
                pass
        return
    with Emulator(folder / "testapp.3dsx", workdir / "b", state=folder / "state") as emu:
        assert emu.frame_total == record["frame_total"]
        result = emu.run(300)
        frames = testapp_log.parse_log(emu.sd / LOG)[0]
    assert result.frames == 300
    assert frames[-1]["v"] > record["last_v"]
