import pytest

from practice_target import load

m = load("p24_patterns_structures")
T = m.TreeNode


def test_valid_parentheses_true_cases():
    assert m.is_valid_parentheses("()[]{}") is True
    assert m.is_valid_parentheses("{[]}") is True
    assert m.is_valid_parentheses("") is True  # empty input is balanced


def test_valid_parentheses_false_cases():
    assert m.is_valid_parentheses("([)]") is False  # wrong order
    assert m.is_valid_parentheses(")") is False  # closer on an empty stack
    assert m.is_valid_parentheses("((") is False  # leftover openers
    assert m.is_valid_parentheses("(") is False  # single element


def test_daily_temperatures_basic():
    assert m.daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert m.daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]


def test_daily_temperatures_edge_cases():
    assert m.daily_temperatures([]) == []
    assert m.daily_temperatures([50]) == [0]
    assert m.daily_temperatures([70, 70, 70]) == [0, 0, 0]  # equal is not warmer
    assert m.daily_temperatures([60, 50, 40]) == [0, 0, 0]


def test_kth_largest_basic():
    assert m.kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert m.kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4  # duplicates count


def test_kth_largest_edge_cases():
    assert m.kth_largest([7], 1) == 7
    assert m.kth_largest([2, 2, 2], 2) == 2
    assert m.kth_largest([-1, -5, -3], 3) == -5


def test_kth_largest_bad_k():
    with pytest.raises(ValueError):
        m.kth_largest([], 1)
    with pytest.raises(ValueError):
        m.kth_largest([1, 2], 0)
    with pytest.raises(ValueError):
        m.kth_largest([1, 2], 3)


def test_level_order_basic():
    root = T(3, T(9), T(20, T(15), T(7)))
    assert m.level_order(root) == [[3], [9, 20], [15, 7]]
    lopsided = T(1, None, T(2, T(3)))
    assert m.level_order(lopsided) == [[1], [2], [3]]


def test_level_order_edge_cases():
    assert m.level_order(None) == []
    assert m.level_order(T(1)) == [[1]]
    assert m.level_order(T(5, T(5), T(5))) == [[5], [5, 5]]  # duplicate values


def test_num_islands_basic():
    grid = [
        [1, 1, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 1, 1],
    ]
    assert m.num_islands(grid) == 3
    assert m.num_islands([[1, 0], [0, 1]]) == 2  # diagonal does not connect


def test_num_islands_edge_cases():
    assert m.num_islands([]) == 0
    assert m.num_islands([[]]) == 0
    assert m.num_islands([[1]]) == 1
    assert m.num_islands([[0, 0], [0, 0]]) == 0


def test_num_islands_does_not_modify_grid():
    grid = [[1, 1], [0, 1]]
    m.num_islands(grid)
    assert grid == [[1, 1], [0, 1]]


def test_num_islands_large_grid_no_recursion_error():
    grid = [[1] * 120 for _ in range(120)]
    assert m.num_islands(grid) == 1


def _is_valid_order(order, n, prereqs):
    if sorted(order) != list(range(n)):
        return False
    pos = {c: i for i, c in enumerate(order)}
    return all(pos[pre] < pos[course] for course, pre in prereqs)


def test_course_order_valid_orders():
    assert m.course_order(2, [(1, 0)]) == [0, 1]
    prereqs = [(1, 0), (2, 0), (3, 1), (3, 2)]
    assert _is_valid_order(m.course_order(4, prereqs), 4, prereqs)


def test_course_order_edge_cases():
    assert m.course_order(0, []) == []
    assert m.course_order(1, []) == [0]
    dup = [(1, 0), (1, 0)]  # duplicate prerequisite pairs
    assert m.course_order(2, dup) == [0, 1]


def test_course_order_cycles():
    assert m.course_order(2, [(1, 0), (0, 1)]) is None
    assert m.course_order(1, [(0, 0)]) is None  # self loop
    assert m.course_order(3, [(1, 0), (2, 1), (1, 2)]) is None


def test_coin_change_basic():
    assert m.coin_change([1, 2, 5], 11) == 3
    assert m.coin_change([1, 3, 4], 6) == 2  # greedy (4 + 1 + 1) is wrong
    assert m.coin_change([186, 419, 83, 408], 6249) == 20


def test_coin_change_edge_cases():
    assert m.coin_change([1], 0) == 0
    assert m.coin_change([], 0) == 0
    assert m.coin_change([], 7) == -1
    assert m.coin_change([2], 3) == -1


def test_coin_change_duplicate_coins_and_medium_amount():
    assert m.coin_change([1, 1, 2], 4) == 2
    assert m.coin_change([1, 2, 5], 300) == 60
