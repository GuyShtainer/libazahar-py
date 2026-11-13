<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 09:36 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|

Nothing runs. Step J is done (item 430 in 5-done): Gen3D's API fixes and the real scene on our core. Its commits
make the staged build-files asset (staged at 7e2cb7e) stale: re-stage before the push (step 1).

## Next steps, in order
1. Wait for Guy (below): R1, then G5-G7. (Re-staged at cd30086, 16 of 16, clone ok: item 420's Evidence.)
2. On his word (phase-i.md 8.2): at the commit to be tagged, re-run `sh tools/mkrelease.sh v0.1.0` and
   `python3 -I tools/release_check.py runs/release/v0.1.0 --pre-push` with LAZ_PRIVATE_NEEDLES (the private replace
   file plus the needles); it must be 16 of 16 (the re-audit's S4: check 10 compares with HEAD). Tag v0.1.0 there,
   push main and the tag only, upload the staged assets as a draft release for Guy to publish.
3. After Guy publishes: I5 (phase-i.md 6: download the release, `shasum -c`, clone_check against GitHub,
   memory_watch), items 420 and 400 to 5-done, then delete the three private history bundles.
4. Answer asks from Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4; the session named "3DP" is a progress
   test helper): both were told on 2026-11-13 to use only libazahar-py. 3DPlatinum switched (smoke: 600 frames in
   0.3 s); its sound lane will ask for an audio route (audio output is not built), with a repro, when that lane nears.

## Waiting on Guy (only what blocks a step above)
- The audit's R1: accept core/PIN's default build route (it downloads Azahar's unchanged tarball and deletes the
  key and certificate headers before compiling) for v0.1.0, with PIN-nokeys the default at the next LAZPY_REV
  (docs/reviews/release-legal-audit-v0.1.0.md, remediation 6).
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter for v0.1.0 (default: "macOS 15 or later"): item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default (the stock-core download is removed, and
  history no longer holds it).
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/5-done/430-step-j-user-fixes.md` (step J, done),
  `docs/status/lazpy/1-in-progress/420-step-i-release.md` (I2-I4 and G8c evidence),
  `docs/status/lazpy/1-in-progress/400-phase-4-release.md` (Guy's asks).
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Old SHAs: `docs/commit-map-g8c.tsv`, then g8b, then g8 (`docs/map/README.md`).
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 6, 2026-11-13 08:10); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
