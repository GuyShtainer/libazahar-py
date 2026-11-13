/* plat/azh_plat.h: the one place where the file calls that differ between macOS and Windows are named.
 * Included by azh_pure.h, so every host file and every unit test sees it. Darwin behaviour is unchanged:
 * O_BINARY is 0, azh_replace is rename() and azh_fsync is fsync(). */
#ifndef AZH_PLAT_H
#define AZH_PLAT_H

#include <fcntl.h>
#include <stdio.h>

/* every open() in host/ ORs this in (tools/check-obinary.sh greps for it); 0 where files have no text mode */
#ifndef O_BINARY
#define O_BINARY 0
#endif

#ifdef _WIN32
#include <io.h>
/* MoveFileExA(MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH): 0 on success, -1 on failure (win_compat.c) */
int azh_win_replace(const char *from, const char *to);
#define azh_replace(from, to) azh_win_replace((from), (to))
#define azh_fsync(fd) _commit(fd)
#define AZH_FSYNC_PATH_NOOP 1      /* a read-only fd cannot be flushed on Windows; the write-through covers it */
#else
#include <unistd.h>
#define azh_replace(from, to) rename((from), (to))
#define azh_fsync(fd) fsync(fd)
#define AZH_FSYNC_PATH_NOOP 0
#endif

#endif
