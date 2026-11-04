"""Reference solutions: lists and tuples."""
import bisect
from typing import TypeVar

T = TypeVar("T")

GRADE_BREAKS = [60, 70, 80, 90]  # must stay sorted for bisect
GRADES = "FDCBA"  # one more grade than breakpoints


def chunk(items: list[T], size: int) -> list[list[T]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    # range steps through the start of each batch; slicing never raises past the end.
    return [items[i : i + size] for i in range(0, len(items), size)]


def flatten(nested: list[list[T]]) -> list[T]:
    # Same order as the nested loops: for row in nested: for item in row: ...
    return [item for row in nested for item in row]


def rotate(items: list[T], k: int) -> list[T]:
    if not items:
        return []
    k %= len(items)  # handles k > len and negative k (rotate left)
    return items[-k:] + items[:-k] if k else items[:]


def make_grid(rows: int, cols: int, fill: T = 0) -> list[list[T]]:
    # A comprehension builds a NEW inner list per row.
    # [[fill] * cols] * rows would repeat one shared row object.
    return [[fill] * cols for _ in range(rows)]


def top_results(results: list[tuple[str, float]], n: int) -> list[tuple[str, float]]:
    # Negate the score for descending order, keep the title ascending for ties.
    # sorted() returns a new list, so the caller's list is untouched.
    return sorted(results, key=lambda pair: (-pair[1], pair[0]))[:n]


def letter_grade(score: float) -> str:
    if not 0 <= score <= 100:
        raise ValueError(f"score out of range: {score}")
    # bisect_right counts how many breakpoints are <= score: 75 -> 2 -> "C".
    return GRADES[bisect.bisect_right(GRADE_BREAKS, score)]
