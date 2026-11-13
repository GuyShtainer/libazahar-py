/* plat_test.h: the POSIX calls the unit tests use that mingw-w64 lacks (mkdtemp, mkstemp, symlink, fts, /tmp).
 * Empty on macOS and Linux. Header-only: every function is static and used by at most a few test files. */
#ifndef PLAT_TEST_H
#define PLAT_TEST_H

#ifdef _WIN32
#include <errno.h>
#include <fcntl.h>
#include <io.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <windows.h>

#include "plat/win_compat.h"

/* the temp folder: TMPDIR, else TEMP, else C:\Windows\Temp; "/tmp" in a template means this folder */
static inline const char *azh_test_tmp(void)
{
    const char *t = getenv("TMPDIR");

    if (t == NULL || *t == '\0') {
        t = getenv("TEMP");
    }
    return (t != NULL && *t != '\0') ? t : "C:\\Windows\\Temp";
}

/* tmpl ends in XXXXXX and may start with "/tmp/"; the result is written back into a buffer of cap bytes */
static inline int azh_test_fix_template(char *tmpl, size_t cap)
{
    char out[1024];
    size_t n = strlen(tmpl);

    if (n < 6u || strcmp(tmpl + n - 6u, "XXXXXX") != 0) {
        return -1;
    }
    if (strncmp(tmpl, "/tmp/", 5u) == 0) {
        (void)snprintf(out, sizeof out, "%s\\%s", azh_test_tmp(), tmpl + 5);
        if (strlen(out) >= cap) {
            return -1;
        }
        memcpy(tmpl, out, strlen(out) + 1u);
    }
    return 0;
}

/* a unique name: the six X become letters from the tick count, the pid and a counter; retried on EEXIST */
static inline int azh_test_unique(char *tmpl, int (*make)(const char *))
{
    static unsigned counter;
    size_t n = strlen(tmpl);
    int attempt;

    for (attempt = 0; attempt < 100; attempt++) {
        unsigned v = (unsigned)GetTickCount() * 2654435761u + (unsigned)_getpid() * 40503u + (++counter) * 977u;
        int i;

        for (i = 0; i < 6; i++) {
            tmpl[n - 6u + (size_t)i] = (char)('a' + (v >> (4 * i)) % 26u);
        }
        if (make(tmpl) == 0) {
            return 0;
        }
        if (errno != EEXIST) {
            return -1;
        }
    }
    return -1;
}

static inline int azh_test_make_dir(const char *p)
{
    return azh_win_mkdir(p);
}

/* mkdtemp(buf): the template must sit in a buffer of at least 1024 bytes or be a literal array as in the tests;
 * the tests pass arrays of 256 or more bytes, and "/tmp/azh-meta-XXXXXX" grows by the temp folder's length */
static inline char *azh_test_mkdtemp(char *tmpl, size_t cap)
{
    if (azh_test_fix_template(tmpl, cap) != 0 || azh_test_unique(tmpl, azh_test_make_dir) != 0) {
        return NULL;
    }
    return tmpl;
}

static inline int azh_test_make_file(const char *p)
{
    int fd = _open(p, _O_CREAT | _O_EXCL | _O_RDWR | _O_BINARY, 0600);

    if (fd < 0) {
        return -1;
    }
    (void)_close(fd);
    return 0;
}

/* mkstemp: the file is created, closed and opened again read-write (the tests only close it at once) */
static inline int azh_test_mkstemp(char *tmpl, size_t cap)
{
    if (azh_test_fix_template(tmpl, cap) != 0 || azh_test_unique(tmpl, azh_test_make_file) != 0) {
        return -1;
    }
    return _open(tmpl, _O_RDWR | _O_BINARY);
}

/* a file symlink without admin needs Developer Mode; 0 on success, -1 (the test then skips, with the reason) */
static inline int azh_test_symlink(const char *target, const char *link)
{
    return CreateSymbolicLinkA(link, target, SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE) != 0 ? 0 : -1;
}

/* tmpfile() wants the drive root on Windows (admin): a temporary, delete-on-close file in the temp folder instead */
static inline FILE *azh_test_tmpfile(void)
{
    char *name = _tempnam(azh_test_tmp(), "azh");
    FILE *f = (name != NULL) ? fopen(name, "w+bTD") : NULL;

    free(name);
    return f;
}

#define AZH_TEST_TMPDIR(var) ((var) != NULL ? (var) : azh_test_tmp())
#else
#define azh_test_tmpfile() tmpfile()
#define AZH_TEST_TMPDIR(var) ((var) != NULL ? (var) : "/tmp")
#endif

#endif
