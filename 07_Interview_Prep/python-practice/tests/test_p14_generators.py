import itertools
import types

import pytest

from practice_target import load

m = load("p14_generators")


def test_first_match():
    assert m.first_match([1, 8, 3, 9], lambda n: n > 5) == 8
    assert m.first_match([1, 2], lambda n: n > 5) is None
    assert m.first_match([], lambda n: True, default=-1) == -1
    # stops early: works on an endless iterator
    assert m.first_match(itertools.count(1), lambda n: n % 7 == 0) == 7


def test_countdown_protocol():
    assert list(m.Countdown(3)) == [3, 2, 1]
    c = m.Countdown(2)
    assert iter(c) is c
    assert next(c) == 2 and next(c) == 1
    with pytest.raises(StopIteration):
        next(c)


def test_countdown_one_shot_and_empty():
    c = m.Countdown(2)
    assert list(c) == [2, 1]
    assert list(c) == []
    assert list(m.Countdown(0)) == []
    assert list(m.Countdown(-4)) == []


def test_clean_lines():
    out = m.clean_lines(["  a ", "", "# note", "b\n", "   #x", "c # not a comment"])
    assert isinstance(out, types.GeneratorType)
    assert list(out) == ["a", "b", "c # not a comment"]
    endless = itertools.cycle(["x", "", "# c"])
    assert list(itertools.islice(m.clean_lines(endless), 3)) == ["x", "x", "x"]


def test_chunked():
    assert list(m.chunked(range(7), 3)) == [[0, 1, 2], [3, 4, 5], [6]]
    assert list(m.chunked((x for x in "abcd"), 2)) == [["a", "b"], ["c", "d"]]
    assert list(m.chunked([], 3)) == []
    with pytest.raises(ValueError):
        m.chunked([1, 2], 0)


def test_flatten():
    assert list(m.flatten([1, [2, (3, [4])], "ab"])) == [1, 2, 3, 4, "ab"]
    assert list(m.flatten([[], [[[]]], {"k": 1}])) == [{"k": 1}]
    assert list(m.flatten([])) == []


def make_api(pages):
    calls = []

    def fetch_page(cursor):
        calls.append(cursor)
        return pages[cursor]

    return fetch_page, calls


def test_paginate_all_pages():
    pages = {
        None: {"items": [1, 2], "next_cursor": "c2"},
        "c2": {"items": [], "next_cursor": "c3"},
        "c3": {"items": [3], "next_cursor": None},
    }
    fetch, calls = make_api(pages)
    assert list(m.paginate(fetch)) == [1, 2, 3]
    assert calls == [None, "c2", "c3"]


def test_paginate_is_lazy():
    pages = {
        None: {"items": [1, 2], "next_cursor": "c2"},
        "c2": {"items": [3], "next_cursor": None},
    }
    fetch, calls = make_api(pages)
    gen = m.paginate(fetch)
    assert calls == []  # nothing fetched until iteration starts
    assert list(itertools.islice(gen, 2)) == [1, 2]
    assert calls == [None]  # second page never requested
