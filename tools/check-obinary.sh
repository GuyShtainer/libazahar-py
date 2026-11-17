#!/bin/sh
# Every open( call in host/ must carry O_BINARY (the flag is 0 where files have no text mode; Windows CRLF-translates
# without it). fopen, dlopen, azh_open, _open and the like do not count. Comment text is dropped first, so a word in a
# comment neither makes a site nor satisfies one. Fewer than MIN_SITES sites is a failure too (the tree moved, or the
# search broke). Exit 0 and "check-obinary: ok N open() sites", or exit 1 and the offending lines. Run from the repo
# root or anywhere: the path is resolved from this script.
MIN_SITES=11
root=$(cd "$(dirname "$0")/.." && pwd)
# file:line:text, with /* ... */ and // text removed from the text part
code=$(grep -rnE '.' "$root/host" --include='*.c' --include='*.h' | sed -E -e 's|/\*[^*]*\*/||g' -e 's|//.*$||' -e 's|/\*.*$||')
all=$(printf '%s\n' "$code" | grep -E '^[^:]*:[0-9]+:.*(^|[^A-Za-z0-9_])open[[:space:]]*\(' | grep -v '^[^:]*:[0-9]*:[[:space:]]*\*')
total=$(printf '%s\n' "$all" | grep -c . || true)
bad=$(printf '%s\n' "$all" | grep -v 'O_BINARY' | grep . || true)
if [ -n "$bad" ]; then
    echo "check-obinary: FAIL, open() without O_BINARY:"
    printf '%s\n' "$bad"
    exit 1
fi
if [ "$total" -lt "$MIN_SITES" ]; then
    echo "check-obinary: FAIL, found $total open() sites, expected at least $MIN_SITES"
    exit 1
fi
echo "check-obinary: ok $total open() sites"
