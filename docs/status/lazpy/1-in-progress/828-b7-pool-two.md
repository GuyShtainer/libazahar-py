---
id: laz-828
title: lazpy
order: 828
kind: step
parent: laz-820
page: Phase B: pool test with two live copies
hours: -
---
# B7: pool test at 2 live copies

## What it is
Phase B: pool test with two live copies.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:32: lane live merged on main; test_pool_live.py -k b7 on the PC (--copies 2): 1 passed. Waits on the
phase B review.

## Pointers
- Plan row: `docs/plans/phase-8.md:172`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- g1/g2/g4 moved into check_cap_kill_and_nice(cap); the 3-copy test was not rerun (the PC allows 2 copies). It must
  run once at 3 copies where that is allowed (CI or the Mac when free) to confirm the refactor.
- The real-slot holder takes 3 slots even under LAZ_MAX_INSTANCES=2 (the fixture clears it): existing design.
