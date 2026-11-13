// SPDX-License-Identifier: GPL-3.0-or-later
// Stencil self-test (control key stencil=N): fill a D24S8 target, draw one stencil-writing quad, copy the depth
// buffer back to linear memory and log the counts on one line per readback. Specified in
// docs/research/stencil-readback.md ("Test-app repro").
#ifndef LAZ_STENCIL_H
#define LAZ_STENCIL_H

#include <stdint.h>

// mode: 1 = variant a (first use) then d (second readback); 2 = variant b (a dummy draw first);
// 3 and 4 = the same as 1 and 2 with the EQUAL/INCR stencil ops. Returns 0 on success.
int stencil_run(uint32_t mode);
// One empty citro3d frame (keeps the app vblanking after the test). Call stencil_run first.
void stencil_idle_frame(void);
void stencil_exit(void);

#endif
