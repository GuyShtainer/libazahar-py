"""Boot the test app, hold A, take a shot, check what happened. Run from the repo root: python examples/quickstart.py"""
import shutil
import struct
import sys
from pathlib import Path

from libazahar import Buttons, Emulator

app = sys.argv[1] if len(sys.argv) > 1 else "build/testapp.3dsx"
work = Path("runs/quickstart")
shutil.rmtree(work, ignore_errors=True)
with Emulator(app, work) as emu:
    result = emu.run(300, inputs=[(150, Buttons.A)], shots=[300])      # A is held from batch frame 150 on
    log = (emu.sd / "testapp/log.txt").read_text().splitlines()
shot = result.shots[300]
sizes = [struct.unpack(">II", Path(p).read_bytes()[16:24]) for p in (shot.top, shot.bottom)]
keys = [int(w[2:], 16) for line in log if line.startswith("f=") for w in line.split() if w.startswith("k=")]
if result.frames != 300 or result.stopped_by != "frames":
    sys.exit(f"quickstart failed: ran {result.frames} frames, stopped by {result.stopped_by}")
if sizes != [(400, 240), (320, 240)]:
    sys.exit(f"quickstart failed: screen sizes {sizes}")
if not keys or keys[0] & 1 or not keys[-1] & 1:
    sys.exit("quickstart failed: A is not in the app's log after the press")
print("quickstart ok")
