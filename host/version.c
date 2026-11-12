/* version.c: the core-version rule (pure; no libretro, no I/O). */
#include <assert.h>
#include <string.h>

#include "azh_pure.h"
#include "pins.h"

int azh_version_ok(const char *v, int any_core)
{
    size_t n = strlen(AZH_STOCK_VERSION);

    assert(n > 0 && strlen(AZH_LAZPY_SUFFIX) > 0);
    assert(any_core == 0 || any_core == 1);
    if (any_core != 0) {
        return 1;
    }
    if (v == NULL) {
        return 0;
    }
    if (strcmp(v, AZH_STOCK_VERSION) == 0) {
        return 1;
    }
    if (strncmp(v, AZH_STOCK_VERSION, n) == 0 && strcmp(v + n, AZH_LAZPY_SUFFIX) == 0) {
        return 1;
    }
    return 0;
}
