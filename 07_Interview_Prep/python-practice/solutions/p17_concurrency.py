"""Lesson 17 solutions: threads, processes and the GIL."""
from __future__ import annotations

import pickle
import queue
import threading
import time
from collections.abc import Callable, Hashable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any


def is_picklable(obj: object) -> bool:
    """Return True if obj survives pickle.dumps, which every process pool needs."""
    try:
        pickle.dumps(obj)
    except (pickle.PicklingError, TypeError, AttributeError):
        # PicklingError: lambdas (and local functions on 3.14+)
        # AttributeError: local functions on older versions
        # TypeError: locks, generators, open files, sockets
        return False
    return True


def thread_map(fn: Callable[[Any], Any], items: Iterable[Any], max_workers: int = 8) -> list[Any]:
    """Blocking I/O in parallel threads; results come back in input order."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        # map keeps input order; list() waits for every result
        return list(pool.map(fn, items))


class SafeCounter:
    """Read-modify-write protected by a lock so no increment is lost."""

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:                 # the whole read, switch, write is one step now
            current = self._value
            time.sleep(0)                # another thread may run here, but cannot enter
            self._value = current + 1

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


def map_collect_errors(
    fn: Callable[[Any], Any], items: list[Hashable], max_workers: int = 4
) -> dict[Any, Any]:
    """Like Promise.allSettled: every item maps to its result or to the exception it raised."""
    out: dict[Any, Any] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn, item): item for item in items}
        for fut in as_completed(futures):          # completion order, not input order
            item = futures[fut]
            try:
                out[item] = fut.result()           # re-raises the worker's exception here
            except Exception as exc:
                out[item] = exc
    return out


_STOP = object()   # a unique sentinel: no real item can be equal to it


def threaded_pipeline(
    items: list[Any], worker_fn: Callable[[Any], Any], n_workers: int = 3
) -> list[Any]:
    """Producer (the caller) -> bounded jobs queue -> n worker threads -> results queue."""
    jobs: queue.Queue[Any] = queue.Queue(maxsize=10)     # put() blocks when full: backpressure
    results: queue.Queue[tuple[int, Any]] = queue.Queue()

    def worker() -> None:
        while (job := jobs.get()) is not _STOP:
            index, item = job
            results.put((index, worker_fn(item)))

    threads = [threading.Thread(target=worker) for _ in range(n_workers)]
    for t in threads:
        t.start()
    for pair in enumerate(items):
        jobs.put(pair)
    for _ in threads:
        jobs.put(_STOP)                                  # one stop signal per worker
    for t in threads:
        t.join()

    ordered: list[Any] = [None] * len(items)
    while not results.empty():                           # safe: every worker has exited
        index, value = results.get()
        ordered[index] = value
    return ordered


def _sum_squares(chunk: Iterable[int]) -> int:
    # Top level, so the pool can pickle it by reference (module + name).
    return sum(x * x for x in chunk)


def parallel_sum_of_squares(chunks: list[range], max_workers: int = 2) -> int:
    """CPU-bound work: each chunk is summed in its own process, each with its own GIL."""
    if not chunks:
        return 0
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        return sum(pool.map(_sum_squares, chunks))
