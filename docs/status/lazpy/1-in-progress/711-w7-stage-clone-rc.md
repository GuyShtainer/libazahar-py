---
id: laz-711
title: lazpy
order: 711
kind: step
parent: laz-700
page: Windows proof: stage the release and prove a fresh clone works
hours: -
---
# Windows proof: stage the release and prove a fresh clone works

## What it is
Main loop: stage v1.1.0, clone_check on the PC from the bundle; W7c: Gen3D and 3DP each run one real job on the release candidate.

## Exit gate
The W7 and W7c gates in the plan. Plan: `docs/plans/phase-7.md` line 311.

## Evidence
- 2026-11-17 20:00 started. W5 is done (run 44138010543, DLL 9f45bca5...). Order: merge main into p7-docs (1.1.0
  lives there), bundle it to the PC, stage with mkrelease --inherit v1.0.0 --win-artifact D:/lazpy/p7/w5/art, then
  the pins. Guy 2026-11-17: no pushes for now. The PC crashed at 19:3x under 3DP + Gen3D load (WHEA cache error):
  one light PC job at a time until Guy has looked; the 4-copy clone_check waits for his word on the PC.

## Pointers
- Plan section: `docs/plans/phase-7.md:311`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
