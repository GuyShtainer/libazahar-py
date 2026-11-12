<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 19:56 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-210: step C fixes B1, S1-S4 from the as-built review (sonnet), ends with the "C fixes done" report | ../libazahar-py-c | acae9a26ca38daf7c | report; then the main loop commits C2+C3, merges step-c, item 210 to done |
| laz-220: step D1 + D2 (Python package, worker, errors; state.c, statemeta.c; sonnet), ends with the "D1+D2 done" report | ../libazahar-py-d (step-d from 0651a8d) | a8301022e123dfae3 | D1+D2 committed b24c436; waits for C's api.c fix and C's merge, then main merged into step-d and D resumed for D3 |
| laz-300: Phase 3 plan review 1 (opus, fresh): writes `docs/reviews/` (phase-3-review-1.md) only | this repo | ab3db82a4ace714b2 | review written; then the author (aed5ccfac0370b719) writes revision 1 |

## Next steps, in order
1. Phase 2's plan is final (5f77e28; fix check all DONE, item 200's notes). C and D build after Phase 1 merges.
2. Phase 1 is done (item 100 in `5-done/`); our core is built (`build-core/azahar_lazpy_libretro.dylib`, 14 min),
   so Phase 2's timed gates may run (one at a time).
3. Phase 2's steps (C, D) build after Phase 1 merges. Phase 3's plan revision 0 is committed (item 300's notes); review 1 runs (above), then revision 1, review 2, revision 2. Phase 4: plan later.

## Waiting on Guy (only what blocks a step above)
- Phase 3 questions Q1-Q3 (real-scene speed row, the new GuestMemoryError class, the cap rule): item 300's notes.
  They block Phase 3's build, not its reviews; the plan's defaults hold until Guy answers.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/1-in-progress/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 4, 18:32); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
