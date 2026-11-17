---
id: laz-701
title: lazpy
order: 701
kind: step
parent: laz-700
page: Windows proof: set up the steps and check the PC's tools
hours: -
---
# Windows proof: set up the steps and check the PC's tools

## What it is
Create items 701-714, rewrite the handoff, read-only PC pre-flight (disk, RAM, MSYS2 packages, venv, Developer Mode), add zip/unzip to the PC's MSYS2, make the four fix worktrees.

## Exit gate
status_check exits 0; runs/p7/w0/preflight.txt lists every tool with its version and the symlink answer. Plan: `docs/plans/phase-7.md` line 212.

## Evidence
- 2026-11-17 12:28: items 701-714 committed (f235f29), status_check OK. PC pre-flight in runs/p7/w0/preflight.txt
  (local, gitignored): C: 29.6 GB free, D: 2,426.9 GB, RAM 6.06 of 15.86 GB free; venv Python 3.10.11; MSYS2 gcc
  16.2.0, make 4.4.1, git 2.56.1, tar 1.35, xz 5.8.4; zip 3.0-5 and unzip 6.0-7 added by pacman (announced to
  Gen3D, 3DP, gba-toolkit-b2). Worktrees runs/p7/wt/{w2a,w2b1,w2b2,w6} at 1c8650f (branches p7-w2a, p7-w2b1,
  p7-w2b2, p7-docs).

## Pointers
- Plan section: `docs/plans/phase-7.md:212`; briefs: `docs/plans/phase-7-briefs.md`
- Review: `docs/reviews/phase-7-review-2.md`

## Lessons and notes
- Symlinks: Developer Mode is off, but an ssh session holds the admin token, so it CAN make symlinks. Tests that
  make symlinks run over ssh; the plan's symlink skip applies only to a non-admin interactive shell. W2a must not
  rely on the skip firing over ssh.
