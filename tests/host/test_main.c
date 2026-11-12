/* test_main.c: runs each test file's entry function, counts checks, prints "test-host: <N> checks, <F> failed". */
#include <stdarg.h>
#include <stdio.h>

#include "azh_pure.h"
#include "test_main.h"

static long checks;
static long failed;

void check(int ok, const char *fmt, ...)
{
    va_list ap;

    checks++;
    if (ok != 0) {
        return;
    }
    failed++;
    if (failed > 200) {
        return;             /* the count still grows; the printout stays short */
    }
    printf("FAIL ");
    va_start(ap, fmt);
    (void)vprintf(fmt, ap);
    va_end(ap);
    printf("\n");
}

int main(void)
{
    azh_png_init();
    test_input();
    test_touch();
    test_match();
    test_msg();
    test_rawcopy();
    test_png();
    test_sdcopy();
    test_statemeta();
    printf("test-host: %ld checks, %ld failed\n", checks, failed);
    return failed == 0 ? 0 : 1;
}
