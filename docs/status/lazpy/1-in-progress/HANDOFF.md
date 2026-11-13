<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-13 12:49 (this project's own session)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Nothing of this session. (3DPlatinum's V6 chain on core 88cc6188… is peer work: step 2 below.)

Guy asked for v1.0.0 (item laz-600, `docs/plans/phase-v1.md`). V0b is done (main 003eaec, core sha256 88cc6188…).
Gen3D's V6 smoke FAILED on it: a state restore crashes the first 3D draw (item laz-660 has the cause and the A/B).

## Next steps, in order
1. Step M (item laz-660): core patch 0011 in `PipelineCache::SwitchCache` (the early return only when a cache is
   selected). Build it in a fresh worktree off main (its own dl/ unpack and build-core/, the source tarball copied in;
   MAIN's build-core/ stays untouched while 3DPlatinum runs). Red then green on the scratchpad repro and on a new
   test-app check (a programmable-shader draw after a restore). Ask 3DPlatinum before the 6-minute build (load).
   Then merge, a V0b-style hold and main build, the gates, and the new sha256 to both projects.
2. V6 again on the new core: Gen3D's smoke and Pool 1-4, 3DPlatinum's chain with A4. Record each answer verbatim in
   item 600. A fail blocks V8.
3. V3 (real-scene multi-instance row, `docs/plans/phase-v1.md` V3): only on a quiet machine, after both projects'
   V6 runs end (rule T). Then README's numbers and the cap (a CHECK FAIL keeps 2).
4. V7 full test pass (quiet), then V8 staging, NOTICES.md from mknotices, fetch.sh's TBD pins, and the legal
   re-audit (16 of 16 on the final HEAD). The audit also checks history for game names (three were removed from
   docs on 2026-11-13; older commits may hold more).
5. V9: Guy's word for the tag and push (below). After he publishes: I5 (`docs/plans/phase-i.md` section 6) against
   v1.0.0, items 420, 400 and 600 closed, then delete the three private history bundles.
6. Answer asks from Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4); both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- The audit's R1 (core/PIN's default build route) is settled by v1.0.0 if Guy keeps the default: PIN-nokeys is the
  default route (`docs/plans/phase-v1.md` D2). Guy may overrule any of D1-D6 there.
- Phase 4's G5-G7 (repo creation, the word "push", publishing the draft), G9 (spike 2's game: default say
  nothing), and whether macOS 11-14 users matter (default D4: "macOS 15 or later"), now for v1.0.0: item 400's notes.
- Phase 4's Q1-Q9 (docs/plans/phase-4.md section 7); Q1 took its default.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/660-step-m-state-restore-shader-cache.md` (step M),
  `docs/status/lazpy/1-in-progress/600-phase-6-v1-release.md` (V0b-V4 notes, the test app's sha256),
  `docs/status/lazpy/5-done/520-step-l-stencil-readback.md` (the last core patch: its build and gate route),
  `docs/status/lazpy/5-done/510-step-k-core-rev-2.md` (the core gates), `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`
  (the asks verbatim), `docs/status/lazpy/1-in-progress/420-step-i-release.md`, `docs/status/lazpy/1-in-progress/400-phase-4-release.md`.
- The push and I5: `docs/plans/phase-i.md` sections 6 and 8.2.
- Audits: `docs/reviews/release-legal-audit-v0.1.0.md`, `docs/reviews/release-legal-audit-v0.1.0-reaudit.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
