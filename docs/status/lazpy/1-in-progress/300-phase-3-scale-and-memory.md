---
id: laz-300
title: lazpy
order: 300
kind: phase
page: Phase 3, scale and memory: many copies, our core passes the full tests, memory reads
hours: phase-3
---
# Phase 3, scale and memory: many copies, our core passes the full tests, memory reads

## What it is
The instance pool and speed table, our built core gated with the full test batch, then memory reads and writes. Steps laz-310, laz-320, laz-330 (PLAN.md: E, F2, G).

## Exit gate
Every step's gate passes (each step file names its PLAN.md line). Before any step is built: the phase plan
(`docs/plans/`), opus review 1, revision, opus review 2, revision (Guy's rule: two loops per phase).

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md` section 3
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Guy 2026-11-12 chose four phases over ten small ones ("4 phases (Recommended)"), each with one plan and two
  review loops; the ten PLAN.md phases became steps.
