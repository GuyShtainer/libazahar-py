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
  process not already nice); docs_check all PASS. Log: runs/j/ (ignored).
- 2026-11-13 08:38: a missing core raises BootError naming tools/fetch.sh --lazpy-core and LAZ_CORE (0165d16), with a
  fast test; the stale "until D" comments in host/azhost.h fixed; make clean of warnings.
- 2026-11-13 09:03-09:26: the real scene on our core: `docs/research/real-scene-j.md`. Gen3D's flip dev build, its
  try-1 keys, 36000 frames in one batch, 13 runs interleaved across both cores and three option profiles. Every run
  that stayed quiet (1-minute load under 6 start to end) is 536-571 fps; our core with its default profile 561.4 fps
  (9.38x), Azahar's own 564.2 and 541.7: the cores match; our option lines cost nothing measurable. Guest memory on a
  real app works: the app's code reads back, 0.024 ms per 4 KiB. README rows and STATUS updated; docs_check PASS.

## Pointers
- Gen3D's report (read only): Gen3D's docs/research/LAZPY-TRY-1.md
- STATUS.md "Next" (ArgumentError, fresh_sd)

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 08:30, Guy: "Test and fix whats needed. When done tell 3DP and Gen3D agents that the tool is ready and
  that they can and need to use only it". Load at 08:30 was 34/19/10: timed runs wait for the quiet gate.
- The first three scene runs (09:03-09:07) said our core was 25% slower (400 against 535 fps); interleaved quiet
  repeats showed other sessions' load arriving mid-run. Judge a run by its load at the end too, and compare two
  cores with interleaved repeats, never one run each.
- The scene script and Gen3D's seed (a commercial game and save) stay in the session scratchpad, never in this repo.
