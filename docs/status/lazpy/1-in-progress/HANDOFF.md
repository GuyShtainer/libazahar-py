<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 16:56 (this project's own session, which took over from the Gen3D session)

New project, nothing built yet. The repo, status folders, maps and research are in place (setup commit 2288e94);
the pre-commit hook runs status_check on main (Guy's yes, 2026-11-12). Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-13: short check of plan revision 2 against Azahar's source (opus), writes `docs/reviews/` (plan-check-3.md) only | this repo | a970bc3a4c214b531 | six verdicts, 20 min cap (about 17:15) |

## Next steps, in order
1. When the short check reports (Guy chose it): commit it, make any edits it asks for in `docs/PLAN.md`, move laz-13.
2. Split `docs/PLAN.md` section 3 into one item per phase (F1, A, B, C, D, E, F2, G, H, I) in `4-not-started/`,
   then a plan per phase; F1, A and B start together (F1's first core build runs detached, nice'd).
3. Book every agent run and main block in `docs/hours.tsv`.

## Waiting on Guy (only what blocks a step above)
- Nothing blocks the steps above. Guy said yes to publishing the progress page (2026-11-12); making a new page
  needs the Artifact tool, which is off, so it waits for him to allow it for one session:
  `docs/status/lazpy/3-waiting-on-guy/ask-01-progress-page.md`.
The full list is generated into `docs/status/README.md`.

## Pointers
- The plan: `docs/PLAN.md` (its two questions for Guy, section 7, block nothing before phase F).
- Rules that bite every turn: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Everything else: `docs/map/README.md`.
