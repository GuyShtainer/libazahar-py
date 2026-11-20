# release-legal-audit: libazahar-py, first push and v0.1.0 (2026-11-13)

I'm not a lawyer, and these are risk grades under the house policy, not legal advice. Anything unusual goes to ip-legal or to an attorney.

Scope: MAIN at HEAD 52bd5ec. `git diff --stat 50ac6c1..HEAD` touches only `docs/status/lazpy/1-in-progress/HANDOFF.md`. The audit covered the full history (149 commits, every ref), the 9 staged assets in `runs/release/v0.1.0/`, and the release notes. I edited no tracked file and committed nothing. Working notes are in `runs/i3/audit-notes.md`.

## Verdict

**Not shippable yet. There is one blocker, and it is in the history.** The history still holds the stock core's pinned download. Everything at HEAD and every staged asset is shippable. A few wording fixes should go in before the push.

| Surface | Verdict |
|---|---|
| Repo (HEAD tree) | **shippable**, after the SHOULD wording fixes (S1-S3) |
| History | **not shippable**: B1 needs a third rewrite |
| Core zip | **shippable**. Re-stage after B1 only if SOURCE.md's translation sentence changes; the dylib does not change |
| Azahar source asset | **shippable**. `core/PIN`'s `SRC_URL` is RISK-ACCEPT (R1) |
| OpenSSL asset | **shippable** |
| Snapshot asset | **shippable** |
| Build-files asset | **shippable**. Regenerate it after B1 (`git archive` stamps the commit id) |
| Test app | **shippable** |
| NOTICES | **shippable** |
| Docs' claims | **shippable after S1-S3** |

## release_check

I re-ran `python3 -I tools/release_check.py runs/release/v0.1.0`. Checks 1-6, 8, 9, 11, 13, 14 and 16 PASS. `history-bytes` scanned 856 blobs with 0 hits. Checks 7 and 12 skipped their needle parts because they ran without the private file. Their earlier runs are 16 of 16 PASS in `runs/i2/release_check.out`.

Check 10 (build-files) FAILs only because HEAD moved. I confirmed that the asset's sha256 equals a fresh `git archive` of 50ac6c1 (the trees are identical) and that nothing under `core/` or `tools/` changed after it. Check 7's NOTEs are the expected Homebrew OpenSSL paths and upstream licence addresses.

## Layer 1: tracked files: FINDINGS (SHOULD/INFO only)

- **227 tracked files.** No image, audio, archive, ROM, BIOS, save, key, certificate, system-data, NAND, `.dylib`, `.3dsx` or decomp file. No tracked file matches `.gitignore`. The `.gitignore` already covers `keys.txt`, `aes_keys.txt`, `seeddb.bin`, `sysdata/`, the ROM and system extensions, `dl/`, `runs/` and `build*/`.
- **No secrets or private data.**
  - No tokens and no PEM blocks.
  - No private IPv4 addresses, MACs or SSIDs.
  - No runs of 8 or more `0xNN` tokens.
  - The personal-address needle is read inside the command from the preferences file and never printed. It has 0 hits at HEAD, in every patch of history, in every commit message, and in every asset, including zip members and tarballs decompressed.
- **Commercial game title at HEAD: `docs/research/spike-1-headless-core.md:51` and `:55`.** Both lines refer to an earlier comparison by game name. They have been there since 2288e94 and survived G8b. Consult section 8 grades naming a game you ran locally as lawful, so this is **SHOULD**: reword it to "a commercial game's movie" and fold it into B1's replace file. `docs/research/spike-2-real-scene.md:58` keeps an in-game place name; the consult calls that optional (INFO).
- **`~/...` paths: INFO, keep.** About 25 plan, review and item files have them, plus `tests/gate_f2.py`, `tools/map_check.py` and `tools/release_check.py`. They hold the local username and folder layout only, nothing secret. `docs/research/libretro-py-probe.md:22` names a session scratchpad folder under `/private/tmp`. That folder is local only, but it is the kind of folder the private replace file lives in, so a generic path there is nicer. Optional.
- **The `claude.ai/artifact/...` progress-page link: INFO.** It is at `docs/status/README.md:37`, `HANDOFF.md:36` and `docs/status/lazpy/5-done/ask-01-progress-page.md:29`.
  - The page is built only from item head lines. No tracked version of `docs/progress.html` holds a G8b replacement marker or any hex, so the page never carried the rewritten material.
  - Version 5 was published at 00:41, before G8b. I could not open the artifact itself. Optionally republish it from HEAD before the push.
- **`3DPlatinum` is named at `docs/map/tools.md:31` and `docs/status/README.md:45`: INFO.** These are design-credit lines naming a sibling project. There is no code from it. Optionally say "a sibling project".
- **Tracked working files** (`CLAUDE.md`, `HANDOFF.md`, `hours.tsv` with agent ids, `progress.html`): INFO. They are tracked on purpose and are not gitignored, so this is not the class of private files tracked by mistake.

## Layer 2: history: FINDINGS (BLOCKER B1)

- **Identity: CLEAN.** All 149 commits have the no-reply address as both author and committer. There are no tags yet. `step-h` and `step-i` are ancestors of `main`. There is no remote, so nothing is SHA-fetchable on GitHub and no Support GC request is needed.
- **No binary was ever committed.** Every one of the 269 paths in history is text. The other 42 paths are status items that were moved.
- **B1: the stock core's asset URL, asset name and sha256 are still in history.**
  - The sha256 is in `docs/research/spike-1-headless-core.md` (143 commits) and `tools/fetch.sh` (140 commits, whose `CORE_VER`/`CORE_URL`/`CORE_SHA` pins form a working scripted fetch).
  - The asset name or URL also appears in old versions of `docs/plans/phase-1.md` (7 commits), `docs/plans/phase-4.md` (18) and `docs/plans/phase-a.md` (7).
  - The total is 144 of 149 commits. HEAD, commit messages and every asset hold 0.
  - Why it blocks:
    - Consult section 7 and the KB entry "Never script-fetch a third-party binary that embeds keys" both say "no pinned URL, no hash" before the first push.
    - Guy's Q1 took the default, "remove". He did not accept the YELLOW.
    - Pushing publishes every one of these commits, including a working fetch.sh with pins. HEAD's plans also say that this binary holds the key blob and the ClCertA arrays (`docs/plans/phase-4.md` section 0.6 and its section 8 row). Together that is "pinned URL plus hash plus what it contains", which is the pattern the consult removes.
    - After a push, history cannot be fully cured: forks and SHA fetches keep it. Before a push it costs seconds.
  - **Fix: a third `git filter-repo` pass (G8c) before the push.** It uses phase-i.md 8.1/8.1b's procedure and the same private replace file.
    - Replace these literally: the stock asset URL in both its literal form and its `$CORE_VER` template form; the asset file name in every version form; the stock sha256; and the `CORE_VER`/`CORE_URL`/`CORE_SHA` lines.
    - Generate the lines by command from `git show` of the pre-083cc56 spike-1 and the pre-5e80e40 fetch.sh, and never print them.
    - **Do not** use a rule that matches the generic `azahar-emu/azahar/releases/download` prefix. HEAD's `core/PIN`, `docs/plans/phase-f1.md:61`, SOURCE.md and `tools/docs_check.py` need it, and the HEAD tree must stay unchanged.
    - Add the spike-1 title lines (Layer 1).
    - Afterwards, check for 0 hits for every replaced string in every commit and message, check that the HEAD tree hash is unchanged, write `docs/commit-map-g8c.tsv`, and re-run `release_check --pre-push` with the needle file.
  - The only alternative is that Guy explicitly risk-accepts B1 (R0 below).

## Layer 3: release surface: CLEAN (two INFO)

- **Core zip.** It has 6 members: `COPYING-azahar.txt` (GPLv2), `LICENSE` (GPLv3), `NOTICES.md`, `SOURCE.md`, `build.inputs` and the dylib.
  - The dylib is 21,828,992 bytes. That is R2's gated 01:06 build, and `cmp` shows it is identical to `build-core/`'s copy. Check 2 PASS means `keyblob_findings()` is empty on this exact file.
  - My own window search, counts only, with windows read at run time from the reading copy:
    - 256 16-byte windows of each of the three arrays in the dylib;
    - 32 windows per member of every tarball asset (20,122 + 1,045 + 16 + 5,889 members);
    - 64 windows per loose file;
    - hex-text forms of the windows as well.
    - Result: **0 hits**.
  - `otool -L` lists system libraries only. There is no MoltenVK; its 3 strings are upstream log texts, not the library. There are 0 `libressl` and 0 `/Users/` strings.
  - Key-file names: `keys.txt`, `aes_keys`, `boot9` and `title.keys` give 0 hits. One `seeddb.bin` path string is upstream's seed loader, and it is inert because there are no keys.
  - The ClCertA and ctr-common strings are log texts that report a missing file. The old fallback text is gone.
  - The Nintendo CA issuer strings come from `unique_data.cpp` and are names only.
  - I checked `ecc.cpp`, `rsa.cpp` and the AES code: the root ECC key and the RSA slots come only from `GetKeysStream()`, which is now empty, and no key literals are compiled in.
  - The OpenSSL Homebrew directories and `build.inputs`' `openssl_prefix=` are the expected values.
- **System archives.** I0's five checks (`runs/step-i/i/rows.md`) all pass:
  - the 4 headers are byte-equal to the tarball's members;
  - the bad-word list is a placeholder only, and the Mii archive is a 73,600-byte RomFS holding only `CFL_Res.dat`;
  - all four generator commits are recorded;
  - NOTICES carries the required texts;
  - the snapshot is attached.
- **Admission text: none.** The release notes, SOURCE.md and NOTICES never call anything Nintendo's, and NOTICES has 0 "Nintendo" strings at all.
- **Patch 0008: INFO.** Its removed (`-`) lines show upstream's decode code. The same code is in the unchanged `key.cpp` inside the source asset. It is upstream GPL code with no blob anywhere, and the consult read 0008. Acceptable.
- **The size baseline holds.** Our earlier keys-off build (21:09) was 19,145,936 bytes. The gated build is larger only by the static OpenSSL, and none of the arrays is present.

## Layer 4: circumvention surface: CLEAN

All five of the consult's conditions hold:
- **Key input path:** none. 0008 makes the stream empty, the blob is OFF and its header is dropped.
- **Docs on dumping or decrypting:** none. docs_check PASS.
- **ClCertA, NAND or online-service features:** none of ours. 0007 removes the fallback, and slot 0x0D can never be set.
- **Commerce:** none. There is no `.github/`, no funding file, and no donate or sponsor text.
- **Extraction hints:** 0 hits in history-bytes and in my scans.

`LAZ_STOCK_CORE` is **GREEN**. It is the exact form the consult recommends: a path the user supplies, with only a prose pointer to Azahar's releases page in `docs/USING.md:254` and the README's table. There is no URL, no hash, and nothing about what the binary contains. The tests skip when it is unset.

## Layer 5: docs and claims: FINDINGS (SHOULD)

- **Present and correct:**
  - The README's first paragraph says "Unofficial: not affiliated with or endorsed by the Azahar project. Report libazahar-py issues here, not to Azahar."
  - There is a Nintendo trademark and non-affiliation line.
  - No images are tracked, and no Azahar logo is used.
  - The docs never claim "clean room".
  - Nominative names only.
  - "macOS 15 or later" appears everywhere.
  - Idle-screen speeds are never quoted.
  - The release notes contain no admission text.
- **S1 (SHOULD): README vs STATUS contradiction.**
  - The README's three real-scene rows say "one commercial game's 3D field scene, run locally" on Azahar's own core, which is the key-bearing one.
  - STATUS's "Considered and dropped" says "Commercial games in tests or docs: homebrew only".
  - What actually ran was Gen3D, a homebrew app, drawing a scene from a GBA game. As written, the rows read as a commercial 3DS title on the stock core, which brushes consult condition 2.
  - Reword the rows to "Gen3D (homebrew) drawing a 3D scene from a GBA game run locally, not distributed", or drop the rows until the quiet-machine re-measure on our core exists.
- **S2 (SHOULD): "no keys" is literally untrue for the release.**
  - The README's Legal section says the repository and its releases contain no "keys". The release notes' "Homebrew only" section says "no keys, no certificates and no system files are included".
  - The Azahar source asset carries cpp-jwt's test keys (10 members), and the OpenSSL tarball carries 88 test key files. The core also compiles in open-source replacement system archives.
  - Change the wording to "no console keys, no Nintendo certificates, no Nintendo system files" (or "no keys or certificates from Nintendo"). The release-notes edit costs nothing because the body is a draft. The README edit is one commit before the push.
- **S3 (SHOULD, cheap): stale statement in phase-4.md.** `docs/plans/phase-4.md` section 0.6 says the stock core is the binary "which `tools/fetch.sh` downloads today", which is no longer true. Reword it to the public fact only: "Azahar's default build embeds the key blob and ClCertA (its CMake default)". Do the same for the section 8 "STOCK holds..." row.
- **INFO:**
  - SOURCE.md gives Azahar's original tarball URL and sha256 as provenance, and the note member gives its sha256. Neither is a hash of the key or certificate headers, so this meets consult section 2. It is a provenance pointer, not our source offer. Acceptable.
  - SOURCE.md's "translate with g8, then g8b" sentence will need "then g8c" after B1. Either regenerate it with mkrelease, which changes the zip's sha and therefore fetch.sh's `LAZPY_CORE_SHA`, or accept that the g8c map in the repo completes the chain.
  - `core/README.md:25` names `sysdata/keys.txt` as "never read". That is the consult's own wording fix and is fine.

## Layer 6: naming and trademark: CLEAN

- **`libazahar-py` is GREEN-to-low-YELLOW**, as the consult found. The mitigations are in place: the first-paragraph disclaimer, the distinct core file name `azahar_lazpy_libretro` with the `-lazpy.1` suffix, no logo, and the AI-POLICY line in STATUS.
- **The fallback `lazpy` (Q8) is fine.** It does not contain the full upstream name. If Azahar ever asks, the core file name can keep `azahar_lazpy` (marking a modified version is what the GPL wants).
- I did not check the fallback against PyPI. PyPI is out of scope.
- No trademark filing, no merchandise, no Nintendo trade dress, and no live-service feature.

## Layer 7: dependencies and licences: CLEAN

- **OpenSSL against Apache-2.0 section 4:**
  - 4(a): the licence text and "The OpenSSL Project Authors" are in NOTICES inside the zip, next to the GPLv3 text.
  - 4(b): not applicable, since nothing is modified.
  - 4(c): met. The tarball's sha256 equals OpenSSL's published value.
  - 4(d): moot. There is no top-level NOTICE (`LICENSE.txt` only).
  - `core/OPENSSL.md` pins the formula's sha256 and path, quotes its configure arguments, gives the bottle's sha256 and both `.a` hashes, and labels the rebuild recipe as untested. This meets GPLv3's scripts clause for a bottle.
- **NOTICES:** the repo, asset and zip copies are byte-identical. It carries:
  - all 9 patches;
  - Azahar GPLv2+;
  - the 8 holders of third-party notices in `src/`;
  - every component on the link line;
  - faad2's Nero line (twice) and Bakker's copyright line;
  - OFL-1.1 in full, with Montserrat's copyright line;
  - Unifont's notice with the font embedding exception;
  - the archives section, with 4 header sha256 values, the 4 generator commits, the 47cdc93 note and f470e0c;
  - the test-app section, with COPYING.NEWLIB verbatim;
  - a "Not included" section.
- **Upstream addresses:** the 23 address-like strings are upstream authors' addresses inside their own licence texts.
- **INFO:** FFmpeg's verbatim header licence says OpenSSL is GPL-incompatible. That is FFmpeg's stale text about the pre-3.0 OpenSSL licence. Optionally add one sentence: "OpenSSL 3 is Apache-2.0, compatible with GPLv3".
- **Snapshot:**
  - It has generator scripts (GPLv2+ `license.txt`), the two fonts, placeholder Mii art, the hand-drawn symbol sheets and a placeholder bad-word list.
  - It does not contain OFL.txt itself. Montserrat's name table carries the copyright, an OFL statement and the URL, and NOTICES (inside the zip and as an asset) carries the full OFL text. INFO.
  - **New finding:** `shared_font/code_manifest.json` (732 KB) is a bcfnt manifest: a glyph map plus font metrics. Its shape matches what `bcfnt.py` writes on extraction. That suggests it came from a console's shared font (*inferred*, the same as the consult's inference about `country.json`). Its content is functional and factual: code points to indexes, plus metrics. Grade: GREEN-to-low-YELLOW, like the country list. No action.
- **Test app:**
  - 151,540 bytes, identical to `build/testapp.3dsx`, with 0 `/Users/` strings.
  - The digit glyphs are our own 3x5 font (`font.c`), and the author is "libazahar-py". The SMDH icon is libctru's default icon.
  - The only foreign strings are newlib build paths from devkitPro's maintainer.
- **Source and decomp:** no decomp code. The test fixtures are synthetic: our own test app.

## Remediation list (ordered)

1. **BLOCKER B1:** do the third history rewrite (G8c) before any push, as Layer 2 describes.
   - Afterwards: write `docs/commit-map-g8c.tsv` and a map line; run `release_check --pre-push` with the needle file; re-run `mkrelease`, which regenerates the build-files asset and, if SOURCE.md's sentence is updated, the zip and fetch.sh's pin.
   - Delete the stale local clone `runs/clone-i2/repo/`, which holds the old history, and the step-h/step-i branches, or push only `main` and the tag.
   - Nothing is public, so no Support GC is needed.
   - R0 (only instead of the fix): Guy signs off that the history keeps a working pinned fetch of a key-bearing binary.
     - The consult calls this the one item worth putting to counsel.
     - Realistic worst case: a §1201-framed notice against the whole repo. That gets no cure window and no put-back, and the notice stays public in github/dmca forever.
     - Not recommended, given that the fix takes seconds.
2. **SHOULD S1:** reword the README's real-scene rows (or drop them) so that they agree with STATUS's "homebrew only" line.
3. **SHOULD S2:** change "no keys / no certificates / no system files" to "no console keys, no Nintendo certificates, no Nintendo system files" in the README and in the release notes before publishing.
4. **SHOULD:** reword `docs/research/spike-1-headless-core.md:51` and `:55` (the game title) at HEAD, and put them in B1's replace file.
5. **SHOULD S3:** remove `docs/plans/phase-4.md` section 0.6's "which tools/fetch.sh downloads today" and keep only the public CMake fact. Do the same for the section 8 STOCK row.
6. **RISK-ACCEPT R1** (Guy signs per item): `core/PIN`'s `SRC_URL` makes `tools/build-core.sh`'s default route download Azahar's unchanged tarball, which holds the key and certificate headers, and then delete them before compiling.
   - It is defensible: the input is GPL source, the key material is deleted unused, and the deletion itself shows the opposite of circumvention intent. Every Citra-family packager does the same.
   - Realistic worst case: a notice naming the build script. That would be a partial-repo notice with a cure window of about one business day; the cure is to flip the default pin.
   - Fix at the next `LAZPY_REV`: make `core/PIN-nokeys` (our stripped asset) the default. Changing it now would break `build.inputs`' `pin=`/`script=` hashes.
7. **NOTE / INFO:**
   - Optionally republish the progress artifact from HEAD.
   - Optionally make the scratchpad path generic at `docs/research/libretro-py-probe.md:22`.
   - Optionally write "a sibling project" for `3DPlatinum`.
   - Optionally add an OpenSSL-3 sentence after FFmpeg's quoted text.
   - The tag must point at the commit the build-files asset was archived from, or the asset must be regenerated (check 10).
   - Patch 0008's comment `aes_keys.txt` waits for the next `LAZPY_REV` (known).
8. **If a notice ever arrives:** cure, don't counter-notice. Delete the named file or asset at once. Keep the questionable parts deletable: `core/PIN`'s URL is one line, and the source and core assets can each be deleted on their own.

## Proposed KB entries (for the main loop; I did not edit the tracked KB)

- **2026-11-13, history counts for the scripted fetch, too:**
  - Removing a pinned fetch of a key-bearing third-party binary at HEAD is not enough before a first push.
  - On libazahar-py the stock core's URL and sha256 sat in 144 of 149 commits (fetch.sh pins, spike-1 notes and three plans) after two rewrites aimed at other material.
  - Remedy: a filter-repo pass with literals generated by command; never use the generic `releases/download` prefix, which HEAD's source pin needs.
  - Basis: the consult's section 7; policy rule 6.
- **2026-11-13, citra_system_archives' `shared_font/code_manifest.json`:**
  - It is a bcfnt manifest (a glyph map plus metrics) in the shape of `bcfnt.py`'s extraction output, so it is likely derived from a console font (*inferred*).
  - It is factual and functional: GREEN-to-low-YELLOW, like `country.json`.
  - The snapshot has no OFL.txt, so ship the OFL text beside it (NOTICES).
  - Source: the snapshot at f470e0c, `shared_font/bcfnt.py:291-292`.
- **2026-11-13, "no keys" claims:**
  - Re-hosted upstream source tarballs carry third-party test keys: cpp-jwt in Azahar, and OpenSSL's `test/certs`.
  - Release text should say "no console keys / no Nintendo certificates", not "no keys".
