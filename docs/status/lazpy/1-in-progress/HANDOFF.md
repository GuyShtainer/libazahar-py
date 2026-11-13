<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 19:27 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | Item | Ends |
|---|---|---|---|---|
| V8's last stage and pre-push check, after this commit | MAIN | main | laz-600 | rc 0 and 16 PASS in runs/g8d/prepush-final.log |

V6, V3 and V7 are done; V8's clone_check passed and the audit says SHIPPABLE WITH CHANGES (item 600's notes,
`docs/reviews/release-legal-audit-v1.0.0.md`). Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`).

## Next steps, in order
1. V8 is done once runs/g8d/prepush-final.log shows rc 0 and 16 PASS (G8d, the re-stage, the fetch.sh pin
   ced9a362… and the positive control are in item 600's notes). Make no commit until the tag: the build-files asset
   embeds HEAD. A commit made anyway means `sh tools/mkrelease.sh v1.0.0` and the pre-push check run again.
2. Tell Guy v1.0.0 is ready for his word (the push and release steps: `docs/plans/phase-i.md` 8.2, with v1.0.0).
3. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…, build.inputs head 4e830e5).
4. V9: Guy's word for the tag and push. After he publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0,
   items 420, 400 and 600 closed, the private history bundles and .git/filter-repo deleted, and tell the PC worker
   "v1.0.0 is tagged" so it rebases its Linux port (item 500's PC worker notes).
5. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md` (V0b-V6 notes, V3's result),
  `docs/status/lazpy/5-done/660-step-m-state-restore-shader-cache.md` (the restore fix, both V6 answers),
  `docs/status/lazpy/5-done/510-step-k-core-rev-2.md` (the core gates), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim, the Linux port), `docs/status/lazpy/1-in-progress/420-step-i-release.md`, `docs/status/lazpy/1-in-progress/400-phase-4-release.md`.
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v1.0.0.md` (now), `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
