"""Reference solutions: Iterators & Generators."""
from collections.abc import Callable, Iterable, Iterator
from itertools import islice
from typing import Any, TypeVar

T = TypeVar("T")


def first_match(items: Iterable[T], predicate: Callable[[T], bool], default: T | None = None) -> T | None:
    # The generator expression is lazy; next() pulls only until the first hit.
    return next((item for item in items if predicate(item)), default)


class Countdown:
    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self) -> "Countdown":
        return self  # an iterator is its own iterable

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration  # this is how a for loop knows to stop
        value = self.current
        self.current -= 1
        return value


def clean_lines(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        text = line.strip()
        if text and not text.startswith("#"):
            yield text


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    # Validate eagerly: code in a generator body runs only on the first next(),
    # so the check lives in this normal function.
    if size < 1:
        raise ValueError("size must be >= 1")
    return _chunks(iter(items), size)


def _chunks(it: Iterator[T], size: int) -> Iterator[list[T]]:
    # islice keeps taking from the SAME iterator, so each call continues
    # where the previous chunk stopped. 3.12+ has itertools.batched (tuples).
    while chunk := list(islice(it, size)):
        yield chunk


def flatten(nested: Iterable[Any]) -> Iterator[Any]:
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)  # delegate to the recursive generator
        else:
            yield item


def paginate(fetch_page: Callable[[str | None], dict[str, Any]]) -> Iterator[Any]:
    cursor: str | None = None
    while True:
        page = fetch_page(cursor)  # runs only when the caller asks for more
        yield from page["items"]
        cursor = page.get("next_cursor")
        if cursor is None:
            return
