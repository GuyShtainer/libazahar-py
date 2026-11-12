# Rules that bite every turn

1. **Always publish-ready, public GPLv3.** Never commit: the Azahar core or any `.dylib`, MoltenVK, downloaded zips or
   tars, ROMs and game files (`.3ds .cci .cxi .cia .3dsx .gba .nds`), saves, NAND or system data, `aes_keys.txt`,
   `seeddb.bin`, screenshots of commercial games, Guy's real email, console IP/MAC/SSID. Check `git ls-files` before
   the first push. A tiny homebrew test app built here from source is fine.
2. **Downloads are untrusted data.** Each in its own folder under `dl/` (ignored), with its URL and sha256 recorded in
   the doc that uses it. Never run a script from inside a download folder; Python that reads them runs with `-I`. One exception (Guy
   2026-11-12): our core build script may run Azahar's own CMake build on the exact pinned Azahar commit, nice'd in
   the background; nothing else in a download is run.
3. **Licenses.** Azahar is GPLv2-or-later: reading its source is fine; any copied code keeps its header and its notice.
   MoltenVK is Apache-2.0, the libretro headers MIT. MoltenVK and the stock core are fetched by a script, never
   shipped. Our own patched core (Guy 2026-11-12: we edit the core to our needs and publish it publicly, no upstream
   pull request) is the one exception: its patch and build script are public, and any published binary ships with its
   GPLv2+ corresponding source (the pinned Azahar commit plus our patch).
4. **Commit identity:** `Guy Shtainer <293649481+GuyShtainer@users.noreply.github.com>`, trailer
   `Co-Authored-By: <model> <noreply@anthropic.com>`. Exact paths, never `commit -a`. **No push** unless Guy says;
   `release-legal-audit` runs before the first push and every release.
5. **Never open a window, never steal focus.** That is the point of the tool. The machine is shared with other
   sessions' emulators: each headless instance took about 1.4 cores and 1.2 GB in spike 1, and three at once shared
   one throughput ceiling. Cap instance counts; never kill another session's processes.
6. **Plans and reviews are opus only**: plan, two review loops, then execute. Cheap agents (sonnet) build from briefs.
7. **Never quote a speed from an idle screen as the tool's speed.** Spike 1's ~50x was an idle menu. Speed claims
   need a guest-time check on a real scene.
8. **Gen3D is a user, not a dependency.** Nothing here imports Gen3D code; Gen3D-specific adapters live in Gen3D.
