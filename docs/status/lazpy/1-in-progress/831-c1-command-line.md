---
id: laz-831
title: lazpy
order: 831
kind: step
parent: laz-830
page: Phase C: a command line (doctor, run) for agents and shell users
hours: -
---
# C1: command line

## What it is
Phase C: a command line (doctor, run) for agents and shell users.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase C review passed.

## Evidence
2026-11-19 02:16: lane cli merged on main (e30a80a): `python -m libazahar doctor` and `run`; test_cli.py 31 passed on the PC, live doctor and run included. Waits on the phase C gate and review.

## Pointers
- Plan row: `docs/plans/phase-8.md:186`
- Briefs: `docs/plans/phase-8c-briefs.md`

## Lessons and notes
Read this part only when you work on this item.
- No console script: pyproject declares none and the plan asks for none, so `python -m libazahar` (USING 2a).
- doctor prints `pid unknown` for held slots on Windows: the slot locks hold no PID. Real PIDs there need a sidecar file
written by _client.py (a review question).
- 2026-11-19 02:40, fix lane fcli merged (4038fd5): review findings 11-18; test_cli.py 40 passed, 1 skipped (no lsof on
Windows) on the PC, live included. Left for later: the core version in `doctor` without a boot (the worker would
report it from azh_open). The lsof PID branch has never run (the Mac runs no pytest); CI's macOS job runs it.
