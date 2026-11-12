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
- 2026-11-12: plan, review 1 (eea12c4), revision 1 (21a152c), review 2 (6d421e2), revision 2 (62fa531); built in
  three worktrees, as-built review and re-check (`docs/reviews/phase-1-as-built.md`), integration run on int-1 green
  (gate-a 8/8, RUNNER=azhost gate-b 14/14, zero warnings), merged to main 570eebf; steps 110, 120, 130 done.
- 2026-11-12 19:40: our core's first build in MAIN, `build-core/build.exit` = 0 after 14 min (nice'd, load ~28):
  `build-core/azahar_lazpy_libretro.dylib` (19,195,472 bytes) exports `lazpy_read_memory`, `lazpy_write_memory`,
  `lazpy_movie_play`; version string carries `-lazpy.1`; the one warning is ld's duplicate-library note. The core's
  test-set gate is step F2 (Phase 3).

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
- For Phase 1's revision 2 (from Phase 2's review 1): the test app must never exit on START (B10); expose
  `check_testapp.py`'s PNG decoder as a function so D reuses it; raw screen pixels (`AZH_FMT_RAW`) move to step C2.
- Phase 2's revision 1 (c54a7dd) adds for revision 2: phase-a says `azh_boot` runs no `retro_run` and the
  missing-first-frame check happens in the first batch frame (A4); "until D" becomes "until C" at phase-a.md:186,
  :238-239 and in phase-1.md's Interfaces for Phase 2 (A18); never-exit-on-START stated as a rule in phase-b section 3
  (B10); `read_png_rgba(path) -> (width, height, rgba_bytes)` in check_testapp.py, RGB expanded to RGBA, CLI behind
  `__main__`, importable under `python3 -I` (B11).
- Review 2 (`docs/reviews/phase-1-review-2.md`): 2 blockers, 9 should fix, 12 nice; ready to build after revision 2
  takes X1 (Interfaces for Phase 2 incomplete), X2 (`laz_record` is 40 bytes, not 32), S1 (F1 stops after configure;
  main loop builds detached in the main checkout), S3/S4 (liveness checks), S5 (wait-idle under the queue mutex) and
  S7 (cross-step gates on a throwaway merge). No third review loop.
- Revision 2: every review-2 finding and Phase 2's five asks taken, none declined. F1 0.75 h, A 1.15 h, B 0.9 h,
  phase 2.8 h; main-loop integration about 0.2 h. Launch and merge order: `docs/plans/phase-1.md` "Merge and launch".
- As-built review (`docs/reviews/phase-1-as-built.md`, a9d6a1a04a7ae2c40): A mergeable after A-X1 (log.c formats the
  guest line) and A-X2 (gate-a breaks when vendor is a symlink); B after B-X1 (gate-b writes into runs/ before it
  exists); F1 mergeable as is (F1-S1 unpack failure not caught, unreachable under the sha pin). Its scratch
  integration (main + A + B): make and make testapp exit 0, gate-a 8/8 on testapp.3dsx, RUNNER=azhost gate-b 13/14
  (the fail is B-X1), so A and B fit. F1's patches checked by hand against 2126.2 signatures; no C++ compiled yet.
  At merge: add host/azh_pure.h to code.md; note lazpy_movie_play's -5 in phase-c; until A-X2 lands, copy vendor in
  the integration clone. untar_checked.py needs Python 3.12+ (filter=).
- Re-check (19:24, appended to the as-built review): A, B, F1 all mergeable; F1 leftovers N5 (`${OUT##*members=}`
  returns the whole output when no members= line) and N6 (OUT reused for the dylib path) optional, sent to F1.
