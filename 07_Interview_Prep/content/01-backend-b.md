# Backend Engineering (part 2)

> Continues the backend track.

## Idempotency

> Interviewers use idempotency to find out whether you have shipped something that money or messages depended on. A weak answer defines the word and says "use a unique key". A strong answer walks the whole lifecycle: where the key comes from, how it is stored, what a second request sees while the first is still running, what happens when the server dies after committing but before replying, and how the same idea carries into queue consumers. Expect the interviewer to keep adding failure cases; the goal is to show that you treat retries as normal traffic, not as an edge case.

### Concepts you must understand
- An operation is idempotent when doing it once or N times leaves the system in the same end state; the response may differ, but good APIs also replay the stored response.
- Retries are unavoidable: client timeouts, load balancer retries, mobile networks, queue redelivery. Without idempotency every retry is a potential duplicate side effect.
- By the HTTP spec, GET, HEAD, OPTIONS, TRACE, PUT and DELETE are idempotent; POST and PATCH are not. Safe is a stronger property (GET and HEAD must not change state).
- The Idempotency-Key pattern: the client generates a UUID per logical attempt, the server stores key, request fingerprint and response, and replays on a repeat.
- Keys are scoped per account and per endpoint, never globally, so tenants cannot collide or block each other.
- Two requests with the same key at the same instant must not both execute: insert the key first under a unique constraint, and the loser gets 409 while the winner is in progress.
- The key row and the business effect must commit in the same transaction, otherwise a crash between them creates a duplicate or a false success.
- At-least-once delivery plus an idempotent consumer is how "effectively once" processing is built; exactly-once delivery across a network does not exist.
- Natural idempotency (set status to paid, versioned conditional updates, upserts on a natural key) is cheaper than a key table; use it when the domain allows.
- The transactional outbox on the producer side and a dedup (inbox) table on the consumer side carry idempotency across service boundaries.

### Q. What is idempotency? Why does it matter for APIs?

**Short answer (45 seconds):** An operation is idempotent when performing it once or many times leaves the system in the same end state. It matters for APIs because clients and intermediaries retry: a mobile client times out after the server has already committed, a load balancer retries a reset connection, a queue redelivers. If the operation is not idempotent, every retry risks a duplicate charge, order or email. Idempotency is what makes retries safe, and safe retries are the foundation of a reliable system.

**Deeper explanation:** The failure is mundane. A client sends POST /payments, the server charges the card and commits, and the response is lost on the way back. The client cannot tell "never processed" from "processed, reply lost", so the only sane move is to retry. The server must recognise the retry as the same logical attempt and return the original outcome instead of charging again.

```text
client --POST /payments (key K)--> server: charge, commit, reply lost
client --POST /payments (key K)--> server: finds K, replays stored 201
```

Idempotency is a property of the server-side effect, not of the response body. DELETE /orders/42 returning 204 the first time and 404 the second time is still idempotent because the state (order gone) is identical. For money and messaging you also store and replay the original response, so the client sees one consistent answer.

**Follow-ups they will ask:**
- Is a GET that bumps a view counter idempotent?: No, and it also violates "safe"; counters belong in POST handlers or analytics events.
- Does idempotency require the response to be identical?: No, the state must be identical; replaying the stored response is an extra guarantee for clients.
- Who generates the key, client or server?: The client, because only it knows that two requests are the same attempt.

**Mistakes to avoid:**
- Saying "we just avoid retries": networks and proxies retry whether you want them to or not.
- Treating it as a database uniqueness problem only: the real risk is external side effects (charges, emails, webhooks) that cannot be rolled back.

### Q. Which HTTP methods are idempotent by spec? Which aren't?

**Short answer (45 seconds):** The HTTP spec defines GET, HEAD, OPTIONS, TRACE, PUT and DELETE as idempotent. POST is not idempotent, and PATCH is not defined as idempotent either, although a particular PATCH format can be. There is also a stronger property called "safe": GET, HEAD, OPTIONS and TRACE must not change server state at all. Clients and proxies are allowed to automatically retry idempotent methods, which is why the classification matters in practice.

**Deeper explanation:** PUT is idempotent because it is a full replacement: sending the same representation twice leaves the same resource. DELETE is idempotent because the resource is gone either way, even if the second call returns 404. POST means "process this", which usually creates a new resource or triggers an action, so two POSTs are two actions. PATCH describes a change; "set price to 10" is idempotent, "increment price by 10" is not, and the spec cannot know which one you sent.

| Method | Idempotent | Safe |
| --- | --- | --- |
| GET, HEAD, OPTIONS, TRACE | yes | yes |
| PUT, DELETE | yes | no |
| POST, PATCH | no | no |

The spec describes intent, not your implementation. A PUT handler that appends to an audit log on every call, or a GET that increments a counter, breaks the contract, and the consequences are real: browsers, HTTP libraries and proxies retry idempotent requests on connection failure without asking.

**Follow-ups they will ask:**
- Why not use PUT /payments/{clientGeneratedId} instead of POST plus a key?: You can, and it is clean, but it leaks resource identity to the client and does not handle "same id, different body" without extra checks.
- Can PATCH be idempotent?: Yes, if the patch document describes target state (JSON Merge Patch) rather than relative changes.

**Mistakes to avoid:**
- Confusing safe with idempotent; PUT is idempotent but not safe.
- Claiming POST "cannot" be idempotent; it is not idempotent by default, but the key pattern fixes that.

### Q. How do you implement idempotency for a payment API endpoint?

**Short answer (45 seconds):** The client sends an Idempotency-Key header, a UUID per payment attempt. The server inserts the key into a table with a unique constraint on (account_id, key), plus a request hash. If the insert wins, it processes the payment and stores the response on the key row in the same transaction. If the insert loses, it checks the hash: a different body gets 422, an in-progress row gets 409, and a completed row gets the stored response replayed.

**Deeper explanation:**

```sql
CREATE TABLE idempotency_keys (
  account_id    bigint NOT NULL,
  key           text   NOT NULL,
  request_hash  text   NOT NULL,
  status        text   NOT NULL,
  response_code int,
  response_body jsonb,
  expires_at    timestamptz NOT NULL DEFAULT now() + interval '24 hours',
  PRIMARY KEY (account_id, key)
);
```

Request flow: compute `request_hash = sha256(method + path + canonical JSON body)`, then run `INSERT ... ON CONFLICT (account_id, key) DO NOTHING RETURNING key`. A returned row means you own the key; otherwise SELECT the existing row and branch on hash and status. The insert is both the dedup check and the lock; Postgres serialises on the unique index.

The money movement, the order update and `UPDATE idempotency_keys SET status = 'completed', response_code = 201, response_body = $1` happen in one transaction, so there is no state where the payment exists but the key does not. If the charge is executed by a payment provider, pass the same key downstream (Stripe accepts an Idempotency-Key header), so the external call is deduplicated too.

**Follow-ups they will ask:**
- Why hash the request?: A client bug can reuse a key with a different amount, and replaying the old response would hide that, so reject it.
- What do you return while the first request is still running?: 409 Conflict with a Retry-After, or hold the connection briefly and then replay.

**Mistakes to avoid:**
- Checking with SELECT then INSERT: two concurrent requests both see nothing and both charge.
- Storing the key in Redis while the payment commits in Postgres: a crash between the two leaves them inconsistent.

### Q. How do you store and look up idempotency keys efficiently?

**Short answer (45 seconds):** Store them in the same database as the business data, keyed by (account_id, key) with a primary key index, so the lookup is a single B-tree probe and the insert doubles as the lock. Store the request hash, status and the serialised response on the row. Give every row an expires_at and purge in batches or by dropping daily partitions. Redis SET NX PX works as a fast pre-check at very high volume, but the transactional store is the source of truth.

**Deeper explanation:** The access pattern is simple: one point lookup or insert per request, never a scan. A composite primary key on (account_id, key) handles that, and scoping by account keeps tenants from colliding or blocking each other.

```js
const { rows } = await db.query(
  `INSERT INTO idempotency_keys (account_id, key, request_hash, status)
   VALUES ($1, $2, $3, 'in_progress')
   ON CONFLICT (account_id, key) DO NOTHING
   RETURNING key`,
  [accountId, key, hash]
);
const weOwnIt = rows.length === 1;
```

Growth is linear in request volume, so expiry matters: index `expires_at` and delete in batches, or range partition by day so cleanup is dropping the old partition, which is instant and creates no bloat.

Redis is tempting because `SET key value NX PX 86400000` is one atomic command. It works as a fast duplicate filter, but Redis cannot join the Postgres transaction, so a crash after the SET and before the commit leaves a key with no effect behind it, and the retry gets a false "already done". Use Redis for the fast path, the database for correctness.

**Follow-ups they will ask:**
- How big does the table get?: Requests per day times retention; millions of rows a day is routine with daily partitions.
- Why not put the key on the payments table itself?: You can, with a unique (account_id, idempotency_key), but you lose the stored response and the in-progress state.

**Mistakes to avoid:**
- Global keys without account scope.
- No expiry, so the table silently becomes the largest in the database.

### Q. What happens if the server processes the request but crashes before responding?

**Short answer (45 seconds):** The client sees a timeout and retries with the same key. Because the key row was marked completed with the stored response in the same transaction as the payment, the retry finds it and replays the 201. The dangerous case is a crash in the middle: after calling the payment provider but before committing. The key row is then stuck in_progress, so the retry must detect the stale lock, ask the provider what happened using the same key, and reconcile instead of charging again.

**Deeper explanation:** Draw the timeline and mark where a crash can land.

```text
1. INSERT key (in_progress)        crash here: retry owns nothing new, sees stale lock
2. call provider with same key     crash here: provider may have charged
3. write payment + key=completed   crash here: nothing committed, same as 2
4. COMMIT                          crash here: safe, retry replays
5. send 201                        crash here: safe, retry replays
```

Step 4 and 5 crashes are the easy case and are why "store the response atomically with the effect" is non-negotiable. Steps 1 to 3 need a recovery rule. Give in_progress rows a `locked_at` timestamp. When a retry finds an in_progress row older than a lease (say 30 seconds), it takes over: it queries the provider by the idempotency key (Stripe returns the original result for a reused key), then either records the completed charge or marks the attempt failed, and only then replays.

**Follow-ups they will ask:**
- What if the provider does not support idempotency keys?: Record a provisional attempt before calling, then reconcile by searching the provider for your reference id; if that is impossible, you need manual review for in_progress rows.
- Should the retry wait or fail while the first attempt is in flight?: Return 409 quickly; waiting ties up connections and the client already has a retry loop.

**Mistakes to avoid:**
- Marking the key completed before the payment commit, or in a separate transaction.
- Treating a stuck in_progress row as permanent; without lease expiry a single crash blocks the key forever.

### Q. How do you handle idempotency in a message queue consumer?

**Short answer (45 seconds):** Assume every message can arrive more than once, because at-least-once is what Kafka, RabbitMQ, SQS and BullMQ actually give you. Make the handler idempotent: either the write itself is naturally idempotent (upsert on a business key, conditional update), or you keep a processed_messages table with a unique message id and insert into it in the same transaction as the business write. Acknowledge or commit the offset only after that transaction commits. On the producer side use a transactional outbox so publishing itself is reliable.

**Deeper explanation:** The dedup table is the general tool.

```sql
CREATE TABLE processed_messages (
  consumer   text NOT NULL,
  message_id text NOT NULL,
  processed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (consumer, message_id)
);
```

Handler: BEGIN; `INSERT INTO processed_messages ... ON CONFLICT DO NOTHING`; if zero rows were inserted, COMMIT and ack (duplicate). Otherwise apply the business write and COMMIT, then ack. A crash between COMMIT and ack redelivers the message, which the table now rejects as a duplicate.

The producer has the mirror problem: write to the database and then publish, and a crash in between loses the event. The transactional outbox fixes it: insert the business row and an `outbox` row in the same transaction, then a relay (a poller, or Debezium reading the write-ahead log) publishes outbox rows to Kafka and marks them sent. The relay can crash after publishing and before marking, so it publishes at least once, which is exactly why the consumer dedup table exists.

**Follow-ups they will ask:**
- Can I use Redis SET NX for dedup instead of a table?: Only when the business write is not in a transactional store; Redis and Postgres cannot commit together, so there is a window for a false duplicate or a double apply.
- How long do you keep processed ids?: At least as long as the broker can redeliver (retention, DLQ replay window); partition by day and drop.

**Mistakes to avoid:**
- Acking before the transaction commits (turns at-least-once into at-most-once).
- Relying on Kafka "exactly-once" for side effects outside Kafka.

### Q. What is the difference between idempotency and exactly-once delivery?

**Short answer (45 seconds):** Exactly-once delivery is a transport promise: the message reaches the consumer one time, no more and no less. Over an unreliable network that promise cannot be kept, because an acknowledgement can always be lost, leaving the sender to choose between resending (at-least-once) or not (at-most-once). Idempotency is a processing property on the receiver: handling the same message twice has the same effect as once. Combine at-least-once delivery with idempotent processing and you get what people really want, exactly-once effects.

**Deeper explanation:** The impossibility is the two generals problem in a different costume. The sender cannot know whether the receiver processed the message unless the receiver says so, and that reply can be lost too, so after any finite exchange one side is unsure. Brokers therefore guarantee at-least-once (ack after processing) or at-most-once (ack before processing), and everything called "exactly-once" is at-least-once plus dedup somewhere.

Kafka's "exactly-once semantics" is a precise, narrow thing: an idempotent producer (sequence numbers per partition so broker-side retries do not duplicate) plus transactions (atomic offset commit and output write, read with `isolation.level=read_committed`). It holds for read-process-write pipelines where input and output are both Kafka topics. The moment the consumer writes to Postgres or calls Stripe, you are back to idempotent consumers.

| Term | Where it lives | Guarantee |
| --- | --- | --- |
| At-least-once | broker and ack protocol | no loss, possible duplicates |
| Idempotency | consumer logic | duplicates are harmless |
| Exactly-once effects | the combination | each message changes state once |

**Follow-ups they will ask:**
- So is Kafka lying about exactly-once?: No, it is scoped to Kafka-to-Kafka processing; the docs say so, people drop the scope.
- Which one would you implement first on a new service?: Idempotent consumers, because they work with any broker and survive replays from a DLQ.

**Mistakes to avoid:**
- Answering "we use exactly-once delivery so we do not need idempotency".
- Treating at-most-once as acceptable for anything involving money.

### Q. Can a non-idempotent operation be made safe to retry? How?

**Short answer (45 seconds):** Yes, by giving each attempt an identity or by restating the operation in terms of target state. Options: an idempotency key with a stored outcome; a versioned conditional update instead of a relative one; an upsert on a natural business id; a ledger row with a unique transaction id so the second insert fails; or a server-issued one-time token (post once exactly). When none of that works, pair retries with a compensating action, which is a saga.

**Deeper explanation:** "Add 100 to the balance" is the classic non-idempotent op. Rewriting it as "set balance to 1100" is idempotent but loses concurrent updates. The correct rewrite keeps the relative semantics and adds identity.

```sql
INSERT INTO ledger (account_id, txn_id, amount)
VALUES ($1, $2, 100)
ON CONFLICT (txn_id) DO NOTHING;

UPDATE accounts
   SET balance = balance + 100, version = version + 1
 WHERE id = $1 AND version = $3;   -- optimistic check, retry on 0 rows
```

Both statements run in one transaction. A retry of the whole thing hits the ledger conflict, inserts nothing, and you skip the UPDATE. The same shape works for "send welcome email": insert into `emails_sent (user_id, template)` with a unique constraint before calling the provider, and the second attempt stops at the insert.

For external effects with no key support, the saga pattern applies: perform the step, record the step as done, and if a later step fails run the compensating action (refund, cancel). Every step is itself idempotent, so the saga coordinator can crash and resume.

**Follow-ups they will ask:**
- Does MongoDB have an equivalent?: Yes, `updateOne` with a unique index on the business id, or `findOneAndUpdate` with a version field in the filter.
- What about rate limits that count attempts?: Count on the key, not the request, so retries of the same attempt are not double charged.

**Mistakes to avoid:**
- Rewriting relative updates as absolute ones and calling it solved; that introduces lost updates.
- Forgetting that the compensating action in a saga must itself be idempotent.

### Practice
- Build the payment endpoint in Express plus Postgres: keys table, hash check, 409 on in-flight, replay on completed. Then kill the process with `kill -9` between the provider call and COMMIT and prove the retry recovers via the stale lock path.
- Write a Kafka or RabbitMQ consumer with a `processed_messages` table, run two consumer instances, replay the same topic from the beginning, and show the business table has no duplicates.
- Implement a transactional outbox with a poller that publishes and marks rows sent; crash it between the two steps and watch the consumer dedup absorb the duplicate.
- Say it out loud: "Walk me through what happens when a client times out on a payment and retries", covering key insert, hash mismatch, in-progress, completed replay, and the crash between provider call and commit, in under three minutes.

## Message Queues

> This section is about architecture, not tool trivia. The interviewer wants to know whether you can say why a queue sits between two services, what the broker promises, what it does not promise, and what you built on top to close the gap. Weak answers list features of RabbitMQ or Kafka. Strong answers talk in terms of delivery guarantees, ordering, consumer scaling, poison messages and what happens when the consumer falls behind, and then pick a tool because of those constraints. Have one real pipeline in mind and describe its failure modes.

### Concepts you must understand
- A queue is point-to-point: one message, one consumer, deleted after ack. Pub/sub fans a message out to every subscriber. Kafka gives both: consumer groups compete inside a group and fan out across groups.
- Brokers offer at-most-once (ack before processing) or at-least-once (ack after processing); exactly-once is at-least-once plus deduplication, scoped to specific systems such as Kafka transactions or SQS FIFO.
- Kafka is a partitioned, replicated, retained log. Ordering is per partition, a partition is read by exactly one consumer per group, and offsets are committed, not messages acked.
- RabbitMQ is a smart broker: producers publish to exchanges (direct, fanout, topic, headers), bindings route to queues, consumers ack or nack individual messages, and prefetch bounds unacked messages per consumer.
- A dead letter queue holds messages that failed too many times, expired, or were rejected, so one poison message cannot block the rest.
- Backpressure is the mechanism that slows producers when consumers cannot keep up: bounded queues, consumer pull, prefetch limits, publisher blocking and lag alarms.
- Duplicate handling belongs in the consumer: dedup table, idempotent writes, ack after commit.
- Queues decouple availability and time: the producer can succeed while the consumer is down, and spikes are absorbed by the buffer instead of by the database.
- Managed and library options: SQS and SNS on AWS, Pub/Sub on GCP, BullMQ on Redis for Node job queues; each has a visibility or lock timeout that behaves like an ack deadline.

### Q. What is the difference between a message queue and pub/sub?

**Short answer (45 seconds):** A message queue is point-to-point: a producer puts a message in a queue, exactly one of the competing consumers receives it, and once acknowledged it is gone. It distributes work. Pub/sub is broadcast: a producer publishes to a topic and every subscriber gets its own copy. It distributes events. Most real systems need both, which is why RabbitMQ routes through exchanges into per-subscriber queues, SNS fans out into SQS queues, and Kafka uses consumer groups so a topic is both shared within a team of consumers and fanned out across teams.

**Deeper explanation:** The distinction is about who should see the message. "Resize this image" wants one worker; "order 42 was placed" wants billing, inventory, analytics and email, each exactly once.

```text
queue:    producer -> [ emails ] -> worker1 | worker2 | worker3
pub/sub:  producer -> (order.placed) -> billing-queue -> billing workers
                                     -> inventory-queue -> inventory workers
```

RabbitMQ makes the two layers explicit: publish to a fanout or topic exchange, bind one queue per consuming service, and inside each queue workers compete. Kafka collapses the layers: a topic has partitions, every consumer group tracks its own offsets, so group `billing` and group `analytics` both read every message while members of one group split the partitions. SQS is a pure queue and SNS is pure pub/sub; the standard pattern is SNS fanning out into one SQS queue per service. Redis Pub/Sub is fire-and-forget with no persistence; Redis Streams with consumer groups is the durable alternative.

**Follow-ups they will ask:**
- What happens to a pub/sub message when a subscriber is down?: In Redis Pub/Sub it is lost; in Kafka it waits in the log until retention expires; in RabbitMQ it waits in that subscriber's durable queue.
- How do you get fan-out plus work distribution in SQS?: SNS topic, one SQS queue per service, many workers per queue.

**Mistakes to avoid:**
- Saying pub/sub is "just a queue with more consumers"; the retention and copy semantics are different.
- Using Redis Pub/Sub for anything that needs delivery guarantees.

### Q. Explain at-most-once, at-least-once, and exactly-once delivery.

**Short answer (45 seconds):** At-most-once: acknowledge or commit before you process, so a crash loses the message but never duplicates it. At-least-once: process first, acknowledge after, so a crash between the two redelivers and you may see duplicates. Exactly-once as a pure delivery guarantee does not exist across a network; what exists is at-least-once plus deduplication, which gives exactly-once effects. Kafka's transactions give it inside Kafka, SQS FIFO deduplicates by id for five minutes, and everything else relies on idempotent consumers.

**Deeper explanation:** Where the ack sits defines the semantics.

```js
// RabbitMQ with amqplib
ch.consume('emails', async (msg) => {
  try {
    await sendEmail(JSON.parse(msg.content.toString()));
    ch.ack(msg);                       // after the work: at-least-once
  } catch (err) {
    ch.nack(msg, false, false);        // no requeue: goes to the DLX
  }
}, { noAck: false });                  // noAck: true would be at-most-once
```

In Kafka the same choice is when you commit the offset. Commit before processing (or auto-commit on a timer that fires mid-batch) is at-most-once for the tail of that batch; commit after processing is at-least-once.

Exactly-once in Kafka means an idempotent producer (per-partition sequence numbers so broker retries do not duplicate, `enable.idempotence=true`) plus transactions (`transactional.id`, consumers reading with `isolation.level=read_committed`) so the offset commit and the output write are atomic. That is real, and it is limited to Kafka topics on both sides.

**Follow-ups they will ask:**
- When is at-most-once acceptable?: Metrics samples, presence pings, anything where the next message supersedes the lost one.
- What does a consumer crash do under at-least-once?: The unacked messages return to the queue and another consumer gets them, possibly out of order relative to its own later work.
- How does SQS FIFO dedup work?: A MessageDeduplicationId (or a content hash) is remembered for five minutes; duplicates in that window are accepted and dropped.

**Mistakes to avoid:**
- Claiming your system has exactly-once delivery because the broker has a checkbox for it.
- Forgetting that auto-commit in Kafka clients can commit offsets for messages you have not finished processing.

### Q. What is a dead letter queue and when does a message end up there?

**Short answer (45 seconds):** A dead letter queue is a parking lot for messages the consumer could not process. A message is moved there after it has been rejected or redelivered more than a configured number of times, when its TTL expires, or when the source queue is full and overflow policy says so. The point is isolation: one poison message must not block the queue or burn CPU on infinite retries. You alarm on DLQ depth, inspect the messages, fix the bug or the data, and replay them.

**Deeper explanation:** Each broker spells it differently. In RabbitMQ you declare a queue with a dead letter exchange; messages are dead lettered when a consumer nacks or rejects with requeue false, when `x-message-ttl` expires, when `x-max-length` is exceeded, or in quorum queues when `x-delivery-limit` redeliveries are reached.

```js
await ch.assertQueue('emails', {
  durable: true,
  deadLetterExchange: 'emails.dlx',
  messageTtl: 60_000,
});
```

In SQS a redrive policy names the DLQ and a `maxReceiveCount`; a message received that many times without being deleted is moved there. Kafka has no broker-side DLQ because it never deletes messages; the pattern is application-level: catch the failure, publish the record with error metadata to a `payments.dlq` topic, and commit the offset so the partition keeps moving.

A good DLQ message carries the original payload, headers, exception, attempt count and source, so replay is possible without guessing. Separate transient failures (database timeout, retry with backoff, maybe via a delayed retry queue) from permanent ones (malformed payload, go straight to the DLQ).

**Follow-ups they will ask:**
- How do you replay from a DLQ safely?: Consumers must be idempotent, and you replay in small batches so a still-broken handler does not refill the DLQ.
- Why not just log and drop?: A DLQ preserves the data and the evidence; logs are sampled, truncated and not replayable.

**Mistakes to avoid:**
- No alerting on the DLQ, so it becomes a graveyard nobody reads.
- Retrying a malformed message five times before dead lettering; permanent failures should skip retries.

### Q. What is backpressure and how do message queues help?

**Short answer (45 seconds):** Backpressure is the signal that flows backwards from a slow consumer to a fast producer saying "slow down". Queues help in two ways: they absorb bursts so the consumer runs at its own pace, and they make the imbalance visible as queue depth or consumer lag, which you can alarm on and autoscale from. The queue is a buffer, not a cure; a producer that is permanently faster than its consumer needs limits, not a bigger queue.

**Deeper explanation:** Kafka consumers pull, so a slow consumer polls less and data waits in the log; the pressure shows up as lag (log end offset minus committed offset). Producers have a bounded `buffer.memory` and block for `max.block.ms` when it is full, so even the producer side eventually feels it.

RabbitMQ pushes, which is why `prefetch` exists: `ch.prefetch(20)` means the broker sends at most 20 unacked messages to this consumer. On the producer side RabbitMQ applies credit-based flow control and blocks publishing connections when a memory or disk alarm fires; queues can also have `x-max-length` with an overflow policy of `drop-head` or `reject-publish`, which is explicit backpressure to the publisher.

```text
producer 5k/s --> [ queue depth rising ] --> consumer 2k/s
```

The design question is always the same: when the buffer is full, who waits, who gets an error, and what gets dropped. BullMQ exposes the same choice as worker `concurrency` and a rate limiter.

**Follow-ups they will ask:**
- What does unbounded buffering look like in production?: Growing memory on the broker or producer, then an OOM kill, then a burst of redeliveries that makes the consumer even slower.
- How do you choose prefetch?: High enough to keep the worker busy (a few times the per-message latency times throughput), low enough that a crash does not strand hundreds of messages.

**Mistakes to avoid:**
- Answering "add more consumers" without asking whether the downstream (database, third-party API) can take the load.
- Accepting a queue that never drains to zero; that is an underprovisioned system, not a buffer.

### Q. How do you handle duplicate messages in a consumer?

**Short answer (45 seconds):** Accept that duplicates will happen under at-least-once delivery and design for it. First choice: make the write naturally idempotent, an upsert on the business id or a version-guarded conditional update. Second choice: a processed_messages table with a unique message id, inserted in the same transaction as the business write, so the second delivery hits the conflict and is acked without effect. Ack or commit the offset only after the transaction commits. Redis SET NX is a fast filter, not a guarantee.

**Deeper explanation:** Pick a stable id. For Kafka the (topic, partition, offset) triple is unique and survives redelivery, but it changes on republish, so a producer-generated event id in the payload is more robust. For RabbitMQ and SQS set a message id yourself.

```js
await db.tx(async (t) => {
  const r = await t.result(
    `INSERT INTO processed_messages (consumer, message_id)
     VALUES ($1, $2) ON CONFLICT DO NOTHING`, ['billing', evt.id]);
  if (r.rowCount === 0) return;            // duplicate
  await t.none(`UPDATE orders SET status = 'paid' WHERE id = $1`, [evt.orderId]);
});
ch.ack(msg);                                // only after commit
```

The dedup row and the business write commit together, so there is no window where one exists without the other. If the business write goes to a system you cannot transact with, insert the dedup row first, call the external system, and treat "row exists but call failed" as the retry path, the same recovery problem as the idempotency key table.

Keep processed ids longer than the longest possible redelivery, including DLQ replays; daily partitions keep that cheap.

**Follow-ups they will ask:**
- Why not dedup in the broker?: Brokers cannot know what your handler did; SQS FIFO dedups producer-side duplicates for five minutes, nothing dedups consumer-side redelivery.
- Does ordering fix duplicates?: No, and duplicates do not fix ordering; use versioned updates for order, dedup rows for repeats.

**Mistakes to avoid:**
- Checking a Redis set and then writing to Postgres as two separate steps.
- Using a per-process in-memory set, which is lost on restart and not shared across consumers.

### Q. What is a consumer group in Kafka and how does it enable scaling?

**Short answer (45 seconds):** A consumer group is a set of consumers that share one group id and split the partitions of a topic between them: each partition is assigned to exactly one consumer in the group, and each consumer may own several partitions. Offsets are tracked per group, so different groups read the same topic independently. Scaling is adding consumers up to the partition count; beyond that the extra consumers sit idle. Ordering is preserved within a partition because only one consumer reads it at a time.

**Deeper explanation:**

```text
topic payments, 4 partitions
group billing   (3 consumers): c1 -> P0, P1   c2 -> P2   c3 -> P3
group analytics (1 consumer):  a1 -> P0, P1, P2, P3
```

Producers choose a partition by hashing the record key, so all events for one order land on the same partition and are seen in order by one consumer. No key means no ordering guarantee across events. The partition count is therefore the unit of parallelism and is set up front; you can add partitions later, but keys will rehash onto different partitions, which breaks ordering for in-flight keys.

When a consumer joins, leaves or is deemed dead, the group coordinator triggers a rebalance and reassigns partitions. Classic eager rebalancing stops the whole group briefly; the cooperative sticky assignor moves only the partitions that need to move. A consumer is deemed dead if it misses heartbeats within `session.timeout.ms` or does not call `poll()` within `max.poll.interval.ms`, so a slow handler causes rebalances and duplicates.

**Follow-ups they will ask:**
- How many partitions should I create?: Enough for your target consumer count plus headroom, bounded by the per-partition overhead on brokers; changing it later is painful for keyed data.
- What if one key is hot?: That partition becomes the bottleneck; fix the key design (add a sub-key) rather than adding partitions.

**Mistakes to avoid:**
- Saying "add more consumers" without knowing the partition count.
- Assuming topic-wide ordering; it is per partition only.

### Q. When would you use a message queue instead of a direct API call?

**Short answer (45 seconds):** Use a queue when the caller does not need the result right now and the work must survive the callee being down or slow: emails, thumbnails, LLM batch jobs, third-party syncs, fanning one event out to several services. The queue buys decoupled availability, burst absorption, retries with backoff, dead lettering and fan-out. Use a direct call when the caller needs the answer to continue, needs read-your-write consistency, or when the extra moving part is not worth it.

**Deeper explanation:** The honest decision table:

| Need | Direct call | Queue |
| --- | --- | --- |
| Caller needs the result to proceed | yes | no |
| Callee may be down and work must not be lost | no | yes |
| Traffic arrives in spikes the callee cannot absorb | no | yes |
| One event, many interested services | awkward | yes |

A direct call couples uptime: if the email provider is down, signup fails unless you add timeouts, circuit breakers and a fallback, at which point you have built half a queue badly. For an AI product the typical queue cases are document ingestion for a RAG index, embedding generation, and long-running agent runs where the API returns a job id and a status endpoint or webhook delivers the result.

The hidden costs: the producer gets "accepted", not "done", so the UI needs a pending state; failures surface later in a DLQ instead of the request log; ordering across services is not guaranteed; and every consumer must be idempotent.

**Follow-ups they will ask:**
- How does the client learn the result?: Polling a job resource, a webhook, or a server-sent events stream keyed by job id.
- Why not an in-process async task (setImmediate, a background promise)?: It dies with the process and cannot be retried or scaled.

**Mistakes to avoid:**
- Putting a queue in front of something the user is waiting on, then polling every 200 ms to hide it.

### Q. What is the difference between Kafka and RabbitMQ?

**Short answer (45 seconds):** Kafka is a replicated, retained log: messages are appended to partitions, kept for a retention period regardless of consumption, and consumers pull and track their own offsets, which gives replay, independent consumer groups and high throughput with per-partition ordering. RabbitMQ is a smart broker: producers publish to exchanges with flexible routing, the broker pushes to consumers, each message is acked and deleted, and you get TTLs, priorities and dead letter exchanges. Pick Kafka for event streaming and replay, RabbitMQ for work distribution with rich routing.

**Deeper explanation:**

| Aspect | Kafka | RabbitMQ |
| --- | --- | --- |
| Model | partitioned log | exchanges feeding queues |
| Delivery | pull | push with prefetch |
| Retention | time or size based, independent of consumers | until acked (or TTL) |
| Replay | yes, reset offsets | no |
| Ordering | per partition | per queue with one consumer |
| Routing | by topic and key | direct, topic, fanout, headers exchanges |

Kafka's "dumb broker, smart consumer" design is why it scales: sequential disk writes, and consumers manage their own position. It fits event sourcing, change data capture (Debezium), stream processing, and any case where several teams want the same events at different times.

RabbitMQ shines when each message is a job: image resizing, webhook delivery, email. Routing keys like `order.*.eu` shape flows without code, priority queues let urgent jobs skip ahead, and quorum queues (Raft-based) are the durable choice. Its weakness is Kafka's strength: once acked a message is gone, and a deep queue degrades performance.

**Follow-ups they will ask:**
- Where do SQS and BullMQ fit?: SQS is a managed RabbitMQ-style queue without routing; BullMQ is a Redis-backed job queue for Node with delays, retries and rate limits.
- Can RabbitMQ do streams?: Yes, RabbitMQ Streams add a log abstraction, but Kafka's ecosystem for streaming is deeper.

**Mistakes to avoid:**
- "Kafka is faster" as the whole answer; the models differ, throughput is a consequence.

### Practice
- Stand up RabbitMQ in Docker, declare a queue with a dead letter exchange and `x-delivery-limit`, write a consumer that fails every third message, and watch the messages land in the DLQ; then replay them.
- Create a Kafka topic with 4 partitions, run 1, 4 and 6 consumers in one group, and print which partitions each gets; then kill one and observe the rebalance and the duplicates it causes.
- Simulate backpressure: a producer at 5k messages per second into a consumer that sleeps 1 ms per message; graph queue depth or lag, then fix it with prefetch, concurrency and a second consumer.
- Say it out loud: "Design the async pipeline for document ingestion into a RAG index", covering queue choice, partition key, idempotent consumer, DLQ, and how the client learns the job finished, in under three minutes.

## Distributed Systems Basics

> These questions check whether you have thought about what breaks when there is more than one machine: messages get lost, clocks disagree, a node that looks dead may just be slow, and two halves of a cluster may both believe they are in charge. Interviewers rarely want proofs; they want you to name the trade-off, give a real system that made each choice, and explain what you would do in your own service. Weak answers recite CAP as "pick two". Strong answers say what consistency means precisely, where quorums and fencing tokens come from, and why a timeout is a guess, not a fact.

### Concepts you must understand
- CAP is about behaviour during a network partition: you keep either linearizable consistency or availability, and partitions are not optional. PACELC adds the normal-case trade-off between latency and consistency.
- Eventual consistency means replicas converge once writes stop; session guarantees (read-your-writes, monotonic reads) are the practical middle ground.
- Consistent hashing places nodes and keys on a ring so adding or removing a node moves only a fraction of keys; virtual nodes smooth the load.
- A quorum is a majority (N/2 + 1): two majorities always overlap, which is what prevents split brain and makes leader election safe.
- A lock with an expiry can be held by two processes after a pause; a fencing token (monotonic number from the lock service, checked by the resource) is the fix.
- Two generals shows agreement over a lossy channel can never be certain; two-phase commit does not beat it, it blocks until the coordinator recovers.
- Failure detection is timeout based, so "dead" always means "did not answer in time"; heartbeats, leases and accrual detectors tune that guess.
- A load balancer distributes traffic at one point; a service mesh puts a proxy next to every service to handle mTLS, retries, timeouts, routing and telemetry for all east-west calls.
- Idempotency, retries with backoff and timeouts on every network call are the baseline hygiene that the rest of this section assumes.

### Q. What is the CAP theorem? Give a real example of a CP and an AP system.

**Short answer (45 seconds):** CAP says that when a network partition separates nodes, a distributed data store must choose between consistency, meaning every read sees the latest write (linearizability), and availability, meaning every request to a live node gets a non-error response. Partition tolerance is not a choice; networks fail. ZooKeeper and etcd are CP: a minority side refuses writes rather than diverge. Cassandra and DynamoDB in eventually consistent mode are AP: every node keeps answering and replicas reconcile later. Most databases let you move along that line per operation.

**Deeper explanation:** The common misreading is "pick two of three". The theorem (Brewer's conjecture, proved by Gilbert and Lynch) only bites during a partition: a node that cannot reach the others must either answer with possibly stale data (A) or refuse (C). In normal operation you can have both, which is why PACELC is the more useful model: if Partitioned choose A or C, Else choose Latency or Consistency. Cassandra is PA/EL: it stays available under partition and trades consistency for latency even when healthy. Consensus systems are PC/EC.

```text
          partition
   [n1 n2] | [n3]        client writes x=2 to n1
CP: n3 refuses reads/writes until it rejoins (etcd minority, ZooKeeper)
AP: n3 serves x=1, accepts writes, merges later (Cassandra, Dynamo-style)
```

CP in practice: etcd and ZooKeeper (Raft and ZAB), Postgres with synchronous replication, which stops accepting commits when it cannot reach the sync standby, MongoDB with majority write concern. AP in practice: Cassandra at `ONE` consistency, DynamoDB default reads, DNS, CouchDB, any multi-leader setup with conflict resolution.

**Follow-ups they will ask:**
- Can a single Postgres primary be CA?: Only trivially, because one node has no partition; the moment you add a replica you are choosing.
- Is availability in CAP the same as uptime?: No, it is a per-request property on live nodes; a CP system can still have excellent uptime.

**Mistakes to avoid:**
- "Pick two" with P as optional.
- Calling a system CP or AP as a whole when it is a per-operation setting.

### Q. What is eventual consistency? Give a real-world example of when it's acceptable.

**Short answer (45 seconds):** Eventual consistency means that if writes stop, all replicas converge to the same value, but a read in the meantime may return stale data. It is acceptable when a stale view is harmless and a slow or unavailable answer is worse: like counts, a catalogue page served from a read replica, DNS records, CDN caches, search indexes. It is not acceptable when a decision depends on the latest value: stock on hand at checkout, an account balance before a withdrawal, revoking an access token.

**Deeper explanation:** Ask what the user does with the value: displaying is usually fine, deciding usually is not. Postgres read replicas are the everyday example: a user updates their profile on the primary, the next request hits a replica that is 200 ms behind, and they see the old name. That is a read-your-writes violation; the fix is a session guarantee, not strong consistency everywhere: route that user's reads to the primary for a few seconds after a write, or check the replica's replay LSN against the write's LSN before serving.

Dynamo-style stores make it explicit: writes go to N replicas with W acks, reads consult R; with W + R > N a read overlaps the latest write, otherwise you are eventually consistent and faster. Replicas converge through anti-entropy and read repair, and concurrent writes need a rule: last-writer-wins, version vectors, or CRDTs for counters and sets.

For an AI product, the vector index being a few seconds behind the document store is acceptable; the permission check that decides which documents a user may retrieve is not.

**Follow-ups they will ask:**
- How do you measure it?: Replication lag (Postgres `pg_stat_replication`, `pg_last_wal_replay_lsn()`), Kafka consumer lag, index freshness timestamps.
- How do you avoid lost updates with last-writer-wins?: Use a version or vector clock on the record, or model the data as a CRDT or an append-only log.

**Mistakes to avoid:**
- Saying eventual consistency means "no consistency"; convergence is a guarantee.
- Serving an authorisation decision from a cache or replica without thinking about the window.

### Q. What is consistent hashing and why is it used?

**Short answer (45 seconds):** Consistent hashing maps both nodes and keys onto the same hash ring, and each key belongs to the first node clockwise from its position. When a node joins or leaves, only the keys between it and its neighbour move, roughly 1/N of the data, instead of nearly everything as with `hash(key) mod N`. Virtual nodes give each physical node many positions on the ring so load is even and bigger machines can take more. It is used for distributed caches, Cassandra and Dynamo-style partitioning, and sticky load balancing.

**Deeper explanation:** With modulo hashing, going from 4 to 5 cache servers remaps about 80 percent of keys, which empties the cache and stampedes the database; on a ring a new node only steals the arc just before it.

```text
ring (0..2^32):  A@10  B@40  C@70   key k hashes to 55 -> C
add D@60:        k now -> D; only keys in (40, 60] move from C to D
```

With one position per node the arcs are uneven, so one node can own several times the data of another, and when a node dies its whole load lands on one neighbour. Virtual nodes solve both: each physical node gets many tokens spread around the ring, so ownership is statistically even and a failed node's load spreads across many successors; a bigger machine simply gets more tokens. Cassandra calls these vnodes (`num_tokens`), and replication walks clockwise to the next distinct physical nodes.

You meet it in memcached clients (ketama), Cassandra and Riak partitioning, Envoy and nginx ring-hash load balancing, and sharded websocket servers.

**Follow-ups they will ask:**
- How do you pick the hash function?: Fast and well distributed, such as MurmurHash or xxHash; never a language's default string hash across processes.
- What about hot keys?: Consistent hashing balances key count, not key popularity; a hot key needs replication or a local cache in front.

**Mistakes to avoid:**
- Describing it as "hash mod N but better" without the ring and the 1/N movement property.

### Q. What is a split-brain problem?

**Short answer (45 seconds):** Split brain is when a network partition leaves two parts of a cluster each believing they are the authoritative side, so both accept writes and the data diverges. In a replicated database it means two primaries, the worst case, because the data can only be reconciled by hand. The defence is a majority quorum: only the side that can reach more than half the nodes may act, so at most one side ever can, plus fencing to stop the old leader doing damage.

**Deeper explanation:** Picture a three-node Postgres cluster with automatic failover. A switch fails and the primary, node 1, is cut off from nodes 2 and 3, which assume it died and promote node 2. Node 1 is alive with clients still connected, so two primaries accept writes until the switch returns, and you lose one side's data.

Quorums break the symmetry: with N = 3 a majority is 2, and both halves cannot have 2, which is why clusters have odd sizes and a 2-node cluster cannot fail over safely without a witness. Raft and ZAB bake it in: a leader needs a majority of votes and each term has at most one. Patroni does Postgres HA this way with a leader lease in etcd or Consul; a primary that cannot renew the lease demotes itself.

Fencing is the second half: the old leader may still be mid-write when it loses the lease, so the new leader's writes must carry a higher epoch or term that storage rejects from stale writers; the hardware equivalent is STONITH, powering off the other node.

**Follow-ups they will ask:**
- Why not detect the dead primary with a heartbeat?: A failed heartbeat is exactly what a partition looks like; it cannot tell dead from unreachable.
- What does Kafka do?: `unclean.leader.election.enable=false` stops an out-of-sync replica becoming leader and losing acked writes.

**Mistakes to avoid:**
- Proposing a two-node active-active database with automatic failover.
- Forgetting fencing; the old leader may step down too late.

### Q. What is a distributed lock and what are its failure modes?

**Short answer (45 seconds):** A distributed lock lets one process at a time across many machines own a resource, typically via `SET key token NX PX ttl` in Redis, an ephemeral node in ZooKeeper, or an etcd lease. Failure modes: the holder pauses past the TTL and a second holder gets the lock while the first still believes it owns it; a Redis failover drops the lock because replication is asynchronous; a client deletes a lock it no longer owns. The fix for the first is a fencing token checked by the resource, not a longer TTL.

**Deeper explanation:** A single-Redis lock is fine for efficiency and wrong for correctness. Redlock hardens it by acquiring the key on a majority of independent Redis nodes within a bounded time, but it still relies on TTLs and comparable clock rates, and a paused client can still wake after expiry and write.

Fencing tokens close the hole: the lock service hands out a strictly increasing number with every grant, the client sends it with every write, and storage rejects any token lower than the highest seen. etcd provides this through lease and revision numbers, ZooKeeper through the zxid. The resource must participate; a lock only the clients know about cannot protect it.

Redis hygiene: a random token as the value, release through a Lua script that deletes only if the value matches, and a watchdog that extends the TTL while work continues. Inside one Postgres, prefer `pg_advisory_xact_lock` or `SELECT ... FOR UPDATE`, released with the transaction and needing none of this.

**Follow-ups they will ask:**
- Why not make the TTL very long?: A crashed holder then blocks everyone for that long; TTL trades double-holder risk against stall time.
- Is Redlock safe?: For efficiency, yes; for correctness its timing assumptions have been criticised, and consensus-backed leases with fencing are safer.

**Mistakes to avoid:**
- `SET NX` without a TTL, or TTL without a unique value.
- Treating the lock as the only defence; writes should also be idempotent or version-checked.

### Q. What is the two-generals problem and why does it matter?

**Short answer (45 seconds):** Two generals on opposite hills must attack at the same time to win, and can only communicate by messengers who may be captured. No finite exchange of messages lets both be certain the other will attack, because the last message sent might not have arrived and its sender cannot know. It matters because it is the formal reason exactly-once delivery over a network is impossible: an acknowledgement can always be lost, so protocols must choose at-least-once or at-most-once and then make the receiver idempotent.

**Deeper explanation:** The proof is short: take the protocol with the fewest messages; its last message may be lost, and if the protocol still works without it, it was unnecessary, so a shorter one exists. Real systems replace certainty with retries and durability; TCP retransmits until an ack arrives or a timeout gives up, and a client still cannot know whether a timed-out POST was processed.

Two-phase commit is the usual counterexample. A coordinator asks participants to prepare; each writes a durable prepared record and votes; if all vote yes the coordinator durably records commit and tells everyone to commit. It does not beat the two generals, it changes the problem: participants that voted yes are in doubt until they hear the decision, hold their locks and wait, possibly forever if the coordinator is lost. The guarantee is atomicity, bought with blocking and the assumption that nodes recover with their logs intact.

Postgres exposes 2PC as `PREPARE TRANSACTION` and `COMMIT PREPARED`; across microservices the pragmatic answer is a saga with idempotent, compensable steps.

**Follow-ups they will ask:**
- How is Byzantine generals different?: Byzantine nodes may lie; two generals only lose messages.
- Where does this show up in a web app?: Any timeout on a write: the client must retry with an idempotency key because it cannot know what happened.

**Mistakes to avoid:**
- Saying 2PC "solves" two generals.
- Confusing it with consensus; 2PC decides one transaction's outcome, consensus agrees on a replicated log.

### Q. What is a heartbeat in distributed systems?

**Short answer (45 seconds):** A heartbeat is a small periodic message a node sends to say it is alive, so that others can detect its failure by the absence of the next one. It drives leader liveness in Raft, membership in Kafka consumer groups, pod health in Kubernetes and membership in gossip systems. The key subtlety is that a missed heartbeat only proves the node did not respond in time; it may be dead, paused, or cut off by the network. Everything built on heartbeats has to tolerate that ambiguity, usually with leases, quorums and fencing.

**Deeper explanation:** A failure detector has two knobs: how fast it notices real failures and how often it falsely accuses slow nodes. Shorter timeouts mean faster failover and more false positives: a needless election in Raft, or a rebalance and duplicates in a Kafka consumer group. Raft leaders send empty AppendEntries as heartbeats and followers start an election after a randomised timeout (150 to 300 ms in the paper), the randomisation preventing split votes. Kafka consumers heartbeat on a background thread every `heartbeat.interval.ms` and are evicted after `session.timeout.ms`.

Two refinements matter. A lease inverts the heartbeat: the leader holds a time-bounded right to act, must renew it, and stops acting when it cannot, which makes a slow-but-alive leader safe. Accrual detectors (the phi accrual detector in Cassandra and Akka) replace a fixed timeout with a suspicion level computed from arrival history, so a noisy network does not trigger failover.

**Follow-ups they will ask:**
- Heartbeat or TCP keepalive?: Keepalive says the connection is up; a heartbeat says the application is responsive, which is what you care about.
- How do you tune the timeout?: Measure p99 heartbeat latency including GC pauses and set the timeout a comfortable multiple above it.

**Mistakes to avoid:**
- Treating a missed heartbeat as proof of death and letting it alone trigger destructive actions.
- Doing the heartbeat on the same thread as the work, so a slow job looks like a dead node.

### Q. What is the difference between a service mesh and a load balancer?

**Short answer (45 seconds):** A load balancer is one component in front of a set of backends that spreads traffic across them at L4 or L7: nginx, HAProxy, an AWS ALB. A service mesh is infrastructure for all service-to-service traffic: a sidecar proxy (Envoy in Istio, a Rust micro-proxy in Linkerd) runs next to every instance and a control plane configures them. The mesh load balances too, but its point is the rest: mTLS, retries, timeouts, circuit breaking, canary traffic splits, authorisation policy and uniform telemetry, without changing application code.

**Deeper explanation:**

With only load balancers, service A calls B through B's internal LB, and retries, timeouts and TLS live in each service's HTTP client. In a mesh, A's sidecar intercepts the call, resolves B's endpoints from the control plane, picks one (client-side balancing with outlier detection), opens mTLS to B's sidecar, applies retry and timeout policy, and emits metrics and trace headers. Istio's `VirtualService` and `DestinationRule` send 5 percent of traffic to a new version, and `AuthorizationPolicy` says only checkout may call payments.

The costs are real: two proxy hops per call add latency, each sidecar uses CPU and memory, and debugging now includes proxy config and certificates; Istio's ambient mode moves to a per-node proxy to cut that overhead. A mesh pays off with many services in several languages that need uniform security and resilience; a handful of Node services behind an ALB does not need one.

**Follow-ups they will ask:**
- Is an API gateway a mesh?: No, a gateway handles the edge (auth, rate limits, external routing); a mesh handles internal calls, and Istio's ingress gateway bridges the two.
- L4 vs L7 load balancing?: L4 forwards TCP connections and cannot see HTTP; L7 can route by path and header, retry requests and terminate TLS.

**Mistakes to avoid:**
- Describing a mesh as "a load balancer per pod"; load balancing is the smallest part of its value.
- Recommending a mesh for a small system without naming the latency and operational cost.

### Practice
- Spin up a three-node etcd cluster in Docker, partition one node with `iptables` or by pausing the container, and observe which side still accepts writes; then do the same with a two-node setup and see why it cannot fail over safely.
- Implement a consistent hash ring in 60 lines of TypeScript with and without virtual nodes, insert 100k keys, add a node, and measure both how many keys moved and the per-node imbalance.
- Build a Redis lock with `SET NX PX`, a random token and a Lua release script; then add a fencing token stored in Postgres and demonstrate a stale holder's write being rejected after a simulated pause.
- Say it out loud: "Explain CAP using a real database you have run, then tell me what you would do if two primaries appeared", covering linearizability, quorum, step-down and fencing, in under three minutes.
