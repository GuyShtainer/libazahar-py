// SPDX-License-Identifier: GPL-3.0-or-later
#include "record.h"

#include <assert.h>
#include <stdio.h>

// Every argument is cast to its format's own type: uint32_t is unsigned long on devkitARM and
// unsigned int on the Mac, and no <inttypes.h> keeps this file warning-free on both.

static int finish(int n, size_t cap)
{
    assert(cap > 0);
    assert(n >= 0);  // snprintf encoding errors cannot happen with these formats
    if (n < 0 || (size_t)n >= cap) {
        return 0;
    }
    return n;
}

void record_fill(laz_record *rec, uint32_t frame, uint32_t vblank, uint32_t keys,
                 uint16_t tx, uint16_t ty, int16_t cx, int16_t cy, uint64_t tick)
{
    assert(rec != NULL);
    assert(sizeof(*rec) == 32);
    rec->magic = LAZ_RECORD_MAGIC;
    rec->frame = frame;
    rec->vblank = vblank;
    rec->keys = keys;
    rec->tx = tx;
    rec->ty = ty;
    rec->cx = cx;
    rec->cy = cy;
    rec->tick = tick;
}

int record_fmt_start(char *buf, size_t cap, uintptr_t addr_global, uintptr_t addr_heap, unsigned size,
                     int mode3d, uint32_t break_at, uint32_t exit_at, uint32_t ready_at, uint32_t boot_frames)
{
    if (buf == NULL || cap == 0) {
        return 0;
    }
    assert(cap > 0);
    int n = snprintf(buf, cap,
                     "start addr_global=0x%08lx addr_heap=0x%08lx size=%u mode=%s break_at=%lu exit_at=%lu "
                     "ready_at=%lu boot_frames=%lu\n",
                     (unsigned long)addr_global, (unsigned long)addr_heap, size, mode3d ? "3d" : "2d",
                     (unsigned long)break_at, (unsigned long)exit_at, (unsigned long)ready_at,
                     (unsigned long)boot_frames);
    return finish(n, cap);
}

int record_fmt_frame(char *buf, size_t cap, const laz_record *rec, uint64_t time_ms)
{
    if (buf == NULL || cap == 0 || rec == NULL) {
        return 0;
    }
    assert(cap > 0);
    int n = snprintf(buf, cap, "f=%lu v=%lu s=%llu t=%llu k=%08lx tx=%u ty=%u td=%u cx=%d cy=%d\n",
                     (unsigned long)rec->frame, (unsigned long)rec->vblank, (unsigned long long)rec->tick,
                     (unsigned long long)time_ms, (unsigned long)rec->keys, (unsigned)rec->tx,
                     (unsigned)rec->ty, (unsigned)((rec->keys >> 20) & 1u), (int)rec->cx, (int)rec->cy);
    return finish(n, cap);
}

int record_fmt_event(char *buf, size_t cap, const char *kind, uint32_t frame, uint32_t vblank)
{
    if (buf == NULL || cap == 0 || kind == NULL) {
        return 0;
    }
    assert(cap > 0);
    int n = snprintf(buf, cap, "%s f=%lu v=%lu\n", kind, (unsigned long)frame, (unsigned long)vblank);
    return finish(n, cap);
}

int record_fmt_booted(char *buf, size_t cap, uint32_t frame, uint32_t vblank, uint32_t sum)
{
    if (buf == NULL || cap == 0) {
        return 0;
    }
    assert(cap > 0);
    int n = snprintf(buf, cap, "booted f=%lu v=%lu sum=%08lx\n", (unsigned long)frame, (unsigned long)vblank,
                     (unsigned long)sum);
    return finish(n, cap);
}

int record_fmt_control_error(char *buf, size_t cap, uint32_t line_no)
{
    if (buf == NULL || cap == 0) {
        return 0;
    }
    assert(cap > 0);
    return finish(snprintf(buf, cap, "control error line=%lu\n", (unsigned long)line_no), cap);
}

int record_fmt_spin_cap(char *buf, size_t cap, uint32_t frame)
{
    if (buf == NULL || cap == 0) {
        return 0;
    }
    assert(cap > 0);
    return finish(snprintf(buf, cap, "boot spin cap f=%lu\n", (unsigned long)frame), cap);
}
