## SQL Interview Patterns [Core]

> SQL rounds are hands-on: a schema, a business question and a short time box. Interviewers watch whether you pin down what one output row means, build the query in small readable steps, choose the right join and window function, and handle ties, NULLs, duplicates and time zones without being prompted. A weak answer is one large query that runs but answers a slightly different question. A strong answer restates the question as a result shape, writes short CTEs, checks edge cases out loud, and knows how to make the query fast with EXPLAIN ANALYZE and the right index.

### In plain words
SQL interview questions are business questions in disguise: who are our best customers, which ad channel paid off, did the campaign work. Picture a spreadsheet with millions of rows. GROUP BY makes subtotals, a JOIN looks up the matching row in another sheet, and a window function writes a rank or running total into a new column without squashing the rows together. Most wrong answers come from not deciding what one row of the result should be, for example one row per customer or one row per customer per day. Once that is clear, the query is a few small steps stacked on top of each other.

### From your saved posts
- jam.with.ai (carousel): the SQL Interview Prep playlist (8 videos) on the Aced, formerly Exponent, YouTube channel, [youtube.com/@aced_io](https://www.youtube.com/@aced_io), works through hands-on problems such as most user orders, analysing marketing channels, upsell campaign impact and departments with the highest revenue, plus query optimisation.

### Concepts you must understand
- Grain first: decide what one output row represents (per customer, per customer per day) before writing a line; most wrong answers are grain mistakes.
- Logical order is FROM and JOIN, WHERE, GROUP BY, HAVING, then the SELECT list (window functions included), DISTINCT, ORDER BY, LIMIT; that is why a window result can only be filtered in an outer query or CTE.
- INNER JOIN drops unmatched rows, LEFT JOIN keeps them with NULLs, and joining a table to a one-to-many child before aggregating multiplies rows and inflates SUMs.
- Window functions compute across related rows without collapsing them: ROW_NUMBER, RANK and DENSE_RANK for top-N, LAG and LEAD for change over time, SUM() OVER () for shares and running totals.
- NULL rules: COUNT(col) and AVG skip NULLs, COUNT(*) does not, NULL = NULL is not true, and NOT IN against a subquery that returns a NULL returns no rows.
- Time: use half-open ranges (>= start AND < end), date_trunc for buckets, and the business time zone, because date_trunc on a timestamptz uses the session's TimeZone setting.
- CTEs make a query readable and checkable step by step; since Postgres 12 a non-recursive, side-effect-free CTE referenced once is inlined, so it no longer blocks optimisation by default.
- Performance: EXPLAIN (ANALYZE, BUFFERS), indexes that match filter and join columns, no functions wrapped around indexed columns in WHERE, and pre-aggregated tables for dashboards.

### Q. Find the top 3 customers by order count in each country.
**Short answer (45 seconds):** Aggregate orders per customer in a CTE, rank customers within each country with a window function partitioned by country and ordered by order count, then filter the rank in an outer query. The real question is ties: ROW_NUMBER returns exactly three rows and breaks ties arbitrarily unless I add a tiebreaker, RANK leaves gaps after ties, and DENSE_RANK returns everyone within the top three distinct counts. I ask which one the business wants.

**Deeper explanation:** Assume `customers(id, name, country)` and `orders(id, customer_id, status, created_at)` with status NOT NULL.

```sql
WITH counts AS (
  SELECT c.country, c.id AS customer_id, c.name, COUNT(*) AS order_count
  FROM customers c
  JOIN orders o ON o.customer_id = c.id
  WHERE o.status <> 'cancelled'
  GROUP BY c.country, c.id, c.name
),
ranked AS (
  SELECT *, DENSE_RANK() OVER (PARTITION BY country ORDER BY order_count DESC) AS rnk
  FROM counts
)
SELECT country, customer_id, name, order_count, rnk
FROM ranked
WHERE rnk <= 3
ORDER BY country, rnk, customer_id;
```

| order_count | ROW_NUMBER | RANK | DENSE_RANK |
|---|---|---|---|
| 10 | 1 | 1 | 1 |
| 9 | 2 | 2 | 2 |
| 9 | 3 | 2 | 2 |
| 8 | 4 | 4 | 3 |

With `rnk <= 3`, ROW_NUMBER keeps three rows, RANK keeps three (10, 9, 9) and DENSE_RANK keeps four (10, 9, 9, 8). Group by customer id, not only name, or namesakes merge. If customers with zero orders must appear, use a LEFT JOIN, move the status condition into the ON clause and count `o.id`; left in WHERE, it silently turns the LEFT JOIN back into an inner join.

**Follow-ups they will ask:**
- Exactly three per country, deterministically?: ROW_NUMBER with a tiebreaker, `ORDER BY order_count DESC, customer_id`.
- Another way without window functions?: A LATERAL subquery per country with ORDER BY and LIMIT 3.
- How do you make it fast?: The aggregate reads every qualifying order, so a dashboard should read a pre-aggregated per-customer count.

**Mistakes to avoid:**
- Filtering on `rnk` in the same SELECT that defines it; a window result needs an outer query.
- Picking ROW_NUMBER without mentioning that ties are dropped arbitrarily.

### Q. Which marketing channel brought the most revenue last month, and what share of total?
**Short answer (45 seconds):** I clarify three things first: attribution (the order's last-touch channel or the customer's acquisition channel), what counts as revenue (paid orders, net of refunds or not), and which time zone defines "last month". Then a CTE for the month boundaries, a CTE that sums revenue per channel with a LEFT JOIN so unattributed orders are kept, and an outer query that computes each channel's share with a window SUM over all rows.

**Deeper explanation:** Assume `orders(id, channel_id, amount numeric, status, created_at timestamptz)` and `channels(id, name)`.

```sql
SET TIME ZONE 'Asia/Kolkata';   -- date_trunc on timestamptz uses the session time zone

WITH bounds AS (
  SELECT date_trunc('month', now()) - interval '1 month' AS start_at,
         date_trunc('month', now())                      AS end_at
),
by_channel AS (
  SELECT COALESCE(ch.name, 'unattributed') AS channel, SUM(o.amount) AS revenue
  FROM orders o
  CROSS JOIN bounds b
  LEFT JOIN channels ch ON ch.id = o.channel_id
  WHERE o.status = 'paid'
    AND o.created_at >= b.start_at AND o.created_at < b.end_at
  GROUP BY 1
)
SELECT channel, revenue,
       ROUND(100 * revenue / NULLIF(SUM(revenue) OVER (), 0), 2) AS pct_of_total
FROM by_channel
ORDER BY revenue DESC;
```

`SUM(revenue) OVER ()` sees every row of the grouped result, so each channel's share comes out in one pass, and `NULLIF` avoids a division-by-zero error in an empty month. The half-open range covers the whole last day, which `BETWEEN '2026-09-01' AND '2026-09-30'` would not for timestamps. If the question is strictly "which channel", add `RANK() OVER (ORDER BY revenue DESC)` and keep rank 1, so a tie returns both channels.

**Follow-ups they will ask:**
- Different attribution models?: First-touch, last-touch and multi-touch can rank channels differently; state which one the numbers use.
- Refunds?: Subtract them in the month of the refund or of the order, whichever finance uses, and say which.
- Month over month?: Group by `date_trunc('month', created_at)` too and use `LAG(revenue) OVER (PARTITION BY channel ORDER BY month)`.

**Mistakes to avoid:**
- BETWEEN on timestamps, which silently drops most of the last day.
- Joining orders to a one-to-many touches table before summing, which counts each order's revenue several times.

### Q. Measure the impact of an upsell campaign on spend.
**Short answer (45 seconds):** "Spend after minus spend before for users who got the campaign" is not the impact, because seasonality, regression to the mean and targeting all move that number; targeted users were often picked because they already spend more. I need a comparison group, ideally a random holdout that was eligible but not sent. Then I compare the change in each group over equal windows around the send date, a difference in differences, and report it with a confidence interval.

**Deeper explanation:** Assume `campaign_assignments(user_id, grp, assigned_at)`, where control users carry the date they would have been sent, plus `orders(user_id, amount, created_at)`.

```sql
WITH per_user AS (
  SELECT a.user_id, a.grp,
         COALESCE(SUM(o.amount) FILTER (WHERE o.created_at >= a.assigned_at - interval '30 days'
                                          AND o.created_at <  a.assigned_at), 0) AS before_spend,
         COALESCE(SUM(o.amount) FILTER (WHERE o.created_at >= a.assigned_at
                                          AND o.created_at <  a.assigned_at + interval '30 days'), 0) AS after_spend
  FROM campaign_assignments a
  LEFT JOIN orders o ON o.user_id = a.user_id
  WHERE a.assigned_at + interval '30 days' <= now()      -- full window observed
  GROUP BY a.user_id, a.grp
)
SELECT grp, COUNT(*) AS users,
       AVG(after_spend - before_spend)         AS avg_change,
       STDDEV_SAMP(after_spend - before_spend) AS sd_change
FROM per_user
GROUP BY grp;
```

The impact estimate is treatment `avg_change` minus control `avg_change`, and `users` with `sd_change` give the standard error for a confidence interval. The `COALESCE(..., 0)` matters: a user who bought nothing spent zero, and leaving them as NULL drops them from the average and inflates it. Spend is skewed, so also check the median change and whether a handful of large buyers drive the result.

**Follow-ups they will ask:**
- No holdout exists?: Build a matched control on prior spend, tenure and segment, or use users scheduled for a later wave, and say the estimate is weaker.
- Did the campaign only pull spend forward?: Extend the after window to 60 or 90 days and see whether the gap closes.
- Make it fast?: An index on `orders(user_id, created_at)` serves the per-user range lookups.

**Mistakes to avoid:**
- Treating users with no orders as missing instead of zero.
- Comparing targeted users with everyone else when the targeting picked high spenders.

### Q. Find departments whose revenue is above the company average.
**Short answer (45 seconds):** First clarify "company average": usually the average of department totals, not the average sale. Then there are three equivalent shapes: a scalar subquery in HAVING, a CTE of department totals compared with the average over that CTE, or a window AVG over the grouped rows. I default to the CTE or window version: readable, and the average comes from the same totals it is compared with.

**Deeper explanation:** Assume `sales(department_id, amount, sold_at)` and `departments(id, name)`.

```sql
-- CTE plus a scalar subquery over the CTE
WITH dept AS (
  SELECT department_id, SUM(amount) AS revenue
  FROM sales
  GROUP BY department_id
)
SELECT d.name, dept.revenue
FROM dept
JOIN departments d ON d.id = dept.department_id
WHERE dept.revenue > (SELECT AVG(revenue) FROM dept);

-- window AVG over the grouped rows
SELECT department_id, revenue, avg_revenue
FROM (
  SELECT department_id, SUM(amount) AS revenue,
         AVG(SUM(amount)) OVER () AS avg_revenue
  FROM sales
  GROUP BY department_id
) t
WHERE revenue > avg_revenue;
```

The pure subquery form is `HAVING SUM(amount) > (SELECT AVG(total) FROM (SELECT SUM(amount) AS total FROM sales GROUP BY department_id) x)`: correct, but it repeats the aggregation. `AVG(SUM(amount)) OVER ()` works because window functions run after GROUP BY, so the window sees one row per department. Two edge cases to raise: departments with no sales are absent from `sales`, so if they should pull the average down, start from `departments` with a LEFT JOIN and `COALESCE(SUM(amount), 0)`; and if a time window applies, filter once in the base CTE so totals and average use the same rows.

**Follow-ups they will ask:**
- Is the CTE slower?: Referenced twice, it is materialised by default in Postgres 12 and later, which is fine at department scale; check with EXPLAIN ANALYZE when it matters.
- Above average per year?: Group by department and year, and partition the window AVG by year.
- Above the median instead?: `percentile_cont(0.5) WITHIN GROUP (ORDER BY revenue)` over the department totals.

**Mistakes to avoid:**
- Comparing department totals with the average sale amount, which is a different question.
- Dropping departments with zero sales without asking whether they count.

### Q. Write a query for 7-day rolling active users and explain how you would make it fast.
**Short answer (45 seconds):** For each day D, count distinct users with at least one event from D minus 6 through D. Postgres does not support `COUNT(DISTINCT ...)` as a window function, so I generate the calendar with generate_series, reduce events to one row per user per active day, join each calendar day to its seven-day range and count distinct users. Speed comes from an index on the timestamp, a pre-aggregated daily-active table, and checking the plan.

**Deeper explanation:**

```sql
WITH days AS (
  SELECT d::date AS day
  FROM generate_series(current_date - 29, current_date - 1, interval '1 day') AS d
),
daily AS (                 -- one row per user per active day
  SELECT DISTINCT user_id, date_trunc('day', created_at)::date AS day
  FROM events
  WHERE created_at >= current_date - 35 AND created_at < current_date
)
SELECT days.day, COUNT(DISTINCT daily.user_id) AS active_users_7d
FROM days
LEFT JOIN daily ON daily.day BETWEEN days.day - 6 AND days.day
GROUP BY days.day
ORDER BY days.day;
```

The calendar guarantees a row for every day, with 0 when nobody was active. The lower bound is 35 days back because the earliest day needs the six days before it, and BETWEEN is safe here because both sides are dates. Day boundaries follow the session time zone, so set it to the business zone. To make it fast:
- `CREATE INDEX ON events (created_at, user_id)` serves the range scan; on a huge append-only table, a BRIN index on `created_at` is tiny and effective because rows arrive in time order.
- The real win is a `daily_active(day, user_id)` table filled once a day, so the rolling query reads far fewer rows than raw events.
- At very large scale, store a HyperLogLog sketch per day (the postgresql-hll extension) and union seven sketches for an approximate count.
- Compare `EXPLAIN (ANALYZE, BUFFERS)` before and after, reading rows and buffers, not just time.

**Follow-ups they will ask:**
- What counts as "active"?: Agree on the events; a background token refresh is not a user being active.
- Rolling seven days or calendar weeks?: Rolling smooths day-of-week effects; calendar weeks match finance reports.

**Mistakes to avoid:**
- Summing daily active users over seven days, which counts a user once per active day.
- Skipping the calendar, so days with zero activity vanish from the chart.

### Q. How do you approach a SQL question you have never seen in an interview?
**Short answer (45 seconds):** I restate the question as a result shape (one row per what, which columns, what order), ask the clarifying questions that change the answer (what counts, time window and time zone, how ties work), and check the keys to see which joins are one-to-many. Then I build it in small CTEs, filter, aggregate, rank, select, checking each step, and finish by walking edge cases out loud: NULLs, duplicates from joins, ties, entities with zero activity, range boundaries and time zones. Performance comes last, if there is time.

**Deeper explanation:**

```text
1 restate   "one row per customer per month, columns ..., sorted by ..."
2 clarify   cancelled or test orders? refunds? which time zone? ties?
3 inspect   primary keys, which joins fan out, nullable columns
4 build     one CTE per step: filter -> aggregate -> rank -> final select
5 edge      NULLs, duplicate rows from joins, ties, zero-activity rows, boundaries
6 speed     indexes on filter and join columns, EXPLAIN ANALYZE, pre-aggregation
```

Two traps catch most candidates. Fan-out: joining `orders` to `order_items` and then summing `orders.amount` counts each order once per item, so aggregate each child table in its own CTE and join the results. And `NOT IN` with NULLs: `WHERE id NOT IN (SELECT referrer_id FROM users)` returns no rows at all if any `referrer_id` is NULL, because the comparison becomes unknown; `NOT EXISTS` behaves as people expect. Write vague-schema assumptions as comments at the top (ids unique, status NOT NULL) so the interviewer can correct them early.

**Follow-ups they will ask:**
- Running out of time?: Finish a correct simple version, then say how you would extend it.
- How do you test without a database?: A few hand-made rows that include a tie, a NULL and a duplicate, with the expected output written next to them.
- When would you use a correlated subquery?: For EXISTS checks; for per-row aggregates, a join to a pre-aggregated CTE is usually clearer and faster.

**Mistakes to avoid:**
- Writing the whole query at once and debugging by staring at it.
- Using NOT IN against a nullable column.

### Practice
- Generate customers, orders, channels and events with `generate_series` and solve all six questions; save EXPLAIN (ANALYZE, BUFFERS) output for the rolling query before and after adding an index and a daily pre-aggregate.
- Build a dataset with deliberate ties and run the top 3 query with ROW_NUMBER, RANK and DENSE_RANK; explain the row-count difference.
- Run the campaign query on a random split of users who received nothing (an A/A test) and see how large a "difference" appears by chance.
- Say it out loud: talk through the marketing-channel question in three minutes, including the attribution, refund and time zone clarifications, before writing any SQL.

## Backend System Design Walkthroughs

### In plain words
A system design interview is like being asked to plan a new restaurant on a napkin in 45 minutes: how many guests, what is on the menu, where the kitchen goes, and what happens when the fridge breaks. Nobody expects the full blueprint; they want to watch how you think when the question is vague and the clock is running. You ask a few questions first, do quick back-of-the-envelope maths, draw the simplest thing that works, and then improve the part the interviewer cares about, explaining the trade-off each time. Practising out loud with mock interviews matters more than memorising diagrams.

### From your saved posts
- jam.with.ai (carousel): designing systems under pressure on a whiteboard in 45 minutes counts for more than Kaggle rank, GitHub stars or certificates.
- System Design Interview Prep playlist (44 videos) on the Aced, formerly Exponent, YouTube channel, [youtube.com/@aced_io](https://www.youtube.com/@aced_io): mock interviews and walkthroughs such as Google Docs, Uber Eats, a key-value store, a distributed LRU cache and a web crawler, plus API design, scalability and database choices.
