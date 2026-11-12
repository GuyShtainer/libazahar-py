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
- C2+C3 report (acae9a26ca38daf7c, 19:46, worktree ../libazahar-py-c, uncommitted after C1): `gate_c: 28 passed, 0
  failed`, rc 0, first full run, no FAIL slow, no build wait (build.exit already 0); planted red (`--only a
  --plant-red`) fails a1/a2 with negative offsets, rc 1. make check, make, test-host (307,679 checks, 0 failed),
  test-version clean. Measured: buttons (hid) land +0 or +1 host frames (counts {0: 1, 1: 29}); ZL/ZR (irrst) +1 for
  all 6; circle +1 for all 5; touch +2 for all 40 with the exact float32 values; c = 3 at every batch end (c_min 3);
  SD stop delay 3 frames at every 30, 0 at every 1; wall-limit stop 3.0 s (bound 4.0); debug-text stop on the stock
  core exits 7 NeedsLazpyCore; RAW shot pixels equal the PNGs (d4); break stops at frame 128 (break v=125) and the
  guest runs on; exit rc 10, map frame_total 214 (exit v=205), message `Fatal Error encountered (16): ` (empty body).
  Real status-14 text holds `Exception Type: Break` (the map keeps 1023 bytes). About 1000 fps on the test app; the
  gate takes about 2 min. Files: edited Makefile, host/api.c, azhost_main.c (660 lines), env.c, log.c, run.c,
  tests/host/messages.txt; new tests/checks_c.py, gate_c.py, testapp_log.py. Runners: `make test-host`; `build/azhost
  run <app> ... --inputs f --stop-file REL --stop-text T --frames N[,N2] [--raw-shot F]`; `build/azhost layout`;
  python3 -I tests/gate_c.py [--only a,b]. No .gitignore lines.
  Deviations for the main loop: (1) three shared symbols declared locally in two .c files, not in the frozen
  azh_internal.h (`extern azh_msgstate azh_msgs`, `azh_run_batch_inputs`, `azh_run_raw_shot`); (2) no per-frame max
  in azh_result, so azhost prints wall_ms_mean and c3's bound is 3.0 s + max(1.0 s, 5 x batch 1's mean frame);
  (3) azhost links build/obj/sdcopy.o directly (azh__copy_tree not exported); (4) gate ids a2.N.hid / a2.N.irrst;
  (5) a frame asked for PNG and RAW reads back twice (pixels equal); (6) the thread-check assert is armed only inside
  retro_run; (7) one message per run, stronger kind wins; (8) a guest exit or error ends azhost with 10 or 11 and no
  later batches, a break continues. Not exercised: our core's debug-text stop and AZH_ACT_EXITED path.
  Lessons: input jitter far below the brief's fear; the 90 % rule is tight for irrst (6 changes); list cross-file
  state (batch inputs, message state) in the frozen prototypes next time; c3 wants a per-frame max wall time.
- As-built review (a9e8f589eeba79788, opus; docs/reviews/phase-2-c-as-built.md): mergeable after B1 and S1-S4.
  B1 api.c azh_boot: always boot_game, phase BOOTED, then azh__state_boot (DEAD on failure, no fall back to OPEN).
  S1 run.c an SD read error ends the batch; S2 azhost load_inputs rejects bad tokens, overflow, an 8th field; S3
  azh__counters_set writes the map; S4 gate_c kills its child on SIGTERM. All eight builder deviations accepted
  (deviation 1: the local extern and prototypes move into host/azh_internal.h). N1 (dbg_text race, our core only)
  goes to F2. Fix list sent to C's builder 19:56 with B1, S1-S4, deviation 1, N2, N3, N5.
