# Phase 4 as-built review: steps H (docs) and I (release tooling)

**Verdict: ready to merge after BLOCKERs B1-B2 and SHOULDs S1-S9.**

Reviewed: H = step-h @ 4ce7181, I = step-i @ 46c808e, both on base 896c2fe. I read both worktrees and the staged
release `runs/release/v0.1.0/` in I, and I merged H then I in a scratch clone. This was a read-only review: I made no
edits in either worktree and wrote nothing in MAIN except this file. I ran no emulator, no `gh` and no build-core.sh.
Paths below are given per repo: H:, I:, MAIN:.

## BLOCKERs

**B1. The README's real-scene rows say "Our core", but they measured Azahar's own core.** Owner: H.
- Where: H:README.md:24-26 (the three "Our core, real scene ..." rows, citing docs/research/spike-2-real-scene.md:32,34,35).
- What is wrong:
  - Spike 2 ran on the stock core. Its commit c806cd0 (2026-11-12 16:20) says "memory reads fail in the stock core".
  - Our core's build script did not exist until 1453741 (19:26 the same day). No real scene has run on our core yet.
- Fix:
  - Relabel the rows "Azahar's own core, real scene, ...".
  - In H:STATUS.md:28-29, say the real-scene rows are on Azahar's own core.
  - Add a STATUS Next line: "a real-scene speed row on our core (quiet machine)".
- How verified: `git log` dates of spike-2 and of build-core.sh in MAIN, plus the spike-2 text at the cited lines.

**B2. Without numpy, pytest fails to collect, so the I2 clone check and USING §18 both fail.** Owner: H.
- Where:
  - tests/python/test_api.py:4 has `import numpy as np` at module level.
  - pyproject lists numpy only as the optional extra `[numpy]`.
  - H:tools/clone_check.sh:66 installs only `pytest`, then line 67 runs the full set.
  - H:docs/USING.md:251-253 (§18) says `.venv/bin/pip install pytest`, then runs the fast set.
- What is wrong: collection errors on test_api.py even with `-m "not slow"`, so a fresh venv fails both commands.
  The README route itself is fine: the library and examples/quickstart.py never import numpy.
- Fix (inside H's files):
  - clone_check.sh:66: `pip install pytest numpy`.
  - USING §18: `.venv/bin/pip install pytest numpy` (or `pip install -e '.[numpy]' pytest`).
  - Fix §9's wording too (see S1).
  - Later, outside Phase 4: `np = pytest.importorskip("numpy")` in test_api.py.
- How verified: read test_api.py:4, pyproject's extras, emulator.py:340-345 (numpy is optional at run time), and
  clone_check.sh:66-67.

## SHOULDs

**S1. USING §9 says `screens()` "returns numpy views".** Owner: H.
- Where: H:docs/USING.md:93.
- Problem: without numpy it returns `bytes` (emulator.py:340-345).
- Fix: "numpy views if numpy is installed (`pip install '.[numpy]'`), else `bytes`".

**S2. `docs_check.py` needs Python 3.12, but the README says 3.10+.** Owner: H.
- Where: H:tools/docs_check.py:262.
- Problem: `f"... {"; ".join(...)}"` nests double quotes inside an f-string. That is legal only from Python 3.12
  (PEP 701); on 3.10 and 3.11 the file is a SyntaxError.
- Fix: `{'; '.join(failed[check][:3])}`.

**S3. clone_check reruns failures and accepts the rerun's pass, whatever failed.** Owner: H.
- Where: H:tools/clone_check.sh:67.
- Problem: it reruns `--lf` after ANY failure and accepts a pass. The plan allows a rerun only for a time-bound failure.
- Fix: rerun only when every failed test id is in a named time-bound list (for example test_state_boot). Otherwise fail.

**S4. release_check check 9 lets a short or padded zip pass.** Owner: I.
- Where: I:tools/release_check.py:362-377 (`compare_members`).
- Problem:
  - `zip(kept, mine)` stops at the shorter list, so a truncated asset, or one with extra trailing members, passes.
  - `untar_findings` only compares against the asset's own count.
- Fix: after the loop, require both iterators to be exhausted, or check `len(asset) == 1 + len(tarball) - dropped`.
  Add a plant that drops the last member.

**S5. Apply D1: quote third-party notices verbatim, and narrow check 7.** Owner: I.
- Where: I:tools/mknotices.py:160 and :275-281, and I:tools/release_check.py:217.
- Problem:
  - mknotices.py:160 replaces addresses with "[address omitted]". The visible result is Boost's Kyle Lutz notice at
    NOTICES.md:162.
  - mknotices.py:275-281 drops the OFL file's first lines and types a copyright line in their place.
  - NOTICES.md:25 claims the Boost notices are "quoted verbatim", which these two changes make untrue.
- Fix: see the D1 ruling below.

**S6. newlib's licence text is not quoted.** Owners: I and the main loop.
- Where: I:NOTICES.md:3535 says only "BSD-style, see COPYING.NEWLIB". No such file is under the devkitPro licenses
  folder.
- Problem: testapp.3dsx links newlib, and several of its BSD clauses require the notice to be reproduced in binary
  distributions.
- Fix:
  - Fetch COPYING.NEWLIB for the newlib version in devkitARM and pin its sha256.
  - Add `--newlib FILE` to mknotices and quote the file verbatim.
  - Re-stage.

**S7. A pre-existing doc lists the stock core's download URL and hash.** Owner: the main loop, before the push and I3.
- Where:
  - MAIN:docs/research/spike-1-headless-core.md:18 and :27-28 hold the stock-core asset URL and its sha256.
  - MAIN:docs/map/runners.md points readers at them ("The downloads' URLs and sha256").
- Problem: the consult's §7 says "No asset URL, no hash".
- Fix:
  - Reword the spike lines to "Azahar's libretro core for macOS, tag 2126.2, from Azahar's releases page".
  - Change the runners pointer to match.
  - Optional: extend release_check check 12 to forbid `stock-core`.

**S8. Merging H then I conflicts in two map files.** Owner: the main loop.
- Where: docs/map/code.md and docs/map/runners.md. Both are append-at-end hunks; docs/map/tools.md auto-merges.
- Fix:
  - Keep both sides.
  - In runners.md, H's block needs its own closing ``` and a blank line before I's "Step I's release tools" block,
    because the shared closing fence was common context.
  - Then run mkmap.py and map_check.py.

**S9. The I2 order must re-stage after the last commit.** Owner: the main loop.
- Problem: release_check check 10 compares the build-files asset with `git archive` of HEAD, so any later commit
  (the pins, a status move) makes it stale. The staged asset also predates core/PIN-nokeys and core/OPENSSL.md
  (made at 896c2fe), so it needs a re-stage anyway; today that shows as PEND.
- Fix: run in this order:
  1. Commit the pins.
  2. Re-run mkrelease. The core zip and the test app are deterministic, so the pins stay valid.
  3. Run release_check `--pre-push`.
  4. Push, with no commits in between.

## NICEs

- N1. H:README.md "Two cores" table, "Input, shots, SD files, savestates | yes (laz-220)" for our core.
  - D's gate ran on the stock core.
  - Cite laz-220 plus laz-320.
- N2. H:STATUS.md, two citation fixes.
  - laz-110 "builds" rests on F2's build; cite it.
  - laz-220 "on both cores" is the same issue as N1.
- N3. H:docs/USING.md:209 says "`LAZ_CORE` is the only variable that names a core".
  - `LAZ_STOCK_CORE` also names one (for tests).
  - Say "the only variable the library reads".
- N4. Exit codes differ.
  - H:tools/docs_check.py `--plant-red` returns 1 when the plants fail as they should; release_check returns 0.
  - Align them.
- N5. I:tools/fetch.sh:156: with `--lazpy-core`, an existing dylib is not re-unpacked when the zip pin changes.
  - Fix: compare a stamp of the zip's sha256.
- N6. I:tools/mkrelease.sh:134: `shasum -a 256 $_names` splits unquoted with no shellcheck disable comment.
  - Add the comment, or loop over the names.
- N7. I:tools/release_check.py, two small items.
  - `version_findings` (line 151) is redundant with the tag checks.
  - The plant-red pass accepts any FAIL, not the expected finding. Match each plant to its finding text.
- N8. I:tools/mknotices.py has no guard that every linked library's component is listed in the components.
- N9. I:NOTICES.md: add OpenSSL README's second copyright line ("Eric A. Young, Tim J. Hudson").
- N10. core/patches/0008's "-" lines quote Azahar's own decode code.
  - The same code is in the source asset's key.cpp, and the consult read 0008 and graded it GREEN.
  - Information for I3 only; no action.

## Rulings on D1, D2, D3

- **D1: confirm the main loop's default.**
  - Quote third-party notices verbatim, addresses included: the OFL file's first line and Boost's notice. Remove
    mknotices.py:160's substitution and :275-281's drop.
  - Narrow check 7 (release_check.py:217):
    - At run time, build an allow-list of the exact addresses found in the pinned upstream inputs that mknotices
      reads: the source notice blocks and the OFL file.
    - Allow those only inside NOTICES.md and zip:NOTICES.md.
    - Every other @gmail.com hit, and every private-needle hit, still FAILs.
    - Add a plant with a non-upstream gmail address in NOTICES.md.
  - Caution: if the private needle file holds a generic gmail pattern, narrow it to the maintainer's own address. Do
    not write that address into any tracked file.
  - Owner: I (S5).
- **D2: confirm the defer.**
  - A missing core gives a BootError that names the path it tried (dl/lazpy-core/...; text from core.c:91, "cannot
    load core %s: %s"), and USING §19 covers it, so it does not mislead.
  - HOST-API already flags the stale "until D" comments in azhost.h.
  - Add one STATUS Next line for both.
- **D3: accept release_check.py at 845 lines** (`plant_cases` is 44 lines). Its checks are table-shaped and
  readable. Fix check 9's hole (S4).

## Extra checks

1. **P17's interface: the two diffs agree.**
   - I's code makes our core the default:
     - _paths.py `core_path` defaults to `dl/lazpy-core/azahar_lazpy_libretro.dylib`.
     - azhost_main.c:14 `DEFAULT_CORE` is the same path.
   - Tests reach the stock core only through `LAZ_STOCK_CORE`:
     - conftest's `_stock_core_path` skips when it is unset, even under `LAZ_REQUIRE_EMULATOR=1`.
     - gate-b.sh:45 uses `${LAZ_STOCK_CORE:?}`.
     - gate_c.py uses `_paths.core_path()`. test_paths.py is new.
   - fetch.sh:
     - has part flags (`--moltenvk --headers --lazpy-core --testapp`); no flag means moltenvk plus headers;
     - takes `LAZ_RELEASE_BASE`;
     - has no stock fetch and no azahar-emu string;
     - dies on `TBD` pins.
   - H's docs say the same: README:45, :92, :99, and USING:13, :215-216, :227, :239, :261.
   - No `dl/azahar/` path is left in code.
   - After both merge, the only wrong doc lines are B1, S1, S7 and N1-N3.
   - The known "USING.md:10 says stock" issue is gone: H's rewrite replaces it (now line 13).
   - I grepped the merged tree for `stock` and `fetch.sh`. Every other hit is correct (PLAN.md's historic lines are
     the plan's record).
2. **Merge, H then I:** shared files are docs/map/code.md, runners.md and tools.md. There are two conflicts; see S8.
   Verified by a real `git merge` in a scratch clone.
3. **The consult's five conditions hold, apart from the two open items below.**
   - (a) The stock core is not fetched or shipped: fetch.sh plus release_check check 12.
   - (b) Our core ships with its source and build files: the source asset plus SOURCE.md with Azahar's tarball URL
     (allowed by the plan).
   - (c) No keys, ROMs or certificates in the release: PIN-nokeys, the strings scan, check 7.
   - (d) Notices are complete: NOTICES.md, apart from S5 and S6.
   - (e) No private data:
     - 0 `/Users/` hits in the core strings, build.inputs, SOURCE.md, NOTICES.md and testapp.3dsx;
     - testapp holds only 6 relative 'testapp/source/' assert strings;
     - the masking issue is resolved by D1.
   - Still open: S7 (the spike-1 URL and hash, outside the release but in the public repo).
4. **README and STATUS numbers.**
   - The light rows match docs/research/speed-table-e.md:27, 29, 36, 38, with their loads; the date is from line 3.
   - The real-scene numbers match spike-2:32, 34, 35, but their label is wrong (B1).
   - The first paragraph (README:6) is present and accurate.
   - STATUS:47 "exits with 2" matches `AZH_EXIT_USAGE == 2`.
5. **Stranger route.**
   - The README steps block (lines 43-49) and the build block (line 55) are real: docs_check `--emit-steps` runs them
     in clone_check.
   - The route works without numpy: quickstart checks the frame count, both PNG sizes and the A bit in the log `k=`.
   - Contributor tests break without numpy (B2).
   - examples/memory_watch.py checks rows, magic, consecutive frames and `memory.u32`; it exits 3 on `NeedsLazpyCore`.
     examples/pool_shots.py is fine.
6. **Licence notices in NOTICES.md and in the zip.**
   - Present:
     - OpenSSL's LICENSE.txt verbatim (checked against the tarball member), its copyright line and the no-NOTICE line
       (no top-level NOTICE exists);
     - faad2's Nero and Bakker lines (553, 555);
     - the four generator commits;
     - Unifont's line plus its exception text;
     - the OFL text.
   - None of spirv-tools, glslang or vulkan-headers has an Apache NOTICE file, so Apache 4(d) needs nothing.
   - Missing: newlib's text (S6).
   - Not verbatim: Boost's notice and the OFL file's first line (S5).
   - The staged release: 9 assets plus SHA256SUMS; the zip has 6 members.
   - The builder ran release_check with `--skip-pins` and got rc 0. I did not re-run it.
