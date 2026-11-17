<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 11:29 (session 3ds-toolkit-eb, a7 renamed after the crash restart; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 600 / 420: v1.0.0 published at 11:08 (Guy: "ok publish the draft."). I5 part 1 done (assets 8/8 OK). I5 part 2,
  the fresh clone from GitHub plus the full pytest, must now run on the PC: Guy ~11:0x (via 9f) made the Mac Garmin-only,
  all 3DS builds, tests and gates on the PC (flag ~/.lazpy/PC_ONLY, toolkit 2568682). Folded into the phase-7 plan.
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). README and STATUS now say
  "work in progress, not proven". Rebased to port-win-v1 (1c8650f, local + PC; bundle
  runs/p7/port-win-v1.bundle). The opus plan agent writes docs/plans/phase-7.md (told: every gate on the PC).

## Next steps, in order
1. Item 700: when the plan agent reports, two opus review loops (one at a time), then execute. Guy allowed pushing
   reviewed, gated phase-7 work to GitHub ("this time you can push"); publishing a release still needs his word.
2. I5 part 2 on the PC (`docs/plans/phase-i.md` section 6, with v1.0.0): the clone_check of
   https://github.com/GuyShtainer/libazahar-py main plus `examples/memory_watch.py`, as phase-7 plans it. If it passes:
   close items 420, 400 and 600; delete the private history bundles (incl. ~/.lazpy-private/g8e), their clones and
   .git/filter-repo.
3. When ios garmin says its run is done: delete ~/.lazpy/MAC_BUSY and tell Gen3D, 3DP and gba-toolkit-b2. Keep
   ~/.lazpy/PC_ONLY until Guy lifts the Garmin-only rule.
4. Pre-push checks need `LAZ_PRIVATE_NEEDLES=~/.lazpy-private/needles.txt` (keep that file; it is not in the repo).
5. No core/ edit or build-core.sh run on main (the gated build is 64026f4a…). The Mac's devkitARM is gcc 16.1 since
   2026-11-17: a rebuilt test app no longer hashes to ba106998.
6. Answer asks from Gen3D and 3DPlatinum; coordinate the PC (rule: free RAM >= 2 GB + 0.6 GB per copy; no caps).

## Waiting on Guy (only what blocks a step above)
- Nothing blocks. D1-D6 (`docs/plans/phase-v1.md`), G9 and D4 (item 400) keep their defaults unless Guy overrules.
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/700-phase-7-windows-proven.md`, `600-phase-6-v1-release.md`,
  `420-step-i-release.md`, `400-phase-4-release.md`, `500-phase-5-user-asks.md` (asks verbatim, the port notes).
- I5: `docs/plans/phase-i.md` section 6. The audit: private in `runs/reviews/` (gitignored); maps:
  `docs/commit-map-g8e.tsv`, then g8d.
- PC worker: toolkit docs/pc-worker/HANDOFF.md and `guy-decisions.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
