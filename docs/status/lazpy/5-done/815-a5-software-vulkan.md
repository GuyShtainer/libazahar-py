---
id: laz-815
title: lazpy
order: 815
kind: step
parent: laz-810
page: Phase A: try a GPU-less Vulkan driver on the PC
hours: -
---
# A5: software Vulkan trial

## What it is
Unpack MSYS2's pinned Mesa package (lavapipe) into its own folder and run two emulator tests on it.

## Exit gate
Both tests pass or not, in runs/p8/a5/; the D3 decision.

## Evidence
2026-11-19 01:22: inconclusive. The pinned packages unpack and load, but the tests ran on the RTX: the elevated ssh session makes the
Vulkan loader ignore the driver override. S10 stays missing; D3 goes to its own CI round with a registry entry on the
runner (runs/p8/a/decisions.md, outside git).

## Pointers
- Plan section: `docs/plans/phase-8.md:152`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
