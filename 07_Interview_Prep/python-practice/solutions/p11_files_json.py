"""Reference solutions: Files, JSON & Data I/O."""
import csv
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any


def count_matching_lines(path: Path, needle: str) -> int:
    count = 0
    # Iterating the file object reads one line at a time: memory stays flat.
    with open(path, encoding="utf-8") as f:
        for line in f:
            if needle in line:
                count += 1
    return count


def find_files(root: Path, suffix: str) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob(f"*{suffix}")
        if p.is_file()
    )


def _json_default(obj: Any) -> Any:
    # json.dumps calls this only for objects it cannot serialize itself.
    if isinstance(obj, (datetime, date)):  # datetime is a subclass of date
        return obj.isoformat()
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def to_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=_json_default)


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    # Never use bool(raw): bool("false") is True because the string is non-empty.
    raise ValueError(f"{name} must be a boolean, got {raw!r}")


def clean_users_csv(src: Path, dst: Path) -> int:
    fields = ["name", "email", "age"]
    written = 0
    # newline="" lets the csv module handle line endings and quoted newlines itself.
    with open(src, newline="", encoding="utf-8") as fin, open(dst, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin, skipinitialspace=True)
        writer = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()
        for row in reader:
            email = (row.get("email") or "").strip().lower()
            if not email:
                continue
            age = (row.get("age") or "").strip()
            writer.writerow({
                "name": (row.get("name") or "").strip(),
                "email": email,
                "age": int(age) if age else "",
            })
            written += 1
    return written


def atomic_write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Same folder as the target, so os.replace is a rename on one filesystem (atomic).
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # make sure the bytes reached the disk
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
