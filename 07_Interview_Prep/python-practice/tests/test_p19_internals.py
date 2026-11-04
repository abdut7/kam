from practice_target import load

import time
import tracemalloc

import pytest

m = load("p19_internals")


def test_is_hashable():
    assert m.is_hashable((1, 2)) is True
    assert m.is_hashable(frozenset({1, 2})) is True
    assert m.is_hashable([1, 2]) is False
    assert m.is_hashable((1, [2])) is False


def test_dedupe_preserve_order():
    assert m.dedupe_preserve_order([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert m.dedupe_preserve_order("banana") == ["b", "a", "n"]
    assert m.dedupe_preserve_order([]) == []


def test_dedupe_is_linear():
    big = list(range(10_000)) * 2
    t0 = time.perf_counter()
    assert m.dedupe_preserve_order(big) == list(range(10_000))
    assert time.perf_counter() - t0 < 0.1           # O(n) takes about 1 ms; `x in list` takes far longer


def test_pair_with_sum():
    assert m.pair_with_sum([2, 7, 11, 15], 9) == (0, 1)
    assert m.pair_with_sum([3, 2, 4], 6) == (1, 2)
    assert m.pair_with_sum([3, 3], 6) == (0, 1)
    assert m.pair_with_sum([1, 2], 10) is None


def test_pair_with_sum_edges():
    assert m.pair_with_sum([], 0) is None
    assert m.pair_with_sum([5], 10) is None
    big = list(range(100_000))
    assert m.pair_with_sum(big, 199_997) == (99_998, 99_999)


def test_point_equality_and_hash():
    a, b = m.Point(1, 2), m.Point(1, 2)
    assert a == b and hash(a) == hash(b)
    assert m.Point(1, 2) != m.Point(2, 1)
    assert m.Point(1, 2) != (1, 2)
    assert len({a, b, m.Point(3, 4)}) == 2


def test_point_as_key_and_slots():
    cache = {m.Point(1, 2): "hit"}
    assert cache[m.Point(1, 2)] == "hit"
    p = m.Point(5, 6)
    assert (p.x, p.y) == (5, 6)
    assert not hasattr(p, "__dict__")
    with pytest.raises(AttributeError):
        p.z = 3


def test_fib():
    assert m.fib(0) == 0
    assert m.fib(1) == 1
    assert m.fib(10) == 55
    assert hasattr(m.fib, "cache_info")             # checked before fib(90), so an uncached fib fails fast
    a, b = 0, 1
    for _ in range(90):
        a, b = b, a + b
    assert m.fib(90) == a


def test_peak_bytes():
    list_peak = m.peak_bytes(lambda: [i for i in range(100_000)])
    gen_peak = m.peak_bytes(lambda: sum(i for i in range(100_000)))
    assert isinstance(list_peak, int)
    assert list_peak > 1_000_000                    # 100k pointers plus 100k int objects
    assert gen_peak < 100_000                       # a generator keeps one item alive at a time
    assert not tracemalloc.is_tracing()
