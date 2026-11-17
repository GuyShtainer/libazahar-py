---
id: laz-702
title: lazpy
order: 702
kind: step
parent: laz-700
page: Windows proof: review every change the Windows port makes
hours: -
---
# Windows proof: review every change the Windows port makes

## What it is
W1a (main loop, on the PC): the Darwin-visible preprocessed diff and the make -B -n diff of v1.0.0 vs the branch. W1 (opus): the full diff review of port-win-v1, including a per-line verdict on Python that macOS sees.

## Exit gate
runs/p7/w1a/darwin-pp.diff and make-n.diff exist (planted-line check passes); docs/reviews/phase-7-diff-review.md per the W1 gate. Plan: `docs/plans/phase-7.md` line 225.

## Evidence
- 2026-11-17 12:25 W1a PASS (runs/p7/w1a/, local): on the PC, MSYS2 gcc -E with Apple predefines and 92 empty
  system-header stubs over 35 C files per tree; the diff is done on the Mac (the PC MSYS2 has no diff).
  darwin-pp.diff 783 lines / 60 hunks / 35 files; make-n.diff one added line, tools/check-obinary.sh (the allowed
  one); a planted __APPLE__ line shows, a planted _WIN32 line does not. W1 (opus review) dispatched 12:26.
- 2026-11-17 12:40 W1 PASS: docs/reviews/phase-7-diff-review.md, verdict "fix then merge". Darwin coverage: C 60/60
  hunks in 35/35 files, Makefile 1/1 line (check-obinary), Python 101/101 hunks in 21/21 files. 19 findings
  P7-R1-1..19: 1 blocker (R1-1, tools/build-core.sh changed; W2b1 restores it), 8 should, 10 nit. Plan B5, B6,
  B10, B12, B13 still hold. Owner conditions 1, 3, 5, 7 quoted and hold (1.1.0 bump left to W6).

## Pointers
- Plan section: `docs/plans/phase-7.md:225`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- W1a: -undef drops __BYTE_ORDER__, and hostmap.c #errors without it; the script adds the arm64 clang byte-order and
  __GNUC__ predefines. A missing `diff` behind `|| true` gave a false "0 hunks"; only the planted line caught it.
  The script now exits 2 when diff is missing.
- W1: owner conditions live in item 500 (lines 39-43), not phase-v1.md. R1-8: the branch has never met real macOS
  headers (W1a used stubs); the first real Mac compile is the macOS CI job after the W4 push of main, so W4 must
  read that job's result before anything else moves.
