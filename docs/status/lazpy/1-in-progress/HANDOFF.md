<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-19 01:56 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-820 second full PC gate, after the review fixes | PC lane gate | main (bg bo8pg3b6d) | runs/p8/b/gate2.out ends with "local rc=" |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. All five lanes are merged (laz-821 to 829, Evidence written; each waits on the review).
2. The full PC gate passed (laz-820 Evidence). The two 3-copy pool tests run in CI or on the Mac, not on the PC.
3. The review's fixes are merged (fimg, flife, fmisc). After gate2 passes: laz-820 and 821-828 to 5-done; 829
   to 5-done too (cause found, guard in place) with the core fix carried into C6a's item (laz-830's notes).
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
