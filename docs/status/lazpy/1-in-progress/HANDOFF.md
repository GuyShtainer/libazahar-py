<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 01:56 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-310: step E2, the timed speed table (Gen3D asked to hold its lanes at 01:57) | ../libazahar-py-e (step-e, main merged at 8c06e26) | a444b28ace71428a3 | reports "E done"; writes runs/e-speed.rc |
| laz-330: step G builder (G1 now; G2's emulator runs wait for E's runs/e-speed.rc) | ../libazahar-py-g (step-g at 9ca360d: main fac16e9 + E1) | a974a8613e6508e64 | reports "G done"; progress in runs/g/progress.md |
| laz-400: Phase 4 plan revision 2 (opus, final) on review 2 plus the ip-legal consult | phase-4.md, phase-h.md, phase-i.md in MAIN | aa4336428ee833bdf | its report; the main loop commits |

Not running: step F2 merged (fac16e9, item 320 done). Worktrees c, d and f2 are merged and kept (ignored outputs).

## Next steps, in order
1. At "E done": tell Gen3D "free"; opus as-built review of step-e (phase-e.md section 12); fixes and merge as
   phase-3.md section 4 step 5 says (fixes to __init__.py, host/run.c, host/azh_pure.h are held until step-g
   merges); then item 320's slot notes (t_state counts slot waits; gate_f2 under hold_slot).
2. At "G done": phase-3.md section 4 step 6 (merge main into step-g, opus as-built review, merge).
3. At revision 2's report: commit the three plan files; items 410/420 stay in 4-not-started until Phase 3 ends.
4. After the phase merges: section 4 step 7 (the full suite once, one background batch); then Phase 4.
5. Before the push: G8b (second history rewrite, item 400's last notes), then release-legal-audit.

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
