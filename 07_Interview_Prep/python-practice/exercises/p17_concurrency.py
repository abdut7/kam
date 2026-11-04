"""Lesson 17: threads, processes and the GIL.

Implement each function, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p17_concurrency.py
"""
from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from typing import Any


def is_picklable(obj: object) -> bool:
    """Return True if obj can be pickled (pickle.dumps works), else False.

    Process pools pickle every function, argument and result they send between
    processes. Lambdas, local functions, locks, open files and generators fail.
    Catch the exceptions pickle raises (more than one type) and return False.

    Example: is_picklable({"a": [1, 2]}) -> True; is_picklable(lambda x: x) -> False
    """
    raise NotImplementedError


def thread_map(fn: Callable[[Any], Any], items: Iterable[Any], max_workers: int = 8) -> list[Any]:
    """Run fn on every item with a ThreadPoolExecutor and return results in input order.

    This is the tool for blocking I/O: 8 calls that each sleep 50 ms should take
    about 50 ms in total with 8 workers, not 400 ms.

    Example: thread_map(lambda x: x * 2, [1, 2, 3]) -> [2, 4, 6]
    """
    raise NotImplementedError


class SafeCounter:
    """A counter many threads can increment at once without losing updates.

    increment() must do a read-modify-write with a thread switch in the middle,
    exactly like real code that reads a value, does some I/O, then writes back:

        current = self._value
        time.sleep(0)              # lets another thread run here
        self._value = current + 1

    Without a lock, 4 threads x 200 increments ends far below 800.
    Protect the sequence with a threading.Lock. The `value` property returns the count.

    Example: 4 threads each calling increment() 200 times -> counter.value == 800
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def increment(self) -> None:
        raise NotImplementedError

    @property
    def value(self) -> int:
        raise NotImplementedError


def map_collect_errors(
    fn: Callable[[Any], Any], items: list[Hashable], max_workers: int = 4
) -> dict[Any, Any]:
    """Run fn on every item in a thread pool using submit() and as_completed().

    Return a dict mapping each item to its result, or to the exception instance it
    raised. One failing item must not stop the others (like Promise.allSettled).

    Example: map_collect_errors(lambda x: 10 // x, [1, 0, 5])
             -> {1: 10, 0: ZeroDivisionError(...), 5: 2}
    """
    raise NotImplementedError


def threaded_pipeline(
    items: list[Any], worker_fn: Callable[[Any], Any], n_workers: int = 3
) -> list[Any]:
    """Producer-consumer with queue.Queue.

    The calling thread is the producer: it puts (index, item) pairs on a bounded
    jobs queue (maxsize=10). n_workers threads take pairs, call worker_fn(item) and
    put (index, result) on a results queue. Stop the workers with one sentinel per
    worker, join them, then return the results in input order.

    Example: threaded_pipeline([1, 2, 3], lambda x: x * x, n_workers=2) -> [1, 4, 9]
    """
    raise NotImplementedError


def parallel_sum_of_squares(chunks: list[range], max_workers: int = 2) -> int:
    """CPU-bound work on a ProcessPoolExecutor: return the sum of x * x over every
    number in every chunk, summing each chunk in a worker process.

    The function you send to the pool must be defined at module top level
    (write a small helper), because lambdas and nested functions cannot be pickled.
    An empty list of chunks returns 0.

    Example: parallel_sum_of_squares([range(0, 3), range(3, 5)]) -> 0 + 1 + 4 + 9 + 16 = 30
    """
    raise NotImplementedError
