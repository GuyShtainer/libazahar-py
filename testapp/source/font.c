// SPDX-License-Identifier: GPL-3.0-or-later
#include "font.h"

#include <assert.h>

// Row-major, three bits per row, bit 14 is the top-left pixel.
static const uint16_t k_glyph[10] = {
    0x7B6F, 0x2C97, 0x73E7, 0x73CF, 0x5BC9, 0x79CF, 0x79EF, 0x7249, 0x7BEF, 0x7BCF,
};

int font_pixel(int digit, int col, int row)
{
    if (digit < 0 || digit > 9 || col < 0 || col >= LAZ_GLYPH_W || row < 0 || row >= LAZ_GLYPH_H) {
        return 0;
    }
    assert(digit >= 0 && digit <= 9);
    assert(row * LAZ_GLYPH_W + col < 15);
    return (k_glyph[digit] >> (14 - (row * LAZ_GLYPH_W + col))) & 1;
}
