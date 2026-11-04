## Concurrency: Threads, Processes & the GIL [Advanced]

> Concurrency questions show up whenever a Python backend waits on many things or crunches a lot of data: a batch script calling an LLM API for 10,000 rows, a FastAPI service parsing PDFs, an ingestion worker hashing files, a Celery fleet. Interviewers want to see you classify the work (waiting or computing), pick threads, processes or asyncio for a stated reason, explain why threads did not speed up a CPU loop (the GIL), and know the bugs each choice brings: races and lost updates with threads, pickling errors and memory cost with processes.

### Why it exists
Most backend time is spent waiting on networks, disks, databases and LLM APIs, and one thread that waits does nothing else in the meantime. Threads let one process overlap those waits, and processes let one program use more than one CPU core. CPython adds a twist: the Global Interpreter Lock (GIL) lets only one thread run Python bytecode at a time, which kept the interpreter and its C extensions simple and single-threaded code fast, but means threads do not speed up pure-Python CPU work. So Python gives you three tools (threads, processes and asyncio) and you pick by workload, paying with race conditions for threads and with pickling, startup time and memory for processes.

### In plain words
Picture a kitchen with exactly one chef's knife, which stands for the GIL. Several cooks (threads) can work in the kitchen, but only the cook holding the knife can chop. When a cook waits for water to boil (I/O), they put the knife down and someone else chops, so extra cooks help a lot when the work is mostly waiting and not at all when it is all chopping. For chopping-heavy work you open more kitchens (processes), each with its own knife, but you must carry ingredients between kitchens in sealed boxes (pickling). asyncio is a single very fast cook who juggles many pots alone and never stands still.

### Walkthrough: choosing threads, processes or asyncio
1. **Classify the work first**: I/O-bound work spends its time waiting (HTTP, database, LLM API, disk); CPU-bound work spends it computing (parsing, tokenizing, pure-Python loops). Measure instead of guessing: if CPU time is far below wall time, you are waiting.

   ```python
   import time

   t0, c0 = time.perf_counter(), time.process_time()
   run_job()
   wall, cpu = time.perf_counter() - t0, time.process_time() - c0
   print(f"wall={wall:.2f}s cpu={cpu:.2f}s")   # cpu much smaller than wall: I/O-bound
   ```

2. **Know what the GIL does**: in CPython one thread per process runs Python bytecode at a time. A running thread is asked to release the GIL every 5 ms so others get a turn, and blocking calls (sleep, socket and file reads) plus many C extensions release it while they wait or compute.

   ```python
   import sys

   print(sys.getswitchinterval())   # 0.005: the 5 ms switch interval
   # time.sleep, socket reads, file reads, hashlib on large buffers and most
   # NumPy kernels release the GIL while they run
   ```

3. **I/O-bound with sync libraries: threads.** requests, boto3 and psycopg2 block, but they release the GIL while waiting on the socket, so 16 threads overlap 16 waits. This is the same idea as Node's libuv pool, except you put your own functions in it.

   ```python
   from concurrent.futures import ThreadPoolExecutor
   import requests

   def get(url: str) -> str:
       return requests.get(url, timeout=10).text

   with ThreadPoolExecutor(max_workers=16) as pool:
       pages = list(pool.map(get, urls))      # input order, about 16 requests at a time
   ```

4. **I/O-bound with async libraries or thousands of connections: asyncio.** One thread, one event loop, tasks that cost a few KB each instead of an OS thread each. This is the model you already know from Node.

   ```python
   import asyncio
   import httpx

   async def fetch_all(urls: list[str]) -> list[str]:
       async with httpx.AsyncClient(timeout=10) as client:
           responses = await asyncio.gather(*(client.get(u) for u in urls))
       return [r.text for r in responses]
   ```

5. **CPU-bound pure Python: processes.** Each process has its own interpreter and its own GIL, so four processes really use four cores. The price is process startup, copying data in and out by pickling, and one copy of your imports per process.

   ```python
   from concurrent.futures import ProcessPoolExecutor

   def score(doc: str) -> int:                 # top level, so it can be pickled
       return sum(len(word) for word in doc.split())

   if __name__ == "__main__":
       with ProcessPoolExecutor() as pool:      # one worker per core by default
           scores = list(pool.map(score, docs, chunksize=100))
   ```

6. **CPU-bound inside C code that releases the GIL: threads can work.** hashlib releases the GIL for inputs larger than about 2 KB, and NumPy does in many array kernels, so threads run those in parallel without pickling. Confirm by watching CPU usage go above 100%.

   ```python
   import hashlib
   from concurrent.futures import ThreadPoolExecutor

   def digest(blob: bytes) -> str:
       return hashlib.sha256(blob).hexdigest()  # GIL released while hashing a large blob

   with ThreadPoolExecutor(max_workers=4) as pool:
       digests = list(pool.map(digest, blobs))
   ```

7. **Mixing them in an async service**: the request path stays on the event loop, a blocking SDK call goes to a thread, and a CPU step goes to a process pool.

   ```python
   async def handle(key: str, cpu_pool: ProcessPoolExecutor) -> dict:
       raw = await asyncio.to_thread(download_from_s3, key)       # blocking boto3 code
       loop = asyncio.get_running_loop()
       return await loop.run_in_executor(cpu_pool, parse_pdf, raw)  # CPU work in a process
   ```

8. **Free-threaded Python changes the CPU rule, with care.** Python 3.13 shipped an experimental free-threaded build (PEP 703), a separate interpreter usually called `python3.13t`, where threads run bytecode in parallel. Python 3.14 made that build officially supported, but it is still optional and not the default, and an extension module that has not declared support turns the GIL back on when imported. Production designs still assume the GIL.

   ```python
   import sys

   print(sys._is_gil_enabled())   # 3.13+: False only on a free-threaded build running without the GIL
   ```

The decision in one table:

| Workload | Tool | Why |
|---|---|---|
| Tens to hundreds of blocking I/O calls, sync libraries | `ThreadPoolExecutor` | the GIL is released while waiting |
| Thousands of concurrent connections, async libraries | asyncio | one thread, tiny cost per task |
| Pure-Python CPU work | `ProcessPoolExecutor` | one GIL per process |
| CPU work in C extensions that release the GIL | threads, after measuring | NumPy, hashlib and zlib run in parallel |
| Jobs that outlive a request | Celery, arq or another task queue | survives restarts, scales separately |

### Walkthrough: threads, locks and queues
1. **Start and join threads**: `threading.Thread` runs a function in a new OS thread; `join()` waits for it. All threads share the same objects in memory, unlike Node's worker_threads, which each get a separate heap.

   ```python
   import threading
   import time

   def download(name: str) -> None:
       time.sleep(0.5)                       # stands in for a blocking HTTP call
       print("done", name)

   threads = [threading.Thread(target=download, args=(n,)) for n in ("a", "b", "c")]
   for t in threads:
       t.start()
   for t in threads:
       t.join()                              # about 0.5 s in total, not 1.5 s
   ```

2. **Shared state plus a read-modify-write is a race.** Here every thread reads the counter, gets switched out at the I/O point, and writes back a stale value, so updates are lost.

   ```python
   counter = 0

   def add(n: int) -> None:
       global counter
       for _ in range(n):
           current = counter        # read
           time.sleep(0)            # any I/O here lets another thread run
           counter = current + 1    # write back a value that may be stale

   threads = [threading.Thread(target=add, args=(1000,)) for _ in range(4)]
   for t in threads:
       t.start()
   for t in threads:
       t.join()
   print(counter)                   # far below 4000, and different on every run
   ```

   A plain `counter += 1` is the same bug in smaller form: it compiles to a load, an add and a store, and a thread can be switched out between them. On recent CPython a tight `+= 1` loop may happen to print the right total, because the interpreter only switches threads at certain points, which makes the bug rarer, not absent. On a free-threaded build it shows up readily.

3. **Fix it with a Lock**: `with lock:` lets one thread at a time through the critical section. Keep that section short, and do slow I/O outside it when you can.

   ```python
   lock = threading.Lock()

   def add(n: int) -> None:
       global counter
       for _ in range(n):
           with lock:                   # acquire, run, release even on exceptions
               current = counter
               time.sleep(0)
               counter = current + 1    # now always 4000
   ```

   `threading.RLock` can be re-acquired by the thread that holds it, which you need when one locked method calls another. Two locks taken in different orders by two threads is the classic deadlock, so always acquire them in one fixed order.

4. **Hand work over with queue.Queue instead of sharing it.** `queue.Queue` is thread-safe and does its own locking; `maxsize` makes `put()` block when consumers fall behind, which is backpressure. Stop each worker with one sentinel.

   ```python
   import queue

   jobs: queue.Queue[str | None] = queue.Queue(maxsize=100)

   def worker() -> None:
       while (url := jobs.get()) is not None:   # None is the stop signal
           process(url)

   workers = [threading.Thread(target=worker) for _ in range(4)]
   for w in workers:
       w.start()
   for url in urls:
       jobs.put(url)                            # blocks while 100 jobs are waiting
   for _ in workers:
       jobs.put(None)                           # one sentinel per worker
   for w in workers:
       w.join()
   ```

   Python 3.13 added `Queue.shutdown()`, which makes blocked `get()` calls raise `queue.ShutDown` once the queue is empty, so new code can drop the sentinels.

5. **Signal with Event, and be careful with daemon threads.** `threading.Event` is a thread-safe flag that threads can wait on. A daemon thread is killed abruptly when the interpreter exits, with no `finally` blocks run, so use an Event for a clean stop.

   ```python
   stop = threading.Event()

   def heartbeat() -> None:
       while not stop.wait(timeout=5):          # wakes every 5 s, or at once when stop is set
           send_ping()

   t = threading.Thread(target=heartbeat, daemon=True)
   t.start()
   # ... at shutdown:
   stop.set()
   t.join()
   ```

6. **Know what is already safe**: one operation on a built-in, such as `list.append` or `d[key] = value`, is thread-safe in CPython, and so are `queue.Queue` and `logging`. A check-then-act sequence is not: two threads can both see a missing key and both run the slow loader.

   ```python
   cache: dict[str, str] = {}
   cache_lock = threading.Lock()

   def get(key: str) -> str:
       with cache_lock:                         # check and set as one step
           if key not in cache:
               cache[key] = load(key)
           return cache[key]
   ```

### Walkthrough: executors and processes
1. **ThreadPoolExecutor.map**: the simplest pool. Results come back in input order, and if a call raised, the exception is raised when iteration reaches that item. The `with` block waits for all work before exiting.

   ```python
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=8) as pool:
       results = list(pool.map(fetch_json, urls))   # same order as urls
   ```

2. **submit and as_completed**: `submit` returns a Future at once; `as_completed` yields futures as they finish, so you can handle each result or error on its own, like `Promise.allSettled` with a loop.

   ```python
   from concurrent.futures import ThreadPoolExecutor, as_completed

   with ThreadPoolExecutor(max_workers=8) as pool:
       futures = {pool.submit(fetch_json, u): u for u in urls}
       for fut in as_completed(futures):
           url = futures[fut]
           try:
               data = fut.result()           # re-raises the worker's exception here
           except Exception as exc:
               log.warning("failed %s: %s", url, exc)
   ```

3. **ProcessPoolExecutor**: the same API, but workers are separate processes. On macOS and Windows children start with `spawn`, a fresh interpreter that re-imports your main module, so the pool must be created under `if __name__ == "__main__":`.

   ```python
   from concurrent.futures import ProcessPoolExecutor

   def count_tokens(text: str) -> int:      # must live at module top level
       return len(text.split())

   if __name__ == "__main__":               # without it, each child would re-run this block
       with ProcessPoolExecutor(max_workers=4) as pool:
           totals = list(pool.map(count_tokens, docs, chunksize=50))
   ```

   `chunksize` sends items in batches, which cuts the per-item messaging cost when tasks are small.

4. **Everything that crosses the boundary is pickled.** Functions are pickled by reference (module plus name), so lambdas and nested functions fail; locks, open files, sockets, database connections and generators fail too. Large arguments are copied, so pass paths or IDs rather than big payloads.

   ```python
   import pickle
   import threading

   pickle.dumps({"id": 1, "text": "ok"})   # fine: plain data
   pickle.dumps(lambda x: x)               # PicklingError
   pickle.dumps(threading.Lock())          # TypeError: cannot pickle '_thread.lock' object
   ```

   A nested function fails with `PicklingError` on 3.14 and with an `AttributeError` naming the local object on older versions. `functools.partial` of a top-level function with picklable arguments works.

5. **multiprocessing basics**: the lower-level module behind the pool. `Process` runs one function in a child, and `Pool` is the older pool API. The start method decides how children are created: `spawn` is the default on macOS and Windows, Linux used `fork` until 3.14 switched it to `forkserver`, because forking a process that has threads can copy a lock held by a thread that does not exist in the child and deadlock.

   ```python
   import multiprocessing as mp

   def work(n: int) -> None:
       print(mp.current_process().name, n * n)

   if __name__ == "__main__":
       p = mp.Process(target=work, args=(7,))
       p.start()
       p.join()
       with mp.Pool(processes=4) as pool:
           print(pool.map(abs, [-1, -2, -3]))   # [1, 2, 3]
   ```

6. **Per-process setup with initializer**: anything expensive, such as a model or a client, is created once per worker process, not once per task, and never sent through pickle.

   ```python
   _model = None

   def init_worker(path: str) -> None:
       global _model
       _model = load_model(path)            # runs once in each worker process

   def embed(text: str) -> list[float]:
       return _model.encode(text)

   pool = ProcessPoolExecutor(max_workers=2, initializer=init_worker, initargs=("model.bin",))
   ```

7. **Compare with Node**: Node runs your JavaScript on one main thread. libuv keeps a thread pool (4 threads by default, `UV_THREADPOOL_SIZE`) for file system calls, `dns.lookup`, some crypto and zlib, while network sockets use epoll or kqueue on the main loop. `worker_threads` are separate V8 isolates with their own heap and event loop that talk through `postMessage`.

   ```js
   const { Worker } = require("node:worker_threads");
   const w = new Worker("./score.js", { workerData: docs });   // separate heap
   w.on("message", (scores) => console.log(scores));
   ```

   ```python
   if __name__ == "__main__":
       with ProcessPoolExecutor() as pool:      # Python's counterpart: separate memory
           scores = list(pool.map(score, docs))   # messages pickled, not structured-cloned
   ```

   The closest Python match to a worker thread is a process: separate memory, messages copied (pickle instead of structured clone). Python threads are a different animal: one shared heap, so you need locks, but one GIL, so no CPU parallelism for Python code.

### Concepts you must understand
- I/O-bound work waits and CPU-bound work computes; threads and asyncio overlap waiting, while only processes (or C code that releases the GIL) add CPU parallelism.
- The GIL lets one thread per process run Python bytecode at a time; it is released during blocking I/O and inside many C extensions, and a running thread is asked to give it up every 5 ms (`sys.getswitchinterval()`).
- The GIL protects the interpreter, not your data: read-modify-write and check-then-act sequences are races, so guard them with `threading.Lock` or avoid sharing by passing messages through `queue.Queue`.
- `queue.Queue` is thread-safe; `maxsize` gives backpressure, and workers stop on one sentinel each (or `Queue.shutdown()` on 3.13+).
- `concurrent.futures` gives one API for both pools: `map` returns results in input order and raises a worker's exception when you reach that item; `submit` returns a Future, and `as_completed` yields futures as they finish.
- Process pools pickle the function, arguments and results: the function must be importable at module top level, and the `if __name__ == "__main__":` guard is required under `spawn` (the default on macOS and Windows).
- Each process has its own memory, GIL and copy of every import, so pools cost startup time and RAM; load heavy models once per worker with `initializer`.
- Free-threaded CPython (PEP 703) was an experimental separate build in 3.13 and is supported but optional in 3.14; extensions that have not declared support re-enable the GIL, so production code still assumes it.
- Node runs JavaScript on one thread, with libuv's pool (4 threads by default) for fs, `dns.lookup`, crypto and zlib; worker_threads have separate heaps, while Python threads share one heap.

| JavaScript | Python | Note |
|---|---|---|
| One main thread running JS | One thread at a time running bytecode (the GIL) | Python can have many OS threads; only one runs Python code at once |
| libuv thread pool (`UV_THREADPOOL_SIZE`) | `ThreadPoolExecutor`, `asyncio.to_thread` | Python's pool runs your own blocking functions |
| `new Worker()` from worker_threads | `ProcessPoolExecutor`, `multiprocessing.Process` | separate memory and message passing in both |
| `postMessage` (structured clone) | pickle | pickle cannot send lambdas, locks or open files |
| `SharedArrayBuffer` and `Atomics` | `multiprocessing.shared_memory`, `Value`, `Array` | rarely needed; prefer passing data |
| `cluster` module or PM2 | Gunicorn or `uvicorn --workers` | one server process per core |
| piscina or a worker pool size | `max_workers` | for I/O, size by the remote limit, not by cores |
| No locks needed in single-threaded JS | `threading.Lock`, `RLock` | Python threads can be switched out between any two bytecodes |
| `Atomics.wait` and `Atomics.notify` | `threading.Event`, `threading.Condition` | |
| `Promise.allSettled` over worker jobs | `as_completed` plus `fut.result()` in try | |

### Q. A script calls an internal API for 2,000 customer IDs one at a time with requests and takes 25 minutes. Write a function that speeds it up with threads, without switching to async libraries.
**Short answer (45 seconds):** The work is I/O-bound: each call spends nearly all its time waiting on the network, and requests releases the GIL while it waits. I would run the calls on a `ThreadPoolExecutor` with a worker count set by what the API tolerates (start around 16), use `submit` and `as_completed` so one failing ID does not kill the batch, give every call a timeout, and keep one `requests.Session` per thread for connection reuse.

**Deeper explanation:**

```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

_local = threading.local()

def _session() -> requests.Session:
    if not hasattr(_local, "session"):
        _local.session = requests.Session()     # one connection pool per thread
    return _local.session

def fetch_customer(cid: int) -> dict:
    resp = _session().get(f"{BASE_URL}/customers/{cid}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_all(ids: list[int], workers: int = 16) -> tuple[dict[int, dict], dict[int, Exception]]:
    ok: dict[int, dict] = {}
    failed: dict[int, Exception] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_customer, cid): cid for cid in ids}
        for fut in as_completed(futures):
            cid = futures[fut]
            try:
                ok[cid] = fut.result()
            except Exception as exc:               # one bad ID must not stop the batch
                failed[cid] = exc
    return ok, failed
```

Wall time drops to roughly (number of calls x latency) / workers until the API, not your script, becomes the limit. `threading.local()` gives each thread its own Session, because requests does not promise that one Session is safe to share across threads. Results are written only by the main thread inside the `as_completed` loop, so no lock is needed. An empty list returns two empty dicts. Retry the `failed` IDs afterwards with backoff rather than inside the hot loop.

**Follow-ups they will ask:**
- How do you choose `max_workers`? : by the API's concurrency or rate limit, not by CPU count; start low, watch throughput and 429 responses, and back off when they appear.
- Why not asyncio? : with `httpx.AsyncClient` and a Semaphore it handles thousands of connections with less memory, which is worth it when the code is already async or the fan-out is huge.
- What happens on Ctrl+C? : the `with` block waits for running calls; `pool.shutdown(cancel_futures=True)` (3.9+) drops the queued ones.

**Mistakes to avoid:**
- Using a process pool for network calls, which pays for startup and pickling and gains nothing.
- Setting `max_workers=len(ids)` and hammering the API with 2,000 parallel requests.
- Using `pool.map` and losing the whole batch when one call raises.

### Q. A RateTracker shared by 8 threads reports fewer hits than the access log shows. Find the race and fix it.
**Short answer (45 seconds):** The tracker reads a count, does some work, then writes the count back, so two threads can read the same value and both write value + 1, losing one update. The GIL does not prevent this: it makes single bytecodes atomic, not sequences. I would put the read and write under a `threading.Lock`, keep slow I/O outside the lock, and read snapshots under the lock too.

**Deeper explanation:** The buggy version:

```python
class RateTracker:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def hit(self, route: str) -> None:
        current = self.counts.get(route, 0)   # read
        self.flush_if_due()                   # does I/O: another thread runs now
        self.counts[route] = current + 1      # write: overwrites the other thread's update
```

The fix:

```python
import threading

class RateTracker:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self._lock = threading.Lock()

    def hit(self, route: str) -> None:
        with self._lock:                      # read and write as one step
            self.counts[route] = self.counts.get(route, 0) + 1
        self.flush_if_due()                   # slow I/O stays outside the lock

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self.counts)          # a copy, safe to iterate
```

The I/O call releases the GIL, which makes the lost update almost certain, but even without it `self.counts[route] += 1` is several bytecodes and can be interrupted between the read and the store. Such code often passes a quick test on recent CPython and then loses counts in production, and it fails much more often on a free-threaded build. The snapshot method matters too: iterating `self.counts` while another thread inserts a new route raises `RuntimeError: dictionary changed size during iteration`.

**Follow-ups they will ask:**
- Lock or RLock? : RLock when a method that holds the lock calls another method that takes it; a plain Lock would deadlock there.
- Can you avoid the lock entirely? : yes, send hits to one owner thread through `queue.Queue`, or keep a counter per thread and merge them when reporting.
- What if the app runs 4 Gunicorn workers? : each process has its own tracker, so use Redis `INCR` or the Prometheus client's multiprocess mode for one total.

**Mistakes to avoid:**
- Claiming the GIL makes Python code thread-safe.
- Holding the lock across slow I/O, which turns 8 threads into a queue of one.
- Running the test once, seeing the right number, and calling it fixed.

### Q. A teammate parallelized PDF parsing with ThreadPoolExecutor and saw no speed-up, then switched to ProcessPoolExecutor and got "Can't pickle local object". Fix both problems.
**Short answer (45 seconds):** Threads did not help because the parser is pure-Python CPU work, and only one thread can hold the GIL and run it at a time. Processes are the right tool, but a process pool pickles the function it sends, and a nested function cannot be pickled because the child cannot import it by name. I would move the function to module top level, pass file paths instead of bytes or open files, add the `__main__` guard, and size the pool to the cores.

**Deeper explanation:** The broken version:

```python
def ingest(paths: list[str]) -> list[str]:
    def parse(path: str) -> str:              # nested: the child cannot import it
        with open(path, "rb") as f:
            return extract_text(f.read())     # pure-Python parser, holds the GIL
    with ProcessPoolExecutor() as pool:
        return list(pool.map(parse, paths))
```

The fix:

```python
import os
import sys
from concurrent.futures import ProcessPoolExecutor

def parse(path: str) -> str:                  # top level: pickled as module + name
    with open(path, "rb") as f:
        return extract_text(f.read())

def ingest(paths: list[str]) -> list[str]:
    workers = min(4, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(parse, paths, chunksize=8))

if __name__ == "__main__":                    # spawn re-imports this module in every child
    texts = ingest(sys.argv[1:])
```

Each process has its own interpreter and GIL, so four processes parse four files at once. Pickle sends a function as a reference that the child re-imports, which is why lambdas and nested functions fail. Passing a path means the child reads the file itself instead of receiving a large byte string through a pipe, and returning plain text keeps the result small. `chunksize` batches small tasks to cut messaging overhead. Memory is workers x the parser's peak, so count it before raising the worker count.

**Follow-ups they will ask:**
- Would threads ever be right here? : yes, if the heavy work runs in C that releases the GIL; measure CPU usage, and above 100% means real parallelism.
- How do you share a large read-only model? : load it once per worker with `initializer`; with `fork` on Linux pages start out shared, but reference count updates gradually copy them.
- Can a child update a global the parent sees? : no, each process has its own memory; return results or use a Manager, a queue or a database.

**Mistakes to avoid:**
- 32 workers on an 8-core machine, which adds switching and memory and no speed.
- Passing open files, database clients or locks as arguments.

### Q. Write a producer-consumer pipeline: one thread reads a large log file, four worker threads parse lines, and the caller gets every result. Memory must stay bounded and shutdown must be clean.
**Short answer (45 seconds):** I would connect the reader to the workers with a bounded `queue.Queue`, so reading can never run more than a fixed number of lines ahead of parsing, collect results on a second queue, and stop each worker with its own sentinel object. Workers catch exceptions per line so one bad line cannot kill a thread, and the caller joins every thread before reading results.

**Deeper explanation:**

```python
import queue
import threading
from collections.abc import Callable, Iterable

_STOP = object()                                    # unique: no real line can equal it

def pipeline(lines: Iterable[str], parse: Callable[[str], dict], workers: int = 4) -> list[dict]:
    jobs: queue.Queue = queue.Queue(maxsize=1000)  # put() blocks when full
    results: queue.Queue = queue.Queue()

    def worker() -> None:
        while (line := jobs.get()) is not _STOP:
            try:
                results.put(parse(line))
            except Exception as exc:               # keep the worker alive
                results.put({"error": repr(exc), "line": line[:80]})

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for t in threads:
        t.start()
    for line in lines:                              # the producer is the calling thread
        jobs.put(line)
    for _ in threads:
        jobs.put(_STOP)                             # one stop signal per worker
    for t in threads:
        t.join()
    return [results.get() for _ in range(results.qsize())]   # exact: all workers have exited
```

Call it as `with open(path) as f: pipeline(f, parse_line)`, so the file is read lazily line by line. The bounded queue gives backpressure: memory holds at most 1,000 pending lines plus the results. A sentinel made with `object()` cannot collide with any real line, unlike `None` or an empty string. If a worker died on an uncaught exception, it would never consume its sentinel; with all workers dead and the queue full, the producer would block forever, which is why the worker catches per line. Results arrive in completion order; carry the line number through the queue if order matters.

**Follow-ups they will ask:**
- Parsing is CPU-heavy pure Python: does this speed it up? : no, threads take turns on the GIL; keep the shape but use `ProcessPoolExecutor.map` with a `chunksize`, or `multiprocessing.Queue`.
- How does 3.13 change this? : `Queue.shutdown()` makes `get()` raise `queue.ShutDown` once the queue is drained, so sentinels become optional.
- Why not daemon threads and no join? : the process can exit while workers still hold parsed lines, silently dropping work.

**Mistakes to avoid:**
- An unbounded queue, which loads the whole file into memory when parsing is slower than reading.
- One sentinel for four workers, which leaves three blocked on `get()` forever.

### Q. Predict how long each of the three timed runs takes on a 4-core laptop, and explain the results with the GIL.
**Short answer (45 seconds):** If one call of `busy` takes T seconds alone, run A takes about 1 second, run B about 4T and run C about T plus process startup. Sleeping releases the GIL, so four threads sleep in parallel. A pure-Python loop holds the GIL, so four threads take turns and add up to the same time as running them one after another. Four processes have four GILs and use four cores.

**Deeper explanation:** The code:

```python
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

def sleepy(_):               # waits, like a network call
    time.sleep(1)

def busy(_):                 # pure-Python CPU work
    total = 0
    for i in range(20_000_000):
        total += i
    return total

def timed(pool_cls, fn) -> float:
    t0 = time.perf_counter()
    with pool_cls(max_workers=4) as pool:
        list(pool.map(fn, range(4)))
    return round(time.perf_counter() - t0, 1)

if __name__ == "__main__":
    print(timed(ThreadPoolExecutor, sleepy))    # A
    print(timed(ThreadPoolExecutor, busy))      # B
    print(timed(ProcessPoolExecutor, busy))     # C
```

A: `time.sleep` releases the GIL, so all four threads wait at the same time and the run takes about 1 second. B: each thread needs the GIL for every bytecode of the loop, and the interpreter hands it around every 5 ms, so the four loops are interleaved on one core and the total is about 4T, sometimes a little more because of switching. C: each process has its own interpreter and GIL, so the four loops run on four cores and finish in about T, plus the cost of starting processes, which is larger with `spawn` because each child imports your modules again. On a free-threaded build, B can approach C because threads then run bytecode in parallel.

**Follow-ups they will ask:**
- What if `busy` called NumPy on large arrays? : many NumPy kernels release the GIL, so threads could scale like C without pickling.
- Why time with `perf_counter`? : it is monotonic and high resolution; `time.time()` can jump when the system clock is adjusted.
- How would you prove B is GIL-bound in production? : CPU usage of the process stays near one core while threads are busy, and `py-spy dump` shows threads waiting to take the GIL.

**Mistakes to avoid:**
- Predicting B at about T because "threads are parallel".
- Predicting A at about 4 seconds because "the GIL blocks sleeping threads".

### Q. A Node.js service hashes uploaded files on a worker_threads pool and calls three APIs with Promise.all. Port the design to Python and explain where each piece of work runs.
**Short answer (45 seconds):** The three API calls are network waits, so in an async Python service they become `asyncio.gather` over an async HTTP client, running on the event loop exactly as they did on Node's main thread. The hashing is CPU work: Node moved it to worker_threads, and in Python I would run it in a thread pool, because hashlib releases the GIL for large buffers. If the CPU step were pure Python, I would use a process pool instead.

**Deeper explanation:** The Node original:

```js
const [user, plan, usage] = await Promise.all([getUser(id), getPlan(id), getUsage(id)]);
const digest = await pool.run(fileBuffer);   // piscina pool of worker_threads
```

The Python port:

```python
import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor

hash_pool = ThreadPoolExecutor(max_workers=4)       # create once, at startup

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()         # releases the GIL for large inputs

async def handle(user_id: int, data: bytes) -> dict:
    user, plan, usage = await asyncio.gather(        # three network waits overlap
        get_user(user_id), get_plan(user_id), get_usage(user_id))
    loop = asyncio.get_running_loop()
    digest = await loop.run_in_executor(hash_pool, sha256, data)
    return {"user": user, "plan": plan, "usage": usage, "sha256": digest}
```

Where the work runs in each runtime:

| Work | Node.js | Python |
|---|---|---|
| HTTP calls | main thread, sockets on epoll or kqueue | event loop thread, sockets on the selector |
| Hashing a large file | worker_threads, a separate heap | pool thread, same heap, GIL released |
| Pure-Python CPU work | worker_threads | `ProcessPoolExecutor`, a separate process |
| Using more cores for requests | cluster or PM2 | `uvicorn --workers` or Gunicorn |

A Python thread shares memory with the caller, so passing `data` costs nothing, while a process pool would pickle and copy it. That is why threads win here even though the work is CPU.

**Follow-ups they will ask:**
- What if the hash ran directly inside `async def`? : a large file would block the loop and freeze every request on that worker until it finished.
- Python's version of transferring an ArrayBuffer? : threads already share memory; across processes, `multiprocessing.shared_memory`.
- Why not raise the pool to 64 threads? : hashing is bounded by cores, so beyond the core count threads only wait for each other.

**Mistakes to avoid:**
- Treating Python threads as worker_threads: they share one heap and one GIL.
- Sending small, fast tasks to a process pool, where pickling costs more than the work.

### Practice
- Practice kit: open `python-practice/exercises/p17_concurrency.py`, implement each function, then run `uv run --with pytest pytest tests/test_p17_concurrency.py` from the `python-practice` folder.
- Run the counter race from the walkthrough five times without the lock and five times with it, and print each total; then remove `time.sleep(0)` and see how rarely the plain loop shows the bug on your version.
- Time the `busy` function from the prediction question with 1, 2 and 4 threads, then 1, 2 and 4 processes, and write down how the totals scale.
- In the REPL, call `pickle.dumps` on a lambda, a nested function, `functools.partial(abs, -1)`, a `threading.Lock()` and a generator; note which fail and with which exception.

## Async Python with asyncio [Advanced]

> This is the API behind every `async def` FastAPI endpoint, every agent that runs tools in parallel, and every script that fans out hundreds of LLM calls. The architecture track explains how the event loop schedules coroutines; this section is the code you write on top of it. Interviewers ask you to write concurrent code with a concurrency limit, a timeout and clean cancellation, and to spot the classic bugs: a missing `await`, a blocking call on the loop, a background task that vanishes.

### Why it exists
Threads can overlap a few hundred waits, but each costs an OS thread and a stack, and because the OS can switch threads at any moment, every shared variable is a potential race. asyncio (in the standard library since 3.4, with `async` and `await` syntax since 3.5) runs thousands of waits on one thread by letting each coroutine say exactly where it may pause, so switching is cooperative, cheap, and only ever happens at an `await`. That fits AI backends, which spend most of their time waiting on LLM APIs, vector stores and HTTP services. The cost is that everything in the call path must be async-aware, a single blocking call stalls every task on the loop, and task lifetimes, timeouts and cancellation become your job.

### In plain words
Think of a chess master playing 30 boards at once. She makes a move on one board and walks to the next while that opponent thinks; the walking is the event loop, each board is a task, and the opponent thinking is I/O. `await` is the moment she says "your move" and steps away. If she stops at one board for a long phone call (a blocking call), all 30 games freeze. A Semaphore is a house rule like "at most 5 boards active at once", and a timeout is "if an opponent takes more than ten minutes, that game is over".

### Walkthrough: from coroutine to concurrent tasks
1. **`async def` makes a coroutine function.** Calling it runs none of the body; it returns a coroutine object that waits to be driven. In JavaScript, calling an async function runs it up to the first `await` and returns a Promise that is already in motion.

   ```python
   import asyncio

   async def fetch_user(uid: int) -> dict:
       await asyncio.sleep(0.1)          # stands in for a network call
       return {"id": uid}

   coro = fetch_user(1)                  # nothing has run yet
   print(type(coro).__name__)            # coroutine
   coro.close()                          # avoids "coroutine 'fetch_user' was never awaited"
   ```

2. **`asyncio.run` starts the loop**, once, at the program's entry point. It creates a loop, runs your coroutine, cancels any tasks still pending, and closes the loop. Under FastAPI, Uvicorn already runs the loop, so you never call it there.

   ```python
   async def main() -> None:
       user = await fetch_user(1)        # await drives the coroutine to its result
       print(user)

   asyncio.run(main())                   # RuntimeError if called inside a running loop
   ```

3. **Consecutive awaits are sequential.** Each `await` waits for its result before the next line runs, so two 100 ms calls take 200 ms.

   ```python
   async def main() -> None:
       a = await fetch_user(1)           # 0.1 s
       b = await fetch_user(2)           # another 0.1 s: about 0.2 s in total
   ```

4. **`create_task` makes them concurrent.** A Task wraps a coroutine and schedules it on the loop; it starts running at the next point where the current code awaits.

   ```python
   async def main() -> None:
       t1 = asyncio.create_task(fetch_user(1))   # scheduled now
       t2 = asyncio.create_task(fetch_user(2))
       a = await t1                              # both run while we wait here
       b = await t2                              # about 0.1 s in total
   ```

5. **`gather` runs a batch.** Results come back in argument order. If one raises, `gather` raises that first exception at once, but the other awaitables keep running and are not cancelled. `return_exceptions=True` returns exceptions as values instead, like `Promise.allSettled`.

   ```python
   users = await asyncio.gather(*(fetch_user(i) for i in range(10)))   # input order
   results = await asyncio.gather(call_a(), call_b(), return_exceptions=True)
   errors = [r for r in results if isinstance(r, Exception)]
   ```

6. **`TaskGroup` (3.11+) is structured concurrency.** No task outlives the `async with` block. If any task fails, the group cancels its siblings, waits for them, and raises an `ExceptionGroup`, which you handle with `except*` (3.11+).

   ```python
   async def main() -> None:
       try:
           async with asyncio.TaskGroup() as tg:
               profile = tg.create_task(fetch_user(1))
               orders = tg.create_task(fetch_orders(1))
           print(profile.result(), orders.result())   # both done once the block exits
       except* TimeoutError as eg:
           log.warning("upstream timed out: %s", eg.exceptions)
   ```

7. **Every task needs an owner.** The event loop keeps only weak references to tasks, so a task nobody references can be garbage collected before it finishes. Keep a strong reference until it is done, or let a TaskGroup own it.

   ```python
   background: set[asyncio.Task] = set()

   def spawn(coro) -> asyncio.Task:
       task = asyncio.create_task(coro)
       background.add(task)                        # strong reference
       task.add_done_callback(background.discard)  # dropped once finished
       return task
   ```

### Walkthrough: timeouts, cancellation and limits
1. **`asyncio.timeout` (3.11+) puts a deadline on a block.** When the deadline passes, the task is cancelled at its current `await` and the block raises the built-in `TimeoutError`.

   ```python
   async def answer(prompt: str) -> str:
       try:
           async with asyncio.timeout(10):          # everything inside: 10 s total
               return await llm.complete(prompt)
       except TimeoutError:
           return "The model is busy, please retry."
   ```

2. **`wait_for` puts a deadline on one awaitable**, and works on older versions. It cancels the awaitable on timeout. Before 3.11 it raised `asyncio.TimeoutError`; from 3.11 that name is an alias of the built-in `TimeoutError`.

   ```python
   reply = await asyncio.wait_for(llm.complete(prompt), timeout=10)
   ```

3. **Cancellation is an exception.** `task.cancel()` raises `asyncio.CancelledError` inside the task at the `await` where it is paused. Since 3.8 it subclasses `BaseException`, so `except Exception` does not catch it. Clean up in `finally` and let it propagate.

   ```python
   async def relay(stream) -> None:
       try:
           async for chunk in stream:
               await send(chunk)
       except asyncio.CancelledError:
           log.info("client went away")
           raise                                    # always re-raise
       finally:
           await stream.aclose()                    # runs on cancel too

   task = asyncio.create_task(relay(stream))
   task.cancel()                                    # CancelledError at its current await
   ```

   `asyncio.shield(aw)` protects an inner awaitable from an outer cancellation, for cleanup that must finish, such as writing an audit row.

4. **`asyncio.Semaphore` limits concurrency**, for example at most 5 LLM calls in flight. Tasks beyond the limit wait at `async with` and cost almost nothing while they wait.

   ```python
   llm_slots = asyncio.Semaphore(5)

   async def summarize(doc: str) -> str:
       async with llm_slots:                        # waits while 5 calls are running
           return await llm.complete("Summarize:\n" + doc)

   summaries = await asyncio.gather(*(summarize(d) for d in docs))   # 200 docs, 5 at a time
   ```

5. **`asyncio.Queue` connects producers and consumers.** `maxsize` makes `await q.put()` wait while the queue is full, `task_done()` marks an item finished, and `await q.join()` waits until every item is.

   ```python
   async def worker(q: asyncio.Queue[str], out: list[str]) -> None:
       while True:
           url = await q.get()
           try:
               out.append(await fetch(url))
           finally:
               q.task_done()

   async def crawl(urls: list[str]) -> list[str]:
       q: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
       out: list[str] = []
       workers = [asyncio.create_task(worker(q, out)) for _ in range(3)]
       for u in urls:
           await q.put(u)
       await q.join()                               # every url processed
       for w in workers:
           w.cancel()
       await asyncio.gather(*workers, return_exceptions=True)
       return out
   ```

   asyncio's Queue, Lock and Semaphore are not thread-safe; use them only from the loop's thread. Python 3.13 added `asyncio.Queue.shutdown()`.

6. **`asyncio.to_thread` (3.9+) runs blocking code off the loop.** It sends a sync function to the loop's default thread pool and awaits the result, so other tasks keep running.

   ```python
   import boto3

   s3 = boto3.client("s3")

   def _download(key: str) -> bytes:
       return s3.get_object(Bucket="docs", Key=key)["Body"].read()   # blocking

   async def load_object(key: str) -> bytes:
       return await asyncio.to_thread(_download, key)                # loop stays free
   ```

7. **`asyncio.wait` for "first one wins"**, the `Promise.race` pattern. Unlike JavaScript, you can and should cancel the losers.

   ```python
   tasks = {asyncio.create_task(ask(model)) for model in ("primary", "fallback")}
   done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
   for t in pending:
       t.cancel()                                   # stop paying for the slower call
   winner = done.pop().result()
   ```

### Walkthrough: async for, async with and the classic bugs
1. **`async with` calls `__aenter__` and `__aexit__`**, which can await, for things like HTTP clients, connection pools and transactions. `contextlib.asynccontextmanager` builds one from an async generator.

   ```python
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def timed(label: str):
       loop = asyncio.get_running_loop()
       start = loop.time()
       try:
           yield
       finally:
           log.info("%s took %.3fs", label, loop.time() - start)

   async with httpx.AsyncClient() as client, timed("search"):
       resp = await client.get(url)
   ```

2. **`async for` iterates an async iterator**, and an `async def` containing `yield` is an async generator. This is how LLM token streams are consumed; it is JavaScript's `for await`.

   ```python
   async def tokens(client: httpx.AsyncClient, prompt: str):
       async with client.stream("POST", "/generate", json={"prompt": prompt}) as resp:
           async for line in resp.aiter_lines():
               yield line                           # an async generator

   async for tok in tokens(client, "hi"):          # JS: for await (const tok of tokens(...))
       print(tok, end="")
   ```

3. **Bug: forgetting `await`.** You get a coroutine object instead of a result, the work never runs, and Python warns `RuntimeWarning: coroutine '...' was never awaited`. In an `if`, a coroutine object is always truthy, which turns a permission check into "allow everyone".

   ```python
   async def is_allowed(user_id: int) -> bool: ...

   if is_allowed(42):          # BUG: coroutine object, always truthy
       grant()
   if await is_allowed(42):    # correct
       grant()
   ```

   mypy reports an unused coroutine by default (`unused-coroutine`), and Pyright has the same check (`reportUnusedCoroutine`).

4. **Bug: blocking the loop.** `time.sleep`, `requests`, sync database drivers and long CPU loops inside `async def` stop every task on that loop. Debug mode logs any step slower than 100 ms.

   ```python
   async def bad() -> None:
       time.sleep(1)                               # freezes every task for 1 s
       requests.get(URL)                           # same problem

   async def good() -> None:
       await asyncio.sleep(1)
       await asyncio.to_thread(requests.get, URL)

   asyncio.run(main(), debug=True)                 # warns about slow steps
   ```

5. **Bug: fire-and-forget tasks.** A task with no reference can be garbage collected mid-flight (`Task was destroyed but it is pending!`), and a task whose exception nobody reads only logs `Task exception was never retrieved` when it is collected. Keep references, log failures in a done callback, and await leftover tasks at shutdown.

   ```python
   async def handler() -> None:
       asyncio.create_task(send_audit_event())     # BUG: unowned, errors unseen
       spawn(send_audit_event())                   # fixed: the spawn helper from the first walkthrough
   ```

   Ruff's rule RUF006 flags a `create_task` result that is not stored.

6. **Bug: swallowing cancellation.** A broad `except BaseException` or a bare `except:` also catches `CancelledError`, so timeouts silently stop working (the block runs past its deadline with no `TimeoutError`) and a TaskGroup cannot cancel the task.

   ```python
   try:
       await call_tool()
   except BaseException:            # BUG: also catches CancelledError
       log.exception("tool failed")

   try:
       await call_tool()
   except Exception:                # correct: CancelledError passes through
       log.exception("tool failed")
   ```

### Concepts you must understand
- A coroutine object does nothing until it is awaited or wrapped in a Task; a JavaScript Promise is already running when you receive it.
- `await` is sequential; concurrency needs tasks, created with `create_task`, `gather` or a `TaskGroup`.
- `gather` returns results in argument order; the first exception propagates but sibling tasks keep running, and `return_exceptions=True` gives `Promise.allSettled` behavior.
- `TaskGroup` (3.11+) guarantees no task outlives the block, cancels the siblings on the first failure, and raises an `ExceptionGroup` handled with `except*`.
- Cancellation is `CancelledError` (a `BaseException` since 3.8) raised at the task's current `await`: clean up in `finally`, re-raise, and never swallow it.
- `asyncio.timeout` (3.11+) bounds a block and `wait_for` bounds one awaitable; both cancel the work and raise the built-in `TimeoutError`, and neither can interrupt code that never awaits.
- `Semaphore` caps operations in flight and a bounded `asyncio.Queue` gives backpressure; both are per process and not thread-safe.
- The loop holds only weak references to tasks: keep a strong reference until done, or use a TaskGroup.
- Never block the loop: send sync I/O to `asyncio.to_thread`, CPU work to a process pool with `run_in_executor`, or switch to an async library.

| JavaScript | Python | Note |
|---|---|---|
| `async function f()` | `async def f()` | calling the Python one returns a lazy coroutine |
| `Promise.all([...])` | `asyncio.gather(...)` or `TaskGroup` | TaskGroup cancels the rest on failure; neither JS nor gather does |
| `Promise.allSettled([...])` | `gather(..., return_exceptions=True)` | exceptions come back as values |
| `Promise.race([...])` | `asyncio.wait(..., return_when=FIRST_COMPLETED)` | then cancel the pending tasks |
| `AbortController` and `signal` | `task.cancel()` | no signal to pass around: CancelledError appears at the await |
| `AbortSignal.timeout(5000)` | `async with asyncio.timeout(5)` | seconds, not milliseconds |
| `for await (const x of it)` | `async for x in it` | async generators work in both |
| p-limit with a limit of 5 | `asyncio.Semaphore(5)` | |
| `await new Promise(r => setTimeout(r, 0))` | `await asyncio.sleep(0)` | yields control to other tasks |
| `unhandledRejection` | `Task exception was never retrieved` | Python logs it only when the task is garbage collected |
| Top-level `await` in ES modules | `asyncio.run(main())` | `python -m asyncio` gives a REPL with top-level await |

### Q. A RAG endpoint calls a vector search, a keyword search and a user-profile service one after another, 300 ms each. Rewrite it to run them concurrently, and decide what happens when one of them fails.
**Short answer (45 seconds):** All three calls are network waits, so running them concurrently cuts latency from the sum (about 900 ms) to the slowest one (about 300 ms). The failure policy is the real decision: the profile is optional and the two retrievers are partly redundant, so I would use `gather` with `return_exceptions=True`, degrade when one part fails, fail only when both retrievers fail, and put one overall timeout on the fan-out.

**Deeper explanation:**

```python
import asyncio
import logging

log = logging.getLogger(__name__)

async def retrieve(query: str, user_id: int) -> dict:
    async with asyncio.timeout(1.5):                  # budget for the whole fan-out
        vec, kw, profile = await asyncio.gather(
            vector_search(query),
            keyword_search(query),
            get_profile(user_id),
            return_exceptions=True,                   # allSettled semantics
        )
    parts = [p for p in (vec, kw) if not isinstance(p, BaseException)]
    if not parts:
        raise RuntimeError("both retrievers failed") from vec
    if isinstance(profile, BaseException):
        log.warning("profile unavailable: %r", profile)
        profile = {}
    return {"docs": [d for part in parts for d in part], "profile": profile}
```

When every part is mandatory, a TaskGroup fails fast instead and cancels the siblings, so no work continues after the request has already failed:

```python
async with asyncio.TaskGroup() as tg:
    v = tg.create_task(vector_search(query))
    k = tg.create_task(keyword_search(query))
docs = v.result() + k.result()
```

If the timeout fires, `gather` is cancelled, which cancels all three children, and `TimeoutError` reaches the caller, which can return a 504 or answer without retrieval. Each part is checked separately, so one bad dependency degrades the answer instead of failing it.

**Follow-ups they will ask:**
- Why not TaskGroup everywhere? : it is all-or-nothing; when partial results are useful, use `gather(return_exceptions=True)` or a try/except inside each task.
- One retriever only has a sync client: what now? : wrap that call in `asyncio.to_thread` so it cannot block the other two.
- Should the profile call get its own shorter timeout? : yes, wrap it in its own `asyncio.timeout(0.3)` so an optional dependency cannot use the whole budget.

**Mistakes to avoid:**
- Writing `await asyncio.create_task(a())` and then `await asyncio.create_task(b())`, which is still sequential.
- Using plain `gather` and assuming the other calls were cancelled when one raised; they keep running and their results are thrown away.
- Having no overall deadline, so one hung dependency hangs the request.

### Q. Write bounded_map: summarize 200 documents with an LLM, with at most 5 calls in flight because of the provider's concurrency limit, and return the summaries in input order.
**Short answer (45 seconds):** I would wrap each call in an `asyncio.Semaphore(5)` and run all of them with `gather`, which preserves input order. Two hundred waiting tasks are cheap, because a task blocked on the semaphore is just a small object. Retries with backoff go inside the per-item function, but the backoff sleep must happen outside the semaphore so a waiting retry does not hold one of the five slots.

**Deeper explanation:**

```python
import asyncio
from collections.abc import Awaitable, Callable

async def bounded_map[T, R](                  # PEP 695 generics: 3.12+
    func: Callable[[T], Awaitable[R]], items: list[T], limit: int = 5
) -> list[R]:
    sem = asyncio.Semaphore(limit)

    async def run_one(item: T) -> R:
        async with sem:                       # at most `limit` calls past this line
            return await func(item)

    return await asyncio.gather(*(run_one(i) for i in items))
```

With retries:

```python
sem = asyncio.Semaphore(5)

async def summarize(doc: str, attempts: int = 3) -> str:
    for attempt in range(attempts):
        try:
            async with sem:
                return await llm.complete("Summarize:\n" + doc)
        except RateLimitError:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)   # slot released while backing off
```

Wall time is roughly ceil(n / limit) x call latency. An empty list returns `[]`, because `gather()` with no arguments gives an empty list. `limit` must be at least 1, since `Semaphore(0)` would block every call forever. For a million items, creating a million tasks up front costs real memory, so switch to a fixed set of workers reading from a bounded `asyncio.Queue`.

**Follow-ups they will ask:**
- The provider limits tokens per minute, not concurrency: what changes? : add a token bucket (for example aiolimiter) in front of the call and honor the `Retry-After` header on 429 responses.
- What if one document fails? : `gather` raises the first error while the others keep running; catch inside `run_one` to return a marker, or use `return_exceptions=True`.
- Does the limit hold across 4 Uvicorn workers? : no, a semaphore is per process; a global limit needs Redis or a gateway in front of the provider.

**Mistakes to avoid:**
- Putting the semaphore around the whole `gather`, which limits nothing.
- Sleeping for backoff while holding the semaphore.
- Using `threading.Semaphore` in async code, which blocks the event loop.

### Q. An agent's web-search tool sometimes hangs forever and the whole agent run hangs with it. Add a 10-second timeout, make sure the hung call is really cancelled, and return a fallback the model can act on.
**Short answer (45 seconds):** I would wrap the tool call in `asyncio.timeout(10)`, catch `TimeoutError`, and return a structured error result the agent loop feeds back to the model, so it can retry with a narrower query or answer without search. Cancellation only works if the tool is awaiting async I/O, so I would also check that the tool uses an async client with its own timeouts and does not call blocking code.

**Deeper explanation:**

```python
import asyncio
import logging

log = logging.getLogger(__name__)

async def run_tool(name: str, args: dict, timeout_s: float = 10.0) -> dict:
    try:
        async with asyncio.timeout(timeout_s):
            result = await TOOLS[name](**args)
        return {"ok": True, "result": result}
    except TimeoutError:
        log.warning("tool %s timed out after %ss", name, timeout_s)
        return {"ok": False, "error": f"{name} timed out after {timeout_s}s; try a narrower query"}
    except Exception as exc:                  # not BaseException: CancelledError must pass
        log.exception("tool %s failed", name)
        return {"ok": False, "error": f"{name} failed: {exc}"}

async def web_search(query: str) -> list[dict]:
    resp = await http.get(SEARCH_URL, params={"q": query}, timeout=8.0)   # httpx
    return resp.json()["results"]
```

When the deadline passes, the timeout cancels the current task: `CancelledError` is raised at the `await http.get(...)`, httpx closes the connection as the exception unwinds, every `finally` block runs, and the context manager turns the cancellation into `TimeoutError`. Three things defeat this. A blocking call such as `requests.get` or `time.sleep` keeps the loop busy, so the timeout cannot fire until it returns. A tool run with `asyncio.to_thread` stops being awaited, but its thread keeps running, because threads cannot be killed. And a tool that catches `BaseException` swallows the cancellation, so the block simply runs past its deadline.

**Follow-ups they will ask:**
- How do you cap the whole agent run? : wrap the agent loop in an outer `asyncio.timeout`; timeouts nest and the inner one fires first.
- Cleanup must finish even on timeout? : put it in `finally`, and wrap anything that must complete in `asyncio.shield`.
- Why return the error instead of raising? : the model can choose another tool or answer with what it has, while an exception ends the whole run.

**Mistakes to avoid:**
- A timeout around blocking code, which cannot fire.
- `except BaseException` or a bare `except:` in tool code.
- Relying only on the outer timeout and giving the HTTP client no timeout of its own.

### Q. This audit code prints "logged" but rows never reach the database, and production logs show "Task was destroyed but it is pending!" and "coroutine 'write_audit' was never awaited". Find and fix the bugs.
**Short answer (45 seconds):** There are two bugs. The admin path calls `write_audit(...)` without `await`, so it only creates a coroutine object that is thrown away. The other path starts a task with `create_task` and keeps no reference, so the task can be garbage collected mid-flight, and any exception it raises goes unseen. I would await the write that must be durable, and give best-effort tasks an owner that logs failures and is drained at shutdown.

**Deeper explanation:** The buggy code:

```python
async def write_audit(event: dict) -> None:
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO audit (data) VALUES ($1)", json.dumps(event))

async def handle(req) -> dict:
    if req.user.is_admin:
        write_audit({"user": req.user.id, "path": req.path})      # bug 1: no await
    asyncio.create_task(write_audit({"path": req.path}))          # bug 2: unowned task
    print("logged")
    return {"ok": True}
```

The fix:

```python
_background: set[asyncio.Task] = set()

def _on_done(task: asyncio.Task) -> None:
    _background.discard(task)
    if not task.cancelled() and task.exception() is not None:
        log.error("audit write failed", exc_info=task.exception())

def spawn(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _background.add(task)                     # strong reference until done
    task.add_done_callback(_on_done)
    return task

async def handle(req) -> dict:
    if req.user.is_admin:
        await write_audit({"user": req.user.id, "path": req.path})   # must not be lost
    spawn(write_audit({"path": req.path}))                          # best effort
    return {"ok": True}
```

At shutdown, in the FastAPI lifespan, `await asyncio.gather(*_background, return_exceptions=True)` drains what is still running. For events that must never be lost, even in a crash, an in-process task is the wrong tool: write to an outbox table in the same transaction, or publish to a durable queue. mypy's `unused-coroutine` check and asyncio debug mode both catch bug 1 before production does.

**Follow-ups they will ask:**
- Would FastAPI `BackgroundTasks` work? : yes for best effort; it runs after the response in the same process and is lost if the process dies.
- Why can a running task be garbage collected? : the loop keeps only weak references; a task paused on a Future with no other reference can be collected.
- Where else does a missing `await` hide? : in conditions, where a coroutine object is always truthy, so `if has_access(user):` grants access to everyone.

**Mistakes to avoid:**
- Adding `await asyncio.sleep(0)` after `create_task` and calling it fixed.
- Keeping tasks in a list that is never cleaned, which leaks memory.

### Q. Build an async ingestion pipeline: a producer pages through an API, three workers embed each document, and the pipeline must stop cleanly when the producer finishes or when any worker crashes.
**Short answer (45 seconds):** I would connect producer and workers with a bounded `asyncio.Queue` for backpressure, have the producer send one sentinel per worker when it runs out of pages, and run everything inside a TaskGroup. If any worker raises, the TaskGroup cancels the producer and the other workers, so nothing deadlocks on a full queue, and the error surfaces as an `ExceptionGroup`.

**Deeper explanation:**

```python
import asyncio

_DONE = object()

async def producer(q: asyncio.Queue, n_workers: int) -> None:
    cursor = None
    while True:
        page, cursor = await fetch_page(cursor)
        for doc in page:
            await q.put(doc)                    # waits while 100 docs are queued
        if cursor is None:
            break
    for _ in range(n_workers):
        await q.put(_DONE)                      # one stop signal per worker

async def worker(q: asyncio.Queue, out: list) -> None:
    while (doc := await q.get()) is not _DONE:
        out.append(await embed(doc))            # an exception here fails the group

async def ingest(n_workers: int = 3) -> list:
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    out: list = []
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q, n_workers))
        for _ in range(n_workers):
            tg.create_task(worker(q, out))
    return out
```

The bounded queue means the producer never fetches more than 100 documents ahead of embedding, so memory stays flat however many pages exist. Sentinels let each worker finish its last document and exit on its own, and an empty API sends only sentinels, so the pipeline ends immediately. The TaskGroup is what prevents the classic hang: with plain `create_task` calls and a dead worker, the producer can block forever on `q.put()` into a full queue that nobody drains. On 3.13+, `q.shutdown()` can replace the sentinels.

**Follow-ups they will ask:**
- One bad document should not stop the run: how? : catch per item inside the worker and send failures to a dead-letter list, so only infrastructure errors fail the group.
- How do you resume after a crash? : persist the cursor and use idempotent upserts keyed by document ID, so reprocessing a page is harmless.
- Embedding uses a local CPU model: what changes? : workers call `loop.run_in_executor` with a process pool, or call a separate embedding service.

**Mistakes to avoid:**
- An unbounded queue, which lets the producer pull the whole dataset into memory.
- One sentinel for three workers, which leaves two waiting forever.
- `gather` over producer and workers with no cancellation on failure, which hangs when a worker dies.

### Q. Rewrite this JavaScript in idiomatic Python: it fetches several URLs in parallel under one 5-second deadline, then streams another response to stdout.
**Short answer (45 seconds):** `Promise.all` becomes a TaskGroup, `AbortSignal.timeout(5000)` becomes `async with asyncio.timeout(5)`, and `for await` becomes `async for` over httpx's streaming API. The biggest difference is cancellation: in JavaScript the signal must be passed to every fetch, while in Python the timeout cancels whatever is awaiting inside the block, with no plumbing.

**Deeper explanation:** The JavaScript:

```js
async function load(urls) {
  const signal = AbortSignal.timeout(5000);            // one deadline for everything
  const res = await Promise.all(urls.map((u) => fetch(u, { signal })));
  return Promise.all(res.map((r) => r.json()));
}

async function tail(url) {
  const res = await fetch(url);
  for await (const chunk of res.body) process.stdout.write(chunk);
}
```

The Python:

```python
import asyncio
import sys
import httpx

async def load(client: httpx.AsyncClient, urls: list[str]) -> list[dict]:
    async with asyncio.timeout(5):                   # no signal to pass around
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(client.get(u)) for u in urls]
    return [t.result().json() for t in tasks]        # body already read, so .json() is sync

async def tail(client: httpx.AsyncClient, url: str) -> None:
    async with client.stream("GET", url) as resp:
        async for text in resp.aiter_text():
            sys.stdout.write(text)

async def main() -> None:
    async with httpx.AsyncClient() as client:        # one pooled client, like a keep-alive agent
        print(await load(client, ["https://a.example/x", "https://b.example/y"]))
        await tail(client, "https://a.example/stream")

asyncio.run(main())
```

If the deadline passes, the timeout cancels the task, the TaskGroup cancels every pending `client.get`, and `TimeoutError` comes out of `load`. If one request fails first, the TaskGroup cancels the others, which `Promise.all` never does. Units differ (seconds, not milliseconds), and a Python script needs an explicit `asyncio.run` where an ES module can use top-level `await`.

**Follow-ups they will ask:**
- What is the Python `Promise.any`? : there is none built in; loop over `asyncio.as_completed`, return the first success, and cancel the rest.
- Why share one AsyncClient? : it pools connections; creating one per request repeats TCP and TLS handshakes.
- Where does this client live in FastAPI? : created in the lifespan handler and closed on shutdown.

**Mistakes to avoid:**
- Translating `fetch` to `requests.get` inside `async def`, which blocks the loop.
- Writing `asyncio.timeout(5000)`, which waits 83 minutes.

### Practice
- Practice kit: open `python-practice/exercises/p18_asyncio.py`, implement each function, then run `uv run --with pytest pytest tests/test_p18_asyncio.py` from the `python-practice` folder.
- In the REPL started with `python -m asyncio`, time two `await asyncio.sleep(0.5)` calls in sequence, then the same two with `gather`, and explain the difference.
- Run a coroutine that calls `time.sleep(0.3)` under `asyncio.run(main(), debug=True)` and read the slow-step warning; then replace it with `await asyncio.to_thread(time.sleep, 0.3)`.
- Write a task with a `finally` block, cancel it, and confirm the cleanup runs; then catch `CancelledError` without re-raising inside `asyncio.timeout(0.1)` and watch the timeout stop working.

## Python Internals & Performance [Advanced]

> Interviewers use internals questions to tell people who write Python from people who understand it. They show up as real problems: an ingestion job that deduplicates IDs in quadratic time, a cache keyed by an unhashable object, a worker whose memory triples when it loads a JSONL file, a slow similarity search, an `lru_cache` that leaks. A strong answer reasons from the object model (names, references, hash tables, dynamic arrays), measures before changing anything, and knows when to leave pure Python for NumPy.

### Why it exists
Python trades raw speed for simplicity: every value, even a small integer, is a heap object with a type and a reference count, so a float takes 24 bytes instead of 8 and every operation goes through the interpreter. Knowing that model explains most performance surprises and many bugs, such as aliasing, unhashable keys and memory blow-ups. Python also ships the tools to measure (timeit, cProfile, tracemalloc), so you can find the real hot spot instead of guessing. The cost of all this flexibility is that heavy numeric loops belong in C-backed libraries such as NumPy, not in tuned Python.

### In plain words
Think of a warehouse full of boxes (objects) and sticky notes (names). A name is a note stuck on a box, and two notes can sit on the same box, so changing the box through one note shows through the other. Every box counts the notes on it, and when the count reaches zero the box is thrown out at once; a cleaner also sweeps now and then for boxes that only point at each other. Dicts and sets are a wall of numbered lockers: hashing a key tells you which locker to open, so a lookup takes the same time with ten items or ten million. Profiling is walking the floor with a stopwatch before you rearrange anything.

### Walkthrough: names, objects and references
1. **Everything is an object.** Integers, functions, classes and modules all have a type, an identity and attributes. There are no primitives in the JavaScript sense.

   ```python
   def greet() -> None: ...

   print(type(42), type(greet), type(int))   # <class 'int'> <class 'function'> <class 'type'>
   print((42).bit_length(), greet.__name__)  # even ints have methods: 6 greet
   ```

2. **Names are references, and assignment never copies.** Two names can point at one list. For immutable objects such as ints and strings, `+=` rebinds the name to a new object instead.

   ```python
   a = [1, 2]
   b = a                 # same list, two names
   b.append(3)
   print(a)              # [1, 2, 3]
   c = a.copy()          # shallow copy; copy.deepcopy for nested data

   x = 10
   y = x
   y += 1                # ints are immutable: y now names a new object, x is still 10
   ```

3. **`id()` and `is` test identity; `==` tests value.** `id()` is unique among objects alive at the same time (in CPython it is the memory address), and can be reused after an object dies. Use `is` only for `None` and sentinel objects.

   ```python
   a = [1, 2]
   b = [1, 2]
   print(a == b, a is b)     # True False: equal values, different objects
   print(id(a) == id(b))     # False
   print(a is not None)      # the idiomatic None check
   ```

4. **Reference counting frees memory immediately.** Each object counts the references to it, and CPython frees it the moment the count reaches zero. `del` removes a name, not an object.

   ```python
   import sys

   data = [0] * 1_000_000
   alias = data
   print(sys.getrefcount(data))   # includes one temporary reference for the call itself
   del data                       # removes a name; the list lives on through alias
   alias = None                   # count reaches zero: freed right here, in CPython
   ```

5. **Cycles need the garbage collector.** Objects that refer to each other never reach a count of zero, so the `gc` module's cycle collector finds unreachable groups and frees them. `weakref` avoids the cycle for back-references and caches.

   ```python
   import gc

   class Node:
       def __init__(self) -> None:
           self.parent: "Node | None" = None
           self.children: list["Node"] = []

   root, child = Node(), Node()
   root.children.append(child)
   child.parent = root          # a cycle: neither count can reach zero
   del root, child
   print(gc.collect())          # finds and frees them; returns how many objects it found
   ```

6. **Small-int caching and string interning are details you must not rely on.** CPython keeps one shared object for each int from -5 to 256 and interns many identifier-like strings, which makes `is` look like it works by accident.

   ```python
   a, b = int("256"), int("256")
   print(a is b)                 # True: cached small int
   a, b = int("257"), int("257")
   print(a is b, a == b)         # False True: two objects with equal values
   s = "".join(["user", "_id"])
   print(s == "user_id")         # True: always compare values with ==
   ```

   Writing `x is "user_id"` even triggers `SyntaxWarning: "is" with 'str' literal`. Literals that appear twice in the same compiled block can share one constant, so `x = 1000; y = 1000; x is y` may print True in a script and False when typed line by line in the REPL.

### Walkthrough: hashing, dicts, sets and lists
1. **Hashable means a stable hash that agrees with equality.** If `a == b`, then `hash(a) == hash(b)` must hold, and the hash must not change while the object is a key. Immutable built-ins are hashable; lists, dicts and sets are not, and a tuple is hashable only if everything inside it is.

   ```python
   hash("a"), hash(3), hash((1, 2)), hash(frozenset({1}))   # all fine
   hash([1, 2])         # TypeError: unhashable type: 'list'
   hash((1, [2]))       # TypeError: unhashable type: 'list'
   ```

2. **dict and set are hash tables.** The hash picks a slot, so lookup, insert and delete are O(1) on average (O(n) only with pathological collisions). Dicts keep insertion order, guaranteed since 3.7; sets do not keep any order.

   ```python
   seen: set[str] = set()
   for doc_id in ids:
       if doc_id in seen:            # O(1) average, not a scan
           continue
       seen.add(doc_id)

   by_id = {doc["id"]: doc for doc in docs}   # O(n) once, then O(1) lookups
   ```

3. **Custom classes**: by default an instance hashes by identity. Defining `__eq__` without `__hash__` sets `__hash__` to `None`, making the class unhashable on purpose. A frozen dataclass generates both from its fields.

   ```python
   from dataclasses import dataclass

   class P:
       def __init__(self, x: int) -> None:
           self.x = x
       def __eq__(self, other: object) -> bool:
           return isinstance(other, P) and other.x == self.x
   # {P(1): "a"} raises TypeError: unhashable type: 'P'

   @dataclass(frozen=True)
   class Point:
       x: int
       y: int

   cache = {Point(1, 2): "hit"}
   print(cache[Point(1, 2)])        # hit: equal fields, equal hashes
   ```

4. **Never mutate an object while it is a key.** The entry stays in the slot chosen by the old hash, so neither the old nor the new value finds it.

   ```python
   class Key:
       def __init__(self, name: str) -> None:
           self.name = name
       def __eq__(self, other: object) -> bool:
           return isinstance(other, Key) and self.name == other.name
       def __hash__(self) -> int:
           return hash(self.name)

   k = Key("a")
   d = {k: 1}
   k.name = "b"
   print(Key("b") in d, Key("a") in d)   # False False: the entry is unreachable
   ```

   String hashes are randomized per process (see `PYTHONHASHSEED`), so never store `hash()` values or use them as cache keys across processes; use `hashlib` for stable digests.

5. **list is a dynamic array of pointers.** Indexing is O(1). `append` over-allocates spare capacity, so it is O(1) amortized and the size jumps only now and then. Inserting or popping at the front shifts every element: O(n).

   ```python
   import sys

   items: list[int] = []
   last = sys.getsizeof(items)
   for i in range(20):
       items.append(i)
       if (size := sys.getsizeof(items)) != last:
           print(f"len={len(items)} bytes={size}")   # grows in steps, not on every append
           last = size
   ```

6. **Use deque for queues.** `collections.deque` gives O(1) appends and pops at both ends; `maxlen` turns it into a ring buffer that drops the oldest items.

   ```python
   from collections import deque

   recent = deque(maxlen=1000)    # last 1,000 events
   recent.append("event")
   jobs = deque(["a", "b"])
   first = jobs.popleft()         # O(1); list.pop(0) would be O(n)
   ```

Cost of common operations in CPython (average case; n is the container size, k the size of the slice or other argument):

| Operation | Cost | Note |
|---|---|---|
| `lst[i]`, `lst[i] = x`, `len(lst)` | O(1) | |
| `lst.append(x)`, `lst.pop()` | O(1) amortized | spare capacity at the end |
| `lst.insert(0, x)`, `lst.pop(0)` | O(n) | shifts every element; use deque |
| `x in lst`, `lst.index(x)`, `lst.remove(x)` | O(n) | linear scan |
| `lst[a:b]` | O(k) | copies k references |
| `lst.sort()`, `sorted(it)` | O(n log n) | Timsort, stable |
| `d[k]`, `d[k] = v`, `k in d`, `del d[k]` | O(1) average | O(n) worst case |
| `s.add(x)`, `x in s`, `s.discard(x)` | O(1) average | |
| `s.union(t)`, `s.intersection(t)` | O(len(s) + len(t)), O(min(len(s), len(t))) | |
| `dq.append`, `dq.appendleft`, `dq.popleft` | O(1) | indexing the middle of a deque is O(n) |
| `heapq.heappush`, `heapq.heappop` | O(log n) | min-heap on a list |
| `bisect.bisect_left(sorted_lst, x)` | O(log n) | `bisect.insort` is O(n) because of the insert |
| `"".join(parts)` | O(total length) | building a string with `+=` in a loop can be quadratic |

### Walkthrough: measure, then optimize
1. **`time.perf_counter` for wall time.** It is monotonic and high resolution, unlike `time.time()`, which can jump when the clock is adjusted.

   ```python
   import time

   t0 = time.perf_counter()
   result = rank(docs, query)
   print(f"rank took {(time.perf_counter() - t0) * 1000:.1f} ms")
   ```

2. **`timeit` for micro-benchmarks.** It runs a statement many times and turns off garbage collection during the run, so comparisons are fair.

   ```python
   import timeit

   setup = "data = list(range(10_000)); s = set(data)"
   print(timeit.timeit("9_999 in data", setup=setup, number=1_000))   # list scan
   print(timeit.timeit("9_999 in s", setup=setup, number=1_000))      # hash lookup
   # shell: python -m timeit -s "data = list(range(10_000))" "9_999 in data"
   ```

3. **`cProfile` to find where time goes.** It records every function call: `tottime` is time inside the function itself, and `cumtime` includes everything it called. It adds overhead, so for a live production process use a sampling profiler such as py-spy.

   ```python
   import cProfile
   import pstats

   with cProfile.Profile() as prof:              # context manager form: 3.8+
       build_index(docs)
   pstats.Stats(prof).sort_stats("cumulative").print_stats(10)
   # shell: python -m cProfile -s cumtime ingest.py
   ```

4. **Memory: `sys.getsizeof` is shallow, tracemalloc is real.** `getsizeof` counts only the object itself, not what it refers to. `tracemalloc` traces every allocation Python makes and reports current and peak bytes and the lines responsible.

   ```python
   import sys
   import tracemalloc

   tracemalloc.start()
   rows = [{"id": i, "text": "x" * 50} for i in range(100_000)]
   current, peak = tracemalloc.get_traced_memory()
   print(sys.getsizeof(rows))                  # only the list's pointer array
   print(f"traced: {current / 1e6:.1f} MB, peak {peak / 1e6:.1f} MB")
   for stat in tracemalloc.take_snapshot().statistics("lineno")[:3]:
       print(stat)                             # the top allocating lines
   tracemalloc.stop()
   ```

5. **`__slots__` for many small objects.** It replaces the per-instance `__dict__` with fixed storage, which saves memory per instance and forbids adding new attributes. `@dataclass(slots=True)` (3.10+) generates it for you.

   ```python
   class Token:
       __slots__ = ("text", "start", "end")

       def __init__(self, text: str, start: int, end: int) -> None:
           self.text, self.start, self.end = text, start, end

   t = Token("hi", 0, 2)
   t.score = 1.0                 # AttributeError: no __dict__ to hold new attributes
   ```

6. **Generators keep memory flat.** A generator produces one item at a time, so a pipeline over a 10 GB file holds one record, not a list of all of them.

   ```python
   import json

   def read_records(path: str):
       with open(path, encoding="utf-8") as f:
           for line in f:                      # one line in memory at a time
               yield json.loads(line)

   total = sum(r["tokens"] for r in read_records("chunks.jsonl"))   # no list built
   ```

7. **`lru_cache` for repeated pure calls.** It memoizes by arguments, which must be hashable. `maxsize` defaults to 128, `functools.cache` (3.9+) is unbounded, and `cache_info()` shows hits and misses.

   ```python
   from functools import lru_cache

   @lru_cache(maxsize=32)
   def get_tokenizer(name: str):
       return load_tokenizer(name)             # slow; same result for the same name

   get_tokenizer("cl100k_base")
   print(get_tokenizer.cache_info())           # CacheInfo(hits=0, misses=1, maxsize=32, currsize=1)
   ```

8. **NumPy when the hot loop is arithmetic over large arrays.** A NumPy array stores raw numbers contiguously, and one call runs the whole loop in compiled code instead of one bytecode at a time over boxed Python floats. It does not help with tiny arrays or per-element Python callbacks.

   ```python
   import numpy as np

   docs = np.asarray(doc_vectors, dtype=np.float32)   # shape (n, d), converted once
   q = np.asarray(query_vector, dtype=np.float32)
   scores = docs @ q / (np.linalg.norm(docs, axis=1) * np.linalg.norm(q))
   top5 = np.argsort(scores)[-5:][::-1]               # indices of the 5 best scores
   ```

### Concepts you must understand
- Every value is a heap object with a type, an identity and a reference count; names are references bound to objects, so assignment never copies.
- `==` compares values through `__eq__` and `is` compares identity; use `is` only for `None` and sentinels, because small-int caching (-5 to 256) and string interning are CPython details that make `is` look right by accident.
- CPython frees an object as soon as its reference count reaches zero; the `gc` module's cycle collector reclaims reference cycles, and `weakref` avoids them for caches and parent pointers.
- A hashable object needs a `__hash__` that agrees with `__eq__` and never changes while it is a key; lists, dicts and sets are unhashable, defining only `__eq__` makes a class unhashable, and `@dataclass(frozen=True)` produces a correct hash.
- dict and set are hash tables with O(1) average lookup, insert and delete; dicts keep insertion order (guaranteed since 3.7) and sets do not.
- list is a dynamic array: O(1) indexing and amortized O(1) append, but O(n) for `insert(0, x)`, `pop(0)` and `x in lst`; use deque for queues and a set for membership.
- Measure before optimizing: `perf_counter` for wall time, `timeit` for micro-benchmarks, cProfile for where time goes, tracemalloc for where memory goes; `sys.getsizeof` is shallow.
- `__slots__` removes the per-instance `__dict__`, which saves memory across millions of small objects; generators process one item at a time in constant memory.
- `lru_cache` memoizes pure functions with hashable arguments, per process, bounded by `maxsize` (128 by default); never cache mutable results callers can change, and never decorate an `async def` with it.
- Reach for NumPy when hot loops do arithmetic over large numeric arrays: the loop then runs in compiled code over contiguous typed memory.

| JavaScript | Python | Note |
|---|---|---|
| `===` on objects (identity) | `is` | Python's `==` calls `__eq__`, which compares values |
| Deep equality (lodash `isEqual`) | `==` on lists and dicts | built-in containers compare element by element |
| `Map` | `dict` | any hashable key; insertion ordered |
| `Set` | `set` | JS compares objects by identity; Python uses `__hash__` and `__eq__` |
| `Object.freeze` | tuple, frozenset, `@dataclass(frozen=True)` | freezing is shallow in both |
| `structuredClone(obj)` | `copy.deepcopy(obj)` | |
| `WeakMap`, `WeakRef` | `weakref.WeakKeyDictionary`, `weakref.ref` | |
| V8's tracing garbage collector | reference counting plus a cycle collector | CPython frees most objects immediately |
| `arr.shift()` | `deque.popleft()` | `list.pop(0)` is O(n) |
| `performance.now()` | `time.perf_counter()` | seconds as a float in Python |
| DevTools CPU profile, `node --prof` | cProfile, py-spy | |
| `Float32Array` | `numpy.ndarray` with `dtype=float32` | contiguous typed memory |

### Q. An ingestion job deduplicates 2 million document IDs with "if doc_id not in seen: seen.append(doc_id)" and runs for hours. Fix it and state the complexity before and after.
**Short answer (45 seconds):** `seen` is a list, so every `in` check scans it: O(n) per check and O(n^2) for the job, which for 2 million IDs is on the order of 10^12 comparisons. A set answers membership in O(1) on average through its hash table, which makes the whole job O(n). I would keep a set for membership and a list for the output, or use `dict.fromkeys` when the order of first appearance matters.

**Deeper explanation:**

```python
def dedupe(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for doc_id in ids:
        if doc_id not in seen:          # hash lookup: O(1) average
            seen.add(doc_id)
            out.append(doc_id)
    return out

# Same result in one line: dicts keep insertion order (3.7+)
unique = list(dict.fromkeys(ids))
```

With the list, the k-th check scans up to k items, so the total is about n^2 / 2 comparisons. With the set, each check hashes the ID once and looks in one slot, so the total is n operations plus the cost of hashing. Memory grows by the hash table, which holds references to the existing strings, not copies. `list(set(ids))` is also O(n) but loses the original order, which matters when the first occurrence carries meaning, such as the newest version of a document. An empty input returns an empty list.

When the items are dicts (unhashable), dedupe on a hashable key instead, such as `key = (doc["source"], doc["id"])`. When the IDs do not fit in memory, push the work to the store: a unique index with `INSERT ... ON CONFLICT DO NOTHING` in Postgres, a Redis set, or a Bloom filter if a small false-positive rate is acceptable.

**Follow-ups they will ask:**
- Is set lookup always O(1)? : on average; many keys hashing to the same slot degrade it toward O(n), and randomized string hashing makes that hard to trigger on purpose.
- How would you prove the fix? : time both versions with `perf_counter` at 10,000, 100,000 and 1,000,000 IDs; the list version grows about 100x per 10x input, the set version about 10x.
- What about 2 billion IDs? : shard by hash prefix, or sort externally and drop adjacent duplicates.

**Mistakes to avoid:**
- Writing `if doc_id not in set(seen)`, which rebuilds a set on every check and is still O(n) each time.
- Using `list(set(ids))` when the order of first appearance matters.

### Q. Predict the output of this code and explain each line.
**Short answer (45 seconds):** Line 1 prints `[1, 2, 3, 4]` because `b` is another name for the same list and `+=` extends it in place. Line 2 prints `([1, 2, 3, 4, 5], 'x')` because a tuple fixes which objects it holds, not their contents. Line 3 prints `True False`: equal values, two separate int objects. Line 4 prints three identical rows, because `* 3` copied one reference. Line 5 prints `unhashable type: 'list'`.

**Deeper explanation:** The code:

```python
a = [1, 2, 3]
b = a
b += [4]
print(a)                          # 1

c = (a, "x")
c[0].append(5)
print(c)                          # 2

x, y = int("1000"), int("1000")
print(x == y, x is y)             # 3

grid = [[0] * 3] * 3
grid[0][0] = 9
print(grid)                       # 4

t = ([1],)
try:
    print(hash(t))
except TypeError as e:
    print(e)                      # 5
```

1. `+=` on a list calls `__iadd__`, which extends the same object, so `a` sees the change. `b = b + [4]` would build a new list and leave `a` alone. JavaScript has no `+=` for arrays: `[1, 2] + [3]` there gives the string `"1,23"`.
2. The tuple holds a reference to the list, and the list is still mutable. Tuples are shallowly immutable, exactly like `Object.freeze`.
3. `int("1000")` builds a new object at runtime each time, and 1000 is outside the small-int cache (-5 to 256), so the identities differ even though the values are equal.
4. `[[0] * 3] * 3` makes an outer list holding the same inner list three times, so one write shows in every row: `[[9, 0, 0], [9, 0, 0], [9, 0, 0]]`. Build rows independently with `[[0] * 3 for _ in range(3)]`.
5. A tuple's hash combines the hashes of its items, and a list has none, so `hash(t)` raises `TypeError: unhashable type: 'list'` even though the tuple itself is immutable.

**Follow-ups they will ask:**
- Would `x = 1000; y = 1000; x is y` print the same? : not necessarily; equal literals compiled in one block can share a constant and print True, which is why `is` on numbers is never reliable.
- Does `copy.copy(grid)` fix line 4? : no, a shallow copy shares the inner lists; `copy.deepcopy` or a comprehension does.
- How do you make line 5 hashable? : use tuples all the way down, `([1],)` becomes `((1,),)`.

**Mistakes to avoid:**
- Assuming tuples are deeply immutable.
- Using `is` to compare numbers or strings.

### Q. You cache LLM responses in a dict keyed by a Query object. After someone adds __eq__, the code crashes with "TypeError: unhashable type: 'Query'", and an earlier version with a hand-written __hash__ silently missed the cache after a field was changed. Fix both.
**Short answer (45 seconds):** Python requires that equal objects have equal hashes, so defining `__eq__` without `__hash__` sets `__hash__` to `None`, and the class becomes unhashable on purpose. The earlier bug was a hash computed from mutable fields: changing a field after insertion leaves the entry in the slot for the old hash, where no lookup finds it. A frozen dataclass fixes both, because it generates `__eq__` and `__hash__` from the same fields and forbids changing them.

**Deeper explanation:** The broken class:

```python
class Query:
    def __init__(self, model: str, prompt: str, temperature: float) -> None:
        self.model, self.prompt, self.temperature = model, prompt, temperature

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Query) and (
            (self.model, self.prompt, self.temperature)
            == (other.model, other.prompt, other.temperature))
```

The fix:

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)          # slots=True needs 3.10+
class Query:
    model: str
    prompt: str
    temperature: float = 0.0

cache: dict[Query, str] = {}

async def complete(q: Query) -> str:
    if q in cache:
        return cache[q]
    answer = await llm.complete(q.model, q.prompt, q.temperature)
    cache[q] = answer
    return answer
```

Assigning to a field of a frozen dataclass raises `FrozenInstanceError`, so a key's hash can never change after insertion. Every field must itself be hashable: a `list[str]` of stop words makes `hash()` fail, so store a tuple. Watch floats too, since `0.1 + 0.2 == 0.3` is False, and two queries that look the same can be different keys. This dict also grows without limit; in production, bound it (an LRU or a TTL cache) or move it to Redis.

For a cache shared across processes, Python's `hash()` is the wrong key: string hashes are randomized per process. Build a stable digest instead, such as `hashlib.sha256(json.dumps(asdict(q), sort_keys=True).encode()).hexdigest()`.

**Follow-ups they will ask:**
- What does a plain `@dataclass` do here? : with the default `eq=True` and `frozen=False` it sets `__hash__` to `None`, so instances are unhashable unless you pass `unsafe_hash=True`.
- What if the class must stay mutable? : key the cache by an immutable tuple of the fields, or by a frozen copy made at lookup time.
- What does a constant `__hash__` (return 1) do? : it is correct but puts every key in one slot, turning lookups into O(n) scans.

**Mistakes to avoid:**
- Computing `__hash__` from fields that can change.
- Using `unsafe_hash=True` on a mutable dataclass to silence the error.

### Q. A worker that loads a 2 GB JSONL file of chunks with embeddings climbs to 9 GB of RAM and gets OOM-killed. Find where the memory goes and cut it.
**Short answer (45 seconds):** First I would measure with tracemalloc, which will point at the line that builds a list of every parsed record. Python objects carry headers and pointers, so a list of dicts holding strings and lists of floats takes several times the size of the raw JSON. The fix is to stream the file with a generator and process in batches, and, for anything that must stay in memory, to store embeddings as NumPy float32 arrays and use slotted objects or tuples instead of dicts.

**Deeper explanation:** Where the memory goes in the original `rows = [json.loads(line) for line in f]`: one embedding of 1,536 floats as a Python list costs 8 bytes per pointer plus 24 bytes per float object, about 49 KB, while the same vector as float32 is 6 KB. Each dict and each string adds its own header on top. `sys.getsizeof(rows)` hides all of this, because it reports only the outer list's pointer array.

```python
import json
import tracemalloc
from collections.abc import Iterator
from itertools import batched            # 3.12+

def iter_chunks(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)        # one record alive at a time

def ingest(path: str) -> None:
    tracemalloc.start()
    for batch in batched(iter_chunks(path), 500):
        upsert_vectors([(c["id"], c["embedding"]) for c in batch])
    _, peak = tracemalloc.get_traced_memory()
    print(f"peak traced: {peak / 1e6:.0f} MB")      # now a few batches, not the file
    tracemalloc.stop()
```

To find the culprit before changing code, take `tracemalloc.take_snapshot()` after loading and print `snapshot.statistics("lineno")[:10]`; the list comprehension line will dominate. If the process must keep everything, for example as an in-memory index, keep one `np.float32` matrix of shape (n, 1536) plus a parallel list of IDs, which drops the per-float objects entirely.

**Follow-ups they will ask:**
- Memory stays high after the batch is done: why? : CPython's allocator can keep freed memory in its pools, so the RSS may not shrink; restart workers after N tasks (Celery's `--max-tasks-per-child`, or `max_tasks_per_child` on `ProcessPoolExecutor` in 3.11+).
- Can tracemalloc run in production? : it slows every allocation, so turn it on for a staging run or behind a flag (`PYTHONTRACEMALLOC=1`).
- Would `gc.collect()` help? : no, there are no cycles here; the memory is live data you are still holding.

**Mistakes to avoid:**
- Trusting `sys.getsizeof` for container sizes.
- Reading the file with `f.read().splitlines()`, which holds the whole file twice.

### Q. Semantic search over 50,000 stored embeddings takes seconds per query in a pure-Python loop. Profile it, prove where the time goes, and fix it.
**Short answer (45 seconds):** I would run the search under cProfile, sorted by `tottime`. It will show nearly all the time inside the cosine function's generator expressions: 50,000 calls, each running three Python-level loops over every dimension and recomputing the document's norm on every query. The fix is to normalize the stored vectors once into a NumPy float32 matrix, so a query is one matrix-vector product in compiled code, then pick the top k with `argpartition`.

**Deeper explanation:** The slow version and how to profile it:

```python
import cProfile
import pstats

def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5            # recomputed for every doc, every query
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb)

def search(q: list[float], index: list[tuple[str, list[float]]], k: int = 5):
    scored = [(cosine(q, vec), doc_id) for doc_id, vec in index]
    return sorted(scored, reverse=True)[:k]

with cProfile.Profile() as prof:
    search(query, index)
pstats.Stats(prof).sort_stats("tottime").print_stats(5)
```

The fix:

```python
import numpy as np

class VectorIndex:
    def __init__(self, ids: list[str], vectors: list[list[float]]) -> None:
        m = np.asarray(vectors, dtype=np.float32)
        self.ids = ids
        self.m = m / np.linalg.norm(m, axis=1, keepdims=True)   # normalize once

    def search(self, q: list[float], k: int = 5) -> list[tuple[str, float]]:
        k = min(k, len(self.ids))
        v = np.asarray(q, dtype=np.float32)
        scores = self.m @ (v / np.linalg.norm(v))               # one call, compiled loop
        top = np.argpartition(scores, -k)[-k:]                  # top k without a full sort
        top = top[np.argsort(scores[top])[::-1]]
        return [(self.ids[i], float(scores[i])) for i in top]
```

Prove the gain with `time.perf_counter` over a few hundred queries, before and after, checking that both return the same IDs. Filter out zero vectors at load time, since their norm is zero. At millions of vectors, move to an approximate index such as FAISS or pgvector with HNSW.

**Follow-ups they will ask:**
- Why is NumPy so much faster? : the data is contiguous float32 rather than boxed Python floats, and the loop runs in compiled code that can use SIMD and BLAS.
- Why not a process pool instead? : it spreads the slow loop over cores but keeps it slow per core; vectorize first, then parallelize if still needed.
- When does NumPy not help? : tiny arrays, per-element Python callbacks, or converting lists on every request.

**Mistakes to avoid:**
- Tuning the sort before profiling shows it matters.
- Converting the stored vectors with `np.asarray` inside every query.

### Q. You added @lru_cache to several functions in a FastAPI service. Now memory grows in every worker, one tenant sees another request's prompt edits, and an async function fails with "RuntimeError: cannot reuse already awaited coroutine". Explain and fix each.
**Short answer (45 seconds):** Three different misuses. An unbounded cache keyed by high-cardinality input, or placed on a method so it holds every `self`, grows forever, once per worker process. A cached function that returns a mutable dict hands the same object to every caller, so one caller's edit changes everyone's result. And `lru_cache` on an `async def` caches the coroutine object, which can only be awaited once. I would bound the caches, return immutable values, and cache async results explicitly.

**Deeper explanation:** The problems:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def load_templates(tenant: str) -> dict[str, str]:
    return read_templates(tenant)                 # 1: same mutable dict for every caller

class Retriever:
    @lru_cache(maxsize=None)
    def embed(self, text: str) -> list[float]:    # 2: keyed on self and every text, unbounded
        return self.model.encode(text)

@lru_cache
async def get_settings(user_id: int) -> dict:     # 3: caches the coroutine object
    return await fetch_settings(user_id)
```

The fixes:

```python
from types import MappingProxyType

@lru_cache(maxsize=256)
def load_templates(tenant: str) -> MappingProxyType:
    return MappingProxyType(read_templates(tenant))   # read-only view

@lru_cache(maxsize=10_000)
def embed_text(text: str) -> tuple[float, ...]:       # module level, bounded, immutable
    return tuple(MODEL.encode(text))

_settings: dict[int, dict] = {}

async def get_settings(user_id: int) -> dict:
    if user_id not in _settings:
        _settings[user_id] = await fetch_settings(user_id)
    return dict(_settings[user_id])                   # a copy for the caller
```

`lru_cache` on a method keeps a strong reference to each instance in the cache, so instances are never freed; cache a module-level function, or use `functools.cached_property` for a per-instance value. Each Uvicorn worker has its own cache, so memory is per-entry size x entries x workers. `lru_cache` has no expiry: data that changes, like user settings, belongs in Redis or a TTL cache, and the dict above suits only values that never change. Watch `cache_info()` to confirm the hit rate justifies the memory.

**Follow-ups they will ask:**
- How do you invalidate one entry? : you cannot; `cache_clear()` empties everything, so use cachetools or Redis for per-key invalidation and TTLs.
- Is `lru_cache` thread-safe? : its data structure stays consistent, but two threads that miss at the same time can both run the function.
- What is a good fit for it? : pure, low-cardinality, process-lifetime values such as parsed config, tokenizers and compiled regexes.

**Mistakes to avoid:**
- `maxsize=None` on arguments that come from user input.
- Caching functions that depend on time, a database session or the current request.

### Practice
- Practice kit: open `python-practice/exercises/p19_internals.py`, implement each function, then run `uv run --with pytest pytest tests/test_p19_internals.py` from the `python-practice` folder.
- Use `timeit` to compare `x in list` and `x in set` at 1,000, 10,000 and 100,000 items, and confirm that only the list time grows with size.
- Measure peak memory with tracemalloc for one million floats as a list, as `array.array("d")` and as a NumPy float64 array, and explain the difference.
- Profile a script of your own with `python -m cProfile -s tottime script.py` and explain the top three rows out loud.
