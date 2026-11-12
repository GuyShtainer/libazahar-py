# Phase 3, scale and memory: the phase plan (item laz-300)

Opus phase plan, 2026-11-12, **revision 0** (before review 1). Steps: E (laz-310, `docs/plans/phase-e.md`), F2
(laz-320, `docs/plans/phase-f2.md`) and G (laz-330, `docs/plans/phase-g.md`). Each brief is complete on its own for
one sonnet builder in its own worktree. This file is the index: order, checkpoints, file ownership, merge plan,
hours, the proposed departures from PLAN.md, the interfaces taken from Phases 1 and 2, the interfaces left for
Phase 4, the checked facts, the risks and the hour-saving pass.

Contract: `docs/PLAN.md` (final) sections 2.2, 2.4, 2.5, 2.7, 2.8, 2.9, the grouping paragraph of section 3 and its
Phase E (PLAN.md:296), F2 (:311) and G (:317) paragraphs. (The step item files still point at :289, :304 and :310;
the main loop fixes those pointers when it moves the items.) This plan refines PLAN.md. Where a brief disagrees with
PLAN.md on a goal, PLAN.md wins and the builder stops and reports, **except for the approved departures** (Phase 2's
P1-P6 and, once the reviews approve them, this plan's P7-P8 in section 5), which the builders follow without stopping.

Phase 2's inputs: `docs/plans/phase-2.md` revision 2 with `phase-c.md` and `phase-d.md` (final, not yet built when
this plan was written: step C was at C1, commit cd2aadd). Phase 1's: merged at 570eebf (A, B, F1). Every interface
this plan takes from them is listed in section 6, so review can reconcile it with the code as built. **If the merged
code differs from a row of section 6, the builder follows the code and reports the row.**

Hours are agent wall time (PLAN.md's unit). Machine time (emulator batches, the core build, a wait for a slot or for
another step's timed run) is not counted.

## 1. The three steps

| Step | Delivers | Gate (headless, this Mac) | Hours |
|---|---|---|---|
| E, laz-310 | `python/libazahar/_slots.py` (the machine-wide `flock` slot cap) and `pool.py` (`Pool`, `LoadWarning`); the worker spawned holding its slot; zlib level 1 (`LAZ_PNG_LEVEL`); one timing line per batch in host.log; `tools/speed_table.py`; unit and live tests; `docs/research/speed-table-e.md` with the default cap | `python3 -m pytest -q tests/python -m "not slow"` passes; `LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python/test_pool_live.py` passes 0 skipped: 3 instances give correct, separate logs and shots; a 4th waits under cap 3; a SIGKILL frees the slot within 1 s; every worker at nice 10; the speed table for 1, 2, 3 instances of the test app's 3D scene, 60 s each, with the guest-time check, written and the default cap set by section 2's fixed rule | 1.1 |
| F2, laz-320 | our core applied with its own profile (`core/options-lazpy.txt`) by `azhost` and by the worker; `azh_stats` after open; the Emulator closes after a returned guest exit; core-kind switches in C's and D's tests; `tests/gate_f2.py` (symbols, version, exact repeats, the exact debug-text stop, cross-core states) | `nm -gU` shows exactly the 25 `_retro_*` plus `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play`; host.log shows `2126.2-lazpy.1`; on our core gate C passes and `LAZ_REQUIRE_EMULATOR=1` pytest passes 0 skipped, stop reasons returned (no exit-path line in any host.log); C(e)'s repeat and D's state boot give identical shot hashes and log lines across two runs; the debug-text stop's frame is exact and equal across runs; stock states into ours (and back) recorded; the stock core still passes gate C and pytest | 0.85 |
| G, laz-330 | ABI 3: `azh_read`/`azh_write` through the exports (`host/mem.c`), the per-frame watch list into a watch area of the map, `AZH_E_UNMAPPED`; Python `emu.memory` (`read`, `write`, `u8`..`u64`, signed, `write_*`, libmgba-py's `.raw_read`), `run(..., watch=)`, `RunResult.watch`, `GuestMemoryError`; unit and live tests | on our core: both records (global and heap) read back the logged values frame by frame for 600 frames, by `read` calls and by the watch list; a write changes the next logged event; a straddling read and a fully unmapped read both raise `GuestMemoryError`; on the stock core every memory call and any watch raises `NeedsLazpyCore`; `make test-host`, gate C and D's pytest still pass | 0.9 |

Phase total: **2.85 h** of step work plus about 0.5 h for the two review loops (PLAN.md section 3's grouping
paragraph) = **about 3.35 h**, against PLAN.md's 1.0 + 0.75 + 0.5 + 0.5 = **2.75 h**. The 0.6 h over is named per
step in section 7. The checkpoint choreography (two commits on branches, one merge into G's worktree, two resumes) is
main-loop time, about 0.15 h, booked to the main loop.

## 2. Order, checkpoints and the parallel split

```
Before launch: Phase 2 merged on main (step-c and step-d); MAIN/build-core/build.exit exists (the core build ended)
  |
  E builder (sonnet, ../libazahar-py-e, step-e)       F2 builder (sonnet, ../libazahar-py-f2, step-f2)
  |  E1: _slots, pool, client spawn, png level,       |  F2-0: the build's result, symbols, version
  |      run.c timing line, speed_table.py,           |  F2-1: profile application, stats after open,
  |      unit tests; NO emulator                      |        guest-exit close, test switches, gate_f2.py
  |  ENDS ITS RUN: "E1 done"                          |  F2-2: the batch on our core, the stock regression,
  |  main loop commits E1 on step-e                   |        the repeats, cross-core   (timed, one instance)
  |                                                   |  ENDS ITS RUN: "F2 done"
  |  (waits for "F2 done": the timed runs never overlap)
  |  main loop resumes E: "E1 committed at <sha>; F2's batch is over; go on with E2"
  |  E2: live pool gate, the speed table              opus as-built review of F2; fixes; commit; merge step-f2
  |      (writes runs/e-speed.rc from a trap)         main loop: git worktree add -b step-g ../libazahar-py-g main;
  |                                                   in it: git merge <E1 sha> (E1's commit on step-e)
  |  ENDS ITS RUN: "E done"                           launch G (message names ../libazahar-py-e/runs/e-speed.rc)
  v                                                   G1: ABI 3, mem.c, watch area, Python memory; no emulator
  opus as-built review of E; fixes; commit;           G2: waits on e-speed.rc if E2 is still timing (Monitor),
  merge step-e into main                                  then the live gate on both cores
                                                      ENDS ITS RUN: "G done"
                                                      main loop: git merge main in ../libazahar-py-g (E2's files)
                                                      opus as-built review of G; fixes; commit; merge step-g
```

- **A builder never waits for the main loop.** A sub-agent reports only by ending its run, so each checkpoint is the
  end of a run: E after E1 and after E2, F2 at its end, G at its end. The main loop commits, then resumes the same
  agent with SendMessage (its context kept). The main loop writes each builder's agent id into the handoff at launch.
  If a resume fails, the fallback is a fresh sonnet given the brief, the earlier report and `git log step-<x>`; the
  reports list exact paths and measured values to make that possible.
- **How a builder waits on its own long command** (Phase 2 S9): never `sleep`-poll, never "be woken". Long runs
  write an rc file from a `trap ... EXIT`; the builder starts them with `run_in_background` and waits with the
  Monitor tool on "the rc file exists" (an until-loop, bounded); it stops every waiter it started (TaskStop) before
  it hands back. Without Monitor, it runs the work in foreground parts under the 10-minute Bash limit and says so.
- **Timed runs never overlap** (rules.md 7; PLAN 2.8): the core build, F2-2, E2 and G2 are each timed or loaded,
  and they run one after another in that order. E1, F2-1 and G1 run no emulator and may overlap anything. G2 starts
  only when `../libazahar-py-e/runs/e-speed.rc` exists (or E's report says E2 is over); it waits with Monitor
  (bounded 90 min). F2-2 runs one emulator at a time; E2 runs up to 3; G2 one at a time.
- **One slot convention, fixed here** because E builds it while F2 already needs it: the folder is `LAZ_SLOT_DIR`,
  else `~/Library/Caches/libazahar-py/slots/` (mode 0700); the files are `slot-0.lock` .. `slot-<cap-1>.lock` (mode
  0600); a slot is held by `flock(LOCK_EX|LOCK_NB)` on its own open file description; the cap is
  `LAZ_MAX_INSTANCES`, default 3. F2 has no `_slots.py` yet, so it holds one slot around each emulator command with
  a 20-line helper in its ignored `runs/f2/` (phase-f2.md section 9); G and later use E's `_slots.py` through the
  Emulator.
- **Why F2 goes first on the machine:** it is on the critical path to G (G needs F2's profile application, and its
  gate needs our core applied right), and E2's numbers are better taken after F2 has shown our core works, so the
  table can carry a row for each core (section 7's hour-saving pass: one table run, both cores).
- **If the core build failed** (F2-0 finds `build.exit` non-zero or no dylib): F2 reads `build.log`, fixes the patch
  in its own worktree's `core/patches/` (the only case where F2 edits `core/`), and ends its run with a "build
  failed" report holding the fix. The main loop copies the fixed patch into MAIN's ignored build tree (never
  committing in MAIN) and restarts `nice -n 10 tools/build-core.sh --detach` there (the STAMP changes, so the tree is
  re-unpacked with the archive's mtimes and the rebuild is incremental). A build that died rather than failed is
  rerun with `LAZ_CORE_LTO=OFF`. F2 is resumed when `build.exit` is 0. E1 goes on meanwhile; E2 then waits for F2-2.
- **Why G's worktree carries E1:** G edits `python/libazahar/__init__.py`, `host/run.c` and the map after E1 has
  edited them (E1's exports, its timing line). Merging E1's commit into G's worktree at launch (Phase 2's
  D-at-C1 pattern) means G's edits sit on top of E1's and the final merges are conflict-free. **E2 edits none of
  E1's shared files** (`__init__.py`, `_client.py`, `host/run.c`, `host/png.c`); a fix there found in E2 is reported
  to the main loop, which sequences it.

## 3. File ownership (who creates or edits what)

| File | Owner in Phase 3 | What changes |
|---|---|---|
| `python/libazahar/_slots.py`, `pool.py` | E (new) | phase-e.md section 3 |
| `python/libazahar/_client.py` | E | the spawn acquires a slot, passes its fd in `pass_fds` and as `argv[3]`, closes the parent's copy, writes `<workdir>/slot.txt` |
| `python/libazahar/__init__.py` | E (E1), then G | E1 exports `Pool`, `LoadWarning`; G exports `Memory`, `WatchRow`, `GuestMemoryError` |
| `host/png.c` | E | zlib level from `LAZ_PNG_LEVEL` (0-9, default 1) |
| `host/run.c` | E (E1: the timing line), then G | G adds the watch rows after each `retro_run` |
| `tools/speed_table.py`, `tests/python/test_slots.py`, `test_pool.py`, `test_pool_live.py`, `docs/research/speed-table-e.md` | E (new) | phase-e.md |
| `host/azhost_main.c` | F2, then G | F2: `--lazpy-profile`; G: only if `azhost layout` needs a change (it should not: it prints `fields[]`) |
| `host/api.c` | F2, then G | F2: `azh_stats` allowed after open; G: `azh_read`, `azh_write`, the watch checks in `azh_run`, the new `fields[]` rows |
| `python/libazahar/_paths.py`, `_worker.py`, `emulator.py` | F2, then G | F2: `lazpy_profile()`, the option plan, the close after a returned guest exit; G: the `read`/`write` ops, `emu.memory`, `run(watch=)` |
| `tests/gate_c.py`, `tests/python/test_c_checks.py`, `test_live_errors.py`, `test_state.py`, `test_api.py`, `tests/python/conftest.py` | F2 | core-kind switches only (`--core`, `--core-kind`, a `core_kind` fixture) |
| `tests/gate_f2.py`, `tests/python/test_lazpy_profile.py` | F2 (new) | phase-f2.md |
| `core/patches/*` | F2, only if the build failed | the smallest fix to the failing hunk |
| `host/azhost.h`, `host/azh_internal.h`, `host/azh_pure.h`, `host/hostmap.c`, `host/core.c` (the `dlsym` of the two exports beside A's detection, wherever the code does it) | G | ABI 3 (phase-g.md section 3) |
| `host/mem.c`, `tests/host/test_mem.c`, `python/libazahar/memory.py`, `tests/python/test_memory.py`, `test_memory_live.py` | G (new) | phase-g.md |
| `python/libazahar/_abi.py`, `_map.py`, `results.py`, `errors.py`, `tests/python/fakeworker.py`, `tests/python/test_abi.py`, `test_map.py`, `Makefile` (`test-host` gets `test_mem`), `docs/USING.md` (a memory section) | G | ABI 3 mirrors, the watch area, `GuestMemoryError` |

A file listed for two steps is edited by the second only after the first's commit is in its worktree (section 2).
**No builder edits a file outside its rows.** F2 may edit another Phase 2 file only when a check fails because of it
and the main loop names the file in a message. Nobody touches: `testapp/`, `tests/check_testapp.py`,
`tests/gate-a.sh`, `tests/gate-b.sh`, `tests/testapp_log.py`, `tests/checks_c.py` (import only), `host/state.c`,
`host/statemeta.c`, `host/crop.c`, `host/frame.c`, `.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`,
`docs/hours.tsv`, the handoff, **every item file**, `prototype/`, `README.md`, and MAIN (read and copy only; MAIN's
`build-core/` is read only). Lines the main loop must add (`.gitignore`, `docs/map/runners.md`, `docs/map/tools.md`)
and the "Lessons and notes" block for the item go in each builder's report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. Before launch: Phase 2 merged; `MAIN/build-core/build.exit` exists. `git worktree list` and a case-insensitive
   name check (`ls .. | grep -i libazahar-py-`), then `git worktree add -b step-e ../libazahar-py-e main` and
   `git worktree add -b step-f2 ../libazahar-py-f2 main`. Dispatch both sonnets without isolation, cwd in the
   worktree; they seed `dl/` and `vendor/` themselves (each brief's step 0). Agent ids into the handoff. If the build
   has not exited, launch E alone and F2 when `build.exit` appears.
2. At "E1 done": commit exactly E1's paths on `step-e` (`git add <paths>`, `git diff --cached --stat`); note the sha
   for step 5. Do not resume E yet.
3. At "F2 done": resume E with "E1 committed at <sha>; F2's batch is over; go on with E2". Opus as-built review of
   the step-f2 diff (phase-f2.md section 12); fixes by the resumed F2 builder if any; commit; merge `step-f2` into
   main; paste the report's "Lessons and notes" into item 320 and move it with its Evidence line (one commit with
   the moved item, per the project's CLAUDE.md).
4. Then: `git worktree add -b step-g ../libazahar-py-g main`; in it `git merge --no-edit <E1 sha>` (E1 touches no
   F2 file, so no conflict is expected; a conflict stops the launch and goes to the main loop); launch G with
   phase-g.md and a message naming `../libazahar-py-e/runs/e-speed.rc` and whether E2 is still running.
5. At "E done": opus as-built review of the step-e diff (phase-e.md section 12), fixes, commit, merge `step-e` into
   main (it merges cleanly: G is not merged yet); item 310 as in 3. In `../libazahar-py-g`: `git merge main` (brings
   E2's files, none of which G edits).
6. At "G done": opus as-built review (phase-g.md section 12), fixes, commit, merge `step-g`; item 330; then the phase
   item 300. Remove each worktree only after `git status --porcelain` is empty in it.
7. After the phase merges, the full suite (gates A, B, C on both cores, F2, D's and E's and G's pytest) runs once as
   one background batch (the main loop is woken on exit), through the slot cap.

## 5. Departures from PLAN.md

Phase 2's P1-P6 stay approved and in force. Proposed here, for the reviews to approve or reject:

| # | PLAN.md says | Phase 3 does | Why |
|---|---|---|---|
| P7 | PLAN 2.5's error classes (plus P6's `HostError`) | adds `AZH_E_UNMAPPED` (-11) and `GuestMemoryError` (a `LibAzaharError`, with `.addr` and `.length`) for a read or write that touches an unmapped guest page; the core's -1 maps to `AZH_E_ORDER` (`HostError`), -3 to `AZH_E_ARG` (`ValueError`) | PLAN's gate asks for "a clean error" on unmapped reads; a caller probing memory (Gen3D's harness, G's own straddle test) must tell "that page is not mapped" from a host bug without parsing text |
| P8 | PLAN 2.4: "a committed option profile ... Users override per key" (one profile) | on our core, the lines of `core/options-lazpy.txt` are applied first, then the profile, then the caller's options (later wins); azhost `--lazpy-profile FILE\|none`, Python `LAZ_LAZPY_PROFILE` | PLAN 2.4 says our core's options are "all pinned on in our core's profile", but no Phase 1 or 2 code applies that file: without it the debug-text stop is `AZH_E_ARG` on our core (phase-c 3.4) and repeats are not exact. The two files share no key (checked by a test), so the order is only for the caller's overrides |

Interface changes inside the project (not PLAN departures; listed so the review sees them): `azh_stats` becomes
valid any time after `azh_open` (Phase A allowed it only after boot), so `azhost` and the worker can learn the core
kind before setting options (F2); ABI 3 appends fields to `azh_batch` and `azh_result` and grows the map (G).

## 6. Interfaces taken from Phases 1 and 2

"State" says how sure the row is: **holds** (checked in code merged on main), **planned** (from a final plan, not yet
built when this was written; the builder checks it against the code and reports a difference).

| # | What Phase 3 relies on | Source | State | Used by |
|---|---|---|---|---|
| A1 | `AZH_E_*` -1 ARG, -2 ORDER, -3 CORE, -4 BOOT, -5 VULKAN, -6 IO, -7 NOMEM, -8 UNSUPPORTED, -9 NEEDS_LAZPY_CORE, -10 SAVESTATE; G adds -11 | phase-a "3. The API"; phase-2.md A1 | holds | G |
| A2 | `int azh_read(uint32_t addr, uint32_t len, void *buf)` and `int azh_write(uint32_t addr, uint32_t len, const void *buf)` exist and return `AZH_E_NEEDS_LAZPY_CORE` on the stock core until G | phase-a "3. The API" | holds | G |
| A3 | Our core is detected at `azh_open` by `dlsym(core, "lazpy_read_memory")`; the result is `azh_stats.is_lazpy_core` and a flag in the state struct | phase-a "3. The API" | holds | F2, G |
| A4 | Call order: open, then options, then boot, then run/shot/stats; `azh_abi_layout`, `azh_error` in any state | phase-a "3. The API" | holds; F2 relaxes `azh_stats` to "after open" | F2 |
| A5 | `azh_set_option` checks at once that the key was registered by the core (SET_VARIABLES in `azh_open`) and the value is listed (`citra_init_time` any decimal), else `AZH_E_ARG` naming the key; our core registers its six extra keys | phase-a "2. Facts" | holds | F2 |
| A6 | `azhost run` defaults are relative to the current directory; `--profile host/options-default.txt`; the library applies no profile; profile then `--opt`, later wins | phase-a "3. The API" | holds | F2 |
| A7 | `azh_version_ok` accepts `AZH_STOCK_VERSION "2126.2"` and that plus `AZH_LAZPY_SUFFIX "-lazpy.1"` (`host/pins.h`); host.log logs the core version at boot | phase-a; step A as built | holds | F2 |
| A8 | `png.c` writes PNGs with `compress2` at level 6, with a row stride ("step E tunes") | phase-a "4. Files"; as built | holds | E |
| A9 | The readback runs only on asked shot frames (run.c after `retro_run`, and `azh_shot`) | phase-2.md A19 | holds | E (the "readback only on asked frames" win is already true) |
| A10 | `azh_stats_t` fields: frames, wall_s, user_s, sys_s (rusage), peak_rss, core_name, core_version, is_lazpy_core; size 240 | phase-2.md A2, A17 | holds | E (CPU ms per frame), F2 |
| A11 | One `azh_open` per process (step A's as-built note A-N1) | `docs/reviews/phase-1-as-built.md` | holds | E (one worker per instance) |
| A12 | `log.c` writes the core's line literally (Phase 1 as-built fix A-X1) | phase-1-as-built review | planned (fix list) | F2 (the debug stop matches the literal line) |
| B1 | `build/testapp.3dsx`, built with devkitARM first in PATH | phase-b; item 130 | holds | all |
| B2 | `<sys>/Azahar/sdmc/testapp/control.txt` keys `draw=2d\|3d`, `break_at`, `exit_at`, `ready_at` (1-1,000,000), `boot_frames` (1-10,000) | phase-b "3. The app" | holds | all |
| B3 | Log lines: `start addr_global=0x%08lx addr_heap=0x%08lx size=%u mode=%s break_at= exit_at= ready_at= boot_frames=`; per frame `f= v= s= t= k= tx= ty= td= cx= cy=`; events `ready f= v=`, `booted`, `break`, `exit`; every line also to `svcOutputDebugString`, before the SD write | testapp/source/record.c:44-46, 58-61; sdlog.c (B as built) | holds | all |
| B4 | In 3D `v` is `C3D_FrameCounter(0)`, so `v == f`; the 3D loop draws with `C3D_FRAME_SYNCDRAW` | testapp/source/scene3d.c:77, 82-85; item 130 | holds | E |
| B5 | The record `laz_record` (32 bytes: magic 0x4C415A52 at 0, frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24 = `svcGetSystemTick`, logged as `s=`); a global `g_record` and a heap copy | testapp/source/record.h:14-21; main.c:24-25 | holds | G |
| B6 | Per frame: `hidScanInput`, `record_fill(&g_record)`, `memcpy` to the heap copy, then the log line from `g_record`; so a host write into the record is overwritten next frame and cannot change a log line | testapp/source/main.c:137-156 | holds | G (the write test targets the control struct instead) |
| B7 | `static laz_control g_ctl`: `int mode3d` 0, u32 `break_at` 4, `exit_at` 8, `ready_at` 12, `boot_frames` 16, `error_count` 20, `error_line[17]` 24 (u32); `run_events` reads `g_ctl.ready_at == f` every frame | testapp/source/control.h:11-19; main.c:23, 159-170 | holds | G |
| B8 | `LAZ_FRAME_CAP` 100,000,000; the app never exits on a button | testapp/source/main.c:16 | holds | E (60 s runs) |
| B9 | `tests/check_testapp.py`: `read_png_rgba`, `markers --top --bottom --mode 2d\|3d` | phase-b "4. Files" | holds | E, F2 |
| F1 | `core/patches/0000`-`0006` (identical in MAIN and `../libazahar-py-f1`, `diff -r` 2026-11-12): `lazpy_read_memory(uint32_t vaddr, void *buf, uint32_t len)` and `lazpy_write_memory(uint32_t vaddr, const void *buf, uint32_t len)`: 0 ok, -1 not running or no process (or an exception), -2 a page unmapped, -3 bad args (NULL, len 0, len > 0x4000000, `vaddr + len > 2^32`); every page checked with `IsValidVirtualAddress` before any byte moves; "call only between frames" | core/patches/0001-lazpy-memory-exports.patch | holds | G |
| F2a | `lazpy_movie_play(const char *path)`: 0 ok, -2 missing, -3 null, -4 invalid, -5 already booted, `""` clears | core/patches/0006 | holds | not used in Phase 3 |
| F3 | The six options in `core/options-lazpy.txt`: `citra_deterministic_async_operations=enabled`, `citra_async_fs_operations=disabled`, `citra_instant_debug_log=enabled`, `citra_init_clock=FixedTime`, `citra_init_time=946681277`, `citra_init_ticks_type=Fixed` | core/options-lazpy.txt; patch 0002 | holds | F2 |
| F4 | Patch 0003: our `retro_run` breaks out after `DisplayMessage` on a non-Success status; patch 0004: log filter Info plus `Debug_Emulated` at Debug; patch 0005: version `2126.2-lazpy.1` | core/patches/0003-0005 | holds | F2 |
| F5 | `nice -n 10 tools/build-core.sh --detach` in MAIN writes `build-core/build.pid`, `build.exit`, `build.log`; output `build-core/azahar_lazpy_libretro.dylib`; STAMP = hash of the patches; `LAZ_CORE_LTO=OFF` fallback | phase-f1; tools/build-core.sh | holds (the first build was running at cd2aadd) | F2 |
| C1 | ABI 2 frozen at C1: `azh_batch` 3348, `azh_result` 304 (`vblanks`, `message[256]` appended), `azh_stats` 240, `azh_layout` 6452 (`n_fields`, `fields[160]` of `{char name[32]; int32 offset, size}`), `const.*` rows for every enum and limit, `map.*` rows | phase-c 3.1-3.2 | planned | G (appends) |
| C2 | Map version 2; offsets 16 heartbeat, 24 stop code, 28 msg len, 32 msg[1024], 1056 dims, 1072 px_frame, 1080 frame_total, 1088 vblanks_total, 1096 msg_seq, 1100 pid, 1104 exit_code, 4096 pixels; size 695,296; bytes 1108-4095 free | phase-c 3.3 | planned | G |
| C3 | After each `retro_run`: first-frame check, heartbeat, frame and vblank totals, the shot, then the stops in priority order; every stop returns 0 | phase-c 3.4 | planned | E (timing line), G (watch rows go after the totals, before the shot) |
| C4 | On our core status 16 is `AZH_ACT_EXITED` (a flag; the batch stops when `retro_run` returns, `stop=guest_exited`); a crash is `AZH_ACT_ERROR` with no count; the exit path (`_exit`) runs only on the stock core and writes one fixed line to the log | phase-c 3.5 | planned | F2 |
| C5 | On our core a debug-text stop needs `citra_instant_debug_log=enabled` in the option store, else `AZH_E_ARG` naming the key; on stock `AZH_E_NEEDS_LAZPY_CORE` (P5) | phase-c 3.4 | planned | F2 |
| C6 | `azhost run` flags `--inputs`, `--sd-seed`, `--stop-file/--stop-text/--stop-every/--stop-new`, `--debug-stop`, `--wall-limit-ms`, `--frames N[,N2]`, `--raw-shot`, `--print-last-line`, `--save`; per-batch summary `... stop= first= last= vblanks= wall_ms_max= batch= msg=`; exit 10/11 when a batch stopped that way on our core; exit 7 for a debug stop on stock; `azhost layout` prints `abi=<n>` and every `fields[]` row | phase-c 6 | planned | F2, G |
| C7 | `tests/gate_c.py` scenarios a-f under `runs/c-gate/<id>/`, `--only`, PASS/FAIL lines, `runs/c-gate.rc`; c4 expects exit 7 on stock; f expects exit 10, map stop code 4 and `exit_code` 10; `tests/testapp_log.py` (`write_control`, `parse_log`), `tests/checks_c.py` (`boot_offsets`, `offsets_ok`, `touch_expected`) | phase-c 8 | planned | F2 (switches), G (regression) |
| D1 | Modules `__init__`, `_abi`, `_host`, `_worker`, `_map`, `_client`, `_paths`, `inputs`, `results`, `errors`, `emulator`; stdlib only, numpy optional | phase-d 4.1 | planned | E, F2, G |
| D2 | Worker spawn: `python -I -c "<...> main(int(sys.argv[1]))" <child fd> <pkg_parent>` with `pass_fds=(child_fd,)`, cwd the workdir, stderr to `worker.err` (P3); `subprocess` default `close_fds=True` | phase-d 4.2 | planned | E (adds the slot fd as `argv[3]` and to `pass_fds`) |
| D3 | Worker ops `start` (core, sysdir, log, map, options list (profile lines then caller's), app, state), `run`, `set_input`, `shot`, `save_state`, `load_state`, `stats`, `close`; replies `("ok", x)` / `("err", code, text)`; `os.nice(10)` in the worker | phase-d 4.1, 4.3 | planned | E (nice check), F2 (`start` gains `lazpy_options`), G (`read`, `write`) |
| D4 | Wait loop and death mapping: exit 10 during `run` gives a `RunResult(stopped_by="guest_exited")` and closes the Emulator; 11 `GuestError`; else `HostCrashed`; heartbeat timeout `HostTimeout` and SIGKILL of its own worker | phase-d 4.4 | planned | E (kill test), F2 |
| D5 | Errors: `LibAzaharError` base; `BootError`, `GuestError` (`.result`), `HostTimeout`, `HostCrashed`, `StateError`, `NeedsLazpyCore`, `HostError`; AZH_E_ARG becomes `ValueError`; `errors.from_code(code, text)` | phase-d 4.5 | planned | G (adds `GuestMemoryError`) |
| D6 | `Emulator(app, workdir, *, sd_seed=None, state=None, core=None, options=None, timeout=30.0, boot_timeout=300.0)`; workdir holds `sys/` (SD at `sys/Azahar/sdmc/`), `shots/`, `host.log`, `host.map`, `worker.err`; `run(frames, inputs=(), shots=(), *, stop_file, stop_text, stop_every, stop_new, debug_text, wall_limit, timeout) -> RunResult`; `run_frame()`, `set_keys(raw=)`, `screens()`, `shot()`, `save_state()`, `load_state()`, `stats()`, `sd`, `frame_total`, `pid`, `closed`, `close()`; "`emu.memory` is Phase G's" | phase-d 4.6 | planned | E, F2, G |
| D7 | `RunResult(frames, stopped_by, first_frame, last_frame, frame_total, vblanks, wall_s, message, shots)`, frozen dataclasses; `Stats(...)` mirrors `azh_stats` | phase-d 4.1 | planned | E, G (appends `watch`) |
| D8 | `_paths`: `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE` (else `<root>/dl/azahar/azahar_libretro.dylib`), `LAZ_MVK`, `LAZ_PROFILE` (else `<root>/host/options-default.txt`), all resolved absolute | phase-d 4.1 | planned | F2 (adds `LAZ_LAZPY_PROFILE`) |
| D9 | States: `<path>`, `<path>.sd/`, `<path>.meta` (`abi=`, `k=`, `frame_total=`, `vblanks_total=`, `created=`, `core_version=`, `app=`, `app_sha256=`); a different `core_version` only warns, the core decides; `abi` must equal `AZH_ABI_VERSION` | phase-d 3.1, 3.3 | planned | F2 (cross-core), G (ABI 3 makes ABI-2 states refused: section 8 risk 7) |
| D10 | Tests: `tests/python/conftest.py` fixtures `host_paths` (skip, or fail under `LAZ_REQUIRE_EMULATOR=1`, P2), `workdir` (`runs/d-pytest/<test>/`), `seed(**control_keys)`; marker `slow`; `fakeworker.py` modes | phase-d 5 | planned | E, F2, G |
| SD | SD file writes are synchronous on the emulator thread (file.cpp:200-217); OpenFile, SetSize, Close are async on the stock core | phase-2.md SD | holds | F2 |

## 7. Hours, against PLAN.md (agent wall time)

| Step | Builder | Review | Commit | Total | PLAN.md | Why the difference |
|---|---|---|---|---|---|---|
| E | 0.8 (E1 0.4, E2 0.4) | 0.2 | 0.1 | **1.1** | 1.0 | the live slot gate holds real slots while it tests a private cap (phase-e 6), a little more test code |
| F2 | 0.55 (F2-0 0.05, F2-1 0.25, F2-2 0.25) | 0.2 | 0.1 | **0.85** | 0.75 | the profile gap (P8) and the core-kind switches were not in PLAN's F2 |
| G | 0.6 (G1 0.4, G2 0.2) | 0.2 | 0.1 | **0.9** | 0.5 | PLAN's 0.5 h did not count the ABI 3 bump the watch list needs (header, `fields[]`, `_abi.py`, the map area) |
| Review loops | | | | 0.5 | 0.5 | |
| **Phase** | | | | **3.35** | **2.75** | |

## 8. Risks for this phase

1. **Our core's first build fails** or dies. F2-0 finds it; the patch fix and the incremental rebuild of section 2;
   E1 and the main loop's other work go on; E2 and G slip by the rebuild's machine time.
2. **Repeats are not identical on our core** (a host thread still leaks into guest time: the Vulkan presentation
   thread, shader compiles, an async path the option does not cover). F2 records the first differing log line and
   shot, does not tune, and reports; the main loop takes it to a review (a new patch is a Phase 3 change of scope).
3. **Torn reads in G**: `retro_run` returns after the slice in which the VBlank fired, so the guest may be part-way
   through `record_fill` for the next frame. G's checks allow a record whose fields all come from line f or f-1 and
   fail above 1 % of reads; the watch rows share the risk.
4. **F2's fixes touch Phase 2 files** that the as-built reviews of C and D may still be changing. F2 launches only
   after Phase 2 merges; its edits are narrow and listed (section 3).
5. **The control-struct write test depends on B's layout** (B7) and on the u32 pair (999001, 999002) appearing once
   near `addr_global`. G scans a bounded window and fails with the hit count if it is not exactly one.
6. **Timed runs overlap** another session's emulators. Each table row records the load at its start and end; the
   slot cap counts only libazahar's workers; rules.md 5. The cap rule (phase-e 7) is fixed in advance so a noisy
   number cannot be argued into a cap.
7. **ABI 3 makes Phase 2's ABI-2 state files refused** (D's meta check). The state files are run artefacts, not
   committed; G's report says so and USING.md gets one line. Gen3D's states made before G must be remade.
8. **The map grows to 4,890,624 bytes per instance** (the 4 MiB watch area). The file is `ftruncate`d, so unwritten
   pages cost no disk on APFS and no memory until touched. G measures `du -k host.map` and RSS in its report.
9. **A between-frames read touches GPU-cached pages** (VRAM, linear heap): `ReadBlock` flushes the rasterizer cache
   for them (memory.cpp:213-). It runs on the worker's one thread, the same thread as `retro_run` (the libretro
   thread, citra_libretro.cpp:284), so it is safe; G's brief says reads are only made by the thread that runs
   batches.
10. **The default cap rests on a light scene.** The test app's 3D scene is lighter than a game; the table labels it
    "light" (rules.md 7) and the cap stays marked provisional until a real-scene row exists (Q1 for Guy).

## 9. Hour-saving pass (revision 0)

| Existing thing or cut | What it saves | Verdict |
|---|---|---|
| The slot fd passed to the worker with `pass_fds` (and closed in the parent); no worker-side slot code, no protocol change | a worker op and a second owner of the lock | taken (E) |
| `concurrent.futures.ThreadPoolExecutor` for `Pool`; each job's Emulator in its own thread (the work is in the worker processes) | a scheduler | taken (E) |
| The kill-frees-slot check at the `_slots` level with a plain `python3 -I -c "sleep"` child, plus one Emulator-level kill | most of the slot gate's machine time | taken (E) |
| One batch per instance per row (`run(10_000_000, wall_limit=60)`) instead of timed loops of small runs | Python overhead in the numbers and code | taken (E) |
| A per-batch host.log timing line (Σ `retro_run` wall vs batch wall) instead of a profiler run | the host-share measurement; `/usr/bin/sample` on one worker for 10 s is an optional cross-check | taken (E) |
| D's `os.nice(10)` in the worker and A's readback-on-asked-frames (A9), C's raw frames | three of PLAN's E items need no code | taken (E: checked only) |
| One speed-table run giving both cores' rows (stock and ours) instead of two scripts | a second run later | taken (E) |
| A real Gen3D row by default | the optional row's set-up time | declined: optional, local-only, needs Guy (Q1) |
| `azhost --lazpy-profile` defaulting to `core/options-lazpy.txt` when our core is detected | every gate and user remembering a flag | taken (F2) |
| Two repeat checks reusing gate_c's input file and D's state-boot test shape | new scenario code | taken (F2) |
| A drain-only core export for D's restore (D 3.3's note) | `drain_ms` | declined unless F2's measured `drain_ms` is over half of `t_state` (then a Phase 4 item, not G: it needs a rebuild) |
| No core patch in G (the exports exist; no rebuild) | a 15-90 min machine rebuild and a re-gate | taken (G) |
| The write test through the control struct found by scanning for a seeded u32 pair, instead of a test-app change | a testapp edit, a rebuild of the `.3dsx`, B's gate rerun | taken (G) |
| `azhost` memory flags (`--read`, `--watch`) | 0.1 h | cut: Python is the memory interface; `azhost` keeps `layout` |
| Watch rows copied into `RunResult.watch` (immutable bytes) instead of zero-copy views into the map | the view-lifetime rules `screens()` needs | taken (G) |
| A ring buffer for unbounded watched batches | nothing needed now | declined: a batch that does not fit is `ValueError` naming the largest frame count; the caller splits |
| libmgba-py's `memory.u32.raw_read(addr)` as an alias on the same objects (gba-toolkit-share `tools/vsd_run.py`) | Gen3D porting cost | taken (G, three lines per width) |

## 10. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/` (GIT-COMMIT 219d743a1e698101fe1ab8bef43e6563126c3c27,
GIT-TAG 2126.2), read 2026-11-12. "PATCHES" = `core/patches/` (MAIN, identical to `../libazahar-py-f1/core/patches/`).

| Fact | Where |
|---|---|
| `BASE_CLOCK_RATE_ARM11 = 268111856`; one frame is 4,481,136 ticks (59.831 Hz); `MAX_SLICE_LENGTH` = clock / 234 | SRC core/core_timing.h:37, 40-42, 184 |
| `init_ticks_type` Random seeds the base ticks from `std::random_device`, so `s` starts at a random value on the stock core; Fixed uses `init_ticks_override` | SRC core/core_timing.cpp:37-44; common/settings.h:506-507 |
| `init_clock` SystemTime takes the host clock (plus DST hour); FixedTime takes `init_time` (default 946681277) | SRC core/hle/kernel/shared_page.cpp:34-63; common/settings.h:503-505 |
| `deterministic_async_operations` (default false) gates `std::async` in HLE requests | SRC common/settings.h:490-491; core/hle/kernel/hle_ipc.h:306, 348 |
| `instant_debug_log` (default false) makes the log backend write inline | SRC common/settings.h:659; common/logging/backend.cpp:353 |
| `retro_run` registers the core-loop thread, loops `RunLoop` until a frame is submitted, `DisplayMessage` on non-Success | SRC citra_libretro/citra_libretro.cpp:284-306 |
| `ReadBlock` zero-fills unmapped pages with a log line; copies `Memory` pages; flushes the rasterizer for cached pages | SRC core/memory.cpp:176-215 |
| `IsValidVirtualAddress`: a page pointer or a non-Unmapped attribute | SRC core/memory.cpp:824-837 |
| `CITRA_PAGE_SIZE` 0x1000 | SRC core/memory.h:34 |
| `Kernel::GetCurrentProcess()` | SRC core/hle/kernel/kernel.h:319 |
| The core's exported symbols come from `libretro.osx.def` via `-exported_symbols_list`; output name `azahar_libretro` | SRC citra_libretro/CMakeLists.txt:32, 96 |
| A savestate is refused if its program id differs or its revision is not `g_scm_rev` ("created from a different revision") | SRC core/savestate.cpp:292-306 |
| A build from the unified tarball takes `GIT_REV` from its `GIT-COMMIT` file, so our core's `g_scm_rev` is 219d743a...; the stock release was built from the same commit, so a stock state may load into ours (F2 records it) | dl/.../CMakeModules/GenerateBuildInfo.cmake:13-16; GIT-COMMIT |
| `retro_serialize_size`, `retro_serialize`, `retro_unserialize` | SRC citra_libretro.cpp:692, 712, 722 |
| `PollInput` runs from the window's VBlank path, once per VBlank | SRC citra_libretro/emu_window/libretro_window.cpp:198-206 |
| The memory exports check every page before `ReadBlock`/`WriteBlock`; codes -1/-2/-3; len cap 0x4000000; no 4 GiB wrap; try/catch to -1 | PATCHES 0001 (citra_libretro.cpp hunk at :746) |
| The `.def` gains `_lazpy_read_memory`, `_lazpy_write_memory` (0001) and `_lazpy_movie_play` (0006) | PATCHES 0001, 0006 |
| This Mac: 12 cores (6 performance), 18 GB RAM, load 17-24 at planning time; PLAN's load warning is above 2 x cpu_count = 24 | `sysctl`, `uptime`, 2026-11-12 |
| macOS `flock(2)`: locks belong to the open file description; two `open`s of one file in one process conflict; a lock held through an fd inherited by a child survives the parent's `close` and is dropped when the last fd to that description closes (the child's death) | `man 2 flock` (macOS); Python `subprocess` `pass_fds` docs |

## 11. Open questions

- **Q1 (for Guy): the real-scene row.** PLAN wants an optional Gen3D 3D-scene row, local only. It needs a game and a
  state from Gen3D (a field scene). Options: (a) Gen3D hands over a field-scene state file and its `.3dsx` path for
  one local run, never committed; (b) skip it and keep the default cap provisional, quoting spike 2's real-scene
  numbers (rules.md 5) beside the light table. The plan does (b) unless Guy says (a).
- **Q2 (for Guy): P7.** A new error class `GuestMemoryError` for unmapped guest memory, rather than reusing
  `ValueError` or `HostError`. Small, but it is public API.
- **Q3 (for Guy): the cap rule.** Phase E keeps cap 3 unless 3 instances give less than 1.25x the total throughput
  of 2 (then cap 2); it never raises the cap above 3 without a 4-instance row. Fixed before the run.
- Q4 (for review): should F2's stock regression (gate C and pytest on the stock core after F2's edits) be the
  phase-end full suite only, to save about 30 min of machine time? The plan keeps it in F2 because F2 edits the
  worker and the Emulator.
- Q5 (for review): the watch area size (4 MiB, about 52,000 rows of two 32-byte records). Enough for Gen3D's
  per-frame party/position watch over a long batch; the review may prefer a size field set at `azh_open`.

## 12. Interfaces for Phase 4 (H: docs, I: release)

- `Pool(n, app, root, **emulator_kwargs)` with `submit`, `map`, `close`; `LoadWarning`; `LAZ_MAX_INSTANCES`,
  `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT`; `<workdir>/slot.txt`.
- `docs/research/speed-table-e.md`: the numbers the README quotes, each with load and date, test-app rows labelled
  light; the default cap and its rule.
- `core/options-lazpy.txt` applied automatically on our core (P8); `azhost --lazpy-profile`; `LAZ_LAZPY_PROFILE`.
- `tests/gate_f2.py`'s results: repeat exactness, the debug-stop frame, cross-core state loading (for STATUS.md).
- ABI 3: `azh_read`, `azh_write`, `azh_watch`, the watch area, `AZH_E_UNMAPPED`; `emu.memory` with libmgba-py names;
  `run(watch=)`, `RunResult.watch`; `GuestMemoryError` (for `docs/HOST-API.md` and USING.md).
- The release (I) ships `azahar_lazpy_libretro.dylib` built from the patches as F2 gated them; any patch fixed in F2
  (risk 1) is the one released.

## 13. Changes from review 1

None yet (revision 0).

## 14. Changes from review 2

None yet.
