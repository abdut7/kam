## FastAPI & Python Async Architecture [Core]

> Interviewers who see FastAPI on a resume ask where the code actually runs: which process, which thread, which loop. A weak answer says "FastAPI is async, so it is fast". A strong answer names every layer a request crosses (Gunicorn master, Uvicorn worker, event loop, ASGI, Starlette, FastAPI, Pydantic), says which code runs on the loop and which runs in the thread pool, and knows the one mistake that freezes a whole worker.

### In plain words
Think of a FastAPI deployment as a restaurant. A manager at the door hires a few identical waiters and replaces any who collapse, but never serves a table. Each waiter handles many tables at once by never standing still: they take an order, pass it to the kitchen, and move on to the next table until a bell says a dish is ready. Every order is written on the same standard slip, a host reads the slip and sends it to the right station, a prep cook gathers everything the dish needs, and a strict clerk rejects slips with missing or wrong fields before any cooking starts. Chores that need someone to stand and wait, like soaking a pot, go to a small back room of helpers, and a banquet-sized job goes to a separate kitchen entirely. If a waiter stops to scrub a pot personally, every one of their tables waits. The manager is the Gunicorn master, the waiters are Uvicorn workers, walking between tables is the asyncio event loop, the slip is ASGI, the host is Starlette, the prep cook is FastAPI's dependency injection, the clerk is Pydantic, the back room is the AnyIO thread pool, and the separate kitchen is a process pool or Celery.

### Walkthrough: one request through FastAPI
1. **Gunicorn master**: binds the listening socket, forks N Uvicorn workers, then only supervises them (restart on crash, SIGTERM for graceful shutdown, SIGHUP for graceful reload). It never reads a byte of any request, and without Gunicorn, `uvicorn --workers N` or one Uvicorn process per container fills this role.
2. **Uvicorn worker**: an OS process that inherited the socket; the kernel hands the new TCP connection to one worker, which accepts it. Each worker has its own copy of the app, its own event loop, its own GIL and its own lifespan resources such as the database pool and LLM client.
3. **asyncio event loop (uvloop)**: the loop is parked in the OS readiness call (epoll on Linux, kqueue on macOS, or libuv when uvloop is installed). When bytes arrive, it wakes and calls Uvicorn's protocol callback with the raw data.
4. **HTTP parser (httptools or h11)**: Uvicorn feeds the bytes to httptools (C-based, used when installed) or h11 (pure Python). When the headers are complete, Uvicorn starts one asyncio Task per request to run the app and passes body bytes along as they arrive.
5. **ASGI (scope, receive, send)**: the server calls `await app(scope, receive, send)`, where `scope` holds the method, path and headers, `receive()` returns body chunks as `http.request` messages, and `send()` takes `http.response.start` and `http.response.body` messages. That three-argument call is the entire contract between server and framework.
6. **Starlette (middleware, routing)**: the call passes through the middleware stack (Starlette's error middleware outermost, then yours, such as CORS or timing, then the exception handlers), and the router matches path and method to one route.
7. **FastAPI (dependency injection, OpenAPI)**: FastAPI reads the body and resolves the endpoint's dependency graph; each dependency runs once per request and is cached for the rest of it, `async def` dependencies are awaited on the loop, and plain `def` dependencies run in the thread pool. The same type hints produce the OpenAPI schema behind `/docs`.
8. **Pydantic validation**: path, query, header and body values are parsed and coerced into typed objects by pydantic-core, which is written in Rust. Any failure becomes a 422 response listing every bad field, and the endpoint never runs.
9. **AnyIO thread pool**: an `async def` endpoint is awaited directly on the event loop, while a plain `def` endpoint is sent to the AnyIO thread pool and the loop keeps serving other requests. CPU-heavy work (local embeddings, PDF parsing) belongs in neither place: it goes to a process pool or a task queue such as Celery.
10. **response_model serialization**: the return value is validated and filtered against `response_model` (or the return annotation), encoded as JSON and sent as `http.response.start` then `http.response.body`, which Uvicorn writes to the socket. Only after the response has been sent do `BackgroundTasks` run, in the same worker.

### Walkthrough: how asyncio runs your coroutines
1. **Coroutine object**: calling an `async def` function runs none of its body; it returns a coroutine object, a paused function waiting to be driven. In Node, calling an async function runs it synchronously up to the first `await`, so this is the first surprise.
2. **Task scheduling**: `asyncio.create_task`, `asyncio.gather`, a `TaskGroup`, or Uvicorn (once per request) wraps the coroutine in a Task, and the Task puts its first step on the loop's ready queue with `loop.call_soon`.
3. **Run until a pending await**: the loop pops the Task's step and resumes the coroutine, which runs as ordinary synchronous Python until it awaits something unfinished. Awaiting another coroutine is just a function call; only a pending Future suspends.
4. **await yields at an I/O point**: deep inside `await client.get(...)`, the code waits on a Future that completes when the socket has data. The Future is pending, so control passes back up the chain of awaits to the Task, which registers a wake-up callback on that Future and returns to the loop.
5. **Selector or uvloop waits on sockets**: with nothing ready to run, the loop calls the selector (epoll or kqueue), or libuv under uvloop, with a timeout equal to the time until the nearest timer, such as an `asyncio.sleep`. The thread sleeps in the kernel and uses no CPU.
6. **Ready callbacks run**: a readable socket or a due timer puts its callback on the ready queue, and the loop runs the callbacks queued at the start of the pass, in order. Reading the data completes the Future, which schedules the Task's wake-up, and the coroutine resumes right after its `await` with the result.
7. **The GIL**: all of this happens on one thread, and even with extra threads only one thread per process runs Python bytecode at a time. The GIL is released during blocking system calls and inside many C extensions, which is why threads help with blocking I/O but not with Python CPU work.
8. **Why one blocking call freezes the worker**: `time.sleep(2)` or `requests.get(...)` inside `async def` blocks the loop's own thread and never returns control to the loop. For that whole time the loop cannot poll sockets, resume other Tasks, accept connections or answer health checks, so every request on that worker waits; the fixes are `await asyncio.sleep`, an async client such as `httpx.AsyncClient`, `await asyncio.to_thread(...)`, or a plain `def` endpoint.

### Concepts you must understand
- ASGI vs WSGI: WSGI (Flask, classic Django) is one synchronous call per request, so concurrency comes from threads or processes; ASGI is an async callable `app(scope, receive, send)` that lets one thread hold thousands of open requests, stream bodies, speak WebSockets and receive lifespan events.
- Uvicorn vs Gunicorn: Uvicorn is the ASGI server that owns the socket, the event loop and HTTP parsing inside a process; Gunicorn is a pre-fork process manager that runs several Uvicorn workers and restarts them, which matters on VMs and matters less in Kubernetes, where the orchestrator restarts processes.
- The event loop is one per worker process, on one thread, alternating between waiting for OS readiness events and running ready callbacks, so its throughput depends on every callback returning quickly.
- Coroutine vs Task vs Future: a coroutine is a paused function that does nothing until driven, a Future is a placeholder for a result with callbacks, and a Task is a Future that drives a coroutine on the loop; keep a reference to tasks you create or they can be garbage collected before finishing.
- The thread pool: `def` endpoints, sync dependencies, sync background tasks and `run_in_threadpool` share AnyIO's default limiter of 40 threads per process, so the 41st concurrent sync call queues; `asyncio.to_thread` uses a different pool, the loop's default executor.
- The GIL lets one thread per process run Python bytecode at a time; free-threaded builds (PEP 703) arrived as experimental in Python 3.13 and became supported but optional in 3.14, many C extensions are not ready, so production designs still assume the GIL and scale CPU work with processes.
- Pydantic v2 runs validation and serialization in pydantic-core, written in Rust, so validating request bodies, responses and LLM JSON output is cheap next to any network or model call.
- Dependency injection: `Depends` builds a per-request graph, each dependency runs once per request unless `use_cache=False`, sync dependencies go to the thread pool, and `yield` dependencies wrap setup and teardown (exactly when teardown runs relative to sending the response has changed between FastAPI versions, so check yours before using a yielded resource in a background task or stream).
- Lifespan: an async context manager passed as `FastAPI(lifespan=...)` runs once per worker process at startup and shutdown, is the place to create connection pools, LLM clients and model weights, and replaces the older `on_event` hooks.
- Streaming and SSE: `StreamingResponse` wraps an iterator or async generator and sends each chunk as an ASGI body message with `more_body=True`; server-sent events are that same stream with `text/event-stream` framing, a `data: ...` line followed by a blank line.

### Q. Walk me through what happens inside FastAPI from the moment a request arrives to the moment the response leaves.
**Short answer (45 seconds):** The Uvicorn worker that accepted the connection wakes on its event loop when bytes arrive, httptools parses the headers, and Uvicorn starts a Task that calls `app(scope, receive, send)`. Starlette runs the middleware stack and routes to the endpoint. FastAPI reads the body, resolves dependencies, and Pydantic validates every input, returning 422 on failure. The endpoint runs on the loop if it is `async def` or in the AnyIO thread pool if it is `def`, the result is validated and serialized through `response_model`, sent as two ASGI messages, and background tasks run after that.

**Deeper explanation:** Underneath every layer sits this call:

```python
async def app(scope, receive, send):
    # scope: {"type": "http", "method": "POST", "path": "/chat", "headers": [...]}
    message = await receive()   # {"type": "http.request", "body": b"...", "more_body": False}
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"ok": true}'})
```

Middleware is an ASGI app wrapping another one, so order matters: in FastAPI the last middleware added is the outermost. Validation errors never reach your code; they are raised as `RequestValidationError` and turned into a 422 by a handler you can override. If the endpoint returns a `Response` object directly, FastAPI skips `response_model` processing. And because Uvicorn runs one Task per request on one loop, a single blocking call anywhere in this chain, middleware included, stalls every other request on that worker.

**Follow-ups they will ask:**
- Does FastAPI read the whole body before the endpoint runs? : yes, when you declare a body parameter it must validate it first; for large uploads use `UploadFile`, which spools to a temporary file, or read `request.stream()` chunk by chunk.
- Where should request-scoped data live? : in `request.state`, a dependency, or a `contextvars` variable, never in a module global shared by all concurrent requests.
- When is the OpenAPI schema built? : from the route signatures on the first request to `/openapi.json`, then cached.

**Mistakes to avoid:**
- Calling FastAPI the server; Uvicorn is the server and FastAPI is an ASGI application.
- Assuming each request gets its own thread, as it would in a WSGI app on a threaded server.

### Q. async def or def for a FastAPI endpoint: how do you choose, and what goes wrong if you choose badly?
**Short answer (45 seconds):** I choose by the libraries the endpoint calls. If every slow call has an async version I can `await` (httpx, asyncpg, redis.asyncio, the async LLM SDK clients), I use `async def`, which runs on the event loop and lets one worker hold thousands of waiting requests. If it calls a sync library (requests, boto3, a sync database driver, a vendor SDK), I use plain `def` and FastAPI runs it in the AnyIO thread pool. The serious mistake is a sync call inside `async def`: it blocks the loop thread and freezes every request on that worker. The milder one is `def` everywhere, which works but caps concurrency at the pool size.

**Deeper explanation:**

```python
import time, requests, httpx
from fastapi import FastAPI

app = FastAPI()
http = httpx.AsyncClient(timeout=10)       # real code: create it in lifespan

@app.get("/bad")
async def bad():
    time.sleep(1)                           # loop thread blocked
    return requests.get(URL).json()         # blocked again

@app.get("/good-async")
async def good_async():
    return (await http.get(URL)).json()     # loop serves others meanwhile

@app.get("/good-sync")
def good_sync():
    return requests.get(URL).json()         # runs in a pool thread
```

Under load, `/bad` turns a worker into a one-request-at-a-time server: the fiftieth concurrent caller waits at least fifty seconds, and health checks time out too. `/good-sync` is fine until the pool (40 threads by default) is full, then requests queue. CPU work inside `async def`, such as tokenizing a large document, is the hidden version of the same bug.

**Follow-ups they will ask:**
- Can one endpoint mix both? : yes, `async def` with `await run_in_threadpool(sync_fn)` or `await asyncio.to_thread(sync_fn)` for the single sync call.
- Do dependencies follow the same rule? : yes, a sync dependency runs in the pool, and a blocking call in an `async def` dependency or middleware blocks the loop.
- How do you find a hidden blocking call? : asyncio debug mode (`PYTHONASYNCIODEBUG=1`) logs slow callbacks, and `py-spy dump` on a stuck worker shows the blocking stack.

**Mistakes to avoid:**
- Writing `async def` everywhere because it "is faster" while calling sync drivers inside.
- Raising the thread limit into the hundreds instead of replacing the sync library.

### Q. What do Uvicorn, Gunicorn, Starlette, Pydantic and FastAPI each do?
**Short answer (45 seconds):** Five layers, one job each. Gunicorn is an optional process manager that forks worker processes and restarts them. Uvicorn is the ASGI server: inside each process it owns the socket, the event loop and HTTP parsing, and turns bytes into ASGI calls. Starlette is the ASGI toolkit FastAPI is built on: routing, middleware, request and response classes, WebSockets, background tasks and the test client. Pydantic validates and serializes data. FastAPI reads your type hints and wires parameters, dependency injection, validation and OpenAPI docs together.

**Deeper explanation:** For a Node developer the mapping is close:

| Layer | Job | Nearest Node.js equivalent |
|---|---|---|
| Gunicorn | fork, supervise, restart workers | PM2 cluster mode or the `cluster` module |
| Uvicorn | socket, event loop, HTTP parsing | the `http` module on libuv's loop |
| Starlette | routing, middleware, requests, responses | Express or Koa core |
| Pydantic | validation and serialization | Zod |
| FastAPI | type hints to DI, validation, OpenAPI | Fastify schemas with @fastify/swagger |

FastAPI subclasses Starlette's application class, so every Starlette feature works directly. Gunicorn on its own is a WSGI server and only serves FastAPI through the Uvicorn worker class. One subtlety: for async workers Gunicorn's `--timeout` acts as a heartbeat, so a worker whose loop stays blocked longer than the timeout is killed and restarted, which can make a blocking bug look like random worker restarts.

**Follow-ups they will ask:**
- Do you need Gunicorn in Kubernetes? : usually not; one Uvicorn process per pod with the orchestrator handling restarts and replicas is simpler, and `uvicorn --workers` or `fastapi run --workers` covers multiple processes elsewhere.
- Can you swap Uvicorn out? : yes, any ASGI server works, for example Hypercorn, which supports HTTP/2, or Granian, which is written in Rust.
- Where does Pydantic run in a request? : once on the way in for parameters and body, and once on the way out for `response_model`.

**Mistakes to avoid:**
- Saying Gunicorn makes the app async; the event loop comes from Uvicorn.
- Describing FastAPI as a replacement for Starlette rather than a layer on top of it.

### Q. How do you run CPU-heavy work, such as embedding generation or PDF parsing, in a FastAPI service?
**Short answer (45 seconds):** First, is it really CPU work? Calling a hosted embeddings API is network I/O, so I just `await` an async client. Local work, such as running a sentence-transformers model or parsing a long PDF, must never run on the event loop, and the default thread pool is no fix because Python code in threads still takes turns on the GIL. For short jobs the caller waits for, I use a `ProcessPoolExecutor` created in lifespan. For long jobs I return 202 with a job id and hand the work to Celery or arq workers. At scale, inference moves to a separate batching service, often on a GPU.

**Deeper explanation:**

```python
import asyncio, io
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile
from pypdf import PdfReader

def extract_text(data: bytes) -> str:          # top level so it can be pickled
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cpu = ProcessPoolExecutor(max_workers=2)
    yield
    app.state.cpu.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/parse")
async def parse(file: UploadFile):
    data = await file.read()
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(app.state.cpu, extract_text, data)
    return {"chars": len(text)}
```

Arguments and results are pickled between processes, so pass bytes or a file path, never clients or ORM objects. Each Uvicorn worker gets its own pool, so total processes are workers times pool size. Threads are acceptable when the heavy part is native code that releases the GIL, as PyTorch and NumPy do inside their kernels, but a pure-Python parser like pypdf holds it.

**Follow-ups they will ask:**
- Why not BackgroundTasks? : they run in the same worker after the response, compete for its loop, threads and GIL, and are lost when the pod restarts.
- How does the client get a long job's result? : it polls `GET /jobs/{id}`, or subscribes over SSE to progress the worker publishes.
- Where do you load the model? : once per process at startup, in lifespan or the pool's `initializer`, never per request.

**Mistakes to avoid:**
- Using `asyncio.to_thread` for a pure-Python CPU loop and expecting a parallel speed-up.
- Loading a large model in every Uvicorn worker and every pool process without counting the memory.

### Q. How does FastAPI stream LLM tokens to a browser, and what must you get right?
**Short answer (45 seconds):** The endpoint returns a `StreamingResponse` wrapping an async generator; each `yield` becomes an ASGI `http.response.body` message with `more_body=True`, which Uvicorn writes to the socket as a chunk. For SSE the media type is `text/event-stream` and each chunk is framed as a `data:` line plus a blank line. What must be right: the framing, cleanup on client disconnect so the upstream LLM call stops, backpressure so a slow client cannot grow memory, no buffering in proxies or compression, and an explicit error event instead of a silent cut.

**Deeper explanation:**

```python
@app.post("/chat")
async def chat(body: ChatIn):
    async def events():
        try:
            async with llm.stream(body.messages) as tokens:   # closes upstream on exit
                async for token in tokens:
                    yield f"data: {json.dumps({'t': token})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception:
            log.exception("generation failed")
            yield 'event: error\ndata: {"message": "generation failed"}\n\n'
    return StreamingResponse(events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

On disconnect, Starlette stops the response: depending on version it cancels the generator at once or the next `send` fails. Either way the `async with` or a `finally` closes the provider stream, so you stop paying for tokens. Backpressure comes free inside the generator, because `send` waits while the socket buffer is full, which pauses the loop over the LLM stream too; it breaks when you put an unbounded `asyncio.Queue` between a producer task and the response. For proxies, set `X-Accel-Buffering: no` or `proxy_buffering off` in nginx, keep gzip away from `text/event-stream`, and send a `: ping` comment line during long tool calls so idle timeouts do not cut the stream.

**Follow-ups they will ask:**
- How does a browser read a POST stream? : with `fetch` and a stream reader, since `EventSource` only issues GET requests.
- Why catch `Exception` and not everything? : cancellation arrives as `asyncio.CancelledError`, a `BaseException`, and swallowing it breaks disconnect handling.
- What does sse-starlette add? : its `EventSourceResponse` handles framing and pings for you; the mechanics underneath are the same.

**Mistakes to avoid:**
- Testing only on localhost, then shipping behind nginx or a CDN that delivers the whole answer at once.
- Starting the LLM call in a background task that keeps generating after the client leaves.

### Practice
- Write a raw ASGI app with no framework (just the three-argument function), run it with `uvicorn`, and log every `receive` and `send` message for a POST with a body.
- Put `time.sleep(1)` in an `async def` endpoint and in a `def` endpoint, hit each with 50 concurrent requests (hey, wrk or locust), and compare throughput and the latency of a `/health` endpoint during the test.
- In lifespan, lower AnyIO's limiter with `anyio.to_thread.current_default_thread_limiter().total_tokens = 4`, send 20 concurrent requests to a `def` endpoint that sleeps, and watch them complete in batches of four.
- Stream a fake 30-second token generator through nginx with default settings, then with `X-Accel-Buffering: no`, and compare what `curl -N` shows.
- Say it out loud: in two minutes, trace one request from the Gunicorn master to the bytes leaving the socket, naming which thread runs each step.

## Node.js vs FastAPI, Side by Side [Core]

> Interviewers like asking a Node developer to compare runtimes, because it shows whether you understand your own stack or only use it. Listing frameworks is weak. The answer that lands maps the concepts one to one (loop to loop, Promise to coroutine, libuv pool to AnyIO pool, cluster to Gunicorn workers) and names exactly where blocking code goes in each runtime.

### In plain words
Node.js and FastAPI are two kitchens built from the same floor plan: one fast chef per station who never stands waiting at the oven, a few helpers in the back for chores that need someone to wait, and more stations when one is not enough. The difference is in the tools. In the Node kitchen nearly every tool is designed as "start it and come back later", so it is hard to block the chef by accident. In the Python kitchen many popular tools are the old kind that make you stand and wait, so you either pick the async version or pass the job to a helper. Python also has a house rule that only one person per station may actually cook at a time, so adding helpers does not speed up heavy cooking; you open more stations instead. The chef is the event loop, the helpers are the libuv or AnyIO thread pool, the stations are processes (cluster or Gunicorn workers), and the one-cook rule is the GIL.

### Concepts you must understand

| Concept | Node.js | FastAPI on Python | What to say |
|---|---|---|---|
| Runtime and threads | V8 runs your JS on one main thread per process; libuv adds a small thread pool | CPython runs your code on one event-loop thread per worker process; AnyIO adds a thread pool | Same shape: one thread runs your code, helper threads run blocking work |
| Event loop implementation | libuv, with phases such as timers, poll and check | asyncio's loop over `selectors` (epoll, kqueue), or uvloop, which is built on libuv | With uvloop, both loops sit on the same C library |
| Unit of async work | Promise, eager: work starts when it is created | coroutine, lazy: runs only when awaited or wrapped in a Task | Calling an async function without `await` does nothing in Python |
| Microtask idea | `process.nextTick` queue, then the promise microtask queue, drained after every callback | no separate microtask queue: a finished Future schedules its callbacks on the ready queue with `call_soon` | Python has one FIFO ready queue; awaiting a coroutine is a plain call until something is pending |
| Thread pool | libuv pool, 4 threads by default (`UV_THREADPOOL_SIZE`), used by fs, `dns.lookup`, crypto and zlib; sockets do not use it | AnyIO pool, default limiter of 40, used for `def` endpoints, sync dependencies and `run_in_threadpool` | In Node the runtime uses the pool for you; in FastAPI your own sync code lands there |
| CPU parallelism | `worker_threads`: separate V8 isolates that truly run in parallel | separate processes (`ProcessPoolExecutor`, Celery), because the GIL serializes Python bytecode across threads | Node threads parallelize JS; Python threads do not parallelize Python |
| Scaling across cores | `cluster` module or PM2 cluster mode | Gunicorn with Uvicorn workers, `uvicorn --workers`, or one process per container | Both scale cores with processes, each with its own memory |
| Middleware | Express `(req, res, next)` chain | Starlette ASGI middleware wrapping the app, or `@app.middleware("http")` | Both are onion layers; in FastAPI the last one added runs first |
| Validation | Zod or Joi, called by you (or JSON schema in Fastify) | Pydantic, driven by type hints, automatic 422 | FastAPI validates before your code runs |
| API docs | written by hand, swagger-jsdoc, or Fastify's swagger plugin | automatic OpenAPI at `/openapi.json`, `/docs` and `/redoc` | FastAPI docs cannot drift from the code |
| Classic blocking mistake | `readFileSync`, `crypto.pbkdf2Sync`, a CPU loop or a huge `JSON.parse` on the main thread | `time.sleep`, `requests.get` or a sync database driver inside `async def` | Same failure: the loop thread is stuck and every request waits |
| Streaming | `res.write()` with `text/event-stream`, respecting the `false` return and the `drain` event | `StreamingResponse` over an async generator; `send` waits on a full socket buffer | Both need disconnect handling and no proxy buffering |
| Best fit for AI backends | hosted-LLM orchestration, realtime WebSockets, a BFF sharing TypeScript types with React | model-adjacent work: local embeddings, rerankers, document parsing, evals, Python-first AI libraries | Many teams run both behind one gateway |

- The one sentence to remember: both run one event loop thread per process, but Node's ecosystem is non-blocking by default and Python's is not, so in Python you choose async libraries deliberately or route sync code to a thread.
- Node's thread pool is mostly invisible infrastructure, while FastAPI's thread pool is where your own code runs whenever you write `def`, so its limit is an application concern.
- The GIL is the real divergence: Node can use `worker_threads` for CPU work inside one process, while Python needs another process or native code that releases the GIL.
- In AI backends the time goes to model and database calls, so raw event loop speed rarely decides between the two; ecosystem and team language usually do.

### Q. Compare the Node.js and FastAPI execution models.
**Short answer (45 seconds):** They share a skeleton: each process runs one thread with an event loop over non-blocking sockets, a thread pool takes blocking work, and you scale across cores with more processes. The differences are in the details. Node's loop is libuv with phases and a microtask queue drained between callbacks, while asyncio has a single ready queue. A Promise starts work when created, a coroutine only when awaited or scheduled. Node uses its pool internally for fs, DNS and crypto, while FastAPI puts your own `def` code in its pool. And because of the GIL, Python threads never run Python code in parallel, while Node's `worker_threads` do.

**Deeper explanation:** The laziness difference is the one that bites in code review:

```js
// Node: the request is already in flight when fetch() returns
const pending = fetch(url);
await doOtherWork();
const res = await pending;
```

```python
# Python: nothing is sent until the coroutine is awaited or scheduled
pending = client.get(url)                     # coroutine object only (Python warns if never awaited)
task = asyncio.create_task(client.get(url))   # now it is running
await do_other_work()
res = await task
```

The queue difference mostly explains ordering puzzles: in Node, `await` on an already resolved promise still defers to the microtask queue, while in Python awaiting a coroutine is an ordinary call that gives up control only when it reaches a pending Future. Under load both behave the same way: throughput depends on every callback returning quickly, and one slow synchronous step delays everything queued behind it on that process.

**Follow-ups they will ask:**
- Is uvloop the same as Node's loop? : it implements the asyncio loop in Cython on top of libuv, the library under Node, so the I/O layer is shared but the scheduling rules are asyncio's.
- What is the Python version of `Promise.all`? : `asyncio.gather`, or `asyncio.TaskGroup` (Python 3.11 and later) for cleaner cancellation when one task fails.

**Mistakes to avoid:**
- Saying "Node is single-threaded and Python is multi-threaded": both run your code on one thread per process by default.
- Treating `asyncio.create_task` like a promise you can drop; keep a reference or it may be garbage collected before it finishes.

### Q. Your team must build an AI backend that calls LLMs, runs embeddings and serves a React app. Node.js or FastAPI, and why?
**Short answer (45 seconds):** I decide by where the heavy work sits. If "AI" means calling hosted models and an embeddings API, streaming tokens, tool calls and a realtime UI, Node with TypeScript is a strong choice: official SDKs, types shared with the React app, one language for the team. If the service runs models itself (local embedding models, rerankers, PDF and OCR pipelines, evaluation jobs) or depends on Python-first libraries, FastAPI is the better fit. When both kinds of work exist, which is common, I run both: a Node gateway for auth, sessions, realtime and the React app, and a FastAPI service behind it for model-adjacent work.

**Deeper explanation:**

| Need | Lean towards | Why |
|---|---|---|
| Chat UI, WebSockets, sessions, BFF for React | Node.js | shared TypeScript types, one language with the frontend |
| Orchestrating hosted LLM calls and tools | either | both have official async SDKs; follow the team's language |
| Local embeddings, rerankers, tokenizers | FastAPI | PyTorch, sentence-transformers and Hugging Face live in Python |
| Document parsing, OCR, evals, data jobs | FastAPI plus workers | the libraries and the ML team's code are Python |

Make the contract between the services explicit: FastAPI publishes OpenAPI, and a generator such as openapi-typescript produces the Node client types, so a renamed field breaks the build instead of production. The extra network hop inside a cluster is small next to a model call measured in seconds. For streaming, Node can pipe the Python stream through with buffering disabled.

**Follow-ups they will ask:**
- Would you ever choose only Python? : yes, if the team is Python-strong and the frontend is thin; FastAPI handles SSE and WebSockets well.
- Would you ever choose only Node? : yes, if every model sits behind an API and nobody needs local ML libraries.
- How do the two share auth? : the gateway authenticates the user and forwards a short-lived signed token, which the Python service verifies rather than trusting plain headers.

**Mistakes to avoid:**
- A tribal answer ("Python is the AI language", "Node is faster") with no reference to the actual workload.
- Two services with no shared contract, so request and response types drift silently.

### Q. Where does blocking code hurt in each runtime, and how do you fix it in each?
**Short answer (45 seconds):** In both, blocking code hurts on the event loop thread, because every request on that process waits behind it. In Node that means sync APIs (`readFileSync`, `pbkdf2Sync`), CPU loops, huge `JSON.parse` calls and catastrophic regexes; a quieter failure is a saturated libuv pool, where fs and crypto calls queue behind 4 threads while the loop looks idle. In FastAPI it means any sync library or CPU work inside `async def`; the quieter failure is a full AnyIO pool when `def` endpoints wait on slow calls. The fixes are parallel: async APIs, a thread for sync I/O, a process or worker for CPU.

**Deeper explanation:**

| Problem | Node.js fix | FastAPI fix |
|---|---|---|
| Sync I/O on the loop | async APIs (`fs.promises`, streams) | async drivers (httpx, asyncpg), a `def` endpoint, or `asyncio.to_thread` |
| CPU work on the loop | `worker_threads` (Piscina), a queue, or chunking with `setImmediate` | `ProcessPoolExecutor`, Celery or arq, or a separate service |
| Thread pool saturation | set `UV_THREADPOOL_SIZE` at startup, or reduce pool-bound calls | raise the AnyIO limiter, or move to async libraries |
| Detecting it | `perf_hooks.monitorEventLoopDelay`, `--cpu-prof`, clinic.js | asyncio debug mode slow-callback logs, `py-spy dump` or `py-spy top` |

In Python, CPU work in a thread still competes for the GIL with the loop thread, so unrelated requests slow down too; a Node worker thread has its own V8 isolate, heap and loop, leaving the main loop free.

**Follow-ups they will ask:**
- What does loop blocking look like on a dashboard? : p99 latency rising together across unrelated endpoints on the same process, with that process pinned near one full core.
- How do you catch it before production? : asyncio debug mode in Python tests, a lint rule against `*Sync` calls in Node request paths, and load tests that watch loop delay.
- Why is bcrypt a classic Node example? : the native bcrypt package hashes on the libuv pool, so a login spike queues hashes and file reads behind the same 4 threads.

**Mistakes to avoid:**
- Fixing Python CPU work with threads, or Node CPU work with more `async`/`await`; neither changes anything.
- Raising pool sizes blindly instead of finding the blocking call.

### Q. How do you scale each one across CPU cores on one machine and across machines?
**Short answer (45 seconds):** On one machine both scale by running more processes, because each process uses roughly one core for application code. Node uses the `cluster` module or PM2 cluster mode; FastAPI uses Gunicorn with Uvicorn workers, `uvicorn --workers` or `fastapi run --workers`, starting at about one worker per core. In containers both are simplest as one process per pod, with the orchestrator adding replicas. Across machines the rules are identical: stateless processes behind a load balancer, shared state in Redis or Postgres, and pub/sub fan-out for WebSockets or SSE. The difference to remember is memory: a Python worker that loads a model multiplies that model's memory by the worker count.

**Deeper explanation:**

```bash
# Node on a VM: one process per core
pm2 start dist/server.js -i max
# FastAPI on a VM: Gunicorn supervises Uvicorn workers
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
# FastAPI in a container: one process, the orchestrator handles replicas
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Connection distribution differs: Node's cluster primary accepts connections and hands them out round-robin (except on Windows), while Gunicorn's workers all accept from the shared socket and the kernel decides. For AI backends, services that mostly wait on LLM calls show low CPU while saturated, so autoscale on in-flight requests, queue depth or latency. Count database connections too: pool size times workers times replicas must stay under the database limit, or you add PgBouncer.

**Follow-ups they will ask:**
- How many workers per pod? : one or two keeps memory predictable and lets the autoscaler work; more only if pods start slowly.
- What breaks when a second instance appears? : in-memory sessions, rate limits, caches and WebSocket rooms; move them to Redis or use sticky sessions.
- Does Gunicorn's `--preload` save memory? : it imports the app once before forking so pages start shared, but reference counting writes to objects and erodes the sharing, and sockets and clients must still be created per worker.

**Mistakes to avoid:**
- Running more workers than cores on a CPU-limited pod, adding memory and context switches for no throughput.
- Autoscaling an LLM-bound service on CPU utilization, which never triggers.

### Practice
- Build the same SSE endpoint twice, in Express with `res.write` and in FastAPI with `StreamingResponse`, each emitting a fake token every 50 ms for 10 seconds, and check both with `curl -N`.
- Load test both with the same tool (k6, autocannon or a small script) at 100 and then 1,000 concurrent streams, and record time to first token, memory per process and error rate.
- Block each on purpose: `fs.readFileSync` on a large file or a 500 ms CPU loop in Express, `time.sleep(0.5)` or `requests.get` inside `async def` in FastAPI; rerun the load test and watch time to first token for every other stream.
- Fix each the idiomatic way (streams or `worker_threads` in Node, an async client, a `def` endpoint or a process pool in Python), rerun, and write down the before and after numbers.
- Say it out loud: compare the two runtimes in ninety seconds using four one-to-one mappings (loop, unit of work, thread pool, scaling) and one sentence on where blocking code goes in each.
