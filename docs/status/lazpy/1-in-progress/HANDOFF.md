<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 12:39 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing of this session. (Gen3D's and 3DPlatinum's V6 runs are peer work: step 0 below.)

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`). V0b is done (main 003eaec, core sha256 88cc6188…).
Worktree ../libazahar-py-k is removed; branch core-rev2 stays at e28e4c2 (merged). Its logs: runs/wt-k/.

## Next steps, in order
0. V6 runs in the two projects on main's core 88cc6188…: 3DPlatinum's A3 self-test passed (item 520); its
   chain with the suite and A4), Gen3D asked for its smoke and Pool 1-4 run. Record each answer verbatim in item 600
  . A fail blocks V8.
1. V4 is done (2168165) except README's numbers (V3) and NOTICES.md (V8, the full mknotices inputs).
2. V3 (real-scene multi-instance row, `docs/plans/phase-v1.md` V3): only on a quiet machine, after both projects'
   V6 runs end (rule T); Gen3D's .3dsx and seed as in `docs/research/real-scene-j.md`. Then README's numbers and the
   cap (a CHECK FAIL keeps 2).
3. V7 full test pass (quiet), then V8 staging and the legal re-audit (16 of 16 on the final HEAD). The test app's
   sha256 is now ba106998… (item 600 notes).
4. V9: Guy's word for the tag and push (below). After he publishes: I5 (`docs/plans/phase-i.md` section 6) against
   v1.0.0, items 420, 400 and 600 closed, then delete the three private history bundles.
5. Answer asks from Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4); both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default (the stock-core download is removed, and
  history no longer holds it).
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/5-done/610-step-v1-api-freeze.md` (V1), `docs/status/lazpy/5-done/520-step-l-stencil-readback.md`
  (step L, report `docs/research/stencil-readback.md`), `docs/status/lazpy/5-done/510-step-k-core-rev-2.md` (step K), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim), `docs/status/lazpy/5-done/430-step-j-user-fixes.md` (step J, done),
  `docs/status/lazpy/1-in-progress/420-step-i-release.md` (I2-I4 and G8c evidence),
  `docs/status/lazpy/1-in-progress/400-phase-4-release.md` (Guy's asks).
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Old SHAs: `docs/commit-map-g8c.tsv`, then g8b, then g8 (`docs/map/README.md`).
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH (version 6, 2026-11-13 08:10); republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
