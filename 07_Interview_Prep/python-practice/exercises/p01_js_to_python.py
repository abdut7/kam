"""Lesson 1: Python for JavaScript developers.

Replace each `raise NotImplementedError` with your code, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p01_js_to_python.py
"""


def active_names(users: list[dict]) -> list[str]:
    """Return the upper-cased names of users whose "active" value is truthy, in order.

    JavaScript version: users.filter(u => u.active).map(u => u.name.toUpperCase())
    A user dict may have no "active" key at all; treat that user as inactive.

    Example: active_names([{"name": "ada", "active": True}, {"name": "bob"}]) == ["ADA"]
    """
    raise NotImplementedError


def describe_pages(total_items: int, page_size: int) -> str:
    """Describe how many pages a list needs, using integer math only (no floats, no math.ceil).

    Return "<total_items> items across <pages> pages of <page_size>".
    Raise ValueError if page_size is not positive or total_items is negative.

    Example: describe_pages(37, 10) == "37 items across 4 pages of 10"
    """
    raise NotImplementedError


def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    """Append tag to tags and return that list. Without tags, start a fresh list on every call.

    The buggy version is `def add_tag(tag, tags=[])`, which shares one list across calls.
    Yours must not. When a list is passed in, append to it and return the same list.

    Example: add_tag("a") == ["a"], then add_tag("b") == ["b"] (not ["a", "b"])
    """
    raise NotImplementedError


def merge_settings(defaults: dict, overrides: dict) -> dict:
    """Return a new dict: defaults updated with overrides, skipping override values that are None.

    JavaScript idea: { ...defaults, ...overrides } but a null override must not wipe a default.
    Falsy values such as 0 or "" still override. Neither input dict may be changed.

    Example: merge_settings({"model": "small", "temperature": 0.2}, {"temperature": 0, "model": None})
             == {"model": "small", "temperature": 0}
    """
    raise NotImplementedError


def parse_bool(value: str | None, default: bool = False) -> bool:
    """Turn an environment-variable string into a bool.

    "1", "true", "yes", "on" -> True. "0", "false", "no", "off", "" -> False.
    Case-insensitive, surrounding spaces ignored. None (variable not set) -> default.
    Anything else raises ValueError.

    Example: parse_bool("False") is False; parse_bool(None, default=True) is True
    """
    raise NotImplementedError


class Cart:
    """A tiny shopping cart, translated from a JavaScript class.

    - Cart() starts empty.
    - add(name, price, qty=1) adds qty units. Adding a name that is already in the cart
      increases its qty and keeps the price from the first add.
      Raise ValueError if qty < 1 or price < 0.
    - total() returns the sum of price * qty over all items (0 for an empty cart).
    - count is a read-only property: the total number of units in the cart.
    - add must keep working when passed around as a callback: handler = cart.add; handler("pen", 2.5)

    Example: c = Cart(); c.add("pen", 2.5, qty=2); c.total() == 5.0; c.count == 2
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def add(self, name: str, price: float, qty: int = 1) -> None:
        raise NotImplementedError

    def total(self) -> float:
        raise NotImplementedError

    @property
    def count(self) -> int:
        raise NotImplementedError
