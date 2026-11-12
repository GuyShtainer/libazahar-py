<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 21:02 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-220: step D guest-exit fix (a guest_exited result closes the Emulator on both cores; sonnet), ends with "D exit fix done" | ../libazahar-py-d (step-d over c1e614e) | ac94c1b1d3eddad30 | report; then commit, the opus as-built review of D, merge |
| laz-300: Phase 3 plan revision 1 (opus, fresh author): edits `docs/plans/` (phase-3, e, f2, g) only | this repo | a848bdbe41c898002 | revision written; then review 2 |
| laz-400: Phase 4 plan review 1 (opus): writes `docs/reviews/` (phase-4-review-1.md) only | this repo | ab421b8f1945fcdfa | review written; then revision 1 |

## Next steps, in order
1. D fixes done: commit on step-d, then a fresh opus as-built review of D (writes docs/reviews/phase-2-d-as-built.md),
   fixes, merge step-d (runners.md and tools.md lines in the D reports, item 220's notes), items 220 and 200 to done.
2. After D's emulator tests end: rebuild our core in MAIN with -DENABLE_BUILTIN_KEYBLOB=OFF and -ffile-prefix-map
   in tools/build-core.sh (P9, item 400's notes), `nice -n 10 tools/build-core.sh --detach`, no timed run meanwhile.
3. Phase 3: revision 1 (above), then opus review 2 and revision 2; build after Phase 2 merges and the rebuild.
4. Phase 4: review 1 (above), then revision 1, review 2, revision 2; the ip-legal consult (phase-i.md 9.1)
   when an opus slot is free. At most 2 opus at once.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G1-G7 (item 400's notes): G1, rebuilding our core with the built-in key blob off before F2, is
  the main loop's default (more conservative); the rest block Phase 4's release, not its reviews.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/1-in-progress/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 4, 18:32); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
