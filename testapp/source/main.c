// SPDX-License-Identifier: GPL-3.0-or-later
// libazahar-py test app. Behaviour is specified in docs/plans/phase-b.md section 3.
// The app never exits on a button (START included): it leaves on aptMainLoop() false, at exit_at, or at the frame cap.
#include <3ds.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "control.h"
#include "draw2d.h"
#include "record.h"
#include "scene3d.h"
#include "sdlog.h"
#include "stencil.h"

enum {
    LAZ_FRAME_CAP = 100000000,
    LAZ_SPIN_WORDS = 16384,           // 64 KiB
    LAZ_SPIN_CHECK_EVERY = 1024,
    LAZ_SPIN_STEP_CAP = 50000000,
    LAZ_CONTROL_BUF = 1100,
};

static laz_control g_ctl;
static laz_record g_record;       // global copy: step G reads it by address
static laz_record *g_heap_record;  // heap copy: same values, same frame
static volatile uint32_t g_vblank;
static uint32_t g_spin_buf[LAZ_SPIN_WORDS];
static uint32_t g_xorshift = 2463534242u;

// The one function pointer the app passes: libctru's GSP event thread calls this on every VBlank0.
// It is registered once at start, before citro3d exists (citro3d owns the single VBlank0 slot after C3D_Init).
static void on_vblank(void *unused)
{
    (void)unused;
    __atomic_fetch_add(&g_vblank, 1u, __ATOMIC_RELAXED);
}

static uint32_t vblank_now(void)
{
    return __atomic_load_n(&g_vblank, __ATOMIC_RELAXED);
}

static void put(const char *line, int len)
{
    if (len > 0) {
        (void)sdlog_line(line, len);  // a failed log write must not stop the app; the checker sees the gap
    }
}

static void put_event(const char *kind, uint32_t f, uint32_t v)
{
    char buf[LAZ_LOG_LINE_MAX];
    put(buf, record_fmt_event(buf, sizeof(buf), kind, f, v));
}

static int app_init(void)
{
    char text[LAZ_CONTROL_BUF];
    char buf[LAZ_LOG_LINE_MAX];

    gfxInitDefault();
    gspSetEventCallback(GSPGPU_EVENT_VBlank0, on_vblank, NULL, false);
    if (sdlog_init() != 0) {
        (void)svcOutputDebugString("testapp: SD archive failed", 26);
        return -1;
    }
    const uint32_t n = sdlog_read_control(text, sizeof(text));
    (void)control_parse(text, n, &g_ctl);
    if (sdlog_open() != 0) {
        (void)svcOutputDebugString("testapp: log open failed", 24);
        return -1;
    }
    g_heap_record = malloc(sizeof(*g_heap_record));
    if (g_heap_record == NULL) {
        return -1;
    }
    memset(g_heap_record, 0, sizeof(*g_heap_record));
    memset(&g_record, 0, sizeof(g_record));
    put(buf, record_fmt_start(buf, sizeof(buf), (uintptr_t)&g_record, (uintptr_t)g_heap_record,
                              (unsigned)sizeof(laz_record), g_ctl.mode3d, g_ctl.break_at, g_ctl.exit_at,
                              g_ctl.ready_at, g_ctl.boot_frames));
    for (uint32_t i = 0; i < g_ctl.error_count && i < LAZ_CONTROL_MAX_LINES + 1u; i++) {
        put(buf, record_fmt_control_error(buf, sizeof(buf), g_ctl.error_line[i]));
    }
    return 0;
}

static uint32_t spin_checksum(void)
{
    uint32_t sum = 0;
    for (int i = 0; i < LAZ_SPIN_WORDS; i++) {
        sum = (sum << 1 | sum >> 31) ^ g_spin_buf[i];
    }
    return sum;
}

// One boot frame: a bounded xorshift loop over a 64 KiB buffer until the VBlank counter moves.
// Returns 1 if the step cap was hit. Assumption B4: libctru's GSP thread preempts us, so the counter moves.
static int spin_one_frame(void)
{
    assert(g_xorshift != 0);  // xorshift32 is stuck at zero
    const uint32_t start = vblank_now();
    uint32_t x = g_xorshift;
    for (uint32_t steps = 1; steps <= LAZ_SPIN_STEP_CAP; steps++) {
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        g_spin_buf[x & (LAZ_SPIN_WORDS - 1)] += x;
        if (steps % LAZ_SPIN_CHECK_EVERY == 0 && vblank_now() != start) {
            g_xorshift = x;
            return 0;
        }
    }
    g_xorshift = x;
    return 1;
}

static void busy_boot(void)
{
    char buf[LAZ_LOG_LINE_MAX];
    int capped = 0;
    assert(g_ctl.boot_frames <= 10000u);
    for (uint32_t f = 1; f <= g_ctl.boot_frames && aptMainLoop(); f++) {
        if (spin_one_frame() && !capped) {
            capped = 1;
            put(buf, record_fmt_spin_cap(buf, sizeof(buf), f));
        }
        gfxFlushBuffers();
        gfxSwapBuffers();
    }
    if (g_ctl.boot_frames > 0) {
        put(buf, record_fmt_booted(buf, sizeof(buf), g_ctl.boot_frames, vblank_now(), spin_checksum()));
    }
}

// Fill both record copies, then write the per-frame line.
static void log_frame(uint32_t f, uint32_t v)
{
    char buf[LAZ_LOG_LINE_MAX];
    touchPosition touch;
    circlePosition circle;
    assert(f >= 1 && f <= LAZ_FRAME_CAP);
    memset(&touch, 0, sizeof(touch));
    memset(&circle, 0, sizeof(circle));
    hidScanInput();
    const uint32_t keys = hidKeysHeld();
    hidTouchRead(&touch);
    hidCircleRead(&circle);
    const uint64_t tick = svcGetSystemTick();
    record_fill(&g_record, f, v, keys, (uint16_t)touch.px, (uint16_t)touch.py, (int16_t)circle.dx,
                (int16_t)circle.dy, tick);
    if (g_heap_record != NULL) {
        memcpy(g_heap_record, &g_record, sizeof(g_record));
    }
    put(buf, record_fmt_frame(buf, sizeof(buf), &g_record, osGetTime()));
}

// break_at, ready_at, exit_at for frame f. Returns 1 when the app should leave after this frame.
static int run_events(uint32_t f, uint32_t v)
{
    assert(f >= 1);
    if (g_ctl.break_at == f) {
        put_event("break", f, v);
        svcBreak(USERBREAK_ASSERT);  // the guest runs on after this returns
    }
    if (g_ctl.ready_at == f) {
        put_event("ready", f, v);
    }
    if (g_ctl.exit_at == f) {
        put_event("exit", f, v);
        return 1;
    }
    return 0;
}

// 2D drawing for frame f: markers once per buffer in the first two frames after the boot, then the counter.
static void draw_frame_2d(uint32_t f)
{
    assert(f > g_ctl.boot_frames);
    uint8_t *top = gfxGetFramebuffer(GFX_TOP, GFX_LEFT, NULL, NULL);
    uint8_t *bottom = gfxGetFramebuffer(GFX_BOTTOM, GFX_LEFT, NULL, NULL);
    if (top == NULL || bottom == NULL) {
        return;
    }
    if (f == g_ctl.boot_frames + 1u || f == g_ctl.boot_frames + 2u) {
        draw_background(top, LAZ_TOP_W);
        draw_markers_on(top, LAZ_TOP_W, 1);
        draw_background(bottom, LAZ_BOTTOM_W);
        draw_markers_on(bottom, LAZ_BOTTOM_W, 0);
    }
    draw_counter(top, LAZ_TOP_W, f);
    gfxFlushBuffers();
    gfxSwapBuffers();
    gspWaitForVBlank0();
}

static void main_loop(void)
{
    const int mode3d = g_ctl.mode3d;
    int leave = 0;
    assert(mode3d == 0 || mode3d == 1);
    assert(g_ctl.boot_frames < LAZ_FRAME_CAP);
    for (uint32_t f = g_ctl.boot_frames + 1u; f <= LAZ_FRAME_CAP && !leave && aptMainLoop(); f++) {
        if (mode3d) {
            scene3d_begin();
        }
        const uint32_t v = mode3d ? scene3d_vblank() : vblank_now();
        log_frame(f, v);
        leave = run_events(f, v);
        if (mode3d) {
            scene3d_draw(f);
            scene3d_end();
        } else {
            draw_frame_2d(f);
        }
    }
}

int main(void)
{
    int rc = 0;
    if (app_init() != 0) {
        rc = 1;
    } else {
        busy_boot();
        if (g_ctl.stencil != 0) {
            if (stencil_run(g_ctl.stencil) != 0) {
                rc = 1;
            }
            for (uint32_t f = 0; f < LAZ_FRAME_CAP && aptMainLoop(); f++) {
                stencil_idle_frame();
            }
            stencil_exit();
        } else if (g_ctl.mode3d && scene3d_init() != 0) {
            put_event("scene3d init failed", 0, 0);
            rc = 1;
        } else {
            main_loop();
        }
        if (g_ctl.mode3d) {
            scene3d_exit();
        }
    }
    sdlog_close();
    free(g_heap_record);
    gfxExit();
    return rc;
}
