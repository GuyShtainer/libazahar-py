/* test_msg.c: the guest-message detector on messages.txt and on synthetic cases. */
#include <stdio.h>
#include <string.h>

#include "azh_pure.h"
#include "test_main.h"

#define LINE_MAX_LEN 4096
#define MSG_FILE "tests/host/messages.txt"

static const char *const action_names[] = { "NONE", "BREAK", "ERROR", "EXITED", "EXIT_EXITED", "EXIT_ERROR" };

static int action_from_name(const char *n)
{
    int i;

    for (i = 0; i < 6; i++) {
        if (strcmp(n, action_names[i]) == 0) {
            return i;
        }
    }
    return -99;
}

/* decode \n and \\ in place */
static void unescape(char *s)
{
    char *w = s;

    while (*s != '\0') {
        if (s[0] == '\\' && s[1] == 'n') {
            *w++ = '\n';
            s += 2;
        } else if (s[0] == '\\' && s[1] == '\\') {
            *w++ = '\\';
            s += 2;
        } else {
            *w++ = *s++;
        }
    }
    *w = '\0';
}

static int first_action(const char *text, int lazpy)
{
    azh_msgstate st;

    azh__msg_begin_run(&st);
    return azh__msg_on_message(&st, text, lazpy);
}

static void test_file(void)
{
    char line[LINE_MAX_LEN];
    FILE *f = fopen(MSG_FILE, "r");
    int n = 0;

    check(f != NULL, "cannot open " MSG_FILE " (run make test-host from the repo root)");
    if (f == NULL) {
        return;
    }
    while (fgets(line, sizeof line, f) != NULL) {
        int status;
        char stock[32];
        char lazpy[32];
        int off = 0;

        line[strcspn(line, "\n")] = '\0';
        if (line[0] == '#' || line[0] == '\0') {
            continue;
        }
        if (sscanf(line, "%d %31s %31s %n", &status, stock, lazpy, &off) < 3 || off == 0) {
            check(0, "bad line in messages.txt: %s", line);
            continue;
        }
        unescape(line + off);
        n++;
        check(azh__msg_status(line + off) == status, "status of line %d is %d, want %d", n,
              azh__msg_status(line + off), status);
        check(first_action(line + off, 0) == action_from_name(stock), "stock action of line %d", n);
        check(first_action(line + off, 1) == action_from_name(lazpy), "lazpy action of line %d", n);
    }
    (void)fclose(f);
    check(n >= 10, "messages.txt has %d lines", n);
}

static void test_counting(void)
{
    azh_msgstate st;
    const char *crash = "Fatal Error encountered (14): Exception Type: Undefined Instruction";
    const char *unk = "Fatal Error encountered (17): x";

    azh__msg_begin_run(&st);
    check(azh__msg_on_message(&st, unk, 0) == AZH_ACT_ERROR, "17 once");
    check(azh__msg_on_message(&st, unk, 0) == AZH_ACT_ERROR, "17 twice");
    check(azh__msg_on_message(&st, unk, 0) == AZH_ACT_EXIT_ERROR, "17 three times in one run (stock)");
    azh__msg_begin_run(&st);
    check(azh__msg_on_message(&st, crash, 0) == AZH_ACT_ERROR, "crash 14 once");
    check(azh__msg_on_message(&st, crash, 0) == AZH_ACT_ERROR, "crash 14 twice");
    check(azh__msg_on_message(&st, crash, 0) == AZH_ACT_EXIT_ERROR, "crash 14 three times in one run (stock)");
    azh__msg_begin_run(&st);
    check(azh__msg_on_message(&st, crash, 0) == AZH_ACT_ERROR, "run 1");
    check(azh__msg_on_message(&st, crash, 0) == AZH_ACT_ERROR, "run 1 again");
    azh__msg_begin_run(&st);
    check(azh__msg_on_message(&st, crash, 0) == AZH_ACT_ERROR, "three across two runs only error");
    azh__msg_begin_run(&st);
    check(azh__msg_on_message(&st, unk, 1) == AZH_ACT_ERROR && azh__msg_on_message(&st, unk, 1) == AZH_ACT_ERROR &&
          azh__msg_on_message(&st, unk, 1) == AZH_ACT_ERROR, "our core never counts to an exit");
    azh__msg_begin_run(&st);
    check(st.brk == 0 && st.err == 0 && st.exited == 0 && st.err_count == 0 && st.first[0] == '\0',
          "begin_run clears everything");
}

static void test_long(void)
{
    static char text[1024];
    azh_msgstate st;
    int n;

    n = snprintf(text, sizeof text, "Fatal Error encountered (14): Thread: ");
    memset(text + n, 'x', 300);
    n += 300;
    (void)snprintf(text + n, sizeof text - (size_t)n, "\nException Type: Break\nR0=0");
    check(strstr(text, "Exception Type:") - text > 200, "the Break line sits past byte 200");
    check(first_action(text, 0) == AZH_ACT_BREAK && first_action(text, 1) == AZH_ACT_BREAK, "late Break line");
    azh__msg_begin_run(&st);
    (void)azh__msg_on_message(&st, text, 0);
    check(strlen(st.first) == AZH_MSG_MAX - 1u && strncmp(st.first, text, AZH_MSG_MAX - 1u) == 0,
          "the first message is kept truncated to AZH_MSG_MAX (%zu)", strlen(st.first));
    azh__msg_begin_run(&st);
    (void)azh__msg_on_message(&st, "Fatal Error encountered (14): Exception Type: Break", 0);
    (void)azh__msg_on_message(&st, "Fatal Error encountered (17): later error", 0);
    check(strstr(st.first, "(17)") != NULL, "an error replaces a break as the kept message");
    (void)azh__msg_on_message(&st, "Fatal Error encountered (17): even later", 0);
    check(strstr(st.first, "later error") != NULL, "the first message of a kind is kept");
}

void test_msg(void)
{
    test_file();
    test_counting();
    test_long();
}
