# A real scene with 1 to 4 instances at once (phase 6, step V3)

2026-11-13 18:11:27-18:17:03, main loop, on an Apple M3 Pro (12 cores: 6 performance, 6 efficiency; 18 GB) with macOS 15.8.1.
Our core is main's build 64026f4a… (Azahar 2126.2-lazpy.2); Azahar's own is the 2126.2 release core.

## Method

The scene is the one in `docs/research/real-scene-j.md`: Gen3D's flip dev build (homebrew; sha256 starts f2f80aee)
drawing its 3D world from a GBA game run locally (not distributed; the game, its save and Gen3D's world cache came
from a seed folder outside this repo), driven by Gen3D's own title keys and a left-right walk. Each instance boots,
runs 3600 frames (the 3D world draws from about frame 3000), and waits at a barrier; then all instances of a row
measure in one shared window of 60 s wall time (`run(..., wall_limit=60)`), walking on. `LAZ_MAX_INSTANCES=4`,
`nice` 10, the slot folder in use, one row at a time. The rows and the cap come from `cap_rule` and `md_core_table`
in `tools/speed_table.py`; the script stays in the session scratchpad (Gen3D's files are never copied here).

The check (`check_ok`) is a guest signal: Gen3D writes `perf.csv`, one row per guest second, whose first column is
the guest clock. The guest seconds that pass in the window, per wall second, must agree with host fps / 59.831
within 10 %, the last row at the window's start and end must show the 3D world ready (`world=6`, `top=0`), and the
batch must stop at its wall limit. The file reaches the SD card in chunks: at the window's start every instance's
last row was 32 guest seconds in, after 3600 frames (about 60 s). So a single window's rate is good to about 6 %
only. Gen3D's `voxel.log` flip lines were the plan's signal, but they appear only when the top screen changes (12
in step J's 36000 frames), too few for a rate. The last instance's start and end shots show the 3D world (the
script wrote every instance's shots to one place, so only the last pair was kept).

Quiet: the 1-minute load was under 6 from start to end. A sampler read `ps` every 10 s. One editor process (a code
indexer) used about one core for the whole run. In the two 1-instance rows, another Python process (not identified)
used about one core for 20-30 s of the window (ours 18:11:27-18:11:57, Azahar's own 18:12:43-18:13:33). The 2-, 3-
and 4-instance rows had nothing else. No other emulator and no build ran.

## Rows

| Core | n | Total host fps | Per-instance host fps | x real time | Peak RSS MB | Load start/end | Check |
|---|---|---|---|---|---|---|---|
| ours | 1 | 550.4 | 550.4 | 9.33 | 1078 | 3.1/4.8 | ok |
| Azahar's own | 1 | 533.6 | 533.6 | 8.80 | 1111 | 4.8/5.5 | ok |
| ours | 2 | 1057.9 | 528.2, 529.7 | 8.80, 8.80 | 805, 804 | 5.5/4.8 | ok |
| ours | 3 | 1586.4 | 528.9, 528.9, 528.6 | 8.80 each | 940, 927, 933 | 4.8/5.7 | ok |
| ours | 4 | 2071.4 | 517.6, 514.2, 520.0, 519.6 | 8.80, 8.53, 8.80, 8.80 | 952, 958, 956, 968 | 5.7/5.9 | ok |

x real time is guest seconds per wall second from `perf.csv`, so it shares the 6 % grain above. Our core's and
Azahar's own core's 1-instance rows agree with step J's quiet runs (536-571 fps).

## The cap

`cap_rule` on our core's rows: n=2 total fps x1.92 of n=1 and load 4.8, step up; n=3 x1.50 and load 5.7, step up;
n=4 x1.31 and load 5.9, step up. Every check is ok, so the default cap becomes 4 (`python/libazahar/_slots.py`),
from the light scene's provisional 2 (`docs/research/speed-table-e.md`). Four is the most the rule tests. Memory:
four fresh instances of this scene peak near 1 GB each; Gen3D measured 1.2-1.56 GB for an instance restored from a
state, so four restored instances need about 6 GB.
