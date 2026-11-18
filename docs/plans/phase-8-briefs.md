# Phase 8 briefs: plan, review, revision (laz-802, laz-803, laz-804)

Guy, 2026-11-18 20:08, verbatim: "research what must work on this kind of product, and plan (with single revision)
on how we get there". One plan, one review, one revision, then stop for Guy's go. Opus agents, one at a time.

## Rules for every agent (paste at the top of each brief)

- The repo is `projects/libazahar-py` in the 3ds-toolkit checkout. You write only the files your brief lists. No
  commits, pushes, tags or branch changes; the main loop commits.
- Plan only: no builds, no emulators, no installs. The Mac is closed to 3DS work. Every later build, test and
  emulator run happens on the PC (`docs/map/runners.md`) or in CI, so the plan must say where each gate runs.
- Public docs: plain English, no commercial game titles, no speed claims, no personal paths, usernames or emails.
  A private test is named only as "a private side test, details kept outside the repo", and nothing more.
- Hard rules: `docs/map/rules.md` (keys never shipped or fetched; clean-room; the PC's light-load rule: one job at a
  time, at most 2 emulator copies, free RAM >= 2 GB + 0.6 GB per copy; CI failures email Guy, so pushes go out
  only when CI is expected to pass).
- Save as you go: write your file's skeleton first and fill it section by section.
- Your final message: the files written, their line counts, and the five things Guy most needs to know.

## Brief laz-802: the plan (opus)

Inputs:
- `docs/research/p8/01` to `06` (06 is the inventory of what we have);
- `README.md`, `STATUS.md`, `docs/USING.md`, `docs/HOST-API.md`;
- `docs/PLAN.md` (the first whole-scope plan, for its shape);
- `docs/plans/phase-7.md` (the last phase plan, for its gate style);
- `docs/hours.tsv` (actual hours per past phase, for estimates).

Write `docs/plans/phase-8.md`, at most about 300 lines:
1. **The bar.** What "working" means for this kind of tool. An acceptance checklist, each row: the capability,
   who needs it (test/CI users, script/bot users, RL users, agent users, our own sibling projects), Must/Should/Nice,
   and how it is proven (the test or gate, and where it runs: PC, CI, Mac when Guy frees it).
2. **The gap.** Each checklist row marked have / partial / missing against the inventory, with a pointer.
3. **Out of scope**, with reasons: what we will not do, such as anything that needs console keys.
4. **Phases to close the Must gaps first, then Should.** Each phase: goal, steps, exit gate, where it runs, hours
   (from hours.tsv's actuals for similar work), and risks. Include a release step for each version that ships
   (the legal audit before every release is mandatory).
5. **Open questions for Guy**, at most five, each with a recommended answer.

## Brief laz-803: the review (opus)

Inputs: `docs/plans/phase-8.md`, the research files, and the inventory. Write `docs/reviews/phase-8-plan-review.md`:
- a verdict: ready / ready with changes / not ready;
- numbered findings, each with a severity (blocker, major, minor), the plan line, what is wrong and the fix;
- checks to make:
  - Is every Must row backed by research evidence, rather than invented?
  - Is any Must missing that the research supports?
  - Are the gates real and runnable on the PC or in CI?
  - Are the hours grounded in hours.tsv?
  - Does any step break a hard rule?
  - Are the phases ordered by user value?
- a short list of hour-saving candidates (existing tools, cheaper tests, scope cuts that keep every gate).

## Brief laz-804: the revision (opus), the only one

Inputs: the plan, the review, and the research. Revise `docs/plans/phase-8.md` in place:
- answer every finding (fixed, or rejected with the reason) in a closing table;
- then the **hour-saving pass**: other code shapes, other testing methods, known better algorithms, existing tools
  and solutions found online (web search allowed). Each idea gets the hours saved, what it risks, and taken or
  rejected. Never save hours by dropping a gate or a review;
- update the totals.
