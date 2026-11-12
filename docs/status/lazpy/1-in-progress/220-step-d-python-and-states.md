---
id: laz-220
title: lazpy
order: 220
kind: step
parent: laz-200
page: The Python layer, savestates and starting a run from a saved state
hours: -
---
# Step D: the Python layer, savestates and starting a run from a saved state

## What it is
`python/libazahar/`, one worker process per instance, typed errors, savestates and state boot with the SD snapshot; pytest on the test app; the Gen3D mapping in USING.md. Gen3D starts its adapter here.

## Exit gate
The gate in `docs/PLAN.md` line 276 ("Phase D"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:276`
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- D1+D2 report (a8301022e123dfae3, 19:47), committed on step-d b24c436: make check, make, test-host (307,737 checks,
  0 failed); pytest -q (tests python folder, -m "not slow") 48 passed in 2.5 s (fake round trip 0.068 ms, 691,200-byte map
  copy 0.130 ms, SIGSEGV death to raise 0.107 s, hang heartbeat stop to raise 1.00 s at timeout=1); a venv `pip
  install -e .` imports `libazahar` 0.1.0.dev0; the real worker loads the dylib, passes the layout check and says
  hello without azh_open. Files: host/state.c (522), statemeta.c (314), tests/host/test_statemeta.c (198),
  pyproject.toml, python/libazahar/ (11 modules), tests/python/ (7 files). .gitignore: `*.egg-info/`.
  Blocker for D3, in C's api.c (sent to C's as-built review): azh_boot with a state calls azh__state_boot instead of
  boot_game, and boot_game is static, so nothing loads the app; D's azh__state_boot assumes the app is loaded (meta
  and app sha256 check, STATE_WARMUP_FRAMES=1 warm-up, restore). Fix: azh_boot runs boot_game(app), then
  azh__state_boot. Notes: statemeta.c stays pure (AZH_E_SAVESTATE for bad files, AZH_E_IO for I/O; state.c writes the
  reason); RunResult on guest exit uses absolute first/last frames; GuestError from a guest_error stop only on our
  core (stock: a RunResult, exit 11 raises); the worker takes the host path from LAZ_HOST. state.c's SD snapshot and
  restore are compiled only; D3 runs them. Lessons: -I implies -P (conftest inserts python/ and tests/);
  HostMap.close() swallows BufferError from live numpy views; the wait loop polls the pipe once after the worker
  exits so a last reply is not lost; fakeworker sidecars host.map.died / .stopped give exact delay times.
- For D3, from C's as-built review: after B1, azh_boot loads the app, sets BOOTED, then calls azh__state_boot
  (state.c:485-502 needs no edit; any state-boot failure leaves the instance DEAD; azhost --state uses the same
  path). azh__counters_set now writes the map: D must not call azh_map_set_counters itself. Stock-core guest
  errors come two ways (one or two error messages in one retro_run: a batch with AZH_STOP_GUEST_ERROR; the third:
  host exit 11); map both to one rule and write it in USING.md. azh_result.message holds only the stopping kind's
  message, cut to 255 bytes (the map's 1023-byte message with msg_seq, and host.log, have more). Messages during
  the drain (retro_serialize_size) set flags the next frame clears, so they are not reported as stops; compare
  msg_seq before and after to warn. px_frame is -1 during a raw copy. c3 through Python: bound 3.0 + max(1.0,
  5 * wall_s / frames) from batch 1. N6: D's integration tests exercise --stop-new.
- D3 interim (a8301022e123dfae3, forced hand-back at about 215k tokens, 20:04), work-in-progress commit on step-d
  c1e614e after main merged at 1cf3609: GuestError for stopped_by == "guest_error" on either core (.result set,
  Emulator stays open); exit 11 also GuestError (Emulator closed): the one rule for USING.md. save_state makes the
  state's parent folder. .gitignore has `*.egg-info/`. New tests: d_helpers.py (not in the brief's list),
  test_c_checks.py (10 passed alone with LAZ_REQUIRE_EMULATOR=1, incl. stop_new; a2 hid m=0 counts {0: 1, 1: 29},
  irrst m=1 {1: 6}, circle m=1 {1: 5}; c3 wall 3.00 s vs bound 4.00 s; b's touch offsets are in runs/d-cc.log),
  test_live_errors.py (never run), test_api.py and test_state.py (last run had at least one F, not read).
  State-boot timing, runs/d-pytest/state-times.txt: t_core_start=0.50 t_boot=6.83 t_state=1.68 ratio=0.247
  fixed_ratio=0.186 k=0 frame_total=6030 v_save=6027; `state load meta_ms=0.0 sha_ms=0.1 read_ms=0.2
  drain_ms=503.7 sd_ms=0.5 unserialize_ms=643.0 bytes=268966`. The restore works (counters matched); BOTH ratios
  fail the 10 % gate: the drain is a whole throwaway serialize (about 0.5 s), unserialize drains again inside the
  core, and t_boot is short because the seed's boot_frames=6000 runs fast. Nothing tuned (phase-2.md risk 3): Guy's
  call.
