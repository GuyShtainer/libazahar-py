---
id: laz-210
title: lazpy
order: 210
kind: step
parent: laz-200
page: Buttons, touch and the circle pad, frame-exact; stop rules and why a run stopped
hours: -
---
# Step C: buttons, touch and the circle pad, frame-exact; stop rules and why a run stopped

## What it is
Batches with input records, touch and circle pad, the SD log stop rule, stop reasons from the core's messages, the heartbeat and wall limit, SD seeding; host unit tests.

## Exit gate
The gate in `docs/PLAN.md` line 265 ("Phase C"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:265`
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- C1 report (acae9a26ca38daf7c, 19:38), committed on step-c 0651a8d: make check, make, test-host (307,673 checks, 0
  failed), test-version clean, no warnings. Float32 touch model: gy = y-1 only at y = 63, 125, 126, 127 (1280 points),
  gx = x. `azhost layout`: abi=2, 114 field rows (limit 160, static assert), sizes batch 3348, result 304, stats 240,
  layout 6452, map 695,296, shot 12; map version 2. Header changes beyond section 3, accepted by the main loop: A's
  `AZH_MSG_MAX 1024` renamed `AZH_LASTMSG_MAX` (azhost.h's `AZH_MSG_MAX` is 256); extra map offsets FRAME_TOTAL 1080,
  VBLANKS_TOTAL 1088, MSG_SEQ 1096, PID 1100, EXIT_CODE 1104; hostmap writers azh_map_set_counters, set_exit_code,
  sync, pixels, raw_begin, raw_end (set_message bumps msg_seq; pid at create; px_frame starts -1); azh_pure.h includes
  azhost.h; `azhost layout` already in azhost_main.c; tests/host/test_main.h added; crop.c in the test-host link.
  log.c already writes the core's line literally (A8 holds). The step-0 by-hand run was not done (C1's no-emulator
  rule won); moved to the start of C2. Lessons: a brief can't promise "headers differ from section 3: nothing" (name
  clashes and map-writer prototypes only show in code); list the hostmap prototypes in the plan; say whether a C1
  by-hand run is allowed. -ffp-contract=off plus a FLT_EVAL_METHOD static assert keep the touch model exact.
