# Top-level folders and files

- `prototype/`: the spike's one-file C host (`prototype/fe2.c`), reference only; see `prototype/README.md`.
- `host/`: the C host library `libazhost.dylib` (the `azh_*` API in `host/azhost.h`) and the `azhost` CLI
  (`host/azhost_main.c`); the pure parts are `host/version.c`, `host/crop.c`, `host/png.c` (prototypes in
  `host/azh_pure.h`); `host/options-default.txt` is the 32-key option profile.
- `Makefile` (top level): builds the host; `make check` runs the clang analyzer, `make test-version` the version
  test, `make testapp` delegates to `testapp/`.
- `testapp/`: the 3DS test app (libctru, GPLv3): corner markers, per-frame log, `control.txt` events, 2D/3D, busy
  boot; builds `build/testapp.3dsx`; `testapp/README.md`.
- `core/`: our patched Azahar libretro core: `core/PIN` (the pinned 2126.2 source), `core/patches/` 0000-0006
  (notices, memory exports, repeatable-run options, retro_run returns on error, log filter, version suffix,
  movie play), `core/options-lazpy.txt`, `core/README.md`.
- `tests/`: step gates and checkers (see `docs/map/tools.md`); `tests/test_version.c` is the host test of the
  version rule.
- `python/`: the Python package `python/libazahar/` (installed editable through `pyproject.toml`); `docs/USING.md` is
  its user guide.
- `docs/`: status folders, maps, research, the plan (once written), `docs/hours.tsv`, the generated
  `docs/progress.html`.
- `tools/`: the status and map scripts (see `docs/map/tools.md`).
- `README.md` (public, honest status), `LICENSE` (GPLv3), `CLAUDE.md` (agent guide), `.gitignore`,
  `pyproject.toml` (the editable install).
- Ignored, never committed: `dl/` (the downloaded Azahar libretro core and MoltenVK), `vendor/` (libretro and Vulkan
  headers), `runs/`, `.pytest_cache/`, `.venv/` (the editable-install venv), `roms/`, `sdmc/`, `build/` (host and
  test app output), `build-core/` (our core's build: `build.log`, `build.pid`, `build.exit`,
  `azahar_lazpy_libretro.dylib`).
- `NOTICES.md`: generated licence notices (`tools/mknotices.py`); also inside the core's release zip.
- `core/PIN-nokeys`: the pin of the source asset (Azahar's tarball minus the drop list); `core/OPENSSL.md`: where
  the statically linked OpenSSL came from and how to rebuild it.
- `docs/release-notes/`: the release notes per tag.
- `tests/python/test_paths.py`: the default core path and the `LAZ_STOCK_CORE` skips.
