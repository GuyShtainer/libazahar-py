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
