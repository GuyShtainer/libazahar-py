// SPDX-License-Identifier: GPL-3.0-or-later
// Our own 3x5 digit glyphs (15-bit masks).
#ifndef LAZ_FONT_H
#define LAZ_FONT_H

#include <stdint.h>

#define LAZ_GLYPH_W 3
#define LAZ_GLYPH_H 5

// 1 if pixel (col 0..2, row 0..4) of digit 0..9 is lit, else 0 (also 0 for bad arguments).
int font_pixel(int digit, int col, int row);

#endif
