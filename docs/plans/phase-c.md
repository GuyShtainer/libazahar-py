# Phase 2, step C: batches, input, touch, stop reasons, raw shots (item laz-210)

Opus step plan, 2026-11-12, **revision 1 (after `docs/reviews/phase-2-review-1.md`), draft for Phase 2's second
opus review loop. Nobody builds from it until the review passes and the main loop launches the step.** Index:
`docs/plans/phase-2.md`. For one sonnet builder in its own git worktree (`../libazahar-py-c`, branch `step-c`, made
at main by the main loop). It refines `docs/PLAN.md` sections 2.2 and 2.3 and the "Phase C" paragraph of section 3;
where they disagree on a goal, PLAN.md wins and the builder stops and reports.

MAIN = `/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/libazahar-py` (the main checkout: read and copy only).

Builder reads first, in this order: `docs/map/rules.md`; PLAN.md 2.1-2.4 and section 3's Phase C paragraph;
`docs/plans/phase-a.md` sections 3 and 4 (the header and files this step extends); `docs/plans/phase-b.md` section 3
(the test app's control keys and log lines); `~/.claude/c-golden-rules.md`, `~/.claude/python-golden-rules.md`.
Then the Phase A code in the worktree: `host/azhost.h`, `host/azh_internal.h`, `host/run.c`, `host/env.c`,
`host/api.c`, `host/hostmap.c`, `host/log.c`, `host/frame.c`, `host/crop.c`, `host/azhost_main.c`, `Makefile`, and
`tests/check_testapp.py` (its `read_png_rgba` function).

## 1. Goal and gate

Goal: `azh_run` takes input records (buttons, touch, circle pad, held across frames and batches), stops on SD text,
on debug text (our core only), on a guest break, exit or error, and on a wall limit, all reported through one
SET_MESSAGE detector; raw shots (`AZH_FMT_RAW`) put RGBA pixels into the map; the map carries the heartbeat, frame
and vblank totals and the last message; `azhost` gets flags for all of it plus SD seeding; pure-C unit tests
(`make test-host`) cover the pure parts. The ABI header is frozen at checkpoint C1 so step D can start from it.

Gate (PLAN.md section 3, "Phase C"), headless, this Mac, stock core, test app only, 2D mode only (the test app's `v`
is meaningful only in 2D):
1. `make check && make && make test-host` exit 0 with no `warning` in their output; `make test-host` ends with the
   line `test-host: <N> checks, 0 failed` (N at least 77,000: the touch chain alone checks all 76,800 pixels).
2. `nice -n 10 python3 -I tests/gate_c.py` (stdlib only; it runs every scenario below one after another, one emulator
   at a time) prints one line per check, `PASS <id> <detail>`, `FAIL <id> <detail>` or `FAIL slow <id> <detail>`,
   then `gate_c: <n> passed, 0 failed`, and exits 0. Ids: `a1 a2 a3 a4` (scenario a, run twice: `a1.1 ... a4.2`),
   `b1 b2 b3`, `c1 c2 c3 c4`, `d1 d2 d3 d4`, `e1 e2 e3`, `f1 f2 f3 f4` (section 8). C(g) is gate line 1 (the unit
   tests fed recorded messages). A `FAIL slow` (a measured time over its bound on a loaded machine) is rerun once
   with `--only <scenario>` before reporting; both outputs go in the report.
3. Once, a planted red: `gate_c.py --only a --plant-red` (it shifts every planned button frame by two in the expected
   table only) shows `FAIL a2.1`; then the real run passes again. Quote both in the report.

## 2. Facts (checked; SRC = `MAIN/dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/`)

**Button map** (libctru `KEY_*` bit to libretro joypad id; SRC citra_libretro/citra_libretro.cpp:150-193; libctru
`/opt/devkitpro/libctru/include/3ds/services/hid.h:12-34`):

| libctru bit | name | libretro id | | libctru bit | name | libretro id |
|---|---|---|---|---|---|---|
| 0 | A | 8 (A) | | 8 | R | 11 (R) |
| 1 | B | 0 (B) | | 9 | L | 10 (L) |
| 2 | SELECT | 2 | | 10 | X | 9 (X) |
| 3 | START | 3 | | 11 | Y | 1 (Y) |
| 4 | DRIGHT | 7 | | 14 | ZL | 12 (L2) |
| 5 | DLEFT | 6 | | 15 | ZR | 13 (R2) |
| 6 | DUP | 4 | | | | |
| 7 | DDOWN | 5 | | | | |

Allowed mask `0x0000CFFF`. Any other bit in a record is `AZH_E_ARG`. Ids 14 (L3, bound to HOME and the screen swap,
citra_libretro.cpp:185-193, 243-244) and 15 (R3) are never answered as pressed. ZL and ZR reach the guest through
ir:rst (SRC core/hle/service/ir/ir_rst.cpp:56-59, 92-93; its own update period, :144, :156); libctru's `hid.o`
imports `APT_CheckNew3DS`, `irrstInit`, `irrstKeysHeld` (`arm-none-eabi-nm` on `libctru.a`, 2026-11-12), so on a New
3DS `hidKeysHeld` merges them. So ZL/ZR get their own measured offset (kind `irrst`). Guest-only bits to mask out when
comparing: `KEY_TOUCH` 20, `KEY_CSTICK_*` 24-27, `KEY_CPAD_*` 28-31. The test app never exits on START (phase-b
section 3; phase-2.md B10), so scenario (a) may press it.

**How the core reads input.** Buttons: `LibRetroButton::GetStatus` calls the frontend's `input_state_cb(port,
RETRO_DEVICE_JOYPAD, 0, id)` at every HID pad poll (SRC citra_libretro/input/input_factory.cpp:29-31,
core/hle/service/hid/hid.cpp:205-218), which runs at `clock / 234` (hid.h:342), 3.91 polls per VBlank, so its phase
drifts against the VBlank. Circle pad: `input_state_cb(0, RETRO_DEVICE_ANALOG, 0, 0 or 1)`, returned as
`(x / INT16_MAX, -y / INT16_MAX)` (input_factory.cpp:60-66); HID then `roundf(f * 0x9A)` and averages with the 2
previous polls, integer division (hid.cpp:227-241, hid.h:372). Touch: the core reads the pointer once per VBlank in
`PollEvents` (SRC citra_libretro/emu_window/libretro_window.cpp:194-224), which also calls `input_poll_cb` once
(line 204); `PollEvents` runs from `RendererBase::EndFrame` at the end of the renderer's `SwapBuffers`
(video_core/renderer_base.cpp:43-48, renderer_vulkan/renderer_vulkan.cpp:1183), once per guest VBlank
(video_core/gpu.cpp:494). So **`input_poll_cb` calls count guest VBlanks** (one per `retro_run` normally; also during
a savestate drain, step D). The only other `input_poll_cb` caller is the no-game branch (citra_libretro.cpp:221).

**Timing, so the gate expects jitter.** The record for frame i is applied before the i-th `retro_run`; the test app
calls `hidScanInput` right after the VBlank that starts that guest frame. Whether a pad poll lands between the two
varies frame to frame, so a button change usually shows in the log one frame later than its record and sometimes on
the same frame. Touch is latched in `PollEvents` at the VBlank, so it lands one frame later again. Hence the gate's
rule: per kind, every change at offset o or o + 1.

**Pointer device** (SRC citra_libretro/input/mouse_tracker.cpp:132-189): with both touchscreen sources on, the core
reads `RETRO_DEVICE_MOUSE` id `LEFT` (answer 0) and `RETRO_DEVICE_POINTER` ids `X`, `Y`, `PRESSED`;
`newX = static_cast<int>((pointerX + 0x7fff) / (float)(0x7fff * 2) * bufferWidth)` (likewise Y with the height;
:144-145 and :171-172); a point with `pointerX == 0 && pointerY == 0` is ignored; a point applies only if
`newX/newY` differ from the last applied one (so holding the same point is free, and releasing then pressing the same
point keeps it).

**The touch chain, in float32** (the unit test models every step; PLAN 2.3):
1. Bottom pixel (x 0-319, y 0-239), frame pixel X = x + 40, Y = y + 240 (frame 400 x 480 at factor 1).
2. Host pointer, integer only: `px = ((2*X + 1) * 32767) / 400 - 32767`, `py = ((2*Y + 1) * 32767) / 480 - 32767`
   (int64 arithmetic; equals `floor((X + 0.5) * 65534 / 400) - 32767`). Never (0, 0) for X 40-359, Y 240-479.
3. Core: `nx = (int)(((float)(px + 32767) / 65534.0f) * 400.0f)`, `ny` with 480; equals X and Y for every pixel.
4. Frame to touch (SRC core/frontend/emu_window.cpp:155-192): `tx = (float)(nx - 40) / 320`,
   `ty = (float)(ny - 240) / 240` (float division); no swap, because `DefaultFrameLayout` calls `LargeFrameLayout`,
   whose result sets `is_rotated = !upright`, true (core/frontend/framebuffer_layout.cpp:57-60, 160).
5. HID (hid.cpp:292-293): `gx = (uint16_t)(tx * 320.0f)`, `gy = (uint16_t)(ty * 240.0f)`.
Result (recomputed in float32 twice, 2026-11-12): gx == x for all 320 columns; **gy == y - 1 for exactly y = 63, 125,
126, 127**, gy == y otherwise. Pointer examples: x 0 -> -26132, 159 -> -82, 160 -> 81, 319 -> 26131; y 0 -> 68,
63 -> 8669, 120 -> 16451, 239 -> 32698. The unit test file starts with `_Static_assert(FLT_EVAL_METHOD == 0, ...)`;
`make test-host` compiles with `-ffp-contract=off` and never `-ffast-math`.

**Circle pad.** Record fields `cx`, `cy` in -32767..32767, `cy` positive = up. The host answers `RETRO_DEVICE_ANALOG`
index 0 (`RETRO_DEVICE_INDEX_ANALOG_LEFT`) id 0 with `cx` and id 1 with `-cy`; index 1 (right stick) with 0 (the
profile pins the right stick to the C-stick; nothing drives it). Guest steady value
`(int16_t)roundf(((float)c / 32767.0f) * 154.0f)`: 32767 -> 154, 16384 -> 77, -32767 -> -154, 0 -> 0. After a
change, the averaging may show one log line with an in-between value; the next is steady.

**Cursor.** Drawn only when visible (mouse_tracker.cpp:243-246); with the pointer timeout on and the right stick on
C-stick, `last_moved` is never set (mouse_tracker.cpp:191-238), so it is never visible. Its crosshair would be 8 px
each side (`bottom height / 30`, renderer_vulkan.cpp:1065-1080), so gate b3 checks a 17 x 17 box.

**Stop reasons** (PLAN 2.2). `retro_run` loops `while (!HasSubmittedFrame())` over `RunLoop()`; on a non-Success
status it calls `DisplayMessage` = `RETRO_ENVIRONMENT_SET_MESSAGE` (6) with `struct retro_message {const char *msg;
unsigned frames;}` (citra_libretro.cpp:287-306, environment.cpp:169-174) and loops again; `RunLoop` resets the status
to Success first (core/core.cpp:110-111). The text is `"Fatal Error encountered (" + N + "): " + details`, or for
status 10 `"Azahar was unable to locate a 3DS system archive: " + details`. Status numbers (core/core.h:92-113): 14
`ErrorCoreExceptionRaised` (svcBreak: `SVC::Break` logs at critical, then `Core::LogException` sets 14 and returns;
svc.cpp:1148-1166, core/arm/exception_handler.cpp:142; the guest runs on, and the test app logs `f=N+1` after
`break f=N`), 16 `ShutdownRequested` (core.cpp:144, 150; the test app's return from `main` reaches it through APT
close, phase-b section 2), 17 `ErrorUnknown`. During a `retro_run` no other SET_MESSAGE is sent (every other
`DisplayMessage` call is in load or `context_reset`, citra_libretro.cpp:379-603). The core never sends
`RETRO_ENVIRONMENT_SHUTDOWN`. SD file writes are synchronous on the emulator thread (file.cpp:198-217, phase-b
section 2), so a log line written in frame F is on disk when `retro_run` F returns.

**The test app** (`docs/plans/phase-b.md` section 3; all parsing in `tests/testapp_log.py`): control file
`<sys>/Azahar/sdmc/testapp/control.txt`, keys `draw=2d|3d`, `break_at=N`, `exit_at=N`, `ready_at=N`,
`boot_frames=N`; log `<sys>/Azahar/sdmc/testapp/log.txt`, lines `start ...`, per frame
`f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d` (`f` from 1, boot frames included), events
`ready f= v=`, `booted f= v= sum=`, `break f= v=`, `exit f= v=`; 2D loop `hidScanInput`, log, events, draw, swap,
`gspWaitForVBlank0()`. Markers: `python3 -I tests/check_testapp.py markers --top <top.png> --bottom <bottom.png>
--mode 2d` prints `markers ok ...`; the same file's `read_png_rgba(path) -> (width, height, rgba_bytes)` decodes
filter-0 PNGs (phase-2.md B11).

## 3. The header after C1 (frozen; `AZH_ABI_VERSION 2`)

Everything in Phase A's `host/azhost.h` stays as it is, names, values and order (`AZH_E_ORDER` -2,
`AZH_E_SAVESTATE` -10 already reserved, `AZH_INPUT_INTS 7`). C1 makes these changes and no others; after C1 nobody
edits the header (a needed change is reported to the main loop, never made).

### 3.1 Additions

```c
#define AZH_ABI_VERSION 2                       /* was 1 */
/* added to the exit enum: */
AZH_EXIT_NEEDS_LAZPY = 7,                       /* azhost: a debug-text stop asked of the stock core */
AZH_EXIT_UNSUPPORTED = 8                        /* azhost: an entry point still returns AZH_E_UNSUPPORTED */
#define AZH_IN_FRAME 0                          /* field indices inside one AZH_INPUT_INTS record */
#define AZH_IN_BUTTONS 1
#define AZH_IN_TOUCH_X 2
#define AZH_IN_TOUCH_Y 3
#define AZH_IN_TOUCH_DOWN 4
#define AZH_IN_CIRCLE_X 5
#define AZH_IN_CIRCLE_Y 6
#define AZH_MAX_INPUTS 1000000                  /* records per batch */
#define AZH_BUTTONS_MASK 0x0000CFFFu            /* libctru KEY_* bits the host accepts */
#define AZH_CIRCLE_MAX 32767
#define AZH_SD_EVERY_DEFAULT 30
#define AZH_MSG_MAX 256
#define AZH_MAX_FIELDS 96
typedef struct { char name[32]; int32_t offset, size; } azh_field;
```

### 3.2 Struct changes (fields appended at the end only)

- `azh_batch`: append `int32_t sd_from_end;` (1: the SD matcher starts at the file's size when the batch starts, so
  only text written during this batch counts; 0: from byte 0, so text already in the file stops the batch at the
  first check).
- `azh_result`: append `int64_t vblanks;` (guest VBlanks in this batch, counted by `input_poll_cb`) and
  `char message[AZH_MSG_MAX];` (the message that caused a guest stop, truncated, NUL-terminated; empty otherwise).
- `azh_layout`: append `int32_t n_fields; azh_field fields[AZH_MAX_FIELDS];` and nothing else. `fields[]` is the
  single source for every offset Phase 2 adds (no `off_*` duplicates).

`fields[]` lists every field of `azh_shot_req`, `azh_batch`, `azh_result`, `azh_stats` and the map, named
`<struct>.<field>` (`shot.frame`, `batch.frames`, `batch.shots`, `batch.sd_from_end`, `result.vblanks`,
`stats.core_version`, `map.heartbeat`, `map.frame_total`, `map.pixels` ...) with its offset and `sizeof`, plus one
`<struct>.__size__` entry for each struct (offset 0, size `sizeof`) and `map.__size__` (695,296). It is filled by one
function in `api.c` from a static table of `{name, offset, size}` rows, one row per line, plain
`offsetof(azh_batch, frames)` and `sizeof(((azh_batch *)0)->frames)` (no token pasting); map rows use the
`hostmap.c` offset constants. Step D checks every row at import.

### 3.3 The map (bytes 1080-4095 were free in Phase A; the version at offset 8 becomes 2)

| Offset | Type | Field (`fields[]` name) | Written |
|---|---|---|---|
| 1056 | u32 x4 | `map.dims`: top w, top h, bottom w, bottom h | by a RAW shot, before its pixels |
| 1072 | i64 | `map.px_frame`: the absolute frame of the pixels; -1 while a copy is in progress | -1 before the copy, the frame after it (release stores) |
| 1080 | i64 | `map.frame_total`: `retro_run` calls since boot (the absolute frame) | after every `retro_run`, atomic release store |
| 1088 | i64 | `map.vblanks_total`: `input_poll_cb` calls since boot | same |
| 1096 | u32 | `map.msg_seq`: +1 after each SET_MESSAGE is copied into the message field | in the SET_MESSAGE handler |
| 1100 | i32 | `map.pid` of the process that opened the map | at `azh_open` |
| 1104 | i32 | `map.exit_code` the host is about to `_exit` with (0 while alive) | just before `_exit` |
| 4096 | u8[] | `map.pixels`: top RGBA 400 x 240 rows, then bottom RGBA 320 x 240 rows | by a RAW shot |

### 3.4 Semantics of `azh_run`, `azh_set_input` and raw shots

- `n` is the number of records (each `AZH_INPUT_INTS` int32), 0 to `AZH_MAX_INPUTS`; `inputs` may be NULL when n is 0.
- Validation before the first frame (any failure: `AZH_E_ARG`, nothing run, the error text names the record index and
  field): frame 1..`b->frames`; frames non-decreasing; `buttons & ~AZH_BUTTONS_MASK` is 0; touch down 0 or 1; when
  down is 1, x 0-319 and y 0-239 (when 0, x and y are ignored); circle -32767..32767. Several records on one frame:
  applied in order, so the last wins.
- **Movie semantics:** the record for frame i sets the whole held state before the i-th `retro_run` of the batch; the
  held state stays after the batch and into the next one. `azh_set_input(rec)` validates the same way (its frame
  field is ignored) and sets the held state now.
- `sd_file` is relative to `<sysdir>/Azahar/sdmc/`; absolute paths, `..` components and empty text with a non-empty
  file are `AZH_E_ARG`. `sd_every` 0 means `AZH_SD_EVERY_DEFAULT`; 1 to 100,000 otherwise. The check runs after
  frame i when `i % sd_every == 0` and after the batch's last frame.
- `debug_text` non-empty on the stock core: `AZH_E_NEEDS_LAZPY_CORE` before any frame.
- `wall_limit_ms` 0 means none; otherwise checked after every frame against `CLOCK_MONOTONIC` since the batch start.
- After each `retro_run`, in this order: heartbeat (A), `frame_total` and `vblanks_total` into the map, the shot if
  asked (A's PNG path, or RAW), then the stops in priority order: guest exited (our core only; the stock core never
  returns from it), guest error, guest break, debug text, SD text, wall limit, then `frames`. The first that holds
  ends the batch with that `stop_reason`; `frames_run`, `last_frame` and `vblanks` count the frame that triggered it.
- Return 0 for every stop reason, including guest stops (they are results, not call failures).
- **Raw shots** (`AZH_FMT_RAW`, factor 1 only, else `AZH_E_UNSUPPORTED`): `azh_shot(screens, AZH_FMT_RAW, NULL)`
  (the path is ignored) reads back the current frame through A's readback path, crops it with A's `crop.c`, and
  writes `px_frame = -1`, the dims, the asked screens' RGBA rows (alpha 255; an unasked screen's area is left as it
  was), then `px_frame = frame_total`. A batch shot request with format RAW does the same after its `retro_run`;
  later RAW shots overwrite earlier ones, so the map holds the latest. One readback serves a frame asked for both PNG
  and RAW.

### 3.5 The guest-message detector (`host/msg.c`, pure) and the exit path

`azh__msg_status(text)`: N from a text starting `Fatal Error encountered (` followed by 1-3 digits and `)`;
`AZH_MSG_OTHER` (-1) for anything else. `azh__msg_on_message(st, text, is_lazpy)` returns one action:

| Status | Stock core | Our core |
|---|---|---|
| 16 | `AZH_ACT_EXIT_EXITED`: the exit path with stop code `AZH_STOP_GUEST_EXITED`, `_exit(AZH_EXIT_GUEST_EXITED)` | `AZH_ACT_EXITED`: flag; the batch stops when `retro_run` returns |
| 14 | `AZH_ACT_BREAK`: flag | same |
| any other N, or OTHER | `AZH_ACT_ERROR`: flag, count +1; on the 3rd in one `retro_run`, `AZH_ACT_EXIT_ERROR`: the exit path with `AZH_STOP_GUEST_ERROR`, `_exit(AZH_EXIT_GUEST_ERROR)` | `AZH_ACT_ERROR`: flag, no count |

`azh__msg_begin_run(st)` clears the flags and the count before every `retro_run`. The first message of a kind is kept
(`AZH_MSG_MAX`). Messages that arrive while A's boot is in progress go to A's boot-failure path unchanged and never
reach the detector.

The exit path (in `env.c`, one function): write stop code, message, length and `msg_seq`; write **`frame_total + 1`**
and `vblanks_total` (the `retro_run` in progress is the frame that exited, and it counts: a batch that exits on its
k-th frame has run k frames); write `exit_code`; `msync(MS_SYNC)`; one `write(2)` of a fixed line to the log's file
descriptor (no stdio, no mutex: another thread may hold it); `_exit`. `_exit` in our own process replaces longjmp
(C rule 1).

### 3.6 Internal prototypes added to `host/azh_internal.h` at C1 (frozen with the header)

```c
/* input.c (pure) */
typedef struct { uint32_t buttons; int32_t touch_x, touch_y, touch_down, circle_x, circle_y;
                 uint16_t retro_mask; int16_t ptr_x, ptr_y; } azh_held;
int azh__input_validate(const int32_t *rec, int32_t n, int32_t frames, char *err, size_t errcap);
void azh__held_from_record(azh_held *h, const int32_t rec[AZH_INPUT_INTS]);
int16_t azh__held_query(const azh_held *h, unsigned port, unsigned device, unsigned index, unsigned id);
void azh__touch_pointer(int32_t x, int32_t y, int16_t *px, int16_t *py);
void azh__model_frame_pixel(int16_t px, int16_t py, int32_t *fx, int32_t *fy);
void azh__model_guest_touch(int32_t fx, int32_t fy, uint16_t *gx, uint16_t *gy);
int16_t azh__model_guest_circle(int32_t c);
/* input glue (run.c): the held state, the two libretro input callbacks, the vblank counter */
void azh__input_set(const azh_held *h);
void azh__input_get(azh_held *h);
int64_t azh__vblanks_total(void);
/* match.c (pure) */
typedef struct { char text[256]; size_t len; char carry[255]; size_t carry_len; int64_t offset; } azh_matcher;
int azh__match_init(azh_matcher *m, const char *text, int64_t start_offset);
int azh__match_feed(azh_matcher *m, const char *buf, size_t n);      /* 1 found, 0 not */
void azh__match_restart(azh_matcher *m);
int azh__match_poll_file(azh_matcher *m, const char *path);          /* 1 found, 0 not, <0 AZH_E_IO */
/* msg.c (pure) */
enum { AZH_MSG_OTHER = -1 };
enum { AZH_ACT_NONE = 0, AZH_ACT_BREAK, AZH_ACT_ERROR, AZH_ACT_EXITED, AZH_ACT_EXIT_EXITED, AZH_ACT_EXIT_ERROR };
typedef struct { int32_t brk, err, exited, err_count; char first[AZH_MSG_MAX]; } azh_msgstate;
int azh__msg_status(const char *text);
void azh__msg_begin_run(azh_msgstate *st);
int azh__msg_on_message(azh_msgstate *st, const char *text, int is_lazpy);
/* sdcopy.c */
int azh__copy_tree(const char *src, const char *dst);   /* dst must not exist; regular files and dirs only */
int azh__clear_tree(const char *dir);                   /* removes dir's contents, keeps dir */
/* log.c additions */
void azh__log_set_debug_stop(const char *text_or_null); /* arms or disarms; clears the hit flag */
int azh__log_debug_hit(void);                           /* atomic */
int azh__log_fd(void);
/* run.c additions, for step D */
int azh__run_one_frame(void);                           /* one retro_run with the message, heartbeat and counter
                                                           handling of a batch frame; no shots, no stops */
void azh__counters_set(int64_t frame_total, int64_t vblanks_total);
void azh__counters_get(int64_t *frame_total, int64_t *vblanks_total);
int azh__sd_root(char *buf, size_t cap);                /* <sysdir>/Azahar/sdmc */
/* state.c and statemeta.c: step D owns them; C1 creates stubs */
void azh__state_note_app(const char *app);              /* api.c's azh_boot calls it on every boot */
int azh__state_boot(const char *app, const char *state_path);
int azh__state_save(const char *path, int32_t *k_out);
int azh__state_load(const char *path);
typedef struct { int32_t abi, k; int64_t frame_total, vblanks_total, created; char core_version[128];
                 char app[AZH_PATH_MAX]; } azh_state_meta;
int azh__meta_format(const azh_state_meta *m, char *buf, size_t cap);    /* bytes written, or AZH_E_ARG */
int azh__meta_parse(const char *text, size_t len, azh_state_meta *m);    /* 0 or AZH_E_SAVESTATE */
int azh__meta_write(const char *path, const azh_state_meta *m);          /* <path>.tmp then rename */
int azh__meta_read(const char *path, azh_state_meta *m);
```
If Phase A's state struct lacks the sysdir, C1 adds it there.

## 4. Behaviour details

- **Input callbacks** (in `run.c`; set with `retro_set_input_state` / `retro_set_input_poll`, replacing A's stubs if
  A has them): `input_state_cb` returns `azh__held_query(&held, ...)`: JOYPAD port 0 ids 0-13 from the mapped mask,
  id `RETRO_DEVICE_ID_JOYPAD_MASK` (256) the whole mask, 14 and 15 always 0; ANALOG port 0 index 0 ids 0/1 as section
  2, index 1 always 0; POINTER port 0 index 0 ids X, Y, PRESSED (`ptr_x`, `ptr_y`, 1) while touch down, and 0, 0, 0
  otherwise; any other port, device or id 0. `input_poll_cb` adds 1 to the vblank counter. Both run on the thread
  that called `retro_run` (the core runs the guest inside it); the held state is only written between `retro_run`
  calls on the same thread, so no lock; one assert checks the thread.
- **SD match** (`match.c`): `azh__match_poll_file` stats the file; missing: no match; size below the offset (the
  file shrank or was recreated): restart at 0 with an empty carry; then reads the new bytes in 64 KiB chunks (a loop
  bounded by the size read at the stat) and feeds each as carry + chunk; keeps the last `len - 1` bytes as the next
  carry, so a text split across two reads is found. Text length 1-255.
- **Debug text** (our core only): while a debug stop is armed (`azh__log_set_debug_stop` with text, done by
  `azh_run` for the batch and disarmed after it), `log.c`'s core-log callback formats every line, whatever its level,
  and `strstr`s it (the guest's `svcOutputDebugString` arrives at debug level, SRC svc.cpp:1170-1190); a hit sets an
  atomic flag the batch loop reads after each `retro_run`. While unarmed, a line below the threshold returns before
  any formatting (A's callback otherwise unchanged). Lines arrive whole, so no carry.
- **Wall limit**: compared after each frame; the stop happens between frames, never inside one.
- **SD seeding** (`azhost --sd-seed DIR`): before `azh_boot`, `azh__copy_tree(DIR, <sys>/Azahar/sdmc)` (the
  destination must not exist yet, so a reused `--sys` with an SD folder is `UsageError:`; the gate uses fresh
  folders). `sdcopy.c` walks with `fts_open(FTS_PHYSICAL)`, refuses symlinks and anything not a regular file or a
  directory (`AZH_E_ARG`), caps at 100,000 entries, makes directories with mode 0755, and copies each file with
  `copyfile(src, dst, NULL, COPYFILE_CLONE)` (an APFS clone where possible, a copy otherwise; `<copyfile.h>`), each
  return checked. `azh__clear_tree` is a post-order `fts` walk (`unlink`, `rmdir`), same cap. The library never
  seeds by itself (the Python layer does, step D).

## 5. Files (the builder creates or edits only these)

| Path | New or edited | Role |
|---|---|---|
| `host/azhost.h` | edit (C1, then frozen) | section 3 |
| `host/azh_internal.h` | edit (C1, then frozen) | section 3.6 |
| `host/input.c` | new | pure: validation, records to held state, the query, the touch pointer, the three model functions |
| `host/match.c` | new | pure: the SD matcher |
| `host/msg.c` | new | pure: status parse and the action table |
| `host/sdcopy.c` | new | copy and clear a tree (POSIX `fts` and `copyfile` only, no libretro) |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | new at C1, **stubs only**, then step D's | `azh__state_note_app` keeps the path in a file static; the other `azh__state_*` and every `azh__meta_*` return `AZH_E_UNSUPPORTED`; `test_statemeta()` registers 0 checks |
| `host/run.c` | edit | the batch loop of 3.4, the input callbacks, counters, `azh__run_one_frame`, `azh__sd_root`, batch RAW shots |
| `host/frame.c` | edit | the RAW copy into the map (section 3.4), beside A's PNG path |
| `host/env.c` | edit (the SET_MESSAGE case only) | after A's copy into the map: `msg_seq`, then, once booted, the detector and the exit path |
| `host/log.c` | edit | the armed debug observer and the early return, `azh__log_fd` |
| `host/hostmap.c` | edit | the new map fields and their offset constants, version 2, `px_frame` |
| `host/api.c` | edit | `azh_run` (validation, no more UNSUPPORTED for n > 0), `azh_set_input`, `azh_shot`'s RAW branch, `azh_abi_layout` (the `fields[]` table); `azh_boot` calls `azh__state_note_app` and, with a state, `azh__state_boot`; `azh_save_state`, `azh_load_state` call `state.c` |
| `host/crop.c` | only if A's signature does not fit the RAW copy (then report the change) | A's pure crop |
| `host/libazhost.exports` | only if a new public symbol appears (none planned) | |
| `host/azhost_main.c` | edit | section 6 |
| `Makefile` | edit | `test-host` target; the new `.c` files in the library; `check` covers them |
| `tests/host/test_main.c`, `test_input.c`, `test_touch.c`, `test_match.c`, `test_msg.c`, `test_crop.c`, `test_png.c`, `test_sdcopy.c`, `tests/host/messages.txt` | new | section 7 |
| `tests/testapp_log.py` | new | the only place that knows B's control and log formats: `write_control(seed_dir, **keys)`, `parse_log(path) -> (frames, events)` (frames: list of dicts with int fields `f v k tx ty td cx cy`), `read_png(path)` = `check_testapp.read_png_rgba` (imported, never copied) |
| `tests/checks_c.py` | new | pure check functions over parsed logs and summaries (D reuses them): `change_offsets(lines, plan, kind)`, `offsets_ok(offsets) -> (ok, counts)` (all at o or o + 1, the commoner at least 90 %), `touch_expected(x, y)` (the float32 model in Python with `struct` round trips), `circle_expected(c)`, `parse_summary(line)`, `read_map(path, layout_rows)` |
| `tests/gate_c.py` | new | section 8; stdlib; inserts its own folder on `sys.path` (it runs with `-I`); under about 300 lines |

No item files: the report's "Lessons and notes" block (section 12) is for the main loop. Every C function under about
60 lines with about 2 asserts; no goto, recursion or setjmp; every loop bounded; every return value used; function
pointers only for the libretro callbacks (A's documented exception). Python files: type hints, docstrings, no
third-party imports, `python3 -I` clean.

## 6. `azhost` additions (A's `run` flags and summary unchanged)

```
--inputs FILE        records, one per line: 7 integers separated by spaces or commas (strtol base 0, so 0x10 works),
                     '#' to end of line is a comment; validated by azh_run
--sd-seed DIR        copied into <sys>/Azahar/sdmc before boot
--stop-file REL --stop-text TEXT [--stop-every K] [--stop-new]     the SD rule (--stop-new sets sd_from_end)
--debug-stop TEXT    our core only; the stock core gives "NeedsLazpyCore: ..." and exit 7
--wall-limit-ms MS
--frames N[,N2,...]  several batches in one process, run in order; inputs, shots and the SD and debug rules apply to
                     the first batch only; the wall limit applies to every batch; the held input carries over
--raw-shot F         one RAW shot (both screens) at frame F of the first batch, into the map
--print-last-line REL   after each batch, print "last <batch>: <last complete line of that SD file>"
--save FILE          after the last batch, azh_save_state(FILE) and print "saved k=<k> frame=<frame_total>";
                     until step D fills state.c: "Unsupported: ..." and exit 8
```
Per batch, one stdout line: A's fields first, then `stop=<frames|sd_text|debug_text|guest_break|guest_exited|
guest_error|wall_limit> first=<a> last=<b> vblanks=<v> wall_ms_max=<longest frame of the batch> batch=<j>
msg="<message, \" and newlines escaped>"`. Exit code: 0, or `AZH_EXIT_GUEST_EXITED` (10) / `AZH_EXIT_GUEST_ERROR`
(11) when a batch stopped that way on our core (on the stock core the process `_exit`s with those codes from inside
the run, with no summary line). New subcommand `azhost layout`: prints `abi=2`, then one line per `fields[]` entry,
`<name> <offset> <size>`.

## 7. Unit tests (`make test-host`, no core, no Vulkan)

`build/test-host` links `input.c match.c msg.c crop.c png.c sdcopy.c statemeta.c` and `tests/host/*.c` with the
library's CFLAGS plus `-ffp-contract=off`; `test_main.c` runs each file's entry function, counts checks, prints
`test-host: <N> checks, <F> failed` and exits non-zero on any failure. A check is one call of a function
`check(int ok, const char *fmt, ...)` that prints the failing case (no macros beyond what the golden rules allow).
- `test_touch.c`: every (x, y) of 320 x 240: the pointer is never (0, 0); the frame pixel equals (x + 40, y + 240); gx
  == x; gy == y except y in {63, 125, 126, 127} where gy == y - 1 (exactly 4 x 320 such points); the 8 pointer
  examples of section 2; `FLT_EVAL_METHOD == 0` asserted at compile time.
- `test_input.c`: validation (frame 0, frame > frames, decreasing frames, each disallowed bit 12, 13, 16-31, touch
  down 2, x 320, y 240, circle 32768 and -32768, n > `AZH_MAX_INPUTS`); each of the 14 bits maps to its id and only
  it; MASK query; ids 14 and 15 always 0; ANALOG left x, y sign, right 0; POINTER pressed and released; MOUSE 0; port
  1 is 0; last record on a frame wins; circle model values of section 2.
- `test_match.c` (files under a `mkdtemp` folder in `$TMPDIR`): text in one write; text split across two appends at
  every split point of a 5-byte text; a text across a 64 KiB chunk boundary; shrink then rewrite restarts; missing
  file; `sd_from_end` ignores old text; lengths 1 and 255.
- `test_msg.c`: every line of `messages.txt` (format: `<expected status> <expected action stock> <expected action
  lazpy> <message text>`); synthetic cases: 14 -> BREAK; 16 -> EXIT_EXITED (stock) and EXITED (ours); 17 once ->
  ERROR, three in one run -> EXIT_ERROR, three across two runs (begin_run between) -> ERROR only; the status 10 text ->
  OTHER -> ERROR; `(1x)`, `()`, `(9999)`, a NUL-free 300-byte message (truncated to `AZH_MSG_MAX`).
- `test_crop.c`: a synthetic 400 x 480 frame with a pattern; top and bottom crops at factor 1 and 2 (A's function).
- `test_png.c`: write a 3 x 2 RGBA image; read it back with zlib `uncompress`; check signature, IHDR, every CRC,
  filter bytes 0, pixels.
- `test_sdcopy.c`: nested copy matches byte for byte; a symlink is refused (the error is returned); clear_tree
  empties and keeps the folder; an existing destination is refused.
- `test_statemeta.c`: step D fills it.

## 8. The gate scenarios (`tests/gate_c.py`)

Each scenario: a fresh `runs/c-gate/<id>/` with `sys/`, `out/` and a seed folder `seed/testapp/control.txt` (written
by `testapp_log.write_control`, passed with `--sd-seed`), then one
`nice -n 10 build/azhost run build/testapp.3dsx --sys ... --out ... --sd-seed ... <flags>` with a timeout of 600 s
(it kills only its own child on timeout and prints `FAIL <id> timeout`). Frames below are host batch frames; a
change's "offset" is `v` of the first log line that shows it minus its planned frame, and `c` (the boot offset of a
run) is a batch's `last` minus the `v` of that batch's last per-frame line.
- **(a) buttons and circle pad**, run twice (`.1`, `.2`) (`--frames 900 --inputs a.txt --shot 600`): from frame 300,
  each of the 14 bits alone for 6 frames with 6 released frames between, then `A|B`, `L|R|ZL|ZR`,
  `START|SELECT|DUP` 6 frames each, then circle (32767, 0), (0, 32767), (-32767, -32767), (16384, -16384), (0, 0) for
  10 frames each.
  a1: for every bit, each planned rise and fall is found in the log (`k & 0xCFFF`) and the bit is held for its planned
  frames (plus or minus one, from the jitter); within a combo every bit rises within one line of the others;
  a2: per kind (`hid`: all bits but ZL and ZR; `irrst`: ZL, ZR), every change's offset is o or o + 1 and the commoner
  value covers at least 90 % of that kind's changes (`checks_c.offsets_ok`); counts printed;
  a3: every circle step reaches its steady value (section 2) at offset o or o + 1 after at most one in-between line;
  counts printed;
  a4: the summary has `stop=frames`, `vblanks=900`; the markers check passes on the frame-600 shot.
- **(b) touch** (`--frames 800 --inputs b.txt --shot 700,780`): 20 points held 6 frames each with 6 released frames
  between, from frame 300: (0,0) (319,0) (0,239) (319,239) (160,120) (10,63) (20,125) (30,126) (40,127) (1,1)
  (318,238) (100,62) (200,64) (50,200) (250,30) (10,128) (300,124) (159,159) (160,63) (80,126); then (160,120) held
  from frame 690 to 720.
  b1: each point appears as `tx ty td=1` equal to `touch_expected(x, y)` and each release as `td=0`; b2: the 40
  changes' offsets pass `offsets_ok` (expected about one frame later than `hid`); counts printed; b3: in the bottom
  shots of frames 700 (touch held) and 780 (released), the 17 x 17 box centred on (160, 120) is identical and every
  pixel in it is `#202020`.
- **(c) stop rules**: `ready_at=200`. c1: `--frames 3000 --stop-file testapp/log.txt --stop-text "ready f=" --stop-every
  30`: `stop=sd_text`, and the delay (the last per-frame line's `v` minus the `ready` line's `v`) is 0 to 30;
  c2: the same with `--stop-every 1`: delay 0 or 1; c3: `--frames 300,10000000 --wall-limit-ms 3000`: batch 2 has
  `stop=wall_limit` and `wall` at most 3.0 s plus batch 1's `wall_ms_max` (over it: `FAIL slow c3`); c4:
  `--frames 600 --debug-stop ready`: exit 7, stderr starts `NeedsLazpyCore:`. Delays and walls printed.
- **(d) vblanks and raw pixels** (`--frames 300,600,1200 --print-last-line testapp/log.txt --shot 300 --raw-shot
  300`): d1: each batch's `vblanks` equals its frames; d2: across the whole log every per-frame line's `v` and `f` are
  the previous plus 1; d3: every batch's c equals batch 1's (SD writes are synchronous, so exact); the c values
  printed; d4: in `host.map` (read at the offsets `azhost layout` prints), `px_frame` is 300, the dims are 400, 240,
  320, 240, and the top and bottom pixel areas equal, byte for byte, the RGBA of `shot_000300_top.png` and
  `shot_000300_bottom.png` (decoded with `read_png_rgba`).
- **(e) break** (`break_at=120`, `--frames 600,120`): e1: batch 1 `stop=guest_break`, `msg` contains `(14)`, and
  `last` is at most the `break` line's `v` + c + 2; e2: batch 2 `stop=frames`, `vblanks=120`; e3: the log has
  per-frame lines after the `break` line, the first with `f` one more than the break's.
- **(f) exit** (`exit_at=200`, `--frames 100,600 --print-last-line testapp/log.txt`; c from batch 1): f1: exit code
  10; f2: `host.map` stop code 4 (`AZH_STOP_GUEST_EXITED`), `exit_code` 10, message contains `(16)`; f3: the map's
  `frame_total` minus (the `exit` line's `v` + c) is 0 to 10 (the frame that exited counts; printed); f4: the log's
  last line is `exit f=200 ...`.
The offsets and their counts, delays, c values and walls go into the report; USING.md (step D) quotes the offsets.

## 9. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree** (it has no `dl/`, `vendor/` or `build/`, all ignored): `mkdir -p dl && cp -R MAIN/dl/azahar
   MAIN/dl/moltenvk MAIN/dl/libretro-headers MAIN/dl/vulkan-headers dl/`, `cp -R MAIN/vendor .`; `make`; then
   `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (or copy `MAIN/build/testapp.3dsx`
   if it exists). Checkpoint: one by-hand `azhost run build/testapp.3dsx ... --frames 600 --shot 600` passes the
   markers check.
1. **C1, the freeze (about 0.45 h).** The header and internal header of section 3; `input.c`, `match.c`, `msg.c`,
   `sdcopy.c`; the stubs `state.c`, `statemeta.c`, `test_statemeta.c`; the `api.c` routing to the stubs (and the
   `azh__state_note_app` call in `azh_boot`); in `run.c` the four functions step D links against
   (`azh__counters_set`, `azh__counters_get` and `azh__sd_root` real, `azh__run_one_frame` real or a stub returning
   `AZH_E_UNSUPPORTED` until C2, so D's code links from the C1 commit); `azh_abi_layout`'s table; the map fields in
   `hostmap.c`; `make test-host` with every section 7 test. Checkpoint: `make check && make && make test-host` clean;
   `build/azhost layout` prints the table; the step 0 run still passes. **Then end your run**: your final report is
   the "C1 done" report (the exact list of C1 paths, the `make test-host` count line, `azhost layout`'s output, and
   anything in the header that differs from section 3, which must be nothing). Do not start C2. The main loop
   commits C1 and resumes you with "C1 committed at <sha>, go on with C2".
2. **C2, the run loop and raw shots (about 0.6 h).** `run.c` (callbacks, held state, the batch loop, counters, batch
   RAW shots), `frame.c` and `api.c` (RAW), `env.c` (detector, exit path), `log.c` (observer). Checkpoint: one
   by-hand run with `--inputs` pressing A from frame 300 shows `k=00000001` lines in the log; one `--raw-shot` run
   shows non-zero pixels in the map.
3. **C3, flags, seeding and the gate (about 0.5 h).** `azhost_main.c` flags; `testapp_log.py`, `checks_c.py`,
   `gate_c.py`; launch the gate in the background (`nice -n 10 python3 -I tests/gate_c.py > runs/c-gate.log 2>&1`)
   and be woken when it exits (never `sleep`-poll); copy the real `(14)` and `(16)` messages from the scenario
   `host.log` files into `messages.txt` and rerun `make test-host`; the planted red. Checkpoint: the whole gate passes;
   quote it.
4. The report (section 12) ends the run. If the opus review asks for fixes, the main loop resumes you again.

## 10. Machine-sharing rules

- One emulator instance at a time (the gate runs its scenarios one after another; never two `azhost` at once), always
  `nice -n 10`, all folders under `runs/c-*` (ignored). Step D's builder runs no emulator while C is building.
- Never open a window: no Azahar app, no `open`, no Preview; look at PNGs with the Read tool.
- Never kill a process you did not start; the gate kills only its own child, only on its timeout.
- Expect slow frames under shared load: a 900-frame run can take a few minutes; the 600 s timeout covers it. Note the
  load average beside the gate output.
- The background gate wakes you on exit; while it runs, do review work, not more emulator runs.

## 11. Files the builder must not touch

Everything outside section 5, in particular: `core/`, `testapp/`, `host/core.c`, `tests/gate-a.sh`,
`tests/gate-b.sh`, `tests/check_testapp.py` (import its decoder and call its CLI, never edit it),
`tests/test_version.c`, `.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`, `docs/hours.tsv`, the handoff,
every item file, `prototype/`, `tools/`, `README.md`, and MAIN (read and copy only). After C1: `host/state.c`,
`host/statemeta.c`, `tests/host/test_statemeta.c` belong to step D, and the two headers are frozen.

## 12. The builder's report

The gate output and the planted red, as printed (and any `FAIL slow` rerun); the measured offsets with their counts
(`hid`, `irrst`, circle, touch) for both (a) runs, the SD stop delays, c values, the c3 walls, f3's exit delay; the
`make test-host` count line; the analyzer result; line counts per new or edited file and the longest function;
anything the core did that section 2 did not predict; the runners block for `docs/map/runners.md`:
```
make test-host                                        # pure-C unit tests
build/azhost run <app> ... --inputs f --stop-file REL --stop-text T --frames N[,N2] [--raw-shot F]
build/azhost layout                                   # the ABI table
python3 -I tests/gate_c.py [--only a,b]               # step C's gate
```
lines the main loop must add to `.gitignore` (none expected); and a final **"Lessons and notes"** block, ready to
paste into item 210.

## 13. Hours (agent wall time)

Builder 1.55 h (C1 0.45, C2 0.6 with raw shots, C3 0.5), the opus diff review 0.25 h, the commit 0.1 h: **1.9 h**,
against PLAN.md's 2.0 (A already ships `azh_stats`, the crop and the input record size; the pure checks are written
once and reused by D).

## 14. Review checklist (the opus as-built review)

1. Header: exactly section 3's changes; A's names, values and order kept; `AZH_ABI_VERSION 2`; `azh_abi_layout`'s
   `fields[]` filled from real `offsetof`/`sizeof` and `hostmap.c`'s constants, one row per field, no token pasting;
   the map version 2 and the new offsets.
2. Inputs: the button table exact (ZR is 13, not 14; ids 14 and 15 never pressed); the mask; validation complete with
   the record index in the error; last record on a frame wins; held state survives batches; `azh_set_input` same rules.
3. Touch: the integer pointer formula; (0, 0) impossible; the float32 model matches section 2 step by step;
   `-ffp-contract=off` and the `FLT_EVAL_METHOD` assert; the test covers all 76,800 pixels and the 4 rows.
4. Circle: y sign (API up positive, libretro y = -up); right stick 0; the model values.
5. Stops: the order of 3.4; the detector table of 3.5 for both cores; flags cleared per `retro_run`; boot messages
   untouched; the exit path writes `frame_total + 1`, `msync`s, uses `write(2)` without the log mutex; exit codes 10
   and 11.
6. Raw shots: factor 1 only; `px_frame` -1 during the copy; one readback for PNG and RAW on the same frame; unasked
   screen untouched; d4 compares against the PNG byte for byte.
7. SD match: only new bytes; the carry of `len - 1`; shrink restarts; bounded loop; missing file is no match;
   `sd_from_end`; relative paths only, `..` refused.
8. Debug text: formatted and matched only while armed; the early return otherwise; atomic flag; refused on the stock
   core with `AZH_E_NEEDS_LAZPY_CORE` before any frame.
9. Counters: `vblanks` from `input_poll_cb` only; `frame_total` and `vblanks_total` in the map after each frame;
   `azh__run_one_frame` and `azh__counters_*` exist for D.
10. sdcopy: no symlinks, bounded, `copyfile` returns checked, destination must not exist; clear keeps the folder.
11. The gate: every scenario of section 8, fresh folders, one instance at a time, nice, its own child only, bounded
    timeouts, the jitter rule as written (not loosened), `FAIL slow` reruns, the planted red; `testapp_log.py` is the
    only file parsing B's formats and imports B's decoder; `checks_c.py` functions pure.
12. C rules: functions under about 60 lines, about 2 asserts, no goto/recursion/setjmp, bounded loops, returns used,
    one state struct, file statics elsewhere; Python rules: type hints, docstrings, stdlib only, `-I` clean.
13. Nothing outside section 5 changed; no item file; no build outputs, PNGs, logs or `runs/` in the diff.

## 15. Interfaces assumed from Phase 1

`docs/plans/phase-2.md` section 5 lists them with their sources. The ones this brief leans on most: A1 (A's header),
A3 (`n` counts records), A4 (`azh_boot` runs no `retro_run`; `frame_total` counts every `retro_run` either way), A5
(map bytes 1080-4095 free), A6 (the state struct), A7 (A's SET_MESSAGE handler), A8 (the log callback), A9 (A's
`crop.c`), A11 (the `azhost run` flags and summary), A13 (the profile), A18 and A19 (the RAW entry point and A's
readback), B2-B5, B8-B11 (control keys, log lines, loop order, break, markers, ready, no START exit, `read_png_rgba`).
If the merged code differs in a name, follow the code and report the difference; if it differs in behaviour this
brief relies on, stop and report.
