/* profile.c: the option-profile format (docs/USING.md section 14), one parser for --profile, --lazpy-profile and the
 * pair rule of --opt. Pure: stdio and string only, no libretro or Vulkan. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"

static void set_err(char *err, size_t cap, const char *msg)
{
    assert(err != NULL && msg != NULL);
    assert(cap > 0);
    (void)snprintf(err, cap, "%s", msg);
}

/* strict UTF-8 (what Python's decoder accepts): no overlong form, no surrogate, nothing above U+10FFFF */
static int utf8_ok(const unsigned char *s, size_t len)
{
    size_t i = 0;

    assert(s != NULL);
    while (i < len) {
        unsigned char c = s[i];
        size_t need;
        size_t k;
        unsigned lo = 0x80u;
        unsigned hi = 0xBFu;

        if (c < 0x80u) {
            i++;
            continue;
        }
        if (c >= 0xC2u && c <= 0xDFu) {
            need = 1;
        } else if (c >= 0xE0u && c <= 0xEFu) {
            need = 2;
            lo = (c == 0xE0u) ? 0xA0u : 0x80u;
            hi = (c == 0xEDu) ? 0x9Fu : 0xBFu;
        } else if (c >= 0xF0u && c <= 0xF4u) {
            need = 3;
            lo = (c == 0xF0u) ? 0x90u : 0x80u;
            hi = (c == 0xF4u) ? 0x8Fu : 0xBFu;
        } else {
            return 0;
        }
        if (len - i <= need) {          /* the sequence runs past the end */
            return 0;
        }
        if (s[i + 1] < lo || s[i + 1] > hi) {
            return 0;
        }
        for (k = 2; k <= need; k++) {
            if (s[i + k] < 0x80u || s[i + k] > 0xBFu) {
                return 0;
            }
        }
        i += need + 1u;
    }
    return 1;
}

int azh__profile_pair(const char *line, size_t len, char *key, size_t keycap, const char **value,
                      char *err, size_t cap)
{
    const char *eq;
    size_t klen;

    assert(line != NULL && key != NULL && value != NULL && err != NULL);
    assert(keycap > 0 && cap > 0);
    err[0] = '\0';
    if (len > AZH_PROFILE_LINE_MAX) {
        set_err(err, cap, "line longer than 511 bytes");
        return AZH_E_ARG;
    }
    if (len == 0) {
        return 1;
    }
    if (memchr(line, '\0', len) != NULL) {
        set_err(err, cap, "NUL byte in line");
        return AZH_E_ARG;
    }
    if (len >= 3 && (unsigned char)line[0] == 0xEF && (unsigned char)line[1] == 0xBB &&
        (unsigned char)line[2] == 0xBF) {
        set_err(err, cap, "byte order mark (the file must be UTF-8 without a BOM)");
        return AZH_E_ARG;
    }
    if (!utf8_ok((const unsigned char *)line, len)) {
        set_err(err, cap, "not valid UTF-8");
        return AZH_E_ARG;
    }
    if (line[0] == '#') {
        return 1;                       /* a comment is free text up to the end of its line (still UTF-8) */
    }
    if (line[0] == ' ' || line[0] == '\t' || line[len - 1] == ' ' || line[len - 1] == '\t') {
        set_err(err, cap, "line starts or ends with a space or tab");
        return AZH_E_ARG;
    }
    eq = strchr(line, '=');
    if (eq == NULL) {
        set_err(err, cap, "expected key=value");
        return AZH_E_ARG;
    }
    klen = (size_t)(eq - line);
    if (klen == 0) {
        set_err(err, cap, "empty key");
        return AZH_E_ARG;
    }
    if (memchr(line, ' ', klen) != NULL || memchr(line, '\t', klen) != NULL) {
        set_err(err, cap, "space or tab in key");
        return AZH_E_ARG;
    }
    if (klen >= keycap) {
        set_err(err, cap, "option key too long");
        return AZH_E_ARG;
    }
    memcpy(key, line, klen);
    key[klen] = '\0';
    *value = eq + 1;
    return 0;
}

/* One line into buf (NUL-terminated, the newline and one trailing CR removed).
 * 1: a line; 2: a last line with no newline (the file ended); 0: end of file; -1: longer than AZH_PROFILE_LINE_MAX; -2: read error. */
static int read_line(FILE *f, char *buf, size_t *len)
{
    size_t n = 0;
    int c = fgetc(f);

    assert(f != NULL && buf != NULL && len != NULL);
    while (c != EOF) {
        if (c == '\n') {
            break;
        }
        if (n > AZH_PROFILE_LINE_MAX) {         /* room for 511 bytes and one CR */
            return -1;
        }
        buf[n++] = (char)c;
        c = fgetc(f);
    }
    if (c == EOF && ferror(f) != 0) {
        return -2;
    }
    if (c == EOF && n == 0) {
        return 0;
    }
    if (n > 0 && buf[n - 1] == '\r') {
        n--;
    }
    buf[n] = '\0';
    *len = n;
    if (n > AZH_PROFILE_LINE_MAX) {
        return -1;
    }
    return (c == EOF) ? 2 : 1;
}

int azh__profile_parse(const char *path, int (*cb)(const char *key, const char *value, void *ud), void *ud,
                       int *err_line, char *err, size_t cap)
{
    char buf[AZH_PROFILE_LINE_MAX + 2];
    char key[AZH_PROFILE_LINE_MAX + 1];
    FILE *f;
    int line_no = 0;
    int last = 0;
    int rc = AZH_OK;

    assert(path != NULL && cb != NULL && err_line != NULL && err != NULL);
    assert(cap > 0);
    *err_line = 0;
    err[0] = '\0';
    f = fopen(path, "rb");
    if (f == NULL) {
        (void)snprintf(err, cap, "cannot read profile %s", path);
        return AZH_E_IO;
    }
    while (rc == AZH_OK && last == 0) {
        size_t len = 0;
        const char *value = NULL;
        int got = read_line(f, buf, &len);
        int kind;

        if (got == 0) {
            break;
        }
        line_no++;
        *err_line = line_no;
        if (line_no > AZH_PROFILE_LINES_MAX) {
            set_err(err, cap, "more than 4096 lines");      /* reported at the first line over the bound */
            rc = AZH_E_ARG;
            break;
        }
        last = (got == 2);
        if (got == -2) {
            (void)snprintf(err, cap, "cannot read profile %s", path);
            *err_line = 0;
            rc = AZH_E_IO;
            break;
        }
        if (got == -1) {
            set_err(err, cap, "line longer than 511 bytes");
            rc = AZH_E_ARG;
            break;
        }
        kind = azh__profile_pair(buf, len, key, sizeof key, &value, err, cap);
        if (kind < 0) {
            rc = kind;
        } else if (kind == 0) {
            rc = cb(key, value, ud);
        }
    }
    (void)fclose(f);        /* read-only */
    return rc;
}
