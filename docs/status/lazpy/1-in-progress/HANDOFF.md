<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-12 18:49 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-100: Phase 1 as-built review (opus), A and B now, F1 when its report is sent; writes `docs/reviews/` (phase-1-as-built.md) only | MAIN, reads the three worktrees | a9d6a1a04a7ae2c40 | ends with fix lists per step; resumed for F1 and re-checks |
| laz-110: step F1, our core's pin, patches, options profile, build script; configure and planted reds only, no build (sonnet) | ../libazahar-py-f1 (step-f1) | a85f3abcf6d608824 | reported 19:03, configure + 3 reds ok, uncommitted; in the as-built review |
| laz-120: step A, host library and azhost CLI, gate-a (sonnet) | ../libazahar-py-a (step-a) | a4e8c6931d1122bf4 | reported 18:59, gate-a 8/8 PASS, uncommitted; in the as-built review |
| laz-130: step B, test app and checker, gate-b (sonnet) | ../libazahar-py-b (step-b) | ab76e8c1f445db1b3 | reported 18:57, gate-b 14/14 PASS (fe2), uncommitted; in the as-built review |
| laz-200: Phase 2 plan revision 2 from `docs/reviews/phase-2-review-2.md` (the plan's author, opus), edits `docs/plans/` (phase-2, c, d) only | this repo | a4bcf09ec00640830 | revised plan; then a main-loop check of each fix, then C and D after Phase 1 merges |

## Next steps, in order
1. Phase 2 revision 2 running (above): commit it, check each review-2 fix is in the text (no third loop).
2. Phase 1 builders running (above). When A and B have reported (F1 reports first and waits): one opus as-built
   review over all three worktrees, then branch commits, the integration run on `int-1`, the merge to main, then the
   core build in MAIN and its waiter. Every step is in `docs/plans/phase-1.md` "Merge and launch".
3. Phase 2's steps (C, D) build after Phase 1 merges. Phases 3 and 4: plan with two review loops each, later.

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
