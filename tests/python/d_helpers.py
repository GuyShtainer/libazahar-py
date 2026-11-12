"""Shared helpers of the integration tests: boot with a seed, read the test app's log, batch offsets."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import checks_c as cc
import testapp_log as tl
from libazahar import Emulator, RunResult

REPO = Path(__file__).resolve().parents[2]
LOG = "testapp/log.txt"


def boot(paths, workdir: Path, seed_dir: Optional[Path] = None, **kwargs) -> Emulator:
    """An Emulator on the test app in ``workdir``."""
    return Emulator(paths.app, workdir, sd_seed=seed_dir, **kwargs)


def log_of(emu: Emulator) -> Tuple[list, list]:
    """(frame lines, event lines) of the test app's log in the emulator's SD folder."""
    path = emu.sd / LOG
    return tl.parse_log(path) if path.exists() else ([], [])


def run_batches(emu: Emulator, sizes: Iterable[int], first_inputs=(), first_shots=(), **first_kwargs) -> Tuple[
        List[RunResult], List[int], int]:
    """Run batches of the given sizes (inputs and shots only in the first); returns (results, c per batch, c_min).
    c = the batch's last absolute frame minus the v of the log's last frame line after it (phase-c.md)."""
    results: List[RunResult] = []
    summaries, last_lines = [], {}
    for index, size in enumerate(sizes, start=1):
        if index == 1:
            result = emu.run(size, first_inputs, first_shots, **first_kwargs)
        else:
            result = emu.run(size)
        results.append(result)
        frames, _ = log_of(emu)
        summaries.append({"last": result.last_frame})
        if frames:
            last_lines[index] = frames[-1]
    offsets = cc.boot_offsets(summaries, last_lines)
    return results, offsets, (min(offsets) if offsets else 0)


def markers_ok(top: str, bottom: str) -> str:
    """Run check_testapp's marker check on two PNGs; returns its output line."""
    done = subprocess.run([sys.executable, "-I", str(REPO / "tests" / "check_testapp.py"), "markers", "--top", top,
                           "--bottom", bottom, "--mode", "2d"], capture_output=True, text=True, check=False)
    return done.stdout.strip() + done.stderr.strip()
