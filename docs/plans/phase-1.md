# Phase 1, foundation: the index (item laz-100)

Opus phase plan, 2026-11-12, **draft for two opus review loops; nothing is built until both pass.** Three steps,
each with its own brief for one sonnet builder in its own worktree:

| Step | Item | Brief | What it delivers | Builder + review |
|---|---|---|---|---|
| F1 | laz-110 | `docs/plans/phase-f1.md` | our core's pin, patches, options profile and `tools/build-core.sh`; the first full core build started detached | 1.0 h |
| A | laz-120 | `docs/plans/phase-a.md` | `build/libazhost.dylib` and `build/azhost` (boot, run frames, two-screen PNGs, options profile, version check, boot errors) | 1.45 h |
| B | laz-130 | `docs/plans/phase-b.md` | `build/testapp.3dsx` (markers, per-frame log, record, break/exit/ready/slow-boot modes) and its checker | 1.1 h |

Phase 1 total: 3.55 h of agent time (PLAN.md: 3.25 h), plus F1's detached build (15-25 min of machine time at 4 jobs,
not booked).

## Order

All three start together (independent files, independent worktrees). F1's builder ends after configure and the
detached launch; the core build keeps running and wakes the main loop when it exits. B uses `prototype/fe2.c` as its
runner, so it does not wait for A. Nothing in Phase 1 needs our core: A and B run on the stock core; our core's own
gate is step F2 (Phase 3).

## Before the launch (main loop)

1. Both review loops pass; commit the four plan files; `python3 -I tools/mkmap.py && python3 -I tools/map_check.py`
   (docs/plans/ is new).
2. Move the main checkout's `dl/` into fetch.sh's layout: `mkdir -p dl/azahar && mv dl/stock-core.zip
   2126.2.zip dl/azahar_libretro.dylib dl/azahar/`, then `tools/fetch.sh` (it fetches the two small header sets once
   and stamps `vendor/`). Worktrees copy `dl/` parts and `vendor/` from there (each brief's step 0).
3. Worktrees at main (check `git worktree list` and a case-insensitive name clash first):
   `git worktree add -b step-f1 ../libazahar-py-f1 main`, likewise `step-a` / `../libazahar-py-a` and `step-b` /
   `../libazahar-py-b`. Dispatch without isolation, cwd in the worktree.
4. Move items 110, 120, 130 from `2-next/` to `1-in-progress/` with their "Running now" rows; book hours rows.
5. No installs are needed (checked: devkitPro, CMake 4.3.4, ninja, Xcode 26.3, spirv-opt, shellcheck, Python 3.14).

## File ownership (no two builders edit the same file)

| Owner | Files |
|---|---|
| F1 | `core/` (PIN, patches/, options-lazpy.txt, README.md), `tools/build-core.sh`, `tools/untar_checked.py`, its item's notes |
| A | top-level `Makefile`, `host/` (all), `tests/gate-a.sh`, its item's notes |
| B | `testapp/` (all, including `testapp/Makefile` and `testapp/README.md`), `tests/check_testapp.py`, `tests/gate-b.sh`, its item's notes |
| main loop only | `.gitignore`, `docs/map/*` (incl. `runners.md`), root `README.md` (nobody this round), `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff, item moves |

`tests/` is shared as a folder only; each file in it has one owner.

## Merge plan

1. Each builder reports; the opus diff review runs per step on its worktree diff (each brief's section 10).
2. Merge order A, then B, then F1 (no file overlaps, so order only matters for the follow-up runs): commit each from
   its worktree branch, merge into main, with exact paths and `git diff --cached --stat` checked.
3. `.gitignore` additions merged once by the main loop: F1 `*.tar.xz`, `*.tar.gz`, `*.orig`, `*.rej`; A `*.plist`,
   `*.dSYM/`; B `*.elf`, `*.smdh`, `*.shbin`, `*.lst`, `*.map`. (`build-core/` and `testapp/build/` are already covered
   by `build-*/` and `build/`.)
4. `docs/map/runners.md` gets the run blocks from the A and B reports and F1's build command; then mkmap and
   map_check.
5. After A and B are on main: a real `git clone` of main into a temp folder, `dl/` and `vendor/` copied in, and
   `tests/gate-a.sh build/testapp.3dsx` (A's gate on our own app instead of Gen3D's) and `RUNNER=azhost
   tests/gate-b.sh`; both outputs become the items' Evidence.
6. F1's worktree stays until the detached build has exited (`build-core/build.exit` exists) and the dylib and
   `build-core/build.log` are copied into the main checkout's `build-core/`; check `git status --porcelain` is empty
   before `git worktree remove`.
