---
id: laz-706
title: lazpy
order: 706
kind: step
parent: laz-700
page: Windows proof: release tools that work on Windows
hours: -
---
# Windows proof: release tools that work on Windows

## What it is
Sonnet agent: Windows modes for fetch, mknotices, mkrelease, release_check (--inherit v1.0.0), clone_check.

## Exit gate
The W2b2 gate in the plan. Plan: `docs/plans/phase-7.md` line 259.

## Evidence
- 2026-11-17 12:43: dispatched.
- 2026-11-17 13:07 W2b2 gates PASS on the PC, on branch p7-w2b2 (e72b1ae, e3d839f): sh -n OK on 4 scripts;
  tests/fetch_fallback.sh "7 cases passed, 0 failed"; release_check --plant-red 24/24 plants fail on their own
  reason (rc 0; the new convention, v1.0.0's was 1); mkrelease --inherit on the real v1.0.0 assets, 13 assets,
  release_check reds only where expected (stand-in DLL, v1.0.0 pins); clone_check --until host rc 0, "307983 checks,
  0 failed" on a scratch merge with p7-w2a + p7-docs. Fixed: MSYS shasum `*name` output; README fetch line with a
  comment. Open for W3/W5: licence markers vs the verbatim mingw-w64 files; LAZPY_CORE_SHA_WIN TBD (W7); the full
  clone_check past --until host not run.
- 2026-11-17 13:12: done; merged into p7-int (9bb34ef) for the W3 fix check. Gates not run here move on: make check
  and actionlint run in CI after the W4 push.

## Pointers
- Plan section: `docs/plans/phase-7.md:259`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
