## Concurrency

> This section is where interviewers find out whether you understand what the runtime and the database actually do when two requests arrive in the same millisecond. Weak answers talk about threads in the abstract or claim "Node is single-threaded so there are no race conditions". Strong answers show a specific read-modify-write race from a real system, point at where the atomic boundary lives (a single conditional UPDATE, a Redis INCR, a compare-and-set), and can explain what the event loop, libuv, and the connection pool are each doing under load.

### Concepts you must understand
- A race condition is any outcome that depends on the timing of operations between concurrent actors; the usual shape is read, decide, write, with a gap in between that another actor slips into.
- Concurrency is many tasks in progress at once by interleaving; parallelism is many tasks executing at the same instant on several cores. Node gives you the first by default and the second only through worker_threads or extra processes.
- The Node event loop runs all JavaScript on one thread; network I/O waits in the kernel (epoll, kqueue), and file system, DNS lookup, zlib, and some crypto work run on libuv's thread pool, four threads by default.
- Single-threaded JavaScript does not prevent races: every `await` is a yield point where another request's code runs, so check-then-act across an await is racy.
- An atomic operation completes indivisibly from every observer's point of view: `UPDATE t SET n = n + 1`, Redis `INCR`, MongoDB `$inc`, and `findOneAndUpdate` are atomic; a GET followed by a SET is not.
- A connection pool keeps a fixed set of open database connections and queues requests for them; without one you pay a handshake per request and can exhaust the database's `max_connections`.
- A distributed lock gives mutual exclusion across processes or machines; it needs a TTL so a crashed holder does not block forever, and an owner token so a stale holder cannot release someone else's lock.
- Thundering herd: many waiters wake for one event (a lock release, an expired key, a reconnect) and overwhelm the resource; fix it with jitter, coalescing, or waking one waiter.
- Safe counters come from pushing the increment into the atomic primitive, batching increments and flushing, or sharding the counter across keys when one key becomes a hot spot.

### Q. What is a race condition? Give a real backend example.
**Short answer (45 seconds):** A race condition is a bug where the result depends on the timing of concurrent operations, usually because another actor changes state in the gap between your read and your write. Real example: a coupon with `uses_left = 1`. Two requests both read 1, both pass the `> 0` check, both decrement, and the coupon is used twice.

**Deeper explanation:**

```js
// racy
const { rows } = await db.query('SELECT uses_left FROM coupons WHERE code = $1', [code]);
if (rows[0].uses_left > 0) {
  await db.query('UPDATE coupons SET uses_left = uses_left - 1 WHERE code = $1', [code]);
}

// safe
const { rowCount } = await db.query(
  'UPDATE coupons SET uses_left = uses_left - 1 WHERE code = $1 AND uses_left > 0', [code]);
if (rowCount === 1) applyDiscount();
```

The second form works because one UPDATE takes the row lock and re-evaluates `uses_left > 0` against the committed value; the second concurrent UPDATE waits for the first to commit, re-checks, sees 0, and matches nothing.

Node makes this subtle: JavaScript is single-threaded, but every `await` lets the event loop run another request's handler, so requests interleave exactly as threads would. Races rarely show up in logs, so design them out: make the database or Redis the atomic boundary, add unique constraints as the last line of defence (a duplicate webhook delivery then fails instead of creating a second order), and treat any read-then-write across an await as suspect.

**Follow-ups they will ask:**
- Is Node immune because it is single-threaded?: No; handlers interleave at every await and across processes.
- How would you reproduce one in a test?: Fire N requests with `Promise.all` at a seeded row, assert the invariant, and repeat, since the failure is probabilistic.

**Mistakes to avoid:**
- A mutex in one Node process when you run several replicas; the lock must live where the shared state lives.
- "We wrapped it in a transaction." Under READ COMMITTED that does not stop two reads of the same value.

### Q. What is the difference between concurrency and parallelism?
**Short answer (45 seconds):** Concurrency is structuring a program so that multiple tasks are in progress at once and make progress by interleaving; parallelism is executing multiple tasks at the same instant on multiple cores. One Node process holding 10,000 open connections is highly concurrent and not parallel for JavaScript execution. Eight Node processes behind `cluster`, or a CPU-heavy job in `worker_threads`, is parallelism. Concurrency is dealing with many things; parallelism is doing many things.

**Deeper explanation:**

```text
Concurrency (one core, interleaved)        Parallelism (two cores, simultaneous)
 A: run..wait......run..wait.....run        core 1: A run....A run....A run
 B: ....run..wait......run..wait....        core 2: B run....B run....B run
```

The distinction decides the fix. If requests are slow because they wait on the database or an LLM API, the work is I/O-bound and concurrency solves it: Node's loop already overlaps thousands of waits, Python needs asyncio or threads (which release the GIL during I/O), and extra cores do not help. If requests are slow because of CPU work (parsing a 50 MB JSON body, computing embeddings locally, bcrypt at a high cost factor), concurrency makes it worse: each heavy task blocks the loop and every other request stalls behind it. That calls for parallelism: `worker_threads` inside one process, `cluster` or more containers across processes, or a queue consumer elsewhere.

A line worth saying: Node is concurrent by default and parallel by configuration; Python with the GIL is the same story, which is why FastAPI apps push CPU-bound jobs into a process pool.

**Follow-ups they will ask:**
- A task that benefits from concurrency but not parallelism?: Fanning out to twenty microservices; the time is network latency, so `Promise.all` is enough.
- How many Node processes per machine?: Usually one per core via cluster or a process manager, since one process executes JavaScript on one core.

**Mistakes to avoid:**
- Using the terms interchangeably, or calling Node "parallel" because it handles many requests at once.
- Reaching for worker_threads for database-bound code; the bottleneck is the wait, and workers add message-passing overhead.

### Q. How does Node.js handle concurrent requests without multiple threads?
**Short answer (45 seconds):** Node runs all JavaScript on one main thread driven by an event loop. When a handler starts I/O, it hands the operation to libuv, registers a callback, and returns to the loop, which picks up the next ready event. Network sockets are non-blocking and multiplexed by the kernel (epoll on Linux, kqueue on macOS); file system, DNS lookups, zlib, and some crypto run on libuv's thread pool, four threads by default.

**Deeper explanation:**

```text
 +----------------------+   readiness events    +----------------+
 |  event loop          | <-------------------- | kernel         |
 |  (one JS thread)     |                       | epoll / kqueue |
 |  timers -> poll ->   |   completions         +----------------+
 |  check -> close      | <-------------------- | libuv pool     |
 |  microtasks between  |                       | (4 threads)    |
 +----------------------+                       +----------------+
```

Each iteration runs phases: expired timers, pending I/O callbacks, poll (wait for I/O and run its callbacks), `setImmediate` callbacks, then close callbacks. Between callbacks Node drains the microtask queue, `process.nextTick` first and then resolved promises, which is why an `await` resumes before the next timer.

Any synchronous CPU work blocks everyone: a 300 ms `JSON.parse` delays every other request by 300 ms (`bcrypt.hashSync` and stringifying huge LLM responses are common offenders), so track `perf_hooks.monitorEventLoopDelay` as a health metric. For CPU work, `worker_threads` run separate V8 isolates with their own loops, communicating by messages or `SharedArrayBuffer`; `cluster` forks whole processes behind one port, one loop per core. On the pool: `fs.*`, `dns.lookup`, `crypto.pbkdf2`, and zlib can saturate four threads (raise `UV_THREADPOOL_SIZE`); sockets never touch it.

**Follow-ups they will ask:**
- `process.nextTick` versus promise microtasks versus `setImmediate`?: nextTick runs before promise callbacks, both before the loop continues; setImmediate runs in the check phase after poll.
- In-flight requests when a cluster worker crashes?: They fail; the primary forks a replacement and clients or the load balancer retry.

**Mistakes to avoid:**
- Saying Node is asynchronous "because of the thread pool" for network I/O; sockets are non-blocking via the kernel.
- Claiming Node cannot have race conditions because it is single-threaded.

### Q. What is an atomic operation? Why does it matter for counters?
**Short answer (45 seconds):** An atomic operation either happens completely or not at all, and no other actor can observe or interleave with its intermediate state. For counters, "read the value, add one, write it back" is three steps, and two concurrent actors can both read 10 and both write 11, losing an increment. An atomic increment (`UPDATE ... SET n = n + 1`, Redis `INCR`, MongoDB `$inc`) performs read-add-write as one indivisible step inside the engine, so every increment counts.

**Deeper explanation:**

```js
// atomic: Redis runs INCR on its single command thread
await redis.incr('views:42');

// atomic with a ceiling: a Lua script runs as one uninterruptible unit
const script = `
  local n = tonumber(redis.call('GET', KEYS[1]) or '0')
  if n >= tonumber(ARGV[1]) then return -1 end
  return redis.call('INCR', KEYS[1])`;
await redis.eval(script, 1, 'signups:beta', 1000);
```

Redis executes commands one at a time on a single thread, so `INCR`, `HINCRBY`, `SETNX`, and any `EVAL` script are atomic by construction; `MULTI/EXEC` groups commands atomically but cannot branch on an intermediate result, which is what Lua is for. In Postgres, `UPDATE counters SET n = n + 1 WHERE id = 1 RETURNING n` is atomic because the row lock serialises updaters and each re-reads the committed value. In MongoDB, `$inc` is atomic per document.

The price is serialisation: every increment of one key queues behind the previous one, so a very hot key becomes a bottleneck; then you shard the counter across keys, batch increments and flush with `INCRBY`, or accept approximate counts.

**Follow-ups they will ask:**
- Is `x++` in Node atomic?: Nothing interrupts it within one process, but it is per-process memory, meaningless across cluster workers or replicas.
- Is `MULTI/EXEC` a transaction like SQL?: Atomic and isolated, but no rollback: if one command errors, the others still apply.

**Mistakes to avoid:**
- "Wrap GET and SET in MULTI" without `WATCH`; MULTI does not read values into your code.
- A counter in a JavaScript variable behind a load balancer.

### Q. What is a connection pool and what happens if you don't use one?
**Short answer (45 seconds):** A connection pool is a set of pre-opened database connections that a process reuses: a request borrows one, runs its queries, and returns it. Without one you pay a TCP handshake, TLS negotiation, and authentication per request, and in Postgres a new backend process each time. Under load you open thousands of connections, exhaust `max_connections`, and the database refuses new ones while existing queries slow down. A pool caps concurrency at a healthy number and queues the rest.

**Deeper explanation:** Postgres forks a process per connection, each with its own memory, so a thousand idle connections are expensive and a thousand active ones thrash. The useful number of concurrent queries is a small multiple of the database's cores; beyond it, more connections mean more waiting, not more throughput.

```js
import pg from 'pg';
const pool = new pg.Pool({
  max: 10,                        // per process; multiply by replicas
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000  // fail fast when the pool is exhausted
});
```

Ten replicas with ten connections each present a hundred to Postgres, so teams put PgBouncer in front in transaction mode: the app sees many connections, the database sees few. Transaction pooling breaks session features (named prepared statements, session `SET`, advisory locks, LISTEN), hence Prisma's `pgbouncer=true` flag. Failure modes: a leaked client (no `release()` on an error path) silently shrinks the pool until every request times out; a transaction held open while awaiting an LLM call starves everyone; serverless functions each open a pool, which is why RDS Proxy and similar poolers exist.

**Follow-ups they will ask:**
- How do you size it?: Start near database cores times a small factor, watch `pool.waitingCount` and database CPU, and raise it only while the database is not saturated.
- Pool exhausted but the database is idle?: Leaked clients or transactions held across slow calls; look for "idle in transaction" in `pg_stat_activity`.

**Mistakes to avoid:**
- A new `Pool` or `PrismaClient` per request.
- `max: 500` "so requests never wait", which moves the queue into the database where it is far more expensive.

### Q. What is a distributed lock and when do you need one?
**Short answer (45 seconds):** A distributed lock gives mutual exclusion across processes or machines, so only one replica runs a piece of work at a time: a nightly job that must not run twice, or a cache rebuild for one key. You need one when the shared resource lives outside any single process and row locks cannot express the critical section. The minimal correct Redis form is `SET lock:key TOKEN NX PX 30000`, released by a Lua script that deletes only if the token still matches.

**Deeper explanation:**

```js
const token = crypto.randomUUID();
const ok = await redis.set(`lock:report:${day}`, token, 'PX', 30_000, 'NX');
if (ok !== 'OK') return;
try {
  await buildReport(day);
} finally {
  await redis.eval(`
    if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end
    return 0`, 1, `lock:report:${day}`, token);
}
```

`NX` makes acquisition atomic; `PX` is the TTL so a crashed holder does not block forever; the token check stops a slow holder whose lock expired from deleting a newer holder's lock. It still cannot save you when the holder stalls past the TTL and another replica acquires the lock: both now believe they own it. The real fix is a fencing token, a monotonically increasing number the protected resource rejects if older than one it has seen. Without that it is an efficiency lock, not a correctness guarantee.

Alternatives often beat Redis: Postgres advisory locks (`pg_try_advisory_lock(key)`) vanish if the connection dies, and a conditional UPDATE on a job row (`SET locked_by = $1 WHERE id = $2 AND locked_by IS NULL`) is often simplest because lock and data share one transaction.

**Follow-ups they will ask:**
- Why a random token instead of plain DEL?: A holder that overran its TTL would otherwise delete another holder's lock.
- When is it the wrong tool?: When a unique constraint, conditional update, or `FOR UPDATE SKIP LOCKED` can enforce the rule.

**Mistakes to avoid:**
- `SETNX` then a separate `EXPIRE`: a crash between them leaves a lock with no TTL.
- Treating a Redis lock as a correctness guarantee without fencing or idempotency.

### Q. What is the thundering herd problem in the context of concurrency?
**Short answer (45 seconds):** The thundering herd problem is many waiting actors being woken by the same event and rushing the same resource at once, so a resource that was fine under steady load collapses under the synchronised spike. Classic cases: a popular cache key expires and every request that misses recomputes it; a Redis or database restart makes every client reconnect in the same second; a lock is released and every blocked worker retries at once; a cron job fires on fifty replicas on the same tick.

**Deeper explanation:** The common thread is synchronisation: independent actors that would normally spread their load get aligned by a shared trigger. Every fix either breaks the alignment or collapses the duplicates.

```js
// request coalescing: one in-flight load per key, everyone else awaits it
const inflight = new Map();
async function getUser(id) {
  const key = `user:${id}`;
  const hit = await redis.get(key);
  if (hit) return JSON.parse(hit);
  if (!inflight.has(key)) {
    inflight.set(key, loadAndCache(id, key).finally(() => inflight.delete(key)));
  }
  return inflight.get(key);
}
```

Coalescing guarantees one database query per key per process however many requests miss. Across processes, a short Redis lock (`SET lock:user:42 1 NX PX 2000`) lets one replica recompute while others wait or serve stale data. For the reconnect herd, every client retries with exponential backoff plus jitter, `delay = random(0, min(cap, base * 2^attempt))`, because fixed delays only move the spike. For cron herds, add a random offset per instance or elect one leader with an advisory lock. For lock release, wake one waiter, or replace the lock with a queue (`FOR UPDATE SKIP LOCKED`).

**Follow-ups they will ask:**
- Why jitter, not just exponential backoff?: Without randomness every client still retries on the same schedule, only more slowly.
- How does this differ from a cache stampede?: A stampede is the cache-specific case; the herd also covers reconnects, locks, and schedulers.

**Mistakes to avoid:**
- "Add read replicas." The herd scales with your fleet; collapse the duplicate work instead.
- Fixed retry delays (`setTimeout(retry, 1000)`) in client code.

### Q. How do you make a counter increment safe under high concurrency?
**Short answer (45 seconds):** Use a primitive that is atomic where the state lives: `UPDATE counters SET n = n + 1 WHERE id = $1 RETURNING n` in Postgres, `INCR` in Redis, `$inc` in MongoDB. Never read in the app and write back. If one row or key becomes a hot spot, shard the counter across N keys and sum on read, buffer increments and flush with `INCRBY`, or emit events and aggregate asynchronously.

**Deeper explanation:** A Postgres row counter is correct and simple, but every increment waits for the row lock and writes WAL, so one global row that every request touches caps throughput; per-user or per-post counters spread naturally. Redis `INCR` handles far more per key, and a Lua script adds the check a rate limiter needs:

```lua
-- allow at most ARGV[1] hits per window
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('PEXPIRE', KEYS[1], ARGV[2]) end
if n > tonumber(ARGV[1]) then return 0 end
return 1
```

Setting the expiry only when `n == 1` is race-free because the whole script runs atomically. For very hot keys, write to `likes:post:9:` plus a random suffix from 0 to 15 and sum with `MGET` on read. When exactness matters at huge volume (LLM token billing), do not count in the request path: emit an event and let a consumer aggregate into Postgres in batches. State the trade: Redis is fast but not the source of truth; a buffer loses a window on crash; the stream is exact but delayed.

**Follow-ups they will ask:**
- Why is `SELECT n` then `UPDATE n = $1` wrong even in a transaction?: Both transactions can read the same n; only `n = n + 1` or `FOR UPDATE` serialises them.
- How do you count unique visitors cheaply?: `PFADD` and `PFCOUNT` (HyperLogLog), about 0.81 percent standard error in roughly 12 KB per key.

**Mistakes to avoid:**
- `count = await get(); await set(count + 1)` in any form, even inside a SQL transaction.
- One global counter row in Postgres for a high-traffic endpoint.

### Practice
- Write an Express endpoint that decrements a coupon with a read-then-write, hit it with 100 parallel requests, observe the over-use, then fix it with a conditional UPDATE and prove the fix with the same test.
- Implement the `SET NX PX` lock with the Lua release, run two processes competing for it, and kill one mid-work to watch the TTL expire and the other proceed.
- Measure event loop lag with `monitorEventLoopDelay` while running a synchronous `JSON.parse` on a 100 MB string, then move the parse into a `worker_threads` worker and measure again.
- Say it out loud: explain to a non-Node colleague in ninety seconds how one thread serves ten thousand connections and what still blocks it.

## Caching

> Interviewers use caching to separate people who have put a Redis GET in front of a query from people who have been burned by a stale cache or a stampede. The weak answer is "cache it in Redis with a TTL". The strong answer names the pattern (cache-aside, read-through, write-through, write-behind), states who owns invalidation, explains what happens when the cache is cold, hot, or down, and ties the TTL to how stale the business can tolerate the data. Have one story ready where the cache made things wrong, not just slow.

### Concepts you must understand
- Cache-aside (lazy loading): the app checks the cache, misses, loads from the database, and writes to the cache; the cache knows nothing about the database.
- Read-through and write-through move that logic into the cache layer so the app only talks to the cache; write-behind acknowledges writes from the cache and persists asynchronously, trading durability for write latency.
- Invalidation options: TTL (bounded staleness), explicit delete on write, versioned keys (never invalidate, just stop reading the old key), and event-driven invalidation from the database change stream.
- A cache stampede is many concurrent misses on one key all recomputing it; prevent it with request coalescing, a short lock, probabilistic early expiration, or serving stale while one request refreshes.
- Hot keys concentrate traffic on one Redis node and one thread; fix them with a local cache, key replication, or sharding the key.
- A local in-process cache has no network cost but is per replica and inconsistent across replicas; a distributed cache is shared but costs a round trip and is a dependency that can fail.
- On writes, delete the cache entry after the database commit rather than updating it; know the delete-before-write and concurrent-backfill races; keep a TTL as the safety net.
- A CDN caches HTTP responses at the edge, controlled by `Cache-Control`, `ETag`, and `Vary`; an application cache stores objects and query results next to your code.
- Cache failures must degrade gracefully: a Redis outage should mean slower requests, not errors, so wrap cache calls in timeouts and treat failures as misses.
- `maxmemory` and the eviction policy (`allkeys-lru`, `allkeys-lfu`, `volatile-ttl`) decide what happens when Redis is full; the default `noeviction` returns errors on writes.

### Q. Explain the four main caching strategies and when to use each.
**Short answer (45 seconds):** Cache-aside: the app reads the cache first and on a miss loads from the database and populates it; the most common pattern. Read-through: the cache layer itself loads from the database on a miss, so the app talks only to the cache. Write-through: every write goes to the cache and synchronously to the database, consistent but slower. Write-behind: writes land in the cache and flush to the database asynchronously, fastest but lossy if the cache dies first.

**Deeper explanation:**

| Strategy | Loads on miss | Write path |
|---|---|---|
| Cache-aside | application | database, then delete the key |
| Read-through | cache layer | database; key expires or is invalidated |
| Write-through | cache layer | cache and database, synchronously |
| Write-behind | cache layer | cache now, database later in batches |

Cache-aside in Node is `redis.get(key)`, else query Postgres and `redis.set(key, JSON.stringify(row), 'PX', ttl)`. Only requested data is cached and the cache can be flushed at any time, but invalidation is entirely your job on every write path, including background jobs and migrations.

Write-through gives a warm, consistent cache but you pay a cache write for data that may never be read. Write-behind is how view counts and likes are done: accumulate in Redis, flush to Postgres every few seconds, accept that a crash loses the unflushed window. Real systems mix them: cache-aside for entity reads, write-behind for metrics, a CDN for HTTP. In an LLM product, cache-aside on embeddings and on deterministic prompt results (keyed by a hash of model, prompt, and parameters) saves real money.

**Follow-ups they will ask:**
- Which one does Redis implement?: None by itself; the strategy lives in your code or a library such as DynamoDB DAX.
- Misses for ids that do not exist?: Cache a short-lived "not found" sentinel, or repeated lookups hammer the database.

**Mistakes to avoid:**
- Listing the four names without saying who owns invalidation in each; that is the real question.
- Write-behind for orders or payments, where losing seconds of writes is unacceptable.

### Q. What is cache invalidation and why is it considered one of the hardest problems in CS?
**Short answer (45 seconds):** Invalidation is removing or refreshing cached data when the source of truth changes. It is hard because a cache is a second copy of state with no transaction linking it to the first: every write path must know every key that depends on it, derived data such as lists depends on many rows, and concurrent reads and writes can reinsert a stale value right after you deleted it.

**Deeper explanation:** Dependency tracking: an order update may need to invalidate `order:42`, `user:7:orders`, and `dashboard:today`, and a new cached view silently breaks when nobody updates the old write paths. Timing races: with cache-aside, "T1 misses and reads the old row; T2 writes and deletes the key; T1 sets the old value" leaves stale data until the TTL. Fan-out: invalidating `products:list` on every edit keeps the list permanently cold.

```text
Strategies, simplest to most precise
  TTL only         bounded staleness, no code on write paths
  delete on write  exact for single-entity keys, racy under concurrency, TTL as backup
  versioned keys   read user:7:v12; writes bump the version, old keys die by TTL
  event driven     change stream (Debezium on the WAL, MongoDB change streams) feeds
                   one consumer that deletes affected keys
```

Versioned keys make "lists depend on many rows" tractable: embed a per-user `profile_version` in every derived key, and bumping it makes every derived entry unreachable at once. Event-driven invalidation puts the dependency knowledge in one consumer instead of every writer. Keep a TTL as the backstop; every scheme eventually misses a path. The hard part is not the DEL command; it is deciding where the knowledge of "what depends on what" lives and bounding the damage when it is wrong.

**Follow-ups they will ask:**
- Delete or update on write?: Delete; two concurrent writers updating can leave the older value last.
- What do very short TTLs cost?: A higher miss rate and more origin load.

**Mistakes to avoid:**
- Blaming Redis; the difficulty is your own write paths and races.
- No TTL at all because "we invalidate explicitly".

### Q. What is a cache stampede / thundering herd and how do you prevent it?
**Short answer (45 seconds):** A cache stampede happens when a popular key expires and every concurrent request that misses recomputes it at once, so the database receives hundreds of identical expensive queries instead of one. Prevention: coalesce concurrent misses so one computation runs per key; take a short Redis lock so only one replica recomputes; refresh slightly before expiry with probabilistic early expiration; or serve the stale value while one request revalidates.

**Deeper explanation:**

```js
// XFetch: entry stores expiresAt and delta (last recompute duration)
async function fetchXFetch(key, ttlMs, loader, beta = 1) {
  const raw = await redis.get(key);
  if (raw) {
    const { value, expiresAt, delta } = JSON.parse(raw);
    const early = -delta * beta * Math.log(Math.random());
    if (Date.now() + early < expiresAt) return value;
  }
  const t0 = Date.now();
  const value = await loader();
  const entry = { value, expiresAt: Date.now() + ttlMs, delta: Date.now() - t0 };
  await redis.set(key, JSON.stringify(entry), 'PX', ttlMs);
  return value;
}
```

The closer to expiry and the costlier the recompute, the likelier a request refreshes early, so refreshes spread out and a busy key never goes cold, with no locks or coordination.

The lock approach is easier to explain: on a miss, `SET lock:key 1 NX PX 3000`; the winner recomputes and the losers poll briefly or return a stale copy (a logical expiry inside a longer physical TTL). Inside one process an in-flight promise map removes duplicate work for free. Also remove the causes: jitter TTLs so keys do not expire together, warm the cache after a deploy, and cache a brief negative result when the loader fails.

**Follow-ups they will ask:**
- Why not just a longer TTL?: Stampedes become rarer, not smaller, and staleness grows.
- What if the lock holder crashes?: The PX TTL releases the lock and waiters retry or fall back, which is why the lock TTL is short.

**Mistakes to avoid:**
- Coalescing only inside one process and forgetting you run twenty replicas.
- Waiters blocking on the lock with no timeout, turning a stampede into hung requests.

### Q. What is a hot key problem in Redis and how do you solve it?
**Short answer (45 seconds):** A hot key is one key receiving a disproportionate share of traffic: the home feed, a viral post's like count, a global feature flag. Redis Cluster shards by key, so all of that traffic lands on one node and one thread, saturating it while other nodes idle. Solutions: cache the key locally in each process with a short TTL, replicate it into N copies and read a random one, shard a hot counter, or move reads to replicas.

**Deeper explanation:** Find them first: `redis-cli --hotkeys` (requires an LFU eviction policy) or client-side sampling. Then choose by access pattern.

```text
Read-heavy (feature flags, config, top-N list)
  -> local in-memory cache (lru-cache) with a 1 to 5 second TTL per replica
  -> or key replication: write flag:v to flag:v:0 .. flag:v:9, read a random copy
Write-heavy (likes on a viral post, global counter)
  -> shard the counter: INCR likes:9:{random 0..15}; read with MGET and sum
  -> or buffer increments in-process and flush with INCRBY every 200 ms
```

The local cache is usually the first move for read-heavy keys because it removes the network entirely; the price is a few seconds of staleness per replica, so invalidate across replicas with Redis pub/sub or server-assisted client-side caching (`CLIENT TRACKING`, Redis 6 and later). Key replication trades write amplification for read spread. For write-heavy keys, sharding is the standard answer; do not wrap the shard keys in one hash tag, which puts them back on one node. Also look for accidental hot keys: a global rate limiter key, or one `sessions` hash holding every session.

**Follow-ups they will ask:**
- Why does Redis Cluster not help?: Sharding is by key hash; one key lives in exactly one slot on one primary.
- Hot key versus big key?: Big is large and slow to serialise; hot is frequently accessed. Both at once is the worst case.

**Mistakes to avoid:**
- "Add more Redis nodes." The key still lives on exactly one of them.
- Local caching with no TTL or invalidation, so a flag flip never reaches some replicas.

### Q. When should you NOT cache something?
**Short answer (45 seconds):** Do not cache when the data must be correct at the instant it is read: balances before a transfer, inventory at checkout, authorisation after a permission revoke. Do not cache when keys rarely repeat, such as long-tail search parameters, because the hit rate will be low. Skip it when the origin is already fast enough that a cache only adds complexity, and when sensitive data would sit in a cache shared across users or tenants.

**Deeper explanation:** Caching trades correctness and complexity for latency and origin load, so it pays only when the read is expensive or frequent, the result is reused, and staleness for the TTL is acceptable. Do the arithmetic: a 20 ms query at fifty calls a second with a 90 percent hit rate saves about 900 ms of database time per second; at a 10 percent hit rate (the key includes a user id and timestamp) it saves almost nothing and adds a round trip to every call.

Correctness cases are stricter: a cached permission check means a revoked user keeps access for the TTL, so either skip the cache or delete on revoke. Stock at checkout must come from a conditional UPDATE, even though the product page can show a cached count. Anything used to make a write decision belongs in the source of truth. Never cache a response keyed only by URL when it varies by user.

Also skip data that changes faster than it is read, responses already served by a CDN, and code you have not profiled: a cache added before profiling often hides a missing index.

**Follow-ups they will ask:**
- How do you pick the TTL?: From the business's tolerance for staleness, then check the hit rate it yields.
- Would you cache LLM responses?: Only for deterministic inputs (temperature 0, identical prompt and context hash), never across users.

**Mistakes to avoid:**
- "Cache everything with a five-minute TTL", which is how balances go stale and revoked users stay logged in.
- Never measuring hit rate or origin savings after adding a cache.

### Q. What is the difference between a local cache and a distributed cache?
**Short answer (45 seconds):** A local cache lives inside the application process (a Map or `lru-cache` in Node): reads cost nanoseconds and need no network, but each replica has its own copy, so replicas disagree and memory is duplicated. A distributed cache such as Redis is a separate service shared by all replicas: one view of the data, survives deploys, far larger capacity, but every read is a network round trip and it is a dependency that can fail. Mature systems use both as tiers.

**Deeper explanation:**

| | Local (in-process) | Distributed (Redis) |
|---|---|---|
| Latency | nanoseconds to microseconds | a network round trip |
| Consistency across replicas | none | one shared value |
| Survives restart | no | yes |
| Invalidation | must be broadcast | one DEL |

Local caches suit small, hot, slow-changing data: feature flags, tenant config, JWT public keys. They need a hard size bound, because an unbounded Map is a memory leak and a bloated Node heap lengthens GC pauses, and a short TTL or a pub/sub invalidation channel so twenty replicas converge.

Distributed caches suit session state, rate limits, computed views, and anything the next request may hit on another replica. The two-tier pattern: check local, then Redis, then the database, and backfill upward. Make each tier optional: treat a Redis timeout as a miss and add a circuit breaker so an outage does not add a timeout to every request. Serialisation is part of the cost; `JSON.stringify` of a large object can cost more than the round trip.

**Follow-ups they will ask:**
- What breaks with a local cache behind a load balancer?: Users bounce between replicas and see different values; sticky sessions hide it without fixing it.
- How do you keep the local tier consistent?: Short TTL plus a Redis pub/sub channel every replica subscribes to.

**Mistakes to avoid:**
- A module-level object as a cache in serverless or multi-process deployments, expecting it to be shared.
- Treating Redis as always available, so a cache outage becomes an application outage.

### Q. How do you handle cache consistency when data changes?
**Short answer (45 seconds):** Write to the database first, then delete the cache entry after the commit, and keep a TTL as the safety net. Delete rather than update, so concurrent writers cannot leave the older value in the cache. For stronger guarantees, use versioned keys so a write bumps a version and all derived entries become unreachable at once, or drive invalidation from the database's change stream so no write path can forget.

**Deeper explanation:**

```text
1. Delete cache, then write DB
   T1 DEL key; T2 misses, loads OLD, SETs old; T1 writes DB.  Stale until TTL.
2. Write DB, then delete cache (preferred)
   T1 commits, then DELs. Residual race: T2 read old just before T1 committed and
   SETs it after the DEL; needs a read slower than write plus delete, so rare.
3. Write DB, then SET the new value
   Two writers' SETs can land in the opposite order to their commits. Avoid.
```

Ordering 2 plus a TTL is the pragmatic default. When even that is unacceptable: delayed double delete (delete again a second later to catch the stale backfill); versioned keys (readers read `user:7:v13`, and a write increments the version in the same transaction, so stale entries are never read again); or event-driven invalidation, where the transactional outbox or a CDC tool (Debezium on the Postgres WAL, MongoDB change streams) publishes each committed change and a consumer deletes affected keys, which also covers writers that forget.

Delete after commit, not inside the transaction, or a reader can backfill the old value before you commit: `await client.query('COMMIT'); await redis.del(key);`, with a failed DEL logged and the TTL as fallback.

**Follow-ups they will ask:**
- Why delete rather than update?: No recomputing the cached shape in the writer, and no last-writer-wins ordering bugs between concurrent updates.
- Lists and aggregates that depend on the changed row?: Versioned keys at the parent level, or event-driven invalidation with a dependency map.

**Mistakes to avoid:**
- Deleting the cache before the database write (ordering 1).
- Invalidating inside the transaction, before commit.

### Q. What is a CDN and how is it different from an application-level cache?
**Short answer (45 seconds):** A CDN is a geographically distributed set of reverse proxies that cache HTTP responses close to users, controlled by headers such as `Cache-Control`, `ETag`, and `Vary`. It cuts latency by serving from an edge near the client and shields the origin from most traffic. An application cache such as Redis sits inside your backend and holds objects, query results, and sessions keyed however your code chooses; you usually want both.

**Deeper explanation:**

| | CDN | Application cache |
|---|---|---|
| Cached unit | full HTTP responses | objects, query results, sessions |
| Keyed by | URL, method, `Vary` headers | whatever your code chooses |
| Best for | static files, public pages | per-user data, hot queries |

The headers are the API. `Cache-Control: public, max-age=31536000, immutable` on fingerprinted assets (`app.3f9a1c.js`) lets CDN and browser cache forever, because a deploy produces a new filename. `private, no-store` keeps authenticated responses out of shared caches. `ETag` with `If-None-Match` lets the edge revalidate with a 304. `stale-while-revalidate` lets the edge serve stale while fetching fresh. `Vary` names request headers that change the response; a careless `Vary: Cookie` makes every user a separate entry and destroys the hit rate.

The model to state: the CDN handles the request before it reaches you, keyed by the HTTP surface; the application cache handles work inside your request, keyed by your domain model. An LLM product uses a CDN for the frontend bundle and Redis for sessions, rate limits, and prompt-result caching.

**Follow-ups they will ask:**
- Can a CDN cache authenticated responses?: Only with per-user cache keys, which most teams avoid at the edge; POST is generally not cached.
- How do you invalidate a CDN?: Purge by URL or cache tag through the provider's API, or avoid the need with fingerprinted filenames.

**Mistakes to avoid:**
- Describing a CDN as "a cache for images"; it is an HTTP cache for any cacheable response, API GETs included.
- A long `max-age` on HTML or non-fingerprinted assets, which blocks rolling out a fix.

### Practice
- Implement cache-aside for a product endpoint in Express with Redis and a 5 second TTL, run `autocannon` while deleting the key in a loop, and watch Postgres QPS; then add request coalescing and compare.
- Implement the XFetch early-expiration helper with a 10 second TTL and a loader that takes 2 seconds, and log when recomputes happen under 200 requests per second.
- Simulate a hot key on a local Redis Cluster: hammer one key, observe one node's CPU, then add a per-process `lru-cache` with a 2 second TTL and observe again.
- Say it out loud: in two minutes, describe how you would cache a user's dashboard, who invalidates what on each write path, and what the dashboard does when Redis is down.
