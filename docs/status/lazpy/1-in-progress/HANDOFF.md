<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 04:51 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-420: I4 after the audit: re-stage after G8c (mkrelease, pins, pre-push, clone), then a re-audit of B1 and S1-S3 | MAIN | main | the re-audit's verdict |

Not running: I3's audit is done (docs/reviews/release-legal-audit-v0.1.0.md; B1 fixed by G8c, item 420's Evidence); I2 is done (staged at 50ac6c1, pre-push 16/16, clone ok; item 420's Evidence); steps H and I are merged (H's item 410 done; I's fixes 3c11544, item 420's Evidence); the joint review is done (docs/reviews/phase-4-as-built.md; item 400's notes). Phase 3 done; G8b, Gen3D's copy check, the downloads done.

## Next steps, in order
1. mkrelease v0.1.0 (SOURCE.md now names the g8c map, so the zip's sha changes); write the zip's and the test
   app's sha256 into tools/fetch.sh's pins, commit it alone; mkrelease again; release_check --pre-push with
   LAZ_PRIVATE_NEEDLES (the private replace file plus the needles); clone_check in the background (phase-i.md 6).
2. Re-audit (release-legal-audit) of only B1 (history), S1-S3 and the zip's SOURCE.md; save it beside the first report.
3. Any commit after the last staging: mkrelease again before the push (check 10 compares with HEAD).
4. The push and the release wait for Guy (G5-G7, Q1-Q9).

## Waiting on Guy (only what blocks a step above)
- The audit's R1: accept core/PIN's default build route (it downloads Azahar's unchanged tarball and deletes the
  key and certificate headers before compiling) for v0.1.0, with PIN-nokeys the default at the next LAZPY_REV
  (docs/reviews/release-legal-audit-v0.1.0.md, remediation 6).
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
