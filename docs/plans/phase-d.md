# Phase 2, step D: the Python layer, savestates, state boot (item laz-220)

Opus step plan, 2026-11-12, **draft for Phase 2's two opus review loops. Nobody builds from it until the reviews
pass and the main loop launches the step.** Index: `docs/plans/phase-2.md`. For one sonnet builder in its own git
worktree (`../wt-d`, branch `step-d`, made by the main loop at step C's checkpoint C1 commit). It refines
`docs/PLAN.md` sections 2.1, 2.5, 2.8 (the worker's `nice`) and 2.9 and the "Phase D" paragraph of section 3; where
they disagree on a goal, PLAN.md wins and the builder stops and reports.

Builder reads first, in this order: `docs/map/rules.md`; PLAN.md 2.1, 2.2, 2.3, 2.5, 2.9 and section 3's Phase D
paragraph; `docs/plans/phase-c.md` sections 2, 3 and 8 (the frozen header, the input facts, the gate scenarios D
reruns through Python); `docs/research/gen3d-harness-needs.md` (USING.md's mapping table);
`~/.claude/python-golden-rules.md`, `~/.claude/c-golden-rules.md`. Then the code at the C1 commit: `host/azhost.h`,
`host/azh_internal.h`, `host/state.c`, `host/statemeta.c`, `host/run.c` (the four functions D links against),
`host/core.c`, `tests/checks_c.py`, `tests/testapp_log.py`.

## 1. Goal and gate

Goal: `import libazahar` gives the API of PLAN.md 2.5: an `Emulator` that runs one host instance in its own worker
process (ctypes over `build/libazhost.dylib`), reads the mapped file `host.map` without a round trip, raises typed
errors, saves and loads states with an SD snapshot, and boots straight from a state; `pip install -e .` works in a
venv; `docs/USING.md` tells Gen3D how to move its harness over.

Gate (PLAN.md section 3, "Phase D"), headless, this Mac, stock core, test app only:
1. `make check && make && make test-host` clean (D adds `test_statemeta.c`'s checks).
2. `nice -n 10 python3 -m pytest -q tests/python` (run from the repo root; pytest is in the user site on this Mac, so
   no `-I` here) reports all passed, **0 skipped, 0 failed**; the slow tests included. It covers: C's checks (a)-(f)
   through Python; SIGSEGV to our own worker raises `HostCrashed` within 1 s; SIGSTOP with `timeout=3` raises
   `HostTimeout` and `os.kill(pid, 0)` then raises `ProcessLookupError`; a 200,000-frame batch returns with
   `stopped_by == "frames"`; the state-boot test of section 8 (same markers, same `v k tx ty td cx cy` fields, restored
   log bytes, state boot under 10 % of the boot's wall time, both times printed).
3. `python3 -m venv runs/d-venv && runs/d-venv/bin/pip install -e .` (the one network step: pip fetches setuptools),
   then `runs/d-venv/bin/python -I -c "import libazahar, sys; print(libazahar.__version__)"` prints `0.1.0.dev0`, and
   `runs/d-venv/bin/python -I -m pytest` is not required (pytest is not in that venv).
4. Once, a planted red: run the state-boot test with `LAZ_TEST_PLANT_RED=1` (it compares against the frame after the
   real one) and see it fail; then it passes again. Quote both.

## 2. Facts (checked; SRC = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/` in the main checkout)

- `retro_serialize_size` first drains pending async guest work: `RunLoop` with presentation suppressed until no async
  operation is pending, up to 5 s, then `SaveStateBuffer`; it returns 0 on a drain timeout, a non-Success status or an
  exception. `retro_serialize(data, size)` copies the buffer made by the last `retro_serialize_size` and frees it; it
  fails if none or if `size` is too small. `retro_unserialize` drains the same way, then `LoadStateBuffer`
  (SRC citra_libretro/citra_libretro.cpp:660-738).
- During the drain the window's `SwapBuffers` returns early (no frame is submitted) but `PollEvents`, and so the
  host's `input_poll_cb`, still runs at every guest VBlank (SRC citra_libretro/emu_window/libretro_window.cpp:68-71,
  194-204; video_core/renderer_base.cpp:43-48). So **k = the change in `azh__vblanks_total()` across
  `retro_serialize_size`**. k is often 0 (nothing pending) and is at most about 5 s of guest time.
- `LoadStateBuffer` refuses a state from another program id (core/savestate.cpp:297) or another build revision
  (:303); states are zstd-compressed (:253). So a state may not survive a core change (PLAN risk 5).
- Guest files open at save time survive: `IOFile` serializes its path with placeholders (`%CITRA_USER_SDMC%`), open
  mode, flags and position, and reopens on load (SRC common/file_util.h:82-104, 667-682; common/file_util.cpp:
  1058-1065); SD files are opened `r+b` (core/file_sys/archive_sdmc.cpp:105). So a state reopens the new instance's own
  SD files, which must hold the snapshot's bytes before the load.
- The emulated SD card is `<sysdir>/Azahar/sdmc/`; the test app's log is `testapp/log.txt` in it, truncated by the app
  at start (phase-b.md section 3). Hence the order in section 3.3: the fresh app's warm-up frame may truncate the log,
  so the SD snapshot is restored after a drain, just before the unserialize.
- This Mac (2026-11-12): python3 3.14.0; pytest 9.2.0 and numpy 2.5.0 in the user site (`~/Library/Python/3.14`),
  so `python3 -I` cannot import pytest; setuptools is not importable under `-I`; Pillow absent. A worker started
  with `-m libazahar._worker` under `-I` cannot import an uninstalled package, so section 4.2 starts it with an explicit
  package root.
- `multiprocessing.Pipe()` on POSIX returns two `Connection`s over a `socketpair`; `Connection(fd)` wraps an inherited
  descriptor; `conn.poll(t)`, `send`, `recv` (pickle) are stdlib (Python docs, multiprocessing.connection).

## 3. Savestates and state boot in C (`host/state.c`, `host/statemeta.c`; stubs from C1, D fills them)

### 3.1 Files of a state at `<path>`

| File | Content | Written |
|---|---|---|
| `<path>` | the core's buffer as returned by `retro_serialize` | `<path>.tmp`, `fsync`, `rename` |
| `<path>.sd/` | a copy of the instance's whole SD folder at the save | `<path>.sd.tmp/`, then renamed (an old `<path>.sd/` is first renamed to `<path>.sd.old/` and removed after) |
| `<path>.meta` | `key=value` lines: `abi=2`, `k=`, `frame_total=`, `vblanks_total=`, `created=` (Unix seconds), `core_version=`, `app=` | last, `<path>.meta.tmp` then `rename`; its presence means the state is complete |

`statemeta.c` is pure (`<stdint.h>`, `<string.h>`, `<stdio.h>`, `<stdlib.h>` only): format into a buffer, parse a
buffer (every key required once; unknown keys rejected; integers by `strtoll` with end and range checks; text values
without newlines, truncated never, refused if too long), and write/read with checked I/O. Errors are
`AZH_E_SAVESTATE` with a reason in `azh_error()`.

### 3.2 Save: `azh__state_save(path, k_out)` (called by `azh_save_state` after a batch, never inside one)

1. `v0 = azh__vblanks_total()`; `size = retro_serialize_size()`; `k = azh__vblanks_total() - v0`. Size 0:
   `AZH_E_SAVESTATE` "the core could not save (drain timeout or error; see host.log)".
2. `buf = malloc(size)` (checked; one owner; freed on every path through one small cleanup function, no goto);
   `retro_serialize(buf, size)` must return true.
3. Write `<path>.tmp` (`open` `O_WRONLY|O_CREAT|O_TRUNC`, 0644, a bounded full-write loop, `fsync`, `close`), `rename`.
4. SD snapshot: remove a stale `<path>.sd.tmp/` (`azh__clear_tree` then `rmdir`), `azh__copy_tree(sd_root,
   <path>.sd.tmp)`, swap in as section 3.1.
5. Counters: `frame_total += k` (so the saving instance and a state boot number frames the same way: a state "at
   frame N" is at N + k, PLAN 2.9); `vblanks_total` already includes the k polls. `azh__counters_set`.
6. Meta with the new `frame_total`, the `vblanks_total`, k, the core version (`azh_stats`), the app path
   (`azh__state_note_app`), `created`. `*k_out = k`.

### 3.3 Restore (shared by state boot and `azh_load_state`)

1. Read and parse `<path>.meta` (missing or bad: `AZH_E_SAVESTATE` "not a complete state"); `abi` must equal
   `AZH_ABI_VERSION`; a different `core_version` is logged as a warning (the core decides).
2. Read `<path>` into a buffer (size cap 2 GiB, checked).
3. Drain: one `retro_serialize_size()` whose result is discarded (it settles the guest's pending SD writes before the
   SD is replaced; its buffer is freed by the next serialize call or at close). Its polls are not counted as k.
4. Replace the SD folder: `azh__clear_tree(sd_root)`, `rmdir(sd_root)`, `azh__copy_tree(<path>.sd, sd_root)`; a
   missing `<path>.sd/` is `AZH_E_SAVESTATE`.
5. `retro_unserialize(buf, size)`: false is `AZH_E_SAVESTATE` "the core refused the state (another program or core
   build; see host.log)".
6. `azh__counters_set(meta.frame_total, meta.vblanks_total)`. The held input is left as it is.

### 3.4 State boot: `azh__state_boot(app, path)` (called by `azh_boot` once A's boot path has loaded the app)

Read and check the meta first (fail before any frame), then `azh__run_one_frame()` once (the warm-up `retro_run`
that completes the Vulkan setup, PLAN 2.9), then 3.3 steps 2-6. The next batch's first frame is absolute frame
`meta.frame_total + 1`. If the screen check of section 8 fails (PLAN risk 8: the GPU side not restored right after
the first frame), the builder tries warm-up counts 2 and 4 once each, records which passes, and reports; the count
becomes a named constant, never a hidden loop.

### 3.5 `core.c`

If Phase A's `retro_*` table lacks `retro_serialize_size`, `retro_serialize`, `retro_unserialize`, add the three
explicit `dlsym` lines in A's pattern (a missing symbol is `AZH_E_CORE` naming it). Nothing else in `core.c`.

## 4. The Python package (`python/libazahar/`)

### 4.1 Modules

| Module | Role |
|---|---|
| `__init__.py` | re-exports `Emulator`, `Buttons`, `Touch`, `Circle`, `RunResult`, `Shot`, `SaveInfo`, `Stats`, the error classes; `__version__ = "0.1.0.dev0"` |
| `_abi.py` | ctypes `Structure`s mirroring `host/azhost.h` exactly (`ShotReq`, `Batch`, `Result`, `Stats`, `Field`, `Layout`), the constants (error codes, stop reasons, screens, formats, `AZH_IN_*`, limits), and `check_layout(layout)`: `abi == 2`, every `size_*`, and every `fields[]` row (name, offset, size) against the ctypes field of that name; any difference raises `HostError("ABI mismatch: <name> ...")` |
| `_host.py` | worker side only: `load(path) -> ctypes.CDLL`, `argtypes`/`restype` for every `azh_*` function, the layout check at load (PLAN: "checked against `azh_abi_layout()` at import"), and `call(fn, *args)` that turns a negative return into `HostCallError(code, azh_error())` |
| `_worker.py` | `main(fd: int) -> int`: `os.nice(10)`, `faulthandler.enable()` (stderr goes to `worker.err`), wrap `Connection(fd)`, load the host, send `("hello", layout_dict)` or `("fatal", text)`, then a bounded request loop (section 4.3) |
| `_map.py` | `HostMap(path, layout)`: read-only `mmap`; `heartbeat()`, `stop_code()`, `message()`, `frame_total()`, `vblanks_total()`, `exit_code()`, `pixels(screen)` (a `memoryview` slice); offsets only from the layout the worker sent; `close()` tolerant of `BufferError` (live numpy views: the map is kept until they die) |
| `_client.py` | the parent side of one worker: spawn, `request(op, args, wait)` with the wait loop of 4.4, death mapping, `close()`; knows nothing about frames or inputs, so the pure tests drive it with a fake worker |
| `_paths.py` | the repo root (`LAZ_ROOT`, else three parents up from this file: `python/libazahar/_paths.py`), the host (`LAZ_HOST`, else `<root>/build/libazhost.dylib`), core (argument, `LAZ_CORE`, else `<root>/dl/azahar/azahar_libretro.dylib`), MoltenVK (`LAZ_MVK`, else A's default path under `<root>/dl/moltenvk/`), profile (`LAZ_PROFILE`, else `<root>/host/options-default.txt`) |
| `inputs.py` | `Buttons(enum.IntFlag)` with libctru names and values (`A=1<<0, B=1<<1, SELECT=1<<2, START=1<<3, DRIGHT=1<<4, DLEFT=1<<5, DUP=1<<6, DDOWN=1<<7, R=1<<8, L=1<<9, X=1<<10, Y=1<<11, ZL=1<<14, ZR=1<<15`; aliases `RIGHT, LEFT, UP, DOWN`); `Touch(x, y)` and the constant `Touch.up`; `Circle(x, y)` (up positive, -32767..32767); `Held` (the whole held state); `fold(inputs, frames, held) -> (array('i'), Held)` |
| `results.py` | frozen dataclasses `Shot(frame, top, bottom)`, `RunResult(frames, stopped_by, first_frame, last_frame, frame_total, vblanks, wall_s, message, shots)`, `SaveInfo(path, k, frame_total)`, `Stats(...)` |
| `errors.py` | the classes of 4.5 and `from_code(code, text)` |
| `emulator.py` | `Emulator` (4.6) |

Type hints and docstrings on every public name; stdlib only (numpy used when importable, Pillow never needed); no
module-level side effects except constants; every loop bounded.

### 4.2 Starting the worker (a refinement of PLAN 2.1's `-m libazahar._worker`)

```python
parent, child = multiprocessing.Pipe(duplex=True)
argv = [sys.executable, "-I", "-c",
        "import sys; sys.path.insert(0, sys.argv[2]); from libazahar._worker import main; sys.exit(main(int(sys.argv[1])))",
        str(child.fileno()), str(pkg_parent)]          # pkg_parent: the folder that holds libazahar/
proc = subprocess.Popen(argv, pass_fds=(child.fileno(),), stdin=subprocess.DEVNULL,
                        stdout=err_file, stderr=err_file, env=env, cwd=workdir)
child.close()
```
`-I` keeps the worker free of the user's site and `PYTHON*` variables (as PLAN wants) and still finds the package,
installed or not. `env` is `os.environ` plus `LAZ_MVK` (assumption A12: the library reads it) and
`LAZ_LOG_LEVEL` if the caller set it. No `multiprocessing` start method is used, so a script without a `__main__`
guard never re-launches itself. `err_file` is `<workdir>/worker.err` opened for append.

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
dead worker goes to the death mapping; for `run`, the heartbeat from the map is read every poll and its last change
time kept, and no change for `timeout` seconds (default 30) means `HostTimeout`; for `start`, the total wall time is
held to `boot_timeout` (default 300, first-run shader compiles); for `save_state` and `load_state`, total wall to
`timeout` plus 10 s (the drain may take 5 s). On a timeout the parent sends SIGKILL to its own worker (works on a
stopped one), reaps it with `wait`, and raises `HostTimeout(op, seconds, last message)`. EOF from `recv` goes to the
death mapping too. The loop is bounded by the timeouts.

Death mapping (return code from `proc.wait()`): 10 (`AZH_EXIT_GUEST_EXITED`): if the op was `run`, return a
`RunResult(stopped_by="guest_exited", frames=map frame_total - frame_total before the batch, message=map message)`
and mark the Emulator closed (the worker is gone); 11: `GuestError(map message)`; anything else (a negative code is a
signal): `HostCrashed(returncode, signal, message=map message, log_tail=last 20 lines of host.log,
err_tail=last 20 lines of worker.err)`.

### 4.5 Errors

`LibAzaharError(Exception)` is the base. `BootError` (AZH_E_BOOT, AZH_E_CORE, AZH_E_VULKAN during `start`),
`GuestError` (exit 11, or a `guest_error` stop on our core: raised with `.result` holding the `RunResult`; the
Emulator stays open), `HostTimeout`, `HostCrashed`, `StateError` (AZH_E_SAVESTATE), `NeedsLazpyCore`
(AZH_E_NEEDS_LAZPY_CORE), and **`HostError`** (a refinement: AZH_E_STATE call order, AZH_E_IO, AZH_E_NOMEM,
AZH_E_UNSUPPORTED, AZH_E_VULKAN outside `start`, an ABI mismatch). AZH_E_ARG becomes `ValueError` (the Python side
validates first, so it means a bug). `guest_break` and `guest_exited` are stop reasons, never errors. Every error
carries the host's text.

### 4.6 `Emulator`

```python
Emulator(app, workdir, *, sd_seed=None, state=None, core=None, options=None, timeout=30.0, boot_timeout=300.0)
```
- `workdir` is created if missing; inside it: `sys/` (the sysdir; the SD folder is `sys/Azahar/sdmc/`), `shots/`,
  `host.log`, `host.map`, `worker.err`. `sd_seed` (a folder, never named `sdmc`, PLAN 2.5) is copied with
  `shutil.copytree(..., symlinks=False, dirs_exist_ok=True)` into the SD folder **before** the boot without a state,
  and **after** the state boot with one (so seed files land on top of the snapshot; USING.md says so).
- `run(frames, inputs=(), shots=(), *, stop_file=None, stop_text=None, stop_every=30, stop_new=False,
  debug_text=None, wall_limit=None) -> RunResult`. `inputs` is an iterable of `(frame, item)`: item is `Buttons`/int
  (the whole button mask), `Touch(x, y)`, `Touch.up`, or `Circle(x, y)`; each changes only its part of the held state;
  sorted by frame (stable), folded into one full record per frame. Validation in Python first (`ValueError`, same rules
  as phase-c.md 3.4). `shots` are batch frames; `result.shots[f]` is a `Shot` whose paths are
  `shots/shot_<absolute frame %06d>_top.png` and `_bottom.png`. `wall_limit` is in seconds (float).
- `run_until(file, text, max_frames, *, every=30, new_only=False, inputs=(), shots=()) -> RunResult` is `run` with
  the SD rule; the caller checks `r.stopped_by == "sd_text"`.
- `run_frame()`, `set_keys(raw=...)` (libmgba-py's names), `set_input(buttons=None, touch=None, circle=None)`.
- `screens()`: one `azh_shot(BOTH, RAW, None)` round trip, then two read-only numpy views into the map
  (`(240, 400, 4)` and `(240, 320, 4)`, `uint8`, RGBA) if numpy imports, else two `bytes`. Views are valid until the
  next call on this Emulator (docstring says so).
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
| `pyproject.toml` | D1 | setuptools backend (`requires = ["setuptools>=68"]`), `[project] name = "libazahar-py"`, `version = "0.1.0.dev0"`, `requires-python = ">=3.10"`, `license = "GPL-3.0-or-later"`, optional extras `numpy`; `[tool.setuptools] package-dir = {"" = "python"}`, `packages = ["libazahar"]`; `[tool.pytest.ini_options] testpaths = ["tests/python"]`, `markers = ["slow: needs the emulator"]` |
| `tests/python/conftest.py` | D1 | puts `python/` and `tests/` on `sys.path`; fixtures `host_paths` (skip with a reason if `build/libazhost.dylib`, the stock core or `build/testapp.3dsx` is missing), `workdir` (a fresh `runs/d-pytest/<test name>/`), `seed(**control_keys)` (a seed folder built with `testapp_log.write_control`) |
| `tests/python/fakeworker.py` | D1 | a stand-in worker for `_client.py` tests: modes `ok`, `exit10`, `exit11`, `segv` (kills itself with SIGSEGV), `hang` (stops the heartbeat), `eof`; it writes a small `host.map` with the layout it is given |
| `tests/python/test_inputs.py`, `test_errors.py`, `test_map.py`, `test_client.py`, `test_abi.py` | D1 | pure or no-core tests (section 7) |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | D2 | section 3 (the stubs from C1 replaced) |
| `host/core.c` | D2, only if needed | section 3.5 |
| `tests/python/test_c_checks.py`, `test_live_errors.py`, `test_state.py`, `test_api.py` | D3 | section 8 |
| `docs/USING.md` | D3 | section 9 |
| item `docs/status/lazpy/1-in-progress/220-step-d-*.md` | any | "Lessons and notes" only |

C rules for `state.c`/`statemeta.c`: functions under about 60 lines, about 2 asserts each, no goto/recursion/setjmp,
bounded loops, every return checked, one owner per buffer.

## 6. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree** (no `dl/`, `vendor/`, `build/`): `mkdir -p dl && cp -R <main checkout>/dl/azahar
   <main checkout>/dl/moltenvk dl/`, `cp -R <main checkout>/vendor .`, `make` (the C1 code builds). Checkpoint:
   `make test-host` passes. **Run no emulator until D3.**
1. **D1, the Python package (about 0.75 h).** Section 4 modules, `pyproject.toml`, the D1 tests. Checkpoint:
   `python3 -m pytest -q tests/python -m "not slow"` passes; the venv check of gate 3.
2. **D2, savestates in C (about 0.4 h).** `statemeta.c` and its unit tests (format/parse round trip, every key
   missing once, an unknown key, a bad integer, an over-long value, an abi mismatch, a tmp-then-rename write and
   read); `state.c` per section 3 (it compiles and passes `make check`; it is exercised in D3); `core.c` if needed.
   Checkpoint: `make check && make && make test-host` clean. **Then report "D1+D2 done" to the main loop with the
   exact list of paths, and stop** (do not poll). The main loop merges main (with step C) into `step-d` and resumes you
   with SendMessage.
3. **D3, integration and docs (about 0.55 h, after C is merged).** `make` again (C2 and C3 are now in); the
   section 8 tests; launch the whole suite in the background (`nice -n 10 python3 -m pytest -q tests/python >
   runs/d-pytest.log 2>&1`) and be woken when it exits (never `sleep`-poll); while it runs, write `docs/USING.md`;
   the planted red; check `~/Library/Logs/DiagnosticReports` once for a new report naming `python3` from the SIGSEGV
   test (report it; do not delete anything). Checkpoint: gate 1-4 pass; quote the pytest summary.
4. The report (section 11).

## 7. Tests that need no emulator (D1, D2)

- `test_inputs.py`: `Buttons` values equal libctru's bits (the table in phase-c.md section 2); folding keeps each
  part (a `Touch` does not clear buttons; `Touch.up` keeps the last x, y but sets down 0); several items on one frame
  fold into one record; out-of-order input is sorted; validation errors (frame 0, beyond `frames`, a bad bit,
  x 320, y 240, circle 32768); the Python float32 touch model (`checks_c.touch_expected`) gives y - 1 exactly on rows
  63, 125, 126, 127.
- `test_errors.py`: every `AZH_E_*` code maps to its class (4.5); `GuestError.result` set.
- `test_map.py`: a synthetic `host.map` made with `struct` at the layout offsets; every reader returns its value;
  `close()` with a live `memoryview` does not raise.
- `test_client.py` (fake worker): `ok` round trip; `exit10` during `run` gives a `guest_exited` result and a closed
  client; `exit11` gives `GuestError`; `segv` gives `HostCrashed` with `signal == SIGSEGV` within 1 s of the death;
  `hang` with `timeout=1` gives `HostTimeout` and the pid is reaped; `eof` goes to the death mapping; `close()` twice is
  fine.
- `test_abi.py` (loads `build/libazhost.dylib` with ctypes in the test process; calls only `azh_abi_layout`):
  `check_layout` passes; a copy of the ctypes `Batch` with one field moved is caught.
- `tests/host/test_statemeta.c` (D2): as step 2 says.

## 8. Integration tests (D3; `@pytest.mark.slow`; each its own `workdir`; one Emulator alive at a time)

- `test_c_checks.py`: phase-c.md section 8's scenarios (a), (b), (c1-c3), (d), (e), (f) through `Emulator.run`,
  `run_until` and `RunResult`, with the same inputs, using `tests/checks_c.py` and `tests/testapp_log.py`; (f) expects
  `RunResult.stopped_by == "guest_exited"` and a closed Emulator; (c4) expects `NeedsLazpyCore`.
- `test_live_errors.py`: SIGSEGV: `threading.Timer(3.0, os.kill, (emu.pid, signal.SIGSEGV))` during
  `run(10_000_000)`; `HostCrashed` is raised and the time from the kill to the raise is under 1.0 s. SIGSTOP:
  `Emulator(..., timeout=3)`, `os.kill(pid, SIGSTOP)` from a timer during a long run; `HostTimeout` within 3 to 6 s;
  then `os.kill(pid, 0)` raises `ProcessLookupError`. Long batch: `run(200_000)` returns `stopped_by == "frames"` and
  `frames == 200_000` with the default timeout (several minutes at today's load; the heartbeat keeps moving).
- `test_api.py`: `screens()` shapes and dtype; a numpy view of the top screen shows the red marker at (0, 0)
  (B's table); `set_keys(raw=Buttons.A)` then `run(10)` logs `k=00000001`; `run_frame()` advances `frame_total` by 1;
  `save_state`/`load_state` on one instance: save, run 300 with inputs, load, run 300 with the same inputs: the same
  `v k tx ty td cx cy` fields; `SaveInfo.k >= 0`.
- `test_state.py`, **the state-boot gate** (PLAN Phase D): seed `boot_frames=6000`. Instance A: start the clock,
  `Emulator(app, wd_a, sd_seed=seed)`, `run_until("testapp/log.txt", "booted f=", max_frames=12_000)`, stop the clock
  (`t_boot`), `save_state(s)`, then `run(600, inputs=I, shots=[100, 300, 600])` where I presses buttons and touches
  points at fixed batch frames; read A's log. Instance B (after A is closed): start the clock,
  `Emulator(app, wd_b, state=s)`, stop the clock (`t_state`); B's `testapp/log.txt` equals `s.sd/testapp/log.txt`
  byte for byte; `B.frame_total == A`'s at the save; `run(600, inputs=I, shots=[100, 300, 600])`. Checks: B's shots
  pass `check_testapp.py markers --top --bottom --mode 2d`; for every per-frame line of A with `v` in
  `(v_save, v_save + 600]` (v_save = A's last per-frame `v` before the save plus k), B has a line with the same `v` and
  the same `k tx ty td cx cy`; `t_state < 0.10 * t_boot`. Both times and the ratio are printed (`-s` not needed:
  `print` to stderr is shown on failure; the test also writes them to `runs/d-pytest/state-times.txt`). The planted red
  (`LAZ_TEST_PLANT_RED=1`) compares A's lines against B's lines one `v` later.
- Assumption B6 (phase-2.md): if B's boot frames are idle, 6000 frames run in a few seconds and the ratio may fail on
  the core's fixed start cost; the builder reports the times and does not tune the test to pass.

## 9. `docs/USING.md` (D3; plain, short sections; no speed claims from the test app)

1. Install: `python3 -m venv .venv && .venv/bin/pip install -e .` (the worker runs `python -I`, so a venv, not the
   user site); `make` builds the host; `tools/fetch.sh` fetches the stock core and MoltenVK.
2. Paths and environment: `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE`, `LAZ_MVK`, `LAZ_PROFILE`, `LAZ_LOG_LEVEL`,
   `LAZ_ANY_CORE`; the instance folder layout.
3. Frames: one `run` frame is one guest VBlank; frames are 1-based in a batch; absolute frame numbers in shot names;
   `frame_total`.
4. Inputs: movie semantics, held across batches; folding; `Buttons` names = libctru; the offsets step C measured
   (buttons, ZL/ZR, circle, touch) as "the guest sees a change made at frame f in its log line of frame f + o".
5. Touch: pixel coordinates; the 4 rows table (`63 -> 62`, `125 -> 124`, `126 -> 125`, `127 -> 126`) and why (HID's
   float truncation, as in Qt Azahar); no cursor is drawn.
6. Circle pad: up positive; 32767 -> 154; the 3-poll averaging (one in-between frame).
7. Stops: every `stopped_by` value and what triggers it; SD text rule (every K frames, `new_only`, split matches,
   shrink); debug text needs our core.
8. Errors and timeouts: each class, when it is raised, `timeout` and `boot_timeout`.
9. Savestates: the three files; k and "a state at frame N is at N + k"; the SD snapshot and seed order; states may not
   survive a core change; the program id check.
10. Stock core and our core: what each gives (exact repeats, debug text, memory reads from Phase G, poll-exact movies
    if Phase F confirms `lazpy_movie_play`).
11. **The Gen3D mapping**: one table, rows 1-17 of `docs/research/gen3d-harness-needs.md`, each mechanism with its
    libazahar-py call (Qt profile pins -> `options`; SD staging -> `sd_seed`; locks/focus/curtain -> dropped; CTM
    movies -> `inputs` (poll-exact needs our core); SD control channel, netlogs, `voxel.log` -> `emu.sd` files and
    `run_until`; window screenshots -> `shots` / `screens()` with the 400x240 + 320x240 split; framebuffer via gdb ->
    `screens()`; gdb RAM reads -> Phase G `emu.memory` or an app log line; `gdbio resume` -> gone; savestates ->
    `save_state` and `Emulator(state=)`); then the forced-mode seed pattern (a seed folder holding the app's control
    file, so one Emulator boots straight into a mode, as the test app's `control.txt` shows) and state boot for the long
    world build (boot once, save, start every test from the state).

## 10. Machine-sharing rules

- D1 and D2 run no emulator (step C's builder is using the machine). In D3: one Emulator alive at a time (each test
  closes its own before the next starts; pytest runs serially, no `-n`), always nice'd (the worker calls
  `os.nice(10)`; the pytest process itself is started with `nice -n 10`), folders under `runs/d-*` (ignored).
- Never open a window: no Azahar app, no `open`, no Preview; PNGs with the Read tool.
- Signals go only to the worker pid our own Emulator reports; never `pkill`/`killall`; never another session's
  process.
- Background runs wake you on exit; no `sleep` polling. The 200,000-frame test is the long one; while it runs, write
  USING.md.

## 11. The builder's report

D1+D2 (the stop point): the paths; `make test-host` and the non-slow pytest summaries; the venv check output; any
header or C-file change D would need (none is allowed; report instead). D3: the full pytest summary (0 skipped), the
planted red, `t_boot`, `t_state` and the ratio, k from the saves, the warm-up count used, whether a crash report
appeared, line counts per file and the longest function; the runners block for `docs/map/runners.md`:
```
python3 -m venv .venv && .venv/bin/pip install -e .      # the Python package
nice -n 10 python3 -m pytest -q tests/python             # step D's tests (slow ones need the emulator)
build/azhost run <app> --frames N --save runs/x.state    # a state from the command line
```
Lines the main loop must add to `.gitignore` (expected: `.venv/` is already there; `*.egg-info/` and
`__pycache__/` if not).

## 12. Hours (agent wall time)

Builder 1.7 h (D1 0.75, D2 0.4, D3 0.55), the opus diff review 0.3 h, the commit 0.1 h: **2.10 h**, against PLAN.md's
2.25 (C's check functions are reused for "C through Python").

## 13. Review checklist (the opus as-built review)

1. ctypes structs match the frozen header field for field; `check_layout` compares every `fields[]` row; it runs
   when the worker loads the host.
2. Worker: `-I`, the explicit package root, `pass_fds`, child end closed in the parent, `os.nice(10)`, stdout/stderr
   to `worker.err`, no `multiprocessing` start method, bounded request loop, exits on EOF.
3. Wait loop: heartbeat timeout for `run`, total wall for `start` and states, SIGKILL only of its own worker, always
   reaped; death mapping for 10, 11, signals, EOF; error classes as 4.5; messages from the map.
4. Inputs: folding per part, one record per frame, validation equal to C's; Buttons equal libctru's bits.
5. Savestates: the order of 3.2 (k from the vblank counter, `frame_total += k`, meta last); restore order of 3.3
   (drain, SD replace, unserialize, counters); state boot reads the meta before any frame; tmp-then-rename for every
   file; one owner per buffer, freed on every path.
6. `statemeta.c` pure and strict; the unit tests cover every failure branch.
7. The state-boot test checks all of section 8 and prints the times; nothing tuned to pass; the planted red shown.
8. `screens()` views read-only and valid until the next call; close tolerant of live views.
9. Python rules: type hints, docstrings, stdlib only, bounded loops, no bare `except`, no module side effects.
10. USING.md covers section 9, the 4 rows, the measured offsets, the Gen3D table; no speed claims.
11. Nothing outside section 5 changed (no C file of step C, no header edit); no build outputs, PNGs, logs, states,
    `runs/` or the venv in the diff.

## 14. Interfaces assumed (from Phase 1 and step C)

From step C (frozen at C1, `docs/plans/phase-c.md` section 3): the header (ABI 2, `AZH_E_SAVESTATE`, `azh_result`
with `vblanks` and `message`, `azh_layout` with `fields[]`), the map offsets 1080-1104, the internal prototypes of
3.6 (`azh__run_one_frame`, `azh__counters_*`, `azh__vblanks_total`, `azh__sd_root`, `azh__copy_tree`,
`azh__clear_tree`, `azh__state_*`, `azh__meta_*`, `azh_state_meta`), `azh_boot` calling `azh__state_note_app` and
`azh__state_boot`, the `--save` flag, `tests/checks_c.py` and `tests/testapp_log.py`.
From Phase 1 (`docs/plans/phase-2.md` section 5): A1 (A's names and error codes), A4 (frames and shot names), A5
(the map), A11 and A12 (paths, the library reading `LAZ_MVK`), A14 (`core.c`'s table), A15 and B1 (the test app),
B2 (control keys, `boot_frames` up to 10,000), B3 (log lines, `booted`), B6 (busy boot frames), B8 (markers and
`check_testapp.py markers --top --bottom`). If the merged code differs in a name, follow the code and report; in
behaviour this brief relies on, stop and report.
