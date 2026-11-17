/* plat/analyze_assert.h: forced into the Windows `make check` clang analysis only (-include), never into a build.
 * mingw-w64 declares the CRT's _assert without noreturn, so the analyzer walks past a failed assert() and reports the
 * very state the assert rules out (a NULL after assert(p != NULL)). This redeclares _assert as noreturn, which is what
 * it does at run time, so the analysis matches the macOS one, where assert() already ends the path. */
#ifndef AZH_ANALYZE_ASSERT_H
#define AZH_ANALYZE_ASSERT_H
#if defined(_WIN32) && defined(__clang_analyzer__)
#include <assert.h>
_CRTIMP __attribute__((noreturn)) void __cdecl _assert(const char *_Message, const char *_File, unsigned _Line);
#endif
#endif
