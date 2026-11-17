---
id: laz-712
title: lazpy
order: 712
kind: step
parent: laz-700
page: Windows proof: legal audit, then Guy's word to publish
hours: -
---
# Windows proof: legal audit, then Guy's word to publish

## What it is
release-legal-audit agent; then the main loop asks Guy for the publish word (quoted here verbatim).

## Exit gate
The W8 gate in the plan; Guy's publish word quoted below. Plan: `docs/plans/phase-7.md` line 343.

## Evidence
- 2026-11-17 22:28 started: release-legal-audit on candidate 309fd0e with runs/p7/w8/brief.md (staged copy refreshed).

## Pointers
- Plan section: `docs/plans/phase-7.md:343`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- For the audit (found in W5, 2026-11-17): the Windows core holds four components the macOS core does not and the W1b
  licence delta did not list: xbyak (BSD-3-Clause), zydis and zycore (MIT), all dynarmic's x86-64 backend; and glad
  (Azahar sets ENABLE_OPENGL on Windows), which ships no licence file: NOTICES-windows-x64.md quotes glad v0.1.36's
  README ("Public Domain, WTFPL or CC0"; GL spec Apache-2.0) and khrplatform.h's Khronos notice. Check those texts.
