<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 12:03 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| Review of the V1 API-freeze commit 64f5d18 (laz-610), read-only opus | ../libazahar-py-k, branch core-rev2; notes in this session's scratchpad v1review/ | a04d832ad11619ae6 | it reports; save it as docs/reviews/api-freeze-1.0-diff-review.md |
| Stencil repro in the test app (laz-520), sonnet | ../libazahar-py-k; progress in runs/stencil/repro-progress.md there | a3f2709cf168b11c4 | it reports red counts on the unpatched core; brief `docs/plans/stencil-briefs.md` R |
| Core patch 0010 for the stencil barriers (laz-520), sonnet | ../libazahar-py-k; progress in runs/stencil/patch-progress.md there | a7a04c6135194c45c | it reports the patch applies; brief `docs/plans/stencil-briefs.md` P |

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`): it replaces the never-published v0.1.0 and step K is
its step V0, so step K merges before the release, not after a v0.1.0 tag.

## Next steps, in order
0. v1.0.0: `docs/plans/phase-v1.md` revision 2 is the plan; follow section 4's order. Now: V1 is on the branch
   (64f5d18, item 610); fix the review's must-fix items on the branch. Step L (item 520): when the repro is red and
   the patch applies, commit both on the branch, rebuild the worktree core (`env -u LAZ_ROOT ... tools/build-core.sh`
   there, about 10 min), rerun the repro (10 launches green), the fast pytest and test-host. 3DPlatinum was asked
   for experiment 2 (`MVK_CONFIG_USE_MTLHEAP=0`) on its self-test; record its answer in item 520.
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
