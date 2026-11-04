## Database Indexing

### Why it exists
Without an index, finding the rows that match a condition means reading the whole table, which is fine at ten thousand rows and painful at thirty million. An index is a separate sorted structure, usually a B-tree (a balanced tree kept in key order), that maps column values to row locations, so the database jumps straight to the matching rows the way you use the index at the back of a book. Before teams understood indexing they bought bigger servers or precomputed answers by hand. The cost is that every insert, update and delete must also maintain each index, indexes take disk and memory, and an index that does not match the query's shape is simply ignored.

## Transactions & Isolation Levels

### Why it exists
A business action usually touches several rows, such as taking money out of one account and putting it into another, and a crash or a concurrent request halfway through would leave the data wrong. A transaction makes a group of changes all-or-nothing and hides them from other work until they are committed, so code can reason as if it ran alone. Without transactions every application had to write its own recovery and locking logic, and most got it wrong. Isolation levels exist because perfect isolation is expensive: stronger levels prevent more anomalies but add locking, aborted transactions and retries, so you choose the weakest level that still keeps your rules true.

## Concurrency

### Why it exists
A backend serves many users at once, and their requests interleave in time, even in single-threaded Node.js, because every `await` lets another request run. When two requests read and write the same data, the result can depend on timing, which produces lost updates, double bookings and counters that drift. Concurrency tools such as atomic operations, locks, connection pools and queues exist to keep shared state correct while still doing many things at once. The trade-off is throughput against safety: more locking means more waiting and possible deadlocks, less locking means more room for race conditions.

## Caching

### Why it exists
Some data is read far more often than it changes, and fetching it from the database or recomputing it on every request wastes time and money. A cache keeps a copy closer to the reader, in process memory, in Redis or at a CDN, so most reads skip the slow path. Before shared caches, teams answered read spikes with bigger databases and more read replicas. The price is staleness and complexity: two copies that can disagree, invalidation rules to get right, and a database that may be too small for the day the cache is suddenly empty.

## Idempotency

### Why it exists
Networks fail in a way that leaves the caller unsure: the request timed out, but did the server process it? The only safe reaction is to retry, and without idempotency a retried payment or order becomes a duplicate. Idempotency means sending the same request twice has the same effect as sending it once, usually by tagging each operation with a unique key and remembering its result. It costs storage for keys and results, an extra lookup on the write path, and careful handling of the case where the first attempt is still running.

## Message Queues

### Why it exists
When one service calls another directly, both must be up and fast at the same moment, and a traffic burst or a slow dependency flows straight back to the user. A queue or log such as RabbitMQ, Kafka or SQS lets the producer hand off work and move on, while consumers process it at their own pace and retry failures. Before brokers were common, teams polled database tables from cron jobs, which worked until load and locking made it slow. The trade-off is that work becomes asynchronous: you now handle duplicates, ordering, poison messages that fail every time, consumer lag, and the question of how the user learns the result.

## Distributed Systems Basics

### Why it exists
One machine cannot hold all the data or traffic of a large product, and a single machine is a single point of failure, so systems spread across many nodes. Once they do, messages can be delayed, lost or duplicated, clocks disagree, and any node can fail while the others keep running. Ideas such as the CAP theorem (during a network split you choose between consistency and availability), consistency models, leases and heartbeats are the vocabulary for deciding what you give up when the network misbehaves. The cost is that simple things become hard: a counter, a lock or "exactly once" all need careful protocols, and every design has to say what happens during a partition.

## API Design

### Why it exists
An API is a contract with teams, apps and customers that you cannot update all at once, so a careless change breaks clients you never see. Good API design, meaning clear resources, consistent errors, pagination, versioning and idempotent writes, lets clients integrate without reading your code and lets you evolve the server without breaking them. Before shared conventions like REST, and later GraphQL and gRPC, every integration was a custom protocol with its own documentation. The trade-off is upfront care and some rigidity: once published, a field name or a status code is very expensive to change.

## Database Design

### Why it exists
How you shape tables and relations decides which questions are cheap to answer, which mistakes the database will stop for you, and how painful every later change will be. Normalisation keeps each fact in one place so copies cannot drift apart, and constraints such as foreign keys and unique indexes let the database reject bad data instead of trusting every code path. Teams that skip design end up with duplicated data, slow joins and migrations that need downtime. The trade-off is write correctness against read speed: denormalising, caching or sharding make some reads fast but add copies to keep in sync.

## Production Debugging

### Why it exists
Production fails in ways that never show up locally: real data volumes, real concurrency, partial outages of dependencies and unusual client behaviour. Debugging there means working from evidence such as metrics, logs, traces and database statistics, without attaching a debugger or stopping the service. Before observability tooling, engineers logged into servers and read log files by hand, which does not work across dozens of short-lived pods. The cost is instrumentation work, storage bills for logs and traces, and the discipline to add request ids and structured logs before the incident rather than during it.

## Node.js Runtime Internals

### Why it exists
Node.js runs your JavaScript on one main thread with an event loop and hands slow I/O to the operating system and a small thread pool, so one process can hold thousands of connections without a thread per request. That design removed the memory and context-switching cost of older "one thread per connection" servers. The trade-off is that any CPU-heavy or synchronous work on the main thread freezes every request in that process, and memory limits, garbage collection and stream backpressure become your problem. Knowing the internals is what lets you explain a latency spike or an out-of-memory kill instead of guessing.

## Authentication, Authorization & API Security

### Why it exists
Every API is reachable by people and bots you did not intend, so the server must know who is calling (authentication) and what they may do (authorization) on every request. Sessions, JWTs, OAuth and API keys exist because sending passwords around or trusting the client's word breaks the moment one request is forged or replayed. Most real breaches are not broken cryptography but missing checks, such as one endpoint that forgets the tenant filter or trusts an id in the URL. The cost is friction and moving parts: token lifetimes, refresh and revocation, key rotation, and a check on every code path.

## Resilience & Microservice Patterns

### Why it exists
Once a system is split into services, each request depends on several network calls, and one slow or failing dependency can drag the whole chain down. Timeouts, retries with backoff, circuit breakers, bulkheads, sagas and the outbox pattern (saving an event in the same database transaction as the change it describes) exist to contain those failures and keep data consistent without one global transaction. Without them, a slow payment provider or a crashed consumer becomes a site-wide outage or silently lost events. The trade-off is complexity and eventual consistency: more states to model, more paths to test, and failures that are handled rather than prevented.

## Python & FastAPI for AI Backends

### Why it exists
Most AI tooling, including model SDKs, embedding libraries, evaluation tools and LangGraph, is Python-first, so AI features often need a Python service even when the rest of the stack is Node.js. FastAPI gives async request handling, validation driven by type hints through Pydantic, and automatic OpenAPI docs, replacing the older pattern of Flask plus hand-written validation. Its main traps are blocking calls inside async handlers, which stall the event loop for every request, and the GIL (the lock that lets only one thread run Python code at a time), which limits CPU-bound work in one process. You also take on a second language's packaging, deployment and observability alongside the main stack.

## Backend System Design Walkthroughs

### Why it exists
Real systems are built under limits of traffic, data size, budget and team size, and there is never one correct architecture. Design walkthroughs exist to practise turning a vague requirement into a concrete, defensible plan: clarify, estimate, sketch, then go deep on the part that breaks first. Without that habit, engineers reach for fashionable tools, overbuild, or miss the one bottleneck that matters. Every choice buys something, such as speed, simplicity or consistency, by giving something else up, and a good answer names both sides.

## SQL Interview Patterns

### Why it exists
Business questions such as "who are our best customers" or "did this campaign work" live in relational data, and SQL answers them inside the database instead of pulling millions of rows into application code. Window functions, CTEs and careful joins replaced pages of loops in scripts and spreadsheet exports. The risk is that a query can run and still answer the wrong question, through double counting after a join, NULL handling or time zones. Writing it well takes time to pin down what one result row means, and making it fast needs the right indexes or pre-aggregated tables.

## Backend Project Scenarios [Scenarios]

> Project rounds open with a situation you could plausibly have lived: "You are building...", "You inherit...", "Your team must migrate...". There is no single correct architecture. The interviewer scores whether you pin down requirements and numbers before drawing, choose the simplest design that meets them, name the trade-off of each decision, and know what breaks first and how you would see it. A weak answer is a list of technologies. A strong answer sounds like someone who has run the launch or the migration: ordered steps, rollback points, and the metrics on the dashboard from day one.

### Concepts you must understand
- Clarify the shape before the design: read and write rates at peak rather than average, data size and growth, the latency target as a percentile, freshness and consistency needs, and who the clients are.
- Do rough numbers out loud: 30 million rows at about 1 KB each is about 30 GB, which fits comfortably on one PostgreSQL instance, so "we need a distributed database" needs a better reason.
- Name the invariant that must never break (no overselling, no double charge, no cross-tenant read) and design the write path around it; most other data can be eventually consistent.
- Prefer boring parts you can operate, such as PostgreSQL, Redis and one queue, and add a new datastore only when a number forces it, because every extra store adds a sync path that can drift.
- Change live systems in reversible steps (expand, migrate, switch, contract) with a feature flag or a routing rule as the rollback at every step.
- Decide each dependency's failure policy up front: timeout, retry budget, fail open or fail closed, and what the user sees.
- Define how you will know it works before you build: the SLO, the business metric, and the alert that fires before customers notice.

### Q. You are building the order and payment API for a flash sale: 5,000 units of one phone and a few hundred thousand users pressing Buy at 12:00 sharp. How do you make sure nothing is oversold and nobody is charged twice?
**Short answer (45 seconds):** I split the contended part, claiming a unit, from the slow part, paying for it. Traffic passes an admission layer that lets in only what checkout can absorb. A reservation is one atomic operation with a per-user limit and an expiry, and the order row in PostgreSQL is the system of record. Payment uses an idempotency key created once per order and passed to the provider, the provider webhook confirms it, and a sweeper returns unpaid reservations to stock.

**Deeper explanation:** First I clarify the per-user limit, hold length, whether payment is synchronous or a 3-D Secure redirect, and the sold-out experience.

```text
waiting room -> admission tokens at a fixed rate
POST /orders (Idempotency-Key)
  Redis Lua: if stock > 0 and user not in buyers -> DECR stock, SADD buyers
  PostgreSQL: INSERT order (reserved, hold_expires_at), UNIQUE (sale_id, user_id)
  create payment with provider, same key
provider webhook -> order paid (dedupe by event id)
sweeper: reserved and expired -> cancelled, INCR stock
```

The Lua script makes check and decrement atomic, so two buyers never both take the last unit. Redis is not the record: replication is asynchronous, so a failover can lose recent decrements, and the unique constraint plus reconciling paid orders against units is the backstop. The pure database option, `UPDATE sale_stock SET remaining = remaining - 1 WHERE sale_id = $1 AND remaining > 0`, is correct but serialises every buyer on one hot row; splitting stock across several bucket rows spreads that lock.

Hold length is a trade-off: long holds park stock in abandoned carts, short holds fail slow payers. I watch admission rate, hold-to-paid conversion, provider latency, and an invariant alert: paid orders never exceed units.

**Follow-ups they will ask:**
- What if Redis fails over mid-sale?: pause admission, rebuild the counter from active orders in PostgreSQL, then resume.
- Why not queue every purchase request?: a single ordered consumer is fair and simple, but users wait for the result over polling or SSE.

**Mistakes to avoid:**
- Reading stock, then updating it in a second step, which oversells.
- Holding a database transaction open across the payment provider call.
- Treating autoscaling as the plan; the database does not scale with pods.

### Q. Your team must add a NOT NULL tenant_id foreign key and a unique (tenant_id, external_ref) rule to a 30-million-row PostgreSQL orders table that takes writes all day. How do you ship it with zero downtime?
**Short answer (45 seconds):** I plan every step by the lock it takes. Nullable column, code that fills it on new rows, a throttled batch backfill, the unique index built concurrently, the foreign key and a NOT NULL check added as NOT VALID and validated separately, then SET NOT NULL. Each DDL gets a short `lock_timeout` and a retry, rehearsed on a production-sized copy.

**Deeper explanation:** First I confirm how old rows map to a tenant and every path that inserts orders.

```sql
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN tenant_id bigint;          -- metadata only, no rewrite
UPDATE orders o SET tenant_id = a.tenant_id FROM accounts a
WHERE o.account_id = a.id AND o.id >= $1 AND o.id < $2 AND o.tenant_id IS NULL;
CREATE UNIQUE INDEX CONCURRENTLY orders_tenant_ref_uq ON orders (tenant_id, external_ref);
ALTER TABLE orders ADD CONSTRAINT orders_tenant_fk
  FOREIGN KEY (tenant_id) REFERENCES tenants (id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_tenant_fk;
ALTER TABLE orders ADD CONSTRAINT orders_tenant_nn CHECK (tenant_id IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_tenant_nn;
ALTER TABLE orders ALTER COLUMN tenant_id SET NOT NULL;  -- PG 12+: uses the check, no scan
```

The outage risk is the lock queue, not the DDL itself. `ALTER TABLE` needs a brief `ACCESS EXCLUSIVE` lock; if a long report query holds the table, the ALTER waits and every new query queues behind it. `lock_timeout` turns that into a retryable failure instead of a frozen table. `VALIDATE CONSTRAINT` takes only `SHARE UPDATE EXCLUSIVE`, so traffic continues while it scans.

The backfill writes 30 million new row versions (bloat and WAL), so it runs in committed primary-key batches of a few thousand rows, pausing on replica lag in `pg_stat_replication`. Dedupe (tenant_id, external_ref) pairs first, or the index build fails. I watch lock waits (`log_lock_waits = on`), replica lag, write p99 and remaining NULLs.

**Follow-ups they will ask:**
- Migration tool?: one step per migration, with the transaction disabled for `CREATE INDEX CONCURRENTLY`, which cannot run inside one.
- The concurrent build failed halfway?: it leaves an INVALID index; `DROP INDEX CONCURRENTLY`, fix the cause, rebuild.

**Mistakes to avoid:**
- One migration running every step in one transaction, or one 30-million-row UPDATE.
- Adding NOT NULL before every insert path writes the column.

### Q. You must extract the billing module from a NestJS monolith into its own service, and other modules join billing tables directly. Walk me through the plan.
**Short answer (45 seconds):** I do not start with a new repo. First I make billing a real module inside the monolith: every other module goes through a BillingService interface and nobody else touches its tables. Then I split the data, stand up the service, and switch callers behind a flag with shadow comparison and per-tenant rollout. Each step ships and rolls back on its own; only the last adds a network hop.

**Deeper explanation:**

1. Clarify the goal (independent deploys, scaling or ownership) and map the seams: imports of billing entities outside the module, SQL joins on invoice tables, transactions writing orders and invoices together.
2. Enforce the boundary in-process: BillingModule exports only its service, and ESLint `no-restricted-imports` or Nx module boundaries block the rest. Joins become calls or a read model.
3. Split ownership: billing tables move to a `billing` schema owned by one database role, and other modules lose their grants. Reports that joined invoices read a projection fed by `InvoiceIssued` events through a transactional outbox.
4. Stand up the service with its own database, kept in sync by logical replication or CDC until cutover.
5. Branch by abstraction: the monolith's BillingService becomes an adapter that runs in-process or calls the service, per a flag. Shadow reads call both and log differences.
6. Cut over reads, then writes, by tenant percentage. Rollback is the flag.
7. Delete the in-process code once the old path shows zero traffic for a full billing cycle.

The transaction spanning orders and invoices is the real design work: it becomes a local write plus an outbox event and an idempotent billing consumer, not a distributed transaction. Synchronous calls remain only for reads needing fresh data, with a timeout and fallback. I measure shadow diff rate, new-path latency and errors, and nightly reconciliation of invoice counts and totals across both stores.

**Follow-ups they will ask:**
- Can you shadow writes?: never for side effects such as charging a card or emailing; shadow reads only.
- Latency?: loops that now call the service per item are an N+1 over the network; add batch endpoints.

**Mistakes to avoid:**
- Copying the code into a new service that still shares the same tables.
- A big-bang cutover with no flag and no reconciliation.

### Q. A client needs near-instant, typo-tolerant search with filters over 30 million records that change all day, in a NestJS and PostgreSQL system like VData. How do you design it?
**Short answer (45 seconds):** I first pin down the query shapes, the latency target and how fresh results must be. If search covers one or two text fields plus filters, PostgreSQL with trigram GIN indexes is often enough and keeps one source of truth. If the client needs relevance ranking across many fields, facets, synonyms and highlighting, I add OpenSearch fed from PostgreSQL by a change stream, never by dual writes from the app.

**Deeper explanation:** Clarify what users type (names, ids, free text), filters, sorts, facets, the p95 target, how soon an edit must be searchable, and permission rules. At about 1 KB per record that is roughly 30 GB, one node for either option.

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY records_name_trgm ON records USING gin (name gin_trgm_ops);
SELECT id, name FROM records
WHERE tenant_id = $1 AND name % $2
ORDER BY similarity(name, $2) DESC
LIMIT 20;
```

The `%` similarity operator uses the GIN index, which also serves `ILIKE '%term%'`, otherwise a sequential scan of 30 million rows. Exact identifiers such as order numbers and emails go to a B-tree lookup instead.

When PostgreSQL is not enough: denormalised OpenSearch documents, built by an indexer consuming an outbox or Debezium change stream through Kafka and writing with the bulk API. Documents become searchable after a refresh (every second by default), the freshness trade-off. Mapping changes build a new index and swap an alias, so search never goes down. Permission filters go inside the query, and `search_after` replaces deep `from` and `size` paging, capped at 10,000 results by default.

I measure p95 and p99 latency, indexing lag, zero-result rate, click-through, and a daily count reconciliation between PostgreSQL and the index.

**Follow-ups they will ask:**
- Trigram search plus the tenant filter in one index?: the `btree_gin` extension lets one GIN index cover `tenant_id` and the trigram column together.
- Autocomplete?: edge n-gram analyzers or the completion suggester in OpenSearch; in PostgreSQL a B-tree with `text_pattern_ops` serves `LIKE 'abc%'`.

**Mistakes to avoid:**
- Writing to PostgreSQL and OpenSearch from the request handler; one write eventually fails and the stores drift.
- Reaching for Elasticsearch before measuring what PostgreSQL does with the right index.

### Q. You are building outbound webhooks for a B2B platform: customers register URLs, every order event must reach them, and some endpoints are slow or down for days. How do you design delivery and retries?
**Short answer (45 seconds):** Events go into an outbox in the same transaction as the business change. A dispatcher fans each event out to matching subscriptions as delivery rows, and workers POST them with a short timeout and an HMAC signature, recording every attempt. Failures retry with exponential backoff and jitter over a bounded window, and each endpoint is isolated so a dead one cannot slow the rest. The contract is at-least-once with an event id for dedupe, plus a replay API.

**Deeper explanation:** I would confirm event volume, the retry window customers expect, and whether anyone needs ordering.

```text
order tx -> outbox -> dispatcher -> deliveries(endpoint_id, event_id, status,
                                               attempts, next_attempt_at)
worker loop:
  SELECT ... FROM deliveries WHERE status = 'pending' AND next_attempt_at <= now()
  ORDER BY next_attempt_at LIMIT 100 FOR UPDATE SKIP LOCKED
  POST with a 10 s timeout, no redirects, private IP ranges blocked
  2xx -> delivered
  else -> attempts + 1, next_attempt_at = now() + backoff(attempts) with jitter
  window exhausted -> failed, visible to the customer
```

Isolation is the key decision: with one shared queue, an endpoint that hangs 10 seconds per call soaks up workers while healthy endpoints wait. So each endpoint gets a concurrency cap and its own breaker: after consecutive failures, pause it and probe occasionally; after days, disable it and email the owner.

Retries reorder events, so I promise no ordering. Payloads carry an event id, type, created_at and resource version; or I send thin events and receivers fetch current state, making order irrelevant. Signing uses a per-endpoint secret over timestamp plus raw body, with two valid secrets during rotation.

I measure per-endpoint success rate, time to first successful delivery, oldest pending age and disabled endpoints.

**Follow-ups they will ask:**
- A customer says an event never arrived?: the attempts log shows status code, latency and response snippet per try, and replay resends it.
- Which responses do you retry?: timeouts, connection errors, 5xx and 429 honouring Retry-After; other 4xx usually mean misconfiguration, though a few retries cover a fix in progress.

**Mistakes to avoid:**
- Sending webhooks inline in the API request.
- One retry queue shared by every endpoint, or unbounded retries that never surface a failure.

### Q. A large enterprise client joins your multi-tenant SaaS. They want proof their data cannot leak to other tenants and that their heavy usage will not slow anyone else down. How do you design for it?
**Short answer (45 seconds):** I first ask what they require: logical isolation, a dedicated database, data residency, their own encryption keys, audit evidence. My default is a pooled model with tenant_id on every row, enforced by PostgreSQL row level security so a forgotten WHERE clause cannot leak data, plus a routing layer that can place a tenant in its own database when the contract demands it. Noisy neighbours are handled with per-tenant limits tied to the plan and fair scheduling of background work.

**Deeper explanation:**

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON invoices
  USING (tenant_id = current_setting('app.tenant_id')::bigint);
-- per request, inside the transaction (safe with PgBouncer transaction mode)
SELECT set_config('app.tenant_id', $1, true);
```

Superusers and BYPASSRLS roles always skip policies, and table owners skip them unless `FORCE ROW LEVEL SECURITY` is set, so the app connects as a plain role that owns nothing. If the setting is missing, the policy expression errors instead of matching rows, so it fails closed.

| Model | Isolation | Cost |
|---|---|---|
| Shared tables, tenant_id, RLS | logical | cheapest, one migration run |
| Schema per tenant | stronger, per-tenant restore | migrations run per schema |
| Database per tenant | physical, own backups and keys | highest operational cost |

Noisy neighbour controls, keyed by tenant and plan: request rate and concurrency limits at the gateway, background jobs queued per tenant and pulled round-robin so one tenant's million-row import does not block others, and `statement_timeout` per role. Per-tenant metrics (p99 latency, database time, queue depth) show who is heavy, and the routing table can move a tenant to its own database. Proof for the client: CI tests that create two tenants and assert every endpoint returns 404 or empty across them, audit logs, and a penetration test report.

**Follow-ups they will ask:**
- Does RLS protect Redis and search?: no; tenant_id goes into every cache key and every search filter.
- Background workers have no request context?: each job carries tenant_id and sets it explicitly, and a job without one fails.

**Mistakes to avoid:**
- Relying on every developer to remember `WHERE tenant_id = $1`.
- Connecting as the table owner, which silently bypasses RLS.

### Practice
- Write the Redis Lua reservation script, fire 2,000 concurrent buyers at 100 units with autocannon or k6, and assert exactly 100 reservations with no user twice; then kill Redis mid-run and rebuild the counter from PostgreSQL.
- Generate 30 million rows with `generate_series`, run the tenant_id migration steps while pgbench drives writes, and record lock waits and p99; then run a plain `SET NOT NULL` and a non-concurrent index build and watch writes stall.
- Compare `ILIKE '%term%'` with and without a trigram GIN index using `EXPLAIN (ANALYZE, BUFFERS)` on a few million rows.
- Build the webhook worker with `FOR UPDATE SKIP LOCKED`, point one subscription at an endpoint that sleeps 10 seconds, and prove healthy endpoints still deliver on time.
- Say it out loud: give the flash sale design in four minutes, starting with the questions you would ask and ending with the dashboard you would watch at 12:00.

## Backend Incidents & Error Cases [Scenarios]

> Incident questions test whether you can be trusted with the pager. Use the same spine every time: clarify the impact (who, how many, since when, is money or data at risk), contain it (roll back, turn a flag off, shed load, pause a consumer), diagnose from evidence in a fixed order, fix the cause, and prevent a repeat with an alert, a test, a limit or a runbook. Weak answers jump to a guessed root cause, or restart things and destroy the evidence. Strong answers name the first command or dashboard they would open, mitigate before they fully understand, and end with the guardrail.

### Concepts you must understand
- Mitigate before you understand: roll back the deploy, turn off the flag, shed or rate limit traffic, pause the consumer; root cause comes after the bleeding stops.
- Correlate with change first: deploys, config, migrations, traffic shape and dependency status pages explain most incidents.
- Read the exact error text and identify which layer produced it (client, gateway, app, pool, database), because "502", "timeout" and "connection refused" each point at a different hop.
- Capture evidence before restarting: a `pg_stat_activity` snapshot, a heap snapshot, the consumer group description, the failing request ids.
- Every incident ends with one guardrail that would have caught it earlier: an alert on the leading metric, a test, a limit or a runbook step.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| `FATAL: sorry, too many clients already` | `pg_stat_activity` grouped by application and state, against `max_connections` | pods times pool size exceeds the limit, rollout surge, leaked connections | pool budget per pod, PgBouncer in transaction mode, cap autoscaling |
| `timeout exceeded when trying to connect` (node-postgres pool) | `pool.totalCount`, `idleCount`, `waitingCount`; `idle in transaction` sessions | client not released on an error path, transaction held across an HTTP or LLM call | `release()` in `finally`, no network calls inside transactions |
| `ERROR: deadlock detected` (SQLSTATE 40P01) | DETAIL lines in the PostgreSQL server log naming both processes and statements | rows or tables locked in different orders by two code paths | one lock order everywhere, smaller transactions, retry on 40P01 |
| `ERROR: could not serialize access due to concurrent update` (40001) | isolation level of the failing transaction | concurrent writers under REPEATABLE READ or SERIALIZABLE | retry the whole transaction with backoff |
| `ERROR: canceling statement due to statement timeout` | `pg_stat_statements` mean time, `EXPLAIN (ANALYZE, BUFFERS)` | missing index, plan flip after statistics changed, lock wait | index or rewrite, `ANALYZE`, longer timeout only for batch roles |
| `ERROR: duplicate key value violates unique constraint` (23505) | which constraint, how often, whether the requests were retries | double submit, retry without an idempotency key, two workers on one job | `INSERT ... ON CONFLICT`, treat as an idempotent replay |
| Kafka consumer lag climbing for hours | `kafka-consumer-groups.sh --describe` LAG per partition, run twice | slow handler or downstream, poison message, hot partition | fix the handler, batch writes, DLQ, scale up to the partition count |
| Constant rebalances, `CommitFailedException` in Java clients | rebalance rate, batch processing time against `max.poll.interval.ms` | a poll batch takes longer than the interval | fewer records per poll, faster handler, larger interval |
| Redis `OOM command not allowed when used memory > 'maxmemory'.` | `INFO memory`, `CONFIG GET maxmemory-policy` | keys without TTL under `noeviction`, large values | TTLs, `allkeys-lru` for a pure cache, bigger node |
| DB load spikes right after Redis empties | `INFO keyspace` key count, `INFO stats` hits against misses | FLUSHALL, restart without persistence, failover to an empty replica | shed load, single-flight misses, controlled warm-up |
| 502 with nginx `upstream prematurely closed connection while reading response header from upstream` | timing of 502s against idle periods and deploys | Node `keepAliveTimeout` shorter than the proxy's idle timeout, pod killed mid-request | server keep-alive above the proxy timeout, graceful shutdown |
| 504 with nginx `upstream timed out (110: Connection timed out) while reading response header from upstream` | latency of that route, `proxy_read_timeout` | slow query or dependency, blocked event loop, long synchronous export | fix the slow path, move long work to a job |
| `TokenExpiredError: jwt expired` or `NotBeforeError: jwt not active` right after login | `chronyc tracking` and `timedatectl` on issuer and verifier hosts | clock skew between nodes, no NTP on new hosts | time sync everywhere, small `clockTolerance` |
| `FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory`, or pod `OOMKilled` (exit 137) | heap trend, `kubectl describe pod` last state | leak, unbounded in-memory cache, whole file or result set loaded at once | heap snapshots, bounded caches, streams, correct limits |

### Q. Support reports customers charged twice for one order, all within ten minutes when the payment provider was slow. What do you do, in order?
**Short answer (45 seconds):** Money is at risk, so I contain first: find every affected order, stop new duplicates by cutting payment retries or pausing checkout, and refund duplicates proactively. Then I trace one duplicated order to find which layer retried without a stable idempotency key: app, client, gateway or queue consumer. The fix is one key per payment, created before the first call and reused on every retry.

**Deeper explanation:** Impact comes from our data and the provider's export, since the worst cases are timeouts we recorded as failed that the provider completed.

```sql
SELECT order_id, count(*) AS charges, sum(amount) AS total
FROM payments
WHERE status = 'succeeded' AND created_at >= now() - interval '2 hours'
GROUP BY order_id HAVING count(*) > 1;
```

Refund via the provider API, with idempotency keys on refunds too. Likely causes, ranked:

1. The service's HTTP client retried a timed-out charge with a new key or none, because keys were generated per attempt, not per payment.
2. The web or mobile client retried, or the user double-tapped, without an `Idempotency-Key`.
3. A queue consumer got the charge job redelivered after a visibility timeout, with no dedupe.
4. The gateway retried POSTs; nginx only does that with `non_idempotent` in `proxy_next_upstream`, so look for it.

Fix: persist the payment attempt and its key before calling the provider, and treat a timeout as unknown, not failed: retry with the same key, which returns the original result, before any new attempt. Add a guardrail so a second success cannot be recorded silently:

```sql
CREATE UNIQUE INDEX CONCURRENTLY payments_one_success_per_order
  ON payments (order_id) WHERE status = 'succeeded';
```

Prevent: the duplicate query as an alert every few minutes, a retry budget and circuit breaker on the provider client, provider latency injected in staging with Toxiproxy, and daily reconciliation against the provider's settlement report.

**Follow-ups they will ask:**
- The provider has no idempotency keys?: send your order reference as metadata and search the provider by it before any retry.
- Who else needs to know?: support gets the refund list and a reply template; finance gets the totals.

**Mistakes to avoid:**
- Generating a fresh key per retry, which makes every retry a new charge.
- Marking timeouts as failed and inviting the user to pay again.

### Q. Since a nightly reconciliation job shipped, the API logs `ERROR: deadlock detected` dozens of times a night and some order updates fail. How do you track it down?
**Short answer (45 seconds):** This is not an outage: PostgreSQL broke each cycle by aborting one transaction. First I make the losing side retry on SQLSTATE 40P01 so users stop seeing errors. Then I read the server log, which names both processes and statements, and change one code path so both lock in the same order, or make the job lock less at a time.

**Deeper explanation:** The server log has the detail the client error lacks:

```text
ERROR:  deadlock detected
DETAIL:  Process 4121 waits for ShareLock on transaction 99812; blocked by process 4377.
         Process 4377 waits for ShareLock on transaction 99790; blocked by process 4121.
         Process 4121: UPDATE payments SET status = 'captured' WHERE order_id = 7
         Process 4377: UPDATE orders SET reconciled_at = now() WHERE id = 7
```

Here the job locks payments then orders while the API locks orders then payments. Turn on `log_lock_waits = on` to see near misses, and during the job window watch who blocks whom:

```sql
SELECT pid, pg_blocking_pids(pid) AS blocked_by, wait_event_type, left(query, 60)
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Likely causes, ranked: two code paths touching the same tables in opposite orders; a multi-row `UPDATE ... WHERE id IN (...)` locking rows in plan order while another path uses a different order; one huge job transaction widening the window; `FOR UPDATE` on parent rows while another path inserts children, whose foreign key checks take share locks on the parent.

Fix: one documented lock order (orders before payments), sorted locking for batches (`SELECT id FROM orders WHERE id = ANY($1) ORDER BY id FOR UPDATE`), small job batches, each its own transaction, and `FOR UPDATE SKIP LOCKED` so the job skips rows the API holds. Prevent: a retry wrapper for 40P01 and 40001 with jitter, an alert on the `deadlocks` counter in `pg_stat_database`, and a test running the job against concurrent API traffic.

**Follow-ups they will ask:**
- Why only at night?: the job is the only writer using the other order; daytime traffic alone never forms a cycle.
- Raise `deadlock_timeout`?: it only delays detection (default one second); it never prevents a cycle.

**Mistakes to avoid:**
- Treating a longer timeout or an off-peak schedule as the fix.
- Swallowing 40P01 without retrying, so updates silently disappear.

### Q. During a traffic spike the API fails with node-postgres `timeout exceeded when trying to connect`, and PostgreSQL logs `FATAL: sorry, too many clients already`. Walk me through it.
**Short answer (45 seconds):** Those are two different limits: the app's pool queue timing out, and the server refusing connections beyond `max_connections`. I contain first: stop the autoscaler adding pods, since each new pod adds a whole pool, and terminate long `idle in transaction` sessions. Then I count who holds connections and for how long.

**Deeper explanation:**

```sql
SELECT application_name, state, count(*),
       max(now() - state_change) AS longest
FROM pg_stat_activity
GROUP BY 1, 2 ORDER BY 3 DESC;
SHOW max_connections;
```

Then do the arithmetic: pods times pool max, plus workers, cron jobs and admin tools. If the autoscaler took 10 pods with `max: 20` to 30 pods, the app alone wants 600 connections; a rolling deploy runs old and new pods at once. Little's law explains the pool side: connections in use equal request rate times hold time, so anything that lengthens the hold exhausts the pool.

Likely causes, ranked:
1. Autoscaling multiplied pools past the database budget.
2. Sessions stuck `idle in transaction`: code that opens a transaction and then awaits a payment or LLM call before COMMIT.
3. A leaked client: `pool.connect()` with no `release()` on an error path, shrinking the pool until every request waits.
4. Slow queries after a plan change, holding every connection longer.

Immediate relief:

```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle in transaction' AND now() - state_change > interval '1 minute';
```

Proper fix: PgBouncer in transaction mode, or RDS Proxy on AWS, in front of the database; a per-pod pool derived from a budget (usable connections over maximum pods); `idle_in_transaction_session_timeout` and `statement_timeout`; `client.release()` in `finally`; no network calls inside transactions. Prevent: alerts on sustained `waitingCount` above zero and on connections above about 80 percent of `max_connections`, and an autoscaler maximum tied to the budget.

**Follow-ups they will ask:**
- Why not raise `max_connections`?: each connection is a process with its own memory, queries beyond the core count only add contention, and it needs a restart.
- What breaks under PgBouncer transaction mode?: session state such as `SET`, advisory locks, `LISTEN`, and on older versions named prepared statements.

**Mistakes to avoid:**
- Raising the pool to 100 per pod, which moves the queue into the database.
- Restarting pods; connections free up briefly and the same leak returns.

### Q. Kafka consumer lag on the order-events topic has grown for six hours, and downstream emails and search updates are hours stale. What do you do?
**Short answer (45 seconds):** First I check whether consumers are slow or stuck: describe the group twice, a minute apart, and compare offsets. Even lag on every partition means a throughput problem; one partition lagging means a hot key or a poison message; offsets that barely move plus frequent rebalances mean consumers are being kicked out mid-batch. I also check that the oldest unconsumed data is not about to fall out of retention, because that turns lag into data loss.

**Deeper explanation:**

```bash
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group search-indexer
# per partition: CURRENT-OFFSET, LOG-END-OFFSET, LAG, CONSUMER-ID
kafka-configs.sh --bootstrap-server kafka:9092 --alter --entity-type topics \
  --entity-name order-events --add-config retention.ms=604800000   # buy time if needed
```

Likely causes, ranked:
1. A slower downstream: the handler writes to a database or search cluster that got slower. Check handler duration p99 and the downstream's own metrics. Fix with batched writes (the bulk API for search) and more consumers, up to the partition count.
2. A rebalance loop: processing one poll batch takes longer than `max.poll.interval.ms` (five minutes by default in the Java client), the consumer is removed, its partitions move, and uncommitted work is redone. Logs show repeated rebalances and `CommitFailedException`. Fix with fewer records per poll and a faster handler, or a larger interval.
3. A poison message: one partition stuck at the same offset while the handler throws and retries forever. Fix with bounded retries, then a dead letter topic.
4. A hot partition: one key, often one large tenant, dominates. Fix the key design.

To catch up, scale consumers to the partition count, and pause non-critical consumers that compete for the same downstream. Prevent: alert on lag measured in time, not just message count, plus handler p99, rebalance rate and dead letter topic depth.

**Follow-ups they will ask:**
- Add partitions to catch up?: it only helps new data and remaps keys to different partitions, which breaks per-key ordering.
- Reset offsets to latest?: that skips data for this group; acceptable only for disposable consumers such as a cache warmer, and the group must be inactive.

**Mistakes to avoid:**
- Adding consumers beyond the partition count; the extras sit idle.
- Committing offsets before processing to make lag look better, which loses messages on a crash.

### Q. Someone ran FLUSHALL on the production Redis during a debugging session. Within a minute PostgreSQL CPU is pinned and the API is timing out. What now?
**Short answer (45 seconds):** The cache was hiding the real read load, and the database was never sized for all of it. I protect the database first: shed or rate limit expensive non-critical endpoints, let connection pools cap database concurrency, and switch on single-flight miss handling if a flag exists. Then I warm the hottest keys at a controlled rate, and afterwards remove the ability to flush production by hand.

**Deeper explanation:** Confirm it was a flush, not eviction or a restart without persistence:

```bash
redis-cli INFO keyspace                       # key count collapsed?
redis-cli INFO stats | grep -E 'keyspace_(hits|misses)|evicted_keys'
redis-cli INFO commandstats | grep -i flush   # cmdstat_flushall calls
redis-cli INFO server | grep uptime_in_seconds
```

In PostgreSQL, `pg_stat_statements` shows cache-backed queries with exploding `calls`.

Containment, in order:
1. Shed load: return 503 with Retry-After on recommendation and analytics endpoints so checkout and login survive.
2. Bulkhead: keep pool limits low so requests queue and fail fast in the app instead of piling onto PostgreSQL.
3. Coalesce misses across replicas: one recompute per key under `SET lock:{key} <token> NX PX 5000`, with losers waiting briefly or returning a fallback.
4. Warm deliberately: a script loads the top keys from access logs or a known hot list at a fixed rate.

Do not restart or scale API pods: new pods arrive with empty local caches and add database load.

Prevent:
- Remove FLUSHALL, FLUSHDB, KEYS and CONFIG from application and human users with Redis ACLs (`-@dangerous`), or `rename-command` on self-managed Redis; humans get read-only users in production.
- Stale-while-revalidate with a logical expiry, jittered TTLs and single-flight in the cache client.
- A cold-cache load test, and an alert on the hit ratio, not just Redis uptime.

**Follow-ups they will ask:**
- Can you restore the data?: with AOF enabled and no rewrite since the flush, stopping Redis and removing the trailing FLUSHALL from the AOF recovers it; for a pure cache, warming is usually faster.
- Sessions lived in the same Redis?: they are gone too, so everyone is logged out; keep durable state and cache in separate instances.

**Mistakes to avoid:**
- Letting every request recompute on a miss.
- Treating it only as a training problem instead of removing the permission.

### Q. After moving the API to Kubernetes behind an ingress, users see bursts of 502s during deploys, scattered 502s at quiet times, and 504s on the report export endpoint. How do you untangle it?
**Short answer (45 seconds):** Three symptoms usually mean three causes, so I split them by status code, timing and route. A 502 from the proxy means the upstream refused, reset or closed the connection; a 504 means it did not answer before the proxy timeout. The ingress error log names the exact upstream failure, and correlating it with deploy times, idle periods and the route usually gives the answer within minutes.

**Deeper explanation:** First confirm who generated the error: an nginx-styled error page or an AWS ALB log entry where `target_status_code` is `-` means the proxy produced it, not the app.

```bash
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller --since=1h \
  | grep -E 'prematurely closed|upstream timed out|connect\(\) failed'
```

Map each message to a cause:

1. Bursts during deploys with `connect() failed (111: Connection refused) while connecting to upstream` or resets: pods stopped while still listed as endpoints. Fix with graceful shutdown: fail readiness, a short preStop sleep, `server.close()`, and `maxUnavailable: 0` in the rollout.
2. Scattered 502s at quiet times with `upstream prematurely closed connection while reading response header from upstream`: the keep-alive race. Node closes idle sockets after `keepAliveTimeout` (5 seconds by default) while the proxy reuses them.

```js
const server = app.listen(3000);
server.keepAliveTimeout = 65_000; // longer than the proxy or ALB idle timeout (ALB default 60 s)
server.headersTimeout = 66_000;   // keep above keepAliveTimeout
```

3. 504s on export with `upstream timed out (110: Connection timed out) while reading response header from upstream`: the request outlives `proxy_read_timeout` (60 seconds by default in nginx). Raising it only moves the cliff; make the export a job that returns 202 and a download link, and cancel server-side work when the client disconnects.

Prevent: a dashboard splitting 5xx by source (proxy or app), a synthetic check running through every deploy, and alerts on ingress 502 rate per route.

**Follow-ups they will ask:**
- 502s only from pods on one node?: suspect the node's networking; cordon it and compare.
- Should the ingress retry?: only idempotent methods, with a small budget, or a slow upstream turns into a retry storm.

**Mistakes to avoid:**
- Raising every timeout to several minutes.
- Treating 502 and 504 as one problem without reading the proxy's error log.

### Q. After the auth service moved to new VMs, a few percent of users get 401s right after login with `NotBeforeError: jwt not active` or `TokenExpiredError: jwt expired`, but only on some API pods. How do you diagnose it?
**Short answer (45 seconds):** Failures seconds after issuance that depend on which pod verified the token point to clocks, not to the tokens. I group failures by node, compare the token's `iat`, `nbf` and `exp` with each host's clock, and check time sync on the new issuer VMs and the failing nodes. The fix is working NTP everywhere, with a small `clockTolerance` in verification as a guard.

**Deeper explanation:** Pods share their node's kernel clock, so "only some pods" usually means "pods on some nodes". Decode a failing token's claims somewhere safe; never log full tokens in production:

```bash
node -e 'console.log(JSON.parse(Buffer.from(process.argv[1].split(".")[1], "base64url")))' "$TOKEN"
date -u +%s          # on the auth host and on the failing node
timedatectl status   # look for "System clock synchronized: yes"
chronyc tracking     # "System time" shows the offset from NTP
```

Read the error type. `jwt not active` means `nbf` is still in the future for the verifier: the issuer's clock runs ahead or the verifier's behind. `jwt expired` seconds after login means the verifier's clock runs ahead, or the issuer's runs behind with a short TTL. `JsonWebTokenError: invalid signature` is a different problem, usually a key or JWKS cache mismatch.

Likely causes, ranked: the new VMs have no time sync running, or outbound NTP is blocked; a VM restored from a snapshot or resumed from suspend with a drifted clock; tokens issued with `nbf` equal to the issue time, so any verifier slightly behind rejects them.

Fix: enable chrony or systemd-timesyncd against the cloud provider's time source (Amazon Time Sync Service at 169.254.169.123 on AWS), drain nodes until they are in sync, and allow a small tolerance:

```js
jwt.verify(token, publicKey, { algorithms: ['RS256'], clockTolerance: 30 }); // seconds
```

Prevent: alert on clock offset per node (node_exporter exposes `node_timex_offset_seconds`) and chart auth failures by reason and by node.

**Follow-ups they will ask:**
- Why not a large tolerance?: it extends the life of stolen or revoked tokens; keep it small and fix the clocks.
- Does the browser's clock matter?: only if the client decides when to refresh from `exp`; refresh on a 401 or from `expires_in` instead.

**Mistakes to avoid:**
- Lengthening token TTLs or setting `ignoreExpiration` to make the errors disappear.

### Q. Right after a deploy that moved order listing to a new TypeORM repository layer, PostgreSQL CPU climbs towards 100 percent and GET /orders p95 is several times slower, yet no single query is slow. What happened and how do you prove it?
**Short answer (45 seconds):** The deploy is the change, so I roll it back or flag it off first; if CPU recovers, that confirms the direction. "CPU up, no slow query" points to query count, not query cost. I compare `calls` in `pg_stat_statements` before and after, and count database spans per request in traces; an N+1 shows up as a cheap primary-key lookup whose calls grew with page size times request rate.

**Deeper explanation:** Reproduce the new build in staging or a canary with stats reset, then sort by calls:

```sql
SELECT pg_stat_statements_reset();   -- staging or canary only
-- run the listing load, then:
SELECT calls, round(mean_exec_time::numeric, 2) AS mean_ms, left(query, 70)
FROM pg_stat_statements ORDER BY calls DESC LIMIT 5;
```

Expect something like `SELECT ... FROM "customer" WHERE "id" = $1` with calls close to orders listed, and a trace waterfall with dozens of identical database spans per request. TypeORM's `logging: ['query']` in staging shows the same pattern.

Likely causes in an ORM refactor, ranked:
1. A DTO mapper that awaits a relation per item, such as lazy relations or `Promise.all(orders.map(o => customerRepo.findOneBy(...)))`. Parallel N+1 is still N+1, and it also grabs pool connections.
2. The `relations` option dropped when moving from QueryBuilder to `find()`.

Fix by loading relations in one go:

```ts
const orders = await orderRepo.find({
  where: { tenantId },
  relations: { customer: true, items: true },
  order: { createdAt: 'DESC' },
  take: 50,
});
```

Or use `leftJoinAndSelect`, an `In(ids)` batch with a map, or DataLoader in GraphQL resolvers.

Prevent: a test that asserts the query count per endpoint through a counting TypeORM logger, ESLint `no-await-in-loop`, an APM alert on database spans per request, and a canary comparing top statements by calls with the previous release.

**Follow-ups they will ask:**
- Why does CPU rise if each query is fast?: every query pays parse, plan, execute and a network round trip; thousands of tiny ones cost more than one larger query.
- No rollback possible because of a migration?: hotfix the read path behind a flag; the schema can stay.

**Mistakes to avoid:**
- Searching only the slow query log, where fast N+1 queries never appear.
- Scaling the database or adding a cache to hide it.

### Practice
- Break it on purpose: run a small Express app with a node-postgres pool of `max: 5`, add a route that opens a transaction and awaits a three-second fake HTTP call before COMMIT, load it with autocannon, and watch `timeout exceeded when trying to connect` and `idle in transaction` rows in `pg_stat_activity`; then move the call outside the transaction and compare throughput.
- Reproduce a deadlock with two `psql` sessions updating two rows in opposite order, read the DETAIL in the server log, then switch both to `ORDER BY id FOR UPDATE` and show it is gone.
- Run a local Kafka broker and a consumer whose handler sleeps longer than a lowered `max.poll.interval.ms`; watch rebalances and lag with `kafka-consumer-groups.sh`, then fix it with smaller batches.
- Put nginx with upstream keep-alive in front of a Node server with `keepAliveTimeout` set to one second, send low-rate traffic until 502s appear, then raise the timeout and confirm they stop.
- Say it out loud: tell the duplicate-charge incident in three minutes as impact, containment, diagnosis, fix and prevention, naming the exact query and the guardrail.
