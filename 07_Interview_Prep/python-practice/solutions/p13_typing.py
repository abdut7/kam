"""Reference solutions: Dataclasses, Enums & Type Hints."""
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Protocol, TypedDict, TypeVar

T = TypeVar("T")  # 3.12+ could write: def first_or_default[T](...)


class Status(StrEnum):
    PENDING = auto()  # auto() in a StrEnum gives the lowercase name: "pending"
    RUNNING = auto()
    DONE = auto()
    FAILED = auto()


def parse_status(raw: str) -> Status:
    # Calling the enum with a value looks the member up and raises
    # ValueError("'x' is not a valid Status") for unknown values.
    return Status(raw.strip().lower())


def first_or_default(items: Iterable[T], default: T) -> T:
    # next() with a default works on any iterable once we take an iterator.
    return next(iter(items), default)


class HasArea(Protocol):
    def area(self) -> float: ...


def total_area(shapes: Iterable[HasArea]) -> float:
    # Structural typing: we only rely on .area(), not on a base class.
    return round(sum(shape.area() for shape in shapes), 2)


@dataclass
class Task:
    title: str
    priority: int = 3
    # A bare [] default would be rejected by @dataclass; default_factory
    # builds a fresh list for every instance.
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("title must not be empty")
        if not 1 <= self.priority <= 5:
            raise ValueError(f"priority must be 1..5, got {self.priority}")


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, text: str) -> "Version":
        parts = text.strip().removeprefix("v").split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"not a version: {text!r}")
        major, minor, patch = (int(p) for p in parts)
        return cls(major, minor, patch)


class UserPayload(TypedDict):
    name: str
    age: int


def validate_payload(data: dict[str, object]) -> UserPayload:
    name = data.get("name")
    age = data.get("age")
    if not isinstance(name, str):
        raise TypeError("name must be a str")
    # bool is a subclass of int, so exclude it explicitly.
    if not isinstance(age, int) or isinstance(age, bool):
        raise TypeError("age must be an int")
    name = name.strip()
    if not name:
        raise ValueError("name must not be empty")
    if not 0 <= age <= 150:
        raise ValueError("age must be between 0 and 150")
    return {"name": name, "age": age}
