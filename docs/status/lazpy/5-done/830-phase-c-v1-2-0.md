---
id: laz-830
title: lazpy
order: 830
kind: phase
page: Phase 8 C: command line, audio, exact input, then release v1.2.0
hours: phase-8c
---
# Phase 8 C: agents and siblings, then v1.2.0

## What it is
Steps C1-C6a of the plan, then the v1.2.0 release.

## Exit gate
v1.2.0 published, audit shippable, post-publish clone check passes.

## Evidence
2026-11-19 02:32: full PC gate on merged phase C (host ABI 5 and the tone app built in the lane): 409 passed, 11
skipped, 1 xfailed (laz-829), 4 failed: test_verdict_live.py ran the example with -I, which ignores PYTHONPATH, so it
imported the venv's installed v1.1.0 (ABI 4). Fixed (the repo's package first on sys.path); 02:34 rerun of the
verdict, audio and CLI tests: 37 passed. C3 waits on a core patch (laz-833, parked for the next core phase). The review runs.
2026-11-19 02:50: the review and both fix lanes merged; full PC gate 439 passed, 12 skipped, 1 xfailed. C1, C2 done;
C3 parked; C4 dropped. Next: C6 (release v1.2.0), with C6a; test-windows.yml and the macOS jobs need a push.
2026-11-19 07:13: main pushed (Guy, 07:03). CI round 1 red on two guards (the skip lists, the macOS Makefile guard and
host/audio.c), fixed and proven on the PC; C6a's OpenSSL folder fix and the zip SOURCE.md entry written, not yet built.
2026-11-19 07:21: macos-live run 44462572191 on pushed main: 427 passed, 2 failed: test_state's 2.5 s state boot bound (3.16 s,
hosted runner; phase D's record-only case) and test_determinism two_tick_seeds_differ (t moved 0 ms on the macOS core; open).
2026-11-20 08:56-11:01: the clock fix (laz-834) merged and pushed; CI round 2 on 638f2a8: core-win64 green (C6a,
laz-835), test-windows green, macos-live 429 passed 1 failed (test_state's bound only); rounds 3-4 fixed the macOS
Makefile guard and the skips list; test and test-windows green on 934dd94.
2026-11-20 11:15: C6 steps 1-2 on the PC (bundle clone of 2ea7720): mkrelease rc 0, Windows zip sha256 404583fa...
(the same bytes from f65a746 and 2ea7720), SHA256SUMS 4e2df781... before the pin commit; release_check --pre-push:
14 PASS; open: 12 history needles (37 hits, all /Users/<mac user> paths in plan docs public since v1.0.0; no line
added since v1.1.0 holds one), 13 PEND (step 7), 16 the notes' macOS line TO BE FILLED (step 5).
2026-11-20 11:35: C6 steps 3-4 on the PC from the bundle of a0ca779: clone_check rc 0 (full suite, the two 3-copy
pool tests deselected on the 2-copy PC: 439 passed, 13 skipped, 1 xfailed; skips_check --list w7 0 problems). The
first try (a526b24) failed only the skips step: the two tone-app audio tests cannot run in a clone, now allowed in
w7. mkfixture v1.2.0 rc 0 (win32, core ee3e9e0a..., frame_total 600, k 0) in the clone's runs/release-fixtures.
2026-11-20 11:36: C6 step 6, a private side test, details kept outside the repo: passed with the a0ca779 clone.
2026-11-20 12:14: C6 step 5, pushed 934dd94..845f6a4 on Guy's word ("Push main"): test.yml run 44715294673 green
(3.10 and 3.14: 354 passed, 9 skipped), macos-live run 44715249847 green (430 passed, 25 skipped, 0 failed; the tone
tests skip there: audio capture untested on macOS, said in STATUS and the notes), test-windows run 44715237141 green.
2026-11-20 11:59: C6 step 7, check 13 run read-only on the Mac (history_bytes_check on 845f6a4): 2070 blobs, 0 hits.
2026-11-20 12:37: C6 step 8, release-legal-audit on 3b548e9 and the staged copy (SHA256SUMS 36af4ae7..., 12 of 12):
not shippable as staged; the 13 assets clean (seven inherited = v1.0.0's sums, the DLL = the attested ee3e9e0a...,
source on the page complete). B1 (one plan sentence) and S1 fixed in the tree 12:37, with notes N1-N5; N7's
.gitignore names left out (the file name is not written in public files). N10: core/OPENSSL.md differs from the
build commit 638f2a8 in prose only, its "- Source:" line unchanged (as v1.1.0's P1). Check 12's history-only paths:
Guy's ruling judged enough. R1 (the sentence in published history) waits on an IP consult and Guy's choice.
2026-11-20 15:04: R1 closed on Guy's choice ("Rewrite history"): main rewritten and force-pushed (head 0257fcd),
tags unchanged; the Windows core rebuilt on 0257fcd (laz-835: run 44737890394, zip fe0bbfd1..., pinned);
test-windows run 44737848948 green on 0257fcd. Next: CI, re-stage and clone check on the pinned head.
2026-11-20 15:40: on pushed 2f959c0 (the pin): test-windows 44741192320 and test.yml 44741219449 green (354
passed, 9 skipped each); macos-live 44741224096 429 passed, 25 skipped, 1 failed in both attempts (test_state_boot's
2.5 s bound on the hosted runner, 3.3 and 3.4 s; said in STATUS and the notes). PC re-stage (SHA256SUMS fe729508...,
Windows zip fe0bbfd1...): release_check 15 PASS, 12 and 13 as ruled; check 13 on the Mac 0 hits; clone_check rc 0
(439 passed, 13 skipped, 1 xfailed); fixture v1.2.0 remade on core 81845090.... The 14 CI runs on rewritten commits
deleted (private list in runs/p8/c6/); the p8 lane branches moved onto their rewritten commits.

## Pointers
- Plan section: `docs/plans/phase-8.md:180`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
- From laz-829 (2026-11-19): the next core phase (after phase 8; C6a is only a CI rebuild of the same patches) must fix the unserialize step's leak of about 2.2 Semaphore
handles per load_state (a winpthreads condvar shape; needs a traced core build). Then flip test_handles_live.py's
strict xfail to a pass.
