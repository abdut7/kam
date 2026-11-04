"""Lesson 1 reference solutions: Python for JavaScript developers."""


def active_names(users: list[dict]) -> list[str]:
    # A list comprehension is filter + map in one expression.
    # .get() returns None for a missing key instead of raising KeyError, and None is falsy.
    return [u["name"].upper() for u in users if u.get("active")]


def describe_pages(total_items: int, page_size: int) -> str:
    if page_size <= 0 or total_items < 0:
        raise ValueError("page_size must be positive and total_items non-negative")
    # Ceiling division with ints only: floor division of the negated value, negated back.
    # (total_items + page_size - 1) // page_size gives the same answer.
    pages = -(-total_items // page_size)
    return f"{total_items} items across {pages} pages of {page_size}"


def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    # Default values are evaluated once, when `def` runs, so a [] default would be shared.
    # None is the standard sentinel: create the list inside the call instead.
    if tags is None:
        tags = []
    tags.append(tag)
    return tags


def merge_settings(defaults: dict, overrides: dict) -> dict:
    # {**a, **b} is the spread equivalent and always builds a new dict.
    # `is not None` keeps falsy but meaningful values like 0 and "".
    return {**defaults, **{k: v for k, v in overrides.items() if v is not None}}


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    text = value.strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    # bool("false") would be True: any non-empty string is truthy, so parse explicitly.
    raise ValueError(f"not a boolean: {value!r}")


class Cart:
    def __init__(self) -> None:
        # Attributes are created by assigning to self; there are no field declarations.
        # The leading underscore says "internal", by convention only.
        self._prices: dict[str, float] = {}
        self._qty: dict[str, int] = {}

    def add(self, name: str, price: float, qty: int = 1) -> None:
        if qty < 1 or price < 0:
            raise ValueError("qty must be >= 1 and price >= 0")
        self._prices.setdefault(name, price)  # keeps the first price
        self._qty[name] = self._qty.get(name, 0) + qty

    def total(self) -> float:
        return sum(self._prices[name] * qty for name, qty in self._qty.items())

    @property
    def count(self) -> int:
        # A property is read like an attribute (cart.count) but computed on access.
        return sum(self._qty.values())
