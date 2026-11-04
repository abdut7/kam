"""Lesson: Iterators & Generators.

Implement each function and class, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p14_generators.py
"""
from collections.abc import Callable, Iterable, Iterator
from typing import Any, TypeVar

T = TypeVar("T")


def first_match(items: Iterable[T], predicate: Callable[[T], bool], default: T | None = None) -> T | None:
    """Return the first item for which predicate(item) is true, else `default`.
    Stop as soon as a match is found (use a generator expression with next()).

    Example: first_match([1, 8, 3, 9], lambda n: n > 5) -> 8
    """
    raise NotImplementedError


class Countdown:
    """An iterator written by hand with the iteration protocol.

    - Countdown(3) yields 3, 2, 1 and then stops (raise StopIteration).
    - __iter__ returns self, so the object is a one-shot iterator: a second
      loop over the same object yields nothing.
    - Countdown(0) or a negative start yields nothing.

    Example: list(Countdown(3)) -> [3, 2, 1]
    """

    def __init__(self, start: int) -> None:
        raise NotImplementedError

    def __iter__(self) -> "Countdown":
        raise NotImplementedError

    def __next__(self) -> int:
        raise NotImplementedError


def clean_lines(lines: Iterable[str]) -> Iterator[str]:
    """Generator: yield each line stripped of surrounding whitespace, skipping
    blank lines and comment lines (those starting with "#" after stripping).
    Must be lazy: it should work on an endless iterator.

    Example: list(clean_lines(["  a ", "", "# note", "b\\n"])) -> ["a", "b"]
    """
    raise NotImplementedError


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Generator: yield lists of up to `size` items; the last list may be shorter.
    Works on any iterable, including generators (no len(), no slicing).
    Raise ValueError if size < 1 (raise it when the function is called, before
    iteration starts, so wrap the generator in a normal function).

    Example: list(chunked(range(7), 3)) -> [[0, 1, 2], [3, 4, 5], [6]]
    """
    raise NotImplementedError


def flatten(nested: Iterable[Any]) -> Iterator[Any]:
    """Generator: flatten lists and tuples nested to any depth, using `yield from`.
    Strings, dicts and other values are yielded as single items.

    Example: list(flatten([1, [2, (3, [4])], "ab"])) -> [1, 2, 3, 4, "ab"]
    """
    raise NotImplementedError


def paginate(fetch_page: Callable[[str | None], dict[str, Any]]) -> Iterator[Any]:
    """Generator over a cursor-paginated API.

    fetch_page(cursor) returns {"items": [...], "next_cursor": str | None}.
    Call it first with None, yield every item of every page, and stop when
    next_cursor is None. Fetch a page only when the caller needs its items
    (if the caller stops early, later pages must not be requested).

    Example: pages {None: [1, 2] -> "c2", "c2": [3] -> None} yields 1, 2, 3
    """
    raise NotImplementedError
