#!/bin/sh
# Every open( call in host/ must carry O_BINARY (the flag is 0 where files have no text mode; Windows CRLF-translates
# without it). fopen, dlopen, azh_open, _open and the like do not count. Exit 0 and "check-obinary: ok N open() sites",
# or exit 1 and the offending lines. Run from the repo root or anywhere: the path is resolved from this script.
root=$(cd "$(dirname "$0")/.." && pwd)
all=$(grep -rnE '(^|[^A-Za-z0-9_])open[[:space:]]*\(' "$root/host" --include='*.c' --include='*.h' | grep -v '^[^:]*:[0-9]*:[[:space:]]*\(/\*\|\*\|//\)')
total=$(printf '%s\n' "$all" | grep -c . || true)
bad=$(printf '%s\n' "$all" | grep -v 'O_BINARY' | grep . || true)
if [ -n "$bad" ]; then
    echo "check-obinary: FAIL, open() without O_BINARY:"
    printf '%s\n' "$bad"
    exit 1
fi
echo "check-obinary: ok $total open() sites"
