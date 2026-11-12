/* options.c: the option store. SET_VARIABLES copies every key and its allowed values (the core's strings are
 * local vectors that die when the call returns); azh_set_option validates against them. */
#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "azh_internal.h"

#define VARS_SCAN_MAX 4096

static azh_opt *find_opt(const char *key)
{
    int i;

    assert(key != NULL);
    for (i = 0; i < azh_g.n_opts; i++) {
        if (strcmp(azh_g.opts[i].key, key) == 0) {
            return &azh_g.opts[i];
        }
    }
    return NULL;
}

/* the V0 format is "Description; default|other|..."; keep what follows "; " */
static const char *allowed_part(const char *desc)
{
    const char *sc = strstr(desc, "; ");

    return (sc != NULL) ? sc + 2 : "";
}

static void add_opt(const struct retro_variable *v)
{
    azh_opt *o;

    if (v->value == NULL || strlen(v->key) >= AZH_OPT_KEY_MAX) {
        azh_log(AZH_LOG_WARN, "option %s skipped (bad key or value text)", v->key);
        return;
    }
    if (find_opt(v->key) != NULL) {
        return;
    }
    if (azh_g.n_opts >= AZH_MAX_OPTS) {
        azh_log(AZH_LOG_WARN, "option store full (%d keys); %s ignored", AZH_MAX_OPTS, v->key);
        return;
    }
    o = &azh_g.opts[azh_g.n_opts];
    memset(o, 0, sizeof *o);
    memcpy(o->key, v->key, strlen(v->key) + 1u);
    o->allowed = strdup(allowed_part(v->value));
    if (o->allowed == NULL) {
        azh_log(AZH_LOG_ERROR, "out of memory registering option %s", v->key);
        return;
    }
    azh_g.n_opts++;
}

void azh_opts_register(const struct retro_variable *vars)
{
    int i;

    assert(vars != NULL);
    for (i = 0; i < VARS_SCAN_MAX && vars[i].key != NULL; i++) {
        add_opt(&vars[i]);
    }
    azh_log(AZH_LOG_INFO, "core registered %d option keys", azh_g.n_opts);
}

/* is value one of the '|' separated words of list? An empty list accepts anything. */
static int value_listed(const char *list, const char *value)
{
    size_t vl = strlen(value);
    const char *p = list;
    const char *bar;
    int i;

    if (*list == '\0') {
        return 1;
    }
    for (i = 0; i < AZH_MAX_OPTS * 4; i++) {
        bar = strchr(p, '|');
        if (strncmp(p, value, vl) == 0 && (p[vl] == '|' || p[vl] == '\0')) {
            return 1;
        }
        if (bar == NULL) {
            return 0;
        }
        p = bar + 1;
    }
    return 0;
}

static int all_digits(const char *s)
{
    size_t i;

    if (*s == '\0') {
        return 0;
    }
    for (i = 0; s[i] != '\0'; i++) {
        if (s[i] < '0' || s[i] > '9') {
            return 0;
        }
    }
    return 1;
}

int azh_opts_set(const char *key, const char *value)
{
    azh_opt *o;

    assert(key != NULL && value != NULL);
    o = find_opt(key);
    if (o == NULL) {
        return azh_fail(AZH_E_ARG, "unknown option key %s (the core did not register it)", key);
    }
    if (strlen(value) >= AZH_OPT_VAL_MAX) {
        return azh_fail(AZH_E_ARG, "option %s: value too long", key);
    }
    if (strcmp(key, "citra_init_time") == 0) {
        if (all_digits(value) == 0) {
            return azh_fail(AZH_E_ARG, "option %s: %s is not a decimal number", key, value);
        }
    } else if (value_listed(o->allowed, value) == 0) {
        return azh_fail(AZH_E_ARG, "option %s: value '%s' is not one of: %s", key, value, o->allowed);
    }
    memcpy(o->value, value, strlen(value) + 1u);
    o->is_set = 1;
    return AZH_OK;
}

int azh_opts_get(struct retro_variable *var)
{
    azh_opt *o;

    assert(var != NULL && var->key != NULL);
    o = find_opt(var->key);
    if (o != NULL && o->is_set != 0) {
        var->value = o->value;
        return 1;
    }
    if (o == NULL || o->warned == 0) {
        if (o != NULL) {
            o->warned = 1;
        }
        if (o != NULL || azh_g.n_unset_warned < 16) {
            if (o == NULL) {
                azh_g.n_unset_warned++;
            }
            azh_log(AZH_LOG_WARN, "GET_VARIABLE %s: no value set, the core uses its default", var->key);
        }
    }
    return 0;
}

void azh_opts_log(void)
{
    int i;

    assert(azh_g.n_opts >= 0 && azh_g.n_opts <= AZH_MAX_OPTS);
    for (i = 0; i < azh_g.n_opts; i++) {
        const azh_opt *o = &azh_g.opts[i];

        azh_log(AZH_LOG_INFO, "option %s=%s", o->key, (o->is_set != 0) ? o->value : "(core default)");
    }
}

void azh_opts_free(void)
{
    int i;

    for (i = 0; i < azh_g.n_opts; i++) {
        free(azh_g.opts[i].allowed);
        azh_g.opts[i].allowed = NULL;
    }
    azh_g.n_opts = 0;
}
