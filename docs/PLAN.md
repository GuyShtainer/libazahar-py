# libazahar-py: the whole-scope plan

Item laz-10, draft 1 (2026-11-12, opus). Reviews: laz-11, laz-12. After them, one item and one short plan per phase.
Inputs: `docs/research/` (spike 1, prior art, Gen3D's needs, the libretro.py probe), `prototype/fe2.c`,
`tools/fetch.sh`, and Azahar's libretro source (`src/citra_libretro/`, master and tag 2126.2, read 2026-11-12).
Parts marked **pending spike 2** have two branches; the right one is picked when
`docs/research/spike-2-real-scene.md` lands.

## 1. What we build, in one paragraph

A small C library, **the host** (`libazhost.dylib`, plus a thin `azhost` command-line program over it), loads the
Azahar libretro core, answers its Vulkan setup through MoltenVK with no window, and runs the guest unpaced. It takes
one batch per call ("run 600 frames with this input table, shoot frames 300 and 600, stop early if this text shows
up in this SD file, copy these memory words every frame") and does the whole batch natively: the frame loop, the
input feed, the GPU readback, the PNG encode, memory reads, the stop checks. A Python package (`libazahar`) gives
each emulator instance its own worker process, which loads the host through ctypes; the user's script talks to the
workers and gets plain results (frame count, why it stopped, screenshot paths or pixel arrays, bytes read). A tiny
homebrew app built here from source is the test guest, so no test needs a commercial game. `tools/fetch.sh`
(done) brings the core, MoltenVK and the headers.

## 2. Decisions

### 2.1 The Python route: our own C host library, a thin ctypes layer, batches only

**libretro.py is not the host** (`docs/research/libretro-py-probe.md`, v0.12.0): it has no Vulkan context, its
Vulkan negotiation answer is a stub that returns false, so with Vulkan the core fails to load; with the Software
renderer it boots at 20 fps. Its loop calls `retro_run` from Python every frame (about 90 µs per frame on a trivial
core, 27 % on top of spike 1's idle-menu frame). We borrow its `Session` API shape (core, game, options, paths,
an input source that takes per-frame lists, `serialize`/`unserialize`), its environment-call table
(`drivers/environment/default.py`) as a checklist for our environment callback, and its memory-map decoding (MIT,
ported with its notice).

**C, not Rust.** The libretro and Vulkan interfaces are C headers, fe2.c already works, and the host is about
1500 lines of glue. Rust would add a toolchain, bindgen and unsafe blocks around every callback for no speed gain.
Rust comes in only if a later phase shows a C problem it would solve.

**One process per instance, never threads.** Azahar's libretro glue drives one process-wide emulator
(`Core::System::GetInstance()` throughout `citra_libretro.cpp`), so a process holds one core.

**A ctypes library in a worker process, not a wire protocol.** The host exports a C API (2.2). Python's
`Emulator` starts a worker (`python -I -m libazahar._worker`, stdlib `multiprocessing` with the spawn method), and
the worker loads `libazhost.dylib` with ctypes and makes one ctypes call per batch. Why this split:
- No request parser in C: the boundary is C function signatures, and the user-to-worker link is Python to Python
  (pickled calls over a `multiprocessing` pipe, stdlib, free).
- A guest crash or hang never kills the user's script: the parent sees the worker die, or kills its own worker
  on a wall timeout (a hung `retro_run` cannot be interrupted inside its own process).
- Pixels and memory come back as buffers the worker fills in place, and numpy can wrap them with no copy.
- No compiled Python extension: `pip install -e .` stays pure Python; the dylib is built by `make`.
The cost, one pipe round trip per batch, is nothing next to a batch of frames. Per-frame Python callbacks never
exist: the input table, the shot list, the stop rule and the memory watch list go into the batch call.

### 2.2 The C/Python boundary: what the host library exports

| C function (all return 0 or a negative error code; `azh_error()` gives the text) | What it does | From |
|---|---|---|
| `azh_open(core_path, sysdir, logpath)` / `azh_close()` | load the core, set the folders | libretro |
| `azh_set_option(key, value)` | a core option, before boot | libretro |
| `azh_boot(app_path)` | load the app; set up Vulkan through MoltenVK (or Software) | libretro |
| `azh_run(const azh_batch *in, azh_result *out)` | the batch: up to N frames, input table, shot list, stop rule, watch list, wall timeout | new |
| `azh_shot(screens, format, path_or_buffer)` | shoot the current frame: top 400x240, bottom 320x240, or both; PNG to a path or raw RGBA into a buffer | RPC TakeScreenshot / ReadScreenshot |
| `azh_read(addr, len, buf)` / `azh_write(addr, len, buf)` | guest memory by virtual address (pending spike 2) | RPC ReadMemory / WriteMemory |
| `azh_save_state(path)` / `azh_load_state(path)` | savestate to and from a file | RPC SaveState / LoadState |
| `azh_set_input(const azh_input *held)` | set the held state now (held until changed) | RPC SetInput |
| `azh_stats(azh_stats *out)` | frames run, wall time, frames per second, peak memory | RPC GetPerfStats |

`azh_batch` holds plain arrays with their lengths: input records (frame, buttons mask, touch x, touch y, touch
down, circle x, circle y), each setting the held state from that frame on (movie semantics, the same as RPC
SetInput's "held until cleared", so Gen3D compiles its CTM movies straight into it); shot frames with a screens and
format choice; the stop rule (an SD file path, a plain text to find in its new bytes, check every K frames); watch
addresses with a result buffer of frames x words. `azh_result` says frames run and why it stopped (frames, text,
timeout, guest error). The host crops natively: the core's default layout puts top at (0,0) and bottom at (40,240)
in a 400x480 frame; the test app proves the offsets. The `azhost` program calls the same functions from command
line arguments (`azhost run app.3dsx --frames 600 --shot 300,600 --opt key=value`), for shell use and debugging.

### 2.3 The Python API (shape from libmgba-py, AzaharRPC.py and libretro.py's Session)

```python
from libazahar import Emulator, Buttons, Touch
with Emulator(app="build/testapp.3dsx", workdir="runs/a", sd_seed="fixtures/sd",
              options={"is_new_3ds": "disabled"}) as emu:      # starts its worker, boots
    r = emu.run(600, inputs=[(10, Buttons.A), (12, 0), (40, Touch(160, 120)), (42, Touch.up)],
                shots=[300, 600])                               # one native batch
    r.frames, r.stopped_by, r.shots[600].top                    # Path to top.png
    emu.run_until(file="testapp/log.txt", text="ready", max_frames=6000)   # path inside the SD folder
    top, bottom = emu.screens()                                 # numpy arrays if numpy is installed, else bytes
    emu.memory.u32(0x0800_0000); emu.memory.read(addr, 64)      # pending spike 2
    emu.save_state("runs/a/s1.state"); emu.load_state("runs/a/s1.state")
    emu.sd / "testapp" / "log.txt"                              # pathlib.Path into the instance's SD folder
```
`run_frame()`, `set_keys(raw=)` and `memory.u8/u32` exist with libmgba-py's names (gba-toolkit's
`tools/vsd_run.py` uses them) for one-off and interactive use; each is one round trip, so never the hot path.
Errors are typed (`BootError`, `HostCrashed`, `HostTimeout`, `UnmappedAddress`); `close()` always reaps the
worker. Type hints and docstrings on every public name; stdlib only, numpy and Pillow optional.

### 2.4 Many instances: one process each, in its own folder, capped machine-wide

`libazahar.Pool(n)` runs jobs across n instances. Each gets its own folder (`workdir/sys/Azahar/sdmc`, `nand`,
`shots/`, `host.log`), seeded from `sd_seed` by copy. Spike 1: one instance used about 1.4 cores and 1.2 GB; three
at once shared one throughput ceiling (3600 frames/s total against 3075 for one, on a busy machine). The machine is
shared with other sessions' emulators, so:
- A machine-wide cap: slot files under `~/Library/Caches/libazahar-py/slots/`, each held with `flock` by a running
  worker. The kernel drops the lock when a process dies, so a crash never leaks a slot and nobody kills anything.
  Default cap 3 (env `LAZ_MAX_INSTANCES`); a worker that finds no free slot waits up to a limit, then fails clearly.
- Workers run at lower priority (`os.nice(10)`) by default, so foreground work and other sessions win.
- The default pool size is the measured knee from Phase E. **Pending spike 2**: if three instances on a real 3D
  scene give more than about 1.5x one instance, the default is 3; if they are capped near one instance's
  throughput, the default is 2 and Phase G looks for the shared limit (the GPU queue through MoltenVK, memory
  bandwidth, or the disk shader cache).

### 2.5 Third-party files

- **Fetched, already done:** `tools/fetch.sh` (committed 9a3977b) fetches the core 2126.2, MoltenVK 1.4.2,
  `libretro.h` and `libretro_vulkan.h` (RetroArch commit 807245dd, MIT) and Vulkan-Headers v1.4.368 into `dl/` and
  `vendor/` (both ignored), each sha256-pinned and checked before unpacking. So a fresh clone builds after one
  `tools/fetch.sh`. Its caveat: GitHub tag-archive tarballs (the Vulkan-Headers one) are not promised to stay
  byte-identical; on a mismatch, re-pin after checking the contents. Updating the core is a pin change plus a full
  test batch.
- The OpenGL path in fe2.c is dropped: this core never offers OpenGL on macOS. The Software renderer stays as the
  fallback that needs no MoltenVK.

### 2.6 Where Gen3D ends and this repo begins

This repo ends at the Python API, its docs and a generic example (a guest driven by SD control files, run until a
log line, judged by screenshots). Gen3D owns its adapter: the azctl replacement, compiling CTM movies into input
tables, recalibrating its picture judges to the core's image, the parity run against its Qt verdicts. Those hours go
in Gen3D's ledger. This repo ships a table mapping each Gen3D mechanism to the API call that replaces it
(`docs/USING.md`), so the adapter is a brief, not research.

## 3. Phases

Each phase: an opus phase plan (short), sonnet builds from it, an opus review of the diff, the main loop commits.
Hours include that overhead. Every gate runs on this Mac, headless, and is a command with a pass/fail answer.
Gen3D's needs map to phases: (1) boot + SD seed and read-back: A and C; (2) frame-exact buttons then touch: C;
(3) both screens cropped: A and C; (4) run until N frames or a log line: C; (5) many instances: E; (6) memory: F.

### Phase A: the host library builds from a fresh clone and boots an app (5 h, sonnet build; opus plan and review)
Delivers: `host/` split from fe2.c into small files (core loading and the environment callback, Vulkan setup and
readback, PNG writing and cropping, the batch loop, the exported API, the `azhost` main), the GL path removed,
every Vulkan and core return value checked, the readback buffer and command pool made once and reused (no
allocation per shot), functions under about 60 lines; the environment callback checked against libretro.py's table
and unknown calls logged once; a Makefile building `build/libazhost.dylib` and `build/azhost` with
`-Wall -Wextra -Werror`, and `make check` that adds `clang --analyze`.
Gate: in a fresh clone in a temp folder, `tools/fetch.sh && make check && make` passes with zero warnings, and
`build/azhost run <app> --frames 600 --shot 300,600` boots headless and writes `top` and `bottom` PNGs of the right
sizes; no window appears (no Dock icon; the process makes no window-server connection, checked with `lsof`).

### Phase B: the test app, built from source (5 h, sonnet build; opus plan and review; runs alongside A)
Delivers: `testapp/` (libctru, devkitARM, GPLv3, ours): draws a fixed pattern with corner markers on both screens
(so cropping is checkable), counts vblanks, and every frame writes to `sdmc/testapp/log.txt` one line with the
vblank count, the guest tick clock, the held buttons, the touch point and the circle pad. It keeps the same values
in a global struct and logs the struct's address once at start (for the memory check). It reads
`sdmc/testapp/control.txt` (switch to a light 3D scene, hang on purpose, crash on purpose, write `ready`). The
citro3d scene gives a repeatable load for speed numbers. `make testapp` builds `build/testapp.3dsx` (ignored; the
release attaches it).
Gate: `make testapp` builds with zero warnings; booted under `azhost run`, the log has one line per frame and the
shots show the markers at the expected pixels.

### Phase C: batches, input, touch, stop rules, SD seeding (7 h, sonnet build; opus plan and review)
Delivers: `azh_run` with the native input table; touch through the libretro pointer device (the host turns a
bottom-screen pixel into the pointer's -0x7fff..0x7fff range over the 400x480 frame); the circle pad through the
left analog stick; stop checks on an SD file every K frames (default 30) with a plain substring match on the new
bytes only; the wall timeout; the SD folder seeded before boot. Core options pinned by default for repeatability:
the right stick as C-stick only (the default routes it to the touch pointer), L3 and R3 never sent (the core binds
them to screen swap and the pointer). Pure-C unit tests (`make test-host`, no core needed) for the input table,
the pointer conversion, cropping, the stop matcher and the PNG writer.
Gate (all on the test app, a script in `tests/`): (a) a button table gives log lines whose button field changes on
exactly the planned frames, with a fixed, measured offset; (b) 20 touch points land on the expected bottom-screen
pixels within 1 px; (c) `ready` stops the batch within K frames of the guest writing it; (d) one `retro_run` is one
guest frame: the vblank count after N runs equals N plus a constant; (e) the same table run twice gives identical
shot hashes, or the difference is written down as a finding.

### Phase D: the Python layer, v1 (6 h, sonnet build; opus plan and review). Gen3D can start its adapter here
Delivers: `python/libazahar/` with `Emulator` (2.3), the worker, the ctypes declarations of 2.2 (one file, checked
against the C header by a test that compiles a tiny C program printing struct sizes and offsets), `Buttons`/`Touch`,
typed errors, `pyproject.toml` for `pip install -e .`, the dylib found by `LAZ_HOST` or the repo's `build/`; pytest
integration tests on the test app (skipped with a clear reason when the core or the app is missing);
`docs/USING.md` with the Gen3D mapping table.
Gate: `pytest` passes the Phase C checks again through Python; the app's crash command raises `HostCrashed` in under
1 s; its hang command raises `HostTimeout` and leaves no process behind (checked by the worker's own pid);
`python3 -I -m libazahar run ...` works as a CLI.

### Phase E: many instances (4 h, sonnet build; opus plan and review)
Delivers: `libazahar.Pool`, per-instance folders, the `flock` slot cap, `nice`, a scaling script that runs 1, 2 and
3 instances of the test app's 3D scene for 60 s each and prints guest frames per wall second (from the app's own
vblank log, not `retro_run` counts) with the load average beside it.
Gate: 3 instances in parallel each produce correct, separate SD logs and shots; a 4th waits for a slot under a cap
of 3; killing one worker frees its slot within 1 s; the scaling table goes into `docs/research/` and sets the
default pool size (2.4).

### Phase F: memory reads and savestates (4 h if the memory map works, 6 h if not; **pending spike 2**)
Savestates are in the core: `retro_serialize` first drains pending guest I/O (up to 5 s); the host writes the state
to a file. Gate: save at frame N, run M frames, load, run M again: identical log lines and shots.
Memory. Source reading (2126.2 and master): the core builds its memory map once, inside `retro_load_game`, from the
current process's heap, linear heap and VRAM regions, and calls `SET_MEMORY_MAPS` only if that list is not empty.
A .3dsx asks for its heap later, in its own start-up code, so the list may well be empty then, which would explain
the probe's "never sends SET_MEMORY_MAPS". Spike 2 tests it on a running game.
- Branch 1, **the map arrives and covers the heap**: the host keeps the core's table, decodes addresses like
  libretro.py does, reads or writes only inside a listed region (else `UnmappedAddress`), and copies watched words
  every frame inside the batch. Gate: the test app's struct, at its logged address, reads back the values the log
  shows, frame by frame, for 600 frames.
- Branch 2, **no map or a stale one**: (a) a small upstream pull request to Azahar that rebuilds the map when the
  process's memory layout changes (a few lines in `citra_libretro.cpp`; we pick it up when a release carries it);
  (b) until then memory is out of the tool and users log values to SD (the test app shows the pattern); building a
  patched core ourselves stays out of scope. Gate: the branch chosen and written in STATUS; `azh_read` returns the
  unmapped error cleanly; the pull request opened only with Guy's yes.

### Phase G: speed pass on real scenes (4 h, sonnet build; opus plan and review; **pending spike 2**)
Delivers: measurements on the test app's 3D scene and, locally, on a Gen3D 3D scene (Gen3D's .3dsx, never
committed) against the guest's own clock; a profile of where host time goes (readback, PNG, input, the core); the
cheap wins (zlib level 1 for PNGs, raw frames when the caller wants pixels, readback only on asked frames, no
per-frame syscalls); the core options that matter (resolution factor 1, shader JIT, disk shader cache).
Gate: a table of guest frames per wall second for 1 and 3 instances on both scenes, with load averages; the host's
own share of a shot-free batch under 5 % of wall time. If a real scene runs well above real time the defaults stand;
if it is near real time the README says so plainly and quotes that number.

### Phase H: docs and the public repo (3 h, sonnet writes; opus reviews)
Delivers: README (what it is, honest status, what is measured and on what, install, a 10-line example),
`STATUS.md` (what works, what does not, the spike 2 branch taken), `docs/USING.md` finished, `docs/HOST-API.md`
(the C API), license notices for any ported libretro.py code, examples.
Gate: a fresh clone followed by only the README's steps runs the example on the test app; every number in the
README has a source row in `docs/research/`.

### Phase I: legal audit and the GitHub release (2 h plus Guy)
Delivers: `release-legal-audit` over the repo, its history and the release assets; fixes; a GitHub release with the
source, a prebuilt `libazhost.dylib` and `azhost` for macOS arm64 and `testapp.3dsx` (all our GPLv3 code); no core,
no MoltenVK.
Gate: the audit says shippable; `git ls-files` shows no forbidden file (rules.md 1); Guy says push.

**Total:** about 40 h with branch 1 of Phase F, 42 h with branch 2 (the plan and its reviews, laz-10 to laz-12,
not included; the fetch script already done). Order: A and B in parallel, then C, D (Gen3D starts), E, F, G, H,
I. F moves before E if Gen3D asks for memory first; G can run any time after E. Gen3D's own estimate of 40-49 h
included its adapter and parity run, which are booked in Gen3D.

## 4. Risks and what we do about them

1. **Memory reads may not work in the stock core** (the map is built once, at load, likely before a .3dsx has a
   heap). Mitigation: spike 2 decides; Phase F branch 2; Gen3D's main runner barely needs RAM (its needs doc), and
   app-side SD logs cover the rest.
2. **Real-scene speed and scaling are unknown** (spike 1's ~50x was an idle menu; rules.md 7). Mitigation: no speed
   is quoted until Phase G measures it against the guest clock; the pool default comes from measurement; the
   machine-wide cap protects other sessions either way.
3. **Touch fidelity and a cursor in screenshots.** The core maps the pointer through the screen layout and draws a
   cursor into the frame (its Vulkan renderer has a cursor pass). Mitigation: Phase C gate (b) checks placement; if
   the cursor shows in shots, try the core's pointer-timeout option, else shoot on frames with no touch held, else
   mask it; record which.
4. **Repeatability.** The guest clock may follow the host's real clock (the core has no fixed-clock option) and
   shaders may compile asynchronously. Mitigation: gate C(e) measures it; Gen3D's judges have tolerances; if exact
   repeats are needed, look for a clock pin in the core's settings or ask upstream.
5. **A ctypes struct out of step with the C header** gives silent garbage. Mitigation: the Phase D layout test;
   plain fixed-width fields only, no unions, no pointers to pointers.
6. **Core updates break things** (2126.2 now, release candidates weekly). Mitigation: pinned by sha256; an update
   is a deliberate change gated by the full test batch.
7. **Vulkan readback correctness** (fe2.c's barrier was never run under a validation layer). Mitigation: Phase A
   checks the test pattern pixels exactly; a validation-layer run only if it is cheap to fetch.
8. **Shared machine.** Mitigation: the slot cap, `nice`, measurements print the load average, and no step ever
   kills a process it did not start.
9. **devkitARM needed for the test app.** It is on this Mac; elsewhere those tests skip with a reason, and the
   release attaches a prebuilt `testapp.3dsx`.

## 5. Out of scope

Windows and Linux builds (macOS-only calls stay in one file, so a later port stays possible); audio output
(samples are counted, not played or saved); a GUI or any window; building the Azahar core ourselves; Azahar's RPC
server (not in libretro builds); commercial games in tests or docs; `.cia` install flows; the 3DS's wireless and
netplay; motion and camera input; a PyPI release (v1 installs from the repo); Gen3D's adapter (Gen3D's work).

## 6. Hour-saving pass

| Existing thing | What it saves | Verdict |
|---|---|---|
| `prototype/fe2.c` | Core loading, environment answers and the Vulkan negotiation already work: Phase A is a cleanup, not a build | use (about 6 h) |
| `tools/fetch.sh` | Downloads, pins and headers are done and tested | use (2 h, already spent) |
| libretro.py (MIT), probed | Session API shape, the environment-call checklist, memory-map decoding; it cannot host this core | borrow (1-2 h) |
| AzaharRPC.py and the RPC request set (GPLv2+) | Request names and meanings (held input, touch in 320x240, screenshot formats, savestates) | borrow semantics, no code (1 h) |
| libmgba-py's API names (`run_frame`, `set_keys(raw=)`, `memory.u8.raw_read`) | Names Guy's sibling tools already use | borrow names (0.5 h, less to learn) |
| ctypes in a worker instead of a pipe protocol | No request parser or its tests in C | use (about 3 h) |
| The core's own `retro_serialize` | Savestates are a file write, not a feature | use (about 2 h) |
| Gen3D's SD control files and log judges | Stop rules are a substring check, not a new protocol | use the pattern; the test app copies it |
| RetroArch as the host | Full frontend that needs a display surface for Vulkan; not checked further | rejected |
| Rust libretro frontends (retro-rs and similar) | No Vulkan HW-core support found, and a new toolchain | rejected |

Cheaper tests: pure-C unit tests for every pure function (no core, milliseconds); one integration batch per phase
on the test app, launched in the background; the full suite once per large batch (Guy's testing rule).

## 7. Questions for Guy

None block Phase A or B. Two later ones:
- Phase F branch 2: may we open a pull request on Azahar's GitHub (under your account) to refresh the memory map?
- Phase I: the public name `libazahar-py` names the Azahar project (not a Nintendo mark); the legal agent checks it
  at release, and Azahar's maintainers might prefer a heads-up. Fine as is?
