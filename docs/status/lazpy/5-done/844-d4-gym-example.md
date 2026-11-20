---
id: laz-844
title: lazpy
order: 844
kind: step
parent: laz-840
page: Phase D: a gymnasium-style example over the test app
hours: -
---
# D4: the gym example

## What it is
Phase D: a gymnasium-style example over the test app.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane and in its CI workflow; the lane merged on main; the D5 review's findings fixed.

## Evidence
2026-11-20 16:34: lane merged on main: `examples/gym_env.py` (TestAppEnv) and test_gym_env.py, outside the promise; on the PC the live check (gymnasium's `check_env` plus 200 steps) printed "gym_env ok" on the v1.2.0 base host; the PC fast tests 359 passed, 6 skipped on the merged tree. 16:57: D5 review fixes merged. Done.

## Pointers
- Plan section: `docs/plans/phase-8.md:208`
- Briefs: `docs/plans/phase-8d-briefs.md`; review: runs/p8/d/d5-review.md (private)

## Lessons and notes
Read this part only when you work on this item.
