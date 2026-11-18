---
id: laz-822
title: lazpy
order: 822
kind: step
parent: laz-820
page: Phase B: write down what repeats run to run, and test it
hours: -
---
# B1: determinism table, digest helper, test

## What it is
Phase B: write down what repeats run to run, and test it.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:34: lane images merged on main; test_determinism.py on the PC 3 runs, 3 passed each (equal digests and
records at 300 and 600, tick seeds differ, held A across load_state). Waits on the phase B review.

## Pointers
- Plan row: `docs/plans/phase-8.md:166`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- USING 10a's rows for random bytes, console ID/MAC and workdir reuse come from the profile and code, not a test (the
  plan's test list did not ask for them).
