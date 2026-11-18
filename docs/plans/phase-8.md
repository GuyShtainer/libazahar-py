# Phase 8 plan: what this kind of tool must get right, and how we get there

Revision 0, 2026-11-18, opus planner (laz-802). Next: one opus review (laz-803), one revision (laz-804), then stop for
Guy's go. Plan only: nothing here has been built or run.

## 0. Reading this plan

Guy, 2026-11-18 20:08, verbatim: "research what must work on this kind of product, and plan (with single revision)
on how we get there". Inputs: `docs/research/p8/01`-`06` (06 is the inventory at v1.1.0), README, STATUS, USING,
HOST-API, `docs/hours.tsv`. Pointers read `R01 §2` (file 01, section 2); `R06` rows are the inventory.

**The short answer.** v1.1.0 already meets most of the bar. Of 16 Must rows, 11 are have and 5 are partial; none is
missing. The partial Musts are small: written determinism rules with a seed check, evidence left behind on a
failure, the input re-press rule, cleanup when the caller dies, and a CI recipe a user can copy. Most of phase 8 is
Should work, ordered by what our users ask for.

**Who the users are** (the "Who" column). **P**: our sibling projects, Gen3D and 3DP; they test their own homebrew
and run from a local checkout, so they get every fix when it merges to main, with no release needed. **A**: the
owner's AI agents, which drive emulators through Python and the shell; they kill runs, time out and retry, on a
shared PC. **T**: test and CI users (homebrew authors). **S**: script and bot users. **R**: RL users. T, S and R are
outside users; today they meet a clone-and-build install.

**Where things run.** The Mac is closed to 3DS work; no step depends on it (it is used only if Guy frees it).
- **PC**: the Windows PC, through the runner in `docs/map/runners.md` (phase 7 used `lane-pc`). Light-load rule: one
  job at a time, at most 2 emulator copies, free RAM at least 2 GB + 0.6 GB per copy.
- **CI**: `test-windows.yml` runs on every push (build, `make check`, host C tests, fast tests). `macos-live.yml` is
  manual and best effort: hosted macOS runners often never start. CI failures email Guy, so a push goes out only
  when CI is expected green, after the same steps pass on the PC.

**No core rebuild in phase 8.** A new core needs a macOS core build: the Mac, or a new macOS core-in-CI route (phase
7's Windows route took 4.9 h of CI rounds, hours.tsv W5). Every step below changes the host, Python, tests or docs
only. The three items deferred to the next core rebuild (HANDOFF) stay deferred.

## 1. The bar

What "working" means for a scriptable, headless emulator host. M = Must, S = Should, N = Nice. A Must needs support
from at least two research files, or one file plus a real user of ours. "Proof" says how it is shown and where.

| ID | Capability | Who | | Research | Proof (where) |
|---|---|---|---|---|---|
| M1 | Step N guest frames and get control back; a frame is one guest VBlank | all | M | R01 §2, R02 §2, R04 §2 | `test_c_checks` d (PC; CI macos-live) |
| M2 | Input is held state (buttons, touch, circle pad); latency and hold rules stated in frames, including the shortest release before a re-press | all | M | R01 §2, R02 §2, R04 §2 and #6 | `test_c_checks` a, b plus a new re-press test (PC) |
| M3 | Both screens as arrays with a stated lifetime; PNG shots of a chosen frame | T S R A P | M | R01 §2, R03 M4, R04 §2 | `test_c_checks` d, `test_map` (PC; CI fast) |
| M4 | Headless: no window, no audio device, never takes focus | all | M | R01 §2 and #12 | gate A's window check (existing) |
| M5 | Savestates from a script; the state covers the SD card; the compatibility rules are written | all | M | R01 §2, R02 §2 and #3, R04 §2 | `test_state*` (PC) |
| M6 | Many instances, one process each, the model documented; a machine-wide cap | T R P | M | R01 #4, R03 M8, R04 §2 | `test_pool_live` (PC, 2 copies) |
| M7 | A native crash becomes a typed error with the log tail; the caller survives | all | M | R05 M4, R04 #8 | `test_live_errors`, `test_client` (PC; CI fast) |
| M8 | Every wait has a deadline; on expiry the worker is killed and reaped | all | M | R05 M5, R03 M2 | `test_client` hang test (CI fast) |
| M9 | Guest memory read and write, bounded, between frames only | S R A P | M | R01 §2, R02 §2, R04 §2 | `test_memory_live` (PC) |
| M10 | Same inputs and same seed give the same frames; every source of randomness is listed; a test shows same seeds match and different seeds differ | T R P | M | R02 §2 and #1, R03 M3, R04 §2 and #4-5 | new `test_determinism` (PC) |
| M11 | A failure leaves evidence: the error names the log, the workdir and the newest shot | T A P | M | R03 M5, M6 | new tests in `test_client` (CI fast) and live (PC) |
| M12 | Host, Python layer and core versions are checked at start, with a clear refusal | all | M | R05 M8, R04 #13 | `test_abi` (CI fast) |
| M13 | A stable, versioned API with a written promise | all | M | R01 #15, R02 #6, R05 S5 | USING's promise; `docs_check` |
| M14 | A support matrix saying exactly what was tested | all | M | R05 M7 | README and STATUS; `docs_check` |
| M15 | Clean close: `close()` frees worker, slot and files; a caller that dies leaves no worker behind | all, A most | M | R04 §2 and #2, R05 S4 | `test_client`, `test_slots` (CI fast); parent death: probe A1 (PC) |
| M16 | A CI recipe a user can copy that runs the emulator on a hosted runner | T | M | R03 M7, R05 S1 | the recipe green 3 runs out of 3 (CI) |
| S1 | Image compare: exact, largest channel delta, count of differing pixels, a diff image | T P | S | R03 S1, S2, #1-3 | new `test_images` (CI fast) |
| S2 | A written pass/fail convention for test apps (an SD file line or a memory mailbox), with an example | T | S | R03 S5, #9 | example runs in `docs_check` (PC) |
| S3 | Exact input timing: poll-exact movies | T P | S | R02 §2 and #1, R01 §2 | offset test, 0 frames for every input kind (PC) |
| S4 | Audio captured to an array (not played) | P S | S | R01 §2 S; 3DP's sound lane (item 500) | new live test on a test app tone (PC) |
| S5 | The cost of a reset is known; states as bytes in memory | R A | S | R01 §2, R02 §2 S, R04 §2 | probe A2 numbers; a bytes test if built (PC) |
| S6 | No growth over many boots and state loads | R T A | S | R01 #11, R04 #1 (unconfirmed reports) | soak probe A2 (PC) |
| S7 | Many-instance GPU and memory use known per platform | R T | S | R04 #14 (a gap), R05 | probe A3 (PC); the Mac rows exist |
| S8 | A command line for agents and shells: `doctor`, and a run that prints JSON | A S | S | R05 N4, R04 §2 S | new `test_cli` (CI fast) and a live run (PC) |
| S9 | Install without a compiler (prebuilt host binaries; wheels later) | T S R | S | R05 M1, R01 #1, R04 N | `clone_check` with no compiler step (PC; CI) |
| S10 | A path with no GPU (a software Vulkan driver) | T | S | R03 M7, #5-6, R05 S1 | probe A5 (PC), then a CI job if it works |
| S11 | Troubleshooting keyed by the exact error text | all | S | R05 S6, M6 | `docs_check` |
| S12 | A private real-game check before each release (core regressions our test app misses) | P, us | S | R02 #8, R03 #11 | a private real-game check, run outside the repo (PC) |
| S13 | Linux | T R | S | R03 §4, R05 §4 | not planned here (Q4) |
| N1 | A Gymnasium-style wrapper as an example | R | N | R04 §2 (Must for RL users; we have none yet) | example run (PC) |
| N2-N7 | Recording live input into a movie; C-stick, HOME and power in the input record; breakpoints and register writes; Python `logging`; a batched vector step; an MCP server for agents | S T R A | N | R01, R02 §2, R04, R06 §6 | - |

Not promoted to Must, with the reason:
- Wheels (R05 M1 says Must): our own users run from a clone, and it is the costliest row; S9 starts with prebuilt
  host binaries. Bytes savestates (R01 says Must): file states serve every current user; S5 measures first. A
  Gymnasium API (R04 says Must for RL): we have no RL users today.
- Thin research, measured instead of built: parent-death cleanup is in M15, but R05 found no user report of orphaned
  emulator processes and R04's search was rate-limited (probe A1). GPU contention: R04 found no evidence either way
  (probe A3, within the PC's 2-copy rule).

## 2. The gap

Against the inventory (`R06`); pointers are its own `file:line`.

| ID | State | Pointer | What is missing, and the step that closes it |
|---|---|---|---|
| M1, M3-M7, M9, M12-M14 | have | USING `:34` (M1), `emulator.py:453-471` (M3), `STATUS.md:98` (M4), USING `:166-180` (M5), `:239-265` (M6), `:136-139` (M7), `:190-199` (M9), `HOST-API.md:18-21` (M12), USING `:8-13` (M13), `README.md:12-19` (M14) | - |
| M2 | partial | `docs/USING.md:74-83` | Offsets are measured with a one-frame tolerance; the shortest release before a re-press is not stated or tested (B4) |
| M8 | have, one limit | `docs/USING.md:36-39` | The Python layer has the heartbeat. `azhost` alone has `wall_limit`, which a hang inside one frame never reaches; say so and give the outer-timeout line (B6) |
| M10 | partial | `STATUS.md:69`, `docs/USING.md:273-276` | Exact repeats are gated in `gate_c`/`gate_f2` on our core. No list of the randomness sources, no seed-variation test in pytest, no helper that hashes a run (B1) |
| M11 | partial | `docs/USING.md:130-131`; `HostCrashed.log_tail` | `HostTimeout` and `GuestError` name no paths; nothing says which shot is the newest (B2) |
| M15 | partial | `_client.py:71-72`, `_slots.py:5`, `_worker.py:130` | A dead parent frees the slot (the kernel does). The worker sees the parent's EOF only between calls, so during a long batch it may run on. Unmeasured (A1, then B5 if needed) |
| M16 | partial | `macos-live.yml:7-9`, `STATUS.md:57-65` | macOS hosted runs work when a runner starts, with one timing failure (`test_state_boot`, a bound made for a quiet machine). No user-facing recipe. Windows hosted runners have no GPU (B7; S10) |
| S1 | missing | `python/libazahar/__init__.py:13-17` | B3 |
| S2 | partial | `docs/USING.md` sections 7 and 12a | The pieces exist (SD text stop, `run_until`, `emu.memory`); no written convention or example (B3) |
| S3 | partial | `STATUS.md:40` | Our core exports `lazpy_movie_play`; the host and Python do not call it (C3). No core rebuild needed |
| S4 | missing | `host/frame.c:74-80` (samples discarded) | Probe A4, then C2 |
| S5 | partial | `docs/USING.md:168` | File states only; `load_state` cost on a live instance unmeasured (A2, then C4 if needed) |
| S6 | unmeasured | - | A2 |
| S7 | partial | `docs/research/real-scene-v3.md` (Mac) | No Windows figures (A3; the figures stay private) |
| S8 | partial | `STATUS.md:80`, `:107` | `azhost` only, no `--help`; no Python command line (C1) |
| S9 | missing | `docs/USING.md:17-19`, `STATUS.md:106` | Windows users build the host in MSYS2 (D1) |
| S10 | missing | `README.md:18` | A5, then D2 |
| S11 | partial | `docs/USING.md:410-425` | Short; not keyed by error text (B6) |
| S12 | missing as a gate | `STATUS.md:102-103` | Each release gets a private real-game check, run outside the repo (C6, D4) |
| S13 | missing | `STATUS.md:38` | Q4 |
| N1-N7 | missing | `R06` §6 | N1 in D3; the rest are not scheduled |

## 3. Out of scope

- **Anything that needs console keys, Nintendo system files, NAND data or encrypted titles** (rule 1; the README's
  legal section): HOME menu and system applets, `.cia` installs, commercial titles in tests or docs.
- **A core rebuild** (section 0). This rules out, for phase 8: breakpoints and a gdb stub (N4), motion, camera and
  microphone, and the three deferred fixes. Each waits for the next core phase.
- **An OpenGL or software renderer inside the host.** The host is Vulkan-only. R05 F10 reports Azahar's core
  crashing in an AMD Vulkan driver; we cannot test AMD or Intel GPUs, so that stays a documented "untested".
- **Savestates between macOS and Windows** (archives store `long`, `docs/USING.md:366`; a fix is core work), and
  **two emulators in one process** (the core keeps global state; one process per instance is the design, M6).
- **Audio playback, any window, an RPC server, wireless.** The tool is headless and frame-synchronous.
- **An MCP server (N7).** The sibling 3DS-MCP is the MCP project; C1's command line gives agents a shell interface.
- **Linux (S13)**, which needs a third core build route (Q4), and **PyPI** (D1's prebuilt binaries come first, Q3).
- **Speed claims.** A1-A5 record numbers privately under `runs/p8/`; only the decisions they drive go public.

## 4. Phases

Order by value: measure first (cheap, and it decides four builds), then the Must gaps our siblings and agents hit,
then the Should work they asked for, then outside users. Phase B merges to main without a release; v1.2.0 ships B
and C together (Q1).

Each phase follows the project loop: briefs from this plan, sonnet builders in worktrees made at main by the main
loop, one opus as-built review of the phase's diff, fixes, then the main loop commits and merges. Hours book to
`phase-8`. Evidence goes under `runs/p8/<step>/` (gitignored), named on each item's Evidence line. Items: laz-810
(A), 820 (B), 830 (C), 840 (D), one file per step.

"Full PC gate": on the PC in a fresh tree, `make check && make && make test-host && make test-version`, then the
full pytest with `LAZ_REQUIRE_EMULATOR=1`, its skips checked by `tools/skips_check.py`, then
`python3 -I tools/docs_check.py`. At most 2 copies; one job at a time.

### Phase A: measure first (no product change)

Goal: numbers for the rows the research left thin (M15, S4, S5, S6, S7, S10). Each probe is a script under
`runs/p8/<step>/` (never committed) and a decision line. All runs on the PC, one at a time, announced on its board.

- **A0. Items and pre-flight** (main loop, 0.2 h). Items 810-816; PC free RAM and disk; whether devkitARM is on the
  PC (C2 needs it); Python version.
- **A1. Orphan probe** (sonnet script 0.15 h; main loop runs and reads it 0.2 h). Kill the parent hard (Windows:
  TerminateProcess) between batches, mid-batch (about 20000 frames) and during boot. Record the seconds until the
  worker is gone, whether the slot frees, and files left behind. Decision: worker gone within 5 s in every case,
  B5 is dropped; otherwise B5 is built. macOS waits for the Mac or B5's fake-worker test.
- **A2. Soak and reset cost** (sonnet script 0.15 h; main loop 0.25 h; plus 1-2 h machine time). One copy: 100
  boot-and-close cycles, then 300 `load_state` calls in one instance. Record peak RSS every 10 cycles, handle counts,
  leftover processes and slot files, and the median `load_state` time. Decisions: growth over 10 % or any leftover
  opens a fix step in B; if file I/O is most of a `load_state`, build C4.
- **A3. Two copies on the PC** (main loop, 0.2 h). One copy, then two, of the test app's 3D scene: GPU memory (the
  driver's own tool), peak RSS, guest frames per second, all private. Decision: USING section 15a says the Windows
  proof ran at most 2 copies; the cap stays 4 unless two copies already show memory trouble.
- **A4. Audio probe** (sonnet scratch host patch in a worktree, never merged, 0.2 h; main loop 0.2 h). Count the
  samples per frame the core hands the host, and the non-zero share, for the test app and, privately, one sibling
  homebrew that plays sound. Also check whether our own made-up DSP component file lets libctru's sound start under
  Azahar's HLE DSP. Nintendo's DSP firmware is a system file: never used, fetched or named in the repo. Decision:
  steady samples and our file works, C2 is gated on our test app; samples but our file fails, C2 is gated on the
  sibling's private check only (weaker; Guy decides); no samples, C2 is dropped.
- **A5. Software Vulkan desk check** (main loop, 0.3 h). Is there an official, pinnable software Vulkan driver for
  Windows with a published hash? If yes, and Guy OKs a new pinned download (like MoltenVK), a PC trial (0.3 h more)
  runs `test_c_checks` and `test_stencil_live` through the Vulkan loader's driver variable. If no, S10 stays missing
  and M16's recipe is macOS-hosted only.

Exit gate (main loop, 0.15 h): `runs/p8/a/decisions.md` gives A1-A5's numbers and one build-or-drop decision each;
the B and C briefs follow it. Where: PC. Hours: 2.0 (range 1.5-3), plus machine time.
Risks: the soak holds the PC's one job slot for 1-2 h and may wait for other sessions. A3 cannot test the default
cap of 4 (2-copy rule).

### Phase B: the Must gaps (siblings and agents first)

Goal: every Must row is have. Host C is unchanged; changes are Python, tests and docs.

- **B1. Determinism** (sonnet, 0.35 h). A USING section, "What repeats", lists every input to a run: the tick seed
  (`citra_init_ticks_override`), the clock base our core fixes (the brief reads `core/patches/` for the exact list),
  and what is not fixed (the stock core's async I/O, host time). A pure helper, `libazahar.images.digest(screens)`.
  New `test_determinism.py`: two instances with the same seed and inputs give equal shot digests and an equal
  test-app record at frames 300 and 600; two tick seeds give a different `tick` field (record offset 24), which
  catches an ignored seed (R04 #5). Gate: PC, 3 runs.
- **B2. Evidence on failure** (sonnet, 0.25 h). `HostTimeout`, `HostCrashed`, `GuestError` and `BootError` gain
  `.workdir` and `.log_path`; their text names `host.log` and the newest PNG under `shots/`, if any. Pickling still
  works. Gate: fake-worker hang and crash tests (CI fast) and the live crash test (PC).
- **B3. Compare helpers and a verdict convention** (sonnet, 0.4 h). `libazahar.images.compare(a, b, *, max_delta=0,
  max_pixels=0)` takes arrays or our PNG paths and returns the largest channel delta and the count of differing
  pixels; `write_diff(path)` writes each differing pixel at full brightness (CInema's normalised diff, R03 M5). It
  needs numpy and reads the host's own 8-bit RGBA PNGs in pure Python. `examples/verdict.py`: the app writes `PASS`
  or `FAIL <why>` to an SD file; the script uses `run_until` and exits 0 pass, 1 fail, 2 harness error or timeout
  (R03 M1). Gate: `test_images` (CI fast); the example in `docs_check` (PC).
- **B4. Re-press rule** (sonnet, 0.1 h, plus a PC run). A live test presses A, releases it for 1 frame and presses
  again; the test app's log must show two presses. USING section 4 states the rule, or the measured minimum if 1
  frame is not enough. Gate: PC.
- **B5. Parent-death watchdog** (only if A1 says so; sonnet, 0.25 h). A thread in the worker (ctypes releases the
  GIL during a batch, so it runs mid-batch). POSIX: compare `os.getppid()` with the start value every 0.5 s.
  Windows: wait on a parent process handle passed at spawn (a handle, so PID reuse cannot fool it). On parent death
  the worker ends the way the host already exits on Windows, with no atexit. Gate: a fake-worker test that kills the
  parent (CI fast on Windows; `test.yml` for macOS) and A1's mid-batch case rerun live (PC).
- **B6. Docs** (sonnet, 0.15 h). USING section 19 becomes a table keyed by each error's exact opening text. The
  `azhost` limit: a hang inside one frame never reaches `wall_limit`, so wrap it in an outer timeout (with the line).
- **B7. A CI recipe users can copy** (main loop, 0.8 h; CI rounds are costly: phase 7's three Windows fix rounds sat
  in a 0.92 h block). `test_state_boot`'s 2.5 s bound (Guy's, for a quiet machine) stays a gate on the PC and the
  Mac; on hosted runners (`CI` set) it records the time and does not fail. A new public `docs/CI.md`: a workflow
  homebrew authors copy for a hosted macOS runner (fetch, `make`, pip, run your app with the verdict script);
  `macos-live.yml` gains one step running it on our test app. The Windows parts pass on the PC before the push.
  Gate: macos-live green 3 dispatches of 3. A dispatch that never starts is not a failure: retry the next day, and
  tell Guy after two days with no runner.
- **B8. Review and merge** (opus as-built review 0.3 h; main loop 1.0 h: briefs, commits, the full PC gate,
  `test-windows.yml` on the merge commit). Merge to main locally; push only with Guy's word.

Exit gate: the full PC gate passes; `test-windows.yml` is green on the merge commit; B7's 3 of 3 (or Guy told);
`skips_check` reports only the known skips. Where: PC and CI. Hours: 3.6 (range 3-5.5).
Risks: every new name joins the promise at v1.2.0, so the review checks names, arguments and error attributes
against USING. A watchdog that fires wrongly kills good runs; the handle wait and the start-value check guard it.

### Phase C: agents and siblings, then v1.2.0

Goal: the Should rows our users asked for (S3, S4, S5, S8), then the release of B and C.

- **C1. Command line** (sonnet, 0.5 h; Q2). `python -m libazahar doctor` prints the OS, Python, host and core paths
  and versions, the Vulkan devices, the slots in use with their PIDs, and a 60-frame boot of the test app if present;
  exits 0 or 1. `python -m libazahar run APP --frames N [--inputs FILE] [--shot F ...] [--state P] [--save P]
  [--json]` prints one JSON object: the RunResult fields and shot paths, or the error class and B2's paths. Exit
  codes: 0 ok, 1 guest error, 2 usage, 3 boot, 4 timeout, 5 crash. `--help` on both. Gate: `test_cli` with the fake
  worker (CI fast) and one live run (PC).
- **C2. Audio capture** (only on A4 and Q5; sonnet: host 0.45 h, Python 0.3 h, test-app tone 0.3 h). The host
  collects the core's sample batches per run into a workdir file (ABI 5; ABI bumps are allowed in 1.x);
  `run(..., audio=True)` fills `RunResult.audio` (int16 stereo) and `audio_rate`. The test app plays a tone from a
  known frame with our own component file from A4, built on the PC with devkitARM (or in a CI job if the PC has
  none). Gate (PC): sample count matches the rate within one frame's worth; the tone's frequency (zero crossings)
  matches; silence before the tone frame. Host C changes also get phase 7's Darwin-visible diff and `test.yml`'s
  macOS build.
- **C3. Poll-exact movies** (sonnet, 0.4 h). Wire our core's `lazpy_movie_play` into the host and Python
  (`run(..., exact_inputs=True)`). The brief reads the core patch first; if the call needs a core change, C3 stops
  for the next core phase. Gate (PC): offset 0 for buttons, ZL/ZR, circle pad and touch over 30 changes each, 3
  repeats.
- **C4. States as bytes** (only if A2 says so; sonnet, 0.2 h). `save_state()` with no path returns bytes and
  `load_state(bytes)` takes them, through a temp file in the workdir; no host change. Gate: B1's digest round trip
  (PC).
- **C5. Review and merge** (opus as-built review 0.3 h; main loop 1.2 h, briefs included). The full PC gate.
- **C6. Release v1.2.0** (main loop and release-legal-audit, 2.5 h):
  1. Version and docs: README, STATUS (each new row names its item), USING.
  2. Stage with `mkrelease` on the PC; `release_check.py --pre-push` (PC).
  3. `clone_check` from a local bundle (PC: full suite, emulator required, `skips_check`).
  4. macOS: `test.yml` and `macos-live.yml` on the candidate commit, plus the Darwin-visible diff (phase 7, W1a).
  5. A private real-game check, run outside the repo (PC; S12).
  6. **release-legal-audit** on the tree, the history and the staged assets (mandatory).
  7. Guy's word, then push main; CI green, then the tag; then publish.
  8. `clone_check` from GitHub and the real release URLs (PC).
  The core assets are unchanged; the test app changes if C2 ships.

Exit gate: v1.2.0 is published, the audit says shippable, the post-publish clone check passes. Where: PC and CI.
Hours: 6.15 (range 4.5-9).
Risks: C2 depends on A4 and on 3DP (Q5). C3 may need the core. Hosted macOS may not start (risk 1).

### Phase D: outside users, then v1.3.0 (on Guy's go, Q3)

Goal: an install without a compiler, and a GPU-less CI path if one exists.

- **D1. Prebuilt host binaries** (main loop 1.0 h, sonnet 0.4 h). A manual CI workflow builds `libazhost.dll` and
  `azhost.exe` (MSYS2) and the macOS `libazhost.dylib` and `azhost`, ad-hoc signed as the last step (R05 M3). Each
  artifact is attested, as `core-win64.yml` does; `fetch.sh --host` downloads them sha256-pinned. The README gains a
  no-compiler route. Gate: `clone_check` without the build step on the PC, and the same in one hosted macOS run.
- **D2. Windows emulator tests in CI** (only if A5 found a driver; main loop, 1.2 h). A manual workflow first, green
  3 of 3; only then does it join the push workflow.
- **D3. Gymnasium-style example** (sonnet, 0.3 h; N1). `examples/gym_env.py`, gymnasium optional, outside the
  promise. Reward from `emu.memory`, the top screen as observation, reset loads a state. Gate: 200 steps (PC).
- **D4. Review, merge and release v1.3.0** (opus 0.3 h, main loop 0.8 h, release 2.5 h). C6's list; the audit
  also covers the new host-binary assets.

Exit gate: as C6, plus the no-compiler clone check on both systems. Where: PC and CI. Hours: 6.5 (range 4.5-11).
Risks: CI build rounds were phase 7's largest cost (4.9 h for the core route). Every step runs on the PC first, and
pushes go out only when CI is expected green.

## 5. Hours

Unit as in `docs/PLAN.md`: agent and main-loop wall time, as `docs/hours.tsv` books it; machine time (soak runs, CI
waits) is apart. Grounding in hours.tsv actuals (phases 1-7: 46.95 h, about 47 h; phase 7 alone 15.84 h):
- A sonnet build step took 0.03-0.47 h (V1's host and Python sides 0.47 h each; W2b2's release tools 0.40 h). An
  opus as-built review took 0.15-0.30 h (steps E and G 0.15 h, phase 4's joint review 0.26 h, W3 0.30 h).
- A probe with live runs took 0.4-0.8 h (V3's scene script 0.40 h; step J's 13 real-scene runs 0.80 h).
- A release with the legal audit took 2.1 h for v1.0.0 (V8, V9) and 6.4 h for v1.1.0 (W7-W10, the first Windows
  release, five clone-check rounds). A new CI build route took 4.9 h of rounds (W5).

| Phase | Hours | Range | Ships |
|---|---|---|---|
| A: measure first | 2.0 | 1.5-3 | decisions only |
| B: the Must gaps | 3.6 | 3-5.5 | main (siblings use it at once) |
| C: agents and siblings, v1.2.0 | 6.15 | 4.5-9 | v1.2.0 |
| A-C | **11.8** | 9-17.5 | every Must, the user-asked Shoulds |
| D: outside users, v1.3.0 | 6.5 | 4.5-11 | v1.3.0 (on Guy's go) |
| All | **18.3** | 13.5-28.5 | |

Not counted: the remaining planning (review and revision, about 0.5 h), machine time, and waits for the PC, the
users and Guy. Conditional steps (B5, C2, C4, D2) are inside the totals; if the probes drop them, A-C is about 10.3 h.

## 6. Risks

1. **macOS proof without the Mac.** Hosted macOS runners often never start, so a macOS-only regression could ship.
   Guards: no core change; phase 7's Darwin-visible diff for host C; `test.yml`'s macOS build and fast tests. If
   `macos-live` has not started after two days, the release waits and Guy is asked (Q1).
2. **Audio needs a DSP component.** libctru's sound loads one before it starts; Nintendo's is a system file and is
   never used. A4 tests our own made-up file under HLE; if it fails, C2's gate is only a sibling's private check.
3. **Poll-exact may need the core.** C3 reads the patch first and stops if so.
4. **CI rounds are expensive, and a red run emails Guy.** Workflow changes run on the PC first; new workflows start
   manual, green 3 of 3 before they join a push trigger.
5. **The PC is shared.** One job, 2 copies at most; A2's soak can wait hours for a slot, with no deadline on it.
6. **New public names are frozen at release.** The as-built reviews check each addition against USING's promise.
7. **Relaxing `test_state_boot` on hosted CI** could look like dropping a gate. It stays a gate on the PC and the
   Mac; only hosted runners record it instead.
8. **AMD and Intel GPUs stay untested** (R05 F10). STATUS keeps "untested"; nothing in phase 8 can prove them.

## 7. Open questions for Guy

- **Q1. Releases.** One release (v1.2.0) after B and C, not one after B alone? Siblings get B at merge, so an extra
  release serves only outside users and costs about 2.5 h. If hosted macOS never starts, may the release wait for a
  short Mac sitting?
  *Recommended:* one release after C; a Mac sitting of about 1 h only if `macos-live` fails to start twice.
- **Q2. A Python command line** (C1). This reverses v1's "no Python command line".
  *Recommended:* yes. It is the cheapest agent interface; its JSON keys and exit codes join the promise at v1.2.0.
- **Q3. Phase D** (prebuilt host binaries, a Windows CI path on a software driver, the Gymnasium example).
  *Recommended:* D1 and D3 after v1.2.0; D2 only if A5 finds an official, pinnable driver. No PyPI in phase 8.
- **Q4. Linux.**
  *Recommended:* not in phase 8; reopen when an outside user asks. It needs a Linux core build route, about phase
  7's size; the PC worker's earlier Linux plan is the starting point.
- **Q5. Audio (C2).** The peers were told to stop messaging, so 3DP's repro has not come.
  *Recommended:* run A4 now; build C2 once 3DP confirms, through you, that its sound lane is near.
