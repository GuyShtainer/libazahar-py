// SPDX-License-Identifier: GPL-3.0-or-later
// The per-frame record and the log-line formatters (pure C; <stdio.h> only for snprintf).
#ifndef LAZ_RECORD_H
#define LAZ_RECORD_H

#include <stddef.h>
#include <stdint.h>

#define LAZ_RECORD_MAGIC 0x4C415A52u  // "LAZR"
#define LAZ_LOG_LINE_MAX 256

// Offsets (step G reads them): magic 0, frame 4, vblank 8, keys 12, tx 16, ty 18, cx 20, cy 22, tick 24.
typedef struct {
    uint32_t magic, frame, vblank, keys;
    uint16_t tx, ty;
    int16_t cx, cy;
    uint64_t tick;
} laz_record;

_Static_assert(sizeof(laz_record) == 32, "laz_record must be 32 bytes");
_Static_assert(offsetof(laz_record, tick) == 24, "laz_record.tick must sit at offset 24");

void record_fill(laz_record *rec, uint32_t frame, uint32_t vblank, uint32_t keys,
                 uint16_t tx, uint16_t ty, int16_t cx, int16_t cy, uint64_t tick);

// Each formatter writes one line ending in "\n" into buf and returns its length, or 0 on error.
int record_fmt_start(char *buf, size_t cap, uintptr_t addr_global, uintptr_t addr_heap, unsigned size,
                     int mode3d, uint32_t break_at, uint32_t exit_at, uint32_t ready_at, uint32_t boot_frames);
int record_fmt_frame(char *buf, size_t cap, const laz_record *rec, uint64_t time_ms);
// kind is "ready", "break" or "exit".
int record_fmt_event(char *buf, size_t cap, const char *kind, uint32_t frame, uint32_t vblank);
int record_fmt_booted(char *buf, size_t cap, uint32_t frame, uint32_t vblank, uint32_t sum);
int record_fmt_control_error(char *buf, size_t cap, uint32_t line_no);
int record_fmt_spin_cap(char *buf, size_t cap, uint32_t frame);

#endif
