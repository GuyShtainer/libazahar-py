<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 19:52 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing. main is clean. v1.0.0 is staged in runs/release/v1.0.0 (zip ced9a362…, test app ba106998…) and passed
the pre-push check at f75ed0b (item 600's last notes). Guy held the push on 2026-11-13: "Lets hold the push",
"We will push in the future".

## Next steps, in order
1. Wait for Guy's word to push (V9). Do not tag or push before it.
2. On his word, in this order:
   - Commits after f75ed0b made the build-files asset stale. Run `sh tools/mkrelease.sh v1.0.0`; the zip must stay
     ced9a362… and the test app ba106998…. If the zip changes, update tools/fetch.sh's LAZPY_CORE_SHA, commit, and
     stage again.
   - The Mac's devkitARM moved to gcc 16.1 on 2026-11-17 02:26 (Gen3D's note), so a rebuilt build/testapp.3dsx no longer
     hashes to ba106998…. Never clean or rebuild it before the tag. If it has changed, run mkrelease with
     `LAZ_REL_APP=runs/release/testapp-gcc15-ba106998.3dsx` (the kept gcc 15 copy).
   - Run `LAZ_PRIVATE_NEEDLES=<private file> python3 -I tools/release_check.py runs/release/v1.0.0 --pre-push`:
     16 PASS. Make no commit between this check and the tag.
   - Then `docs/plans/phase-i.md` 8.2 with v1.0.0 (the tag line and `gh release create` in `docs/plans/phase-v1.md`
     V9). G5 (creating the repo), the push and publishing the draft each need Guy's word.
3. After he publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0; close items 420, 400 and 600; delete
   the four private history bundles, their clones and .git/filter-repo; tell the PC worker session (3ds-toolkit-11)
   "v1.0.0 is tagged" so it rebases port-linux through `docs/commit-map-g8d.tsv` (it agreed, item 500's notes).
4. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…, build.inputs head 4e830e5).
5. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The push itself (V9): his word, then G5-G7 (repo creation, the push, publishing the draft).
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- G9 (spike 2's game: default say nothing) and whether macOS 11-14 users matter (default D4: "macOS 15 or
  later"): item 400's notes. Phase 4's Q1-Q9: `docs/plans/phase-4.md` section 7; Q1 took its default.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md` (V0b-V8 notes, the hold),
  `docs/status/lazpy/5-done/660-step-m-state-restore-shader-cache.md` (the restore fix),
  `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md` (the asks verbatim, the Linux port),
  `docs/status/lazpy/1-in-progress/420-step-i-release.md`, `docs/status/lazpy/1-in-progress/400-phase-4-release.md`.
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2; `docs/plans/phase-v1.md` V9.
- The audit: `docs/reviews/release-legal-audit-v1.0.0.md`; the G8d map: `docs/commit-map-g8d.tsv`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
