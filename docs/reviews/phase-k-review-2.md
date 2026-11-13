# Phase K plan, review 2

Reviewer: opus agent a1ec125776e22c832, 2026-11-13 10:32-10:42, read-only, on `docs/plans/phase-k.md` revision 1.
Saved verbatim by the main loop.

Verdict: the design holds, but revision 1 is not ready to run. I found 3 blockers: the worktree cannot build the host, the ABI 4 bump breaks two tests the plan does not list, and gate 4's stack check fails by construction for a libctru app. Gate 3's addresses and its "exactly 1000000" claim both check out against the 2126.2 source.

## Verified (holds)
- 40-byte struct: 10 u32 fields with no padding. tid and priority are u32, the `ThreadStatus` enum casts to u32, `ThreadContext` holds `cpu_registers[16]` and `cpsr`. `SaveContext` has no side effects (arm_dynarmic.cpp:294, arm_dyncom.cpp:114).
- Gate 3 offsets: `SharedPageDef` has `date_time_counter` at 0x0 and `date_time_1` at 0x40, and `update_tick` sits at +8 inside `DateTime`. So 0x1FF81000 is the u32 counter and 0x1FF81048 is the u64. The callback picks `date_time_1` when the counter is even (shared_page.cpp:130).
- "Exactly 1000000": `Timer` starts with `is_timer_sane = true` and `slice_length == downcount` (core_timing.h:228-232). So `ScheduleEvent(0)` in the Handler constructor lands at exactly base. The first `Advance` adds 0 cycles and fires the event, and `GetTicks()` returns `executed_ticks == base`. That makes v(0) == 0 and the difference exactly 1000000. The update repeats hourly, so the counter is 1 at frame 300.
- State compatibility across cores: Azahar refuses only on a `g_scm_rev` mismatch (savestate.cpp:301). Both trees take it from `GIT-COMMIT`, which the nokeys tarball keeps (GenerateBuildInfo.cmake:13). MAIN's core holds 219d743…. No patch changes any serialized class. The host only warns on a core-version mismatch (state.c:405).
- lazpy.1 under the suffix list: `is_lazpy` comes from the two memory exports. If `lazpy_threads` is bound as optional, lazpy.1 keeps everything except `threads()`, and options-lazpy.txt does not change.
- Seeding against build-core.sh: `-f` follows the tarball link and the script never deletes a file it did not download (:55-65). `rm -rf` reaches only the worktree's real `build-src` (:79-101). The unpacked folder is read only. The nokeys tarball's sha equals PIN-nokeys' `SRC_SHA256`. Note: the worktree `../libazahar-py-k` already exists and is seeded this way.
- Review-1 findings fixed as written: B1, B3, S1, S2, S7, S8, S9, N1, N2, N3. B2, S3, S4, S5, S6, N4 and N5 are open; see below.

## Blockers
- **B1. The host cannot build in the worktree (plan §2 seeding list).** The Makefile compiles with `-isystem vendor -isystem vendor/include` (Makefile:4), and `libretro.h`, `libretro_vulkan.h` and the Vulkan headers live in MAIN's git-ignored `vendor/`. The worktree has no `vendor/`, and the `dl/*-headers` links are only download caches. So gates 2 and 4 cannot run.
  - Fix: `cp -R <MAIN>/vendor <wt>/vendor`.
  - Do not run `fetch.sh` in the worktree. `--force` does `rm -rf "$DL/moltenvk/MoltenVK"` (fetch.sh:105), and `verify()` deletes the file on a mismatch. Both would reach MAIN through the `dl/` links.
- **B2. The ABI 4 bump breaks tests the plan does not list (§4, Host bullet on ABI).**
  - tests/python/test_state.py:114-116 builds `abi={_abi.AZH_ABI_VERSION}`, which becomes 4. The meta now says 3, so `assert line in text` fails.
  - tests/python/test_abi.py:38 sets `bad.abi = 4` and expects a HostError. Under ABI 4 it passes the check and the test fails.
  - Fix: test_state.py uses the state-meta ABI, either as a new `const.AZH_STATE_META_ABI` row with its `_abi.py` constant, or a literal 3. test_abi.py uses `AZH_ABI_VERSION + 1`. tests/host/test_statemeta.c:18 may stay.
  - Also register the `thread` prefix in `_abi._STRUCTS`. Otherwise `check_layout` raises "unknown row" (_abi.py, near the end).
- **B3. Gate 4's stack range cannot pass by construction (§6 gate 4).** libctru's `initSystem` (testapp.elf 0x10e0a0) moves sp to `fake_heap_start + __stacksize__`, with `__stacksize__ = 0x8000` in .data at 0x121024. It then stores that value back into `fake_heap_start` (0x136734). So the main thread's stack is in the app heap near 0x08xxxxxx, not near 0x10000000. Azahar's loader stack (3dsx.cpp:304, `DEFAULT_STACK_SIZE`) is abandoned.
  - Fix: take `top = u32 at &fake_heap_start` (from `nm build/testapp.elf`) through `emu.read`, and pass when `top - __stacksize__ <= sp <= top`.
  - Also define "main thread" as the lowest tid with the app's pid.

## Should
- **S1. The safety loop ignores failures except in its last pass (§2, line 34).** `for d in …; do A && B; done` returns only the last iteration's status, so a linked `dl` passes. Fix: `|| { echo "unsafe $d"; exit 1; }` inside the loop body.
- **S2. B2 of review 1 is half-fixed (tests/gate_f2.py:178-179).** `keyblob_findings` also reads core/PIN for `drop` and `OPENSSL_VERSION`. Keep core/PIN's drop list there (the three key headers and libressl) for the tree and `.o.d` checks. Switching it to PIN-nokeys' single `LIBAZAHAR-PY-REMOVED.txt` would quietly weaken the check. Use the chosen pin only for `_inputs_findings`' `drop`/`tarball`/`pin` keys. Make :153's `-lazpy.N` come from the pin's `LAZPY_REV`, not a new hardcoded value.
- **S3. Other environment variables can still redirect the build and the tests (§2, line 36; gate 2).**
  - Build: an exported `LAZ_CORE_PIN` or `LAZ_CORE_PATCHES` with an absolute path to MAIN builds the wrong inputs. That wastes a 60-minute build; gate 1 would catch it. Use `env -u LAZPY_ROOT -u LAZ_CORE_PIN -u LAZ_CORE_PATCHES -u LAZ_OPENSSL_PREFIX`.
  - Gate 2 / 3DPlatinum: `_paths.py` honours `LAZ_ROOT`, `LAZ_HOST`, `LAZ_PROFILE` and `LAZ_LAZPY_PROFILE` (_paths.py:17, 24, 48, 55). If any of them is exported, the worktree tests run MAIN's host. Unset them for gate 2, and tell 3DPlatinum to set `LAZ_ROOT=<wt>` (or `LAZ_HOST`) explicitly.
- **S4. The deployment target is set in two places (§5; tools/build-core.sh:15).** The script itself does `export MACOSX_DEPLOYMENT_TARGET=11.0`, which overrides any outer environment. Edit line 15 to 15.0. Grep the cache with `^CMAKE_OSX_DEPLOYMENT_TARGET:[A-Z]*=15.0$`, or pass `-DCMAKE_OSX_DEPLOYMENT_TARGET:STRING=15.0`.
- **S5. The work after the merge is not planned (§2, merge bullet).** After the merge, MAIN's `build-core/` is still lazpy.1. Gate code on main (version and symbols for lazpy.2, `_lazpy_threads`) then fails until a rebuild. The worktree's `build-core/` cannot simply be moved: CMakeCache.txt pins absolute source and build paths. Plan one more full build on main (machine time 30-60 min), or accept the worktree core as the gated binary for that release.
- **S6. The new Python with an old host fails with an AttributeError (python/libazahar/_host.py:37-40).** `load()` runs `getattr` on every prototype before `check_layout`, so `azh_threads` missing in a v0.1.0 host raises AttributeError, not an ABI HostError. Fix: catch AttributeError and raise HostError("host lacks azh_threads (needs the lazpy.2 host)").
- **S7. Wrong live-register citation (§4 A1, N5's "fix").** arm_interface.h:32-52 are the accessors of the saved `ThreadContext`, not the live CPU. The live ones are `GetPC` :104, `GetReg` :111 and `GetCPSR` :152. Simplest: call `GetCore(c).SaveContext(tmp)` (:178), then use one read path for both cases.

## Nits
- **N1. §6 gate 3 citation.** The header is `src/core/hle/kernel/shared_page.h`. `date_time_1` is at :75 (:72 is `mcu_hw_info`), and `update_tick` is at :35.
- **N2. §4 struct and prototype location.** `azh_thread` and `azh_threads` belong in `host/azhost.h`, next to `AZH_ABI_VERSION` at :9. api.c's layout table needs that header. Also update `azh_pure.h:12` and the `version.c:12` assert for the suffix list.
- **N3. §4 status names.** The host struct carries only a raw u32 `status`. Map the names in Python, keyed by value. Mapping "in the host" needs a string field nobody planned.
- **N4. Gate 3's state step proves little.** It only shows that the shared page's memory is restored. To back the claim "keeps its own ticks", add the reverse direction to gate 2 (a lazpy.2 state into the lazpy.1 core); the plan claims both ways but tests one.
- **N5. Docs to touch.** USING.md:218 (`LAZ_CORE_PIN` default `core/PIN`) and :247 need the new default. The gate_f2.py:526 comment "MAIN, also from a worktree" is now wrong, since a real `dl/azahar-src` makes `default_main` the worktree (which is correct).
- **N6. Merge conflicts.** Keep the docs/status item, docs/hours.tsv and the HANDOFF on main only, so the branch merge does not conflict with the progress files.

## Hour-saving
- **H1. Skip the ABI bump.** `check_layout` already fails an old Python against a new host on any new `thread.*` row ("unknown row"). A new Python against an old host fails at the `getattr` (S6) before the abi check is ever reached. So the bump to 4 adds no protection. Keeping `AZH_ABI_VERSION` at 3 drops `AZH_STATE_META_ABI`, B2's edits, and the changes at test_memory.py:183 and test_memory_live.py:239. Only `n_fields` changes. That saves about 0.2-0.3 h and removes the risk of S3 coming back.
- **H2. Drop the `flags` field.** The current thread of a core is exactly the one whose status is Running, so `is_current` can come from status. Keep 40 bytes with a reserved word, or go to 36.
- **H3. Gate 4 tools.** Take `.text` bounds and `fake_heap_start` / `__stacksize__` from `nm build/testapp.elf`. `testapp/build/testapp.map` already lists them, so no test-app change is needed.
