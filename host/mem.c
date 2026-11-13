/* mem.c: guest memory through our core's two exports (lazpy_read_memory / lazpy_write_memory, core patch 0001), the
 * guest threads through lazpy_threads (patch 0009, core lazpy.2, optional), and the
 * per-frame watch rows written into the map's watch area (docs/plans/phase-g.md 3.3). Everything runs on the thread
 * that calls retro_run, between frames. The pure checks are in watch.c. */
#include <assert.h>
#ifdef _WIN32
#include "plat/win_compat.h"
#else
#include <dlfcn.h>
#endif
#include <stdint.h>
#include <string.h>

#include "azh_internal.h"

/* function-pointer exception (4): the core's exports have the patch's C signature, address then buffer then length */
typedef int (*mem_rd_fn)(uint32_t vaddr, void *buf, uint32_t len);
typedef int (*mem_wr_fn)(uint32_t vaddr, const void *buf, uint32_t len);
typedef int (*thr_fn)(azh_thread *out, uint32_t max, uint32_t *count);

_Static_assert(sizeof(azh_thread) == 40, "azh_thread must match the core's 40-byte lazpy_thread");

static mem_rd_fn core_read;
static mem_wr_fn core_write;
static thr_fn core_threads;                     /* NULL on a lazpy.1 core */

/* the watch plan of the running batch */
static struct {
    int on;
    uint32_t row_bytes, words, rows_max, rows;
    int32_t every, status;
    int32_t last_row_frame;             /* batch frame of the last row written, 0 none */
} wl;

int azh__mem_bind(void *core_handle)
{
    void *rd;
    void *wr;
    void *th;

    assert(core_handle != NULL);
    rd = dlsym(core_handle, "lazpy_read_memory");
    wr = dlsym(core_handle, "lazpy_write_memory");
    th = dlsym(core_handle, "lazpy_threads");
    core_read = NULL;
    core_write = NULL;
    core_threads = NULL;
    if (rd == NULL && wr == NULL) {
        return 0;
    }
    if (rd == NULL || wr == NULL) {
        return -1;
    }
    memcpy(&core_read, &rd, sizeof rd);         /* dlsym gives void *; the cast of a data pointer to a function pointer */
    memcpy(&core_write, &wr, sizeof wr);
    if (th != NULL) {
        memcpy(&core_threads, &th, sizeof th);
    }
    return 1;
}

/* the texts of the core's failure codes */
static int mem_fail(int core_rc, uint32_t addr, uint32_t len)
{
    int code = azh__mem_code(core_rc);

    assert(core_rc != 0);
    switch (code) {
    case AZH_E_ORDER:
        return azh_fail(code, "guest memory 0x%08x+%u: the core has no current process", addr, len);
    case AZH_E_UNMAPPED:
        return azh_fail(code, "guest memory 0x%08x+%u: a page is unmapped", addr, len);
    case AZH_E_ARG:
        return azh_fail(code, "guest memory 0x%08x+%u: the core refused the arguments", addr, len);
    default:
        return azh_fail(code, "guest memory 0x%08x+%u: the core returned %d", addr, len, core_rc);
    }
}

int azh__mem_read(uint32_t addr, uint32_t len, void *buf)
{
    char err[160];
    int rc;

    assert(core_read != NULL);
    if (buf == NULL) {
        return azh_fail(AZH_E_ARG, "azh_read: NULL buffer");
    }
    if (azh__mem_check(addr, len, err, sizeof err) != 0) {
        return azh_fail(AZH_E_ARG, "azh_read: %s", err);
    }
    rc = core_read(addr, buf, len);
    return rc == 0 ? AZH_OK : mem_fail(rc, addr, len);
}

int azh__mem_write(uint32_t addr, uint32_t len, const void *buf)
{
    char err[160];
    int rc;

    assert(core_write != NULL);
    if (buf == NULL) {
        return azh_fail(AZH_E_ARG, "azh_write: NULL buffer");
    }
    if (azh__mem_check(addr, len, err, sizeof err) != 0) {
        return azh_fail(AZH_E_ARG, "azh_write: %s", err);
    }
    rc = core_write(addr, buf, len);
    return rc == 0 ? AZH_OK : mem_fail(rc, addr, len);
}

int azh__mem_threads(azh_thread *out, int32_t max, int32_t *count)
{
    uint32_t n = 0;
    int rc;

    if (count == NULL || max < 0 || (out == NULL && max > 0)) {
        return azh_fail(AZH_E_ARG, "azh_threads: needs count, max >= 0, and out when max > 0");
    }
    *count = 0;
    if (core_threads == NULL) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "core lacks lazpy_threads (lazpy.1): thread registers need core lazpy.2");
    }
    rc = core_threads(out, (uint32_t)max, &n);
    if (rc == -1) {
        return azh_fail(AZH_E_ORDER, "azh_threads: the core is not running");
    }
    if (rc != 0) {
        return azh_fail(rc == -3 ? AZH_E_ARG : AZH_E_CORE, "azh_threads: the core returned %d", rc);
    }
    *count = n > (uint32_t)INT32_MAX ? INT32_MAX : (int32_t)n;
    return AZH_OK;
}

/* ---- the watch list ---- */

int azh__watch_check(const azh_batch *b)
{
    uint32_t row_bytes;
    uint32_t words;
    uint32_t rows_max;
    char err[300];

    assert(b != NULL);
    if (b->n_watch == 0) {
        return AZH_OK;
    }
    if (azh_g.is_lazpy == 0) {
        return azh_fail(AZH_E_NEEDS_LAZPY_CORE, "a watch list needs the libazahar core (this core is stock)");
    }
    if (azh__watch_plan(b->watch, b->n_watch, b->frames, b->watch_every, &row_bytes, &words, &rows_max, err,
                        sizeof err) != 0) {
        return azh_fail(AZH_E_ARG, "azh_run: %s", err);
    }
    return AZH_OK;
}

void azh__watch_begin(const azh_batch *b)
{
    uint8_t *area = azh_map_watch();
    char err[16];
    uint32_t seq;
    int64_t first = azh_g.abs_frames;

    assert(b != NULL);
    memset(&wl, 0, sizeof wl);
    if (b->n_watch == 0 || area == NULL) {
        return;
    }
    wl.every = (b->watch_every == 0) ? 1 : b->watch_every;
    if (azh__watch_plan(b->watch, b->n_watch, b->frames, wl.every, &wl.row_bytes, &wl.words, &wl.rows_max, err,
                        sizeof err) != 0) {
        return;                              /* azh__watch_check passed this plan already */
    }
    wl.on = 1;
    __atomic_store_n((uint32_t *)(void *)(area + 0), 0u, __ATOMIC_RELEASE);
    memcpy(area + 4, &wl.row_bytes, 4);
    memcpy(area + 8, &wl.words, 4);
    seq = __atomic_load_n((uint32_t *)(void *)(area + 12), __ATOMIC_RELAXED) + 1u;
    __atomic_store_n((uint32_t *)(void *)(area + 12), seq, __ATOMIC_RELEASE);
    memcpy(area + 16, &first, 8);
}

/* one row: frame, status, failed count, then each entry's words (a failed entry's words are zero) */
static void write_row(const azh_batch *b, int32_t i)
{
    uint8_t *area = azh_map_watch();
    uint8_t *row;
    int64_t frame = azh_g.abs_frames;
    int32_t status = 0;
    uint32_t failed = 0u;
    int32_t e;
    uint32_t off = AZH_WATCH_ROW_HDR;
    int rc;

    assert(wl.on != 0 && area != NULL && wl.rows < wl.rows_max);
    row = area + AZH_WATCH_HDR_BYTES + (size_t)wl.rows * wl.row_bytes;
    for (e = 0; e < b->n_watch && e < AZH_MAX_WATCH; e++) {
        uint32_t nbytes = 4u * b->watch[e].words;

        rc = core_read(b->watch[e].addr, row + off, nbytes);
        if (rc != 0) {
            memset(row + off, 0, nbytes);
            failed++;
            status = (status == 0) ? azh__mem_code(rc) : status;
        }
        off += nbytes;
    }
    assert(off == wl.row_bytes);
    memcpy(row, &frame, 8);
    memcpy(row + 8, &status, 4);
    memcpy(row + 12, &failed, 4);
    wl.rows++;
    wl.last_row_frame = i;
    wl.status = (wl.status == 0) ? status : wl.status;
    __atomic_store_n((uint32_t *)(void *)(area + 0), wl.rows, __ATOMIC_RELEASE);
}

void azh__watch_row(const azh_batch *b, int32_t i)
{
    assert(b != NULL && i >= 1);
    if (wl.on != 0 && i % wl.every == 0) {
        write_row(b, i);
    }
}

void azh__watch_finish(const azh_batch *b, int32_t frames_run, azh_result *out)
{
    assert(b != NULL && out != NULL);
    if (wl.on == 0) {
        return;
    }
    if (frames_run >= 1 && wl.last_row_frame != frames_run) {
        write_row(b, frames_run);
    }
    out->watch_rows = (int32_t)wl.rows;
    out->watch_status = wl.status;
    wl.on = 0;
}
