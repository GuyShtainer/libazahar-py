# Plan review 2 (laz-12): adversarial, fresh eyes

Reviewer: opus, 2026-11-12. Object: `docs/PLAN.md` revision 1 (380 lines). Source checked: Azahar tag 2126.2
(commit 219d743a1e698101fe1ab8bef43e6563126c3c27), fetched raw from GitHub; "src:" below means that tag. Local
facts from this Mac (macOS 15.8.1, Xcode 26.3, CMake 4.3.4, 12 cores, load 32-37 at 16:37). Gen3D files read only.
Written before reading review 1; the last section checks review 1's blockers.

Counts: 3 blockers, 12 should fix, 12 nice.

## Blockers

**B1. The stop reasons rest on three wrong source readings, and the C header D starts from would freeze them.**
- svcBreak does reach SET_MESSAGE. src svc.cpp:1164-1165 logs and then calls `Core::LogException`, which ends in
  `system.SetStatus(ErrorCoreExceptionRaised, report)` (src core/arm/exception_handler.cpp:140-142). `RunLoop`
  returns that status (src core.cpp:310), and `retro_run` turns it into `DisplayMessage("Fatal Error encountered
  (14): ...")` (src citra_libretro.cpp:290-304; 14 is ErrorCoreExceptionRaised in core.h:92-113). PLAN.md:67-68
  and 351-353 say the opposite: "svcBreak only logs, so guest_break comes from the log line, not SET_MESSAGE".
- The core never sends RETRO_ENVIRONMENT_SHUTDOWN. `LibRetro::Shutdown()` (src environment.cpp:164) has no
  caller (GitHub code search: no `LibRetro::Shutdown` anywhere). A guest exit is status 16 (ShutdownRequested), so
  it comes as the same "Fatal Error encountered (16)" message. PLAN.md:69 `guest_exited` "(the core sent SHUTDOWN)"
  can never fire.
- `retro_run` does not return on an error. Its `while (!HasSubmittedFrame())` loop (src citra_libretro.cpp:287-306)
  shows the message and calls `RunLoop` again. A lasting error (not powered on, missing system files) spins forever,
  repeating the message. So `guest_error` (PLAN.md:68-69) can never be a returned stop reason. It turns into a
  HostTimeout only after T seconds.
- The log-line route is also late. The core's log goes through a queue and a backend thread (src
  common/logging/backend.cpp:352-359, 452-459) unless `instant_debug_log` is set (settings.h:659, not a libretro
  option).
**Fix:** one detector, the SET_MESSAGE callback, which reads the number: 14 is `guest_break` (also real CPU aborts,
which is what we want), 16 is `guest_exited`, 10 is missing system files, anything else is `guest_error`. It sets a
flag that is checked after `retro_run` returns. If one `retro_run` gets 3 such messages without returning, the host
writes the reason into the shared block and `_exit`s the worker with a set code. The parent raises GuestError at
once instead of waiting T (C rule 1 forbids longjmp, and `_exit` in our own worker is clean). On our core, a 3-line
patch makes the loop return on a non-Success status. The test app gets an "exit at frame N" mode, and gate C checks
`guest_exited` next to (f). Freeze the header only after this.

**B2. The repeat and savestate gates can flake on both cores: guest file I/O is asynchronous.**
SD file writes run on host threads (src hle/service/fs/file.cpp:240 `RunAsync`; src hle/kernel/hle_ipc.h:306-315
uses `std::async` unless `Settings::values.deterministic_async_operations`, settings.h:490, default false, no
libretro option). The test app writes a flushed line every frame (PLAN.md:199-200), so host wall timing leaks into
guest timing on a machine at load 35-96. Three gates are hit: C(e) "identical shot hashes", D "identical log lines
after each load", and F "the fixed clock makes C(e) identical". Also, the save drain (src citra_libretro.cpp:665-688)
runs extra guest frames with presentation suppressed. So a save "at frame N" is really at N+k vblanks, with k
unknown, and neither the host's frame counter nor gate C(d) ("vblank count = N + a constant") sees it.
**Fix:** our patch adds two options in core_settings.cpp, `deterministic_async_operations` and `instant_debug_log`,
each one setting line, both pinned on in our core's profile. The repeat gates run on our core. On the stock core
they only record the difference. `azh_save_state` reports k (the test app's vblank count before and after), and
USING.md says so. C(d) excludes batches that contain a save. With the instant log on, the debug-text stop rule is
exact on our core, which settles PLAN.md:208-210's 15-minute check there.

**B3. The patch touches the wrong files, so F's core would build but our functions could not be found.**
macOS links the core with `-exported_symbols_list libretro.osx.def` (src citra_libretro/CMakeLists.txt:93-96). That
file lists exactly the 25 `retro_*` symbols, and `nm -gU dl/azahar_libretro.dylib` shows 25 on the stock core. A
`lazpy_read_memory` the list does not name is hidden, so dlsym fails. `library_version` is set in src
environment.cpp:270 (`g_build_fullname`), not in citra_libretro.cpp. The output name is hard-set to
`azahar_libretro` (CMakeLists.txt:32). PLAN.md:139 says the patch "touches only citra_libretro.cpp and
core_settings.cpp", and a sonnet builder follows the brief as written.
**Fix:** the patch list is citra_libretro.cpp, core_settings.cpp, environment.cpp and libretro.osx.def. The build
script copies the output to `azahar_lazpy_libretro.dylib`. Gate F adds `nm -gU` showing both `lazpy_*` symbols.

## Should fix

**S1. Touch: 4 bottom-screen rows land one pixel high.** The plan models only the first step (pointer to frame
pixel, src mouse_tracker.cpp:171-172). After it come `EmuWindow::TouchPressed`, a float division
(src core/frontend/emu_window.cpp:169-185), and HID's `static_cast<u16>(y * 240)` (src hid.cpp:291-292). I ran
every pixel in float32: the pointer step misses 0 of 560 frame pixels in x and y, and all 320 x values are exact,
but y = 63, 125, 126 and 127 reach the guest as y-1. The planned unit test (PLAN.md:84-85) would pass, while gate
C(b)'s 20 points hit one of those rows about 30 % of the time: a flaky gate. **Fix:** the unit test models the
whole chain in float32 and gives the expected guest pixel. Gate C(b) compares against that, and USING.md lists the
4 rows. Do not patch HID: Qt Azahar runs the same float chain at its own window size, so Gen3D's touch targets
already live with a one-pixel truncation, and a patched HID would make our core differ from both.

**S2. The boot-failure rationale is out of date.** At 2126.2, `retro_load_game` checks the file early and returns
false for a missing path or a non-3DS file (src citra_libretro.cpp:521-553). Only `System::Load` failures inside
`context_reset` go the SET_MESSAGE route (371-405, 473-474), and then `retro_run` uploads a NULL 0x0 frame
(218-223). PLAN.md:127-129 says load_game "returns true before the app loads". **Fix:** BootError covers load_game
false, a SET_MESSAGE during `context_reset`, or a NULL frame on the first `retro_run`. Gate A stays as it is.

**S3. "Gen3D compiles its CTM movies straight into it" (PLAN.md:64) is wrong for its poll-exact tests.** Gen3D's
ctm.py:22-62 records HID polls at 234 Hz (3.91 per frame), and its golden test S1.11 uses `wait_polls`,
`hold_polls` and `touch_polls`. Frame records cannot express that. **Fix:** in F's plan, check (15 min) whether our
core can export `lazpy_movie_play(path)` over the core's own Movie playback (hid.cpp:203 already calls
`Movie().HandleTouchStatus`, and core.cpp:593 takes the movie's start time, which is a fixed clock for free). Then
Gen3D's movies run unchanged and poll-exact. The stock core keeps frame records, and USING.md says poll-exact
needs our core.

**S4. Memory export: ReadBlock does not fail on unmapped pages.** It logs and fills with zeros (src
memory.cpp:188-195), and WriteBlock silently skips them (247-253). Checking `IsValidVirtualAddress` on the start
address only (PLAN.md:140) lets a read that runs into an unmapped page return zeros as data. **Fix:** check every
page in [addr, addr+len) before the copy. Gate G adds a read that straddles the end of a mapped region.

**S5. Booking F's build.** hours.tsv books "start to end of each agent run" (PLAN.md:8). An agent that waits
40-90 min for a build books that wait as agent time, but the plan counts it as machine time (PLAN.md:239-242).
**Fix:** `build-core.sh` runs detached, the agent ends, and the main loop wakes on exit (Guy's testing rule) and
sends a short gate agent.

**S6. The hour estimates.** A (1.25) and B (1) are believable: fetch.sh, 147 lines, took 0.05 h, and each plan or
review round took 0.07-0.15 h (hours.tsv). Each phase also carries about 0.35 h of phase plan, diff review and
commit, so 9.5 h leaves about 6.3 h of building. C and D are each about 0.5 h low (B1 and S1 rework, the worker
and shared block, typed errors, pytest), and F is 0.5-1 h low for first-build failures. CMake here is 4.3.4, the
root needs 3.25, and old `cmake_minimum_required` lines in the 36 submodules may fail under CMake 4. Xcode 26.3
matches CI's macos-26. Realistic: 11-12 h as planned, about 10 h after the hour-saving list. Not wildly
optimistic.

**S7. Order: Gen3D waits on work it did not ask for first.** Savestates are not among its first needs but sit in D,
the phase its adapter waits for. Several instances are a first need but sit in E, behind the speed table. C(e) and
the debug-string check are settled only on our core (B2). **Fix:** D becomes the Python layer plus `Pool`, slots
and nice. E becomes savestates plus the speed table. C(e) and the debug check move to F. Cut the Python CLI
(`python3 -m libazahar run`, PLAN.md:227): `azhost run` already exists.

**S8. F can start at once, not "right after A" (PLAN.md:239, 271).** `build-core.sh` needs nothing from A. Start
the first core build at the very start, in the background, so risk 1 is retired before C ends.

**S9. Gate A's `otool -L build/azhost` (PLAN.md:192-193) proves nothing.** The stock core links Cocoa and
AVFoundation (`otool -L dl/azahar_libretro.dylib`), MoltenVK links AppKit, and both load at run time. **Fix:** a
runtime check (`lsappinfo` while the run is live, plus no window owned by the pid). The option profile also pins
the camera and the microphone to none, so AVFoundation never shows a permission prompt, which would be a window.

**S10. The fresh-clone gate would download.** fetch.sh keeps the core at `dl/azahar/azahar_libretro.dylib`
(fetch.sh:85-86), but this repo's `dl/` has it at `dl/azahar_libretro.dylib` (there is no `dl/azahar/`), and
runners.md says the same. Seeding "dl/ by copy" (PLAN.md:190) then makes fetch.sh fetch. **Fix:** move the files
into fetch.sh's layout once, fix runners.md, and the gate asserts no "fetch" line.

**S11. Rule 7: the README speed line.** A "light citro3d scene" (PLAN.md:198, 236-237) is close to an idle screen,
and rule 7 needs a real scene with a guest-time check. **Fix:** the README quotes spike 2's 3D-field numbers with
their load and date (the source row exists), and labels the test-app figure as a light scene.

**S12. The licence of the patch, and C hygiene in A's brief.** PLAN.md:153 says "ours is GPLv3" next to the
GPLv2-or-later core files. **Fix:** the patch hunks stay GPLv2-or-later, like the files they change, so the
published core keeps one licence (the repo stays GPLv3). The legal agent confirms. For A's brief: fe3.c's
token-pasting `IFN`/`DFN` macros (fe3.c:78-79) break C rule 8, and they look up about 18 procs on every shot
(fe3.c:114-116). Use one function-pointer table loaded at init, and size the two 64 MB `malloc(4096*4096*4)`
buffers (fe3.c:62, 132) from the av info.

## Nice

- N1. Savestate citation: core.cpp:167-170 is the slot-file path. The buffer path checks only the git revision
  (src savestate.cpp:300-305).
- N2. The boot gets its own timeout, apart from the heartbeat's T (the first run compiles shaders).
- N3. The SD text match keeps the last len(text)-1 bytes, so a match split across two reads is found. It also
  handles a file that shrinks.
- N4. CPU ms per frame leaves out GPU time (Metal through MoltenVK; spike 1 suspected a GPU ceiling). Print wall
  ms per frame too.
- N5. The core formats every Debug line before our C filter sees it (log filter Debug, src citra_libretro.cpp:59).
  Our core can raise it to Info plus Debug_Emulated.
- N6. Build script: `-j` (CI's macOS step passes none, libretro.yml:195);
  `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` if CMake 4 refuses an external; `FETCHCONTENT_FULLY_DISCONNECTED=ON`
  (rule 2). The libretro macOS path downloads nothing at configure (root CMakeLists.txt:431-436).
- N7. Cursor-off relies on `now - time_point::min()`, which overflows (mouse_tracker.cpp:117, 263-266). It works
  today, and gate C's pixel check covers it.
- N8. The worker's `-I` drops the user site, so a `pip install --user` breaks. Say venv in USING.md.
- N9. `.gitignore` ignores `sdmc/`. Fixtures must not use that name (the plan's `fixtures/sd` is fine; tell the
  brief).
- N10. "Unsigned downloads are quarantined" (PLAN.md:265) is true of our core asset too when a browser fetches it.
  curl sets no quarantine. The honest reason is "make takes seconds".
- N11. Mapping a file in the instance folder instead of `multiprocessing.shared_memory`: no resource tracker, and
  the last core message survives a worker crash for HostCrashed's report.
- N12. Flat int32 input records (7 per entry) instead of a struct leave less for `azh_abi_layout` to guard.

## Checked and right

ZL 12, ZR 13, L3 as HOME and screen swap (src citra_libretro.cpp:185-193, 243). Circle-pad y is inverted (src
input_factory.cpp:65). The pointer formula is exact for every frame pixel and never sends (0,0). The cursor moves
only with the right stick (mouse_tracker.cpp:191-238). `ReadBlock`/`WriteBlock`/`IsValidVirtualAddress` exist
(memory.h:558, 599, 673). The `init_clock`/`init_time` settings exist (settings.h:503-504), so the start-clock
option is a few lines. Variable-size savestates (628-630) and the 5 s drain (665-688) are right. Spike 2's CPU ms
per frame recomputes to 4.2, 4.6 and 4.2. The CI lines (libretro.yml:174-196), the 36 submodules and the retro_run
loop at 287 are right. Tools: devkitARM, ninja and spirv-opt are installed.

## Hour-saving list

1. **Azahar's own source tarball** `azahar-unified-source-2126.2.tar.xz` (43 MB, a .sha256sum beside it, in the
   2126.2 release; .ci/source.sh builds it with `git archive-all --force-submodules` plus GIT-COMMIT/GIT-TAG). It
   becomes the build input: one sha256 pin, fetch.sh style, instead of a 1-2 GB recursive clone and 37 commit pins.
   It is also re-hosted unchanged as the GPL source asset next to our patches. Apply with `patch -p1`, not
   `git am`. Saves about 0.5-0.75 h now and per update, and removes the tarball work from I. The pinned revision is
   then the stock one, so stock states load into ours. The `-lazpy` suffix still tells the builds apart.
2. The core's own Movie playback for Gen3D's CTM files (S3): no frame-record compiler for poll-exact tests, and a
   fixed clock comes with it.
3. `deterministic_async_operations` + `instant_debug_log` options (B2): a trivial drain, and the debug-string
   check needs no test.
4. One message detector for every stop reason (B1) replaces the log-line matcher.
5. Cut the Python CLI (S7) and the vacuous otool check (S9).
6. Start F's build at minute zero (S8): calendar time, not agent time.

## Review 1's blockers: are they really fixed?

Read after the sections above were written.
- **Review 1's B1 (memory through our own core): fixed in design, not quite in execution.** The read/write
  export, the move off SET_MEMORY_MAPS, dropping savestate parsing, and the global-plus-heap gate are all in
  (PLAN.md:139-148, 247-253). But review 1 also wrote "our patch touches only citra_libretro.cpp and
  core_settings.cpp" (its S11), and the plan copied that. The macOS export list hides the new functions (B3 here).
  The start-address-only validity check also lets zeros through (S4 here).
- **Review 1's B2 (crash and hang gates): half fixed.** HostCrashed by SIGSEGV, HostTimeout by SIGSTOP and the
  heartbeat are right and checkable (PLAN.md:224-226). The guest-side stop reasons are not. Review 1 assumed the
  core sends SHUTDOWN (env 7) and that svcBreak only logs. The revision then moved `guest_break` onto the log line.
  The source says svcBreak sets status 14, which becomes a SET_MESSAGE; no SHUTDOWN is ever sent; and `retro_run`
  loops instead of returning on an error. That is B1 here, and it must land before C's header freezes.
- **Review 1's B3 (GPL release and build exception): fixed.** rules.md 2 and 3 carry Guy's exception. Patches, the
  pin, the build script, the source beside the binary, notices, the distinct name and the audit are all in
  (PLAN.md:131-157, 262-268). Two improvements, not gaps: re-host Azahar's own unified source tarball instead of
  building one (hour-saving 1), and keep the patch GPLv2-or-later (S12).
- Review 1's S8 (silent boot failure) was based on an older load path. The plan inherited it (S2 here); harmless
  for the gate.

## Verdict

Not ready to split yet. B1-B3 are each a few lines of plan text plus small patch additions, not a redesign. Once
they are fixed, together with S1, S3, S4 and S7, the plan is ready to split into phase items without another
review round.
