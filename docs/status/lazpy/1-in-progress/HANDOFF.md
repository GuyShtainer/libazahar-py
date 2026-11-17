<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 20:00 (session 3ds-toolkit-eb; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). Plan revision 2 is final
  (`docs/plans/phase-7.md`); briefs in `docs/plans/phase-7-briefs.md`. Steps are items 701-714.
- Item 711: W7 + W7c, staging v1.1.0. Item 710 (W5) is done: core-win64 run 44138010543 on main 6345b83, DLL sha256
  9f45bca561fe674c1edcfb59b532e0f84edc09263b7a8292876ce24bae124f62, attestation 68746211; evidence
  runs/p7/w5/checks.txt. The artifact is on the PC at D:\lazpy\p7\w5\art (sha checked there).
- Item 600 / 420: v1.0.0 published 11:08. W10's post-publish check closes I5 part 2.

## Next steps, in order
1. Item 711 (W7, plan line 311): merge main into p7-docs (worktree runs/p7/wt/w6; version 1.1.0 lives there),
   check `git diff 6345b83 p7-docs -- $(cat tools/build-files.txt)` is empty, bundle p7-docs to the PC, clone,
   fetch tags, then in MSYS2 `sh tools/mkrelease.sh --inherit v1.0.0 --win-artifact D:/lazpy/p7/w5/art --out
   D:/lazpy/rel/v1.1.0`; log the staged SHA256SUMS sha. Pins on p7-docs (REL_TAG, REL_TAG_PREV,
   LAZPY_CORE_ZIP_WIN, LAZPY_CORE_SHA_WIN), OPENSSLDIR line from build.inputs, merge p7-docs into local main.
2. The 4-copy clone_check and release_check (plan W7 steps 3-6): only after Guy's word that the PC is stable.
3. W7c, then W8 (release-legal-audit, one opus slot; note the four Windows-only components in item 712), then ask
   Guy for the publish word. W9 and W10 after that.
4. After W10 passes: close items 420, 400 and 600; delete the private history bundles (incl. ~/.lazpy-private/g8e),
   their clones and .git/filter-repo.
5. Pre-push checks need `LAZ_PRIVATE_NEEDLES=~/.lazpy-private/needles.txt` (keep that file; not in the repo).
6. Answer asks from Gen3D and 3DPlatinum; coordinate the PC (free RAM >= 2 GB + 0.6 GB per copy).

## Waiting on Guy (only what blocks a step above)
- Pushes: Guy 2026-11-17 ~19:50 "No pushes for now" (each failed GitHub run mails him; the macOS jobs of test.yml
  and macos-live.yml get no GitHub runner and end failed). Main 6345b83 is the last push. Ask before any push.
- The PC crashed at ~19:31 (WHEA cache error on a core, bugcheck 0x101) under 3DP + Gen3D builds; back 19:42.
  One light PC job at a time until Guy says the PC is fine.
- The PC install of diffutils and actionlint: denied by the permission classifier; Guy asked, no answer.
- The v1.1.0 publish word is asked at the end of W8 (item 712).
The full list is generated into `docs/status/README.md`.

## Pointers
- Items: `docs/status/lazpy/1-in-progress/700-phase-7-windows-proven.md` and its steps 701-714;
  `600-phase-6-v1-release.md`, `420-step-i-release.md`, `400-phase-4-release.md`, `500-phase-5-user-asks.md`.
- Reviews: `docs/reviews/phase-7-review-1.md`, `docs/reviews/phase-7-review-2.md`. Evidence: runs/p7/<step>/.
- PC worker: toolkit docs/pc-worker/HANDOFF.md and `guy-decisions.md`.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH; republish only inside the progress command or
  when Guy asks.
- Rules that bite every turn: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
