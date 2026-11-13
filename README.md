# libazahar-py

A headless host for Azahar's 3DS libretro core on macOS arm64, plus a Python layer: no window, several copies at
once, buttons and touch, screenshots, savestates, and guest memory on our own core. It is for automated tests of 3DS
homebrew, and it is named after libmgba-py.
Unofficial: not affiliated with or endorsed by the Azahar project. Report libazahar-py issues here, not to Azahar.

## Status

v0.1.0, an early prerelease. It runs 3DS homebrew headless, with inputs, shots, SD files, savestates, many instances
at once and guest memory reads on our core; `STATUS.md` lists each item with the work that proved it. What does not
work: macOS before 15 and Intel Macs, audio output, anything with a window, and anything that is not homebrew.

## Measured numbers

| What | Value | Scene | Load | Date | Source |
|---|---|---|---|---|---|
| Our core, 1 instance | 36.39x real time (2177.4 fps) | test app, light scene | 10.9/9.4 | 2026-11-13 | docs/research/speed-table-e.md:27,3 |
| Our core, 3 instances, each | 19.71x, 19.76x, 19.70x real time (1179.4, 1182.0, 1178.5 fps) | test app, light scene | 15.1/14.5 | 2026-11-13 | docs/research/speed-table-e.md:29,3 |
| Our core, 3 instances, peak memory each | 787, 807, 781 MB | test app, light scene | 15.1/14.5 | 2026-11-13 | docs/research/speed-table-e.md:29,3 |
| Our core, host share of a batch without shots | 0.1% | test app, light scene | 10.9/9.4 | 2026-11-13 | docs/research/speed-table-e.md:27,3 |
| Azahar's own core, 1 instance | 27.61x real time (1652.2 fps) | test app, light scene | 16.6/32.8 | 2026-11-13 | docs/research/speed-table-e.md:36,3 |
| Azahar's own core, 3 instances, each | 15.48x real time (926.1, 926.3, 926.1 fps) | test app, light scene | 35.9/36.3 | 2026-11-13 | docs/research/speed-table-e.md:38,3 |
| Azahar's own core, real scene, 1 instance | 334 fps, 5.6x real time | one commercial game's 3D field scene, run locally | 26.7 (16:07) | 2026-11-12 | docs/research/spike-2-real-scene.md:32,1 |
| Azahar's own core, real scene, 1 instance, busy machine | 129 fps, 2.2x real time | one commercial game's 3D field scene, run locally | 68-96 (16:09-16:11) | 2026-11-12 | docs/research/spike-2-real-scene.md:34,1 |
| Azahar's own core, real scene, 3 instances, each | 136-138 fps, 2.3x real time | one commercial game's 3D field scene, run locally | 58 rising to 90 | 2026-11-12 | docs/research/spike-2-real-scene.md:35,1 |

Speed depends on the scene and the machine's load; the light rows are the test app, the real-scene rows are one
commercial game's scene run locally on a busy machine. Load is the 1-minute load average (at the start and the end of
a light row). The real-scene rows are not a clean measure: a re-measure on a quiet machine is still owed. Azahar's
own core ran while the machine was busier.

## Requirements

macOS 15 or later on Apple silicon; Xcode command-line tools; Python 3.10 or newer (python.org or Homebrew; macOS's
own `python3` is 3.9); `curl`, `shasum` and `unzip` (stock). devkitARM is needed only to build the test app yourself.

## Install

1. `git clone https://github.com/GuyShtainer/libazahar-py && cd libazahar-py`
2. Run these commands from the repository folder:

<!-- docs_check: steps -->
```sh
sh tools/fetch.sh --moltenvk --headers --lazpy-core --testapp   # MoltenVK, headers, our core, the test app (sha256-pinned)
make                                                            # build/libazhost.dylib and build/azhost
python3 -m venv .venv && .venv/bin/pip install -e .             # the Python layer (editable install only)
.venv/bin/python examples/quickstart.py                         # prints "quickstart ok" (on our core, the default)
```

Build the test app yourself, instead of `--testapp` (needs devkitPro):

<!-- docs_check: steps-build -->
```sh
DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make testapp   # build/testapp.3dsx
```

## Example

<!-- docs_check: quickstart -->
```python
"""Boot the test app, hold A, take a shot, check what happened. Run from the repo root: python examples/quickstart.py"""
import shutil
import struct
import sys
from pathlib import Path

from libazahar import Buttons, Emulator

app = sys.argv[1] if len(sys.argv) > 1 else "build/testapp.3dsx"
work = Path("runs/quickstart")
shutil.rmtree(work, ignore_errors=True)
with Emulator(app, work) as emu:
    result = emu.run(300, inputs=[(150, Buttons.A)], shots=[300])      # A is held from batch frame 150 on
    log = (emu.sd / "testapp/log.txt").read_text().splitlines()
shot = result.shots[300]
sizes = [struct.unpack(">II", Path(p).read_bytes()[16:24]) for p in (shot.top, shot.bottom)]
keys = [int(w[2:], 16) for line in log if line.startswith("f=") for w in line.split() if w.startswith("k=")]
if result.frames != 300 or result.stopped_by != "frames":
    sys.exit(f"quickstart failed: ran {result.frames} frames, stopped by {result.stopped_by}")
if sizes != [(400, 240), (320, 240)]:
    sys.exit(f"quickstart failed: screen sizes {sizes}")
if not keys or keys[0] & 1 or not keys[-1] & 1:
    sys.exit("quickstart failed: A is not in the app's log after the press")
print("quickstart ok")
```

## Two cores

| | Our core | Azahar's own core |
|---|---|---|
| Where it comes from | our release (`sh tools/fetch.sh --lazpy-core`), or `tools/build-core.sh` | Azahar's releases page, by hand, for comparisons |
| Input, shots, SD files, savestates | yes (laz-220, laz-320) | yes (laz-220) |
| Guest memory reads and writes, the watch list | yes (laz-330) | no: `NeedsLazpyCore` |
| Debug-text stop | yes (laz-320) | no: `NeedsLazpyCore` |
| Exact repeats | yes (laz-320) | no: repeats are not exact |
| Poll-exact movies | not tested | no |

The library uses `LAZ_CORE` if set, else `dl/lazpy-core/azahar_lazpy_libretro.dylib` (where `fetch.sh --lazpy-core`
puts our core). After building it yourself, set `LAZ_CORE=build-core/azahar_lazpy_libretro.dylib`. Details are in
`docs/USING.md`.

## Docs

- [STATUS.md](STATUS.md): what works, what does not, what was dropped
- [docs/USING.md](docs/USING.md): the Python guide
- [docs/HOST-API.md](docs/HOST-API.md): the C library and the `azhost` command
- [examples/README.md](examples/README.md): three runnable examples
- [core/README.md](core/README.md): our patched core, its patches and its build
- [NOTICES.md](NOTICES.md): every component in the core

## Licence and credits

libazahar-py is GPLv3 (`LICENSE`). Azahar (GPLv2 or later) is by the Azahar and Citra teams. Our patched core binary is
distributed under GPLv3, with its complete source on the release page. MoltenVK (Apache-2.0) is downloaded by
`fetch.sh` from its upstream, never included; the libretro headers are MIT. `NOTICES.md` lists every component in the
core. The idea and the name come from libmgba-py.

## Legal

Homebrew only. This repository and its releases contain no ROMs, game data, system files, NAND data, keys or encrypted
titles. Our core is built without Azahar's built-in key data and default HTTP client certificate, and it loads no keys.
Nintendo 3DS is a trademark of Nintendo; this project is not affiliated with or endorsed by Nintendo or by the Azahar
project.
