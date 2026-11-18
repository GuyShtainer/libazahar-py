<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-19 01:28 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-823 + laz-826: error evidence, parent death | runs/p8/wt/life (p8-life) | a6b0fe70c10ad86e4 | its final message |
| laz-829: handle leak per state load | runs/p8/wt/leak (p8-leak) | ac78fd5236d372d02 | its final message |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Lanes rel, live and images (laz-821, 822, 824, 825, 827, 828) are merged. As each other lane ends: check its diff and its PC test lines, commit it on its branch, move its items to 5-done with
   Evidence (laz-829: copy LEAK-NOTES.md's finding into the item, then delete that file).
2. With all five merged: the full PC gate (fast + live tests) through pclane.
3. The opus as-built review, docs/reviews/phase-8b-as-built.md (brief at the end of docs/plans/phase-8b-briefs.md);
   sonnet fixes; laz-820 to 5-done.
4. test-windows.yml on the merge needs a push: ask Guy.
   docs_check's links check fails on the PC lane only (no .git there); it runs on the Mac. Then phase C (laz-830).

## Waiting on Guy (only what blocks a step above)
- Pushes: each one needs his word. Local main is ahead of origin, and phase 8 commits stay local until he says so.
- The PC install of diffutils and actionlint: the classifier denied it; Guy was asked and has not answered.
The full list is generated into `docs/status/README.md`.

## Pointers
- Plan: `docs/plans/phase-8.md` (rev 1; phase B rows at lines 165-173). Lane briefs: `docs/plans/phase-8b-briefs.md`.
- Items: laz-820 and its steps 821-829 in 1-in-progress; 830 and 840 in 4-not-started.
- PC commands: `docs/map/runners.md` (Windows PC section); the helpers runs/p8/bin/pc and pclane are outside git.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
