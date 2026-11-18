# Scripting and automation in standalone emulators

Date: 2026-11-18. Scope: what power users need from the scripting, movie and replay features of BizHawk, mGBA, Dolphin, DeSmuME, melonDS and Citra/Azahar/Lime3DS, and what they report breaking. Sources are docs pages and GitHub issues/PRs; items marked "(inferred)" are my reading, not a cited statement.

## 1. Tools

| Tool | Link | Licence | What it is |
|---|---|---|---|
| BizHawk | https://github.com/TASEmulators/BizHawk | MIT (not shown by the API; from memory) | Multi-system TAS emulator: Lua, movies, TAStudio, rewind, many cores incl. a 3DS (Citra-based) one |
| mGBA | https://mgba.io/docs/scripting.html | MPL-2.0 (https://github.com/mgba-emu/mgba) | GBA/GB emulator with a Lua scripting API (0.10+) |
| Dolphin | https://bugs.dolphin-emu.org/issues/13728 | GPL-2.0+ (API reports NOASSERTION) | GC/Wii emulator; no upstream scripting, only an open feature request |
| Felk's Dolphin fork | https://github.com/Felk/dolphin | as Dolphin | Python scripting fork, minimal API, one listener per event |
| Dolphin Memory Engine | https://github.com/aldelaro5/Dolphin-memory-engine | MIT | External tool that attaches to Dolphin's process to watch/edit guest RAM |
| DeSmuME | https://github.com/TASEmulators/desmume | GPL-2.0 | DS emulator, Lua and .dsm movies; TASVideos no longer recommends it for new TASes (https://tasvideos.org/EmulatorResources/DeSmuME) |
| melonDS | https://github.com/melonDS-emu/melonDS | GPL-3.0 | DS emulator; no scripting, requests open (https://github.com/melonDS-emu/melonDS/issues/561, /462) |
| Azahar | https://github.com/azahar-emu/azahar | GPL-3.0 | 3DS emulator (Citra successor); UDP RPC server, movies (.ctm), savestates, libretro core |
| Lime3DS | https://github.com/Lime3DS/Lime3DS | GPL-3.0 | Citra fork, same RPC lineage (no RPC issues found in its tracker) |

## 2. What must work

### Must
- **Frame stepping under script control.** BizHawk scripts loop on `emu.frameadvance`; forgetting it freezes the UI. `emu.yield` runs a script while paused. https://tasvideos.org/BizHawk/LuaFunctions. mGBA exposes `runFrame()` and a `frame` callback: https://mgba.io/docs/scripting.html. Relied on by: every bot/TAS script, since "press, step N frames, read" is the basic loop.
- **Memory read and write by address, with domains/process selection.** BizHawk `memory`/`mainmemory` domains; mGBA `read8/16/32`, `readRange`, named domains (links above). Azahar RPC ReadMemory/WriteMemory with a selectable process (https://github.com/azahar-emu/azahar/blob/master/src/core/rpc/rpc_server.cpp). Dolphin users go external via DME for the same need (https://github.com/aldelaro5/Dolphin-memory-engine). Relied on by: RAM watches, randomizer connectors, bots.
- **Memory access synchronised with the emulation thread.** Azahar's RPC server was asynchronous; reads of GPU-touched pages crashed the emulator (https://github.com/azahar-emu/azahar/issues/2619) and the fix queues requests to the emulation thread (https://github.com/azahar-emu/azahar/pull/2631, rpc_server.cpp comment on `ENABLE_SCRIPTING_SYNC`).
- **Scriptable input including touch and analog.** Azahar `SetInput` (buttons, home/power, touch, circle pad), held until the next packet (https://github.com/azahar-emu/azahar/pull/2731). mGBA `addKey/setKeys` plus a `keysRead` callback that fires before input is read (mGBA docs). BizHawk `joypad` with analog (LuaFunctions page). Relied on by: bots and replay scripts.
- **Savestates by slot/file/buffer, callable from script.** BizHawk slots plus in-memory `memorysavestate`; mGBA files/slots/buffers with flags (docs above); Azahar `SaveState/LoadState` RPC (https://github.com/azahar-emu/azahar/pull/2730). Relied on by: search/branching bots, TAS re-record, test fixtures.
- **Deterministic replay: same inputs, same result.** Azahar's "Force deterministic async operations" setting exists because "host timings leak into the guest" (https://github.com/azahar-emu/azahar/issues/2587). BizHawk 3DS movies desync too (https://github.com/TASEmulators/BizHawk/issues/4390). Relied on by: TAS, regression tests, many parallel instances giving equal results.
- **Screenshot on demand, as pixels.** Azahar `TakeScreenshot`/`ReadScreenshot` (PNG or raw RGB, 10 s timeout, fails on the software renderer; rpc_server.cpp). mGBA `Core:screenshot(file)`. BizHawk `client.screenshot`. Relied on by: visual checks, bots.

### Should
- **Clean startup from a known state** (power-on vs savestate vs save data). BizHawk issue shows desync when save data is not part of a savestate (https://github.com/TASEmulators/BizHawk/issues/4390 comments); request to record from SRAM/savestate: https://github.com/TASEmulators/BizHawk/issues/4808. Resume-recording request for Citra-family: https://github.com/azahar-emu/azahar/issues/536.
- **Callbacks for lifecycle events** (frame, reset, savestate saved/loaded, rewind). mGBA lists frame/start/stop/reset/keysRead...; callbacks for rewind/stateSaved/stateLoaded are still a request (https://github.com/mgba-emu/mgba/issues/3064), pre-frame callback another (https://github.com/mgba-emu/mgba/issues/3638).
- **Documented, versioned protocol.** Azahar RPC is documented only by `dist/scripting/AzaharRPC.py`; users asked for docs after updates "killed existing RPC scripts" (https://github.com/azahar-emu/azahar/issues/2269). Packets carry a version and wrong ones get an empty reply (rpc_server.cpp).
- **Headless launch of scripts.** BizHawk request to expose `--script` (https://github.com/TASEmulators/BizHawk/issues/3706); mGBA docs describe the Tools-menu route only.
- **Configurable bind address/port, localhost default.** Azahar RPC hard-codes 0.0.0.0:45987 (https://github.com/azahar-emu/azahar/issues/2829).
- **Bulk reads.** BizHawk deprecated `readbyterange` for `read_bytes_as_*` and recommends native integer ops for speed (LuaFunctions page).
- **Fast in-RAM savestates** for slow storage (https://github.com/azahar-emu/azahar/issues/1781, closed).

### Nice
- Breakpoints/execution callbacks (BizHawk `on_bus_*`, request for execution callbacks https://github.com/TASEmulators/BizHawk/issues/2742); GDB stub in Azahar (touched by https://github.com/azahar-emu/azahar/pull/2631).
- Rewind (BizHawk `client.enablerewind`; LuaFunctions page).
- Free camera over RPC (`SetFreeCam`, build-flagged; rpc_server.cpp).
- Perf stats over RPC (`GetPerfStats`; rpc_server.cpp).
- Language-neutral transport: UDP RPC was cited as an advantage over Lua-only (https://github.com/melonDS-emu/melonDS/issues/561). BizHawk `comm` offers HTTP, sockets, memory-mapped files.

### Azahar changes since 2025 (from the PR/issue list)
Merged: RPC toggle setting off by default (#1047, https://github.com/azahar-emu/azahar/pull/1047), RPC setting saved to config (#1129), fix cheats/RPC hitting the wrong process (#956), packet handling and sync (#2631), free camera (#2723), SaveState/LoadState RPC (#2730), SetInput RPC plus DSP sleep timing (#2731). Open: document the RPC (#2269), configurable port/bind (#2829). SendKey/SendSignal PRs (#375, #601) were closed unmerged. Libretro core merged in #1215; "Install the core" #2801 closed. All via `gh` search on azahar-emu/azahar; the RPC set is as listed in rpc_server.cpp (ReadMemory, WriteMemory, ProcessList, SetGetProcess, TakeScreenshot, ReadScreenshot, GetPerfStats, SaveState, LoadState, SetInput, SetFreeCam).

## 3. Failure modes users report

| # | Report | Links | Root-cause class |
|---|---|---|---|
| 1 | .ctm movie desyncs at start; input polls and movie inputs mismatch | https://github.com/azahar-emu/azahar/issues/2587 | Host timing leaking into guest (async data-read delays) |
| 2 | BizHawk 3DS movie desyncs after 80k-450k frames, differs run to run | https://github.com/TASEmulators/BizHawk/issues/4390 | Nondeterminism plus save data not in savestate |
| 3 | Savestate does not carry save data; branching desyncs | https://github.com/TASEmulators/BizHawk/issues/4390, https://github.com/TASEmulators/BizHawk/issues/2175 | State scope incomplete (disk/SRAM outside state) |
| 4 | TAStudio desyncs, hash mismatch on discarding greenzone | https://github.com/TASEmulators/BizHawk/issues/4675, https://github.com/TASEmulators/BizHawk/issues/4079 | Replay/state-cache bookkeeping |
| 5 | RPC memory read crashes emulator while GPU renders, 10 of 10 on VRAM | https://github.com/azahar-emu/azahar/issues/2619 | Cross-thread access to emulator state |
| 6 | Updates "killed existing RPC scripts"; protocol undocumented | https://github.com/azahar-emu/azahar/issues/2269 | Unversioned/undocumented API break |
| 7 | Savestate load crashes when launched by a frontend (Network::Init never ran) | https://github.com/azahar-emu/azahar/issues/2448 | Init path differs per front end |
| 8 | Savestate crashes on every title on one device; crash on load | https://github.com/azahar-emu/azahar/issues/2498, https://github.com/azahar-emu/azahar/issues/761 | Savestate serialisation bugs (LLE modules fixed in #2730) |
| 9 | Savestate freeze/graphics error after load in melonDS | https://github.com/melonDS-emu/melonDS/issues/1884, https://github.com/melonDS-emu/melonDS/issues/1142 | Incomplete state (GPU/timing) |
| 10 | Lua script window makes mGBA lag and input arrive late | https://github.com/mgba-emu/mgba/issues/3071 | Script/UI cost on emulation thread |
| 11 | Frame callback fires 0-160 extra times after reset; callbacks not cleared on reset | https://github.com/mgba-emu/mgba/issues/3625 | Callback lifecycle |
| 12 | `emu:loadFile` breaks savestate menu/hotkeys | https://github.com/mgba-emu/mgba/issues/2804 | Scripting API/emulator state coupling |
| 13 | Input recording by `keysRead` falls apart on reset/savestate use | https://github.com/mgba-emu/mgba/issues/3064 | No lifecycle hooks for replay |
| 14 | API churn: `bit.*`, `onmemoryread`, `readbyterange` deprecated; socket framing changed in 2.6.2 | https://tasvideos.org/BizHawk/LuaFunctions | Scripting API versioning |
| 15 | DeSmuME 0.9.10/0.9.11 sync problems on older movies; mic input must be embedded in movie | https://tasvideos.org/EmulatorResources/DeSmuME | Emulator-version drift; non-button inputs missing from movies |
| 16 | DME watches do not update, hook fails ("no game running") | https://github.com/aldelaro5/Dolphin-memory-engine/issues/287, https://github.com/aldelaro5/Dolphin-memory-engine/issues/286 | External-process attach is fragile |

Touch: I found no report of movies lacking touch; the evidence is that DS microphone had to be embedded separately (row 15) and that Azahar's own RPC input carries touch (#2731). Slow memory polling: only BizHawk's bulk-read advice is documented; no concrete slow-poll issue was found.

## 4. Implications for a headless 3DS libretro-core host

- Determinism is the top risk: expose and default-on the equivalent of "force deterministic async operations", and test replay twice from a clean state (Azahar #2587 shows it is not sufficient alone; inferred).
- Define the state to restore: savestate plus save data/SDMC/NAND. BizHawk's NSMB2 desyncs came from save data outside the state (#4390).
- Drive everything from the single emulation thread (frame-synchronous): memory, input, screenshot, state calls run between `retro_run` calls. This sidesteps the crash class of #2619.
- Input API must carry touch, circle pad and home/power with hold semantics, as Azahar's SetInput does (#2731).
- Provide bulk memory reads and a screenshot path that works with the renderer used, since Azahar's RPC screenshot fails on the software renderer.
- Version the Python API and document it; Azahar users were broken by silent changes (#2269).
- Provide lifecycle events (reset, state loaded) so recording/replay scripts stay consistent (mGBA #3064, #3625).
- Test the frontend init path separately: Azahar #2448 crashed only when launched by a frontend.
- Bind any network surface to localhost by default (#2829).
- Pin the guest clock and RNG seed per instance (inferred; none of the sources above state how Azahar seeds them).
