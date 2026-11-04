"""Reference solutions: Object-Oriented Python."""
import functools
import math
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from typing import Any


class BankAccount:
    interest_rate = 0.02  # class attribute: immutable, so sharing it is safe

    def __init__(self, owner: str, balance: float = 0.0) -> None:
        if balance < 0:
            raise ValueError("balance cannot be negative")
        self.owner = owner
        self._balance = float(balance)  # leading underscore: internal by convention

    @property
    def balance(self) -> float:
        # No setter, so `account.balance = 5` raises AttributeError.
        return self._balance

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("withdrawal must be positive")
        if amount > self._balance:
            raise ValueError("insufficient funds")
        self._balance -= amount
        return self._balance

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BankAccount":
        # `cls` (not BankAccount) so a subclass calling from_dict gets a subclass instance.
        return cls(data["owner"], data.get("balance", 0.0))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(owner={self.owner!r}, balance={self._balance!r})"


class Temperature:
    ABSOLUTE_ZERO = -273.15

    def __init__(self, celsius: float = 0.0) -> None:
        self.celsius = celsius  # goes through the setter, so it is validated too

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < self.ABSOLUTE_ZERO:
            raise ValueError(f"{value} is below absolute zero")
        self._celsius = float(value)

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        self.celsius = (value - 32) * 5 / 9


@functools.total_ordering
class Money:
    def __init__(self, cents: int, currency: str) -> None:
        self.cents = cents
        self.currency = currency

    def _key(self) -> tuple[int, str]:
        return (self.cents, self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented  # let Python try the other side, then fall back to identity
        return self._key() == other._key()

    def __hash__(self) -> int:
        # Defining __eq__ sets __hash__ to None; hash the same fields eq compares.
        return hash(self._key())

    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"cannot mix {self.currency} and {other.currency}")

    def __lt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self.cents < other.cents

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self.cents + other.cents, self.currency)

    def __repr__(self) -> str:
        return f"Money({self.cents!r}, {self.currency!r})"

    def __str__(self) -> str:
        return f"{self.cents / 100:.2f} {self.currency}"


class Playlist:
    def __init__(self, name: str, songs: list[str] | None = None) -> None:
        self.name = name
        self._songs = list(songs) if songs is not None else []  # own copy, never shared

    def add(self, song: str) -> None:
        self._songs.append(song)

    def __len__(self) -> int:
        return len(self._songs)

    def __iter__(self) -> Iterator[str]:
        return iter(self._songs)

    def __getitem__(self, index: int | slice) -> str | list[str]:
        return self._songs[index]  # list handles both ints and slices

    def __contains__(self, song: object) -> bool:
        if not isinstance(song, str):
            return False
        target = song.casefold()
        return any(s.casefold() == target for s in self._songs)


class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """Subclasses must implement this."""

    def describe(self) -> str:
        return f"{type(self).__name__} with area {self.area():.2f}"


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius**2


class CallCounter:
    def __init__(self, func: Callable[..., Any]) -> None:
        functools.update_wrapper(self, func)  # copies __name__, __doc__, __wrapped__
        self.func = func
        self.calls = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        return self.func(*args, **kwargs)
