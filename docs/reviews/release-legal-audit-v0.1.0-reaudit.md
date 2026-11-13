# release-legal-audit re-audit: libazahar-py v0.1.0, after G8c (2026-11-13, 05:03)

I'm not a lawyer. These are risk grades under the house policy, not legal advice.

**Scope.** I audited from 1132bc1. During the audit, at 04:56, `main` moved to ad66b68. That commit touches only `docs/hours.tsv`, `docs/progress.html`, the 420 item and HANDOFF, and I audited it too. I edited nothing tracked and committed nothing. Notes: `runs/i3/reaudit-notes.md`.

## Verdict: shippable

| Surface | Verdict |
|---|---|
| History | **shippable**: B1 is resolved |
| Repo at HEAD | **shippable**. One small SHOULD is left over from S1 (S1r below) |
| Core zip | **shippable** |
| Build-files asset | **shippable**, as long as the tag goes on 1132bc1. If the tag goes on any later commit, regenerate the asset at that commit (S4) |
| Azahar source asset, OpenSSL asset, snapshot, test app, NOTICES | **shippable**. Unchanged from the first audit (the SHA256SUMS sums verify) |
| Docs' claims | **shippable**, after S1r |
| R1 (`core/PIN`'s `SRC_URL` default route) | **still RISK-ACCEPT, waiting for Guy**. Unchanged |

## (1) B1: RESOLVED (no grade)

**Searches, all 0 hits:**
- The stock asset name prefix, the stock sha256 prefix, the forms `azahar-libretro-` and `azahar_libretro-`, and any `releases/download/...azahar[-_]libretro` form.
- Where I searched:
  - `git log --all -p` with every commit message;
  - a `git cat-file --batch` dump of all 1876 reachable objects (`git rev-list --all --objects`);
  - the reflog;
  - `runs/clone-i4/repo`'s history.

**Every `releases/download` form in history:**
- our own repo;
- OpenSSL;
- MoltenVK;
- Azahar's unified source tarball (expected);
- our nokeys asset.

The old fetch.sh's `CORE_SHA`/`CORE_URL` lines now hold placeholders, so the fetch no longer works. `CORE_VER` keeps the public version number only.

**Private rules.** I ran the cumulative private replace file (57 rules) and the I2 needle file (59) over the same four surfaces. Neither hit any rule line.
- **Positive control:** a throwaway clone of the private pre-G8c bundle hits 7 rule lines and both B1 strings, so the scanner does detect them. I deleted that clone afterwards.

**INFO:** `docs/plans/phase-f1.md:67` names Azahar's upstream CI job (a substring of the old asset name). It is a build reference, not the asset name, URL or hash.

**Refs:**
- Only `refs/heads/main` exists. There are no tags, no remote and no stash.
- `--all` equals `main`: 154 commits.
- One identity (the no-reply address) for author and committer on all of them.
- `git fsck --unreachable --no-reflogs` returns nothing.
- So a push of `main` carries nothing that B1 named.

**HEAD tree:** 32f3046's tree equals the pre-rewrite HEAD tree recorded in the private folder. G8c did not change the tree.

**INFO, local only, never pushed:**
- `.git/filter-repo/` (old-to-new commit maps).
- `ORIG_HEAD`, which points to 32f3046 (rewritten history).
- The private folder's `pre-rewrite`, `pre-g8b` and `pre-g8c` bundles. These **hold the removed material**. Keep them out of the repo and every upload. Delete them once the push has landed and the rollback is no longer needed.

## (2) S1-S3 and the spike-1 name

**S2, resolved.** `README.md:121-122`, `STATUS.md:32` and `docs/release-notes/v0.1.0.md:31-32` now say "console keys / Nintendo certificates / Nintendo system files". 1132bc1's change to release_check only widens the allowed prefix to "no console ".

**S3, resolved.** `docs/plans/phase-4.md:83-84` and `:368` keep only the CMake-default fact.

**Spike-1, resolved.** `docs/research/spike-1-headless-core.md:51` and `:55` are reworded. The game literals in the private rules hit 0 objects and 0 messages across all of history.

**S1, resolved in the table rows.** `README.md:24-26` is accurate against `docs/research/spike-2-real-scene.md:1-6` and `:28-36`.

**S1r (SHOULD, one line):** the prose under the table, `README.md:28-29`, still says that the real-scene rows are "one commercial game's scene run locally".
- That sentence brings back the reading S1 removed: a commercial title on the stock core.
- It also contradicts `STATUS.md:68` ("homebrew only").
- **Fix:** say "Gen3D's (homebrew) 3D scene" to match the rows. This is a HEAD edit and needs no history rewrite.

## (3) Re-staged release, `runs/release/v0.1.0/`

**Hashes:**
- `shasum -c SHA256SUMS`: all 8 OK.
- fetch.sh's `LAZPY_CORE_SHA` and `TESTAPP_SHA` equal the staged zip and test app in full. The test app also equals `build/testapp.3dsx`.

**The zip:**
- It has 6 members.
- The dylib equals `build-core`'s copy (21,828,992 bytes, unchanged).
- `build.inputs` equals `build-core`'s copy.
- NOTICES is the same in the zip, the asset and the repo.
- The zip's SOURCE.md equals the top-level SOURCE.md.

**SOURCE.md is accurate:**
- Its build commit translates through the g8, g8b and g8c maps to 8669f89, which is an ancestor of `main`.
- `tools/build-core.sh` and all 9 patch sha256 values match SOURCE.md, 8669f89 and HEAD.
- Its URLs are Azahar's source tarball and OpenSSL only.

**`release_check` without the private file, at ad66b68:**
- Checks 1-6, 8, 9, 11, 13 (878 blobs, 0 hits), 14 and 16 PASS.
- Checks 7 and 12 skip their needle parts.
- **Check 10 FAILs only because of HEAD drift.** The asset is byte-equal to `git archive` of **1132bc1** (its pax comment is 1132bc1), and the archived paths are unchanged from 1132bc1 to ad66b68.

**Build-files asset contents:** both needle files give 0 hits. Its URLs are Azahar's source tarball, our nokeys asset and OpenSSL.

**S4 (SHOULD, process):** put tag `v0.1.0` on 1132bc1, or re-run mkrelease at the tagged commit before uploading. SOURCE.md item 5 promises "this repository at the tag v0.1.0", and check 10 must pass at the tag. Regenerating changes only that asset's line in SHA256SUMS. The zip does not change, because SOURCE.md names that asset without a hash.

**INFO:** the NOTE text at `tools/release_check.py:135` still says "g8 then g8b". It should also name g8c, as SOURCE.md already does.

## (4) What the rewrite could have broken: nothing found

- `git fsck --full` is clean.
- `runs/clone-i4/repo` holds only `main` at 1132bc1, 153 commits, and its tree equals 1132bc1's.
- The README route ran: fetch.sh (all pins verified), then `make`, then the venv, then "quickstart ok". The full pytest gave 136 passed and 3 skipped, rc 0 (`runs/i2/clone4.log`, `runs/clone-i4/clone.log`).
- HEAD keeps the expected generic source URL at `core/PIN:3`, `docs/plans/phase-f1.md:61` and `tools/docs_check.py:29`.
- The old clone `runs/clone-i2` is gone.

## Carried over unchanged

From the first audit: Layers 4, 6 and 7 CLEAN, R1 RISK-ACCEPT (Guy), and the INFO items. The INFO items are:
- the progress artifact;
- the scratchpad path at `docs/research/libretro-py-probe.md:22`;
- `3DPlatinum`;
- the OpenSSL-3 sentence;
- the `aes_keys.txt` comment in 0008;
- `docs/research/spike-2-real-scene.md:58`.

## Remediation list (ordered)

1. **SHOULD S1r:** reword `README.md:28-29` to match rows 24-26 ("Gen3D's (homebrew) 3D scene"). This is a HEAD commit.
2. **SHOULD S4:** tag 1132bc1, or regenerate the build-files asset and SHA256SUMS at the tag commit. Re-run `release_check --pre-push` with the private file at the tag.
3. **RISK-ACCEPT R1:** unchanged. Guy's per-item sign-off is still needed (worst case: a partial-repo notice naming the build script, with a cure window of about one business day; the cure is to flip the default to `core/PIN-nokeys`).
4. **INFO:**
   - Update release_check's NOTE text to name g8c.
   - After the push lands, delete the private pre-rewrite bundles and `.git/filter-repo/`.
   - Push `main` and the tag only.
5. **If a notice arrives:** cure, don't counter-notice.

**Proposed KB entry (for the main loop):** 2026-11-13. After a history rewrite, prove the leak scanner works by running it on the pre-rewrite bundle and watching it hit, and only then trust a 0-hit result on the new history. Also, a wording fix to a table must include the prose beside it: README:28-29 kept the claim that rows 24-26 dropped.
