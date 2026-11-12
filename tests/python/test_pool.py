"""Pool against a fake Emulator (no emulator, no slots)."""
import threading
import warnings

import pytest

from libazahar import Pool, _slots


class FakeEmu:
    """Records its construction, closing and the thread it ran in."""

    made = []
    lock = threading.Lock()

    def __init__(self, app, workdir, **kwargs):
        self.app, self.workdir, self.kwargs, self.closed = app, workdir, kwargs, 0
        with FakeEmu.lock:
            FakeEmu.made.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self.closed += 1


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    FakeEmu.made = []
    monkeypatch.setenv("LAZ_MAX_INSTANCES", "3")


def test_p1_results_in_order_in_job_folders(tmp_path):
    with Pool(3, "app.3dsx", tmp_path, factory=FakeEmu) as pool:
        results = pool.map(lambda emu, item: (item * 2, emu.workdir.name), range(7))
    assert results == [(i * 2, f"job-{i:04d}") for i in range(7)]
    assert sorted(e.workdir.name for e in FakeEmu.made) == [f"job-{i:04d}" for i in range(7)]


def test_p2_a_raising_job_is_raised_after_all_ended(tmp_path):
    def job(emu, item):
        if item == 2:
            raise RuntimeError("job 2 failed")
        return item

    pool = Pool(2, "app", tmp_path, factory=FakeEmu)
    with pytest.raises(RuntimeError, match="job 2 failed"):
        pool.map(job, range(6))
    pool.close()
    assert len(FakeEmu.made) == 6 and all(e.closed == 1 for e in FakeEmu.made)


def test_p3_overrides_win_over_kwargs(tmp_path):
    with Pool(1, "app", tmp_path, factory=FakeEmu, sd_seed="base", timeout=5.0) as pool:
        pool.map(lambda emu, item: None, [1], sd_seed="mine", state="s.state")
        pool.submit(lambda emu, item: None, 2).result()
    first, second = FakeEmu.made
    assert first.kwargs == {"sd_seed": "mine", "timeout": 5.0, "state": "s.state"}
    assert second.kwargs == {"sd_seed": "base", "timeout": 5.0}


def test_p4_size_checks(tmp_path):
    with pytest.warns(UserWarning, match=r"Pool\(5\) > cap 3") as caught:
        Pool(5, "app", tmp_path, factory=FakeEmu).close()
    assert len([w for w in caught if "cap 3" in str(w.message)]) == 1
    for bad in (0, 65):
        with pytest.raises(ValueError):
            Pool(bad, "app", tmp_path, factory=FakeEmu)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        if _slots.os.getloadavg()[0] <= 2 * (_slots.os.cpu_count() or 1):
            Pool(3, "app", tmp_path, factory=FakeEmu).close()
