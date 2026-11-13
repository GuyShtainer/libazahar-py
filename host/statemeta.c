/* statemeta.c (pure): the savestate meta file, `key=value` lines (docs/plans/phase-d.md 3.1).
 * Strict on read: every key exactly once, no unknown key, integers checked with strtoll, text values refused when
 * they do not fit, app_sha256 exactly 64 lowercase hex digits. Includes only the pure header and libc. */
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "azh_pure.h"

#define META_MAX 8192                  /* bytes; a real meta is under 1.5 KiB (app up to 1023 bytes) */
#define META_KEYS 8
#define SHA_HEX 64

enum { K_ABI, K_K, K_FRAME_TOTAL, K_VBLANKS_TOTAL, K_CREATED, K_CORE_VERSION, K_APP, K_APP_SHA256 };

static const char *const key_names[META_KEYS] = { "abi", "k", "frame_total", "vblanks_total", "created",
                                                  "core_version", "app", "app_sha256" };

static int is_lower_hex(char c)
{
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
}

static int sha_ok(const char *s)
{
    int i;

    assert(s != NULL);
    if (strnlen(s, SHA_HEX + 1) != (size_t)SHA_HEX) {
        return 0;
    }
    for (i = 0; i < SHA_HEX; i++) {
        if (!is_lower_hex(s[i])) {
            return 0;
        }
    }
    return 1;
}

int azh__meta_format(const azh_state_meta *m, char *buf, size_t cap)
{
    int n;

    assert(m != NULL && buf != NULL && cap > 0u);
    if (m->abi < 0 || m->k < 0 || m->frame_total < 0 || m->vblanks_total < 0 || m->created < 0) {
        return AZH_E_ARG;
    }
    if (memchr(m->core_version, '\0', sizeof m->core_version) == NULL ||
        memchr(m->app, '\0', sizeof m->app) == NULL || !sha_ok(m->app_sha256)) {
        return AZH_E_ARG;
    }
    if (strpbrk(m->core_version, "\r\n") != NULL || strpbrk(m->app, "\r\n") != NULL) {
        return AZH_E_ARG;
    }
    n = snprintf(buf, cap, "abi=%d\nk=%d\nframe_total=%lld\nvblanks_total=%lld\ncreated=%lld\ncore_version=%s\n"
                           "app=%s\napp_sha256=%s\n",
                 (int)m->abi, (int)m->k, (long long)m->frame_total, (long long)m->vblanks_total,
                 (long long)m->created, m->core_version, m->app, m->app_sha256);
    if (n < 0 || (size_t)n >= cap) {
        return AZH_E_ARG;
    }
    return n;
}

/* a whole-string integer in [lo, hi] */
static int parse_int(const char *v, long long lo, long long hi, long long *out)
{
    char *end = NULL;
    long long x;

    assert(v != NULL && out != NULL);
    if (*v == '\0' || *v == ' ' || *v == '+') {
        return 0;
    }
    errno = 0;
    x = strtoll(v, &end, 10);
    if (errno != 0 || end == v || *end != '\0' || x < lo || x > hi) {
        return 0;
    }
    *out = x;
    return 1;
}

static int copy_text(char *dst, size_t cap, const char *v)
{
    size_t n;

    assert(dst != NULL && v != NULL && cap > 1u);
    n = strlen(v);
    if (n >= cap) {
        return 0;
    }
    memcpy(dst, v, n + 1u);
    return 1;
}

/* store one value into t; 1 on success */
static int store_value(azh_state_meta *t, int key, const char *v)
{
    long long x = 0;

    assert(t != NULL && key >= 0 && key < META_KEYS);
    switch (key) {
    case K_ABI:
        if (!parse_int(v, 0, 0x7fffffffLL, &x)) {
            return 0;
        }
        t->abi = (int32_t)x;
        return 1;
    case K_K:
        if (!parse_int(v, 0, 0x7fffffffLL, &x)) {
            return 0;
        }
        t->k = (int32_t)x;
        return 1;
    case K_FRAME_TOTAL:
        return parse_int(v, 0, INT64_MAX, &t->frame_total) ? 1 : 0;
    case K_VBLANKS_TOTAL:
        return parse_int(v, 0, INT64_MAX, &t->vblanks_total) ? 1 : 0;
    case K_CREATED:
        return parse_int(v, 0, INT64_MAX, &t->created) ? 1 : 0;
    case K_CORE_VERSION:
        return copy_text(t->core_version, sizeof t->core_version, v);
    case K_APP:
        return copy_text(t->app, sizeof t->app, v);
    default:
        if (!sha_ok(v)) {
            return 0;
        }
        return copy_text(t->app_sha256, sizeof t->app_sha256, v);
    }
}

/* one line (no newline, NUL-terminated in work) */
static int parse_line(azh_state_meta *t, char *line, unsigned *seen)
{
    char *eq = strchr(line, '=');
    int key;

    assert(t != NULL && line != NULL && seen != NULL);
    if (eq == NULL) {
        return 0;
    }
    *eq = '\0';
    for (key = 0; key < META_KEYS; key++) {
        if (strcmp(line, key_names[key]) == 0) {
            break;
        }
    }
    if (key == META_KEYS || (*seen & (1u << key)) != 0u) {
        return 0;               /* unknown or repeated key */
    }
    if (!store_value(t, key, eq + 1)) {
        return 0;
    }
    *seen |= 1u << key;
    return 1;
}

int azh__meta_parse(const char *text, size_t len, azh_state_meta *m)
{
    static const unsigned all = (1u << META_KEYS) - 1u;
    char work[META_MAX + 1];
    azh_state_meta t;
    unsigned seen = 0u;
    char *line;
    char *nl;
    int guard;

    assert(text != NULL && m != NULL && len < (size_t)1 << 30);
    if (len == 0u || len > (size_t)META_MAX || text[len - 1u] != '\n' || memchr(text, '\0', len) != NULL) {
        return AZH_E_SAVESTATE;
    }
    memcpy(work, text, len);
    work[len] = '\0';
    memset(&t, 0, sizeof t);
    line = work;
    for (guard = 0; guard <= META_KEYS && *line != '\0'; guard++) {
        nl = strchr(line, '\n');
        if (nl == NULL) {
            return AZH_E_SAVESTATE;
        }
        *nl = '\0';
        if (!parse_line(&t, line, &seen)) {
            return AZH_E_SAVESTATE;
        }
        line = nl + 1;
    }
    if (*line != '\0' || seen != all) {
        return AZH_E_SAVESTATE;         /* more lines than keys, or a key missing */
    }
    *m = t;
    return AZH_OK;
}

/* write all of buf to fd; bounded by the byte count (a write that returns 0 is a failure) */
static int write_all(int fd, const char *buf, size_t n)
{
    size_t done = 0u;
    ssize_t w;

    assert(fd >= 0 && buf != NULL);
    while (done < n) {
        w = write(fd, buf + done, n - done);
        if (w <= 0) {
            if (w < 0 && errno == EINTR) {
                continue;
            }
            return AZH_E_IO;
        }
        done += (size_t)w;
    }
    return AZH_OK;
}

static int fsync_path(const char *path)
{
    int fd;
    int rc;

    assert(path != NULL);
    fd = open(path, O_RDONLY | O_BINARY);
    if (fd < 0) {
        return AZH_E_IO;
    }
    rc = (fsync(fd) == 0) ? AZH_OK : AZH_E_IO;
    if (close(fd) != 0) {
        rc = AZH_E_IO;
    }
    return rc;
}

/* <tmp> holds the bytes, fsynced and closed; 0 or AZH_E_IO */
static int write_tmp(const char *tmp, const char *buf, size_t n)
{
    int fd;
    int rc;

    assert(tmp != NULL && buf != NULL);
    fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC | O_BINARY, 0644);
    if (fd < 0) {
        return AZH_E_IO;
    }
    rc = write_all(fd, buf, n);
    if (rc == AZH_OK && fsync(fd) != 0) {
        rc = AZH_E_IO;
    }
    if (close(fd) != 0) {
        rc = AZH_E_IO;
    }
    return rc;
}

int azh__meta_write(const char *path, const azh_state_meta *m)
{
    char buf[META_MAX];
    char tmp[AZH_PATH_MAX + 8];
    int n;
    int rc;

    assert(path != NULL && m != NULL);
    n = azh__meta_format(m, buf, sizeof buf);
    if (n < 0) {
        return n;
    }
    if (snprintf(tmp, sizeof tmp, "%s.tmp", path) >= (int)sizeof tmp) {
        return AZH_E_ARG;
    }
    rc = write_tmp(tmp, buf, (size_t)n);
    if (rc != AZH_OK) {
        (void)unlink(tmp);
        return rc;
    }
    if (rename(tmp, path) != 0) {
        (void)unlink(tmp);
        return AZH_E_IO;
    }
    return fsync_path(path);
}

int azh__meta_read(const char *path, azh_state_meta *m)
{
    char buf[META_MAX + 1];
    size_t got = 0u;
    ssize_t r = 1;
    int fd;
    int guard;

    assert(path != NULL && m != NULL);
    fd = open(path, O_RDONLY | O_BINARY);
    if (fd < 0) {
        return (errno == ENOENT) ? AZH_E_SAVESTATE : AZH_E_IO;
    }
    for (guard = 0; guard < META_MAX + 2 && r > 0 && got <= (size_t)META_MAX; guard++) {
        r = read(fd, buf + got, (size_t)META_MAX + 1u - got);
        if (r > 0) {
            got += (size_t)r;
        } else if (r < 0 && errno == EINTR) {
            r = 1;
        }
    }
    (void)close(fd);
    if (r < 0) {
        return AZH_E_IO;
    }
    if (got > (size_t)META_MAX) {
        return AZH_E_SAVESTATE;
    }
    return azh__meta_parse(buf, got, m);
}
