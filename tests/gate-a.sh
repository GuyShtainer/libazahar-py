#!/bin/sh
# gate-a.sh: step A's gate. usage: tests/gate-a.sh <app.3dsx>   (build/testapp.3dsx once step B exists)
# Prints one PASS/FAIL line per check, exits non-zero on any FAIL. KEEP=1 keeps the temporary copy.
set -eu
[ $# -eq 1 ] || { echo "usage: $0 <app.3dsx>" >&2; exit 2; }
REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
COPY=$(mktemp -d "${TMPDIR:-/tmp}/lazpy-gate-a.XXXXXX")
BGPID=""
cleanup() {
    if [ -n "$BGPID" ] && kill -0 "$BGPID" 2>/dev/null; then kill "$BGPID" 2>/dev/null || true; fi
    if [ "${KEEP:-0}" != 1 ]; then rm -rf "${COPY:?}"; else echo "kept $COPY"; fi
}
trap cleanup EXIT
FAILS=0
pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; FAILS=$((FAILS + 1)); }
# png_size FILE: prints "W H" read from the IHDR
png_size() {
    python3 -I -c 'import struct,sys; d=open(sys.argv[1],"rb").read(24); print(*struct.unpack(">II",d[16:24]))' "$1"
}

# 1. fresh copy: tracked and new non-ignored files, dl/ and vendor/ symlinked in
# (vendor and dl are left out of the list: in a clone they may be symlinks that git lists as untracked files)
(cd "$REPO" && git ls-files -z --cached --others --exclude-standard | grep -zvE '^(vendor|dl)(/|$)' \
    | tar -cf - --null -T -) | tar -xf - -C "$COPY"
mkdir -p "$COPY/dl"
ln -sfn "$REPO/vendor" "$COPY/vendor"
for d in azahar moltenvk libretro-headers vulkan-headers; do ln -sfn "$REPO/dl/$d" "$COPY/dl/$d"; done
cd "$COPY"
FRC=0
sh tools/fetch.sh >fetch.out 2>&1 || FRC=$?
OTHER=$(sed -n '/^$/q;p' fetch.out | grep -vc '^have   ' || true)
if [ "$FRC" -eq 0 ] && [ "$OTHER" -eq 0 ] && grep -q '^have   ' fetch.out; then pass "1 fresh copy, fetch.sh exits 0 and prints only have lines"
else fail "1 fetch.sh exit $FRC or non-have lines (see $COPY/fetch.out)"; fi

# 2. zero warnings
if (make check && make && make test-version) >build.log 2>&1 && [ "$(grep -ci warning build.log)" -eq 0 ] \
   && grep -q '^test-version ok$' build.log; then pass "2 zero warnings, check/make/test-version"; else fail "2 build (see $COPY/build.log)"; fi

# 3. two screens
mkdir -p runs/g
printf 'not a 3dsx\n' > runs/g/bad.3dsx
if nice -n 10 build/azhost run "$APP" --sys runs/g/sys --out runs/g/out --frames 600 --shot 300,600 >runs/g/run3.txt 2>&1; then
    OK=1
    for s in 000300 000600; do
        [ "$(png_size "runs/g/out/shot_${s}_top.png")" = "400 240" ] || OK=0
        [ "$(png_size "runs/g/out/shot_${s}_bottom.png")" = "320 240" ] || OK=0
    done
    [ "$(grep -c '^\[info\] option citra_' runs/g/out/host.log)" -ge 32 ] || OK=0
    grep -q '^\[info\] core Azahar version ' runs/g/out/host.log || OK=0
    if [ "$OK" -eq 1 ]; then pass "3 two screens, 400x240 and 320x240, log lines"; else fail "3 shots or host.log wrong"; fi
else fail "3 azhost run exited non-zero"; fi

# 4. no window: its own 3000-frame run in the background
nice -n 10 build/azhost run "$APP" --sys runs/g/sys4 --out runs/g/out4 --frames 3000 >runs/g/run4.txt 2>&1 &
BGPID=$!
hb() { python3 -I -c 'import struct,sys; print(struct.unpack("<Q",open(sys.argv[1],"rb").read(24)[16:24])[0])' "$1" 2>/dev/null || echo 0; }
N=0
while [ "$N" -lt 120 ] && [ "$(hb runs/g/out4/host.map)" -eq 0 ]; do sleep 1; N=$((N + 1)); done
if [ "$(hb runs/g/out4/host.map)" -eq 0 ]; then fail "4 heartbeat never rose within 120 s"
elif ! kill -0 "$BGPID" 2>/dev/null; then fail "4 run ended before the check"
else
    LRC=0
    LIST=$(lsappinfo list 2>/dev/null) || LRC=$?
    SEEN=$(printf '%s\n' "$LIST" | grep -E "pid = $BGPID( |\$)" || true)
    if [ "$LRC" -ne 0 ] || [ -z "$LIST" ]; then fail "4 lsappinfo failed or printed nothing (the check would be vacuous)"
    elif [ -n "$SEEN" ]; then fail "4 the process has a window or app entry"
    elif ! kill -0 "$BGPID" 2>/dev/null; then fail "4 run ended before the check"
    else pass "4 no window (heartbeat up, no lsappinfo entry)"; fi
fi
N=0
while [ "$N" -lt 300 ] && kill -0 "$BGPID" 2>/dev/null; do sleep 1; N=$((N + 1)); done
if kill -0 "$BGPID" 2>/dev/null; then kill "$BGPID" 2>/dev/null || true; echo "note: 3000-frame run killed after 300 s"; fi
wait "$BGPID" 2>/dev/null || true
BGPID=""

# 5. boot failures
for pair in "/nonexistent/x.3dsx|Failed to obtain loader" "runs/g/bad.3dsx|Failed to load ROM"; do
    f=${pair%%|*}
    want=${pair#*|}
    RC=0
    nice -n 10 build/azhost run "$f" --sys runs/g/sys5 --out runs/g/out5 --frames 5 >/dev/null 2>runs/g/err5.txt || RC=$?
    if [ "$RC" -eq 3 ] && grep -q "^BootError: .*$want" runs/g/err5.txt; then pass "5 boot failure exit 3 for $f"; else fail "5 boot failure for $f (exit $RC)"; fi
done

# 6. core checks
RC=0
build/azhost run x --core build/libazhost.dylib --sys runs/g/sys6 --out runs/g/out6 --frames 5 >/dev/null 2>runs/g/err6.txt || RC=$?
if [ "$RC" -eq 4 ] && grep -q '^CoreError: missing symbol retro_' runs/g/err6.txt; then pass "6a wrong core exits 4 with missing symbol"; else fail "6a (exit $RC)"; fi
if grep -q '^test-version ok$' build.log; then pass "6b version rule proven by make test-version"; else fail "6b test-version"; fi

[ "$FAILS" -eq 0 ]
