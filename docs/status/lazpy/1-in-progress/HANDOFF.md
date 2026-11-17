<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 10:19 (session 3ds-toolkit-a7, which also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
Item 600, V9: pushed at 10:17. Public repo GuyShtainer/libazahar-py, main and tag v1.0.0 (on 6f1a713), draft release
v1.0.0 with 9 assets (digests equal SHA256SUMS). The first CI run on push (44045482328) went green at 10:19.

## Next steps, in order
1. Guy publishes the draft (G7, his word or click); told at 10:19. The tag never moves without his word.
2. After he publishes: I5 (`docs/plans/phase-i.md` section 6) against v1.0.0; close items 420, 400 and 600; delete
   the private history bundles (incl. ~/.lazpy-private/g8e), their clones and .git/filter-repo; port-win (PC,
   D:\lazpy\src\lazpy-win, cut on 0537394 = f93c755 now) rebases through the g8e map. Tell the PC worker.
3. Pre-push checks need `LAZ_PRIVATE_NEEDLES=~/.lazpy-private/needles.txt` (rebuilt 2026-11-17; under --pre-push a
   needle SKIP is a FAIL). Keep that file; it is not in the repo.
4. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…, build.inputs head 4e830e5). The Mac's
   devkitARM is gcc 16.1 since 2026-11-17: a rebuilt test app no longer hashes to ba106998.
5. Answer asks from Gen3D and 3DPlatinum; both use only libazahar-py.

## Waiting on Guy (only what blocks a step above)
- Publishing the draft release v1.0.0 (G7), after CI is green: his word or his click.
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
