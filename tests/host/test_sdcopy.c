/* test_sdcopy.c: copy and clear of a folder tree. */
#ifndef _WIN32
#include <fts.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "azh_internal.h"
#include "plat_test.h"
#include "test_main.h"

static char root[512];

static void path(char *out, size_t cap, const char *a, const char *b)
{
    (void)snprintf(out, cap, "%s/%s", a, b);
}

static int put(const char *p, const char *data)
{
    FILE *f = fopen(p, "wb");
    size_t n = strlen(data);

    if (f == NULL) {
        return -1;
    }
    if (n > 0u && fwrite(data, 1, n, f) != n) {
        (void)fclose(f);
        return -1;
    }
    return fclose(f);
}

static int same(const char *a, const char *b)
{
    char ba[256];
    char bb[256];
    FILE *fa = fopen(a, "rb");
    FILE *fb = fopen(b, "rb");
    size_t na;
    size_t nb;
    int ok = 0;

    if (fa != NULL && fb != NULL) {
        na = fread(ba, 1, sizeof ba, fa);
        nb = fread(bb, 1, sizeof bb, fb);
        ok = na == nb && memcmp(ba, bb, na) == 0;
    }
    if (fa != NULL) {
        (void)fclose(fa);
    }
    if (fb != NULL) {
        (void)fclose(fb);
    }
    return ok;
}

#ifdef _WIN32
static void rm_all(void)
{
    (void)azh__clear_tree(root);       /* the folder itself is removed by the caller */
}
#else
static void rm_all(void)
{
    char *const roots[2] = { root, NULL };
    FTS *fts = fts_open(roots, FTS_PHYSICAL | FTS_NOCHDIR, NULL);
    FTSENT *e;

    if (fts == NULL) {
        return;
    }
    while ((e = fts_read(fts)) != NULL) {
        if (e->fts_info == FTS_DP) {
            (void)rmdir(e->fts_path);
        } else if (e->fts_info != FTS_D) {
            (void)unlink(e->fts_path);
        }
    }
    (void)fts_close(fts);
}
#endif

void test_sdcopy(void)
{
    const char *tmp = getenv("TMPDIR");
    char src[600], dst[600], p[700], q[700], link[700];
    struct stat st;

    (void)snprintf(root, sizeof root, "%s/azh-sdcopy-XXXXXX", AZH_TEST_TMPDIR(tmp));
#ifdef _WIN32
    check(azh_test_mkdtemp(root, sizeof root) != NULL, "mkdtemp");
#else
    check(mkdtemp(root) != NULL, "mkdtemp");
#endif
    path(src, sizeof src, root, "seed");
    path(dst, sizeof dst, root, "out");
    check(mkdir(src, 0755) == 0, "mkdir seed");
    path(p, sizeof p, src, "a");
    check(mkdir(p, 0755) == 0, "mkdir a");
    path(p, sizeof p, src, "a/b");
    check(mkdir(p, 0755) == 0, "mkdir a/b");
    path(p, sizeof p, src, "a/b/deep.txt");
    check(put(p, "deep text") == 0, "write deep");
    path(p, sizeof p, src, "top.bin");
    check(put(p, "top bytes\n") == 0, "write top");
    check(azh__copy_tree(src, dst) == AZH_OK, "copy_tree of a nested tree");
    path(p, sizeof p, src, "a/b/deep.txt");
    path(q, sizeof q, dst, "a/b/deep.txt");
    check(same(p, q), "deep file matches byte for byte");
    path(p, sizeof p, src, "top.bin");
    path(q, sizeof q, dst, "top.bin");
    check(same(p, q), "top file matches byte for byte");
    check(azh__copy_tree(src, dst) == AZH_E_ARG, "an existing destination is refused");
    path(link, sizeof link, src, "link");
#ifdef _WIN32       /* a file symlink needs Developer Mode (or admin): without it the case is skipped, with the reason */
    if (azh_test_symlink("top.bin", link) != 0) {
        printf("SKIP a symlink is refused: CreateSymbolicLinkA failed (Windows error %lu; Developer Mode is off)\n",
               (unsigned long)GetLastError());
        (void)unlink(link);
    } else {
        path(dst, sizeof dst, root, "out2");
        check(azh__copy_tree(src, dst) == AZH_E_ARG, "a symlink is refused");
    }
#else
    check(symlink("top.bin", link) == 0, "symlink");
    path(dst, sizeof dst, root, "out2");
    check(azh__copy_tree(src, dst) == AZH_E_ARG, "a symlink is refused");
#endif
    path(dst, sizeof dst, root, "out");
    check(azh__clear_tree(dst) == AZH_OK, "clear_tree");
    check(stat(dst, &st) == 0 && S_ISDIR(st.st_mode), "clear_tree keeps the folder");
    path(q, sizeof q, dst, "a");
    check(stat(q, &st) != 0, "clear_tree removed the contents");
    check(azh__clear_tree("/") == AZH_E_ARG, "clear_tree refuses /");
    rm_all();
    (void)rmdir(root);
}
