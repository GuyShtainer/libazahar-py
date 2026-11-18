---
id: laz-820
title: lazpy
order: 820
kind: phase
page: Phase 8 B: close the Must gaps (determinism, evidence, exit codes, cleanup, window test)
hours: phase-8b
---
# Phase 8 B: the Must gaps

## What it is
Steps B0-B8 of the plan: every Must row becomes have. Python, tests, docs, one release tool.

## Exit gate
The full PC gate passes with only the known skips; test-windows.yml green on the merge commit.

## Evidence
2026-11-19 01:50: the full PC gate on merged main (2777af1 + handoff commits), fast + live, the two 3-copy pool tests
excluded (PC rule: 2 copies): 357 passed, 11 skipped (each with its reason), 1 xfailed (the core's handle leak,
laz-829) in 6 min 16 s. The review runs.

## Pointers
- Plan section: `docs/plans/phase-8.md:158`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
- From A2 (laz-812, 2026-11-19): add step B9, the handle leak per state load. On Windows, worker handles rise by about 2
  per load_state (415 to 1023 over 300 loads); RSS stays flat. Find whether the host or the core holds them; check
  macOS for a matching fd leak (its default limit of 256 would fail after about 120 loads); fix it; add a test that
  200 loads keep the count within 5 %. Plan rule (A2 row): growth over 10 % opens a fix step in B.
