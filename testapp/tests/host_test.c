// SPDX-License-Identifier: GPL-3.0-or-later
// Host test of control parsing and the record/log-line formats. Build: see tests/gate-b.sh.
#include <stdio.h>
#include <string.h>

#include "../source/control.h"
#include "../source/record.h"

static int g_fail;

static void check(int ok, const char *what)
{
    if (!ok) {
        printf("host_test FAIL: %s\n", what);
        g_fail = 1;
    }
}

static uint32_t parse(const char *text, laz_control *ctl)
{
    return control_parse(text, (uint32_t)strlen(text), ctl);
}

static void test_control(void)
{
    laz_control c;
    check(parse("", &c) == 0 && c.mode3d == 0 && c.break_at == 0 && c.boot_frames == 0, "empty is defaults");
    check(control_parse(NULL, 0, &c) == 0 && c.exit_at == 0, "no file is defaults");
    check(parse("draw=3d\nbreak_at=120\nexit_at=5\nready_at=60\nboot_frames=90\n", &c) == 0, "good keys parse");
    check(c.mode3d == 1 && c.break_at == 120 && c.exit_at == 5 && c.ready_at == 60 && c.boot_frames == 90,
          "good key values");
    check(parse("# comment\n\ndraw=2d\r\nbreak_at=7", &c) == 0 && c.break_at == 7 && c.mode3d == 0,
          "comment, blank, CRLF, no final newline");
    check(parse("bogus=1\nbreak_at=3\n", &c) == 1 && c.error_line[0] == 1 && c.break_at == 3, "unknown key");
    check(parse("break_at=0\nexit_at=1000001\nboot_frames=10001\nready_at=abc\ndraw=4d\n", &c) == 5 &&
              c.break_at == 0 && c.exit_at == 0 && c.boot_frames == 0 && c.ready_at == 0 && c.error_line[4] == 5,
          "out-of-range and bad values keep defaults");
    check(parse("break_at=\nnoequals\n", &c) == 2, "empty value and no equals");
    check(parse("break_at=1000000\nboot_frames=10000\n", &c) == 0 && c.break_at == 1000000u && c.boot_frames == 10000u,
          "upper bounds accepted");
    char longline[96];
    memset(longline, 'a', sizeof(longline) - 1);
    longline[sizeof(longline) - 1] = '\0';
    check(parse(longline, &c) == 1, "line over 64 bytes");
    char many[256];
    many[0] = '\0';
    for (int i = 0; i < 17; i++) {
        strcat(many, "# x\n");
    }
    strcat(many, "break_at=9\n");
    check(parse(many, &c) == 1 && c.break_at == 0 && c.error_line[0] == 18, "line 18 is past the 16-line limit");
}

static void test_record(void)
{
    laz_record r;
    char buf[LAZ_LOG_LINE_MAX];
    record_fill(&r, 7, 8, 0x100000u | 0x1u, 12, 34, -5, 6, 99);
    check(sizeof(r) == 32 && r.magic == 0x4C415A52u, "record size and magic");
    check(record_fmt_frame(buf, sizeof(buf), &r, 1234) > 0, "frame line fits");
    check(strcmp(buf, "f=7 v=8 s=99 t=1234 k=00100001 tx=12 ty=34 td=1 cx=-5 cy=6\n") == 0, "frame line format");
    check(record_fmt_start(buf, sizeof(buf), 0x1000, 0x2000, 32, 1, 1, 2, 3, 4) > 0, "start fits");
    check(strcmp(buf, "start addr_global=0x00001000 addr_heap=0x00002000 size=32 mode=3d break_at=1 exit_at=2 "
                      "ready_at=3 boot_frames=4\n") == 0, "start line format");
    check(record_fmt_event(buf, sizeof(buf), "break", 120, 121) > 0 && strcmp(buf, "break f=120 v=121\n") == 0,
          "event line format");
    check(record_fmt_booted(buf, sizeof(buf), 90, 91, 0xBEEF) > 0 && strcmp(buf, "booted f=90 v=91 sum=0000beef\n") == 0,
          "booted line format");
    check(record_fmt_control_error(buf, sizeof(buf), 3) > 0 && strcmp(buf, "control error line=3\n") == 0,
          "control error format");
    check(record_fmt_spin_cap(buf, sizeof(buf), 4) > 0 && strcmp(buf, "boot spin cap f=4\n") == 0, "spin cap format");
    check(record_fmt_event(buf, 4, "break", 1, 1) == 0, "too-small buffer returns 0");
}

int main(void)
{
    test_control();
    test_record();
    if (g_fail) {
        return 1;
    }
    printf("host_test ok\n");
    return 0;
}
