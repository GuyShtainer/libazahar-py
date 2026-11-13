# Phase 6 (v1.0.0) plan, review 2

Reviewer: opus agent ad9c5acb09a5871bc, 2026-11-13 11:09-11:17, read-only, on `docs/plans/phase-v1.md` revision 1 (main and the `core-rev2` worktree).
Saved verbatim by the main loop.

**Verdict.** Revision 1 fixes most of review 1. V0b's order is right: copy the lazpy.1 core, seed the tarball, merge, edit the pin on main, build, gate. release_check and gate_f2 will accept main's `build.inputs` after the pin edit. mkrelease and release_check need no code change for v1.0.0. The plan is still not ready to run, for three reasons. First, V3 as written cannot produce a cap. `cap_rule` takes its `check_ok` input from the test app's own log, so on Gen3D every row fails the check. On that path `cap_rule` returns 3, which would raise today's default of 2 on a failed run. Second, section 1 freezes things that are not specified anywhere: the option-profile format has no written definition and two parsers that behave differently, and the exit codes appear only in a header. Third, two steps break the "tag on the exact HEAD" rule and the "no build-core edit" rule in ways the plan does not guard: the audit report commit moves HEAD after staging, and any later `build-core.sh` run invalidates the gated build. All three have cheap fixes, listed below.

## Review-1 fixes
- **B1: partly.** `phase-v1.md:18-20` says mixing a host and a Python from different releases "raises HostError". That only happens when the ABI or layout differs (`_abi.py:231-232`, the rows after it). Two releases with the same ABI mix silently. Fix: "mixing is unsupported; the layout check catches an ABI or layout difference". Also say the C promise is source-level only: names and meaning, while struct layouts may grow with an ABI bump, so C callers rebuild for each release.
- **B2: fixed** (step 5 comes before step 6, plus the no-edit rule). Nit: the branch's `core/PIN-nokeys` header comment has no "v0.1.0". Only `SRC_URL` (`:8`) has it.
- **B3: fixed.** `build-core.sh:65-70` checks the size and sha again anyway.
- **B4: fixed** (D5). Nit: the USING line numbers in V4 (46, 116, 147, 233) are main's. After the merge they move by 6 to 12 lines (the CTM row is at worktree `:153`, the table row at `:245`). Anchor them on text, not numbers.
- **B5: fixed in substance.** Step 1 should say the hold lasts from step 1 to step 8, not just "no run going" at step 1. Also see Blocker 3: V1's edits hit 3DPlatinum in the worktree.
- **S1: partly.** The state test across core revisions is a standing V7 item. "Every later 1.x host on the same core revision" has no standing test. Fix: keep one test-app state made by v1.0.0 (outside git, under `runs/release-fixtures/`) and add "a v1.0.0 state loads" to V7 for every 1.x release.
- **S2, S3, S5, S7: fixed.**
- **S4: partly.** See Should 1 (the audit report commit after staging).
- **S6: not fixed.** See Blocker 1.
- **S8: partly.** See Blocker 2.
- **S9:** answered by decision (no deadline, staging blocked on both answers). That is acceptable if Guy agrees.
- **Nits: fixed.**

## Blockers
1. **V3 cannot use `cap_rule` as it stands (`phase-v1.md:67-76`).**
   - `speed_table.measure` sets `check_ok` from `last_frame_line`, which reads `testapp/log.txt` (`tools/speed_table.py:76-79, 128-135`). It writes the test app's control file (`:107-110`) and uses threads plus a `Barrier` (`:139-169`), not `Pool`.
   - On Gen3D, `tick_ok` is False, so `check_ok` is False and `cap_rule` returns **3** ("cap stays 3", `:50-51`). The default is 2 (`_slots.py:25`).
   - "Guest frames from `Stats` against wall time" is circular. `Stats` has no guest clock (`results.py:64-74`), and frames over wall is just host fps.
   - Fix: the scratchpad scene script builds the `cap_rule` rows itself (`n`, `total_host_fps`, `load_end`, `check_ok`). It warms up past J's 3D-world frame (about 3000, `real-scene-j.md:6-7`) and measures in a window shared through a barrier inside the Pool job.
   - Its `check_ok` comes from a real guest signal: Gen3D's `voxel.log` flip lines per wall second (USING section 12 row 8), or a guest frame counter read through `emu.memory`. It must agree with host fps within a stated tolerance, with a shot at the start and at the end of each window showing the 3D world.
   - State that a CHECK FAIL keeps the cap at 2 (not `cap_rule`'s 3), and that a cap change edits `_slots.py:25` and `test_slots.py` before V6 and V7.
2. **Section 1 freezes formats that are not written down (`phase-v1.md:14-17`).**
   - The environment variables are USING **section 15** (`:199`), not section 16. Section 16 is "The two cores".
   - The option-profile format is described only in `host/options-default.txt:2` ("key=value, one per line"), and the two parsers differ:
     - Python (`emulator.py:27-36`) strips whitespace, treats an indented `#` line as a comment, and raises HostError on a line with no `=`.
     - `azhost` (`azhost_main.c:269-296`) does not strip, treats `#` as a comment only in column 0, and reads at most 4096 lines.
   - The exit codes exist only in the `azhost.h:16-19` enum. USING mentions only code 11.
   - Fix: V1 picks one strict format (`key=value`, `#` in column 0, blank lines, later wins, what an unknown key does) and makes both parsers follow it, with one test each. USING section 14 documents it, and USING gains an exit-code table. Otherwise drop those items from the promise. Also say whether `azhost run`'s summary line (`frames= wall= ...`) and the `--inputs` file are covered.
3. **V1's changes land in the worktree that 3DPlatinum is using (`phase-v1.md:49-53`, `:65`).** That is B5 again, moved one checkout over. Fix: hold 3DPlatinum while V1's edits and `make` happen. Or apply V1 on main inside the V0b block, between steps 4 and 5, and run the fast pytest there.

## Should
1. **V8 order.** Committing the audit report (`phase-i.md` I3: "Commit the report"), or any status, hours or handoff commit, moves HEAD after `mkrelease`. The build-files asset then no longer matches HEAD (check 10, `mkrelease.sh:134`). An uncommitted report also fails check 15's clean-tree test (`release_check.py` `pre_push_findings`). Fix: commit the report, then `mkrelease v1.0.0` once more (the zip and test-app sha256s must not change). Then run `release_check --pre-push` and get 16 of 16, and tag that HEAD with no commit in between.
2. **Widen V0b step 5's rule.** Not only "no edit": no `build-core.sh` run of any kind on main after step 6.
   - A `--configure-only` run, or a `LAZ_CORE_PIN=core/PIN` run, deletes and re-unpacks `build-src` (the stamp is keyed on the tarball, `:81-83`).
   - It also rewrites `CMakeCache.txt`, so gate_f2's "core newer than the cache" check fails (`gate_f2.py:186-188`), and with it release_check's check 2.
   - The same goes for `LAZ_CORE_PIN=core/PIN`: that route is not gated on lazpy.2, so STATUS's laz-110 line should name the PIN-nokeys route.
3. **Check that the source tarball still reproduces, before the build.** Run mkrelease's `tar` line (`mkrelease.sh:59-73`) from `src.tar.xz` into the scratchpad and compare the result to f7a70044…. If today's bsdtar no longer reproduces it, the pin has to change, and that is cheap before step 6 and a second build after it.
4. **Build from a fresh build folder on main.** Move `build-core/build` aside before step 6. Its cache dates from the lazpy.1 configure under deployment target 11.0, so a release built on it is not the build a user reproduces. The cost is about the same, because the re-unpacked tree recompiles almost everything anyway.
5. **V5 needs a clean runner, not "locally".** The local checkout has `dl/`, `vendor/` and `build-core/`.
   - What `fetch.sh --headers` downloads: two `raw.githubusercontent.com` headers and the Vulkan-Headers tarball (`fetch.sh:114-148`). That is enough for `make` and `make test-host` (`Makefile:41-50`), which need no core.
   - The workflow also needs `actions/setup-python`, pinned by SHA. Run it on 3.10, the claimed floor; only 3.14 exists on this Mac.
   - pytest is not a declared dependency, so the workflow needs `pip install -e . pytest numpy`.
   - Add `permissions: contents: read`.
   - Gate: run the steps in a fresh `git clone` under `env -i`, as `clone_check.sh` does, so the first public run is not red.
6. **Claims 1.0 makes without a test.**
   - "Python 3.10 or newer" (README:39, USING:12): never run. Run the fast suite on 3.10 in V7, or state the version actually tested.
   - "macOS 15 or later": tested only on 15.8.
   - In V3, also record any CPU-heavy non-emulator process (builds count too).

## Nits
- V4 sets `LAZPY_CORE_ZIP` to lazpy.2 while the sha pins still belong to lazpy.1, until V8. Set them to `TBD` meanwhile; `pin_set` already refuses that (`fetch.sh:95-97`).
- "v0.1.0 core" in `host/pins.h:6` and `tests/python/test_threads_live.py:128` names a release that never happened. Say "the lazpy.1 core".
- V9: give `gh release create` an explicit asset list and add `--verify-tag`.
- V8's `env -i` rebuild of the test app: compare its sha256 with 53b699e8…. A difference means V7 tested other bytes; clone_check covers that, but note it.
- The host's minos of 15.0 (check 16 requires exactly that) comes from the toolchain's default, not from the Makefile. Pin `-mmacosx-version-min=15.0` in a later release.

## Hour-saving
- **The core build takes about 10 minutes, not 30-60.** The worktree's full LTO build (1055 compile steps) ran 10:53 to 11:03. V0b's hold on the two other projects is therefore about 30 minutes, not 1.5 hours.
- **Drop V0a's gate 2** (the worktree's full pytest, waiting on Gen3D's lane). That core is thrown away. V0b step 7 and V7 both rerun the suite on the final core, and V6 counts only the final sha.
- **Run the full pytest once.** Make V0b step 7 gate 1 plus the fast pytest plus `test_threads_live.py` with `LAZ_CORE_OLD` (about 1 min), enough to release the users. Then V7 is the only full suite before clone_check. That saves one quiet window and about 0.3 h.
- **Move 3DPlatinum's A4** to V6 on the final core. Its repro needs the windowed route, which the headless-only rule may forbid; accept a headless count instead.
- **V3:** reuse `cap_rule` and `md_core_table` from `tools/speed_table.py` by import. Only the row builder and the Gen3D guest check are new, about 40 lines in the scratchpad.
