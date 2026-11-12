/* state.c: savestates and state boot (docs/plans/phase-d.md section 3). A state at <path> is three things: the
 * core's buffer (<path>), a copy of the instance's SD folder (<path>.sd/) and a meta file (<path>.meta, written last,
 * whose presence means the state is complete). Restore order: check the meta and the app, read, drain, replace the
 * SD folder, unserialize, set the counters. */
#include <CommonCrypto/CommonDigest.h>
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include "azh_internal.h"

#define STATE_SIZE_CAP ((int64_t)2 << 30)        /* 2 GiB */
#define STATE_WARMUP_FRAMES 1                    /* retro_run calls before the restore (phase-d 3.4, PLAN risk 8) */
#define SHA_CHUNK 65536
#define SHA_CHUNKS_MAX (1 << 20)                 /* 64 GiB of app: more is a mistake */
#define PATH_EXT (AZH_PATH_MAX + 16)

typedef struct {
    azh_state_meta meta;
    double meta_ms, sha_ms, read_ms, drain_ms, sd_ms, unserialize_ms;
    size_t bytes;
} restore_t;

static char noted_app[AZH_PATH_MAX];

void azh__state_note_app(const char *app)
{
    assert(app != NULL);
    (void)snprintf(noted_app, sizeof noted_app, "%s", app);
    assert(noted_app[0] != '\0' || app[0] == '\0');
}

static double now_ms(void)
{
    struct timespec t;

    (void)clock_gettime(CLOCK_MONOTONIC, &t);
    assert(t.tv_nsec >= 0 && t.tv_sec >= 0);
    return (double)t.tv_sec * 1000.0 + (double)t.tv_nsec * 1e-6;
}

/* <base><suffix> into out; 0 or AZH_E_ARG */
static int join_path(char *out, size_t cap, const char *base, const char *suffix)
{
    int n;

    assert(out != NULL && base != NULL && suffix != NULL && cap > 0u);
    n = snprintf(out, cap, "%s%s", base, suffix);
    return (n > 0 && (size_t)n < cap) ? AZH_OK : AZH_E_ARG;
}

static int is_dir(const char *path)
{
    struct stat st;

    assert(path != NULL);
    return (stat(path, &st) == 0 && S_ISDIR(st.st_mode)) ? 1 : 0;
}

/* sha256 of a file as 64 lowercase hex digits (hex needs 65 bytes) */
static int app_sha256(const char *path, char *hex)
{
    static unsigned char chunk[SHA_CHUNK];
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256_CTX ctx;
    ssize_t r;
    int fd;
    int i;

    assert(path != NULL && hex != NULL);
    fd = open(path, O_RDONLY);
    if (fd < 0) {
        return AZH_E_IO;
    }
    (void)CC_SHA256_Init(&ctx);
    r = 1;
    for (i = 0; i < SHA_CHUNKS_MAX && r != 0; i++) {
        r = read(fd, chunk, sizeof chunk);
        if (r > 0) {
            (void)CC_SHA256_Update(&ctx, chunk, (CC_LONG)r);
        } else if (r < 0 && errno != EINTR) {
            (void)close(fd);
            return AZH_E_IO;
        }
    }
    (void)close(fd);
    if (r != 0) {
        return AZH_E_IO;
    }
    (void)CC_SHA256_Final(digest, &ctx);
    for (i = 0; i < CC_SHA256_DIGEST_LENGTH; i++) {
        (void)snprintf(hex + 2 * i, 3, "%02x", digest[i]);
    }
    return AZH_OK;
}

static int write_all(int fd, const void *buf, size_t n)
{
    const char *p = buf;
    size_t done = 0u;
    ssize_t w;

    assert(fd >= 0 && buf != NULL);
    while (done < n) {
        w = write(fd, p + done, n - done);
        if (w < 0 && errno == EINTR) {
            continue;
        }
        if (w <= 0) {
            return AZH_E_IO;
        }
        done += (size_t)w;
    }
    return AZH_OK;
}

/* <path>.tmp, fsync, rename */
static int write_file_atomic(const char *path, const void *buf, size_t n)
{
    char tmp[PATH_EXT];
    int fd;
    int rc;

    assert(path != NULL && buf != NULL);
    if (join_path(tmp, sizeof tmp, path, ".tmp") != AZH_OK) {
        return AZH_E_ARG;
    }
    fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        return AZH_E_IO;
    }
    rc = write_all(fd, buf, n);
    if (rc == AZH_OK && fsync(fd) != 0) {
        rc = AZH_E_IO;
    }
    if (close(fd) != 0) {
        rc = AZH_E_IO;
    }
    if (rc == AZH_OK && rename(tmp, path) != 0) {
        rc = AZH_E_IO;
    }
    if (rc != AZH_OK) {
        (void)unlink(tmp);
    }
    return rc;
}

/* the whole file into a malloc'ed buffer (the caller frees); 1 to STATE_SIZE_CAP bytes */
static int read_file(const char *path, void **buf_out, size_t *n_out)
{
    struct stat st;
    char *buf;
    size_t done = 0u;
    ssize_t r;
    int fd;

    assert(path != NULL && buf_out != NULL && n_out != NULL);
    *buf_out = NULL;
    fd = open(path, O_RDONLY);
    if (fd < 0 || fstat(fd, &st) != 0 || st.st_size <= 0 || (int64_t)st.st_size > STATE_SIZE_CAP) {
        if (fd >= 0) {
            (void)close(fd);
        }
        return AZH_E_SAVESTATE;
    }
    buf = malloc((size_t)st.st_size);
    if (buf == NULL) {
        (void)close(fd);
        return AZH_E_NOMEM;
    }
    while (done < (size_t)st.st_size) {
        r = read(fd, buf + done, (size_t)st.st_size - done);
        if (r < 0 && errno == EINTR) {
            continue;
        }
        if (r <= 0) {
            break;
        }
        done += (size_t)r;
    }
    (void)close(fd);
    if (done != (size_t)st.st_size) {
        free(buf);
        return AZH_E_SAVESTATE;
    }
    *buf_out = buf;
    *n_out = done;
    return AZH_OK;
}

/* remove a folder and its contents; a missing folder is fine */
static int remove_dir(const char *dir)
{
    assert(dir != NULL);
    if (!is_dir(dir)) {
        return AZH_OK;
    }
    if (azh__clear_tree(dir) != AZH_OK || (rmdir(dir) != 0 && errno != ENOENT)) {
        return AZH_E_IO;
    }
    return AZH_OK;
}

/* <path>.sd.tmp/ from the SD folder, then swapped in over <path>.sd/ */
static int snapshot_sd(const char *path, const char *sd_root)
{
    char tmp[PATH_EXT], cur[PATH_EXT], old[PATH_EXT];
    int have_old;

    assert(path != NULL && sd_root != NULL);
    if (join_path(tmp, sizeof tmp, path, ".sd.tmp") != AZH_OK || join_path(cur, sizeof cur, path, ".sd") != AZH_OK ||
        join_path(old, sizeof old, path, ".sd.old") != AZH_OK) {
        return AZH_E_ARG;
    }
    if (remove_dir(tmp) != AZH_OK || remove_dir(old) != AZH_OK || azh__copy_tree(sd_root, tmp) != AZH_OK) {
        return AZH_E_IO;
    }
    have_old = is_dir(cur);
    if (have_old && rename(cur, old) != 0) {
        return AZH_E_IO;
    }
    if (rename(tmp, cur) != 0) {
        return AZH_E_IO;
    }
    return have_old ? remove_dir(old) : AZH_OK;
}

/* steps 1 to 3 of the save: serialize, count the polls, write <path>; the buffer is freed here */
static int save_core(const char *path, int32_t *k_out, size_t *bytes_out, double *ms_ser, double *ms_write)
{
    int64_t v0, dv;
    size_t size;
    void *buf;
    double t0 = now_ms();
    int rc;

    assert(path != NULL && k_out != NULL && bytes_out != NULL);
    v0 = azh__vblanks_total();
    size = azh_g.core.serialize_size();
    dv = azh__vblanks_total() - v0;
    if (size == 0u) {
        return azh_fail(AZH_E_SAVESTATE, "the core could not save (drain timeout or error; see host.log)");
    }
    if (dv < 0 || dv > 0x7fffffffLL) {
        return azh_fail(AZH_E_SAVESTATE, "the vblank counter moved by %lld during the save", (long long)dv);
    }
    buf = malloc(size);
    if (buf == NULL) {
        return azh_fail(AZH_E_NOMEM, "cannot allocate %zu bytes for the state", size);
    }
    rc = azh_g.core.serialize(buf, size) ? AZH_OK : AZH_E_SAVESTATE;
    *ms_ser = now_ms() - t0;
    if (rc != AZH_OK) {
        free(buf);
        return azh_fail(AZH_E_SAVESTATE, "retro_serialize failed after a size of %zu bytes", size);
    }
    t0 = now_ms();
    rc = write_file_atomic(path, buf, size);
    free(buf);
    *ms_write = now_ms() - t0;
    if (rc != AZH_OK) {
        return azh_fail(AZH_E_IO, "cannot write %s: %s", path, strerror(errno));
    }
    *k_out = (int32_t)dv;
    *bytes_out = size;
    return AZH_OK;
}

/* step 6: the meta, written last */
static int write_meta(const char *path, int32_t k, double *ms_sha)
{
    char mpath[PATH_EXT];
    azh_state_meta m;
    double t0 = now_ms();
    int rc;

    assert(path != NULL && ms_sha != NULL && noted_app[0] != '\0');
    memset(&m, 0, sizeof m);
    m.abi = AZH_ABI_VERSION;
    m.k = k;
    azh__counters_get(&m.frame_total, &m.vblanks_total);
    m.created = (int64_t)time(NULL);
    (void)snprintf(m.core_version, sizeof m.core_version, "%s", azh_g.core_version);
    (void)snprintf(m.app, sizeof m.app, "%s", noted_app);
    rc = app_sha256(noted_app, m.app_sha256);
    *ms_sha = now_ms() - t0;
    if (rc != AZH_OK) {
        return azh_fail(AZH_E_IO, "cannot hash the app %s", noted_app);
    }
    if (join_path(mpath, sizeof mpath, path, ".meta") != AZH_OK) {
        return azh_fail(AZH_E_ARG, "state path too long");
    }
    rc = azh__meta_write(mpath, &m);
    return (rc == AZH_OK) ? AZH_OK : azh_fail(AZH_E_SAVESTATE, "cannot write %s (code %d)", mpath, rc);
}

static int save_args_ok(const char *path, const int32_t *k_out)
{
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_save_state: needs a successful azh_boot");
    }
    if (path == NULL || *path == '\0' || k_out == NULL || strlen(path) >= (size_t)AZH_PATH_MAX) {
        return azh_fail(AZH_E_ARG, "azh_save_state: a path and a k_out are required (path under %d bytes)",
                        AZH_PATH_MAX);
    }
    return AZH_OK;
}

int azh__state_save(const char *path, int32_t *k_out)
{
    char mpath[PATH_EXT], sd_root[AZH_PATH_MAX];
    int64_t frame_total, vblanks;
    double ms_ser = 0.0, ms_write = 0.0, ms_sd, ms_sha = 0.0, t0;
    size_t bytes = 0u;
    int32_t k = 0;
    int rc = save_args_ok(path, k_out);

    if (rc != AZH_OK) {
        return rc;
    }
    if (join_path(mpath, sizeof mpath, path, ".meta") != AZH_OK || azh__sd_root(sd_root, sizeof sd_root) != AZH_OK) {
        return azh_fail(AZH_E_ARG, "state path too long");
    }
    (void)unlink(mpath);                               /* step 0: a crash below never leaves an old meta */
    rc = save_core(path, &k, &bytes, &ms_ser, &ms_write);
    if (rc != AZH_OK) {
        return rc;
    }
    t0 = now_ms();
    if (snapshot_sd(path, sd_root) != AZH_OK) {
        return azh_fail(AZH_E_IO, "cannot snapshot the SD folder %s into %s.sd", sd_root, path);
    }
    ms_sd = now_ms() - t0;
    azh__counters_get(&frame_total, &vblanks);
    azh__counters_set(frame_total + k, vblanks);       /* a state "at frame N" is at N + k (PLAN 2.9) */
    rc = write_meta(path, k, &ms_sha);
    if (rc != AZH_OK) {
        return rc;
    }
    *k_out = k;
    azh_log(AZH_LOG_INFO, "state save k=%d bytes=%zu serialize_ms=%.1f write_ms=%.1f sd_ms=%.1f sha_ms=%.1f",
            (int)k, bytes, ms_ser, ms_write, ms_sd, ms_sha);
    return AZH_OK;
}

/* the app must be the one the state was made with; 1 when it is (or LAZ_STATE_ANY_APP=1 says to go on) */
static int check_app(const char *app, const restore_t *r, double *ms_sha)
{
    char hex[65];
    const char *any;
    double t0 = now_ms();
    int rc;

    assert(app != NULL && r != NULL && ms_sha != NULL);
    rc = app_sha256(app, hex);
    *ms_sha = now_ms() - t0;
    if (rc != AZH_OK) {
        return azh_fail(AZH_E_IO, "cannot hash the app %s", app);
    }
    if (strcmp(hex, r->meta.app_sha256) == 0) {
        return AZH_OK;
    }
    any = getenv("LAZ_STATE_ANY_APP");
    if (any != NULL && strcmp(any, "1") == 0) {
        azh_log(AZH_LOG_WARN, "state is for another app (%s); going on because LAZ_STATE_ANY_APP=1", r->meta.app);
        return AZH_OK;
    }
    return azh_fail(AZH_E_SAVESTATE, "state is for another app (%s)", r->meta.app);
}

/* step 1: everything that can be refused without changing anything */
static int restore_check(const char *app, const char *path, restore_t *r)
{
    char mpath[PATH_EXT], sdpath[PATH_EXT];
    double t0 = now_ms();
    int rc;

    assert(app != NULL && path != NULL && r != NULL);
    memset(r, 0, sizeof *r);
    if (join_path(mpath, sizeof mpath, path, ".meta") != AZH_OK || join_path(sdpath, sizeof sdpath, path, ".sd") != AZH_OK) {
        return azh_fail(AZH_E_ARG, "state path too long");
    }
    rc = azh__meta_read(mpath, &r->meta);
    if (rc != AZH_OK) {
        return azh_fail(AZH_E_SAVESTATE, "not a complete state (%s is missing or damaged)", mpath);
    }
    r->meta_ms = now_ms() - t0;
    if (r->meta.abi != AZH_ABI_VERSION) {
        return azh_fail(AZH_E_SAVESTATE, "state was made with host abi %d, this host is abi %d", (int)r->meta.abi,
                        AZH_ABI_VERSION);
    }
    if (!is_dir(sdpath)) {
        return azh_fail(AZH_E_SAVESTATE, "not a complete state (%s is missing)", sdpath);
    }
    rc = check_app(app, r, &r->sha_ms);
    if (rc != AZH_OK) {
        return rc;
    }
    if (strcmp(r->meta.core_version, azh_g.core_version) != 0) {
        azh_log(AZH_LOG_WARN, "state core version %s, running core %s (the core decides)", r->meta.core_version,
                azh_g.core_version);
    }
    return AZH_OK;
}

/* step 4: the SD folder becomes the snapshot */
static int replace_sd(const char *path)
{
    char sd_root[AZH_PATH_MAX], sdpath[PATH_EXT], parent[PATH_EXT];

    assert(path != NULL);
    if (azh__sd_root(sd_root, sizeof sd_root) != AZH_OK || join_path(sdpath, sizeof sdpath, path, ".sd") != AZH_OK ||
        join_path(parent, sizeof parent, azh_g.sysdir, "/Azahar") != AZH_OK) {
        return azh_fail(AZH_E_ARG, "state path too long");
    }
    if (remove_dir(sd_root) != AZH_OK) {
        return azh_fail(AZH_E_IO, "cannot clear the SD folder %s", sd_root);
    }
    if (mkdir(parent, 0755) != 0 && errno != EEXIST) {
        return azh_fail(AZH_E_IO, "cannot create %s", parent);
    }
    if (azh__copy_tree(sdpath, sd_root) != AZH_OK) {
        return azh_fail(AZH_E_IO, "cannot copy %s to %s", sdpath, sd_root);
    }
    return AZH_OK;
}

/* steps 3 to 5 on a buffer the caller owns */
static int restore_core(const char *path, const void *buf, restore_t *r)
{
    double t0 = now_ms();
    int rc;

    assert(path != NULL && buf != NULL && r != NULL && r->bytes > 0u);
    if (azh_g.core.serialize_size() == 0u) {
        return azh_fail(AZH_E_SAVESTATE, "drain timed out (the guest kept async work pending; see host.log)");
    }
    r->drain_ms = now_ms() - t0;
    t0 = now_ms();
    rc = replace_sd(path);
    r->sd_ms = now_ms() - t0;
    if (rc != AZH_OK) {
        return rc;
    }
    t0 = now_ms();
    if (!azh_g.core.unserialize(buf, r->bytes)) {
        return azh_fail(AZH_E_SAVESTATE, "the core refused the state (another core build; see host.log)");
    }
    r->unserialize_ms = now_ms() - t0;
    return AZH_OK;
}

/* steps 2 to 7 */
static int restore_apply(const char *path, restore_t *r)
{
    void *buf = NULL;
    double t0 = now_ms();
    int rc;

    assert(path != NULL && r != NULL);
    rc = read_file(path, &buf, &r->bytes);
    if (rc != AZH_OK) {
        return azh_fail(rc, "cannot read the state file %s", path);
    }
    r->read_ms = now_ms() - t0;
    rc = restore_core(path, buf, r);
    free(buf);
    if (rc != AZH_OK) {
        return rc;
    }
    azh__counters_set(r->meta.frame_total, r->meta.vblanks_total);
    azh_log(AZH_LOG_INFO, "state load meta_ms=%.1f sha_ms=%.1f read_ms=%.1f drain_ms=%.1f sd_ms=%.1f "
            "unserialize_ms=%.1f bytes=%zu", r->meta_ms, r->sha_ms, r->read_ms, r->drain_ms, r->sd_ms,
            r->unserialize_ms, r->bytes);
    return AZH_OK;
}

int azh__state_boot(const char *app, const char *state_path)
{
    restore_t r;
    int rc;
    int i;

    assert(app != NULL && state_path != NULL);
    rc = restore_check(app, state_path, &r);
    if (rc != AZH_OK) {
        return rc;                                     /* before any frame */
    }
    for (i = 0; i < STATE_WARMUP_FRAMES; i++) {
        rc = azh__run_one_frame();
        if (rc != AZH_OK) {
            return rc;
        }
    }
    return restore_apply(state_path, &r);
}

int azh__state_load(const char *path)
{
    restore_t r;
    int rc;

    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_load_state: needs a successful azh_boot");
    }
    if (path == NULL || *path == '\0' || strlen(path) >= (size_t)AZH_PATH_MAX) {
        return azh_fail(AZH_E_ARG, "azh_load_state: a path under %d bytes is required", AZH_PATH_MAX);
    }
    rc = restore_check(noted_app, path, &r);
    if (rc != AZH_OK) {
        return rc;
    }
    return restore_apply(path, &r);
}
