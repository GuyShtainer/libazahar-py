/* core.c: dlopen the core, bind its 25 retro_* symbols, check name and version, install the callbacks. */
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "azh_internal.h"
#include "pins.h"

/* dlsym with the first missing name remembered; the cast from void * is the POSIX-sanctioned dlsym idiom */
static void *sym(void *dl, const char *name, const char **first_missing)
{
    void *p = dlsym(dl, name);

    if (p == NULL && *first_missing == NULL) {
        *first_missing = name;
    }
    return p;
}

static void bind_input_side(azh_core *c, const char **miss)
{
    void *d = c->dl;

    c->api_version = (unsigned (*)(void))sym(d, "retro_api_version", miss);
    c->set_environment = (void (*)(retro_environment_t))sym(d, "retro_set_environment", miss);
    c->set_video_refresh = (void (*)(retro_video_refresh_t))sym(d, "retro_set_video_refresh", miss);
    c->set_audio_sample = (void (*)(retro_audio_sample_t))sym(d, "retro_set_audio_sample", miss);
    c->set_audio_sample_batch = (void (*)(retro_audio_sample_batch_t))sym(d, "retro_set_audio_sample_batch", miss);
    c->set_input_poll = (void (*)(retro_input_poll_t))sym(d, "retro_set_input_poll", miss);
    c->set_input_state = (void (*)(retro_input_state_t))sym(d, "retro_set_input_state", miss);
    c->init = (void (*)(void))sym(d, "retro_init", miss);
    c->deinit = (void (*)(void))sym(d, "retro_deinit", miss);
    c->get_system_info = (void (*)(struct retro_system_info *))sym(d, "retro_get_system_info", miss);
    c->get_system_av_info = (void (*)(struct retro_system_av_info *))sym(d, "retro_get_system_av_info", miss);
    c->set_controller_port_device = (void (*)(unsigned, unsigned))sym(d, "retro_set_controller_port_device", miss);
}

static void bind_run_side(azh_core *c, const char **miss)
{
    void *d = c->dl;

    c->reset = (void (*)(void))sym(d, "retro_reset", miss);
    c->run = (void (*)(void))sym(d, "retro_run", miss);
    c->serialize_size = (size_t (*)(void))sym(d, "retro_serialize_size", miss);
    c->serialize = (bool (*)(void *, size_t))sym(d, "retro_serialize", miss);
    c->unserialize = (bool (*)(const void *, size_t))sym(d, "retro_unserialize", miss);
    c->cheat_reset = (void (*)(void))sym(d, "retro_cheat_reset", miss);
    c->cheat_set = (void (*)(unsigned, bool, const char *))sym(d, "retro_cheat_set", miss);
    c->load_game = (bool (*)(const struct retro_game_info *))sym(d, "retro_load_game", miss);
    c->load_game_special = (bool (*)(unsigned, const struct retro_game_info *, size_t))
        sym(d, "retro_load_game_special", miss);
    c->unload_game = (void (*)(void))sym(d, "retro_unload_game", miss);
    c->get_region = (unsigned (*)(void))sym(d, "retro_get_region", miss);
    c->get_memory_data = (void *(*)(unsigned))sym(d, "retro_get_memory_data", miss);
    c->get_memory_size = (size_t (*)(unsigned))sym(d, "retro_get_memory_size", miss);
}

/* name and version into the state; refuse a version azh_version_ok does not accept */
static int check_version(void)
{
    struct retro_system_info si;
    const char *any = getenv("LAZ_ANY_CORE");
    int any_core = (any != NULL && strcmp(any, "1") == 0) ? 1 : 0;

    memset(&si, 0, sizeof si);
    azh_g.core.get_system_info(&si);
    snprintf(azh_g.core_name, sizeof azh_g.core_name, "%s", si.library_name != NULL ? si.library_name : "(null)");
    snprintf(azh_g.core_version, sizeof azh_g.core_version, "%s",
             si.library_version != NULL ? si.library_version : "(null)");
    azh_log(AZH_LOG_INFO, "core %s version %s", azh_g.core_name, azh_g.core_version);
    if (azh_version_ok(si.library_version, any_core) == 0) {
        return azh_fail(AZH_E_CORE, "core version %s refused (accepted: %s or %s%s; LAZ_ANY_CORE=1 overrides)",
                        azh_g.core_version, AZH_STOCK_VERSION, AZH_STOCK_VERSION, AZH_LAZPY_SUFFIX);
    }
    return AZH_OK;
}

int azh_core_open(const char *path)
{
    const char *miss = NULL;
    azh_core *c = &azh_g.core;
    int bound;

    assert(path != NULL && c->dl == NULL);
    c->dl = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (c->dl == NULL) {
        const char *e = dlerror();

        return azh_fail(AZH_E_CORE, "cannot load core %s: %s", path, e != NULL ? e : "unknown error");
    }
    bind_input_side(c, &miss);
    bind_run_side(c, &miss);
    if (miss != NULL) {
        return azh_fail(AZH_E_CORE, "missing symbol %s in %s", miss, path);
    }
    if (c->api_version() != (unsigned)RETRO_API_VERSION) {
        return azh_fail(AZH_E_CORE, "core speaks libretro API %u, not %d", c->api_version(), RETRO_API_VERSION);
    }
    bound = azh__mem_bind(c->dl);
    if (bound < 0) {
        return azh_fail(AZH_E_CORE, "our core lacks lazpy_write_memory (or lazpy_read_memory): half-exported core %s",
                        path);
    }
    azh_g.is_lazpy = bound;
    return check_version();
}

void azh_core_install_callbacks(void)
{
    azh_core *c = &azh_g.core;

    assert(c->dl != NULL);
    c->set_environment(azh_env);          /* the option store and sysdir are live before this call */
    c->set_video_refresh(azh_video_cb);
    c->set_audio_sample(azh_audio_sample_cb);
    c->set_audio_sample_batch(azh_audio_batch_cb);
    c->set_input_poll(azh_input_poll_cb);
    c->set_input_state(azh_input_state_cb);
}

/* unload the game and deinit what was set up; the core stays mapped (it owns threads, dlclose is unsafe) */
void azh_core_close(void)
{
    azh_core *c = &azh_g.core;

    if (c->dl == NULL) {
        return;
    }
    if (azh_g.have_hw != 0 && azh_g.hw.context_destroy != NULL && azh_g.vk_ready != 0) {
        azh_g.hw.context_destroy();      /* libretro's order: destroy the context, then unload */
    }
    if (azh_g.game_loaded != 0) {
        c->unload_game();
        azh_g.game_loaded = 0;
    }
    if (azh_g.core_inited != 0) {
        c->deinit();
        azh_g.core_inited = 0;
    }
}
