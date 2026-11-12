/* crop.c: where top and bottom sit in a core frame (pure; no Vulkan). */
#include <assert.h>
#include <stdint.h>

#include "azh_pure.h"

#define AZH_CROP_MAX_FACTOR 10u

int azh_crop_rects(uint32_t fw, uint32_t fh, azh_rect *top, azh_rect *bottom)
{
    uint32_t f;

    assert(top != NULL && bottom != NULL);
    if (fw == 0u || fw % 400u != 0u) {
        return -1;
    }
    f = fw / 400u;
    if (f > AZH_CROP_MAX_FACTOR || fh != 480u * f) {
        return -1;
    }
    top->x = 0u;
    top->y = 0u;
    top->w = 400u * f;
    top->h = 240u * f;
    bottom->x = 40u * f;
    bottom->y = 240u * f;
    bottom->w = 320u * f;
    bottom->h = 240u * f;
    assert(bottom->y + bottom->h == fh);
    return 0;
}
