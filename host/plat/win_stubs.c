/* plat/win_stubs.c: the probe host does not do states, SD seeding or the tree walk: each returns AZH_E_UNSUPPORTED. */
#ifdef _WIN32
#include <assert.h>

#include "azh_internal.h"

void azh__state_note_app(const char *app)
{
    assert(app != NULL);
}

int azh__state_boot(const char *app, const char *state_path)
{
    assert(app != NULL && state_path != NULL);
    return azh_fail(AZH_E_UNSUPPORTED, "--state is not supported by the Windows probe host");
}

int azh__state_save(const char *path, int32_t *k_out)
{
    assert(path != NULL && k_out != NULL);
    return azh_fail(AZH_E_UNSUPPORTED, "save state is not supported by the Windows probe host");
}

int azh__state_load(const char *path)
{
    assert(path != NULL);
    return azh_fail(AZH_E_UNSUPPORTED, "load state is not supported by the Windows probe host");
}

int azh__copy_tree(const char *src, const char *dst)
{
    assert(src != NULL && dst != NULL);
    return azh_fail(AZH_E_UNSUPPORTED, "--sd-seed (the tree copy) is not supported by the Windows probe host");
}

int azh__clear_tree(const char *dir)
{
    assert(dir != NULL);
    return azh_fail(AZH_E_UNSUPPORTED, "the tree walk is not supported by the Windows probe host");
}
#endif
