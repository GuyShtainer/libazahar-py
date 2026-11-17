<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 23:26 (session 3ds-toolkit-eb; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). Plan revision 2 is final
  (`docs/plans/phase-7.md`); briefs in `docs/plans/phase-7-briefs.md`. Steps are items 701-714.
- Item 711 done: W7 + W7c passed (3DP and Gen3D jobs ran on the RC deploy, fp fb0def44, PASS).
- Item 713: W9 runs now (main loop): re-stage, pre-push gate, push, CI, tag, release, publish.
  The PC crashed twice today: Guy "if it crashes so much dont overload it"; at most 2 copies.
- Item 712 done: audit shippable, fixes in 3543987, re-staged (SHA256SUMS 01d284b8...), Guy: "Yes, publish after the
  jobs". macOS workflows are manual-only (Guy: "Yes, manual only"), committed.
- Item 600 / 420: v1.0.0 published 11:08. W10's post-publish check closes I5 part 2.

## Next steps, in order
1. W9 (item 713): re-stage if HEAD moved (bundle main --tags, stage-pc.sh, rc-pc.ps1 with needles on
   stdin), needle scan, push main (Windows CI only now), dispatch test.yml + macos-live.yml once, pick STATUS's macOS
   line (713's notes), tag, release, publish (Guy's word in 712). Then W10 (item 714).
2. After W10 passes: close items 420, 400 and 600; delete the private history bundles (incl. ~/.lazpy-private/g8e),
   their clones and .git/filter-repo.
3. Pre-push checks need `LAZ_PRIVATE_NEEDLES=~/.lazpy-private/needles.txt` (keep that file; not in the repo).
4. Answer asks from Gen3D and 3DPlatinum; coordinate the PC (free RAM >= 2 GB + 0.6 GB per copy).

## Waiting on Guy (only what blocks a step above)
- Pushes: "No pushes for now" (~19:50) is replaced for v1.1.0 by "Yes, publish after the jobs" (item 712): pushes
  for W9 only, after W7c; push only expected-green; after a red run, ask Guy before the next push.
- The PC install of diffutils and actionlint: denied by the permission classifier; Guy asked, no answer.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/700-phase-7-windows-proven.md` and its steps 701-714;
  `600-phase-6-v1-release.md`, `420-step-i-release.md`, `400-phase-4-release.md`, `500-phase-5-user-asks.md`.
- Reviews: `docs/reviews/phase-7-review-1.md`, `docs/reviews/phase-7-review-2.md`. Evidence: runs/p7/<step>/.
- PC worker: toolkit docs/pc-worker/HANDOFF.md and `guy-decisions.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
