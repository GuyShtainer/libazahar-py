#!/bin/sh
# mkrelease.sh <tag>: stage a release in runs/release/<tag>/ (nothing is committed, pushed or uploaded).
#   core zip      our core + NOTICES.md + LICENSE + COPYING-azahar.txt + SOURCE.md + build.inputs
#   source asset  Azahar's unified tarball minus the drop list, plus a note member
#   OpenSSL and citra_system_archives tarballs (byte for byte), the build-files asset, the test app, NOTICES.md,
#   SOURCE.md and SHA256SUMS.
# Inputs (repo-relative, each overridable): LAZ_REL_CORE LAZ_REL_INPUTS LAZ_REL_APP LAZ_REL_TARBALL LAZ_REL_OSSL
# LAZ_REL_SNAP LAZ_REL_NEWLIB LAZ_REL_BUILD (the cmake build folder). Run twice, the assets are byte-identical (compare SHA256SUMS
# minus the build-files line, which embeds HEAD's commit id). Needs bsdtar, zip, shasum, git.
#
# Windows mode (v1.1.0 and later, run in the MSYS2 MINGW64 shell on the PC; needs tar, xz, zip, git, curl, sha256sum):
#   mkrelease.sh --inherit v1.0.0 --win-artifact DIR --out DIR
# stages a release whose macOS side is inherited, byte for byte, from v1.0.0: SHA256SUMS is downloaded from the v1.0.0
# page and checked against the pinned digest V1_0_0_SHA256SUMS first, then each of the seven inherited assets against
# its line, then five of them against the pins this repo already holds. DIR of --win-artifact holds the CI artifact:
# azahar_lazpy_libretro.dll, build.inputs, NOTICES-windows-x64.md, gate_f2.txt, mingw-w64-runtime-source.tar
# (--no-runtime-source drops the last). The tag is the name of the --out folder; it must be v<pyproject version>.
# LAZ_INHERIT_BASE=<url> replaces the v1.0.0 page (tests, file://); the pinned digests still apply.
set -eu

# the GitHub digest of v1.0.0's SHA256SUMS: the anchor of everything inherited
V1_0_0_SHA256SUMS=288c2a257948498bb5c0f4e56a582ee311fd6654aa523b51fc85876e5ce19bec

# citra_system_archives snapshot, commit f470e0c9d341db73b8a24880295d2eab4cd81660 (our own downloaded bytes)
SNAP_SHA=faada632bdad4f5d437998aa1ce20a72715e55999387538b7f3ee6aca135d7a3
# COPYING.NEWLIB of newlib 4.6.0 (the version devkitARM ships), quoted in NOTICES.md for the test app
NEWLIB_SHA=f3afe48e4bc6ed8466a42e9dacb6be1d8f9cbf5aac15cb8e474a5ccde8b40ef6

usage() { echo "usage: $0 <tag>   (for example v1.0.0)
       $0 --inherit v1.0.0 --win-artifact DIR --out DIR [--no-runtime-source]" >&2; exit 2; }
INHERIT=""; WINART=""; WOUT=""; NO_RT=0; TAG=""
if [ "${1:-}" = --inherit ]; then
  while [ $# -gt 0 ]; do
    case "$1" in
      --inherit) [ $# -ge 2 ] || usage; INHERIT=$2; shift 2 ;;
      --win-artifact) [ $# -ge 2 ] || usage; WINART=$2; shift 2 ;;
      --out) [ $# -ge 2 ] || usage; WOUT=$2; shift 2 ;;
      --no-runtime-source) NO_RT=1; shift ;;
      *) usage ;;
    esac
  done
  [ -n "$INHERIT" ] && [ -n "$WINART" ] && [ -n "$WOUT" ] || usage
else
  [ $# -eq 1 ] || usage
  TAG=$1
fi
ROOT="${LAZ_ROOT:-${LAZPY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"   # LAZPY_ROOT: the old name, kept for 1.x
cd "$ROOT"
export TZ=UTC LC_ALL=C
die() { echo "mkrelease: $*" >&2; exit 1; }
# -t and --text: two spaces before the name, as v1.0.0 has (a Windows shasum or sha256sum writes " *" by default)
if command -v shasum >/dev/null 2>&1; then SUM256="shasum -a 256 -t"; else SUM256="sha256sum --text"; fi
sha_of() { $SUM256 "$1" | cut -d' ' -f1; }
pin() { sed -n "s/^$1=//p" core/PIN; }
inp() { sed -n "s/^$1=//p" "$INPUTS"; }

# ---- Windows mode: the v1.1.0 release, the macOS side inherited from v1.0.0 by checksum -------------------------------
win_release() {
  [ "$INHERIT" = v1.0.0 ] || die "--inherit supports v1.0.0 only"
  case "$WOUT" in /*|?:*) OUT=$WOUT ;; *) OUT="$ROOT/$WOUT" ;; esac
  case "$WINART" in /*|?:*) ART=$WINART ;; *) ART="$ROOT/$WINART" ;; esac
  TAG=$(basename "$OUT")
  _ver=$(sed -n 's/^version *= *"\(.*\)"/\1/p' pyproject.toml | head -1)
  [ "$TAG" = "v$_ver" ] || die "the --out folder is named $TAG, but pyproject's version is $_ver"
  [ -f tools/build-files.txt ] || die "tools/build-files.txt is missing"
  for f in azahar_lazpy_libretro.dll build.inputs NOTICES-windows-x64.md gate_f2.txt; do
    [ -f "$ART/$f" ] || die "missing $ART/$f"
  done
  RT=mingw-w64-runtime-source.tar
  [ "$NO_RT" -eq 1 ] || [ -f "$ART/$RT" ] || die "missing $ART/$RT (or pass --no-runtime-source)"
  INPUTS="$ART/build.inputs"; STAMP=202601010000
  AZTAG=$(pin AZAHAR_TAG); REV=$(pin LAZPY_REV); TOP=$(pin SRC_TOP); OSV=$(pin OPENSSL_VERSION)
  # the Windows core must be the one gate_f2.txt describes
  [ "$(sed -n 's/^core_sha256=//p' "$ART/gate_f2.txt")" = "$(sha_of "$ART/azahar_lazpy_libretro.dll")" ] \
    || die "gate_f2.txt's core_sha256 is not the DLL's sha256"
  [ "$(sed -n 1p "$ART/gate_f2.txt")" = "gate_f2 1 target=win64" ] || die "gate_f2.txt does not start with 'gate_f2 1 target=win64'"
  MAC_ZIP="azahar_lazpy_libretro-$AZTAG-lazpy.$REV-macos-arm64.zip"
  WIN_ZIP="azahar_lazpy_libretro-$AZTAG-lazpy.$REV-windows-x64.zip"
  SRC_ASSET="azahar-unified-source-$AZTAG-lazpy-nokeys.tar.xz"
  OSSL_ASSET="openssl-$OSV.tar.gz"
  SNAP_ASSET="citra_system_archives-f470e0c.tar.gz"
  OLD_BUILD="libazahar-py-core-build-$INHERIT.tar.gz"
  NEW_BUILD="libazahar-py-core-build-$TAG.tar.gz"
  SEVEN="$MAC_ZIP NOTICES.md $SRC_ASSET $OSSL_ASSET $SNAP_ASSET testapp.3dsx $OLD_BUILD"

  # 1: v1.0.0's SHA256SUMS against the pinned digest, then each of the seven assets against its line
  BASE="${LAZ_INHERIT_BASE:-https://github.com/GuyShtainer/libazahar-py/releases/download/$INHERIT}"
  INH="$OUT.inherit"
  if [ -z "${LAZ_INHERIT_BASE:-}" ]; then echo "note   inherited assets come from the live $INHERIT release page"; else echo "note   LAZ_INHERIT_BASE is set: a stand-in page, not the live release (a real run leaves it unset)"; fi
  # the test app's source: this tag's testapp/ folder only if it is unchanged since v1.0.0, else v1.0.0's
  git rev-parse -q --verify "refs/tags/$INHERIT" >/dev/null || die "tag $INHERIT is not in this clone (git fetch --tags)"
  if git diff --quiet "$INHERIT" HEAD -- testapp/; then APP_SRC_TAG=$TAG; else APP_SRC_TAG=$INHERIT; fi
  rm -rf "$OUT" "$INH"; mkdir -p "$OUT" "$INH"
  curl -fsSL --retry 2 -o "$INH/SHA256SUMS" "$BASE/SHA256SUMS" || die "download failed: $BASE/SHA256SUMS"
  [ "$(sha_of "$INH/SHA256SUMS")" = "$V1_0_0_SHA256SUMS" ] || die "v1.0.0's SHA256SUMS does not match V1_0_0_SHA256SUMS"
  echo "ok     v1.0.0 SHA256SUMS matches the pin"
  for name in $SEVEN; do
    _line=$(grep -c "^[0-9a-f]\{64\}  $name\$" "$INH/SHA256SUMS" || true)
    [ "$_line" -eq 1 ] || die "v1.0.0's SHA256SUMS has $_line line(s) for $name"
    _want=$(sed -n "s/^\([0-9a-f]\{64\}\)  $name\$/\1/p" "$INH/SHA256SUMS")
    curl -fsSL --retry 2 -o "$INH/$name" "$BASE/$name" || die "download failed: $BASE/$name"
    [ "$(sha_of "$INH/$name")" = "$_want" ] || die "$name does not match v1.0.0's SHA256SUMS line"
    echo "ok     $name"
  done
  # 2: five of them against the pins this repo already holds
  _nokeys=$(sed -n 's/^SRC_SHA256=//p' core/PIN-nokeys)
  [ "$(sha_of "$INH/$SRC_ASSET")" = "$_nokeys" ] || die "$SRC_ASSET does not match core/PIN-nokeys"
  _ossl=$(grep -A1 '^- Source:' core/OPENSSL.md | grep -o '[0-9a-f]\{64\}' | head -1)
  [ -n "$_ossl" ] && [ "$(sha_of "$INH/$OSSL_ASSET")" = "$_ossl" ] || die "$OSSL_ASSET does not match core/OPENSSL.md"
  [ "$(sha_of "$INH/$SNAP_ASSET")" = "$SNAP_SHA" ] || die "$SNAP_ASSET does not match this script's SNAP_SHA"
  [ "$(sha_of "$INH/NOTICES.md")" = "$(sha_of NOTICES.md)" ] || die "NOTICES.md does not match the repo's NOTICES.md"
  _fetch() { sed -n "s/^$1=//p" tools/fetch.sh | head -1; }
  [ "$(sha_of "$INH/$MAC_ZIP")" = "$(_fetch LAZPY_CORE_SHA)" ] || die "$MAC_ZIP does not match fetch.sh's LAZPY_CORE_SHA"
  [ "$(sha_of "$INH/testapp.3dsx")" = "$(_fetch TESTAPP_SHA)" ] || die "testapp.3dsx does not match fetch.sh's TESTAPP_SHA"
  echo "ok     five repo pins agree with the inherited bytes"
  for name in $SEVEN; do cp "$INH/$name" "$OUT/$name"; done

  # 3: the Windows zip
  STG="$OUT.stage"; rm -rf "$STG"; mkdir -p "$STG/zip"
  cp "$ART/azahar_lazpy_libretro.dll" "$STG/zip/azahar_lazpy_libretro.dll"
  cp "$ART/NOTICES-windows-x64.md" "$STG/zip/NOTICES.md"
  cp LICENSE "$STG/zip/LICENSE"
  tar -xOJf "$OUT/$SRC_ASSET" "$TOP/license.txt" > "$STG/zip/COPYING-azahar.txt"
  cp "$INPUTS" "$STG/zip/build.inputs"
  win_zip_source_md > "$STG/zip/SOURCE.md"
  for f in "$STG"/zip/*; do touch -t "$STAMP" "$f"; done
  (cd "$STG/zip" && zip -X -9 -q "$OUT/$WIN_ZIP" COPYING-azahar.txt LICENSE NOTICES.md SOURCE.md azahar_lazpy_libretro.dll build.inputs)
  cp "$ART/NOTICES-windows-x64.md" "$OUT/NOTICES-windows-x64.md"
  [ "$NO_RT" -eq 1 ] || cp "$ART/$RT" "$OUT/$RT"

  # 4: the build-files asset: git archive of exactly the paths in tools/build-files.txt
  # shellcheck disable=SC2046  # intentional split: one repo path per line, none with a space (CR stripped: a Windows checkout may add it)
  git archive --format=tar.gz --prefix=libazahar-py-core-build/ -o "$OUT/$NEW_BUILD" HEAD $(tr -d '\r' < tools/build-files.txt)

  # 5: SOURCE.md (all binaries) and SHA256SUMS
  top_source_md > "$OUT/SOURCE.md"
  _names=$(cd "$OUT" && ls | LC_ALL=C sort)
  # shellcheck disable=SC2086  # intentional split of the sorted asset names
  (cd "$OUT" && $SUM256 $_names > "$OUT.sums")
  mv "$OUT.sums" "$OUT/SHA256SUMS"
  rm -rf "$STG" "$INH"
  echo "staged $OUT:"
  (cd "$OUT" && ls -l | sed 's/^/  /')
  echo "SHA256SUMS sha256 $(sha_of "$OUT/SHA256SUMS")"
}

# the Windows zip's own SOURCE.md: the binary, its inputs, the pieces linked in
win_zip_source_md() {
  echo "# SOURCE"
  echo
  echo "What the binary is: \`azahar_lazpy_libretro.dll\`, Windows x64. Azahar $AZTAG (commit $(pin AZAHAR_COMMIT)) with libazahar-py's patches, built with OpenSSL $OSV linked statically, cross-compiled with mingw-w64 in a container whose image is pinned in \`build.inputs\`. Release tag: $TAG."
  echo
  echo "Built at repository commit $(inp head). \`build.inputs\` in this zip records the exact inputs: the container image, the cmake command, the OpenSSL source sha256 and the build script."
  echo
  echo "## Corresponding Source, all on the release page"
  echo
  echo "1. \`$SRC_ASSET\`: the Azahar source the binary was built from, plus the patches in \`$NEW_BUILD\`."
  echo "2. \`$OSSL_ASSET\`: OpenSSL's own tarball, the source of the statically linked OpenSSL."
  echo "3. \`$NEW_BUILD\`: the build script, the toolchain file, the CI workflow, the pins and the patches."
  if [ "$NO_RT" -eq 0 ]; then
    echo "4. \`$RT\`: the source of the compiler runtime parts linked in statically (libstdc++, libgcc, winpthreads and the mingw-w64 C runtime)."
  fi
  echo "5. This repository at the tag $TAG."
}

# the release's SOURCE.md: each binary and the assets that are its source
top_source_md() {
  echo "# SOURCE"
  echo
  echo "Release $TAG of libazahar-py. Each binary below is listed with the assets on this page that are its corresponding source. \`SHA256SUMS\` has the sha256 of every asset."
  echo
  echo "## \`$MAC_ZIP\` (macOS 15 or later, arm64)"
  echo
  echo "The macOS core is the build of release $INHERIT, unchanged: the same bytes. Source: \`$OLD_BUILD\` (the patches, pins, options and build script of that build), \`$SRC_ASSET\`, \`$OSSL_ASSET\` and \`$SNAP_ASSET\`. Its notices are \`NOTICES.md\`, which is also inside this zip."
  echo
  echo "## \`$WIN_ZIP\` (Windows, x64)"
  echo
  echo "Source: \`$NEW_BUILD\`, \`$SRC_ASSET\`, \`$OSSL_ASSET\`$([ "$NO_RT" -eq 1 ] || printf ' and `%s` (the source of libstdc++, libgcc, winpthreads and the mingw-w64 C runtime, which are linked in statically)' "$RT"). The zip's own \`SOURCE.md\` and \`build.inputs\` say how it was built. Its notices are \`NOTICES-windows-x64.md\`, which is also inside the zip as \`NOTICES.md\`. Do not use the macOS \`NOTICES.md\` for this zip."
  echo
  echo "## \`testapp.3dsx\`"
  echo
  echo "The same bytes as release $INHERIT. Source: the \`testapp/\` folder of this repository at the tag $APP_SRC_TAG."
  echo
  echo "## Notices"
  echo
  echo "\`NOTICES.md\` goes with the macOS zip (the same bytes as release $INHERIT). \`NOTICES-windows-x64.md\` goes with the Windows zip."
}

if [ -n "$INHERIT" ]; then win_release; exit 0; fi

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
    echo "Built at repository commit $(inp head) (translate older SHAs with \`docs/commit-map-g8.tsv\`, then docs/commit-map-g8b.tsv, then docs/commit-map-g8c.tsv)."
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
