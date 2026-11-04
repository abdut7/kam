"""Lesson 19: Python internals and performance.

Implement each function and the Point class, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p19_internals.py
"""
from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from typing import Any


def is_hashable(obj: object) -> bool:
    """Return True if obj can be a dict key or set member (hash(obj) works), else False.

    Example: is_hashable((1, 2)) -> True; is_hashable([1, 2]) -> False;
             is_hashable((1, [2])) -> False, because a tuple hashes its items
    """
    raise NotImplementedError


def dedupe_preserve_order(items: Iterable[Hashable]) -> list[Any]:
    """Remove duplicates, keeping the first occurrence of each item, in order.

    Must be O(n): use a set for membership checks, never `x in some_list`.

    Example: dedupe_preserve_order([3, 1, 3, 2, 1]) -> [3, 1, 2]
    """
    raise NotImplementedError


def pair_with_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return indices (i, j) with i < j and nums[i] + nums[j] == target, or None.

    Scan left to right and return the first pair found when you reach j; for i use
    the earliest index holding the needed value. Must be O(n): one pass with a dict
    of value -> index, not two nested loops.

    Example: pair_with_sum([2, 7, 11, 15], 9) -> (0, 1); pair_with_sum([1, 2], 10) -> None
    """
    raise NotImplementedError


class Point:
    """A 2D point that works as a dict key and set member, using __slots__.

    - Point(1, 2) == Point(1, 2) is True, and both have the same hash
    - Point(1, 2) == (1, 2) is False (compare only with other Points)
    - instances have no __dict__, so setting an unknown attribute raises AttributeError

    Example: {Point(1, 2): "a"}[Point(1, 2)] -> "a"
    """

    def __init__(self, x: int, y: int) -> None:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError


def fib(n: int) -> int:
    """Return the n-th Fibonacci number (fib(0) == 0, fib(1) == 1) using plain recursion,
    made fast by decorating it with functools.cache or functools.lru_cache.

    fib(90) must return instantly, and fib.cache_info() must exist.

    Example: fib(10) -> 55
    """
    raise NotImplementedError


def peak_bytes(fn: Callable[[], object]) -> int:
    """Run fn() and return the peak number of bytes Python allocated while it ran.

    Use tracemalloc: start(), call fn, get_traced_memory() returns (current, peak),
    then stop() (in a finally block, so tracing never stays on).

    Example: peak_bytes(lambda: [0] * 1_000_000) -> at least 8_000_000 (one 8-byte pointer per item)
    """
    raise NotImplementedError
