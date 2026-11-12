---
id: laz-200
title: lazpy
order: 200
kind: phase
page: Phase 2, control: input, touch, stop rules, the Python layer, savestates and state boot
hours: phase-2
---
# Phase 2, control: input, touch, stop rules, the Python layer, savestates and state boot

## What it is
Frame-exact buttons, touch and circle pad, stop rules and stop reasons, then the Python layer with savestates and starting a run from a saved state; Gen3D starts using the tool here. Steps laz-210, laz-220 (PLAN.md: C, D).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
- 2026-11-13 00:42: step C merged 7584a8d (gate_c 28 passed), step D merged a113cf6 (69 passed, 0 skipped); plan
  revision 2 after two opus reviews (5f77e28); as-built reviews `docs/reviews/phase-2-c-as-built.md` and
  `docs/reviews/phase-2-d-as-built.md`, every should-fix done.

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: `docs/plans/phase-2.md`, `phase-c.md`, `phase-d.md` (draft 3147409, revision 1 c54a7dd)
- Review: `docs/reviews/phase-2-review-1.md` (65ebefd); review 2 brief in `docs/plans/next-briefs.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Revision 1 (c54a7dd): both blockers fixed (raw shots in C2; builders end their run at a checkpoint and are
  resumed by message), all should-fix and nice except N4 (separate stop code 0, declined). C about 1.9 h, D about
  2.0 h, phase about 4.4 h with its review loops. Author agent id a4bcf09ec00640830.
- For Phase 2's revision 2, from Phase 1's revision 2 (commit after 6d421e2): `python3 -I` implies `-P` on 3.11+, so
  tests/testapp_log.py and D's tests insert the absolute tests/ path before `import check_testapp`; the core build
  starts in the main checkout after Phase 1's merge (F2 reads `build-core/azahar_lazpy_libretro.dylib` and
  build.log there); the stock core forwards svcOutputDebugString at debug level, so C's debug-text stop may work on
  stock with LAZ_LOG_LEVEL=debug; the test app's memory record is 32 bytes (magic 0, frame 4, vblank 8, keys 12,
  tx 16, ty 18, cx 20, cy 22, tick 24); rows A4, A18, B10, B11 and abi_layout/error-before-open now hold as written;
  A19 (readback after retro_run returns; azh_shot reads the last frame after a batch) and A6 (sysdir already in the
  state struct) are stated.
- Review 2 (`docs/reviews/phase-2-review-2.md`): 1 blocker, 10 should fix, 15 nice; ready after the fixes, no third
  loop (a main-loop check that each fix is in the text). X1: status 14 is set for every guest exception, not only
  svcBreak (exception_handler.cpp:80-142), so read the "Exception Type" line. S5 touches Phase 1's log.c (the core
  passes the finished line as the format string; write it literally), sent to the as-built review. S10: C3's gate and
  D3 wait for `build-core/build.exit`. Re-read C1's frozen header once before C1 starts.
- Revision 2 (a4bcf09ec00640830, 19:13): X1 and S1-S10 taken (S5 is Phase 1's as-built fix), N1-N15 taken; approved
  departures P1-P6 in phase-2.md section 5; declined: the X-macro header generator (C rule 8; const rows catch drift),
  the numpy touch oracle, debug-text stops on the stock core (late log thread; P5). C 2.0 h, D 2.1 h, phase about
  4.6 h. Frozen sizes: batch 3348, result 304, stats 240, layout 6452 (AZH_MAX_FIELDS 160). Still from Phase 1:
  log.c writes the core's line literally; optionally a getter for an option's current value. PLAN.md's state-boot
  line now says sha256, not program id (P4).
- Fix check after review 2 (a37dca8c056570872, 19:16): all 26 findings DONE in the plan text (S5 as moved to Phase
  1), no "be woken" and no checkpoint wait left in the briefs. Verdict: ready to build. Two loose-but-stated points:
  X1's synthetic cases live in test_msg.c, not messages.txt rows; a1's window is "planned frame plus 0 to 3" (a2
  holds the tight rule). Phase 2's plan is final; C and D build after Phase 1 merges.
