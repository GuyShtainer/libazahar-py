---
id: laz-825
title: lazpy
order: 825
kind: step
parent: laz-820
page: Phase B: test that pressing the same button twice registers twice
hours: -
---
# B4: re-press tests

## What it is
Phase B: test that pressing the same button twice registers twice.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:32: lane live merged on main; test_repress.py on the PC: 12 passed (A, ZL, ZR, touch; gaps 1-3 frames).
Waits on the phase B review.
2026-11-19 02:16: the review (docs/reviews/phase-8b-as-built.md, ready with changes) and its fixes merged (lanes fimg, flife, fmisc). Second full PC gate: 379 passed, 11 skipped, 1 xfailed (laz-829), 1 failed: test_m5_stock_core_refuses, a load flake (3 of 3 alone at 02:16; its boot retry doubled to 600 frames). Done.

## Pointers
- Plan row: `docs/plans/phase-8.md:169`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- One frame of release is enough for every input; USING section 4 says so.
