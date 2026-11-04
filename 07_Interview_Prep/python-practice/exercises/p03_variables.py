"""Lesson 3: variables, types and operators.

Replace each `raise NotImplementedError` with your code, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p03_variables.py
"""

from decimal import Decimal


def page_limit(raw: int | None, default: int = 20, maximum: int = 100) -> int:
    """Return the page size to use for an API query.

    None gives default. Any int is clamped into 0..maximum. 0 is valid ("count only") and
    must stay 0, so `raw or default` is the wrong tool here.

    Example: page_limit(None) == 20; page_limit(0) == 0; page_limit(500) == 100
    """
    raise NotImplementedError


def validate_quantity(value: object) -> int:
    """Return value if it is a real int between 1 and 99 inclusive.

    Raise TypeError for anything that is not an int, including True and False
    (bool is a subclass of int, so isinstance(True, int) is True).
    Raise ValueError for ints outside 1..99. Use a chained comparison.

    Example: validate_quantity(3) == 3; validate_quantity(True) raises TypeError
    """
    raise NotImplementedError


def clone_with_tag(doc: dict, tag: str) -> dict:
    """Return a copy of doc with tag appended to its "tags" list. doc itself must not change.

    "tags" may be missing; then the copy gets [tag]. Nested values (lists, dicts) must not be
    shared with the original, so a shallow copy is not enough.

    Example: d = {"id": 1, "tags": ["a"]}; clone_with_tag(d, "b") == {"id": 1, "tags": ["a", "b"]}
             and d["tags"] is still ["a"]
    """
    raise NotImplementedError


def to_number(text: str) -> int | float:
    """Convert user input to an int when it is a whole number, otherwise to a float.

    Surrounding spaces are ignored. "42" and "-7" give ints; "3.5" and "1e3" give floats.
    Raise ValueError for text that is not a number, and for "nan", "inf" and other
    non-finite values.

    Example: to_number(" 42 ") == 42 (an int); to_number("2.50") == 2.5
    """
    raise NotImplementedError


def sum_money(amounts: list[str]) -> Decimal:
    """Add money amounts given as strings exactly, then round to cents (half up).

    Build decimal.Decimal values from the strings, never from floats.
    An empty list gives Decimal("0.00").

    Example: sum_money(["0.10", "0.20"]) == Decimal("0.30"); sum_money(["1.005"]) == Decimal("1.01")
    """
    raise NotImplementedError
