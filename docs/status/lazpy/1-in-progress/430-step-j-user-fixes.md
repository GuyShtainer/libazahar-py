---
id: laz-430
title: lazpy
order: 430
kind: step
parent: laz-400
page: Fixes from Gen3D's first real use, and a real scene on our core
hours: -
---
# Step J: fixes from Gen3D's first real use, and a real scene on our core

## What it is
Gen3D's first real run (its LAZPY-TRY-1.md) found four rough edges in the Python layer: the timeout for a long
batch, frame 0 giving a plain ValueError, shot keys versus shot file names, and reusing a workdir for its warm
shader cache also keeping old SD files. Fix them with tests and doc lines, then run a real scene on our own core
(not only the test app) on a quiet machine and add that row to the README. Then tell Gen3D and 3DPlatinum to use it.

## Exit gate
Fast pytest and the full emulator pytest pass; docs_check passes; the real-scene row on our core has its source
line; release_check --pre-push 16 of 16 at the new HEAD.

## Evidence
- 2026-11-13 08:36: the four API fixes at the commit that adds this line. `ArgumentError` (a `LibAzaharError` and a
  `ValueError`) for every bad argument, AZH_E_ARG included; `Emulator(fresh_sd=True)` empties the SD folder and keeps
  the rest of `sys/` (refuses a symlinked SD folder); `Shot.frame_total` is the frame since boot, the number in the
  file name; the run() docstring and USING.md say `timeout` is a no-progress limit (Gen3D's report read it as a wall
  bound; the code already was one). New tests: tests/python/test_arguments.py (fast) and three live tests in
  test_api.py (fresh_sd, shot frames, an 8000-frame batch under timeout=1.0). Fast pytest 117 passed; full pytest on
  our core (LAZ_CORE=build-core/..., LAZ_REQUIRE_EMULATOR=1) 146 passed, 3 skipped (two need LAZ_STOCK_CORE, one a
  process not already nice); docs_check all PASS. Log: runs/j/ (ignored). The real-scene run waits for the quiet gate.

## Pointers
- Gen3D's report (read only): Gen3D's docs/research/LAZPY-TRY-1.md
- STATUS.md "Next" (ArgumentError, fresh_sd)

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 08:30, Guy: "Test and fix whats needed. When done tell 3DP and Gen3D agents that the tool is ready and
  that they can and need to use only it". Load at 08:30 was 34/19/10: timed runs wait for the quiet gate.
