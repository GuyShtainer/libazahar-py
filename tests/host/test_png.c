/* test_png.c: write a 3 x 2 RGBA image with a stride wider than the row, read it back with zlib. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <zlib.h>

#include "azh_pure.h"
#include "plat_test.h"
#include "test_main.h"

static uint32_t rd32(const uint8_t *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void check_chunks(const uint8_t *b, size_t n, uint8_t *idat, size_t *idat_len)
{
    static const uint8_t sig[8] = { 0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a };
    size_t at = 8;
    int guard;

    check(n > 8 && memcmp(b, sig, 8) == 0, "PNG signature");
    *idat_len = 0;
    for (guard = 0; guard < 8 && at + 12 <= n; guard++) {
        uint32_t len = rd32(b + at);
        uint32_t crc;

        check(at + 12 + len <= n, "chunk %d fits", guard);
        if (at + 12 + len > n) {
            return;
        }
        crc = (uint32_t)crc32(crc32(0L, b + at + 4, 4), b + at + 8, len);
        check(crc == rd32(b + at + 8 + len), "CRC of chunk %.4s", (const char *)(b + at + 4));
        if (memcmp(b + at + 4, "IHDR", 4) == 0) {
            check(len == 13 && rd32(b + at + 8) == 3 && rd32(b + at + 12) == 2 && b[at + 16] == 8 && b[at + 17] == 6,
                  "IHDR is 3 x 2, 8-bit RGBA");
        } else if (memcmp(b + at + 4, "IDAT", 4) == 0) {
            memcpy(idat + *idat_len, b + at + 8, len);
            *idat_len += len;
        }
        at += 12 + len;
    }
}

void test_png(void)
{
    uint8_t px[2 * 20];
    uint8_t file[1024];
    uint8_t idat[512];
    uint8_t raw[2 * (3 * 4 + 1)];
    uLongf raw_len = sizeof raw;
    size_t idat_len = 0;
    char path[512];
    const char *tmp = getenv("TMPDIR");
    int fd;
    FILE *f;
    size_t n;
    int i;
    int y;

    (void)snprintf(path, sizeof path, "%s/azh-png-XXXXXX", AZH_TEST_TMPDIR(tmp));
#ifdef _WIN32
    fd = azh_test_mkstemp(path, sizeof path);
#else
    fd = mkstemp(path);
#endif
    check(fd >= 0, "mkstemp");
    if (fd < 0) {
        return;
    }
    (void)close(fd);
    for (i = 0; i < 40; i++) {
        px[i] = (uint8_t)(i * 5 + 1);
    }
    check(azh_png_write(path, px, 3, 2, 20) == 0, "azh_png_write with stride 20");
    f = fopen(path, "rb");
    check(f != NULL, "reopen");
    if (f == NULL) {
        (void)unlink(path);
        return;
    }
    n = fread(file, 1, sizeof file, f);
    (void)fclose(f);
    (void)unlink(path);
    check_chunks(file, n, idat, &idat_len);
    check(uncompress(raw, &raw_len, idat, (uLong)idat_len) == Z_OK && raw_len == sizeof raw, "uncompress");
    for (y = 0; y < 2; y++) {
        check(raw[y * 13] == 0, "filter byte of row %d", y);
        check(memcmp(raw + y * 13 + 1, px + y * 20, 12) == 0, "pixels of row %d", y);
    }
}
