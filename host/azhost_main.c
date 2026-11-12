/* azhost_main.c: the azhost program. "azhost run <app> ..." calls the same azh_* functions a Python worker will. */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include "azh_internal.h"

#define DEFAULT_PROFILE "host/options-default.txt"
#define DEFAULT_CORE "dl/azahar/azahar_libretro.dylib"
#define MAX_OPTS 64
#define LINE_MAX_LEN 512
#define MAX_BATCHES 16
#define TAIL_MAX 65536

static int printed;     /* the error line for the current failure is already on stderr */
static int guest_exit;  /* AZH_EXIT_GUEST_EXITED or _ERROR when a batch stopped that way on our core */

typedef struct {
    const char *app, *sys, *out, *profile, *core, *mvk, *state;
    long frames[MAX_BATCHES];
    int n_batches;
    const char *shot_list;
    const char *inputs_file, *sd_seed, *stop_file, *stop_text, *debug_stop, *print_last, *save;
    long stop_every, wall_limit_ms, raw_shot;
    int stop_new;
    const char *opts[MAX_OPTS];
    int n_opts;
} args_t;

static int usage_error(const char *what)
{
    assert(what != NULL);
    assert(AZH_EXIT_USAGE == 2);
    fprintf(stderr, "UsageError: %s\n", what);
    fprintf(stderr, "usage: azhost run <app> --sys <dir> --out <dir> --frames N[,N2,...] [--shot f1,f2,...]\n"
                    "              [--opt key=value]... [--profile file] [--core path] [--mvk path] [--state file]\n"
                    "              [--inputs file] [--sd-seed dir] [--stop-file rel --stop-text t [--stop-every k] [--stop-new]]\n"
                    "              [--debug-stop t] [--wall-limit-ms ms] [--raw-shot f] [--print-last-line rel] [--save file]\n"
                    "       azhost layout\n");
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

/* a whole-string decimal in lo..hi */
static int parse_long(const char *val, long lo, long hi, long *out)
{
    char *end = NULL;
    long n;

    assert(val != NULL && out != NULL);
    n = strtol(val, &end, 10);
    if (*val == '\0' || *end != '\0' || n < lo || n > hi) {
        return -1;
    }
    *out = n;
    return 0;
}

/* N[,N2,...]: up to MAX_BATCHES batch lengths */
static int parse_frames(args_t *a, const char *val)
{
    char list[LINE_MAX_LEN];
    char *tok;
    char *save = NULL;

    assert(a != NULL && val != NULL);
    if (strlen(val) >= sizeof list) {
        return -1;
    }
    memcpy(list, val, strlen(val) + 1);
    a->n_batches = 0;
    for (tok = strtok_r(list, ",", &save); tok != NULL; tok = strtok_r(NULL, ",", &save)) {
        if (a->n_batches >= MAX_BATCHES || parse_long(tok, 1, 100000000L, &a->frames[a->n_batches]) != 0) {
            return -1;
        }
        a->n_batches++;
    }
    return a->n_batches > 0 ? 0 : -1;
}

static int set_flag(args_t *a, const char *flag, const char *val)
{
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
        return parse_frames(a, val);
    } else if (strcmp(flag, "--inputs") == 0) {
        a->inputs_file = val;
    } else if (strcmp(flag, "--sd-seed") == 0) {
        a->sd_seed = val;
    } else if (strcmp(flag, "--stop-file") == 0) {
        a->stop_file = val;
    } else if (strcmp(flag, "--stop-text") == 0) {
        a->stop_text = val;
    } else if (strcmp(flag, "--debug-stop") == 0) {
        a->debug_stop = val;
    } else if (strcmp(flag, "--print-last-line") == 0) {
        a->print_last = val;
    } else if (strcmp(flag, "--save") == 0) {
        a->save = val;
    } else if (strcmp(flag, "--stop-every") == 0) {
        return parse_long(val, 1, 100000, &a->stop_every);
    } else if (strcmp(flag, "--wall-limit-ms") == 0) {
        return parse_long(val, 1, 2000000000L, &a->wall_limit_ms);
    } else if (strcmp(flag, "--raw-shot") == 0) {
        return parse_long(val, 1, 100000000L, &a->raw_shot);
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
        const char *val;

        if (strcmp(flag, "--stop-new") == 0) {
            a->stop_new = 1;
            continue;
        }
        val = flag_value(argc, argv, &i);

        if (val == NULL) {
            return usage_error("a flag is missing its value");
        }
        if (set_flag(a, flag, val) != 0) {
            fprintf(stderr, "UsageError: bad flag or value: %s %s\n", flag, val);
            return AZH_EXIT_USAGE;
        }
    }
    if (a->sys == NULL || a->out == NULL || a->n_batches == 0) {
        return usage_error("--sys, --out and --frames are required");
    }
    if ((a->stop_file == NULL) != (a->stop_text == NULL) || (a->stop_every != 0 && a->stop_file == NULL) ||
        (a->stop_new != 0 && a->stop_file == NULL)) {
        return usage_error("--stop-file and --stop-text go together; --stop-every and --stop-new need them");
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
    case AZH_E_NEEDS_LAZPY_CORE: cls = "NeedsLazpyCore"; code = AZH_EXIT_NEEDS_LAZPY; break;
    case AZH_E_UNSUPPORTED: cls = "Unsupported"; code = AZH_EXIT_UNSUPPORTED; break;
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

/* batch j (0-based): its frames and the wall limit; the first batch also gets the shots and the SD and debug rules */
static int build_batch(const args_t *a, int j, azh_batch *b)
{
    char list[LINE_MAX_LEN];
    char *tok;
    char *save = NULL;

    assert(a != NULL && b != NULL && j >= 0 && j < a->n_batches);
    memset(b, 0, sizeof *b);
    b->frames = (int32_t)a->frames[j];
    b->wall_limit_ms = (int32_t)a->wall_limit_ms;
    if (j > 0) {
        return 0;
    }
    if (snprintf(b->shot_dir, sizeof b->shot_dir, "%s", a->out) >= (int)sizeof b->shot_dir) {
        return -1;
    }
    if (a->stop_file != NULL &&
        (snprintf(b->sd_file, sizeof b->sd_file, "%s", a->stop_file) >= (int)sizeof b->sd_file ||
         snprintf(b->sd_text, sizeof b->sd_text, "%s", a->stop_text) >= (int)sizeof b->sd_text)) {
        return -1;
    }
    b->sd_every = (int32_t)a->stop_every;
    b->sd_from_end = a->stop_new;
    if (a->debug_stop != NULL && snprintf(b->debug_text, sizeof b->debug_text, "%s", a->debug_stop) >=
                                     (int)sizeof b->debug_text) {
        return -1;
    }
    if (a->raw_shot > 0) {
        if (a->raw_shot > a->frames[0]) {
            return -1;
        }
        b->shots[b->n_shots].frame = (int32_t)a->raw_shot;
        b->shots[b->n_shots].screens = AZH_SCREEN_BOTH;
        b->shots[b->n_shots].format = AZH_FMT_RAW;
        b->n_shots++;
    }
    if (a->shot_list == NULL) {
        return 0;
    }
    if (strlen(a->shot_list) >= sizeof list) {
        return -1;
    }
    memcpy(list, a->shot_list, strlen(a->shot_list) + 1);
    for (tok = strtok_r(list, ",", &save); tok != NULL; tok = strtok_r(NULL, ",", &save)) {
        long f;

        if (parse_long(tok, 1, a->frames[0], &f) != 0 || b->n_shots >= AZH_MAX_SHOTS) {
            return -1;
        }
        b->shots[b->n_shots].frame = (int32_t)f;
        b->shots[b->n_shots].screens = AZH_SCREEN_BOTH;
        b->shots[b->n_shots].format = AZH_FMT_PNG;
        b->n_shots++;
    }
    return 0;
}

/* one --inputs line: 7 integers (int32) separated by spaces, tabs or commas, '#' comment already cut.
   Returns the count parsed (0 for a blank line), or -1 for a bad token, a range error, or trailing junk. */
static int parse_input_line(char *line, int32_t rec[AZH_INPUT_INTS])
{
    char *p = line;
    int k;

    assert(line != NULL && rec != NULL);
    for (k = 0; k < AZH_INPUT_INTS; k++) {
        char *end = NULL;
        long v;

        while (*p == ' ' || *p == ',' || *p == '\t') {
            p++;
        }
        if (*p == '\0' || *p == '\n' || *p == '\r') {
            break;
        }
        errno = 0;
        v = strtol(p, &end, 0);
        if (end == p || errno == ERANGE || v < INT32_MIN || v > INT32_MAX) {
            return -1;
        }
        rec[k] = (int32_t)v;
        p = end;
    }
    while (*p == ' ' || *p == ',' || *p == '\t' || *p == '\r' || *p == '\n') {
        p++;
    }
    return (*p == '\0') ? k : -1;
}

/* --inputs: one record per line, '#' comments; the array is malloc'd */
static int load_inputs(const char *path, int32_t **recs, int32_t *n)
{
    char line[LINE_MAX_LEN];
    FILE *f = fopen(path, "r");
    int32_t cap = 0;
    long lines;

    assert(path != NULL && recs != NULL && n != NULL);
    *recs = NULL;
    *n = 0;
    if (f == NULL) {
        fprintf(stderr, "IOError: cannot read inputs file %s\n", path);
        printed = 1;
        return AZH_E_IO;
    }
    for (lines = 0; lines < 4 * (long)AZH_MAX_INPUTS && fgets(line, sizeof line, f) != NULL; lines++) {
        char *hash = strchr(line, '#');
        int32_t rec[AZH_INPUT_INTS];
        int k;

        if (hash != NULL) {
            *hash = '\0';
        }
        k = parse_input_line(line, rec);
        if (k == 0) {
            continue;       /* blank or comment */
        }
        if (k != AZH_INPUT_INTS || *n >= AZH_MAX_INPUTS) {
            fprintf(stderr, "UsageError: %s line %ld: want %d integers\n", path, lines + 1, AZH_INPUT_INTS);
            printed = 1;
            (void)fclose(f);
            free(*recs);
            *recs = NULL;
            return AZH_E_ARG;
        }
        if (*n >= cap) {
            int32_t ncap = (cap == 0) ? 256 : cap * 2;
            int32_t *grown = realloc(*recs, (size_t)ncap * AZH_INPUT_INTS * sizeof **recs);

            if (grown == NULL) {
                (void)fclose(f);
                free(*recs);
                *recs = NULL;
                return AZH_E_NOMEM;
            }
            *recs = grown;
            cap = ncap;
        }
        memcpy(*recs + (size_t)*n * AZH_INPUT_INTS, rec, sizeof rec);
        (*n)++;
    }
    (void)fclose(f);
    return AZH_OK;
}

/* --sd-seed DIR: copied to <sys>/Azahar/sdmc, which must not exist yet */
static int seed_sd(const args_t *a)
{
    char azahar[AZH_PATH_MAX];
    char sdmc[AZH_PATH_MAX];
    int rc;

    assert(a != NULL && a->sd_seed != NULL);
    if (snprintf(azahar, sizeof azahar, "%s/Azahar", a->sys) >= (int)sizeof azahar ||
        snprintf(sdmc, sizeof sdmc, "%s/sdmc", azahar) >= (int)sizeof sdmc || make_dirs(azahar) != 0) {
        fprintf(stderr, "UsageError: --sys path too long or not writable\n");
        printed = 1;
        return AZH_E_ARG;
    }
    rc = azh__copy_tree(a->sd_seed, sdmc);
    if (rc != AZH_OK) {
        fprintf(stderr, "UsageError: --sd-seed %s could not be copied to %s (the destination must not exist)\n",
                a->sd_seed, sdmc);
        printed = 1;
    }
    return rc;
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
    if (a->sd_seed != NULL && seed_sd(a) != AZH_OK) {
        return AZH_E_ARG;
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

static const char *stop_name(int32_t reason)
{
    static const char *const names[7] = { "frames", "sd_text", "debug_text", "guest_break", "guest_exited",
                                          "guest_error", "wall_limit" };

    return (reason >= 0 && reason < 7) ? names[reason] : "unknown";
}

/* the message with \ as \\ and newlines as \n, quotes left alone */
static void print_escaped(const char *m)
{
    for (; *m != '\0'; m++) {
        if (*m == '\\') {
            fputs("\\\\", stdout);
        } else if (*m == '\n') {
            fputs("\\n", stdout);
        } else if (*m != '\r') {
            fputc(*m, stdout);
        }
    }
}

/* "last <j>: <last complete line of <sys>/Azahar/sdmc/REL>" */
static void print_last_line(const args_t *a, int j)
{
    static char tail[TAIL_MAX + 1];
    char path[AZH_PATH_MAX];
    FILE *f;
    size_t n;
    char *end;
    char *start;

    assert(a != NULL && a->print_last != NULL);
    if (snprintf(path, sizeof path, "%s/Azahar/sdmc/%s", a->sys, a->print_last) >= (int)sizeof path) {
        return;
    }
    f = fopen(path, "r");
    if (f == NULL) {
        printf("last %d:\n", j + 1);
        return;
    }
    if (fseek(f, 0, SEEK_END) == 0 && ftell(f) > (long)TAIL_MAX) {
        (void)fseek(f, -(long)TAIL_MAX, SEEK_END);
    } else {
        (void)fseek(f, 0, SEEK_SET);
    }
    n = fread(tail, 1, TAIL_MAX, f);
    (void)fclose(f);
    tail[n] = '\0';
    end = strrchr(tail, '\n');
    if (end == NULL) {
        printf("last %d:\n", j + 1);
        return;
    }
    *end = '\0';
    start = strrchr(tail, '\n');
    printf("last %d: %s\n", j + 1, start != NULL ? start + 1 : tail);
}

static void print_summary(const args_t *a, const azh_result *r, int j)
{
    double frame_ms = r->frames_run > 0 ? r->wall_s * 1000.0 / (double)r->frames_run : 0.0;

    printf("frames=%lld wall=%.2f fps=%.1f shots=%d stop=%s first=%lld last=%lld vblanks=%lld wall_ms_mean=%.2f "
           "batch=%d msg=\"", (long long)r->frames_run, r->wall_s,
           r->wall_s > 0.0 ? (double)r->frames_run / r->wall_s : 0.0, r->shots_done, stop_name(r->stop_reason),
           (long long)r->first_frame, (long long)r->last_frame, (long long)r->vblanks, frame_ms, j + 1);
    print_escaped(r->message);
    printf("\"\n");
    if (a->print_last != NULL) {
        print_last_line(a, j);
    }
    fflush(stdout);
}

/* --save after the last batch; until step D fills state.c this is "Unsupported:" */
static int save_state(const char *path)
{
    int32_t k = 0;
    struct azh_stats st;
    int rc = azh_save_state(path, &k);

    if (rc == AZH_OK && azh_stats(&st) == AZH_OK) {
        printf("saved k=%d frame=%lld\n", (int)k, (long long)st.frames);
    }
    return rc;
}

/* every batch in order; a guest exit or error (our core) ends the run with its exit code after the summary */
static int run_batches(const args_t *a, const int32_t *recs, int32_t n_recs)
{
    azh_batch b;
    azh_result r;
    int rc = AZH_OK;
    int j;

    assert(a != NULL && a->n_batches >= 1);
    for (j = 0; j < a->n_batches && rc == AZH_OK; j++) {
        if (build_batch(a, j, &b) != 0) {
            fprintf(stderr, "UsageError: bad --shot, --raw-shot or stop-rule value (frames 1..%ld)\n", a->frames[0]);
            printed = 1;
            return AZH_E_ARG;
        }
        memset(&r, 0, sizeof r);
        rc = azh_run(j == 0 ? recs : NULL, j == 0 ? n_recs : 0, &b, &r);
        if (rc != AZH_OK) {
            return rc;
        }
        print_summary(a, &r, j);
        if (r.stop_reason == AZH_STOP_GUEST_EXITED || r.stop_reason == AZH_STOP_GUEST_ERROR) {
            guest_exit = (r.stop_reason == AZH_STOP_GUEST_EXITED) ? AZH_EXIT_GUEST_EXITED : AZH_EXIT_GUEST_ERROR;
            return AZH_OK;
        }
    }
    return a->save != NULL ? save_state(a->save) : AZH_OK;
}

static int run_it(const args_t *a)
{
    int32_t *recs = NULL;
    int32_t n_recs = 0;
    int rc;

    assert(a != NULL && a->app != NULL);
    assert(a->n_batches >= 1);
    rc = (a->inputs_file != NULL) ? load_inputs(a->inputs_file, &recs, &n_recs) : AZH_OK;
    if (rc == AZH_OK) {
        rc = open_and_configure(a);
    }
    if (rc == AZH_OK) {
        rc = azh_boot(a->app, a->state);
    }
    if (rc == AZH_OK) {
        rc = run_batches(a, recs, n_recs);
    }
    free(recs);
    return rc;
}

/* "azhost layout": the ABI table, one line per fields[] entry */
static int print_layout(void)
{
    static azh_layout lay;
    int32_t i;

    if (azh_abi_layout(&lay) != AZH_OK) {
        fprintf(stderr, "HostError: %s\n", azh_error());
        return AZH_EXIT_USAGE;
    }
    printf("abi=%u\n", (unsigned)lay.abi);
    for (i = 0; i < lay.n_fields && i < AZH_MAX_FIELDS; i++) {
        printf("%s %d %d\n", lay.fields[i].name, (int)lay.fields[i].offset, (int)lay.fields[i].size);
    }
    return AZH_EXIT_OK;
}

int main(int argc, char **argv)
{
    args_t a;
    int rc;
    int code;

    if (argc == 2 && strcmp(argv[1], "layout") == 0) {
        return print_layout();
    }
    rc = parse_args(argc, argv, &a);

    if (rc != AZH_OK) {
        return rc;
    }
    rc = run_it(&a);
    if (rc == AZH_OK) {
        code = guest_exit;
    } else {
        code = report(rc);
    }
    (void)azh_close();
    return code;
}
