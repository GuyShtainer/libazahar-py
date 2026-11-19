<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-19 02:20 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-832 + laz-833: audio capture, exact inputs (host ABI 5) | runs/p8/wt/hostav (p8-hostav) | acc71522513f7ee40 | its final message |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Phase B is done (laz-821 to 829 in 5-done). laz-820 stays open for test-windows.yml and test.yml on a pushed
   commit (the push waits on Guy) and the two 3-copy pool tests (CI or the Mac). The core leak fix is in C6a.
2. Phase C (laz-830): briefs docs/plans/phase-8c-briefs.md. Lane cli (laz-831) is merged on main. When hostav ends:
   review its diff, commit on p8-hostav, merge, then the full PC gate (command in docs/plans/phase-8b-briefs.md).
3. Then the opus review (brief at the end of phase-8c-briefs.md) and its fix lanes; then C6, release v1.2.0.
   docs_check's links check fails on the PC lane only (no .git there); it runs on the Mac.

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
