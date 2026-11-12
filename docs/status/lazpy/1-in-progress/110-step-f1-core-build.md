---
id: laz-110
title: lazpy
order: 110
kind: step
parent: laz-100
page: Our patched core: patch files, version pin and build script; the first build started
hours: -
---
# Step F1: our patched core: patch files, version pin and build script; the first build started

## What it is
Our own Azahar core build: the pinned source tarball, our patches (memory read/write calls, repeatable-run and clock options, our version name), the build script, the notices. The first full build runs detached and nice'd.

## Exit gate
The gate in `docs/PLAN.md` line 298 ("Phase F1"), run headless on this Mac with a pass/fail answer.

## Evidence
none yet

## Pointers
- Plan section: `docs/PLAN.md:298`
- Phase plan: none yet
- Review: none yet

## Lessons and notes
Read this part only when you work on this item. Blockers, numbers and Guy's words go here verbatim.
- Builder report (a85f3abcf6d608824, 2026-11-12 19:03, worktree ../libazahar-py-f1, uncommitted): stops after
  configure and three planted reds, no build. Files: core/PIN; core/patches/ 0000-lazpy-notices (39 lines),
  0001-lazpy-memory-exports (81), 0002-lazpy-options (152), 0003-lazpy-run-returns-on-error (11), 0004-lazpy-log-filter
  (21), 0005-lazpy-version (13), 0006-lazpy-movie-play (84); core/options-lazpy.txt; core/README.md;
  tools/build-core.sh (102, shellcheck clean); tools/untar_checked.py. Gate from clean: pin ok, sha256 ok, 21133
  members unpacked (path check ok), 7 patches ok with `--fuzz 0`, 0 rejects, "configure done: build-core/build",
  exit 0; configure 2 min 18 s nice'd at high load (CMake 42 s). Reds: one sha digit changed -> "SHA256 MISMATCH ...
  file kept, not refetched" exit 1; one 0003 context line changed -> "REJECTED (tree removed)" exit 1; tar with
  "../evil" -> "REFUSED" exit 1, nothing written. The patched tree and configured build dir stay in the worktree's
  ignored `dl/azahar-src/build-src/` and `build-core/` (the build runs in MAIN after merge, per phase-1.md).
  Deviations: the mismatch line names size and both hashes; `lazpy_movie_play` has an extra return -5 "already
  booted"; a `configure (log ...)` line dropped to match the brief's expected output.
  .gitignore: `*.tar.xz *.tar.gz *.orig *.rej`. Map lines: code.md `core/` (PIN, patches 0000-0006, options-lazpy.txt,
  README.md); tools.md tools/ (build-core.sh) (verify/fetch, unpack, patch, configure, `--build`/`--detach` builds
  `build-core/azahar_lazpy_libretro.dylib`), tools/ (untar_checked.py) (pre-scan, refuse unsafe members, extract with
  filter="data"). runners.md: none.
  Lessons: Movie verdict YES: order PrepareForPlayback(path), System::Load, StartPlayback(path) (citra_qt.cpp :1504,
  ~:1545, :1559), done via do_load_game() so retro_reset replays it; Movie survives System::Shutdown; the movie's
  program id is stored, never checked; a revision mismatch only warns (Qt 2125.1.2 movies load); StartPlayback is
  silent on a bad file, so lazpy_movie_play pre-validates with ValidateMovie; with the Software renderer the boot runs
  inside retro_load_game so the call returns -5; with hardware rendering "after retro_load_game, before
  context_reset" works; playback overrides pad, touch, accelerometer and gyro; F2 decides whether replay on reset is
  wanted. A1 yes: configure works without a git repo; scm_rev.cpp gets GIT-COMMIT 219d743a, BUILD_VERSION and FULLNAME
  2126.2, so the savestate revision should match stock. A2 yes: no _deps, 0 downloads, FetchContent unused. A3 not
  tested (no build; `LAZ_CORE_LTO=OFF` fallback in the script). No C++ compiled yet: the first compile is the
  detached build. lazpy_* are extern "C" globals, underscore names in the .def; 0002's keys come from
  citra_setting(BaseKeys::...), all six exist in settings.h; init_time's stoull is in try/catch. BSD patch quotes file
  names in its output: check with `diff -r`, not a pipeline's exit code (a first `rc=0` was tr's). `--detach` checked
  by reading and `sh -n` only. Builder scratch: session scratchpad f1-notes.md, e0.py-e6.py, mkpatch.sh.
- Fix round (19:22): F1-S1, N1, N2, N3 done. Changed: tools/ (build-core.sh, now 110 lines, shellcheck clean),
  core/patches/0002 (158 lines) and 0006 (89); the stack was rebuilt from pristine source (0000, 0001, 0003-0005
  same content). Clean --configure-only: 7 patches, 0 rejects, configure done, exit 0. Reds 1-3 as before, exit 1;
  new red 4 (an evil tarball through the full script with a matching scratch PIN): "REFUSED" then "unpack REFUSED or
  failed (tree removed)", exit 1, no misleading patch REJECTED; new red 5 (empty SRC_TOP): "pin <file> is missing a
  value", exit 1. lazpy_movie_play codes: -2 missing file, -3 null path (empty path clears, returns 0), -4 not a movie,
  -5 already booted. init_time needs a leading digit (else the 946681277 fallback). Lessons: never pipe
  untar_checked.py (sed hides its exit and REFUSED line); read $? from a separate rerun, not a pipe (no PIPESTATUS
  in sh); to change a patch mid-stack, rebuild the stack from pristine source, never hand-edit hunks.
