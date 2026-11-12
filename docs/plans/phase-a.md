# Phase 1, step A: the host library (item laz-120)

Opus step plan, 2026-11-12, **draft for Phase 1's two opus review loops. Nobody builds from it until the reviews
pass and the main loop launches the step.** Index: `docs/plans/phase-1.md`. For one sonnet builder in its own git
worktree. It refines `docs/PLAN.md` sections 2.1, 2.2, 2.4, 2.6 and the "Phase A" paragraph of section 3; where they
disagree on a goal, PLAN.md wins and the builder stops and reports.

Builder reads first: `docs/map/rules.md`, PLAN.md 2.1-2.6, `prototype/fe2.c` and `prototype/fe3.c` (what works;
not how to write it), `docs/research/spike-1-headless-core.md`, `docs/research/libretro-py-probe.md` (its
environment-call checklist), `~/.claude/c-golden-rules.md`, `~/.claude/shell-golden-rules.md`.

## 1. Goal and gate

Goal: the C host, split from fe2.c/fe3.c into small files: `build/libazhost.dylib` (the `azh_*` API of PLAN 2.2) and
the thin `build/azhost` program over it. It loads a core, answers its Vulkan setup through MoltenVK with no window,
boots an app, runs a batch of frames and writes both screens as PNGs, with the option profile, the core-version
check and boot-failure detection. GL is gone. Inputs, stop rules, savestates and memory are later steps (C, D, G):
their entry points exist now and return `AZH_E_UNSUPPORTED` (or `AZH_E_NEEDS_LAZPY_CORE`).

Gate (PLAN.md section 3, "Phase A"), made concrete. All of it is `tests/gate-a.sh <app.3dsx>`, which prints one
`PASS`/`FAIL` line per check and exits non-zero on any FAIL:
1. **Fresh copy.** Agents never commit, so "a fresh clone" is emulated: every tracked and new non-ignored file of
   the worktree (`git ls-files -z --cached --others --exclude-standard`) is copied by tar into a new folder under the
   scratchpad, plus `dl/` and `vendor/` by `cp -R`. In that copy `tools/fetch.sh` prints, before its blank line and
   "Done." block, only lines starting `have   `. (The main loop reruns this as a real `git clone` after the commit.)
2. **Zero warnings.** In the copy: `make check && make`, output to a log; `grep -ci warning <log>` is 0; both exit 0.
3. **Two screens.** `nice -n 10 build/azhost run <app> --sys <run>/sys --out <run>/out --frames 600 --shot 300,600`
   exits 0 and writes `shot_000300_top.png`, `shot_000300_bottom.png`, `shot_000600_top.png`,
   `shot_000600_bottom.png`; each top PNG's IHDR reads 400 x 240 and each bottom 320 x 240 (read by a 5-line
   `python3 -I` IHDR check, not `file`). `host.log` has the core version line and the effective option lines.
4. **No window.** While that run is alive (started in the background, checked once its `host.map` heartbeat is
   above 0, a bounded wait of at most 120 s inside the script), `lsappinfo list | grep -E "pid = <pid>( |$)"`
   prints nothing.
5. **Boot failures.** `azhost run /nonexistent/x.3dsx ...` and `azhost run <run>/bad.3dsx ...` (a text file) each
   exit 3 (`AZH_EXIT_BOOT`) and print a line starting `BootError:` on stderr.
6. **Version check.** With `--core <a copy of the stock dylib>` it boots; with `--core` pointing at any other
   dylib (use `build/libazhost.dylib` itself, which has no `retro_*` symbols) it exits 4 (`AZH_EXIT_CORE`) without
   `LAZ_ANY_CORE=1`.

The gate's app: Phase B's test app does not exist yet in this worktree. Use a copy of Gen3D's own homebrew build
`/Users/guyshtainer/VSCodeProjects/3ds-toolkit/projects/Gen3D/Gen3D.3dsx` (5,085,000 bytes on 2026-11-12; read-only;
copy it into `runs/a-gate/` first because another session may rebuild it; its menu shows "CHOOSE TWO GAMES / No games
found" with no SD data, spike 1). Never commit it or its shots (rules.md 1, 8: a test fixture, not a dependency).
After A and B merge, the main loop reruns check 3 with `build/testapp.3dsx`.

## 2. Facts checked for this plan (reviewers: verify these)

"SRC" = the main checkout's pristine tarball tree `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (tag 2126.2,
GIT-COMMIT 219d743a). Read 2026-11-12.

Environment calls the core makes (grep of `RETRO_ENVIRONMENT_` in SRC `src/citra_libretro/*.cpp`). Ids from
`vendor/libretro.h`; `|E` = `| RETRO_ENVIRONMENT_EXPERIMENTAL` (0x10000). Use the names, never fe2's numbers.
| Call (id) | Answer |
|---|---|
| GET_SYSTEM_DIRECTORY (9), GET_SAVE_DIRECTORY (31) | the instance's sysdir (`<run>/sys`); the core puts `Azahar/sdmc`, `Azahar/nand` under it |
| GET_LIBRETRO_PATH (19) | the core's path (fe2 wrongly returned sysdir) |
| GET_LOG_INTERFACE (27) | our log callback (2.3 below) |
| GET_CORE_OPTIONS_VERSION (52) | 0, so the core registers V0 variables, "desc; default\|others" with the default first (SRC core_settings.cpp:722-823) |
| SET_VARIABLES (16) | record every key and its allowed values (31 keys, below); cap 128 |
| GET_VARIABLE (15) | the value set for that key; an unset key returns false (the core uses its default) and boot logs a warning |
| GET_VARIABLE_UPDATE (17) | false |
| SET_CORE_OPTIONS (53), SET_CORE_OPTIONS_V2 (67) | false (only V0 is used) |
| GET_PREFERRED_HW_RENDER (56) | `RETRO_HW_CONTEXT_VULKAN` (fe2 said OpenGL) |
| SET_HW_RENDER (14) | true only for `RETRO_HW_CONTEXT_VULKAN`; keep the callback struct (its `context_reset` is how the host triggers `System::Load`) |
| SET_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE (43\|E) | copy it; true if `interface_type == RETRO_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE_VULKAN` |
| GET_HW_RENDER_INTERFACE (41\|E) | a pointer to our `retro_hw_render_interface_vulkan` once Vulkan is up, else false |
| GET_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE_SUPPORT (73\|E), SET_HW_SHARED_CONTEXT (44\|E) | false (as fe2) |
| SET_PIXEL_FORMAT (10) | true for XRGB8888 only (the core asks for it, citra_libretro.cpp:555) |
| SET_MESSAGE (6) | log it at warn; copy into the map's last-message field; during `context_reset` it marks a boot failure (2.6). The "(N)" parsing is step C's. |
| SET_MEMORY_MAPS (36\|E) | true; log the descriptor count once (sent once, SRC environment.cpp:119) |
| GET_MICROPHONE_INTERFACE (75\|E) | false (no permission prompt can appear, PLAN 2.4) |
| SET_GEOMETRY (37), SET_SYSTEM_AV_INFO (32) | true; re-read the av info |
| SET_INPUT_DESCRIPTORS (11), SET_CONTROLLER_INFO (35), SET_SERIALIZATION_QUIRKS (44), SET_PERFORMANCE_LEVEL (8), SET_SUPPORT_NO_GAME (18) | true, ignored |
| GET_CAN_DUPE (3) | true |
| GET_SENSOR_INTERFACE, GET_VFS_INTERFACE, GET_JIT_CAPABLE, GET_CURRENT_SOFTWARE_FRAMEBUFFER, SET_AUDIO_CALLBACK, SET_FRAME_TIME_CALLBACK, SHUTDOWN | false |
| anything else | false; logged once per id at debug |

Vulkan (SRC):
- citra_libretro.cpp:607-615: the negotiation struct is `{type VULKAN, RETRO_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE_
  VULKAN_VERSION, GetVulkanApplicationInfo, CreateVulkanDevice, nullptr}`, so `create_instance` and `create_device2`
  are NULL (`vendor/libretro_vulkan.h:30` version 2). The host creates the `VkInstance` itself (MoltenVK, no surface,
  no portability flag needed with a direct dylib load, spike 1) with the core's `get_application_info()`, then calls
  `create_device(&ctx, instance, gpu, VK_NULL_HANDLE, vkGetInstanceProcAddr, NULL, 0, NULL, 0, NULL)`. Keep the
  create_device2 / create_instance branches only if `interface_version >= 2` and the pointers are non-NULL.
- `src/citra_libretro/libretro_vk.cpp:703-708`: `Present` sets `image_layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_
  OPTIMAL`, passes the view's create info (its `.image` is the `VkImage`) and the graphics queue family to
  `set_image`, then `SwapBuffers` uploads `RETRO_HW_FRAME_BUFFER_VALID` (emu_window/libretro_window.cpp:88-91).
  `libretro_vk.h:158` the output format is `eR8G8B8A8Unorm`: no channel swap (fe2's BGRA swap stays only as a
  checked fallback for B8G8R8A8; any other format is an error).
- The interface we hand back is `struct retro_hw_render_interface_vulkan` (`vendor/libretro_vulkan.h`, version 5 at
  :29): fill it with designated initializers, not fe2's positional list.

Frames, failures, layout (SRC citra_libretro.cpp):
- :218-223 a not-loaded game makes `retro_run` upload `(NULL, 0, 0, 0)`; :503-557 `retro_load_game` returns false
  for a missing path ("Failed to obtain loader for the specified ROM.") or a bad format ("The ROM format is not
  supported."); :371-405 `do_load_game` (inside `context_reset`) reports `System::Load` failures by SET_MESSAGE.
  PLAN 2.6: any of the three is a `BootError`.
- Default layout at resolution factor 1: one 400x480 frame, top at (0,0) 400x240, bottom at (40,240) 320x240 (spike 1,
  PLAN 2.2). At factor f the frame is 400f x 480f and the rectangles scale by f; any other frame size is an error.
- The stock core's `library_version` is `Common::g_build_fullname` (environment.cpp:270); `strings` on the stock
  dylib shows "2126.2". Assumption A1: the stock string is exactly `2126.2`; the builder confirms with `azhost info`
  and pins what it prints.

The 31 core option keys at 2126.2 (SRC core_settings.cpp:144-717) and the profile value for each. This is
`host/options-default.txt`, one `key=value` per line, `#` comments allowed:
```
citra_use_cpu_jit=enabled
citra_cpu_clock_percentage=100
citra_is_new_3ds=New 3DS
citra_region_value=Auto
citra_language_value=English
citra_audio_emulation=hle
citra_input_type=none
citra_graphics_api=Vulkan
citra_use_hw_shader=enabled
citra_use_shader_jit=enabled
citra_shaders_accurate_mul=enabled
citra_use_disk_shader_cache=enabled
citra_resolution_factor=1
citra_texture_filter=none
citra_texture_sampling=GameControlled
citra_custom_textures=disabled
citra_dump_textures=disabled
citra_layout_option=default
citra_swap_screen=Top
citra_swap_screen_mode=Toggle
citra_large_screen_proportion=4.00
citra_render_3d=off
citra_factor_3d=0
citra_use_virtual_sd=enabled
citra_use_libretro_save_path=LibRetro Default
citra_analog_function=c_stick
citra_analog_deadzone=15
citra_enable_mouse_touchscreen=enabled
citra_enable_touch_touchscreen=enabled
citra_enable_touch_pointer_timeout=enabled
citra_enable_motion=disabled
citra_motion_sensitivity=1.0
```
Choices that differ from the core default, with reasons: `graphics_api` Vulkan (default "auto"); `input_type` none
(no microphone, PLAN 2.4); `analog_function` c_stick (right stick is C-stick only, so no cursor, PLAN 2.3);
`enable_motion` disabled (PLAN 2.4). Two core defaults are not in their own value lists (`graphics_api` "auto" vs
"Auto", `language_value` "english" vs "English"), one more reason to set every key. At boot the host checks every set
key exists in the SET_VARIABLES list and its value is listed (`citra_init_time` excepted: any decimal), else
`AZH_E_ARG` naming the key. Our core's extra keys come from step F1's `core/options-lazpy.txt` in F2; unknown keys in
the profile are an error only when the core did not register them.

## 3. The API (the header `host/azhost.h`; C may extend it, D freezes it)

Every function returns 0 or a negative `AZH_E_*`; `azh_error()` returns the last error text (a static buffer, one
instance per process). Fixed-size arrays in every struct (no pointers inside), so ctypes in D needs no allocation.
```c
#define AZH_ABI_VERSION 1
enum { AZH_OK = 0, AZH_E_ARG = -1, AZH_E_STATE = -2, AZH_E_CORE = -3, AZH_E_BOOT = -4, AZH_E_VULKAN = -5,
       AZH_E_IO = -6, AZH_E_NOMEM = -7, AZH_E_UNSUPPORTED = -8, AZH_E_NEEDS_LAZPY_CORE = -9 };
enum { AZH_EXIT_OK = 0, AZH_EXIT_USAGE = 2, AZH_EXIT_BOOT = 3, AZH_EXIT_CORE = 4, AZH_EXIT_VULKAN = 5,
       AZH_EXIT_IO = 6, AZH_EXIT_GUEST_EXITED = 10, AZH_EXIT_GUEST_ERROR = 11 };     /* azhost and worker exits */
enum { AZH_SCREEN_TOP = 1, AZH_SCREEN_BOTTOM = 2, AZH_SCREEN_BOTH = 3 };
enum { AZH_FMT_PNG = 0, AZH_FMT_RAW = 1 };                 /* RAW = RGBA8 into the map's pixel area */
enum { AZH_STOP_FRAMES = 0, AZH_STOP_SD_TEXT = 1, AZH_STOP_DEBUG_TEXT = 2, AZH_STOP_GUEST_BREAK = 3,
       AZH_STOP_GUEST_EXITED = 4, AZH_STOP_GUEST_ERROR = 5, AZH_STOP_WALL_LIMIT = 6 };   /* C fills 1-6 */
#define AZH_MAX_SHOTS 64
#define AZH_PATH_MAX 1024
typedef struct { int32_t frame, screens, format; } azh_shot_req;      /* frame: 1-based within the batch */
typedef struct {
    int32_t frames;                        /* retro_run calls in this batch, 1 to 100,000,000 */
    int32_t n_shots; azh_shot_req shots[AZH_MAX_SHOTS];
    char shot_dir[AZH_PATH_MAX];           /* PNGs: <shot_dir>/shot_<absolute frame, %06lld>_<top|bottom>.png */
    char sd_file[AZH_PATH_MAX]; char sd_text[256]; int32_t sd_every;  /* step C; must be empty / 0 in A */
    char debug_text[256];                  /* step C, our core; empty in A */
    int32_t wall_limit_ms;                 /* step C; 0 in A */
} azh_batch;
typedef struct { int64_t frames_run, first_frame, last_frame; int32_t stop_reason, shots_done; double wall_s; } azh_result;
typedef struct { int64_t frames; double wall_s, user_s, sys_s; int64_t peak_rss; char core_name[64], core_version[128];
                 int32_t is_lazpy_core; } azh_stats;
typedef struct { uint32_t abi, size_batch, size_result, size_stats, size_layout, map_size, map_px_off, map_px_size;
                 uint32_t off_heartbeat, off_stop, off_msg, off_px_frame; } azh_layout;
int azh_open(const char *core, const char *sysdir, const char *log, const char *mapfile);
int azh_close(void);
int azh_set_option(const char *key, const char *value);   /* before azh_boot; a later call for a key wins */
int azh_boot(const char *app, const char *state_or_null); /* state: AZH_E_UNSUPPORTED until step D */
int azh_run(const int32_t *inputs, int32_t n, const azh_batch *b, azh_result *out);  /* n > 0: UNSUPPORTED until C */
int azh_shot(int32_t screens, int32_t format, const char *path_prefix);  /* PNG: <prefix>_top.png / _bottom.png */
int azh_save_state(const char *path, int32_t *k_out);    /* AZH_E_UNSUPPORTED until D */
int azh_load_state(const char *path);                    /* AZH_E_UNSUPPORTED until D */
int azh_read(uint32_t addr, uint32_t len, void *buf);    /* AZH_E_NEEDS_LAZPY_CORE on the stock core (G) */
int azh_write(uint32_t addr, uint32_t len, const void *buf);
int azh_set_input(const int32_t rec[7]);                 /* AZH_E_UNSUPPORTED until C */
int azh_stats(azh_stats *out);
int azh_abi_layout(azh_layout *out);
const char *azh_error(void);
```
Call order is checked (`AZH_E_STATE`): open, then options, then boot, then run/shot/stats in any order, then close.

The mapped file `host.map` (created by `azh_open`, fixed size, little-endian; offsets also reported by
`azh_abi_layout`): 0 magic `"LAZMAP1\0"`; 8 u32 version 1; 12 u32 header size 4096; 16 u64 heartbeat (atomic
store, +1 after every `retro_run`); 24 i32 stop code (0 running); 28 i32 message length; 32 char[1024] last core
message; 1056 u32 x4 top w, top h, bottom w, bottom h; 1072 i64 frame of the pixels; 4096 pixels, top RGBA 400x240
then bottom RGBA 320x240 (691,200 bytes); total 695,296. Raw shots exist only at resolution factor 1
(`AZH_E_UNSUPPORTED` otherwise; PNG works at any factor).

`azhost` (PLAN 2.2: it calls the same functions; no Python CLI):
```
azhost run <app> --sys <dir> --out <dir> --frames N [--shot f1,f2,...] [--opt key=value]...
               [--profile file] [--core path] [--mvk path] [--state file]
azhost info [--core path]          # prints library_name, library_version, valid_extensions, lazpy symbols yes/no
```
Defaults, relative to the current directory (run from the repo root): `--profile host/options-default.txt`,
`--core $LAZ_CORE` else `dl/azahar/azahar_libretro.dylib`, `--mvk $LAZ_MVK` else
`dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib`. The profile is applied with `azh_set_option`
first, then each `--opt` (later wins). `host.log` and `host.map` go into `--out`. Shots are 1-based frame numbers of
the batch; one batch from boot means frame k is the frame the k-th `retro_run` delivered. Stdout: one summary line
`frames=<n> wall=<s> fps=<f> shots=<k>`. Errors: one line on stderr starting with the error class (`BootError:`,
`CoreError:`, `VulkanError:`, `IOError:`, `UsageError:`) and the exit code above. The core version is refused unless
it equals `AZH_STOCK_VERSION` or ends with `AZH_LAZPY_SUFFIX` (both in `host/pins.h`; `"-lazpy.1"`), or
`LAZ_ANY_CORE=1`; step F2 pins our build's exact string.

## 4. Files the builder creates (and owns); every function under about 60 lines, about 2 asserts each

| Path | Role |
|---|---|
| `host/azhost.h` | the public API of section 3 (nothing else; no libretro or Vulkan types in it) |
| `host/azh_internal.h` | the one internal state struct (core table, Vulkan table, options, av info, frame counters), shared prototypes; file-static data everywhere else |
| `host/pins.h` | `AZH_STOCK_VERSION`, `AZH_LAZPY_SUFFIX` |
| `host/core.c` | `dlopen` (RTLD_NOW\|RTLD_LOCAL), the `retro_*` function table filled once by explicit `dlsym` lines (a missing symbol is `AZH_E_CORE` naming it), `retro_get_system_info` and the version check, init, load_game, unload, deinit |
| `host/env.c` | the environment callback: a `switch` that hands each id group to one small function (section 2's table); the SET_MESSAGE capture; the boot-failure flag |
| `host/options.c` | the option store: set (key, value), the core's registered keys and values from SET_VARIABLES, GET_VARIABLE lookup, boot-time validation, logging the effective set |
| `host/vk.c` | MoltenVK `dlopen`, the Vulkan proc table loaded once (named fields assigned by explicit `vkGet*ProcAddr` calls, each checked; no token pasting, C rule 8), instance creation, `create_device`, the render interface callbacks (set_image, queue lock and unlock as a mutex, the rest as fe2), and the readback: one host-visible buffer, one command pool and one command buffer created once from the av info's max geometry and reused; every `VkResult` checked |
| `host/frame.c` | the video callback (HW frame: note it and, on shot frames, read back; software XRGB8888: copy rows with the pitch); the crop to top and bottom, scaled by the factor; alpha 255 |
| `host/png.c` | the PNG writer: filter 0 rows, zlib `compress2` (level 6 for now; step E tunes), CRC table built in an init call, chunks written by small functions (no macros) |
| `host/hostmap.c` | create, `ftruncate`, `mmap` and `munmap` the map; heartbeat, stop code, message, pixels |
| `host/log.c` | `host.log`: a mutex around a formatted write; levels debug/info/warn/error, threshold from `LAZ_LOG_LEVEL` (default info); the core's variadic `retro_log_printf_t` (`vsnprintf` into a local buffer, then one write); the core logs from several threads |
| `host/api.c` | the `azh_*` functions of section 3: state checks, parameter checks, error text |
| `host/run.c` | the batch loop: `retro_run` up to `frames` times (a bounded loop), heartbeat after each, shots at their frames (PNG written after `retro_run` returns, not inside the callback), `azh_result` |
| `host/azhost_main.c` | argument parsing (no `getopt_long` tricks needed; a small table), profile file reading, calls into the API, exit codes |
| `host/libazhost.exports` | the exported symbol list (`_azh_open` ...), passed with `-Wl,-exported_symbols_list` (as Azahar does) |
| `host/options-default.txt` | section 2's profile |
| `Makefile` | see below |
| `tests/gate-a.sh` | the gate of section 1, POSIX `sh`, `set -eu`, ShellCheck clean, under about 100 lines; takes the app path as `$1` |
| item `docs/status/lazpy/1-in-progress/120-step-a-host-library.md` (the main loop moves it there from 2-next/ at launch) | only its "Lessons and notes" section |

`Makefile` (A owns the top-level one): `CC = clang`; `CFLAGS = -std=c11 -O2 -g -Wall -Wextra -Werror -Wshadow
-Wstrict-prototypes -Wmissing-prototypes -I vendor -I vendor/include`; targets `all` (default: `build/libazhost.dylib`
with `-dynamiclib -install_name @rpath/libazhost.dylib -lz -lpthread` and the exports list; `build/azhost` linked to
it with `-Wl,-rpath,@loader_path`), `check` (`clang --analyze -Xclang -analyzer-werror -Xanalyzer
-analyzer-output=text $(CFLAGS)` on every `host/*.c`, so no `.plist` files appear; if `-analyzer-werror` is not
accepted by this clang, fail the target on any analyzer output line instead), `testapp` (delegates:
`$(MAKE) -C testapp`, which step B provides; this target must exist even though B's folder is absent in this
worktree), `clean` (`rm -rf build/libazhost.dylib build/azhost build/obj`). Object files in `build/obj/`. No GL, no
`-framework OpenGL`. Asserts stay on (no `-DNDEBUG`).

C rules in practice: no `goto` (unwind with small helper functions), no recursion, no `setjmp`; every loop bounded (the
frame loop by `frames`, SET_VARIABLES by its cap, the env table by its size); every allocation checked and owned (the
readback buffers belong to `vk.c`, freed in close); every return value used or cast to `(void)` with a reason;
function pointers only for the libretro and Vulkan callbacks and the two proc tables (the documented exception, C
rule 9; one comment says so in `azh_internal.h`); no globals outside the one state struct and file statics.

## 5. Steps, with a checkpoint after each (save files as you go; never commit)

0. **The `dl/` layout first (PLAN's first step).** The main loop has already moved the main checkout's `dl/` into
   fetch.sh's layout (`dl/azahar/azahar_libretro.dylib`, `dl/azahar/stock-core.zip`) and run
   `tools/fetch.sh` there. In this worktree (which has no `dl/` or `vendor/`, both ignored):
   `cp -R <main checkout>/dl/azahar <main checkout>/dl/moltenvk <main checkout>/dl/libretro-headers
   <main checkout>/dl/vulkan-headers dl/` (make `dl/` first; do not copy `dl/azahar-src`, 470 MB, not needed) and
   `cp -R <main checkout>/vendor .`, then `tools/fetch.sh`. If any folder is missing in the main checkout, let
   fetch.sh download it (about 70 MB at most). Do not edit `docs/map/runners.md`: put the corrected run lines in your
   report (section 8). Checkpoint: a second `tools/fetch.sh` prints only `have` lines.
1. `azhost.h`, `azh_internal.h`, `pins.h`, `log.c`, `options.c`, `options-default.txt`, the Makefile. Checkpoint:
   `make` compiles what exists with zero warnings.
2. `core.c`, `env.c`, `api.c` (open, set_option, close, error, abi_layout, stats), `azhost info`. Run
   `LAZ_ANY_CORE=1 build/azhost info` on the stock core: record the exact `library_version` and pin it in
   `pins.h`. Checkpoint: `info` prints it; `info --core build/libazhost.dylib` gives `CoreError:` and exit 4.
3. `vk.c`, `frame.c`, `png.c`, `hostmap.c`, `run.c`, `azh_boot`, `azh_run`, `azh_shot`, `azhost run`. Boot the gate
   app once for 600 frames, nice'd. Look at both PNGs with the Read tool (never `open`): top shows the Gen3D menu,
   bottom its buttons. Checkpoint: check 3 passes by hand.
4. Boot-failure paths: the missing file, the text file, and a SET_MESSAGE during `context_reset`. Checkpoint: check 5.
5. `make check` clean (fix every analyzer finding, do not silence it); `tests/gate-a.sh`; ShellCheck. Plant one red:
   make the IHDR check expect 401 wide once, see FAIL, revert. Checkpoint: the whole gate PASSes; quote its output.
6. The report.

## 6. Machine-sharing rules

- One emulator instance at a time, always `nice -n 10`, its folders under `runs/a-*` (ignored). The gate's
  background run is the only background instance and the script waits for it (bounded).
- Never open a window: no Azahar app, no `open`, no Preview, no AppKit in the host. Look at PNGs with the Read tool.
- Never kill a process you did not start; the gate kills only the pid it started, and only on a timeout.
- Expect slow frames: the machine was at load 86 when this was written; a 600-frame run can take a minute or two.
  Timeouts: 300 s for a 600-frame run (the first boot compiles shaders).

## 7. Files the builder must not touch

Everything outside section 4: `core/`, `tools/build-core.sh`, `tools/untar_checked.py`, `testapp/`,
`tests/gate-b.sh`, `tests/check_testapp.py`, `.gitignore`, `docs/map/*`, `README.md`, `docs/PLAN.md`,
`docs/plans/*`, `docs/hours.tsv`, the handoff, other items, `tools/fetch.sh` (if it needs a change, stop and report),
`prototype/`, and the main checkout (read and copy only).

## 8. The builder's report

The gate output as printed (and the red); the pinned stock version string; a line count per file and the longest
function's length; the analyzer result; anything the core did that this plan did not predict (env ids, a negotiation
branch, the image format); the runners block for the main loop to put in `docs/map/runners.md`:
```
make check && make                      # build/libazhost.dylib and build/azhost
build/azhost run <app.3dsx> --sys runs/x/sys --out runs/x/out --frames 600 --shot 300,600
build/azhost info                       # core name and version
tests/gate-a.sh <app.3dsx>              # step A's gate
```
and the `.gitignore` lines for the main loop: `*.plist`, `*.dSYM/`.

## 9. Hours (agent wall time)

Builder 1.1 h (header and options 0.15, core and env 0.25, Vulkan, frame and PNG 0.35, boot failures 0.1, gate and
analyzer 0.25), plus the opus diff review and the commit, about 0.35 h: **1.45 h**, 0.2 h over PLAN.md's 1.25 (the
split into eleven files with checked returns is more than fe2's 194 lines; the reviewers may cut the `info`
subcommand or the version check's red to win it back).

## 10. Review checklist (the opus diff review)

1. API matches section 3 (names, return codes, struct layouts with fixed arrays); `azh_abi_layout` reports real
   `sizeof`/`offsetof` values; later-step functions return their documented codes.
2. Env callback: every id in section 2's table answered as written; GET_LIBRETRO_PATH gives the core path; the
   microphone refused; nothing GL left; names, not numbers.
3. Vulkan: proc table loaded once, no `IFN`/`DFN` macros; every `VkResult` and core return checked; readback buffer,
   pool and command buffer created once and freed in close; queue mutex held around the copy; designated
   initializers for the render interface; format checked.
4. Boot failure: all three cases give `AZH_E_BOOT` and `BootError:` with the core's message.
5. Options: the profile sets all 31 keys; values validated against SET_VARIABLES; the effective set and the core
   version logged on every boot; the version refused without `LAZ_ANY_CORE=1`.
6. C rules: no goto/recursion/setjmp; loops bounded; functions under about 60 lines; about 2 asserts per function;
   one documented function-pointer exception; returns checked; one state struct.
7. Log callback: thread-safe, level-filtered, no unbounded formatting (`vsnprintf` into a fixed buffer, truncation
   marked).
8. Makefile: `-Wall -Wextra -Werror` and `make check` with the analyzer; the exports list; no `.plist` files left;
   a `testapp` target that delegates.
9. Gate script: ShellCheck clean, bounded waits, kills only its own pid, the planted red shown; the fresh-copy
   emulation copies tracked plus new non-ignored files only.
10. No window: no AppKit, `lsappinfo` check passes; nothing written outside `build/` and `runs/`.
