/* state.c: savestates and state boot. STUB from C1; step D fills it. Every azh__state_* except the note returns
 * AZH_E_UNSUPPORTED (with the error text set). */
#include <assert.h>
#include <stdio.h>

#include "azh_internal.h"

static char noted_app[AZH_PATH_MAX];

void azh__state_note_app(const char *app)
{
    assert(app != NULL);
    (void)snprintf(noted_app, sizeof noted_app, "%s", app);
    assert(noted_app[0] != '\0' || app[0] == '\0');
}

int azh__state_boot(const char *app, const char *state_path)
{
    (void)app;
    (void)state_path;
    return azh_fail(AZH_E_UNSUPPORTED, "booting from a savestate arrives in step D");
}

int azh__state_save(const char *path, int32_t *k_out)
{
    (void)path;
    (void)k_out;
    return azh_fail(AZH_E_UNSUPPORTED, "savestates arrive in step D");
}

int azh__state_load(const char *path)
{
    (void)path;
    return azh_fail(AZH_E_UNSUPPORTED, "savestates arrive in step D");
}
