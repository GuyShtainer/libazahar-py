# Prior art for a headless 3DS test runner (2026-11-12)

From the Gen3D session's prior-art agent (aecf5c1e, sonnet, web and source reading). Cells it marked "?" or
"unverified" were not checked on the repo.

## Key finding: memory reads and Azahar's scripting RPC

- Azahar has a scripting RPC: `src/core/rpc/{rpc_server,server,packet}.cpp` and the Python client
  `dist/scripting/AzaharRPC.py` (GPLv2+), in the azahar-emu/azahar repo. Transport: UDP 127.0.0.1:45987. Requests:
  ReadMemory, WriteMemory, ProcessList, SetGetProcess, TakeScreenshot, ReadScreenshot (PNG or raw RGB888),
  GetPerfStats, SetFreeCam, SaveState, LoadState, SetInput (buttons, home, power, touch 320x240, circle pad ±0x9A, held
  until cleared). Requests on emulated state run on the emulation thread via `ProcessCoreRequests()`
  (`src/core/core.cpp` ~l.331).
- It is **not in the libretro build**. The server starts only under `#ifdef ENABLE_SCRIPTING` and
  `Settings::values.enable_rpc_server` (default false, `src/common/settings.h:699`), at `src/core/core.cpp` ~l.704.
  The root `CMakeLists.txt` ~l.109 lists `ENABLE_SCRIPTING` in `_LIBRETRO_INCOMPATIBLE_OPTIONS`; setting it ON with
  `ENABLE_LIBRETRO` is a CMake FATAL_ERROR. `src/citra_libretro/core_settings.cpp` has no RPC option.
- **libretro memory:** `retro_get_memory_data` returns NULL and `retro_get_memory_size` 0
  (`src/citra_libretro/citra_libretro.cpp` ~l.750-758). Memory is published through
  `RETRO_ENVIRONMENT_SET_MEMORY_MAPS` instead (`setup_memory_maps()`, ~l.319-376): heap, linear heap and new-linear
  heap as SYSTEM_RAM, VRAM as VIDEO_RAM, addressed by the current process's guest virtual addresses. A frontend can
  read guest memory by keeping that map from its environment callback. No RPC needed for reads. (Being checked in
  practice by spike 2, `spike-2-real-scene.md` when it lands.)
- Standalone Azahar: `src/citra_cli` exists but looks like a utility (compression, room), not a headless runner. No
  SDL no-window mode confirmed.

## Candidates

| Candidate | License | macOS arm64 | Headless HW render | Scripted input | Screenshots | Memory reads | Maintained |
|---|---|---|---|---|---|---|---|
| Azahar RPC + AzaharRPC.py (non-libretro builds) | GPLv2+ | yes (Qt app), needs a window | no, drives the GUI app | yes (buttons, touch, circle pad) | yes | yes, by guest VA | yes |
| Azahar libretro core, stock | GPL | yes | yes (spike 1) | via frontend | via frontend | via SET_MEMORY_MAPS | yes |
| libretro.py (JesseTG, Python, for core tests) | MIT | yes | OpenGL documented; Vulkan unverified | yes | yes | yes (memory maps unverified) | yes |
| RetroArch network commands / MCP server | GPL-3 | yes | needs a display context; unverified | not found in the MCP doc | yes | yes | very |
| stable-retro | MIT | ? | no (2D, software) | yes | frames | yes | yes |
| emutest (kivutar, headless libretro, Lua) | GPL-3 | ? | probably no | Lua | ? | ? | dead (2021) |
| ludo | GPL-3 | yes | full frontend, not headless | no | no | no | semi |
| Panda3DS | GPL-3 | yes | GUI emulator | Lua (unchecked) | ? | ? | yes |

Not found: an established CI harness for 3DS homebrew (search not exhaustive). Not checked: nanoarch-style minimal
frontends, pdretro, RetroPy.

## Verdict (the agent's)

1. Not new in pieces: Azahar's RPC and libretro.py cover parts. A prebuilt headless macOS arm64 runner for a
   Vulkan-based 3DS libretro core, many instances, aimed at 3DS homebrew testing, does not seem to exist.
2. Reuse: copy the RPC's request set and `AzaharRPC.py` semantics (GPLv2+, compatible with GPLv3) for a remote
   interface; read memory from the libretro memory map; try libretro.py as the Python layer first, and keep the C
   host only if libretro.py cannot host a Vulkan HW core.
