"""Reference solutions: functions, arguments, scope and closures."""
from collections.abc import Callable
from typing import Any


def append_item(item: Any, items: list | None = None) -> list:
    """Append `item` to `items` and return the list. With no list given, start a new one.

    Each call without `items` must get its own fresh list (no shared mutable default).
    Example: append_item(1) == [1]; append_item(2) == [2]; append_item(3, [0]) == [0, 3]
    """
    if items is None:  # the None sentinel: a new list is built on every call
        items = []
    items.append(item)
    return items


def make_counter(start: int = 0) -> Callable[[], int]:
    """Return a function that returns start + 1, start + 2, ... on successive calls.

    Each counter keeps its own state.
    Example: c = make_counter(); c() == 1; c() == 2
    """
    count = start

    def counter() -> int:
        nonlocal count  # rebind the enclosing variable instead of creating a local one
        count += 1
        return count

    return counter


def build_url(host: str, /, *segments: str, secure: bool = True, **params: str) -> str:
    """Build a URL from a host, path segments, a keyword-only `secure` flag and query params.

    `host` is positional-only, `secure` is keyword-only, params keep the order they were passed.
    Example: build_url("api.example.com", "v1", "users", page="2", limit="10")
             == "https://api.example.com/v1/users?page=2&limit=10"
    """
    scheme = "https" if secure else "http"
    url = f"{scheme}://{host}"
    if segments:
        url += "/" + "/".join(segments)
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return url


def make_multipliers(n: int) -> list[Callable[[int], int]]:
    """Return n functions where the i-th function multiplies its argument by i.

    Avoid the late-binding closure trap.
    Example: fs = make_multipliers(3); [f(10) for f in fs] == [0, 10, 20]
    """
    # i=i freezes the current value as a default; a bare `lambda x: i * x`
    # would look up i when called, after the loop has finished.
    return [lambda x, i=i: i * x for i in range(n)]


def compose(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Compose functions right to left: compose(f, g)(x) == f(g(x)).

    compose() with no functions returns the identity function.
    Example: compose(str, abs)(-5) == "5"
    """

    def composed(x: Any) -> Any:
        for f in reversed(funcs):
            x = f(x)
        return x

    return composed


def flatten(nested: list) -> list:
    """Flatten arbitrarily nested lists using recursion.

    Only lists are flattened; tuples, strings and other values are kept as they are.
    Example: flatten([1, [2, [3, [4]]], 5]) == [1, 2, 3, 4, 5]
    """
    out: list = []
    for item in nested:
        if isinstance(item, list):
            out.extend(flatten(item))  # base case: an empty list adds nothing
        else:
            out.append(item)
    return out
