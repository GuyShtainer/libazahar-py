# libretro.py probe (laz-06), 2026-11-12

## Verdict: borrow parts (not usable as the host)
libretro.py cannot host the Azahar core with the Vulkan renderer, so it cannot be our host for the fast path. It does
host the core headless with the Software renderer (works, slow). Keep fe2.c (C) as the host; borrow ideas only.

## What was read
libretro.py v0.12.0 (latest tag; PyPI wheel `libretro_py-0.12.0-py3-none-macosx_11_0_arm64.whl`, MIT). Paths below are
inside the wheel's `libretro/` package.

| Question | Answer | Evidence |
|---|---|---|
| SET_HW_RENDER for Vulkan | No. Only OpenGL (moderngl) hardware driver exists; the Vulkan enum value is present but unsupported | `api/video/context.py:68-74` ("libretro.py doesn't currently support Vulkan contexts. Pull requests are welcome!"); `drivers/video/` holds only `opengl/moderngl.py`, `software/`, `multi.py`; `py/_common.py:97,127` and `py/runs.py:81-82` only map a Vulkan name onto a driver that does not exist |
| HW context negotiation interface (create_device) | Stub, returns False | `drivers/environment/composite.py:1293-1296` (`return False  # TODO: Implement`) |
| GET_HW_RENDER_INTERFACE | Plumbed, but returns False unless the video driver supplies one; no driver does for Vulkan | `drivers/environment/composite.py:1260-1270` |
| SET_MEMORY_MAPS | Implemented: stores a deep copy of the core's retro_memory_map, exposed as `memory_maps` | `drivers/environment/composite.py:1187-1192`. Azahar does not call it anyway (spike 1: memory API returns 0/NULL) |
| Variadic log callback | Not supported by ctypes; it passes the unformatted format string. Azahar pre-formats its messages, so its log reads fine | `drivers/log/driver.py:34-42`, default `UnformattedLogDriver` |
| Headless | Yes for software and for the no-window default; windowed GL is opt-in | `py/runs.py:62-68` |
| Frame loop | Python per frame: `for _ in range(frames): session.run()` calls `retro_run` through ctypes | `py/runs.py:96-98`, `core.py:490-496` |

## Real try (macOS arm64, Python 3.14 venv in scratch, `-I`, one instance, core dl/azahar_libretro.dylib, ROM Gen3D.3dsx)
Script: `/private/tmp/claude-501/-Users-guyshtainer-VSCodeProjects-3ds-toolkit/27a3b0de-48d1-4ae4-9576-db27c1f9f28c/scratchpad/lrpy/try.py`.
Temp-dir system/save path driver (default); no window opened.
* `citra_graphics_api=Vulkan`: the core logs `Using Vulkan hw renderer`, then `Session` raises `RuntimeError: Failed to
  load game` (libretro.py answers SET_HW_RENDER for Vulkan with false). Confirms the source reading. Same for Auto.
* `citra_graphics_api=Software`: loads, Gen3D boots, 300 frames run with no crash. First `retro_run` 0.22 s,
  then **20.3 frames/s** (300 frames in 14.8 s). fe2.c software run measured 30-44 fps (spike 1), so the software
  renderer itself is the cost and this is no use for speed.

## Per-frame Python overhead
Could not be measured on Azahar (the only working mode is dominated by software rendering). Measured instead on
libretro.py's bundled `software_rendering` sample core (trivial core, the full Session loop incl. its video driver
copying the frame): **11,100 run/s = 90 us per `session.run()`** (20,000 frames). Treat 90 us as an upper bound on the
Python plus ctypes plus frame-copy cost. Against fe2's ~3000 retro_run/s (330 us per frame on an idle menu) that adds
about 27 %; against a heavy 3D scene it is small. The bundled `tests/test` core ran at 770/s (1.3 ms/frame) because of
its own log output, not the loop. A bare ctypes `retro_run` call is cheaper than 90 us.

## What is worth borrowing
* The API shape: `Session(core, game, options=..., path=..., input=...)` with pluggable drivers, `serialize`/`unserialize`
  wrappers, an input driver taking per-frame iterables (matches our scripted per-frame pad/touch plan).
* Environment-call dispatch table (`drivers/environment/default.py:124-330`) as a checklist of calls the core may make.
* Do not borrow the video path; the Vulkan negotiation and readback stay in fe2.c / a native module.

## Plan impact
Python drives batches over our native host (fe2-derived); do not depend on libretro.py. If a pure-Python control
layer is wanted later, a ctypes shim around our own host library is smaller than adding Vulkan to libretro.py
(that would need the negotiation interface, VkInstance/device handoff and image readback: what fe2.c already does).
