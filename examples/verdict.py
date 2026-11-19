"""Run a test app until it reports, then exit by the exit-code table of docs/USING.md section 3.

The guest side is a line in an SD file. The test app writes no PASS or FAIL, so this example waits for the line it
does write when its boot work is done (`booted f=`). A real app would write `PASS`, or `FAIL <why>`, to a file of its
own: change RESULT_FILE and PASS_TEXT to match. Run from the repo root: python examples/verdict.py [app]
"""
import os
import shutil
import signal
import sys
import threading
from pathlib import Path
from typing import NoReturn

from libazahar import (ArgumentError, BootError, Emulator, GuestError, HostCrashed, HostError, HostTimeout,
                       LibAzaharError, SlotTimeout, StateError)

RESULT_FILE = "testapp/log.txt"      # the SD file the guest writes
PASS_TEXT = "booted f="              # the line that means the test passed
FAIL_TEXT = "FAIL"                   # a line starting with this means it failed; the rest of the line is the reason
MAX_FRAMES = 600

EXIT_FAILED, EXIT_USAGE, EXIT_BOOT = 1, 2, 3
EXIT_GUEST_EXITED, EXIT_GUEST_ERROR, EXIT_TIMEOUT, EXIT_CRASHED = 10, 11, 12, 13

# Test hooks, read from the environment so a live test can drive each failure code (tests/python/test_verdict_live.py).
# A normal run sets none of them.
PASS_TEXT = os.environ.get("LAZ_VERDICT_PASS_TEXT", PASS_TEXT)
MAX_FRAMES = int(os.environ.get("LAZ_VERDICT_FRAMES", MAX_FRAMES))
RUN_TIMEOUT = float(os.environ["LAZ_VERDICT_TIMEOUT"]) if "LAZ_VERDICT_TIMEOUT" in os.environ else None
KILL_AFTER = float(os.environ["LAZ_VERDICT_KILL_AFTER"]) if "LAZ_VERDICT_KILL_AFTER" in os.environ else None
STOP_AFTER = float(os.environ["LAZ_VERDICT_STOP_AFTER"]) if "LAZ_VERDICT_STOP_AFTER" in os.environ else None


def finish(code: int, why: str) -> NoReturn:
    """Exit with the table's code: a pass prints its detail and `verdict ok`; anything else one line on stderr."""
    if code:
        print(f"verdict failed: {why}", file=sys.stderr)
        sys.exit(code)
    print(why)
    print("verdict ok")
    sys.exit(0)


def kill_later(pid: int, seconds: float) -> None:
    """Hard-kill the worker after ``seconds`` (the crash hook)."""
    threading.Timer(seconds, lambda: os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))).start()


def stop_later(pid: int, seconds: float) -> None:
    """Freeze the worker after ``seconds``, so its heartbeat stops and ``timeout`` fires (the timeout hook; it borrows
    the test helpers' suspend, which is SIGSTOP on POSIX and NtSuspendProcess on Windows)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests" / "python"))
    from proc_helpers import suspend
    threading.Timer(seconds, lambda: suspend(pid)).start()


def main() -> None:
    app = sys.argv[1] if len(sys.argv) > 1 else "build/testapp.3dsx"
    work = Path("runs/verdict")
    shutil.rmtree(work, ignore_errors=True)
    (work / "seed" / "testapp").mkdir(parents=True)
    (work / "seed" / "testapp" / "control.txt").write_text("boot_frames=60\n")     # logs `booted` after 60
    try:
        with Emulator(app, work / "run", sd_seed=work / "seed") as emu:
            if KILL_AFTER is not None:
                kill_later(emu.pid, KILL_AFTER)
            if STOP_AFTER is not None:
                stop_later(emu.pid, STOP_AFTER)
            result = emu.run_until(RESULT_FILE, PASS_TEXT, MAX_FRAMES, timeout=RUN_TIMEOUT)
            log = emu.sd / RESULT_FILE
            lines = log.read_text(errors="replace").splitlines() if log.exists() else []
    except SlotTimeout as exc:
        finish(EXIT_CRASHED, f"no instance slot was free, nothing was started ({exc})")
    except HostTimeout as exc:
        finish(EXIT_TIMEOUT, f"timed out, worker killed ({exc})")
    except HostCrashed as exc:
        finish(EXIT_CRASHED, f"worker or host crashed ({exc})")
    except ArgumentError as exc:
        finish(EXIT_USAGE, str(exc))
    except BootError as exc:
        finish(EXIT_BOOT, f"the app failed to boot ({exc})")
    except GuestError as exc:
        finish(EXIT_GUEST_ERROR, f"the guest stopped with an error ({exc})")
    except (HostError, StateError) as exc:
        finish(EXIT_CRASHED, f"the host could not run ({exc})")
    except LibAzaharError as exc:
        finish(EXIT_CRASHED, str(exc))
    failures = [line for line in lines if line.startswith(FAIL_TEXT)]
    if failures:
        finish(EXIT_FAILED, failures[0])
    if result.stopped_by == "guest_exited":
        finish(EXIT_GUEST_EXITED, f"the guest exited after {result.frames} frames")
    if result.stopped_by != "sd_text":
        finish(EXIT_FAILED, f"no {PASS_TEXT!r} line in {RESULT_FILE} after {result.frames} frames "
                            f"(stopped by {result.stopped_by})")
    finish(0, f"{PASS_TEXT!r} seen at frame {result.last_frame}")


main()
