// SPDX-License-Identifier: GPL-3.0-or-later
// Parse sdmc:/testapp/control.txt (pure C: <stdint.h> and <string.h> only).
#ifndef LAZ_CONTROL_H
#define LAZ_CONTROL_H

#include <stdint.h>

#define LAZ_CONTROL_MAX_LINES 16
#define LAZ_CONTROL_MAX_LINE_BYTES 64

typedef struct {
    int mode3d;            // 0 = 2d (default), 1 = 3d
    uint32_t break_at;     // 0 = off
    uint32_t exit_at;      // 0 = off
    uint32_t ready_at;     // 0 = off
    uint32_t boot_frames;  // 0 = no busy boot
    uint32_t error_count;  // number of bad lines (recorded in error_line)
    uint32_t error_line[LAZ_CONTROL_MAX_LINES + 1];  // 1-based line numbers
} laz_control;

// Set every field to its default.
void control_defaults(laz_control *ctl);

// Parse `len` bytes of `text` (not NUL-terminated) into `ctl`; the defaults are set first.
// Returns the number of bad lines. A bad line (unknown key, bad value, too long, past line 16)
// keeps the default for that line.
uint32_t control_parse(const char *text, uint32_t len, laz_control *ctl);

#endif
