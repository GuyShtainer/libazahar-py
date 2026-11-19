<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-19 02:34 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-830 the opus review of phase C, as built | docs/reviews/phase-8c-as-built.md (Mac, read-only) | a2c24efaeec4b7f9a | its final message |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Phase B is done (laz-821 to 829 in 5-done). laz-820 stays open for test-windows.yml and test.yml on a pushed
   commit (the push waits on Guy) and the two 3-copy pool tests (CI or the Mac). The core leak fix is in C6a.
2. Phase C (laz-830): lanes cli (laz-831) and hostav (laz-832) are merged; C3 exact inputs (laz-833, in 2-next) needs
   a core patch first, so it moves into C6a with the leak fix (notes in 833 and 830). The PC gate is green (laz-830 Evidence). Next: the opus
   review (brief at the end of docs/plans/phase-8c-briefs.md), its fix lanes, then C6 release v1.2.0.
3. Not run anywhere yet: make check (clang analyze) on the new C; CI's macOS job runs it after a push.
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
