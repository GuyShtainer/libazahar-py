/* azh_pure.h: prototypes of the pure modules (version.c, crop.c, png.c). They include only this header and
 * <stdint.h>/<string.h>/zlib, never libretro or Vulkan, so Phase 2's unit tests can link them alone. */
#ifndef AZH_PURE_H
#define AZH_PURE_H

#include <stddef.h>
#include <stdint.h>

/* version.c: 1 when v is the pinned stock version, the stock version plus AZH_LAZPY_SUFFIX exactly, or any_core. */
int azh_version_ok(const char *v, int any_core);

/* crop.c: where the two screens sit in a core frame (default layout at resolution factor f: the frame is
 * 400f x 480f, top at (0,0) 400f x 240f, bottom at (40f,240f) 320f x 240f). Returns 0, or -1 for any other size. */
typedef struct { uint32_t x, y, w, h; } azh_rect;
int azh_crop_rects(uint32_t fw, uint32_t fh, azh_rect *top, azh_rect *bottom);

/* png.c: 8-bit RGBA PNG, filter 0, zlib level 6. azh_png_init() builds the CRC table once and must come first.
 * px points at the first pixel, stride is the byte distance between rows. Returns 0, -1 (bad argument), -2 (I/O). */
void azh_png_init(void);
int azh_png_write(const char *path, const uint8_t *px, uint32_t w, uint32_t h, size_t stride);

#endif
