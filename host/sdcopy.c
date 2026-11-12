/* sdcopy.c: copy and clear a folder tree for SD seeding (POSIX fts and macOS copyfile only, no libretro).
 * Regular files and folders only: a symlink or anything else is refused. At most AZH_TREE_MAX entries. */
#include <assert.h>
#include <copyfile.h>
#include <errno.h>
#include <fts.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "azh_internal.h"

#define AZH_TREE_MAX 100000

/* a writable copy of a path without trailing slashes */
static int clean_path(const char *in, char *out, size_t cap)
{
    size_t n;

    assert(in != NULL && out != NULL && cap > 1u);
    n = strnlen(in, cap);
    if (n == 0u || n >= cap) {
        return AZH_E_ARG;
    }
    memcpy(out, in, n + 1u);
    while (n > 1u && out[n - 1u] == '/') {
        out[--n] = '\0';
    }
    return AZH_OK;
}

static int copy_entry(const FTSENT *e, const char *src, const char *dst)
{
    char to[PATH_MAX];
    int n;

    assert(e != NULL && strlen(e->fts_path) >= strlen(src));
    n = snprintf(to, sizeof to, "%s%s", dst, e->fts_path + strlen(src));
    if (n < 0 || (size_t)n >= sizeof to) {
        return AZH_E_ARG;
    }
    if (e->fts_info == FTS_D) {
        return (mkdir(to, 0755) == 0) ? AZH_OK : AZH_E_IO;
    }
    if (e->fts_info == FTS_F) {     /* an APFS clone where possible, a plain copy otherwise */
        return (copyfile(e->fts_path, to, NULL, COPYFILE_ALL | COPYFILE_CLONE) == 0) ? AZH_OK : AZH_E_IO;
    }
    if (e->fts_info == FTS_DP) {
        return AZH_OK;
    }
    return AZH_E_ARG;               /* symlink, device, socket, unreadable: refused */
}

int azh__copy_tree(const char *src, const char *dst)
{
    char s[PATH_MAX];
    char d[PATH_MAX];
    char *const roots[2] = { s, NULL };
    struct stat st;
    FTS *fts;
    FTSENT *e;
    int rc = AZH_OK;
    int count = 0;

    assert(src != NULL && dst != NULL);
    if (clean_path(src, s, sizeof s) != AZH_OK || clean_path(dst, d, sizeof d) != AZH_OK) {
        return AZH_E_ARG;
    }
    if (lstat(d, &st) == 0 || errno != ENOENT) {
        return AZH_E_ARG;           /* the destination must not exist */
    }
    if (lstat(s, &st) != 0 || !S_ISDIR(st.st_mode)) {
        return AZH_E_ARG;
    }
    fts = fts_open(roots, FTS_PHYSICAL | FTS_NOCHDIR, NULL);
    if (fts == NULL) {
        return AZH_E_IO;
    }
    while (rc == AZH_OK && (e = fts_read(fts)) != NULL) {
        rc = (++count > AZH_TREE_MAX) ? AZH_E_ARG : copy_entry(e, s, d);
    }
    if (fts_close(fts) != 0 && rc == AZH_OK) {
        rc = AZH_E_IO;
    }
    return rc;
}

static int clear_entry(const FTSENT *e)
{
    assert(e != NULL);
    if (e->fts_level == 0) {
        return AZH_OK;              /* the folder itself stays */
    }
    if (e->fts_info == FTS_DP) {
        return (rmdir(e->fts_path) == 0) ? AZH_OK : AZH_E_IO;
    }
    if (e->fts_info == FTS_D) {
        return AZH_OK;
    }
    return (unlink(e->fts_path) == 0) ? AZH_OK : AZH_E_IO;
}

int azh__clear_tree(const char *dir)
{
    char p[PATH_MAX];
    char *const roots[2] = { p, NULL };
    FTS *fts;
    FTSENT *e;
    int rc = AZH_OK;
    int count = 0;

    assert(dir != NULL);
    if (clean_path(dir, p, sizeof p) != AZH_OK || strcmp(p, "/") == 0) {
        return AZH_E_ARG;
    }
    fts = fts_open(roots, FTS_PHYSICAL | FTS_NOCHDIR, NULL);
    if (fts == NULL) {
        return AZH_E_IO;
    }
    while (rc == AZH_OK && (e = fts_read(fts)) != NULL) {
        rc = (++count > AZH_TREE_MAX) ? AZH_E_ARG : clear_entry(e);
    }
    if (fts_close(fts) != 0 && rc == AZH_OK) {
        rc = AZH_E_IO;
    }
    return rc;
}
