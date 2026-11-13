---
id: laz-510
title: lazpy
order: 510
kind: step
parent: laz-500
page: Core revision 2: tick seed option and thread registers for 3DPlatinum
hours: -
---
# Step K: core revision 2 (3DPlatinum's tick seed and thread registers)

## What it is
One core rebuild (2126.2-lazpy.2) carrying 3DPlatinum's two asks (A4: `citra_init_ticks_override` as an option;
A1: each guest thread's pc, lr and sp between batches) and the items queued for the next core revision (the macOS 15
header, patch 0008's comment, core/PIN-nokeys as the default pin). Built in its own worktree with a real dl/ (never
MAIN's build tree), on branch core-rev2; merged after v0.1.0 is tagged unless Guy rules otherwise.

## Exit gate
`docs/plans/phase-k.md` section 6 (written 2026-11-13, two opus reviews before work).

## Evidence
2026-11-13 12:34: merged into main (72f8d61, V0b step 4) and built on main from a fresh build folder (12:26-12:32,
pin core/PIN-nokeys with SRC_URL at v1.0.0, 003eaec). Gate 1 on main: build.inputs clean=yes, head 003eaec, 11
patches (0000-0010); otool minos 15.0; version suffix `-lazpy.2`; 4 lazpy_* exports; 0 "built for newer macOS
version" lines; `tests/gate_f2.py --ours ... --stock ... --only keyblob,symbols,version`: "gate_f2: 0 FAIL,
gate_c.failed 0". test_threads_live.py with `LAZ_CORE_OLD` (runs/core-lazpy1/): 8 passed, plus the stock-core test
with `LAZ_STOCK_CORE`: 1 passed. Fast pytest 244 passed; test-host 307973 checks, 0 failed. Core sha256
88cc6188cb499bf6e5f87c781526d9dcc4c2437d2c5ed31c4772afb3bec7fd0c, sent to Gen3D and 3DPlatinum for V6.

## Pointers
- Plan: `docs/plans/phase-k.md`
- Asks verbatim: item laz-500's notes.

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 10:28 and 10:42: reviews 1 and 2 saved (`docs/reviews/phase-k-review-1.md`, `docs/reviews/phase-k-review-2.md`);
  plan revision 2 answers both.
- Process slip, recorded honestly: the worktree seeding and the code edits started at 10:33, while review 2 still ran
  (the rule is two reviews, then execute). Nothing was committed or built before review 2 returned; its findings were
  applied to the edits (two of its blockers, the missing vendor/ headers and the two ABI tests, were already fixed).
- Patch method that worked: a scratch git repo with the six touched files from the unpacked source, one commit per
  patch, fixup commits squashed with `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash`, then a fresh apply of the
  whole stack at fuzz 0 compared byte for byte with the scratch tree. Git's diff aligns hunks differently from the
  original patches, so unchanged patches are kept as they are and changed ones are edited in place where small.
- 2026-11-13 10:48: the branch's host and Python with MAIN's lazpy.1 core: full pytest 150 passed, 9 skipped (the
  lazpy.2-only tests), at load about 30 (another session's gates). The stock core's `threads()` raised NeedsLazpyCore.
- 2026-11-13 10:51: configure-only first stopped on the cache check: cmake stores the minimum as
  `CMAKE_OSX_DEPLOYMENT_TARGET:UNINITIALIZED=15.0` (review 2's S4 said to take any type; fixed). The two patched files
  compiled alone (`make core_settings.cpp.o citra_libretro.cpp.o` in the build's src/citra_libretro) before the
  full build: a cheap check that saves an hour-long build from a C++ typo.
- 2026-11-13 11:03: the full build exited 0 (10:53-11:03). Gate 1 holds: build.inputs clean=yes, pin PIN-nokeys
  (drop LIBAZAHAR-PY-REMOVED.txt), patches 0000-0009, head d64aabb; otool minos 15.0; version '2126.2-lazpy.2'; nm
  shows the 4 lazpy_* exports; `tests/gate_f2.py --only keyblob,symbols,version`: "gate_f2: 0 FAIL, gate_c.failed 0",
  and 0 "built for newer macOS version" lines in build.log. MAIN's core is unchanged (Nov 13 01:06).
- 2026-11-13 11:04: gates 3 and 4 (tests/python/test_threads_live.py, 9 passed, load about 40): "k3: update_tick
  after 300 frames: {'0': 0, '1000000': 1000000, 'random': 388092194}; counters 1, 1"; "k4: 3 threads; app pid 0xb,
  main tid 1, stack 0x8000000..0x8008000" (main sp 0x08007ec8); states crossed lazpy.1 and lazpy.2 both ways.
  First try failed: the worktree's libazhost.dylib was built in the same minute as the options.c edit, so make kept
  it and the old allowed-list check refused '1000000'. A `make` fixed it. Lesson: rebuild the host right before a
  live gate (the 10:48 run of 150 passed was on that stale host; gate 2 reruns everything on a fresh one).
- 2026-11-13 by 11:06, 3DPlatinum (3ds-toolkit-f4), verbatim: "A1: PASS. 3DP.3dsx, 600 frames on an empty SD
  (stopped_by=frames, frames 600; LoadWarning load 54 on the machine). emu.threads() gave 3 threads, all pid 11. Each
  pc and lr maps to a real 3DP.elf symbol ... sps 0803f0a0, 080411a0, 08043448 (distinct stacks). No where.py
  comparison: our rule now forbids windowed runs beyond five planned comparison runs ... A4: not run yet. The repro
  needs the windowed route's count lines, which our comparison lane ... is producing right now."
- 2026-11-13 by 11:06, Gen3D (3ds-toolkit-1c): no live suite on libazahar-py yet; its timed GBA-game soak lane runs now
  (about 40 min, fails on any frame gap over 2 s), then a smoke on the candidate, then the Pool 1-4 run when quiet
  ("count Gen3D as 'not tested'" until then). Gate 2 is held for that lane (rule T): its runner waits for a flag the
  main loop sets on Gen3D's "lane done", then for the quiet-load gate. My gate 3/4 run (11:03-11:05) overlapped
  Gen3D's probe before its message came; Gen3D was told.
- 2026-11-13 11:13: gate 6 holds on the branch (docs_check 0 FAIL, map_check OK); NOTICES.md regenerated for lazpy.2
  (only the patch hashes and a 0009 row changed), branch commit 6eacf41.
- 2026-11-13 11:17: gate 2 in the worktree dropped on phase 6 review 2's hour-saving (that core is replaced by main's
  build; the full suite runs on the final core in phase 6's V7); its held runner was stopped before it ran anything.
  3DPlatinum's A4 moves to the final core (phase 6's V6). Step K closes with phase 6's V0b (merge, main build, gate 1
  and the live tests on main).
- 2026-11-13 by 11:28, 3DPlatinum (3ds-toolkit-f4), A4 on the worktree core, verbatim: "one headless trio had already
  run on it (11:16, 4 make targets, rc 0 each) with citra_init_ticks_type=Fixed + citra_init_ticks_override=1000. For
  your step K evidence: against the same trio on lazpy.1 (Fixed, no override) every count line is identical (120,
  156, 158 x3 lines) except the PICA readback line (edge-marked 1534881 vs 1534877, within our 1e-4 floor, a known
  jitter). Against the windowed route, all count lines match except one: our audio lead line (ndsp sink watermark
  minus vclock, ms). It is unchanged by the override (e.g. lead=91 headless vs 127 windowed, d_max 23 vs 21), so the
  tick seed does not close that gap. We've ruled it a cross-route timing line (masked across routes only)." It left
  the worktree (read only, nothing written). Its Platinum runners lane may run on main's lazpy.1: ask before the hold.
