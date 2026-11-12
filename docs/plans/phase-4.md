# Phase 4, release: the phase plan (item laz-400)

Opus phase plan, 2026-11-12, **revision 0** (before review 1). Steps: H (laz-410, `docs/plans/phase-h.md`) and I
(laz-420, `docs/plans/phase-i.md`). Each brief is complete on its own for one sonnet builder in its own worktree.
This file is the index: goal, order, checkpoints, file ownership, merge plan, the proposed departures from PLAN.md,
the interfaces taken from Phases 1-3, what Guy must do, the checked facts, the risks, the hours and the hour-saving
pass.

Contract: `docs/PLAN.md` (final) section 2.7 (the release paragraph), section 3's Phase H (PLAN.md:324) and Phase I
(:330) paragraphs, section 5 (out of scope: CI, PyPI, Windows/Linux). (The step item files still point at :317 and
:323; the main loop fixes those pointers when it moves the items.) Where a brief disagrees with PLAN.md on a goal,
PLAN.md wins and the builder stops and reports, **except for the approved departures** (Phase 2's P1-P6, Phase 3's
P7-P8 once approved, and, once the reviews and Guy approve them, this plan's P9-P13 in section 5).

Inputs: Phase 1 merged (570eebf; core built 19:40, `build-core/build.exit` 0); Phase 2 final, C merged-in-progress
and D at D1+D2 (b24c436); Phase 3 at revision 0 under review 1. **Most of what Phase 4 documents and ships is not
built yet**, so section 6 marks every row holds or planned, and both briefs start with a step 0 that checks each
planned row against the merged code. If the merged code differs from a row, the builder follows the code and reports
the row; if a row's feature is missing or its gate failed, the docs say "not done" for it (never a claim).

Hours are agent wall time (PLAN.md's unit). Machine time (the fresh clone's downloads, a core rebuild, the example
run) and Guy's time are not counted.

## 0. The finding that reshapes this phase (read first)

**Our built core contains Azahar's built-in console key blob.** Azahar's CMake has `option(ENABLE_BUILTIN_KEYBLOB
"Enable the inclusion of the default crypto keys blob" ON)` (SRC `CMakeLists.txt:154`); `src/core/hw/default_keys.h`
(46,817 bytes) holds `default_keys_enc[]`, which `src/core/hw/aes/key.cpp:302-312` decrypts with AES-CBC under an
all-zero 16-byte key and IV (`std::vector<u8> kiv(16)`) when no `aes_keys.txt` exists. `tools/build-core.sh:95-97`
does not set the option, so it is ON in `build-core/build/CMakeCache.txt` and `-DENABLE_BUILTIN_KEYBLOB` is in
`citra_core.dir/flags.make`; the blob's first 16 bytes (`[removed]`) are at
offset 13,960,800 of `build-core/azahar_lazpy_libretro.dylib` (checked 2026-11-12 20:00). The unchanged unified
tarball PLAN 2.7 says we re-host contains the same header.

Guy's IP policy, hard rule 7: "No TPM/circumvention surface, ever, in any toolkit: no key handling ... 3DS-era work
that goes near a TPM needs counsel first." A release asset that carries the 3DS AES keys (lightly wrapped) is the
textbook §1201 trafficking exposure, worse than anything the policy lists as RED, and the repo's own `rules.md` 1
already forbids `aes_keys.txt`. So, as planned in this file:

1. Our core is built with `-DENABLE_BUILTIN_KEYBLOB=OFF` (P9). Homebrew `.3dsx` files are not encrypted and need no
   keys, so the test app and Gen3D should run the same; the F2 gate on the rebuilt core proves it. **This should be
   done before step F2 runs** (one line in `build-core.sh`, one rebuild of about 15 min quiet, 40-90 min loaded), so
   F2 gates the binary we ship. That is a Phase 3 change the main loop must route now (open question G1, R1). If it
   is not done by Phase 4, the main loop does it before step I is launched and re-runs F2's gate on the new build
   (phase-i.md section 5, "Before you are launched"); step I's I0 stops if the blob is still in the binary.
2. The source asset cannot be the unchanged tarball (it holds `default_keys.h`). P10 proposes Azahar's tarball with
   that one file removed, re-packed deterministically, with a SOURCE.md that names the original (URL, sha256), the
   removed path and its sha256, and the proof the build never read it. Guy and the `ip-legal` agent choose among
   P10's three options before step I packages anything (G2).

Two more licence facts from the same check shape step I (section 8 has the evidence): the core statically links
LibreSSL (`libcrypto.a`, `libssl.a`; used by `core/hle/service/ssl/ssl_c.cpp` and `am/am.cpp`), whose OpenSSL and
SSLeay licences carry an advertising clause the FSF lists as GPL-incompatible (G3, for `ip-legal`); and the core
links SPIRV-Tools (Apache-2.0), which is compatible with GPLv3 but not GPLv2, so the binary as a whole is
distributable only under GPLv3 (Azahar's "or later" permits it) (G4).

## 1. Goal and the two steps

Goal: a public GitHub repo `GuyShtainer/libazahar-py` and a first release that a stranger can use from the README
alone, that says nothing it has not measured, and that meets every licence obligation of the binary it ships, with
the legal audit saying shippable. Push and publish only on Guy's word.

| Step | Delivers | Gate (headless, this Mac) | Hours |
|---|---|---|---|
| H, laz-410 | `README.md` rewritten (what it is, honest status, measured numbers with load and date, install, the 10-line example, the cores, links); `STATUS.md` (works / does not / considered and dropped); `docs/USING.md` finished (D's and G's sections kept, E's pool, F2's profile, a cores table); `docs/HOST-API.md`; `examples/quickstart.py` (= the README block), `examples/pool_shots.py`, `examples/memory_watch.py`; `tools/docs_check.py` | `python3 -I tools/docs_check.py` passes (every README number has a source line in `docs/research/` that contains it; the README example block is byte-equal to `examples/quickstart.py`; every relative link resolves; no forbidden claim word without a source); then a fresh `git clone` of the committed `step-h` branch into an empty folder, following only the README's numbered steps as a script, ends with the quickstart printing `quickstart ok` on the test app, nothing borrowed from MAIN | 0.75 |
| I, laz-420 | `NOTICES.md` (generated from the link inputs); `tools/mknotices.py`, `tools/release_pack.py`, `tools/mkrelease.sh`, `tools/release_check.py`, `core/PIN-nokeys`; `docs/release-notes/v0.1.0.md`; `tools/fetch.sh --lazpy-core` (sha256-pinned download of our core from the release URL); `core/README.md`'s licence and source lines; the staged assets in `runs/release/v0.1.0/` (ignored); the `release-legal-audit` and `ip-legal` reports in `docs/reviews/`; then, on Guy's word, the push and a draft release | `tools/release_check.py runs/release/v0.1.0` passes (key blob absent; exports exactly 25 `retro_*` + 3 `lazpy_*`; version `2126.2-lazpy.1`; `otool -L` system libraries only; no MoltenVK; no `/Users/` path, email, IP or MAC string; every static library on the core's link line has its licence text in `NOTICES.md`; the source asset matches SOURCE.md's hashes and its removed-file list; SHA256SUMS matches); `fetch.sh --lazpy-core` with a `file://` URL to the staged zip verifies and unpacks; the audit says **shippable** for the repo, its history, the core asset, the source asset, the test app and the notices; `git ls-files` shows no forbidden file (rules.md 1); **Guy says push** | 0.8 + 0.3 main loop and legal agents + Guy |

Phase total: **1.85 h** of step work (H 0.75, I 0.8, the main loop's and legal agents' 0.3) plus about 0.4 h for the
two review loops = **about 2.25 h**, against PLAN.md's
0.5 + 0.6 = **1.1 h** (plus the review loops PLAN's grouping paragraph counts separately). The over-run is named per
step in section 9; most of it is the key blob (P9, P10) and generating the notices from the binary's real inputs.

## 2. Order, checkpoints and the parallel split

```
Before launch: Phase 3 merged (E, F2, G) and its phase-end suite passed; our core built with P9 (key blob OFF)
and F2's gate passed on THAT build; I-pre: the ip-legal consult answered (phase-i.md 9.1; it needs no build, so it
can run as soon as this plan is final); Guy has answered G2 (the source-asset option) and G4
  |
  H builder (sonnet, ../libazahar-py-h, step-h)        I builder (sonnet, ../libazahar-py-i, step-i)
  |  H0: check section 6's rows against main            |  I0: check rows; key blob absent in the core
  |  H1: README, STATUS, USING, HOST-API, examples,     |      (else STOP: "P9 not applied")
  |      docs_check.py; quickstart run once in the      |  I1: mknotices.py -> NOTICES.md, mkrelease.sh,
  |      worktree (one emulator, nice'd, slot cap)      |      release_check.py, the source asset, fetch.sh
  |  ENDS ITS RUN: "H1 done"                            |      --lazpy-core, release notes; stage + check
  |  main loop commits H1 on step-h                     |  ENDS ITS RUN: "I1 done"
  |  main loop resumes H: "H1 committed at <sha>"       |  main loop commits I1 on step-i
  |  H2: fresh clone of step-h, README steps only       |
  |  ENDS ITS RUN: "H done"                             |
  v                                                     v
  opus as-built review of H; fixes; commit;           opus as-built review of I1; fixes; commit;
  merge step-h into main                              merge step-i into main (after H: README links NOTICES.md)
  |_____________________________________________________|
                         |
  main loop: re-stage on main (tools/mkrelease.sh), release_check.py      (I2, main loop, 0.05 h)
  release-legal-audit agent over main + history + runs/release/v0.1.0     (I3, its own run)
  BLOCKERs -> I builder resumed for fixes (I4) -> re-audit of the changed items only
                         |
  WAITING ON GUY: answers G1-G7; "push"; creates or lets us create the GitHub repo
                         |
  main loop, on Guy's word: push; gh release create --draft --prerelease; Guy looks at the draft and publishes it
  post-release check (I5): fresh clone, fetch.sh --lazpy-core against the real URL, the memory example on our core
```

- **A builder never waits for the main loop.** A sub-agent reports only by ending its run, so each checkpoint is the
  end of a run: H after H1 and after H2, I after I1 and after I4. The main loop commits, then resumes the same agent
  with SendMessage. Agent ids go into the handoff at launch. If a resume fails, a fresh sonnet gets the brief, the
  earlier report and `git log step-<x>`.
- **Why H's fresh-clone gate needs a commit first:** the gate is "a fresh clone", so it must clone what was
  committed. Cloning the worktree's uncommitted files would hide a file the main loop forgot to `git add`. H1's
  report lists every path to add; the clone in H2 catches a missing one.
- **H and I run side by side.** Neither runs a timed emulator test; H runs one nice'd instance for its example (H1
  once, H2 once), I runs none (I0's checks read the dylib; I4 only if a fix needs one). Both go through the slot cap.
  Nothing in Phase 4 is timed, so no speed number comes from Phase 4 (rules.md 7).
- **How a builder waits on its own long command** (Phase 2 S9): long runs write an rc file from a `trap ... EXIT`,
  start with `run_in_background`, and the builder waits with Monitor on "the rc file exists" (an until-loop,
  bounded); it stops every waiter it started (TaskStop) before it hands back. Without Monitor: foreground parts under
  the 10-minute Bash limit, and it says so.
- **The audit runs on main after both merges**, never on a branch: the history it audits is the history Guy pushes.
  The staged assets are rebuilt from main by `tools/mkrelease.sh` first (I2), so the audited files are the uploaded
  files (their sha256 values go in the audit report and the release notes).
- **Nothing reaches GitHub before Guy's word.** The repo has no remote today (`git remote -v` is empty). Every
  network write (repo creation, push, tag, release) is a "Waiting on Guy" item (section 7).

## 3. File ownership (who creates or edits what)

| File | Owner | What changes |
|---|---|---|
| `README.md` | H | rewritten whole (phase-h.md section 3.1) |
| `STATUS.md` (new, repo root) | H | phase-h.md 3.2 |
| `docs/USING.md` | H | finished: E's pool section, F2's profile lines, the cores table, a troubleshooting list; D's and G's sections kept, edited only where a fact changed (phase-h.md 3.3) |
| `docs/HOST-API.md` (new) | H | phase-h.md 3.4 |
| `examples/quickstart.py`, `examples/pool_shots.py`, `examples/memory_watch.py`, `examples/README.md` (new) | H | phase-h.md 3.5 |
| `tools/docs_check.py` (new) | H | phase-h.md 3.6 |
| `NOTICES.md` (new, repo root), `tools/mknotices.py` (new) | I | phase-i.md 3.1 (P11) |
| `tools/release_pack.py`, `tools/mkrelease.sh`, `core/PIN-nokeys`, `tools/release_check.py` (new) | I | phase-i.md 3.2, 3.3 |
| `tools/fetch.sh` | I | the `--lazpy-core` flag and its pin block only (phase-i.md 3.4) |
| `tools/build-core.sh` | the main loop, before I is launched, **only if** P9 was not applied in Phase 3 | the two cmake flags of P9, then `nice -n 10 tools/build-core.sh --detach` in MAIN and F2's gate re-run |
| `core/README.md` | I | the "Licenses" section: key blob off, the source asset, GPLv3 for the binary (P9, P10, G4) |
| `docs/release-notes/v0.1.0.md` (new) | I | phase-i.md 3.5 |
| `pyproject.toml` | I | `version = "0.1.0"` (from `0.1.0.dev0`), nothing else |
| `docs/reviews/release-ip-legal.md`, `docs/reviews/release-legal-audit-v0.1.0.md` | the two legal agents (via the main loop) | their reports, verbatim |

A file listed for one step is never edited by the other. H's README **links** `NOTICES.md` and the release; it does
not write them. I's release notes **link** the README; they do not restate its numbers. **No builder edits a file
outside its rows.** Nobody in Phase 4 touches: `host/`, `python/` (code), `testapp/`, `tests/`, `core/patches/`,
`core/PIN`, `.gitignore`, `docs/map/*`, `docs/PLAN.md`, `docs/plans/*`, `docs/research/*` (read only: the sources of
every number), `docs/hours.tsv`, the handoff, **every item file**, `prototype/`, `LICENSE`, and MAIN (read and copy
only; MAIN's `build-core/` is read only; only the main loop rebuilds it, for P9). A code bug found
while writing docs is reported, not fixed: the docs describe the code as it is, and the main loop decides. Lines the
main loop must add (`.gitignore`, `docs/map/runners.md`, `docs/map/tools.md`, `docs/map/code.md` for `examples/`)
and the "Lessons and notes" blocks go in each report.

## 4. Merge plan (the main loop does every commit; agents never commit)

1. Before launch: section 2's conditions. `git worktree list` and the case-insensitive name check (`ls .. | grep -i
   libazahar-py-`), then `git worktree add -b step-h ../libazahar-py-h main` and `git worktree add -b step-i
   ../libazahar-py-i main`. Dispatch both sonnets without isolation, cwd in the worktree. Agent ids into the handoff.
2. At "H1 done": commit exactly H1's listed paths on `step-h` (`git add <paths>`, `git diff --cached --stat`), then
   resume H with "H1 committed at <sha>; go on with H2".
3. At "I1 done": commit I1's paths on `step-i`. Opus as-built review of the step-i diff (phase-i.md section 12);
   fixes by the resumed I builder; commit.
4. At "H done": opus as-built review of the step-h diff (phase-h.md section 12); fixes (a fix that changes the
   README's steps re-runs H2); commit; merge `step-h` into main; item 410 moves with its Evidence line (one commit with
   the moved item). Then merge `step-i` into main (no shared file; a conflict stops and goes to the main loop).
5. I2 (main loop, in MAIN): `tools/mkrelease.sh v0.1.0` then `python3 -I tools/release_check.py
   runs/release/v0.1.0`; both pass or the I builder is resumed.
6. I3: dispatch `release-legal-audit` (the brief is phase-i.md section 9, written out so the main loop pastes it).
   Its report goes verbatim to `docs/reviews/release-legal-audit-v0.1.0.md`. BLOCKERs: resume I (I4), re-stage,
   re-check, re-audit only the changed items. Commit the report on main.
7. Waiting on Guy (section 7). On "push": phase-i.md section 8's exact commands, in order, the main loop running them
   (or handing them to Guy if he prefers). The draft release is created, Guy publishes it, then I5's post-release
   check. Item 420 and the phase item 400 move to done with their Evidence (the release URL and the audit verdict).
8. Remove each worktree only after `git status --porcelain` is empty in it.

## 5. Departures from PLAN.md (proposed; review and Guy approve or reject)

| # | PLAN.md says | Phase 4 does | Why |
|---|---|---|---|
| P9 | PLAN 2.7's build: Azahar's CI cmake flags plus `-j`, `FETCHCONTENT_FULLY_DISCONNECTED`, the policy minimum | adds `-DENABLE_BUILTIN_KEYBLOB=OFF` and `-DCMAKE_C_FLAGS=-ffile-prefix-map=<tree>/=azahar/ -DCMAKE_CXX_FLAGS=<same>` (one rebuild, ideally before F2, section 0) | the option is ON by default and puts the 3DS key blob into our binary (section 0; policy rule 7). The prefix map drops 461 absolute `/Users/guyshtainer/...` build paths from the binary's assert strings (privacy hygiene; same rebuild, no extra machine time) |
| P10 | PLAN 2.7 / PLAN Phase I: "Azahar's unified tarball **re-hosted unchanged**" | option (a), recommended: `azahar-unified-source-2126.2-lazpy-nokeys.tar.xz` = the tarball minus `src/core/hw/default_keys.h`, re-packed deterministically (sorted members, fixed mtime and owner), plus `SOURCE.md` naming the original URL and sha256, the removed file and its sha256, and the proof the build never read it (no `default_keys.h` in any dependency file of the build, phase-i.md 3.2). Option (b): no tarball asset; SOURCE.md points at Azahar's own release asset (GPLv3 §6(d), source on a third party's server) plus our patches; cheaper, but we then depend on Azahar keeping that asset up for as long as we distribute. Option (c): the unchanged tarball (PLAN as written): re-hosts the key blob, **not recommended** | the unchanged tarball contains `default_keys.h`; re-hosting it is distributing the keys. With P9 the file is not part of the binary's corresponding source, so (a) is complete source without it. Guy chooses (G2) after `ip-legal` answers |
| P11 | PLAN Phase H delivers `NOTICES.md` | step I writes `NOTICES.md`, generated by `tools/mknotices.py` from the core's real link inputs; H links it | the notices are the binary release's licence obligation; they come from the link line I checks anyway, and a hand-written list would miss what the link line shows (LibreSSL was not in PLAN's mental list) |
| P12 | PLAN Phase I: "Then `fetch.sh` gets a sha256-pinned download of our core" (after the release) | the pin is committed **before** the push: the sha256 of the exact zip we upload is known when it is staged; I tests the flag with a `file://` URL to the staged zip; after Guy publishes, I5 checks the real URL once | one push instead of two; the release's own commit already fetches its own asset |
| P13 | PLAN Phase I's gate: "Guy says push" | plus: the release is created as a **draft prerelease** by `gh release create --draft --prerelease`; Guy looks at it on GitHub and presses publish (or tells us to) | a draft is visible only to the repo's owner, so Guy sees the exact assets and text before anyone else; prerelease because STATUS.md lists what is not done |

Not departures (interpretations, listed so the review sees them): H's fresh-clone gate uses the stock core (fetched
by `fetch.sh`) and builds the test app with devkitARM, because the release (with `testapp.3dsx` and our core) does not
exist yet; the README gives both routes. The memory example needs our core, so it is gated in I5 after the release
(and on this Mac in H1 with MAIN's core).

## 6. Interfaces taken from Phases 1-3

"State": **holds** (checked in code or files on main or in MAIN today, 2026-11-12 20:05), **planned** (from a plan,
not built yet; step 0 checks it), **proposed** (needs a decision first).

| # | What Phase 4 relies on | Source | State | Used by |
|---|---|---|---|---|
| R1 | Our core built with the key blob OFF (P9) and gated by F2 on that build | section 0 | proposed (today's build has the blob) | I (the release binary), H (STATUS) |
| R2 | `build-core/azahar_lazpy_libretro.dylib`, 19,195,472 bytes today; `strip -x`, ad-hoc `codesign`; install name `@rpath/azahar_libretro.dylib`; `otool -L`: Cocoa, AVFoundation, IOSurface, CoreFoundation, libc++, libSystem only | `tools/build-core.sh:104-110`; `otool -L` 2026-11-12 | holds (re-checked on the P9 build) | I |
| R3 | Exports: 25 `_retro_*` + `_lazpy_read_memory`, `_lazpy_write_memory`, `_lazpy_movie_play`; version `2126.2-lazpy.1` | phase-f2 gate; patches 0001, 0005, 0006 | planned (F2) | I (`release_check.py`) |
| R4 | The core's link line: `build-core/build/src/citra_libretro/CMakeFiles/citra_libretro.dir/link.txt` lists cryptopp, mcl, dynarmic, enet, faad2, fmt, SPIRV, glslang, boost_iostreams, boost_serialization, LibreSSL crypto + ssl, zstd_seekable, lodepng, sirit, SoundTouch, SPIRV-Tools, SPIRV-Tools-opt, teakra, xxhash, zstd, and Azahar's own libs | the file, 2026-11-12 | holds (re-read after P9's rebuild) | I (`mknotices.py`) |
| R5 | `core/PIN`: tag 2126.2, commit 219d743a..., `SRC_URL`, `SRC_SHA256=85c8b56f...a4cd26`, `SRC_SIZE=43224348`, `SRC_TOP=azahar-unified-source-2126.2`, `LAZPY_REV=1` | core/PIN | holds | I |
| R6 | `dl/azahar-src/src.tar.xz` verified; `tools/untar_checked.py` path-checks members; `LAZ_CORE_PIN` env overrides the pin file | tools/build-core.sh:7, 60-80 | holds | I (the source asset is read with `python3 -I`, nothing in it run) |
| R7 | `tools/fetch.sh`: `get URL SHA FILE` (download only if missing or wrong, a mismatch deletes and exits), `verify`, `--force`, `LAZPY_ROOT`; pins block at the top; macOS stock curl, shasum, unzip, tar | tools/fetch.sh:1-60 | holds | I (adds `--lazpy-core`), H (README step) |
| R8 | `make` builds `build/libazhost.dylib` and `build/azhost` in seconds; `make testapp` builds `build/testapp.3dsx` with devkitARM first in PATH; `make check`, `make test-host` | Makefile:9, 24, 38, 45; docs/map/runners.md | holds | H |
| R9 | `.gitignore` ignores `dl/ vendor/ *.dylib *.zip *.tar* *.3dsx runs/ build/ build-*/` and the game/system list | .gitignore | holds | H (the clone has none of them), I (assets staged under `runs/`) |
| R10 | Every commit's author and committer is `Guy Shtainer <293649481+GuyShtainer@users.noreply.github.com>` (72 commits, 79f6b01) | `git log --format` | holds (re-checked before the push) | I |
| R11 | `pyproject.toml`: name `libazahar-py`, version `0.1.0.dev0`, `requires-python >=3.10`, `license = "GPL-3.0-or-later"`, setuptools>=77, package-dir `python`; `pip install -e .` in a venv | ../libazahar-py-d/pyproject.toml (D1, b24c436) | planned (D merged) | H (install steps), I (version) |
| R12 | The editable-install rule: the package finds `build/`, `dl/`, `host/` from its own folder; `LAZ_ROOT`, `LAZ_HOST`, `LAZ_CORE`, `LAZ_MVK`, `LAZ_PROFILE` (D8), `LAZ_LAZPY_PROFILE` (F2), `LAZ_MAX_INSTANCES`, `LAZ_SLOT_DIR`, `LAZ_SLOT_TIMEOUT` (E), `LAZ_PNG_LEVEL` (E), `LAZ_REQUIRE_EMULATOR`, `LAZ_STATE_ANY_APP` | phase-d 4.1, 9; phase-e; phase-f2 | planned | H |
| R13 | `Emulator(app, workdir, *, sd_seed, state, core, options, timeout, boot_timeout)`, `run(...) -> RunResult`, `set_keys`, `screens()`, `shot()`, `save_state()`, `load_state()`, `stats()`, `sd`, `close()`, context manager; `Buttons` names = libctru | phase-d 4.6 (D6, D7) | planned | H (quickstart, USING, HOST-API) |
| R14 | Errors `LibAzaharError`, `BootError`, `GuestError`, `HostTimeout`, `HostCrashed`, `StateError`, `NeedsLazpyCore`, `HostError`, `ValueError` for bad args; `GuestMemoryError` (P7) | phase-d 4.5; phase-3 P7 | planned (P7 proposed: Q2 of Phase 3) | H |
| R15 | `Pool(n, app, root, **emulator_kwargs)` with `submit`, `map`, `close`; `LoadWarning`; the default cap 3 (or what E's rule set) | phase-3.md section 12; phase-e 3.3 | planned | H (`pool_shots.py`, USING) |
| R16 | `emu.memory` (`read`, `write`, `u8`..`u64`, `s8`..`s64`, `write_*`, `.raw_read`), `run(..., watch=, watch_every=)`, `RunResult.watch` of `WatchRow`; our core only | phase-g 4 | planned | H (`memory_watch.py`) |
| R17 | `core/options-lazpy.txt` applied automatically on our core (P8); `azhost --lazpy-profile FILE\|none` | phase-f2 | planned (P8 proposed) | H (USING cores table) |
| R18 | `docs/research/speed-table-e.md`: per row the date, commit, core and version, load at start and end, guest fps, x real time, CPU and wall ms per frame, the guest-time check; test-app rows labelled light; the default cap and its rule | phase-e 7 | planned | H (README numbers) |
| R19 | `docs/research/spike-2-real-scene.md`: 334-345 fps, 5.6-5.7x at load 26.7 (16:07) on a real 3D field (Gen3D, a commercial game, local only); 129 fps 2.2x at load 68-96; 3 instances 136-138 fps each at 58-90; 0.5-0.8 GB per instance; "a clean re-measure on a quiet machine is still owed" | the file, lines 30-43 | holds | H (README numbers, labelled "real scene, one game, busy machine") |
| R20 | F2's report: repeat exactness on our core, the debug-stop frame, whether stock states load into ours; C's measured input offsets (m values); D's state-boot ratio | phase-f2 9; phase-c 8; phase-d gate | planned (in the items' Lessons and notes after each merge) | H (STATUS, USING) |
| R21 | `docs/USING.md` exists with D's 12 sections (phase-d 9) and G's "Guest memory" section (phase-g 4) | phase-d 9; phase-g 4 | planned | H |
| R22 | `host/azhost.h` is the C API's reference (every `azh_*` with its comment, the error enum, the limits); `build/azhost layout` prints `abi=<n>` and every `fields[]` row; ABI 3 after G | phase-a 3; phase-c 3.1; phase-g 3.1 | holds for ABI 1-2 headers on main; planned for ABI 3 | H (HOST-API) |
| R23 | `build/testapp.3dsx` is ours (GPLv3-or-later, `testapp/README.md`; glyphs and shader our own; libctru, citro2d, citro3d statically linked, zlib licence) | testapp/README.md; testapp/source/font.c:1 | holds | I (the asset, NOTICES' devkitPro lines) |
| R24 | The test app's markers and log: `tests/check_testapp.py markers --top --bottom --mode 2d`, the `start`/per-frame/`ready` log lines, `control.txt` keys | phase-b 3; phase-3 B2, B3, B9 | holds | H (quickstart's own check, done in-line, no import from `tests/`) |
| R25 | Spike 1's 50x is an idle menu and is never quoted as speed (rules.md 7) | docs/research/spike-1-headless-core.md:9, 55 | holds | H (docs_check's forbidden list) |
| R26 | No remote; no GitHub repo created by us yet; `gh` 2.95.0 installed with `release create --draft --prerelease --notes-file --target --verify-tag` | `git remote -v`; `gh release create --help` 2026-11-12 | holds | I (section 8 commands) |

## 7. Waiting on Guy

Only Guy can do or decide these. The main loop asks them together, once, before step I's I1 packages (G1-G4) and at
the end (G5-G7). Defaults hold until he answers, except where marked "blocks".

- **G1 (blocks F2's meaning, ask now).** Rebuild our core with the key blob off (P9) before Phase 3's F2 gates it?
  Default: yes. The main loop can do it today: one line in `tools/build-core.sh`, `nice -n 10 tools/build-core.sh
  --detach`, about 15-90 min machine time. If it waits until Phase 4, F2's gate runs twice.
- **G2 (blocks I1's packaging).** The source asset: P10 option (a) the tarball minus the key header (recommended), (b)
  a link to Azahar's own tarball under GPLv3 §6(d), or (c) the unchanged tarball (re-hosts the keys; against policy
  rule 7). `ip-legal` answers first (I-pre, phase-i.md 9.1); Guy decides.
- **G3 (blocks the release, not the push of the repo).** LibreSSL inside the GPL core: Azahar ships the same
  combination in every release. Accept on `ip-legal`'s advice (with its licence text and acknowledgments in
  NOTICES.md), or hold the core asset and release the repo only (users build the core with `build-core.sh`)?
  Default: follow `ip-legal`; if it says "counsel", release without the core asset.
- **G4.** The core binary is distributed under GPLv3 (Azahar's "or later", needed because SPIRV-Tools is
  Apache-2.0). Default: yes, stated in NOTICES.md and core/README.md.
- **G5 (account step).** Create the public repo `GuyShtainer/libazahar-py`: Guy creates it on GitHub, or tells the
  main loop to run `gh repo create GuyShtainer/libazahar-py --public --source . --remote origin` (no push). `gh auth
  status` must show **GuyShtainer** (not the older Guy-Shtainer); a cached old token is cleared as his
  git-publishing preferences say.
- **G6. "Push."** The push of main and the tag, and the creation of the draft release: only on his word (rules.md 4).
- **G7. Publish.** Guy opens the draft on GitHub, checks the assets and the text, and publishes it (or says "publish"
  and the main loop runs `gh release edit v0.1.0 --draft=false`). Also: the version (default `v0.1.0`, prerelease)
  and the two hygiene choices the audit will raise: the tracked `claude.ai/artifact/...` links (in
  `docs/status/README.md`, the handoff, `5-done/ask-01-progress-page.md`) and the `/Users/guyshtainer/...` paths in
  ten plan and review files. Default: keep both (the artifact is private to his account; the username is his GitHub
  handle), unless the audit grades them above "info".

## 8. Facts checked for this plan (reviewers: verify these)

"SRC" = `dl/azahar-src/unpacked/azahar-unified-source-2126.2/` (GIT-COMMIT 219d743a..., GIT-TAG 2126.2), read
2026-11-12. "CORE" = `build-core/azahar_lazpy_libretro.dylib` (built 19:40, `build.exit` 0).

| Fact | Where |
|---|---|
| `option(ENABLE_BUILTIN_KEYBLOB ... ON)`; `add_compile_definitions(ENABLE_BUILTIN_KEYBLOB)` when on; `default_keys.h` added to `citra_core` only when on | SRC CMakeLists.txt:154; src/CMakeLists.txt:186-187; src/core/CMakeLists.txt:501-503 |
| `default_keys.h` (46,817 bytes) holds `default_keys_enc[]`; it `#error`s if the option is off; `key.cpp` includes it only under `#ifdef` and decrypts it [removed] when `aes_keys.txt` is missing | SRC src/core/hw/default_keys.h:7-11; src/core/hw/aes/key.cpp:21-23, 302-312 |
| Our build has the option on, and CORE holds the [removed] 13,960,800 | build-core/build/CMakeCache.txt (`ENABLE_BUILTIN_KEYBLOB:BOOL=ON`); citra_core.dir/flags.make; a byte search 2026-11-12 |
| `build-core.sh` sets no keyblob flag; it reruns `cmake` every build (so a new `-D` applies), and `LAZ_CORE_PIN` overrides the pin file | tools/build-core.sh:7, 95-104 |
| The core links LibreSSL `libcrypto.a` and `libssl.a`; 198 assert strings from `externals/libressl/` are in CORE; SSL is used by `core/hle/service/ssl/ssl_c.cpp` and `am/am.cpp` | link.txt (R4); `strings` on CORE; `grep '#include <openssl/'` SRC/src |
| LibreSSL's COPYING: new code ISC; OpenSSL code under the OpenSSL License (clause 3: advertising acknowledgment) and the original SSLeay licence | SRC externals/libressl/COPYING:1-40 |
| Linked licences: boost BSL-1.0; cryptopp Boost-style compilation licence; dynarmic 0BSD (ISC-style); mcl, oaknut, teakra, enet, fmt, vma MIT; faad2 GPLv2-or-later (COPYING:308-309); glslang BSD-3/BSD-2/MIT/Apache-2.0 parts (LICENSE.txt:27-99; its GPL-3+Bison section covers a generated parser it says was removed, :5-6, 303); lodepng zlib; sirit BSD-3; SoundTouch LGPL-2.1; SPIRV-Tools Apache-2.0 (no NOTICE file); spirv-headers MIT-style Khronos; xxHash BSD-2; zstd BSD-3; inih BSD-3 | each externals/<name>/LICENSE* (head), 2026-11-12 |
| No linked component's licence file is MPL-2.0 (grep for "Mozilla Public License" over the linked externals: no hit); none has an Apache NOTICE file (only `library-headers/fdk-aac/NOTICE`, not linked) | grep, find, 2026-11-12 |
| `open_source_archives/include/` holds generated system archives compiled into `citra_core`: `shared_font.app.romfs.h` 6.8 MB, `mii.app.romfs.h` 454 KB, `country_list.app.romfs.h` 1.35 MB, `bad_word_list.app.romfs.h` 9 KB, "generated by https://github.com/B3n30/citra_system_archives at git commit 0baa5f57..." (its licence and data provenance are not stated in the tarball: an audit item) | SRC externals/open_source_archives/Readme.md; src/core/CMakeLists.txt:510 |
| `ClCertA` (the HTTP client cert) is loaded from the user's NAND, not embedded | SRC src/core/hle/service/http/http_c.cpp:1850, 1999-2000 |
| `externals/cpp-jwt/` holds test RSA/EC private keys (`*.pem`, `jwtRS256.key`); cpp-jwt is not on the core's link line | find SRC -name '*.pem' -o -name '*.key'; link.txt |
| 461 strings in CORE contain `/Users/guyshtainer/...` build paths; none contain an email | `strings -a CORE \| grep -c` 2026-11-12 |
| Azahar's own stock macOS libretro zip contains only `azahar_libretro.dylib` (no licence file) | `unzip -l dl/azahar/stock-core.zip` |
| Azahar's `license.txt` is the GPLv2 text; the libretro sources say "Licensed under GPLv2 or any later version" | SRC license.txt; src/citra_libretro/citra_libretro.cpp:1-3 |
| The repo has no remote; 72 commits, all author and committer the no-reply identity | `git remote -v`; `git log --format='%an <%ae>\|%cn <%ce>'` at 79f6b01 |
| Tracked files hold three `claude.ai/artifact` links and ten files with `/Users/guyshtainer` paths; no `gmail` | `git grep` 2026-11-12 |
| Fresh-clone downloads: the stock core zip 7,351,896 bytes, MoltenVK tar 59,563,008 bytes, the headers | dl/ sizes |
| Apple's `/usr/bin/python3` is 3.9.6, below `requires-python >=3.10`: a stock Mac needs python.org's or Homebrew's Python (README Requirements; H2's clean PATH puts python.org's 3.14 first) | `/usr/bin/python3 --version`, `which -a python3` |
| No `user.email`/`user.name` in any git config for this repo (commits so far carried the identity per command), so a plain `git tag -a` would use a machine-local address: the push commands set the repo's identity first | `git config --show-origin --get-all user.email` (empty) |
| `gh` 2.95.0: `release create` has `--draft`, `--prerelease`, `--notes-file`, `--target`, `--verify-tag`, `--latest` | `gh release create --help` |
| GPLv2 §3(a) / GPLv3 §6(a): object code accompanied by the Corresponding Source (incl. "the scripts used to control compilation and installation"); GPLv3 §6(d): source on a different server allowed with clear directions, the distributor stays obliged to keep it available; Apache-2.0 §4(a)-(d): a copy of the licence, keep notices, NOTICE file contents if any; BSD/MIT/zlib/BSL: BSD-2/3 and MIT need the notice in binary distributions' docs, zlib and BSL-1.0 do not; OpenSSL clause 3: acknowledgment in advertising materials | the licence texts (GPL texts in SRC license.txt and our LICENSE) |

## 9. Hours, against PLAN.md (agent wall time)

| Step | Builder | Review | Commit | Total | PLAN.md | Why the difference |
|---|---|---|---|---|---|---|
| H | 0.5 (H0 0.05, H1 0.35, H2 0.1) | 0.15 | 0.1 | **0.75** | 0.5 | the docs checker (numbers, the example block, links) and the commit-then-clone checkpoint were not in PLAN's 0.5; NOTICES moved to I (-0.05) |
| I | 0.6 (I0 0.1, I1 0.4, I4 fixes 0.1) | 0.15 | 0.05 | **0.8** | 0.6 | the key blob (P9 check, P10 source asset, about 0.15 h) and generating NOTICES from the link line (0.1) |
| I-pre, I2, I3, I5 (main loop and the two legal agents) | 0.3 (ip-legal consult 0.1, re-stage 0.05, audit run 0.1, post-release check 0.05) | | | **0.3** | (in I's 0.6) | the consult and the audit are their own agent runs |
| Review loops | | | | 0.4 | | two loops of a two-step phase |
| **Phase** | | | | **2.25** | **1.1** + loops | |

If P9 is not done in Phase 3: +0.2 h (the main loop's flag edit and F2's gate re-run by a resumed or fresh F2
builder, 0.15, and a short review) plus the rebuild's machine time. Guy's time: answering G1-G7 (about 10 min), the repo and token step (5 min, if needed), the
draft check and publish (5-10 min).

## 10. Risks for this phase

1. **The key-blob rebuild changes behaviour** (an HLE service the test app or Gen3D touches wanted a key). Homebrew
   needs none; F2's full gate on the P9 build is the check; a difference is a STATUS line and a Guy question, never a
   reason to ship the blob.
2. **`ip-legal` says counsel for LibreSSL or the key-adjacent code** (Azahar's AES and NCCH code is in every build,
   blob or not; policy: "3DS TPM-adjacent work needs counsel first"). Then the release ships the repo, the test app,
   the patches and the build script only, no core binary (G3's default), and STATUS.md says why. The repo itself
   ships no keys and no decryption code of ours.
3. **Docs drift from code** (the code is not merged when H starts). H0 checks every planned row; docs_check runs the
   example; HOST-API cites `azhost.h` and `azhost layout` output, not memory.
4. **A number in the README without load or date.** docs_check refuses it; the only real-scene numbers are spike 2's
   (busy machine, one game) and E's light table; both labelled.
5. **The fresh clone needs the network** (GitHub release downloads, PyPI's setuptools for `pip install -e .`).
   A network failure is a retry, not a red; the gate log records the bytes fetched.
6. **The deterministic re-pack differs from Azahar's tree beyond the removed file** (mode bits, a symlink, mtimes).
   `release_check.py` compares the two trees member by member (names, modes, sizes, sha256, symlink targets): only the
   removed file may differ. The 7 relative symlinks under `externals/` (phase-f1) are kept as symlinks.
7. **The audit finds something in history** (a forbidden file committed then removed). `git log --all --diff-filter=A
   --name-only` over the forbidden patterns is in release_check; a hit means a history rewrite before the first push
   (Guy's policy, safe while nothing is public) and a re-audit.
8. **A downloaded dylib is quarantined** when a user fetches it with a browser (curl sets no quarantine attribute).
   README's troubleshooting line: `xattr -d com.apple.quarantine <file>`; `fetch.sh` is the documented route.
9. **The macOS deployment target** is 11.0 (`build-core.sh:15`), but the binary is tested only on this Mac (macOS
   15, arm64). README says "tested on macOS 15 arm64; built for 11.0+, untested there".
10. **The open-source system archives** (font, Mii, country list, bad-word list) compiled into the core have no
    licence file in the tarball. The audit checks their provenance (the generator repo's licence and sources); if
    unclear it is a BLOCKER for the core asset only (the repo ships none of them).
11. **The tag or a later commit gets a machine-local email** (no git identity is configured, section 8). Phase-i.md
    section 8 sets the repo's `user.name`/`user.email` first, and `release_check.py --pre-push` checks it and every
    tag's tagger before the push.

## 11. Hour-saving pass (revision 0)

| Existing thing or cut | What it saves | Verdict |
|---|---|---|
| `gh release create v0.1.0 --draft --prerelease --notes-file ... <assets>` (one command, assets uploaded with it) instead of a GitHub Actions release workflow or the web form | a workflow file plus a macOS runner core build (40+ min a run; CI is out of scope, PLAN 5); about 0.3 h | taken (I) |
| `NOTICES.md` generated by `tools/mknotices.py` from the link line and each external's own licence file, instead of written by hand | about 0.15 h, and no transcription error; re-run on every core update | taken (I, P11) |
| A stdlib `release_check.py` (about 200 lines, with `mknotices.py`'s component table) mapping the link line's `.a` inputs and the header-only externals the core includes to licence sections, instead of ScanCode Toolkit (a heavy pip install, slow over a 43 MB tree, output needs triage), `reuse lint` (checks our own SPDX headers, not a binary's components) or `licensee` (LICENSE-file detection only, Ruby) | about 0.3 h of install and triage; none of the three is installed here | taken (I); ScanCode noted as the follow-up if a reviewer wants a second opinion |
| The corresponding-source proof by the build's own dependency files (no `default_keys.h` in any `*.d`/`depend.make` under `build-core/build/`, plus the cmake cache line) instead of rebuilding from the stripped tarball | a 15-90 min rebuild and about 0.1 h | taken (I) |
| The README example block **is** `examples/quickstart.py` (byte-equal, checked), and H2 runs that file | a second copy to keep in step; the "README example runs" gate is the clone run itself | taken (H) |
| HOST-API.md cites `host/azhost.h` and pastes `build/azhost layout` output, instead of re-describing every struct field by hand | about 0.1 h and the drift risk | taken (H) |
| No history rewrite: every one of the 72 commits already has the no-reply identity (R10) | 0.1-0.2 h of `filter-repo` and its re-check | taken (re-checked by release_check before the push) |
| GitHub's automatic "Source code" archives at the tag carry our repo's source, which is the test app's corresponding source | a separate test-app source asset | taken (I; the release notes say so) |
| `fetch.sh --lazpy-core` pinned before the push, tested with `file://` (P12) | a second commit, push and audit pass after the release | taken (I) |
| One `ip-legal` consult with six exact questions (key blob, source option, LibreSSL, GPLv3 for the binary, the system archives, the name) before packaging, instead of discovering them in the audit | an audit-fix-re-audit loop (about 0.25 h) | taken (I-pre, phase-i.md 9.1) |
| P9 applied in Phase 3 before F2 (G1) | F2's gate run twice and a second rebuild: about 0.2 h agent, 15-90 min machine | proposed to the main loop now |
| Pre-seeding the fresh clone's `dl/` from MAIN to skip about 67 MB of downloads | a minute or two of machine time | declined: the gate is "only the README's steps" |
| Screenshots in the README | an art-free test-app shot would be fine (policy: own UI is green) | declined for v0.1.0: text only, 0.05 h saved; a follow-up |
| A real Gen3D speed row in the README | | declined: needs a commercial game, never published (rules.md 1); spike 2's numbers are quoted with their label |

## 12. Open questions

For Guy: G1-G7 (section 7).

For review:
- Q1. Is P10 (a)'s deterministic re-pack worth its code (about 60 lines of `python3 -I` in `release_pack.py source`:
  tarfile, the original members' order and mtimes, uid/gid 0) and the configure check over option (b)? (b) is nearly free but makes our compliance
  depend on Azahar's release page.
- Q2. Should the release also attach `libazhost.dylib` (PLAN says no: `make` takes seconds)? The plan keeps PLAN.
- Q3. Should H's fresh-clone gate also run `pytest -m "not slow"` from the clone (about a minute, proves the install
  without the core)? The plan includes it as H2's second check; review may cut it.
- Q4. Is `docs/release-notes/v0.1.0.md` worth committing, or should the notes live only in the release body? The plan
  commits them (the audit audits the text; a deleted release keeps its notes in git).

## 13. Changes from review 1

None yet (revision 0).

## 14. Changes from review 2

None yet.
