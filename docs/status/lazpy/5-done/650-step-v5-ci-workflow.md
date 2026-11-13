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
2026-11-13 11:26: `.github/workflows/test.yml` (actions/checkout v7.0.1 and actions/setup-python v7.1.0 pinned by
commit SHA, `permissions: contents: read`) parses (ruby YAML: 7 steps). Its steps ran in a fresh `git clone` of main
(a41f196) under `env -i` with Python 3.14: `tools/fetch.sh --headers`, `make check && make && make test-version`
("test-version ok"), `make test-host` ("test-host: 307782 checks, 0 failed"), the venv and `pip install -e . pytest
numpy`, the fast pytest ("118 passed, 32 deselected"). Python 3.10 runs only on GitHub after the push (none here).

## Pointers
- Plan: `docs/plans/phase-v1.md` section 3
- Reviews: `docs/reviews/phase-v1-review-1.md`, `docs/reviews/phase-v1-review-2.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- The steps ran on main before the core-rev2 merge; V8's clone_check runs the README route on the final HEAD.
