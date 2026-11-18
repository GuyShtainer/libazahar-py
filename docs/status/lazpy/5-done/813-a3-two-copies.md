---
id: laz-813
title: lazpy
order: 813
kind: step
parent: laz-810
page: Phase A: one copy, then two, of the 3D scene
hours: -
---
# A3: one and two copies

## What it is
GPU memory, peak RSS and guest fps for one and two copies of the test app's 3D scene; private numbers.

## Exit gate
Numbers in runs/p8/a3/ and the cap decision.

## Evidence
2026-11-19 01:15: one copy, then two, of the 3D scene ran with no memory trouble, about 1 GB RSS and 117 MB GPU memory per copy,
two copies at x1.88 the total fps; the cap stays 4 (runs/p8/a/decisions.md, outside git).

## Pointers
- Plan section: `docs/plans/phase-8.md:150`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
