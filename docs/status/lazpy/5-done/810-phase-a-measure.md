---
id: laz-810
title: lazpy
order: 810
kind: phase
page: Phase 8 A: measure first (memory over time, two copies, audio, a GPU-less driver)
hours: phase-8a
---
# Phase 8 A: measure first

## What it is
Numbers for the rows the research left thin; each decides whether a later build happens. No product change.

## Exit gate
runs/p8/a/decisions.md with each probe's numbers and one build-or-drop line (plan A-exit).

## Evidence
2026-11-19 01:22: runs/p8/a/decisions.md (outside git).
- Soak: boots clean; a handle leak of 2 per state load opens B9; C4 is dropped.
- Two copies fine: the cap stays 4.
- Audio works with our own made-up DSP file: C2 is built.
- Software Vulkan is inconclusive on the PC (elevated session): D3 is proven in CI.

## Pointers
- Plan section: `docs/plans/phase-8.md:141`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
- PC crash 2026-11-18 ~23:00 during the soak while two of our jobs ran at once (soak + package unpack): our fault; one
  job strictly from then on. Per-copy RAM is about 1 GB (test app) against the PC rule's 0.6 GB: tell Guy.
