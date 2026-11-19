---
id: laz-821
title: lazpy
order: 821
kind: step
parent: laz-820
page: Phase B: the release check stops printing PASS for a check that did not run
hours: -
---
# B0: release check 13 SKIP/PEND

## What it is
Phase B: the release check stops printing PASS for a check that did not run.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:29: built in lane rel and merged on main; `release_check.py --self-test` 2 of 2 on the Mac and on
the PC. Waits on the phase B review.
2026-11-19 02:16: the review (docs/reviews/phase-8b-as-built.md, ready with changes) and its fixes merged (lanes fimg, flife, fmisc). Second full PC gate: 379 passed, 11 skipped, 1 xfailed (laz-829), 1 failed: test_m5_stock_core_refuses, a load flake (3 of 3 alone at 02:16; its boot retry doubled to 600 frames). Done.

## Pointers
- Plan row: `docs/plans/phase-8.md:165`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- `--self-test` did not exist before this step; it was added here and covers only the copy-absent case (it must
  never read the copy). A normal run without the copy now prints SKIP 13; a `--pre-push` run must be on a machine
  that has the copy, or it fails.
