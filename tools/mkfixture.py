#!/usr/bin/env python3
"""Make a release's state fixture: a test-app state every later 1.x release must load (docs/plans/phase-v1.md
section 1, "States"; checked by tests/python/test_release_fixture.py).

    nice -n 10 python3 -I tools/mkfixture.py <tag>        # writes runs/release-fixtures/<tag>/ (outside git)

The folder holds the state (plus its .sd/ and .meta), a copy of the test app it was made with, and fixture.json
(the tag, the core's version and sha256, the app's sha256, frame_total and the test app's last log line). It refuses
to overwrite an existing fixture.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _folder in (REPO / "python", REPO / "tests"):
    sys.path.insert(0, str(_folder))
import testapp_log  # noqa: E402
from libazahar import Emulator, _paths  # noqa: E402

LOG = "testapp/log.txt"
FRAMES = 600


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv):
    if len(argv) != 1:
        sys.exit("usage: mkfixture.py <tag>   (for example v1.0.0)")
    out = REPO / "runs" / "release-fixtures" / argv[0]
    if out.exists():
        sys.exit(f"mkfixture: {out} exists; a fixture is made once per release")
    work = REPO / "runs" / "mkfixture-work"
    if work.exists():
        shutil.rmtree(work)
    app, core = REPO / "build" / "testapp.3dsx", _paths.core_path()
    seed = work / "seed"
    testapp_log.write_control(seed, draw="3d")     # the 3D draw also covers a restore's first 3D frame (laz-660)
    out.mkdir(parents=True)
    shutil.copy2(app, out / "testapp.3dsx")
    with Emulator(out / "testapp.3dsx", work / "a", sd_seed=seed) as emu:
        emu.run(FRAMES)
        info = emu.save_state(out / "state")
        version = emu.stats().core_version
    frames = testapp_log.parse_log(Path(f"{out / 'state'}.sd") / LOG)[0]
    record = {"tag": argv[0], "core_version": version, "core_sha256": sha(core), "app_sha256": sha(app),
              "frame_total": info.frame_total, "k": info.k, "last_v": frames[-1]["v"]}
    (out / "fixture.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps(record))


if __name__ == "__main__":
    main(sys.argv[1:])
