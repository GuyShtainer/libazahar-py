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

/* the layout table (docs/plans/phase-c.md 3.2): one row per line, the single source of every offset and constant */
static const struct { const char *name; int32_t offset; int32_t size; } field_rows[] = {
    { "shot.frame", offsetof(azh_shot_req, frame), sizeof(((azh_shot_req *)0)->frame) },
    { "shot.screens", offsetof(azh_shot_req, screens), sizeof(((azh_shot_req *)0)->screens) },
    { "shot.format", offsetof(azh_shot_req, format), sizeof(((azh_shot_req *)0)->format) },
    { "shot.__size__", 0, sizeof(azh_shot_req) },
    { "batch.frames", offsetof(azh_batch, frames), sizeof(((azh_batch *)0)->frames) },
    { "batch.n_shots", offsetof(azh_batch, n_shots), sizeof(((azh_batch *)0)->n_shots) },
    { "batch.shots", offsetof(azh_batch, shots), sizeof(((azh_batch *)0)->shots) },
    { "batch.shot_dir", offsetof(azh_batch, shot_dir), sizeof(((azh_batch *)0)->shot_dir) },
    { "batch.sd_file", offsetof(azh_batch, sd_file), sizeof(((azh_batch *)0)->sd_file) },
    { "batch.sd_text", offsetof(azh_batch, sd_text), sizeof(((azh_batch *)0)->sd_text) },
    { "batch.sd_every", offsetof(azh_batch, sd_every), sizeof(((azh_batch *)0)->sd_every) },
    { "batch.debug_text", offsetof(azh_batch, debug_text), sizeof(((azh_batch *)0)->debug_text) },
    { "batch.wall_limit_ms", offsetof(azh_batch, wall_limit_ms), sizeof(((azh_batch *)0)->wall_limit_ms) },
    { "batch.sd_from_end", offsetof(azh_batch, sd_from_end), sizeof(((azh_batch *)0)->sd_from_end) },
    { "batch.n_watch", offsetof(azh_batch, n_watch), sizeof(((azh_batch *)0)->n_watch) },
    { "batch.watch_every", offsetof(azh_batch, watch_every), sizeof(((azh_batch *)0)->watch_every) },
    { "batch.watch", offsetof(azh_batch, watch), sizeof(((azh_batch *)0)->watch) },
    { "watch.addr", offsetof(azh_watch, addr), sizeof(((azh_watch *)0)->addr) },
    { "watch.words", offsetof(azh_watch, words), sizeof(((azh_watch *)0)->words) },
    { "watch.__size__", 0, sizeof(azh_watch) },
    { "batch.__size__", 0, sizeof(azh_batch) },
    { "result.frames_run", offsetof(azh_result, frames_run), sizeof(((azh_result *)0)->frames_run) },
    { "result.first_frame", offsetof(azh_result, first_frame), sizeof(((azh_result *)0)->first_frame) },
    { "result.last_frame", offsetof(azh_result, last_frame), sizeof(((azh_result *)0)->last_frame) },
    { "result.stop_reason", offsetof(azh_result, stop_reason), sizeof(((azh_result *)0)->stop_reason) },
    { "result.shots_done", offsetof(azh_result, shots_done), sizeof(((azh_result *)0)->shots_done) },
    { "result.wall_s", offsetof(azh_result, wall_s), sizeof(((azh_result *)0)->wall_s) },
    { "result.vblanks", offsetof(azh_result, vblanks), sizeof(((azh_result *)0)->vblanks) },
    { "result.message", offsetof(azh_result, message), sizeof(((azh_result *)0)->message) },
    { "result.watch_rows", offsetof(azh_result, watch_rows), sizeof(((azh_result *)0)->watch_rows) },
    { "result.watch_status", offsetof(azh_result, watch_status), sizeof(((azh_result *)0)->watch_status) },
    { "result.__size__", 0, sizeof(azh_result) },
    { "stats.frames", offsetof(struct azh_stats, frames), sizeof(((struct azh_stats *)0)->frames) },
    { "stats.wall_s", offsetof(struct azh_stats, wall_s), sizeof(((struct azh_stats *)0)->wall_s) },
    { "stats.user_s", offsetof(struct azh_stats, user_s), sizeof(((struct azh_stats *)0)->user_s) },
    { "stats.sys_s", offsetof(struct azh_stats, sys_s), sizeof(((struct azh_stats *)0)->sys_s) },
    { "stats.peak_rss", offsetof(struct azh_stats, peak_rss), sizeof(((struct azh_stats *)0)->peak_rss) },
    { "stats.core_name", offsetof(struct azh_stats, core_name), sizeof(((struct azh_stats *)0)->core_name) },
    { "stats.core_version", offsetof(struct azh_stats, core_version), sizeof(((struct azh_stats *)0)->core_version) },
    { "stats.is_lazpy_core", offsetof(struct azh_stats, is_lazpy_core), sizeof(((struct azh_stats *)0)->is_lazpy_core) },
    { "stats.__size__", 0, sizeof(struct azh_stats) },
    { "thread.tid", offsetof(azh_thread, tid), sizeof(((azh_thread *)0)->tid) },
    { "thread.pid", offsetof(azh_thread, pid), sizeof(((azh_thread *)0)->pid) },
    { "thread.status", offsetof(azh_thread, status), sizeof(((azh_thread *)0)->status) },
    { "thread.core", offsetof(azh_thread, core), sizeof(((azh_thread *)0)->core) },
    { "thread.priority", offsetof(azh_thread, priority), sizeof(((azh_thread *)0)->priority) },
    { "thread.flags", offsetof(azh_thread, flags), sizeof(((azh_thread *)0)->flags) },
    { "thread.pc", offsetof(azh_thread, pc), sizeof(((azh_thread *)0)->pc) },
    { "thread.lr", offsetof(azh_thread, lr), sizeof(((azh_thread *)0)->lr) },
    { "thread.sp", offsetof(azh_thread, sp), sizeof(((azh_thread *)0)->sp) },
    { "thread.cpsr", offsetof(azh_thread, cpsr), sizeof(((azh_thread *)0)->cpsr) },
    { "thread.__size__", 0, sizeof(azh_thread) },
    { "layout.abi", offsetof(azh_layout, abi), sizeof(((azh_layout *)0)->abi) },
    { "layout.size_batch", offsetof(azh_layout, size_batch), sizeof(((azh_layout *)0)->size_batch) },
    { "layout.size_result", offsetof(azh_layout, size_result), sizeof(((azh_layout *)0)->size_result) },
    { "layout.size_stats", offsetof(azh_layout, size_stats), sizeof(((azh_layout *)0)->size_stats) },
    { "layout.size_layout", offsetof(azh_layout, size_layout), sizeof(((azh_layout *)0)->size_layout) },
    { "layout.map_size", offsetof(azh_layout, map_size), sizeof(((azh_layout *)0)->map_size) },
    { "layout.map_px_off", offsetof(azh_layout, map_px_off), sizeof(((azh_layout *)0)->map_px_off) },
    { "layout.map_px_size", offsetof(azh_layout, map_px_size), sizeof(((azh_layout *)0)->map_px_size) },
    { "layout.off_heartbeat", offsetof(azh_layout, off_heartbeat), sizeof(((azh_layout *)0)->off_heartbeat) },
    { "layout.off_stop", offsetof(azh_layout, off_stop), sizeof(((azh_layout *)0)->off_stop) },
    { "layout.off_msg", offsetof(azh_layout, off_msg), sizeof(((azh_layout *)0)->off_msg) },
    { "layout.off_px_frame", offsetof(azh_layout, off_px_frame), sizeof(((azh_layout *)0)->off_px_frame) },
    { "layout.n_fields", offsetof(azh_layout, n_fields), sizeof(((azh_layout *)0)->n_fields) },
    { "layout.fields", offsetof(azh_layout, fields), sizeof(((azh_layout *)0)->fields) },
    { "layout.__size__", 0, sizeof(azh_layout) },
    { "map.magic", 0, 8 },
    { "map.version", 8, 4 },
    { "map.header_size", 12, 4 },
    { "map.heartbeat", AZH_MAP_OFF_HEARTBEAT, 8 },
    { "map.stop_code", AZH_MAP_OFF_STOP, 4 },
    { "map.msg_len", AZH_MAP_OFF_MSGLEN, 4 },
    { "map.message", AZH_MAP_OFF_MSG, AZH_MAP_MSG_MAX },
    { "map.dims", AZH_MAP_OFF_SIZES, 16 },
    { "map.px_frame", AZH_MAP_OFF_PXFRAME, 8 },
    { "map.frame_total", AZH_MAP_OFF_FRAME_TOTAL, 8 },
    { "map.vblanks_total", AZH_MAP_OFF_VBLANKS_TOTAL, 8 },
    { "map.msg_seq", AZH_MAP_OFF_MSG_SEQ, 4 },
    { "map.pid", AZH_MAP_OFF_PID, 4 },
    { "map.exit_code", AZH_MAP_OFF_EXIT_CODE, 4 },
    { "map.pixels", AZH_MAP_HEADER, AZH_MAP_PX_SIZE },
    { "map.watch_rows", AZH_MAP_OFF_WATCH_ROWS, 4 },
    { "map.watch_row_bytes", AZH_MAP_OFF_WATCH_ROW_BYTES, 4 },
    { "map.watch_words", AZH_MAP_OFF_WATCH_WORDS, 4 },
    { "map.watch_seq", AZH_MAP_OFF_WATCH_SEQ, 4 },
    { "map.watch_first", AZH_MAP_OFF_WATCH_FIRST, 8 },
    { "map.watch_data", AZH_MAP_OFF_WATCH_DATA, AZH_WATCH_AREA_BYTES - AZH_WATCH_HDR_BYTES },
    { "map.__size__", 0, AZH_MAP_SIZE },
    { "const.AZH_OK", (int32_t)AZH_OK, 0 },
    { "const.AZH_E_ARG", (int32_t)AZH_E_ARG, 0 },
    { "const.AZH_E_ORDER", (int32_t)AZH_E_ORDER, 0 },
    { "const.AZH_E_CORE", (int32_t)AZH_E_CORE, 0 },
    { "const.AZH_E_BOOT", (int32_t)AZH_E_BOOT, 0 },
    { "const.AZH_E_VULKAN", (int32_t)AZH_E_VULKAN, 0 },
    { "const.AZH_E_IO", (int32_t)AZH_E_IO, 0 },
    { "const.AZH_E_NOMEM", (int32_t)AZH_E_NOMEM, 0 },
    { "const.AZH_E_UNSUPPORTED", (int32_t)AZH_E_UNSUPPORTED, 0 },
    { "const.AZH_E_NEEDS_LAZPY_CORE", (int32_t)AZH_E_NEEDS_LAZPY_CORE, 0 },
    { "const.AZH_E_SAVESTATE", (int32_t)AZH_E_SAVESTATE, 0 },
    { "const.AZH_E_UNMAPPED", (int32_t)AZH_E_UNMAPPED, 0 },
    { "const.AZH_EXIT_OK", (int32_t)AZH_EXIT_OK, 0 },
    { "const.AZH_EXIT_USAGE", (int32_t)AZH_EXIT_USAGE, 0 },
    { "const.AZH_EXIT_BOOT", (int32_t)AZH_EXIT_BOOT, 0 },
    { "const.AZH_EXIT_CORE", (int32_t)AZH_EXIT_CORE, 0 },
    { "const.AZH_EXIT_VULKAN", (int32_t)AZH_EXIT_VULKAN, 0 },
    { "const.AZH_EXIT_IO", (int32_t)AZH_EXIT_IO, 0 },
    { "const.AZH_EXIT_NEEDS_LAZPY", (int32_t)AZH_EXIT_NEEDS_LAZPY, 0 },
    { "const.AZH_EXIT_UNSUPPORTED", (int32_t)AZH_EXIT_UNSUPPORTED, 0 },
    { "const.AZH_EXIT_GUEST_EXITED", (int32_t)AZH_EXIT_GUEST_EXITED, 0 },
    { "const.AZH_EXIT_GUEST_ERROR", (int32_t)AZH_EXIT_GUEST_ERROR, 0 },
    { "const.AZH_SCREEN_TOP", (int32_t)AZH_SCREEN_TOP, 0 },
    { "const.AZH_SCREEN_BOTTOM", (int32_t)AZH_SCREEN_BOTTOM, 0 },
    { "const.AZH_SCREEN_BOTH", (int32_t)AZH_SCREEN_BOTH, 0 },
    { "const.AZH_FMT_PNG", (int32_t)AZH_FMT_PNG, 0 },
    { "const.AZH_FMT_RAW", (int32_t)AZH_FMT_RAW, 0 },
    { "const.AZH_STOP_FRAMES", (int32_t)AZH_STOP_FRAMES, 0 },
    { "const.AZH_STOP_SD_TEXT", (int32_t)AZH_STOP_SD_TEXT, 0 },
    { "const.AZH_STOP_DEBUG_TEXT", (int32_t)AZH_STOP_DEBUG_TEXT, 0 },
    { "const.AZH_STOP_GUEST_BREAK", (int32_t)AZH_STOP_GUEST_BREAK, 0 },
    { "const.AZH_STOP_GUEST_EXITED", (int32_t)AZH_STOP_GUEST_EXITED, 0 },
    { "const.AZH_STOP_GUEST_ERROR", (int32_t)AZH_STOP_GUEST_ERROR, 0 },
    { "const.AZH_STOP_WALL_LIMIT", (int32_t)AZH_STOP_WALL_LIMIT, 0 },
    { "const.AZH_ABI_VERSION", (int32_t)AZH_ABI_VERSION, 0 },
    { "const.AZH_STATE_META_ABI", (int32_t)AZH_STATE_META_ABI, 0 },
    { "const.AZH_THREAD_CURRENT", (int32_t)AZH_THREAD_CURRENT, 0 },
    { "const.AZH_MAX_SHOTS", (int32_t)AZH_MAX_SHOTS, 0 },
    { "const.AZH_PATH_MAX", (int32_t)AZH_PATH_MAX, 0 },
    { "const.AZH_INPUT_INTS", (int32_t)AZH_INPUT_INTS, 0 },
    { "const.AZH_IN_FRAME", (int32_t)AZH_IN_FRAME, 0 },
    { "const.AZH_IN_BUTTONS", (int32_t)AZH_IN_BUTTONS, 0 },
    { "const.AZH_IN_TOUCH_X", (int32_t)AZH_IN_TOUCH_X, 0 },
    { "const.AZH_IN_TOUCH_Y", (int32_t)AZH_IN_TOUCH_Y, 0 },
    { "const.AZH_IN_TOUCH_DOWN", (int32_t)AZH_IN_TOUCH_DOWN, 0 },
    { "const.AZH_IN_CIRCLE_X", (int32_t)AZH_IN_CIRCLE_X, 0 },
    { "const.AZH_IN_CIRCLE_Y", (int32_t)AZH_IN_CIRCLE_Y, 0 },
    { "const.AZH_MAX_INPUTS", (int32_t)AZH_MAX_INPUTS, 0 },
    { "const.AZH_BUTTONS_MASK", (int32_t)AZH_BUTTONS_MASK, 0 },
    { "const.AZH_CIRCLE_MAX", (int32_t)AZH_CIRCLE_MAX, 0 },
    { "const.AZH_SD_EVERY_DEFAULT", (int32_t)AZH_SD_EVERY_DEFAULT, 0 },
    { "const.AZH_MSG_MAX", (int32_t)AZH_MSG_MAX, 0 },
    { "const.AZH_MAX_FIELDS", (int32_t)AZH_MAX_FIELDS, 0 },
    { "const.AZH_MEM_MAX_LEN", (int32_t)AZH_MEM_MAX_LEN, 0 },
    { "const.AZH_MAX_WATCH", (int32_t)AZH_MAX_WATCH, 0 },
    { "const.AZH_WATCH_MAX_WORDS", (int32_t)AZH_WATCH_MAX_WORDS, 0 },
    { "const.AZH_WATCH_EVERY_MAX", (int32_t)AZH_WATCH_EVERY_MAX, 0 },
    { "const.AZH_WATCH_AREA_OFF", (int32_t)AZH_WATCH_AREA_OFF, 0 },
    { "const.AZH_WATCH_AREA_BYTES", (int32_t)AZH_WATCH_AREA_BYTES, 0 },
    { "const.AZH_WATCH_HDR_BYTES", (int32_t)AZH_WATCH_HDR_BYTES, 0 },
    { "const.AZH_WATCH_ROW_HDR", (int32_t)AZH_WATCH_ROW_HDR, 0 },
};
#define FIELD_ROWS ((int32_t)(sizeof field_rows / sizeof field_rows[0]))
_Static_assert(sizeof field_rows / sizeof field_rows[0] <= AZH_MAX_FIELDS, "fields[] is too small for the table");

static void fill_fields(azh_layout *out)
{
    int32_t i;

    assert(out != NULL && FIELD_ROWS <= AZH_MAX_FIELDS);
    memset(out->fields, 0, sizeof out->fields);
    for (i = 0; i < FIELD_ROWS; i++) {
        assert(strlen(field_rows[i].name) < sizeof out->fields[i].name);
        (void)snprintf(out->fields[i].name, sizeof out->fields[i].name, "%s", field_rows[i].name);
        out->fields[i].offset = field_rows[i].offset;
        out->fields[i].size = field_rows[i].size;
    }
    out->n_fields = FIELD_ROWS;
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
    fill_fields(out);
    assert(out->size_layout == sizeof(azh_layout) && out->map_size == AZH_WATCH_AREA_OFF + AZH_WATCH_AREA_BYTES);
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
    azh__input_install();
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
    azh__state_note_app(app);
    azh_opts_log();
    azh_log(AZH_LOG_INFO, "boot %s with core %s %s", app, azh_g.core_name, azh_g.core_version);
    rc = boot_game(app);
    if (rc != AZH_OK) {
        azh_g.phase = AZH_PH_DEAD;
        return rc;
    }
    azh_g.t_boot = mono_s();
    azh_g.phase = AZH_PH_BOOTED;        /* before the state boot: its warm-up frame needs it */
    if (state_or_null != NULL) {
        rc = azh__state_boot(app, state_or_null);
        if (rc != AZH_OK) {
            azh_g.phase = AZH_PH_DEAD;
            return rc;
        }
    }
    return AZH_OK;
}

/* 1 when a path has a ".." component (a bare "..", or between slashes, or at either end) */
static int has_dotdot(const char *path)
{
    const char *p = path;

    assert(path != NULL);
    while (*p != '\0') {
        size_t n = strcspn(p, "/");

        if (n == 2u && p[0] == '.' && p[1] == '.') {
            return 1;
        }
        p += n;
        if (*p == '/') {
            p++;
        }
    }
    return 0;
}

/* the stop-rule fields: terminated strings, a relative SD path, ranges, the debug-text rules of the two cores */
static int check_stop_rules(const azh_batch *b)
{
    struct retro_variable var;

    assert(b != NULL);
    if (memchr(b->sd_file, '\0', sizeof b->sd_file) == NULL || memchr(b->sd_text, '\0', sizeof b->sd_text) == NULL ||
        memchr(b->debug_text, '\0', sizeof b->debug_text) == NULL) {
        return azh_fail(AZH_E_ARG, "azh_run: sd_file, sd_text or debug_text is not terminated");
    }
    if ((b->sd_file[0] != '\0') != (b->sd_text[0] != '\0')) {
        return azh_fail(AZH_E_ARG, "azh_run: sd_file and sd_text go together");
    }
    if (b->sd_file[0] == '/' || has_dotdot(b->sd_file)) {
        return azh_fail(AZH_E_ARG, "azh_run: sd_file must be relative to the SD folder, without ..");
    }
    if (b->sd_every < 0 || b->sd_every > 100000 || b->wall_limit_ms < 0 ||
        (b->sd_from_end != 0 && b->sd_from_end != 1)) {
        return azh_fail(AZH_E_ARG, "azh_run: sd_every 0..100000, wall_limit_ms >= 0, sd_from_end 0 or 1");
    }
    if (b->debug_text[0] == '\0') {
        return AZH_OK;
    }
    if (azh_g.is_lazpy == 0) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "a debug-text stop needs the libazahar core (this core is stock)");
    }
    memset(&var, 0, sizeof var);
    var.key = "citra_instant_debug_log";
    if (azh_opts_get(&var) == 0 || var.value == NULL || strcmp(var.value, "enabled") != 0) {
        return azh_fail(AZH_E_ARG, "azh_run: a debug-text stop needs the option citra_instant_debug_log=enabled");
    }
    return AZH_OK;
}

static int check_shots(const azh_batch *b)
{
    int32_t i;
    int png = 0;

    assert(b != NULL);
    if (b->n_shots < 0 || b->n_shots > AZH_MAX_SHOTS) {
        return azh_fail(AZH_E_ARG, "azh_run: n_shots must be 0 to %d", AZH_MAX_SHOTS);
    }
    for (i = 0; i < b->n_shots; i++) {
        if (b->shots[i].frame < 1 || b->shots[i].frame > b->frames) {
            return azh_fail(AZH_E_ARG, "azh_run: shot frame %d is outside 1..%d", b->shots[i].frame, b->frames);
        }
        if (b->shots[i].screens < AZH_SCREEN_TOP || b->shots[i].screens > AZH_SCREEN_BOTH) {
            return azh_fail(AZH_E_ARG, "azh_run: shot screens must be 1, 2 or 3");
        }
        if (b->shots[i].format != AZH_FMT_PNG && b->shots[i].format != AZH_FMT_RAW) {
            return azh_fail(AZH_E_ARG, "azh_run: shot format must be PNG (0) or RAW (1)");
        }
        png += (b->shots[i].format == AZH_FMT_PNG);
    }
    if (png > 0 && memchr(b->shot_dir, '\0', sizeof b->shot_dir) == NULL) {
        return azh_fail(AZH_E_ARG, "azh_run: shot_dir is not terminated");
    }
    if (png > 0 && b->shot_dir[0] == '\0') {
        return azh_fail(AZH_E_ARG, "azh_run: PNG shots need a shot_dir");
    }
    return AZH_OK;
}

static int check_batch(const azh_batch *b)
{
    int rc;

    assert(b != NULL);
    if (b->frames < 1 || b->frames > 100000000) {
        return azh_fail(AZH_E_ARG, "azh_run: frames must be 1 to 100,000,000");
    }
    if (check_shots(b) != AZH_OK) {
        return AZH_E_ARG;
    }
    rc = check_stop_rules(b);
    return (rc != AZH_OK) ? rc : azh__watch_check(b);
}

int azh_run(const int32_t *inputs, int32_t n, const azh_batch *b, azh_result *out)
{
    char err[200];
    int rc;

    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_run: needs a successful azh_boot");
    }
    if (b == NULL || out == NULL || n < 0) {
        return azh_fail(AZH_E_ARG, "azh_run: NULL batch or result, or negative n");
    }
    rc = check_batch(b);
    if (rc != AZH_OK) {
        return rc;
    }
    if (azh__input_validate(inputs, n, b->frames, err, sizeof err) != AZH_OK) {
        return azh_fail(AZH_E_ARG, "azh_run: %s", err);
    }
    memset(out, 0, sizeof *out);
    return azh_run_batch_inputs(inputs, n, b, out);
}

int azh_shot(int32_t screens, int32_t format, const char *path_prefix)
{
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_shot: needs a successful azh_boot");
    }
    if (screens < AZH_SCREEN_TOP || screens > AZH_SCREEN_BOTH) {
        return azh_fail(AZH_E_ARG, "azh_shot: screens must be 1, 2 or 3");
    }
    if (format == AZH_FMT_RAW) {
        return azh_run_raw_shot(screens);        /* the prefix is ignored */
    }
    if (format != AZH_FMT_PNG || path_prefix == NULL) {
        return azh_fail(AZH_E_ARG, "azh_shot: a PNG shot needs a prefix (format 0), or format 1 for raw");
    }
    return azh_frame_write(screens, path_prefix);
}

int azh_save_state(const char *path, int32_t *k_out)
{
    return azh__state_save(path, k_out);
}

int azh_load_state(const char *path)
{
    return azh__state_load(path);
}

/* the order and core checks of a memory call: after boot like azh_shot, and our core only */
static int memory_gate(const char *who)
{
    assert(who != NULL);
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "%s: needs a successful azh_boot", who);
    }
    if (azh_g.is_lazpy == 0) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "guest memory access needs the libazahar core (this core is stock)");
    }
    return AZH_OK;
}

int azh_read(uint32_t addr, uint32_t len, void *buf)
{
    int rc = memory_gate("azh_read");

    return (rc != AZH_OK) ? rc : azh__mem_read(addr, len, buf);
}

int azh_write(uint32_t addr, uint32_t len, const void *buf)
{
    int rc = memory_gate("azh_write");

    return (rc != AZH_OK) ? rc : azh__mem_write(addr, len, buf);
}

int azh_threads(azh_thread *out, int32_t max, int32_t *count)
{
    int rc = memory_gate("azh_threads");

    if (rc != AZH_OK && count != NULL) {
        *count = 0;
    }
    return (rc != AZH_OK) ? rc : azh__mem_threads(out, max, count);
}

int azh_set_input(const int32_t rec[AZH_INPUT_INTS])
{
    char err[200];
    int32_t one[AZH_INPUT_INTS];
    azh_held h;

    if (rec == NULL) {
        return azh_fail(AZH_E_ARG, "azh_set_input: NULL record");
    }
    memcpy(one, rec, sizeof one);
    one[AZH_IN_FRAME] = 1;          /* the frame field is ignored */
    if (azh__input_validate(one, 1, 1, err, sizeof err) != AZH_OK) {
        return azh_fail(AZH_E_ARG, "azh_set_input: %s", err);
    }
    azh__held_from_record(&h, one);
    azh__input_set(&h);
    return AZH_OK;
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
