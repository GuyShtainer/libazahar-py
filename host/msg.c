/* msg.c (pure): the guest-message detector. One SET_MESSAGE text in, one action out (docs/plans/phase-c.md 3.5).
 * The break test reads the full text handed in, never the AZH_MSG_MAX copy: the "Exception Type:" line of a status 14
 * can sit past byte 200. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"
#ifdef _WIN32
#include "plat/win_compat.h"
#else
#define AZH_O_BINARY 0
#endif

#define SCAN_MAX 1048576u
#define FATAL_PREFIX "Fatal Error encountered ("

int azh__msg_status(const char *text)
{
    size_t p = sizeof FATAL_PREFIX - 1u;
    int n = 0;
    int digits = 0;

    assert(text != NULL);
    if (strncmp(text, FATAL_PREFIX, p) != 0) {
        return AZH_MSG_OTHER;
    }
    while (digits < 4 && text[p] >= '0' && text[p] <= '9') {
        n = n * 10 + (text[p] - '0');
        p++;
        digits++;
    }
    if (digits < 1 || digits > 3 || text[p] != ')') {
        return AZH_MSG_OTHER;
    }
    return n;
}

int azh__msg_is_break(const char *text)
{
    static const char needle[] = "Exception Type: Break";
    size_t len;

    assert(text != NULL);
    len = strnlen(text, SCAN_MAX);
    return memmem(text, len, needle, sizeof needle - 1u) != NULL;
}

void azh__msg_begin_run(azh_msgstate *st)
{
    assert(st != NULL);
    st->brk = 0;
    st->err = 0;
    st->exited = 0;
    st->err_count = 0;
    st->first[0] = '\0';
}

/* keep the first message; a message of a stronger kind (exited > error > break) replaces it */
static void keep_first(azh_msgstate *st, const char *text, int rank)
{
    int have = (st->exited != 0) ? 3 : (st->err != 0) ? 2 : (st->brk != 0) ? 1 : 0;

    assert(rank >= 1 && rank <= 3);
    if (have >= rank) {
        return;
    }
    (void)strncpy(st->first, text, AZH_MSG_MAX - 1u);
    st->first[AZH_MSG_MAX - 1u] = '\0';
}

int azh__msg_on_message(azh_msgstate *st, const char *text, int is_lazpy)
{
    int status;

    assert(st != NULL && text != NULL);
    status = azh__msg_status(text);
    if (status == 16) {
        keep_first(st, text, 3);
        st->exited = 1;
        return is_lazpy != 0 ? AZH_ACT_EXITED : AZH_ACT_EXIT_EXITED;
    }
    if (status == 14 && azh__msg_is_break(text) != 0) {
        keep_first(st, text, 1);
        st->brk = 1;
        return AZH_ACT_BREAK;
    }
    keep_first(st, text, 2);
    st->err = 1;
    if (is_lazpy != 0) {
        return AZH_ACT_ERROR;
    }
    st->err_count++;
    return (st->err_count >= 3) ? AZH_ACT_EXIT_ERROR : AZH_ACT_ERROR;
}

void azh__print_escaped(FILE *f, const char *m)
{
    assert(f != NULL && m != NULL);
    for (; *m != '\0'; m++) {
        if (*m == '\\') {
            fputs("\\\\", f);
        } else if (*m == '"') {
            fputs("\\\"", f);
        } else if (*m == '\n') {
            fputs("\\n", f);
        } else if (*m != '\r') {
            fputc(*m, f);
        }
    }
}
