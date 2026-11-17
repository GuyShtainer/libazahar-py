<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-17 20:51 (session 3ds-toolkit-eb; it also runs the PC worker)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
- Item 700: the Windows port, proven (Guy: "move forward so its windows proven"). Plan revision 2 is final
  (`docs/plans/phase-7.md`); briefs in `docs/plans/phase-7-briefs.md`. Steps are items 701-714.
- Item 711: W7, the fresh-clone check on the PC. Local main d6b9793 (unpushed since 6345b83). Run 2 was clean but
  for the fixture test (fixed since); run 3 failed only on PC load. Nothing runs now: the PC crashed twice
  (19:31, 20:48) under 3DP builds, and all PC work is held until Guy has looked at it.
- Item 600 / 420: v1.0.0 published 11:08. W10's post-publish check closes I5 part 2.

## Next steps, in order
1. Item 711, once Guy says the PC is fine and it is quiet: `git bundle create runs/p7/w7/main.bundle main --tags`,
   tar it to D:\lazpy\p7\w7, then in MINGW64 bash (script as a file argument, never piped through Get-Content: BOM)
   `bash -l /d/lazpy/p7/w7/stage-pc.sh`, then `cc-pc.sh` (4 copies), then
   `powershell -File D:\lazpy\p7\w7\rc-pc.ps1` with ~/.lazpy-private/needles.txt on stdin. Gate: clone_check rc 0,
   skips_check --list w7 rc 0, release_check rc 0 with only `<pick after W9>` PEND. Logs runs/p7/w7/.
2. W7c (Gen3D and 3DP one normal job each on the release candidate), then W8: release-legal-audit with
   runs/p7/w8/brief.md (re-copy the new SHA256SUMS and build-files asset into runs/p7/w8/staged first), then ask
   Guy for the publish word (item 712). W9 and W10 after that.
3. After W10 passes: close items 420, 400 and 600; delete the private history bundles (incl. ~/.lazpy-private/g8e),
   their clones and .git/filter-repo.
4. Pre-push checks need `LAZ_PRIVATE_NEEDLES=~/.lazpy-private/needles.txt` (keep that file; not in the repo).
5. Answer asks from Gen3D and 3DPlatinum; coordinate the PC (free RAM >= 2 GB + 0.6 GB per copy).

## Waiting on Guy (only what blocks a step above)
- The PC: crashed 19:31 (WHEA cache error, bugcheck 0x101) and again 20:48, both under 3DP builds. No PC work
  until Guy says it is fine.
- Pushes: Guy 2026-11-17 ~19:50 "No pushes for now" (each failed GitHub run mails him; the macOS jobs of test.yml
  and macos-live.yml get no GitHub runner and end failed). Ask before any push.
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
