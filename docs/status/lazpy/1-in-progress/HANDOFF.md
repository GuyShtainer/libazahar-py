<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 18:20 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing of this session. V6 is done (both projects pass on 64026f4a…), V3 is done (cap 4, item 600's notes).
Gen3D's two harness agents may run single-instance checks on main's core; Gen3D messages when they end.

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`); "Sure, when ever you can finish these up" means
V7 and V8 now, V9 on his word.

## Next steps, in order
1. V7 full test pass: after Gen3D's message, ask Gen3D, 3DPlatinum (3ds-toolkit-f4) and the PC worker
   (3ds-toolkit-11) to hold emulator runs and builds, check load under 6, then run `sh <scratchpad>/v7.sh >
   runs/v7/v7.log 2>&1` in the background (it makes the v1.0.0 state fixture with `tools/mkfixture.py`), then
   message "done" to all three. Gate: 0 failed, 0 unexpected skips (test_api.py:109 may skip by design), counts
   in item 600's Evidence.
2. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…, build.inputs head 4e830e5).
3. V8 staging (`docs/plans/phase-v1.md` V8): the test app rebuilt under `env -i` and compared, `sh
   tools/mkrelease.sh v1.0.0`, fetch.sh's TBD pins (the core zip, the test app ba106998…), commit, mkrelease
   again, clone_check, then the release-legal-audit agent on the repo, its history (item 600's 13:16 note: game
   names in three old commits) and the staged assets (16 of 16 on the final HEAD).
4. V9: Guy's word for the tag and push. After he publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0,
   items 420, 400 and 600 closed, the three private history bundles deleted, and tell the PC worker session
   "v1.0.0 is out" so it rebases its Linux port (item 500's PC worker notes: our 8 conditions).
5. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md` (V0b-V6 notes, V3's result),
  `docs/status/lazpy/5-done/660-step-m-state-restore-shader-cache.md` (the restore fix, both V6 answers),
  `docs/status/lazpy/5-done/510-step-k-core-rev-2.md` (the core gates), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim, the Linux port), `docs/status/lazpy/1-in-progress/420-step-i-release.md`, `docs/status/lazpy/1-in-progress/400-phase-4-release.md`.
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
