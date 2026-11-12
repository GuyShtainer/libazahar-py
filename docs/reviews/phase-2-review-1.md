# Phase 2 plan, review 1 of 2 (laz-200)

Opus adversarial review, 2026-11-12, of `docs/plans/phase-2.md`, `phase-c.md` and `phase-d.md`. It checks them against
PLAN.md (final), the Phase 1 drafts (`phase-a.md`, `phase-b.md`: both the committed draft and the revision 1 now in the
working tree), and Azahar 2126.2's source on disk (SRC = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`).
Every source claim below was read in SRC. Nothing was built or run. The only computation was a numpy float32
recompute of the touch chain.

Counts: **2 blockers, 14 should fix, 9 nice.**

## Blockers

**X1. Nobody implements `AZH_FMT_RAW`, but D's `screens()` and `test_api.py` need it.**
- Problem: Phase A revision 1 now says RAW is "AZH_E_UNSUPPORTED until D" (phase-a.md:186) and "the pixel area stays
  zero until step D implements `AZH_FMT_RAW`" (:237-239). Phase-d section 5's file table has no `frame.c`, `api.c` or
  `hostmap.c` row, and section 4 calls `azh_shot(BOTH, RAW, None)` (phase-d.md:213). Phase C does not mention RAW.
- Result: the D builder hits `UnsupportedError` in D3 and is not allowed to edit the files that would fix it.
- Fix: give RAW to C2. It touches `host/frame.c` (an RGBA8 copy of the cropped top and bottom into the map at 4096,
  plus the `frame of the pixels` i64 at 1072) and the `azh_shot` branch, and adds a gate (d) check that reads the
  map's pixels after `--shot`. Add the rows to phase-c section 5. Update phase-a.md:186/:238 to "until C" and add
  the row to phase-2 section 5 as A18. Doing it in C keeps D on the Python side and lets C's gate test it in C.
- Docs: tell users that `screens()` returns views that change on the next shot. Either say so in USING.md or copy the
  pixels, and decide which now.

**X2. "Report to the main loop and wait" cannot be done by a subagent.**
- Problem: phase-c.md:429-430 says to report "C1 done" and wait, and phase-2.md:37 says D "stops, reports, waits".
  A subagent has only one way to report: end its run with SubagentHandback. It cannot wait in a loop for a commit.
  A sonnet builder told to wait will either end its run, or go on into C2 on top of uncommitted C1 files, or poll.
- Fix: write it as "C1: end your run. Your final report is the 'C1 done' report with the exact C1 path list. The
  main loop commits, then resumes you with SendMessage, saying 'C1 committed at <sha>, go on with C2'." Write the same
  for D after D2. In phase-2 section 2, add: the main loop writes each builder's agent id into the handoff at launch.
  If resuming fails (the id is lost or the context is gone), the fallback is a fresh sonnet with the plan, the
  earlier report and `git log step-c`.

## Should fix

**S1. Input offsets jitter by one frame. Decide the rule now (c a2, a3, b2).**
- Evidence: the HID pad update runs at `clock/234` (hid.h:342), which is 3.911 polls per VBlank, so its phase moves
  0.089 of a poll each frame. The record for frame N is applied before `retro_run` N. The guest's `hidScanInput` runs
  just after the VBlank that started `retro_run` N (phase-b main loop: `gspWaitForVBlank0` then `hidScanInput`).
- Result: whether a pad poll falls between "record applied" and "guest scans" changes from frame to frame. Most
  changes show at frame N+1, and a few at N. a2's "the same offset for every change" (and b2 and a3's "constant") can
  then fail once in about 40 changes, on a loaded machine more often, and that is a correct result.
- Fix: in a2, a3 and b2, accept offset o or o+1 per change. Print how many changes had each. Pass if one value
  covers at least 90 % and no other value appears. Run scenario (a) twice in the gate. If o+1 never shows up, the
  reviewers may tighten the check later; the builder never does.

**S2. a1 must be per bit.**
- `L|R|ZL|ZR` mixes kinds: L and R come through HID, ZL and ZR through ir:rst (ir_rst.cpp:56-59, which has its own
  update period, :144/:156). So one combo can split across two log lines.
- Fix: a1 checks each bit's own rise and fall, and expects the combo to land within one line of the same frame.

**S3. The restore pre-drain is a full savestate.**
- Evidence: phase-d 3.3 step 3 drains with a discarded `retro_serialize_size()`. That call drains and then runs a
  full `SaveStateBuffer`, a boost archive plus zstd over guest RAM (citra_libretro.cpp:647-726, savestate.cpp:244-310).
  It returns 0 when the drain times out after 5 s.
- Result: every state boot and every `load_state` pays for a second serialize, which may be over a second against
  the 10 % budget, and it holds a buffer the size of a state.
- Fix: (a) a result of 0 is `AZH_E_SAVESTATE` "drain timed out", not ignored. (b) Log the time of each restore step
  (meta, read, drain, SD swap, unserialize) to host.log, and have test_state print them, so a 10 % failure can be
  diagnosed. (c) Note for G: the lazpy core can export a drain-only entry point.

**S4. B6 is resolved. Update the text and the gate expectations.**
- phase-b revision 1 now makes `boot_frames` a busy CPU boot ("stands in for Gen3D's world build", xorshift spin
  until the vblank counter moves). So phase-2.md:127 and phase-d.md:304-305 should say "resolved by phase-b r1".
- The time ratio is still at risk, because `t_state` includes dlopen, Vulkan setup and the first frame's shader
  compile on a fresh `wd_b`. Fix: print `t_core_start` (an `Emulator` with no state, closed at once) next to
  `t_state`. The pass rule stays `t_state < 0.10 * t_boot`. The builder reports the times and does not tune the test.

**S5. B5 is resolved.** phase-b revision 1 (review X2): after `break`, per-frame lines go on from `f=121`. Drop
phase-c.md:410's "if Phase B's final app halts ..." clause and the conflict row phase-2.md:126. e3 is unconditional.

**S6. c3's 4.0 s wall bound is fragile.** `--frames 10000000 --wall-limit-ms 3000` starts with the first batch frame.
That frame may compile shaders on a fresh sysdir, and at load 86 one frame can take more than 1 s. Fix: write it as
`--frames 300,10000000 --wall-limit-ms 3000`, with the stop rules applying per batch (already true in phase-c:188).
c3 then reads the second batch: `wall` at most 3000 ms plus the longest frame of batch 1, printed.

**S7. The SIGSTOP test can time out for the wrong reason.** `Emulator(..., timeout=3)` sets 3 s for every call. A
first-frame stall of more than 3 s raises HostTimeout before the timer's SIGSTOP. The test then passes or fails by
chance. Fix: add a per-call `timeout=` to `run()`/`run_until()` (it is useful anyway). Construct the Emulator with
the default timeout, run `run(300)`, then `run(10_000_000, timeout=3)` with the timer measured from the kill.

**S8. Frame counts on a guest exit are off by one.** The status-16 SET_MESSAGE comes during `retro_run` (only site
during a run: citra_libretro.cpp:304). C's `_exit` path (phase-c.md:209) writes `frame_total` before the per-frame
update for that `retro_run`. So D's `frames = map frame_total - before` (phase-d.md:180) counts one frame short.
Fix: on the exit path, write `frame_total + 1` ("the frame that exited counts"). State the rule in both plans, and
have gate f check `frames` against the `exit f=` line.

**S9. Where does the first `retro_run` happen?** phase-a.md:120 handles the NULL first frame "in code", but does not
say whether `azh_boot` runs a `retro_run` itself. If it does, D's warm-up frame (phase-d 3.4) is the second, and the
rule "frame k = the k-th batch `retro_run`" and `frame_total` (phase-c:166, "made by batches") disagree with B's
boot offset. Fix: in A, say whether `azh_boot` runs no frame. Then D's warm-up frame counts in `frame_total` or not,
and the counting is one line in phase-2 section 5 (A4).

**S10. The debug-text observer costs CPU on every debug line.** The core logs `OutputDebugString` at LOG_DEBUG
(svc.cpp:1190) and does much other debug logging. Fix: format and match log lines only while a debug stop is armed.
Otherwise the callback returns at once on level.

**S11. Worktree names.** `../wt-c` and `../wt-d` land in the toolkit's shared `projects/` folder, where other
sessions' worktrees also live. Use `../libazahar-py-c` and `../libazahar-py-d` as Phase 1 does (phase-1.md), after
the `git worktree list` and case-insensitive name check that phase-2.md:78 already has.

**S12. Builders must not edit item files.** phase-2.md:70 and phase-d's file table (the `220-step-d` row) let them
write "Lessons and notes". Phase 1 revision S11 says "No item files: notes go in the report". The main loop owns the
status moves (CLAUDE.md). Fix: drop the rows and use the report's "Lessons and notes" block.

**S13. `setuptools>=68` is too old for `license = "GPL-3.0-or-later"`.** A plain SPDX string in `[project].license`
(PEP 639) needs setuptools 77 or later. Older versions reject the string under PEP 621. Fix: `requires =
["setuptools>=77"]`.

**S14. The added layout fields need check rules.** phase-c.md:152 appends five `off_*` fields to `azh_layout` that
duplicate `fields[]` rows (`map.frame_total` and the others), and :157 does not say what `check_layout` does with
`map.*` rows. Fix: drop the five `off_*` fields and keep `fields[]` as the single source. `_abi.py` checks every
`map.*` name and offset against `_map.py`'s constants and raises an ABI mismatch on any difference.

## Nice

- N1 Citations. The touch "no swap" is at framebuffer_layout.cpp:160 (`res{..., !upright}` inside
  `LargeFrameLayout`, called from `DefaultFrameLayout` :57-60). :290 is `HybridScreenLayout` (phase-c.md:80,
  phase-2.md:151). EndFrame is at renderer_vulkan.cpp:1183, not :1182 (phase-c.md:63). The pointer formula is at
  mouse_tracker.cpp:144-145 as well as :171-172.
- N2 A1 says 15 functions. Phase A's header has 14.
- N3 `--save` on the stock core: "Unsupported" exits 6, which is the IO code. Give it its own code or document it.
- N4 A map stop code 0 means both "running" and "stopped by frames". Make `frames` its own nonzero code.
- N5 phase-2's open question on status 16 is answered by phase-1 review Q4 (apt.c:371-431, ctru_exit.c:32-36,
  applet_manager.cpp:1173-1177). Close it.
- N6 SIGSEGV within 1 s: a `kill(SIGSEGV)` is a signal, not a Mach exception. dynarmic's EXC_BAD_ACCESS port
  (exception_handler_macos.cpp:92) does not see it. ReportCrash works on a corpse, so `waitpid` returns quickly. The
  risk is low, but print the measured delay.
- N7 Verified correct:
  - The touch chain and the 4 rows: float32 recompute, y-1 exactly at rows 63, 125, 126 and 127; all 8 pointer
    examples.
  - Circle 32767 → 154, 16384 → 77, -32767 → -154 (hid.cpp:204-241, roundf × 0x9A, averaging of 3).
  - ZL and ZR through ir:rst (libctru `hid.o` imports `irrst*`; ir_rst.cpp:56-59).
  - Joypad ids 12, 13 and 14 (citra_libretro.cpp:150-193).
  - Statuses 14, 16 and 17 (core.h:92-113; exception_handler.cpp:142; core.cpp:110-111, :144).
  - The serialize drain and quirks (citra_libretro.cpp:647-726); IOFile reopen by path (file_util.h:667-682).
  - The `-I -c` worker start (argv[1] fd, argv[2] package parent; a non-editable install would break the `_paths`
    default root, so say editable only).
  - SIGKILL then reap of a stopped worker.
- N8 Reuse `check_testapp.py`'s PNG decoder. B should expose `read_png_rgba()` behind a `__main__` guard instead of
  D writing a second one.
- N9 Assumption B10: the test app must not exit on START. phase-b r1 leaves only on `aptMainLoop()` false or the
  frame cap. Add it to phase-2 section 5 so a later B edit cannot add the usual examples' START exit; gate (a) presses
  START.

## Phase 1 interface mismatches (phase-2 section 5 against phase-a and phase-b revision 1)

| Row | State | Fix, and which plan changes |
|---|---|---|
| A1 | changed | `AZH_E_STATE` is now `AZH_E_ORDER`; `AZH_E_SAVESTATE` (-10) is reserved in A, so C does not add it; 14 functions. Fix phase-2 A1 and phase-c's header list |
| A3 | resolved | `AZH_INPUT_INTS 7`, n counts records. phase-2 cites it |
| A4 | open | where the first `retro_run` and the NULL-frame check happen (S9). A states it; phase-2 copies it |
| A6 | resolved | the state struct has the booted and is-lazpy flags |
| A8 | check | format is checked before the filter in A; C's PNG order must follow it |
| A9 | changed | `host/crop.c` is A's (pure), so drop C's move of it |
| A12 | resolved | the library reads `LAZ_MVK`; the worker only sets it |
| A14 | resolved | A loads all 25 `retro_*` symbols, so drop phase-d 3.5 and the `core.c` row |
| A17 | resolved | 32 option keys, validated at open time |
| A18 (new) | **blocker** | RAW has no owner (X1): give it to C2 |
| `azhost info` | removed in A | check that C and D do not call it (the gates use `azhost layout`) |
| item files | conflict | Phase 1 forbids builders to edit them (S12) |
| worktrees | conflict | `../libazahar-py-<x>` naming (S11) |
| B3 | changed | in 3D, `v` is `C3D_FrameCounter(0)` and restarts; C's gates use 2D only, so say so |
| B5 | resolved | the guest runs on after `break` (S5) |
| B6 | resolved | busy boot (S4); the ratio still includes core start |
| B10 (new) | add | no START exit (N9) |
| PNG decode | duplicate | B exposes the function (N8) |

## Q2: will a sonnet builder get stuck, and is the parallel plan worth it?

- Stuck points: X1 (RAW), X2 (waiting), S9 (frame counting), and S3's ignored 0 from the drain. With those fixed,
  phase-c and phase-d are concrete enough for sonnet. Their gates are headless, pass/fail, and use only the test app.
- C1 freeze, D waits, then resume: D1 and D2 (the Python package, worker, client, fakeworker, statemeta and pure
  tests) need only the frozen header. That saves about 1.1 h of elapsed time on the path Gen3D waits on. The cost is
  about 0.1-0.2 h of main-loop time (two commits, one merge, two resumes).
- Verdict: keep it, with X2's end-the-run mechanics. Running C then D one after the other is the fallback if the C1
  header changes after the freeze. Any header change after C1 is a stop for both builders.

## Gates on a loaded machine

Flake sources:
- S1: input offsets.
- S6: c3 timing.
- S7: SIGSTOP early timeout.
- S4: the time ratio.
- `run(200_000)` under the 30 s heartbeat: the heartbeat moves after every frame, so it is fine.

Rule for all of them: print the measured value, and give a "slow" result a separate `FAIL slow` line, as phase-b
does, so the builder reruns before reporting.

## Hour-saving list

1. RAW in C2 (X1): about 0.3 h less than finding it missing in D3 and re-planning.
2. C drops the crop move and D drops the `core.c` edit (both are now in A): about 0.2 h.
3. Drop the five duplicate `off_*` fields (S14): less code and fewer checks.
4. Reuse B's PNG decoder (N8): about 0.2 h.
5. `sdcopy`/`azh__copy_tree`: use `copyfile(3)` with `COPYFILE_CLONE` per file (an APFS clone) instead of 1 MiB
   chunk loops. It is less code, and each state save and boot copies in near-constant time.
6. c3 on the last batch (S6) and o/o+1 offsets (S1): fewer reruns of slow gates.
7. End-the-run checkpoints (X2): no idle builder, nothing lost.

## Verdict

**Not ready to build.** Fix X1 and X2, then S1-S14 (most are one line). S4, S5 and the A rows only update text to
match Phase 1 revision 1. Then go to review 2, after Phase 1's own second review fixes the interfaces this plan copies.
