---
id: laz-704
title: lazpy
order: 704
kind: step
parent: laz-700
page: Windows proof: fix the host, Python, tests and build files
hours: -
---
# Windows proof: fix the host, Python, tests and build files

## What it is
Sonnet agent: MSYS2 make builds into build/, Python finds it, tests and skips_check.py, the Windows CI file.

## Exit gate
The W2a gate in the plan. Plan: `docs/plans/phase-7.md` line 247.

## Evidence
- 2026-11-17 12:43: dispatched.
- 2026-11-17 12:58 W2a local gates PASS on the PC, committed on branch p7-w2a (55a4ff4): make -j4 OK; test-host
  "307983 checks, 0 failed"; test-version OK; check-obinary "ok 11 open() sites"; pytest fast 251 passed, 5
  skipped, skips_check 0 problems; skips_check --self-test 17/17; Darwin make -n guard differs only on the
  check-obinary line. NOT RUN: `make check` (no clang on the PC), actionlint (not on the PC), pip install -e +
  quickstart (left to W4's full run).
- 2026-11-17 13:12: done; merged into p7-int (9bb34ef) for the W3 fix check. Gates not run here move on: make check
  and actionlint run in CI after the W4 push.

## Pointers
- Plan section: `docs/plans/phase-7.md:247`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
None yet; planned in phase-7 revision 2.
