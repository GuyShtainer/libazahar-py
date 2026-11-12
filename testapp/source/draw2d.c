// SPDX-License-Identifier: GPL-3.0-or-later
#include "draw2d.h"

#include <assert.h>
#include <stddef.h>

#include "font.h"

static const laz_marker k_top[LAZ_MARKER_COUNT] = {
    {0, 0, 0xFF0000u}, {392, 0, 0x00FF00u}, {0, 232, 0x0000FFu}, {392, 232, 0xFFFFFFu},
};
static const laz_marker k_bottom[LAZ_MARKER_COUNT] = {
    {0, 0, 0xFFFF00u}, {312, 0, 0x00FFFFu}, {0, 232, 0xFF00FFu}, {312, 232, 0xFF8000u},
};

const laz_marker *draw_markers(int top)
{
    return top ? k_top : k_bottom;
}

void draw_fill(uint8_t *fb, int width, int x, int y, int w, int h, uint32_t rgb)
{
    assert(width == LAZ_TOP_W || width == LAZ_BOTTOM_W);
    if (fb == NULL) {
        return;
    }
    const uint8_t r = (uint8_t)(rgb >> 16), g = (uint8_t)(rgb >> 8), b = (uint8_t)rgb;
    for (int px = x; px < x + w && px < width; px++) {
        for (int py = y; py < y + h && py < LAZ_SCREEN_H; py++) {
            if (px < 0 || py < 0) {
                continue;
            }
            uint8_t *p = fb + ((px * LAZ_SCREEN_H) + (LAZ_SCREEN_H - 1 - py)) * 3;
            p[0] = b;
            p[1] = g;
            p[2] = r;
        }
    }
}

void draw_background(uint8_t *fb, int width)
{
    draw_fill(fb, width, 0, 0, width, LAZ_SCREEN_H, LAZ_BG_RGB);
}

void draw_markers_on(uint8_t *fb, int width, int top)
{
    assert(width == LAZ_TOP_W || width == LAZ_BOTTOM_W);
    const laz_marker *m = draw_markers(top);
    for (int i = 0; i < LAZ_MARKER_COUNT; i++) {
        draw_fill(fb, width, m[i].x, m[i].y, LAZ_MARKER_SIZE, LAZ_MARKER_SIZE, m[i].rgb);
    }
}

void draw_counter(uint8_t *fb, int width, uint32_t value)
{
    assert(width == LAZ_TOP_W);
    draw_fill(fb, width, LAZ_COUNTER_X, LAZ_COUNTER_Y, LAZ_COUNTER_DIGITS * LAZ_COUNTER_STRIDE, LAZ_GLYPH_H,
              LAZ_BG_RGB);
    for (int d = LAZ_COUNTER_DIGITS - 1; d >= 0; d--) {
        const int digit = (int)(value % 10u);
        value /= 10u;
        for (int row = 0; row < LAZ_GLYPH_H; row++) {
            for (int col = 0; col < LAZ_GLYPH_W; col++) {
                if (font_pixel(digit, col, row)) {
                    draw_fill(fb, width, LAZ_COUNTER_X + d * LAZ_COUNTER_STRIDE + col, LAZ_COUNTER_Y + row, 1, 1,
                              0xFFFFFFu);
                }
            }
        }
    }
}
