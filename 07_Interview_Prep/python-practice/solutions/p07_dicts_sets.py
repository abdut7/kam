"""Reference solutions: dicts, sets and the collections module."""
from collections import Counter, defaultdict


def first_repeat(items: list[str]) -> str | None:
    """Return the first item that appears a second time, or None if all are unique.

    Example: first_repeat(["a", "b", "c", "b", "a"]) == "b"
    """
    seen: set[str] = set()  # set membership is O(1) on average, a list would be O(n)
    for item in items:
        if item in seen:
            return item
        seen.add(item)
    return None


def invert(mapping: dict[str, str]) -> dict[str, list[str]]:
    """Group the keys of `mapping` by their value, keeping the original key order.

    Example: invert({"a": "x", "b": "y", "c": "x"}) == {"x": ["a", "c"], "y": ["b"]}
    """
    groups: defaultdict[str, list[str]] = defaultdict(list)  # missing key -> fresh []
    for key, value in mapping.items():
        groups[value].append(key)
    return dict(groups)  # hand back a plain dict so callers do not get auto-create surprises


def set_report(a: list[str], b: list[str]) -> dict[str, set[str]]:
    """Compare two lists as sets.

    Return a dict with keys "both", "only_a", "only_b" and "either_not_both".
    Example: set_report(["x", "y"], ["y", "z"]) == {
        "both": {"y"}, "only_a": {"x"}, "only_b": {"z"}, "either_not_both": {"x", "z"}}
    """
    sa, sb = set(a), set(b)
    return {
        "both": sa & sb,             # intersection
        "only_a": sa - sb,           # difference
        "only_b": sb - sa,
        "either_not_both": sa ^ sb,  # symmetric difference
    }


def top_k_words(text: str, k: int) -> list[tuple[str, int]]:
    """Return the k most common lowercase words with their counts.

    Words are split on whitespace. Ties keep the order in which words first appeared.
    Example: top_k_words("the cat and the hat", 2) == [("the", 2), ("cat", 1)]
    """
    # most_common sorts by count; equal counts keep first-seen order.
    return Counter(text.lower().split()).most_common(k)


def deep_merge(base: dict, override: dict) -> dict:
    """Merge `override` into `base` recursively and return a NEW dict.

    When both sides hold a dict under the same key, merge those dicts too;
    otherwise the value from `override` wins. Neither input is mutated.
    Example: deep_merge({"db": {"host": "a", "port": 5432}}, {"db": {"host": "b"}})
             == {"db": {"host": "b", "port": 5432}}
    """
    result = dict(base)  # shallow copy so we never write into the caller's dict
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class LRUCache:
    """A least-recently-used cache holding at most `capacity` items.

    get(key) returns the value or None and marks the key as recently used.
    put(key, value) inserts or updates; when over capacity, evict the least recently used key.
    Example:
        c = LRUCache(2); c.put("a", 1); c.put("b", 2); c.get("a"); c.put("c", 3)
        c.get("b") is None   # "b" was the least recently used, so it was evicted
    """

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        # A plain dict keeps insertion order, so the first key is the oldest.
        self._data: dict[str, int] = {}

    def get(self, key: str) -> int | None:
        if key not in self._data:
            return None
        value = self._data.pop(key)  # pop and re-insert moves the key to the end
        self._data[key] = value
        return value

    def put(self, key: str, value: int) -> None:
        self._data.pop(key, None)
        self._data[key] = value
        if len(self._data) > self.capacity:
            oldest = next(iter(self._data))  # first key in insertion order
            del self._data[oldest]
