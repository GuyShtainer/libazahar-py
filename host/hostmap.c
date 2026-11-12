/* hostmap.c: the mapped file host.map (layout in azh_internal.h; little-endian). */
#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#include "azh_internal.h"

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

int azh_map_create(const char *path)
{
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
    map = p;
    heartbeat = 0u;
    memset(map, 0, AZH_MAP_SIZE);
    memcpy(map, "LAZMAP1", 8);     /* includes the terminating NUL */
    put32(map + 8, 1u);
    put32(map + 12, AZH_MAP_HEADER);
    put32(map + AZH_MAP_OFF_SIZES, 400u);
    put32(map + AZH_MAP_OFF_SIZES + 4, 240u);
    put32(map + AZH_MAP_OFF_SIZES + 8, 320u);
    put32(map + AZH_MAP_OFF_SIZES + 12, 240u);
    return 0;
}

void azh_map_close(void)
{
    if (map != NULL) {
        (void)munmap(map, AZH_MAP_SIZE);     /* teardown: nothing to do on failure */
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
}
