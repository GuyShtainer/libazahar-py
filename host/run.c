/* run.c: the batch loop, the input callbacks, the counters and the raw copy of a frame into the map.
 * Per frame: the input records of that frame, retro_run, heartbeat and counters, shots, then the stop rules in
 * priority order (docs/plans/phase-c.md 3.4). Shots are written after retro_run returns, never inside a callback. */
#include <assert.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

#include "azh_internal.h"


static azh_held held;                   /* the held input state; written only between retro_run calls */
static int64_t vblanks_total;           /* input_poll_cb calls since boot */
static pthread_t run_thread;            /* the thread inside retro_run, for the callbacks' assert */
static int run_active;

/* 1 when no batch is running, or when the caller is the thread inside retro_run: the audio callbacks assert it */
int azh__in_run_thread(void)
{
    return run_active == 0 || pthread_equal(pthread_self(), run_thread) ? 1 : 0;
}

static int16_t input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id)
{
    assert(run_active == 0 || pthread_equal(pthread_self(), run_thread));
    return azh__held_query(&held, port, device, index, id);
}

static void input_poll_cb(void)
{
    assert(run_active == 0 || pthread_equal(pthread_self(), run_thread));
    vblanks_total++;
}

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
    assert(azh_g.core.set_input_state != NULL && azh_g.core.set_input_poll != NULL);
    azh_g.core.set_input_poll(input_poll_cb);
    azh_g.core.set_input_state(input_state_cb);
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
    azh_map_set_counters(frame_total, vblanks);
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

static double now_s(void)
{
    struct timespec t;

    assert(sizeof t >= sizeof(time_t));
    (void)clock_gettime(CLOCK_MONOTONIC, &t);     /* CLOCK_MONOTONIC cannot fail on macOS */
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

static int64_t now_ns(void)
{
    struct timespec t;

    (void)clock_gettime(CLOCK_MONOTONIC, &t);     /* CLOCK_MONOTONIC cannot fail on macOS */
    return (int64_t)t.tv_sec * 1000000000 + (int64_t)t.tv_nsec;
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

int azh__run_one_frame(int64_t *run_ns)
{
    int rc = AZH_OK;
    int64_t t_run;

    assert(azh_g.phase == AZH_PH_BOOTED && azh_g.core.run != NULL);
    azh_g.cb_calls = 0;
    azh__msg_begin_run(&azh_msgs);
    run_thread = pthread_self();
    run_active = 1;
    t_run = now_ns();
    azh_g.core.run();
    if (run_ns != NULL) {
        *run_ns = now_ns() - t_run;         /* wall of the retro_run call */
    }
    run_active = 0;
    azh_g.abs_frames++;
    if (azh_g.first_run_done == 0) {
        rc = check_first_frame();
    }
    azh_map_heartbeat();
    azh_map_set_counters(azh_g.abs_frames, vblanks_total);
    return rc;
}

/* the RGBA pixels of the last frame (the same two sources as frame.c's PNG path) */
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

/* a raw shot of the current frame into the map; px_frame is -1 while the copy runs (called from api.c too) */
int azh_run_raw_shot(int32_t screens)
{
    const uint8_t *px = NULL;
    uint32_t dims[4] = { 400u, 240u, 320u, 240u };
    azh_rect top;
    azh_rect bottom;
    uint8_t *dst = azh_map_pixels();
    int32_t stride;
    int rc;

    assert(screens >= AZH_SCREEN_TOP && screens <= AZH_SCREEN_BOTH);
    if (dst == NULL) {
        return azh_fail(AZH_E_ORDER, "no map to write raw pixels into");
    }
    if (azh_g.fw != 400u || azh_g.fh != 480u) {
        return azh_fail(AZH_E_UNSUPPORTED, "raw shots need resolution factor 1 (frame %ux%u)", azh_g.fw, azh_g.fh);
    }
    rc = frame_pixels(&px);
    if (rc != AZH_OK) {
        return rc;
    }
    if (azh_crop_rects(azh_g.fw, azh_g.fh, &top, &bottom) != 0) {
        return azh_fail(AZH_E_CORE, "unexpected frame size %ux%u", azh_g.fw, azh_g.fh);
    }
    stride = (int32_t)(azh_g.fw * 4u);
    azh_map_raw_begin(dims);
    if ((screens & AZH_SCREEN_TOP) != 0) {
        azh__raw_copy(px, stride, (int32_t)top.x, (int32_t)top.y, (int32_t)top.w, (int32_t)top.h, dst);
    }
    if ((screens & AZH_SCREEN_BOTTOM) != 0) {
        azh__raw_copy(px, stride, (int32_t)bottom.x, (int32_t)bottom.y, (int32_t)bottom.w, (int32_t)bottom.h,
                      dst + 400u * 240u * 4u);
    }
    azh_map_raw_end(azh_g.abs_frames);
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
        if (b->shots[i].format == AZH_FMT_RAW) {
            rc = azh_run_raw_shot(b->shots[i].screens);
        } else {
            (void)snprintf(prefix, sizeof prefix, "%s/shot_%06lld", b->shot_dir, (long long)azh_g.abs_frames);
            rc = azh_frame_write(b->shots[i].screens, prefix);
        }
        if (rc != AZH_OK) {
            return rc;
        }
        (*done)++;
    }
    return AZH_OK;
}

/* everything one batch keeps between frames */
typedef struct {
    const azh_batch *b;
    azh_result *out;
    const int32_t *in;
    int32_t n_in;
    int32_t next_in;
    int32_t lo, hi;                     /* first and last shot frame */
    int sd_on;
    int32_t sd_every;
    azh_matcher sd;
    char sd_path[AZH_PATH_MAX + 64];
    int debug_on;
    double t0;
    int64_t core_ns;                    /* sum of the retro_run walls (callbacks from inside retro_run count here) */
    int64_t shot_ns;                    /* sum of the PNG and RAW shot walls */
} batch_t;

/* the records of frame i, in order: the last one wins */
static void apply_inputs(batch_t *c, int32_t i)
{
    azh_held h;

    assert(c != NULL && i >= 1);
    while (c->next_in < c->n_in && c->in[(size_t)c->next_in * AZH_INPUT_INTS + AZH_IN_FRAME] == i) {
        azh__held_from_record(&h, c->in + (size_t)c->next_in * AZH_INPUT_INTS);
        azh__input_set(&h);
        c->next_in++;
    }
}

static int sd_start(batch_t *c)
{
    char root[AZH_PATH_MAX];
    struct stat st;
    int64_t from = 0;

    assert(c != NULL && c->b->sd_file[0] != '\0');
    if (azh__sd_root(root, sizeof root) != AZH_OK ||
        snprintf(c->sd_path, sizeof c->sd_path, "%s/%s", root, c->b->sd_file) >= (int)sizeof c->sd_path) {
        return azh_fail(AZH_E_ARG, "azh_run: the SD file path is too long");
    }
    if (c->b->sd_from_end != 0 && stat(c->sd_path, &st) == 0) {
        from = azh__file_size_fresh(c->sd_path, (int64_t)st.st_size);
    }
    c->sd_every = (c->b->sd_every == 0) ? AZH_SD_EVERY_DEFAULT : c->b->sd_every;
    c->sd_on = 1;
    return azh__match_init(&c->sd, c->b->sd_text, from) == AZH_OK ? AZH_OK :
           azh_fail(AZH_E_ARG, "azh_run: bad sd_text");
}

static int batch_init(batch_t *c, const int32_t *in, int32_t n, const azh_batch *b, azh_result *out)
{
    int32_t i;

    memset(c, 0, sizeof *c);
    c->b = b;
    c->out = out;
    c->in = in;
    c->n_in = n;
    c->lo = 0x7fffffff;
    c->t0 = now_s();
    for (i = 0; i < b->n_shots; i++) {
        c->lo = (b->shots[i].frame < c->lo) ? b->shots[i].frame : c->lo;
        c->hi = (b->shots[i].frame > c->hi) ? b->shots[i].frame : c->hi;
    }
    if (b->sd_file[0] != '\0' && sd_start(c) != AZH_OK) {
        return AZH_E_ARG;
    }
    if (b->debug_text[0] != '\0') {
        azh__log_set_debug_stop(b->debug_text);
        c->debug_on = 1;
    }
    azh__watch_begin(b);
    return AZH_OK;
}

static void finish_message(azh_result *out)
{
    (void)snprintf(out->message, sizeof out->message, "%s", azh_msgs.first);
}

/* the stop that holds after frame i, in priority order; AZH_STOP_FRAMES is returned only on the last frame */
static int stop_after(batch_t *c, int32_t i, int *sd_error)
{
    const azh_batch *b = c->b;
    int found;

    if (azh_msgs.exited != 0) {
        return AZH_STOP_GUEST_EXITED;
    }
    if (azh_msgs.err != 0) {
        return AZH_STOP_GUEST_ERROR;
    }
    if (azh_msgs.brk != 0) {
        return AZH_STOP_GUEST_BREAK;
    }
    if (c->debug_on != 0 && azh__log_debug_hit() != 0) {
        return AZH_STOP_DEBUG_TEXT;
    }
    if (c->sd_on != 0 && (i % c->sd_every == 0 || i == b->frames)) {
        found = azh__match_poll_file(&c->sd, c->sd_path);
        if (found < 0) {
            *sd_error = found;
        } else if (found > 0) {
            return AZH_STOP_SD_TEXT;
        }
    }
    if (b->wall_limit_ms > 0 && (now_s() - c->t0) * 1000.0 >= (double)b->wall_limit_ms) {
        return AZH_STOP_WALL_LIMIT;
    }
    return (i == b->frames) ? AZH_STOP_FRAMES : -1;
}

/* once per process, at the first batch: the PNG level in use (png.c stays pure, so the log line is here) */
static void log_png_level_once(void)
{
    static int logged;
    const char *bad;

    if (logged != 0) {
        return;
    }
    logged = 1;
    bad = azh_png_level_bad();
    if (bad != NULL) {
        azh_log(AZH_LOG_INFO, "png level=%d (bad LAZ_PNG_LEVEL \"%s\", using 1)", azh_png_level(), bad);
    } else {
        azh_log(AZH_LOG_INFO, "png level=%d", azh_png_level());
    }
}

static const char *stop_name(int reason)
{
    static const char *const names[] = { "frames", "sd_text", "debug_text", "guest_break", "guest_exited",
                                         "guest_error", "wall_limit" };

    return (reason >= 0 && reason < (int)(sizeof names / sizeof names[0])) ? names[reason] : "unknown";
}

/* the batch timing line: core_ms is the retro_run walls (the core's callbacks run inside it), host_ms the rest */
static void log_batch_timing(const batch_t *c)
{
    int64_t wall_ns = (int64_t)(c->out->wall_s * 1e9);

    azh_log(AZH_LOG_INFO, "batch frames=%d wall_ms=%.3f core_ms=%.3f host_ms=%.3f shot_ms=%.3f stop=%s",
            (int)c->out->frames_run, (double)wall_ns / 1e6, (double)c->core_ns / 1e6,
            (double)(wall_ns - c->core_ns) / 1e6, (double)c->shot_ns / 1e6, stop_name(c->out->stop_reason));
}

static int run_frames(batch_t *c)
{
    const azh_batch *b = c->b;
    int64_t v0 = azh__vblanks_total();
    int32_t i;
    int rc = AZH_OK;
    int sd_error = 0;
    int stop = -1;
    int64_t t_shot;
    int64_t run_ns = 0;

    c->out->first_frame = azh_g.abs_frames + 1;
    for (i = 1; i <= b->frames && stop < 0 && rc == AZH_OK && sd_error == 0; i++) {
        apply_inputs(c, i);
        rc = azh__run_one_frame(&run_ns);
        c->core_ns += run_ns;
        c->out->frames_run = i;
        c->out->vblanks = azh__vblanks_total() - v0;
        if (rc == AZH_OK) {
            azh__watch_row(b, i);
        }
        if (rc == AZH_OK && i >= c->lo && i <= c->hi) {
            t_shot = now_ns();
            rc = take_shots(b, i, &c->out->shots_done);
            c->shot_ns += now_ns() - t_shot;
        }
        if (rc == AZH_OK) {
            stop = stop_after(c, i, &sd_error);
        }
    }
    if (rc == AZH_OK && sd_error < 0) {
        rc = azh_fail(AZH_E_IO, "azh_run: cannot read the SD file %s", c->sd_path);
    }
    c->out->stop_reason = (stop < 0) ? AZH_STOP_FRAMES : stop;
    if (rc == AZH_OK) {
        azh__watch_finish(b, (int32_t)c->out->frames_run, c->out);
    }
    return rc;
}

int azh_run_batch_inputs(const int32_t *inputs, int32_t n, const azh_batch *b, azh_result *out)
{
    batch_t c;
    int rc;

    assert(b != NULL && out != NULL);
    assert(b->frames >= 1 && b->n_shots >= 0 && b->n_shots <= AZH_MAX_SHOTS);
    out->shots_done = 0;
    log_png_level_once();
    rc = batch_init(&c, inputs, n, b, out);
    if (rc != AZH_OK) {
        return rc;
    }
    rc = run_frames(&c);
    azh__log_set_debug_stop(NULL);
    out->last_frame = azh_g.abs_frames;
    if (out->stop_reason >= AZH_STOP_GUEST_BREAK && out->stop_reason <= AZH_STOP_GUEST_ERROR) {
        finish_message(out);
    }
    azh_map_set_stop(out->stop_reason);
    out->wall_s = now_s() - c.t0;
    if (rc == AZH_OK) {
        log_batch_timing(&c);
    }
    return rc;
}

int azh_run_batch(const azh_batch *b, azh_result *out)
{
    return azh_run_batch_inputs(NULL, 0, b, out);
}
