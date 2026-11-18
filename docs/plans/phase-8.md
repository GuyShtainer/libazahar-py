# Phase 8 plan: what this kind of tool must get right, and how we get there

Revision 1, 2026-11-18, opus reviser (laz-804): the single revision of rev 0 (laz-802) against the review (laz-803).
Plan only: nothing here has been built or run. Next: stop for Guy's go and his answers to section 8.

## 0. Reading this plan

Guy, 2026-11-18 20:08, verbatim: "research what must work on this kind of product, and plan (with single revision)
on how we get there". Inputs: `docs/research/p8/01`-`06` (06: the inventory at v1.1.0), the review
`docs/reviews/phase-8-plan-review.md`, `docs/hours.tsv`, `docs/map/rules.md`. `R01 §2` is research file 01, section 2;
`F3` is review finding 3. Section 6 is the hour-saving pass; section 9 answers every finding.

**The short answer.** Of 16 Must rows, 8 are have, 1 is have with a limit and 7 are partial; none is missing. The
partial ones: the re-press rule (M2), a window check without the Mac (M4), held input across a state load (M5), the
full list of randomness sources (M10), evidence on a failure (M11), cleanup when the caller dies (M15), one exit-code
table (M17). One release blocker is a tool, not a capability: the key-bytes history scan cannot run off the Mac and
still reports PASS there (B0, Q2).

**Users** ("Who"). **P**: our sibling projects, from a local checkout; they get every fix at merge. **A**: the owner's
AI agents; they kill runs, time out and retry on a shared PC. Outside users, who meet a clone-and-build install:
**T** test and CI users (homebrew authors), **S** script and bot users, **R** RL users.

**Where things run.** The Mac is closed to 3DS work; no step needs it except Q2's two short asks. **PC**: the Windows
PC through the toolkit's PC runner (`tools/pc/lane-pc`, its `docs/pc-worker/`), over SSH; A0 adds a PC section to
`docs/map/runners.md`. Light load: one job, at most 2 emulator copies, free RAM >= 2 GB + 0.6 GB per copy. **CI**:
`test-windows.yml` on every push (build, `make check`, host C tests, fast tests). `test.yml` (macOS fast) and
`macos-live.yml` (macOS emulator, `continue-on-error`) are manual: hosted macOS runners often never start, and each
cancel mails Guy. A push goes out only when CI is expected green, after the same steps pass on the PC.

**The full PC gate**, once per phase (H10), in a fresh tree, in a quiet window booked on the board: `make check &&
make && make test-host && make test-version`; `LAZ_REQUIRE_EMULATOR=1 python -m pytest -q -rs --junitxml
runs/p8/<step>/full.xml tests/python`; `python3 -I tools/skips_check.py runs/p8/<step>/full.xml --list w7` (which also
needs `test_release_fixture.py` and `test_profile_format.py` to have run); `python3 -I tools/docs_check.py`. Each new
live test adds its allowed skips to the lists in its own step. At most 2 live copies (B7, F8).

**No core rebuild in phase 8, by choice** (F2). A macOS core has no route without the Mac. A Windows core does
(`core-win64.yml`, phase 7 W5, attested); a rebuild costs a CI round, a new pin, and a note that old Windows states may
not load (USING allows it). Two deferred items are Windows core items: the OpenSSL ENGINESDIR/MODULESDIR prefix (a
low-risk CVE-2019-1552-class issue) and the Windows zip's own SOURCE.md entry. Folding them in is Q1. The third,
check 13, is a tool fix: B0 (F1).

## 1. The bar

What "working" means for a scriptable, headless emulator host. M = Must, S = Should, N = Nice. A Must needs support
from at least two research files, or from one file plus a real user of ours. "Proof" says how it is shown and where.
`test_c_checks` and every `*_live` test are slow and live, so they run on the PC, not in CI fast (F20).

| ID | Capability | Who | | Research | Proof (where) |
|---|---|---|---|---|---|
| M1 | Step N guest frames and get control back; a frame is one guest VBlank | all | M | R01 §2, R02 §2, R04 §2 | `test_c_checks` d (PC) |
| M2 | Input is held state (buttons, touch, circle pad); latency and hold rules in frames, including the shortest release before a re-press | all | M | R01 §2, R02 §2, R04 §2 | `test_c_checks` a, b; B4's re-press test (PC) |
| M3 | Both screens as arrays with a stated lifetime; PNG shots of a chosen frame | T S R A P | M | R01 §2, R03 M4, R04 §2 | `test_c_checks` d (PC); `test_map` (CI fast) |
| M4 | Headless: no window, no audio device, never takes focus | all | M | R01 §2, R05 N6 | gate A (Mac only); B6's Windows window test (PC) |
| M5 | Savestates from a script; the state covers the SD card; the rules say what a load restores, held input included | all | M | R01 §2 and F7, R02 §2 and §4, R04 §2 | `test_state*`, B1's held-input test (PC) |
| M6 | Many instances, one process each, the model documented; a machine-wide cap | T R P | M | R01 §2, R03 M8, R04 §2 | `test_pool_live` at 2 live copies (PC; B7) |
| M7 | A native crash becomes a typed error with the log tail; the caller survives | all | M | R05 M4, R04 §3 | `test_live_errors` (PC), `test_client` (CI fast) |
| M8 | Every wait has a deadline; on expiry the worker is killed and reaped | all | M | R05 M5, R03 M2 | `test_client` hang test (CI fast) |
| M9 | Guest memory read and write, bounded, between frames only | S R A P | M | R01 §2, R02 §2, R04 §2 | `test_memory_live` (PC) |
| M10 | Same inputs, seed and workdir give the same frames; every randomness source is listed as fixed, fixed on our core only, or not fixed; a test shows equal seeds match and different seeds differ | T R P | M | R02 §2, R03 M3, R04 §2 | B1's `test_determinism` (PC) |
| M11 | A failure leaves evidence: every live-instance error names the log, the workdir and the newest shot | T A P | M | R03 M5, M6 | B2's tests: `test_client` (CI fast), live (PC) |
| M12 | Host, Python layer and core versions are checked at start, with a clear refusal | all | M | R05 M8, R04 §3 | `test_abi` (CI fast) |
| M13 | A stable, versioned API with a written promise | all | M | R01 §2, R02 §2, R05 S5 | USING's promise; `docs_check` |
| M14 | A support matrix saying exactly what was tested | all | M | R05 M7 | README, STATUS; `docs_check` |
| M15 | Clean close: `close()` frees worker, slot and files; a caller that dies leaves no worker, even mid-batch | all, A most | M | R04 §2, R05 M4, S4 | `test_client`, `test_slots` (CI fast); B5's parent-kill test (CI fast) and A1's script live (PC) |
| M17 | One exit-code table for `azhost`, the CLI and the verdict example: pass, fail, timeout and harness error told apart | T A | M | R03 M1; our agents read `$?` | `test_cli`, `test_windows_cli` (CI fast) |
| S1 | Image compare: exact, largest channel delta, count of differing pixels, a diff image | T P | S | R03 S1, S2, F1-F3 | B3's `test_images` (CI fast) |
| S2 | A written pass/fail convention for test apps (an SD file line or a memory mailbox), with an example | T | S | R03 M1, S5 | the example in `docs_check` (PC) |
| S3 | Exact input timing: poll-exact movies | T P | S | R02 §2, R01 §2 | offset 0 for every input kind (PC) |
| S4 | Audio captured to an array (not played) | P S | S | R01 §2; 3DP's sound lane (item 500) | C2's tone test (PC) |
| S5 | Fast reset: the cost of a state load known; states as bytes | R A | S | R01 §2, R02 §2, R04 §2 | A2's numbers; C4's round trip (PC) |
| S6 | No growth over many boots and state loads | R T A | S | R01 §3, R04 §3 (unconfirmed reports) | A2's soak (PC) |
| S7 | Many-instance GPU and memory use known per platform | R T | S | R04 §3 (a gap), R05 | A3 (PC); the Mac rows exist |
| S8 | A command line for agents and shells: `doctor`, and a run that prints JSON | A S | S | R05 N4, R04 §2 | C1's `test_cli` (CI fast), one live run (PC) |
| S9 | Install without a compiler (prebuilt host binaries; wheels later) | T S R | S | R05 M1, R01 §2 N | `clone_check` with no build step (PC; CI) |
| S10 | A path with no GPU (a pinned software Vulkan driver) | T | S | R03 M7 (a Must there), R05 S1 | A5 trial (PC), then D3 in CI |
| S11 | Troubleshooting keyed by the exact error text | all | S | R05 S6, M6 | `docs_check` |
| S12 | A private real-game check before each release | P, us | S | R02 §3, R03 §3 | a private real-game check, run outside the repo (PC) |
| S13 | Linux | T R | S | R03 §4, R05 §4 | not planned (Q4) |
| S14 | A hosted-CI recipe users can copy (was M16, F6) | T | S | R03 N5, R05 S1 | one green dispatch plus the same steps on the PC (D2) |
| N1 | A Gymnasium-style wrapper as an example | R | N | R04 §2 (a Must for RL users; we have none yet) | D4: gymnasium's `check_env` (PC) |
| N2-N7 | Recording live input into a movie; C-stick, HOME, power in the input record; breakpoints and register writes; Python `logging`; a batched vector step; an MCP server | S T R A | N | R01, R02, R04, R06 §6 | - |

Not promoted to Must: **wheels** (R05 M1; our users run from a clone; S9 starts with host binaries); **bytes states**
(R01; file states serve every user; A2 measures first); **a Gymnasium API** (R04; no RL users yet); **no-GPU
operation** (R03 M7; R05 rates it Should, and no user of ours lacks a GPU; cheap now, H12); **a CI recipe** (rev 0's
M16; R03 rates it Nice, N5): now S14 in D (F6). M16 is retired, not reused, so rev 0's ids stay valid.

## 2. The gap

Against the inventory (`R06`); pointers are its own `file:line` unless named.

| ID | State | Pointer | What is missing, and the step that closes it |
|---|---|---|---|
| M1, M3, M6-M7, M9, M12-M14 | have | USING `:34` (M1), `emulator.py:453-471` (M3), USING `:239-265` (M6), `:136-139` (M7), `:190-199` (M9), `HOST-API.md:18-21` (M12), USING `:8-13` (M13), `README.md:12-19` (M14) | M6's gate exceeds 2 copies today (B7) |
| M2 | partial | USING `:74-83` | Re-press rule not stated or tested for A, ZL/ZR (another service) or touch (B4) |
| M4 | partial (F3) | `STATUS.md:99`; `tests/gate-a.sh:65` (`lsappinfo`, macOS) | No Windows window or focus test; `CREATE_NO_WINDOW` (`_client.py:180`) is design, not proof (B6) |
| M5 | partial (F4) | USING section 10; `emulator.py:490-493` | `load_state` keeps `self._held`; `Emulator(state=)` starts with nothing held; neither is written (B1) |
| M8 | have, one limit | USING `:36-39` | `azhost` alone has `wall_limit`, which a hang inside one frame never reaches (B2's doc table) |
| M10 | partial (F5) | `STATUS.md:69`; `core/options-lazpy.txt` | Unlisted: ps and ssl random bytes, the fresh config's console ID and MAC, the option profile, workdir reuse, held input (B1) |
| M11 | partial | USING `:130-131`; `errors.py` | Only `HostCrashed.log_tail`; no workdir, log or shot paths (B2) |
| M15 | partial (F10) | `_worker.py:126-147` | On EOF `_serve` returns 0 with no `hard_exit`, which can hang on Windows; mid-batch the worker cannot see EOF (B5) |
| M17 | partial (F7) | USING `:52-67` | `azhost` has a table (1 and 12-127 reserved); C1 and the example must use it, not invent two more (B3, C1) |
| S1 | missing | `python/libazahar/__init__.py:13-17` | B3 |
| S2 | partial | USING sections 7 and 12a | Pieces exist (SD text stop, `run_until`, `emu.memory`); no convention or example (B3) |
| S3 | partial | `STATUS.md:40`; `core/patches/0006-lazpy-movie-play.patch` | The core plays an Azahar movie file at boot; the host and Python never call it (C3; A0 checks the Windows export, F18) |
| S4 | missing | `host/frame.c:74-82` (samples discarded) | A4, then C2 |
| S5 | partial | USING section 10 | File states only; `load_state` cost unmeasured (A2, then C4) |
| S6, S7 | unmeasured / Mac only | `docs/research/real-scene-v3.md` | A2, A3 (figures stay private) |
| S8 | partial | `STATUS.md:80`, `:107` | `azhost` only; no Python command line (C1) |
| S9 | missing | USING `:17-21` | Windows users build the host in MSYS2 (D1) |
| S10 | missing | `test-windows.yml:3-4` (no Vulkan driver) | A5, then D3 |
| S11 | partial | USING `:410-425` | Short; not keyed by error text (B2) |
| S12 | missing as a gate | `STATUS.md:102-103` | C6 step 6, D5 |
| S14 | missing | `macos-live.yml:1-4` | D2 |
| N1-N7 | missing | `R06` §6 | N1 in D4; the rest are not scheduled |

## 3. Out of scope

| What | Why |
|---|---|
| Anything that needs console keys, system files, NAND data or encrypted titles: HOME menu, applets, `.cia` installs, commercial titles in tests or docs | rule 1; the README's legal section |
| A macOS core rebuild, so: breakpoints and a gdb stub (N4), motion, camera, microphone | no macOS core route without the Mac (section 0); a Windows-only rebuild is Q1 |
| An OpenGL or software renderer inside the host | the host is Vulkan-only; a software Vulkan driver (S10) covers no-GPU machines |
| AMD and Intel GPU support claims | R05 F10 reports the core crashing in an AMD driver; we cannot test them; STATUS keeps "untested" |
| Savestates between macOS and Windows | archives store `long` (USING `:366`); a fix is core work |
| Two emulators in one process | the core keeps global state; one process per instance is the design (M6) |
| Audio playback, any window, an RPC server, wireless, an MCP server (N7) | headless and frame-synchronous; the sibling 3DS-MCP is the MCP project, and C1 gives agents a shell interface |
| Linux (S13), PyPI wheels | a third core route; prebuilt host binaries come first (Q4) |
| A perceptual image compare | documented as a recipe on our arrays with an existing library (H16), not built |
| Speed claims | A2-A5 numbers stay private under `runs/p8/`; only the decisions they drive go public |

## 4. Phases

Order by value: measure first (cheap; it decides three builds), then the Must gaps siblings and agents hit, then the
Shoulds they asked for and v1.2.0, then outside users (D, on Guy's go). Each phase: briefs from this plan, sonnet
builders in worktrees made at main by the main loop, one opus as-built review of the phase's diff, fixes, then the
main loop commits and merges. Hours book to `phase-8`; evidence goes under `runs/p8/<step>/` (gitignored), named on
each item's Evidence line. Items: laz-810 (A), 820 (B), 830 (C), 840 (D), one file per step. Hours in the step tables
are agent or main-loop time as hours.tsv books it (section 5).

### Phase A: measure first (no product change)

Goal: numbers for the rows the research left thin. Probe scripts live under `runs/p8/<step>/` (never committed). All
runs on the PC, one at a time, announced on its board.

| Step | What | Hours | Decision |
|---|---|---|---|
| A0 | Items 810-815. PC free RAM and disk; devkitARM r67.1 present (C2's tone app); Python version; the `lazpy_movie_play` export in the shipped Windows core, by an export listing (F18); a PC section in `docs/map/runners.md`, then `mkmap` and `map_check` (F14) | main 0.3 | no export: C3 is dropped before any brief |
| A2 | Soak and reset cost (F17). 100 boot-and-close cycles: the parent's RSS and handle count, system free RAM, GPU memory, leftover workdir and slot files. Then 300 `load_state` calls in one instance: its RSS, the median load time and the file-I/O share (`state load` lines in `host.log`) | sonnet 0.1, main 0.4; machine 1-2 h apart | growth over 10 % or any leftover opens a fix step in B; file I/O most of a load builds C4 |
| A3 | One copy, then two, of the test app's 3D scene: GPU memory (the driver's tool), peak RSS, guest frames per second, all private | main 0.3 | the cap stays 4 unless two copies already show memory trouble |
| A4 | Audio probe (scratch host patch in a worktree, never merged): samples per frame and the non-zero share, for the test app and, privately, one sibling homebrew that plays sound; and whether our own made-up DSP component file lets libctru's sound start under Azahar's HLE DSP. Nintendo's DSP firmware is a system file: never used, fetched or named | sonnet 0.15, main 0.3 | samples and our file works: C2 gated on the tone app; samples only: C2 gated on the sibling's private check (Guy decides); no samples: C2 dropped |
| A5 | Software Vulkan trial, only after Q4's OK for a new pinned download. This revision answered the desk check (H12): MSYS2's `mingw-w64-x86_64-mesa` ships lavapipe (`vulkan_lvp.dll`, `lvp_icd.x86_64.json`), MIT, with a sha256 on its package page. Unpack it and the runtime DLLs it needs into its own `dl/` folder, as MoltenVK is; never install it into the PC's MSYS2. `VK_DRIVER_FILES` at its ICD, `LAZ_VK_DEVICE` at its index; run `test_c_checks` and `test_stencil_live` once | main 0.4 | both pass: D3 is built; else S10 stays missing |
| A-exit | `runs/p8/a/decisions.md`: each probe's numbers and one build-or-drop line; the B and C briefs follow it | main 0.15 | - |

A1 (rev 0's orphan probe) is dropped: the code shows a mid-batch worker cannot see EOF (F10, H1); its script is B5's
live gate. Exit: the decisions file (PC). Risks: the soak holds the PC 1-2 h; A3 cannot test the cap of 4 (2 copies).

### Phase B: the Must gaps (siblings and agents first)

Goal: every Must row is have. Python, tests, docs and one release tool; host C is unchanged. Merges to main with no
release; siblings use it at once.

| Step | What | Hours | Gate (where) |
|---|---|---|---|
| B0 | Release check 13 (F1): where the key-header reading copy is missing, report SKIP (PEND under `--pre-push`), never a NOTE inside a PASS; a self-test with the copy absent expects that | sonnet 0.1 | `release_check.py --self-test` (CI fast) |
| B1 | Determinism (F4, F5). A USING table, "What repeats": each run input and whether it is fixed, fixed on our core only, or not fixed, and which guest calls reach it. Inputs: the tick seed and clock base (`core/options-lazpy.txt`); deterministic async I/O (our core only; the stock core ignores some options, so the profile in force is itself an input); ps and ssl random bytes (host randomness, not fixed: needs a core change); the console ID and MAC a fresh config draws at random (not fixed on a fresh workdir; carried over on a reused one); workdir reuse (SD, NAND, config, shader cache); held input across `load_state`. Held input: keep today's behaviour and write it down (the promise holds input "across batches"; `Emulator(state=)` starts with nothing held; release everything with `set_input` before a reset). A pure helper `libazahar.images.digest(screens)`. `test_determinism.py`: same seed, inputs and fresh workdirs give equal digests and an equal test-app record at frames 300 and 600; two tick seeds give a different `tick` field (record offset 24); hold A, save, load, run: A is still down; boot from that state: A is up | sonnet 0.3 | PC, 3 runs, inside the phase's full PC gate |
| B2 | Evidence on failure (F16, H8). Every error raised by a live instance (`BootError`, `GuestError`, `HostTimeout`, `HostCrashed`, `StateError`, `HostError`, `GuestMemoryError`) gains `.workdir` and `.log_path`; the text names `host.log` and the newest PNG under `shots/`, if any; USING says that shot is the newest taken, not the frame at the failure. Pickling still works. USING section 19 becomes a table keyed by each error's opening text, with the `azhost` limit (a hang inside one frame never reaches `wall_limit`: wrap it in an outer timeout, with the line) | sonnet 0.25 | fake-worker hang and crash tests (CI fast); live crash test (PC) |
| B3 | Compare, verdict, one exit-code table (F7, F22, H5, H9). `libazahar.images.compare(a, b, *, max_delta=0, max_pixels=0)` on arrays or our PNG paths: largest channel delta, count of differing pixels; `write_diff(path)` at full brightness per differing pixel (CInema's normalised diff, R03 M5). numpy is imported lazily; without it a clear error names the `numpy` extra. The PNG reader reads only the host's own format (8-bit RGBA, filter 0, one IDAT; `host/png.c`) and refuses others. One table in USING section 3: `azhost`'s codes keep their meanings; the reserved 1 becomes "the test failed", 12 "timed out, worker killed", 13 "worker or host crashed". `examples/verdict.py`: the app writes `PASS` or `FAIL <why>` to an SD file; the script uses `run_until` and exits by that table | sonnet 0.3 | `test_images` (CI fast, the extra installed); the example in `docs_check` (PC) |
| B4 | Re-press (F15). Press, release for 1 frame, press again, for A, for ZL/ZR (another service), and a touch release and re-tap; the test app's log must show two presses each. USING section 4 states the rule, or the measured minimum | sonnet 0.1 | PC |
| B5 | Parent death (F10, H2, H15). Windows: the parent puts each worker in one Job object with kill-on-close, created at the first spawn (a few ctypes calls); the worker starts no children, so the short gap before the assignment is harmless; if assignment fails, one warning and EOF only. Every OS: EOF ends in `hard_exit` on Windows, as `close` already does. macOS: a daemon thread in the worker waits on the stdlib's `select.kqueue` for the parent's exit (rechecking `getppid` after it registers), then `os._exit`; ctypes releases the GIL during a batch, so it fires mid-batch | sonnet 0.3 | fake-worker parent-kill test (CI fast on Windows; `test.yml` for macOS, else it waits for the Mac); A1's script live: between batches, mid-batch (~20000 frames) and during boot, worker gone within 5 s and slot free (PC) |
| B6 | Window test on Windows (F3). During a live run, enumerate every top-level window, hidden ones included, and assert none belongs to the worker or `azhost.exe`. A positive control: the test first makes its own hidden window and must find it, so the check cannot pass empty (as gate A guards `lsappinfo`). The foreground check (before and after) means something only in an interactive session; over SSH it skips with that reason (an allowed skip) | sonnet 0.15 | PC |
| B7 | Pool test at 2 live copies (F8): boot 2 under a private cap of 2, a third waits; g1, g2 and g4 keep their checks | sonnet 0.1 | PC |
| B8 | Opus as-built review 0.25, sonnet fixes 0.15. Main loop 2.0: briefs and worktrees 0.4, hand-backs and merges 0.4, one full PC gate in a booked quiet window, waits included, 0.8, `test-windows.yml` on the merge commit plus one fix round 0.4. Merge locally; push only on Guy's word | 2.4 | the full PC gate; `test-windows.yml` green |

Exit gate: the full PC gate passes with only the known skips; `test-windows.yml` is green on the merge commit. Where:
PC and CI. Hours: 4.0 (range 3-5.5). Risks: every new name joins the promise at v1.2.0, so the review checks names,
arguments, error attributes and exit codes against USING. A Job object that fails to assign falls back to today's
behaviour, never to a false kill.

### Phase C: agents and siblings, then v1.2.0

Goal: the Shoulds our users asked for (S3, S4, S5, S8), then the release of B and C.

| Step | What | Hours | Gate (where) |
|---|---|---|---|
| C1 | Command line (Q3). `python -m libazahar doctor`: OS, Python, host and core paths and versions, slots in use with their PIDs, and a 60-frame boot of the test app if present, whose `host.log` gives the Vulkan devices ("unknown" without it, F19); exits 0 or 1. `python -m libazahar run APP --frames N [--inputs FILE] [--shot F ...] [--state P] [--save P] [--json]`: `--inputs` reads `azhost`'s input-script format (USING 4a); one JSON object (RunResult fields and shot paths, or the error class and B2's paths); exit codes from B3's table. `--help` on both | sonnet 0.35 | `test_cli` with the fake worker (CI fast); one live run (PC) |
| C2 | Audio capture (only on A4 and Q5). One host change with C3, ABI 5 (H3). The host collects the core's sample batches into a workdir file; `run(..., audio=True)` fills `RunResult.audio` (int16 stereo) and `audio_rate`. The tone plays in a separate small app, `testapp-tone/`, built with the pinned devkitARM, so the main test app and every state fixture stay as they are (F11, H4) | sonnet 0.6; main 0.2 (tone app build) | sample count within one frame's worth of the rate; the tone's frequency by the spectrum's peak (H27); silence before the tone frame (PC). Host C: phase 7's Darwin-visible diff and `test.yml`'s macOS build |
| C3 | Poll-exact movies. Python writes Azahar's movie file from a held-input movie (the format from the pinned core's own movie source) and calls `lazpy_movie_play` before boot: `run(..., exact_inputs=True)`, from boot only. If the call needs a core change, C3 stops for the next core phase | sonnet 0.35 | offset 0 for buttons, ZL/ZR, circle pad and touch over 30 changes each, 3 repeats (PC) |
| C4 | States as bytes (only if A2 says so): `save_state()` with no path returns bytes, `load_state(bytes)` takes them, through a temp file in the workdir; no host change | sonnet 0.1 | B1's digest round trip (PC) |
| C5 | Opus as-built review 0.3, sonnet fixes 0.2. Main loop 2.2: briefs, the Darwin-visible diff on the PC, merges, the full PC gate, CI | 2.7 | the full PC gate; `test-windows.yml` green |
| C6 | Release v1.2.0: main loop 3.5 (v1.0.0's V7-V9 took 3.7 h with its audits), release-legal-audit 0.3. The list is below | 3.8 | the list below |
| C6a | Only if Q1 says yes: `core-win64.yml` once with the OpenSSL prefix fix and the zip's SOURCE.md entry; a new Windows pin in `fetch.sh`; the state note. One CI round only: if it is not green, defer again with the reason written | main 1.5 | the attested artifact; C6's clone checks on it |

C6, in order: (1) version and docs: README, STATUS (each new row names its item), USING. (2) Stage with `mkrelease`
and run `release_check.py --pre-push` (PC); check 13 says SKIP or PEND (B0). (3) Fixtures (F12): `test_release_fixture`
on the v1.1.0 fixture (on Windows only if the core is unchanged); make the v1.2.0 one with `tools/mkfixture.py`. (4)
`clone_check` from a local bundle (PC; full suite, emulator required, `--list w7`). (5) macOS: `test.yml` and
`macos-live.yml` on the candidate, read from the pytest step's outcome and summary line, never the run's conclusion
(F21), plus the Darwin-visible diff; a dispatch not started in 30 minutes is cancelled once, then Q2's sitting. (6) A
private real-game check, run outside the repo (PC; S12). (7) Check 13 closed before the push (F1): Q2's Mac scan or
Guy's written ruling. (8) **release-legal-audit** on the tree, the history and the staged assets (mandatory). (9) Guy's
word, push main, CI green, tag, publish. (10) `clone_check` from GitHub and the real release URLs (PC).

Exit gate: v1.2.0 published, the audit says shippable, the post-publish clone check passes. Where: PC and CI (and the
Mac for Q2's scan). Hours: 8.1 (range 6-11.5), plus 1.5 if C6a. Risks: C2 depends on A4 and 3DP (Q5); C3 may need the
core; hosted macOS may not start (risk 1).

### Phase D: outside users, then v1.3.0 (on Guy's go, Q4)

| Step | What | Hours | Gate (where) |
|---|---|---|---|
| D1 | Prebuilt host binaries (S9; H18). A manual workflow reusing `test-windows.yml`'s MSYS2 build steps and `test.yml`'s macOS steps: `libazhost.dll`, `azhost.exe`, `libazhost.dylib`, `azhost`; the Mach-O files re-signed ad hoc as the last step (R05 M3); each artifact attested as `core-win64.yml` does. `fetch.sh --host` downloads them sha256-pinned; `mkrelease` and `release_check` gain their rows; the README gains a no-compiler route | sonnet 0.3, main 2.0 | `clone_check` with no build step on the PC, and once on hosted macOS |
| D2 | The user CI recipe (S14, was rev 0's B7; F6, H19). `docs/CI.md` points at a trimmed copy of our own `macos-live.yml` (fetch, the D1 binaries, pip, run your app with the verdict script); `macos-live.yml` gains one step running it on our test app. `test_state_boot`'s 2.5 s bound (Guy's ruling) records and does not fail on hosted runners (`CI` set) only if Q4 allows it; it stays a gate on the PC and the Mac | sonnet 0.2, main 1.0 | one green dispatch, read as in C6 step 5, plus the same steps on the PC; a dispatch not started in 30 minutes is cancelled once, no retry loop |
| D3 | Windows emulator tests in CI (S10; only if A5 passed). A manual workflow like `test-windows.yml` that also unpacks the pinned MSYS2 Mesa package, sets `VK_DRIVER_FILES` and runs the slow tests that need no second copy | sonnet 0.2, main 1.5 | green 3 dispatches of 3 (Windows runners start reliably), then it joins the push trigger |
| D4 | Gymnasium-style example (N1). `examples/gym_env.py`, gymnasium optional, outside the promise: reward from `emu.memory`, the top screen as observation, reset loads a state and releases held input (B1) | sonnet 0.2, main 0.1 | gymnasium's own `check_env` (H23) and 200 steps (PC) |
| D5 | Opus review 0.25, fixes 0.15; main loop merge 1.2; release v1.3.0 by C6's list, the audit also covering the host-binary assets: main 3.5, audit 0.3 | 5.4 | as C6, plus the no-compiler clone check on both systems |

Exit gate: as C6, plus the no-compiler clone check on both systems. Where: PC and CI. Hours: 10.9 (range 8-15). If Q4
picks one release after D, C6 and D5's releases merge and save about 3 h (H20). Risks: CI rounds were phase 7's
largest cost; D1 and D3 run their steps on the PC first, start manual, and push only when CI is expected green.

## 5. Hours

Unit as `docs/hours.tsv` books it: agent duration and main-loop session time, **including** the PC and CI waits the
session sits through (W10's 1.73 h was mostly a wait for the PC). Only unattended machine time (A2's soak, a CI build
nobody watches) is apart. Each step is priced from the actuals of similar work, not from rev 0's estimate rates (F9).

| Grounding (hours.tsv actuals) | Hours |
|---|---|
| Phases 1-7 | 44.72 (46.64 with setup, plan and build rows; 47.36 with phase 8 so far: research 0.31, plan 0.19, review 0.22) |
| Phase 7: estimated 15.9, took 15.84, only because the errors cancelled | sonnet steps estimated 8.25, took 1.05; main loop estimated about 4.2, took 13.10 |
| Phase 6: estimated 6.5, took 7.69 | main loop 5.62 of it (73 %); phase 7 83 % |
| A sonnet build step | 0.03-0.47 (V1's two sides 0.47 each; W2a 0.25, W2b1 0.20, W2b2 0.40, W3 fixes 0.17) |
| An opus as-built or fix review | 0.10-0.30 (V1 0.10 and 0.19, W1 0.23, W3 0.30) |
| Merge with PC gates and CI | 0.47 (W2 hand-backs and merge), 0.92 (W3-W4: gates, push, three CI fix rounds) |
| A probe with live runs | 0.40 (V3's scene script), 0.80 (step J's 13 runs) |
| A release with its legal audits | 3.69 (v1.0.0, V7-V9), 6.35 main loop alone (v1.1.0, W7-W10, the first Windows release) |
| A new CI build route | 4.93 (W5, ten rounds) |

| Phase | Sonnet | Opus agents | Main loop | Total | Range | Ships |
|---|---|---|---|---|---|---|
| A: measure first | 0.25 | 0 | 1.85 | **2.1** | 1.6-3.2 | decisions only |
| B: the Must gaps | 1.75 | 0.25 | 2.0 | **4.0** | 3-5.5 | main (siblings use it at once) |
| C: agents and siblings, v1.2.0 | 1.6 | 0.6 | 5.9 | **8.1** | 6-11.5 | v1.2.0 |
| A-C | 3.6 | 0.85 | 9.75 | **14.2** | 10.6-20.2 | every Must, the asked-for Shoulds |
| C6a (Q1 yes) | 0 | 0 | 1.5 | 1.5 | 1-2.5 | the Windows core fixes |
| D: outside users, v1.3.0 | 1.05 | 0.55 | 9.3 | **10.9** | 8-15 | v1.3.0 (on Guy's go) |
| All, without C6a | 4.65 | 1.4 | 19.05 | **25.1** | 18.6-35.2 | |

Rev 0 said 11.8 h (A-C) and 18.3 h (all); the gap is main loop, now priced at what phases 6 and 7 took (76 % of the
total; 73 % and 83 % there). Probes that drop C2, C4 and D3 give A-C 13.3 h, D 9.2 h; one release after D (H20) gives
about 22 h in all. Not counted: this revision (its own row) and waits for Guy or the sibling projects.

## 6. Hour-saving pass

Every idea keeps every gate and every review. H1-H11 are the review's; H12-H27 are this revision's, from the code
and a web search (sources at the end of this section).

| # | Idea | Saves | Risk | Taken? |
|---|---|---|---|---|
| H1 | Drop A1's decision; its script becomes B5's live gate | 0.3 h | none: the code already answers it | taken (A, B5) |
| H2 | Windows Job object with kill-on-close, parent side, instead of a watchdog thread on Windows | 0.1 h; no mid-batch false kills | an outer job that forbids assignment: warn and fall back | taken (B5) |
| H3 | One ABI bump (5) and one host diff for C2 and C3 | 0.4 h | the two features share one review | taken |
| H4 | A separate tone app; the main test app and its fixtures stay | 0.5-1 h (no fixture rebuild) | one more small build artifact | taken (C2) |
| H5 | Reuse `azhost`'s exit-code table and input-script parser in C1 and the example | 0.2 h; one table to freeze | none | taken (B3, C1) |
| H6 | The user CI recipe moves to D, gated on one green dispatch plus the PC | 0.5 h in B; fewer cancel mails | a macOS flake is caught later | taken (D2) |
| H7 | Fix check 13's false PASS as a tool change now | removes a blocker for 0.1 h | none | taken (B0) |
| H8 | Fold the error-text table into B2's doc change | 0.1 h | none | taken |
| H9 | A PNG reader for the host's own format only | keeps B3 at 0.3 h | refuses other PNGs, by design | taken |
| H10 | One full PC gate per phase, not per step (Guy's large-batch rule) | 0.5-1 h of PC booking and waits | a failure needs a narrower rerun | taken (B8, C5) |
| H11 | Sonnet estimates down to actuals, main-loop rows up | 0 h; honest totals | none | taken (section 5) |
| H12 | Software Vulkan from MSYS2's own `mingw-w64-x86_64-mesa` package (lavapipe; MIT; the package page publishes a sha256; MSYS2 is already our Windows toolchain), unpacked into `dl/` like MoltenVK | A5's desk check (0.3 h, done here) and any Mesa build route (W5-class, 2-5 h) | lavapipe is not a conformant driver; it is the testing path, and baselines may differ from a GPU's (R03 F1-F3); the dependency DLLs need their own pins | taken (A5, D3) |
| H13 | Community Windows builds (pal1000/mesa-dist-win, jakoch/rasterizers, mmozeiko/build-mesa) or SwiftShader | the same | not official: neither Mesa nor Google publishes Windows binaries; SwiftShader would need our own build | rejected |
| H14 | Reuse the PC worker's earlier result: the core already passed the test app's gates on lavapipe under Linux (toolkit PC-worker notes) | A5 needs one trial run, not a matrix | Windows lavapipe is a different build | taken (A5) |
| H15 | macOS parent death through the stdlib's `kqueue` process-exit event instead of polling `getppid` every 0.5 s | 0 h; no polling loop, no 0.5 s delay | a parent that died before the wait registers: recheck `getppid` | taken (B5) |
| H16 | Perceptual compare: document the pixelmatch Python port (ISC, no dependencies) on our arrays instead of building a fourth mode | about 0.3 h | none; outside the promise | taken (B3's doc line) |
| H17 | Pillow or pypng to read PNGs | 0 h | a new dependency for a reader of our own fixed format | rejected |
| H18 | D1 reuses the existing CI build steps and adds upload and attest steps, instead of a new build route | 1-1.5 h against W5's pattern | hosted macOS may not start (risk 1) | taken (D1) |
| H19 | Our own `macos-live.yml` is the user recipe's source (a trimmed copy), not a new example workflow | 0.2 h | the copy drifts: `docs_check` compares their steps | taken (D2) |
| H20 | One release after D instead of v1.2.0 and v1.3.0 | about 3 h | outside users wait longer; more change per audit | Guy's choice (Q4) |
| H21 | A hashed key-window file kept on the PC so check 13 runs off the Mac | 0.25 h per release | data derived from key headers leaves the Mac: needs an ip-legal ruling and a Mac sitting to make | rejected for phase 8 |
| H22 | The window check through PowerShell's `MainWindowHandle` | 0.05 h | sees only a main window; hidden and secondary windows slip through | rejected (B6 enumerates all) |
| H23 | gymnasium's own `check_env` as D4's gate | 0.1 h; a stronger gate (spaces, reset and step contract) | gymnasium installed in that test only | taken (D4) |
| H24 | pywin32's job API instead of ctypes | 0 h | a new dependency for a few calls | rejected |
| H25 | Clear held input on `load_state` (the review's simplest rule) | 0 h | a behaviour change inside 1.x for every caller that relies on input held across batches | rejected; keep and document (B1) |
| H26 | A Windows core rebuild without a cap on CI rounds | - | W5 took ten rounds | rejected: C6a gets one round |
| H27 | The tone check by the spectrum's peak (numpy) instead of counting zero crossings | 0 h; robust to noise | none | taken (C2) |

Sources (2026-11-18): MSYS2's `mingw-w64-x86_64-mesa` package page; mesa-dist-win, jakoch/rasterizers, build-mesa and
SwiftShader; Microsoft's Job Objects page, the Android NDK's `win32.py`, Rust's bootstrap `job.rs`; pixelmatch on PyPI.

## 7. Risks

| # | Risk | Guard |
|---|---|---|
| 1 | macOS proof without the Mac: hosted macOS runners often never start, so a macOS-only regression could ship | no macOS core change; the Darwin-visible diff for host C; `test.yml` and `macos-live.yml` read by step outcome; Q2's Mac sitting if they do not start |
| 2 | Check 13 cannot run off the Mac | B0 makes it say SKIP or PEND; C6 step 7 closes it by a Mac scan or Guy's written ruling (Q2) |
| 3 | Audio needs a DSP component; Nintendo's is a system file, never used | A4 tests our own made-up file under HLE; if it fails, C2's gate is a sibling's private check, on Guy's word |
| 4 | Poll-exact may need the core, or the Windows export may be missing | A0 checks the export; C3 stops if a core change is needed |
| 5 | CI rounds are expensive, and a red run emails Guy | every workflow change runs on the PC first; new workflows start manual; C6a gets one round |
| 6 | The PC is shared: the full gate needs a quiet window, and `test_pool_live`'s 1 s kill-to-acquire bound failed under load once (W7 run 4) | one full gate per phase, booked on the board; the wait is counted in the main-loop hours |
| 7 | New public names, attributes and exit codes freeze at release | the as-built reviews check each against USING's promise |
| 8 | lavapipe output differs from a GPU's, and software drivers have intermittent bugs (R03 F4-F6) | D3 runs gates that check behaviour, not pixel baselines; the driver is pinned by sha256 and named in the log |
| 9 | Over SSH, the PC's jobs have no interactive desktop, so the focus half of B6 skips there | the owned-window half has a positive control; the skip names its reason |
| 10 | AMD and Intel GPUs stay untested (R05 F10) | STATUS keeps "untested" |

## 8. Open questions for Guy

| Q | Question | Recommended |
|---|---|---|
| Q1 | A Windows-only core rebuild in v1.2.0 (F2)? It fixes the OpenSSL ENGINESDIR/MODULESDIR prefix (a low-risk, CVE-2019-1552-class item in a shipped binary) and the Windows zip's SOURCE.md entry through `core-win64.yml`; about 1.5 h, a new Windows pin, a note that v1.1.0 Windows states may not load | yes, as C6a with one CI round; not green: defer again with the reason written |
| Q2 | Two short Mac sittings, no 3DS work (F1, risk 1)? About 15 minutes before each release push for a read-only check-13 scan of the new history (the key-header copy never leaves the Mac); about 1 h for the emulator suite only if `macos-live` has not started in 30 minutes | yes to both; the other way, a written ruling to ship with check 13 pending, leaves rule 1 unchecked on the new commits |
| Q3 | A Python command line (C1), reversing v1's "no Python command line"? | yes: the cheapest agent interface; its JSON keys and B3's exit codes join the promise at v1.2.0 |
| Q4 | Phase D (F6, H12, H20): (a) do D1-D4 at all; (b) one release after D instead of v1.2.0 plus v1.3.0; (c) on hosted runners only, `test_state_boot`'s 2.5 s bound (your ruling) records the time instead of failing, staying a gate on the PC and the Mac; (d) a new pinned download, MSYS2's Mesa package for lavapipe (A5 needs it) | (a) yes, after v1.2.0, no Linux or PyPI; (b) no, two releases, so outside users get B and C sooner; (c) yes, hosted runners measured 5.3 s; (d) yes: official, MIT, sha256-pinned, own `dl/` folder |
| Q5 | Audio (C2)? The peers were told to stop messaging, so 3DP's repro has not come | run A4 now; build C2 once 3DP confirms, through you, that its sound lane is near |

## 9. The review's findings, answered

| F | Sev. | Answer | Where |
|---|---|---|---|
| 1 | blocker | Fixed. Check 13 says SKIP or PEND where it cannot run (B0, 0.1 h); each release closes it by a Mac scan or Guy's written ruling before the push (C6 step 7, D5); the choice is Q2 | B0, C6, Q2 |
| 2 | major | Fixed. "No core rebuild, by choice", with the Windows route named; the Windows rebuild is Q1 with a recommendation; check 13 moved to B0 | §0, C6a, Q1 |
| 3 | major | Fixed. M4 is partial; B6 adds a Windows window test with a positive control; the pointer is `STATUS.md:99`; gate A stays for the Mac. Added: the focus half skips over SSH (risk 9) | §1, §2, B6 |
| 4 | major | Fixed. M5 covers what a load restores; B1 writes the held-input rule and tests it. The rule chosen: keep today's behaviour and document it, not clear on load, since clearing changes 1.x behaviour (H25) | M5, B1 |
| 5 | major | Fixed. B1's "What repeats" lists ps and ssl random bytes, the fresh config's console ID and MAC, the option profile, workdir reuse and held input, each marked fixed, fixed on our core only, or not fixed | B1 |
| 6 | major | Fixed. The recipe is S14 in D (D2); its gate is one green dispatch read by step outcome plus the PC, with one cancel and no retry loop; the `test_state_boot` relaxation is Q4 (c). S10 notes R03 M7 as a Must there but stays a Should (one research Must, no user of ours) | §1, D2, Q4 |
| 7 | major | Fixed. One table: `azhost`'s codes keep their meanings; the reserved 1 becomes fail, 12 timeout, 13 crash; C1 and the example use it; C1's `--inputs` reads `azhost`'s input script. Added as Must M17 (R03 M1 plus our agents) | M17, B3, C1 |
| 8 | major | Fixed. B7 caps the pool test at 2 live copies; the full gate is one per phase in a booked quiet window; the load-sensitive bound is risk 6 | §0, B7 |
| 9 | major | Fixed. Each step priced from comparable actuals (section 5), waits included as hours.tsv books them; sonnet down, main loop up. A-C 14.2 h, all 25.1 h; the 46.95 h figure corrected to 44.72 / 46.64 / 47.36 | §5 |
| 10 | major | Fixed. A1's decision is dropped and B5 is built: a Job object on Windows, `hard_exit` on EOF, a `kqueue` exit wait on macOS; A1's three cases are B5's live gate | A, B5 |
| 11 | major | Fixed. The tone lives in a separate app built with the pinned devkitARM; the main test app and its fixtures stay; C2 and C3 share one ABI bump | C2, C3 |
| 12 | minor | Fixed. C6 step 3 runs the v1.1.0 fixture and makes the v1.2.0 one | C6 |
| 13 | minor | Fixed. The full gate names `--junitxml`, `--list w7` and its two required files; each new live test adds its allowed skips | §0 |
| 14 | minor | Fixed. The plan points at the toolkit's PC runner; A0 adds a PC section to `runners.md` | §0, A0 |
| 15 | minor | Fixed. B4 tests A, ZL/ZR and a touch re-tap | B4 |
| 16 | minor | Fixed. Every live-instance error class gains the fields (seven; `ArgumentError` and `NeedsLazpyCore` have no instance); USING says the shot is the newest taken | B2 |
| 17 | minor | Fixed. A2 measures the parent, free RAM, GPU memory and leftovers across boots; per-instance RSS only across the 300 loads | A2 |
| 18 | minor | Fixed. A0 checks the Windows export; no export drops C3 before any brief | A0 |
| 19 | minor | Fixed. `doctor` reads the Vulkan devices from the boot's `host.log`, "unknown" without the test app | C1 |
| 20 | minor | Fixed in the plan: S2 cites R03 M1; the M1 and M3 proofs are live (PC). The inventory file itself is not edited: this revision writes only the plan | §1 |
| 21 | minor | Fixed. `macos-live` is read from the pytest step's outcome and summary line, never the run's conclusion | C6 step 5, D2 |
| 22 | minor | Fixed. numpy is imported lazily, with a clear error naming the extra; the fast test installs it | B3 |
