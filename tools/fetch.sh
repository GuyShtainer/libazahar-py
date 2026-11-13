#!/bin/sh
# fetch.sh: download MoltenVK, the libretro/Vulkan headers, our core and the test app, pinned and sha256-checked.
#
#   tools/fetch.sh [PART...] [--force]
#     --moltenvk     MoltenVK (dl/moltenvk/)
#     --headers      the libretro and Vulkan headers (vendor/)
#     --lazpy-core   our core from the release: the zip, verified; the core, NOTICES.md and SOURCE.md unpacked into
#                    dl/lazpy-core/ (the core there is the default core path; LAZ_CORE overrides it)
#     --testapp      the test app from the release, into dl/testapp/ and build/testapp.3dsx
#     --force        delete and refetch what the chosen parts fetch
#   No part flag means --moltenvk --headers. A second run downloads nothing.
#   LAZPY_ROOT=<dir>        use <dir> instead of the repo root (for tests on a temp copy)
#   LAZ_RELEASE_BASE=<url>  use <url> instead of the release page (for tests, file://)
#
# Downloads are untrusted data (docs/map/rules.md rule 2): each lives in its own folder under dl/, is hashed BEFORE
# it is unpacked, and nothing from a download is ever run here. dl/ and vendor/ are git-ignored. Needs only the macOS
# stock curl, shasum, unzip, tar, cp.
set -eu

ROOT="${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
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
REL_TAG=v0.1.0
REL_BASE="${LAZ_RELEASE_BASE:-https://github.com/GuyShtainer/libazahar-py/releases/download/$REL_TAG}"
LAZPY_CORE_ZIP=azahar_lazpy_libretro-2126.2-lazpy.1-macos-arm64.zip
LAZPY_CORE_SHA=6ef0c129f85c996f534394d295d5158d1a6604c8c3f993d3e8a8bf90e122987f
TESTAPP_SHA=53b699e87974bd5c74cc6d14123eba95f0b0c02cdcd174e28249f768512ccabc
# ------------------------------------------------------------------------------------------------------------------

FORCE=0; DO_MVK=0; DO_HEADERS=0; DO_CORE=0; DO_APP=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --moltenvk) DO_MVK=1 ;;
    --headers) DO_HEADERS=1 ;;
    --lazpy-core) DO_CORE=1 ;;
    --testapp) DO_APP=1 ;;
    *) echo "usage: $0 [--moltenvk] [--headers] [--lazpy-core] [--testapp] [--force]" >&2; exit 2 ;;
  esac
done
if [ $((DO_MVK + DO_HEADERS + DO_CORE + DO_APP)) -eq 0 ]; then DO_MVK=1; DO_HEADERS=1; fi

die() { echo "fetch.sh: $*" >&2; exit 1; }

sha_of() { shasum -a 256 "$1" | cut -d' ' -f1; }

# ok FILE SHA: true when FILE exists and has that sha256
ok() { [ -f "$1" ] && [ "$(sha_of "$1")" = "$2" ]; }

# get URL SHA FILE: make FILE verified; download only if it is missing or wrong. A mismatch deletes the file and exits.
get() {
  _url=$1; _sha=$2; _file=$3
  if [ "$FORCE" -eq 0 ] && ok "$_file" "$_sha"; then
    echo "have   $_file (sha256 ok)"
    return 0
  fi
  mkdir -p "$(dirname "$_file")"
  rm -f "$_file"
  echo "fetch  $_url"
  curl -fsSL --retry 2 -o "$_file" "$_url" || { rm -f "$_file"; die "download failed: $_url"; }
  _got=$(sha_of "$_file")
  if [ "$_got" != "$_sha" ]; then
    rm -f "$_file"
    die "SHA256 MISMATCH for $_url
  expected $_sha
  got      $_got
  the file was deleted; nothing was unpacked"
  fi
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
  pin_set "$LAZPY_CORE_SHA" --lazpy-core
  [ "$FORCE" -eq 0 ] || rm -f "$LAZPY_DIR/azahar_lazpy_libretro.dylib" "$LAZPY_DIR/NOTICES.md" "$LAZPY_DIR/SOURCE.md"
  get "$REL_BASE/$LAZPY_CORE_ZIP" "$LAZPY_CORE_SHA" "$LAZPY_DIR/$LAZPY_CORE_ZIP"
  if [ ! -f "$LAZPY_DIR/azahar_lazpy_libretro.dylib" ] || [ "$(cat "$LAZPY_DIR/.unpacked-sha256" 2>/dev/null)" != "$LAZPY_CORE_SHA" ]; then
    verify "$LAZPY_DIR/$LAZPY_CORE_ZIP" "$LAZPY_CORE_SHA"
    unzip -q -o "$LAZPY_DIR/$LAZPY_CORE_ZIP" azahar_lazpy_libretro.dylib NOTICES.md SOURCE.md -d "$LAZPY_DIR"
    [ -f "$LAZPY_DIR/azahar_lazpy_libretro.dylib" ] || die "zip did not contain azahar_lazpy_libretro.dylib"
    echo "$LAZPY_CORE_SHA" > "$LAZPY_DIR/.unpacked-sha256"
    echo "unpack $LAZPY_DIR/{azahar_lazpy_libretro.dylib,NOTICES.md,SOURCE.md}"
  fi
fi

# ---- the test app (release asset) --------------------------------------------------------------------------------
if [ "$DO_APP" -eq 1 ]; then
  pin_set "$TESTAPP_SHA" --testapp
  get "$REL_BASE/testapp.3dsx" "$TESTAPP_SHA" "$DL/testapp/testapp.3dsx"
  mkdir -p "$ROOT/build"
  if ! ok "$ROOT/build/testapp.3dsx" "$TESTAPP_SHA"; then
    verify "$DL/testapp/testapp.3dsx" "$TESTAPP_SHA"
    cp "$DL/testapp/testapp.3dsx" "$ROOT/build/testapp.3dsx"
    echo "copy   $ROOT/build/testapp.3dsx"
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
  echo "  core        our core is at dl/lazpy-core/azahar_lazpy_libretro.dylib, the default core path (LAZ_CORE overrides it)"
fi
if [ "$DO_APP" -eq 1 ]; then
  echo "  test app    $ROOT/build/testapp.3dsx"
fi
