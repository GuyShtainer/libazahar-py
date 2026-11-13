# Core patch 0011 review (the shader-cache switch after a state load)

Reviewer: opus agent af7ecbcfd68c8532d, 2026-11-13 12:55-13:00, read-only, on the first text of
`core/patches/0011-lazpy-shader-cache-switch.patch`. Saved verbatim by the main loop; only the scratchpad path is
shortened (the session scratchpad, not tracked). The main loop then made the changes in findings 2 and 5 (the save
guard, the comments, the README rows); the committed patch is that version.

**Verdict: ship with changes.** The patch fixes the root cause on both crash paths. It needs one more line so a state load stops overwriting the on-disk driver cache, and its comments need to name the second path.

All paths below are under build-src/azahar-unified-source-2126.2/src/ unless noted. For every file I read, the build-src copy is identical to pristine upstream. I checked the patch's format by hand only; I did not run `patch --dry-run` or any build. Notes: the session scratchpad's `m-review/notes.md`.

1. **Root cause: yes, it is fixed.** The early return in SwitchCache (vk_pipeline_cache.cpp:161) checks only `current_program_id`. That value starts at 0 (vk_pipeline_cache.h:163). The function never checks `curr_disk_cache`, which stays null until LoadDiskCache (vk_pipeline_cache.cpp:302).
   - **State-load path:** serialize calls Shutdown(true) then Init (core.cpp:962-966). Shutdown resets the GPU (core.cpp:776) and Init builds a new one (core.cpp:651), so the new PipelineCache has id 0 and a null cache. Nothing in core.cpp calls LoadDefaultDiskResources. Then core.cpp:1019 calls SwitchDiskResources(0), reaching SwitchCache through vk_rasterizer.cpp:1033. Since 0 == 0, it returns at :161. That return logs only at LOG_DEBUG, which is why the log has no "Switching" line.
   - **Disk-cache-disabled boot:** citra_libretro.cpp:432-435 calls LoadDefaultDiskResources only when the disk cache is enabled. Upstream's libretro frontend has the same check (pristine :411); Qt (bootmanager.cpp:87) and Android (native.cpp:344) call it every time. The app's first AcquireRight then calls SwitchDiskResources(0) at gsp_gpu.cpp:945, which hits the same return at :161.
   - **Crash site:** vk_rasterizer.cpp:404 calls vk_pipeline_cache.cpp:538, which uses the null `curr_disk_cache`. With use_hw_shader off, :583 → :575 (fragment shader) and BindPipeline :373 dereference the same null pointer.
   - **Patched, cache enabled:** :169-172 creates an empty driver cache, :182 saves it, :184 loads it back. SwitchDiskCache sees a null current cache and an empty list, so it creates a ShaderDiskCache(0) and calls Init at :331. Init loads the VS/FS/GS/PL files.
   - **Patched, cache disabled:** the save returns at :271 and the load creates an empty cache at :222-223. Init returns at vk_shader_disk_cache.cpp:62, so the cache lives in memory only (Append no-ops because the file mode is NONE, :376). Either way `curr_disk_cache` is set before the first draw.

2. **Side effects of running the switch body.**
   - **Bug, overwrites the driver cache file:** during Shutdown(true), the old renderer's destructor saves its driver cache to `0000000000000000-<vendor><device>.bin` (:150). The patched path then saves the freshly created, empty cache over that same file (:182) and reads the empty file back (:184). So every state load of a .3dsx wipes the saved driver pipeline cache. This costs speed, not correctness.
   - The same overwrite already happens upstream on a .cia state load, because :182 runs while the id is still 0.
   - **Change:** at :182, write `if (curr_disk_cache) { SaveDriverPipelineDiskCache(); }`. Then the load at :184 reads the file the old renderer just saved, and the .cia case is fixed too.
   - **Applet cleanup loops:** no-ops. `prev_applet` is false when the cache is null (:339), and the list has one entry, which the loop keeps.
   - **Work started:** Init compiles VS/FS/GS SPIR-V synchronously on the emulator thread inside retro_unserialize (vk_shader_disk_cache.cpp:689, 846, 990). It queues PL pipeline builds on `pipeline_workers` (:1455-1459), not shader workers. That is the same cost as a boot. No pipeline was built with the throwaway driver cache, so replacing it at :201 is safe.

3. **Other paths to a null cache.**
   - UseFixedGeometryShader (:556), UseFragmentShader (:575) and BindPipeline/GetPipeline (:373) all read `curr_disk_cache`, so the fix covers them.
   - The trivial vertex shader path (:549) does not read it, but the same draw then calls :575 and :373. Those are covered too.
   - **A .cia (id not 0):** never hit this bug, because 0 != id lets the switch run. Its only issue is the overwrite in finding 2.
   - **Remaining gap:** if no process holds GSP rights at save time (core.cpp:1013), serialize does no switch. Draws need rights, though (gsp_gpu.cpp:647), and the next AcquireRight switches at :945. So no gap I could find.
   - **RecreateRenderer:** the libretro core calls it only for OpenGL (citra_libretro.cpp:497-499). With the disk cache disabled it would leave the cache null, since gpu.cpp:519 skips the load and the GSP right is already held (gsp_gpu.cpp:940 returns before :945). Vulkan never reaches it.
   - **OpenGL:** no bug. Its switch checks `curr_shader_manager &&` (gl_rasterizer.cpp:196).

4. **Alternatives — recommend this patch plus the save guard from finding 2.**
   - It is one file. It gives Vulkan the same check OpenGL already has (gl_rasterizer.cpp:196), and it matches upstream's own note that the cache can be null (vk_pipeline_cache.cpp:310-311). It covers both crash paths.
   - Calling LoadDefaultDiskResources in serialize after Init (around core.cpp:1010) would work; the app loader survives a state load (core.cpp:777-783). But that needs a second patch in citra_libretro.cpp:432 to cover the disabled-cache boot.
   - Null checks that return early in PipelineCache are worse. Only the vertex shader has a software fallback; the fragment shader and BindPipeline would silently drop draws.

5. **Format: OK.**
   - Context lines match source lines 1-6 and 158-164 exactly, with no CR or trailing spaces. The `+159,9` count is right, the file ends with a newline, and the notice line matches 0010's form.
   - The sha256 in NOTICES.md (9ea5c7df…) matches the current file. Update it if you edit the patch.
   - **Comment change:** both comments name only the state load. Make the notice "…no disk cache is selected yet (a state load, or a boot with the disk shader cache off, of a program with id 0)…". Add to the in-code comment: "…and the libretro boot skips LoadDefaultDiskResources when the disk cache is off." Mention that the driver cache save is skipped if you add the guard.
   - The in-code comment lines run to 113 columns; upstream's clang-format limit is 100, so wrap them.
   - core/README.md's patch table has no rows for 0010 or 0011. Add both.
