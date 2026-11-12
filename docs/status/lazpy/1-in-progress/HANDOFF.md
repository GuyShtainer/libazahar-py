<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 01:41 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-320: waiter that reruns r2, test_state_boot and gate_c --only f (our core) once the load is low (1-min under 10, 5-min under 14; 4 h at most) | ../libazahar-py-f2 runs/f2/quiet-rerun.sh | main (background bi08wz1d9) | runs/f2/rerun-*.rc written |
| laz-400: Phase 4 plan revision 2 (opus, final) on review 2 plus the ip-legal consult | phase-4.md, phase-h.md, phase-i.md | aa4336428ee833bdf | its report; the main loop commits |

Not running: step-e at a74aaec (E1 committed, parked until step-f2 merges); step-f2 at 6578c3c (built, reviewed,
fixes in; all green except r2's state-load timing under load 28-46; item 320's last notes).

## Next steps, in order
1. When runs/f2/rerun-*.rc are written: green, merge step-f2 into main and move item 320 to 5-done with Evidence
   (phase-3.md section 4 step 3); a timing miss at low load gets judged in item 320 first.
2. Then section 4 step 4: merge main into ../libazahar-py-e, resume E (a444b28ace71428a3, or a fresh sonnet with
   item 310's notes) for E2: tell Gen3D "hold now" first, "free" after; item 330 to 1-in-progress (PLAN.md :317);
   worktree step-g, merge a74aaec into it, launch G (phase-g.md). After E merges, apply item 320's slot notes.
3. At revision 2's report: commit the three plan files; items 410/420 stay in 0 until Phase 3 ends.
4. Before the push: G8b (second history rewrite, item 400's last notes), then release-legal-audit.
5. Message Gen3D when Phase 3's timed runs end.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter for v0.1.0 (default: "macOS 15 or later"): item 400's notes.
- Q7 from the ip-legal consult: remove the scripted stock-core download (recommended) or accept its YELLOW grade;
  docs/reviews/release-ip-legal.md section 7. G1, G3 and G8 are answered and done.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/5-done/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 5, 2026-11-13 00:41); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
