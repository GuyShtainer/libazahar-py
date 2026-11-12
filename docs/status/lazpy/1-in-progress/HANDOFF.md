<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 17:02 (this project's own session, which took over from the Gen3D session)

New project, nothing built yet. The repo, status folders, maps and research are in place (setup commit 2288e94);
the pre-commit hook runs status_check on main (Guy's yes, 2026-11-12). Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-20, laz-21, laz-22: phase plans for our core build, the host library and the test app (one opus), writes `docs/plans/` (phase-f1.md, phase-a.md, phase-b.md) only | this repo | ad1f072f69021fa61 | three plans written |

## Next steps, in order
1. When the phase plans report: commit them; make one worktree per phase at main (F1, A, B); launch three sonnet
   builders, one per worktree, each from its plan. F1's full core build runs detached and nice'd.
2. Each phase: opus diff review, main loop merges and commits, the item moves with Evidence.
3. Then C (needs A and B), D, E and F2, G, H, I in plan order (`docs/PLAN.md` section 3).
4. Agent budget: 1 expensive (plus 1 extra Guy allowed for now) and up to 6 cheap at once.

## Waiting on Guy (only what blocks a step above)
- Nothing blocks the steps above. The progress page is not made yet: the call that makes it was blocked twice by
  the auto-mode classifier and needs Guy to approve or run it (`docs/status/lazpy/3-waiting-on-guy/ask-01-progress-page.md`).
The full list is generated into `docs/status/README.md`.

## Pointers
- The plan: `docs/PLAN.md` (its two questions for Guy, section 7, block nothing before phase F).
- Rules that bite every turn: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Everything else: `docs/map/README.md`.
