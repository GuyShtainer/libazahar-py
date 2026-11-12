/* input.c (pure): input records to held state, the libretro input query, the touch pointer, and the float32 model
 * of what the guest sees (docs/plans/phase-c.md sections 2 and 4). Includes no libretro header: the device and id
 * numbers below are libretro.h's, and tests/host/test_input.c checks them against it. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"

enum { DEV_JOYPAD = 1, DEV_MOUSE = 2, DEV_ANALOG = 5, DEV_POINTER = 6 };
enum { ID_MASK = 256, ID_PTR_X = 0, ID_PTR_Y = 1, ID_PTR_PRESSED = 2, ID_JOY_L3 = 14, ID_JOY_R3 = 15 };
enum { FRAME_W = 400, FRAME_H = 480, BOT_X = 40, BOT_Y = 240, BOT_W = 320, BOT_H = 240, PTR_MAX = 32767 };
#define KEYMAP_N 14

/* libctru KEY_* bit -> libretro joypad id (docs/plans/phase-c.md section 2) */
static const struct { uint8_t bit, id; } keymap[KEYMAP_N] = {
    { 0, 8 }, { 1, 0 }, { 2, 2 }, { 3, 3 }, { 4, 7 }, { 5, 6 }, { 6, 4 },
    { 7, 5 }, { 8, 11 }, { 9, 10 }, { 10, 9 }, { 11, 1 }, { 14, 12 }, { 15, 13 },
};

static int fail(char *err, size_t cap, int32_t i, const char *field, const char *what)
{
    assert(err != NULL || cap == 0u);
    if (err != NULL && cap > 0u) {
        (void)snprintf(err, cap, "input record %d: %s %s", (int)i, field, what);
    }
    return AZH_E_ARG;
}

static int validate_one(const int32_t *r, int32_t i, int32_t frames, int32_t prev, char *err, size_t cap)
{
    assert(r != NULL);
    if (r[AZH_IN_FRAME] < 1 || r[AZH_IN_FRAME] > frames) {
        return fail(err, cap, i, "frame", "is outside 1..frames");
    }
    if (r[AZH_IN_FRAME] < prev) {
        return fail(err, cap, i, "frame", "is lower than the previous record's");
    }
    if (((uint32_t)r[AZH_IN_BUTTONS] & ~AZH_BUTTONS_MASK) != 0u) {
        return fail(err, cap, i, "buttons", "has a bit outside the mask 0xCFFF");
    }
    if (r[AZH_IN_TOUCH_DOWN] != 0 && r[AZH_IN_TOUCH_DOWN] != 1) {
        return fail(err, cap, i, "touch_down", "must be 0 or 1");
    }
    if (r[AZH_IN_TOUCH_DOWN] == 1 && (r[AZH_IN_TOUCH_X] < 0 || r[AZH_IN_TOUCH_X] >= BOT_W)) {
        return fail(err, cap, i, "touch_x", "must be 0..319");
    }
    if (r[AZH_IN_TOUCH_DOWN] == 1 && (r[AZH_IN_TOUCH_Y] < 0 || r[AZH_IN_TOUCH_Y] >= BOT_H)) {
        return fail(err, cap, i, "touch_y", "must be 0..239");
    }
    if (r[AZH_IN_CIRCLE_X] < -AZH_CIRCLE_MAX || r[AZH_IN_CIRCLE_X] > AZH_CIRCLE_MAX) {
        return fail(err, cap, i, "circle_x", "must be -32767..32767");
    }
    if (r[AZH_IN_CIRCLE_Y] < -AZH_CIRCLE_MAX || r[AZH_IN_CIRCLE_Y] > AZH_CIRCLE_MAX) {
        return fail(err, cap, i, "circle_y", "must be -32767..32767");
    }
    return AZH_OK;
}

int azh__input_validate(const int32_t *rec, int32_t n, int32_t frames, char *err, size_t errcap)
{
    int32_t i;
    int32_t prev = 1;
    int rc;

    assert(errcap == 0u || err != NULL);
    if (err != NULL && errcap > 0u) {
        err[0] = '\0';
    }
    if (n < 0 || n > AZH_MAX_INPUTS) {
        return fail(err, errcap, 0, "count", "n must be 0..1,000,000");
    }
    if (n > 0 && rec == NULL) {
        return fail(err, errcap, 0, "records", "are NULL");
    }
    for (i = 0; i < n; i++) {
        rc = validate_one(rec + (size_t)i * AZH_INPUT_INTS, i, frames, prev, err, errcap);
        if (rc != AZH_OK) {
            return rc;
        }
        prev = rec[(size_t)i * AZH_INPUT_INTS + AZH_IN_FRAME];
    }
    return AZH_OK;
}

void azh__touch_pointer(int32_t x, int32_t y, int16_t *px, int16_t *py)
{
    int64_t fx;
    int64_t fy;

    assert(px != NULL && py != NULL);
    assert(x >= 0 && x < BOT_W && y >= 0 && y < BOT_H);
    fx = x + BOT_X;
    fy = y + BOT_Y;
    *px = (int16_t)(((2 * fx + 1) * PTR_MAX) / FRAME_W - PTR_MAX);
    *py = (int16_t)(((2 * fy + 1) * PTR_MAX) / FRAME_H - PTR_MAX);
}

void azh__held_from_record(azh_held *h, const int32_t rec[AZH_INPUT_INTS])
{
    int i;

    assert(h != NULL && rec != NULL);
    memset(h, 0, sizeof *h);
    h->buttons = (uint32_t)rec[AZH_IN_BUTTONS] & AZH_BUTTONS_MASK;
    h->touch_down = rec[AZH_IN_TOUCH_DOWN];
    h->circle_x = rec[AZH_IN_CIRCLE_X];
    h->circle_y = rec[AZH_IN_CIRCLE_Y];
    for (i = 0; i < KEYMAP_N; i++) {
        if ((h->buttons >> keymap[i].bit & 1u) != 0u) {
            h->retro_mask = (uint16_t)(h->retro_mask | (1u << keymap[i].id));
        }
    }
    if (h->touch_down == 1) {
        h->touch_x = rec[AZH_IN_TOUCH_X];
        h->touch_y = rec[AZH_IN_TOUCH_Y];
        azh__touch_pointer(h->touch_x, h->touch_y, &h->ptr_x, &h->ptr_y);
    }
    assert((h->retro_mask & ((1u << ID_JOY_L3) | (1u << ID_JOY_R3))) == 0u);
}

static int16_t query_analog(const azh_held *h, unsigned index, unsigned id)
{
    if (index != 0u) {
        return 0;               /* the right stick is the C-stick; nothing drives it */
    }
    if (id == 0u) {
        return (int16_t)h->circle_x;
    }
    return (id == 1u) ? (int16_t)(-h->circle_y) : 0;
}

static int16_t query_pointer(const azh_held *h, unsigned index, unsigned id)
{
    if (index != 0u || h->touch_down != 1) {
        return 0;
    }
    if (id == ID_PTR_X) {
        return h->ptr_x;
    }
    if (id == ID_PTR_Y) {
        return h->ptr_y;
    }
    return (id == ID_PTR_PRESSED) ? 1 : 0;
}

int16_t azh__held_query(const azh_held *h, unsigned port, unsigned device, unsigned index, unsigned id)
{
    assert(h != NULL);
    if (port != 0u) {
        return 0;
    }
    if (device == DEV_JOYPAD) {
        if (id == ID_MASK) {
            return (int16_t)h->retro_mask;
        }
        return (id < 14u) ? (int16_t)((h->retro_mask >> id) & 1u) : 0;     /* 14 (L3, HOME) and 15 never */
    }
    if (device == DEV_ANALOG) {
        return query_analog(h, index, id);
    }
    if (device == DEV_POINTER) {
        return query_pointer(h, index, id);
    }
    assert(device != DEV_JOYPAD && device != DEV_ANALOG && device != DEV_POINTER);
    return 0;               /* DEV_MOUSE and everything else: no button, no motion */
}

/* the core's mouse_tracker.cpp:144-145 step, in float32 */
void azh__model_frame_pixel(int16_t px, int16_t py, int32_t *fx, int32_t *fy)
{
    float nx;
    float ny;

    assert(fx != NULL && fy != NULL);
    nx = ((float)(px + PTR_MAX) / (float)(PTR_MAX * 2)) * (float)FRAME_W;
    ny = ((float)(py + PTR_MAX) / (float)(PTR_MAX * 2)) * (float)FRAME_H;
    *fx = (int32_t)nx;
    *fy = (int32_t)ny;
}

/* emu_window.cpp:155-192 then hid.cpp:292-293 */
void azh__model_guest_touch(int32_t fx, int32_t fy, uint16_t *gx, uint16_t *gy)
{
    float tx;
    float ty;

    assert(gx != NULL && gy != NULL);
    tx = (float)(fx - BOT_X) / (float)BOT_W;
    ty = (float)(fy - BOT_Y) / (float)BOT_H;
    *gx = (uint16_t)(tx * (float)BOT_W);
    *gy = (uint16_t)(ty * (float)BOT_H);
}

int16_t azh__model_guest_circle(int32_t c)
{
    assert(c >= -AZH_CIRCLE_MAX && c <= AZH_CIRCLE_MAX);
    return (int16_t)roundf(((float)c / 32767.0f) * 154.0f);
}
