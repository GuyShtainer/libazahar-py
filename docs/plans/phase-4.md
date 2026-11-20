# Phase 4, release: the phase plan (item laz-400)

Opus phase plan, **revision 2 (final)**, 2026-11-13. It takes in review 2 (docs/reviews/phase-4-review-2.md: 4
blockers, 9 should fix, 7 nice; verdict "ready after revision 2, no third review"), the ip-legal consult
(docs/reviews/release-ip-legal.md, 2026-11-13, sections 1-10), Gen3D's first-use friction (Gen3D's
docs/phase2-safe/LAZPY-TRY-1.md:46-58) and Phase 3's F2 diff (worktree ../libazahar-py-f2, not merged yet).
Revision 1 (00:38-01:02) took in review 1 (`docs/reviews/phase-4-review-1.md`), Phase 3 review 2's asks and Guy's
rulings G3 (OpenSSL 3) and G8 (history rewrite). There is no third review: the joint as-built review (phase-h.md 12,
phase-i.md 12) catches the rest. Steps: H (laz-410, `docs/plans/phase-h.md`) and I (laz-420,
`docs/plans/phase-i.md`). Each brief is complete on its own for one sonnet builder in its own worktree. This file is
the index: goal, order, checkpoints, file ownership, merge plan, departures from PLAN.md, the interfaces taken from
Phases 1-3, the questions for Guy (section 7), the checked facts, risks, hours and the hour-saving pass. Section 13
maps every finding of review 1, review 2 and the consult to where it went; section 14 says what revision 2 changed.

**Never write a key or certificate byte value, its offset in any binary, or how the key blob is decoded**, in any
plan, doc, script, report or commit message (consult section 9). Say "the key blob" and "the ClCertA arrays". The
gate code reads its byte windows from the local, unshipped source at run time and never commits them.

Contract: `docs/PLAN.md` section 2.7 (the release paragraph), section 3's Phase H (PLAN.md:324) and Phase I (:330)
paragraphs, section 5 (out of scope: CI, PyPI, Windows/Linux). (The step item files still point at :317 and :323;
the main loop fixes those pointers when it moves the items.) Where a brief disagrees with PLAN.md on a goal, PLAN.md
wins and the builder stops and reports, **except for the approved departures** (Phase 2's P1-P6, Phase 3's P7-P8 and
its step-0 "P9b", and this plan's P9-P19 in section 5).

Inputs: main at bd62873 (2026-11-13). Phases 1 and 2 are done. Phase 3's step 0 ("P9b") is committed as 7c33f38
(799e8c3 before G8) and its build ended 01:06 with exit 0 (`build-core/build.inputs`: `head=799e8c3...`,
`clean=yes`). G8 is done (01:06-01:08, 6898a4b; section 0.5). The consult's section 9 material was reworded at HEAD
(776e8da). Phase 3's E (step-e, E1 at a74aaec) and F2 (step-f2, uncommitted in its worktree) are running; G has not
started. Step 0 as built (review 2 section A): patch 0007 (no default ClCertA), patch 0008 (load no keys), the drop
list `LAZ_CORE_DROP` in `core/PIN` with **four** entries (`src/core/hw/default_keys.h`, the two
`src/core/hle/service/http/ctr-common-1-*.h` headers and the **directory** `externals/libressl`), a static OpenSSL 3
(`OPENSSL_VERSION=3.6.5`, `OPENSSL_PREFIX=/opt/homebrew/opt/openssl@3`, resolved with `cd -P` to
`/opt/homebrew/Cellar/openssl@3/3.6.5`; the override is `LAZ_OPENSSL_PREFIX`) instead of the bundled LibreSSL (G3),
and `build-core/build.inputs`. F2 gates it with `keyblob_findings()`. **Phase 4 does not rebuild.** Most of what
Phase 4 documents is not merged yet, so section 6 marks each row holds or planned, and both briefs start with a step 0
that checks the planned rows against the merged code. If the code differs from a row, the builder follows the code
and reports the row; if a row's feature is missing or its gate failed, the docs say "not done" for it (never a claim).

Hours are agent wall time (PLAN.md's unit). Machine time (downloads, the clone run, example runs) and Guy's time are
not counted.

## 0. What reshapes this phase (read first)

1. **The key blob** (rev 0's finding, confirmed by review 1 A): Azahar's `ENABLE_BUILTIN_KEYBLOB` defaults ON and
   puts `default_keys_enc[]` (SRC `src/core/hw/default_keys.h`, read by
   `src/core/hw/aes/key.cpp:302-312`) into the core. `default_keys.h` carries a "GPLv2 or later" header; a licence
   header does not make console keys shippable (N9). P9 (`-DENABLE_BUILTIN_KEYBLOB=OFF`, `-ffile-prefix-map=$PWD/=`)
   is done (e40e59c; the 21:09 build: cache `OFF`, the array absent, 0 `/Users/` strings).
2. **Nintendo's ClCertA** (review 1 B1): `src/core/hle/service/http/ctr-common-1-cert.h` and `ctr-common-1-key.h`
   (an HTTPS client certificate and its private key, AES-encrypted under key slot 0x0D) are included with no `#ifdef`
   (`http_c.cpp:37-38`) and used as the fallback at `http_c.cpp:2281-2289`. Both arrays are in the 21:09 build.
   Phase 3's P9b removes them (patch 0007), deletes the two headers from the build tree (`LAZ_CORE_DROP`), and F2's
   `keyblob_findings()` gates their absence. Revision 0's line "ClCertA is loaded from the user's NAND, not embedded"
   was wrong and is gone from section 8.
3. **Key loading** (review 1 S4): patch 0008 makes `HW::AES::GetKeysStream()` (`key.cpp:292-314`) return an empty
   stream, so the published core neither holds nor accepts console keys and cannot run an encrypted title. Homebrew
   `.3dsx` needs no keys; F2's gate proves it. Default yes (Phase 3's Q6). Azahar 2126.2's keys file is
   `sysdata/keys.txt` (`src/common/common_paths.h:83`); patch 0008's own comment says `aes_keys.txt`, the older
   Citra name. `core/README.md` says so at HEAD; the patch comment is corrected only at the next `LAZPY_REV` (editing
   it changes the patch hash and so `build.inputs`; no rebuild for this alone, consult section 1). `.gitignore`
   lists `keys.txt` (line 47).
4. **OpenSSL 3 instead of LibreSSL** (Guy G3, "Switch to OpenSSL 3"): LibreSSL's OpenSSL and SSLeay licences are
   GPL-incompatible on their texts (COPYING:17-72, :74-132, :127-131). Step 0 links Homebrew's static
   `libssl.a`/`libcrypto.a` (OpenSSL 3.6.5, Apache-2.0, GPLv3-compatible) through `USE_SYSTEM_OPENSSL`, from the
   keg's real path `/opt/homebrew/Cellar/openssl@3/3.6.5` (`build.inputs`' `openssl_prefix=`; no build file names
   `/opt/homebrew/opt/`). So Phase 4 ships **OpenSSL's exact source**, the upstream release tarball
   `openssl-3.6.5.tar.gz` pinned by sha256, as part of the Corresponding Source (P14); carries OpenSSL's Apache-2.0
   licence verbatim, with "The OpenSSL Project Authors" copyright line, in NOTICES.md **inside the core's zip** as
   well as in the repo (Apache-2.0 4(a), consult section 3); and a NOTICE file's text only if the tarball has one
   (4(d); the tag has none at its top level, consult section 3; I0 settles it from the tarball's member list).
   LibreSSL is the drop list's fourth entry, so **the stripped tree and our source asset hold no LibreSSL at all**
   (review 2 B1). SOURCE.md and NOTICES say "Azahar's original tarball also contains the bundled LibreSSL; we
   removed it with the three headers". `keyblob_findings()` proves it absent from the link line, the `.o.d` files and
   the binary's strings.
5. **G8 is done (a record).** One plan line had named the local part of Guy's personal address (review 1 B2; Guy
   G8, "Rewrite before push"). The main loop rewrote history 01:06-01:08 (6898a4b): 20 commits rewritten (15d0323
   became 1844a5d, and the 19 after it), 98 commits before and after, HEAD's tree unchanged, identities unchanged, no
   `refs/replace`, fsck clean, 0 hits in every commit and message; `step-c` and `step-d` kept their SHAs. The map is
   `docs/commit-map-g8.tsv` (20 rows), pointed at from `docs/map/README.md`. Old SHAs in text stay; the maps
   translate them (`build.inputs`' `head=799e8c3` is 7c33f38 now). One duty stands: nothing committed before the
   push may bring the needle back (`release_check` checks `private` and `repo` with the needle file, and
   `--pre-push`). phase-i.md 8.1 is the procedure for any further pass.
6. **The stock core carries the blob and ClCertA too, and our script fetched it.** Azahar's default build embeds the
   key blob and the ClCertA arrays (its CMake default). The README's default route is **our core and the test app
   from our release** (P16). The consult
   grades the scripted stock fetch **YELLOW** (section 7): within rule 7's letter, not its "describable" clause.
   **Default (P17):** before the first push, remove the pinned stock-core URL and sha256 from `tools/fetch.sh` and
   the stock core from every default path (the library's and `azhost`'s default core, the test suite's fixtures and
   gate scripts); tests that compare cores skip unless `LAZ_STOCK_CORE` names a file the user downloaded; the
   contributor docs say in prose where to get Azahar's own core, with no URL, no hash and nothing about what the
   binary contains. **Guy may instead accept the YELLOW** (Q1 in section 7): then a `--stock-core` flag stays as an
   explicit opt-in, never in the README route and never in a default test run.
7. **The consult (2026-11-13) sets the release's conditions.** The patched core is **GREEN** under rule 7 while five
   conditions hold (consult section 1); section 0.9 makes them standing checks. The source asset is (a), the
   tarball minus the drop list, with a neutral note and **no hashes of the key and certificate headers** (section 2).
   OpenSSL is fine if its licence text ships inside the zip (section 3). faad2's Nero line goes verbatim into NOTICES
   (section 4). The system archives need five checks before shipping and OFL-1.1, Unifont and citra_system_archives
   notices (section 5). The name stays, with mitigations: an "unofficial; not affiliated with or endorsed by the
   Azahar project" first paragraph, never Azahar's logo, a fallback name decided now, a courtesy note at Guy's
   choice, and no upstream patch without Azahar's AI-POLICY.md (section 6). Spike 2's game lines are reworded
   (section 8). Byte values, offsets and decode notes in tracked docs **block the push** until reworded at HEAD
   (done, 776e8da) and removed from history (G8b, section 0.8).
8. **G8b, a second history rewrite (P18).** 22 of 100 commits carry the section 9 material, and spike 2's research
   file names a commercial game, its product code and where the game file sits (consult section 8). The main loop
   rewrites them out with `git filter-repo --replace-text/--replace-message`, from a replace file kept **outside the
   repo** in the session's private folder (its path is never written in the repo), **after Phase 3's worktrees are
   merged and removed and before Phase 4's worktrees are made** (so no branch but `main` is rewritten), and before the
   first push. Then docs/commit-map-g8b.tsv joins the G8 map. Procedure: phase-i.md 8.1b.
9. **Standing checks for the consult's conditions** (section 1's five, kept cheap):

   | Condition | Standing check |
   |---|---|
   | 1. No key input path, ever | `release_check` check `keyblob` (`keyblob_findings()`: 0008 in `build.inputs`, no blob, no windows, no ClCertA string) on the exact attached binary; check `repo` fails on `keys.txt`, `aes_keys`, `seeddb`, `boot9`, `title.keys` in tracked code (`host/`, `python/`, `testapp/`, `examples/`, `tools/fetch.sh`); `docs_check` forbids the same words in the docs |
   | 2. No docs on dumping, decrypting or running commercial titles | `docs_check` forbids `decrypt`, the key-file names and `ClCertA`; the as-built review's legal item |
   | 3. No ClCertA, NAND or online features | patch 0007 and check `keyblob`; the review's legal item |
   | 4. No commerce | `docs_check` forbids `patreon`, `ko-fi`, `donate`, `sponsor`; check `repo` fails on a tracked `.github/FUNDING.yml` |
   | 5. No published extraction hints | check `history-bytes` (new: hex-text windows of the three arrays, made at run time from the local source, searched in every commit, counts only); check `repo` fails on any tracked `.md` holding a run of 8 or more `0xNN` tokens |

## 1. Goal and the two steps

Goal: a public GitHub repo `GuyShtainer/libazahar-py` and a first release that a stranger can use from the README
alone, that says nothing it has not measured, that ships no key, certificate or private string, and that meets every
licence obligation of the binary it ships, with the legal audit saying shippable. Push and publish only on Guy's word.

| Step | Delivers | Gate (headless, this Mac) | Hours |
|---|---|---|---|
| H, laz-410 | `README.md` rewritten (its first paragraph: "unofficial; not affiliated with or endorsed by the Azahar project"); `STATUS.md`; `docs/USING.md` finished (with Gen3D's four lines); docs/HOST-API.md; `examples/quickstart.py` (= the README block), `pool_shots.py`, `memory_watch.py`, `examples/README.md`; `tools/docs_check.py`; `tools/clone_check.sh` (the fresh-clone run, used at I2 and I5) | `python3 -I tools/docs_check.py --allow-missing NOTICES.md` passes and `--plant-red` fails on each plant; the three examples on this Mac (quickstart on our core and, with `LAZ_CORE` at MAIN's local stock file, on the stock core; pool; memory on both); `sh -n tools/clone_check.sh` and its `--dry-run` | 0.50 |
| I, laz-420 | `NOTICES.md` (generated: link inputs, DEPS externals, Azahar `src/` notices, OpenSSL 3, the system archives with OFL-1.1 and Unifont); `tools/mknotices.py`, `tools/mkrelease.sh`, `tools/release_check.py`; `core/PIN-nokeys`, `core/OPENSSL.md`; `tools/fetch.sh` part flags, its stock part removed (P17); the default core path in `python/libazahar/_paths.py` and `host/azhost_main.c`, the stock fixture and gate defaults in `tests/` (P17); one `-ffile-prefix-map` line in `testapp/Makefile` (B4); docs/release-notes/v0.1.0.md; `core/README.md` licence lines; the version in `pyproject.toml` and `python/libazahar/__init__.py` | `python3 -I tools/release_check.py runs/release/v0.1.0 --skip-pins` passes and `--plant-red` fails on each plant; `fetch.sh --lazpy-core --testapp` against a `file://` base verifies, refuses a flipped byte, downloads nothing on a second run; the fast pytest passes; `strings -a build/testapp.3dsx \| grep -c /Users/` is 0 | 0.75 |
| Main loop and legal agents | done: the ip-legal consult (I-pre), G8, the section 9 rewording at HEAD; to do: spike 2's rewording at HEAD, G8b, two downloads, I2 (test app built clean, stage, pins commit, checks, the fresh clone of main with the full suite), I3 audit, I5 after publishing | section 2 | 0.62 |

Phase total: H 0.50 + I 0.75 + one joint as-built review 0.2 + main loop and legal agents 0.62 + review loops 0.4 =
**about 2.5 h**, against PLAN.md's 0.5 + 0.6 = **1.1 h** (plus loops PLAN counts separately). Section 9 names the
over-run per step: the key blob and ClCertA, generated notices, OpenSSL's source, the two history rewrites, and the
consult's conditions (the stock core out of every default, the archive and font notices, the standing checks).

## 2. Order, checkpoints and the parallel split

```
Done: I-pre (the consult, docs/reviews/release-ip-legal.md); G8 (01:06-01:08, 6898a4b); the section 9 rewording
  at HEAD (776e8da); `brew pin openssl@3` (01:04)
Before launch (main loop, in this order):
  1. Phase 3 merged (E, F2, G), its phase-end suite passed; F2 gated step 0's core (0007, 0008, the drop list,
     OpenSSL 3, build.inputs); every worktree but MAIN removed (`git status --porcelain --ignored` empty in each)
  2. spike 2's game lines reworded at HEAD (consult section 8; phase-i.md 6), committed
  3. G8b: the second history rewrite (phase-i.md 8.1b); docs/commit-map-g8b.tsv; checks re-run
  4. downloads (phase-i.md 6, I-pre): OSSL if not there yet; the citra_system_archives snapshot (SNAP); the font
     licence texts only if SNAP lacks them
  5. the launch message says: Q1's answer (default: remove the stock fetch), G2 (a), the consult's verdict (GREEN)
  |
  H builder (sonnet, ../libazahar-py-h, step-h)        I builder (sonnet, ../libazahar-py-i, step-i)
  |  H0: seed, link OURS, check section 6's rows       |  I0: seed, link OURS; rows; keyblob_findings() empty
  |  H1: examples, docs_check, clone_check.sh,         |      (else STOP); KEG path; the five archive checks;
  |      README, STATUS, USING, HOST-API; runs          |      the stock-core hits in code and tests
  |  ENDS ITS RUN: "H1 done"                            |  I1: P17 code, the testapp prefix map, mknotices,
  |  main loop commits H1 on step-h (+ map lines)       |      mkrelease.sh, release_check, fetch.sh, OPENSSL.md,
  |                                                     |      PIN-nokeys, notes; stage and check
  |                                                     |  ENDS ITS RUN: "I1 done"
  |                                                     |  main loop commits I1 on step-i (+ map, rules.md 3 lines)
  v_____________________________________________________v
  one opus as-built review over both diffs (phase-h.md 12, phase-i.md 12); fixes by the resumed builders; commit
  merge step-h, then step-i, into main; item 410 (Evidence: H1's gates) moves; worktrees removed (porcelain empty)
                         |
  I2 (main loop, MAIN, 0.15 h): make testapp in a clean env; tools/mkrelease.sh v0.1.0; fill fetch.sh's pins from
     the staged files and commit; release_check (with the needle file); docs_check (no --allow-missing);
     tools/clone_check.sh on a fresh clone of main with LAZ_RELEASE_BASE=file://.../runs/release/v0.1.0
     (background; the README steps, the build block, the full pytest on the default core, our core)
  I3: release-legal-audit on main + its rewritten history + runs/release/v0.1.0
  I4: BLOCKERs -> the I (or H) builder resumed -> re-stage, re-check, re-audit the changed items only
                         |
  WAITING ON GUY: section 7's questions Q1-Q9 (Q2-Q4 are G5 repo and PAT, G6 "push", G7 publish)
                         |
  main loop, on Guy's word: release_check --pre-push; push main and the tag; gh release create --draft --prerelease;
  Guy publishes; I5: assets' SHA256SUMS, a fresh clone with the real URLs, the memory example on our core
```

- **A builder never waits for the main loop.** A sub-agent reports only by ending its run, so each checkpoint is the
  end of a run: H after H1, I after I1, either after a fix round. The main loop commits, then resumes the same agent
  with SendMessage. Agent ids go into the handoff at launch. If a resume fails, a fresh sonnet gets the brief, the
  earlier report and `git log step-<x>`.
- **The fresh clone runs once, on main, at I2 (review 1 S8).** Revision 0's H2 cloned `step-h` before I's fetch.sh
  changes existed, so the pushed tree was never cloned before the push. Now H writes `tools/clone_check.sh` and the
  main loop runs it on a clone of main after both merges: README's steps block, the build block, the quickstart, the
  full pytest with `LAZ_REQUIRE_EMULATOR=1`. The README's route needs the release, which does not exist before the push, so the one deviation is
  `LAZ_RELEASE_BASE=file://<MAIN>/runs/release/v0.1.0` (fetch.sh's own override, I's); I5 repeats the clone against
  the real URLs after publishing.
- **H and I run side by side.** Neither runs a timed test; H runs one nice'd instance at a time (three for the pool,
  through the slot cap); I runs none. Nothing in Phase 4 is timed, so no speed number comes from Phase 4 (rules.md 7).
  The clone's full pytest at I2 holds D's state-boot bound; a failed time bound there is re-run once with the load
  printed, and never becomes a number in the docs.
- **H documents what I builds for P17** (the default core path, `LAZ_STOCK_CORE`, fetch.sh without the stock part).
  Both briefs carry the same interface (R12, R32); the as-built review checks that the two diffs agree.
- **How a builder waits on its own long command** (Phase 2 S9): an rc file from a `trap ... EXIT`, `run_in_background`,
  a bounded Monitor until-loop on "the rc file exists"; every waiter stopped (TaskStop) before the hand-back. Without
  Monitor: foreground parts under the 10-minute Bash limit, and it says so.
- **The audit runs on main after both merges and after the rewrite**, never on a branch: the history it audits is the
  history Guy pushes. The staged assets are rebuilt from main first (I2), so the audited files are the uploaded files.
- **Nothing reaches GitHub before Guy's word.** No remote today. Every network write is a "Waiting on Guy" item.
- **Never run `tools/build-core.sh`** (builders or I2): in a worktree it would `rm -rf` MAIN's build tree through the
  `dl/` link (Phase 3 review 2 N10). Phase 4 reads the P9b build only.

## 3. File ownership (who creates or edits what)

| File | Owner | What changes |
|---|---|---|
| `README.md` | H | rewritten whole (phase-h.md 3.1) |
| `STATUS.md` (new, root) | H | phase-h.md 3.2 |
| `docs/USING.md` | H | finished (phase-h.md 3.3) |
| docs/HOST-API.md (new) | H | phase-h.md 3.4 |
| `examples/quickstart.py`, `pool_shots.py`, `memory_watch.py`, `examples/README.md` (new) | H | phase-h.md 3.5 |
| `tools/docs_check.py`, `tools/clone_check.sh` (new) | H | phase-h.md 3.6, 3.7 |
| `NOTICES.md` (new, root), `tools/mknotices.py` (new) | I | phase-i.md 3.1 (P11) |
| `tools/mkrelease.sh`, `tools/release_check.py`, `core/PIN-nokeys`, `core/OPENSSL.md` (new) | I | phase-i.md 3.2, 3.3 |
| `tools/fetch.sh` | I | the part flags, the release pins block, `LAZ_RELEASE_BASE`, the stock part removed (phase-i.md 3.4, P17) |
| `python/libazahar/_paths.py` (`core_path`'s default only), `host/azhost_main.c` (`DEFAULT_CORE` only) | I | the default core is ours (phase-i.md 3.5, P17) |
| `tests/python/conftest.py` (`stock_core`, `lazpy_core`, one hint text), `tests/gate_c.py` (its default core), `tests/gate-b.sh:45`, `tests/python/test_paths.py` (new), and any stock-path hit I0 finds in E's or G's tests | I | phase-i.md 3.5 (P17) |
| `testapp/Makefile` | I | one `-ffile-prefix-map` line (review 2 B4, phase-i.md 3.6) |
| `core/README.md` | I | the "Licenses" section only (phase-i.md 4) |
| docs/release-notes/v0.1.0.md (new) | I | phase-i.md 3.2 |
| `pyproject.toml`, `python/libazahar/__init__.py` | I | the version line in each, `0.1.0` (review 1 S10); nothing else |
| `tools/fetch.sh` pins (the two sha256 lines) | the main loop at I2 | filled from the staged files, one commit before the push (S11) |
| `docs/research/spike-2-real-scene.md` (the lines naming the game, its product code and the file location) | the main loop, before G8b | reworded to "one commercial Gen-3 GBA game, run locally (not distributed)" (consult section 8) |
| `docs/commit-map-g8.tsv` (G8, done); docs/commit-map-g8b.tsv (new); the pointer line in `docs/map/README.md` | the main loop (G8b) | old-to-new SHAs of the rewritten commits |
| `docs/map/rules.md` rule 3's stock-core clause; `docs/map/runners.md`'s fetch, gate B and gate F2 lines | the main loop | in I1's commit (P17; phase-i.md 3.5 gives the wording) |
| `docs/reviews/release-ip-legal.md` (done), docs/reviews/release-legal-audit-v0.1.0.md, docs/reviews/phase-4-as-built.md | the agents (via the main loop) | their reports, verbatim |
| `docs/map/code.md`, `tools.md`, `runners.md` lines; `.gitignore` if needed | the main loop | **in the same commit** as the files they map (H1's, I1's), since `map_check.py` fails otherwise (N8) |

A file listed for one step is never edited by the other. H's README **links** `NOTICES.md` and names fetch.sh's new
flags; it does not write them. I's release notes **link** the README; they do not restate its numbers. **No builder
edits a file outside its rows.** Nobody in Phase 4 touches anything else under `host/`, `python/`, `testapp/` or
`tests/` (I imports `tests/gate_f2.py`, read only), nor `core/patches/`, **`core/PIN`** (any edit changes `pin=`
against `build.inputs` and so fails check `keyblob`; phase-3.md:586's "Phase 4 pins its tarball URL and sha256 in
`core/PIN`" is superseded: OpenSSL's URL and sha256 live in `core/OPENSSL.md`, review 2 S6), `tools/build-core.sh`,
`docs/PLAN.md`, `docs/plans/*`, `docs/research/*` (read only: the sources of every number), `docs/hours.tsv`, the
handoff, **every item file**, `prototype/`, `LICENSE`, and MAIN (read and copy only; MAIN's `build-core/` and `dl/`
are read only). A code bug found while writing docs is reported, not fixed: the docs describe the code as it is.
Lines the main loop must add and the "Lessons and notes" blocks go in each report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. Before launch: section 2's five conditions, in order (Phase 3 merged and its worktrees removed; spike 2's
   rewording; G8b; the downloads; the launch message). `git worktree list` shows MAIN only, and the case-insensitive
   name check (`ls .. | grep -i libazahar-py-`), then `git worktree add -b step-h ../libazahar-py-h main` and `git
   worktree add -b step-i ../libazahar-py-i main`. Dispatch both sonnets without isolation, cwd in the worktree.
   Agent ids into the handoff.
2. At "H1 done" and "I1 done": commit exactly the listed paths with their map lines on each branch (`git add <paths>`,
   `git diff --cached --stat`, `tools/map_check.py`, `status_check.py --strict-handoff`).
3. One opus as-built review over both diffs (`git diff main step-h`, `git diff main step-i`), writing
   docs/reviews/phase-4-as-built.md with phase-h.md 12 and phase-i.md 12 as its checklists. Fixes by the resumed
   builders; commit.
4. Merge `step-h` into main (item 410 moves with its Evidence in the same commit), then `step-i` (no shared file; a
   conflict stops and goes to the main loop). Remove each worktree after `git status --porcelain --ignored` is empty
   in it (ignored outputs die with it); delete the merged step branches (`git branch -d`).
5. I2 (phase-i.md section 6). Both `release_check` and `docs_check` pass and the clone ends `clone ok`, or the builder
   whose file failed is resumed (a fresh sonnet with its brief if its worktree is gone).
6. I3 (phase-i.md 9.2); the report verbatim to docs/reviews/release-legal-audit-v0.1.0.md; BLOCKERs to I4; commit.
7. Waiting on Guy (section 7). On "push": phase-i.md section 8.2's commands in order. Then I5. Items 420 and 400 move
   to done with their Evidence (the release URL, the audit verdict, I5's lines).

## 5. Departures from PLAN.md (proposed; review and Guy approve or reject)

| # | PLAN.md says | Phase 4 does | Why |
|---|---|---|---|
| P9 | PLAN 2.7's build flags | done in Phase 3: `-DENABLE_BUILTIN_KEYBLOB=OFF` and `-ffile-prefix-map=$PWD/=` (e40e59c; the strings now read `dl/azahar-src/build-src/...`, review 1 S3). P9b (Phase 3 step 0) adds 0007, 0008, `LAZ_CORE_DROP`, OpenSSL 3, `build.inputs`; Phase 4 only checks them | section 0 |
| P10 | "Azahar's unified tarball **re-hosted unchanged**" | option (a), the default (G2, and the consult's answer 2): Azahar's tarball minus `LAZ_CORE_DROP` (three headers and the directory `externals/libressl`), made by stock bsdtar from the original without extracting (`tar -cJf ... --exclude ... @TARBALL`), plus one member `LIBAZAHAR-PY-REMOVED.txt` at its top: a neutral notice with the removed paths and the date, **no hashes** (GPLv3 5(a) / GPLv2 2(a); a published hash of key-bearing files only fingerprints them, consult section 2). The binary is **built from the stripped tree** (step 0), so the asset is the build's own input (review 1 S1). (b) points at Azahar's tarball (lawful, worse: it sends users to the blob and ClCertA); (c) the unchanged tarball is **RED** (consult) | the unchanged tarball holds the key blob and ClCertA |
| P11 | PLAN Phase H delivers `NOTICES.md` | step I generates it from the link line, the DEPS externals, the `src/` third-party notices (S7) and OpenSSL's tarball; H links it | the notices are the binary's licence obligation |
| P12 | the `fetch.sh` pin after the release | the pins are filled by the main loop at I2 from the files staged on main and committed **before** the push (S11); I1 stages with placeholders and `--skip-pins`; I5 checks the real URLs | one push instead of two, and no pin cycle in I1 |
| P13 | "Guy says push" | plus a **draft prerelease** (`gh release create --draft --prerelease`) that Guy publishes; a draft is visible to anyone with push access to the repo (here only Guy, N7) | Guy sees the exact assets first |
| P14 | (PLAN predates G3) | the release also attaches `openssl-3.6.5.tar.gz`, byte-identical to OpenSSL's own release asset (sha256 pinned in `core/OPENSSL.md`), and `core/OPENSSL.md` records how the linked libraries were built: the keg's own formula `KEG/.brew/openssl@3.rb` (its sha256 and homebrew-core path, its configure arguments quoted, not attached), the bottle, no patches (review 2 Q7) | GPLv3 Corresponding Source includes statically linked libraries' source and build scripts |
| P15 | (PLAN assumed a clean history, rev 0's R10) | done: the main loop rewrote this repo's history (G8, 01:06-01:08) and committed `docs/commit-map-g8.tsv` | Guy's privacy rule |
| P16 | PLAN Phase H: the README route uses `fetch.sh` (stock core) and the test app built with devkitARM | README's default route is our core and the test app from our release; `make testapp` is the "build it yourself" block; the stock core is not in the README at all (P17) | the stock core carries the key blob and ClCertA (section 0.6); the route then needs no devkitARM |
| P17 | PLAN 2.7, Phase I: "fetch.sh" fetches the stock core; the library's default core is the stock core's path | **default**: no pinned stock-core URL or sha256 anywhere in `tools/`; the library's and `azhost`'s default core is `dl/lazpy-core/azahar_lazpy_libretro.dylib` (where `fetch.sh --lazpy-core` puts ours); stock-core comparisons in `tests/` skip unless `LAZ_STOCK_CORE` names a file; docs say in prose where to get Azahar's core; rules.md rule 3's stock clause changes with it. Alternative if Guy accepts the YELLOW (Q1): a `--stock-core` opt-in flag in fetch.sh, never in the no-flag set, the README or a default test | consult section 7 (YELLOW); also review 2 N3 (`LAZ_CORE` no longer needed after the README route) |
| P18 | (none) | G8b: a second `git filter-repo` pass for the consult's section 9 material and spike 2's game lines, with a replace file outside the repo; docs/commit-map-g8b.tsv | consult sections 8, 9 (blocks the push) |
| P19 | PLAN Phase I's asset list | the core zip also carries `LICENSE` (GPLv3), `COPYING-azahar.txt` and `NOTICES.md` (Apache-2.0, OFL-1.1, Unifont, faad2's Nero line, citra_system_archives); one more asset, the citra_system_archives snapshot `citra_system_archives-f470e0c.tar.gz` (byte copy of SNAP); Phase 4 edits a few code lines (P17, B4) although PLAN gave it docs and release files only | consult sections 3-5 (the snapshot is the consult's SHOULD, cheap; the audit grades it) |

Not departures (interpretations): the fresh clone of the README runs at I2 on main with a `file://` release base
(section 2) and again at I5 with the real URLs; the memory example on our core is gated in H1 and I5.

## 6. Interfaces taken from Phases 1-3

"State": **holds** (checked on main, D at 721209f, or MAIN on 2026-11-13), **planned** (from a plan, not built yet;
step 0 checks it), **proposed**.

| # | What Phase 4 relies on | Source | State | Used by |
|---|---|---|---|---|
| R1 | Our core built by step 0 (7c33f38, 799e8c3 before G8: 0007, 0008, the four-entry drop list, OpenSSL 3, `build.inputs`; the build ended 01:06, exit 0) and gated by F2's f1 (`keyblob_findings()` empty) and F2's full batch on that build | phase-3 rev 2 step 0; phase-f2 f1; review 2 A | built (holds after F2 merges) | I, H (STATUS) |
| R2 | `build-core/azahar_lazpy_libretro.dylib` of the 01:06 build (the one F2 gates): `strip -x`, ad-hoc `codesign`, installed atomically; install name `@rpath/azahar_libretro.dylib`; `otool -L`: Cocoa, AVFoundation, IOSurface, CoreFoundation, libc++, libSystem only; 21,828,992 bytes (item 300's last note; the same size as the 00:52 build; the 21:09 build was 19,145,936), `vtool -show-build`: minos 11.0, sdk 26.2 (see R31) | build-core.sh; `otool -L`; item 300 | holds on the 01:06 build | I |
| R3 | Exports: 25 `_retro_*` + `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play`. Version: the strings `2126.2` and `-lazpy.1` are separate (patch 0005 joins them at run time); `LAZPY_REV=1`, no bump (Phase 3 review 2 N7) | review 1 A, B5; patches 0001, 0005, 0006 | holds (exports); planned (F2) | I |
| R4 | The link line `build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt`: cryptopp, mcl, dynarmic, enet, faad2, fmt, SPIRV, glslang, boost_iostreams, boost_serialization, zstd_seekable, lodepng, sirit, SoundTouch, SPIRV-Tools, SPIRV-Tools-opt, teakra, xxhash, zstd, Azahar's five libs, and **`/opt/homebrew/Cellar/openssl@3/3.6.5/lib/libssl.a` and `libcrypto.a`** (the keg's real path; no `/opt/homebrew/opt/` and no `externals/libressl` path anywhere in the build) | link.txt; review 2 A | holds (01:06 build) | I (`mknotices.py`) |
| R5 | `core/PIN`: tag 2126.2, commit 219d743a..., `SRC_URL`, `SRC_SHA256=85c8b56f...a4cd26`, `SRC_SIZE=43224348`, `SRC_TOP=azahar-unified-source-2126.2`, `LAZPY_REV=1`, `LAZ_CORE_DROP` with **four** entries (`src/core/hw/default_keys.h src/core/hle/service/http/ctr-common-1-cert.h src/core/hle/service/http/ctr-common-1-key.h externals/libressl`; the last a directory, `rm -rf`, `build-core.sh:89-96`; the `.o.d` guard greps each basename, `:161-166`), `OPENSSL_VERSION=3.6.5`, `OPENSSL_PREFIX=/opt/homebrew/opt/openssl@3` (`cd -P`, `build-core.sh:70`; override `LAZ_OPENSSL_PREFIX`, `:8, 39`). `build-core.sh:40-42` refuses an empty drop list. Phase 4 never edits `core/PIN` | core/PIN; review 2 A | holds | I |
| R6 | TARBALL `dl/azahar-src/src.tar.xz` verified; the build tree is `dl/azahar-src/build-src/<SRC_TOP>/` (stripped by P9b; DEPS paths name `build-src`); the reading copy `dl/azahar-src/unpacked/<SRC_TOP>/` keeps every file (the byte windows' source); `LAZ_CORE_PIN` overrides the pin file | build-core.sh:7, 43-44, 60-80 | holds | I |
| R7 | `tools/fetch.sh`: `get URL SHA FILE`, `ok`, `verify`, `sha_of`, pins block at the top (the stock core `CORE_VER`/`CORE_URL`/`CORE_SHA` at :17-20, MoltenVK, the headers), `LAZPY_ROOT`; **the parser takes one argument** (`case "${1:-}"`, fetch.sh:38-43, `--force` only); the stock core's `--force` removal at :80 and its fetch block at :85-93; no `LAZ_RELEASE_BASE` yet | fetch.sh | holds | I (rewrites the parser, removes the stock part, P17), H (README) |
| R8 | `make` builds `build/libazhost.dylib`, `build/azhost`; `make testapp` needs `DEVKITPRO` and `DEVKITARM` set (testapp/Makefile:5-6 stops with "Set DEVKITARM") and devkitARM first in PATH | Makefile:9, 24, 38, 45 | holds | H, I2 |
| R9 | `.gitignore` lists `*.tar`, `*.tar.xz`, `*.tar.gz`, `*.zip`, `*.dylib`, `*.3dsx`, `dl/`, `vendor/`, `runs/`, `build/`, `build-*/` (covers `build-core/`), `aes_keys.txt` (:23), `keys.txt` (:47) and the game/system list (N4) | .gitignore | holds | H, I |
| R10 | Every commit's author and committer is the no-reply identity (98 commits at G8, `git log --all`); the address is out of history (G8); **the consult's section 9 material and spike 2's game lines are still in older commits** until G8b (section 0.8) | `git log --format`; item 400 | holds (identity, address); planned (G8b) | I, main loop |
| R11 | `pyproject.toml`: name `libazahar-py`, version `0.1.0.dev0`, `requires-python >=3.10`, `license = "GPL-3.0-or-later"`, setuptools>=77, package-dir `python`; **no pytest in any dependency or extra** (B4); `python/libazahar/__init__.py:8` holds `__version__ = "0.1.0.dev0"` (S10) | main (D merged, a113cf6) | holds | H (install, tests), I (versions) |
| R12 | Environment: `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE` (Python and `azhost`; today's default core is `<root>/dl/azahar/azahar_libretro.dylib`, `_paths.py:34-36`, `azhost_main.c:13`; **after P17 the default is `<root>/dl/lazpy-core/azahar_lazpy_libretro.dylib`**, where `fetch.sh --lazpy-core` puts our core), `LAZ_MVK`, `LAZ_PROFILE`, `LAZ_LAZPY_PROFILE` (F2: `none` or a file; default `<root>/core/options-lazpy.txt` when present, `_paths.lazpy_profile()`), `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT` (default 3600 s) (E), `LAZ_PNG_LEVEL` (C side, 0-9, default 1, E), `LAZ_LOG_LEVEL` (`host/log.c:40`), `LAZ_ANY_CORE` (`host/core.c:64`), `MVK_CONFIG_LOG_LEVEL` (`host/api.c:261`), `LAZ_STATE_ANY_APP` (C, `host/state.c:370`); tests only: `LAZ_REQUIRE_EMULATOR`, **`LAZ_STOCK_CORE`** (P17: a stock core the user downloaded; unset, the stock comparisons skip). Build and fetch time (N2): `LAZ_OPENSSL_PREFIX`, `LAZ_CORE_PIN`, `LAZ_CORE_PATCHES`, `LAZ_CORE_LTO`, `LAZ_CORE_JOBS` (`build-core.sh:7-8`), `LAZ_RELEASE_BASE` and `LAZPY_ROOT` (fetch.sh). **No `LAZ_LAZPY_CORE` exists** (Phase 3 review 2 S5) | `python/libazahar/_paths.py`, host/, F2's diff; phase-3 rev 2 section 12 | holds (A-D); planned (E, F2, P17) | H, I |
| R13 | `Emulator(app, workdir, *, sd_seed, state, core, options, timeout, boot_timeout)`, `run(...) -> RunResult`, `run_until`, `run_frame`, `set_keys`, `set_input`, `screens()`, `shot(path_prefix)` (returns two paths), `save_state()`, `load_state()`, `stats()`, `sd`, `pid`, `closed`, `frame_total`, `close()`, context manager; `Buttons` names = libctru | `python/libazahar/emulator.py` | holds | H |
| R14 | Errors `LibAzaharError`, `BootError`, `GuestError`, `HostTimeout`, `HostCrashed`, `StateError`, `NeedsLazpyCore`, `HostError`, `ValueError` for bad args; `GuestMemoryError` (P7); **`SlotTimeout(HostTimeout)`**: `.op == "slot"`, `.seconds`, text "no libazahar slot free after <s> s: all <cap> are held; see <dir>"; `HostCallError` internal | `python/libazahar/errors.py`; phase-3 rev 2 section 12 | holds (D's); planned (E, G) | H |
| R15 | `Pool(n, app, root, *, factory=None, **emulator_kwargs)`: `submit`, `map`, `close(wait=True)`; `LoadWarning`; the default cap (E's rule); fake workers take no slot | phase-e 3.2-3.3 (rev 2, B3) | planned | H |
| R16 | `emu.memory` (`read`, `write`, `u8`..`u64`, `s8`..`s64`, `write_u8`..`write_u64`, `.raw_read`), `run(..., watch=[(addr, words)], watch_every=)`, `RunResult.watch` of `WatchRow` (`.u32(entry, word)`, 1-based batch frame); our core only | phase-g 4 | planned | H |
| R17 | `core/options-lazpy.txt` applied automatically on our core (P8); `azhost --lazpy-profile FILE\|none` (relative to the cwd) | phase-f2 3.2-3.3 | planned | H |
| R18 | docs/research/speed-table-e.md: per row date, commit, core and version, load at start and end, guest fps, x real time, CPU and wall ms per frame, the guest-time check; light-scene label; the cap and its rule | phase-e 7 | planned | H |
| R19 | `docs/research/spike-2-real-scene.md:30-42`: 334-345 fps, 5.6-5.7x at load 26.7 (16:07); 129 fps, 2.2x at load 68-96; 3 instances 136-138 fps at 58-90; 0.5-0.8 GB per instance; "a clean re-measure on a quiet machine is still owed". Lines 22 and 57 name a commercial game and its product code (audit item, S15); line 37 says "51x" | the file | holds | H, I3 |
| R20 | F2's report (repeat exactness on our core, the debug-stop frame, stock states into ours, `stock_r1`); C's input offsets; D's state-boot times | items' notes after each merge | planned | H |
| R21 | `docs/USING.md`, D's 12 sections; section 11 now says repeats are exact only on our core (D's as-built fix N13, 721209f, review 1 S13), G's "Guest memory" section | main; phase-g 4 | holds (D); planned (G) | H |
| R22 | `host/azhost.h` (every `azh_*` with its comment, the error enum, the limits); `build/azhost layout` prints `abi=<n>` and every `fields[]` row; ABI 3 after G; **`azhost` has no `--help`**: any other first argument prints the usage to stderr and exits non-zero (`azhost_main.c:34-40, 159-160`) | A, C, G | holds (ABI 2); planned (ABI 3) | H |
| R23 | `build/testapp.3dsx` is ours (GPLv3-or-later; glyphs and shader ours; libctru, citro2d, citro3d zlib; newlib's libc/libm BSD-style; libctru's default icon in the SMDH, no `ICON` in testapp/Makefile) | testapp/README.md; font.c:1; N5 | holds | I (NOTICES' test-app section) |
| R24 | The test app's log `testapp/log.txt` (`k=%08lx`, record.c:58; sdlog.c:51), markers, `control.txt` keys (`tests/testapp_log.write_control`) | phase-b; D | holds | H |
| R25 | Spike 1's ~50x (and spike 2's "51x") is an idle menu and is never quoted | spike-1:9, 55; spike-2:37 | holds | H |
| R26 | No remote; `gh` 2.95.0, logged in as **GuyShtainer** (keyring OAuth); `git push` uses the osxkeychain PAT, fine-grained "Contents: read/write" (a PAT scoped to selected repos does not cover a new repo: 403) | `gh auth status`; review 1 E | holds | I (section 8.2), G5 |
| R27 | `build-core/build.inputs` (written after the configure guards, before the compile, `tools/build-core.sh:140-158`): `tarball=`, `pin=`, `script=`, one `patch <name>=<sha256>` per patch (0000-0008), `drop=`, `openssl_version=`, `openssl_prefix=` (the resolved Cellar path), `openssl_libssl_sha256=`, `openssl_libcrypto_sha256=` (`:150-153`), `head=` (a pre-rewrite SHA: today `799e8c3...`, which is 7c33f38 after G8 and changes again at G8b), `clean=yes\|no`, and last `cmake=`, **the whole configure command** with `$ROOT` as `<repo>` (`:156`). Today's: clean yes, libssl.a 23c6a50d..., libcrypto.a 88981a4c... | build-core/build.inputs (01:02); review 2 A | holds | I (SOURCE.md quotes `cmake=`; `keyblob_findings` compares the hashes with the checkout) |
| R28 | `tests/gate_f2.py: keyblob_findings(build_dir, core, src_root, tree, repo) -> list[str]`, and `keyblob_records(...)` (F2's diff): the drop list, pins and `OPENSSL_VERSION` come from `repo/core/PIN`; f1's items: `build.exit` 0, **the core's mtime later than `CMakeCache.txt`'s**, every input hash, `clean=yes`, the OpenSSL version and cache lines, the drop entries absent from the build tree, no `.o.d` naming any entry's basename, none of 8 windows of each of the three arrays in the core (parsed at run time from the reading copy by `_header_bytes(src_root, rel, array)`), the strings (`-lazpy.1`, no `/Users/`, no ClCertA fallback text, no `libressl`, `OpenSSL 3.6.5`), `otool -L` (no libssl/libcrypto) and `link.txt`; an empty list means pass | phase-f2.md:28-54, 218-224; F2's diff | planned (F2 merges) | I (imported by release_check checks `keyblob` and `history-bytes`) |
| R29 | States: an ABI-3 host loads ABI-2 and ABI-3 states; an ABI-2 host refuses ABI-3 states (`host/state.c:395-396`, `meta.abi < 2 \|\| meta.abi > AZH_ABI_VERSION`) | D; phase-3 rev 2 section 12 | holds (D); planned (G) | H (STATUS, USING) |
| R30 | Homebrew `openssl@3` 3.6.5 at **KEG = `/opt/homebrew/Cellar/openssl@3/3.6.5`** (what `cd -P /opt/homebrew/opt/openssl@3` gives, and `build.inputs`' `openssl_prefix=`): `lib/libssl.a` (1,475,544 bytes) and `lib/libcrypto.a` (8,593,624), built 2026-09-29 as a bottle (`INSTALL_RECEIPT.json`: poured from bottle; its `source.path` holds a home-folder path: never copy it); the keg's `sbom.spdx.json` names the source `https://github.com/openssl/openssl/releases/download/openssl-3.6.5/openssl-3.6.5.tar.gz`, sha256 `a2157c2830efdec3788939b00c9b0638306d3f0bbb76dc4832ee503bb397df98` (the consult checked OpenSSL's published `.sha256`), the bottle sha256 `0994a8029175af4578c3b93b3020e58dffa638ca21dc22d862c6bc02fea7e73b`, licence Apache-2.0, no patch entries; the formula Homebrew installed, `KEG/.brew/openssl@3.rb` (6,723 bytes, sha256 `8fa691c3aade8a06699a7f36f11bf66dd81a7747f9163642a08d71df155a3853`; configure arguments at its lines 44-56, 85, 93; homebrew-core path `Formula/o/openssl@3.rb`; no tap here, so `brew cat` would need the network); `openssl version -a`: platform `darwin64-arm64-cc`, compiler flags `-fPIC -arch arm64 -O3 -Wall -DL_ENDIAN -DOPENSSL_PIC -D_REENTRANT -DOPENSSL_BUILDING_OPENSSL -DNDEBUG`, `OPENSSLDIR "/opt/homebrew/etc/openssl@3"`. The two `.a` files' sha256 equal `build.inputs`'. `brew pin openssl@3` since 01:04. The core holds OpenSSL's compiled-in directories as strings: `OPENSSLDIR` `/opt/homebrew/etc/openssl@3`, `ENGINESDIR` and `MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`; 0 `/Users/` strings | the keg, 2026-11-13; review 2 A | holds (re-checked at I0 against `build.inputs`) | I |
| R31 | **The core needs macOS 15 or later.** The linker warns that every object in the keg's `libcrypto.a` was built for macOS 15.0, while the core's `LC_BUILD_VERSION` says minos 11.0 (`tools/build-core.sh:15` exports `MACOSX_DEPLOYMENT_TARGET=11.0`). Our `build/libazhost.dylib` and `build/azhost` are already minos 15.0 (the Makefile sets no target, so clang uses the SDK host default) | coordinator, P9b link log; `vtool -show-build` 2026-11-13 | holds | H, I |
| R32 | F2's interface (its worktree diff, 2026-11-13): `azhost run ... --lazpy-profile file\|none` (default `core/options-lazpy.txt`, applied first on our core only); `_paths.lazpy_profile()`; `tests/gate_c.py --core PATH --core-kind auto\|stock\|lazpy` (its fallback core is `LAZ_CORE`, else `dl/azahar/azahar_libretro.dylib`); D's `test_c4_debug_text_needs_our_core` (`stock_core` fixture) and F2's twin `test_c4_debug_text_on_our_core` (`lazpy_core`); `tests/python/test_lazpy_profile.py` (no emulator); `tests/gate_f2.py --ours OURS --stock STOCK` (`--stock` required; scenarios `symbols.stock`, `stock_r1` and half of `cross` use it). F2 edits `_paths.py` and `azhost_main.c` too, so I's P17 lines go on top of F2's merge | `git -C ../libazahar-py-f2 diff`; phase-f2.md 5-6 | planned (F2 merges) | I (P17), H (USING) |
| R33 | `build/testapp.3dsx` (151,948 bytes, 00:53) holds 6 `/Users/<user>/...` strings: `assert()`'s `__FILE__` paths (`testapp/source/draw2d.c:4, 23, 48, 57`, `font.c:4`); `testapp/Makefile:22-23` has no prefix map; it compiles from `TOPDIR` (= `testapp/`, :9) through devkitPro's `3ds_rules` | review 2 A, B4; testapp/Makefile | holds | I (B4) |
| R34 | The system archives (consult section 5): four headers under `externals/open_source_archives/include/` (shared font, Mii, country list, bad-word list), each naming its own generator commit in its header (848af47, 5e6b5df, bbe60b5, 47cdc93; the last is not in B3n30/citra_system_archives' history, its content matches 2d98119); the font holds glyphs from Montserrat Regular 4.000 (SIL OFL 1.1, "Copyright 2011 - 2016 The Montserrat Project Authors") and GNU Unifont 10.0.05 (GPLv2 or later with the font embedding exception); the Mii header decodes to a 73,600-byte RomFS holding one `CFL_Res.dat`; the bad-word header holds one placeholder pattern per file; a snapshot of citra_system_archives at f470e0c holds four of the generator commits | the consult | holds (I0 re-checks 1-2) | I |
| R35 | Gen3D's first use (review 2 A, G): `run(timeout=)` is a no-progress limit (the heartbeat moves every frame, `host/run.c:117`; `_client.py:153-176`); a bad input frame raises a plain `ValueError` (`inputs.py:146`); `result.shots` is keyed by batch frame while file names hold whole-run frames (`emulator.py:142, 181-190`; `docs/USING.md:24`); nothing clears `sys/Azahar/sdmc/` on reuse (`emulator.py:55-56, 76`). Gen3D's 222.6 fps (LAZPY-TRY-1.md:20) is **not** a README number (outside this repo, a commercial game on its SD, load 13-46) | review 2 A, G, N4 | holds | H |

## 7. Waiting on Guy, and the questions for Guy

Only Guy can do or decide these. Every item has a safe default, so nothing below blocks a step before the push (S14).

Answered or facts (records):
- **G1 (answered).** Key blob off (P9, e40e59c); ClCertA (0007) and "load no keys" (0008) in step 0 (Phase 3's Q6).
- **G2 (answered by the consult: (a)).** The source asset is P10 (a). (b) is lawful but worse; (c) is RED.
- **G3 (answered 2026-11-13: "Switch to OpenSSL 3").** Step 0 links a static OpenSSL 3; Phase 4 ships its source and
  licence (P14). The consult grades the core GREEN under rule 7, so the core asset ships. If the audit (I3) still
  holds the core back, the default stays: release the repo, the test app and the build files without the core binary
  and its source assets; STATUS says why (risk 2).
- **G4 (a fact).** The core binary goes out under GPLv3 only (Azahar's "or later"): it links Apache-2.0 code
  (SPIRV-Tools, OpenSSL 3), which GPLv2 does not accept. Never offer it under a non-GPL licence (faad2, consult 4).
- **G8 (answered "Rewrite before push"; done 01:06-01:08).** G8b (P18) is the same ruling applied to the consult's
  section 9 material and spike 2's game lines; it needs no new answer.

**Questions for Guy** (the main loop asks them in one message; the default holds until he answers):

| # | Question | Default (what happens with no answer) |
|---|---|---|
| Q1 | The scripted download of Azahar's stock core (consult section 7, YELLOW). **Remove it (recommended)**: no stock URL or sha256 in `tools/`, the default core is ours, stock comparisons need `LAZ_STOCK_CORE` (P17). **Or accept the YELLOW**: a `--stock-core` opt-in flag stays in fetch.sh, never in the README route and never in a default test run (the consult calls this the one item worth putting to counsel) | remove (P17's default). Either way the README never names the stock core's download |
| Q2 | G5, the account step: Guy creates the public repo `GuyShtainer/libazahar-py` on the web, or tells the main loop to run `gh repo create` (no push). If git's osxkeychain PAT is scoped to selected repos, Guy adds the new repo to it, or approves `gh auth setup-git` (git then uses gh's GuyShtainer token). `git ls-remote origin` must work before any push | nothing is created |
| Q3 | G6, "push": main and the tag, and the draft release | no push |
| Q4 | G7, publish the draft (or "publish" and the main loop runs `gh release edit --draft=false`). Version `v0.1.0`, prerelease. Hygiene: keep the tracked `claude.ai/artifact/...` links and the `/Users/<user>` paths in plan and review files (the username is his GitHub handle) unless the audit grades them above INFO | the draft stays a draft |
| Q5 | G9, spike 2's scene: may STATUS say "measured with a game dumped from the maintainer's own cartridge" (policy "Method" prefers saying so)? Never the title, product code or file location (consult section 8) | no ownership line; "one commercial game's scene, run locally" |
| Q6 | macOS 11-14 users in v0.1.0? Serving them means OpenSSL built from its tarball with an 11.0 target, a core rebuild and F2 again (about 0.35 h of agent time plus about 10 minutes of machine time, risk 9), and Q7 first | "macOS 15 or later" (risk 9); a Phase 5 candidate |
| Q7 | May rules.md rule 2's exception (today: Azahar's own CMake build on the pinned commit) also cover building OpenSSL from its pinned tarball, nice'd in the background, so the published rebuild recipe can be tested (review 2 S4) and Q6 becomes possible? | no; the recipe in `core/OPENSSL.md` says "not tested by this project" |
| Q8 | A fallback name, decided now so a rename request costs an hour, not a week (consult section 6). Recommended: **`lazpy`** (already in every internal name: `azahar_lazpy_libretro`, `-lazpy.1`, `LAZPY_*`; a rename changes the repo, the README title, `pyproject.toml`'s name and the import package `libazahar`). Another: `headless3ds-py` | `lazpy` is recorded as the fallback; nothing is renamed now |
| Q9 | An optional courtesy note to Azahar's maintainers before the release (consult section 6: Guy's call; it is also discovery). If yes, the main loop drafts five plain lines for Guy to send himself | no note |

Standing rules from the consult that need no answer: the README's first paragraph says "unofficial; not affiliated
with or endorsed by the Azahar project; report libazahar-py issues here, not to Azahar"; never Azahar's logo or icon;
our build is never called "Azahar" alone (its file name and `-lazpy.1` suffix stay); patches are never sent upstream
without following Azahar's `AI-POLICY.md` (STATUS's "Considered and dropped" says so).

## 8. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (GIT-COMMIT 219d743a..., GIT-TAG 2126.2). "CORE" =
`build-core/azahar_lazpy_libretro.dylib` (the 01:06 build). "STOCK" = `dl/azahar/azahar_libretro.dylib` (a local
file on this Mac; after P17 no script of ours fetches it).

| Fact | Where |
|---|---|
| `option(ENABLE_BUILTIN_KEYBLOB ... ON)`; the define when on; `default_keys.h` added to `citra_core` only when on (the only CMake reference) | SRC CMakeLists.txt:154; src/CMakeLists.txt:186-187; src/core/CMakeLists.txt:501-503 |
| `default_keys.h` 46,817 bytes, `#error` guard :7-9, array :11; `key.cpp` includes it under `#ifdef` (:21-23) and reads it (:302-312); every key path goes through `GetKeysStream()` (:292-314) | SRC src/core/hw/ |
| ClCertA: `ctr-common-1-cert.h` (1,264-byte array) and `ctr-common-1-key.h` (1,232) included without `#ifdef` at `http_c.cpp:37-38`; fallback at :2281-2289; `DecryptClCertA()` returns at the missing slot 0x0D (:2262-2266); in no CMake file | SRC src/core/hle/service/http/; review 1 A; Phase 3 review 2 B1, N1 |
| The 21:09 build: cache `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF` (:728), the blob absent, no `.o.d` names `default_keys.h`, 0 `/Users/` strings, ClCertA arrays present, one `.o.d` names `ctr-common-1-*` | review 1 A; Phase 3 review 2 section 3 |
| STOCK: Azahar's default build embeds the blob and both ClCertA arrays and links LibreSSL | Azahar's CMake defaults, 2026-11-13 |
| LibreSSL `externals/libressl/COPYING` (133 lines): ISC :2-4; OpenSSL License :17-72 (clause 3 :35-38, clause 6 :49-52, Young/Hudson :68-70); SSLeay :74-132 (:127-131 "cannot simply be copied and put under another distribution licence [including the GNU Public Licence.]"); built unless `USE_SYSTEM_OPENSSL` (`externals/CMakeLists.txt:319-333`, `find_package(OpenSSL 1.1)`); httplib links it (:361-362) | SRC; review 1 A, S6 |
| faad2: GPLv2 or later per `faad2/faad2/README:12-39` and each file header (`libfaad/decoder.c:5-8`), "Any non-GPL usage ... strictly forbidden" (README:19-20), required notice "Code from FAAD2 is copyright (c) Nero AG, www.nero.com" (:22-23) (COPYING:308-309 is only GPLv2's own template) | SRC externals/faad2 |
| Other linked licences: boost BSL-1.0; cryptopp Boost-style; dynarmic 0BSD-style; mcl, oaknut, teakra, enet, fmt, vma MIT; glslang BSD-3/BSD-2/MIT/Apache-2.0 parts (LICENSE.txt:27-99; its GPL-3+Bison part covers a parser removed long ago, :5-6, :303); lodepng zlib; sirit BSD-3; SoundTouch LGPL-2.1 (COPYING.TXT:1-2; complete corresponding source of the whole work meets LGPL 2.1 section 6); SPIRV-Tools Apache-2.0, no NOTICE; spirv-headers Khronos MIT-style; xxHash BSD-2; zstd BSD-3; inih BSD-3. The only NOTICE file under `externals/` is `library-headers/fdk-aac/NOTICE` (not linked); no MPL-2.0 file | each externals/<name>/LICENSE* |
| Third-party notices inside Azahar's own `src/`, compiled in: `src/common/cityhash.{h,cpp}` (MIT), `src/common/bit_field.h`, `vector_math.h` (Tony Wasserka), `src/core/file_sys/plugin_3gx*` and `src/core/hle/service/plgldr/plgldr.*` (MIT, The Pixellizer Group), `src/video_core/host_shaders/texture_filtering/*.frag` | review 1 A, S7 |
| `open_source_archives/include/`: `shared_font.app.romfs.h` 6.8 MB, `mii.app.romfs.h` 453,989 bytes, `country_list.app.romfs.h` 1,350,888, `bad_word_list.app.romfs.h` 9 KB; the Readme names B3n30/citra_system_archives at 0baa5f57 and lists only the font and the bad-word list; no licence file; linked at `src/core/CMakeLists.txt:509` | SRC |
| Azahar `license.txt` is the GPLv2 text with **no OpenSSL exception**; the libretro sources say "GPLv2 or any later version" | SRC license.txt; citra_libretro.cpp:1-3 |
| `externals/cpp-jwt/` holds test RSA/EC private keys; cpp-jwt is not on the link line | find; link.txt |
| Homebrew OpenSSL 3.6.5 (R30): the keg has `LICENSE.txt` (Apache-2.0 text), `AUTHORS.md`, `CHANGES.md`, `NEWS.md`, `README.md` and no NOTICE; Homebrew copies `notice` files into a keg (`Library/Homebrew/metafiles.rb:13` lists `notice`), so the tarball most likely has no top-level NOTICE: I0 settles it from the tarball's member list | the keg; metafiles.rb |
| Apache-2.0 section 4: (a) a copy of the licence, (b) prominent notices in modified files (we modify none), (c) keep notices in the source form we redistribute (the tarball unchanged), (d) only "if the Work includes a NOTICE text file", its attribution notices in a NOTICE file or the documentation | Apache-2.0 text (the keg's LICENSE.txt) |
| GPLv3 section 1: Corresponding Source = the source "needed to generate, install, and (for an executable work) run the object code and to modify the work", including the scripts used to control compilation, and the source of libraries the work is linked with (OpenSSL is not a System Library here: bundled and statically linked); 5(a) prominent notices with a date; 6(a) object code with the source; 6(d) source on another server, the distributor stays obliged | LICENSE |
| `git filter-repo` 2.47.0 at `/opt/homebrew/bin/git-filter-repo`; it aborts outside a fresh clone unless `--force`; `--replace-text` and `--replace-message` take `literal==>replacement` lines; `--replace-refs` defaults to `update-no-add` (no new `refs/replace/`); it ends by expiring reflogs, repacking and resetting the main worktree (untracked and ignored files stay) | `git filter-repo --version`, `--help` |
| History scan 2026-11-13 00:55: 93 commits; the local part of Guy's personal address in 6 (first 15d0323, last 8a16f9e), all in `docs/plans/phase-i.md`; 0 in commit messages; 0 at HEAD; no tags; only `main` contains 15d0323 (`git branch --contains`); worktrees `../libazahar-py-c` (step-c) and `../libazahar-py-d` (step-d) | `git grep -c -i -F` per commit (needle read from Guy's preferences file by the command, never written), `git branch --contains` |
| bsdtar 3.5.3 (libarchive 3.7.4, liblzma 5.4.3): `-c ... @archive` copies members from an archive without extracting; `--exclude`, `--uid`, `--gid`, `--uname`, `--gname`; Apple zip 3.0: `-X` drops extra attributes | `tar --version`, `zip -v`, man bsdtar |
| Apple's `/usr/bin/python3` is 3.9.6, below `requires-python >=3.10` | `/usr/bin/python3 --version` |
| No `user.email`/`user.name` in this repo's git config | `git config --show-origin --get-all user.email` (empty) |
| `gh` 2.95.0: `release create` has `--draft`, `--prerelease`, `--notes-file`, `--target`, `--verify-tag`, `--latest` | `gh release create --help` |
| Step 0 as built: `OPENSSL_PREFIX` resolved with `cd -P` (`build-core.sh:70`), override `LAZ_OPENSSL_PREFIX` (:8, 39), no `OPENSSL_ROOT` or `LAZ_OPENSSL_ROOT` anywhere; the drop loop takes directories (:89-96); `build.inputs` written at :140-158 with `openssl_*` keys (:150-153) and the full `cmake=` command (:156); `CMakeCache.txt`: `USE_SYSTEM_OPENSSL:BOOL=ON`, both `OPENSSL_*_LIBRARY` at the Cellar path; no build file names `/opt/homebrew/opt/` | review 2 A |
| The stock core in code and tests at bd62873: `tools/fetch.sh:17-20` (pins), :80 (`--force`), :85-93 (fetch and unzip); `python/libazahar/_paths.py:34-36` and `host/azhost_main.c:13` (the default core); `tests/python/conftest.py:67-72` (`stock_core`), :76-83 (`lazpy_core` falls back to `build-core/`); :61 and :72 the hint texts; `tests/gate-b.sh:45`; F2 adds `tests/gate_c.py`'s fallback and `tests/gate_f2.py --stock` (R32). E's and G's tests: I0 greps them after the merge. `docs/research/spike-1-headless-core.md:18, 27-28` records the stock asset's URL and sha256 (rules.md 2's record, not a script; the audit grades it) | `git grep` at HEAD; F2's diff |
| Spike 2's research file still names the game, its product code and revision, and where the game file sits, at HEAD (lines 22, 57); `dc2fe80` added them | `sed -n`, `git log` (the text is never copied here) |
| The section 9 rewording commit 776e8da changed `docs/plans/phase-3.md`, `docs/plans/phase-4.md`, `docs/reviews/phase-3-review-2.md`, `docs/reviews/phase-4-review-1.md` and item 400 (plus unrelated lines); 107 commits in `git rev-list --all` at bd62873 | `git show --stat 776e8da` |
| `git filter-repo --replace-text` lines are literal by default, take `regex:` and `glob:` prefixes, and `==>` sets the replacement (default `***REMOVED***`); `--replace-message` takes the same syntax | `git filter-repo --help` |
| `git show --word-diff=porcelain <commit>` prints each removed run on a `-` line and each added run on a `+` line, so a rewording commit lists exactly the words it removed | git's diff options |
| `build/testapp.3dsx` holds 6 `/Users/` strings (R33); `build/libazhost.dylib` holds 0 | review 2 A |
| The consult's facts used here: the keys file is `sysdata/keys.txt` (`src/common/common_paths.h:83`); the OpenSSL tag has no top-level NOTICE (GitHub API); the archives' generator commits and contents (R34); no github/dmca notice names Citra, Lime3DS, Azahar, ClCertA or a 3DS keys file (searched 2026-11-13) | docs/reviews/release-ip-legal.md sections 1, 3, 5 |

## 9. Hours, against PLAN.md (agent wall time)

| Step | Builder | Review | Commit | Total | PLAN.md | Why the difference |
|---|---|---|---|---|---|---|
| H | 0.45 (H0 0.05, H1 0.40) | (joint) | 0.05 | **0.50** | 0.5 | revision 1's 0.45, plus Gen3D's four USING lines (+0.02, review 2 S7), the consult's first paragraph, the longer forbidden list and two small docs_check checks (+0.02), the build-variable table and N3/N4 lines (+0.01); P17's docs are net zero (the stock line and `export LAZ_CORE` go, one prose paragraph comes) |
| I | 0.70 (I0 0.13, I1 0.47, I4 0.1) | (joint) | 0.05 | **0.75** | 0.6 | revision 1's 0.65; review 2 net -0.02 (B1, B4, S4 +0.06; S2, S3, S9 -0.08); the note without hashes (-0.01); no `--openssl-src` flag (-0.02); P17's code and tests (+0.06); the consult's notices: OFL, Unifont, the archives, two copyright lines (+0.03); the five archive checks in I0 (+0.02); the snapshot asset (+0.01); the standing checks (+0.03) |
| Joint as-built review (H and I) | | 0.2 | | **0.2** | | one opus run over two small diffs |
| Main loop and legal agents | spent: ip-legal 0.1, G8 0.05, the section 9 rewording 0.03; to do: spike 2's rewording 0.02, G8b 0.1, downloads 0.02, I2 0.15, I3 audit 0.1, I5 0.05 | | | **0.62** | (in I's 0.6) | the two rewrites and the clone at I2 are new |
| Review loops | | | | 0.4 | | two loops (spent) |
| **Phase** | | | | **about 2.5** | **1.1** + loops | the consult's conditions add about 0.3 h to revision 1's 2.2 |

Guy's time: section 7's questions in one message (about 5 min), G5 (5 min), G6 and G7 (5-10 min). Machine time: the
clone at I2 (local `file://` release copies plus MoltenVK and headers from upstream, a few minutes, then the full
pytest, about 10-15 minutes, nice'd), the xz pack (1-3 min), G8b (seconds).

## 10. Risks for this phase

1. **P9b changes behaviour** (0007, 0008 or OpenSSL 3 breaks an HLE path the test app touches). F2's full batch on
   the 01:06 build is the check (Phase 3); a difference is a STATUS line and a Guy question, never a reason to ship
   keys.
2. **The audit holds the core back** although the consult graded it GREEN (consult section 1, its five conditions).
   Then the release ships the repo, the test app and the build files, with no core binary and none of its source
   assets (G3's default); STATUS says why; the README's route falls back to the build block (`build-core.sh`, `make
   testapp`) and I4 swaps the steps marker (phase-h.md 3.1). The standing checks (section 0.9) make a late surprise
   unlikely.
3. **Docs drift from code** (Phase 3 is not merged when H starts). H0 checks every planned row; the examples run.
4. **A number without load or date.** docs_check refuses it (numbers check; the forbidden list holds 50x and 51x).
5. **The clone at I2 needs the network** (MoltenVK, headers, PyPI's setuptools and pytest). A network failure is a
   retry, not a red; the log records the bytes fetched.
6. **The bsdtar copy differs from Azahar's tree beyond the drop list** (mode bits, a symlink, pax headers).
   `release_check` check `source` compares the two member lists name by name (type, mode, size, sha256, link target):
   a member is dropped if its name equals a drop-list entry or starts with `<entry>/` (review 2 B1), and only dropped
   members and the note member may differ; `tools/untar_checked.py` must accept the asset (S4); two runs give the same
   sha256. The 7 relative symlinks stay symlinks.
7. **G8b misses a variant** (a reworded run that is split across lines, or a later commit that brings a line back).
   The replace file comes from the rewording commits' own word-diff, not from memory; check `history-bytes` scans
   every commit for the arrays' hex-text windows (counts only) and check `repo` for long `0xNN` runs; the audit reads
   the history. A hit after G8b means one more pass (seconds of machine time, about 0.05 h; safe while nothing is
   public).
8. **A downloaded dylib is quarantined** when fetched with a browser. README troubleshooting: `xattr -d
   com.apple.quarantine <file>`; curl sets none.
9. **The macOS floor** (R31): the core's header says 11.0 but its libcrypto needs 15.0. **Chosen: the release says
   "macOS 15 or later"** (README, STATUS, release notes, SOURCE.md); `release_check` check `macos` (16) reads every
   shipped Mach-O's minos and the keg's libcrypto object target. Phase 3 is asked to set `MACOSX_DEPLOYMENT_TARGET=15.0`
   at its next core rebuild (ask 8 in section 12); the v0.1.0 core keeps 11.0 in its header, which STATUS records.
   Declined for v0.1.0 (Guy Q6, Q7): OpenSSL built from its tarball with an 11.0 target, a core rebuild and F2 again
   (about 0.35 h of agent time plus about 10 minutes of machine time), for macOS 11-14 users nobody can test here.
10. **The system archives' provenance.** The consult (section 5) found the generator repository, its licence-free
    state and the font and Mii sources. I0 runs its five checks as commands (phase-i.md 5); NOTICES carries OFL-1.1,
    Unifont and the citra_system_archives notice, and the snapshot asset ships (P19). A failed check is a BLOCKER for
    the core asset only.
11. **The tag gets a machine-local address** (no git identity configured). Section 8.2 of phase-i.md sets the repo's
    identity first; `release_check --pre-push` checks it and every tag's tagger.
12. **A test still assumes the stock core after P17** (a hidden `dl/azahar/` path in E's or G's tests, or a fixture
    that silently picks the stock file). I0 greps the merged tests for every stock path and name; I1 changes each hit
    (phase-i.md 3.5); the clone at I2 runs the full pytest with `LAZ_REQUIRE_EMULATOR=1` on a machine state with no
    stock core in the clone, so a hidden stock assumption fails there, not on a stranger's Mac. If Guy accepts the
    YELLOW (Q1), the same tests still skip without `LAZ_STOCK_CORE`.
13. **Homebrew upgrades `openssl@3` before the release**, so the keg no longer matches the linked libraries.
    `openssl@3` is pinned since 01:04 (`brew pin`), held until I5. `release_check` check `openssl` compares OSSL's
    name with `openssl_version=`, and under `--pre-push` the keg's `.a` files with `build.inputs`' hashes.
14. **The statically linked libcrypto carries Homebrew's paths** (R30: `OPENSSLDIR` `/opt/homebrew/etc/openssl@3`,
    `ENGINESDIR` and `MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`), so the guest's HTTPS uses
    Homebrew's CA file when `openssl@3` is installed and has none on a Mac without Homebrew. That does not matter for
    testing homebrew; STATUS "Known limits" gets one line. Not private (no `/Users/`): `release_check` check `private`
    (7) lists these three as expected `NOTE` lines, and the audit brief (phase-i.md 9.2) names them as expected.
15. **A history rewrite loses work**: filter-repo resets the main worktree. G8b's preconditions (phase-i.md 8.1b): no
    worktree but MAIN, no agent running in it, the tracked tree committed, a bundle backup outside the repo, the HEAD
    tree hash checked before and after (it changes only where the replace file matched at HEAD, which should be
    nowhere: the rewording is committed first).
16. **Old SHAs in docs and other repos go stale after G8 and G8b** (and `build.inputs`' `head=`). The two maps
    (`docs/commit-map-g8.tsv` and docs/commit-map-g8b.tsv) translate them; old SHAs in text are not edited. Gen3D's
    copy of the package must hold no `.git` from before the rewrites (phase-i.md 8.1b, review 2 N5).
17. **core/PIN's `SRC_URL` still names Azahar's unchanged tarball**, which holds the dropped headers. The build drops
    them before it compiles, and `keyblob_findings()` proves the result clean, but a reader of `core/PIN` is pointed at
    the original. Mitigation: USING's rebuild route uses `LAZ_CORE_PIN=core/PIN-nokeys` (our stripped asset), and the
    audit brief asks the auditor to grade `core/PIN`'s URL (a build input, not a link we promote). Not changed by
    Phase 4: editing `core/PIN` breaks `pin=` against `build.inputs` (S6).
18. **A rename request** (consult section 6). The fallback name is decided now (Q8, `lazpy` by default), so a rename
    is about an hour: the repo, the README title, `pyproject.toml`'s name, the import package.

## 11. Hour-saving pass (revision 1)

| Existing thing or cut | What it saves | Verdict |
|---|---|---|
| Stock bsdtar `@archive` with `--exclude` for the source asset (no `release_pack.py`); `touch -t` then `zip -X -9 -j` for the core zip; `git archive` for the build-files asset (committed files only, deterministic per commit) | about 0.08 h (a tool, its plants) and the I1-to-I2 re-stage drift (S11) | taken |
| The binary built from the stripped tree (Phase 3's drop list): no configure check, no "run from a download" exception in I | about 0.03 h and 1-3 min machine | taken (Phase 3 does it) |
| `release_check` imports `gate_f2.keyblob_findings()` instead of a second set of windows | about 0.03 h and a drift risk | taken |
| The fresh clone runs once at I2 on main (not H2 on step-h), by H's `clone_check.sh` | about 0.1 h net, and it tests the pushed tree | taken |
| One opus as-built review over both diffs | about 0.1 h | taken |
| Pins filled by the main loop at I2 | the likely I4 re-pin cycle, about 0.05 h | taken |
| docs_check without `stray-numbers` (false-positive prone); keep `numbers` and `forbidden` (50x, 51x, full speed) and the review checklist's number item | about 0.02 h | taken |
| OpenSSL's source URL and sha256 from the keg's own SPDX SBOM (R30), cross-checked against OpenSSL's published `.sha256` when fetched; fetched with fetch.sh's existing `get` helper | finding and pinning by hand | taken |
| `git filter-repo --replace-text` (installed; GitHub's documented tool for removing sensitive data) instead of `git filter-branch` or BFG | about 0.1 h and a slower, error-prone rewrite | taken (filter-branch is the documented fallback) |
| G8 right after the P9b build, before Phase 3's worktrees, instead of at the end | the commit map shrinks from about 110 to about 25 rows; no worktree branch is rewritten (today only `main` holds the affected commits) | taken (done 01:06-01:08) |
| The ip-legal consult now, with 0008, ClCertA, OpenSSL and the stock-core question in one brief | an audit-fix-re-audit loop (about 0.25 h) and a possible second rebuild if 0008 were refused late | taken (done 2026-11-13) |
| README route on our released core (P16): the clone needs no devkitARM; the build block is checked by I2's `make testapp` | the devkitARM env trap (B3) leaves the main route | taken |
| ScanCode, `reuse lint`, `licensee` for the notices | | declined: heavy installs, triage; the stdlib generator reads the real link line |
| GitHub Actions for the release | | declined: CI out of scope (PLAN 5) |
| Pre-seeding the clone's `dl/` from MAIN | a minute | declined: the gate is "only the README's steps" (the `file://` base is the one named deviation) |
| A `[test]` extra in `pyproject.toml` for pytest | a line in USING | declined for v0.1.0: I owns only the version line; the clone installs pytest explicitly (B4); a follow-up |
| Screenshots in the README | 0.05 h | declined for v0.1.0 (text only) |

## 11b. Hour-saving pass (revision 2)

| Existing thing or cut | What it saves | Verdict |
|---|---|---|
| S2: check `keyblob` is the import of `keyblob_findings()`; checks `version`, `linkage` and `openssl` keep only what f1 lacks; the old check 7 (`inputs`) and plants 6 and 7 go | about 0.04 h and a second copy of B2's fixes | taken |
| S3: SOURCE.md quotes `build.inputs`' `cmake=` line verbatim (step 0 writes the executed words) | about 0.02 h | taken |
| S9: the formula from the keg's own `.brew/openssl@3.rb`, not `brew cat` with a network fallback | about 0.02 h and a report item | taken |
| The note member without hashes (consult section 2): fewer lines to generate and check | about 0.01 h | taken |
| No `--openssl-src` flag in fetch.sh: OSSL is a release asset and a one-time main-loop download (phase-i.md 6), not something users fetch | about 0.02 h (a flag, its pin, its test) | taken |
| G8b's replace file generated from `git show --word-diff=porcelain` of the rewording commits, not typed by hand | about 0.03 h and the "missed a word" risk (risk 7) | taken |
| `git filter-repo --replace-text` with `regex:` lines for the few runs that vary by spacing, instead of one literal line per variant | a handful of lines | taken where needed |
| One private replace file serves G8b and `LAZ_PRIVATE_NEEDLES` (check `private` and `--pre-push`) | a second private file and its upkeep | taken |
| Check `history-bytes` builds its needles with `gate_f2._header_bytes()` at run time (no committed windows, no new parser) | about 0.03 h | taken |
| One default core path (`dl/lazpy-core/azahar_lazpy_libretro.dylib`) in `_paths.py` and `azhost`; the README route needs no `export LAZ_CORE` | the README line, review 2 N3's troubleshooting case, about 0.01 h | taken (P17) |
| The clone's full pytest at I2 (with `LAZ_REQUIRE_EMULATOR=1`) is the I-side test of P17, not a separate suite run in I1 | about 0.05 h of I1 and its machine time | taken (I1 runs the fast pytest only) |
| The consult's five archive checks as I0 shell commands (phase-i.md 5), not a new tool | about 0.03 h | taken |
| The font licence texts read from SNAP when it holds them; downloaded only if not | one download and its pin | taken |
| gitleaks or trufflehog for the history scan | | declined: neither knows the key blob's or ClCertA's bytes; `history-bytes` does, with our own code |
| `vtool -set-build-version` to write minos 15.0 into the core | | declined: the shipped binary would differ from the script's output (review 2 H) |
| OpenSSL built for macOS 11 | | declined for v0.1.0 (risk 9, Q6, Q7) |
| ScanCode or `reuse lint` for NOTICES | | declined (as revision 1) |

Net against revision 1's 2.2 h: review 2's own items about -0.05 h; the consult's conditions about +0.35 h (P17's
code and tests, G8b, the archive notices and checks, the snapshot asset, the standing checks), less the cuts above.
The phase is **about 2.5 h** (section 9).

## 12. Open questions (for the reviews and Phase 3)

For Guy: section 7's table (Q1-Q9). Nothing else.

Review 2's questions, answered:
- Q5 (P16): keep it. The README's route is our core and the test app from our release; the consult's section 7
  makes it stronger (P17 removes the stock core from every default).
- Q6 (G8's timing): settled by events. G8 ran 01:06-01:08, before Phase 3's worktrees existed. G8b runs after they
  are removed (section 2).
- Q7 (the formula): take it from the keg (`KEG/.brew/openssl@3.rb`), not `brew cat` (review 2 S9; phase-i.md 3.2).

Answered from review 1 (H): Q1 (a), by bsdtar `@archive` plus the note member; Q2 no `libazhost.dylib` asset; Q3
keep the fast pytest in the clone, pytest installed explicitly (revision 2: the clone runs the full pytest, risk 12);
Q4 commit the release notes.

Phase 3's asks (review 2 S6):

| # | Ask | State |
|---|---|---|
| 1 | `brew pin openssl@3`, held until the release is published | done 01:04 |
| 2 | `tests/gate_f2.py` imports cleanly from `tools/` (no work at import; `drop` taken as a list of strings) | stands |
| 3 | MAIN's `build-core/build/` and `build-core/build.inputs` stay as F2 gated them until the release: no clean or rebuild between F2 and I2 | stands |
| 4 | G8 before Phase 3's worktrees | done 01:06-01:08 |
| 5 | `build-core.sh` accepts an empty `LAZ_CORE_DROP` | optional; not needed: `core/PIN-nokeys` names the note member as its drop entry (`build-core.sh:40-42` refuses an empty list) |
| 6 | `build.inputs` carries the full cmake command | done (`cmake=`, `build-core.sh:156`) |
| 7 | `externals/libressl` in the drop list | done (`core/PIN:9`) |
| 8 | `MACOSX_DEPLOYMENT_TARGET=15.0` at the next core rebuild (`tools/build-core.sh:15`); with it, patch 0008's comment fix (`keys.txt`) and a new `LAZPY_REV` (consult section 1) | stands, not before v0.1.0 unless Phase 3 rebuilds anyway; if it does before I2, STATUS drops the "header says 11.0" line and check `macos` expects 15.0 everywhere |

## 13. Where every finding went (review 1, review 2, the consult)

### 13.1 Review 1

Blockers:
- B1 ClCertA: Phase 3's P9b (0007, drop list); section 0.2; R1, R28; release_check takes `keyblob_findings()`;
  ip-legal question 1; audit item; section 8 fact corrected.
- B2 the address: the plan line was removed 2026-11-12; needles from a file outside the repo (phase-i.md 3.3 check
  `private`, history content scanned); the rewrite (G8, P15, phase-i.md 8.1); the audit brief names it.
- B3 `env -i` drops DEVKITARM: the build block sets `DEVKITPRO` and `DEVKITARM`; the main route needs no devkitARM
  (P16); Requirements says so (phase-h.md 3.1).
- B4 no pytest: the clone runs `.venv/bin/pip install pytest` first; USING says so (phase-h.md 3.3, 3.7).
- B5 no joined version string: check `version` looks for `2126.2` and `-lazpy.1` separately plus `build.inputs`'
  patch 0005 hash (R3, phase-i.md 3.3).
- B6 compares with uncommitted files: working tree by default, `--pre-push` adds "clean and equal to HEAD"; the
  build-files asset is `git archive` (phase-i.md 3.2, 3.3).
- B7 `8.8.8.8`: the IPv4 FAIL set is the private ranges only; public resolver literals are listed (phase-i.md 3.3).

Should fix:
- S1 built from the stripped tree: Phase 3's drop list; check 10 gone; P10.
- S2 `build.inputs`: Phase 3 writes it; release_check compares its hashes with HEAD; SOURCE.md quotes it (R27).
- S3 the real prefix map: P9 row; SOURCE.md copies the cmake line from `build.inputs`, never a template.
- S4 key loading: 0008 in P9b (Phase 3's Q6, default yes); ip-legal question 1.
- S5 LibreSSL: superseded by G3 (OpenSSL 3, P14); LibreSSL's proof of absence (check `openssl`); NOTICES carries
  no LibreSSL section; SOURCE.md says its sources ride in Azahar's tarball unbuilt.
- S6 citations: section 8 (LibreSSL :17-72/:74-132, faad2 README:12-39 with the Nero line, CMakeLists.txt:509, the
  partial Readme list).
- S7 `src/` notices: mknotices scans DEPS-listed `src/` files and the embedded shaders (phase-i.md 3.1).
- S8 the clone on the pushed tree: at I2 on main by `clone_check.sh`; H2 removed.
- S9 what the flags fetch: every part is a flag that fetches only itself; no flag = today's set; the parser loops
  (phase-i.md 3.4).
- S10 `__version__`: I's row adds `python/libazahar/__init__.py`'s version line; release_check compares both.
- S11 re-stage drift: `git archive`, SOURCE.md without asset hashes (only the source tarballs' sha256 and the tag),
  pins filled at I2.
- S12 the test app from the tag: I2 runs `make testapp` in a clean env before staging.
- S13 D's USING line: fixed in D (721209f); H0 checks it (R21).
- S14 safe defaults: G2 (a), G3 answered, G4 a fact, G5 default, G8 answered, G9 default (section 7).
- S15 audit misses: ClCertA, the history content scan, the research file's game name and product code (G9).
- S16 Phase 3's rows: R12 (no `LAZ_LAZPY_CORE`; `LAZ_PNG_LEVEL`, slot variables), R14 (`SlotTimeout`), R29 (states).
- S17 the consult now: section 2 ("Now"), with the new questions.

Nice:
- N1 `azhost` has no `--help`: R22; phase-h.md 3.4 pastes the usage output and says the exit code is not 0.
- N2 Load and Date tokens checked too: phase-h.md 3.6 check `numbers`.
- N3 the clone script's body: `tools/clone_check.sh` is written out (phase-h.md 3.7).
- N4 R9 wording and R10's count: fixed.
- N5 newlib and the default icon: R23; NOTICES' test-app section.
- N6 the note member inside the tarball: P10.
- N7 drafts visible to push-access users: P13.
- N8 map lines in the same commit: section 3, last row.
- N9 the blob's GPL header does not make keys shippable: section 0.1; the audit brief.
- N10 the layout's 137 rows: declined; HOST-API has no length budget and the full `azhost layout` output in a
  `<details>` block is the reference.

Guy's rulings: G3 OpenSSL 3 (section 0.4, P14, R30, NOTICES, the source asset); G8 the rewrite (section 0.5, P15,
phase-i.md 8.1); G4 stated as a fact; G2 defaults to (a). Q1-Q4 as review 1 recommended (section 12).

Phase 3's decisions taken: Phase 4 does not rebuild (P9b is Phase 3's step 0); R1 holds after F2; check 10 dropped;
`LAZ_LAZPY_CORE` dropped; `LAZ_PNG_LEVEL` and the slot variables added; `SlotTimeout` is a `HostTimeout`; ABI-3
hosts load ABI-2 and ABI-3 states; `keyblob_findings()` imported. New in this revision: the stock core's blob and
ClCertA (section 0.6, P16, risk 12).

The coordinator's P9b facts (2026-11-13, after revision 1 was drafted): the core needs macOS 15+ (R31; chosen: say
"macOS 15 or later", risk 9 with the declined source-built OpenSSL and its cost; check 17; Phase 3 ask 8); OpenSSL's
Homebrew directories are in the core's strings as expected values (R30, risk 14, ch### 13.2 Review 2 (docs/reviews/phase-4-review-2.md)

| Id | Where it went |
|---|---|
| B1 the drop list holds a directory | phase-4.md 0.4, P10, R5, R28; phase-i.md 3.2 (the note lists `externals/libressl/` with its member count, no hashes), 3.3 check `source` (the prefix rule, `untar_checked.py`), 5 I1 (`tar -tf ... \| grep -c externals/libressl` is 0), 9.2 (no LibreSSL in the asset; the consult's 9.1 Q2 is moot) |
| B2 stale step-0 interface | phase-4.md inputs paragraph, R27, R30, section 8; phase-i.md 0 (KEG = `openssl_prefix=`, checked with `cd -P` at I0), 2, 3.1 (classify by KEG), 3.3 checks `keyblob` (`repo=`) and `openssl`; `LAZ_OPENSSL_PREFIX` everywhere; "7c33f38 (799e8c3 before G8)" |
| B3 docs_check forbids STATUS's lines | phase-h.md 2 ("never write 11.0 as a requirement"), 3.6 (`forbidden` holds the claims `macOS 11 or later`, `macOS 11+`, `macOS 11.0 or later`, `macOS 11 and later`, not the number) |
| B4 the test app's `/Users/` strings | phase-4.md 3 (testapp/Makefile row), R33, P19; phase-i.md 3.6 (one `-ffile-prefix-map` line; `strings` count 0; no `-DNDEBUG`), 4, 5 I0 and I1 |
| S1 mtime | phase-i.md 3.3 check `keyblob`: sha256 of the zip's dylib equals CORE's, then `keyblob_findings()` on CORE; the plant copies the core and appends the window |
| S2 release_check repeats f1 | phase-i.md 3.3 (checks `version`, `linkage`, `openssl` shrink; the old check 7 and plants 6, 7 go); section 11b |
| S3 SOURCE.md's build lines | phase-i.md 3.2 (`cmake=` verbatim plus `configure.log`'s two compiler lines); section 12 ask 6 done |
| S4 the rebuild route | phase-h.md 3.3 ("Getting our core"); phase-i.md 3.2 (SOURCE.md, OPENSSL.md's untested recipe ending `make install_sw`), 3.3 check `source` (`untar_checked.py`); Guy Q7 |
| S5 G8 is done | phase-4.md 0.5, 2, 4, P15, risks 15-16, section 11, section 12; phase-i.md 8.1 (a record and the procedure for G8b, 8.1b) |
| S6 Phase 3's asks | section 12's table; section 3 (Phase 4 never edits `core/PIN`); R30; risk 13 |
| S7 Gen3D's four lines | phase-h.md 3.3 and checklist item 5; R35 |
| S8 stale build facts | inputs paragraph, R1, R2, R10; phase-i.md 2 (the 01:06 build) |
| S9 the formula from the keg | P14; phase-i.md 3.2 (OPENSSL.md), 10 (no `brew cat` item) |
| N1 numbering | phase-i.md 3.3 renumbered 1-17 (16 `macos`, 17 `plant-red`) |
| N2 build variables | phase-h.md 3.3 (a "build and fetch" table) |
| N3 `LAZ_CORE` after the route | made moot by P17 (one default core path); phase-h.md 3.3 troubleshooting keeps a "no core at <path>" line with H0's real error text |
| N4 Gen3D's fps | phase-h.md 2 (one sentence: not a README number) |
| N5 Gen3D's rsync copy | phase-i.md 8.1b (the main loop asks Gen3D's session to confirm the copy has no `.git`) |
| N6 the audit brief | phase-i.md 9.2 |
| N7 more key-file words | phase-h.md 3.6 (`title.keys`, `boot9`, `sysdata`, `keys.txt`, `aes_keys`) |

### 13.3 The consult (docs/reviews/release-ip-legal.md)

| Section | Where it went |
|---|---|
| 1 the patched core: GREEN under five conditions | section 0.7, 0.9 (standing checks); patch 0008's comment fix at the next `LAZPY_REV` (section 12 ask 8, no forced rebuild); `.gitignore`'s `keys.txt` (0.3, a fact); phase-h.md 3.6, phase-i.md 3.3 checks `repo` and `history-bytes` |
| 2 the source asset: (a) | P10 (a), G2 answered; phase-i.md 3.2 (the neutral note, no key-header hashes; SOURCE.md says LibreSSL was removed) |
| 3 OpenSSL | 0.4; P19 (NOTICES.md and the GPLv3 text inside the zip); phase-i.md 3.1 (OpenSSL's licence verbatim with its copyright line; NOTICE only if the tarball has one), 3.3 check `assets` (the zip's members) |
| 4 faad2 | phase-i.md 3.1 (the Nero line verbatim); G4 (never a non-GPL licence) |
| 5 the system archives | R34, risk 10, P19 (the snapshot asset); phase-i.md 3.1 (OFL-1.1, Unifont, citra_system_archives sections, the generator commits read from the headers, never "Nintendo's" wording), 5 I0 (the five checks as commands), 6 (SNAP download) |
| 6 the name | section 7 (standing rules; Q8 fallback name; Q9 courtesy note); phase-h.md 3.1 (first paragraph), 3.2 (AI-POLICY in "Considered and dropped"), 3.6 (checks `first-paragraph`, no images) |
| 7 the stock-core fetch: YELLOW | 0.6, P17, Q1, risk 12, R32; phase-h.md 3.1, 3.3 (prose only); phase-i.md 3.4 (stock part removed), 3.5 (the exact code and test changes), 5 I0 (stock grep); the main loop's rules.md 3 and runners lines |
| 8 spike 2's game lines | Q5 (G9); section 2 step 2 (reworded at HEAD); P18 (G8b); phase-i.md 6, 8.1b |
| 9 key fragments in tracked docs | the header rule; done at HEAD (776e8da); P18, G8b (phase-i.md 8.1b: the replace file outside the repo, generated by word-diff); check `history-bytes`; risk 7 |
| 10 what blocks the release | items 1-2: P18 and P17 (or Q1's YELLOW); item 3: P19; item 4: check `keyblob` on the attached binary and P10's note; the audit brief (phase-i.md 9.2) lists all four |

Gen3D's first use (LAZPY-TRY-1.md:46-58): its four USING lines go in H (phase-h.md 3.3); `ArgumentError` and a
`fresh_sd` option come after v0.1.0 (STATUS "Next", phase-h.md 3.2).

## 14. Changes from review 2 (revision 2, 2026-11-13)

- Every review 2 blocker and should-fix is taken (13.2); all seven nice items too (N3 by P17).
- The consult's ten sections are folded in (13.3): P17 (the stock core out of every default, Guy may keep it as an
  opt-in), P18 (G8b), P19 (the zip's notices and the snapshot asset), the standing checks (0.9), the name's
  mitigations and the Guy questions (section 7).
- G8 is a record, not a branch (S5); Phase 3's asks have states (S6).
- release_check is renumbered and leans on `keyblob_findings()` (N1, S2); two new checks (`history-bytes`, and long
  `0xNN` runs inside check `repo`).
- New risks 12 (a hidden stock assumption), 17 (core/PIN's URL) and 18 (a rename); risks 2, 7, 10, 13, 15 and 16
  rewritten.
- Hours: H 0.50, I 0.75, main loop 0.62; the phase is about 2.5 h (section 9, 11b).
