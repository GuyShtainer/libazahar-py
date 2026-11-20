<!-- handoff: slim v1 | current tasks only | rewritten whole from docs/status/templates/handoff.md | budget 80 lines | never append -->
# libazahar-py handoff

As of: 2026-11-20 02:37 (session 3ds-toolkit-eb)

This file lives in docs/status/lazpy/1-in-progress/, beside its item files. It holds only what
the next session needs to act now, and points at the rest. Goals, rules, decisions and history live elsewhere.

## Running now
| What | Where | Agent id | It stops when |
|---|---|---|---|

Phase 8 is under way: Guy, 2026-11-18 ~21:00, "you have my green light. go". He did not answer Q1-Q5, so the
plan's recommended answers apply (laz-810 notes). Phase A is done: runs/p8/a/decisions.md. All lane PC jobs go
through runs/p8/bin/pclane under one shared PC lock (one job of ours at a time since the 2026-11-18 PC crash).

## Next steps, in order
1. Phase B is done (laz-821 to 829 in 5-done). laz-820 stays open for test-windows.yml and test.yml on a pushed
   commit (the push waits on Guy) and the two 3-copy pool tests (CI or the Mac). The core leak fix waits for the next core phase.
2. Phase C (laz-830): C1 command line and C2 audio done (laz-831, 832; the full PC gate 02:50 after the review fixes).
   C3 exact inputs parked (laz-833) for the next core phase with the leak fix. Next: C6, release v1.2.0, by the list
   under the plan's phase C table (docs/plans/phase-8.md). Step 1 drafts (version 1.2.0, README, STATUS) are on main.
   Main pushed 07:03 (Guy's yes). CI round 1: test-windows and test (macOS) red on two guards only: the skip
   lists lacked phase 8's new Windows skips, and the macOS Makefile guard did not allow host/audio.c. Both fixed
   locally and proven on the PC (fast tier + skips_check; the w7 rules on the real junit). C6a's prefix fix is
   written (tools/build-core-win64.sh: the three OpenSSL folders on the make line, the build fails if any is not
   under C:/Program Files/; mkrelease's zip SOURCE.md names the snapshot), committed locally as 587c171.
   Guy, 07:15: HOLD the push (asked after the red round). Nothing is pushed until he says so; then test-windows,
   test and core-win64 (C6a's one round), then fetch.sh's new Windows pin and the docs.
   macOS live run 44462572191 (the hosted runner, the v1.0.0 macOS core): 427 passed, 2 failed. (a) test_state: state
   boot 3.16 s over the 2.5 s bound: the hosted-runner case Q4 makes record-only in phase D. (b) NEW, not seen on the
   PC: test_determinism two_tick_seeds_differ, the clock field t moved 0 ms for a 1000000-tick seed (3-4 wanted).
   Cause found (laz-834): the core counts the clock from 2000-01-01 in the HOST's local zone; our start time is just
   before that midnight in UTC, so a UTC host reads 0. Fix built in lane p8-tz (runs/p8/wt/tz), unmerged: the worker
   runs with TZ=UTC0, the start time is 946688477 (the clock UTC+2 machines saw), USING 10a, a 3-zone test.
   Commits bc51552 + 81fdcbc (review fixes; opus review: merge after fixes, done). PC full suite 440 passed.
   Merge on Guy's morning word, moving laz-834 to 5-done in that commit; then macOS live after the push.
   The release audit must also read commit 44ad3c5's text (review finding 2).
3. Not run anywhere yet: make check (clang analyze) on the new C; CI's macOS job runs it after a push.
   docs_check's links check fails on the PC lane only (no .git there); it runs on the Mac.

## Waiting on Guy (only what blocks a step above)
- Pushes: each one needs his word. Local main is ahead of origin, and phase 8 commits stay local until he says so.
- Push main (587c171 + status commits) and start core-win64's one round: Guy said yes, "Push and rebuild"
  (relayed by the goodnight session, 2026-11-20 02:20). The push was blocked by the Mac's permission check (a yes
  relayed by another session does not count there), so it waits for him to say it here, or he runs
  `git push origin main` himself; then `gh workflow run core-win64.yml` and test.yml. Docs check passed 02:20.
- v1.2.0 waits for the clock cause: Guy said yes, "find cause first" (relayed 02:20). Cause found (laz-834).
- NIGHT DECISION 2026-11-20 02:18: how to fix the host-zone clock | took: worker TZ=UTC0 + start time 946688477
  (recommended) | others: ship it as a known macOS limit; pin TZ in the tests only | switch costs: drop branch p8-tz
  | work: lane p8-tz (runs/p8/wt/tz), its commits, not merged
- The PC install of diffutils and actionlint: the classifier denied it; Guy was asked and has not answered.
The full list is generated into `docs/status/README.md`.

## Pointers
- Plan: `docs/plans/phase-8.md` (rev 1; phase B rows at lines 165-173). Lane briefs: `docs/plans/phase-8b-briefs.md`.
- Items: laz-820 and its steps 821-829 in 1-in-progress; 830 and 840 in 4-not-started.
- PC commands: `docs/map/runners.md` (Windows PC section); the helpers runs/p8/bin/pc and pclane are outside git.
- Progress page: https://claude.ai/artifact/TFaGBKNbr5pDFZGDCNJUgH. Republish it only inside the progress command
  or when Guy asks.
- Rules that bite every turn, and the stop list's place: `docs/map/rules.md`. Everything else: `docs/map/README.md`.
