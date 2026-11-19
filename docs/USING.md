# Using libazahar-py

A headless Azahar for 3DS homebrew: no window, many copies at once, inputs, screenshots, SD files, savestates, and
guest memory on our own core. Plain sections. This guide makes no speed claim; the README's table has the numbers, each
with its scene, load and date. "The stock core" means Azahar's own libretro core; "our core" is the patched build
(`azahar_lazpy_libretro`, section 17).

The promise (semantic versioning from 1.0.0): until 2.0, these change only in compatible ways, and additions come in
minor releases. They are `libazahar.__all__` (names, arguments, return types, error classes), the C functions in
`host/azhost.h` at source level (names and meaning; struct layouts may grow, so C callers rebuild for each release),
the `azhost` command line with its exit codes and summary keys (section 3), the input-script format (section 4a), the
option-profile format (section 14) and the first table of section 15. The host library and the Python package are one
unit: use both from one checkout or one release. A savestate loads in later 1.x releases on the same core revision.

## 1. Install

`python3 -m venv .venv && .venv/bin/pip install -e .` (the worker runs `python -I`, so a venv, not the user site).
Editable install only: the package finds the repo (`build/`, `dl/`, `host/`) from its own folder; a plain install
must set `LAZ_ROOT`. Needs macOS 15 or later on Apple silicon, or Windows x64 (section 15a), and Python 3.10 or newer (macOS's own `python3` is 3.9).
`make` builds the host; `sh tools/fetch.sh --moltenvk --headers --lazpy-core --testapp` fetches MoltenVK, the headers,
our core and the test app, each sha256-pinned. The README's Install section is the full route, with its own Windows steps.

## 2. Paths and environment

Every variable is in the table in section 15. An instance folder `workdir/` holds `host.log`, `host.map`, `shots/` and
`sys/Azahar/sdmc/` (the SD card; `emu.sd` is that path). `sd_seed` is a folder (never named `sdmc`) whose contents are
copied onto the SD card: before boot, or with `state=` after the restore, so seed files land on top of the snapshot.
Reusing `workdir` keeps everything under `sys/`, the SD included; `sd_seed` is copied on top and nothing is cleared. For
a warm shader cache and a clean SD, pass `fresh_sd=True`: it empties `workdir/sys/Azahar/sdmc/` before the seed is
copied and keeps the rest of `sys/` (it refuses an SD folder that is a symlink).

## 2a. The command line

`python -m libazahar --help` lists two commands, and each has its own `--help`. Nothing here needs more than the
standard library. The package declares no console script, so use `python -m libazahar`.

`python -m libazahar doctor` prints the OS, Python, the host library (path and ABI number), the core (path), the slots
in use and, if `build/testapp.3dsx` is present, a 60-frame boot of the test app with the core's name and version and the
Vulkan device lines from that boot's `host.log` (`vulkan: unknown` when there was no boot or the log has none). It exits
0 when every part works, else 1. The slot check takes each free slot for a moment to see which are held. The PIDs of the
holders come from `lsof` where it exists and read `unknown` elsewhere, Windows included.

`python -m libazahar run APP --frames N [--inputs FILE] [--shot F ...] [--state P] [--save P] [--json]` boots `APP`,
runs `N` frames and prints one summary line (`frames= stop= first= last= vblanks= wall=`), the shot paths, and the
working folder. `--inputs` reads the script of section 4a; its records are the whole held state, so each becomes the
button mask, a touch or a lift, and the circle pad on that frame. `--shot` is a batch frame and may repeat. `--state`
boots from a savestate and `--save` writes one after the run (not after a guest exit). `--workdir DIR`, `--sd-seed DIR`
and `--timeout S` set the working folder (default: a new temporary one, which is kept), the SD seed and the no-progress
limit.

`--json` prints one object. On success: `ok`, `exit_code`, `workdir`, `result` (every field of `RunResult`, with the
paths of the shots; arrays and bytes are left out) and `saved` (or `null`). On an error: `ok` false, `exit_code`,
`workdir` and `error` with `class`, `message`, `workdir` and `log_path` (the last two are `null` when the error has no
instance behind it). The exit codes are those of section 3: 0, 2 (a bad argument or flag), 3 (boot failed), 10 (the guest
exited), 11 (a guest error), 12 (timed out), 13 (the worker or host crashed or could not run). The command never
returns 1.

## 3. Frames

One `run` frame is one guest VBlank. Frames are 1-based inside a batch (`run(10, inputs=[(1, ...)])` acts on the
first frame). `inputs` and `shots` take batch frames 1..`frames`; anything else raises `ArgumentError` (a `LibAzaharError`
that is also a `ValueError`). Shot names carry absolute frame numbers: `result.shots` is keyed by the batch frame
you asked for (`Shot.frame`); the file name holds the frame since boot, `first_frame + f - 1` (`Shot.frame_total`). `timeout` is a no-progress limit: seconds with no new frame
(default 30), not a bound on the batch, so a long batch needs no big value. Use `wall_limit` for a wall bound. Raise
`timeout` only when one frame can stall long (first shader compiles mid-run). `frame_total` counts every frame since boot. The frame the
guest exits on counts. `RunResult.wall_s` is the batch's wall time; `azhost run` prints one summary per batch,
`frames= wall= fps= shots= stop= first= last= vblanks= wall_ms_mean= batch= msg=` (the mean frame time; there is no
max).

`run` takes the number of frames as its only positional argument; every other option (`inputs`, `shots`, `stop_file`,
`stop_text`, `stop_every`, `stop_new`, `debug_text`, `wall_limit`, `timeout`, `watch`, `watch_every`) is keyword-only.
`run_until(file, text, max_frames, ...)` takes the same options under the same names. `frames` and every entry of
`shots`, and `stop_every`, must be whole numbers (a numpy integer is fine; `1.5`, `True` and strings raise
`ArgumentError`). `wall_limit`, `timeout` and `boot_timeout` must be numbers (not a bool or NaN), else `ArgumentError`.
`watch_every` is 1 to 100000. `Shot.top` and `Shot.bottom` are `pathlib.Path` values, and `Shot.frame_total` is always
set. `RunResult` is a frozen dataclass whose `shots` is a dict: two results compare by equality but are not hashable.

The `azhost` exit codes:

| Code | Meaning |
|---|---|
| 0 | Every batch ran. The stop reason is in each summary line (`frames`, `sd_text`, `debug_text`, `guest_break`, `wall_limit`). |
| 2 | Usage: a bad flag or value, a bad profile or input-script line, an unknown option key or value. |
| 3 | The app failed to boot. |
| 4 | The core failed to load or has an unknown version. |
| 5 | Vulkan or MoltenVK failed. |
| 6 | I/O or out of memory: an unreadable profile or input script; a seed copy that fails; an unwritable `--out` or `--sys`; a `--save` file that cannot be written. A missing or refused seed folder is a usage error (2). |
| 7 | The run needs our core, for example `--debug-stop` on the stock core. |
| 8 | Unsupported request, for example `--raw-shot` at a resolution factor other than 1. |
| 9 | A savestate could not be loaded (`--state`), or `--save` could not drain or serialize the state (a write failure is 6). |
| 10 | The guest exited. Our core: the batch's summary line (`stop=guest_exited`) comes first. Stock core: the process exits from inside the run, with no summary for that batch. |
| 11 | A guest error ended the run. Our core: summary first (`stop=guest_error`). Stock core: none. |
| 128+n | Killed by signal n (shown by the shell; azhost never returns it itself). |

Codes 1, 12 and 13 are the verdict codes of scripts built on the package; `azhost` itself does not return them.
`examples/verdict.py` exits by this one table: 1 the test failed (the app reported a failure, or never reported a
pass), 12 timed out and the worker was killed (`HostTimeout`), 13 the worker or host crashed (`HostCrashed`), or the
host could not run at all (`HostError`, `StateError`, or no instance slot free), and 2, 3, 10 and 11 as above for a bad
argument, a boot failure, a guest exit and a guest error. An uncaught Python exception in your own script also exits 1,
so a bug in the script reads as a failed test; catch what you can tell apart. Codes 14 to 127 are reserved.

Summary-line keys are frozen: `frames wall fps shots stop first last vblanks wall_ms_mean batch msg`. Units: `wall` is
in seconds, `wall_ms_mean` in milliseconds, `batch` counts from 1. New keys are inserted before `msg`, which is always
last and escapes `\` as `\\`, a newline as `\n` and `"` as `\"`; a `\r` is dropped. The stdout lines `saved k= frame=` and `last N:` are
frozen too. The `Class: text` line on stderr is for people and is outside the promise.

## 4. Inputs

`inputs` is a movie: `(frame, item)` pairs, held across batches. A `Buttons` value (libctru `KEY_*` names, also
`UP/DOWN/LEFT/RIGHT`) replaces the whole held mask; `Touch` and `Circle` change only their part. Several changes in
one frame fold into one. `set_input` and `set_keys(raw=...)` set held state for the next run.

Measured offsets (step C, test app on our host): a change made at batch frame f shows in the guest's log line of host
frame f + m, or sometimes f + m + 1. Buttons (A and others): m = 0 (counts 0: 1, 1: 29 over 30 changes; the first
one lands on f, the rest on f + 1); ZL/ZR (irrst path): m = 1 (6 of 6); circle pad: m = 1 (5 of 5); touch: m = 2
(40 of 40). Plan checks with a tolerance of one frame.

Pressing again: a release of one frame between two presses reaches the guest as two presses. Checked with the test app
on Windows, for A, for ZL and ZR (the other service) and for a touch lift and re-tap, with gaps of 1, 2 and 3 frames:
the log shows two presses each time, so one frame is enough. Write the release and the second press as two items, for
example `(f, Buttons.A), (f + 6, Buttons(0)), (f + 7, Buttons.A)`. Two items for one button on the same frame fold into
one, so a press-release-press needs separate frames. Inputs are applied by the host at frame boundaries, so a change lands a frame or two after the frame you name (the
offsets above). A movie that fixes the input at every poll of the guest, from boot, is not available from Python: the
Azahar movie format stores the pad, touch and extra-pad (ZL, ZR, C-stick) records in one stream, and the order of the
extra-pad records depends on when the app starts that service, which a caller cannot know. Our core exports the movie
call and the host can pass it a file (`azh_movie_play`, `docs/HOST-API.md`), but a correct movie needs a change to the core
first; there is no `exact_inputs` option.

## 4a. The input script (`azhost --inputs FILE`)

One record per line: `frame buttons touch_x touch_y touch_down circle_x circle_y`. That is 7 int32 fields separated by
spaces, tabs or commas. Each field is decimal (with an optional `-`) or `0x` / `0X` hex. A leading `0` does not mean
octal: `010` is 10 and `0x10` is 16; `0x0x10` is an error.

- A `#` anywhere starts a comment that runs to the end of the line. Blank lines are skipped.
- A line is at most 511 bytes (a comment included; one trailing `\r` is dropped first). A longer line, or a line
  holding a NUL byte, is an error that names the line number.
- Each record is the whole held state from its frame on. This differs from the Python `inputs` items, where each item
  changes only its own part (buttons, touch or circle).
- The script applies to the first batch only. A script has at most 1,000,000 records and 4,000,000 lines; data past
  that is an error at line 4000001, never a silent cut.
- A bad line prints `UsageError: <file> line N: ...` and exits 2; an unreadable file exits 6.

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

Every successful batch writes one timing line (`batch frames=...`) to `host.log`, so a script that calls `run(1)` once
per frame grows `host.log` by about a line per frame.

## 8. Errors and timeouts

The macOS check that a worker ends when its caller dies has not been run live yet (see "When the caller dies" below).
`LibAzaharError` is the base. `BootError`: core, Vulkan or the app failed to start. `GuestError`: section 7.
`HostTimeout`: the heartbeat stopped for `timeout` seconds (Emulator-wide default 30, or per call); the worker is
killed and reaped. `SlotTimeout` is a `HostTimeout` (`.op == "slot"`, `.seconds`) raised when no machine-wide slot
frees up (section 13). `HostCrashed`: the worker died (a signal gives a negative code). Every error class survives
pickling, so errors cross a process pool. `StateError`: section 10.
`NeedsLazpyCore`: the call needs our patched core. `HostError`: wrong call order, I/O, memory, ABI mismatch, missing
host, an unsupported call, a guest exit outside `run`. `ArgumentError` (also a `ValueError`) for every bad argument. The crash tests leave a macOS
crash report each run. On the stock core a guest-exit result has `wall_s` 0.0 and no `shots`. `boot_timeout`
(default 300 s) covers boot and the first frames' shader compiles. A long batch is not a hang while the heartbeat moves.

| Call | Raises |
|---|---|
| `Emulator(...)` | `ArgumentError`, `BootError`, `HostError`, `SlotTimeout`, `HostTimeout`, `HostCrashed` |
| `run`, `run_until`, `run_frame` | `ArgumentError`, `GuestError`, `NeedsLazpyCore`, `HostTimeout`, `HostCrashed`, `HostError` |
| `save_state`, `load_state` | `StateError`, or `HostError` for an I/O failure |
| `memory` calls | `GuestMemoryError`, `NeedsLazpyCore`, `ArgumentError`, or `TypeError` for data that is not bytes |
| any call after `close()` | `HostError` |

**Evidence.** Every error raised once the worker has started (`BootError`, `GuestError`, `HostTimeout`, `HostCrashed`,
`StateError`, `HostError`, `GuestMemoryError`) has `.workdir` and `.log_path` (the folder and its `host.log`), and its
text ends with a line naming `host.log` and the newest shot under `shots/` (both PNGs of the pair, so it does not
matter which one the file system stamps later), or saying no shot was taken. The shot folder is read when the text is first asked for. That shot is
the newest one taken, not the frame at the failure. The two fields survive pickling. Other errors have both as `None`. So do errors raised before the worker exists: `SlotTimeout`, a missing host library, a
working folder that cannot be made, an unreadable option profile, and a missing core. The core error cannot name a
`host.log` that was never written.

**When the caller dies.** On Windows (live check run) and macOS (live check not yet run) a worker ends when its caller
dies, however the caller dies, and its slot is free again. On Windows each worker is put in one Job object with kill-on-close (made at the first spawn), so even a worker inside a
long batch ends with its caller; if the job cannot be made, one `RuntimeWarning` says so and the worker then ends only
when the caller dies between batches. On macOS the worker watches its caller's process through `kqueue` and exits at
once, mid-batch too. On Linux a worker ends only between batches (when the pipe closes); a caller that may be killed
mid-batch should end the worker itself first (`close()`). The macOS path is covered by unit tests with a stand-in
`kqueue`; its live check has not been run yet.

A missing `sd_seed` folder is an `ArgumentError`; a `workdir` that cannot be made is a `HostError` naming the path; an
unreadable option profile is a `HostError`; a profile line that
breaks the format (section 14) is an `ArgumentError` naming the file and the line. `SlotTimeout` and `LoadWarning`
are defined in `libazahar.errors`. The promise is `libazahar.__all__`; `libazahar.errors` stays importable.

## 9. Screens

`screens()` returns numpy views if numpy is installed (`pip install '.[numpy]'`), else `bytes`: top 400x240, bottom
320x240, read-only, and they change at the next raw shot; `.copy()` (numpy) to keep one. `shots=[frames]` saves PNGs and returns them in `result.shots`.

`shot(prefix)` returns the two PNG paths as a tuple of `pathlib.Path`, and `result.shots[f].top` / `.bottom` are
`Path` values too. Code that needs a string calls `str(path)`.

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

`SaveInfo.path` is a `pathlib.Path` (resolved, absolute).

## 10a. What repeats

A run is repeatable when every input in this table is fixed. Same app, same options, same inputs and a fresh working
folder give the same screens and the same guest-visible state, measured on the test app at frames 300 and 600 with
`libazahar.images.digest` and the app's log (`tests/python/test_determinism.py`). Two inputs are not fixed, and each is
named here so a test does not lean on it. The last column of the table says, for each row, whether the test measures it
(measured) or the row is read from the option profile and the code (from the code).

| Input | Fixed? | What reaches it | Basis |
|---|---|---|---|
| Tick seed and clock base (`core/options-lazpy.txt`: fixed ticks, fixed start time) | Fixed on our core. `citra_init_ticks_override` picks the seed (section 14); two seeds give a different tick count, and the guest's clock reading shifts with it (a seed of 1000000 ticks moves `osGetTime` by about 3 to 4 ms) | `svcGetSystemTick`, `osGetTime`, `time()` | measured (tick count and `osGetTime` reading; `time()` from the code) |
| Asynchronous file and service timing (deterministic async operations, async file system off) | Fixed on our core. The stock core ignores some of these options, so the profile in force is itself an input: compare runs only under one core and one profile | any call that waits on the file system or a service | from the code |
| Random bytes from the process and SSL services | Not fixed. They come from the host's own randomness; fixing them needs a core change | `PS_GenerateRandomBytes`, `SSLC_GenerateRandomData` | from the code |
| Console ID and Wi-Fi MAC | A fresh working folder draws them at random, so they are not fixed there. A reused folder keeps the ones it drew | the services that return the console's unique ID and MAC | from the code |
| Working folder reuse (SD, NAND, config, shader cache) | Fixed only if the folder is the same. Use a new folder for each run you want to repeat (`fresh_sd=True` clears just the SD) | every file the app reads or writes | measured (fresh folders repeat); the rest from the code |
| Held input across `load_state` | Kept: `load_state` does not change the held buttons, touch or circle pad, and does not restore the ones in the state. A new `Emulator(state=...)` starts with nothing held | `run` inputs, `set_input` | measured |

For an app that reads the console ID or MAC: a fresh folder gives a different ID each run, so keep one folder and reset
only the SD. Run the first time in that folder to draw the ID, then boot each repeat in the same folder with
`fresh_sd=True` (it clears the SD and keeps the config, so the ID stays). Do not use a new folder per run for such an app.

Held input in practice: input is held "across batches" (section 4). Holding A, saving, loading the state and running
on leaves A down; booting a second instance from that state leaves A up. Release everything with `set_input` before a
reset so the next run starts clean.

## 11. Stock core and our core

Stock: SD text stops, guest errors, savestates (the same log fields after a state restore, gated on the test app).
Repeats are exact only on our core, where the repeat gates run (PLAN 2.4); on the stock core they record the
difference only. Our patched core adds debug text, memory reads and the watch list (section 12a). It also exports a
movie call; the host can pass it a file, Python does not (section 4). Calls that need our core raise `NeedsLazpyCore`. The table of
both cores is in section 16.

## 12a. Guest memory (our core only)

`emu.memory.read(addr, n)` returns `n` bytes at a guest virtual address of the running app's process;
`write(addr, data)` stores bytes. Widths `u8 u16 u32 u64 s8 s16 s32 s64` are callable (`emu.memory.u32(addr)`) and have
`raw_read(addr)` and `raw_write(addr, value)` (libmgba-py's names); `write_u8 .. write_u64` are range-checked,
little-endian. Calls happen between batches. The guest may be part-way into a frame, so a record of several fields can
be torn (some fields from the frame before); the watch list has the same property. A range with an unmapped page
(address 0 included) raises `GuestMemoryError` (`.addr`, `.length`); a failed write changes nothing. A bad range
(negative, past 4 GiB, length 0 or over 64 MiB) is an `ArgumentError`. On the stock core every memory call and every
`watch=` raises `NeedsLazpyCore`.

**Watch list.** `run(frames, watch=[(addr, words), ...], watch_every=1)`: at most 32 entries of 1..256 u32 words. After
every `watch_every`-th batch frame, and after the last frame run, the host reads each entry; `result.watch` is a tuple
of `WatchRow(frame, status, data)` (`frame` absolute, `data` one `bytes` per entry, `row.u32(entry, word)`). An
unmapped entry reads as zeros and sets the row status (`AZH_E_UNMAPPED`), the batch goes on. Rows live in a 4 MiB area
of `host.map`; a batch that needs more rows is refused with an `ArgumentError` naming the largest frame count that fits at
that `watch_every`. States saved under ABI 2 still load.

**Threads (core lazpy.2).** `emu.threads()` returns a tuple of `ThreadInfo(tid, pid, status, status_name, core,
priority, is_current, pc, lr, sp, cpsr)` for every guest thread on every core, read between batches. A core's current
thread (`is_current`) is read from the live CPU, every other thread from its saved registers. System-module threads may
be listed too, so filter by `pid`; `pid` is `0xFFFFFFFF` for a thread with no owner process. Bit 5 of `cpsr` is the
Thumb bit. On the stock core and on a lazpy.1 core it raises `NeedsLazpyCore`.

## 12b. Audio

`run(frames, audio=True)` keeps the audio the app made during that batch: `result.audio` is int16 stereo (a numpy array of
shape `(n, 2)` when numpy is installed, else an `array.array('h')` of interleaved left, right values) and
`result.audio_rate` is the core's sample rate in Hz. Without `audio=True` nothing is captured, `result.audio` is `None`
and `audio_rate` is 0. `run_until` takes the same argument. After a guest exit the audio is empty. The audio is not part of
`RunResult` equality and is left out of its `repr`.

What to expect: the batch holds whatever the guest's sound library produced while those frames ran, about the rate times
the batch's time in seconds, so a short first batch can hold nothing: sound usually starts some frames after boot. The
capture goes through a file in the instance folder (`audio.raw`), which is removed when the batch returns; a 10 minute
batch is about 80 MB on disk while it runs.

The app's audio library looks for a component file on the SD card and fails to start without it.
The tests seed a made-up one (`tests/python/dsp_component.py`), which Azahar's high-level DSP ignores apart from logging
its hash. The tone test app is `testapp-tone/` (`make testapp-tone`); `tests/python/test_audio_live.py` runs it.

## 12. The Gen3D mapping

Rows 1-17 of docs/research/gen3d-harness-needs.md:

| Gen3D mechanism | libazahar-py |
|---|---|
| 1 Qt profile pins | `options` |
| 2 SD staging | `sd_seed` |
| 3 locks, focus, bundle clones | dropped (plain processes, own folders) |
| 4 curtain window | dropped (no pacing) |
| 5 CTM movies | `inputs` (poll-exact: our core exports it; the host and Python do not call it) |
| 6, 7 SD control channel, netlogs | `emu.sd` files and `run_until` |
| 8 `voxel.log` flip lines | `emu.sd` file and `run_until` |
| 9 window screenshots | `shots` / `screens()` (400x240 top, 320x240 bottom) |
| 10 framebuffer via gdb | `screens()` |
| 11, 12 gdb RAM reads | `emu.memory` on our core (the test app's 32-byte record: magic 0, frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24) or an app log line |
| 13 `see rec` | `shots` with frame numbers |
| 14 `gdbio resume` | gone |
| 15, 16 savewarp, picture judges | unchanged |
| 17 savestates | `save_state` and `Emulator(state=)` |

Forced-mode seed: a seed folder holding the app's control file, so one Emulator boots straight into a mode (the test
app's control.txt shows it). For the long world build: boot once, `save_state`, start every test from the state, and
reuse the instance folder's `sys/` for the shader cache.

## 13. Many instances

`Pool(n, app, root, **emulator_kwargs)` runs jobs on fresh Emulators, `n` at a time. `submit(fn, item, **overrides)`
returns a `Future`; `map(fn, items, **overrides)` returns the results in item order and raises the first error after
every job ends; `close(wait=True)` stops it (a `with` block closes it). Each job gets a new instance in
`root/job-0000`, `job-0001`, ... (its own `sys/`, `shots/`, `host.log`, `host.map`), closed when the job ends, however
it ends. `fn(emulator, item)` is the job. Per-job overrides, such as `sd_seed`, win over the Pool's keywords:

    with Pool(3, app, "runs/x") as pool:
        results = pool.map(job, seeds, sd_seed=seed_folder)      # job(emu, item) -> result, in item order

`examples/pool_shots.py` is a runnable one. The machine-wide cap holds the number of live instances: a fixed set of
lock files, one per slot, shared by every libazahar process on the Mac. `LAZ_MAX_INSTANCES` sets the cap (default 4,
from a real 3D scene on an M3 Pro: `docs/research/real-scene-v3.md`), `LAZ_SLOT_DIR` the lock folder, `LAZ_SLOT_TIMEOUT` how long an Emulator waits
for a slot (default 3600 s). When it runs out, `SlotTimeout` is raised (a `HostTimeout`; `.op == "slot"`, `.seconds`;
its text names the cap and the slot folder). The kernel frees a slot when its worker dies, however it dies. The cap
counts only libazahar's own workers, so other emulators on the machine are not counted. `Pool(n)` above the cap warns
(`UserWarning`) and the extra jobs wait; a load above twice the core count warns with `LoadWarning`. Workers run at
`nice` 10 at least (a parent that is already nicer keeps its value).

- An `Emulator` is used from one thread at a time. Separate `Emulator` objects may run in parallel threads or in
  parallel processes.
- A `Pool` that reuses a `root` reuses `root/job-NNNN/sys/`, the SD card included, unless `fresh_sd=True` is passed
  in its keywords.
- When the body of a `with Pool(...)` block raises, jobs that are still queued are cancelled; jobs already running
  finish and close their Emulators. A body that ends normally waits for every queued job.
- `factory=` is a test hook outside the promise.

## 14. Our core's profile

On our core `core/options-lazpy.txt` is applied first (the extra option lines our core takes), then the default
profile and your `options`. `azhost run --lazpy-profile FILE|none` and `LAZ_LAZPY_PROFILE` (a file, or `none`) change
it. The stock core never sees it.

The tick seed: with `citra_init_ticks_type=Fixed` (the profile's value), `citra_init_ticks_override` sets the base CPU
ticks (core lazpy.2; default `0`; any decimal from 0 to 4294967295, else `ArgumentError`). It takes effect at boot. It
also shifts the guest's clock by that many ticks (268 MHz), a played movie replaces it with the movie's own, and a
loaded state keeps the ticks it was saved with.

The option-profile format:

A profile is a text file of `key=value` lines. `--profile`, `--lazpy-profile` and Python's profile argument all read it
by the same rules. `options=` pairs and `--opt` pass the same rule for one `key=value` line; a bad Python pair is
`ArgumentError` naming the key (a newline or trailing `\r` in a value is refused too).

1. Lines are split on `\n` only; one trailing `\r` is removed. A last line without a newline counts. Every line,
   comments included, is valid UTF-8 with no NUL byte, and no line starts with a BOM.
2. A line is at most 511 bytes (the newline excluded). A file has at most 4096 lines, comments and blank lines
   included. Going over either limit is an error, never a silent cut. Lines are checked in file order and the first
   error is reported; a 4097th line is reported as line 4097.
3. A line that is empty is skipped. A line whose first byte is `#` is a comment. A `#` anywhere else is part of the
   text.
4. Every other line is `key=value`, split at the first `=`. The key is not empty and has no space, tab or `=`. The
   value is everything after the `=`, as written: inner spaces are kept (`citra_is_new_3ds=New 3DS`), and it may be
   empty, in which case the host decides.
5. Nothing is trimmed. A line that starts or ends with a space or tab is an error. This includes an indented `#`.
6. Pairs are applied in file order, after the earlier sources: the lazpy profile, then the default (or given) profile,
   then `options=` / `--opt` in order. The later line wins, inside a file and across sources.
7. An unknown key, or a value outside the core's list, is refused by the host and never ignored. On the stock core a
   key that only our core has is unknown.
8. How errors show up:
   - Python: a bad line raises `ArgumentError("<path>:<line>: <reason>")` (`<path>:4097: more than 4096 lines` for a
     long file); an unreadable file raises `HostError`; an
     unknown key raises `ArgumentError` at boot.
   - azhost: a bad line or an unknown key prints `UsageError: <path> line N: <reason>` and exits 2; an unreadable file
     prints `IOError` and exits 6.

The tests in `tests/data/profile-cases/` (one `.txt` and one `.expect` per case) run through both parsers.

## 15. Environment

Library and host (the last column says who reads it). Only this first table is part of the promise; the test and
build variables below may change in a minor release:

| Variable | What it does | Default | Read by |
|---|---|---|---|
| `LAZ_ROOT` | the repo folder | the folder the package sits in | Python |
| `LAZ_HOST` | the host library | macOS: `<root>/build/libazhost.dylib`; Windows: `<root>/build/libazhost.dll` | Python |
| `LAZ_CORE` | the core | `<root>/dl/lazpy-core/azahar_lazpy_libretro.dylib` (Windows: `.dll`) | Python, `azhost` |
| `LAZ_MVK` | the Vulkan loader: MoltenVK on macOS | macOS: `<root>/dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib`; Windows: `vulkan-1.dll` from System32 | Python, host |
| `LAZ_PROFILE` | the option profile | `<root>/host/options-default.txt` | Python |
| `LAZ_LAZPY_PROFILE` | the extra options on our core: a file or `none` | `<root>/core/options-lazpy.txt` when present | Python |
| `LAZ_VK_DEVICE` | which Vulkan device the host uses: its index in the loader's list, or a part of its name (see below) | unset: the first device | host |
| `LAZ_MAX_INSTANCES` | the slot cap, 1 to 64 | 4 | Python |
| `LAZ_SLOT_DIR` | the slot lock folder | macOS: `~/Library/Caches/libazahar-py/slots`; Windows: `%LOCALAPPDATA%\libazahar-py\slots` | Python |
| `LAZ_SLOT_TIMEOUT` | seconds to wait for a slot | 3600 | Python |
| `LAZ_PNG_LEVEL` | PNG compression, 0 to 9 (a bad value gives 1) | 1 | host |
| `LAZ_LOG_LEVEL` | `host.log` threshold: `debug`, `info`, `warn`, `error` (or 0 to 3) | `info` | host |
| `LAZ_ANY_CORE` | `1` accepts any core version | unset: only the stock core (`2126.2`, or `219d743` as Azahar's Windows build names it) and our core (`2126.2-lazpy.1`, `2126.2-lazpy.2`) | host |
| `MVK_CONFIG_LOG_LEVEL` | MoltenVK's log level | 1 | host |
| `LAZ_STATE_ANY_APP` | `1` loads a state made with another build of the app | unset | host |

`LAZ_VK_DEVICE`: a value of digits only is always an index from 0, with no name fallback. A name part is matched with
the case ignored. No match is an `AZH_E_VULKAN` error at boot that names every device, never a silent fallback. The
choice goes to `host.log`, and to stderr when the variable is set or when more than one device exists.

Tests only: `LAZ_REQUIRE_EMULATOR=1` (a missing emulator fails instead of skipping) and `LAZ_STOCK_CORE` (a stock core
you downloaded; unset, the comparison tests skip), `LAZ_CORE_OLD` (a lazpy.1 core, for the test that it still
boots). `LAZ_CORE` is the only variable the library reads to find a core.

Build and fetch time (the scripts' header comments are the reference):

| Variable | What it does | Default | Script |
|---|---|---|---|
| `LAZ_ROOT` | use this folder instead of the repo root (the same meaning as for the library; the old name `LAZPY_ROOT` still works in 1.x) | the repo root | `fetch.sh`, `build-core.sh`, `mkrelease.sh` |
| `LAZ_RELEASE_BASE` | where the release downloads come from; a `file://` folder works for a local release | the release page | `fetch.sh` |
| `LAZ_CORE_PIN` | the pin file | `core/PIN-nokeys` | `build-core.sh` |
| `LAZ_CORE_PATCHES` | the patch folder | `core/patches` | `build-core.sh` |
| `LAZ_CORE_LTO` | link-time optimisation | `ON` | `build-core.sh` |
| `LAZ_CORE_JOBS` | build jobs | 4 | `build-core.sh` |
| `LAZ_OPENSSL_PREFIX` | install prefix of the static OpenSSL | the pin's `OPENSSL_PREFIX` | `build-core.sh` |

## 15a. Windows differences

The 1.0 promise holds on Windows. These are the differences from macOS; nothing else in this guide changes.

| | macOS | Windows (x64) |
|---|---|---|
| Build | `make` with Xcode tools | `make` in the MSYS2 MINGW64 shell (the Makefile refuses the other MSYS2 shells), with MINGW64 gcc and a static zlib |
| Files | `libazhost.dylib`, `azhost`, `azahar_lazpy_libretro.dylib` | `libazhost.dll`, `azhost.exe`, `azahar_lazpy_libretro.dll` |
| Vulkan loader (`LAZ_MVK`) | MoltenVK, fetched by `fetch.sh` | `vulkan-1.dll` from System32. A GPU driver with Vulkan is required; nothing Vulkan is shipped |
| `LoadWarning` | can be raised | never raised |
| Worker priority | a nice value | BELOW_NORMAL |
| Slot folder (`LAZ_SLOT_DIR`) | `~/Library/Caches/libazahar-py/slots` | `%LOCALAPPDATA%\libazahar-py\slots`; `Slot.fd` is a HANDLE |
| Paths | any | ASCII only and under 260 characters: clone into a short path such as `C:\src` |
| SD folder names | follows the volume | case-insensitive |
| `runs/` behind a junction | n/a | not supported |
| Savestates between macOS and Windows | a Windows state is refused (expected; not run) | a macOS state is refused (checked on Windows): `StateError` "the core refused the state", and `host.log` gives the reason, "incompatible native format - size of long" (Azahar's boost archives store `long`, 8 bytes on macOS and 4 on Windows). Make states on the system that loads them |
| The guest's HTTPS (CA file) | Homebrew's `openssl@3` paths | none: the compiled-in OPENSSLDIR, `/opt/lazpy/openssl-3.6.5-mingw64/C:/Program Files/Common Files/SSL`, is not a usable Windows path |

No windows: the worker and `azhost.exe` create no top-level window, hidden ones included. A live test on Windows lists
every top-level window of the desktop during a run and finds none that belongs to the worker. The test first makes a
hidden window of its own and requires the list to hold it, so an empty list cannot pass. Whether a run can take the
focus is not yet checked: that test needs a logged-in desktop, and over SSH it skips.

Windows has no lazpy.1 core: the Windows core is lazpy.2. The limits of what was tested are in `STATUS.md`: one PC,
Windows 10, an NVIDIA GPU. Windows 11 and AMD and Intel GPUs are untested.

## 16. The two cores

| | Our core | Azahar's own core (stock) |
|---|---|---|
| Where it comes from | our release (`sh tools/fetch.sh --lazpy-core`) or `tools/build-core.sh` | Azahar's releases page, by hand, for comparisons |
| Input, shots, SD files, savestates | yes | yes |
| Guest memory, the watch list (`emu.memory`, `watch=`) | yes | `NeedsLazpyCore` |
| Debug-text stop (`debug_text=`) | yes | `NeedsLazpyCore` |
| Thread registers (`emu.threads()`) | lazpy.2 only (lazpy.1: `NeedsLazpyCore`) | `NeedsLazpyCore` |
| Exact repeats | yes (gated) | no: recorded as a difference only |
| Poll-exact movies | our core exports it; the host can pass it a file, Python does not | no |
| Option profile | `core/options-lazpy.txt` first (section 14) | the default profile only |

States move between the two cores both ways in the gate, but a state may not load across core versions.

## 17. Getting our core

The release: `sh tools/fetch.sh --lazpy-core` puts it at `dl/lazpy-core/azahar_lazpy_libretro.dylib`, the default path,
so no `LAZ_CORE` is needed. Or build it: `nice -n 10 tools/build-core.sh --detach` (15 to 90 minutes; the exit code
lands in `build-core/build.exit`, the log in `build-core/build.log`), then set
`LAZ_CORE=build-core/azahar_lazpy_libretro.dylib`. The build needs a static OpenSSL at the version in `core/PIN`
(3.6.5). Homebrew ships only its current `openssl@3`. If that is 3.6.5, the build finds it. If not, build 3.6.5 from
`openssl-3.6.5.tar.gz` (a release asset; the recipe in `core/OPENSSL.md` is not tested by this project) and set
`LAZ_OPENSSL_PREFIX` to its install prefix. The build starts from our stripped source asset (`core/PIN-nokeys`, the
default); to start from Azahar's original tarball instead, set `LAZ_CORE_PIN=core/PIN`. `core/README.md` lists the
patches; `core/OPENSSL.md` covers OpenSSL. The core needs macOS 15 or later (core lazpy.2's header says 15.0; the
lazpy.1 header said 11.0, although its OpenSSL already needed 15). This host accepts cores lazpy.1 and lazpy.2.

## 18. Contributors

`.venv/bin/pip install pytest numpy` (the tests import numpy), then `.venv/bin/python -m pytest -q tests/python -m "not slow"` (the fast set needs no
emulator). The full set needs our core and the test app: `LAZ_REQUIRE_EMULATOR=1 .venv/bin/python -m pytest -q
tests/python`. On Windows use `.venv/Scripts/` for `.venv/bin/`. `make check` runs the rest (on Windows it also
needs `mingw-w64-x86_64-clang` from pacman). To compare with Azahar's own core, download Azahar's libretro core for
macOS from Azahar's releases page yourself and set `LAZ_STOCK_CORE` to the file. Tests that compare the two cores skip
without it. Build the test app with the line in the README (`make testapp` needs `DEVKITPRO` and `DEVKITARM` set and
devkitARM first in `PATH`).

## 19. Troubleshooting

- `BootError: cannot load core <path>: dlopen(...) ... (no such file)`: no core at that path. Run
  `sh tools/fetch.sh --lazpy-core`, or set `LAZ_CORE` to a core file.
- A host library or MoltenVK not found: run `make`, or `sh tools/fetch.sh --moltenvk`; check `LAZ_ROOT`, `LAZ_HOST` and
  `LAZ_MVK`.
- A dylib you downloaded with a browser is quarantined: `xattr -d com.apple.quarantine <file>` (`curl` sets none).
- `make testapp` stops with "Set DEVKITARM": set `DEVKITPRO` and `DEVKITARM` and put devkitARM first in `PATH`;
  Homebrew's arm gcc gives other results.
- `SlotTimeout`: other instances hold every slot. Look in the slot folder (`LAZ_SLOT_DIR`), or raise
  `LAZ_MAX_INSTANCES` if the machine can take it.
- A `LoadWarning`: other sessions' emulators share the machine; wait, or run fewer instances.
- `HostTimeout` in the first frames: shader compiles. Raise `boot_timeout` (default 300 s).
- A hang inside one frame never reaches `wall_limit` (it is checked between frames) and the heartbeat is the only
  watch, so a script that must not hang inside one frame relies on the heartbeat `timeout`, which does catch it. An
  `azhost` run needs an outer limit of your own: `timeout` (coreutils; `gtimeout` on macOS with Homebrew coreutils), a
  `subprocess.run(..., timeout=)` wrapper, or PowerShell `Wait-Process -Timeout` on Windows. (Windows' own `timeout`
  command only waits.)
- The core refuses to load on macOS older than 15.
- Windows: a boot error naming `vulkan-1.dll` means no Vulkan driver is installed; install the GPU maker's current driver.
  A path error at start usually means a long or non-ASCII folder: clone into `C:\src`.

Errors by their opening text. Each line is the start of `str(error)`; every error raised once the worker has started ends with the
`host.log` and newest-shot line (section 8), so look at the log first.

| The error starts with | Class | Meaning and next step |
|---|---|---|
| `cannot load core` | `BootError` | No core at that path: fetch our core or set `LAZ_CORE`. |
| `core ... is missing` | `BootError` | The same, found before the worker started. |
| `<call> timed out after N s (last guest message: ...)` | `HostTimeout` | No new frame for N s; the worker was killed. In the first frames raise `boot_timeout`. |
| `no libazahar slot free after` | `SlotTimeout` | Other instances hold every slot (`LAZ_SLOT_DIR`, `LAZ_MAX_INSTANCES`). |
| `the worker died (signal N)` or `(exit code N)` | `HostCrashed` | Read the `host.log` and `worker.err` tails in the text. |
| `the guest stopped with a fatal error` or the guest's own message | `GuestError` | A guest crash; `.result` holds the batch while the Emulator is open. |
| `the guest exited during <call>` | `HostError` | A guest exit outside `run`. |
| `the emulator is closed` | `HostError` | A call after `close()`, a dead worker or a guest exit. |
| `cannot load the host` | `HostError` | The host library is missing or its ABI differs: run `make`, check `LAZ_HOST`. |
| `guest memory 0x...: a page is unmapped` | `GuestMemoryError` | An unmapped guest page; the write changed nothing. |
| `host library ... not found` | `HostError` | Raised in the caller before any worker: run `make`, check `LAZ_ROOT` and `LAZ_HOST`. |
| `cannot make the working folder` | `HostError` | The `workdir` could not be created: check the path and its rights. |
| `cannot read the option profile` | `HostError` | `LAZ_PROFILE` or the profile file is unreadable (section 14). |
| a bad argument, such as a frame outside the range or an address | `ArgumentError` | Also a `ValueError`. Fix the call; a profile line that breaks the format names its file and line. |
| `... needs the libazahar core (this core is stock)` | `NeedsLazpyCore` | The call needs our core: section 17, or set `LAZ_CORE`. |
| a savestate message | `StateError` | The state could not be saved, read or restored (section 10). |

## 20. API reference

One line per name in `libazahar.__all__`. Units: seconds in Python, frames are guest VBlanks.

- `Emulator(app, workdir, *, sd_seed, state, core, options, timeout, boot_timeout, fresh_sd)`: one headless instance in its own worker process. Context manager; `close()` may be called twice.
  - `app`, `workdir`: read-only `Path` properties. `timeout` (no-progress limit, default 30 s) and `boot_timeout` (default 300 s) may be set at any time.
  - `sd`: the emulated SD folder. `pid`: the worker's process id. `closed`: True after `close()`, a dead worker or a guest exit. `frame_total`: frames since boot. `memory`: guest memory (our core only).
  - `run(frames, *, ...)`, `run_until(file, text, max_frames, *, ...)`, `run_frame()` (one frame): return a `RunResult`.
  - `set_input(buttons, touch, circle)`, `set_keys(raw)`: change the held input now.
  - `screens()`: both screens as read-only arrays (or `bytes`). `shot(prefix)`: save both screens as PNG, returns two `Path`.
  - `save_state(path)` returns a `SaveInfo`; `load_state(path)`; `threads()` returns a tuple of `ThreadInfo` (our core only).
  - `stats()`: a `Stats` snapshot. `close()`: stop the worker.
- `Pool(n, app, root, **emulator_kwargs)`: `submit`, `map`, `close`; section 13.
- `Buttons`: the button bits (libctru names plus `UP`, `DOWN`, `LEFT`, `RIGHT`); a value is the whole held mask. `Touch(x, y)` and `Touch.up`: the touch point; `Circle(x, y)`: the circle pad.
- `RunResult`: what one batch did (`frames`, `stopped_by`, `first_frame`, `last_frame`, `frame_total`, `vblanks`, `wall_s` in seconds, `message`, `shots`, `watch`, `audio` and `audio_rate` (section 12b; `audio` is not compared)). New `stopped_by` values may be added; callers must accept unknown ones.
- `Shot`: `frame` (batch frame), `top` and `bottom` (`Path`), `frame_total` (frames since boot).
- `WatchRow`: one row of a watch list: `frame`, `status`, `data` (one `bytes` per entry), and `u32(entry, word)`.
- `Memory`: the type of `Emulator.memory`, exported for type hints; users never construct it. `read`, `write`, `u8` to `u64`, `s8` to `s64`, `write_u8` to `write_u64`, `raw_read`, `raw_write`.
- `SaveInfo`: `path` (`Path`), `k` (guest VBlanks the save's drain ran; a state "at frame N" is at N + k), `frame_total`.
- `Stats`: `frames` (since boot), `wall_s`, `user_s`, `sys_s` (seconds), `peak_rss` (bytes), `core_name`, `core_version`, `is_lazpy_core`.
- `ThreadInfo`: one guest thread: `tid`, `pid`, `status`, `status_name`, `core`, `priority`, `is_current`, `pc`, `lr`, `sp`, `cpsr`.
- `LibAzaharError`: the base class of every error raised on purpose.
- `ArgumentError`: a bad argument (also a `ValueError`). `BootError`: the core, Vulkan or the app failed to start. `GuestError`: the guest stopped with a fatal error; `.result` holds the `RunResult` while the Emulator is open.
- `HostTimeout`: no progress in time; `.op`, `.seconds`, `.message` (the last guest message). `SlotTimeout`: a `HostTimeout` with `.op == "slot"`, `.slots`, `.folder`.
- `HostCrashed`: the worker died; `.returncode`, `.signal`, `.message`, `.log_tail`, `.err_tail`; `HostCrashed.signal_name(number)` gives a signal's name (the digits when unknown, `none` for None).
- `StateError`: a savestate could not be saved, read or restored. `NeedsLazpyCore`: the call needs our core. `GuestMemoryError`: an unmapped guest address; `.addr`, `.length`. `HostError`: wrong call order, I/O, memory, an unsupported call, an ABI mismatch or a missing host.
- `LoadWarning`: the machine's load average is above twice its core count.
- `__version__`: the package version string.
- `libazahar.images` (import it with `from libazahar import images`; it is not in `__all__`):
  - `images.digest((top, bottom))`: a SHA-256 hex string of the two screens from `screens()` (arrays or `bytes`); it needs no numpy.
  - `images.compare(a, b, *, max_delta=0, max_pixels=0)`: each side is a `(H, W, 4)` uint8 array or the path of a PNG the host wrote. Returns a `CompareResult`: `largest_delta` (the measured largest single-channel difference; the `max_delta` argument is the limit), `pixels` (pixels that differ at all), `over` (pixels with a channel off by more than the `max_delta` limit), `within` (`over <= max_pixels`). `result.write_diff(path, *, over_only=False)` saves a PNG of the same size, white for every differing pixel and black elsewhere; with `over_only=True` only the pixels over the limit are white. A `CompareResult` is made by `compare`; one built by hand has no picture, and `write_diff` raises `ArgumentError`. Needs numpy (`pip install 'libazahar-py[numpy]'`), else an `ImportError` names the extra.
  - The PNG reader takes only the host's own files (8-bit RGBA, filter 0 on every row, one IDAT) and raises `ArgumentError` for any other PNG, a bad CRC or a different picture size.

Evidence on failure and parent death:
- `.workdir`, `.log_path` on `BootError`, `GuestError`, `HostTimeout`, `HostCrashed`, `StateError`, `HostError` and `GuestMemoryError` once the worker has started: the instance's folder and its `host.log`, both `None` on any other error (`SlotTimeout` too) and on errors raised before the worker exists; the error text names `host.log` and the newest shot (its top and bottom PNG) under `shots/`, read when the text is first asked for (section 8).

Command line (section 2a):
- `python -m libazahar doctor` and `python -m libazahar run APP --frames N [--inputs FILE] [--shot F ...] [--state P] [--save P] [--json] [--workdir DIR] [--sd-seed DIR] [--timeout S]`. Both take `--help`. The module `libazahar._cli` is private; the commands, their flags, the `--json` keys (`ok`, `exit_code`, `workdir`, `result`, `saved`, `error`) and the exit codes of section 3 are the promise.
