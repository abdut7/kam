"""Lesson 18 solutions: async Python with asyncio (needs Python 3.11+)."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def gather_in_order(aws: list[Awaitable[Any]]) -> list[Any]:
    """Run every awaitable concurrently; results in input order."""
    async with asyncio.TaskGroup() as tg:              # 3.11+: cancels the rest if one fails
        tasks = [tg.create_task(_as_coro(aw)) for aw in aws]
    return [t.result() for t in tasks]                 # every task is done once the block exits


async def _as_coro(aw: Awaitable[Any]) -> Any:
    # create_task needs a coroutine; this wrapper also accepts Futures and Tasks.
    return await aw


async def run_blocking_concurrently(fn: Callable[[Any], Any], items: list[Any]) -> list[Any]:
    """Blocking functions go to threads so the event loop stays free."""
    return await asyncio.gather(*(asyncio.to_thread(fn, item) for item in items))


async def with_timeout(aw: Awaitable[Any], seconds: float, default: Any) -> Any:
    """Return the result, or default once the deadline passes (the work is cancelled)."""
    try:
        async with asyncio.timeout(seconds):           # 3.11+; asyncio.wait_for works too
            return await aw
    except TimeoutError:                               # built-in TimeoutError on 3.11+
        return default


async def settle_all(aws: list[Awaitable[Any]]) -> list[tuple[str, Any]]:
    """Promise.allSettled: ("ok", value) or ("error", exception), in input order."""
    results = await asyncio.gather(*aws, return_exceptions=True)
    return [
        ("error", r) if isinstance(r, BaseException) else ("ok", r)
        for r in results
    ]


async def bounded_map(
    func: Callable[[Any], Awaitable[Any]], items: list[Any], limit: int
) -> list[Any]:
    """At most `limit` calls in flight; results in input order."""
    sem = asyncio.Semaphore(limit)

    async def run_one(item: Any) -> Any:
        async with sem:                                # waits while `limit` calls are running
            return await func(item)

    return await asyncio.gather(*(run_one(item) for item in items))


async def queue_pipeline(
    items: list[Any], worker: Callable[[Any], Awaitable[Any]], n_workers: int = 3
) -> list[Any]:
    """Producer-consumer with asyncio.Queue; results in input order, no tasks left behind."""
    q: asyncio.Queue[tuple[int, Any]] = asyncio.Queue(maxsize=10)
    results: list[Any] = [None] * len(items)

    async def consume() -> None:
        while True:
            index, item = await q.get()
            try:
                results[index] = await worker(item)
            finally:
                q.task_done()                          # always, so join() cannot hang

    workers = [asyncio.create_task(consume()) for _ in range(n_workers)]
    try:
        for pair in enumerate(items):
            await q.put(pair)                          # waits while the queue is full
        await q.join()                                 # every item has been processed
    finally:
        for w in workers:
            w.cancel()                                 # workers loop forever: stop them
        await asyncio.gather(*workers, return_exceptions=True)   # wait until they are gone
    return results
