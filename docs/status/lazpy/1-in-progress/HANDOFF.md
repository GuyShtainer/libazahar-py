<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 18:34 (this project's own session; Guy said continue after the SlowStop)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-200: Phase 2 plan review 2 (opus, fresh), writes `docs/reviews/` (phase-2-review-2.md) only | this repo | a9a87f41abaabc096 | review written, then revision 2 by `a4bcf09ec00640830` |

## Next steps, in order
1. Both briefs from `docs/plans/next-briefs.md` are running (see above).
2. Commit each report and book its hours in `docs/hours.tsv`. Then Phase 2 revision 2 (resume `a4bcf09ec00640830`).
3. After Phase 1 revision 2: launch the three Phase 1 builders as the revised `docs/plans/phase-1.md` says
   (F1 core build, A host library, B test app; sonnet, worktrees at main; items 110/120/130 to `1-in-progress/`
   first). Review 2 changed the launch: F1 stops after configure; the main loop runs the core build in the main
   checkout after the as-built review.
4. Phase 2's steps (C, D) build after Phase 1 merges. Phases 3 and 4: plan with two review loops each, later.

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
