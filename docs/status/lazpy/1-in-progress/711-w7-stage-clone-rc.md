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
- 2026-11-17 20:03 W7 step 1 staged on the PC from p7-docs cadcc30 (main merged in; the build files equal 6345b83, 0 diff
  lines): mkrelease --inherit v1.0.0 rc 0, the seven inherited assets and five repo pins ok; D:/lazpy/rel/v1.1.0
  SHA256SUMS sha256 711634f8cef341c8264acf215cebc76ae76ca2b59e611f174ff9df6ca6f51c8a (log runs/p7/w7/stage.out).
  Windows zip sha256 791efc1a...; the Mac zip and test app equal the v1.0.0 pins.
- 2026-11-17 20:03 W7 step 2 pins on p7-docs: fetch.sh REL_TAG=v1.1.0 (REL_TAG_PREV v1.0.0), LAZPY_CORE_SHA_WIN. Found:
  the DLL's OPENSSLDIR is "/opt/lazpy/openssl-3.6.5-mingw64/C:/Program Files/Common Files/SSL" (Configure runs on
  Linux, sees C:/ as relative and joins the prefix), not the planned Windows path: the guest's HTTPS finds no CA file
  on Windows. STATUS, USING, the release notes and core/OPENSSL.md say so; core/OPENSSL.md also gets the two .a shas
  of run 44138010543. DEVIATION for W9 step 3: core/ is a build file, so `git diff 6345b83 HEAD -- build files` is
  not empty; it holds only core/OPENSSL.md prose and the two .a shas, never the "- Source:" line the build reads.
  W8's auditor and W9's gate check exactly that. Re-stage after this commit (the build-files asset is HEAD's).

## Pointers
- Plan section: `docs/plans/phase-7.md:311`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
