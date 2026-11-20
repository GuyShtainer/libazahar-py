# libazahar-py status

As of 2026-11-20. v1.2.0. The items new in 1.2.0 ran on the Windows PC; for macOS see
"macOS in v1.2.0" below. Each item below names the work item (`laz-NNN`) whose
Evidence, in `docs/status/lazpy/5-done/`, proves it. Nothing is listed as working that no gate ran.

## What works

- The host library `libazhost.dylib` and the `azhost` command boot a 3DS homebrew app on Azahar's libretro core with no
  window, run batches of frames, save PNG shots of both screens and report stats (laz-120)
- The test app (`build/testapp.3dsx`, ours) draws exact corner markers in 2D and 3D and logs one line per frame; its
  markers and four events are checked (laz-130)
- Input and stops: buttons, touch and circle pad as a per-frame movie; stops on SD-file text, a guest break, a guest
  exit, a guest error and a wall-clock limit (laz-210)
- The Python layer (`Emulator`, `run`, `run_until`, `screens`, `shot`, the error classes) and savestates, with an SD
  snapshot, gated on Azahar's own core; our core's gate below repeats the state checks (laz-220)
- Our patched core builds from Azahar's pinned source (the gated route is `core/PIN-nokeys`) with our patch files
  and a build script; the build itself is gated in laz-320 (laz-110)
- Our core's gate: built without Azahar's built-in key data and default HTTP client certificate, loading no keys; the
  debug-text stop; exact repeats; states restored into equal instances; states moving between the two cores
  (laz-320)
- Many instances at once: `Pool`, the machine-wide slot cap, `LoadWarning`, the speed table, a default cap of 4
  (the number from a real 3D scene, docs/research/real-scene-v3.md) (laz-310)
- Guest memory on our core: `emu.memory` reads and writes and the per-frame watch list (laz-330)
- A real app on our core: Gen3D's 3D scene (36000 frames, one batch) runs as fast as on Azahar's own core on a quiet
  machine, and its code reads back through `emu.memory`; bad arguments raise `ArgumentError`, `fresh_sd` and
  `Shot.frame_total` exist (laz-430)
- Core lazpy.2: `threads()` lists the guest threads, and `citra_init_ticks_override` seeds the guest's clock; states
  move between lazpy.1 and lazpy.2 both ways (laz-510)
- The 1.0 API freeze: keyword-only run options, `Path` returns, one strict option-profile format read the same way
  by the host and Python, the input-script bounds and the `azhost` exit codes, each with tests (laz-610)
- Depth-stencil readback on MoltenVK: exact on our test app's check (0 bad of 90 on core 88cc6188, the build before
  patch 0011; the release core 64026f4a passes the same test in the full pass) and on a user's own self-test (laz-520)
- Restoring a saved state, then drawing 3D: an Azahar bug crashed the first 3D draw after a state load; our core
  fixes it (patch 0011), with a test-app test, and both user projects pass on it (laz-660)
- New in 1.2.0: the release check prints SKIP or PEND, not PASS, for a check that could not run (laz-821)
- New in 1.2.0: what repeats run to run is written down (`docs/USING.md` section 10a) and tested, with `images.digest` (laz-822)
- New in 1.2.0: errors carry `.workdir` and `.log_path`, and name the log and the newest screenshot (laz-823)
- New in 1.2.0: `images.compare` with pixel limits, the pass/fail example `examples/verdict.py`, and one exit-code table (USING
  section 3) (laz-824)
- New in 1.2.0: the same button pressed twice registers twice when released for one frame between (laz-825)
- New in 1.2.0: a worker ends when the script that started it dies: a kill-on-close Job object on Windows, a kqueue watch on macOS
  (laz-826)
- New in 1.2.0: no window opens on Windows: a window watch during a full run (laz-827)
- New in 1.2.0: `Pool` with two live copies (laz-828)
- New in 1.2.0: a command line: `python -m libazahar doctor` and `python -m libazahar run` (USING section 2a) (laz-831)
- New in 1.2.0: audio capture: `run(..., audio=True)` gives the batch's samples as int16 stereo and the rate (USING section 12b),
  checked on Windows on a two-channel tone app of ours; not yet tested on macOS (laz-832)
- New in 1.2.0: the guest clock no longer depends on the host's time zone: the worker runs in UTC, so on our core one tick
  seed gives one clock on every machine (USING section 10a) (laz-834)
- New in 1.2.0: a rebuilt Windows core with OpenSSL's folders at their Windows defaults (`C:/Program Files/...`)
  instead of paths inside the build's own prefix; the same source and patches as v1.1.0's (laz-835)

## What does not work yet

- macOS before 15, Intel Macs and Linux. The core needs macOS 15 (see Known limits).
- Windows 11 and AMD and Intel GPUs: untested (see Windows below).
- Poll-exact movies: our core exports `lazpy_movie_play`, but its playback loses step once an app starts the ZL/ZR
  service, so the host and Python do not call it. It needs a core patch first (laz-833).
- Audio playback: nothing plays sound; audio is captured only (USING section 12b).
- Guest memory and the watch list on Azahar's own core: they raise `NeedsLazpyCore`.
- Any app that is not homebrew: no console keys, no Nintendo system files, no encrypted titles.

## Windows (proven on one PC)

The native Windows build (core, host library and Python layer, no WSL) is proven on one PC only: Windows 10 Pro 22H2,
x64, an NVIDIA GeForce RTX 3060, driver 610.88, Python 3.10.11. There, a fresh clone built from the README's Windows steps
passes the host C tests and the full pytest with the emulator required; its only skips are the by-design ones (no
lazpy.1 Windows core, no `LoadWarning`, no nice values, the symlink test while Developer Mode is off, the thread test that needs
`build/testapp.elf`, which the release test app does not ship, and since v1.2.0 the two audio tests, which need the tone
test app that no release ships). For v1.2.0 the two 3-copy `Pool` tests were left out there (that PC runs at most two
copies); they passed in the macOS CI emulator suite.
- CI adds Windows Server 2025 for the build, the fast tests and the core load test.
- Windows 11 and AMD and Intel GPUs are untested.
- A GPU driver with Vulkan is required; nothing Vulkan is shipped.
- No Windows speed figures. The instance cap stays 4.
- Differences from macOS are in `docs/USING.md` section 15a.

## macOS in v1.2.0

macOS uses the same core as v1.0.0 and v1.1.0. The v1.2.0 changes were built and tested on the Windows PC. On macOS
they ran in the hosted CI jobs on the release candidate (commit 2f959c0): the fast tests passed on Python 3.10 and
3.14 (354 passed, 9 skipped each, `test.yml` run 44741219449), and the emulator suite (`macos-live.yml` run
44741224096) had 429 passed, 25 skipped and 1 failed in both attempts, `test_state_boot` (3.3 and 3.4 s against its
2.5 s bound on that shared runner, as at v1.1.0). The kqueue parent watch and the `lsof` slot lookup passed there. Its skips are Windows-only tests, the comparisons with Azahar's own core (not given to that job), four inputs that
job lacks (a release fixture, the test app's ELF, two older cores), and the two audio tests: CI has no tone test app
(no release ships it), so audio capture is not yet tested on macOS.

## macOS in v1.1.0

macOS uses the same core as v1.0.0. The emulator suite last passed in full on a Mac at v1.0.0. The v1.1.0 release
candidate ran on hosted macOS CI runners: the fast tests passed, and the emulator suite (`macos-live.yml`) had 292
passed, 14 skipped and 1 failed, `test_state_boot` (5.3 s against its 2.5 s bound on that shared runner). Earlier v1.1.0
runs there also failed `test_k_threads`, which now skips on macOS as on Windows, since the release test app ships no
ELF. The v1.1.0 changes that reach macOS are small: the host also accepts a stock core that names itself `219d743` (and
names it when it refuses a core), the version is 1.1.0, `tools/fetch.sh` has the v1.1.0 pins, and three tests changed (a
skip when there is no test-app ELF, a longer boot wait, and the cross-system state check).

## Known limits

- Runs on Azahar's own core do not repeat exactly; exact repeats are gated on our core only.
- Touch rows 63, 125, 126 and 127 reach the guest one pixel off (HID truncates a float, as in Azahar's Qt build);
  `docs/USING.md` section 5 has the table.
- An ABI-3 host loads ABI-2 and ABI-3 states; an older host refuses newer states, and a state may not load across core
  versions.
- The Windows core of v1.2.0 is a new build (the OpenSSL folder fix): a state made with the v1.1.0 Windows core may
  not load with it; make new states. The macOS core is unchanged since v1.0.0.
- A multi-field record read from guest memory can be torn (some fields from the frame before); the watch list too.
- One `azh_open` per process: the Python layer runs each Emulator in its own worker process.
- The slot cap counts only libazahar's own workers, not other emulators on the machine.
- On macOS, the core, `libazhost.dylib` and `azhost` need macOS 15 or later (the core's OpenSSL is built for 15).
- The guest's HTTPS finds a CA file only at OpenSSL's compiled-in paths: Homebrew's `openssl@3` on macOS. On Windows the
  compiled-in OPENSSLDIR is `C:/Program Files/Common Files/SSL` (since v1.2.0) and nothing is installed there, so it
  finds none unless one is put at `cert.pem` in that folder (not tested). Homebrew tests do not need it.
- On Windows each state load leaves about two Semaphore handles open in the core (laz-829); a long run of loads in one
  instance grows its handle count. A test tracks it; the fix needs a core patch.
- `python -m libazahar doctor` shows `pid unknown` for held slots on Windows.
- `azhost` has no `--help`; an unknown first argument prints the usage and exits with 2.
- The promise (semantic versioning from 1.0.0): until 2.0, the Python API, the C functions in `host/azhost.h`, the
  `azhost` command line and exit codes, and the input-script and option-profile formats change only in compatible ways.
  `docs/USING.md` lists them.

## Considered and dropped

- A fuller `SET_MEMORY_MAPS` table: Azahar's core builds it once, so we did not patch it; guest memory comes from our
  core's own read and write calls.
- Savestate parsing as a way to read memory: dropped for the same reason.
- An upstream pull request: Guy decided "no need to submit a pull request, we edit the core to our needs". Any
  upstream patch would first have to follow Azahar's `AI-POLICY.md`.
- Building OpenSSL ourselves so the core runs on macOS 11-14: it needs a core rebuild and a new gate; the release says
  macOS 15 or later instead.
- A scripted download of Azahar's own core: removed before the first release. Our core is the default, and comparisons take
  `LAZ_STOCK_CORE`, a file you download yourself.
- Out of scope (PLAN section 5), one line each:
  - Linux: macOS arm64 first, then Windows (done in 1.1.0, above).
  - Audio playback: not built (capture is, USING section 12b).
  - Any window: the tool is headless.
  - Patching HID's touch truncation: four rows move by one pixel; documented.
  - Azahar's RPC server and gdb stub: not in libretro builds.
  - Commercial 3DS titles: not supported; the tests in this repository use our own test app. The real-scene speed rows are a
    user's homebrew (Gen3D) running a GBA game supplied locally, not distributed.
  - `.cia` installs: the host loads `.3dsx`.
  - Wireless, motion and camera: not built.
  - PyPI: the route is a clone and an editable install.
  - HOME: not offered.
  - Gen3D's adapter: Gen3D's own work.

## Next

- CI on GitHub runners: `.github/workflows/test-windows.yml` (Windows, every push) and `test.yml` (macOS, started by
  hand).
- Gen3D's adapter (Gen3D's own work).
