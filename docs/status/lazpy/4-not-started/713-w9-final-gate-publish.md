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
none yet

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
