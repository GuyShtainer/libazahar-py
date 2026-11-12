/* run.c: the batch loop. retro_run up to `frames` times, heartbeat after each, PNG shots at their frames
 * (written after retro_run returns, never inside the video callback). */
#include <assert.h>
#include <stdio.h>
#include <time.h>

#include "azh_internal.h"

static azh_held held;                   /* the held input state; written only between retro_run calls */
static int64_t vblanks_total;           /* input_poll_cb calls since boot (C2 counts them) */

void azh__input_set(const azh_held *h)
{
    assert(h != NULL);
    held = *h;
}

void azh__input_get(azh_held *h)
{
    assert(h != NULL);
    *h = held;
}

void azh__input_install(void)
{
    /* C2: passes the input callbacks through the core table */
    assert(azh_g.core.set_input_state != NULL);
}

int64_t azh__vblanks_total(void)
{
    return vblanks_total;
}

void azh__counters_set(int64_t frame_total, int64_t vblanks)
{
    assert(frame_total >= 0 && vblanks >= 0);
    azh_g.abs_frames = frame_total;
    vblanks_total = vblanks;
}

void azh__counters_get(int64_t *frame_total, int64_t *vblanks)
{
    assert(frame_total != NULL && vblanks != NULL);
    *frame_total = azh_g.abs_frames;
    *vblanks = vblanks_total;
}

int azh__sd_root(char *buf, size_t cap)
{
    int n;

    assert(buf != NULL && cap > 0u);
    n = snprintf(buf, cap, "%s/Azahar/sdmc", azh_g.sysdir);
    return (n > 0 && (size_t)n < cap) ? AZH_OK : AZH_E_ARG;
}

int azh__run_one_frame(void)
{
    /* C2 */
    return AZH_E_UNSUPPORTED;
}

static double now_s(void)
{
    struct timespec t;

    assert(sizeof t >= sizeof(time_t));
    (void)clock_gettime(CLOCK_MONOTONIC, &t);     /* CLOCK_MONOTONIC cannot fail on macOS */
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

/* first retro_run since boot: a NULL or 0x0 frame means System::Load failed (docs/PLAN.md 2.6, case 3) */
static int check_first_frame(void)
{
    assert(azh_g.first_run_done == 0);
    assert(azh_g.abs_frames >= 1);
    azh_g.first_run_done = 1;
    if (azh_g.cb_calls == 0 || azh_g.cb_null != 0) {
        azh_g.phase = AZH_PH_DEAD;
        return azh_fail(AZH_E_BOOT, "%s", azh_g.last_msg[0] != '\0' ? azh_g.last_msg :
                        "the first frame was empty (NULL or 0x0)");
    }
    return AZH_OK;
}

static int take_shots(const azh_batch *b, int32_t frame, int32_t *done)
{
    char prefix[AZH_PATH_MAX + 32];
    int32_t i;
    int rc;

    assert(b != NULL && done != NULL);
    assert(frame >= 1 && frame <= b->frames);
    for (i = 0; i < b->n_shots; i++) {
        if (b->shots[i].frame != frame) {
            continue;
        }
        (void)snprintf(prefix, sizeof prefix, "%s/shot_%06lld", b->shot_dir, (long long)azh_g.abs_frames);
        rc = azh_frame_write(b->shots[i].screens, prefix);
        if (rc != AZH_OK) {
            return rc;
        }
        (*done)++;
    }
    return AZH_OK;
}

int azh_run_batch(const azh_batch *b, azh_result *out)
{
    double t0 = now_s();
    int32_t lo = 0x7fffffff;
    int32_t hi = 0;
    int32_t i;
    int rc = AZH_OK;

    assert(b != NULL && out != NULL);
    assert(b->frames >= 1 && b->n_shots >= 0 && b->n_shots <= AZH_MAX_SHOTS);
    for (i = 0; i < b->n_shots; i++) {
        if (b->shots[i].frame < lo) {
            lo = b->shots[i].frame;
        }
        if (b->shots[i].frame > hi) {
            hi = b->shots[i].frame;
        }
    }
    out->first_frame = azh_g.abs_frames + 1;
    out->shots_done = 0;
    for (i = 1; i <= b->frames && rc == AZH_OK; i++) {
        azh_g.cb_calls = 0;
        azh_g.core.run();
        azh_g.abs_frames++;
        azh_map_heartbeat();
        out->frames_run = i;
        if (azh_g.first_run_done == 0) {
            rc = check_first_frame();
        }
        if (rc == AZH_OK && i >= lo && i <= hi) {
            rc = take_shots(b, i, &out->shots_done);
        }
    }
    out->last_frame = azh_g.abs_frames;
    out->stop_reason = AZH_STOP_FRAMES;
    out->wall_s = now_s() - t0;
    return rc;
}
