"""Lesson: Object-Oriented Python.

Implement each class, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p12_oop.py
"""
from collections.abc import Callable, Iterator
from typing import Any


class BankAccount:
    """A bank account.

    - Class attribute `interest_rate = 0.02` (shared by all accounts).
    - __init__(owner, balance=0.0): raise ValueError if balance is negative.
      Store the balance in `self._balance`.
    - `balance`: a read-only @property (no setter).
    - deposit(amount) and withdraw(amount) return the new balance; raise
      ValueError for amount <= 0 or for withdrawing more than the balance.
    - from_dict(data): a @classmethod alternative constructor reading
      {"owner": ..., "balance": ...}; balance is optional.
    - __repr__: BankAccount(owner='Asha', balance=100.0)

    Example: BankAccount("Asha", 100.0).withdraw(30.0) -> 70.0
    """

    interest_rate = 0.02

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        raise NotImplementedError

    @property
    def balance(self) -> float:
        raise NotImplementedError

    def deposit(self, amount: float) -> float:
        raise NotImplementedError

    def withdraw(self, amount: float) -> float:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BankAccount":
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError


class Temperature:
    """A temperature stored in Celsius.

    - `celsius` property with a setter that raises ValueError below -273.15.
    - `fahrenheit` property computed from celsius (F = C * 9 / 5 + 32), with a
      setter that converts back and goes through the celsius validation.

    Example: t = Temperature(100); t.fahrenheit -> 212.0
    """

    def __init__(self, celsius: float = 0.0) -> None:
        raise NotImplementedError

    @property
    def celsius(self) -> float:
        raise NotImplementedError

    @celsius.setter
    def celsius(self, value: float) -> None:
        raise NotImplementedError

    @property
    def fahrenheit(self) -> float:
        raise NotImplementedError

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        raise NotImplementedError


class Money:
    """An amount of money in integer minor units (paise, cents) plus a currency.

    - __eq__ and __hash__ based on (cents, currency), so Money works in sets
      and as a dict key. Comparing with a non-Money returns NotImplemented.
    - __lt__: ValueError if currencies differ. Decorate the class with
      functools.total_ordering so <=, > and >= work too.
    - __add__: same currency only (ValueError otherwise).
    - __repr__: Money(1050, 'INR')    __str__: 10.50 INR

    Example: Money(1050, "INR") + Money(50, "INR") == Money(1100, "INR")
    """

    def __init__(self, cents: int, currency: str) -> None:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError

    def __lt__(self, other: "Money") -> bool:
        raise NotImplementedError

    def __add__(self, other: "Money") -> "Money":
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class Playlist:
    """A container of song titles that behaves like a built-in collection.

    - __init__(name, songs=None): copy songs into a new list. Do not use a
      mutable default argument.
    - add(song) appends a title.
    - len(p), for s in p, p[0], p[1:3] (a slice returns a plain list).
    - "song" in p is case-insensitive.

    Example: p = Playlist("Focus", ["Intro"]); p.add("Flow"); len(p) -> 2
    """

    def __init__(self, name: str, songs: list[str] | None = None) -> None:
        raise NotImplementedError

    def add(self, song: str) -> None:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError

    def __getitem__(self, index: int | slice) -> str | list[str]:
        raise NotImplementedError

    def __contains__(self, song: object) -> bool:
        raise NotImplementedError


class Shape:
    """Make this an abstract base class (inherit from abc.ABC) with an abstract
    method area() -> float, so Shape() raises TypeError.

    Keep describe() concrete: it returns "<ClassName> with area <area to 2 decimals>".

    Example: Rectangle(2, 3).describe() -> "Rectangle with area 6.00"
    """

    def area(self) -> float:
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


class Rectangle(Shape):
    """A rectangle with width and height. area() = width * height."""

    def __init__(self, width: float, height: float) -> None:
        raise NotImplementedError

    def area(self) -> float:
        raise NotImplementedError


class Circle(Shape):
    """A circle with a radius. area() = math.pi * radius ** 2."""

    def __init__(self, radius: float) -> None:
        raise NotImplementedError

    def area(self) -> float:
        raise NotImplementedError


class CallCounter:
    """Wrap a function, count how many times it is called, and forward the call.

    Works as a decorator because instances are callable (__call__).
    Expose the count as `calls` and the wrapped function's name as `__name__`.

    Example:
        @CallCounter
        def add(a, b): return a + b
        add(1, 2) -> 3; add.calls -> 1
    """

    def __init__(self, func: Callable[..., Any]) -> None:
        raise NotImplementedError

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
