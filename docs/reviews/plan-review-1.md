# Plan review 1 of 2 (laz-11): docs/PLAN.md draft 1

Reviewer: opus, 2026-11-12. Read: PLAN.md, rules.md, the four research notes plus spike 2 (landed mid-review),
prototype fe2.c and fe3.c, fetch.sh, and Azahar's source at tag 2126.2 and master (citra_libretro.cpp,
core_settings.cpp, input/mouse_tracker.cpp, emu_window/libretro_window.cpp, environment.cpp, core/core.cpp,
hle/kernel/svc.cpp, hle/kernel/process.cpp, memory.h, the root CMakeLists.txt, .github/workflows/libretro.yml).
"src:" below means github.com/azahar-emu/azahar at tag 2126.2. Also covered: Guy's two answers (we patch, build and
publish our own core, with no upstream pull request; the name is approved).

Counts: 3 blockers, 11 should fix, 8 nice.

## Blockers

**B1. Phase F as written cannot work, and the patched-core route needs its own phase.** (PLAN 190-205, 236-238)
- Problem: branch 1 is dead. Spike 2 saw SET_MEMORY_MAPS sent once, at frame 0, with only 0x0FFFC000 (0x4000) and
  VRAM. The source says why. The map is built once, in the load step, which in the Vulkan path runs from
  `context_reset`, not `retro_load_game` (src: citra_libretro.cpp:474, 416; PLAN 194 has this wrong). At that point
  the kernel has mapped only the code segments and the main stack at the heap's top end
  (process.cpp:243-248, stack = HEAP_VADDR_END - 0x4000, which is exactly spike 2's descriptor). The region filter
  then drops the code/data segment (citra_libretro.cpp:321-336). So even a re-sent "fuller map" would still miss
  **globals** (.data/.bss at 0x00100000+). Gen3D's `g_fieldDbg` (needs doc row 11) and the test app's planned
  "global struct" (PLAN 150) are both globals.
- Fix (patched core, per Guy):
  - Do not fix the map. Export two plain C functions from the core, read and write by guest virtual address.
    Each one calls the existing `Memory::ReadBlock(process, vaddr, buf, len)` / `WriteBlock` on the current process
    (memory.h:558, 599) after an `IsValidVirtualAddress` check (memory.h:673). That is about 30 lines, and it covers
    globals, heap, linear heap and VRAM with no map decoding. The host finds them with dlsym. With a stock core they
    are missing, and memory calls fail cleanly ("needs the libazahar core").
  - The same patch adds one core option for a fixed start clock (S6), since the core has none.
  - A fuller SET_MEMORY_MAPS (re-sent when the process's memory changes) is optional, for RetroArch cheat users only.
  - Cut "port libretro.py's map decoding" (PLAN 31, 197-199, 273), because fe3.c already holds a 3-line reader.
  - Move the per-frame watch list out of v1 batches (PLAN 14, 59, 69-70) until the export lands, then add it back,
    since it is a memcpy per word.
- Savestate parsing as a fallback: drop it. The state is a compressed archive whose memory layout must be decoded.
  Taking it runs the guest on to drain pending I/O (citra_libretro.cpp:665-705). It costs a 256 MB serialize per read.
  The patch is cheaper and exact. Keep one line in STATUS saying it was considered.
- Test-app gate: the struct is kept both as a global and in a heap allocation. Both must read back the values its log
  shows, frame by frame, for 600 frames, on the patched core. On the stock core, reads fail with the clean error.

**B2. The crash and hang gates test the wrong mechanism.** (PLAN 44-46, 152, 178-179)
- Problem: a guest crash does not kill the host. `svcBreak` only logs (svc.cpp:1148-1166). Unmapped guest accesses
  are logged and execution goes on. When RunLoop fails, `retro_run` posts a message and loops again
  (citra_libretro.cpp:287-303). A guest spin loop still produces vblanks, so `retro_run` keeps returning.
  So "the app's crash command raises HostCrashed in under 1 s" and "its hang command raises HostTimeout" cannot pass.
- Fix:
  - Capture the core's SET_MESSAGE (env 6) and SHUTDOWN (env 7) calls in the environment callback. Turn them into
    stop reasons "guest error (text)" and "guest exited", and add both to `azh_result` (PLAN 70).
  - The test app's crash command calls svcBreak, and the gate expects a guest-error stop.
  - HostCrashed is tested by sending SIGSEGV to our own worker. HostTimeout is tested by sending it SIGSTOP.
  - The parent's timeout watches a frame-progress heartbeat, not total batch time. The worker's C loop bumps a
    counter in a shared-memory word. Then a 200,000-frame batch is never mistaken for a hang.
  - The batch-level wall timeout (PLAN 59) stays as a between-frames check.

**B3. The release phase must carry a GPL-complete core release, and the rules need a build carve-out.**
(PLAN 112-119, 223-227; rules.md 1-3)
- Problem: we now publish a modified core binary. The plan ships "no core" and has no source, notice or build story.
  Building Azahar runs its CMake scripts from a downloaded tree, which rules.md 2 forbids ("never run a script from
  inside a download folder").
- Fix, where things live: **patch files in our repo**, not a public fork. This means `core/patches/000N-*.patch`,
  `core/PIN` (the full 40-hex Azahar commit plus each submodule's commit, checked after the clone) and
  `tools/build-core.sh`. A fork would add a second repo to keep publish-ready and audit, for no gain. Updating means
  `git am -3` onto the new pin.
  - Keep `fetch.sh` download-only.
  - rules.md 2 gets a narrow, Guy-approved exception: CMake is run on the pinned Azahar clone in `dl/azahar-src/`
    only by `build-core.sh`, nice'd, never as root.
- Fix, corresponding source:
  - Tag 2126.2 files say "GPLv2 or any later version". On master they now say GPLv3+ (commit "Update project
    license to GPLv3+").
  - Either way the simplest compliant route is to put the source next to the binary in the same GitHub release:
    a `git archive`-style tarball of the pinned tree **with every submodule** (36 in .gitmodules), plus our patches
    and the build script. This is GPLv2 §3(a), or GPLv3 §6(a)/(d) with us keeping the files available.
  - Do not just point at Azahar's repo: the submodules sit on third-party hosts we do not control.
  - Add a prominent "modified by libazahar-py on <date>" notice in each patched file (GPLv2 §2(a), GPLv3 §5(a)).
  - Name the binary so it is not taken for Azahar's own build, for example `azahar_lazpy_libretro.dylib`.
  - Ship the license texts of everything linked statically into the core (boost, dynarmic, fmt and the rest). Azahar's
    CI already makes an SPDX list per release (libretro.yml:198-220), so reuse that.
  - `release-legal-audit` checks the core asset, the source tarball and the notices.
- Fix, user flow: `fetch.sh` downloads our released patched core (sha256-pinned, the fast default) or
  `build-core.sh` builds it. The stock core stays fetchable and works for everything but memory.

## Should fix

**S1. Touch conversion is off by one, and fe3.c also maps ZR to HOME.** (PLAN 159-160, 166-167)
- The core maps the pointer value as `int((p + 0x7fff) / 65534 * width)` (mouse_tracker.cpp:144, 171).
  - fe3.c's formula lands 1 px left. Bottom-screen x = 0 maps to frame x 39, which is outside the screen, so the
    touch is ignored. Computed: X 40 gives 39, X 200 gives 199.
  - Aiming at the pixel centre, `p = floor((X + 0.5) * 65534 / 400) - 32767` (and the same with 480 for y), gives
    the exact pixel at 40, 41, 200 and 359.
  - Also: a pointer at exactly (0,0) is ignored (mouse_tracker.cpp:148). A point outside the bottom screen keeps the
    press but not the move, so the host must reject points outside 320x240.
- fe3.c's button table sends ZR as id 14, which is L3, and the core binds L3 to **HOME** and screen swap
  (citra_libretro.cpp:191-193, 243). ZR is 13.
- Fix: a pure-C round-trip unit test of our formula against the core's, at every bottom-screen pixel, in
  `make test-host`. The brief says "do not copy fe3's button table".

**S2. Risk 3 (the cursor) is answered by the source.** (PLAN 242-245)
- The pointer-timeout option defaults to enabled (core_settings.cpp:665-676). The cursor's "last moved" time is set
  only by right-stick movement (mouse_tracker.cpp:191, 221, 266). With the right stick pinned to C-stick only, the
  cursor is never drawn.
- Visibility is wall-clock based, so it must never depend on timing.
- Fix: pin both options, and add a gate check that a shot with touch held has no cursor pixels. Drop the
  try-or-mask fallback chain.

**S3. The worker mechanism is mixed up, and "no copy" is only true inside the worker.** (PLAN 40-47)
- `python -I -m libazahar._worker` and "multiprocessing with the spawn method" are two different launchers. Spawn
  re-imports the user's main script, so a one-off script without a `__main__` guard re-launches itself.
- Pixel buffers filled in the worker are pickled to the parent, which is a copy.
- Fix: `subprocess.Popen([sys.executable, "-I", "-m", "libazahar._worker"])` with a
  `multiprocessing.connection` over an inherited pipe. Hand the C host a `multiprocessing.shared_memory` block for
  pixels and the heartbeat word (B2), so numpy in the parent wraps it with no copy.

**S4. Savestates should arrive with Python v1, not in F.** (PLAN 190-192)
- Spike 2's Gen3D boot needs 7600-9200 frames to reach the 3D field (spike-2 line 22). A savestate cuts that from
  every run.
- Semantics the plan misses:
  - `retro_serialize_size` does the work and runs the guest to drain I/O (citra_libretro.cpp:692-705).
  - The size varies, because the core declares a variable-size quirk (citra_libretro.cpp:628-630).
  - States are tied to the core build (core.cpp:167-170), so a pin change makes every saved state useless. Add this
    to risk 6.
  - SD files are not in the state, so "identical log lines" after a load is mis-specified.
- Fix: move savestates into D (about 1.5 h). The gate compares shot hashes and the log lines written after each run,
  with the SD log copied aside before the load.

**S5. The speed and scaling branches: measure CPU per guest frame, and the "capped" branch is likely wrong for real
scenes.** (PLAN 105-108, 183-188, 207-214)
- Spike 2 gives a load-robust number: about 4.1-4.6 ms of CPU per guest frame.
  - Load 27: 1.4 cores at 340 fps.
  - Load 68-96: 54 s of CPU over 11,739 frames.
  - Three instances: 109 s per instance over about 26,000 frames each.
- At the same heavy load, three instances gave 3 x 137 fps against 129 for one, about 3.2x the total. So the
  3D scene is not stuck at spike 1's shared ceiling. The idle menu's ceiling was probably GPU or present cost.
- Fix:
  - Every speed table reports fps, CPU ms per guest frame (from rusage) and the load average. Then no gate waits
    for a quiet machine that a shared Mac may never have.
  - Make the default pool 3, provisional.
  - Define Phase G's "well above / near real time" as one instance at 3x real time or better at load under 10. If
    the machine is never that quiet, give the 1 / ms-per-frame figure.
  - Merge G's test-app rows into E's scaling script.
  - The Gen3D-scene row needs a commercial game on disk, so it is an optional local row that agents may skip. Its
    screenshots are never committed (rules.md 1).

**S6. Risk 4 (repeatability) is half answered.** (PLAN 246-248)
- Spike 2 shows the guest clock moves with guest time: the HUD went from 15:56 to 16:04 over 535 guest seconds while
  the run was about 5x faster than real time. Only the boot value comes from the host clock.
- 2126.2 has no clock option; the full option list is in core_settings.cpp, keys at lines 41-93.
- Gen3D's profile pins a fixed clock (needs doc row 1), so that row is not met by the stock core.
- Fix:
  - Our core patch adds a fixed start-clock option (B1).
  - The test app logs the clock at boot, and gate C(e) runs on both cores.
  - USING.md says plainly what the stock core cannot repeat.

**S7. Pin and log the whole option set and the core version.** (PLAN 162-164, 251)
- fe2 answers the option-version query with 0. That makes the core fall back to the old option list, where unset
  options take the first listed value. RetroArch's defaults may differ (for example, the right stick defaults to
  "c_stick_and_touchscreen", core_settings.cpp:615-620).
- Fix:
  - A committed option profile sets every key explicitly, including motion off, the stick deadzone and both
    touchscreen sources.
  - The host writes the effective set, plus the library version from `retro_get_system_info`, into host.log on every
    boot.
  - The host refuses a core whose version does not match the pin unless an override is set.
- State the circle-pad units: plus or minus 32767, with y inverted by the core (input_factory.cpp:65).
- Make the `Buttons` bits match libctru's KEY_* layout, so the test app's logged held keys and Gen3D's movies compare
  one-to-one.
- Note that HOME is L3 and so is not offered in v1.

**S8. Boot failure is silent in the Vulkan path.** (PLAN 58, 92)
- `retro_load_game` returns true before the app is loaded (citra_libretro.cpp:515-520). A bad path then shows up
  only as a SET_MESSAGE plus empty frames from `retro_run` (citra_libretro.cpp:218-223).
- Fix: `azh_boot` treats a load-failure message, or a missing frame image after the first `retro_run`, as BootError.
  Gate: a missing file and a non-3DS file both raise BootError.

**S9. Phase A's gate has an uncheckable part and a check it cannot do yet.** (PLAN 145, 253-254)
- `lsof` cannot show a window-server connection. Use `lsappinfo list` (no entry for the process) and
  `otool -L build/azhost` (no AppKit).
- Risk 7 says Phase A checks the test pattern exactly, but A runs alongside B, which builds the pattern. Move the
  exact-pixel check into B's gate, which also checks the 40 px bottom-screen offset.

**S10. The test app needs a forced mode at boot and safe SD writes.** (PLAN 147-156; spike 2 point c)
- Plain Gen3D never draws its 3D world without a forced-layout build. The test app reads a seeded `control.txt`
  **before** its first frame, so a seed alone picks the 3D scene with no input. USING.md shows that pattern for
  user apps.
- It flushes its log after each line. Otherwise guest-side buffering delays the stop rule, which gate C(c) would
  report as a failure.
- It uses no system archives (shared font), since NAND and system data can never be committed. Draw with our own
  glyphs.

**S11. The estimate's unit is unclear, and the patched core is not costed.** (PLAN 131, 229-232)
- hours.tsv books agent wall time: the whole plan took 0.12 h, fetch.sh 0.05 h. PLAN's hours look like Gen3D's
  one-worker hours. Pick one unit and say which.
- The core-build cost on this Mac is checked here. Xcode 26.3 and cmake are present; `brew install spirv-tools` is
  needed (libretro.yml:191). Azahar's own macOS libretro job is just `cmake -DENABLE_LIBRETRO=ON` and a build of
  `citra_libretro` (libretro.yml:174-196).
  - First recursive clone: 36 submodules (boost and dynarmic are the bulk), about 1-2 GB.
  - Clean build, my estimate: 15-25 min on the 12 cores when quiet, 40-90 min at the load spike 2 saw (run it
    nice'd in the background).
  - A rebuild after a patch edit: a few minutes.
  - Each Azahar update: fetch, `git am -3`, rebuild and the full test batch, about 1 h of machine time plus about
    0.5 h of agent time if the patch applies cleanly. Our patch touches only citra_libretro.cpp and core_settings.cpp.
  - Agent work for the new core phase: patch, build script, pin check, first build and tests, about 5 h. Most of the
    risk is a first build hitting a toolchain difference from Azahar's macos-26 runner.

## Nice

- N1. The guest can talk to the host with no SD I/O. `svcOutputDebugString` lands in the core log at debug level
  (svc.cpp:1188-1190), and the core sets its filter to Debug (citra_libretro.cpp:59). Check it in 15 min in Phase C.
  It makes a stop rule on a guest line, and lets the test app carry its per-frame record with no file reads. Log
  lines may arrive a little late, because the log backend runs on a thread.
- N2. Filter core log lines by level in C. At Debug level and hundreds of fps, log writes can enter the hot path.
- N3. Replace the "compile a C program to print struct offsets" test (PLAN 173-174) with an exported
  `azh_abi_layout()` that the Python test compares. No compiler is needed at test time, and the check also runs on
  installed copies.
- N4. Skip the prebuilt `libazhost.dylib` in the release (PLAN 225). A downloaded unsigned dylib is quarantined by
  Gatekeeper, and `make` is seconds. Ship the patched core (B3) and `testapp.3dsx`.
- N5. The slot cap counts only our workers. Spike 2's load of 58-96 came from other sessions' windowed Azahar
  instances, which the cap cannot see. Print a warning when the load average is above about 2x the core count.
- N6. A CI job on GitHub's macOS arm64 runners for `make test-host` and the Python unit tests (no core, no GPU),
  about 1 h, after Phase D. Building the patched core in CI too would take that work off this busy Mac; consider it
  at the first core update.
- N7. Allow `fetch.sh` to copy from a local cache in the fresh-clone gate (PLAN 143), so each gate run does not
  download about 40 MB.
- N8. Golden rules: say in the Phase A brief that callbacks are the documented function-pointer exception (C rule 9).
  Savestates allocate per call because of the variable size; that is fine on a hosted tool if the owner is clear
  (C rule 3). Aim for about 2 assertions per function (C rule 5). The Python side already meets rules 3, 6, 7 and 9
  as planned.

## Phase order and gaps

- The order should be A + B, then C, then D (Python v1 **plus savestates**), then E, and F (our core, B1/B3) in
  parallel with E. F's first build can start in the background as soon as A is done, since it is mostly machine
  time. G becomes a row set inside E (S5). Then H, then I.
- D can start from the frozen C header while C is being built: the batch struct is fixed in C's plan.
- Gen3D's first needs (seeded SD and files read back, frame-exact buttons then touch, cropped shots, run until a
  frame count or a log line) all land by D. Savestates now do too. Memory lands in F, which is fine: Gen3D's main
  runner barely needs RAM.
- Missing work, now covered above: guest-error and guest-exit stop reasons (B2), boot-failure detection (S8),
  core-version check (S7), heartbeat timeout (B2), and the core's GPL release (B3). Determinism is gated by C(e),
  which now runs on both cores.

## Hour-saving pass

| Change | Saves |
|---|---|
| Memory by a 30-line read/write export in our core, not map decoding, a ported decoder or savestate parsing (B1) | about 2 h against plan F's 6 h branch, before adding the core build itself |
| Reuse fe3.c's frame-range input table and memory-map handler shape in C (after fixing S1) | about 1 h |
| CPU ms per guest frame as the metric; G folded into E; no quiet-machine wait (S5) | about 2 h |
| Cursor and clock questions answered from source now (S2, S6) | about 0.5 h |
| ABI layout exported by the dylib (N3) | about 0.5 h |
| No prebuilt host dylib in the release (N4) | about 0.5 h |
| USING.md written in D, so H only finishes it | about 1 h |
| Patch files in our repo, not a fork (B3) | about 1 h now, plus 0.5 h per update |
| Existing things checked: nanoarch-style frontends are GL plus a window; RetroArch's Vulkan path needs a surface; libretro.py has no Vulkan (probe); Azahar's RPC is not in libretro builds and the gdb stub is excluded by CMake (root CMakeLists.txt:109-111). None beat fe3.c | 0 h, rejections stand |

Total saved: about 8.5 h. Added: the core phase (about 5 h agent time plus 1 h of release and notice work), the
crash and exit stop reasons, the boot check and the option log (about 1 h). Net, in PLAN's units: about 40-42 h
becomes about 39 h, with memory that actually works.

## Verdict

The architecture holds: a C host, one process per instance, ctypes in a worker, and batches only. The single-core
process claim is right (`GetInstance()` and file statics throughout citra_libretro.cpp), and the flock slot cap is
sound (the kernel drops the lock on exit). Draft 2 must:
- rewrite F around our own core with a read/write export, plus its GPL-complete release and the build carve-out;
- fix the crash and hang gates;
- fix the touch formula and the cursor and clock risks;
- pull savestates into D;
- switch speed to CPU per guest frame.

Then it is ready for review 2.
