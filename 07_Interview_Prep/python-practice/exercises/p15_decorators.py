"""Lesson: Decorators & Context Managers.

Implement each function and class, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p15_decorators.py
"""
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any


def shout(func: Callable[..., str]) -> Callable[..., str]:
    """Decorator: call func with any arguments and return its result uppercased.
    Keep the original __name__ and __doc__ (use functools.wraps).

    Example:
        @shout
        def greet(name): return f"hi {name}"
        greet("asha") -> "HI ASHA"; greet.__name__ -> "greet"
    """
    raise NotImplementedError


def count_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: count how many times the function is called.
    The wrapper has a `calls` attribute that starts at 0 and goes up by one per
    call, even when the call raises. Keep the original __name__.

    Example: after calling a decorated add(1, 2) twice, add.calls -> 2
    """
    raise NotImplementedError


class Timer:
    """Context manager that measures how long its block took.

    - __enter__ records time.perf_counter() and returns self.
    - __exit__ stores the duration in seconds in `self.elapsed` (a float) and
      returns False so exceptions from the block are NOT swallowed.
    - `elapsed` is None before the block finishes.

    Example:
        with Timer() as t:
            time.sleep(0.01)
        t.elapsed >= 0.01 -> True
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def __enter__(self) -> "Timer":
        raise NotImplementedError

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        raise NotImplementedError


def retry(times: int, exceptions: tuple[type[BaseException], ...] = (Exception,)) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory: @retry(times=3) runs the function up to `times` attempts.

    - Retry only when the raised exception is an instance of one of `exceptions`;
      any other exception propagates at once.
    - If every attempt fails, re-raise the last exception.
    - Raise ValueError when retry() is called with times < 1.
    - Keep the original __name__. (No sleeping, to keep the tests fast.)

    Example: a function that fails twice with ConnectionError and then returns
    "ok" gives "ok" under @retry(times=3, exceptions=(ConnectionError,)).
    """
    raise NotImplementedError


class Router:
    """A tiny version of how FastAPI's @app.get registers routes.

    - self.routes is a dict mapping (method, path) -> handler function.
    - get(path) and post(path) return a decorator that registers the handler
      and returns the SAME function unchanged (so it can still be called directly).
    - dispatch(method, path, **kwargs) calls the registered handler with kwargs,
      or raises LookupError if nothing is registered.

    Example:
        router = Router()
        @router.get("/health")
        def health(): return {"ok": True}
        router.dispatch("GET", "/health") -> {"ok": True}
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        raise NotImplementedError

    def post(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        raise NotImplementedError

    def dispatch(self, method: str, path: str, **kwargs: Any) -> Any:
        raise NotImplementedError


@contextmanager
def temp_env(**values: str) -> Iterator[None]:
    """Context manager (a generator under @contextmanager): set os.environ[key] = value
    for each keyword, then restore the previous state on exit, even when the block
    raises. Keys that did not exist before must be removed again.

    Example:
        with temp_env(APP_MODE="test"):
            os.environ["APP_MODE"] -> "test"
        "APP_MODE" in os.environ -> back to what it was before
    """
    raise NotImplementedError
    yield  # keeps this a generator function; remove when you implement it
