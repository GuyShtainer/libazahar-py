# Step E: many copies at once, the machine-wide cap, and the speed table (item laz-310)

Brief for one sonnet builder, revision 2 (2026-11-13, after review 2; final). Phase index: `docs/plans/phase-3.md`
(order, ownership, merges, departures, interfaces, Phase 2's holds H1-H7). Contract: `docs/PLAN.md:296` ("Phase E") and
section 2.8. Where this brief disagrees with PLAN.md on a goal, PLAN.md wins: stop and report (except the approved
departures P1-P8 and refinements R1-R4 of phase-3.md section 5 and phase-2.md section 5, which you follow; R2, the
4-instance row, and R3, no Gen3D row, are this step's).

You work in `../libazahar-py-e` (branch `step-e`, made at main after Phase 2 merged; before E2 the main loop merges
main, with step F2, into it). "MAIN" is `/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`.
**Never commit, never edit item files, never write in MAIN, never run `tools/build-core.sh`** (in a worktree its
build tree is the linked `dl/azahar-src/build-src`, MAIN's: a run would delete it and start a full build; the core
build is the main loop's, and step 0's rebuild runs while you do E1). Read first: the repo's `CLAUDE.md`,
`docs/map/rules.md`, `docs/map/README.md`, phase-3.md sections 2, 3 and 6, phase-d.md sections 4 and 8 (the Python
package you extend), `~/.claude/python-golden-rules.md`, and for the two C edits `~/.claude/c-golden-rules.md`.

## 1. Goal and gate

Deliver `Pool`, the machine-wide slot cap, the workers held to it, `LoadWarning`, `SlotTimeout`, a committed
one-slot command runner, two cheap host wins, and the speed table. The gate (all headless, this Mac):

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
   - **g4**: every live worker's nice is **at least 10** (`ps -o nice= -p <pid>`; hold H2: the worker raises itself
     to 10 only when the parent is nicer, so under `nice -n 10` it is exactly 10).
3. `python3 -I tools/speed_table.py ...` (section 7) writes `runs/e-speed/table.md` and `table.json`, the guest-time
   check passes on every row, and `docs/research/speed-table-e.md` holds the table (1, 2, 3 instances on each core
   and 4 on the cap's core), the host share, the round-trip and shot rows, the load, the workers' nice and the
   effective option set per core, the date, and the default cap chosen by section 7's rule, which `_slots.py`'s
   `DEFAULT_CAP` then holds.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`)

- One frame is 4,481,136 guest ticks; the clock is 268,111,856 Hz (SRC core/core_timing.h:37, 40-42). One
  `retro_run` is one VBlank (the VBlank callback presents, the present ends the loop: gpu.cpp:488-498,
  citra_libretro/emu_window/libretro_window.cpp:68-71 and :327-331, the loop citra_libretro.cpp:282-306), so x real
  time = host fps / 59.831.
- The log's `s=` is `svcGetSystemTick` (testapp/source/main.c:149; record.c:58-61). Its start is random on the
  stock core and fixed on ours, but its **deltas** are guest time on both, so `Δs / 268,111,856` is guest seconds.
- In 3D mode the app's `v` is `C3D_FrameCounter(0)` (testapp/source/scene3d.c:82-85), so `v == f`: the app's own
  frame rate is `Δf / wall`; frames it misses show as `Δf < Δvblanks`.
- The app logs one SD line per frame (synchronous on the emulator thread); that I/O is part of the test app's cost
  and the reason its numbers are "light", not a game's (rules.md 7). On our core `instant_debug_log` also flushes the
  log per guest line (SRC common/logging/backend.cpp:353-357): the our-core rows carry that cost, as users will.
- `flock(2)` on macOS: the lock belongs to the open file description, so two `open`s of one file in one process
  conflict; an fd inherited by a child keeps the lock after the parent closes its copy; the kernel drops it when the
  child dies. Python opens files non-inheritable (PEP 446); `subprocess.Popen(pass_fds=...)` makes exactly those fds
  inheritable in the child and `close_fds=True` (the default) closes the rest; with `pass_fds` Python uses
  fork+exec, so a sibling thread's child never keeps a slot fd past `exec`.
- D's worker nice is at least 10 (hold H2) and A's readback runs only on asked frames (phase-3.md A9); C gives raw
  frames (`screens()`): three of PLAN's items are already true and are only checked here.
- `host/png.c` is a **pure** module (stdlib and zlib only) built into `build/test-host` (`Makefile:42` `TEST_SRC` after
  D's merge), so it must not call `azh_log`; its level is `#define PNG_LEVEL 6` (`png.c:11`), used by `compress2`
  (`:136`).
- D's `HostTimeout(op, seconds, message)` prints its third argument as "(last guest message: ...)"
  (`errors.py:32-36`); a slot timeout needs its own text (3.1).
- host.log has one `option <key>=<value>` line per registered key at boot (`host/options.c:164`): the effective
  option set.
- `python3 -I` ignores `PYTHONPATH` and the current folder, so `python3 -I -m libazahar._slots` cannot find the
  package; a tool under `tools/` inserts `<repo>/python` into `sys.path` itself (phase-2.md B12).
- This Mac: 12 cores, 18 GB, load around 17-24 when this was planned; `os.cpu_count()` is 12, so the load warning is
  above 24.

## 3. The design

### 3.1 `python/libazahar/_slots.py` (new; stdlib plus `errors.HostTimeout`)

```python
DEFAULT_CAP = 3                 # E2 sets it from section 7's rule (1..4); nothing else reads a literal 3
def slot_dir() -> Path          # LAZ_SLOT_DIR, else ~/Library/Caches/libazahar-py/slots; mkdir(mode=0o700, parents, exist_ok)
def cap() -> int                # LAZ_MAX_INSTANCES, int 1..64, else ValueError naming the variable; default DEFAULT_CAP
def acquire(timeout: float | None = None) -> Slot
class Slot:                     # .index, .fd, .path, .waited_s; .release() closes the fd (idempotent); context manager
class SlotTimeout(HostTimeout)  # str(): "no libazahar slot free after <s> s: all <cap> are held; see <dir>"
class LoadWarning(UserWarning)
```
- **`slot_dir()`, `cap()` and the timeout read the environment on every call**, never at import (review 1 S5), so a
  test or a tool may change them between acquisitions.
- `acquire`: `timeout` None means `LAZ_SLOT_TIMEOUT` (float seconds, default 3600). Loop: for k in 0..cap-1, `fd =
  os.open(dir / f"slot-{k}.lock", os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)`, `fcntl.flock(fd, LOCK_EX |
  LOCK_NB)`; success returns the slot; `BlockingIOError` closes that fd and tries the next. After a full round with
  no slot, sleep 0.1 s and go again, bounded by the deadline (an explicit maximum round count derived from it, Python
  rule on bounded loops). Past the deadline: `raise SlotTimeout(timeout, cap, dir)`. On success, write nothing into
  the lock file (the lock is the state).
- `SlotTimeout` subclasses D's `HostTimeout` (so `except HostTimeout` still catches it) and sets its own message: call
  `HostTimeout.__init__` as D's signature needs (with no guest message) and override `__str__`; check D's class in
  the merged code and report what you did.
- One `LoadWarning` per `acquire` when `os.getloadavg()[0] > 2 * os.cpu_count()`: `warnings.warn(LoadWarning(
  "load <l> is above 2 x <n> cores; other sessions' emulators share this Mac"), stacklevel=3)`. `LoadWarning` and
  `SlotTimeout` live in `_slots.py` (E does not edit `errors.py`) and are exported from `__init__`.
- The module docstring says: the cap is machine-wide only if every user reads the same `LAZ_MAX_INSTANCES` (a
  process with cap 5 takes slots 3 and 4 beside three cap-3 users) (review 1 N8).

### 3.2 The worker holds its slot (`python/libazahar/_client.py`, D's spawn)

`WorkerClient.__init__` gains one keyword, `slot: bool | None = None` (review 2 B3): `None` means "take a slot only
for the real worker" (D's `argv` callable is `None`); `True` takes one for a fake worker too; `False` never takes
one. D's fake-worker tests (`test_client.py`) pass no keyword, so they never touch the real slot folder or the cap,
and the non-slow suite never waits behind a running pool. The docstring says so.

When a slot is taken, in D's spawn, before `Popen`: `slot = _slots.acquire()`. Then `pass_fds=(child.fileno(), slot.fd)`
and append `str(slot.fd)` to the argv as `argv[3]` (D's `-c` text reads only `argv[1]` and `argv[2]`, so the worker
needs no change; the number shows in `ps` for whoever debugs a held slot). Right after `Popen` returns, `slot.release()`
in the parent (the child keeps the lock). If `Popen` raises, release and re-raise. Write `<workdir>/slot.txt`
**after** `Popen`: `slot=<k> pid=<worker pid> acquired=<time.time() at the lock, 6 decimals> waited_s=<x>`. D's
spawn already closes both pipe ends when `Popen` raises (`except BaseException`); put the slot's release in that
same `except`. With no slot taken, the argv, `pass_fds` and `slot.txt` stay as D's. Change nothing else in
`_client.py`. The spawn knows the workdir (D's cwd, `self.workdir`); the fake worker's argv is a
callable, so appending the slot fd works for both.

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
  its own folder (PLAN 2.8: `workdir/sys/Azahar/sdmc`, `nand`, `shots/`, `host.log`, `host.map`), closed (worker
  reaped, slot freed) even when `fn` raises. A job's `sd_seed`, `state` or `options` come in `overrides`.
- `factory` is for the pure tests (a fake Emulator); the docstring says so.
- Docstring example: `with Pool(3, app, "runs/x") as p: rs = p.map(job, seeds, sd_seed=...)`.

### 3.4 The two C edits

- `host/png.c` (stays pure): `int azh_png_level(void)`: on its first call reads `LAZ_PNG_LEVEL` with `getenv` and
  `strtol` (end and range checks, 0-9), remembers the level and whether the text was bad (file statics), and
  returns the level; **default 1** (PLAN "zlib level 1"); a bad value gives 1. A second function or an out-parameter
  tells the caller the text was bad (your choice; one line in `azh_pure.h` per prototype). `compress2` uses
  `azh_png_level()`. No logging in `png.c`.
- `host/run.c`: once per process, at the first batch, one host.log line `png level=<n>` (plus ` (bad LAZ_PNG_LEVEL
  "<text>", using 1)` when bad). At the end of every batch (every exit of the batch function that returns 0) one
  host.log line: `batch frames=<n> wall_ms=<batch wall> core_ms=<sum of retro_run walls> host_ms=<wall - core>
  shot_ms=<sum of the PNG and RAW shot walls> stop=<reason>`. `CLOCK_MONOTONIC` around each `azh__run_one_frame`'s
  `retro_run`; the sums in `int64` ns. Callbacks the core calls from inside `retro_run` (video refresh, input poll,
  log) count as core time; the docstring and the report say so. Do not change the batch logic.

### 3.5 `tools/hold_slot.py` (new, about 25 lines; review 1 N7)

`python3 -I tools/hold_slot.py [--timeout S] -- CMD [ARG...]`: inserts the absolute `<repo>/python` into `sys.path`,
`slot = _slots.acquire(timeout)`, prints `hold_slot: slot=<k> waited_s=<x>` to stderr, `os.set_inheritable(slot.fd,
True)`, then `os.execvp(CMD, [CMD, ARG...])`: the lock lives on in the command's process and dies with it. Exit 2 with
a usage line when no command follows `--`. Step G and the phase-end suite run azhost commands under it.

### 3.6 What stays as it is

D's worker nice (checked by g4), A's readback only on asked frames, C's raw frames, the Emulator's folders. If any of
these is not true in the merged code, report it; do not fix it in E.

## 4. Files (you create or edit only these)

| Path | Step | Role |
|---|---|---|
| `python/libazahar/_slots.py`, `python/libazahar/pool.py`, `tools/hold_slot.py` | E1 | section 3; in E2 only the value of `DEFAULT_CAP` changes |
| `python/libazahar/_client.py` | E1 | section 3.2 only |
| `python/libazahar/__init__.py` | E1 | export `Pool`, `LoadWarning`, `SlotTimeout` |
| `host/png.c`, `host/run.c`, `host/azh_pure.h` | E1 | section 3.4 only (`azh_pure.h`: the prototype lines) |
| `tools/speed_table.py` | E1 (written), E2 (run) | section 7 |
| `tests/python/test_slots.py`, `tests/python/test_pool.py` | E1 | section 5 |
| `tests/python/test_pool_live.py` | E1 (written), E2 (run) | section 6 |
| `docs/research/speed-table-e.md` | E2 | section 7 |

**In E2 you edit none of `__init__.py`, `_client.py`, `host/run.c`, `host/png.c`, `host/azh_pure.h`** (step G's
worktree carries E1's versions of them, phase-3.md section 2). A bug found there in E2 goes in your report with the
fix you propose; the main loop decides. Everything else is outside your files (phase-3.md section 3).

## 5. Tests that need no emulator (E1)

`tests/python/test_slots.py` (each test sets `LAZ_SLOT_DIR` to its own `tmp_path` with `monkeypatch`, never the
real folder):
- s1: with cap 3, three `acquire()`s give indices {0, 1, 2}; a 4th with `timeout=0.3` raises `SlotTimeout` (also an
  instance of `HostTimeout`) after 0.3-1.0 s, and its text names the folder and the cap; after one `release()`, a
  4th succeeds at once with that index.
- s2: the kill test: `acquire()` with cap 1; spawn `[sys.executable, "-I", "-c", "import time; time.sleep(60)"]`
  with `pass_fds=(slot.fd,)`; `slot.release()` in the parent; `acquire(timeout=0.3)` raises; `os.kill(pid,
  SIGKILL)`, `wait()`; `acquire(timeout=2)` succeeds and the time from the kill is under 1.0 s (printed).
- s3: `LAZ_MAX_INSTANCES` values "0", "65", "x" raise `ValueError` naming the variable; "5" gives 5; unset gives
  `_slots.DEFAULT_CAP`; a value set **after** the module was imported is seen by the next `cap()` call (S5).
- s4: the slot folder is created mode 0700, lock files 0600.
- s5: `LoadWarning` is warned when `os.getloadavg` is patched to return `(1000, 0, 0)`, and not at `(0, 0, 0)`.
- s6: D's fake worker (mode `ok`) spawned through `_client` with **`slot=True`** under cap 1 and a private
  `LAZ_SLOT_DIR` (monkeypatch) holds the slot (a second `acquire(timeout=0.3)` raises) and frees it when the fake
  exits; `slot.txt` has the four keys. The same fake with no keyword writes no `slot.txt` and leaves the folder's
  lock files free.
- s7: `tools/hold_slot.py` under cap 1 runs `python3 -I -c "import time; time.sleep(60)"`; meanwhile
  `acquire(timeout=0.3)` raises; after SIGKILL of that child, `acquire(timeout=2)` succeeds; with nothing after `--`
  it exits 2.

`tests/python/test_pool.py` (a fake Emulator class with `__enter__`, `__exit__`, `close` that records calls):
- p1: `map(fn, range(7))` with n=3 returns the 7 results in order, made in workdirs `job-0000` .. `job-0006`.
- p2: a job that raises: `map` raises it after every job ended; every fake was closed.
- p3: `overrides` reach the factory (`sd_seed`, `state`); `emulator_kwargs` too; overrides win.
- p4: `Pool(5)` under cap 3 warns once; `Pool(0)` and `Pool(65)` raise `ValueError`.

Checkpoint E1: section 1 gate 1 passes.

## 6. The live tests (`tests/python/test_pool_live.py`, `@pytest.mark.slow`, E2)

Use D's `host_paths`, `workdir` and `seed` fixtures. Two rules keep the gate honest on a shared Mac, in this order
inside one fixture (review 1 S5):
1. **The gate obeys the machine-wide cap**: with `LAZ_SLOT_DIR` and `LAZ_MAX_INSTANCES` **unset** (the real folder,
   the default cap), acquire 3 slots (`_slots.acquire(timeout=1800)`, printing how long it waited) and hold them
   until teardown, so other libazahar users wait while the gate runs its instances (at most 3 alive at once).
2. **Then the cap under test is private**: `monkeypatch.setenv("LAZ_SLOT_DIR", runs/e-pytest/slots/)` (cleared
   first) and `monkeypatch.setenv("LAZ_MAX_INSTANCES", "3")`. Because `_slots` reads both on every call, the
   Emulators of the test use the private folder.

g1-g4 as section 1 says. Details:
- g1/g2: start three `Emulator(app, workdir/"i<k>", sd_seed=seed(ready_at=...))` one after another and `run(60)`
  each (all three alive). Start the 4th in a `threading.Thread` that constructs its Emulator and runs 60 frames,
  storing the result or the exception. After 3.0 s: the thread is alive, the 4th workdir has no `slot.txt` and no
  `host.map`. Then `t_kill = time.time(); os.kill(emus[1].pid, SIGKILL)`. Join the thread (bounded, `boot_timeout`
  + 60 s); its `slot.txt`'s `acquired` minus `t_kill` is printed and must be under 1.0; its slot index equals the
  killed one's; its result has 60 frames. Close everything (`emus[1].close()` reaps the dead worker).
- g3: `Pool(3, app, workdir/"pool")` and `map(job, [100, 200, 300])` where each job's seed is `seed(ready_at=r)` (pass
  it as the `sd_seed` override) and `job(emu, r)` runs 400 frames with a PNG shot at 300 and returns `(emu.sd /
  "testapp/log.txt").read_text()` plus the shot paths. Checks as section 1 says (parse with
  `testapp_log.parse_log`; markers through `d_helpers.markers_ok`).
- g4: inside g1 while the three are alive: `int(ps -o nice= -p <pid>) >= 10` for each; print the values.
- Print the load average at the start and end of each test.

## 7. The speed table (`tools/speed_table.py`, E2)

Usage: `nice -n 10 python3 -I tools/speed_table.py --app build/testapp.3dsx --core <path> [--core <path2>]
[--cap-core <path>] [--instances 1,2,3,4] [--seconds 60] [--extra-rows | --only-extra] --out runs/e-speed`. It
inserts the absolute `<repo>/python` and `<repo>/tests` folders into `sys.path` first and imports `libazahar` and
`testapp_log`. `--cap-core` defaults to the core whose file name holds "lazpy" if one is given, else the first
`--core`. **4-instance rows run only on the cap core**; the other cores stop at 3. `--extra-rows` adds the two extra
rows after the tables; `--only-extra` runs only them. No state-row option (Guy, Q1).

Slots: instances go through the **real** slot folder. The script sets `os.environ["LAZ_MAX_INSTANCES"] = "4"` for
itself before any acquisition, so the n=4 row can hold slots 0-3; while it does, every cap-3 user finds slots 0-2
held and waits. A row waits for its n slots and records the wait (a cap-3 user already holding a slot makes the n=4
row wait, which is correct).

Per core and per n (n instances at once):
1. n threads each make `Emulator(app, runs/e-speed/<core>-n<n>/i<k>, sd_seed=<a seed with draw=3d>)` and `run(300)`
   (warm-up: shader compiles, boot); then a `threading.Barrier(n, timeout=1800 + boot_timeout)`. A broken barrier
   (`BrokenBarrierError`) ends the row as `CHECK FAIL slot` with the per-instance state, never a hang (N5).
2. Each records: `os.getloadavg()`, `emu.stats()` (S0), the last complete per-frame log line (f0, s0), then
   `r = emu.run(10_000_000, wall_limit=seconds)` (one batch, `stopped_by == "wall_limit"` expected), then S1 and
   (f1, s1), and its worker's nice (`ps -o nice= -p <emu.pid>`).
3. Per instance: `host_fps = r.frames / r.wall_s`; `app_fps = (f1 - f0) / r.wall_s`; `x_real = (s1 - s0) /
   268111856 / r.wall_s`; `ticks_per_vblank = (s1 - s0) / r.vblanks`; `cpu_ms = ((S1.user_s + S1.sys_s) - (S0.user_s
   + S0.sys_s)) * 1000 / r.frames` (the worker's rusage, which leaves out Metal GPU time, PLAN 2.8); `wall_ms =
   r.wall_s * 1000 / r.frames`; `peak_rss` from S1; the host share from the batch's host.log timing line
   (`host_ms / wall_ms`, section 3.4).
4. **The guest-time check** (rules.md 7): every instance's `ticks_per_vblank` is within 1 % of 4,481,136, and
   `x_real` is within 2 % of `host_fps / 59.831`. A failure marks the row `CHECK FAIL`.
5. Row: core, n, per-instance and total `host_fps`, `app_fps`, `x_real`, `cpu_ms`, `wall_ms`, host share, peak RSS,
   the workers' nice, load at start and end, slot wait, date. Per core, once: the effective option set (the `option
   ` lines of instance 0's host.log at n=1) and the core version.

Two extra rows, one instance, on the cap core:
- **Round trip**: 600 x `run(1)` vs one `run(600)`: wall ms per frame for each, and the difference per call (the
  parent/worker cost Gen3D pays per small batch).
- **Shots**: 20 x `shot(prefix)` at `LAZ_PNG_LEVEL` 1 and 6 (a fresh Emulator for each level, the variable set in
  `os.environ` before it starts, since the level is read once per process): ms per shot, the bytes of one top PNG,
  and the `png level=` line from its host.log.

Output: `runs/e-speed/table.json` (every number), `runs/e-speed/table.md` (one Markdown table per core plus the
extra rows), and the rc file: the whole table run is started as
`sh -c 'trap "echo \$? > runs/e-speed.rc" EXIT; nice -n 10 python3 -I tools/speed_table.py ... > runs/e-speed.log 2>&1'`
with `run_in_background`, because step G's live gate waits on `runs/e-speed.rc` (phase-3.md section 2). Write the
rc file even if you stop early.

**The default cap, by a rule fixed now** (Guy, Q3, 2026-11-12: "Allow 4 too"; written before any run). Use the
rows of the cap core only. Let T(n) be the total `host_fps` at n instances and L(n) the 1-minute load at the end of
the n row; C = `os.cpu_count()`.
- If any cap-core row is `CHECK FAIL`, the table is not used: the cap stays 3 (`DEFAULT_CAP` unchanged) and the
  report says why.
- Else start at cap = 1 and, for n = 2, 3, 4 in order: **step up to n only if T(n) >= 1.25 x T(n-1) and L(n) < 2 x
  C**; stop at the first n that fails.
- The cap is marked "provisional (light scene)" (no real-scene row, Guy Q1).

`speed_table.py` computes the cap with this rule (one small pure function, `cap_rule(rows, cpu_count) -> (cap,
reasons)`, unit-tested in `test_slots.py` or a `test_speed_rule` block there with made-up rows: a clean climb to 4, a
stop at 2 for throughput, a stop at 3 for load, a CHECK FAIL). After the run, set `DEFAULT_CAP` in `_slots.py` to
the result (the one E2 edit to an E1 file).

`docs/research/speed-table-e.md`: the date, the commit, the cores and their versions, the effective option set per
core, the Mac (cores, RAM), the tables copied from `table.md`, the guest-time check per row, the workers' nice, the
host share of the shot-free batches (PLAN's target: under 5 %; if over, say which part of `host_ms` is largest and
stop there, no tuning), the round-trip and shot rows, the cap rule (verbatim from this section), its numbers and
its result, and one line: "Test-app numbers are a light scene (rules.md 7); spike 2's real 3D-field numbers are in
spike-2-real-scene.md." No speed claim beyond the table.

## 8. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree**: `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers azahar-src; do [ -e
   MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done` (link the children, never `dl/` itself), `cp -R MAIN/vendor .`; `mkdir
   -p build-core && ln -sf MAIN/build-core/azahar_lazpy_libretro.dylib build-core/azahar_lazpy_libretro.dylib` (D's
   `lazpy_core` falls back to the checkout's `build-core/`; the link is your worktree's, ignored; MAIN's `build-core/`
   stays read-only; review 2 B2); `make`; `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make
   testapp` (or copy `MAIN/build/testapp.3dsx`). Checkpoint: `make test-host` and `python3 -m pytest -q tests/python -m
   "not slow"` pass before your edits (D's baseline, about 49 passed after D's fixes; print the counts).
1. **E1 (about 0.4 h; no emulator).** Sections 3, 4 (E1 rows), 5; write `test_pool_live.py` and
   `tools/speed_table.py` but do not run them. Checkpoint: gate 1 passes; `python3 -I tools/speed_table.py --help`
   and `python3 -I tools/hold_slot.py` (exit 2) work. **Then end your run**: your final report is the "E1 done"
   report: the exact list of E1 paths, the test counts, the `run.c` and `png.c` diffs in a few lines each, how
   `SlotTimeout` meets D's class, and anything in D's code that differed from phase-3.md section 6 (D2, D3, D5, D6).
   Do not start E2. The main loop commits E1, merges main (with F2) into your tree and resumes you with "E1
   committed at <sha>; main (with F2) merged into your tree at <sha>; go on with E2".
2. **E2 (about 0.4 h; timed).** Run only after the resume message (step F2 merged; never beside the core build or
   another timed part). First `git log --oneline -3` (F2's merge is there), `make`, and the non-slow pytest (F2's
   files are in your tree now). Then the live tests, then the table:
   - `sh -c 'trap "echo \$? > runs/e-pytest.rc" EXIT; LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs
     tests/python/test_pool_live.py > runs/e-pytest.log 2>&1'` with `run_in_background`; wait with Monitor until
     `runs/e-pytest.rc` exists (bounded 45 min).
   - The table as section 7 says, with both cores if `MAIN/build-core/azahar_lazpy_libretro.dylib` exists (pass its
     absolute path; read only; it is step 0's build F2 gated) and the stock core `dl/azahar/azahar_libretro.dylib`,
     with `--extra-rows`; wait with Monitor on `runs/e-speed.rc` (bounded 75 min). Expected machine time: 7 rows
     (stock 1-3, ours 1-4) x (60 s + boot and warm-up) plus the extra rows, about 20-25 min.
   - Set `DEFAULT_CAP`; write `docs/research/speed-table-e.md`. Checkpoint: gate 2 and 3 pass; quote them.
   Without Monitor: run the live tests one test per foreground call and the table one `--instances` value per call
   (`--instances 1`, `2`, `3`, `4`, then `--only-extra`), each under the 10-minute limit; say so. Still write
   `runs/e-speed.rc` at the end (step G waits on it).
3. The report (section 10) ends the run. Stop every waiter and background task you started (TaskStop) first. If the
   opus review asks for fixes, the main loop resumes you; any emulator rerun is a timed part (phase-3.md rule T):
   the resume message says when the machine is free (wait on `../libazahar-py-g/runs/g-batch.rc` with Monitor if it
   says G2 is running).

## 9. Machine-sharing rules

- E1 runs no emulator. E2 runs at most 4 instances at once (only in the n=4 row), all through the slot cap (the
  live tests hold 3 real slots, section 6; the table uses the real folder with its own cap of 4), always nice'd
  (the worker's nice, the pytest and table processes under `nice -n 10`), folders under `runs/e-*` (ignored).
- E2 never runs beside the core build or another timed part (phase-3.md rule T; the resume message is the
  go-ahead; G waits for your rc file).
- Never open a window: no Azahar app, no `open`, no Preview; PNGs with the Read tool.
- Signals go only to worker pids your own Emulators report (g2's SIGKILL) and to children you started (s2, s7);
  never `pkill`/`killall`; never another session's process. Never delete files in the real slot folder.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 10. The builder's report

E1 (end of the first run): as step 1 says. E2: the live-test summary (0 skipped) and g2's kill-to-acquire time,
g1's 3 s check, g4's nice values, the real-slot wait; the speed tables as printed; the guest-time check per row; the
host share; the round-trip and shot rows; the load and nice at each row; the option set per core; the cap, the
rule's numbers and the `DEFAULT_CAP` edit; any `CHECK FAIL`; line counts per new or edited file and the longest
function; the runners block for `docs/map/runners.md`:
```
nice -n 10 python3 -I tools/speed_table.py --app build/testapp.3dsx --core <path> [--core <path2>] --extra-rows --out runs/e-speed
LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_pool_live.py   # step E's live gate
python3 -I tools/hold_slot.py -- <command ...>   # run one command holding one libazahar slot
```
the lines for `docs/map/tools.md` (`tools/speed_table.py`: the 1-2-3-4 instance speed table with the guest-time
check and the cap rule; `tools/hold_slot.py`: hold one slot of the machine-wide cap, then exec a command); lines for
`.gitignore` (none expected: `runs/` is ignored); and a final **"Lessons and notes"** block, ready to paste into item
310.

## 11. Hours (agent wall time)

Builder 0.81 h (E1 0.41, E2 0.4), the opus as-built review 0.2 h, the commit 0.1 h: **1.11 h**, against PLAN.md's
1.0 (the live slot gate's real-plus-private slots, the 4-instance row and its rule, the `slot=` keyword; less the
cut state row and the cut `_slots` timing print). The slot waits, the live tests and the table runs are machine time.

## 12. Review checklist (the opus as-built review)

1. `_slots.acquire` is bounded (a maximum round count), closes every fd it does not keep, never writes into a lock
   file, and raises `SlotTimeout` (a `HostTimeout`) whose text names the folder and the cap; `slot_dir()`, `cap()`
   and the timeout read the environment on every call.
2. The parent closes its slot fd right after `Popen` (and on a `Popen` failure); `slot.txt` is written after
   `Popen`; `pass_fds` holds exactly the pipe fd and the slot fd; **a fake-worker spawn takes no slot unless asked**
   (`slot=None` default, `slot=True` in s6 only).
3. No lock is held in the parent process for a live worker (check with `lsof -p <parent pid>` in the report, or by
   reading the code path); `tools/hold_slot.py` makes only the slot fd inheritable before `execvp`.
4. `Pool` closes every Emulator on every path; results come back in item order; overrides win over kwargs.
5. The live tests take 3 real slots first, then set the private folder and cap; g2 measures from the kill to the
   acquire, not to the boot; g4 checks `>= 10`.
6. `run.c`'s timing line is written on every successful batch exit and does not change the batch's behaviour;
   `png.c` stays pure (no `azh_log`, still in `TEST_SRC`), reads the level once, validates it; `run.c` logs it once.
7. The table's guest-time check is computed as section 7 says; the cap follows the fixed rule (unit-tested
   `cap_rule`), with 4-instance rows only on the cap core; test-app rows are labelled light; no speed claim outside
   the table; `DEFAULT_CAP` holds the rule's result.
8. E2 edited none of `__init__.py`, `_client.py`, `run.c`, `png.c`, `azh_pure.h`, and of `_slots.py` only
   `DEFAULT_CAP`.
9. Python rules: type hints and docstrings on public names, bounded loops, no bare `except`, every opened fd closed
   on every path; C rules for the two edits (checked returns, no new globals beyond file statics).
10. Nothing committed by the builder; no item file touched; nothing written in MAIN; `tools/build-core.sh` never run.

## 13. Interfaces assumed

From phase-3.md section 6: H2, A5, A8-A11, B1-B4, B8, B9, D1-D7, D10, and the slot convention of phase-3.md section
2. If D's spawn, worker argv, `HostTimeout`, `Stats` fields or fixtures differ from those rows, follow the code and
report the difference.
