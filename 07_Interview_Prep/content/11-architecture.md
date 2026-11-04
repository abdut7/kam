# Internal Architecture

> This track opens up the runtimes and models you use every day: Node.js, FastAPI and Python async, the LLM transformer, and the Jev decision model. Each section starts with a picture, then a step-by-step walkthrough, then interview questions. The aim is to explain what happens inside, in plain words first and precisely always, so you can answer the follow-up after the follow-up.

## Node.js Runtime Architecture [Core]

> Interviewers probe this runtime from the inside: the event loop phases in order, why microtasks run before the next timer (microtasks vs macrotasks), exactly which operations use the thread pool and which go straight to the kernel, how one thread serves thousands of connections, and the ways you block it by accident. A weak answer says "Node is single-threaded and non-blocking" and stops. A strong answer draws the layers, follows one request through them, and names the tool that proves where the time went.

### In plain words
Picture a restaurant with exactly one waiter, and he is extremely fast. He never stands at a table waiting while customers decide; he notes what they need, hands it off, and moves on. Slow jobs like cooking go to a small kitchen crew in the back, and when a dish is ready the kitchen rings a bell for him. Most tables never need the kitchen at all: the front desk phone system rings whenever a table is ready to order or pay, so the waiter only walks over when there is something to do. He checks things in the same order every round (alarms he set, tables that rang, quick favours he promised), and he always finishes his small "right after this" notes before moving to the next item. The restaurant only falls apart when the waiter does a long job himself, because while he is busy every table waits.

In Node terms: the waiter is the single JavaScript thread running on V8, the kitchen crew is the libuv thread pool, the phone system is the OS kernel's async I/O (epoll, kqueue, IOCP), his fixed round is the event loop, and the "right after this" notes are the process.nextTick queue and the promise microtask queue.

### Walkthrough: one HTTP request through Node.js
1. A client opens a TCP connection. The OS kernel (epoll, kqueue, IOCP) completes the handshake and reports the listening socket as ready, and libuv accepts the connection during the poll phase of the event loop.
2. Request bytes arrive on the socket. libuv reads them, and the Node bindings (C++) feed them to the HTTP parser, which calls up into the Node core APIs (`http`) to build `req` and `res` and emit `request`.
3. V8 runs the Express middleware and your handler on the call stack of the single JavaScript thread. `req`, `res` and every object your code creates live on the heap.
4. The handler calls `await fs.promises.readFile('template.html')`. The Node core APIs pass the call through the Node bindings (C++) to libuv, which queues it on the thread pool, and the function returns a pending promise at once.
5. The `await` suspends the handler and the call stack empties, so the event loop is free to serve other requests. Meanwhile one thread pool thread makes the blocking open and read system calls.
6. When the read finishes, the pool thread signals the event loop, and in the poll phase Node runs the completion callback that resolves the promise. The rest of the handler then runs from the promise microtask queue, right after that callback returns.
7. The handler calls `await pool.query(...)` on an already open Postgres connection, and libuv writes the query bytes to that TCP socket straight into the OS kernel (epoll, kqueue, IOCP). Network sockets never use the thread pool; only fs, dns.lookup, async crypto (pbkdf2, scrypt, randomBytes) and zlib do.
8. While Postgres works, the event loop keeps cycling through timers, poll and check for other requests; a query timeout, if you set one, waits in timers. If nothing is ready, the loop parks in poll inside the kernel's wait call.
9. The reply arrives, the kernel reports the socket readable, and libuv reads it in poll. The pg driver parses the rows on the call stack and resolves its promise, so the handler resumes from the promise microtask queue (anything in the process.nextTick queue runs first).
10. `res.json()` serializes the body on the call stack and libuv writes it to the socket; if the client reads slowly, libuv keeps the remainder and writes it when the socket is writable again. With keep-alive the socket stays open for the next request; if it is destroyed, its close handler runs in close callbacks, and V8's garbage collector later reclaims the request's objects from the heap.

### Walkthrough: the event loop, phase by phase
1. **timers**: runs setTimeout and setInterval callbacks whose delay has passed. A delay is a minimum, not an exact time, and setTimeout(fn, 0) is stored as 1 ms.
2. **pending callbacks**: runs a few I/O callbacks that libuv deferred from the previous turn, such as some TCP error reports (Node's documentation uses ECONNREFUSED as the example).
3. **idle/prepare**: internal bookkeeping for libuv and Node; nothing you schedule runs here.
4. **poll**: runs callbacks for completed I/O (new connections, socket data, finished thread pool jobs), and this is where the loop waits for I/O. It blocks inside the OS kernel until an event arrives or the next timer is due, and it does not block at all if a setImmediate is queued.
5. **check**: runs setImmediate callbacks, which is why a setImmediate scheduled inside an I/O callback always beats a 0 ms timer. Immediates queued during this phase wait for the next turn.
6. **close callbacks**: runs close handlers for handles that were shut down abruptly, for example a socket's `close` event after `socket.destroy()`.
7. After every single callback in any phase, Node drains the process.nextTick queue completely, then the promise microtask queue completely, and repeats until both are empty before it runs the next callback. That is why a recursive nextTick or an endless promise chain starves I/O.
8. At the end of a turn the loop checks whether anything is still alive (active timers, open servers or sockets, pending requests). If so it goes back to timers; if not, the process exits.

### Concepts you must understand
- V8 executes JavaScript: the call stack holds the frames of the functions running right now, and the heap holds objects, closures and strings, cleaned up by a generational garbage collector.
- There is one JavaScript thread per process (and one per worker), so only one callback runs at a time and any long synchronous work delays every other request.
- libuv is the C library under Node that owns the event loop, the timers, the thread pool and a cross-platform layer over the kernel's async I/O.
- The thread pool has 4 threads by default, set with UV_THREADPOOL_SIZE when the process starts, and runs fs, dns.lookup, async crypto (pbkdf2, scrypt, randomBytes) and async zlib.
- Network sockets never use the thread pool: epoll (Linux) and kqueue (macOS, BSD) tell libuv which sockets are ready, IOCP on Windows reports completed operations instead, and libuv hides the difference.
- The event loop runs phases in a fixed order (timers, pending callbacks, idle/prepare, poll, check, close callbacks), and poll is where it waits for I/O when nothing else is due.
- Macrotasks are callbacks that belong to a phase (timers, I/O, immediates); microtasks are the process.nextTick queue and the promise microtask queue, which Node drains completely after every callback.
- worker_threads give parallel JavaScript inside one process for CPU work, cluster runs several copies of your server sharing one port, and child_process runs any other program.
- Blocking the loop (sync fs calls, a huge JSON.parse, heavy loops, catastrophic regex backtracking) delays every request at once and shows up as event loop delay and p99 latency.
- Streams apply backpressure: write() returning false means stop until `drain`, and stream.pipeline wires that, plus error handling and cleanup, across every stage.

### Q. Draw the Node.js architecture and explain what each layer does.
**Short answer (45 seconds):** Top to bottom: your code and npm packages; the Node core APIs in JavaScript (http, fs, net, crypto, stream, timers); the Node bindings (C++) that connect them to native code; then V8, which compiles and runs JavaScript with its call stack and heap, beside libuv, which owns the event loop, the thread pool and a portable layer over the OS kernel's async I/O. Your code runs on one thread inside V8; anything slow is handed down and comes back as a callback.

**Deeper explanation:**

```text
your code: Express routes, npm packages
------------------------------------------------------------
Node core APIs (JS): http, fs, net, crypto, stream, timers
------------------------------------------------------------
Node bindings (C++)    bundled libs: llhttp, OpenSSL, zlib, c-ares
------------------------------------------------------------
V8: call stack, heap, GC     |   libuv: event loop, thread pool
------------------------------------------------------------
OS kernel (epoll, kqueue, IOCP): network stack, file system
```

V8 knows nothing about files or sockets; it executes JavaScript, manages the heap and collects garbage. Everything else Node adds comes from core APIs calling through the bindings into libuv or a bundled library: llhttp parses HTTP, OpenSSL does TLS and crypto, zlib compresses, c-ares backs dns.resolve. libuv asks the kernel which sockets are ready, fires due timers, and pushes work the OS cannot do asynchronously (file system calls, getaddrinfo, heavy crypto, compression) onto its thread pool. Results come back up the same path as a main-thread callback.

**Follow-ups they will ask:**
- Is V8 the event loop? : no, V8 supplies the promise microtask queue; the phased loop belongs to libuv and Node, and the nextTick queue is Node's own.
- Where do native addons fit? : compiled C++ loaded through Node-API, beside the bindings; they can queue work on the thread pool.
- How do Deno and Bun differ? : Deno pairs V8 with Rust and Tokio instead of libuv, Bun uses JavaScriptCore; both keep one JS thread plus native async I/O.

**Mistakes to avoid:**
- Drawing V8 as the part that does I/O; V8 has no I/O at all.
- Leaving out the thread pool, then failing to explain why fs and crypto behave unlike sockets.

### Q. What is the output order of this snippet, and why?
**Short answer (45 seconds):** Synchronous code runs first, then the process.nextTick queue, then the promise microtask queue, and only then the event loop. At the top level, setTimeout(0) and setImmediate can come out in either order. Inside an I/O callback the order is fixed: nextTick, then setImmediate in the check phase of the same turn, then setTimeout in the next turn's timers phase.

**Deeper explanation:**

```js
const fs = require('node:fs');
console.log('A sync start');
setTimeout(() => console.log('E timeout'), 0);
setImmediate(() => console.log('F immediate'));
process.nextTick(() => console.log('C nextTick'));
Promise.resolve().then(() => console.log('D promise'));
fs.readFile(__filename, () => {
  console.log('G readFile callback');
  setTimeout(() => console.log('J timeout in I/O'), 0);
  setImmediate(() => console.log('I immediate in I/O'));
  process.nextTick(() => console.log('H nextTick in I/O'));
});
console.log('B sync end');
// Typical output: A B C D E F G H I J (E and F can swap)
```

A and B are the synchronous script. C then D: once the stack empties, Node drains the nextTick queue, then the promise microtask queue. E versus F is the non-deterministic part: a 0 ms timer is really 1 ms, and whether 1 ms has passed when the loop first checks timers depends on how long startup took. G lands in a later poll phase because readFile is several thread pool round trips (open, stat, read, close); in practice that is after E and F, but it is timing, not a rule. H runs the moment G's callback returns. I always beats J: the loop is in poll, check comes next, and timers only come round on the next turn.

**Follow-ups they will ask:**
- Does this change in an ES module? : it can; top-level ESM code is evaluated inside the loader's promise machinery, so D may print before C. Never depend on it.
- What if a .then schedules another .then? : it runs in the same drain, before any timer; that is how promise chains starve I/O.

**Mistakes to avoid:**
- Saying the timeout always runs first because it was scheduled first.
- Treating nextTick as an event loop phase; it is a queue drained after every callback.

### Q. If Node.js is single-threaded, how does it handle ten thousand concurrent connections?
**Short answer (45 seconds):** A waiting connection costs no thread, only a socket file descriptor registered with the OS kernel and a few objects on the heap. libuv asks the kernel, through epoll, kqueue or IOCP, which of those thousands of sockets have something to do, and the event loop runs callbacks only for those. The JavaScript thread spends a short burst of CPU per event and is free the rest of the time, so the limits are CPU per request, memory and file descriptors, not thread count.

**Deeper explanation:** Compare thread-per-connection servers, where each connection holds a thread and its stack while it waits, so memory and context switching cap concurrency. Node turns waiting into data: a socket in the kernel's interest list and a callback in a table. One kernel wait call over ten thousand idle WebSocket clients returns only the handful that became ready.

| Limit | Symptom | Fix |
|---|---|---|
| JS CPU per request | event loop delay rises, throughput flat at one core | profile, offload, one process per core |
| File descriptors | EMFILE errors | raise ulimit -n and container limits |
| Downstream pools | requests queue waiting for a pg connection | size pools to what the database can take |

Throughput is arithmetic: at 2 ms of JavaScript CPU per request, one process tops out near 500 requests per second however many connections are open. For more cores, run more processes (cluster, PM2, extra pods).

**Follow-ups they will ask:**
- Does each await create a thread? : no, an await stores a continuation and the thread moves on.
- What was the C10k problem? : serving ten thousand concurrent connections on one machine, solved by readiness-based I/O like epoll rather than more threads.
- Are SSE or WebSocket connections a problem? : not for the loop; watch memory per socket and load balancer idle timeouts.

**Mistakes to avoid:**
- Saying the thread pool handles the connections; sockets never touch it.
- Implying one thread wins at everything; one CPU-heavy request still stalls all ten thousand.

### Q. Which operations use the libuv thread pool, and what happens when it is saturated?
**Short answer (45 seconds):** The pool runs work the OS cannot do without blocking: fs operations, dns.lookup (which calls getaddrinfo), async crypto such as pbkdf2, scrypt and randomBytes, async zlib, and native addons that queue async work. It has 4 threads by default (UV_THREADPOOL_SIZE) and one shared FIFO queue. When it is saturated, new jobs wait in that queue, so unrelated operations slow down together while event loop delay looks perfectly healthy.

**Deeper explanation:** The trap is head-of-line blocking across features. Picture a login endpoint calling crypto.scrypt per request. During a login burst all 4 threads are hashing, and behind them wait a template read via fs.readFile and, less obviously, every outbound HTTP call to a hostname, because dns.lookup runs before the socket connects. The payment API looks slow and the dashboards blame the provider.

```js
const fs = require('node:fs');
// a trivial pool job: rising time with flat loop delay means pool saturation
setInterval(() => {
  const start = process.hrtime.bigint();
  fs.stat(__filename, () => {
    metrics.gauge('uv_pool_probe_ms', Number(process.hrtime.bigint() - start) / 1e6);
  });
}, 5000);
```

Fixes: set UV_THREADPOOL_SIZE in the environment at process start (it is read once, when the pool is first used); move heavy hashing to a worker_threads pool such as piscina so it stops competing with fs; reuse connections with keep-alive agents so lookups are rare. Do not switch to the sync variants: crypto.scryptSync runs on the main thread and blocks the whole loop.

**Follow-ups they will ask:**
- Does raising the size always help? : for waiting-type work like slow disks or DNS, yes; for CPU-bound hashing, going past the core count only adds context switching.
- Which bcrypt library uses the pool? : the native bcrypt package does; bcryptjs is pure JavaScript and runs on the main thread.
- Do fs streams avoid the pool? : no, each chunk read is a pool job; streams bound memory, not pool usage.

**Mistakes to avoid:**
- Raising UV_THREADPOOL_SIZE to fix slow database queries; sockets never touch the pool.
- Setting process.env.UV_THREADPOOL_SIZE late in startup and assuming it took effect.

### Q. How do you detect and fix a blocked event loop in production?
**Short answer (45 seconds):** Detect it with numbers: export event loop delay percentiles from perf_hooks.monitorEventLoopDelay and utilization from performance.eventLoopUtilization, and alert when p99 delay climbs. Then capture a CPU profile (--cpu-prof, the inspector, or clinic flame) and find the wide synchronous frame. Fix by taking sync work off the request path: stream or cap big payloads, chunk loops with setImmediate, or move CPU-heavy work to worker_threads.

**Deeper explanation:** Event loop delay is how late a timer fires compared with when it was due (the histogram reports nanoseconds). A blocked loop shows spikes as long as the blocking task, and every request that arrived meanwhile inherits them. Utilization says whether the loop is always busy (add processes) or mostly idle with spikes (one bad code path).

To find the code: `node --cpu-prof server.js` writes a .cpuprofile on exit for Chrome DevTools; clinic doctor tells loop, GC and I/O problems apart, and clinic flame draws a flame graph. `--trace-sync-io` prints a stack trace whenever sync I/O runs after the first loop turn.

```js
// yield to I/O between slices instead of blocking for the whole array
async function forEachChunked(items, fn, size = 1000) {
  for (let i = 0; i < items.length; i += size) {
    for (const item of items.slice(i, i + size)) fn(item);
    await new Promise((resolve) => setImmediate(resolve));
  }
}
```

Chunking makes latency fair but total CPU is unchanged; for heavy work (PDF parsing, embeddings math) a worker_threads pool gives real parallelism.

**Follow-ups they will ask:**
- Why yield with setImmediate and not nextTick or a resolved promise? : both drain before the loop moves on, so they never let I/O in.
- Is profiling safe in production? : it has overhead; take short captures on one instance, never leave it on.
- What if the profile shows mostly GC? : that is a memory problem; look at allocation rate and heap size.

**Mistakes to avoid:**
- Watching only average latency; loop blocking lives in the p99.
- Wrapping sync code in a promise and calling it fixed; JSON.parse inside a promise still runs on the same thread.

### Q. Where does memory live in Node, and how do the heap, the stack and garbage collection affect latency?
**Short answer (45 seconds):** The call stack holds the frames of the functions running right now; it is small and short-lived. Objects, closures, strings and arrays live on the V8 heap, split into a young generation for new objects and an old generation for survivors. Buffer and ArrayBuffer contents live outside the V8 heap. Garbage collection pauses JavaScript on the main thread for part of its work, so allocation patterns show up directly as tail latency.

**Deeper explanation:** Most objects die young: a request's parsed body is garbage once the response is sent. V8 collects the young generation with a scavenge, a fast copying collector that moves only the survivors. Objects that survive two scavenges are promoted to the old generation, collected by mark-sweep-compact: mark everything reachable, sweep the rest, compact to cut fragmentation. V8 does much of that concurrently or incrementally, but main-thread pauses remain and grow with the live heap.

```bash
# old generation limit in MB; --trace-gc prints each collection and its pause
node --max-old-space-size=1536 --trace-gc server.js
```

What hurts latency: a high allocation rate (many scavenges), request objects held across slow awaits until promoted, and an old generation near its limit, where V8 runs major collections back to back before failing with "JavaScript heap out of memory". A big in-process cache is weight every major collection must mark.

Buffers show up as external and arrayBuffers in process.memoryUsage(); they count toward RSS and the container limit, not toward --max-old-space-size.

**Follow-ups they will ask:**
- What overflows the stack? : deep or unbounded recursion, giving "RangeError: Maximum call stack size exceeded"; make it iterative.
- Can a garbage-collected program leak? : yes, anything reachable stays: module-level Maps, listeners never removed, closures in long-lived timers.
- How do you see GC pauses as metrics? : a perf_hooks PerformanceObserver on `gc` entries.

**Mistakes to avoid:**
- Saying primitives live on the stack and objects on the heap; in V8 strings and most non-small numbers are heap objects, and closure-captured variables live in heap-allocated contexts.
- Setting --max-old-space-size above the container limit; the kernel kills the process before V8 reports anything.

### Practice
- Run the output-order snippet as a .js file and as a .mjs file (swap require for import) ten times each; record which lines move and explain every move using the phase list.
- Build a tiny Express app with a `/hash` route calling crypto.pbkdf2 and a `/file` route calling fs.readFile; load-test `/hash` with autocannon while timing `/file`, then repeat with UV_THREADPOOL_SIZE=8 and compare.
- Write a script that fills a Map cache without eviction and also allocates Buffers; run it with --trace-gc and log process.memoryUsage() every second, then explain which numbers move for the Map (heapUsed, longer mark-compact pauses) and which for the Buffers (external, RSS).
- Say it out loud: in under two minutes, trace one Express request that reads a file and queries Postgres, naming every layer it touches and which thread does the work at each step.
