// SPDX-License-Identifier: GPL-3.0-or-later
// CPU drawing into libctru BGR8 framebuffers (column-major, 240 pixels tall), plus the marker table.
#ifndef LAZ_DRAW2D_H
#define LAZ_DRAW2D_H

#include <stdint.h>

#define LAZ_SCREEN_H 240
#define LAZ_TOP_W 400
#define LAZ_BOTTOM_W 320
#define LAZ_BG_RGB 0x202020u
#define LAZ_MARKER_SIZE 8
#define LAZ_MARKER_COUNT 4
// The frame counter: 8 digits, 4 pixels apart, at the top screen's centre (at least 16 px from every marker).
#define LAZ_COUNTER_DIGITS 8
#define LAZ_COUNTER_X 184
#define LAZ_COUNTER_Y 118
#define LAZ_COUNTER_STRIDE 4

typedef struct {
    int x, y;
    uint32_t rgb;  // 0xRRGGBB
} laz_marker;

// The four markers of a screen (top = 1, bottom = 0); LAZ_MARKER_COUNT entries.
const laz_marker *draw_markers(int top);

// All drawing takes the framebuffer, its width (400 or 320), and clips to the screen.
void draw_fill(uint8_t *fb, int width, int x, int y, int w, int h, uint32_t rgb);
void draw_background(uint8_t *fb, int width);
void draw_markers_on(uint8_t *fb, int width, int top);
// Redraw the counter area with value mod 10^8 (background first).
void draw_counter(uint8_t *fb, int width, uint32_t value);

#endif
