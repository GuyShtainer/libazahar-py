<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 18:09 (this project's own session, which took over from the Gen3D session)

New project, nothing built yet. The repo, status folders, maps and research are in place (setup commit 2288e94);
the pre-commit hook runs status_check on main (Guy's yes, 2026-11-12). Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-100: Phase 1 plan review 2 (opus, fresh; reads review 1 only after its own findings), writes `docs/reviews/` (phase-1-review-2.md) only | this repo | a3e46afeb4c8d10cf | review written, then revision 2 by the plan's author (ad1f072f69021fa61) |
| laz-200: Phase 2 plan revision 1 from `docs/reviews/phase-2-review-1.md` (the plan's author, opus), edits `docs/plans/` (phase-2, c, d) only | this repo | a4bcf09ec00640830 | revised plan, then Phase 2 review 2 |

## Next steps, in order
1. Phase 1 (laz-100): plan drafted (`docs/plans/phase-1.md` and its three step files, commit dae8f49); review 1
   done (eea12c4); revision 1 done (21a152c); review 2 running; then revision 2. Nothing is built before it. `dl/` is
   already in fetch.sh's layout.
2. Then make one worktree per step at main (F1, A, B) and launch three sonnet builders; F1's core build runs
   detached and nice'd. Each step: opus as-built review, main loop merges and commits, the step file moves.
3. Phases 2, 3, 4 the same way (`docs/PLAN.md` section 3, grouping paragraph).
4. Agent budget (Guy 2026-11-12): 2 expensive at once when their phases don't depend on each other, up to 12 cheap.
   Phase 2's plan runs beside Phase 1's; it lists the interfaces it assumes from Phase 1, reconciled at review.

## Waiting on Guy (only what blocks a step above)
- Nothing.
The full list is generated into `docs/status/README.md`.

## Pointers
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 3); republish only inside the progress command or when Guy asks.
- The plan: `docs/PLAN.md` (its two questions for Guy, section 7, block nothing before phase F).
- Rules that bite every turn: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Everything else: `docs/map/README.md`.
