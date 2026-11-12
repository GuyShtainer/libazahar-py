<!-- Copied 2026-11-12 from the Gen3D session's scratchpad (agent a3f9c08b, sonnet). Paths: the scratch `.../azlr/dl/`
is this repo's `dl/` (ignored), `.../azlr/dl-mvk/` is `dl/moltenvk/`, `.../azlr/hdr/` is `vendor/` (ignored),
`.../azlr/fe/fe2.c` is `prototype/fe2.c`; the run folders and screenshots were not kept. -->
# Spike 1: Azahar libretro core headless (from Gen3D), 2026-11-12

## Verdict
**Works.** Azahar's libretro core (macOS arm64) runs Gen3D.3dsx fully headless (no window, no Dock icon, no display
needed) under my own ~300-line C frontend, with the **Vulkan** renderer through MoltenVK. Both screens render correctly.
Measured **~3000 retro_run calls per wall second (about 50x real time)** on the idle Gen3D ROM-picker screen, one
instance, 65 s, on a busy machine (load 9-15). 3 instances at once: ~1200 each (~3600 total, so total throughput is
roughly capped, not 3x). Software renderer also works but is slow (30-44 fps = 50-74 % of real time).
Biggest caveat: guest-time calibration (see "Speed" below) is circumstantial, and the gdb-stub/RAM-read part of the
harness has no equivalent in the core (see "What the harness needs").

## Part 1: survey (web + GitHub API, 2026-11-12)
| Candidate | macOS arm64 | New 3DS | .3dsx/.cia | GPU accuracy | Speed | Scripting hooks | SD folder | Licence | Maintenance |
|---|---|---|---|---|---|---|---|---|---|
| **Azahar libretro core** | yes, official release asset `stock-core.zip` (2126.2 stable, 2127.0-rc2 on 2026-11-06) https://github.com/azahar-emu/azahar/releases | yes, option `citra_is_new_3ds` (default New 3DS) + `citra_cpu_clock_percentage` | .3dsx/.3ds/.cci/.cxi/.elf/.app load (docs list no .cia; Gen3D .3dsx loads fine) | same GPU emulation as Azahar Qt (Vulkan/MoltenVK; options Auto/Vulkan/Software; NO OpenGL on macOS) | fast, see below | libretro API: input callback, video callback, env vars; memory API returns 0 size | `<system or save dir>/Azahar/sdmc/` (option `citra_use_virtual_sd`, `citra_use_libretro_save_path`) | GPLv2+ | very active, 2127 RCs a week old |
| Azahar standalone, headless/SDL build | Release assets only Qt (`azahar-macos-*`); the repo has an SDL frontend (`azahar` binary via `ENABLE_SDL2_FRONTEND`) but no prebuilt macOS asset (not verified a build works headless; SDL still opens a window) | yes | yes (.cia too) | reference | window-paced like Qt unless hidden | gdb stub, config file | native | GPLv2+ | active |
| Panda3DS (libretro core + SDL/Qt) | yes, v0.9 MacOS-SDL/-Qt zips | not clearly supported | .3dsx yes | HLE, "early stage", many games fail, OpenGL/Vulkan(MoltenVK) | decent | libretro, Lua scripting in its own frontend | yes | GPLv3 | last tag v0.9 Dec 2024, repo pushed Nov 2026 |
| Citra libretro (old) | docs: no working macOS build | partial | yes | old Citra | n/a | libretro | yes | GPLv2 | dead (Citra archived 2024) |
| Mandarine, Lime3DS, Borked3DS, Torzu etc. | not checked in depth (limited time) | | | | | | | GPL | Azahar is the merged continuation of Lime3DS/PabloMK7; forks not worth it |
Pick: **Azahar libretro core**, because it is the same emulator Guy already tests against (same GPU/HLE behavior as
the Qt 2125.1.2), is official, signed-by-CI prebuilt for arm64 mac, and exposes the New 3DS switch.

## Part 2: what I built and ran
* Core: .../scratchpad/azlr/dl/azahar_libretro.dylib from Azahar's releases page
  sha256 `[stock core sha256]` (version 2126.2, Mach-O arm64, 19 MB, links only system frameworks, no GL/Vulkan inside).
* MoltenVK 1.4.2 (needed by the Vulkan path, the core brings none): https://github.com/KhronosGroup/MoltenVK/releases/download/v1.4.2/MoltenVK-macos.tar
  sha256 `f95765a6229cb7b915990a2890ce12ebe36a730b021545d3d52ae69ce4c4024e`, unpacked in .../azlr/dl-mvk/.
* Headers (libretro.h, libretro_vulkan.h, Vulkan-Headers main) in .../azlr/hdr/.
* Frontends in .../azlr/fe/: fe.c (GL/CGL offscreen + software path; GL context is useless, see below) and **`fe2.c`** (the real one: adds Vulkan; build:
  `cc -O2 -I hdr -I hdr/include -o fe2 fe2.c -framework OpenGL -lz`).
  Run: `MVK_LIB=<libMoltenVK.dylib> OPT_citra_graphics_api=Vulkan fe2 core.dylib app.3dsx <sysdir> <outdir> <seconds> <shot frames comma list>`.
  Any core option can be set as env `OPT_<key>=value`; unset options default to the first listed value.
* Why C and not Python ctypes: the core calls variadic log callbacks, needs several env callbacks and the Vulkan negotiation/readback structs; C against the real headers was safer.
* Why not an OpenGL FBO as asked: this macOS build offers only `Auto|Vulkan|Software` (log: `Using Vulkan hw renderer`); macOS GL is 4.1 and the core does not offer it. `SET_HW_RENDER` arrives with type 6 (VULKAN). So the
  frontend answers `SET_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE` (core gives `create_device`, v2, no create_instance), makes a VkInstance itself (no surface, no swapchain, no window), lets the core create the device, hands back
  `GET_HW_RENDER_INTERFACE`, records `set_image`, and at the requested frames does vkCmdCopyImageToBuffer into host memory and writes a PNG (own zlib PNG writer). Offscreen, nothing opens a window.
* Run directories: .../azlr/run/ (logs `v3.log`, `m1-3.log`, `s1.log`). Guest app was `Gen3D's own `Gen3D.3dsx`` (read only).

## Screenshots (400x480 = top 400x240 above bottom 320x240 centered, default layout; I viewed them, both screens correct: top "CHOOSE TWO GAMES / No games found", bottom Rescan + Start without a game buttons)
* Vulkan: .../azlr/run/v2o/shot_000300.png, .../run/v3o/shot_000600.png, `shot_060000.png`, `shot_150000.png`
* Software: .../azlr/run/o2/shot_000600.png
Frame-by-frame boot (frames 5/15/30/45/60/90) in run/b1o (Vulkan) and run/b2o (software) show the menu appears by frame 30 in both, i.e. one retro_run is about one guest frame in both modes.

## Speed (retro_run calls per wall second, guest vblank = 59.83 Hz; app on the Gen3D menu screen, which is nearly idle)
| Setup | emulated fps | vs real time |
|---|---|---|
| Qt Azahar window, default (SPEED.md) | ~60 | 94-107 % (display-paced) |
| Qt + frame_limit=0 + curtain window (SPEED.md, GBA game movie, heavier) | 200-540 | 3.4-9x |
| **Headless Vulkan, 1 instance, 65 s** (`v3.log`) | **3075 avg (2880-3170 per 5 s)** | **~51x** |
| Headless Vulkan, 3 instances, 30 s each | 1202 / 1199 / 1237 | ~20x each |
| Headless Software renderer, 1 instance | 30-44 (avg 30 over 75 s, 37 over 20 s) | 50-74 % |
Process cost (Vulkan, 1 instance): user 61 s + sys 29 s over 65 s wall (about 1.4 cores), 1.2 GB RSS. Note this was a light screen; a 3D-heavy Gen3D scene will be far lower, and "50x" mostly comes from idle skipping, so the GBA-game-movie-like comparison must be redone with a real scene. Guest-time calibration: the audio sample counter was 0 (app does not use DSP), so I could not read guest seconds directly; evidence that retro_run is one guest frame is the identical boot progression vs the software run at frames 5-90. Treat the 50x as "upper bound for an idle UI" until checked against a guest clock (e.g. frame counter the app writes to sdmc, or a TIME read).

## What the current harness needs vs the core
| Harness need | Libretro core |
|---|---|
| Framebuffer reads via gdb stub | Replaced and better: the frontend gets the composited frame every retro_run (my Vulkan readback). Bottom/top screens are one 400x480 image in default layout (`citra_layout_option`, `citra_resolution_factor` adjustable up to 18x). Raw per-screen framebuffer-from-RAM reads are not offered. |
| RAM reads/writes via gdb stub | **Not available**: `retro_get_memory_data/size` return 0/NULL for ids 0-4 (core says memory monitoring unsupported). The binary has `Debug.GDBStub`/`use_gdbstub` strings but no core option; untested whether it can be enabled via the Azahar config file in the system dir (worth 15 min to test). Without it the harness must use the app's own logs/SD files or screenshots. |
| Emulated SD folder | Yes: `<systemdir>/Azahar/sdmc/` (real directory; Gen3D already created `sdmc/Gen3D` there). Pre-seed control files before launch, read log files after/during. NAND under `<systemdir>/Azahar/nand`. |
| Input injection | Yes, trivially: my `instate()` callback can return any joypad/touch/C-stick value per frame (core options `citra_analog_function`, touch via pointer/mouse device). Frame-exact, scripted, deterministic. Not implemented in fe2 (stub returns 0). |
| New 3DS model | Yes: `citra_is_new_3ds` (default New 3DS), and cpu clock `citra_cpu_clock_percentage` up to 400. Log shows the app's `ConfigureNew3DSCPU` ptm:sysm call is unimplemented (same as in Qt Azahar). |
| Frame limit / pacing | None: the frontend decides, no frame limiter, no display link. |
| Audio | App produced no samples; `citra_audio_emulation` hle|lle; DSP firmware matter as before. |

## Blockers / risks
1. No RAM access (above): the biggest gap for the existing gdb-stub-based tests.
2. Vulkan negotiation needs a MoltenVK dylib supplied by the frontend (1.4.2 used; fine on this Mac). Instance flags: portability enumeration NOT needed with direct dylib load.
3. Guest-time calibration unproven; 3 instances share a throughput ceiling (GPU/MoltenVK or memory), not 3x.
4. Core option "Software" is a slower but dependency-free fallback.
5. 2126.2 stable core vs Qt 2125.1.2: slight version difference, results should be cross-checked once on a heavy scene.
6. fe2.c readback assumes the image is sampled-only-safe for transfer-src (worked on MoltenVK; no validation layer run).

## Rough work to make it the harness backend (my estimate)
* Input scripting (per-frame pad/touch table from a script file or stdin), save/exit control, a JSON/CLI front (`azhl run --frames N --shots ... --opt k=v --sdmc dir`): 0.5 day.
* Clean up fe2 (no leaks in readback, reuse buffer, proper shutdown, retro_serialize for savestates if wanted): 0.5 day.
* Replace RAM-based checks: test enabling the gdb stub via config, else rewrite those checks to use SD logs/screenshots/`retro_serialize` parsing: 0.5-2 days depending on how many tests peek RAM.
* Multi-instance runner + guest-time calibration + comparison against Qt on a heavy scene: 0.5 day.
Total about 2-3 days for parity with screenshots/input/SD; more only if RAM peeking is mandatory.

Not touched: Qt Azahar app, tools/emutest/az-*, ~/.cache/azctl, the repo. No commits.
