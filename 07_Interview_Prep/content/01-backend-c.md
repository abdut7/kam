# Backend Engineering (part 3)

> Continues the backend track.

## API Design

> Interviewers use API design to see whether you think about the people on the other side of the contract: the mobile team that cannot ship a hotfix for two weeks, the partner who parsed your error body with a regex, the client that retries blindly. A weak answer recites "use nouns and the right verbs". A strong answer talks about compatibility, pagination that survives inserts, status codes that let clients branch correctly, long-running work that does not hold a connection open, and a deprecation path that breaks nobody on a Friday night. Expect them to take one endpoint you describe and ask you to redesign it under a new constraint.

### Concepts you must understand
- A resource is a noun with a stable identity (the URL); the representation (JSON, protobuf) is separate from the resource, and the HTTP method carries the semantics (GET is safe and idempotent, PUT is idempotent, POST is neither by default).
- Statelessness means every request carries what the server needs (token, cursor, idempotency key); server-side session state is what breaks horizontal scaling and retries.
- Compatibility is a contract with clients you do not control: additive changes are safe, removals and changes of type or meaning are breaking, and "optional" today must stay optional tomorrow.
- Pagination is a consistency problem as much as a performance one: offset pagination drifts under inserts and costs O(offset) rows, while keyset or cursor pagination seeks with an index.
- Status codes are machine-readable branches for the client; the body (Problem Details for HTTP APIs, RFC 9457, formerly RFC 7807) is for humans and logs, and the two must never disagree.
- Long-running work is modelled as a job resource: respond 202 with a URL to poll, push completion by webhook or SSE, and make the submission idempotent.
- REST, GraphQL and gRPC solve different problems: coarse resources over HTTP for public APIs, client-shaped reads for aggregated UIs, typed binary RPC with streaming for internal services.
- Versioning is a last resort; the first line of defence is designing for extension (objects instead of scalars, enums clients must treat as open, tolerant readers).
- Error bodies, rate limiting (429 plus Retry-After), idempotency keys and request ids are part of the API design, not operational afterthoughts.

### Q. What makes an API RESTful? What are the constraints?
**Short answer (45 seconds):** REST is Fielding's architectural style, not "JSON over HTTP". The constraints: client-server separation, statelessness, cacheability, a layered system, a uniform interface (resources identified by URIs, manipulated through representations, self-descriptive messages, hypermedia links) and optional code on demand. Most production APIs stop at resources plus verbs plus status codes, level 2 of the Richardson Maturity Model, which is the right trade-off for a product API.

**Deeper explanation:** Each constraint buys a property. Statelessness means any instance can serve any request, so load balancing, retries and scale-down are trivial; a server-side "current page" throws that away. Cacheability means GETs carry `Cache-Control` and `ETag`, so CDNs and browsers serve them and conditional requests return 304. The uniform interface lets a stranger guess that `GET /orders/42` reads and `DELETE /orders/42` deletes, and lets generic tooling (OpenAPI codegen, gateways rate limiting by method and path) work without special cases.

```text
L0  one URL, POST everything          RPC over HTTP
L1  resource URLs                     /orders/42
L2  verbs, status codes, headers      PUT, 201, 404, ETag
L3  hypermedia controls               "links": [{"rel": "cancel"}]
```

Defaults at level 2: plural nouns, nesting one level deep, filters as query parameters, PATCH with a defined merge format, one error shape, and non-CRUD actions as sub-resources (`POST /orders/42/cancellation`), never `?action=cancel`.

**Follow-ups they will ask:**
- PUT or PATCH for a partial update?: PATCH; PUT replaces the whole representation and is idempotent, PATCH is idempotent only if the patch format is.
- Why does statelessness matter if sticky sessions exist?: they break on scale-down, deploys and retries, and pin hot users to one instance.
- Can a POST be retried safely?: only with an idempotency key, which is why payment APIs require one.

**Mistakes to avoid:**
- "It uses JSON and HTTP verbs, so it is RESTful": name the constraints and what they buy you.
- Dismissing hypermedia without a reason (OpenAPI and codegen cover most of its value for first-party clients).

### Q. When would you use REST vs GraphQL vs gRPC?
**Short answer (45 seconds):** REST for public and partner APIs, where HTTP caching, simple tooling and coarse resources matter. GraphQL when several clients need different shapes of the same graph and you want to stop writing one endpoint per screen. gRPC for internal service-to-service calls where typed contracts, low overhead, deadlines and streaming matter, usually behind a REST edge.

**Deeper explanation:** The real trade-off is who controls the query shape and what the transport gives you.

| | REST | GraphQL | gRPC |
|---|---|---|---|
| Shape decided by | server | client | server (proto) |
| Transport | HTTP, JSON | HTTP POST, JSON | HTTP/2, protobuf |
| Caching | native HTTP | application level | none built in |
| Streaming | SSE, WebSocket | subscriptions | unary, server, client, bidirectional |
| Browser | direct | direct | grpc-web or a gateway |
| Failure mode | over and under fetching | N+1 resolvers, deep queries | proto coupling |

GraphQL moves cost to the server: every resolver can trigger an N+1 unless you batch with DataLoader, and a client can send a ten-level query, so you need depth and complexity limits and per-field authorisation. gRPC gives generated clients, propagated deadlines and cheap serialisation, but you lose curl-ability and need interceptors for auth, retries and tracing.

**Follow-ups they will ask:**
- How do you cache GraphQL?: persisted queries as GET with a hash, per-type response caching with TTLs, and a normalised client cache (Apollo Client).
- Does gRPC work from a browser?: not directly; it needs grpc-web through Envoy or a REST translation layer.
- How do you version gRPC?: field numbers are the contract; add fields, never renumber or reuse, mark removed ones `reserved`.

**Mistakes to avoid:**
- Presenting GraphQL as "REST but better"; it trades client flexibility for server complexity and loses HTTP caching.
- Choosing gRPC for a public API that partners call from scripts and browsers.

### Q. How do you version an API without breaking existing clients?
**Short answer (45 seconds):** First, avoid needing a version: make changes additive and require clients to tolerate unknown fields. When a change is truly breaking, pick one scheme and apply it everywhere: a path prefix (`/v2/orders`) is visible and easy to route and cache; a header (`Stripe-Version: 2024-06-20`) keeps URLs stable and lets you pin a default version per API key. Run both, measure traffic per version, announce a sunset date, retire with warnings.

**Deeper explanation:**

| Scheme | Pros | Cons |
|---|---|---|
| URL path `/v1/` | obvious, routable, cache friendly | whole surface bumps at once |
| Header (`Accept: application/vnd.api.v2+json` or custom) | stable URLs, per-client pinning | invisible in browsers and logs unless added |
| No version, additive only | zero migration cost | needs discipline, semantics frozen |

Date-based header versioning (Stripe's model) pins each account to the version it signed up with; the server keeps one current implementation plus a chain of thin transforms that rewrite requests and responses for each older version. For retirement: send `Deprecation` and `Sunset` (RFC 8594) headers on old-version responses, log the version on every request so you know who is still on it, contact the owners, then run short announced brownouts before the final shutdown. In NestJS, `app.enableVersioning({ type: VersioningType.URI })` or `VersioningType.HEADER` versions per controller.

**Follow-ups they will ask:**
- What counts as breaking?: removing or renaming a field, changing a type or format, tightening validation, changing default behaviour or an error code clients branch on.
- How long do you keep the old version?: until the announced sunset or usage is near zero; measure it.
- How do you version GraphQL?: you mostly do not; mark fields `@deprecated(reason:)` and add new ones.

**Mistakes to avoid:**
- Versioning every minor change; `/v7/` means clients rewrote their integration six times.
- Forking the codebase per version instead of transforming at the edge.

### Q. What is cursor-based pagination and why is it better than offset?
**Short answer (45 seconds):** Offset pagination says "skip 10,000 rows and give me 20"; the database still walks those rows, and if a row is inserted or deleted between pages the client sees duplicates or gaps. Cursor pagination says "give me 20 rows after this specific row", where the cursor encodes the sort key of the last item (`created_at` plus `id`). The query becomes an index seek, cost is constant per page, and results stay stable under writes.

**Deeper explanation:**

```sql
-- offset: scans and discards 10000 rows on every page
SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 10000;

-- keyset: seeks to the position; index on (created_at DESC, id DESC)
SELECT * FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The second column is the tie-breaker; without it two orders with the same timestamp can be skipped or repeated. The cursor is an opaque base64 string of `created_at|id` so you can change the encoding later. MongoDB: `find({ _id: { $lt: lastId } }).sort({ _id: -1 }).limit(20)`, which works because ObjectId is roughly time ordered. Costs: no "jump to page 37", totals need a separate query, and sorting by a mutable column such as `updated_at` makes rows move between pages.

**Follow-ups they will ask:**
- How do you page backwards?: flip the comparison and the ORDER BY, reverse the batch in memory, return both `next_cursor` and `prev_cursor`.
- Why base64 the cursor?: so clients treat it as opaque and you can change the internals.
- When is offset fine?: small admin tables, search pages where users expect page numbers, data that does not change under the reader.

**Mistakes to avoid:**
- Using only `created_at` as the cursor; collisions skip rows.
- Exposing the raw `id` as the cursor and then being unable to change the sort order.

### Q. What HTTP status codes should your API return for these scenarios?
**Short answer (45 seconds):** Pick the code for what the client should do next: 2xx done, 3xx go elsewhere, 4xx fix the request and do not retry blindly, 5xx our fault, retry with backoff. The distinctions matter: 401 is "who are you" and 403 is "I know you and no", 404 versus 410 says whether to come back, and 429 and 503 carry `Retry-After`.

**Deeper explanation:**

| Scenario | Code |
|---|---|
| Validation failure (bad email, missing field) | 400 or 422, pick one, with a field-level error list |
| Missing or invalid credentials | 401 plus `WWW-Authenticate` |
| Authenticated but not allowed | 403, or 404 if existence is secret |
| Unknown id | 404 |
| Deleted permanently | 410 Gone |
| Duplicate create, illegal state transition | 409 Conflict |
| `If-Match` ETag mismatch | 412 Precondition Failed |
| Rate limited | 429 plus `Retry-After` |
| Long job accepted, not finished | 202 plus `Location` of the job |
| Byte range of a large file | 206 plus `Content-Range` |
| Upstream failed or timed out | 502 or 504; our own crash is 500 |
| Overloaded or in maintenance | 503 plus `Retry-After` |

Pair every 4xx and 5xx with one body shape (`application/problem+json`: `type`, `title`, `status`, `detail`, `instance`, plus `request_id`), and let the framework map validation to 400 or 422 (NestJS `ValidationPipe`, FastAPI request validation) instead of 500.

**Follow-ups they will ask:**
- 400 or 422 for validation?: both defensible; 400 for malformed syntax, 422 for well-formed but invalid, and consistency matters more than the choice.
- When should a client retry?: on 429, 502, 503, 504 and network errors, with exponential backoff and jitter; never on other 4xx.

**Mistakes to avoid:**
- Returning 200 for everything with errors in the body; clients, proxies, dashboards and retry logic all go blind.
- Swapping 401 and 403, or 500 for a user's bad input.

### Q. How do you design an API endpoint that might take 30 seconds to complete?
**Short answer (45 seconds):** Do not hold the connection open for 30 seconds. Validate, enqueue the work, and return 202 Accepted with a job resource the client can poll: `Location: /jobs/j_42`. The job has a small state machine (queued, running, succeeded, failed) and when done carries the result or a link to it. Clients that cannot poll get a webhook; browsers get SSE for progress. Submission is idempotent so a retried POST does not create two jobs.

**Deeper explanation:** Holding connections burns a server slot per request, hits load balancer idle timeouts (AWS ALB defaults to 60 seconds), and leaves the client unsure whether a timeout meant "failed" or "still running".

```text
client  POST /reports   Idempotency-Key: k1
server  202 Accepted    Location: /jobs/j_42    Retry-After: 2
        { "id": "j_42", "status": "queued" }
client  GET /jobs/j_42  -> 200 { "status": "running", "progress": 40 }
client  GET /jobs/j_42  -> 200 { "status": "succeeded", "result_url": "/reports/r_9" }
                           (or 303 See Other -> /reports/r_9)
```

In Node the job goes to BullMQ on Redis with a separate worker; in Python, Celery or arq. Workers are idempotent and retry with backoff; the job row stores attempts, last error and timestamps. Webhooks are signed (HMAC over timestamp plus body) and retried on non-2xx; receivers acknowledge fast and process asynchronously. SSE (`text/event-stream`) is the simplest browser push once proxy buffering is off.

**Follow-ups they will ask:**
- How do you stop clients polling too hard?: `Retry-After`, growing intervals, ETag plus 304 on the job, or push via SSE.
- What if the worker dies mid-job?: the queue's lock or visibility timeout expires, the job is picked up again, and the idempotent handler reruns safely.
- When is a synchronous 30 second call acceptable?: internal tooling with explicit timeouts, never on a user-facing path.

**Mistakes to avoid:**
- Raising every timeout in the chain to 60 seconds instead of changing the model.
- Fire-and-forget with no job record, so clients never discover failures.

### Q. What is HATEOAS and is it worth implementing?
**Short answer (45 seconds):** HATEOAS (Hypermedia As The Engine Of Application State) means responses include links to the actions available next, so a client navigates by following `rel` names instead of hardcoding URLs: an order carries a `cancel` link only while cancellation is allowed. It is level 3 of the Richardson model and the part of REST almost nobody implements fully. Worth it in a narrow form: `self` and related links plus state-dependent action links, which stops clients duplicating business rules.

**Deeper explanation:**

```json
{
  "id": "ord_42",
  "status": "paid",
  "_links": {
    "self":   { "href": "/orders/ord_42" },
    "items":  { "href": "/orders/ord_42/items" },
    "cancel": { "href": "/orders/ord_42/cancellation", "method": "POST" }
  }
}
```

Formats: HAL (`_links`), JSON:API (`links`), Siren (actions with fields). PayPal's REST API returns `links` arrays with `rel` and `method`; GitHub's returns `*_url` fields. The payoff is in the UI: the frontend renders a Cancel button if and only if the `cancel` link is present, so permission and state logic lives once, on the server, and a rule change needs no app release. The costs are larger payloads, clients that hardcode URLs anyway, and no mainstream codegen that discovers endpoints at runtime, which is why OpenAPI won for first-party clients.

**Follow-ups they will ask:**
- How does it help with versioning?: clients that follow links do not break when URLs move, only when `rel` names or payload shapes change.
- Difference from OpenAPI?: OpenAPI describes the API statically at build time; hypermedia describes what this resource allows right now.
- Would you add it to GraphQL?: no, the schema and client-side state handle discovery differently there.

**Mistakes to avoid:**
- Saying HATEOAS is required for REST without naming one concrete benefit.
- Shipping links no client reads; use them where they change client behaviour, such as state-dependent actions.

### Q. How do you design backward-compatible API changes?
**Short answer (45 seconds):** Only add, never take away or change meaning: new optional fields, new endpoints, new enum values clients are told to treat as unknown-but-valid, new optional parameters whose defaults preserve old behaviour. Never rename or remove a field, change a type, tighten validation on existing inputs, or change what a status code means. Clients follow the tolerant reader rule: ignore unknown fields, never fail on extra data. Enforce it with a schema diff in CI and contract tests.

**Deeper explanation:** Compatibility has two directions. Backward: new server, old clients keep working. Forward: old server, new clients degrade gracefully when a field is absent. Design for both up front: return objects rather than bare scalars so you can add siblings (`"price": {"amount": 10, "currency": "INR"}` instead of `"price": 10`), use string enums and document that new values will appear, and keep API field names decoupled from column names so a schema rename never leaks.

Semantics are the sneaky breaking change: an always-present field becoming nullable, a default sort changing, a 404 becoming a 403. Guard it mechanically: generate the OpenAPI spec from code (NestJS Swagger decorators; FastAPI does it natively), diff it against the last released spec with `oasdiff` and fail the build on breaking changes, and run consumer-driven contract tests (Pact) so the mobile team's expectations are executable. For protobuf, never reuse field numbers; mark removed ones `reserved`.

**Follow-ups they will ask:**
- Is adding a required request field compatible?: no, old clients will not send it; make it optional with a default, or it is a new version.
- How do you eventually remove a field?: deprecate it in docs and with a `Deprecation` header, log which API keys still use the endpoint, remove it in the next major version.

**Mistakes to avoid:**
- Treating "now nullable" as non-breaking; a client doing `user.address.city` now crashes.
- Relying on "we told them in Slack" instead of machine-checked contracts.

### Practice
- Take an endpoint that uses `?page=37` today and rewrite it as keyset pagination over `(created_at, id)`; run `EXPLAIN ANALYZE` on both at offset 100,000 and compare rows scanned.
- Build `POST /reports` returning 202 with a BullMQ job and a `GET /jobs/:id` poll endpoint; add an `Idempotency-Key` so a retried POST returns the same job.
- Generate the OpenAPI spec from code, commit it, add `oasdiff` to CI, then rename a field and watch the build fail.
- Say it out loud: in two minutes, explain to a mobile developer why you are moving from `/v1` to date-based header versioning and exactly what they must change.

## Database Design

> Schema questions are where interviewers find out whether you have lived with a design for two years or only drawn it on a whiteboard. Weak answers recite normal forms and say "MongoDB scales". Strong answers talk about the query patterns the schema was built for, the N+1 that showed up in the ORM logs, the migration that locked a table in the middle of the afternoon, and the point where one Postgres primary stopped being enough and what you tried before sharding. Expect the constraint to change mid-answer: "now reads are 100 times writes", "now there are 40 tenants in one table".

### Concepts you must understand
- Normalisation stores each fact once so it is updated once; 1NF is atomic values, 2NF removes partial dependencies on a composite key, 3NF removes transitive dependencies between non-key columns.
- Denormalisation is a deliberate copy of data to make a read cheap; it trades write complexity and drift risk for read speed, and the copy must be rebuildable from the normalised source.
- N+1 is one query for a list plus one query per item, usually from lazy loading; the fix is batching (JOIN, IN, DataLoader) and the detection is query logs and `pg_stat_statements` call counts.
- SQL versus NoSQL is about access patterns, consistency needs and team skills, not about scale; Postgres JSONB covers many "NoSQL" cases and MongoDB has had multi-document transactions for years.
- Sharding splits one logical dataset across nodes by a shard key; the key decides hotspot risk and which queries become scatter-gather, and resharding later is the expensive part.
- Zero-downtime schema changes follow expand, migrate, contract, and every DDL statement must be checked for the lock it takes and how long it holds it.
- Postgres connections are processes; pools keep a small number warm, and the total across all app instances must fit under `max_connections`.
- Foreign keys are integrity the database enforces for you; they cost an index lookup per child write and a lock on the parent row, and they do not cross shard or service boundaries.
- Indexes, constraints and migrations are code: reviewed, tested against production-sized data, and reversible.

### Q. What is database normalisation? What are 1NF, 2NF, 3NF?
**Short answer (45 seconds):** Normalisation organises tables so each fact lives in one place, which removes update anomalies (change a customer's city in one row and forget the other forty). 1NF: every column holds one atomic value and rows are unique, so no comma-separated lists or repeating column groups. 2NF: 1NF plus every non-key column depends on the whole primary key, not part of a composite key. 3NF: 2NF plus non-key columns depend only on the key, not on another non-key column.

**Deeper explanation:** One flat table, fixed step by step:

```text
orders_flat(order_id, product_ids "p1,p2", customer_id, customer_city)
  1NF violation: product_ids is a list
  -> order_items(order_id, product_id, qty, product_name)   key (order_id, product_id)
order_items: product_name depends on product_id alone, half the key
  2NF violation (partial dependency)
  -> products(product_id, product_name); order_items keeps qty
orders(order_id, customer_id, customer_city)
  customer_city depends on customer_id, not on the order
  3NF violation (transitive dependency)
  -> customers(customer_id, city); orders keeps customer_id
```

Each step removes a place where the same fact could disagree with itself. BCNF is a stricter 3NF for tables with overlapping candidate keys. The price is joins: an order with product names and the customer's city is now a three-table join, fine with indexes on the FK columns. Document stores invert the default: embed what you read together (an order with its items) and accept duplicated product names, which is sometimes correct, since the name at purchase time should not change later.

**Follow-ups they will ask:**
- Is a JSONB column a 1NF violation?: technically yes; fine when the blob is read and written as a unit and never joined on by its parts.
- Name an anomaly denormalised data causes: update anomaly, one customer with two cities after a partial update; delete anomaly, deleting the last order deletes the customer.

**Mistakes to avoid:**
- Reciting definitions without pointing at the dependency in a concrete table.
- "Always 3NF" or "always denormalise for speed"; it depends on the read to write ratio.

### Q. When would you denormalise a database and what are the trade-offs?
**Short answer (45 seconds):** Denormalise when a hot read path pays for a join or aggregate on every request and keeping a copy in sync is cheaper: a `comment_count` on posts, the customer's name stored on the invoice, a flattened reporting table, or order items embedded in a MongoDB order document. The trade-offs are write amplification, drift between copies, and more storage. Keep a normalised source of truth and treat the copy as derived data you can rebuild.

**Deeper explanation:** Ways to keep the copy in sync, in increasing order of decoupling: update both in one transaction (`UPDATE posts SET comment_count = comment_count + 1` alongside the insert), a trigger, a materialized view (`REFRESH MATERIALIZED VIEW CONCURRENTLY` needs a unique index and recomputes everything), or an async job fed by change data capture (Debezium reading the WAL into Kafka). Counters are the classic case: `SELECT count(*)` over two million comments per page view is a scan per request; a maintained counter is one indexed row.

In MongoDB the decision is embed versus reference. Embed when the child is always read with the parent, is bounded in size (the 16 MB document limit is real, and unbounded arrays make every update rewrite the document) and is owned by the parent. Reference when the child is shared, large or queried on its own. Some duplication is semantically right: an invoice must keep the address as it was when billed.

**Follow-ups they will ask:**
- How do you detect drift?: a reconciliation job that recomputes a sample and alerts on mismatch, plus a rebuild command you have actually run.
- When would you avoid a counter column?: very high write rates on one row cause lock contention; move it to Redis `INCR` and flush periodically.

**Mistakes to avoid:**
- Denormalising first and normalising later; the reverse is far cheaper.
- Forgetting that duplicated data needs an owner, a sync mechanism and a rebuild path.

### Q. What is the N+1 query problem? How do you detect and fix it?
**Short answer (45 seconds):** N+1 is one query to fetch N parents and then one query per parent for a relation, so a page of 50 orders issues 51 queries. It hides in code because the ORM lazy loads `order.customer` on access. Detect it from query logs, APM traces showing 50 identical spans, or `pg_stat_statements` where one normalised query has a huge `calls` count. Fix it by loading the relation in bulk: a JOIN, one `WHERE id IN (...)`, or a batching layer such as DataLoader.

**Deeper explanation:**

```ts
// N+1: one query per order
const orders = await prisma.order.findMany({ take: 50 });
for (const o of orders) {
  await prisma.customer.findUnique({ where: { id: o.customerId } });
}
// fixed: one batched IN query for the relation
const withCustomer = await prisma.order.findMany({
  take: 50,
  include: { customer: true },   // or select: { customer: { select: { name: true } } }
});
```

Prisma's `include` issues one batched `IN` query per relation rather than one per parent, and `select` also trims columns. Equivalents: Mongoose `populate` (a second query with `$in`), Django `select_related` (JOIN) and `prefetch_related` (IN), SQLAlchemy `selectinload` or `joinedload`. In GraphQL every resolver runs per field, so N+1 is the default; DataLoader collects all `customerLoader.load(id)` calls in one tick and fires one batched fetch. Turn on `log: ['query']` in Prisma or `mongoose.set('debug', true)` in development, assert query counts in tests, and watch `pg_stat_statements` ordered by `calls` in production.

**Follow-ups they will ask:**
- JOIN or IN?: JOIN for one-to-one or small one-to-many; two queries with IN when the join would multiply rows or the relation is large.
- Is the fix always better?: an `IN` with 10,000 ids or a row-exploding JOIN can be worse; paginate the parents first.

**Mistakes to avoid:**
- Only describing the problem; interviewers want detection and the specific ORM fix.
- Eager loading everything everywhere, which turns N+1 into one giant query fetching columns nobody needs.

### Q. When would you choose SQL over NoSQL and vice versa?
**Short answer (45 seconds):** Start from access patterns and consistency needs, not from scale. Relational (Postgres) when you have many related entities, need ad hoc queries and reporting, need multi-row transactions and constraints, or do not yet know all the access patterns. Document or key-value when the data is an aggregate read and written as a unit, the schema varies per record, access patterns are few and known, or you need horizontal write scale beyond one primary.

**Deeper explanation:**

| Question | Points to SQL | Points to NoSQL |
|---|---|---|
| Queries join 3+ entities or change often? | yes | no, fixed lookups by key |
| Atomic multi-row updates and FKs? | yes | per-document atomicity is enough |
| Schema per record | uniform | variable, sparse |
| Scale | one primary, replicas, partitioning | horizontal writes from day one |

The lines are blurry on purpose. Postgres `JSONB` with GIN indexes handles semi-structured attributes inside a relational model. MongoDB has had multi-document transactions since 4.0 and schema validation, so "no transactions" is an outdated argument. What actually differs: joins (`$lookup` exists but is not what Mongo is built for), planner maturity for ad hoc analytics, and operational scaling (Mongo shards natively; Postgres needs Citus or application-level sharding). Weigh team experience too: a managed Postgres you know beats a database you learn during an incident.

**Follow-ups they will ask:**
- Can Postgres replace MongoDB for documents?: often, with JSONB, until documents are large, deeply nested and updated in place constantly.
- Embeddings and chat history for an AI product?: Postgres with `pgvector` while the index fits one node and metadata is relational; a dedicated vector store when it does not.

**Mistakes to avoid:**
- "NoSQL because it scales"; most products never outgrow one well-indexed Postgres primary with read replicas.
- Picking a store because of a tutorial rather than a query you can name.

### Q. What is database sharding? What problems does it introduce?
**Short answer (45 seconds):** Sharding is horizontal partitioning: one logical table is split across many database nodes by a shard key, so each node holds a slice of the rows and of the write load. You do it when a single primary cannot take the writes or hold the data even after vertical scaling, read replicas, partitioning and caching. It introduces cross-shard queries and transactions, hotspots from a bad key, global uniqueness problems, and resharding pain when you add nodes.

**Deeper explanation:** The shard key decides everything. Hash sharding (`hash(user_id) mod N`) spreads writes evenly but turns range queries into scatter-gather. Range sharding keeps ranges together, but a monotonically increasing key such as a timestamp sends every new write to the last shard. Skew is the other hotspot: one whale tenant whose rows all land on one shard, so multi-tenant systems often give the largest tenants their own shard.

Cross-shard costs: a JOIN between users and orders only works if both are sharded by the same key (co-location); otherwise the application scatters the query and merges, and `COUNT`, `ORDER BY ... LIMIT` and uniqueness checks become distributed operations. Transactions across shards need two-phase commit or sagas. Resharding with `mod N` moves almost every row when N changes, so use consistent hashing or many virtual shards mapped onto a few physical nodes and migrate them one at a time; MongoDB splits data into chunks that its balancer migrates between shards.

**Follow-ups they will ask:**
- How do you choose a shard key?: the field most queries filter on, with high cardinality, even distribution, and known at write time; usually `tenant_id` or `user_id`.
- Citus, Vitess or application sharding?: use a layer (Citus for Postgres, Vitess for MySQL) when you can; application sharding means you own routing, migrations and rebalancing.

**Mistakes to avoid:**
- Proposing sharding before mentioning replicas, partitioning and caching.
- Picking `created_at` or an auto-increment id as a range shard key.

### Q. How do you run a database migration with zero downtime?
**Short answer (45 seconds):** Expand and contract: add the new structure beside the old, deploy code that writes both and reads the old, backfill in batches, switch reads to the new, stop writing the old, and drop it a release later. Every step is compatible with the code version before and after it, so a rollback never needs a reverse migration.

**Deeper explanation:** Renaming `users.name` to `full_name`:

```sql
ALTER TABLE users ADD COLUMN full_name text;             -- 1 expand, metadata only
-- 2 deploy: write both, read name
UPDATE users SET full_name = name                        -- 3 backfill in PK-range batches
WHERE id BETWEEN $1 AND $2 AND full_name IS NULL;
ALTER TABLE users ADD CONSTRAINT full_name_nn
  CHECK (full_name IS NOT NULL) NOT VALID;               -- 4 no long lock
ALTER TABLE users VALIDATE CONSTRAINT full_name_nn;      --   scans without blocking writes
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;   --   PG 12+: no scan
-- 5 deploy: read full_name only
ALTER TABLE users DROP COLUMN name;                      -- 6 contract, next release
```

Pitfalls: `ADD COLUMN ... NOT NULL` without a default fails on a populated table, and a bare `SET NOT NULL` scans the table under an `ACCESS EXCLUSIVE` lock. Plain `CREATE INDEX` blocks writes; use `CREATE INDEX CONCURRENTLY` (a failure leaves an `INVALID` index to drop and retry). Set `lock_timeout` to a couple of seconds and retry, so waiting DDL does not block every other query. Old pods still `SELECT *`, so contract waits a release.

**Follow-ups they will ask:**
- Why batch the backfill?: one giant UPDATE holds row locks for its duration, bloats WAL, and stalls replicas.
- How do you roll back?: redeploy the previous code; each schema step works with both versions, so no down migration runs.

**Mistakes to avoid:**
- Running `ALTER TABLE` from the deploy pipeline without knowing its lock, on a table with live traffic.
- Dropping the old column in the same release that stops writing it.

### Q. What is connection pooling and what happens without it?
**Short answer (45 seconds):** A pool keeps a fixed set of open database connections and lends one to a request for the duration of a query or transaction, then takes it back. Without it, every request pays TCP, TLS and auth handshakes, and in Postgres each connection is a server process with its own memory, so a traffic spike becomes thousands of processes, `FATAL: sorry, too many clients already`, and CPU spent context switching instead of running queries.

**Deeper explanation:** Node's `pg` Pool defaults to 10 connections per process; the MongoDB driver defaults to 100. The number that matters is the total: 20 API pods times a pool of 10 is 200 connections, and Postgres `max_connections` defaults to 100. Oversizing does not help either: past a small number of active connections, throughput falls as they contend for cores and disks. Start with a pool on the order of the database's core count, measure, and set `connectionTimeoutMillis` so requests fail fast instead of queueing forever.

When you cannot keep the total small (many pods, or serverless functions that each open their own connections), put PgBouncer or a managed equivalent (RDS Proxy, Supavisor) in front. In transaction pooling mode PgBouncer multiplexes thousands of client connections over a few dozen server connections, at the cost of session features: `SET` session variables, session-level advisory locks, `LISTEN/NOTIFY`, and named prepared statements (supported in newer releases).

**Follow-ups they will ask:**
- Pools and transactions?: every statement of a transaction must run on the same checked-out client (`pool.connect()` then `client.query`), released in `finally`.
- Why do serverless functions break connection limits?: each concurrent invocation has its own pool, so concurrency 500 means 500 pools; use a proxy or an HTTP data API.

**Mistakes to avoid:**
- "Bigger pool means more throughput"; past the database's capacity it means more contention and lock waits.
- Leaking clients by skipping `release()` on an error path, which drains the pool and hangs the service.

### Q. What is a foreign key constraint and when would you skip it?
**Short answer (45 seconds):** A foreign key makes the database refuse a child row pointing at a missing parent and defines what happens when the parent goes away (`RESTRICT`, `CASCADE`, `SET NULL`). Keep them by default in OLTP schemas; skip them when the reference crosses a database or service boundary, in analytics and bulk-load tables, on extremely write-hot tables, and when deletion semantics (soft deletes, archival) do not match a cascade.

**Deeper explanation:** The costs are concrete. On every insert or update of the child's FK column, Postgres looks up the parent's primary key and takes a `FOR KEY SHARE` lock on the parent row. On delete of a parent, Postgres must find child rows, and it does not automatically index FK columns (MySQL InnoDB does); without an index on `orders.customer_id`, deleting a customer scans orders while holding locks. `ON DELETE CASCADE` on a parent with millions of children is one long transaction with a huge lock footprint; many teams use `RESTRICT` and delete children in batches.

Reasons to skip: microservices, where orders live in one database and users in another, so the reference is just an id and consistency comes from events and reconciliation; sharded tables, where parent and child may sit on different nodes; and MongoDB, which has no FK constraints, so integrity is application code. When you skip them, write down what replaces them: API validation, orphan-detection jobs, idempotent cleanup.

**Follow-ups they will ask:**
- How do you add an FK to a large live table?: `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT`, to avoid a long blocking scan.
- Soft deletes and FKs?: the constraint still holds, so children of a soft-deleted parent stay valid; filter in queries and decide explicitly whether to cascade the flag.

**Mistakes to avoid:**
- "FKs are slow, drop them" without naming the cost or what replaces the integrity check.
- Forgetting the index on the FK column and blaming the constraint for slow deletes.

### Practice
- Take one wide table from a project, normalise it to 3NF on paper, then write the three-table query for its main screen and the index each join needs.
- Turn on Prisma query logging (or `mongoose.set('debug', true)`) for a list endpoint, count the queries, fix the N+1 with `include` or DataLoader, and add a test that asserts the count.
- Rename a column on a one million row table in local Postgres with expand and contract; watch `pg_locks` from a second session at each step, and try `CREATE INDEX` with and without `CONCURRENTLY`.
- Say it out loud: explain to a product manager why the migration takes three deploys instead of one and what would happen if you did it in one.

## Production Debugging

> Scenario questions here test method under pressure. The interviewer does not have a single right answer either; they are watching whether you observe before you guess, change one thing at a time, say "mitigate first, understand later" when users are hurting, and close the loop with prevention. Weak answers jump to "probably the database" or list tools. Strong answers narrate a runbook: which dashboard you open first, what you expect to see, how you confirm or kill each hypothesis, and what you ship afterwards so the same page never fires again.

### Concepts you must understand
- The order is observe, hypothesise, test, fix, prevent; the most common failure is skipping observe and fixing a hunch.
- "What changed?" is the first question: deploys, config and feature flags, traffic shape, data volume crossing a threshold, dependencies, infrastructure events, scheduled jobs.
- Metrics are cheap aggregates for alerting and trends, logs are discrete events for detail, traces show the causal path of one request across services; a request id or trace id ties the three together.
- Latency is read at percentiles per endpoint and per instance, never as an average; a doubled p99 on one pod is a different problem from a doubled p50 everywhere.
- Database CPU saturation is almost always a query plan, a missing index, a connection storm or vacuum debt, and `pg_stat_activity` plus `pg_stat_statements` show which within minutes.
- Node.js memory leaks are found by comparing heap snapshots over time, not by reading code; RSS, heap and external memory tell different stories.
- Rare errors are a slicing problem: find the dimension (pod, version, tenant, input shape, time) where the 1% becomes 100%.
- Race conditions are debugged by logging ordering and asserting invariants, and fixed with atomic operations and constraints that make the race impossible rather than unlikely.
- During the incident, mitigation beats diagnosis (roll back, scale, shed load); the blameless post-mortem with owned action items is where the real fix happens.

### Q. Your API response times doubled overnight. Walk me through debugging this.
**Short answer (45 seconds):** First confirm and scope: which percentiles, endpoints, instances or regions, and since exactly when. Then ask what changed overnight: a deploy, a config or flag change, traffic shape, a dependency, an infrastructure event, or a scheduled job. Form two or three ranked hypotheses, test each with one piece of evidence, mitigate as soon as you can (roll back, scale, disable a feature), then find the root cause.

**Deeper explanation:** The runbook I would narrate:

```text
observe   p50/p95/p99 by endpoint, pod, region; error rate; RPS; exact start time
          everything slow (shared dependency) or one route (its code or query)?
changed?  deploys, flags, infra events, cron jobs, traffic shape, data growth
app       event loop lag (perf_hooks.monitorEventLoopDelay), GC time, CPU throttling, pool waits
db        pg_stat_statements top by total_exec_time, pg_stat_activity waits, plan change
cache     hit ratio drop, Redis evictions, keys expiring together
deps      third-party p99, DNS, TLS handshakes (keep-alive off?)
```

"Overnight with no deploy" points at time-based causes: a nightly job still running, a cache that expired all at once, or a table that grew past the point where the planner switched to a sequential scan. Prove it: `EXPLAIN (ANALYZE, BUFFERS)` on the top query against its previous plan, or `ANALYZE` the table and watch latency. Mitigate first: roll back, stop the batch job, scale out, add the index `CONCURRENTLY`. Prevent: p99 alerts per endpoint and nightly jobs on a replica.

**Follow-ups they will ask:**
- Nothing was deployed, now what?: the data or the environment changed; check table growth, autovacuum, the dependency's status page and the cloud provider's event log.
- App or database?: compare DB span time in traces with total request time; if the DB share did not grow, it is the app or a dependency.

**Mistakes to avoid:**
- Jumping to "add more pods" or "it must be the database" before scoping which requests slowed.
- Changing three things at once, so you never learn what fixed it.

### Q. Your database CPU is at 100%. What are the first 5 things you check?
**Short answer (45 seconds):** In order: what is running right now (`pg_stat_activity`: active queries, their age, wait events); which queries ate CPU recently (`pg_stat_statements` by total time, and by calls to catch a tight loop); the connection count and whether it spiked, since each Postgres connection is a process; whether a plan flipped to sequential scans (`pg_stat_user_tables` seq_scan climbing, stale statistics, missing index); and what changed (deploy, data growth, a batch job).

**Deeper explanation:**

```sql
-- 1 who is running what, for how long
SELECT pid, now() - query_start AS age, state, wait_event_type, left(query, 80)
FROM pg_stat_activity WHERE state <> 'idle' ORDER BY age DESC;
-- 2 top CPU burners (pg_stat_statements enabled)
SELECT calls, round(total_exec_time) AS total_ms, round(mean_exec_time) AS mean_ms, left(query, 80)
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;
```

Then act. A runaway query: `pg_cancel_backend(pid)`, escalating to `pg_terminate_backend`. A hot query with a bad plan: `EXPLAIN (ANALYZE, BUFFERS)`, then `ANALYZE` the table or add an index `CONCURRENTLY`. A connection storm (hundreds of `active` or `idle in transaction`): cap pools, add PgBouncer, set `statement_timeout` and `idle_in_transaction_session_timeout`. A cheap query with an enormous `calls` count is an N+1 or a retry storm; fix the app or rate limit. MongoDB equivalents: `db.currentOp()`, the profiler with `slowms`, `explain("executionStats")` showing `COLLSCAN`.

**Follow-ups they will ask:**
- CPU at 100% but queries look fine?: autovacuum on a bloated table, a checkpoint storm, or far too many processes context switching; check the process count and `pg_stat_progress_vacuum`.
- How do you stop it recurring?: `statement_timeout` per role, `EXPLAIN` review for new queries, alerts on `pg_stat_statements` deltas.

**Mistakes to avoid:**
- Restarting the database; the same query comes straight back and the evidence is gone.
- Scaling the instance first; a sequential scan over a large table saturates the bigger box too.

### Q. How do you find a memory leak in a production Node.js service?
**Short answer (45 seconds):** Confirm it is a leak, not a high plateau: graph `process.memoryUsage()` per pod over hours; a leak climbs through traffic cycles until the container is OOM-killed. Then capture heap snapshots from one instance at two or three points in time, use the DevTools comparison view to find what grew, and follow the retainer chain to the code holding it. Usual culprits: module-level Maps without eviction, listeners added per request, timers never cleared.

**Deeper explanation:**

```bash
node --heapsnapshot-signal=SIGUSR2 server.js   # then: kill -USR2 PID writes a .heapsnapshot
node --inspect server.js                       # or attach Chrome DevTools, Memory tab
npx clinic doctor -- node server.js            # local: event loop, GC and memory diagnosis
npx clinic heapprofiler -- node server.js      # local: who allocates
```

Snapshot a canary pod pulled out of the load balancer, because the snapshot pauses the process and can briefly double its memory; `require('v8').writeHeapSnapshot()` works from code too. In DevTools sort the comparison by size delta: thousands of `Promise`, `(closure)`, `Array` or your own class names point at the culprit, and the retainers panel shows who holds them. `external` and `arrayBuffers` growing while `heapUsed` stays flat means Buffers are retained, not JS objects. Node-specific leaks: `EventEmitter` listeners added inside handlers (`MaxListenersExceededWarning` is the early signal), `setInterval` without `clearInterval`. Prevent: alert on memory slope, a bounded `lru-cache` instead of a `Map`, and `--max-old-space-size` below the container limit.

**Follow-ups they will ask:**
- Why does rss stay high after heapUsed drops?: V8 does not return freed heap to the OS immediately; flat rss is not a leak.
- Is a growing heap always a leak?: no; a cache filling to its bound or a warm-up plateau is normal, which is why you watch the slope across cycles.

**Mistakes to avoid:**
- Restarting pods on a schedule and calling it fixed.
- Reading code looking for the leak instead of letting a snapshot diff point at the retained objects.

### Q. What is distributed tracing and how does it help debug microservices?
**Short answer (45 seconds):** Distributed tracing records one request as a tree of spans across every service it touched: each span is a named, timed operation with attributes, and all spans share a trace id propagated in headers from hop to hop. When checkout is slow, the trace shows that 1.2 of 1.4 seconds went to the inventory service. OpenTelemetry is the standard SDK and wire format; Jaeger, Tempo or Honeycomb store and visualise traces.

**Deeper explanation:** Propagation uses the W3C Trace Context header:

```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             version, trace-id (16 bytes hex), parent span id, flags (01 = sampled)
tracestate:  vendor-specific key=value pairs
```

Each service reads `traceparent`, starts a child span, and injects a new `traceparent` into outgoing HTTP calls, Kafka headers or BullMQ job data. Inside a Node process the active span follows async work through `AsyncLocalStorage`; in Python it rides on `contextvars`. `@opentelemetry/auto-instrumentations-node` wraps http, express, pg, mongodb and ioredis without code changes, and you add manual spans around business steps with `tracer.startActiveSpan('price.calculate', ...)`. Sampling controls cost: head-based sampling decides at the root (keep 10%), tail-based sampling in the OpenTelemetry Collector keeps every trace that errored or exceeded a latency threshold. Put the trace id into every log line so you can jump from a log to its trace.

**Follow-ups they will ask:**
- How does context cross a queue?: inject `traceparent` into message headers at produce time and extract at consume time, usually as a span link rather than a parent because the consumer runs much later.
- What does tracing find that logs cannot?: fan-out and sequencing (30 sequential calls that should be parallel), time waiting in queues, and which hop added latency.

**Mistakes to avoid:**
- Describing tracing as "logs with a request id"; the span tree and its timing are the point.
- Sampling 1% uniformly and then having no trace for the error you are debugging.

### Q. What is the difference between a metric, a log, and a trace?
**Short answer (45 seconds):** A metric is a number aggregated over time, cheap to store and ideal for alerting and dashboards, but the individual event is gone. A log is a record of one event with arbitrary detail, expensive at volume, and answers "what exactly happened to request abc". A trace is a set of causally linked spans for one request across services and answers "where did the time go". Correlate them with a trace id in the logs and exemplars that link a histogram bucket to a sample trace.

**Deeper explanation:**

| | Metric | Log | Trace |
|---|---|---|---|
| Unit | time series | one event | span tree per request |
| Cost driver | label cardinality | volume | spans and sampling rate |
| Best question | is it broken, since when | why did this one fail | which hop is slow |

Cardinality is the metric trap: a label such as `user_id` turns one series into millions and takes the metrics store down; that detail belongs in logs and traces. Logs should be structured JSON (pino in Node, structlog in Python) with `request_id` and `trace_id`. A strong pattern is the canonical log line: one wide event per request holding everything, which answers most questions with one query. Alert on metrics (RED: rate, errors, duration), debug with traces, read logs last.

**Follow-ups they will ask:**
- Histogram or summary for latency?: histograms, because percentiles can be aggregated across pods and you choose the buckets; summaries compute quantiles per instance and cannot be merged.
- Where do SLOs fit?: an SLO is a target on a metric; burn-rate alerts page you when the error budget is being spent too fast.

**Mistakes to avoid:**
- Treating them as interchangeable "three pillars" you buy once; each answers a different question with a different cost model.
- Putting unbounded labels on metrics.

### Q. Your error rate is 1% but you can't reproduce the error. How do you debug it?
**Short answer (45 seconds):** A 1% error you cannot reproduce is not random; it is 100% for some slice you have not found yet. Start from the failing requests: pull their request ids, trace ids and structured logs, then group by every dimension you have (pod, deploy version, region, client version, tenant, payload shape, time of day). Bursty points to infrastructure (restarts, connection resets, a dependency); steady points to input (one locale, one tenant). Once you find the slice, replay those inputs in staging and write the regression test.

**Deeper explanation:** Make the errors debuggable first: every error carries a stack and its `cause` (`new Error('charge failed', { cause: err })`), and log lines carry request id, route, tenant and a sanitised input. Tail-based sampling or an error tracker such as Sentry keeps every failing request's trace even when successes are sampled at 1%.

Then slice. Errors on one pod: a bad node or config drift. Errors on one replica: replication lag breaking read-your-own-writes. Errors on a rhythm: a keep-alive mismatch, where the Node server's `keepAliveTimeout` (default 5 seconds) is shorter than the load balancer's idle timeout, so the balancer reuses a socket the server is closing and clients see intermittent 502s or `ECONNRESET`; the fix is a server timeout longer than the balancer's. If nothing correlates, add targeted debug logging behind a feature flag. Prevent: an error-rate dashboard broken down by those dimensions.

**Follow-ups they will ask:**
- How do you reproduce a timing-dependent failure?: slow the dependency in staging with a proxy such as Toxiproxy, or hit the suspect call with concurrent identical requests.
- Is 1% worth chasing?: at a million requests a day that is 10,000 failures; the SLO decides the urgency, not the percentage.

**Mistakes to avoid:**
- A blanket retry or try/catch that hides it.
- Searching the code for the bug before looking at the failing requests' actual attributes.

### Q. How do you debug a race condition that only happens in production?
**Short answer (45 seconds):** Production has what a laptop does not: many instances, real concurrency on one key, and latency that widens the window between a check and a write. Start from the violated invariant (a negative balance, a duplicate booking), find the shared state and the check-then-act window, then log ordering: monotonic timestamps, instance id, request id, value read and value written. Reproduce by widening the window; fix by making the operation atomic in the data store.

**Deeper explanation:**

```ts
// racy: both requests read available = 1, both pass, both write 0
const s = await db.seat.findUnique({ where: { id } });
if (s.available > 0) await db.seat.update({ where: { id }, data: { available: s.available - 1 } });
// atomic: the database checks and writes together
const n = await db.$executeRaw`UPDATE seats SET available = available - 1 WHERE id = ${id} AND available > 0`;
if (n === 0) throw new SoldOutError();
```

Debugging steps: add an invariant check that logs loudly; log every read and write of the shared state with `request_id`, `instance_id` and `process.hrtime.bigint()`, sort by time and read the interleaving. Reproduce in staging with `Promise.all` of 50 calls on one key and an `await sleep(200)` between read and write. Node's single thread does not protect you: every `await` lets another request run, and other pods run in parallel. Fixes: conditional `UPDATE`, unique constraint plus `ON CONFLICT`, optimistic version column, `SELECT ... FOR UPDATE`.

**Follow-ups they will ask:**
- Why not a mutex in the Node process?: it serialises one process only; with two pods the race is back, so the lock must live in the shared store.
- Optimistic or pessimistic?: optimistic (version column, retry on zero rows) for low contention; `FOR UPDATE` for hot rows.

**Mistakes to avoid:**
- "Add a lock" without saying where it lives and what happens when the holder dies.
- Fixing the symptom with a cleanup job instead of closing the window.

### Q. What should a good post-mortem contain?
**Short answer (45 seconds):** A good post-mortem is blameless and specific: impact in numbers (duration, requests failed, SLO budget burned), a timestamped timeline from trigger through detection, mitigation and resolution, the root cause and the contributing factors that let it reach production, what went well and where you were lucky, and action items with an owner, a priority and a due date. "Human error" is never the root cause; ask why the system let one mistake become an outage.

**Deeper explanation:**

```text
Summary        what broke, for whom, how long
Impact         duration, % requests failed, tenants affected, SLO budget burned
Timeline (UTC) 14:02 deploy; 14:09 p99 alert; 14:15 paged; 14:31 rollback; 14:36 recovered
               time to detect 7 min, time to mitigate 29 min
Root cause     migration set NOT NULL on a 40M row table under ACCESS EXCLUSIVE lock
Contributing   no lock_timeout, migration ran inside the deploy, alert threshold too high
Went well / went poorly / got lucky
Action items   [owner] [P1] CI check for unsafe DDL, due date, ticket
```

Blameless means the document treats each decision as reasonable given what people knew at the time, then asks what would have made the right action obvious or the wrong one impossible. Action items should mix prevention (make the failure class impossible), detection (alert sooner) and mitigation (recover faster). Review within a week, publish widely, and track the actions to completion; an unactioned post-mortem is just a story.

**Follow-ups they will ask:**
- What if someone really did type the wrong command?: ask why that was possible in production without a guard, a review or a dry run, and fix the system.
- How do you stop action items rotting?: ticket each one, review open items in a recurring meeting, report the completion rate.

**Mistakes to avoid:**
- A timeline without timestamps or a detection time, so nothing can be measured.
- Action items without owners, which is a wish list.

### Practice
- Run a local Node service with `--inspect`, add a deliberate leak (a module-level array that grows per request), load it with `autocannon`, take three heap snapshots and find the array in the comparison view.
- Instrument an Express or NestJS app with `@opentelemetry/auto-instrumentations-node`, export to a local Jaeger container, and find the slowest span in a request that touches Postgres and Redis.
- Write the racy seat-booking handler, fire 50 concurrent requests with `Promise.all`, observe the negative count, then fix it with a conditional `UPDATE` and rerun.
- Say it out loud: pick one production problem you handled and narrate it in three minutes as observe, hypothesise, test, fix, prevent, ending with the post-mortem action items.
