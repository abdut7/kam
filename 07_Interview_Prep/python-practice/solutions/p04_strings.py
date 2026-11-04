"""Reference solutions: strings and text."""
import re
import unicodedata

# Compiled once at import time and reused on every call.
LOG_LINE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2}) "
    r"(?P<time>\d{2}:\d{2}:\d{2}) "
    r"(?P<level>[A-Z]+) "
    r"\[(?P<service>[\w-]+)\] "
    r"(?P<message>.*)"
)


def reverse_words(sentence: str) -> str:
    # split() with no argument splits on runs of whitespace and drops empty pieces,
    # so leading, trailing and doubled spaces disappear for free.
    return " ".join(sentence.split()[::-1])


def is_palindrome(text: str) -> bool:
    # Keep letters and digits only; casefold() is the Unicode-aware lower().
    cleaned = "".join(ch.casefold() for ch in text if ch.isalnum())
    return cleaned == cleaned[::-1]


def mask_secret(token: str, visible: int = 4) -> str:
    if len(token) <= visible:
        return "*" * len(token)
    # Do not write token[-visible:]: when visible is 0, token[-0:] is the WHOLE string.
    cut = len(token) - visible
    return "*" * cut + token[cut:]


def format_price(amount: float, currency: str = "INR") -> str:
    # "," adds a thousands separator, ".2f" fixes two decimals.
    return f"{currency} {amount:,.2f}"


def slugify(title: str) -> str:
    # NFKD splits "é" into "e" + a combining accent; encoding to ASCII with
    # errors="ignore" then drops the accent and keeps the "e".
    ascii_text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    # Any run of characters that is not a lowercase letter or digit becomes one hyphen.
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower())
    return slug.strip("-")


def parse_log_line(line: str) -> dict[str, str] | None:
    match = LOG_LINE.fullmatch(line.strip())
    return match.groupdict() if match else None
