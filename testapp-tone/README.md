libazahar-py tone test app: a small 3DS homebrew (`build/testapp-tone.3dsx`) that plays a stereo sine through the
system sound library from guest frame 60: 440 Hz at amplitude 12000 on the left, 660 Hz at amplitude 6000 on the right
(different on each side, so a swapped or duplicated channel shows). It logs once a second to `sdmc:/tone/log.txt`.
Licence: GPLv3 or later (our own code; nothing copied from the devkitPro examples).
Build: built and tested with devkitARM r67.1 (`DEVKITPRO=/c/devkitPro-r67.1` on the PC):
`PATH=/c/devkitPro-r67.1/devkitARM/bin:/c/devkitPro-r67.1/tools/bin:$PATH DEVKITPRO=/c/devkitPro-r67.1 DEVKITARM=/c/devkitPro-r67.1/devkitARM make -C testapp-tone`
(output `../build/testapp-tone.3dsx`). Any devkitARM works, but the tested binary came from r67.1.
The app's audio library looks for a component file on the SD card; the tests seed a made-up one
(`tests/python/dsp_component.py`), which Azahar's high-level DSP ignores apart from logging its hash.
`test_no_component_file_gives_silence` in `tests/python/test_audio_live.py` shows what happens without it. Driven by
`tests/python/test_audio_live.py`.
