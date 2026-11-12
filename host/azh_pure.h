/* azh_pure.h: prototypes of the pure modules (version.c, crop.c, png.c, input.c, match.c, msg.c, rawcopy.c,
 * statemeta.c). They include only this header, azhost.h and <stdint.h>/<string.h>/zlib, never libretro or Vulkan,
 * so the unit tests can link them alone. */
#ifndef AZH_PURE_H
#define AZH_PURE_H

#include <stddef.h>
#include <stdint.h>

#include "azhost.h"

/* version.c: 1 when v is the pinned stock version, the stock version plus AZH_LAZPY_SUFFIX exactly, or any_core. */
int azh_version_ok(const char *v, int any_core);

/* crop.c: where the two screens sit in a core frame (default layout at resolution factor f: the frame is
 * 400f x 480f, top at (0,0) 400f x 240f, bottom at (40f,240f) 320f x 240f). Returns 0, or -1 for any other size. */
typedef struct { uint32_t x, y, w, h; } azh_rect;
int azh_crop_rects(uint32_t fw, uint32_t fh, azh_rect *top, azh_rect *bottom);

/* png.c: 8-bit RGBA PNG, filter 0, zlib level from azh_png_level() (default 1). azh_png_init() builds the CRC table once and must come first.
 * px points at the first pixel, stride is the byte distance between rows. Returns 0, -1 (bad argument), -2 (I/O). */
void azh_png_init(void);
int azh_png_write(const char *path, const uint8_t *px, uint32_t w, uint32_t h, size_t stride);
/* The zlib level: LAZ_PNG_LEVEL (0-9) read once on the first call; default 1; a bad text gives 1. */
int azh_png_level(void);
/* NULL when LAZ_PNG_LEVEL was fine or unset, else the bad text (cut at 31 bytes) for the caller's log line. */
const char *azh_png_level_bad(void);

/* input.c */
typedef struct { uint32_t buttons; int32_t touch_x, touch_y, touch_down, circle_x, circle_y;
                 uint16_t retro_mask; int16_t ptr_x, ptr_y; } azh_held;
int azh__input_validate(const int32_t *rec, int32_t n, int32_t frames, char *err, size_t errcap);
void azh__held_from_record(azh_held *h, const int32_t rec[AZH_INPUT_INTS]);
int16_t azh__held_query(const azh_held *h, unsigned port, unsigned device, unsigned index, unsigned id);
void azh__touch_pointer(int32_t x, int32_t y, int16_t *px, int16_t *py);
void azh__model_frame_pixel(int16_t px, int16_t py, int32_t *fx, int32_t *fy);
void azh__model_guest_touch(int32_t fx, int32_t fy, uint16_t *gx, uint16_t *gy);
int16_t azh__model_guest_circle(int32_t c);
/* match.c */
typedef struct { char text[256]; size_t len; char carry[255]; size_t carry_len; int64_t offset; } azh_matcher;
int azh__match_init(azh_matcher *m, const char *text, int64_t start_offset);
int azh__match_feed(azh_matcher *m, const char *buf, size_t n);      /* 1 found, 0 not */
void azh__match_restart(azh_matcher *m);
int azh__match_poll_file(azh_matcher *m, const char *path);          /* 1 found, 0 not, <0 AZH_E_IO */
/* msg.c */
enum { AZH_MSG_OTHER = -1 };
enum { AZH_ACT_NONE = 0, AZH_ACT_BREAK, AZH_ACT_ERROR, AZH_ACT_EXITED, AZH_ACT_EXIT_EXITED, AZH_ACT_EXIT_ERROR };
typedef struct { int32_t brk, err, exited, err_count; char first[AZH_MSG_MAX]; } azh_msgstate;
int azh__msg_status(const char *text);
int azh__msg_is_break(const char *text);
void azh__msg_begin_run(azh_msgstate *st);
int azh__msg_on_message(azh_msgstate *st, const char *text, int is_lazpy);
/* rawcopy.c: one screen's rectangle (as azh_crop_rects returns it) from the RGBA readback into the map */
void azh__raw_copy(const uint8_t *src, int32_t src_stride, int32_t x, int32_t y, int32_t w, int32_t h,
                   uint8_t *dst);                                     /* dst rows are w * 4 bytes; alpha 255 */
/* statemeta.c: step D owns it; C1 creates the stub */
typedef struct { int32_t abi, k; int64_t frame_total, vblanks_total, created; char core_version[128];
                 char app[AZH_PATH_MAX]; char app_sha256[65]; } azh_state_meta;
int azh__meta_format(const azh_state_meta *m, char *buf, size_t cap);    /* bytes written, or AZH_E_ARG */
int azh__meta_parse(const char *text, size_t len, azh_state_meta *m);    /* 0 or AZH_E_SAVESTATE */
int azh__meta_write(const char *path, const azh_state_meta *m);          /* <path>.tmp then rename */
int azh__meta_read(const char *path, azh_state_meta *m);

#endif
