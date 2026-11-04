"""Lesson 20 reference solutions: Testing Python with pytest."""
import os
import re
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol

DEFAULT_BASE_URL = "https://api.example.com"


def now() -> float:
    """Current time in seconds. Tests patch this helper."""
    return time.time()


def get_api_base_url() -> str:
    # os.environ.get never raises; "" and a missing variable both fall back.
    value = os.environ.get("API_BASE_URL", "").strip()
    return (value or DEFAULT_BASE_URL).rstrip("/")


def is_expired(created_at: float, ttl_seconds: float) -> bool:
    # now() is looked up in this module's globals at call time, which is
    # exactly what patch.object(module, "now") and monkeypatch.setattr replace.
    return now() - created_at >= ttl_seconds


def read_config(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")  # splits on the first "=" only
        if not sep:
            continue
        result[key.strip()] = value.strip()
    return result


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


def summarize(text: str, client: LLMClient) -> str:
    if not text.strip():
        return ""  # do not pay for an LLM call on empty input
    return client.complete(f"Summarize: {text}").strip()


# Every group is optional, so the empty string matches too: check for it first.
_DURATION = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(text: str) -> int:
    match = _DURATION.fullmatch(text)
    if not text or match is None:
        raise ValueError(f"invalid duration: {text!r}")
    hours, minutes, seconds = (int(group) if group else 0 for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds


async def call_with_retry(fn: Callable[[], Awaitable[Any]], attempts: int = 3) -> Any:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    last_error: TimeoutError | None = None
    for _ in range(attempts):
        try:
            return await fn()
        except TimeoutError as exc:  # asyncio.TimeoutError is this class since 3.11
            last_error = exc
            # Real code would await asyncio.sleep(backoff) here; tests patch it.
    assert last_error is not None
    raise last_error
