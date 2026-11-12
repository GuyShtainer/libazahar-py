# Step E: many copies at once, the machine-wide cap, and the speed table (item laz-310)

Brief for one sonnet builder, revision 0 (2026-11-12). Phase index: `docs/plans/phase-3.md` (order, ownership,
merges, departures, interfaces). Contract: `docs/PLAN.md:296` ("Phase E") and section 2.8. Where this brief
disagrees with PLAN.md on a goal, PLAN.md wins: stop and report (except the approved departures P1-P8 of
phase-3.md section 5 and phase-2.md section 5, which you follow).

You work in `../libazahar-py-e` (branch `step-e`, made at main after Phase 2 merged). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. **Never commit, never edit item files, never
write in MAIN.** Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, `docs/map/README.md`, phase-3.md sections
2, 3 and 6, phase-d.md sections 4 and 8 (the Python package you extend), `~/.claude/python-golden-rules.md`, and for
the two C edits `~/.claude/c-golden-rules.md`.

## 1. Goal and gate

Deliver `Pool`, the machine-wide slot cap, the workers held to it, `LoadWarning`, two cheap host wins, and the speed
table. The gate (all headless, this Mac):

1. `make check && make && make test-host` clean; `python3 -m pytest -q tests/python -m "not slow"` passes (D's
   tests plus `test_slots.py` and `test_pool.py`).
2. `LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_pool_live.py` passes with 0
   skipped:
   - **g1**: 3 Emulators boot at once and a 4th, started in a thread under cap 3, is still waiting (no `host.map`, no
     `slot.txt` in its workdir) 3 s later;
   - **g2**: SIGKILL of one of the 3 workers lets the 4th acquire its slot within 1.0 s of the kill (measured from
     `os.kill` to the time in the 4th's `slot.txt`), and the 4th then boots and runs 60 frames;
   - **g3**: `Pool(3)` runs 3 jobs with seeds `ready_at` 100, 200, 300: each job's `host.log`, SD `log.txt` and
     shots are in its own workdir, each log's `start` line carries its own `ready_at` and its `ready f=` line its own
     frame, no file of one job names another job's folder, and every frame-300 shot passes `check_testapp.py
     markers --mode 2d`;
   - **g4**: every live worker reports nice 10 (`ps -o nice= -p <pid>`).
3. `python3 -I tools/speed_table.py ...` (section 7) writes `runs/e-speed/table.md` and `table.json`, the guest-time
   check passes on every row, and `docs/research/speed-table-e.md` holds the table, the host share, the round-trip
   rows, the load, the date, and the default cap chosen by section 7's rule.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`)

- One frame is 4,481,136 guest ticks; the clock is 268,111,856 Hz (SRC core/core_timing.h:37, 40-42). One
  `retro_run` is one VBlank (PLAN 2.8), so x real time = host fps / 59.831.
- The log's `s=` is `svcGetSystemTick` (testapp/source/main.c:149; record.c:58-61). Its start is random on the
  stock core (SRC core/core_timing.cpp:37-44) and fixed on ours, but its **deltas** are guest time on both, so
  `Δs / 268,111,856` is guest seconds.
- In 3D mode the app's `v` is `C3D_FrameCounter(0)` (testapp/source/scene3d.c:82-85), so `v == f` (item 130): the
  app's own frame rate is `Δf / wall`; frames it misses show as `Δf < Δvblanks`.
- The app logs one SD line per frame (synchronous on the emulator thread, phase-2.md SD); that I/O is part of the
  test app's cost and the reason its numbers are "light", not a game's (rules.md 7).
- `flock(2)` on macOS: the lock belongs to the open file description, so two `open`s of one file in one process
  conflict; an fd inherited by a child keeps the lock after the parent closes its copy; the kernel drops it when the
  child dies. Python opens files non-inheritable (PEP 446); `subprocess.Popen(pass_fds=...)` makes exactly those fds
  inheritable in the child and `close_fds=True` (the default) closes the rest.
- D's worker already calls `os.nice(10)` (phase-d 4.1) and A's readback runs only on asked frames (phase-3.md A9);
  C gives raw frames (`screens()`): three of PLAN's items are already true and are only checked here.
- A's `png.c` calls `compress2` at level 6 (phase-a "4. Files"; read it in the merged code to find the line).
- This Mac: 12 cores, 18 GB, load around 17-24 when this was planned; `os.cpu_count()` is 12, so the load warning is
  above 24.

## 3. The design

### 3.1 `python/libazahar/_slots.py` (new; stdlib only: `os`, `fcntl`, `time`, `pathlib`)

```python
DEFAULT_CAP = 3
def slot_dir() -> Path          # LAZ_SLOT_DIR, else ~/Library/Caches/libazahar-py/slots; mkdir(mode=0o700, parents, exist_ok)
def cap() -> int                # LAZ_MAX_INSTANCES, int 1..64, else ValueError naming the variable; default 3
def acquire(timeout: float | None = None) -> Slot
class Slot:                     # .index, .fd, .path, .waited_s; .release() closes the fd (idempotent); context manager
```
- `acquire`: `timeout` None means `LAZ_SLOT_TIMEOUT` (float seconds, default 3600). Loop: for k in 0..cap-1, `fd =
  os.open(dir / f"slot-{k}.lock", os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)`, `fcntl.flock(fd, LOCK_EX |
  LOCK_NB)`; success returns the slot; `BlockingIOError` closes that fd and tries the next. After a full round with
  no slot, sleep 0.1 s and go again, bounded by the deadline (an explicit maximum round count derived from it, Python
  rule on bounded loops). Past the deadline: `HostTimeout("slot", timeout, "all <cap> libazahar slots are held; see
  <dir>")`. On success, write nothing into the lock file (the lock is the state).
- One `LoadWarning` per `acquire` when `os.getloadavg()[0] > 2 * os.cpu_count()`: `warnings.warn(LoadWarning(
  "load <l> is above 2 x <n> cores; other sessions' emulators share this Mac"), stacklevel=3)`.
- `class LoadWarning(UserWarning)` lives in `_slots.py` (D's `errors.py` holds errors, and E does not edit it) and
  is exported from `__init__`.

### 3.2 The worker holds its slot (`python/libazahar/_client.py`, D's spawn)

In D's spawn (phase-d 4.2), before `Popen`: `slot = _slots.acquire()`. Then `pass_fds=(child.fileno(), slot.fd)` and
append `str(slot.fd)` to the argv as `argv[3]` (D's `-c` text reads only `argv[1]` and `argv[2]`, so the worker needs
no change; the number shows in `ps` for whoever debugs a held slot). Right after `Popen` returns, `slot.release()`
in the parent (the child keeps the lock). If `Popen` raises, release and re-raise. Write `<workdir>/slot.txt`
**after** `Popen`: `slot=<k> pid=<worker pid> acquired=<time.time() at the lock, 6 decimals> waited_s=<x>`. Change
nothing else in `_client.py`. The workdir is known at spawn (D's cwd); if D's spawn function does not receive it,
add one keyword argument and report that edit.

Consequences you document in the docstring: the slot is free the moment the worker dies, however it dies; the
parent never holds a lock, so a parent killed with SIGKILL leaks nothing; `Emulator.close()` frees the slot by
reaping its worker (D's close).

### 3.3 `python/libazahar/pool.py` (new)

```python
class Pool:
    def __init__(self, n: int, app, root, *, factory=None, **emulator_kwargs): ...
    def submit(self, fn, item, **overrides) -> concurrent.futures.Future
    def map(self, fn, items, **overrides) -> list      # results in item order; the first exception is raised after all jobs end
    def close(self, wait=True) / __enter__ / __exit__
```
- `n` 1..64 (`ValueError`); `root` is created and resolved. If `n > _slots.cap()`, one plain
  `warnings.warn(UserWarning("Pool(<n>) > cap <c>: at most <c> run at once; the rest wait for a slot"))`. One
  `LoadWarning` at construction if the load is high (3.1's test).
- A `ThreadPoolExecutor(max_workers=n, thread_name_prefix="libazahar-pool")`. Each job `i` (a counter under a lock,
  starting at 0): `workdir = root / f"job-{i:04d}"`; `kwargs = {**emulator_kwargs, **overrides}`; `with
  (factory or Emulator)(app, workdir, **kwargs) as emu: return fn(emu, item)`. So each job gets a fresh instance in
  its own folder (PLAN 2.8: `workdir/sys/Azahar/sdmc`, `nand` (the core makes `sys/Azahar/nand`), `shots/`,
  `host.log`, `host.map`), closed (worker reaped, slot freed) even when `fn` raises. A job's `sd_seed`, `state` or
  `options` come in `overrides`.
- `factory` is for the pure tests (a fake Emulator); the docstring says so.
- Docstring example (USING.md gets the same lines in G or H, not here): `with Pool(3, app, "runs/x") as p: rs =
  p.map(job, seeds, sd_seed=...)`.

### 3.4 The two C edits

- `host/png.c`: the level is `LAZ_PNG_LEVEL` read once (0-9 by `strtol` with end and range checks; anything else
  logs one warning and uses the default), **default 1** (PLAN "zlib level 1"). One host.log line at the first PNG:
  `png level=<n>`.
- `host/run.c`: at the end of every batch (every exit of the batch function that returns 0) one host.log line:
  `batch frames=<n> wall_ms=<batch wall> core_ms=<sum of retro_run walls> host_ms=<wall - core> shot_ms=<sum of the
  PNG and RAW shot walls> stop=<reason>`. `CLOCK_MONOTONIC` around each `retro_run`; the sums in `int64` ns. Callbacks
  the core calls from inside `retro_run` (video refresh, input poll, log) count as core time; the docstring and the
  report say so. Do not change the batch logic.

### 3.5 What stays as it is

D's `os.nice(10)` (checked by g4), A's readback only on asked frames, C's raw frames, the Emulator's folders (D 4.6).
If any of these is not true in the merged code, report it; do not fix it in E.

## 4. Files (you create or edit only these)

| Path | Step | Role |
|---|---|---|
| `python/libazahar/_slots.py`, `python/libazahar/pool.py` | E1 | section 3 |
| `python/libazahar/_client.py` | E1 | section 3.2 only |
| `python/libazahar/__init__.py` | E1 | export `Pool`, `LoadWarning` |
| `host/png.c`, `host/run.c` | E1 | section 3.4 only |
| `tools/speed_table.py` | E1 (written), E2 (run) | section 7 |
| `tests/python/test_slots.py`, `tests/python/test_pool.py` | E1 | section 5 |
| `tests/python/test_pool_live.py` | E1 (written), E2 (run) | section 6 |
| `docs/research/speed-table-e.md` | E2 | section 7 |

**In E2 you edit none of `__init__.py`, `_client.py`, `host/run.c`, `host/png.c`** (step G's worktree carries E1's
versions of them, phase-3.md section 2). A bug found there in E2 goes in your report with the fix you propose; the
main loop decides. Everything else is outside your files (phase-3.md section 3).

## 5. Tests that need no emulator (E1)

`tests/python/test_slots.py` (each test sets `LAZ_SLOT_DIR` to its own `tmp_path` with `monkeypatch`, never the
real folder):
- s1: with cap 3, three `acquire()`s give indices {0, 1, 2}; a 4th with `timeout=0.3` raises `HostTimeout` after
  0.3-1.0 s; after one `release()`, a 4th succeeds at once with that index.
- s2: the kill test: `acquire()` with cap 1; spawn `[sys.executable, "-I", "-c", "import time; time.sleep(60)"]`
  with `pass_fds=(slot.fd,)`; `slot.release()` in the parent; `acquire(timeout=0.3)` raises; `os.kill(pid,
  SIGKILL)`, `wait()`; `acquire(timeout=2)` succeeds and the time from the kill is under 1.0 s (printed).
- s3: `LAZ_MAX_INSTANCES` values "0", "65", "x" raise `ValueError` naming the variable; "5" gives 5; unset gives 3.
- s4: the slot folder is created mode 0700, lock files 0600.
- s5: `LoadWarning` is warned when `os.getloadavg` is patched to return `(1000, 0, 0)`, and not at `(0, 0, 0)`.
- s6: D's fake worker (phase-d `fakeworker.py`, mode `ok`) spawned through `_client` under cap 1 holds the slot (a
  second `acquire(timeout=0.3)` raises) and frees it when the fake exits; `slot.txt` has the four keys.

`tests/python/test_pool.py` (a fake Emulator class with `__enter__`, `__exit__`, `close` that records calls):
- p1: `map(fn, range(7))` with n=3 returns the 7 results in order, made in workdirs `job-0000` .. `job-0006`.
- p2: a job that raises: `map` raises it after every job ended; every fake was closed.
- p3: `overrides` reach the factory (`sd_seed`, `state`); `emulator_kwargs` too; overrides win.
- p4: `Pool(5)` under cap 3 warns once; `Pool(0)` and `Pool(65)` raise `ValueError`.

Checkpoint E1: section 1 gate 1 passes. Also time the `_slots` loop: 1,000 `acquire`/`release` pairs (printed).

## 6. The live tests (`tests/python/test_pool_live.py`, `@pytest.mark.slow`, E2)

Use D's `host_paths`, `workdir` and `seed` fixtures (phase-d 5). Two rules keep the gate honest on a shared Mac:
- **The cap under test is private**: a fixture sets `LAZ_SLOT_DIR` to `runs/e-pytest/slots/` (cleared first) and
  `LAZ_MAX_INSTANCES=3`.
- **The gate still obeys the machine-wide cap**: the same fixture first acquires 3 slots from the **real** folder
  (`_slots.acquire` with `LAZ_SLOT_DIR` unset, `timeout=1800`; it prints how long it waited) and holds them until
  teardown, so other libazahar users wait while the gate runs its 3 (later 4) instances.

g1-g4 as section 1 says. Details:
- g1/g2: start three `Emulator(app, workdir/"i<k>", sd_seed=seed(ready_at=...))` one after another and `run(60)`
  each (all three alive). Start the 4th in a `threading.Thread` that constructs its Emulator and runs 60 frames,
  storing the result or the exception. After 3.0 s: the thread is alive, the 4th workdir has no `slot.txt` and no
  `host.map`. Then `t_kill = time.time(); os.kill(emus[1].pid, SIGKILL)`. Join the thread (bounded, `boot_timeout`
  + 60 s); its `slot.txt`'s `acquired` minus `t_kill` is printed and must be under 1.0; its slot index equals the
  killed one's; its result has 60 frames. Close everything (`emus[1].close()` reaps the dead worker; D's close
  tolerates it).
- g3: `Pool(3, app, workdir/"pool")` and `map(job, [100, 200, 300])` where each job's seed is `seed(ready_at=r)` (pass
  it as the `sd_seed` override) and `job(emu, r)` runs 400 frames with a PNG shot at 300 and returns `(emu.sd /
  "testapp/log.txt").read_text()` plus the shot paths. Checks as section 1 says (parse with
  `testapp_log.parse_log`; markers with `check_testapp.py markers --top <png> --bottom <png> --mode 2d`, as D's
  tests call it).
- g4: inside g1 while the three are alive: `ps -o nice= -p <pid>` is `10` for each (strip spaces).
- Print the load average at the start and end of each test.

## 7. The speed table (`tools/speed_table.py`, E2)

Usage: `nice -n 10 python3 -I tools/speed_table.py --app build/testapp.3dsx --core <path> [--core <path2>]
--instances 1,2,3 --seconds 60 --out runs/e-speed [--state FILE --label NAME]`. It inserts the absolute
`<repo>/python` and `<repo>/tests` folders into `sys.path` first (`-I` implies `-P`, phase-2.md B12) and imports
`libazahar` and `testapp_log`. Instances go through the **real** slot folder (no private cap): a row waits for its n
slots and records the wait.

Per core and per n in the list (n instances at once):
1. n threads each make `Emulator(app, runs/e-speed/<core>-n<n>/i<k>, sd_seed=<a seed with draw=3d>)` and `run(300)`
   (warm-up: shader compiles, boot); a `threading.Barrier(n)`.
2. Each records: `os.getloadavg()`, `emu.stats()` (S0), the last complete per-frame log line (f0, s0), then
   `r = emu.run(10_000_000, wall_limit=seconds)` (one batch, `stopped_by == "wall_limit"` expected), then S1 and
   (f1, s1).
3. Per instance: `host_fps = r.frames / r.wall_s`; `app_fps = (f1 - f0) / r.wall_s`; `x_real = (s1 - s0) /
   268111856 / r.wall_s`; `ticks_per_vblank = (s1 - s0) / r.vblanks`; `cpu_ms = ((S1.user_s + S1.sys_s) - (S0.user_s
   + S0.sys_s)) * 1000 / r.frames` (the worker's rusage, which leaves out Metal GPU time, PLAN 2.8); `wall_ms =
   r.wall_s * 1000 / r.frames`; `peak_rss` from S1; the host share from the batch's host.log timing line
   (`host_ms / wall_ms`, section 3.4).
4. **The guest-time check** (rules.md 7): every instance's `ticks_per_vblank` is within 1 % of 4,481,136, and
   `x_real` is within 2 % of `host_fps / 59.831`. A failure marks the row `CHECK FAIL` and the table is not used for
   the cap.
5. Row: core, n, per-instance and total `host_fps`, `app_fps`, `x_real`, `cpu_ms`, `wall_ms`, host share, peak RSS,
   load at start and end, slot wait, date.

Two extra rows, one instance, our core if given else stock:
- **Round trip**: 600 x `run(1)` vs one `run(600)`: wall ms per frame for each, and the difference per call (the
  parent/worker cost Gen3D pays per small batch).
- **Shots**: 20 x `shot(prefix)` at `LAZ_PNG_LEVEL` 1 and 6 (a fresh Emulator for each level, since the level is
  read once): ms per shot and the bytes of one top PNG.

`--state FILE --label NAME` adds a row from a state boot (`Emulator(app, ..., state=FILE)`); this is the Gen3D row,
run only when the main loop's message gives the app and the state (phase-3.md Q1). Its shots are never taken and
nothing under it is committed.

Output: `runs/e-speed/table.json` (every number), `runs/e-speed/table.md` (one Markdown table per core plus the
extra rows), and the rc file: the whole E2 table run is started as
`sh -c 'trap "echo \$? > runs/e-speed.rc" EXIT; nice -n 10 python3 -I tools/speed_table.py ... > runs/e-speed.log 2>&1'`
with `run_in_background`, because step G's live gate waits on `runs/e-speed.rc` (phase-3.md section 2). Write the
rc file even if you stop early.

**The default cap, by a rule fixed now** (phase-3.md Q3): from the rows of the core Gen3D will use (ours if it ran,
else stock), let T(n) be the total `host_fps` at n instances. Keep **3** if T(3) >= 1.25 x T(2) and the load at the
end of the n=3 row is below 2 x cpu_count; else **2** if T(2) >= 1.25 x T(1); else **1**. Never above 3 (no
4-instance row). Write the rule, the numbers and the result. The cap is marked "provisional (light scene)" unless a
real-scene row exists.

`docs/research/speed-table-e.md`: the date, the commit, the cores and their versions, the Mac (cores, RAM), the
tables copied from `table.md`, the guest-time check per row, the host share of the shot-free batches (PLAN's target:
under 5 %; if over, say which part of `host_ms` is largest and stop there, no tuning), the round-trip and shot rows,
the cap rule and result, and one line: "Test-app numbers are a light scene (rules.md 7); spike 2's real 3D-field
numbers are in spike-2-real-scene.md." No speed claim beyond the table.

## 8. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree**: `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers azahar-src; do
   [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done` (link the children, never `dl/` itself), `cp -R MAIN/vendor .`;
   `make`; `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (or copy
   `MAIN/build/testapp.3dsx`). Checkpoint: `make test-host` and `python3 -m pytest -q tests/python -m "not slow"`
   pass before your edits (D's baseline; print the counts).
1. **E1 (about 0.4 h; no emulator).** Sections 3, 4 (E1 rows), 5; write `test_pool_live.py` and
   `tools/speed_table.py` but do not run them. Checkpoint: gate 1 passes; `python3 -I tools/speed_table.py --help`
   works. **Then end your run**: your final report is the "E1 done" report: the exact list of E1 paths, the test
   counts, the `_slots` timing, the `run.c` and `png.c` diffs in a few lines each, and anything in D's code that
   differed from phase-3.md section 6 (D2, D3, D6). Do not start E2. The main loop commits E1 and resumes you with
   "E1 committed at <sha>; F2's batch is over; go on with E2".
2. **E2 (about 0.4 h; timed).** Run only after the resume message (step F2's timed batch must be over; never beside
   the core build). First the live tests, then the table:
   - `sh -c 'trap "echo \$? > runs/e-pytest.rc" EXIT; LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs
     tests/python/test_pool_live.py > runs/e-pytest.log 2>&1'` with `run_in_background`; wait with Monitor until
     `runs/e-pytest.rc` exists (bounded 45 min).
   - The table as section 7 says, with both cores if `MAIN/build-core/azahar_lazpy_libretro.dylib` exists (pass
     its absolute path; read only) and the stock core `dl/azahar/azahar_libretro.dylib`; wait with Monitor on
     `runs/e-speed.rc` (bounded 60 min). Expected machine time: 2 cores x (1 + 2 + 3 instances) x (60 s + boot) plus
     the extra rows, about 15-20 min.
   - Write `docs/research/speed-table-e.md`. Checkpoint: gate 2 and 3 pass; quote them.
   Without Monitor: run the live tests one test per foreground call and the table one `--instances` value per call
   (`--instances 1`, `2`, `3`, then `--extra-rows`), each under the 10-minute limit; say so. Still write
   `runs/e-speed.rc` at the end (step G waits on it).
3. The report (section 10) ends the run. Stop every waiter and background task you started (TaskStop) first.

## 9. Machine-sharing rules

- E1 runs no emulator. E2 runs at most 3 instances at once, all through the slot cap (the live tests hold 3 real
  slots, section 6; the table uses the real folder), always nice'd (the worker's `os.nice(10)`, the pytest and
  table processes under `nice -n 10`), folders under `runs/e-*` (ignored).
- E2 never runs beside the core build, beside step F2's batch or beside step G's live gate (the resume message is
  the go-ahead; G waits for your rc file).
- Never open a window: no Azahar app, no `open`, no Preview; PNGs with the Read tool.
- Signals go only to worker pids your own Emulators report (g2's SIGKILL); never `pkill`/`killall`; never another
  session's process. Never delete files in the real slot folder.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 10. The builder's report

E1 (end of the first run): as step 1 says. E2: the live-test summary (0 skipped) and g2's kill-to-acquire time,
g1's 3 s check, g4's nice values, the real-slot wait; the speed tables as printed; the guest-time check per row; the
host share; the round-trip and shot rows; the load at each row; the cap and the rule's numbers; any `CHECK FAIL`;
line counts per new or edited file and the longest function; the runners block for `docs/map/runners.md`:
```
nice -n 10 python3 -I tools/speed_table.py --app build/testapp.3dsx --core <path> --instances 1,2,3 --seconds 60 --out runs/e-speed
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_pool_live.py   # step E's live gate
```
the line for `docs/map/tools.md` (`tools/speed_table.py`: the 1-2-3 instance speed table with the guest-time
check); lines for `.gitignore` (none expected: `runs/` is ignored); and a final **"Lessons and notes"** block, ready
to paste into item 310.

## 11. Hours (agent wall time)

Builder 0.8 h (E1 0.4, E2 0.4), the opus as-built review 0.2 h, the commit 0.1 h: **1.1 h**, against PLAN.md's 1.0.
The slot waits, the live tests and the table runs are machine time.

## 12. Review checklist (the opus as-built review)

1. `_slots.acquire` is bounded (a maximum round count), closes every fd it does not keep, never writes into a lock
   file, and raises `HostTimeout` with the folder named.
2. The parent closes its slot fd right after `Popen` (and on a `Popen` failure); `slot.txt` is written after
   `Popen`; `pass_fds` holds exactly the pipe fd and the slot fd.
3. No lock is held in the parent process for a live worker (check with `lsof -p <parent pid>` in the report, or by
   reading the code path).
4. `Pool` closes every Emulator on every path; results come back in item order; overrides win over kwargs.
5. The live tests use a private slot folder for the cap under test **and** hold 3 real slots; g2 measures from the
   kill to the acquire, not to the boot.
6. `run.c`'s timing line is written on every successful batch exit and does not change the batch's behaviour;
   `png.c`'s level is read once, validated, logged.
7. The table's guest-time check is computed as section 7 says; no row without it is used for the cap; the cap
   follows the fixed rule; test-app rows are labelled light; no speed claim outside the table.
8. E2 edited none of `__init__.py`, `_client.py`, `run.c`, `png.c`.
9. Python rules: type hints and docstrings on public names, bounded loops, no bare `except`, every opened fd closed
   on every path; C rules for the two edits (checked returns, no new globals beyond file statics).
10. Nothing committed by the builder; no item file touched; nothing written in MAIN.

## 13. Interfaces assumed

From phase-3.md section 6: A8, A9, A10, A11, B1-B4, B8, B9, D1-D4, D6, D7, D10, and the slot convention of
phase-3.md section 2. If D's spawn, worker argv, `Stats` fields or fixtures differ from those rows, follow the code
and report the difference.
