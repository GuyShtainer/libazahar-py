# Phase 1, step B: the test app (item laz-130)

Opus step plan, 2026-11-12, **draft for Phase 1's two opus review loops. Nobody builds from it until the reviews
pass and the main loop launches the step.** Index: `docs/plans/phase-1.md`. For one sonnet builder in its own git
worktree. It refines `docs/PLAN.md`'s "Phase B" paragraph of section 3; where they disagree on a goal, PLAN.md wins
and the builder stops and reports.

Builder reads first: `docs/map/rules.md`, PLAN.md section 3 "Phase B" and 2.2 (the frame layout and stop reasons
the app must exercise), `docs/research/spike-1-headless-core.md` (the emulated SD folder), `~/.claude/c-golden-rules.md`,
`~/.claude/shell-golden-rules.md`, `~/.claude/python-golden-rules.md`.

## 1. Goal and gate

Goal: `build/testapp.3dsx`, our own small 3DS homebrew app (libctru, GPLv3, our own glyphs and shader, no system
archives, no shared font), so every later test runs without a commercial game. It reads
`sdmc:/testapp/control.txt` once before its first frame and then: draws exact corner markers on both screens (in a
plain 2D mode or over a light citro3d scene), writes one flushed line per frame to `sdmc:/testapp/log.txt` and the
same text through `svcOutputDebugString`, keeps a small record in a global and in a heap block (their addresses logged
at start, for step G), and on request breaks (`svcBreak`), exits, writes `ready`, or boots slowly at a given frame.

Gate (PLAN.md section 3, "Phase B"), made concrete. Step A's `azhost` does not exist in this worktree (A is built in
parallel), so the runner here is the tracked prototype `prototype/fe2.c`; the main loop reruns the same checks with
`azhost` after the merge (section 8). All of it is `tests/gate-b.sh`, one `PASS`/`FAIL` line per check, non-zero exit
on any FAIL:
1. **Zero warnings.** `make -C testapp` (with the PATH of section 2) exits 0, its log has no `warning`, and
   `build/testapp.3dsx` exists. A host compile of the pure-C files passes: `cc -std=c11 -Wall -Wextra -Werror
   testapp/source/control.c testapp/source/record.c testapp/tests/host_test.c -o build/testapp-host-test &&
   build/testapp-host-test` prints `host_test ok`.
2. **Markers, 2D.** No `control.txt`. fe2 runs 40 s with shots at fe2 frames 299 and 599 (fe2 counts from 0, so
   these are the 300th and 600th `retro_run`). `python3 -I tests/check_testapp.py markers <png> --mode 2d` prints
   `markers ok top=4 bottom=4` for both shots (section 3's pixel table, exact RGB).
3. **One line per frame.** For the same run: `python3 -I tests/check_testapp.py log <sys>/Azahar/sdmc/testapp/log.txt
   --runs <fe2 frames from its DONE line>` prints `log ok lines=<L> first_v=<a> last_v=<b> offset=<o>` where every
   per-frame line's `f` is the previous plus 1 and `v` is the previous plus 1, the `start` line comes first, and the
   boot offset `o` = fe2 frames minus the last `f` is between 0 and 120 (assumption B1).
4. **Markers, 3D.** `control.txt` = `draw=3d`; same shots; `check_testapp.py markers --mode 3d` prints `markers ok`.
5. **Events.** Four short runs (20 s each), one per line of `control.txt`: `break_at=120` (the log's last line is
   `break f=120 ...`, no per-frame line after it); `exit_at=120` (last line `exit f=120 ...`); `ready_at=60` (a line
   `ready f=60 ...` and per-frame lines continue past 60); `boot_frames=90` (the first per-frame line is `f=91`,
   preceded by `booted f=90 ...`, and the two 2D shots still pass with `--mode 2d`). `check_testapp.py event <log>
   <kind> <n>` prints `event ok`.
6. **Planted red.** Once, run the markers check with `--expect-shift 1` (it shifts every expected pixel by one) and see
   it FAIL; then the real run passes again.

## 2. Facts checked for this plan (reviewers: verify these)

Toolchain (checked 2026-11-12): devkitPro at `/opt/devkitpro`, `DEVKITPRO` and `DEVKITARM` set; `picasso`, `tex3ds`,
`smdhtool`, `3dsxtool` in `/opt/devkitpro/tools/bin`. Homebrew's `arm-none-eabi-gcc` at `/opt/homebrew/bin` is found
first in a plain shell, so every build runs with `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH`
(the toolkit memory "devkitARM first in PATH"; `base_tools` also prepends them inside make, but set it anyway). The
Makefile pattern to start from (copy the structure, write our own file): `/opt/devkitpro/examples/3ds/graphics/gpu/
simple_tri/Makefile` (the PICA shader rules: `PICAFILES` :88, :123, :128, the `.shbin` rules :212-225), and the
C3D-plus-C2D mixing pattern in `/opt/devkitpro/examples/3ds/graphics/gpu/composite_scene/`. Not the toolkit's
`3ds-tool-template/Makefile` (it carries the `.cia` rules and no PICA rules; B makes a `.3dsx` only).

libctru (header lines in `/opt/devkitpro/libctru/include/3ds/`):
- `gfx.h:61` `gfxInit(top, bottom, vrambuffers)`; `gfx.h:46` `gfxInitDefault()` = BGR8 on both screens.
- BGR8 framebuffers are column-major, 240 pixels tall: pixel (x, y) of a screen is at byte `((x * 240) + (239 - y)) * 3`,
  in the order B, G, R. Width 400 top, 320 bottom.
- `services/gspgpu.h:150` `gspSetEventCallback(GSPGPU_EVENT_VBlank0, cb, data, false)` (the vblank counter);
  `:177` `gspWaitForVBlank0()`.
- `svc.h:1306` `svcOutputDebugString(const char *str, s32 length)`; `svc.h:1291` `svcBreak(UserBreakType)`, with
  `USERBREAK_ASSERT = 1` at `svc.h:334`; `svc.h:1149` `svcGetSystemTick()`; `os.h:260` `osGetTime()`.
- `services/fs.h:20` `FS_WRITE_FLUSH = BIT(0)`; `:988` `FSFILE_Write(handle, &written, offset, buf, size, flags)`.
- `hidKeysHeld()`, `hidTouchRead(touchPosition*)`, `hidCircleRead(circlePosition*)`, `KEY_TOUCH = BIT(20)`.

Azahar 2126.2 (SRC = the main checkout's `dl/azahar-src/unpacked/azahar-unified-source-2126.2/`):
- The emulated SD card is `<system dir>/Azahar/sdmc/` (spike 1, a real host folder; Gen3D already wrote
  `sdmc/Gen3D` there). So the host's `sdmc:/testapp/control.txt` is `<sys>/Azahar/sdmc/testapp/control.txt`.
- `src/core/file_sys/disk_archive.cpp:30-40`: `DiskFile::Write` calls the host file's `Flush()` when the guest's
  flush flag is set. So writing each line with `FSFILE_Write(..., FS_WRITE_FLUSH)` makes it visible on the host at
  once, even if the run is cut off. (newlib's `fflush` path is not checked; do not rely on stdio for the log.)
- `src/core/hle/kernel/svc.cpp:1170-1190`: `OutputDebugString` reads the string and logs it at **debug** level
  (`LOG_DEBUG(Debug_Emulated, ...)`), so the stock core's info-level log does not show it. B still calls it (step C's
  debug-text stop uses our core); B's gate does not check it.
- svcBreak reaches `Core::LogException` and status 14 (`ErrorCoreExceptionRaised`) (docs/reviews/plan-check-3.md
  section 1, svc.cpp:1164-1165, exception_handler.cpp:142). The guest stops; the core keeps returning frames.
- A guest exit: `svcExitProcess` only terminates the process (svc.cpp:582-584); the shutdown request (status 16)
  comes from APT `CloseApplication` with no Home Menu loaded (apt/applet_manager.cpp:1173-1177), which libctru's
  normal exit path from `main` is expected to reach (assumption B2; step C's gate checks the stop reason, B only
  checks the `exit` line). So `exit_at` returns from `main` normally after `gfxExit()`, never calls `svcExitProcess`.

fe2 as the runner (prototype/fe2.c, tracked, read 2026-11-12): usage `fe2 core content sysdir outdir seconds
shots` (fe2.c:2, :173-174), core options from env `OPT_<key>` else the core default (:153), MoltenVK from env
`MVK_LIB` (:92), shot files `<outdir>/shot_%06ld.png` of the whole 400x480 frame (:59) where the number is the
0-based frame count, and a final stderr line `DONE frames=<n> wall=... shots=<k>` (:192). Build (rules: it is a
tracked file, so building it is fine): `cc -O2 -I vendor -I vendor/include -o build/fe2 prototype/fe2.c -framework
OpenGL -lz`. Run line used by the gate:
```
MVK_LIB=dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib OPT_citra_graphics_api=Vulkan \
OPT_citra_input_type=none OPT_citra_enable_motion=disabled \
nice -n 10 build/fe2 dl/azahar/azahar_libretro.dylib build/testapp.3dsx <run>/sys <run>/out 40 299,599
```
The frame layout at resolution factor 1 (PLAN 2.2, spike 1): top at (0,0) 400x240, bottom at (40,240) 320x240 in a
400x480 frame; x 0-39 and 360-399 of rows 240-479 are black.

## 3. The app (exact behaviour)

`control.txt`, read once before the first frame; absent means all defaults. One `key=value` per line, `#` comments,
at most 16 lines of at most 64 bytes:
| Key | Values | Default | Effect |
|---|---|---|---|
| `draw` | `2d`, `3d` | `2d` | 2D: CPU writes into the BGR8 framebuffers. 3D: a rotating flat-coloured triangle on the top screen by citro3d, then the markers by citro2d rectangles on both screens |
| `break_at` | 1 to 1,000,000 | off | at that frame: log `break ...`, then `svcBreak(USERBREAK_ASSERT)` |
| `exit_at` | 1 to 1,000,000 | off | at that frame: log `exit ...`, leave the main loop, `gfxExit()`, return 0 |
| `ready_at` | 1 to 1,000,000 | off | at that frame: log `ready ...` (and `svcOutputDebugString("ready")`), keep running |
| `boot_frames` | 1 to 10,000 | 0 | the first N frames draw only the background, log no per-frame line; then log `booted ...` |
An unknown key or bad value: log `control error line=<n>` and use the default for that line (the gate's host test
covers it).

Markers: 8x8 solid squares, background `#202020`, everything else on the screen (the 3D triangle, a 3x5-pixel
frame counter in the middle of the top screen drawn with our own digit glyphs) stays at least 16 pixels from every
marker.
| Screen | Top-left at | Colour |
|---|---|---|
| top | (0,0) / (392,0) / (0,232) / (392,232) | red `FF0000` / green `00FF00` / blue `0000FF` / white `FFFFFF` |
| bottom | (0,0) / (312,0) / (0,232) / (312,232) | yellow `FFFF00` / cyan `00FFFF` / magenta `FF00FF` / orange `FF8000` |
`check_testapp.py markers` checks, for each marker, its four corner pixels and its centre are the colour, and the
pixel diagonally just outside its inner corner is `#202020`; in a full 400x480 frame it adds the bottom offset (40,
240) and checks (39,240) and (360,240) are black. It also takes a pair of split PNGs (`--top a.png --bottom b.png`,
400x240 and 320x240), the shape `azhost` writes, so the main loop's rerun uses the same checker. Mode `3d`: also exact
(assumption B3: citro2d axis-aligned rectangles at integer coordinates render without blending at factor 1); if not,
the builder reports the largest channel difference seen and the reviewers decide; the 2D check never loosens.

Log lines (`sdmc:/testapp/log.txt`, truncated at start, each line written by one `FSFILE_Write` with `FS_WRITE_FLUSH`
at its running offset; the same text to `svcOutputDebugString`). `f` = main-loop frame, from 1; `v` = vblank
callback count; `s` = `svcGetSystemTick()`; `t` = `osGetTime()`:
```
start addr_global=0x%08lx addr_heap=0x%08lx size=%u mode=2d|3d break_at=%lu exit_at=%lu ready_at=%lu boot_frames=%lu
f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d
ready f=%lu v=%lu        booted f=%lu v=%lu        break f=%lu v=%lu        exit f=%lu v=%lu
```
The record (for step G's memory reads): `typedef struct { uint32_t magic, frame, vblank, keys; uint16_t tx, ty;
int16_t cx, cy; uint64_t tick; uint32_t pad[2]; } laz_record;` with `magic = 0x4C415A52` ("LAZR"),
`_Static_assert(sizeof(laz_record) == 32, ...)`; one global instance and one `malloc`'d copy (checked, freed at exit),
both updated with the same values every frame before the log line.

Main loop order per frame: `hidScanInput`; fill the record; write the log line; draw; `gfxFlushBuffers` and
`gfxSwapBuffers` (2D) or `C3D_FrameEnd` (3D); `gspWaitForVBlank0()`. The loop is bounded (`f` up to 100,000,000,
then exit) and leaves on `aptMainLoop()` false.

## 4. Files the builder creates (and owns); functions under about 60 lines, about 2 asserts each

| Path | Role |
|---|---|
| `testapp/Makefile` | devkitPro 3ds_rules, `TARGET testapp`, our own `BUILD := build` (inside `testapp/`, ignored by the root `build/` rule), output to `../build/testapp.3dsx` (`mkdir -p ../build`), `.3dsx` only with an SMDH (title "lazpy test app", author "libazahar-py"), `-Wall -Wextra -Werror -O2`, libctru/citro headers by `-isystem` so their own warnings cannot fail us, libs `-lcitro2d -lcitro3d -lctru -lm`, PICA rules for `source/*.v.pica` |
| `testapp/README.md` | three lines: what it is, GPLv3, `make -C testapp` (this file is inside B's folder, so it is not the root README) |
| `testapp/source/main.c` | init (gfx, gsp callback, fs, hid), read control, the main loop, exit |
| `testapp/source/control.c`, `control.h` | pure C (`<stdint.h>`, `<string.h>` only): parse the control text into a struct |
| `testapp/source/record.c`, `record.h` | pure C: the record type, fill and format-a-log-line helpers (`snprintf` into a caller buffer) |
| `testapp/source/draw2d.c`, `draw2d.h` | BGR8 pixel, rectangle, the markers, background, the digit counter |
| `testapp/source/font.c`, `font.h` | our own 3x5 glyphs for 0-9 (15-bit masks) |
| `testapp/source/scene3d.c`, `scene3d.h` | citro3d init, one triangle, citro2d markers on both screen targets, exit |
| `testapp/source/vshader.v.pica` | our own minimal pass-through vertex shader (position by a projection uniform, colour) |
| `testapp/source/sdlog.c`, `sdlog.h` | open/truncate `/testapp/log.txt` on the SD archive (`FSUSER_OpenArchive` SDMC, `FSUSER_CreateDirectory` for `/testapp`, `FSUSER_OpenFile` create+write, `FSFILE_SetSize(0)`), write one line with flush, close; read `control.txt` |
| `testapp/tests/host_test.c` | host test of control parsing (good keys, unknown key, out-of-range value, comment, no file) and the record size and line format; prints `host_test ok` |
| `tests/check_testapp.py` | stdlib only (`zlib`, `struct`): PNG decode (colour types 2 and 6, bit depth 8, all five filter types, one IDAT stream), the `markers`, `log` and `event` subcommands; runs with `python3 -I`; under about 200 lines |
| `tests/gate-b.sh` | section 1's gate: POSIX `sh`, `set -eu`, ShellCheck clean, under about 100 lines; `RUNNER=fe2` (default) or `RUNNER=azhost` (for the main loop after the merge: `build/azhost run ... --frames 600 --shot 300,600` and the split-PNG checker form) |
| item `docs/status/lazpy/1-in-progress/130-step-b-test-app.md` (the main loop moves it there from 2-next/ at launch) | only its "Lessons and notes" section |

Every source file starts with `// SPDX-License-Identifier: GPL-3.0-or-later`. No code copied from the devkitPro
examples beyond the Makefile's structure (their rules file include and variable names are the standard way to use the
toolchain). No assets other than our own glyphs. C rules as in `~/.claude/c-golden-rules.md`: no goto, recursion or
setjmp; bounded loops; every libctru `Result` checked (`R_FAILED`), with a failed init logged and the app exiting
cleanly; one owner per allocation; function pointers only for the gsp vblank callback (one comment says so).

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

0. Seed the worktree: `mkdir -p dl && cp -R <main checkout>/dl/azahar <main checkout>/dl/moltenvk dl/` and
   `cp -R <main checkout>/vendor .` (both ignored; the main loop has moved its `dl/` into fetch.sh's layout before the
   launch). Build fe2 (section 2). Checkpoint: `build/fe2` exists.
1. Makefile, `main.c` with gfx init, 2D background and markers only. Checkpoint: zero-warning build; one 40 s fe2 run;
   look at `shot_000299.png` with the Read tool (never `open`).
2. `control.c`, `record.c`, `host_test.c`. Checkpoint: `host_test ok`.
3. `sdlog.c`, the log lines, the vblank callback, the record. Checkpoint: the log check (gate 3) on a fe2 run; note the
   boot offset.
4. `scene3d.c`, the shader. Checkpoint: gate 4.
5. The four events. Checkpoint: gate 5.
6. `check_testapp.py` complete, `gate-b.sh`, ShellCheck, the planted red. Checkpoint: the whole gate PASSes; quote it.
7. The report.

## 6. Machine-sharing rules

- One emulator instance at a time (the gate runs its six fe2 runs one after another), always `nice -n 10`, folders
  under `runs/b-*` (ignored); a fresh `<run>/sys` per run with only `Azahar/sdmc/testapp/control.txt` seeded.
- Never open a window: no Azahar app, no `open`, no Preview. Look at PNGs with the Read tool.
- Never kill a process you did not start. fe2 ends on its own after its seconds; the gate waits for it with a bounded
  timeout (seconds plus 120) and kills only its own pid if it overruns.
- The machine was at load 86 when this was written. If a 40 s run delivers fewer than 600 frames, the gate prints
  `FAIL slow: frames=<n>` and the builder reruns with `SECS=90` before reporting (not a code fault).

## 7. Files the builder must not touch

Everything outside section 4. In particular the top-level `Makefile`, `host/`, `tests/gate-a.sh` (A's),
`core/`, `tools/` (F1's and the existing tools), `prototype/` (build fe2, never edit it), `.gitignore`, `docs/map/*`,
the root `README.md`, `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff, other items, and the main
checkout (read and copy only).

## 8. The builder's report, and what the main loop does after the merge

Report: the gate output (and the red); the measured boot offset (assumption B1) and what it was per run; whether 3D
markers came out exact (B3); the `.3dsx` size; line counts and the longest function; anything the core did that this
plan did not predict. The `.gitignore` lines for the main loop: `*.elf`, `*.smdh`, `*.shbin`, `*.lst`, `*.map`
(devkitPro build outputs; `build/` already covers `testapp/build/`). The runners block for `docs/map/runners.md`:
```
PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make -C testapp   # build/testapp.3dsx
tests/gate-b.sh                       # step B's gate (fe2); RUNNER=azhost tests/gate-b.sh after step A
```
After A and B both merge, the main loop runs `RUNNER=azhost tests/gate-b.sh` once (it needs A's `build/azhost`; A's
top-level Makefile `testapp` target delegates to `testapp/Makefile`, so `make testapp` then works too) and books it as
B's evidence.

## 9. Hours (agent wall time)

Builder 0.75 h (Makefile and 2D 0.15, control and host test 0.1, log and record 0.15, 3D 0.15, events 0.1, checker
and gate 0.1), plus the opus diff review and the commit, about 0.35 h: **1.1 h**, 0.1 h over PLAN.md's 1.0. The six
fe2 runs are about 3 minutes of wall time at today's load and are inside the estimate.

## 10. Review checklist (the opus diff review)

1. Behaviour matches section 3: control keys, defaults, ranges, the error line; the marker table exact; the log line
   formats exact; the record 32 bytes with its magic; both addresses logged at start.
2. Each log line is one `FSFILE_Write` with `FS_WRITE_FLUSH`; no stdio for the log; offsets advance correctly.
3. `break_at` uses `svcBreak(USERBREAK_ASSERT)`; `exit_at` returns from `main` after `gfxExit()`, no `svcExitProcess`;
   `boot_frames` logs nothing per frame until it ends.
4. Pure-C files include only `<stdint.h>`/`<string.h>` (and `<stdio.h>` for `snprintf` in record.c if needed) and
   compile on the host with `-Werror`.
5. C rules: no goto/recursion/setjmp; bounded loops; every `Result` checked; functions under about 60 lines; asserts;
   one function-pointer use, documented.
6. Licence and clean-room: SPDX headers; our own glyphs and shader; no copied example code; no system archive or
   shared font use.
7. Makefile: `.3dsx` only, `-Wall -Wextra -Werror`, `-isystem` for library headers, output in `build/`, no edits
   outside `testapp/`.
8. Checker: stdlib only, `-I`, handles all five PNG filters, both frame shapes; the planted red shown.
9. Gate script: ShellCheck clean, bounded waits, one emulator at a time, kills only its own pid, the slow-run message.
10. Nothing in the diff that is a build output (`.3dsx`, `.elf`, `.smdh`, `.shbin`, PNGs, logs).
