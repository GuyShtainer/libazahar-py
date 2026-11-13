// SPDX-License-Identifier: GPL-3.0-or-later
#include "control.h"

#include <assert.h>
#include <string.h>

enum { LAZ_MAX_VALUE_DIGITS = 8 };

void control_defaults(laz_control *ctl)
{
    if (ctl == NULL) {
        return;
    }
    memset(ctl, 0, sizeof(*ctl));
}

// Parse decimal digits only; accept lo..hi. Returns 1 on success.
static int parse_number(const char *s, uint32_t n, uint32_t lo, uint32_t hi, uint32_t *out)
{
    uint32_t value = 0;
    if (s == NULL || out == NULL || n == 0 || n > LAZ_MAX_VALUE_DIGITS) {
        return 0;
    }
    for (uint32_t i = 0; i < n; i++) {
        if (s[i] < '0' || s[i] > '9') {
            return 0;
        }
        value = value * 10u + (uint32_t)(s[i] - '0');
    }
    if (value < lo || value > hi) {
        return 0;
    }
    *out = value;
    return 1;
}

static int key_is(const char *key, uint32_t klen, const char *name)
{
    return strlen(name) == klen && memcmp(key, name, klen) == 0;
}

// Apply one "key=value" line (no newline). Returns 1 if accepted.
static int apply_line(const char *line, uint32_t n, laz_control *ctl)
{
    const char *eq = memchr(line, '=', n);
    if (eq == NULL || ctl == NULL) {
        return 0;
    }
    const uint32_t klen = (uint32_t)(eq - line);
    assert(klen < n);
    const char *val = eq + 1;
    const uint32_t vlen = n - klen - 1u;
    if (key_is(line, klen, "draw")) {
        if (vlen == 2 && memcmp(val, "2d", 2) == 0) {
            ctl->mode3d = 0;
            return 1;
        }
        if (vlen == 2 && memcmp(val, "3d", 2) == 0) {
            ctl->mode3d = 1;
            return 1;
        }
        return 0;
    }
    if (key_is(line, klen, "break_at")) {
        return parse_number(val, vlen, 1, 1000000u, &ctl->break_at);
    }
    if (key_is(line, klen, "exit_at")) {
        return parse_number(val, vlen, 1, 1000000u, &ctl->exit_at);
    }
    if (key_is(line, klen, "ready_at")) {
        return parse_number(val, vlen, 1, 1000000u, &ctl->ready_at);
    }
    if (key_is(line, klen, "boot_frames")) {
        return parse_number(val, vlen, 1, 10000u, &ctl->boot_frames);
    }
    if (key_is(line, klen, "stencil")) {
        return parse_number(val, vlen, 1, 4u, &ctl->stencil);
    }
    return 0;
}

static void add_error(laz_control *ctl, uint32_t line_no)
{
    assert(ctl != NULL && line_no >= 1);
    if (ctl->error_count < LAZ_CONTROL_MAX_LINES + 1u) {
        ctl->error_line[ctl->error_count] = line_no;
    }
    ctl->error_count++;
}

// Handle one line: comment/blank lines are skipped, others applied or recorded as errors.
static void handle_line(const char *line, uint32_t n, uint32_t line_no, laz_control *ctl)
{
    assert(line != NULL && ctl != NULL);
    if (n > 0 && line[n - 1u] == '\r') {
        n--;
    }
    if (n == 0 || line[0] == '#') {
        return;
    }
    if (line_no > LAZ_CONTROL_MAX_LINES || n > LAZ_CONTROL_MAX_LINE_BYTES || !apply_line(line, n, ctl)) {
        add_error(ctl, line_no);
    }
}

uint32_t control_parse(const char *text, uint32_t len, laz_control *ctl)
{
    if (ctl == NULL) {
        return 0;
    }
    control_defaults(ctl);
    if (text == NULL) {
        return 0;
    }
    uint32_t start = 0;
    uint32_t line_no = 1;
    for (uint32_t i = 0; i <= len; i++) {
        if (i == len || text[i] == '\n') {
            if (i > start || i < len) {
                handle_line(text + start, i - start, line_no, ctl);
            }
            start = i + 1u;
            line_no++;
        }
    }
    return ctl->error_count;
}
