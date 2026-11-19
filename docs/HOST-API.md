# The host library and `azhost`

For C users, and for anyone reading the Python layer's worker. The Python layer (`python/libazahar/`) calls this
library through `ctypes`; `docs/USING.md` is the guide to the Python side. The promise: the host and the Python layer
are one unit and ship together, so the layout and the Python-to-host calls are checked at load time and may change in a
1.x release (each change bumps `AZH_ABI_VERSION`, now 5); the C promise is at source level: the names, argument orders
and meanings of the `azh_*` functions and `AZH_*` constants in `host/azhost.h` do not change in 1.x, and struct
layouts may grow.

## Build

`make` builds `build/libazhost.dylib` and `build/azhost`. The header is `host/azhost.h`: its comments are the
reference, and this page does not restate struct fields. The library needs a libretro core (`LAZ_CORE` or the path you
pass to `azh_open`), MoltenVK, and the headers `tools/fetch.sh` puts in `vendor/`.

## The ABI version and the layout

`AZH_ABI_VERSION` is 5 (`host/azhost.h` line 9). `azh_abi_layout()` fills an `azh_layout` with the size of every
struct, the map's size and offsets, and one `fields[]` row (name, offset, size) per struct member. A caller checks
these against its own view at load time, as `python/libazahar/_abi.py` does, and refuses a host whose layout differs.
`build/azhost layout` prints the same rows (the full output is at the end of this page).

## Call order

`azh_open`, then `azh_set_option` (as many as you need), then `azh_boot`, then any of `azh_run`, `azh_shot`,
`azh_stats`, `azh_read`, `azh_write`, `azh_threads`, `azh_set_input`, `azh_audio_capture`, `azh_audio_info`, `azh_save_state`, `azh_load_state`, then `azh_close`.
`azh_error` and `azh_abi_layout` work at any time. One `azh_open` per process: the core and MoltenVK stay mapped after
`azh_close`, so a second open is refused (`AZH_E_ORDER`). The Python layer runs each Emulator in its own worker process
for this reason. Every function returns 0 or a negative `AZH_E_*` code; `azh_error()` returns the text of the last
error.

## The functions

| Function | What it does | Header |
|---|---|---|
| `azh_open` | loads the core, starts Vulkan, opens the log and the map file | `host/azhost.h` line 89 |
| `azh_close` | stops the core and closes the files | `host/azhost.h` line 90 |
| `azh_set_option` | sets one core option, after open and before boot; a later call for a key wins; an unknown key or value returns `AZH_E_ARG` | `host/azhost.h` line 91 |
| `azh_boot` | loads the app, and a savestate when one is given | `host/azhost.h` line 93 |
| `azh_run` | runs a batch of frames with input records, shots, stop rules and a watch list; fills an `azh_result` | `host/azhost.h` line 94 |
| `azh_shot` | saves the current frame of one or both screens as PNG or raw RGBA | `host/azhost.h` line 96 |
| `azh_save_state` | writes a savestate; returns the VBlanks the drain ran | `host/azhost.h` line 97 |
| `azh_load_state` | restores a savestate | `host/azhost.h` line 98 |
| `azh_read` | reads guest memory (our core; `AZH_E_NEEDS_LAZPY_CORE` on the stock core) | `host/azhost.h` line 99 |
| `azh_write` | writes guest memory (our core) | `host/azhost.h` line 100 |
| `azh_threads` | lists the guest's threads (our core, ABI 4); `*count` is the total even when it is above `max` | `host/azhost.h` line 101 |
| `azh_set_input` | sets the held input now | `host/azhost.h` line 103 |
| `azh_audio_capture` | (ABI 5) writes the core's audio to a file as raw interleaved 16-bit stereo; off by default; NULL stops it | `host/azhost.h` line 104 |
| `azh_audio_info` | (ABI 5) stereo frames written so far and the core's sample rate | `host/azhost.h` line 107 |
| `azh_stats` | frames, wall and CPU time, peak memory, the core's name and version, whether it is our core | `host/azhost.h` line 110 |
| `azh_abi_layout` | fills the layout record | `host/azhost.h` line 111 |
| `azh_error` | the last error text | `host/azhost.h` line 112 |

## Errors

| Code | Name | Python class |
|---|---|---|
| 0 | `AZH_OK` | none |
| -1 | `AZH_E_ARG` | `ArgumentError` (a `ValueError`) |
| -2 | `AZH_E_ORDER` (call order) | `HostError` |
| -3 | `AZH_E_CORE` | `BootError` during start, else `HostError` |
| -4 | `AZH_E_BOOT` | `BootError` |
| -5 | `AZH_E_VULKAN` | `BootError` during start, else `HostError` |
| -6 | `AZH_E_IO` | `HostError` |
| -7 | `AZH_E_NOMEM` | `HostError` |
| -8 | `AZH_E_UNSUPPORTED` | `HostError` |
| -9 | `AZH_E_NEEDS_LAZPY_CORE` | `NeedsLazpyCore` |
| -10 | `AZH_E_SAVESTATE` | `StateError` |
| -11 | `AZH_E_UNMAPPED` | `GuestMemoryError` |

The stop reasons of a batch (`AZH_STOP_*`) are in the header line 23; the Python names are in `docs/USING.md`
section 7.

## The map file

`azh_open` is given a path for the map file (`host.map` in an instance folder). It is a memory-mapped file that the
host writes and a reader may map read-only. It holds a header (magic `LAZMAP1`, version, a heartbeat counter that moves
every frame, the stop code and the stop message, the screen sizes, the frame and VBlank totals, the pid and the exit
code), then, at byte 4096, the pixels of the last raw shot (top 400x240 and bottom 320x240, RGBA), then, at byte
696320, a 4 MiB area for the watch rows. The Python layer reads it for the heartbeat (the no-progress timeout), for
`screens()` and for watch rows. Offsets are never hard-coded by callers: they come from `azhost layout` (the `map.*`
rows) or from the layout record.

## The `azhost` command

`azhost` runs the same calls from a shell. It has no `--help`: any first argument other than `run` or `layout` prints
the usage to stderr and exits with 2. This is the text (`build/azhost usage 2>&1`):

```
UsageError: expected: azhost run <app> ...
usage: azhost run <app> --sys <dir> --out <dir> --frames N[,N2,...] [--shot f1,f2,...]
              [--opt key=value]... [--profile file] [--lazpy-profile file|none] [--core path] [--mvk path] [--state file]
              [--inputs file] [--sd-seed dir] [--stop-file rel --stop-text t [--stop-every k] [--stop-new]]
              [--debug-stop t] [--wall-limit-ms ms] [--raw-shot f] [--print-last-line rel] [--save file]
       azhost layout
```

Exit codes: the table in `docs/USING.md` section 3 is the reference (0 ok; 2 usage; 3 boot; 4 core; 5 Vulkan; 6 I/O;
7 the run needs our core; 8 unsupported; 9 a savestate failed; 10 the guest exited; 11 a guest error). On our core a
guest break ends that batch (`stop=guest_break`); `azhost` goes on to the next batch and to `--save`, and the exit code stays
0 if every batch ran. A guest exit or guest error prints that batch's summary line first
and then exits 10 or 11. On the stock core the process itself exits from inside the run, with no summary line for that
batch. A summary line per batch looks like `frames= wall= fps= shots= stop= first= last= vblanks= wall_ms_mean= batch=
msg=` (see `docs/USING.md` section 3); `msg=` is always last, so new keys go before it.
The default core of `azhost` is the one `LAZ_CORE` names, else the path in section 15 of `docs/USING.md`.

## `azhost layout`

Taken 2026-11-19 from a build of ABI 5 (the struct rows are those of ABI 4; ABI 5 adds calls only). Each row is `name offset size`.

<details>
<summary>The full output of <code>build/azhost layout</code> (152 lines)</summary>

```
abi=5
shot.frame 0 4
shot.screens 4 4
shot.format 8 4
shot.__size__ 0 12
batch.frames 0 4
batch.n_shots 4 4
batch.shots 8 768
batch.shot_dir 776 1024
batch.sd_file 1800 1024
batch.sd_text 2824 256
batch.sd_every 3080 4
batch.debug_text 3084 256
batch.wall_limit_ms 3340 4
batch.sd_from_end 3344 4
batch.n_watch 3348 4
batch.watch_every 3352 4
batch.watch 3356 256
watch.addr 0 4
watch.words 4 4
watch.__size__ 0 8
batch.__size__ 0 3612
result.frames_run 0 8
result.first_frame 8 8
result.last_frame 16 8
result.stop_reason 24 4
result.shots_done 28 4
result.wall_s 32 8
result.vblanks 40 8
result.message 48 256
result.watch_rows 304 4
result.watch_status 308 4
result.__size__ 0 312
stats.frames 0 8
stats.wall_s 8 8
stats.user_s 16 8
stats.sys_s 24 8
stats.peak_rss 32 8
stats.core_name 40 64
stats.core_version 104 128
stats.is_lazpy_core 232 4
stats.__size__ 0 240
thread.tid 0 4
thread.pid 4 4
thread.status 8 4
thread.core 12 4
thread.priority 16 4
thread.flags 20 4
thread.pc 24 4
thread.lr 28 4
thread.sp 32 4
thread.cpsr 36 4
thread.__size__ 0 40
layout.abi 0 4
layout.size_batch 4 4
layout.size_result 8 4
layout.size_stats 12 4
layout.size_layout 16 4
layout.map_size 20 4
layout.map_px_off 24 4
layout.map_px_size 28 4
layout.off_heartbeat 32 4
layout.off_stop 36 4
layout.off_msg 40 4
layout.off_px_frame 44 4
layout.n_fields 48 4
layout.fields 52 6400
layout.__size__ 0 6452
map.magic 0 8
map.version 8 4
map.header_size 12 4
map.heartbeat 16 8
map.stop_code 24 4
map.msg_len 28 4
map.message 32 1024
map.dims 1056 16
map.px_frame 1072 8
map.frame_total 1080 8
map.vblanks_total 1088 8
map.msg_seq 1096 4
map.pid 1100 4
map.exit_code 1104 4
map.pixels 4096 691200
map.watch_rows 696320 4
map.watch_row_bytes 696324 4
map.watch_words 696328 4
map.watch_seq 696332 4
map.watch_first 696336 8
map.watch_data 696384 4194240
map.__size__ 0 4890624
const.AZH_OK 0 0
const.AZH_E_ARG -1 0
const.AZH_E_ORDER -2 0
const.AZH_E_CORE -3 0
const.AZH_E_BOOT -4 0
const.AZH_E_VULKAN -5 0
const.AZH_E_IO -6 0
const.AZH_E_NOMEM -7 0
const.AZH_E_UNSUPPORTED -8 0
const.AZH_E_NEEDS_LAZPY_CORE -9 0
const.AZH_E_SAVESTATE -10 0
const.AZH_E_UNMAPPED -11 0
const.AZH_EXIT_OK 0 0
const.AZH_EXIT_USAGE 2 0
const.AZH_EXIT_BOOT 3 0
const.AZH_EXIT_CORE 4 0
const.AZH_EXIT_VULKAN 5 0
const.AZH_EXIT_IO 6 0
const.AZH_EXIT_NEEDS_LAZPY 7 0
const.AZH_EXIT_UNSUPPORTED 8 0
const.AZH_EXIT_STATE 9 0
const.AZH_EXIT_GUEST_EXITED 10 0
const.AZH_EXIT_GUEST_ERROR 11 0
const.AZH_SCREEN_TOP 1 0
const.AZH_SCREEN_BOTTOM 2 0
const.AZH_SCREEN_BOTH 3 0
const.AZH_FMT_PNG 0 0
const.AZH_FMT_RAW 1 0
const.AZH_STOP_FRAMES 0 0
const.AZH_STOP_SD_TEXT 1 0
const.AZH_STOP_DEBUG_TEXT 2 0
const.AZH_STOP_GUEST_BREAK 3 0
const.AZH_STOP_GUEST_EXITED 4 0
const.AZH_STOP_GUEST_ERROR 5 0
const.AZH_STOP_WALL_LIMIT 6 0
const.AZH_ABI_VERSION 5 0
const.AZH_STATE_META_ABI 3 0
const.AZH_THREAD_CURRENT 1 0
const.AZH_MAX_SHOTS 64 0
const.AZH_PATH_MAX 1024 0
const.AZH_INPUT_INTS 7 0
const.AZH_IN_FRAME 0 0
const.AZH_IN_BUTTONS 1 0
const.AZH_IN_TOUCH_X 2 0
const.AZH_IN_TOUCH_Y 3 0
const.AZH_IN_TOUCH_DOWN 4 0
const.AZH_IN_CIRCLE_X 5 0
const.AZH_IN_CIRCLE_Y 6 0
const.AZH_MAX_INPUTS 1000000 0
const.AZH_BUTTONS_MASK 53247 0
const.AZH_CIRCLE_MAX 32767 0
const.AZH_SD_EVERY_DEFAULT 30 0
const.AZH_MSG_MAX 256 0
const.AZH_MAX_FIELDS 160 0
const.AZH_MEM_MAX_LEN 67108864 0
const.AZH_MAX_WATCH 32 0
const.AZH_WATCH_MAX_WORDS 256 0
const.AZH_WATCH_EVERY_MAX 100000 0
const.AZH_WATCH_AREA_OFF 696320 0
const.AZH_WATCH_AREA_BYTES 4194304 0
const.AZH_WATCH_HDR_BYTES 64 0
const.AZH_WATCH_ROW_HDR 16 0
```

</details>
