# Commands

Checks (before every commit):
```
python3 -I tools/mkmap.py && python3 -I tools/mkprogress.py && python3 -I tools/status_check.py --strict-handoff && python3 -I tools/map_check.py
```

Build and gate the host and the test app (devkitARM first in PATH for the 3DS build):
```
make check && make && make test-version          # build/libazhost.dylib, build/azhost, the version test
PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp   # build/testapp.3dsx
tests/gate-a.sh build/testapp.3dsx               # step A's gate
RUNNER=azhost tests/gate-b.sh                    # step B's gate through azhost (default runner fe2 needs LAZ_STOCK_CORE)
build/azhost run <app.3dsx> --sys runs/x/sys --out runs/x/out --frames 600 --shot 300,600
make test-host                                   # pure host modules, seconds: "test-host: 307743 checks, 0 failed"
build/azhost layout                              # the ABI table, also checked by the check target
```

Step C's gate, a few minutes, needs our core and build/testapp.3dsx; run it in the background and wait on the rc file
(delete runs/c-gate.rc first; `--only a1,b,...` picks scenarios, `--plant-red` must fail a1/a2):
```
rm -f runs/c-gate.rc; PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH nice -n 10 python3 -I tests/gate_c.py > runs/c-gate.log 2>&1
```
Expect "gate_c: 28 passed, 0 failed". azhost's per-batch summary field is `wall_ms_mean`. A guest exit or guest
error ends azhost with exit code 10 or 11; a break stop continues the run.
`--core <dylib>` runs it on another core (our core: `build-core/azahar_lazpy_libretro.dylib`).

Step F2's gate, our patched core against the stock one, a few minutes; wait until the 1-min load is under 10 for its
r2 timing (`--only keyblob,symbols` needs no emulator; `keyblob_findings()` is the release check's import):
```
nice -n 10 python3 -I tests/gate_f2.py --ours build-core/azahar_lazpy_libretro.dylib --stock "$LAZ_STOCK_CORE" > runs/f2-gate.log 2>&1
```
Expect no FAIL lines; RECORD lines carry sizes, hashes and timings.

Step G's guest-memory gate (both cores; one Emulator at a time, never under `tools/hold_slot.py`):
```
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py
```
Expect "6 passed", 0 skipped.

A release's state fixture (once per release, at V7; outside git), then the check every later 1.x release runs:
```
nice -n 10 python3 -I tools/mkfixture.py v1.0.0       # runs/release-fixtures/v1.0.0/: state, test app, fixture.json
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_release_fixture.py
```

The Python package and step D's tests (the slow ones run one Emulator at a time):
```
python3 -m venv .venv && .venv/bin/pip install -e .          # the Python package (editable install only)
nice -n 10 python3 -m pytest -q -m "not slow" tests/python  # fast tests, no emulator: "49 passed"
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python   # step D's gate, about 70 s: "69 passed", 0 skipped
LAZ_CORE=build-core/azahar_lazpy_libretro.dylib LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q tests/python/test_c_checks.py   # C's checks on our core: "10 passed"
LAZ_TEST_PLANT_RED=1 LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q tests/python/test_state.py -k test_state_boot   # must FAIL: "lines differ"
build/azhost run <app.3dsx> --frames N --save runs/x.state   # a state from the command line (--state boots one; not gated in D)
```
`LAZ_REQUIRE_EMULATOR=1` turns a missing host, core or app into a failure; `LAZ_CORE` picks the core (the header
line prints its kind); the debug-text check c4 uses the stock core and skips unless `LAZ_STOCK_CORE` names one. In a worktree, link MAIN's
build-core/azahar_lazpy_libretro.dylib into its own build-core/ first; never run tools/build-core.sh there.

Our patched core (detached, nice'd; `--configure-only` stops after the patches and configure):
```
nice -n 10 tools/build-core.sh --detach         # build-core/azahar_lazpy_libretro.dylib, build-core/build.exit
```

Build the spike's prototype (from the repo root; headers in `vendor/`, ignored):
```
mkdir -p build && cc -O2 -I vendor -I vendor/include -o build/fe2 prototype/fe2.c -framework OpenGL -lz
```

Fetch first: `tools/fetch.sh` (MoltenVK and headers; sha256-checked); the prototype runs Azahar's own core, `$LAZ_STOCK_CORE`. Run it (any core option as `OPT_<key>=value`):
```
MVK_LIB=dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib OPT_citra_graphics_api=Vulkan \
  build/fe2 "$LAZ_STOCK_CORE" <app.3dsx> <sysdir> <outdir> <seconds> <shot frames, comma list>
```
The core's SD folder is `<sysdir>/Azahar/sdmc/`. Azahar's own core (`LAZ_STOCK_CORE`, opt-in) is not downloaded by any script; spike 1 names where it came from: `docs/research/spike-1-headless-core.md`.

Step H's docs gate and the examples (each example with `nice -n 10`; `LAZ_CORE` picks a core):
```
python3 -I tools/docs_check.py                    # README numbers, the example and steps blocks, links, claims (step H's gate)
.venv/bin/python examples/quickstart.py           # prints "quickstart ok"
sh tools/clone_check.sh --repo "$PWD" --branch main --out runs/clone --release-base "file://$PWD/runs/release/v1.0.0"   # the fresh clone (I2)
```

Step I's release tools (the README route fetches our core and the test app; `LAZ_STOCK_CORE` adds the core-comparison tests):
```
tools/fetch.sh --moltenvk --headers --lazpy-core --testapp   # our core (default path dl/lazpy-core/) and the test app
tools/mkrelease.sh v1.0.0                                    # stage the release in runs/release/v1.0.0/ (about 100 s)
python3 -I tools/release_check.py runs/release/v1.0.0        # the release checks (--skip-pins before I2, --pre-push before a push, --plant-red)
python3 -I tools/mknotices.py --link <link.txt> --deps build-core/build --tree <build-src tree> --src <unpacked tree> --inputs build-core/build.inputs --openssl dl/openssl-src/openssl-3.6.5.tar.gz --sysarch dl/sysarch-src/citra_system_archives-f470e0c.tar.gz --ofl dl/font-licences/Montserrat-v4.001-OFL.txt --unifont dl/font-licences/unifont-10.0.05-notice.txt --newlib dl/newlib-licence/COPYING.NEWLIB-4.6.0 > NOTICES.md
LAZ_STOCK_CORE=<Azahar's own core> .venv/bin/python -m pytest -q tests/python   # adds the core-comparison tests; unset, they skip
```
