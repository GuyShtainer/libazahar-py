# Python libraries that drive an emulator programmatically

Date: 2026-11-18. Scope: what a scriptable, headless, many-instance emulator host must get right, taken from
PyBoy, stable-retro (and its parent gym-retro), mGBA's Python bindings, libretro.py, nes-py and cynes, plus their
issue trackers. Issue counts are comment counts read via the GitHub API on this date. Read-only research; nothing
was installed or run. Where a README did not state something, this file says "not documented" instead of guessing.

## 1. Tools

| Name | Link | Licence | What it is |
|---|---|---|---|
| PyBoy | https://github.com/Baekalfen/PyBoy | Custom `LICENSE.md` (GitHub reports no SPDX id) | Game Boy emulator written in Python/Cython; `tick()`, `button()`, `memory[]`, PIL screen; built for bots and RL |
| stable-retro | https://github.com/Farama-Foundation/stable-retro | MIT (cores keep their own, see LICENSES.md) | Maintained gym-retro fork; Gymnasium envs over libretro cores for ~15 systems |
| gym-retro (retro) | https://github.com/openai/retro | MIT | Original OpenAI project; the largest issue history (install, determinism, parallelism) |
| mGBA Python bindings | https://github.com/mgba-emu/mgba/tree/master/src/platform/python | MPL-2.0 | cffi bindings inside the mGBA tree (`core.py`, `gb.py`, `gba.py`, `memory.py`, `image.py`); built from source with CMake, no wheel evidence found |
| libretro.py | https://github.com/JesseTG/libretro.py | MIT | Pure-Python ctypes binding of the libretro API, "intended for testing cores"; Win/macOS/Linux, Python 3.12+ |
| nes-py | https://github.com/Kautenja/nes-py | MIT | C++ NES core with Gymnasium API, zero-copy numpy frames, `VectorNESEmulator`; wheels for 3 OSes |
| cynes | https://github.com/Youlixx/cynes | MIT | C++ NES core, headless `NES` class, `step()` returns a numpy frame, numpy save states |

## 2. What must work

### Must
- **Step N frames, returning control** (all of them). `tick(n)` in PyBoy, `step(frames=n)` in cynes, `step()` in nes-py,
  `session.run()` in libretro.py. Everything else hangs off this. A guest-side hang inside it freezes the caller
  (https://github.com/Baekalfen/PyBoy/issues/375: `tick` never returned after `load_state`).
  Docs: https://github.com/Baekalfen/PyBoy , https://github.com/Youlixx/cynes
- **Input as explicit state, not events.** cynes: `nes.controller` bitmask that persists until cleared; PyBoy: `button(name, delay)`
  then `tick`; PyBoy README warns input only registers after a tick. Users train bots on this, so press/release timing in frames
  must be exact and documented. Snapshots must include input latch state: https://github.com/Kautenja/nes-py/issues/110
  (restore resumed a pad read wrongly because controllers were not in the snapshot).
- **Screen as a numpy array, cheap.** nes-py returns a zero-copy strided `(240,256,3)` view plus explicit contiguous/grayscale
  copy helpers with reusable output buffers (https://github.com/Kautenja/nes-py). PyBoy exposes a PIL image
  (https://github.com/Baekalfen/PyBoy) and users ask about ndarray and screenshots
  (https://github.com/Baekalfen/PyBoy/issues/359, /248, /201). Must handle row pitch larger than width x bytes-per-pixel
  (https://github.com/JesseTG/libretro.py/issues/8) and 16-bit pixel formats (libretro.py issue 5), and rotation
  (libretro.py issue 3).
- **Headless by default, windowing optional.** cynes `NES` vs `WindowedNES`; nes-py `human` render must be on the main thread
  and viewer created inside the child process (https://github.com/Kautenja/nes-py). Audio init must not be a hard
  failure with no device: https://github.com/Baekalfen/PyBoy/issues/405 (`SDL_InitSubSystem audio failed`).
- **Savestate save/restore in memory and to bytes, with a documented compatibility contract.** nes-py states are "opaque
  same-process checkpoint objects, not a stable cross-version format"; cynes warns they are slow and not to be edited.
  PyBoy states break across releases (maintainer's reply in https://github.com/Baekalfen/PyBoy/issues/375). Users need to
  know which of "same process", "same build", "same version" holds.
- **Multiple instances, independent state.** RL and test farms rely on this. gym-retro's backend "cannot be loaded into the same
  process more than once", so users used subprocesses (https://github.com/openai/retro/issues/42). nes-py had global
  state that broke threads and same-thread instances (https://github.com/Kautenja/nes-py/issues/35).
- **Guest memory read (and write) by address, bounded.** PyBoy `memory[addr]`, nes-py/cynes `nes[addr]`, libretro.py
  `core.get_memory()`. Bounds must be explicit: `list(pyboy.memory)` hung because the object advertises no size
  (https://github.com/Baekalfen/PyBoy/issues/402). Must return the full region, not a truncated view
  (https://github.com/JesseTG/libretro.py/issues/22).
- **Clean teardown and reset.** gym-retro could not load a second ROM into one emulator; the maintainer answer was "close and
  make a new one" (https://github.com/openai/retro/issues/244). Reset must restore every piece of state, including RAM
  contents: https://github.com/Youlixx/cynes/issues/10 (uninitialised RAM made sequential tests pass by reusing the old
  instance's memory).

### Should
- **Determinism you can verify.** gym-retro users compared RAM after `reset` vs `set_state` and found core-specific
  mismatches (https://github.com/openai/retro/issues/114, still open). Provide a state-hash or frame-hash helper so users can
  check themselves; document what is seeded (RNG, RTC). PyBoy has "Force clock value" as a request
  (https://github.com/Baekalfen/PyBoy/issues/328) and a corrupted-RTC-on-load report (issue 99).
- **Speed control and frame skip.** `set_emulation_speed(0)` removes the cap; `tick(n, render=False)` skips rendering for the
  inner frames; the README reports large real-time multiples when not rendering (https://github.com/Baekalfen/PyBoy).
  Keep render-skipping a first-class argument.
- **Batched/vector stepping** so Python call overhead is paid once per N instances (nes-py `VectorNESEmulator`,
  https://github.com/Kautenja/nes-py).
- **Audio capture as an array**, not only playback. Asked for repeatedly: https://github.com/Baekalfen/PyBoy/issues/217,
  /368 (sound in recorder). libretro.py ships `ArrayAudioDriver` and a wave writer (issue 13 lists a size bug in them).
- **Pluggable drivers** (video/audio/input/options) so a test can swap them: libretro.py design, https://github.com/JesseTG/libretro.py
- **Core options set before load**, with the right pointer semantics: https://github.com/JesseTG/libretro.py/issues/12.

### Nice
- Wheels for every supported platform, including ARM Windows (https://github.com/JesseTG/libretro.py/issues/27, /26).
- A live docs site and a test suite (libretro.py issues 11 and 10 both asked for them early on).
- Gymnasium wrapper on top (stable-retro, nes-py) and PettingZoo for multi-player
  (https://github.com/Farama-Foundation/stable-retro/issues/277).
- Memory search / watch tools (https://github.com/Farama-Foundation/stable-retro/issues/271: the memory search function uses too much RAM).
- Recording/replay of inputs (stable-retro replay issues, e.g. https://github.com/Farama-Foundation/stable-retro/issues/186).

## 3. Failure modes users report

1. **Install fails: no wheel, source build breaks.** PyBoy: "Missing wheels on PyPI" for Windows/macOS, 11 comments, workaround
   pin an older version (https://github.com/Baekalfen/PyBoy/issues/321). gym-retro: dozens of install threads, e.g. 31 comments on
   Windows 7 (https://github.com/openai/retro/issues/26), 13 on Apple M1 (https://github.com/openai/retro/issues/264).
   stable-retro: Apple silicon build fails, 18 comments (https://github.com/Farama-Foundation/stable-retro/issues/107); macOS
   wheel builds disabled (https://github.com/Farama-Foundation/stable-retro/issues/267). nes-py: Xcode/GCC/MSVC compile failures
   (https://github.com/Kautenja/nes-py/issues/57, /55, /53). Class: packaging / toolchain.
2. **Non-ASCII install or ROM path crashes the native layer.** nes-py `access violation reading 0x7FFC`, cause was a Chinese
   path (https://github.com/Kautenja/nes-py/issues/103). Class: Windows path encoding at the C boundary.
3. **Illegal instruction on older CPUs.** gym-retro compiled SSSE3 paths that the CPU lacked, process died on `make`
   (https://github.com/openai/retro/issues/187); stable-retro now documents an SSE3 minimum (https://github.com/Farama-Foundation/stable-retro).
   Class: build flags / CPU baseline.
4. **One emulator per process; globals in the native core.** gym-retro (https://github.com/openai/retro/issues/42), nes-py
   threads and same-thread instances ("invalid opcode", https://github.com/Kautenja/nes-py/issues/35). Class: global/static state.
5. **Cross-instance pointers in savestates.** cynes saved absolute mapper pointers, so loading into another instance or process
   hit invalid memory (AddressSanitizer repro, https://github.com/Youlixx/cynes/issues/6). Class: state serialisation.
6. **Restored state shows stale frame or a segfault.** PyBoy: image differs after load until one more tick
   (https://github.com/Baekalfen/PyBoy/issues/174); cynes: frame buffer wrong after load (issue 25), the fix then segfaulted;
   nes-py: "Graphical glitch after backup" (https://github.com/Kautenja/nes-py/issues/36). Class: derived/cached state not in snapshot.
7. **Snapshot omits peripheral state.** nes-py controllers latch not saved (https://github.com/Kautenja/nes-py/issues/110);
   PyBoy "send_input not stored when saving/loading state" (https://github.com/Baekalfen/PyBoy/issues/170). Class: incomplete snapshot.
8. **Savestate incompatibility across versions.** PyBoy 2.5 froze on `tick` after loading an old state; maintainer: states are not
   consistent between releases (https://github.com/Baekalfen/PyBoy/issues/375). PyBoy CGB states not loading (issue 245).
   nes-py documents the non-guarantee up front. Class: undocumented format contract.
9. **Nondeterminism between reset and set_state.** gym-retro Atari/Genesis cores gave different RAM after `set_state`
   (https://github.com/openai/retro/issues/114, open). Class: core-side serialise gaps; RAM/RTC seeding.
10. **Uninitialised memory leaks across instances.** cynes tests passed because a new instance reused freed RAM
    (https://github.com/Youlixx/cynes/issues/10). Class: allocator reuse, no zeroing.
11. **Slow-growing memory in long runs.** lr-mgba "slowly takes up all memory" until the core crashes; the maintainer said the core
    does not allocate while running and suspected the frontend (https://github.com/mgba-emu/mgba/issues/2991, open). Python side:
    libretro.py VFS callbacks leaked returned bytes objects (https://github.com/JesseTG/libretro.py/issues/30). Class: leak at the
    callback/ownership boundary, not in the core.
12. **Threading and GIL / windowing from threads.** nes-py pyglet render fails from a second thread
    (https://github.com/Kautenja/nes-py/issues/50, 10 comments; now documented as main-thread only for `human`). Stable-retro
    "human render mode not rendering properly on Ubuntu" (https://github.com/Farama-Foundation/stable-retro/issues/209). Class: GL/window
    context bound to a thread.
13. **Memory view wrong or hanging.** libretro.py `get_memory(SYSTEM_RAM)` returned incomplete data
    (https://github.com/JesseTG/libretro.py/issues/22); PyBoy `list(memory)` hang (https://github.com/Baekalfen/PyBoy/issues/402).
    Class: unbounded or mis-sized view over native memory.
14. **Frontend/core mismatch: pitch, pixel format, defaults.** Framebuffer too small when pitch > width x bpp
    (https://github.com/JesseTG/libretro.py/issues/8); 16-bit screenshots (issue 5); a new release needed content set to a default
    driver or video reinit failed (https://github.com/JesseTG/libretro.py/issues/25). Many cores misbehave under a generic host:
    melonDS inconsistent (issue 23), Flycast does not render (issue 18), MAME freezes on load (issue 15), Vectrex crashes at render init
    (issue 16). Class: libretro contract corners; hardware-render cores need a GL context.
15. **API breaks between releases.** PyBoy `send_input` TypeError after an upgrade (https://github.com/Baekalfen/PyBoy/issues/380);
    nes-py `reset(seed=)` vs Gymnasium wrappers (https://github.com/Kautenja/nes-py/issues/96); libretro.py `active_context` sometimes a
    callable, sometimes a value (https://github.com/JesseTG/libretro.py/issues/19). Class: unstable surface, version drift.
16. **Native crashes in the underlying emulator are the user's problem.** mGBA's tracker is full of crashes on save state, rewind and
    multiplayer windows (https://github.com/mgba-emu/mgba/issues/3442, /3448, /3550). Class: core bugs surfaced through the host.

## 4. Implications for a headless 3DS libretro-core host

- Treat savestate as a versioned container: embed core build id, host version and a platform tag, and refuse mismatches with a clear
  error. Say in the docs that states are not portable across versions (failure modes 5, 8).
- Snapshot everything that affects the next frame: input latch, touch state, RTC, and any frontend-held buffers; then run a
  round-trip test (save, run N, load, run N, compare hashes) in CI (6, 7, 9).
- Zero all guest memory at instance start and offer a deterministic seed for RNG and clock (9, 10).
- Decide the instance model first. If the core keeps process-wide globals, the supported scaling path is one process per instance
  with a pool and clean teardown; say so, and test creating and destroying hundreds of instances for leaks (4, 11).
- Make frame access explicit: zero-copy view with a documented lifetime, plus a copy helper taking a reusable buffer; honour pitch,
  pixel format and rotation; 3DS has two screens of different size, so return them separately (3 of Must, 14).
- Never open an audio device or window by default; collect audio samples into an array or drop them (failure 12, PyBoy issue 405).
- Bound every memory API with a size and fail loudly on a wrong region; avoid iterator protocols over native memory (13).
- Ship wheels for each supported OS/arch and a tested source-build fallback; pin the CPU baseline; test paths with non-ASCII
  characters on Windows (1, 2, 3).
- Keep a small, stable, versioned Python surface; changes behind deprecations (15).
- Hardware-rendered cores need a GL context in the host; plan for that explicitly or document it as a limit (14).
