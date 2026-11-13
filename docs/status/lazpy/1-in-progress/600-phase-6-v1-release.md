---
id: laz-600
title: lazpy
order: 600
kind: phase
page: Version 1.0.0: every claim gated, a stable API promise, the first public release
hours: phase-6
---
# Phase 6: release v1.0.0

## What it is
Guy, 2026-11-13: "Ok i see why its not 1. Than do all the proper tests and builds to make it version 1". Close each
reason the release was 0.1 (untested poll-exact movie, provisional instance cap, the ABI promise, the macOS header,
no user confirmation), freeze the API under semantic versioning, and stage v1.0.0 as the first public release in
place of the never-published v0.1.0.

## Exit gate
`docs/plans/phase-v1.md` section 3, steps V0-V8 each at its gate; V9 waits on Guy.

## Evidence
none yet

## Pointers
- Plan: `docs/plans/phase-v1.md`
- Step K (V0): `docs/status/lazpy/1-in-progress/510-step-k-core-rev-2.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 10:58: plan revision 0 written; reviews 1 and 2 next.
- 2026-11-13 11:07: review 1 saved (`docs/reviews/phase-v1-review-1.md`); revision 1 answers it. Biggest changes:
  poll-exact movies leave 1.0 (no host call, no movie writer, the test app reads input once per frame); host and
  Python are one unit (the layout check refuses a mix); main's rebuild needs the PIN-nokeys URL moved to v1.0.0 and
  the nokeys tarball copied into dl/ first; the merge itself waits until Gen3D and 3DPlatinum run nothing.
- Guy, 2026-11-13 (during step K's gates): "Dont forget to use the gen3d and 3dp agents for real live testings" (V6).
- 2026-11-13 11:17: review 2 saved (`docs/reviews/phase-v1-review-2.md`); revision 2 answers it and is the plan
  work follows. The API review (V1, item laz-610) runs; 3DPlatinum was asked to leave the worktree before V1's edits.
- 2026-11-13 11:20, Gen3D (3ds-toolkit-1c), verbatim: "nothing in Gen3D uses main's libazahar-py right now. the GBA game's
  lane runs on the old Azahar app ... so you can merge and rebuild main whenever you like. The only cost is CPU load
  during our timed soak, which runs until about 11:55. A heavy build before then could add a frame gap. After that,
  build freely." So V0b's core build starts after 11:55.
- 2026-11-13 12:03: V1 is on the branch (64f5d18, item 610), under opus review. Step L's core patch (item 520) lands
  in `core/patches` before V0b's build, so V0b waits on the review's fixes and on step L's red-then-green repro.

