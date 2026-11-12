# Commands

Checks (before every commit):
```
python3 -I tools/mkmap.py && python3 -I tools/mkprogress.py && python3 -I tools/status_check.py --strict-handoff && python3 -I tools/map_check.py
```

Build and gate the host and the test app (devkitARM first in PATH for the 3DS build):
```
make check && make && make test-version          # build/libazhost.dylib, build/azhost, the version test
PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp   # build/testapp.3dsx
tests/gate-a.sh build/testapp.3dsx               # step A's gate
RUNNER=azhost tests/gate-b.sh                    # step B's gate through azhost (default runner: fe2)
build/azhost run <app.3dsx> --sys runs/x/sys --out runs/x/out --frames 600 --shot 300,600
```

Our patched core (detached, nice'd; `--configure-only` stops after the patches and configure):
```
nice -n 10 tools/build-core.sh --detach         # build-core/azahar_lazpy_libretro.dylib, build-core/build.exit
```

Build the spike's prototype (from the repo root; headers in `vendor/`, ignored):
```
mkdir -p build && cc -O2 -I vendor -I vendor/include -o build/fe2 prototype/fe2.c -framework OpenGL -lz
```

Fetch first: `tools/fetch.sh` (core, MoltenVK, headers; sha256-checked). Run it (any core option as `OPT_<key>=value`):
```
MVK_LIB=dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib OPT_citra_graphics_api=Vulkan \
  build/fe2 dl/azahar/azahar_libretro.dylib <app.3dsx> <sysdir> <outdir> <seconds> <shot frames, comma list>
```
The core's SD folder is `<sysdir>/Azahar/sdmc/`. The downloads' URLs and sha256: `docs/research/spike-1-headless-core.md`.
