/* version.c: the core-version rule (pure; no libretro, no I/O). */
#include <assert.h>
#include <string.h>

#include "azh_pure.h"
#include "pins.h"

int azh_version_ok(const char *v, int any_core)
{
    static const char *const suffixes[] = AZH_LAZPY_SUFFIXES;
    size_t n = strlen(AZH_STOCK_VERSION);
    size_t i;

    assert(n > 0 && sizeof suffixes / sizeof suffixes[0] > 0);
    assert(any_core == 0 || any_core == 1);
    if (any_core != 0) {
        return 1;
    }
    if (v == NULL) {
        return 0;
    }
    if (strcmp(v, AZH_STOCK_VERSION) == 0 || strcmp(v, AZH_STOCK_COMMIT) == 0) {
        return 1;
    }
    if (strncmp(v, AZH_STOCK_VERSION, n) != 0) {
        return 0;
    }
    for (i = 0; i < sizeof suffixes / sizeof suffixes[0]; i++) {
        assert(suffixes[i] != NULL && suffixes[i][0] != '\0');
        if (strcmp(v + n, suffixes[i]) == 0) {
            return 1;
        }
    }
    return 0;
}
