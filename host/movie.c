/* movie.c: play a movie file (Azahar's .ctm) from boot, through our core's lazpy_movie_play export (core patch 0006).
 * azh_movie_play only stores the path; azh_boot hands it to the core between retro_load_game and the render context's
 * reset, the one window in which the core takes it. */
#include <assert.h>
#ifdef _WIN32
#include "plat/win_compat.h"
#else
#include <dlfcn.h>
#endif
#include <stdio.h>
#include <string.h>

#include "azh_internal.h"

static char movie_path[AZH_PATH_MAX];       /* empty: no movie */

/* the one function pointer here: the core's lazpy_movie_play(path) (C golden rule 9, documented in azh_internal.h) */
typedef int (*movie_play_fn)(const char *path);

void azh__movie_clear(void)
{
    movie_path[0] = '\0';
}

int azh_movie_play(const char *path)
{
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_OPEN) {
        return azh_fail(AZH_E_ORDER, "azh_movie_play: only after azh_open and before azh_boot");
    }
    if (path == NULL || *path == '\0') {
        azh__movie_clear();
        return AZH_OK;
    }
    if (azh_g.is_lazpy == 0) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "a movie needs the libazahar core (this core is stock)");
    }
    if (strlen(path) >= sizeof movie_path) {
        return azh_fail(AZH_E_ARG, "azh_movie_play: path too long");
    }
    (void)snprintf(movie_path, sizeof movie_path, "%s", path);
    return AZH_OK;
}

static int core_code(int code)
{
    switch (code) {
    case 0:
        return AZH_OK;
    case -2:
        return azh_fail(AZH_E_IO, "the movie file %s does not exist", movie_path);
    case -4:
        return azh_fail(AZH_E_ARG, "%s is not a movie file the core accepts", movie_path);
    case -5:
        return azh_fail(AZH_E_ORDER, "the core had already booted when the movie was set");
    default:
        return azh_fail(AZH_E_CORE, "the core refused the movie %s (code %d)", movie_path, code);
    }
}

int azh__movie_apply(void)
{
    movie_play_fn play;
    void *sym;

    assert(azh_g.core.dl != NULL);
    if (movie_path[0] == '\0') {
        return AZH_OK;
    }
    sym = dlsym(azh_g.core.dl, "lazpy_movie_play");
    if (sym == NULL) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "the core lacks lazpy_movie_play: it needs core patch 0006");
    }
    memcpy(&play, &sym, sizeof play);       /* the POSIX-sanctioned void * to function pointer copy */
    azh_log(AZH_LOG_INFO, "movie %s", movie_path);
    return core_code(play(movie_path));
}
