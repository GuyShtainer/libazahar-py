# libazahar-py: the whole-scope plan

Item laz-10, revision 1 (2026-11-12, opus), after review 1 (`docs/reviews/plan-review-1.md`). Review 2 is laz-12;
after it, one item and one short plan per phase. Inputs: `docs/research/` (spikes 1 and 2, prior art, Gen3D's
needs, the libretro.py probe), `prototype/fe2.c` and `fe3.c`, `tools/fetch.sh`, and Azahar's source at tag 2126.2
(`src/citra_libretro/`, `src/core/hle/kernel/svc.cpp`, read 2026-11-12). "src:" means that tag.

**Hours unit: agent wall time**, the unit `docs/hours.tsv` books (start to end of each agent run and main-loop
block, opus plans and reviews included). Machine time (core builds, background test batches) is listed apart and is
not in the totals. For scale: draft 1's numbers were one-worker hours; the same work comes to about 39 of those.

## 1. What we build, in one paragraph

A small C library, **the host** (`libazhost.dylib`, plus a thin `azhost` command-line program over it), loads an
Azahar libretro core, answers its Vulkan setup through MoltenVK with no window, and runs the guest unpaced. It takes
one batch per call ("run 600 frames with this input table, shoot frames 300 and 600, stop early if this text shows
up in this SD file") and does the whole batch natively: the frame loop, the input feed, the GPU readback, the PNG
encode, the stop checks, and (with our core) memory reads. A Python package (`libazahar`) gives each emulator
instance its own worker process, which loads the host through ctypes; the user's script gets plain results.
**Our own patched core** (`azahar_lazpy_libretro.dylib`, built from a pinned Azahar commit plus our patch files)
adds what the stock core lacks: guest memory read and write, and a fixed start clock. It is published with its full
source. The stock core still works for everything but memory and the fixed clock. A tiny homebrew app built here
from source is the test guest, so no test needs a commercial game.

## 2. Decisions

### 2.1 The Python route: our own C host library, a thin ctypes layer, batches only

- **libretro.py is not the host** (`docs/research/libretro-py-probe.md`, v0.12.0): no Vulkan context, its Vulkan
  negotiation answer is a stub returning false, so the core fails to load with Vulkan; with Software it boots at
  20 fps. It calls `retro_run` from Python every frame (about 90 µs per frame). We borrow its `Session` API shape
  and its environment-call table (`drivers/environment/default.py`) as a checklist for our environment callback.
- **C, not Rust.** The libretro and Vulkan interfaces are C headers, fe2.c and fe3.c work, the host is about
  1500 lines of glue. Rust would add a toolchain and unsafe blocks around every callback for no speed gain.
- **One process per instance, never threads.** Azahar's libretro glue drives one process-wide emulator
  (`Core::System::GetInstance()` and file statics throughout `citra_libretro.cpp`).
- **ctypes in a worker process, not a wire protocol.** `Emulator` starts its worker with
  `subprocess.Popen([sys.executable, "-I", "-m", "libazahar._worker"], pass_fds=...)` and talks to it through a
  `multiprocessing.connection.Connection` over an inherited pipe (pickled calls; stdlib). No `multiprocessing`
  spawn, so a user script without a `__main__` guard never re-launches itself. The worker loads the dylib with
  ctypes and makes one ctypes call per batch. A `multiprocessing.shared_memory` block, created by the parent and
  handed to the C host, holds the pixel buffers, the heartbeat word and the last core message, so numpy in the
  parent wraps pixels with no copy. Why this split: no request parser in C; a guest hang or a host crash never kills
  the user's script; no compiled Python extension (`pip install -e .` stays pure Python, `make` builds the dylib).
  Per-frame Python callbacks never exist.

### 2.2 The C/Python boundary: what the host library exports

| C function (0 or a negative error code; `azh_error()` gives the text) | What it does | From |
|---|---|---|
| `azh_open(core, sysdir, log, shm)` / `azh_close()` | load the core, set the folders, attach the shared block | libretro |
| `azh_set_option(key, value)` | a core option, before boot | libretro |
| `azh_boot(app)` | load the app, set up Vulkan through MoltenVK (or Software); detects a failed boot (2.6) | libretro |
| `azh_run(const azh_batch *in, azh_result *out)` | the batch (below) | new |
| `azh_shot(screens, format, path)` | the current frame: top 400x240, bottom 320x240 or both; PNG to a path or raw RGBA into the shared block | RPC Take/ReadScreenshot |
| `azh_save_state(path)` / `azh_load_state(path)` | savestate to and from a file | RPC Save/LoadState |
| `azh_read(addr, len, buf)` / `azh_write(addr, len, buf)` | guest memory by virtual address; our core only, else the error "needs the libazahar core" | RPC Read/WriteMemory |
| `azh_set_input(const azh_input *held)` | set the held state now (held until changed) | RPC SetInput |
| `azh_stats(azh_stats *out)` | frames, wall time, CPU time (rusage), peak memory, core version | RPC GetPerfStats |
| `azh_abi_layout(azh_layout *out)` | sizes and field offsets of every struct above, for the Python layout check | new |

`azh_batch` holds plain fixed-width arrays with their lengths. Input records (frame, buttons, touch x, touch y,
touch down, circle x, circle y), each setting the held state from that frame on (movie semantics, as RPC SetInput's
"held until cleared"), so Gen3D compiles its CTM movies straight into it. Shot frames, each with a screens and
format choice. The stop rule: an SD file and a plain text to find in its new bytes, checked every K frames. A
between-frames wall limit. After Phase G, a watch list (addresses, and a frames x words result area).
`azh_result` gives frames run and the stop reason: `frames`, `text`, `wall_limit`, `guest_break` (the core logged
"Emulated program broke execution", src svc.cpp:1148-1166, which svcBreak causes), `guest_error` (the core sent a
fatal SET_MESSAGE, src citra_libretro.cpp:287-303), `guest_exited` (the core sent SHUTDOWN). The host bumps the
heartbeat word after every `retro_run`. The parent, not the C loop, catches the two cases where `retro_run` never
returns: a guest that stops submitting frames (src citra_libretro.cpp:286 loops until a frame is submitted) or a
dead worker. The crop is native: the core's default layout puts top at (0,0) and bottom at (40,240) in a
400x480 frame. `azhost run <app> --frames 600 --shot 300,600 --opt key=value` calls the same functions.

### 2.3 Inputs, exactly

- `Buttons` bits are libctru's `KEY_*` layout, so the test app's logged keys and Gen3D's movies compare one-to-one.
  The host maps them to libretro joypad ids. ZL is 12 and ZR is 13. L3 (14) and R3 (15) are never sent: the core
  binds L3 to HOME and screen swap (src citra_libretro.cpp:191-193, 243), so HOME is not offered in v1. Do not copy
  fe3.c's button table; it sends ZR as 14.
- Touch: the host takes a bottom-screen pixel (x 0-319, y 0-239), rejects points outside it, and turns frame pixel
  (X, Y) = (x + 40, y + 240) into pointer values `p = floor((X + 0.5) * 65534 / 400) - 32767`, and the same for Y
  with 480. That lands on the exact pixel under the core's mapping `int((p + 0x7fff) / 65534 * width)` (src
  mouse_tracker.cpp:144, 171). A unit test round-trips every bottom-screen pixel through both formulas and asserts
  the pointer is never (0,0), which the core ignores (mouse_tracker.cpp:148).
- Circle pad: plus or minus 32767 on the left analog stick; the core inverts y (src input_factory.cpp:65); the API
  takes the 3DS sense (up is positive) and the host converts.
- The cursor: the pointer-timeout option defaults to on, and the cursor's "last moved" time is set only by
  right-stick movement (src mouse_tracker.cpp:191, 221, 266). With the right stick pinned to C-stick only, no
  cursor is ever drawn. Both options are pinned, and gate C checks that a shot with touch held has no cursor pixels.

### 2.4 Options, versions, repeatability

- A committed option profile (`host/options-default.txt`) sets **every** core key explicitly (renderer Vulkan,
  New 3DS on, right stick C-stick only, pointer timeout on, motion off, deadzone, both touchscreen sources, the
  resolution factor 1). fe2 answers the option-version query with 0, so unset keys take the first listed value,
  which differs from RetroArch's defaults; the profile removes that guess. Users override per key.
- On every boot host.log gets the effective option set and the core's `library_version`. The host refuses a core
  whose version is not the pinned stock or our pinned build unless `LAZ_ANY_CORE=1`.
- The guest clock runs on guest time (spike 2: the HUD went 15:56 to 16:04 over 535 guest seconds at 5x real time);
  only its start value comes from the host clock, and 2126.2 has no option to fix it. Our core adds one (2.7), so
  runs repeat exactly on it; on the stock core USING.md says the start clock varies.

### 2.5 The Python API (shape from libmgba-py, AzaharRPC.py and libretro.py's Session)

```python
from libazahar import Emulator, Buttons, Touch
with Emulator(app="build/testapp.3dsx", workdir="runs/a", sd_seed="fixtures/sd",
              options={"is_new_3ds": "disabled"}) as emu:      # starts its worker, boots
    r = emu.run(600, inputs=[(10, Buttons.A), (12, 0), (40, Touch(160, 120)), (42, Touch.up)],
                shots=[300, 600])                               # one native batch
    r.frames, r.stopped_by, r.shots[600].top                    # Path to top.png
    emu.run_until(file="testapp/log.txt", text="ready", max_frames=6000)   # path inside the SD folder
    top, bottom = emu.screens()                                 # numpy arrays if numpy is installed, else bytes
    emu.save_state("runs/a/field.state"); emu.load_state("runs/a/field.state")
    emu.memory.u32(addr); emu.memory.read(addr, 64)             # our core only (Phase G)
    emu.sd / "testapp" / "log.txt"                              # pathlib.Path into the instance's SD folder
```
`run_frame()`, `set_keys(raw=)` and `memory.u8/u32` keep libmgba-py's names (gba-toolkit's `tools/vsd_run.py` uses
them) for one-off use; each is one round trip, never the hot path. Errors are typed: `BootError`, `GuestBreak`,
`GuestError`, `HostTimeout` (no heartbeat for T seconds; the parent kills its own worker and attaches the last core
message), `HostCrashed` (the worker died), `NeedsLazpyCore`. `close()` always reaps the worker. Type hints and
docstrings on every public name; stdlib only, numpy and Pillow optional.

### 2.6 Boot failure is detected, not assumed

`retro_load_game` returns true before the app loads (src citra_libretro.cpp:515-520); a bad path shows up only as a
SET_MESSAGE and empty frames (218-223). `azh_boot` runs the first `retro_run` and fails with `BootError` on a
load-failure message or when no frame image arrives.

### 2.7 Our patched core

- **Where:** patch files in this repo, not a public fork (a fork is a second repo to keep publish-ready and audit).
  `core/PIN` holds the full 40-hex Azahar commit (tag 2126.2, the core we measured) and every submodule's commit,
  checked after the clone. `core/patches/000N-*.patch` are applied with `git am`. `tools/build-core.sh` clones into
  `dl/azahar-src/`, checks the pins, applies the patches and runs Azahar's own libretro build
  (`cmake -DENABLE_LIBRETRO=ON`, target `citra_libretro`, as its CI job `libretro.yml:174-196` does), at `nice 10`,
  never as root. rules.md 2 allows exactly this (Guy 2026-11-12); it needs Homebrew's `spirv-tools` (installed).
- **The patch** touches only `citra_libretro.cpp` and `core_settings.cpp`: (1) two exported C functions,
  `lazpy_read_memory(vaddr, buf, len)` and `lazpy_write_memory(...)`, which check `IsValidVirtualAddress` and call
  `Memory::ReadBlock` / `WriteBlock` on the current process (src memory.h:558, 599, 673): about 30 lines covering
  globals, heap, linear heap and VRAM, with no map decoding; the host calls them only between frames and finds them
  with dlsym; (2) a fixed start-clock option; (3) `library_version` gets a `-lazpy.N` suffix. Each patched file gets
  a "modified by libazahar-py on <date>" notice.
- **Not patched:** the SET_MEMORY_MAPS table. Spike 2 saw it sent once with only the stack page (0x0FFFC000, 0x4000)
  and VRAM: the map is built once, from `context_reset` in the Vulkan path (src citra_libretro.cpp:474, 416), when
  only the code and the stack are mapped, and the region filter drops code and data. A fuller map would still miss
  globals. Savestate parsing is dropped too: a compressed archive, a guest run to drain I/O, 256 MB per read.
- **Name and release:** the binary is `azahar_lazpy_libretro.dylib`, so nobody takes it for Azahar's build. Each
  GitHub release that carries it carries, next to it, the corresponding source: a tarball of the pinned tree with
  every submodule (36 in `.gitmodules`; Azahar's repo alone is not enough, the submodules live on hosts we do not
  control), our patches, the build script, and the license texts of everything linked in (the tarball holds them;
  `NOTICES.md` lists them). That is GPLv2 §3(a). Files at 2126.2 say GPLv2-or-later; ours is GPLv3.
- **User flow:** `fetch.sh` gains, after the first release, a sha256-pinned download of our released core (the fast
  default); `build-core.sh` is the from-source route. The stock core stays fetchable.
- **Updates:** fetch the new commit, `git am -3`, rebuild, the full test batch. About 1 h machine time and 0.3 h agent
  time when the patch applies. States saved by one core build do not load in another (src core.cpp:167-170).

### 2.8 Many instances and speed (spike 2's facts)

- Real 3D scene, one instance, at load 27: 334-345 guest frames per second, 5.6-5.7x real time, about 1.4 cores,
  0.5-0.8 GB. Under heavy load from other sessions (68-96): 129 fps alone, 3 x 136-138 at once. The load-robust
  number is CPU per guest frame: about 4.1-4.6 ms in every run. Three instances at the same heavy load gave about
  3.2x one instance's total, so the 3D scene is not stuck at spike 1's idle-menu ceiling. One `retro_run` is one
  guest vblank (spike 2's clock check), so x real time = fps / 59.83.
- `libazahar.Pool(n)` runs jobs across n instances, each in its own folder (`workdir/sys/Azahar/sdmc`, `nand`,
  `shots/`, `host.log`), seeded from `sd_seed` by copy. A machine-wide cap: slot files under
  `~/Library/Caches/libazahar-py/slots/`, each held with `flock` by a running worker; the kernel drops the lock when
  a process dies, so nobody kills anything. Default cap 3 (provisional, set by Phase E's table; env
  `LAZ_MAX_INSTANCES`). Workers run at `os.nice(10)`. The cap sees only our workers, so `Pool` also warns when the
  load average is above twice the core count (other sessions' emulators).
- Every speed table reports fps, CPU ms per guest frame and the load average, so no gate waits for a quiet machine.

## 3. Phases

Each phase: an opus phase plan, sonnet builds from it, an opus review of the diff, the main loop commits. Every
gate runs on this Mac, headless, as a command with a pass/fail answer. Gen3D's needs: (1) boot + SD seed and
read-back: A, C; (2) frame-exact buttons then touch: C; (3) both screens cropped: A, B, C; (4) run until N frames
or a log line: C; savestates to skip its 7600-9200-frame boot: D; (5) many instances: E; (6) memory: F, G.

### Phase A: the host library builds from a fresh clone and boots an app (1.25 h)
Delivers: `host/` split from fe2.c and fe3.c into small files (core loading and the environment callback, Vulkan
setup and readback, PNG and cropping, the batch loop, the exported API, the `azhost` main); the GL path removed;
every Vulkan and core return value checked; the readback buffer and command pool made once and reused; the log
callback thread-safe and filtered by level in C (the core logs at Debug, possibly from its log thread); the option
profile and the version check (2.4); boot-failure detection (2.6); a Makefile building `build/libazhost.dylib` and
`build/azhost` with `-Wall -Wextra -Werror`, and `make check` adding `clang --analyze`. Brief notes for the golden
rules: libretro and Vulkan callbacks are the documented function-pointer exception (C rule 9), functions under
about 60 lines, about 2 assertions each, savestate buffers allocate per call with one clear owner (C rule 3).
Gate: a fresh clone in a temp folder with `dl/` and `vendor/` seeded by copy (`fetch.sh` verifies and downloads
nothing), then `make check && make` with zero warnings; `build/azhost run <app> --frames 600 --shot 300,600` writes
`top` and `bottom` PNGs of the right sizes; `lsappinfo list` has no entry for it and `otool -L build/azhost` shows
no AppKit; a missing file and a non-3DS file both give `BootError`.

### Phase B: the test app, built from source (1 h; alongside A)
Delivers: `testapp/` (libctru, devkitARM, GPLv3, ours, no system archives: its own glyphs, no shared font). It reads
a seeded `sdmc/testapp/control.txt` **before its first frame** (so a seed alone picks a mode: 2D pattern, a light
citro3d scene, break on purpose with svcBreak, write `ready` at frame N), draws corner markers on both screens,
and every frame writes one flushed line to `sdmc/testapp/log.txt` (vblank count, guest clock, held keys, touch
point, circle pad) and the same record through `svcOutputDebugString`. It keeps the record both in a global and in
a heap block, and logs both addresses at start. `make testapp` builds `build/testapp.3dsx` (ignored).
Gate: zero warnings; under `azhost run` the log has one line per frame, and the shots show the markers at the exact
expected pixels on both screens (this proves the 40 px bottom offset and the readback).

### Phase C: batches, input, touch, stop rules (1.5 h)
Delivers: `azh_run` with the input table, touch and circle pad (2.3), the SD-file stop rule (plain substring on new
bytes only, every K frames, default 30), the stop reasons and the heartbeat (2.2), the wall limit, SD seeding.
A 15-minute check of the debug-string route: if the test app's `svcOutputDebugString` lines reach the log callback
within two frames, add a `debug_text` stop rule (no file reads); if late, record it and keep files only. Pure-C
unit tests (`make test-host`, no core): input table, the touch round trip of every pixel, crop, stop matcher, PNG.
Gate (test app, a script in `tests/`): (a) planned button changes appear in the log on exactly the planned frames,
with a fixed, measured offset; (b) 20 touch points land on the exact bottom-screen pixels, and a shot with touch held
has no cursor pixels; (c) `ready` stops the batch within K frames; (d) the vblank count after N runs is N plus a
constant; (e) the same seed and table twice give identical shot hashes on the stock core, or the start-clock
difference is written down (rerun on our core in Phase F); (f) the break mode stops with `guest_break`.

### Phase D: the Python layer v1, with savestates (1.5 h). Gen3D starts its adapter here
Delivers: `python/libazahar/` (2.5), the worker and shared block (2.1), the ctypes declarations checked against
`azh_abi_layout()`, typed errors, `pyproject.toml` for `pip install -e .`, the dylib found by `LAZ_HOST` or
`build/`; savestates (`retro_serialize_size` does the work, drains guest I/O for up to 5 s, and its size varies);
pytest integration tests on the test app, skipped with a reason when the core or the app is missing; `docs/USING.md`
with the Gen3D mapping table (each Gen3D mechanism and its replacement call) and the forced-mode seed pattern.
D may start from the frozen C header while C is built.
Gate: `pytest` passes the Phase C checks through Python; SIGSEGV sent to our own worker raises `HostCrashed` within
1 s; SIGSTOP sent to it raises `HostTimeout` after T and leaves no process (checked by its pid); a 200,000-frame
batch is not taken for a hang; save at frame N, run M, copy the SD log aside, load, run M: identical shot hashes and
identical log lines written after each load; `python3 -I -m libazahar run ...` works as a CLI.

### Phase E: many instances and the speed table (1 h)
Delivers: `Pool`, per-instance folders, the slot cap, `nice`, the load warning; a scaling script running 1, 2 and 3
instances of the test app's 3D scene for 60 s each, printing guest fps (from the app's own vblank log), CPU ms per
guest frame and the load average; an optional local row on a Gen3D 3D scene that agents may skip (needs a game on
disk; its shots never committed). The host's own share of a shot-free batch is measured (target under 5 %); the
cheap wins are taken (zlib level 1, raw frames when pixels are wanted, readback only on asked frames).
Gate: 3 instances give correct, separate logs and shots; a 4th waits for a slot under a cap of 3; killing one frees
its slot within 1 s; the table goes into `docs/research/` and sets the default cap; the README speed line is "x real
time at load under 10" if one instance reaches 3x there, else the CPU ms per frame figure.

### Phase F: our patched core (1.5 h agent; 1-2 h machine; alongside E, can start right after A)
Delivers: `core/PIN`, `core/patches/` (2.7), `tools/build-core.sh`, the notices in patched files; the first build
runs in the background. Azahar's tree is about 1-2 GB with submodules; a clean build is about 15-25 min on a quiet
machine, 40-90 min at spike 2's load; a rebuild after a patch edit a few minutes.
Gate: `tools/build-core.sh` from an empty `dl/azahar-src/` checks every pin, applies the patches and builds
`azahar_lazpy_libretro.dylib`; the host boots the test app on it and logs the `-lazpy` version; the Phase C and D
test batch passes on it; the fixed-clock option makes gate C(e) give identical shot hashes.

### Phase G: memory reads and the watch list (0.5 h; after F)
Delivers: `azh_read`/`azh_write` through the exported functions, `emu.memory`, the per-frame watch list in batches
(a copy per word), `NeedsLazpyCore` on the stock core.
Gate: on our core, the test app's record at both logged addresses (global and heap) reads back the values its log
shows, frame by frame, for 600 frames, both by `read` calls and by the watch list; a write to the record changes the
next logged line; an unmapped address gives a clean error; on the stock core every memory call raises
`NeedsLazpyCore`.

### Phase H: docs and the public repo (0.5 h)
Delivers: README (what it is, honest status, measured numbers with their load, install, a 10-line example),
`STATUS.md` (what works, what does not, that a fuller memory map and savestate parsing were considered and
dropped), `docs/USING.md` finished, `docs/HOST-API.md` (the C API), `NOTICES.md`, examples.
Gate: a fresh clone followed by only the README's steps runs the example on the test app; every number in the
README has a source row in `docs/research/`.

### Phase I: legal audit and the GitHub release (0.75 h plus Guy)
Delivers: `release-legal-audit` over the repo, its history and every asset; fixes; a release with
`azahar_lazpy_libretro.dylib`, the core's source tarball with submodules, patches, build script and notices,
`testapp.3dsx` (ours), and the repo's own source. No prebuilt host dylib (unsigned downloads are quarantined;
`make` takes seconds), no MoltenVK, no stock core. Then `fetch.sh` gets the pinned download of our core.
Gate: the audit says shippable for the repo, the core asset, the source tarball and the notices; `git ls-files`
shows no forbidden file (rules.md 1); Guy says push.

**Total: about 9.5 h agent wall time** (A 1.25, B 1, C 1.5, D 1.5, E 1, F 1.5, G 0.5, H 0.5, I 0.75), plus about
1-2 h machine time for the first core build and background test batches. Order: A and B in parallel; then C; then
D; then E with F in parallel (F's build can start as soon as A is done); G after F; H; I. Gen3D's needs (1)-(4)
and savestates land by D; memory by G.

## 4. Risks and what we do about them

1. **The first core build fails on this Mac** (a toolchain difference from Azahar's macos-26 runner; heavy load).
   Mitigation: start it right after A, in the background, nice'd; follow Azahar's CI commands exactly; the stock
   core keeps every phase but G moving.
2. **Speed under shared load.** Spike 2 got 5.6x at load 27 and 2.2x at load 68-96. Mitigation: CPU ms per guest
   frame as the stable figure; the slot cap, `nice` and the load warning; no speed quoted without its load.
3. **The GPL release of a modified core** is new work for this project. Mitigation: source tarball with every
   submodule next to the binary, notices in patched files, the distinct name, the audit on every asset.
4. **A ctypes struct out of step with the C header** gives silent garbage. Mitigation: `azh_abi_layout()` compared
   at import; fixed-width fields only, no unions, no pointers to pointers.
5. **Core updates break things or old states** (release candidates weekly; states are tied to one build).
   Mitigation: both cores pinned; an update is a deliberate change with `git am -3` and the full test batch; USING.md
   says states do not survive a core change.
6. **Debug-string lines may arrive late** (the core's log runs on a thread). Mitigation: SD files stay the main stop
   rule; the debug route is added only if Phase C's check shows it within two frames.
7. **The machine is shared.** Mitigation: as 2; no step ever kills a process it did not start.
8. **devkitARM is needed for the test app.** It is on this Mac; elsewhere those tests skip with a reason, and the
   release attaches `testapp.3dsx`.

## 5. Out of scope

Windows and Linux (macOS-only calls stay in one file); audio output (counted, not played); any window or GUI; a
fuller SET_MEMORY_MAPS table; savestate parsing; an upstream pull request (Guy: we edit the core to our needs);
Azahar's RPC server and gdb stub (excluded from libretro builds, root CMakeLists.txt:109-111); commercial games in
tests or docs; `.cia` install flows; wireless and netplay; motion and camera; a PyPI release; HOME and the right
stick as touch; CI on GitHub runners (after the first push: `make test-host` and the Python unit tests, about
0.5 h; building the core there at the first update); Gen3D's adapter (Gen3D's work and ledger).

## 6. Hour-saving pass (revision 1)

| Existing thing | What it saves | Verdict |
|---|---|---|
| `prototype/fe2.c` and `fe3.c` | Core loading, Vulkan negotiation, readback, the frame-range input table and the env-call handler shape all work: A is a cleanup | use, minus fe3's button table and touch formula |
| `tools/fetch.sh` (done) | Downloads, pins and headers | use; the fresh-clone gate seeds `dl/` by copy |
| Azahar's own CI job (`libretro.yml:174-196`) | The exact configure and build commands for the macOS core | copy the commands into `build-core.sh` (we run our script, never theirs) |
| The core's `Memory::ReadBlock` / `WriteBlock` | Memory reads are a 30-line export, not map decoding or savestate parsing | use (about 2 h saved against draft 1's branch 2) |
| Patch files plus a pin, not a fork | No second repo to audit and keep publish-ready | use (about 1 h now, 0.5 h per update) |
| The core's `retro_serialize` | Savestates are a file write | use |
| The core's own log lines for svcBreak and SET_MESSAGE | Guest-crash detection with no new mechanism | use |
| libretro.py (MIT), probed | Session shape and the env-call checklist; cannot host this core | borrow ideas only (map decoding no longer needed) |
| AzaharRPC.py's request set | Names and meanings of held input, touch range, screenshot formats, states | borrow semantics, no code |
| libmgba-py's names (`run_frame`, `set_keys(raw=)`, `memory.u8`) | Names Guy's sibling tools already use | borrow names |
| `azh_abi_layout()` instead of a compiled layout test | No compiler at test time | use (0.5 h) |
| CPU ms per guest frame; speed rows folded into E | No separate speed phase, no quiet-machine wait | use (about 2 h in draft 1's units) |
| Source answers for the cursor and the clock | No try-and-mask chain | use |
| Nanoarch-style frontends, RetroArch, Rust frontends | GL plus a window; Vulkan needs a surface; no Vulkan HW core support found | rejected |

Cheaper tests: pure-C unit tests for every pure function; one integration batch per phase on the test app, launched
in the background; the full suite once per large batch (Guy's testing rule).

## 7. Questions for Guy

Answered 2026-11-12:
- Phase F: we patch and build the core ourselves so memory reads work, and publish the patched core publicly "so it
  works for everyone". No upstream pull request (Guy: "no need to submit a pull request, we edit the core to our
  needs"; this replaced his earlier yes to one). Spike 2 showed the stock core 2126.2 exposes no heap or FCRAM.
  Published core binaries ship with their GPLv2+ corresponding source (pinned Azahar commit plus our patch).
- Phase I: the name `libazahar-py` is approved (Guy: "its informative and excct. so if its clear we use it"), subject
  to the legal agent's check at release.
- The core build (Guy 2026-11-12): our build script may run Azahar's own CMake build on the exact pinned commit,
  nice'd in the background; nothing else in a download is run (now rules.md 2). `build-core.sh` checks every commit
  in `core/PIN` (Azahar and each submodule) before it builds, writes only inside `dl/azahar-src/` and `build-core/`,
  and never runs as root.
- `spirv-tools` (needed by Azahar's macOS libretro build) is installed with Homebrew on Guy's Mac.

Open: none.

## 8. Changes from review 1

- B1 (Phase F cannot work): done. F is now our patched core (2.7, Phase F) with a 30-line read/write export over
  `Memory::ReadBlock`/`WriteBlock`; memory moved to Phase G; the map-load location corrected to `context_reset`;
  libretro.py's map decoding cut; the watch list moved to G; savestate parsing dropped (STATUS keeps one line);
  G's gate reads a global and a heap record. The fuller SET_MEMORY_MAPS is declined: only RetroArch cheat users
  would gain, and it still misses globals.
- B2 (crash and hang gates): done. Stop reasons `guest_break`, `guest_error`, `guest_exited`, `wall_limit` (2.2);
  the heartbeat in shared memory; HostCrashed by SIGSEGV and HostTimeout by SIGSTOP to our own worker; the test
  app's break mode. One change to the review: svcBreak only logs (src svc.cpp:1165), so `guest_break` comes from the
  log line, not from SET_MESSAGE.
- B3 (GPL release and build carve-out): done. Patch files plus `core/PIN` and `build-core.sh`, no fork; source
  tarball with every submodule beside the binary; notices; the distinct name; NOTICES.md; the audit covers every
  asset; the rules.md 2 exception is decided (Guy, now in rules.md 2), as is the `spirv-tools` install.
- S1 (touch off by one, ZR as HOME): done (2.3), with the every-pixel round-trip unit test.
- S2 (cursor): done (2.3); the fallback chain dropped; gate C(b) checks no cursor pixels.
- S3 (worker launch, copies): done (2.1): `Popen` of `-m libazahar._worker`, a Connection over an inherited pipe,
  a shared-memory block for pixels and the heartbeat.
- S4 (savestates in D): done, with the variable size, the I/O drain, states tied to a core build (risk 5) and a
  gate that compares shots and post-load log lines.
- S5 (speed metric and branches): done (2.8, Phase E): CPU ms per guest frame, default cap 3 provisional, the
  "3x at load under 10" rule, G's rows folded into E, the Gen3D row optional and local.
- S6 (clock): done (2.4): the start-clock option in our core; C(e) runs on both cores; USING.md says what the stock
  core cannot repeat.
- S7 (options and version): done (2.4, 2.3): the full option profile, the effective set and version in host.log, the
  version refusal, circle-pad units, libctru key bits, HOME not offered.
- S8 (silent boot failure): done (2.6, gate A).
- S9 (gate A checks): done: `lsappinfo` and `otool -L`; the exact-pixel check moved to B.
- S10 (test app): done: control file read before the first frame, flushed lines, no system archives.
- S11 (units and core cost): done: one unit, agent wall time, stated at the top; core build cost and update cost in
  2.7 and Phase F; machine time listed apart.
- Nice, taken: N1 (debug-string check in C, risk 6), N2 (log filter in C), N3 (`azh_abi_layout`), N4 (no prebuilt
  host dylib), N5 (load warning), N7 (fresh-clone gate seeds `dl/` by copy), N8 (golden-rule notes in A's brief).
- Nice, declined for v1: N6 (CI on GitHub runners) needs a pushed repo, which waits for Guy's push; listed in
  section 5 as the first follow-up after the release.
- Also changed: the core pin stays tag 2126.2 (the core both spikes measured; GPLv2-or-later files); moving to 2127
  is an ordinary update. rules.md 5 still quotes spike 1's 1.2 GB and the shared ceiling; spike 2 says 0.5-0.8 GB
  and about 3.2x for three instances on a 3D scene (left for the main loop, since this revision edits PLAN.md only).
