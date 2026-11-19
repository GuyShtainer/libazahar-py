#!/bin/sh
# build-core-win64.sh: turn Azahar's pinned unified source tarball into build-core/azahar_lazpy_libretro.dll, a
# mingw-w64 (posix threads) cross build on Debian or Ubuntu. CI runs it (.github/workflows/core-win64.yml); the macOS
# core is built by tools/build-core.sh, which this file never touches.
#   tools/build-core-win64.sh --configure-only   OpenSSL, tarball, unpack, patch, cmake configure (no compile)
#   tools/build-core-win64.sh --build            the above, then compile, copy, strip (long; use --detach)
#   tools/build-core-win64.sh --detach           run --build in its own session; pid -> build-core/build.pid,
#                                                exit code -> build-core/build.exit, log -> build-core/build.log
# Env: LAZ_ROOT, LAZ_CORE_PIN (default core/PIN-nokeys), LAZ_CORE_PATCHES (default core/patches), LAZ_CORE_LTO (OFF),
#      LAZ_CORE_JOBS (4), LAZ_OPENSSL_PREFIX (default /opt/lazpy/openssl-3.6.5-mingw64: the OpenSSL this script builds),
#      LAZ_IMAGE (the container image, recorded as image= in build.inputs; none outside CI). The pin file is read with
#      sed, never sourced. Needs: gcc/g++ mingw-w64 (posix), binutils-mingw-w64, cmake, make, perl, patch, curl, tar, xz,
#      python3, git, dpkg. Output and rules: core/README.md; the OpenSSL recipe: core/OPENSSL.md.
set -eu
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
ROOT="${LAZ_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
MODE="${1:-}"
case "$MODE" in --configure-only | --build | --detach) ;; *) echo "usage: $0 --configure-only | --build | --detach" >&2; exit 2 ;; esac
cd "$ROOT"
say() { echo "build-core-win64: $*"; }
die() { say "$*" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || die "refusing to run as root"
# sha256 of a file: shasum where present (macOS, perl), else sha256sum (Debian, Ubuntu, MSYS2)
sha_of() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi
}
sha() { sha_of "$1"; }

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
DROP="$(pin LAZ_CORE_DROP)"; SSL_VER="$(pin OPENSSL_VERSION)"
SSL_PIN="${LAZ_OPENSSL_PREFIX:-/opt/lazpy/openssl-$SSL_VER-mingw64}"
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
# the head of this checkout and the image are recorded in build.inputs; neither may be a guess
HEAD_SHA="$(git -C "$ROOT" rev-parse HEAD)" || die "git rev-parse HEAD failed (no head to record)"
IMAGE="${LAZ_IMAGE:-none}"
command -v dpkg-query >/dev/null 2>&1 || die "no dpkg-query (this script builds on Debian or Ubuntu)"
# Azahar's GenerateBuildInfo.cmake ignores the tarball's GIT-TAG when CI and GITHUB_ACTIONS are set and the push is not
# a tag, and names the build by its commit (219d743) instead of $TAG. Configure and build never see those two variables.
unset CI GITHUB_ACTIONS

DOWNLOADED=0
if [ ! -f "$TARBALL" ]; then
  say "fetch $URL"
  curl -fsSL --retry 2 -o "$TARBALL.part" "$URL" || die "download failed"
  mv "$TARBALL.part" "$TARBALL"
  DOWNLOADED=1
fi
SIZE="$(wc -c <"$TARBALL" | tr -d ' ')"
SHA="$(sha_of "$TARBALL")"
if [ "$SIZE" != "$WANT_SIZE" ] || [ "$SHA" != "$WANT_SHA" ]; then
  [ "$DOWNLOADED" -eq 0 ] || rm -f "$TARBALL"
  die "SHA256 MISMATCH for $FILE (size $SIZE want $WANT_SIZE, sha256 $SHA want $WANT_SHA); file kept, not refetched"
fi
if [ "$DOWNLOADED" -eq 1 ]; then say "fetch $FILE ok"; else say "have $FILE ($SIZE bytes, sha256 ok)"; fi

# OpenSSL: the A1 recipe (the toolkit's tools/pc/build-ossl-win.sh), static mingw-w64, only --prefix and --openssldir
# changed. The source is the release's openssl-$SSL_VER.tar.gz; its sha256 is the one core/OPENSSL.md states.
OSSL_SHA="$(grep -A1 '^- Source:' core/OPENSSL.md | grep -o '[0-9a-f]\{64\}' | head -1)"
[ -n "$OSSL_SHA" ] || die "core/OPENSSL.md states no source sha256"
OSSL_TAR="$ROOT/dl/openssl-src/openssl-$SSL_VER.tar.gz"
OSSL_URL="https://github.com/GuyShtainer/libazahar-py/releases/download/v1.0.0/openssl-$SSL_VER.tar.gz"
OPENSSLDIR_ARG="C:/Program Files/Common Files/SSL"
CONFIGURE_LINE="CC=gcc-posix ./Configure mingw64 no-shared no-tests no-ssl3 no-ssl3-method no-zlib --cross-compile-prefix=x86_64-w64-mingw32- --prefix=$SSL_PIN --openssldir=\"$OPENSSLDIR_ARG\" --libdir=lib"
# Configure runs on Linux and joins the prefix to a "C:/" path (not absolute there), and ENGINESDIR and MODULESDIR come
# from the Linux prefix: on Windows both would be C:\opt\..., which a plain user can create (CVE-2019-1552 class). So
# the three compiled-in folders are set on the make line, to OpenSSL's own Windows defaults (admin-only folders).
ENGINESDIR_ARG="C:/Program Files/OpenSSL/lib/engines-3"
MODULESDIR_ARG="C:/Program Files/OpenSSL/lib/ossl-modules"
MAKE_DIRS_LINE="make build_libs OPENSSLDIR=\"$OPENSSLDIR_ARG\" ENGINESDIR=\"$ENGINESDIR_ARG\" MODULESDIR=\"$MODULESDIR_ARG\""
mkdir -p "$(dirname "$OSSL_TAR")"
if [ ! -f "$OSSL_TAR" ]; then
  say "fetch $OSSL_URL"
  curl -fsSL --retry 2 -o "$OSSL_TAR.part" "$OSSL_URL" || die "OpenSSL download failed"
  mv "$OSSL_TAR.part" "$OSSL_TAR"
fi
[ "$(sha_of "$OSSL_TAR")" = "$OSSL_SHA" ] || die "SHA256 MISMATCH for $OSSL_TAR (core/OPENSSL.md says $OSSL_SHA); file kept"
OSSL_STAMP="$SSL_PIN/.lazpy-built-$(printf '%s\n%s\n%s\n' "$OSSL_SHA" "$CONFIGURE_LINE" "$MAKE_DIRS_LINE" | sha_of /dev/stdin)"
if [ ! -f "$OSSL_STAMP" ]; then
  say "build OpenSSL $SSL_VER (mingw64, static) into $SSL_PIN"
  OSSL_WORK="$ROOT/build-core/ossl"
  rm -rf "$OSSL_WORK" "$SSL_PIN"
  mkdir -p "$OSSL_WORK" "$SSL_PIN"
  tar -xzf "$OSSL_TAR" -C "$OSSL_WORK"
  (
    cd "$OSSL_WORK/openssl-$SSL_VER"
    # CC gets the cross prefix prepended by Configure, so it names the posix-threads gcc without it
    CC=gcc-posix ./Configure mingw64 no-shared no-tests no-ssl3 no-ssl3-method no-zlib \
      --cross-compile-prefix=x86_64-w64-mingw32- --prefix="$SSL_PIN" --openssldir="$OPENSSLDIR_ARG" --libdir=lib
    make -j"${LAZ_CORE_JOBS:-4}" build_libs OPENSSLDIR="$OPENSSLDIR_ARG" ENGINESDIR="$ENGINESDIR_ARG" MODULESDIR="$MODULESDIR_ARG"
    make install_dev
  ) >build-core/openssl-build.log 2>&1 || { tail -n 30 build-core/openssl-build.log; die "the OpenSSL build failed"; }
  rm -rf "$OSSL_WORK"
  : >"$OSSL_STAMP"
else
  say "OpenSSL up to date (stamp ok)"
fi
SSL_ROOT="$(cd -P "$SSL_PIN" 2>/dev/null && pwd)" || die "no OpenSSL at $SSL_PIN"
for A in lib/libssl.a lib/libcrypto.a include/openssl/opensslv.h; do [ -f "$SSL_ROOT/$A" ] || die "no $SSL_ROOT/$A"; done
SSL_GOT="$(sed -n 's/^# *define OPENSSL_VERSION_STR "\(.*\)"$/\1/p' "$SSL_ROOT/include/openssl/opensslv.h")"
[ "$SSL_GOT" = "$SSL_VER" ] || die "OpenSSL at $SSL_ROOT is '$SSL_GOT', core/PIN pins $SSL_VER"
strings -a "$SSL_ROOT/lib/libcrypto.a" | grep -q "OpenSSL $SSL_VER " || die "libcrypto.a at $SSL_ROOT is not OpenSSL $SSL_VER"
say "OpenSSL $SSL_VER static at $SSL_ROOT"

STAMP="$BUILD_SRC/.ready-$SHA-$({ cat "$PATCHES"/*.patch; echo "drop=$DROP"; } | sha_of /dev/stdin)"
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

# stale objects of the bundled LibreSSL from earlier builds (their .obj.d files name it)
rm -rf build-core/build/externals/libressl
# win64: mingw-w64 (posix threads). The toolchain file names the compilers; the .def is made from the patched tree.
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
set -- cmake -S "$TREE" -B build-core/build -DENABLE_LIBRETRO=ON \
  -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE="$ROOT/tools/toolchain-win64.cmake" -DLIBTYPE=STATIC \
  -DCLANG_FORMAT=/bin/true "-DCMAKE_SHARED_LINKER_FLAGS=$ROOT/build-core/libretro.win.def -Wl,-Map=$ROOT/build-core/core.map" \
  "-DCMAKE_CXX_STANDARD_LIBRARIES=-lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -lws2_32 -lcrypt32 -lbcrypt" \
  -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCITRA_WARNINGS_AS_ERRORS=OFF -DENABLE_LTO="${LAZ_CORE_LTO:-OFF}" \
  -DENABLE_BUILTIN_KEYBLOB=OFF \
  -DUSE_SYSTEM_OPENSSL=ON -DOPENSSL_USE_STATIC_LIBS=TRUE -DOPENSSL_ROOT_DIR="$SSL_ROOT" \
  -DOPENSSL_INCLUDE_DIR="$SSL_ROOT/include" -DOPENSSL_SSL_LIBRARY="$SSL_ROOT/lib/libssl.a" \
  -DOPENSSL_CRYPTO_LIBRARY="$SSL_ROOT/lib/libcrypto.a" \
  -DCMAKE_C_FLAGS="-ffile-prefix-map=$PWD/=" -DCMAKE_CXX_FLAGS="-ffile-prefix-map=$PWD/=$WIN_CXXDEFS"
if ! "$@" >build-core/configure.log 2>&1; then
  tail -n 30 build-core/configure.log
  die "configure failed"
fi
CACHE=build-core/build/CMakeCache.txt
grep -q '^ENABLE_BUILTIN_KEYBLOB:BOOL=OFF$' "$CACHE" \
  || die "the built-in console key blob is not OFF (we never ship console keys)"
grep -q 'SSE4.2 enabled' build-core/configure.log || die "configure: no 'SSE4.2 enabled' line (CMAKE_SYSTEM_PROCESSOR?)"
grep -q 'Enabling SSE2 for xxHash' build-core/configure.log || die "configure: no 'Enabling SSE2 for xxHash' line"
grep -q '^USE_SYSTEM_OPENSSL:BOOL=ON$' "$CACHE" || die "configure did not take USE_SYSTEM_OPENSSL"
for L in SSL:libssl CRYPTO:libcrypto; do
  grep -Eq "^OPENSSL_${L%%:*}_LIBRARY:[A-Z]*=$SSL_ROOT/lib/${L#*:}\.a\$" "$CACHE" \
    || die "configure did not pick $SSL_ROOT/lib/${L#*:}.a"
done
grep '^FIND_PACKAGE_MESSAGE_DETAILS_OpenSSL:INTERNAL=' "$CACHE" | grep -qF "v$SSL_VER" \
  || die "configure did not find OpenSSL $SSL_VER"
say "configure done: build-core/build"
[ "$MODE" = --build ] || exit 0

# build.inputs: what this build was made from (gate_f2 and the release check compare it)
CLEAN=no
[ -z "$(git -C "$ROOT" status --porcelain -- core tools/build-core-win64.sh tools/toolchain-win64.cmake 2>/dev/null)" ] && CLEAN=yes
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
  echo "openssl_src_sha256=$OSSL_SHA"
  echo "openssl_configure=$CONFIGURE_LINE"
  echo "openssl_make_dirs=$MAKE_DIRS_LINE"
  echo "target=win64 def=$(sha build-core/libretro.win.def)"
  echo "head=$HEAD_SHA"
  echo "image=$IMAGE"
  echo "clean=$CLEAN"
  printf 'cmake='; printf ' %s' "$@" | sed "s|$ROOT|<repo>|g; s|^ ||"; echo
} >build-core/build.inputs.tmp
mv -f build-core/build.inputs.tmp build-core/build.inputs

cmake --build build-core/build --target citra_libretro --config Release -j "${LAZ_CORE_JOBS:-4}"
# the host accepts only $TAG-lazpy.$REV: the generated build name must be the pinned tag
grep -qxF "#define BUILD_FULLNAME \"$TAG\"" build-core/build/src/common/scm_rev.cpp \
  || die "the build is not named $TAG (scm_rev.cpp: $(grep -h 'define BUILD_FULLNAME' build-core/build/src/common/scm_rev.cpp))"
for D in $DROP; do
  B="$(basename "$D" | sed 's/\./\\./g')"
  if find build-core/build \( -name '*.o.d' -o -name '*.obj.d' \) -exec grep -l "$B" {} + 2>/dev/null | grep -q .; then
    die "an object still reads $(basename "$D") (on the drop list)"
  fi
done
LINKDIR=build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir
# mingw puts the libraries into linkLibs.rsp, not link.txt
cat "$LINKDIR/link.txt" "$LINKDIR/linkLibs.rsp" >build-core/link.all
LINK=build-core/link.all
grep -qF -e -lole32 "$LINK" || die "the link line lacks -lole32"
for A in libssl.a libcrypto.a; do grep -qF "$SSL_ROOT/lib/$A" "$LINK" || die "the link line lacks $SSL_ROOT/lib/$A"; done
if grep -qi libressl "$LINK"; then die "the link line still names libressl"; fi
OUTLIB=build-core/build/bin/Release/azahar_libretro.dll
if strings -a "$OUTLIB" | grep -qi 'libressl'; then die "LibreSSL is still in the core"; fi
if strings -a "$OUTLIB" | grep -q "OpenSSL $SSL_VER"; then :; else say "note: no 'OpenSSL $SSL_VER' string in the core"; fi
DLL=build-core/azahar_lazpy_libretro.dll
cp "$OUTLIB" "$DLL.tmp"
x86_64-w64-mingw32-strip --strip-unneeded "$DLL.tmp"
if x86_64-w64-mingw32-objdump -p "$DLL.tmp" | grep 'DLL Name' | grep -Eq 'libssl|libcrypto|libtls'; then
  rm -f "$DLL.tmp"; die "the core links an SSL DLL (static OpenSSL only; stop and report)"
fi
mv -f "$DLL.tmp" "$DLL"
say "built $DLL"

# What the DLL itself says, recorded into build.inputs after the build (core/OPENSSL.md and USING quote these).
dll_ossl() { strings -a "$DLL" | sed -n "s/^$1: //p" | head -n 1; }
{
  for K in OPENSSLDIR ENGINESDIR MODULESDIR; do
    V="$(dll_ossl $K)"
    echo "openssl_$(echo "$K" | tr 'A-Z' 'a-z')=${V:-absent}"
    case "$V" in
      '"C:/Program Files/'*) ;;    # the DLL quotes it: OPENSSLDIR: "C:/..."
      *) die "the DLL's $K is '${V:-absent}', not under C:/Program Files/ (the prefix fix did not take)" ;;
    esac
  done
  for P in gcc-mingw-w64-base gcc-mingw-w64-x86-64-posix g++-mingw-w64-x86-64-posix gcc-mingw-w64-x86-64-posix-runtime \
    binutils-mingw-w64-x86-64 mingw-w64-x86-64-dev; do
    echo "mingw_pkg $P=$(dpkg-query -W -f='${Version}' "$P")"
  done
} >>build-core/build.inputs

# The GCC idents in the DLL, each mapped to its package by evidence (D13): an ident is searched with strings(1) in the
# archives of linkLibs.rsp and in the compiler's implicit ones, and the archive's path goes through dpkg -S.
GCCBIN=x86_64-w64-mingw32-gcc-posix
{
  for W in $(cat "$LINK"); do
    case "$W" in
      /*.a) [ -f "$W" ] && echo "$W" ;;
      -l*) printf '%s\n' "$($GCCBIN -print-file-name="lib${W#-l}.a")" ;;
    esac
  done
  for N in libstdc++.a libgcc.a libgcc_eh.a libmingw32.a libmingwex.a libmoldname.a libwinpthread.a libpthread.a libmsvcrt.a; do
    printf '%s\n' "$($GCCBIN -print-file-name="$N")"
  done
} | grep '^/usr/' | sort -u >build-core/ident-archives.txt
strings -a "$DLL" | grep '^GCC: ' | sort -u >build-core/gcc-idents.txt || true
[ -s build-core/gcc-idents.txt ] || say "note: no GCC ident string in the core"
while IFS= read -r IDENT; do
  MAP=""
  while IFS= read -r ARC; do
    if strings -a "$ARC" | grep -qxF "$IDENT"; then
      PKG="$(dpkg -S "$ARC" 2>/dev/null | head -n 1 | cut -d: -f1)"
      [ -n "$PKG" ] || PKG="$(dpkg -S "$(readlink -f "$ARC")" 2>/dev/null | head -n 1 | cut -d: -f1)"
      [ -n "$PKG" ] || die "no package owns $ARC (dpkg -S)"
      MAP="$MAP${MAP:+;}$PKG($(basename "$ARC"))"
    fi
  done <build-core/ident-archives.txt
  [ -n "$MAP" ] || die "the GCC ident '$IDENT' is in no archive of the link line (map it by hand and report)"
  echo "gcc_ident $IDENT=$MAP" >>build-core/build.inputs
done <build-core/gcc-idents.txt

# Which runtime archives the final link pulled in (the link map lists every archive member and its archive). linkLibs.rsp
# misses what g++ adds itself, so the map is the evidence: libquadmath, libssp or libatomic in it changes the notices.
[ -s build-core/core.map ] || die "the link map build-core/core.map is missing"
RTLIBS="$(sed -n '/^Archive member included/,/^Discarded input sections/p' build-core/core.map \
  | grep -o '/[^ (]*/lib\(stdc++\|gcc\|gcc_eh\|winpthread\|pthread\|quadmath\|ssp\|atomic\|mingw32\|mingwex\)[^ (/]*\.a' \
  | sed 's|.*/lib||; s|\.a$||' | sort -u | tr '\n' ' ' | sed 's/ $//')"
echo "runtime_libs=${RTLIBS:-none}" >>build-core/build.inputs
say "runtime-libs: ${RTLIBS:-none}"
case " $RTLIBS " in *" quadmath "* | *" ssp "* | *" atomic "*) say "note: libquadmath, libssp or libatomic is linked: the notices need its licence (LGPL-2.1 for libquadmath) and its source" ;; esac
say "build.inputs complete"
