---
id: laz-120
title: lazpy
order: 120
kind: step
parent: laz-100
page: The host library: builds from a fresh clone, boots an app, screenshots both screens
hours: -
---
# Step A: the host library: builds from a fresh clone, boots an app, screenshots both screens

## What it is
The C host library split from the prototypes (fe2.c, fe3.c) into small files, with every return value checked, the option profile, the version check and boot-failure detection; `libazhost.dylib` and the `azhost` command.

## Exit gate
The gate in `docs/PLAN.md` line 241 ("Phase A"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:241`
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Builder report (a4e8c6931d1122bf4, 2026-11-12 18:59, worktree ../libazahar-py-a, uncommitted): gate-a 8/8 PASS on
  Gen3D's .3dsx, exit 0; planted red (expect 401x240) printed FAIL 3. `make check` (analyzer, -analyzer-werror) clean,
  0 build warnings, shellcheck clean. Files: host/ azhost.h, azh_internal.h, pins.h, azh_pure.h, version.c, crop.c,
  png.c, core.c, env.c, options.c, vk.c (555 lines, largest), frame.c, hostmap.c, log.c, api.c, run.c, azhost_main.c,
  libazhost.exports, options-default.txt (32 keys); Makefile; tests/test_version.c; tests/gate-a.sh (83 lines).
  600 idle-menu frames in 1.7 s at load ~35 (not a speed claim). Boot errors: missing file "Failed to obtain loader
  for the specified ROM.", text file "Failed to load ROM!", both exit 3. abi_layout: batch 3344, result 40, stats 240,
  layout 48, map 695,296, heartbeat offset 16.
  Deviations: (1) the typedef and the function can't both be `azh_stats`: struct is `struct azh_stats` (typedef
  `azh_stats_t`), function `int azh_stats(struct azh_stats *)`, layout unchanged; Phase 2's plan should say so.
  (2) host/azh_pure.h added (prototypes of the pure files). (3) crop.c is rectangles only (`azh_crop_rects`); the PNG
  writer takes a stride; a copy for raw shots is C's. (4) vendor/ copied in the worktree (`.gitignore` `vendor/`
  doesn't match a symlink); the gate symlinks inside its copy. (5) vk.c sets MVK_CONFIG_LOG_LEVEL=1 unless set.
  Core facts: no `create_instance` (negotiation v2, `create_device` only, the host makes the instance); NULL features
  works; image R8G8B8A8, no swap; readback buffer 400x480 = 768,000 bytes from the first frame; the first retro_run
  gives a valid HW frame; SET_MEMORY_MAPS once with 2 descriptors in context_reset; av_info base 400x480, max
  7200x4800, 60 fps; close runs unload and deinit cleanly; core and MoltenVK never dlclose'd.
  .gitignore: `*.plist *.dSYM/`. runners.md: `make check && make && make test-version`; `build/azhost run <app.3dsx>
  --sys runs/x/sys --out runs/x/out --frames 600 --shot 300,600`; `tests/gate-a.sh build/testapp.3dsx`. code.md:
  `host/`, top-level `Makefile` (check, test-version, testapp delegates to testapp/), `tests/`. tools.md:
  `tests/gate-a.sh <app.3dsx>` (8 checks, temp fresh copy, KEEP=1 keeps it).
  Lessons: DeviceWaitIdle under the queue mutex before the readback copy held; a text file named .3dsx fails via
  SET_MESSAGE in context_reset, a missing file in retro_load_game; fetch.sh is not executable (gate runs `sh
  tools/fetch.sh`); `.gitignore` dir patterns don't match symlinks, so symlink dl/* children, not dl/; host.log's 32
  option lines are counted with -ge 32, so our core's extra keys pass.
- Fix round (19:17): A-X1, A-X2, A-S1..S5, A-N1, A-N2, A-N4 done; A-N3 skipped (review: UsageError exit 2 is fine for
  Phase 1). Changed: host/log.c, api.c, vk.c, core.c, frame.c, run.c, version.c, azhost_main.c, tests/gate-a.sh.
  gate-a 8/8 in the worktree and twice in a scratch clone with vendor a symlink (MAIN's vendor/ untouched);
  `make check` clean; shellcheck clean. The `%` guest line was not run through the new log path (code change only).
  A second azh_open returns AZH_E_ORDER (flag set only after a successful open); the MoltenVK log-level setenv is at
  the start of open_steps in api.c and logged. Lessons: BSD grep has no `\|` in basic regex (use grep -zvE on NUL
  lists); a clone lists a symlinked vendor as untracked, so copy gates exclude it and use ln -sfn; setenv before the
  core makes threads.
