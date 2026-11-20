---
id: laz-842
title: lazpy
order: 842
kind: step
parent: laz-840
page: Phase D: a CI recipe for outside users and the hosted-runner state-boot rule
hours: -
---
# D2: the CI recipe

## What it is
Phase D: a CI recipe for outside users and the hosted-runner state-boot rule.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane and in its CI workflow; the lane merged on main; the D5 review's findings fixed.

## Evidence
2026-11-20 16:34: lane merged on main: `examples/ci/macos.yml`, `docs/CI.md`, and the state-boot bound that only records on a GitHub-hosted runner (test_state_bound.py); test_state live 4 passed on the PC.
2026-11-20 20:24: macos-live run 44789222255 on da90a6a: 432 passed, 25 skipped, 0 failed, and its recipe step printed "verdict ok". Done.

## Pointers
- Plan section: `docs/plans/phase-8.md:208`
- Briefs: `docs/plans/phase-8d-briefs.md`; review: runs/p8/d/d5-review.md (private)

## Lessons and notes
Read this part only when you work on this item.
