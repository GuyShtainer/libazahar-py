/* log.c: host.log. One mutex, one write() per line, level threshold from LAZ_LOG_LEVEL (default info).
 * The core logs from several threads, so every line is formatted into a local buffer first. */
#include <assert.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "azh_internal.h"

#define LOG_LINE_MAX 2048

static int log_fd = -1;
static int threshold = AZH_LOG_INFO;
static pthread_mutex_t log_mx = PTHREAD_MUTEX_INITIALIZER;
static int dbg_armed;                   /* atomic */
static int dbg_hit;                     /* atomic */
static char dbg_text[256];

static int parse_level(const char *s)
{
    assert(s != NULL);
    if (strcmp(s, "debug") == 0 || strcmp(s, "0") == 0) {
        return AZH_LOG_DEBUG;
    }
    if (strcmp(s, "warn") == 0 || strcmp(s, "2") == 0) {
        return AZH_LOG_WARN;
    }
    if (strcmp(s, "error") == 0 || strcmp(s, "3") == 0) {
        return AZH_LOG_ERROR;
    }
    return AZH_LOG_INFO;
}

int azh_log_open(const char *path)
{
    const char *lv = getenv("LAZ_LOG_LEVEL");
    int fd;

    assert(path != NULL);
    fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_BINARY, 0644);
    if (fd < 0) {
        return -1;
    }
    (void)pthread_mutex_lock(&log_mx);
    log_fd = fd;
    threshold = (lv != NULL) ? parse_level(lv) : AZH_LOG_INFO;
    (void)pthread_mutex_unlock(&log_mx);
    return 0;
}

void azh_log_close(void)
{
    (void)pthread_mutex_lock(&log_mx);
    if (log_fd >= 0) {
        (void)close(log_fd);     /* nothing useful to do if close fails */
        log_fd = -1;
    }
    (void)pthread_mutex_unlock(&log_mx);
}

/* format "[level] text\n" in one buffer, mark truncation, write it in one call */
static void emit(int level, const char *fmt, va_list ap)
{
    static const char *const names[4] = { "debug", "info", "warn", "error" };
    char buf[LOG_LINE_MAX];
    int head;
    int n;
    size_t len;

    assert(fmt != NULL);
    if (level < 0) {
        level = 0;
    }
    if (level > AZH_LOG_ERROR) {
        level = AZH_LOG_ERROR;
    }
    head = snprintf(buf, sizeof buf, "[%s] ", names[level]);
    if (head < 0 || (size_t)head >= sizeof buf) {
        return;
    }
    n = vsnprintf(buf + head, sizeof buf - (size_t)head - 2u, fmt, ap);
    if (n < 0) {
        return;
    }
    len = (size_t)head + (size_t)n;
    if (len >= sizeof buf - 2u) {
        len = sizeof buf - 2u;
        memcpy(buf + len - 14u, "...[truncated]", 14u);
    }
    while (len > (size_t)head && buf[len - 1u] == '\n') {
        len--;
    }
    buf[len++] = '\n';
    (void)pthread_mutex_lock(&log_mx);
    if (log_fd >= 0 && level >= threshold) {
        (void)write(log_fd, buf, len);     /* a failed log write has nowhere to be reported */
    }
    (void)pthread_mutex_unlock(&log_mx);
}

void azh_log(int level, const char *fmt, ...)
{
    va_list ap;

    va_start(ap, fmt);
    emit(level, fmt, ap);
    va_end(ap);
}

/* Azahar's backend passes the finished guest line as the FORMAT string (backend.cpp:97-98), so a '%' in guest
 * text must never be interpreted: the string is logged as the argument of "%s", and the arguments the core may
 * have passed are ignored. The threshold is checked first so filtered lines cost nothing. */
void azh_core_log(enum retro_log_level level, const char *fmt, ...)
{
    if (fmt == NULL) {
        return;
    }
    if (__atomic_load_n(&dbg_armed, __ATOMIC_ACQUIRE) != 0 && strstr(fmt, dbg_text) != NULL) {
        __atomic_store_n(&dbg_hit, 1, __ATOMIC_RELEASE);     /* whatever the line's level */
    }
    if ((int)level < threshold) {
        return;
    }
    azh_log((int)level, "%s", fmt);
}

/* the debug-text observer (our core only): armed by azh_run for one batch, a hit sets a flag the batch loop reads. The
 * core's lines arrive whole, so no carry. The arm order (flag off, text, flag on) keeps a reader on another thread
 * from seeing a half-written text. */
void azh__log_set_debug_stop(const char *text_or_null)
{
    __atomic_store_n(&dbg_armed, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&dbg_hit, 0, __ATOMIC_RELEASE);
    if (text_or_null != NULL && text_or_null[0] != '\0') {
        (void)snprintf(dbg_text, sizeof dbg_text, "%s", text_or_null);
        __atomic_store_n(&dbg_armed, 1, __ATOMIC_RELEASE);
    }
}

int azh__log_debug_hit(void)
{
    return __atomic_load_n(&dbg_hit, __ATOMIC_ACQUIRE);
}

int azh__log_fd(void)
{
    return log_fd;
}
