# P8-05: Packaging and robustness for a Python wrapper around a native emulator host

Date: 2026-11-18. Scope: what a Python package that ships a native host plus a large emulator core (GPU-dependent) must get right on macOS arm64, Windows x64 and Linux, and how it should behave when the guest or the GPU misbehaves. Evidence is web docs and public issue trackers only. Licences marked (m) are from memory, not re-checked on the page.

## 1. Tools and projects consulted

| Name | Link | Licence | What it is |
|---|---|---|---|
| cibuildwheel | https://cibuildwheel.pypa.io/en/stable/options/ | BSD-2 (m) | CI wheel builder; runs repair + test per platform |
| auditwheel / delocate / delvewheel | https://github.com/adang1345/delvewheel | MIT / BSD-2 / MIT (m) | Bundle shared libs into Linux / macOS / Windows wheels |
| PyBoy | https://github.com/Baekalfen/PyBoy | LGPL-3.0 (m) | Python Game Boy emulator with scripting API, Cython core |
| stable-retro | https://github.com/Farama-Foundation/stable-retro | MIT (core licences listed per core) | Gymnasium wrapper over libretro cores; wheels per platform |
| pygame | https://github.com/pygame/pygame | LGPL-2.1 (m) | SDL wrapper; headless via SDL_VIDEODRIVER dummy |
| PyTorch | https://github.com/pytorch/pytorch/blob/main/RELEASE.md | BSD-3 (m) | Large native wheels; published platform matrix |
| MoltenVK | https://github.com/KhronosGroup/MoltenVK | Apache-2.0 (m) | Vulkan over Metal; Khronos-deprecated, community maintained |
| Mesa lavapipe / SwiftShader | https://docs.mesa3d.org/ | MIT / Apache-2.0 (m) | CPU Vulkan ICDs for GPU-less machines |
| Azahar libretro core | https://github.com/azahar-emu/azahar | GPL-2.0+ (m) | The 3DS core this project hosts |
| PyPI storage limits | https://docs.pypi.org/project-management/storage-limits/ | n/a | Size rules for uploads |

## 2. What must work

### Must

- **M1. Prebuilt wheels for every supported platform, so `pip install` never compiles.**
  - Relied on by every user who is not a toolchain owner; the failure is silent until a source build blows up.
  - PyBoy users on Windows and macOS fell back to the sdist and hit Cython build errors when wheels were missing: https://github.com/Baekalfen/PyBoy/issues/321
  - stable-retro tracks "re-enable macOS binary wheels" and Linux ARM wheels as open work, i.e. a platform matrix that has already lost entries: https://github.com/Farama-Foundation/Stable-Retro/issues/267 , https://github.com/Farama-Foundation/Stable-Retro/issues/268
  - cibuildwheel defaults: auditwheel (Linux), delocate (macOS), delvewheel (Windows), manylinux_2_28 image: https://cibuildwheel.pypa.io/en/stable/options/
- **M2. Windows: bundled DLLs are found by explicit directory, never via PATH.**
  - Relied on by every Windows import. Since Python 3.8 dependent DLLs load only from trusted locations plus `os.add_dll_directory()`: https://docs.python.org/3/whatsnew/3.8.html
  - delvewheel patches `__init__.py` to do this; a top-level `.pyd` with no package had no place for the patch: https://github.com/adang1345/delvewheel/issues/9
  - If the host is an `.exe` child process, set its working dir / `PATH` for the child explicitly instead.
- **M3. macOS arm64: every shipped Mach-O is (at least ad-hoc) signed after the last edit.**
  - Apple silicon kills unsigned or invalidly signed code; `install_name_tool` (used by delocate-style rpath rewriting) invalidates signatures, so re-run `codesign --force -s -` last: https://gitlab.kitware.com/cmake/cmake/-/work_items/21854 and https://developer.apple.com/forums/thread/130313
  - Add a CI smoke test that runs the installed wheel on an arm64 runner, not the build tree (cibuildwheel `test-command` runs against the installed wheel from a temp dir).
- **M4. Core in a child process, with parent-death cleanup.**
  - Relied on by any caller running many copies or untrusted guest code: a guest crash, access violation or driver crash must not kill the Python caller.
  - Native crashes are routine in this domain: the libretro Azahar core crashes in the AMD Vulkan driver on Windows (`0xC0000005` in `vkCreateImage`): https://github.com/azahar-emu/azahar/issues/2742 and https://github.com/azahar-emu/azahar/issues/2577
  - In-process Cython wrappers turn ordinary errors into segfaults (PyBoy, invalid ROM path): https://github.com/Baekalfen/PyBoy/issues/97
  - `Popen.wait/communicate(timeout)` does NOT kill the child; the caller must kill and reap: https://docs.python.org/3/library/subprocess.html
- **M5. Timeouts and a watchdog on every call that waits for the host.** Frame step, load, save state and screenshot each get a deadline; on expiry, kill the child, reap it, raise a typed error naming the operation. Source for the kill-then-reap rule: https://docs.python.org/3/library/subprocess.html
- **M6. Actionable import/start errors.** PyTorch's own maintainers were asked to fix the bare "DLL load failed" message, since users resorted to reinstalling unrelated components: https://github.com/pytorch/pytorch/issues/32916 . On failure, report: OS and arch, Python version, which file was missing (full path), and the next step.
- **M7. A published support matrix with tested versions.** PyTorch lists OS, arch, minimum OS version, Python range and accelerator versions per release: https://github.com/pytorch/pytorch/blob/main/RELEASE.md . Stable-retro lists SSE3 CPU requirement and per-OS caveats: https://github.com/Farama-Foundation/stable-retro
- **M8. Host/core/wrapper version pinning checked at start-up.** Mismatched binaries crash instead of erroring (see F9, F10). Wrapper must verify the core build id before the first call.

### Should

- **S1. Headless Vulkan fallback story, documented.** On Linux or CI with no GPU, a software ICD is the norm: lavapipe via `VK_DRIVER_FILES` / `VK_ICD_FILENAMES`, or SwiftShader (Dawn, ONNX Runtime CI use it). One CI recipe sets both variables: https://github.com/BabylonJS/BabylonNative/pull/1648/files ; ONNX Runtime moved from lavapipe to SwiftShader after an incompatible-driver error: https://app.semanticdiff.com/gh/microsoft/onnxruntime/commit/eea7db461e1bedd5a3eb86804f1e2e8716c65a45 . Container GPU runtimes may inject the driver library but not the ICD JSON (same ONNX source family, second commit: https://app.semanticdiff.com/gh/microsoft/onnxruntime/commit/72cb0426bfa166a1c050a5a2ace8f202752c68ed).
- **S2. Renderer choice exposed as a documented option, with an OpenGL or software fallback.** Users of the Azahar core worked around the Vulkan crash by selecting OpenGL in the core option file: https://github.com/azahar-emu/azahar/issues/2577
- **S3. Machine-wide instance cap** (named lock or lock-file directory counting live PIDs) with a clear "N of M slots in use, held by PIDs..." error. Evidence of demand: users run vector environments through `SubprocVecEnv` and hit process-spawn problems: https://github.com/Farama-Foundation/Stable-Retro/issues/112
- **S4. Leftover cleanup:** per-instance temp dir named with owner PID, reaped on next start if the PID is dead; atexit + signal handlers; on Windows a Job object (kill-on-close), on Linux `PR_SET_PDEATHSIG`, on macOS a pipe-EOF watchdog in the child. `CREATE_NEW_PROCESS_GROUP` is needed to signal a Windows child: https://docs.python.org/3/library/subprocess.html
- **S5. SemVer with a deprecation window.** 0.y.z means anything may change; after 1.0, keep at least one minor release carrying the deprecation before a major removal: https://semver.org/
- **S6. Docs users expect:** quickstart, API reference, troubleshooting page keyed by exact error strings, support matrix. PyBoy's README sends install problems to a wiki page and a chat server rather than a troubleshooting table, and support questions pile up as issues: https://github.com/Baekalfen/PyBoy/issues/138
- **S7. Size discipline.** PyPI file limit is 100 MB (200 MB for organisation projects), project total 10 GB; increases need a prior release under the limit and a request: https://docs.pypi.org/project-management/storage-limits/ . A host plus a GPU-emulator core can approach this, so strip symbols and measure per wheel.
- **S8. Stable-ABI (abi3) or no-extension design** so one wheel per platform serves all Python minors: https://packaging.python.org/en/latest/guides/packaging-binary-extensions/ . Using a pure-ctypes/pipe wrapper around a separate host binary achieves the same.

### Nice

- **N1. MSVC runtime is the only runtime in the wheel.** Builds with VS 2019+ need `VCRUNTIME140_1.dll`, which older CPython installs may lack: https://packaging.python.org/en/latest/guides/packaging-binary-extensions/ . delvewheel can bundle the runtime, but a mis-ordered bundled runtime has caused load failures: https://github.com/adang1345/delvewheel/issues/49
- **N2. Windows code signing of the host `.exe`/DLLs.** Antivirus false positives on unsigned, packed binaries are a recurring problem; signing and vendor submission are the standard mitigations: https://groups.google.com/g/pyinstaller/c/Y-PsWjys6GA/m/FZ3dkGXZhR0J , https://discuss.python.org/t/pyinstaller-false-positive/43171
- **N3. macOS notarization** for a separate downloadable bundle (not needed for pip-installed files). Quarantine is set on browser-downloaded files and can make a library load fail with a library error rather than a security message; `xattr -l` diagnoses it: https://developer.apple.com/forums/thread/732370 , https://racket.discourse.group/t/libintl-9-dylib-cannot-be-verified-error-with-macos-executable/690
- **N4. `doctor` command** that prints platform, GPU/ICD found, core build id, free slots, temp dir state, and a pass/fail for a one-frame run.
- **N5. Memory-map and state caveats documented** per core version (see F12).
- **N6. First-class headless flag precedent.** pygame's maintainers discuss a dedicated headless API rather than env vars: https://github.com/pygame/pygame/issues/2377

## 3. Failure modes users report

| # | Symptom | Root-cause class | Links |
|---|---|---|---|
| F1 | `pip install` builds from source and fails (Cython errors) because no wheel matched Windows or macOS/Python combo | Missing wheel / platform-tag gap | https://github.com/Baekalfen/PyBoy/issues/321 |
| F2 | Wheels dropped for macOS and Linux ARM in a downstream project | CI matrix rot | https://github.com/Farama-Foundation/Stable-Retro/issues/267 , https://github.com/Farama-Foundation/Stable-Retro/issues/268 |
| F3 | `ImportError: DLL load failed while importing` after delvewheel repair (top-level `.pyd`) | Windows DLL search path | https://github.com/adang1345/delvewheel/issues/9 |
| F4 | Same error, bundled runtime DLL conflicts; loading one dependency first makes the other load | Dependency load order / bundled MSVC runtime | https://github.com/adang1345/delvewheel/issues/49 |
| F5 | `from torch._C import *` DLL load failed with no hint; file-operation trace shows search path misses | Opaque error message + search path | https://github.com/pytorch/pytorch/issues/32916 |
| F6 | macOS: "cannot be verified" / library load fails for a downloaded dylib | Gatekeeper quarantine (unsigned/un-notarized) | https://racket.discourse.group/t/libintl-9-dylib-cannot-be-verified-error-with-macos-executable/690 , https://developer.apple.com/forums/thread/732370 |
| F7 | arm64 binary or dylib killed with Code Signature Invalid after relinking/rpath edit | Signature invalidated by post-link edit | https://gitlab.kitware.com/cmake/cmake/-/work_items/21854 , https://developer.apple.com/forums/thread/130313 |
| F8 | delocate wheel repair links different libraries depending on arch on a newer macOS runner | Universal2 / per-arch library resolution | https://github.com/pypa/cibuildwheel/issues/2121 |
| F9 | Libretro core crashes right after loading content on Windows x64 since one release; fine on the older build | Core/version regression, GPU API | https://github.com/azahar-emu/azahar/issues/2577 |
| F10 | Same core crashes only on AMD GPUs inside the Vulkan driver (invalid queue-family fields in an image-create struct); OpenGL works | Vendor driver + core bug; no fallback | https://github.com/azahar-emu/azahar/issues/2742 |
| F11 | Invalid ROM path causes a segfault instead of an exception | In-process native code, no input validation | https://github.com/Baekalfen/PyBoy/issues/97 |
| F12 | Core exposes its memory map once at load, so later heap regions are never visible to a memory-reading client | Core API semantics vary by version | https://github.com/azahar-emu/azahar/issues/2667 |
| F13 | "No hardware accelerated renderers available" on a VM; SDL dummy driver is the usual escape, discussed as needing a proper API | Missing GPU / headless path | https://github.com/pygame/pygame/issues/3835 , https://github.com/pygame/pygame/issues/2377 |
| F14 | Headless Vulkan compute sample froze the whole machine on MoltenVK | Metal/MoltenVK headless hang | https://github.com/KhronosGroup/MoltenVK/issues/836 |
| F15 | Users ask for a headless mode in the emulator itself (no window manager, CI use) | Missing feature upstream | https://github.com/azahar-emu/azahar/issues/1476 |
| F16 | Multiprocessing vector-env crash in a forked/spawned worker (wrapper attribute missing in subprocess) | Process model not designed for fan-out | https://github.com/Farama-Foundation/Stable-Retro/issues/112 |

Gap: I found no public issue specifically about zombie or orphaned emulator processes in these trackers; the zombie rules in S4 rest on the Python subprocess docs (timeouts do not kill the child), not on user reports.

## 4. Implications for a headless 3DS libretro-core host

- Ship the host as a separate executable launched per instance. This isolates guest and Vulkan-driver crashes (F9, F10, F11) and makes the wheel mostly data plus a thin pure-Python controller, so abi3 or py3-none wheels are possible.
- Plan one wheel per (macOS arm64, Windows x64, optional Linux x64); each must pass an install-and-run-one-frame test on a clean runner of that OS, GPU or no GPU (F1, F2, F3).
- Core size matters: check the compressed wheel against the 100 MB default PyPI limit early and file the increase request before the first release (S7).
- macOS: sign host and core ad-hoc as the final step; if the core is downloaded outside pip, document the `xattr` step and consider notarization (F6, F7).
- Windows: launch the host with an explicit DLL directory and working dir; prefer one MSVC runtime; sign the binaries if affordable; document the Defender submission route (F3, F4, N2).
- Treat the GPU backend as configuration: auto-detect, offer a software or OpenGL fallback, and report the active renderer in `doctor` output (S1, S2, F10).
- Pin and verify host, core and wrapper build ids at start-up; refuse mismatches with a message that names both versions (F9, F12).
- Own the process lifecycle: deadlines on every call, kill-and-reap on timeout, parent-death handling per OS, PID-tagged temp dirs, and a machine-wide slot cap with a readable error (M4, M5, S3, S4).
- Start at 0.y.z, mark the API provisional in the README, then adopt SemVer plus a one-minor deprecation window at 1.0 (S5).
- Write the troubleshooting page from the table in section 3, keyed by exact error text.
