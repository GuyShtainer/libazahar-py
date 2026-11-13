"""Step K's gates 3 and 4 (docs/plans/phase-k.md section 6): the tick seed option and the guest thread registers,
both on core lazpy.2 (patches 0002 and 0009). Numbers worth reporting go to runs/k/live-numbers.txt (and stderr)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

import pytest

import d_helpers as dh
from libazahar import ArgumentError, Emulator, NeedsLazpyCore

pytestmark = pytest.mark.slow

REPO = Path(__file__).resolve().parents[2]
NUMBERS = REPO / "runs" / "k" / "live-numbers.txt"
ELF = REPO / "build" / "testapp.elf"
# the kernel shared page (src/core/hle/kernel/shared_page.h): date_time_counter at +0x0, date_time_1 at +0x40 with
# update_tick at +8 inside it; the first update (at boot, counter 0 -> date_time_1) stores the base ticks there
COUNTER = 0x1FF81000
UPDATE_TICK = 0x1FF81048
FRAMES = 300


def note(line: str) -> None:
    print(line, file=sys.stderr)
    NUMBERS.parent.mkdir(parents=True, exist_ok=True)
    with open(NUMBERS, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def needs_rev2(core: Path) -> None:
    """Skip on a core without patch 0009 (lazpy.1), unless LAZ_REQUIRE_EMULATOR=1 (then fail)."""
    out = subprocess.run(["nm", "-gU", str(core)], capture_output=True, text=True, check=False).stdout
    if "_lazpy_threads" not in out:
        import os
        if os.environ.get("LAZ_REQUIRE_EMULATOR") == "1":
            pytest.fail(f"{core} is not core lazpy.2 (no lazpy_threads)")
        pytest.skip(f"{core} is not core lazpy.2")


def ticks_boot(host_paths, core, workdir, name, options) -> Tuple[Emulator, int, int]:
    emu = dh.boot(host_paths, workdir / name, core=core, options=options)
    assert emu.run(FRAMES).stopped_by == "frames"
    return emu, emu.memory.u32(COUNTER), emu.memory.u64(UPDATE_TICK)


def test_k_ticks_override(host_paths, lazpy_core, workdir):
    needs_rev2(lazpy_core)
    fixed = {"citra_init_ticks_type": "Fixed"}
    values: Dict[str, int] = {}
    emu0, count0, values["0"] = ticks_boot(host_paths, lazpy_core, workdir, "z", {**fixed, "citra_init_ticks_override": "0"})
    emu0.close()
    emu1, count1, values["1000000"] = ticks_boot(host_paths, lazpy_core, workdir, "m",
                                                 {**fixed, "citra_init_ticks_override": "1000000"})
    state = workdir / "st" / "state"
    emu1.save_state(state)
    emu1.close()
    emur, _, values["random"] = ticks_boot(host_paths, lazpy_core, workdir, "r", {"citra_init_ticks_type": "Random"})
    emur.close()
    note(f"k3: update_tick after {FRAMES} frames: {values}; counters {count0}, {count1}")
    assert count0 == 1 and count1 == 1
    assert values["0"] < 1 << 20
    assert values["1000000"] - values["0"] == 1000000
    assert values["random"] not in (values["0"], values["1000000"])
    with Emulator(host_paths.app, workdir / "s", state=state, core=lazpy_core,
                  options={**fixed, "citra_init_ticks_override": "0"}) as emu:
        assert emu.memory.u64(UPDATE_TICK) == values["1000000"]
        note("k3: a state from the 1000000 boot keeps its update_tick when loaded into a 0-override boot")


@pytest.mark.parametrize("bad", ["-5", "1x", "4294967296", " 1"])
def test_k_ticks_override_refused(host_paths, lazpy_core, workdir, bad):
    needs_rev2(lazpy_core)
    with pytest.raises(ArgumentError, match="citra_init_ticks_override"):
        dh.boot(host_paths, workdir / "a", core=lazpy_core, options={"citra_init_ticks_override": bad})


def elf_symbols() -> Dict[str, int]:
    out = subprocess.run(["nm", str(ELF)], capture_output=True, text=True, check=True).stdout
    return {m.group(2): int(m.group(1), 16) for m in re.finditer(r"^([0-9a-f]+) \w (\S+)$", out, re.M)}


def text_range() -> Tuple[int, int]:
    out = subprocess.run(["objdump", "-h", str(ELF)], capture_output=True, text=True, check=True).stdout
    match = re.search(r"^\s*\d+ \.text\s+([0-9a-f]+) ([0-9a-f]+)", out, re.M)
    assert match, "no .text in the test app's section headers"
    start = int(match.group(2), 16)
    return start, start + int(match.group(1), 16)


def test_k_threads(host_paths, lazpy_core, workdir):
    needs_rev2(lazpy_core)
    syms = elf_symbols()
    lo, hi = text_range()
    with dh.boot(host_paths, workdir / "a", core=lazpy_core) as emu:
        assert emu.run(FRAMES).stopped_by == "frames"
        threads = emu.threads()
        again = emu.threads()
        top = emu.memory.u32(syms["fake_heap_start"])
        size = emu.memory.u32(syms["__stacksize__"])
    for t in threads:
        note(f"k4: tid={t.tid} pid={t.pid:#x} {t.status_name} core={t.core} prio={t.priority} "
             f"current={t.is_current} pc={t.pc:#010x} lr={t.lr:#010x} sp={t.sp:#010x} cpsr={t.cpsr:#010x}")
    assert threads == again, "two calls with no run between differ"
    in_text = [t for t in threads if lo <= t.pc < hi]
    assert in_text, f"no thread has its pc in the app's .text {lo:#x}..{hi:#x}"
    app_pid = min(in_text, key=lambda t: t.tid).pid
    main = min((t for t in threads if t.pid == app_pid), key=lambda t: t.tid)
    assert lo <= main.pc < hi and main.lr != 0
    assert top - size <= main.sp <= top, f"sp {main.sp:#x} outside libctru's stack {top - size:#x}..{top:#x}"
    for core in {t.core for t in threads}:
        assert sum(1 for t in threads if t.core == core and t.is_current) <= 1
    note(f"k4: {len(threads)} threads; app pid {app_pid:#x}, main tid {main.tid}, stack {top - size:#x}..{top:#x}")


def test_k_threads_stock_core(host_paths, stock_core, workdir):
    with dh.boot(host_paths, workdir / "a", core=stock_core) as emu:
        emu.run(30)
        with pytest.raises(NeedsLazpyCore):
            emu.threads()


def test_k_threads_lazpy1_core(host_paths, workdir):
    """The v0.1.0 core (LAZ_CORE_OLD, lazpy.1) still boots under this host; only threads() needs lazpy.2."""
    import os
    old = os.environ.get("LAZ_CORE_OLD")
    if not old:
        pytest.skip("set LAZ_CORE_OLD to a lazpy.1 core")
    with dh.boot(host_paths, workdir / "a", core=Path(old)) as emu:
        assert emu.run(30).stopped_by == "frames"
        assert emu.stats().core_version.endswith("-lazpy.1")
        with pytest.raises(NeedsLazpyCore, match="lazpy_threads"):
            emu.threads()


def test_k_states_both_ways(host_paths, lazpy_core, workdir):
    """States cross between lazpy.1 (LAZ_CORE_OLD) and lazpy.2 in both directions; the meta says abi=3."""
    import os
    needs_rev2(lazpy_core)
    old = os.environ.get("LAZ_CORE_OLD")
    if not old:
        pytest.skip("set LAZ_CORE_OLD to a lazpy.1 core")
    for name, made_by, loaded_by in (("old-new", Path(old), lazpy_core), ("new-old", lazpy_core, Path(old))):
        state = workdir / name / "st" / "state"
        with dh.boot(host_paths, workdir / name / "a", core=made_by) as emu:
            emu.run(60)
            emu.save_state(state)
        assert "abi=3\n" in Path(f"{state}.meta").read_text()
        with Emulator(host_paths.app, workdir / name / "b", state=state, core=loaded_by) as emu:
            assert emu.run(10).stopped_by == "frames"
        note(f"k2: a state made by {made_by.name} ({name}) loaded and ran 10 frames")
