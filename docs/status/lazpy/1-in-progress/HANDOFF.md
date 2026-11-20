<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 09:25 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|
| laz-820/830: CI on pushed d449db0 (09:24): test 44694732962, test-windows 44694733821 | GitHub Actions | main | both finish |

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Phase B is done (laz-821 to 829 in 5-done). laz-820 stays open for test-windows.yml and test.yml on a pushed
   commit (the push waits on Guy) and the two 3-copy pool tests (CI or the Mac). The core leak fix waits for the next core phase.
2. Phase C (laz-830): C1 command line and C2 audio done (laz-831, 832; the full PC gate 02:50 after the review fixes).
   C3 exact inputs parked (laz-833) for the next core phase with the leak fix. Next: C6, release v1.2.0, by the list
   under the plan's phase C table (docs/plans/phase-8.md). Step 1 drafts (version 1.2.0, README, STATUS) are on main.
   CI round 2 on pushed 5cf51cf (Guy's push, morning 2026-11-20): test-windows green; core-win64 green (C6a's one
   round: artifact core-win64, sha256 025d8a54..., run 44691632561); macos-live 429 passed, 1 failed (test_state's
   2.5 s bound at 2.76 s, phase D's record-only case): the clock fix (laz-834, merged) works on a UTC host. test
   (macOS) red on my Makefile guard (the sed also stripped audio.o off its own compile line). Fixed (f44ee12),
   proven on the real make -B -n output, clang analyze on the Mac clean (24 files), pushed d449db0 on Guy's yes.
   Next, C6 step 1: stage v1.2.0 with mkrelease from core-win64's artifact (fetch.sh's Windows zip sha256 is filled
   at staging), the OpenSSL docs (core/OPENSSL.md 81-83, STATUS.md:100, USING:484), then release_check --pre-push.
   The release audit must also read commit 44ad3c5's text (review finding 2).
3. make check's analyzer passes on the Mac by hand (2026-11-20 09:2x); CI's macOS job runs it on d449db0.
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
