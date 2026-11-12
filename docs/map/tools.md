# Scripts

- `tools/`: `mkprogress.py` (writes `docs/progress.html` and the lists in `docs/status/README.md`), `status_check.py`
  (items, handoff rows, hours rows), `mkmap.py` (writes `docs/map/gen/`), `map_check.py` (paths in docs exist, every
  top-level entry and script folder is mapped).
- `tools/build-core.sh`: verifies (or fetches) the pinned Azahar tarball, unpacks it with `tools/untar_checked.py`,
  applies `core/patches/` with `--fuzz 0`, configures, and with `--build` or `--detach` builds
  `build-core/azahar_lazpy_libretro.dylib`. `tools/untar_checked.py` pre-scans a tar.xz, refuses unsafe members,
  then extracts with `filter="data"` (Python 3.12+).
- `tools/fetch.sh`: the stock core, MoltenVK and headers into `dl/`, sha256-pinned.
- `tests/gate-a.sh <app.3dsx>`: step A's gate (8 checks in a temporary fresh copy; `KEEP=1` keeps it).
- `tests/gate-b.sh`: step B's gate (`RUNNER=fe2` default, or `RUNNER=azhost`); one PASS/FAIL line per check.
- `tests/check_testapp.py`: `markers`, `log` and `event` checks on the test app's output; exports
  `read_png_rgba(path)`, a filter-0 PNG decoder (import it with the absolute `tests/` path; `-I` drops the script
  folder from `sys.path`). Copied from Gen3D on 2026-11-12 (3DPlatinum's design).
