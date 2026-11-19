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

## Pointers
- Plan row: `docs/plans/phase-8.md:167`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- SlotTimeout keeps the fields but its own __str__ hides the evidence line.
- test_api.py has no list for class attributes, so .workdir/.log_path are not in a frozen list yet.
