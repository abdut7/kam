import pytest

from practice_target import load

m = load("p08_functions")


def test_append_item_no_shared_default():
    assert m.append_item(1) == [1]
    assert m.append_item(2) == [2]  # fails if the default list is shared
    existing = [0]
    assert m.append_item(3, existing) is existing
    assert existing == [0, 3]


def test_make_counter():
    c = m.make_counter()
    assert [c(), c(), c()] == [1, 2, 3]
    other = m.make_counter(10)
    assert other() == 11
    assert c() == 4  # counters do not share state


def test_build_url():
    assert (
        m.build_url("api.example.com", "v1", "users", page="2", limit="10")
        == "https://api.example.com/v1/users?page=2&limit=10"
    )
    assert m.build_url("localhost:8000", secure=False) == "http://localhost:8000"
    with pytest.raises(TypeError):
        m.build_url(host="api.example.com")  # host is positional-only
    assert m.build_url("h", "a", "b") == "https://h/a/b"
    assert m.build_url("h", q="x y") == "https://h?q=x y"  # no encoding required


def test_make_multipliers():
    fs = m.make_multipliers(3)
    assert [f(10) for f in fs] == [0, 10, 20]
    assert m.make_multipliers(0) == []
    assert m.make_multipliers(5)[4](2) == 8


def test_compose():
    assert m.compose(str, abs)(-5) == "5"
    assert m.compose(lambda x: x + 1, lambda x: x * 2)(3) == 7  # (3 * 2) + 1
    assert m.compose()("same") == "same"


def test_flatten():
    assert m.flatten([1, [2, [3, [4]]], 5]) == [1, 2, 3, 4, 5]
    assert m.flatten([]) == []
    assert m.flatten([[], [[]]]) == []
    assert m.flatten(["ab", (1, 2), [None]]) == ["ab", (1, 2), None]
