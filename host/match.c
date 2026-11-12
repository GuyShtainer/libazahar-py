/* match.c (pure besides stat/open/read): the SD text matcher. It sees only bytes it has not seen, keeps the last
 * len - 1 bytes as a carry so a text split across two reads is found. */
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "azh_pure.h"

#define CHUNK 65536u

int azh__match_init(azh_matcher *m, const char *text, int64_t start_offset)
{
    size_t len;

    assert(m != NULL);
    if (text == NULL || start_offset < 0) {
        return AZH_E_ARG;
    }
    len = strnlen(text, sizeof m->text);
    if (len < 1u || len > sizeof m->text - 1u) {
        return AZH_E_ARG;
    }
    memset(m, 0, sizeof *m);
    memcpy(m->text, text, len);
    m->len = len;
    m->offset = start_offset;
    assert(m->len >= 1u && m->len <= 255u);
    return AZH_OK;
}

void azh__match_restart(azh_matcher *m)
{
    assert(m != NULL);
    m->offset = 0;
    m->carry_len = 0u;
}

/* keep the last len - 1 bytes of (carry + buf) */
static void keep_carry(azh_matcher *m, const char *buf, size_t n)
{
    size_t keep = m->len - 1u;

    assert(keep <= sizeof m->carry);
    if (n >= keep) {
        memcpy(m->carry, buf + (n - keep), keep);
        m->carry_len = keep;
        return;
    }
    if (m->carry_len + n > keep) {
        size_t drop = m->carry_len + n - keep;

        memmove(m->carry, m->carry + drop, m->carry_len - drop);
        m->carry_len -= drop;
    }
    memcpy(m->carry + m->carry_len, buf, n);
    m->carry_len += n;
}

int azh__match_feed(azh_matcher *m, const char *buf, size_t n)
{
    char junction[2u * sizeof m->carry];
    size_t head;
    int found = 0;

    assert(m != NULL && m->len >= 1u);
    assert(buf != NULL || n == 0u);
    head = (n < m->len - 1u) ? n : m->len - 1u;
    if (m->carry_len > 0u && head > 0u) {          /* a match that uses both carry and new bytes ends in buf's head */
        memcpy(junction, m->carry, m->carry_len);
        memcpy(junction + m->carry_len, buf, head);
        found = memmem(junction, m->carry_len + head, m->text, m->len) != NULL;
    }
    if (found == 0 && n >= m->len) {
        found = memmem(buf, n, m->text, m->len) != NULL;
    }
    if (n > 0u) {
        keep_carry(m, buf, n);
    }
    return found;
}

static int feed_file(azh_matcher *m, int fd, int64_t size)
{
    static char chunk[CHUNK];
    int64_t left = size - m->offset;
    int64_t guard = left / (int64_t)CHUNK + 2;
    int found = 0;

    assert(fd >= 0 && left >= 0);
    if (lseek(fd, (off_t)m->offset, SEEK_SET) < 0) {
        return AZH_E_IO;
    }
    while (left > 0 && guard-- > 0 && found == 0) {
        ssize_t got = read(fd, chunk, (left > (int64_t)CHUNK) ? CHUNK : (size_t)left);

        if (got < 0) {
            return AZH_E_IO;
        }
        if (got == 0) {
            break;
        }
        found = azh__match_feed(m, chunk, (size_t)got);
        m->offset += got;
        left -= got;
    }
    return found;
}

int azh__match_poll_file(azh_matcher *m, const char *path)
{
    struct stat st;
    int fd;
    int rc;

    assert(m != NULL && path != NULL);
    if (stat(path, &st) != 0) {
        return (errno == ENOENT) ? 0 : AZH_E_IO;
    }
    if (!S_ISREG(st.st_mode)) {
        return AZH_E_IO;
    }
    if ((int64_t)st.st_size < m->offset) {
        azh__match_restart(m);
    }
    if ((int64_t)st.st_size == m->offset) {
        return 0;
    }
    fd = open(path, O_RDONLY);
    if (fd < 0) {
        return (errno == ENOENT) ? 0 : AZH_E_IO;
    }
    rc = feed_file(m, fd, (int64_t)st.st_size);
    (void)close(fd);
    return rc;
}
