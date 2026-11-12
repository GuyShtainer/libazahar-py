# libazahar-py: the whole-scope plan

Item laz-10, revision 2, final (2026-11-12, opus), after reviews 1 and 2 (`docs/reviews/plan-review-{1,2}.md`).
Next: one item and one short plan per phase. Inputs: `docs/research/` (spikes 1 and 2, prior art, Gen3D's needs,
the libretro.py probe), `prototype/fe2.c` and `fe3.c`, `tools/fetch.sh`, and Azahar's source at tag 2126.2
(commit 219d743a1e698101fe1ab8bef43e6563126c3c27). "src:" means that tag; every src claim in this revision was
re-read there on 2026-11-12.

**Hours unit: agent wall time**, what `docs/hours.tsv` books (start to end of each agent run and main-loop block,
opus plans and reviews included). Machine time (core builds, background test batches) runs detached, is listed
apart, and is not in the totals: no agent waits on a build (Guy's testing rule: launch, end the turn, be woken).

## 1. What we build, in one paragraph

A small C library, **the host** (`libazhost.dylib`, plus a thin `azhost` program over it), loads an Azahar libretro
core, answers its Vulkan setup through MoltenVK with no window, and runs one batch per call natively ("run 600
frames with this input table, shoot frames 300 and 600, stop if this text shows up in this SD file"). A
whole-console **savestate** can be written at any frame, and a later run can **start from that file instead of
booting** (Gen3D skips its app boot, world build and game title this way). A Python package (`libazahar`) gives each
instance its own worker process, which loads the host through ctypes. **Our own patched core**
(`azahar_lazpy_libretro.dylib`, Azahar's 2126.2 source tarball plus our patches, published with its source) adds
memory read and write, a fixed start clock, deterministic guest I/O and clean error returns; the stock core works
for everything else. A tiny homebrew app built here from source is the test guest.

## 2. Decisions

### 2.1 The Python route: our own C host library, a thin ctypes layer, batches only

- **libretro.py is not the host** (`docs/research/libretro-py-probe.md`): no Vulkan context, so the core fails to
  load; Software runs at 20 fps; Python calls `retro_run` every frame. We borrow its `Session` shape and its
  environment-call table as a checklist.
- **C, not Rust.** C headers, working prototypes, about 1500 lines of glue; Rust adds a toolchain for no speed gain.
- **One process per instance, never threads.** Azahar's libretro glue drives one process-wide emulator
  (`Core::System::GetInstance()` and file statics throughout `citra_libretro.cpp`).
- **ctypes in a worker process, not a wire protocol.** `Emulator` starts its worker with
  `subprocess.Popen([sys.executable, "-I", "-m", "libazahar._worker"], pass_fds=...)` and talks to it through a
  `multiprocessing.connection.Connection` over an inherited pipe (pickled calls; stdlib; no `multiprocessing` spawn,
  so a script without a `__main__` guard never re-launches itself). The worker makes one ctypes call per batch.
  A fixed-size **mapped file in the instance folder** (`host.map`; stdlib `mmap` in Python, `mmap` in C) holds the
  heartbeat, the stop code, the last core message and the pixel area: numpy in the parent wraps pixels with no copy,
  there is no shared-memory resource tracker, and the last message survives a worker crash for the error report.
  `-I` drops the user site, so USING.md says: install into a venv. Per-frame Python callbacks never exist.

### 2.2 The C/Python boundary: what the host library exports

| C function (0 or a negative error code; `azh_error()` gives the text) | What it does | From |
|---|---|---|
| `azh_open(core, sysdir, log, mapfile)` / `azh_close()` | load the core, set the folders, map the shared file | libretro |
| `azh_set_option(key, value)` | a core option, before boot | libretro |
| `azh_boot(app, state_or_null)` | load the app, set up Vulkan (or Software); with a state file, load it before the first counted frame (2.9) | libretro |
| `azh_run(const int32_t *inputs, n, const azh_batch *b, azh_result *out)` | the batch (below) | new |
| `azh_shot(screens, format, path)` | current frame: top 400x240, bottom 320x240 or both; PNG to a path or raw RGBA into the map | RPC Take/ReadScreenshot |
| `azh_save_state(path, int32_t *k_out)` / `azh_load_state(path)` | savestate to and from a file; `k_out` is the drain's extra guest frames (2.9) | RPC Save/LoadState |
| `azh_read(addr, len, buf)` / `azh_write(...)` | guest memory by virtual address; our core only, else "needs the libazahar core" | RPC Read/WriteMemory |
| `azh_set_input(const int32_t rec[7])` | set the held state now (held until changed) | RPC SetInput |
| `azh_stats(azh_stats *out)` | frames, wall and CPU time (rusage), peak memory, core version | RPC GetPerfStats |
| `azh_abi_layout(azh_layout *out)` | sizes and offsets of `azh_batch`, `azh_result`, `azh_stats` and the map | new |

- **Inputs** are flat `int32` records of 7 (frame, buttons, touch x, touch y, touch down, circle x, circle y); each
  sets the held state from that frame on (movie semantics, as RPC SetInput's "held until cleared").
- **`azh_batch`**: frames, shot frames (each with screens and format), the SD stop rule (file, plain text, check
  every K frames, default 30), the debug-text stop rule (our core only), a between-frames wall limit, and after
  Phase G a watch list (addresses; frames x words land in the map).
- **The SD text match** reads only new bytes, keeps the last len(text)-1 bytes so a match split across two reads is
  found, and restarts from 0 if the file shrank.
- **Crop** is native: the core's default layout puts top at (0,0) and bottom at (40,240) in a 400x480 frame.
- `azhost run <app> [--state f] --frames 600 --shot 300,600 --opt key=value` calls the same functions. There is no
  separate Python CLI.

**Stop reasons, from one detector** (src read 2026-11-12). Every guest failure reaches the host the same way:
`retro_run` loops `while (!HasSubmittedFrame())` over `RunLoop()` and, on any non-Success status, sends a
SET_MESSAGE "Fatal Error encountered (N): ..." and loops again (src citra_libretro.cpp:287-306; "unable to locate a
3DS system archive" for N = 10). svcBreak logs and then calls `Core::LogException`, which sets status 14,
ErrorCoreExceptionRaised (src svc.cpp:1164-1165, core/arm/exception_handler.cpp:142); `RunLoop` resets the status
to Success at its start (core.cpp:111), so the guest runs on. A guest exit is status 16, ShutdownRequested
(core.cpp:144, 150). The core never sends RETRO_ENVIRONMENT_SHUTDOWN (`LibRetro::Shutdown()`, environment.cpp:164,
has no caller). So the environment callback's SET_MESSAGE case reads N and:
- N = 14: flag `guest_break`; the batch stops when `retro_run` returns (it does: the guest keeps submitting frames).
- N = 16: write `guest_exited` and the message into the map and `_exit(EXIT_GUEST_EXITED)` at once (nothing useful
  follows a guest exit). Status 10's message and boot-time messages carry no "(N)" (check 3).
- Any other N: flag `guest_error`; if one `retro_run` gets 3 such messages without returning, write the reason and
  `_exit(EXIT_GUEST_ERROR)`. `_exit` in our own worker replaces longjmp (C rule 1).
- On our core, a 3-line patch makes `retro_run` return on a non-Success status (2.7), so all three come back as
  plain stop reasons with no `_exit`.
- The parent maps worker exit codes to `RunResult(stopped_by="guest_exited")` (the Emulator then closes) or
  `GuestError(message)`; any other death is `HostCrashed`; no heartbeat change for T seconds (default 30) is
  `HostTimeout`, and the parent kills its own worker. The boot has its own, longer timeout (first-run shader
  compiles). The host bumps the heartbeat after every `retro_run`.

### 2.3 Inputs, exactly

- `Buttons` bits are libctru's `KEY_*` layout, so the test app's logged keys and Gen3D's movies compare one-to-one.
  The host maps them to libretro ids: ZL 12, ZR 13; L3 (14) and R3 (15) are never sent, because the core binds L3 to
  HOME and screen swap (src citra_libretro.cpp:185-193, 243). HOME is not offered in v1. fe3.c's table (ZR as 14)
  is not copied.
- Touch: the host takes a bottom-screen pixel (x 0-319, y 0-239), rejects points outside it, and turns frame pixel
  (X, Y) = (x + 40, y + 240) into `p = floor((X + 0.5) * 65534 / 400) - 32767` (480 for Y). That hits the exact
  frame pixel under the core's `int((p + 0x7fff) / 65534 * width)` (src mouse_tracker.cpp:171-172) and is never
  (0,0), which the core ignores. After that come a float division (core/frontend/emu_window.cpp:169-185) and HID's
  `static_cast<u16>(y * 240)` (hid.cpp:292-293). In float32, x is exact for all 320 columns, but **guest y = 63,
  125, 126 and 127 arrive as y - 1** (recomputed here). We do not patch HID: Qt Azahar runs the same chain, so
  Gen3D's targets already live with it. The unit test models the whole chain in float32 and gives the expected guest
  pixel; gate C(b) compares against that; USING.md lists the 4 rows.
- Circle pad: plus or minus 32767 on the left analog stick; the core inverts y (src input_factory.cpp:65); the API
  takes up as positive and the host converts.
- The cursor: the pointer-timeout option defaults on and only right-stick movement sets "last moved"
  (mouse_tracker.cpp:191-238); with the right stick pinned to C-stick only no cursor is drawn. (It rests on
  `now - time_point::min()`, which overflows but works; gate C(b)'s no-cursor-pixel check covers it.)
- Gen3D's CTM movies record HID polls at 234 Hz (3.91 per frame) and its golden test uses poll counts, which frame
  records cannot express. Phase F checks (15 min) whether our core can export `lazpy_movie_play(path)` over the
  core's own Movie playback (hid.cpp:203, 296 already feed it); if yes, poll-exact movies run unchanged on our core.
  The stock core keeps frame records, and USING.md says poll-exact needs our core.

### 2.4 Options, versions, repeatability

- A committed option profile (`host/options-default.txt`) sets **every** core key explicitly (Vulkan, New 3DS on,
  right stick C-stick only, pointer timeout on, motion off, deadzone, both touchscreen sources, resolution factor
  1). fe2 answers the option-version query with 0, so unset keys would take the first listed value. Users override
  per key. The host answers no to the libretro microphone interface, so no permission prompt (a window) can appear.
- On every boot host.log gets the effective option set and the core's `library_version`. The host refuses a core
  that is neither the pinned stock build nor our pinned build unless `LAZ_ANY_CORE=1`.
- **Guest file I/O is asynchronous by default**: SD writes run on host threads (src hle/service/fs/file.cpp:240
  `RunAsync`; hle/kernel/hle_ipc.h:306-315 uses `std::async` unless `deterministic_async_operations`,
  settings.h:490, default false, no libretro option). Host load then leaks into guest timing, so exact repeats are
  not possible on the stock core. Our core adds options for `deterministic_async_operations`, `instant_debug_log`
  (settings.h:659) and a fixed start clock (`init_clock`/`init_time`, settings.h:503-504), all pinned on in our
  core's profile. The guest clock otherwise runs on guest time and starts from the host clock (spike 2).
- Repeat gates (identical shot hashes) run on our core; on the stock core they record the difference only.

### 2.5 The Python API (shape from libmgba-py, AzaharRPC.py and libretro.py's Session)

```python
from libazahar import Emulator, Buttons, Touch
with Emulator(app="build/testapp.3dsx", workdir="runs/a", sd_seed="fixtures/sd") as emu:
    emu.run_until(file="testapp/log.txt", text="ready", max_frames=12000)   # first run: the long boot
    emu.save_state("runs/field.state")                          # whole console plus an SD snapshot
with Emulator(app="build/testapp.3dsx", workdir="runs/b", state="runs/field.state") as emu:  # no boot
    r = emu.run(600, inputs=[(10, Buttons.A), (12, 0), (40, Touch(160, 120)), (42, Touch.up)],
                shots=[300, 600])                               # one native batch
    r.frames, r.stopped_by, r.shots[600].top                    # Path to top.png
    top, bottom = emu.screens()                                 # numpy arrays if numpy is installed, else bytes
    emu.memory.u32(addr); emu.memory.read(addr, 64)             # our core only (Phase G)
    emu.sd / "testapp" / "log.txt"                              # pathlib.Path into the instance's SD folder
```
`run_frame()`, `set_keys(raw=)` and `memory.u8/u32` keep libmgba-py's names (gba-toolkit's `tools/vsd_run.py`) for
one-off use; each is one round trip. Errors: `BootError`, `GuestError`, `HostTimeout`, `HostCrashed`,
`StateError`, `NeedsLazpyCore`; `guest_break` and `guest_exited` are stop reasons, not errors. `close()` always
reaps the worker. Type hints and docstrings on every public name; stdlib only, numpy and Pillow optional. Fixture
folders must not be named `sdmc` (`.gitignore` ignores that name).

### 2.6 Boot failure is detected

At 2126.2 `retro_load_game` checks the file early and returns false for a missing path or a non-3DS file (src
citra_libretro.cpp:521-553). `System::Load` failures inside `context_reset` go the SET_MESSAGE route (371-405,
473-474), and then `retro_run` uploads a NULL 0x0 frame (218-223). `azh_boot` gives `BootError` on any of the three:
load_game false, a SET_MESSAGE during `context_reset`, or a NULL frame on the first `retro_run`.

### 2.7 Our patched core

- **Build input:** Azahar's own `azahar-unified-source-2126.2.tar.xz` (43,224,348 bytes, a release asset with every
  submodule, made by `.ci/source.sh` with `git archive-all --force-submodules`; sha256 `85c8b56f...a4cd26` from the
  `.sha256sum` beside it). One pin in `core/PIN` (URL, sha256, tag, commit 219d743a), fetched fetch.sh-style into
  `dl/azahar-src/`, path-checked on unpack. No 1-2 GB recursive clone, no 37 commit pins.
- **Patches:** `core/patches/000N-*.patch`, applied with `patch -p1`. Files touched: `citra_libretro.cpp`,
  `core_settings.cpp`, `environment.cpp`, `libretro.osx.def`. What they do:
  - Memory: `lazpy_read_memory(vaddr, buf, len)` / `lazpy_write_memory(...)` check `IsValidVirtualAddress` for
    **every page** in [vaddr, vaddr+len) (ReadBlock fills unmapped pages with zeros and WriteBlock skips them, src
    memory.cpp:188-195, 247-253), then call `Memory::ReadBlock`/`WriteBlock` on the current process (memory.h:558,
    599, 673). Globals, heap, linear heap and VRAM, no map decoding. Called only between frames.
  - Both names (and `lazpy_movie_play` if 2.3's check passes) are added to `libretro.osx.def`. macOS links with
    `-exported_symbols_list` on that file (src citra_libretro/CMakeLists.txt:96), which lists exactly the 25
    `retro_*` symbols, so anything not listed is hidden from dlsym.
  - Options: deterministic async I/O, instant debug log, fixed start clock (2.4).
  - `retro_run` returns on a non-Success status (2.2).
  - The log filter goes up to Info plus `Debug_Emulated` (src citra_libretro.cpp:59 sets Debug, so every Debug line
    is formatted before our filter sees it).
  - `library_version` gets a `-lazpy.N` suffix (set in environment.cpp:270 from `g_build_fullname`).
  - Each patched file gets a "modified by libazahar-py on <date>" notice. Patch hunks stay GPLv2-or-later like the
    files they change, so the published core has one license; our repo stays GPLv3; the legal agent confirms.
- **Not patched:** the SET_MEMORY_MAPS table (built once from `context_reset`, citra_libretro.cpp:416, 474, when
  only code and stack exist; spike 2 saw only the stack page and VRAM) and HID's touch truncation (2.3).
- **Build:** `tools/build-core.sh` (rules.md 2's exception: Azahar's own CMake build on the exact pinned source,
  nice'd, in the background, never root) runs Azahar's CI commands for macOS (`libretro.yml:174-196`: `cmake
  -DENABLE_LIBRETRO=ON`, target `citra_libretro`) plus `-j`, `FETCHCONTENT_FULLY_DISCONNECTED=ON`, and
  `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` if CMake 4.3 refuses an old submodule. The output name is hard-set
  (CMakeLists.txt:32), so the script copies it to `build-core/azahar_lazpy_libretro.dylib`. Clean build 15-25 min
  quiet, 40-90 min at spike 2's load; detached; the main loop is woken on exit and sends a short gate agent.
- **Release:** the binary, Azahar's unified tarball **re-hosted unchanged**, our patches and the build script, side
  by side in the same GitHub release (GPLv2 §3(a)), plus `NOTICES.md` (the tarball holds every license text).
- **Updates:** a new tarball pin, `patch -p1` (fix any rejected hunk), rebuild, the full test batch: about 1 h
  machine, 0.3 h agent. Savestates check the program id and the git revision (src savestate.cpp:295-305), so states
  from one build may not load in another; whether stock states load into ours is checked in gate F, not assumed.

### 2.8 Many instances and speed (spike 2's facts)

- Real 3D scene, one instance, at load 27: 334-345 guest fps, 5.6-5.7x real time, about 1.4 cores, 0.5-0.8 GB.
  At load 68-96: 129 fps alone, 3 x 136-138 at once (about 3.2x one instance's total, so a 3D scene is not held to
  spike 1's idle-menu ceiling). CPU per guest frame was about 4.2-4.6 ms in every run. One `retro_run` is one guest
  vblank, so x real time = fps / 59.83.
- `libazahar.Pool(n)` runs jobs across n instances, each in its own folder (`workdir/sys/Azahar/sdmc`, `nand`,
  `shots/`, `host.log`, `host.map`), seeded from `sd_seed` by copy. Machine-wide cap: slot files under
  `~/Library/Caches/libazahar-py/slots/`, each held with `flock` by a live worker (the kernel drops it when the
  process dies). Default cap 3 (provisional until Phase E's table; env `LAZ_MAX_INSTANCES`). Workers run at
  `os.nice(10)`. The cap sees only our workers, so `Pool` warns when the load average is above twice the core count.
- Every speed table gives fps, CPU ms and wall ms per guest frame (CPU time leaves out Metal GPU time), and the load.
- The README quotes spike 2's 3D-field numbers with load and date; test-app numbers are labelled light (rules.md 7).

### 2.9 Savestates and booting from a state (first-class; Gen3D's ask)

- `azh_save_state` calls `retro_serialize_size`, which does the work: it first drains pending guest I/O by running
  the guest with presentation suppressed for up to 5 s (src citra_libretro.cpp:665-705), then serializes. A state
  "at frame N" is therefore at N + k vblanks; the host reports k (the test app's vblank count before and after) and
  USING.md says so. The size varies per call (628-630), so the buffer is allocated per call with one owner.
- SD files are not in the state, and the guest may hold them open, so `save_state` also copies the instance's SD
  folder to `<state>.sd/` by default; a state boot restores it into the new instance's folder first.
- State boot: `azh_boot(app, state)` loads the app (the core's program-id check is 0 for every `.3dsx`, so our state meta stores the app's sha256 and
  refuses another app; Phase 2 departure P4), completes the Vulkan setup and
  the first `retro_run`, loads the state, and counts frames from there as N + k. The windowed Qt app cannot load
  states without GUI focus, so this is something only we offer.

## 3. Phases

**Grouping (Guy 2026-11-12, after the split):** the ten units below are *steps* in four phases, and each phase
gets Guy's full loop before anything in it is built: phase plan, opus review 1, revision, opus review 2, revision,
then sonnet builds the steps, an opus as-built review per step, the main loop commits.
Phase 1 foundation = F1, A, B. Phase 2 control = C, D. Phase 3 scale and memory = E, F2, G. Phase 4 release = H, I.
The two loops add about 0.5 h per phase (about 2 h in all) to the step hours below.

Each step: sonnet builds from the approved phase plan, an opus review of the diff, the main loop commits (about
0.35 h of each step's hours). Every gate runs on this Mac, headless, as a command with a pass/fail answer.

| Order | Phase | Needs first | Hours | Gen3D need it serves |
|---|---|---|---|---|
| 1 | F1: core patches and build script; the first build launched detached | nothing | 1.0 | (6) memory, repeats |
| 1 | A: host library, fresh-clone build, boot | nothing | 1.25 | (1), (3) |
| 1 | B: test app from source | nothing | 1.0 | test guest for all |
| 2 | C: batches, input, touch, stop reasons | A, B | 2.0 | (2), (4) |
| 3 | D: Python layer, savestates, state boot | C (D may start from C's frozen header) | 2.25 | (1)-(4), state boot |
| 4 | E: many instances, then the speed table | D | 1.0 | (5) |
| 4 | F2: gate our core with the full test batch | F1's build, D | 0.75 | (6), repeats |
| 5 | G: memory reads and the watch list | F2 | 0.5 | (6) |
| 6 | H: docs | E, G | 0.5 | adapter brief |
| 7 | I: legal audit and release | H | 0.6 + Guy | public core |

**Total: about 10.9 h agent wall time**, plus about 1-2 h machine time (the first core build, detached) and
background test batches. Gen3D's needs (1)-(4) and state boot land by D; instances by E; memory by G.

**Phase A: the host library (1.25 h).** Delivers: `host/` split from fe2.c and fe3.c into small files (core loading
and the environment callback, Vulkan setup and readback, PNG and crop, the batch loop, the exported API, the
`azhost` main); the GL path removed; every Vulkan and core return value checked; Vulkan procs loaded once into one
table (no token-pasting `IFN`/`DFN` macros, C rule 8); readback buffers sized from the av info and reused; the log
callback thread-safe and level-filtered; the option profile, the version check and boot-failure detection (2.4, 2.6); the
mapped file; a Makefile building `build/libazhost.dylib` and `build/azhost` with `-Wall -Wextra -Werror`, and
`make check` adding `clang --analyze`. Brief notes: callbacks are the documented function-pointer exception
(C rule 9), functions under about 60 lines with about 2 assertions each. First step: move this repo's `dl/` files
into fetch.sh's layout (`dl/azahar/azahar_libretro.dylib`) and fix `docs/map/runners.md`.
Gate: a fresh clone in a temp folder with `dl/` and `vendor/` seeded by copy, `tools/fetch.sh` prints only "have"
lines, then `make check && make` with zero warnings; `build/azhost run <app> --frames 600 --shot 300,600` writes
`top` and `bottom` PNGs of the right sizes; while it runs, `lsappinfo list` has no entry for its pid; a missing file
and a non-3DS file both give `BootError`.

**Phase B: the test app (1 h).** Delivers: `testapp/` (libctru, devkitARM, GPLv3, ours; no system archives, own
glyphs, no shared font). It reads a seeded `sdmc/testapp/control.txt` **before its first frame**, so a seed alone
picks a mode: 2D pattern, a light citro3d scene, svcBreak at frame N, exit at frame N, write `ready` at frame N, a
slow "boot" of N frames (stands in for Gen3D's world build in state-boot tests). It draws corner markers on both
screens; every frame it writes one flushed line to `sdmc/testapp/log.txt` (vblank count, guest clock, held keys,
touch point, circle pad) and the same record through `svcOutputDebugString`; it keeps the record in a global and in
a heap block and logs both addresses at start. `make testapp` builds `build/testapp.3dsx` (ignored).
Gate: zero warnings; under `azhost run` the log has one line per frame, and shots show the markers at the exact
expected pixels on both screens (proves the 40 px offset and the readback).

**Phase C: batches, input, touch, stop reasons (2 h).** Delivers: `azh_run` with the input records, touch and
circle pad (2.3), the SD stop rule, the one-detector stop reasons, the heartbeat and the wall limit (2.2), SD
seeding. Pure-C unit tests (`make test-host`, no core): input records, the whole float32 touch chain for every
pixel, crop, the split-match and shrink cases of the stop matcher, the message-number detector, PNG.
Gate (test app, `tests/`, stock core): (a) planned button changes appear in the log on exactly the planned frames,
with a fixed, measured offset; (b) 20 touch points, including rows 63 and 126, reach the guest at the pixels the
float32 model predicts, and a shot with touch held has no cursor pixels; (c) `ready` stops the batch within K
frames; (d) the vblank count after N runs is N plus a constant (batches with a save excluded); (e) svcBreak gives
`guest_break` and the guest runs on; (f) exit makes `azhost` end with the guest-exited code and the reason in the
map; (g) other error numbers and the 3-in-one-run rule are covered by the unit tests, fed recorded messages.

**Phase D: the Python layer, savestates, state boot (2.25 h). Gen3D starts its adapter here.** Delivers:
`python/libazahar/` (2.5), the worker and mapped file (2.1), ctypes declarations checked against `azh_abi_layout()`
at import, typed errors, `pyproject.toml` for `pip install -e .`, the dylib found by `LAZ_HOST` or `build/`;
savestates and state boot with the SD snapshot (2.9); pytest integration tests on the test app, skipped with a
reason when the core or the app is missing; `docs/USING.md` with the Gen3D mapping table (each Gen3D mechanism and
its replacement call, the forced-mode seed pattern, the 4 touch rows, state boot, venv).
Gate (stock core): `pytest` passes the Phase C checks through Python; SIGSEGV sent to our own worker raises
`HostCrashed` within 1 s; SIGSTOP raises `HostTimeout` after T and leaves no process (checked by its pid); a
200,000-frame batch is not taken for a hang; **state boot**: run the slow-boot mode (N = 6000) to its end, save, run M more
recording shots and log lines; a new Emulator started from the state file runs M frames and reaches the same screen
(marker pixels exact) and the same vblank, keys and touch fields in its log lines (exact hashes are F2's job); the
state boot's wall time is under 10 % of the original boot's.

**Phase E: many instances, then the speed table (1 h).** Delivers: `Pool`, per-instance folders, the slot cap,
`nice`, the load warning; then a scaling script running 1, 2 and 3 instances of the test app's 3D scene for 60 s
each, printing guest fps (from the app's own vblank log), CPU and wall ms per guest frame, and the load; an
optional local row on a Gen3D 3D scene that agents may skip (needs a game on disk; its shots never committed). The
host's own share of a shot-free batch is measured (target under 5 %); cheap wins taken (zlib level 1, raw frames
when pixels are wanted, readback only on asked frames).
Gate: 3 instances give correct, separate logs and shots; a 4th waits for a slot under a cap of 3; killing one frees
its slot within 1 s; the table goes into `docs/research/` and sets the default cap.

**Phase F1: our core's patches and build script (1 h; starts at minute zero).** Delivers: `core/PIN`,
`core/patches/` and `tools/build-core.sh` (2.7), the notices; the 15-minute Movie-playback check (2.3) written into
the item; the first build launched detached. Gate: `build-core.sh` verifies the tarball's sha256, unpacks with path
checks, applies every patch with no rejects, and the build reaches the configure step's end (the full build's
result is F2's).

**Phase F2: gate our core (0.75 h; after the build exits and D).** Gate: `azahar_lazpy_libretro.dylib` exists;
`nm -gU` shows the 25 `retro_*` symbols plus both `lazpy_*`; host.log shows the `-lazpy` version; the Phase C and D
test batch passes on it, with stop reasons returned (no `_exit`); C(e)'s repeat and D's state boot give identical
shot hashes and log lines on two runs; the debug-text stop fires on the exact frame; whether a stock-core state
loads into ours is recorded.

**Phase G: memory reads and the watch list (0.5 h).** Delivers: `azh_read`/`azh_write` through the exported
functions, `emu.memory`, the per-frame watch list, `NeedsLazpyCore` on the stock core. Gate: on our core, the
record at both logged addresses (global and heap) reads back the values the log shows, frame by frame, for 600
frames, by `read` calls and by the watch list; a write changes the next logged line; a read that straddles the end
of a mapped region and a fully unmapped one both give a clean error; on the stock core every memory call raises
`NeedsLazpyCore`.

**Phase H: docs (0.5 h).** Delivers: README (what it is, honest status, measured numbers with load and date, install
in a venv, a 10-line example), `STATUS.md` (what works, what does not, what was considered and dropped: a fuller
memory map, savestate parsing, an upstream pull request), `docs/USING.md` finished, `docs/HOST-API.md`,
`NOTICES.md`, examples. Gate: a fresh clone and only the README's steps run the example on the test app; every
number in the README has a source row in `docs/research/`.

**Phase I: legal audit and release (0.6 h plus Guy).** Delivers: `release-legal-audit` over the repo, its history
and every asset; fixes; a release with `azahar_lazpy_libretro.dylib`, Azahar's unified tarball unchanged, our
patches and build script, `NOTICES.md`, and `testapp.3dsx` (ours). No prebuilt host dylib (`make` takes seconds),
no MoltenVK, no stock core. Then `fetch.sh` gets a sha256-pinned download of our core. Gate: the audit says
shippable for the repo, the core asset, the tarball and the notices; `git ls-files` shows no forbidden file
(rules.md 1); Guy says push.

## 4. Risks and what we do about them

1. **The first core build fails on this Mac** (CMake 4.3 against old submodule minimums; heavy load). Mitigation:
   launched at minute zero, detached, nice'd; Azahar's CI commands plus the policy flag; the stock core keeps A-E
   moving.
2. **Speed under shared load** (5.6x at load 27, 2.2x at load 68-96). Mitigation: CPU and wall ms per frame; the
   cap, `nice`, the load warning; no speed quoted without its load.
3. **Stock-core runs do not repeat exactly** (async guest I/O, host start clock). Mitigation: repeat gates on our
   core; stock gates compare fields, not hashes; USING.md says which core gives what.
4. **A ctypes struct out of step with the header.** Mitigation: `azh_abi_layout()` at import; inputs are flat int32.
5. **Core updates break patches or states.** Mitigation: one tarball pin; the full test batch per update; USING.md
   says states may not survive a core change.
6. **The GPL release of a modified core.** Mitigation: Azahar's tarball unchanged beside the binary, notices, the
   distinct name, the audit on every asset.
7. **devkitARM is needed for the test app.** On this Mac; elsewhere those tests skip, and releases attach the app.
8. **A state loaded right after the first frame may not restore the GPU side cleanly.** Mitigation: D's gate checks
   the screen; if it fails, the boot runs a few frames before loading and counts them in k.

## 5. Out of scope

Windows and Linux; audio output; any window; a fuller SET_MEMORY_MAPS table; savestate parsing; an upstream pull
request; patching HID's touch truncation; Azahar's RPC server and gdb stub (not in libretro builds); commercial
games in tests or docs; `.cia` installs; wireless; motion and camera; PyPI; a Python CLI; HOME; CI on GitHub runners
(first follow-up after the first push, about 0.5 h); Gen3D's adapter (Gen3D's work and ledger).

## 6. Hour-saving pass (revision 2)

| Existing thing | What it saves | Verdict |
|---|---|---|
| Azahar's unified source tarball (verified: release asset, 43 MB, sha256 file beside it) | Build input and GPL source in one: no clone, no 37 pins, no tarball work in I | use (0.5-0.75 h now and per update) |
| The core's own SET_MESSAGE for every guest failure | One detector, no log-line matcher | use |
| The core's `deterministic_async_operations`, `instant_debug_log`, `init_clock` settings | Repeats and an exact debug-text stop are option lines, not code | use (patch, a few lines each) |
| The core's Movie playback | Gen3D's poll-exact movies may run unchanged on our core | 15-min check in F1 |
| The core's `retro_serialize` and its drain | Savestates and state boot are a file write plus an SD copy | use |
| `prototype/fe2.c` and `fe3.c` | Core loading, Vulkan, readback, the frame-range input table | use, minus fe3's macros, button table and buffers |
| `tools/fetch.sh` (done) | Downloads, pins and headers | use; the core tarball fetch copies its pattern |
| A mapped file instead of `multiprocessing.shared_memory` | No resource tracker, crash-proof last message | use |
| Flat int32 input records and `azh_abi_layout()` | Less to guard, no compiler at test time | use |
| Cutting the Python CLI and the `otool` check | Code and a vacuous gate | use (about 0.25 h) |
| F1 at minute zero, detached | Build time leaves the critical path and the agent ledger | use |
| libretro.py, AzaharRPC.py, libmgba-py; nanoarch, RetroArch, Rust frontends | Ideas and names; the others need GL, a window or a surface | borrow names; rest rejected |

Tests: pure-C unit tests for pure functions; one background integration batch per phase; the full suite per batch.

## 7. Decisions from Guy (2026-11-12)

- We patch and build the core ourselves and publish it publicly "so it works for everyone"; no upstream pull request
  ("no need to submit a pull request, we edit the core to our needs"). Published core binaries ship with their
  corresponding source.
- The name `libazahar-py` is approved ("its informative and excct. so if its clear we use it"), subject to the legal
  agent's check at release.
- The core build: our build script may run Azahar's own CMake build on the exact pinned source, nice'd in the
  background; nothing else in a download is run (rules.md 2). `spirv-tools` is installed with Homebrew.

Open: none. For Guy: each release hosts an unchanged copy of Azahar's 43 MB source tarball (the GPL's source rule).

## 8. Changes from review 1 (summary)

All 3 blockers and 11 should-fix items taken; nice N1-N5, N7, N8 taken, N6 (CI) declined until the first push.
Review 2 corrected three of revision 1's source readings (svcBreak, SHUTDOWN, the export list): see section 9.

## 9. Changes from review 2

- B1 (stop reasons): done (2.2), verified: svcBreak gives status 14 via `LogException` (exception_handler.cpp:142),
  no SHUTDOWN is sent, `retro_run` loops on errors; revision 1's "svcBreak only logs" was wrong. Gates C(e)-(g).
- B2 (async I/O, the drain's k): done (2.4, 2.9): three options in our core, repeat gates there, k reported.
- B3 (export list, version, output name): done (2.7), verified (25 symbols in the `.def`, environment.cpp:270,
  CMakeLists.txt:32); `nm -gU` in gate F2.
- S1 (touch rows): done (2.3); the 4 rows recomputed in float32 here (63, 125, 126, 127); HID not patched.
- S2 (boot failure): done (2.6) with the three cases; verified at citra_libretro.cpp:521-553.
- S3 (poll-exact movies): done as a 15-min check in F1 (2.3); stock core keeps frame records.
- S4 (unmapped pages): done: every page checked; a straddling-read gate in G. Verified at memory.cpp:188-195.
- S5 (booking the build): done: detached build, the main loop is woken, a short gate agent (F2).
- S6 (estimates): done: C and D +0.5 h each, F as F1 + F2 (1.75 h), less the savings: 10.9 h.
- S7 (order): partly. Taken: the Python CLI cut; repeats and the debug-text check moved to F2. Declined: savestates
  stay in D and `Pool` in E, because Gen3D now asks for state boot first; E follows D at once.
- S8 (F at once): done: F1 runs at order 1, alongside A and B.
- S9 (otool proves nothing): done: `otool` cut; `lsappinfo` while live; the microphone interface refused.
- S10 (fetch layout): done: Phase A's first step; the gate asserts only "have" lines.
- S11 (README speed line): done (2.8).
- S12 (patch license, C hygiene): done: hunks GPLv2-or-later; one proc table, no macros, buffers from the av info.
- N1 (savestate citation): done: savestate.cpp:295-305 (program id and git revision), verified.
- N2 (boot timeout): done (2.2).
- N3 (split match, shrink): done (2.2, unit tests in C).
- N4 (wall ms per frame): done (2.8).
- N5 (log level in our core): done (2.7).
- N6 (build flags): done (2.7).
- N7 (cursor overflow): noted (2.3); covered by gate C(b).
- N8 (venv): done (2.1, USING.md).
- N9 (fixtures not named sdmc): done (2.5).
- N10 (quarantine reason): done: the reason for no prebuilt host dylib is now "make takes seconds".
- N11 (mapped file): done (2.1).
- N12 (flat int32 records): done (2.2).
- Hour-saving 1 (unified tarball): done (2.7), the asset verified. Not taken unchecked: "stock states load into
  ours" (the tarball's GIT-COMMIT holds `git describe` output, so the revision may differ); gate F2 records it.
- Gen3D's new need (state boot, from laz-12's notes): done (2.9, Phase D gate, test app's slow-boot mode).
