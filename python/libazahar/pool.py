"""``Pool``: run one job per fresh Emulator, several at once, held to the machine-wide slot cap (phase-e.md 3.3).

    with Pool(3, app, "runs/x") as p:
        results = p.map(job, seeds, sd_seed=seed_folder)      # job(emu, item) -> result, in item order

Each job gets its own Emulator in ``root/job-0000``, ``job-0001``, ... (its own ``sys/``, ``shots/``, ``host.log``,
``host.map``), closed when the job ends, however it ends. ``n`` threads run jobs; how many Emulators are alive at
once is still bounded by the slot cap (``_slots.cap()``), so ``n`` above the cap makes the extra jobs wait for a slot.
"""
from __future__ import annotations

import threading
import warnings
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Union

from . import _slots
from .emulator import Emulator
from .errors import ArgumentError

__all__ = ["Pool"]

MAX_N = 64


class Pool:
    """``n`` job threads over fresh Emulators of ``app`` under ``root``.

    ``emulator_kwargs`` go to every Emulator; ``submit``/``map`` ``overrides`` win over them (for example a per-job
    ``sd_seed``, ``state`` or ``options``). ``factory`` replaces ``Emulator`` (for tests with a fake). Raises
    ArgumentError when ``n`` is outside 1..64. Warns UserWarning when ``n`` exceeds the slot cap and LoadWarning when
    the machine is loaded.
    """

    def __init__(self, n: int, app: Union[str, Path], root: Union[str, Path], *,
                 factory: Optional[Callable[..., Any]] = None, **emulator_kwargs: Any) -> None:
        if not 1 <= int(n) <= MAX_N:
            raise ArgumentError(f"Pool size {n} is outside 1 to {MAX_N}")
        self.n = int(n)
        self.app = app
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._factory = factory or Emulator
        self._kwargs = dict(emulator_kwargs)
        self._lock = threading.Lock()
        self._next_job = 0
        slots = _slots.cap()
        if self.n > slots:
            warnings.warn(UserWarning(f"Pool({self.n}) > cap {slots}: at most {slots} run at once; "
                                      "the rest wait for a slot"), stacklevel=2)
        _slots.warn_if_loaded(stacklevel=3)
        self._executor = ThreadPoolExecutor(max_workers=self.n, thread_name_prefix="libazahar-pool")

    def _job(self, fn: Callable[[Any, Any], Any], item: Any, index: int, overrides: dict) -> Any:
        workdir = self.root / f"job-{index:04d}"
        kwargs = {**self._kwargs, **overrides}
        with self._factory(self.app, workdir, **kwargs) as emu:
            return fn(emu, item)

    def submit(self, fn: Callable[[Any, Any], Any], item: Any, **overrides: Any) -> Future:
        """Queue ``fn(emulator, item)`` on a fresh Emulator; the Future holds its result or its exception."""
        with self._lock:
            index = self._next_job
            self._next_job += 1
        return self._executor.submit(self._job, fn, item, index, overrides)

    def map(self, fn: Callable[[Any, Any], Any], items: Iterable[Any], **overrides: Any) -> List[Any]:
        """Run ``fn`` over ``items``; results in item order. The first exception is raised after all jobs end."""
        futures = [self.submit(fn, item, **overrides) for item in items]
        errors = [future.exception() for future in futures]      # waits for every job
        for error in errors:
            if error is not None:
                raise error
        return [future.result() for future in futures]

    def close(self, wait: bool = True) -> None:
        """Stop accepting jobs; with ``wait`` block until the running ones end (each closes its Emulator)."""
        self._executor.shutdown(wait=wait)

    def __enter__(self) -> "Pool":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Wait for running jobs; when the body raised, jobs still queued are cancelled instead of run."""
        self._executor.shutdown(wait=True, cancel_futures=exc_type is not None)
