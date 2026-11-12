// SPDX-License-Identifier: GPL-3.0-or-later
// 3D mode: citro3d draws a rotating triangle on the top screen, citro2d draws the markers and the counter.
#ifndef LAZ_SCENE3D_H
#define LAZ_SCENE3D_H

#include <stdint.h>

// Start citro3d and citro2d, create both screen targets and load the shader. Returns 0 on success.
int scene3d_init(void);
// Wait for the VBlank and open the frame (C3D_FrameBegin with SYNCDRAW, which blocks and cannot fail).
void scene3d_begin(void);
// citro3d's VBlank counter (our `v` in 3D mode).
uint32_t scene3d_vblank(void);
// Draw the triangle, then the markers on both screens and the counter on the top one.
void scene3d_draw(uint32_t frame);
void scene3d_end(void);
void scene3d_exit(void);

#endif
