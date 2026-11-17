# Phase 7, W1: review of the Windows port branch (laz-702)

Reviewed 2026-11-17, 12:26 to 12:39. Read-only: nothing was built or run.

- Diff: `git diff v1.0.0 port-win-v1`. The two ends are tag v1.0.0 (6f1a713) and branch port-win-v1 (1c8650f). The
  diff touches 65 files, +1738 / -166.
- 9 of those 65 files come from main's own commits, v1.0.0..a551d5f, where a551d5f is the merge base: docs/status/*,
  docs/hours.tsv, docs/progress.html, README.md, STATUS.md and some others. The branch's own work is 24 commits
  (a5f56dc..1c8650f) over 56 files.
- Inputs: `runs/p7/w1a/darwin-pp.diff` and `runs/p7/w1a/make-n.diff`, both made on the PC in W1a. Also the plan
  `docs/plans/phase-7.md` (section 9, D2, D3, D6, D9) and the owner conditions in
  `docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md`.

## Verdict: fix then merge

There is one blocker, `tools/build-core.sh` (P7-R1-1). It is a planned fix, owned by W2b1. Every hunk the macOS build
can see is behaviour-preserving on macOS. The Windows code is sound in its design, but one fault would bite users
(P7-R1-4), and the plan's known gaps (B5, B6, B10, B12, B13) are all still open on the branch.

## Gate counts

| Section | Covered / in file |
|---|---|
| C, `runs/p7/w1a/darwin-pp.diff` | 60 / 60 hunks, in 35 / 35 files |
| Makefile, `runs/p7/w1a/make-n.diff` | 1 / 1 hunk, 1 / 1 changed line (+1, -0) |
| Python, every hunk in `git diff -U0 v1.0.0 port-win-v1 -- '*.py'` | 101 / 101 hunks, in 21 / 21 files |
| Findings | 19 in all: 1 blocker, 8 should, 10 nit |

## Findings

| Id | Severity | Where (port-win-v1) | What | Fix | Owner |
|---|---|---|---|---|---|
| P7-R1-1 | blocker | `tools/build-core.sh:7`, `:16-20`, `:124-150` | Plan B11. The branch adds a `LAZ_CORE_TARGET` case (mac or win64) and a win64 cmake route to `tools/build-core.sh`. D3 requires this file to stay byte-identical to v1.0.0, so the v1.0.0 Mac core and its keyblob check carry over by checksum (D2). | Restore the file to v1.0.0's bytes (`git diff v1.0.0 -- tools/build-core.sh` must come out empty). Move the win64 case, with `tools/toolchain-win64.cmake`, into a new `tools/build-core-win64.sh`. gate_f2 takes the build script per target. | W2b1 |
| P7-R1-2 | should | `Makefile:66`; `python/libazahar/_paths.py:28`; `tests/python/conftest.py:37`; `tests/python/test_profile_format.py:44` | Plan B5. `make win64` writes to `build/win64/`, but Python and the tests look for `build/libazhost.dll` and `build/azhost.exe`. Without `LAZ_HOST` set, a Windows user's `import libazahar` does not find the host. | Write the four outputs to `build/` and keep the objects, `.def` and `.a` in `build/win64/`. The names cannot clash with the Mac outputs (`.dll` against `.dylib`, `azhost.exe` against `azhost`). The other choice is to change all three Python sites, which is wider. | W2a |
| P7-R1-3 | should | `Makefile:64`, `:65`, `:99` | Plan B6. `WIN_CC ?= x86_64-w64-mingw32-gcc-posix` and `ZLIB_PREFIX ?= $(HOME)/3ds/zlib-mingw` are WSL cross-build values, and the comment above `test-version-win` speaks of WSL. D6 says users build with MSYS2 `make` in a MINGW64 shell. | Default to `WIN_CC ?= gcc` and `ZLIB_PREFIX ?= /mingw64`, the MINGW64 zlib package. Reword the block comment (`:59-63`) and `:99` for MSYS2. A cross build can still override both variables. | W2a |
| P7-R1-4 | should | `host/plat/win_compat.c:32`; `host/azhost_main.c:18`, `:168`; `host/core.c:92` | The core is loaded with `LOAD_LIBRARY_SEARCH_DEFAULT_DIRS \| LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR`. Microsoft's LoadLibraryEx documentation says that DLL_LOAD_DIR requires a fully qualified path. Yet azhost.exe's default core (`dl/lazpy-core/azahar_lazpy_libretro.dll`) is relative, and so is any relative `--core`, so the load should fail (ERROR_INVALID_PARAMETER). Python is safe because `_paths.core_path()` resolves the path. No test catches this: every CLI test passes an absolute `--core`. The fault is inferred from the documentation, not seen on the PC. | In `azh_win_dlopen`, call `GetFullPathNameA` before `LoadLibraryExA` whenever the path holds a separator. Add a CLI test that runs azhost.exe from the repo root with no `--core`. Check a relative `LAZ_MVK` too: with the SYSTEM32 flag, a relative path is looked up under System32. | W2a |
| P7-R1-5 | should | `.github/workflows/` (no change on the branch) | Plan B10. The branch adds no CI file: no Windows build job in the test workflow, and no `core-win64.yml`. | W2a: add the Windows build-and-test job to the CI test files, non-blocking and in its own file, as answered in item 500. W2b1: add `.github/workflows/core-win64.yml` (D4). | W2a, W2b1 |
| P7-R1-6 | should | `tools/fetch.sh`, `tools/mknotices.py`, `tools/mkrelease.py`, `tools/release_check.py`, `tools/clone_check.py`, `tests/gate_f2.py` (none changed on the branch) | Plan B12. The release and check tools are still macOS-only. The branch touches none of them. | W2b1: gate_f2 per target, and the PE keyblob twin (B9). W2b2: the fetch fallback (D7), the Windows zip in mknotices, mkrelease, release_check and clone_check. | W2b1, W2b2 |
| P7-R1-7 | should | the release tools (none changed); `pyproject.toml:10` | Plan B13. The branch has no `LAZ_WIN_PY`. `requires-python = ">=3.10"` guards a pip install, but nothing stops a release tool from running on the PC's default 3.7 `python`. The worker side is fine: `_client.worker_python()` uses the running interpreter's base `python.exe`. | Every release tool run on the PC takes `LAZ_WIN_PY` (D9). Where a tool can tell, it refuses a Python older than 3.10 with a clear message. | W2b2 |
| P7-R1-8 | should | the whole branch | port-win-v1 has never been compiled against real macOS headers. W1a ran the preprocessor with Apple's predefines and empty system-header stubs. That shows every change in this branch's own text, but it cannot see what an include adds. `host/azh_plat.h` now pulls `<fcntl.h>`, `<stdio.h>` and `<unistd.h>` into every file (through `azh_pure.h`), and `host/api.c` moves `<dlfcn.h>` and `<sys/resource.h>`. I found no identifier clash by reading (optarg, optind, FREAD, BUFSIZ, and the like), but `-std=c11 -Werror` and `make check`'s `clang --analyze -analyzer-werror` have not run on this code. | Before main moves, run the macOS CI job on p7-int (`make check`, `make`, `make test-host`, `make test-version`, the fast test tier). Pushing p7-int is Guy's call. Without that, W3's Mac gates are the first real Darwin compile. | W2a (CI file), run at W3/W4 |
| P7-R1-9 | should | `README.md:10`, `:15-16`; `STATUS.md:3`, `:39-42`; `docs/USING.md:318`, `:321`, `:323` | The docs still say v1.0.0, and that Windows has "no CI and no download" and that "nothing in this release runs on Windows". USING lacks the Windows defaults: `LAZ_MVK` is the bare `vulkan-1.dll` from System32, and `LAZ_SLOT_DIR` is `%LOCALAPPDATA%\libazahar-py\slots`. USING also needs the Windows table (MSYS2 build, `make win64`, outputs). The `LAZ_VK_DEVICE` row is correct but long. The version bump to 1.1.0 (owner condition 1) is not on the branch. | Write these texts in our own words (owner condition 8). Bump to 1.1.0. Split the `LAZ_VK_DEVICE` row into the row plus one line of prose. | W6 |
| P7-R1-10 | nit | `host/plat/win_compat.h:2`, `:30` | Line 2 still says "Scope: azhost.exe run only. State, SD seeding and the tree walk are AZH_E_UNSUPPORTED (win_stubs.c)". That file is gone, and state works now. Line 30 has a stray second comment about TerminateProcess on the `azh_win_proc_times` line, which belongs to `azh_win_exit`. | Rewrite the scope comment. Move the TerminateProcess comment to `azh_win_exit`. | W2a |
| P7-R1-11 | nit | `host/plat/win_compat.c:42-55`; `host/core.c:93` | `azh_win_dlsym` never sets `err_text`. After a missing symbol, `dlerror()` returns the last LoadLibrary text, or "" in a fresh thread, not the symbol's error. | On NULL, set `err_text` to "GetProcAddress(<name>) failed, Windows error <n>". | W2a |
| P7-R1-12 | nit | `host/plat/win_sdcopy.c:153` | `SetFileAttributesA(p, FILE_ATTRIBUTE_NORMAL \| DIRECTORY)`. FILE_ATTRIBUTE_NORMAL is valid only when used alone, and DIRECTORY cannot be set this way. A read-only file may keep its flag, so the delete that follows fails. | Pass `FILE_ATTRIBUTE_NORMAL` alone, or clear only `FILE_ATTRIBUTE_READONLY` from `GetFileAttributesA`. | W2a |
| P7-R1-13 | nit | `host/match.c:118-137`, `:153`, `:160` | On Windows, each poll opens the guest log twice: once in `azh__file_size_fresh` and once in `poll_file`. | `fstat` the descriptor `poll_file` already opens, and keep `azh__file_size_fresh` for `run.c:255`. | W2a |
| P7-R1-14 | nit | `tools/hold_slot.py:67-71` | The child is put into the kill-on-close job only after `Popen`, and the return of `AssignProcessToJobObject` is not checked. A failed assign goes unnoticed, and so does a grandchild started in that window: either can outlive hold_slot while it holds the slot. | Check the return value. On failure, kill the child and raise `WinError`. Say in a comment why the slot release comes first. | W2a |
| P7-R1-15 | nit | `tools/speed_table.py:83-92` | `vram_used_mb()` runs `nvidia-smi` with no timeout and catches only FileNotFoundError. On macOS it adds a `vram_mb: None` key to every row. That is harmless, but no test covers it. | Pass `timeout=10` and catch `(OSError, subprocess.TimeoutExpired)`. On macOS, skip the call. | W2a |
| P7-R1-16 | nit | `tests/python/test_threads_live.py:67` | On Windows, `needs_rev2` looks for the bytes `lazpy_threads` anywhere in the DLL, not in its export table. A string in the data section would pass. | Parse the PE export directory, as `elf_info` does for ELF, or use MSYS2's `objdump -p`. | W2a |
| P7-R1-17 | nit | `tests/python/test_client.py:134` | The file ends with a blank line (two newlines). | Drop the last newline. | W2a |
| P7-R1-18 | nit | `tools/check-obinary.sh:6-8` | A site whose same-line comment holds the word O_BINARY passes. Zero sites also pass ("ok 0"), for example when the tree has moved. | Strip `/* ... */` and `//` text before the O_BINARY grep. Fail when the count is 0, or when it drops below the branch's number. | W2a |
| P7-R1-19 | nit | `host/vk.c:298-302` | `contains_nocase` calls `strnlen` on both arguments before its `assert` that they are not NULL. | Put the assert first. | W2a |

## Plan findings B5, B6, B10 to B13, against the branch

| Plan finding | Holds on port-win-v1? | Review id | Owner |
|---|---|---|---|
| B5, `build/win64/` against `build/` | Yes (`Makefile:66` against `_paths.py:28`, `conftest.py:37`, `test_profile_format.py:44`) | P7-R1-2 | W2a |
| B6, WSL defaults | Yes (`Makefile:64-65`, `:99`) | P7-R1-3 | W2a |
| B10, no CI file | Yes (no `.github/` change) | P7-R1-5 | W2a (test CI), W2b1 (`core-win64.yml`) |
| B11, `build-core.sh` edits | Yes (`tools/build-core.sh` changed in 3 hunks) | P7-R1-1 | W2b1 |
| B12, release tools macOS-only | Yes (none touched) | P7-R1-6 | W2b1 (gate_f2), W2b2 (fetch, mknotices, mkrelease, release_check, clone_check) |
| B13, PC Python 3.7 | Yes (no `LAZ_WIN_PY`; `pyproject.toml:10` guards installs only) | P7-R1-7 | W2b2 |

W2 must fix all six. W6 owns the doc and version side: P7-R1-9.

## Owner conditions 1, 3, 5 and 7

The brief points to phase-v1.md, but the conditions are not there. They are in
`docs/status/lazpy/1-in-progress/500-phase-5-user-asks.md:39-43` (the answer of 2026-11-13, 13:47), which lists 8 of
them. The PC worker's reply at 14:12, on line 44 of the same file, makes them binding. They are numbered here in the
order given there, which matches the plan's D12. The answer quoted in full, verbatim:

> "Answered yes, on conditions: it merges after v1.0.0 as 1.1.0, rebased only after our push; its core uses
> core/PIN-nokeys; the Darwin Makefile block stays verbatim; device choice unchanged on a one-GPU Mac; `DEFAULT_CAP`
> stays (the PC sets `LAZ_MAX_INSTANCES`); no core/ or build-core.sh change on main before v1.0.0; no Linux release
> asset without Guy and the legal audit; our own review and Mac gates before the merge; USING.md wording is ours."

| # | Condition (verbatim) | Holds? | Evidence |
|---|---|---|---|
| 1 | "it merges after v1.0.0 as 1.1.0, rebased only after our push" | Yes, in timing. The 1.1.0 part is still open. | v1.0.0 is tagged (6f1a713), and the branch was cut on main after it (merge base a551d5f). The branch does not bump the version: STATUS.md:3 still says v1.0.0. That is W6 (P7-R1-9). |
| 3 | "the Darwin Makefile block stays verbatim" | Yes | `runs/p7/w1a/make-n.diff` has 1 hunk with 1 added line, `tools/check-obinary.sh` under `check:`, and no removed line. That line is the one the plan allows. The win64 block (`Makefile:57-107`) adds only new targets and variables, and `make -n` on Darwin does not read them. |
| 5 | "`DEFAULT_CAP` stays (the PC sets `LAZ_MAX_INSTANCES`)" | Yes | `python/libazahar/_slots.py` keeps `DEFAULT_CAP = 4`. No hunk touches it or the cap rule. |
| 7 | "no Linux release asset without Guy and the legal audit" | Yes | The branch adds no release tooling, no workflow and no Linux build target. The new win64 route is Windows only. |

The other four, briefly. Condition 4 holds: with `LAZ_VK_DEVICE` unset, the device is still `gpus[0]`
(`host/vk.c:416`), and stderr stays silent when there is only one device (`:403`). Condition 6 was about main before
v1.0.0 and is now moot, though D3 keeps the same rule for this phase (P7-R1-1). Condition 2 is for W2b1 and W5 to
check. Condition 8 is this review plus W3.

## C: every hunk in `runs/p7/w1a/darwin-pp.diff` (60 / 60)

How to read it: each side is `gcc -E` output with Apple's predefines, so `O_BINARY` shows as `| 0`, `azh_replace` as
`rename`, and `azh_fsync` as `fsync`. Each hunk below maps to its source line on port-win-v1. "OK" means macOS
behaviour is unchanged unless the row says otherwise. Tests: test-host means `make test-host` (the C unit tests), and
live means the emulator tests (the macos-live workflow).

### The 35 prototype hunks (one per file)

Each of these adds one line: `int64_t azh__file_size_fresh(const char *path, int64_t from_stat);`. It comes from
`host/azh_pure.h:52`, which every file includes. Verdict for all 35: OK, a declaration only. The hunks, by index and
file:

| Hunks | Files |
|---|---|
| 1-7 | host/api.c, host/azhost_main.c, host/core.c, host/crop.c, host/env.c, host/frame.c, host/hostmap.c |
| 9, 12, 14 | host/input.c, host/log.c, host/match.c |
| 17-23 | host/mem.c, host/msg.c, host/options.c, host/png.c, host/profile.c, host/rawcopy.c, host/run.c |
| 25, 26, 34 | host/sdcopy.c, host/state.c, host/statemeta.c |
| 39, 40, 42 | host/version.c, host/vk.c, host/watch.c |
| 43, 45, 46, 48, 49 | tests/host/test_input.c, test_main.c, test_match.c, test_msg.c, test_png.c |
| 51-53, 55, 58, 59 | tests/host/test_profile.c, test_rawcopy.c, test_sdcopy.c, test_statemeta.c, test_touch.c, test_watch.c |
| 60 | tests/test_version.c |

### The other 25 hunks

| Hunk | Source on port-win-v1 | Change as macOS sees it | Verdict | Test |
|---|---|---|---|---|
| 8 | host/hostmap.c:52 | `open(..., O_RDWR\|O_CREAT\|O_TRUNC \| 0, 0644)` | OK, same flags | live |
| 10 | host/input.c:211 | `long v` becomes `long long v` | OK: both are 64-bit on arm64, and the range checks are unchanged | test-host test_input |
| 11 | host/input.c:228 | `strtol` becomes `strtoll` | OK, same result on LP64 | test-host test_input |
| 13 | host/log.c:44 | `open(... \| 0 ...)` | OK | test-host, live |
| 15 | host/match.c:118-137 | new `azh__file_size_fresh`. On macOS it asserts and returns `from_stat` | OK | test-host test_match |
| 16 | host/match.c:153, :160 | `poll_file` takes the size from it (the stat size on macOS), and its `open` gets `\| 0` | OK | test-host test_match |
| 24 | host/run.c:255 | `from = azh__file_size_fresh(c->sd_path, st.st_size)`, which is `st.st_size` on macOS | OK | live |
| 27 | host/state.c:61-70 | `join_path`: the assert on `base`/`suffix` becomes a runtime NULL check that returns AZH_E_ARG | OK. It differs only for a NULL argument, which no caller passes (`:151`, `:237-238`, `:316`, `:348`, `:407`, `:439-440`) | live (state tests) |
| 28 | host/state.c:92-99 | `open(... \| 0)`. The `CC_SHA256_Init` result is now checked and the fd closed on failure | OK: CommonCrypto's Init always returns 1 | live |
| 29 | host/state.c:114-116 | the `CC_SHA256_Final` result is now checked | OK, always 1 on macOS | live |
| 30 | host/state.c:154 | `open(tmp, ... \| 0, 0644)` | OK | live |
| 31 | host/state.c:165 | `rename((tmp), (path))` | OK, only the macro's parentheses | live |
| 32 | host/state.c:185 | `open(path, O_RDONLY \| 0)` | OK | live |
| 33 | host/state.c:245, :248 | the two directory renames in `snapshot_sd`, through the macro | OK. On Windows the targets are removed first (`:241`), so MoveFileExA on a directory works | live |
| 35 | host/statemeta.c:226-229 | `if (0 != 0) return AZH_OK;` before `fsync_path`'s open, plus `\| 0` | OK, dead on macOS. clang's default checks (including `--analyze`) do not flag it, but this is unproven until P7-R1-8 | test-host test_statemeta |
| 36 | host/statemeta.c:247 | `open(tmp, ... \| 0, 0644)` | OK | test-host test_statemeta |
| 37 | host/statemeta.c:281 | `rename((tmp), (path))` | OK | test-host test_statemeta |
| 38 | host/statemeta.c:297 | `open(path, O_RDONLY \| 0)` | OK | test-host test_statemeta |
| 41 | host/vk.c:294-407, :408-440 | new `contains_nocase`, `read_device_props`, `digits_only`, `pick_device` and `report_device`, plus the device choice in `make_device` (+109 -2) | OK, see the note below | live |
| 44 | tests/host/test_input.c:161 | new refused cases -2147483649, 4294967296 and 0xffffffff (line 158 already had the accepted INT32_MIN) | OK | test-host test_input |
| 47 | tests/host/test_match.c:97 | tmp dir through `AZH_TEST_TMPDIR(tmp)` (`tests/host/plat_test.h`), which on macOS gives the same `tmp ? tmp : "/tmp"` | OK | test-host test_match |
| 50 | tests/host/test_png.c:64 | same as 47 | OK | test-host test_png |
| 54 | tests/host/test_sdcopy.c:93 | same as 47 | OK | test-host test_sdcopy |
| 56 | tests/host/test_statemeta.c:63-94 | the doubled-key loop gains `check(... < sizeof text, "doubled-key text fits")` (`:90`) | OK, a stricter check | test-host test_statemeta |
| 57 | tests/host/test_statemeta.c:166-167 | `dir[512]`, `path[600]`, `tmp[620]` (were 21 bytes, 256 and 300) | OK: larger buffers, and the same `/tmp` template for mkdtemp | test-host test_statemeta |

Hunk 41 on macOS: `make_device` now reads every device's name and type (`vkGetPhysicalDeviceProperties` through
`gipa`; with no proc the names stay empty). It writes one new INFO line to host.log on every boot. It writes to stderr
only when `LAZ_VK_DEVICE` is set or there is more than one device; a Mac has one. The default device is still
`gpus[0]`. No test or tool in tests/ or tools/ asserts exact host.log lines or an empty stderr, so the extra INFO line
breaks nothing. Note that only live tests cover this path, and no test covers `LAZ_VK_DEVICE` on macOS.

What this method cannot see, which I read in the source instead:
- `host/api.c` moves `<dlfcn.h>` and `<sys/resource.h>` to after `azh_internal.h`, under `#ifndef _WIN32`.
- `host/state.c` wraps the CommonCrypto include in `#ifdef __APPLE__`.
- The new includes in `host/azh_plat.h`.

None of them changes macOS behaviour as far as reading goes. The real compile is P7-R1-8.

## Makefile: every line in `runs/p7/w1a/make-n.diff` (1 / 1)

| Hunk | Line | Verdict |
|---|---|---|
| 1 | `+tools/check-obinary.sh`, after `build/test-version` and before the `analyze` loop of `make check` (`Makefile:26`) | OK. It is the one line the plan allows (W2a gate). The script uses only `grep`, `printf` and `sh`, all present on macOS, and it reads only `host/`. |

No other line differs. The Darwin block is verbatim (owner condition 3).

## Python: every changed line that runs on macOS (101 / 101 hunks)

"Win only" means that every changed line in the hunk sits behind `_WIN`, `WIN` or `sys.platform == "win32"`, or is a
comment or docstring, so macOS never runs it. "Runs on macOS" rows give the line, the verdict and the test that
covers it.

### python/libazahar (36 hunks)

| File (hunks) | Runs on macOS | Verdict | Test |
|---|---|---|---|
| `_client.py` (10) | `:9` `import signal` dropped (no `signal.` use is left). `:23` `_WIN = False`. `:42-46` `worker_python()` returns `sys.executable` on macOS. `:49-52` `worker_argv` head `[sys.executable]`, same argv. `:168-169` the `if _WIN` test. `:197-198` slot.txt written with `encoding="utf-8", newline="\n"`: the same bytes as `write_text` on macOS. `:304`, comment only. `:328-335` `kill_own_worker(sig=None)`: None calls `proc.kill()` (SIGKILL on POSIX, as before), and a number still goes to `os.kill`. Win only: `_popen_windows` (`:173-191`). | OK, equivalent | test_client.py (spawn, argv); test_slots.py `test_w8_hard_killed_worker_gives_the_slot_back` (`kill_own_worker()`, its only caller); waited_in through test_slots |
| `_paths.py` (8) | `:5` `import sys`. `:14` `SUFFIX = ".dylib"` on darwin. `:15` a constant. `:28` `build/libazhost.dylib`, as before. `:40` `dl/lazpy-core/azahar_lazpy_libretro.dylib`, resolved as before. `:47` the `if not env and win32` test is false. The others are docstrings. | OK, equivalent | test_paths.py `test_default_core_is_ours`; conftest `host_lib` |
| `_slots.py` (12) | `:21` `import sys`. `:29-34` `_WIN` false, so `import fcntl` runs as before. `:47-52` slot_dir: `LAZ_SLOT_DIR`, else `~/Library/Caches/...`, as before. `:95-98` release: `os.close`, as before. `:111` `read_text(encoding="utf-8")`: the file is ASCII. `:119-120` the `if _WIN` test. `:128-131` module constants. `:151-152` the `if _WIN` test. Win only: `_try_round_win` (`:134-147`). Docstrings: `:10-15`, `:44-45`, `:82-83`. | OK, equivalent | test_slots.py s1-s7 and w8; test_pool.py |
| `_worker.py` (6) | `:20-22` `_WIN` false. `:145`, `:182` and `:186-193` are the `if _WIN` tests: `os.set_inheritable`, `Connection(fd)` and `raise_nice_floor()` run as before. `hard_exit` and `set_error_mode` (`:151-170`) are defined but never called on macOS. | OK, equivalent | test_client.py (fakeworker); live tests (the real worker) |

### tests/python (57 hunks)

| File (hunks) | Runs on macOS | Verdict | Test |
|---|---|---|---|
| `conftest.py` (2) | `host_lib` imports `_paths` and uses `SUFFIX`, which gives the same path. `lazpy_core` builds the same two candidates. | OK | every test that uses those fixtures |
| `fakeworker.py` (2) | `Connection` import and SIGSEGV, as before, behind the `else` branch | OK | test_client.py |
| `proc_helpers.py` (1, new) | `pid_alive` is `os.kill(pid, 0)`. `hard_kill` is SIGKILL. `suspend` is SIGSTOP. `popen_holding` is `Popen(pass_fds=)`. `base_python` and `sleeper` give `sys.executable`. All the same calls the tests made before. | OK | test_client, test_slots, test_live_errors, test_pool_live |
| `test_arguments.py` (1) | `os.symlink` in a try that skips on OSError. It never fails on macOS. | OK | itself |
| `test_client.py` (7) | `worker_python()` is `sys.executable`. `alive()` calls `pid_alive`. The SEGV assert splits in two, and the macOS branch keeps `signal == SIGSEGV` and the time check. `assert not alive(pid)` replaces `pytest.raises(ProcessLookupError)`, which is equivalent. The new Windows test is skipped. | OK. See P7-R1-17 (trailing blank line). | itself |
| `test_lazpy_profile.py` (2) | `import sys` and a `skipif(win32)` mark | OK | itself |
| `test_live_errors.py` (5) | SIGSEGV and SIGSTOP through `suspend()`. `pid_alive` as above. The macOS asserts are unchanged. | OK | itself (live) |
| `test_memory_live.py` (4) | `footprint_kib` runs `du -k`, as before. m7 uses `read_bytes().decode()` / `write_bytes(...encode())`, the same bytes on macOS (UTF-8, `\n`). | OK | itself (live) |
| `test_paths.py` (1) | compares `parts[-3:]` against `endswith`, the same check | OK | itself |
| `test_pool.py` (1) | `monkeypatch.setattr(..., raising=False)`. `os.getloadavg` exists on macOS, so it behaves as before. | OK | itself |
| `test_pool_live.py` (5) | `import signal` dropped (none used). `load()` and `worker_nice` behave as before. `hard_kill` is SIGKILL. | OK | itself (live) |
| `test_profile_format.py` (7) | `build/azhost`, as before. The skip text uses `exe.name`. The `nice -n 10` prefix is kept. `_unreadable` does chmod 0 and then 0600, the same as before, now in a context manager. | OK | itself |
| `test_slots.py` (12) | `import signal` dropped. `SLEEPER = sleeper()`, the same argv. `popen_holding` and `hard_kill` as above. s4's mode asserts run (`not WIN`). s5 runs and its Windows twin is skipped. s7's `SLEEPER[0]` is `sys.executable`. New w8 runs on macOS. | OK | itself |
| `test_state.py` (2) | `read_bytes().decode()` / `write_bytes()`: the same bytes | OK | itself (live) |
| `test_threads_live.py` (5) | `import struct`. `elf_info` is defined but only called on Windows. `nm -gU`, `elf_symbols` and `text_range` take the macOS path, as before. | OK. See P7-R1-16 (Windows only). | itself (live) |

### tools (8 hunks)

| File (hunks) | Runs on macOS | Verdict | Test |
|---|---|---|---|
| `hold_slot.py` (2) | the `if sys.platform == "win32"` test in `main`. `run_windows` is Windows only. The exec path is unchanged. | OK | test_slots.py s7 |
| `speed_table.py` (6) | `load_now()` is `os.getloadavg()[0]`, as before (`:153`, `:171`, `:208`, `:214`). `nice_of` keeps its POSIX body. New: `vram_used_mb()` runs on macOS, finds no `nvidia-smi`, and adds `"vram_mb": None` to each row (`:171`). | OK. The change is one extra key, and nothing reads the rows' key set strictly. See P7-R1-15. | no test (test_slots.py:178 imports only `cap_rule`) |

## Windows-side notes (no finding)

- Slot lock. A share-0 `CreateFile` handle (`_slots.py:134-147`) goes to the worker through
  `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` only. The parent closes its copy right after the spawn, and test w8 checks that
  a hard kill frees the slot. This matches the item-500 answer (3).
- Worker exit. `TerminateProcess` runs after the close reply is written (`_worker.py:145-146`), with exit code 0. This
  matches answer (5).
- O_BINARY. One plat header defaults it to 0 (`host/plat/azh_plat.h`), and `tools/check-obinary.sh` runs from
  `make check`. This matches answer (4).
- CRT and paths. `azh_win_early_init` sets `_set_fmode(_O_BINARY)` and the error mode. The fopen "r" readers in
  `azhost_main.c` accept one CR per line. `win_sdcopy.c` refuses reparse points and caps depth at 32.
- `input.c` takes `long long` because Windows has a 32-bit `long`, and test_input covers the edges.

## Left open

- P7-R1-4 comes from Microsoft's LoadLibraryEx documentation, not from a run on the PC. W2a should reproduce it first.
- P7-R1-8: until a real macOS compile, the C verdicts above rest on the preprocessed text plus reading. They do not
  cover the content of system headers.
- Not checked here: owner condition 2 (the PIN-nokeys core) and the PE keyblob twin (B9). Those are W2b1 and W5.
