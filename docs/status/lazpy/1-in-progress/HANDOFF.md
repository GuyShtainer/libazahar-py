<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 01:09 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-310: step E1 builder (sonnet; no emulator this run) | ../libazahar-py-e (step-e) | a444b28ace71428a3 | reports "E1 done"; progress in its runs/e/progress.md |
| laz-320: step F2 builder (sonnet; F2-0 to F2-2, the only emulator user now) | ../libazahar-py-f2 (step-f2) | a76e4f3e6572c2142 | reports "F2 done"; progress in its runs/f2/progress.md |
| laz-400: Phase 4 plan review 2 (opus; also Gen3D's friction list) | this repo | a520c6028898077dc | docs/reviews/phase-4-review-2.md written; then revision 2 |
| laz-400: ip-legal consult, phase-i.md 9.1 | this repo | aee2a9ba07ce653cf | docs/reviews/release-ip-legal.md written |

## Next steps, in order
1. At "E1 done": commit exactly E1's paths on step-e, note the sha; do not resume E yet (phase-3.md section 4 step 2).
2. At "F2 done": opus as-built review of step-f2 (phase-f2.md section 12); fixes, reruns under rule T; commit;
   merge step-f2; item 320 to 5-done with its notes (section 4 step 3).
3. Then section 4 step 4: merge main into ../libazahar-py-e, resume E for E2 (tell Gen3D "hold now" first, "free"
   after); item 330 to 1-in-progress (PLAN.md :317); worktree step-g with E1's sha merged; launch G (phase-g.md).
4. When review 2 and the consult report: commit both, then Phase 4 revision 2 (opus; at most 2 opus at once).
5. `test_state_boot` (5.50 s under load 45 on the stock core) reruns alone after F2-2, before E2; rule T.
6. Message Gen3D when Phase 3's timed runs end. Phase 4's ask to set MACOSX_DEPLOYMENT_TARGET=15.0 waits for
   review 2 (the gated build stays as it is).

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
