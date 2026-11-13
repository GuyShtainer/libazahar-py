<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 13:11 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing of this session. Gen3D's smoke plus Pool 1-4 and 3DPlatinum's A3 + chain with A4 run on main's core
64026f4a… as peer work (step 1). Worktree ../libazahar-py-m is removed; branch core-rev3 stays at aa29901 (merged).

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`). Main 4e830e5 holds core patch 0011 (item laz-660):
the state-restore crash Gen3D's first V6 smoke found is fixed and gated; core sha256 64026f4a… replaces 88cc6188.

## Next steps, in order
1. V6 on 64026f4a…: 3DPlatinum (3ds-toolkit-f4) started its A3 self-test at 13:10, then the chain with A4; Gen3D
   (3ds-toolkit-1c) reruns lazgame.py and Pool 1-4. Record each answer verbatim in item 660 (the restore) and 600.
   Both pass: item 660 to 5-done with a STATUS.md works line. A fail blocks V8.
2. No core/ edit or build-core.sh run on main from here (the gated build is 64026f4a…, build.inputs head 4e830e5).
3. V3 (real-scene multi-instance row, `docs/plans/phase-v1.md` V3): only on a quiet machine, after both projects'
   V6 runs end (rule T). Then README's numbers and the cap (a CHECK FAIL keeps 2).
4. V7 full test pass (quiet), then V8 staging, NOTICES.md from mknotices, fetch.sh's TBD pins (the core zip of
   64026f4a…, the test app ba106998…), and the legal re-audit (16 of 16 on the final HEAD). The audit also checks
   history for game names (three were removed from docs on 2026-11-13; older commits may hold more).
5. V9: Guy's word for the tag and push (below). After he publishes: I5 (`docs/plans/phase-i.md` section 6) against
   v1.0.0, items 420, 400 and 600 closed, then delete the three private history bundles.
6. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/660-step-m-state-restore-shader-cache.md` (step M),
  `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md` (V0b-V4 notes, the test app's sha256),
  `docs/status/lazpy/5-done/520-step-l-stencil-readback.md` (the last core patch: its build and gate route),
  `docs/status/lazpy/5-done/510-step-k-core-rev-2.md` (the core gates), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim), `docs/status/lazpy/1-in-progress/420-step-i-release.md`, `docs/status/lazpy/1-in-progress/400-phase-4-release.md`.
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
