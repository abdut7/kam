"""Reference solutions: modules, imports and a tour of the standard library."""
import importlib
import itertools
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

# Compiled once, when the module is first imported (module code runs once per process).
TICKET_RE = re.compile(r"\b[A-Z]{2,10}-\d+\b")


def weekday_name(iso_date: str) -> str:
    """Return the English weekday name for an ISO date string (YYYY-MM-DD).

    Raise ValueError for an invalid date.
    Example: weekday_name("2026-11-02") == "Monday"
    """
    # fromisoformat raises ValueError on bad input, which is exactly what we want.
    return date.fromisoformat(iso_date).strftime("%A")


def filter_by_suffix(paths: list[str], suffix: str) -> list[str]:
    """Return the file names (not full paths) whose suffix matches, case-insensitively, sorted.

    `suffix` includes the dot, like ".py".
    Example: filter_by_suffix(["src/app.py", "README.md", "tests/Test_App.PY"], ".py")
             == ["Test_App.PY", "app.py"]
    """
    wanted = suffix.lower()
    return sorted(Path(p).name for p in paths if Path(p).suffix.lower() == wanted)


def run_lengths(text: str) -> list[tuple[str, int]]:
    """Run-length encode a string with itertools.groupby.

    Example: run_lengths("aaabcc") == [("a", 3), ("b", 1), ("c", 2)]
    """
    # groupby groups CONSECUTIVE equal items, which is exactly run-length encoding.
    return [(char, len(list(group))) for char, group in itertools.groupby(text)]


def parse_json_lines(text: str) -> list[dict]:
    """Parse JSON Lines text (one JSON object per line), skipping blank lines.

    On invalid JSON raise ValueError whose message contains "line N" (1-based).
    Example: parse_json_lines('{"a": 1}\\n\\n{"b": 2}') == [{"a": 1}, {"b": 2}]
    """
    records: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:  # JSONDecodeError is a subclass of ValueError
            raise ValueError(f"invalid JSON on line {number}: {exc.msg}") from exc
    return records


def extract_ticket_ids(text: str) -> list[str]:
    """Return ticket ids like "API-42" (2 to 10 capital letters, a dash, digits).

    Keep the order of first appearance and drop duplicates.
    Example: extract_ticket_ids("Fixes API-42 and WEB-7, see API-42") == ["API-42", "WEB-7"]
    """
    # dict.fromkeys de-duplicates while keeping insertion order.
    return list(dict.fromkeys(TICKET_RE.findall(text)))


def load_object(spec: str) -> Any:
    """Import an object from a "module:attribute" string, like uvicorn's "main:app".

    The attribute part may be dotted ("os.path:join" or "collections:OrderedDict.fromkeys").
    Raise ValueError if there is no colon. Let ImportError and AttributeError propagate.
    Example: load_object("json:dumps") is json.dumps
    """
    module_name, sep, attr_path = spec.partition(":")
    if not sep or not module_name or not attr_path:
        raise ValueError(f"expected 'module:attribute', got {spec!r}")
    obj: Any = importlib.import_module(module_name)  # cached in sys.modules after first import
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj
