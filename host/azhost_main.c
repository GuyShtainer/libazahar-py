/* azhost_main.c: the azhost program. "azhost run <app> ..." calls the same azh_* functions a Python worker will. */
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "azhost.h"

#define DEFAULT_PROFILE "host/options-default.txt"
#define DEFAULT_CORE "dl/azahar/azahar_libretro.dylib"
#define MAX_OPTS 64
#define LINE_MAX_LEN 512

static int printed;     /* the error line for the current failure is already on stderr */

typedef struct {
    const char *app, *sys, *out, *profile, *core, *mvk, *state;
    long frames;
    const char *shot_list;
    const char *opts[MAX_OPTS];
    int n_opts;
} args_t;

static int usage_error(const char *what)
{
    assert(what != NULL);
    assert(AZH_EXIT_USAGE == 2);
    fprintf(stderr, "UsageError: %s\n", what);
    fprintf(stderr, "usage: azhost run <app> --sys <dir> --out <dir> --frames N [--shot f1,f2,...] [--opt key=value]...\n"
                    "              [--profile file] [--core path] [--mvk path] [--state file]\n");
    return AZH_EXIT_USAGE;
}

/* a flag that takes a value: returns the value, or NULL when the value is missing */
static const char *flag_value(int argc, char **argv, int *i)
{
    assert(argv != NULL && i != NULL);
    assert(*i >= 0 && *i < argc);
    if (*i + 1 >= argc) {
        return NULL;
    }
    (*i)++;
    return argv[*i];
}

static int set_flag(args_t *a, const char *flag, const char *val)
{
    long n;
    char *end = NULL;

    assert(a != NULL && flag != NULL);
    assert(val != NULL);
    if (strcmp(flag, "--sys") == 0) {
        a->sys = val;
    } else if (strcmp(flag, "--out") == 0) {
        a->out = val;
    } else if (strcmp(flag, "--profile") == 0) {
        a->profile = val;
    } else if (strcmp(flag, "--core") == 0) {
        a->core = val;
    } else if (strcmp(flag, "--mvk") == 0) {
        a->mvk = val;
    } else if (strcmp(flag, "--state") == 0) {
        a->state = val;
    } else if (strcmp(flag, "--shot") == 0) {
        a->shot_list = val;
    } else if (strcmp(flag, "--frames") == 0) {
        n = strtol(val, &end, 10);
        if (*val == '\0' || *end != '\0' || n < 1 || n > 100000000L) {
            return -1;
        }
        a->frames = n;
    } else if (strcmp(flag, "--opt") == 0) {
        if (a->n_opts >= MAX_OPTS) {
            return -1;
        }
        a->opts[a->n_opts++] = val;
    } else {
        return -1;
    }
    return 0;
}

static int parse_args(int argc, char **argv, args_t *a)
{
    int i;

    assert(argv != NULL && a != NULL);
    assert(argc >= 1);
    memset(a, 0, sizeof *a);
    a->profile = DEFAULT_PROFILE;
    a->core = getenv("LAZ_CORE");
    if (a->core == NULL || *a->core == '\0') {
        a->core = DEFAULT_CORE;
    }
    if (argc < 3 || strcmp(argv[1], "run") != 0) {
        return usage_error("expected: azhost run <app> ...");
    }
    a->app = argv[2];
    for (i = 3; i < argc; i++) {
        const char *flag = argv[i];
        const char *val = flag_value(argc, argv, &i);

        if (val == NULL) {
            return usage_error("a flag is missing its value");
        }
        if (set_flag(a, flag, val) != 0) {
            fprintf(stderr, "UsageError: bad flag or value: %s %s\n", flag, val);
            return AZH_EXIT_USAGE;
        }
    }
    if (a->sys == NULL || a->out == NULL || a->frames == 0) {
        return usage_error("--sys, --out and --frames are required");
    }
    return AZH_OK;
}

/* mkdir -p, one component at a time (a bounded loop over the path) */
static int make_dirs(const char *path)
{
    char buf[AZH_PATH_MAX];
    size_t i;
    size_t n = strlen(path);

    assert(path != NULL);
    assert(sizeof buf == AZH_PATH_MAX);
    if (n == 0 || n >= sizeof buf) {
        return -1;
    }
    memcpy(buf, path, n + 1);
    for (i = 1; i <= n; i++) {
        if (buf[i] == '/' || buf[i] == '\0') {
            char saved = buf[i];

            buf[i] = '\0';
            if (mkdir(buf, 0755) != 0 && errno != EEXIST) {
                return -1;
            }
            buf[i] = saved;
        }
    }
    return 0;
}

static int report(int rc)
{
    const char *cls = "UsageError";
    int code = AZH_EXIT_USAGE;

    assert(rc < 0);
    assert(printed == 0 || printed == 1);
    switch (rc) {
    case AZH_E_BOOT: cls = "BootError"; code = AZH_EXIT_BOOT; break;
    case AZH_E_CORE: cls = "CoreError"; code = AZH_EXIT_CORE; break;
    case AZH_E_VULKAN: cls = "VulkanError"; code = AZH_EXIT_VULKAN; break;
    case AZH_E_IO: case AZH_E_NOMEM: cls = "IOError"; code = AZH_EXIT_IO; break;
    default: break;
    }
    if (printed == 0) {
        fprintf(stderr, "%s: %s\n", cls, azh_error());
    }
    return code;
}

/* one "key=value" into azh_set_option */
static int apply_pair(const char *pair)
{
    char key[LINE_MAX_LEN];
    const char *eq = strchr(pair, '=');
    size_t n;

    assert(pair != NULL);
    assert(sizeof key == LINE_MAX_LEN);
    if (eq == NULL || eq == pair) {
        fprintf(stderr, "UsageError: expected key=value, got '%s'\n", pair);
        printed = 1;
        return AZH_E_ARG;
    }
    n = (size_t)(eq - pair);
    if (n >= sizeof key) {
        fprintf(stderr, "UsageError: option key too long\n");
        printed = 1;
        return AZH_E_ARG;
    }
    memcpy(key, pair, n);
    key[n] = '\0';
    return azh_set_option(key, eq + 1);
}

static int apply_profile(const char *path)
{
    char line[LINE_MAX_LEN];
    FILE *f = fopen(path, "r");
    int rc = AZH_OK;
    int i;

    assert(path != NULL);
    assert(sizeof line == LINE_MAX_LEN);
    if (f == NULL) {
        fprintf(stderr, "IOError: cannot read profile %s\n", path);
        printed = 1;
        return AZH_E_IO;
    }
    for (i = 0; i < 4096 && rc == AZH_OK && fgets(line, sizeof line, f) != NULL; i++) {
        size_t n = strlen(line);

        while (n > 0 && (line[n - 1] == '\n' || line[n - 1] == '\r')) {
            line[--n] = '\0';
        }
        if (n == 0 || line[0] == '#') {
            continue;
        }
        rc = apply_pair(line);
    }
    (void)fclose(f);     /* read-only */
    return rc;
}

static int build_batch(const args_t *a, azh_batch *b)
{
    char list[LINE_MAX_LEN];
    char *tok;
    char *save = NULL;

    assert(a != NULL && b != NULL);
    assert(a->frames >= 1);
    memset(b, 0, sizeof *b);
    b->frames = (int32_t)a->frames;
    if (snprintf(b->shot_dir, sizeof b->shot_dir, "%s", a->out) >= (int)sizeof b->shot_dir) {
        return -1;
    }
    if (a->shot_list == NULL) {
        return 0;
    }
    if (strlen(a->shot_list) >= sizeof list) {
        return -1;
    }
    memcpy(list, a->shot_list, strlen(a->shot_list) + 1);
    for (tok = strtok_r(list, ",", &save); tok != NULL; tok = strtok_r(NULL, ",", &save)) {
        char *end = NULL;
        long f = strtol(tok, &end, 10);

        if (*tok == '\0' || *end != '\0' || f < 1 || f > a->frames || b->n_shots >= AZH_MAX_SHOTS) {
            return -1;
        }
        b->shots[b->n_shots].frame = (int32_t)f;
        b->shots[b->n_shots].screens = AZH_SCREEN_BOTH;
        b->shots[b->n_shots].format = AZH_FMT_PNG;
        b->n_shots++;
    }
    return 0;
}

static int open_and_configure(const args_t *a)
{
    char log[AZH_PATH_MAX];
    char map[AZH_PATH_MAX];
    int rc;
    int i;

    assert(a != NULL && a->out != NULL && a->sys != NULL);
    assert(a->n_opts >= 0 && a->n_opts <= MAX_OPTS);
    if (make_dirs(a->out) != 0 || make_dirs(a->sys) != 0) {
        fprintf(stderr, "IOError: cannot create %s or %s\n", a->out, a->sys);
        printed = 1;
        return AZH_E_IO;
    }
    if (snprintf(log, sizeof log, "%s/host.log", a->out) >= (int)sizeof log ||
        snprintf(map, sizeof map, "%s/host.map", a->out) >= (int)sizeof map) {
        fprintf(stderr, "UsageError: --out path too long\n");
        printed = 1;
        return AZH_E_ARG;
    }
    if (a->mvk != NULL && setenv("LAZ_MVK", a->mvk, 1) != 0) {
        fprintf(stderr, "IOError: cannot set LAZ_MVK\n");
        printed = 1;
        return AZH_E_IO;
    }
    rc = azh_open(a->core, a->sys, log, map);
    if (rc != AZH_OK) {
        return rc;
    }
    rc = apply_profile(a->profile);
    for (i = 0; i < a->n_opts && rc == AZH_OK; i++) {
        rc = apply_pair(a->opts[i]);
    }
    return rc;
}

static int run_it(const args_t *a)
{
    azh_batch b;
    azh_result r;

    int rc;

    assert(a != NULL && a->app != NULL);
    assert(a->frames >= 1);
    memset(&b, 0, sizeof b);
    memset(&r, 0, sizeof r);
    rc = open_and_configure(a);

    if (rc == AZH_OK && build_batch(a, &b) != 0) {
        fprintf(stderr, "UsageError: bad --shot list (frames 1..%ld, at most %d)\n", a->frames, AZH_MAX_SHOTS);
        printed = 1;
        return AZH_E_ARG;
    }
    if (rc == AZH_OK) {
        rc = azh_boot(a->app, a->state);
    }
    if (rc == AZH_OK) {
        rc = azh_run(NULL, 0, &b, &r);
    }
    if (rc == AZH_OK) {
        printf("frames=%lld wall=%.2f fps=%.1f shots=%d\n", (long long)r.frames_run, r.wall_s,
               r.wall_s > 0.0 ? (double)r.frames_run / r.wall_s : 0.0, r.shots_done);
        return AZH_EXIT_OK;
    }
    return rc;
}

int main(int argc, char **argv)
{
    args_t a;
    int rc = parse_args(argc, argv, &a);
    int code;

    if (rc != AZH_OK) {
        return rc;
    }
    rc = run_it(&a);
    code = (rc == AZH_OK) ? AZH_EXIT_OK : report(rc);
    (void)azh_close();
    return code;
}
