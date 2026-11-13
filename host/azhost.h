/* azhost.h: the public API of libazhost (docs/PLAN.md 2.2, docs/plans/phase-a.md section 3).
 * Every function returns 0 or a negative AZH_E_*; azh_error() gives the last error text. No libretro or Vulkan
 * types here, and fixed-size arrays only in the structs, so ctypes needs no allocation. */
#ifndef AZHOST_H
#define AZHOST_H

#include <stdint.h>

#define AZH_ABI_VERSION 4                       /* 4: azh_threads (core lazpy.2) */
#define AZH_STATE_META_ABI 3                    /* the abi= of a state's meta file: states did not change in 4 */

enum { AZH_OK = 0, AZH_E_ARG = -1, AZH_E_ORDER = -2 /* call order */, AZH_E_CORE = -3, AZH_E_BOOT = -4,
       AZH_E_VULKAN = -5, AZH_E_IO = -6, AZH_E_NOMEM = -7, AZH_E_UNSUPPORTED = -8, AZH_E_NEEDS_LAZPY_CORE = -9,
       AZH_E_SAVESTATE = -10 /* reserved for step D */,
       AZH_E_UNMAPPED = -11 /* step G: a guest page in the range is unmapped */ };
enum { AZH_EXIT_OK = 0, AZH_EXIT_USAGE = 2, AZH_EXIT_BOOT = 3, AZH_EXIT_CORE = 4, AZH_EXIT_VULKAN = 5,
       AZH_EXIT_IO = 6, AZH_EXIT_NEEDS_LAZPY = 7 /* azhost: a debug-text stop asked of the stock core */,
       AZH_EXIT_UNSUPPORTED = 8 /* azhost: an entry point still returns AZH_E_UNSUPPORTED */,
       AZH_EXIT_GUEST_EXITED = 10, AZH_EXIT_GUEST_ERROR = 11 };     /* azhost and worker exits */
enum { AZH_SCREEN_TOP = 1, AZH_SCREEN_BOTTOM = 2, AZH_SCREEN_BOTH = 3 };
enum { AZH_FMT_PNG = 0, AZH_FMT_RAW = 1 };    /* RAW = RGBA8 into the map's pixel area (factor 1 only) */
enum { AZH_STOP_FRAMES = 0, AZH_STOP_SD_TEXT = 1, AZH_STOP_DEBUG_TEXT = 2, AZH_STOP_GUEST_BREAK = 3,
       AZH_STOP_GUEST_EXITED = 4, AZH_STOP_GUEST_ERROR = 5, AZH_STOP_WALL_LIMIT = 6 };   

#define AZH_MAX_SHOTS 64
#define AZH_PATH_MAX 1024
#define AZH_INPUT_INTS 7                       /* one input record = 7 int32 (PLAN 2.3) */
#define AZH_IN_FRAME 0                         /* field indices inside one AZH_INPUT_INTS record */
#define AZH_IN_BUTTONS 1
#define AZH_IN_TOUCH_X 2
#define AZH_IN_TOUCH_Y 3
#define AZH_IN_TOUCH_DOWN 4
#define AZH_IN_CIRCLE_X 5
#define AZH_IN_CIRCLE_Y 6
#define AZH_MAX_INPUTS 1000000                 /* records per batch */
#define AZH_BUTTONS_MASK 0x0000CFFFu           /* libctru KEY_* bits the host accepts */
#define AZH_CIRCLE_MAX 32767
#define AZH_SD_EVERY_DEFAULT 30
#define AZH_MSG_MAX 256
#define AZH_MAX_FIELDS 160
#define AZH_MEM_MAX_LEN 0x4000000u             /* the core's cap on one guest read or write (patch 0001) */
#define AZH_MAX_WATCH 32                       /* watch entries per batch (ABI 3, step G) */
#define AZH_WATCH_MAX_WORDS 256                /* u32 words per entry */
#define AZH_WATCH_EVERY_MAX 100000
#define AZH_WATCH_AREA_OFF 696320              /* page-aligned, right after the map's pixels */
#define AZH_WATCH_AREA_BYTES 4194304           /* header + rows (fixed 4 MiB) */
#define AZH_WATCH_HDR_BYTES 64
#define AZH_WATCH_ROW_HDR 16
typedef struct { uint32_t addr, words; } azh_watch;      /* guest virtual address, u32 words to read there */
typedef struct { char name[32]; int32_t offset, size; } azh_field;
#define AZH_THREAD_CURRENT 1u                  /* azh_thread.flags: the current thread of its core (live CPU) */
#define AZH_THREAD_NO_PID 0xFFFFFFFFu          /* azh_thread.pid of a thread with no owner process */
/* one guest thread (ABI 4, core patch 0009's lazpy_thread, the same 40 bytes): status is Azahar's ThreadStatus */
typedef struct { uint32_t tid, pid, status, core, priority, flags, pc, lr, sp, cpsr; } azh_thread;

typedef struct { int32_t frame, screens, format; } azh_shot_req;      /* frame: 1-based within the batch */

typedef struct {
    int32_t frames;                        /* retro_run calls in this batch, 1 to 100,000,000 */
    int32_t n_shots; azh_shot_req shots[AZH_MAX_SHOTS];
    char shot_dir[AZH_PATH_MAX];           /* PNGs: <shot_dir>/shot_<absolute frame, %06lld>_<top|bottom>.png */
    char sd_file[AZH_PATH_MAX]; char sd_text[256]; int32_t sd_every;  /* step C; must be empty / 0 in A */
    char debug_text[256];                  /* step C, our core; empty in A */
    int32_t wall_limit_ms;                 /* step C; 0 in A */
    int32_t sd_from_end;                   /* 1: the SD matcher starts at the file's size when the batch starts */
    int32_t n_watch;                       /* ABI 3: watch entries (0: no rows); our core only */
    int32_t watch_every;                   /* one row every this many batch frames (0 means 1) */
    azh_watch watch[AZH_MAX_WATCH];
} azh_batch;

typedef struct { int64_t frames_run, first_frame, last_frame; int32_t stop_reason, shots_done; double wall_s;
                 int64_t vblanks;                  /* guest VBlanks in this batch (input_poll_cb calls) */
                 char message[AZH_MSG_MAX];        /* the message that caused a guest stop; empty otherwise */
                 int32_t watch_rows;               /* ABI 3: watch rows written in this batch */
                 int32_t watch_status;             /* 0, or the first non-zero row status */
               } azh_result;

/* the function azh_stats and a type azh_stats cannot share one C name, so the struct is "struct azh_stats" (plus the
 * typedef azh_stats_t); its layout is the plan's */
struct azh_stats { int64_t frames; double wall_s, user_s, sys_s; int64_t peak_rss; char core_name[64], core_version[128];
                   int32_t is_lazpy_core; };
typedef struct azh_stats azh_stats_t;

typedef struct { uint32_t abi, size_batch, size_result, size_stats, size_layout, map_size, map_px_off, map_px_size;
                 uint32_t off_heartbeat, off_stop, off_msg, off_px_frame;
                 int32_t n_fields; azh_field fields[AZH_MAX_FIELDS]; } azh_layout;

int azh_open(const char *core, const char *sysdir, const char *log, const char *mapfile);
int azh_close(void);
int azh_set_option(const char *key, const char *value);   /* after open, before boot; a later call for a key wins */
int azh_boot(const char *app, const char *state_or_null); /* state: step D */
int azh_run(const int32_t *inputs, int32_t n, const azh_batch *b, azh_result *out);
        /* n = number of input records (AZH_INPUT_INTS int32 each), not of ints; see docs/plans/phase-c.md 3.4 */
int azh_shot(int32_t screens, int32_t format, const char *path_prefix);  /* PNG: <prefix>_top.png / _bottom.png */
int azh_save_state(const char *path, int32_t *k_out);    /* k_out: VBlanks the save's drain ran */
int azh_load_state(const char *path);
int azh_read(uint32_t addr, uint32_t len, void *buf);    /* AZH_E_NEEDS_LAZPY_CORE on the stock core (G) */
int azh_write(uint32_t addr, uint32_t len, const void *buf);
int azh_threads(azh_thread *out, int32_t max, int32_t *count);
        /* every guest thread; *count is the total even above max (retry larger); lazpy.2 core only (ABI 4) */
int azh_set_input(const int32_t rec[AZH_INPUT_INTS]);    /* sets the held state now (frame field ignored) */
int azh_stats(struct azh_stats *out);
int azh_abi_layout(azh_layout *out);
const char *azh_error(void);

#endif
