#!/bin/sh
# clone_check.sh: follow the README from a fresh clone, in a clean environment (step H; the main loop runs it at I2, I5).
#
#   sh tools/clone_check.sh --repo <path or URL> --branch <name> --out <dir> [--release-base <url>] [--dry-run]
#
# Steps: 1 clone; 2 the README's steps block (ends with the quickstart); 3 the build block, then the quickstart on the
# freshly built test app; 4 the full test suite on the default core. Nothing from another checkout is used: no linked
# dl/, no copied vendor/, no prebuilt build/. --release-base sets LAZ_RELEASE_BASE (the one named deviation, for a
# release that is not published yet). --dry-run prints each command instead of running it. Every step's output goes to
# <out>/clone.log and the exit code to <out>/rc. No timing from this run belongs in a document.
set -eu

REPO=""; BRANCH=""; OUT=""; BASE=""; DRY=0
usage() { echo "usage: sh tools/clone_check.sh --repo <path|url> --branch <name> --out <dir> [--release-base <url>] [--dry-run]" >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) [ $# -ge 2 ] || usage; REPO=$2; shift 2 ;;
    --branch) [ $# -ge 2 ] || usage; BRANCH=$2; shift 2 ;;
    --out) [ $# -ge 2 ] || usage; OUT=$2; shift 2 ;;
    --release-base) [ $# -ge 2 ] || usage; BASE=$2; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) usage ;;
  esac
done
[ -n "$REPO" ] && [ -n "$BRANCH" ] && [ -n "$OUT" ] || usage
case "$OUT" in /|.|..|"") echo "clone_check: refusing --out '$OUT'" >&2; exit 2 ;; esac

case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac      # absolute: the steps run in other folders

# a Python 3.10+ as Requirements says: the 3.14 framework build, else the newest 3.1x one
PYBIN=/Library/Frameworks/Python.framework/Versions/3.14/bin
if [ ! -d "$PYBIN" ]; then
  PYBIN=$(ls -d /Library/Frameworks/Python.framework/Versions/3.1*/bin 2>/dev/null | tail -n 1 || true)
  [ -n "$PYBIN" ] || { echo "clone_check: no Python 3.1x under /Library/Frameworks" >&2; exit 2; }
  echo "clone_check: using $PYBIN"
fi
CENV="env -i HOME=\"\$HOME\" PATH=$PYBIN:/usr/bin:/bin:/usr/sbin:/sbin LANG=en_US.UTF-8"
[ -z "$BASE" ] || CENV="$CENV LAZ_RELEASE_BASE=$BASE"
CLONE="$OUT/repo"; LOG="$OUT/clone.log"

START=$(date +%s)
if [ "$DRY" -eq 0 ]; then
  rm -rf "$OUT"; mkdir -p "$OUT"
  trap 'rc=$?; echo "$rc" > "$OUT/rc"' EXIT
fi

# run_step NAME EXPECT COMMAND: run COMMAND with sh -c, output appended to the log; EXPECT, when not empty, must
# appear in that step's output. A failure names the step and exits.
run_step() {
  _name=$1; _expect=$2; _cmd=$3
  if [ "$DRY" -eq 1 ]; then printf 'step %s: %s\n' "$_name" "$_cmd"; return 0; fi
  echo "== step $_name: $_cmd" >> "$LOG"
  _before=$(wc -l < "$LOG")
  sh -c "$_cmd" >> "$LOG" 2>&1 || { echo "clone_check: step $_name failed (see $LOG)" >&2; exit 1; }
  if [ -n "$_expect" ] && ! tail -n +"$((_before + 1))" "$LOG" | grep -q "$_expect"; then
    echo "clone_check: step $_name did not print '$_expect' (see $LOG)" >&2; exit 1
  fi
}

# step 4 rule: a failed suite is re-run once on the failed tests only; a pass then is logged as a time-bound rerun
PYTEST="LAZ_REQUIRE_EMULATOR=1 nice -n 10 .venv/bin/python -m pytest -q tests/python"
run_step clone "" "git clone --branch \"$BRANCH\" \"$REPO\" \"$CLONE\""
run_step steps "quickstart ok" "cd \"$CLONE\" && $CENV python3 -I tools/docs_check.py --emit-steps README.md > \"$OUT/steps.sh\" && $CENV sh -eux \"$OUT/steps.sh\""
run_step build "" "cd \"$CLONE\" && $CENV python3 -I tools/docs_check.py --emit-steps README.md --block build > \"$OUT/build.sh\" && $CENV sh -eux \"$OUT/build.sh\""
run_step quickstart-built "quickstart ok" "cd \"$CLONE\" && $CENV .venv/bin/python examples/quickstart.py build/testapp.3dsx"
run_step pytest-install "" "cd \"$CLONE\" && $CENV .venv/bin/pip install pytest"
run_step pytest "" "cd \"$CLONE\" && ($CENV $PYTEST || (uptime; $CENV $PYTEST --lf && echo \"time-bound rerun passed (load \$(uptime | sed 's/.*load averages*: //'))\"))"

if [ "$DRY" -eq 1 ]; then echo "dry run: nothing was cloned or downloaded"; exit 0; fi
echo "clone ok: $(( $(date +%s) - START )) s wall; $(du -sh "$CLONE/dl" | cut -f1) in dl/" | tee -a "$LOG"
