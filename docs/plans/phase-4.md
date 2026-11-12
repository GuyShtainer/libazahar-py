# Phase 4, release: the phase plan (item laz-400)

Opus phase plan, **revision 1** (2026-11-13, a fresh author), after review 1 (`docs/reviews/phase-4-review-1.md`:
7 blockers, 17 should fix, 10 nice), Phase 3 review 2's asks (`docs/reviews/phase-3-review-2.md` sections 4, 8, 9)
and Guy's rulings G3 (OpenSSL 3) and G8 (history rewrite). Steps: H (laz-410, `docs/plans/phase-h.md`) and I
(laz-420, `docs/plans/phase-i.md`). Each brief is complete on its own for one sonnet builder in its own worktree.
This file is the index: goal, order, checkpoints, file ownership, merge plan, departures from PLAN.md, the
interfaces taken from Phases 1-3, what Guy must do, the checked facts, risks, hours and the hour-saving pass.
Section 13 lists every review-1 finding and where it went.

Contract: `docs/PLAN.md` section 2.7 (the release paragraph), section 3's Phase H (PLAN.md:324) and Phase I (:330)
paragraphs, section 5 (out of scope: CI, PyPI, Windows/Linux). (The step item files still point at :317 and :323;
the main loop fixes those pointers when it moves the items.) Where a brief disagrees with PLAN.md on a goal, PLAN.md
wins and the builder stops and reports, **except for the approved departures** (Phase 2's P1-P6, Phase 3's P7-P8 and
its step-0 "P9b", and this plan's P9-P16 in section 5 once review 2 and Guy approve them).

Inputs: main at 4d76406 (2026-11-13 00:50): Phases 1 and 2 done (step D merged, a113cf6); P9 (e40e59c); **P9b
committed (5e95423) and its rebuild running in MAIN since 00:49** (`build-core/build.inputs` written, `head=5e95423`,
`clean=yes`); Phase 3 at revision 2 being written. P9b is Phase 3's step 0: patch 0007 (no default ClCertA), patch
0008 (load no keys), the drop list `LAZ_CORE_DROP` in `core/PIN` (`default_keys.h` and the two `ctr-common-1-*.h`
headers deleted after the unpack), `build-core/build.inputs`, a static OpenSSL 3 (`OPENSSL_VERSION=3.6.5`,
`OPENSSL_ROOT=/opt/homebrew/opt/openssl@3` in `core/PIN`) instead of the bundled LibreSSL (G3); F2 then gates it
with `keyblob_findings()`. **Phase 4 does not rebuild.** Most of what Phase 4 documents is not merged yet, so section 6 marks each row holds or
planned, and both briefs start with a step 0 that checks the planned rows against the merged code. If the code differs
from a row, the builder follows the code and reports the row; if a row's feature is missing or its gate failed, the
docs say "not done" for it (never a claim).

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
   `.3dsx` needs no keys; F2's gate proves it. Default yes (Phase 3's Q6).
4. **OpenSSL 3 instead of LibreSSL** (Guy G3, "Switch to OpenSSL 3"): LibreSSL's OpenSSL and SSLeay licences are
   GPL-incompatible on their texts (COPYING:17-72, :74-132, :127-131). P9b links Homebrew's static
   `libssl.a`/`libcrypto.a` (OpenSSL 3.6.5, Apache-2.0, GPLv3-compatible) through `USE_SYSTEM_OPENSSL`. So Phase 4
   ships **OpenSSL's exact source**, the upstream release tarball `openssl-3.6.5.tar.gz` pinned by sha256, as part of
   the Corresponding Source (P14); carries OpenSSL's Apache-2.0 licence verbatim in NOTICES (Apache-2.0 4(a)) and a
   NOTICE file's text only if the tarball has one (4(d); evidence so far: none, section 8; I0 decides from the
   tarball's member list); and removes LibreSSL from every duty list, after proving from the link line, the `.o.d`
   files and the binary's strings that `externals/libressl` is not linked (I0, `release_check` check `openssl`).
   LibreSSL's sources stay inside Azahar's tarball (we re-host that tarball minus the drop list), unbuilt; SOURCE.md
   says so.
5. **Guy's personal address is in this repo's history** (review 1 B2; Guy G8, "Rewrite before push"): one plan line
   (added in 15d0323, removed from the tree on 2026-11-12) named its local part. A scan on 2026-11-13 00:55 finds it
   in 6 of 93 commits (15d0323 to 8a16f9e), one path (`docs/plans/phase-i.md`), 0 commit messages, 0 at HEAD. The
   main loop rewrites history with `git filter-repo` before the first push (P15, phase-i.md section 8.1), from a
   replacement file kept outside the repo and never named in a tracked file. 15d0323 and the 19 commits after it on
   main get new SHAs. **Recommended timing: as soon as the P9b build ends and before Phase 3's worktrees are made**:
   today only `main` holds the affected commits (`step-c` and `step-d` do not), so no worktree branch is rewritten and
   the commit map stays at about 25 rows. The running build's `build.inputs` says `head=5e95423`, a pre-rewrite SHA:
   `release_check` never compares `head=` (it compares the input hashes), and SOURCE.md translates it through
   `docs/commit-map-g8.tsv`.
6. **New in revision 1: the stock core carries the blob and ClCertA too.** Azahar's own macOS libretro build, which
   `tools/fetch.sh` downloads and revision 0's README route used, holds the key blob and the ClCertA arrays
   (`python3 -I` byte search of
   `dl/azahar/azahar_libretro.dylib`, 2026-11-13). We never re-host it, but our script fetches it. So the README's
   default route becomes **our core and the test app from our release** (`tools/fetch.sh --moltenvk --headers
   --lazpy-core --testapp`), the stock core is optional (plain `tools/fetch.sh`, for contributors comparing cores),
   and ip-legal question 7 asks whether fetching it at all is within policy rule 7 (P16, risk 12).

## 1. Goal and the two steps

Goal: a public GitHub repo `GuyShtainer/libazahar-py` and a first release that a stranger can use from the README
alone, that says nothing it has not measured, that ships no key, certificate or private string, and that meets every
licence obligation of the binary it ships, with the legal audit saying shippable. Push and publish only on Guy's word.

| Step | Delivers | Gate (headless, this Mac) | Hours |
|---|---|---|---|
| H, laz-410 | `README.md` rewritten; `STATUS.md`; `docs/USING.md` finished; `docs/HOST-API.md`; `examples/quickstart.py` (= the README block), `pool_shots.py`, `memory_watch.py`, `examples/README.md`; `tools/docs_check.py`; `tools/clone_check.sh` (the fresh-clone run, used at I2) | `python3 -I tools/docs_check.py --allow-missing NOTICES.md` passes and `--plant-red` fails on each plant; the three examples on this Mac (quickstart on our core and on the stock core, pool, memory on both cores); `sh -n tools/clone_check.sh` and its `--dry-run` | 0.45 |
| I, laz-420 | `NOTICES.md` (generated: link inputs, DEPS externals, Azahar `src/` notices, OpenSSL 3); `tools/mknotices.py`, `tools/mkrelease.sh`, `tools/release_check.py`; `core/PIN-nokeys`, `core/OPENSSL.md`; `tools/fetch.sh` part flags; `docs/release-notes/v0.1.0.md`; `core/README.md` licence lines; the version in `pyproject.toml` and `python/libazahar/__init__.py` | `python3 -I tools/release_check.py runs/release/v0.1.0 --skip-pins` passes and `--plant-red` fails on each plant; `fetch.sh --lazpy-core --testapp` against a `file://` base verifies, refuses a flipped byte, downloads nothing on a second run; `--openssl-src` finds the seeded tarball and downloads nothing | 0.65 |
| Main loop and legal agents | ip-legal consult (I-pre, now); the history rewrite (G8); I2 (test app built clean, stage, pins commit, checks, the fresh clone of main); I3 audit; I5 after publishing | section 2 | 0.5 |

Phase total: H 0.45 + I 0.65 + one joint as-built review 0.2 + main loop and legal agents 0.5 + review loops 0.4 =
**about 2.2 h**, against PLAN.md's 0.5 + 0.6 = **1.1 h** (plus loops PLAN counts separately). Section 9 names the
over-run per step: the key blob and ClCertA, generated notices, OpenSSL's source, the history rewrite.

## 2. Order, checkpoints and the parallel split

```
Now (main loop, independent of Phase 3's builders):
  I-pre: the ip-legal consult (phase-i.md 9.1), so Q6/0008, G2 and question 7 are answered before step 0 builds
  G8:    the history rewrite (phase-i.md 8.1), when the P9b build has ended, no agent writes in MAIN, MAIN's
         tracked tree is committed, and before Phase 3's worktrees are made (recommended)
Before launch: Phase 3 merged (E, F2, G), its phase-end suite passed; F2 gated P9b's core (0007, 0008, drop list,
  OpenSSL 3, build.inputs); `brew pin openssl@3` held since P9b (risk 13)
  |
  H builder (sonnet, ../libazahar-py-h, step-h)        I builder (sonnet, ../libazahar-py-i, step-i)
  |  H0: seed, link OURS, check section 6's rows       |  I0: seed, link OURS; rows; keyblob_findings() empty;
  |  H1: examples, docs_check, clone_check.sh,         |      OpenSSL linked and LibreSSL not (else STOP)
  |      README, STATUS, USING, HOST-API; runs          |  I1: mknotices, mkrelease.sh, release_check, fetch.sh
  |  ENDS ITS RUN: "H1 done"                            |      flags, OPENSSL.md, PIN-nokeys, notes; stage+check
  |  main loop commits H1 on step-h (+ map lines)       |  ENDS ITS RUN: "I1 done"
  |                                                     |  main loop commits I1 on step-i (+ map lines)
  v_____________________________________________________v
  one opus as-built review over both diffs (phase-h.md 12, phase-i.md 12); fixes by the resumed builders; commit
  merge step-h, then step-i, into main; items 410 (Evidence: H1's gates) moves; worktrees removed (porcelain empty)
  [G8 here if not done "now": no worktree left, so nothing else is rewritten; then re-run the checks]
                         |
  I2 (main loop, MAIN, 0.15 h): make testapp in a clean env; tools/mkrelease.sh v0.1.0; fill fetch.sh's pins from
     the staged files and commit; release_check (with the needle file); docs_check (no --allow-missing);
     tools/clone_check.sh on a fresh clone of main with LAZ_RELEASE_BASE=file://.../runs/release/v0.1.0 (background)
  I3: release-legal-audit on main + its (rewritten) history + runs/release/v0.1.0
  I4: BLOCKERs -> the I (or H) builder resumed -> re-stage, re-check, re-audit the changed items only
                         |
  WAITING ON GUY: G5 (repo, PAT), G6 "push", G7 publish, G9 (ownership wording)
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
  fast pytest. The README's route needs the release, which does not exist before the push, so the one deviation is
  `LAZ_RELEASE_BASE=file://<MAIN>/runs/release/v0.1.0` (fetch.sh's own override, I's); I5 repeats the clone against
  the real URLs after publishing.
- **H and I run side by side.** Neither runs a timed test; H runs one nice'd instance at a time (three for the pool,
  through the slot cap); I runs none. Nothing in Phase 4 is timed, so no speed number comes from Phase 4 (rules.md 7).
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
| `docs/HOST-API.md` (new) | H | phase-h.md 3.4 |
| `examples/quickstart.py`, `pool_shots.py`, `memory_watch.py`, `examples/README.md` (new) | H | phase-h.md 3.5 |
| `tools/docs_check.py`, `tools/clone_check.sh` (new) | H | phase-h.md 3.6, 3.7 |
| `NOTICES.md` (new, root), `tools/mknotices.py` (new) | I | phase-i.md 3.1 (P11) |
| `tools/mkrelease.sh`, `tools/release_check.py`, `core/PIN-nokeys`, `core/OPENSSL.md` (new) | I | phase-i.md 3.2, 3.3 |
| `tools/fetch.sh` | I | the part flags, the release pins block, `LAZ_RELEASE_BASE` (phase-i.md 3.4) |
| `core/README.md` | I | the "Licenses" section only (phase-i.md 4) |
| `docs/release-notes/v0.1.0.md` (new) | I | phase-i.md 3.2 |
| `pyproject.toml`, `python/libazahar/__init__.py` | I | the version line in each, `0.1.0` (review 1 S10); nothing else |
| `tools/fetch.sh` pins (the two sha256 lines) | the main loop at I2 | filled from the staged files, one commit before the push (S11) |
| `docs/commit-map-g8.tsv` (new), one pointer line in `docs/map/README.md` | the main loop (G8) | old-to-new SHAs of the rewritten commits |
| `docs/reviews/release-ip-legal.md`, `release-legal-audit-v0.1.0.md`, `phase-4-as-built.md` | the agents (via the main loop) | their reports, verbatim |
| `docs/map/code.md`, `tools.md`, `runners.md` lines; `.gitignore` if needed | the main loop | **in the same commit** as the files they map (H1's, I1's), since `map_check.py` fails otherwise (N8) |

A file listed for one step is never edited by the other. H's README **links** `NOTICES.md` and names fetch.sh's new
flags; it does not write them. I's release notes **link** the README; they do not restate its numbers. **No builder
edits a file outside its rows.** Nobody in Phase 4 touches: `host/`, `python/` (except I's one version line),
`testapp/`, `tests/` (I imports `tests/gate_f2.py`, read only), `core/patches/`, `core/PIN`, `tools/build-core.sh`,
`docs/PLAN.md`, `docs/plans/*`, `docs/research/*` (read only: the sources of every number), `docs/hours.tsv`, the
handoff, **every item file**, `prototype/`, `LICENSE`, and MAIN (read and copy only; MAIN's `build-core/` and `dl/`
are read only). A code bug found while writing docs is reported, not fixed: the docs describe the code as it is.
Lines the main loop must add and the "Lessons and notes" blocks go in each report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. Before launch: section 2's conditions. `git worktree list` and the case-insensitive name check (`ls .. | grep -i
   libazahar-py-`), then `git worktree add -b step-h ../libazahar-py-h main` and `git worktree add -b step-i
   ../libazahar-py-i main`. Dispatch both sonnets without isolation, cwd in the worktree. Agent ids into the handoff.
2. At "H1 done" and "I1 done": commit exactly the listed paths with their map lines on each branch (`git add <paths>`,
   `git diff --cached --stat`, `tools/map_check.py`, `status_check.py --strict-handoff`).
3. One opus as-built review over both diffs (`git diff main step-h`, `git diff main step-i`), writing
   `docs/reviews/phase-4-as-built.md` with phase-h.md 12 and phase-i.md 12 as its checklists. Fixes by the resumed
   builders; commit.
4. Merge `step-h` into main (item 410 moves with its Evidence in the same commit), then `step-i` (no shared file; a
   conflict stops and goes to the main loop). Remove each worktree after `git status --porcelain` is empty in it;
   delete the merged step branches (`git branch -d`).
5. G8 now if it was not done earlier (phase-i.md 8.1).
6. I2 (phase-i.md section 6). Both `release_check` and `docs_check` pass and the clone ends `clone ok`, or the builder
   whose file failed is resumed (a fresh sonnet with its brief if its worktree is gone).
7. I3 (phase-i.md 9.2); the report verbatim to `docs/reviews/release-legal-audit-v0.1.0.md`; BLOCKERs to I4; commit.
8. Waiting on Guy (section 7). On "push": phase-i.md section 8.2's commands in order. Then I5. Items 420 and 400 move
   to done with their Evidence (the release URL, the audit verdict, I5's lines).

## 5. Departures from PLAN.md (proposed; review and Guy approve or reject)

| # | PLAN.md says | Phase 4 does | Why |
|---|---|---|---|
| P9 | PLAN 2.7's build flags | done in Phase 3: `-DENABLE_BUILTIN_KEYBLOB=OFF` and `-ffile-prefix-map=$PWD/=` (e40e59c; the strings now read `dl/azahar-src/build-src/...`, review 1 S3). P9b (Phase 3 step 0) adds 0007, 0008, `LAZ_CORE_DROP`, OpenSSL 3, `build.inputs`; Phase 4 only checks them | section 0 |
| P10 | "Azahar's unified tarball **re-hosted unchanged**" | option (a), the default (G2): Azahar's tarball minus `LAZ_CORE_DROP`, made by stock bsdtar from the original without extracting (`tar -cJf ... --exclude ... @TARBALL`), plus one member `LIBAZAHAR-PY-REMOVED.txt` at its top (the removed paths, their sha256, the date: GPLv3 5(a)'s notice inside the source itself, N6). The binary is **built from the stripped tree** (P9b), so the asset is the build's own input, not a proof after the fact (S1). (b) points at Azahar's tarball (GPLv3 6(d), lawful only under GPLv3, with a standing duty to keep it available, and it points users at the blob and ClCertA); (c) re-hosts both: not offered | the unchanged tarball holds the key blob and ClCertA |
| P11 | PLAN Phase H delivers `NOTICES.md` | step I generates it from the link line, the DEPS externals, the `src/` third-party notices (S7) and OpenSSL's tarball; H links it | the notices are the binary's licence obligation |
| P12 | the `fetch.sh` pin after the release | the pins are filled by the main loop at I2 from the files staged on main and committed **before** the push (S11); I1 stages with placeholders and `--skip-pins`; I5 checks the real URLs | one push instead of two, and no pin cycle in I1 |
| P13 | "Guy says push" | plus a **draft prerelease** (`gh release create --draft --prerelease`) that Guy publishes; a draft is visible to anyone with push access to the repo (here only Guy, N7) | Guy sees the exact assets first |
| P14 | (PLAN predates G3) | the release also attaches `openssl-3.6.5.tar.gz`, byte-identical to OpenSSL's own release asset (sha256 pinned in fetch.sh and `core/OPENSSL.md`), and `core/OPENSSL.md` records how the linked libraries were built (Homebrew's bottle, its configure line, no patches) | GPLv3 Corresponding Source includes statically linked libraries' source and build scripts |
| P15 | (PLAN assumed a clean history, rev 0's R10) | the main loop rewrites this repo's history before the first push (G8) and commits `docs/commit-map-g8.tsv` | Guy's privacy rule; the address's local part sits in 6 commits |
| P16 | PLAN Phase H: the README route uses `fetch.sh` (stock core) and the test app built with devkitARM | README's default route is our core and the test app from our release; the stock core and `make testapp` are the "build or compare" block | the stock core carries the key blob and ClCertA (section 0.6); the route then needs no devkitARM; ip-legal question 7 |

Not departures (interpretations): the fresh clone of the README runs at I2 on main with a `file://` release base
(section 2) and again at I5 with the real URLs; the memory example on our core is gated in H1 and I5.

## 6. Interfaces taken from Phases 1-3

"State": **holds** (checked on main, D at 721209f, or MAIN on 2026-11-13), **planned** (from a plan, not built yet;
step 0 checks it), **proposed**.

| # | What Phase 4 relies on | Source | State | Used by |
|---|---|---|---|---|
| R1 | Our core built by P9b (5e95423: 0007, 0008, the drop list, OpenSSL 3, `build.inputs`; the build started 00:49) and gated by F2's f1 (`keyblob_findings()` empty) and F2's full batch on that build | phase-3 rev 2 step 0; phase-f2 f1 | building (holds after F2) | I, H (STATUS) |
| R2 | `build-core/azahar_lazpy_libretro.dylib`: `strip -x`, ad-hoc `codesign`, installed atomically (P9b, N8); install name `@rpath/azahar_libretro.dylib`; `otool -L`: Cocoa, AVFoundation, IOSurface, CoreFoundation, libc++, libSystem only; P9b build (00:52): 21,828,992 bytes (the 21:09 build was 19,145,936; OpenSSL 3 static adds the difference), `vtool -show-build`: minos 11.0, sdk 26.2 (see R31) | build-core.sh; `otool -L`; coordinator 2026-11-13 | holds on P9b | I |
| R3 | Exports: 25 `_retro_*` + `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play`. Version: the strings `2126.2` and `-lazpy.1` are separate (patch 0005 joins them at run time); `LAZPY_REV=1`, no bump (Phase 3 review 2 N7) | review 1 A, B5; patches 0001, 0005, 0006 | holds (exports); planned (F2) | I |
| R4 | The link line `build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt`: cryptopp, mcl, dynarmic, enet, faad2, fmt, SPIRV, glslang, boost_iostreams, boost_serialization, zstd_seekable, lodepng, sirit, SoundTouch, SPIRV-Tools, SPIRV-Tools-opt, teakra, xxhash, zstd, Azahar's five libs, and after P9b **Homebrew's `libssl.a` and `libcrypto.a`** (OpenSSL 3.6.5) with no `externals/libressl` path | link.txt (21:09); P9b | holds for 21:09; planned (OpenSSL) | I (`mknotices.py`, check `openssl`) |
| R5 | `core/PIN`: tag 2126.2, commit 219d743a..., `SRC_URL`, `SRC_SHA256=85c8b56f...a4cd26`, `SRC_SIZE=43224348`, `SRC_TOP=azahar-unified-source-2126.2`, `LAZPY_REV=1`, and after P9b `LAZ_CORE_DROP=src/core/hw/default_keys.h src/core/hle/service/http/ctr-common-1-cert.h src/core/hle/service/http/ctr-common-1-key.h` | core/PIN; phase-3 review 2 section 4 | holds; planned (drop list) | I |
| R6 | TARBALL `dl/azahar-src/src.tar.xz` verified; the build tree is `dl/azahar-src/build-src/<SRC_TOP>/` (stripped by P9b; DEPS paths name `build-src`); the reading copy `dl/azahar-src/unpacked/<SRC_TOP>/` keeps every file (the byte windows' source); `LAZ_CORE_PIN` overrides the pin file | build-core.sh:7, 43-44, 60-80 | holds | I |
| R7 | `tools/fetch.sh`: `get URL SHA FILE`, `ok`, `verify`, `sha_of`, pins block at the top, `LAZPY_ROOT`; **the parser takes one argument** (`case "${1:-}"`, fetch.sh:38-43, `--force` only); no `LAZ_RELEASE_BASE` yet | fetch.sh | holds | I (rewrites the parser), H (README) |
| R8 | `make` builds `build/libazhost.dylib`, `build/azhost`; `make testapp` needs `DEVKITPRO` and `DEVKITARM` set (testapp/Makefile:5-6 stops with "Set DEVKITARM") and devkitARM first in PATH | Makefile:9, 24, 38, 45 | holds | H, I2 |
| R9 | `.gitignore` lists `*.tar`, `*.tar.xz`, `*.tar.gz`, `*.zip`, `*.dylib`, `*.3dsx`, `dl/`, `vendor/`, `runs/`, `build/`, `build-*/` (covers `build-core/`) and the game/system list (N4) | .gitignore | holds | H, I |
| R10 | Every commit's author and committer is the no-reply identity (93 commits, `git log --all`, 2026-11-13); **the content is not clean** until G8 (section 0.5) | `git log --format` | holds (identity); planned (content, G8) | I, main loop |
| R11 | `pyproject.toml`: name `libazahar-py`, version `0.1.0.dev0`, `requires-python >=3.10`, `license = "GPL-3.0-or-later"`, setuptools>=77, package-dir `python`; **no pytest in any dependency or extra** (B4); `python/libazahar/__init__.py:8` holds `__version__ = "0.1.0.dev0"` (S10) | main (D merged, a113cf6) | holds | H (install, tests), I (versions) |
| R12 | Environment: `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE` (Python and `azhost`; the default core is `<root>/dl/azahar/azahar_libretro.dylib`, `_paths.py:34-36`; there is no default for our core), `LAZ_MVK`, `LAZ_PROFILE`, `LAZ_LAZPY_PROFILE` (F2), `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT` (default 3600 s) (E), `LAZ_PNG_LEVEL` (C side, 0-9, default 1, E), `LAZ_LOG_LEVEL` (`host/log.c:40`), `LAZ_ANY_CORE` (`host/core.c:64`), `MVK_CONFIG_LOG_LEVEL` (`host/api.c:261`), `LAZ_STATE_ANY_APP` (C, `host/state.c:370`); tests only: `LAZ_REQUIRE_EMULATOR`. **No `LAZ_LAZPY_CORE` exists** (Phase 3 review 2 S5) | `python/libazahar/_paths.py`, host/; phase-3 rev 2 section 12 | holds (A-D); planned (E, F2) | H |
| R13 | `Emulator(app, workdir, *, sd_seed, state, core, options, timeout, boot_timeout)`, `run(...) -> RunResult`, `run_until`, `run_frame`, `set_keys`, `set_input`, `screens()`, `shot(path_prefix)` (returns two paths), `save_state()`, `load_state()`, `stats()`, `sd`, `pid`, `closed`, `frame_total`, `close()`, context manager; `Buttons` names = libctru | `python/libazahar/emulator.py` | holds | H |
| R14 | Errors `LibAzaharError`, `BootError`, `GuestError`, `HostTimeout`, `HostCrashed`, `StateError`, `NeedsLazpyCore`, `HostError`, `ValueError` for bad args; `GuestMemoryError` (P7); **`SlotTimeout(HostTimeout)`**: `.op == "slot"`, `.seconds`, text "no libazahar slot free after <s> s: all <cap> are held; see <dir>"; `HostCallError` internal | `python/libazahar/errors.py`; phase-3 rev 2 section 12 | holds (D's); planned (E, G) | H |
| R15 | `Pool(n, app, root, *, factory=None, **emulator_kwargs)`: `submit`, `map`, `close(wait=True)`; `LoadWarning`; the default cap (E's rule); fake workers take no slot | phase-e 3.2-3.3 (rev 2, B3) | planned | H |
| R16 | `emu.memory` (`read`, `write`, `u8`..`u64`, `s8`..`s64`, `write_u8`..`write_u64`, `.raw_read`), `run(..., watch=[(addr, words)], watch_every=)`, `RunResult.watch` of `WatchRow` (`.u32(entry, word)`, 1-based batch frame); our core only | phase-g 4 | planned | H |
| R17 | `core/options-lazpy.txt` applied automatically on our core (P8); `azhost --lazpy-profile FILE\|none` (relative to the cwd) | phase-f2 3.2-3.3 | planned | H |
| R18 | `docs/research/speed-table-e.md`: per row date, commit, core and version, load at start and end, guest fps, x real time, CPU and wall ms per frame, the guest-time check; light-scene label; the cap and its rule | phase-e 7 | planned | H |
| R19 | `docs/research/spike-2-real-scene.md:30-42`: 334-345 fps, 5.6-5.7x at load 26.7 (16:07); 129 fps, 2.2x at load 68-96; 3 instances 136-138 fps at 58-90; 0.5-0.8 GB per instance; "a clean re-measure on a quiet machine is still owed". Lines 22 and 57 name a commercial game and its product code (audit item, S15); line 37 says "51x" | the file | holds | H, I3 |
| R20 | F2's report (repeat exactness on our core, the debug-stop frame, stock states into ours, `stock_r1`); C's input offsets; D's state-boot times | items' notes after each merge | planned | H |
| R21 | `docs/USING.md`, D's 12 sections; section 11 now says repeats are exact only on our core (D's as-built fix N13, 721209f, review 1 S13), G's "Guest memory" section | main; phase-g 4 | holds (D); planned (G) | H |
| R22 | `host/azhost.h` (every `azh_*` with its comment, the error enum, the limits); `build/azhost layout` prints `abi=<n>` and every `fields[]` row; ABI 3 after G; **`azhost` has no `--help`**: any other first argument prints the usage to stderr and exits non-zero (`azhost_main.c:34-40, 159-160`) | A, C, G | holds (ABI 2); planned (ABI 3) | H |
| R23 | `build/testapp.3dsx` is ours (GPLv3-or-later; glyphs and shader ours; libctru, citro2d, citro3d zlib; newlib's libc/libm BSD-style; libctru's default icon in the SMDH, no `ICON` in testapp/Makefile) | testapp/README.md; font.c:1; N5 | holds | I (NOTICES' test-app section) |
| R24 | The test app's log `testapp/log.txt` (`k=%08lx`, record.c:58; sdlog.c:51), markers, `control.txt` keys (`tests/testapp_log.write_control`) | phase-b; D | holds | H |
| R25 | Spike 1's ~50x (and spike 2's "51x") is an idle menu and is never quoted | spike-1:9, 55; spike-2:37 | holds | H |
| R26 | No remote; `gh` 2.95.0, logged in as **GuyShtainer** (keyring OAuth); `git push` uses the osxkeychain PAT, fine-grained "Contents: read/write" (a PAT scoped to selected repos does not cover a new repo: 403) | `gh auth status`; review 1 E | holds | I (section 8.2), G5 |
| R27 | `build-core/build.inputs` (P9b, written before the compile, `tools/build-core.sh:130-145`): `tarball=`, `pin=`, `script=`, one `patch <name>=<sha256>` per patch (0000-0008), `drop=`, `openssl=3.6.5 /opt/homebrew/opt/openssl@3 libssl.a=<sha256> libcrypto.a=<sha256>`, `head=` (a pre-rewrite SHA, section 0.5), `clean=yes\|no`, `cmake=` (the cmake binary only: the flags are in `build-core.sh`, whose sha256 is `script=`). Today's: head 5e95423, clean yes, libssl.a 23c6a50d..., libcrypto.a 88981a4c... | build-core/build.inputs (00:49) | holds (re-read after the build ends) | I (SOURCE.md quotes it; release_check compares its hashes with the checkout) |
| R28 | `tests/gate_f2.py: keyblob_findings(build_dir, core, src_root, tree, drop) -> list[str]` (build.inputs matches the checkout's inputs and lists 0007 and 0008; drop-list files absent from `build-src/<TOP>/`; no `.o.d` names any of the three headers; none of 8 windows of each of the three arrays in the core; no `/Users/` and no "ClCertA file missing, using default" string); an empty list means pass | phase-3 review 2 sections 4, 8.1 | planned | I (imported by release_check) |
| R29 | States: an ABI-3 host loads ABI-2 and ABI-3 states; an ABI-2 host refuses ABI-3 states (`host/state.c:395-396`, `meta.abi < 2 \|\| meta.abi > AZH_ABI_VERSION`) | D; phase-3 rev 2 section 12 | holds (D); planned (G) | H (STATUS, USING) |
| R30 | Homebrew `openssl@3` 3.6.5: `/opt/homebrew/opt/openssl@3/lib/libssl.a` (1,475,544 bytes) and `libcrypto.a` (8,593,624), built 2026-09-29 as a bottle (`INSTALL_RECEIPT.json`: poured from bottle); the keg's `sbom.spdx.json` names the source `https://github.com/openssl/openssl/releases/download/openssl-3.6.5/openssl-3.6.5.tar.gz`, sha256 `a2157c2830efdec3788939b00c9b0638306d3f0bbb76dc4832ee503bb397df98`, the bottle sha256 `0994a8029175af4578c3b93b3020e58dffa638ca21dc22d862c6bc02fea7e73b`, licence Apache-2.0, no patch entries; `openssl version -a`: platform `darwin64-arm64-cc`, compiler flags `-fPIC -arch arm64 -O3 -Wall -DL_ENDIAN -DOPENSSL_PIC -D_REENTRANT -DOPENSSL_BUILDING_OPENSSL -DNDEBUG`, `OPENSSLDIR "/opt/homebrew/etc/openssl@3"`. The two `.a` files' sha256 equal `build.inputs`' (checked 00:58); `openssl@3` is **not** `brew pin`ned yet. The core holds OpenSSL's compiled-in directories as strings: `OPENSSLDIR` `/opt/homebrew/etc/openssl@3` (its `cert.pem`, `certs`), `ENGINESDIR` and `MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`; 0 `/Users/` strings (coordinator, P9b) | the keg, 2026-11-13 | holds (re-checked at I0 against `build.inputs`) | I |
| R31 | **The core needs macOS 15 or later.** The linker warns that every object in the keg's `libcrypto.a` was built for macOS 15.0, while the core's `LC_BUILD_VERSION` says minos 11.0 (`tools/build-core.sh:15` exports `MACOSX_DEPLOYMENT_TARGET=11.0`). Our `build/libazhost.dylib` and `build/azhost` are already minos 15.0 (the Makefile sets no target, so clang uses the SDK host default) | coordinator, P9b link log; `vtool -show-build` 2026-11-13 | holds | H, I |

## 7. Waiting on Guy

Only Guy can do or decide these. Every item has a safe default, so nothing below blocks a step before the push (S14).

- **G1 (answered).** Key blob off before F2: done (P9, e40e59c). ClCertA (0007) and "load no keys" (0008) go into
  the same P9b rebuild (Phase 3's Q6, default yes).
- **G2 (default (a)).** The source asset: P10 (a), the tarball minus the drop list. I builds (a). If Guy picks (b)
  after ip-legal answers, I4 drops one asset and SOURCE.md's paragraph.
- **G3 (answered 2026-11-13: "Switch to OpenSSL 3").** P9b links a static OpenSSL 3; Phase 4 ships its source and
  licence (P14). If ip-legal says counsel on rule 7 for the core as a whole (question 1), the default stays: release
  the repo, the test app and the build files without the core binary and its source assets, and STATUS says why.
- **G4 (a fact, not a question).** The core binary goes out under GPLv3 only (Azahar's "or later"): it links
  Apache-2.0 code (SPIRV-Tools, and now OpenSSL 3), which GPLv2 does not accept. NOTICES and core/README state it.
- **G5 (account step).** Guy creates the public repo `GuyShtainer/libazahar-py` on the web (default), or tells the
  main loop to run `gh repo create` (no push). The push uses git's osxkeychain PAT: if it is scoped to selected repos,
  Guy adds the new repo to it, or approves `gh auth setup-git` (git then uses gh's GuyShtainer token). `git
  ls-remote origin` must work before any push.
- **G6. "Push."** Main and the tag, and the draft release: only on his word.
- **G7. Publish** the draft (or "publish" and the main loop runs `gh release edit --draft=false`). Version default
  `v0.1.0`, prerelease. Hygiene defaults: keep the tracked `claude.ai/artifact/...` links and the `/Users/guyshtainer`
  paths in plan and review files (the username is his GitHub handle) unless the audit grades them above INFO.
- **G8 (answered 2026-11-13: "Rewrite before push").** The main loop rewrites history before the first push (P15,
  phase-i.md 8.1). Recommended timing: as soon as the P9b build has ended (it has, 00:52) and before Phase 3's
  worktrees are made. Without the rewrite the default is "do not push".
- **G9 (new; default: say nothing).** Spike 2's real-scene numbers come from a commercial game run locally. Policy
  ("Method": start from lawfully owned cartridges and say so) suggests STATUS say the scene came from a cartridge Guy
  owns. Only Guy can say that. Default: no ownership line; the README names no game ("one commercial game, local
  only, busy machine"); the audit grades the research file's game name and product code (lines 22, 57).

## 8. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (GIT-COMMIT 219d743a..., GIT-TAG 2126.2). "CORE" =
`build-core/azahar_lazpy_libretro.dylib` (21:09 build until P9b replaces it). "STOCK" = `dl/azahar/azahar_libretro.dylib`.

| Fact | Where |
|---|---|
| `option(ENABLE_BUILTIN_KEYBLOB ... ON)`; the define when on; `default_keys.h` added to `citra_core` only when on (the only CMake reference) | SRC CMakeLists.txt:154; src/CMakeLists.txt:186-187; src/core/CMakeLists.txt:501-503 |
| `default_keys.h` 46,817 bytes, `#error` guard :7-9, array :11; `key.cpp` includes it under `#ifdef` (:21-23) and reads it (:302-312); every key path goes through `GetKeysStream()` (:292-314) | SRC src/core/hw/ |
| ClCertA: `ctr-common-1-cert.h` (1,264-byte array) and `ctr-common-1-key.h` (1,232) included without `#ifdef` at `http_c.cpp:37-38`; fallback at :2281-2289; `DecryptClCertA()` returns at the missing slot 0x0D (:2262-2266); in no CMake file | SRC src/core/hle/service/http/; review 1 A; Phase 3 review 2 B1, N1 |
| The 21:09 build: cache `ENABLE_BUILTIN_KEYBLOB:BOOL=OFF` (:728), the blob absent, no `.o.d` names `default_keys.h`, 0 `/Users/` strings, ClCertA arrays present, one `.o.d` names `ctr-common-1-*` | review 1 A; Phase 3 review 2 section 3 |
| STOCK holds the blob and both ClCertA arrays; 198 `libressl` strings | `python3 -I` byte search, 2026-11-13 |
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

## 9. Hours, against PLAN.md (agent wall time)

| Step | Builder | Review | Commit | Total | PLAN.md | Why the difference |
|---|---|---|---|---|---|---|
| H | 0.4 (H0 0.05, H1 0.35) | (joint) | 0.05 | **0.45** | 0.5 | the clone moved to I2 (-0.15 with its commit-resume cycle); docs_check without `stray-numbers` (-0.02); `clone_check.sh` (+0.03) |
| I | 0.6 (I0 0.1, I1 0.4, I4 0.1) | (joint) | 0.05 | **0.65** | 0.6 | no `release_pack.py` and no configure check (-0.11); OpenSSL's notice, source asset and `OPENSSL.md` (+0.05); the `src/` notice scan (+0.03); needles and the LibreSSL proof (+0.03) |
| Joint as-built review (H and I) | | 0.2 | | **0.2** | | one opus run over two small diffs, instead of 0.15 + 0.15 |
| Main loop and legal agents | ip-legal 0.1, G8 rewrite 0.1, I2 0.15, I3 audit 0.1, I5 0.05 | | | **0.5** | (in I's 0.6) | the rewrite (G8) and the clone at I2 are new |
| Review loops | | | | 0.4 | | two loops |
| **Phase** | | | | **2.2** | **1.1** + loops | |

Guy's time: G5 (5 min), G6 and G7 (5-10 min), G9 (a minute). Machine time: the clone at I2 (about 67 MB of
downloads are local `file://` copies plus MoltenVK and headers from upstream, a few minutes), the xz pack (1-3 min).

## 10. Risks for this phase

1. **P9b changes behaviour** (0007, 0008 or OpenSSL 3 breaks an HLE path the test app touches). F2's full batch on
   the P9b build is the check (Phase 3); a difference is a STATUS line and a Guy question, never a reason to ship keys.
2. **ip-legal says counsel** for the core as a whole (rule 7: Azahar's AES and NCCH code stays in every build, inert
   with 0008). Then the release ships the repo, the test app and the build files, no core binary and no source
   assets for it (G3's default); STATUS says why; README's route falls back to the build block (stock core or
   `build-core.sh`, `make testapp`) and I4 swaps the steps marker (phase-h.md 3.1).
3. **Docs drift from code** (Phase 3 is not merged when H starts). H0 checks every planned row; the examples run.
4. **A number without load or date.** docs_check refuses it (numbers check; the forbidden list holds 50x and 51x).
5. **The clone at I2 needs the network** (MoltenVK, headers, PyPI's setuptools and pytest). A network failure is a
   retry, not a red; the log records the bytes fetched.
6. **The bsdtar copy differs from Azahar's tree beyond the drop list** (mode bits, a symlink, pax headers).
   `release_check` compares the two member lists name by name (type, mode, size, sha256, link target): only the drop
   list and the note member may differ; two runs give the same sha256. The 7 relative symlinks stay symlinks.
7. **The audit finds something in history** beyond the known needle. `release_check` scans the history for rules.md 1
   paths and, with the needle file, the content; a hit means another G8 pass (safe while nothing is public).
8. **A downloaded dylib is quarantined** when fetched with a browser. README troubleshooting: `xattr -d
   com.apple.quarantine <file>`; curl sets none.
9. **The macOS floor** (R31): the core's header says 11.0 but its libcrypto needs 15.0. **Chosen: the release says "macOS 15 or later"** (README, STATUS, release notes, SOURCE.md), `release_check` check 17 reads every shipped Mach-O's minos and the keg's libcrypto object target, and Phase 3 is asked to set `MACOSX_DEPLOYMENT_TARGET=15.0` at its next core rebuild so the header tells the truth (the v0.1.0 core keeps 11.0 in its header: recorded in STATUS, not fixed by Phase 4, which never rebuilds). Cost: about 0.03 h of docs and one check. Declined for v0.1.0: building OpenSSL 3.6.5 from the release tarball with `MACOSX_DEPLOYMENT_TARGET=11.0` (a `build-openssl.sh` step pinned by sha256, `LAZ_OPENSSL_ROOT` pointed at it, a core rebuild and F2 again, and `make` built with `-mmacosx-version-min=11.0`): about 0.35 h of agent time plus about 10 minutes of machine time, for macOS 11-14 users nobody can test here. It would also make OpenSSL's build scripts ours instead of Homebrew's formula, a small gain for the source story; it is a Phase 5 candidate.
10. **The system archives' provenance** (font, Mii, country list, bad-word list; no licence file). The audit decides;
    unclear means a BLOCKER for the core asset only.
11. **The tag gets a machine-local address** (no git identity configured). Section 8.2 sets the repo's identity first;
    `release_check --pre-push` checks it and every tag's tagger.
12. **ip-legal says even fetching the stock core is outside policy** (question 7). Then fetch.sh's stock part goes
    (a Phase 5 change to tests that compare cores); the README already does not use it (P16).
13. **Homebrew upgrades `openssl@3` between P9b and the release**, so the keg no longer matches the linked libraries.
    The release offers the version recorded in `build.inputs` (3.6.5), not the keg; `release_check` compares the
    binary's `OpenSSL 3.6.5` string, `build.inputs` and the tarball name. Ask: `brew pin openssl@3` from P9b to the
    release (Phase 3 section 12).
14. **The statically linked libcrypto carries Homebrew's paths** (R30: `OPENSSLDIR` `/opt/homebrew/etc/openssl@3`,
    `ENGINESDIR` and `MODULESDIR` under `/opt/homebrew/Cellar/openssl@3/3.6.5/lib`), so the guest's HTTPS uses Homebrew's
    CA file when `openssl@3` is installed and has none on a Mac without Homebrew. That does not matter for testing
    homebrew; STATUS "Known limits" gets one line. Not private (no `/Users/`): `release_check` check 8 lists these
    three as expected `NOTE` lines, and the audit brief (phase-i.md 9.2) names them as expected, not as leaks.
15. **The history rewrite loses work**: filter-repo resets the main worktree. Preconditions (phase-i.md 8.1): no agent
    writing in MAIN, tracked tree committed, a bundle backup outside the repo, the HEAD tree hash unchanged after.
16. **Old SHAs in docs and other repos go stale after G8** (and `build.inputs`' `head=`). `docs/commit-map-g8.tsv`
    maps them; old SHAs in text are not edited. Doing G8 early keeps the map to about 25 commits.

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
| G8 right after the P9b build, before Phase 3's worktrees, instead of at the end | the commit map shrinks from about 110 to about 25 rows; no worktree branch is rewritten (today only `main` holds the affected commits) | proposed to the main loop now |
| The ip-legal consult now, with 0008, ClCertA, OpenSSL and the stock-core question in one brief | an audit-fix-re-audit loop (about 0.25 h) and a possible second rebuild if 0008 were refused late | proposed to the main loop now |
| README route on our released core (P16): the clone needs no devkitARM; the build block is checked by I2's `make testapp` | the devkitARM env trap (B3) leaves the main route | taken |
| ScanCode, `reuse lint`, `licensee` for the notices | | declined: heavy installs, triage; the stdlib generator reads the real link line |
| GitHub Actions for the release | | declined: CI out of scope (PLAN 5) |
| Pre-seeding the clone's `dl/` from MAIN | a minute | declined: the gate is "only the README's steps" (the `file://` base is the one named deviation) |
| A `[test]` extra in `pyproject.toml` for pytest | a line in USING | declined for v0.1.0: I owns only the version line; the clone installs pytest explicitly (B4); a follow-up |
| Screenshots in the README | 0.05 h | declined for v0.1.0 (text only) |

## 12. Open questions

For Guy: G5, G6, G7, G9 (section 7); G8's timing (after the P9b build, before Phase 3's worktrees: recommended);
the macOS floor is decided as "macOS 15 or later" (risk 9) unless Guy wants macOS 11-14 users served in v0.1.0.

For review 2:
- Q5. Is P16 (README route on our released core) right, or should the README keep the stock route until ip-legal
  answers question 7? The plan's default is P16 either way (our core is the audited one).
- Q6. G8 right after the P9b build (before Phase 3's worktrees) versus after both Phase 4 merges: any reason to wait?
- Q7. `core/OPENSSL.md` records the Homebrew configure line read from `brew cat openssl@3`; if that needs the
  network at I0, the main loop fetches the formula once. Enough for "scripts used to control compilation", or should
  the release also attach the formula file?

Answered from review 1 (H): Q1 (a), by bsdtar `@archive` plus the note member; Q2 no `libazhost.dylib` asset; Q3
keep the fast pytest in the clone, pytest installed explicitly; Q4 commit the release notes.

For Phase 3 (the main loop routes these into its revision 2 or its step 0; Phase 4 assumes 1-4):
1. `brew pin openssl@3` now (the P9b build linked 3.6.5), held until the release is published (risk 13).
2. `tests/gate_f2.py` imports cleanly from `tools/` (no work at import; `drop` taken as a list of strings), so
   `release_check` can call `keyblob_findings()`.
3. MAIN's `build-core/build/` (its `.o.d` files, `link.txt`, `CMakeCache.txt`, `configure.log`) and
   `build-core/build.inputs` stay as F2 gated them until the release: no clean or rebuild between F2 and I2.
4. G8 between the end of the P9b build and the creation of Phase 3's worktrees, if the main loop takes the
   recommended timing (about 0.1 h; nothing in Phase 3 waits on it otherwise).
5. Optional: `build-core.sh` could accept an empty `LAZ_CORE_DROP` (today `"$DROP"` is in the required-values loop,
   :40-42). Phase 4 does not need it: `core/PIN-nokeys` names the note member `LIBAZAHAR-PY-REMOVED.txt` as its drop
   entry (it is in the stripped tree, so the "must exist" rule holds, and deleting it changes nothing the build reads).
6. Optional: `build.inputs` could carry the full cmake flags and the compiler line (today `cmake=` is the binary
   only); Phase 4 quotes `build-core.sh` at the `script=` hash and `configure.log`'s compiler identification instead.
7. Optional: `externals/libressl` in the drop list (a directory), so the build fails closed if `USE_SYSTEM_OPENSSL`
   ever flips; the drop step would need to take directories. Not needed: `build-core.sh` already dies if `LibreSSL`
   is in the core's strings.
8. At its next core rebuild (not before v0.1.0 unless it rebuilds anyway): `tools/build-core.sh:15`
   `MACOSX_DEPLOYMENT_TARGET=15.0`, so the core's header matches the libcrypto it links (R31, risk 9). If Phase 3
   rebuilds before I2 with it, Phase 4 drops STATUS's "header says 11.0" line and check 17 expects 15.0 everywhere.

## 13. Changes from review 1

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
Homebrew directories are in the core's strings as expected values (R30, risk 14, check 8, the audit brief); R2's size
is the P9b build's.

## 14. Changes from review 2

None yet.
