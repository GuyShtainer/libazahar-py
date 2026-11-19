---
id: laz-824
title: lazpy
order: 824
kind: step
parent: laz-820
page: Phase B: image compare, a pass/fail example, one exit-code table
hours: -
---
# B3: compare, verdict, exit codes

## What it is
Phase B: image compare, a pass/fail example, one exit-code table.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:34: lane images merged on main; test_images.py + test_api.py on the PC 26 passed; fast suite 263
passed, 5 skipped; examples/verdict.py exits 0 on the test app and 2 on a bad path. Waits on the phase B review.
2026-11-19 02:16: the review (docs/reviews/phase-8b-as-built.md, ready with changes) and its fixes merged (lanes fimg, flife, fmisc). Second full PC gate: 379 passed, 11 skipped, 1 xfailed (laz-829), 1 failed: test_m5_stock_core_refuses, a load flake (3 of 3 alone at 02:16; its boot retry doubled to 600 frames). Done.

## Pointers
- Plan row: `docs/plans/phase-8.md:168`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- compare: `pixels` = differ at all, `over` = a channel off by more than max_delta, `within` = over <= max_pixels.
- The test app writes no PASS/FAIL, so verdict.py waits on its boot line; codes 1, 12, 13 were not run live.
- docs_check's links check fails on the PC lane only because the lane has no .git; run docs_check on the Mac.
