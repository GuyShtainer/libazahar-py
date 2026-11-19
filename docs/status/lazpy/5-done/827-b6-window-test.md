---
id: laz-827
title: lazpy
order: 827
kind: step
parent: laz-820
page: Phase B: prove on Windows that no window ever opens
hours: -
---
# B6: window test with a positive control

## What it is
Phase B: prove on Windows that no window ever opens.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:32: lane live merged on main; test_windows_windows.py on the PC: 2 passed, 1 skipped (the foreground
check, over SSH). Waits on the phase B review.
2026-11-19 02:16: the review (docs/reviews/phase-8b-as-built.md, ready with changes) and its fixes merged (lanes fimg, flife, fmisc). Second full PC gate: 379 passed, 11 skipped, 1 xfailed (laz-829), 1 failed: test_m5_stock_core_refuses, a load flake (3 of 3 alone at 02:16; its boot retry doubled to 600 frames). Done.

## Pointers
- Plan row: `docs/plans/phase-8.md:171`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- The worker is python.exe; the test checks its pid, its children and azhost.exe children of the test. Other
  projects' azhost.exe are not flagged.
- The foreground check has never run (SSH only); it needs a logged-in desktop sitting. USING says it is unchecked.
