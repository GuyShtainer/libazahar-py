# Azahar 2126.2 unified tarball: source check (laz-100)

Measured 2026-11-12. Tarball sha256 verified (85c8b56f...a4cd26) before unpacking; 21,133 members, none absolute or
containing `..`. Unpacked to dl/azahar-src/unpacked/azahar-unified-source-2126.2/ (GIT-TAG 2126.2, GIT-COMMIT
219d743a1e698101fe1ab8bef43e6563126c3c27, matches the plan). Paths below are relative to that root. Nothing built or run.
Note: the archive holds 7 symlinks, all under externals/ (libusb, sdl2, dynarmic/zydis, zstd tests, soundtouch), none
touched by the libretro build; none escaped the folder on unpack (find -type l only, targets not followed).

| Fact | Plan says | Tarball path:line | Result |
|---|---|---|---|
| Export list | 25 `_retro_*` lines | src/citra_libretro/libretro.osx.def (grep -c '^_retro_' = 25) | holds |
| Version string | environment.cpp:270 | src/citra_libretro/environment.cpp:270 `info->library_version = Common::g_build_fullname;` | holds |
| Export list linked | CMakeLists.txt:96 | src/citra_libretro/CMakeLists.txt:96 (`-Wl,-exported_symbols_list`) | holds |
| Output name | CMakeLists.txt:32 | src/citra_libretro/CMakeLists.txt:32 `OUTPUT_NAME "azahar_libretro"` | holds |
| Visibility preset | CMakeLists.txt:363 | CMakeLists.txt:363 `CMAKE_CXX_VISIBILITY_PRESET default` | holds |
| deterministic_async_operations | settings.h:490-491 | src/common/settings.h:490-491 | holds |
| init_clock / init_time | :503 / :504 | src/common/settings.h:503 / 504 (init_time_offset :505) | holds |
| instant_debug_log | :659 | src/common/settings.h:659 | holds |
| core_settings.cpp option table | `option_definitions[]` | src/citra_libretro/core_settings.cpp:144 (table), :720 (v2 struct) | holds; none of the four settings has a row (grep) |
| ParseCoreOptions | defined in core_settings.cpp | core_settings.cpp:1130; called citra_libretro.cpp:113 and :228 | holds for the function; plan-check-3 cites :113 and :515, the second call is at :228 (differs, minor) |
| ReadBlock on unmapped | memory.cpp:188-195 | src/core/memory.cpp:186-195 (case Unmapped :187, LOG_ERROR, memset :193) in ReadBlockImpl (:174) | holds |
| WriteBlock on unmapped | 247-253 | src/core/memory.cpp:247-253 (logs, no write) | holds |
| IsValidVirtualAddress | 824-837 | src/core/memory.cpp:824-837 | holds |
| Public ReadBlock/WriteBlock decls | memory.h:558, 599, 673 | src/core/memory.h:558 (process overload), 577 (current process), 599, 621; no ReadBlock/WriteBlock at 673 | differs: 673 is not a Read/WriteBlock; use 577 / 621 for the current-process overloads |
| Exception sets status 14 | exception_handler.cpp:142 | src/core/arm/exception_handler.cpp:142; enum core/core.h:109 | holds |
| retro_run loop | citra_libretro.cpp:287-306 | src/citra_libretro/citra_libretro.cpp:287-306 (while !HasSubmittedFrame, RunLoop :288, DisplayMessage :304) | holds |
| Log filter level | citra_libretro.cpp:59 Debug | citra_libretro.cpp:59 `log_filter(Level::Debug)` | holds |
| SET_MEMORY_MAPS call | citra_libretro.cpp:416, 474 | only src/citra_libretro/environment.cpp:119 (the call); citra_libretro.cpp:741 is a comment | differs: plan's two citra_libretro.cpp lines not verified as the SET_MEMORY_MAPS sites; the call itself is in environment.cpp:119 |
| Savestate id/revision check | savestate.cpp:295-305 | src/core/savestate.cpp:295 (program_id check), revision compare :65-71 | holds (revision check is :71, not 295-305) |
| CI macOS libretro job | libretro.yml:174-196 | .github/workflows/libretro.yml:174-196; `CORE_ARGS: -DENABLE_LIBRETRO=ON` (:12); deps: `brew install spirv-tools` only | holds |

## Tree and submodules

- Size 429 MB unpacked (tarball 43 MB). 41 dirs under externals/, all non-empty (smallest: faad2, dllwalker, httplib,
  inih, json, libretro-common, lodepng, sdl2, sirit each hold 2 entries, i.e. a real checkout). All submodules present.
- Other submodules inside: dynarmic/externals (e.g. zydis) present.

## Build tools expected

- Root CMakeLists.txt:3 `cmake_minimum_required(VERSION 3.25)`; C++20 (:359). macOS deployment target set 14.0 / 13.4
  (:57, :65) unless libretro (:48 skips that block); CI sets MACOSX_DEPLOYMENT_TARGET 11.0.
- libretro build (-DENABLE_LIBRETRO=ON, CMakeLists.txt:165-178) is incompatible with Qt/SDL2 etc., which are turned
  off; Vulkan externals (spirv-headers, glslang, sirit) are skipped for libretro (:431 `ENABLE_VULKAN AND NOT
  ENABLE_LIBRETRO`). CI installs only spirv-tools. Boost/fmt/cryptopp etc. are vendored (USE_SYSTEM_* off by default).
- One old submodule minimum: externals/nihstro/CMakeLists.txt:1 `cmake_minimum_required(VERSION 2.6)`; CMake 4.x
  refuses below 3.5, so `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` is likely needed (as plan 2.7 already says). Four others
  declare 3.5 (ok).

## This Mac

- cmake 4.3.4 (needs the policy flag above); ninja at /opt/homebrew/bin/ninja; Xcode 26.3 (17C529).
- spirv-opt: /opt/homebrew/bin/spirv-opt present (matches the CI's spirv-tools).
- glslangValidator: not found. Gap only if Vulkan is built; libretro build skips it per above, so probably none.
- Homebrew sdl2, sdl2-compat present; not needed for libretro.

## Gaps

None that block. Watch: CMake 4 policy flag for nihstro; glslangValidator absent (likely unused).
