## Node.js Runtime Architecture

### Why it exists
Before Node.js, most web servers gave each connection its own thread or process, so thousands of slow or idle clients meant thousands of stacks in memory and a lot of time spent switching between them. Node.js put Google's V8 JavaScript engine on top of libuv, a C library that asks the operating system which sockets are ready, so one thread can serve many waiting connections and only runs code when something actually happens. It also let teams use one language in the browser and on the server. The trade-off is that all your JavaScript shares that one thread: a slow synchronous step, such as a huge JSON.parse or a CPU-heavy loop, makes every request wait, so CPU work has to move to worker threads or other processes.

## Express.js Request Pipeline

### Why it exists
Node's built-in http module hands you a raw request and response and nothing else, so without a framework every handler parses URLs, reads bodies, checks auth and formats errors on its own. Express added routing and an ordered chain of middleware functions, so shared work such as body parsing, logging, authentication and error handling is written once and runs in a predictable order. Its small core is why it became the default way to write Node APIs and why so many libraries plug into it. The cost is that it gives no structure beyond that chain: folder layout, wiring and error conventions are left to each team, ordering mistakes become real bugs, and Express 4 does not catch errors from async handlers on its own.

## NestJS Architecture

### Why it exists
Large Express codebases tend to drift: each team invents its own folder layout, creates dependencies by hand with `new`, and puts auth or validation in slightly different places, which makes the code hard to test and hard to change safely. NestJS adds that structure on top of Express or Fastify: modules that decide what is visible where, a dependency injection container that builds services and hands them out, and a fixed request pipeline of guards, interceptors, pipes and exception filters. Large teams get one obvious place for each concern, and swapping a real dependency for a fake in a test becomes a one-line change. The price is more ceremony, slower startup, decorators that hide how things are wired, and boot-time errors such as unresolved dependencies or circular imports that confuse anyone who does not know how the container works.

## FastAPI & Python Async Architecture

### Why it exists
Classic Python web frameworks follow WSGI, where each request is one blocking function call, so serving many slow requests at once needs many threads or processes; that fits poorly with streaming, WebSockets and thousands of requests waiting on LLM APIs. ASGI and asyncio let one Python process keep many requests open on a single event loop, and FastAPI builds on them with type hints that drive validation, dependency injection and OpenAPI docs, replacing hand-written parsing and checking. It became the common choice for AI backends because it sits right next to Python's machine learning libraries. The trade-off is that much of the Python ecosystem is still synchronous, so one blocking call inside an `async def` endpoint freezes the whole worker, and the GIL means CPU-heavy work still needs separate processes.

## Node.js vs FastAPI, Side by Side

### Why it exists
AI products usually need two kinds of work: waiting on networks (LLM APIs, databases, streams to the browser) and heavy computation (parsing, embeddings, evaluation), and someone has to decide which runtime does which. Both runtimes look the same from far away, one event loop per process plus helper threads, but they fail in different places, so choosing by habit ("Python is for AI", "Node is faster") ends in frozen workers or an awkward rewrite. Comparing them side by side turns the choice into a mapping of loop, thread pool, CPU parallelism and ecosystem onto the actual workload. Running both is often the right answer, at the cost of two languages, an extra network hop and an API contract that must be kept in sync.

## LLM Transformer Architecture

### Why it exists
Before transformers, language models were mostly recurrent networks (RNNs and LSTMs) that read text one word at a time, so training could not be spread across a whole sequence at once and information from far back tended to fade. The transformer replaced that with attention, where every position looks directly at every earlier position, and whole sequences train in parallel on GPUs, which is what made today's very large models practical. Knowing the blocks explains the bill you pay when serving: attention work in prefill grows with the square of the prompt length, the KV cache grows with every token kept in context, and generation still produces one token at a time. Those three facts drive latency, GPU memory and cost per request.

## Jev: Decision-Layer Model Architecture

### Why it exists
When an agent lets a generative LLM decide which tool to call, the decision comes back as free text or JSON that can be off-list or inconsistent, usually without a probability you can put a threshold on, so risky actions have no clear stopping point. Before decision models, teams used keyword rules, embedding routers or fine-tuned classifiers, which are fast but either miss context or need labelled data and a retrain whenever the options change. A decision-layer model such as Jev answers questions you define about the current state, picks only from options you supply and returns probabilities, so ordinary code can apply thresholds, send uncertain cases to review and log every decision. The cost is another vendor dependency and network call, probabilities you must check on your own data, and answers that can still be confidently wrong inside the allowed set.

## Runtime Project Scenarios [Scenarios]

> Project and design scenarios in this track test whether you can turn runtime internals into decisions: which process does which work, where blocking work goes, how a request pipeline is layered, and how much GPU memory a context length costs. Interviewers give a goal plus one or two constraints (a deadline, a team, a latency target, a budget) and then add twists. A weak answer lists technologies. A strong answer asks two or three clarifying questions, estimates with simple arithmetic, picks a design, names the trade-off and the risk it accepts, and says what it will measure in the first week.

### Concepts you must understand
- Classify the work before choosing a runtime: waiting on networks (LLM calls, databases, streams) suits any event loop, while CPU work (parsing, local embeddings, tokenizing long text) needs its own threads, processes or service.
- Estimate out loud with arithmetic: CPU milliseconds per request set requests per second per process (2 ms means about 500), and open streams times memory per stream set memory per pod.
- For self-hosted models, GPU memory is weights plus KV cache, and KV cache per token is 2 × layers × KV heads × head size × bytes per value, multiplied by tokens per sequence and by concurrent sequences.
- Split the latency budget before designing: time to first token, total generation time and the p99 of ordinary endpoints are different targets with different fixes.
- Give each cross-cutting concern exactly one owner in the pipeline (identity, tenant, validation, logging, error mapping) and place it by what that stage can see.
- Migrate without a freeze using a strangler pattern: old and new code run side by side, traffic moves route by route, contract tests prove parity, and rollback is a small change.
- Anything that needs more than a short burst of CPU becomes a job with an id, idempotency, retries, a status endpoint and its own scaling signal.
- Put probabilistic components behind deterministic gates, and decide fail open or fail closed per action before launch, not during the first incident.

### Q. You are building a new AI service that streams LLM answers to a few thousand concurrent users and embeds every uploaded document with a local model. The team writes TypeScript every day. How do you decide the runtime and the process layout?
**Short answer (45 seconds):** I split the work by shape before picking a language. Streaming hosted-LLM answers is waiting on sockets, which a Node.js gateway in TypeScript handles well and the team already knows. Running a local embedding model is CPU or GPU work that must never share a process with the streams. So: a Node gateway for auth, sessions and SSE, an ingestion worker fed by a queue, and the embedding model behind its own server, each scaled on its own signal.

**Deeper explanation:** Clarify: peak streams, documents per hour and their size, how soon a document must be searchable, and whether a GPU exists.

Then estimate. Each open stream is a socket plus some heap, so memory per pod sets streams per pod. If a stream delivers around 30 tokens a second, 2,000 streams means about 60,000 small writes a second, so I coalesce tokens into frames every 50 ms or so.

```text
browser <-SSE- Node gateway (auth, sessions, LLM stream)   scale on: open streams, loop delay
upload  -----> queue (Redis Streams or BullMQ)
               -> ingestion worker (parse, chunk)           scale on: queue depth
               -> embedding server (batched) -> Qdrant      scale on: CPU or GPU use
```

The real decision is where the model runs. Transformers.js or onnxruntime-node in a worker_threads pool keeps one language, but you own batching. A ready-made server such as Hugging Face text-embeddings-inference batches for you and needs no Python from the team. A small FastAPI service makes sense only if someone will own Python. For this team I pick the ready-made server and accept one more container and its list of supported models.

From week one I measure time to first token at the gateway, event loop delay p99, open connections per pod, the age of the oldest queued job and end-to-end ingestion time.

**Follow-ups they will ask:**
- Why not one process for everything? : one large ingestion batch would stall every open stream on it.
- What breaks at the load balancer? : idle timeouts cut quiet streams; send SSE comment pings.

**Mistakes to avoid:**
- Answering "Python, because it is AI" without looking at the workload or the team.
- Autoscaling the gateway on CPU, which stays low while it is saturated with open streams.

### Q. Your team must move a large Express 4 codebase to NestJS while still shipping features every week. How do you plan the migration without a code freeze?
**Short answer (45 seconds):** I run both in one process first: create the Express instance, mount the legacy app on it, and hand that same instance to Nest through ExpressAdapter. I port the cross-cutting pieces first (auth, error format, logging) so ported routes behave exactly like legacy ones, then move one feature at a time, proving parity with the same contract tests against both. New features are written in Nest from day one, so the legacy part only shrinks.

**Deeper explanation:** Clarify: route count and test coverage, whether clients depend on exact error bodies, and whether sessions or a shared database pool exist.

```ts
const server = express();
server.use(legacyApp);   // unported routes still answer first
const app = await NestFactory.create(AppModule, new ExpressAdapter(server), { bodyParser: false });
await app.listen(3000);  // init adds Nest routes, then its 404 and error handlers
```

Order matters: Nest registers its not-found and exception handlers at the end of the stack during init, so anything mounted after init never runs. Legacy routes match first, so the legacy app must drop its own 404 handler, and porting a route means deleting it from the legacy router so the request falls through to Nest. Decide which side parses bodies (`bodyParser: false` turns off Nest's), and expose the legacy pg pool as a Nest provider with `useValue`, so there is one pool, not two.

Port well-tested leaf modules first, and busy modules whenever a feature touches them. Each port runs the shared supertest suite against both implementations; for risky routes I replay recorded traffic with a tool such as GoReplay and diff the responses.

Risks: ValidationPipe with `whitelist: true` silently drops fields legacy accepted, and startup time grows. I measure per-route error rate and p95 before and after each port, and the share of traffic still on legacy code.

**Follow-ups they will ask:**
- Why not a separate Nest service behind the gateway? : independent deploys, but double the infrastructure and split sessions and pools.
- When are you done? : the legacy router is empty and the mount line is deleted.

**Mistakes to avoid:**
- A big-bang rewrite on a branch that falls weeks behind main.
- Porting routes before auth and error-format parity, so clients see different responses mid-migration.

### Q. You are designing the request pipeline for a multi-tenant NestJS API on PostgreSQL where every query must be tenant scoped and the access log must include rejected requests. Where does each concern go?
**Short answer (45 seconds):** Each concern goes where it can see what it needs. Middleware sets the request id, opens an async context and writes the access log on `finish`, so rejected requests are logged too. Guards verify the token, then take the tenant from the verified claim, check membership and store it in the context. A global ValidationPipe checks input, repositories filter by tenant with Postgres row-level security as the backstop, and one exception filter maps domain errors to one error body.

**Deeper explanation:** Clarify: where the tenant comes from (subdomain, token claim or both), whether users belong to several tenants, and the isolation model.

```text
middleware   request id, ClsModule context, access log on res 'finish'
guards       JwtAuthGuard (honours @Public), then TenantGuard: claim -> membership -> cls.set
interceptor  timing and structured logs with tenantId
pipe         global ValidationPipe, whitelist and forbidNonWhitelisted
repository   tenant from ClsService in every query, RLS behind it
filter       DomainError -> status + one body; 5xx logged with request id
```

How the tenant travels matters: a `Scope.REQUEST` provider would make everything that injects it request scoped, so I use AsyncLocalStorage through nestjs-cls and keep singletons. Postgres enforces isolation too, because a forgotten `where tenant_id` is the classic cross-tenant leak:

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON documents
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- in each transaction: SELECT set_config('app.tenant_id', $1, true);
```

Risks: superusers, BYPASSRLS roles and, without FORCE ROW LEVEL SECURITY, the table owner all skip policies, so the app connects as its own role; queue jobs have no request, so the tenant id travels in the payload. I measure 401 and 403 rates per tenant and pipeline overhead at p99, and keep an e2e test where a tenant A user asking for a tenant B record gets 404.

**Follow-ups they will ask:**
- Why the `true` in set_config? : the setting ends with the transaction, so a pooled connection cannot carry a tenant into the next request.
- 404 or 403 for another tenant's record? : 404, so its existence is not confirmed.

**Mistakes to avoid:**
- Trusting an `X-Tenant-Id` header without checking it against the verified token.
- Logging only in an interceptor, which never sees requests a guard rejected.

### Q. You inherit an Express service that parses uploaded PDFs inside the request handler, and every endpoint slows down when customers upload large files. How do you move the parsing out of the request path?
**Short answer (45 seconds):** In two steps. This week I move the parse into a worker_threads pool such as piscina, which keeps the API contract and stops blocking the event loop. Then parsing becomes a job: the file goes to object storage, the API answers 202 with a document id, a queue worker parses it, and the client polls a status endpoint or listens on SSE. Before and after each step I compare event loop delay and the p99 of unrelated endpoints.

**Deeper explanation:** Clarify: file sizes, uploads per hour, parse time and whether the client needs the text immediately.

Step one removes the symptom: the main thread hands the bytes to a pool thread and awaits, so other requests keep flowing. A burst of big files can still queue, so cap the pool and reject oversized files early.

Step two changes the contract:

```ts
const queue = new Queue('pdf-parse', { connection });
app.post('/documents', async (req, res) => {
  const doc = await documents.create({ s3Key: req.body.s3Key, status: 'queued' });
  await queue.add('parse', { docId: doc.id },
    { jobId: doc.id, attempts: 3, backoff: { type: 'exponential', delay: 5000 } });
  res.status(202).json({ id: doc.id, status: 'queued' });
});
// separate deployment: new Worker('pdf-parse', parseDocument, { connection, concurrency: 2 })
```

Key decisions: the browser uploads straight to S3 with a presigned URL, so the API never buffers the file; the job id is the document id, so retries do not parse twice; workers are their own deployment, scaled on queue depth, with a per-job timeout and memory limit, because PDFs are untrusted input and a malformed file should kill only its own worker. I also track queue wait, job duration p95 and the failed set.

For existing clients the old synchronous endpoint stays behind a flag for a while: it enqueues, waits a few seconds, and falls back to 202.

**Follow-ups they will ask:**
- Node or Python for the worker? : whichever parser handles your documents best; the queue makes it a detail.
- UI progress? : the worker publishes to Redis and the API relays it over SSE.

**Mistakes to avoid:**
- Wrapping the parse in a promise and calling it async; it still runs on the main thread.
- An in-process queue, which loses pending jobs on restart.

### Q. A client wants a self-hosted model on vLLM for a contract assistant that reads 30-page documents, with a time-to-first-token target and a budget of one or two GPUs. How do you choose the model size and context length?
**Short answer (45 seconds):** I start from the documents and targets, not a leaderboard: count real contracts with the model's tokenizer, set the context length the task needs, and check that weights plus KV cache per sequence times expected concurrency fit the GPUs. Then I pick the smallest of two or three candidate sizes that meets the quality bar on labelled real contracts, with time to first token measured under load.

**Deeper explanation:** Clarify: concurrent users, questions per contract, the task (clause extraction or drafting) and data residency.

```text
KV per token = 2 (K and V) x layers x KV heads x head size x bytes
Llama 3 8B, FP16:  2 x 32 x 8 x 128 x 2 B = 128 KiB per token
                   32k-token sequence = 4 GiB, weights about 16 GB
Llama 3 70B, FP16: 2 x 80 x 8 x 128 x 2 B = 320 KiB per token
                   32k-token sequence = 10 GiB, weights about 140 GB
```

On one 80 GB GPU the 8B model leaves room for roughly a dozen full 32k sequences. The 70B model needs two GPUs and FP8 or 4-bit weights before any cache, and holds far fewer long sequences. So the choice is usually a smaller model, perhaps LoRA fine-tuned on contracts, with long context, or a larger one with retrieval over clauses to keep prompts short.

Serving settings: `--max-model-len` at the length you tested, not the advertised maximum; prefix caching with the contract before the question, so follow-ups reuse its KV cache; chunked prefill, so one long prompt does not stall streaming for everyone else. vLLM logs its KV cache capacity at startup, which checks the arithmetic.

I measure TTFT p95 and inter-token latency under real load, labelled-set quality, and cost per document (GPU cost per hour over documents per hour).

**Follow-ups they will ask:**
- Why not the longest supported context? : KV cache and prefill grow with it, and quality near the limit often trails retrieval.
- An FP8 KV cache? : `--kv-cache-dtype fp8` halves cache memory versus FP16; check long-input quality first.

**Mistakes to avoid:**
- Sizing GPUs by weights alone and ignoring KV cache at the target concurrency.
- Promising a TTFT number before measuring prefill on real document lengths.

### Q. Your customer-support agent issued account credits it should not have, twice this month, and you have two sprints to add a decision layer in front of its tools. What is your plan?
**Short answer (45 seconds):** First I classify both incidents. If the credits broke a rule the system already knows (wrong account owner, over the limit, already credited), the fix is a deterministic check, not a model. If they were judgment errors, I add a decision layer for write tools only: shadow mode against labelled cases in sprint one, then enforcement in sprint two with a human review band and a fail-closed default.

**Deeper explanation:** Clarify: which tools write data or move money, who staffs review, the latency budget, and whether conversations may go to a vendor.

Sprint one: rank tools as read-only, reversible writes, or irreversible and money, and gate only the last two. Pull every credit proposal from the traces (Langfuse, in a system like CADBEATER) and label a few hundred of them, the two incidents included. Choose by trade-off: Jev needs no training and its options are editable, but it is a vendor call whose probabilities you must verify; a fine-tuned classifier is cheap per call but needs retraining when options change; an LLM judge is flexible but slower and uncalibrated. Behind one interface, run it in shadow mode next to what actually happened.

```ts
async function gate(call: ToolCall, state: string): Promise<'ALLOW' | 'REVIEW' | 'DENY'> {
  if (!GATED_TOOLS.has(call.tool)) return 'ALLOW';
  const p = await decisions.pAppropriate(state, call).catch(() => null); // timeout or error
  if (p === null) return 'REVIEW';                                         // fail closed
  const t = thresholds[call.tool];
  return p >= t.allow ? 'ALLOW' : p >= t.deny ? 'REVIEW' : 'DENY';
}
```

Sprint two: set thresholds from shadow results and the cost of each mistake, enforce on one tool, then the rest. Authorization and policy checks still run after an ALLOW and can veto it, and every decision is logged with model version, probabilities, threshold version and outcome.

I measure wrong-allow rate, review volume against staff, override rate, added p95 latency and cost per decision.

**Follow-ups they will ask:**
- Review queue too big? : narrow the band only where labelled data shows high accuracy.
- Why not gate read-only tools? : mistakes there are cheap, and gating adds latency to every step.

**Mistakes to avoid:**
- Adding a model when the incident was a missing authorization check.
- Defaulting to ALLOW when the decision call times out.

### Practice
- Read the config.json of Llama 3 8B and 70B, compute KV cache per token and per 32k sequence by hand, then start vLLM with `--max-model-len 32768` on a rented GPU and compare your number with the KV cache capacity it logs at startup.
- Mount a small legacy Express router on an Express instance, wrap it with Nest through ExpressAdapter, port one route to a controller, and run the same supertest suite against the route before and after; diff the error bodies.
- Put a PDF parse inside an Express handler, load test another endpoint with autocannon while uploading PDFs, then move the parse to piscina and finally to a BullMQ worker; record event loop delay p99 and the other endpoint's p99 at each step.
- Say it out loud: pick one scenario and answer in three minutes: three clarifying questions, the design, one trade-off, one accepted risk and three metrics.

## Runtime Incidents & Error Cases [Scenarios]

> Incident questions are scored on order and evidence. Use the same five beats every time: clarify the impact (which endpoints, pods or workers, since when, after which change), contain it with the cheapest reversible lever (roll back, flip the flag, scale out, fail closed), diagnose with a named signal (event loop delay, heap trend, `py-spy dump`, finish_reason, a confidence histogram), fix the root cause, and prevent a repeat with an alert, a test or a guardrail. A weak candidate jumps to a favourite cause. A strong candidate says what they would look at first and which result would change their mind.

### Concepts you must understand
- Read the shape before guessing the cause: every endpoint slow at once on one process points at the event loop; one endpoint slow points at its dependency; slow with idle CPU points at a pool or a downstream service.
- Exact error text is a search key: query the logs for it, find the first occurrence, and line it up with the deploy or config change just before it.
- Crashes leave evidence in the previous container: `kubectl logs POD --previous` and the exit code in `kubectl describe pod` (1 for an uncaught error, usually 134 for an abort such as a V8 heap failure, 137 for SIGKILL, often the OOM killer).
- Contain before you diagnose: a rollback or a flag flip takes minutes, a root cause can take an afternoon, and every crash or restart drops in-flight requests.
- For model-backed components the "error" is usually a quality shape (repetition, a confidence drop), so the first check is the per-request metadata you logged: token counts, finish_reason, model version, option and threshold versions.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| p99 rises on every route at once, one core pinned, database idle | event loop delay p99 and a CPU profile from one pod | sync CPU on the main thread: huge JSON.parse or stringify, catastrophic regex, `*Sync` calls, GC pressure | roll back, then stream, cap input or move work to worker_threads |
| fs, DNS or crypto calls slow while event loop delay stays flat | a thread pool probe (time a trivial fs.stat) and UV_THREADPOOL_SIZE | libuv pool saturated by scrypt, pbkdf2 or native bcrypt, slow disks, many dns.lookup calls | hashing in a piscina pool, keep-alive agents, pool size set at process start |
| `FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory` | heapUsed trend over hours and the real heap limit inside the container | unbounded Map cache, listeners added per request, whole result sets or transcripts held in memory | bounded LRU, remove listeners, stream or paginate; confirm with heap snapshots |
| Pod `OOMKilled`, exit code 137, while heapUsed looks normal | rss, external and arrayBuffers from process.memoryUsage() against the container limit | Buffers and native memory outside the V8 heap, --max-old-space-size above the limit | stream large payloads, keep the heap limit well under the container limit |
| Process exits with code 1 on an unhandled promise rejection | `kubectl logs POD --previous`, the stack, the change just deployed | missing await, fire-and-forget promise, promise started early and awaited late, Express 4 async handler | await or return it, Promise.all, Express 5 or a wrapper, the no-floating-promises lint rule |
| `Error [ERR_HTTP_HEADERS_SENT]: Cannot set headers after they are sent to the client` | the stack of the second write and the request id | missing return after an early response, next() after sending, timeout middleware, error handler without a headersSent check | one owner per response, `return res...`, check res.headersSent |
| `Nest can't resolve dependencies of the OrdersService (?)` | the argument index and module context named in the message | provider not exported, module not imported, interface type with no token, circular file import | export and import, @Inject(TOKEN), break the import cycle |
| `Nest cannot create the OrdersModule instance. The module at index [1] of the OrdersModule "imports" array is undefined.` | `npx madge --circular --extensions ts src/` | module import cycle, often through barrel index.ts files | extract a shared module or use events; forwardRef only as a stopgap |
| FastAPI worker stops answering, `/health` times out, every endpoint on it stalls | `py-spy dump --pid PID` on the stuck worker | sync library or CPU work inside `async def`, sync driver in an async dependency | async client, `def` endpoint, `asyncio.to_thread`, process pool |
| Gunicorn `[CRITICAL] WORKER TIMEOUT (pid:1234)` followed by a new worker booting | what the worker was doing at that moment and the slowest request durations | loop blocked longer than --timeout (UvicornWorker heartbeat), long requests on sync workers | remove the blocking call; raising --timeout only hides it |
| Gunicorn `Worker (pid:1234) was sent SIGKILL! Perhaps out of memory?` | `kubectl describe pod` for OOMKilled, memory per worker | a model loaded in every worker, memory that grows per request | fewer workers per pod, load once, `--max-requests` to recycle workers |
| `def` endpoints queue once about 40 run at the same time | the AnyIO thread limiter and concurrent requests per worker | default limiter of 40 threads shared by sync endpoints and sync dependencies | async libraries, or raise the limiter deliberately |
| LLM answers loop or turn into gibberish on long inputs only | prompt tokens, finish_reason and sampling parameters of failing requests | input past the trained or configured context, wrong rope_scaling, truncated instructions, greedy decoding | keep inputs in the tested range, fix config and stop tokens, tune penalties |
| Decision confidence drops and the review queue grows after a product change | confidence and chosen-option histograms by day, option set and model versions | new intent missing from the options, overlapping descriptions, changed state shape, moved model pin | add the option plus an "unclear" option, re-run the eval, re-tune thresholds |

### Q. Right after a release, p99 latency on every endpoint of a Node API jumps at the same moment, one core per pod sits at 100 percent and the database looks idle. Walk me through it.
**Short answer (45 seconds):** Unrelated routes slowing together while dependencies are quiet says the event loop is blocked by synchronous work. If I can profile one bad pod within a minute I take a 30-second CPU profile, then roll back; otherwise I roll back first and reproduce in staging. The profile shows the wide synchronous frame, and the release diff usually confirms it.

**Deeper explanation:**
1. Confirm: event loop delay p99 from `perf_hooks.monitorEventLoopDelay` jumps with latency and `performance.eventLoopUtilization()` sits near 1. Flat loop delay with slow fs or crypto calls would mean the libuv thread pool instead.
2. Contain: `kubectl rollout undo deployment/api`; scaling out only spreads the pain.
3. Profile one bad pod, or a staging pod under autocannon:

```bash
kubectl exec api-7d9f-abc -- kill -USR1 1        # node as PID 1 opens the inspector on 127.0.0.1:9229
kubectl port-forward pod/api-7d9f-abc 9229:9229   # chrome://inspect, record a CPU profile
node --cpu-prof server.js                         # locally: writes a .cpuprofile on exit
```

Likely causes, most common first: new synchronous CPU on the hot path, such as JSON.parse or JSON.stringify of a huge payload (a whole conversation history) or sorting thousands of records in memory; a regex with catastrophic backtracking on user input; a sync API (`readFileSync`, `crypto.pbkdf2Sync`, bcryptjs) in a handler; or GC pressure from a new allocation pattern, visible as GC frames in the profile and long pauses under `--trace-gc`.

Fix the cause: cap or stream the payload, rewrite the regex or use re2 with bounded input, switch to async APIs, or move real CPU work to a piscina pool. Chunking with setImmediate only spreads the cost.

Prevent: alert on loop delay p99 per pod, fail CI when an autocannon run's p99 regresses, enable `n/no-sync` from eslint-plugin-n for request code, and ship through a canary so one pod shows the shape first.

**Follow-ups they will ask:**
- The profile looks normal? : check `--trace-gc` and the thread pool, then log handler time per route to find one slow request type.
- Why was the database idle? : requests were stuck before reaching it, so it saw less traffic, not more.

**Mistakes to avoid:**
- Blaming the database or raising its pool size because latency went up.
- Profiling in production for an hour instead of rolling back first.

### Q. Pods restart every few hours and the last log lines show `FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory`. What do you do?
**Short answer (45 seconds):** The V8 heap hit its limit and the process aborted: something keeps too many objects reachable, or one request loads too much at once. I make sure replicas absorb the restarts, roll back if a release started it, then use the heapUsed trend to tell a leak from a spike, capture snapshots near the limit and follow the retainers of whatever grows.

**Deeper explanation:**
1. Confirm: `kubectl logs POD --previous` shows the fatal line after the last GC lines, and `kubectl describe pod` usually shows exit code 134 (abort). Exit code 137 would be the kernel enforcing the container limit instead.
2. Check the real limit inside the container and arrange snapshots before the next crash:

```bash
node -p "require('v8').getHeapStatistics().heap_size_limit / 1048576"   # MB
node --max-old-space-size=1536 --heapsnapshot-near-heap-limit=2 server.js
```

3. Read the trend: a sawtooth whose floor climbs for hours is a leak; flat and then a cliff is one request or job loading too much.
4. Compare two snapshots in Chrome DevTools (Comparison view, sorted by retained size) and follow the retainer chain to the long-lived owner.

Likely causes, ranked: an unbounded Map used as a cache, keyed by user, tenant or conversation; listeners or intervals added per request and never removed (`MaxListenersExceededWarning` in the logs is a strong hint); whole result sets or long LLM transcripts held in memory, such as an export endpoint; rarely, a limit too small for a legitimate working set.

Fix: a bounded LRU (lru-cache with `max`) or Redis, listeners removed on `close`, cursors and pagination. Raise `--max-old-space-size` only for a proven working set, well below the container limit so Buffers still fit.

Prevent: alert when heapUsed over heap_size_limit stays high, soak test for hours before major releases, and fail tests on MaxListenersExceededWarning.

**Follow-ups they will ask:**
- A snapshot in production? : on one pod out of rotation; it blocks the main thread and, per Node's docs, needs about twice the heap size in memory.
- Restart nightly instead? : it hides a leak that grows with traffic and returns on the busiest day.

**Mistakes to avoid:**
- Raising the heap limit above the container limit, which turns the abort into an OOMKilled.
- Guessing the leak from code reading instead of comparing two snapshots.

### Q. After a deploy, the Node API crashes several times an hour and the previous container's log ends with an unhandled promise rejection. How do you handle it?
**Short answer (45 seconds):** Since Node 15 the default `--unhandled-rejections=throw` mode raises an unhandled rejection as an uncaught exception, so the process exits with code 1 and every in-flight request on it fails. I roll back first, then use the stack and the deploy diff to find the promise nobody awaited. The fix is correct error propagation, never a global handler that logs and carries on.

**Deeper explanation:**
1. Evidence: climbing restarts in `kubectl get pods`, exit code 1 in `kubectl describe pod`, the stack in `kubectl logs POD --previous`. If the reason was not an Error, Node wraps it with code `ERR_UNHANDLED_REJECTION` and there is barely a stack: always reject with Error objects.
2. The stack shows where the error was created, often deep in a driver. Async stack traces only follow awaited chains, so when it stops at the library, look for the caller that did not await.
3. Search the diff with typescript-eslint's `no-floating-promises` rule.

Likely causes, ranked: an Express 4 async handler without a wrapper, so one bad input kills the process; a fire-and-forget call with no catch whose dependency started failing; a promise started early and awaited late; async callbacks passed to `forEach`, `setTimeout` or an EventEmitter.

```js
const quotaP = quota.check(userId);   // rejects after 50 ms
const doc = await docs.load(id);      // still waiting: quotaP has no handler yet
await quotaP;                         // too late
// fix: const [allowed, doc] = await Promise.all([quota.check(userId), docs.load(id)]);
```

Fix: await or return every promise, Promise.all for parallel work, a logging `.catch` on deliberate fire-and-forget calls, and Express 5 or a wrapper. Keep `process.on('unhandledRejection')` only to log with context and exit, so the orchestrator restarts a clean process.

Prevent: the lint rule in CI, a per-route test that fails a dependency and expects a 5xx rather than a crash, and an alert on `kube_pod_container_status_restarts_total`.

**Follow-ups they will ask:**
- Why not `--unhandled-rejections=warn`? : requests hitting the bug hang and state may be half written; a crash is louder and safer.
- Would Express 5 have prevented it? : only for promises the handler returns or awaits.

**Mistakes to avoid:**
- A global handler that swallows the error to stop the restarts.
- Fixing one stack trace without searching for the pattern elsewhere.

### Q. Logs show `Error [ERR_HTTP_HEADERS_SENT]: Cannot set headers after they are sent to the client` on an Express API, sometimes followed by a process crash. How do you track it down?
**Short answer (45 seconds):** The error means code tried to set a header, a status or a body after the response had started, so two code paths both think they own the response. The stack shows the second write; my job is to find the first. I also treat it as a possible security bug, because a missing `return` after an early 403 means the protected action still ran.

**Deeper explanation:**
1. The request id on the error gives the route and inputs; the stack points at the second `res.status`, `res.setHeader` or `res.json`.
2. Find the first write. In staging, record where the head was written:

```js
app.use((req, res, next) => {
  const writeHead = res.writeHead;
  res.writeHead = function (...args) {
    res.locals.firstWrite = new Error('first write').stack;  // staging only
    return writeHead.apply(this, args);
  };
  next();
});
// error handler: if (err.code === 'ERR_HTTP_HEADERS_SENT') log res.locals.firstWrite
```

3. The crash: a second write after an `await` in an Express 4 handler throws inside a promise, an unhandled rejection that ends the process on Node 15 or later.

Likely causes, ranked: an early response without `return` (`if (!user) res.status(404).json(...)` and the code carries on); middleware that sends and also calls `next()`; `error` and `end` handlers that both respond; a timeout middleware that sends 503 while the handler finishes later; an error handler calling `res.status(500)` on an SSE stream that already sent chunks.

Fix: one exit per branch (`return res.status(404).json(...)`), `if (res.headersSent) return next(err)` in error middleware, a `req.timedout` check with connect-timeout, and for streams an error event plus `res.end()`. In NestJS the same error appears when a handler injects `@Res({ passthrough: true })` and also sends the response itself, because Nest then sends again.

Prevent: tests asserting no side effect on rejected requests and a log alert on the error string.

**Follow-ups they will ask:**
- Why does the client often get a sensible answer? : the first write won; the damage is the extra work and its side effects.
- Can the client see a broken response? : yes, a truncated body if Express destroys the socket.

**Mistakes to avoid:**
- Wrapping the second `res.json` in a headersSent check, which hides the double path.
- Dismissing it as log noise when it fires on an authorization branch.

### Q. After a refactor that added barrel `index.ts` files, the NestJS API will not boot and logs `Nest can't resolve dependencies of the OrdersService (?)`. Walk me through the fix.
**Short answer (45 seconds):** With readiness probes this is contained by design: new pods never become ready, the rollout stalls and old pods keep serving. The message names the constructor argument index and the module context. Either the dependency is not visible in that module, or its type was undefined when the decorator ran because of a circular file import, which a barrel refactor makes very likely.

**Deeper explanation:**
1. Read the whole message: argument index, module and potential solutions. A real class name at that index means visibility: is the provider in this module's `providers`, or exported by a module it imports? No real name (Nest prints a generic placeholder) means the type was undefined at decoration time.
2. Find the cycle:

```bash
npx madge --circular --extensions ts src/
# e.g. orders/orders.service.ts > payments/index.ts > payments/payments.service.ts > orders/index.ts
```

3. A cycle between modules gives a different message: `Nest cannot create the OrdersModule instance. The module at index [1] of the OrdersModule "imports" array is undefined.`

Likely causes, ranked: an import cycle through barrels, where importing from `../payments` loads an index.ts that re-exports something which imports orders; a provider not exported, or a module not imported; a parameter typed with an interface or a type-only import, which emits `Object` and needs `@Inject(TOKEN)`; in tests only, a runner such as Vitest on esbuild that emits no decorator metadata.

Fix: inside a feature, import concrete files, not barrels; for a real two-way dependency, extract the shared logic into a third module or use an event. `forwardRef(() => PaymentsModule)` on both sides boots, but construction order becomes indeterminate, neither constructor may use the other, and the design problem stays.

Prevent: madge or dependency-cruiser with a no-cycles rule in CI, a test that compiles the real AppModule with `Test.createTestingModule({ imports: [AppModule] }).compile()`, and readiness probes so a pod that cannot boot never takes traffic.

**Follow-ups they will ask:**
- Why can an unrelated import change break boot? : import order decides which side of the cycle is still undefined when decorators run.
- Listing the provider in both modules boots. Fine? : each module gets its own instance, which breaks shared state.

**Mistakes to avoid:**
- Sprinkling forwardRef until it boots.
- Marking a module @Global() to hide a missing import.

### Q. After a release, a FastAPI service freezes for seconds at a time, `/health` checks fail and Gunicorn logs `[CRITICAL] WORKER TIMEOUT (pid:...)` before replacing workers. The release added a vendor SDK call inside an `async def` endpoint. What do you do?
**Short answer (45 seconds):** A classic blocked loop: the SDK makes a synchronous network call on the event loop thread, so the Uvicorn worker serves nothing else and misses its heartbeat, and after `--timeout` (30 seconds by default) Gunicorn kills it with every in-flight request. I contain with a rollback or a one-line hotfix that moves the call to a thread, confirm with `py-spy dump`, then switch to an async client.

**Deeper explanation:**
1. Confirm the shape: every endpoint on the worker stalls, not only the new one, and freezes line up with slow vendor responses. `Worker (pid:...) was sent SIGKILL! Perhaps out of memory?` would be the OOM killer, a different incident.
2. Look inside a stuck worker:

```bash
py-spy dump --pid 4242   # in Docker or Kubernetes this needs the SYS_PTRACE capability
# expect MainThread in an ssl or socket recv, called from the vendor SDK, called from the endpoint
```

3. In staging, `PYTHONASYNCIODEBUG=1` makes asyncio log callbacks that hold the loop longer than 100 ms.

Likely causes, ranked: a sync HTTP client (requests, boto3, most vendor SDKs) inside `async def`; CPU work inside `async def`, such as tokenizing or parsing a large document; a sync database driver in an `async def` dependency; on Gunicorn's default sync workers, plain long requests.

```python
# hotfix: keep async def, run the sync call in a thread
report = await asyncio.to_thread(vendor.create_report, payload)
# real fix: the vendor's async client or httpx.AsyncClient, created in lifespan, with a timeout
```

Give the SDK a timeout too: a hung call in a thread holds a pool thread forever.

Prevent: ruff's ASYNC rules (ported from flake8-async) in CI flag blocking HTTP calls and `time.sleep` in async functions; a load test watches `/health` latency while the slow path runs; an alert fires on worker restarts per hour.

**Follow-ups they will ask:**
- Why not raise `--timeout` to 120? : the worker still serves nothing while blocked; each freeze just lasts longer.
- Plain Uvicorn in Kubernetes? : it blocks the same way, and the liveness probe becomes what kills it.

**Mistakes to avoid:**
- Switching every endpoint to `def` without finding the blocking call.
- Treating WORKER TIMEOUT as an infrastructure problem and adding replicas.

### Q. Users report that answers about long documents start repeating the same sentence or drift into gibberish, while short prompts are fine. The model is self-hosted on vLLM. How do you debug it?
**Short answer (45 seconds):** A failure only on long inputs points first at context: prompts beyond what the model was trained or configured for, a wrong RoPE scaling setting, or truncation that cut the instructions. Decoding settings come second. I pull failing requests with prompt token counts, finish_reason and sampling parameters, then reproduce one at temperature 0 and shorten it until the problem disappears.

**Deeper explanation:**
1. Per-request metadata from Langfuse or gateway logs: prompt and completion tokens, finish_reason, sampling parameters, model and adapter version. Bucket failures by prompt length; a cliff at one length is a strong clue, and finish_reason `length` on a looping answer means no stop token came.
2. Configuration: `max_position_embeddings` and `rope_scaling` in config.json, vLLM's `--max-model-len`, whether someone forced a longer length with `VLLM_ALLOW_LONG_MAX_MODEL_LEN`, and whether a merged fine-tune kept the base model's rope_scaling.
3. The rendered prompt: chat template applied once, instructions present, and how the app trims long inputs; trimming from the front drops the system prompt.
4. Bisect: one document cut to increasing lengths at temperature 0, then the same on unquantized weights with an FP16 KV cache to rule out quantization.

Likely causes, ranked: input past the trained or extended context, or wrong RoPE scaling; app-side truncation removing instructions; greedy decoding with no repetition control; quantization degrading at long range; a stop-token mismatch after fine-tuning (Llama 3 instruct ends a turn with `<|eot_id|>`, id 128009), which usually shows on short prompts too.

```python
resp = client.chat.completions.create(
    model="contracts-8b", messages=msgs, temperature=0.2, max_tokens=800,
    frequency_penalty=0.2,                     # tune on the eval set
    extra_body={"stop_token_ids": [128009]},   # vLLM sampling extension
)
log.info("finish=%s prompt_tokens=%s", resp.choices[0].finish_reason, resp.usage.prompt_tokens)
```

Fix: keep inputs inside the tested length with retrieval or map-reduce summarization, correct the config and stop tokens, and add a stream guard that aborts when recent sentences repeat. Prevent: a long-input eval slice with a repeated n-gram metric, and an alert on the rate of finish_reason `length`.

**Follow-ups they will ask:**
- Why not just raise repetition_penalty? : it hides the symptom; past the trained context the model is still guessing.
- Proof of the fix? : the long-input eval slice before and after.

**Mistakes to avoid:**
- Raising `--max-model-len` because documents are long, without checking the trained length.
- Debugging with random sampling, so every rerun looks different.

### Q. A week after a launch added a "pause subscription" feature, the decision layer's confidence on `next_step` drops, the review queue doubles and some pause requests are routed to cancellation. What do you do?
**Short answer (45 seconds):** This is a change-induced shift, not random drift: users have an intent the options do not describe, and a closed-set model must still pick one of them. I make the cancellation path fail closed, then compare confidence and chosen options before and after launch, label low-confidence cases, and check what changed in options, state and model version.

**Deeper explanation:**
1. Contain: `cancel` decisions require explicit user confirmation until the fix ships.
2. Query the decision log per day and chosen option:

```sql
SELECT date_trunc('day', created_at) AS day, answer->>'choice' AS choice, count(*),
       avg((answer->>'confidence')::float) AS avg_conf,
       avg((action = 'REVIEW')::int) AS review_rate
FROM decision_log
WHERE question = 'next_step' AND created_at > now() - interval '21 days'
GROUP BY 1, 2 ORDER BY 1, 2;
```

3. Read the change log: option set and threshold versions, the model pin (did someone switch to `jev-latest`?), the state builder (new or renamed JSON fields, a shorter transcript window) and the agent prompt.
4. Label low-confidence cases and cancellations that users later reversed.

Likely causes, ranked: no option for the new intent, so probability spreads across `cancel` and `modify_plan`; overlapping option descriptions; a state that changed shape and lost the user's words; a moved model version; a real change in who the users are.

Fix: add a `pause_subscription` option whose description clearly separates it from cancellation, plus an explicit `unclear` option; extend the labelled set with post-launch cases, re-run the evaluation, re-tune thresholds, then shadow and ship it as a new config version. With a fine-tuned classifier the same fix means new labels and a retrain, which is the trade-off between the two.

Prevent: decision options on the launch checklist, an evaluation gate in CI for changes to options, thresholds, state building or the model pin, and alerts on shifts in confidence and review rate per option.

**Follow-ups they will ask:**
- Why did confidence drop instead of staying high and wrong? : the evidence partly fits two options; some cases are still confidently wrong, so track reversed outcomes too.
- Did thresholds help? : yes, they sent part of it to review instead of cancellation.

**Mistakes to avoid:**
- Lowering the ALLOW threshold to shrink the review queue.
- Re-tuning thresholds before fixing the option set.

### Practice
- Break it on purpose (Node): add a route that runs JSON.parse on a 50 MB string, a route that fills a Map with no eviction, and a route that starts a rejecting promise and awaits it late; run with `--max-old-space-size=256 --heapsnapshot-near-heap-limit=1`, load test with autocannon, then capture the loop delay graph, a heap snapshot and the crash log, and fix each one.
- Break it on purpose (Python): call `requests.get` on a slow endpoint inside `async def`, run under `gunicorn -k uvicorn.workers.UvicornWorker --timeout 10`, wait for WORKER TIMEOUT, take a `py-spy dump`, then fix it with `asyncio.to_thread` and finally with `httpx.AsyncClient`.
- Create an OrdersModule and PaymentsModule cycle through barrel files, read both Nest boot errors, find the cycle with madge, and remove it by extracting a shared module.
- Write a five-line runbook (first check, contain, likely causes, fix, prevention) for every row of the table you have not seen in production.
- Say it out loud: pick one error from the table and in ninety seconds cover impact, containment, first check, ranked causes, fix and prevention.
