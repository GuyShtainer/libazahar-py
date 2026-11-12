#!/bin/sh
# fetch.sh: download the Azahar libretro core, MoltenVK and the libretro/Vulkan headers, pinned and sha256-checked.
#
#   tools/fetch.sh            fetch what is missing or unverified; a second run downloads nothing
#   tools/fetch.sh --force    delete and refetch everything
#   LAZPY_ROOT=<dir>          use <dir> instead of the repo root (for tests on a temp copy)
#
# Downloads are untrusted data (docs/map/rules.md rule 2): each lives in its own folder under dl/, is hashed BEFORE
# it is unpacked, and nothing from a download is ever run here. dl/ and vendor/ are git-ignored. Needs only the macOS
# stock curl, shasum, unzip, tar, cp.
set -eu

ROOT="${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DL="$ROOT/dl"
VENDOR="$ROOT/vendor"

# ---- pins (change a version only together with its sha256) ------------------------------------------------------
CORE_VER=2126.2
CORE_URL="Azahar's releases page"
CORE_SHA=[stock core sha256]

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
# ------------------------------------------------------------------------------------------------------------------

FORCE=0
case "${1:-}" in
  "") ;;
  --force) FORCE=1 ;;
  *) echo "usage: $0 [--force]" >&2; exit 2 ;;
esac

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

if [ "$FORCE" -eq 1 ]; then
  rm -f "$DL/azahar/azahar_libretro.dylib" "$VENDOR/libretro.h" "$VENDOR/libretro_vulkan.h" \
        "$VENDOR/include/.vulkan-headers-$VKH_VER"
  rm -rf "$DL/moltenvk/MoltenVK" "$DL/vulkan-headers/src"
fi

# ---- Azahar core -------------------------------------------------------------------------------------------------
CORE_ZIP="$DL/azahar/stock-core.zip"
CORE_LIB="$DL/azahar/azahar_libretro.dylib"
get "$CORE_URL" "$CORE_SHA" "$CORE_ZIP"
if [ ! -f "$CORE_LIB" ]; then
  verify "$CORE_ZIP" "$CORE_SHA"
  unzip -q -o "$CORE_ZIP" azahar_libretro.dylib -d "$DL/azahar"
  [ -f "$CORE_LIB" ] || die "zip did not contain azahar_libretro.dylib"
  echo "unpack $CORE_LIB"
fi

# ---- MoltenVK ----------------------------------------------------------------------------------------------------
MVK_TAR="$DL/moltenvk/MoltenVK-macos.tar"
MVK_LIB_PATH="$DL/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
get "$MVK_URL" "$MVK_SHA" "$MVK_TAR"
if [ ! -f "$MVK_LIB_PATH" ]; then
  verify "$MVK_TAR" "$MVK_SHA"
  tar -xf "$MVK_TAR" -C "$DL/moltenvk"
  [ -f "$MVK_LIB_PATH" ] || die "tar did not contain MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib"
  echo "unpack $MVK_LIB_PATH"
fi

# ---- libretro headers --------------------------------------------------------------------------------------------
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

cat <<EOF

Done. Everything verified against its pinned sha256.
  core        $CORE_LIB  (Azahar $CORE_VER)
  MoltenVK    $MVK_LIB_PATH  ($MVK_VER)
  headers     $VENDOR/libretro.h  $VENDOR/libretro_vulkan.h  $VENDOR/include/{vulkan,vk_video}  (Vulkan-Headers $VKH_VER)
Use:
  export MVK_LIB="$MVK_LIB_PATH"
  cc -O2 -I $VENDOR -I $VENDOR/include -o build/fe2 prototype/fe2.c -framework OpenGL -lz
EOF
