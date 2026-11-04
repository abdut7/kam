"""Lesson: Dataclasses, Enums & Type Hints.

Implement each function and class, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p13_typing.py
"""
from collections.abc import Iterable
from enum import StrEnum, auto
from typing import Protocol, TypedDict, TypeVar

T = TypeVar("T")


class Status(StrEnum):
    """Given: a StrEnum whose values are the lowercase member names."""

    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
    FAILED = auto()


def parse_status(raw: str) -> Status:
    """Turn user input into a Status member.

    Strip whitespace and lowercase the input, then look the value up.
    Raise ValueError for anything that is not a valid status.

    Example: parse_status(" Running ") -> Status.RUNNING
    """
    raise NotImplementedError


def first_or_default(items: Iterable[T], default: T) -> T:
    """Return the first item of any iterable (list, tuple, generator), or `default`
    when it is empty. Do not call len() or index into it: generators have neither.

    Example: first_or_default((x for x in [7, 8]), 0) -> 7
    """
    raise NotImplementedError


class HasArea(Protocol):
    """Given: anything with an area() -> float method matches, no inheritance needed."""

    def area(self) -> float: ...


def total_area(shapes: Iterable[HasArea]) -> float:
    """Return the sum of shape.area() for every shape, rounded to 2 decimals.
    0.0 for no shapes.

    Example: total_area([Square(2), Circle(1)]) -> 7.14
    """
    raise NotImplementedError


class Task:
    """Replace this whole class with a @dataclass named Task.

    Fields, in this order:
    - title: str (required). __post_init__ strips surrounding whitespace and
      raises ValueError if the stripped title is empty.
    - priority: int = 3. __post_init__ raises ValueError unless 1 <= priority <= 5.
    - tags: list[str], defaulting to a NEW empty list for every instance.

    Example: Task("  write tests ").title -> "write tests"
             Task("a").tags is not Task("b").tags -> True
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError


class Version:
    """Replace this whole class with a frozen, ordered @dataclass named Version.

    - Fields major, minor, patch: int, compared in that order (order=True).
    - Instances are immutable (frozen=True) and therefore hashable.
    - A @classmethod parse(text) that turns "1.4.2" (or " v1.4.2 ") into
      Version(1, 4, 2) and raises ValueError for anything else, such as "1.4"
      or "1.x.2".

    Example: sorted([Version.parse("1.10.0"), Version.parse("1.9.0")])[0] -> Version(1, 9, 0)
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError

    @classmethod
    def parse(cls, text: str) -> "Version":
        raise NotImplementedError


class UserPayload(TypedDict):
    """Given: at runtime this is a plain dict; the hints are not checked."""

    name: str
    age: int


def validate_payload(data: dict[str, object]) -> UserPayload:
    """Type hints are not enforced at runtime, so check the data yourself.

    - "name" must be a non-empty str (stripped), "age" must be an int between
      0 and 150. bool is NOT an acceptable int here (isinstance(True, int) is True).
    - Missing keys or wrong types raise TypeError; an empty name or an age out of
      range raises ValueError.
    - Return a new dict with only "name" (stripped) and "age"; ignore extra keys.

    Example: validate_payload({"name": " Asha ", "age": 31, "x": 1}) -> {"name": "Asha", "age": 31}
    """
    raise NotImplementedError
