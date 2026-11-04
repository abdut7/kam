"""Lesson: Files, JSON & Data I/O.

Implement each function, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p11_files_json.py
"""
from pathlib import Path
from typing import Any


def count_matching_lines(path: Path, needle: str) -> int:
    """Count lines in a UTF-8 text file that contain `needle`.

    Stream the file line by line (never read it all into memory), so it works
    for a 20 GB log as well as a 2 KB one.

    Example: a file with "ERROR a\\nINFO b\\nERROR c\\n" and needle "ERROR" -> 2
    """
    raise NotImplementedError


def find_files(root: Path, suffix: str) -> list[str]:
    """Return every file under `root` (recursively) whose name ends with
    `suffix`, as sorted POSIX-style paths relative to root.

    Example: root has a.json and sub/b.json -> ["a.json", "sub/b.json"]
    """
    raise NotImplementedError


def to_json(data: Any) -> str:
    """Serialize data with json.dumps using indent=2, sort_keys=True and
    ensure_ascii=False. Support these extra types through `default=`:
    datetime and date -> ISO 8601 string, set -> sorted list.
    Any other unsupported type must still raise TypeError.

    Example: to_json({"at": date(2026, 11, 2)}) -> '{\\n  "at": "2026-11-02"\\n}'
    """
    raise NotImplementedError


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean from an environment variable.

    Unset -> default. "1", "true", "yes", "on" -> True and "0", "false", "no",
    "off" -> False (case-insensitive, surrounding spaces ignored).
    Anything else -> raise ValueError naming the variable.

    Example: with DEBUG=False in the environment, env_bool("DEBUG") -> False
    """
    raise NotImplementedError


def clean_users_csv(src: Path, dst: Path) -> int:
    """Read a users CSV (header: name,email,age) with csv.DictReader and write a
    cleaned CSV to dst with csv.DictWriter, same three columns in that order.

    Cleaning rules: strip spaces from every value, lowercase the email,
    skip rows whose email is empty, convert age to int (an empty age is written
    as an empty cell). Return the number of data rows written.

    Example: " Asha ,ASHA@X.COM, 31" -> "Asha,asha@x.com,31"
    """
    raise NotImplementedError


def atomic_write_json(path: Path, data: Any) -> None:
    """Write data as JSON (indent=2) to `path` so a crash never leaves a
    half-written file: create the parent folders, write to a temporary file in
    the same folder, then swap it into place with os.replace. Leave no
    temporary file behind, even if serialization fails.

    Example: atomic_write_json(tmp / "state" / "run.json", {"step": 3})
    """
    raise NotImplementedError
