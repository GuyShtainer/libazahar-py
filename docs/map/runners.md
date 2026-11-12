# Commands

Checks (before every commit):
```
python3 -I tools/mkmap.py && python3 -I tools/mkprogress.py && python3 -I tools/status_check.py --strict-handoff && python3 -I tools/map_check.py
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
