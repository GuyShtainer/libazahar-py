# What Gen3D's emulator harness needs from a headless backend (2026-11-12)

From the Gen3D session's read-only inventory agent (afb3e9d3, sonnet). File references are in the Gen3D repo
(`3ds-toolkit/projects/Gen3D/tools/emutest/`). Gen3D is this tool's first user; its harness drives the windowed
Azahar Qt app today. The hours are that agent's estimates for one worker doing every step in order.

## Key finding

Gen3D's main scene runner (scenes.py) barely needs guest RAM. Input goes through the app's own SD control files
(scenes.py:521, grammar in Gen3D's source/control.h); pass or fail comes from the app's `voxel.log` `flip:` lines
(flipcheck.py:68, soakcheck.py:30-32) and the control log's `script done f=N` (scenes.py:485-504). Its only gdb uses
are `gdbio resume` (scenes.py:304, a workaround for the Qt app parking boots with the stub on; gone with libretro) and
`P1_SHOT=fb` (scenes.py:527-536; the frame callback replaces it).

## Mechanisms

| # | Mechanism (Gen3D files) | Needs guest RAM? | With libazahar-py |
|---|---|---|---|
| 1 | Qt profile pins (azctl.py:640-718): frame limit, fixed RTC, filters, gdb port, `is_new_3ds=false` for movies | no | core options (model, CPU clock); fixed RTC if the core has it |
| 2 | Boot/stop, SD staging, recent.bin, fixtures (azctl.py:1099-1670) | no | seed the real SD folder; stage_roms/recent.bin logic kept |
| 3 | Locks, machine slots, focus guard, bundle clones (azctl.py:153-530, instance.py) | no | dropped: plain processes with own folders |
| 4 | Curtain window for fast runs (curtain.swift, speed.py) | no | not needed: no pacing |
| 5 | CTM TAS movies, button and touch (ctm.py, movie fixtures) | no | a frame-indexed input list for the input callback; touch to be confirmed |
| 6 | SD control channel in (sdmc.py:77-200) | no | unchanged on a real SD folder |
| 7 | Netlogs and control log out (sdmc.py:205-300) | no | unchanged |
| 8 | `voxel.log` `flip:` lines (flipcheck.py, soakcheck.py, menucheck.py) | no | unchanged |
| 9 | Window screenshots (see.py, native.py: 2.25x upscale undone) | no | the core's 400x480 frame, cropped (bottom probably x offset 40) |
| 10 | Framebuffer via gdb (fbdump.py) | yes | not needed: the frame callback |
| 11 | gdb RAM reads of globals (fstate.py `g_fieldDbg`, gdbio.py) | yes | memory map reads, or an app log line |
| 12 | gdb reads in smoke.sh (:317-343 liveness/quit, :517-529 a pref, :610-612 a counter) | yes | memory map reads, or frames differ / log lines / consumed files |
| 13 | `see rec --with-state` | yes | per-frame images with the frame index |
| 14 | `gdbio resume` workaround | n/a | gone |
| 15 | savewarp save patching (savewarp.py) | no | unchanged |
| 16 | Picture judges (flipcheck.py, censusguard.py, compare.py) | no | unchanged; thresholds recalibrated to the core's image |
| 17 | Savestates | not used today | optional new tool |

## What a Gen3D adapter would replace and keep

Replace (Qt-specific): azctl.py, instance.py, curtain.swift, speed.py, see.py, native.py, gdbio.py, fbdump.py,
fstate.py, the gdb rows of smoke.sh, ctm.py's movie path. Keep: scenes.py logic and the scene JSON, flipcheck,
soakcheck, censusguard, compare, zoom, sheet, savewarp, games, the pure parts of sdmc.py.

## The agent's estimate (one worker, in order)

Common 40 h: the C frontend 10 (dlopen, env callbacks, unpaced loop, PNG on demand, input from a frame list, stop
conditions); a control protocol 3 (shot now, quit, run N frames); an `azctl` replacement 5; input scripts 3 (compile
ctm.py ops, touch included); rewire scenes.py 4; frame crop and judge recalibration 4; host tests 3; a parity run on
two games against Qt verdicts 6; docs 2. With memory reads +3 (43 h); without +9 (49 h). Part of this is Gen3D-side
work (the adapter), not this repo's: the split is for the plan to decide.

Risks it named: headless rendering (already shown working by spike 1); input and touch fidelity, and the Old-3DS pin
Gen3D uses to avoid an ir:rst movie desync; picture-judge drift (thresholds were set on the Qt capture).
