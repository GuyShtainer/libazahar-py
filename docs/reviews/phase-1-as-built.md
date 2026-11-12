# Phase 1 as-built review (opus, 2026-11-12)

Reviewer: opus as-built lane, read-only on the three worktrees (`../libazahar-py-a`, `-b`, `-f1`). Checklists:
`docs/plans/phase-a.md`, `phase-b.md`, `phase-f1.md` section 10. Severity: **blocker** (must fix before merge),
**should fix** (fix in this round), **nice** (optional). Paths are relative to the step's worktree.

Status: done (A, B, F1).

## Step A (host library, azhost)

Read: every file in `host/`, `Makefile`, `tests/gate-a.sh`, `tests/test_version.c`, against phase-a.md sections 2-4
and 10 and phase-2.md section 5. Independent run: `TMPDIR=<scratch> nice -n 10 sh tests/gate-a.sh
runs/a-gate/app.3dsx` in the A worktree, **8/8 PASS, exit 0** (load ~31). ShellCheck clean. No `goto`/`setjmp`/
recursion/token pasting/GL/AppKit; longest function under 45 lines; `azh_abi_layout` sizes match a hand count (batch
3344, result 40, stats 240, layout 48).

### Blockers

**A-X1. The core's log line is used as a printf format** (Phase 2 review 2 S5, confirmed here).
`host/log.c:111-118` passes the core's `fmt` to `vsnprintf` (via `emit`, :82). Azahar's libretro log backend formats
the entry itself and calls `callback(level, str.c_str())` with no arguments (SRC `common/logging/backend.cpp:97-98`;
the only caller, `citra_libretro.cpp:72` via `environment.cpp:211-217`), and guest `svcOutputDebugString` text is
logged verbatim at debug. A `%s`/`%n` in guest text (or a core line, e.g. a path) is undefined behaviour inside the
host today, because `emit` formats **before** the threshold check (:82 vs :96), so even debug lines dropped at the
default info level are run through `vsnprintf`. Fix: `azh_core_log` writes `fmt` literally: `azh_log((int)level,
"%s", fmt)` (ignore the varargs; one comment citing backend.cpp:97-98 and saying a core that passes arguments would
log its raw format). Also check the level against the threshold before any formatting in `emit` (read `threshold`
once; it is set only in `azh_log_open`), which Phase 2's A8 row wanted anyway.

**A-X2. gate-a's symlinks break in the integration clone and write into MAIN's `vendor/`.**
`tests/gate-a.sh:24-27`. phase-1.md "Merge and launch" 4 symlinks `vendor/` from MAIN into the clone. `.gitignore`'s
`vendor/` does not match a symlink (checked: `git ls-files --others --exclude-standard` lists `vendor`, the builder's
own lesson), so line 24's tar copies the `vendor` symlink into `$COPY`, and line 26's `ln -s "$REPO/vendor"
"$COPY/vendor"` then follows that existing link and creates `MAIN/vendor/vendor` (outside build/, runs/, $COPY); on
the next run `ln` fails "File exists" and `set -e` aborts the gate with no FAIL line. Fix: drop `vendor` and `dl`
from the tar list (`... | grep -zv -e '^vendor$' -e '^dl/' | tar ...`, or simpler: `tar --exclude vendor --exclude
dl`), and make the links with `ln -sfn` (or `[ -e ] ||`) so an existing entry is never followed. Re-run the gate in a
scratch clone with `vendor` symlinked to prove it.

### Should fix

**A-S1. Check 1 passes when fetch.sh fails.** `tests/gate-a.sh:29`: no `pipefail`, so a `fetch.sh` that exits
non-zero after printing nothing (or only to stderr) gives `grep -vc` = 0 = PASS. Fix: run `sh tools/fetch.sh
>fetch.log 2>&1` and require exit 0, at least one `have   ` line before the blank line (four: azahar, moltenvk,
libretro-headers, vulkan-headers, or whatever fetch.sh's count is), and no other line before it.

**A-S2. Check 5 does not check the core's message.** `tests/gate-a.sh:74` greps only `^BootError:`; the fallback
texts ("retro_load_game failed", api.c:169) would pass. Checklist item 4 asks for the core's message. Fix: expect
`BootError: Failed to obtain loader` for `/nonexistent/x.3dsx` and `BootError: Failed to load ROM` for
`runs/g/bad.3dsx` (two expected strings in the loop, e.g. `for case in "/nonexistent/x.3dsx|Failed to obtain
loader" ...`).

**A-S3. Check 4 is vacuous if `lsappinfo` fails.** `tests/gate-a.sh:59`: `|| true` swallows a failing or missing
`lsappinfo`, so SEEN is empty and the check passes. Fix: `LIST=$(lsappinfo list) || fail ...`; require LIST non-empty
(it always lists Finder/Dock), then grep it for the pid.

**A-S4. `setenv` from inside the library while core threads may be running.** `host/vk.c:192` sets
`MVK_CONFIG_LOG_LEVEL` in `azh_boot` (after `retro_init`, which starts Azahar's logging thread); `setenv` is not
thread-safe against concurrent `getenv` on macOS. Deviation 5 itself is accepted (errors-only MoltenVK output is a
sensible default and the caller can override). Fix: move the `setenv(..., 0)` to the start of `azh_open` (before
`azh_core_open`, so before any core thread exists) and log the effective value once (`MoltenVK log level 1 (default;
set MVK_CONFIG_LOG_LEVEL to change)`).

**A-S5. Asserts are far below "about 2 per function"** (C rule 5, phase-a section 4). Counts: `api.c` 1 assert in 22
functions, `azhost_main.c` 0 in 12, `vk.c` 7 in 30, `version.c` 0 in 1, `run.c` 2 in 4. Fix (preconditions and
invariants only, side-effect free), at least: `api.c` `check_batch` (b != NULL), `boot_game` (app != NULL, phase ==
OPEN), `open_steps` (paths non-NULL), `teardown` (n_opts in range), `azh_abi_layout` postcondition (`size_layout ==
sizeof(azh_layout)`), `mono_s`; `vk.c` `record_copy` (cb, buf, img non-NULL; w, h > 0), `ensure_buffer` (bytes > 0),
`ensure_commands`, `convert` (mapped, rgba non-NULL; pixels*4 <= cap), `pick_memory_type` (out != NULL),
`submit_and_convert`, `make_device`/`make_instance` (inst state), `fill_interface`; `run.c` `take_shots`,
`check_first_frame`; `azhost_main.c` `set_flag`, `apply_pair`, `build_batch`, `make_dirs` (args non-NULL); `version.c`
(the pinned strings are non-empty, `n > 0`).

### Nice

**A-N1.** One session per process is the real contract: `azh_close` leaves MoltenVK, the instance and device and the
core mapped (vk.c:554, core.c:117), and `teardown`'s memset forgets them, so a second `azh_open` in the same process
leaks them and relies on Azahar surviving `retro_deinit` then `retro_init`. Say so in `azhost.h` beside `azh_close`
("one open per process; Phase 2 runs one worker process per instance"), or make a second `azh_open` return
`AZH_E_ORDER`.

**A-N2.** `hw.context_destroy` is never called before `retro_unload_game` (libretro's usual order). Azahar ran clean
without it; a one-line call in `azh_core_close` when `have_hw` and `context_destroy != NULL` matches the protocol.

**A-N3.** `azhost` maps `AZH_E_UNSUPPORTED`/`AZH_E_ORDER` to `UsageError` exit 2 (azhost_main.c:136-147), so
`--state f` says "UsageError: booting from a savestate arrives in step D". Fine for Phase 1; C/D may want an
`UnsupportedError` class.

**A-N4.** `frame.c:59-69`: a failed software-frame `realloc` leaves `frame_kind` and the old pixels, so a shot would
write a stale frame without error. Set `frame_kind = 0` on that path.

### The five named deviations

1. `struct azh_stats` + `azh_stats_t`, function `azh_stats(struct azh_stats *)`: **accepted**; the plan's typedef and
   function share C's ordinary-identifier namespace and cannot coexist. Layout and ctypes unchanged. Main loop: note
   it in phase-c.md's `fields[]` table (`offsetof(struct azh_stats, ...)`) and phase-d.md's `stats` row.
2. `host/azh_pure.h`: **accepted**; it keeps the pure files free of libretro/Vulkan headers, which is the point of
   rule 4, and C's `test-host` can include it. Main loop: add it to code.md's `host/` line.
3. `crop.c` rectangles only (`azh_crop_rects`) and a stride-taking `azh_png_write`: **accepted**; it avoids a copy per
   PNG, and C's RAW copy is a row loop over the same rectangles (C's test_crop tests the rectangles at factors 1, 2).
   Main loop: note in phase-c.md that C writes the RAW row copy, A's function is rectangles only.
4. `vendor/` copied (not symlinked) in the worktree: **accepted** (that is what phase-a step 0 says); but see A-X2,
   the gate's own `vendor` handling is where the symlink problem bites.
5. `MVK_CONFIG_LOG_LEVEL=1` unless set: **accepted**, with A-S4 (where it is set) .

### Checklist

1 API: holds (names, codes incl. -2/-10, fixed arrays, `n` records, abi_layout/error in any state, boot runs no
retro_run, first-frame check, RAW and later steps return their codes). 2 Env: holds (names only; SET_VARIABLES
copied; callback before set_environment; microphone refused; no GL). 3 Vulkan: holds (one load, every proc checked,
buffer sized from the first frame and grown, freed in close; mutex, DeviceWaitIdle, barrier, copy, barrier back,
submit, QueueWaitIdle; no pointer kept; designated init, `.handle` = state; format checked; LAZ_MVK). 4 Boot
failures: coded and passing; gate too weak (A-S2). 5 Options: holds. 6 C rules: holds except asserts (A-S5). 7 Log:
**fails** (A-X1). 8 Makefile: holds. 9 Gate: A-X2, A-S1, A-S3. 10 No window: holds (lsappinfo empty; the stock core
wrote nothing under `~/Library/Application Support/Azahar`, last modified Aug 11).

**A verdict: not mergeable as is; mergeable after A-X1 and A-X2** (both small), with A-S1..S5 in the same round.

## Step B (test app, checker)

Read: every file under `testapp/`, `tests/check_testapp.py`, `tests/gate-b.sh`, against phase-b.md sections 1-4 and
10 and phase-2.md section 5 (B1-B11). ShellCheck clean. Glyphs decoded by hand (0-9 correct). No goto/setjmp/
recursion, no `KEY_START`, no `svcExitProcess`, no romfs/shared font/system archive; SPDX on every source file.

**Early integration run (reviewer's scratch, not a substitute for "Merge and launch" 4).** A scratch tree = main +
A's files + B's files, `vendor/` copied, the four `dl/` parts symlinked, `git init` + `git add`: `make && make
testapp` exit 0; `RUNNER=azhost sh tests/gate-b.sh` **13 PASS, 1 FAIL** (the FAIL is B-X1 below; every marker, log,
3D, event and boot check passed on azhost: offset 7, vjumps 0, 3D exact); then `tests/gate-a.sh build/testapp.3dsx`
**8/8 PASS**. So A's and B's interfaces fit as written.

### Blockers

**B-X1. gate-b fails check 1 in a fresh clone: `runs/` does not exist.** `tests/gate-b.sh:77` redirects `make`'s
output into `runs/b-$TAG-make.txt` before anything creates `runs/` (the first `mkdir -p` is in `run_app`, :33, and
`build` at :79). Seen in the scratch run: `line 77: runs/b-190722-make.txt: No such file or directory`, `FAIL build`.
The builder's worktree already had `runs/`, so it never showed. The main loop's integration clone is fresh, so its
`RUNNER=azhost` run would fail. Fix: `mkdir -p runs build` right after `cd "$REPO"` (and drop the later
`mkdir -p build`).

### Should fix

**B-S1. Check 1's zero-warning test is vacuous on a built tree.** `tests/gate-b.sh:77-78` runs plain `make -C
testapp`; when `testapp/build/` and `build/testapp.3dsx` are current (the builder's reruns, and the integration run,
where phase-1.md step 4 runs `make testapp` before the gate) make compiles nothing and the log trivially has no
`warning`. Fix: `make -C testapp clean` first (it removes `testapp/build`, `build/testapp.{3dsx,smdh,elf}`), then the
build, so every gate run compiles every file.

**B-S2. "Still running at the end unless `exit_at`" is not checked for the event runs.** phase-b section 1 check 5's
last bullet. `cmd_event` (check_testapp.py:154-172) checks `fs[-1] > n` for break/ready, which an app that stalled at
frame 121 would pass. Fix: for break, ready and booted, also require the boot offset `FRAMES - last f` within 0..120,
as `cmd_log` does: add `--runs` to the `event` subparser (optional, required by the gate for those kinds) and pass
`--runs "$FRAMES"` from gate-b.sh:97 and :100.

**B-S3. `read_png_rgba` raises non-`ValueError` exceptions on malformed files.** check_testapp.py:30, :34 and :43: a
short IHDR raises `struct.error`, a bad IDAT `zlib.error`; both escape `main`'s `except (ValueError, OSError)` (a
traceback instead of a FAIL line) and break the B11 contract Phase 2 imports ("raising `ValueError` on unsupported
PNGs"). Fix: check `length == 13` before unpacking IHDR, wrap `zlib.decompress` and re-raise `ValueError(...) from
exc`; also refuse a chunk whose body runs past the file end, and a compression or filter method byte that is not 0.

**B-S4. Asserts well below "about 2 per function"** (C rule 5, phase-b section 4). Counts: `control.c` 0, `record.c`
0, `font.c` 0, `main.c` 1, `scene3d.c` 1, `sdlog.c` 1. The NULL guards in the pure files are kept (host-tested); add
precondition and invariant asserts where a bad value is a bug, not input: `control.c` `apply_line` (klen < n),
`add_error`, `handle_line` (line non-NULL); `record.c` formatters (`cap >= LAZ_LOG_LINE_MAX` at the call sites' size);
`main.c` `spin_one_frame`, `log_frame`, `run_events`, `draw_frame_2d` (f > boot_frames), `main_loop`; `scene3d.c`
`shader_init` (`g_uloc_projection >= 0` after the lookup, plus an error return if it is negative), `draw_triangle`;
`sdlog.c` `sdlog_line` (`g_offset` does not wrap). asserts stay on in both builds (no `-DNDEBUG`).

### Nice

**B-N1.** `main.c:198-200`: `scene3d_begin() != 0` `continue`s, which advances `f` with no log line (a gap the log
check would call a jump) and the comment says "try again". With `C3D_FRAME_SYNCDRAW` and no `NONBLOCK`,
`C3D_FrameBegin` blocks and does not return false, so this is dead code; either make it `break` with a logged
`scene3d frame failed f=` line, or drop the branch and the -1 return.

**B-N2.** gate-b's azhost branch ignores azhost's exit code (`wait_pid` swallows it, :26); a BootError shows up only
as missing PNGs. Record the code (`wait "$1"; echo $? >"$RUN/rc"`) and print it in the FAIL text.

**B-N3.** `check_screen` appends to the caller's `errors` list (python rule 2); return `(good, errors)` instead.

**B-N4.** Each fe2 shot run leaves up to 5 MB of log under `runs/b-<time>-*`; a `KEEP` switch or removing passed
runs would keep `runs/` small. Not urgent (ignored folder).

### Checklist

1 Behaviour: holds (keys, defaults, ranges, error line; marker table exact; bottom screen markers only; formats with
every argument cast, host-tested; record 32 bytes, tick at 24, magic; both addresses at start; no button exit; 2D
markers at boot_frames+1 and +2). 2 Log: holds (opened once, `FSFILE_Write` + `FS_WRITE_FLUSH` at a running offset,
no stdio, existing `/testapp` ignored and proven by the open). 3 Events: holds (`svcBreak(USERBREAK_ASSERT)` and on;
exit returns from `main` after `gfxExit()`; busy boot bounded, no VBlank wait, no per-frame line). 4 citro3d: holds
(callback registered before `C3D_Init` only; SYNCDRAW / FrameEnd(0); `v = C3D_FrameCounter(0)`). 5 Pure C: holds
(compiled `-Werror` on the host by the gate). 6 C rules: B-S4, B-N1. 7 Licence: holds (README notes libctru's default
icon for Phase I). 8 Makefile: holds (`.3dsx` only, -Werror, `-isystem`, output in `../build`). 9 Checker and gate:
B-X1, B-S1, B-S2, B-S3; `read_png_rgba` signature and import-safety hold; the azhost branch matches A (proven by the
scratch run). 10 No build outputs among the untracked files (`git ls-files --others --exclude-standard`: 19 source
files only).

**B verdict: not mergeable as is; mergeable after B-X1** (one line), with B-S1..S4 in the same round.

## Step F1 (patched core, build script)

Read every patch against the Azahar 2126.2 source in `dl/azahar-src/build-src` and the generated
`build-core/build/src/common/setting_keys.h`. No C++ has been compiled yet, so each API a patch calls was checked
by its signature. Calls checked: `CITRA_PAGE_MASK` (memory.h:35), `GetCurrentProcess` returning `shared_ptr`
(kernel.h:319), `ReadBlock/WriteBlock(const Process&, ...)` (memory.h:558/:599), `IsValidVirtualAddress`
(memory.h:673), `Settings::InitClock` and `InitTicks` enums, `Setting<u64> init_time`, `Core::Movie`
(`ValidationResult`, `PrepareForPlayback`, `StartPlayback`, `ValidateMovie`), and `FileUtil::Exists`. I found no
compile error. The six option keys all exist in `setting_keys.h`. ShellCheck `-s sh` is clean on
`tools/build-core.sh` (101 lines). No build was started: there is no `build.pid` or dylib, no cmake process, and
only `build/`, `configure.log` and `patch.log` sit in `build-core/`. `git status` shows only `core/`,
`tools/build-core.sh` and `tools/untar_checked.py`. `build-core/` and `dl/` are git-ignored.

### Should fix

- **F1-S1** `tools/build-core.sh:68`. In
  `N="$(python3 -I tools/untar_checked.py ... | sed -n 's/.*members=//p')"`, the pipe's status is sed's, so under
  `set -eu` a failed or REFUSED unpack does not stop the script. `sed` also swallows the `REFUSED: <member>` line,
  because it goes to stdout. I proved this in a scratch shell: `set -eu; N="$(sh -c 'echo REFUSED: x; exit 1' |
  sed ...)"` carries on with `N=[]`. The script would then print `unpacked  members ... (path check ok)` and fail
  later on the first patch with a misleading "REJECTED". Red 3 passed only because it ran the helper directly.
  The sha256 pin makes this unreachable today, but the line claims "path check ok", and that claim must be able
  to fail. Fix:
  `OUT="$(python3 -I tools/untar_checked.py "$TARBALL" "$BUILD_SRC")" || { printf '%s\n' "$OUT" >&2; rm -rf "$BUILD_SRC"; die "unpack REFUSED or failed (tree removed)"; }`,
  then `N="${OUT##*members=}"` and `[ -n "$N" ] || die ...`.

### Nice

- **F1-N1** `0002` `ParseLazpyOptions`: `std::stoull` accepts `"-1"`, which wraps to 2^64-1, and it accepts
  leading spaces. Reject a value whose first character is not a digit, and log the fallback.
- **F1-N2** `0006`: once `lazpy_movie_play(path)` is set, nothing clears it (an empty path returns -3). That is
  fine for one boot per process (A-N1). Document it in the README line, or let `""` clear it.
- **F1-N3** `build-core.sh` pin read: an empty value (a missing key) only fails later and less clearly. Check each
  `WANT_*` is non-empty right after the `sed` read.
- **F1-N4** `build-core.sh:46-47`: the trap is split into `EXIT` plus `INT TERM HUP -> exit 143`. That is
  equivalent to the brief's single trap, and the exit code is still recorded. Accepted.

### Deviations (all accepted)

1. The mismatch message names the size and both hashes. It is better than the brief's text.
2. `lazpy_movie_play` returns -5 when a game is already loaded. This is correct: the hook only works before the
   next boot. Phase A/C callers must map -5. Note it in phase-c.
3. One configure log line dropped. Harmless.

### Checklist (section 10)

1. Holds. 0000 adds one notice per file that names every change. The hunks touch only the four allowed files and
   stay minimal. F1's report shows they apply with `--fuzz 0` to a fresh unpack.
2. Holds. `extern "C"`, `_lazpy_read_memory` and `_lazpy_write_memory` are in the `.def`. The checks cover null,
   zero, the 64 MiB cap, the 2^32 wrap, powered-on and the process, and every page is checked before one
   Read/WriteBlock on the same `shared_ptr` process. `catch (...)` returns -1.
3. Holds. Every row's `default_value` is set to stock. The keys come from `citra_setting(BaseKeys::...)`.
   `init_time` is parsed in try/catch, and `ParseLazpyOptions` runs last. The descriptions cite fs_user.cpp and
   core_timing.cpp.
4. Holds. There is one `break;` after `DisplayMessage`, and it exits the `while (!HasSubmittedFrame())` loop. The
   log filter is Info, with `Debug_Emulated` at Debug. The version string is a `static const std::string`, so it
   outlives the call. The movie hook calls Prepare before Load and Start after Success.
5. Holds except F1-S1. Checked: `set -eu`, quoted, the size and sha256 checked first, a present bad file kept and
   a downloaded bad file deleted, the pin read with `sed`, root refused, `nice -n 10`, `cd "$ROOT"`,
   `MACOSX_DEPLOYMENT_TARGET=11.0`, detach through `python3 -I` `os.setsid` + `execvp` with the pid and
   `build.exit` recorded, a live pid refused, and `rm -rf` only on `${ROOT:?}/dl/azahar-src/build-src`.
   `unpacked/` is never touched.
6. Holds. `-I` and stdlib only. The pre-scan reads every member before `mkdir` or `extractall`.
   `filter="data"` adds a second check against escapes through symlinks. Hard links resolve from the archive
   root, symlinks from their own folder. The 7 relative `externals/` symlinks pass. This needs Python 3.12 or
   later for `filter=`; the machine has 3.14.
7. Holds. F1's report quotes the gate and the three reds; git status and the no-build state are confirmed above.
8. Holds. The README makes no speed claims and states GPLv2-or-later, with any binary shipped alongside the
   unchanged tarball plus the patches.

**Verdict: mergeable as is.** F1-S1 is a correctness fix for a path the pin makes unreachable today. Land it in
the same round as the A and B fixes, or as the first change of the build step, but it does not block the merge.

## Re-check (fix rounds, 2026-11-12)

Each fixed item was re-checked by reading it in its worktree against what this review asked for. No gate was
re-run, because every fix can be judged by reading, and the builders report fresh gate runs: A 8/8 in the
worktree and twice in a clone with a symlinked `vendor`; B 14/14 from a fresh tree on both runners; F1 a clean
`--configure-only` plus 5 reds.

### A

- A-X1 is fixed. `host/log.c:113-118` checks the threshold first, then calls `azh_log((int)level, "%s", fmt)`, with
  a comment citing backend.cpp:97-98.
- A-X2 is fixed. `tests/gate-a.sh:24-28` drops `vendor` and `dl` from the NUL list (`grep -zvE`) and uses
  `ln -sfn`.
- A-S1 is fixed. `gate-a.sh:31-35` requires exit 0, only `have` lines, and at least one.
- A-S2 is fixed. Check 5 expects `Failed to obtain loader` and `Failed to load ROM` after `BootError:`.
- A-S3 is fixed. Check 4 FAILs when lsappinfo exits non-zero or prints nothing.
- A-S4 is fixed. `setenv` (no overwrite) is the first step of `open_steps` (`host/api.c:118`), before the core is
  opened, and the level is logged.
- A-S5 is fixed. Assert counts are now api.c 21 over 22 functions, azhost_main.c 22/12, vk.c 40/30, version.c 2/1
  and run.c 7/4, and they check real invariants.
- A-N1 is fixed. `opened_once` is set only after a successful open, and a second open returns `AZH_E_ORDER`.
- A-N2 is fixed. `host/core.c:125-127` calls `context_destroy` before `unload_game`.
- A-N4 is fixed. `frame.c` sets `frame_kind = 0` when the realloc fails.
- A-N3 was skipped, as agreed.

**A: mergeable.** Nothing remains.

### B

- B-X1 is fixed. `tests/gate-b.sh:7-8` runs `cd "$REPO"` and then `mkdir -p runs build`.
- B-S1 is fixed. `make -C testapp clean` runs before the zero-warning build.
- B-S2 is fixed. `cmd_event` requires `--runs` for every event except exit, plus `0 <= runs - last_f <= 120`. The
  gate passes `--runs "$FRAMES"` to all four event runs and to the log check.
- B-S3 is fixed. `read_png_rgba` checks chunk-header and chunk bounds, the IHDR length, the compression and filter
  methods, and the decompressed size, and wraps `zlib.error`. Every path now raises ValueError.
- B-S4 is fixed. Assert counts are control 3, record 10, font 2, main 7, scene3d 4 (including
  `g_uloc_projection >= 0`) and sdlog 3.
- B-N2 is fixed. A non-zero azhost exit is a FAIL (`gate-b.sh:50`).
- B-N4 is fixed. Runs that pass are removed unless `KEEP=1`.
- B-N1 and B-N3 are reported done. I did not re-read them; they are nice items only.

**B: mergeable.** Nothing remains.

### F1

- F1-S1 is fixed. `tools/build-core.sh:71-78` uses `OUT="$(python3 -I ...)" || { print, rm -rf, die }`, then
  `N="${OUT##*members=}"` and a check that N is non-empty. F1's new red 4 runs an evil tarball through the full
  script and gets REFUSED, then "unpack REFUSED or failed (tree removed)", exit 1.
- F1-N1 is fixed. 0002 requires a leading digit before `stoull`; otherwise it keeps 946681277.
- F1-N2 is fixed. 0006 clears the movie on an empty path and returns 0. The return codes are documented above the
  function.
- F1-N3 is fixed. `build-core.sh:39` checks that all seven pin values are non-empty; red 5 covers it.
- ShellCheck `-s sh` is clean, and the script is 110 lines (the cap).
- Two leftovers, both nice only:
  - **F1-N5:** when the output holds no `members=`, `${OUT##*members=}` returns the whole output, so the `-n` check
    cannot fire. Use `case $OUT in *members=*) ;; *) die "unpack printed no member count";; esac`.
  - **F1-N6:** `OUT` is reused for the dylib path at :105. Rename one of the two.
- The C++ is still uncompiled. 0002 now catches `const std::exception&`, which `<string>` brings in through
  libc++. The build step is the first real compile.

**F1: mergeable.** N5 and N6 are optional.
