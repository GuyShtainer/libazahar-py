---
id: laz-841
title: lazpy
order: 841
kind: step
parent: laz-840
page: Phase D: the host prebuilt (host-bin.yml zips, fetch.sh --host)
hours: -
---
# D1: the host, prebuilt

## What it is
Phase D: the host prebuilt (host-bin.yml zips, fetch.sh --host).

## Exit gate
The plan row's gate, run on the PC through runs/p8/bin/pclane and in its CI workflow; the lane merged on main; the D5 review's findings fixed.

## Evidence
2026-11-20 16:34: lane merged on main (the prebuilt-host workflow `host-bin.yml` and `fetch.sh --host`, pins TBD until the release). 16:57: D5 review fixes merged (the macOS host stripped of build paths before signing, a NOTICES.md in the Windows host zip, release_check row 1c ties the zip's commit to the tag); fetch_fallback 14 of 14 and release_check self-test 24 of 24 on the PC.
2026-11-20 20:24: host-bin run 44789150709 green: both zips hold the listed files and no build path, the macOS files signed ad hoc. The release pins come from the run on the v1.3.0 commit (laz-840). Done.

## Pointers
- Plan section: `docs/plans/phase-8.md:208`
- Briefs: `docs/plans/phase-8d-briefs.md`; review: runs/p8/d/d5-review.md (private)

## Lessons and notes
Read this part only when you work on this item.
