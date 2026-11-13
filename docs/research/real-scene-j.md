# A real scene on our core and on Azahar's own core (step J), 2026-11-13

Main loop, 09:03-09:26. The first real scene on our core: Gen3D's phase-2 flip dev build (homebrew; its sha256
starts f2f80aeeb47f912f) drawing its 3D world from a GBA game supplied locally (not distributed; the game, its save and
Gen3D's world cache came from a seed folder outside this repo). The script is Gen3D's own try-1 soak
(LAZPY-TRY-1.md in Gen3D's repo), unchanged keys: one `run(1)`, then one `run(35999)` with the title-screen button presses and a
left-right walk on the field; the 3D world draws from about frame 3000 to the end. One copy at a time, `nice -n 10`,
never overlapping, a fresh workdir each run, run from a scratch folder outside both repos. After the batch the script
reads 16 bytes of the app's code at 0x00100000 and times 200 reads of 4 KiB there.

Cores: ours is build-core/azahar_lazpy_libretro.dylib (Azahar 2126.2-lazpy.1); Azahar's own is the 2126.2 release
core (LAZ_STOCK_CORE route). Profiles: "default" is our core with core/options-lazpy.txt (deterministic async
operations on, a fixed clock); "none" is our core with LAZ_LAZPY_PROFILE=none (the stock defaults); "no det" is the
default with deterministic async operations off. Load is the 1-minute average before and after the batch.

## Quiet runs (1-minute load under 6 from start to end)

| Run | Core and profile | Start | Load before/after | fps | x real time | Wall s | Peak RSS MB | Memory |
|---|---|---|---|---|---|---|---|---|
| stock-b | Azahar's own | 09:16:35 | 4.65/3.87 | 564.2 | 9.43 | 63.81 | 880.0 | NeedsLazpyCore |
| stock-c | Azahar's own | 09:19:52 | 4.24/4.37 | 541.7 | 9.05 | 66.45 | 1222.8 | NeedsLazpyCore |
| ours-b | ours, default | 09:23:28 | 3.85/4.43 | 561.4 | 9.38 | 64.12 | 1013.6 | 0.024 ms per 4 KiB |
| none-b | ours, none | 09:17:40 | 3.87/4.22 | 536.2 | 8.96 | 67.14 | 1135.4 | 0.017 ms per 4 KiB |
| none-c | ours, none | 09:20:59 | 4.37/4.42 | 542.4 | 9.07 | 66.36 | 1412.3 | 0.02 ms per 4 KiB |
| nodet-b | ours, no det | 09:18:48 | 4.22/4.24 | 571.1 | 9.54 | 63.04 | 1193.8 | 0.019 ms per 4 KiB |
| nodet-c | ours, no det | 09:22:06 | 4.42/4.17 | 563.7 | 9.42 | 63.86 | 1135.9 | 0.021 ms per 4 KiB |

Every quiet run is 536-571 fps (9.0-9.5x real time): our core matches Azahar's own core on this scene, and our
option lines (exact repeats) cost nothing measurable here. On our core every run read the app's code (spike 2 could
not reach app memory at all on Azahar's own core); 4 KiB takes about 0.02 ms.

## Runs where the load moved (not used for numbers)

| Run | Core and profile | Start | Load before/after | fps |
|---|---|---|---|---|
| ours | ours, default | 09:03:33 | 8.20/10.75 | 400.3 |
| stock | Azahar's own | 09:05:35 | 8.44/6.23 | 534.6 |
| ours2 | ours, default | 09:06:43 | 6.23/11.99 | 395.1 |
| none | ours, none | 09:13:00 | 8.42/10.24 | 446.1 |
| nodet | ours, no det | 09:14:52 | 9.33/5.95 | 568.7 |
| ours-c | ours, default | 09:24:44 | 4.03/16.65 | 344.8 |

The first three alone suggested our core was 25% slower; the interleaved quiet repeats show that was other
sessions' load arriving mid-run (every slow run ends at a higher load than it started). Lesson: the quiet gate must
hold at the end of a run too, and a two-core comparison needs interleaved repeats.

Against Gen3D's try 1 (Azahar's own core, 222.6 fps at load 13 rising to 38): the same scene runs about 2.5x faster
on a quiet machine. The windowed Azahar comparison (Gen3D's SPEED.md: a visible window caps near 1x; its fast
curtain gives 4-5x on the 2D overworld) was not re-measured here (no windows while Guy works).
