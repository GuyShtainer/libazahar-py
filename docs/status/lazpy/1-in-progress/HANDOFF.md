<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 01:17 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-320: step F2 builder, second run (nice-20 worker fix, batch rerun; the only emulator user) | ../libazahar-py-f2 (step-f2) | a83e1355c6bcddc1f | reports "F2 done"; progress in its runs/f2/progress.md |
| laz-400: ip-legal consult, phase-i.md 9.1 | this repo | aee2a9ba07ce653cf | docs/reviews/release-ip-legal.md written |

Not running: step-e at a74aaec (E1 committed, parked until step-f2 merges).

## Next steps, in order
1. At "F2 done": opus as-built review of step-f2 (phase-f2.md section 12; include the _worker.py nice fix);
   fixes, reruns under rule T; commit; merge step-f2; item 320 to 5-done (phase-3.md section 4 step 3).
2. Then section 4 step 4: merge main into ../libazahar-py-e, resume E (a444b28ace71428a3, or a fresh sonnet with
   item 310's notes) for E2: tell Gen3D "hold now" first, "free" after; item 330 to 1-in-progress (PLAN.md :317);
   worktree step-g, merge a74aaec into it, launch G (phase-g.md).
3. When the consult reports: commit it and review 2, then Phase 4 revision 2 (opus) on review 2 plus the consult.
4. `test_state_boot` (5.50 s under load 45 on the stock core) reruns alone after F2, before E2; rule T.
5. Message Gen3D when Phase 3's timed runs end.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter for v0.1.0 (default: "macOS 15 or later"): item 400's notes.
  G1, G3 and G8 are answered and done; the rest block Phase 4's release, not its reviews.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/5-done/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 5, 2026-11-13 00:41); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
