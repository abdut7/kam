"""Reference solutions: Pythonic Idioms."""
from collections import Counter, defaultdict
from operator import itemgetter
from pathlib import Path
from typing import Any


def safe_int(value: Any, default: int = 0) -> int:
    # EAFP: just try it, and handle the specific failures.
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def index_of_max(values: list[float]) -> int | None:
    if not values:  # truthiness: an empty list is falsy
        return None
    # max keeps the first maximum on ties; itemgetter(1) compares the values.
    index, _ = max(enumerate(values), key=itemgetter(1))
    return index


def merge_settings(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    # "is not None", not truthiness: 0, "" and False are legitimate overrides.
    # The | operator (3.9+) builds a new dict and leaves both inputs alone.
    return defaults | {key: value for key, value in overrides.items() if value is not None}


def word_frequencies(text: str, top: int) -> list[tuple[str, int]]:
    words = (word.strip(".,!?;:\"'") for word in text.lower().split())
    return Counter(word for word in words if word).most_common(top)


def rank_users(users: list[dict[str, Any]]) -> list[str]:
    # sorted() returns a new list; a tuple key sorts by several fields,
    # and negating the score flips just that field to descending.
    ranked = sorted(users, key=lambda u: (-u["score"], u["name"].lower()))
    return [user["name"] for user in ranked]


def files_by_suffix(root: Path, suffix: str) -> dict[str, list[str]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() == suffix.lower():
            folder = path.parent.relative_to(root).as_posix()  # "." for root itself
            groups[folder].append(path.name)
    return {folder: sorted(names) for folder, names in sorted(groups.items())}
