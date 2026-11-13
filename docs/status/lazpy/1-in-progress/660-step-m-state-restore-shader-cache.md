---
id: laz-660
title: lazpy
order: 660
kind: step
parent: laz-600
page: Restoring a saved state crashed apps that draw 3D (Gen3D's V6 smoke)
hours: -
---
# Step M: restoring a state crashes on the first 3D draw (the shader-cache switch)

## What it is
Gen3D's V6 smoke on the final core 88cc6188: a state boot of its app succeeds, then the first `run` kills the
worker (signal 11, 4 of 4). Cause: loading a state shuts the core down and re-inits it, which makes a new Vulkan
renderer with no shader cache selected. The restore then asks the renderer to switch its cache to the running
program's id, and `PipelineCache::SwitchCache` returns early when the id equals its current one. A `.3dsx` has id 0,
the same as a new renderer's default, so the cache is never selected and the first programmable-shader draw reads
through a null pointer. This is upstream Azahar's bug: the stock 2126.2 core crashes the same way.

## Exit gate
Core patch 0011 (the early return also needs a selected cache). Red then green: the repro (boot, run 600, save,
state boot, run 300) crashes on the current core and passes on the patched one, and a test-app regression test
that draws with a programmable shader after a state restore does the same. Then a main build under a hold, the
V0b gates again, and Gen3D's smoke plus 3DPlatinum's chain on the new sha256 (V6).

## Evidence
none yet

## Pointers
- Plan section: `docs/plans/phase-v1.md:116` (V6); the core-build steps are V0b's.
- Review: none yet

## Lessons and notes
- 2026-11-13 12:41, Gen3D (3ds-toolkit-1c), verbatim except a game name replaced and scratchpad paths cut: "Gen3D V6
  smoke on core sha256 88cc6188cb499bf6e5f87c781526d9dcc4c2437d2c5ed31c4772afb3bec7fd0c (main 003eaec, Azahar
  2126.2-lazpy.2): FAIL. Restoring a saved state crashes the worker, 4 of 4 runs. What fails: save_state succeeds
  (0.67-0.81 s, k=0). A new Emulator(app, workdir, state=path) boots from it fine (\"state boot\" 1.75-1.79 s; host.log
  shows `state load meta_ms=0.0 sha_ms=2.3 read_ms=0.6 drain_ms=558.2 sd_ms=3.9 unserialize_ms=694.1 bytes=3922150`).
  Then the first run(300) kills the worker: `HostCrashed: the worker died (signal 11)`, worker.err `Unhandled
  EXC_BAD_ACCESS at pc 0x...d26674` (page offset 0x674 every time ...). Python stack: _host.py:60 call <-
  _worker.py:58 _op_run. It happens both on Gen3D's own menu (state at frame 600) and with [a GBA game] running in
  Gen3D (state at frame_total 8400). ... What works on this core: Boot 1.9 s. Memory: the 256 bytes at 0x00100000
  equal the ELF's .text. threads() lists 4 threads. Shots, touch and buttons drive Gen3D's menu into the game. Speed:
  Gen3D's menu 1664-2483 fps; [the GBA game] running inside Gen3D (boot screens, A taps) 400-509 fps at load 8-12.
  peak_rss 671 MB. The Pool 1-4 run waits until a state restore works: Gen3D's port plans to start every test from a
  state. Send me a fixed core's sha256 and I'll rerun the same scripts."
- 2026-11-13 12:42-12:47, main loop A/B (minimal repro in the session scratchpad: boot, run 600, save, state boot,
  run 300; Gen3D's app and seed read in place): final core 88cc6188 crash 3/3; the pre-0010 lazpy.2 core 3/3; the
  lazpy.1 core 3/3; the stock 2126.2 core 2/2. So neither patch 0010 nor the 1.0 changes caused it.
  The unstripped build of 88cc6188 names the frames: `ShaderDiskCache::UseProgrammableVertexShader+0x1d0`
  (`ldr x27, [x20, #0x780]`, `this` = the current disk cache) <- `RasterizerVulkan::AccelerateDrawBatch` <- PICA
  command list <- `GSP_GPU::TriggerCmdReqQueue`. With `citra_use_disk_shader_cache=disabled` even a normal boot
  crashes at the same pc (the GSP acquire path hits the same early return); with `citra_use_hw_shader=disabled` the
  state run still crashes, in the same disk-cache code. The restored run's log has no "Switching pipeline cache" line
  and the title id is 0 (the app is a `.3dsx`). Our own state tests miss it: the test app draws no programmable-
  shader frame after a restore.
