---
id: laz-330
title: lazpy
order: 330
kind: step
parent: laz-300
page: Reading and writing the game's memory
hours: -
---
# Step G: reading and writing the game's memory

## What it is
Memory reads and writes through our core's exported calls, the per-frame watch list, a clear error on the stock core.

## Exit gate
The gate in `docs/PLAN.md` line 310 ("Phase G"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:317`
- Phase plan: `docs/plans/phase-g.md` (the builder brief), `docs/plans/phase-3.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- G1 (a974a8613e6508e64, sonnet, 01:56-02:03; uncommitted in ../libazahar-py-g, progress in runs/g/progress.md):
  ABI 3 (map v3, 4,890,624 bytes; 137 fields[] rows of 160), new host/watch.c (pure) and host/mem.c (binds the two
  lazpy exports; a half-exported core fails at azh_open), the watch hooks in run.c between the frame and the
  shots, python/libazahar/memory.py, USING.md section 12a. make check and make clean; test-host 307782/0 (+39);
  pytest not slow 102 passed, 1 skipped. test_memory_live.py written, not run. G2 (runs/g/batch.sh: gate_c on our
  core, then the full pytest with test_memory_live.py) waits for E's runs/e-speed.rc; then resume the builder.
  Runners line: LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_memory_live.py.
