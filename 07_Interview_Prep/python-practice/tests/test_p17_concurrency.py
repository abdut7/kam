from practice_target import load

import functools
import threading
import time

m = load("p17_concurrency")


def _top_level(x):
    return x


def test_is_picklable():
    assert m.is_picklable({"a": [1, 2], "b": (3, "x")}) is True
    assert m.is_picklable(_top_level) is True
    assert m.is_picklable(functools.partial(abs, -1)) is True
    assert m.is_picklable(lambda x: x) is False


def test_is_picklable_unpicklable_objects():
    def local(x):
        return x

    assert m.is_picklable(local) is False
    assert m.is_picklable(threading.Lock()) is False
    assert m.is_picklable(i for i in range(3)) is False


def test_thread_map_order_and_values():
    assert m.thread_map(lambda x: x * 2, [1, 2, 3]) == [2, 4, 6]
    assert m.thread_map(str.upper, ["a", "b"], max_workers=1) == ["A", "B"]
    assert m.thread_map(lambda x: x, []) == []


def test_thread_map_overlaps_blocking_io():
    def slow(x):
        time.sleep(0.05)
        return x

    t0 = time.perf_counter()
    assert m.thread_map(slow, list(range(8)), max_workers=8) == list(range(8))
    assert time.perf_counter() - t0 < 0.25          # sequential would be 0.4 s


def test_safe_counter_no_lost_updates():
    counter = m.SafeCounter()
    assert counter.value == 0

    def work():
        for _ in range(200):
            counter.increment()

    threads = [threading.Thread(target=work) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert counter.value == 800


def test_map_collect_errors():
    out = m.map_collect_errors(lambda x: 10 // x, [1, 0, 5])
    assert out[1] == 10
    assert out[5] == 2
    assert isinstance(out[0], ZeroDivisionError)
    assert m.map_collect_errors(lambda x: x, []) == {}


def test_threaded_pipeline_order():
    assert m.threaded_pipeline([1, 2, 3], lambda x: x * x, n_workers=2) == [1, 4, 9]

    def slow_for_small(x):
        time.sleep(0.01 * (5 - x))                  # finishing order differs from input order
        return x * 10

    assert m.threaded_pipeline(list(range(5)), slow_for_small, n_workers=3) == [0, 10, 20, 30, 40]


def test_threaded_pipeline_edges():
    before = threading.active_count()
    assert m.threaded_pipeline([], lambda x: x) == []
    assert m.threaded_pipeline(list(range(25)), lambda x: x + 1, n_workers=8) == list(range(1, 26))
    assert threading.active_count() == before      # every worker thread has exited


def test_parallel_sum_of_squares():
    assert m.parallel_sum_of_squares([range(0, 3), range(3, 5)]) == 30
    assert m.parallel_sum_of_squares([range(1000)], max_workers=1) == sum(x * x for x in range(1000))
    assert m.parallel_sum_of_squares([]) == 0
