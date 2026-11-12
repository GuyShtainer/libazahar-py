# Phase 1 plan, review 1 of 2 (laz-100)

Opus adversarial review, 2026-11-12, of `docs/plans/phase-1.md`, `phase-f1.md`, `phase-a.md`, `phase-b.md` against
`docs/PLAN.md` (final). "SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/`, read directly for every claim
below. libctru source read at `3ds-toolkit/projects/_reference/libctru` (git 9b55eda; installed is 2.7.0-1, the exit
path is the same); citro3d checked by `nm` on `/opt/devkitpro/libctru/lib/libcitro3d.a`. Nothing built or run.

**Counts: 3 blockers, 13 should-fix, 12 nice.** Verdict at the end.

## Blockers

**X1 (F1) The patches do not stack, and the dry run cannot see it.** Step 2 makes each patch by `diff -u` of a file
copied from pristine SRC, and the checkpoint is "each `patch -p1 --dry-run` clean against a scratch copy" (one at a
time). But `citra_libretro.cpp` gets 0001, 0003, 0004 and 0006, `libretro.osx.def` gets 0001 and 0006, and every
patch adds its own "Modified by" line at the same spot under the license header. After 0001 lands, 0003's top hunk
no longer matches. macOS `patch` is BSD (`patch 2.0-12u11-Apple`) with a default max fuzz of 2, so it may apply with
fuzz silently or reject. The script's "dry-run every patch first, then apply all" checks each patch against the
*unpatched* tree, which proves nothing about the stack. The builder has to make a decision the brief does not make.
Fix (phase-f1.md section 3 intro, step 2, the `build-core.sh` paragraph, red 2):
- "Patches form a stack: make patch N against SRC with patches 1..N-1 already applied (a scratch tree you patch as
  you go). Each patched file gets one notice line, added by the first patch that touches it and listing every lazpy
  change (or one `0000-lazpy-notices.patch` for all four files; pick the 0000 form)."
- Script: "The tree under `build-src/` is a fresh, throwaway unpack, so there is no dry-run stage. Apply each patch in
  order with `patch -p1 --forward --batch --fuzz 0`. A failure prints `patch <name> REJECTED`, runs `rm -rf` on the
  tree, and exits 1." Red 2 becomes "... → `patch <name> REJECTED`, the tree is removed".
- Step 2 checkpoint: "the whole stack 0001-0005 applies in order with `--fuzz 0` to a fresh scratch unpack."

**X2 (B) svcBreak does not stop the guest; gate 5's `break_at` expects the opposite.** `SVC::Break` (SRC
`src/core/hle/kernel/svc.cpp:1148-1166`) logs and calls `Core::LogException`, which only sets status 14
(`exception_handler.cpp:142`) and returns. `RunLoop` resets the status at `core.cpp:111`, and libctru's `svcBreak`
is not `noreturn` (`svc.h:1291`), so the app's loop keeps going. PLAN 2.2 and gate C(e) say "the guest runs on".
phase-b.md section 2 ("The guest stops") and gate 5 ("no per-frame line after it") are wrong, so a correct app fails
its gate, and a builder who "fixes" it with a spin after `svcBreak` breaks C(e). Fix (section 2 bullet and gate 5):
"after `svcBreak` returns the app goes on as normal: the log has `break f=120 ...` and then per-frame lines from
`f=121` (PLAN C(e)); `check_testapp.py event <log> break 120` checks the line and that `f=121` follows it."

**X3 (B) citro3d owns the VBlank0 callback slot.** `gspSetEventCallback` keeps one callback per event
(libctru `gspgpu.c:282-289`: `gspEventCb[id] = cb`). `libcitro3d.a` imports `gspSetEventCallback` and defines
`onVBlank0`/`onVBlank1` (renderqueue: `C3Di_RenderQueueEnableVBlank`). It counts vblanks for `C3D_FrameSync` and
`C3D_FrameCounter`. If B registers its counter after `C3D_Init`, citro3d's frame pacing stops counting and
`C3D_FrameBegin(C3D_FRAME_SYNCDRAW)` can wait forever (3D mode draws nothing; gate 4 cannot pass). If B registers
first, citro3d overwrites it and `v` freezes. Fix (section 3, the `v` definition, main-loop order, files table):
"`v` comes from our own `GSPGPU_EVENT_VBlank0` callback in 2D mode only. In 3D mode `v = C3D_FrameCounter(0)` (citro3d's
own VBlank0 counter, `c3d/renderqueue.h:29`) and the app never calls `gspSetEventCallback`. 3D loop order:
`C3D_FrameBegin(C3D_FRAME_SYNCDRAW)`, draw, `C3D_FrameEnd(0)`, with no extra `gspWaitForVBlank0()`. The `v`
column is checked in 2D runs only." The review checklist item 5 becomes "function pointers: the 2D vblank callback".

## Should fix

**S1 (A) A text file named `bad.3dsx` passes `retro_load_game`.** `GetLoader` falls back to the extension when it
cannot identify the file (SRC `src/core/loader/loader.cpp:175-176`). The 3DSX loader does not override
`LoadKernelMemoryMode`, so it gets the base version that returns Success (`loader.h:144-150`), and the early check at
`citra_libretro.cpp:528-553` passes. The failure comes later, inside `context_reset`: `System::Load` → `Load3DSXFile`
fails → `ErrorLoader` (`core.cpp:492-511`, after a clean `System::Shutdown`) → SET_MESSAGE "Failed to load ROM!"
(`citra_libretro.cpp:381-382`). Fix the facts line ("bad format → 'The ROM format is not supported.'" applies only to
loaders that read a header early, e.g. NCCH). Gate check 5's text file then covers the context_reset path by itself.
Step 4: "the text file *is* the SET_MESSAGE-during-context_reset case; plant nothing else."

**S2 (A) The readback buffer "from the av info's max geometry" is 138 MB.** `retro_get_system_av_info` reports max
7200 x 4800 (`environment.cpp:315-316`, sized for side-by-side at 10x). Fix (vk.c row, review item 3): "size it from
the first HW frame's `w x h` (400f x 480f); if a later frame is larger, free the buffer and make a bigger one; log both
sizes."

**S3 (A) SET_VARIABLES strings die when the call returns, and the call comes before `retro_init`.**
`RegisterCoreOptions` builds `variables` and `values_buffer` as local vectors (`core_settings.cpp:774-775`). It runs
from `retro_set_environment` → `OnConfigureEnvironment` (`environment.cpp:243, 294-297`). Fix (env.c / options.c
rows): "copy every key and value string (`strdup` into the option store, or fixed arrays); never keep the core's
pointers. The environment callback, sysdir and option store must be live before `retro_set_environment` is called
(in `azh_open`)."

**S4 (A) It is 32 keys, not 31.** The table at `core_settings.cpp:144-716` has 32 entries; the stock dylib's strings
show 32 `citra_*` keys; the profile in section 2 lists 32 lines, and every value in it is in its key's list (checked
by script). Replace "31" by "32" everywhere (section 2 twice, review item 5).

**S5 (A) Check 6 does not test the version check.** `build/libazhost.dylib` has no `retro_*` symbols, so it fails at
`dlsym` (a CoreError for a missing symbol) and never reaches the version comparison. `LAZ_ANY_CORE=1` would not
rescue it either. Fix: "6a. `--core build/libazhost.dylib` exits 4 with `CoreError: missing symbol retro_...`.
6b. The comparison is a pure function `azh_version_ok(const char *v, int any_core)` in `core.c`, tested by
`make test-version` (a 20-line host test: `2126.2` ok, `2126.3` refused, `2126.2-lazpy.1` ok, `x` with any_core ok)."
That costs about as much as the current red and actually proves the check.

**S6 (A) Where the gate's fresh copy lives, and which build checks 3-6 use.** "A new folder under the scratchpad"
is a session path that a committed script cannot know. Fix: "`COPY=$(mktemp -d "${TMPDIR:-/tmp}/lazpy-gate-a.XXXXXX")`,
removed by `trap` on exit unless `KEEP=1`; checks 2-6 all run inside `$COPY` (its `build/azhost`, its `runs/`). The
app path `$1` is made absolute before the copy."

**S7 (A) A1 is answered: pin `2126.2` now.** `BUILD_FULLNAME` = `GIT_TAG` (`CMakeModules/GenerateBuildInfo.cmake:42-56`;
the CI tag build takes it from `GITHUB_REF_NAME`). The stock dylib's strings show the scm block in `scm_rev.cpp.in`
order: `219d743a1e69...`, `HEAD`, `219d743`, `2026-10-08T22:14:10Z`, `2126.2`, `2126.2` (fullname, version). Fix:
write `#define AZH_STOCK_VERSION "2126.2"` into section 3; step 2's "record and pin" becomes "confirm".

**S8 (B) The log formats do not dual-compile.** `%lu`/`%08lx` with `uint32_t` arguments: on devkitARM `uint32_t` is
`unsigned long`, on macOS arm64 it is `unsigned int`. So `-Wall -Werror` fails on one of the two compilers (gate 1
compiles record.c on both). Fix (section 3, under the formats): "every argument is cast to the format's own type
(`(unsigned long)rec->frame`, `(unsigned long long)tick`); no `<inttypes.h>`, so record.c stays pure C as the
checklist wants."

**S9 (B) The azhost branch of gate-b.sh needs A's exact interface.** B cannot run it, and the brief gives only
"`build/azhost run ... --frames 600 --shot 300,600` and the split-PNG checker form". Fix: paste A's run line
`build/azhost run build/testapp.3dsx --sys <run>/sys --out <run>/out --frames 600 --shot 300,600`. Then: the shots are
`<run>/out/shot_000300_top.png` / `_bottom.png`, the frame count is `frames=<n>` on stdout, and the log is
`<run>/sys/Azahar/sdmc/testapp/log.txt`. Mark that branch "written, run first by the main loop after the merge".

**S10 (F1) Red 1 re-downloads 43 MB, and SRC_FILE paths are unclear.** "Download ... when it is missing or wrong",
as in fetch.sh's `get` (`tools/fetch.sh:53-71`: delete and refetch on mismatch), means a pin with one wrong digit
fetches the tarball again from GitHub on every red run. Fix: "a present file with the wrong size or sha256 is
refused (`SHA256 MISMATCH`, exit 1) and never deleted or re-downloaded; only a missing file is downloaded; a file
this run downloaded is deleted on a mismatch. `SRC_FILE` may be absolute; a relative one is under ROOT."

**S11 (index) Item moves come after worktree creation.** In "Before the launch", step 3 makes the worktrees and
step 4 moves items 110-130 to `1-in-progress/`. Each brief then has its builder edit "only its 'Lessons and notes'
section" at the `1-in-progress/` path, a path the worktree branch does not have yet. The result is a rename/add
conflict at merge, or a second copy of the item. Cheapest fix: "builders do not edit item files; each report ends with
a 'Lessons and notes' block, which the main loop pastes when it commits." (Remove the item row from each brief's
section 4.) Otherwise swap steps 3 and 4 and commit the move first.

**S12 (index) The rest of the merge plan.** (a) Step 5's clone has no `build/testapp.3dsx` (`build/` is ignored), so
add `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` before the two gates.
(b) "Wakes the main loop when it exits" has no mechanism. Add: "main loop starts one background waiter in the F1
worktree, a bounded loop on `build-core/build.exit` (at most 3 h, 60 s polls, no `pgrep`), then reads the exit code."
(c) Steps 2's `mv` is already done (`dl/azahar/` holds both files today); mark it done or make it
`[ -f dl/azahar_libretro.dylib ] && mv ...`.

**S13 (F1/index) Names the builder needs.** phase-f1.md step 0 says branch `phase-f1`, while the index says `step-f1`
(and the builder should create no branch at all). Every brief uses `<main checkout>`. Fix: step 0 says "you are
in the worktree the main loop made (branch `step-f1`); the main checkout is
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py`". Same for A and B.

## Nice

- N1 (A) Gen3D.3dsx is 5,085,008 bytes now (rebuilt 17:16 today); drop the byte count. Add "the Gen3D path appears in
  no committed file; `gate-a.sh`'s usage line names `build/testapp.3dsx`" (rules.md 8). Safety otherwise holds:
  `runs/` and `*.3dsx` are ignored (`git check-ignore` confirmed), the app is Guy's own homebrew, the menu shows no game.
- N2 (A) The render interface's `.handle` must be non-NULL: the core calls `wait_sync_index`/`get_sync_index` only
  when it is (`libretro_vk.cpp:643, 649`). Say so beside "designated initializers".
- N3 (A) `make check`: add `-o /dev/null` per file so `--analyze` writes no `.plist`; clang 17 takes
  `-Xclang -analyzer-werror`, so the "if not accepted" clause can go.
- N4 (A) The env table rows GET_LIBRETRO_PATH, GET_CAN_DUPE, SET_SYSTEM_AV_INFO, SET_PERFORMANCE_LEVEL,
  SET_SUPPORT_NO_GAME and 73|E name calls this core never makes (grep of SRC `src/citra_libretro/`). Keep them for
  safety, but label them "not sent at 2126.2".
- N5 (B) Why per-line logging is safe: SD writes are synchronous on the emulator thread in both cores (`file.cpp:198-217`,
  `!AllowsCachedReads()`, DiskFile's default is false), but OpenFile, SetSize and Close are async on stock
  (`fs_user.cpp:70`, `file.cpp:288, 317`). Say: "open the log once and never close and reopen it per line; treat
  `FSUSER_CreateDirectory`'s already-exists result as success."
- N6 (B) In 2D, clear each of the two framebuffers to the background once and redraw only the counter digits each
  frame (gfx is double-buffered). That keeps an iteration far under one vblank at the default 268 MHz.
- N7 (B) Gate 3's "`v` is the previous plus 1" is probably fine (the writes are synchronous, N5), but it is C(d)'s
  claim. If it fails, report the jumps and do not chase them in B; `f` + 1 stays exact.
- N8 (F1) Patch 0002's "values (first = default)": V2 rows carry `default_value` as their own last field; V0 puts it
  first on its own (`core_settings.cpp:785-805`). Set the field; the order in the list does not matter.
- N9 (F1) CMake gives AppleClang `-flto=thin` (Homebrew CMake `Modules/Compiler/Clang.cmake:79`). ThinLTO's link
  backend uses every core whatever `-j` says. It is nice'd, so it is acceptable; A3's `LAZ_CORE_LTO=OFF` fallback
  stays.
- N10 (F1, for F2) The tarball build's `g_scm_rev` comes from GIT-COMMIT (`GenerateBuildInfo.cmake:13-16`), the same
  `219d743a...` as stock. The savestate revision test (`savestate.cpp:71`) compares exactly that, so stock states
  very likely load into ours. PLAN 9's "may differ" worry looks unfounded; F2 still records it.
- N11 (index) Merge order does not matter (no shared files). Merge each step as its review passes; F1's builder
  finishes first.
- N12 (PLAN, record only) PLAN 2.6's "returns false for ... a non-3DS file" is true only for loaders that check a
  header early (S1). PLAN 2.4's "SD writes run on host threads (file.cpp:240)" is wrong for SD files (N5). Both go in
  the phase notes; PLAN stays as it is.

## The planner's open questions, answered from source

1. **`async_fs_operations = false`: keep.** With `deterministic_async_operations` on, `RunAsync`/`RunOnThreadWorker` run
   the work inline (`hle_ipc.h:306, 348`). But the async FS branches still compute the guest's sleep as "modelled delay
   minus host-measured time" (`fs_user.cpp:108-114`, `steady_clock::now() - pre_timer`), so host speed still leaks into
   guest time. Only `async_fs_operations = false` takes the sync branch with the modelled `open_timeout_ns`
   (`fs_user.cpp:70-84`; also `file.cpp:288, 317, 348`, `directory.cpp:76, 92`).
   **`init_ticks_type = Fixed`: keep.** `core_timing.cpp:37-44`: Random seeds the base ticks from
   `std::random_device`. Then the app's `s=svcGetSystemTick()` field differs on every run, and F2's "identical log
   lines" cannot hold.
2. **Stock version string: exactly `2126.2`** (S7). Our build gives `2126.2-lazpy.1`.
3. **Boot within 120 frames: probably, but source cannot prove it.** First-boot shader compiles cost host wall time,
   not guest frames, and per-line SD writes take no extra guest time (N5). Spike 1 saw Gen3D's heavier menu by frame
   30. Expect about 10-40; keep 120 and report the measured offset.
4. **Return from `main` reaching status 16: holds.** libctru `__appExit` → `aptExit`
   (`apt.c:371-431`): not crippled, no reinit or chainload, so `doClose`. That calls
   `APT_PrepareToCloseApplication(true)` and sets `__system_retAddr = aptExitProcess`. `__libctru_exit` then calls
   `APT_CloseApplication` before `svcExitProcess` (`ctru_exit.c:32-36`). In Azahar, PrepareToClose sets the target to
   HomeMenu (`applet_manager.cpp:1131-1136`), and CloseApplication with no HomeMenu registered calls `RequestShutdown`
   (`:1173-1177`), so `RunLoop` returns 16 (`core.cpp:144`). B's "return normally after `gfxExit()`" is right.
5. **Pixel-exact 3D markers: likely, but not provable from source.** The libretro core forces nearest-neighbour
   presentation (`core_settings.cpp:1139`, `renderer_vulkan.cpp:189`). The layout background is black
   (`settings.h:608-610`). Flat alpha-255 colours at integer edges at factor 1 should come out exact. Keep B3's
   fallback, and fix X3 first, or 3D mode never draws.

## Hour-saving pass

| Cut or cheaper route | Saves | Where |
|---|---|---|
| Pin `2126.2` now; step 2 only confirms (S7) | 0.05 h | A |
| Cut `azhost info`: host.log already logs name and version on every boot, and F2 uses `nm -gU` for the lazpy symbols. Keep it only if it stays under 30 lines | 0.05-0.1 h | A |
| The text-file boot covers the context_reset failure, so plant nothing in step 4 (S1) | 0.05 h | A |
| A pure version-compare test replaces the dylib red (S5); it is cheaper and actually tests the check | ~0 h, real coverage | A |
| Defer `AZH_FMT_RAW` (raw shots into the map) to D, its first user; A's map keeps heartbeat, stop code and message | 0.05 h | A |
| No dry-run stage: apply to the throwaway unpack with `--fuzz 0` (X1) | 0.05 h, shorter script | F1 |
| Red 1 without a 43 MB download (S10) | minutes per red run | F1 |
| fe2 runs of 15 s (markers) and 10 s (events) instead of 40/20. The light app makes far more than 600 frames in 10 s; keep the `FAIL slow` rerun | about 1.5 min per gate run | B |
| check_testapp.py decodes filter 0 only and fails on others: fe2 and azhost both write filter 0 | 0.03 h | B |
| Builders write no item files; notes go in the report (S11) | merge conflicts avoided | index |

About 0.25-0.35 h back, enough to bring Phase 1 from 3.55 h to about PLAN's 3.25 h.

## Verdict

**Not ready to build.** X1 makes F1's patch stack a coin toss, X2 makes B's own gate fail on correct code, and X3
leaves B's 3D mode hung. All three fixes are text-only and small. With S1-S13 applied as well, the plan is sound: the
facts I re-read hold (the patch-target lines, settings lines, the libctru header lines, the 32-key profile, the
Vulkan negotiation struct and the R8G8B8A8 output, the disk flush, the exit path). The file ownership splits cleanly,
and Gen3D's app is safe as A's temporary fixture. Review 2 should check X1's patch-stack wording and X3's 3D
loop most closely.
