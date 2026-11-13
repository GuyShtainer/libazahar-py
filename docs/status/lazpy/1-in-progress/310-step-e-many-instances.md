---
id: laz-310
title: lazpy
order: 310
kind: step
parent: laz-300
page: Many copies at once with a machine-wide cap, and the speed table
hours: -
---
# Step E: many copies at once with a machine-wide cap, and the speed table

## What it is
The instance pool, per-instance folders, the slot cap and nice; a 1-2-3 instance scaling run on the test app's 3D scene giving guest fps and CPU ms per guest frame.

## Exit gate
The gate in `docs/PLAN.md` line 296 ("Phase E"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:296`
- Phase plan: `docs/plans/phase-e.md` (the builder brief), `docs/plans/phase-3.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- E1 (a444b28ace71428a3, sonnet, 01:09-01:16) committed on step-e at a74aaec: _slots.py, pool.py,
  tools/hold_slot.py, tools/speed_table.py, test_slots.py, test_pool.py, test_pool_live.py (written, not run);
  host/png.c (azh_png_level, LAZ_PNG_LEVEL 0-9, default 1), host/run.c (png level line once; per batch
  "batch frames= wall_ms= core_ms= host_ms= shot_ms= stop=<name>"), _client.py (slot acquired before the Pipe,
  a _popen helper releases the slot fd on failure), __init__.py exports Pool, LoadWarning, SlotTimeout.
  make check, make, test-host 307743/0; pytest not slow 61 passed. Departures: g1/g2/g4 one test; the fixture takes
  min(3, cap) slots; speed_table sets LAZ_MAX_INSTANCES=4 in main(); LoadWarning shows at load 58. E2 next, after
  step-f2 merges (phase-3.md section 4 step 4).
- E2 run 1 (a444b28ace71428a3 resumed 01:56, forced hand-back 01:58): main merged into step-e at 8c06e26; make
  clean, pytest not slow 71 passed. Gate 2: test_pool_live.py 2 passed, 0 skipped (g1 the 4th Emulator waits with
  no slot.txt; g2 kill-to-acquire 0.063 s; g4 nice [10, 10, 10]); g3 fixed in the test (one seed folder per job,
  own_seed()). Gate 3: the speed table runs detached (speed_table.py, both cores, --extra-rows, out runs/e-speed;
  an EXIT trap writes runs/e-speed.rc). Left: read the table, the cap_rule line, set DEFAULT_CAP in _slots.py
  (stays 3 if any cap-core row is CHECK FAIL), write docs/research/speed-table-e.md (phase-e.md section 7). Only
  tests/python/test_pool_live.py changed since a74aaec.
- Speed table done 02:04 (rc 0; ../libazahar-py-e/runs/e-speed/table.md, light scene, nice 15): our core n=1 2177
  fps, n=2 3167 total, n=3 3540, n=4 3434; the stock core n=1 1652, n=2 2305, n=3 2779 (load 17-36 during its
  rows). Every check ok, slot waits 0. cap_rule on our core: 2 (n=2 x1.45 at load 15.1; n=3 x1.12, under x1.25).
  Round trip 0.11 ms per call; a shot 6.2 ms at PNG level 1, 5.8 ms at 6. The builder finishes DEFAULT_CAP=2 and
  docs/research/speed-table-e.md (no emulator).
- E2 done (a444b28ace71428a3, run 2, 02:05 report): DEFAULT_CAP = 2 in _slots.py, docs/research/speed-table-e.md
  (relative core paths), the own_seed fix in test_pool_live.py; all uncommitted on step-e. pytest not slow 71
  passed. Notes: DEFAULT_CAP 2 makes 3-job gates wait unless LAZ_MAX_INSTANCES is set (test_pool_live sets 3); the
  effective-options block starts with a stray "keys" line (the reviewer explains it). Opus as-built review
  a0d33437db53e74c5 launched 02:05 (phase-e.md section 12).
- As-built review (a0d33437db53e74c5, docs/reviews/step-e-as-built.md): no blocker; checklist 1-10 PASS; merge after
  S1-S5 (all on step-e: the live pool test's slot leak on a timeout, the option parse, the research doc's versions
  and reasons, p4's skipped load check, the slot left held when Pipe() raises). Fixer aabe4967660dca2d8 launched.
  The "keys" line is the host's own "core registered 38 option keys" log line caught by a loose parse, not key
  loading; our core's log has no key-file line. Held for main after step-g merges (NICE): N4 one host.log line per
  batch, N5 last_run_ns via a file static, N6 the long __all__ line, N10 the worker keeps the slot fd inheritable.
- After both merges (on main, review section on F2's timing): gate_f2.py:435-437 subtract b/slot.txt's waited_s
  from t_state and show it at :467; test_state.py:32-52 subtract a's wait from t_core_start and t_boot and b's from
  t_state, print both; run gate_f2 and pytest with no outer hold_slot.py (cap 2: the outer slot plus one Emulator
  uses both); gate_c.py:46-48 run_azhost takes a slot in-process (pass_fds), releases it after Popen, records
  waited_s; phase-3.md section 4 step 7 wraps only gate-a.sh's and gate-b.sh's direct azhost lines in hold_slot.py.
