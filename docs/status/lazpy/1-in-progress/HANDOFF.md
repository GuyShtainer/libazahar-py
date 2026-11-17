<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 12:20 (session 3ds-toolkit-eb, a7 renamed after the crash restart; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). Plan revision 2 is final
  (`docs/plans/phase-7.md`, two review loops done); briefs in `docs/plans/phase-7-briefs.md`. Steps are items
  701-714 (W1a+W1 share 702, W7+W7c share 711, Guy's publish word goes in 712).
- Items 703-707: W1b (ip-legal licence delta) and the four sonnet fix agents W2a, W2b1, W2b2, W6, from 12:4x; W1 review done (fix then merge, 1 blocker).
- Item 600 / 420: v1.0.0 published at 11:08. I5 part 2 (fresh clone + full pytest) is folded into phase 7: the
  W10 post-publish check closes it. All 3DS work runs on the PC (flag ~/.lazpy/PC_ONLY, toolkit 2568682).

## Next steps, in order
1. Items 703-707 (worktrees runs/p7/wt/*): read each agent hand-back, commit its notes; actionlint is not on the PC (install blocked; ask Guy).
2. Then 708 (W3, opus fix check), then 709-714 in the plan's order (section 3). Guy allowed pushing reviewed, gated phase-7 work
   ("this time you can push"): main and the tag only. Publishing v1.1.0 still needs his word, asked at the end of W8.
3. After W10 passes: close items 420, 400 and 600; delete the private history bundles (incl. ~/.lazpy-private/g8e),
   their clones and .git/filter-repo.
4. When ios garmin says its run is done: delete ~/.lazpy/MAC_BUSY and tell Gen3D, 3DP and gba-toolkit-b2. Keep
   ~/.lazpy/PC_ONLY until Guy lifts the Garmin-only rule.
5. Pre-push checks need `LAZ_PRIVATE_NEEDLES=~/.lazpy-private/needles.txt` (keep that file; it is not in the repo).
6. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…).
7. Answer asks from Gen3D and 3DPlatinum; coordinate the PC (rule: free RAM >= 2 GB + 0.6 GB per copy; no caps).

## Waiting on Guy (only what blocks a step above)
- Nothing blocks now. The v1.1.0 publish word is asked at the end of W8 (item 712).
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/700-phase-7-windows-proven.md` and its steps 701-714;
  `600-phase-6-v1-release.md`, `420-step-i-release.md`, `400-phase-4-release.md`, `500-phase-5-user-asks.md`.
- Reviews: `docs/reviews/phase-7-review-1.md`, `docs/reviews/phase-7-review-2.md`. Evidence: runs/p7/<step>/.
- PC worker: toolkit docs/pc-worker/HANDOFF.md and `guy-decisions.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
