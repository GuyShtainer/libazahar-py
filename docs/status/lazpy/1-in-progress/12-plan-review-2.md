---
id: laz-12
title: lazpy
order: 12
kind: phase
page: Plan review 2 and its revision
hours: plan ~ review 2
---
# Plan review 2 and revision

## What it is
An adversarial opus review of the plan (review 2 of 2), then the plan's revision. After it: one item per phase in 4-not-started/, then a plan per phase, starting with the first.

## Exit gate
The review file and the revised plan committed.

## Evidence
none yet

## Pointers
- Plan: `docs/PLAN.md`
- Review: `docs/reviews/` (plan-review-2.md, being written; a fresh reviewer, reads review 1 only after its own findings)

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- For revision 2 (Gen3D session, 2026-11-12, from Guy's question "can you use save states to skip the menu loading
  time?"): booting from a saved whole-console state is a first-class feature, not an extra. Save a state at frame N to
  a file; a later run starts from that file instead of booting. Gen3D uses it to skip the app boot, world build and
  game title on every run after the first. Phase D's gate must show a run started from a state file reaching the same
  screen and log lines. Windowed Azahar can't load states without GUI focus, so this is something only we offer.
