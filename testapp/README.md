libazahar-py test app: a small 3DS homebrew (`build/testapp.3dsx`) that draws exact corner markers, logs one line per frame to `sdmc:/testapp/log.txt`, and obeys `sdmc:/testapp/control.txt`.
Licence: GPLv3 or later (our own code, glyphs and shader; nothing copied from the devkitPro examples).
Build: `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make -C testapp` (output `../build/testapp.3dsx`).
