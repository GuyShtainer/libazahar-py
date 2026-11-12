<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 17:12 (this project's own session, which took over from the Gen3D session)

New project, nothing built yet. The repo, status folders, maps and research are in place (setup commit 2288e94);
the pre-commit hook runs status_check on main (Guy's yes, 2026-11-12). Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-100: Phase 1's plan (our core build, the host library, the test app; one opus), writes `docs/plans/` (phase-f1.md, phase-a.md, phase-b.md) only | this repo | ad1f072f69021fa61 | three plan files written |
| laz-200: Phase 2's plan (input, stops, Python, state boot; opus, in parallel with Phase 1's), writes `docs/plans/` (phase-2.md, phase-c.md, phase-d.md) only | this repo | a4bcf09ec00640830 | three plan files written |

## Next steps, in order
1. Phase 1 (laz-100), Guy's loop before any build: when the plan reports, commit it; opus review 1 (one fresh
   agent over all three files); revision by the plan's author; opus review 2; revision 2. Nothing is built before it.
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
