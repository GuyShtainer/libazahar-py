/* test_main.h: the check counter and the entry function of each test file. */
#ifndef TEST_MAIN_H
#define TEST_MAIN_H

/* one check: prints the failing case when ok is 0 */
#ifdef _WIN32
#define CHECK_FMT gnu_printf     /* __USE_MINGW_ANSI_STDIO makes printf the C99 one */
#else
#define CHECK_FMT printf
#endif
void check(int ok, const char *fmt, ...) __attribute__((format(CHECK_FMT, 2, 3)));

void test_input(void);
void test_touch(void);
void test_match(void);
void test_msg(void);
void test_rawcopy(void);
void test_png(void);
void test_sdcopy(void);
void test_statemeta(void);
void test_watch(void);
void test_profile(void);

#endif
