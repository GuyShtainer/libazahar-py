# Phase 2, control: the phase plan (item laz-200)

Opus phase plan, 2026-11-12, **draft for Phase 2's two opus review loops. Nothing is built from it until both loops
pass.** Steps: C (laz-210, `docs/plans/phase-c.md`) and D (laz-220, `docs/plans/phase-d.md`); each brief is complete
on its own for one sonnet builder. This file is the index: order, file ownership, merge plan, hours, the interfaces
assumed from Phase 1 (to reconcile at review), and the facts checked for the plan.

Contract: `docs/PLAN.md` (final) sections 2.1-2.9, the grouping paragraph of section 3 and its Phase C and Phase D
paragraphs. This plan refines them; where a brief seems to disagree with PLAN.md on a goal, PLAN.md wins and the
builder stops and reports. Phase 1's plans (`docs/plans/phase-a.md` read 2026-11-12 17:25, not yet reviewed;
`phase-f1.md` skimmed; `phase-b.md` read later the same day; `phase-1.md` the index) are the other input.

Hours are agent wall time (PLAN.md's unit). Machine time (emulator test batches in the background) is not counted.

## 1. The two steps

| Step | Delivers | Gate (headless, this Mac, test app, stock core) | Hours |
|---|---|---|---|
| C, laz-210 | `azh_run` with input records, touch and circle pad; the SD and debug-text stop rules; stop reasons from one SET_MESSAGE detector; heartbeat and wall limit in the map; SD seeding; `azhost` flags; pure-C unit tests (`make test-host`); the frozen ABI header | `make test-host` passes; `python3 -I tests/gate_c.py` prints PASS for C(a)-(f); C(g) is in the unit tests | 1.85 |
| D, laz-220 | `python/libazahar/` (Emulator, worker process, mapped file, typed errors, ctypes checked against `azh_abi_layout()`), `pyproject.toml`; `host/state.c`: savestates, the SD snapshot and state boot; pytest; `docs/USING.md` with the Gen3D mapping | `python3 -m pytest -q tests/python` all pass, 0 skipped: C's checks through Python, SIGSEGV gives `HostCrashed` within 1 s, SIGSTOP gives `HostTimeout` and no process, 200,000 frames not a hang, state boot same screen and log fields at under 10 % of the boot's wall time; a scratch venv `pip install -e .` imports | 2.10 |

Phase total: **3.95 h** of step work plus about 0.5 h for this plan's two review loops (PLAN.md section 3's
grouping paragraph) = **about 4.45 h**, against PLAN.md's 2.0 + 2.25 + 0.5 = 4.75 h. Where the 0.3 h went: C does
not own `azh_stats` (Phase A already ships it), and D reuses C's check functions for its "C through Python" tests.

## 2. Order and the parallel split

```
Phase 1 merged on main (A and B at least; F1 not needed)
  |
  C builder (sonnet, worktree wt-c at main) ---- C1: frozen header + pure modules + unit tests (about 0.5 h)
  |                                                 | main loop commits C1 on branch step-c
  |                                                 v
  |                                       D builder (sonnet, worktree wt-d at the C1 commit)
  |   C2: run loop, inputs, stops, map           D1: Python package, worker, errors, pure-Python tests
  |   C3: azhost flags, seeding, gate_c.py       D2: host/state.c, statemeta.c, its unit tests
  |   gate C in the background                    -> stops, reports "D1+D2 done", waits
  v
  opus as-built review of C; main loop merges step-c into main
                                                  main loop merges main into step-d (in wt-d)
                                                  D builder resumed (SendMessage, same agent): D3 integration
                                                  pytest + docs/USING.md; gate D in the background
                                                  opus as-built review of D; main loop merges step-d
```

- **D may start from C's frozen header** (PLAN.md section 3): the freeze is checkpoint C1, which also creates the
  stub files D owns (`host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c`) so the two builders never edit
  the same file. After C1, C never edits D's files and D never edits C's. A header change after C1 needs a note to
  the main loop, which tells the other builder; none is planned.
- Only C's builder runs the emulator during the parallel window (D1 and D2 are unit tests only), so the machine never
  has more than one of our instances per agent. D3 runs after C merged, one instance at a time.
- If D1+D2 finish before C merges, the D builder reports and stops (it does not idle-poll); the main loop resumes the
  same agent with SendMessage after the merge, so its context is kept.

## 3. File ownership (who creates or edits what)

Phase 1 (A) creates the host files; Phase 2 edits named functions in them. Each file has one owner at a time.

| File | Owner in Phase 2 | What changes |
|---|---|---|
| `host/azhost.h` | C (frozen at C1) | extended per phase-c.md section 3; nobody edits it after C1 |
| `host/azh_internal.h` | C (frozen at C1) | the internal prototypes both steps use (phase-c.md section 3.6) |
| `host/input.c`, `host/match.c`, `host/msg.c`, `host/sdcopy.c` | C | new pure modules |
| `host/crop.c` | C | the crop function moved out of A's `frame.c` so the unit tests link it without Vulkan |
| `host/run.c`, `host/env.c` (SET_MESSAGE case only), `host/log.c` (one observer call), `host/hostmap.c` (new fields), `host/api.c` (`azh_run`, `azh_set_input`, `azh_abi_layout`), `host/azhost_main.c` (run flags, `layout`), `Makefile` (`test-host`) | C | phase-c.md section 5 |
| `tests/host/*.c` except `test_statemeta.c`, `tests/host/messages.txt`, `tests/testapp_log.py`, `tests/checks_c.py`, `tests/gate_c.py` | C | new |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | D (C1 creates stubs) | savestates and state boot |
| `host/core.c` (the three serialize symbols, only if A's table lacks them; C never edits `core.c`) | D | phase-d.md section 5. C1 already routes `azh_boot`'s state branch, `azh_save_state`, `azh_load_state` and `azhost --save` to `state.c`, so D edits no C file |
| `python/libazahar/**`, `pyproject.toml`, `tests/python/**`, `docs/USING.md` | D | new |
| item files 210 and 220 | the builder of that step, "Lessons and notes" only | |

Neither builder touches: `core/`, `testapp/`, `tests/gate-a.sh`, `tests/gate-b.sh`, `tests/check_testapp.py`,
`.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff, other items, `prototype/`,
`tools/`, `README.md`. Lines the main loop must add (`.gitignore`, runners) go in the builder's report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. Create `wt-c` with `git worktree add ../wt-c -b step-c main` (check `git worktree list` and the case-insensitive
   name first); seed its ignored `dl/` and `vendor/` by `cp -R` from the main checkout (`dl/azahar`, `dl/moltenvk`,
   not `dl/azahar-src`); copy `build/testapp.3dsx` in or let the builder run `make testapp` (devkitARM first in PATH).
   Launch C with phase-c.md.
2. When C reports C1: commit exactly C1's paths on `step-c` (`git add <paths>`, `git diff --cached --stat`), then
   `git worktree add ../wt-d -b step-d <C1 commit>`, seed as in 1, launch D with phase-d.md.
3. When C reports done: opus as-built review of the step-c diff (phase-c.md section 14), fixes by the C builder
   if any, commit, merge `step-c` into main (no fast-forward needed), move item 210 with its Evidence line.
4. In `wt-d`: `git merge main` (expect no conflicts: disjoint files). Resume the D builder for D3.
5. When D reports done: opus as-built review (phase-d.md section 13), fixes, commit, merge `step-d` into main, move
   item 220, then the phase item 200. Remove both worktrees only after `git status --porcelain` is empty in each.
6. Background test batches: each builder launches its own gate in the background and is woken on exit (never
   `sleep`-polls). The full suite (gates A, B, C, D) runs once after the phase merges, as one background batch.

## 5. Interfaces assumed from Phase 1 (reconcile at review)

From `docs/plans/phase-a.md` (read, unreviewed). If A's final plan changes any of these, the matching brief section
changes with it.

| # | Assumption | Used by | Source |
|---|---|---|---|
| A1 | `host/azhost.h` is A's section 3 header: `AZH_E_*` codes (-1 ARG, -2 STATE = call order, -3 CORE, -4 BOOT, -5 VULKAN, -6 IO, -7 NOMEM, -8 UNSUPPORTED, -9 NEEDS_LAZPY_CORE), `AZH_EXIT_*` (2 usage, 3 boot, 4 core, 5 vulkan, 6 io, 10 guest exited, 11 guest error), `AZH_SCREEN_*`, `AZH_FMT_*`, `AZH_STOP_*` 0-6, fixed-array structs `azh_shot_req`, `azh_batch`, `azh_result`, `azh_stats`, `azh_layout`, and the 15 functions | C, D | phase-a.md:148-193 |
| A2 | "C may extend it, D freezes it": this plan moves the freeze to C's checkpoint C1 so D can start in parallel (PLAN.md: "D may start from C's frozen header") | C, D | phase-a.md:148 |
| A3 | `azh_run(inputs, n, b, out)`: `n` is the number of 7-int32 records (not of ints); A returns `AZH_E_UNSUPPORTED` for `n > 0` | C | phase-a.md:182 (count unit not stated) |
| A4 | Frames: 1-based within a batch; "frame k is the frame the k-th `retro_run` delivered"; shot PNGs `<shot_dir>/shot_<absolute frame %06lld>_<top|bottom>.png`, written after `retro_run` returns | C, D | phase-a.md:164, 168, 211-212, 234 |
| A5 | `host.map`: 0 magic `LAZMAP1\0`, 8 version, 12 header size 4096, 16 u64 heartbeat (+1 after every `retro_run`), 24 i32 stop code, 28 i32 message length, 32 char[1024] last core message (A copies every SET_MESSAGE there), 1056 u32 x4 screen sizes, 1072 i64 pixel frame, 4096 pixels (top RGBA 400x240, then bottom 320x240); bytes 1080-4095 free for C | C, D | phase-a.md:195-200 |
| A6 | One internal state struct in `host/azh_internal.h` with the core proc table, frame counters, a booted flag and the is-our-core flag (`azh_stats.is_lazpy_core`); file statics elsewhere | C, D | phase-a.md:223 |
| A7 | `host/env.c` has a SET_MESSAGE handler that logs, copies to the map and sets the boot-failure flag during `context_reset`; the "(N)" parsing is C's | C | phase-a.md:69, 226 |
| A8 | `host/log.c` serializes the core's log lines through one mutex and one formatted write; C adds one observer call there | C, D | phase-a.md:232 |
| A9 | The crop to top and bottom lives in `host/frame.c` beside the video callback; C moves the pure crop function into `host/crop.c` (signature kept) so `make test-host` links without Vulkan | C | phase-a.md:229 |
| A10 | `host/png.c` is pure (zlib only) and linkable by the unit tests | C | phase-a.md:230 |
| A11 | `azhost run <app> --sys <dir> --out <dir> --frames N [--shot ...] [--opt k=v]... [--profile f] [--core p] [--mvk p] [--state f]`; `host.log` and `host.map` in `--out`; stdout summary `frames=<n> wall=<s> fps=<f> shots=<k>`; errors as `BootError:` etc. on stderr | C, D | phase-a.md:202-216 |
| A12 | Defaults: profile `host/options-default.txt` (applied by `azhost` with `azh_set_option`, not by the library), core `$LAZ_CORE` else `dl/azahar/azahar_libretro.dylib`, MoltenVK `$LAZ_MVK` else `dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib` (how the library receives the MoltenVK path is A's; D's worker sets `LAZ_MVK` in its environment and assumes the library reads it) | D | phase-a.md:208-210 |
| A13 | The profile sets `citra_analog_function=c_stick`, both touchscreen sources enabled, pointer timeout enabled, resolution factor 1 | C | phase-a.md:132-136 |
| A14 | `core.c` loads the `retro_*` table by explicit `dlsym`; if it lacks `retro_serialize_size`, `retro_serialize`, `retro_unserialize`, D adds those three lines | D | phase-a.md:225 |
| A15 | `make testapp` delegates to B's `testapp/` and produces `build/testapp.3dsx` | C, D | phase-a.md:247 |
| A16 | Our core's extra profile is F1's `core/options-lazpy.txt`; F1's patch makes `retro_run` return after the SET_MESSAGE on a non-Success status | C (lazpy branch) | phase-f1.md:164, 183 |
| A17 | Naming hazard, not a dependency: A's `AZH_E_STATE` means "call order", not savestate. C1 adds `AZH_E_SAVESTATE = -10` for savestate failures (Python `StateError`). Review may rename A's code to `AZH_E_ORDER`. | C, D | phase-a.md:154, 193 |

From Phase B (`docs/plans/phase-b.md`, read 2026-11-12 after its draft appeared, not yet reviewed). Every log and
control detail goes through one helper file (`tests/testapp_log.py`), so a format change touches one function.

| # | Assumption | Used by | Source |
|---|---|---|---|
| B1 | `build/testapp.3dsx` from `make testapp` (needs `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH`) | C, D | phase-b.md:146, 206 |
| B2 | `sdmc:/testapp/control.txt` = `<sys>/Azahar/sdmc/testapp/control.txt`, read once before the first frame; keys `draw=2d|3d`, `break_at=N`, `exit_at=N`, `ready_at=N` (1 to 1,000,000), `boot_frames=N` (1 to 10,000) | C, D | phase-b.md:99-109 |
| B3 | `log.txt` is truncated at start; lines: `start addr_global=... mode=...`; per frame `f=<loop frame from 1> v=<vblank callback count> s=<tick> t=<osGetTime ms> k=<hidKeysHeld %08lx> tx=<u> ty=<u> td=<0|1> cx=<d> cy=<d>`; events `ready f= v=`, `booted f= v=`, `break f= v=`, `exit f= v=`; each line one flushed `FSFILE_Write` | C, D | phase-b.md:125-131 |
| B4 | Main loop: `hidScanInput`, record, log line, draw, swap, `gspWaitForVBlank0()`; so input is sampled right after each VBlank | C | phase-b.md:138-140 |
| B5 | **Conflict to reconcile.** B's gate expects no per-frame line after `break` ("the guest stops"). Azahar's `SVC::Break` only logs and sets status 14, then the svc returns and the guest continues (SRC core/hle/kernel/svc.cpp:1148-1166; exception_handler.cpp:111-145). PLAN.md C(e) wants "the guest runs on". This plan asks B's app to keep looping after `svcBreak` (it will, unless B halts it on purpose); C(e) checks both the core (120 more frames, 120 VBlanks) and, if lines continue, the log | C | phase-b.md:37-38, 77, 104 |
| B6 | **Conflict to reconcile.** B's `boot_frames` draws only the background and waits for VBlank, so it is idle: 6000 idle frames run in a few seconds and D's "state boot under 10 % of the boot's wall time" cannot pass (the core's own start, about 1-2 s, is most of a state boot). This plan asks B to keep the guest CPU busy during boot frames (no VBlank wait inside them; spin until the VBlank counter moves), as Gen3D's world build is. If B keeps it idle, D's gate prints the ratio and reports | D | phase-b.md:107; PLAN.md Phase B "stands in for Gen3D's world build" |
| B7 | `exit_at` returns from `main` after `gfxExit()`; the status 16 path is B's assumption B2, checked by C(f) | C | phase-b.md:78-81 |
| B8 | Markers: 8x8 squares at B's table; background `#202020`; the frame counter is on the top screen only, so the bottom screen is flat `#202020` in a 17x17 box around (160, 120); `tests/check_testapp.py markers --top a.png --bottom b.png` checks split PNGs; it holds a stdlib PNG decoder | C, D | phase-b.md:111-123, 157 |
| B9 | `ready_at` writes `ready f= v=` and keeps running; `svcOutputDebugString` carries the same text (stock core logs it at debug level only) | C | phase-b.md:73-75, 106 |

## 6. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (GIT-COMMIT 219d743a, GIT-TAG 2126.2), read
2026-11-12. "LIBCTRU" = `/opt/devkitpro/libctru/include/3ds/services/hid.h` on this Mac.

| Fact | Where |
|---|---|
| Joypad bindings: A=8, B=0, X=9, Y=1, Up=4, Down=5, Left=6, Right=7, L=10, R=11, Start=3, Select=2, ZL=12, ZR=13, Home=14 (L3) | SRC src/citra_libretro/citra_libretro.cpp:150-193 |
| L3 also toggles the screen swap | SRC citra_libretro.cpp:243-244 |
| Circle pad is `axis:0`, C-stick `axis:1` unless the analog function is Touchscreen | SRC citra_libretro.cpp:196-203 |
| `retro_run` loops `while (!HasSubmittedFrame())` over `RunLoop()`; non-Success sends "Azahar was unable to locate a 3DS system archive: ..." (status 10) or "Fatal Error encountered (N): ..." via `DisplayMessage` | SRC citra_libretro.cpp:287-306 |
| `DisplayMessage` is plain `RETRO_ENVIRONMENT_SET_MESSAGE` (6) with `struct retro_message {msg, frames}` | SRC src/citra_libretro/environment.cpp:169-174; vendor/libretro.h:835 |
| `CheckInput` calls the frontend's `input_state_cb` directly; `PollInput` calls `input_poll_cb` | SRC environment.cpp:53-55, 219-221 |
| Buttons are read at every HID poll through `CheckInput` (`LibRetroButton::GetStatus`) | SRC src/citra_libretro/input/input_factory.cpp:29-31; core/hle/service/hid/hid.cpp:205-218 |
| Circle pad: `(float)CheckInput(..., ANALOG, 0, 0/1)`, returned as `(x / INT16_MAX, -y / INT16_MAX)` | SRC input_factory.cpp:60-66 |
| HID circle pad: `roundf(f * 0x9A)`, then averaged with the 2 previous polls (`CIRCLE_PAD_AVERAGING = 3`, integer division) | SRC hid.cpp:227-241; hid.h:372 |
| ZL and ZR reach the guest through ir:rst, not the HID pad | SRC core/hle/service/ir/ir_rst.cpp:56-59, 92-93 |
| Touch: the pointer is read and the touch state set in `PollEvents`, once per VBlank, from `RendererBase::EndFrame` | SRC src/citra_libretro/emu_window/libretro_window.cpp:194-224; video_core/renderer_base.cpp:43-48; video_core/renderer_vulkan/renderer_vulkan.cpp:1182 (`EndFrame()` at the end of `SwapBuffers`), video_core/gpu.cpp:494 (VBlank calls `SwapBuffers`) |
| Pointer to frame pixel: `static_cast<int>((p + 0x7fff) / (float)(0x7fff * 2) * bufferWidth)`; a point with p = (0, 0) is ignored; a new point applies only if it differs from the last one | SRC src/citra_libretro/input/mouse_tracker.cpp:164-189 |
| Frame pixel to touch: `(float)(X - left) / (right - left)` and `(float)(Y - top) / (bottom - top)`; no swap when `is_rotated` (default layout: `upright` false, so `is_rotated` true) | SRC core/frontend/emu_window.cpp:155-192; core/frontend/framebuffer_layout.cpp:290 |
| HID: `static_cast<u16>(x * 320)`, `static_cast<u16>(y * 240)` | SRC hid.cpp:292-293 |
| Recomputed here in float32 (Python `struct` round trips, 2026-11-12): p = floor((X + 0.5) * 65534 / 400) - 32767 (480 for Y) lands on the exact frame pixel for all X 40-359 and Y 240-479; guest x exact for all 320 columns; guest y = y - 1 for exactly y = 63, 125, 126, 127; examples x 0 -> -26132, 160 -> 81, 319 -> 26131; y 0 -> 68, 63 -> 8669, 239 -> 32698 | this plan; matches plan-check-3 section 6 |
| Cursor: drawn in the Vulkan render pass only if visible; with the timeout on, visible needs right-stick movement in the last 4 s, which needs the analog function not `c_stick`; crosshair half-length 240 / 30 = 8 px | SRC mouse_tracker.cpp:191-238, 260-269; renderer_vulkan.cpp:1065-1080 |
| Savestate: `retro_serialize_size` drains pending async ops (up to 5 s, presentation suppressed) then serializes and returns the size; `retro_serialize` copies it out; `retro_unserialize` drains, then `LoadStateBuffer` | SRC citra_libretro.cpp:665-738 |
| During the drain `SwapBuffers` returns early (no frame), but `PollEvents` still runs every VBlank, so the host's input-poll count measures k | SRC libretro_window.cpp:68-71, 204; renderer_base.cpp:48 |
| `LoadStateBuffer` checks the program id (:297) and the git revision (:303); `SaveStateBuffer` compresses with zstd (:253) | SRC core/savestate.cpp:281-310 |
| Open guest files survive a state: `IOFile` serializes its path, open mode and position and reopens on load; SD files are opened `r+b`; paths are stored with placeholders (`%CITRA_USER_SDMC%`), so a state reopens the new instance's SD files | SRC common/file_util.h:82-104, 667-682; common/file_util.cpp:1058-1065; core/file_sys/archive_sdmc.cpp:105 |
| libctru keys: A 0, B 1, SELECT 2, START 3, DRIGHT 4, DLEFT 5, DUP 6, DDOWN 7, R 8, L 9, X 10, Y 11, ZL 14, ZR 15, TOUCH 20, CSTICK 24-27, CPAD 28-31 | LIBCTRU:12-34 |
| `touchPosition {u16 px, py}`, `circlePosition {s16 dx, dy}` | LIBCTRU:44-55 |
| This Mac: python3 3.14.0; pytest 9.2.0 and numpy 2.5.0 installed, pytest only in the user site (`~/Library/Python/3.14`), so `python3 -I` cannot import pytest; setuptools not importable under `-I`; Pillow absent | `python3 -c` checks, 2026-11-12 |

## 7. Risks for this phase

1. **Input timing differs by kind.** Buttons are sampled at every HID poll inside the frame; touch is latched in
   `PollEvents` at the end of the VBlank, so touch probably lands one frame after buttons. Mitigation: C(a) and C(b)
   measure one offset per kind and require each to be constant; USING.md states them.
2. **The 10 % state-boot wall check** compares against the test app's slow boot. If B's slow-boot mode idles, 6000
   frames take seconds and the core's own start (dlopen, Vulkan, first frame, the drain, state load) can exceed 10 %.
   Mitigation: assumption B6 (busy boot); the gate prints both times and the ratio; a fail is reported, not tuned away.
3. **A state boot's warm-up frame touches the SD.** The fresh app's first frame may create or truncate its log
   before the state loads. Mitigation (phase-d.md section 3.3): drain, then replace the SD folder with the snapshot,
   then unserialize, all inside `azh_boot`; the gate compares the restored log bytes.
4. **Stock-core async I/O** can delay the SD text by one check interval. C(c) records the measured delay; it must be
   at most K frames plus one interval to pass, and the item notes the real number.
5. **`-I` and the user-site pytest** on this Mac: the worker cannot use `-m libazahar._worker` unless the package is
   installed into the interpreter, so D starts it with an explicit package root (phase-d.md section 4.2); USING.md
   still says: install into a venv.
6. **macOS crash reports** for a killed worker: not checked whether a SIGSEGV sent with `kill` makes ReportCrash
   write a report (no window either way: the worker is not a GUI app); D's builder checks
   `~/Library/Logs/DiagnosticReports` once after the test and reports, deleting nothing.
7. **The 200,000-frame test** takes several minutes of machine time at today's load (the light 2D app at a few
   hundred frames per second); it runs once per suite, in the background batch, marked `slow`.

## 8. What the reviews should check in this plan

That nothing contradicts PLAN.md 2.1-2.9 or the Phase C and D paragraphs; the refinements, each flagged in its brief:
the freeze moved to C1 (A2); `AZH_E_SAVESTATE` (A17); k measured by input polls with the test app's vblank count as
the cross-check (phase-d.md 2 and 3.2); the SD snapshot restore placed inside `azh_boot` between warm-up and unserialize,
and also on `load_state` (phase-d.md 3.3, 3.4); the worker start line (risk 5); a `HostError` class for host codes that
map to none of PLAN.md's six errors (phase-d.md 4.5); the ABI field table appended to `azh_layout` (phase-c.md 3.2); `azh_batch.sd_from_end` and
`AZH_EXIT_NEEDS_LAZPY = 7` (phase-c.md 3.1, 3.2); azhost's multi-batch `--frames` and `--print-last-line` for gate
C(d) (phase-c.md 6, 8); the state boot's pre-drain before the SD restore (phase-d.md 3.3, step 3).
