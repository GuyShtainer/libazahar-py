# Phase 6 plan: release v1.0.0

Revision 2, 2026-11-13 11:20, main loop. Answers review 1 (`docs/reviews/phase-v1-review-1.md`, tags [R1-*]) and
review 2 (`docs/reviews/phase-v1-review-2.md`, tags [R2-*]). Two reviews done: work starts from this revision.

Guy, 2026-11-13: "Ok i see why its not 1. Than do all the proper tests and builds to make it version 1", and
"Dont forget to use the gen3d and 3dp agents for real live testings". The reasons it was 0.1 (STATUS.md): the ABI may
still change, the poll-exact movie is untested, the instance cap rests on a light scene, the core's header says
macOS 11.0, and no user had confirmed real use on the release candidate. This phase closes each one, or moves it out
of the 1.0 promise in writing.

## 1. What 1.0 means (the promise)

- Semantic versioning from 1.0.0. Covered, changed only compatibly until 2.0 (additions are minor releases): the
  public Python API (`libazahar.__all__`: names, arguments, return types, error classes); the C functions in
  `host/azhost.h` at source level (names and meaning; struct layouts may grow with an ABI bump, so C callers rebuild
  for each release) [R2-B1 fix]; the `azhost` command line, its exit-code table and the keys of its summary line (new
  keys may be added); the input-script file and the option-profile file, in the formats USING.md writes down (V1);
  the environment variables of USING.md section 15 [R2-B2]. [R1-S8]
- Host and Python are one unit [R1-B1, R2-B1 fix]: use the host library and the Python package from one checkout or
  one release. Mixing is unsupported; the layout check raises `HostError` when the ABI or layout differs. So
  `AZH_ABI_VERSION` may bump in a minor release; it is not part of the promise.
- States [R1-S1, R2-S1 fix]: a state loads in every later 1.x host on the same core revision; a v1.0.0 test-app state
  kept under `runs/release-fixtures/` (outside git) is loaded at every 1.x release (V7). Across core revisions (lazpy.N)
  it is tested at each release (the old core's state into the new core and back, step K's test) and the result goes
  in the release notes.
- Core lazpy.1 support (the host's suffix list) is not part of the promise and may go in any 1.x release. [R1-S8]
- Assets: every 1.x tag uploads the full asset set (core, source, build files, test app), as release_check's check
  11 and `expected_assets` require; `tools/fetch.sh`'s REL_TAG follows the newest tag. [R1 nit]
- Platforms as tested [R2-S6]: macOS 15 or later on arm64 (tested on 15.8); Python 3.10 or newer is the declared
  floor, tested on 3.14 here and on 3.10 by CI once pushed (V5), and the docs say exactly that.
- Everything STATUS.md lists under "What works" has a gate that ran on the lazpy.2 core, or is labelled with the core
  it ran on. Anything not gated is listed as "not in 1.0", never as working. The build route gated on lazpy.2 is
  core/PIN-nokeys; STATUS's build line names it [R2-S2].

## 2. Decisions taken by default (Guy may overrule any; each is reversible until the push)

- D1. v1.0.0 is the first public release. v0.1.0 was staged, never tagged or pushed. `docs/release-notes/v0.1.0.md`
  is deleted in V4 [R1 nit]; `runs/release/v0.1.0` stays until v1.0.0 is staged.
- D2. The 1.0 core is 2126.2-lazpy.2, built from core/PIN-nokeys on main. This settles the audit's R1 (the default
  route no longer downloads the key-bearing tarball).
- D3. Audio output is not in 1.0. It is a 1.x addition when 3DPlatinum's sound lane sends its ask.
- D4. macOS 15 or later, arm64 only (the lazpy.2 core's header says 15.0).
- D5. Poll-exact movies are not in 1.0 [R1-B4]: the core exports `lazpy_movie_play`, but the host and Python do not
  call it, there is no movie writer, and the test app reads input once per frame. The export stays.
- D6. V6 has no deadline [R1-S9]: v1.0.0 is not staged without both projects' answers on the final core.

## 3. Steps, in order

Each step is an item under laz-600 (created when it starts). Hours book to `phase-6`, except step K's (phase-5).

- **V0a. Step K's gates in the worktree** (item laz-510). Gates 1, 3, 4 and 6 passed (2026-11-13). Gate 2 (the
  worktree's full pytest) is dropped [R2 hour-saving]: that core is replaced by main's build, and the full suite runs
  on the final core in V7. 3DPlatinum's A1 passed; its A4 moves to V6 on the final core, headless counts accepted
  [R2 hour-saving]. 3DPlatinum is asked to stop using the worktree, so V1's edits there touch no one [R2-B3].
- **V1. API freeze review and changes** (opus review, read-only, now; then the main loop codes the changes on branch
  core-rev2 once 3DPlatinum has left the worktree [R2-B3]). The review reads `libazahar.__all__`, `host/azhost.h`,
  the exports list, `azhost`'s usage, exit codes and summary line, the input-script and option-profile parsers
  (`python/libazahar/emulator.py:27-36`, `host/azhost_main.c:269-296`), the environment variables and USING.md. It
  lists each name, default or behaviour we would regret freezing, "change before 1.0" or "keep". Fixed scope
  [R2-B2]: one strict option-profile format (`key=value`, `#` comments in column 0, blank lines skipped, the later
  line wins, an unknown key's behaviour stated), both parsers made to follow it with one test each, USING section 14
  documenting it, and a USING exit-code table. Text fixes: "v0.1.0 core" → "the lazpy.1 core" in `host/pins.h:6` and
  `tests/python/test_threads_live.py:128` [R2 nit]. Gate: make, make test-host, the fast pytest and the changed tests
  pass on the branch. Any change to `core/patches` lands before V0b's build.
- **V0b. Merge and rebuild on main** [R1-B2, B3, B5], one block; the hold on Gen3D and 3DPlatinum lasts from step 1
  to step 8 (about 30 minutes: the build takes about 10) [R2-B5 note, R2 hour-saving]:
  1. Announce to Gen3D and 3DPlatinum, and wait until neither has any run going on main's libazahar-py.
  2. `cp` MAIN's build-core dylib to `runs/core-lazpy1/` (step K's `LAZ_CORE_OLD`, and the rollback).
  3. `cp` (not `ln`) `runs/release/v0.1.0/azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` to
     `dl/azahar-src/src-nokeys.tar.xz`, and check its sha256 against PIN-nokeys' `SRC_SHA256` (f7a70044…). Rerun
     mkrelease's `tar` line (`tools/mkrelease.sh:59-73`) from `src.tar.xz` into the scratchpad and compare with
     f7a70044… [R2-S3]; a mismatch means a new pin before step 6.
  4. Merge core-rev2 into main (no fast-forward; exact paths checked), then `make`, then the fast pytest.
  5. On main: `core/PIN-nokeys`'s `SRC_URL` (`:8`) v0.1.0 → v1.0.0; commit. From here on, no edit to `core/` or
     `tools/build-core.sh`, and no `build-core.sh` run of any kind (no `--configure-only`, no `LAZ_CORE_PIN=core/PIN`)
     on main, or the gated build is invalid [R2-S2].
  6. Move `build-core/build` aside to `runs/core-lazpy1/build-old` [R2-S4], then the full core build on main.
  7. Gate 1 of step K on main (build.inputs, minos, version, exports, `gate_f2.py --only keyblob,symbols,version`),
     the fast pytest, and `tests/python/test_threads_live.py` with `LAZ_CORE_OLD=runs/core-lazpy1/...` and
     `LAZ_REQUIRE_EMULATOR=1` (about a minute) [R2 hour-saving].
  8. Release the hold. 3DPlatinum's `LAZ_ROOT` is MAIN again. The worktree is removed only after step 7 passes and
     `git status --porcelain --ignored` there holds nothing we need.
- **V3. Real-scene multi-instance row** [R1-S2, S6, R2-B1]. Method of `docs/research/real-scene-j.md`: Gen3D's .3dsx
  pinned by sha256, the game and world cache from a seed folder outside both repos, nothing written in Gen3D's tree,
  no game name in our docs. A scene script in the scratchpad (about 40 lines) imports `cap_rule` and `md_core_table`
  from `tools/speed_table.py` and builds their rows itself (`n`, `total_host_fps`, `load_end`, `check_ok`). Each
  instance warms up past the 3D-world frame (about 3000, real-scene-j.md:6-7), then all measure in one window shared
  through a barrier inside the Pool job. `check_ok` comes from a guest signal: Gen3D's `voxel.log` flip lines per
  wall second (USING section 12) agreeing with host fps within 10 %, and a shot at the start and end of each window
  showing the 3D world. On main's lazpy.2 core: 1, 2, 3 and 4 instances (`LAZ_MAX_INSTANCES=4` for the run), plus one
  interleaved 1-instance row on Azahar's own core. Quiet: load under 6 at the start, and no other session's emulator
  or CPU-heavy process (builds too) in `ps` from start to end [R2-S6]. A CHECK FAIL keeps the cap at 2, not
  `cap_rule`'s 3. A cap change edits `python/libazahar/_slots.py:25` and `tests/python/test_slots.py` before V6 and
  V7. Gate: the rows and the cap in USING.md's speed table with date and machine; STATUS.md drops "provisional"; the
  light-scene rows are labelled "core lazpy.1, 2026-11-13" or rerun with `tools/speed_table.py` in the same window.
- **V4. Version and docs** (after V1 and V3 [R1-S7]). `__version__` and pyproject `1.0.0`; `tools/fetch.sh` REL_TAG
  `v1.0.0` and `LAZPY_CORE_ZIP` (lazpy.1 → lazpy.2) with its sha pins set to `TBD` until V8 (`pin_set` refuses
  `TBD`, `fetch.sh:95-97`) [R2 nit]; STATUS.md rewritten for 1.0 (the version and commit line, poll-exact as not in
  1.0, the macOS 11.0 header limit gone, the ABI line replaced by section 1's promise, the stock-core download line,
  `threads()` and `init_ticks_override` in "What works" with laz-510, the build line naming PIN-nokeys); README's
  version line and measured numbers; `docs/map/runners.md`'s v0.1.0 commands; USING.md's four poll-exact places,
  found by text ("Poll-exact", "poll-exact"), not line numbers [R2 nit], say "our core exports it; the host and
  Python do not call it"; the usage examples in `tools/mkrelease.sh:17` and `tools/release_check.py:4` become
  `<tag>`; `docs/release-notes/v1.0.0.md` written (the change list; "macOS 15 or later"; no speed tokens, no "keys"
  outside the allowed phrases, `release_check.py:646-655`); `docs/release-notes/v0.1.0.md` deleted; NOTICES.md
  regenerated from main's build (`tools/mknotices.py`). Gate: docs_check, map_check, and release_check's docs and
  version checks at V8 (check 15 runs only with `--pre-push`).
- **V5. CI workflow, prepared** [R2-S5]. `.github/workflows/test.yml` with `permissions: contents: read`, a
  macos-15 arm64 runner, `actions/checkout` and `actions/setup-python` pinned by commit SHA, Python 3.10 and 3.14;
  steps: `tools/fetch.sh --headers` (two headers and the Vulkan-Headers tarball; never the core), `make`,
  `make test-host`, `pip install -e . pytest numpy`, the fast pytest (`-m "not slow"`). It runs only after Guy's
  push. Gate: the same steps pass in a fresh `git clone` under `env -i` (as `tools/clone_check.sh` does), and a
  YAML parse; STATUS.md "Next" says CI starts at the push.
- **V6. Users confirm on the final core** (Guy: "use the gen3d and 3dp agents for real live testings") [R1-S9].
  Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4) each run their own real suite on main after V0b and V4
  (`LAZ_ROOT` MAIN, the core's sha256 given to them), and reply pass or fail with numbers. 3DPlatinum's run includes
  its A4 count lines (headless counts accepted). Answers on the worktree core stay as step K's evidence only. A fail
  blocks V8. D6: no deadline; a silent project is asked again after each of its lanes ends.
- **V7. Full test pass on the candidate** (quiet machine) [R1 hour-saving]: host C tests, the full pytest with
  `LAZ_REQUIRE_EMULATOR=1`, `LAZ_STOCK_CORE` and `LAZ_CORE_OLD` (the state test across core revisions, standing
  [R1-S1]), `tests/gate_f2.py --stock`, memory_watch, map, status and docs checks; then make the v1.0.0 fixture
  state under `runs/release-fixtures/` [R2-S1]. Gate: 0 failed, 0 unexpected skips, counts in laz-600's Evidence.
  `clone_check` in V8 stands for the plain full pytest from a clean clone.
- **V8. Release staging and the legal re-audit** [R1-S4, R2-S1], in this order: rebuild the test app from source
  under `env -i` and compare its sha256 with 53b699e8… (a difference is noted; clone_check covers it) [R2 nit];
  `sh tools/mkrelease.sh v1.0.0`; write the zip and test-app sha256s into `tools/fetch.sh`; commit;
  `sh tools/mkrelease.sh v1.0.0` again; clone_check; the release-legal-audit agent on the repo, its history and the
  staged assets (mandatory before the first push); commit its report (and the status, hours and handoff); then
  `sh tools/mkrelease.sh v1.0.0` once more (the zip and test-app sha256s must not change), then
  `python3 -I tools/release_check.py runs/release/v1.0.0 --pre-push` with LAZ_PRIVATE_NEEDLES: 16 of 16. No commit
  after that until the tag. Gate: a shippable verdict under docs/reviews/, 16 of 16 on the final HEAD.
- **V9. Waits on Guy:** repo creation, the word "push", the tag and publishing the draft (phase 4's G5-G7) [R1-S5]:
  `git tag -a v1.0.0 -m "libazahar-py 1.0.0"` on the HEAD V8 checked, push main and the tag only, then
  `gh release create v1.0.0 --draft --verify-tag --title "libazahar-py 1.0.0" --notes-file docs/release-notes/v1.0.0.md`
  followed by the explicit list of staged asset files from `runs/release/v1.0.0` (no `--prerelease`) [R2 nit]. Then
  I5 of `phase-i.md` section 6 against v1.0.0, and the three private history bundles deleted.

## 4. Order and overlap

Now: V1's review (opus, read-only) and V5 (no emulator). V1's code changes on the branch once 3DPlatinum has left the
worktree. Then V0b (a 30-minute hold, when Gen3D's timed lane has ended), V3 (quiet machine), V4, V6 and V7, V8.
Rule T: no two timed runs overlap, ours or another session's.

## 5. Hours (estimates; actuals go to docs/hours.tsv)

V1 0.5 review + 1.0 changes, V0b 0.7, V3 1.0, V4 1.0, V5 0.5, V6 0.3 (our side), V7 0.5, V8 1.0. About 6.5 hours,
plus the users' runs and Guy's steps. Dropped: V2 (poll-exact, 1-4 h) and V0a's gate 2 (0.3 h and a quiet window).

## 6. Risks

- V0b changes main's host, Python and core under two other projects: one announced 30-minute hold when neither runs
  anything, with the lazpy.1 dylib kept for rollback [R1-B5].
- V1 may want a breaking rename: cheap now, impossible after 1.0. It lands before V0b's build.
- V3 needs a quiet machine; other sessions' long gates may delay it. It does not block V1, V4 or V5.
- A main rebuild may not reproduce the worktree core's bytes; V6 therefore runs on main's final core sha only.
- Not pinned yet: the host's minos 15.0 comes from the toolchain default, not the Makefile; a later release pins
  `-mmacosx-version-min=15.0` [R2 nit].
