---
id: laz-650
title: lazpy
order: 650
kind: step
parent: laz-600
page: Automatic tests on GitHub, ready for the first push
hours: -
---
# CI workflow for the first push (plan step V5)

## What it is
A GitHub Actions workflow that builds the host and runs the fast tests on a macOS 15 arm64 runner, Python 3.10 and 3.14. It runs only after Guy pushes; until then its steps are proven in a fresh clone.

## Exit gate
`docs/plans/phase-v1.md` section 3, V5: the steps pass in a fresh clone under env -i, and the YAML parses.

## Evidence
none yet

## Pointers
- Plan: `docs/plans/phase-v1.md` section 3
- Reviews: `docs/reviews/phase-v1-review-1.md`, `docs/reviews/phase-v1-review-2.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
