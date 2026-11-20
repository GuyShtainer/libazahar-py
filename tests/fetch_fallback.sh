#!/bin/sh
# fetch_fallback.sh: tests tools/fetch.sh's fallback to the previous release (plan D7) against two local folders that
# stand for the current and the previous release page. No network: LAZ_RELEASE_BASE is always set. Run it with `sh`
# (the MSYS2 MINGW64 shell on Windows, or any sh on macOS). Prints "ok <case>" per case and "fetch_fallback: N cases
# passed" at the end; any failed case prints "FAIL <case>" and the run exits 1.
set -eu

HERE=$(cd "$(dirname "$0")/.." && pwd)
T=$(mktemp -d "${TMPDIR:-/tmp}/fetchfb.XXXXXX")
trap 'rm -rf "$T"' EXIT
if command -v shasum >/dev/null 2>&1; then sha() { shasum -a 256 "$1" | cut -d' ' -f1; }; else sha() { sha256sum "$1" | cut -d' ' -f1; }; fi

CUR="$T/cur"; PREV="$T/prev"; mkdir -p "$CUR" "$PREV" "$T/pack"
MAC_ZIP=azahar_lazpy_libretro-2126.2-lazpy.2-macos-arm64.zip
WIN_ZIP=azahar_lazpy_libretro-2126.2-lazpy.2-windows-x64.zip

# stand-in assets: harmless text, never a real core
pack() {  # pack ZIP CORE_FILE TEXT DEST
  rm -rf "$T/pack"; mkdir -p "$T/pack"
  printf '%s\n' "$3" > "$T/pack/$2"; echo "notices" > "$T/pack/NOTICES.md"; echo "source" > "$T/pack/SOURCE.md"
  rm -f "$4/$1"; (cd "$T/pack" && zip -q -X "$4/$1" "$2" NOTICES.md SOURCE.md)
}
pack "$MAC_ZIP" azahar_lazpy_libretro.dylib "mac stand-in" "$PREV"
pack "$WIN_ZIP" azahar_lazpy_libretro.dll "windows stand-in" "$PREV"
echo "test app stand-in" > "$PREV/testapp.3dsx"
# the host zips of tag v1.1.0 (stand-ins: harmless text), on their own page
HOSTREL="$T/hostrel"; mkdir -p "$HOSTREL"
HOST_MAC_ZIP=libazahar-py-host-1.1.0-macos-arm64.zip
HOST_WIN_ZIP=libazahar-py-host-1.1.0-windows-x64.zip
hostpack() {  # hostpack ZIP LIB EXE [NOTICES.md]  (the Windows zip carries NOTICES.md, the macOS zip does not)
  rm -rf "$T/pack"; mkdir -p "$T/pack"
  echo "lib stand-in" > "$T/pack/$2"; echo "exe stand-in" > "$T/pack/$3"; echo "licence" > "$T/pack/LICENSE"
  echo "built at commit 0123456789abcdef0123456789abcdef01234567" > "$T/pack/SOURCE.md"
  [ -z "${4:-}" ] || echo "notices" > "$T/pack/$4"
  rm -f "$HOSTREL/$1"; (cd "$T/pack" && zip -q -X "$HOSTREL/$1" "$2" "$3" ${4:-} LICENSE SOURCE.md)
}
hostpack "$HOST_MAC_ZIP" libazhost.dylib azhost
hostpack "$HOST_WIN_ZIP" libazhost.dll azhost.exe NOTICES.md
MAC_SHA=$(sha "$PREV/$MAC_ZIP"); WIN_SHA=$(sha "$PREV/$WIN_ZIP"); APP_SHA=$(sha "$PREV/testapp.3dsx")

# a copy of fetch.sh with the pins of these stand-ins, as the release would have them
mkdir -p "$T/tools"
sed -e "s/^REL_TAG=.*/REL_TAG=v1.1.0/" -e "s/^REL_TAG_PREV=.*/REL_TAG_PREV=v1.0.0/" \
    -e "s/^LAZPY_CORE_SHA=.*/LAZPY_CORE_SHA=$MAC_SHA/" -e "s/^TESTAPP_SHA=.*/TESTAPP_SHA=$APP_SHA/" \
    -e "s/^LAZPY_CORE_SHA_WIN=.*/LAZPY_CORE_SHA_WIN=$WIN_SHA/" \
    -e "s/^LAZPY_HOST_SHA_MAC=.*/LAZPY_HOST_SHA_MAC=$(sha "$HOSTREL/$HOST_MAC_ZIP")/" \
    -e "s/^LAZPY_HOST_SHA_WIN=.*/LAZPY_HOST_SHA_WIN=$(sha "$HOSTREL/$HOST_WIN_ZIP")/" "$HERE/tools/fetch.sh" > "$T/tools/fetch.sh"
# the same script with its host pins left as the repo has them (TBD or filled), for the "TBD dies" case
sed -e "s/^LAZPY_HOST_SHA_MAC=.*/LAZPY_HOST_SHA_MAC=TBD/" -e "s/^LAZPY_HOST_SHA_WIN=.*/LAZPY_HOST_SHA_WIN=TBD/" \
    "$T/tools/fetch.sh" > "$T/tools/fetch-tbd.sh"

N=0; BAD=0
pass() { N=$((N + 1)); echo "ok $1"; }
fail() { BAD=$((BAD + 1)); echo "FAIL $1"; }
# run_fetch OS ARGS...: a fresh root, then fetch.sh with CUR as LAZ_RELEASE_BASE (and PREV as the previous page when
# PREV_ON is set); output in $T/out, status in $RC
run_fetch() {
  _os=$1; shift
  rm -rf "$T/root"; mkdir -p "$T/root"
  RC=0
  if [ -n "$PREV_ON" ]; then
    LAZ_ROOT="$T/root" LAZ_RELEASE_BASE="file://$CUR" LAZ_RELEASE_BASE_PREV="file://$PREV" LAZ_FETCH_OS="$_os" \
      sh "$T/tools/fetch.sh" "$@" > "$T/out" 2>&1 || RC=$?
  else
    env -u LAZ_RELEASE_BASE_PREV LAZ_ROOT="$T/root" LAZ_RELEASE_BASE="file://$CUR" LAZ_FETCH_OS="$_os" \
      sh "$T/tools/fetch.sh" "$@" > "$T/out" 2>&1 || RC=$?
  fi
}
has() { grep -q "$1" "$T/out"; }

# 1: the macOS zip and the test app are missing from the current page: both fall back and print the notice
PREV_ON=1; run_fetch Darwin --lazpy-core --testapp
if [ "$RC" -eq 0 ] && has "fell back to v1.0.0 for $MAC_ZIP" && has "fell back to v1.0.0 for testapp.3dsx" \
   && [ -f "$T/root/dl/lazpy-core/azahar_lazpy_libretro.dylib" ] && [ -f "$T/root/build/testapp.3dsx" ]; then
  pass "missing from current: falls back to v1.0.0 and prints the notice"; else fail "fallback"; cat "$T/out"; fi

# 2: the asset is on the current page: no fallback line (LAZ_FETCH_OS=Darwin picks the Mac zip on any host)
cp "$PREV/$MAC_ZIP" "$PREV/testapp.3dsx" "$CUR/"
PREV_ON=1; run_fetch Darwin --lazpy-core --testapp
if [ "$RC" -eq 0 ] && ! has "fell back" && [ -f "$T/root/dl/lazpy-core/azahar_lazpy_libretro.dylib" ]; then
  pass "LAZ_FETCH_OS=Darwin: the Mac zip comes from the current page, no fallback"; else fail "darwin current"; cat "$T/out"; fi

# 3: a wrong-sha file on the current page dies with no fallback, and the file is deleted
echo "tampered" > "$CUR/$MAC_ZIP"
PREV_ON=1; run_fetch Darwin --lazpy-core
if [ "$RC" -ne 0 ] && has "SHA256 MISMATCH" && ! has "fell back" && [ ! -e "$T/root/dl/lazpy-core/$MAC_ZIP" ]; then
  pass "wrong sha256 on the current page: dies, deletes the file, no fallback"; else fail "mismatch"; cat "$T/out"; fi
echo "tampered" > "$CUR/testapp.3dsx"
PREV_ON=1; run_fetch Darwin --testapp
if [ "$RC" -ne 0 ] && has "SHA256 MISMATCH" && ! has "fell back"; then
  pass "wrong sha256 test app: dies, no fallback"; else fail "mismatch app"; cat "$T/out"; fi

# 4: LAZ_RELEASE_BASE set, LAZ_RELEASE_BASE_PREV not: no fallback, so a local base never reaches the network
rm -f "$CUR/$MAC_ZIP" "$CUR/testapp.3dsx"
PREV_ON=""; run_fetch Darwin --lazpy-core
if [ "$RC" -ne 0 ] && has "download failed" && ! has "fell back"; then
  pass "LAZ_RELEASE_BASE without LAZ_RELEASE_BASE_PREV: no fallback"; else fail "no prev base"; cat "$T/out"; fi

# 5: the Windows zip is missing from the current page: dies, never falls back (the previous page has one)
PREV_ON=1; run_fetch MINGW64_NT-10.0 --lazpy-core
if [ "$RC" -ne 0 ] && has "v1.1.0 is not published yet" && ! has "fell back"; then
  pass "Windows zip missing: dies with 'v1.1.0 is not published yet', no fallback"; else fail "windows missing"; cat "$T/out"; fi

# 6: the Windows zip on the current page: its dll is unpacked and MoltenVK is skipped
cp "$PREV/$WIN_ZIP" "$CUR/"
PREV_ON=1; run_fetch MINGW64_NT-10.0 --moltenvk --lazpy-core
if [ "$RC" -eq 0 ] && [ -f "$T/root/dl/lazpy-core/azahar_lazpy_libretro.dll" ] && has "skip   MoltenVK"; then
  pass "Windows zip present: the dll is unpacked and MoltenVK is skipped"; else fail "windows ok"; cat "$T/out"; fi

# 7: --host on macOS: the zip is verified, the two binaries land in build/, the zip stays in dl/lazpy-host/
host_run() {  # host_run SCRIPT OS BASE ARGS...
  _s=$1; _os=$2; _b=$3; shift 3
  rm -rf "$T/root"; mkdir -p "$T/root"; RC=0
  env -u LAZ_RELEASE_BASE_PREV LAZ_ROOT="$T/root" LAZ_RELEASE_BASE="file://$_b" LAZ_FETCH_OS="$_os" \
    sh "$_s" "$@" > "$T/out" 2>&1 || RC=$?
}
host_run "$T/tools/fetch.sh" Darwin "$HOSTREL" --host
if [ "$RC" -eq 0 ] && [ -f "$T/root/build/libazhost.dylib" ] && [ -f "$T/root/build/azhost" ] \
   && [ ! -e "$T/root/build/azhost.exe" ] && [ -f "$T/root/dl/lazpy-host/$HOST_MAC_ZIP" ] && ! has "fell back"; then
  pass "--host on macOS: libazhost.dylib and azhost land in build/"; else fail "host mac"; cat "$T/out"; fi
# a second run downloads nothing
RC=0; env -u LAZ_RELEASE_BASE_PREV LAZ_ROOT="$T/root" LAZ_RELEASE_BASE="file://$T/nowhere" LAZ_FETCH_OS=Darwin \
  sh "$T/tools/fetch.sh" --host > "$T/out" 2>&1 || RC=$?
if [ "$RC" -eq 0 ] && has "have   " && ! has "fetch  "; then
  pass "--host a second time: downloads nothing"; else fail "host again"; cat "$T/out"; fi

# a host built with make (other bytes in build/) is replaced by a plain --host, as docs/USING.md says
echo "built with make" > "$T/root/build/azhost"
RC=0; env -u LAZ_RELEASE_BASE_PREV LAZ_ROOT="$T/root" LAZ_RELEASE_BASE="file://$T/nowhere" LAZ_FETCH_OS=Darwin \
  sh "$T/tools/fetch.sh" --host > "$T/out" 2>&1 || RC=$?
if [ "$RC" -eq 0 ] && has "unpack " && [ "$(cat "$T/root/build/azhost")" = "exe stand-in" ]; then
  pass "--host over a make-built host: replaces it with the release's file"; else fail "host replaces make build"; cat "$T/out"; fi

# 8: --host on Windows
host_run "$T/tools/fetch.sh" MINGW64_NT-10.0 "$HOSTREL" --host
if [ "$RC" -eq 0 ] && [ -f "$T/root/build/libazhost.dll" ] && [ -f "$T/root/build/azhost.exe" ] \
   && [ ! -e "$T/root/build/libazhost.dylib" ] && [ -f "$T/root/dl/lazpy-host/unpacked/NOTICES.md" ]; then
  pass "--host on Windows: libazhost.dll and azhost.exe land in build/, NOTICES.md is unpacked beside SOURCE.md"; else fail "host win"; cat "$T/out"; fi

# 9: a TBD pin dies with one clear line and downloads nothing
host_run "$T/tools/fetch-tbd.sh" Darwin "$HOSTREL" --host
if [ "$RC" -ne 0 ] && has "pins are filled at release time" && [ "$(grep -c . "$T/out")" -eq 1 ] && [ ! -e "$T/root/dl/lazpy-host" ]; then
  pass "--host with a TBD pin: one clear line, nothing fetched"; else fail "host tbd"; cat "$T/out"; fi

# 10: a wrong-sha zip dies, deletes the file and unpacks nothing; a missing zip does not fall back to the previous page,
# even when the previous page holds a host zip with the right bytes
cp "$HOSTREL/$HOST_MAC_ZIP" "$T/good.zip"; echo tampered > "$HOSTREL/$HOST_MAC_ZIP"
host_run "$T/tools/fetch.sh" Darwin "$HOSTREL" --host
if [ "$RC" -ne 0 ] && has "SHA256 MISMATCH" && [ ! -e "$T/root/build/azhost" ] && [ ! -e "$T/root/dl/lazpy-host/$HOST_MAC_ZIP" ]; then
  pass "--host with a wrong sha256: dies, deletes the zip, unpacks nothing"; else fail "host mismatch"; cat "$T/out"; fi
rm -f "$HOSTREL/$HOST_MAC_ZIP"; cp "$T/good.zip" "$PREV/$HOST_MAC_ZIP"
rm -rf "$T/root"; mkdir -p "$T/root"; RC=0
LAZ_ROOT="$T/root" LAZ_RELEASE_BASE="file://$HOSTREL" LAZ_RELEASE_BASE_PREV="file://$PREV" LAZ_FETCH_OS=Darwin \
  sh "$T/tools/fetch.sh" --host > "$T/out" 2>&1 || RC=$?
if [ "$RC" -ne 0 ] && has "download failed" && ! has "fell back" && [ ! -e "$T/root/build/azhost" ]; then
  pass "--host with the zip missing: dies, no fallback to the previous release (which holds a good zip)"; else fail "host missing"; cat "$T/out"; fi
rm -f "$PREV/$HOST_MAC_ZIP"

echo "fetch_fallback: $N cases passed, $BAD failed"
[ "$BAD" -eq 0 ]
