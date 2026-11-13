# D24S8 stencil readback on MoltenVK (step L, item laz-520)

Investigator: opus agent a68ab49f94481d0d2, 2026-11-13 11:51-12:01, read-only (nothing built or run). Saved verbatim
by the main loop; only the notes path is shortened (the session scratchpad, not tracked).

Source root (S) = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/src/video_core`. This was read-only: nothing was built or run. My notes are in the session scratchpad (`a3-notes.md`).

## Findings (cited)
1. **Format.** D24S8 maps to `eD24UnormS8Uint` (`renderer_vulkan/vk_instance.cpp:38`). If that format is unsuitable (Apple GPUs), it falls back to `eD32SfloatS8Uint` with `needs_conversion=true` (`vk_instance.cpp:285-305`). The aspect is Depth|Stencil (`vk_instance.cpp:107-108`). Upload de-interleaves on the CPU into D32 float plus a separate stencil plane (`vk_texture_runtime.cpp:89-122`, `:906-916`).
2. **Memory fill.** `AccelerateFill` only registers a Fill surface (`rasterizer_cache/rasterizer_cache.h:359-384`). When the depth buffer is first validated, `CopySurface` turns it into `ClearTexture` (`rasterizer_cache.h:441-450`). Stencil is taken from bits 24..31 (`rasterizer_cache/surface_base.cpp:155-161`), and the `ClearValue` is zero-initialised. A full-rect clear calls `clearDepthStencilImage` with aspect = `surface.Aspect()`, so both aspects are cleared (`vk_texture_runtime.cpp:347-405`). A partial clear uses a render pass with `stencilLoadOp = load_op` (`vk_render_manager.cpp:175-184`). The stencil aspect is kept by the clear.
3. **Download.** `Surface::Download` for D24S8 calls `BlitHelper::DepthToBuffer`, then `scheduler.Finish()` (`vk_texture_runtime.cpp:1029-1041`). DepthToBuffer binds `DepthView()` and `StencilView()` as combined samplers in `eDepthStencilReadOnlyOptimal` (`renderer_vulkan/vk_blit_helper.cpp:513-519`).
   - Pre-barrier: General → DSReadOnly, D|S aspects, srcStage Early/LateFragmentTests only, srcAccess DSAttachmentWrite only (`vk_blit_helper.cpp:525-561`).
   - Dispatch is `w/8 × h/8` (`:577`).
   - Shader (`host_shaders/vulkan_depth_to_buffer.comp:22-29`): `texture()` on a `usampler2D` at **texel-corner** coordinates (`tex_icoord/extent`, no +0.5). The D24S8→RGBA8 shader uses `texelFetch` instead.
   - The stencil and depth views are created lazily on first use (`vk_texture_runtime.cpp:1303-1330`).
4. **Where first use differs.** `is_framebuffer` becomes true only in `FramebufferView()` (`vk_texture_runtime.h:228-231`). That is called from the Framebuffer constructor (`vk_texture_runtime.cpp:1487`), which runs *after* `ValidateSurface(depth_id…)` (`rasterizer_cache.h:784` vs `:798`). So the first fill-clear on a fresh depth surface builds its post-barrier from `PipelineStageFlags()` and `AccessFlags()` without attachment stages or access (`vk_texture_runtime.cpp:1170-1195`). Its dst scope is Transfer|FragmentShader with ShaderRead/TransferRW, and has no Early/LateFragmentTests or DSAttachmentRead.
   - `BeginRendering` records no barrier (`vk_render_manager.cpp:47-66`).
   - The render pass has `dependencyCount = 0` (`vk_render_manager.cpp:229`).
   - Result: the draw's stencil `loadOp=LOAD` has **no dependency on the clear's transfer write**. This is a real Vulkan sync hazard, and it exists only on first use; once `is_framebuffer` is set, later clears are covered.
5. **Same gap on transfer → compute.** `CopyTextures` (the accelerated GX TextureCopy into a fresh D24S8 surface) ends with dst stages = `dest.PipelineStageFlags()` (`vk_texture_runtime.cpp:589-590`, no Compute). DepthToBuffer's src scope is only fragment tests, so a transfer write followed by the compute read forms no barrier chain. The same applies to `ConvertDS24S8ToRGBA8` (`vk_blit_helper.cpp:402-510`).
6. **Environment.** The renderer is identical between 2125.1.2 and 2126.2. I fetched the 2125.1.2 files and diffed them: blit_helper and render_manager differ only in license lines. `vk_texture_runtime.cpp` differs in clear layer ranges, `Finish→Flush` (`:319-322`) and the resource-free tick. What does differ:
   - **MoltenVK version.** The windowed 2125.1.2 bundle ships MoltenVK **1.2.9**; our host loads **1.4.2** (`dl/moltenvk/.../Docs/Whats_New.md:16`). MoltenVK 1.3.0 turned `MVK_CONFIG_USE_MTLHEAP` on by default and moved barriers to Metal fences (`Whats_New.md:241-242, 263`). With placement heaps, Metal's automatic hazard tracking no longer hides missing app barriers. My inference is that 1.2.9's tracked resources made gaps 4–5 harmless.
   - **Instance and device setup.** The libretro path creates its own device through negotiation v1 `create_device` (`citra_libretro/libretro_vk.cpp:62-220`, `citra_libretro.cpp:608-614`). The MoltenVK layer settings in `renderer_vulkan/vk_platform.cpp:357-386` are never applied, and host `vk.c:250-275` creates the instance with no `VK_EXT_layer_settings`. Our host's device has no `separateDepthStencilLayouts` or other 1.2 features, and Azahar does not need them: it always uses combined layouts.

## Ranked causes
1. **Most likely: first-use clear → render-pass LOAD hazard (finding 4), exposed by MoltenVK 1.4.2's heap/fence regime (finding 6).** The evidence fits all of it:
   - only first use is affected, and later readbacks pass;
   - it varies between launches, which is a race signature;
   - only some tiles are correct (the partial bboxes);
   - the wrong value is ff, which is neither the clear (00) nor the draw (0x80), so it is pre-clear memory;
   - a stencil test or op against a garbage loaded value explains 0x81→ff and 0x89→0x88 in the second app;
   - the same code passes on 1.2.9.

   Not explained by the code: why depth comes out exact while stencil does not. Apple stores stencil as a separate plane, so a per-plane timing difference is plausible, but I have not verified it.
2. **The transfer→compute gap in DepthToBuffer and ConvertDS24S8 (finding 5).** This bites when the last writer was a clear or copy rather than a draw, such as the accelerated TextureCopy into a fresh surface.
3. **A MoltenVK stencil-view or heap bug.** The X32_Stencil8 view is created lazily on first use, and 1.4.1/1.4.2 fix bugs in `MVKImagePlane::getMTLTexture` and the placement-heap checks. The tracker has known heap-default corruption (#2475, AMD, fixed by #2509) and D32S8 aspect copy bugs (#2880). This is possible but would not by itself explain the partial correct tiles.
4. **Corner-coordinate `texture()` sampling in the shader (finding 3).** A nearest-filter lookup exactly on a texel boundary can round to the neighbour. That could produce edge jitter, but it would be deterministic. The 4 px in 1.53 M jitter is more likely cause 1 on the color path, which has the same `is_framebuffer` gap for color clears.
5. **Ruled out:**
   - the clear applying depth only (aspect is D|S);
   - stencil being dropped in the render pass (stencil is LOAD/STORE);
   - the download running before submit (`Finish` waits on a fence: `libretro_vk.cpp:772-866`);
   - a missing stencil aspect in the barriers (all are D|S).

## Upstream
- `vk_blit_helper.cpp` and `vulkan_depth_to_buffer.comp` have had no functional change since 2023/2024 (GitHub commit history). The commits after 2126.2 are the MSAA work (736189ea77, 6b4e7f2e69, in 2127.0-rc), with no stencil or barrier fix.
- An issue search of azahar-emu/azahar for "stencil" found nothing relevant.
- So there is no upstream fix to pick up. The 2125.1.2 pass is explained by its MoltenVK, not by different Azahar code.

## Proposed patch
New file `core/patches/0009-lazpy-ds-barriers.patch` (main loop's note: 0009 is taken by the thread-registers patch, so this one is 0010), against `renderer_vulkan/vk_texture_runtime.cpp:1170-1195` and `vk_blit_helper.cpp`:
```diff
 vk::AccessFlags Surface::AccessFlags() const noexcept {
-           (is_framebuffer ? attachment_flags : vk::AccessFlagBits::eNone) |
+           ((is_framebuffer || type != SurfaceType::Texture) ? attachment_flags : vk::AccessFlagBits::eNone) |
 vk::PipelineStageFlags Surface::PipelineStageFlags() const noexcept {
-           (is_framebuffer ? attachment_flags : vk::PipelineStageFlagBits::eNone) |
-           (is_storage ? vk::PipelineStageFlagBits::eComputeShader : vk::PipelineStageFlagBits::eNone);
+           ((is_framebuffer || type != SurfaceType::Texture) ? attachment_flags : vk::PipelineStageFlagBits::eNone) |
+           ((is_storage || type == SurfaceType::DepthStencil) ? vk::PipelineStageFlagBits::eComputeShader
+                                                              : vk::PipelineStageFlagBits::eNone);
 // vk_blit_helper.cpp DepthToBuffer (:527, :559-561) and ConvertDS24S8ToRGBA8 (:416, its pre barrier):
-            .srcAccessMask = vk::AccessFlagBits::eDepthStencilAttachmentWrite,
+            .srcAccessMask = vk::AccessFlagBits::eDepthStencilAttachmentWrite | vk::AccessFlagBits::eTransferWrite,
-        cmdbuf.pipelineBarrier(eEarlyFragmentTests | eLateFragmentTests, eComputeShader, ...
+        cmdbuf.pipelineBarrier(eEarlyFragmentTests | eLateFragmentTests | eTransfer, eComputeShader, ...
```
- The stage and access widening is legal without attachment usage.
- Optional: change the shader to `texelFetch(depth|stencil, tex_icoord, 0)`, which removes the boundary rounding.
- Optional: fix the harmless self-assignment at `vk_texture_runtime.cpp:239` (`Mip0 = Mip0`).

## Experiment
These need no rebuild; run each N=20 times on the self-test.
1. Set `LAZ_MVK` (`host/vk.c:196-201`) to the windowed 2125.1.2 bundle's `Contents/Frameworks/libMoltenVK.dylib` (version 1.2.9). If every run passes, the environment is confirmed as the trigger.
2. On 1.4.2, set `MVK_CONFIG_USE_MTLHEAP=0`. MoltenVK reads `MVK_CONFIG_*` environment variables, and our instance sets no layer settings. If this passes, it is the heap/untracked regime.
3. Guest-side: draw one dummy pass into the depth buffer before the fill. That sets `is_framebuffer` early. If the test then passes on 1.4.2, the first-use barrier gap is confirmed.
4. After applying the patch, run 1.4.2 with heaps on. Every run should pass. Optionally run with Khronos sync validation, which should report RAW hazards on the unpatched core.

## Test-app repro
libctru/citro3d, a fresh process per run:
1. Make a D24S8 target: `C3D_RenderTargetCreate(…, GPU_RB_DEPTH24_STENCIL8)`.
2. Clear it with `C3D_RenderTargetClear(C3D_CLEAR_ALL, 0, 0x00FFFFFE)`, a 32-bit GX MemoryFill. Avoid 24-bit fills: their stencil byte is not 00.
3. Draw one quad of exactly 100×80 px at a known rect:
   - `C3D_DepthTest(true, GPU_ALWAYS, GPU_WRITE_ALL)`;
   - `C3D_StencilTest(true, GPU_ALWAYS, 0x80, 0xFF, 0xFF)`;
   - `C3D_StencilOp(KEEP, KEEP, REPLACE)`;
   - z chosen so depth = 0x4001ff.

   Variant B uses `GPU_EQUAL` with ref 0 and `INCR`, to amplify a garbage loaded value.
4. After `C3D_FrameEnd`, run `GX_TextureCopy(depthbuf → linearAlloc dst, size = w*h*4)`, wait for PPF, then `GSPGPU_InvalidateDataCache`.
5. Count over the copy. Each pixel is a little-endian u32 with stencil in byte 3 and depth in bytes 0-2. Record:
   - a histogram of the stencil byte;
   - the bbox of 0x80 after Morton de-tiling;
   - mismatches in the depth code.

   Expected: 8000 px of 0x80, the rest 00; depth 4001ff inside and fffffe outside.
6. Variants: (a) first use; (b) pre-touched, with a dummy draw before the fill; (c) DisplayTransfer instead of TextureCopy; (d) a second readback in the same process.
7. Publish the counts at a fixed RAM address for the host's memory exports. A bug is reproduced if (a) differs between launches while (b) and (d) always pass.

Sources: [MoltenVK #2475](https://github.com/KhronosGroup/MoltenVK/issues/2475), [MoltenVK #2880](https://github.com/KhronosGroup/MoltenVK/issues/2880), [Apple X32_Stencil8](https://developer.apple.com/documentation/metal/mtlpixelformat/x32_stencil8.md), [MoltenVK stencil-view commit](https://skia.googlesource.com/external/github.com/KhronosGroup/MoltenVK/+/333c75a760563e1de8ce3b0d85862f913d74388e%5E%21/)
