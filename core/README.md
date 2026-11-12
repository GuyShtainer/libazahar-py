# core/: our patched Azahar libretro core

libazahar-py runs Nintendo 3DS software headlessly through a libretro core. The stock Azahar core does not expose
guest memory, repeatable-run options or a movie hook, so we build the pinned stock source plus a short patch stack
into our own `azahar_lazpy_libretro.dylib`.

## Pin

`core/PIN` (plain `KEY=value` lines, read with `sed`, never sourced): Azahar tag 2126.2, commit
`219d743a1e698101fe1ab8bef43e6563126c3c27`, the unified source tarball URL, its size and sha256, and `LAZPY_REV=1`.
The tarball is verified (size and sha256) before anything is unpacked; a present file that fails is refused and kept.

## Patches (`core/patches/`, applied in name order with `patch -p1 --fuzz 0`; each assumes the ones before it)

| Patch | What it does |
|---|---|
| `0000-lazpy-notices.patch` | one "Modified by libazahar-py" notice per touched file |
| `0001-lazpy-memory-exports.patch` | `lazpy_read_memory` / `lazpy_write_memory` by guest virtual address, every page checked |
| `0002-lazpy-options.patch` | six core options: deterministic async operations, async FS operations, instant debug log, init clock, init time, init ticks type (defaults equal stock) |
| `0003-lazpy-run-returns-on-error.patch` | `retro_run` returns after a fatal-error message instead of looping |
| `0004-lazpy-log-filter.patch` | log level Info, with the emulated program's debug output (`Debug_Emulated`) at Debug |
| `0005-lazpy-version.patch` | library version string gets the suffix `-lazpy.1` |
| `0006-lazpy-movie-play.patch` | `lazpy_movie_play(path)` plays a `.ctm` movie from the next boot |
| `0007-lazpy-no-default-clcert.patch` | the HTTP service no longer falls back to a built-in ClCertA certificate and key; a missing console file is an error |
| `0008-lazpy-no-key-loading.patch` | `GetKeysStream()` returns an empty stream: no AES keys are ever loaded (no `aes_keys.txt`, no built-in blob) |

## What the core never contains

No console keys and no Nintendo certificate. `tools/build-core.sh` deletes the files on the pin's `LAZ_CORE_DROP`
list (`default_keys.h`, `ctr-common-1-cert.h`, `ctr-common-1-key.h`) right after the unpack, configures with
`-DENABLE_BUILTIN_KEYBLOB=OFF`, and after the compile fails if any object still read a dropped file. Build paths are
stripped with `-ffile-prefix-map`. Homebrew needs none of these.

## OpenSSL

Azahar bundles LibreSSL for its HTTP client. We link a static OpenSSL of the pinned version instead
(`OPENSSL_VERSION` and `OPENSSL_ROOT` in the pin; Homebrew's `openssl@3` by default, `LAZ_OPENSSL_ROOT` overrides).
The script refuses another version, checks that configure picked the static `.a` files, and fails if the core links
an SSL dylib or still carries LibreSSL. `build-core/build.inputs` records the tarball, pin, script, every patch, the
drop list, the OpenSSL archives (sha256 each), the repo head and whether the tree was clean.

`core/options-lazpy.txt` holds the option lines our core's runs add on top of the default profile.

## Licenses

Azahar is GPLv2 or later. Every patch hunk is GPLv2 or later, as the file it patches. Any published binary of this
core ships with the unchanged source tarball plus these patches. OpenSSL 3 is Apache-2.0, which is compatible with GPLv3 but
not GPLv2, so a published binary of this core is distributed under GPLv3 (Azahar's "or later" allows it).

## Build

```
nice -n 10 tools/build-core.sh --configure-only   # fetch/verify, unpack, patch, configure; no compile
nice -n 10 tools/build-core.sh --detach           # compile in its own session; see the script header
```

The result is `build-core/azahar_lazpy_libretro.dylib`. `build-core/` and `dl/` are git-ignored.
