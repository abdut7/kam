import pytest

from practice_target import load

m = load("p06_lists_tuples")


def test_chunk():
    assert m.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert m.chunk(["a", "b"], 5) == [["a", "b"]]
    assert m.chunk([], 3) == []
    with pytest.raises(ValueError):
        m.chunk([1, 2], 0)


def test_flatten():
    assert m.flatten([[1, 2], [], [3]]) == [1, 2, 3]
    assert m.flatten([]) == []
    assert m.flatten([["a"], ["b", "c"]]) == ["a", "b", "c"]


def test_rotate():
    data = [1, 2, 3, 4, 5]
    assert m.rotate(data, 2) == [4, 5, 1, 2, 3]
    assert m.rotate(data, 7) == [4, 5, 1, 2, 3]
    assert m.rotate(data, -1) == [2, 3, 4, 5, 1]
    assert m.rotate(data, 0) == [1, 2, 3, 4, 5] and m.rotate(data, 0) is not data
    assert m.rotate([], 3) == []
    assert data == [1, 2, 3, 4, 5]


def test_make_grid():
    grid = m.make_grid(2, 3)
    assert grid == [[0, 0, 0], [0, 0, 0]]
    grid[0][0] = 9
    assert grid[1][0] == 0
    assert m.make_grid(1, 2, fill=".") == [[".", "."]]
    assert m.make_grid(0, 4) == []


def test_top_results():
    results = [("b", 0.9), ("a", 0.9), ("c", 0.5), ("d", 0.95)]
    assert m.top_results(results, 3) == [("d", 0.95), ("a", 0.9), ("b", 0.9)]
    assert m.top_results(results, 10) == [("d", 0.95), ("a", 0.9), ("b", 0.9), ("c", 0.5)]
    assert m.top_results(results, 0) == []
    assert results == [("b", 0.9), ("a", 0.9), ("c", 0.5), ("d", 0.95)]


def test_letter_grade():
    assert [m.letter_grade(s) for s in (0, 59.5, 60, 75, 89, 90, 100)] == ["F", "F", "D", "C", "B", "A", "A"]
    with pytest.raises(ValueError):
        m.letter_grade(101)
    with pytest.raises(ValueError):
        m.letter_grade(-1)
