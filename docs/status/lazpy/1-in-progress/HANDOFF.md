<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 03:19 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-410: step H fix round (review B1, B2, S1-S3, N1-N3, D2's STATUS line) | ../libazahar-py-h (step-h at 4ce7181) | af156d29564cfc9ce | its report "H fixes done" |
| laz-420: step I fix round (review S4, S5, S6 newlib, N4-N9), re-stage | ../libazahar-py-i (step-i at 46c808e) | a8e760acbd1172ce5 | its report "I fixes done" |

Not running: the joint review is done (docs/reviews/phase-4-as-built.md; item 400's notes). Phase 3 done; G8b, Gen3D's copy check, the downloads done.

## Next steps, in order
1. On "H fixes done" / "I fixes done": commit each on its branch (exact paths, scans); book hours.
2. Merge step-h, then step-i, into main (review S8: code.md and runners.md conflicts, keep both sides, H's runners
   block gets its own closing fence; then mkmap, map_check); remove both worktrees (porcelain --ignored looked at).
3. S7: reword spike 1's stock-core URL and sha256 lines (docs/research/spike-1-headless-core.md:18, :27-28) and the
   runners.md pointer; then I2 in MAIN (phase-i.md 6; S9's order), I3 release-legal-audit (phase-i.md 9.2), I4.
4. The push and the release wait for Guy (G5-G7, Q1-Q9).

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
