# Phase 1, foundation: the index (item laz-100)

Opus phase plan, 2026-11-12, revision 1 (after `docs/reviews/phase-1-review-1.md`), **draft for the second opus
review loop; nothing is built until it passes.** Three steps, each with its own brief for one sonnet builder in its
own worktree:

| Step | Item | Brief | What it delivers | Hours |
|---|---|---|---|---|
| F1 | laz-110 | `docs/plans/phase-f1.md` | our core's pin, patch stack, options profile and `tools/build-core.sh`; the first full core build started detached | 0.8 |
| A | laz-120 | `docs/plans/phase-a.md` | `build/libazhost.dylib` and `build/azhost` (boot, run frames, two-screen PNGs, options profile, version check, boot errors) | 1.15 |
| B | laz-130 | `docs/plans/phase-b.md` | `build/testapp.3dsx` (markers, per-frame log, record, break/exit/ready/busy-boot modes) and its checker | 0.9 |

## Hours

Builders: F1 0.6, A 0.95, B 0.7. One opus diff review for all three steps (a single big lane, Guy's "consolidate
expensive" rule) plus the commits: about 0.6 h, split 0.2 per step in the table. **Phase 1: 2.85 h** of agent time
(PLAN.md: 3.25 h; revision 0: 3.55 h). If the main loop prefers one review per step (0.35 each), the steps are
1.0 / 1.3 / 1.05 h and the phase 3.35 h. F1's detached build is machine time, not booked (15-25 min quiet, 40-90 min
at today's load).

## Order

All three start together (independent files, independent worktrees). F1's builder ends after configure and the
detached launch; the build keeps running. B uses `prototype/fe2.c` as its runner, so it does not wait for A. Nothing
in Phase 1 needs our core: A and B run on the stock core; our core's own gate is step F2 (Phase 3). The one review
starts when A and B have both reported (F1 reports first and waits; its merge is not urgent, F2 is in Phase 3).

## Before the launch (main loop)

1. The second review passes; commit the four plan files; `python3 -I tools/mkmap.py && python3 -I tools/map_check.py`
   (docs/plans/ is new).
2. `dl/` is already in fetch.sh's layout (`dl/azahar/` holds the zip and the dylib; done 2026-11-12). Run
   `tools/fetch.sh` once more in MAIN so `dl/libretro-headers/`, `dl/vulkan-headers/` and the `vendor/` stamp exist
   for the worktrees to copy.
3. Worktrees at main (check `git worktree list` and a case-insensitive name clash first):
   `git worktree add -b step-f1 ../libazahar-py-f1 main`, likewise `step-a` / `../libazahar-py-a` and `step-b` /
   `../libazahar-py-b`. Dispatch without isolation, cwd in the worktree.
4. Move items 110, 120, 130 from `2-next/` to `1-in-progress/` with their "Running now" rows; book hours rows.
   Builders never edit item files (their notes come back in the report), so the move on main cannot conflict.
5. No installs are needed (checked: devkitPro, CMake 4.3.4, ninja, Xcode 26.3, spirv-opt, shellcheck, Python 3.14).
   No Guy decision blocks the launch.

## File ownership (no two builders edit the same file)

| Owner | Files |
|---|---|
| F1 | `core/` (PIN, patches/, options-lazpy.txt, README.md), `tools/build-core.sh`, `tools/untar_checked.py` |
| A | top-level `Makefile`, `host/` (all), `tests/gate-a.sh`, `tests/test_version.c` |
| B | `testapp/` (all, including `testapp/Makefile` and `testapp/README.md`), `tests/check_testapp.py`, `tests/gate-b.sh` |
| main loop only | `.gitignore`, `docs/map/*` (incl. `runners.md`), root `README.md` (nobody this round), `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff, every item file |

`tests/` is shared as a folder only; each file in it has one owner.

## Merge plan

1. F1 reports first. The main loop then starts one background waiter in F1's worktree: a bounded loop on
   `build-core/build.exit` (at most 3 h, 60 s polls, no `pgrep`), which reads the exit code when the file appears.
2. When A and B have reported, the one opus diff review covers the three worktree diffs (each brief's section 10).
3. Commit each step from its branch with exact paths and `git diff --cached --stat` checked; merge into main in any
   order (no shared files). Paste each report's "Lessons and notes" block into its item.
4. `.gitignore` additions, merged once by the main loop: F1 `*.tar.xz`, `*.tar.gz`, `*.orig`, `*.rej`; A `*.plist`,
   `*.dSYM/`; B `*.elf`, `*.smdh`, `*.shbin`, `*.lst`, `*.map`. (`build-core/` and `testapp/build/` are already
   covered by `build-*/` and `build/`.)
5. `docs/map/runners.md` gets the run blocks from A's and B's reports and F1's build command; then mkmap and map_check.
6. After A and B are on main: a real `git clone` of main into a temp folder, `dl/` and `vendor/` copied in, then
   `make && PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (the clone has no
   `build/`), then `tests/gate-a.sh build/testapp.3dsx` and `RUNNER=azhost tests/gate-b.sh`. Both outputs become the
   items' Evidence.
7. F1's worktree stays until the build has exited (the waiter fired), and the dylib and `build-core/build.log` are
   copied into MAIN's `build-core/`; `git status --porcelain` empty before `git worktree remove`.

## Interfaces for Phase 2

Phase 2's plan (`docs/plans/phase-2.md` section 5) lists what it assumes from Phase 1. After this revision, every
row holds except these differences, which Phase 2's revision should absorb:
- **A9, the crop:** A now creates `host/crop.c` itself (pure, no Vulkan), so C does not move it; C may still edit it
  only if A's signature does not fit, and then it owns that change.
- **A14, savestate symbols:** A's `core.c` already loads all 25 `retro_*` symbols, including the three serialize
  ones; D adds no `dlsym` lines.
- **A17, error names:** A's code -2 is `AZH_E_ORDER` (call order), and A's header already reserves
  `AZH_E_SAVESTATE = -10`; C1 does not add it.
- **A1, raw shots:** `AZH_FMT_RAW` is in the header, but A returns `AZH_E_UNSUPPORTED` for it; the map's pixel area
  exists and stays zero. Raw shots are D's (their first user); Phase 2's table should say so.
- **A3, `n`:** now stated: `n` counts input records of `AZH_INPUT_INTS` (7) int32, as Phase 2 assumed.
- **A12, MoltenVK:** now stated: the library reads `LAZ_MVK`; `azhost --mvk` only sets it. As Phase 2 assumed.
- **Options:** `azh_set_option` validates against the registered keys at once (`AZH_E_ARG` at set time, not at
  boot), because SET_VARIABLES arrives inside `azh_open`.
- **`azhost info` is cut:** the core name and version are in host.log on every boot; F2 uses `nm -gU`.
- **Tests:** A adds `tests/test_version.c` and `make test-version`; C's `make test-host` may absorb it (A owns it in
  Phase 1; C may take it over).
- **B3, `v`:** in 3D mode `v = C3D_FrameCounter(0)` and restarts at citro3d's start; `v` is only meaningful in 2D.
  B's gate reports `v` jumps without failing (one `v` per frame stays C(d)'s check). The `booted` line gains
  `sum=%08lx`.
- **B4, loop order:** 2D as Phase 2 assumed; 3D is `C3D_FrameBegin(SYNCDRAW)` (it waits for the VBlank), then
  `hidScanInput`, record, log, draw, `C3D_FrameEnd(0)`, so input is still sampled right after a VBlank.
- **B5, svcBreak, resolved as Phase 2 asks:** the app logs `break f=N`, calls `svcBreak` and runs on (`f=N+1`
  follows).
- **B6, busy boot, resolved as Phase 2 asks:** boot frames spin a bounded busy loop until the vblank counter moves, no
  VBlank wait; `boot_frames` up to 10,000 (D's 6,000 fits).
- **B8, PNG filters:** `tests/check_testapp.py` decodes filter-0 PNGs only and fails loudly on others. If step E's
  PNG tuning adds filters, E extends the decoder.

PLAN.md notes from review 1 (recorded only; PLAN stays as it is): PLAN 2.6's "retro_load_game returns false for a
non-3DS file" holds only for loaders that read a header early (N12, S1); PLAN 2.4's "SD writes run on host threads
(file.cpp:240)" is wrong for SD files, which write synchronously (N5).

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
