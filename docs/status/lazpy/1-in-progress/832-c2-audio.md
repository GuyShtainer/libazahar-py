---
id: laz-832
title: lazpy
order: 832
kind: step
parent: laz-830
page: Phase C: audio capture into RunResult, with a tone app of our own
hours: -
---
# C2: audio capture

## What it is
Phase C: audio capture into RunResult, with a tone app of our own.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase C review passed.

## Evidence
2026-11-19 02:26: lane hostav merged on main (f71627a): run(audio=True), host ABI 5, testapp-tone/. On the PC: test_audio_live.py 2 passed (FFT peak 440 Hz within 2 %, silence before frame 60, no-component silence with the app's init failure logged), make test-host 307983 checks 0 failed, fast suite 302 passed. Not run: make check (clang analyze; no clang on the PC, CI's macOS job). Waits on the phase C gate and review.

## Pointers
- Plan row: `docs/plans/phase-8.md:187`
- Briefs: `docs/plans/phase-8c-briefs.md`

## Lessons and notes
Read this part only when you work on this item.
- The sample count: 240 frames gave 130400 stereo frames, about 884 short of 240 * rate / 59.83. The sound starts about 1.6
guest frames after the app's start call; the steady rate is 59.83 fps. The test allows 3 frames short, 1 frame over.
