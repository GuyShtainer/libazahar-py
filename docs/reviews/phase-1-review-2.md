# Phase 1 review 2 (laz-100): adversarial, fresh eyes, the last before building

Reviewer: opus, 2026-11-12, about 18:15 (load 44 at 18:16). Object: revision 1 of `docs/plans/phase-1.md`,
`phase-f1.md`, `phase-a.md`, `phase-b.md` (commit 21a152c). Checked against: PLAN.md sections 2-3; SRC =
`dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (every patch target line re-read); libctru and citro3d headers
in `/opt/devkitpro` and libctru source at `projects/_reference/libctru`; `prototype/fe2.c`; `tools/fetch.sh`,
`tools/map_check.py`; the stock dylib's strings; `docs/plans/phase-2.md` section 5 and `phase-c.md`/`phase-d.md` as
they stand in the working tree (Phase 2 revision 1 is in progress, uncommitted). Written before reading review 1;
the last section checks it. Nothing built, nothing run, nothing else edited.

Counts: **2 blockers, 9 should fix, 12 nice.**

## What holds (verified, so the builders can trust it)

- Every patch target: citra_libretro.cpp :59, :73, :287-306 (the `break;` after :304 lands inside the `if`, so it
  leaves the `while`), :371-373, :427, :503, :740; core.h :193/:280/:295/:313; memory.h :34-35, :558, :577, :599,
  :621, :673; filter.h :36/:38; types.h `Debug_Emulated`; environment.cpp :267-273, :294-297; core_settings.cpp :14,
  :23-25, :144, :713-715 (terminator), :722-823, :881, :1130; settings.h :490-507, :659 and the enums :28-36; the
  six setting keys exist in `CMakeModules/GenerateSettingKeys.cmake` (so `BaseKeys::<name>` compiles).
- Stacking with `--fuzz 0` is sound by construction: each patch is diffed against the cumulative tree, and the
  0000 notices (lines 4-5 of each file, after the two `#` lines in the `.def`) sit more than 3 context lines from
  every other hunk (nearest: citra_libretro.cpp :59, the `.def` tail at :27). `/usr/bin/patch` is
  `2.0-12u11-Apple` and its man page has `-F/--fuzz`, `-N/--forward`, `-t/--batch`. An offset is not fuzz, so a
  changed line count in an earlier patch still applies. The one break is the hand edit (S2).
- SET_VARIABLES is sent from `retro_set_environment` (environment.cpp:294-297 -> :243), V0 strings are locals
  (core_settings.cpp:774-775), default first (:785-806). The 32 keys in phase-a equal the stock dylib's 32
  `citra_*` strings (diffed). Every core SET_MESSAGE during `context_reset` is a failure (all call sites listed).
- Boot failures: missing file -> `GetLoader` null (loader.cpp:157-161); text file -> extension fallback (:175-176)
  and the base `LoadKernelMemoryMode` (loader.h:144-150). `create_device` with NULL features is handled
  (libretro_vk.cpp:113). Negotiation version 2 in the core's own header.
- libctru: one callback per event (gspgpu.c:282-289); gfx registers none; the GSP event thread is priority 0x1A
  (gspgpu.c:196), so B4 is plausible; `svcBreak` is not noreturn (svc.h:1291); the exit chain is real
  (apt.c:424-428 sets `__system_retAddr = aptExitProcess`, ctru_exit.c:32-33 calls it). SD writes are
  synchronous (file.cpp:200-217) and flush on `flags & 0xFF` (:197). fe2's frame numbering, `DONE` line, `OPT_`
  and `MVK_LIB` are as phase-b says. `RunLoop` returns 16 once and runs on (core.cpp:111, 149-150), so fe2 does not
  hang after `exit_at`.
- No download in a libretro configure: `download_qt`/`download_moltenvk` sit behind `ENABLE_QT` / `NOT
  ENABLE_LIBRETRO` (CMakeLists.txt:380-435); the clang-format download is WIN32 only.

## Blockers

**X1. "Interfaces for Phase 2" is not complete, and one row contradicts Phase 2.** Phase 2 section 5 (working
tree) marks five R2 rows that Phase 1 revision 2 must state; phase-1.md lists none of them, and phase-c/phase-d
already build on them:
- A4: `azh_boot` runs no `retro_run`; the NULL-first-frame check happens in the first batch frame (phase-c:553
  relies on it). phase-a states neither.
- A18: phase-1.md says "Raw shots are D's"; Phase 2 now makes `AZH_FMT_RAW` C2's (phase-2.md:21, :125, :210).
  phase-a.md:186 and :238-239 say "until D".
- B10: "the app never exits on START" (phase-c:49 presses START; phase-c:60). phase-b section 3 does not say it.
- B11: `tests/check_testapp.py` exposes `read_png_rgba(path) -> (width, height, rgba_bytes)`, RGB expanded to
  RGBA, CLI behind `if __name__ == "__main__"` (phase-c:131, :348, :444). phase-b does not ask for it.
- Not in either list: D's `test_abi.py` calls only `azh_abi_layout`, with no `azh_open` (phase-d:275). phase-a:222
  ("Call order is checked: open, then options, then boot...") lets a builder refuse it with `AZH_E_ORDER`.
**Fix:** phase-a section 3: "`azh_boot` runs no `retro_run`; the NULL-first-frame check is made on the first
`retro_run` of the first batch (`AZH_E_BOOT` from `azh_run`)"; "RAW: `AZH_E_UNSUPPORTED` until C"; "`azh_abi_layout`
and `azh_error` work in any state, before `azh_open` too". phase-b section 3: "The app never exits on a button
(START included); it leaves only on `aptMainLoop()` false, `exit_at` or the frame cap", and in section 4's
`check_testapp.py` row the `read_png_rgba` signature above. phase-1.md "Interfaces": replace the A1 bullet with
"RAW is C2's" and add A4, B10, B11 and the abi_layout rule.

**X2. `laz_record` is 40 bytes, so `_Static_assert(sizeof(laz_record) == 32)` fails on both compilers.**
phase-b.md:188-190: 4 x u32 (0-15), tx/ty (16-19), cx/cy (20-23), `uint64_t tick` at 24-31 (8-aligned on AAPCS and
arm64), `pad[2]` at 32-39. The builder either stops (the brief contradicts itself) or picks a layout for step G on
its own. **Fix:** drop `pad[2]` (32 bytes, `tick` at offset 24), and say "step G reads these offsets: magic 0, frame
4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24".

## Should fix

**S1. F1 launches a 40-90 min build before anyone reviews its patches, beside A's and B's emulator gates, in a
worktree that is later deleted.** phase-f1 step 7 detaches the build at minute ~40; the combined review comes after A
and B report (phase-1.md "Order"). A review finding in a hunk means a rebuild; the 4-job build plus a thin-LTO link
on every core runs while A and B time their 600-frame runs at load 60-90; and `git worktree remove` (merge step 7)
discards `build-core/build`, so any F2 fix is a full rebuild. The build is not on the critical path (F2 waits for D,
hours later). Also: the "40-90 min rebuild" premise (f1 :199, :243-244) is overstated for a kept build dir:
`tarfile` restores member mtimes, so a re-unpack leaves unpatched sources older than their objects and only the four
patched files recompile, plus the LTO link. **Fix:** F1's builder stops after `--configure-only` and the three reds
(drop the detach launch from its gate; keep `--detach` in the script). After the review passes F1 and A/B's gates
are done, the main loop commits F1 and runs `nice -n 10 tools/build-core.sh --detach` **in MAIN** (MAIN already has
the tarball), checks `kill -0` and the log's first lines, and starts the waiter there. Merge step 7 goes; F1's
worktree is removed with the others. Say in f1 section 4: "a patch change re-unpacks; with build-core/build kept,
only the patched files recompile".

**S2. The Movie check (step 6) comes after the notices patch, so a "no" means hand-editing a patch file.** Step 2
writes 0000 with 0006's clause; a skip means removing it by hand (fixing the `@@` counts) and re-running the step 2
checkpoint and step 3. **Fix:** do step 6 (15 min, reads SRC only) right after step 1; then 0000 is written once with
the right clauses, and 0006, if any, is made in the stack like the others. Saves a rerun and a fragile edit.

**S3. The waiter cannot tell a killed build from a slow one.** The `trap` writes `build.exit` only on a normal exit;
an OOM kill or SIGKILL in the LTO link (A3's own risk) leaves no file, and the waiter sleeps the full 3 h.
**Fix:** each 60 s poll also runs `kill -0 "$(cat build-core/build.pid)"`; dead with no `build.exit` -> exit at once
with "build died without an exit code". The script traps `EXIT INT TERM HUP`.

**S4. gate-a check 4 passes vacuously if the run has already ended.** A light app runs 600 frames in a few seconds
(spike 1: ~1,200 fps on a menu); if the heartbeat poll sees `>0` late, the pid is gone and `lsappinfo` prints nothing:
PASS with nothing checked. **Fix:** `kill -0 <pid>` must succeed before and after the `lsappinfo` call (else FAIL
"run ended before the check"), and check 4 uses its own `--frames 3000` run, not check 3's.

**S5. The readback has no sync rule.** The core calls `set_image(handle, &img, 0, nullptr, qf)` with no semaphores
(libretro_vk.cpp:707), and fe2 only works because it calls `vkDeviceWaitIdle` under the queue mutex before the copy
(fe2.c:117). phase-a's vk.c row says "the rest as fe2" about the interface only. A builder who drops the wait gets
stale or torn shots and flaky marker checks. **Fix:** vk.c row: "lock the queue mutex, `vkQueueWaitIdle` (or
`vkDeviceWaitIdle`), barrier from `image_layout` to TRANSFER_SRC and back, copy, submit, wait; the core gives no
semaphores".

**S6. The merge plan misses the map edits, so `map_check.py` fails at the first step commit.** map_check fails when a
top-level folder or file is not named in `docs/map/code.md` and when a script folder is not in `docs/map/tools.md`
(map_check.py:7-9). New: `core/`, `host/`, `testapp/`, `tests/`, the top-level `Makefile`, and scripts in `tests/`
and `tools/`. **Fix:** merge step 5 also edits code.md (one line each) and tools.md (`tests/`, `build-core.sh`,
`untar_checked.py`); each brief's report gives its one-line map entries.

**S7. The two cross-step runs happen only after both steps are on main, and nobody owns a failure.** B's
`RUNNER=azhost` branch is written blind, and `gate-a.sh build/testapp.3dsx` is first run in the post-merge clone
(merge step 6). **Fix:** run step 6 on a throwaway branch `git merge step-a step-b` (no shared files; a clone of that
branch), before anything lands on main; a failure goes back to the owning builder by SendMessage; main gets the
commits only when both gates pass.

**S8. The clone test copies all of `dl/` twice.** Merge step 6 copies MAIN's `dl/` (470 MB of it is `azahar-src`,
21k files) into the clone, and gate-a check 1 copies it again into `$COPY`. **Fix:** copy only `dl/azahar`,
`dl/moltenvk`, `dl/libretro-headers`, `dl/vulkan-headers` (as phase-a step 0 does) and `vendor/`.

**S9. "The first two frames" for the 2D markers collides with `boot_frames`.** phase-b:170 says clear and draw the
markers "the first two frames"; with `boot_frames=90`, frames 1-90 are boot frames that "draw nothing new"
(:147). A builder keying on `f == 1, 2` draws nothing, and gate 5's boot shots fail. **Fix:** "the first two
main-loop frames after the busy boot (f = boot_frames + 1 and + 2)".

## Nice

- N1. The `.def` has no licence lines (`#LIBRARY "libretro"`, `#EXPORTS`): say "the `#` notice goes after line 2".
- N2. build-core.sh: `export MACOSX_DEPLOYMENT_TARGET=11.0` (CI :183) explicitly; `cd "$ROOT"` first (the
  relative `build-core/` paths and the nohup log depend on it).
- N3. f1 gate text says "the script prints full paths" but the sample shows relative ones; pick one.
- N4. Fact fix (f1 :74-75, azahar-source-check): CMakeLists.txt:431 is the MoltenVK download, not "Vulkan externals
  skipped". glslang, spirv-tools, spirv-headers and sirit are built from `externals/` (externals/CMakeLists.txt:
  428-463; video_core/CMakeLists.txt:205); `glslangValidator` is unneeded only because
  `ENABLE_GLSLANG_BINARIES OFF` (:458). They count in the build time.
- N5. 0006 in `do_load_game` also runs from `retro_reset` (citra_libretro.cpp:496); note it, F2 decides.
- N6. phase-a Makefile: `-isystem vendor -isystem vendor/include`, as B does for libctru, so a third-party header
  can never fail `-Werror` or the zero-warning grep.
- N7. `.gitignore` has no `*.png`; add to merge step 3 a check that `git diff --cached --name-only` holds no
  `.png`, `.3dsx`, `.elf`, `.log`, `.dylib` (Gen3D shots live only in `runs/`, which is ignored, so this is a net).
- N8. The test app's SMDH takes libctru's `default_icon.png` when no icon is given (simple_tri Makefile :28-32,
  :140-150); fine (zlib licence), but Phase I's audit should know the shipped `.3dsx` carries it.
- N9. Shell rule 3: no `timeout` on macOS. gate-b's "seconds plus 120" wait is a background pid plus a bounded
  `kill -0` loop; say so in the brief.
- N10. gate-b: on `FAIL slow`, let the script itself rerun that check once at `SECS=40`, so the main loop's clone
  rerun needs no judgement.
- N11. phase-b :97-99: the stock core does forward `OutputDebugString` (its filter is Debug, citra_libretro.cpp:59,
  and the backend maps Debug to `RETRO_LOG_DEBUG`, backend.cpp:79-81); only the host's info threshold hides it.
  So "debug-text stop on our core only" is a speed choice, not a necessity. Worth one line for Phase 2.
- N12. Phase-1 "Before the launch" step 2 is already done: `dl/libretro-headers/`, `dl/vulkan-headers/` and
  `vendor/include/.vulkan-headers-1.4.368` exist in MAIN.

## The one combined opus as-built review

Not unsafe for A and B: no shared files, the review is read-only, and one lane is cheaper. It is unsafe as the
plan stands for two reasons, both fixed above: F1's build would already be running on unreviewed hunks (S1), and
the review cannot run the cross-step gates, which first run after the merge with no fix path (S7). With S1 and S7
taken, keep it, plus: the reviewer works through the three section-10 checklists in order and writes findings to
disk as it goes (agent-limit hygiene); fixes go back to the owning builder by SendMessage, and the reviewer re-checks
only the changed items.

## Hour-saving pass

Taken by revision 1 and sound: no dry-run stage, fe2 as B's runner, one review lane, crop/serialize/busy boot now.
More: S1 (no kept worktree, no copy step, incremental rebuilds in MAIN later), S2 (no hand edit, one fewer
checkpoint rerun), S8 (about 1 GB less copying per clone run). Possible: gate-a's `$COPY` could symlink `dl/` and
`vendor/` instead of copying (fetch.sh only reads when all is present).

## Review 1's findings: really fixed in the plan text?

Read after the sections above were written.
- **X1 patch stacking: fixed.** phase-f1 section 3 (stack, one `0000` notices patch, `--fuzz 0`), section 4 (no
  dry-run stage, `REJECTED` removes `build-src/`), step 2 (`stack.prev/` diffs, whole-stack checkpoint on a fresh
  unpack), red 2, checklist 1. Left over: the hand edit of 0000 when 0006 is skipped (S2 above).
- **X2 svcBreak runs on: fixed.** phase-b section 2 ("The guest runs on", svc.cpp:1148-1166, core.cpp:111), the
  `break_at` row, gate 5 (`break f=120` then `f=121`), checklist 3. Matches PLAN C(e) and Phase 2's B5.
- **X3 citro3d's VBlank0 slot: fixed.** phase-b section 2 (one callback per event), section 3 (our callback only
  before `C3D_Init`, the busy boot runs before citro3d in both modes, 3D loop `C3D_FrameBegin(SYNCDRAW)` ...
  `C3D_FrameEnd(0)`, no `gspSetEventCallback` after `C3D_Init`, `v = C3D_FrameCounter(0)`), gate checks `v` in 2D
  only, checklist 4. `C3D_FRAME_SYNCDRAW` and `C3D_FrameCounter` are at `c3d/renderqueue.h:23, 29`.
- **Should-fix S1-S13: all fixed in the text.** S1 (text file is the context_reset case, phase-a :115-121), S2
  (readback from the first HW frame), S3 (strings copied, store live before `retro_set_environment`), S4 (32), S5
  (`azh_version_ok` in a pure `version.c` plus `make test-version`, better than review 1's `core.c`), S6 (`mktemp`
  copy, trap, `KEEP=1`), S7 (`2126.2` pinned), S8 (casts), S9 (A's run line in phase-b), S10 (a present bad
  tarball refused and kept), S11 (no item files), S12 (a, b, c), S13 (branches `step-*`, MAIN path in each brief).
  Two follow-ons this review adds: S12(b)'s waiter needs a liveness check (S3 above), and its F1-worktree home
  moves to MAIN (S1 above).
- **Nice N1-N12:** taken or recorded as listed; N11 (merge as each review passes) declined with a reason that holds.
  N6 (draw the markers once per buffer) introduced the `boot_frames` ambiguity (S9 above).
- **Hour-saving row "defer `AZH_FMT_RAW` to D"** is now overtaken by Phase 2, which gives RAW to C2 (X1 above).

## Verdict

**Ready to build after revision 2**, provided it takes X1 and X2 (text-only, about ten lines in phase-a, phase-b
and phase-1) and S1, S3, S4, S5 and S7 (the build launch, the waiter, the no-window check, the readback wait, the
pre-main integration run). The rest are cheap and can go in the same pass. No third review loop is needed: none of
these findings changes the design, and every fact the builders depend on was re-read in the source.
