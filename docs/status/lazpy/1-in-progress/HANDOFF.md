<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 02:05 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-310: opus as-built review of step E (phase-e.md section 12; fixes to __init__.py, host/run.c, host/azh_pure.h are held until step-g merges) | ../libazahar-py-e, read-only | a0d33437db53e74c5 | docs/reviews/step-e-as-built.md written |
| laz-330: step G2, the emulator batch (runs/g/batch.sh: gate_c on our core, the full pytest with test_memory_live.py); Gen3D still held | ../libazahar-py-g (step-g at 9ca360d, uncommitted) | a974a8613e6508e64 | reports "G done"; runs/g-batch.rc |

Not running: step F2 merged (fac16e9, item 320 done). Worktrees c, d and f2 are merged and kept (ignored outputs).

## Next steps, in order
1. At "G done": tell Gen3D "free". At the E review: fixes and merge as
   phase-3.md section 4 step 5 says (fixes to __init__.py, host/run.c, host/azh_pure.h are held until step-g
   merges); then item 320's slot notes (t_state counts slot waits; gate_f2 under hold_slot).
2. At "G done": phase-3.md section 4 step 6 (merge main into step-g, opus as-built review, merge).
3. Phase 4's plan is final (revision 2); items 410/420 stay in 4-not-started until Phase 3 ends.
4. After the phase merges: section 4 step 7 (the full suite once, one background batch); then Phase 4.
5. Before the push: G8b (second history rewrite, item 400's last notes), then release-legal-audit.

## Waiting on Guy (only what blocks a step above)
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter for v0.1.0 (default: "macOS 15 or later"): item 400's notes.
- Phase 4's questions Q1-Q9 (docs/plans/phase-4.md section 7), first Q1: remove the scripted stock-core download
  (recommended) or accept its YELLOW grade (docs/reviews/release-ip-legal.md section 7). G1, G3 and G8 are answered and done.
The full list is generated into `docs/status/README.md`.

## Pointers
- Phase 1: `docs/status/lazpy/5-done/100-phase-1-foundation.md` (its notes hold Phase 2's asks and review 2's
  verdict); review `docs/reviews/phase-1-review-2.md`.
- Phase 2: `docs/status/lazpy/5-done/200-phase-2-control.md`; plans `docs/plans/phase-2.md`, `phase-c.md`,
  `phase-d.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 5, 2026-11-13 00:41); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
