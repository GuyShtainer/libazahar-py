/* watch.c: the pure checks of guest memory calls and of the per-frame watch list (docs/plans/phase-g.md 3.2).
 * Includes only azh_pure.h, so it links into build/test-host; the core calls and the map writes are in mem.c. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"

#define FOUR_GIB ((uint64_t)1 << 32)

static void put_err(char *err, size_t cap, const char *text)
{
    if (err != NULL && cap > 0u) {
        (void)snprintf(err, cap, "%s", text);
    }
}

int azh__mem_check(uint32_t addr, uint32_t len, char *err, size_t cap)
{
    if (len < 1u || len > AZH_MEM_MAX_LEN) {
        if (err != NULL && cap > 0u) {
            (void)snprintf(err, cap, "guest memory length %u is outside 1..%u", len, AZH_MEM_MAX_LEN);
        }
        return AZH_E_ARG;
    }
    if ((uint64_t)addr + (uint64_t)len > FOUR_GIB) {
        if (err != NULL && cap > 0u) {
            (void)snprintf(err, cap, "guest memory 0x%08x+%u passes the end of the 4 GiB address space", addr, len);
        }
        return AZH_E_ARG;
    }
    return 0;
}

int azh__mem_code(int core_rc)
{
    switch (core_rc) {
    case 0:
        return 0;
    case -1:
        return AZH_E_ORDER;
    case -2:
        return AZH_E_UNMAPPED;
    case -3:
        return AZH_E_ARG;
    default:
        return AZH_E_CORE;
    }
}

/* every and the entries; sets *total to the words of one row */
static int plan_entries(const azh_watch *w, int32_t n, int32_t every, uint32_t *total, char *err, size_t cap)
{
    int32_t i;
    char text[160];

    if (n < 0 || n > AZH_MAX_WATCH) {
        (void)snprintf(text, sizeof text, "watch: %d entries, at most %d", n, AZH_MAX_WATCH);
        put_err(err, cap, text);
        return AZH_E_ARG;
    }
    if (every < 1 || every > AZH_WATCH_EVERY_MAX) {
        (void)snprintf(text, sizeof text, "watch_every %d is outside 0..%d", every, AZH_WATCH_EVERY_MAX);
        put_err(err, cap, text);
        return AZH_E_ARG;
    }
    *total = 0u;
    for (i = 0; i < n; i++) {
        if (w[i].words < 1u || w[i].words > (uint32_t)AZH_WATCH_MAX_WORDS) {
            (void)snprintf(text, sizeof text, "watch entry %d: %u words, must be 1..%d", i, w[i].words,
                           AZH_WATCH_MAX_WORDS);
            put_err(err, cap, text);
            return AZH_E_ARG;
        }
        if ((uint64_t)w[i].addr + 4u * (uint64_t)w[i].words > FOUR_GIB) {
            (void)snprintf(text, sizeof text, "watch entry %d: 0x%08x + %u words passes the end of the 4 GiB space",
                           i, w[i].addr, w[i].words);
            put_err(err, cap, text);
            return AZH_E_ARG;
        }
        *total += w[i].words;
    }
    return 0;
}

int azh__watch_plan(const azh_watch *w, int32_t n, int32_t frames, int32_t every,
                    uint32_t *row_bytes, uint32_t *total_words, uint32_t *rows_max, char *err, size_t cap)
{
    uint32_t total = 0u;
    uint64_t rb;
    uint64_t room;
    uint64_t rows_needed;
    char text[256];
    int rc;

    if (row_bytes == NULL || total_words == NULL || rows_max == NULL || (w == NULL && n > 0) || frames < 1) {
        put_err(err, cap, "watch: bad arguments to the plan");
        return AZH_E_ARG;
    }
    if (every == 0) {
        every = 1;
    }
    rc = plan_entries(w, n, every, &total, err, cap);
    if (rc != 0) {
        return rc;
    }
    rb = (uint64_t)AZH_WATCH_ROW_HDR + 4u * (uint64_t)total;
    room = (uint64_t)AZH_WATCH_AREA_BYTES - (uint64_t)AZH_WATCH_HDR_BYTES;
    *row_bytes = (uint32_t)rb;
    *total_words = total;
    *rows_max = (uint32_t)(room / rb);
    rows_needed = (uint64_t)frames / (uint64_t)every + (((uint64_t)frames % (uint64_t)every) != 0u ? 1u : 0u);
    if (rows_needed > (uint64_t)*rows_max) {
        (void)snprintf(text, sizeof text,
                       "watch rows for %d frames at watch_every %d need %llu rows of %u bytes, the area holds %u rows: "
                       "the largest batch at this watch_every is %llu frames",
                       frames, every, (unsigned long long)rows_needed, (unsigned)rb, (unsigned)*rows_max,
                       (unsigned long long)*rows_max * (unsigned long long)every);
        put_err(err, cap, text);
        return AZH_E_ARG;
    }
    return 0;
}
