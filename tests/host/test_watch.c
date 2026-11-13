/* test_watch.c: the pure memory and watch-list checks (host/watch.c). */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"
#include "test_main.h"

static void test_mem_check(void)
{
    char err[160] = "";

    check(azh__mem_check(0x1000u, 0u, err, sizeof err) == AZH_E_ARG && err[0] != '\0', "mem_check len 0");
    check(azh__mem_check(0u, AZH_MEM_MAX_LEN, NULL, 0u) == 0, "mem_check cap length");
    check(azh__mem_check(0u, AZH_MEM_MAX_LEN + 1u, NULL, 0u) == AZH_E_ARG, "mem_check cap + 1");
    check(azh__mem_check(0xFFFFFFFCu, 4u, NULL, 0u) == 0, "mem_check 0xFFFFFFFC + 4");
    check(azh__mem_check(0xFFFFFFFCu, 8u, err, sizeof err) == AZH_E_ARG, "mem_check 0xFFFFFFFC + 8");
    check(azh__mem_check(0xFFFFFFFFu, 1u, NULL, 0u) == 0, "mem_check last byte");
    check(azh__mem_check(0xFFFFFFFFu, 2u, NULL, 0u) == AZH_E_ARG, "mem_check last byte + 1");
}

static void test_mem_code(void)
{
    check(azh__mem_code(0) == 0, "code 0");
    check(azh__mem_code(-1) == AZH_E_ORDER, "code -1");
    check(azh__mem_code(-2) == AZH_E_UNMAPPED, "code -2");
    check(azh__mem_code(-3) == AZH_E_ARG, "code -3");
    check(azh__mem_code(-7) == AZH_E_CORE, "code -7");
}

/* the largest frames that fit at this every, for the entries w[0..n) */
static void largest(const azh_watch *w, int32_t n, int32_t every, const char *name)
{
    uint32_t rb = 0u;
    uint32_t tw = 0u;
    uint32_t rm = 0u;
    char err[300] = "";
    char want[32];
    int32_t fit;

    check(azh__watch_plan(w, n, 1, every, &rb, &tw, &rm, err, sizeof err) == 0, "%s: one frame plans", name);
    fit = (int32_t)(rm * (uint32_t)every);
    check(azh__watch_plan(w, n, fit, every, &rb, &tw, &rm, err, sizeof err) == 0, "%s: %d frames fit", name, fit);
    err[0] = '\0';
    check(azh__watch_plan(w, n, fit + 1, every, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "%s: %d refused", name,
          fit + 1);
    (void)snprintf(want, sizeof want, "%d frames", fit);
    check(strstr(err, want) != NULL, "%s: text names %d (got: %s)", name, fit, err);
}

static void test_plan(void)
{
    azh_watch w[AZH_MAX_WATCH + 1];
    azh_watch two[2] = { { 0x00122dd8u, 8u }, { 0x08000000u, 8u } };
    uint32_t rb = 0u;
    uint32_t tw = 0u;
    uint32_t rm = 0u;
    char err[300] = "";
    int i;

    memset(w, 0, sizeof w);
    for (i = 0; i <= AZH_MAX_WATCH; i++) {
        w[i].addr = 0x1000u * (uint32_t)(i + 1);
        w[i].words = 1u;
    }
    check(azh__watch_plan(w, AZH_MAX_WATCH + 1, 10, 1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "33 entries");
    check(azh__watch_plan(w, AZH_MAX_WATCH, 10, 1, &rb, &tw, &rm, err, sizeof err) == 0, "32 entries");
    check(azh__watch_plan(w, -1, 10, 1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "negative n");
    w[0].words = 0u;
    check(azh__watch_plan(w, 1, 10, 1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "0 words");
    w[0].words = 257u;
    check(azh__watch_plan(w, 1, 10, 1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "257 words");
    w[0].words = 256u;
    check(azh__watch_plan(w, 1, 10, 1, &rb, &tw, &rm, err, sizeof err) == 0 && tw == 256u, "256 words");
    w[0].addr = 0xFFFFFFFCu;
    w[0].words = 2u;
    check(azh__watch_plan(w, 1, 10, 1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "wraps 4 GiB");
    w[0].words = 1u;
    check(azh__watch_plan(w, 1, 10, 1, &rb, &tw, &rm, err, sizeof err) == 0, "ends at 4 GiB");
    check(azh__watch_plan(two, 2, 10, 0, &rb, &tw, &rm, err, sizeof err) == 0, "every 0 is 1");
    check(azh__watch_plan(two, 2, 10, 1, &rb, &tw, &rm, err, sizeof err) == 0 && rb == 80u && tw == 16u,
          "(8, 8): row bytes 80, words 16 (got %u, %u)", rb, tw);
    check(azh__watch_plan(two, 2, 10, 100000, &rb, &tw, &rm, err, sizeof err) == 0, "every 100000");
    check(azh__watch_plan(two, 2, 10, 100001, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "every 100001");
    check(azh__watch_plan(two, 2, 10, -1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "every -1");
    check(azh__watch_plan(two, 2, 0, 1, &rb, &tw, &rm, err, sizeof err) == AZH_E_ARG, "0 frames");
    check(azh__watch_plan(two, 0, 10, 1, &rb, &tw, &rm, err, sizeof err) == 0 && tw == 0u, "no entries");
    largest(two, 2, 1, "(8,8) every 1");
    largest(two, 2, 10, "(8,8) every 10");
    largest(two, 2, 7, "(8,8) every 7");
}

void test_watch(void)
{
    test_mem_check();
    test_mem_code();
    test_plan();
}
