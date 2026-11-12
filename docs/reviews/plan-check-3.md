# Plan check 3: revision 2's changes against Azahar 2126.2 (laz-13)

Narrow check, 2026-11-12. Scope: only PLAN.md section 9's six claims listed by the brief. Source: raw files at tag
2126.2 (lightweight tag, points at commit 219d743a1e698101fe1ab8bef43e6563126c3c27, checked via the GitHub API) and
the release's asset list. Nothing built, nothing downloaded beyond single source files and the 102-byte checksum file.

## 1. Stop reasons and the detector: holds (one parenthetical to fix)

- `ResultStatus` (core/core.h:92-113): ErrorSystemFiles = 10, ErrorCoreExceptionRaised = 14, ShutdownRequested = 16.
- svcBreak: svc.cpp:1164-1165 logs then calls `Core::LogException`; exception_handler.cpp:142 sets status 14
  (skipped only if `g_ignore_exceptions_for_session`, :109, which the libretro core never sets).
- `RunLoop` resets status to Success at core.cpp:111 and returns it at :310; Signal::Shutdown and reset-during-setup
  return 16 (core.cpp:144, 150). Guest exits reach it through `RequestShutdown()` (core.h:174): APT close with no
  Home Menu (apt/applet_manager.cpp:1177), srv notification 0x203 (sm/srv.cpp:253), NS ShutdownAsync (apt.cpp:99),
  the reboot kernel state (svc.cpp:1478).
- `retro_run` (citra_libretro.cpp:287-306) loops on `HasSubmittedFrame()` and sends every non-Success result via
  `DisplayMessage`, which is plain `RETRO_ENVIRONMENT_SET_MESSAGE` (environment.cpp:169-174). `LibRetro::Shutdown()`
  (environment.cpp:164) has no caller. So one SET_MESSAGE handler sees all three cases. The detector is workable.
- Two handler details the plan should keep in mind (no plan edit needed, both are in 2.2/2.6 already in spirit):
  status 10 arrives as "Azahar was unable to locate a 3DS system archive: ..." with no "(N)", so a post-boot message
  that does not parse as "Fatal Error encountered (N)" must count as "any other N"; boot-time SET_MESSAGEs
  (citra_libretro.cpp:503-557) also carry no N and belong to 2.6's boot-failure path.
- Fix: the N = 16 parenthetical "and `retro_run` would never return" is not supported by the source. Frames are
  presented from the core's VBlank path (`SwapBuffers` sets `submittedFrame`, emu_window/libretro_window.cpp:68-71,
  195-202), and the system stays powered on after ShutdownRequested, so `retro_run` most likely keeps returning.
  Replace "(nothing follows a guest exit, and `retro_run` would never return)" with "(nothing useful follows a guest
  exit)". The `_exit` choice is unaffected. The same VBlank presentation is what makes the N = 14 claim ("the guest
  keeps submitting frames") hold regardless of what the guest does after svcBreak; gate C(e) confirms it.

## 2. Patch file list: holds

- libretro.osx.def lists exactly 25 `_retro_*` symbols; CMakeLists.txt:96 passes it as `-exported_symbols_list` on
  Darwin; CMakeLists.txt:32 hard-sets OUTPUT_NAME "azahar_libretro"; environment.cpp:270 sets `library_version =
  Common::g_build_fullname`. All as cited.
- Complete for two exports plus options: definitions in citra_libretro.cpp (`extern "C"`), names in the `.def`,
  option rows in `option_definitions[]` and assignments in `ParseCoreOptions` (both core_settings.cpp; the `config`
  key namespace lives in the .cpp, so core_settings.h needs no change), version in environment.cpp. The root
  CMakeLists.txt:363 sets `CMAKE_CXX_VISIBILITY_PRESET default`, so no visibility attribute is needed.
- Implementation note only: Mach-O names in the `.def` take the leading underscore (`_lazpy_read_memory`), as the
  existing 25 lines do.

## 3. The four settings: holds

settings.h:490-491 `deterministic_async_operations` (SwitchableSetting, default false), :503 `init_clock`
(enum `InitClock`, :28, default SystemTime), :504 `init_time` (default 946681277), :659 `instant_debug_log`.
core_settings.cpp has no option for any of them, so the stock core cannot set them; our patch must wire them
(an option row each plus a `Settings::values.x = ...` line in `ParseCoreOptions`). Keys exist: settings.h declares
each with `Keys::...`, and `HKeys` (used by core_settings.cpp's `citra_setting`) is generated from the same list
(common/setting_keys.h.in:15-27). `ParseCoreOptions` runs before load (citra_libretro.cpp:113, 515), as needed.

## 4. ReadBlock on unmapped pages: holds

memory.cpp:188-195: Unmapped logs an error and `memset`s zeros (no failure returned); :247-253 WriteBlock logs and
skips. `IsValidVirtualAddress` (memory.cpp:824-837) is true for any non-Unmapped attribute, so a per-page check is
the right guard. Implementation note: check every page from `vaddr` through `vaddr + len - 1` and reject a range
that wraps past 2^32.

## 5. Unified source tarball: holds

Release 2126.2 asset `azahar-unified-source-2126.2.tar.xz`, 43,224,348 bytes. The published
`azahar-unified-source-2126.2.tar.xz.sha256sum` reads `85c8b56fac703df04720125044b8ff887997911858a6cde545dfb1107ba4cd26`,
which matches PLAN.md's `85c8b56f...a4cd26` and GitHub's own asset digest. Not downloaded. `core/PIN` must hold the
full 64 hex digits above.

## 6. Touch rows: holds

Chain read at mouse_tracker.cpp:171-172 and mouse_tracker.h:53-55, core/frontend/emu_window.cpp:155-185, and
hid.cpp:292-293 (kScreenBottomHeight 240, kScreenBottomWidth 320, 3ds.h:18-19). numpy float32 recompute: the pointer
step lands on the exact frame pixel for every X 40-359 and Y 240-479 (p is never 0); `(float)y / 240 * 240`
truncates to y - 1 for exactly y = 63, 125, 126, 127; x is exact for all 320 columns.

## Verdict

Ready to split, after one wording fix: in 2.2's N = 16 bullet, replace "(nothing follows a guest exit, and
`retro_run` would never return)" with "(nothing useful follows a guest exit)".
