#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Step B gate: the test app builds clean, draws exact markers, logs one line per frame, obeys control.txt.
# RUNNER=fe2 (default, prototype/fe2.c) or RUNNER=azhost (step A's build/azhost). SECS = seconds of a shot run.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
mkdir -p runs build
RUNNER="${RUNNER:-fe2}"
SECS="${SECS:-15}"
chk() { python3 -I tests/check_testapp.py "$@"; }
APP=build/testapp.3dsx
FAILS=0
TAG="$(date +%H%M%S)"

say() { printf '%s\n' "$*"; }
ok() { say "PASS $1"; }
bad() { say "FAIL $1"; FAILS=$((FAILS + 1)); }
# verdict NAME CMD...: PASS when the command succeeds; its output is kept on failure
verdict() { vname="$1"; shift; if out="$("$@" 2>&1)"; then ok "$vname: $out"; else bad "$vname: $out"; fi; }

# wait_pid PID SECONDS: bounded wait; kills only our own pid if it overruns
wait_pid() {
    i=0
    while kill -0 "$1" 2>/dev/null && [ "$i" -lt "$2" ]; do sleep 1; i=$((i + 1)); done
    if kill -0 "$1" 2>/dev/null; then kill "$1" 2>/dev/null || true; say "note: pid $1 overran and was killed"; fi
    RC=0
    wait "$1" 2>/dev/null || RC=$?
}

# run_app NAME SECONDS SHOTS CONTROL_TEXT: sets RUN and FRAMES
run_app() {
    RUN="runs/b-$TAG-$1"
    rm -rf "${RUN:?}"
    mkdir -p "$RUN/sys/Azahar/sdmc/testapp" "$RUN/out"
    [ -z "$4" ] || printf '%s\n' "$4" > "$RUN/sys/Azahar/sdmc/testapp/control.txt"
    if [ "$RUNNER" = azhost ]; then
        shotarg=""
        [ -z "$3" ] || shotarg="--shot 300,600"
        # shellcheck disable=SC2086  # shotarg is a flag pair or empty
        nice -n 10 build/azhost run "$APP" --sys "$RUN/sys" --out "$RUN/out" --frames 600 $shotarg > "$RUN/out.txt" 2>&1 &
    else
        MVK_LIB=dl/moltenvk/MoltenVK/MoltenVK/dynamic/dylib/macOS/libMoltenVK.dylib OPT_citra_graphics_api=Vulkan \
        OPT_citra_input_type=none OPT_citra_enable_motion=disabled \
        nice -n 10 build/fe2 "${LAZ_STOCK_CORE:?set LAZ_STOCK_CORE to Azahar's own core}" "$APP" "$RUN/sys" "$RUN/out" "$2" "$3" > "$RUN/out.txt" 2>&1 &
    fi
    wait_pid "$!" "$(($2 + 120))"
    FRAMES="$(sed -n 's/.*frames=\([0-9]*\).*/\1/p' "$RUN/out.txt" | tail -n 1)"
    FRAMES="${FRAMES:-0}"
    STOP="$(sed -n 's/.* stop=\([a-z_]*\) .*/\1/p' "$RUN/out.txt" | tail -n 1)"
    # on our core a guest exit ends azhost with _exit(10) and no summary (phase-c.md 3.5); the stock core runs on
    if [ "$RC" -eq 10 ] && [ "$1" = ev-exit ]; then RC=0; fi
    if [ "$RC" -ne 0 ] && [ "$RUNNER" = azhost ]; then say "note: azhost exit code $RC ($1)"; bad "azhost exit code $RC in run $1"; fi
    LOG="$RUN/sys/Azahar/sdmc/testapp/log.txt"
}

# shot_run NAME CONTROL: a shot run, rerun once with SECS=40 when slow (fe2 only)
shot_run() {
    run_app "$1" "$SECS" 299,599 "$2"
    if [ "$RUNNER" = fe2 ] && [ "$FRAMES" -lt 600 ]; then
        say "note: slow run (frames=$FRAMES), rerunning once with SECS=40"
        run_app "$1" 40 299,599 "$2"
        [ "$FRAMES" -ge 600 ] || { bad "slow: frames=$FRAMES"; return 1; }
    fi
}

# shots_markers NAME MODE [extra args]: check both shots of the last run
shots_markers() {
    name="$1"; mode="$2"; shift 2
    for s in 000299:000300 000599:000600; do
        if [ "$RUNNER" = azhost ]; then
            n="${s#*:}"
            verdict "$name $n" chk markers --top "$RUN/out/shot_${n}_top.png" --bottom "$RUN/out/shot_${n}_bottom.png" --mode "$mode" "$@"
        else
            n="${s%:*}"
            verdict "$name $n" chk markers "$RUN/out/shot_$n.png" --mode "$mode" "$@"
        fi
    done
}

say "gate-b RUNNER=$RUNNER SECS=$SECS"
# 1. zero warnings, host test
DKP="/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH"
PATH="$DKP" make -C testapp clean > /dev/null 2>&1 || true
if PATH="$DKP" make -C testapp > "runs/b-$TAG-make.txt" 2>&1 \
    && ! grep -qi warning "runs/b-$TAG-make.txt" && [ -f "$APP" ]; then ok "build: zero warnings, $APP"; else bad "build (see runs/b-$TAG-make.txt)"; fi
mkdir -p build
if cc -std=c11 -Wall -Wextra -Werror testapp/source/control.c testapp/source/record.c testapp/tests/host_test.c -o build/testapp-host-test \
    && [ "$(build/testapp-host-test)" = "host_test ok" ]; then ok "host_test ok"; else bad "host_test"; fi

# 2 and 3. 2D markers and the log
if shot_run 2d ""; then
    shots_markers "markers 2d" 2d
    verdict "log" chk log "$LOG" --runs "$FRAMES"
    shots_markers "planted red (must fail)" 2d --expect-shift 1 > "runs/b-$TAG-red.txt" || true
    if grep -c '^FAIL' "runs/b-$TAG-red.txt" | grep -q '^2$'; then ok "planted red: the shifted check failed on both shots"; else bad "planted red did not fail"; fi
    FAILS=$((FAILS - $(grep -c '^FAIL' "runs/b-$TAG-red.txt" || true)))
fi
# 4. 3D markers
if shot_run 3d "draw=3d"; then shots_markers "markers 3d" 3d; fi
# 5. events
for ev in "break_at=120:break:120" "exit_at=120:exit:120" "ready_at=60:ready:60"; do
    ctl="${ev%%:*}"; rest="${ev#*:}"
    run_app "ev-${rest%%:*}" 10 "" "$ctl"
    # azhost on our core stops at a guest break (stop=guest_break); the stock core and fe2 run on past it
    if [ "${rest%%:*}" = break ] && [ "$STOP" = guest_break ]; then stopped=--stopped; else stopped=""; fi
    # shellcheck disable=SC2086  # stopped is one flag or empty
    verdict "event $ctl" chk event "$LOG" "${rest%%:*}" "${rest##*:}" --runs "$FRAMES" $stopped
done
if shot_run boot "boot_frames=90"; then
    verdict "event boot_frames=90" chk event "$LOG" booted 90 --runs "$FRAMES"
    shots_markers "markers after boot" 2d
fi

# passed runs are removed (KEEP=1 keeps them); a failing gate keeps everything for inspection
if [ "$FAILS" -eq 0 ]; then
    [ "${KEEP:-0}" = 1 ] || rm -rf "runs/b-$TAG-"*
    say "gate-b: ALL PASS"
else say "gate-b: $FAILS FAIL"; exit 1; fi
