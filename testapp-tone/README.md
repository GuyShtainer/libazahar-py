libazahar-py tone test app: a small 3DS homebrew (`build/testapp-tone.3dsx`) that plays a 440 Hz sine, stereo, through the
system sound library from guest frame 60, and logs once a second to `sdmc:/tone/log.txt`.
Licence: GPLv3 or later (our own code; nothing copied from the devkitPro examples).
Build: `PATH=/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH make -C testapp-tone` (output `../build/testapp-tone.3dsx`).
The app's audio library looks for a component file on the SD card; the tests seed a made-up one
(`tests/python/dsp_component.py`), which Azahar's high-level DSP ignores apart from logging its hash. Without it the audio library fails to start and no audio is produced. Driven by `tests/python/test_audio_live.py`.
