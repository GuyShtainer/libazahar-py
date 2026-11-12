<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 00:42 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-220: step D as-built fixes S1-S6 and nice items (sonnet), ends with "D as-built fixes done" | ../libazahar-py-d (88cdbe6) | ac94c1b1d3eddad30 | report; then commit, merge step-d, items 220 and 200 to done |
| laz-300: Phase 3 plan revision 2 (opus, fresh; final, with OpenSSL 3 and patches 0007/0008) | this repo | ae13bb77d6994c473 | revision written; then the main loop's step 0 (P9b rebuild) and the builds |
| laz-400: Phase 4 plan revision 1 (opus, fresh) | this repo | a739c8de18f2e6992 | revision written; then review 2 |

## Next steps, in order
1. D fixes done: commit on step-d, then a fresh opus as-built review of D (writes docs/reviews/phase-2-d-as-built.md),
   fixes, merge step-d (runners.md and tools.md lines in the D reports, item 220's notes), items 220 and 200 to done.
2. Our core is rebuilt with the key blob off (P9 done, item 300's notes); F2 gates that binary.
3. Phase 3: opus review 2 of revision 1 (fresh reviewer; brief like review 1's, plus "check each review-1 fix"), then revision 2; build after Phase 2 merges and the rebuild.
4. Phase 4: review 1 (above), then revision 1, review 2, revision 2; the ip-legal consult (phase-i.md 9.1)
   when an opus slot is free. At most 2 opus at once.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft): item 400's notes. G1 (keys off, done), G3 and G8 answered;
  the rest block Phase 4's release, not its reviews.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/1-in-progress/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 4, 18:32); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
