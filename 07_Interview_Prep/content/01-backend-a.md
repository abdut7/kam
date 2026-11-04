# Backend Engineering

> This track covers the storage and runtime fundamentals that come up in nearly every senior backend or AI full stack interview: how indexes make queries fast, how transactions keep data correct, what really happens when two requests touch the same row or counter in the same millisecond, and how caching trades freshness for speed. For an AI Full Stack Engineer these matter twice over. Your agents, tool calls, and RAG pipelines sit on top of Postgres, Redis, and MongoDB, and interviewers want proof that you can keep that layer correct and fast while an LLM drives it at unpredictable concurrency. Every answer here is written to be said out loud, with the follow-ups and traps that separate a mid-level answer from a senior one.

## Database Indexing

> Interviewers rarely want the textbook definition of an index. They want to hear that you have read an EXPLAIN plan, recognised a sequential scan on a large table, and fixed it with the right composite or covering index, and that you know when an index would make things worse. A weak answer says "add an index on the column in the WHERE clause". A strong answer talks about selectivity, the left-prefix rule, write amplification, and the planner's estimated versus actual rows, and names the tools: EXPLAIN (ANALYZE, BUFFERS), pg_stat_statements, pg_stats.

### Concepts you must understand
- A B-tree index is a balanced, sorted tree of key values with pointers to rows; equality lookups, range scans, and ORDER BY on the indexed columns cost a few page reads instead of a full table scan.
- Postgres tables are heaps: every index, including the primary key, is a secondary structure pointing to a tuple location (ctid); MySQL InnoDB stores the table itself inside the primary key B-tree and secondary indexes store the primary key value.
- A composite index is sorted by its first column, then the second within equal first values, so a query can only use it efficiently for a leading prefix of the columns (the left-prefix rule).
- Selectivity drives the planner: an index on a column with three distinct values is nearly useless on its own, while an index on a unique email is ideal.
- A covering index (Index Only Scan) answers the query from the index alone; in Postgres that also depends on the visibility map, because the index stores no row visibility information.
- Every index adds write amplification (extra page writes and WAL on INSERT, UPDATE, DELETE), storage, and vacuum work; Postgres UPDATEs that do not touch indexed columns can be HOT (heap-only tuple) updates that skip index maintenance.
- EXPLAIN (ANALYZE, BUFFERS) shows what the planner chose and what actually happened: estimated versus actual rows, buffer hits versus reads, and the node where the time goes.
- pg_stat_statements aggregates call counts and total time per normalised query across the server, so you find the query that matters in aggregate before explaining anything.
- Other index types fit other query shapes: GIN for arrays, jsonb, and full-text search; GiST for geometry and ranges; BRIN for huge append-only tables; HNSW or IVFFlat in pgvector for embeddings.
- Partial indexes (`WHERE status = 'pending'`) and expression indexes (`lower(email)`) keep an index small and match the exact predicate the query uses.

### Q. What is a B-tree index and how does it work internally?
**Short answer (45 seconds):** A B-tree index is a balanced, sorted tree over the indexed values. Internal pages hold separator keys that route a lookup to a leaf; leaves hold the keys with pointers to rows. The tree is wide and shallow, three or four levels for hundreds of millions of rows, and the leaves are linked in sorted order, so equality lookups, range scans, and ORDER BY on the indexed columns cost a few page reads instead of a full scan.

**Deeper explanation:** Each node is one page (8 KB in Postgres). The root and internal pages stay in memory, so `WHERE email = 'a@b.com'` reads the root, one or two internal pages, one leaf, then follows the tuple pointer (the ctid) to the heap page holding the row. A full leaf splits in two and pushes a separator key up, so every root-to-leaf path keeps the same depth.

```text
             [ 40 | 80 ]                 root
          /       |       \
  [10|20|30] [50|60|70] [90|100]         internal pages
  leaves, sorted and linked left to right:
  (5,ctid)(8,ctid) -> (10,ctid)(12,ctid) -> ...
```

Range queries use the leaf links: for `created_at BETWEEN x AND y` the engine descends once and walks right until the key exceeds y. The same walk yields sorted output, which is why an index on `(user_id, created_at)` satisfies `ORDER BY created_at` with no Sort node. Postgres stores one entry per heap tuple version, so UPDATE churn bloats indexes until VACUUM removes dead entries.

**Follow-ups they will ask:**
- Why not a hash index?: Equality only, no range scans or ordering, so B-tree is the default.
- Does the index store the row?: Not in Postgres; it stores key plus ctid, so non-covering lookups also fetch the heap page, which is where random I/O comes from.

**Mistakes to avoid:**
- Calling it a binary tree; nodes hold hundreds of keys, which is why it is so shallow.
- Saying an index makes "the query" fast. A filter on another column, or a function wrapped around the column, never touches it.

### Q. What is the difference between a clustered and non-clustered index?
**Short answer (45 seconds):** A clustered index determines the physical order of the table: the row data lives in the leaf pages of that index, so a table can have only one. A non-clustered, or secondary, index is a separate structure whose leaves point back at the row. In MySQL InnoDB and SQL Server the primary key is clustered. Postgres has no clustered indexes: tables are heaps, and every index, including the primary key, is secondary.

**Deeper explanation:** In InnoDB a secondary index leaf stores the indexed value plus the primary key, so a secondary lookup does two B-tree descents: the secondary index to find the primary key, then the clustered index to reach the row. Wide primary keys therefore inflate every secondary index, and random UUIDv4 keys split pages all over the clustered tree, while auto-increment or time-ordered keys (UUIDv7, ULID) append to the right-most leaf.

In Postgres, index leaves store the ctid (page number and item offset). `CLUSTER orders USING orders_created_idx` rewrites the table once in index order but does not maintain that order as rows arrive, so it is a one-off optimisation for range-heavy reads.

| | InnoDB (MySQL) | Postgres |
|---|---|---|
| Table storage | clustered primary key B-tree | heap, unordered |
| Secondary index leaf | key + primary key value | key + ctid |
| Lookup via secondary | two descents | one descent + heap fetch |

**Follow-ups they will ask:**
- Why do random UUIDs hurt InnoDB more than Postgres?: They split pages across the clustered tree and evict hot buffer pool pages; in Postgres they only churn the primary key index.
- What does CLUSTER cost?: An ACCESS EXCLUSIVE lock and a full rewrite, so use a maintenance window or pg_repack.

**Mistakes to avoid:**
- Stating "the primary key is the clustered index" as universal. True for InnoDB and SQL Server, not Postgres.
- Treating Postgres `CLUSTER` as if it kept the table ordered afterwards.

### Q. What is a composite index? Explain the left-prefix rule.
**Short answer (45 seconds):** A composite index is one B-tree over several columns, sorted by the first column, then by the second within equal first values, and so on. Because of that ordering it can be searched efficiently only on a leading prefix: an index on `(a, b, c)` serves filters on `a`, on `a` and `b`, and on all three, but not on `b` or `c` alone. Order columns as equality filters first, then the range or ORDER BY column.

**Deeper explanation:** Think of a phone book sorted by last name, then first name. For the hot query

```sql
SELECT * FROM orders
WHERE user_id = 42 AND status = 'paid'
ORDER BY created_at DESC LIMIT 20;
```

the ideal index is `(user_id, status, created_at DESC)`: equality on the first two columns pins a contiguous run of entries already sorted by `created_at`, so the planner reads twenty and stops. Put `created_at` first and it must walk orders by time and filter, or sort.

A range predicate ends the useful prefix. With `(user_id, created_at, status)` the index narrows on `user_id` and the date range, but `status` is checked entry by entry inside that range, because entries are not grouped by status there. Postgres can still use a B-tree when only non-leading columns are constrained, but it scans the whole index, which rarely beats a sequential scan. An index on `(a, b)` also serves lookups on `a` alone, so a separate `(a)` index is usually redundant.

**Follow-ups they will ask:**
- Does `(a, b)` help `WHERE b = ? AND a = ?`?: Yes, predicate order in SQL is irrelevant; only the index column order matters.
- How does MongoDB handle this?: Compound indexes follow the same prefix rule, with the documented ESR guideline: Equality, Sort, Range.

**Mistakes to avoid:**
- One single-column index per filtered column, hoping the planner combines them. Postgres can bitmap-AND them, but one composite index is far cheaper.
- Putting the range column first because "it narrows the most rows".

### Q. When would you NOT add an index?
**Short answer (45 seconds):** When the table is small enough that a sequential scan is cheaper anyway; when the column has very low selectivity, such as a boolean or a three-value status, so the planner would ignore it; when the table is write-heavy and the index would tax every INSERT and UPDATE for a rare query; and when an existing composite index already covers the access path. Each index is another B-tree to write, store, vacuum, and keep in cache.

**Deeper explanation:** The planner costs plans in page reads. On a table that fits in a few pages, descending an index and then fetching heap pages costs more than reading everything, so Postgres picks a Seq Scan regardless. Low selectivity has the same effect: if 60 percent of rows have `status = 'active'`, reaching them through an index means random access to most heap pages, which loses to a sequential read.

On write-heavy tables such as event logs or the chat message table an LLM product appends to constantly, every index adds page writes and WAL per insert and can disable HOT updates. Check what is actually used before adding more:

```sql
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes ORDER BY idx_scan ASC;
```

Often a partial or expression index, or a query rewrite that uses an existing composite index, is the better tool.

**Follow-ups they will ask:**
- When is a low-cardinality column still worth indexing?: As a partial index on the rare value, or as a trailing column that refines a selective prefix.
- Would you index a foreign key?: Almost always; without it, deleting a parent row scans the child table for the referential check.
- Adding an index to a busy table?: `CREATE INDEX CONCURRENTLY`, which does not block writes but leaves an INVALID index to drop if it fails.

**Mistakes to avoid:**
- "Index every column in the WHERE clause." Most are never chosen and all of them cost writes.
- Forgetting that Postgres still visits the heap for visibility, so a low-selectivity index can be slower than a scan.

### Q. What is a covering index?
**Short answer (45 seconds):** A covering index contains every column a query needs, so the engine answers the query from the index alone without touching the table; Postgres calls this an Index Only Scan. You build one by adding the selected columns to the key, or in Postgres with `INCLUDE`, which stores extra columns in the leaf pages without making them part of the sort order or the uniqueness check.

**Deeper explanation:** For `SELECT status, total FROM orders WHERE user_id = 42`, an index on `(user_id)` finds the entries fast but then does one random heap read per matching row to fetch the other two columns. With

```sql
CREATE INDEX orders_user_cover ON orders (user_id) INCLUDE (status, total);
```

the planner can choose an Index Only Scan, and EXPLAIN ANALYZE reports `Heap Fetches: 0` when it fully succeeds. The Postgres twist is visibility: the index carries no transaction information, so for each entry the engine checks the visibility map to see whether the heap page is marked all-visible; if the page changed recently and has not been vacuumed, it must fetch the tuple anyway. Covering indexes therefore pay off on well-vacuumed tables, and a high Heap Fetches count is a signal to tune autovacuum.

In InnoDB the clustered index is covering by definition and every secondary index implicitly includes the primary key, so `SELECT id FROM users WHERE email = ?` is covered by an index on `email`.

**Follow-ups they will ask:**
- Why INCLUDE rather than widening the key?: The key stays narrow, uniqueness applies to key columns only, and included columns need no B-tree operator class.
- Downsides?: A wider index, more write cost, and it only helps queries selecting exactly those columns.
- How do you confirm it worked?: EXPLAIN (ANALYZE, BUFFERS) shows Index Only Scan with a low Heap Fetches count.

**Mistakes to avoid:**
- Claiming Postgres never touches the heap with a covering index; the visibility map check means it may.
- Covering `SELECT *` by stuffing every column into an index, which duplicates the table.

### Q. How do you diagnose a slow query in production?
**Short answer (45 seconds):** First find which query is actually slow in aggregate, from pg_stat_statements or the slow query log, instead of guessing. Then run EXPLAIN (ANALYZE, BUFFERS) against production-like data and read the plan for the node where time goes: a sequential scan on a big table, a nested loop fed by bad estimates, a sort spilling to disk, or far more buffer reads than hits. Fix the cause, re-explain, and confirm in pg_stat_statements that the mean time dropped.

**Deeper explanation:**

```sql
-- which statements cost the most overall?
SELECT calls, round(mean_exec_time) AS mean_ms, round(total_exec_time) AS total_ms,
       left(query, 80) AS query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE user_id = 42 AND status = 'paid'
ORDER BY created_at DESC LIMIT 20;
```

Read the plan from the innermost node outward. A large gap between estimated and actual rows means stale statistics (run ANALYZE) or correlated columns the planner cannot model (`CREATE STATISTICS`). `Buffers: shared hit=... read=...` with a large read count means the data was not cached. `Sort Method: external merge Disk` means work_mem was too small.

Then look outside the plan: `pg_stat_activity` for lock waits, `n_dead_tup` for bloat, and whether the app issues 200 fast queries in a loop (N+1) rather than one slow one. pg_stat_statements needs `shared_preload_libraries` plus `CREATE EXTENSION`; `auto_explain` logs the plan of every statement over a threshold without you reproducing it.

**Follow-ups they will ask:**
- Estimated 1 row, actual 50,000?: Stale statistics after a bulk load, or a correlated predicate; ANALYZE first, then extended statistics.
- The index exists but the planner skips it?: A function or cast on the column, low selectivity, a tiny table, or a type mismatch.
- Is EXPLAIN ANALYZE safe in production?: It executes the statement, so wrap writes in a transaction you ROLLBACK, and prefer auto_explain for ongoing visibility.

**Mistakes to avoid:**
- Plain EXPLAIN and trusting estimates; only ANALYZE shows actual rows and timing.
- Jumping to "add an index" before checking which query matters in aggregate.

### Q. What is index cardinality and why does it matter for query planning?
**Short answer (45 seconds):** Cardinality is the number of distinct values in an indexed column relative to the row count. High cardinality (email, order id) means each index entry points at very few rows, so the index is selective and worth using. Low cardinality (boolean, country, status) means each value matches a large share of the table, so the planner usually prefers a sequential scan.

**Deeper explanation:** The planner uses statistics that ANALYZE collects into pg_stats: `n_distinct`, `most_common_vals` with frequencies, a histogram of the rest, and `correlation` between index order and physical order. For `WHERE status = 'pending'` it multiplies the frequency of 'pending' by the row count, then costs an index scan (random reads) against a sequential scan and takes the cheaper.

```sql
SELECT attname, n_distinct, most_common_vals, most_common_freqs, correlation
FROM pg_stats WHERE tablename = 'orders';
```

Two consequences. If 'pending' is 0.5 percent of rows and 'completed' is 90 percent, the same index is excellent for one value and useless for the other; a partial index on `status = 'pending'` is tiny and always the right shape. When statistics are stale or columns are correlated (city and country), the planner underestimates rows and picks nested loops over thousands of rows it expected to be one. `ALTER TABLE orders ALTER COLUMN status SET STATISTICS 1000` enlarges the sample for a skewed column; `CREATE STATISTICS (dependencies)` teaches it about correlated columns.

**Follow-ups they will ask:**
- Does a low-cardinality column ever belong in an index?: Yes, as a trailing composite column or a partial index on the rare value.
- What does a negative n_distinct mean?: A ratio of the row count; -1 means every row is distinct and the estimate scales with the table.
- How often are statistics refreshed?: Autovacuum analyzes after roughly 10 percent of rows change by default, so ANALYZE yourself after bulk loads.

**Mistakes to avoid:**
- Treating cardinality as fixed; it is a property of the data and drifts.
- Declaring "the planner is broken" when the column had too few distinct values to make the index worthwhile.

### Q. How does an index affect INSERT, UPDATE, and DELETE performance?
**Short answer (45 seconds):** Every index is another B-tree to keep in sync. Each INSERT writes one entry per index, each DELETE leaves a dead entry per index for VACUUM, and each UPDATE in Postgres creates a new row version and, unless it qualifies as a HOT update, inserts a new entry into every index. The cost is extra page writes, WAL, random I/O, and cache pressure, and it scales with the number of indexes on the table.

**Deeper explanation:** Postgres uses MVCC: UPDATE never changes a row in place; it writes a new tuple version and marks the old one dead. If no indexed column changed and the new version fits on the same heap page, the update is HOT (heap-only tuple): index entries keep pointing at the old tuple, which chains to the new one, and no index is touched. Change an indexed column, or run out of page space, and every index gets a new entry. That is why indexing `updated_at` or `last_seen_at` is expensive, and why a `fillfactor` below 100 raises the HOT rate on update-heavy tables.

```sql
SELECT n_tup_upd, n_tup_hot_upd,
       round(100.0 * n_tup_hot_upd / nullif(n_tup_upd, 0), 1) AS hot_pct
FROM pg_stat_user_tables WHERE relname = 'sessions';
```

DELETE marks tuples dead and the index entries stay until VACUUM removes them, so delete churn with infrequent vacuum means index bloat. For bulk loads, drop the indexes, COPY, then build them once: one sort beats millions of individual insertions.

**Follow-ups they will ask:**
- Why did updates slow down after indexing `updated_at`?: Every update changes that column, so no update can be HOT and every index receives a new entry.
- How do you load 50 million rows fast?: COPY into a table without indexes, create them afterwards, then ANALYZE.
- Index bloat?: Dead entries and half-empty pages from churn; `REINDEX CONCURRENTLY` rebuilds without blocking.

**Mistakes to avoid:**
- Saying indexes only affect reads.
- Forgetting MVCC: a Postgres UPDATE costs like an INSERT in every index unless it is HOT.

### Practice
- Build an `orders` table with five million rows from `generate_series`, run the user/status/created_at query with no index, a single-column index, and a composite index, and save the EXPLAIN (ANALYZE, BUFFERS) output of each so you can quote the difference.
- Enable pg_stat_statements locally, write a small Express or FastAPI endpoint with an intentional N+1 pattern, and find it from pg_stat_statements alone before looking at the code.
- Index an `updated_at` column, run 100k updates, compare `n_tup_hot_upd` before and after, then set `fillfactor = 70` and repeat.
- Say it out loud: in under two minutes, explain why the planner skipped your index on `status` and what you would do instead.

## Transactions & Isolation Levels

> Most candidates can recite ACID and name four isolation levels. Far fewer can say what level their production database runs at by default, which anomaly that leaves open, and how that anomaly turns into a real bug such as a double booking or a negative balance. Interviewers push for exactly that. A strong answer names the default (READ COMMITTED in Postgres, REPEATABLE READ in InnoDB), describes a lost update you have actually seen, and explains how you closed it with `SELECT ... FOR UPDATE`, a version column, a unique constraint, or SERIALIZABLE with a retry loop.

### Concepts you must understand
- Atomicity means all or nothing per transaction; durability means a committed transaction survives a crash because its WAL records reach disk before COMMIT returns.
- Isolation is a spectrum: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE, each closing more anomalies at more cost.
- Postgres defaults to READ COMMITTED and never allows dirty reads; its REPEATABLE READ is snapshot isolation that also blocks phantoms; InnoDB defaults to REPEATABLE READ and uses gap locks.
- The anomalies to name: dirty read, non-repeatable read, phantom read, lost update, and write skew, the one only SERIALIZABLE prevents.
- MVCC lets readers and writers avoid blocking each other: each statement or transaction sees a snapshot, and writers block only other writers of the same row.
- Pessimistic locking (`SELECT ... FOR UPDATE`) serialises access up front; optimistic locking (a version column checked in the UPDATE) detects conflicts at write time and retries.
- Deadlocks are detected by the database (Postgres aborts one transaction after `deadlock_timeout`, one second by default); you prevent them with consistent lock ordering and short transactions.
- Postgres SERIALIZABLE (SSI) takes no blocking locks; it aborts conflicting transactions with SQLSTATE 40001, so the application must retry.
- Two-phase commit gives atomic commit across several resources but blocks if the coordinator dies; the outbox pattern and sagas are the usual alternatives between services.
- Savepoints give partial rollback inside a transaction, which is how you recover from an expected error without losing earlier work, especially in Postgres where any error aborts the whole transaction.

### Q. What are ACID properties? Explain each one with a real example.
**Short answer (45 seconds):** ACID is what a transaction guarantees. Atomicity: all statements commit or none do, so a transfer never debits without crediting. Consistency: the database moves between valid states, with constraints such as `balance >= 0` and foreign keys enforced. Isolation: concurrent transactions do not see each other's intermediate state, to the degree the isolation level specifies. Durability: once COMMIT returns, the change survives a crash because it reached the write-ahead log first.

**Deeper explanation:** A checkout in Node with `pg`:

```js
const client = await pool.connect();
try {
  await client.query('BEGIN');
  await client.query(
    'UPDATE inventory SET qty = qty - $1 WHERE sku = $2 AND qty >= $1', [n, sku]);
  await client.query(
    'INSERT INTO orders (user_id, sku, qty) VALUES ($1, $2, $3)', [uid, sku, n]);
  await client.query('COMMIT');
} catch (e) {
  await client.query('ROLLBACK');
  throw e;
} finally {
  client.release();
}
```

Atomicity makes ROLLBACK meaningful: if the INSERT fails, the decrement disappears with it. Consistency is partly the database's job (a CHECK constraint `qty >= 0` rejects an oversell even if someone removes the WHERE guard) and partly yours, for rules the schema cannot express. Isolation decides what a concurrent checkout sees: under READ COMMITTED its UPDATE on the same row waits for the first to commit, then re-evaluates `qty >= $1` against the new value, which is why the guard is correct. Durability comes from the WAL: Postgres flushes the commit record before acknowledging; `synchronous_commit = off` trades a small loss window for throughput.

**Follow-ups they will ask:**
- Is MongoDB ACID?: Single-document writes are atomic; multi-document transactions exist on replica sets and sharded clusters with snapshot isolation.
- Where is the transaction in Prisma?: `prisma.$transaction([...])` for a batch, or the interactive `$transaction(async (tx) => ...)`, which maps to BEGIN and COMMIT on one connection.
- Does durability cover replicas?: Only the primary's disk by default; cross-node durability needs synchronous replication (`synchronous_standby_names`).

**Mistakes to avoid:**
- Explaining Consistency as "replicas agree". That is the CAP meaning, not the ACID one.
- Forgetting `release()` in `finally`, leaking a pooled connection with an open transaction.

### Q. What are the 4 isolation levels? What problem does each one prevent?
**Short answer (45 seconds):** READ UNCOMMITTED allows dirty reads of uncommitted data. READ COMMITTED prevents them: each statement sees only data committed before it started. REPEATABLE READ also prevents non-repeatable reads: the whole transaction sees one snapshot. SERIALIZABLE prevents everything, including phantoms and write skew, by guaranteeing a result equivalent to some serial order. Postgres defaults to READ COMMITTED, InnoDB to REPEATABLE READ.

**Deeper explanation:**

| Level | Dirty read | Non-repeatable | Phantom | Write skew |
|---|---|---|---|---|
| READ UNCOMMITTED | allowed (never in Postgres) | allowed | allowed | allowed |
| READ COMMITTED | prevented | allowed | allowed | allowed |
| REPEATABLE READ | prevented | prevented | standard allows; Postgres prevents | allowed |
| SERIALIZABLE | prevented | prevented | prevented | prevented |

Postgres has three distinct behaviours: READ UNCOMMITTED acts as READ COMMITTED, and REPEATABLE READ is snapshot isolation, which also stops phantoms because the snapshot is fixed at the first statement. What it misses is write skew: two transactions read overlapping rows, decide, and write to different rows, and together they break an invariant neither broke alone (two on-call doctors both see "two on call" and both leave). Only SERIALIZABLE catches that.

```sql
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT sum(amount) FROM ledger WHERE account_id = 7;  -- stable for the whole transaction
COMMIT;
```

InnoDB's REPEATABLE READ differs: locking reads (`FOR UPDATE`) see the latest committed rows and take gap locks, so identical code can behave differently on the two engines.

**Follow-ups they will ask:**
- What does your app run at today?: READ COMMITTED on Postgres unless changed, which leaves lost updates on read-modify-write open.
- Under Postgres REPEATABLE READ, you UPDATE a row changed after your snapshot?: Error 40001, "could not serialize access due to concurrent update"; you retry.

**Mistakes to avoid:**
- Saying REPEATABLE READ allows phantoms in Postgres. The standard permits them; Postgres does not produce them.
- Assuming READ COMMITTED protects read-modify-write. Two transactions can both read `qty = 1` and both decrement.

### Q. What is a dirty read, phantom read, and non-repeatable read?
**Short answer (45 seconds):** A dirty read sees another transaction's uncommitted change, which may later be rolled back. A non-repeatable read reads the same row twice in one transaction and gets different values because someone committed an update in between. A phantom read runs the same range query twice and gets a different set of rows because someone committed a matching insert or delete. They scale up in scope: a value, a row, a set of rows.

**Deeper explanation:**

```text
Non-repeatable read (READ COMMITTED):
  T1: SELECT balance FROM acct WHERE id = 1;            -> 100
  T2: UPDATE acct SET balance = 50 WHERE id = 1; COMMIT;
  T1: SELECT balance FROM acct WHERE id = 1;            -> 50

Phantom read:
  T1: SELECT count(*) FROM bookings WHERE room = 7 AND day = '2026-11-01';  -> 0
  T2: INSERT INTO bookings (room, day) VALUES (7, '2026-11-01'); COMMIT;
  T1: same query                                                           -> 1
```

The damage comes from check-then-act. Under READ COMMITTED both transactions count zero, both insert, and the room is double booked. Postgres REPEATABLE READ fixes the read (both still see zero) but not the outcome, because each insert is a new row that conflicts with nothing; that is write skew, which needs SERIALIZABLE or, far better, a unique constraint on `(room, day)`.

Dirty reads never happen in Postgres at any level; you would only see one on MySQL under READ UNCOMMITTED. Non-repeatable reads matter most for read, compute, write-back code: by the time you write, the value you relied on may be gone. That is the lost update, which `SELECT ... FOR UPDATE` and version columns prevent.

**Follow-ups they will ask:**
- Which level fixes which?: READ COMMITTED stops dirty reads; REPEATABLE READ stops non-repeatable reads (and phantoms in Postgres); SERIALIZABLE stops write skew.
- Is a lost update one of these?: No, a fourth anomaly; Postgres snapshot isolation detects it with 40001, READ COMMITTED does not.

**Mistakes to avoid:**
- Mixing up non-repeatable (one row's value changes) with phantom (the set of rows changes).
- Claiming to have seen dirty reads on Postgres.

### Q. What is a deadlock? How do you detect and prevent one?
**Short answer (45 seconds):** A deadlock is two or more transactions each waiting for a lock the other holds: T1 locks row A and wants B, T2 locks B and wants A. Postgres detects it: after a transaction has waited `deadlock_timeout` (one second by default) it checks the wait-for graph for a cycle and aborts one participant with SQLSTATE 40P01. Prevent it with consistent lock ordering, short transactions, and locking what you need up front.

**Deeper explanation:**

```text
T1: UPDATE accounts SET bal = bal - 10 WHERE id = 1;   -- locks row 1
T2: UPDATE accounts SET bal = bal - 10 WHERE id = 2;   -- locks row 2
T1: UPDATE accounts SET bal = bal + 10 WHERE id = 2;   -- waits for T2
T2: UPDATE accounts SET bal = bal + 10 WHERE id = 1;   -- waits for T1: deadlock
```

Postgres logs "deadlock detected" with both statements. The fix for transfers is a deterministic order (lower id first, whoever is the sender), or locking both rows at the start with `SELECT id FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE`.

Less obvious sources: batch UPDATEs walking the same rows in different orders; foreign key checks taking share locks on parent rows; and application-level deadlocks where a Node service holds a row lock while awaiting an HTTP call that needs that row, which the database cannot detect because half the wait is outside it. Never hold a transaction open across a call to another service or an LLM API.

**Follow-ups they will ask:**
- Which transaction is aborted?: The one that detected the cycle; there is no priority setting, so make every transaction retryable.
- How do you retry safely?: Catch 40P01, ROLLBACK, back off with jitter, rerun the whole transaction, and defer side effects until after commit.

**Mistakes to avoid:**
- "One big transaction", which widens the lock footprint and makes deadlocks likelier.
- Calling a long lock wait a deadlock. A deadlock needs a cycle.

### Q. What is the difference between optimistic and pessimistic locking?
**Short answer (45 seconds):** Pessimistic locking assumes conflicts are likely and locks the row before reading, typically `SELECT ... FOR UPDATE`, so other writers wait. Optimistic locking assumes conflicts are rare: read a version with the row, work without a lock, and write back with `UPDATE ... WHERE id = ? AND version = ?`; zero affected rows means someone else changed it, so retry. Pessimistic suits hot rows and short transactions; optimistic is the only option when the work spans user think time or an external call.

**Deeper explanation:**

```sql
-- pessimistic
BEGIN;
SELECT qty FROM inventory WHERE sku = 'A1' FOR UPDATE;
UPDATE inventory SET qty = qty - 1 WHERE sku = 'A1';
COMMIT;

-- optimistic
SELECT qty, version FROM inventory WHERE sku = 'A1';   -- 5, 12
UPDATE inventory SET qty = 4, version = 13
WHERE sku = 'A1' AND version = 12;                     -- rowCount 0 means retry
```

`FOR UPDATE` blocks other `FOR UPDATE`, UPDATE, and DELETE on those rows until commit, while plain SELECTs read freely under MVCC. `SKIP LOCKED` turns a jobs table into a work queue: `FOR UPDATE SKIP LOCKED LIMIT 10` lets ten workers grab different rows without blocking.

ORMs implement optimistic locking with a version column; in MongoDB you put the old version in the update filter, which is atomic per document. For an agent that reads state, calls an LLM for seconds, then writes, pessimistic is wrong, since you would hold a row lock across the model call; version the row instead.

**Follow-ups they will ask:**
- `FOR UPDATE` under REPEATABLE READ when the row changed after your snapshot?: Postgres raises 40001 rather than returning stale data.
- Isn't the optimistic UPDATE itself a race?: No, a single UPDATE re-checks its WHERE clause under the row lock, so exactly one writer wins.

**Mistakes to avoid:**
- Plain SELECT, compute in Node, UPDATE without a version check, and calling it optimistic locking.
- Holding `FOR UPDATE` across an external API call.

### Q. When would you use SERIALIZABLE isolation and what does it cost you?
**Short answer (45 seconds):** Use SERIALIZABLE when the invariant spans several rows and cannot be a constraint: at most N bookings per slot, or a ledger that must balance across rows. It guarantees the outcome equals some serial execution. In Postgres the cost is not blocking but aborts: transactions that would produce a non-serializable result fail with SQLSTATE 40001 and must be retried, plus CPU and memory for tracking read dependencies.

**Deeper explanation:** Postgres implements it as Serializable Snapshot Isolation (SSI): each transaction runs on a snapshot like REPEATABLE READ, and the engine tracks what each transaction read (SIReadLocks) to detect read-write dependency cycles, aborting one transaction when no serial order could explain the result. Nobody waits because of SSI, unlike lock-based implementations such as InnoDB's, where SELECTs take shared and range locks.

```js
async function serializable(pool, fn, attempts = 5) {
  for (let i = 0; ; i++) {
    const c = await pool.connect();
    try {
      await c.query('BEGIN ISOLATION LEVEL SERIALIZABLE');
      const out = await fn(c);
      await c.query('COMMIT');
      return out;
    } catch (e) {
      await c.query('ROLLBACK');
      if (e.code !== '40001' || i >= attempts - 1) throw e;
      await new Promise(r => setTimeout(r, 20 * 2 ** i));
    } finally { c.release(); }
  }
}
```

Costs to name: the retry loop wraps the whole operation, so side effects (emails, payment calls) move after commit; abort rates climb with contention and transaction length, so a hot counter row thrashes; and read-only transactions can abort too unless declared `READ ONLY DEFERRABLE`. Default to READ COMMITTED plus explicit locks or constraints; reserve SERIALIZABLE for transactions whose conflicts you cannot enumerate.

**Follow-ups they will ask:**
- Why not REPEATABLE READ?: It prevents lost updates but not write skew, the multi-row invariant case.
- What does `SERIALIZABLE READ ONLY DEFERRABLE` do?: Waits for a snapshot guaranteed not to conflict, then runs with no abort risk; ideal for long reports.

**Mistakes to avoid:**
- Enabling it globally without handling 40001, so users see random failures under load.
- Describing Postgres SERIALIZABLE as "it locks the tables".

### Q. What is a two-phase commit and what problem does it solve?
**Short answer (45 seconds):** Two-phase commit commits one logical transaction across several independent resources, such as two databases or a database and a broker, so that all commit or none do. A coordinator asks each participant to PREPARE, meaning write everything durably and promise it can commit; only when all vote yes does it send COMMIT, and any no or timeout means ABORT everywhere. It solves atomicity across systems, at the cost of blocking: a prepared participant holds its locks until the coordinator decides.

**Deeper explanation:**

```text
Coordinator            DB A                 DB B
    |--- PREPARE ------->|                    |
    |--- PREPARE ------------------------->   |
    |<-- YES ------------|                    |
    |<-- YES ------------------------------   |
    |  log the COMMIT decision                |
    |--- COMMIT -------->|                    |
    |--- COMMIT -------------------------->   |
```

Postgres supports the participant role natively: `PREPARE TRANSACTION 'tx1'` writes the transaction to disk and keeps its locks; `COMMIT PREPARED 'tx1'` or `ROLLBACK PREPARED 'tx1'` finishes it (needs `max_prepared_transactions` above zero).

The failure mode is why people avoid it: if the coordinator crashes after participants prepared, they sit "in doubt", holding row locks until it recovers or an operator resolves them by hand (`pg_prepared_xacts` lists them), and the slowest participant gates every commit. Between services, the alternatives are the transactional outbox (write the event in the same database transaction as the change; a relay publishes it to Kafka) and sagas (local transactions with compensating actions). Both give eventual consistency instead of atomicity, which is almost always the right trade for "save the order and notify the warehouse".

**Follow-ups they will ask:**
- What does 2PC not solve?: Coordinator failure during commit (blocking), and isolation across systems; it provides atomic commit only.
- 2PC versus a saga?: 2PC is atomic and blocking; a saga is committed local steps undone by compensations, never atomic but never blocked on a peer.

**Mistakes to avoid:**
- Proposing 2PC between Postgres and a third-party payment API; the API cannot prepare. Use idempotency keys and reconciliation.
- Confusing two-phase commit with two-phase locking, a concurrency control technique inside one database.

### Q. What is a savepoint? When would you use one?
**Short answer (45 seconds):** A savepoint is a named marker inside an open transaction that you can roll back to without aborting the whole transaction: `SAVEPOINT s1; ... ROLLBACK TO SAVEPOINT s1;` undoes only the work after the marker and leaves the transaction live. Use it when part of a transaction may legitimately fail: try an insert that may hit a unique violation, recover, and keep everything before it. It matters most in Postgres, where any error puts the transaction into an aborted state until ROLLBACK.

**Deeper explanation:**

```sql
BEGIN;
INSERT INTO orders (id, user_id) VALUES (1001, 42);
SAVEPOINT before_tag;
INSERT INTO order_tags (order_id, tag) VALUES (1001, 'gift');  -- may violate unique
ROLLBACK TO SAVEPOINT before_tag;   -- on error: order insert survives, transaction open
INSERT INTO order_audit (order_id, note) VALUES (1001, 'tag skipped');
COMMIT;
```

Postgres implements savepoints as subtransactions with their own transaction ids, and that has a known cost: more than 64 subtransactions in one transaction overflow a per-session cache and force other sessions to consult the shared pg_subtrans structure. Savepoints are for a handful of guarded steps, not a per-row loop over a million rows.

Typical uses: batch imports where one bad row must not kill the batch but the batch still commits as a unit, and try-the-fast-path-then-fall-back logic. When the expected error is a unique violation, `INSERT ... ON CONFLICT DO NOTHING` is cheaper and clearer than a savepoint plus catch.

**Follow-ups they will ask:**
- Why does Postgres need savepoints more than MySQL?: In Postgres any error aborts the whole transaction; InnoDB rolls back only the failing statement.
- What does `RELEASE SAVEPOINT` do?: Discards the marker and merges the work into the parent; you cannot roll back to it afterwards.
- Are locks released on rollback to a savepoint?: Locks taken after it are released; earlier ones remain.

**Mistakes to avoid:**
- A savepoint per row in a big loop, which hits the subtransaction overflow problem.
- Catching the error in Node and sending more statements without rolling back to a savepoint, then being surprised that every query fails.

### Practice
- Open two psql sessions and run the double-booking scenario under READ COMMITTED, REPEATABLE READ, and SERIALIZABLE; write down what each session saw and which transaction failed with 40001.
- Reproduce a deadlock with two transfers in opposite order, read the "deadlock detected" log line, then fix it with `ORDER BY id FOR UPDATE` and confirm it is gone.
- Implement optimistic locking with a version column in a small Express endpoint, hit it with 50 concurrent requests from a `Promise.all` loop, and count the retries.
- Say it out loud: "Our Postgres runs READ COMMITTED, which means..." and finish with the exact bug that leaves open and how your code prevents it.
