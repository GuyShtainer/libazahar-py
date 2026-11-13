<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 10:53 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| Core lazpy.2 full build (laz-510), detached, pid 46921, started 10:53 | ../libazahar-py-k at d64aabb, branch core-rev2 | main | build-core/build.exit appears there (30-60 min) |

Step K (core lazpy.2 for 3DPlatinum's asks) is in planning: `docs/plans/phase-k.md` revision 2 (reviews 1 and 2 answered). The v0.1.0 release
stays staged from main with core lazpy.1; step K works on branch core-rev2 and merges after v0.1.0 is tagged.

## Next steps, in order
1. Step K, when the build exits 0: gates 1-6 of `docs/plans/phase-k.md` in the worktree (gate 2 with `env -u LAZ_ROOT
   -u LAZ_HOST -u LAZ_PROFILE -u LAZ_LAZPY_PROFILE`, `LAZ_CORE_OLD` = MAIN's build-core dylib; the live tests are
   tests/python/test_threads_live.py on the branch), then NOTICES.md regenerated and STATUS.md on the branch, then tell
   3DPlatinum (3ds-toolkit-f4) the worktree's core, host and Python paths with `LAZ_ROOT=<wt>`. Item laz-510's notes
   hold the full pytest on lazpy.1 (150 passed). Never run tools/fetch.sh in the worktree (its dl/ parts link to MAIN).
2. Release: wait for Guy (below): R1, then G5-G7. (Re-staged at cd30086, 16 of 16, clone ok: item 420's
   Evidence; the later step K plan commits make the build-files asset stale again: re-stage at the tagged commit.)
3. On his word (phase-i.md 8.2): at the commit to be tagged, re-run `sh tools/mkrelease.sh v0.1.0` and
   `python3 -I tools/release_check.py runs/release/v0.1.0 --pre-push` with LAZ_PRIVATE_NEEDLES (the private replace
   file plus the needles); it must be 16 of 16 (the re-audit's S4: check 10 compares with HEAD). Tag v0.1.0 there,
   push main and the tag only, upload the staged assets as a draft release for Guy to publish.
4. After Guy publishes: I5 (phase-i.md 6: download the release, `shasum -c`, clone_check against GitHub,
   memory_watch), items 420 and 400 to 5-done, then delete the three private history bundles.
5. Answer asks from Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4; the session named "3DP" is a progress
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
- Items: `docs/status/lazpy/1-in-progress/510-step-k-core-rev-2.md` (step K), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim), `docs/status/lazpy/5-done/430-step-j-user-fixes.md` (step J, done),
  `docs/status/lazpy/1-in-progress/420-step-i-release.md` (I2-I4 and G8c evidence),
  `docs/status/lazpy/1-in-progress/400-phase-4-release.md` (Guy's asks).
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Old SHAs: `docs/commit-map-g8c.tsv`, then g8b, then g8 (`docs/map/README.md`).
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 6, 2026-11-13 08:10); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
