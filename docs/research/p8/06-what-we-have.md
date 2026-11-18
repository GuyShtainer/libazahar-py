# What libazahar-py has at v1.1.0: inventory

Facts only, each with a pointer. Read-only survey of the repo docs, `python/libazahar/`, `tests/`, `.github/workflows/` and
status items 500, 700-714. Pointers are `file:line`.

## 1. Public API surface
Python (`python/libazahar/__init__.py:13-17`, `__all__`; the promise is `docs/USING.md:8-13`, semver from 1.0.0 until 2.0):
- `Emulator(app, workdir, *, sd_seed, state, core, options, timeout, boot_timeout, fresh_sd)`: one instance in its own
  worker process; context manager (`docs/USING.md:431-433`).
- `Emulator.run(frames, *, inputs, shots, stop_file, stop_text, stop_every, stop_new, debug_text, wall_limit, timeout, watch,
  watch_every)`; frames positional only, rest keyword-only (`docs/USING.md:44-45`).
- `run_until(file, text, max_frames, ...)`, `run_frame()` (`docs/USING.md:46`, `:434`).
- `set_input(buttons, touch, circle)`, `set_keys(raw)` (`docs/USING.md:435`).
- `screens()` (numpy views if numpy installed, else `bytes`), `shot(prefix)` (two PNG `Path`s) (`docs/USING.md:160-164`).
- `save_state(path)` -> `SaveInfo`, `load_state(path)`, `threads()` -> `ThreadInfo` tuple, `stats()` -> `Stats`, `close()`
  (`docs/USING.md:437-438`).
- Properties `app`, `workdir`, `sd`, `pid`, `closed`, `frame_total`, `memory` (`docs/USING.md:432-433`).
- `emu.memory`: `read`, `write`, `u8..u64`, `s8..s64`, `write_u8..write_u64`, `raw_read`, `raw_write`; our core only
  (`docs/USING.md:190-199`, `:444`).
- `Pool(n, app, root, **emulator_kwargs)`: `submit`, `map`, `close` (`docs/USING.md:241-248`).
- `Buttons` (libctru KEY_* bits: A B SELECT START D-pad L R X Y ZL ZR, plus UP/DOWN/LEFT/RIGHT aliases;
  `python/libazahar/inputs.py:18-38`), `Touch(x, y)`/`Touch.up`, `Circle(x, y)` (`inputs.py:61`).
- Result types `RunResult`, `Shot`, `WatchRow`, `SaveInfo`, `Stats`, `ThreadInfo` (`docs/USING.md:441-447`).
- Errors: `LibAzaharError`, `ArgumentError` (also ValueError), `BootError`, `GuestError`, `HostTimeout`, `SlotTimeout`,
  `HostCrashed`, `StateError`, `NeedsLazpyCore`, `GuestMemoryError`, `HostError`, `LoadWarning` (`docs/USING.md:448-453`).
- `__version__` = "1.1.0" (`python/libazahar/__init__.py:15`).
- Python stability promise: `__all__` names, arguments, return types, error classes; `libazahar.errors` stays importable
  (`docs/USING.md:9`, `:156`). New `stopped_by` values may be added (`docs/USING.md:441`).
- Install is an editable install from a clone only (`docs/USING.md:17-19`); no plain pip install, no PyPI (`STATUS.md:106`).

C host API (`host/azhost.h`; `docs/HOST-API.md:32-50`): `azh_open`, `azh_close`, `azh_set_option`, `azh_boot`, `azh_run`,
`azh_shot`, `azh_save_state`, `azh_load_state`, `azh_read`, `azh_write`, `azh_threads`, `azh_set_input`, `azh_stats`,
`azh_abi_layout`, `azh_error`. One `azh_open` per process (`docs/HOST-API.md:27-29`).
- C promise: names, argument orders, meanings of `azh_*` and `AZH_*` do not change in 1.x; struct layouts may grow, so C
  callers rebuild each release (`docs/HOST-API.md:4-8`, `docs/USING.md:10-11`).
- The host/Python layout is NOT promised: `AZH_ABI_VERSION` is 4 and may bump in 1.x; the layout is checked at load
  (`docs/HOST-API.md:4-6`, `:18-21`).
- `azhost run ...` and `azhost layout` command line, exit codes 0,2-11 and the summary keys
  `frames wall fps shots stop first last vblanks wall_ms_mean batch msg` are frozen (`docs/USING.md:52-72`).
- Input-script format (7 int32 per line) and option-profile format are frozen (`docs/USING.md:85-98`, `:278-306`).
- Environment table (first table only): `LAZ_ROOT/HOST/CORE/MVK/PROFILE/LAZPY_PROFILE/VK_DEVICE/MAX_INSTANCES/SLOT_DIR/
  SLOT_TIMEOUT/PNG_LEVEL/LOG_LEVEL/ANY_CORE/STATE_ANY_APP` (`docs/USING.md:310-329`).
- Savestates load in later 1.x on the same core revision only (`docs/USING.md:13`).

## 2. Platforms and how each is proven
- macOS arm64 (macOS 15+): v1.0.0 full emulator suite on a Mac: 299 passed, 1 skipped (nice-value skip) with
  LAZ_REQUIRE_EMULATOR=1 and a stock and old core (`docs/status/lazpy/5-done/600-phase-6-v1-release.md:122`);
  fresh clone 292 passed, 8 skipped (`...600...:130`); fast tier 244 passed (`...600...:109`).
- macOS at v1.1.0: no local full run. Hosted runner `macos-live`: 292 passed, 14 skipped, 1 failed (`test_state_boot`,
  5.3 s vs 2.5 s bound) (`STATUS.md:57-65`, `docs/status/lazpy/5-done/713-w9-final-gate-publish.md:22-24`). Fast tests
  on hosted macOS: 245 passed, 6 skipped, Python 3.10 and 3.14 (`...713...:22-23`).
- Windows x64 native (v1.1.0), proven on ONE PC: Windows 10 Pro 22H2, RTX 3060 driver 610.88, Python 3.10.11
  (`STATUS.md:44-50`, `README.md:15-19`).
  - Fresh clone: 299 passed, 8 skipped, `skips_check` 0 problems, 2 copies (`...714...:15-17`); host C tests
    "307983 checks, 0 failed" (`...704...:21`, `...709...:22`); stage-clone RC run 298 passed (`...711...:43`).
  - Earlier runs had failures that were fixed or timing-only (stock-core name, cross-OS state fixture, state_boot
    bound) (`...711...:43-58`).
- Windows hosted CI (Server 2025): build, host C tests, fast tests, Python 3.10 and 3.14 (`.github/workflows/test-windows.yml:16-56`).
- Not proven: Windows 11, AMD and Intel GPUs (`STATUS.md:52`); Intel Macs, macOS before 15, Linux (`STATUS.md:38`).
- Release assets: SHA256SUMS digests of 13 assets verified from the release URLs after publish (`...714...:14-15`).
- No Windows speed figures (`STATUS.md:54`); the README has macOS-only measured numbers (`README.md:21-49`).

## 3. Tests
- Host C tests (`make test-host`, `tests/host/`): input, match, msg, png, profile, rawcopy, sdcopy, statemeta, touch,
  watch (`tests/host/test_*.c`); plus `tests/test_version.c`.
- Static checks (`make check`): `tools/check-obinary.sh` plus clang `--analyze` on every host source
  (`Makefile:30-36`, Windows `:128-135`).
- Python tests, 29 files in `tests/python/`; `slow` and `needs_core` markers (`pyproject.toml:22`). Groups:
  - no emulator: `test_abi`, `test_api`, `test_arguments`, `test_client`, `test_errors`, `test_inputs`, `test_map`,
    `test_paths`, `test_profile_parser`, `test_slots`, `test_c_checks`.
  - live emulator: `test_live_errors`, `test_memory_live`, `test_pool_live`, `test_state`, `test_state_3d`,
    `test_stencil_live`, `test_threads_live`, `test_lazpy_profile`, `test_profile_format`, `test_windows_cli`.
  - also `test_release_fixture` (a prior-release state fixture), `test_review_fixes`.
- Gate scripts outside pytest: `tests/gate-a.sh`, `gate-b.sh`, `gate_c.py`, `gate_f2.py`, `gate_f2_pe.py`,
  `check_testapp.py`, `fetch_fallback.sh` (7 cases).
- Tools: `tools/docs_check.py` (runs README/USING snippets), `tools/skips_check.py` (allows only `needs_core` skips in
  the fast tier), `tools/release_check.py` (with `--plant-red` self-test), `tools/clone_check.sh`.
- Skip list (conftest `needs_core` rule: skip, or fail under `LAZ_REQUIRE_EMULATOR=1`; `tests/python/conftest.py:26-48`):
  - stock-core comparison tests skip unless `LAZ_STOCK_CORE` is set, even under REQUIRE (`conftest.py:82-86`).
  - `test_threads_live.py:199,213`: need `LAZ_CORE_OLD` (a lazpy.1 core). `:103`: core is not lazpy.2.
    `:163`: no `build/testapp.elf` (release test app ships none; also skipped on macOS CI).
  - `test_lazpy_profile.py:58`: Windows has no nice values. `:68`: process already nicer than the test's value.
  - `test_slots.py:94`: no load average on Windows; `:105` its Windows twin skips off Windows.
  - `test_client.py:123`: Windows priority class only. `test_windows_cli.py:18`: Windows only.
  - `test_arguments.py:49`: no symlink rights (Windows without Developer Mode).
  - `test_api.py:109`: skips if the batch was not longer than the timeout.
  - `test_release_fixture.py:28`: no fixture under `runs/release-fixtures/`.
  - `test_map.py:51`: numpy missing. `test_profile_format.py:46`, `test_windows_cli.py:25`: binary not built.
  - No lazpy.1 Windows core, so lazpy.1 tests skip on Windows (`STATUS.md:48-50`).
- CI (all manual or Windows-push only):
  - `test-windows.yml`: on push; build, `make check`, `test-host`, `test-version`, fast pytest (`-m "not slow"`), `skips_check`.
  - `test.yml`: macOS 15, manual (`workflow_dispatch`), fast tier plus a Makefile-command guard
    (`.github/workflows/test.yml:7-9`, `:28-66`).
  - `macos-live.yml`: macOS 15, manual, the full emulator suite, `continue-on-error` (`macos-live.yml:8-36`).
  - `core-win64.yml`: manual; builds the Windows core, load-tests on a clean Windows runner, leak check, attest
    (`core-win64.yml:2-3`, `:230`).
- Local only: the whole emulator suite on macOS (no automatic macOS run), the stock-core comparison, the old-core
  boot test, the Windows emulator suite on the one PC, the core build gates (`gate_f2*`).

## 4. Documented limits and non-goals
- No Linux; macOS before 15 and Intel Macs unsupported (`README.md:12-19`, `STATUS.md:38`).
- Homebrew only: no commercial titles, keys, system files, encrypted titles, `.cia` installs (`STATUS.md:42`, `:102-104`).
- No audio output, no window, no wireless, motion or camera, no RPC server or gdb stub (`STATUS.md:98-105`).
- No PyPI wheel and no Python CLI (`STATUS.md:106-107`); editable install only (`docs/USING.md:17-19`).
- Guest memory, watch list, debug-text stop, `threads()` need our patched core; stock core raises `NeedsLazpyCore`
  (`docs/USING.md:372-383`). `threads()` needs lazpy.2 (`docs/USING.md:208-212`).
- Repeats exact on our core only (`STATUS.md:69`); poll-exact movie call exported by the core but not called by host or
  Python (`STATUS.md:40`).
- Touch rows 63, 125, 126, 127 land one pixel off (`STATUS.md:70-71`, `docs/USING.md:100-103`).
- Savestates: do not carry between macOS and Windows (boost `long` size); may not load across core versions; NAND files
  not snapshotted; an older host refuses newer states (`docs/USING.md:366`, `:171-173`; `STATUS.md:72-73`).
- Multi-field memory reads and watch rows can be torn across a frame (`STATUS.md:74`, `docs/USING.md:195-196`).
- One `azh_open` per process, so one worker process per Emulator (`STATUS.md:75`).
- Slot cap (default 4, 1..64) counts only libazahar workers (`STATUS.md:76`, `docs/USING.md:250-257`).
- Guest HTTPS finds a CA file only at OpenSSL's compiled-in paths: Homebrew `openssl@3` on macOS, none on Windows
  (`STATUS.md:78-79`, `docs/USING.md:367`).
- Windows: ASCII paths under 260 chars, no `runs/` behind a junction, a Vulkan driver required and not shipped
  (`docs/USING.md:355-367`).
- A Vulkan loader is required on every host (MoltenVK fetched on macOS) (`README.md:55-58`).
- Frame = one guest VBlank; the timeout is no-progress, not a batch bound (`docs/USING.md:34-40`).
- An `Emulator` is for one thread at a time (`docs/USING.md:259`).
- The built-in key data and default HTTP client certificate are removed from our core (`README.md:161-163`).
- `azhost` has no `--help` (`STATUS.md:80`).

## 5. Known bugs, open deferred items, open user asks
- Known flaky: `test_state_boot` exceeds its 2.5 s bound on a shared hosted macOS runner (`STATUS.md:61-62`,
  `...713...:23-24`). A kill-to-acquire slot test also went over its bound on a busy PC (`...711...:56`).
- Deferred to the next core rebuild (`docs/status/lazpy/1-in-progress/HANDOFF.md:20-23`): the Windows zip's own
  SOURCE.md snapshot entry; the OpenSSL ENGINESDIR/MODULESDIR prefix; `release_check` check 13 printing PASS when it did
  not run.
- Open: the PC install of diffutils and actionlint was denied by the permission classifier (`HANDOFF.md:27`).
- Open: pushes need explicit approval (`HANDOFF.md:26`). No new phase is planned until requested (`HANDOFF.md:18-19`).
- Item 500 (open-ended, no Evidence yet; `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md:19-20`): the user
  asks from Gen3D and 3DPlatinum. Done: tick seed (core lazpy.2) and `threads()` (`STATUS.md:27-28`). Still noted: an
  audio route for 3DPlatinum's sound lane, "an ask with a repro follows" (`500...:35-36`); a possible later
  `lle_applets` ask (`500...:32-33`). Peer sessions were told to stop messaging; a new ask waits for a restart (`HANDOFF.md:14-15`).
- Not built, documented: poll-exact movies via `lazpy_movie_play` (`STATUS.md:40`).
- Gen3D's adapter is that project's own work (`STATUS.md:109`, `:115`).

## 6. What is NOT there
| Capability | Status | Pointer |
|---|---|---|
| Frame advance | have: `run(n)`, `run_frame()`, `run_until` (frame = guest VBlank) | `docs/USING.md:34`, `:434` |
| Buttons (all KEY bits incl. ZL/ZR, D-pad) | have; ZL/ZR work via a separate path with 1-frame offset | `inputs.py:18-38`, `docs/USING.md:82` |
| Touch | have (bottom screen pixels); 4 rows 1 px off | `docs/USING.md:100-103` |
| Circle pad | have (-32767..32767) | `docs/USING.md:105-108` |
| C-stick (New 3DS) | missing: no `Circle`-like type, input record has 7 ints only | `docs/HOST-API.md:243-250` |
| Home / power buttons | missing: not in `Buttons` or the record (`AZH_BUTTONS_MASK` 53247) | `inputs.py:18-38`, `docs/HOST-API.md:252` |
| Gyro / accelerometer | missing: "motion not built" | `STATUS.md:105` |
| Microphone, camera | missing: "camera not built"; no mic anywhere | `STATUS.md:105` |
| Screenshots as numpy, no PNG round trip | have: `screens()` returns uint8 arrays (240x400x4, 240x320x4) from the map; bytes without numpy; arrays are read-only views that change at next raw shot | `emulator.py:453-471`, `docs/USING.md:160-161` |
| Audio capture | missing (audio output not built) | `STATUS.md:98` |
| Memory read/write | have, our core only: `emu.memory` | `docs/USING.md:190-199` |
| Memory watch | partial: per-frame sampled watch list (<=32 entries, 1..256 words), not a trigger; torn reads possible | `docs/USING.md:201-206` |
| Breakpoints on addresses | missing: only guest `svcBreak`/`bkpt` stop; gdb stub not in libretro builds | `docs/USING.md:112-114`, `STATUS.md:101` |
| Register access | partial: `threads()` gives pc, lr, sp, cpsr per thread (lazpy.2); no r0-r12, no write | `docs/USING.md:208-212` |
| Savestates to file | have: `save_state(path)` writes state + meta + SD snapshot; `Emulator(state=)` / `load_state` | `docs/USING.md:166-180` |
| Savestates in memory (bytes) | missing: path based only | `docs/USING.md:168` |
| Deterministic replay / seeds | partial: exact repeats gated on our core only; tick seed `citra_init_ticks_override`; no RNG-seed API | `STATUS.md:69`, `docs/USING.md:273-276` |
| Input movie record / replay | partial: `inputs=[(frame, item)]` plays a movie; `azhost --inputs FILE`; no recording of live input; poll-exact call not wired | `docs/USING.md:74-98`, `STATUS.md:40` |
| Many instances | have: `Pool`, machine-wide slot cap (default 4) | `docs/USING.md:239-265` |
| Subprocess crash boundary | have: each Emulator in its own worker process; `HostCrashed` with log tail | `docs/HOST-API.md:27-29`, `docs/USING.md:136-139` |
| Timeouts / hang detection | have: heartbeat no-progress `timeout`, `boot_timeout`, `wall_limit`, `SlotTimeout` | `docs/USING.md:36-39`, `:133-143` |
| Logging | partial: `host.log` per instance, `LAZ_LOG_LEVEL`; no Python `logging` integration found in the package | `docs/USING.md:130-131`, `:326` |
| Golden-image comparison helpers | missing: no diff/compare helper in `python/libazahar/` (tests compare markers themselves) | `python/libazahar/__init__.py:13-17` |
| Gym-style env wrapper | missing | `STATUS.md:105-109` (not listed anywhere) |
| MCP / agent interface | missing (the sibling 3DS-MCP is a separate tool for real hardware) | `CLAUDE.md` project note |
| CLI | partial: `azhost` (C) only; no Python CLI, no `--help` | `STATUS.md:107`, `:80` |
| pip wheels / PyPI | missing: editable install from a clone, `LAZ_ROOT` otherwise | `docs/USING.md:17-19`, `STATUS.md:106` |
| Linux | missing (a port was discussed and answered yes in principle, then Windows was done instead) | `STATUS.md:38`, `:97`; `500...:37-43` |
| Software-Vulkan CI path | missing: a real Vulkan driver is required; macOS CI is manual and flaky on hosted runners | `README.md:18`, `test.yml:7-9`, `STATUS.md:59-64` |
| Real commercial-game coverage | missing by policy: homebrew only; tests use the project's own test app; real-scene runs use one user's homebrew | `STATUS.md:102-103`, `:42` |
| Docs: quickstart | have: README example and `examples/quickstart.py`, 3 examples | `README.md:98-126`, `examples/README.md` |
| Docs: troubleshooting | have: USING section 19 (short) | `docs/USING.md:410-425` |
| Docs: API reference | have: one line per name, plus C header comments; no per-argument generated reference | `docs/USING.md:427-454`, `docs/HOST-API.md:12-14` |
| Versioning policy | have: semver from 1.0.0, what is covered is listed; ABI of host/Python layout excluded | `docs/USING.md:8-13`, `docs/HOST-API.md:4-8` |
| Windows 11 / AMD / Intel GPU / Intel Mac proof | missing (untested) | `STATUS.md:52`, `:38` |
