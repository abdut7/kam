# Backend Interview Questions (source: onyx-foundation-744.notion.site, fetched 2026-10-30)

## Database Indexing
> Indexing is the #1 performance topic in backend interviews. Interviewers don't want definitions, they want to know if you've actually run EXPLAIN, seen a slow query, and fixed it.
1. What is a B-tree index and how does it work internally?
2. What is the difference between a clustered and non-clustered index?
3. What is a composite index? Explain the left-prefix rule.
4. When would you NOT add an index?
5. What is a covering index?
6. How do you diagnose a slow query in production?
7. What is index cardinality and why does it matter for query planning?
8. How does an index affect INSERT, UPDATE, and DELETE performance?

## Transactions & Isolation Levels
> This is one of the most misunderstood backend topics. Most developers use transactions but can't explain what isolation level their app runs at or what bugs that might cause.
1. What are ACID properties? Explain each one with a real example.
2. What are the 4 isolation levels? What problem does each one prevent?
3. What is a dirty read, phantom read, and non-repeatable read?
4. What is a deadlock? How do you detect and prevent one?
5. What is the difference between optimistic and pessimistic locking?
6. When would you use SERIALIZABLE isolation and what does it cost you?
7. What is a two-phase commit and what problem does it solve?
8. What is a savepoint? When would you use one?

## Concurrency
> Concurrency bugs are the hardest to reproduce and the most expensive in production. Interviewers use this topic to test if you understand what actually happens when two requests hit the same code at the same millisecond.
1. What is a race condition? Give a real backend example.
2. What is the difference between concurrency and parallelism?
3. How does Node.js handle concurrent requests without multiple threads?
4. What is an atomic operation? Why does it matter for counters?
5. What is a connection pool and what happens if you don't use one?
6. What is a distributed lock and when do you need one?
7. What is the thundering herd problem in the context of concurrency?
8. How do you make a counter increment safe under high concurrency?

## Caching
> Caching questions are in almost every senior backend interview. The wrong answers are 'use Redis' and 'add a TTL'. The right answers involve strategy, invalidation, and failure modes.
1. Explain the four main caching strategies and when to use each.
2. What is cache invalidation and why is it considered one of the hardest problems in CS?
3. What is a cache stampede / thundering herd and how do you prevent it?
4. What is a hot key problem in Redis and how do you solve it?
5. When should you NOT cache something?
6. What is the difference between a local cache and a distributed cache?
7. How do you handle cache consistency when data changes?
8. What is a CDN and how is it different from an application-level cache?

## Idempotency
> Idempotency is a senior-level topic that most junior devs have never heard of and most mid-level devs know the word but can't implement. It comes up in every payments, messaging, and distributed systems interview.
1. What is idempotency? Why does it matter for APIs?
2. Which HTTP methods are idempotent by spec? Which aren't?
3. How do you implement idempotency for a payment API endpoint?
4. How do you store and look up idempotency keys efficiently?
5. What happens if the server processes the request but crashes before responding?
6. How do you handle idempotency in a message queue consumer?
7. What is the difference between idempotency and exactly-once delivery?
8. Can a non-idempotent operation be made safe to retry? How?

## Message Queues
> Message queue questions test if you understand async architecture, not just whether you've used a tool. Interviewers want to know when you'd use a queue and what breaks without one.
1. What is the difference between a message queue and pub/sub?
2. Explain at-most-once, at-least-once, and exactly-once delivery.
3. What is a dead letter queue and when does a message end up there?
4. What is backpressure and how do message queues help?
5. How do you handle duplicate messages in a consumer?
6. What is a consumer group in Kafka and how does it enable scaling?
7. When would you use a message queue instead of a direct API call?
8. What is the difference between Kafka and RabbitMQ?

## Distributed Systems Basics
> Distributed systems questions separate developers who've built on one server from engineers who've thought about what happens when you have many. Every FAANG and product company interview includes at least two of these.
1. What is the CAP theorem? Give a real example of a CP and an AP system.
2. What is eventual consistency? Give a real-world example of when it's acceptable.
3. What is consistent hashing and why is it used?
4. What is a split-brain problem?
5. What is a distributed lock and what are its failure modes?
6. What is the two-generals problem and why does it matter?
7. What is a heartbeat in distributed systems?
8. What is the difference between a service mesh and a load balancer?

## API Design
> API design is asked in almost every backend interview because it reveals how you think about contracts, versioning, and the developers who will consume what you build. A good API is harder to design than to build.
1. What makes an API RESTful? What are the constraints?
2. When would you use REST vs GraphQL vs gRPC?
3. How do you version an API without breaking existing clients?
4. What is cursor-based pagination and why is it better than offset?
5. What HTTP status codes should your API return for these scenarios?
6. How do you design an API endpoint that might take 30 seconds to complete?
7. What is HATEOAS and is it worth implementing?
8. How do you design backward-compatible API changes?

## Database Design
> Database design questions reveal whether you've designed a schema that worked in production or just one that worked in development. The N+1 problem, migrations, and sharding are the three most common deep dives.
1. What is database normalisation? What are 1NF, 2NF, 3NF?
2. When would you denormalise a database and what are the trade-offs?
3. What is the N+1 query problem? How do you detect and fix it?
4. When would you choose SQL over NoSQL and vice versa?
5. What is database sharding? What problems does it introduce?
6. How do you run a database migration with zero downtime?
7. What is connection pooling and what happens without it?
8. What is a foreign key constraint and when would you skip it?

## Production Debugging
> This is the most practical category — interviewers ask scenario questions to see if you've actually been paged at 2am and solved a real problem. Structure your answers: observe, hypothesise, test, fix, prevent.
1. Your API response times doubled overnight. Walk me through debugging this.
2. Your database CPU is at 100%. What are the first 5 things you check?
3. How do you find a memory leak in a production Node.js service?
4. What is distributed tracing and how does it help debug microservices?
5. What is the difference between a metric, a log, and a trace?
6. Your error rate is 1% but you can't reproduce the error. How do you debug it?
7. How do you debug a race condition that only happens in production?
8. What should a good post-mortem contain?
