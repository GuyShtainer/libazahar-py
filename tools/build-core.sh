#!/bin/sh
# build-core.sh: turn Azahar's pinned unified source tarball into build-core/azahar_lazpy_libretro.dylib.
#   tools/build-core.sh --configure-only   fetch/verify tarball, unpack, patch, cmake configure (no compile)
#   tools/build-core.sh --build            the above, then compile, copy, strip, codesign (long; use --detach)
#   tools/build-core.sh --detach           run --build in its own session; pid -> build-core/build.pid,
#                                          exit code -> build-core/build.exit, log -> build-core/build.log
# Env: LAZ_CORE_TARGET (mac, the default, or win64: a mingw-w64 cross build to .dll, run on Linux/WSL), LAZ_ROOT (old name LAZPY_ROOT), LAZ_CORE_PIN (default core/PIN-nokeys; core/PIN builds from Azahar's own tarball), LAZ_CORE_PATCHES (default core/patches), LAZ_CORE_LTO (ON),
#      LAZ_CORE_JOBS (4), LAZ_OPENSSL_PREFIX (default: the pin's OPENSSL_PREFIX; a static OpenSSL of the pinned version, resolved to its real path). The pin file is read with sed, never sourced. Output and rules: core/README.md.
set -eu
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
ROOT="${LAZ_ROOT:-${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"   # LAZPY_ROOT: the old name, kept for 1.x
MODE="${1:-}"
case "$MODE" in --configure-only | --build | --detach) ;; *) echo "usage: $0 --configure-only | --build | --detach" >&2; exit 2 ;; esac
cd "$ROOT"
export MACOSX_DEPLOYMENT_TARGET=15.0
case "${LAZ_CORE_TARGET:-mac}" in
  mac) TARGET=mac; CORE_EXT=dylib ;;
  win64) TARGET=win64; CORE_EXT=dll ;;
  *) echo "build-core: LAZ_CORE_TARGET must be mac or win64 (got '$LAZ_CORE_TARGET')" >&2; exit 2 ;;
esac
say() { echo "build-core: $*"; }
die() { say "$*" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || die "refusing to run as root"

if [ "$MODE" = --detach ]; then
  mkdir -p build-core
  if [ -f build-core/build.pid ] && kill -0 "$(cat build-core/build.pid)" 2>/dev/null; then
    die "a build is already running (pid $(cat build-core/build.pid))"
  fi
  rm -f build-core/build.exit build-core/build.inputs
  nohup nice -n 10 python3 -I -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' \
    "$SELF" --build </dev/null >build-core/build.log 2>&1 &
  echo "$!" >build-core/build.pid
  say "started pid $!, log build-core/build.log, exit code -> build-core/build.exit"
  exit 0
fi

PIN="${LAZ_CORE_PIN:-core/PIN-nokeys}"
PATCHES="${LAZ_CORE_PATCHES:-core/patches}"
case "$PATCHES" in /*) ;; *) PATCHES="$ROOT/$PATCHES" ;; esac
pin() { sed -n "s/^$1=//p" "$PIN"; }
TAG="$(pin AZAHAR_TAG)"; COMMIT="$(pin AZAHAR_COMMIT)"; URL="$(pin SRC_URL)"; WANT_SHA="$(pin SRC_SHA256)"
WANT_SIZE="$(pin SRC_SIZE)"; FILE="$(pin SRC_FILE)"; TOP="$(pin SRC_TOP)"
DROP="$(pin LAZ_CORE_DROP)"; SSL_VER="$(pin OPENSSL_VERSION)"; SSL_PIN="${LAZ_OPENSSL_PREFIX:-$(pin OPENSSL_PREFIX)}"
REV="$(pin LAZPY_REV)"
for V in "$TAG" "$COMMIT" "$URL" "$WANT_SHA" "$WANT_SIZE" "$FILE" "$TOP" "$DROP" "$SSL_VER" "$SSL_PIN" "$REV"; do
  [ -n "$V" ] || die "pin $PIN is missing a value"
done
# the version suffix patch and the pin's LAZPY_REV must agree (the release zip is named from the pin)
grep -qF "\"-lazpy.$REV\";" "$PATCHES/0005-lazpy-version.patch" \
  || die "patch 0005's version suffix is not -lazpy.$REV (the pin's LAZPY_REV)"
case "$FILE" in /*) TARBALL="$FILE" ;; *) TARBALL="$ROOT/$FILE" ;; esac
BUILD_SRC="${ROOT:?}/dl/azahar-src/build-src"
TREE="$BUILD_SRC/$TOP"
say "pin $TAG commit $COMMIT"
mkdir -p build-core "$(dirname "$TARBALL")"
if [ "$MODE" = --build ]; then
  # exit code of every exit we can catch (a SIGKILL or OOM kill leaves no file)
  trap 'echo $? >"$ROOT/build-core/build.exit"' EXIT
  trap 'exit 143' INT TERM HUP
fi

DOWNLOADED=0
if [ ! -f "$TARBALL" ]; then
  say "fetch $URL"
  curl -fsSL --retry 2 -o "$TARBALL.part" "$URL" || die "download failed"
  mv "$TARBALL.part" "$TARBALL"
  DOWNLOADED=1
fi
SIZE="$(wc -c <"$TARBALL" | tr -d ' ')"
SHA="$(shasum -a 256 "$TARBALL" | cut -d' ' -f1)"
if [ "$SIZE" != "$WANT_SIZE" ] || [ "$SHA" != "$WANT_SHA" ]; then
  [ "$DOWNLOADED" -eq 0 ] || rm -f "$TARBALL"
  die "SHA256 MISMATCH for $FILE (size $SIZE want $WANT_SIZE, sha256 $SHA want $WANT_SHA); file kept, not refetched"
fi
if [ "$DOWNLOADED" -eq 1 ]; then say "fetch $FILE ok"; else say "have $FILE ($SIZE bytes, sha256 ok)"; fi

# OpenSSL: a static OpenSSL of exactly the pinned version replaces Azahar's bundled LibreSSL (GPLv3-compatible).
SSL_ROOT="$(cd -P "$SSL_PIN" 2>/dev/null && pwd)" || die "no OpenSSL at $SSL_PIN (brew install openssl@3)"
for A in lib/libssl.a lib/libcrypto.a include/openssl/opensslv.h; do [ -f "$SSL_ROOT/$A" ] || die "no $SSL_ROOT/$A"; done
SSL_GOT="$(sed -n 's/^# *define OPENSSL_VERSION_STR "\(.*\)"$/\1/p' "$SSL_ROOT/include/openssl/opensslv.h")"
[ "$SSL_GOT" = "$SSL_VER" ] || die "OpenSSL at $SSL_ROOT is '$SSL_GOT', core/PIN pins $SSL_VER"
strings -a "$SSL_ROOT/lib/libcrypto.a" | grep -q "OpenSSL $SSL_VER " || die "libcrypto.a at $SSL_ROOT is not OpenSSL $SSL_VER"
say "OpenSSL $SSL_VER static at $SSL_ROOT"

STAMP="$BUILD_SRC/.ready-$SHA-$({ cat "$PATCHES"/*.patch; echo "drop=$DROP"; } | shasum -a 256 | cut -d' ' -f1)"
if [ ! -f "$STAMP" ]; then
  rm -rf "$BUILD_SRC"
  OUT="$(python3 -I tools/untar_checked.py "$TARBALL" "$BUILD_SRC")" || {
    printf '%s\n' "$OUT" >&2
    rm -rf "$BUILD_SRC"
    die "unpack REFUSED or failed (tree removed)"
  }
  case "$OUT" in *members=*) ;; *) die "unpack printed no member count" ;; esac
  N="${OUT##*members=}"
  say "unpacked $N members into dl/azahar-src/build-src/$TOP (path check ok)"
  # the drop list: files that must never be built or shipped (console keys, Nintendo's ClCertA)
  set -f
  for D in $DROP; do
    case "$D" in /* | *..* | "") rm -rf "$BUILD_SRC"; die "unsafe drop-list entry '$D'" ;; esac
    [ -e "$TREE/$D" ] || { rm -rf "$BUILD_SRC"; die "drop-list entry $D is not in the tree"; }
    rm -rf -- "${TREE:?}/${D:?}"
    say "dropped $D"
  done
  set +f
  COUNT=0
  for P in "$PATCHES"/*.patch; do
    if ! (cd "$TREE" && patch -p1 --forward --batch --fuzz 0 <"$P") >build-core/patch.log 2>&1; then
      tail -n 20 build-core/patch.log
      rm -rf "$BUILD_SRC"
      die "patch $(basename "$P") REJECTED (tree removed)"
    fi
    say "patch $(basename "$P") ok"
    COUNT=$((COUNT + 1))
  done
  say "applied $COUNT patches, 0 rejects"
  : >"$STAMP"
else
  say "tree up to date (stamp ok)"
fi

# stale objects of the bundled LibreSSL from earlier builds (their .o.d files name it)
rm -rf build-core/build/externals/libressl
set -- cmake -S "$TREE" -B build-core/build -DENABLE_LIBRETRO=ON
if [ "$TARGET" = mac ]; then
  set -- "$@" -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=15.0
else
  # win64: mingw-w64 (posix threads) on Linux. The toolchain file names the compilers; the .def is made from the patched tree.
  mkdir -p build-core/toolbin
  printf '#!/bin/sh\nexec x86_64-w64-mingw32-gcc-ar-posix "$@"\n' >build-core/toolbin/x86_64-w64-mingw32.static-gcc-ar
  chmod +x build-core/toolbin/x86_64-w64-mingw32.static-gcc-ar
  export PATH="$ROOT/build-core/toolbin:$PATH"
  { echo EXPORTS; grep -v '^#' "$TREE/src/citra_libretro/libretro.osx.def" | sed 's/^_//'; } >build-core/libretro.win.def
  [ "$(grep -c lazpy_ build-core/libretro.win.def)" -eq 4 ] || die "libretro.win.def does not hold the 4 lazpy_ exports"
  # mingw-w64 13: fstat() takes `struct stat*`, but common/file_util.cpp:551-552 (libretro branch) passes a `_stat64` (MSVC builds
  # get `#define fstat _fstat64` there). A force-included C++ overload fixes that one call and leaves every other file's fstat
  # alone (a global -Dfstat broke fmt and boost). C++ only; no source patch.
  printf '#include <sys/stat.h>\nstatic inline int fstat(int fd, struct _stat64 *s) { return _fstat64(fd, s); }\n' >build-core/win64-fstat.h
  WIN_CXXDEFS=" -include $ROOT/build-core/win64-fstat.h"
  set -- "$@" -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE="$ROOT/tools/toolchain-win64.cmake" -DLIBTYPE=STATIC \
    -DCLANG_FORMAT=/bin/true "-DCMAKE_SHARED_LINKER_FLAGS=$ROOT/build-core/libretro.win.def" \
    "-DCMAKE_CXX_STANDARD_LIBRARIES=-lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -lws2_32 -lcrypt32 -lbcrypt"
fi
set -- "$@" \
  -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCITRA_WARNINGS_AS_ERRORS=OFF -DENABLE_LTO="${LAZ_CORE_LTO:-$([ "$TARGET" = mac ] && echo ON || echo OFF)}" \
  -DENABLE_BUILTIN_KEYBLOB=OFF \
  -DUSE_SYSTEM_OPENSSL=ON -DOPENSSL_USE_STATIC_LIBS=TRUE -DOPENSSL_ROOT_DIR="$SSL_ROOT" \
  -DOPENSSL_INCLUDE_DIR="$SSL_ROOT/include" -DOPENSSL_SSL_LIBRARY="$SSL_ROOT/lib/libssl.a" \
  -DOPENSSL_CRYPTO_LIBRARY="$SSL_ROOT/lib/libcrypto.a" \
  -DCMAKE_C_FLAGS="-ffile-prefix-map=$PWD/=" -DCMAKE_CXX_FLAGS="-ffile-prefix-map=$PWD/=${WIN_CXXDEFS:-}"
if ! "$@" >build-core/configure.log 2>&1; then
  tail -n 30 build-core/configure.log
  die "configure failed"
fi
grep -q '^ENABLE_BUILTIN_KEYBLOB:BOOL=OFF$' build-core/build/CMakeCache.txt \
  || die "the built-in console key blob is not OFF (we never ship console keys)"
CACHE=build-core/build/CMakeCache.txt
if [ "$TARGET" = mac ]; then
  grep -Eq '^CMAKE_OSX_DEPLOYMENT_TARGET:[A-Z]*=15.0$' "$CACHE" \
    || die "configure did not take macOS 15.0 as the minimum (an older build tree's cache?)"
else
  grep -q 'SSE4.2 enabled' build-core/configure.log || die "configure: no 'SSE4.2 enabled' line (CMAKE_SYSTEM_PROCESSOR?)"
  grep -q 'Enabling SSE2 for xxHash' build-core/configure.log || die "configure: no 'Enabling SSE2 for xxHash' line"
fi
grep -q '^USE_SYSTEM_OPENSSL:BOOL=ON$' "$CACHE" || die "configure did not take USE_SYSTEM_OPENSSL"
for L in SSL:libssl CRYPTO:libcrypto; do
  grep -Eq "^OPENSSL_${L%%:*}_LIBRARY:[A-Z]*=$SSL_ROOT/lib/${L#*:}\.a\$" "$CACHE" \
    || die "configure did not pick $SSL_ROOT/lib/${L#*:}.a"
done
grep '^FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL:INTERNAL=' "$CACHE" | grep -qF "v$SSL_VER" \
  || die "configure did not find OpenSSL $SSL_VER"
say "configure done: build-core/build"
[ "$MODE" = --build ] || exit 0

# build.inputs: what this build was made from (Phase 3 F2 and Phase 4's release check compare it)
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
CLEAN=no
[ -z "$(git -C "$ROOT" status --porcelain -- core tools/build-core.sh 2>/dev/null)" ] && CLEAN=yes
{
  echo "tarball=$SHA"
  echo "pin=$(sha "$PIN")"
  echo "script=$(sha "$SELF")"
  for P in "$PATCHES"/*.patch; do echo "patch $(basename "$P")=$(sha "$P")"; done
  echo "drop=$DROP"
  echo "openssl_version=$SSL_VER"
  echo "openssl_prefix=$SSL_ROOT"
  echo "openssl_libssl_sha256=$(sha "$SSL_ROOT/lib/libssl.a")"
  echo "openssl_libcrypto_sha256=$(sha "$SSL_ROOT/lib/libcrypto.a")"
  [ "$TARGET" = mac ] || echo "target=win64 def=$(sha build-core/libretro.win.def)"
  echo "head=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo none)"
  echo "clean=$CLEAN"
  printf 'cmake='; printf ' %s' "$@" | sed "s|$ROOT|<repo>|g; s|^ ||"; echo
} >build-core/build.inputs.tmp
mv -f build-core/build.inputs.tmp build-core/build.inputs

cmake --build build-core/build --target citra_libretro --config Release -j "${LAZ_CORE_JOBS:-4}"
for D in $DROP; do
  B="$(basename "$D" | sed 's/\./\\./g')"
  if find build-core/build -name '*.o.d' -exec grep -l "$B" {} + 2>/dev/null | grep -q .; then
    die "an object still reads $(basename "$D") (on the drop list)"
  fi
done
LINK=build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt
if [ "$TARGET" = win64 ]; then   # mingw puts the libraries into linkLibs.rsp, not link.txt
  cat "$LINK" "${LINK%link.txt}linkLibs.rsp" >build-core/link.all
  LINK=build-core/link.all
  grep -qF -e -lole32 "$LINK" || die "the link line lacks -lole32"
fi
for A in libssl.a libcrypto.a; do grep -qF "$SSL_ROOT/lib/$A" "$LINK" || die "the link line lacks $SSL_ROOT/lib/$A"; done
if grep -qi libressl "$LINK"; then die "the link line still names libressl"; fi
OUTLIB=build-core/build/bin/Release/azahar_libretro.$CORE_EXT
if strings -a "$OUTLIB" | grep -qi 'libressl'; then die "LibreSSL is still in the core"; fi
if strings -a "$OUTLIB" | grep -q "OpenSSL $SSL_VER"; then :; else say "note: no 'OpenSSL $SSL_VER' string in the core"; fi
DYLIB=build-core/azahar_lazpy_libretro.$CORE_EXT
cp "$OUTLIB" "$DYLIB.tmp"
if [ "$TARGET" = mac ]; then
  strip -x "$DYLIB.tmp"
  codesign --force -s - "$DYLIB.tmp"
  codesign -v "$DYLIB.tmp"
  LINKED="$(otool -L "$DYLIB.tmp")"
else
  x86_64-w64-mingw32-strip --strip-unneeded "$DYLIB.tmp"
  LINKED="$(x86_64-w64-mingw32-objdump -p "$DYLIB.tmp" | grep 'DLL Name')"
fi
if printf '%s\n' "$LINKED" | grep -Eq 'libssl|libcrypto|libtls'; then
  rm -f "$DYLIB.tmp"; die "the core links an SSL dylib (static OpenSSL only; stop and report)"
fi
mv -f "$DYLIB.tmp" "$DYLIB"
say "built $DYLIB"
