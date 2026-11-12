<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 19:40 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-210: step C2 then C3 (run loop, inputs, stops, raw shots; azhost flags, seeding, gate_c.py; sonnet); C3's gate waits for the core build | ../libazahar-py-c (step-c, C1 at 0651a8d) | acae9a26ca38daf7c | C report; then the opus as-built review of C |
| laz-220: step D1 + D2 (Python package, worker, errors; state.c, statemeta.c; sonnet), ends with the "D1+D2 done" report | ../libazahar-py-d (step-d from 0651a8d) | a8301022e123dfae3 | report; after C merges, main merged into step-d and D resumed for D3 |
| laz-100: our core's first build, detached and nice'd in MAIN (`tools/build-core.sh --detach`) | MAIN build-core/ | main | `build-core/build.exit` written (or the pid dies); waiter reports |
| laz-300: Phase 3 plan (opus): writes `docs/plans/` (phase-3, e, f2, g) only | this repo | aed5ccfac0370b719 | plan written; then review 1 |

## Next steps, in order
1. Phase 2's plan is final (5f77e28; fix check all DONE, item 200's notes). C and D build after Phase 1 merges.
2. Phase 1 merged to main (A, B, F1 done). When the core build exits: record it in item 100, close Phase 1, remove the
   four worktrees (`git status --porcelain` empty first) and branch int-1. Phase 2's C (C2/C3) and D (D1/D2) run side
   by side (`docs/plans/phase-2.md` section 2); timed gates wait for `build-core/build.exit`.
3. Phase 2's steps (C, D) build after Phase 1 merges. Phase 3's plan is being written (above); then two review loops. Phase 4: plan later.

## Waiting on Guy (only what blocks a step above)
- Nothing.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/1-in-progress/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/1-in-progress/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 4, 18:32); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
