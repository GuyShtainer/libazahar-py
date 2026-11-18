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

## Pointers
- Plan row: `docs/plans/phase-8.md:171`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- The worker is python.exe; the test checks its pid, its children and azhost.exe children of the test. Other
  projects' azhost.exe are not flagged.
- The foreground check has never run (SSH only); it needs a logged-in desktop sitting. USING says it is unchecked.
