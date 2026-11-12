# The spike's prototype host (kept as found, 2026-11-12)

`fe2.c` is the one-file C host the Gen3D spike wrote (agent a3f9c08b): it loads the Azahar libretro core, answers its
Vulkan setup through MoltenVK (no window, no surface), runs frames unpaced and writes PNG screenshots of both screens
(400x480, top over bottom). Input is a stub (returns 0); no memory reads. It is reference for the plan, not the
product. Build and run lines: `docs/map/runners.md`. Results: `docs/research/spike-1-headless-core.md`.
