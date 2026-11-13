<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 11:23 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| 1.0 API freeze review (laz-610), read-only opus | ../libazahar-py-k, branch core-rev2 | a5a4eeb6772bd50c9 | it reports; save it as docs/reviews/api-freeze-1.0.md, then code its changes on the branch once 3DPlatinum says "left the worktree" |

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`): it replaces the never-published v0.1.0 and step K is
its step V0, so step K merges before the release, not after a v0.1.0 tag.

## Next steps, in order
0. v1.0.0: `docs/plans/phase-v1.md` revision 2 (both reviews answered) is the plan; follow section 4's order. Now:
   V5 (CI) is done (item laz-650); next V1's changes on the branch; then V0b (merge and
   main build, after 11:55 when Gen3D's timed soak ends; Gen3D needs no hold, 3DPlatinum's OK is asked first).
1. Step K (laz-510) closes inside V0b: its gates 1, 3, 4 and 6 passed in the worktree; gate 2 there was dropped
   (item notes). Never run tools/fetch.sh in the worktree (its dl/ parts link to MAIN).
2. Release v1.0.0 (not v0.1.0): V8 and V9 of `docs/plans/phase-v1.md` (staging, the legal re-audit, 16 of 16 on the
   final HEAD), then Guy's word for the tag and push (below).
3. After Guy publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0, items 420, 400, 510 and 600 closed,
   then delete the three private history bundles.
4. V6: Gen3D and 3DPlatinum run their real suites on main's final core (sha256 sent to them); both answers are needed
   before staging.
5. Answer asks from Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4; the session named "3DP" is a progress
   test helper): both were told on 2026-11-13 to use only libazahar-py. 3DPlatinum switched (smoke: 600 frames in
   0.3 s); its sound lane will ask for an audio route (audio output is not built), with a repro, when that lane nears.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
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
