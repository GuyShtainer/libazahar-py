/* env.c: the libretro environment callback. One switch; each id group goes to one small function.
 * The ids and answers are docs/plans/phase-a.md section 2's table. Names only, never numbers. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "azh_internal.h"

azh_msgstate azh_msgs;      /* the guest-message state of the current retro_run (run.c reads it) */

/* an id we do not know: answered false, logged once per id at debug */
static bool env_unknown(unsigned cmd)
{
    int i;

    for (i = 0; i < azh_g.n_seen; i++) {
        if (azh_g.seen[i] == cmd) {
            return false;
        }
    }
    if (azh_g.n_seen < AZH_SEEN_MAX) {
        azh_g.seen[azh_g.n_seen++] = cmd;
    }
    azh_log(AZH_LOG_DEBUG, "environment call %u not handled", cmd);
    return false;
}

static bool env_dirs(unsigned cmd, void *data)
{
    assert(data != NULL);
    if (cmd == RETRO_ENVIRONMENT_GET_LIBRETRO_PATH) {
        *(const char **)data = azh_g.core_path;
    } else {
        *(const char **)data = azh_g.sysdir;     /* system and save directory: the core adds Azahar/sdmc, /nand */
    }
    return true;
}

/* the host exits from inside the run (docs/plans/phase-c.md 3.5): the map first, one write(2) with no stdio and no
 * mutex (another thread may hold the log's), then _exit. The retro_run in progress is the frame that exited. */
static void exit_path(int stop_code, int exit_code)
{
    static const char line[] = "[error] the guest stopped the host; the host process exits now\n";
    int fd;

    assert(exit_code == AZH_EXIT_GUEST_EXITED || exit_code == AZH_EXIT_GUEST_ERROR);
    azh_map_set_stop(stop_code);
    azh_map_set_counters(azh_g.abs_frames + 1, azh__vblanks_total());
    azh_map_set_exit_code(exit_code);
    azh_map_sync();
    fd = azh__log_fd();
    if (fd >= 0) {
        (void)write(fd, line, sizeof line - 1u);     /* nowhere to report a failed log write */
    }
    _exit(exit_code);
}

/* one guest message, handed in full to the detector; only a booted host in a retro_run gets here */
static void on_guest_message(const char *text)
{
    int act;

    assert(text != NULL);
    act = azh__msg_on_message(&azh_msgs, text, azh_g.is_lazpy);
    if (act == AZH_ACT_EXIT_EXITED) {
        exit_path(AZH_STOP_GUEST_EXITED, AZH_EXIT_GUEST_EXITED);
    } else if (act == AZH_ACT_EXIT_ERROR) {
        exit_path(AZH_STOP_GUEST_ERROR, AZH_EXIT_GUEST_ERROR);
    }
}

static bool env_message(const void *data)
{
    const struct retro_message *m = data;
    const char *text;

    assert(data != NULL);
    text = (m->msg != NULL) ? m->msg : "";
    azh_log(AZH_LOG_WARN, "core message: %s", text);
    snprintf(azh_g.last_msg, sizeof azh_g.last_msg, "%s", text);
    azh_map_set_message(azh_g.last_msg);
    if (azh_g.in_reset != 0) {
        azh_g.boot_failed = 1;
    } else if (azh_g.phase == AZH_PH_BOOTED) {
        on_guest_message(text);
    }
    return true;
}

static bool env_variables(unsigned cmd, void *data)
{
    assert(data != NULL);
    if (cmd == RETRO_ENVIRONMENT_SET_VARIABLES) {
        azh_opts_register(data);
        return true;
    }
    return azh_opts_get(data) != 0;
}

static bool env_hw_render(void *data)
{
    const struct retro_hw_render_callback *r = data;

    assert(data != NULL);
    if (r->context_type != RETRO_HW_CONTEXT_VULKAN) {
        azh_log(AZH_LOG_WARN, "core asked for hardware context type %d; only Vulkan is served", (int)r->context_type);
        return false;
    }
    azh_g.hw = *r;     /* context_reset is how the host triggers System::Load */
    azh_g.have_hw = 1;
    return true;
}

static bool env_hw_negotiation(void *data)
{
    const struct retro_hw_render_context_negotiation_interface_vulkan *n = data;

    assert(data != NULL);
    if (n->interface_type != RETRO_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE_VULKAN) {
        return false;
    }
    azh_g.neg = *n;
    azh_g.have_neg = 1;
    return true;
}

static bool env_hw_interface(void *data)
{
    const struct retro_hw_render_interface_vulkan *iface = azh_vk_iface();

    assert(data != NULL);
    if (iface == NULL) {
        return false;
    }
    *(const struct retro_hw_render_interface_vulkan **)data = iface;
    return true;
}

static bool env_geometry(unsigned cmd, const void *data)
{
    assert(data != NULL);
    if (cmd == RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO) {
        azh_g.av = *(const struct retro_system_av_info *)data;
    } else {
        azh_g.av.geometry = *(const struct retro_game_geometry *)data;
    }
    azh_log(AZH_LOG_DEBUG, "geometry now %ux%u (max %ux%u)", azh_g.av.geometry.base_width,
            azh_g.av.geometry.base_height, azh_g.av.geometry.max_width, azh_g.av.geometry.max_height);
    return true;
}

static bool env_memory_maps(const void *data)
{
    const struct retro_memory_map *m = data;

    assert(data != NULL);
    if (azh_g.mm_logged == 0) {
        azh_g.mm_logged = 1;
        azh_log(AZH_LOG_INFO, "SET_MEMORY_MAPS: %u descriptors", m->num_descriptors);
    }
    return true;
}

/* calls that are accepted and ignored, or refused; the answer is the table's */
static bool env_simple(unsigned cmd, void *data)
{
    switch (cmd) {
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        ((struct retro_log_callback *)data)->log = azh_core_log;
        return true;
    case RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
        *(unsigned *)data = 0u;                    /* so the core registers V0 variables */
        return true;
    case RETRO_ENVIRONMENT_GET_PREFERRED_HW_RENDER:
        *(unsigned *)data = (unsigned)RETRO_HW_CONTEXT_VULKAN;
        return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        *(bool *)data = false;
        return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:
        *(bool *)data = true;
        return true;
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        return *(const enum retro_pixel_format *)data == RETRO_PIXEL_FORMAT_XRGB8888;
    default:
        return env_unknown(cmd);
    }
}

bool azh_env(unsigned cmd, void *data)
{
    switch (cmd) {
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_LIBRETRO_PATH:
        return env_dirs(cmd, data);
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_GET_VARIABLE:
        return env_variables(cmd, data);
    case RETRO_ENVIRONMENT_SET_MESSAGE:
        return env_message(data);
    case RETRO_ENVIRONMENT_SET_HW_RENDER:
        return env_hw_render(data);
    case RETRO_ENVIRONMENT_SET_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE:
        return env_hw_negotiation(data);
    case RETRO_ENVIRONMENT_GET_HW_RENDER_INTERFACE:
        return env_hw_interface(data);
    case RETRO_ENVIRONMENT_SET_GEOMETRY:
    case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO:
        return env_geometry(cmd, data);
    case RETRO_ENVIRONMENT_SET_MEMORY_MAPS:
        return env_memory_maps(data);
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
    case RETRO_ENVIRONMENT_SET_SERIALIZATION_QUIRKS:
    case RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:
    case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:
        return true;
    case RETRO_ENVIRONMENT_GET_HW_RENDER_CONTEXT_NEGOTIATION_INTERFACE_SUPPORT:
    case RETRO_ENVIRONMENT_SET_HW_SHARED_CONTEXT:
    case RETRO_ENVIRONMENT_GET_MICROPHONE_INTERFACE:     /* refused: no permission prompt can ever appear */
    case RETRO_ENVIRONMENT_GET_SENSOR_INTERFACE:
    case RETRO_ENVIRONMENT_GET_VFS_INTERFACE:
    case RETRO_ENVIRONMENT_GET_JIT_CAPABLE:
    case RETRO_ENVIRONMENT_GET_CURRENT_SOFTWARE_FRAMEBUFFER:
    case RETRO_ENVIRONMENT_SET_AUDIO_CALLBACK:
    case RETRO_ENVIRONMENT_SET_FRAME_TIME_CALLBACK:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2:
    case RETRO_ENVIRONMENT_SHUTDOWN:
        return false;
    default:
        return env_simple(cmd, data);
    }
}
