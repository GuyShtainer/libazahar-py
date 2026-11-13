/* test_profile.c: every file pair of tests/data/profile-cases/ through azh__profile_parse (run from the repo root).
 * <name>.txt is a profile; <name>.expect is the applied key=value lines, or one line "error line N" for a refused
 * file. tests/python/test_profile_format.py runs the same pairs through the Python parser. */
#include <dirent.h>
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"
#include "test_main.h"

#define CASE_DIR "tests/data/profile-cases"
#define OUT_MAX 65536

typedef struct { char out[OUT_MAX]; size_t n; } collect_t;

static int collect_cb(const char *key, const char *value, void *ud)
{
    collect_t *c = ud;
    int n = snprintf(c->out + c->n, OUT_MAX - c->n, "%s=%s\n", key, value);

    if (n < 0 || (size_t)n >= OUT_MAX - c->n) {
        return AZH_E_NOMEM;
    }
    c->n += (size_t)n;
    return 0;
}

/* the file's bytes as text, or -1 when it cannot be opened */
static long slurp(const char *path, char *buf, size_t cap)
{
    FILE *f = fopen(path, "rb");
    size_t n;

    if (f == NULL) {
        return -1;
    }
    n = fread(buf, 1, cap - 1, f);
    buf[n] = '\0';
    (void)fclose(f);
    return (long)n;
}

static void run_case(const char *name)
{
    static collect_t got;
    static char want[OUT_MAX];
    char path[512];
    char err[160];
    int line = 0;
    int rc;

    (void)snprintf(path, sizeof path, "%s/%s.expect", CASE_DIR, name);
    check(slurp(path, want, sizeof want) >= 0, "profile case %s: no .expect file", name);
    (void)snprintf(path, sizeof path, "%s/%s.txt", CASE_DIR, name);
    got.n = 0;
    got.out[0] = '\0';
    rc = azh__profile_parse(path, collect_cb, &got, &line, err, sizeof err);
    if (rc == AZH_OK) {
        check(strcmp(got.out, want) == 0, "profile case %s: applied '%s', want '%s'", name, got.out, want);
    } else {
        char shown[64];

        (void)snprintf(shown, sizeof shown, "error line %d\n", line);
        check(rc == AZH_E_ARG && err[0] != '\0', "profile case %s: rc %d err '%s'", name, rc, err);
        check(strcmp(shown, want) == 0, "profile case %s: got '%s' (%s), want '%s'", name, shown, err, want);
    }
}

static int stop_cb(const char *key, const char *value, void *ud)
{
    (void)key;
    (void)value;
    (void)ud;
    return AZH_E_ARG;
}

static void test_other(void)
{
    char err[160];
    char key[32];
    const char *value = NULL;
    int line = -1;
    int rc;

    rc = azh__profile_parse(CASE_DIR "/no-such-file.txt", collect_cb, NULL, &line, err, sizeof err);
    check(rc == AZH_E_IO && err[0] != '\0', "missing profile: rc %d", rc);
    /* a callback refusal stops the parse, returns its code with err empty and names the line */
    rc = azh__profile_parse(CASE_DIR "/order-and-duplicates.txt", stop_cb, NULL, &line, err, sizeof err);
    check(rc == AZH_E_ARG && err[0] == '\0' && line == 1, "callback refusal: rc %d line %d", rc, line);
    /* the --opt pair rule */
    check(azh__profile_pair("a=b", 3, key, sizeof key, &value, err, sizeof err) == 0 && strcmp(key, "a") == 0 &&
          strcmp(value, "b") == 0, "pair a=b");
    check(azh__profile_pair("", 0, key, sizeof key, &value, err, sizeof err) == 1, "empty pair is a skip");
    check(azh__profile_pair("a b=c", 5, key, sizeof key, &value, err, sizeof err) < 0, "space in key");
    check(azh__profile_pair("abcdefghijklmnopqrstuvwxyz0123456=1", 35, key, sizeof key, &value, err, sizeof err) < 0,
          "key longer than the buffer");
}

void test_profile(void)
{
    DIR *d = opendir(CASE_DIR);
    struct dirent *e;
    int n = 0;

    check(d != NULL, "cannot open %s (run make test-host from the repo root)", CASE_DIR);
    if (d == NULL) {
        return;
    }
    for (e = readdir(d); e != NULL && n < 1000; e = readdir(d)) {
        size_t len = strlen(e->d_name);

        if (len > 4 && strcmp(e->d_name + len - 4, ".txt") == 0) {
            char name[256];

            (void)snprintf(name, sizeof name, "%.*s", (int)(len - 4), e->d_name);
            run_case(name);
            n++;
        }
    }
    (void)closedir(d);
    check(n >= 30, "profile cases found: %d", n);
    test_other();
}
