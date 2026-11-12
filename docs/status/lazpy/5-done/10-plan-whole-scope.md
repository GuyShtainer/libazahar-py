---
id: laz-10
title: lazpy
order: 10
kind: phase
page: Plan the whole project: scope, phases, costs
hours: plan
---
# Plan the whole scope

## What it is
One opus plan for the whole tool, from the research to a public release: what is built (the headless C host, input
and touch, memory reads, savestates, the Python layer, a many-instance runner, the fetch script for the core and
MoltenVK, a homebrew test app built from source, CI-style tests, docs, the legal audit, the GitHub release), in
phases, each with an exit gate and an hours estimate. It also decides the Python route (libretro.py or our own C host
plus ctypes) and where Gen3D's adapter ends and this repo begins.

## Exit gate
`docs/` (PLAN.md) written, with phases, gates and estimates, and added to `ANCHOR_FILES` in `tools/mkmap.py`
(so its headings get line numbers in the generated map); then laz-11.

## Evidence
2026-11-12, opus agent aa56e6986026ffbe0: `docs/PLAN.md` written (290 lines; phases A to I, about 40 to 42 h; speed,
scaling and memory branches marked "pending spike 2"); added to `ANCHOR_FILES` in `tools/mkmap.py`; mkmap,
mkprogress, status_check --strict-handoff and map_check pass. Its two questions for Guy are in PLAN.md section 7.

## Pointers
- Research: `docs/research/` (spike 1, prior art, Gen3D's needs; spike 2 when it lands)
- Prototype: `prototype/README.md`
- Rules: `docs/map/rules.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.

- Guy's order (2026-11-12): "the progress page, progrs files, indexing, plan the whole scope, revisions and than per
  phase". So: whole-scope plan, two review loops with revisions, then one item and one plan per phase.
- Hour-saving pass in each revision: look for cheaper code, tests and existing online solutions (libretro.py, the
  Azahar RPC's request set, libmgba-py's API shape) before building.
