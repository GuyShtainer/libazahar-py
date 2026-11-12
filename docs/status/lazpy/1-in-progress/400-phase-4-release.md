---
id: laz-400
title: lazpy
order: 400
kind: phase
page: Phase 4, release: docs, the legal audit and the public GitHub release
hours: phase-4
---
# Phase 4, release: docs, the legal audit and the public GitHub release

## What it is
Docs with honest numbers, the release legal audit, and the release with our core and its full source. Push only on Guy's word. Steps laz-410, laz-420 (PLAN.md: H, I).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: `docs/plans/phase-4.md` (index), `phase-h.md`, `phase-i.md`
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Plan revision 0 (a867570428c4f7738, opus, 20:00-20:20). Hours about 2.25 h plus Guy (PLAN.md 1.1): H 0.75, I
  0.8, main loop and the two legal agents 0.3, review loops 0.4. Urgent: our built core contains Azahar's
  built-in 3DS console AES key blob: ENABLE_BUILTIN_KEYBLOB is ON by default (CMakeLists.txt:154),
  src/core/hw/default_keys.h is read by key.cpp:302-312; ON in
  build-core/build/CMakeCache.txt; the [removed] 13,960,800 of the dylib; Azahar's unchanged
  tarball holds the same header. Breaks the policy's no-key-handling rule. P9: -DENABLE_BUILTIN_KEYBLOB=OFF and
  -ffile-prefix-map (removes 461 home-path strings) in one rebuild before F2. P10: the source asset is Azahar's
  tarball minus default_keys.h, re-packed deterministically, with SOURCE.md proving from the build's .o.d files
  that no object read it. P11 NOTICES generated from the link line in I; P12 fetch.sh pins before the push; P13 a
  draft prerelease Guy publishes. Facts: LibreSSL static (advertising clause), SPIRV-Tools Apache-2.0 (so GPLv3
  only), faad2 GPLv2+, SoundTouch LGPL-2.1, no MPL code; system archives (font, Mii, country and bad-word lists)
  carry no licence file; Apple python3 is 3.9.6 (README: Python 3.10+); no git user.email is set, so tags set the
  identity. Guy: G1 rebuild key blob off before F2; G2 source-asset option after ip-legal; G3 LibreSSL (default:
  follow ip-legal, no core binary if it says counsel); G4 core binary under GPLv3; G5 create the GitHub repo on
  GuyShtainer; G6 "push"; G7 publish the draft (v0.1.0 prerelease). Review: Q1 P10(a) vs (b); Q2 attach
  libazhost.dylib; Q3 fast tests in H2's clone; Q4 commit release notes. The ip-legal consult brief is
  phase-i.md 9.1 (no build, can run now).
