---
id: laz-811
title: lazpy
order: 811
kind: step
parent: laz-810
page: Phase A: check the PC and add its section to the runners map
hours: -
---
# A0: PC preflight and the runners map

## What it is
PC free RAM and disk, devkitARM r67.1, Python version, the lazpy_movie_play export in the Windows core; a PC section in docs/map/runners.md.

## Exit gate
The checks recorded in runs/p8/a0/notes.md; runners.md has its PC section; mkmap and map_check pass.

## Evidence
2026-11-18 22:58: PC preflight done (runs/p8/a0/notes.md, outside git): RAM, disk, devkitARM r67.1, Python 3.10.11, and the
lazpy_movie_play export in the shipped Windows core (so C3 stays); the PC section is in docs/map/runners.md.

## Pointers
- Plan section: `docs/plans/phase-8.md:148`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
