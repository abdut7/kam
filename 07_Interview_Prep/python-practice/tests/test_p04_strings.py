from practice_target import load

m = load("p04_strings")


def test_reverse_words():
    assert m.reverse_words("  hello   big world ") == "world big hello"
    assert m.reverse_words("one") == "one"
    assert m.reverse_words("a\tb\nc") == "c b a"
    assert m.reverse_words("   ") == ""


def test_is_palindrome():
    assert m.is_palindrome("A man, a plan, a canal: Panama") is True
    assert m.is_palindrome("race a car") is False
    assert m.is_palindrome("No 'x' in Nixon") is True
    assert m.is_palindrome("") is True


def test_mask_secret():
    assert m.mask_secret("sk-live-12345678") == "************5678"
    assert m.mask_secret("abcdef", visible=2) == "****ef"
    assert m.mask_secret("abc") == "***"
    assert m.mask_secret("secret", visible=0) == "******"


def test_format_price():
    assert m.format_price(1234567.5) == "INR 1,234,567.50"
    assert m.format_price(0) == "INR 0.00"
    assert m.format_price(999.999, "USD") == "USD 1,000.00"
    assert m.format_price(-42.1, "AED") == "AED -42.10"


def test_slugify():
    assert m.slugify("  Café Déjà Vu: 2026 Edition! ") == "cafe-deja-vu-2026-edition"
    assert m.slugify("FastAPI vs. Express") == "fastapi-vs-express"
    assert m.slugify("already-a-slug") == "already-a-slug"
    assert m.slugify("!!!") == ""


def test_parse_log_line():
    assert m.parse_log_line("2026-11-02 14:03:27 ERROR [payments] Card declined") == {
        "date": "2026-11-02",
        "time": "14:03:27",
        "level": "ERROR",
        "service": "payments",
        "message": "Card declined",
    }
    parsed = m.parse_log_line("2026-01-05 09:00:00 INFO [auth-api] user [42] logged in\n")
    assert parsed is not None
    assert parsed["service"] == "auth-api" and parsed["message"] == "user [42] logged in"
    assert m.parse_log_line("ERROR payments Card declined") is None
    assert m.parse_log_line("") is None
