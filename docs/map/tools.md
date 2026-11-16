# Scripts

- `tools/`: `mkprogress.py` (writes `docs/progress.html` and the lists in `docs/status/README.md`), `status_check.py`
  (items, handoff rows, hours rows), `mkmap.py` (writes `docs/map/gen/`), `map_check.py` (paths in docs exist, every
  top-level entry and script folder is mapped).
- `tools/check-obinary.sh`: every `open(` in `host/` must carry `O_BINARY` (0 on POSIX; Windows CRLF-translates without
  it); prints `check-obinary: ok N open() sites` or the offending lines and exits 1. Run by `make check` and
  `make test-host-win`.
- `tools/build-core.sh`: verifies (or fetches) the pinned Azahar tarball, unpacks it with `tools/untar_checked.py`,
  applies `core/patches/` with `--fuzz 0`, configures, and with `--build` or `--detach` builds
  `build-core/azahar_lazpy_libretro.dylib`. `tools/untar_checked.py` pre-scans a tar.xz, refuses unsafe members,
  then extracts with `filter="data"` (Python 3.12+).
- `tools/fetch.sh`: MoltenVK and headers (no flag), or the parts named (`--moltenvk --headers --lazpy-core --testapp`),
  sha256-pinned; our core and the test app come from the release (`LAZ_RELEASE_BASE` overrides its URL).
- `tools/mknotices.py`: writes `NOTICES.md` from the link line, the `.o.d` dependency files and the licence texts;
  exits 1 on an unknown path, component or notice.
- `tools/mkrelease.sh <tag>`: stages the release assets deterministically in `runs/release/<tag>/`.
- `tools/release_check.py <dir>`: the release's machine checks (`--skip-pins`, `--pre-push`, `--plant-red`).
- `tests/gate-a.sh <app.3dsx>`: step A's gate (8 checks in a temporary fresh copy; `KEEP=1` keeps it).
- `tests/gate-b.sh`: step B's gate (`RUNNER=fe2` default, or `RUNNER=azhost`); one PASS/FAIL line per check.
- `tests/gate_c.py`: step C's gate (scenarios a1, a2, b-f: frame-exact input, touch, circle pad, stops, raw shots,
  SD seeding; 28 checks); `tests/checks_c.py` its checkers, `tests/testapp_log.py` the test app's log parser.
- `tests/python/`: step D's pytest suite. Fast (no emulator): inputs, errors, the map, the worker client against
  `tests/python/fakeworker.py`, the ABI check. Slow (`slow` marker, needs the core and `build/testapp.3dsx`): C's
  checks through Python, crashes and stalls, the 200,000-frame batch, savestates and state boot (`runs/d-pytest/`,
  times in `runs/d-pytest/state-times.txt`). `conftest.py` has the fixtures (`host_paths`, `stock_core`,
  `lazpy_core`) and the core header line; `d_helpers.py` the shared boot and log helpers. Every crash test leaves a
  Python crash report in ~/Library/Logs/DiagnosticReports.
- `python/libazahar/`: the package: `emulator.py` (Emulator), the worker and its client, the ABI and map readers,
  paths, inputs, results, errors. `docs/USING.md` is the user guide.
- `tests/host/`: the pure host modules' unit tests, built by `make test-host`.
- `tests/check_testapp.py`: `markers`, `log` and `event` checks on the test app's output; exports
  `read_png_rgba(path)`, a filter-0 PNG decoder (import it with the absolute `tests/` path; `-I` drops the script
  folder from `sys.path`). Copied from Gen3D on 2026-11-12 (3DPlatinum's design).
- `tools/docs_check.py`: step H's gate over the docs: README numbers against their sources, the example and steps
  blocks, links, forbidden claims, the first paragraph; `--plant-red`, `--emit-steps`.
- `tools/clone_check.sh`: the fresh-clone check (clone, the README's steps and build blocks, the quickstart, the
  full pytest); `--dry-run` prints the steps.
