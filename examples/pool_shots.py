"""Run three test-app instances through a Pool, one shot each. Run from the repo root: python examples/pool_shots.py"""
import re
import shutil
import sys
from pathlib import Path

from libazahar import Pool

APP = "build/testapp.3dsx"
ROOT = Path("runs/pool_shots").resolve()
SEEDS = {"2d": "draw=2d", "3d": "draw=3d", "2d-ready": "draw=2d\nready_at=5"}      # the test app's control.txt keys


def job(emu, name):
    """Run 120 frames, shoot the last one, and report the mode the app logged."""
    result = emu.run(120, shots=[120])
    start = (emu.sd / "testapp/log.txt").read_text().splitlines()[0]
    return name, result.shots[120], emu.workdir, re.search(r"mode=(\w+)", start).group(1)


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    with Pool(3, APP, ROOT / "jobs") as pool:
        futures = []
        for name, text in SEEDS.items():
            seed = ROOT / "seeds" / name
            (seed / "testapp").mkdir(parents=True)
            (seed / "testapp/control.txt").write_text(text + "\n")
            futures.append(pool.submit(job, name, sd_seed=seed))
        done = [future.result() for future in futures]
    if len({str(d[2]) for d in done}) != 3 or len({d[1].top for d in done}) != 3:
        sys.exit("pool_shots failed: the jobs share a folder or a shot")
    for name, shot, workdir, mode in done:
        if mode != name[:2] or not (shot.top.is_file() and shot.bottom.is_file()):
            sys.exit(f"pool_shots failed: job {name} logged mode {mode} or has no shot in {workdir}")
    print("pool_shots ok")


main()
