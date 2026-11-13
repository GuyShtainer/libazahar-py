/* plat/win_sdcopy.c: copy and clear a folder tree on Windows, the contract of sdcopy.c (Win32 only, no libretro).
 * Regular files and folders only: a reparse point (symlink or junction) or anything else is refused as AZH_E_ARG.
 * At most AZH_TREE_MAX entries; the destination of a copy must not exist; clear keeps the folder itself. */
#ifdef _WIN32
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include <windows.h>

#include "azh_internal.h"

#define AZH_TREE_MAX 100000
#define TREE_DEPTH_MAX 32                /* folders deep; each level holds two path buffers */

typedef struct {
    int count;                           /* entries visited so far */
} walk_t;

/* a writable copy of a path without trailing slashes (a bare "C:" or "C:\" keeps its slash) */
static int clean_path(const char *in, char *out, size_t cap)
{
    size_t n;

    assert(in != NULL && out != NULL && cap > 1u);
    n = strnlen(in, cap);
    if (n == 0u || n >= cap) {
        return AZH_E_ARG;
    }
    memcpy(out, in, n + 1u);
    while (n > 1u && (out[n - 1u] == '/' || out[n - 1u] == '\\') && !(n == 3u && out[1] == ':')) {
        out[--n] = '\0';
    }
    return AZH_OK;
}

static int is_root(const char *p)
{
    assert(p != NULL);
    return strcmp(p, "/") == 0 || strcmp(p, "\\") == 0 ||
           (strlen(p) <= 3u && p[0] != '\0' && p[1] == ':' && (p[2] == '\0' || p[2] == '/' || p[2] == '\\'));
}

/* 1 when the path exists (any kind); *attr gets its attributes */
static int exists(const char *p, DWORD *attr)
{
    DWORD a;

    assert(p != NULL && attr != NULL);
    a = GetFileAttributesA(p);
    *attr = a;
    return a != INVALID_FILE_ATTRIBUTES;
}

static int join(char *out, size_t cap, const char *dir, const char *name)
{
    int n;

    assert(out != NULL && dir != NULL && name != NULL);
    n = snprintf(out, cap, "%s\\%s", dir, name);
    return (n > 0 && (size_t)n < cap) ? AZH_OK : AZH_E_ARG;
}

static int dots(const char *name)
{
    assert(name != NULL);
    return strcmp(name, ".") == 0 || strcmp(name, "..") == 0;
}

static int copy_dir(const char *src, const char *dst, int depth, walk_t *w);

static int copy_entry(const WIN32_FIND_DATAA *fd, const char *src, const char *dst, int depth, walk_t *w)
{
    char from[AZH_PATH_MAX];
    char to[AZH_PATH_MAX];

    assert(fd != NULL && w != NULL);
    if (join(from, sizeof from, src, fd->cFileName) != AZH_OK || join(to, sizeof to, dst, fd->cFileName) != AZH_OK) {
        return AZH_E_ARG;
    }
    if ((fd->dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0u) {
        return AZH_E_ARG;               /* symlink or junction: refused */
    }
    if ((fd->dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0u) {
        return copy_dir(from, to, depth + 1, w);
    }
    if ((fd->dwFileAttributes & (FILE_ATTRIBUTE_DEVICE)) != 0u) {
        return AZH_E_ARG;
    }
    return CopyFileA(from, to, TRUE) != 0 ? AZH_OK : AZH_E_IO;
}

static int copy_dir(const char *src, const char *dst, int depth, walk_t *w)
{
    char pat[AZH_PATH_MAX];
    WIN32_FIND_DATAA fd;
    HANDLE h;
    int rc = AZH_OK;

    assert(src != NULL && dst != NULL && w != NULL);
    if (depth > TREE_DEPTH_MAX || join(pat, sizeof pat, src, "*") != AZH_OK) {
        return AZH_E_ARG;
    }
    if (CreateDirectoryA(dst, NULL) == 0) {
        return AZH_E_IO;
    }
    h = FindFirstFileA(pat, &fd);
    if (h == INVALID_HANDLE_VALUE) {
        return AZH_E_IO;
    }
    do {
        if (dots(fd.cFileName)) {
            continue;
        }
        rc = (++w->count > AZH_TREE_MAX) ? AZH_E_ARG : copy_entry(&fd, src, dst, depth, w);
    } while (rc == AZH_OK && FindNextFileA(h, &fd) != 0);
    (void)FindClose(h);
    return rc;
}

int azh__copy_tree(const char *src, const char *dst)
{
    char s[AZH_PATH_MAX];
    char d[AZH_PATH_MAX];
    DWORD attr;
    walk_t w = { 0 };

    assert(src != NULL && dst != NULL);
    if (clean_path(src, s, sizeof s) != AZH_OK || clean_path(dst, d, sizeof d) != AZH_OK) {
        return AZH_E_ARG;
    }
    if (exists(d, &attr) || (GetLastError() != ERROR_FILE_NOT_FOUND && GetLastError() != ERROR_PATH_NOT_FOUND)) {
        return AZH_E_ARG;               /* the destination must not exist */
    }
    if (!exists(s, &attr) || (attr & FILE_ATTRIBUTE_DIRECTORY) == 0u || (attr & FILE_ATTRIBUTE_REPARSE_POINT) != 0u) {
        return AZH_E_ARG;
    }
    return copy_dir(s, d, 0, &w);
}

static int clear_dir(const char *dir, int depth, walk_t *w);

static int clear_entry(const WIN32_FIND_DATAA *fd, const char *dir, int depth, walk_t *w)
{
    char p[AZH_PATH_MAX];
    int is_dir = (fd->dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0u;
    int is_link = (fd->dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0u;

    assert(fd != NULL && w != NULL);
    if (join(p, sizeof p, dir, fd->cFileName) != AZH_OK) {
        return AZH_E_ARG;
    }
    (void)SetFileAttributesA(p, FILE_ATTRIBUTE_NORMAL | (is_dir ? FILE_ATTRIBUTE_DIRECTORY : 0u));
    if (is_dir && !is_link) {
        int rc = clear_dir(p, depth + 1, w);

        return (rc == AZH_OK && RemoveDirectoryA(p) == 0) ? AZH_E_IO : rc;
    }
    if (is_dir) {
        return RemoveDirectoryA(p) != 0 ? AZH_OK : AZH_E_IO;   /* a directory link goes, its target stays */
    }
    return DeleteFileA(p) != 0 ? AZH_OK : AZH_E_IO;
}

static int clear_dir(const char *dir, int depth, walk_t *w)
{
    char pat[AZH_PATH_MAX];
    WIN32_FIND_DATAA fd;
    HANDLE h;
    int rc = AZH_OK;

    assert(dir != NULL && w != NULL);
    if (depth > TREE_DEPTH_MAX || join(pat, sizeof pat, dir, "*") != AZH_OK) {
        return AZH_E_ARG;
    }
    h = FindFirstFileA(pat, &fd);
    if (h == INVALID_HANDLE_VALUE) {
        DWORD e = GetLastError();

        return (e == ERROR_FILE_NOT_FOUND || e == ERROR_PATH_NOT_FOUND) ? AZH_OK : AZH_E_IO;
    }
    do {
        if (dots(fd.cFileName)) {
            continue;
        }
        rc = (++w->count > AZH_TREE_MAX) ? AZH_E_ARG : clear_entry(&fd, dir, depth, w);
    } while (rc == AZH_OK && FindNextFileA(h, &fd) != 0);
    (void)FindClose(h);
    return rc;
}

int azh__clear_tree(const char *dir)
{
    char p[AZH_PATH_MAX];
    walk_t w = { 0 };

    assert(dir != NULL);
    if (clean_path(dir, p, sizeof p) != AZH_OK || is_root(p)) {
        return AZH_E_ARG;
    }
    return clear_dir(p, 0, &w);
}
#endif
