"""Reference solutions: Errors & Exceptions."""
import json
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def safe_int(text: str | None, default: int = 0) -> int:
    # int("abc") raises ValueError; int(None) raises TypeError. Catch exactly those.
    try:
        return int(text)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return default


def get_nested(data: Any, *keys: Any, default: Any = None) -> Any:
    # EAFP: just try the lookups instead of checking each level first.
    try:
        for key in keys:
            data = data[key]
    except (KeyError, IndexError, TypeError):
        # KeyError: missing dict key, IndexError: list too short,
        # TypeError: indexing None, an int, or a list with a str key.
        return default
    return data


class InsufficientFundsError(Exception):
    def __init__(self, balance: float, amount: float) -> None:
        super().__init__(f"cannot withdraw {amount}, balance is {balance}")
        self.balance = balance
        self.amount = amount


def withdraw(balance: float, amount: float) -> float:
    if amount <= 0:
        raise ValueError(f"amount must be positive, got {amount}")
    if amount > balance:
        raise InsufficientFundsError(balance, amount)
    return balance - amount


class ConfigError(Exception):
    """Raised for any problem with a config document. (Given, do not change.)"""


def parse_config(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        # `from exc` sets __cause__, so the traceback shows the original parse error.
        raise ConfigError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config must be a JSON object")
    if "name" not in data:
        raise ConfigError('config is missing "name"')
    return data


def retry(
    func: Callable[[], T],
    attempts: int = 3,
    retry_on: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError),
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except retry_on:
            if attempt == attempts:
                raise  # bare raise keeps the original traceback
            # A real client would sleep with backoff and jitter here.
    raise AssertionError("unreachable")


def run_all(funcs: list[Callable[[], T]]) -> list[T]:
    results: list[T] = []
    errors: list[Exception] = []
    for func in funcs:
        try:
            results.append(func())
        except Exception as exc:  # collect, do not stop at the first failure
            errors.append(exc)
    if errors:
        raise ExceptionGroup(f"{len(errors)} of {len(funcs)} calls failed", errors)
    return results
