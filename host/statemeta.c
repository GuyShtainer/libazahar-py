/* statemeta.c (pure): the savestate meta file. STUB from C1; step D fills it. */
#include <assert.h>

#include "azh_pure.h"

int azh__meta_format(const azh_state_meta *m, char *buf, size_t cap)
{
    assert(m != NULL && buf != NULL && cap > 0u);
    return AZH_E_UNSUPPORTED;
}

int azh__meta_parse(const char *text, size_t len, azh_state_meta *m)
{
    assert(text != NULL && m != NULL && len < (size_t)1 << 30);
    return AZH_E_UNSUPPORTED;
}

int azh__meta_write(const char *path, const azh_state_meta *m)
{
    assert(path != NULL && m != NULL);
    return AZH_E_UNSUPPORTED;
}

int azh__meta_read(const char *path, azh_state_meta *m)
{
    assert(path != NULL && m != NULL);
    return AZH_E_UNSUPPORTED;
}
