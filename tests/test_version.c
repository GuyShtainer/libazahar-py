/* test_version.c: host test of azh_version_ok (gate A check 6b). */
#include <stdio.h>

#include "azh_pure.h"

static int failures;

static void expect(const char *v, int any_core, int want)
{
    if (azh_version_ok(v, any_core) != want) {
        printf("FAIL azh_version_ok(\"%s\", %d) != %d\n", v, any_core, want);
        failures++;
    }
}

int main(void)
{
    expect("2126.2", 0, 1);
    expect("2126.3", 0, 0);
    expect("2126.2-lazpy.1", 0, 1);
    expect("2126.2-lazpy", 0, 0);
    expect("2126.2-lazpy.12", 0, 0);
    expect("x", 0, 0);
    expect("x", 1, 1);
    if (failures != 0) {
        return 1;
    }
    printf("test-version ok\n");
    return 0;
}
