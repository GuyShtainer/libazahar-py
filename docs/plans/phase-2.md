# Phase 2, control: the phase plan (item laz-200)

Opus phase plan, 2026-11-12, **revision 2** (after `docs/reviews/phase-2-review-1.md` and
`docs/reviews/phase-2-review-2.md`). Review 2 asked for no third loop: the main loop checks that each X and S fix
below is in the text, then launches. Steps: C (laz-210, `docs/plans/phase-c.md`) and D (laz-220,
`docs/plans/phase-d.md`). Each brief is complete on its own for one sonnet builder. This file is the index: order,
checkpoints, file ownership, merge plan, hours, the approved departures from PLAN.md, the interfaces taken from
Phase 1, the checked facts, and the changes from both reviews.

Contract: `docs/PLAN.md` (final) sections 2.1-2.9, the grouping paragraph of section 3 and its Phase C and Phase D
paragraphs. This plan refines them. Where a brief disagrees with PLAN.md on a goal, PLAN.md wins and the builder stops
and reports, **except for the approved departures of section 5**, which the builders follow without stopping. Phase
1's inputs: revision 2 (commit 62fa531: `phase-1.md` with its "Interfaces for Phase 2", `phase-a.md`, `phase-b.md`,
`phase-f1.md`) and step A's as-built report (item 120's "Lessons and notes": gate-a 8/8, not yet merged).

Hours are agent wall time (PLAN.md's unit). Machine time (emulator batches, and any wait for the core build) is not
counted.

## 1. The two steps

| Step | Delivers | Gate (headless, this Mac, test app, stock core) | Hours |
|---|---|---|---|
| C, laz-210 | `azh_run` with input records, touch and circle pad; raw shots into the map (`AZH_FMT_RAW`); the SD and debug-text stop rules; stop reasons from one SET_MESSAGE detector that tells a crash from a break; heartbeat, frame and vblank totals and the wall limit in the map; SD seeding; `azhost` flags; pure-C unit tests (`make test-host`); the frozen ABI header with a checked layout table | `make test-host` passes; `python3 -I tests/gate_c.py` prints PASS for C(a)-(f) and the raw-shot check; C(g) is in the unit tests | 2.0 |
| D, laz-220 | `python/libazahar/` (Emulator, worker process, mapped file, typed errors, ctypes checked against `azh_abi_layout()`), `pyproject.toml`; `host/state.c`, `host/statemeta.c`: savestates with the app's identity, the SD snapshot and state boot; pytest; `docs/USING.md` with the Gen3D mapping | `LAZ_REQUIRE_EMULATOR=1 python3 -m pytest -q -rs tests/python` all pass, 0 skipped: C's checks through Python, SIGSEGV gives `HostCrashed` within 1 s, SIGSTOP gives `HostTimeout` and no process, 200,000 frames not a hang, state boot same screen and log fields at under 10 % of the boot's wall time; a scratch venv `pip install -e .` imports | 2.1 |

Phase total: **4.1 h** of step work plus about 0.5 h for the two review loops (PLAN.md section 3's grouping
paragraph) = **about 4.6 h**, against PLAN.md's 2.0 + 2.25 + 0.5 = 4.75 h. The checkpoint choreography (two commits,
one merge, two resumes) is main-loop time, about 0.15 h, booked to the main loop.

## 2. Order, checkpoints and the parallel split

```
Phase 1 merged on main (A and B; F1 not needed); the core build may be running in MAIN (phase-1.md "Merge and
launch" step 6)
  |
  C builder (sonnet, ../libazahar-py-c, branch step-c)
  |  C1: frozen headers + pure modules + unit tests + D's stubs; ENDS ITS RUN with the "C1 done" report
  |     main loop re-reads the frozen header once (review 2's verdict), commits C1 on step-c,
  |     creates ../libazahar-py-d (branch step-d) at the C1 commit,
  |     resumes C (SendMessage "C1 committed at <sha>, go on with C2")
  |     and launches the D builder (sonnet) with phase-d.md
  |  C2: run loop, inputs, stops, raw shots           D1: Python package, worker, errors, pure tests
  |  C3: azhost flags, seeding, gate_c.py              D2: state.c, statemeta.c, unit tests
  |  gate C (after the core build ends)               D ENDS ITS RUN with the "D1+D2 done" report
  v
  opus as-built review of C; fixes; main loop commits and merges step-c into main
                                                      main loop: git merge main in ../libazahar-py-d
                                                      main loop resumes D (SendMessage "main merged at <sha>,
                                                      go on with D3"): integration pytest + docs/USING.md
                                                      opus as-built review of D; main loop merges step-d
```

- **A builder never waits for the main loop.** A subagent reports only by ending its run, so each checkpoint is the
  end of a run: C after C1, D after D2. The main loop commits, then resumes the same agent with SendMessage, so its
  context is kept. At each launch the main loop writes the builder's agent id into the handoff. If a resume fails
  (the id is lost or the context gone), the fallback is a fresh sonnet given the brief, the earlier report and
  `git log step-c` (or `step-d`); the reports list their exact paths and measured values to make that possible.
- **How a builder waits on its own long command** (review 2 S9): never `sleep`-poll and never "be woken" (a sub-agent
  that ends its turn ends its run). Long runs write an rc file from a `trap` on every exit path; the builder starts
  them with `run_in_background` and waits with the Monitor tool on "the rc file exists" (an until-loop, bounded); it
  stops every waiter it started (TaskStop) before it hands back. If Monitor is not in its tool list, it runs the gate
  in foreground parts that each fit under the 10-minute Bash limit, and says so in its report.
- **The core build** (review 2 S10): Phase 1 starts our core's 15-90 minute build in MAIN right after its merge. C1,
  C2, D1 and D2 may overlap it (no emulator, or only C2's two short by-hand runs). C3's gate and D3's slow tests
  start only when `MAIN/build-core/build.exit` exists, or `MAIN/build-core/build.pid` names no live process, or
  neither file exists (no build started). Otherwise the builder waits with Monitor (bounded 120 min) and reports
  the wait. The main loop may instead tell a builder "run under the build"; then a `FAIL slow` is rerun after the
  build. The wait is machine time. Builders only read MAIN's `build-core/`: F2 (Phase 3) reads
  `build-core/azahar_lazpy_libretro.dylib` and `build.log` there.
- **D starts from C's frozen headers** (PLAN.md section 3): the freeze is checkpoint C1. C1 also creates the stub
  files D owns (`host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c`) and real or stub versions of the
  run.c functions D links against, so D's code builds from the C1 commit and the two builders never edit the same
  file. After C1 nobody edits `azhost.h`, `azh_internal.h` or `azh_pure.h`. A needed change stops both builders and
  goes to the main loop (then C and D run one after the other, the fallback order).
- Only C's builder runs the emulator during the parallel window (D1 and D2 are unit tests only). D3 runs after C is
  merged, one instance at a time.
- Why parallel (review 1, Q2): D1 and D2 need only the frozen headers. That saves about 1.1 h of elapsed time on the
  path Gen3D waits on, for about 0.15 h of main-loop time.

## 3. File ownership (who creates or edits what)

Phase 1's A creates the host files; Phase 2 edits named functions in them. Each file has one owner at a time.

| File | Owner in Phase 2 | What changes |
|---|---|---|
| `host/azhost.h`, `host/azh_internal.h`, `host/azh_pure.h` | C (frozen at C1) | phase-c.md section 3; nobody edits them after C1 |
| `host/input.c`, `host/match.c`, `host/msg.c`, `host/rawcopy.c`, `host/sdcopy.c` | C | new modules (all pure except `sdcopy.c`, which uses only POSIX) |
| `host/run.c` (batch loop, input callbacks, counters, batch RAW shots), `host/env.c` (SET_MESSAGE case), `host/log.c` (the armed debug observer), `host/hostmap.c` (new fields), `host/api.c` (`azh_run`, `azh_set_input`, `azh_shot`'s RAW branch, `azh_abi_layout`, the input-callback install at the end of `azh_open`, the routing to `state.c`), `host/azhost_main.c` (run flags, `layout`), `Makefile` (`test-host`) | C | phase-c.md section 5 |
| `host/crop.c`, `host/frame.c`, `host/png.c` | A's; C calls them and edits none | |
| `tests/host/*.c` except `test_statemeta.c`, `tests/host/messages.txt`, `tests/testapp_log.py`, `tests/checks_c.py`, `tests/gate_c.py` | C | new |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | D (C1 creates stubs) | savestates and state boot |
| `python/libazahar/**`, `pyproject.toml`, `tests/python/**`, `docs/USING.md` | D | new |

Neither builder touches: `core/`, `testapp/`, `host/core.c` (A loads all 25 `retro_*` symbols), `tests/gate-a.sh`,
`tests/gate-b.sh`, `tests/check_testapp.py` (both import its PNG decoder; neither edits it), `tests/test_version.c`
(A's; Phase 2 does not take it over), `.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`,
the handoff, **every item file**, `prototype/`, `tools/`, `README.md`, anything in MAIN (read and copy only; MAIN's
`build-core/` is read only). Lines the main loop must add (`.gitignore`, runners) and the "Lessons and notes" block
for the item go in the builder's report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. `git worktree list` and a case-insensitive name check first, then `git worktree add -b step-c
   ../libazahar-py-c main`. Dispatch without isolation, cwd in the worktree. The builder seeds its ignored `dl/` and
   `vendor/` itself (phase-c.md step 0). Write the agent id into the handoff.
2. At "C1 done": re-read the frozen `host/azhost.h` once against phase-c.md section 3 (review 2's verdict); commit
   exactly C1's paths on `step-c` (`git add <paths>`, `git diff --cached --stat`); `git worktree add -b step-d
   ../libazahar-py-d <C1 commit>`; launch D with phase-d.md (id into the handoff); resume C with "C1 committed at
   <sha>, go on with C2".
3. At "C done": opus as-built review of the step-c diff (phase-c.md section 14); fixes by the resumed C builder if
   any; commit; merge `step-c` into main; paste the report's "Lessons and notes" into item 210 and move it with its
   Evidence line.
4. At "D1+D2 done" (it may come before or after 3): commit D's paths on `step-d`. Once step 3 is done: in
   `../libazahar-py-d`, `git merge main` (disjoint files, no conflicts expected); resume D with "main merged at <sha>,
   go on with D3".
5. At "D done": opus as-built review (phase-d.md section 13), fixes, commit, merge `step-d` into main; item 220 as in
   3; then the phase item 200. Remove each worktree only after `git status --porcelain` is empty in it.
6. The main loop's own background batches keep the usual rule (launched in the background, the main loop is woken
   on exit). The full suite (gates A, B, C, D) runs once after the phase merges, as one background batch.

## 5. Approved departures from PLAN.md (review 2 S4; builders follow these without stopping)

| # | PLAN.md says | Phase 2 does | Why |
|---|---|---|---|
| P1 | Phase C gate (a): inputs seen "on exactly the planned frames, with a fixed, measured offset" | every change's offset from its planned frame, counted in host frames with the run's smallest boot offset, is never negative and lies in {m, m + 1} for the kind's smallest m (at most 2), and the commoner value covers at least 90 % of the kind's changes; expected sets are {0, 1} for buttons and ZL/ZR and {1, 2} for touch, and another m prints a `NOTE`, not a fail | the HID pad poll runs at clock/234, 3.91 polls per VBlank, so its phase drifts against the frame (hid.h:342; review 1 S1, review 2 S1). A change can never show before its frame, so the set still catches causality and off-by-two bugs |
| P2 | Phase D: integration tests "skipped with a reason when the core or the app is missing" | kept, plus `LAZ_REQUIRE_EMULATOR=1` turns each such skip into a failure; the gate command sets it and asks 0 skipped | the gate must prove the slow tests ran; public users without the core still get skips |
| P3 | PLAN 2.1: the worker runs `python -I -m libazahar._worker` | `python -I -c "..."` with the package root as an argument | `-I` hides an uninstalled package from `-m` (phase-d.md section 2) |
| P4 | PLAN 2.9: "the state checks the program id" | the meta also stores the app's sha256; a state for another app is refused before any frame unless `LAZ_STATE_ANY_APP=1` | every `.3dsx` has title id 0 (the 3DSX loader has no `ReadProgramId`), so the core's check is a no-op for homebrew (review 2 S3) |
| P5 | PLAN 2.2's debug-text stop | refused on the stock core (`AZH_E_NEEDS_LAZPY_CORE`) | without `instant_debug_log` the core's log runs on its own thread (backend.cpp:353-360, 452-466), so a hit can land frames late or after the batch disarmed it; no stock option sets it; our core's profile does (phase-f1.md) |
| P6 | PLAN 2.5's error classes | adds `HostError` (call order, I/O, memory, unsupported, ABI mismatch) | a typed home for host-side failures that are not the guest's |

Guy should hear about P4: PLAN 2.9's program-id sentence does not hold for `.3dsx`.

## 6. Interfaces taken from Phase 1 (revision 2, commit 62fa531, and step A as built)

Cited by section name (review 2 N15). "As built" means step A's report (item 120, "Lessons and notes"), which the
merged code may still refine; if a name differs, the builders follow the code and report it.

| # | What Phase 2 relies on | Source | State |
|---|---|---|---|
| A1 | A's header: `AZH_E_*` -1 ARG, -2 `AZH_E_ORDER`, -3 CORE, -4 BOOT, -5 VULKAN, -6 IO, -7 NOMEM, -8 UNSUPPORTED, -9 NEEDS_LAZPY_CORE, -10 `AZH_E_SAVESTATE` (reserved for D); `AZH_EXIT_*` 0, 2-6, 10, 11; `AZH_SCREEN_*`, `AZH_FMT_*`, `AZH_STOP_*` 0-6; `AZH_INPUT_INTS 7`; fixed-array structs; 14 functions | phase-a "3. The API" | holds; C1 adds no error code |
| A2 | The stats struct is `struct azh_stats` with the typedef `azh_stats_t`; the function is `int azh_stats(struct azh_stats *)` | step A as built | holds; Phase 2 writes `azh_stats_t` |
| A3 | `n` counts records of `AZH_INPUT_INTS` int32 | phase-a "3. The API" | holds |
| A4 | `azh_boot` runs no `retro_run`; the NULL-first-frame check is made on the first `retro_run` of the first batch (`AZH_E_BOOT` from `azh_run`); every `retro_run` since boot counts toward the absolute frame | phase-a "3. The API"; phase-1 "Interfaces for Phase 2" | holds |
| A5 | `host.map`: 0 magic, 8 version, 12 header size, 16 heartbeat, 24 stop code, 28 message length, 32 message [1024], 1056 dims, 1072 pixel frame, bytes 1080-4095 free for C, 4096 pixels (top 400x240 then bottom 320x240 RGBA), total 695,296 | phase-a "3. The API"; as built (map 695,296, heartbeat 16) | holds |
| A6 | One internal state struct holding the sysdir, frame counters, a booted flag and the is-our-core flag; file statics elsewhere | phase-a "4. Files"; phase-1 "Interfaces for Phase 2" | holds |
| A7 | `env.c`'s SET_MESSAGE capture and the boot-failure flag; the "(N)" parsing is C's | phase-a "4. Files" | holds |
| A8 | `log.c`: a mutex around one write; the level threshold from `LAZ_LOG_LEVEL`; the core's log callback **writes the line the core passes as text, never as a format** (the core passes a finished line as `fmt`, backend.cpp:97-98) | phase-a "4. Files"; Phase 1 as-built fix list (review 2 S5) | Phase 2 relies on the literal write; if the merged `log.c` still formats `fmt`, the C builder reports it and does not fix it |
| A9 | `host/crop.c` is pure and computes rectangles only (`azh_crop_rects`); the PNG writer takes a row stride | step A as built | holds; C's raw copy is new code (`rawcopy.c`) built on `azh_crop_rects` |
| A10 | `host/azh_pure.h` holds the pure files' prototypes | step A as built | holds; C1 adds its pure prototypes there |
| A11 | `azhost run <app> --sys --out --frames N [--shot ...] [--opt k=v]... [--profile] [--core] [--mvk] [--state]`; summary `frames=<n> wall=<s> fps=<f> shots=<k>`; `BootError:` etc. on stderr; no `info` subcommand | phase-a "3. The API" | holds; C adds the `layout` subcommand |
| A12 | The library reads `LAZ_MVK`; `azhost --mvk` only sets it; default paths relative to the current directory; `vk.c` sets `MVK_CONFIG_LOG_LEVEL=1` unless set | phase-a "3. The API"; as built | holds; D sends absolute paths |
| A13 | The profile: 32 keys, right stick C-stick only, pointer timeout on, both touchscreen sources, resolution factor 1; `azh_set_option` validates at once | phase-a "2. Facts"; phase-1 "Interfaces" | holds |
| A14 | `core.c` loads all 25 `retro_*` symbols, the three serialize ones included | phase-a "3. The API" | holds; D adds no `dlsym` |
| A15 | `make testapp` delegates to `testapp/`; `build/testapp.3dsx` | phase-a "4. Files" | holds |
| A16 | Our core's `retro_run` returns after the message on a non-Success status | phase-f1 | holds (used only on our core) |
| A17 | `azh_abi_layout` and `azh_error` work in any state, before `azh_open` too; as built, `azh_abi_layout` reports batch 3344, result 40, stats 240, layout 48 | phase-a "3. The API"; as built | holds; C1's sizes are in phase-c.md 3.2 |
| A18 | `AZH_FMT_RAW` returns `AZH_E_UNSUPPORTED` until step C | phase-a "3. The API" | holds; C2 implements it |
| A19 | The readback runs in run.c after `retro_run` returns on shot frames, and from `azh_shot` for the last frame after a batch; `frame.c` only notes the frame; the readback buffer is 400x480 RGBA (768,000 bytes) from the first frame | phase-a "4. Files"; phase-1 "Interfaces"; as built | holds; C's RAW copy sits beside the readback, in run.c and api.c |
| A20 | The core offers no `create_instance`; the host makes the Vulkan instance | as built | nothing in Phase 2 depends on it |
| B1 | `build/testapp.3dsx`, built with `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH` | phase-b "2. Facts" | holds |
| B2 | `<sys>/Azahar/sdmc/testapp/control.txt`, read before the first frame; keys `draw=2d|3d`, `break_at`, `exit_at`, `ready_at` (1 to 1,000,000), `boot_frames` (1 to 10,000) | phase-b "3. The app" | holds |
| B3 | Log lines `start ...` (it contains `ready_at=`); per frame `f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d`; events `ready f= v=`, `booted f= v= sum=`, `break f= v=`, `exit f= v=`; `f` from 1 including boot frames; `v` meaningful in 2D only; **every log line also goes to `svcOutputDebugString`** | phase-b "3. The app" | holds; Phase 2's gates use 2D only, and debug-text stops match `ready f=`, never a bare `ready` |
| B4 | 2D loop: `hidScanInput`, record, log, events, draw, swap, `gspWaitForVBlank0()` | phase-b "3. The app" | holds |
| B5 | After `break f=N`, `svcBreak(USERBREAK_ASSERT)`, then `f=N+1` goes on | phase-b "3. The app" | holds |
| B6 | Busy boot frames, no per-frame lines, then `booted` | phase-b "3. The app" | holds |
| B7 | `exit_at` returns from `main`; libctru's exit path reaches APT close and status 16 | phase-b "2. Facts" | holds |
| B8 | Markers at the corners, background `#202020`; `check_testapp.py markers --top --bottom --mode 2d` | phase-b "3. The app" | holds |
| B9 | `ready_at` writes `ready f= v=` and keeps running | phase-b "3. The app" | holds |
| B10 | The app never exits on a button, START included | phase-b "3. The app" | holds |
| B11 | `tests/check_testapp.py` exposes `read_png_rgba(path) -> (width, height, rgba_bytes)`, RGB expanded to RGBA, `ValueError` on unsupported PNGs, the CLI behind `if __name__ == "__main__":` | phase-b "4. Files" | holds |
| B12 | `python3 -I` implies `-P` (3.11+): a script's own folder is not on `sys.path`, so every importer of `check_testapp` inserts the absolute `tests/` path first | phase-1 "Interfaces for Phase 2" | holds; phase-c 5 and phase-d 5 say where |
| B13 | The test app's memory record: 32 bytes, magic 0, frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24 | phase-b "3. The app" | for Phase 3's step G; Phase 2 reads no guest memory; USING.md's Gen3D table points at it |
| SD | SD file writes are synchronous on the emulator thread (file.cpp:200-217), so a line is on the host when the guest's write returns; OpenFile, SetSize and Close run async on the stock core (fs_user.cpp:70, file.cpp:288, 317) | phase-b "2. Facts" | holds; which `retro_run` a write falls in can still slip by one (review 2 S2), so C's bounds use the smallest measured boot offset |

## 7. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/` (GIT-COMMIT 219d743a, GIT-TAG 2126.2), read
2026-11-12. "LIBCTRU" = `/opt/devkitpro/libctru/include/3ds/services/hid.h` on this Mac.

| Fact | Where |
|---|---|
| Joypad bindings: A=8, B=0, X=9, Y=1, Up=4, Down=5, Left=6, Right=7, L=10, R=11, Start=3, Select=2, ZL=12, ZR=13, Home=14 (L3) | SRC citra_libretro/citra_libretro.cpp:150-193 |
| L3 also toggles the screen swap | SRC citra_libretro.cpp:243-244 |
| `retro_run` loops `while (!HasSubmittedFrame())` over `RunLoop()`; non-Success sends "Azahar was unable to locate a 3DS system archive: ..." (status 10) or "Fatal Error encountered (N): ..."; it is the only `DisplayMessage` during a run | SRC citra_libretro.cpp:287-306; other callers :379-603 |
| `RunLoop` resets the status to Success first, so the guest runs on after an exception | SRC core/core.cpp:110-111 |
| **Status 14 is set by `Core::LogException` for every guest exception**: undefined or unpredictable instruction, decode error, no-execute fault and `bkpt` (dynarmic), unmapped access when `enable_exception_handler` is on (default off), and `SVC::Break`. The message details are the report: `Thread:`, `Process:`, `Exception Type: <Unmapped Read\|Unmapped Write\|Data Abort\|Prefetch Abort\|Undefined Instruction\|Break\|Unknown>`, registers, stack, one item per line. So `Exception Type: Break` is a break; any other 14 is a crash | SRC core/arm/exception_handler.cpp:80-96, 99-142; core/arm/dynarmic/arm_dynarmic.cpp:144-159; core/memory.cpp:578-582; common/settings.h:662; core/hle/kernel/svc.cpp:1148-1166 |
| After status 16 the shutdown signal is consumed and the VBlank keeps firing, so the stock `retro_run` may well return; the host never lets it (its handler `_exit`s) | SRC core.cpp:132-150; video_core/gpu.cpp:487-497 |
| Status numbers: 10 SystemFiles, 14 CoreExceptionRaised, 16 ShutdownRequested, 17 Unknown | SRC core/core.h:92-113 |
| `DisplayMessage` is `RETRO_ENVIRONMENT_SET_MESSAGE` (6) with `struct retro_message {msg, frames}` | SRC citra_libretro/environment.cpp:169-174 |
| Buttons are read at every HID pad poll; the pad update runs at `clock / 234` (3.91 polls per VBlank); `MAX_SLICE_LENGTH` is the same period, so the guest's work after a VBlank can slip into the next `retro_run` | SRC citra_libretro/input/input_factory.cpp:29-31; core/hle/service/hid/hid.cpp:205-218; hid.h:342; core/core_timing.h:184; core.cpp:276-300 |
| Circle pad: `(x / INT16_MAX, -y / INT16_MAX)`; HID `roundf(f * 0x9A)`, averaged over 3 polls | SRC input_factory.cpp:60-66; hid.cpp:227-241; hid.h:372 |
| ZL and ZR reach the guest through ir:rst (own update period); libctru's `hid.o` imports `irrstInit`, `irrstKeysHeld`, `APT_CheckNew3DS` | SRC core/hle/service/ir/ir_rst.cpp:56-59, 92-93, 144, 156; `arm-none-eabi-nm libctru.a` 2026-11-12 |
| Touch: `PollEvents` reads the pointer and calls `input_poll_cb` once per VBlank, from `EndFrame` at the end of the renderer's `SwapBuffers` | SRC citra_libretro/emu_window/libretro_window.cpp:194-224; video_core/renderer_base.cpp:43-48; renderer_vulkan/renderer_vulkan.cpp:1183; video_core/gpu.cpp:494 |
| Pointer to frame pixel: `static_cast<int>((p + 0x7fff) / (float)(0x7fff * 2) * bufferWidth)`; (0, 0) ignored; applied only if it differs from the last | SRC citra_libretro/input/mouse_tracker.cpp:144-145, 171-189 |
| Frame pixel to touch: float division; no swap, because `DefaultFrameLayout` calls `LargeFrameLayout`, whose result has `is_rotated = !upright` = true | SRC core/frontend/emu_window.cpp:155-192; core/frontend/framebuffer_layout.cpp:57-60, 159 |
| HID: `static_cast<u16>(x * 320)`, `static_cast<u16>(y * 240)` | SRC hid.cpp:292-293 |
| float32 recompute: the pointer formula hits the exact frame pixel; guest x exact; guest y = y - 1 for exactly y = 63, 125, 126, 127 | this plan, review 1 N7 and review 2 section 3 (numpy) |
| Cursor: drawn only if visible; never visible because `last_moved` starts at `time_point::min()` and `now - last_moved` wraps into a huge count, with the timeout on and the right stick on C-stick; crosshair 8 px each side. The hidden cursor rests on that wrap: nobody changes the profile's pointer timeout | SRC mouse_tracker.cpp:117, 191-238, 243-269; renderer_vulkan.cpp:1065-1080 |
| The core's libretro log backend formats the line itself and passes it as the format with no arguments; without `instant_debug_log` the backend runs on the `citra:Log` thread; no stock option sets it | SRC common/logging/backend.cpp:69-99, 345-361, 452-466; phase-f1.md (`citra_instant_debug_log`) |
| Savestate: `retro_serialize_size` drains while async work is pending (up to 5 s, presentation suppressed), returns 0 on timeout or error, then a full `SaveStateBuffer`; `retro_serialize` copies it; `retro_unserialize` drains, then `LoadStateBuffer` | SRC citra_libretro.cpp:649-738 |
| During the drain the window's `SwapBuffers` returns early but `PollEvents` still runs every VBlank | SRC libretro_window.cpp:68-71, 204 |
| `LoadStateBuffer` checks the program id and the build revision; zstd. For a `.3dsx` the program id is 0 (no `ReadProgramId` in the 3DSX loader) | SRC core/savestate.cpp:253, 296-306; core/loader/loader.h:219-221; core.cpp:515-519 |
| Open guest files survive a state: `IOFile` keeps path (with `%CITRA_USER_SDMC%`, `%CITRA_ROM_FILE%`), mode and position and reopens on load; SD files open `r+b`; NAND files reopen from the new instance's NAND, which is not snapshotted | SRC common/file_util.h:80-104, 667-682; file_util.cpp:1058-1065; file_sys/archive_sdmc.cpp:105 |
| libctru keys: A 0, B 1, SELECT 2, START 3, DRIGHT 4, DLEFT 5, DUP 6, DDOWN 7, R 8, L 9, X 10, Y 11, ZL 14, ZR 15, TOUCH 20, CSTICK 24-27, CPAD 28-31 | LIBCTRU:12-34 |
| macOS `copyfile(3)`: `COPYFILE_CLONE` (1<<24) clones on APFS and falls back to a copy | `$(xcrun --show-sdk-path)/usr/include/copyfile.h:113` |
| macOS CommonCrypto `CC_SHA256_Init/Update/Final` (in libSystem, no extra link flag) | `$(xcrun --show-sdk-path)/usr/include/CommonCrypto/CommonDigest.h` |
| This Mac: python3 3.14.0; pytest 9.2.0 and numpy 2.5.0 only in the user site; setuptools not importable under `-I`; Pillow absent | `python3 -c` checks, 2026-11-12 |

## 8. Risks for this phase

1. **Input timing jitters by one frame** (P1). The gate's sets are named and causal; the builder reports the
   measured sets; reviewers may tighten later, builders never loosen.
2. **The boot offset c slips by one** at some batch ends (the same drift). Mitigation: scenario (a) ends with eight
   one-frame batches, so the run's smallest c (c_min) is measured nine times; every bound uses c_min; d3 accepts
   c_min or c_min + 1.
3. **The 10 % state-boot wall check** includes the core's own start. Mitigation: the test prints `t_core_start`
   (instance A's `Emulator(...)` wall), `t_boot`, `t_state`, the plain ratio and the ratio with the fixed cost
   removed, and each restore step's time. If only the plain ratio fails, the builder reports and the main loop takes
   it to Guy; nothing is tuned.
4. **The restore's drain is a full serialize** (the only drain entry point). Timed in host.log; a 0 is an error;
   Phase G's core may export a drain-only call.
5. **`-I` and the user-site pytest** on this Mac: the worker starts with an explicit package root (P3); USING.md says:
   editable install into a venv.
6. **Loaded-machine flakes** (c3 timing, SIGSTOP timing, the ratio): every check prints its measured value; a slow
   result is a separate `FAIL slow <id>` line, rerun once before reporting; the timed gates wait for the core build
   (section 2).
7. **macOS crash reports** for the SIGSEGV test: the test prints the kill-to-raise delay and the builder checks
   `~/Library/Logs/DiagnosticReports` once, deleting nothing.
8. **The real status-14 text** might lack the `Exception Type: Break` line for `svcBreak`. Gate (e) would then show
   `guest_error`; the builder stops and reports with the text (never matches on something looser).

## 9. Hour-saving pass (revision 2)

| Existing thing or cut | What it saves | Verdict |
|---|---|---|
| A's `crop.c` rectangles, A's 25-symbol `core.c`, A's reserved `AZH_E_SAVESTATE`, A's `AZH_INPUT_INTS`, A's `azh_pure.h` | C's crop work, D's `dlsym` edit, header lines | taken |
| Raw shots in C2 beside A's readback, one readback per frame | finding the gap in D3 | taken |
| `fields[]` as the only layout source, plus `const.*` rows for every enum and limit (review 2 N7) | hand-checked constants in `_abi.py`; a stale code found at import, not in a test | taken (C1 +0.05 h, saves more later) |
| One X-macro list generating the header, `fields[]` and `_abi.py` (review 2 section 6) | the same drift, by generation | declined: heavy preprocessor use against C rule 8, and the `const.*` rows already catch every drift at import |
| B's PNG decoder (`read_png_rgba`) for C and D | a second decoder | taken |
| `copyfile(3)` with `COPYFILE_CLONE` per file, inside one `fts` walk | the copy loop; near-constant SD copies on APFS | taken |
| Worktrees link `dl/*` children from MAIN instead of `cp -R` (Phase 1's lesson: `.gitignore`'s `dl/` matches the real folder, not a symlink named `dl`); `vendor/` is copied (its pattern does not match a symlink) | minutes and disk per worktree | taken |
| Foreground gate parts under 10 minutes, or one Monitor wait on an rc file (S9) | an idle or lost builder | taken |
| The review's numpy touch script as the oracle | `checks_c.touch_expected` | declined: it is not in the repo; the stdlib `struct` version is about 15 lines and needs no numpy under `-I` |
| A fake-worker round-trip timing in D1 (`test_client.py` prints the mean `ok` round trip and `screens()`-sized copy time) | finding a slow parent/worker design before the emulator | taken (printed, no bound) |
| Instance B starts with A's `sys/` minus the SD folder (the shader cache comes along, as in Gen3D's reused folders) | `t_state`'s fixed cost; a first-try ratio pass | taken |
| App identity in the meta now (S3) | a later format change | taken |
| Searching for a cheaper drain on the stock core | nothing: none exists | not attempted (review 2 section 6) |
| Dropping `azhost --save` | a few lines | declined: two lines on C1's routing, and a command-line state for Gen3D |
| Running C's scenarios once, not again through Python | D3 machine time | declined: PLAN's Phase D gate asks for them; (a) runs once in D |

## 10. Changes from review 2

| Finding | Outcome |
|---|---|
| X1 status 14 is every exception | done: `msg.c` reads the full text it is handed; a 14 with `Exception Type: Break` is `AZH_ACT_BREAK`, any other 14 is `AZH_ACT_ERROR` (counted on the stock core); `messages.txt` gets a synthetic `Undefined Instruction` 14 and a `Break` 14 whose `Exception Type:` line sits past byte 200; fact row, risk 8, USING.md (phase-c 2, 3.5, 7; phase-d 9) |
| S1 planted red cannot redden a2 | done: offsets in host frames, `o_rel = v + c_min - p`, never negative, all in {m, m + 1} with m at most 2, plus the 90 % rule; expected sets named (buttons and ZL/ZR {0, 1}, touch {1, 2}) with a `NOTE` if m differs; a +2 shift gives negative offsets and fails; c_min from eight extra one-frame batches; a1's window is the planned frame plus or minus one line (phase-c 8) |
| S2 d3 exact c | done: c_min measured over many batch ends; d3 accepts c_min or c_min + 1; e1 and f3 use c_min; "exact" dropped from the SD row (section 6; phase-c 8) |
| S3 `.3dsx` program id 0 | done: `app_sha256=` in the meta (CommonCrypto in `state.c`), refused before any frame unless `LAZ_STATE_ANY_APP=1`; USING.md; P4 for Guy (section 5; phase-d 3) |
| S4 departures trip "PLAN wins" | done: section 5's list, a line in each brief; `host_paths` skips with a reason unless `LAZ_REQUIRE_EMULATOR=1`; the gate sets it and asks 0 skipped (phase-d 1, 5) |
| S5 guest text through `vsnprintf` | sent to Phase 1's as-built fix list (the coordinator's decision); Phase 2 relies on the literal write (A8); the observer `strstr`s the line as given (phase-c 4) |
| S6 who runs the first-frame check | done: `azh__run_one_frame` includes A's first-frame boot check, marks it done and returns `AZH_E_BOOT` on a NULL frame; D's 3.4 cites it (phase-c 3.6, 9; phase-d 3.4) |
| S7 SIGSTOP lower bound | done: measured from the `os.kill`, `timeout - 0.2 <= delay <= timeout + 3`; the fake `hang` mode 0.8 to 4 s (phase-d 7, 8) |
| S8 multi-line messages | done: `messages.txt` decodes `\n` and `\\`; C3 writes the real texts escaped (phase-c 7, 9) |
| S9 builders cannot be woken | done: rc file from a `trap`, `run_in_background` plus a bounded Monitor wait, waiters stopped before hand-back; else foreground parts under 10 minutes (section 2; phase-c 9, 10; phase-d 6, 10) |
| S10 the core build | done: C3's gate and D3's slow tests wait for `MAIN/build-core/build.exit` (or no live build), or run under it by the main loop's choice with `FAIL slow` reruns (section 2; phase-c 9; phase-d 6) |
| N1 debug text on stock | done: still refused, with the exactness reason (P5); on our core `azh_run` checks `citra_instant_debug_log` is `enabled` in the option store, else `AZH_E_ARG` naming the key (phase-c 2, 3.4; phase-d 9) |
| N2 "never returns" | done: "the stock core is not given the chance: the handler exits" (section 7; phase-c 2, 3.4) |
| N3 cursor rests on a wrap | done: :117 cited, the wrap stated (section 7; phase-c 2) |
| N4 save order | done: unlink `<path>.meta` first; `fsync` the meta by path after its rename (phase-d 3.2) |
| N5 log after run 1 | done: `test_api.py` reads the log after run 1, before the load (phase-d 8) |
| N6 paths | done: `Path(__file__).resolve().parents[2]`; every path the parent sends is absolute (phase-d 4.1, 4.2) |
| N7 layout size first, const rows | done: `check_layout` compares `size_layout` with `ctypes.sizeof(Layout)` first; `const.<NAME>` rows (phase-c 3.2; phase-d 4.1) |
| N8 deaths outside `run` | done: a death during `start` before the map holds its magic gives `HostCrashed` with the log tail and no message; an exit 10 during another op closes the Emulator and raises `HostError("the guest exited during <op>")` (phase-d 4.4) |
| N9 first run's shader compiles | done: `boot_timeout` applies until the heartbeat first moves after `start` (phase-d 4.4) |
| N10 `t_core_start` | done: instance A's `Emulator(...)` wall; the fixed-cost ratio printed; a plain-ratio-only fail goes to Guy (risk 3; phase-d 8) |
| N11 NAND and RomFS reopen | done: one USING.md line, and one more reason for S3 (phase-d 9) |
| N12 input-callback install | done: `api.c` passes run.c's two callbacks through A's core table at the end of `azh_open` (phase-c 4) |
| N13 RAW copy location | done: `rawcopy.c` (pure) called from run.c and api.c beside the readback; `frame.c` dropped from C's list (section 3; phase-c 5) |
| N14 async OpenFile/SetSize/Close | done: fact in the SD row and phase-d 2 (the reason the restore drains first) |
| N15 citation drift | done: framebuffer_layout.cpp:159; section names instead of phase-a line numbers (sections 6, 7) |
| Phase 1 cross-check items 3, 4, 8, 9, 11 | done: no A6 line in C1; readback in run.c; symlinked `dl/*`; `test_version.c` stays A's; debug stops match `ready f=` (sections 3, 6, 9; phase-c 8, 9) |
| Phase 1 revision 2 lessons (item 200) | done: `-P` path insert (B12); F2 reads MAIN's `build-core/`, which builders only read (section 2); debug text on stock (P5); the 32-byte record (B13); the granted asks' fallbacks dropped (section 6) |
| Step A as built | done: `azh_stats_t`, `azh_pure.h`, `azh_crop_rects` plus the strided PNG writer, the as-built sizes, no `create_instance`, `MVK_CONFIG_LOG_LEVEL` (A2, A9, A10, A12, A17, A19, A20) |

## 11. Changes from review 1 (revision 1, kept for the record)

X1 raw shots: C2's. X2 waiting builders: end-the-run checkpoints. S1 jitter: o / o + 1 (now P1's sets). S2 a1 per
bit. S3 the restore drain is a serialize: a 0 is an error, timed. S4 and S5 B6 and B5 resolved. S6 c3 from the batch
start. S7 per-call `timeout=`. S8 the exiting frame counts (`frame_total + 1`). S9 the first `retro_run` (now A4).
S10 the debug observer's early return (now moot: the line is written literally, A8). S11 worktree names. S12 no item
files. S13 `setuptools>=77`. S14 `fields[]` only. N1-N3, N5-N9 done. N4 (a separate stop code 0) declined: the map's
stop code is read only after a worker death, where 0 means "no stop recorded"; changing A's enum costs more than it
gives.
