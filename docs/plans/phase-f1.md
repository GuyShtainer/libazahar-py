# Phase 1, step F1: our core's patches and the build script (item laz-110)

Opus step plan, 2026-11-12, **draft for Phase 1's two opus review loops. Nobody builds from it until the reviews
pass and the main loop launches the step.** Index of the phase: `docs/plans/phase-1.md`. For one sonnet builder
working alone in its own git worktree. It refines `docs/PLAN.md` section 2.7 and the "Phase F1" paragraph of
section 3; where they disagree on a goal, PLAN.md wins and the builder stops and reports. Where they disagree on a
source line number, `docs/research/azahar-source-check.md` (laz-100, measured in the unpacked tarball) wins.

Builder reads first: `docs/map/rules.md`, PLAN.md 2.4 and 2.7, `docs/research/azahar-source-check.md`,
`~/.claude/shell-golden-rules.md`. Python helpers: stdlib only, run with `python3 -I`.

## 1. Goal and gate

Goal: `core/PIN`, `core/patches/000N-*.patch`, `tools/build-core.sh` (plus one small Python helper) and the notices,
so one command turns Azahar's pinned unified source tarball into `build-core/azahar_lazpy_libretro.dylib`; the
Movie-playback check (PLAN 2.3) written into the item; then the first full build, launched detached. The build's
result is step F2's job.

Gate (PLAN.md section 3, "Phase F1"), made concrete. From the worktree root, after a clean `rm -rf
dl/azahar-src/build-src build-core` (the tarball may be seeded by copy, see step 0):
```
nice -n 10 tools/build-core.sh --configure-only ; echo "exit=$?"
```
Expected, in this order (the script prints full paths):
```
build-core: pin 2126.2 commit 219d743a1e698101fe1ab8bef43e6563126c3c27
build-core: have dl/azahar-src/src.tar.xz (43224348 bytes, sha256 ok)     <- "fetch ... ok" if it downloaded
build-core: unpacked 21133 members into dl/azahar-src/build-src/azahar-unified-source-2126.2 (path check ok)
build-core: patch 0001-lazpy-memory-exports.patch ok
...                                                                         <- one line per patch
build-core: applied <P> patches, 0 rejects
build-core: configure done: build-core/build
exit=0
```
Then three planted reds (shell rule 10), each exits non-zero with the quoted text:
1. `LAZ_CORE_PIN=<scratch copy of core/PIN, one sha256 digit changed, SRC_FILE pointing at a scratch copy of the
   tarball>` → `SHA256 MISMATCH`; the real tarball and tree are untouched.
2. A scratch copy of `core/patches/` with one context line altered, used through `LAZ_CORE_PATCHES=<dir>` →
   `patch <name> REJECTED`, printed by the dry run before the tree is touched.
3. `python3 -I tools/untar_checked.py <scratch>/evil.tar.xz <scratch>/out` on a hand-made tar holding `../evil` and
   `/abs` members → `REFUSED: ...`; `<scratch>/out` stays empty.

Then the detached launch: `tools/build-core.sh --detach` prints the pid, the log path and the exit-file path;
`kill -0 <pid>` succeeds. The builder does not wait for the build and ends its run.

## 2. Facts checked for this plan (reviewers: verify these)

"SRC" = the main checkout's pristine tree `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (laz-100: tarball
sha256 verified before unpacking, 21,133 members, none absolute or `..`, GIT-COMMIT
`219d743a1e698101fe1ab8bef43e6563126c3c27`, GIT-TAG `2126.2`, 429 MB, 41 externals all present). Lines below were read
there on 2026-11-12, by laz-100 or by this plan's author.

Tarball: `https://github.com/azahar-emu/azahar/releases/download/2126.2/azahar-unified-source-2126.2.tar.xz`,
43,224,348 bytes, sha256 `85c8b56fac703df04720125044b8ff887997911858a6cde545dfb1107ba4cd26` (plan-check-3 section 5;
laz-100). Already in the main checkout as `dl/azahar-src/src.tar.xz` (43,224,348 bytes). Top folder
`azahar-unified-source-2126.2`. 7 symlinks, all relative and inside `externals/` (libusb README, sdl2 android
project, dynarmic/zydis subprojects, soundtouch test lib, two zstd test bins): the path check must accept these.

Build (CI file `.github/workflows/libretro.yml` at the tag, job `libretro-macos`, :174-196; `CORE_ARGS` at :12):
`MACOSX_DEPLOYMENT_TARGET=11.0`; `cmake -DENABLE_LIBRETRO=ON -DCMAKE_OSX_ARCHITECTURES=arm64 . -B <dir>`;
`cmake --build <dir> --target citra_libretro --config Release`; `strip -x <dir>/bin/Release/azahar_libretro.*`. Only
extra install: `brew install spirv-tools` (here: `/opt/homebrew/bin/spirv-opt`). This Mac: CMake 4.3.4, Xcode 26.3,
Apple clang 17, 12 cores, 18 GB RAM, about 89 GB free disk, load average 86 at 17:03.
- Root `CMakeLists.txt`: :3 minimum 3.25; :44-45 default build type Release; :94-95 LTO defaults ON for Release;
  :109-111 the libretro-incompatible options (SDL2, Qt, web service, scripting, gdbstub, OpenAL, room, cubeb,
  libusb), force-disabled at :165-187; :161 `CITRA_WARNINGS_AS_ERRORS` default ON; :363 `CMAKE_CXX_VISIBILITY_PRESET
  default` (no visibility attribute needed on our exports); :431 Vulkan externals skipped for libretro (so the
  missing `glslangValidator` does not matter).
- `externals/nihstro/CMakeLists.txt:1` asks for CMake 2.6, which CMake 4 refuses: `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`
  is needed (laz-100). Always pass it.
- `src/citra_libretro/CMakeLists.txt`: :1 library dir `${CMAKE_BINARY_DIR}/bin/$<CONFIG>` (so the file is
  `build-core/build/bin/Release/azahar_libretro.dylib`); :32 OUTPUT_NAME `azahar_libretro`; :96
  `-Wl,-exported_symbols_list,${CMAKE_CURRENT_SOURCE_DIR}/libretro.osx.def` on Darwin.
- `src/citra_libretro/libretro.osx.def`: two `#` comment lines, then exactly 25 `_retro_*` lines (Mach-O names
  take the leading underscore). Anything not listed is hidden from `dlsym`.

Patch targets (SRC):
- `src/citra_libretro/citra_libretro.cpp`: :59 `CitraLibRetro() : log_filter(Common::Log::Level::Debug) {}`; :73
  `Common::Log::SetGlobalFilter(emu_instance->log_filter);` in `retro_init`; :217 `retro_run`; :218-223 a not-loaded
  game uploads a NULL 0x0 frame; :287-306 `while (!emu_instance->emu_window->HasSubmittedFrame())` with `RunLoop()`
  at :288 and `LibRetro::DisplayMessage(msg.c_str());` at :304; :371-373 `do_load_game()` calls
  `Core::System::GetInstance().Load(*emu_instance->emu_window, LibRetro::settings.file_path)`; :427 `context_reset`;
  :503 `retro_load_game`; `ParseCoreOptions()` is called at :113 (`UpdateSettings`) and :228 (option update in
  `retro_run`); :740 `retro_get_memory_data` returns NULL. It already includes `core/core.h`, `core/memory.h`,
  `core/hle/kernel/process.h`.
- `src/core/core.h`: `IsPoweredOn()` :193, `Kernel()` :280, `Memory()` :295 (`Memory::MemorySystem&`), `Movie()`
  :313 (`Core::Movie&`).
- `src/core/memory.h`: `CITRA_PAGE_SIZE = 0x1000`, `CITRA_PAGE_MASK` (:34-35). `MemorySystem` has
  `ReadBlock(const Kernel::Process&, VAddr, void*, std::size_t)` :558 and the current-process overload
  `ReadBlock(VAddr, void*, std::size_t)` :577; `WriteBlock(const Kernel::Process&, VAddr, const void*, std::size_t)`
  :599 and `WriteBlock(VAddr, const void*, std::size_t)` :621; `IsValidVirtualAddress(const Kernel::Process&, VAddr)`
  :673. Use the process overloads (558/599) with the same process object the page check used.
  `src/core/memory.cpp`: unmapped pages are zero-filled by ReadBlock (:186-195) and skipped by WriteBlock (:247-253)
  without failing; `IsValidVirtualAddress` (:824-837) is true for any non-Unmapped page. So every page is checked.
- `src/common/logging/filter.h`: `class Filter` :30, `ResetAll(Level)` :36, `SetClassLevel(Class, Level)` :38.
  `src/common/logging/types.h:44` `Debug_Emulated` ("Debug messages from the emulated programs").
- `src/citra_libretro/core_settings.cpp`: :14 `BaseKeys = Settings::HKeys`; :23-25 `citra_setting(key)` gives
  `citra_<key>`; :144 `option_definitions[]` (entries: key, desc, desc_categorized, info, info_categorized,
  category, values ending `{ nullptr, nullptr }`, default); :722-823 `RegisterCoreOptions` (the host answers option
  version 0, so the core sends V0 variables "desc; default|others", default first); :881 `ParseSystemOptions` is the
  pattern; :1130 `ParseCoreOptions()` calls the seven `Parse*Options()`.
- `src/common/settings.h`: :490-491 `deterministic_async_operations` (default false); :499 `async_fs_operations`
  (default **true**); :503 `init_clock` (enum :28-31 `SystemTime = 0, FixedTime = 1`); :504 `init_time` (default
  946681277); :506 `init_ticks_type` (enum :33-36 `Random = 0, Fixed = 1`); :507 `init_ticks_override` (default 0);
  :659 `instant_debug_log`. No libretro option sets any of them (grep of core_settings.cpp).
- Where those settings act: `src/core/hle/kernel/hle_ipc.h:306, 348` run async work synchronously when
  `deterministic_async_operations` is set; `src/core/hle/service/fs/fs_user.cpp:70, 155, 264, 318, 369, 414, 461, 510`
  take the synchronous FS path only when `!async_fs_operations` (eight FS calls); `src/core/core_timing.cpp:38`
  seeds the base ticks from `init_ticks_override` when `init_ticks_type == Fixed`, else from `std::random_device`.
  So repeatable runs need all five: PLAN 2.4's three plus `async_fs_operations = false` and `init_ticks_type =
  Fixed`. This plan adds the two (PLAN 2.4 aims at "deterministic guest I/O and a fixed start clock"; these are the
  rest of it). **Reviewer: confirm or cut.**
- `src/citra_libretro/environment.cpp:267-273` `retro_get_system_info`; :270 `info->library_version =
  Common::g_build_fullname;`. (SET_MEMORY_MAPS is sent only at environment.cpp:119; not patched, PLAN 2.7.)
- Movie (for the check, step 6): `src/core/movie.h:31` class `Movie`; Qt calls `movie.PrepareForPlayback(path)` at
  `src/citra_qt/citra_qt.cpp:1504`, before the boot, and `movie.StartPlayback(path)` at :1559, after it; the
  libretro glue calls neither. `src/core/movie.cpp:463-477` `ValidateHeader` returns `RevisionDismatch` (a warning,
  "playback may desync") when the movie's revision differs from `Common::g_scm_rev`; `StartPlayback` (:525-532)
  goes on unless the header is `Invalid`. So movies recorded on Qt Azahar 2125.1.2 would load with that warning.
  `src/core/core.cpp:589, 593` take the movie's override base ticks and init time at boot (why Prepare must come
  before Load).

Assumptions (not checked; the builder checks each and records the answer):
- A1: configure works without a `.git` folder (the tarball is meant to be built; GIT-COMMIT and GIT-TAG are there).
- A2: Azahar's configure downloads nothing for a libretro build (`FETCHCONTENT_FULLY_DISCONNECTED=ON` is passed
  anyway). The builder greps SRC's CMake files for `file(DOWNLOAD`, `FetchContent_Declare`, `ExternalProject_Add`,
  `CPMAddPackage` and records which a libretro build reaches.
- A3: 4 jobs plus LTO fit in memory beside other sessions' emulators. If the detached build dies in the LTO link,
  F2 reruns with `LAZ_CORE_LTO=OFF` (the script supports it).

## 3. What the patches do (PLAN 2.7; one concern per patch; `diff -u` against SRC, `a/` `b/` prefixes, `-p1`)

Every patched file gets, under its license lines, `// Modified by libazahar-py on 2026-11-12: <what changed>.
Licensed GPLv2 or later, as this file.` (a `#` line in the `.def`). Hunks stay GPLv2-or-later (rules.md 3).

1. `0001-lazpy-memory-exports.patch` (citra_libretro.cpp, libretro.osx.def):
   ```cpp
   // Guest memory by virtual address in the current process. Call only between frames.
   // 0 ok; -1 not running or no process; -2 a page in the range is unmapped; -3 bad arguments.
   extern "C" int lazpy_read_memory(uint32_t vaddr, void* buf, uint32_t len);
   extern "C" int lazpy_write_memory(uint32_t vaddr, const void* buf, uint32_t len);
   ```
   One static helper does the checks: `buf` non-null, `len` 1 to 0x4000000 (64 MiB), `(uint64_t)vaddr + len <=
   0x100000000`; `IsPoweredOn()`; a non-null `Kernel().GetCurrentProcess()`; `IsValidVirtualAddress(*process, page)`
   for every page from `vaddr & ~CITRA_PAGE_MASK` through `vaddr + len - 1` (at most 16,385 iterations). Then one
   `Memory().ReadBlock(*process, ...)` / `WriteBlock(*process, ...)`. No exception may leave an `extern "C"`
   function (wrap the body in try/catch returning -1). Append `_lazpy_read_memory` and `_lazpy_write_memory` to the
   `.def`.
2. `0002-lazpy-options.patch` (core_settings.cpp). Rows at the end of `option_definitions[]`, category
   `config::category::system`, keys from `config::citra_setting(BaseKeys::<name>)` declared in the `config::system`
   block. Defaults equal stock behaviour, so our core under a stock profile acts like stock:
   | key | values (first = default) | sets |
   |---|---|---|
   | `citra_deterministic_async_operations` | `disabled`, `enabled` | `Settings::values.deterministic_async_operations` |
   | `citra_async_fs_operations` | `enabled`, `disabled` | `Settings::values.async_fs_operations` |
   | `citra_instant_debug_log` | `disabled`, `enabled` | `Settings::values.instant_debug_log` |
   | `citra_init_clock` | `SystemTime`, `FixedTime` | `Settings::values.init_clock` |
   | `citra_init_time` | `946681277` (one listed value; the host may send any decimal) | `Settings::values.init_time` |
   | `citra_init_ticks_type` | `Random`, `Fixed` | `Settings::values.init_ticks_type` (override stays 0) |
   A new `static void ParseLazpyOptions(void)`, called last in `ParseCoreOptions()`; `init_time` via `std::stoull`
   in try/catch, falling back to 946681277. Note: `ParseCoreOptions` also runs mid-game (:228); these settings only
   matter at boot, which is fine.
3. `0003-lazpy-run-returns-on-error.patch` (citra_libretro.cpp): after :304 add `break;` and a one-line comment
   (the host still gets the SET_MESSAGE; `retro_run` returns instead of looping, so statuses 14 and 16 come back as
   plain stop reasons, PLAN 2.2). The next `retro_run` loops until a frame as before.
4. `0004-lazpy-log-filter.patch` (citra_libretro.cpp): :59 becomes `Level::Info`; before :73,
   `emu_instance->log_filter.SetClassLevel(Common::Log::Class::Debug_Emulated, Common::Log::Level::Debug);`.
5. `0005-lazpy-version.patch` (environment.cpp:270): `library_version` = `g_build_fullname` + `-lazpy.1`, held in a
   function-local `static const std::string` and returned with `.c_str()`.
6. `0006-lazpy-movie-play.patch`, if step 6's check confirms the facts above: `extern "C" int
   lazpy_movie_play(const char* path)` stores the path (call it after `retro_load_game`, before the host calls
   `context_reset`; returns -3 on null or empty, -2 if the file is missing, -4 if `ValidateMovie` says `Invalid`);
   `do_load_game()` (:371) calls `Movie().PrepareForPlayback(path)` before `Load` and `StartPlayback(path)` after a
   Success. About 20 lines; `_lazpy_movie_play` in the `.def`. A later rebuild costs 40-90 min of machine time,
   so a small hook goes in now. If the check finds a blocker, skip it and write the design into the item.

## 4. Files the builder creates (and owns)

| Path | Role |
|---|---|
| `core/PIN` | `KEY=value` lines, never sourced: `AZAHAR_TAG=2126.2`, `AZAHAR_COMMIT=219d743a1e698101fe1ab8bef43e6563126c3c27`, `SRC_URL=<the URL above>`, `SRC_SHA256=85c8b56fac703df04720125044b8ff887997911858a6cde545dfb1107ba4cd26`, `SRC_SIZE=43224348`, `SRC_FILE=dl/azahar-src/src.tar.xz`, `SRC_TOP=azahar-unified-source-2126.2`, `LAZPY_REV=1`. Read with `sed -n 's/^KEY=//p'`. |
| `core/patches/0001-...` to `0005-...` (`0006` if step 6 passes) | section 3 |
| `core/options-lazpy.txt` | profile lines our core's runs add on top of Phase A's `host/options-default.txt`: `citra_deterministic_async_operations=enabled`, `citra_async_fs_operations=disabled`, `citra_instant_debug_log=enabled`, `citra_init_clock=FixedTime`, `citra_init_time=946681277`, `citra_init_ticks_type=Fixed` |
| `core/README.md` | short and plain: what our core is, the pin, one line per patch, the licenses (patches GPLv2-or-later; any published binary ships with the unchanged tarball plus these patches, PLAN 2.7), the one build command. No speed claims. |
| `tools/build-core.sh` | POSIX `sh`, `set -eu`, ShellCheck clean, about 110 lines at most (shell rule 9); modes below |
| `tools/untar_checked.py` | `untar_checked.py <tar.xz> <dest>`: `tarfile` pre-scan refuses (prints `REFUSED: <member>`, exit 1, writes nothing) a member that is absolute, has a `..` component, is a device or fifo, is not under one single top folder, or is a link whose resolved target leaves that top folder; else `extractall(dest, filter="data")` and prints `top=<name> members=<N>`. Functions under 60 lines. |
| item `docs/status/lazpy/1-in-progress/110-step-f1-core-build.md` (the main loop moves it there from 2-next/ at launch) | only its "Lessons and notes" section: the Movie verdict, A1-A3 answers, configure time, pid and log path |

`build-core.sh`. `ROOT` from the script's location, or `LAZPY_ROOT` (as `tools/fetch.sh`); pin `LAZ_CORE_PIN`
(default `core/PIN`); patches `LAZ_CORE_PATCHES` (default `core/patches`). Shared stages, one `build-core:` line each:
refuse root (`id -u` is 0); read the pin; tarball: download to `SRC_FILE` with `curl -fsSL --retry 2` only when it
is missing or wrong, then check size and sha256 before anything else, and on a mismatch delete only a file this run
downloaded (copy `get`/`verify` from `tools/fetch.sh`); unpack with `untar_checked.py` into `dl/azahar-src/build-src/`
when the stamp `build-src/.unpacked-<sha256>` is absent; patches: when the stamp `build-src/.patched-<sha256 of the
patch files in order>` is absent, re-unpack fresh, `patch -p1 --forward --batch --dry-run` every patch first (a
failure prints `patch <name> REJECTED`, exit 1), then apply all and write the stamp; configure (section 2's command
plus `-S <tree> -B build-core/build -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON
-DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCITRA_WARNINGS_AS_ERRORS=OFF -DENABLE_LTO=${LAZ_CORE_LTO:-ON}`, default
generator as CI) into `build-core/configure.log`, printing its tail on failure. `rm -rf` only on `${ROOT:?}/dl/
azahar-src/build-src`. The script never touches `dl/azahar-src/unpacked/` (the main checkout's pristine reference).
- `--configure-only`: the shared stages, then `build-core: configure done: build-core/build`.
- `--build`: the shared stages, then `cmake --build build-core/build --target citra_libretro --config Release -j
  "${LAZ_CORE_JOBS:-4}"`, copy to `build-core/azahar_lazpy_libretro.dylib`, `strip -x` the copy, `codesign --force -s
  - <copy>` and `codesign -v <copy>` (strip can invalidate the arm64 linker signature), print `build-core: built
  <path>`. A `trap` writes the exit code to `build-core/build.exit` on every exit.
- `--detach`: refuse if `build-core/build.pid` names a live process; remove an old `build.exit`; start `nohup nice -n
  10 python3 -I -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' "$0" --build </dev/null
  >build-core/build.log 2>&1 &` (its own session survives the agent's shell; the exec chain keeps one pid); write
  `$!` to `build-core/build.pid`; print `build-core: started pid <pid>, log build-core/build.log, exit code ->
  build-core/build.exit`.
- no argument or an unknown one: usage, exit 2.
Why `-DCITRA_WARNINGS_AS_ERRORS=OFF`: our hunks are first compiled in the detached build, and one warning-as-error
there costs a 40-90 min rebuild; F2 greps `build.log` for warnings in the patched files instead. Why 4 jobs: 18 GB
of RAM shared with other sessions' emulators.

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

0. Setup (5 min). Own worktree, branch `phase-f1`. Seed the tarball by copy:
   `mkdir -p dl/azahar-src && cp <main checkout>/dl/azahar-src/src.tar.xz dl/azahar-src/` (the script re-verifies
   it). No core, MoltenVK or headers needed. Checkpoint: `git status --short` empty; `which cmake spirv-opt
   shellcheck patch` all resolve.
1. `core/PIN` and `tools/untar_checked.py`; make the evil tar in the scratchpad. Checkpoint: red 3 passes, and
   `python3 -I tools/untar_checked.py dl/azahar-src/src.tar.xz <scratch>/t` reports `members=21133` (then delete
   `<scratch>/t`).
2. Make the patches: copy each file you change from SRC (`<main checkout>/dl/azahar-src/unpacked/
   azahar-unified-source-2126.2/`, read-only, never edited) into `<scratchpad>/work/` with the same relative path,
   read around the cited lines, edit, `diff -u` into `core/patches/`. No C++ is compiled here; re-read each hunk
   for `extern "C"`, the `.def` underscore, the notice, and warnings you can see by eye (unused parameters, sign
   compares, narrowing). Checkpoint: 0001-0005 on disk, each `patch -p1 --dry-run` clean against a scratch copy.
3. `tools/build-core.sh`; run the gate command in the foreground, nice'd, 10-minute timeout. If configure fails, read
   `build-core/configure.log`, fix, rerun; note each fix and A1/A2 in the item. Checkpoint: section 1's output.
4. Reds 1 and 2 in scratch copies; `shellcheck -s sh tools/build-core.sh` and `sh -n` clean. Checkpoint: the three
   reds quoted in the notes.
5. `core/options-lazpy.txt`, `core/README.md`.
6. The Movie check, 15 minutes by the clock, reading SRC only: confirm section 2's Movie facts, check that
   `PrepareForPlayback`/`StartPlayback` need nothing the libretro glue lacks (a `System` already set up, the
   loader's program id), and whether the movie's program id is checked against the app. Verdict (yes / no / yes with
   conditions) and the call order go into the item. If yes: patch 0006, then rerun step 3 (the patch stamp
   changes, so it re-unpacks).
7. Launch: `tools/build-core.sh --detach`; `kill -0 <pid>`; read the first lines of `build-core/build.log` once.
   Checkpoint: the pid is alive. End the run.

## 6. Machine-sharing rules

- No emulator instance in this step. The heavy work is configure (foreground, `nice -n 10`) and the detached build
  (`nice -n 10`, 4 jobs). Never run the full build in the foreground; never wait on it.
- Never kill a process you did not start; never `pkill`/`pgrep` by a loose name. Never run anything as root.
- Never open a window (no Azahar app, no `open`, no Preview).
- Nothing from the download is run except Azahar's own CMake build of the exact pinned source (rules.md 2's one
  exception); `untar_checked.py` reads the tarball, it runs nothing in it.

## 7. Files the builder must not touch

Everything outside section 4: `host/`, `Makefile`, `testapp/`, `tests/`, `.gitignore`, `docs/map/*`, `README.md`,
`docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff, other items, `tools/fetch.sh`, `prototype/`, and the
main checkout's `dl/` (read and copy only). `.gitignore` lines it wants go in its report (section 8).
`build-core/` and `dl/` are already ignored (`build-*/`, `dl/`).

## 8. The builder's report

The gate output and the three reds as printed; pid, log and exit-file paths; the patch list with line counts; the
Movie verdict; A1-A3; anything in configure.log worth knowing; time per step; `.gitignore` lines for the main loop:
`*.tar.xz`, `*.tar.gz`, `*.orig`, `*.rej`.

## 9. Hours (agent wall time)

Builder 0.65 h (script and helper 0.2, patches 0.25, Movie check 0.15, configure and launch 0.05), plus the opus diff
review and the commit, about 0.35 h: **1.0 h**, as PLAN.md. Machine time (detached, not booked): the build, 15-25 min
quiet, 40-90 min at today's load, more if LTO's link swaps.

## 10. Review checklist (the opus diff review)

1. Every patch applies to a fresh unpack with `patch -p1 --dry-run`, no fuzz; each patched file has the dated notice;
   hunks touch only citra_libretro.cpp, core_settings.cpp, environment.cpp and libretro.osx.def (PLAN 2.7) and stay
   minimal.
2. Memory exports: `extern "C"`, both names in the `.def` with the underscore, arguments checked (null, zero, cap,
   2^32 wrap), every page checked before one Read/WriteBlock on the same process object, no exception escapes.
3. Options: defaults equal stock; keys from `citra_setting(BaseKeys::...)`; parsing cannot throw out of
   `ParseCoreOptions`; the two keys beyond PLAN 2.4 cite fs_user.cpp and core_timing.cpp:38.
4. `retro_run`: the one `break;` after :304. Log filter: Info, with `Debug_Emulated` at Debug. Version: ends in
   `-lazpy.1`, storage outlives the call. Movie hook (if any): Prepare before Load, Start after Success.
5. `build-core.sh`: `set -eu`, ShellCheck clean, every expansion quoted, size and sha256 checked before unpack, the
   pin never sourced, root refused, nice'd, detach survives the shell (setsid) and records pid and exit code, a
   second launch refused while the first lives, `rm -rf` only under `${ROOT:?}/dl/azahar-src/build-src`,
   `unpacked/` never touched. About 110 lines at most.
6. `untar_checked.py`: `-I`, stdlib, pre-scan before any write, `filter="data"`, accepts the 7 inside symlinks.
7. The gate output and three reds quoted; `git status` shows only section 4's files.
8. `core/README.md` claims nothing unmeasured; licenses as PLAN 2.7 and rules.md 3.
