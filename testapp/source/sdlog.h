// SPDX-License-Identifier: GPL-3.0-or-later
// The emulated/real SD card: read control.txt, write sdmc:/testapp/log.txt one flushed line at a time.
#ifndef LAZ_SDLOG_H
#define LAZ_SDLOG_H

#include <stdint.h>

// Open the SDMC archive. Returns 0 on success.
int sdlog_init(void);
// Read sdmc:/testapp/control.txt into buf (at most cap bytes). Returns the length, 0 when absent.
uint32_t sdlog_read_control(char *buf, uint32_t cap);
// Create /testapp (exists is fine) and open log.txt once, truncated. Returns 0 on success.
int sdlog_open(void);
// Append one line with FS_WRITE_FLUSH, and send the same text to svcOutputDebugString. Returns 0 on success.
int sdlog_line(const char *line, int len);
// Close the log and the archive.
void sdlog_close(void);

#endif
