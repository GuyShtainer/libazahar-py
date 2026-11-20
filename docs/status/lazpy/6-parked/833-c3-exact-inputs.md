---
id: laz-833
title: lazpy
order: 833
kind: step
parent: laz-830
page: Phase C: exact-frame inputs from boot through the core movie hook
hours: -
---
# C3: exact inputs

## What it is
Phase C: exact-frame inputs from boot through the core movie hook.

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane; the lane merged on main; the phase C review passed.

## Evidence
2026-11-19 02:26: stopped by lane hostav: the core's movie playback needs a patch first (notes). The host call azh_movie_play and the worker's movie argument are in ABI 5 but never ran live; no exact_inputs option yet. Parked for the next core phase (after phase 8): the plan keeps C6a to one CI rebuild of the same patches.

## Pointers
- Plan row: `docs/plans/phase-8.md:188`
- Briefs: `docs/plans/phase-8c-briefs.md`

## Lessons and notes
Read this part only when you work on this item.
- 2026-11-19, lane hostav (stopped C3, a core change is needed):

Plan: `run(..., exact_inputs=True)` from boot, writing an Azahar `.ctm` movie and playing it with the core's
`lazpy_movie_play(path)` (core patch 0006; call it after `retro_load_game` and before the render `context_reset`;
returns 0 ok, -2 file missing, -3 null path, -4 not a movie, -5 already booted).

Why it cannot work with the core as it is:
- A `.ctm` file is a 256-byte header ("CTM\x1B", program id, revision, clock init time, id, author, rerecord count,
  input count, timing base ticks) followed by one byte stream of 7-byte records. Each record has a type byte (pad and
  circle, touch, accelerometer, gyroscope, IR_RST, extra HID response).
- Playback reads the stream in order, one record per callback. A type mismatch is logged as an error but the 7 bytes are
  still consumed, so the stream desyncs from then on.
- The HID pad callback (about 234 Hz) consumes a pad record then a touch record. The IR_RST callback (ZL, ZR, C-stick) is a
  separate timer that the guest starts at a time and a period of its own choosing. Accelerometer and gyroscope records
  exist only if the app enables them.
- So where the IR_RST records sit in the stream depends on when the app initialises that service, which Python cannot
  know. The test app uses ZL/ZR, so the planned live test (buttons, ZL/ZR, circle pad, touch; 30 changes each, 3
  repeats, offsets m = 0, 1, 1, 2) cannot pass.

Fix needed (a new core patch, in the next core phase after phase 8; the plan keeps C6a to one CI rebuild): make `Movie::Play` take the next record of its own type (type skipping), or keep
one cursor per record type. Then add `exact_inputs` to `Emulator` and a live test, test_exact_inputs_live.py (still to write).

State in the tree: the host call `azh_movie_play` and the worker's optional movie argument (`args[8]` of `_op_start`)
are in ABI 5. They compile but have never run live, and `Emulator` does not reach them. No `exact_inputs` option and no
live test were added; USING section 4 says the option does not exist.

Source files read (Azahar commit 219d743a; the scratch copies are gone, fetch them again at that commit): `movie.cpp`, `movie.h`, `hid.cpp`, `ir_rst.cpp`,
`extra_hid.cpp`. The last three were needed because the record interleaving cannot be read from the movie files alone.
- 2026-11-19 02:45: the movie call is out of the host again (review finding 1; lane fav). Its code (host/movie.c,
azh_movie_play, the worker's movie argument) is in commit 1ad80b8 on branch p8-hostav: bring it back with the core
patch, in one ABI bump.
