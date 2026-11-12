<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 21:18 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-220: step D as-built review (opus), writes `docs/reviews/` (phase-2-d-as-built.md) only | MAIN, reads ../libazahar-py-d (88cdbe6) | a1685c2425484d723 | fix list for D's builder (ac94c1b1d3eddad30); then merge step-d |
| laz-300: Phase 3 plan revision 1 written (committed); review 2 waits for an opus slot | this repo | main | review 2 (fresh opus), then revision 2 |
| laz-400: Phase 4 plan review 1 written (committed); revision 1 waits for an opus slot | this repo | main | revision 1, then review 2 |

## Next steps, in order
1. D fixes done: commit on step-d, then a fresh opus as-built review of D (writes docs/reviews/phase-2-d-as-built.md),
   fixes, merge step-d (runners.md and tools.md lines in the D reports, item 220's notes), items 220 and 200 to done.
2. Our core is rebuilt with the key blob off (P9 done, item 300's notes); F2 gates that binary.
3. Phase 3: opus review 2 of revision 1 (fresh reviewer; brief like review 1's, plus "check each review-1 fix"), then revision 2; build after Phase 2 merges and the rebuild.
4. Phase 4: review 1 (above), then revision 1, review 2, revision 2; the ip-legal consult (phase-i.md 9.1)
   when an opus slot is free. At most 2 opus at once.

## Waiting on Guy (only what blocks a step above)
- G8: rewrite this repo's history before the first push: commit 15d0323 names his personal address's local part
  (item 400's notes, review B2). Nothing is pushed; no remote exists.
- G3: the core links LibreSSL, whose licence the review reads as incompatible with GPLv3 (item 400's notes).
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
