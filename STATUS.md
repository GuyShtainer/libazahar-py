# libazahar-py status

As of 2026-11-13. v1.0.0. Each item below names the work item (`laz-NNN`) whose
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
- Depth-stencil readback on MoltenVK: exact on our test app's check (0 bad of 90 on the release core) and on a
  user's own self-test (laz-520)
- Restoring a saved state, then drawing 3D: an Azahar bug crashed the first 3D draw after a state load; our core
  fixes it (patch 0011), with a test-app test, and both user projects pass on it (laz-660)

## What does not work yet

- macOS before 15, Intel Macs, Windows and Linux. The core needs macOS 15 (see Known limits).
- Poll-exact movies: our core exports `lazpy_movie_play`; the host and Python do not call it; not in 1.0.
- Guest memory and the watch list on Azahar's own core: they raise `NeedsLazpyCore`.
- Any app that is not homebrew: no console keys, no Nintendo system files, no encrypted titles.

## Known limits

- Runs on Azahar's own core do not repeat exactly; exact repeats are gated on our core only.
- Touch rows 63, 125, 126 and 127 reach the guest one pixel off (HID truncates a float, as in Azahar's Qt build);
  `docs/USING.md` section 5 has the table.
- An ABI-3 host loads ABI-2 and ABI-3 states; an older host refuses newer states, and a state may not load across core
  versions.
- A multi-field record read from guest memory can be torn (some fields from the frame before); the watch list too.
- One `azh_open` per process: the Python layer runs each Emulator in its own worker process.
- The slot cap counts only libazahar's own workers, not other emulators on the machine.
- The core, `libazhost.dylib` and `azhost` need macOS 15 or later (the core's OpenSSL is built for 15).
- The guest's HTTPS finds a CA file only where Homebrew's `openssl@3` is installed (OpenSSL's compiled-in paths).
  Homebrew tests do not need it.
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
  - Windows and Linux: macOS arm64 first.
  - Audio output: not built.
  - Any window: the tool is headless.
  - Patching HID's touch truncation: four rows move by one pixel; documented.
  - Azahar's RPC server and gdb stub: not in libretro builds.
  - Commercial games in tests or docs: homebrew only.
  - `.cia` installs: the host loads `.3dsx`.
  - Wireless, motion and camera: not built.
  - PyPI: the route is a clone and an editable install.
  - A Python command line: not built (`azhost` is the host's command line).
  - HOME: not offered.
  - CI on GitHub runners: see Next.
  - Gen3D's adapter: Gen3D's own work.

## Next

- CI on GitHub runners (about 0.5 h).
- A core rebuild with patch 0008's comment fixed.
- Gen3D's adapter (Gen3D's own work).
