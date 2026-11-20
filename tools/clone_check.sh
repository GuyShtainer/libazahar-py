#!/bin/sh
# clone_check.sh: follow the README from a fresh clone, in a clean environment (step H; the main loop runs it at I2, I5).
#
#   sh tools/clone_check.sh --repo <path or URL> --branch <name> --out <dir> [--release-base <url>] [--until host]
#                           [--stock-core <path>] [--fixture <dir>] [--dry-run]
#
# macOS: 1 clone; 2 the README's steps block (ends with the quickstart); 3 the build block, then the quickstart on the
# freshly built test app; 4 the full test suite on the default core.
# Windows (the MSYS2 MINGW64 shell; run with the PC's Python from LAZ_WIN_PY, default C:\lazpy\venv\Scripts\python.exe,
# whose venv's pyvenv.cfg names the base interpreter that makes the clone's venv; that path is read at run time and
# never written down): 1 clone; 2 the README's Windows block (steps-win; its pacman and clone lines are dropped, the
# clone is ours); 3 `make test-host`; 4 the full suite with -rs and a junit file, then tools/skips_check.py --list w7.
# The devkitARM build block is skipped: the release test app (fetch.sh) is used, and the log says so.
#
# Nothing from another checkout is used: no linked dl/, no copied vendor/, no prebuilt build/. The named deviations:
#   --release-base URL  sets LAZ_RELEASE_BASE (a release that is not published yet)
#   --stock-core PATH   sets LAZ_STOCK_CORE in the clean environment (Azahar's own core, for the comparison tests)
#   --fixture DIR       copies DIR (a release's state fixture) to runs/release-fixtures/<name>/ in the clone
#   --deselect NODEID   passes pytest --deselect NODEID (repeatable; a test the machine may not run, such as a 3-copy
#                       pool test on a PC limited to 2 copies); the log names each one
#   --until host        stops after the host build and `make test-host`: fetch.sh gets no --lazpy-core and no
#                       --testapp (the Windows pin may not exist yet), and the venv, quickstart and pytest do not run
# --dry-run prints each command instead of running it. Every step's output goes to <out>/clone.log and the exit code to
# <out>/rc. No timing from this run belongs in a document.
set -eu

REPO=""; BRANCH=""; OUT=""; BASE=""; DRY=0; UNTIL=""; STOCK=""; FIXTURE=""; DESEL=""
usage() { echo "usage: sh tools/clone_check.sh --repo <path|url> --branch <name> --out <dir> [--release-base <url>] [--until host] [--stock-core <path>] [--fixture <dir>] [--deselect <nodeid>]... [--dry-run]" >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) [ $# -ge 2 ] || usage; REPO=$2; shift 2 ;;
    --branch) [ $# -ge 2 ] || usage; BRANCH=$2; shift 2 ;;
    --out) [ $# -ge 2 ] || usage; OUT=$2; shift 2 ;;
    --release-base) [ $# -ge 2 ] || usage; BASE=$2; shift 2 ;;
    --until) [ $# -ge 2 ] || usage; UNTIL=$2; shift 2 ;;
    --stock-core) [ $# -ge 2 ] || usage; STOCK=$2; shift 2 ;;
    --fixture) [ $# -ge 2 ] || usage; FIXTURE=$2; shift 2 ;;
    --deselect) [ $# -ge 2 ] || usage
      case "$2" in tests/python/*::*) ;; *) echo "clone_check: --deselect takes tests/python/<file>::<test>" >&2; exit 2 ;; esac
      case "$2" in *[!A-Za-z0-9_./:-]*) echo "clone_check: --deselect $2 holds an odd character" >&2; exit 2 ;; esac
      DESEL="$DESEL --deselect $2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) usage ;;
  esac
done
[ -n "$REPO" ] && [ -n "$BRANCH" ] && [ -n "$OUT" ] || usage
case "$UNTIL" in ""|host) ;; *) echo "clone_check: --until takes host" >&2; exit 2 ;; esac
case "$OUT" in /|.|..|"") echo "clone_check: refusing --out '$OUT'" >&2; exit 2 ;; esac

WIN=0
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) WIN=1 ;; esac

if [ "$WIN" -eq 1 ]; then OUT=$(cygpath -m "$OUT" 2>/dev/null || echo "$OUT"); fi
case "$OUT" in /*|?:*) ;; *) OUT="$PWD/$OUT" ;; esac      # absolute: the steps run in other folders
[ -z "$STOCK" ] || case "$STOCK" in /*|?:*) ;; *) STOCK="$PWD/$STOCK" ;; esac
[ -z "$FIXTURE" ] || case "$FIXTURE" in /*|?:*) ;; *) FIXTURE="$PWD/$FIXTURE" ;; esac
[ -z "$STOCK" ] || [ "$DRY" -eq 1 ] || [ -f "$STOCK" ] || { echo "clone_check: --stock-core $STOCK is not a file" >&2; exit 2; }
[ -z "$FIXTURE" ] || [ "$DRY" -eq 1 ] || [ -f "$FIXTURE/fixture.json" ] || { echo "clone_check: --fixture $FIXTURE has no fixture.json" >&2; exit 2; }

# q STRING: STRING as one single-quoted shell word (paths hold spaces on the PC)
q() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

if [ "$WIN" -eq 1 ]; then
  # a Python 3.10+: LAZ_WIN_PY (the PC's venv). Its pyvenv.cfg `home =` names the base interpreter folder.
  WINPY="${LAZ_WIN_PY:-C:\\lazpy\\venv\\Scripts\\python.exe}"
  "$WINPY" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null \
    || { echo "clone_check: LAZ_WIN_PY is missing or older than Python 3.10 (never the PC's default python, which is 3.7)" >&2; exit 2; }
  CFG="$(dirname "$(dirname "$(cygpath -u "$WINPY")")")/pyvenv.cfg"
  PYHOME=$(sed -n 's/^home *= *//p' "$CFG" 2>/dev/null | tr -d '\r' | head -n 1)
  [ -n "$PYHOME" ] || { echo "clone_check: no 'home =' line in $CFG" >&2; exit 2; }
  PYBIN=$(cygpath -u "$PYHOME")
  [ -d "$PYBIN" ] || { echo "clone_check: the base interpreter folder from pyvenv.cfg is missing" >&2; exit 2; }
  VENVPY=".venv/Scripts/python.exe"; VENVPIP=".venv/Scripts/pip"
else
  # a Python 3.10+ as Requirements says: the 3.14 framework build, else the newest 3.1x one
  PYBIN=/Library/Frameworks/Python.framework/Versions/3.14/bin
  if [ ! -d "$PYBIN" ]; then
    PYBIN=$(ls -d /Library/Frameworks/Python.framework/Versions/3.1*/bin 2>/dev/null | tail -n 1 || true)
    [ -n "$PYBIN" ] || { echo "clone_check: no Python 3.1x under /Library/Frameworks" >&2; exit 2; }
    echo "clone_check: using $PYBIN"
  fi
  VENVPY=".venv/bin/python"; VENVPIP=".venv/bin/pip"
fi
CLONE="$OUT/repo"; LOG="$OUT/clone.log"

# the clean environment: <out>/cenv.sh runs its arguments under `env -i` with only what the steps need
CENV="sh $(q "$OUT/cenv.sh")"
make_cenv() {
  {
    echo '#!/bin/sh'
    if [ "$WIN" -eq 1 ]; then
      printf 'exec env -i HOME=%s PATH=%s MSYSTEM=MINGW64 LANG=en_US.UTF-8' "$(q "$HOME")" "$(q "$PYBIN:/mingw64/bin:/usr/bin:/bin")"
      for name in SystemRoot SYSTEMROOT SystemDrive SYSTEMDRIVE windir WINDIR COMSPEC ComSpec PATHEXT LOCALAPPDATA APPDATA USERPROFILE TEMP TMP; do
        eval "val=\${$name:-}"
        [ -z "$val" ] || printf ' %s=%s' "$name" "$(q "$val")"
      done
    else
      printf 'exec env -i HOME=%s PATH=%s LANG=en_US.UTF-8' "$(q "$HOME")" "$(q "$PYBIN:/usr/bin:/bin:/usr/sbin:/sbin")"
    fi
    [ -z "$BASE" ] || printf ' LAZ_RELEASE_BASE=%s' "$(q "$BASE")"
    [ -z "$STOCK" ] || printf ' LAZ_STOCK_CORE=%s' "$(q "$STOCK")"
    echo ' "$@"'
  } > "$OUT/cenv.sh"
  # a portable load line: /proc/loadavg where there is one (MSYS2), else uptime's, else n/a
  {
    echo '#!/bin/sh'
    echo 'if [ -r /proc/loadavg ]; then cut -d" " -f1-3 /proc/loadavg'
    echo 'elif command -v uptime >/dev/null 2>&1; then uptime | sed "s/.*load averages*: //"'
    echo 'else echo "n/a"; fi'
  } > "$OUT/load.sh"
}

START=$(date +%s)
if [ "$DRY" -eq 0 ]; then
  rm -rf "$OUT"; mkdir -p "$OUT"
  trap 'rc=$?; echo "$rc" > "$OUT/rc"' EXIT
  make_cenv
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
note() { if [ "$DRY" -eq 1 ]; then echo "note: $*"; else echo "== note: $*" >> "$LOG"; fi; }

# step 4 rule: the suite fails unless it passes. On macOS only a failure of the named time-bound tests (TIMED, a grep
# pattern; today D'"'"'s state-boot bound) is re-run once, on the failed tests only; any other failure, or a second one,
# fails. On Windows there is no re-run: the junit file must describe the run that passed (skips_check reads it).
TIMED="::test_state_boot"
LOADSH="$OUT/load.sh"
export CENV PYTEST OUT TIMED LOADSH WIN
PYSTEP='eval "$CENV $PYTEST -rfs" > "$OUT/pytest1.log" 2>&1; rc=$?; cat "$OUT/pytest1.log"; [ "$rc" -eq 0 ] && exit 0
[ "$WIN" -eq 0 ] || { echo "pytest failed (no re-run on Windows)"; exit 1; }
n=$(grep -c "^FAILED" "$OUT/pytest1.log"); o=$(grep "^FAILED" "$OUT/pytest1.log" | grep -vc "$TIMED")
{ [ "$n" -gt 0 ] && [ "$o" -eq 0 ]; } || { echo "failure outside the time-bound tests"; exit 1; }
echo "time-bound failure; load: $(sh "$LOADSH")"; eval "$CENV $PYTEST --lf" && echo "time-bound rerun passed (load $(sh "$LOADSH"))"'

if [ "$WIN" -eq 1 ]; then
  PYTEST="LAZ_REQUIRE_EMULATOR=1 $VENVPY -m pytest -q --junitxml=\"$OUT/junit.xml\" tests/python$DESEL"
else
  PYTEST="LAZ_REQUIRE_EMULATOR=1 nice -n 10 $VENVPY -m pytest -q tests/python$DESEL"
fi
run_step clone "" "git clone --branch \"$BRANCH\" \"$REPO\" \"$CLONE\""
[ -z "$DESEL" ] || note "deselected (not run here):$DESEL"

if [ "$WIN" -eq 1 ]; then
  # the README's Windows block, as steps.sh. The pacman line and the clone line are the reader's own setup, not ours.
  # --until host: no --lazpy-core and no --testapp, and nothing from the venv line on (the Windows pin may not exist yet).
  EMIT='awk -v m="<!-- docs_check: steps-win -->" '"'"'f == 0 && index($0, m) { f = 1; next } f == 1 && /^```/ { if (inb) exit; inb = 1; next } f == 1 && inb { print }'"'"' README.md'
  FILTER="grep -v -e '^pacman ' -e '^cd .*git clone'"
  if [ -n "$UNTIL" ]; then
    FILTER="$FILTER | sed -e '/-m venv/,\$d' -e 's/ --lazpy-core//g' -e 's/ --testapp//g' -e 's|^sh tools/fetch.sh *\(#.*\)\{0,1\}\$|sh tools/fetch.sh --headers|'"
    note "--until host: fetch.sh runs as --headers, without the core and the test app (the Windows pin does not exist yet); venv, quickstart and pytest do not run"
  fi
  run_step steps "" "cd \"$CLONE\" && $EMIT | $FILTER > \"$OUT/steps.sh\" && [ -s \"$OUT/steps.sh\" ] && $CENV sh -eux \"$OUT/steps.sh\""
  note "windows mode: the devkitARM build block is skipped; the test app is the release's (fetch.sh), not a rebuild"
  run_step host-tests "0 failed" "cd \"$CLONE\" && $CENV make test-host"
else
  run_step steps "quickstart ok" "cd \"$CLONE\" && $CENV python3 -I tools/docs_check.py --emit-steps README.md > \"$OUT/steps.sh\" && $CENV sh -eux \"$OUT/steps.sh\""
  run_step build "" "cd \"$CLONE\" && $CENV python3 -I tools/docs_check.py --emit-steps README.md --block build > \"$OUT/build.sh\" && $CENV sh -eux \"$OUT/build.sh\""
  run_step quickstart-built "quickstart ok" "cd \"$CLONE\" && $CENV $VENVPY examples/quickstart.py build/testapp.3dsx"
fi

if [ "$UNTIL" != host ]; then
  if [ "$WIN" -eq 1 ]; then
    run_step quickstart "quickstart ok" "cd \"$CLONE\" && $CENV $VENVPY examples/quickstart.py"
    [ -z "$FIXTURE" ] || run_step fixture "" "mkdir -p \"$CLONE/runs/release-fixtures\" && cp -R \"$FIXTURE\" \"$CLONE/runs/release-fixtures/$(basename "$FIXTURE")\""
  fi
  run_step pytest-install "" "cd \"$CLONE\" && $CENV $VENVPIP install pytest numpy"
  run_step pytest "" "cd \"$CLONE\" && $PYSTEP"
  if [ "$WIN" -eq 1 ]; then
    # every skip must be on the w7 list (plan section 6); skips_check.py is part of the tree, never stubbed here
    run_step skips "" "cd \"$CLONE\" && [ -f tools/skips_check.py ] && $CENV $VENVPY -I tools/skips_check.py \"$OUT/junit.xml\" --list w7"
  fi
fi

if [ "$DRY" -eq 1 ]; then echo "dry run: nothing was cloned or downloaded"; exit 0; fi
echo "clone ok: $(( $(date +%s) - START )) s wall; $(du -sh "$CLONE/dl" 2>/dev/null | cut -f1) in dl/" | tee -a "$LOG"
