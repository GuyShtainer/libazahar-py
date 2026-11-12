# Phase 1, foundation: the index (item laz-100)

Opus phase plan, 2026-11-12, revision 2 (after `docs/reviews/phase-1-review-1.md` and `phase-1-review-2.md`). Review
2's verdict: ready to build after this revision, no third loop. Three steps, each with its own brief for one sonnet
builder in its own worktree:

| Step | Item | Brief | What it delivers | Hours |
|---|---|---|---|---|
| F1 | laz-110 | `docs/plans/phase-f1.md` | our core's pin, patch stack, options profile and `tools/build-core.sh`, configured and its reds shown; the build itself is started by the main loop in MAIN after the review | 0.75 |
| A | laz-120 | `docs/plans/phase-a.md` | `build/libazhost.dylib` and `build/azhost` (boot, run frames, two-screen PNGs, options profile, version check, boot errors) | 1.15 |
| B | laz-130 | `docs/plans/phase-b.md` | `build/testapp.3dsx` (markers, per-frame log, record, break/exit/ready/busy-boot modes) and its checker with `read_png_rgba` | 0.9 |

MAIN = `/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`, the main checkout.

## Hours

Builders: F1 0.55, A 0.95, B 0.7. One opus as-built review for all three steps (one big lane) plus the commits:
about 0.6 h, split 0.2 per step in the table. **Phase 1: 2.8 h** of agent time (PLAN.md 3.25; revision 1: 2.85). The
main loop's own work (the integration run, the launch in MAIN, the waiter) is about 0.2 h of its time. F1's
detached build is machine time, not booked (15-25 min quiet, 40-90 min at load 60-90).

## Order

All three builders start together (independent files, independent worktrees). F1 ends after configure and its reds;
it starts no build. B uses `prototype/fe2.c` as its runner, so it does not wait for A. Nothing in Phase 1 needs our
core: A and B run on the stock core; our core's own gate is step F2 (Phase 3). The as-built review starts when A and B
have both reported (F1 reports first and waits). The core build starts in MAIN after the review passes and the
integration run is green, while nobody times frames (the build is not on the critical path: F2 waits for Phase 2).

## Before the launch (main loop)

1. Commit the four plan files; `python3 -I tools/mkmap.py && python3 -I tools/map_check.py` (docs/plans/ is new).
2. `dl/` is in fetch.sh's layout and `dl/libretro-headers/`, `dl/vulkan-headers/` and
   `vendor/include/.vulkan-headers-1.4.368` exist in MAIN (done 2026-11-12; review 2 N12).
3. Worktrees at main (check `git worktree list` and a case-insensitive name clash first):
   `git worktree add -b step-f1 ../libazahar-py-f1 main`, likewise `step-a` / `../libazahar-py-a` and `step-b` /
   `../libazahar-py-b`. Dispatch without isolation, cwd in the worktree.
4. Move items 110, 120, 130 from `2-next/` to `1-in-progress/` with their "Running now" rows; book hours rows.
   Builders never edit item files (their notes come back in the report), so the move on main cannot conflict.
5. No installs are needed (devkitPro, CMake 4.3.4, ninja, Xcode 26.3, spirv-opt, shellcheck, Python 3.14). No Guy
   decision blocks the launch.

## File ownership (no two builders edit the same file)

| Owner | Files |
|---|---|
| F1 | `core/` (PIN, patches/, options-lazpy.txt, README.md), `tools/build-core.sh`, `tools/untar_checked.py` |
| A | top-level `Makefile`, `host/` (all), `tests/gate-a.sh`, `tests/test_version.c` |
| B | `testapp/` (all, including `testapp/Makefile` and `testapp/README.md`), `tests/check_testapp.py`, `tests/gate-b.sh` |
| main loop only | `.gitignore`, `docs/map/*` (incl. `code.md`, `tools.md`, `runners.md`), root `README.md` (nobody this round), `docs/PLAN.md`, `docs/plans/*`, `docs/reviews/*`, `docs/hours.tsv`, the handoff, every item file |

`tests/` is shared as a folder only; each file in it has one owner.

## Merge and launch (main loop)

1. **Reports.** F1 reports first, then A and B. Nothing is committed yet.
2. **The as-built review** (one opus lane, read-only on the three worktrees). It works through the three briefs'
   section 10 checklists in order (F1, A, B) and writes its findings to `docs/reviews/phase-1-as-built.md` in MAIN
   as it goes (agent-limit hygiene). Each fix goes back to the owning builder by SendMessage; the reviewer then
   re-checks only the changed items.
3. **Branch commits.** In each worktree the main loop commits the step's own files on its branch (exact paths, then
   `git diff --cached --stat`), and checks `git diff --cached --name-only` holds no `.png`, `.3dsx`, `.elf`, `.log`,
   `.dylib`, `.tar*` or `.zip` (review 2 N7; these live in ignored folders, so this is a net).
4. **Integration run, before main.** A throwaway branch: `git -C MAIN branch int-1 main`, a worktree for it, `git
   merge --no-ff step-a step-b` there (no shared files, so no conflicts). Then a real clone of that branch into
   `$(mktemp -d)`, with `vendor/` and only `dl/azahar`, `dl/moltenvk`, `dl/libretro-headers`, `dl/vulkan-headers`
   symlinked from MAIN (review 2 S8); in the clone: `make && PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/
   bin:$PATH make testapp`, then `tests/gate-a.sh build/testapp.3dsx` and `RUNNER=azhost tests/gate-b.sh`, nice'd,
   one at a time. A failure goes to the owning builder by SendMessage (A for gate-a and the azhost interface, B for
   its app and checker); it fixes in its worktree, the main loop recommits on the step branch and repeats this step.
   Both outputs become the items' Evidence.
5. **Main.** Merge `step-a`, `step-b` and `step-f1` into main. In the same pass the main loop commits:
   - `.gitignore`: F1 `*.tar.xz`, `*.tar.gz`, `*.orig`, `*.rej`; A `*.plist`, `*.dSYM/`; B `*.elf`, `*.smdh`,
     `*.shbin`, `*.lst`, `*.map` (`build-core/` and `testapp/build/` are already covered by `build-*/` and `build/`);
   - `docs/map/code.md`: one line each for `core/`, `host/`, `testapp/`, `tests/` and the top-level `Makefile`;
     `docs/map/tools.md`: `tests/` (gate-a.sh, gate-b.sh, check_testapp.py), `tools/build-core.sh`,
     `tools/untar_checked.py` (map_check.py:7-9 fails without them; each report gives its lines); `docs/map/runners.md`:
     the run blocks from A's and B's reports and F1's build command;
   - each report's "Lessons and notes" block into its item, Evidence lines, items 120 and 130 to done, 110 to done
     (its gate is configure plus the reds; the build's result is F2's), hours rows;
   - then `python3 -I tools/mkmap.py && python3 -I tools/status_check.py --strict-handoff && python3 -I
     tools/map_check.py`, and the progress page.
6. **The core build, in MAIN.** MAIN already holds `dl/azahar-src/src.tar.xz`. From MAIN's root:
   `nice -n 10 tools/build-core.sh --detach`; check `kill -0 "$(cat build-core/build.pid)"` and read the first lines
   of `build-core/build.log` once. Start one background waiter in MAIN (a bounded loop, at most 3 h, 60 s polls,
   no `pgrep`): each poll, if `build-core/build.exit` exists, print its code and exit; else if `kill -0
   "$(cat build-core/build.pid)"` fails, print "build died without an exit code" and exit at once (an OOM kill or
   SIGKILL in the LTO link leaves no exit file). The waiter's exit wakes the main loop, which books the result for
   F2. The build directory `build-core/build` stays in MAIN, so a later patch fix recompiles only the patched files.
7. **Clean up.** `git status --porcelain` empty in each step worktree and the integration worktree, then `git worktree
   remove` all four; delete `int-1` (and the step branches once merged).

## Interfaces for Phase 2

Checked against `docs/plans/phase-2.md` section 5, `phase-c.md` and `phase-d.md` (revision 1, commit c54a7dd). Every
row of Phase 2's table now holds as written in Phase 1's briefs, including the five it marked "R2":
- **A4:** `azh_boot` runs no `retro_run`; the NULL-first-frame check is made on the first `retro_run` of the first
  batch (`AZH_E_BOOT` from `azh_run`); every `retro_run` since boot counts toward the absolute frame (phase-a
  section 3).
- **A18:** `AZH_FMT_RAW` returns `AZH_E_UNSUPPORTED` until step C (C2 implements it; phase-a section 3).
- **A19:** the readback runs after `retro_run` returns on shot frames, and `azh_shot` reads back the last frame after
  a batch; `set_image` copies the image handle, which stays valid until the core's next `wait_sync_index`, inside the
  next `retro_run` (phase-a section 2).
- **abi_layout:** `azh_abi_layout` and `azh_error` work in any state, before `azh_open` too (D's `test_abi.py`).
- **B10:** the app never exits on a button, START included; it leaves only on `aptMainLoop()` false, `exit_at` or the
  frame cap (phase-b section 3).
- **B11:** `tests/check_testapp.py` exposes `read_png_rgba(path) -> (width, height, rgba_bytes)`, RGB expanded to
  RGBA, raising `ValueError` on unsupported PNGs, the CLI behind `if __name__ == "__main__":` (phase-b section 4).

Earlier rows that still hold from revision 1: A9 (`crop.c` is A's, pure), A14 (all 25 `retro_*` symbols loaded),
A17 (`AZH_E_ORDER` -2, `AZH_E_SAVESTATE` -10 reserved), A3 (`n` counts records), A12 (`LAZ_MVK`), A13 (validation
at `azh_set_option`), no `azhost info`, `tests/test_version.c` (A's; C may take it over), B3 (`v` is 2D only;
`booted ... sum=`), B4 (3D loop order), B5 (break runs on), B6 (busy boot), B8 (filter-0 PNGs only; step E extends
the decoder if it adds filters). A6: the state struct holds the sysdir already (the env callback needs it), so C1
has nothing to add there.

What Phase 2 should change or note:
- **Importing `check_testapp`:** `python3 -I` implies `-P` (Python 3.11+), so the script's own folder is *not* on
  `sys.path`. `tests/testapp_log.py` and D's tests must insert the absolute `tests/` path themselves (or run under
  pytest's rootdir handling) before `import check_testapp`.
- **The record layout** (for step G, Phase 3): 32 bytes, no padding; offsets magic 0, frame 4, vblank 8, keys 12,
  tx 16, ty 18, cx 20, cy 22, tick 24 (phase-b section 3).
- **Debug text on the stock core** (review 2 N11): the stock core does forward `svcOutputDebugString` at
  `RETRO_LOG_DEBUG`; only the host's info threshold hides it. So C's "debug-text stop on our core only" is a speed
  choice, not a necessity; C may say so or allow it on stock with `LAZ_LOG_LEVEL=debug`.
- **The core build** now starts in MAIN after Phase 1's merge, not during Phase 1; F2's input is MAIN's
  `build-core/azahar_lazpy_libretro.dylib` and `build-core/build.log` (no copy from a worktree).

PLAN.md notes from review 1 (recorded only; PLAN stays as it is): PLAN 2.6's "retro_load_game returns false for a
non-3DS file" holds only for loaders that read a header early (N12, S1); PLAN 2.4's "SD writes run on host threads
(file.cpp:240)" is wrong for SD files, which write synchronously (N5).

## Changes from review 2

| Finding | Outcome |
|---|---|
| X1 Interfaces for Phase 2 incomplete | done: A4, A18 (RAW until C), B10, B11 and the any-state `azh_abi_layout`/`azh_error` rule in phase-a/phase-b and above |
| X2 `laz_record` 40 bytes | done: `pad[2]` dropped; 32 bytes, `tick` at 24, both asserted; step G's offsets listed |
| S1 F1's build before review | done: F1 stops after configure and the reds; the main loop runs `--detach` in MAIN after the review and the integration run ("Merge and launch" 6); the old worktree-keeping step is gone; the incremental-rebuild note in phase-f1 section 4 |
| S2 Movie check order | done: the Movie check is step 2, before any patch; no hand edit of 0000 |
| S3 waiter vs a killed build | done: the waiter checks `kill -0` on every poll; the script traps `EXIT INT TERM HUP` |
| S4 no-window check vacuous | done: its own 3000-frame run, `kill -0` before and after `lsappinfo` |
| S5 readback sync | done: mutex, wait idle, barrier, copy, barrier back, submit, wait; no semaphores from the core |
| S6 map edits | done: code.md and tools.md lines in "Merge and launch" 5; each report gives its lines |
| S7 cross-step gates before main | done: the integration branch `int-1` and its clone run ("Merge and launch" 4); failures go back by SendMessage |
| S8 `dl/` copied twice | done: only the four needed `dl/` folders and `vendor/`, symlinked, in both the clone and gate-a's copy |
| S9 2D markers vs `boot_frames` | done: drawn in the first two main-loop frames after the busy boot |
| N1 `.def` notice placement | done: after line 2 |
| N2 deployment target, `cd "$ROOT"` | done |
| N3 full or relative paths | done: relative, as the sample shows |
| N4 CMakeLists.txt:431 fact | done: corrected in phase-f1 section 2; externals' build time noted |
| N5 0006 also on `retro_reset` | done: noted, F2 decides |
| N6 `-isystem vendor` | done |
| N7 build outputs in the diff | done: the `--cached --name-only` net in "Merge and launch" 3 |
| N8 default SMDH icon | done: in B's report for Phase I's audit |
| N9 no `timeout` on macOS | done: background pid plus a bounded `kill -0` loop, in B and in F1's configure wait |
| N10 slow rerun inside the script | done |
| N11 stock core forwards debug text | done: phase-b section 2 and "What Phase 2 should change" |
| N12 header step already done | done: "Before the launch" 2 marked done |
| As-built review conditions | done: checklists in order, findings to disk as it goes, fixes by SendMessage, re-check only changed items |
| Hour-saving "symlink `dl/` and `vendor/`" | done (S8) |
| Phase 2's asks (item 100's notes): no exit on START, `read_png_rgba`, RAW until C, `azh_boot` runs no `retro_run`, abi_layout before open | all done (X1) |

Declined: none.

Hour-saving pass of this revision (Guy's rule), per step:
- F1: the Movie check first (no patch rewritten, one checkpoint rerun fewer); no launch by the builder; the build
  later in MAIN keeps its build directory, so any F2 fix is an incremental rebuild, not 15-90 min. Online: a
  prebuilt core with our patches does not exist (our patches are ours), so there is nothing to download instead.
- A: `dl/` and `vendor/` symlinked in the gate copy (about 100 MB not copied per gate run); check 4's own short run
  instead of a longer wait. Considered and kept: our own 60-line PNG writer over vendoring `stb_image_write.h` (a
  1,700-line header to audit for one function).
- B: `read_png_rgba` serves Phase 2 too, so C and D write no decoder; the slow-run rerun inside the script saves a
  main-loop judgement and a rerun by hand.
- Phase: the integration run on a throwaway branch catches A/B mismatches before main, where a fix would cost a
  revert commit; one review lane, as before.

## Changes from review 1

| Finding | Outcome |
|---|---|
| X1 patch stack | done: patches made and applied as a stack, `0000-lazpy-notices.patch` holds every notice, `--fuzz 0`, no dry run, a reject removes the tree (phase-f1 sections 1, 3, 4, 5, 10) |
| X2 svcBreak | done: the guest runs on; gate 5 expects `break f=120` then `f=121` (phase-b sections 1-3) |
| X3 citro3d VBlank0 slot | done: our callback only before `C3D_Init`; 3D uses `C3D_FrameBegin(SYNCDRAW)`/`C3D_FrameEnd(0)` and `C3D_FrameCounter(0)` (phase-b 2, 3, 10) |
| S1 text file boot path | done: the facts line fixed; the text file is the context_reset case; step 4 plants nothing else |
| S2 readback size | done: sized from the first HW frame, grown if needed, both logged |
| S3 SET_VARIABLES lifetime | done: strings copied; callback and store live before `retro_set_environment` in `azh_open` |
| S4 32 keys | done |
| S5 version check test | done: check 6(a) missing symbol, 6(b) `azh_version_ok` and `make test-version` |
| S6 gate copy location | done: `mktemp -d` under `$TMPDIR`, trap, `KEEP=1`, absolute `$1`, checks 2-6 inside the copy |
| S7 pin 2126.2 | done: pinned in section 3; `azhost info` cut |
| S8 log formats | done: every argument cast; no `<inttypes.h>` |
| S9 azhost branch of gate-b | done: A's exact run line, file names, frame count and log path pasted into phase-b section 2 |
| S10 red 1 download | done: a present bad file is refused and kept; only a missing file is downloaded; `SRC_FILE` may be absolute |
| S11 item files | done: builders write no item files; each report ends with a "Lessons and notes" block |
| S12 merge plan | done: (a) `make testapp` in the clone, (b) the bounded waiter, (c) the `dl/` move marked done |
| S13 names | done: branches `step-f1`/`step-a`/`step-b`, the MAIN path in every brief |
| N1 Gen3D fixture | done: byte count dropped; no Gen3D path in any created file; the usage line names `build/testapp.3dsx` |
| N2 `.handle` non-NULL | done |
| N3 `make check` | done: `-o /dev/null`; the fallback clause removed |
| N4 env rows not sent | done: labelled "not sent" |
| N5 SD write safety | done: the log opened once, never reopened per line; an existing `/testapp` is success |
| N6 2D redraw | done: both buffers cleared once; only the digits redrawn |
| N7 `v` jumps | done: reported as `vjumps`, not a failure |
| N8 option default field | done: each row's `default_value` field set |
| N9 thin LTO | done: noted in F1's A3 |
| N10 scm_rev for F2 | done: recorded in F1 section 2 |
| N11 merge as each review passes | declined: one combined review saves about 0.45 h of opus time, and F1's merge is not urgent (F2 is Phase 3); merge order still does not matter |
| N12 PLAN notes | done: recorded above; PLAN unchanged |
| Q1 `async_fs_operations`, `init_ticks_type` | done: both kept, with review 1's reasons in F1 section 2 |
| Q2 version string | done: `2126.2` (S7) |
| Q3 boot within 120 frames | done: kept at 120, measured offset reported |
| Q4 exit path to status 16 | done: the confirmed chain written into phase-b section 2 |
| Q5 3D markers exact | done: B3 fallback kept, after the X3 fix |
| Hour-saving rows (pin now, cut `info`, no planted boot failure, version test, defer RAW, no dry run, no red download, shorter fe2 runs, filter-0 decoder, no item files) | all taken |

Hour-saving pass of this revision (Guy's rule), beyond review 1's rows: one combined opus diff review instead of three
(about 0.45 h); A's `crop.c` and the serialize symbols now, so Phase 2's C and D skip a move and an edit; B's busy
boot now, so D's state-boot check needs no B rework. Checked and kept: fe2 as B's runner (cheaper than waiting for A);
`tools/fetch.sh` reused as is; no third-party PNG library (zlib and 60 lines of our own are cheaper to audit than a
vendored one).
