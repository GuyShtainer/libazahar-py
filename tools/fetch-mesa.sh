#!/bin/sh
# fetch-mesa.sh DEST: download MSYS2's Mesa (lavapipe, a software Vulkan driver) and its 16 runtime packages (the last is the Vulkan loader: a GPU-less runner has no vulkan-1.dll), check
# each sha256 BEFORE unpacking, and unpack them into DEST (a folder of your own, never an MSYS2 install). Used by
# .github/workflows/test-windows-live.yml; prints "icd=<path to lvp_icd.x86_64.json>", "bin=<folder of the DLLs>" and "loader=<path to vulkan-1.dll>"
# (give that last one to the host as LAZ_MVK: a path with a separator is loaded from its own folder, not System32).
#   DEST            the folder to unpack into (default dl/mesa)
#   LAZ_MESA_BASE   use this URL instead of https://repo.msys2.org/mingw/mingw64 (for tests, file://)
# Pins: the packages and sha256 below are the ones trialled on 2026-11-19 (Mesa 26.2.7-1); the loader (1.4.363.0-1) was added 2026-11-20. Change a version only
# together with its sha256. Downloads are untrusted data: each package is hashed before tar sees it, the member list
# is refused if any name is absolute or holds "..", and nothing from a package is run here.
set -eu

BASE="${LAZ_MESA_BASE:-https://repo.msys2.org/mingw/mingw64}"
DEST="${1:-dl/mesa}"
PKG="$DEST.pkg"

PINS='mingw-w64-x86_64-mesa-26.2.7-1-any.pkg.tar.zst 87a13a5e6ac4817215025e4b4080865b8e10df2c06e4041462611d19277c0a51
mingw-w64-x86_64-llvm-libs-23.1.5-1-any.pkg.tar.zst 570fefeced592d99c65236a9fc6655fd0bc88620e196ac9ac29df90b1b899a85
mingw-w64-x86_64-spirv-tools-3~1.4.363.0-1-any.pkg.tar.zst c9fde26d5dafa8f175de4914fc81e38335d3cf58740445c8fec07232e11b7916
mingw-w64-x86_64-libsystre-1.0.2-3-any.pkg.tar.zst ea20a54127fe2a606ef0f2bef62b1abef77710840b661b832a933b4020bfe316
mingw-w64-x86_64-libtre-0.9.0-2-any.pkg.tar.zst c4051508d063258e1e02dd29615edb7d73c5c5f582ae42795fdd92e7ddce506b
mingw-w64-x86_64-libwinpthread-14.0.0.r598.ge3d18511f-1-any.pkg.tar.zst 942a62a3ecafbb4f5a80016685a0e3002a8de903012eed49c213e4f5b693668a
mingw-w64-x86_64-zlib-1.4-2-any.pkg.tar.zst 2a065fb3311d6c08bd2c7431a092b912ade08a83954474e06ea4eb0479d908cd
mingw-w64-x86_64-zstd-1.5.7-2-any.pkg.tar.zst 1add6705b344664f6aca108c85f79ab5bdd9e1162662bb06a4cf40a34f6e0907
mingw-w64-x86_64-libffi-3.8.1-1-any.pkg.tar.zst 92ba29c4a632a01affff6cb48617bcb62d65c02bfe6df2ed27fb087a9ba51de3
mingw-w64-x86_64-libxml2-2.15.4-3-any.pkg.tar.zst 5939674e6519082e2cb990f70ff0156a08876f85722d1178a3fdd7839fc38fb3
mingw-w64-x86_64-libiconv-1.19.1-1-any.pkg.tar.zst 50e915aa36fdbe6c84acc8954e939275609ba051cdb4eeeff3884453c28efde0
mingw-w64-x86_64-xz-5.8.4-1-any.pkg.tar.zst 2de0f26da60b7ff7aa192a226330d7de6b1099cb9b9f9de4145affb80146bbc8
mingw-w64-x86_64-gcc-libs-16.2.0-7-any.pkg.tar.zst 2df8a63906d569892b49719fb8ff73b7c5c8abb49bdaccf9a35dc709f182b7e2
mingw-w64-x86_64-libstdc++-16.2.0-7-any.pkg.tar.zst 578db695632bdb5bafd716958c4caa62560f3de2633680b258ae6f684201276d
mingw-w64-x86_64-gettext-runtime-1.0-1-any.pkg.tar.zst be68d7f260633284b910c588c6d82ee304a81c8817a686d2cd9df83f872c27af
mingw-w64-x86_64-libgcc-16.2.0-7-any.pkg.tar.zst 6d1311b397ba33be542fd46bae3de60338bfd967e95e221847f01269e98983b8
mingw-w64-x86_64-vulkan-loader-1~1.4.363.0-1-any.pkg.tar.zst 281fa31b1a023485d4fd04a092a8b5e9ca2f59804df7fcf9f2d4e5aaa5438af0'

die() { echo "fetch-mesa: $*" >&2; exit 1; }
sha_of() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
command -v zstd >/dev/null 2>&1 || die "zstd is not on PATH (MSYS2 has it)"

mkdir -p "$PKG" "$DEST"
DEST=$(cd "$DEST" && pwd)   # absolute, so the printed paths work from any folder
# Pass 1: download and verify every package; nothing is unpacked until all of them match.
echo "$PINS" | while read -r f want; do
  [ -f "$PKG/$f" ] && [ "$(sha_of "$PKG/$f")" = "$want" ] && { echo "have   $f"; continue; }
  rm -f "$PKG/$f"
  url="$BASE/$(printf %s "$f" | sed 's/~/%7E/; s/+/%2B/g')"
  echo "fetch  $url"
  curl -fsSL --retry 2 -o "$PKG/$f" "$url" || { rm -f "$PKG/$f"; die "download failed: $url"; }
  got=$(sha_of "$PKG/$f")
  [ "$got" = "$want" ] || { rm -f "$PKG/$f"; die "SHA256 MISMATCH for $f (deleted): got $got"; }
done
# Pass 2: refuse an unsafe member list, then unpack (packages only; the docs and headers are skipped).
echo "$PINS" | while read -r f want; do
  zstd -dc "$PKG/$f" | tar -t | grep -E '^/|(^|/)\.\.(/|$)' >/dev/null && die "REFUSED: unsafe member in $f"
  zstd -dc "$PKG/$f" | tar -x -C "$DEST" --exclude='mingw64/include' --exclude='mingw64/share/doc' --exclude='mingw64/share/man' \
    --exclude='mingw64/share/locale' --exclude='mingw64/share/info' || die "unpack failed: $f"
done

ICD="$DEST/mingw64/share/vulkan/icd.d/lvp_icd.x86_64.json"
[ -f "$ICD" ] || die "no lavapipe ICD at $ICD after unpacking"
[ -f "$DEST/mingw64/bin/vulkan-1.dll" ] || die "no vulkan-1.dll after unpacking"
[ -f "$DEST/mingw64/bin/vulkan_lvp.dll" ] || die "no vulkan_lvp.dll after unpacking"
if command -v cygpath >/dev/null 2>&1; then
  echo "icd=$(cygpath -w "$ICD")"; echo "bin=$(cygpath -w "$DEST/mingw64/bin")"
  echo "loader=$(cygpath -w "$DEST/mingw64/bin/vulkan-1.dll")"
else
  echo "icd=$ICD"; echo "bin=$DEST/mingw64/bin"; echo "loader=$DEST/mingw64/bin/vulkan-1.dll"
fi
