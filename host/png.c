/* png.c: the PNG writer (pure; zlib only). 8-bit RGBA, filter 0 on every row, one IDAT. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#include "azh_pure.h"

#define PNG_LEVEL 6                 /* step E tunes this */
#define PNG_MAX_DIM 65535u

static uint32_t crc_table[256];
static int crc_ready;

void azh_png_init(void)
{
    uint32_t n;
    uint32_t k;
    int j;

    for (n = 0u; n < 256u; n++) {
        k = n;
        for (j = 0; j < 8; j++) {
            k = ((k & 1u) != 0u) ? (0xedb88320u ^ (k >> 1)) : (k >> 1);
        }
        crc_table[n] = k;
    }
    crc_ready = 1;
}

static uint32_t crc_update(uint32_t crc, const uint8_t *d, size_t len)
{
    size_t i;

    assert(crc_ready != 0);
    for (i = 0; i < len; i++) {
        crc = crc_table[(crc ^ d[i]) & 255u] ^ (crc >> 8);
    }
    return crc;
}

static void be32(uint8_t *out, uint32_t v)
{
    out[0] = (uint8_t)(v >> 24);
    out[1] = (uint8_t)(v >> 16);
    out[2] = (uint8_t)(v >> 8);
    out[3] = (uint8_t)v;
}

/* one chunk: length, type, data, CRC over type and data. Returns 0 or -1. */
static int put_chunk(FILE *f, const char *type, const uint8_t *data, size_t len)
{
    uint8_t head[8];
    uint8_t tail[4];
    uint32_t crc;

    assert(f != NULL && type != NULL && strlen(type) == 4u);
    assert(len <= 0x7fffffffu);
    be32(head, (uint32_t)len);
    memcpy(head + 4, type, 4);
    crc = crc_update(0xffffffffu, (const uint8_t *)type, 4);
    crc = crc_update(crc, data, len);
    be32(tail, ~crc);
    if (fwrite(head, 1, 8, f) != 8u) {
        return -1;
    }
    if (len > 0u && fwrite(data, 1, len, f) != len) {
        return -1;
    }
    return fwrite(tail, 1, 4, f) == 4u ? 0 : -1;
}

/* the filtered scanlines: a 0 byte, then the row's RGBA bytes */
static void fill_rows(uint8_t *raw, const uint8_t *px, uint32_t w, uint32_t h, size_t stride)
{
    size_t row_len = (size_t)w * 4u + 1u;
    uint32_t y;

    for (y = 0u; y < h; y++) {
        raw[(size_t)y * row_len] = 0u;
        memcpy(raw + (size_t)y * row_len + 1u, px + (size_t)y * stride, (size_t)w * 4u);
    }
}

static int write_file(const char *path, const uint8_t *z, size_t zlen, uint32_t w, uint32_t h)
{
    static const uint8_t sig[8] = { 0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a };
    uint8_t ihdr[13];
    FILE *f = fopen(path, "wb");
    int rc = 0;

    if (f == NULL) {
        return -2;
    }
    be32(ihdr, w);
    be32(ihdr + 4, h);
    ihdr[8] = 8;        /* bit depth */
    ihdr[9] = 6;        /* colour type RGBA */
    ihdr[10] = 0;
    ihdr[11] = 0;
    ihdr[12] = 0;
    if (fwrite(sig, 1, 8, f) != 8u || put_chunk(f, "IHDR", ihdr, 13u) != 0 ||
        put_chunk(f, "IDAT", z, zlen) != 0 || put_chunk(f, "IEND", NULL, 0u) != 0) {
        rc = -2;
    }
    if (fclose(f) != 0) {
        rc = -2;
    }
    return rc;
}

int azh_png_write(const char *path, const uint8_t *px, uint32_t w, uint32_t h, size_t stride)
{
    size_t raw_len;
    uLongf z_len;
    uint8_t *raw;
    uint8_t *z;
    int rc;

    if (path == NULL || px == NULL || w == 0u || h == 0u || w > PNG_MAX_DIM || h > PNG_MAX_DIM ||
        stride < (size_t)w * 4u || crc_ready == 0) {
        return -1;
    }
    raw_len = ((size_t)w * 4u + 1u) * h;
    z_len = compressBound((uLong)raw_len);
    raw = malloc(raw_len);
    z = malloc((size_t)z_len);
    if (raw == NULL || z == NULL) {
        free(raw);
        free(z);
        return -2;
    }
    fill_rows(raw, px, w, h, stride);
    if (compress2(z, &z_len, raw, (uLong)raw_len, PNG_LEVEL) != Z_OK) {
        rc = -2;
    } else {
        rc = write_file(path, z, (size_t)z_len, w, h);
    }
    free(raw);
    free(z);
    return rc;
}
