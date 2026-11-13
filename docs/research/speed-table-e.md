# Speed table, step E (light scene)

Date: 2026-11-13. Commit: step-e at 8c06e26 plus the uncommitted E2 edits (`_slots.py` DEFAULT_CAP, `test_pool_live.py`; the E2 commit sha is the one that adds this file). Mac: 12 cores, 18 GB. Cores: our patched core
(`build-core/azahar_lazpy_libretro.dylib`, core version 2126.2-lazpy.1, step 0 build, cap core) and the stock core (`dl/azahar/azahar_libretro.dylib`, core version 2126.2, 4-instance row skipped by rule).
Test app, draw=3d, 60 s wall_limit batch after 300 warm-up frames; workers run at nice 15 because the table process itself ran at nice 15 (its launch shell was already at nice 5) and a worker keeps a parent's nice when above 10 (H2); under a plain `nice -n 10` it is 10, as g4 measures.
Test-app numbers are a light scene (rules.md 7); spike 2's real 3D-field numbers are in spike-2-real-scene.md. No speed claim beyond the table.

Guest-time check (ticks per vblank within 1 % of 4,481,136; x_real within 2 % of host fps / 59.831): passed on every row (all `ok`).
Host share of the shot-free batches: 0.0-0.1 % on every row (PLAN target under 5 %): met.
Load: the 1-minute load was 9-17 for the lazpy rows; the stock rows ran at load 16-37 (the load rose to 32-36 during the stock-core rows: the table's own copies plus other sessions; not waited for, the stock core is not the cap core). The stock rows are therefore less clean than the lazpy rows.

Cap rule (fixed before any run, Guy Q3 2026-11-12): use the cap core's rows only. T(n) = total host fps at n, L(n) = 1-minute load at the end of the n row,
C = os.cpu_count() = 12. Any cap-core CHECK FAIL: the table is not used and the cap stays 3. Else start at cap 1 and for n = 2, 3, 4 in order step up to n only if
T(n) >= 1.25 x T(n-1) and L(n) < 2 x C; stop at the first n that fails. Marked provisional (light scene).
Numbers: T = 2177.4, 3167.4 (x1.45, L 15.1: step up), 3539.9 (x1.12 < 1.25: stop), 3434.3. Result: **cap 2**. `_slots.DEFAULT_CAP = 2`.

Round trip (1 instance, our core): run(1) x 600 = 1.069 ms per frame, run(600) = 0.955 ms per frame, difference 0.114 ms per call.
Shots (20 each, fresh Emulator per level): level 1: 6.21 ms per shot, top PNG 3930 bytes, host.log `png level=1`; level 6: 5.76 ms per shot, 1882 bytes, `png level=6`.
PNG level 1 was not faster than level 6 on this scene (6.21 vs 5.76 ms per shot, 3930 vs 1882 bytes); PLAN's level-1 win is not shown by the test app's tiny PNGs; no tuning.

# Speed table (light scene: the test app, rules.md 7), 2026-11-13T01:57:12

### build-core/azahar_lazpy_libretro.dylib

| n | total host fps | per-instance host fps | app fps | x real | cpu ms/frame | wall ms/frame | host share | peak RSS MB | nice | load start/end | slot wait s | check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2177.4 | 2177.4 | 2177.4 | 36.39 | 0.7 | 0.5 | 0.1% | 1177 | 15 | 10.9/9.4 | 0.0 | ok |
| 2 | 3167.4 | 1585.0 / 1582.4 | 1585.0 / 1582.4 | 26.49 / 26.45 | 0.8 / 0.8 | 0.6 / 0.6 | 0.1% / 0.1% | 796 / 769 | 15 / 15 | 9.4/15.1 | 0.0 / 0.0 | ok |
| 3 | 3539.9 | 1179.4 / 1182.0 / 1178.5 | 1179.4 / 1182.0 / 1178.5 | 19.71 / 19.76 / 19.70 | 0.9 / 0.9 / 0.9 | 0.8 / 0.8 / 0.8 | 0.1% / 0.1% / 0.1% | 787 / 807 / 781 | 15 / 15 / 15 | 15.1/14.5 | 0.0 / 0.0 / 0.0 | ok |
| 4 | 3434.3 | 858.7 / 858.5 / 858.5 / 858.6 | 858.7 / 858.5 / 858.5 / 858.6 | 14.35 / 14.35 / 14.35 / 14.35 | 0.9 / 0.9 / 0.9 / 0.9 | 1.2 / 1.2 / 1.2 / 1.2 | 0.1% / 0.0% / 0.1% / 0.1% | 1093 / 768 / 1105 / 1190 | 15 / 15 / 15 / 15 | 14.5/16.6 | 0.0 / 0.0 / 0.0 / 0.0 | ok |

### dl/azahar/azahar_libretro.dylib

| n | total host fps | per-instance host fps | app fps | x real | cpu ms/frame | wall ms/frame | host share | peak RSS MB | nice | load start/end | slot wait s | check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1652.2 | 1652.2 | 1652.2 | 27.61 | 0.8 | 0.6 | 0.1% | 1586 | 15 | 16.6/32.8 | 0.0 | ok |
| 2 | 2305.2 | 1154.8 / 1150.3 | 1154.8 / 1150.3 | 19.30 / 19.23 | 1.0 / 1.0 | 0.9 / 0.9 | 0.1% / 0.1% | 960 / 1014 | 15 / 15 | 32.8/35.9 | 0.0 / 0.0 | ok |
| 3 | 2778.5 | 926.1 / 926.3 / 926.1 | 926.1 / 926.3 / 926.1 | 15.48 / 15.48 / 15.48 | 0.9 / 0.9 / 0.9 | 1.1 / 1.1 / 1.1 | 0.1% / 0.1% / 0.1% | 787 / 914 / 808 | 15 / 15 / 15 | 35.9/36.3 | 0.0 / 0.0 / 0.0 | ok |

Cap rule on build-core/azahar_lazpy_libretro.dylib: cap 2 (provisional, light scene). n=2: total fps x1.45 and load 15.1: step up; n=3: total fps x1.12 of n=2 is under x1.25: stop at 2

Round trip: {"run1_ms_per_frame": 1.0693674316765585, "run600_ms_per_frame": 0.9549313200113829, "per_call_ms": 0.11443611166517553}

Shots: [{"level": 1, "ms_per_shot": 6.207618750340771, "top_png_bytes": 3930, "log_line": "png level=1"}, {"level": 6, "ms_per_shot": 5.762449999747332, "top_png_bytes": 1882, "log_line": "png level=6"}]

Effective options of build-core/azahar_lazpy_libretro.dylib:

```
citra_use_cpu_jit=enabled
citra_cpu_clock_percentage=100
citra_is_new_3ds=New 3DS
citra_region_value=Auto
citra_language_value=English
citra_audio_emulation=hle
citra_input_type=none
citra_graphics_api=Vulkan
citra_use_hw_shader=enabled
citra_use_shader_jit=enabled
citra_shaders_accurate_mul=enabled
citra_use_disk_shader_cache=enabled
citra_resolution_factor=1
citra_texture_filter=none
citra_texture_sampling=GameControlled
citra_custom_textures=disabled
citra_dump_textures=disabled
citra_layout_option=default
citra_swap_screen=Top
citra_swap_screen_mode=Toggle
citra_large_screen_proportion=4.00
citra_render_3d=off
citra_factor_3d=0
citra_use_virtual_sd=enabled
citra_use_libretro_save_path=LibRetro Default
citra_analog_function=c_stick
citra_analog_deadzone=15
citra_enable_mouse_touchscreen=enabled
citra_enable_touch_touchscreen=enabled
citra_enable_touch_pointer_timeout=enabled
citra_enable_motion=disabled
citra_motion_sensitivity=1.0
citra_deterministic_async_operations=enabled
citra_async_fs_operations=disabled
citra_instant_debug_log=enabled
citra_init_clock=FixedTime
citra_init_time=946681277
citra_init_ticks_type=Fixed
```

Effective options of dl/azahar/azahar_libretro.dylib:

```
citra_use_cpu_jit=enabled
citra_cpu_clock_percentage=100
citra_is_new_3ds=New 3DS
citra_region_value=Auto
citra_language_value=English
citra_audio_emulation=hle
citra_input_type=none
citra_graphics_api=Vulkan
citra_use_hw_shader=enabled
citra_use_shader_jit=enabled
citra_shaders_accurate_mul=enabled
citra_use_disk_shader_cache=enabled
citra_resolution_factor=1
citra_texture_filter=none
citra_texture_sampling=GameControlled
citra_custom_textures=disabled
citra_dump_textures=disabled
citra_layout_option=default
citra_swap_screen=Top
citra_swap_screen_mode=Toggle
citra_large_screen_proportion=4.00
citra_render_3d=off
citra_factor_3d=0
citra_use_virtual_sd=enabled
citra_use_libretro_save_path=LibRetro Default
citra_analog_function=c_stick
citra_analog_deadzone=15
citra_enable_mouse_touchscreen=enabled
citra_enable_touch_touchscreen=enabled
citra_enable_touch_pointer_timeout=enabled
citra_enable_motion=disabled
citra_motion_sensitivity=1.0
```
