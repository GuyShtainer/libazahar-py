# P8-04: Emulators driven by RL and by LLM agents

Date: 2026-11-18. Scope: what RL environments built on emulators (Gymnasium, stable-retro, ALE, EnvPool, PyBoy projects)
and LLM-agent harnesses (emulator MCP servers, VideoGameBench) need from the emulator host, and what breaks for their
users. Method: docs pages, READMEs, GitHub issues. Where I found no evidence for a topic, the text says so; absence of a
hit is not proof that users have no problem. The GitHub search API was rate-limited part-way, so issue coverage is thin
for memory growth, leftover processes and GPU contention.

## 1. Tools surveyed

| Tool | Link | Licence | What it is |
|---|---|---|---|
| Gymnasium | https://github.com/Farama-Foundation/Gymnasium | MIT | Standard single-agent RL env API plus vector envs (`SyncVectorEnv`, `AsyncVectorEnv`). |
| Stable-Retro | https://github.com/Farama-Foundation/stable-retro | MIT | Gym-retro fork: console emulator cores as Gymnasium envs, savestate starts, memory-variable rewards. |
| gym-retro (archived) | https://github.com/openai/retro | MIT (per repo) | Original; read-only since 2026-05-29 (per https://github.com/openai/retro/issues/230). |
| ALE | https://github.com/Farama-Foundation/Arcade-Learning-Environment | GPL-2.0 | Atari 2600 reference env: frameskip, sticky actions, C++ threaded vector env. |
| EnvPool | https://github.com/sail-sg/envpool | Apache-2.0 | C++ thread-pool batched env engine, pybind11, `send`/`recv` async API. |
| PyBoy | https://github.com/Baekalfen/PyBoy | custom (see repo) | Python Game Boy emulator with `tick`, memory access, RL example projects. |
| mcp-pyboy | https://github.com/ssimonitch/mcp-pyboy | MIT | MCP server: load ROM, press buttons, capture screen, save/load state, notes. |
| mcp-mgba | https://github.com/dmang-dev/mcp-mgba | MIT | MCP server (Node) bridging to mGBA over a Lua TCP script: memory, input, screenshot, step. |
| Gearboy MCP | https://github.com/drhelius/Gearboy | GPL-3.0 | Emulator with embedded MCP server (stdio/HTTP, `--headless`), also built as a RetroArch core. |
| mcp-openmsx | https://github.com/nataliapc/mcp-openmsx | GPL-2.0 | MCP server automating openMSX: savestates, memory, screen capture, keyboard. |
| VideoGameBench | https://arxiv.org/pdf/2505.18134 | see repo | Benchmark of vision-language models playing 1990s games via PyBoy/DOSBox; ReAct-style scaffold. |

## 2. What must work

### Must

- **Gymnasium-shaped step/reset contract.** `reset()` then `step(action)` returning `obs, reward, terminated, truncated,
  info` (https://stable-retro.farama.org/python/); vector envs return batched arrays of shape `(num_envs,)` and put
  info in one dict of arrays (https://gymnasium.farama.org/api/vector/). RL trainers (stable-baselines3 etc.) rely on it.
- **Precisely defined input latency and hold semantics.** Users repeatedly hit "my press did nothing". PyBoy README
  says to tick at least one frame "to let the game register the input"
  (https://github.com/Baekalfen/PyBoy); PyBoy issue #246 was closed by adding one tick
  (https://github.com/Baekalfen/PyBoy/issues/246). Stable-retro: same input on consecutive frames is a hold; a quick
  re-press needs at least one released frame (https://github.com/Farama-Foundation/Stable-Retro/issues/136). mcp-mgba
  had a bug where repeated presses merged into one, fixed by a FIFO queue
  (https://github.com/dmang-dev/mcp-mgba). The API must state "input set before frame N is visible to the guest in
  frame N+k" and the press/release frame counts.
- **Fast reset from a savestate.** Stable-retro starts episodes from a `.state` file or power-on
  (https://stable-retro.farama.org/python/); mcp-pyboy, mcp-mgba and mcp-openmsx all expose save/load state
  (links in table). RL needs thousands of resets; agents need checkpoints before risky actions.
- **Reward/state from guest memory reads.** Stable-retro puts `data.json` variables into `info` each step and offers a
  RAM observation (https://stable-retro.farama.org/python/); ALE offers a 128-byte RAM observation
  (https://ale.farama.org/environments/); mcp-mgba exposes read8/16/32 and range reads up to 4096 bytes
  (https://github.com/dmang-dev/mcp-mgba). Bounded, explicit-range reads are needed: PyBoy dropped `list(pyboy.memory)`
  because the space is unbounded and it hung (https://github.com/Baekalfen/PyBoy/issues/402).
- **Many parallel instances, with the process-vs-thread model documented.** Gymnasium `AsyncVectorEnv` uses
  subprocesses and pipes, `daemon=True` by default (https://gymnasium.farama.org/api/vector/async_vector_env/);
  ALE and EnvPool use native thread pools, ALE advises `num_envs` near the physical core count
  (https://ale.farama.org/vector-environment/, https://pypi.org/project/envpool/). Emulator cores with global state
  force one instance per process: libretro says "Implementations are designed to be single-instance, so global state is
  allowed" (https://docs.libretro.com/development/cores/developing-cores/); gym-retro refused a second emulator in one
  process (https://github.com/openai/retro/issues/2). A libretro host must therefore choose processes (or isolated
  library copies) and say so.
- **Deterministic seeded runs, with randomness explicit.** ALE is "entirely deterministic" and stochasticity comes only
  from sticky actions (25 % in v5) and frameskip ranges (https://ale.farama.org/environments/); users were misled when
  this was invisible (https://github.com/Farama-Foundation/Arcade-Learning-Environment/issues/166). Stable-retro `.bk2`
  replays reproduce because the emulators are deterministic (https://stable-retro.farama.org/python/).
- **Observation as a numpy array of fixed shape/dtype.** ALE: `uint8 (210,160,3)` rgb, grayscale, or RAM
  (https://ale.farama.org/environments/); stable-retro IMAGE/RAM (https://stable-retro.farama.org/python/).
- **Clean shutdown: `close()` that releases the emulator and no leftover workers.** Gymnasium runs close on GC/exit and
  workers are daemonic (https://gymnasium.farama.org/api/vector/async_vector_env/); a leaked emulator blocks the next
  `make` (https://github.com/openai/retro/issues/2).

### Should

- **Frame-skip / action-repeat in the API.** ALE `frameskip` int or random-range tuple, default 4 in v5
  (https://ale.farama.org/environments/); PyBoy `tick(n, render=False)` skips rendering but game logic still runs
  (https://github.com/Baekalfen/PyBoy). Skip-without-render is the main speed lever; make it a first-class argument.
- **Batched/async stepping.** ALE and EnvPool offer `step` plus `send`/`recv`, with `batch_size` and env IDs in info
  (https://ale.farama.org/vector-environment/, https://pypi.org/project/envpool/). Gymnasium documents autoreset modes
  (next-step default) in `metadata` (https://gymnasium.farama.org/api/vector/).
- **Observation sharing without copies, with ownership stated.** Gymnasium async uses shared memory for large image
  observations and `copy=True` by default (https://gymnasium.farama.org/api/vector/async_vector_env/). The ALE vector
  page does not mention zero-copy (https://ale.farama.org/vector-environment/), so users cannot tell whether a returned
  array is valid after the next step; document it.
- **Screenshot as PNG/image plus text state for LLMs.** mcp-mgba `screenshot` saves a PNG; return format is
  unspecified in its README (https://github.com/dmang-dev/mcp-mgba). mcp-pyboy lists capture_screen and a per-game notes
  store (https://github.com/ssimonitch/mcp-pyboy). VideoGameBench gives the model raw frames only and forbids RAM access
  for its benchmark (https://arxiv.org/pdf/2505.18134), while homebrew-dev MCPs expose memory on purpose.
- **Pause-while-thinking control.** VideoGameBench Lite pauses the emulator during model inference and resumes it only
  to execute the action (https://arxiv.org/pdf/2505.18134). Agent harnesses need pause/step/advance_frames
  (https://github.com/dmang-dev/mcp-mgba).
- **Input as named buttons, queued, with explicit frame duration** (mcp-mgba button list and FIFO queue; mcp-pyboy
  `press_button`/`hold_button`/`release_button`/`send_input_sequence`, https://github.com/ssimonitch/mcp-pyboy).
- **Seed validation tests across parallel envs.** EnvPool found resets ignoring the seed that still passed a same-seed
  equality test (https://github.com/sail-sg/envpool/pull/434); ALE found a vector env that skipped seed 0
  (https://github.com/Farama-Foundation/Arcade-Learning-Environment/pull/603).

### Nice

- **Replay/movie recording of inputs** (`.bk2`, small, deterministic playback) (https://stable-retro.farama.org/python/).
- **CPU affinity / thread pinning option** (ALE `thread_affinity_offset`, https://ale.farama.org/vector-environment/;
  EnvPool NUMA mode, https://pypi.org/project/envpool/).
- **Compact tool routing and stdio plus HTTP MCP transports** (Gearboy `--mcp-router`, https://github.com/drhelius/Gearboy;
  mcp-openmsx hybrid stdio/HTTP, https://github.com/nataliapc/mcp-openmsx).
- **Capability discovery** so a client can ask what the host supports (mcp-mgba `get_info` capabilities because some
  builds lack pause/frameAdvance, https://github.com/dmang-dev/mcp-mgba).
- **Prebuilt wheels per platform with stated limits** (EnvPool lists Linux, Windows x64, macOS 13+ arm64 only,
  https://pypi.org/project/envpool/).

## 3. Failure modes users report

1. **Memory grows on repeated `reset()`.** Gym-retro Pong: process memory rose on each reset, macOS immediately, Linux
   intermittently; never root-caused, repo now archived. https://github.com/openai/retro/issues/230 (a fix PR exists:
   https://github.com/openai/retro/pull/156). Root cause class: native resource leak across reset/load-state (unconfirmed).
2. **Second emulator in the same process refused.** `RuntimeError: Cannot create multiple emulator instances per
   process`; an old emulator was still alive. https://github.com/openai/retro/issues/2 . Class: global state in the core
   plus lifetime/GC of the previous instance.
3. **Stochasticity hidden from users.** Researchers assumed ALE was deterministic, got sticky actions; wasted research
   time; the project later made randomness explicit. https://github.com/Farama-Foundation/Arcade-Learning-Environment/issues/166
   . Class: undocumented default randomness.
4. **Vector env not seeded when seed is 0.** https://github.com/Farama-Foundation/Arcade-Learning-Environment/pull/603 .
   Class: falsy-value check in seeding code.
5. **Reset ignores its seed yet passes the equality test.** https://github.com/sail-sg/envpool/pull/434 . Class: test
   too weak to catch frozen state; need variation-across-seeds checks.
6. **Input "ignored".** Button sent but the game never saw it until a tick was added.
   https://github.com/Baekalfen/PyBoy/issues/246 . Class: input latency/semantics not obvious (also
   https://github.com/Farama-Foundation/Stable-Retro/issues/136 for hold vs re-press). Related: old mcp-mgba merged
   repeated presses (https://github.com/dmang-dev/mcp-mgba).
7. **Async vector step hangs forever when fewer actions than envs.** Only some pipes got the command, `step_wait` blocked
   on the rest. https://github.com/Farama-Foundation/Gymnasium/issues/1417 (fix PR
   https://github.com/Farama-Foundation/Gymnasium/pull/1419). Class: no argument validation before cross-process wait.
8. **Worker crash surfaces as a misleading `ConnectionResetError`.** The worker died on a wrapper attribute error before
   sending its spaces; the parent only saw the broken pipe. https://github.com/Farama-Foundation/Stable-Retro/issues/112
   . Class: worker failure reporting; wrapper/API mismatch.
9. **Unbounded memory iteration hangs and eats RAM.** `list(pyboy.memory)` stalled and consumed RAM.
   https://github.com/Baekalfen/PyBoy/issues/402 . Class: API without a length or bounds; guest-memory side effects on
   read handlers (suspected, unconfirmed).
10. **Segfault at large batch sizes.** EnvPool Atari crashed when batch size exceeded 255.
    https://github.com/sail-sg/envpool/issues/152 . Class: fixed-width index/overflow in native batching (fix:
    https://github.com/sail-sg/envpool/pull/284 for a related segfault).
11. **Bridge port stuck or stale after a crash/reload.** mcp-mgba: `bind failed` when a previous instance still holds
    port 8765; stale behaviour after hot-reloading the script; tool calls hang when the script errored.
    https://github.com/dmang-dev/mcp-mgba . Class: leftover process/socket state; no health check or restart.
12. **Intermittent memory read failures.** mcp-mgba notes "invoking failed" on `read8/16/32`, cleared by retry.
    https://github.com/dmang-dev/mcp-mgba . Class: unreliable scripting-bridge call path.
13. **Save states glitchy or runahead artifacts in a libretro core.** GB/GBC save states glitchy
    https://github.com/libretro/mgba/issues/126 ; runahead artifacts/skips after a core update
    https://github.com/libretro/mgba/issues/222 . Class: incomplete serialization of core state. Libretro only requires
    that the serialize size never grow between load and unload and does not promise determinism
    (https://docs.libretro.com/development/cores/developing-cores/).
14. **Platform and wheel limits.** EnvPool Python 3.12+ only; macOS arm64 only; Linux rendering needs system EGL/OpenGL
    packages; Windows CI uses Mesa software OpenGL. https://pypi.org/project/envpool/ . Class: native dependencies and GPU
    context. I found no direct issue on GPU contention between many emulator instances; this is a gap, not a clean bill.
15. **Real-time latency confounds agent results.** Model inference time makes real-time games unwinnable; the benchmark
    added a paused variant. https://arxiv.org/pdf/2505.18134 . Class: harness must decouple wall-clock from guest time.

## 4. Implications for a headless 3DS libretro-core host

- Treat each emulator as one process, or one isolated library copy: libretro cores may keep global state and give no
  thread-safety promise (https://docs.libretro.com/development/cores/developing-cores/), and gym-retro shows the failure.
  Document process-per-instance and give a supervisor that reaps workers and reports why a worker died (items 2, 8, 11).
- Define and test input latency: state in frames when a press becomes visible, the minimum release gap, and a hold API
  (items 6; PyBoy and stable-retro precedent).
- Make `run_frames(n, render=False)` the frame-skip primitive, with video not copied or converted unless requested.
- State array ownership: either a view valid until the next run call or an explicit copy flag; copy cost is the usual
  hidden cost (Gymnasium `copy=True` default).
- Savestate must be a tested round trip: save, run N frames, load, run N frames, compare frame hashes and guest memory.
  Serialize size must be stable per libretro rules; run this check on every core version (item 13).
- Offer explicit seeds plus a "deterministic" flag that lists every randomness source (RTC, RNG seeds, sticky input),
  and test that different seeds differ and same seeds match (items 3-5).
- Bounded memory-read API (address plus length, with a cap) and typed helpers for reward code; never an iterable over
  guest memory (item 9).
- Provide screenshot (image) and a compact text state (button state, frame counter, chosen memory fields) for LLM tools,
  plus pause/advance semantics so agent latency does not run the guest (item 15). Report capabilities to clients.
- Long-run tests: millions of reset/load-state cycles watching RSS and open handles; crash-kill tests that verify no
  orphan processes, ports or temp files (items 1, 11).
- Many-instance GPU use is unmeasured in the sources I found; test a software-rendering path and the shared-GPU path
  separately before promising either.
