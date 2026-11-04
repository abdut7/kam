"""Practice: dicts, sets and the collections module.

Replace each `raise NotImplementedError` with your code, then run:
    uv run --with pytest pytest tests/test_p07_dicts_sets.py
"""
from collections import Counter, defaultdict  # noqa: F401  (you will likely need these)


def first_repeat(items: list[str]) -> str | None:
    """Return the first item that appears a second time, or None if all are unique.

    Use a set for O(1) membership checks.
    Example: first_repeat(["a", "b", "c", "b", "a"]) == "b"
    """
    raise NotImplementedError


def invert(mapping: dict[str, str]) -> dict[str, list[str]]:
    """Group the keys of `mapping` by their value, keeping the original key order.

    Return a plain dict (not a defaultdict).
    Example: invert({"a": "x", "b": "y", "c": "x"}) == {"x": ["a", "c"], "y": ["b"]}
    """
    raise NotImplementedError


def set_report(a: list[str], b: list[str]) -> dict[str, set[str]]:
    """Compare two lists as sets.

    Return a dict with keys "both", "only_a", "only_b" and "either_not_both".
    Example: set_report(["x", "y"], ["y", "z"]) == {
        "both": {"y"}, "only_a": {"x"}, "only_b": {"z"}, "either_not_both": {"x", "z"}}
    """
    raise NotImplementedError


def top_k_words(text: str, k: int) -> list[tuple[str, int]]:
    """Return the k most common lowercase words with their counts.

    Words are split on whitespace. Ties keep the order in which words first appeared.
    Example: top_k_words("the cat and the hat", 2) == [("the", 2), ("cat", 1)]
    """
    raise NotImplementedError


def deep_merge(base: dict, override: dict) -> dict:
    """Merge `override` into `base` recursively and return a NEW dict.

    When both sides hold a dict under the same key, merge those dicts too;
    otherwise the value from `override` wins. Neither input is mutated.
    Example: deep_merge({"db": {"host": "a", "port": 5432}}, {"db": {"host": "b"}})
             == {"db": {"host": "b", "port": 5432}}
    """
    raise NotImplementedError


class LRUCache:
    """A least-recently-used cache holding at most `capacity` items.

    get(key) returns the value or None and marks the key as recently used.
    put(key, value) inserts or updates; when over capacity, evict the least recently used key.
    Hint: a plain dict remembers insertion order (or use collections.OrderedDict).
    Example:
        c = LRUCache(2); c.put("a", 1); c.put("b", 2); c.get("a"); c.put("c", 3)
        c.get("b") is None   # "b" was the least recently used, so it was evicted
    """

    def __init__(self, capacity: int) -> None:
        raise NotImplementedError

    def get(self, key: str) -> int | None:
        raise NotImplementedError

    def put(self, key: str, value: int) -> None:
        raise NotImplementedError
