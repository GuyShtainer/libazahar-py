/* test_statemeta.c: the savestate meta format, parse (every failure branch) and the tmp-then-rename write/read. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "azh_pure.h"
#include "plat_test.h"
#include "test_main.h"

#define SHA_A "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

static const char *const keys[8] = { "abi", "k", "frame_total", "vblanks_total", "created", "core_version", "app",
                                     "app_sha256" };

static void sample(azh_state_meta *m)
{
    memset(m, 0, sizeof *m);
    m->abi = AZH_ABI_VERSION;
    m->k = 3;
    m->frame_total = 6003;
    m->vblanks_total = 6010;
    m->created = 1762900000;
    (void)snprintf(m->core_version, sizeof m->core_version, "2126.2");
    (void)snprintf(m->app, sizeof m->app, "/tmp/some dir/testapp.3dsx");
    (void)snprintf(m->app_sha256, sizeof m->app_sha256, "%s", SHA_A);
}

static int same(const azh_state_meta *a, const azh_state_meta *b)
{
    return a->abi == b->abi && a->k == b->k && a->frame_total == b->frame_total &&
           a->vblanks_total == b->vblanks_total && a->created == b->created &&
           strcmp(a->core_version, b->core_version) == 0 && strcmp(a->app, b->app) == 0 &&
           strcmp(a->app_sha256, b->app_sha256) == 0;
}

static int parse_str(const char *s, azh_state_meta *out)
{
    return azh__meta_parse(s, strlen(s), out);
}

static void test_roundtrip(void)
{
    azh_state_meta m, back;
    char buf[8192];
    int n;

    sample(&m);
    n = azh__meta_format(&m, buf, sizeof buf);
    check(n > 0 && (size_t)n == strlen(buf), "format returns the byte count (%d)", n);
    check(azh__meta_parse(buf, (size_t)n, &back) == AZH_OK && same(&m, &back), "format then parse round trip");
    check(azh__meta_format(&m, buf, 20) == AZH_E_ARG, "format into a too small buffer is refused");
    m.k = -1;
    check(azh__meta_format(&m, buf, sizeof buf) == AZH_E_ARG, "format refuses a negative k");
    sample(&m);
    (void)snprintf(m.app, sizeof m.app, "a\nb");
    check(azh__meta_format(&m, buf, sizeof buf) == AZH_E_ARG, "format refuses a newline in a text value");
    sample(&m);
    m.app_sha256[3] = 'G';
    check(azh__meta_format(&m, buf, sizeof buf) == AZH_E_ARG, "format refuses a bad sha");
}

/* every key left out once, and every key doubled once */
static void test_missing_and_double(void)
{
    azh_state_meta m, out;
    char buf[8192], text[8192], line[1200];
    char *p, *q;
    int i, n;

    sample(&m);
    n = azh__meta_format(&m, buf, sizeof buf);
    check(n > 0, "sample formats");
    for (i = 0; i < 8; i++) {
        size_t klen = strlen(keys[i]);

        text[0] = '\0';
        for (p = buf; *p != '\0'; p = q + 1) {
            q = strchr(p, '\n');
            (void)snprintf(line, sizeof line, "%.*s\n", (int)(q - p), p);
            if (strncmp(line, keys[i], klen) == 0 && line[klen] == '=') {
                continue;
            }
            strcat(text, line);
        }
        check(parse_str(text, &out) == AZH_E_SAVESTATE, "missing key %s is refused", keys[i]);
        {
            size_t bl = strlen(buf);

            check(bl + klen + 4 < sizeof text, "doubled-key text fits");
            memcpy(text, buf, bl);
            (void)snprintf(text + bl, sizeof text - bl, "%s=1\n", keys[i]);
        }
        check(parse_str(text, &out) == AZH_E_SAVESTATE, "doubled key %s is refused", keys[i]);
    }
}

static void expect_bad(const char *label, const char *text)
{
    azh_state_meta out;

    memset(&out, 0x5a, sizeof out);
    check(parse_str(text, &out) == AZH_E_SAVESTATE, "%s is refused", label);
    check(out.abi == 0x5a5a5a5a, "%s leaves the output untouched", label);
}

static void test_bad_values(void)
{
    static const char head[] = "abi=2\nk=0\nframe_total=1\nvblanks_total=1\ncreated=1\ncore_version=x\n";
    char text[8192], big[1500];

    expect_bad("empty text", "");
    expect_bad("no final newline", "abi=2\nk=0\nframe_total=1\nvblanks_total=1\ncreated=1\ncore_version=x\napp=y\n"
               "app_sha256=" SHA_A);
    (void)snprintf(text, sizeof text, "%sapp=y\napp_sha256=%s\nextra=1\n", head, SHA_A);
    expect_bad("an unknown key", text);
    (void)snprintf(text, sizeof text, "%sapp=y\napp_sha256=%s\nabi\n", head, SHA_A);
    expect_bad("a line without =", text);
    (void)snprintf(text, sizeof text, "abi=2x\nk=0\nframe_total=1\nvblanks_total=1\ncreated=1\ncore_version=x\n"
                   "app=y\napp_sha256=%s\n", SHA_A);
    expect_bad("a trailing character in an integer", text);
    (void)snprintf(text, sizeof text, "abi=\nk=0\nframe_total=1\nvblanks_total=1\ncreated=1\ncore_version=x\n"
                   "app=y\napp_sha256=%s\n", SHA_A);
    expect_bad("an empty integer", text);
    (void)snprintf(text, sizeof text, "abi=2\nk=-1\nframe_total=1\nvblanks_total=1\ncreated=1\ncore_version=x\n"
                   "app=y\napp_sha256=%s\n", SHA_A);
    expect_bad("a negative k", text);
    (void)snprintf(text, sizeof text, "abi=2\nk=4294967296\nframe_total=1\nvblanks_total=1\ncreated=1\n"
                   "core_version=x\napp=y\napp_sha256=%s\n", SHA_A);
    expect_bad("k beyond int32", text);
    (void)snprintf(text, sizeof text, "abi=2\nk=0\nframe_total=99999999999999999999\nvblanks_total=1\ncreated=1\n"
                   "core_version=x\napp=y\napp_sha256=%s\n", SHA_A);
    expect_bad("frame_total beyond int64", text);
    memset(big, 'a', sizeof big - 1u);
    big[sizeof big - 1u] = '\0';
    (void)snprintf(text, sizeof text, "%sapp=%s\napp_sha256=%s\n", head, big, SHA_A);
    expect_bad("an over-long app", text);
    (void)snprintf(text, sizeof text, "abi=2\nk=0\nframe_total=1\nvblanks_total=1\ncreated=1\ncore_version=%s\n"
                   "app=y\napp_sha256=%s\n", big, SHA_A);
    expect_bad("an over-long core_version", text);
    (void)snprintf(text, sizeof text, "%sapp=y\napp_sha256=%.63s\n", head, SHA_A);
    expect_bad("a 63-digit sha", text);
    (void)snprintf(text, sizeof text, "%sapp=y\napp_sha256=%s0\n", head, SHA_A);
    expect_bad("a 65-digit sha", text);
    (void)snprintf(text, sizeof text, "%sapp=y\napp_sha256=%.63sG\n", head, SHA_A);
    expect_bad("a non-hex sha", text);
    (void)snprintf(text, sizeof text, "%sapp=y\napp_sha256=%.63sA\n", head, SHA_A);
    expect_bad("an upper-case sha", text);
}

static void test_abi_mismatch(void)
{
    azh_state_meta m, out;
    char buf[8192];
    int n;

    sample(&m);
    m.abi = 1;
    n = azh__meta_format(&m, buf, sizeof buf);
    check(n > 0 && azh__meta_parse(buf, (size_t)n, &out) == AZH_OK && out.abi == 1,
          "an old abi parses (the caller compares it with AZH_ABI_VERSION)");
}

static void test_files(void)
{
    char dir[512] = "/tmp/azh-meta-XXXXXX";
    char path[600], tmp[620];
    azh_state_meta m, back;
    FILE *f;

#ifdef _WIN32
    check(azh_test_mkdtemp(dir, sizeof dir) != NULL, "mkdtemp");
#else
    check(mkdtemp(dir) != NULL, "mkdtemp");
#endif
    (void)snprintf(path, sizeof path, "%s/x.meta", dir);
    (void)snprintf(tmp, sizeof tmp, "%s.tmp", path);
    sample(&m);
    check(azh__meta_read(path, &back) == AZH_E_SAVESTATE, "reading a missing meta is AZH_E_SAVESTATE");
    check(azh__meta_write(path, &m) == AZH_OK, "write");
    check(access(tmp, F_OK) != 0, "no .tmp left after the write");
    check(azh__meta_read(path, &back) == AZH_OK && same(&m, &back), "read gives what was written");
    m.k = 7;
    check(azh__meta_write(path, &m) == AZH_OK && azh__meta_read(path, &back) == AZH_OK && back.k == 7,
          "a second write replaces the first");
    f = fopen(path, "w");
    check(f != NULL, "reopen to damage");
    if (f != NULL) {
        (void)fputs("abi=2\nk=0\n", f);
        (void)fclose(f);
    }
    check(azh__meta_read(path, &back) == AZH_E_SAVESTATE, "a truncated file is refused");
    m.abi = -5;
    check(azh__meta_write(path, &m) == AZH_E_ARG && access(tmp, F_OK) != 0, "a bad meta is not written");
    (void)unlink(path);
    (void)rmdir(dir);
    (void)snprintf(path, sizeof path, "%s/nodir/x.meta", dir);
    sample(&m);
    check(azh__meta_write(path, &m) == AZH_E_IO, "writing into a missing folder is AZH_E_IO");
}

void test_statemeta(void)
{
    test_roundtrip();
    test_missing_and_double();
    test_bad_values();
    test_abi_mismatch();
    test_files();
}
