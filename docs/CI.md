# Running your app in CI

How a homebrew author runs their own `.3dsx` under libazahar-py in GitHub Actions, headless, on a hosted macOS runner.
The recipe is `examples/ci/macos.yml`; copy it to `.github/workflows/` in your repository and change the lines marked
`CHANGE`. Nothing here opens a window.

## What the recipe does

1. Checks out your repository and, in a sub-folder, libazahar-py at a release tag you choose.
2. Runs `sh tools/fetch.sh --moltenvk --host --lazpy-core`: the prebuilt host, our core and MoltenVK, each checked
   against a sha256 pinned inside `fetch.sh`. No compiler and no `make`. (`--host` needs a libazahar-py release that
   carries the host zips: v1.3.0 or later. On an earlier tag, build the host with `make`, as the README says.)
3. Makes a venv and installs the Python layer (`pip install -e .`; the package finds its host and core from the
   checkout).
4. Runs your copy of `examples/verdict.py` (see "Make your app report") on your app. It boots the app, runs until the app writes a pass line to a file on its SD
   card, and exits by the table in `docs/USING.md` section 3: 0 for a pass, 1 for a failed test, 12 for a timeout, and
   so on.

## Make your app report

The guest side is one line in an SD file. Have your app write `PASS` (or `FAIL <why>`) to a file under its SD root, then
copy `examples/verdict.py` into your repository (the recipe expects `ci/verdict.py`) and set `RESULT_FILE`, `PASS_TEXT` and `FAIL_TEXT` at the top to match.
Run it with the path to your built app as its one argument.

## Reading the result

A hosted macOS runner may have no usable Vulkan path, and its runs are sometimes never started. So the job in the recipe
has `continue-on-error: true` and is started by hand (`workflow_dispatch`): a red result then does not mark your commit
red. Read the verdict step's own outcome and its last lines in the run log: `verdict ok` is a pass; `verdict failed:
<why>` with an exit code is not. Once the job has passed several runs in a row for you, remove `continue-on-error` and
add a push or pull-request trigger.

If a run is not started within about half an hour, cancel it once and try later; do not loop retries.

## State-boot timing on hosted runners

Our own test suite bounds a state boot on the test app (`docs/USING.md` section 10). On a hosted runner
(`GITHUB_ACTIONS=true` and `CI` set) that bound only records the time and does not fail; off a hosted runner it is a
gate. If you time your own states in CI, do the same: record on shared runners, gate on a machine you control.

## Pinning

The recipe pins every action by full commit sha. Do the same for libazahar-py: use a release tag you have read, or a
full commit sha. The sha256 pins live in `tools/fetch.sh` in that checkout, so they move only when you move the tag.
