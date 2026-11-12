# libazahar-py: read these first, in this order

**The progress files are always current. This rule comes before any other work** (Guy 2026-11-11: "Its very very
very VERY important"). The item files under docs/status/ are the plan being followed. Before work starts, its item
sits in 1-in-progress/ (copy docs/status/templates/item.md if it has none). When a step lands, the same commit
moves the item and writes its Evidence. Every "Running now" row names its item id. `tools/status_check.py` fails
otherwise.

1. docs/status/lazpy/1-in-progress/HANDOFF.md   what runs now and the next steps (the one HANDOFF.md there).
2. docs/status/README.md     where every phase, step and ask is. The folder an item file sits in is its status.
3. docs/map/README.md        which file answers which need. Open a map before you search or list folders.
- Never read docs/progress.html to orient and never edit it. It is generated for Guy by tools/mkprogress.py.
- A status change is one step: git mv the item file to its new state folder, add its Evidence line, run
  python3 -I tools/mkprogress.py && python3 -I tools/status_check.py --strict-handoff && python3 -I tools/map_check.py,
  republish docs/progress.html. Run status_check.py --strict-handoff before every commit.
- Open an item file only when you work on that item; its last section holds its lessons and notes.
- When a file or folder moves, or a tool is added: python3 -I tools/mkmap.py, then tools/map_check.py.
- Never append to the handoff. Rewrite it whole from docs/status/templates/handoff.md (80 lines at most):
  current tasks and pointers only. The rules that bite every turn are in docs/map/rules.md.
- Hours: every agent run and main-loop block gets a row in docs/hours.tsv (times from `date` or the transcript),
  booked to a phase an item's `hours:` key claims.

# libazahar-py: what it is

A headless host for the Azahar 3DS emulator's libretro core (macOS arm64 first), plus a Python layer, so scripts can
run 3DS homebrew with no window, many copies at once, press buttons and touch, take screenshots and read guest memory.
Named after libmgba-py (the prebuilt mGBA Python bindings gba-toolkit uses). Born 2026-11-12 from a Gen3D spike
(Gen3D item g3d-32); Gen3D's emulator test harness is its first user, 3DS-MCP is its sibling tool. Public GPLv3 repo,
always publish-ready. It lives in its own repo at `3ds-toolkit/projects/libazahar-py/` (the toolkit ignores projects/).

Hard rules: `docs/map/rules.md`. Commands: `docs/map/runners.md`. Research so far: `docs/research/`.
Plans and reviews: opus only; plan, two review loops, then execute (global rule).
