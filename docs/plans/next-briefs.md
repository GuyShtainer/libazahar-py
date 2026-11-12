# Ready briefs for the next session (written 2026-11-12 18:25, at the end of a SlowStop)

The main loop dispatches these as written. Both are opus. They may run side by side (the budget is 2 opus at once,
`docs/map/rules.md`), because Phase 2's review checks Phase 1's working copy last.

## 1. Phase 1 plan revision 2 (item laz-100)

Resume the plan's author by SendMessage (`ad1f072f69021fa61`). If that fails, start a fresh opus with this text and
tell it to read `docs/plans/phase-1.md` first.

> Write revision 2 of the Phase 1 plan. Read `docs/reviews/phase-1-review-2.md` (2 blockers, 9 should fix, 12 nice;
> commit 6d421e2). Take both blockers and every should-fix, at least X1, X2, S1, S3, S4, S5 and S7, and each nice item
> unless you say in one line why not. Also take the asks Phase 2 made of Phase 1, listed in
> `docs/status/lazpy/1-in-progress/100-phase-1-foundation.md` under "Lessons and notes" (the never-exit-on-START
> rule, `read_png_rgba(path) -> (width, height, rgba_bytes)` in check_testapp.py, raw shots until C not D, `azh_boot`
> runs no `retro_run`, and `azh_abi_layout`/`azh_error` working before `azh_open`). Check "Interfaces for Phase 2" in
> phase-1.md against `docs/plans/phase-2.md`, `phase-c.md` and `phase-d.md` (revision 1, commit c54a7dd). S1 changes
> the launch: F1's builder stops after configure and the planted reds; the main loop runs the core build detached and
> niced in the main checkout after the as-built review. Write the merge and launch steps that follow from that.
> Do the hour-saving pass (cheaper code, tests or an online solution for each step). Add "Changes from review 2"
> to phase-1.md, one line per finding. Edit only `docs/plans/phase-1.md`, `phase-f1.md`, `phase-a.md` and
> `phase-b.md`. Don't commit, build or run an emulator. Save to disk as you go. Report: hours per step, every item you
> declined and why, and anything Phase 2 must change.

Then: commit, book hours, and launch the Phase 1 builders as the revised phase-1.md says (worktrees at main, checking
`git worktree list` and case-variant names first; items 110/120/130 to `1-in-progress/` before launch).

## 2. Phase 2 plan review 2 (item laz-200)

A fresh opus, not the author.

> Review the Phase 2 plan (`docs/plans/phase-2.md`, `phase-c.md`, `phase-d.md`, revision 1, commit c54a7dd) as
> review 2. Write findings to `docs/reviews/phase-2-review-2.md` only, saving as you go. Find your own problems first;
> only then read `docs/reviews/phase-2-review-1.md` and check that each of its findings is really fixed in the plan
> text. Grade blocker / should fix / nice. Check every claim about Azahar against the source at
> `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (file:line). Check the step briefs a sonnet builder could
> follow without asking: file ownership, gates that can fail, checkpoint reports that end the run (a sub-agent cannot
> wait). Last, check Phase 2's assumptions against Phase 1's plan in the working tree (`docs/plans/phase-1.md`,
> `phase-a.md`, `phase-b.md`; Phase 1's revision 2 may be in progress), and list every mismatch. Do the hour-saving
> pass. Edit nothing else, build nothing, run no emulator. End with a verdict: ready to build after which fixes, and
> whether a third loop is needed.

Then: resume the Phase 2 author (`a4bcf09ec00640830`) for revision 2 from that review. Phase 2's steps build after
Phase 1 merges.
