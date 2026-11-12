---
id: laz-100
title: lazpy
order: 100
kind: phase
page: Phase 1, foundation: our patched core build, the host library and the test app
hours: phase-1
---
# Phase 1, foundation: our patched core build, the host library and the test app

## What it is
Our patched core (patches, pin, build script, first build), the C host library from the prototypes, and our own test app. Steps laz-110, laz-120, laz-130 (PLAN.md section 3: F1, A, B).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Fact-check before review 1 (sonnet a224ebd3b67974496, 2026-11-12): `docs/research/azahar-source-check.md`. The
  tarball verified and unpacked in `dl/azahar-src/` (429 MB, all submodules). Four line-number corrections for
  PLAN 2.7 (memory.h 577/621, SET_MEMORY_MAPS at environment.cpp:119, ParseCoreOptions at citra_libretro.cpp:228,
  savestate revision check at savestate.cpp:65-71); CMake 4 needs `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`.
