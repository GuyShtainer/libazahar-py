---
id: laz-130
title: lazpy
order: 130
kind: step
parent: laz-100
page: A small test app built from source, so tests need no commercial game
hours: -
---
# Step B: a small test app built from source, so tests need no commercial game

## What it is
Our own 3DS test app (libctru, GPLv3): reads a seeded control file before its first frame to pick a mode, draws corner markers, logs one line per frame to the SD card and the debug channel.

## Exit gate
The gate in `docs/PLAN.md` line 255 ("Phase B"), run headless on this Mac with a pass/fail answer.

## Evidence
- 2026-11-12 19:26, step-b 58bf72d, merged to main: in the int-1 fresh clone `RUNNER=azhost tests/gate-b.sh` 14/14
  PASS (offset 7, vjumps 0, markers exact in 2D, 3D and after busy boot, four events), zero build warnings; also 14/14
  on fe2 from a fresh tree. As-built review and re-check: mergeable.

## Pointers
- Plan section: `docs/PLAN.md:255`
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Builder report (ab76e8c1f445db1b3, 2026-11-12 18:57, worktree ../libazahar-py-b, uncommitted): gate-b with
  RUNNER=fe2 14/14 PASS, exit 0 (`runs/gate-b-2.txt` there); RUNNER=azhost written, not run (no A yet). Files:
  testapp/Makefile, README.md, source/ (main.c, control, record, draw2d, font, scene3d, sdlog .c/.h, vshader.v.pica),
  testapp/tests/host_test.c, tests/check_testapp.py (202 lines), tests/gate-b.sh (104, ShellCheck clean). Boot offset
  6-7 frames; vjumps 0; 3D markers exact under the strict check; busy boot spin cap never hit
  (`booted f=90 v=96`); .3dsx 150,928 bytes; longest function about 45 lines.
  .gitignore: `*.elf *.smdh *.shbin *.lst *.map`. Map lines: code.md `testapp/`; tools.md `tests/gate-b.sh`,
  `tests/check_testapp.py` (exports `read_png_rgba(path)`); runners.md `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make -C testapp`
  and `tests/gate-b.sh` (`RUNNER=azhost` after A).
  Lessons: fe2 runs unthrottled (600 frames in under a second; a 15 s run logs 20k-70k lines, up to 5 MB); in 3D `v`
  equals `f` (C3D_FrameCounter), so `v` restarts when citro3d starts; svcBreak lets the guest run on; returning from
  main after gfxExit() ends the log with the exit line; the SMDH uses libctru's zlib-licensed default_icon.png (for
  the licence audit); shell traps: `&&`-chained `cat <<EOF` silently skips on an earlier failure, a global `name` in a
  helper clobbers the caller's loop variable. Not exercised: gate-b's azhost branch, the split-PNG markers form,
  svcOutputDebugString forwarding.
- Fix round (19:18): B-X1, B-S1..S4, B-N1..N4 done. Changed: tests/gate-b.sh, tests/check_testapp.py,
  testapp/source/ main.c, scene3d.c/.h, control.c, record.c, font.c, sdlog.c. gate-b 14/14 PASS from a fresh tree
  with RUNNER=fe2, and 14/14 with RUNNER=azhost (A's build copied in, host/ symlinked, all removed after; azhost boot
  offset 12, 588 log lines for 600 frames). Lessons: azhost reads host/options-default.txt relative to the working
  directory and needs the dylib beside it (standalone runs without host/ fail with IOError); the new exit-code check
  caught a broken first run as exit 6; asserts stay on (no -DNDEBUG); scene3d_begin() is void (SYNCDRAW without
  NONBLOCK always returns true); fe2's log checks need --runs from the DONE line.
