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

`core/options-lazpy.txt` holds the option lines our core's runs add on top of the default profile.

## Licenses

Azahar is GPLv2 or later. Every patch hunk is GPLv2 or later, as the file it patches. Any published binary of this
core ships with the unchanged source tarball plus these patches.

## Build

```
nice -n 10 tools/build-core.sh --configure-only   # fetch/verify, unpack, patch, configure; no compile
nice -n 10 tools/build-core.sh --detach           # compile in its own session; see the script header
```

The result is `build-core/azahar_lazpy_libretro.dylib`. `build-core/` and `dl/` are git-ignored.
