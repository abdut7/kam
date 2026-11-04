"""Lesson 20: Testing Python with pytest.

The functions here are small on purpose. The real lesson is in
tests/test_p20_testing.py, which uses parametrize, pytest.raises, fixtures
(including a yield fixture), tmp_path, monkeypatch, Mock, patch and AsyncMock.
After each function passes, read the tests that check it.

Run: uv run --with pytest pytest tests/test_p20_testing.py
"""
import os
import re
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol

DEFAULT_BASE_URL = "https://api.example.com"


def now() -> float:
    """Current time in seconds. Already done: the tests patch this helper."""
    return time.time()


def get_api_base_url() -> str:
    """Return the API_BASE_URL environment variable without trailing slashes,
    or DEFAULT_BASE_URL when the variable is missing or empty.

    Example: API_BASE_URL="http://localhost:8000/" -> "http://localhost:8000"
    """
    raise NotImplementedError


def is_expired(created_at: float, ttl_seconds: float) -> bool:
    """True when at least ttl_seconds have passed since created_at.
    Call the module-level now() helper, not time.time(), so tests can patch it.

    Example: with now() returning 1000.0, is_expired(900.0, 100.0) -> True
    """
    raise NotImplementedError


def read_config(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines from a UTF-8 text file into a dict.
    Skip blank lines, lines starting with "#" and lines without "=".
    Split on the first "=" only and strip spaces around keys and values.

    Example: "A = 1\\n# note\\nURL=http://x?a=b\\n" -> {"A": "1", "URL": "http://x?a=b"}
    """
    raise NotImplementedError


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str: ...


def summarize(text: str, client: LLMClient) -> str:
    """Return client.complete("Summarize: " + text) with surrounding whitespace
    stripped. When text is empty or only whitespace, return "" and do not call
    the client at all.

    Example: summarize("long text", client) calls client.complete("Summarize: long text")
    """
    raise NotImplementedError


def parse_duration(text: str) -> int:
    """Convert durations like "1h30m", "45s" or "2h5s" into seconds.
    Units h, m and s each appear at most once, in that order, with no spaces.
    Raise ValueError with a message containing "invalid duration" for empty or
    malformed input such as "", "90", "1m1h" or "1h 30m".

    Example: parse_duration("1h30m") -> 5400
    """
    raise NotImplementedError


async def call_with_retry(fn: Callable[[], Awaitable[Any]], attempts: int = 3) -> Any:
    """Await fn() and return its result. If it raises TimeoutError, call it
    again, up to `attempts` calls in total, then re-raise the last TimeoutError.
    Any other exception propagates immediately, without a retry.

    Example: fn times out twice, then returns "ok" -> returns "ok" after 3 calls
    """
    raise NotImplementedError
