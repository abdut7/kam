"""Lesson 18: async Python with asyncio (needs Python 3.11+).

Implement each coroutine function, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p18_asyncio.py
The tests call your code with asyncio.run(...), so no pytest plugin is needed.
Until a function is implemented you may see "coroutine ... was never awaited"
warnings: the tests built coroutines that your stub never awaited.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


async def gather_in_order(aws: list[Awaitable[Any]]) -> list[Any]:
    """Run every awaitable concurrently and return their results in input order.

    Use asyncio.TaskGroup (3.11+) or asyncio.gather. Four calls that each sleep
    50 ms should take about 50 ms in total, not 200 ms. An empty list returns [].

    Example: await gather_in_order([fetch(1), fetch(2)]) -> [user1, user2]
    """
    raise NotImplementedError


async def run_blocking_concurrently(fn: Callable[[Any], Any], items: list[Any]) -> list[Any]:
    """fn is a normal blocking function (a sync SDK call, time.sleep, a file read).

    Call it for every item without blocking the event loop, using asyncio.to_thread,
    run the calls concurrently, and return results in input order.

    Example: await run_blocking_concurrently(slow_square, [1, 2, 3]) -> [1, 4, 9]
    """
    raise NotImplementedError


async def with_timeout(aw: Awaitable[Any], seconds: float, default: Any) -> Any:
    """Await aw, but give up after `seconds` and return `default` instead.

    On timeout the awaited work must be cancelled, not left running. Use
    `async with asyncio.timeout(seconds)` (3.11+) or asyncio.wait_for, and catch
    TimeoutError.

    Example: await with_timeout(asyncio.sleep(1, result="x"), 0.01, "fallback") -> "fallback"
    """
    raise NotImplementedError


async def settle_all(aws: list[Awaitable[Any]]) -> list[tuple[str, Any]]:
    """Python's Promise.allSettled.

    Run every awaitable concurrently and return, in input order, ("ok", value) for
    each success and ("error", exception) for each failure.

    Example: await settle_all([ok_one(), fails()]) -> [("ok", 1), ("error", ValueError("boom"))]
    """
    raise NotImplementedError


async def bounded_map(
    func: Callable[[Any], Awaitable[Any]], items: list[Any], limit: int
) -> list[Any]:
    """Call `await func(item)` for every item with at most `limit` calls in flight,
    for example at most 5 LLM calls at once. Return results in input order.

    Use asyncio.Semaphore(limit) around each call.

    Example: await bounded_map(call_llm, prompts, limit=5) -> [answer0, answer1, ...]
    """
    raise NotImplementedError


async def queue_pipeline(
    items: list[Any], worker: Callable[[Any], Awaitable[Any]], n_workers: int = 3
) -> list[Any]:
    """Producer-consumer with asyncio.Queue.

    Put (index, item) pairs on a bounded queue (maxsize=10). Start n_workers tasks
    that loop: get a pair, store `await worker(item)` at that index, call task_done().
    Wait for queue.join(), then cancel the workers and wait for them to finish, so no
    task is left running. Return results in input order.

    Example: await queue_pipeline([1, 2, 3], double, n_workers=2) -> [2, 4, 6]
    """
    raise NotImplementedError
