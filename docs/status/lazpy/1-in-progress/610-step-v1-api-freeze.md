---
id: laz-610
title: lazpy
order: 610
kind: step
parent: laz-600
page: Freeze the public API for 1.0 and write down its file formats
hours: -
---
# API freeze for 1.0 (plan step V1)

## What it is
Freeze the public API for 1.0: review every public name, default and file format, apply the few changes worth making now, write down the option-profile format and the azhost exit codes.

## Exit gate
`docs/plans/phase-v1.md` section 3, V1: make, make test-host, the fast pytest and the changed tests pass on the branch.

## Evidence
none yet

## Pointers
- Plan: `docs/plans/phase-v1.md` section 3
- Reviews: `docs/reviews/phase-v1-review-1.md`, `docs/reviews/phase-v1-review-2.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 11:25: the review is saved (`docs/reviews/api-freeze-1.0.md`): 13 changes before 1.0, three of them
  breaking for callers (keyword-only `run` options, `run_until`'s names, `Path` returns), none hitting Gen3D or
  3DPlatinum by the reviewer's check. All 13 taken; item 13's Touch/Circle range check skipped (optional).
- 2026-11-13 11:28: briefs `docs/plans/v1-briefs.md`; two sonnet agents in the worktree on separate files (host:
  items 1 C side, 2, 3, 12; python: items 1 Python side, 4-10, 13). Item 11 (the `LAZPY_ROOT` alias) is the main
  loop's. 3DPlatinum left the worktree first (its word came by 11:28).
