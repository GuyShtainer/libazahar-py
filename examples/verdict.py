"""Run a test app until it reports, then exit by the exit-code table of docs/USING.md section 3.

The guest side is a line in an SD file. The test app writes no PASS or FAIL, so this example waits for the line it
does write when its boot work is done (`booted f=`). A real app would write `PASS`, or `FAIL <why>`, to a file of its
own: change RESULT_FILE and PASS_TEXT to match. Run from the repo root: python examples/verdict.py [app]
"""
import shutil
import sys
from pathlib import Path

from libazahar import ArgumentError, BootError, Emulator, GuestError, HostCrashed, HostTimeout, LibAzaharError

RESULT_FILE = "testapp/log.txt"      # the SD file the guest writes
PASS_TEXT = "booted f="              # the line that means the test passed
FAIL_TEXT = "FAIL"                   # a line starting with this means it failed; the rest of the line is the reason
MAX_FRAMES = 600

EXIT_FAILED, EXIT_USAGE, EXIT_BOOT, EXIT_TIMEOUT, EXIT_CRASHED = 1, 2, 3, 12, 13


def finish(code: int, why: str) -> None:
    """Exit with the table's code: a pass prints its detail and `verdict ok`; anything else one line on stderr."""
    if code:
        print(f"verdict failed: {why}", file=sys.stderr)
        sys.exit(code)
    print(why)
    print("verdict ok")
    sys.exit(0)


def main() -> None:
    app = sys.argv[1] if len(sys.argv) > 1 else "build/testapp.3dsx"
    work = Path("runs/verdict")
    shutil.rmtree(work, ignore_errors=True)
    (work / "seed" / "testapp").mkdir(parents=True)
    (work / "seed" / "testapp" / "control.txt").write_text("boot_frames=60\n")      # the test app logs `booted` after 60
    try:
        with Emulator(app, work / "run", sd_seed=work / "seed") as emu:
            result = emu.run_until(RESULT_FILE, PASS_TEXT, MAX_FRAMES)
            lines = (emu.sd / RESULT_FILE).read_text(errors="replace").splitlines() if (emu.sd / RESULT_FILE).exists() else []
    except HostTimeout as exc:
        finish(EXIT_TIMEOUT, f"timed out, worker killed ({exc})")
    except HostCrashed as exc:
        finish(EXIT_CRASHED, f"worker or host crashed ({exc})")
    except ArgumentError as exc:
        finish(EXIT_USAGE, str(exc))
    except BootError as exc:
        finish(EXIT_BOOT, f"the app failed to boot ({exc})")
    except GuestError as exc:
        finish(EXIT_FAILED, f"the guest stopped with an error ({exc})")
    except LibAzaharError as exc:
        finish(EXIT_CRASHED, str(exc))
    failures = [line for line in lines if line.startswith(FAIL_TEXT)]
    if failures:
        finish(EXIT_FAILED, failures[0])
    if result.stopped_by != "sd_text":
        finish(EXIT_FAILED, f"no {PASS_TEXT!r} line in {RESULT_FILE} after {result.frames} frames (stopped by {result.stopped_by})")
    finish(0, f"{PASS_TEXT!r} seen at frame {result.last_frame}")


main()
