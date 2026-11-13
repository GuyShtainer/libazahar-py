# Phase 6 plan: release v1.0.0

Revision 0, 2026-11-13 10:58, main loop. Reviews: none yet (two opus reviews before work, global rule).

Guy, 2026-11-13: "Ok i see why its not 1. Than do all the proper tests and builds to make it version 1". The reasons
it was 0.1 (STATUS.md, "What does not work yet" and "Known limits"): the ABI may still change, the poll-exact movie
is untested, the instance cap rests on a light scene, the core's header says macOS 11.0, and no user had confirmed
real use on the release candidate. This phase closes each one, or moves it out of the 1.0 promise in writing.

## 1. What 1.0 means (the promise)

- Semantic versioning from 1.0.0: the public Python API (`libazahar.__all__`), the C ABI (`host/azhost.h`, the
  exports list) and the `azhost` command line change only in a compatible way until 2.0. Additions are minor
  releases. `AZH_ABI_VERSION` keeps counting layout changes; a 1.x host never refuses a 1.0 Python, and states made
  by any 1.x host load in every later 1.x host (same core source).
- Everything STATUS.md lists under "What works" has a gate that ran on the release candidate, on the release core.
- Anything not gated is either gated in this phase or listed as "not in 1.0" in STATUS.md, never as working.

## 2. Decisions taken by default (Guy may overrule any; each is reversible until the push)

- D1. v1.0.0 is the first public release. v0.1.0 was staged but never tagged or pushed; it is not published. Its
  staging stays in `runs/release/v0.1.0` until v1.0.0 is staged (the worktree's tarball link points into it).
- D2. The 1.0 core is 2126.2-lazpy.2 (step K), built from core/PIN-nokeys on main. This also settles the audit's
  R1: the default build route no longer downloads the key-bearing tarball.
- D3. Audio output is not in 1.0. It becomes a 1.x addition when 3DPlatinum's sound lane sends its ask.
- D4. macOS 15 or later, arm64 only. The lazpy.2 core's header says 15.0, which closes the "header says 11.0" limit.
- D5. The host keeps loading lazpy.1 cores (the suffix list) during 1.x only as a courtesy; the gated core is lazpy.2.

## 3. Steps, in order

Each step is an item under laz-600 (created when it starts). Hours book to `phase-6`, except step K's (phase-5).

- **V0. Step K lands** (item laz-510, `docs/plans/phase-k.md`). Gates 1-6 in the worktree, 3DPlatinum's A4/A1
  repros, then merge core-rev2 into main (no fast-forward, exact paths checked), then one full core build on main
  (review 2's S5; 30-60 min machine time; MAIN's build-core/ then changes, so Gen3D and 3DPlatinum are told first
  and their LAZ_CORE keeps working because the path is unchanged). Gate: plan K's gates 1-2 again on main.
- **V1. API freeze review** (opus, read-only). Read `python/libazahar/__init__.py`'s exports, `host/azhost.h`,
  `host/libazhost.exports`, `azhost`'s usage, USING.md sections 1-17. List every name, default or behaviour we
  would regret freezing (naming, error classes, units, optional arguments that should be keyword-only, the
  `azhost` exit codes). Output: a short list of changes, each "change before 1.0" or "keep". Main loop applies the
  "change" ones with their tests. Gate: the full pytest after the changes.
- **V2. Poll-exact movie gate.** A live test on the lazpy.2 core: the test app logs the buttons it reads on each
  poll; a `.ctm` movie made by our movie writer plays through `lazpy_movie_play` from boot; the logged buttons equal
  the movie, poll for poll, in two runs, and the two runs' logs are byte-equal. If the test app does not log per
  poll today, add that (test app source is ours). Gate: the test passes 3 runs in a row; USING.md lines 46, 116,
  147 and 233 change from "not tested" to the result. If it fails and the fix is not small, poll-exact moves to
  "not in 1.0" and its call stays documented as experimental.
- **V3. Real-scene multi-instance row.** On a quiet machine (rule T, quiet-load gate), Gen3D's 3D scene (its own
  .3dsx, run from Gen3D's tree read-only, the scene script kept in the scratchpad, no game name in our docs) at 1,
  2, 3 and 4 instances through `Pool`, on the lazpy.2 core: frames per second per instance and the machine load.
  The cap stays 2 or moves to the largest count that keeps each instance at full speed, with a margin. Gate: the
  row is in USING.md's speed table with its date and machine, and STATUS.md drops "provisional".
- **V4. Version and docs.** `__version__` and pyproject `1.0.0`; `tools/fetch.sh` REL_TAG; release_check's version
  check; STATUS.md rewritten for 1.0 (drop "early prerelease" and "The ABI may change before 1.0"; add the promise
  of section 1 and D3-D5); README and USING.md version lines; a CHANGES.md with 1.0.0's list; NOTICES.md regenerated
  (`tools/mknotices.py`). Gate: `python3 -I tools/release_check.py` checks 14 (versions) and the docs checks pass.
- **V5. CI workflow, prepared.** `.github/workflows/test.yml`: macos-15 arm64 runner, build the host, run the fast
  tests (no core, no emulator). It runs only once Guy pushes; until then it is checked with a YAML parse and by
  running its steps locally. Gate: the steps pass locally; STATUS.md "Next" says CI starts at the push.
- **V6. Users confirm.** Gen3D (3ds-toolkit-1c) and 3DPlatinum (3ds-toolkit-f4) each run their own real suite on the
  v1.0.0 candidate (main after V0-V4, `LAZ_ROOT` set to MAIN) and reply pass or fail with their numbers. Their
  replies go verbatim into item laz-600's notes. A fail blocks V8.
- **V7. Full test pass on the candidate.** Quiet machine: host C tests, the full pytest with
  `LAZ_REQUIRE_EMULATOR=1` and `LAZ_STOCK_CORE`, `tests/gate_f2.py`, memory_watch, map/status/docs checks. Gate:
  0 failed, 0 unexpected skips, the counts in item laz-600's Evidence.
- **V8. Release staging and the legal re-audit.** `sh tools/mkrelease.sh v1.0.0`, then
  `python3 -I tools/release_check.py runs/release/v1.0.0 --pre-push` with LAZ_PRIVATE_NEEDLES (16 of 16), then
  clone_check, then the release-legal-audit agent on the repo, its history and the staged assets (mandatory before
  the first push). Gate: shippable verdict saved under docs/reviews/, 16 of 16.
- **V9. Waits on Guy:** repo creation, the word "push", the tag v1.0.0 and publishing the draft (phase 4's G5-G7,
  now for v1.0.0). Then I5 of phase-i.md section 6 against v1.0.0, and the three private history bundles deleted.

## 4. Order and overlap

V0 runs now (the build is running). V1 (a read-only review) and V5 (no emulator) may run during V0's build. V2 and
V3 need the lazpy.2 core: V2 may run on the worktree's core, V3 waits for a quiet machine. V4 after V1's changes.
V6 and V7 after V0-V5 are on main. V8 after V7. Rule T: no two timed runs overlap.

## 5. Hours (estimates; actuals go to docs/hours.tsv)

V0 1.5 (plus 1 h machine time), V1 0.5 review + 1.0 changes, V2 1.0, V3 1.0, V4 1.0, V5 0.5, V6 0.3 (our side),
V7 0.5, V8 1.0. About 8 hours of work, plus the users' own runs and Guy's steps.

## 6. Risks

- The rebuild on main changes the core under Gen3D and 3DPlatinum mid-run: announce first, build when neither
  reports a timed run, and keep a copy of the lazpy.1 dylib in `runs/` for rollback.
- V1 may want a breaking rename: cheap now, impossible after 1.0. Take it now.
- V3 needs a quiet machine; another session's long gates may delay it. It does not block V1, V2, V4 or V5.
- V2's per-poll log may need a test app change; that changes the test app's own gates (laz-130): rerun them.
