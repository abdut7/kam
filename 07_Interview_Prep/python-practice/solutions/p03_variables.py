"""Lesson 3 reference solutions: variables, types and operators."""

import copy
import math
from decimal import ROUND_HALF_UP, Decimal


def page_limit(raw: int | None, default: int = 20, maximum: int = 100) -> int:
    # `raw or default` would turn a valid 0 into 20, because 0 is falsy. Test for None instead.
    if raw is None:
        return default
    return min(max(raw, 0), maximum)


def validate_quantity(value: object) -> int:
    # Check bool first: True is an int subclass and would pass isinstance(value, int).
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"quantity must be an int, got {type(value).__name__}")
    if not 1 <= value <= 99:  # chained: 1 <= value and value <= 99
        raise ValueError(f"quantity must be between 1 and 99, got {value}")
    return value


def clone_with_tag(doc: dict, tag: str) -> dict:
    # deepcopy copies nested lists and dicts too; dict(doc) or doc.copy() would share them.
    result = copy.deepcopy(doc)
    result.setdefault("tags", []).append(tag)
    return result


def to_number(text: str) -> int | float:
    cleaned = text.strip()  # int() and float() also accept surrounding spaces, but be explicit
    try:
        return int(cleaned)
    except ValueError:
        pass
    number = float(cleaned)  # raises ValueError for text that is not a number
    if not math.isfinite(number):
        raise ValueError(f"not a finite number: {text!r}")
    return number


CENT = Decimal("0.01")


def sum_money(amounts: list[str]) -> Decimal:
    # Decimal("0.1") is exact; Decimal(0.1) would capture the float's binary error.
    total = sum((Decimal(a) for a in amounts), Decimal("0"))
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
