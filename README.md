# libazahar-py

Run the [Azahar](https://github.com/azahar-emu/azahar) 3DS emulator with **no window**, as fast as the machine allows,
several copies at once, and drive it from scripts: press buttons and touch, take screenshots, read guest memory. The
aim is automated testing of 3DS homebrew, the way [libmgba-py](https://github.com/hanzi/libmgba-py) makes this easy
for GBA.

**Status: not usable yet.** A one-file C prototype (`prototype/fe2.c`) loads the Azahar libretro core on macOS arm64,
renders through Vulkan (MoltenVK) with no window, and saves PNG screenshots of both screens. On an idle homebrew menu
it ran at about 50x real time (a ceiling, not checked on a 3D scene yet). Input, memory reads and the Python layer are
not built. The plan is being written.

How it works: Azahar ships a libretro core. This project is the small program that hosts that core without a display
(answering its Vulkan setup and copying each frame back to memory), plus a Python layer on top. The core and MoltenVK
are downloaded by a script, never shipped here.

License: GPLv3 (see `LICENSE`). Azahar is GPLv2-or-later; MoltenVK is Apache-2.0; the libretro headers are MIT.
No ROMs, game data, system files or keys are included or will be.
