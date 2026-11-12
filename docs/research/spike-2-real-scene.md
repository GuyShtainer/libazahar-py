# Spike 2: memory reads and real speed on a 3D scene (from Gen3D), 2026-11-12

Agent a8bc5d5c (sonnet), 15:46-16:20, run by the Gen3D session; hours booked in Gen3D's ledger. Written into this
repo by the Gen3D session, not committed (this repo's session commits it). The frontend it built is `prototype/fe3.c`
(adds frame-exact scripted input via `FE_SCRIPT`; touch coded, untested). Its screenshots are in runs/spike2/
(ignored: they show a commercial game's scene, never commit them).

## Verdicts (the agent's hand-back, numbers verbatim)

**Q1, memory reads: does not work (the app's RAM is unreachable).**
- The gdb stub does not come up: `use_gdbstub=true`, `gdbstub_port=24777` in `sdl2-config.ini`, `qt-config.ini` and
  `config.ini` under `<sys>/Azahar/config/` were all ignored (no listener, no GDB log line).
- `SET_MEMORY_MAPS` (env 36|0x10000) is sent only once, at frame 0, with 2 descriptors: 0x0FFFC000 (len 0x4000, flags
  4) and VRAM at 0x1F000000 (len 0x600000). No heap, linear-heap or FCRAM descriptor, never re-sent while the game
  runs. A read of 0x00100000 (app code) through the map fails. VRAM is readable but is GPU data. (So the source
  reading in `prior-art.md` was only half right for this 2126.2 build.)
- Not tried: parsing a `retro_serialize` savestate, which would contain FCRAM.

**Q2, speed on a real scene.**
- Plain `Gen3D.3dsx` picks layout A and never draws the 3D world; Gen3D's flipdev build (force=1) picks layout B and
  draws it, so every field number uses flipdev.
- Game: one commercial Gen-3 GBA game, run locally (not distributed); the save boots into the PC box menu; the script reaches the outdoor 3D field at about frame
  7600-9200.
- World build: the app logs "built in 184 s" by its own clock = about 12,000 `retro_run` calls (about 200 guest
  seconds) at roughly 275 emulated fps, so about 44 wall seconds (load not recorded). Qt reference: about 5 minutes.
- Guest-time check: the in-app clock advanced 15:56 to 16:04 over 32,000 `retro_run` calls = 535 guest seconds
  (matches at minute resolution); `voxel.log` "peaks over 600 frames" lines give about 0.53 app frames per `retro_run`,
  matching the app's HUD of about 32-37 fps. So one `retro_run` is one guest vblank; x real time = fps / 59.83.

| Setup (Vulkan) | Load average | Emulated fps | x real time | Cores / memory per instance |
|---|---|---|---|---|
| 1 instance, 3D field standing | 26.7 (16:07) | 334 | 5.6x | about 1.4 cores, about 0.5-0.8 GB |
| 1 instance, 3D field walking | 26.7 | 340-345 | 5.7x | same |
| 1 instance, standing, rerun | 68-96 (16:09-16:11) | 129 | 2.2x | 774 MB peak, 46 s user + 8 s sys over 91 s |
| 3 instances at once, standing | 58 rising to 90 | 136-138 each | 2.3x each | 665 MB each, about 0.57 cores each |
| 3 instances at once, walking | 58 rising to 90 | 172, then 87 each | 1.5-2.9x | same |
| Spike 1, idle picker (reference) | 9-15 | 3075 | 51x | about 1.4 cores, 1.2 GB |

Every row except the load-27 single-instance pair was taken under heavy contention from other sessions' windowed
Azahar instances; one vs three instances cannot be separated from the load (the three used only about 0.57 cores
each, so they were not core-bound themselves). Cleanest figures: 334-345 fps at load 27. One earlier run at about 450
fps had no `uptime` recorded. A clean re-measure on a quiet machine is still owed.

What it changes: the real field gain is about 6x real time (about 2x under heavy load), not 51x; still about 2-3x the
Qt fast profile's figures. A harness needs a flipdev-style build (or another way to force layout B). With no RAM
reads, RAM-peeking tests move to SD logs and screenshots or to `retro_serialize` parsing. A savestate or another save
would shorten boot scripts (this save lands in the PC box and needs B presses).

## The agent's own notes (FINDINGS2.md, as written)

# Headless Azahar follow-up (2026-11-12 15:46-16:20, 34 min)
## Q1 memory reads: DOES NOT WORK for app RAM
* Config route: sdl2-config.ini / qt-config.ini / config.ini with use_gdbstub=true, gdbstub_port=24777 in <sys>/Azahar/config/: ignored (no listener, no GDB log line). Core builds its settings from core options only.
* SET_MEMORY_MAPS (env 36|0x10000) IS sent, once, at frame 0, n=2: [0] flags=4 start=0x0FFFC000 len=0x4000; [1] flags=0x10 start=0x1F000000 select=0xFF800000 len=0x600000 (VRAM). No heap / linear heap / FCRAM descriptor, never re-sent while the game runs. Reading 0x00100000 (app code) through the map: no descriptor, fails. So guest app RAM (Gen3D's GBA EWRAM) is unreachable; VRAM is readable but is GPU data.
* Not tried: retro_serialize savestate parse (would contain FCRAM; untested).
## Q2
Guest app: Gen3D.3dsx (plain) stays layout A and never draws the voxel world (single session). Gen3D-flipdev.3dsx (the dev build az-i uses, force=1) picks layout B and draws the 3D world, so all field numbers use flipdev. Game = one commercial Gen-3 GBA game, run locally (not distributed). Slider not needed (voxSlider3d=0).
Boot path script (frames): wait 300, A, mash A/START 4200 frames (title -> Continue -> lands in the PC box menu), mash B 40x (out of PC), LEFT, DOWN x2 (a building door) -> outdoor field with 3D world at frame ~7600-9200. Script: run/x2.scr, z.scr; frontend fe/fe3.c (FE_SCRIPT, H/W/T/P lines; touch implemented via pointer device, untested).
World build (first boot, no pak): app's own log "built in 184 s"; ~12,000 retro_runs (~200 guest s) at ~275 emulated fps = ~44 wall s (load at the time not recorded; earlier spike saw 9-15). Qt reference ~5 min real.
Guest time check: HUD clock (guest RTC) advanced 15:56 -> 16:04 over 32000 retro_runs (535 s at 59.83 Hz) = consistent (minute resolution); app frame count from voxel.log "peaks over 600 frames" lines = ~0.53 app frames per retro_run (app runs ~32-37 fps guest, as its HUD says). So 1 retro_run = 1 guest vblank, x real time = fps/59.83.
| Setup | load avg at the time | emulated fps | x real | cores / RSS |
|---|---|---|---|---|
| 1 inst, 3D field standing (z1) | 26.7 (16:07) | 334 | 5.6x | ~1.4 cores, 0.5-0.6 GB (see below) |
| 1 inst, 3D field walking (z1) | 26.7 | 340-345 | 5.7x | same |
| 1 inst, standing (s5) | 68-96 (16:09-16:11) | 129 | 2.2x | 774 MB peak RSS, 45.8 s user+8.3 sys over 91 s |
| 3 inst at once, standing | 58 -> 90 | 136-138 each | 2.3x each | 665 MB each, 95 s user + 14 s sys over 191 s (~0.57 cores each) |
| 3 inst, walking | 58 -> 90 | 172 then 87 each (load spiking) | 1.5-2.9x | same |
| 3 inst early try (no field yet) | ~27-30 | 106-117 each while booting | 1.8-1.9x | |
| (spike 1) idle picker, 1 inst | 9-15 | 3075 | 51x | |
Everything below load ~27 is contaminated: other sessions' windowed Azahar instances ran at the same time (load 26 at 16:07, 96 at 16:09, 89 at 16:19). The clean figures are the 334-345 fps single-instance ones (load 27, still busy) and the 450 fps y1 run (load unrecorded). 3-instance vs 1-instance cannot be separated from the load; per-process CPU (0.57 cores each) says it is not core-bound itself.
Screenshots (400x480, top 3D world + bottom touch pad): run/field-standing.png, run/field-walking-1.png, run/field-walking-2.png (plus run/y1o/shot_014402.png).
## Effects on the 2-3 day estimate
* Speed gain over Qt is real but 6x in the 3D field (not 51x), 2x under heavy machine load. Frame-exact input works.
* Need Gen3D-flipdev-style build (or a way to force layout B) for the 3D field; plain .3dsx picks layout A.
* No RAM reads: any test that peeks GBA RAM must move to SD logs/screenshots, or try retro_serialize parsing: keep the 0.5-2 day line, lean to 2.
* The Gen3D boot lands in the PC box for this save; a savestate or a different save would shorten scripts.
