# Phase K plan, review 1

Reviewer: opus agent a1ccf7c7e336d0f39, 2026-11-13 10:19-10:28, read-only, on `docs/plans/phase-k.md` revision 0.
Saved verbatim by the main loop; only the reviewer's scratch-notes path is left out.

Verdict: the core of A4 and A1 is sound. The setting is applied before `System::Init`, the shared page is readable, and taking live CPU registers for the current thread and the saved context otherwise is correct. The plan still has 3 blockers: the host's version pin, the gate code that hardcodes core/PIN, and the missing exports-list entry.

## Facts checked (all hold)
- **A4 timing.** `retro_load_game` calls `UpdateSettings()` -> `ParseCoreOptions()` (citra_libretro.cpp:515) before `do_load_game` -> `System::Load` -> `Init` -> `Timing(... movie.GetOverrideBaseTicks())` (core.cpp:588). The movie returns -1 unless a movie is playing (movie.h:175), so `GenerateBaseTicks()` returns `init_ticks_override` when the type is Fixed (core_timing.cpp:27, 38-39). The option name `citra_init_ticks_override` exists (CMakeModules/GenerateSettingKeys.cmake:26). Changing the option mid-run only affects the next boot or reset.
- **A4 gate idea is real.** The shared page is mapped into every process, read-only (kernel/memory.cpp:167-178, process.cpp:252), so `IsValidVirtualAddress` passes (memory.cpp:824). `UpdateTimeCallback` is scheduled at 0 cycles when the kernel is built and then runs hourly (shared_page.cpp). The first write goes to `date_time_1`, because the counter is 0 and `0 % 2` selects `date_time_1` (shared_page.h:72). It sets `update_tick = timing.GetTicks()`, which is base + a small deterministic delta.
- **A1.** `SwitchContext` saves the CPU into `previous_thread->context` and loads the new one (thread.cpp:146-191). So the current thread's `context` is stale and the live CPU must be read; when a core idles, `current_thread` is null. The New 3DS profile runs 4 cores (core.cpp:453-456; options-default.txt sets `is_new_3ds=New 3DS`), and threads live in the manager of their processor_id (thread.cpp:408), so all 4 lists matter. `Process::GetThreadList` (process.cpp:614) does the same loop the plan describes.
- **Locking.** libretro calls are sequential (citra_libretro.cpp:657). Async workers only push to the thread-safe queue. No lock is needed between frames.
- **Section 2 is safe with a real `dl/azahar-src`.** build-core.sh deletes only `$ROOT/dl/azahar-src/build-src`, `build-core/build/externals/libressl`, `build-core/build.{exit,inputs}`, and a tarball it downloaded itself with a bad sha. Outside ROOT it only reads `/opt/homebrew/opt/openssl@3`, which is 3.6.5 with minos 15.0 today.

## Blockers
- **B1. The host refuses a lazpy.2 core.** host/pins.h:6 is `"-lazpy.1"` and version.c:23 compares exactly, so core.c:73 fails unless `LAZ_ANY_CORE=1`. Gate 2's "lazpy.1 states into lazpy.2" and "a lazpy.1 core gives NeedsLazpyCore" both need the host to accept both cores.
  Fix: accept a list of suffixes `{"-lazpy.1","-lazpy.2"}`. Update tests/test_version.c:20-22, tests/gate_f2.py:153,311 and the core.c:74 message.
- **B2. Gate 1's key-material check fails by construction with PIN-nokeys as default.** `gate_f2._inputs_findings` (tests/gate_f2.py:97-121, also :178) hardcodes core/PIN: it expects tarball = core/PIN's SRC_SHA256, pin = sha(core/PIN) and drop = core/PIN's list. A PIN-nokeys build records the other tarball, pin and drop. In addition, `keyblob_check` (release_check.py:124-136) needs a staged release dir with a zip, and `_window_findings` needs `dl/azahar-src/unpacked/...` (SRC_REL, :34).
  Fix: make `_inputs_findings` accept either pin, chosen by matching the `pin=` sha, and take that pin's tarball and drop. Gate 1 calls `gate_f2.keyblob_findings(<wt>/build-core, ...)` directly. Link `dl/azahar-src/unpacked` into the worktree read-only; build-core.sh never deletes it.
- **B3. Patch 0009 must add `_lazpy_threads` to src/citra_libretro/libretro.osx.def.** The link uses `-exported_symbols_list` with that file (src/citra_libretro/CMakeLists.txt:96), the same way 0001 adds its two exports. Without the entry, `dlsym` finds nothing and the core looks like lazpy.1. Also update release_check.py:44 `EXPORT_EXTRA` (check 3 FAILs otherwise) and gate_f2.py:238 `LAZPY_EXTRA`.

## Should
- **S1. Cap the tick value.** `GetGlobalTimeUs` computes `ticks*1000000` in s64 (core_timing.cpp:157), which overflows above about 9.2e12. Azahar keeps its random seed within 32 bits for this reason (core_timing.cpp:41). A negative value gives negative `executed_ticks` (:27, :164).
  Fix: host and core both refuse anything above 4294967295 (or a stated cap below 2^40), so it fails loudly. Plain `std::stoll("1x")` returns 1 rather than falling back, so the core needs a leading-digit check plus `pos == size()`, then a `static_cast<s64>`.
- **S2. Concrete A4 gate, with no test-app change.** Read u32 at 0x1FF81000 (`date_time_counter`, expect 1 after about 300 frames) and u64 at 0x1FF81048 (`date_time_1.update_tick`, shared_page.h:35-37 and :72). Assert v(1000000) - v(0) == 1000000 exactly, and v(0) < 2^20. Add the Random boot, plus a `--state` boot showing a loaded state keeps its own ticks.
  Docs: the override also shifts the guest clock by base/268 MHz (`GetSystemTimeSince2000` uses global ticks), and a played movie overrides it (core.cpp:589, movie.cpp:603).
- **S3. The ABI 4 bump leaks into state files.** state.c:286 writes `abi=AZH_ABI_VERSION`, and state.c:396 refuses meta abi above the host's own. States made by the branch host are therefore refused by v0.1.0's host, so "states keep loading across 3 and 4" holds only one way.
  Fix: add a separate `AZH_STATE_META_ABI` that stays 3, or document the one-way rule. Tests that pin 3: tests/python/test_memory.py:181-184 (`abi == 3`, `n_fields == 137`) and test_memory_live.py:239-240 (`"abi=3\n"`). The table limit `AZH_MAX_FIELDS` of 160 still fits.
- **S4. The host/Python wiring list is incomplete.** Missing: `_azh_threads` in host/libazhost.exports, the public `azh_threads` in api.c, an `"threads"` op in _worker.py:106, the signature in _host.py:23, the client method, and new layout rows plus `_abi.py`. `azh__mem_bind` (mem.c:26-44) must bind `lazpy_threads` separately and as optional, so a lazpy.1 core does not count as half-exported. azhost has only `run` and `layout` (azhost_main.c:163, 685), so `azhost threads` should be a `run --threads` flag that prints after the last batch.
- **S5. The deployment-target change does not reach an existing build tree.** The minimum is set only through the CMake cache: MAIN's build-core/build/CMakeCache.txt:453 holds `CMAKE_OSX_DEPLOYMENT_TARGET:STRING=11.0`, and Azahar sets 13.4 only when `NOT ENABLE_LIBRETRO` (CMakeLists.txt:48, 65). Changing the env var leaves an existing cache at 11.0; the worktree's fresh tree is unaffected, but main's next rebuild would silently stay at 11.0.
  Fix: add `-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0` to the cmake line (build-core.sh:111) and grep the cache value. OpenSSL is independent of this: it is Homebrew's prefix and already minos 15.0.
- **S6. Worktree safety needs more checks.**
  - `ROOT="${LAZPY_ROOT:-...}"` (build-core.sh:11): if `LAZPY_ROOT` is exported (USING.md:216 documents it), the worktree's script builds in MAIN. Run it with `env -u LAZPY_ROOT` or set it to the worktree explicitly.
  - Check that `dl`, `dl/azahar-src`, `dl/azahar-src/build-src` and `build-core` are not links: `[ "$(cd -P dl/azahar-src && pwd)" = "$(pwd -P)/dl/azahar-src" ]`. A linked `dl` gets past the plan's single test.
  - What the build needs from dl/: only the pin's SRC_FILE (`dl/azahar-src/src-nokeys.tar.xz`). A link to it is fine, because the script deletes a tarball only if it downloaded it.
  - `src.tar.xz` is needed only by mkrelease.sh:24-41, which does not run on the branch, so link it rather than copy key-bearing bytes.
  - openssl-src, sysarch-src, newlib-licence, font-licences and unifont-src feed mkrelease and release_check, not the build. Link them only if those tools run.
  - Tests need `dl/moltenvk`, the headers, and `build/testapp.{3dsx,elf}`. Copy those from MAIN rather than rebuild, to keep the pinned app sha.
- **S7. Commit before the build.** build.inputs gets `clean=no` when core/ or build-core.sh are uncommitted (build-core.sh:136), and gate_f2.py:106 wants `clean=yes`. Commit the patches on the branch before `--detach`.
- **S8. fetch.sh on the branch.** `REL_TAG` is shared by `--lazpy-core` and `--testapp` (fetch.sh:39-44). Moving it, or setting the core pin to TBD, breaks the test-app fetch and fresh clones after the merge.
  Fix: leave fetch.sh at v0.1.0/lazpy.1 until the next release stages; with B1 the lazpy.1 core still loads.
- **S9. Missing doc and notice edits.**
  - Patch 0000's notice lines: citra_libretro.cpp adds `lazpy_threads`, the .def line, "six" -> "seven" options (0000:17), and "-lazpy.1" -> "-lazpy.2" (0000:27).
  - NOTICES.md's patch-sha list, regenerated by mknotices.py:298 (0009 added, 0000/0002/0005/0008 changed).
  - core/README.md:10 (`LAZPY_REV=1`), :19, :22, :25 and a new 0009 row.
  - The PIN-nokeys header comment (:4) and STATUS.md:46 and :83.
  - Tell 3DPlatinum that "test by path" needs the worktree's Python and host too, since MAIN's host refuses lazpy.2.

## Nits
- **N1.** The 0008 fix belongs in 0008's own notice line (0008:7, "aes_keys.txt is not read"). 0000 has no such text.
- **N2.** build-core.sh never reads `LAZPY_REV`. Add an assert that 0005's suffix equals `-lazpy.$(pin LAZPY_REV)`, so the pin and the version string cannot drift; mkrelease.sh:49 and release_check.py:83 name the zip from it.
- **N3.** Struct fields: use the manager's `core_id` (thread.h, const). Report pid as 0xFFFFFFFF when `owner_process.lock()` is empty. Map `ThreadStatus` (thread.h:50-61) to names in the host, not by raw order. Consider an `is_current` flag bit and `cpsr` (the Thumb bit) for where.py; the size can stay fixed with packed fields.
- **N4.** Gate 4: take the stack range from the app's stack size below 0x10000000. Pin "two equal calls" to the same pid/tid set.
- **N5.** The plan's arm_interface.h:32-46 citation is really the accessors at :32-52, with the registers at :54-58.
