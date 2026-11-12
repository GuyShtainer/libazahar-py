# Phase 2, control: the phase plan (item laz-200)

Opus phase plan, 2026-11-12, **revision 1** (after `docs/reviews/phase-2-review-1.md`), **draft for the second
opus review loop. Nothing is built from it until that loop passes.** Steps: C (laz-210, `docs/plans/phase-c.md`) and
D (laz-220, `docs/plans/phase-d.md`). Each brief is complete on its own for one sonnet builder. This file is the
index: order, checkpoints, file ownership, merge plan, hours, the interfaces taken from Phase 1, the checked facts,
and the changes from review 1.

Contract: `docs/PLAN.md` (final) sections 2.1-2.9, the grouping paragraph of section 3 and its Phase C and Phase D
paragraphs. This plan refines them; where a brief seems to disagree with PLAN.md on a goal, PLAN.md wins and the
builder stops and reports. Phase 1's revision 1 (commit 21a152c: `phase-1.md` with its "Interfaces for Phase 2",
`phase-a.md`, `phase-b.md`, `phase-f1.md`) is the other input; its review 2 is running, so section 5 lists what
Phase 1's revision 2 must still state.

Hours are agent wall time (PLAN.md's unit). Machine time (emulator test batches in the background) is not counted.

## 1. The two steps

| Step | Delivers | Gate (headless, this Mac, test app, stock core) | Hours |
|---|---|---|---|
| C, laz-210 | `azh_run` with input records, touch and circle pad; raw shots into the map (`AZH_FMT_RAW`); the SD and debug-text stop rules; stop reasons from one SET_MESSAGE detector; heartbeat, frame and vblank totals and the wall limit in the map; SD seeding; `azhost` flags; pure-C unit tests (`make test-host`); the frozen ABI header | `make test-host` passes; `python3 -I tests/gate_c.py` prints PASS for C(a)-(f) and the raw-shot check; C(g) is in the unit tests | 1.9 |
| D, laz-220 | `python/libazahar/` (Emulator, worker process, mapped file, typed errors, ctypes checked against `azh_abi_layout()`), `pyproject.toml`; `host/state.c`, `host/statemeta.c`: savestates, the SD snapshot and state boot; pytest; `docs/USING.md` with the Gen3D mapping | `python3 -m pytest -q tests/python` all pass, 0 skipped: C's checks through Python, SIGSEGV gives `HostCrashed` within 1 s, SIGSTOP gives `HostTimeout` and no process, 200,000 frames not a hang, state boot same screen and log fields at under 10 % of the boot's wall time; a scratch venv `pip install -e .` imports | 2.0 |

Phase total: **3.9 h** of step work plus about 0.5 h for the two review loops (PLAN.md section 3's grouping
paragraph) = **about 4.4 h**, against PLAN.md's 2.0 + 2.25 + 0.5 = 4.75 h. The checkpoint choreography (two commits,
one merge, two resumes) is main-loop time, about 0.15 h, booked to the main loop.

## 2. Order, checkpoints and the parallel split

```
Phase 1 merged on main (A and B; F1 not needed)
  |
  C builder (sonnet, ../libazahar-py-c, branch step-c)
  |  C1: frozen header + pure modules + unit tests + D's stubs; ENDS ITS RUN with the "C1 done" report
  |     main loop commits C1 on step-c, creates ../libazahar-py-d (branch step-d) at the C1 commit
  |     main loop resumes C (SendMessage "C1 committed at <sha>, go on with C2")
  |     and launches the D builder (sonnet) with phase-d.md
  |  C2: run loop, inputs, stops, raw shots           D1: Python package, worker, errors, pure tests
  |  C3: azhost flags, seeding, gate_c.py              D2: state.c, statemeta.c, unit tests
  |  gate C in the background                         D ENDS ITS RUN with the "D1+D2 done" report
  v
  opus as-built review of C; fixes; main loop commits and merges step-c into main
                                                      main loop: git merge main in ../libazahar-py-d
                                                      main loop resumes D (SendMessage "main merged at <sha>,
                                                      go on with D3"): integration pytest + docs/USING.md
                                                      opus as-built review of D; main loop merges step-d
```

- **A builder never waits.** A subagent can report only by ending its run, so each checkpoint is the end of a run:
  C after C1, D after D2. The main loop commits, then resumes the same agent with SendMessage, so its context is kept.
  At each launch the main loop writes the builder's agent id into the handoff. If a resume fails (the id is lost or
  the context gone), the fallback is a fresh sonnet given the brief, the earlier report and `git log step-c` (or
  `step-d`); the reports are written to make that possible (each lists its exact paths and its measured values).
- **D starts from C's frozen header** (PLAN.md section 3): the freeze is checkpoint C1, which also creates the stub
  files D owns (`host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c`) and real or stub versions of the
  run.c functions D links against, so D's code builds from the C1 commit and the two builders never edit the same
  file. After C1 nobody edits `azhost.h` or `azh_internal.h`; a needed change stops both builders and goes to the
  main loop (then C and D run one after the other, the fallback order).
- Only C's builder runs the emulator during the parallel window (D1 and D2 are unit tests only). D3 runs after C is
  merged, one instance at a time.
- Why parallel (review 1, Q2): D1 and D2 need only the frozen header, which saves about 1.1 h of elapsed time on the
  path Gen3D waits on, for about 0.15 h of main-loop time.

## 3. File ownership (who creates or edits what)

Phase 1's A creates the host files; Phase 2 edits named functions in them. Each file has one owner at a time.

| File | Owner in Phase 2 | What changes |
|---|---|---|
| `host/azhost.h`, `host/azh_internal.h` | C (frozen at C1) | phase-c.md section 3; nobody edits them after C1 |
| `host/input.c`, `host/match.c`, `host/msg.c`, `host/sdcopy.c` | C | new pure modules |
| `host/run.c`, `host/env.c` (SET_MESSAGE case), `host/log.c` (the armed debug observer), `host/hostmap.c` (new fields, raw pixels), `host/frame.c` (the raw copy), `host/api.c` (`azh_run`, `azh_set_input`, `azh_shot`'s RAW branch, `azh_abi_layout`, the routing to `state.c`), `host/azhost_main.c` (run flags, `layout`), `Makefile` (`test-host`) | C | phase-c.md section 5 |
| `host/crop.c` | A's; C edits it only if A's signature does not fit, and then owns that change | |
| `tests/host/*.c` except `test_statemeta.c`, `tests/host/messages.txt`, `tests/testapp_log.py`, `tests/checks_c.py`, `tests/gate_c.py` | C | new |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | D (C1 creates stubs) | savestates and state boot |
| `python/libazahar/**`, `pyproject.toml`, `tests/python/**`, `docs/USING.md` | D | new |

Neither builder touches: `core/`, `testapp/`, `host/core.c` (A loads all 25 `retro_*` symbols), `tests/gate-a.sh`,
`tests/gate-b.sh`, `tests/check_testapp.py` (both import its PNG decoder; neither edits it), `tests/test_version.c`,
`.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff, **every item file**,
`prototype/`, `tools/`, `README.md`. Lines the main loop must add (`.gitignore`, runners) and the "Lessons and notes"
block for the item go in the builder's report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. `git worktree list` and a case-insensitive name check first, then `git worktree add -b step-c
   ../libazahar-py-c main`. Dispatch without isolation, cwd in the worktree. The builder seeds its ignored `dl/` and
   `vendor/` itself (phase-c.md step 0). Write the agent id into the handoff.
2. At "C1 done": commit exactly C1's paths on `step-c` (`git add <paths>`, `git diff --cached --stat`), then
   `git worktree add -b step-d ../libazahar-py-d <C1 commit>`, launch D with phase-d.md (id into the handoff), and
   resume C with "C1 committed at <sha>, go on with C2".
3. At "C done": opus as-built review of the step-c diff (phase-c.md section 14); fixes by the resumed C builder if
   any; commit; merge `step-c` into main; paste the report's "Lessons and notes" into item 210 and move it with its
   Evidence line.
4. At "D1+D2 done" (it may come before or after 3): commit D's paths on `step-d`. Once step 3 is done: in
   `../libazahar-py-d`, `git merge main` (disjoint files, no conflicts expected); resume D with "main merged at <sha>,
   go on with D3".
5. At "D done": opus as-built review (phase-d.md section 13), fixes, commit, merge `step-d` into main; item 220 as in
   3; then the phase item 200. Remove each worktree only after `git status --porcelain` is empty in it.
6. Background test batches: each builder launches its own gate in the background and is woken on exit (never
   `sleep`-polls). The full suite (gates A, B, C, D) runs once after the phase merges, as one background batch.

## 5. Interfaces taken from Phase 1 (revision 1, commit 21a152c)

Every row is read from Phase 1's revision 1; "R2" marks what Phase 1's revision 2 must still state or change.

| # | What Phase 2 relies on | Source | State |
|---|---|---|---|
| A1 | A's header: `AZH_E_*` -1 ARG, -2 `AZH_E_ORDER` (call order), -3 CORE, -4 BOOT, -5 VULKAN, -6 IO, -7 NOMEM, -8 UNSUPPORTED, -9 NEEDS_LAZPY_CORE, -10 `AZH_E_SAVESTATE` (reserved for D); `AZH_EXIT_*` 0, 2-6, 10, 11; `AZH_SCREEN_*`, `AZH_FMT_*`, `AZH_STOP_*` 0-6; `AZH_INPUT_INTS 7`; fixed-array structs; 14 functions | phase-a.md:174-222 | holds; C1 adds no error code |
| A2 | "Phase 2's C may extend it, then it freezes": the freeze is C1 | phase-a.md:174 | holds |
| A3 | `n` counts records of `AZH_INPUT_INTS` int32 | phase-a.md:191, 211 | holds |
| A4 | Frames 1-based in a batch; shot PNGs named by the absolute frame; PNGs written after `retro_run` returns; **`azh_boot` runs no `retro_run`, and the NULL-first-frame boot check happens in the first batch frame** | phase-a.md:250-251, 112-121 | **R2: A must state the bold part** (review 1 S9). Phase 2's rule either way: `frame_total` counts every `retro_run` since boot, batch or not; D's warm-up frame counts until the state's counters replace it |
| A5 | `host.map`: 0 magic, 8 version, 12 header size, 16 heartbeat (+1 after every `retro_run`), 24 stop code (0 running), 28 message length, 32 message [1024] (every SET_MESSAGE copied), 1056 dims, 1072 pixel frame, bytes 1080-4095 free for C, 4096 pixels, total 695,296 | phase-a.md:232-239 | holds |
| A6 | One internal state struct with frame counters, a booted flag and the is-our-core flag; file statics elsewhere | phase-a.md:263 | holds; C1 adds the sysdir to it if absent |
| A7 | `env.c`'s SET_MESSAGE capture and the boot-failure flag; the "(N)" parsing is C's | phase-a.md:267 | holds |
| A8 | `log.c`: one mutex around a formatted write; the level threshold; the core's variadic callback | phase-a.md:274 | holds; C makes the callback return before formatting when below the threshold and no debug stop is armed |
| A9 | `host/crop.c` is A's (pure) | phase-a.md:271; phase-1.md "Interfaces" | holds; C does not move it |
| A10 | `host/png.c` is pure (zlib) | phase-a.md:272 | holds |
| A11 | `azhost run <app> --sys --out --frames N [--shot ...] [--opt k=v]... [--profile] [--core] [--mvk] [--state]`; summary `frames=<n> wall=<s> fps=<f> shots=<k>`; `BootError:` etc. on stderr; no `info` subcommand | phase-a.md:241-256 | holds; C adds the `layout` subcommand |
| A12 | The library reads `LAZ_MVK`; `azhost --mvk` only sets it; default paths relative to the current directory | phase-a.md:228-231 | holds |
| A13 | The profile: 32 keys, right stick C-stick only, pointer timeout on, both touchscreen sources, resolution factor 1; `azh_set_option` validates at once after `azh_open` | phase-a.md section 2; phase-1.md "Options" | holds |
| A14 | `core.c` loads all 25 `retro_*` symbols, including the three serialize ones | phase-a.md:224-226 | holds; D adds no `dlsym` |
| A15 | `make testapp` delegates to `testapp/`; `build/testapp.3dsx` | phase-a.md:292 | holds |
| A16 | Our core's `retro_run` returns after the message on a non-Success status | phase-f1.md | holds (used only on our core) |
| A18 | `AZH_FMT_RAW` is in the header and the pixel area exists; A returns `AZH_E_UNSUPPORTED` for RAW | phase-a.md:186, 238-239 | **R2: change "until D" to "until C" at phase-a.md:186 and :238-239** (review 1 X1: raw shots are C2's) |
| A19 | A reads back the frame only on shot frames, and `azh_shot` can read back the current frame after a batch | phase-a.md:270 | C's RAW branch reuses that readback path |
| B1 | `build/testapp.3dsx`, built with `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH` | phase-b.md section 2 | holds |
| B2 | `<sys>/Azahar/sdmc/testapp/control.txt`, read before the first frame; keys `draw=2d|3d`, `break_at`, `exit_at`, `ready_at` (1 to 1,000,000), `boot_frames` (1 to 10,000) | phase-b.md:134-143 | holds |
| B3 | Log lines `start ...`; per frame `f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d`; events `ready f= v=`, `booted f= v= sum=`, `break f= v=`, `exit f= v=`; `f` counts from 1 including boot frames; `v` is meaningful only in 2D (3D: citro3d's counter) | phase-b.md:174-186 | holds; **Phase 2's gates use 2D only** |
| B4 | 2D loop: `hidScanInput`, record, log, events, draw, swap, `gspWaitForVBlank0()`: input sampled right after a VBlank | phase-b.md:193-199 | holds |
| B5 | After `break f=N`, `svcBreak`, then `f=N+1` goes on | phase-b.md:139, 46-47 | resolved; C(e) e3 is unconditional |
| B6 | Busy boot frames (bounded spin until the vblank counter moves, no VBlank wait), no per-frame lines, then `booted` | phase-b.md:145-152 | resolved; the time ratio still includes the core's start (D prints it) |
| B7 | `exit_at` returns from `main`; libctru's exit path reaches APT close and status 16 | phase-b.md section 2 (apt.c:371-431, ctru_exit.c:32-36, applet_manager.cpp:1173-1177) | resolved by Phase 1 review 1 Q4 |
| B8 | Markers table, background `#202020`, bottom screen is background plus markers only; `check_testapp.py markers --top --bottom --mode 2d` | phase-b.md:154-170 | holds |
| B9 | `ready_at` writes `ready f= v=` and keeps running; `svcOutputDebugString` carries the same text | phase-b.md:141 | holds |
| B10 | **The app never exits on START** (gate (a) presses START): it leaves only on `aptMainLoop()` false or the frame cap | phase-b.md:193 | holds; **R2: state it as a rule in phase-b section 3** so no later edit adds the examples' START exit |
| B11 | **`tests/check_testapp.py` exposes `read_png_rgba(path) -> (width, height, rgba_bytes)`** (filter-0 decoder, RGB expanded to RGBA), importable with the CLI behind `if __name__ == "__main__"` | review 1 N8; decided by the main loop | **R2: Phase 1 revision 2 exposes it with this name and return shape** |
| SD | SD file writes are synchronous on the emulator thread (file.cpp:198-217), so a line logged in frame F is on disk when `retro_run` F returns | phase-b.md section 2; phase-1.md PLAN notes | holds; C(c) and C(d) bounds are exact |

## 6. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (GIT-COMMIT 219d743a, GIT-TAG 2126.2), read
2026-11-12. "LIBCTRU" = `/opt/devkitpro/libctru/include/3ds/services/hid.h` on this Mac.

| Fact | Where |
|---|---|
| Joypad bindings: A=8, B=0, X=9, Y=1, Up=4, Down=5, Left=6, Right=7, L=10, R=11, Start=3, Select=2, ZL=12, ZR=13, Home=14 (L3) | SRC src/citra_libretro/citra_libretro.cpp:150-193 |
| L3 also toggles the screen swap | SRC citra_libretro.cpp:243-244 |
| `retro_run` loops `while (!HasSubmittedFrame())` over `RunLoop()`; non-Success sends "Azahar was unable to locate a 3DS system archive: ..." (status 10) or "Fatal Error encountered (N): ..."; it is the only `DisplayMessage` during a run | SRC citra_libretro.cpp:287-306; other callers :379-603 |
| `RunLoop` resets the status to Success first, so the guest runs on after svcBreak | SRC core/core.cpp:110-111 |
| `SVC::Break` logs at critical, then `Core::LogException`, which sets status 14 and returns | SRC core/hle/kernel/svc.cpp:1148-1166; core/arm/exception_handler.cpp:142 |
| Status numbers: 10 SystemFiles, 14 CoreExceptionRaised, 16 ShutdownRequested, 17 Unknown | SRC core/core.h:92-113; core.cpp:144, 150 |
| `DisplayMessage` is `RETRO_ENVIRONMENT_SET_MESSAGE` (6) with `struct retro_message {msg, frames}` | SRC src/citra_libretro/environment.cpp:169-174 |
| Buttons are read at every HID pad poll through `CheckInput`; the pad update runs at `clock / 234` (3.91 polls per VBlank) | SRC input/input_factory.cpp:29-31; core/hle/service/hid/hid.cpp:205-218; hid.h:342 |
| Circle pad: `(x / INT16_MAX, -y / INT16_MAX)`; HID `roundf(f * 0x9A)`, averaged over 3 polls | SRC input_factory.cpp:60-66; hid.cpp:227-241; hid.h:372 |
| ZL and ZR reach the guest through ir:rst (own update period); libctru's `hid.o` imports `irrstInit`, `irrstKeysHeld`, `APT_CheckNew3DS` | SRC core/hle/service/ir/ir_rst.cpp:56-59, 92-93, 144, 156; `arm-none-eabi-nm libctru.a` 2026-11-12 |
| Touch: `PollEvents` reads the pointer and calls `input_poll_cb` once per VBlank, from `EndFrame` at the end of the renderer's `SwapBuffers` | SRC citra_libretro/emu_window/libretro_window.cpp:194-224; video_core/renderer_base.cpp:43-48; renderer_vulkan/renderer_vulkan.cpp:1183; video_core/gpu.cpp:494 |
| Pointer to frame pixel: `static_cast<int>((p + 0x7fff) / (float)(0x7fff * 2) * bufferWidth)`; (0, 0) ignored; applied only if it differs from the last | SRC input/mouse_tracker.cpp:144-145, 171-189 |
| Frame pixel to touch: float division; no swap, because `DefaultFrameLayout` calls `LargeFrameLayout`, whose result has `is_rotated = !upright` = true | SRC core/frontend/emu_window.cpp:155-192; core/frontend/framebuffer_layout.cpp:57-60, 160 |
| HID: `static_cast<u16>(x * 320)`, `static_cast<u16>(y * 240)` | SRC hid.cpp:292-293 |
| float32 recompute: the pointer formula hits the exact frame pixel; guest x exact; guest y = y - 1 for exactly y = 63, 125, 126, 127 | this plan and review 1 N7 (numpy) |
| Cursor: drawn only if visible; never visible with the timeout on and the right stick on C-stick; crosshair 8 px each side | SRC mouse_tracker.cpp:191-238, 243-269; renderer_vulkan.cpp:1065-1080 |
| Savestate: `retro_serialize_size` drains while async work is pending (up to 5 s, presentation suppressed), returns 0 on timeout or error, then a full `SaveStateBuffer`; `retro_serialize` copies it; `retro_unserialize` drains, then `LoadStateBuffer` | SRC citra_libretro.cpp:647-738 |
| During the drain the window's `SwapBuffers` returns early but `PollEvents` still runs every VBlank | SRC libretro_window.cpp:68-71, 204 |
| `LoadStateBuffer` checks the program id and the build revision; zstd | SRC core/savestate.cpp:253, 297, 303 |
| Open guest files survive a state: `IOFile` keeps path (with `%CITRA_USER_SDMC%`), mode and position and reopens on load; SD files open `r+b` | SRC common/file_util.h:82-104, 667-682; file_util.cpp:1058-1065; file_sys/archive_sdmc.cpp:105 |
| libctru keys: A 0, B 1, SELECT 2, START 3, DRIGHT 4, DLEFT 5, DUP 6, DDOWN 7, R 8, L 9, X 10, Y 11, ZL 14, ZR 15, TOUCH 20, CSTICK 24-27, CPAD 28-31 | LIBCTRU:12-34 |
| macOS `copyfile(3)`: `COPYFILE_CLONE` (1<<24) clones on APFS and falls back to a copy | `$(xcrun --show-sdk-path)/usr/include/copyfile.h:113` |
| This Mac: python3 3.14.0; pytest 9.2.0 and numpy 2.5.0 only in the user site; setuptools not importable under `-I`; Pillow absent | `python3 -c` checks, 2026-11-12 |

## 7. Risks for this phase

1. **Input timing jitters by one frame.** The pad poll's phase drifts against the VBlank (3.91 polls per frame), so a
   change usually shows one frame after its record and sometimes on the same frame; touch is latched at the VBlank
   and lands one frame later again. Mitigation: per kind, every change at o or o + 1, the dominant one at least 90 %,
   counts printed; scenario (a) runs twice. Reviewers may tighten later; builders never do.
2. **The 10 % state-boot wall check** includes the core's own start (dlopen, Vulkan, the first frame's shaders on a
   fresh folder). Mitigation: the test prints `t_boot`, `t_core_start` (a plain boot, closed at once), `t_state` and
   each restore step's time from host.log; a fail is reported, not tuned away.
3. **The restore's drain is a full serialize** (`retro_serialize_size` is the only drain entry point). Mitigation:
   timed in host.log; a 0 is an error; Phase G's core may export a drain-only call.
4. **`-I` and the user-site pytest** on this Mac: the worker starts with an explicit package root (phase-d.md 4.2);
   USING.md says: editable install into a venv.
5. **Loaded-machine flakes** (c3 timing, SIGSTOP timing, the ratio): every check prints its measured value; a slow
   result is a separate `FAIL slow <id>` line, and the builder reruns once before reporting.
6. **macOS crash reports** for the SIGSEGV test: `kill(SIGSEGV)` is a signal, not a Mach exception; the test prints
   the measured kill-to-raise delay and the builder checks `~/Library/Logs/DiagnosticReports` once, deleting nothing.
7. **The 200,000-frame test** takes several minutes of machine time; it runs once per suite, marked `slow`.

## 8. Hour-saving pass (revision 1)

| Existing thing or cut | What it saves | Verdict |
|---|---|---|
| A's `crop.c`, A's 25-symbol `core.c`, A's reserved `AZH_E_SAVESTATE`, A's `AZH_INPUT_INTS` | C's crop move, D's `dlsym` edit, two header lines | taken (about 0.2 h) |
| Raw shots in C2 beside A's readback (X1) | finding the gap in D3 and re-planning | taken (about 0.3 h of rework avoided; C +0.1 h) |
| `fields[]` as the only layout source, no `off_*` duplicates (S14) | code and checks | taken |
| B's PNG decoder (`read_png_rgba`) for C and D (N8) | a second decoder | taken (about 0.1 h) |
| `copyfile(3)` with `COPYFILE_CLONE` per file, inside one `fts` walk | the 1 MiB copy loop; state saves and boots copy the SD in near-constant time on APFS | taken |
| SD writes synchronous (Phase 1 N5) | the "one frame behind" tolerance in C(c) and C(d) | taken: exact bounds |
| End-the-run checkpoints (X2) | no idle or polling builder | taken |
| Per-call `timeout=` on `run` (S7) | a flaky SIGSTOP test and its reruns | taken |
| `copyfile` `COPYFILE_RECURSIVE` for the whole tree | the `fts` walk too | declined: it copies symlinks as links, and the seed folder must refuse them; the walk is also needed by `clear_tree` |
| Dropping `azhost --save` | a few lines | declined: two lines on C1's routing, and it gives a command-line state for Gen3D |
| Running C's scenarios once, not again through Python | D3 machine time | declined: PLAN's Phase D gate asks for them; (a) runs once in D (twice only in C) |

## 9. Changes from review 1

| Finding | Outcome |
|---|---|
| X1 raw shots unowned | done: `AZH_FMT_RAW` is C2's (frame.c copy, map pixels and pixel frame, `azh_shot` branch, batch RAW shots), gate check d4 compares the map's pixels with the PNG of the same frame (phase-c 3.4, 5, 8); A18 asks Phase 1 R2 to say "until C"; `screens()` returns views that change at the next shot, said in its docstring and USING.md (phase-d 4.6, 9) |
| X2 waiting builders | done: C ends its run at C1, D at D2; resumed by SendMessage; agent ids in the handoff; fresh-sonnet fallback (section 2; phase-c 9; phase-d 6) |
| S1 offset jitter | done: o or o + 1 per change, dominant at least 90 %, counts printed, (a) run twice (phase-c 8) |
| S2 a1 per bit | done: each bit's own rise and fall; combos within one line (phase-c 8) |
| S3 restore drain | done: a 0 is `AZH_E_SAVESTATE` "drain timed out"; each restore step timed in host.log and printed by the test; note for G (phase-d 3.3, 8) |
| S4 B6 resolved | done: B6 marked resolved; `t_core_start` printed; the pass rule unchanged (section 5; phase-d 8) |
| S5 B5 resolved | done: e3 unconditional; the conflict row removed (section 5; phase-c 8) |
| S6 c3 bound | done: `--frames 300,10000000 --wall-limit-ms 3000`, read on batch 2, bound 3000 ms plus batch 1's longest frame (phase-c 8) |
| S7 SIGSTOP timeout | done: per-call `timeout=` on `run`/`run_until`; default for the Emulator, 3 s for the stopped call (phase-d 4.6, 8) |
| S8 exit frame count | done: the exit path writes `frame_total + 1` (the frame that exited counts); gate f3 checks it against the `exit f=` line (phase-c 3.5, 8; phase-d 4.4) |
| S9 first `retro_run` | done here (A4: Phase 2's counting rule either way), and listed for Phase 1 R2 |
| S10 debug observer cost | done: below-threshold lines return before formatting unless a debug stop is armed (phase-c 4) |
| S11 worktree names | done: `../libazahar-py-c` and `../libazahar-py-d` (sections 2, 4) |
| S12 item files | done: builders edit no item file; reports end with "Lessons and notes" (section 3; phase-c 12; phase-d 11) |
| S13 setuptools version | done: `setuptools>=77` (phase-d 5) |
| S14 layout fields | done: no `off_*` additions; `_abi.py` checks every `map.*` row against `_map.py`'s constants (phase-c 3.2; phase-d 4.1) |
| N1 citations | done: framebuffer_layout.cpp:57-60, 160; renderer_vulkan.cpp:1183; mouse_tracker.cpp:144-145 (section 6, phase-c 2) |
| N2 function count | done: 14 (A1) |
| N3 `--save` exit code | done: `AZH_EXIT_UNSUPPORTED = 8` added at C1 (phase-c 3.1) |
| N4 stop code 0 | declined: the map's stop code is read only after a worker death, where 0 means "no stop recorded"; batch results carry the reason; changing A's enum values costs more than it gives |
| N5 status 16 | done: B7 resolved with Phase 1's citations (section 5) |
| N6 SIGSEGV delay | done: printed (phase-d 8) |
| N7 editable install only | done: USING.md and `_paths.py` say the default root needs an editable install, else `LAZ_ROOT` (phase-d 4.1, 9) |
| N8 PNG decoder | done: B11; C and D import `read_png_rgba` (phase-c 5; phase-d 5) |
| N9 no START exit | done: B10 (section 5) |
| Interface table rows A1, A3, A4, A6, A8, A9, A12, A14, A17, A18, `info`, item files, worktrees, B3, B5, B6, B10, PNG decode | done: section 5 rewritten against revision 1; R2 asks listed there |
