# Phase 6 (v1.0.0) plan, review 1

Reviewer: opus agent ad7b8a7b2342fa4b1, 2026-11-13 10:59-11:07, read-only, on `docs/plans/phase-v1.md` revision 0.
Saved verbatim by the main loop.

**Verdict.** The plan is the right shape: one release, the lazpy.2 core, gates on the release candidate, and the legal re-audit before the push. It is not ready to execute. There are four blockers. (a) Section 1 promises host/Python cross-version compatibility, but the code refuses it: Python checks for an exact ABI match. (b) `core/PIN-nokeys` points at a v0.1.0 release that will never exist, and correcting it changes the pin sha that `build.inputs` records. So the fix has to land before V0's main rebuild, not in V4. Main also has no seeded nokeys tarball, so that rebuild would 404 as things stand. (c) V2 assumes a `.ctm` writer and a host call that do not exist, and a test app that reads input per poll, which it does not. (d) The V0 merge itself, not just the rebuild, breaks Gen3D and 3DPlatinum mid-run. V2 should move to "not in 1.0" now. That saves the most hours, and no public API is lost: nothing in the host or Python calls the export.

## Verified (holds)
- Check 14 (`tools/release_check.py:618-626, :856`) takes the version from the release folder name. It needs no code change for v1.0.0. The plant (`:781`, `0.1.0.dev0`) still turns it red against 1.0.0.
- Check 11 (`release_check.py:465`) already fails if `fetch.sh` REL_TAG is not the staged tag. Check 9 (`:419-421`) fails if PIN-nokeys' SHA or size differs from the staged source asset. These catch two of the V4 misses below, but only at V8.
- mkrelease's source-asset note (`tools/mkrelease.sh:65`) does not contain the tag. Re-staging under v1.0.0 should therefore reproduce the nokeys tarball byte for byte (f7a7…), as phase-i gate 2 showed for repeat runs.
- build-core.sh replaces the dylib atomically (`mv -f`, worktree `tools/build-core.sh:188`). A process that loads the core during the build gets one whole file, either the old or the new one.
- V3 is feasible without writing in Gen3D's tree. `docs/research/real-scene-j.md:3-8` did it already: Gen3D's build pinned by sha, the game and world cache from a seed folder outside both repos, the script outside both repos. README rows 24-29 already carry audit-clean wording ("Gen3D (homebrew) drawing a 3D scene from a GBA game run locally, not distributed").
- The machine (18 GB, 12 cores) fits 4 instances at J's peak of 0.9-1.4 GB each. `LAZ_MAX_INSTANCES` (`python/libazahar/_slots.py:56-60`) lifts the cap for the run.
- No tag and no remote exist yet. `runs/release/v0.1.0` is intact.

## Blockers
- **B1. The host/Python promise is false as written (`phase-v1.md:13-15`).** `_abi.py:231-232` refuses any host whose ABI differs from Python's (`host abi X, Python abi Y`). `_abi.py:200` refuses unknown const rows, and `_host.py:37-40` refuses a host that lacks a prototype. Step K's purely additive 3→4 bump already breaks a v0.1.0 Python against the new host, and the reverse. Fix: promise "host and Python from one checkout are one unit; mixing versions raises HostError". Alternatively, make `check_layout` accept `host abi >= Python abi` and ignore unknown rows, and add a test. Say in section 1 which one, and list `AZH_ABI_VERSION` as "may bump in minor releases".
- **B2. `core/PIN-nokeys:7-8` (and the worktree's) has `SRC_URL=…/releases/download/v0.1.0/…`.** Phase-k.md:144-145 accepted that only because v0.1.0 was to be published first. D1 reverses that, so main and the v1.0.0 build-files asset would point at an asset that never exists. Changing the line changes `sha256(PIN-nokeys)`, which `build.inputs` records as `pin=` and `gate_f2._inputs_findings` (worktree `tests/gate_f2.py:117-122`) compares. Fix: in V0, after the merge and **before** the main build, change v0.1.0→v1.0.0 in PIN-nokeys (header comment too) and commit. Add the rule: no edit to `core/` or `tools/build-core.sh` after the main build, or the build is invalid.
- **B3. Main cannot fetch its nokeys tarball.** Main's `dl/azahar-src/` has only `src.tar.xz`, `unpacked` and `build-src`. With PIN-nokeys as the default (`build-core.sh:33`), the V0 build would curl the v0.1.0 URL (404, `:61`) and die. Fix: in V0, `cp` (not `ln`) `runs/release/v0.1.0/azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` to `dl/azahar-src/src-nokeys.tar.xz` and check its sha (f7a7…). A copy survives D1's later cleanup and a re-run of mkrelease, which does `rm -rf "$OUT"`.
- **B4. V2 cannot run as written (`phase-v1.md:42-47`).**
  - No host or Python code calls `lazpy_movie_play`. A search of host/ and python/ finds it only in the export lists (`tests/gate_f2.py:238`, `release_check.py:44`).
  - There is no `.ctm` writer anywhere.
  - Patch 0006 needs the call after `retro_load_game` and before the host's `context_reset` (else -5). That means a new `azh_open` path, which is an ABI addition.
  - Azahar's movie is a strict interleave of 7-byte entries in core-timing order: PadAndCircle and Touch at 234 Hz (`hid.h:342`), IrRst at the app's irrst period, accelerometer and gyro when enabled. A type mismatch only logs "out of sync" and plays on (`movie.cpp:237-246`). A writer would have to replay CoreTiming exactly.
  - The test app reads HID once per frame (`testapp/source/main.c:145-146`), not once per poll.
  - Fix: take the plan's own exit now. Poll-exact goes to "not in 1.0". USING.md 46/116/233 and STATUS:30 say "our core exports it; the host and Python do not call it". The 1.0 hour is better spent on B1-B3. If it is wanted in 1.x, V1 should reserve an additive open path (an `azh_open` options field or a new function) so that adding it later is not a 2.0 change.
- **B5. The merge breaks users before the rebuild does (`phase-v1.md:35-36`, `:86-87`).** Gen3D and 3DPlatinum load MAIN's Python and MAIN's `build/libazhost.dylib` (`_paths.py:23-25`), and each worker imports Python fresh. Once core-rev2 merges, `_abi.py` says ABI 4 while `build/libazhost.dylib` is still ABI 3. Every new worker then fails until `make` runs. A core swap in the middle of a suite also mixes lazpy.1 and lazpy.2 instances, which breaks exact-repeat and state comparisons, not just timing. Fix: announce; wait until neither project has *any* run going (not just "no timed run"); then merge, `make`, and run the fast pytest as one block. Copy lazpy.1's dylib to `runs/core-lazpy1/` before the build: K's gate 2 needs it as `LAZ_CORE_OLD`. Tell 3DPlatinum to move its `LAZ_ROOT` from the worktree back to MAIN before the worktree is removed, and remove it only after V0's main gates pass (`--ignored` porcelain check: its `build-core/` is ignored).

## Should
- **S1. The state promise needs a scope (`phase-v1.md:14-15`).** "Same core source" is undefined. Azahar's savestate carries the build revision (`savestate.cpp:65-77`), and any patch that touches serialized state breaks loading. Fix: "a state loads in every later 1.x host on the same core revision; across core revisions it is tested at each release (old core's state into new core, K gate 2's `LAZ_CORE_OLD` test) and listed in the release notes". Make that test a standing V7 item.
- **S2. "What works" items that no V-step reruns on lazpy.2 (`STATUS.md:8-25` vs section 1's rule at `phase-v1.md:16`):**
  - laz-310's speed table and README's "Measured numbers" (`README.md:14-29`) are lazpy.1 runs.
  - laz-430's "as fast as on Azahar's own core" (STATUS:23-24) needs an interleaved stock row.
  - Fix: V3 adds one interleaved 1-instance stock row. Either rerun `tools/speed_table.py` on lazpy.2 (a timed run) or label the light-scene rows "core lazpy.1, 2026-11-13". V4 adds K's `threads()` and `init_ticks_override` to "What works" (laz-510).
- **S3. V4's version list is incomplete (`phase-v1.md:53-56`).** A grep of tracked files gives:
  - `core/PIN-nokeys:7` (moved to V0, B2).
  - `tools/fetch.sh:42` `LAZPY_CORE_ZIP` …lazpy.1… → lazpy.2.
  - `fetch.sh:43-44` pins.
  - `STATUS.md:3` (also "commit 6d5ca11"), `:46`, `:62`.
  - `README.md:10`.
  - `docs/map/runners.md:75,81,82` (v0.1.0 commands).
  - `docs/release-notes/v1.0.0.md`, which does not exist. `release_check.py:310` reads it for checks 7, 15 and 16, and it must say "macOS 15 or later" and hold no speed tokens or "keys" outside the allowed phrases (`:646-655`).
  - USING.md has no version line, so drop that item.
- **S4. V8 omits phase-i I2's steps 2-3 (`phase-i.md:550-557`).** Rebuild the test app from source under `env -i` (no `/Users/` strings). `mkrelease.sh v1.0.0`, write the zip and test-app sha into `fetch.sh`, commit, then `mkrelease` again: check 10 compares a HEAD archive that embeds the commit id (`mkrelease.sh:8-9`). Also the audit's S4 (`release-legal-audit-v0.1.0-reaudit.md:97`): tag the exact HEAD the build-files asset came from. Copy those steps into V8 as written.
- **S5. V9 reuses phase-i 8.2 (`phase-i.md:672-673`),** which has `--prerelease` and "(prerelease)" in the title. Fix: put a v1.0.0 command block in this plan without `--prerelease`, notes from `docs/release-notes/v1.0.0.md`.
- **S6. V3's gate is not concrete (`phase-v1.md:48-52`).** "Full speed with a margin" is undefined for an uncapped headless run. The quiet-load gate (load under 6 at start and end, real-scene-j.md:16) cannot hold with 4 of our own instances running. Fix:
  - Use `tools/speed_table.py`'s `cap_rule` (`:42-62`; ×1.25 total gain, end load under 2×CPU) as the criterion.
  - Quiet means load under 6 before the run and no other session's emulator in `ps` from start to end.
  - Name the guest-time check (rule 7), e.g. guest frames from `Stats` against wall time plus one shot showing the 3D world.
  - Pin Gen3D's .3dsx by sha, as J did.
- **S7. The order has V4 too early (`phase-v1.md:76`).** STATUS and README need V2's and V3's results. Fix: V4 runs after V1, V2 and V3. V1's review must finish before the main core build if it might touch `core/patches` (export names), because any patch edit forces another 30-60 min build (B2).
- **S8. D5 (`phase-v1.md:27`).** No lazpy.1 core was ever published, so "courtesy" support binds nobody. State it as "not part of the 1.0 promise; may be removed in any 1.x release". Also say in section 1 whether the env vars (`USING.md:200-202`), `azhost` exit codes and the option-profile file format are covered by semver.
- **S9. V6 has no time limit (`phase-v1.md:60-62`).** Give it a deadline and say what happens if a project stays silent: e.g. 3DPlatinum's K gate-5 answer counts if the core sha is unchanged, but a main rebuild gives a new sha.

## Nits
- `tools/mkrelease.sh:17` and `tools/release_check.py:4` usage examples say v0.1.0. Use `<tag>`.
- `docs/release-notes/v0.1.0.md` stays tracked for a release that never happened. Delete it, or add "never published" in its first line.
- `phase-v1.md:56`: "16 checks" and "check 14" are fine, but V8's "16 of 16" needs `--pre-push` (check 15 runs only then, `release_check.py:857-858`). Say so in V4's gate too.
- V5: the workflow needs `tools/fetch.sh --headers` before `make` (the `vendor/` includes, `Makefile:4`), and it must not fetch the core. State it.
- 1.x policy: check 11 and `expected_assets` (`release_check.py:83-86`) require the full core and source asset set on every tag. Decide whether 1.0.1 re-uploads the core or `REL_TAG` may stay at v1.0.0. Record the decision in section 1.

## Hour-saving
- Drop V2 (B4): saves the planned 1.0 h. A real attempt would be 4 h or more: a writer, a host ABI addition, a test app change and re-gating laz-130.
- No code change to release_check check 14 (Verified). V4 is doc and pin edits only.
- Drop CHANGES.md. `docs/release-notes/v1.0.0.md` is required anyway (S3) and serves as the change list. One file less for map_check and the audit.
- V7 and V8 overlap. `clone_check` already runs the full pytest with `LAZ_REQUIRE_EMULATOR=1` (`tools/clone_check.sh:68`). Keep V7 for the stock-core run (`LAZ_STOCK_CORE`), `gate_f2.py --stock` and memory_watch, and let clone_check's log stand for the plain full pytest.
- V0: the main rebuild cannot be avoided once B2's pin edit lands (the worktree's `build.inputs` pin sha goes stale). Start it right after the merge commit and run V5 and V1's read-only review alongside it.
- V3: reuse `cap_rule` and the Pool path that `speed_table.py` already uses. Only the scene script (in the scratchpad) is new.
