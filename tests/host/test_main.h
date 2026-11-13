/* test_main.h: the check counter and the entry function of each test file. */
#ifndef TEST_MAIN_H
#define TEST_MAIN_H

/* one check: prints the failing case when ok is 0 */
void check(int ok, const char *fmt, ...) __attribute__((format(printf, 2, 3)));

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
