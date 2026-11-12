# Phase 1, step B: the test app (item laz-130)

Opus step plan, 2026-11-12, revision 2 (after `docs/reviews/phase-1-review-1.md` and `phase-1-review-2.md`), **the
plan to build from once the main loop launches the step.** Index, and what
changed in this revision: `docs/plans/phase-1.md`. For one sonnet builder in its own git worktree. It refines
`docs/PLAN.md`'s "Phase B" paragraph of section 3; where they disagree on a goal, PLAN.md wins and the builder stops
and reports. Phase 2 (`docs/plans/phase-2.md` section 5) uses the control keys, log lines and markers of section 3;
a change to them is a change to Phase 2.

Where you are: in the worktree the main loop made, branch `step-b` (create no branch). The main checkout, read and
copy only, is `/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py` (called MAIN below).

Builder reads first: `docs/map/rules.md`, PLAN.md section 3 "Phase B" and 2.2 (the frame layout and stop reasons
the app must exercise), `docs/research/spike-1-headless-core.md` (the emulated SD folder), `~/.claude/c-golden-rules.md`,
`~/.claude/shell-golden-rules.md`, `~/.claude/python-golden-rules.md`.

## 1. Goal and gate

Goal: `build/testapp.3dsx`, our own small 3DS homebrew app (libctru, GPLv3, our own glyphs and shader, no system
archives, no shared font), so every later test runs without a commercial game. It reads
`sdmc:/testapp/control.txt` once before its first frame and then: draws exact corner markers on both screens (in a
plain 2D mode or over a light citro3d scene), writes one flushed line per frame to `sdmc:/testapp/log.txt` and the
same text through `svcOutputDebugString`, keeps a small record in a global and in a heap block (their addresses logged
at start, for step G), and on request calls `svcBreak` and runs on, exits, writes `ready`, or boots slowly with the
CPU busy (it stands in for Gen3D's world build).

Gate (PLAN.md section 3, "Phase B"), made concrete. Step A's `azhost` does not exist in this worktree (A is built in
parallel), so the runner here is the tracked prototype `prototype/fe2.c`; the main loop reruns the same checks with
`RUNNER=azhost` on its integration branch (section 8). All of it is `tests/gate-b.sh`, one `PASS`/`FAIL` line per check,
non-zero exit on any FAIL:
1. **Zero warnings.** `make -C testapp` (with the PATH of section 2) exits 0, its log has no `warning`, and
   `build/testapp.3dsx` exists. A host compile of the pure-C files passes: `cc -std=c11 -Wall -Wextra -Werror
   testapp/source/control.c testapp/source/record.c testapp/tests/host_test.c -o build/testapp-host-test &&
   build/testapp-host-test` prints `host_test ok`.
2. **Markers, 2D.** No `control.txt`. fe2 runs `SECS` seconds (default 15) with shots at fe2 frames 299 and 599 (fe2
   counts from 0, so these are the 300th and 600th `retro_run`). `python3 -I tests/check_testapp.py markers <png>
   --mode 2d` prints `markers ok top=4 bottom=4` for both shots (section 3's pixel table, exact RGB).
3. **One line per frame.** For the same run: `python3 -I tests/check_testapp.py log <sys>/Azahar/sdmc/testapp/log.txt
   --runs <fe2 frames from its DONE line>` prints `log ok lines=<L> first_v=<a> last_v=<b> offset=<o> vjumps=<j>`.
   It requires: the `start` line first; every per-frame line's `f` is the previous plus 1; the boot offset `o` = fe2
   frames minus the last `f` is between 0 and 120 (assumption B1). It reports `v` jumps (`v` not the previous plus 1)
   as `vjumps`, and does not fail on them: one `v` per frame is step C's claim (C(d)); if `vjumps` is not 0, report
   the jumps and do not chase them in B.
4. **Markers, 3D.** `control.txt` = `draw=3d`; same shots; `check_testapp.py markers --mode 3d` prints `markers ok`.
5. **Events.** Four short runs (10 s each), one `control.txt` line each, checked by `check_testapp.py event <log>
   <kind> <n>`, which prints `event ok`:
   - `break_at=120`: a `break f=120 ...` line, then per-frame lines go on from `f=121` (svcBreak does not stop the
     guest, section 2; PLAN C(e) "the guest runs on").
   - `exit_at=120`: the last line is `exit f=120 ...`.
   - `ready_at=60`: a `ready f=60 ...` line, and per-frame lines continue past 60.
   - `boot_frames=90`: a `booted f=90 ...` line, the first per-frame line is `f=91`, and (one 15 s run with shots)
     both 2D shots still pass `--mode 2d`.
   - In every run the app is still running at the end unless `exit_at` was set (no exit on a button).
6. **Planted red.** Once, run the markers check with `--expect-shift 1` (it shifts every expected pixel by one) and see
   it FAIL; then the real run passes again.

Waits: macOS has no `timeout` (shell rule 3), so each fe2 or azhost run is a background pid with a bounded `kill -0`
loop (seconds plus 120). On `FAIL slow: frames=<n>` (fewer than 600 frames in a shot run) the script itself reruns
that check once with `SECS=40` before failing, so the main loop's rerun needs no judgement.

## 2. Facts checked for this plan (reviewers: verify these)

Toolchain (checked 2026-11-12): devkitPro at `/opt/devkitpro`, `DEVKITPRO` and `DEVKITARM` set; `picasso`, `tex3ds`,
`smdhtool`, `3dsxtool` in `/opt/devkitpro/tools/bin`. Homebrew's `arm-none-eabi-gcc` at `/opt/homebrew/bin` is found
first in a plain shell, so every build runs with `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH`
(the toolkit memory "devkitARM first in PATH"; `base_tools` also prepends them inside make, but set it anyway). The
Makefile pattern to start from (copy the structure, write our own file): `/opt/devkitpro/examples/3ds/graphics/gpu/
simple_tri/Makefile` (the PICA shader rules: `PICAFILES` :88, :123, :128, the `.shbin` rules :212-225), and the
C3D-plus-C2D mixing pattern in `/opt/devkitpro/examples/3ds/graphics/gpu/composite_scene/`. Not the toolkit's
`3ds-tool-template/Makefile` (it carries the `.cia` rules and no PICA rules; B makes a `.3dsx` only).

libctru (header lines in `/opt/devkitpro/libctru/include/3ds/`; libctru source read by review 1 at
`3ds-toolkit/projects/_reference/libctru`, git 9b55eda; installed 2.7.0-1):
- `gfx.h:61` `gfxInit(top, bottom, vrambuffers)`; `gfx.h:46` `gfxInitDefault()` = BGR8 on both screens; the
  framebuffers are double-buffered.
- BGR8 framebuffers are column-major, 240 pixels tall: pixel (x, y) of a screen is at byte `((x * 240) + (239 - y)) * 3`,
  in the order B, G, R. Width 400 top, 320 bottom.
- `services/gspgpu.h:150` `gspSetEventCallback(GSPGPU_EVENT_VBlank0, cb, data, false)`; `:177` `gspWaitForVBlank0()`.
  **One callback per event** (`gspgpu.c:282-289`, `gspEventCb[id] = cb`), and citro3d uses the VBlank0 slot itself
  (`libcitro3d.a` imports `gspSetEventCallback` and defines `onVBlank0`/`onVBlank1`; its counter is
  `C3D_FrameCounter(0)`, `c3d/renderqueue.h:29`, and `C3D_FrameBegin(C3D_FRAME_SYNCDRAW)` waits on it). So our own
  vblank callback is used only while citro3d is not initialised (section 3).
- `svc.h:1306` `svcOutputDebugString(const char *str, s32 length)`; `svc.h:1291` `svcBreak(UserBreakType)` (not
  `noreturn`), with `USERBREAK_ASSERT = 1` at `svc.h:334`; `svc.h:1149` `svcGetSystemTick()`; `os.h:260` `osGetTime()`.
- `services/fs.h:20` `FS_WRITE_FLUSH = BIT(0)`; `:988` `FSFILE_Write(handle, &written, offset, buf, size, flags)`.
- `hidKeysHeld()`, `hidTouchRead(touchPosition*)`, `hidCircleRead(circlePosition*)`, `KEY_TOUCH = BIT(20)`.
- On devkitARM `uint32_t` is `unsigned long`; on macOS arm64 it is `unsigned int`. So a `%lu` with a bare `uint32_t`
  fails `-Werror` on one of the two compilers (section 3 casts every argument).
- The exit path: return from `main` → `__appExit` → `aptExit` (`apt.c:371-431`: not crippled, no chainload, so it
  calls `APT_PrepareToCloseApplication(true)`) → `__libctru_exit` calls `APT_CloseApplication` before
  `svcExitProcess` (`ctru_exit.c:32-36`).

Azahar 2126.2 (SRC = MAIN's `dl/azahar-src/unpacked/azahar-unified-source-2126.2/`):
- The emulated SD card is `<system dir>/Azahar/sdmc/` (spike 1, a real host folder). So the guest's
  `sdmc:/testapp/control.txt` is `<sys>/Azahar/sdmc/testapp/control.txt`.
- `src/core/file_sys/disk_archive.cpp:30-40`: `DiskFile::Write` calls the host file's `Flush()` when the guest's
  flush flag is set. Writes to SD files are synchronous on the emulator thread on both cores (`file.cpp:198-217`,
  `DiskFile` does not allow cached reads), but OpenFile, SetSize and Close run async on the stock core
  (`fs_user.cpp:70`, `file.cpp:288, 317`). So: open the log once, never close and reopen it per line, write each line
  with `FSFILE_Write(..., FS_WRITE_FLUSH)` at a running offset; the line is on the host at once, even if the run is
  cut off. (newlib's `fflush` path is not checked; do not use stdio for the log.)
- `src/core/hle/kernel/svc.cpp:1170-1190`: `OutputDebugString` logs the string at **debug** level
  (`LOG_DEBUG(Debug_Emulated, ...)`). The stock core does forward it: its filter is Debug (citra_libretro.cpp:59) and
  the backend maps Debug to `RETRO_LOG_DEBUG` (backend.cpp:79-81); only the host's info threshold hides it. Our core
  (patch 0004) keeps only that class at debug, which is cheaper. B calls it; B's gate does not check it.
- svcBreak: `SVC::Break` (svc.cpp:1148-1166) logs and calls `Core::LogException`, which sets status 14 and returns
  (exception_handler.cpp:142); `RunLoop` resets the status (core.cpp:111). **The guest runs on** after svcBreak
  returns; the app does nothing special after it.
- A guest exit: `svcExitProcess` alone only terminates the process (svc.cpp:582-584). The shutdown request (status 16)
  comes from APT: PrepareToClose sets the target to HomeMenu (apt/applet_manager.cpp:1131-1136), and
  `CloseApplication` with no Home Menu registered calls `RequestShutdown` (:1173-1177), so `RunLoop` returns 16
  (core.cpp:144). libctru's normal exit path (above) does both, so `exit_at` returns from `main` after `gfxExit()`
  and never calls `svcExitProcess` itself (review 1 confirmed from source; step C's gate checks the stop reason).

fe2 as the runner (prototype/fe2.c, tracked): usage `fe2 core content sysdir outdir seconds shots` (fe2.c:2,
:173-174), core options from env `OPT_<key>` else the core default (:153), MoltenVK from env `MVK_LIB` (:92), shot
files `<outdir>/shot_%06ld.png` of the whole 400x480 frame (:59) where the number is the 0-based frame count, filter
0 rows (`png()`, :46), and a final stderr line `DONE frames=<n> wall=... shots=<k>` (:192). Build (it is a tracked
file, so building it is fine): `cc -O2 -I vendor -I vendor/include -o build/fe2 prototype/fe2.c -framework OpenGL
-lz`. Run line used by the gate:
```
MVK_LIB=dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib OPT_citra_graphics_api=Vulkan \
OPT_citra_input_type=none OPT_citra_enable_motion=disabled \
nice -n 10 build/fe2 dl/azahar/azahar_libretro.dylib build/testapp.3dsx <run>/sys <run>/out "$SECS" 299,599
```
The azhost run line (step A's interface, `docs/plans/phase-a.md` section 3), for `RUNNER=azhost`:
```
nice -n 10 build/azhost run build/testapp.3dsx --sys <run>/sys --out <run>/out --frames 600 --shot 300,600
```
Its shots are `<run>/out/shot_000300_top.png` / `_bottom.png` (and `000600`), split 400x240 and 320x240, written
with filter 0; the frame count is `frames=<n>` on stdout; the log is `<run>/sys/Azahar/sdmc/testapp/log.txt`. The
event runs use `--frames 600` with no shots. That branch of `gate-b.sh` is written by B and run first by the main
loop on its integration branch (A and B merged, before main).

The frame layout at resolution factor 1 (PLAN 2.2, spike 1): top at (0,0) 400x240, bottom at (40,240) 320x240 in a
400x480 frame; x 0-39 and 360-399 of rows 240-479 are black (the layout background, settings.h:608-610).

## 3. The app (exact behaviour)

`control.txt`, read once before the first frame; absent means all defaults. One `key=value` per line, `#` comments,
at most 16 lines of at most 64 bytes:
| Key | Values | Default | Effect |
|---|---|---|---|
| `draw` | `2d`, `3d` | `2d` | 2D: CPU writes into the BGR8 framebuffers. 3D: a rotating flat-coloured triangle on the top screen by citro3d, then the markers by citro2d rectangles on both screens |
| `break_at` | 1 to 1,000,000 | off | at that frame: log `break ...`, then `svcBreak(USERBREAK_ASSERT)`, then go on as normal |
| `exit_at` | 1 to 1,000,000 | off | at that frame: log `exit ...`, leave the main loop, `gfxExit()`, return 0 |
| `ready_at` | 1 to 1,000,000 | off | at that frame: log `ready ...` (and `svcOutputDebugString("ready")`), keep running |
| `boot_frames` | 1 to 10,000 | 0 | the first N frames are a busy boot (below), with no per-frame line; then log `booted ...` |
An unknown key or bad value: log `control error line=<n>` and use the default for that line (the host test covers it).

The busy boot (`boot_frames`): it stands in for Gen3D's world build, so the guest CPU stays busy, not idle (Phase 2's
step D times a savestate boot against it). It runs before citro3d is initialised, in both modes. Each boot frame:
draw nothing new; spin on a bounded busy loop (an xorshift32 over a 64 KiB static buffer, checking our vblank counter
every 1024 steps, at most 50,000,000 steps per frame) until our vblank counter moves; no `gspWaitForVBlank0()`; then
`gfxFlushBuffers` and `gfxSwapBuffers`. If the step cap is hit, log `boot spin cap f=<n>` once and go on. Our vblank
callback (an atomic `uint32_t` increment, registered once at start) is the only function pointer the app passes. A
buffer checksum goes in the `booted` line so the loop cannot be optimised away. (Assumption B4: libctru's GSP event
thread, priority 0x1A, preempts the spinning main thread, priority 0x30, so the counter still moves.)

**The app never exits on a button, START included** (Phase 2's gate presses START). It leaves only on `aptMainLoop()`
false, at `exit_at`, or at the frame cap; no code from the devkitPro examples' `if (kDown & KEY_START) break;` is
added.

Markers: 8x8 solid squares, background `#202020`. Only the top screen carries anything else (the 3D triangle and a
3x5-pixel frame counter at the top screen's centre, drawn with our own digit glyphs), always at least 16 pixels from
every marker; the bottom screen is background plus its four markers only.
| Screen | Top-left at | Colour |
|---|---|---|
| top | (0,0) / (392,0) / (0,232) / (392,232) | red `FF0000` / green `00FF00` / blue `0000FF` / white `FFFFFF` |
| bottom | (0,0) / (312,0) / (0,232) / (312,232) | yellow `FFFF00` / cyan `00FFFF` / magenta `FF00FF` / orange `FF8000` |
`check_testapp.py markers` checks, for each marker, its four corner pixels and its centre are the colour, and the
pixel diagonally just outside its inner corner is `#202020`; in a full 400x480 frame it adds the bottom offset (40,
240) and checks (39,240) and (360,240) are black. It also takes split PNGs (`--top a.png --bottom b.png`, 400x240 and
320x240), the shape `azhost` writes. It decodes 8-bit RGB or RGBA PNGs whose rows all use filter 0 (both fe2 and
azhost write filter 0) and fails with `unsupported PNG filter <n>` on any other. Mode `3d`: also exact (assumption B3:
citro2d axis-aligned rectangles at integer coordinates render without blending at factor 1; the core presents with
nearest-neighbour sampling, core_settings.cpp:1139); if not, the builder reports the largest channel difference seen
and the reviewers decide; the 2D check never loosens.

2D drawing: clear each of the two framebuffers to the background and draw the markers once, in the first two
main-loop frames after the busy boot (f = boot_frames + 1 and f = boot_frames + 2, one per buffer; with no busy boot,
f = 1 and 2); after that redraw only the counter digits each frame. The busy boot itself draws nothing new. 3D: citro3d and citro2d draw everything each
frame, as usual.

Log lines (`sdmc:/testapp/log.txt`; at start create `/testapp` (an already-exists result counts as success), open
the file once with create and write, `FSFILE_SetSize(0)`; each line one `FSFILE_Write` with `FS_WRITE_FLUSH` at its
running offset; the same text to `svcOutputDebugString`). `f` = main-loop frame, from 1, counting boot frames too;
`v` = the vblank count (2D: our callback's counter; 3D: `C3D_FrameCounter(0)`, so `v` restarts when citro3d starts;
the gate checks `v` in 2D only); `s` = `svcGetSystemTick()`; `t` = `osGetTime()`:
```
start addr_global=0x%08lx addr_heap=0x%08lx size=%u mode=2d|3d break_at=%lu exit_at=%lu ready_at=%lu boot_frames=%lu
f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d
ready f=%lu v=%lu        booted f=%lu v=%lu sum=%08lx        break f=%lu v=%lu        exit f=%lu v=%lu
```
Every argument is cast to its format's own type (`(unsigned long)rec->frame`, `(unsigned long long)tick`,
`(unsigned)rec->tx`, `(int)rec->cx`, `(unsigned long)(uintptr_t)&g_record`); no `<inttypes.h>`, so `record.c`
stays pure C and compiles warning-free on both devkitARM and the Mac.

The record (for step G's memory reads): `typedef struct { uint32_t magic, frame, vblank, keys; uint16_t tx, ty;
int16_t cx, cy; uint64_t tick; } laz_record;` with `magic = 0x4C415A52` ("LAZR"),
`_Static_assert(sizeof(laz_record) == 32, ...)` and `_Static_assert(offsetof(laz_record, tick) == 24, ...)` (true on
AAPCS and arm64: `tick` is 8-aligned at 24, no padding). Step G reads these offsets: magic 0, frame 4, vblank 8,
keys 12, tx 16, ty 18, cx 20, cy 22, tick 24; one global instance and one `malloc`'d copy (checked, freed at exit),
both updated with the same values every frame before the log line.

Main loop per frame, bounded (`f` up to 100,000,000, then exit; it also leaves on `aptMainLoop()` false; never on a
button):
- 2D: `hidScanInput`; fill the record; write the log line; events; draw; `gfxFlushBuffers`, `gfxSwapBuffers`;
  `gspWaitForVBlank0()`. So input is sampled right after a VBlank.
- 3D: `C3D_FrameBegin(C3D_FRAME_SYNCDRAW)` (it waits for the VBlank); `hidScanInput`; fill the record; write the log
  line; events; draw the triangle, then the citro2d markers on both screen targets; `C3D_FrameEnd(0)`. No extra
  `gspWaitForVBlank0()` and no `gspSetEventCallback` after `C3D_Init`.

## 4. Files the builder creates (and owns); functions under about 60 lines, about 2 asserts each

| Path | Role |
|---|---|
| `testapp/Makefile` | devkitPro 3ds_rules, `TARGET testapp`, our own `BUILD := build` (inside `testapp/`, ignored by the root `build/` rule), output to `../build/testapp.3dsx` (`mkdir -p ../build`), `.3dsx` only with an SMDH (title "lazpy test app", author "libazahar-py"), `-Wall -Wextra -Werror -O2`, libctru/citro headers by `-isystem` so their own warnings cannot fail us, libs `-lcitro2d -lcitro3d -lctru -lm`, PICA rules for `source/*.v.pica` |
| `testapp/README.md` | three lines: what it is, GPLv3, `make -C testapp` (inside B's folder; not the root README) |
| `testapp/source/main.c` | init (gfx, the vblank callback, fs, hid), read control, the busy boot, the main loop, exit |
| `testapp/source/control.c`, `control.h` | pure C (`<stdint.h>`, `<string.h>` only): parse the control text into a struct |
| `testapp/source/record.c`, `record.h` | pure C (plus `<stdio.h>` for `snprintf` and `<stddef.h>` for `offsetof`): the record type, fill and format-a-log-line helpers into a caller buffer |
| `testapp/source/draw2d.c`, `draw2d.h` | BGR8 pixel, rectangle, the markers, background, the digit counter |
| `testapp/source/font.c`, `font.h` | our own 3x5 glyphs for 0-9 (15-bit masks) |
| `testapp/source/scene3d.c`, `scene3d.h` | citro3d init, one triangle, citro2d markers on both screen targets, exit |
| `testapp/source/vshader.v.pica` | our own minimal pass-through vertex shader (position by a projection uniform, colour) |
| `testapp/source/sdlog.c`, `sdlog.h` | the SD archive (`FSUSER_OpenArchive` SDMC), `/testapp` creation, the log opened once and written line by line with flush, closed at exit; reading `control.txt` |
| `testapp/tests/host_test.c` | host test of control parsing (good keys, unknown key, out-of-range value, comment, no file) and the record size and line format; prints `host_test ok` |
| `tests/check_testapp.py` | stdlib only (`zlib`, `struct`), runs with `python3 -I`, under about 170 lines. A public function `read_png_rgba(path: str) -> tuple[int, int, bytes]` returning (width, height, RGBA bytes, row-major, RGB expanded to RGBA with alpha 255): the filter-0 decoder, raising `ValueError` on any other filter, colour type or bit depth; Phase 2 imports it (`tests/` on `sys.path`), never copies it. The `markers`, `log` and `event` subcommands sit behind `if __name__ == "__main__":`, so importing runs nothing |
| `tests/gate-b.sh` | section 1's gate: POSIX `sh`, `set -eu`, ShellCheck clean, under about 100 lines; `RUNNER=fe2` (default) or `RUNNER=azhost` (section 2's azhost line and the split-PNG checker form) |

No item files: notes go in the report's "Lessons and notes" block (section 8).

Every source file starts with `// SPDX-License-Identifier: GPL-3.0-or-later`. No code copied from the devkitPro
examples beyond the Makefile's structure (their rules file include and variable names are the standard way to use the
toolchain). No assets other than our own glyphs. C rules as in `~/.claude/c-golden-rules.md`: no goto, recursion or
setjmp; bounded loops; every libctru `Result` checked (`R_FAILED`), with a failed init logged and the app exiting
cleanly; one owner per allocation; function pointers only for the vblank callback (one comment says so).

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

0. Seed the worktree: `mkdir -p dl && cp -R MAIN/dl/azahar MAIN/dl/moltenvk dl/` and `cp -R MAIN/vendor .` (both
   ignored; MAIN's `dl/` is already in fetch.sh's layout). Build fe2 (section 2). Checkpoint: `build/fe2` exists.
1. Makefile, `main.c` with gfx init, 2D background and markers only. Checkpoint: zero-warning build; one 15 s fe2 run;
   look at `shot_000299.png` with the Read tool (never `open`).
2. `control.c`, `record.c`, `host_test.c`. Checkpoint: `host_test ok`.
3. `sdlog.c`, the log lines, the vblank callback, the record. Checkpoint: the log check (gate 3) on a fe2 run; note the
   boot offset and `vjumps`.
4. `scene3d.c`, the shader. Checkpoint: gate 4.
5. The four events and the busy boot. Checkpoint: gate 5.
6. `check_testapp.py` complete, `gate-b.sh` (both runner branches), ShellCheck, the planted red. Checkpoint: the whole
   gate PASSes with `RUNNER=fe2`; quote it.
7. The report.

## 6. Machine-sharing rules

- One emulator instance at a time (the gate's fe2 runs go one after another), always `nice -n 10`, folders under
  `runs/b-*` (ignored); a fresh `<run>/sys` per run with only `Azahar/sdmc/testapp/control.txt` seeded.
- Never open a window: no Azahar app, no `open`, no Preview. Look at PNGs with the Read tool.
- Never kill a process you did not start. fe2 ends on its own after its seconds; the gate waits for it with a bounded
  timeout (seconds plus 120) and kills only its own pid if it overruns.
- The machine was at load 86 when this was written. If a shot run delivers fewer than 600 frames, the gate prints
  `FAIL slow: frames=<n>` and the builder reruns with `SECS=40` before reporting (not a code fault).

## 7. Files the builder must not touch

Everything outside section 4. In particular the top-level `Makefile`, `host/`, `tests/gate-a.sh` and
`tests/test_version.c` (A's), `core/`, `tools/` (F1's and the existing tools), `prototype/` (build fe2, never edit
it), `.gitignore`, `docs/map/*`, the root `README.md`, `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the
handoff, every item file, and MAIN (read and copy only).

## 8. The builder's report, and what the main loop does on the integration branch

Report: the gate output (and the red); the measured boot offset (B1) per run and `vjumps`; whether 3D markers came
out exact (B3); whether the busy boot hit its cap (B4) and its wall time for 90 frames; the `.3dsx` size; line counts
and the longest function; anything the core did that this plan did not predict. The `.gitignore` lines for the main
loop: `*.elf`, `*.smdh`, `*.shbin`, `*.lst`, `*.map` (devkitPro build outputs; `build/` already covers
`testapp/build/`). The runners block for `docs/map/runners.md`:
```
PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make -C testapp   # build/testapp.3dsx
tests/gate-b.sh                       # step B's gate (fe2); RUNNER=azhost tests/gate-b.sh after step A
```
The map lines for the main loop (one each): `testapp/` for `docs/map/code.md`, `tests/gate-b.sh` and
`tests/check_testapp.py` for `docs/map/tools.md`. For Phase I's licence audit: the SMDH takes libctru's
`default_icon.png` when no icon is given (simple_tri Makefile :28-32, :140-150, zlib licence), so the shipped
`.3dsx` carries it. Last, a block headed `Lessons and notes` for the main loop to paste into item laz-130.

On its integration branch (A and B merged, before main; phase-1.md "Merge and launch" 4), the main loop runs `RUNNER=azhost tests/gate-b.sh` once (it needs A's `build/azhost`; A's
top-level `make testapp` delegates to `testapp/Makefile`) and books it as B's evidence.

## 9. Hours (agent wall time)

Builder 0.7 h (Makefile and 2D 0.15, control and host test 0.1, log and record 0.15, 3D 0.15, events and busy boot
0.1, checker and gate 0.05 with the filter-0 decoder; review 2's additions are a few lines each), plus its share of
the one as-built review and the commit (about 0.2 h, `docs/plans/phase-1.md` "Hours"): **0.9 h** (PLAN.md: 1.0). The gate's seven fe2 runs
are about 1.5 minutes of wall time at today's load.

## 10. Review checklist (the opus diff review)

1. Behaviour matches section 3: control keys, defaults, ranges, the error line; the marker table exact; the bottom
   screen carries only markers; the log line formats exact with every argument cast; the record 32 bytes, `tick` at
   24, its magic; both addresses logged at start; no exit on any button; 2D markers drawn in the first two frames
   after the busy boot.
2. The log is opened once; each line is one `FSFILE_Write` with `FS_WRITE_FLUSH`; no stdio for the log; offsets
   advance correctly; an existing `/testapp` is not an error.
3. `break_at` calls `svcBreak(USERBREAK_ASSERT)` and the loop goes on; `exit_at` returns from `main` after
   `gfxExit()`, no `svcExitProcess`; `boot_frames` spins busy (bounded) with no VBlank wait and no per-frame line.
4. Our vblank callback is never registered after `C3D_Init`; 3D mode uses `C3D_FrameBegin(C3D_FRAME_SYNCDRAW)` /
   `C3D_FrameEnd(0)` with no extra VBlank wait, and `v = C3D_FrameCounter(0)`.
5. Pure-C files include only `<stdint.h>`/`<string.h>` (and `<stdio.h>`, `<stddef.h>` in record.c) and compile on the host with
   `-Werror`.
6. C rules: no goto/recursion/setjmp; bounded loops; every `Result` checked; functions under about 60 lines; asserts;
   one function-pointer use (the 2D vblank callback), documented.
7. Licence and clean-room: SPDX headers; our own glyphs and shader; no copied example code; no system archive or
   shared font use.
8. Makefile: `.3dsx` only, `-Wall -Wextra -Werror`, `-isystem` for library headers, output in `build/`, no edits
   outside `testapp/`.
9. Checker and gate: stdlib only, `-I`, `read_png_rgba` with the stated signature and importable with no side
   effects, filter-0 decoder that refuses others, both frame shapes, the planted red shown; ShellCheck clean, no
   `timeout` (background pid plus a bounded `kill -0` loop), one emulator at a time, kills only its own pid, the
   slow-run rerun at `SECS=40` inside the script, the azhost branch matches A's interface.

10. Nothing in the diff that is a build output (`.3dsx`, `.elf`, `.smdh`, `.shbin`, PNGs, logs).
