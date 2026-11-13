<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 03:19 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-420: step I builder (phase-i.md): P17 code, NOTICES/mknotices, mkrelease, release_check, fetch.sh, OPENSSL.md | ../libazahar-py-i (step-i at 896c2fe) | a8e760acbd1172ce5 | its report "I1 done" |

Not running: step H's builder finished: H1 committed on step-h (4ce7181), report in item 410's notes. Phase 3 done (item 300); G8b, Gen3D's copy check and the downloads done (item 400's notes).

## Next steps, in order
1. On "H1 done" / "I1 done": commit each report's files on its branch (exact paths, with the map lines it names, and
   for I the rules.md rule 3 and runners.md lines); book its hours row; the builders never commit.
2. When both are committed: one opus as-built review over both diffs (phase-h.md 12, phase-i.md 12); fixes by the
   resumed builders (SendMessage to the ids above); then merge step-h, then step-i; items 410 (and 420 at I5).
3. I2 in MAIN (phase-i.md 6), I3 release-legal-audit (its brief: phase-i.md 9.2), I4 fixes.
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
