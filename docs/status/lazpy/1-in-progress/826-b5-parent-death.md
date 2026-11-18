---
id: laz-826
title: lazpy
order: 826
kind: step
parent: laz-820
page: Phase B: workers die when the script that started them dies
hours: -
---
# B5: parent death

## What it is
Phase B: workers die when the script that started them dies.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase B review passed.

## Evidence
2026-11-19 01:35: lane life merged on main; test_parent_death.py on the PC 12 passed (live: between batches,
mid-batch, during boot; worker gone in under 0.1 s, slot free). Removing the job assignment made the mid-batch case
fail (the test can fail). Waits on the phase B review and the macOS live check.

## Pointers
- Plan row: `docs/plans/phase-8.md:170`
- Briefs: `docs/plans/phase-8b-briefs.md`

## Lessons and notes
Read this part only when you work on this item.

- macOS kqueue path: unit tests with a stand-in select only; the live check waits for the Mac.
- Linux: a worker mid-batch still ends only between batches; USING section 8 says so.
- Main-loop fix at merge: the watch exits at once when the worker starts already reparented (ppid 1).
