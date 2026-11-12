# Step F2: gate our patched core with the full test batch (item laz-320)

Brief for one sonnet builder, revision 0 (2026-11-12). Phase index: `docs/plans/phase-3.md` (order, ownership,
merges, departures, interfaces). Contract: `docs/PLAN.md:311` ("Phase F2"), sections 2.4 and 2.7. Where this brief
disagrees with PLAN.md on a goal, PLAN.md wins: stop and report (except the approved departures P1-P8 of
phase-3.md section 5 and phase-2.md section 5, which you follow).

You work in `../libazahar-py-f2` (branch `step-f2`, made at main after Phase 2 merged). "MAIN" is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`. "OURS" is
`MAIN/build-core/azahar_lazpy_libretro.dylib` (absolute path; **read only**); "STOCK" is
`dl/azahar/azahar_libretro.dylib` in your worktree (a link to MAIN's). **Never commit, never edit item files, never
write in MAIN.** Read first: the repo's `CLAUDE.md`, `docs/map/rules.md`, phase-3.md sections 2, 3, 5 and 6,
phase-c.md sections 3.4, 3.5, 6, 8, phase-d.md sections 3, 4 and 8, `core/README.md`, `core/options-lazpy.txt`,
`~/.claude/python-golden-rules.md` and `~/.claude/c-golden-rules.md`.

## 1. Goal and gate

Prove our core works with everything Phases 1 and 2 built, applied with its own option profile, and that it gives
the exact repeats the stock core cannot. The gate (headless, this Mac):

1. **f1** `MAIN/build-core/build.exit` holds `0` and OURS exists.
2. **f2** `/usr/bin/nm -gU OURS` lists exactly the 25 `_retro_*` names of SRC
   `citra_libretro/libretro.osx.def` plus `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play` (28,
   nothing else); STOCK lists exactly the 25.
3. **f3** a run on OURS writes `2126.2-lazpy.1` as the core version in host.log, and the effective option set logged
   at boot holds the six keys of `core/options-lazpy.txt` with its values (P8 works).
4. **f4** on OURS: `make test-host` passes; `python3 -I tests/gate_c.py --core OURS` prints PASS for C(a)-(f) and the
   raw-shot check with the our-core expectations of section 5; `LAZ_CORE=OURS LAZ_REQUIRE_EMULATOR=1 python3 -m
   pytest -q -rs tests/python` passes with 0 skipped; **no host.log** under `runs/c-gate/` or `runs/d-pytest/` from
   these runs holds C's exit-path line (stop reasons returned, no `_exit`).
5. **f5** C(e)'s repeat (section 6, r1): two runs on OURS in fresh folders give identical shot sha256s, a
   byte-identical SD `log.txt` (`s=` and `t=` included) and identical summary lines (wall fields removed).
6. **f6** D's state boot repeat (section 6, r2): two full chains on OURS give identical shot sha256s and log lines
   after the state for the two restored instances.
7. **f7** the debug-text stop (section 6, dbg): `stop=debug_text`; the batch's last frame is within {0, 1} of the
   `ready` line's host frame and **equal across two runs**; the SD log at the stop ends at the `ready f=200` line or
   the one per-frame line after it.
8. **f8** recorded, not gated: a stock-made state loaded into OURS and an OURS state loaded into STOCK (ok, or the
   error class and text); r1 on STOCK twice (which fields differ); the state bytes of the two r2 chains after the
   256-byte header; `drain_ms` and `t_state` from the r2 host.logs.
9. **f9** the stock core still passes after your edits: `python3 -I tests/gate_c.py --core STOCK` and `LAZ_CORE=STOCK
   LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python`.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`, PATCHES = `core/patches/`)

- macOS exports only what `libretro.osx.def` lists (SRC citra_libretro/CMakeLists.txt:96, `-exported_symbols_list`);
  the file has 25 symbols after two comment lines (27 lines). Patch 0001 appends `_lazpy_read_memory` and
  `_lazpy_write_memory`; 0006 appends `_lazpy_movie_play`.
- Patch 0005 sets the version suffix `-lazpy.1`; A's `azh_version_ok` accepts `2126.2` and `2126.2-lazpy.1`
  (`host/pins.h`).
- Our core's six options exist only when it registers them (patch 0002); A's `azh_set_option` refuses an
  unregistered key with `AZH_E_ARG` (phase-a "2. Facts"), so **the lazpy lines must not be sent to the stock core**.
  No Phase 1 or 2 code applies `core/options-lazpy.txt` (phase-3.md P8): you add that.
- What makes repeats exact on our core, and what breaks them on stock:
  - async HLE work runs on `std::async` unless `deterministic_async_operations` (SRC common/settings.h:490-491;
    core/hle/kernel/hle_ipc.h:306, 348);
  - the guest's tick base is random unless `init_ticks_type=Fixed` (SRC core/core_timing.cpp:37-44), so `s=`
    differs run to run on stock;
  - the guest clock starts from the host clock unless `init_clock=FixedTime` (SRC core/hle/kernel/shared_page.cpp:
    34-63), so `t=` differs on stock;
  - the log runs on its own thread unless `instant_debug_log` (SRC common/logging/backend.cpp:353), which is why a
    debug-text stop is refused on stock (P5) and must be exact on ours.
- On our core status 16 does not `_exit`: patch 0003 makes `retro_run` return after `DisplayMessage`, C's detector
  flags `AZH_ACT_EXITED` and the batch returns `stop=guest_exited` (phase-c 3.5); azhost exits 10 after printing the
  summary (phase-c 6). A crash is `guest_error` with no 3-in-one-run count; the Emulator stays open after a
  `GuestError` on our core (phase-d 4.5).
- A state's 256-byte `CSTHeader` holds the program id, the revision, **the wall-clock time of the save** and the
  build name (SRC core/savestate.cpp:24-36, 262), so two states of one guest moment differ in their first 256 bytes.
  A state is refused when its revision is not `g_scm_rev` (savestate.cpp:296-303). A build from the unified tarball
  takes `GIT_REV` from its `GIT-COMMIT` file (`dl/azahar-src/unpacked/.../CMakeModules/GenerateBuildInfo.cmake:13-16`),
  the same commit the stock release was built from, so the two cores may accept each other's states; D's meta only
  warns on a different `core_version` (phase-d 3.3). f8 records what happens.
- C's exit-path line: find its exact fixed text in `host/env.c` (phase-c 3.5: one `write(2)` of a fixed line to the
  log fd) and grep for that text.

## 3. The code changes (F2-1)

### 3.1 `azh_stats` after open (`host/api.c`)

Allow `azh_stats` in every state after `azh_open` succeeded (before boot it reports frames 0, the rusage so far, the
core's name and version and `is_lazpy_core`). Change only the call-order check for this one function; the header
comment in `azhost.h` is not edited (frozen); the change goes in your report for USING.md and HOST-API.md (Phase 4).
If the merged code already allows it, change nothing.

### 3.2 `azhost` applies our core's profile (`host/azhost_main.c`)

New flag `--lazpy-profile FILE|none`, default `core/options-lazpy.txt` (relative to the current directory, like A's
`--profile` default). After `azh_open`: `azh_stats`; if `is_lazpy_core`, apply the file's lines with A's profile
reader and `azh_set_option` **first**, then A's `--profile` lines, then each `--opt` (later wins, A's rule). `none`
skips it. On the stock core the lazpy file is not read. A missing or bad lazpy file on our core is handled exactly
as A handles a missing or bad `--profile` (same message shape, same exit code). Add the flag to `--help`.

### 3.3 The Python side

- `_paths.py`: `lazpy_profile() -> Path | None`: `LAZ_LAZPY_PROFILE` (the text `none` gives None), else
  `<root>/core/options-lazpy.txt`, resolved; a missing default file gives None with no error (a pip user without the
  repo's `core/`), a missing file named by the variable gives `HostError`.
- `_worker.py`: the `start` request gains `lazpy_options` (an ordered list of pairs, maybe empty). After `azh_open`:
  `azh_stats`; then apply `option_plan(is_lazpy, lazpy_options, options)` in order, then `azh_boot`. `option_plan`
  is a small pure function (lazpy pairs first only when `is_lazpy`, then the others) so it is unit-tested.
- `emulator.py`: read the lazpy file with the same reader the profile uses and send its pairs; after a `run` reply
  whose `stopped_by` is `guest_exited` (the our-core path: the worker is alive), close the Emulator (D's graceful
  close, then reap) before returning the `RunResult`, so both cores leave the user in the same state (closed).
  Nothing else in the Emulator changes.

### 3.4 Core-kind switches in the tests (no expectation loosened)

- `tests/gate_c.py`: `--core PATH` (passed to `azhost --core`; default as before) and `--core-kind auto|stock|lazpy`
  (auto: `/usr/bin/nm -gU <core>` lists `_lazpy_read_memory`). The kind is printed first. Our-core expectations in
  section 5; the stock expectations are unchanged.
- `tests/python/conftest.py`: a session fixture `core_kind` ("stock" or "lazpy", by the same `nm` test on the core
  `host_paths` resolves). D's slow tests whose outcome depends on the core branch on it; each branch asserts as
  strictly as the stock one (section 5). Edit only the tests that need it (`test_c_checks.py`, `test_live_errors.py`,
  `test_state.py`, `test_api.py`) and list every changed assertion in the report.
- New `tests/python/test_lazpy_profile.py` (no emulator): `option_plan` order and the stock skip; `lazpy_profile()`
  with the variable set, `none`, unset with and without the file; **no key of `core/options-lazpy.txt` appears in
  `host/options-default.txt`** (so the order between the two files can never matter).

## 4. Files (you create or edit only these)

| Path | Role |
|---|---|
| `host/api.c` | 3.1 only |
| `host/azhost_main.c` | 3.2 only |
| `python/libazahar/_paths.py`, `_worker.py`, `emulator.py` | 3.3 only |
| `tests/gate_c.py`, `tests/python/conftest.py`, `test_c_checks.py`, `test_live_errors.py`, `test_state.py`, `test_api.py` | 3.4 only |
| `tests/python/test_lazpy_profile.py`, `tests/gate_f2.py` | new |
| `core/patches/*` | only in the build-failed path (section 7 step 0) |

Run artefacts go under `runs/f2/` (ignored), including the slot helper of section 9. Everything else is outside your
files (phase-3.md section 3): in particular `host/run.c`, `host/png.c`, `python/libazahar/_client.py` and
`__init__.py` (step E edits them in parallel), every header, `testapp/`, `tests/testapp_log.py`, `tests/checks_c.py`
(import only). If a check fails because of another Phase 2 file, stop and report with the failing output; edit it
only if the main loop names the file in a message.

## 5. Our-core expectations in C's and D's tests

| Check | Stock (unchanged) | Ours |
|---|---|---|
| C(c) c4 `--debug-stop "ready f="` | exit 7, stderr `NeedsLazpyCore:` | exit 0, `stop=debug_text`, batch 1's `last` below 600 |
| C(e) break | `stop=guest_break`, runs on | the same |
| C(f) exit | f1 exit 10; f2 map stop code 4, `exit_code` 10, message `(16)`; f3; f4 | f1 exit 10 **after** a summary line with `stop=guest_exited` and `msg` holding `(16)`; f2 map `exit_code` 0 and no exit-path line in host.log; f3 with the summary's `last` in place of the map's `frame_total`; f4 the same |
| C(g)-style error count (D's live tests) | 3 errors in one `retro_run`: exit 11, `GuestError`, Emulator closed | `GuestError` with `.result` (`stopped_by == "guest_error"`), Emulator open, one more `run(1)` works |
| D's debug-text test (if any) | `NeedsLazpyCore` | `stopped_by == "debug_text"` |
| D's exit test | `RunResult(stopped_by="guest_exited")` from the death mapping, Emulator closed | the same `RunResult` from the reply, Emulator closed (3.3) |
| Everything else | as written | identical expectations |

## 6. `tests/gate_f2.py` (new; stdlib plus `tests/` modules)

`python3 -I tests/gate_f2.py --ours OURS --stock STOCK [--only symbols,version,dbg,r1,r2,cross,stock_r1]`. It
inserts the absolute `tests/` and `python/` paths into `sys.path` first (phase-2.md B12). Every scenario runs in a
fresh `runs/f2/<id>/`; azhost runs are `nice -n 10 build/azhost run build/testapp.3dsx --sys ... --out ...
--sd-seed ... --core <core>` with a 600 s timeout that kills only its own child. Lines printed: `PASS <id> ...`,
`FAIL <id> ...`, `RECORD <id> ...`; the summary goes to `runs/f2/summary.txt`; exit 0 only if no FAIL.

- **symbols**: f2 (section 1). The 25 names are read from SRC's `libretro.osx.def` (lines starting with `_`), not
  typed in. Print any extra or missing name.
- **version**: a 30-frame run on OURS; f3 (section 1), the six key=value pairs found in the logged option set.
- **dbg** (f7), twice (`.1`, `.2`): seed `ready_at=200`; `--frames 600,1,1,1,1,1,1,1,1 --debug-stop "ready f="
  --print-last-line testapp/log.txt`. d1 batch 1 `stop=debug_text`; c_min from batches 2-9 with
  `checks_c.boot_offsets`; d2 batch 1's `last 1:` line is `ready f=200 ...` or the per-frame line `f=201 ...`; d3
  `last - (ready.v + c_min)` is 0 or 1 (printed); d4 run 2's batch-1 `last` and `last 1:` line equal run 1's. Also
  one `--stop-every 1` SD-stop run of the same seed: print its `last` beside the debug stop's (a RECORD line).
- **r1** (f5), twice on OURS: seed `break_at=300`; an inputs file written by the gate (A held frames 120-129, B
  140-149, touch (160, 120) down 150-159, circle (32767, 0) 170-179, all before the break); `--frames 600,120
  --inputs r1.txt --shot 100,250 --print-last-line testapp/log.txt`. Batch 1 must stop `guest_break` (as C(e)).
  Compare the two runs: the four PNGs' sha256, `log.txt` bytes, the summary lines with `wall=`, `fps=`,
  `wall_ms_max=` fields removed. Any difference is a FAIL naming the first differing line and field.
- **stock_r1** (f8): r1 twice on STOCK; RECORD which fields differ (expected: `s=` and `t=`, section 2) and whether
  the shots match.
- **r2** (f6), two chains on OURS, in Python through `libazahar` (core passed as `core=OURS`):
  1. `a = Emulator(app, runs/f2/r2-<c>/a, sd_seed=seed(boot_frames=1200))`; `a.run(1300)`; the log has the
     `booted` line; `S = a.save_state(runs/f2/r2-<c>/s.state)`; note the SD `log.txt` length at the save;
     `a.run(300, shots=[100, 300])`; keep a's log lines after the noted length and its shot sha256s; `a.close()`.
  2. `b = Emulator(app, runs/f2/r2-<c>/b, state=s.state)`; `b.run(300, shots=[100, 300])`; b's log lines after the
     snapshot's length (the snapshot's `log.txt` is a's at the save) and its shot sha256s; the `state load ...
     drain_ms=` line from b's host.log; `b.close()`.
  Gate: b of chain 1 equals b of chain 2 (lines and shot hashes). RECORD: a1 == a2; a_c == b_c within a chain (a
  saved instance and its restore continue alike); the two `s.state` files equal after byte 256 (and their first
  256 bytes, expected to differ only in the time field); `drain_ms`, `t_state`.
- **cross** (f8): `x = Emulator(app, ..., core=STOCK)`, `run(300)`, `save_state(stock.state)`, close; then
  `Emulator(app, ..., core=OURS, state=stock.state)` and `run(60)`: RECORD ok (and whether the log's `f` continues
  from the save) or the error class and text. The reverse with r2's chain-1 `s.state` into STOCK.

## 7. Steps, with a checkpoint after each (save files as you go; never commit)

0. **F2-0 (about 0.05 h): the build.** Read `MAIN/build-core/build.exit`, `ls -l OURS`, the tail of
   `MAIN/build-core/build.log`.
   - `build.exit` is `0` and OURS exists: go on.
   - The build failed (non-zero): find the first error in `build.log`. If it is in a patched file, fix the patch in
     your worktree's `core/patches/` with the smallest change (keep the hunk's notice; re-check it applies with `patch
     -p1 --dry-run` on a scratch copy of the pristine unpacked tree under `runs/f2/`, never in MAIN). **Then end your
     run** with a "build failed" report: the error, the patch diff, and the restart command for the main loop
     (`cd MAIN && nice -n 10 tools/build-core.sh --detach`, with `LAZ_CORE_LTO=OFF` if the log shows the linker was
     killed or ran out of memory). If the error is not in our patches (CMake, a submodule), report it with the log
     lines and stop. The main loop resumes you when `build.exit` is 0.
   - No `build.exit` and a live `build.pid`: the build is still running; wait with Monitor (bounded 120 min) and
     report the wait.
   Then f2 with `nm`. Seed the worktree: `mkdir -p dl && for d in azahar moltenvk libretro-headers vulkan-headers
   azahar-src; do [ -e MAIN/dl/$d ] && ln -s MAIN/dl/$d dl/$d; done`, `cp -R MAIN/vendor .`, `make`,
   `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (or copy
   `MAIN/build/testapp.3dsx`). Checkpoint: f1, f2; `make test-host` and the non-slow pytest pass (baseline counts
   printed).
1. **F2-1 (about 0.25 h; no emulator except one by-hand check).** Sections 3 and 6 (write `gate_f2.py`, do not run
   it). Checkpoint: `make check && make && make test-host` clean; `python3 -m pytest -q tests/python -m "not slow"`
   passes with `test_lazpy_profile.py`; one by-hand `azhost run build/testapp.3dsx ... --core OURS --frames 30`
   through the slot helper shows f3's version and the six keys in host.log.
2. **F2-2 (about 0.25 h of agent time; about 60-90 min of machine time).** One background batch, every emulator
   command through the slot helper, one instance at a time, in this order: gate C on OURS; pytest on OURS;
   `gate_f2.py` (all ids); gate C on STOCK; pytest on STOCK. Write it as `runs/f2/batch.sh` with one rc file per part
   (`runs/f2/<part>.rc`) and the whole batch's from a trap: `sh -c 'trap "echo \$? > runs/f2-batch.rc" EXIT; nice -n
   10 sh runs/f2/batch.sh > runs/f2-batch.log 2>&1'` with `run_in_background`; wait with Monitor until
   `runs/f2-batch.rc` exists (bounded 150 min). Then grep the host.logs for the exit-path line (f4). Without
   Monitor: run each part as its own foreground call, each split under the 10-minute limit (`gate_c.py --only`,
   pytest per file, `gate_f2.py --only`), and say so. Checkpoint: gate f1-f9; quote every PASS/FAIL/RECORD line.
3. The report (section 10) ends the run. Stop every waiter and background task you started (TaskStop) first. If the
   opus review asks for fixes, the main loop resumes you.

## 8. When a repeat is not identical

Do not tune and do not add options. Record the first differing log line (both versions), which fields differ, the
first differing shot frame, and whether the a1 == a2 RECORD differs at the same place. Then report; the main loop
takes it to review (a new core patch is a change of scope for Phase 3). The rest of the batch still runs.

## 9. Machine-sharing rules

- One emulator instance at a time, always nice'd, folders under `runs/f2*`, `runs/c-gate/`, `runs/d-pytest/`
  (ignored). Step E's builder runs no emulator while your batch runs (the main loop holds it at its E1 checkpoint);
  your batch never runs beside the core build.
- **The slot cap** (phase-3.md section 2): step E's `_slots.py` is not in your tree, so every emulator command runs
  under `runs/f2/hold_slot.py` (about 20 lines, ignored, not committed): it opens `LAZ_SLOT_DIR` or
  `~/Library/Caches/libazahar-py/slots/` (mkdir 0700), tries `slot-0.lock` .. `slot-<LAZ_MAX_INSTANCES or 3,
  minus 1>.lock` (0600) with `fcntl.flock(LOCK_EX | LOCK_NB)` each 0.1 s up to 1 h, prints the slot and the wait to
  stderr, `os.set_inheritable(fd, True)`, then `os.execvp` the command (the lock lives on in the command's process
  and dies with it). Run it with `python3 -I`.
- Never open a window: no Azahar app, no `open`, no Preview; PNGs with the Read tool.
- Never kill a process you did not start; timeouts kill only your own child. Never write in MAIN's `build-core/`.
- No `sleep` polling; one Monitor wait per long run, stopped before hand-back.

## 10. The builder's report

F2-0's result (and any wait or build failure); f1-f9 as printed; every changed assertion in C's and D's tests (old
and new, with the reason); the `option_plan` and the azhost order as built; the r1 and r2 comparisons and every
RECORD line (stock's differing fields, the state bytes after byte 256, `drain_ms` and `t_state`, cross-core
results); the dbg frames of both runs; the slot waits; whether `azh_stats` needed the order change; line counts per
edited file and the longest function; the runners block for `docs/map/runners.md`:
```
build/azhost run <app> ... --core build-core/azahar_lazpy_libretro.dylib [--lazpy-profile core/options-lazpy.txt|none]
python3 -I tests/gate_c.py --core <core> [--core-kind auto|stock|lazpy]
python3 -I tests/gate_f2.py --ours <our core> --stock <stock core> [--only ...]   # step F2's gate
```
lines for `.gitignore` (none expected); one line for USING.md (Phase 4): "on our core `core/options-lazpy.txt` is
applied first; `LAZ_LAZPY_PROFILE=none` turns it off"; and a final **"Lessons and notes"** block, ready to paste into
item 320 (with the drain numbers for D 3.3's note: whether a drain-only export is worth a Phase 4 item).

## 11. Hours (agent wall time)

Builder 0.55 h (F2-0 0.05, F2-1 0.25, F2-2 0.25), the opus as-built review 0.2 h, the commit 0.1 h: **0.85 h**,
against PLAN.md's 0.75 (P8's profile application and the core-kind switches were not in PLAN's F2). The batch, a
build wait and a rebuild are machine time.

## 12. Review checklist (the opus as-built review)

1. f2 compares against the `.def` file read from the source, not a typed list; it fails on any extra export.
2. The lazpy profile is applied only when `is_lazpy_core`, first, before the profile and the caller's options, in
   azhost and in the worker alike; `none` and a missing default behave as 3.2 and 3.3 say; the no-shared-key test
   exists.
3. `azh_stats` after open changes nothing else in the call-order rules.
4. The Emulator closes after a returned `guest_exited` and only then; `GuestError` on our core leaves it open.
5. Every changed test assertion is at least as strict on our core as the stock one; no stock expectation changed.
6. r1 compares bytes and hashes (no fuzzy match); r2's gate compares the two restored instances across chains; the
   state comparison skips exactly the 256-byte header.
7. dbg's d3 and d4 are computed from the printed `last` values; the SD-stop comparison is a RECORD only.
8. The exit-path grep uses the exact text from `env.c` and covers every our-core host.log of the batch.
9. Every emulator command ran under the slot helper, one at a time, nice'd; nothing written in MAIN; no item file
   touched; nothing committed.
10. Any patch change (build-failed path) is the smallest fix and keeps its notice.

## 13. Interfaces assumed

From phase-3.md section 6: A3-A7, A12, B1-B3, B9, F1-F5, C4-C7, D1-D10, SD. If a merged name, flag or line differs
from those rows (the exit-path text, `--print-last-line`'s format, D's fixtures or the `start` arguments), follow
the code and report the difference.
