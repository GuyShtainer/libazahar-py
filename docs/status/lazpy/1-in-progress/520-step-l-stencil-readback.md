---
id: laz-520
title: lazpy
order: 520
kind: step
parent: laz-500
page: Depth-stencil readback gives wrong stencil values on first use (3DPlatinum's ask)
hours: -
---
# Step L: D24S8 stencil readback on the Vulkan route (3DPlatinum's A3 rev b)

## What it is
On our core (Vulkan via MoltenVK), copying a D24S8 depth-stencil buffer back to guest memory returns exact depth but
wrong stencil values on first use, different from launch to launch. Azahar's windowed 2125.1.2 passes the same
checks. It blocks 3DPlatinum's test-migration gate, and a renderer result that changes between runs undercuts 1.0's
"exact repeats" claim, so it is weighed as a 1.0 item.

## Exit gate
Our own test-app repro (a stencil-writing quad read back through a GX copy) gives the exact counts on 10 launches in
a row on our core, and 3DPlatinum's self-test passes on the final core. The plan line is written once the cause is
known (the investigation's report).
Plan (2026-11-13 12:03): the fix is core patch 0010 (the missing first-use barrier stages,
`docs/research/stencil-readback.md` "Proposed patch"), proven by our test-app repro red on the unpatched core and
green on the patched one (10 launches each), before V0b's main build; briefs `docs/plans/stencil-briefs.md`.

## Evidence
none yet

## Pointers
- Ask verbatim: the notes below.
- Report: `docs/research/stencil-readback.md`. Briefs: `docs/plans/stencil-briefs.md`.

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 by 11:51, 3DPlatinum (3ds-toolkit-f4), verbatim: "ask A3 rev b (it now blocks our test-migration exit
  gate). On lazpy.1 (2126.2, Vulkan via MoltenVK, resolution 1), reading back a D24S8 depth-stencil buffer to guest
  memory with a GX TextureCopy returns the right depth but the wrong stencil, and the wrong values change between
  launches with identical guest input. A self-test clears the buffer to depth fffffe and stencil 00, draws one opaque
  quad covering 100x80 px that writes stencil 0x80, then copies the buffer back. - One launch: 8000 px with stencil
  0x80, clear stencil 00 (correct). - Two other launches: 480 px (bbox 40..127 x 40..109) and 240 px (bbox 48..79 x
  80..109), with clear stencil ff. - In all three the depth codes are exact (4001ff inside, fffffe at the clear). A
  second app's check reads stencil ff where 0x81 is written and 0x88 where 0x89 is written. Later readbacks in the
  same process pass. Windowed Azahar 2125.1.2 (also Vulkan, same options) passed every one of these checks exactly.
  ... Questions: is the stencil aspect of a D24S8 surface kept through the memory fill (clear) and the DepthToBuffer
  download on MoltenVK? Is it a first-use or ordering issue (barrier, StencilView)? Does citra_graphics_api=Software
  (if the core takes it) give 8000 / 00 as a diagnostic? This joins the earlier readback note (the edge-marked count
  jitter, 28 px in 1.53 M), likely the same path."
- Their repro is in their tree (make targets that write there); we never write there, so our own test app gets a
  repro. Told them the core takes `citra_graphics_api=Software` (the host handles software frames) as a diagnostic.
- 2026-11-13 by 11:56, 3DPlatinum, verbatim: "With citra_graphics_api=Software in place of the Vulkan line, all 3 launches
  of our self-test died before the guest ran: stopped_by=error frames=0 error=\"BootError: the core did not ask for a
  Vulkan render context\"." My earlier answer was wrong: I checked that the core lists Software and that the host
  copies software frames, not that boot refuses a core with no Vulkan context. Lesson: before offering a route, check
  the boot path end to end. No software boot path is added for this; the repro is our test app.
- 2026-11-13 12:01: the investigation reported (saved verbatim as `docs/research/stencil-readback.md`). Likely cause:
  the first fill-clear of a fresh depth-stencil surface has no barrier to the draw's stencil LOAD (and a transfer
  write has none to the compute readback); the renderer code is the same as 2125.1.2, but MoltenVK 1.4.2 (ours)
  uses Metal heaps by default while the windowed 2125.1.2 ships 1.2.9, whose tracked resources hid the gap.
- 2026-11-13 by 12:03: two sonnet agents in the worktree (repro a3f2709cf168b11c4: test-app self-test and
  tests/python/test_stencil_live.py; patch a7a04c6135194c45c: core/patches/0010-lazpy-ds-barriers.patch and its
  NOTICES row, no build). 3DPlatinum asked to run experiment 2 (`MVK_CONFIG_USE_MTLHEAP=0`) and optionally 1
  (MoltenVK 1.2.9 through `LAZ_MVK`) on its self-test.

- 2026-11-13 12:05: patch agent done: core/patches/0010-lazpy-ds-barriers.patch (sha256 7a443f32…) in the worktree,
  every cited line right for 2126.2, 0000-0010 apply with `--fuzz 0`, no rejects; NOTICES row added. Not built yet
  (the build waits for the repro's red counts on the unpatched core). The `type != Texture` condition also widens
  color surfaces' first-use barriers (the same gap, cause 4); kept as the report wrote it.
- 2026-11-13 12:08: repro agent done (branch commit 39aff14 with the patch). On the unpatched lazpy.2 core, N=10 per
  variant: a (first use) bad 1/10, d (second readback, same process) bad 4/10, b (dummy draw first) bad 5/10; then
  N=30: a 0/30, b 0/30, d 7/30. So it is not first-use only (the report expected b and d always to pass): the
  readback's transfer-to-compute gap (cause 2) fits d. Bad shapes: stencil ff everywhere with depth partly stale
  (n80=0 nff=16384 dbad=10368..16384), or a tile mix with exact depth (n80=3952 n00=5264 nff=7168). Good line:
  `n80=8000 n00=8384 nff=0 nother=0 bbox=10,20,109,99 dq=8000 dbad=0`. Because the rate swings, the pass gate is 0
  bad across a, b and d at N=30 or more (`LAZ_STENCIL_RUNS=30`), not N=10. The unpatched core is kept in the
  worktree's runs/stencil/core-unpatched/ (sha256 8f72e75d…) for A/B.
- 2026-11-13 by 12:10, 3DPlatinum, verbatim: "A3 results (stencil readback, 10 fresh headless launches per setting,
  make emu-pica-replay-port, instance r, finished 12:08): the old MoltenVK fixes it every time; turning heaps off
  does not. LAZ_MVK = the windowed app's libMoltenVK 1.2.9: 10 of 10 exact (stencil 0x80 count 8000 of 8000, clear
  00, rc 0 on every launch). MVK_CONFIG_USE_MTLHEAP=0 on the bundled 1.4.2: 2 of 10 exact. The other 8: counts 0 (6
  launches), 288 and 64, with clear reading ff. rc 2 on all 10 (on the two exact launches, self-test A passed but the
  run still failed elsewhere: \"selftest ds: FAIL\" and pica_replay FAIL, edge band worst 31.83%). ... heap0 1-10
  counts: 0, 0, 288, 0, 8000, 0, 0, 64, 0, 8000 (clear ff except launches 5 and 10, which read 00); mvk129 1-10
  counts: 8000 x10 (clear 00 x10). So the heap setting alone is not the trigger. Something else that changed between
  1.2.9 and 1.4.2 is."
- So: the MoltenVK version is confirmed as the trigger (experiment 1), the heap default is not (experiment 2). If
  patch 0010 does not reach 0 bad at N=30, the fallback is our own A/B with MoltenVK 1.2.9 through `LAZ_MVK` on the
  test app, then a choice between more barrier work and pinning an older MoltenVK in tools/fetch.sh.
- 2026-11-13 12:14: patched core (worktree, 0000-0010, incremental build 12:08-12:09, sha256 f89d34492df6dd45…)
  passes our repro: N=30 per variant at 12:10, 0 bad of 90; then an A/B back to back (12:12-12:14): unpatched a 1/30,
  b 0/30, d 4/30 bad; patched 0/30 each. Totals: unpatched 22 bad of 210 readbacks, patched 0 of 180. Our half of
  the exit gate is met on the worktree core; it is rerun on main's final core in V7, and 3DPlatinum's self-test on
  that core (V6) is the other half. 3DPlatinum was offered a preview run on the worktree core.
- 2026-11-13 by 12:16, 3DPlatinum, verbatim: "I'll pass on the preview run, though. This session's standing rule is no
  more runs on the libazahar-py-k tree, and its core counts. I'll run the same self-test the first time main's v1.0.0
  core lands: 10 fresh headless launches on the bundled MoltenVK, no overrides. I'll report the stencil line,
  \"selftest ds\" and pica_replay's edge band, plus the suite and A4. Send the sha256 when it's built. Note: a Platinum
  chain lane now runs headless on instance p (started 12:14). Before any 30-minute hold, tell me first and I'll say
  when it's clear."
