"""Reference solutions: control flow."""
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def classify_status(code: int) -> str:
    # Chained comparisons read like maths: 200 <= code < 300.
    if 100 <= code < 200:
        return "informational"
    elif 200 <= code < 300:
        return "success"
    elif 300 <= code < 400:
        return "redirect"
    elif 400 <= code < 500:
        return "client_error"
    elif 500 <= code < 600:
        return "server_error"
    else:
        return "unknown"


def find_first_over(values: list[float], limit: float) -> int | None:
    for index, value in enumerate(values):
        if value > limit:
            found = index
            break
    else:
        # Runs only when the loop finished without hitting break.
        found = None
    return found


def pair_up(names: list[str], scores: list[int]) -> list[str]:
    # strict=True (3.10+) raises ValueError instead of silently dropping the extras.
    return [f"{name}: {score}" for name, score in zip(names, scores, strict=True)]


def call_with_retries(fn: Callable[[], T], attempts: int) -> T:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    last_error: ConnectionError | None = None
    for _ in range(attempts):
        try:
            result = fn()
            break
        except ConnectionError as exc:
            last_error = exc
    else:
        # Every attempt failed: the loop never reached break.
        assert last_error is not None
        raise last_error
    return result


def parse_command(text: str) -> tuple:
    match text.lower().split():
        case []:
            return ("noop",)
        case ["quit" | "exit"]:
            return ("quit",)
        case ["go", direction]:
            return ("move", direction)
        case ["pick", "up", item]:
            return ("take", item)
        case ["drop", *items] if items:
            return ("drop", items)
        case _:
            return ("error", text)


def route_event(event: dict) -> str:
    match event:
        case {"type": "message", "text": str(text)} if text.strip():
            return f"reply:{text.strip()}"
        case {"type": "tool_call", "name": str(name), "args": dict()}:
            return f"run:{name}"
        case {"type": "payment", "amount": int() | float() as amount} if amount > 10_000:
            return "review"
        case {"type": "payment", "amount": int() | float()}:
            return "approve"
        case _:
            return "ignore"
