<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 00:45 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-300: Phase 3 plan revision 2 (opus, fresh; final, with OpenSSL 3 and patches 0007/0008) | this repo | ae13bb77d6994c473 | revision written; then the main loop's step 0 (P9b rebuild) and the builds |
| laz-400: Phase 4 plan revision 1 (opus, fresh) | this repo | a739c8de18f2e6992 | revision written; then review 2 |

## Next steps, in order
1. Phase 2 is done (items 200, 210, 220 in `5-done/`; main a113cf6). Tell Gen3D the tool is usable (USING.md).
2. When Phase 3's revision 2 reports: commit it, then the main loop's step 0 "P9b" exactly as the report says
   (patches 0007/0008, drop list, static OpenSSL 3, build.inputs; one detached, niced rebuild in MAIN), then E1
   and F2 builders in their worktrees made at main (`docs/plans/phase-3.md` order section).
3. When Phase 4's revision 1 reports: commit it, then opus review 2 and revision 2.
4. Before the first push: the history rewrite (Guy's G8, item 400's notes), then release-legal-audit.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft): item 400's notes. G1 (keys off, done), G3 and G8 answered;
  the rest block Phase 4's release, not its reviews.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/5-done/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 5, 2026-11-13 00:41); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
