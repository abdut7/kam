"""Practice: strings and text.

Replace each `raise NotImplementedError` with your code, then run:
    uv run --with pytest pytest tests/test_p04_strings.py
"""
import re  # noqa: F401  (you will need these for the last two functions)
import unicodedata  # noqa: F401


def reverse_words(sentence: str) -> str:
    """Return the words of `sentence` in reverse order, joined by single spaces.

    Extra spaces, tabs and newlines between or around words are dropped.
    Example: reverse_words("  hello   big world ") == "world big hello"
    """
    raise NotImplementedError


def is_palindrome(text: str) -> bool:
    """Return True if `text` reads the same backwards, ignoring case and any
    character that is not a letter or digit. An empty string is a palindrome.

    Example: is_palindrome("A man, a plan, a canal: Panama") is True
    """
    raise NotImplementedError


def mask_secret(token: str, visible: int = 4) -> str:
    """Replace every character except the last `visible` ones with "*".

    If the token has `visible` characters or fewer, mask all of it.
    Watch out: token[-0:] is the whole string, not an empty one.
    Example: mask_secret("sk-live-12345678") == "************5678"
    """
    raise NotImplementedError


def format_price(amount: float, currency: str = "INR") -> str:
    """Format `amount` with a thousands separator and exactly two decimals,
    prefixed by the currency code and a space. Use an f-string format spec.

    Example: format_price(1234567.5) == "INR 1,234,567.50"
    """
    raise NotImplementedError


def slugify(title: str) -> str:
    """Turn a title into a URL slug: lowercase ASCII letters and digits separated
    by single hyphens, no leading or trailing hyphen. Accented letters lose their
    accent (normalise with unicodedata, NFKD form). Return "" if nothing is left.

    Example: slugify("  Café Déjà Vu: 2026 Edition! ") == "cafe-deja-vu-2026-edition"
    """
    raise NotImplementedError


def parse_log_line(line: str) -> dict[str, str] | None:
    """Parse a log line of the form
    "YYYY-MM-DD HH:MM:SS LEVEL [service] message" with a regular expression
    using named groups. Return a dict with keys date, time, level, service and
    message, or None if the line does not match. Ignore surrounding whitespace.

    Example: parse_log_line("2026-11-02 14:03:27 ERROR [payments] Card declined")
    == {"date": "2026-11-02", "time": "14:03:27", "level": "ERROR",
        "service": "payments", "message": "Card declined"}
    """
    raise NotImplementedError
