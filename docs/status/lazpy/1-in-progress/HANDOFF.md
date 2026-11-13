<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 04:26 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-420: I3, the release legal audit (phase-i.md 9.2, plus the history's old stock-core URL and hash) | MAIN, read only; notes in runs/i3/ | aa81b7f45c2e7eb9b | its report (saved as runs/i3/release-legal-audit-v0.1.0.md) |

Not running: I2 is done (staged at 50ac6c1, pre-push 16/16, clone ok; item 420's Evidence); steps H and I are merged (H's item 410 done; I's fixes 3c11544, item 420's Evidence); the joint review is done (docs/reviews/phase-4-as-built.md; item 400's notes). Phase 3 done; G8b, Gen3D's copy check, the downloads done.

## Next steps, in order
1. On the audit's report: save it verbatim to docs/reviews/release-legal-audit-v0.1.0.md and commit it.
   BLOCKERs go to I4 (a sonnet builder with exact fixes), then re-stage: mkrelease v0.1.0, release_check
   --pre-push with LAZ_PRIVATE_NEEDLES (the private replace file plus the needles), clone_check (phase-i.md 6, I2
   steps 3-5), and a re-audit of only the changed items. SHOULD items go to Guy's list.
2. Any commit after the last staging: mkrelease again before the push (check 10 compares with HEAD).
3. The push and the release wait for Guy (G5-G7, Q1-Q9).

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
