<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 18:49 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-300: Phase 3 plan (opus): writes `docs/plans/` (phase-3, e, f2, g) only | this repo | aed5ccfac0370b719 | plan written; then review 1 |
| laz-110: step F1, our core's pin, patches, options profile, build script; configure and planted reds only, no build (sonnet) | ../libazahar-py-f1 (step-f1) | a85f3abcf6d608824 | fixing F1-S1 and nice items from the as-built review (mergeable as is); then the integration run |
| laz-120: step A, host library and azhost CLI, gate-a (sonnet) | ../libazahar-py-a (step-a) | a4e8c6931d1122bf4 | fixes done 19:17 (gate-a 8/8, twice in a symlinked clone); waits for the re-check |
| laz-130: step B, test app and checker, gate-b (sonnet) | ../libazahar-py-b (step-b) | ab76e8c1f445db1b3 | fixing B-X1, B-S1..S4 and nice items; then the integration run |

## Next steps, in order
1. Phase 2's plan is final (5f77e28; fix check all DONE, item 200's notes). C and D build after Phase 1 merges.
2. Phase 1 builders fixing the as-built review's lists (`docs/reviews/phase-1-as-built.md`); a short re-check of the
   fixed items (resume `a9d6a1a04a7ae2c40`), then branch commits, the integration run on `int-1`, the merge to main, then the
   core build in MAIN and its waiter. Every step is in `docs/plans/phase-1.md` "Merge and launch".
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
