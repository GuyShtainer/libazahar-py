/* plat/win_compat.c: Windows shims for the probe host (mingw-w64). */
#ifdef _WIN32
#include <assert.h>
#include <fcntl.h>
#include <io.h>
#include <stdio.h>

#include <windows.h>
#include <bcrypt.h>
#include <psapi.h>

#include "win_compat.h"

#undef dlopen
#undef dlsym
#undef dlerror
#undef mkdir
#undef memmem
#undef setenv

static __thread char err_text[256];

void *azh_win_dlopen(const char *path, int system32_only)
{
    HMODULE h;
    DWORD flags;

    assert(path != NULL);
    if (system32_only != 0) {
        flags = LOAD_LIBRARY_SEARCH_SYSTEM32;
    } else {
        flags = LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR;
    }
    h = LoadLibraryExA(path, NULL, flags);
    if (h == NULL) {
        snprintf(err_text, sizeof err_text, "LoadLibraryExA failed, Windows error %lu", (unsigned long)GetLastError());
    }
    return (void *)h;
}

void *azh_win_dlsym(void *h, const char *name)
{
    FARPROC p;
    void *out;

    assert(h != NULL && name != NULL);
    p = GetProcAddress((HMODULE)h, name);
    memcpy(&out, &p, sizeof out);
    return out;
}

const char *azh_win_dlerror(void)
{
    return err_text;
}

int azh_win_mkdir(const char *path)
{
    size_t n;

    assert(path != NULL);
    n = strlen(path);
    if (n == 2u && path[1] == ':') {     /* a bare drive: it exists */
        errno = EEXIST;
        return -1;
    }
    return _mkdir(path);
}

int azh_win_setenv(const char *name, const char *value, int overwrite)
{
    assert(name != NULL && value != NULL);
    if (overwrite == 0 && getenv(name) != NULL) {
        return 0;
    }
    return _putenv_s(name, value) == 0 ? 0 : -1;
}

void *azh_win_memmem(const void *hay, size_t hn, const void *needle, size_t nn)
{
    const unsigned char *h = hay;
    size_t i;

    assert(hay != NULL && needle != NULL);
    if (nn == 0u) {
        return (void *)hay;
    }
    for (i = 0; i + nn <= hn; i++) {
        if (h[i] == *(const unsigned char *)needle && memcmp(h + i, needle, nn) == 0) {
            return (void *)(h + i);
        }
    }
    return NULL;
}

void azh_win_early_init(void)
{
    (void)SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    _set_fmode(_O_BINARY);                       /* no CRLF in stdout, host.log or the maps */
    (void)_setmode(1, _O_BINARY);
    (void)_setmode(2, _O_BINARY);
}

void azh_win_exit(int code)
{
    (void)TerminateProcess(GetCurrentProcess(), (UINT)code);
    for (;;) {
        Sleep(1000);
    }
}

int azh_win_replace(const char *from, const char *to)
{
    assert(from != NULL && to != NULL);
    return MoveFileExA(from, to, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0 ? 0 : -1;
}

int azh_win_sha256_init(azh_win_sha256 *c)
{
    assert(c != NULL);
    c->alg = NULL;
    c->hash = NULL;
    c->failed = 0;
    if (BCryptOpenAlgorithmProvider((BCRYPT_ALG_HANDLE *)&c->alg, BCRYPT_SHA256_ALGORITHM, NULL, 0) != 0 ||
        BCryptCreateHash(c->alg, (BCRYPT_HASH_HANDLE *)&c->hash, NULL, 0, NULL, 0, 0) != 0) {
        c->failed = 1;
        if (c->alg != NULL) {
            (void)BCryptCloseAlgorithmProvider(c->alg, 0);
            c->alg = NULL;
        }
        return 0;
    }
    return 1;
}

int azh_win_sha256_update(azh_win_sha256 *c, const void *data, size_t len)
{
    assert(c != NULL && data != NULL && len <= 0xffffffffu);
    if (c->failed == 0 && BCryptHashData(c->hash, (PUCHAR)(uintptr_t)data, (ULONG)len, 0) != 0) {
        c->failed = 1;
    }
    return c->failed == 0 ? 1 : 0;
}

int azh_win_sha256_final(unsigned char *digest32, azh_win_sha256 *c)
{
    int ok;

    assert(digest32 != NULL && c != NULL);
    ok = (c->failed == 0 && BCryptFinishHash(c->hash, digest32, 32, 0) == 0) ? 1 : 0;
    if (c->hash != NULL) {
        (void)BCryptDestroyHash(c->hash);
    }
    if (c->alg != NULL) {
        (void)BCryptCloseAlgorithmProvider(c->alg, 0);
    }
    c->hash = NULL;
    c->alg = NULL;
    return ok;
}

void *azh_win_map_create(const char *path, size_t size)
{
    HANDLE f;
    HANDLE m;
    void *p;

    assert(path != NULL && size > 0u);
    f = CreateFileA(path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, CREATE_ALWAYS,
                    FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) {
        return NULL;
    }
    m = CreateFileMappingA(f, NULL, PAGE_READWRITE, (DWORD)((uint64_t)size >> 32), (DWORD)(size & 0xffffffffu), NULL);
    (void)CloseHandle(f);     /* the mapping keeps the file */
    if (m == NULL) {
        return NULL;
    }
    p = MapViewOfFile(m, FILE_MAP_ALL_ACCESS, 0, 0, size);
    (void)CloseHandle(m);     /* the view keeps the mapping */
    return p;
}

void azh_win_map_close(void *p)
{
    if (p != NULL) {
        (void)UnmapViewOfFile(p);
    }
}

void azh_win_map_flush(void *p, size_t size)
{
    if (p != NULL) {
        (void)FlushViewOfFile(p, size);     /* best effort: the process is about to exit */
    }
}

static double filetime_s(FILETIME ft)
{
    uint64_t t = ((uint64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;

    return (double)t * 1e-7;
}

int azh_win_proc_times(double *user_s, double *sys_s, int64_t *peak_rss)
{
    FILETIME c, e, k, u;
    PROCESS_MEMORY_COUNTERS pmc;

    assert(user_s != NULL && sys_s != NULL && peak_rss != NULL);
    if (GetProcessTimes(GetCurrentProcess(), &c, &e, &k, &u) == 0) {
        return -1;
    }
    *user_s = filetime_s(u);
    *sys_s = filetime_s(k);
    *peak_rss = 0;
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof pmc) != 0) {
        *peak_rss = (int64_t)pmc.PeakWorkingSetSize;
    }
    return 0;
}
#endif
