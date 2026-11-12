# Phase 3 plan, review 1 (revision 0)

Opus review, 2026-11-12. Plan: `docs/plans/phase-3.md` (index), `phase-e.md`, `phase-f2.md`, `phase-g.md`, all
revision 0. Checked against: Azahar source at `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (SRC),
`core/patches/0000-0006` (PATCHES), Phase 1 code on main, Phase 2 plans (revision 2, final), step C's worktree
`../libazahar-py-c` (C1 0651a8d + uncommitted C2/C3), step D's worktree `../libazahar-py-d` (b24c436), and
`docs/reviews/phase-2-c-as-built.md`.

Grades: **blocker** (the build fails or a gate cannot be met as written), **should fix** (a builder would ask, or a
gate is weaker than it says), **nice** (cheaper or clearer).

Counts: 5 blockers, 9 should fix, 12 nice. Verdict in section 9.

## 1. Blockers (a gate cannot be met as written, or the builder must stop)

- **B1. `tests/python/conftest.py:42-51` (D's `host_paths`) ignores `LAZ_CORE`; F2 and G gate on it.**
  phase-f2.md:28-29 (f4 `LAZ_CORE=OURS ... pytest`), :111-112 (`core_kind` "by the same `nm` test on the core
  `host_paths` resolves"), phase-g.md:24-35 (gates 2-4 select the core with `LAZ_CORE`). D's fixture hard-codes
  `REPO/dl/azahar/azahar_libretro.dylib` and checks only that file. So `core_kind` is always "stock"; if a D3 test
  passes `core=host_paths.core` the run is on stock whatever `LAZ_CORE` says (f4 "pytest on OURS" silently runs
  stock), and if it passes no core the Emulator runs ours while every branch asserts the stock expectations.
  Fix (F2, conftest.py is F2's): `host_paths.core = _paths.core_path()` (honours `LAZ_CORE`), the existence check
  on that path, `core_kind` from it; the first line of every live run prints `core=<path> kind=<kind>`; and F2's
  report lists which D3 tests pass `core=` explicitly. Better still, see B4 (explicit core fixtures).
- **B2. phase-e.md:31, 193 (g4: every worker reports nice `10`) cannot pass under its own command.** The gate runs
  `nice -n 10 python3 -m pytest ...` (phase-e.md:21, 264) and D's worker calls `os.nice(10)`, an *increment*
  (`python/libazahar/_worker.py:111`), so the worker sits at 20 (shown as 19/20 by `ps`), never 10. The same doubles
  the speed table's workers (phase-e.md:198, 233) and F2's/G's batches. Fix: g4 asserts `nice >= 10`; drop
  `nice -n 10` from the pytest and table commands (the parents are light, the workers nice themselves), or make the
  worker set an absolute level (`os.setpriority(os.PRIO_PROCESS, 0, max(10, os.getpriority(os.PRIO_PROCESS, 0)))`,
  F2 owns `_worker.py`). The table records the workers' nice value per row either way.
- **B3. phase-f2.md:29-30, 213 (f4's exit-path grep) inspects stock artefacts.** F2-2 runs gate C and pytest on OURS,
  then on STOCK, into the same `runs/c-gate/<id>/` and `runs/d-pytest/<test>/` folders (D's `workdir` fixture
  deletes and remakes them, conftest.py:54-63), and only "then grep[s] the host.logs". Stock's C(f) and D's exit
  test write the exit-path line by design (`host/env.c:44`, "[error] the guest stopped the host; the host process
  exits now"), so the grep either FAILs on stock's lines or no longer sees ours. Fix: `batch.sh` greps right after
  each OURS part and writes `runs/f2/exitpath-ours.txt` (or moves `runs/c-gate` and `runs/d-pytest` to
  `runs/f2/ours-*` before the stock parts).
- **B4. phase-g.md:36-38 (gate 4, `LAZ_CORE=OURS ... pytest tests/python` "0 skipped") includes the stock test m5**,
  which on OURS must skip (or fail); the phase-end suite (phase-3.md:146) has the mirror problem for m1-m4 on stock.
  Fix (also cheaper): F2's conftest gains `lazpy_core` and `stock_core` session fixtures (OURS =
  `LAZ_LAZPY_CORE`, else `MAIN`-relative `build-core/azahar_lazpy_libretro.dylib`; fail under
  `LAZ_REQUIRE_EMULATOR=1` when missing), and G's live tests pass `core=` explicitly. Then one pytest run covers
  m1-m5 on both cores, gate 4 holds with 0 skipped, and G2's batch shrinks from four parts to two (section 6).
- **B5. phase-g.md:121, 195-196, 209 (`test_mem.c` in `make test-host`) needs files G does not own.** C's
  `Makefile:40-48` builds `build/test-host` from a fixed `TEST_SRC` list of pure modules plus every
  `tests/host/*.c`, with one runner `tests/host/test_main.c` whose entry list is `tests/host/test_main.h:8-15`. A
  "pure half" of `host/mem.c` cannot link there (mem.c also holds `dlsym`, `azh_g`, `azh_fail`, which live in
  api.c, not in `TEST_SRC`), and registering `test_mem()` means editing `test_main.c`/`.h`, which are in no row of
  phase-3.md section 3 ("No builder edits a file outside its rows", phase-3.md:117). Fix: the pure functions go in
  a new pure `host/watch.c` (no "or"), added to `TEST_SRC`; add `tests/host/test_main.c` and
  `tests/host/test_main.h` (one line each) to G's rows.

## 2. Should fix

- **S1. Timed runs can still overlap at three seams** (phase-3.md:71-74, 134-135, 141-143; phase-g.md:253-255).
  (a) "fixes by the resumed F2 builder" after F2's as-built review run while E2 is timing (E is resumed at "F2
  done", before the review); (b) the same for fixes after E's as-built review while G2 runs; (c) G waits at most
  90 min for `e-speed.rc`, but E2's own bounds are 45 min (live tests) + 60 min (table) = 105 min, and the brief
  does not say what G does on a timeout. Fix: one rule in section 2: "any emulator rerun after an as-built review
  is a timed part and queues behind the one running (it waits on that part's rc file)"; G's bound becomes 120 min,
  and on timeout G ends its run with a "waiting for E2" report (it never starts G2 on its own).
- **S2. E2's our-core rows run without P8** (phase-3.md:49-50, 82-83; phase-e.md:267-270). E's worktree is made
  at main before F2 merges and E is resumed at "F2 done", so `speed_table.py --core OURS` runs our core with the
  stock defaults (patch 0002 registers all six options with stock defaults, `core/patches/0002-lazpy-options.patch`
  lines "Defaults equal stock behaviour"), not as users will run it (`instant_debug_log` flushes the log on every
  entry, `common/logging/backend.cpp:353-357`, which costs time on a log-heavy app like the test app). Fix: resume
  E only after `step-f2` merged, with `git merge --no-edit main` in `../libazahar-py-e` first (E1 touches no F2
  file, so it is clean; E2 then also gets F2's conftest fixes); the table records the effective option set per core
  (the `host.log` option dump). Costs about 0.2 h of calendar on E2 only; G1 runs meanwhile.
- **S3. phase-f2.md:167-168 (r1 strips `wall=`, `fps=`, `wall_ms_max=`).** The summary as built is `frames= wall=
  fps= shots= stop= first= last= vblanks= wall_ms_mean= batch= msg=` (`../libazahar-py-c/host/azhost_main.c:564-
  567`; C as-built deviation 2), so r1 FAILs on `wall_ms_mean`. Fix: strip `wall=`, `fps=`, `wall_ms_mean=`; correct
  row C6 (phase-3.md:200) the same way.
- **S4. phase-e.md:117-119 (`png.c` logs `png level=<n>`) breaks the pure build.** `host/png.c` is pure (its line 1;
  it includes only stdlib and zlib) and is in `TEST_SRC` (`Makefile:40`); a call to `azh_log` there fails the
  `build/test-host` link, gate 1. Fix: `png.c` gains `int azh_png_level(void)` (reads `LAZ_PNG_LEVEL` once with
  `getenv`/`strtol`, returns 1 on a bad value and remembers that it was bad); `run.c` writes `png level=<n>` (plus
  `bad LAZ_PNG_LEVEL` when so) once per process at the first batch; the prototype is one line in
  `host/azh_pure.h`, so add `azh_pure.h` to E1's rows (G edits that header later, on top of E1, as for `run.c`).
- **S5. phase-e.md:63-64, 174-178: when `LAZ_SLOT_DIR`/`LAZ_MAX_INSTANCES` are read, and the fixture's order.**
  The live fixture needs 3 real slots *and* a private folder in one process. Say: `slot_dir()` and `cap()` read the
  environment on every call (never at import); the fixture first acquires the 3 real slots with `LAZ_SLOT_DIR`
  unset, then `monkeypatch.setenv`s the private folder and cap. Without this a builder caching at import gets a gate
  that silently tests the real folder.
- **S6. phase-3.md:142-143 (`git merge main` into `../libazahar-py-g` "at E done") runs while G's builder may be
  editing or timing in that tree**, and any E as-built fix to an E1 file (`_client.py`, `run.c`, `png.c`,
  `__init__.py`) then conflicts with G's edits on top of E1. Fix: merge main into G's worktree only at "G done",
  before G's review; E's as-built fixes to E1 files are applied in G's worktree by the main loop (or held until
  step-g merges), never on step-e after G launched.
- **S7. ABI 3 refuses every ABI-2 state (risk 7, phase-3.md:241-242) for no reason in the state's content.**
  `../libazahar-py-d/host/state.c:395` requires `meta.abi == AZH_ABI_VERSION`; ABI 3 only appends batch/result
  fields and the watch area, none of which a state holds. Gen3D would remake its states for nothing. Fix: G changes
  that one check to `2 <= meta.abi && meta.abi <= AZH_ABI_VERSION` (add `host/state.c`, that line only, to G's rows;
  phase-3.md:119 lists it as untouchable) and USING.md says "states from ABI 2 load"; risk 7 goes.
- **S8. phase-e.md:72-73 (`HostTimeout("slot", timeout, "all <cap> ... held")`) misreads D's class.** D's
  `HostTimeout(op, seconds, message)` prints the third argument as "(last guest message: ...)" (`errors.py:32-36`),
  so the user reads "slot timed out after 3600.0 s (last guest message: all 3 libazahar slots are held)". Fix: a
  `SlotTimeout(HostTimeout)` in `_slots.py` with its own text ("no libazahar slot free after 3600 s: all 3 are held;
  see <dir>"), exported; or pass `message=None` and put the folder in the docstring. (E does not edit `errors.py`.)
- **S9. phase-f2.md:143 (the "C(g)-style error count (D's live tests)" row) names a test that no plan has.** D's
  section 8 (phase-d.md:349-356) has SIGSEGV, SIGSTOP and the long batch, no three-errors test; C's gate has a-f.
  Fix: drop the row, or name where the case is exercised (stock: C as-built "a guest error on the stock core
  arrives two ways"); "D's debug-text test (if any)" is `test_c_checks.py` c4 (phase-d.md:348): say so.

## 3. Nice

- **N1. F2-0 is already answered** (phase-f2.md:21-24, 187-203). Checked 2026-11-12 in MAIN: `build-core/build.exit`
  is `0` (19:40), `azahar_lazpy_libretro.dylib` 19,195,472 bytes, `nm -gU` gives 28 names (the 25 `_retro_*` plus
  `_lazpy_movie_play`, `_lazpy_read_memory`, `_lazpy_write_memory`), STOCK gives 25, the `.def` has 25 `_` lines in
  27, and the dylib holds the `-lazpy.1` string. The tarball's `GIT-TAG` is `2126.2`, so `g_build_fullname` is
  `2126.2` (`CMakeModules/GenerateBuildInfo.cmake:40-55`) and the version is `2126.2-lazpy.1`. Cut the build-failed
  branch, the Monitor wait and risk 1 to one line ("if `build.exit` is not 0, stop and report"); f1/f2 stay as
  checks in `gate_f2.py`.
- **N2. phase-f2.md:78-83 (3.1, `azh_stats` after open) is a no-op.** `host/api.c:369-371` on main (and C's tree,
  `api.c` end) already refuses only `AZH_PH_NONE`. Row A4 (phase-3.md:172) and the "interface change" paragraph
  (phase-3.md:158-160) are wrong: it is already the rule. Drop 3.1 (keep a one-line check that it holds).
- **N3. phase-g.md:102-104 (`AZH_MAX_FIELDS` may grow to 256) is moot.** C's tree (C1 + C2/C3) has 114 `field_rows`
  (`api.c:49-164`); G adds 23 (6 batch/watch, 2 result, 6 map, 9 const) = 137 <= 160 (C's `_Static_assert`,
  `api.c:166`). Drop the branch and the "10,292" size.
- **N4. phase-g.md:180-181 (Python mirrors `azh__watch_plan`) duplicates C.** D's `from_code` maps `AZH_E_ARG` to
  `ValueError` with the host's text (`errors.py:96-97`), so C's message (with the largest-frames hint) already
  reaches the caller. Python checks only types and the 32-entry count; the mirror tests go. About 0.05 h.
- **N5. phase-e.md:198-199, 272-273**: `--extra-rows` appears in the no-Monitor path but not in the usage line;
  add it (and `--only-extra`). Give the `threading.Barrier(n)` a timeout (the slot wait + `boot_timeout`) so a row
  whose third slot never frees ends with a `CHECK FAIL slot` line, not a hang.
- **N6. phase-f2.md:180, 244**: `t_state` is not in D's `state load` line (`../libazahar-py-d/host/state.c:479-480`
  logs `meta_ms sha_ms read_ms drain_ms sd_ms unserialize_ms bytes`). Define it as D does (phase-d.md:367): the wall
  of b's `Emulator(...)` construction, measured in `gate_f2.py`.
- **N7. A committed slot runner instead of three throw-away ones.** F2's `runs/f2/hold_slot.py` (phase-f2.md:231-
  235), G's `runs/g/hold_slot.py` (phase-g.md:257-258) and the phase-end suite's azhost gates (phase-3.md:146-147)
  all need "hold one slot, exec a command". E1 can ship it as `python3 -I -m libazahar._slots --exec -- CMD...`
  (about 12 lines in `_slots.py`, tested by s2's child); G and the phase-end suite use it; F2 keeps its temporary one
  because E1 is not in its tree.
- **N8. The cap is machine-wide only if every user reads the same `LAZ_MAX_INSTANCES`**: a process with cap 5 takes
  slots 3 and 4 beside three cap-3 users. Say so in `_slots`'s docstring (and USING.md in Phase 4); no code.
- **N9. phase-f2.md:101-104 (close after a returned `guest_exited`)**: D's graceful close waits up to `timeout`
  (30 s) for the `close` reply (`_client.py:241-249`) on a core whose guest has exited. Use a short wait (5 s)
  there, then the SIGKILL of D's `_reap`, so the f-tests do not pay 30 s if `retro_unload_game` stalls.
- **N10. phase-g.md:31-32 (m3) checks the next *event* line, PLAN (PLAN.md:320) says "a write changes the next
  logged line".** B6's reason (the record is rewritten each frame) is sound; list it as a refinement in
  phase-3.md section 5 so the review of G does not flag it.
- **N11. phase-3.md:16**: "step C was at C1, commit cd2aadd": C1 is `0651a8d` on step-c; `cd2aadd` is the MAIN
  commit that started the core build. Section 12 lists "`azh_watch`" as an interface; in phase-g it is the entry
  typedef, not a function: say "the `azh_watch` entry type".
- **N12. phase-f2.md:152-153**: reuse C's `gate_c.run_azhost` (with C as-built S4's kill-on-`BaseException` fix) and
  its summary parser by import, rather than a second azhost runner in `gate_f2.py`.

## 4. The "Interfaces assumed" table (phase-3.md section 6) against the code

Checked against main (`cb3406c`), `../libazahar-py-c` (0651a8d + the uncommitted C2/C3 tree) and
`../libazahar-py-d` (b24c436). "ok" = matches.

| Row | Finding |
|---|---|
| A1 | ok: `host/azhost.h:11-13` (C tree), -1 ARG .. -10 SAVESTATE. |
| A2 | ok, with a detail: before boot but after open the stub reaches the lazpy check (`api.c` `memory_gate`: ORDER only in `AZH_PH_NONE`); on our core it returns `AZH_E_UNSUPPORTED` "arrives in step G". G's "call order as `azh_shot`" (after boot) is a tightening; fine. |
| A3 | ok: `host/core.c:100` in `azh_core_open` (called by `azh_open`); G's bind goes there. |
| A4 | **wrong**: `azh_stats` is already valid after open (`api.c:369-371` main; C tree `api.c:583-585`). N2. |
| A5 | not re-checked in code beyond `azh_set_option` existing; consistent with C's `check_stop_rules` reading the option store (`azh_opts_get`). |
| A6 | ok: `azhost_main.c:155` (`DEFAULT_PROFILE`), `:496-499` (profile, then `--opt`). |
| A7 | ok: `host/pins.h`; the built core reports `2126.2-lazpy.1` (N1). |
| A8 | **differs in a way that matters**: `#define PNG_LEVEL 6` (`png.c:11`), and `png.c` is a *pure* module in `TEST_SRC`. S4. |
| A9 | ok: `run.c` `run_frames` takes shots only for `lo <= i <= hi`. |
| A10 | ok: 236 bytes of fields, padded to 240. |
| A11 | ok: `api.c` `opened_once`. |
| A12 | not re-checked (C's `log.c` is in the uncommitted diff). |
| B1-B9 | ok: `record.c:43-48, 58-61`, `record.h:13-21`, `control.h:11-19`, `main.c:16, 23-25, 137-174` (lines as cited, give or take one). `build/testapp.elf` in C's tree puts `g_ctl` at 0x00122d74 and `g_record` at 0x00122dd8 (100 bytes apart; `g_spin_buf` 64 KiB after them), so m3's ±64 KiB scan and m4's upward probe both work. |
| F1-F4 | ok: patch 0001 as quoted (`LazpyCheckRange`, -1/-2/-3, len cap, wrap, try/catch); 0002's six keys, **all registered with stock defaults** (why P8 is needed); 0005 the suffix. |
| F5 | **out of date**: the build finished (N1). |
| C1 | ok: `azh_batch` 3348, `azh_result` 304, `azh_stats` 240, `azh_layout` 6452 (12 x u32 + n_fields + 160 x 40). 114 field rows now (N3). |
| C2 | ok: `azh_internal.h:21-36` (C tree). |
| C3 | ok: `run.c` `run_frames`: `azh__run_one_frame`, then `frames_run`/`vblanks`, then shots, then `stop_after`. E's timing and G's watch row go between `azh__run_one_frame` and `take_shots`. |
| C4 | ok: `msg.c:75` (`AZH_ACT_EXITED` on our core), `env.c:42-56` (the exit path, stock only). |
| C5 | ok: `api.c` `check_stop_rules` (`citra_instant_debug_log` must read `enabled` from the option store). |
| C6 | **differs**: `wall_ms_mean`, not `wall_ms_max` (S3); azhost has no `--core-kind` (F2 adds it to `gate_c.py`, not azhost: fine). |
| C7 | ok in shape; `gate_c.py` has no `--core` yet (F2 adds it) and checks no `abi=` literal (G needs no edit there). |
| D1 | ok, plus `_host.py`; `inputs.py`. |
| D2 | ok: `_client.py:28-29, 42-44, 108-126`; the spawn knows `self.workdir` (no new keyword needed); stdout also goes to `worker.err`; the fake worker's argv is a callable (`test_client.py:20-23`), so appending the slot fd works for both. |
| D3 | ok: `_worker.py:27-33` (`start` = core, sysdir, log, map, options, app, state; `azh_stats` after boot), `:111` `os.nice(10)` (an increment: B2). |
| D4 | ok: `_client.py:212-233` returns `("exited", info)` for 10 during `run`. |
| D5 | ok, plus internal `HostCallError`; `HostTimeout`'s third argument is a guest message (S8). |
| D6 | ok: `emulator.py:62-64, 133-136`; also `set_input`, `run_until(file, text, max_frames, ...)` delegates to `run` (G's pass-through works). |
| D7 | ok: `results.py:19-32`; `shots` has a default, so `watch=()` appends cleanly. |
| D8 | ok: `_paths.py`. |
| D9 | ok, and the strict `abi` equality is `state.c:395` (S7). |
| D10 | **differs**: `host_paths` ignores `LAZ_CORE` (B1); `slow` marker registered in `pyproject.toml:22`. |
| (known) | C's `azh_boot` with a state never calls `boot_game` (C as-built B1; fix on its way). F2's r2 and cross and every state test depend on it. |

Not in the table but relied on: D3's test files (`test_c_checks.py`, `test_live_errors.py`, `test_state.py`,
`test_api.py`) do not exist yet (D is at D1+D2); F2 edits them, so F2 truly cannot start before D3 merges.

## 5. The plan's checked facts (phase-3.md section 10) against SRC and PATCHES

| Fact | Verdict |
|---|---|
| clock 268,111,856; 4,481,136 ticks/frame; `MAX_SLICE_LENGTH` clock/234 | ok: `core/core_timing.h:37, 40-42, 184` |
| Random base ticks from `std::random_device`; Fixed uses the override | ok: `core_timing.cpp:37-44`; `settings.h:506-507` |
| `init_clock` SystemTime (+DST hour) / FixedTime | ok: `shared_page.cpp:34-63`; `settings.h:503-505` |
| `deterministic_async_operations` gates `std::async` | ok: `settings.h:490-491`; `hle_ipc.h:306, 348` |
| `instant_debug_log` writes inline | ok: `settings.h:659`; `backend.cpp:353-357` (it also `Flush`es every backend per entry: a speed cost, S2) |
| `retro_run` registers the thread, loops `RunLoop` until a frame, `DisplayMessage` on non-Success | ok: `citra_libretro.cpp:282-306` (the registration is first-run only) |
| one `retro_run` = one VBlank | ok, and worth stating with its source: `GPU::VBlankCallback` presents every VBlank (`video_core/gpu.cpp:488-498`), the present calls `emu_window.SwapBuffers()` (`libretro_vk.cpp:710-711`), which sets `submittedFrame` (`libretro_window.cpp:68-71`) that ends the loop (`:327-331`). So E's `x_real` vs `host_fps / 59.831` check is sound. |
| `ReadBlock` zero-fills unmapped, copies `Memory`, flushes cached pages | ok: `memory.cpp:173-229` (flush at 212-217); `WriteBlock` skips unmapped at 247-253 |
| `IsValidVirtualAddress` | ok: `memory.cpp:824-837` |
| `CITRA_PAGE_SIZE` 0x1000 | ok: `memory.h:34` |
| `Kernel::GetCurrentProcess()` | ok: `kernel.h:319` |
| `.def` via `-exported_symbols_list`; output `azahar_libretro` | ok: `citra_libretro/CMakeLists.txt:32, 96` |
| state refused on program id or revision | ok: `savestate.cpp:291-301`; the body after the 256-byte `CSTHeader` is zstd (`:303-304`), so f8's "equal after byte 256" compares compressed bytes: fine as a RECORD |
| `GIT_REV` from `GIT-COMMIT` | ok: `GenerateBuildInfo.cmake:13-16`; and `BUILD_FULLNAME` from `GIT-TAG` (`:47-55`) |
| `retro_serialize_size`/`retro_serialize`/`retro_unserialize` | ok: `citra_libretro.cpp:692, 712, 722`; `retro_serialize_size` drains and serializes (D's `drain_ms` note stands) |
| `PollInput` from the VBlank path | ok: `libretro_window.cpp:194-206` (also at `citra_libretro.cpp:221`, only when no game is loaded) |
| PATCHES 0001 checks, codes, cap, wrap, try/catch; `.def` lines | ok: the hunk at `citra_libretro.cpp:746` as quoted |
| this Mac, `flock(2)` semantics | ok (and Python's `subprocess` uses fork+exec, not `posix_spawn`, when `close_fds=True`/`pass_fds` is given, so a sibling thread's child never keeps a slot fd past `exec`) |

Also checked, not in the plan: `async_shader_compilation` defaults to false (`settings.h:537`), so shots are
complete on both cores (good for r1/r2); `frame_limit` is forced to 0 by the libretro core
(`core_settings.cpp:1133`). One "existing solution" checked and rejected: the stock core already sends
`RETRO_ENVIRONMENT_SET_MEMORY_MAPS` (`citra_libretro.cpp:309-345`, called at `:416` in `retro_load_game`), but only
for heap, linear-heap and VRAM VMAs that exist at load time, before the app has allocated its heap, and never for
the app image (`.data`/`.bss`, where `g_record` lives). It cannot replace the lazpy exports or lift P5 on stock.

## 6. The step briefs: can a sonnet follow them?

- **Ownership.** E and F2 share no file (checked row by row); G's shared files (`run.c`, `__init__.py` after E1;
  `api.c`, `_worker.py`, `emulator.py` after F2) are correctly ordered by the G worktree recipe. Gaps: B5
  (`tests/host/test_main.c/.h`), S4 (`azh_pure.h` for E1), S7 (`state.c` one line for G), B4 (F2's conftest gains two
  fixtures). With those, no builder needs to ask.
- **Gates that can fail.** Every gate has a real failure path, except where B2-B4 make them fail for the wrong
  reason. E's guest-time check, F2's byte compares and G's per-field compares are strict; the torn rule is bounded
  (1 %). Good. One weak spot: m1's "at least 590 distinct frames" passes even if every read is one frame behind;
  that is fine for PLAN's gate (the values match their own frame) and the report prints the lag.
- **Checkpoints end the run.** E1, E2, F2 and G each end with a report; the main loop commits and resumes. Correct.
  F2-0's "wait with Monitor (bounded 120 min)" is now moot (N1).
- **Timed runs.** Order core build -> F2-2 -> E2 -> G2 is right; S1 closes the three seams.
- **Slot convention.** One folder, one file naming, `flock` on its own open file description, cap 3, the same in
  E's `_slots`, F2's helper and G's helper. Correct; N7 removes the duplicate helpers, N8 documents the one limit.
- **Sonnet traps found while reading:** B2 (nice increments), S5 (env read at import), S8 (the `HostTimeout` text),
  S3 (`wall_ms_mean`), N5 (`--extra-rows`). E's g1/g2 kill test measures from `os.kill` to the 4th's `acquired`
  stamp, written after `Popen` but stamped at the lock: correct as written.

## 7. Departures P7, P8 and the interface change

- **P7 (`AZH_E_UNMAPPED` -11, `GuestMemoryError`): sound.** The core's -2 is exactly "a page is unmapped" and is
  decided before any byte moves (patch 0001 `LazpyCheckRange`), so a distinct class is honest and cheap; a prober
  (G's m4, Gen3D's harness) must tell it from a host bug without parsing text. Two notes: map the core's -1 to
  `AZH_E_ORDER` only when the host knows the guest is running; after a returned `guest_exited` the Emulator is
  closed (F2), so the -1 case is "no current process" (an applet, a reboot) and `HostError` with the core's reason
  in the text is right. Keep `GuestMemoryError` a direct `LibAzaharError` (not a `ValueError`): the argument was valid.
- **P8 (our core applies `core/options-lazpy.txt` first): sound and necessary.** Patch 0002 registers all six
  options with **stock defaults** ("Defaults equal stock behaviour"), and C's debug-stop check reads
  `citra_instant_debug_log` from the option store (`api.c` `check_stop_rules`), so without P8 our core is stock-like
  and the debug stop is `AZH_E_ARG`. The no-shared-key test is the right guard (checked: the two files share no key
  today). Two additions: the effective option set must be in host.log (f3 checks it) and in E's table rows (S2);
  USING.md says that `instant_debug_log` flushes the log per guest line (a speed cost on chatty apps).
- **`azh_stats` valid after open: not a change** (N2); it already holds on main and in C.
- **Q4 (keep F2's stock regression run?)** Recommend: **cut it to a stock smoke** in F2-2: `gate_c.py --core STOCK
  --only c,f` (the two scenarios whose stock expectations F2's branches touch: c4 exit 7, f's exit path) and
  `pytest -k "c4 or exit or lazpy_profile"` on STOCK, about 5 min instead of about 30. F2's stock-path edits are
  narrow (the option plan skips the lazpy lines on stock, tested without an emulator; the close-after-exit runs only
  on a returned `guest_exited`, which stock never returns), G's batch runs D's whole suite again after the larger
  edits, and the phase-end suite runs everything on stock. The 25 min saved are on the critical path (E2 and G2 wait
  for F2-2).
- **Q5 (fixed 4 MiB watch area vs a size set at open):** Recommend **fixed 4 MiB now**, with two cheap guards: (a)
  Python reads the area's size from the `fields[]` row (`map.watch_data`'s size, and `map.__size__`) instead of a
  hard-coded constant, so a later resize is a host-only change with no ABI bump; (b) the `ValueError` names the
  largest batch that fits (already planned). A size at open needs a new `azh_open` argument or an option (a frozen
  signature) for a need nobody has shown: 52,428 rows of two 32-byte records is 14.6 min of guest time per batch at
  every frame, and `watch_every` stretches it.
- **Q1-Q3 if Guy has not answered:** all three defaults are safe. Q1 (b) skips the Gen3D row and keeps the cap
  provisional: nothing is claimed. Q2 builds P7: additive, pre-release (nothing pushed), reversible by aliasing the
  class. Q3's rule is fixed before the run and never raises the cap above PLAN's provisional 3.

## 8. Hour-saving pass (agent wall time; machine time noted where it is on the critical path)

| Step | Cheaper path, test or existing solution | Saves |
|---|---|---|
| E | Keep the design: stdlib `fcntl.flock` is the right tool (POSIX named semaphores are not released when a holder dies on macOS; `filelock`/`fasteners` are not stdlib and add nothing here), `ThreadPoolExecutor` for `Pool`. Add N7's `--exec` runner (+0.02 h) and drop the 1,000-pair `_slots` timing print (-0.01 h). | about 0 in E; pays back in G and the phase end |
| E | S2 (resume E2 after F2 merged) costs calendar, not agent hours, and saves a second "ours" table run later. | a rerun (about 0.1 h + 20 min machine) avoided |
| F2 | N1 (F2-0 already answered), N2 (3.1 is a no-op), N12 (import `gate_c`'s runner and parser), Q4 (stock smoke instead of a full stock pass). | about 0.11 h; about 25 min machine off the critical path |
| G | N4 (no Python mirror of `azh__watch_plan`; C's `AZH_E_ARG` text already arrives as `ValueError`), N3 (no `AZH_MAX_FIELDS` branch), B4 (explicit cores: G2's four batch parts become two), N7 (no ad-hoc slot holder). S7 adds 0.01 h. | about 0.1 h; about 15 min machine |
| G | Considered and declined: a sticky `azh_set_watch()` function instead of appending to `azh_batch`/`azh_result` (the ABI version still moves for the map rows; no saving), reading `g_ctl`'s address from `testapp.elf` with devkitARM `nm` instead of m3's scan (exact, but adds a devkitARM dependency to a pytest; the scan costs nothing), the stock core's `SET_MEMORY_MAPS` (section 5: does not cover the app image). | - |

Result: step work about **2.6 h** (E 1.1, F2 about 0.75, G about 0.8) plus the 0.5 h of review loops = **about
3.1 h**, against PLAN.md's 2.75 h. The remaining 0.35 h is G's ABI 3 bump, which PLAN's 0.5 h did not count and
which the watch list needs; accept it.

## 9. Verdict

**Ready to build after revision 1 fixes B1-B5 and S1-S3** (all are text edits to the four plan files; none needs
new research). S4-S9 and the nice items are small enough to take in the same revision.

Top 5 fixes, in order:
1. **B1**: F2's conftest resolves the core from `LAZ_CORE` (today's `host_paths` always says stock), so "pytest on
   OURS" really runs ours.
2. **B4**: explicit `lazpy_core`/`stock_core` fixtures and explicit `core=` in G's live tests, so G's gate 4 and the
   phase-end suite can pass with 0 skipped (and G2's batch halves).
3. **B2**: g4 checks `nice >= 10` (D's `os.nice(10)` is an increment; under `nice -n 10` workers sit at 20), or
   the worker sets an absolute level.
4. **B3**: F2's exit-path grep runs right after the our-core parts, before stock rewrites the same folders.
5. **B5**: G's pure functions in a pure `host/watch.c` in `TEST_SRC`, and `tests/host/test_main.c/.h` added to G's
   files.

## 10. What Phase 2 must (or should) change

- **C (known):** `azh_boot` with a state must run `boot_game` first (C as-built B1); F2's r2/cross and D's state tests
  depend on it.
- **D3 (cheapest now, else F2 does it):** `host_paths` honours `LAZ_CORE`, and the live tests take the core from a
  fixture (B1/B4). D owns `conftest.py` until it merges; doing it in D3 removes F2's riskiest edit.
- **D (should):** the worker's `os.nice(10)` becomes "at least 10" (B2), or D's own nice check and docs say
  "parent + 10".
- **D (should, or G under S7):** `state.c:395` accepts `2 <= abi <= AZH_ABI_VERSION`, so states survive ABI 3.
- **C's docs (already in C's as-built):** `docs/map/runners.md` and USING.md say `wall_ms_mean`, not `wall_ms_max`.
