/* test_rawcopy.c: one rectangle at a time from a synthetic 400 x 480 RGBA frame, alpha forced to 255. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "azh_pure.h"
#include "test_main.h"

#define FW 400
#define FH 480

static uint8_t src_byte(int x, int y, int c)
{
    return (uint8_t)((x * 7 + y * 13 + c * 29) & 0xff);
}

static void fill_frame(uint8_t *f, int stride)
{
    int x;
    int y;
    int c;

    memset(f, 0xAA, (size_t)stride * FH);
    for (y = 0; y < FH; y++) {
        for (x = 0; x < FW; x++) {
            for (c = 0; c < 3; c++) {
                f[(size_t)y * (size_t)stride + (size_t)x * 4u + (size_t)c] = src_byte(x, y, c);
            }
            f[(size_t)y * (size_t)stride + (size_t)x * 4u + 3u] = 0;
        }
    }
}

static void check_rect(const uint8_t *dst, azh_rect r, const char *name)
{
    long bad = 0;
    uint32_t x;
    uint32_t y;
    int c;

    for (y = 0; y < r.h; y++) {
        for (x = 0; x < r.w; x++) {
            const uint8_t *p = dst + ((size_t)y * r.w + x) * 4u;

            for (c = 0; c < 3; c++) {
                bad += p[c] != src_byte((int)(r.x + x), (int)(r.y + y), c);
            }
            bad += p[3] != 255;
        }
    }
    check(bad == 0, "%s: %ld wrong bytes", name, bad);
}

static void run_stride(int stride)
{
    azh_rect top;
    azh_rect bottom;
    uint8_t *frame = malloc((size_t)stride * FH);
    uint8_t *dst = malloc(400u * 240u * 4u);

    check(frame != NULL && dst != NULL, "allocation");
    if (frame == NULL || dst == NULL) {
        free(frame);
        free(dst);
        return;
    }
    fill_frame(frame, stride);
    check(azh_crop_rects(FW, FH, &top, &bottom) == 0, "azh_crop_rects 400x480");
    memset(dst, 0x55, 400u * 240u * 4u);
    azh__raw_copy(frame, stride, (int32_t)top.x, (int32_t)top.y, (int32_t)top.w, (int32_t)top.h, dst);
    check_rect(dst, top, "top");
    memset(dst, 0x55, 400u * 240u * 4u);
    azh__raw_copy(frame, stride, (int32_t)bottom.x, (int32_t)bottom.y, (int32_t)bottom.w, (int32_t)bottom.h, dst);
    check_rect(dst, bottom, "bottom");
    check(dst[320 * 240 * 4] == 0x55, "bytes past the bottom screen's area are untouched");
    free(frame);
    free(dst);
}

void test_rawcopy(void)
{
    run_stride(FW * 4);
    run_stride(FW * 4 + 64);        /* a source stride wider than the frame */
}
