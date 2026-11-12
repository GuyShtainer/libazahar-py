# Phase 2, step C: batches, input, touch, stop reasons (item laz-210)

Opus step plan, 2026-11-12, **draft for Phase 2's two opus review loops. Nobody builds from it until the reviews
pass and the main loop launches the step.** Index: `docs/plans/phase-2.md`. For one sonnet builder in its own git
worktree (`../wt-c`, branch `step-c`, made at main by the main loop). It refines `docs/PLAN.md` sections 2.2 and 2.3
and the "Phase C" paragraph of section 3; where they disagree on a goal, PLAN.md wins and the builder stops and
reports.

Builder reads first, in this order: `docs/map/rules.md`; PLAN.md 2.1-2.4 and section 3's Phase C paragraph;
`docs/plans/phase-a.md` sections 3 and 4 (the header and files this step extends); `docs/plans/phase-b.md` section 3
(the test app's control keys and log lines); `~/.claude/c-golden-rules.md`, `~/.claude/python-golden-rules.md`.
Then the Phase A code on main: `host/azhost.h`, `host/azh_internal.h`, `host/run.c`, `host/env.c`, `host/api.c`,
`host/hostmap.c`, `host/log.c`, `host/frame.c`, `host/azhost_main.c`, `Makefile`.

## 1. Goal and gate

Goal: `azh_run` takes input records (buttons, touch, circle pad, held across frames and batches), stops on SD text,
on debug text (our core only), on a guest break, exit or error, and on a wall limit, all reported through one
SET_MESSAGE detector; the map carries the heartbeat, frame and vblank totals and the last message; `azhost` gets
flags for all of it plus SD seeding; pure-C unit tests (`make test-host`) cover the pure parts. The ABI header is
frozen at checkpoint C1 so step D can start from it.

Gate (PLAN.md section 3, "Phase C"), headless, this Mac, stock core, test app only:
1. `make check && make && make test-host` exit 0 with no `warning` in their output; `make test-host` ends with the
   line `test-host: <N> checks, 0 failed` (N at least 77,000: the touch chain alone checks all 76,800 pixels).
2. `nice -n 10 python3 -I tests/gate_c.py` (stdlib only; it runs every scenario below one after another, one emulator
   at a time) prints one line per check, `PASS <id> <detail>` or `FAIL <id> <detail>`, then
   `gate_c: <n> passed, 0 failed`, and exits 0. Ids: `a1 a2 a3 a4 b1 b2 b3 c1 c2 c3 c4 d1 d2 d3 e1 e2 e3 f1 f2 f3`
   (section 8). C(g) is gate line 1 (the unit tests fed recorded messages).
3. Once, a planted red: run `gate_c.py --only a --plant-red` (it shifts every planned button frame by one in the
   expected table only) and see `FAIL a2`; then the real run passes again. Quote both in the report.

## 2. Facts (checked; SRC = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/` in the main checkout)

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
ir:rst (SRC core/hle/service/ir/ir_rst.cpp:56-59, 92-93); libctru's `hid.o` references `APT_CheckNew3DS`,
`irrstInit`, `irrstKeysHeld` (`arm-none-eabi-nm` on `libctru.a`, 2026-11-12), so on a New 3DS `hidKeysHeld` merges
them. ir:rst updates on its own timer, so ZL/ZR get their own measured offset (kind `irrst`). Guest-only bits to mask
out when comparing: `KEY_TOUCH` 20, `KEY_CSTICK_*` 24-27, `KEY_CPAD_*` 28-31.

**How the core reads input.** Buttons: `LibRetroButton::GetStatus` calls the frontend's `input_state_cb(port,
RETRO_DEVICE_JOYPAD, 0, id)` at every HID pad poll (SRC citra_libretro/input/input_factory.cpp:29-31,
core/hle/service/hid/hid.cpp:205-218); about 4 polls per frame. Circle pad: `input_state_cb(0, RETRO_DEVICE_ANALOG,
0, 0 or 1)`, returned as `(x / INT16_MAX, -y / INT16_MAX)` (input_factory.cpp:60-66); HID then
`roundf(f * 0x9A)` and averages with the 2 previous polls, integer division (hid.cpp:227-241, hid.h:372). Touch:
the core reads the pointer once per VBlank in `PollEvents` (SRC citra_libretro/emu_window/libretro_window.cpp:194-224),
which also calls `input_poll_cb` once (line 204); `PollEvents` runs from `RendererBase::EndFrame` at the end of the
renderer's `SwapBuffers` (video_core/renderer_base.cpp:43-48, renderer_vulkan/renderer_vulkan.cpp:1182), once per
guest VBlank (video_core/gpu.cpp:494). So **`input_poll_cb` calls count guest VBlanks** (one per `retro_run`
normally; also during a savestate drain, step D). The only other `input_poll_cb` caller is the no-game branch
(citra_libretro.cpp:221).

**Pointer device** (SRC citra_libretro/input/mouse_tracker.cpp:132-189): with both touchscreen sources on, the core
reads `RETRO_DEVICE_MOUSE` id `LEFT` (answer 0) and `RETRO_DEVICE_POINTER` ids `X`, `Y`, `PRESSED`;
`newX = static_cast<int>((pointerX + 0x7fff) / (float)(0x7fff * 2) * bufferWidth)` (likewise Y with the height); a
point with `pointerX == 0 && pointerY == 0` is ignored; a point applies only if `newX/newY` differ from the last
applied one (so holding the same point is free, and releasing then pressing the same point keeps it).

**The touch chain, in float32** (the unit test models every step; PLAN 2.3):
1. Bottom pixel (x 0-319, y 0-239), frame pixel X = x + 40, Y = y + 240 (frame 400 x 480 at factor 1).
2. Host pointer, integer only: `px = ((2*X + 1) * 32767) / 400 - 32767`, `py = ((2*Y + 1) * 32767) / 480 - 32767`
   (int64 arithmetic; equals `floor((X + 0.5) * 65534 / 400) - 32767`). Never (0, 0) for X 40-359, Y 240-479.
3. Core: `nx = (int)(((float)(px + 32767) / 65534.0f) * 400.0f)`, `ny` with 480; equals X and Y for every pixel.
4. Frame to touch (SRC core/frontend/emu_window.cpp:155-192; no swap because the default layout's `is_rotated` is
   true, core/frontend/framebuffer_layout.cpp:290): `tx = (float)(nx - 40) / 320`, `ty = (float)(ny - 240) / 240`
   (float division).
5. HID (hid.cpp:292-293): `gx = (uint16_t)(tx * 320.0f)`, `gy = (uint16_t)(ty * 240.0f)`.
Result (recomputed in float32, 2026-11-12): gx == x for all 320 columns; **gy == y - 1 for exactly y = 63, 125, 126,
127**, gy == y otherwise. Pointer examples: x 0 -> -26132, 159 -> -82, 160 -> 81, 319 -> 26131; y 0 -> 68,
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
to Success first (core/core.cpp:111). The text is `"Fatal Error encountered (" + N + "): " + details`, or for status
10 `"Azahar was unable to locate a 3DS system archive: " + details`. Status numbers (core/core.h:92-113): 14
`ErrorCoreExceptionRaised` (svcBreak: `SVC::Break` logs at critical, then `Core::LogException` sets 14 and returns;
svc.cpp:1148-1166, core/arm/exception_handler.cpp:142; the guest runs on), 16 `ShutdownRequested` (core.cpp:144,
150), 17 `ErrorUnknown`. During a `retro_run` no other SET_MESSAGE is sent (every other `DisplayMessage` call is in
load or `context_reset`, citra_libretro.cpp:379-603). The core never sends `RETRO_ENVIRONMENT_SHUTDOWN`.

**The test app** (`docs/plans/phase-b.md` section 3; the gate depends on these, all parsing in `tests/testapp_log.py`):
control file `<sys>/Azahar/sdmc/testapp/control.txt`, keys `draw=2d|3d`, `break_at=N`, `exit_at=N`, `ready_at=N`,
`boot_frames=N`; log `<sys>/Azahar/sdmc/testapp/log.txt`, lines `start ...`, per frame
`f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d`, events `ready f= v=`, `booted f= v=`,
`break f= v=`, `exit f= v=`; main loop `hidScanInput`, log, draw, swap, `gspWaitForVBlank0()`. Markers check:
`python3 -I tests/check_testapp.py markers --top <top.png> --bottom <bottom.png> --mode 2d` prints `markers ok ...`.

## 3. The header after C1 (frozen; `AZH_ABI_VERSION 2`)

Everything in Phase A's `host/azhost.h` stays as it is, names and order. C1 makes these changes and no others; after
C1 nobody edits the header (a needed change is reported to the main loop, never made).

### 3.1 Additions

```c
#define AZH_ABI_VERSION 2                       /* was 1 */
/* added after AZH_E_NEEDS_LAZPY_CORE in the error enum: */
AZH_E_SAVESTATE = -10                           /* a savestate file, its meta or its SD snapshot failed (step D) */
/* added to the exit enum: */
AZH_EXIT_NEEDS_LAZPY = 7                        /* azhost: a debug-text stop asked of the stock core */
#define AZH_IN_FRAME 0
#define AZH_IN_BUTTONS 1
#define AZH_IN_TOUCH_X 2
#define AZH_IN_TOUCH_Y 3
#define AZH_IN_TOUCH_DOWN 4
#define AZH_IN_CIRCLE_X 5
#define AZH_IN_CIRCLE_Y 6
#define AZH_IN_FIELDS 7                         /* int32 per record */
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
- `azh_layout`: append `uint32_t off_frame_total, off_vblanks_total, off_msg_seq, off_pid, off_exit_code;` then
  `int32_t n_fields; azh_field fields[AZH_MAX_FIELDS];`.

`fields[]` lists every field of `azh_shot_req`, `azh_batch`, `azh_result`, `azh_stats` and the map, named
`<struct>.<field>` (`batch.frames`, `batch.shots`, `shot.frame`, `result.vblanks`, `stats.core_version`,
`map.heartbeat`, `map.pixels` ...) with `offsetof` and the field's `sizeof`, plus one `<struct>.__size__` entry each
(offset 0, size `sizeof`). It is filled by one function in `api.c` from a static table of `{name, offsetof, size}`
rows, one row per line (no macros that paste tokens; plain `offsetof(azh_batch, frames)` per row). Step D's Python
checks every ctypes field against it at import.

### 3.3 The map (bytes 1080-4095 were free in Phase A)

| Offset | Type | Field | Written |
|---|---|---|---|
| 1080 | i64 | frame_total: `retro_run` calls made by batches since boot (the absolute frame) | after every `retro_run`, atomic release store |
| 1088 | i64 | vblanks_total: `input_poll_cb` calls since boot | same |
| 1096 | u32 | msg_seq: +1 after each SET_MESSAGE is copied into the message field | in the SET_MESSAGE handler |
| 1100 | i32 | pid of the process that opened the map | at `azh_open` |
| 1104 | i32 | exit_code the host is about to `_exit` with (0 while alive) | just before `_exit` |

The map version at offset 8 becomes 2.

### 3.4 Semantics of `azh_run` and `azh_set_input`

- `n` is the number of records (each `AZH_IN_FIELDS` int32), 0 to `AZH_MAX_INPUTS`; `inputs` may be NULL when n is 0.
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
  asked (A), then the stops in priority order: guest exited (our core only; the stock core never returns from it),
  guest error, guest break, debug text, SD text, wall limit, then `frames`. The first that holds ends the batch with
  that `stop_reason`; `frames_run`, `last_frame` and `vblanks` count the frame that triggered it.
- Return 0 for every stop reason, including guest stops (they are results, not call failures).

### 3.5 The guest-message detector (`host/msg.c`, pure)

`azh__msg_status(text)`: N from a text starting `Fatal Error encountered (` followed by 1-3 digits and `)`;
`AZH_MSG_OTHER` (-1) for anything else. `azh__msg_on_message(st, text, is_lazpy)` returns one action:

| Status | Stock core | Our core |
|---|---|---|
| 16 | `AZH_ACT_EXIT_EXITED`: map stop code `AZH_STOP_GUEST_EXITED`, message, `_exit(AZH_EXIT_GUEST_EXITED)` at once | `AZH_ACT_EXITED`: flag; the batch stops when `retro_run` returns |
| 14 | `AZH_ACT_BREAK`: flag | same |
| any other N, or OTHER | `AZH_ACT_ERROR`: flag, count +1; on the 3rd in one `retro_run`, `AZH_ACT_EXIT_ERROR`: map stop code `AZH_STOP_GUEST_ERROR`, `_exit(AZH_EXIT_GUEST_ERROR)` | `AZH_ACT_ERROR`: flag, no count |

`azh__msg_begin_run(st)` clears the flags and the count before every `retro_run`. The first message of a kind is kept
(`AZH_MSG_MAX`). Messages that arrive while A's boot is in progress go to A's boot-failure path unchanged and never
reach the detector. The `_exit` path (in `env.c`, one function): write stop code, message, length, `msg_seq`,
`frame_total` and `exit_code` into the map, `msync(MS_SYNC)`, one `write(2)` of a fixed line to the log's file
descriptor (no stdio, no mutex: another thread may hold it), `_exit`. `_exit` in our own process replaces longjmp
(C rule 1).

### 3.6 Internal prototypes added to `host/azh_internal.h` at C1 (frozen with the header)

```c
/* input.c (pure) */
typedef struct { uint32_t buttons; int32_t touch_x, touch_y, touch_down, circle_x, circle_y;
                 uint16_t retro_mask; int16_t ptr_x, ptr_y; } azh_held;
int azh__input_validate(const int32_t *rec, int32_t n, int32_t frames, char *err, size_t errcap);
void azh__held_from_record(azh_held *h, const int32_t rec[AZH_IN_FIELDS]);
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
/* crop.c (moved from frame.c, signature as A wrote it) */
/* log.c additions */
void azh__log_set_debug_stop(const char *text_or_null);
int azh__log_debug_hit(void);                           /* atomic; cleared by set_debug_stop */
int azh__log_fd(void);
/* run.c additions, for step D */
int azh__run_one_frame(void);                           /* one retro_run with the message, heartbeat and counter
                                                           handling of a batch frame; no shots, no stops */
void azh__counters_set(int64_t frame_total, int64_t vblanks_total);
void azh__counters_get(int64_t *frame_total, int64_t *vblanks_total);
int azh__sd_root(char *buf, size_t cap);                /* <sysdir>/Azahar/sdmc */
/* state.c and statemeta.c: step D owns them; C1 creates stubs returning AZH_E_UNSUPPORTED */
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
If Phase A's state struct lacks a field this needs (the sysdir, the booted flag), C1 adds it there.

## 4. Behaviour details

- **Input callbacks** (in `run.c`, registered by A's core setup if A already has stubs there; otherwise C sets them
  with `retro_set_input_state` / `retro_set_input_poll`): `input_state_cb` returns `azh__held_query(&held, ...)`:
  JOYPAD port 0 ids 0-13 from the mapped mask, id `RETRO_DEVICE_ID_JOYPAD_MASK` (256) the whole mask, 14 and 15
  always 0; ANALOG port 0 index 0 ids 0/1 as section 2, index 1 always 0; POINTER port 0 index 0 ids X, Y, PRESSED
  (`ptr_x`, `ptr_y`, 1) while touch down, and 0, 0, 0 otherwise; any other port, device or id 0. `input_poll_cb`
  adds 1 to the vblank counter. Both run on the thread that called `retro_run` (the core runs the guest inside it);
  the held state is only written between `retro_run` calls on the same thread, so no lock; one assert checks the
  thread.
- **SD match** (`match.c`): `azh__match_poll_file` stats the file; missing: no match; size below the offset (the
  file shrank or was recreated): restart at 0 with an empty carry; then reads the new bytes in 64 KiB chunks (a loop
  bounded by the size read at the stat) and feeds each as carry + chunk; keeps the last `len - 1` bytes as the next
  carry, so a text split across two reads is found. Text length 1-255.
- **Debug text** (our core only): `log.c`'s core-log callback hands every formatted core line to the observer
  before the level filter (the guest's `svcOutputDebugString` arrives at debug level, SRC svc.cpp:1170-1190); a
  `strstr` hit sets an atomic flag the batch loop reads after each `retro_run`. Lines arrive whole, so no carry.
- **Wall limit**: compared after each frame; the stop happens between frames, never inside one.
- **SD seeding** (`azhost --sd-seed DIR`): before `azh_boot`, `azh__copy_tree(DIR, <sys>/Azahar/sdmc)` (the
  destination must not exist yet, so a reused `--sys` with an SD folder is `UsageError:`; the gate uses fresh
  folders). `sdcopy.c` uses `fts_open` with `FTS_PHYSICAL`, refuses symlinks and anything not a regular file or a
  directory (`AZH_E_ARG`), caps at 100,000 entries, copies file data in 1 MiB chunks with checked reads and writes,
  modes 0644 and 0755. The library itself never seeds (the Python layer does, step D).
- **`azh_shot` and A's code paths** stay as they are; the PNG crop moves to `crop.c` with its signature unchanged.

## 5. Files (the builder creates or edits only these)

| Path | New or edited | Role |
|---|---|---|
| `host/azhost.h` | edit (C1, then frozen) | section 3 |
| `host/azh_internal.h` | edit (C1, then frozen) | section 3.6 |
| `host/input.c` | new | pure: validation, records to held state, the query, the touch pointer, the three model functions |
| `host/match.c` | new | pure: the SD matcher |
| `host/msg.c` | new | pure: status parse and the action table |
| `host/sdcopy.c` | new | copy and clear a tree (POSIX only, no libretro) |
| `host/crop.c` | new | the crop function moved out of `host/frame.c` (edit `frame.c` to call it) |
| `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` | new at C1, **stubs only**, then step D's | `azh__state_note_app` keeps the path in a file static; the other `azh__state_*` and every `azh__meta_*` return `AZH_E_UNSUPPORTED`; `test_statemeta()` registers 0 checks |
| `host/run.c` | edit | the batch loop of 3.4, the input callbacks, counters, `azh__run_one_frame`, `azh__sd_root` |
| `host/env.c` | edit (the SET_MESSAGE case only) | after A's copy into the map: `msg_seq`, then, once booted, the detector and the `_exit` path |
| `host/log.c` | edit | the debug-stop observer, `azh__log_fd` |
| `host/hostmap.c` | edit | the five new map fields, version 2 |
| `host/api.c` | edit | `azh_run` (validation, no more UNSUPPORTED for n > 0), `azh_set_input`, `azh_abi_layout` (new fields and the table); `azh_boot`'s state branch, `azh_save_state`, `azh_load_state` call the `state.c` stubs |
| `host/libazhost.exports` | edit only if a new public symbol appears (none planned) | |
| `host/azhost_main.c` | edit | section 6 |
| `Makefile` | edit | `test-host` target; the new `.c` files in the library; `check` covers them |
| `tests/host/test_main.c`, `test_input.c`, `test_touch.c`, `test_match.c`, `test_msg.c`, `test_crop.c`, `test_png.c`, `test_sdcopy.c`, `tests/host/messages.txt` | new | section 7 |
| `tests/testapp_log.py` | new | the only place that knows B's control and log formats: `write_control(sys_dir, **keys)`, `parse_log(path) -> (frames, events)` (frames: list of dicts with int fields `f v k tx ty td cx cy`), `read_png_rgba(path) -> (w, h, bytes)` for A's filter-0 RGBA PNGs (zlib, struct; about 25 lines) |
| `tests/checks_c.py` | new | pure check functions over parsed logs and summaries (D reuses them): `first_change_lines`, `offsets_constant`, `touch_expected(x, y)` (the float32 model in Python with `struct` round trips), `circle_expected(c)`, `vblank_constant`, `parse_summary(line)` |
| `tests/gate_c.py` | new | section 8; stdlib; inserts its own folder on `sys.path` (it runs with `-I`); under about 300 lines |
| item `docs/status/lazpy/1-in-progress/210-step-c-*.md` | "Lessons and notes" only | |

Every C function under about 60 lines with about 2 asserts; no goto, recursion or setjmp; every loop bounded; every
return value used; function pointers only for the libretro callbacks (A's documented exception). Python files: type
hints, docstrings, no third-party imports, `python3 -I` clean.

## 6. `azhost run` additions (A's flags and summary unchanged)

```
--inputs FILE        records, one per line: 7 integers separated by spaces or commas (strtol base 0, so 0x10 works),
                     '#' to end of line is a comment; validated by azh_run
--sd-seed DIR        copied into <sys>/Azahar/sdmc before boot
--stop-file REL --stop-text TEXT [--stop-every K] [--stop-new]     the SD rule (--stop-new sets sd_from_end)
--debug-stop TEXT    our core only; the stock core gives "NeedsLazpyCore: ..." and exit 7
--wall-limit-ms MS
--frames N[,N2,...]  several batches in one process, run in order; inputs, shots and stop rules apply to the first
                     batch only; the held input carries over
--print-last-line REL   after each batch, print "last <batch>: <last complete line of that SD file>"
--save FILE          after the last batch, azh_save_state(FILE) and print "saved k=<k> frame=<frame_total>";
                     until step D fills state.c it prints "Unsupported: ..." and exits 6
```
Per batch, one stdout line: A's fields first, then `stop=<frames|sd_text|debug_text|guest_break|guest_exited|
guest_error|wall_limit> first=<a> last=<b> vblanks=<v> batch=<j> msg="<message, \" and newlines escaped>"`. Exit
code: 0, or `AZH_EXIT_GUEST_EXITED` (10) / `AZH_EXIT_GUEST_ERROR` (11) when a batch stopped that way on our core (on
the stock core the process `_exit`s with those codes from inside the run, with no summary line). New subcommand
`azhost layout`: prints `abi=2`, then one line per `fields[]` entry, `<name> <offset> <size>`.

## 7. Unit tests (`make test-host`, no core, no Vulkan)

`build/test-host` links `input.c match.c msg.c crop.c png.c sdcopy.c statemeta.c` and `tests/host/*.c` with the
library's CFLAGS plus `-ffp-contract=off`; `test_main.c` runs each file's entry function, counts checks, prints
`test-host: <N> checks, <F> failed` and exits non-zero on any failure. A check is one `CHECK(cond, fmt, ...)` call
that prints the failing case (a function, not a macro, if the golden rules require: `check(int ok, const char *what)`
plus a formatted message helper).
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
- `test_crop.c`: a synthetic 400 x 480 frame with a pattern; top and bottom crops at factor 1 and 2.
- `test_png.c`: write a 3 x 2 RGBA image; read it back with zlib `uncompress`; check signature, IHDR, every CRC,
  filter bytes 0, pixels.
- `test_sdcopy.c`: nested copy matches byte for byte; a symlink is refused and nothing is half-copied silently (the
  error is returned); clear_tree empties and keeps the folder; an existing destination is refused.
- `test_statemeta.c`: step D fills it.

## 8. The gate scenarios (`tests/gate_c.py`)

Each scenario: a fresh `runs/c-gate/<id>/` with `sys/`, `out/` and a seed folder `seed/testapp/control.txt` (written
by `testapp_log.write_control`, passed with `--sd-seed`), then one
`nice -n 10 build/azhost run build/testapp.3dsx --sys ... --out ... --sd-seed ... <flags>` with a timeout of 600 s
(it kills only its own child on timeout and prints `FAIL <id> timeout`). Frames below are host batch frames; "offset"
is `v` of the first log line that shows a change minus the planned frame of that change.
- **(a) buttons and circle pad** (`--frames 900 --inputs a.txt --shot 600`): from frame 300, each of the 14 bits alone
  for 6 frames with 6 released frames between, then `A|B`, `L|R|ZL|ZR`, `START|SELECT|DUP` 6 frames each, then circle
  (32767, 0), (0, 32767), (-32767, -32767), (16384, -16384), (0, 0) for 10 frames each.
  a1: every planned change is found in the log (`k & 0xCFFF`) and held for exactly its planned frames;
  a2: the offset is the same for every change of kind `hid` (all bits but ZL, ZR) and the same for every change of
  kind `irrst` (ZL, ZR); both printed;
  a3: every circle step reaches its steady value (section 2) with at most one in-between line; its offset printed and
  constant;
  a4: the summary has `stop=frames`, `vblanks=900`; the markers check passes on the frame-600 shot.
- **(b) touch** (`--frames 800 --inputs b.txt --shot 700,780`): 20 points held 6 frames each with 6 released frames
  between, from frame 300: (0,0) (319,0) (0,239) (319,239) (160,120) (10,63) (20,125) (30,126) (40,127) (1,1)
  (318,238) (100,62) (200,64) (50,200) (250,30) (10,128) (300,124) (159,159) (160,63) (80,126); then (160,120) held
  from frame 690 to 720.
  b1: each point appears as `tx ty td=1` equal to `touch_expected(x, y)` and each release as `td=0`; b2: one constant
  offset for all 40 changes (printed; expected one frame later than `hid`, PLAN risk 1); b3: in the bottom shots of
  frames 700 (touch held) and 780 (released), the 17 x 17 box centred on (160, 120) is identical and every pixel in
  it is `#202020`.
- **(c) stop rules**: `ready_at=200`. c1: `--frames 3000 --stop-file testapp/log.txt --stop-text "ready f=" --stop-every
  30`: `stop=sd_text`, and the delay (the last per-frame line's `v` minus the `ready` line's `v`) is 0 to 31; c2: the
  same with `--stop-every 1`: delay 0 to 2; c3: `--frames 10000000 --wall-limit-ms 3000`: `stop=wall_limit`, `wall`
  at most 4.0 s; c4: `--frames 600 --debug-stop ready`: exit 7, stderr starts `NeedsLazpyCore:`. Delays printed.
- **(d) vblanks** (`--frames 300,600,1200 --print-last-line testapp/log.txt`): d1: each batch's `vblanks` equals its
  frames; d2: across the whole log every per-frame line's `v` and `f` are the previous plus 1; d3: with c = (batch 1
  `last`) minus (batch 1 last line's `v`), every batch's `last - v` is c or c + 1 (the stock core's asynchronous SD
  writes can leave the last line one frame behind; PLAN 2.4); the values printed.
- **(e) break** (`break_at=120`, `--frames 600,120`): e1: batch 1 `stop=guest_break`, `msg` contains `(14)`, and
  `last` is at most the break line's `v` + c + 2; e2: batch 2 `stop=frames`, `vblanks=120`; e3: the log has per-frame
  lines after the `break` line (the guest runs on, PLAN C(e)). If Phase B's final app halts after the break by design,
  e3 is dropped by the reviewers, not by the builder (phase-2.md, assumption B5).
- **(f) exit** (`exit_at=120`, `--frames 600`): f1: exit code 10; f2: `host.map` stop code 4 (`AZH_STOP_GUEST_EXITED`),
  `exit_code` 10, message contains `(16)`, read with `struct` at the offsets `azhost layout` prints; f3: the log's last
  line is `exit f=120 ...`.
The offsets, delays and c values go into the report and the item's notes; USING.md (step D) quotes them.

## 9. Steps, with a checkpoint after each (save files as you go; never commit)

0. **Seed the worktree** (it has no `dl/`, `vendor/` or `build/`, all ignored): `mkdir -p dl && cp -R <main
   checkout>/dl/azahar <main checkout>/dl/moltenvk dl/`, `cp -R <main checkout>/vendor .`; `make`; then
   `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp` (or copy the main checkout's
   `build/testapp.3dsx` if it exists). Checkpoint: A's `tests/gate-a.sh build/testapp.3dsx` check 3 passes by hand
   (one 600-frame run).
1. **C1, the freeze (about 0.5 h).** The header and internal header of section 3; `input.c`, `match.c`, `msg.c`,
   `sdcopy.c`, `crop.c` (and `frame.c` calling it); the stubs `state.c`, `statemeta.c`, `test_statemeta.c`; the
   `api.c` routing to the stubs (and the `azh__state_note_app` call in `azh_boot`); in `run.c` the four functions
   step D links against: `azh__counters_set`, `azh__counters_get` and `azh__sd_root` real, `azh__run_one_frame`
   real or a stub returning `AZH_E_UNSUPPORTED` until C2 (so D's code links from the C1 commit);
   `azh_abi_layout`'s table; the map fields in `hostmap.c`; `make test-host` with every section 7 test. Checkpoint: `make check && make && make test-host` clean; `build/azhost layout` prints the table;
   A's gate check 3 still passes. **Then report to the main loop and wait** with the message "C1 done" and the exact
   list of C1 paths; the main loop commits them on `step-c` and starts step D from that commit. Continue with C2 only
   when the main loop replies (it does so at once after the commit).
2. **C2, the run loop (about 0.45 h).** `run.c` (callbacks, held state, the batch loop, counters), `env.c` (detector,
   `_exit` path), `log.c` (observer). Checkpoint: one by-hand run with `--inputs` pressing A from frame 300 shows
   `k=00000001` lines in the log.
3. **C3, flags, seeding and the gate (about 0.55 h).** `azhost_main.c` flags; `testapp_log.py`, `checks_c.py`,
   `gate_c.py`; launch the gate in the background (`nice -n 10 python3 -I tests/gate_c.py > runs/c-gate.log 2>&1`)
   and be woken when it exits (never `sleep`-poll); copy the real `(14)` and `(16)` messages from the scenario
   `host.log` files into `messages.txt` and rerun `make test-host`; the planted red. Checkpoint: the whole gate passes;
   quote it.
4. The report (section 12).

## 10. Machine-sharing rules

- One emulator instance at a time (the gate runs its scenarios one after another; never two `azhost` at once), always
  `nice -n 10`, all folders under `runs/c-*` (ignored). Step D's builder runs no emulator while C is building.
- Never open a window: no Azahar app, no `open`, no Preview; look at PNGs with the Read tool.
- Never kill a process you did not start; the gate kills only its own child, only on its timeout.
- Expect slow frames under shared load: a 900-frame run can take a few minutes; the 600 s timeout covers it. If the
  load average is above 40, the builder notes it beside the gate output.
- The background gate wakes you on exit; while it runs, do review work, not more emulator runs.

## 11. Files the builder must not touch

Everything outside section 5, in particular: `core/`, `testapp/`, `tests/gate-a.sh`, `tests/gate-b.sh`,
`tests/check_testapp.py` (call its CLI, never edit it), `.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`,
`docs/hours.tsv`, the handoff, other items, `prototype/`, `tools/`, `README.md`, and the main checkout (read and copy
only). After C1: `host/state.c`, `host/statemeta.c`, `tests/host/test_statemeta.c` belong to step D, and the two
headers are frozen. Lines the main loop must add (`.gitignore`, runners) go in the report.

## 12. The builder's report

The gate output and the planted red, as printed; the measured offsets (`hid`, `irrst`, circle, touch), the SD stop
delays, c and its spread, whether the guest logged on after the break; `make test-host`'s count line; the analyzer
result; line counts per new or edited file and the longest function; anything the core did that section 2 did not
predict; the runners block for `docs/map/runners.md`:
```
make test-host                                        # pure-C unit tests
build/azhost run <app> ... --inputs f --stop-file REL --stop-text T --frames N[,N2]
build/azhost layout                                   # the ABI table
python3 -I tests/gate_c.py [--only a,b]               # step C's gate
```

## 13. Hours (agent wall time)

Builder 1.5 h (C1 0.5, C2 0.45, C3 0.55), the opus diff review 0.25 h, the commit 0.1 h: **1.85 h**, against PLAN.md's
2.0 (A already ships `azh_stats`; the pure checks are written once and reused by D).

## 14. Review checklist (the opus as-built review)

1. Header: exactly section 3's changes; A's names and order kept; `AZH_ABI_VERSION 2`; `azh_abi_layout` filled from
   real `offsetof`/`sizeof`, one row per field, no token pasting; the map version 2 and the five offsets.
2. Inputs: the button table exact (ZR is 13, not 14; ids 14 and 15 never pressed); the mask; validation complete with
   the record index in the error; last record on a frame wins; held state survives batches; `azh_set_input` same rules.
3. Touch: the integer pointer formula; (0, 0) impossible; the float32 model matches section 2 step by step;
   `-ffp-contract=off` and the `FLT_EVAL_METHOD` assert; the test covers all 76,800 pixels and the 4 rows.
4. Circle: y sign (API up positive, libretro y = -up); right stick 0; the model values.
5. Stops: the order of 3.4; the detector table of 3.5 for both cores; flags cleared per `retro_run`; boot messages
   untouched; the `_exit` path writes the map, `msync`s, uses `write(2)` without the log mutex; exit codes 10 and 11.
6. SD match: only new bytes; the carry of `len - 1`; shrink restarts; bounded loop; missing file is no match;
   `sd_from_end`; relative paths only, `..` refused.
7. Debug text: observer before the level filter; atomic flag; refused on the stock core with
   `AZH_E_NEEDS_LAZPY_CORE` before any frame.
8. Counters: `vblanks` from `input_poll_cb` only; `frame_total` and `vblanks_total` in the map after each frame;
   `azh__run_one_frame` and `azh__counters_*` exist for D.
9. sdcopy: no symlinks, bounded, checked I/O, destination must not exist; clear keeps the folder.
10. The gate: every scenario of section 8, fresh folders, one instance at a time, nice, its own child only, bounded
    timeouts, the planted red; `testapp_log.py` is the only file parsing B's formats; `checks_c.py` functions pure.
11. C rules: functions under about 60 lines, about 2 asserts, no goto/recursion/setjmp, bounded loops, returns used,
    one state struct, file statics elsewhere; Python rules: type hints, docstrings, stdlib only, `-I` clean.
12. Nothing outside section 5 changed; no build outputs, PNGs, logs or `runs/` in the diff.

## 15. Interfaces assumed from Phase 1

`docs/plans/phase-2.md` section 5 lists them (A1-A17, B1-B9) with their sources; the ones this brief leans on most:
A1 (A's header), A3 (`n` counts records), A4 (frames 1-based, absolute shot numbers, no counted `retro_run` inside
`azh_boot`), A5 (map bytes 1080-4095 free), A6 (one state struct holding the sysdir and the booted flag; C1 adds them
if absent), A7 (A's SET_MESSAGE handler), A8 (the log callback in `log.c`), A9 (the crop in `frame.c`), A11 (the
`azhost run` flags and summary), A13 (the profile), B2-B5, B8, B9 (control keys, log lines, loop order, break
behaviour, markers, ready). If Phase A's merged code differs, follow the code for names and report the difference;
if it differs in behaviour this brief relies on, stop and report.
