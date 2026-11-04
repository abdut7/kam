"""Reference solutions: Decorators & Context Managers."""
import functools
import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any


def shout(func: Callable[..., str]) -> Callable[..., str]:
    @functools.wraps(func)  # copies __name__, __doc__, __wrapped__ and more
    def wrapper(*args: Any, **kwargs: Any) -> str:
        return func(*args, **kwargs).upper()

    return wrapper


def count_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        wrapper.calls += 1  # functions are objects, so they can hold attributes
        return func(*args, **kwargs)

    wrapper.calls = 0
    return wrapper


class Timer:
    def __init__(self) -> None:
        self.elapsed: float | None = None
        self._start = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self  # this is what "as t" receives

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self.elapsed = time.perf_counter() - self._start
        return False  # False (or None) lets any exception propagate


def retry(times: int, exceptions: tuple[type[BaseException], ...] = (Exception,)) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    if times < 1:
        raise ValueError("times must be >= 1")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise  # bare raise keeps the original traceback
                    # production code would sleep here: backoff * 2 ** attempt + jitter
            raise AssertionError("unreachable")

        return wrapper

    return decorator


class Router:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], Callable[..., Any]] = {}

    def _register(self, method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes[(method, path)] = func
            return func  # registration only: the function itself is unchanged

        return decorator

    def get(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("GET", path)

    def post(self, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._register("POST", path)

    def dispatch(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            handler = self.routes[(method, path)]
        except KeyError:
            raise LookupError(f"no route for {method} {path}") from None
        return handler(**kwargs)


_MISSING = object()


@contextmanager
def temp_env(**values: str) -> Iterator[None]:
    saved = {key: os.environ.get(key, _MISSING) for key in values}
    os.environ.update(values)
    try:
        yield  # the with-block runs here
    finally:  # runs on success, on exceptions, and on early return
        for key, old in saved.items():
            if old is _MISSING:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
