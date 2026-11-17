---
id: laz-713
title: lazpy
order: 713
kind: step
parent: laz-700
page: Windows proof: final checks, tag, and publish v1.1.0
hours: -
---
# Windows proof: final checks, tag, and publish v1.1.0

## What it is
Main loop: push main, CI green, tag, draft, publish on Guy's word.

## Exit gate
The W9 gate in the plan. Plan: `docs/plans/phase-7.md` line 354.

## Evidence
- 2026-11-17 23:26 started: W7c passed (item 711), Guy's word in item 712. Evidence files: runs/p7/w9/.

## Pointers
- Plan section: `docs/plans/phase-7.md:354`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- Exemption for step 3, the build-files gate (W8 audit P1, 2026-11-17 22:45): the diff from the core's build.inputs head 6345b83 to
  HEAD is empty except core/OPENSSL.md, which changed only in prose and its two .a shas after the CI build; its
  "- Source:" line (the only line build-core-win64.sh:92 and mkrelease read) must be identical. The gate passes on that.
- Guy's word (item 712): publish once Gen3D's and 3DP's release-candidate jobs PASS (item 711, W7c) and CI is green.
- The macOS workflows are started by hand now (Guy, 2026-11-17). STATUS's macOS line: Variant B says the v1.1.0 macOS
  changes "pass the CI build and fast tests", but test.yml last passed at 6000112 (16:01), before the host/version.c
  change. Dispatch test.yml and macos-live.yml once on the release commit; if no runner starts (cancelled after ~15 min,
  one mail), reword Variant B to what ran (no macOS CI on the last host changes) before the tag.
- Deviation (2026-11-17 23:27): STATUS's macOS line is written before the push so that it is true whatever the hand-started macOS
  runs do ("the emulator suite last ran on a Mac at v1.0.0 ... their host C tests ran on Windows"); neither variant
  sentence was kept. Step 4 waits for test-windows.yml green; test.yml and macos-live.yml are dispatched once on the
  pushed commit and waited on ~20 min: a real failure stops the tag, a run no runner picks up does not (Guy made them
  manual-only). Step 5 (macos-live's v1.0.0 fallback) is logged if that run starts, else recorded as not run.
