"""Step E's live gate (docs/plans/phase-e.md section 6): the slot cap, a kill freeing a slot, the Pool, the nice.

Run: LAZ_REQUIRE_EMULATOR=1 nice -n 10 python3 -m pytest -q -rs tests/python/test_pool_live.py
"""
from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

import d_helpers as dh
import testapp_log as tl
from libazahar import Emulator, Pool, _slots

pytestmark = pytest.mark.slow

REAL_SLOTS = 3
STARTS_WAIT_S = 3.0
KILL_TO_ACQUIRE_S = 1.0
RUN_FRAMES = 60


def info(text: str) -> None:
    print(text, file=sys.stderr)


def load() -> str:
    return f"load {os.getloadavg()[0]:.1f}"


@pytest.fixture
def gate_slots(monkeypatch, repo_root):
    """Rule 1: hold the real machine-wide slots (real folder, default cap) while the gate runs; rule 2: then a
    private folder with cap 3 for the Emulators under test. Order matters: the real ones are taken first."""
    monkeypatch.delenv("LAZ_SLOT_DIR", raising=False)
    monkeypatch.delenv("LAZ_MAX_INSTANCES", raising=False)
    begin = time.monotonic()
    held = [_slots.acquire(timeout=1800) for _ in range(min(REAL_SLOTS, _slots.cap()))]
    info(f"real slots: took {len(held)} after {time.monotonic() - begin:.1f} s ({load()})")
    private = repo_root / "runs" / "e-pytest" / "slots"
    shutil.rmtree(private, ignore_errors=True)
    monkeypatch.setenv("LAZ_SLOT_DIR", str(private))
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "3")
    try:
        yield private
    finally:
        for slot in held:
            slot.release()
        info(f"end: {load()}")


def worker_nice(pid: int) -> int:
    done = subprocess.run(["ps", "-o", "nice=", "-p", str(pid)], capture_output=True, text=True, check=True)
    return int(done.stdout.strip())


def slot_txt(workdir: Path) -> dict:
    return dict(part.split("=") for part in (workdir / "slot.txt").read_text().split())


def test_g1_g2_g4_cap_kill_and_nice(host_paths, workdir, seed, gate_slots):
    """g1: three boot, a fourth waits; g2: a kill frees its slot within 1 s; g4: every worker's nice is 10 or more."""
    info(f"start: {load()}")
    emus = []
    fourth = {}

    def boot_fourth():
        try:
            fourth["emu"] = Emulator(host_paths.app, workdir / "i3", sd_seed=seed(ready_at=400))
            fourth["result"] = fourth["emu"].run(RUN_FRAMES)
        except BaseException as error:  # noqa: BLE001  (stored, then asserted on in the main thread)
            fourth["error"] = error

    try:
        for k in range(3):
            emu = Emulator(host_paths.app, workdir / f"i{k}", sd_seed=seed(ready_at=100 * (k + 1)))
            emus.append(emu)
            assert emu.run(RUN_FRAMES).frames == RUN_FRAMES
        niceness = [worker_nice(emu.pid) for emu in emus]
        info(f"g4: worker nice values {niceness}")
        assert all(value >= 10 for value in niceness)
        thread = threading.Thread(target=boot_fourth)
        thread.start()
        time.sleep(STARTS_WAIT_S)
        waiting = workdir / "i3"
        assert thread.is_alive(), f"the 4th should wait for a slot: {fourth}"
        assert not (waiting / "slot.txt").exists() and not (waiting / "host.map").exists()
        killed = slot_txt(workdir / "i1")["slot"]
        t_kill = time.time()
        os.kill(emus[1].pid, signal.SIGKILL)
        thread.join(timeout=emus[0].boot_timeout + RUN_FRAMES)
        assert not thread.is_alive(), "the 4th never finished"
        assert "error" not in fourth, fourth.get("error")
        acquired = float(slot_txt(waiting)["acquired"])
        info(f"g2: kill to acquire {acquired - t_kill:.3f} s; slot {slot_txt(waiting)['slot']} (killed one: {killed})")
        assert 0 <= acquired - t_kill < KILL_TO_ACQUIRE_S
        assert slot_txt(waiting)["slot"] == killed
        assert fourth["result"].frames == RUN_FRAMES
    finally:
        for emu in [*emus, fourth.get("emu")]:
            if emu is not None:
                emu.close()


def job(emu: Emulator, ready_at: int):
    """400 frames with a PNG shot at 300; returns the SD log text and the shot paths."""
    result = emu.run(400, shots=[300])
    shot = result.shots[300]
    return (emu.sd / "testapp" / "log.txt").read_text(), shot.top, shot.bottom


def test_g3_pool_of_three(host_paths, workdir, seed, gate_slots):
    info(f"start: {load()}")
    seeds = [100, 200, 300]
    with Pool(3, host_paths.app, workdir / "pool") as pool:
        futures = [pool.submit(job, ready_at, sd_seed=seed(ready_at=ready_at)) for ready_at in seeds]
        results = [future.result() for future in futures]
    for index, (ready_at, (text, top, bottom)) in enumerate(zip(seeds, results)):
        folder = workdir / "pool" / f"job-{index:04d}"
        assert top.startswith(str(folder)) and bottom.startswith(str(folder))
        assert re.search(rf"^start .*\bready_at={ready_at}\b", text, re.M), text[:200]
        _, events = tl.parse_log(folder / "sys" / "Azahar" / "sdmc" / "testapp" / "log.txt")
        assert [e["f"] for e in events if e["kind"] == "ready"] == [ready_at]
        verdict = dh.markers_ok(top, bottom)
        assert verdict.startswith("markers ok"), verdict
        others = [f"job-{j:04d}" for j in range(3) if j != index]
        for path in (folder / "host.log", folder / "sys" / "Azahar" / "sdmc" / "testapp" / "log.txt"):
            body = path.read_text(errors="replace")
            assert not any(name in body for name in others), f"{path} names another job's folder"
        assert any((folder / "shots").glob("*.png"))
