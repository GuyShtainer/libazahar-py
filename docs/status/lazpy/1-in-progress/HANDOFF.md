<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 11:10 (session 3ds-toolkit-eb, a7 renamed after the crash restart; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 600 / 420: v1.0.0 published at 11:08 (Guy: "ok publish the draft."). I5 part 1 done (assets 8/8 OK). I5 part 2,
  the fresh clone from GitHub plus the full pytest, waits for the Mac (ios garmin's heavy run since 10:50, MAC_BUSY).
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). README and STATUS now say
  "work in progress, not proven". Next: rebase port-win onto main, then the phase-7 plan.

## Next steps, in order
1. Item 700: on the PC (D:\lazpy\src\lazpy-win), add GitHub as a remote, and rebase port-win's 22 commits
   (0537394..7471be0, 56 files) onto main as a new branch port-win-v1, keeping port-win. Main moved only 6 docs
   commits past f93c755 (= old 0537394).
2. Item 700: one opus agent writes docs/plans/phase-7.md (the gate: merged, fresh-clone full pytest with
   LAZ_REQUIRE_EMULATOR=1 on the PC, Windows CI job, legal audit, a Windows asset), then two review loops, then execute.
   Inputs: toolkit docs/pc-worker/NATIVE-PLAN-v3.md, lanes/WB.md, HANDOFF.md (lanes B5-B8).
3. When ios garmin says its run is done: delete ~/.lazpy/MAC_BUSY, tell Gen3D, 3DP and gba-toolkit-b2; then I5
   part 2 (`docs/plans/phase-i.md` section 6, with v1.0.0): `sh tools/clone_check.sh --repo
   https://github.com/GuyShtainer/libazahar-py --branch main --out runs/clone-i5`, then `examples/memory_watch.py`.
   If it passes: close items 420, 400 and 600; delete the private history bundles (incl. ~/.lazpy-private/g8e), their
   clones and .git/filter-repo.
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
