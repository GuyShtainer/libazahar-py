<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

SLOWSTOP DONE 2026-11-12 18:27

As of: 2026-11-12 18:27 (this project's own session, end of Guy's SlowStop)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| Nothing (laz-100 and laz-200 are planning; no agent, job, worktree or merge open) | main at 6d421e2 | main | - |

## Next steps, in order
1. Both briefs are ready at `docs/plans/next-briefs.md`; dispatch them side by side (2 opus at once is allowed):
   Phase 1 plan revision 2 (laz-100, resume `ad1f072f69021fa61`) and Phase 2 plan review 2 (laz-200, a fresh opus).
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
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
