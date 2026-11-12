# Release IP and legal consult: the patched core, its source and licences (ip-legal, 2026-11-13)

Consult for Phase 4 (item laz-400, step I-pre). Read: `docs/plans/phase-4.md` sections 0, 5 and 8, `core/README.md`,
`core/PIN`, `core/patches/0007` and `0008`, `~/.claude/ip-publishing-policy.md`, the toolkit IP knowledge base, and
the pinned Azahar 2126.2 source (`dl/azahar-src/unpacked/`). Also checked: B3n30/citra_system_archives (cloned to a
scratch folder, read only; none of its code was run), OpenSSL's tag `openssl-3.6.5`, the github/dmca corpus, and the
FSF, ASF and OFL texts. Nothing was built and nothing was committed. This file is the only file created in the repo.

**Not legal advice.** I am not a lawyer. These are risk gradings under the house policy: RED (never ship), YELLOW
(defensible, Guy signs off), GREEN. Each claim carries a label: *settled law*, *persuasive precedent*, *enforcement
pattern*, *community folklore* or *unresolved*.

This file is written to be published. It deliberately repeats none of the byte values, binary offsets, decryption
details or game identifiers that section 9 asks to remove from other files.

## Summary

| # | Question | Answer | Counsel? |
|---|---|---|---|
| 1 | Patched core vs rule 7 | Within rule 7: **GREEN, with conditions** (section 1) | No, while the conditions hold |
| 2 | GPL source asset | **(a)**: re-host the tarball minus the drop list. (b) is lawful but worse. (c) is **RED**. The AES/NCCH source inside (a) is fine | No |
| 3 | OpenSSL 3 (Apache-2.0) in a GPLv3 binary | Compatible. The tarball plus the licence meets Apache section 4, provided the licence text **ships inside the binary's zip**. 4(d) applies only if the tarball has a NOTICE (none at the tag) | No |
| 4 | faad2 | Carry the Nero line verbatim, keep faad2's source in the source asset, never offer the core under a non-GPL licence. No runtime banner is owed today | No |
| 5 | System archives | Original or placeholder data. Verify five things before shipping and carry the OFL and Unifont notices (section 5) | No |
| 6 | Name "libazahar-py" | Keep it: **GREEN-to-low-YELLOW**. Courtesy risk, not legal risk. Mitigations in section 6 | No |
| 7 | Scripted fetch of the stock core | **YELLOW**. Within rule 7's letter but not its "describable" clause. Recommendation: remove the pinned stock-core fetch before the first push | No, if removed. Keeping it scripted is the one item to put to counsel |
| 8 | Game title and product code in spike-2 | **Reword** before the push. Fold the change into the G8 rewrite | No |
| new | Key-material fragments, offsets and a decoding note in tracked docs (22 of 100 commits) | **Blocks the push** under rule 7 until reworded at HEAD and folded into the G8 history rewrite (section 9) | No |

## 1. The patched core and policy rule 7

**Rule 7** says: no key handling, no decryption of protected content, nothing describable as circumvention, and
3DS-era work that goes near a TPM needs counsel first.

**What I verified in the pinned source (2126.2):**
- Every key the AES engine can hold comes from one place: `GetKeysStream()`, called by `LoadPresetKeys()` and
  `InitKeys()` (`src/core/hw/aes/key.cpp:151-152`, `:292`, `:316-322`).
- The key-scrambler generator constant also comes from that stream (`key.cpp:217-218`). It is not hard-coded.
- 2126.2 has no boot-ROM or firmware key loader. A search of `src/` for those finds nothing, and no other file calls
  the key setters with file data.
- Patch 0008 makes the stream empty. The built core therefore holds no key material and has no input path for any.
  Guest software can set a KeyY, but no normal key can be derived from it.
- Patch 0007 removes the built-in ClCertA. Its fallback, the console's own ClCertA file, needs key slot 0x0D to
  decrypt, and that slot is now always empty. So the core can never present an HTTPS client certificate to a
  Nintendo server.
- A sweep of the whole tarball for embedded keys and certificates finds only the three dropped headers and cpp-jwt's
  test keys. cpp-jwt is not on the link line, and its keys are library fixtures, not Nintendo data.
- The only other large array compiled in is the 3GX plugin bootloader. It is MIT-licensed (The Pixellizer Group),
  with its assembly source in the header comment.

**Law:**
- **US, §1201(a)(2) and (b)(1)** *(settled text)*: a trafficking claim needs a technology that is primarily designed
  to circumvent, has only limited other commercial purpose, or is marketed for circumvention. A core that cannot
  decrypt anything has no circumvention function.
- **LibHac** *(enforcement pattern)*: Nintendo's notice attacked a key-free library because it was "primarily
  designed" to decrypt with keys the user supplied. Our core accepts no keys from anyone, so it sits on the far side
  of that line. It is also on the far side of stock Azahar, which embeds keys.
- **Japan, UCPA Art. 2(1)(xvii)/(xviii) and Copyright Act Art. 120-2** *(settled text)*: both need a device "with a
  function" that interferes with a technological restriction measure. There is none here.
- **EU, InfoSoc Art. 6(2) and Nintendo v PC Box (C-355/12)** *(persuasive)*: liability turns on the device's
  purpose and use. This core has no circumvention purpose.
- **Israel** *(KB, partially verified)*: no anti-circumvention law at all.

**The inert AES and NCCH code** is ordinary hardware emulation: guest homebrew uses the PS service. Its decryption
paths are unreachable without keys. "Someone could patch it back" is true of every emulator's source and is not a
property of what we ship.

**Enforcement** *(pattern, not a safe harbour)*: the github/dmca corpus has no notice naming Citra, Lime3DS, Azahar,
`ClCertA`, `ctr-common` or a 3DS keys file (searched 2026-11-13). The only 3DS-tool notice is freeShop (2016, title
keys). Azahar's own repo, which ships the key blob on by default, has been public about two years with no recorded
notice.

**Verdict: GREEN under rule 7, and not counsel-worthy as configured.** The patches take the core out of the
"near a TPM" class rather than into it. The release audit still confirms the binary itself (F2's
`keyblob_findings()` must be empty on the exact file attached).

Conditions that keep this GREEN. Breaking any one makes it counsel-worthy:
1. No key input path is ever restored: no `keys.txt`, no built-in blob, no option, no environment variable.
2. No documentation or tooling about dumping, decrypting or running commercial titles. Keep "bring your own homebrew".
3. No ClCertA, NAND or online-service features.
4. No commerce (rule 8).
5. No published extraction hints (section 9).

**Truthfulness fix (minor).** Azahar 2126.2's keys file is `sysdata/keys.txt` (`src/common/common_paths.h:83`,
`KEYS_FILE "keys.txt"`). The name `aes_keys.txt` belongs to older Citra.
- `core/README.md:25` and patch 0008's notice comment both say `aes_keys.txt`. Fix the README wording now.
- Change the patch comment only at the next `LAZPY_REV`. Editing it changes the patch hash, and so the build inputs.
- `.gitignore` covers `sysdata/` and `aes_keys.txt` but not a stray `keys.txt` elsewhere. Add `keys.txt`.

## 2. The GPL source asset

**(a) Re-host the tarball minus `LAZ_CORE_DROP`: recommended, and keep it as the default.**
- Corresponding Source = the stripped tarball + `core/patches/` + `tools/build-core.sh` + `core/PIN` + OpenSSL's
  source and build record (GPLv3 section 1).
- The binary is built from exactly that stripped tree, so the asset is the real input, not a reconstruction.
- The added member `LIBAZAHAR-PY-REMOVED.txt` is the GPLv3 5(a) / GPLv2 2(a) notice of modification. Removing files
  is a modification; the remaining members stay byte-identical with their own notices intact.

Wording for the note member: neutral and truthful, for example "removed by libazahar-py on <date>: <the three paths>
(console key and certificate data, not used by this build); externals/libressl (not used; this build links
OpenSSL 3)".
- **Drop the sha256 lines for the three key and certificate headers.** GPL asks for a notice and a date, not hashes.
  A published hash of key-bearing files only fingerprints them. *(House hygiene, not law.)* Hashes for the LibreSSL
  directory are harmless.

**(b) Point at Azahar's own asset (GPLv3 6(d)): lawful, but worse.**
- 6(d) leaves you obliged to keep the source available for as long as you offer the binary, and you do not control
  Azahar's asset.
- It is a superset of the source, and users still need our patches.
- It sends every user to a file that holds the key blob and ClCertA: an unforced link to key material.
  *Universal v. Corley* (2d Cir. 2001, *settled in that circuit*) upheld an injunction against knowingly linking to
  circumvention code. Here our purpose would be GPL compliance, so the theory is weak, but it costs nothing to avoid.

**(c) Re-host the unchanged tarball: RED.**
- It puts Nintendo's key blob and a Nintendo private key and certificate into our own release asset.
- The blob is encrypted only under a key published in the same source, so it is effectively plaintext.
- That is rules 5 and 7 together. Release assets are the first thing notices target, and a §1201 claim has no
  put-back path and is repo-fatal.

**The AES and NCCH source in (a): no problem.**
- GPL requires that source: it is part of the work we ship (inert, but compiled in).
- It is the same code every Citra-family repo has carried publicly for years, with no recorded notice
  *(enforcement pattern)*.
- It contains no key material once the drop list is applied.
- One fix for SOURCE.md: phase-4.md section 0.4 still says LibreSSL "stays inside" the re-hosted tarball. The pin
  now drops `externals/libressl`, so SOURCE.md should say it was removed. Either is lawful: LibreSSL's licences
  allow source redistribution with notices.

## 3. OpenSSL 3.6.5, Apache-2.0, in a GPLv3 binary

**Compatibility** *(settled: both FSF and ASF say so)*: Apache-2.0 code may go into a GPLv3 work. FSF calls
Apache-2.0 "compatible with version 3 of the GNU GPL" and not with GPLv2. ASF says "Apache 2 software can therefore
be included in GPLv3 projects". Shipping the core under GPLv3 only, using Azahar's "or later", is correct (G4).

**Apache-2.0 section 4:**
- **4(a), a copy of the licence:** NOTICES.md with the full text meets it, **if NOTICES.md (and the GPLv3 text) is
  inside the release zip that holds the dylib.** Recipients of the binary may never see the repo. Include OpenSSL's
  copyright line ("The OpenSSL Project Authors").
- **4(b), notices in modified files:** not applicable. We modify nothing, and the keg's SBOM lists no patches.
- **4(c), keep the notices in the source we redistribute:** met by the byte-identical tarball. Its sha256 equals
  OpenSSL's published value; I checked the `.sha256` asset on 2026-11-13.
- **4(d), NOTICE:** applies only if the Work includes a NOTICE file. The tree at tag `openssl-3.6.5` has none at the
  top level (GitHub API, 2026-11-13). The tag's top-level entries include test-only submodules (krb5, gost-engine,
  and others) that are not compiled into libssl or libcrypto. I0's member list settles the tarball itself. If it has
  no top-level NOTICE, 4(d) owes nothing.

**GPLv3 side** *(settled text)*: OpenSSL is statically linked and bundled, so it is not a System Library. Its source
and "the scripts used to control compilation" belong in Corresponding Source. `core/OPENSSL.md` should pin the
Homebrew formula (`openssl@3.rb`) at the homebrew-core commit that built the 3.6.5 bottle, with its configure line.
Bit-identical rebuilds are not required.

## 4. faad2

- **GPLv2-or-later code in a GPLv3 binary** is fine *(settled)*.
- **"Any non-GPL usage ... strictly forbidden"** restates the GPL for us. Never offer the core binary under any
  non-GPL or dual licence.
- **The Nero line** (README:22-23, every file header) is FAAD2's "appropriate copyright message" for GPLv2 2(c). Under
  GPLv3 it is a section 7(b) attribution term, which the licence permits.
  - Carry it verbatim in NOTICES.md, both in the repo and in the release zip, along with the copyright line
    (M. Bakker, Nero AG).
- **No runtime banner is owed.**
  - GPLv2 2(c) and GPLv3 5(d) apply only to interactive interfaces, and are excused when the original shows none.
  - The core is a library, and `azhost` has no about or version screen.
  - If either ever gains one, the Nero line goes there.
- **faad2's source** stays in the re-hosted tarball unchanged. It is not on the drop list.
- **Patents (informational, *unresolved / not researched*):** faad2's README warns that AAC use "may require the
  payment of patent royalties". This is not a Nintendo vector, distribution is gratis, and AAC decoders ship
  everywhere in free software. No action.

## 5. The "open source" system archives

What they actually are. Upstream's `externals/open_source_archives/Readme.md` is stale: it names one generator
commit and two archives. Each header records its own generator commit:

| Archive (header) | Generator commit | What it is | Grade |
|---|---|---|---|
| Shared font | 848af47 (2018-07-09) | Glyphs rendered from **Montserrat Regular 4.000** (SIL OFL 1.1, "Copyright 2011 - 2016 The Montserrat Project Authors", no Reserved Font Name in its name table) and **GNU Unifont 10.0.05** (GPLv2 or later with the font-embedding exception). Also 15 hand-drawn sheets replacing Nintendo's private-use symbols (commit d8667a7, "replacement characters for Nintendo custom symbols"). I viewed the sheets: crude original redraws of functional symbols (letters in circles, arrows, card suits, hand-lettered labels), not extractions | GREEN, with notice duties |
| Mii (`CFL_Res.dat`) | 5e6b5df (2019-03-09) | Placeholder data built with `mii.py -c` from `mii/custom/`: 307 models of 0 to 4 vertices, 167 blank 8x8 textures, 18 32x32 "no"-sign textures. The header decodes to a 73,600-byte RomFS holding one `CFL_Res.dat`, consistent with that (not proved byte for byte) | GREEN |
| Country list | bbe60b5 (2018-09-23) | `country.json`: country and region names in 12 languages, numeric IDs, sort orders, latitude and longitude, eShop-lock bits. No source is stated anywhere. Its shape suggests it was converted from a console's own archive with the tool's `-x` mode (*inferred, not stated*). The content is factual | GREEN to low YELLOW |
| Bad-word list | 47cdc93 (**not in** B3n30/citra_system_archives' history as of 2026-11-13; the content matches its 2d98119) | One placeholder pattern, `^badword$`, per file; the decoded header holds exactly that | GREEN |

**Law for the country list:**
- **US** *(settled)*: facts are unprotectable (*Feist*). The selection and arrangement here are dictated by the
  console's format, so merger applies.
- **Japan** *(settled text)*: facts are not works. A database work (Art. 12-2) needs creative selection or
  structure, and this structure is functional.
- **EU**: the sui generis database right reaches only makers who are EU nationals or companies (Directive 96/9
  Art. 11), and who made this data is unknown. *Unresolved, low.*
- **Enforcement** *(pattern)*: Citra and Azahar have shipped all four archives since 2018-19 with nothing recorded.

**Generator licence:** `license.txt` is GPLv2, and the scripts say "GPLv2 or any later version". Both are compatible
with the GPLv3 binary.

**OFL point** *(unresolved, low)*:
- OFL FAQ 2.2 says a format change "normally is considered modification", so the bitmap font is a Modified Version
  of Montserrat.
- OFL condition 2: each copy must carry Montserrat's copyright notice and the OFL text. Condition 5: that portion
  stays OFL.
- FSF calls the OFL a free copyleft font licence but does not list it as GPL-compatible. OFL FAQ 1.3: "Only the
  portions based on the Font Software are required to be released under the OFL."
- So the font portion stays OFL inside a GPLv3 binary. That has been upstream's posture for about eight years, with
  no dispute recorded. Not counsel-worthy.

**Verify before shipping** (I0 or the release audit):
1. The four headers in `build-src/` are byte-identical to the pinned tarball's. Record their sha256 values in
   NOTICES.
2. Decode the bad-word header: it holds only the placeholder. Decode the Mii header: it holds only `CFL_Res.dat`, at
   the size above.
3. NOTICES.md (repo and release zip) carries:
   - the full OFL-1.1 text with Montserrat's copyright line;
   - Unifont's notice (copyright line plus "GPLv2 or later with the GNU font embedding exception");
   - citra_system_archives' GPLv2-or-later notice, naming the four generator commits from the headers and noting
     that 47cdc93 cannot be found upstream.
4. **SHOULD, for Corresponding Source:** the "preferred form for modification" of a generated hex blob is arguably
   the generator plus its fonts, not the `.h` file. Azahar ships only the `.h`. As distributor we can close the gap
   cheaply: attach a snapshot of citra_system_archives at f470e0c (it contains 848af47, bbe60b5, 5e6b5df and
   2d98119) to the source asset, or as its own asset. *Unresolved* whether this is required; no enforcement ever.
5. Wording: never call these archives Nintendo's. Describe them as "open-source replacement system archives
   generated by the Citra project's citra_system_archives".

## 6. The name "libazahar-py"

**Law:**
- Azahar is not a Nintendo mark, so policy rule 10 does not apply.
- I found no registration in a web search. I did not query USPTO or EUIPO directly, so this is *unresolved*.
- Even a registered mark would allow nominative or descriptive use if the use is honest and implies no sponsorship
  *(persuasive)*: US *New Kids* and *Toyota v. Tabari*; EU TMD Art. 14(1)(c); Israel Trade Marks Ordinance s.47.
- An unregistered name supports only a passing-off claim, which needs a misrepresentation.

**The real risk is courtesy and affiliation** *(press reports, 2025-26)*. The Azahar team has publicly objected to
blurring of which build is official: the "AzaharPlus" fork's name confusion, and in October 2026 it withdrew support
from Anbernic over promotion of that fork. "lib<X>-py" reads like official bindings, and we distribute a modified
Azahar binary. Our build is the opposite of a "piracy-focused" fork (it has fewer keys than stock), which lowers the
friction.

**Keep the name, with these mitigations:**
1. The README's first paragraph says "unofficial; not affiliated with or endorsed by the Azahar project; report
   libazahar-py issues here, not to Azahar".
2. Keep the core's distinct file name and version suffix (`azahar_lazpy_libretro`, `-lazpy.1`). Never call our build
   "Azahar" alone.
3. Never use Azahar's logo or icon.
4. Decide a fallback name now, so a rename request costs an hour, not a week.
5. A courtesy note to Azahar's maintainers is optional and is Guy's call (it is also discovery).
6. Never upstream these patches without following Azahar's `AI-POLICY.md`, which prohibits undisclosed or
   substantially AI-written submissions.

## 7. Scripted download of Azahar's stock core

**Letter vs spirit:**
- Rule 7's letter: `fetch.sh` handles no keys and decrypts nothing.
- Its "nothing describable as circumvention" clause is another matter. Our repo would automate obtaining a binary
  that embeds a usable Nintendo keyset and a Nintendo private key. Our own tracked docs say so, with locations
  (section 9).

**Law:**
- §1201(a)(2) reaches anyone who "provides, or otherwise traffics in" a component.
- *Corley* extended that to knowing linking done to disseminate.
- A test-convenience fetch of a general-purpose emulator from its official source is a weak claim *(persuasive
  precedent cuts our way)*.
- But a notice on Nintendo's template only has to describe the repo plausibly, and a §1201 notice has no put-back
  path *(KB, settled mechanics)*.
- *Enforcement pattern:* no notice has ever named Azahar.

**Grade: YELLOW.**

**Recommendation:**
- P16 already makes our core the default route, so before the first push **remove the pinned stock-core URL and
  sha256 from `fetch.sh` and from the test suite's default path.**
- Tests that compare cores skip unless an environment variable such as `LAZ_STOCK_CORE` points to a file the user
  supplies.
- The contributor docs say, in prose, "to compare, download Azahar's own libretro core from Azahar's releases page
  and point `LAZ_STOCK_CORE` at it". No asset URL, no hash, nothing about what the stock binary contains.
- This costs users nothing and removes the only functional link between this repo and key-bearing bytes.

**If Guy prefers to keep a scripted fetch:**
- make it an explicit opt-in flag that is never in the README route and never in a default test run;
- never publish the section 9 material;
- treat it as the one item in this consult worth putting to counsel.

## 8. Game title and product code in `docs/research/spike-2-real-scene.md`

- **Law:** naming a commercial game you ran locally is nominative and lawful *(GREEN legally)*.
- **Hygiene:** lines 22 and 57 add a product code and revision. Line 57 also states where the local game file sits,
  which is a possession statement with no benefit to readers.
- **House lesson (2026-10-19):** prose about the maintainer's own game files belongs out of public repos.

**Recommendation:**
- **Reword before the push** to "one commercial Gen-3 GBA game, run locally (not distributed)".
- Drop the title, product code, revision and file location. Line 58's in-game place name is optional to keep.
- Fold the old lines into the G8 `--replace-text` pass, since that rewrite runs anyway (low priority).
- If Guy confirms G9 (he dumped the game from a cartridge he owns), STATUS may say "measured with a game dumped
  from the maintainer's own cartridge". The policy prefers saying so, but still without the title or code.

## 9. New finding: key-material fragments and extraction hints in tracked docs (blocks the push)

**What is in the tracked docs** (byte-window search of HEAD and all 100 commits, 2026-11-13; 22 commits carry this):
- the first bytes of the encrypted key blob from a keys-on build: `docs/plans/phase-3.md:522`;
- the first bytes of both ClCertA arrays: `docs/reviews/phase-3-review-2.md:24-25`;
- the byte offsets of the blob and the ClCertA arrays inside Azahar's downloadable stock binary and inside our early
  builds: `docs/plans/phase-4.md:67-73`, `:290-291`; `docs/reviews/phase-4-review-1.md:33`;
  `docs/status/lazpy/1-in-progress/400-phase-4-release.md:51`;
- how the blob is decoded: `docs/plans/phase-4.md:34`, `:288`; `docs/reviews/phase-4-review-1.md:22`; item 400 `:33`.

**Assessment:**
- The fragments are 8 to 16 bytes of *ciphertext*, not usable keys. There is no infringement in them.
- Together, though, the lines read as a recipe: "download this pinned asset, read at this offset, decode it this
  way". That is exactly what rule 7's "nothing describable as circumvention" and the KB's recipe tripwire (2026-10-20,
  "a hint that names where matching bytes can be found") exclude.
- History counts (rule 6), and G8 rewrites history before the push anyway, so the fix costs almost nothing.

**Fix:**
1. At HEAD, keep the facts that are public in Azahar's own CMake ("Azahar can embed a built-in key blob and a
   ClCertA; we build with the blob off, patch both out, and drop their headers"). Remove every byte value, every
   offset, and the decoding description.
2. Add the same strings to the G8 `--replace-text` file, which is kept outside the repo.
3. The gate code (`keyblob_findings()`) reads its byte windows from the local, unshipped source at run time. Keep it
   that way: never commit the windows.

## 10. What blocks the release

1. **Section 9:** reword at HEAD and fold into G8, before the first push.
2. **Section 7:** remove the scripted stock-core fetch, or Guy explicitly accepts the YELLOW (counsel optional).
3. **Release zip contents:** NOTICES.md (Apache-2.0, OFL-1.1, Unifont, faad2's Nero line, citra_system_archives) and
   the GPLv3 text go *inside* the binary's asset (sections 3-5).
4. Standing: the release audit confirms `keyblob_findings()` is empty on the exact attached binary, and that the
   source asset is (a) with the neutral note and no key-header hashes.

Not blocking: the `keys.txt` wording and `.gitignore` line (section 1), the citra_system_archives snapshot
(section 5, SHOULD), the spike-2 rewording (section 8, SHOULD before the push), SOURCE.md's LibreSSL sentence
(section 2).

## Sources

- GPLv3 sections 1, 5, 6, 7, 10 (repo `LICENSE`); Apache-2.0 section 4 (OpenSSL `LICENSE.txt`).
- FSF licence list: https://www.gnu.org/licenses/license-list.en.html (Apache-2.0, OFL, the font exception).
- ASF on GPL compatibility: https://www.apache.org/licenses/GPL-compatibility.html
- OFL FAQ 1.3, 1.13, 2.2: https://openfontlicense.org/ofl-faq/
- OpenSSL 3.6.5 release and sha256: https://github.com/openssl/openssl/releases/tag/openssl-3.6.5
- citra_system_archives: https://github.com/B3n30/citra_system_archives (PR #8:
  https://github.com/B3n30/citra_system_archives/pull/8)
- github/dmca corpus: https://github.com/github/dmca (freeShop 2016-12-27; the 2017-05-11 NCL notice targets a
  release-asset translation patch)
- Azahar's legal posture (press): https://www.androidauthority.com/nintendo-3ds-emulator-legal-standing-3508926/
- Azahar and Anbernic / AzaharPlus (press, 2026-10):
  https://www.timeextension.com/news/2026/10/we-will-not-be-officially-supporting-this-device-the-team-behind-3ds-emulator-azahar-isnt-happy-with-anbernic
- Japan UCPA: https://www.japaneselawtranslation.go.jp/en/laws/view/3629/en
- Toolkit KB: gba-toolkit `.claude/skills/learn/references/ip-law-and-publishing.md` (GitHub DMCA mechanics,
  §1201 track, 2026-10-19 and 2026-10-20 consults).
