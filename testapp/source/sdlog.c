// SPDX-License-Identifier: GPL-3.0-or-later
#include "sdlog.h"

#include <3ds.h>
#include <assert.h>
#include <string.h>

static FS_Archive g_archive;
static Handle g_log;
static int g_archive_open;
static int g_log_open;
static u64 g_offset;

int sdlog_init(void)
{
    if (R_FAILED(fsInit())) {
        return -1;
    }
    if (R_FAILED(FSUSER_OpenArchive(&g_archive, ARCHIVE_SDMC, fsMakePath(PATH_EMPTY, "")))) {
        return -1;
    }
    g_archive_open = 1;
    return 0;
}

uint32_t sdlog_read_control(char *buf, uint32_t cap)
{
    Handle h;
    u32 got = 0;
    if (buf == NULL || cap == 0 || !g_archive_open) {
        return 0;
    }
    if (R_FAILED(FSUSER_OpenFile(&h, g_archive, fsMakePath(PATH_ASCII, "/testapp/control.txt"), FS_OPEN_READ, 0))) {
        return 0;
    }
    if (R_FAILED(FSFILE_Read(h, &got, 0, buf, cap))) {
        got = 0;
    }
    (void)FSFILE_Close(h);  // read-only handle; a close failure changes nothing for us
    assert(got <= cap);
    return got;
}

int sdlog_open(void)
{
    if (!g_archive_open) {
        return -1;
    }
    // An already-existing directory is a failed Result we deliberately ignore: OpenFile below proves it is usable.
    (void)FSUSER_CreateDirectory(g_archive, fsMakePath(PATH_ASCII, "/testapp"), 0);
    if (R_FAILED(FSUSER_OpenFile(&g_log, g_archive, fsMakePath(PATH_ASCII, "/testapp/log.txt"),
                                 FS_OPEN_CREATE | FS_OPEN_WRITE, 0))) {
        return -1;
    }
    g_log_open = 1;
    if (R_FAILED(FSFILE_SetSize(g_log, 0))) {
        return -1;
    }
    g_offset = 0;
    return 0;
}

int sdlog_line(const char *line, int len)
{
    u32 written = 0;
    assert(g_offset < 0xF0000000ull);  // the running offset never wraps a 32-bit file
    if (line == NULL || len <= 0) {
        return -1;
    }
    assert(len < 4096);
    (void)svcOutputDebugString(line, len);  // debug output has no result worth checking
    if (!g_log_open) {
        return -1;
    }
    if (R_FAILED(FSFILE_Write(g_log, &written, g_offset, line, (u32)len, FS_WRITE_FLUSH)) || written != (u32)len) {
        return -1;
    }
    g_offset += written;
    return 0;
}

void sdlog_close(void)
{
    if (g_log_open) {
        (void)FSFILE_Close(g_log);  // at exit; nothing left to do on failure
        g_log_open = 0;
    }
    if (g_archive_open) {
        (void)FSUSER_CloseArchive(g_archive);
        g_archive_open = 0;
    }
    fsExit();
}
