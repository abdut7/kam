"""Lesson 19 solutions: Python internals and performance."""
from __future__ import annotations

import tracemalloc
from collections.abc import Callable, Hashable, Iterable
from functools import cache
from typing import Any


def is_hashable(obj: object) -> bool:
    """hash() works only if the object, and everything a tuple holds, is hashable."""
    try:
        hash(obj)
    except TypeError:                   # "unhashable type: 'list'"
        return False
    return True


def dedupe_preserve_order(items: Iterable[Hashable]) -> list[Any]:
    """O(n): set membership is O(1) on average, `x in some_list` would be O(n)."""
    seen: set[Hashable] = set()
    out: list[Any] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
    # One-liner with the same result: list(dict.fromkeys(items)), since dicts keep insertion order.


def pair_with_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    """One pass with a dict of value -> first index: O(n) instead of O(n^2)."""
    first_index: dict[int, int] = {}
    for j, value in enumerate(nums):
        i = first_index.get(target - value)
        if i is not None:
            return (i, j)
        first_index.setdefault(value, j)   # keep the earliest index for duplicates
    return None


class Point:
    """Equal points hash equally; __slots__ removes the per-instance __dict__."""

    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented          # lets Python try the other side, then fall back to False
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))      # built from the same fields __eq__ compares

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"


@cache                                     # functools.cache (3.9+) is lru_cache(maxsize=None)
def fib(n: int) -> int:
    """Each n is computed once, so the call tree collapses from O(2^n) to O(n)."""
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def peak_bytes(fn: Callable[[], object]) -> int:
    """Peak bytes Python allocated while fn ran, measured with tracemalloc."""
    tracemalloc.start()
    try:
        fn()
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()                 # tracing slows every allocation: always stop it
    return peak
