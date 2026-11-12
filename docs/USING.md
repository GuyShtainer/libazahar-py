# Using libazahar-py

A headless Azahar for 3DS homebrew: no window, many copies at once, inputs, screenshots, SD files, savestates.
Plain sections; no speed claim here comes from the test app (an idle app proves nothing about a real scene).

## 1. Install

`python3 -m venv .venv && .venv/bin/pip install -e .` (the worker runs `python -I`, so a venv, not the user site).
Editable install only: the package finds the repo (`build/`, `dl/`, `host/`) from its own folder; a plain install
must set `LAZ_ROOT`. `make` builds the host; `tools/fetch.sh` fetches the stock core and MoltenVK.

## 2. Paths and environment

`LAZ_ROOT` (repo folder), `LAZ_HOST` (the worker's host library), `LAZ_CORE` (the core), `LAZ_MVK` (MoltenVK),
`LAZ_PROFILE`, `LAZ_LOG_LEVEL`, `LAZ_ANY_CORE`, `LAZ_STATE_ANY_APP` (see section 10), `LAZ_REQUIRE_EMULATOR` (tests:
a missing emulator fails instead of skipping), `MVK_CONFIG_LOG_LEVEL` (1 unless set). An instance folder `workdir/`
holds `host.log`, `host.map`, `shots/` and `sys/Azahar/sdmc/` (the SD card; `emu.sd` is that path). `sd_seed` is a
folder (never named `sdmc`) whose contents are copied onto the SD card: before boot, or with `state=` after the
restore, so seed files land on top of the snapshot.

## 3. Frames

One `run` frame is one guest VBlank. Frames are 1-based inside a batch (`run(10, inputs=[(1, ...)])` acts on the
first frame). Shot names carry absolute frame numbers. `frame_total` counts every frame since boot. The frame the
guest exits on counts. `RunResult.wall_s` is the batch's wall time; `azhost run` prints one summary per batch,
`frames= wall= fps= shots= stop= first= last= vblanks= wall_ms_mean= batch= msg=` (the mean frame time; there is no
max).

## 4. Inputs

`inputs` is a movie: `(frame, item)` pairs, held across batches. A `Buttons` value (libctru `KEY_*` names, also
`UP/DOWN/LEFT/RIGHT`) replaces the whole held mask; `Touch` and `Circle` change only their part. Several changes in
one frame fold into one. `set_input` and `set_keys(raw=...)` set held state for the next run.

Measured offsets (step C, test app on our host): a change made at batch frame f shows in the guest's log line of host
frame f + m, or sometimes f + m + 1. Buttons (A and others): m = 0 (counts 0: 1, 1: 29 over 30 changes; the first
one lands on f, the rest on f + 1); ZL/ZR (irrst path): m = 1 (6 of 6); circle pad: m = 1 (5 of 5); touch: m = 2
(40 of 40). Plan checks with a tolerance of one frame. Poll-exact movies need our patched core.

## 5. Touch

Pixel coordinates on the bottom screen (320x240). Four rows move by one because HID truncates a float, as in Qt
Azahar: y 63 -> 62, 125 -> 124, 126 -> 125, 127 -> 126. No cursor is drawn.

## 6. Circle pad

`Circle(x, y)` takes -32767..32767; up is positive; 32767 gives 154 in the guest. The guest averages 3 polls, so a
change shows with one in-between frame.

## 7. Stops

`RunResult.stopped_by` is one of: `frames` (the batch ran out), `sd_text` (the SD text rule matched), `debug_text`
(our core only), `guest_break`, `guest_exited`, `guest_error`, `wall_limit`. A guest crash is `guest_error`; a
`svcBreak` or `bkpt` is `guest_break` and the guest runs on after it.

SD text rule: every `stop_every` frames (and after the last) the file is read from the SD folder; `stop_new` looks
only at text written after the batch began; matches split across reads are found; a file that shrinks is read again
from its start. Debug text needs our core: on the stock core the core's log runs on its own thread, so a hit could
arrive frames late.

The one guest-error rule: `GuestError` is raised when `stopped_by == "guest_error"` on either core (the Emulator stays
open; `error.result` holds the RunResult), and also when the host exits with code 11 (the Emulator is closed). A
guest exit with no error is a normal `guest_exited` result, and after it the Emulator is closed, on both cores (on
our core the worker is shut down cleanly once the result is built).

`azh_result.message` is the stopping kind's message cut to 255 bytes. The map's message (1023 bytes, with `msg_seq`)
and `host.log` hold more. Messages that arrive while the host drains for a savestate are not reported as stops;
each is in `host.log` as a `core message:` line.

## 8. Errors and timeouts

`LibAzaharError` is the base. `BootError`: core, Vulkan or the app failed to start. `GuestError`: section 7.
`HostTimeout`: the heartbeat stopped for `timeout` seconds (Emulator-wide default 30, or per call); the worker is
killed and reaped. `HostCrashed`: the worker died (a signal gives a negative code). `StateError`: section 10.
`NeedsLazpyCore`: the call needs our patched core. `HostError`: wrong call order, I/O, memory, ABI mismatch, missing
host, an unsupported call, a guest exit outside `run`. `ValueError` for bad arguments. The crash tests leave a macOS
crash report each run. On the stock core a guest-exit result has `wall_s` 0.0 and no `shots`. `boot_timeout`
(default 300 s) covers boot and the first frames' shader compiles. A long batch is not a hang while the heartbeat moves.

## 9. Screens

`screens()` returns numpy views (top 400x240, bottom 320x240, read-only) that change at the next raw shot; `.copy()`
to keep one. `shots=[frames]` saves PNGs and returns them in `result.shots`.

## 10. Savestates

`save_state(path)` writes three files: the state, its meta and an SD snapshot (`<path>.sd`); it makes the parent
folder. `SaveInfo.k >= 0`: a state taken at frame N is at N + k. `Emulator(app, workdir, state=path)` boots the app,
checks its sha256 against the meta (the core's own program-id check does nothing for a `.3dsx`; set
`LAZ_STATE_ANY_APP=1` after a deliberate rebuild), restores the SD snapshot (then the seed on top) and the state. States
may not survive a core change. NAND files are not snapshotted (they reopen from the new instance's NAND) and the
app's RomFS reopens from the new app path. `load_state` replaces the SD folder: read logs before it. Restore steps
are timed in `host.log` (`state load ...`). Reusing an instance's `sys/` folder (without `Azahar/sdmc/`) keeps the
shader cache. Gate on the test app (Guy's ruling): a state boot takes under 2.5 s (1.6 s
measured); a real game's state is larger, so time your own. A `load_state` that fails after the SD folder was replaced
leaves the instance unusable (later calls raise HostError); close it and boot again. The meta's `app=` is the absolute
app path, so a shared state carries it. An I/O failure while saving is a HostError, not a StateError.

## 11. Stock core and our core

Stock: SD text stops, guest errors, savestates (the same log fields after a state restore, gated on the test app).
Repeats are exact only on our core, where the repeat gates run (PLAN 2.4); on the stock core they record the
difference only. Our patched core adds debug text, memory reads (Phase
G) and poll-exact movies if Phase F confirms them. Calls that need it raise `NeedsLazpyCore`.

## 12. The Gen3D mapping

Rows 1-17 of docs/research/gen3d-harness-needs.md:

| Gen3D mechanism | libazahar-py |
|---|---|
| 1 Qt profile pins | `options` |
| 2 SD staging | `sd_seed` |
| 3 locks, focus, bundle clones | dropped (plain processes, own folders) |
| 4 curtain window | dropped (no pacing) |
| 5 CTM movies | `inputs` (poll-exact needs our core) |
| 6, 7 SD control channel, netlogs | `emu.sd` files and `run_until` |
| 8 `voxel.log` flip lines | `emu.sd` file and `run_until` |
| 9 window screenshots | `shots` / `screens()` (400x240 top, 320x240 bottom) |
| 10 framebuffer via gdb | `screens()` |
| 11, 12 gdb RAM reads | Phase G `emu.memory` (the test app's 32-byte record: magic 0, frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24) or an app log line |
| 13 `see rec` | `shots` with frame numbers |
| 14 `gdbio resume` | gone |
| 15, 16 savewarp, picture judges | unchanged |
| 17 savestates | `save_state` and `Emulator(state=)` |

Forced-mode seed: a seed folder holding the app's control file, so one Emulator boots straight into a mode (the test
app's control.txt shows it). For the long world build: boot once, `save_state`, start every test from the state, and
reuse the instance folder's `sys/` for the shader cache.
