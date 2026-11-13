<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 12:15 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| V1 review fixes, host side (laz-610), sonnet | ../libazahar-py-k; progress in runs/v1/fix-host-progress.md there | a444f6a4e5d19a299 | it reports; brief `docs/plans/v1-fix-briefs.md` HF |
| V1 review fixes, Python side (laz-610), sonnet | ../libazahar-py-k; progress in runs/v1/fix-py-progress.md there | aa0abb629238080e0 | it reports; brief `docs/plans/v1-fix-briefs.md` PF |

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`): it replaces the never-published v0.1.0 and step K is
its step V0, so step K merges before the release, not after a v0.1.0 tag.

## Next steps, in order
0. v1.0.0: `docs/plans/phase-v1.md` revision 2 is the plan; follow section 4's order. Now: V1's review fixes run
   (`docs/reviews/api-freeze-1.0-diff-review.md`). When both report: edit USING.md from their progress notes (the exit
   table's seed and `--save` rows, `options=`, CRLF, `0X`, the `\r` drop in `msg=`, 4097 lines, `LAZ_CORE_OLD` in
   the test-only list, `HostCrashed.signal_name`), rerun make check, test-host, the fast pytest and test_profile_format
   (with `LAZ_STOCK_CORE`), commit on the branch. Step L (item 520): patch 0010 and the repro are on the branch
   (39aff14) and pass on the worktree core (0 bad of 180); 3DPlatinum was offered a preview run on it.
1. Then V0b (merge and main build; plan section 3): ask both projects for the hold first (3DPlatinum's OK; Gen3D needs
   none). Step K (laz-510) closes inside it. Never run tools/fetch.sh in the worktree (its dl/ parts link to MAIN).
2. V3, V4, V6 (Gen3D and 3DPlatinum run their real suites on main's final core sha256; both answers needed), V7, V8.
3. Release v1.0.0: V8 and V9 (staging, the legal re-audit, 16 of 16 on the final HEAD), then Guy's word for the tag
   and push (below).
4. After Guy publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0, items 420, 400, 510, 520 and 600
   closed, then delete the three private history bundles.
5. Answer asks from Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4): both use only libazahar-py. 3DPlatinum's
   sound lane will ask for an audio route (not built; D3: no audio in 1.0).

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default (the stock-core download is removed, and
  history no longer holds it).
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/610-step-v1-api-freeze.md` (V1), `docs/status/lazpy/1-in-progress/520-step-l-stencil-readback.md`
  (step L, report `docs/research/stencil-readback.md`), `docs/status/lazpy/1-in-progress/510-step-k-core-rev-2.md` (step K), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim), `docs/status/lazpy/5-done/430-step-j-user-fixes.md` (step J, done),
  `docs/status/lazpy/1-in-progress/420-step-i-release.md` (I2-I4 and G8c evidence),
  `docs/status/lazpy/1-in-progress/400-phase-4-release.md` (Guy's asks).
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Old SHAs: `docs/commit-map-g8c.tsv`, then g8b, then g8 (`docs/map/README.md`).
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 6, 2026-11-13 08:10); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
