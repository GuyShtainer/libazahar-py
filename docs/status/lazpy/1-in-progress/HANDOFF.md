<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 01:05 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-300: step 0 core rebuild as revision 2 writes it (detached, niced) | MAIN build-core/ | main (pid 40445) | build-core/build.exit appears (waiter bounded 150 min) |
| laz-400: Phase 4 plan review 2 (opus; also Gen3D's friction list) | this repo | a520c6028898077dc | docs/reviews/phase-4-review-2.md written; then revision 2 |
| laz-400: ip-legal consult, phase-i.md 9.1 | this repo | aee2a9ba07ce653cf | docs/reviews/release-ip-legal.md written |

## Next steps, in order
1. When build.exit is 0: put `cat build-core/build.inputs`, `otool -L` of the dylib and the count of
   "built for newer" lines into item 300; run F2's f1 checks by hand only if F2 is late (F2 owns them).
2. Then G8, the history rewrite, exactly as `docs/plans/phase-i.md` section 8.1 (preconditions: build ended, no
   agent editing tracked files in MAIN; the consult and review only create new files). Remove the merged
   ../libazahar-py-c and -d worktrees first (status --porcelain --ignored empty), or check 8.1 step 1's ancestor rule.
3. Then `docs/plans/phase-3.md` section 4 step 1: items 310 and 320 to 1-in-progress (PLAN.md pointers :296, :311),
   worktrees step-e and step-f2 from main, the E and F2 sonnet builders together (briefs `docs/plans/phase-e.md`,
   `phase-f2.md`); their ids here.
4. Rerun `test_state_boot` alone when load is under 12 (5.50 s under load 45 on the stock core); rule T.
5. When review 2 and the consult report: commit both, then Phase 4 revision 2 (opus).
6. Gen3D was told at 01:05 that timed runs start; message it when Phase 3's timed runs end.

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
