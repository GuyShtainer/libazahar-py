# libazahar-py status

As of 2026-11-13, commit 896c2fe. v0.1.0 is an early prerelease. Each item below names the work item (`laz-NNN`) whose
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
- Our patched core builds from Azahar's pinned source with our patch files and a build script; the build itself is gated in laz-320 (laz-110)
- Our core's gate: built without Azahar's built-in key data and default HTTP client certificate, loading no keys; the
  debug-text stop; exact repeats; states restored into equal instances; states moving between the two cores
  (laz-320)
- Many instances at once: `Pool`, the machine-wide slot cap, `LoadWarning`, the speed table, a default cap of 2
  (laz-310)
- Guest memory on our core: `emu.memory` reads and writes and the per-frame watch list (laz-330)

## What does not work yet

- macOS before 15, Intel Macs, Windows and Linux. The core needs macOS 15 (see Known limits).
- Poll-exact movies (`lazpy_movie_play` is in our core, but no gate ran it): not tested.
- The default instance cap (2) rests on a light scene (the test app). It stays provisional until a real-scene row
  exists. The real-scene speed rows in the README were measured on Azahar's own core (spike 2 ran before our core
  existed), on a busy machine; no real scene has run on our core yet.
- Guest memory and the watch list on Azahar's own core: they raise `NeedsLazpyCore`.
- Any app that is not homebrew: no keys, no system files, no encrypted titles.

## Known limits

- Runs on Azahar's own core do not repeat exactly; exact repeats are gated on our core only.
- Touch rows 63, 125, 126 and 127 reach the guest one pixel off (HID truncates a float, as in Azahar's Qt build);
  `docs/USING.md` section 5 has the table.
- An ABI-3 host loads ABI-2 and ABI-3 states; an older host refuses newer states, and a state may not load across core
  versions.
- A multi-field record read from guest memory can be torn (some fields from the frame before); the watch list too.
- One `azh_open` per process: the Python layer runs each Emulator in its own worker process.
- The slot cap counts only libazahar's own workers, not other emulators on the machine.
- The v0.1.0 core's header says macOS 11.0, but it needs macOS 15: its OpenSSL is built for 15. `libazhost.dylib` and
  `azhost` are built for macOS 15.0.
- The guest's HTTPS finds a CA file only where Homebrew's `openssl@3` is installed (OpenSSL's compiled-in paths).
  Homebrew tests do not need it.
- `azhost` has no `--help`; an unknown first argument prints the usage and exits with 2.
- The ABI may change before 1.0; each change bumps `AZH_ABI_VERSION` (now 3).

## Considered and dropped

- A fuller `SET_MEMORY_MAPS` table: Azahar's core builds it once, so we did not patch it; guest memory comes from our
  core's own read and write calls.
- Savestate parsing as a way to read memory: dropped for the same reason.
- An upstream pull request: Guy decided "no need to submit a pull request, we edit the core to our needs". Any
  upstream patch would first have to follow Azahar's `AI-POLICY.md`.
- Building OpenSSL ourselves so the core runs on macOS 11-14: it needs a core rebuild and a new gate; the release says
  macOS 15 or later instead.
- A scripted download of Azahar's own core: removed before v0.1.0. Our core is the default, and comparisons take
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
- A real-scene speed row on our core (quiet machine), and a real-scene row for the cap.
- A hint in the missing-core `BootError` ("run tools/fetch.sh --lazpy-core or set LAZ_CORE"), and the stale "until D"
  comments in `host/azhost.h`.
- `ArgumentError`: a `LibAzaharError` that is also a `ValueError`, raised for every bad argument.
- A `fresh_sd=True` option that clears the SD folder before seeding.
- A core rebuild with a macOS 15 header and patch 0008's comment fixed.
- Gen3D's adapter (Gen3D's own work).
