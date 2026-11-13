<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 15:02 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing of this session. Peer work on main's core 64026f4a…: Gen3D (3ds-toolkit-1c) runs its Pool 1-4 (V6), on
our go at 15:00. 3DPlatinum's V6 chain ended (PASS, item laz-660's notes).

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`); "Sure, when ever you can finish these up" means
V6, V3, V7 and V8 now, V9 on his word.

## Next steps, in order
1. Record Gen3D's Pool 1-4 answer verbatim in item 600. A fail blocks V8.
2. V3 (real-scene multi-instance row): after Gen3D says its emulator work is done, load under 6, no other emulator
   or build in `ps`. Run `LAZ_MAX_INSTANCES=4 nice -n 10 env -u LAZ_ROOT -u LAZ_HOST -u LAZ_PROFILE -u
   LAZ_LAZPY_PROFILE python3 <scratchpad>/scene/v3scene.py <scratchpad>/scene/v3 "ours:1,stock:1,ours:2,ours:3,ours:4" 60`
   in the background (method in item 600's notes, 13:38). Look at the v3start/v3end shots. Then USING's speed
   table with date and machine, README's numbers, the cap (a CHECK FAIL keeps 2; a change edits
   `python/libazahar/_slots.py:25` and `tests/python/test_slots.py`), and STATUS drops "provisional".
3. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…, build.inputs head 4e830e5).
4. V7 full test pass (quiet), then V8 staging: fetch.sh's TBD pins (the core zip of 64026f4a…, the test app
   ba106998…), and the legal re-audit (16 of 16 on the final HEAD). The audit also checks history for game names
   (item 600's 13:16 note).
5. V9: Guy's word for the tag and push. After he publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0,
   items 420, 400 and 600 closed, the three private history bundles deleted, and tell the PC worker session
   (3ds-toolkit-11) "v1.0.0 is out" so it rebases its Linux port (item 500's PC worker notes: our 8 conditions).
6. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md` (V0b-V6 notes, the V3 method),
  `docs/status/lazpy/5-done/660-step-m-state-restore-shader-cache.md` (the restore fix, both V6 answers),
  `docs/status/lazpy/5-done/510-step-k-core-rev-2.md` (the core gates), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim, the Linux port), `docs/status/lazpy/1-in-progress/420-step-i-release.md`, `docs/status/lazpy/1-in-progress/400-phase-4-release.md`.
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
