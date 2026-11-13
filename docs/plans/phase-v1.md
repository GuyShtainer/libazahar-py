# Phase 6 plan: release v1.0.0

Revision 1, 2026-11-13 11:10, main loop. Answers review 1 (`docs/reviews/phase-v1-review-1.md`); tags [R1-*] name
its findings. Review 2 next, then work (two opus reviews before work, global rule).

Guy, 2026-11-13: "Ok i see why its not 1. Than do all the proper tests and builds to make it version 1", and
"Dont forget to use the gen3d and 3dp agents for real live testings". The reasons it was 0.1 (STATUS.md): the ABI may
still change, the poll-exact movie is untested, the instance cap rests on a light scene, the core's header says
macOS 11.0, and no user had confirmed real use on the release candidate. This phase closes each one, or moves it out
of the 1.0 promise in writing.

## 1. What 1.0 means (the promise)

- Semantic versioning from 1.0.0. Covered, changed only compatibly until 2.0 (additions are minor releases): the
  public Python API (`libazahar.__all__`, names, arguments, return types, error classes); the C functions in
  `host/azhost.h` (names and meaning); the `azhost` command line and its exit codes; the documented environment
  variables (USING.md section 16); the option-profile file format. [R1-S8]
- Host and Python are one unit [R1-B1]: the host library and the Python package from one checkout or one release go
  together. Mixing a host and a Python from different releases raises `HostError` (the layout check). So
  `AZH_ABI_VERSION` may bump in a minor release; it is not part of the promise.
- States [R1-S1]: a state loads in every later 1.x host on the same core revision. Across core revisions (lazpy.N)
  it is tested at each release (the old core's state into the new core and back, step K's test) and the result goes
  in the release notes.
- Core lazpy.1 support (the host's suffix list) is not part of the promise and may go in any 1.x release. [R1-S8]
- Assets: every 1.x tag uploads the full asset set (core, source, build files, test app), as release_check's checks
  11 and `expected_assets` require; `tools/fetch.sh`'s REL_TAG follows the newest tag. [R1 nit]
- Everything STATUS.md lists under "What works" has a gate that ran on the lazpy.2 core, or is labelled with the core
  it ran on. Anything not gated is listed as "not in 1.0", never as working.

## 2. Decisions taken by default (Guy may overrule any; each is reversible until the push)

- D1. v1.0.0 is the first public release. v0.1.0 was staged, never tagged or pushed. `docs/release-notes/v0.1.0.md`
  is deleted in V4 [R1 nit]; `runs/release/v0.1.0` stays until v1.0.0 is staged.
- D2. The 1.0 core is 2126.2-lazpy.2, built from core/PIN-nokeys on main. This settles the audit's R1 (the default
  route no longer downloads the key-bearing tarball).
- D3. Audio output is not in 1.0. It is a 1.x addition when 3DPlatinum's sound lane sends its ask.
- D4. macOS 15 or later, arm64 only (the lazpy.2 core's header says 15.0).
- D5. Poll-exact movies are not in 1.0 [R1-B4]: the core exports `lazpy_movie_play`, but the host and Python do not
  call it, there is no movie writer, and the test app reads input once per frame. A 1.x addition would need a writer
  that replays the core's input timing, a new open path and a test app change (4 h or more). The export stays.

## 3. Steps, in order

Each step is an item under laz-600 (created when it starts). Hours book to `phase-6`, except step K's (phase-5).

- **V0a. Step K's gates in the worktree** (item laz-510, `docs/plans/phase-k.md`). Gates 1, 3 and 4 passed
  (2026-11-13 11:04). Left: gate 2 (full pytest, held until Gen3D's timed lane ends, then the quiet-load gate),
  gate 6, 3DPlatinum's A4 numbers (its A1 passed).
- **V1. API freeze review** (opus, read-only, right after this plan's review 2, and before V0b's build because it
  may touch export names [R1-S7]). It reads `libazahar.__all__`, `host/azhost.h`, the exports list, `azhost`'s usage
  and exit codes, the environment variables and USING.md. It lists each name, default or behaviour we would regret
  freezing, marked "change before 1.0" or "keep". The main loop applies the changes with their tests on the branch.
  Gate: the fast pytest and the changed tests pass.
- **V0b. Merge and rebuild on main** [R1-B2, B3, B5], one block:
  1. Announce to Gen3D and 3DPlatinum, and wait until neither has any run going on main's libazahar-py (not only
     timed ones).
  2. `cp` MAIN's build-core dylib to `runs/core-lazpy1/` (step K's `LAZ_CORE_OLD`, and the rollback).
  3. `cp` (not `ln`) `runs/release/v0.1.0/azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` to
     `dl/azahar-src/src-nokeys.tar.xz`, and check its sha256 against PIN-nokeys' `SRC_SHA256` (f7a70044…).
  4. Merge core-rev2 into main (no fast-forward; exact paths checked), then `make`, then the fast pytest.
  5. On main: `core/PIN-nokeys` URL and header comment v0.1.0 → v1.0.0; commit. From here on, no edit to `core/` or
     `tools/build-core.sh` without another build.
  6. Full core build on main (30-60 min machine time; the dylib is replaced atomically by `mv -f`).
  7. Step K's gates 1 and 2 again on main (`LAZ_CORE_OLD=runs/core-lazpy1/...`).
  8. Tell both projects. 3DPlatinum moves its `LAZ_ROOT` back to MAIN. The worktree is removed only after this
     step's gates pass and `git status --porcelain --ignored` there holds nothing we need.
- **V3. Real-scene multi-instance row** [R1-S2, S6]. Method of `docs/research/real-scene-j.md`: Gen3D's .3dsx
  pinned by sha256, the game and world cache from a seed folder outside both repos, the scene script in the
  scratchpad, nothing written in Gen3D's tree, no game name in our docs. On main's lazpy.2 core: 1, 2, 3 and 4
  instances through `Pool` (with `LAZ_MAX_INSTANCES=4` for the run), plus one interleaved 1-instance row on Azahar's
  own core. Quiet means load under 6 at the start and no other session's emulator in `ps` from start to end. The
  criterion is `tools/speed_table.py`'s `cap_rule` (`:42-62`: a ×1.25 total gain, end load under 2×CPU).
  The guest-time check (rule 7): guest frames from `Stats` against wall time, and one shot per instance showing the 3D
  world. Gate: the rows and the chosen cap go in USING.md's speed table with date and machine, STATUS.md drops
  "provisional", and the light-scene rows are labelled with the core they ran on (lazpy.1, 2026-11-13) or rerun with
  `tools/speed_table.py` in the same quiet window.
- **V4. Version and docs** (after V1 and V3 [R1-S7]). `__version__` and pyproject `1.0.0`; `tools/fetch.sh` REL_TAG
  `v1.0.0`, `LAZPY_CORE_ZIP` (lazpy.1 → lazpy.2) and its pins (`fetch.sh:42-44`, set for real in V8); STATUS.md
  rewritten for 1.0 (`:3` version and commit, `:30` poll-exact as not in 1.0, `:46`, `:51` the ABI line becomes the
  promise of section 1, `:62`; add `threads()` and `init_ticks_override` to "What works", laz-510); README `:10` and
  its measured numbers; `docs/map/runners.md:75,81,82`; USING.md lines 46, 116, 147 and 233 say "our core exports it;
  the host and Python do not call it"; the usage examples in `tools/mkrelease.sh:17` and `tools/release_check.py:4`
  become `<tag>`; `docs/release-notes/v1.0.0.md` written (it is the change list; "macOS 15 or later"; no speed tokens,
  no "keys" outside the allowed phrases, `release_check.py:646-655`); `docs/release-notes/v0.1.0.md` deleted;
  NOTICES.md regenerated (`tools/mknotices.py`). [R1-S3] Gate: docs_check, map_check, and release_check's
  docs and version checks at V8 (check 15 runs only with `--pre-push`).
- **V5. CI workflow, prepared.** `.github/workflows/test.yml`: a macos-15 arm64 runner, `tools/fetch.sh --headers`
  (the `vendor/` includes, `Makefile:4`; never the core), `make`, `make test-host`, the fast pytest (`-m "not slow"`).
  It runs only after Guy's push; until then a YAML parse and its steps run locally. Gate: the steps pass locally;
  STATUS.md "Next" says CI starts at the push.
- **V6. Users confirm on the final core** (Guy: "use the gen3d and 3dp agents for real live testings") [R1-S9].
  Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4) each run their own real suite on main after V0b and V4
  (`LAZ_ROOT` MAIN, the core's sha256 given to them), and reply pass or fail with numbers. Earlier answers on the
  worktree core (3DPlatinum's A1 pass) are kept as evidence for step K, but V6 counts only runs on the final core
  sha. A fail blocks V8. No deadline: a silent project is asked again after each of its lanes ends; v1.0.0 is not
  staged without both answers.
- **V7. Full test pass on the candidate** (quiet machine) [R1 hour-saving]: host C tests, the full pytest with
  `LAZ_REQUIRE_EMULATOR=1` and `LAZ_STOCK_CORE` and `LAZ_CORE_OLD` (the state test across core revisions, a standing
  item [R1-S1]), `tests/gate_f2.py --stock`, memory_watch, map, status and docs checks. Gate: 0 failed, 0 unexpected
  skips, counts in laz-600's Evidence. `clone_check` in V8 stands for the plain full pytest from a clean clone.
- **V8. Release staging and the legal re-audit** [R1-S4], phase-i.md I2's steps as written (`phase-i.md:550-557`):
  rebuild the test app from source under `env -i`; `sh tools/mkrelease.sh v1.0.0`; write the zip and test-app
  sha256s into `tools/fetch.sh`; commit; `sh tools/mkrelease.sh v1.0.0` again (check 10 compares a HEAD archive);
  `python3 -I tools/release_check.py runs/release/v1.0.0 --pre-push` with LAZ_PRIVATE_NEEDLES: 16 of 16; clone_check;
  then the release-legal-audit agent on the repo, its history and the staged assets (mandatory before the first push).
  Gate: a shippable verdict saved under docs/reviews/, 16 of 16, and the tag goes on the exact HEAD the build-files
  asset came from (the re-audit's S4).
- **V9. Waits on Guy:** repo creation, the word "push", the tag and publishing the draft (phase 4's G5-G7) [R1-S5]:
  `git tag -a v1.0.0 -m "libazahar-py 1.0.0"`, push main and the tag only, then
  `gh release create v1.0.0 --draft --title "libazahar-py 1.0.0" --notes-file docs/release-notes/v1.0.0.md` with the
  staged assets (no `--prerelease`). Then I5 of `phase-i.md` section 6 against v1.0.0, and the three private history
  bundles deleted.

## 4. Order and overlap

Now: V0a waits on Gen3D's lane and 3DPlatinum's A4 run; this plan's review 2, then V1's review (one opus at a
time), run meanwhile, and V5 too (no emulator). Then V0b (after V1's changes land on the branch), V3 (quiet machine,
main's final core), V4, V6 and V7, V8. Rule T: no two timed runs overlap, ours or another session's.

## 5. Hours (estimates; actuals go to docs/hours.tsv)

V0a 0.5, V1 0.5 review + 1.0 changes, V0b 1.0 (plus 1 h machine time), V3 1.0, V4 1.0, V5 0.5, V6 0.3 (our side),
V7 0.5, V8 1.0. About 7.3 hours, plus the users' runs and Guy's steps. V2 (poll-exact) dropped: saves 1-4 h [R1].

## 6. Risks

- V0b changes main's host, Python and core under two other projects: one announced block when neither runs
  anything, with the lazpy.1 dylib kept for rollback [R1-B5].
- V1 may want a breaking rename: cheap now, impossible after 1.0. It lands before V0b's build.
- V3 needs a quiet machine; other sessions' long gates may delay it. It does not block V1, V4 or V5.
- A main rebuild may not reproduce the worktree core's bytes; V6 therefore runs on main's final core sha only.
