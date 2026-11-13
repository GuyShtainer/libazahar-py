"""Read the test app's 32-byte record from guest memory (our core only). Run: python examples/memory_watch.py"""
import re
import shutil
import sys
from pathlib import Path

from libazahar import Emulator, NeedsLazpyCore

APP, WORK, MAGIC = "build/testapp.3dsx", Path("runs/memory_watch"), 0x4C415A52


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    with Emulator(APP, WORK) as emu:
        emu.run(30)                                           # let the app write its start line
        start = (emu.sd / "testapp/log.txt").read_text()
        addr = int(re.search(r"^start addr_global=0x([0-9a-f]+)", start, re.M).group(1), 16)
        rows = emu.run(60, watch=[(addr, 8)]).watch           # eight u32 words after each of 60 frames
        frame_word = emu.memory.u32(addr + 4)                 # the record's frame counter, read between batches
    frames = [row.frame for row in rows]
    if len(rows) != 60 or frames != list(range(frames[0], frames[0] + 60)):
        sys.exit(f"memory_watch failed: {len(rows)} rows, frames {frames[:3]}...")
    if any(row.status != 0 or row.u32(0, 0) != MAGIC for row in rows) or frame_word < rows[-1].u32(0, 1):
        sys.exit("memory_watch failed: a row has a bad status or magic, or the frame counter went back")
    print("memory_watch ok")


try:
    main()
except NeedsLazpyCore:
    print("needs our core: see README, Two cores")
    sys.exit(3)
