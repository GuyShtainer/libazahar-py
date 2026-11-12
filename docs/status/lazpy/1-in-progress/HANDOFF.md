<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 16:02 (the Gen3D session, at setup)

New project, nothing built yet. The repo, status folders, maps and research are in place; the first commit is the
setup. Nothing pushed. The downloaded core and MoltenVK are already in `dl/` (ignored), the headers in `vendor/`.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-05: second test, memory reads and real 3D-scene speed (run by the Gen3D session) | Gen3D session's scratchpad | a8bc5d5c | done or 60 min (about 16:46) |

## Next steps, in order
1. Read `docs/research/` (spike 1, prior art, Gen3D's harness needs) and `prototype/README.md`.
2. When laz-05's result lands in `docs/research/` (spike-2-real-scene.md; the Gen3D session copies it in and moves
   laz-05), read it. The plan may start before that; leave the speed and memory parts open until it lands.
3. Plan the whole scope (laz-10, opus): write `docs/` (PLAN.md). Guy's order: whole scope, two review rounds with
   revisions (laz-11, laz-12), then one item per phase in `docs/status/lazpy/4-not-started/`, then a plan per phase.
   Each revision runs the hour-saving pass (laz-10's notes).
4. Book every agent run and main block in `docs/hours.tsv` (phase `plan` for laz-10 to laz-12).

## Waiting on Guy (only what blocks a step above)
- Nothing blocks the steps above. The first publish of the progress page waits for his yes:
  `docs/status/lazpy/3-waiting-on-guy/ask-01-progress-page.md`.
The full list is generated into `docs/status/README.md`.

## Pointers
- First plan item: `docs/status/lazpy/2-next/10-plan-whole-scope.md`.
- Rules that bite every turn: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Everything else: `docs/map/README.md`.
