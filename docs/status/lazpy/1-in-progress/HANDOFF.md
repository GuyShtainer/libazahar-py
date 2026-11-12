<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 16:47 (this project's own session, which took over from the Gen3D session)

New project, nothing built yet. The repo, status folders, maps and research are in place (setup commit 2288e94);
the pre-commit hook runs status_check on main (Guy's yes, 2026-11-12). Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-12: revision 2 (the last) of the plan from `docs/reviews/plan-review-2.md`, by the plan's author (opus), edits `docs/PLAN.md` only | this repo | aa56e6986026ffbe0 | revised plan, then commit and split into phase items |

## Next steps, in order
1. When revision 2 reports: check review 2's blockers are resolved (svcBreak checked against source), commit,
   move laz-12 to done.
2. Then one item per phase (A to I) in `4-not-started/` from `docs/PLAN.md` section 3, then a plan per phase,
   A and B first (they run side by side), F right after A.
3. Book every agent run and main block in `docs/hours.tsv`.

## Waiting on Guy (only what blocks a step above)
- Nothing blocks the steps above. Guy said yes to publishing the progress page (2026-11-12); making a new page
  needs the Artifact tool, which is off, so it waits for him to allow it for one session:
  `docs/status/lazpy/3-waiting-on-guy/ask-01-progress-page.md`.
The full list is generated into `docs/status/README.md`.

## Pointers
- The plan: `docs/PLAN.md` (its two questions for Guy, section 7, block nothing before phase F).
- Rules that bite every turn: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Everything else: `docs/map/README.md`.
