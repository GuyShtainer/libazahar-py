---
id: laz-200
title: lazpy
order: 200
kind: phase
page: Phase 2, control: input, touch, stop rules, the Python layer, savestates and state boot
hours: phase-2
---
# Phase 2, control: input, touch, stop rules, the Python layer, savestates and state boot

## What it is
Frame-exact buttons, touch and circle pad, stop rules and stop reasons, then the Python layer with savestates and starting a run from a saved state; Gen3D starts using the tool here. Steps laz-210, laz-220 (PLAN.md: C, D).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: `docs/plans/phase-2.md`, `phase-c.md`, `phase-d.md` (draft 3147409, revision 1 c54a7dd)
- Review: `docs/reviews/phase-2-review-1.md` (65ebefd); review 2 brief in `docs/plans/next-briefs.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
- Revision 1 (c54a7dd): both blockers fixed (raw shots in C2; builders end their run at a checkpoint and are
  resumed by message), all should-fix and nice except N4 (separate stop code 0, declined). C about 1.9 h, D about
  2.0 h, phase about 4.4 h with its review loops. Author agent id a4bcf09ec00640830.
