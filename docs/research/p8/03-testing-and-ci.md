# Emulators as test runners: what a CI-facing headless host must get right

Date: 2026-11-18. Scope: how homebrew and emulator projects run automated tests on emulators (Game Boy, NES, GBA, DS, 3DS, GameCube/Wii, libretro), what a CI-facing tool must provide, and what breaks in practice.
Sources are public docs, source files and issues. Items I could not confirm are marked "unverified". Licences were read from the GitHub repo metadata or README where shown; "not shown" means I could not see one.

## Tools surveyed
| Tool | Link | Licence | What it is |
|---|---|---|---|
| mGBA CInema | https://github.com/mgba-emu/mgba (src/platform/test/cinema-main.c) | MPL-2.0 | Directory-driven ROM/video-log runner with PNG baselines, xfail, parallel jobs, diffs |
| Mooneye test suite | https://github.com/Gekkio/mooneye-test-suite | MIT | Game Boy ROMs; pass/fail via register values, serial and an `LD B, B` marker |
| Blargg-style GB/NES ROMs | https://gbdev.gg8.se/wiki/articles/Test_ROMs , https://www.nesdev.org/wiki/Emulator_tests | mixed, per ROM | Serial or memory-text result protocols; some never terminate |
| gba-tests (jsmolka) | https://github.com/jsmolka/gba-tests | MIT | GBA ROMs that show "all pass" or the first failing test number on screen |
| SameBoy tester | https://github.com/LIJI32/SameBoy (Tester/main.c) | MIT (per repo; not re-checked) | Headless tester: runs ROMs N seconds with scripted input, writes a BMP; results page at https://sameboy.github.io/automation/ |
| Dolphin FifoCI | https://github.com/dolphin-emu/fifoci | BSD-2-Clause | Service that replays recorded GPU command logs per build to catch rendering regressions |
| Azahar unit tests | https://github.com/azahar-emu/azahar (src/tests) | GPL-3.0 | Catch2-style unit tests (core timing, memory, audio, shader), run with `ctest -VV` in CI (`.ci/linux.sh`) |
| mikage-emu/hwtests | https://github.com/mikage-emu/hwtests | not shown | "Automatic and reproducible tests for 3DS hardware features"; built via conan + devkitARM, last push 2024-02 |
| Normmatt/hwtests | https://github.com/Normmatt/hwtests | not shown | Early Citra-oriented 3DS homebrew test suite, started by A button, no result protocol documented |
| Archive of 3DS tests | https://git.openpunk.com/OpenPunk/citra/wiki/Archive-of-3DS-Tests | n/a | Citra-era wiki listing scattered 3DS hardware/GPU test repos (last edited 2017) |
| rust3ds actions / test-runner | https://github.com/rust3ds/test-runner , https://github.com/rust3ds/actions | not shown | GitHub Actions that run 3DS Rust test executables in a Citra container and upload test output artifacts |
| Miniretro | https://github.com/davidgfnet/miniretro , https://www.davidgf.net/2021/08/15/miniretro/ | not shown | Headless libretro frontend: core + ROM + fake input, N frames, periodic image dumps, HTML diff report |
| emutest | https://github.com/kivutar/emutest | not shown (page 404 on fetch) | Libretro test framework with Lua scripting and framebuffer checksums (as described by a search summary; unverified) |
| RetroArch | https://man.archlinux.org/man/retroarch.6.en | GPL-3.0 | Main libretro frontend; scripted screenshot-after-N-frames is a known pattern (https://github.com/thingsiplay/snapscreen), no dedicated test mode found |
| Vulkan CI render validation tutorial | https://docs.vulkan.org/tutorial/latest/ML_Inference/Desktop_Applications/04_ci_render_validation.html | CC-BY (Khronos docs; unverified) | Guidance for golden images on software Vulkan (SwiftShader/lavapipe) |

## What must work

### Must
1. **Exit codes that mean something.** CInema returns 0 when every test passes, xfails, xpasses or is skipped, and 1 for any fail, error, no tests found or bad arguments. Relied on by CI steps that only look at status. Evidence: https://raw.githubusercontent.com/mgba-emu/mgba/master/src/platform/test/cinema-main.c . Distinguish "test failed" from "harness error" and from "timed out" (three codes), since SameBoy's and Blargg's runners otherwise conflate no-output with fail (https://gbdev.gg8.se/forums/viewtopic.php?id=989 , https://lr.us.psf.lt/r/EmuDev/comments/1k5ud48/gameboy_emulator_no_serial_bus_output_with).
2. **Frame-count or time budget with hang detection.** Blargg's grouped `cpu_instrs` prints OK per sub-test but never exits, so a runner needs a cap (https://gbdev.gg8.se/forums/viewtopic.php?id=989). CInema bounds runs by a frame limit (default 3600) and stops early when the frame counter stalls, but has no wall-clock timeout (cinema-main.c above), so a hung host is not covered. Mooneye ends in a self-jump loop after `LD B, B`, which a runner can detect (https://github.com/Gekkio/mooneye-test-suite). Need both: guest-frame budget and host wall-clock watchdog.
3. **Deterministic runs.** CInema sets `TZ=UTC` and fixes the RTC epoch so baselines are repeatable (cinema-main.c). NESdev recommends recording a movie, hashing result screenshots at fixed times and replaying to detect regressions (https://www.nesdev.org/wiki/Emulator_tests). Azahar has a "determinism mode" for movies, and a fix was needed because the filesystem module still used host timing (https://github.com/azahar-emu/azahar/pull/2732). Need fixed clock/RTC, fixed RNG seeds, scripted input keyed to frame numbers, not wall time.
4. **Screenshot capture of a known frame to a lossless file** (PNG/BMP), keyed by frame number, plus raw-pixel hashing as a cheap check. Used by CInema (`baseline_NNNN.png`), SameBoy (BMP at end of run), Miniretro (dump every N frames). Evidence: cinema-main.c; https://github.com/LIJI32/SameBoy/blob/master/Tester/main.c ; https://github.com/davidgfnet/miniretro .
5. **Artifacts on failure.** CInema `-d` writes result, expected, diff and a normalised diff (max channel difference mapped to 255) and `-4` writes a 2x2 composite (cinema-main.c). The Vulkan tutorial uploads `test_output/` as a workflow artifact only on failure. rust3ds uploads test output artifacts (https://github.com/rust3ds/actions). Also save the log and the last frame on timeout.
6. **Log capture separate from machine results.** Guest/emulator log to a file or stream, not interleaved with the result protocol. Blargg-style serial parsers must not stop at the first line because failing runs print diagnostics before the verdict (https://gbdev.gg8.se/forums/viewtopic.php?id=771). rust3ds docs say the test-runner crate is what gives "useful test output on failures".
7. **No-display, no-GPU operation.** CI runners have no GPU, so use a CPU Vulkan/GL (SwiftShader or lavapipe) and render offscreen then read pixels back (Vulkan tutorial above). Distro build farms hit the same (https://gitlab.gnome.org/GNOME/gtk/-/issues/6085).
8. **Many instances in parallel, isolated.** CInema `-j N` with per-thread buffered logs; Miniretro `regression.py --threads` (cinema-main.c; miniretro README). Needs no shared global state (config dir, shader cache, save dir) between copies.

### Should
1. **Tolerant image comparison, selectable.** CInema is exact on RGB, no tolerance, which works because its renderer is a deterministic software one (cinema-main.c). With GPU or software-GPU output, exact matching is fragile (Vulkan tutorial). Offer exact, per-channel max-delta, differing-pixel-count, and perceptual modes; report the numbers.
2. **Baseline management.** Rebaseline failing (`-r`), missing only (`-R`), and a separate xfail baseline so known-bad output is pinned and a regression from "known bad" still fails (cinema-main.c). Relied on by emulator authors with long-lived known failures.
3. **Per-backend baselines or a pinned software ICD.** Mixing lavapipe and SwiftShader gives small real differences (https://github.com/zzuegg/jGibbonEngine/pull/6 , unmerged draft, anecdotal); pin one ICD and record its version in results.
4. **Input scripts tied to frames**: button and touch events at frame N, as in SameBoy's tester (pseudo-random start/A presses by frame count) and NES movie replay (Tester/main.c; nesdev page above).
5. **State-based assertions, not only pixels.** Mooneye's registers-and-serial protocol and the NES `$6000` output convention are easy to detect without any rendering (https://github.com/Gekkio/mooneye-test-suite ; https://www.nesdev.org/wiki/Emulator_tests). For a 3DS host: read guest memory at a mailbox address and compare.
6. **Snapshot/restore as a test accelerator**: boot once, restore per test. Azahar had save-state crash and version issues (https://github.com/azahar-emu/azahar/pull/2394 , https://github.com/azahar-emu/azahar/pull/2557), so versioned and checked states matter.
7. **Flaky-test policy built in**: bounded retry that records "passed on retry" as a distinct result, and quarantine/xfail rather than silent skip (CInema xfail/xpass model; wgpu #5665 below is a case where an intermittent software-GPU result was hard to even reproduce).

### Nice
1. **HTML/side-by-side report** over many runs (Miniretro `report.py compare`, red background on changed screenshots; README is "still pretty barebones" on how comparison works).
2. **Video/frame-sequence output** via ffmpeg pipe of BMP + PCM (Miniretro article, https://www.libretro.com/?p=49685).
3. **Lockstep two-core divergence finder**: save a state each frame and compare to find the first differing frame (Miniretro's companion tool, same article). Useful for bisecting nondeterminism.
4. **Fuzz/perf entry points** next to the test runner, as mGBA has `fuzz-main.c` and `perf-main.c` in the same directory (https://github.com/mgba-emu/mgba/tree/master/src/platform/test).
5. **GitHub Actions wrapper** (setup + run-tests) so homebrew authors need a few YAML lines (https://github.com/rust3ds/actions).

## Failure modes users report
| # | Failure | Evidence | Root-cause class |
|---|---|---|---|
| 1 | Reftest images differ by 1 RGBA level in a few pixels under software GL (softpipe); distro worked around by allowing small differences | https://gitlab.gnome.org/GNOME/gtk/-/issues/6085 | Renderer arithmetic differences; exact compare too strict |
| 2 | Screenshot tests pass on real GPUs, fail on CI with 0.01-0.24% pixel differences between llvmpipe and SwiftShader (draft PR, anecdotal) | https://github.com/zzuegg/jGibbonEngine/pull/6 | Different software ICDs, float rounding |
| 3 | Golden images break on driver updates, resolution changes, software vs hardware; thresholds must be tuned for the CI renderer | https://docs.vulkan.org/tutorial/latest/ML_Inference/Desktop_Applications/04_ci_render_validation.html | Golden image drift |
| 4 | Intermittent software-Vulkan result: test "worked once, then stopped"; CI green, local red with matching Mesa/SDK; never root-caused | https://github.com/gfx-rs/wgpu/issues/5665 | Unknown/nondeterministic software-driver behaviour |
| 5 | Segfault in `libvulkan_lvp.so` on CPU-only CI machines, sometimes; and crashes when Xvfb/llvmpipe coexists with a real GPU ICD | https://list.winehq.org/archives/list/wine-gitlab@list.winehq.org/message/OACAP54PRHIUFB5GXURO5ZLA2YDE5OYL | Software-Vulkan driver bug / ICD selection |
| 6 | Old lavapipe returns `VK_ERROR_INCOMPATIBLE_DRIVER` for a Vulkan 1.3 instance; project switched to SwiftShader | https://app.semanticdiff.com/gh/microsoft/onnxruntime/commit/eea7db461e1bedd5a3eb86804f1e2e8716c65a45 | CI image has old Mesa; version drift |
| 7 | Runner crash handler dereferences a NULL test pointer for a crash outside any test (CInema parallel mode) | cinema-main.c (raw link above) | Harness bug: crash isolation incomplete |
| 8 | No wall-clock timeout in the runner; only frame counts | cinema-main.c | Hang detection gap |
| 9 | Test never terminates (Blargg grouped ROM) or prints nothing (early bail-out), indistinguishable from fail without a cap | https://gbdev.gg8.se/forums/viewtopic.php?id=989 ; https://lr.us.psf.lt/r/EmuDev/comments/1k5ud48/gameboy_emulator_no_serial_bus_output_with | Result protocol with no terminal marker |
| 10 | Movie/TAS replay desyncs from nondeterministic async data-read timing, and from host timings in the FS module in determinism mode | https://github.com/azahar-emu/azahar/pull/2732 (fixes issue 2587) | Host time leaking into guest-visible state |
| 11 | Random native crash in Vulkan on macOS arm64 via MoltenVK (null + 0x58) during play and after a save-state load, in "a commercial game" | https://github.com/azahar-emu/azahar/issues/2720 ; guard added in https://github.com/azahar-emu/azahar/pull/2728 | Platform graphics-layer null handling; state-load invalidation path |
| 12 | Screenshot colour channels wrong on RGBA swapchain formats | https://github.com/azahar-emu/azahar/pull/2170 | Pixel-format/readback mismatch per backend |
| 13 | 3DS test repos scattered and unmaintained; prerequisites undocumented, no unified runner | https://git.openpunk.com/OpenPunk/citra/wiki/Archive-of-3DS-Tests ; https://github.com/Normmatt/hwtests | Ecosystem gap: no result protocol |
| 14 | Rust 3DS test action needs the Docker socket mounted to launch the runner; the cargo test runner cannot find a 3dsx built in the same run | https://github.com/rust3ds/actions ; https://github.com/rust3ds/test-runner | CI plumbing / build ordering |
| 15 | Qt offscreen platform is not a drop-in display: focus tests fail, OpenGL errors reported; Xvfb is the usual fallback | https://pytest-qt.readthedocs.io/en/latest/troubleshooting.html ; https://forum.qt.io/post/784304 | Headless windowing differs from a real display |
| 16 | Dolphin's own software renderer gets little use, so it is tested less than hardware backends (bug-tracker remark) | https://bugs.dolphin-emu.org/issues/12519 (unverified wording) | Slow path not in CI, bit-rots |

Not found despite searching: public reports of BIOS/firmware or licence problems in emulator CI specific to 3DS (Azahar's own CI builds only and runs unit tests, with no game ROMs: https://github.com/azahar-emu/azahar/blob/master/.github/workflows/build.yml). Game Boy CI has no such problem because boot ROMs are optional (SameBoy tester accepts `--boot`, Tester/main.c). Treat 3DS system archives, keys and shared-font data as a likely CI-secret issue, and say so in docs rather than assume.

## Implications for a headless 3DS libretro-core host
- Offer a first-class run mode: `run N guest frames or T seconds wall, then exit` with distinct codes for pass, fail, timeout and host error, and a machine-readable result file (JSON) next to the log.
- Make determinism explicit and testable: fixed RTC/seed, frame-keyed input, and a self-check that runs the same script twice and compares frame hashes (the Miniretro lockstep idea). Surface Azahar's determinism-mode gaps (host timings in FS) as known risks.
- Provide a guest-memory mailbox convention so 3DS homebrew can report pass/fail without pixels (the Mooneye/NES pattern); keep screenshots for visual tests.
- Ship compare helpers: exact, max-delta and differing-pixel-count with a per-test tolerance; write result/expected/diff/normalised diff on failure, as CInema does.
- Document and CI-test a software-GPU path: pin the ICD (lavapipe or SwiftShader) and Mesa version, record them in output, keep baselines per renderer, and expect small pixel differences (items 1-6 above). On macOS expect MoltenVK-specific crashes (item 11); ship a GPU-free or software path where possible.
- Add a wall-clock watchdog that kills a hung core and still saves the last frame and log; do not rely on frame counters only.
- Instance isolation for parallel runs: separate user/config/save dirs and shader caches, crash isolation per instance (item 7 shows the pitfall).
- State the firmware/keys requirement for CI plainly, and keep any such files out of artifacts and logs.
- Provide a tiny GitHub Actions example and a flaky policy (retry once, mark "flaky-pass", never silently skip), following CInema's xfail and rust3ds's action style.
