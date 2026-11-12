/* api.c: the azh_* functions: call-order checks, parameter checks, error text, setup and teardown. */
#include <assert.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <time.h>

#include "azh_internal.h"

azh_state azh_g;                    /* the one state struct */
static char err_text[512];
static int opened_once;           /* one azh_open per process: the core and MoltenVK stay mapped after close */

int azh_fail(int code, const char *fmt, ...)
{
    va_list ap;

    assert(sizeof err_text > 1);
    assert(code < 0 && fmt != NULL);
    va_start(ap, fmt);
    (void)vsnprintf(err_text, sizeof err_text, fmt, ap);
    va_end(ap);
    azh_log(AZH_LOG_ERROR, "%s", err_text);
    return code;
}

const char *azh_error(void)
{
    return err_text;
}

static double mono_s(void)
{
    struct timespec t;

    (void)clock_gettime(CLOCK_MONOTONIC, &t);
    assert(t.tv_nsec >= 0 && t.tv_nsec < 1000000000L);
    assert(t.tv_sec >= 0);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

int azh_abi_layout(azh_layout *out)
{
    if (out == NULL) {
        return azh_fail(AZH_E_ARG, "azh_abi_layout: out is NULL");
    }
    out->abi = AZH_ABI_VERSION;
    out->size_batch = (uint32_t)sizeof(azh_batch);
    out->size_result = (uint32_t)sizeof(azh_result);
    out->size_stats = (uint32_t)sizeof(struct azh_stats);
    out->size_layout = (uint32_t)sizeof(azh_layout);
    out->map_size = AZH_MAP_SIZE;
    out->map_px_off = AZH_MAP_HEADER;
    out->map_px_size = AZH_MAP_PX_SIZE;
    out->off_heartbeat = AZH_MAP_OFF_HEARTBEAT;
    out->off_stop = AZH_MAP_OFF_STOP;
    out->off_msg = AZH_MAP_OFF_MSG;
    out->off_px_frame = AZH_MAP_OFF_PXFRAME;
    assert(out->size_layout == sizeof(azh_layout) && out->map_size == AZH_MAP_HEADER + out->map_px_size);
    return AZH_OK;
}

/* undo whatever open or boot set up; safe in any phase and when called twice */
static void teardown(void)
{
    assert(azh_g.n_opts >= 0 && azh_g.n_opts <= AZH_MAX_OPTS);
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    azh_core_close();
    azh_vk_close();
    azh_frame_free();
    azh_opts_free();
    if (azh_g.vk.qmx_ready != 0) {
        (void)pthread_mutex_destroy(&azh_g.vk.qmx);
    }
    azh_map_close();
    azh_log_close();
    memset(&azh_g, 0, sizeof azh_g);
}

int azh_close(void)
{
    teardown();
    return AZH_OK;
}

static int check_paths(const char *core, const char *sysdir, const char *log, const char *mapfile)
{
    struct stat st;

    assert(AZH_PATH_MAX > 1);
    if (core == NULL || sysdir == NULL || log == NULL || mapfile == NULL) {
        return azh_fail(AZH_E_ARG, "azh_open: a NULL argument");
    }
    if (strlen(core) >= AZH_PATH_MAX || strlen(sysdir) >= AZH_PATH_MAX) {
        return azh_fail(AZH_E_ARG, "azh_open: path too long");
    }
    if (stat(sysdir, &st) != 0 || !S_ISDIR(st.st_mode)) {
        return azh_fail(AZH_E_IO, "system directory %s does not exist", sysdir);
    }
    return AZH_OK;
}

/* open the files, then the core; the callbacks go in with the option store and sysdir already live */
static int open_steps(const char *core, const char *log, const char *mapfile)
{
    const char *lvl;
    int rc;

    assert(core != NULL && log != NULL && mapfile != NULL);
    assert(azh_g.phase == AZH_PH_NONE);
    /* set before any core thread exists (setenv is not thread-safe); a caller's own value wins */
    (void)setenv("MVK_CONFIG_LOG_LEVEL", "1", 0);
    if (azh_log_open(log) != 0) {
        return azh_fail(AZH_E_IO, "cannot open log %s", log);
    }
    if (azh_map_create(mapfile) != 0) {
        return azh_fail(AZH_E_IO, "cannot create map %s", mapfile);
    }
    lvl = getenv("MVK_CONFIG_LOG_LEVEL");
    azh_log(AZH_LOG_INFO, "MoltenVK log level %s (default 1; set MVK_CONFIG_LOG_LEVEL to change)",
            lvl != NULL ? lvl : "?");
    rc = azh_core_open(core);
    if (rc != AZH_OK) {
        return rc;
    }
    azh_core_install_callbacks();
    azh_g.core.init();
    azh_g.core_inited = 1;
    return AZH_OK;
}

int azh_open(const char *core, const char *sysdir, const char *log, const char *mapfile)
{
    int rc;

    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_NONE || opened_once != 0) {
        return azh_fail(AZH_E_ORDER, "azh_open: one open per process (the core and MoltenVK stay mapped)");
    }
    rc = check_paths(core, sysdir, log, mapfile);
    if (rc != AZH_OK) {
        return rc;
    }
    memset(&azh_g, 0, sizeof azh_g);
    snprintf(azh_g.core_path, sizeof azh_g.core_path, "%s", core);
    snprintf(azh_g.sysdir, sizeof azh_g.sysdir, "%s", sysdir);
    azh_png_init();
    if (pthread_mutex_init(&azh_g.vk.qmx, NULL) != 0) {
        return azh_fail(AZH_E_NOMEM, "cannot create the queue mutex");
    }
    azh_g.vk.qmx_ready = 1;
    rc = open_steps(core, log, mapfile);
    if (rc != AZH_OK) {
        teardown();
        return rc;
    }
    azh_g.phase = AZH_PH_OPEN;
    opened_once = 1;
    return AZH_OK;
}

int azh_set_option(const char *key, const char *value)
{
    assert(azh_g.n_opts >= 0 && azh_g.n_opts <= AZH_MAX_OPTS);
    if (azh_g.phase != AZH_PH_OPEN) {
        return azh_fail(AZH_E_ORDER, "azh_set_option: only after azh_open and before azh_boot");
    }
    if (key == NULL || value == NULL) {
        return azh_fail(AZH_E_ARG, "azh_set_option: NULL key or value");
    }
    return azh_opts_set(key, value);
}

static int boot_game(const char *app)
{
    struct retro_game_info gi;
    int rc;

    assert(app != NULL);
    assert(azh_g.phase == AZH_PH_OPEN && azh_g.core.load_game != NULL);
    memset(&gi, 0, sizeof gi);
    gi.path = app;
    azh_g.last_msg[0] = '\0';
    if (!azh_g.core.load_game(&gi)) {
        return azh_fail(AZH_E_BOOT, "%s", azh_g.last_msg[0] != '\0' ? azh_g.last_msg : "retro_load_game failed");
    }
    azh_g.game_loaded = 1;
    azh_g.core.get_system_av_info(&azh_g.av);
    azh_log(AZH_LOG_INFO, "av info base %ux%u max %ux%u fps %.3f", azh_g.av.geometry.base_width,
            azh_g.av.geometry.base_height, azh_g.av.geometry.max_width, azh_g.av.geometry.max_height,
            azh_g.av.timing.fps);
    if (azh_g.have_hw == 0 || azh_g.hw.context_reset == NULL) {
        return azh_fail(AZH_E_CORE, "the core did not ask for a Vulkan render context");
    }
    rc = azh_vk_init();
    if (rc != AZH_OK) {
        return rc;
    }
    azh_g.in_reset = 1;
    azh_g.boot_failed = 0;
    azh_g.hw.context_reset();       /* the core's Vulkan setup and System::Load run here */
    azh_g.in_reset = 0;
    if (azh_g.boot_failed != 0) {
        return azh_fail(AZH_E_BOOT, "%s", azh_g.last_msg);
    }
    return AZH_OK;
}

int azh_boot(const char *app, const char *state_or_null)
{
    int rc;

    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_OPEN) {
        return azh_fail(AZH_E_ORDER, "azh_boot: needs azh_open first and runs once");
    }
    if (app == NULL || *app == '\0') {
        return azh_fail(AZH_E_ARG, "azh_boot: no app path");
    }
    if (state_or_null != NULL) {
        return azh_fail(AZH_E_UNSUPPORTED, "booting from a savestate arrives in step D");
    }
    azh_opts_log();
    azh_log(AZH_LOG_INFO, "boot %s with core %s %s", app, azh_g.core_name, azh_g.core_version);
    rc = boot_game(app);
    if (rc != AZH_OK) {
        azh_g.phase = AZH_PH_DEAD;
        return rc;
    }
    azh_g.t_boot = mono_s();
    azh_g.phase = AZH_PH_BOOTED;
    return AZH_OK;
}

/* batch parameter checks: everything the stop rules of step C would use must still be empty */
static int check_batch(const azh_batch *b)
{
    int32_t i;

    assert(b != NULL);
    assert(AZH_MAX_SHOTS > 0);
    if (b->frames < 1 || b->frames > 100000000) {
        return azh_fail(AZH_E_ARG, "azh_run: frames must be 1 to 100,000,000");
    }
    if (b->n_shots < 0 || b->n_shots > AZH_MAX_SHOTS) {
        return azh_fail(AZH_E_ARG, "azh_run: n_shots must be 0 to %d", AZH_MAX_SHOTS);
    }
    if (b->sd_file[0] != '\0' || b->sd_text[0] != '\0' || b->sd_every != 0 || b->debug_text[0] != '\0' ||
        b->wall_limit_ms != 0) {
        return azh_fail(AZH_E_UNSUPPORTED, "stop rules arrive in step C");
    }
    if (b->n_shots > 0 && memchr(b->shot_dir, '\0', sizeof b->shot_dir) == NULL) {
        return azh_fail(AZH_E_ARG, "azh_run: shot_dir is not terminated");
    }
    if (b->n_shots > 0 && b->shot_dir[0] == '\0') {
        return azh_fail(AZH_E_ARG, "azh_run: shots need a shot_dir");
    }
    for (i = 0; i < b->n_shots; i++) {
        if (b->shots[i].frame < 1 || b->shots[i].frame > b->frames) {
            return azh_fail(AZH_E_ARG, "azh_run: shot frame %d is outside 1..%d", b->shots[i].frame, b->frames);
        }
        if (b->shots[i].screens < AZH_SCREEN_TOP || b->shots[i].screens > AZH_SCREEN_BOTH) {
            return azh_fail(AZH_E_ARG, "azh_run: shot screens must be 1, 2 or 3");
        }
        if (b->shots[i].format != AZH_FMT_PNG) {
            return azh_fail(AZH_E_UNSUPPORTED, "raw shots arrive in step C");
        }
    }
    return AZH_OK;
}

int azh_run(const int32_t *inputs, int32_t n, const azh_batch *b, azh_result *out)
{
    int rc;

    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    (void)inputs;     /* only n == 0 is accepted until step C */
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_run: needs a successful azh_boot");
    }
    if (b == NULL || out == NULL || n < 0) {
        return azh_fail(AZH_E_ARG, "azh_run: NULL batch or result, or negative n");
    }
    if (n > 0) {
        return azh_fail(AZH_E_UNSUPPORTED, "input records arrive in step C");
    }
    rc = check_batch(b);
    if (rc != AZH_OK) {
        return rc;
    }
    memset(out, 0, sizeof *out);
    return azh_run_batch(b, out);
}

int azh_shot(int32_t screens, int32_t format, const char *path_prefix)
{
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_shot: needs a successful azh_boot");
    }
    if (screens < AZH_SCREEN_TOP || screens > AZH_SCREEN_BOTH || path_prefix == NULL) {
        return azh_fail(AZH_E_ARG, "azh_shot: screens must be 1, 2 or 3 and a prefix is required");
    }
    if (format != AZH_FMT_PNG) {
        return azh_fail(AZH_E_UNSUPPORTED, "raw shots arrive in step C");
    }
    return azh_frame_write(screens, path_prefix);
}

int azh_save_state(const char *path, int32_t *k_out)
{
    (void)path;
    (void)k_out;
    return azh_fail(AZH_E_UNSUPPORTED, "savestates arrive in step D");
}

int azh_load_state(const char *path)
{
    (void)path;
    return azh_fail(AZH_E_UNSUPPORTED, "savestates arrive in step D");
}

/* memory access needs our patched core; the stock core says so */
static int memory_gate(void)
{
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase == AZH_PH_NONE) {
        return azh_fail(AZH_E_ORDER, "memory access needs azh_open first");
    }
    if (azh_g.is_lazpy == 0) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "guest memory access needs the libazahar core (this core is stock)");
    }
    return azh_fail(AZH_E_UNSUPPORTED, "guest memory access arrives in step G");
}

int azh_read(uint32_t addr, uint32_t len, void *buf)
{
    (void)addr;
    (void)len;
    (void)buf;
    return memory_gate();
}

int azh_write(uint32_t addr, uint32_t len, const void *buf)
{
    (void)addr;
    (void)len;
    (void)buf;
    return memory_gate();
}

int azh_set_input(const int32_t rec[AZH_INPUT_INTS])
{
    (void)rec;
    return azh_fail(AZH_E_UNSUPPORTED, "inputs arrive in step C");
}

int azh_stats(struct azh_stats *out)
{
    struct rusage ru;

    assert(azh_g.abs_frames >= 0);
    if (azh_g.phase == AZH_PH_NONE) {
        return azh_fail(AZH_E_ORDER, "azh_stats: needs azh_open first");
    }
    if (out == NULL) {
        return azh_fail(AZH_E_ARG, "azh_stats: out is NULL");
    }
    memset(out, 0, sizeof *out);
    if (getrusage(RUSAGE_SELF, &ru) != 0) {
        return azh_fail(AZH_E_IO, "getrusage failed");
    }
    out->frames = azh_g.abs_frames;
    out->wall_s = (azh_g.t_boot > 0.0) ? mono_s() - azh_g.t_boot : 0.0;
    out->user_s = (double)ru.ru_utime.tv_sec + (double)ru.ru_utime.tv_usec * 1e-6;
    out->sys_s = (double)ru.ru_stime.tv_sec + (double)ru.ru_stime.tv_usec * 1e-6;
    out->peak_rss = (int64_t)ru.ru_maxrss;       /* bytes on macOS */
    snprintf(out->core_name, sizeof out->core_name, "%s", azh_g.core_name);
    snprintf(out->core_version, sizeof out->core_version, "%s", azh_g.core_version);
    out->is_lazpy_core = azh_g.is_lazpy;
    return AZH_OK;
}
