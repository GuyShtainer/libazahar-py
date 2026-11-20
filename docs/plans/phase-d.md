# Phase 2, step D: the Python layer, savestates, state boot (item laz-220)

Opus step plan, 2026-11-12, **revision 2 (after `docs/reviews/phase-2-review-1.md` and `phase-2-review-2.md`).
Nobody builds from it until the main loop has checked the review-2 fixes and launches the step.** Index:
`docs/plans/phase-2.md`. For one sonnet builder in its own git worktree (`../libazahar-py-d`, branch `step-d`, made
by the main loop at step C's checkpoint C1 commit). It refines `docs/PLAN.md` sections 2.1, 2.5, 2.8 (the worker's
`nice`) and 2.9 and the "Phase D" paragraph of section 3; where they disagree on a goal, PLAN.md wins and the builder
stops and reports, **except for phase-2.md section 5's approved departures** (P2: `LAZ_REQUIRE_EMULATOR`; P3: the
worker's start line; P4: the app identity in a state; P6: `HostError`), which this brief follows without stopping.

MAIN = `~/VSCodeProjects/3ds-toolkit/projects/libazahar-py` (the main checkout: read and copy only).

Builder reads first, in this order: `docs/map/rules.md`; PLAN.md 2.1, 2.2, 2.3, 2.5, 2.9 and section 3's Phase D
paragraph; `docs/plans/phase-2.md` section 5 (the departures); `docs/plans/phase-c.md` sections 2, 3 and 8 (the
frozen headers, the input facts, the gate scenarios D reruns through Python); `docs/research/gen3d-harness-needs.md`
(USING.md's mapping table); `~/.claude/python-golden-rules.md`, `~/.claude/c-golden-rules.md`. Then the code at the
C1 commit: `host/azhost.h`, `host/azh_internal.h`, `host/azh_pure.h`, `host/state.c`, `host/statemeta.c`,
`host/run.c` (the four functions D links against), `host/api.c` (`azh_boot`'s state branch),
`tests/check_testapp.py` (its `read_png_rgba`). After the D3 resume, also `tests/checks_c.py` and
`tests/testapp_log.py` as merged.

## 1. Goal and gate

Goal: `import libazahar` gives the API of PLAN.md 2.5: an `Emulator` that runs one host instance in its own worker
process (ctypes over `build/libazhost.dylib`), reads the mapped file `host.map` without a round trip, raises typed
errors, saves and loads states with an SD snapshot and the app's identity, and boots straight from a state;
`pip install -e .` works in a venv; `docs/USING.md` tells Gen3D how to move its harness over.

Gate (PLAN.md section 3, "Phase D"), headless, this Mac, stock core, test app only:
1. `make check && make && make test-host` clean (D adds `test_statemeta.c`'s checks).
2. `LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python` (run from the repo root; pytest is in
   the user site on this Mac, so no `-I` here) reports all passed, **0 skipped, 0 failed**, slow tests included (or
   the same tests in the parts of section 6 step 3, each 0 skipped). It covers: C's checks (a)-(f) through Python;
   SIGSEGV to our own worker raises `HostCrashed` within 1 s (the delay printed); SIGSTOP during a call made with
   `timeout=3` raises `HostTimeout` between 2.8 and 6 s after the stop (printed), and `os.kill(pid, 0)` then raises
   `ProcessLookupError`; a 200,000-frame batch returns with `stopped_by == "frames"`; a state for another app is
   refused; the state-boot test of section 8 (same markers, same `v k tx ty td cx cy` fields, restored log bytes,
   state boot under 10 % of the boot's wall time; `t_core_start`, `t_boot`, `t_state`, both ratios and the restore
   step times printed).
3. `python3 -m venv runs/d-venv && runs/d-venv/bin/pip install -e .` (the one network step: pip fetches setuptools
   77 or later into its build environment), then `runs/d-venv/bin/python -I -c "import libazahar, sys;
   print(libazahar.__version__)"` prints `0.1.0.dev0`. pytest is not needed in that venv.
4. Once, a planted red: run the state-boot test with `LAZ_TEST_PLANT_RED=1` (it compares against the frame after the
   real one) and see it fail; then it passes again. Quote both.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`)

- `retro_serialize_size` first drains pending async guest work: `RunLoop` with presentation suppressed until no async
  operation is pending, up to 5 s, then `SaveStateBuffer`; it returns 0 on a drain timeout, a non-Success status or an
  exception. `retro_serialize(data, size)` copies the buffer made by the last `retro_serialize_size` and frees it; it
  fails if none or if `size` is too small. `retro_unserialize` drains the same way, then `LoadStateBuffer`
  (SRC citra_libretro/citra_libretro.cpp:649-738). So a drain through `retro_serialize_size` is a full serialize: it
  costs about what a save costs (section 3.3 times it). No cheaper drain exists on the stock core; do not look for one.
- During the drain the window's `SwapBuffers` returns early (no frame is submitted) but `PollEvents`, and so the
  host's `input_poll_cb`, still runs at every guest VBlank (SRC citra_libretro/emu_window/libretro_window.cpp:68-71,
  194-204; video_core/renderer_base.cpp:43-48). So **k = the change in `azh__vblanks_total()` across
  `retro_serialize_size`**. k is often 0 (nothing pending) and is at most about 5 s of guest time.
- `LoadStateBuffer` refuses a state from another program id (core/savestate.cpp:296-299) or another build revision
  (:300-306); states are zstd-compressed (:253). **For a `.3dsx` the program id is always 0**: the 3DSX loader has
  no `ReadProgramId` (the base returns `ErrorNotImplemented`, core/loader/loader.h:219-221; core.cpp:515-519), so
  the core's check never refuses one homebrew's state in another. Hence the app identity in the meta (P4). A state may
  not survive a core change (PLAN risk 5).
- Guest files open at save time survive: `IOFile` serializes its path with placeholders (`%CITRA_USER_SDMC%`,
  `%CITRA_ROM_FILE%`), open mode, flags and position, and reopens on load (SRC common/file_util.h:80-104, 667-682;
  common/file_util.cpp:1058-1065); SD files are opened `r+b` (core/file_sys/archive_sdmc.cpp:105). So a state reopens
  the new instance's own SD files, which must hold the snapshot's bytes before the load; it reopens the app's RomFS
  from the new app path; and NAND files reopen from the new instance's NAND, which is not snapshotted.
- The emulated SD card is `<sysdir>/Azahar/sdmc/`; the test app's log is `testapp/log.txt` in it, truncated by the app
  at start with `FSFILE_SetSize(0)` (phase-b "3. The app"). On the stock core OpenFile, SetSize and Close run
  **async** (fs_user.cpp:70, file.cpp:288, 317; phase-b "2. Facts"), while writes are synchronous (file.cpp:200-217).
  So the fresh app's warm-up frame can leave a truncation pending; the restore drains first, then replaces the SD,
  then unserializes (section 3.3). Never "optimise" the drain away.
- `azh_boot` runs no `retro_run` (phase-2.md A4); `frame_total` counts every `retro_run` since boot, so the state
  boot's warm-up frame counts until section 3.3 step 7 replaces the counters. `azh__run_one_frame` makes A's
  first-frame boot check (phase-c.md 3.6), so the warm-up frame is where a broken Vulkan setup shows, as `AZH_E_BOOT`.
- Phase A's `core.c` already loads the three serialize symbols (all 25, phase-2.md A14); D adds no `dlsym`.
- CommonCrypto's `CC_SHA256_Init/Update/Final` are in libSystem (`<CommonCrypto/CommonDigest.h>`), no extra link flag.
- This Mac (2026-11-12): python3 3.14.0; pytest 9.2.0 and numpy 2.5.0 in the user site (`~/Library/Python/3.14`),
  so `python3 -I` cannot import pytest; setuptools is not importable under `-I`; Pillow absent. `-I` implies `-P`, so
  a script's own folder is not on `sys.path`. A worker started with `-m libazahar._worker` under `-I` cannot import an
  uninstalled package, so section 4.2 starts it with an explicit package root (P3).
- `multiprocessing.Pipe()` on POSIX returns two `Connection`s over a `socketpair`; `Connection(fd)` wraps an inherited
  descriptor; `conn.poll(t)`, `send`, `recv` (pickle) are stdlib (Python docs, multiprocessing.connection).
- `license = "GPL-3.0-or-later"` as an SPDX string in `[project]` needs setuptools 77 or later (PEP 639 support).
- A's `vk.c` sets `MVK_CONFIG_LOG_LEVEL=1` unless it is set (step A as built); the worker passes the environment
  through.

## 3. Savestates and state boot in C (`host/state.c`, `host/statemeta.c`; stubs from C1, D fills them)

### 3.1 Files of a state at `<path>`

| File | Content | Written |
|---|---|---|
| `<path>` | the core's buffer as returned by `retro_serialize` | `<path>.tmp`, `fsync`, `rename` |
| `<path>.sd/` | a copy of the instance's whole SD folder at the save | `<path>.sd.tmp/`, then renamed (an old `<path>.sd/` is first renamed to `<path>.sd.old/` and removed after) |
| `<path>.meta` | `key=value` lines: `abi=2`, `k=`, `frame_total=`, `vblanks_total=`, `created=` (Unix seconds), `core_version=`, `app=` (the path, for messages), `app_sha256=` (64 lowercase hex digits) | last, `<path>.meta.tmp` then `rename`, then `fsync` by path; its presence means the state is complete |

`statemeta.c` is pure (`<stdint.h>`, `<string.h>`, `<stdio.h>`, `<stdlib.h>` only): format into a buffer, parse a
buffer (every key required once; unknown keys rejected; integers by `strtoll` with end and range checks; text values
without newlines, never truncated, refused if too long; `app_sha256` exactly 64 hex digits), and write/read with
checked I/O. Errors are `AZH_E_SAVESTATE` with a reason in `azh_error()`. `state.c` hashes the app file with
CommonCrypto in a bounded loop of 64 KiB reads (`azh__app_sha256(path, hex65)`, a file-static helper).

### 3.2 Save: `azh__state_save(path, k_out)` (called by `azh_save_state` after a batch, never inside one)

0. `unlink(<path>.meta)` (missing is fine), so a crash in the steps below never leaves an old meta beside new files.
1. `v0 = azh__vblanks_total()`; `size = retro_serialize_size()`; `k = azh__vblanks_total() - v0`. Size 0:
   `AZH_E_SAVESTATE` "the core could not save (drain timeout or error; see host.log)".
2. `buf = malloc(size)` (checked; one owner; freed on every path through one small cleanup function, no goto);
   `retro_serialize(buf, size)` must return true.
3. Write `<path>.tmp` (`open` `O_WRONLY|O_CREAT|O_TRUNC`, 0644, a bounded full-write loop, `fsync`, `close`), `rename`.
4. SD snapshot: remove a stale `<path>.sd.tmp/` (`azh__clear_tree` then `rmdir`), `azh__copy_tree(sd_root,
   <path>.sd.tmp)` (C's `fts` walk with `copyfile(COPYFILE_CLONE)` per file, so near-constant time on APFS), swap in
   as section 3.1.
5. Counters: `frame_total += k` (so the saving instance and a state boot number frames the same way: a state "at
   frame N" is at N + k, PLAN 2.9); `vblanks_total` already includes the k polls. `azh__counters_set`.
6. Meta with the new `frame_total`, the `vblanks_total`, k, the core version (`azh_stats`), the app path
   (`azh__state_note_app`) and its sha256, `created`; written as section 3.1. `*k_out = k`. One `host.log` line:
   `state save k=<k> bytes=<size> serialize_ms= write_ms= sd_ms= sha_ms=`.

### 3.3 Restore (shared by state boot and `azh_load_state`)

Each step's wall time (`CLOCK_MONOTONIC`) is kept, and one `host.log` line at the end gives them:
`state load meta_ms= sha_ms= read_ms= drain_ms= sd_ms= unserialize_ms= bytes=` (the state-boot test prints it).
1. Read and parse `<path>.meta` (missing or bad: `AZH_E_SAVESTATE` "not a complete state"); `abi` must equal
   `AZH_ABI_VERSION`; `<path>.sd/` must exist; the sha256 of the app being booted (state boot) or of the noted app
   (`azh_load_state`) must equal `app_sha256`, else `AZH_E_SAVESTATE` "state is for another app (<meta app>)",
   unless `getenv("LAZ_STATE_ANY_APP")` is `"1"` (then one warning line in host.log); a different `core_version` is
   logged as a warning (the core decides). Nothing has changed yet when any of these fails.
2. Read `<path>` into a buffer (size cap 2 GiB, checked).
3. Drain: one `retro_serialize_size()`; a 0 is `AZH_E_SAVESTATE` "drain timed out (the guest kept async work
   pending; see host.log)", and nothing is replaced. The buffer it made is discarded (freed by the next serialize
   call or at close). Its polls are not counted as k.
4. Replace the SD folder: `azh__clear_tree(sd_root)`, `rmdir(sd_root)`, `azh__copy_tree(<path>.sd, sd_root)`.
5. `retro_unserialize(buf, size)`: false is `AZH_E_SAVESTATE` "the core refused the state (another core build; see
   host.log)".
6. Free the buffer.
7. `azh__counters_set(meta.frame_total, meta.vblanks_total)`. The held input is left as it is.

Note for Phase G (our core): the drain is a whole serialize thrown away; if `drain_ms` is a large part of `t_state`,
Phase G may add a drain-only entry point to our core. D records the numbers; it does not optimise.

### 3.4 State boot: `azh__state_boot(app, path)` (called by `azh_boot` once A's boot path has loaded the app)

Section 3.3 step 1 first (fail before any frame), then `azh__run_one_frame()` once (the warm-up `retro_run` that
completes the Vulkan setup; it makes A's first-frame boot check and returns `AZH_E_BOOT` on a NULL frame,
phase-c.md 3.6; PLAN 2.9), then 3.3 steps 2-7. The next batch's first frame is absolute frame
`meta.frame_total + 1`. If the screen check of section 8 fails (PLAN risk 8: the GPU side not restored right after
the first frame), the builder tries warm-up counts 2 and 4 once each, records which passes, and reports; the count
becomes a named constant, never a hidden loop.

## 4. The Python package (`python/libazahar/`)

### 4.1 Modules

| Module | Role |
|---|---|
| `__init__.py` | re-exports `Emulator`, `Buttons`, `Touch`, `Circle`, `RunResult`, `Shot`, `SaveInfo`, `Stats`, the error classes; `__version__ = "0.1.0.dev0"` |
| `_abi.py` | ctypes `Structure`s mirroring `host/azhost.h` exactly (`ShotReq`, `Batch`, `Result`, `Stats`, `Field`, `Layout`), the constants (error codes, stop reasons, exit codes, screens, formats, `AZH_IN_*`, `AZH_INPUT_INTS`, limits), and `check_layout(layout)`: first `layout.size_layout == ctypes.sizeof(Layout)` (else `fields[]` would be read from the wrong place) and `abi == 2`; then every `<struct>.<field>` row of `fields[]` against the ctypes field of that name (offset and size), every `<struct>.__size__` against `ctypes.sizeof`, every `map.*` row against `_map.py`'s offset constants, and every `const.<NAME>` row against `_abi.py`'s constant of that name; any difference, and any row naming something the Python side lacks, raises `HostError("ABI mismatch: <name> ...")` |
| `_host.py` | worker side only: `load(path) -> ctypes.CDLL`, `argtypes`/`restype` for every `azh_*` function (`azh_stats` takes `POINTER(Stats)`, the header's `struct azh_stats`), the layout check at load (PLAN: "checked against `azh_abi_layout()` at import"), and `call(fn, *args)` that turns a negative return into `HostCallError(code, azh_error())` |
| `_worker.py` | `main(fd: int) -> int`: `os.nice(10)`, `faulthandler.enable()` (stderr goes to `worker.err`), wrap `Connection(fd)`, load the host, send `("hello", layout_rows)` or `("fatal", text)`, then a bounded request loop (section 4.3) |
| `_map.py` | the map offset constants (`HEARTBEAT = 16`, `STOP_CODE = 24`, `MSG_LEN = 28`, `MSG = 32`, `DIMS = 1056`, `PX_FRAME = 1072`, `FRAME_TOTAL = 1080`, `VBLANKS_TOTAL = 1088`, `MSG_SEQ = 1096`, `PID = 1100`, `EXIT_CODE = 1104`, `PIXELS = 4096`, `SIZE = 695296`; checked by `_abi.check_layout`) and `HostMap(path)`: read-only `mmap`; `valid()` (the magic is there), `heartbeat()`, `stop_code()`, `message()`, `frame_total()`, `vblanks_total()`, `exit_code()`, `px_frame()`, `pixels(screen)` (a `memoryview` slice); `close()` tolerant of `BufferError` (live numpy views: the map is kept until they die) |
| `_client.py` | the parent side of one worker: spawn, `request(op, args, wait)` with the wait loop of 4.4, death mapping, `close()`; knows nothing about frames or inputs, so the pure tests drive it with a fake worker |
| `_paths.py` | the repo root (`LAZ_ROOT`, else `Path(__file__).resolve().parents[2]`, which is the repo only for an editable install or a run from the tree; if `<root>/build/libazhost.dylib` is not there, `HostError` "set LAZ_ROOT, or install with pip install -e"), the host (`LAZ_HOST`, else `<root>/build/libazhost.dylib`), core (argument, `LAZ_CORE`, else `<root>/dl/azahar/azahar_libretro.dylib`), MoltenVK (`LAZ_MVK`, else A's default path under `<root>/dl/moltenvk/`), profile (`LAZ_PROFILE`, else `<root>/host/options-default.txt`); every result `resolve()`d to an absolute path |
| `inputs.py` | `Buttons(enum.IntFlag)` with libctru names and values (`A=1<<0, B=1<<1, SELECT=1<<2, START=1<<3, DRIGHT=1<<4, DLEFT=1<<5, DUP=1<<6, DDOWN=1<<7, R=1<<8, L=1<<9, X=1<<10, Y=1<<11, ZL=1<<14, ZR=1<<15`; aliases `RIGHT, LEFT, UP, DOWN`); `Touch(x, y)` and the constant `Touch.up`; `Circle(x, y)` (up positive, -32767..32767); `Held` (the whole held state); `fold(inputs, frames, held) -> (array('i'), Held)` |
| `results.py` | frozen dataclasses `Shot(frame, top, bottom)`, `RunResult(frames, stopped_by, first_frame, last_frame, frame_total, vblanks, wall_s, message, shots)`, `SaveInfo(path, k, frame_total)`, `Stats(...)` |
| `errors.py` | the classes of 4.5 and `from_code(code, text)` |
| `emulator.py` | `Emulator` (4.6) |

Type hints and docstrings on every public name; stdlib only (numpy used when importable, Pillow never needed); no
module-level side effects except constants; every loop bounded.

### 4.2 Starting the worker (phase-2.md P3)

```python
parent, child = multiprocessing.Pipe(duplex=True)
argv = [sys.executable, "-I", "-c",
        "import sys; sys.path.insert(0, sys.argv[2]); from libazahar._worker import main; sys.exit(main(int(sys.argv[1])))",
        str(child.fileno()), str(pkg_parent)]          # pkg_parent: the absolute folder that holds libazahar/
proc = subprocess.Popen(argv, pass_fds=(child.fileno(),), stdin=subprocess.DEVNULL,
                        stdout=err_file, stderr=err_file, env=env, cwd=workdir)
child.close()
```
`-I` keeps the worker free of the user's site and `PYTHON*` variables (as PLAN wants) and still finds the package,
installed or not. `env` is `os.environ` plus `LAZ_MVK` (phase-2.md A12: the library reads it) and `LAZ_LOG_LEVEL` if
the caller set it. The worker's cwd is the workdir and A's defaults are relative to the cwd, so **every path the
parent sends (core, sysdir, log, map, profile, app, state, shot folders) is absolute**. No `multiprocessing` start
method is used, so a script without a `__main__` guard never re-launches itself. `err_file` is `<workdir>/worker.err`
opened for append.

### 4.3 The worker's requests (one ctypes call each, except `start`)

| Op | Args | Does | Reply |
|---|---|---|---|
| `start` | core, sysdir, log, map, options (ordered list of pairs: the profile file's lines first, then the caller's), app, state or None | `azh_open`, each `azh_set_option`, `azh_boot(app, state)` | `("ok", stats dict)` |
| `run` | the flat records (`array('i')` bytes), a `Batch` as bytes | `azh_run` | `("ok", Result as bytes)` |
| `set_input` | 7 ints | `azh_set_input` | `("ok", None)` |
| `shot` | screens, format, prefix or None | `azh_shot` | `("ok", None)` |
| `save_state` / `load_state` | path | `azh_save_state` / `azh_load_state` | `("ok", k)` / `("ok", None)` |
| `stats` | | `azh_stats` | `("ok", dict)` |
| `close` | | `azh_close`, then reply, then return 0 | `("ok", None)` |
An error reply is `("err", code, text)`. The loop ends on `close` or on EOF.

### 4.4 The parent's wait loop (`_client.py`)

Per request: `send`, then loop with `conn.poll(0.1)`; on data, `recv` and return. Between polls: `proc.poll()`; a
dead worker goes to the death mapping. Limits per op:
- `run`: the heartbeat from the map is read every poll and its last change time kept; no change for `timeout`
  seconds (the call's own `timeout` if given, else the Emulator's, default 30) means `HostTimeout`. Until the
  heartbeat has moved once after `start`, the limit is `boot_timeout` instead (the first frames carry the shader
  compiles, since boot runs no frame).
- `start`: total wall time held to `boot_timeout` (default 300).
- `save_state` and `load_state`: total wall to `timeout` plus 10 s (the drain may take 5 s).
- the other ops: total wall to `timeout`.
On a timeout the parent sends SIGKILL to its own worker (works on a stopped one), reaps it with `wait`, and raises
`HostTimeout(op, seconds, last message)`. EOF from `recv` goes to the death mapping too. The loop is bounded by the
timeouts.

Death mapping (return code from `proc.wait()`; the map is read only if `HostMap.valid()`):
- 10 (`AZH_EXIT_GUEST_EXITED`) during `run`: return a `RunResult(stopped_by="guest_exited", frames=F,
  first_frame=1, last_frame=F, frame_total=map frame_total, message=map message)` with `F = map frame_total -
  frame_total before the batch` (C's exit path writes `frame_total + 1`, so the frame that exited counts), and mark
  the Emulator closed (the worker is gone).
- 10 during any other op (a state's drain runs the guest): mark the Emulator closed and raise `HostError("the guest
  exited during <op>: <map message>")`.
- 11: `GuestError(map message)`; the Emulator is closed.
- anything else (a negative code is a signal), during any op: `HostCrashed(returncode, signal, message=map message
  or None, log_tail=last 20 lines of host.log, err_tail=last 20 lines of worker.err)`. A death during `start` before
  the map is valid gives `message=None` and the two tails.

### 4.5 Errors

`LibAzaharError(Exception)` is the base. `BootError` (AZH_E_BOOT, AZH_E_CORE, AZH_E_VULKAN during `start`, and
AZH_E_BOOT from the first `run`), `GuestError` (exit 11, or a `guest_error` stop on our core: raised with `.result`
holding the `RunResult`; on our core the Emulator stays open), `HostTimeout`, `HostCrashed`, `StateError`
(AZH_E_SAVESTATE), `NeedsLazpyCore` (AZH_E_NEEDS_LAZPY_CORE), and **`HostError`** (P6: `AZH_E_ORDER` call order,
AZH_E_IO, AZH_E_NOMEM, AZH_E_UNSUPPORTED, AZH_E_VULKAN outside `start`, an ABI mismatch, a missing host, a guest exit
outside `run`). AZH_E_ARG becomes `ValueError` (the Python side validates first, so it means a bug). `guest_break`
and `guest_exited` are stop reasons, never errors; a guest crash is a `guest_error` (phase-c.md 3.5). Every error
carries the host's text.

### 4.6 `Emulator`

```python
Emulator(app, workdir, *, sd_seed=None, state=None, core=None, options=None, timeout=30.0, boot_timeout=300.0)
```
- `workdir` is created if missing and resolved to an absolute path; inside it: `sys/` (the sysdir; the SD folder is
  `sys/Azahar/sdmc/`), `shots/`, `host.log`, `host.map`, `worker.err`. `sd_seed` (a folder, never named `sdmc`,
  PLAN 2.5) is copied with `shutil.copytree(..., symlinks=False, dirs_exist_ok=True)` into the SD folder **before**
  the boot without a state, and **after** the state boot with one (so seed files land on top of the snapshot;
  USING.md says so).
- `run(frames, inputs=(), shots=(), *, stop_file=None, stop_text=None, stop_every=30, stop_new=False,
  debug_text=None, wall_limit=None, timeout=None) -> RunResult`. `inputs` is an iterable of `(frame, item)`: item is
  `Buttons`/int (the whole button mask), `Touch(x, y)`, `Touch.up`, or `Circle(x, y)`; each changes only its part of
  the held state; sorted by frame (stable), folded into one full record per frame. Validation in Python first
  (`ValueError`, same rules as phase-c.md 3.4). `shots` are batch frames; `result.shots[f]` is a `Shot` whose paths
  are `shots/shot_<absolute frame %06d>_top.png` and `_bottom.png`. `wall_limit` is in seconds (float). `timeout`
  replaces the Emulator's heartbeat timeout for this call only.
- `run_until(file, text, max_frames, *, every=30, new_only=False, inputs=(), shots=(), timeout=None) -> RunResult` is
  `run` with the SD rule; the caller checks `r.stopped_by == "sd_text"`.
- `run_frame()`, `set_keys(raw=...)` (libmgba-py's names), `set_input(buttons=None, touch=None, circle=None)`.
- `screens()`: one `azh_shot(BOTH, RAW, None)` round trip (C's raw shot), then two read-only numpy views into the map
  (`(240, 400, 4)` and `(240, 320, 4)`, `uint8`, RGBA) if numpy imports, else two `bytes`. The views show whatever
  the map holds, so they change at the next raw shot (the next `screens()` or a batch RAW shot); the docstring says
  so, and says to `.copy()` to keep a frame. `px_frame()` must equal `frame_total` after the call (else `HostError`).
- `shot(path_prefix)`: PNGs of the current frame.
- `save_state(path) -> SaveInfo`; `load_state(path)`; `stats() -> Stats`; properties `sd` (`Path` of the SD folder),
  `frame_total`, `pid`, `closed`.
- `close()` always reaps (graceful `close` op with `timeout`, then SIGKILL of its own worker); idempotent;
  `__enter__`/`__exit__`; `weakref.finalize` reaps a forgotten one. Using a closed Emulator raises `HostError`.
- `emu.memory` is Phase G's; not defined here.

## 5. Files (the builder creates or edits only these)

| Path | When | Role |
|---|---|---|
| `python/libazahar/__init__.py`, `_abi.py`, `_host.py`, `_worker.py`, `_map.py`, `_client.py`, `_paths.py`, `inputs.py`, `results.py`, `errors.py`, `emulator.py` | D1 | section 4 |
| `pyproject.toml` | D1 | setuptools backend (`requires = ["setuptools>=77"]`, `build-backend = "setuptools.build_meta"`), `[project] name = "libazahar-py"`, `version = "0.1.0.dev0"`, `requires-python = ">=3.10"`, `license = "GPL-3.0-or-later"`, optional extras `numpy`; `[tool.setuptools] package-dir = {"" = "python"}`, `packages = ["libazahar"]`; `[tool.pytest.ini_options] testpaths = ["tests/python"]`, `markers = ["slow: needs the emulator"]` |
| `tests/python/conftest.py` | D1 | inserts the absolute `python/` and `tests/` paths (`Path(__file__).resolve().parents[...]`) into `sys.path` before any `import check_testapp` (B12); fixtures `host_paths` (when `build/libazhost.dylib`, the stock core or `build/testapp.3dsx` is missing: `pytest.skip` with the reason, or `pytest.fail` with it when `LAZ_REQUIRE_EMULATOR=1`, P2), `workdir` (a fresh `runs/d-pytest/<test name>/`), `seed(**control_keys)` (a seed folder built with `testapp_log.write_control` once C is merged; D1's tests need no seed) |
| `tests/python/fakeworker.py` | D1 | a stand-in worker for `_client.py` tests: modes `ok`, `exit10`, `exit11`, `segv` (kills itself with SIGSEGV), `hang` (stops the heartbeat), `eof`, `die_at_start` (exits before writing the map); it writes a small `host.map` at `_map.py`'s offsets |
| `tests/python/test_inputs.py`, `test_errors.py`, `test_map.py`, `test_client.py`, `test_abi.py` | D1 | pure or no-core tests (section 7) |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | D2 | section 3 (the stubs from C1 replaced) |
| `tests/python/test_c_checks.py`, `test_live_errors.py`, `test_state.py`, `test_api.py` | D3 | section 8; PNGs decoded with `check_testapp.read_png_rgba` (imported, never copied) |
| `docs/USING.md` | D3 | section 9 |

No item files: the report's "Lessons and notes" block (section 11) is for the main loop. C rules for
`state.c`/`statemeta.c`: functions under about 60 lines, about 2 asserts each, no goto/recursion/setjmp, bounded
loops, every return checked, one owner per buffer.

## 6. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree** (no `dl/`, `vendor/`, `build/`, all ignored): `mkdir -p dl && for d in azahar moltenvk
   libretro-headers vulkan-headers; do ln -s MAIN/dl/$d dl/$d; done` (link the children, never `dl/` itself),
   `cp -R MAIN/vendor .`, `make` (the C1 code builds). Checkpoint: `make test-host` passes. **Run no emulator until
   D3.**
1. **D1, the Python package (about 0.75 h).** Section 4 modules, `pyproject.toml`, the D1 tests. Checkpoint:
   `python3 -m pytest -q tests/python -m "not slow"` passes; the venv check of gate 3.
2. **D2, savestates in C (about 0.4 h).** `statemeta.c` and its unit tests (format/parse round trip, every key
   missing once, an unknown key, a bad integer, an over-long value, a bad `app_sha256`, an abi mismatch, a
   tmp-then-rename write and read); `state.c` per section 3 (it compiles and passes `make check`; it is exercised in
   D3). Checkpoint: `make check && make && make test-host` clean. **Then end your run**: your final report is the
   "D1+D2 done" report (the exact list of paths, the `make test-host` and non-slow pytest summaries with the fake
   round-trip times, the venv check output, and any header or C-file change D would need, which must be none). Do
   not start D3. The main loop merges main (with step C) into `step-d` and resumes you with "main merged at <sha>, go
   on with D3".
3. **D3, integration and docs (about 0.55 h, after C is merged).** `make` again (C2 and C3 are now in); read
   `tests/checks_c.py` and `tests/testapp_log.py`; write the section 8 tests. **Before the slow tests**: if
   `MAIN/build-core/build.pid` names a live process (`kill -0`) and `MAIN/build-core/build.exit` does not exist, wait
   with the Monitor tool until `build.exit` exists or the pid is gone (bounded, 120 min), unless the main loop's
   message said "run under the build"; report the wait. Then start the whole suite with `run_in_background`:
   `sh -c 'trap "echo \$? > runs/d-pytest.rc" EXIT; LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs
   tests/python > runs/d-pytest.log 2>&1'`, and wait with Monitor until `runs/d-pytest.rc` exists (bounded, 90 min);
   never `sleep`-poll. If Monitor is not in your tool list, run it in foreground parts under the 10-minute Bash limit
   (`-m "not slow"`, then one call per slow test file, the 200,000-frame test alone with `-k long_batch`) and say so.
   While it runs, write `docs/USING.md`. The planted red. Check `~/Library/Logs/DiagnosticReports` once for a new
   report naming `python3` from the SIGSEGV test (report it; do not delete anything). Checkpoint: gate 1-4 pass;
   quote the pytest summary.
4. The report (section 11) ends the run. Before handing back, stop every waiter or background task you started
   (TaskStop). If the opus review asks for fixes, the main loop resumes you again.

## 7. Tests that need no emulator (D1, D2)

- `test_inputs.py`: `Buttons` values equal libctru's bits (the table in phase-c.md section 2); folding keeps each
  part (a `Touch` does not clear buttons; `Touch.up` keeps the last x, y but sets down 0); several items on one frame
  fold into one record; out-of-order input is sorted; validation errors (frame 0, beyond `frames`, a bad bit,
  x 320, y 240, circle 32768). (The float32 touch model lives in C's `checks_c.py`; D3's `test_c_checks.py` uses it.)
- `test_errors.py`: every `AZH_E_*` code maps to its class (4.5); `GuestError.result` set.
- `test_map.py`: a synthetic `host.map` made with `struct` at `_map.py`'s offsets; every reader returns its value;
  `valid()` false on a zero file; `close()` with a live `memoryview` does not raise.
- `test_client.py` (fake worker): `ok` round trip (the mean of 200 round trips and of a 691,200-byte copy from the map
  printed, no bound); `exit10` during `run` gives a `guest_exited` result with `frames` from the map and a closed
  client; `exit10` during `save_state` gives `HostError` and a closed client; `exit11` gives `GuestError`; `segv`
  gives `HostCrashed` with `signal == SIGSEGV` within 1 s of the death; `hang` with a per-call `timeout=1` gives
  `HostTimeout` between 0.8 and 4 s after the heartbeat stopped, and the pid is reaped; `die_at_start` gives
  `HostCrashed` with `message is None`; `eof` goes to the death mapping; `close()` twice is fine.
- `test_abi.py` (loads `build/libazhost.dylib` with ctypes in the test process; calls only `azh_abi_layout`):
  `check_layout` passes; a wrong `size_layout` is caught before any row is read; a copy of the ctypes `Batch` with one
  field moved is caught; a `_map.py` constant changed by one is caught; an `_abi.py` constant changed is caught by its
  `const.*` row.
- `tests/host/test_statemeta.c` (D2): as step 2 says.

## 8. Integration tests (D3; `@pytest.mark.slow`; each its own `workdir`; one Emulator alive at a time)

- `test_c_checks.py`: phase-c.md section 8's scenarios (a) once, (b), (c1-c3), (d), (e), (f) through `Emulator.run`,
  `run_until`, `screens()` and `RunResult`, with the same inputs, batch splits (the extra one-frame batches give
  c_min) and checks, using `tests/checks_c.py` and `tests/testapp_log.py`; (d4) compares `screens()` against the PNG
  of the same frame; (e) expects `stopped_by == "guest_break"`; (f) expects `RunResult.stopped_by ==
  "guest_exited"`, `frames` equal to C's f3 rule, and a closed Emulator; (c4) expects `NeedsLazpyCore`.
- `test_live_errors.py`: SIGSEGV: `threading.Timer(3.0, os.kill, (emu.pid, signal.SIGSEGV))` during
  `run(10_000_000)`; `HostCrashed` is raised and the time from the kill to the raise is under 1.0 s (printed).
  SIGSTOP: `run(300)` first (the boot and shader work done at the default limits), then a `threading.Timer(2.0,
  os.kill, (emu.pid, signal.SIGSTOP))` and `run(10_000_000, timeout=3)`; `HostTimeout` is raised with the delay from
  the `os.kill` to the raise between `timeout - 0.2` and `timeout + 3` (2.8 to 6 s; printed; the last heartbeat
  change is seen up to one 0.1 s poll before the stop); then `os.kill(pid, 0)` raises `ProcessLookupError`. Long
  batch (`test_long_batch`): `run(200_000)` returns `stopped_by == "frames"` and `frames == 200_000` with the default
  timeout (several minutes at today's load; the heartbeat keeps moving).
- `test_api.py`: `screens()` shapes and dtype; a numpy view of the top screen shows the red marker at (0, 0)
  (B's table); `set_keys(raw=Buttons.A)` then `run(10)` logs `k=00000001`; `run_frame()` advances `frame_total` by 1;
  `save_state`/`load_state` on one instance: save, run 300 with inputs, **read the log now** (the load replaces the SD
  folder), load, run 300 with the same inputs, read the log: the same `v k tx ty td cx cy` fields; `SaveInfo.k >= 0`.
- `test_state.py`, **the state-boot gate** (PLAN Phase D): seed `boot_frames=6000`. Instance A: start the clock,
  `Emulator(app, wd_a, sd_seed=seed)` (its wall is `t_core_start`: core load and `azh_boot`, no frames),
  `run_until("testapp/log.txt", "booted f=", max_frames=12_000)`, stop the clock (`t_boot`, including
  `t_core_start`), `save_state(s)`, then `run(600, inputs=I, shots=[100, 300, 600])` where I presses buttons and
  touches points at fixed batch frames; read A's log; close A. Instance B: copy A's `sys/` into `wd_b/sys/` without
  `Azahar/sdmc/` (the state restores that; the shader cache and NAND come along, as in Gen3D's reused instance
  folders; list the folders copied in the report); start the clock, `Emulator(app, wd_b, state=s)`, stop the clock
  (`t_state`); B's `testapp/log.txt` equals `s.sd/testapp/log.txt` byte for byte; `B.frame_total == A`'s at the
  save; `run(600, inputs=I, shots=[100, 300, 600])`. Checks: B's shots pass `check_testapp.py markers --top
  --bottom --mode 2d`; for every per-frame line of A with `v` in `(v_save, v_save + 600]` (v_save = A's last
  per-frame `v` before the save plus k), B has a line with the same `v` and the same `k tx ty td cx cy`;
  `t_state < 0.10 * t_boot`. Printed (to stderr, shown on failure) and written to `runs/d-pytest/state-times.txt`:
  `t_core_start`, `t_boot`, `t_state`, the ratio `t_state / t_boot`, the fixed-cost ratio
  `(t_state - t_core_start) / (t_boot - t_core_start)`, k, and B's `state load ...` line from `host.log`. If only the
  plain ratio fails, the builder reports both ratios and the main loop takes it to Guy; nothing is tuned. The planted
  red (`LAZ_TEST_PLANT_RED=1`) compares A's lines against B's lines one `v` later.
- `test_state.py::test_other_app`: copy `build/testapp.3dsx` to `wd/other.3dsx` with one byte appended (a different
  sha256, the same program); `Emulator(other, wd_c, state=s)` raises `StateError` naming the meta's app before any frame (the map in
  `wd_c` shows `frame_total` 0); then with
  `monkeypatch.setenv("LAZ_STATE_ANY_APP", "1")` the same call boots and `run(10)` works.

## 9. `docs/USING.md` (D3; plain, short sections; no speed claims from the test app)

1. Install: `python3 -m venv .venv && .venv/bin/pip install -e .` (the worker runs `python -I`, so a venv, not the
   user site). **Editable install only**: the package finds the repo (`build/`, `dl/`, `host/`) from its own folder;
   a plain install must set `LAZ_ROOT`. `make` builds the host; `tools/fetch.sh` fetches the stock core and MoltenVK.
2. Paths and environment: `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE`, `LAZ_MVK`, `LAZ_PROFILE`, `LAZ_LOG_LEVEL`,
   `LAZ_ANY_CORE`, `LAZ_STATE_ANY_APP`, `LAZ_REQUIRE_EMULATOR` (tests), `MVK_CONFIG_LOG_LEVEL` (1 unless set); the
   instance folder layout.
3. Frames: one `run` frame is one guest VBlank; frames are 1-based in a batch; absolute frame numbers in shot names;
   `frame_total`; the frame a guest exits on counts.
4. Inputs: movie semantics, held across batches; folding; `Buttons` names = libctru; the offsets step C measured
   (buttons, ZL/ZR, circle, touch) as "a change made at frame f shows in the guest's log line of host frame f + m, or
   sometimes f + m + 1", with C's m values and counts.
5. Touch: pixel coordinates; the 4 rows table (`63 -> 62`, `125 -> 124`, `126 -> 125`, `127 -> 126`) and why (HID's
   float truncation, as in Qt Azahar); no cursor is drawn.
6. Circle pad: up positive; 32767 -> 154; the 3-poll averaging (one in-between frame).
7. Stops: every `stopped_by` value and what triggers it. **A guest crash is `guest_error`; a `svcBreak` or `bkpt` is
   `guest_break`** (the guest runs on after it). SD text rule (every K frames, `new_only`, split matches, shrink).
   Debug text needs our core: on the stock core the core's log runs on its own thread, so a hit could arrive frames
   late (P5).
8. Errors and timeouts: each class, when it is raised, `timeout` (Emulator-wide and per call), `boot_timeout` (also
   covers the first frames' shader compiles).
9. Screens: `screens()` views change at the next raw shot; `.copy()` to keep one.
10. Savestates: the three files; k and "a state at frame N is at N + k"; the SD snapshot and seed order; the app
    check (sha256; the core's own program-id check does nothing for a `.3dsx`; `LAZ_STATE_ANY_APP=1` after a
    deliberate rebuild); states may not survive a core change; NAND files are not snapshotted (they reopen from the
    new instance's NAND), and the app's RomFS reopens from the new app path; the restore step times in `host.log`.
11. Stock core and our core: what each gives (exact repeats, debug text, memory reads from Phase G, poll-exact movies
    if Phase F confirms `lazpy_movie_play`).
12. **The Gen3D mapping**: one table, rows 1-17 of `docs/research/gen3d-harness-needs.md`, each mechanism with its
    libazahar-py call (Qt profile pins -> `options`; SD staging -> `sd_seed`; locks/focus/curtain -> dropped; CTM
    movies -> `inputs` (poll-exact needs our core); SD control channel, netlogs, `voxel.log` -> `emu.sd` files and
    `run_until`; window screenshots -> `shots` / `screens()` with the 400x240 + 320x240 split; framebuffer via gdb ->
    `screens()`; gdb RAM reads -> Phase G `emu.memory` (the test app's 32-byte record shows the pattern: magic 0,
    frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24) or an app log line; `gdbio resume` -> gone;
    savestates -> `save_state` and `Emulator(state=)`); then the forced-mode seed pattern (a seed folder holding the
    app's control file, so one Emulator boots straight into a mode, as the test app's `control.txt` shows) and state
    boot for the long world build (boot once, save, start every test from the state, reusing the instance folder's
    `sys/` for the shader cache).

## 10. Machine-sharing rules

- D1 and D2 run no emulator (step C's builder is using the machine). In D3: one Emulator alive at a time (each test
  closes its own before the next starts; pytest runs serially, no `-n`), always nice'd (the worker calls
  `os.nice(10)`; the pytest process itself is started with `nice -n 10`), folders under `runs/d-*` (ignored).
- The slow tests do not run beside the core build in MAIN (step 3). Never write in MAIN's `build-core/`.
- Never open a window: no Azahar app, no `open`, no Preview; PNGs with the Read tool.
- Signals go only to the worker pid our own Emulator reports; never `pkill`/`killall`; never another session's
  process.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back. The 200,000-frame test is the long
  one; while it runs, write USING.md.

## 11. The builder's report

D1+D2 (the end of the first run): as step 2 says. D3: the full pytest summary (0 skipped) or each part's, and which
way it was run; the planted red; `t_core_start`, `t_boot`, `t_state`, both ratios, the restore step times and the
folders copied into B's `sys/`; k from the saves; the warm-up count used; the SIGSEGV and SIGSTOP delays; the fake
round-trip times; any wait for the core build; whether a crash report appeared; line counts per file and the longest
function; the runners block for `docs/map/runners.md`:
```
python3 -m venv .venv && .venv/bin/pip install -e .      # the Python package (editable only)
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python   # step D's tests (slow ones need the emulator)
build/azhost run <app> --frames N --save runs/x.state    # a state from the command line
```
Lines the main loop must add to `.gitignore` (expected: `.venv/` and `__pycache__/` are already there;
`*.egg-info/` if not); and a final **"Lessons and notes"** block, ready to paste into item 220.

## 12. Hours (agent wall time)

Builder 1.7 h (D1 0.75 with the death cases and the boot-timeout rule, D2 0.4 with the app hash, D3 0.55), the opus
diff review 0.3 h, the commit 0.1 h: **2.1 h**, against PLAN.md's 2.25 (A's `core.c` already loads the serialize
symbols; C's check functions, B's PNG decoder and C's SD copy are reused). A wait for the core build is machine time.

## 13. Review checklist (the opus as-built review)

1. ctypes structs match the frozen header field for field; `check_layout` compares `size_layout` first, then every
   `fields[]` row, the struct sizes, every `map.*` row against `_map.py` and every `const.*` row against `_abi.py`;
   it runs when the worker loads the host.
2. Worker: `-I`, the explicit package root, absolute paths only, `pass_fds`, child end closed in the parent,
   `os.nice(10)`, stdout/stderr to `worker.err`, no `multiprocessing` start method, bounded request loop, exits on EOF.
3. Wait loop: heartbeat timeout for `run` (per-call `timeout` honoured; `boot_timeout` until the first heartbeat
   move), total wall for `start`, states and the other ops, SIGKILL only of its own worker, always reaped; death
   mapping for 10 in `run` (frames from the map) and outside it, 11, signals, a death before the map is valid, EOF;
   error classes as 4.5; messages from the map.
4. Inputs: folding per part, one record per frame, validation equal to C's; Buttons equal libctru's bits.
5. Savestates: the order of 3.2 (meta unlinked first, k from the vblank counter, `frame_total += k`, meta last and
   fsynced); restore order of 3.3 (meta, `.sd/` and the app hash checked first, read, drain with a 0 refused, SD
   replace, unserialize, counters; every step timed in `host.log`); `LAZ_STATE_ANY_APP` only as written; state boot
   fails before any frame on a bad meta; tmp-then-rename for every file; one owner per buffer, freed on every path.
6. `statemeta.c` pure and strict; the unit tests cover every failure branch.
7. The state-boot test checks all of section 8, seeds B's `sys/` as written, prints the times and both ratios;
   nothing tuned to pass; the planted red shown; the other-app test.
8. `screens()` views read-only, documented as changing at the next raw shot; `px_frame` checked; close tolerant of
   live views.
9. Python rules: type hints, docstrings, stdlib only, bounded loops, no bare `except`, no module side effects; the
   `tests/` path inserted before `import check_testapp`; skips only through `host_paths`.
10. USING.md covers section 9, the editable-install rule, crash versus break, the 4 rows, the measured offsets, the app
    check, the Gen3D table; no speed claims.
11. Nothing outside section 5 changed (no C file of step C, no header edit, no `core.c` edit, no item file); no build
    outputs, PNGs, logs, states, `runs/` or the venv in the diff; no waiter left running.

## 14. Interfaces assumed (from Phase 1 and step C)

From step C (frozen at C1, `docs/plans/phase-c.md` section 3): the headers (ABI 2, `azh_result` with `vblanks` and
`message`, `azh_layout` with `fields[]` including the `const.*` rows and nothing else new, the sizes 3348, 304, 240,
6452, `AZH_EXIT_UNSUPPORTED`), the map offsets 1056-1104 and 4096, raw shots into the map (C2), the prototypes of
3.6 (`azh__run_one_frame` with the first-frame check, `azh__counters_*`, `azh__vblanks_total`, `azh__sd_root`,
`azh__copy_tree`, `azh__clear_tree`, `azh__state_*`, `azh__meta_*`, `azh_state_meta` with `app_sha256`), `azh_boot`
calling `azh__state_note_app` and `azh__state_boot`, the crash-versus-break detector, the exit path writing
`frame_total + 1`, the `--save` flag, `tests/checks_c.py` and `tests/testapp_log.py` (after the D3 resume).
From Phase 1 (`docs/plans/phase-2.md` section 6): A1 and A2 (A's names and error codes, `AZH_E_ORDER`, the reserved
`AZH_E_SAVESTATE`, `struct azh_stats` / `azh_stats_t`), A4 (frames, shot names, `azh_boot` runs no `retro_run`), A5
(the map), A11 and A12 (paths, the library reading `LAZ_MVK`, `MVK_CONFIG_LOG_LEVEL`), A14 (`core.c` loads the
serialize symbols), A15 and B1 (the test app), A17 (`azh_abi_layout` works before `azh_open`), B2 (control keys,
`boot_frames` up to 10,000), B3 (log lines, `booted`), B6 (busy boot frames), B8 (markers and `check_testapp.py
markers --top --bottom`), B11 (`read_png_rgba`), B12 (the `-P` path insert), B13 (the record, for USING.md only), SD
(async OpenFile, SetSize, Close). If the merged code differs in a name, follow the code and report; in behaviour this
brief relies on, stop and report.
