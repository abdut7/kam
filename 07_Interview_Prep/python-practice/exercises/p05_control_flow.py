"""Practice: control flow (if/elif, loops, for/else, zip, match/case).

Replace each `raise NotImplementedError` with your code, then run:
    uv run --with pytest pytest tests/test_p05_control_flow.py
"""
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def classify_status(code: int) -> str:
    """Classify an HTTP status code with if/elif/else and chained comparisons.

    1xx -> "informational", 2xx -> "success", 3xx -> "redirect",
    4xx -> "client_error", 5xx -> "server_error", anything else -> "unknown".
    Example: classify_status(404) == "client_error"
    """
    raise NotImplementedError


def find_first_over(values: list[float], limit: float) -> int | None:
    """Return the index of the first value strictly greater than `limit`,
    or None if there is none. Use enumerate and a for/else.

    Example: find_first_over([3, 9, 12, 15], 10) == 2
    """
    raise NotImplementedError


def pair_up(names: list[str], scores: list[int]) -> list[str]:
    """Pair each name with its score as "name: score".

    The lists must have the same length: raise ValueError if they do not
    (zip with strict=True does this for you).
    Example: pair_up(["asha", "ravi"], [91, 78]) == ["asha: 91", "ravi: 78"]
    """
    raise NotImplementedError


def call_with_retries(fn: Callable[[], T], attempts: int) -> T:
    """Call `fn()` up to `attempts` times and return the first successful result.

    Only ConnectionError triggers a retry; any other exception propagates at once.
    If every attempt raises ConnectionError, re-raise the last one.
    Raise ValueError if attempts is less than 1. Try a for/else.
    Example: a fn that fails twice then returns "ok" gives "ok" with attempts=3.
    """
    raise NotImplementedError


def parse_command(text: str) -> tuple:
    """Parse a text command with match/case sequence patterns on text.lower().split().

    ""                -> ("noop",)
    "quit" or "exit"  -> ("quit",)
    "go <dir>"        -> ("move", dir)
    "pick up <item>"  -> ("take", item)
    "drop <a> <b>..." -> ("drop", [a, b, ...])   (at least one item)
    anything else     -> ("error", text)          (the original text)
    Example: parse_command("GO North") == ("move", "north")
    """
    raise NotImplementedError


def route_event(event: dict) -> str:
    """Route an event dict by its shape with match/case mapping patterns and guards.

    {"type": "message", "text": <non-blank str>}        -> "reply:<text stripped>"
    {"type": "tool_call", "name": <str>, "args": <dict>} -> "run:<name>"
    {"type": "payment", "amount": <int or float> > 10_000} -> "review"
    {"type": "payment", "amount": <int or float>}        -> "approve"
    anything else                                         -> "ignore"
    Extra keys in the dict are allowed.
    Example: route_event({"type": "payment", "amount": 25_000}) == "review"
    """
    raise NotImplementedError
