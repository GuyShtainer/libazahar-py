<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 10:12 (session 3ds-toolkit-a7, which also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Item 600, V9: Guy said "Push" (2026-11-17, by 08:29). The delta legal audit blocked on the saved v1.0.0 audit in
history; G8e (10:11) removed it (`docs/commit-map-g8e.tsv`; bundle ~/.lazpy-private/g8e/pre-g8e.bundle). Now:
re-stage, pre-push check, push.

## Next steps, in order
1. `LAZ_REL_APP=runs/release/testapp-gcc15-ba106998.3dsx sh tools/mkrelease.sh v1.0.0`. The zip must stay ced9a362…
   and the test app ba106998… (the Mac's devkitARM is gcc 16.1 since 2026-11-17; never rebuild the test app before
   the tag). If the zip changes, update tools/fetch.sh's LAZPY_CORE_SHA, commit, stage again.
2. `python3 -I tools/release_check.py runs/release/v1.0.0 --pre-push`: all PASS except the needle SKIP (the private
   needles file is lost; the delta was read by hand and audited). No commit between this and the tag.
3. `docs/plans/phase-i.md` 8.2 with v1.0.0 and `docs/plans/phase-v1.md` V9: create GuyShtainer/libazahar-py (public),
   push main and the tag only, `gh release create v1.0.0 --draft --verify-tag`. Publishing the draft is Guy's
   (after the first CI run on push is green).
4. After he publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0; close items 420, 400 and 600; delete
   the private history bundles (incl. ~/.lazpy-private/g8e), their clones and .git/filter-repo; port-win (PC,
   D:\lazpy\src\lazpy-win, cut on 0537394 = f93c755 now) rebases through the g8e map.
5. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…, build.inputs head 4e830e5).
6. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- Publishing the draft release (G7): his word or his click.
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
- The audit: kept private in `runs/reviews/release-legal-audit-v1.0.0.md` (gitignored, G8e); maps: `docs/commit-map-g8e.tsv`, then g8d.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
