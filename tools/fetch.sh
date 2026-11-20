#!/bin/sh
# fetch.sh: download MoltenVK, the libretro/Vulkan headers, our core and the test app, pinned and sha256-checked.
#
#   tools/fetch.sh [PART...] [--force]
#     --moltenvk     MoltenVK (dl/moltenvk/)
#     --headers      the libretro and Vulkan headers (vendor/)
#     --lazpy-core   our core from the release: the zip, verified; the core, NOTICES.md and SOURCE.md unpacked into
#                    dl/lazpy-core/ (the core there is the default core path; LAZ_CORE overrides it)
#     --testapp      the test app from the release, into dl/testapp/ and build/testapp.3dsx
#     --host         the prebuilt host for this system from the release (libazhost + azhost, sha256-pinned): the zip is
#                    kept in dl/lazpy-host/ and the two binaries are unpacked into build/ (build/libazhost.dll and
#                    build/azhost.exe on Windows, build/libazhost.dylib and build/azhost on macOS), the paths the
#                    Python layer reads. Never part of the default set; it replaces a host built by `make`.
#     --force        delete and refetch what the chosen parts fetch
#   No part flag means --moltenvk --headers on macOS, and --headers --lazpy-core --testapp on Windows (MoltenVK is
#   macOS only and is skipped there). A second run downloads nothing.
#   LAZ_ROOT=<dir>          use <dir> instead of the repo root (for tests on a temp copy; LAZPY_ROOT is the old name)
#   LAZ_RELEASE_BASE=<url>  use <url> instead of the release page (for tests, file://)
#   LAZ_RELEASE_BASE_PREV=<url>  the page of the previous release, for the fallback below (for tests, file://); when
#                           LAZ_RELEASE_BASE is set and this is not, there is no fallback
#   LAZ_FETCH_OS=<name>     use <name> instead of `uname -s` (Darwin: the macOS zip; MINGW64_NT, MSYS_NT or
#                           Windows: the Windows zip)
#
# The host zip, libazahar-py-host-<version>-windows-x64.zip or -macos-arm64.zip (<version> is REL_TAG without the v),
# exists in the release that built it and has no fallback to an older release.
#
# The fallback: the macOS core zip and the test app have the same bytes in the previous release. When one of them
# cannot be downloaded from the current release (any curl failure), it is fetched once from the previous release
# and checked against the same pinned sha256, and "fell back to <tag> for <asset>" goes to stderr. A sha256 mismatch
# never falls back. The Windows zip has no fallback: before its release is published, fetch says so.
#
# Downloads are untrusted data (docs/map/rules.md rule 2): each lives in its own folder under dl/, is hashed BEFORE
# it is unpacked, and nothing from a download is ever run here. dl/ and vendor/ are git-ignored. Needs only the macOS
# stock curl, shasum (or sha256sum), unzip, tar, cp.
set -eu

ROOT="${LAZ_ROOT:-${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"   # LAZPY_ROOT: the old name, kept for 1.x
DL="$ROOT/dl"
VENDOR="$ROOT/vendor"

# ---- pins (change a version only together with its sha256) ------------------------------------------------------
MVK_VER=1.4.2
MVK_URL="https://github.com/KhronosGroup/MoltenVK/releases/download/v$MVK_VER/MoltenVK-macos.tar"
MVK_SHA=f95765a6229cb7b915990a2890ce12ebe36a730b021545d3d52ae69ce4c4024e

# libretro.h and libretro_vulkan.h from RetroArch's libretro-common at one commit (MIT)
RA_COMMIT=807245ddcd0448b37331d36c9f25af35fbe70644
RA_BASE="https://raw.githubusercontent.com/libretro/RetroArch/$RA_COMMIT/libretro-common/include"
LIBRETRO_SHA=7a1962d8ac8c4eb6fdcc787f0714ebd62d4aa012741a51a71383bdf5a1073477
LIBRETRO_VK_SHA=8c17fe6647069e22779cc5126cef43f8f5f0c83debf2ca2726385b5c8f493f9d

# Vulkan-Headers tag; only include/ is used (vulkan/ and vk_video/ go to vendor/include/)
VKH_VER=1.4.368
VKH_URL="https://github.com/KhronosGroup/Vulkan-Headers/archive/refs/tags/v$VKH_VER.tar.gz"
VKH_SHA=5c5c6f64fcce28a24cc934143a048707af036a858e4ed11d7f71fe016006ecda
# our release: the tag, the base URL and the two assets' sha256 (filled at release time; TBD makes the flag die)
REL_TAG=v1.3.0
REL_TAG_PREV=v1.0.0
REL_BASE="${LAZ_RELEASE_BASE:-https://github.com/GuyShtainer/libazahar-py/releases/download/$REL_TAG}"
# the previous release's page: LAZ_RELEASE_BASE_PREV, else (only when LAZ_RELEASE_BASE is not set) the GitHub page
if [ -n "${LAZ_RELEASE_BASE_PREV:-}" ]; then REL_BASE_PREV=$LAZ_RELEASE_BASE_PREV
elif [ -z "${LAZ_RELEASE_BASE:-}" ]; then REL_BASE_PREV="https://github.com/GuyShtainer/libazahar-py/releases/download/$REL_TAG_PREV"
else REL_BASE_PREV=""; fi
LAZPY_CORE_ZIP=azahar_lazpy_libretro-2126.2-lazpy.2-macos-arm64.zip
LAZPY_CORE_SHA=ced9a36283ec72318b20f9686601335a2e57699ffb9278f31885697161bb609e
TESTAPP_SHA=ba10699831f2a1c88b56de119bd2f8caab465e051eb350954b7be1cd7b027ccd
# the Windows core zip (in the release only; no fallback)
LAZPY_CORE_ZIP_WIN=azahar_lazpy_libretro-2126.2-lazpy.2-windows-x64.zip
LAZPY_CORE_SHA_WIN=fe0bbfd1d6a7930e70309b0c97de162ec78b4e4fcc67e4e9c3eea04281ddf370
# the prebuilt host zips (filled at release time; TBD makes --host die). No fallback: each release carries its own.
LAZPY_HOST_SHA_WIN=TBD
LAZPY_HOST_SHA_MAC=TBD
# ------------------------------------------------------------------------------------------------------------------

FORCE=0; DO_MVK=0; DO_HEADERS=0; DO_CORE=0; DO_APP=0; DO_HOST=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --moltenvk) DO_MVK=1 ;;
    --headers) DO_HEADERS=1 ;;
    --lazpy-core) DO_CORE=1 ;;
    --testapp) DO_APP=1 ;;
    --host) DO_HOST=1 ;;
    *) echo "usage: $0 [--moltenvk] [--headers] [--lazpy-core] [--testapp] [--host] [--force]" >&2; exit 2 ;;
  esac
done

MISSING_HINT=""
die() { echo "fetch.sh: $*" >&2; exit 1; }

if command -v shasum >/dev/null 2>&1; then
  sha_of() { shasum -a 256 "$1" | cut -d' ' -f1; }
else
  sha_of() { sha256sum "$1" | cut -d' ' -f1; }
fi

case "${LAZ_FETCH_OS:-$(uname -s)}" in
  Darwin*) OS_KIND=mac ;;
  MINGW*|MSYS*|CYGWIN*|Windows*) OS_KIND=win ;;
  *) OS_KIND=other ;;
esac
if [ $((DO_MVK + DO_HEADERS + DO_CORE + DO_APP + DO_HOST)) -eq 0 ]; then
  # no part flag: macOS gets MoltenVK and the headers; Windows gets the headers, our core and the test app
  if [ "$OS_KIND" = win ]; then DO_HEADERS=1; DO_CORE=1; DO_APP=1; else DO_MVK=1; DO_HEADERS=1; fi
fi
if [ "$OS_KIND" = win ] && [ "$DO_MVK" -eq 1 ]; then echo "skip   MoltenVK (macOS only)"; DO_MVK=0; fi

# ok FILE SHA: true when FILE exists and has that sha256
ok() { [ -f "$1" ] && [ "$(sha_of "$1")" = "$2" ]; }

# get URL SHA FILE [FALLBACK_URL]: make FILE verified; download only if it is missing or wrong. A mismatch deletes the
# file and exits. When the download fails and FALLBACK_URL is not empty, that one is tried once, with the same sha256.
get() {
  _url=$1; _sha=$2; _file=$3; _fb=${4:-}; _fell=0
  if [ "$FORCE" -eq 0 ] && ok "$_file" "$_sha"; then
    echo "have   $_file (sha256 ok)"
    return 0
  fi
  mkdir -p "$(dirname "$_file")"
  rm -f "$_file"
  echo "fetch  $_url"
  if ! curl -fsSL --retry 2 -o "$_file" "$_url"; then
    rm -f "$_file"
    [ -n "$_fb" ] || die "download failed: $_url${MISSING_HINT:+ ($MISSING_HINT)}"
    echo "fetch  $_fb"
    curl -fsSL --retry 2 -o "$_file" "$_fb" || { rm -f "$_file"; die "download failed: $_fb"; }
    _fell=1
  fi
  _got=$(sha_of "$_file")
  if [ "$_got" != "$_sha" ]; then
    rm -f "$_file"
    die "SHA256 MISMATCH for $_url
  expected $_sha
  got      $_got
  the file was deleted; nothing was unpacked"
  fi
  [ "$_fell" -eq 0 ] || echo "fell back to $REL_TAG_PREV for $(basename "$_file")" >&2
  echo "ok     $_file (sha256 verified)"
}

# verify FILE SHA: re-check a file that is about to be unpacked or copied (guards a file edited since the download)
verify() {
  ok "$1" "$2" || { rm -f "$1"; die "SHA256 MISMATCH for $1 (deleted); run again to refetch"; }
}

# pin_set SHA FLAG: the pin must have been filled at release time
pin_set() {
  case "$1" in TBD*) die "$2: the release pins are filled at release time (this checkout has none yet)" ;; esac
}

# ---- MoltenVK ----------------------------------------------------------------------------------------------------
if [ "$DO_MVK" -eq 1 ]; then
  [ "$FORCE" -eq 0 ] || rm -rf "$DL/moltenvk/MoltenVK"
  MVK_TAR="$DL/moltenvk/MoltenVK-macos.tar"
  MVK_LIB_PATH="$DL/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
  get "$MVK_URL" "$MVK_SHA" "$MVK_TAR"
  if [ ! -f "$MVK_LIB_PATH" ]; then
    verify "$MVK_TAR" "$MVK_SHA"
    tar -xf "$MVK_TAR" -C "$DL/moltenvk"
    [ -f "$MVK_LIB_PATH" ] || die "tar did not contain MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
    echo "unpack $MVK_LIB_PATH"
  fi
fi

# ---- libretro and Vulkan headers ---------------------------------------------------------------------------------
if [ "$DO_HEADERS" -eq 1 ]; then
  if [ "$FORCE" -eq 1 ]; then
    rm -f "$VENDOR/libretro.h" "$VENDOR/libretro_vulkan.h" "$VENDOR/include/.vulkan-headers-$VKH_VER"
    rm -rf "$DL/vulkan-headers/src"
  fi
  mkdir -p "$VENDOR"
  for pair in "libretro.h $LIBRETRO_SHA" "libretro_vulkan.h $LIBRETRO_VK_SHA"; do
    # shellcheck disable=SC2086  # intentional split of "name sha" into two words
    set -- $pair
    name=$1; sha=$2
    get "$RA_BASE/$name" "$sha" "$DL/libretro-headers/$name"
    if ! ok "$VENDOR/$name" "$sha"; then
      verify "$DL/libretro-headers/$name" "$sha"
      cp "$DL/libretro-headers/$name" "$VENDOR/$name"
      echo "copy   $VENDOR/$name"
    fi
  done

  # ---- Vulkan-Headers (include/ only) ------------------------------------------------------------------------------
  VKH_TGZ="$DL/vulkan-headers/Vulkan-Headers-$VKH_VER.tar.gz"
  VKH_STAMP="$VENDOR/include/.vulkan-headers-$VKH_VER"
  get "$VKH_URL" "$VKH_SHA" "$VKH_TGZ"
  if [ ! -f "$VKH_STAMP" ] || [ ! -f "$VENDOR/include/vulkan/vulkan.h" ]; then
    verify "$VKH_TGZ" "$VKH_SHA"
    rm -rf "$DL/vulkan-headers/src"
    mkdir -p "$DL/vulkan-headers/src" "$VENDOR/include"
    tar -xzf "$VKH_TGZ" -C "$DL/vulkan-headers/src"
    SRC_INC="$DL/vulkan-headers/src/Vulkan-Headers-$VKH_VER/include"
    [ -f "$SRC_INC/vulkan/vulkan.h" ] || die "tag archive has no include/vulkan/vulkan.h"
    rm -rf "$VENDOR/include/vulkan" "$VENDOR/include/vk_video"
    cp -R "$SRC_INC/vulkan" "$SRC_INC/vk_video" "$VENDOR/include/"
    : > "$VKH_STAMP"
    echo "copy   $VENDOR/include/{vulkan,vk_video}"
  fi
fi

# ---- our core (release asset) ------------------------------------------------------------------------------------
LAZPY_DIR="$DL/lazpy-core"
if [ "$DO_CORE" -eq 1 ]; then
  case "$OS_KIND" in
    mac) CORE_ZIP=$LAZPY_CORE_ZIP; CORE_SHA=$LAZPY_CORE_SHA; CORE_FILE=azahar_lazpy_libretro.dylib ;;
    win) CORE_ZIP=$LAZPY_CORE_ZIP_WIN; CORE_SHA=$LAZPY_CORE_SHA_WIN; CORE_FILE=azahar_lazpy_libretro.dll ;;
    *) die "no core is released for this OS (macOS arm64 and Windows x64 only)" ;;
  esac
  pin_set "$CORE_SHA" --lazpy-core
  [ "$FORCE" -eq 0 ] || rm -f "$LAZPY_DIR/$CORE_FILE" "$LAZPY_DIR/NOTICES.md" "$LAZPY_DIR/SOURCE.md"
  if [ "$OS_KIND" = mac ]; then
    # the macOS zip has the same bytes in the previous release: fall back to it when the current page lacks it
    _fb=""; [ -z "$REL_BASE_PREV" ] || _fb="$REL_BASE_PREV/$CORE_ZIP"
    get "$REL_BASE/$CORE_ZIP" "$CORE_SHA" "$LAZPY_DIR/$CORE_ZIP" "$_fb"
  else
    # no fallback for the Windows zip: it exists only in this release
    MISSING_HINT="$REL_TAG is not published yet"
    get "$REL_BASE/$CORE_ZIP" "$CORE_SHA" "$LAZPY_DIR/$CORE_ZIP"
    MISSING_HINT=""   # the hint belongs to this download only
  fi
  if [ ! -f "$LAZPY_DIR/$CORE_FILE" ] || [ "$(cat "$LAZPY_DIR/.unpacked-sha256" 2>/dev/null)" != "$CORE_SHA" ]; then
    verify "$LAZPY_DIR/$CORE_ZIP" "$CORE_SHA"
    unzip -q -o "$LAZPY_DIR/$CORE_ZIP" "$CORE_FILE" NOTICES.md SOURCE.md -d "$LAZPY_DIR"
    [ -f "$LAZPY_DIR/$CORE_FILE" ] || die "zip did not contain $CORE_FILE"
    echo "$CORE_SHA" > "$LAZPY_DIR/.unpacked-sha256"
    echo "unpack $LAZPY_DIR/{$CORE_FILE,NOTICES.md,SOURCE.md}"
  fi
fi

# ---- the test app (release asset) --------------------------------------------------------------------------------
if [ "$DO_APP" -eq 1 ]; then
  pin_set "$TESTAPP_SHA" --testapp
  _fb=""; [ -z "$REL_BASE_PREV" ] || _fb="$REL_BASE_PREV/testapp.3dsx"
  get "$REL_BASE/testapp.3dsx" "$TESTAPP_SHA" "$DL/testapp/testapp.3dsx" "$_fb"
  mkdir -p "$ROOT/build"
  if ! ok "$ROOT/build/testapp.3dsx" "$TESTAPP_SHA"; then
    verify "$DL/testapp/testapp.3dsx" "$TESTAPP_SHA"
    cp "$DL/testapp/testapp.3dsx" "$ROOT/build/testapp.3dsx"
    echo "copy   $ROOT/build/testapp.3dsx"
  fi
fi

# ---- the prebuilt host (release asset) ---------------------------------------------------------------------------
if [ "$DO_HOST" -eq 1 ]; then
  HOST_DIR="$DL/lazpy-host"
  case "$OS_KIND" in
    mac) HOST_OS_NAME=macos-arm64; HOST_SHA=$LAZPY_HOST_SHA_MAC; HOST_FILES="libazhost.dylib azhost"; HOST_DOCS="LICENSE SOURCE.md" ;;
    win) HOST_OS_NAME=windows-x64; HOST_SHA=$LAZPY_HOST_SHA_WIN; HOST_FILES="libazhost.dll azhost.exe"; HOST_DOCS="NOTICES.md LICENSE SOURCE.md" ;;
    *) die "no prebuilt host is released for this OS (macOS arm64 and Windows x64 only)" ;;
  esac
  HOST_ZIP="libazahar-py-host-${REL_TAG#v}-$HOST_OS_NAME.zip"
  pin_set "$HOST_SHA" --host
  [ "$FORCE" -eq 0 ] || rm -f "$HOST_DIR/$HOST_ZIP" "$HOST_DIR/.unpacked-sha256"
  MISSING_HINT="$REL_TAG may not carry the host zips"
  get "$REL_BASE/$HOST_ZIP" "$HOST_SHA" "$HOST_DIR/$HOST_ZIP"
  MISSING_HINT=""
  # unpack unless build/ already holds exactly the pinned files: a host built with make (or an older one) differs from the
  # unpacked zip, so a plain --host replaces it; the same bytes are left alone ("have")
  _have=1
  [ "$(cat "$HOST_DIR/.unpacked-sha256" 2>/dev/null)" = "$HOST_SHA" ] || _have=0
  for f in $HOST_FILES; do cmp -s "$ROOT/build/$f" "$HOST_DIR/unpacked/$f" 2>/dev/null || _have=0; done
  if [ "$_have" -eq 0 ]; then
    verify "$HOST_DIR/$HOST_ZIP" "$HOST_SHA"
    mkdir -p "$ROOT/build"
    # shellcheck disable=SC2086  # intentional split: two file names
    unzip -q -o "$HOST_DIR/$HOST_ZIP" $HOST_FILES $HOST_DOCS -d "$HOST_DIR/unpacked"
    for f in $HOST_FILES; do
      [ -f "$HOST_DIR/unpacked/$f" ] || die "zip did not contain $f"
      cp "$HOST_DIR/unpacked/$f" "$ROOT/build/$f"
    done
    chmod +x "$ROOT/build/azhost" "$ROOT/build/azhost.exe" 2>/dev/null || true
    echo "$HOST_SHA" > "$HOST_DIR/.unpacked-sha256"
    echo "unpack $ROOT/build/{$(echo $HOST_FILES | sed 's/ /,/')}"
  fi
fi

echo
echo "Done. Everything verified against its pinned sha256."
if [ "$DO_MVK" -eq 1 ]; then
  echo "  MoltenVK    $MVK_LIB_PATH  ($MVK_VER)"
  echo "  use:  export MVK_LIB=\"$MVK_LIB_PATH\""
fi
if [ "$DO_HEADERS" -eq 1 ]; then
  echo "  headers     $VENDOR/libretro.h  $VENDOR/libretro_vulkan.h  $VENDOR/include/{vulkan,vk_video}  (Vulkan-Headers $VKH_VER)"
fi
if [ "$DO_CORE" -eq 1 ]; then
  echo "  core        our core is at dl/lazpy-core/$CORE_FILE, the default core path (LAZ_CORE overrides it)"
fi
if [ "$DO_HOST" -eq 1 ]; then
  echo "  host        the prebuilt host is in $ROOT/build/ (SOURCE.md, LICENSE and, on Windows, NOTICES.md: dl/lazpy-host/unpacked/)"
fi
if [ "$DO_APP" -eq 1 ]; then
  echo "  test app    $ROOT/build/testapp.3dsx"
fi
