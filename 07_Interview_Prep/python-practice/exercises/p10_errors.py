"""Lesson: Errors & Exceptions.

Implement each function, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p10_errors.py
"""
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def safe_int(text: str | None, default: int = 0) -> int:
    """Convert text to an int. Return `default` when the text is not a valid
    integer or is None. Catch only the exceptions int() can raise here.

    Example: safe_int(" 42 ") -> 42, safe_int("4.2", -1) -> -1, safe_int(None) -> 0
    """
    raise NotImplementedError


def get_nested(data: Any, *keys: Any, default: Any = None) -> Any:
    """Follow keys (dict keys or list indexes) into nested data, EAFP style:
    try the lookups and return `default` if any step fails (missing key,
    bad index, or a value that cannot be indexed).

    Example: get_nested({"a": [{"b": 1}]}, "a", 0, "b") -> 1
             get_nested({"a": None}, "a", "b", default="x") -> "x"
    """
    raise NotImplementedError


class InsufficientFundsError(Exception):
    """Raised when a withdrawal is larger than the balance.

    Store `balance` and `amount` as attributes and pass a readable message
    to Exception.__init__ so str(err) is
    "cannot withdraw 80.0, balance is 50.0".
    """

    def __init__(self, balance: float, amount: float) -> None:
        raise NotImplementedError


def withdraw(balance: float, amount: float) -> float:
    """Return the new balance after withdrawing `amount`.

    Raise ValueError if amount <= 0, and InsufficientFundsError if
    amount > balance.

    Example: withdraw(100.0, 30.0) -> 70.0
    """
    raise NotImplementedError


class ConfigError(Exception):
    """Raised for any problem with a config document. (Given, do not change.)"""


def parse_config(text: str) -> dict[str, Any]:
    """Parse a JSON config string that must be an object with a "name" key.

    - Invalid JSON: raise ConfigError("invalid JSON: <original message>")
      chained from the json.JSONDecodeError (use `raise ... from ...`).
    - Not a dict, or no "name" key: raise ConfigError (no chaining needed).
    Return the dict on success.

    Example: parse_config('{"name": "api", "port": 8000}') -> {"name": "api", "port": 8000}
    """
    raise NotImplementedError


def retry(
    func: Callable[[], T],
    attempts: int = 3,
    retry_on: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError),
) -> T:
    """Call func() up to `attempts` times and return its first successful result.

    Only exceptions that are instances of `retry_on` trigger another attempt.
    Any other exception propagates immediately. If every attempt fails, re-raise
    the last exception. Raise ValueError if attempts < 1.

    Example: a func that raises ConnectionError twice and then returns "ok"
             -> retry(func, attempts=3) == "ok"
    """
    raise NotImplementedError


def run_all(funcs: list[Callable[[], T]]) -> list[T]:
    """Call every function, even if some fail, and return the results in order.

    If one or more raised an Exception, raise an ExceptionGroup (3.11+) whose
    message is "<failed> of <total> calls failed" and whose exceptions are the
    caught exceptions in call order.

    Example: run_all([lambda: 1, lambda: 2]) -> [1, 2]
    """
    raise NotImplementedError
