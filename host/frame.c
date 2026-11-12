/* frame.c: the video, audio and input callbacks, and writing the last frame as PNGs.
 * The video callback only notes the frame (HW) or copies it (software); the readback and PNG run after retro_run. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "azh_internal.h"

#define FRAME_MAX_W 7200u
#define FRAME_MAX_H 4800u

/* software XRGB8888 (B, G, R, X in memory) to RGBA with alpha 255, rows copied with the pitch */
static void copy_sw(const uint8_t *src, unsigned w, unsigned h, size_t pitch)
{
    unsigned y;
    unsigned x;
    uint8_t *dst = azh_g.sw;

    for (y = 0; y < h; y++) {
        const uint8_t *s = src + (size_t)y * pitch;

        for (x = 0; x < w; x++) {
            dst[0] = s[2];
            dst[1] = s[1];
            dst[2] = s[0];
            dst[3] = 255u;
            s += 4;
            dst += 4;
        }
    }
}

void azh_video_cb(const void *data, unsigned w, unsigned h, size_t pitch)
{
    size_t need;

    azh_g.cb_calls++;
    if (data == NULL || w == 0u || h == 0u) {
        azh_g.cb_null = 1;
        return;
    }
    azh_g.cb_null = 0;
    if (w > FRAME_MAX_W || h > FRAME_MAX_H) {
        azh_log(AZH_LOG_ERROR, "video frame %ux%u exceeds the %ux%u maximum; ignored", w, h, FRAME_MAX_W,
                FRAME_MAX_H);
        return;
    }
    if (w != azh_g.fw || h != azh_g.fh) {
        azh_log(AZH_LOG_INFO, "frame size %ux%u", w, h);
    }
    azh_g.fw = w;
    azh_g.fh = h;
    if (data == RETRO_HW_FRAME_BUFFER_VALID) {
        azh_g.frame_kind = 1;
        return;
    }
    need = (size_t)w * h * 4u;
    if (azh_g.sw_cap < need) {
        uint8_t *p = realloc(azh_g.sw, need);

        if (p == NULL) {
            azh_log(AZH_LOG_ERROR, "out of memory for a %ux%u software frame", w, h);
            azh_g.frame_kind = 0;     /* never let a shot write the old pixels */
            return;
        }
        azh_g.sw = p;
        azh_g.sw_cap = need;
    }
    copy_sw((const uint8_t *)data, w, h, pitch);
    azh_g.frame_kind = 2;
}

void azh_audio_sample_cb(int16_t l, int16_t r)
{
    (void)l;     /* audio is discarded: the host never plays it */
    (void)r;
}

size_t azh_audio_batch_cb(const int16_t *data, size_t frames)
{
    (void)data;
    return frames;
}

void azh_input_poll_cb(void)
{
}

int16_t azh_input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id)
{
    (void)port;     /* step C answers inputs; until then nothing is ever pressed */
    (void)device;
    (void)index;
    (void)id;
    return 0;
}

/* the RGBA pixels of the last frame: a fresh readback for a HW frame, the copy for a software one */
static int frame_pixels(const uint8_t **px)
{
    if (azh_g.frame_kind == 1) {
        return azh_vk_readback(azh_g.fw, azh_g.fh, px);
    }
    if (azh_g.frame_kind == 2 && azh_g.sw != NULL) {
        *px = azh_g.sw;
        return AZH_OK;
    }
    return azh_fail(AZH_E_ORDER, "no frame has been delivered yet");
}

static int write_one(const char *prefix, const char *name, const uint8_t *px, const azh_rect *r)
{
    char path[AZH_PATH_MAX + 16];
    size_t stride = (size_t)azh_g.fw * 4u;
    int n = snprintf(path, sizeof path, "%s_%s.png", prefix, name);

    if (n < 0 || (size_t)n >= sizeof path) {
        return azh_fail(AZH_E_ARG, "shot path too long");
    }
    if (azh_png_write(path, px + (size_t)r->y * stride + (size_t)r->x * 4u, r->w, r->h, stride) != 0) {
        return azh_fail(AZH_E_IO, "cannot write %s", path);
    }
    azh_log(AZH_LOG_INFO, "wrote %s (%ux%u)", path, r->w, r->h);
    return AZH_OK;
}

int azh_frame_write(int32_t screens, const char *prefix)
{
    const uint8_t *px = NULL;
    azh_rect top;
    azh_rect bottom;
    int rc;

    assert(prefix != NULL);
    assert(screens >= AZH_SCREEN_TOP && screens <= AZH_SCREEN_BOTH);
    rc = frame_pixels(&px);
    if (rc != AZH_OK) {
        return rc;
    }
    if (azh_crop_rects(azh_g.fw, azh_g.fh, &top, &bottom) != 0) {
        return azh_fail(AZH_E_CORE, "unexpected frame size %ux%u (want 400f x 480f)", azh_g.fw, azh_g.fh);
    }
    if ((screens & AZH_SCREEN_TOP) != 0) {
        rc = write_one(prefix, "top", px, &top);
        if (rc != AZH_OK) {
            return rc;
        }
    }
    if ((screens & AZH_SCREEN_BOTTOM) != 0) {
        rc = write_one(prefix, "bottom", px, &bottom);
    }
    return rc;
}

void azh_frame_free(void)
{
    free(azh_g.sw);
    azh_g.sw = NULL;
    azh_g.sw_cap = 0;
}
