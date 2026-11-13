<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 02:05 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-300: Phase 3's full suite once (phase-3.md section 4 step 7): build, gates A, B, C on both cores, F2, the full pytest on each core, the live pool test; each part waits for load under 10 | MAIN runs/p3/batch.sh, rc files runs/p3/*.rc | main (background) | runs/p3/summary.txt written |

Not running: steps F2 (fac16e9), E (cbe823c) and G (04926c4) are merged; items 320, 310 and 330 are done.
Worktrees c, d, e, f2 and g are merged and kept (ignored outputs).

## Next steps, in order
1. When runs/p3/summary.txt is all 0: item 300 to 5-done with Evidence (Phase 3 done); tell Gen3D Phase 3's timed
   runs ended; then remove worktrees c, d, e, f2, g (git status --porcelain --ignored checked first).
2. Phase 4's plan is final (revision 2); items 410/420 stay in 4-not-started until Phase 3 ends.
3. After the phase merges: section 4 step 7 (the full suite once, one background batch); then Phase 4.
4. Before the push: G8b (second history rewrite, item 400's last notes), then release-legal-audit.

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
