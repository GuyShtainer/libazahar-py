/* test_match.c: the SD text matcher, on in-memory feeds and on files under a mkdtemp folder. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "azh_pure.h"
#include "plat_test.h"
#include "test_main.h"

static char dir[512];
static char file[600];

static int append(const char *data, size_t n, int truncate_first)
{
    FILE *f = fopen(file, truncate_first != 0 ? "wb" : "ab");

    if (f == NULL) {
        return -1;
    }
    if (n > 0u && fwrite(data, 1, n, f) != n) {
        (void)fclose(f);
        return -1;
    }
    return fclose(f);
}

static void test_feed_splits(void)
{
    const char *text = "ready";
    int split;

    for (split = 0; split <= 5; split++) {
        azh_matcher m;
        int a;
        int b;

        check(azh__match_init(&m, text, 0) == AZH_OK, "init");
        a = azh__match_feed(&m, text, (size_t)split);
        b = azh__match_feed(&m, text + split, (size_t)(5 - split));
        check(a == 0 || split == 5, "no early match at split %d", split);
        check((a != 0) || (b != 0), "text split at %d is found", split);
    }
    {
        azh_matcher m;

        check(azh__match_init(&m, "ab", 0) == AZH_OK, "init ab");
        check(azh__match_feed(&m, "xa", 2) == 0 && azh__match_feed(&m, "bx", 2) == 1, "carry across two feeds");
        check(azh__match_feed(&m, "b", 1) == 0, "a seen text is not rediscovered from the carry");
    }
}

static void test_files(void)
{
    azh_matcher m;
    static char big[70000];

    check(azh__match_init(&m, "ready f=", 0) == AZH_OK, "init");
    check(azh__match_poll_file(&m, file) == 0, "missing file: no match");
    check(append("start ok\n", 9, 1) == 0, "write");
    check(azh__match_poll_file(&m, file) == 0, "no text yet");
    check(append("rea", 3, 0) == 0 && azh__match_poll_file(&m, file) == 0, "half the text");
    check(append("dy f=", 5, 0) == 0 && azh__match_poll_file(&m, file) == 1, "text split across two appends");
    check(append("start\n", 6, 1) == 0 && azh__match_poll_file(&m, file) == 0, "shrink restarts, the new file has no text");
    check(append("ready f=1\n", 10, 0) == 0 && azh__match_poll_file(&m, file) == 1, "the recreated file matches");
    memset(big, 'x', sizeof big);
    memcpy(big + 65536 - 4, "ready f=", 8);              /* straddles the 64 KiB chunk boundary */
    check(azh__match_init(&m, "ready f=", 0) == AZH_OK && append(big, sizeof big, 1) == 0, "big file");
    check(azh__match_poll_file(&m, file) == 1, "text across a 64 KiB boundary");
    check(append("old ready f=\n", 13, 1) == 0 && azh__match_init(&m, "ready f=", 13) == AZH_OK, "old text");
    check(azh__match_poll_file(&m, file) == 0, "sd_from_end ignores old text");
    check(append("ready f=\n", 9, 0) == 0 && azh__match_poll_file(&m, file) == 1, "new text after the start offset");
}

static void test_lengths(void)
{
    azh_matcher m;
    char one[2] = "z";
    char long255[256];
    char long256[257];

    memset(long255, 'q', 255);
    long255[255] = '\0';
    memset(long256, 'q', 256);
    long256[256] = '\0';
    check(azh__match_init(&m, one, 0) == AZH_OK && azh__match_feed(&m, "abz", 3) == 1, "length 1");
    check(azh__match_init(&m, long255, 0) == AZH_OK, "length 255");
    check(azh__match_feed(&m, long255, 100) == 0 && azh__match_feed(&m, long255 + 100, 155) == 1, "255 bytes in two feeds");
    check(azh__match_init(&m, long256, 0) == AZH_E_ARG, "length 256 refused");
    check(azh__match_init(&m, "", 0) == AZH_E_ARG, "length 0 refused");
}

void test_match(void)
{
    const char *tmp = getenv("TMPDIR");

    (void)snprintf(dir, sizeof dir, "%s/azh-match-XXXXXX", AZH_TEST_TMPDIR(tmp));
#ifdef _WIN32
    check(azh_test_mkdtemp(dir, sizeof dir) != NULL, "mkdtemp");
#else
    check(mkdtemp(dir) != NULL, "mkdtemp");
#endif
    (void)snprintf(file, sizeof file, "%s/log.txt", dir);
    test_feed_splits();
    test_files();
    test_lengths();
    (void)unlink(file);
    (void)rmdir(dir);
}
