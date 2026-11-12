# Phase 2 plan, review 2 (opus)

Reviewed: `docs/plans/phase-2.md`, `phase-c.md`, `phase-d.md` at revision 1 (commit c54a7dd; unchanged in the
working tree). Azahar source: `SRC` = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`. Written as I go
(2026-11-12): own findings first (section 1), then the check of review 1 (section 2), the Azahar fact check
(section 3), the brief-followability check (section 4), the Phase 1 cross-check (section 5), the hour-saving pass
(section 6), counts and verdict (section 7).

Grades: **X** blocker, **S** should fix, **N** nice.

## 1. Own findings

### X1. Status 14 is not only svcBreak: a guest crash becomes `guest_break`, and a repeating crash never becomes `guest_error`
- Where: phase-c.md:116-119 (stop reasons), :226-230 (the detector table, row 14), :396-399 (test_msg cases);
  phase-2.md:151 (fact row).
- Problem: `Core::LogException` sets status 14 (`ErrorCoreExceptionRaised`) for every guest exception, not just
  `svcBreak`: undefined instruction, unpredictable instruction, decode error, no-execute fault and `bkpt`
  (SRC core/arm/dynarmic/arm_dynarmic.cpp:144-159), unmapped reads and writes when the exception handler setting is
  on (core/memory.cpp:578-582), and `SVC::Break` (core/hle/kernel/svc.cpp:1165). The report that becomes the message
  details names the kind: `Exception Type: <Unmapped Read|Unmapped Write|Data Abort|Prefetch Abort|Undefined
  Instruction|Break|Unknown>` (core/arm/exception_handler.cpp:80-96, 125-142), after a `Thread:` and `Process:` line.
  The plan maps every 14 to `AZH_ACT_BREAK` (a flag, no count). Two results: (1) Gen3D's first real crash is reported
  as `stopped_by == "guest_break"`, which PLAN 2.2 and USING.md section 7 describe as a deliberate break the guest
  runs on from; (2) on the stock core, a guest thread that faults again on every `RunLoop` sends a 14 each time
  (`RunLoop` resets the status first, core.cpp:110), and since a 14 is never counted toward the 3-in-one-run rule,
  the detector never ends the run as `guest_error`: most likely every later batch stops after its first frame with
  `guest_break`, forever, and Gen3D's harness reads that as "the app hit its break point".
- Fix: in `msg.c`, a 14 whose text contains `Exception Type: Break` is `AZH_ACT_BREAK`; any other 14 is
  `AZH_ACT_ERROR` (counted on the stock core like any error). Add `messages.txt` rows for a synthetic `Undefined
  Instruction` 14 and a `Break` 14 whose `Exception Type:` line sits past byte 200 (the 256-byte `AZH_MSG_MAX` copy
  must not be what the detector reads: it reads the full text it is handed). State it in the fact row and in
  USING.md section 7 ("a crash is `guest_error`, a `svcBreak` or `bkpt` is `guest_break`"). Graded blocker because the
  action table is created at C1 and is what D's errors, USING.md and Gen3D build on, and gate (e) passes either way,
  so no later gate would catch it; the fix is about ten lines and two test rows.

### S1. The planted red of gate C cannot turn a2 red: offsets are only compared with each other
- Where: phase-c.md:36-37 (planted red "shows `FAIL a2.1`"), :421-422 (a2), :349 (`offsets_ok`).
- Problem: a2 passes when every change's offset is o or o + 1 for the measured mode o. Shifting every planned
  button frame by two in the expected table shifts every offset by the same -2, so the offsets are still all o' or
  o' + 1 and a2 still passes. a1 might fail, but only if its search window happens to be tight, which the brief does
  not fix. So the gate's own red check fails in a way the brief does not predict, and a sonnet builder will either
  stop or "fix" the check.
- Fix: anchor the offsets to the run's boot offset c (section 8 already measures it per batch): for a planned host
  frame p shown first in the line with guest count v, define `o_rel = v + c - p`. Require, per kind, every `o_rel`
  in a named small set that includes causality (`hid` and `irrst`: 0 or 1; touch: 1 or 2; the builder reports the
  sets measured, reviewers may tighten) plus the 90 % rule. A +2 shift of the plan then gives negative `o_rel`
  (the guest "saw" a change before it was applied) and a2 fails for a reason that can only be a bug. Keep a1's
  window at the planned frame plus or minus one line, stated.

### S2. Gate d3 asks the boot offset c to be exactly equal across batches; it can jitter by one
- Where: phase-c.md:440-441 (d3 "exact"), :122-123; phase-2.md:138 (SD row "C(c) and C(d) bounds are exact"),
  :199.
- Problem: SD writes being synchronous (the write path flushes through `backend->GetSize()`, whose `fseeko` empties
  the stdio buffer: SRC core/hle/service/fs/file.cpp:200-205, common/file_util.cpp:559-572) says the line is on the
  host when the guest's write returns; it says nothing about which `retro_run` the guest's write falls in. A
  `retro_run` returns when the `RunLoop` call in which the VBlank event fired ends (citra_libretro.cpp:287-306); the
  VBlank fires inside `Advance()` and the woken guest thread then runs only until that slice ends, which is the next
  timing event (core.cpp:276-300; `MAX_SLICE_LENGTH` = clock / 234, core/core_timing.h:184, the same period as the
  pad poll, whose phase drifts 3.91 polls per frame). When the next pad poll is close after the VBlank, the guest's
  `hidScanInput` + log write slip into the next `retro_run`. This is the same drift that makes the button offsets
  jitter (risk 1), so c can be c0 + 1 for some batches. With three batch ends in (d), a false red is plausible.
- Fix: d3 passes when every batch's c is c_min or c_min + 1 (values printed); keep d1 (host counter, exact) and d2
  (guest counter, exact) as they are. Drop "exact" from the SD fact row, and make e1's and f3's bounds use c_min.

### S3. The program-id check does not protect a `.3dsx` state: every homebrew has title id 0
- Where: phase-d.md:54-55, :118-119 ("another program or core build"), :355 (USING "the program id check");
  phase-2.md:165; PLAN.md 2.9 ("the state checks the program id").
- Problem: `LoadStateBuffer` compares the state's `program_id` with `title_id` (SRC core/savestate.cpp:296-299), and
  `title_id` comes from `app_loader->ReadProgramId` (core/core.cpp:515-519). The 3DSX loader does not implement
  `ReadProgramId` (no override in core/loader/3dsx.cpp; the base returns `ErrorNotImplemented`,
  core/loader/loader.h:219-221), so `title_id` stays 0 for every `.3dsx`, and a test-app state loads into Gen3D (or
  an older Gen3D build) without complaint, then misbehaves.
- Fix: the meta already stores `app=`; also store `app_size=` and `app_mtime=` (or a sha256 of the app file; it is a
  few MB, and `statemeta.c` stays pure if `state.c` computes it with CommonCrypto). State boot and `azh_load_state`
  refuse a mismatch with `AZH_E_SAVESTATE` "state is for another app (<meta app>)" before any frame; a
  `LAZ_STATE_ANY_APP=1` escape for the case where Gen3D rebuilt on purpose. USING.md says the core's program-id check
  is a no-op for homebrew. Tell Guy PLAN 2.9's sentence is wrong for `.3dsx`.

### S4. Two deliberate departures from PLAN.md trip the briefs' own "PLAN.md wins, stop and report" rule
- Where: phase-c.md:6-7 with :415-423; phase-d.md:6-8 with :248 (conftest "fails, never skips"); PLAN.md section 3,
  Phase C gate (a) "on exactly the planned frames, with a fixed, measured offset", Phase D "pytest integration tests
  on the test app, skipped with a reason when the core or the app is missing".
- Problem: a sonnet builder reads PLAN.md first, then a brief that loosens (a) to "o or o + 1" and turns PLAN's
  skip-with-reason into a hard failure. By the brief's first paragraph it must stop and report, so the step stalls.
  The second departure also loses a PLAN deliverable: a public user without the core gets failures, not skips.
- Fix: one "Approved departures from PLAN.md" list in phase-2.md (and a line in each brief): (a)'s jitter rule
  (review 1 S1, with the source reason) and anything else the review loops changed. For the tests, keep PLAN's
  behaviour: `host_paths` skips with a reason when a file is missing, unless `LAZ_REQUIRE_EMULATOR=1`, which turns
  the skip into a failure; the gate command sets it (`LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs
  tests/python`) and still asks 0 skipped.

### S5. The core hands the log callback a finished line as the format: guest text goes through `vsnprintf`
- Where: phase-c.md:312-316 (the armed observer "formats every line"); phase-2.md:116 (A8); phase-a.md:274 (A's
  callback `vsnprintf`s).
- Problem: Azahar's libretro log backend formats the whole entry itself and calls `callback(log_level,
  str.c_str())` with no arguments (SRC common/logging/backend.cpp:97-98). The guest's `svcOutputDebugString` text is
  logged verbatim (`LOG_DEBUG(Debug_Emulated, "{}", string)`, core/hle/kernel/svc.cpp:1190). So any `%` in a guest
  debug string (Gen3D's own logs, a `100%` progress line) or in a core line becomes a conversion specifier that
  reads arguments that do not exist: undefined behaviour inside the host, exactly on the path C arms for debug-text
  stops (and on every line when `LAZ_LOG_LEVEL=debug`).
- Fix: the callback never treats `fmt` as a format: it writes `fmt` as text (one bounded copy, the newline the
  core appends kept), and the observer `strstr`s `fmt` directly; a comment cites backend.cpp:97-98. That also
  removes the formatting cost S10 of review 1 worked around. It is A's code, so it is an ask for Phase 1 (section
  5); if Phase 1 keeps `vsnprintf`, C's log.c edit makes the change and reports it.

### S6. `azh__run_one_frame` and A's first-frame boot check: the two briefs disagree on who does it
- Where: phase-c.md:280-281 ("one retro_run with the message, heartbeat and counter handling of a batch frame; no
  shots, no stops"); phase-d.md:128-129 (the warm-up "runs A's first-frame boot check").
- Problem: A puts the NULL-first-frame check in the first batch frame (phase-a.md section 3). C's prototype comment
  does not include it; D assumes it. The two builders work in parallel from C1, so neither can see the other's
  choice; if neither does it, a state boot with a broken Vulkan setup unserializes into a dead renderer and the first
  error is a confusing one.
- Fix: C1's prototype comment says "including A's first-frame boot check, which it marks done, so the batch after it
  does not repeat it; returns `AZH_E_BOOT` on a NULL frame", and C2 implements that; D's 3.4 cites it.

### S7. The SIGSTOP check's lower bound of 3 s fails about half the time by construction
- Where: phase-d.md:308-310 ("`HostTimeout` within 3 to 6 s of the stop").
- Problem: the wait loop records the heartbeat's last change at the poll that saw it (every 0.1 s, 4.4). The worker
  is moving the heartbeat every few ms until the stop, so the last observed change is the last poll before the stop,
  0 to 0.1 s before it, and the timeout fires 3 s after that: 2.9 to 3.1 s after the stop. "3 to 6 s" is red about
  half the time on a quiet machine.
- Fix: measure from the `Timer`'s `os.kill` and require `timeout - 0.2 <= delay <= timeout + 3` (2.8 to 6 s),
  printed. Same care in `test_client.py`'s `hang` mode (1 s timeout: 0.8 to 4 s).

### S8. `messages.txt` is one line per message, but a real status-14 message is many lines
- Where: phase-c.md:396-397 (format), :477-478 (C3 copies the real `(14)` and `(16)` messages in).
- Problem: the 14 text is the exception report: `Thread:`, `Process:`, `Exception Type:`, registers and a stack
  dump, one item per line (SRC core/arm/exception_handler.cpp:107-140). It cannot be pasted as one line, and with
  X1's fix the `Exception Type:` line (the third) is the one that matters.
- Fix: in `messages.txt`, `\n` and `\\` are escapes that `test_msg.c` decodes (the same escaping as the azhost
  summary's `msg="..."`), and C3 writes the real messages escaped.

### S9. "Launch the gate in the background and be woken when it exits" is not something a sub-agent can do
- Where: phase-c.md:475-477 (C3), phase-d.md:274-276 (D3), phase-2.md:100-101.
- Problem: the same trap as review 1's X2, one level down. A sub-agent that ends its turn ends its run (and hands
  back); nothing wakes it when its background command exits. A sonnet builder told "be woken, never sleep-poll" will
  either hand back with the gate still running (the main loop then gets a report with no gate result), or write an
  `until ...; do sleep 5; done` waiter, which the global rule forbids and which leaves a listed waiter behind
  (memory "subagent-leftover-waiters").
- Fix: say exactly how a builder waits. The gate script writes its exit status to `runs/c-gate.rc` from a `trap`
  on every exit path (so the file always appears); the builder starts the gate with `run_in_background` and waits
  with the Monitor tool on "`runs/c-gate.rc` exists" (a bounded wait, 60 min), and stops its waiter before handing
  back. If Monitor is not in the builder's tool list, it runs the gate in the foreground in parts that each fit
  under the 10-minute Bash limit (`--only a`, `--only b,c`, `--only d,e,f`), and says so in the report. Same for D3's
  pytest (`-m "not slow"` plus one call per slow test file). The main loop's own background batches (section 4.6)
  keep the "be woken" wording.

### S10. Phase 1 now starts our core's 15-90 minute build in MAIN right after its merge, the moment Phase 2 starts
- Where: phase-2.md:30-46 (order: "Phase 1 merged on main" then C at once); phase-1.md:83-89 ("Merge and launch" 6:
  the build starts "while nobody times frames", phase-1.md:27-28).
- Problem: Phase 2's timed checks (c3's wall bound, the SIGSEGV 1 s, the SIGSTOP window, the 10 % state-boot ratio,
  the 200,000-frame run's minutes) would run beside a nice'd LTO build of Azahar using every core, which Phase 1
  itself says nobody should time frames beside. Phase 2's plan does not mention the build at all.
- Fix: one line in phase-2.md section 2: C1, C2, D1 and D2 may overlap the core build (no emulator, or only C2's two
  by-hand runs); C3's gate and D3 start only after `build-core/build.exit` exists in MAIN (the main loop's waiter
  already wakes on it), or the main loop records that it chose to run them under the build and treats a `FAIL slow`
  as a rerun after it. Book the wait as machine time.

## 1b. Nice

- **N1** (phase-c.md:312-316, phase-1.md:123-125) Phase 1 now says the debug-text stop on the stock core is "a speed
  choice, not a necessity". It is also exactness: without `instant_debug_log` the libretro backend runs on the
  `citra:Log` thread (SRC common/logging/backend.cpp:353-360, 452-466), so a hit arrives a frame or more after the
  guest wrote it, possibly after the batch disarmed the stop; no stock option sets `instant_debug_log`
  (phase-f1.md:116), and our core's profile does (phase-f1.md:214). Keep refusing it on the stock core and say why in
  phase-c section 2 and USING.md; on our core, `azh_run` may check that the option is `enabled` in the option store.
- **N2** (phase-c.md:210-211) "the stock core never returns from it" is not shown by the source: after 16 the
  shutdown signal is consumed (core.cpp:132-137, 149-150) and the VBlank event keeps firing (video_core/gpu.cpp:
  487-497), so the stock `retro_run` probably does return. Harmless (the stock path `_exit`s inside the handler),
  but say "the stock core is not given the chance: the handler exits".
- **N3** (phase-c.md:108-110, phase-2.md:162) The cursor stays hidden because `last_moved` starts at
  `time_point::min()` (mouse_tracker.cpp:117) and `now - last_moved` (:262-264) overflows and wraps into a huge
  unsigned count; it holds in practice and b3 checks it, but the fact row should cite :117 and say it rests on
  that wrap, so nobody "fixes" the profile's pointer timeout.
- **N4** (phase-d.md:81-83, 92-104) Save order: the new `<path>` is renamed in (step 3) while an older `<path>.meta`
  still says "complete", so a crash between steps 3 and 6 leaves a mixed state that loads. Unlink `<path>.meta`
  first (step 0); then "meta present = complete" holds. `statemeta.c` writes the meta through stdio with no `fsync`;
  `state.c` can `fsync` it by path after the rename.
- **N5** (phase-d.md:313-316) `test_api.py` save/load on one instance: the load replaces the SD folder with the
  snapshot, so run 1's log lines are gone after it. Say "read the log after run 1, before the load".
- **N6** (phase-d.md:146) "three parents up from this file": write `Path(__file__).resolve().parents[2]`, and make
  every path the parent sends the worker absolute (the worker's cwd is the workdir, phase-d.md:163, and A's
  defaults are relative to the cwd, phase-2.md A12).
- **N7** (phase-d.md:141) `check_layout` should first compare the layout's own `size_layout` with
  `ctypes.sizeof(Layout)`: if `AZH_MAX_FIELDS` or the struct differs, `fields[]` is read from the wrong place.
  Also cheap: `const.<NAME>` rows in `fields[]` (value in `offset`, size 0) for every enum and limit, so `_abi.py`'s
  copies of the error codes and stop reasons are checked too.
- **N8** (phase-d.md:195-200) The death mapping should cover a death during `start` before the map exists (no map
  message, `log_tail` only) and an exit 10 during an op other than `run` (`save_state`'s drain runs the guest):
  `HostCrashed`-like `GuestExited` text or a closed Emulator with a clear error.
- **N9** (phase-d.md:186-190) Boot runs no frame (A4), so the first frames' shader compiles land in the first `run`,
  under the 30 s heartbeat timeout, not `boot_timeout`. Use `boot_timeout` until the heartbeat first moves after
  `start`. Cheap, and it matters for Gen3D's cold first run.
- **N10** (phase-2.md:178, phase-d.md:318) `t_core_start` has two definitions ("a plain boot, closed at once" vs
  instance A's `Emulator(...)` wall). Pick instance A's (it costs no extra boot). And pre-state the decision if the
  ratio fails only on fixed cost (print `(t_state - t_core_start) / (t_boot - t_core_start)` too, and the main loop
  takes it to Guy), so the step does not stall.
- **N11** (phase-d.md:56-59) NAND files the guest holds open are reopened by path from the new instance's NAND,
  which is not snapshotted; harmless for the test app, worth one USING.md line for Gen3D. Also `%CITRA_ROM_FILE%`
  (common/file_util.cpp:1058-1060) reopens the app's own RomFS from the new path, which is one more reason for S3's
  app identity check.
- **N12** (phase-c.md:301-307) Input callbacks: say where they get installed. A's `azh_open` sets "the other
  callbacks" (phase-a section 3) inside A's files; C may not edit `core.c`. Write: run.c's two functions are passed
  through A's core table (`retro_set_input_state`, `retro_set_input_poll`, environment.cpp:287-288 just stores the
  pointer) at the end of `azh_open` in api.c, overriding A's stubs wherever they are.
- **N13** (phase-c.md:338, phase-a section 4 "frame.c") In Phase 1 revision 2 the readback runs in run.c (shot
  frames) and from `azh_shot`, not in frame.c. Put C's RAW copy beside the readback (run.c / api.c, both C's) and
  drop frame.c from C's list unless A's code puts it there.
- **N14** (phase-d.md:60-63) Add Phase 1's fact that the stock core runs OpenFile, SetSize and Close async
  (phase-b section 2: fs_user.cpp:70, file.cpp:288, 317): the fresh app's truncation of its log is an async
  `SetSize`, which is the concrete reason the restore drains before it replaces the SD. Without it a builder may
  "optimise" step 3 away.
- **N15** (phase-2.md section 6) Citation drift: the no-swap line is framebuffer_layout.cpp:159, not :160; and every
  `phase-a.md:<line>` in section 5 points at revision 1's numbering (revision 2 moved the header to about :188-236,
  the boot rule to :239-242, the map to :254-259, the file table to :282-301). Cite section names instead.

## 2. Review 1: is each finding fixed in the plan text?

Checked against the plan at c54a7dd (working tree identical).

| Review 1 | Fixed? | Notes |
|---|---|---|
| X1 RAW unowned | yes | C owns `AZH_FMT_RAW` (phase-c step C2); D's `screens()` uses it. See N13 for where the copy now sits. |
| X2 "report and wait" | yes, mostly | Checkpoints end the run and are resumed by SendMessage. Left over: "launch in the background and be woken" in steps C3 and D3 (this review's S9). |
| S1 input offset jitter | yes | The o / o+1 rule is written. But the gate cannot fail on causality (S1 here), and the rule is a PLAN.md departure (S4). |
| S2 a1 per bit | yes | |
| S3 restore pre-drain is a savestate | yes | phase-d states it and times it. |
| S4 B6 resolved | yes | |
| S5 B5 resolved | yes | |
| S6 c3 4.0 s fragile | yes | Bound now from the batch start. |
| S7 SIGSTOP timeout | yes | The new window's lower bound of 3 s is the new problem (S7 here). |
| S8 frame counts on exit | yes | |
| S9 first `retro_run` | partly | C1 and D1 still disagree who runs A's first-frame check (S6 here). |
| S10 debug observer cost | yes | Cost answered; the `vsnprintf` of guest text is not (S5 here), and exactness on the stock core is N1. |
| S11 worktree names | yes | |
| S12 builders and item files | yes | |
| S13 setuptools version | yes | |
| S14 layout field checks | yes | Add the `size_layout` check first (N7). |
| N1-N3, N5-N9 | yes | |
| N4 | declined with a reason | The reason holds. |
| N6 SIGSEGV crash reporter | n/a | Kept as a note; this review agrees ReportCrash works on a corpse. A host `sigaction` that `_exit(128+sig)`s is an option if the delay ever shows. |

Two review-1-era leftovers outside the table: the framebuffer_layout citation (:159, N15) and the two
`t_core_start` definitions (N10).

## 3. Azahar fact check

SRC = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`. Every claim in phase-2/c/d was checked.
Confirmed (the plan's citation is right or within a line):

- Button map and L3 per `retro_run`: citra_libretro/citra_libretro.cpp:150-193, :243.
- The `retro_run` loop and SET_MESSAGE on a bad status: citra_libretro.cpp:287-306; `DisplayMessage` with 600
  frames: citra_libretro/environment.cpp:169-174.
- `HasSubmittedFrame` resets its flag: citra_libretro/libretro_window.cpp:327-331. `SwapBuffers` returns early on
  `suppressPresentation`: :68-71. `PollEvents` calls `PollInput` once per VBlank: :194-225, :204.
- `RunLoop` resets the status: core/core.cpp:110; the shutdown signal is consumed: :132-150; status enum: core.h:92-113.
- `SVC::Break`: core/hle/kernel/svc.cpp:1148-1166; `OutputDebugString` is `LOG_DEBUG "{}"`: svc.cpp:1190.
- Status 14 is set by `LogException` for every exception type (core/arm/exception_handler.cpp:80-96, 99-142), and
  dynarmic maps its exceptions to UndefinedInstruction or Break (core/arm/dynarmic/arm_dynarmic.cpp:144-159): the
  basis of X1. Unmapped access reaches it only with `enable_exception_handler` (core/memory.cpp:578-582,
  common/settings.h:662, default false).
- HID pad update and its period (clock/234 ticks, so 3.91 polls per VBlank): core/hle/service/hid/hid.cpp:205-241,
  hid.h:342; touch read at hid.cpp:292-293; averaging hid.h:372. ir:rst: ir_rst.cpp:56-59, :92-93.
  `MAX_SLICE_LENGTH`: core/core_timing.h:184; `FRAME_TICKS = 4481136`: video_core/gpu.h:36. Basis of S2.
- Mouse tracker: citra_libretro/input/mouse_tracker.cpp:132-241; `last_moved = time_point::min()` at :117 (N3);
  `GetPressedPosition` gives the absolute position: mouse_tracker.h:53-56. `TouchPressed`:
  core/frontend/emu_window.cpp:155-192.
- Layout: no-swap at core/frontend/framebuffer_layout.cpp:159 (plan says :160); `DefaultFrameLayout` :57-60.
- `DrawCursor`: video_core/renderer_vulkan/renderer_vulkan.cpp:1065-1080. VBlank callback: video_core/gpu.cpp:487-497.
  `EndFrame` / `DoFrameLimiting`: video_core/renderer_base.cpp:43-48; frame limit 0: citra_libretro/core_settings.cpp:1133.
- Touch chain recomputed in numpy float32: gy = y-1 exactly at y = 63, 125, 126, 127; gx exact; the frame pixel
  exact; never (0, 0); all 8 pointer examples in phase-c are right.
- Savestates: citra_libretro.cpp:649-738 (drain :649-686, `retro_serialize_size` :690-707, `retro_unserialize`
  drains itself :720-738). `SaveStateBuffer` / `LoadStateBuffer`: core/savestate.cpp:245-310; program-id check
  :296-299 (a no-op for `.3dsx`, S3: core/loader/loader.h:219-221 and core.cpp:515-519); revision check :300-306.
- Open files: `IOFile` serialized by path and mode, reopened on load: common/file_util.h:80-104, 667-682;
  `SerializePath` including `%CITRA_ROM_FILE%`: common/file_util.cpp:1058-1065. SD files open `r+b`:
  core/file_sys/archive_sdmc.cpp:105.
- SD writes are synchronous when `!AllowsCachedReads` (core/hle/service/fs/file.cpp:200-217,
  file_sys/file_backend.h:92); `GetSize(FILE*)`'s `fseeko` flushes (common/file_util.cpp:559-572);
  `DiskFile::Write`: file_sys/disk_archive.cpp:30-40. `async_fs_operations` defaults true: settings.h:499.
  `HAVE_LIBRETRO_VFS` only on Android: citra_libretro/CMakeLists.txt:68-73.
- Log backend: `LibRetroBackend::Write` passes the formatted line as the format (common/logging/backend.cpp:69-99,
  S5); queued unless `instant_debug_log` (:345-361), thread at :452-466 (N1); libretro filter Debug:
  citra_libretro.cpp:59, 72-73.

Wrong or unsupported: the :160 citation (N15); "the stock core never returns" after 16 (N2); "c is exact" in the
SD fact row (S2); "the program-id check refuses a state from another app" for `.3dsx` (S3).

## 4. Can a sonnet builder follow the briefs without asking?

- **File ownership:** clear for C and D, with three holes. The input callbacks' install point, given that C may
  not edit `core.c` (N12); the RAW copy's file, now that Phase 1 moved the readback into run.c (N13); and who runs
  A's first-frame check (S6). Each is a one-line fix in the brief.
- **Gates that can fail:** a1, a3, b1-b3, c1-c3, d1, d2 can all fail on a real bug. a2 cannot fail on a
  causality bug (S1). d3 can fail with no bug, on the boot offset (S2). The SIGSTOP check fails about half the
  time with no bug (S7). The planted reds are good, apart from a2's.
- **Checkpoints that end the run:** C1 (ABI frozen) and D's checkpoints end the run with a report and are resumed
  by SendMessage. Good. Gaps: the "be woken" wording (S9), and the "PLAN.md wins, stop" rule colliding with the
  plan's own departures (S4). Without S4's list, a careful builder stops twice for no reason.
- **Long commands:** the C gate (200,000 frames plus the timed checks) and D3 are long. Give each an rc file
  written by a trap, plus a Monitor until-loop, or split them into foreground parts of under 10 minutes (S9).
  Each brief should say "stop every waiter you started before you hand back".
- **Machine sharing:** nothing says the timed gates must not run under the core build (S10).

## 5. Phase 2 against Phase 1 (working tree, revision 2)

1. **Line citations:** every `phase-a.md:<line>` in phase-2.md section 5 and the briefs points at revision 1's
   numbering (N15). Cite section names.
2. **Phase 2's asks of revision 2 are all done:** A4 (boot runs no frame), A18, B10 (no exit on START), B11
   (`read_png_rgba` raises ValueError), and `azh_abi_layout` / `azh_error` working before open. Phase 2's
   "if A does not" fallbacks can go.
3. **A6:** the sysdir is already in A's state struct, so C1 has nothing to add. Drop C1's A6 line.
4. **Readback location:** A's frame.c now only notes the frame; the readback runs in run.c and `azh_shot` (N13).
5. **`log.c` still `vsnprintf`s** the line the core passes as the format (S5). Phase 2 must either ask A to write
   it literally, or C must own a literal write path. Today neither plan does it.
6. **Debug-text stop on the stock core:** Phase 1 suggests it is "speed only" and could be allowed. It is also
   exactness (N1). Phase 2's refusal stands; Phase 1's note should change.
7. **`-I` implies `-P`:** Phase 1 notes the tests must put `tests/` on `sys.path`; Phase 2 already does. Consistent.
8. **Worktree seeding:** Phase 1 symlinks `dl/` and `vendor/` into worktrees; Phase 2 says `cp -R`. Use symlinks
   (hour saving below).
9. **`test_version.c`:** Phase 1 says "C may take over"; Phase 2 says neither builder touches it. Consistent in
   effect; one line in phase-c makes it explicit.
10. **Core build in MAIN right after the merge** overlaps Phase 2's timed gates (S10).
11. **B's debug lines also go to `svcOutputDebugString`** (phase-b revision 2), so every test-app log line is a
    debug-text candidate for C's stop. c-gate expectations that count debug hits must count those too, or match
    on a marker prefix only. Worth one line in phase-c's gate text.
12. **Markers sit at the corners only** in B revision 2. Phase 2's shot checks that sample pixels match that.
    No change needed.
13. **Gate A checks the heartbeat at offset 16 only.** C's `off_stop` / `off_msg` checks are C's own; no conflict.

## 6. Hour-saving pass

- **C1 (ABI freeze):** generate `_abi.py`'s constants and the `fields[]` table from one X-macro list in the header,
  so the layout check, the const rows (N7) and the Python mirror can never drift. Saves the hour of chasing a
  stale offset later.
- **C2 (input, touch, RAW):** the touch chain is already proven in numpy float32 (section 3). Paste that script
  into `tests/` as the expected-pointer oracle instead of writing a new one. RAW: copy beside A's readback (N13),
  with no second readback.
- **C3 (stops, exits, gate):** split the gate into parts of under 10 minutes, each in the foreground, so no
  waiter is needed (S9). The 200,000-frame run can run in the background beside the short parts, each with its
  own instance. Write the literal log path (S5); it also drops a `vsnprintf` per guest line.
- **D1 (Python layer):** measure the parent-to-worker round trip and `screens()` cost with a fake worker (no core)
  on day one, so a slow design shows before the emulator is involved. Use `multiprocessing.shared_memory`-free
  `mmap` of `host.map` directly (already the plan); keep to the stdlib.
- **D2 (savestates):** no cheaper drain exists on the stock core (the drain is the savestate, review 1 S3); do
  not spend time looking for one. Store the app identity in the meta now (S3); retrofitting costs more.
- **D3 (state boot):** seed the shader cache directory from instance A into the state-boot instance's workdir
  before timing. It cuts `t_state`'s fixed cost and makes the 10 % ratio more likely to pass on the first try
  (N10).
- **Worktrees:** symlink `dl/` and `vendor/` instead of `cp -R` (Phase 1's choice); it saves minutes and disk per
  lane.
- **Builds:** no core build in Phase 2. Build only with `make -j8` and the host tests; no `.cia` and no hardware.

## 7. Counts and verdict

- Blocker: **1** (X1). Should fix: **10** (S1-S10). Nice: **15** (N1-N15).

Top findings in plain words:
1. A guest crash and a deliberate guest break both show up as status 14, and the plan calls every 14 a break.
   A crashing game is then reported as a clean break, and never as an error (X1).
2. The input timing gate cannot catch the bug it exists for: it compares offsets only with each other, so a
   press that lands a frame early still passes (S1).
3. Two checks fail with no bug: the exact boot offset in d3 (S2) and the SIGSTOP window's 3 s floor (S7).
4. A savestate from one homebrew app loads into another without complaint, because every `.3dsx` has title id 0
   (S3).
5. Guest log text goes through `printf` formatting, so a `%` in it garbles or crashes the host (S5).
6. The briefs tell a sub-agent to wait in the background, which it cannot do, and to stop on any PLAN.md
   departure, while the plan contains two deliberate ones (S9, S4).
7. Phase 2's timed gates would run beside the core build that Phase 1 starts right after its merge (S10).

**Verdict:** ready to build after X1 and S1-S10 are fixed. Most are one to five lines of plan text; X1, S1 and
S3 need a short design paragraph each. The N items can be folded in the same pass or left to the builders. No
third full review loop is needed: a short main-loop check that each X/S fix is in the text is enough. The one
exception: if the X1 fix changes the C1 ABI (a new stop reason or error code), re-read C1's frozen header once
before C1 starts.
