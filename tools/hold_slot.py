#!/usr/bin/env python3
"""Hold one libazahar slot of the machine-wide cap, then exec a command (docs/plans/phase-e.md 3.5).

    python3 -I tools/hold_slot.py [--timeout S] -- CMD [ARG...]

The lock lives on in the command's process and dies with it. Exit 2 with a usage line when no command follows
``--``. Step G's gate and the phase-end suite run azhost commands under it.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from libazahar import _slots  # noqa: E402

USAGE = "usage: hold_slot.py [--timeout S] -- CMD [ARG...]"


def parse(argv):
    """(timeout or None, command list), or None for a usage error."""
    args = list(argv)
    timeout = None
    if len(args) >= 2 and args[0] == "--timeout":
        try:
            timeout = float(args[1])
        except ValueError:
            return None
        args = args[2:]
    if not args or args[0] != "--" or len(args) < 2:
        return None
    return timeout, args[1:]


def main(argv):
    """Acquire a slot, make only its fd inheritable, exec the command (does not return on success)."""
    parsed = parse(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2
    timeout, command = parsed
    slot = _slots.acquire(timeout)
    print(f"hold_slot: slot={slot.index} waited_s={slot.waited_s:.3f}", file=sys.stderr, flush=True)
    os.set_inheritable(slot.fd, True)
    os.execvp(command[0], command)
    return 127


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
