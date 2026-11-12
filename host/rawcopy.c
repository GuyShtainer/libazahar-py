/* rawcopy.c (pure): one screen's rectangle from the RGBA readback into the map's pixel area, alpha forced to 255. */
#include <assert.h>
#include <string.h>

#include "azh_pure.h"

void azh__raw_copy(const uint8_t *src, int32_t src_stride, int32_t x, int32_t y, int32_t w, int32_t h,
                   uint8_t *dst)
{
    int32_t row;
    int32_t col;

    assert(src != NULL && dst != NULL);
    assert(x >= 0 && y >= 0 && w > 0 && h > 0 && src_stride >= (x + w) * 4);
    for (row = 0; row < h; row++) {
        const uint8_t *s = src + (size_t)(y + row) * (size_t)src_stride + (size_t)x * 4u;
        uint8_t *d = dst + (size_t)row * (size_t)w * 4u;

        memcpy(d, s, (size_t)w * 4u);
        for (col = 0; col < w; col++) {
            d[(size_t)col * 4u + 3u] = 255u;
        }
    }
}
