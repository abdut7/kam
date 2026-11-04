# Backend Engineering (part 4)

> Beyond the question list: what senior interviews also probe.

## Node.js Runtime Internals

> Interviewers use runtime questions to separate people who use Node from people who understand it. A weak answer recites "single-threaded, non-blocking". A strong answer explains which work runs on the loop, which runs on the libuv pool, which runs in the kernel, what happens when you block the loop, and how you would measure and fix it in production.

### Concepts you must understand
- The event loop runs in phases (timers, pending callbacks, idle/prepare, poll, check, close callbacks); the poll phase is where I/O callbacks run and where the loop waits when there is nothing else to do.
- process.nextTick callbacks drain before promise microtasks, and both drain completely after every macrotask callback, so a recursive nextTick or promise chain starves I/O.
- Network I/O does not use threads at all; the kernel (epoll, kqueue, IOCP) notifies libuv. The libuv thread pool (4 threads by default, UV_THREADPOOL_SIZE) handles fs, dns.lookup, async crypto (pbkdf2, scrypt, randomBytes) and zlib.
- Blocking the loop means every concurrent request waits; the classic culprits are JSON.parse on large bodies, sync fs calls, big in-memory sorts, catastrophic regex backtracking and bcrypt with a high cost running on too few pool threads.
- worker_threads share a process and can share memory (SharedArrayBuffer); cluster forks whole processes that share one listening port; child_process runs any program. Pick by whether you need CPU parallelism, process isolation or an external binary.
- Streams exist so memory stays flat: write() returning false means "stop until drain", and stream.pipeline propagates errors and destroys every stage, which the old .pipe() does not.
- The V8 heap has its own limit, separate from the container's memory limit; --max-old-space-size raises or lowers it, and Buffers live outside the heap, so RSS can exceed heapTotal by a lot.
- Graceful shutdown is a protocol: fail readiness, stop accepting, finish in-flight requests, close pools and consumers, then exit before the orchestrator's hard kill.
- Since Node 15 an unhandled promise rejection crashes the process by default; the fix is correct error propagation, not a global handler that swallows errors.

### Q. Walk me through the Node.js event loop. Where do process.nextTick, promises, setTimeout and setImmediate run relative to each other?
**Short answer (45 seconds):** The loop cycles through phases: expired timers, pending I/O callbacks, poll (where it runs ready I/O callbacks and blocks waiting for new events), check (setImmediate), then close callbacks. After each callback finishes, Node fully drains the process.nextTick queue and then the promise microtask queue before touching the next callback. So nextTick beats promises, both beat any timer or immediate, and inside an I/O callback setImmediate always fires before a setTimeout(0).

**Deeper explanation:** The important model is "macrotask, then drain all microtasks". Timers and immediates are macrotasks that belong to a phase; nextTick and promise callbacks are not part of any phase, they run between callbacks. That is why a function that schedules another nextTick forever will stop the loop from ever reaching the poll phase: sockets stay unread and the process looks hung while CPU is at 100 percent.

```js
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
process.nextTick(() => console.log('nextTick'));
Promise.resolve().then(() => console.log('promise'));
console.log('sync');
// sync, nextTick, promise, then timeout and immediate.
// From the main module the timeout/immediate order is not guaranteed;
// inside an fs or socket callback, immediate always comes first.
```

The timeout versus immediate ambiguity from the main module exists because a 0 ms timer is really a 1 ms timer, and whether 1 ms has elapsed when the loop first checks the timers phase depends on how long startup took. Inside the poll phase the check phase is next, so setImmediate is deterministic there.

**Follow-ups they will ask:**
- Why does an await in a loop of 10,000 iterations not block the loop? : each await yields to the microtask queue, but a tight chain of already-resolved promises still starves I/O because microtasks drain fully before the next phase.
- When would you choose setImmediate over process.nextTick? : setImmediate yields to I/O first; nextTick runs before anything else and is for "finish this synchronously-looking API after the caller's code returns".
- Does an HTTP request to a database use the thread pool? : no, sockets are handled by the kernel's readiness notification, the pool is for fs, dns.lookup, crypto and zlib.

**Mistakes to avoid:**
- Saying "Node is single-threaded" and stopping there; JavaScript runs on one thread but libuv has a pool and the kernel does the I/O.
- Claiming setTimeout(0) always fires before setImmediate; it depends on where you call it.

### Q. What is the libuv thread pool, what actually runs on it, and when would you change its size?
**Short answer (45 seconds):** It is a fixed pool of 4 threads libuv uses for operations the OS cannot do asynchronously: file system calls, dns.lookup (which calls getaddrinfo), async crypto such as pbkdf2, scrypt and randomBytes, and zlib compression. Sockets never touch it. If you do a lot of fs or hashing, those 4 threads queue up and latency climbs even though the event loop is idle; UV_THREADPOOL_SIZE raises the count, up to 1024, and must be set in the environment before the pool is created.

**Deeper explanation:** A typical symptom: an auth service hashes passwords with bcrypt at cost 12, each hash takes around 250 ms of CPU, and under load the p99 for unrelated fs reads spikes. The loop is fine, the pool is saturated. Options: raise UV_THREADPOOL_SIZE to roughly the number of cores you have reserved, move hashing to a dedicated worker pool, or scale horizontally so each process gets fewer hashes.

```bash
UV_THREADPOOL_SIZE=16 node server.js
```

dns.lookup is the hidden one: every outbound http request to a hostname goes through getaddrinfo on the pool unless you cache DNS or use dns.resolve (which uses c-ares and the network, not the pool). A burst of outbound calls to a slow resolver can stall fs operations for no obvious reason.

**Follow-ups they will ask:**
- Can you change the size at runtime? : no, it is read once when the pool is first created, so set it before any pool work runs.
- Does the pool help with a CPU-heavy JSON transform in your handler? : no, that runs on the main thread; you need worker_threads for that.
- How would you see pool saturation? : measure latency of a trivial fs.stat or pbkdf2 call over time, or use the Node inspector's CPU profile and async hooks based tooling; event loop delay will look healthy, which is the giveaway.

**Mistakes to avoid:**
- Saying "increase UV_THREADPOOL_SIZE to fix slow HTTP calls"; sockets do not use the pool.
- Confusing dns.lookup (pool) with dns.resolve (network, no pool).

### Q. Something is blocking the event loop in production and p99 latency spikes every few minutes. How do you find it and fix it?
**Short answer (45 seconds):** First confirm it is the loop and not a downstream: measure event loop delay with perf_hooks.monitorEventLoopDelay and export the p99 as a metric; if it jumps when latency jumps, something synchronous is hogging the thread. Then capture a CPU profile during the spike with --cpu-prof or the inspector and read the flame graph. Usual culprits are JSON.parse or stringify of multi-megabyte payloads, sync fs calls, sorting or deduplicating large arrays, a bad regex, or a logger serializing huge objects. Fix by streaming, chunking with setImmediate, moving to worker_threads, or capping payload sizes.

**Deeper explanation:**

```js
const { monitorEventLoopDelay } = require('perf_hooks');
const h = monitorEventLoopDelay({ resolution: 20 });
h.enable();
setInterval(() => {
  metrics.gauge('loop_delay_p99_ms', h.percentile(99) / 1e6); // values are nanoseconds
  h.reset();
}, 10000);
```

The periodic pattern ("every few minutes") is a hint toward a scheduled job inside the API process: a cache rebuild that sorts 500k records, a cron that reads a large file with fs.readFileSync, or a metrics flush that stringifies a huge object. Move scheduled work out of request-serving processes. For unavoidable CPU work, either hand it to a worker pool (piscina is a common library) or break it into slices that yield with setImmediate between slices so I/O callbacks interleave.

Also check garbage collection: a heap near its limit causes long mark-sweep pauses that look identical to blocking code. Run with --trace-gc briefly to see pause durations.

**Follow-ups they will ask:**
- Why does splitting work with setImmediate help but splitting with process.nextTick does not? : nextTick runs before the loop continues, so it still starves I/O; setImmediate runs after the poll phase.
- How do you cap damage from a client sending a 50 MB JSON body? : body size limits in the parser (express.json({ limit: '1mb' })) and reject early at the gateway.
- What about a regex? : nested quantifiers on untrusted input can backtrack exponentially; use bounded patterns or a linear-time engine such as RE2.

**Mistakes to avoid:**
- Adding more pods without checking the loop; the blocking code blocks every pod the same way.
- Measuring only average latency; loop blocking shows up at the tail.

### Q. worker_threads versus cluster versus child_process: when do you use which?
**Short answer (45 seconds):** worker_threads run JavaScript in parallel inside the same process with their own event loop and V8 isolate, with cheap message passing and optional shared memory; they are for CPU-bound work like parsing, image processing or embeddings math. cluster forks full processes that share one listening port so one machine's cores all serve HTTP; today Kubernetes replicas or PM2 usually play that role. child_process runs any executable (ffmpeg, a Python script) and talks over stdio or IPC. Pick by the question: parallel JS with shared memory, more copies of my server, or run something that is not my server.

**Deeper explanation:**

```js
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
if (isMainThread) {
  const w = new Worker(__filename, { workerData: { rows } });
  w.once('message', (result) => res.json(result));
  w.once('error', next);
} else {
  parentPort.postMessage(expensiveTransform(workerData.rows));
}
```

Each worker costs a V8 isolate (tens of megabytes) and startup time, so create a pool once rather than a worker per request. Data sent with postMessage is structured-cloned, which is itself CPU work; for large numeric buffers transfer an ArrayBuffer or share a SharedArrayBuffer instead of copying.

cluster's primary process accepts connections and hands them to workers round-robin (except on Windows). Its weakness is that workers share nothing: in-memory caches and rate-limit counters become per-worker, which is the same lesson as horizontal scaling: move shared state to Redis.

child_process.fork is a Node-specific spawn with an IPC channel; spawn streams stdio and is right for large output; exec buffers the whole output and has a maxBuffer, so it is wrong for anything big.

**Follow-ups they will ask:**
- Would you use a worker to call an external API? : no, that is I/O; the main loop handles thousands of concurrent sockets fine.
- How does a worker report progress? : postMessage events, or Atomics on a SharedArrayBuffer for counters.
- Why not just run more pods instead of workers? : pods isolate failures and scale independently, but a single request that needs 2 seconds of CPU still blocks its pod; workers fix per-request blocking.

**Mistakes to avoid:**
- Treating cluster as a way to share memory between workers; they are separate processes.
- Spawning a new Worker per request; the isolate startup cost dominates.

### Q. Explain backpressure in Node streams. How would you stream a multi-gigabyte file from S3 to an HTTP response without running out of memory?
**Short answer (45 seconds):** Backpressure is the consumer telling the producer to slow down. A writable's write() returns false once its internal buffer passes highWaterMark; a correct producer stops and resumes on the drain event. pipe and pipeline do this for you; manual write loops that ignore the return value are how a 5 GB download becomes a 5 GB heap. For S3 to HTTP, get the object as a stream and run it through stream.pipeline into res, which handles backpressure, error propagation and cleanup when the client disconnects.

**Deeper explanation:**

```js
const { pipeline } = require('stream/promises');
const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');

app.get('/files/:key', async (req, res, next) => {
  try {
    const obj = await s3.send(new GetObjectCommand({ Bucket, Key: req.params.key }));
    res.setHeader('Content-Type', obj.ContentType || 'application/octet-stream');
    if (obj.ContentLength) res.setHeader('Content-Length', obj.ContentLength);
    await pipeline(obj.Body, res);
  } catch (err) {
    if (!res.headersSent) next(err); else res.destroy();
  }
});
```

Why pipeline and not .pipe(): pipe does not forward errors or destroy upstream when downstream fails. If the client closes the connection mid-download, a plain pipe leaves the S3 stream open and buffering. pipeline destroys every stage and rejects, so you can log and release.

Memory stays bounded at roughly the sum of highWaterMarks (16 KB default for byte streams per stage), regardless of file size. The same principle applies to uploads: for large files, prefer presigned URLs so bytes never pass through your Node process at all; if they must, use a multipart upload that consumes the request stream (for example the Upload helper in @aws-sdk/lib-storage).

**Follow-ups they will ask:**
- What happens to a Transform that is slow? : the readable side fills, write() returns false upstream, the source pauses; the slowest stage sets the throughput.
- Where does backpressure break in practice? : when someone collects chunks into an array, or an EventEmitter based consumer has no way to pause the producer.
- How do you handle a client that disconnects? : listen for close on req or rely on pipeline rejecting, then release the upstream.

**Mistakes to avoid:**
- Reading the whole object with fs.readFile or Body.transformToByteArray then res.send; it works at 10 MB and kills the pod at 2 GB.
- Setting a huge highWaterMark to "make it faster"; that just trades memory for throughput with no backpressure benefit.

### Q. Our Node service in Kubernetes has a 2 GB memory limit and keeps getting OOM-killed while heapUsed looks fine. What is going on and how do you fix it?
**Short answer (45 seconds):** Two different limits are in play. V8 caps only the JavaScript heap, and its default depends on the Node version and the memory it detects, so it may be set either too high for the container (V8 happily grows past what the cgroup allows and the kernel kills the pod) or too low (V8 throws heap out of memory while the container has headroom). Also, Buffers, native addon memory and thread stacks live outside the heap, so RSS can be far above heapUsed. Set --max-old-space-size explicitly to leave headroom under the container limit, and measure RSS, heapUsed and external separately.

**Deeper explanation:**

```bash
# roughly 75 percent of a 2 GB limit for the JS heap, rest for buffers and native memory
NODE_OPTIONS="--max-old-space-size=1536" node server.js
```

```js
setInterval(() => {
  const m = process.memoryUsage();
  metrics.gauge('rss_mb', m.rss / 1048576);
  metrics.gauge('heap_used_mb', m.heapUsed / 1048576);
  metrics.gauge('external_mb', m.external / 1048576); // Buffers and native
}, 15000);
```

If external climbs while heapUsed is flat, look for buffered uploads, large base64 strings, or an unbounded queue of outgoing messages. If heapUsed climbs steadily, it is a classic leak: event listeners added per request, a module-level Map cache without eviction, closures captured by long-lived timers. Take two heap snapshots a few minutes apart (v8.writeHeapSnapshot or the inspector) and compare retained sizes by constructor.

Right-sizing also matters for GC behaviour: a heap that is near its limit spends a lot of time in full mark-sweep collections, which shows up as event loop delay before the OOM happens.

**Follow-ups they will ask:**
- Why not just raise the pod limit? : if the heap limit stays below it the crash just moves; and a leak will consume anything you give it.
- How do you get a heap snapshot from a crashing pod? : --heapsnapshot-near-heap-limit writes snapshots as the heap approaches the limit; mount a volume to keep them.
- What is the difference between heapTotal and heapUsed? : heapTotal is memory V8 has reserved for the heap; heapUsed is what live objects actually occupy.

**Mistakes to avoid:**
- Treating heapUsed as total process memory; the kernel kills on RSS.
- Fixing an OOM by restarting pods on a schedule; say that is a mitigation, not a fix.

### Q. How do you implement graceful shutdown for an Express service running in Kubernetes so deploys do not drop requests?
**Short answer (45 seconds):** Kubernetes sends SIGTERM and waits terminationGracePeriodSeconds (30 by default) before SIGKILL. On SIGTERM I flip the readiness probe to failing so the Service stops routing new traffic, call server.close() so the listener stops accepting while in-flight requests finish, drain background consumers, close the Postgres pool and Redis clients, then exit 0. A hard timer shorter than the grace period forces exit if something hangs. Without this, in-flight requests get connection resets on every deploy.

**Deeper explanation:**

```js
const server = app.listen(3000);
let draining = false;
app.get('/readyz', (req, res) => res.status(draining ? 503 : 200).end());

process.on('SIGTERM', () => {
  draining = true;
  setTimeout(() => process.exit(1), 25000).unref();   // hard deadline under 30s
  setTimeout(() => {                                    // give the LB time to see 503
    server.close(async () => {
      await consumer.disconnect();                      // Kafka or BullMQ worker
      await pgPool.end();
      await redis.quit();
      process.exit(0);
    });
    server.closeIdleConnections?.();                    // keep-alive sockets with no request
  }, 5000);
});
```

The small delay before server.close matters: endpoint updates propagate asynchronously, so for a few seconds after SIGTERM new connections still arrive. Failing readiness immediately and waiting covers that window. Keep-alive is the other trap: server.close waits for idle keep-alive sockets, which can take until the client closes them; newer Node versions provide closeIdleConnections and closeAllConnections for this.

For queue consumers, stop fetching new jobs, finish the current job, and commit offsets or ack before exit; otherwise the job is redelivered and you rely on idempotency.

**Follow-ups they will ask:**
- What if a request legitimately takes 60 seconds? : raise terminationGracePeriodSeconds and the hard deadline together, or move that work to a job.
- Does PID 1 matter? : yes, if Node is PID 1 in the container it must handle signals itself; using an init like tini or the Docker --init flag also forwards signals correctly.
- How do you test this? : send SIGTERM locally while a slow request is in flight and confirm it completes while new connections are refused.

**Mistakes to avoid:**
- Calling process.exit in the SIGTERM handler immediately; that is exactly the dropped-request behaviour you were asked to prevent.
- Forgetting the hard deadline; a stuck pool.end() keeps the pod in Terminating until SIGKILL.

### Q. Express versus Fastify versus NestJS: how do you choose, and how does error handling differ, especially unhandled rejections?
**Short answer (45 seconds):** Express is minimal with the largest middleware ecosystem, but gives you nothing for validation, serialization or structure. Fastify is built around JSON Schema: requests are validated and responses serialized from schemas, plugins are encapsulated, logging is pino, and it is noticeably faster on JSON-heavy APIs. NestJS is an opinionated framework with dependency injection, modules, decorators, pipes, guards and interceptors, running on Express or Fastify underneath; it pays off on large codebases and teams, at the cost of boilerplate. For error handling, Express 4 does not catch a rejected promise from an async handler, so you must wrap handlers; Express 5 and Fastify route rejections to the error handler automatically.

**Deeper explanation:**

```js
// Express 4: a rejected promise here never reaches the error middleware
app.get('/users/:id', async (req, res) => {
  const user = await repo.find(req.params.id);  // throws -> unhandledRejection
  res.json(user);
});
// Fix: wrapper, or Express 5
const wrap = (fn) => (req, res, next) => fn(req, res, next).catch(next);
app.get('/users/:id', wrap(handler));
```

Since Node 15 an unhandled rejection crashes the process (the default mode is throw). That is the right default: a swallowed rejection means a request hangs with no response until the client times out. Log in process.on('unhandledRejection') and process.on('uncaughtException') for forensics, then let the process exit and the orchestrator restart it; continuing after an uncaught exception leaves the process in unknown state.

In Fastify, validation failures return 400 with a structured body before your handler runs, and setErrorHandler gives one place to map domain errors to status codes. In NestJS, exception filters do the same, and the ValidationPipe with class-validator DTOs replaces hand-written checks. Separate operational errors (bad input, upstream down) which you handle and map, from programmer errors (undefined is not a function) which you crash on.

**Follow-ups they will ask:**
- Why is Fastify faster at JSON? : fast-json-stringify compiles the response schema into a specialized serializer instead of generic JSON.stringify.
- Would you adopt NestJS for a small service? : usually no; the DI and module overhead is for codebases where consistency across many developers matters.
- How do you attach a request id to every log line? : AsyncLocalStorage holds per-request context across awaits; pino and Nest both integrate with it.

**Mistakes to avoid:**
- Registering a global unhandledRejection handler that just logs and continues; you convert a crash into silent hung requests.

### Practice
- Write a tiny script that fires setTimeout(0), setImmediate, nextTick and a promise from the main module and from inside an fs.readFile callback; predict the order, then run it.
- Add monitorEventLoopDelay to a toy Express app, then hit an endpoint that sorts 2 million numbers and watch p99 loop delay; move the sort into a worker_threads pool and compare.
- Stream a 1 GB file through zlib.createGzip to disk with stream.pipeline while watching process.memoryUsage(); then replace pipeline with manual write() calls that ignore the return value and watch the heap grow.
- Run a local server with --max-old-space-size=100, push objects into a module-level array per request, and take two heap snapshots to find the retainer.
- Say it out loud: explain to a colleague in two minutes why a bcrypt-heavy login endpoint can slow down unrelated file reads, and the two fixes you would consider.

## Authentication, Authorization & API Security

> Security questions are where "I used Passport and a JWT library" falls apart. Interviewers want to hear that you know what each token is for, where it lives, how it gets revoked, which attacks each design is exposed to, and what you check on every request. Strong answers name the attack, the mitigation and the trade-off in the same breath.

### Concepts you must understand
- A session cookie is a reference to server-side state (revocable instantly, needs a shared store); a JWT is a self-contained signed claim set (verifiable anywhere, hard to revoke, visible to anyone who holds it).
- Access tokens should be short-lived and refresh tokens should rotate on every use, with reuse detection that revokes the whole token family when a stale refresh token appears.
- OAuth 2.0 is about delegated authorization (grants and scopes); OpenID Connect layers identity on top with the id_token, discovery document and userinfo endpoint. Authorization code with PKCE is the flow for anything with a user; client credentials is for machine-to-machine.
- RBAC maps users to roles to permissions and is easy to reason about; ABAC evaluates policies over attributes of subject, resource, action and context, which is what multi-tenant ownership rules actually need.
- Every webhook you accept must be verified: HMAC over the raw body plus a timestamp, constant-time comparison, replay window, idempotent handling by event id.
- CORS is a browser rule about who may read a cross-origin response; CSRF is about a browser automatically attaching cookies to a request the user did not intend. One does not fix the other.
- Rate limiting is an algorithm choice: fixed window is simple but allows a double burst at the boundary, sliding window log is exact but memory heavy, token bucket allows controlled bursts with a steady refill.
- Passwords get a slow, salted, memory-hard hash (argon2id, or bcrypt with a tuned cost); API keys and tokens are high-entropy random strings, so a fast SHA-256 hash at rest is fine for them.
- Secrets belong in a secrets manager injected at runtime with least-privilege access and rotation, not in images, repos or long-lived environment files; mTLS gives service-to-service identity using certificates on both ends, usually handled by a mesh.

### Q. Sessions or JWTs for a new SaaS web app: which do you pick and why?
**Short answer (45 seconds):** For a first-party web app with a browser client I default to server-side sessions: an opaque session id in an httpOnly, Secure, SameSite cookie backed by Redis. Logout and "sign out everywhere" are a single delete, nothing sensitive sits in the browser, and the cookie is tiny. JWTs earn their place when many services or third parties must verify identity without calling back to an auth server, or for mobile and API clients. The honest trade-off: JWTs remove a lookup per request but make revocation and rotation your problem.

**Deeper explanation:** A session store lookup is one Redis GET per request, which is sub-millisecond and horizontally scalable, so "stateless scales better" is rarely the real constraint. What JWTs buy is verification with a public key anywhere: a gateway, a Go service, a Python worker can all check RS256 or ES256 signatures without shared state. Use asymmetric keys when more than one service verifies, HS256 only when the issuer and verifier are the same deployable, and publish keys via a JWKS endpoint so you can rotate them.

```js
app.use(session({
  store: new RedisStore({ client: redis }),
  secret: process.env.SESSION_SECRET,
  cookie: { httpOnly: true, secure: true, sameSite: 'lax', maxAge: 8 * 3600 * 1000 },
  resave: false, saveUninitialized: false,
}));
```

Where the token lives decides the attack surface. A cookie is attached automatically, which is the CSRF problem (mitigated by SameSite plus an Origin check or a CSRF token). A token in localStorage is readable by any injected script, which is the XSS problem, and a stolen JWT is valid until expiry. That is why access tokens should expire in minutes and the refresh token should be the thing in an httpOnly cookie.

**Follow-ups they will ask:**
- How do you store passwords? : argon2id (the current OWASP first choice) or bcrypt with a cost tuned so one hash takes a few hundred milliseconds, always per-user salted by the library; never MD5, SHA-1 or unsalted SHA-256.
- Why not a JWT in localStorage for an SPA? : XSS turns into full account takeover with no revocation path.

**Mistakes to avoid:**
- "JWT because it is stateless and scales": a Redis lookup is not your bottleneck, and you will add a deny-list anyway the first time someone asks for forced logout.

### Q. Design the access token and refresh token flow. How do you rotate, revoke, and implement logout with JWTs?
**Short answer (45 seconds):** The access token is a short-lived JWT, 5 to 15 minutes, sent as a Bearer header and verified locally. The refresh token is an opaque high-entropy string, stored hashed in the database with the user id, a family id and an expiry, and delivered in an httpOnly cookie scoped to the refresh path. Every refresh call rotates: issue a new pair, mark the old refresh token used. If a used token is presented again, that is theft or a replay, so revoke the whole family. Logout deletes the refresh token server-side and, if you need instant effect, adds the access token's jti to a short-TTL deny-list in Redis.

**Deeper explanation:**

```sql
CREATE TABLE refresh_tokens (
  token_hash  TEXT PRIMARY KEY,          -- sha256 of the opaque token
  user_id     UUID NOT NULL,
  family_id   UUID NOT NULL,             -- one family per login/device
  expires_at  TIMESTAMPTZ NOT NULL,
  used_at     TIMESTAMPTZ,               -- set on rotation
  revoked_at  TIMESTAMPTZ
);
```

Refresh handler logic: look up by hash; if missing or revoked, 401; if used_at is set, revoke everything in family_id and 401 (reuse detection); otherwise set used_at, insert the new token in the same family, return a new access token. Do the read-and-mark in one transaction, or an UPDATE ... WHERE used_at IS NULL RETURNING, so two concurrent refreshes cannot both succeed.

Revocation of access tokens has three honest options: accept the window until expiry (fine at 5 minutes for most apps), keep a deny-list of jti with TTL equal to the remaining lifetime (one Redis lookup per request, cheap), or store a per-user token_version and embed it in the token so a password change bumps the version and invalidates every token at once.

**Follow-ups they will ask:**
- Why hash the refresh token at rest? : a database leak would otherwise hand out live sessions; hashing a 256-bit random value with SHA-256 is enough because it cannot be brute-forced.
- What does the user see if reuse detection fires? : all devices in that family are logged out and they must sign in again; log it as a security event.

**Mistakes to avoid:**
- Long-lived access tokens "so users do not get logged out"; that is what the refresh token is for.
- Issuing refresh tokens that never rotate; a stolen one is then permanent.

### Q. Explain the OAuth 2.0 authorization code flow with PKCE. Why is the implicit flow deprecated, when do you use client credentials, and what does OpenID Connect add?
**Short answer (45 seconds):** The client generates a random code_verifier, hashes it into a code_challenge and redirects the user to the provider's authorize endpoint with client_id, redirect_uri, scope, state and the challenge. The user logs in and consents, the provider redirects back with a one-time code, and the client exchanges code plus the original verifier at the token endpoint for tokens. PKCE binds the code to the client that started the flow, so an intercepted code is useless. Implicit flow returned tokens in the URL fragment, leaking them through history, referrers and logs, with no client authentication and no refresh tokens, which is why it is dropped. Client credentials is for one service calling another with no user: POST the client id and secret, get a scoped access token. OIDC adds the id_token (a signed JWT about who logged in), the nonce, discovery and userinfo, turning OAuth's authorization into authentication.

**Deeper explanation:**

```text
Browser/SPA                      Auth server                      API
  | code_verifier = random(43..128 chars)
  | code_challenge = base64url(sha256(verifier))
  |--- GET /authorize?response_type=code&client_id&redirect_uri
  |        &scope=openid profile&state&code_challenge&code_challenge_method=S256
  |<-- 302 redirect_uri?code=...&state=...   (verify state matches)
  |--- POST /token  grant_type=authorization_code&code&code_verifier&redirect_uri&client_id
  |<-- { access_token, id_token, refresh_token, expires_in }
  |---------------------------------- Authorization: Bearer access_token --->|
```

state defends against CSRF on the callback (an attacker tricking your browser into completing their login into your session); nonce in OIDC binds the id_token to this request. Public clients (SPAs, mobile) have no secret, so PKCE is mandatory for them; the OAuth 2.1 draft requires PKCE for every client. The id_token is for your app to establish the user; the access token is for calling APIs; do not use the id_token as an API bearer token because its audience is your client, not the API.

**Follow-ups they will ask:**
- What do you validate in an id_token? : signature against the provider's JWKS, iss, aud equals your client_id, exp, and nonce.
- Why is client credentials unsuitable for a browser client? : the secret would ship to every user; browsers are public clients.
- What does the scope offline_access do in many providers? : requests a refresh token.

**Mistakes to avoid:**
- Describing OAuth as a login protocol; without OIDC it only says what the token may do, not who the user is.
- Skipping state or redirect_uri exact matching; open redirectors and code injection follow.

### Q. RBAC versus ABAC: how would you model permissions for a multi-tenant B2B product where users have roles but also own specific resources?
**Short answer (45 seconds):** Start with RBAC for the coarse structure: tenant admin, member, viewer, mapped to permission strings like project:write. Then handle the ownership and tenancy rules with attribute checks, because "a member can edit a document if it belongs to their tenant and they created it or are listed as a collaborator, unless the document is archived" cannot be expressed as a role. Put the check in one authorization function called by every handler, give it the subject, action and resource, and make tenant_id a mandatory predicate on every query so isolation does not depend on remembering a WHERE clause.

**Deeper explanation:**

```ts
type Decision = 'allow' | 'deny';
function can(user: User, action: string, doc: Doc): Decision {
  if (doc.tenantId !== user.tenantId) return 'deny';            // tenancy first, always
  if (user.roles.includes('admin')) return 'allow';
  if (action === 'read') return 'allow';
  if (action === 'write' && doc.status !== 'archived' &&
      (doc.ownerId === user.id || doc.collaborators.includes(user.id))) return 'allow';
  return 'deny';
}
```

Three design points matter in interviews. First, authorization happens after fetching the resource, so the check sees real attributes; checking only the URL parameter is how broken object level authorization happens. Second, roles are per tenant, not global: a user can be admin in one workspace and viewer in another, so the membership table carries (user_id, tenant_id, role). Third, defense in depth at the database: Postgres row-level security with a session variable for the current tenant means a forgotten filter returns zero rows instead of another customer's data.

When policies grow (dozens of resource types, rules shared between services), move to a policy engine: Open Policy Agent with Rego, Casbin, or a relationship-based system like OpenFGA or SpiceDB modelled on Google's Zanzibar, where permissions are derived from tuples such as document:42#editor@user:7. Those also answer "list everything this user can see", which an in-code function cannot do efficiently.

**Follow-ups they will ask:**
- How do you avoid an authorization check per item on a list endpoint? : filter in the query (tenant and ownership predicates, or the policy engine's list-objects API) instead of fetching then filtering.
- Where do permissions live in the request? : resolved from the database or a short-TTL cache per request, not baked into a long-lived token.

**Mistakes to avoid:**
- Checking roles in middleware only by route; function-level checks miss object ownership.
- Encoding the tenant in a client-supplied header or body field instead of deriving it from the authenticated principal.

### Q. How do you secure webhooks, both the ones you send to customers and the ones you receive from providers like Stripe, and how do you manage API keys?
**Short answer (45 seconds):** Sign every webhook with HMAC-SHA256 over a timestamp plus the raw body using a per-endpoint secret, and send the timestamp and signature in a header. The receiver recomputes over the exact raw bytes, compares in constant time, rejects anything older than a few minutes, and deduplicates by event id because retries are guaranteed. API keys are random 256-bit strings shown once, stored as a SHA-256 hash with a visible prefix for lookup, scoped to permissions, sent in a header, and rotatable without downtime by allowing two active keys.

**Deeper explanation:**

```js
// receiving: body must be the raw bytes, so register before express.json()
app.post('/webhooks/pay', express.raw({ type: 'application/json' }), (req, res) => {
  const [t, v1] = parseHeader(req.get('X-Signature')); // "t=1700000000,v1=hex"
  if (Math.abs(Date.now() / 1000 - Number(t)) > 300) return res.sendStatus(400);
  const expected = crypto.createHmac('sha256', secret)
    .update(`${t}.${req.body}`).digest();
  const given = Buffer.from(v1, 'hex');
  if (given.length !== expected.length || !crypto.timingSafeEqual(given, expected))
    return res.sendStatus(401);
  enqueue(JSON.parse(req.body));   // ack fast, process async, dedupe by event.id
  res.sendStatus(200);
});
```

Signing the raw body is the detail people miss: if you parse JSON and re-stringify, key order and whitespace change and the signature fails intermittently. Stripe's Stripe-Signature header with t= and v1= is this exact scheme. The timestamp bounds replay; the event id handles the retries the provider sends when you were slow or returned 5xx.

For sending, keep a per-subscription secret, retry with exponential backoff on non-2xx for a bounded period, record every delivery attempt for the customer to see, and disable endpoints that fail for days. Never follow redirects, and resolve and block private IP ranges before connecting, or your webhook sender becomes an SSRF tool into your own network.

**Follow-ups they will ask:**
- Why timingSafeEqual? : a plain string comparison returns early on the first differing byte, which leaks the signature one byte at a time over many requests.
- Where do the HMAC secrets live? : in a secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault) injected at startup, with rotation that supports two valid secrets during the overlap.
- What is mTLS and when would you use it instead? : both client and server present certificates, giving mutual identity at the transport layer; a service mesh like Istio or Linkerd does it for internal service-to-service calls, but for third-party webhooks HMAC is far simpler to adopt.

**Mistakes to avoid:**
- Verifying the signature over the parsed and re-serialized body.
- Putting API keys in query strings; they end up in access logs, proxies and browser history.

### Q. Explain the difference between CORS and CSRF. If my API sets CORS headers correctly, am I protected against CSRF?
**Short answer (45 seconds):** No. CORS is a browser-enforced read permission: it decides whether JavaScript on origin A may read the response from origin B, and for non-simple requests it asks first with a preflight. CSRF is about the browser automatically attaching cookies to a request that a malicious page caused, like a form POST to your /transfer endpoint; the attacker does not need to read the response, the side effect already happened. Simple requests such as a form-encoded POST are sent without preflight regardless of CORS. CSRF defenses are SameSite cookies, checking the Origin or Referer header, and synchronizer tokens; CORS is about controlling which origins can call your API from JavaScript with credentials.

**Deeper explanation:**

```text
Preflight (triggered by PUT/DELETE/PATCH, Authorization header, Content-Type: application/json):
  OPTIONS /api/orders
  Origin: https://app.example.com
  Access-Control-Request-Method: PUT
  Access-Control-Request-Headers: authorization, content-type
Response:
  Access-Control-Allow-Origin: https://app.example.com     (never * with credentials)
  Access-Control-Allow-Credentials: true
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE
  Access-Control-Allow-Headers: Authorization, Content-Type
  Access-Control-Max-Age: 600
```

CORS protects users, not servers: curl ignores it entirely. Reflecting the request's Origin header back as Allow-Origin with credentials true is the same as disabling CORS; keep an explicit allow-list.

CSRF only matters for cookie-authenticated endpoints. A Bearer token in the Authorization header is not attached automatically, so token-based APIs are not CSRF-able, but their SPAs are XSS-exposed instead, which is the trade-off from the sessions question. Chrome treats cookies without SameSite as Lax by default, which blocks cross-site POSTs carrying cookies but still allows top-level GET navigations, so state-changing GET endpoints remain vulnerable; make them POST. SameSite=Strict breaks "arrive from an email link and be logged in", so most apps use Lax for the session cookie and Strict for the refresh cookie.

**Follow-ups they will ask:**
- How do you implement a CSRF token in Express? : generate per session, embed in forms or a meta tag, require it in a header or body field, compare server-side.
- What does Access-Control-Max-Age do? : it lets the browser cache a preflight result so repeated calls skip the OPTIONS round trip.

**Mistakes to avoid:**
- "We set Access-Control-Allow-Origin: * so CORS is handled": with credentials that is invalid, and without credentials it is public anyway.
- Claiming SameSite alone solves CSRF for all cases; GET side effects and older browsers remain.

### Q. Which items from the OWASP API Security Top 10 have you actually seen in Node codebases, and how do they happen?
**Short answer (45 seconds):** The ones I see most are broken object level authorization, where /orders/:id checks that you are logged in but not that the order is yours; broken object property level authorization, which includes mass assignment when a handler does Model.create(req.body) and a client adds role: 'admin', and over-exposure when you return the whole Mongoose document including password hashes; unrestricted resource consumption, meaning no body limits, no pagination caps, no rate limits, and an LLM endpoint with no token cap; and server-side request forgery wherever a user supplies a URL that the server fetches. Broken authentication rounds it out: predictable reset tokens, no brute-force protection, long-lived tokens.

**Deeper explanation:**

```js
// Mass assignment: anything the client sends becomes a field
const user = await User.create(req.body);
// Fix: whitelist with a schema, and set privileged fields server-side
const body = signupSchema.parse(req.body);              // zod or Joi: only known fields
const user = await User.create({ ...body, role: 'member', tenantId: req.user.tenantId });
```

The 2023 list is: broken object level authorization, broken authentication, broken object property level authorization, unrestricted resource consumption, broken function level authorization, unrestricted access to sensitive business flows, server side request forgery, security misconfiguration, improper inventory management, unsafe consumption of APIs. Function level authorization failures look like an admin route that exists in the router but whose only protection is that the UI hides the button. Unsafe consumption is trusting a partner API's response without validation, which for AI backends includes treating LLM output as trusted input to a database or shell.

For SSRF (webhook URLs, "import from URL", image fetchers): resolve DNS, reject private and link-local ranges including metadata endpoints such as 169.254.169.254, disallow redirects or re-validate after each one, and run the fetcher in a network-restricted egress.

**Follow-ups they will ask:**
- How do you find BOLA systematically? : every handler that loads by id must scope the query by the principal (WHERE id = $1 AND tenant_id = $2), and tests should assert a 404 or 403 for another tenant's id.
- How do you avoid leaking fields in responses? : explicit response serializers or DTOs, never the raw ORM document; select only needed columns.
- What logging helps? : log authorization denials with principal, resource and action; a spike means someone is enumerating ids.

**Mistakes to avoid:**
- Listing the names without a concrete code-level example; interviewers want the mechanism.

### Q. Compare rate limiting algorithms and show how you would implement one in Redis for a distributed API.
**Short answer (45 seconds):** Fixed window counts requests per minute in one key; it is trivial but a client can send 2x the limit across a window boundary. Sliding window log stores a timestamp per request in a sorted set and counts the last 60 seconds; exact, but memory grows with the limit. Sliding window counter approximates by weighting the previous window; cheap and smooth. Token bucket holds up to N tokens refilled at a steady rate, so clients get controlled bursts with a predictable average. For a multi-instance API the counter must be in Redis, and the check-and-decrement must be atomic, so I use a small Lua script or MULTI with the result checked after EXEC.

**Deeper explanation:**

```lua
-- KEYS[1] = bucket key; ARGV = capacity, refill_per_second, now_ms, cost
local cap, rate, now, cost = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3]), tonumber(ARGV[4])
local tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens') or cap)
local ts = tonumber(redis.call('HGET', KEYS[1], 'ts') or now)
tokens = math.min(cap, tokens + (now - ts) / 1000 * rate)
local allowed = 0
if tokens >= cost then tokens = tokens - cost; allowed = 1 end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(cap / rate * 1000) + 1000)
return allowed
```

Lua runs atomically on the Redis server, so two instances cannot both see 1 token and both allow. Keys are per identity (API key, user id, or IP as a last resort behind a proxy where you trust X-Forwarded-For only from your own load balancer). Return 429 with a Retry-After header and the standard rate limit headers so clients can back off instead of hammering.

Put the limiter as early as possible (gateway or first middleware) so rejected requests cost almost nothing, and fail open or closed deliberately: if Redis is down, most APIs choose to fail open and alert, while an auth endpoint protecting against brute force should fail closed.

**Follow-ups they will ask:**
- Where do you rate limit an LLM endpoint? : per user on requests and on tokens consumed, using the response's usage counts to debit a bucket after the fact plus an estimate before.
- Why not rate limit in process memory? : each instance would allow the full limit, so the real limit is N times higher and changes with autoscaling.

**Mistakes to avoid:**
- INCR then separately checking and EXPIRE without atomicity; a crash between them leaves a key that never expires and locks the client out.
- Rate limiting by IP alone; shared NATs and mobile carriers put thousands of users behind one address.

### Practice
- Build the refresh token rotation table and handler with reuse detection, then write a test where the same refresh token is presented twice and assert the whole family is revoked.
- Run through the authorization code with PKCE flow against a real provider (Auth0, Keycloak or Google) with openid-client, print the id_token claims and verify them by hand against the JWKS.
- Implement the token bucket Lua script in Redis, hit it from two Node processes at once with a load tool, and confirm the combined admitted rate matches the configured rate.
- Write a webhook receiver that verifies an HMAC over the raw body, then break it on purpose by registering express.json() first and watch the signature mismatch.
- Say it out loud: in ninety seconds, explain to a frontend engineer why their SPA should not keep the JWT in localStorage and what you will give them instead.

## Resilience & Microservice Patterns

> This section is where interviewers test whether you have lived through a cascading failure. Weak answers list patterns by name. Strong answers explain the failure each pattern prevents, what it costs, how the patterns compose (timeouts under retries under breakers under bulkheads), and when the right answer is "do not split the service".

### Concepts you must understand
- Every network call needs a timeout, and timeouts must nest: a caller's deadline has to exceed the sum of its downstream attempts, otherwise retries happen after the client has already given up.
- Retries amplify load; exponential backoff with jitter spreads them out, a retry budget caps them, and only idempotent operations or explicitly retry-safe errors (connection reset, 503, 429) may be retried.
- A circuit breaker stops calling a dependency that is failing so it can recover and so your threads, sockets and event loop are not tied up waiting; it has closed, open and half-open states.
- Bulkheads isolate resources (connection pools, concurrency limits, worker pools, deployments) per dependency or tenant so one slow thing cannot consume everything; load shedding rejects excess work early with 503 so the work you do accept finishes.
- A saga is a sequence of local transactions with compensating actions; choreography spreads the flow across event handlers, orchestration centralizes it in a durable state machine.
- The dual write problem (database commit plus message publish cannot be atomic) is solved by the transactional outbox: write the event in the same transaction and relay it afterwards, accepting at-least-once delivery.
- CQRS separates write and read models; event sourcing stores the events as the source of truth and derives state from them. They are independent choices, both carry eventual consistency and schema evolution costs.
- An API gateway handles edge concerns (TLS, auth, rate limits, routing); a BFF shapes data for one client type; service discovery in Kubernetes is DNS plus Services, and a mesh adds mTLS, retries and telemetry in sidecars.
- Microservices trade in-process simplicity for independent deployment and scaling; a modular monolith with enforced boundaries gets most of the organisation benefits with none of the network failure modes, and the strangler fig pattern is how you migrate incrementally when you do split.

### Q. How do you set timeouts and retries across a chain of service calls so that a slow dependency does not cause a retry storm?
**Short answer (45 seconds):** Start from the user-facing deadline and work inward: if the API promises 2 seconds, each downstream call gets a budget such that attempts plus backoff fit inside it, and the remaining budget is passed downstream as a deadline. Retry only operations that are idempotent or errors that are safe (connection refused, reset, 503, 429 honouring Retry-After), use exponential backoff with full jitter, cap attempts at two or three, and enforce a retry budget so retries never exceed a small percentage of normal traffic. Without jitter every client retries at the same instant and the dependency that was recovering gets hit by a synchronized wave.

**Deeper explanation:**

```js
async function withRetry(fn, { retries = 2, baseMs = 100, capMs = 1500, signal } = {}) {
  for (let attempt = 0; ; attempt++) {
    try { return await fn(signal); }
    catch (err) {
      if (attempt >= retries || !isRetryable(err) || signal?.aborted) throw err;
      const delay = Math.random() * Math.min(capMs, baseMs * 2 ** attempt); // full jitter
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}
const res = await withRetry((s) => fetch(url, { signal: s }), { signal: AbortSignal.timeout(1800) });
```

isRetryable should say yes to network errors and 503 or 429, no to 400, 401, 403, 404 and 422 (retrying a bad request just repeats it), and only yes to POST when the request carries an idempotency key. The retry budget idea (used by Google and in Envoy) is: track the ratio of retries to first attempts over a window and stop retrying when it exceeds, say, 10 percent; that converts a cascading failure into a slightly elevated error rate.

Deadline propagation is the piece that separates senior answers: gRPC carries deadlines natively; over HTTP you pass a header with the remaining milliseconds and each hop subtracts its own time. Otherwise the bottom of the chain keeps working on requests whose caller timed out seconds ago, which is pure wasted capacity during an incident.

**Follow-ups they will ask:**
- Why full jitter rather than a fixed backoff? : fixed backoff keeps clients synchronized; random delay in [0, cap] decorrelates them and lowers peak load on the recovering service.
- Should retries happen at the gateway or in the service? : one layer only; retries stacked at three layers multiply into 27 attempts.

**Mistakes to avoid:**
- Retrying non-idempotent POSTs without an idempotency key; you create duplicate orders during the exact incident you are trying to survive.

### Q. Explain the circuit breaker pattern. How does it differ from retries, and how would you implement one in a Node service?
**Short answer (45 seconds):** A breaker wraps calls to one dependency and tracks failures over a rolling window. Closed means calls flow normally. When failures cross a threshold with enough volume it opens: calls fail immediately with a fallback or error, without touching the dependency, so your sockets and event loop are not tied up and the dependency gets breathing room. After a reset timeout it goes half-open and lets a trial request through; success closes it, failure reopens it. Retries try harder; a breaker tries less. In Node I use opossum with one breaker per dependency and export state changes as metrics.

**Deeper explanation:**

```js
const CircuitBreaker = require('opossum');
const inventoryBreaker = new CircuitBreaker(getStock, {
  timeout: 800,                   // a call slower than this counts as a failure
  errorThresholdPercentage: 50,   // open when half of calls in the window fail
  volumeThreshold: 20,            // but only once there is enough traffic to judge
  resetTimeout: 10000,            // try half-open after 10s
});
inventoryBreaker.fallback(() => ({ stock: null, degraded: true }));
inventoryBreaker.on('open', () => log.warn({ dep: 'inventory' }, 'breaker open'));
const stock = await inventoryBreaker.fire(sku);
```

Two design decisions matter. First, granularity: one breaker per dependency (or per dependency and operation), never one global breaker, otherwise an outage in the recommendations service blocks checkout. Second, what the fallback is: a cached value, a default, a degraded response with a flag, or a fast error. The product decision "checkout works without stock hints" is the actual resilience; the breaker is just the mechanism.

The volume threshold avoids opening on two failures at 3 a.m. with one request per minute. Timeouts counting as failures is essential, because a dependency that is slow but not erroring is the more common cascading failure. Breakers are per process, so each pod discovers the outage independently; that is acceptable, and a shared breaker in Redis adds a dependency to your resilience mechanism.

**Follow-ups they will ask:**
- What happens to in-flight requests when the breaker opens? : they complete or time out on their own; only new calls are short-circuited.
- How do you test it? : inject failures (a toxiproxy or a stub returning 503) and assert the breaker opens, the fallback is served, and it closes after recovery.

**Mistakes to avoid:**
- Describing the states without saying why the breaker helps the caller (frees resources) as well as the callee (reduces load).

### Q. One slow downstream dependency took down your whole API last quarter. What are bulkheads and load shedding, and how would you apply them?
**Short answer (45 seconds):** The failure mode is resource exhaustion: every request waiting on the slow dependency holds a connection, a pool slot and memory, until the healthy endpoints starve too. Bulkheads partition resources so each dependency, and sometimes each tenant, gets its own bounded pool and concurrency limit; when inventory is slow, only inventory calls queue, and the limit makes them fail fast instead of piling up. Load shedding is the other half: when the process is over capacity (queue depth, event loop delay, in-flight count), reject new work immediately with 503 and Retry-After so the requests you already accepted finish within their deadlines.

**Deeper explanation:**

```js
const pLimit = require('p-limit');
const limits = { inventory: pLimit(50), pricing: pLimit(100) };  // per-dependency concurrency

async function callInventory(sku) {
  if (limits.inventory.pendingCount > 200) throw new ServiceBusy('inventory');  // fail fast
  return limits.inventory(() => inventoryBreaker.fire(sku));
}
```

The queue bound is the point: an unbounded queue just moves the latency, a bounded one converts overload into fast errors that the client can retry later or degrade around. Separate Postgres pools for latency-sensitive API queries and for background reporting is the same idea; so is running batch consumers in a separate deployment from the HTTP pods so a backlog cannot steal CPU from requests.

For shedding, Node gives you a direct signal: event loop delay. If p99 loop lag exceeds, say, 200 ms, the process is already failing its deadlines, so a middleware that returns 503 for a slice of new requests (toobusy-js is built on this) keeps the rest fast. Shed the cheapest and least important first: health checks and already-authenticated critical paths stay, anonymous expensive searches go. Shedding is also what makes autoscaling work; a pod that accepts everything and times out looks healthy to the autoscaler while serving nothing.

**Follow-ups they will ask:**
- Where do you put per-tenant bulkheads? : concurrency limit keyed by tenant at the gateway or first middleware, so one customer's traffic spike degrades only that customer.
- Why not just scale out? : scaling takes minutes, overload takes seconds, and if the bottleneck is the slow dependency, more pods just queue more calls against it.

**Mistakes to avoid:**
- Proposing bigger connection pools; the pool was not the problem, the unbounded waiting was.

### Q. Walk me through an order placement flow across payments, inventory and shipping services as a saga. Choreography or orchestration, and why?
**Short answer (45 seconds):** A saga replaces the distributed transaction with a sequence of local transactions, each with a compensating action: reserve stock (release), charge payment (refund), create shipment (cancel). With choreography each service reacts to events, OrderPlaced leads to StockReserved leads to PaymentCaptured, and emits its own; it is decoupled but the overall flow lives nowhere, so debugging and changing it is painful. With orchestration a durable orchestrator sends commands, waits for replies, and runs compensations on failure. For anything with more than three steps or real money I choose orchestration, implemented either as a saga state table in Postgres driven by a worker, or with a workflow engine such as Temporal.

**Deeper explanation:**

```text
Orchestrator (durable state per order)
  CREATED -> RESERVING_STOCK -> CHARGING -> SHIPPING -> COMPLETED
     |            |  fail           |  fail          |  fail
     |            v                 v                v
     |        CANCELLED     RELEASE_STOCK -> CANCELLED   REFUND -> RELEASE_STOCK -> CANCELLED
```

The orchestrator persists the saga state before every command, so a crash mid-flow resumes from the last step instead of forgetting the order. Every command carries the saga id as an idempotency key, because the message layer is at-least-once and the orchestrator will resend after a timeout. Each participant must handle "reserve stock for order 42" twice without double reserving.

Isolation is the awkward part: between the stock reservation and the payment capture, other transactions can see partial state. Sagas handle this with semantic locks (the order is in PENDING, the stock is in a reserved_quantity column rather than subtracted) and with commutative updates where possible. Compensations are not rollbacks: a refund is a new transaction the customer sees, and some steps cannot be compensated at all (an email sent), so order the steps so that the non-compensatable ones come last.

**Follow-ups they will ask:**
- How does the orchestrator time out a step? : a scheduled check per saga (a due_at column polled by the worker, or the workflow engine's timer) that triggers compensation when no reply arrives.
- Where does the saga state live? : in the orchestrating service's own database, written in the same transaction as its outbox event so command publishing is reliable.

**Mistakes to avoid:**
- Calling it two-phase commit; sagas exist precisely because 2PC across heterogeneous services is impractical.

### Q. Your service updates Postgres and publishes a Kafka event for each order. What is the dual write problem and how does the transactional outbox solve it?
**Short answer (45 seconds):** If I commit to Postgres and then publish to Kafka, a crash between the two loses the event forever; if I publish first and the commit fails, downstream systems act on an order that does not exist. There is no transaction spanning both systems. The outbox pattern writes the event into an outbox table in the same database transaction as the business row, so they commit or roll back together. A separate relay reads unpublished rows and publishes them, marking them sent. Delivery becomes at-least-once, so consumers deduplicate by event id. Change data capture with Debezium can replace the polling relay by reading the Postgres WAL.

**Deeper explanation:**

```sql
BEGIN;
INSERT INTO orders (id, user_id, total_cents, status) VALUES ($1, $2, $3, 'PLACED');
INSERT INTO outbox (id, aggregate_id, event_type, payload)
VALUES (gen_random_uuid(), $1, 'OrderPlaced', $4::jsonb);
COMMIT;

-- relay worker, safe to run on several instances
SELECT id, aggregate_id, event_type, payload FROM outbox
WHERE published_at IS NULL ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED;
-- publish each to Kafka with key = aggregate_id, then UPDATE outbox SET published_at = now()
```

Keying the Kafka message by aggregate_id keeps all events for one order on one partition, so consumers see them in order. SKIP LOCKED lets multiple relay instances share the work without double publishing within one batch; a crash after publishing but before marking still produces a duplicate, which is why the consumer side needs an inbox table or idempotent handlers keyed by event id. Delete or archive published rows so the table does not grow forever; a partial index on published_at IS NULL keeps the relay query fast.

Polling adds latency (a few hundred milliseconds is typical) and load; Postgres LISTEN/NOTIFY can wake the relay immediately. Debezium reads the WAL instead, so there is no polling at all and no application relay code, at the cost of running Kafka Connect.

**Follow-ups they will ask:**
- Why not use Kafka transactions? : they make the Kafka side atomic, not the Postgres commit plus the publish.
- What does the consumer's inbox look like? : a processed_events table keyed by event id, inserted in the same transaction as the consumer's own writes, with a unique violation meaning "already handled".

**Mistakes to avoid:**
- Publishing inside the transaction before commit "so it is atomic"; Kafka cannot roll back when Postgres does.
- Promising exactly-once; the realistic contract is at-least-once delivery with idempotent consumers.

### Q. What are CQRS and event sourcing, how are they different, and when would you actually use them?
**Short answer (45 seconds):** CQRS splits the model used for writes from the models used for reads: commands go through domain logic into the write store, and read models are denormalized projections built from change events, so each can be shaped and scaled for its job. Event sourcing changes what you store: instead of the current row, you append every state change as an event and rebuild state by replaying them, which gives a complete audit log and lets you create new projections from history. They are independent; most CQRS systems do not use event sourcing. I would reach for CQRS when read and write shapes diverge badly, and for event sourcing in domains that are naturally a ledger, like payments, inventory movements or an agent's action history. For a CRUD app both add cost without benefit.

**Deeper explanation:**

```text
Command: ReserveStock(sku, qty)
  -> load events for sku, fold into current state, validate, append StockReserved
Projections (consumers of the event stream):
  -> stock_by_warehouse table (Postgres) for the API
  -> search index (OpenSearch) for the dashboard
  -> daily movements (BigQuery) for finance
```

Event sourcing pays off through replay: a bug in a projection is fixed by rebuilding it from events, and a new requirement ("show stock as of last Tuesday") is a new projection, not a migration. The costs are real. Events are immutable, so changing their shape means versioning plus upcasters that translate old events on read. Loading an aggregate with 50,000 events needs snapshots. Projections are eventually consistent, so the UI must handle "I just created it and the list does not show it yet".

CQRS without event sourcing is just a well-known architecture: write to normalized Postgres tables, publish change events through an outbox, and maintain read models in Redis, MongoDB or materialized views. That is often the pragmatic answer to "the dashboard query joins nine tables and times out".

**Follow-ups they will ask:**
- How do you handle a projection falling behind? : monitor consumer lag, surface a version or timestamp on reads so clients can wait for their own write, and rebuild from the stream if it is corrupted.
- What is a snapshot? : a stored fold of the first N events so loading an aggregate replays only the tail.

**Mistakes to avoid:**
- Treating CQRS and event sourcing as a package deal.

### Q. What does an API gateway do that a load balancer does not, when do you add a BFF, and how does service discovery work in Kubernetes?
**Short answer (45 seconds):** A load balancer spreads connections; a gateway understands requests: it terminates TLS, validates JWTs or API keys, applies rate limits and quotas, routes by path or header to services, rewrites and versions, and emits uniform access logs. Kong, Envoy-based gateways, NGINX and the cloud providers' gateways all fit. A backend for frontend is a thin service owned by a client team that aggregates several services into the exact shape one client needs, so a mobile app makes one call instead of six and can evolve without coordinating with the web team. In Kubernetes discovery is DNS: a Service gets a stable name and virtual IP, kube-proxy or the CNI routes to healthy pods, and a mesh like Istio or Linkerd adds mTLS, retries and per-route telemetry in sidecars without changing application code.

**Deeper explanation:**

```text
Clients -> Gateway (TLS, auth, rate limit, routing)
            |-- /web/*    -> web-BFF    -> orders, users, search
            |-- /mobile/* -> mobile-BFF -> orders, users (compact payloads)
            |-- /api/v1/* -> public API service (API keys, quotas)
In-cluster: http://orders.prod.svc.cluster.local:8080  (Service DNS, no hardcoded IPs)
```

The gateway is where cross-cutting concerns stop being copy-pasted into every service. Doing JWT validation there means services receive trusted identity headers, but only if the network guarantees traffic came through the gateway; otherwise each service must verify again. Keep the gateway dumb about business logic; the moment it starts aggregating, it is an accidental BFF owned by nobody.

A BFF exists for client shape, not for reuse. Each BFF is allowed to be specific and even duplicate aggregation logic, because the alternative is one generic aggregation layer that every client team must negotiate changes to.

**Follow-ups they will ask:**
- How does a gateway handle streaming responses for an LLM endpoint? : it must not buffer; configure proxy buffering off and idle timeouts long enough for a slow token stream.
- What breaks when the gateway becomes a single point of failure? : everything, so it runs as multiple replicas behind a cloud load balancer and does nothing stateful.

**Mistakes to avoid:**
- Putting business aggregation in the gateway "because it is already there".
- Confusing a service mesh with a gateway; the mesh is east-west inside the cluster, the gateway is north-south at the edge.

### Q. A team wants to split their monolith into microservices. How do you decide whether to, what is a modular monolith, and how would you migrate safely with the strangler fig pattern?
**Short answer (45 seconds):** I ask what problem they are solving. Independent deployment and team autonomy, different scaling profiles, or isolation of a risky component are real reasons; "it is messy" is not, because a distributed mess is worse. First option is a modular monolith: one deployable with hard internal boundaries, each module owning its tables and exposing an interface, no cross-module database access, enforced by lint rules or package structure. That gives clean ownership without network calls, partial failures and distributed transactions. When a module clearly needs to be a service, use the strangler fig: route traffic through a facade, build the new service behind it, migrate one capability at a time, keep data flowing with an outbox or CDC, and retire the old code path once traffic is at zero.

**Deeper explanation:**

```text
Step 0: Clients -> Monolith
Step 1: Clients -> Facade/Gateway -> Monolith (no behaviour change, just a routing layer)
Step 2: Facade -> /notifications/* -> new Notification service
                -> everything else   -> Monolith (which now publishes events the new service consumes)
Step 3: repeat per capability; delete monolith code as each path reaches zero traffic
```

Pick the first candidate by low coupling and clear data ownership: notifications, search indexing, PDF generation, an LLM inference wrapper. Avoid starting with the core domain (orders, users) because everything joins to it. Data is the hard part: during migration the new service must not read the monolith's tables directly; it gets its data via events or a sync API, and the monolith stops writing that data once the cutover is done.

**Follow-ups they will ask:**
- How do you enforce module boundaries in a Node monolith? : separate packages in a monorepo with explicit public exports, ESLint import restrictions, separate Postgres schemas per module, and a rule that cross-module calls go through the module's service layer.
- What about the shared database? : it is the main coupling; splitting services that share tables gives you distributed deployment with none of the independence.
- How do you know the migration is done? : the facade shows zero traffic to the old path for a full business cycle, and the old tables are read-only, then dropped.

**Mistakes to avoid:**
- Proposing a big-bang rewrite; the strangler fig exists because big bangs fail on the data migration and the long freeze.

### Practice
- Write a client with timeout, retry with full jitter and a retry budget, point it at a stub server that returns 503 for 20 seconds, and plot attempt timing with and without jitter.
- Wrap a fake dependency in opossum, inject latency with a proxy or a sleep, and watch the breaker open, half-open and close while the fallback serves degraded data; graph the state transitions.
- Implement the outbox: an orders table, an outbox table, a relay using FOR UPDATE SKIP LOCKED publishing to Kafka or BullMQ, and a consumer with an inbox table; kill the relay mid-batch and prove nothing is lost and duplicates are ignored.
- Sketch an order saga as a state table with a due_at column and a worker; make the payment step time out and verify the compensation path runs exactly once.
- Say it out loud: give a two-minute answer to "should we move to microservices?" for a team of eight with a Node monolith, ending with a concrete first extraction and how you would route traffic to it.

## Python & FastAPI for AI Backends

> Most AI teams run inference, RAG and agent services in Python even when the product backend is Node. Interviewers probe whether you understand asyncio's rules (one blocking call freezes the loop), how FastAPI decides where a handler runs, how you validate and stream model output, and how you ship it: workers, the GIL, lockfiles. Weak answers say "FastAPI is fast". Strong answers say where the threads are.

### Concepts you must understand
- asyncio is single-threaded cooperative concurrency like Node, but nothing is async by default: a coroutine runs only when awaited or scheduled, and any sync library call (requests, psycopg2, time.sleep) blocks the whole loop.
- FastAPI runs async def handlers on the event loop and plain def handlers in a thread pool; a blocking call in an async handler stalls every request, the same call in a def handler just occupies a thread.
- Pydantic models are the contract for request bodies, responses, settings and LLM output; model_validate_json fails loudly with structured errors you can feed back to the model.
- Depends is a composable DI system: dependencies run per request, can yield for cleanup, are cached within a request, and can be overridden in tests without monkeypatching.
- BackgroundTasks run in the same process after the response and die with it; real jobs go to a queue (Celery, RQ, arq, Dramatiq) with persistence, retries and separate worker processes.
- One uvicorn worker is one process with one event loop and one GIL; scale CPU with more workers or pods, scale I/O concurrency within a worker with async code.
- Streaming LLM output is a StreamingResponse over an async generator in SSE format, with disconnect detection, no proxy buffering, and an error event instead of a silent cut.
- The GIL means threads do not run Python bytecode in parallel; I/O releases it, so threads help for blocking I/O, while CPU work needs processes, native code or a queue.
- pyproject.toml plus a lockfile (uv.lock or poetry.lock) and a multi-stage Docker build is what makes a Python service reproducible; type hints with mypy or pyright catch what tests miss.

### Q. You come from Node. How does asyncio's event loop differ, and what bites a Node developer writing FastAPI?
**Short answer (45 seconds):** The model is the same: one thread, an event loop, non-blocking I/O, callbacks scheduled when sockets are ready. The culture is different. In Node almost every library is non-blocking, so you cannot easily block the loop by accident. In Python the default libraries are synchronous, so a requests.get or a psycopg2 query inside an async def handler blocks every other request until it returns. You must use async drivers (httpx.AsyncClient, asyncpg or SQLAlchemy's async engine, motor, redis.asyncio) or push sync calls to a thread. Also, a coroutine does nothing until awaited or wrapped in a task, unlike a Promise which starts immediately.

**Deeper explanation:**

```python
import asyncio, httpx

async def fetch_all(urls: list[str]) -> list[str]:
    sem = asyncio.Semaphore(10)                      # bound concurrency, like p-limit
    async with httpx.AsyncClient(timeout=5.0) as client:
        async def one(u: str) -> str:
            async with sem:
                r = await client.get(u)
                r.raise_for_status()
                return r.text
        return await asyncio.gather(*(one(u) for u in urls))   # Promise.all
```

Things that surprise Node developers: calling an async function without await returns a coroutine object and runs nothing (Node would at least start the work). asyncio.gather is Promise.all, but if you need "fire and forget" you must keep a reference to the asyncio.create_task result or it can be garbage collected. There is no setImmediate; await asyncio.sleep(0) yields to the loop. Exceptions in tasks you never await are reported only when the task is collected. uvloop is a drop-in loop implementation built on libuv, the same library Node uses, and uvicorn can use it with --loop uvloop.

**Follow-ups they will ask:**
- How do you run a sync SDK call without blocking? : await asyncio.to_thread(fn, *args), or starlette's run_in_threadpool; the GIL is released during the I/O wait so the loop continues.
- What is the asyncio equivalent of an unhandled rejection? : a task exception that is never retrieved; the loop logs "Task exception was never retrieved" at garbage collection, so always await or add a done callback.
- Does async make CPU-bound code faster? : no, it only helps when the work is waiting on I/O; CPU work needs processes.

**Mistakes to avoid:**
- Using requests or time.sleep inside async def because "it worked in dev" where there was one request at a time.
- Claiming Python's async is slower than Node's by nature; the loop overhead is rarely the bottleneck compared to the model call.

### Q. In FastAPI, what is the difference between a def and an async def endpoint, and what happens when each makes a blocking call?
**Short answer (45 seconds):** An async def endpoint runs directly on the event loop, so it should only await non-blocking calls; a blocking call inside it freezes the whole worker for its duration. A plain def endpoint is run by Starlette in a thread pool via anyio, so a blocking database or SDK call there just occupies one thread while the loop keeps serving other requests. The rule: async def with async libraries, def with sync libraries, never mix a sync library into async def. The thread pool is bounded, so a service built only on def handlers has a hard concurrency ceiling, and CPU-bound work still contends on the GIL whichever you pick.

**Deeper explanation:**

```python
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

app = FastAPI()

@app.get("/a")                # runs in a worker thread: blocking is tolerated
def sync_handler():
    return legacy_sdk.fetch_report()           # sync HTTP call, 2 s

@app.get("/b")                # runs on the loop: blocking here stalls every request
async def async_handler():
    return await httpx_client.get(url)         # correct: non-blocking

@app.get("/c")
async def mixed_handler():
    data = await run_in_threadpool(legacy_sdk.fetch_report)   # sync call offloaded
    return await enrich(data)
```

The thread pool has a default capacity (anyio's limiter, 40 threads unless changed), so 41 concurrent def requests queue even if the loop is idle. For heavy sync traffic raise the limiter, or better, replace the sync library. CPU-bound code (parsing a 50 MB PDF, running a tokenizer over a corpus) belongs in a ProcessPoolExecutor via loop.run_in_executor or in a worker queue, because threads share the GIL and will slow the loop's own Python work too.

**Follow-ups they will ask:**
- Is def always safer then? : it is safer against accidental blocking but caps concurrency at the pool size and adds a thread hop per request; async def with correct drivers scales further.
- How do you find a blocking call in production? : run with PYTHONASYNCIODEBUG=1 or loop.slow_callback_duration in staging to log callbacks over 100 ms, and watch per-worker latency correlate across unrelated endpoints.
- How do you cap concurrency against the LLM provider? : an asyncio.Semaphore shared per worker, plus the provider's rate limit headers for backoff.

**Mistakes to avoid:**
- "async def is always faster": with a sync driver inside, it is dramatically slower under load.
- Forgetting that middleware and dependencies have the same constraint as handlers.

### Q. How do you use Pydantic in an AI backend, including validating structured output from an LLM?
**Short answer (45 seconds):** Pydantic models are the typed boundary for everything entering or leaving the service: request bodies, response models that filter fields, settings loaded from the environment with pydantic-settings, and the JSON a model returns when I ask for structured output. For LLM output I define the schema as a model, pass its JSON schema (model_json_schema) to the provider's structured output or tool-call mechanism, then model_validate_json the result. On ValidationError I send the error list back to the model for one repair attempt, then fail the request rather than guess. Pydantic v2 runs its core in Rust, so validation cost is negligible compared to the model call.

**Deeper explanation:**

```python
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

class TicketTriage(BaseModel):
    category: Literal["billing", "bug", "feature_request"]
    priority: int = Field(ge=1, le=5)
    summary: str = Field(max_length=200)
    needs_human: bool

async def triage(text: str) -> TicketTriage:
    raw = await llm_json(text, schema=TicketTriage.model_json_schema())
    try:
        return TicketTriage.model_validate_json(raw)
    except ValidationError as e:
        repaired = await llm_json(text, schema=TicketTriage.model_json_schema(),
                                  errors=e.errors(include_url=False))
        return TicketTriage.model_validate_json(repaired)   # raises again if still bad
```

Literal and constrained fields do real work here: the model cannot return "urgent" as a priority or invent a category, and downstream code can trust the types. Use response_model on routes so internal fields (embedding vectors, provider request ids) never leak, and model_dump(exclude_none=True) when building provider payloads.

Settings belong in a BaseSettings class so a missing API key fails at startup, not on the first request. For validation beyond types, field_validator and model_validator express rules like "if needs_human then summary must be non-empty".

**Follow-ups they will ask:**
- Pydantic model, dataclass or TypedDict? : Pydantic when data crosses a trust boundary and needs validation; dataclasses for internal plain data; TypedDict for typing dicts you do not construct yourself.
- What about the provider's native structured output? : it constrains generation to the schema, which removes most failures, but still validate: schemas can be loosely enforced and your business rules are not in the JSON schema.
- Why not parse with json.loads and check keys by hand? : you lose coercion rules, nested validation, clear error messages and the OpenAPI schema for free.

**Mistakes to avoid:**
- Retrying LLM validation failures in an unbounded loop; cap at one or two attempts and record the failure.
- Returning ORM objects or raw dicts without a response model, which leaks fields the moment someone adds a column.

### Q. Explain FastAPI's dependency injection. How do you use Depends for database sessions, authentication and testing?
**Short answer (45 seconds):** Depends declares what a handler needs and FastAPI resolves it per request, building a graph: the handler depends on current_user, which depends on get_db and a header. A dependency that yields runs its setup before the handler and its teardown after the response, which is how a database session or a transaction is scoped to the request. The same dependency used twice in one request is evaluated once. For tests, app.dependency_overrides replaces a dependency with a fake, so you test handlers against an in-memory user or a test database without patching modules.

**Deeper explanation:**

```python
from collections.abc import AsyncIterator
from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:        # setup
        yield session                             # handler runs here
                                                  # teardown: session closed after response

async def current_user(authorization: str = Header(), db: AsyncSession = Depends(get_db)) -> User:
    user = await verify_bearer(authorization, db)
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/me")
async def me(user: User = Depends(current_user)):
    return user

# tests
app.dependency_overrides[current_user] = lambda: User(id="u1", role="admin")
```

Dependencies compose authorization cleanly: a require_role("admin") factory returns a dependency that depends on current_user and raises 403, and routers can take dependencies=[Depends(...)] so a whole router is protected without repeating it per handler. For AI services, dependencies are also where shared clients live: an LLM client created once at startup (lifespan) and injected per request, so handlers never build their own connections.

A yield dependency can wrap a transaction: begin before yield, commit after the handler returns, roll back if the handler raises. Keep yield dependencies free of heavy work after the yield, because that runs after the response and delays worker availability.

**Follow-ups they will ask:**
- What is the lifespan context manager for? : startup and shutdown of process-wide resources (connection pools, model clients, warmups) with app = FastAPI(lifespan=lifespan).
- Can a dependency be cached across requests? : not by Depends itself; use a module-level singleton or lru_cache on a factory for expensive clients.
- How does this compare to NestJS providers? : Nest's DI is class-based with scopes and modules; FastAPI's is function-based and per request, lighter but less structured.

**Mistakes to avoid:**
- Opening a new engine or client inside a dependency on every request; pools belong in lifespan.
- Testing with monkeypatch when dependency_overrides exists; overrides are explicit and scoped.

### Q. A request needs to embed a 500-page document, which takes two minutes. BackgroundTasks, Celery, RQ or arq, and how does the client get the result?
**Short answer (45 seconds):** Not BackgroundTasks: they run in the API process after the response, they are lost if the pod restarts or deploys, there are no retries, and they compete with request handling. For a two-minute job I return 202 with a job id and enqueue work to a separate worker fleet. In an async codebase that mostly waits on embedding API calls I pick arq (asyncio-native, Redis-backed, with job ids for deduplication); for CPU-heavy or mixed workloads Celery with Redis or RabbitMQ is the mature choice; RQ is the simple sync option. The client polls GET /jobs/{id} or subscribes to progress over SSE; the job record in Redis or Postgres holds status, progress and the result location.

**Deeper explanation:**

```python
from arq import create_pool
from arq.connections import RedisSettings

async def embed_document(ctx, doc_id: str) -> None:
    chunks = await load_chunks(doc_id)
    for i, batch in enumerate(batched(chunks, 64)):
        vectors = await embed(batch)                       # async call to the embeddings API
        await store_vectors(doc_id, vectors)
        await set_progress(doc_id, (i + 1) * 64 / len(chunks))

class WorkerSettings:
    functions = [embed_document]
    redis_settings = RedisSettings(host="redis")
    max_jobs = 10
    job_timeout = 600

@app.post("/documents/{doc_id}/embed", status_code=202)
async def start_embed(doc_id: str, redis=Depends(get_arq)):
    job = await redis.enqueue_job("embed_document", doc_id, _job_id=f"embed:{doc_id}")
    return {"job_id": f"embed:{doc_id}", "status": "queued" if job else "already_running"}
```

Using the document id as the job id makes the endpoint idempotent: a double click does not embed twice. The job itself should be resumable: store progress per batch so a retry after a worker crash skips completed batches rather than re-paying for embeddings. Set a job timeout, a retry count with backoff, and a dead-letter path for jobs that keep failing. Workers scale independently of the API and can run on different hardware.

**Follow-ups they will ask:**
- How does the client get notified without polling? : SSE or WebSocket from the API that subscribes to a Redis pub/sub channel per job, or a webhook for server-to-server callers.
- Celery versus arq in one line? : Celery is batteries-included and sync-first with prefork workers; arq is small and async-first, right when the work is awaiting network calls.
- How do you cancel a job? : set a cancel flag in the job record that the worker checks between batches; you cannot safely kill a coroutine mid-await from outside.

**Mistakes to avoid:**
- Holding the HTTP request open for two minutes; proxies and clients time out and a retry starts a duplicate job.
- Running the worker inside the API container "to save a deployment"; a deploy of the API then kills in-flight jobs.

### Q. How do you deploy a FastAPI service: uvicorn versus gunicorn, how many workers, and what does the GIL mean for your choices?
**Short answer (45 seconds):** uvicorn is the ASGI server; each worker is a process with its own event loop and its own GIL. For a single container I run several uvicorn workers, either with uvicorn's own --workers flag or with gunicorn as the process manager using the UvicornWorker class, which gives mature restart and graceful reload behaviour. Because handlers are async, one worker per core is the usual starting point; the GIL means a worker never uses more than one core for Python code, so CPU parallelism comes only from more processes. In Kubernetes many teams run one or two workers per pod and let the horizontal autoscaler add pods, which keeps memory per pod predictable.

**Deeper explanation:**

```bash
# option 1: uvicorn manages its own worker processes
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --loop uvloop --timeout-graceful-shutdown 30
# option 2: gunicorn as process manager, uvicorn as the worker class
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 \
  --timeout 120 --graceful-timeout 30
```

Memory is the sizing constraint people forget: each worker imports the whole app, so a service that loads a tokenizer or a local embedding model multiplies that footprint by the worker count. Load models once per process at startup via lifespan, or move them to a dedicated inference service and keep the API workers thin.

GIL implications in practice: threads are fine for blocking I/O (the GIL is released while waiting), useless for CPU parallelism, and a CPU-heavy request in one worker degrades every other request in that worker. Python 3.13 ships an experimental free-threaded build, but most libraries are not yet verified against it, so plan on processes. Gunicorn's --timeout kills a worker whose request exceeds the limit; for long streaming responses raise it or rely on uvicorn's own handling.

**Follow-ups they will ask:**
- What does the 2 times cores plus 1 rule mean here? : that is gunicorn's heuristic for sync workers that block per request; async workers need fewer because one handles many concurrent requests.
- How do you do zero-downtime deploys? : rolling updates with readiness probes and a graceful timeout longer than your slowest request; gunicorn also supports a HUP reload for single-host setups.

**Mistakes to avoid:**
- Running --workers 16 on a 2-core pod; you get memory pressure and GIL-independent context switching with no throughput gain.

### Q. How do you stream LLM output to a browser from FastAPI with server-sent events, and how do you handle disconnects and upstream errors?
**Short answer (45 seconds):** I return a StreamingResponse with media type text/event-stream wrapping an async generator that iterates the provider SDK's stream and yields data: lines in SSE framing. Inside the loop I check request.is_disconnected() so a closed tab stops the upstream call and stops the token bill. Errors are sent as a named error event, then the stream ends, so the client distinguishes "model failed" from "network dropped". Headers disable caching and proxy buffering (X-Accel-Buffering: no for nginx), and the gateway timeout must exceed the longest response. Because browsers' EventSource only supports GET, a POST chat endpoint is consumed with fetch and a ReadableStream reader.

**Deeper explanation:**

```python
import json
from fastapi import Request
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request):
    async def events():
        try:
            async with llm.messages.stream(model=MODEL, max_tokens=1024,
                                           messages=body.messages) as stream:
                async for text in stream.text_stream:
                    if await request.is_disconnected():
                        return                                   # closes upstream via the context manager
                    yield f"data: {json.dumps({'delta': text})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception:
            log.exception("stream failed")
            yield f"event: error\ndata: {json.dumps({'message': 'generation failed'})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

Persist as you stream: append deltas to a buffer and write the final assistant message (plus token usage) to the database in a finally block, so a disconnect mid-stream still leaves a consistent conversation record marked partial. Send a comment line (a line starting with a colon) every 15 seconds or so during long tool calls so proxies do not drop the idle connection. If you emit tool-call events, give each SSE event a type (event: tool_call) and a JSON payload so the client renders them differently from text.

**Follow-ups they will ask:**
- SSE or WebSocket for chat? : SSE for server to client streaming over plain HTTP with trivial infrastructure; WebSocket when the client also streams (voice) or needs many messages both ways on one connection.
- How do you resume a stream after a network drop? : assign ids to events and support Last-Event-ID, or simpler, persist the partial message and let the client fetch it and continue.
- What does the gateway need? : no response buffering, idle timeout above your longest generation, and HTTP/1.1 chunked or HTTP/2 passthrough.

**Mistakes to avoid:**
- Collecting the full response and sending it at the end "to simplify"; the user waits 20 seconds staring at nothing.
- Ignoring disconnects; the model keeps generating and you pay for tokens nobody reads.

### Q. What makes a Python AI service production-grade in terms of typing, mypy and packaging with uv or poetry?
**Short answer (45 seconds):** Type hints everywhere, checked in CI with mypy or pyright in a strict mode, because they are also what FastAPI and Pydantic use to validate and document the API. Dependencies declared in pyproject.toml with a committed lockfile (uv.lock or poetry.lock) so every build and every developer resolves the identical set; uv is the current fast choice for resolving, installing and running, poetry is the established alternative with the same lockfile idea. A multi-stage Docker build installs from the lockfile before copying the source so layers cache, runs as a non-root user, and pins the base image. Add ruff for lint and format, pytest with httpx's AsyncClient for API tests, and structured JSON logging with request ids.

**Deeper explanation:**

```dockerfile
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.4.0 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project      # deps layer, cached until the lock changes
COPY . .
RUN uv sync --frozen --no-dev
RUN useradd -m app && chown -R app /app
USER app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Pin the uv image tag to whatever version you have tested rather than latest. --frozen fails the build if the lockfile is out of date with pyproject.toml, which is exactly what you want in CI. Separate dependency groups (dev, test) keep the runtime image small and the attack surface lower.

Typing for AI code specifically: Protocol classes for "anything with an async generate method" so you can swap providers in tests, TypedDict or Pydantic models for tool-call arguments, Literal for model names and roles, and a mypy plugin for Pydantic. Treat mypy errors as build failures or the type coverage decays within weeks.

**Follow-ups they will ask:**
- uv or poetry? : both give pyproject plus a lockfile; uv is much faster and also manages Python versions and tools, poetry has a longer track record; the important thing is the lockfile and one chosen tool per repo.
- How do you test async endpoints? : pytest with an async test runner (anyio or pytest-asyncio) and httpx.AsyncClient against the ASGI app, overriding dependencies for the database and the LLM client.

**Mistakes to avoid:**
- Installing with pip install -r requirements.txt from a file without pins; two builds a week apart differ.
- Typing only the public signatures and leaving Any inside; the first refactor breaks silently.

### Practice
- Write one FastAPI app with three endpoints: a sync requests.get inside async def, the same inside def, and httpx inside async def; load test each with 50 concurrent connections and compare p99 and throughput.
- Build the SSE chat endpoint above against a real provider, open it from a browser with fetch and a reader, close the tab mid-stream and confirm from logs that the upstream call stopped.
- Set up arq or Celery with a two-minute fake job that reports progress to Redis, expose 202 plus a polling endpoint, kill the worker mid-job and verify the retry resumes from the last batch.
- Convert a service to pyproject.toml with uv, commit the lockfile, build the multi-stage image, and confirm a change to the source does not re-install dependencies.
- Say it out loud: explain in ninety seconds why a blocking SDK call in an async FastAPI handler takes the service down under load, and the two ways you would fix it.

## Backend System Design Walkthroughs

> A system design round is not a quiz about components, it is a test of whether you can drive an ambiguous problem to a defensible design in 45 minutes while thinking out loud. Weak candidates draw boxes immediately. Strong candidates pin down requirements and numbers first, write the API and data model, draw the simplest design that meets the numbers, then go deep where the interviewer points, naming trade-offs at every step.

### Concepts you must understand
- Minutes 0 to 5 are requirements: functional (what it does), non-functional (latency, availability, consistency, durability), scale (users, QPS, data size), and what is explicitly out of scope; state assumptions aloud and write them down.
- Minutes 5 to 10 are estimates: daily volume divided by roughly 10^5 seconds gives QPS, peak is 2 to 5 times average, row size times rows gives storage; the point is to find which number dominates the design, not precision.
- Minutes 10 to 15 are the API and data model: endpoints with request and response shapes, the main tables or collections with keys and indexes, and where idempotency keys and pagination cursors live.
- Minutes 15 to 25 are the high-level design: clients, gateway, stateless services, databases, cache, queue, workers, drawn with the main request path traced end to end; start simple and justify every box.
- Minutes 25 to 40 are deep dives chosen by the interviewer: the hot path, the hard consistency problem, the failure modes, scaling the bottleneck; have two prepared for every design.
- The last 5 minutes are trade-offs and operations: what you chose not to do, what breaks first at 10x, how you would monitor it and roll it out.
- Every design reuses the same toolbox: cache for read-heavy, queue for bursty or slow work, idempotency for retries, partitioning by the natural key, async fan-out, and explicit consistency choices per data item.
- Read versus write ratio, fan-out factor and payload size decide the architecture more than anything else; say which one dominates and design for it.
- Always close the loop on failure: what happens when the cache, the queue, the provider or a region is down, and what the user sees.

### Q. How do you structure a 45-minute system design interview so you cover everything the interviewer is scoring?
**Short answer (45 seconds):** I run a fixed agenda and say it out loud: clarify requirements and scale, do quick estimates to find the dominant constraint, define the API and data model, draw the high-level design tracing one request end to end, then spend most of the remaining time on deep dives the interviewer cares about, and close with trade-offs, failure modes and what I would change at ten times the load. The agenda keeps me from drawing a Kafka cluster for a problem with 50 writes per second, and it makes sure the interviewer gets to steer.

**Deeper explanation:**

```text
0-5    Requirements: functional, non-functional (p99, availability, consistency), scale, out of scope
5-10   Estimates: QPS (daily / 1e5), peak factor, storage (rows x size x retention), bandwidth
10-15  API + data model: endpoints, request/response, tables, keys, indexes, idempotency, pagination
15-25  High-level design: trace the hot path through every box; justify each component
25-40  Deep dives: the bottleneck, the hard consistency case, failure handling, scaling the hot spot
40-45  Trade-offs, monitoring, rollout, what breaks at 10x
```

The estimates step is where seniority shows. One million writes a day is about 12 per second, which one Postgres primary handles trivially; the design then should not include sharding. A chat system with 50 million daily messages and a fan-out of 10 is 500 million deliveries, which is a fan-out problem, not a storage problem. Say the number, say what it implies, move on.

For the data model, name primary keys and the two or three indexes that serve the hot queries, and say which operations need transactions. For the high-level design, start with a load balancer, stateless API servers, one database and a cache, then add a queue and workers only when a step is slow, bursty or needs retries. Each addition should be an answer to a stated problem.

**Follow-ups they will ask:**
- What if the interviewer keeps interrupting? : follow them; the agenda is a default, their questions are the scoring rubric.
- How much detail in the API? : enough to show idempotency, pagination and auth in the shapes; not every field.
- What if you do not know a number? : state a reasonable assumption, label it, and design so it is not load-bearing.

**Mistakes to avoid:**
- Jumping to the diagram before asking about consistency and scale; you cannot justify any box without them.
- Spending 20 minutes on estimates; they exist to find the dominant constraint, nothing more.

### Q. Design a URL shortener handling 100 million new links a month with a heavy read load.
**Short answer (45 seconds):** 100 million a month is about 40 writes per second and, at a 100 to 1 read ratio, around 4,000 redirects per second with spiky peaks. Writes go to Postgres: a links table keyed by a 7-character base62 code with the long URL, owner, expiry and created_at. Codes come from a database sequence or a Snowflake-style id encoded in base62, so no collision checks are needed. Redirects are served from Redis (code to URL) with a Postgres fallback, returning 302 so clicks are counted, and click events are published asynchronously to a queue for analytics. 62 to the power of 7 is about 3.5 trillion codes, so the keyspace lasts for decades.

**Deeper explanation:**

```sql
CREATE TABLE links (
  code        VARCHAR(10) PRIMARY KEY,         -- base62 of an id, or a custom alias
  long_url    TEXT NOT NULL,
  owner_id    UUID,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at  TIMESTAMPTZ
);
-- API: POST /links {long_url, custom_alias?, expires_at?} -> 201 {code, short_url}
--      GET /:code -> 302 Location: long_url   (404 or 410 if missing or expired)
```

Redirect path: check Redis GET code; on miss read Postgres, SET with a TTL, respond. Cache negative results briefly so a flood of random codes does not hit the database. The hot set is small (recent and viral links), so a modest Redis fits it. At 4,000 reads per second a single Postgres replica would also cope, but the cache keeps p99 flat under viral spikes.

Analytics: the redirect handler emits an event (code, timestamp, country, user agent) to Kafka or a lightweight queue and returns immediately; a consumer aggregates into a clicks table or a warehouse. Never write analytics synchronously on the redirect path. Abuse: rate limit creation per user and IP, check destinations against a malware blocklist, and support disabling a code, which is why 302 beats a permanently cached 301.

**Follow-ups they will ask:**
- 301 or 302? : 301 is cached by browsers so later clicks never reach you and cannot be disabled; 302 or 307 keeps control and counting at the cost of one extra request per click.
- How do you delete expired links? : a daily job deletes by expires_at with an index on it, and the cache TTL is bounded by expires_at.

**Mistakes to avoid:**
- Hashing the URL with MD5 and truncating; collisions need handling and the same URL from two users gets one code with one owner.

### Q. Design a distributed rate limiter used by all our public API services.
**Short answer (45 seconds):** The limiter sits at the gateway or as the first middleware in each service, keyed by API key or user id, with rules per plan such as 1,000 requests per minute and a burst allowance. State lives in Redis so all instances share one view; each check is one atomic Lua script implementing a token bucket or sliding window, returning allow or deny and the remaining count, which goes into response headers along with Retry-After on 429. Redis is sharded by key for throughput, limiter clients cache rules locally, and the failure policy is explicit: fail open with an alert for most APIs, fail closed for login and expensive endpoints.

**Deeper explanation:**

```text
Request -> Gateway middleware
             |- rule lookup: plan -> {capacity, refill/s}  (local cache, refreshed from config store)
             |- EVALSHA token_bucket  key=rl:{api_key}:{route_group}  -> allowed, remaining, reset_ms
             |- allowed: forward, add X-RateLimit-Limit / Remaining / Reset
             |- denied: 429 + Retry-After, count metric per key
```

Token bucket is the usual choice because it allows short bursts without allowing a sustained overrun; sliding window log is exact but costs a sorted set entry per request, which at thousands of requests per second per key is wasteful.

Scaling: Redis Cluster shards by key hash, so one tenant's limiter lives on one node and a single abusive key can hot-spot that node; mitigate by giving each gateway instance a local token bucket holding a fraction of the global limit for very high-traffic keys, accepting slight imprecision in exchange for removing the round trip. Multi-region: either a Redis per region with per-region limits (simple, allows N times the limit globally) or a global limit with asynchronous reconciliation; say which you choose and why.

**Follow-ups they will ask:**
- Token bucket versus sliding window counter? : bucket for burst-tolerant APIs with smooth refill; sliding window counter when you promise an exact "N per minute" number to customers.
- How do you limit by cost rather than count? : charge tokens per request weight (an LLM call costs 20, a GET costs 1) and debit the actual cost after the response where it is only known then.

**Mistakes to avoid:**
- Per-instance in-memory counters behind a load balancer; the effective limit scales with your replica count.

### Q. Design a notification service that sends push, email, SMS and in-app messages for all our products.
**Short answer (45 seconds):** The service exposes one API: POST /notifications with recipient, template, data, channels or a preference lookup, priority and an idempotency key. The API validates, resolves user preferences and quiet hours, persists a notification record, and publishes one message per channel to a queue. Channel workers render templates and call providers (FCM and APNs, an email provider, an SMS provider) with retries, exponential backoff and a dead-letter queue, then record delivery status, including provider webhooks for bounces and delivery receipts. In-app notifications are written to an inbox table and pushed over WebSocket or SSE to connected clients. Priority queues keep OTPs ahead of marketing digests, and per-user rate limits stop any product from spamming.

**Deeper explanation:**

```text
Producers -> POST /notifications (idempotency key)
          -> notifications table (status=queued) + outbox
          -> Kafka topics or BullMQ queues per channel and priority:
               push.high  push.low  email.high  email.low  sms.high  inapp
          -> workers: render template, check preferences again, call provider, record attempt
          -> provider webhooks -> delivery_events table -> status updates
          -> DLQ after N attempts, alert on DLQ growth
```

Idempotency is central because producers retry: the key is stored with the notification record, so a duplicate request returns the existing id and nothing sends twice. Preferences and unsubscribe must be checked at send time, not only at enqueue time, since a user may opt out while a digest is queued. Provider failover (two email providers, routing by health) is a real requirement for critical channels, and per-provider rate limits must be respected by the workers.

Scheduling and batching: a scheduled_at column with a scheduler that moves due rows onto the queue, and a digest mode that collapses many low-priority events into one message. Storage is append-heavy: a notifications table partitioned by month and a delivery_events table; archive old partitions. Observability is the product here: per-channel delivery rate, provider latency, bounce rate and DLQ depth are the dashboards the on-call lives by.

**Follow-ups they will ask:**
- How do you guarantee an OTP is not delayed by a marketing campaign? : separate queues and worker pools per priority, so bulk traffic cannot occupy the high-priority workers.
- How do you handle a provider outage? : circuit breaker per provider, failover to the secondary for critical channels, and let the queue absorb the backlog for the rest.

**Mistakes to avoid:**
- Calling providers synchronously inside the API request; provider latency and failures become your API's.

### Q. Design a chat system supporting one-to-one and group messaging with delivery receipts and offline users.
**Short answer (45 seconds):** Clients hold a WebSocket to a stateless chat gateway; a connection registry in Redis maps user id to the gateway node holding its socket. A sent message goes to the chat service, which assigns a monotonically increasing id per conversation, persists it, then fans out through pub/sub to the recipients' gateways, which push it down their sockets; offline recipients get a push notification via the notification service. Storage is partitioned by conversation id, which keeps "load the last 50 messages" a single-partition range read. Receipts (delivered, read) are small events flowing the same way. On reconnect a client sends its last seen message id per conversation and gets everything after it, which also makes delivery at-least-once with client-side deduplication by message id.

**Deeper explanation:**

```text
Sender -> WS Gateway A -> Chat service: id = next_seq(conversation), persist (conv_id, id, sender, body, ts)
                       -> publish conv:{id} -> Redis pub/sub or Kafka
                       -> Gateway B (recipient online) pushes; else -> notification service (push)
Receipts: recipient -> gateway -> chat service -> stored per (conv_id, user_id, last_read_id) -> fan-out
Reconnect: client sends {conv_id: last_seen_id} -> server returns messages WHERE id > last_seen_id
```

Ordering: a per-conversation sequence (a counter in Redis with persistence, or the database assigning the next id under a row lock on the conversation) gives a total order per conversation, which is what users expect; global ordering is unnecessary. For storage at scale, a wide-column store such as Cassandra or ScyllaDB with partition key conversation id and clustering by message id fits perfectly; Postgres partitioned by conversation hash works well below that scale.

Group fan-out: for groups up to a few hundred, fan out on write to each online member; for very large groups, store once per conversation and let clients pull, because writing a copy per member explodes. Presence is a heartbeat updating a Redis key with a short TTL; expiry means offline.

**Follow-ups they will ask:**
- How do you avoid duplicate messages when the sender retries? : a client-generated message id stored with a unique constraint per conversation; the retry returns the existing server id.
- How do you handle a gateway node dying? : clients reconnect to another node, re-register, and sync from last seen id; nothing is lost because persistence happened before fan-out.

**Mistakes to avoid:**
- Fanning out before persisting; a crash between them loses messages that some recipients saw.

### Q. Design a file upload service for user documents up to several gigabytes using presigned URLs.
**Short answer (45 seconds):** The bytes never pass through my API. The client calls POST /uploads with filename, size and content type; the service authorizes, creates a file record in pending state with a server-generated object key, and returns a presigned PUT URL (or multipart upload URLs for large files) valid for a few minutes. The client uploads directly to S3 or GCS, then the service learns of completion either from the client's POST /uploads/{id}/complete or from a bucket event notification, verifies the object with a HEAD request (size, checksum), runs post-processing such as virus scanning and thumbnailing through a queue, and marks the file ready. Downloads are presigned GET URLs or CDN signed URLs, never public objects.

**Deeper explanation:**

```text
POST /uploads {name, size, type}  -> files(id, owner, key=tenant/uuid, status=pending, size, type)
                                   -> presigned PUT (expires 15 min) or
                                      multipart: CreateMultipartUpload + presigned UploadPart URLs per 10-100 MB part
Client PUTs parts directly to the bucket; CompleteMultipartUpload via POST /uploads/{id}/complete
Bucket event (ObjectCreated) -> queue -> worker: HEAD object, verify size/etag, scan, thumbnail -> status=ready
Lifecycle rule: abort incomplete multipart uploads and delete pending objects after 24h
GET /files/{id} -> authorize -> presigned GET (short expiry) or CDN signed URL
```

Server-generated keys matter: user filenames are stored as metadata, never as object keys, which prevents path tricks and collisions and keeps tenants separated by prefix. The presigned URL is scoped to one key and method and expires, so even if it leaks it is a short-lived write to one path. Validate size and type after upload with HEAD rather than trusting the client's claim; presigned POST policies can also constrain content length. Multipart gives resumability: a failed part is retried alone, and the client can pause and resume with the same upload id.

Bucket events are more reliable than the client's completion call (the client can crash after the PUT), so treat the client call as a hint and the event as the source of truth, and make the completion handler idempotent.

**Follow-ups they will ask:**
- Why not proxy uploads through the API for simplicity? : every byte would consume your pods' bandwidth and memory, and a 5 GB upload would hold a connection for minutes; the bucket is built for this.
- How do you prevent an attacker from filling your storage? : per-user quotas checked at POST /uploads, size limits, short URL expiry, and lifecycle rules for abandoned uploads.

**Mistakes to avoid:**
- Marking the file ready when the presigned URL is issued; nothing has been uploaded yet.

### Q. Design the backend for an LLM chat product with streaming responses, tool calls and persistent conversations.
**Short answer (45 seconds):** Stateless API nodes expose conversations and messages; sending a message opens an SSE stream. The handler loads the conversation, builds the prompt within the model's context budget, calls the provider with streaming and tool definitions, and runs an agent loop: when the model emits a tool call, validate the arguments against the tool's schema, execute with a timeout, append the result, call the model again, until it finishes or hits an iteration cap. Every step is persisted as it happens, including tool calls, tool results, token usage and partial text, so a crash mid-turn leaves a consistent record and a reconnecting client can recover. Redis holds a per-conversation lock so only one generation runs at a time, and per-user limits on requests and tokens protect cost.

**Deeper explanation:**

```sql
CREATE TABLE conversations (id UUID PRIMARY KEY, user_id UUID NOT NULL, title TEXT,
  model TEXT NOT NULL, system_prompt_id UUID, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE messages (
  id UUID PRIMARY KEY, conversation_id UUID NOT NULL REFERENCES conversations(id),
  seq INT NOT NULL,                       -- order within the conversation
  role TEXT NOT NULL,                     -- user | assistant | tool
  parts JSONB NOT NULL,                   -- [{type:'text'},{type:'tool_call',name,args,id},{type:'tool_result',...}]
  status TEXT NOT NULL,                   -- streaming | complete | interrupted | failed
  input_tokens INT, output_tokens INT, created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (conversation_id, seq));
-- POST /conversations/{id}/messages {content, idempotency_key} -> SSE: text deltas, tool_call, tool_result, done, error
```

The agent loop deserves its own deep dive: tools are an allowlist with JSON schemas, arguments are validated before execution, side-effecting tools require idempotency keys and sometimes an explicit user confirmation step (the loop pauses, persists a pending tool call, and resumes on approval), and the iteration cap plus a wall-clock budget prevents runaway loops.

Context management: keep the system prompt stable for prompt caching, include recent turns verbatim, and summarize older turns into a stored summary message when the token count approaches the budget.

Reliability: a circuit breaker and fallback model per provider, retries only on connection errors before any token was streamed.

**Follow-ups they will ask:**
- How do you stop a double-submit from generating twice? : the idempotency key on the message plus the per-conversation lock; the second request attaches to the existing stream or returns the stored result.
- What is the hard multi-tenant issue? : tools that access customer data must run with the user's permissions, not a service account, and every retrieval must be scoped by tenant.

**Mistakes to avoid:**
- Storing only the final assistant text; without tool calls and results you cannot debug, audit or resume a turn.
- Letting the model's tool arguments reach a database or shell without schema validation and an allowlist.

### Practice
- Pick the URL shortener and run the full 45-minute agenda alone with a timer, writing the estimates, API, schema and diagram by hand; then critique where you spent too long.
- Implement the token-bucket limiter as an Express or FastAPI middleware backed by Redis, add the standard rate limit headers, and load test it from two instances to confirm the shared limit holds.
- Build the presigned upload flow end to end against a local MinIO or a real bucket: pending record, presigned PUT, bucket event or completion call, HEAD verification, ready status, and a lifecycle rule for abandoned uploads.
- Build the LLM chat agent loop with one tool, persist every step as a message row, kill the process mid-turn and confirm the conversation record is consistent and the client can resume.
- Say it out loud: in three minutes, present the chat system design to a peer, leading with the ordering and reconnect-sync problems before they ask.
