from practice_target import load

import asyncio
import time

m = load("p18_asyncio")


async def _echo(value, delay):
    await asyncio.sleep(delay)
    return value


async def _boom(delay):
    await asyncio.sleep(delay)
    raise ValueError("boom")


def test_gather_in_order_results_and_speed():
    async def main():
        t0 = time.perf_counter()
        out = await m.gather_in_order([_echo("a", 0.05), _echo("b", 0.01), _echo("c", 0.03), _echo("d", 0.02)])
        return out, time.perf_counter() - t0

    out, elapsed = asyncio.run(main())
    assert out == ["a", "b", "c", "d"]
    assert elapsed < 0.15                         # sequential would be 0.11 s plus overhead
    assert asyncio.run(m.gather_in_order([])) == []


def test_run_blocking_concurrently():
    def slow_square(x):
        time.sleep(0.05)                          # blocking on purpose
        return x * x

    async def main():
        t0 = time.perf_counter()
        out = await m.run_blocking_concurrently(slow_square, [1, 2, 3, 4])
        return out, time.perf_counter() - t0

    out, elapsed = asyncio.run(main())
    assert out == [1, 4, 9, 16]
    assert elapsed < 0.15                         # sequential would be 0.2 s
    assert asyncio.run(m.run_blocking_concurrently(slow_square, [])) == []


def test_with_timeout_returns_value_when_fast():
    assert asyncio.run(m.with_timeout(_echo("ok", 0.001), 0.5, "fallback")) == "ok"


def test_with_timeout_cancels_slow_work():
    state = {}

    async def slow():
        try:
            await asyncio.sleep(1)
            return "late"
        except asyncio.CancelledError:
            state["cancelled"] = True
            raise

    async def main():
        t0 = time.perf_counter()
        result = await m.with_timeout(slow(), 0.02, "fallback")
        return result, time.perf_counter() - t0, state.get("cancelled", False)

    result, elapsed, cancelled = asyncio.run(main())
    assert result == "fallback"
    assert elapsed < 0.3
    assert cancelled is True                      # the slow work was really cancelled


def test_settle_all():
    out = asyncio.run(m.settle_all([_echo(1, 0.01), _boom(0.005), _echo(3, 0)]))
    assert out[0] == ("ok", 1)
    assert out[1][0] == "error" and isinstance(out[1][1], ValueError)
    assert out[2] == ("ok", 3)
    assert asyncio.run(m.settle_all([])) == []


def _tracker():
    stats = {"now": 0, "peak": 0}

    async def call(x):
        stats["now"] += 1
        stats["peak"] = max(stats["peak"], stats["now"])
        await asyncio.sleep(0.01)
        stats["now"] -= 1
        return x * 10

    return stats, call


def test_bounded_map_limits_concurrency():
    stats, call = _tracker()
    out = asyncio.run(m.bounded_map(call, list(range(12)), limit=3))
    assert out == [x * 10 for x in range(12)]
    assert stats["peak"] == 3


def test_bounded_map_edges():
    stats, call = _tracker()
    assert asyncio.run(m.bounded_map(call, [5, 6], limit=1)) == [50, 60]
    assert stats["peak"] == 1
    assert asyncio.run(m.bounded_map(call, [], limit=5)) == []


def test_queue_pipeline_order_and_cleanup():
    async def worker(x):
        await asyncio.sleep(0.005 * (6 - x))      # later items finish first
        return x * 2

    async def main():
        t0 = time.perf_counter()
        out = await m.queue_pipeline(list(range(6)), worker, n_workers=3)
        leftover = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        return out, time.perf_counter() - t0, leftover

    out, elapsed, leftover = asyncio.run(main())
    assert out == [0, 2, 4, 6, 8, 10]
    assert elapsed < 0.2
    assert leftover == []                         # workers were cancelled and awaited


def test_queue_pipeline_edges():
    async def double(x):
        await asyncio.sleep(0)
        return x * 2

    assert asyncio.run(m.queue_pipeline([], double)) == []
    assert asyncio.run(m.queue_pipeline(list(range(25)), double, n_workers=8)) == [x * 2 for x in range(25)]
