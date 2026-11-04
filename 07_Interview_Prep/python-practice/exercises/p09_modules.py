"""Practice: modules, imports and a tour of the standard library.

Replace each `raise NotImplementedError` with your code, then run:
    uv run --with pytest pytest tests/test_p09_modules.py

Every task needs only the standard library. Import what you need at the top.
"""
from typing import Any


def weekday_name(iso_date: str) -> str:
    """Return the English weekday name for an ISO date string (YYYY-MM-DD).

    Raise ValueError for an invalid date. Hint: datetime.date.fromisoformat and strftime.
    Example: weekday_name("2026-11-02") == "Monday"
    """
    raise NotImplementedError


def filter_by_suffix(paths: list[str], suffix: str) -> list[str]:
    """Return the file names (not full paths) whose suffix matches, case-insensitively, sorted.

    `suffix` includes the dot, like ".py". Hint: pathlib.Path(...).name and .suffix.
    Example: filter_by_suffix(["src/app.py", "README.md", "tests/Test_App.PY"], ".py")
             == ["Test_App.PY", "app.py"]
    """
    raise NotImplementedError


def run_lengths(text: str) -> list[tuple[str, int]]:
    """Run-length encode a string with itertools.groupby.

    Example: run_lengths("aaabcc") == [("a", 3), ("b", 1), ("c", 2)]
    """
    raise NotImplementedError


def parse_json_lines(text: str) -> list[dict]:
    """Parse JSON Lines text (one JSON object per line), skipping blank lines.

    On invalid JSON raise ValueError whose message contains "line N" (1-based).
    Example: parse_json_lines('{"a": 1}\\n\\n{"b": 2}') == [{"a": 1}, {"b": 2}]
    """
    raise NotImplementedError


def extract_ticket_ids(text: str) -> list[str]:
    """Return ticket ids like "API-42" (2 to 10 capital letters, a dash, digits).

    Keep the order of first appearance and drop duplicates. Hint: re.findall.
    Example: extract_ticket_ids("Fixes API-42 and WEB-7, see API-42") == ["API-42", "WEB-7"]
    """
    raise NotImplementedError


def load_object(spec: str) -> Any:
    """Import an object from a "module:attribute" string, like uvicorn's "main:app".

    The attribute part may be dotted ("os.path:join" or "collections:OrderedDict.fromkeys").
    Raise ValueError if there is no colon. Let ImportError and AttributeError propagate.
    Hint: importlib.import_module and getattr.
    Example: load_object("json:dumps") is json.dumps
    """
    raise NotImplementedError
