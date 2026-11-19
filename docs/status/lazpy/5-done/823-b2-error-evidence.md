---
id: laz-823
title: lazpy
order: 823
kind: step
parent: laz-820
page: Phase B: errors carry the workdir, the log and the newest screenshot
hours: -
---
# B2: evidence on failure

## What it is
Phase B: errors carry the workdir, the log and the newest screenshot.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:35: lane life merged on main; fast suite on the PC 268 passed, 5 skipped; test_live_errors.py -k
"crash_error or sigsegv" 2 passed. Waits on the phase B review.
2026-11-19 02:16: the review (docs/reviews/phase-8b-as-built.md, ready with changes) and its fixes merged (lanes fimg, flife, fmisc). Second full PC gate: 379 passed, 11 skipped, 1 xfailed (laz-829), 1 failed: test_m5_stock_core_refuses, a load flake (3 of 3 alone at 02:16; its boot retry doubled to 600 frames). Done.

## Pointers
- Plan row: `docs/plans/phase-8.md:167`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- SlotTimeout keeps the fields but its own __str__ hides the evidence line.
- test_api.py has no list for class attributes, so .workdir/.log_path are not in a frozen list yet.
