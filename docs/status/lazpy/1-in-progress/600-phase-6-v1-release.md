---
id: laz-600
title: lazpy
order: 600
kind: phase
page: Version 1.0.0: every claim gated, a stable API promise, the first public release
hours: phase-6
---
# Phase 6: release v1.0.0

## What it is
Guy, 2026-11-13: "Ok i see why its not 1. Than do all the proper tests and builds to make it version 1". Close each
reason the release was 0.1 (untested poll-exact movie, provisional instance cap, the ABI promise, the macOS header,
no user confirmation), freeze the API under semantic versioning, and stage v1.0.0 as the first public release in
place of the never-published v0.1.0.

## Exit gate
`docs/plans/phase-v1.md` section 3, steps V0-V8 each at its gate; V9 waits on Guy.

## Evidence
none yet

## Pointers
- Plan: `docs/plans/phase-v1.md`
- Step K (V0): `docs/status/lazpy/5-done/510-step-k-core-rev-2.md`

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- 2026-11-13 10:58: plan revision 0 written; reviews 1 and 2 next.
- 2026-11-13 11:07: review 1 saved (`docs/reviews/phase-v1-review-1.md`); revision 1 answers it. Biggest changes:
  poll-exact movies leave 1.0 (no host call, no movie writer, the test app reads input once per frame); host and
  Python are one unit (the layout check refuses a mix); main's rebuild needs the PIN-nokeys URL moved to v1.0.0 and
  the nokeys tarball copied into dl/ first; the merge itself waits until Gen3D and 3DPlatinum run nothing.
- Guy, 2026-11-13 (during step K's gates): "Dont forget to use the gen3d and 3dp agents for real live testings" (V6).
- 2026-11-13 11:17: review 2 saved (`docs/reviews/phase-v1-review-2.md`); revision 2 answers it and is the plan
  work follows. The API review (V1, item laz-610) runs; 3DPlatinum was asked to leave the worktree before V1's edits.
- 2026-11-13 11:20, Gen3D (3ds-toolkit-1c), verbatim: "nothing in Gen3D uses main's libazahar-py right now. the GBA game's
  lane runs on the old Azahar app ... so you can merge and rebuild main whenever you like. The only cost is CPU load
  during our timed soak, which runs until about 11:55. A heavy build before then could add a frame gap. After that,
  build freely." So V0b's core build starts after 11:55.
- 2026-11-13 12:03: V1 is on the branch (64f5d18, item 610), under opus review. Step L's core patch (item 520) lands
  in `core/patches` before V0b's build, so V0b waits on the review's fixes and on step L's red-then-green repro.

- 2026-11-13 by 12:26, Gen3D, verbatim: "Gen3D is OK with the hold: nothing of ours runs on main's libazahar-py, and
  nothing new will start until you send \"hold released\" with the sha256. Our only jobs right now are host tests (no
  emulator). My smoke script already uses keyword arguments and wraps shot paths in Path, so the v1.0.0 changes
  shouldn't break it. I'll check section 20 before I run it."
- 2026-11-13 12:34: V0b done. Hold 12:24-12:34 (both projects confirmed clear). Steps: 2 lazpy.1 core kept in
  runs/core-lazpy1/; 3 the source tarball copied (sha256 f7a70044…); 4 merge 72f8d61, make, fast pytest 244 passed;
  5 PIN-nokeys SRC_URL at v1.0.0 (003eaec), so no core/ or build-core.sh edit or run on main from here; 6 old build
  folder moved to runs/core-lazpy1/build-old, full build 12:26-12:32; 7 gates (item 510's Evidence) and the stencil
  test 0 bad of 90; 8 hold released with the sha256 88cc6188… to both. The worktree ../libazahar-py-k is removed (its
  runs/ and build logs kept in runs/wt-k/); branch core-rev2 stays at e28e4c2. The test app's sha256 is now
  ba106998… (the stencil self-test was added), not 53b699e8…; V8's env -i rebuild compares against ba106998….
  V6 started: 3DPlatinum at 12:35 (A3 self-test, then the chain with A4); Gen3D asked for the smoke and Pool 1-4 run.
- 2026-11-13 12:38: V4 done except README's measured numbers (V3) and NOTICES.md: version 1.0.0 (pyproject,
  `__version__`), fetch.sh REL_TAG v1.0.0 and the lazpy.2 zip with LAZPY_CORE_SHA and TESTAPP_SHA `TBD` (pin_set
  refuses TBD), STATUS.md for 1.0 (three new What-works lines, the promise, poll-exact not in 1.0), README's version
  line, USING's four poll-exact places, runners.md, `docs/release-notes/v1.0.0.md` (notes_wording_findings: []),
  v0.1.0 notes deleted (that deletion landed in 232f003 by accident: the agent's `git rm` was staged when the main
  loop amended; lesson: an agent's `git rm` on shared main stages, so check `--cached --stat` before every amend).
  NOTICES.md is regenerated in V8 with the full mknotices inputs (`docs/map/runners.md`), from main's build.
- 2026-11-13 13:11: V6's first Gen3D smoke failed (state restore, item laz-660); patch 0011 fixed it, and main's
  core is now 64026f4a… (4e830e5), replacing 88cc6188 as the v1.0.0 candidate. V6 restarts on it in both projects;
  V8's fetch.sh pin and release zip use the new sha256. The 88cc6188 core is kept in runs/core-88cc/.
- 2026-11-13 by 13:14, 3DPlatinum, verbatim: "V6 on the final core, sha256
  64026f4afa2036a552345ac4b73c95ebbf27190ad8590a1cfd70f6b5ab1893cf: A3 self-test PASS, 10 of 10, finished 13:13.
  Bundled MoltenVK, no overrides. Every launch gave: stencil 0x80 count 8000 of 8000, clear 00, \"selftest ds:
  PASS\", make emu-pica-replay-port rc 0, and edge band worst 54.65% (the same as on 88cc6188 and on the old
  MoltenVK). The whole chain with records starts now on instance p, and its result plus A4 come when it ends."
  Gen3D's smoke on 64026f4a: PASS (verbatim in item 660); its Pool 1-4 waits for 3DPlatinum's chain to end.
- 2026-11-13 13:13: V8's NOTICES step done early on main's 64026f4a build: tools/mknotices.py with the runners.md
  inputs; the notice sentence is now derived from the patches (0007, 0008, 0010 and 0011 add their own notices;
  the hand text named only 0010 and 0011). Every file any patch changes carries a notice (9 of 9).
- 2026-11-13 13:16, for V8's legal re-audit: three commits add a game name, removed from the tree by e54e38f:
  1748f65 (`docs/research/spike-2-real-scene.md` line 58, 2026-11-12; touches Guy's G9 "say nothing" default),
  9c5f959 and a41f196 (status notes quoting Gen3D). Nothing is pushed; the audit rules whether history needs a
  rewrite (as G8c did) before the first push.
- 2026-11-13 13:38, V3 prepared (not run): the scene script is in the session scratchpad (scene/v3scene.py), Gen3D's
  build pinned by sha256 f2f80aee…, the step J seed. One change from the plan: the guest rate comes from Gen3D's
  perf.csv (one row per guest second, its t_ms column is guest time), not voxel.log's flip lines, which appear only
  when the top screen changes (12 in step J's 36000-frame run), too few for a rate. check_ok: guest seconds per
  wall second within 10 % of host fps / 59.831, world=6 (ready) and top=0 (the 3D world) in the perf rows at the
  window's start and end, the batch stopped by its wall limit; v3start/v3end shots are kept for a look. A ps sampler
  (every 10 s) records other processes over 50 % CPU or named like builds and emulators. Rows: ours 1, stock 1, ours
  2, 3, 4; 60 s windows. It waits for both V6 runs to end and a load under 6.
- 2026-11-13 15:01, V6: 3DPlatinum PASS on 64026f4a… (its whole chain headless, 72 steps PASS, its only failures its
  own link step; A4's 5 pairs differ only in the game ELF's sha, a rebuilt ELF in its fresh tree; verbatim in
  laz-660's notes). Gen3D's smoke passed at 13:10; its Pool 1-4 run started on our go at 15:01 (load 1.96).
- 2026-11-13 15:18, V6: 3DPlatinum's A4 caveat closed, verbatim: "A4 on the final core (64026f4a...): EQUAL. We reran
  the windowed trio headless on the very game ELF the windowed records used (sha 44d17faa...). route_equal gives
  \"EQUAL (5 A records, 5 B records, 0 one-sided excused)\", with only the audio-lead timing line masked by design.
  All four targets rc 0, no hold, no SlotTimeout. With the chain result I sent at 15:00, V6 is a pass from our
  side." V6 now waits only on Gen3D's Pool 1-4.
- 2026-11-13 17:19, V6: Gen3D (3ds-toolkit-1c) Pool 1-4, verbatim except a game name replaced: "Gen3D Pool 1-4 run on
  core 64026f4a: PASS. My emulator work is done; the machine is yours for the speed table. Setup:
  Gen3D-flipdev.3dsx with [a GBA game] running inside it; every job restored from the state saved in the V6 smoke,
  then 3600 frames with A taps; LAZ_MAX_INSTANCES=4; 1-min load 5.5 before (3ds-toolkit-11 told me their lane
  starts no Mac emulator runs before 17:30). n=1: 467 fps per instance, 467 total; wall 9.6 s including boot;
  peak_rss 1551 MB. n=2: 431, 388 per instance, 818 total; wall 12.6 s; peak_rss max 1560 MB. n=3: 402, 450, 448
  per instance, 1300 total; wall 12.9 s; peak_rss max 1220 MB. n=4: 454, 454, 445, 404 per instance, 1757 total;
  wall 13.1 s; peak_rss max 1345 MB; load 6.3 at the end. Every job finished with no error or crash. Note: peak_rss
  for a restored instance (1.2-1.56 GB) is about twice the cold-boot smoke's 732 MB." V6 is done: both projects
  pass on 64026f4a…. (The restored-instance memory is a note for USING's memory line at V3, not a blocker.)
