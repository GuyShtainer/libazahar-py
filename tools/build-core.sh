#!/bin/sh
# build-core.sh: turn Azahar's pinned unified source tarball into build-core/azahar_lazpy_libretro.dylib.
#   tools/build-core.sh --configure-only   fetch/verify tarball, unpack, patch, cmake configure (no compile)
#   tools/build-core.sh --build            the above, then compile, copy, strip, codesign (long; use --detach)
#   tools/build-core.sh --detach           run --build in its own session; pid -> build-core/build.pid,
#                                          exit code -> build-core/build.exit, log -> build-core/build.log
# Env: LAZPY_ROOT, LAZ_CORE_PIN (default core/PIN), LAZ_CORE_PATCHES (default core/patches), LAZ_CORE_LTO (ON),
#      LAZ_CORE_JOBS (4). The pin file is read with sed, never sourced. Output and rules: core/README.md.
set -eu
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
ROOT="${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
MODE="${1:-}"
case "$MODE" in --configure-only | --build | --detach) ;; *) echo "usage: $0 --configure-only | --build | --detach" >&2; exit 2 ;; esac
cd "$ROOT"
export MACOSX_DEPLOYMENT_TARGET=11.0
say() { echo "build-core: $*"; }
die() { say "$*" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || die "refusing to run as root"

if [ "$MODE" = --detach ]; then
  mkdir -p build-core
  if [ -f build-core/build.pid ] && kill -0 "$(cat build-core/build.pid)" 2>/dev/null; then
    die "a build is already running (pid $(cat build-core/build.pid))"
  fi
  rm -f build-core/build.exit
  nohup nice -n 10 python3 -I -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' \
    "$SELF" --build </dev/null >build-core/build.log 2>&1 &
  echo "$!" >build-core/build.pid
  say "started pid $!, log build-core/build.log, exit code -> build-core/build.exit"
  exit 0
fi

PIN="${LAZ_CORE_PIN:-core/PIN}"
PATCHES="${LAZ_CORE_PATCHES:-core/patches}"
case "$PATCHES" in /*) ;; *) PATCHES="$ROOT/$PATCHES" ;; esac
pin() { sed -n "s/^$1=//p" "$PIN"; }
TAG="$(pin AZAHAR_TAG)"; COMMIT="$(pin AZAHAR_COMMIT)"; URL="$(pin SRC_URL)"; WANT_SHA="$(pin SRC_SHA256)"
WANT_SIZE="$(pin SRC_SIZE)"; FILE="$(pin SRC_FILE)"; TOP="$(pin SRC_TOP)"
for V in "$TAG" "$COMMIT" "$URL" "$WANT_SHA" "$WANT_SIZE" "$FILE" "$TOP"; do
  [ -n "$V" ] || die "pin $PIN is missing a value"
done
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

STAMP="$BUILD_SRC/.ready-$SHA-$(cat "$PATCHES"/*.patch | shasum -a 256 | cut -d' ' -f1)"
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

if ! cmake -S "$TREE" -B build-core/build -DENABLE_LIBRETRO=ON -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCITRA_WARNINGS_AS_ERRORS=OFF -DENABLE_LTO="${LAZ_CORE_LTO:-ON}" >build-core/configure.log 2>&1; then
  tail -n 30 build-core/configure.log
  die "configure failed"
fi
say "configure done: build-core/build"
[ "$MODE" = --build ] || exit 0

cmake --build build-core/build --target citra_libretro --config Release -j "${LAZ_CORE_JOBS:-4}"
DYLIB=build-core/azahar_lazpy_libretro.dylib
cp build-core/build/bin/Release/azahar_libretro.dylib "$DYLIB"
strip -x "$DYLIB"
codesign --force -s - "$DYLIB"
codesign -v "$DYLIB"
say "built $DYLIB"
