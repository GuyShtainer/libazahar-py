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
