<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 16:17 (this project's own session, which took over from the Gen3D session)

New project, nothing built yet. The repo, status folders, maps and research are in place (setup commit 2288e94);
the pre-commit hook runs status_check on main (Guy's yes, 2026-11-12). Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-05: second test, memory reads and real 3D-scene speed (run by the Gen3D session) | Gen3D session's scratchpad | a8bc5d5c | done or 60 min (about 16:46) |
| laz-11: plan review 1 (opus, adversarial), writes `docs/reviews/` (plan-review-1.md) only | this repo | a178c51a6cde6b1c3 | review written, then the revision |

## Next steps, in order
1. When review 1 reports: send it to the plan's author (aa56e6986026ffbe0) for the revision of `docs/PLAN.md`,
   with the hour-saving pass; commit review and revision, move laz-11 to done.
2. When laz-05's result lands (`docs/research/` (spike-2-real-scene.md), copied in uncommitted by the Gen3D session,
   which messages this session): read it, commit it, move laz-05, and fold it into the plan's pending branches.
3. Review round 2 (laz-12) after spike 2 is folded in, then one item per phase (A to I) in `4-not-started/`, then a
   plan per phase, A and B first (they run side by side).
4. Book every agent run and main block in `docs/hours.tsv`.

## Waiting on Guy (only what blocks a step above)
- Nothing blocks the steps above. Guy said yes to publishing the progress page (2026-11-12); making a new page
  needs the Artifact tool, which is off, so it waits for him to allow it for one session:
  `docs/status/lazpy/3-waiting-on-guy/ask-01-progress-page.md`.
The full list is generated into `docs/status/README.md`.

## Pointers
- The plan: `docs/PLAN.md` (its two questions for Guy, section 7, block nothing before phase F).
- Rules that bite every turn: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Everything else: `docs/map/README.md`.
