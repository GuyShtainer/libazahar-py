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
Done 2026-11-13 15:01: both projects pass on core 64026f4a… (V6 notes below: Gen3D's smoke restores and draws;
3DPlatinum's whole chain PASS, its only failures its own link step). Our side done 2026-11-13 13:10: main 4e830e5 (patch 0011 sha256 64dc6cbf…, branch
commit aa29901), built 13:02-13:08 from a fresh build folder; core sha256
64026f4afa2036a552345ac4b73c95ebbf27190ad8590a1cfd70f6b5ab1893cf. Gates (session scratchpad v0c-gates.sh):
build.inputs clean=yes, head 4e830e5, 12 patches; minos 15.0; `lazpy.2` in the strings; 4 lazpy_* exports; 0
"built for newer macOS version" lines; gate_f2 "0 FAIL, gate_c.failed 0"; fast pytest 244 passed;
test_threads_live.py with LAZ_CORE_OLD and LAZ_STOCK_CORE 9 passed; `test_state_3d.py` 2 passed (red on 88cc6188);
test_state.py -m slow 3 passed; test_stencil_live.py with 10 launches 1 passed; Gen3D's restore repro 3 of 3 ok.
The test app is unchanged (ba106998…). Review: `docs/reviews/patch-0011-review.md`.

## Pointers
- Plan section: `docs/plans/phase-v1.md:116` (V6); the core-build steps are V0b's.
- Review: `docs/reviews/patch-0011-review.md`

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
- 2026-11-13 12:51-12:59: test build of patch 0011 in the worktree ../libazahar-py-m (branch core-rev3; its own
  unpack and build-core/, the nokeys tarball copied in, dl/moltenvk and vendor/ from MAIN), 3DPlatinum's "build
  ok, go ahead now" first. 12 patches, 0 rejects; core sha256 a548c03c…, built from the first text of 0011
  (sha256 17798328…). The final 0011 (9ea5c7df…) only adds the "Modified by libazahar-py" notice line; main's
  gated build uses it. New test `tests/python/test_state_3d.py` (the test app's `draw=3d`, run 300, save, state
  boot, run 300; two trials): red on 88cc6188, 2 of 2 HostCrashed signal 11, same 0x674 page offset as Gen3D's.
- 2026-11-13 13:00: green on the test build a548c03c…: `test_state_3d.py` 2 passed, Gen3D's minimal repro 3 of 3
  ok (frames 300 each). Opus review (af7ecbcfd68c8532d, `docs/reviews/patch-0011-review.md`): ship with changes;
  done: the driver-cache save only from a selected cache (a state load wiped the saved driver cache), both paths
  in the comments, wrapped under 100 columns, core/README rows for 0010 and 0011. Final 0011 sha256 64dc6cbf…,
  applies to pristine source with no fuzz. Branch commit aa29901, merged into main 4e830e5.
- 2026-11-13 13:01-13:02: hold. 3DPlatinum: "(a). Our chain was stopped at 13:01, during host tests, before any
  emulator run, and nothing of ours now uses main's build-core core. Hold and build." Gen3D idle since 12:50
  ("Main's core stays idle on our side"). The 88cc6188 core, its build.inputs and its unstripped build folder are
  kept in runs/core-88cc/. Main's fresh build started 13:02:29.
- 2026-11-13 13:10: hold released with the sha256 64026f4a… to both. 3DPlatinum, verbatim: "received. I checked the
  sha256 on disk and it is 64026f4afa2036a552345ac4b73c95ebbf27190ad8590a1cfd70f6b5ab1893cf. The A3 self-test (10
  launches) started at 13:10, and the whole chain with records follows it in the same tree." The worktree
  ../libazahar-py-m is removed (its build logs in runs/wt-m/); branch core-rev3 stays at aa29901 (merged).
  The release notes say the fix in one line; STATUS.md gets its works line when this item closes.
- 2026-11-13 by 13:12, Gen3D, verbatim except a game name replaced and a path cut: "Gen3D V6 smoke on core 64026f4a
  (main 4e830e5): PASS, including the restore with [a GBA game] running in Gen3D. app Gen3D-flipdev.3dsx (Gen3D
  main 752b09d build), script lazgame.py ... game: 3600 frames wall=10.1 s fps=356.4 (machine load 27.5 on 12 cores
  during the run: your LoadWarning fired, 3DPlatinum's chain was running, so this speed is not a quiet-machine
  number; the old core's quiet run was 400-509); stats: peak_rss=732 MB, core Azahar 2126.2-lazpy.2; save_state
  1.14 s, k=0, frame_total=8400; state boot 1.80 s; restored run ok (300 frames); its top shot 300 frames on is
  byte-identical to the original run's. The Pool 1-4 instance run waits for a quiet machine (rule T)."
- 2026-11-13 15:01, 3DPlatinum (3ds-toolkit-f4), verbatim: "V6 on the final core (sha256
  64026f4afa2036a552345ac4b73c95ebbf27190ad8590a1cfd70f6b5ab1893cf): PASS from our side, with one A4 caveat. The
  whole [3DPlatinum] chain ran headless with records (instance p, about 35 min for the first full pass, then resumed
  pieces). It reached CHAIN-DONE. 72 steps PASS, including every graphics-readback gate (pica-replay-port,
  pica-replay, hwcheck, hw-kit-dryrun), the two hwcheck mutants failing as planted, and the sound mix and its
  mutant. Our only two failures are our own link error (a missing hook in our port, our step pt-181), not the
  library. F2: 54 headless run lines, all stopped_by=guest_exited; 100 records, 93 rc 0, 7 rc 1, all planted. A4
  route_equal against the windowed trio: 5 pairs. Each differs only in the [build]'s sha, because our fresh tree
  rebuilt the [build] while the windowed records used the main checkout's. rc, framebuffer and file hashes and count
  lines are equal (the two timing lines are masked by design). So it is not a library difference. Our review
  decides whether we rerun the trio on the same [build]; I'll send that line if we do. Host tests on the client: 42/0."
  (Verbatim except "[3DPlatinum]" for the project's short name and "[build]" for its words for its own binary.)
