/* plat/win_compat.h: the Windows (mingw-w64) shims of the probe host. Included only under _WIN32, after the system
 * headers. Scope: what the host needs from Windows: loading the core and the Vulkan loader, file mappings, SHA-256,
 * process times, directory copy and clear (win_sdcopy.c), and the CRT and path helpers. */
#ifndef AZH_WIN_COMPAT_H
#define AZH_WIN_COMPAT_H
#ifdef _WIN32

#include <direct.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "azh_plat.h"

#define RTLD_NOW 0
#define RTLD_LOCAL 0

/* the core: its own folder joins the DLL search; system32 is for the Vulkan loader only */
void *azh_win_dlopen(const char *path, int system32_only);
void *azh_win_dlsym(void *h, const char *name);
const char *azh_win_dlerror(void);
int azh_win_mkdir(const char *path);
int azh_win_setenv(const char *name, const char *value, int overwrite);
void azh_win_early_init(void);   /* SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX) */
void azh_win_exit(int code);   /* TerminateProcess: no atexit, no DLL detach of the core's threads */
void *azh_win_map_create(const char *path, size_t size);   /* a file-backed shared mapping, NULL on failure */
void azh_win_map_close(void *p);
void azh_win_map_flush(void *p, size_t size);
int azh_win_proc_times(double *user_s, double *sys_s, int64_t *peak_rss);   /* GetProcessTimes + peak working set */

/* SHA-256 through BCrypt, shaped like CommonCrypto: each returns 1 on success, 0 on failure (update is sticky) */
typedef struct { void *alg; void *hash; int failed; } azh_win_sha256;
int azh_win_sha256_init(azh_win_sha256 *c);
int azh_win_sha256_update(azh_win_sha256 *c, const void *data, size_t len);
int azh_win_sha256_final(unsigned char *digest32, azh_win_sha256 *c);

void *azh_win_memmem(const void *hay, size_t hn, const void *needle, size_t nn);
#define memmem(h, hn, n, nn) azh_win_memmem((h), (hn), (n), (nn))
#define dlopen(p, f) azh_win_dlopen((p), 0)
#define dlsym(h, n) azh_win_dlsym((h), (n))
#define dlerror() azh_win_dlerror()
#define mkdir(p, m) azh_win_mkdir(p)
#define setenv(n, v, o) azh_win_setenv((n), (v), (o))

#endif
#endif
