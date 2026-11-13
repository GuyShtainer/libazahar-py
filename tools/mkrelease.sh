#!/bin/sh
# mkrelease.sh <tag>: stage a release in runs/release/<tag>/ (nothing is committed, pushed or uploaded).
#   core zip      our core + NOTICES.md + LICENSE + COPYING-azahar.txt + SOURCE.md + build.inputs
#   source asset  Azahar's unified tarball minus the drop list, plus a note member
#   OpenSSL and citra_system_archives tarballs (byte for byte), the build-files asset, the test app, NOTICES.md,
#   SOURCE.md and SHA256SUMS.
# Inputs (repo-relative, each overridable): LAZ_REL_CORE LAZ_REL_INPUTS LAZ_REL_APP LAZ_REL_TARBALL LAZ_REL_OSSL
# LAZ_REL_SNAP LAZ_REL_NEWLIB LAZ_REL_BUILD (the cmake build folder). Run twice, the assets are byte-identical (compare SHA256SUMS
# minus the build-files line, which embeds HEAD's commit id). Needs bsdtar, zip, shasum, git.
set -eu

# citra_system_archives snapshot, commit f470e0c9d341db73b8a24880295d2eab4cd81660 (our own downloaded bytes)
SNAP_SHA=faada632bdad4f5d437998aa1ce20a72715e55999387538b7f3ee6aca135d7a3
# COPYING.NEWLIB of newlib 4.6.0 (the version devkitARM ships), quoted in NOTICES.md for the test app
NEWLIB_SHA=f3afe48e4bc6ed8466a42e9dacb6be1d8f9cbf5aac15cb8e474a5ccde8b40ef6

[ $# -eq 1 ] || { echo "usage: $0 <tag>   (for example v0.1.0)" >&2; exit 2; }
TAG=$1
ROOT="${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"
export TZ=UTC LC_ALL=C
die() { echo "mkrelease: $*" >&2; exit 1; }
sha_of() { shasum -a 256 "$1" | cut -d' ' -f1; }
pin() { sed -n "s/^$1=//p" core/PIN; }
inp() { sed -n "s/^$1=//p" "$INPUTS"; }

CORE="${LAZ_REL_CORE:-build-core/azahar_lazpy_libretro.dylib}"
INPUTS="${LAZ_REL_INPUTS:-build-core/build.inputs}"
APP="${LAZ_REL_APP:-build/testapp.3dsx}"
TARBALL="${LAZ_REL_TARBALL:-$(pin SRC_FILE)}"
OSSL="${LAZ_REL_OSSL:-dl/openssl-src/openssl-$(pin OPENSSL_VERSION).tar.gz}"
SNAP="${LAZ_REL_SNAP:-dl/sysarch-src/citra_system_archives-f470e0c.tar.gz}"
BUILD="${LAZ_REL_BUILD:-build-core/build}"
NEWLIB="${LAZ_REL_NEWLIB:-dl/newlib-licence/COPYING.NEWLIB-4.6.0}"
for f in "$CORE" "$INPUTS" "$APP" "$TARBALL" "$OSSL" "$SNAP" "$NEWLIB" NOTICES.md LICENSE; do
  [ -f "$f" ] || die "missing input $f"
done

AZTAG=$(pin AZAHAR_TAG); REV=$(pin LAZPY_REV); TOP=$(pin SRC_TOP); DROP=$(pin LAZ_CORE_DROP); OSV=$(pin OPENSSL_VERSION)
SRC_SHA=$(pin SRC_SHA256)
[ "$(sha_of "$TARBALL")" = "$SRC_SHA" ] || die "$TARBALL does not match core/PIN's SRC_SHA256"
OSSL_SHA=$(grep -A1 '^- Source:' core/OPENSSL.md | grep -o '[0-9a-f]\{64\}' | head -1)
[ -n "$OSSL_SHA" ] && [ "$(sha_of "$OSSL")" = "$OSSL_SHA" ] || die "$OSSL does not match core/OPENSSL.md's sha256"
[ "$(sha_of "$SNAP")" = "$SNAP_SHA" ] || die "$SNAP does not match this script's SNAP_SHA"
[ "$(sha_of "$NEWLIB")" = "$NEWLIB_SHA" ] || die "$NEWLIB does not match this script's NEWLIB_SHA"
[ "$DROP" = "src/core/hw/default_keys.h src/core/hle/service/http/ctr-common-1-cert.h src/core/hle/service/http/ctr-common-1-key.h externals/libressl" ] \
  || die "core/PIN's LAZ_CORE_DROP differs from the one the note text describes"

CORE_ZIP="azahar_lazpy_libretro-$AZTAG-lazpy.$REV-macos-arm64.zip"
SRC_ASSET="azahar-unified-source-$AZTAG-lazpy-nokeys.tar.xz"
OSSL_ASSET="openssl-$OSV.tar.gz"
SNAP_ASSET="citra_system_archives-f470e0c.tar.gz"
BUILD_ASSET="libazahar-py-core-build-$TAG.tar.gz"
OUT="runs/release/$TAG"; STG="runs/release/$TAG.stage"
rm -rf "$OUT" "$STG"; mkdir -p "$OUT" "$STG"
STAMP=202601010000

# ---- the source asset: Azahar's tarball minus the drop list, plus a note member (first) ----------------------------
make_source_asset() {
  # members dropped: a name equal to an entry or under it (the entry's own directory member counts)
  _n=$(tar -tf "$TARBALL" | awk -v top="$TOP" 'BEGIN { e = top "/externals/libressl" }
    { name = $0; sub(/\/$/, "", name); if (name == e || index(name, e "/") == 1) c++ }
    END { print c + 0 }')
  mkdir -p "$STG/note/$TOP"
  printf '%s\n' "Removed by libazahar-py on 2026-11-13 from Azahar's azahar-unified-source-$AZTAG.tar.xz (sha256 $SRC_SHA), before building its core: src/core/hw/default_keys.h, src/core/hle/service/http/ctr-common-1-cert.h and src/core/hle/service/http/ctr-common-1-key.h (console key and certificate data, not used by this build: patches 0007 and 0008, ENABLE_BUILTIN_KEYBLOB=OFF); externals/libressl/, the bundled LibreSSL, $_n members (not used: this build links OpenSSL $OSV, USE_SYSTEM_OPENSSL=ON). Every other file is unchanged." \
    > "$STG/note/$TOP/LIBAZAHAR-PY-REMOVED.txt"
  touch -t "$STAMP" "$STG/note/$TOP/LIBAZAHAR-PY-REMOVED.txt"
  set --
  for e in $DROP; do set -- "$@" --exclude "$TOP/$e"; done
  case "$TARBALL" in /*) _abs=$TARBALL ;; *) _abs="$ROOT/$TARBALL" ;; esac
  tar -c -J -f "$OUT/$SRC_ASSET" --uid 0 --gid 0 --uname '' --gname '' "$@" -C "$STG/note" "$TOP/LIBAZAHAR-PY-REMOVED.txt" "@$_abs"
  [ "$(tar -tf "$OUT/$SRC_ASSET" | grep -c 'externals/libressl')" -eq 0 ] || die "externals/libressl is still in the source asset"
}

# ---- SOURCE.md --------------------------------------------------------------------------------------------------
make_source_md() {
  _ssha=$(sha_of "$OUT/$SRC_ASSET")
  _cc=$(grep -h '^set(CMAKE_C_COMPILER_\(ID\|VERSION\) ' "$BUILD"/CMakeFiles/*/CMakeCCompiler.cmake | sed 's/^set([A-Z_]*_COMPILER_[A-Z]* "\(.*\)")$/\1/' | tr '\n' ' ' | sed 's/ $//')
  _cxx=$(grep -h '^set(CMAKE_CXX_COMPILER_\(ID\|VERSION\) ' "$BUILD"/CMakeFiles/*/CMakeCXXCompiler.cmake | sed 's/^set([A-Z_]*_COMPILER_[A-Z]* "\(.*\)")$/\1/' | tr '\n' ' ' | sed 's/ $//')
  {
    echo "# SOURCE"
    echo
    echo "What the binary is: \`azahar_lazpy_libretro.dylib\`, macOS 15 or later, arm64. Azahar $AZTAG (commit $(pin AZAHAR_COMMIT)) with libazahar-py's patches, built with OpenSSL $OSV linked statically. Release tag: $TAG."
    echo
    echo "Built at repository commit $(inp head) (translate older SHAs with \`docs/commit-map-g8.tsv\`, then docs/commit-map-g8b.tsv)."
    echo
    echo "The build script \`tools/build-core.sh\` has sha256 $(inp script). The patches, in order:"
    echo
    sed -n 's/^patch \(.*\)=\([0-9a-f]*\)$/- `\1` sha256 \2/p' "$INPUTS"
    echo
    echo "## Corresponding Source, all on this release page"
    echo
    echo "1. \`$SRC_ASSET\`, sha256 $_ssha: Azahar's \`azahar-unified-source-$AZTAG.tar.xz\` ($(pin SRC_URL), sha256 $SRC_SHA) minus the drop list, plus the note member \`$TOP/LIBAZAHAR-PY-REMOVED.txt\`. The binary was built from exactly this tree plus the patches. Azahar's original tarball also contains the bundled LibreSSL; we removed it with the three headers."
    echo "2. \`$OSSL_ASSET\`, sha256 $OSSL_SHA: OpenSSL's own tarball (https://github.com/openssl/openssl/releases/download/openssl-$OSV/$OSSL_ASSET), the source of the statically linked \`libssl.a\` and \`libcrypto.a\`. \`core/OPENSSL.md\` says how they were built."
    echo "3. \`$SNAP_ASSET\`, sha256 $SNAP_SHA: the generator and fonts behind the compiled-in system archives (open-source replacement archives generated by the Citra project's citra_system_archives)."
    echo "4. \`$BUILD_ASSET\`: the patches, the pins, the options, \`core/OPENSSL.md\` and the build script."
    echo "5. This repository at the tag $TAG."
    echo
    echo "## The build"
    echo
    echo "The cmake command (\`<repo>\` is the checkout):"
    echo
    echo '```text'
    inp cmake
    echo '```'
    echo
    echo "Compilers (from the cmake configure step): C $_cc; C++ $_cxx."
    echo
    echo "## Rebuilding"
    echo
    echo "Homebrew ships only its current \`openssl@3\`. If it is $OSV, \`tools/build-core.sh\` finds it. If not, build $OSV from (2) with the recipe in \`core/OPENSSL.md\` (not tested by this project) and set \`LAZ_OPENSSL_PREFIX\` to its install prefix. Then \`LAZ_CORE_PIN=core/PIN-nokeys tools/build-core.sh --build\`."
  } > "$OUT/SOURCE.md"
}

# ---- the core zip -------------------------------------------------------------------------------------------------
make_core_zip() {
  mkdir -p "$STG/zip"
  cp "$CORE" "$STG/zip/azahar_lazpy_libretro.dylib"
  cp NOTICES.md "$STG/zip/NOTICES.md"
  cp LICENSE "$STG/zip/LICENSE"
  tar -xOJf "$TARBALL" "$TOP/license.txt" > "$STG/zip/COPYING-azahar.txt"
  cp "$OUT/SOURCE.md" "$STG/zip/SOURCE.md"
  cp "$INPUTS" "$STG/zip/build.inputs"
  for f in "$STG"/zip/*; do touch -t "$STAMP" "$f"; done
  _abs="$ROOT/$OUT/$CORE_ZIP"
  (cd "$STG/zip" && zip -X -9 -q "$_abs" COPYING-azahar.txt LICENSE NOTICES.md SOURCE.md azahar_lazpy_libretro.dylib build.inputs)
}

make_source_asset
make_source_md
make_core_zip
cp "$OSSL" "$OUT/$OSSL_ASSET"
cp "$SNAP" "$OUT/$SNAP_ASSET"
git archive --format=tar.gz --prefix=libazahar-py-core-build/ -o "$OUT/$BUILD_ASSET" HEAD core tools/build-core.sh tools/untar_checked.py
cp "$APP" "$OUT/testapp.3dsx"
cp NOTICES.md "$OUT/NOTICES.md"
_names=$(cd "$OUT" && ls | LC_ALL=C sort)
# shellcheck disable=SC2086  # intentional split of the sorted asset names
(cd "$OUT" && shasum -a 256 $_names > "$ROOT/$STG.sums")
mv "$STG.sums" "$OUT/SHA256SUMS"
rm -rf "$STG"
echo "staged $OUT:"
(cd "$OUT" && ls -l | sed 's/^/  /')
