/* hostmap.c: the mapped file host.map (layout in azh_internal.h; little-endian). */
#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#ifndef _WIN32
#include <sys/mman.h>
#endif

#include "azh_internal.h"
#ifdef _WIN32
#include "plat/win_compat.h"
#endif

#if !defined(__BYTE_ORDER__) || __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "host.map is little-endian and written with plain stores"
#endif

static uint8_t *map;
static uint64_t heartbeat;

static void put32(uint8_t *at, uint32_t v)
{
    at[0] = (uint8_t)v;
    at[1] = (uint8_t)(v >> 8);
    at[2] = (uint8_t)(v >> 16);
    at[3] = (uint8_t)(v >> 24);
}

static void store64(uint32_t off, int64_t v)
{
    assert(map != NULL && off + 8u <= AZH_MAP_HEADER && off % 8u == 0u);
    __atomic_store_n((int64_t *)(void *)(map + off), v, __ATOMIC_RELEASE);
}

int azh_map_create(const char *path)
{
#ifdef _WIN32
    void *p;

    assert(path != NULL && map == NULL);
    p = azh_win_map_create(path, AZH_MAP_SIZE);
    if (p == NULL) {
        return -1;
    }
#else
    int fd;
    void *p;

    assert(path != NULL && map == NULL);
    fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        return -1;
    }
    if (ftruncate(fd, (off_t)AZH_MAP_SIZE) != 0) {
        (void)close(fd);
        return -1;
    }
    p = mmap(NULL, AZH_MAP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    (void)close(fd);     /* the mapping keeps the file */
    if (p == MAP_FAILED) {
        return -1;
    }
#endif
    map = p;
    heartbeat = 0u;
    memset(map, 0, AZH_MAP_PX_END);      /* the watch area stays untouched: zero pages take no memory until written */
    memcpy(map, "LAZMAP1", 8);     /* includes the terminating NUL */
    put32(map + 8, AZH_MAP_VERSION);
    put32(map + 12, AZH_MAP_HEADER);
    put32(map + AZH_MAP_OFF_SIZES, 400u);
    put32(map + AZH_MAP_OFF_SIZES + 4, 240u);
    put32(map + AZH_MAP_OFF_SIZES + 8, 320u);
    put32(map + AZH_MAP_OFF_SIZES + 12, 240u);
    store64(AZH_MAP_OFF_PXFRAME, -1);              /* no pixels yet */
    put32(map + AZH_MAP_OFF_PID, (uint32_t)getpid());
    return 0;
}

void azh_map_close(void)
{
    if (map != NULL) {
#ifdef _WIN32
        azh_win_map_close(map);
#else
        (void)munmap(map, AZH_MAP_SIZE);     /* teardown: nothing to do on failure */
#endif
        map = NULL;
    }
}

void azh_map_heartbeat(void)
{
    if (map == NULL) {
        return;
    }
    heartbeat++;
    __atomic_store_n((uint64_t *)(void *)(map + AZH_MAP_OFF_HEARTBEAT), heartbeat, __ATOMIC_RELEASE);
}

void azh_map_set_stop(int32_t code)
{
    if (map == NULL) {
        return;
    }
    put32(map + AZH_MAP_OFF_STOP, (uint32_t)code);
}

void azh_map_set_message(const char *msg)
{
    size_t n;

    assert(msg != NULL);
    if (map == NULL) {
        return;
    }
    n = strnlen(msg, AZH_MAP_MSG_MAX - 1u);
    memcpy(map + AZH_MAP_OFF_MSG, msg, n);
    map[AZH_MAP_OFF_MSG + n] = 0;
    put32(map + AZH_MAP_OFF_MSGLEN, (uint32_t)n);
    __atomic_add_fetch((uint32_t *)(void *)(map + AZH_MAP_OFF_MSG_SEQ), 1u, __ATOMIC_RELEASE);
}

void azh_map_set_counters(int64_t frame_total, int64_t vblanks_total)
{
    if (map == NULL) {
        return;
    }
    store64(AZH_MAP_OFF_FRAME_TOTAL, frame_total);
    store64(AZH_MAP_OFF_VBLANKS_TOTAL, vblanks_total);
}

void azh_map_set_exit_code(int32_t code)
{
    if (map == NULL) {
        return;
    }
    put32(map + AZH_MAP_OFF_EXIT_CODE, (uint32_t)code);
}

void azh_map_sync(void)
{
    if (map != NULL) {
#ifdef _WIN32
        azh_win_map_flush(map, AZH_MAP_SIZE);
#else
        (void)msync(map, AZH_MAP_SIZE, MS_SYNC);     /* best effort: the process is about to exit */
#endif
    }
}

uint8_t *azh_map_pixels(void)
{
    return (map != NULL) ? map + AZH_MAP_HEADER : NULL;
}

uint8_t *azh_map_watch(void)
{
    return (map != NULL) ? map + AZH_WATCH_AREA_OFF : NULL;
}

void azh_map_raw_begin(const uint32_t dims[4])
{
    int i;

    assert(dims != NULL);
    if (map == NULL) {
        return;
    }
    store64(AZH_MAP_OFF_PXFRAME, -1);
    for (i = 0; i < 4; i++) {
        put32(map + AZH_MAP_OFF_SIZES + 4u * (uint32_t)i, dims[i]);
    }
}

void azh_map_raw_end(int64_t px_frame)
{
    if (map == NULL) {
        return;
    }
    assert(px_frame >= 0);
    store64(AZH_MAP_OFF_PXFRAME, px_frame);
}
