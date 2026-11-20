#!/bin/sh
# mkhostnotices.sh: write NOTICES.md for the Windows host zip on standard output.
#
#   sh tools/mkhostnotices.sh [LICENSE_DIR]      LICENSE_DIR defaults to /mingw64/share/licenses (MSYS2 MINGW64)
#
# The Windows host (libazhost.dll, azhost.exe) is linked with -static -static-libgcc (Makefile, WIN_LDFLAGS), so these
# parts of other projects are inside the two files: zlib (-lz), winpthreads (host/ uses pthreads), the mingw-w64 C
# runtime and libgcc. Their licence texts are copied verbatim from the MSYS2 packages that were linked, which is why the
# build runs this on the build machine. The macOS host links nothing statically (system libraries only), so its zip
# has no NOTICES.md. Output has no dates. Exits 1 naming any text that is missing.
set -eu
D=${1:-/mingw64/share/licenses}
need() { [ -f "$D/$1" ] || { echo "mkhostnotices: missing $D/$1" >&2; exit 1; }; }
need zlib/LICENSE; need winpthreads/COPYING; need crt/COPYING; need crt/COPYING.MinGW-w64-runtime.txt; need libgcc/COPYING.RUNTIME
section() {  # section TITLE FILE: a heading and the file verbatim, in a fence
  printf '### %s\n\n```text\n' "$1"; cat "$D/$2"; printf '\n```\n\n'
}
cat <<'HEAD'
# Third-party notices: the Windows host

`libazhost.dll` and `azhost.exe` are built with mingw-w64 (MSYS2 MINGW64) and linked statically (`-static
-static-libgcc`). These parts of other projects are therefore inside the two files. Every text below is verbatim from
the MSYS2 package that was linked. The host's own licence is the GPLv3 text in `LICENSE`.

- zlib (the zlib licence)
- winpthreads (MIT-style; the host uses POSIX threads)
- the mingw-w64 C runtime (public domain and permissive licences; see the files below)
- libgcc, the GCC runtime library (GPLv3 with the GCC Runtime Library Exception; the GPLv3 text is `LICENSE`, the
  exception follows)

The libretro and Vulkan headers the host is compiled against are fetched by `tools/fetch.sh --headers` and are not
shipped in this zip.

HEAD
section "zlib" zlib/LICENSE
section "winpthreads" winpthreads/COPYING
section "mingw-w64 C runtime: COPYING" crt/COPYING
section "mingw-w64 C runtime: COPYING.MinGW-w64-runtime.txt" crt/COPYING.MinGW-w64-runtime.txt
section "libgcc: GCC Runtime Library Exception" libgcc/COPYING.RUNTIME
