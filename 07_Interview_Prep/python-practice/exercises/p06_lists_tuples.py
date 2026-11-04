"""Practice: lists and tuples.

Replace each `raise NotImplementedError` with your code, then run:
    uv run --with pytest pytest tests/test_p06_lists_tuples.py
"""
import bisect  # noqa: F401  (you will need it for letter_grade)
from typing import TypeVar

T = TypeVar("T")


def chunk(items: list[T], size: int) -> list[list[T]]:
    """Split `items` into consecutive batches of `size` (the last may be shorter),
    for example to send texts to an embeddings API in groups.
    Raise ValueError if size is less than 1.

    Example: chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    """
    raise NotImplementedError


def flatten(nested: list[list[T]]) -> list[T]:
    """Flatten one level of nesting with a nested list comprehension.

    Example: flatten([[1, 2], [], [3]]) == [1, 2, 3]
    """
    raise NotImplementedError


def rotate(items: list[T], k: int) -> list[T]:
    """Return a NEW list rotated right by k positions using slicing.
    k may be larger than the list or negative (negative rotates left).
    The input list must not change.

    Example: rotate([1, 2, 3, 4, 5], 2) == [4, 5, 1, 2, 3]
    """
    raise NotImplementedError


def make_grid(rows: int, cols: int, fill: T = 0) -> list[list[T]]:
    """Build a rows x cols grid filled with `fill` where every row is an
    independent list (changing one cell must not change other rows).

    Example: make_grid(2, 3) == [[0, 0, 0], [0, 0, 0]]
    """
    raise NotImplementedError


def top_results(results: list[tuple[str, float]], n: int) -> list[tuple[str, float]]:
    """Return the n best (title, score) pairs: highest score first, and for equal
    scores, title in ascending order. Do not modify the input list.

    Example: top_results([("b", 0.9), ("a", 0.9), ("c", 0.5)], 2) == [("a", 0.9), ("b", 0.9)]
    """
    raise NotImplementedError


def letter_grade(score: float) -> str:
    """Map a score from 0 to 100 to a grade with the bisect module:
    below 60 -> "F", 60-69 -> "D", 70-79 -> "C", 80-89 -> "B", 90 and above -> "A".
    Raise ValueError if the score is outside 0..100.

    Example: letter_grade(75) == "C"
    """
    raise NotImplementedError
