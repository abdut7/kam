from practice_target import load
import pytest

m = load("p01_js_to_python")


def test_active_names():
    users = [
        {"name": "ada", "active": True},
        {"name": "bob"},
        {"name": "cy", "active": False},
        {"name": "di", "active": 1},
    ]
    assert m.active_names(users) == ["ADA", "DI"]
    assert m.active_names([]) == []
    assert m.active_names([{"name": "x", "active": None}]) == []


def test_describe_pages():
    assert m.describe_pages(37, 10) == "37 items across 4 pages of 10"
    assert m.describe_pages(40, 10) == "40 items across 4 pages of 10"
    assert m.describe_pages(0, 10) == "0 items across 0 pages of 10"
    with pytest.raises(ValueError):
        m.describe_pages(5, 0)


def test_add_tag_does_not_share_state():
    assert m.add_tag("a") == ["a"]
    assert m.add_tag("b") == ["b"]
    existing = ["x"]
    result = m.add_tag("y", existing)
    assert result == ["x", "y"]
    assert result is existing


def test_merge_settings():
    defaults = {"model": "small", "temperature": 0.2}
    overrides = {"temperature": 0, "model": None, "top_p": 0.9}
    merged = m.merge_settings(defaults, overrides)
    assert merged == {"model": "small", "temperature": 0, "top_p": 0.9}
    assert defaults == {"model": "small", "temperature": 0.2}
    assert overrides == {"temperature": 0, "model": None, "top_p": 0.9}
    assert m.merge_settings({}, {}) == {}


def test_parse_bool():
    assert m.parse_bool(" YES ") is True
    assert m.parse_bool("False") is False
    assert m.parse_bool("0") is False
    assert m.parse_bool("") is False
    assert m.parse_bool(None) is False
    assert m.parse_bool(None, default=True) is True
    with pytest.raises(ValueError):
        m.parse_bool("maybe")


def test_cart():
    cart = m.Cart()
    assert cart.total() == 0
    assert cart.count == 0
    cart.add("pen", 2.5, qty=2)
    handler = cart.add  # bound method keeps self
    handler("pad", 1.25)
    handler("pen", 99.0)  # same name: qty grows, first price kept
    assert cart.count == 4
    assert cart.total() == 2.5 * 3 + 1.25
    with pytest.raises(ValueError):
        cart.add("bad", 1.0, qty=0)
