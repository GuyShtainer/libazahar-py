---
id: laz-814
title: lazpy
order: 814
kind: step
parent: laz-810
page: Phase A: does sound come out of the core at all
hours: -
---
# A4: audio probe

## What it is
A scratch host patch (never merged) counts audio samples; checks whether our own made-up DSP file lets sound start. Nintendo's DSP firmware is never used.

## Exit gate
Numbers in runs/p8/a4/ and the C2 decision.

## Evidence
2026-11-19 01:16: with our own made-up DSP file, the tone app's sound reaches the host (547 stereo frames per guest frame,
99.8 % non-zero, from frame 62); without it, none. C2 is built, gated on the tone app (runs/p8/a/decisions.md, outside git).

## Pointers
- Plan section: `docs/plans/phase-8.md:151`
- Review: `docs/reviews/phase-8-plan-review.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy, 2026-11-18 ~21:00, verbatim: "you have my green light. go". Q1-Q5 not answered: the plan's recommended
answers are in force (Q1 yes, Q3 yes, Q4 yes to D after v1.2.0 / two releases / the hosted bound / the MSYS2 Mesa
download, Q5 probe now) until Guy says otherwise.
