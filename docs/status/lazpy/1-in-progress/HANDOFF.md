<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 14:36 (session 3ds-toolkit-eb, a7 renamed after the crash restart; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). Plan revision 2 is final
  (`docs/plans/phase-7.md`, two review loops done); briefs in `docs/plans/phase-7-briefs.md`. Steps are items
  701-714 (W1a+W1 share 702, W7+W7c share 711, Guy's publish word goes in 712).
- Item 710: W5. Item 709 (W4) is done: main 49c81ed pushed, CI green (macos-live pytest step 2 CI-only failures,
  so STATUS takes plan section 7.6's fallback macOS sentence at W7). core-win64.yml run 44084612822 dispatched 14:35;
  watch log runs/p7/w5/watch.txt. Item 707 (W6) done; p7-docs tip 9069e95 (docs_check posix fix).
- Item 600 / 420: v1.0.0 published at 11:08. I5 part 2 (fresh clone + full pytest) is folded into phase 7: the
  W10 post-publish check closes it. All 3DS work runs on the PC (flag ~/.lazpy/PC_ONLY, toolkit 2568682).

## Next steps, in order
1. Item 710 (W5, plan line 295): when the run is green (build, load test, leak check), gh run download on the
   Mac, copy to D:\lazpy\p7\w5\, then on the PC: sha vs gate_f2.txt and the job log, PE machine and imports,
   needle scan of DLL strings + build.inputs + NOTICES, licence markers, one smoke boot. Gate file runs/p7/w5/checks.txt.
   Then fill OPENSSLDIR and the OpenSSL .a shas on p7-docs. On a leak failure delete the run's logs.
2. Then 711-714 in the plan's order (section 3). Guy allowed pushing reviewed, gated phase-7 work
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
