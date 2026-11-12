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
- For Phase 1's revision (from Phase 2's plan, 2026-11-12): two conflicts with B's draft. Break: B's gate expects no
  log line after svcBreak, but SVC::Break only sets status 14 and returns, so the guest runs on (PLAN gate C(e)).
  Slow boot: B's slow-boot frames are idle; D's "state boot under 10 % of the boot's wall time" needs them CPU-busy.
  Phase 2 also assumes 17 things of A and 9 of B (`docs/plans/phase-2.md` section 5): reconcile at revision.
- Main loop's choice (2026-11-12): one combined opus as-built review over F1, A and B once A and B have reported
  (fewer, larger opus runs, Guy's delegation rule), not one per step. Phase 1 = 2.85 h after revision 1.
