"""Step L (item laz-520): the D24S8 stencil readback self-test of the test app, one fresh process per launch.

``testapp/source/stencil.c`` fills a 128 x 128 depth+stencil target (32-bit clear: depth fffffe, stencil 00), draws one
100 x 80 quad (depth 4001ff, stencil 0x80) and logs the counts of a GX TextureCopy readback on one ``stencil`` line.
Variant a is the first use of the target, b has a dummy draw before the fill, d is a second readback in the same process
as a. Every launch's counts go to runs/stencil/launches.txt. ``LAZ_STENCIL_RUNS`` sets the launches per variant (10)."""
from __future__ import annotations

import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List

import pytest

import testapp_log
from libazahar import Emulator

pytestmark = pytest.mark.slow

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "runs" / "stencil"
LAUNCHES = int(os.environ.get("LAZ_STENCIL_RUNS", "10"))
LINE = re.compile(r"^stencil v=(?P<v>\w) (?P<rest>n.*)$")
# the good result: 100 x 80 = 8000 pixels of the quad's stencil, the other 8384 of 16384 untouched, depth exact
GOOD = {"n80": 8000, "n00": 8384, "nff": 0, "nother": 0, "bbox": "10,20,109,99", "dq": 8000, "dbad": 0}
MODE_VARIANTS = {1: ("a", "d"), 2: ("b",)}      # control stencil=N -> the lines it logs
FRAME_STEP = 30
FRAME_LIMIT = 900


def parse_line(text: str) -> Dict[str, object]:
    """``n80=8000 n00=... bbox=10,20,109,99 ...`` to a dict (ints, bbox kept as text)."""
    out: Dict[str, object] = {}
    for token in text.split():
        key, _, value = token.partition("=")
        out[key] = value if key == "bbox" else int(value)
    return out


def launch(host_paths, workdir: Path, mode: int, index: int) -> Dict[str, Dict[str, object]]:
    """Boot the test app once with stencil=<mode>; return {variant: counts} from its log."""
    folder = workdir / f"m{mode}_{index}"
    if folder.exists():
        shutil.rmtree(folder)
    testapp_log.write_control(folder / "seed", stencil=mode)
    found: Dict[str, Dict[str, object]] = {}
    with Emulator(host_paths.app, folder / "work", sd_seed=folder / "seed", core=host_paths.core) as emu:
        for _ in range(FRAME_LIMIT // FRAME_STEP):
            emu.run(FRAME_STEP)
            log = emu.sd / "testapp" / "log.txt"
            text = log.read_text(errors="replace") if log.exists() else ""
            found = {}
            for row in text.splitlines():
                hit = LINE.match(row)
                if hit:
                    found[hit["v"]] = parse_line(hit["rest"])
            if len(found) == len(MODE_VARIANTS[mode]):
                break
    shutil.rmtree(folder, ignore_errors=True)
    return found


def test_stencil_readback_counts(host_paths, workdir):
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%F %T")
    rows: List[str] = []
    bad: List[str] = []
    for mode, variants in MODE_VARIANTS.items():
        for index in range(1, LAUNCHES + 1):
            found = launch(host_paths, workdir, mode, index)
            for variant in variants:
                counts = found.get(variant)
                row = f"{stamp} core={host_paths.core.name} mode={mode} launch={index} v={variant} " + (
                    " ".join(f"{k}={v}" for k, v in counts.items()) if counts else "MISSING")
                rows.append(row)
                if counts != GOOD:
                    bad.append(row)
    with open(OUT / "launches.txt", "a", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + "\n")
    print("\n".join(rows), file=sys.stderr)
    assert not bad, f"{len(bad)} of {len(rows)} readbacks differ from {GOOD}:\n" + "\n".join(bad)
