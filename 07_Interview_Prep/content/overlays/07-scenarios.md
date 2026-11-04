## The ML Lifecycle & MLOps Maturity

### Why it exists
Most models used to be built once in a notebook, copied to a server by hand and then forgotten, while the data they saw in production slowly moved away from the data they were trained on. Nobody could say which version was running, retraining happened when someone remembered, and a bad model was noticed only when a business number fell. MLOps treats the model as a system that keeps running: a loop of data, training, testing, deployment, monitoring and retraining, with automation and checks at each step. The cost is pipelines, tooling and clear ownership to maintain, so the right maturity level depends on how often the model changes and how expensive a bad version is.

## Experiment Tracking, Registry & Reproducibility

### Why it exists
Without tracking, the honest answer to "which model is in production and how was it built?" is often "we are not sure". Teams kept results in spreadsheets and files named like `final_v3_fixed.pkl`, so nobody could rebuild a model or explain a number months later. An experiment tracker records each run's code commit, data version, settings and metrics; a registry turns chosen runs into numbered versions with labels such as production; data versioning pins the exact snapshot used. The trade-off is discipline and storage, and even with every pin in place, GPU training is not always bit-for-bit repeatable.

## Model Serving & Deployment Patterns

### Why it exists
A trained model creates no value until it answers real requests reliably, within a latency budget, at a cost the business accepts. The early approach was a small web app on one server, replaced in place on each release, so a bad version reached every user at once and going back meant a rebuild. Serving patterns (containers, autoscaling, batch versus online inference) handle load and reliability, and rollout patterns (shadow, canary, blue/green) expose a new version to a small slice first with a quick way back. The price is infrastructure complexity, extra compute while two versions run side by side, and the need to split every metric by version.

## Monitoring ML Systems

### Why it exists
ML systems fail quietly: the service keeps returning 200 OK quickly while its predictions get worse, because the inputs changed or the world changed. Ordinary application monitoring watches errors and latency, so it misses this entirely. ML monitoring adds checks on input data quality, on shifts in input and prediction distributions, and on model performance once true labels arrive. The difficulty is that labels often arrive weeks late, statistical tests are noisy on large data, and alerts that fire without a clear action quickly teach the team to ignore them.

## Prompt Management & Versioning

### Why it exists
In an LLM feature the prompt is behavior: changing one sentence can change every answer the product gives. When prompts lived as strings in code or were edited live in a dashboard, nobody could say which wording produced a given answer, review a change before it shipped, or undo it quickly. Prompt management gives each prompt immutable versions, labels per environment, a review step and a version stamp on every model call. The cost is a second release channel next to code deployments, and unless the two are released and rolled back together, a rollback can restore only half of the system.

## Evaluation Pipelines in CI/CD

### Why it exists
LLM outputs vary from run to run and nothing fails to compile when a prompt gets worse, so "it looked fine on three examples" is how regressions reach users. An evaluation pipeline runs a fixed, versioned set of realistic cases through the candidate on every change, grades the outputs with code checks, model judges or people, and blocks the merge when quality drops, much like unit tests do for code. It turns opinions about a prompt into evidence. The costs are API spend on every run, a dataset that must be kept in step with real traffic, and judges that are models themselves and can be wrong.

## Observability & Tracing for LLM Apps

### Why it exists
One LLM request is a chain of steps (query rewriting, retrieval, one or more model calls, tool calls, formatting), and each step adds latency, cost and a chance to go wrong. With only per-service logs, a "wrong answer" or "slow answer" complaint turns into guesswork about which step failed. Tracing records every step of one request under a shared trace ID, with inputs, outputs, timings, token usage and the prompt and model versions used. The trade-off is that the trace store becomes a large copy of user data, so it needs redaction, access control, sampling and a retention limit.

## Governance, Security & Compliance

### Why it exists
LLM features read customer data, send it to outside providers and sometimes take actions, so buyers and regulators ask where the data goes, who can see it, how long it stays and who approved each change. Without deliberate controls, prompts, traces and provider calls become untracked copies of personal data, and a single leak can stop an enterprise deal or trigger legal notification duties. Governance builds data minimization, redaction, retention limits, audit trails and human approvals into the architecture instead of adding them after launch. The cost is slower launches, extra engineering and sometimes a narrower choice of models because of regional hosting rules.

## Feedback Loops & the Data Flywheel

### Why it exists
Eval sets written before launch cover only the cases the team imagined, and real users quickly find failures nobody predicted. Before feedback loops, those failures sat in support tickets and chat complaints that nobody connected to a specific prompt, model or retrieved document. A feedback loop captures signals such as ratings, edits and escalations, links each one to the exact trace, and turns the important ones into eval cases and later into training data. The costs are labeling time, consent and privacy rules for reusing user data, and bias, because the people who leave feedback are not a fair sample of all users.

## Cost Management & FinOps for AI

### Why it exists
LLM spend grows with every request and every token, so a prompt that adds context, an agent stuck in a loop or a broken prompt cache can double the bill overnight. With one shared API key the damage shows up weeks later as a single number on an invoice, and nobody can say which feature or customer caused it. FinOps for AI tags every call with feature and tenant, sets budgets, caps and alerts, and applies levers such as caching, shorter outputs and routing to smaller models. The trade-offs are tagging discipline, sometimes an extra network hop through a gateway, and the risk that cost cuts quietly lower quality unless each one is checked with evals.

## AIOps & Platform Engineering

### Why it exists
Once several teams ship AI features, each one tends to rebuild its own model client, tracing, eval scripts and budget checks, with different gaps in each, while on-call engineers face a growing stream of alerts from more systems. Platform engineering answers the first problem with a paved road: one approved gateway, tracing setup, eval harness and project template that product teams reuse. AIOps answers the second by applying machine learning or LLMs to operations data, grouping related alerts and suggesting likely causes. The cost is that the platform becomes a product with its own roadmap and can turn into a bottleneck, and AI help in operations must stop short of unreviewed changes to production.

## LLMOps Project Scenarios [Scenarios]

> Project and design scenarios in this area start underspecified on purpose: "we are shipping our first LLM feature", "finance wants cost per customer", "the bank's security team sent a questionnaire". Interviewers watch whether you clarify risk and constraints before naming tools, sequence the work so the riskiest gaps close first, define what one release contains and what gates it, estimate cost and effort with simple arithmetic, and say what you would measure to know it worked. A weak answer is a list of tools. A strong answer is an ordered plan with trade-offs, including what you would deliberately not build yet.

### Concepts you must understand
- Ask about risk first: does the output go to a person who reviews it (a draft) or straight to a customer or a system of record (an action)? That one answer sets how heavy the gates, reviews and audit trail must be.
- Ask who changes behavior and how: engineers in git, product staff in a prompt registry UI, a vendor moving a model alias. Every path that changes behavior needs the same gate.
- Define the release unit: prompt version, model ID and settings, tool schemas, output schema and retrieval config move together; versioning only the prompt leaves half the behavior unpinned.
- Funnel every model call through one place (a client wrapper or a gateway) early; tags, budgets, timeouts, usage capture and model config all hang off that choke point.
- Estimate before designing: monthly cost is roughly requests per day x 30 x (input tokens x input price + output tokens x output price), and one eval run costs items x samples x (candidate call + judge call).
- Buy versus build is mostly a data question: a hosted trace store or registry is fast to adopt, but residency and retention rules may force self-hosting.
- Name the measures up front: quality (eval scores by slice, online task success), operations (p95 latency, fallback and error rates), cost (cost per task, cache ratio) and process (time to roll back, regressions that escaped the gate).

### Q. Your team ships its first LLM feature, a reply drafter for support staff, in six weeks, and there is no LLMOps at all. What do you set up, and in what order?

**Short answer (45 seconds):** First I clarify risk: staff review every draft, so a bad output costs time, not a wrong refund. Then I build in order of what is hardest to add later: one client wrapper that every call goes through, tracing with prompt and model versions from day one, prompts in versioned files, a small eval set with a CI smoke gate, then dashboards, budgets and feedback capture, and finally a canary launch with a rehearsed rollback.

**Deeper explanation:** Clarify traffic, data sensitivity and region, who edits prompts, and the budget per draft. Then:

```text
wk 1  llm client wrapper (tags, timeouts, retries, usage), tracing, prompt files + version stamp
wk 2  eval set: 60-100 real historical tickets, slices, must-include facts
wk 3  CI smoke gate (deterministic checks + calibrated judge), compared to production
wk 4  dashboards: p95 latency, cost per draft, fallback rate; per-request and daily caps
wk 5  feedback: accepted / edited / discarded per draft, linked by trace ID
wk 6  release checklist, canary to one support team, rollback drill
```

The wrapper matters most; every later control hangs off it:

```ts
const res = await client.messages.create({ model: cfg.model, max_tokens: cfg.maxTokens,
  system: cfg.systemPrompt, messages });
await usageSink.record({ feature: "reply_draft", tenantId, traceId,
  promptVersion: cfg.promptVersion, model: res.model, usage: res.usage });
```

Trade-offs: hosted Langfuse is faster to adopt; self-hosting is the answer if customer data cannot leave the region. Prompts in git are enough until non-engineers need to edit them. Measure draft acceptance rate, edit distance between draft and sent reply, cost per accepted draft, p95 latency and the eval score trend. Risks: PII in traces from day one, so redaction ships with tracing; and over-building, so no feature store, training pipeline or custom platform.

**Follow-ups they will ask:**
- What would you cut with three weeks?: Keep wrapper, tracing, the smoke gate and rollback; defer dashboard polish and the review queue.
- What is your launch gate?: Eval comparison on the frozen set, redaction tests passing, cost per draft under budget, rollback rehearsed.

**Mistakes to avoid:**
- Starting with a tool shopping list instead of risk, data and ownership questions.
- Adding tracing and cost capture after launch, so the first incident has no evidence.

### Q. Product managers edit prompts in the registry UI, engineers edit them in git, and last month an unreviewed UI edit reached production. Design an eval gate that no path can bypass.

**Short answer (45 seconds):** Separate drafting from promotion. Anyone may create prompt versions in the registry, but production resolves only a version pinned in a lock file in git, and changing that pin is a pull request that runs the eval gate as a required status check. If the registry has a production label, only the CI service account moves it, after merge. One gate covers both editing paths, and git history becomes the audit trail.

**Deeper explanation:** Clarify the number of prompts and owners, how fast PMs expect changes live, and the CI budget (I aim for a smoke suite under ten minutes).

```yaml
on:
  pull_request:
    paths: ["prompts.lock.yaml", "prompts/**", "evals/**"]
jobs:
  eval-gate:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: |
          python -m evals.gate --changed-from origin/main --suite smoke \
            --compare-to production --must-pass evals/must_pass.jsonl
```

Decisions. Only suites for prompts whose pin changed run, so one team's change does not run everyone's evals. It compares candidate and production on the same dataset with the model and settings production actually resolves, blocks on must-pass failures or drops beyond measured run-to-run noise, and comments the worst regressions on the pull request. A small bot turns "promote version 18" in the registry UI into a pull request, so PMs keep their workflow. Break-glass exists: a named approver can merge with the gate red, and the override is logged.

Trade-off: PMs lose instant publishing, and the bot keeps the delay to one CI run. Risk: the gate goes stale if the eval set stops matching traffic, so a weekly job scores a fresh production sample. Measure gate runtime, flake rate on unchanged reruns, override count, and production regressions the gate passed.

**Follow-ups they will ask:**
- What about urgent fixes?: The same pull request with a second approver; never a direct label move.
- What if someone moves the label in the UI anyway?: Restrict the permission, and have production read the pinned version, so a stray move has no effect.

**Mistakes to avoid:**
- Gating only the git path while the registry UI still publishes straight to production.
- Running every suite on every change, so the gate takes 40 minutes and gets bypassed.

### Q. You run dev, staging and production, plus a separate in-region production stack in the UAE with its own prompt registry for residency. Design versioning and rollback across all of them.

**Short answer (45 seconds):** Make git the source of truth for a release manifest per feature that pins prompt version and content hash, model ID and settings, tool and output schema versions, and retrieval config. Each environment pins a manifest version, and CI syncs prompt text into each region's registry and verifies the hash. Promotion is a pull request that changes an environment's pin; rollback is reverting it, one command for every region.

**Deeper explanation:** Clarify whether prompts may differ by region (an Arabic variant, a different model available in-region) and how fast a rollback must take effect.

```yaml
# releases/support_answer/23.yaml
prompt:    {name: support-answer, version: 15, sha256: 9f2c41d0}
model:     {id: model-snapshot-2026-09, max_tokens: 800, temperature: 0.2}
tools:     tools/support_v4.json
output:    {schema: support_answer, version: 3}
retrieval: {index_version: 2026-10-20, top_k: 6}
# envs/prod-uae.yaml pins {support_answer: 22}
```

Key decisions. The manifest, not the prompt, is the unit of release, because a prompt tuned for one model and one output shape is a different change under another. Code declares which output schema versions it can parse, and the service fails its readiness probe if asked to load a manifest it cannot handle, which turns a mismatched rollback into a failed deploy instead of broken answers. A nightly job compares hashes between git and each registry and alerts on drift, so nobody hand-edits the UAE registry and forgets. Every trace records the manifest version, so one field answers "what was running".

Trade-off: instant label flips are gone in production; keep them in dev and staging, where experimentation matters. Risk: a manifest pins an index version that was deleted, so retention keeps the last few pinned versions of everything. Measure time to roll back in a drill, hash-drift alerts, and the share of traces carrying a manifest version.

**Follow-ups they will ask:**
- What if the in-region model differs?: That region gets its own manifest with its own eval run; same structure, different pins.
- How do canaries work with pins?: The resolver reads two pins with a traffic weight, and both appear on traces.

**Mistakes to avoid:**
- Versioning the prompt alone while model, tools and output schema move independently.
- Letting each region's registry become a separately edited copy.

### Q. Support flags around 200 bad answers a week, and you have one engineer-day a week to turn them into eval coverage. Design the loop.

**Short answer (45 seconds):** Automate everything except judgment. Flags arrive already joined to their trace; a nightly job redacts, deduplicates and clusters them by intent and failure type; a domain expert reviews one representative per cluster and writes the rubric; a bot opens a pull request adding the items with frozen context. The engineer-day goes to fixing the largest cluster, not to data entry.

**Deeper explanation:** Clarify what counts as a flag (thumbs down, heavy edit, escalation), whether flagged content may be stored, and who defines "correct".

```text
flag (trace_id) -> nightly: redact -> dedupe (input hash) -> embed + cluster
  -> judge pre-labels failure type -> triage queue: 1 item per cluster + 10 random
  -> expert writes rubric, sets severity -> bot PR: evals/support/*.jsonl
  -> CI runs new items against production (they must fail) -> merge
weekly: fix the largest open cluster, re-run, close it when its items pass
```

Decisions. Clustering is the leverage: 200 flags may be fifteen real problems, and one careful rubric per cluster beats 200 rushed ones. Each new item must fail on the current production version when added, otherwise it does not reproduce the reported failure. Freeze context with chunk IDs and index version so the item tests the model, not tomorrow's retrieval. Add a few random unflagged traces to every triage batch, because flags show only what users bothered to report.

Trade-off: judge pre-labels speed triage but can anchor the reviewer, so the expert reads the trace before seeing the label. Risks: PII entering the eval repository (redact before the pull request, scan new items in CI) and bloat (retire items that have passed for months and are covered elsewhere). Measure time from flag to eval item, recurrence of closed failure types, and the gap between fixed-set and fresh-sample scores.

**Follow-ups they will ask:**
- When does a cluster become training data?: When it survives prompt and retrieval fixes and has hundreds of curated, consented examples.
- How do you prioritize clusters?: Frequency times severity, with safety and compliance clusters first.

**Mistakes to avoid:**
- Turning every flag into an item by hand, which burns the budget and fills the set with duplicates.
- Building the loop only from complaints and never sampling unflagged traffic.

### Q. Five services call the model provider directly with one shared API key, and finance wants cost per feature and margin per tenant by next quarter. How do you build it?

**Short answer (45 seconds):** In three steps. This week, split API keys or provider workspaces per service and environment, which gives coarse attribution with no code change. Next, route every call through one gateway or shared client that refuses untagged calls and records feature, tenant, prompt version, model and usage as events in the warehouse. Then add a versioned price table, daily reconciliation with the provider's cost data, budgets with burn-rate alerts, and the margin report.

**Deeper explanation:** Clarify how finance bills (seats, usage, plan tier), whether tenant revenue is in the warehouse, and how shared costs are allocated.

```sql
SELECT u.feature, sum(u.cost_usd) AS mtd,
       sum(u.cost_usd) / extract(day FROM current_date)
         * extract(day FROM date_trunc('month', current_date)
                   + interval '1 month - 1 day') AS projected,
       max(b.monthly_usd) AS budget
FROM llm_usage u JOIN feature_budget b ON b.feature = u.feature
WHERE u.day >= date_trunc('month', current_date)
GROUP BY u.feature;
```

Decisions. A gateway (an internal service, or LiteLLM's proxy, which offers virtual keys with budgets) covers every language and gives one enforcement point, but adds a hop and a component that must stay highly available. A shared library avoids the hop but must exist per language and can be bypassed. Untagged spend is its own report line, and driving it to zero is the first milestone. Budgets act at three levels: per-request ceilings in code, per-tenant quotas by plan, and per-feature monthly budgets whose burn-rate alert fires mid-month rather than after the invoice.

Risk: tags that lie, such as a batch job tagged as the chat feature, so tags come from service identity where possible. Measure the attributed share of spend, the gap between computed cost and the invoice, alert lead time, and cost per task against revenue per tenant.

**Follow-ups they will ask:**
- Fail open or closed if the gateway is down?: Closed for batch jobs, open with local caps for user-facing paths, decided per feature in advance.
- How do you allocate shared costs?: By measured usage, such as queries per tenant against the shared index, with the rule printed on the report.

**Mistakes to avoid:**
- Estimating tokens from character counts instead of using the usage the provider returns.
- Waiting for the month-end invoice instead of projecting the burn rate.

### Q. An enterprise customer in the UAE, or a regulated lender in India, will sign only after a security and compliance review, and launch is in four weeks. What do you prepare?

**Short answer (45 seconds):** Evidence, not assurances. A data-flow and retention table for every hop, PII minimization and redaction with test results, in-region hosting and model routes confirmed, the audit trail and access controls, and a system card, eval report, risk assessment and incident process. Legal interprets the law; engineering proves the controls work.

**Deeper explanation:** Clarify which regimes apply (the UAE federal data protection law, DIFC or ADGM rules in those free zones, a sector regulator such as the central bank; in India the DPDP Act plus RBI rules for regulated entities), whether data must stay in-country, and whether customer data may train anything.

| Hop | Data | Region | Retention | Control |
|---|---|---|---|---|
| API and app DB | tickets, accounts | in-country cloud region | contract | tenant isolation, SSO |
| Model provider | redacted prompts | in-region route | per contract | no-training terms |
| Trace store | redacted samples | self-hosted, in-region | 30 days | RBAC, access log |
| Vector DB | embeddings | in-region | contract life | per-tenant filter |

Four weeks: map flows and list gaps; close gaps (redaction on tool results and retrieved documents, retention jobs, a deletion path covering traces and embeddings); test (a PII-laden eval set with detector recall, an injection suite, tenant isolation tests); document (system card, eval report, runbooks) and dry-run the questionnaire with security.

Trade-offs: in-region hosting may limit which models are available, so run the eval suite on the in-region model before promising quality; self-hosting satisfies residency but adds GPU and on-call cost. Risk: claims tests cannot back, such as "no PII is stored" while error logs hold request bodies. Measure questionnaire items closed with evidence, detector recall, a deletion drill finished within the agreed time, and audit completeness for approvals.

**Follow-ups they will ask:**
- What if no data may leave their network?: An open-weight model in their cloud account, with the capability gap shown on the eval set.
- How do you prove deletion?: Logged deletion jobs and a drill that searches every store afterwards.

**Mistakes to avoid:**
- Quoting clauses or dates from memory instead of naming the regime and verifying with counsel.
- Leaving traces, error trackers, backups and embeddings off the data-flow map.

### Practice
- Write the six-week plan for an LLM feature you know, then cut it to three weeks and justify each cut by the incident it would leave you unable to debug.
- Build the lock-file gate: a `prompts.lock.yaml`, a GitHub Actions job that runs a 30-item smoke suite only for changed pins, and a required status check; open a pull request that should fail and confirm it is blocked.
- Draft a release manifest for one feature plus a startup check that refuses an incompatible output schema version; prove it on a local kind or minikube cluster by deploying a mismatched pair.
- Say it out loud: in two minutes, answer "we have one LLM feature and no process; where do you start?" as an ordered plan that includes what you would not build yet.

## LLMOps Incidents & Error Cases [Scenarios]

> Incident questions test whether you stay ordered under pressure. Use the same structure every time: clarify impact (who is affected, since when, how badly), contain with the cheapest reversible lever (move a prompt label, flip a flag, cap spend), diagnose from evidence (traces split by version, deploy and promotion history, provider status), fix the cause, and prevent a repeat with an eval item, test, alert, guardrail or runbook line. In LLM systems the first question is "what changed?", and the answer can come from four channels: code, prompt, model or data. A weak answer jumps to a fix. A strong answer stops the damage first and names the evidence that would confirm or kill each theory.

### Concepts you must understand
- Four change channels: code deploys, prompt label moves, model changes (including moving aliases and fallbacks) and data or index updates; annotate dashboards with all four so a step in a metric lines up with its cause.
- Contain first with something fast and reversible, then diagnose; rolling forward under pressure compounds errors.
- Evidence lives in traces split by prompt version, model ID and manifest version; if a trace cannot tell you those, the first fix is instrumentation.
- Every incident leaves an artifact behind: an eval item, a contract test, an alert with a runbook, or a cap in code.
- Incidents involving personal data carry legal deadlines and owners outside engineering, so security and the data protection officer join early.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| Thumbs-down or escalation rate up right after a prompt promotion | Metrics split by prompt version; label-move audit log | Eval set missing a slice; eval run with different model or settings | Move label back; add the slice; build eval config from the production resolver |
| `jinja2.exceptions.UndefinedError: 'policy_chunks' is undefined` after a promotion | Variables the new version expects vs what the code passes | Prompt promoted ahead of the code that supplies the variable | Roll back the label; declare variables in prompt metadata and check them in CI |
| `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` in the output parser | Raw completion and stop reason on a failing trace | Prose or code fences around the JSON; output cut at `max_tokens`; prompt and parser out of step | Structured outputs or a tool schema; check stop reason; pin prompt with code |
| Pydantic `ValidationError` with "Field required" right after a code rollback | Live prompt version vs the output schema the code parses | Code rolled back, prompt label not | Move label back; release manifest; startup schema check |
| Streamed generations show no token usage | Is the call streamed, and when does the span end | OpenAI stream without `stream_options={"include_usage": True}`; span closed before the final event | Request usage on streams; end the span after the last chunk |
| Worker spans appear as separate root traces | Is `traceparent` present in the queue message | Trace context not propagated through Kafka, Redis Streams or Celery | Inject and extract W3C trace context at produce and consume |
| Traces missing from serverless functions or short jobs | Is the tracing client flushed before exit | Batched exporter buffer lost when the process ends | Call the SDK's flush or shutdown in a finally block |
| HTTP 404 `model_not_found` (OpenAI) or `not_found_error` (Anthropic) | Provider deprecation page, exact model ID, key or project access | Retired model, typo, model not enabled for that key | Migrate after evals; model IDs only in config |
| HTTP 429 `rate_limit_error` or 529 `overloaded_error` (Anthropic) | Requests and tokens per minute by tenant; provider status page | Noisy tenant, retry storm without jitter, batch job on the production key | Per-tenant limits, backoff with jitter, separate keys |
| `context_length_exceeded` (OpenAI) or "prompt is too long" (Anthropic) | Token count per section of the rendered prompt | Unbounded chat history, too many chunks, a tool result dumping a whole document | Enforce a context budget; truncate or summarize tool results |
| Emirates ID, Aadhaar or card numbers found in a log search | Which sinks, and since when | Request-body debug logging; redaction on user input only; exceptions carrying payloads | Stop writes, purge, redact at the exporter, PII canary test |
| Judge pass rate jumps to near 100 percent | Judge model ID, parse-failure count, golden-set agreement | Judge on a moving alias; parser defaults to pass; string "false" is truthy | Pin the judge; strict schema; fail closed; sentinel items |
| Spend doubled and no feature is named | Provider usage by key, model and token type per day | Untagged service, agent loop, cache regression, CI on the production key | Caps in code, gateway with required tags, daily reconciliation |
| Drift alert fires daily and is acknowledged without action | Alert history: fires vs actions taken | Per-feature alerts, significance on huge samples, stale reference window | Alerts tied to actions; effect-size thresholds; persistence; tickets, not pages |

### Q. A prompt change passed the eval gate and review on Tuesday. By Thursday, thumbs-down and escalations for the support assistant have doubled. What do you do?

**Short answer (45 seconds):** Confirm the link first: split thumbs-down and escalation rates by prompt version and check the step lines up with the label move, not a deploy or index refresh. If it does, move the production label back and confirm new traces show the old version. Then find out why the gate passed it: the deeper bug is in the eval.

**Deeper explanation:** Split by version:

```sql
SELECT date_trunc('hour', t.created_at) AS hour, t.prompt_version,
       avg(CASE WHEN f.score = -1 THEN 1.0 ELSE 0 END) AS thumbs_down_rate
FROM traces t LEFT JOIN feedback f ON f.trace_id = t.trace_id
WHERE t.feature = 'support_answer' AND t.created_at > now() - interval '5 days'
GROUP BY 1, 2 ORDER BY 1;
```

1. Impact: which tenants, languages and intents moved.
2. Contain: label back to the previous version; clients pick it up when their prompt cache expires, or a pod restart forces it.
3. Diagnose: pull 30 thumbs-down traces from the new version, group by intent, and replay those inputs through the offline eval for both versions.

Likely causes, ranked. The eval set lacks the slice that broke, such as Arabic or Hinglish tickets or long multi-issue tickets. The harness used settings production does not: another model alias or temperature, missing tools, or short frozen contexts where production retrieves eight chunks. The rubric rewards what users dislike, such as citation coverage that made answers terse. Or another change landed the same day; deploy annotations show it.

Fix: a new version for the slice, with the failing traces as eval items that fail on the bad version and pass on the fix. Prevent: the eval harness takes its configuration from the production resolver, a weekly eval on a fresh production sample catches coverage gaps, and prompt promotions go out as a canary with thumbs-down rate per version as the abort signal.

**Follow-ups they will ask:**
- What if the replayed inputs score fine offline?: Then the rubric or judge is blind to it; fix it and re-validate on human labels.
- What if rolling back does not help?: The prompt was not the cause; check the other three channels.

**Mistakes to avoid:**
- Rewriting the prompt live while the bad version still serves everyone.
- Fixing the prompt without asking why the gate passed it.

### Q. An escalation needs the trace, and you find a generation with no token usage, worker spans sitting in separate traces, and `prompt: production` where a version number should be. What do you do?

**Short answer (45 seconds):** Two jobs. For the escalation, I narrow the candidate prompt versions from the label-move audit log and the request time, then replay the input against each candidate. The gaps are an instrumentation bug with three causes: usage capture on streams, trace context through the queue, and stamping of resolved versions. Then a contract test so none of them regress.

**Deeper explanation:** One cause per gap.

Missing usage usually means streaming. OpenAI's Chat Completions API sends usage on a final chunk only when the request sets `stream_options={"include_usage": True}`; Anthropic sends input usage in `message_start` and output usage in `message_delta`. A wrapper that ends the span on the first chunk, or when the client disconnects, never records it. Check the share of generations with null usage split by the stream flag.

Orphaned spans: the API puts the job on Redis Streams and the worker starts a fresh root span, because nothing carried the context.

```python
from opentelemetry import propagate, trace
tracer = trace.get_tracer("support")

# API
carrier = {}
propagate.inject(carrier)                     # adds traceparent
r.xadd("jobs", {"payload": body, **carrier})

# worker (redis client created with decode_responses=True)
ctx = propagate.extract(fields)
with tracer.start_as_current_span("retrieve_and_answer", context=ctx):
    handle(fields["payload"])
```

Missing version: the code logs the label it asked for instead of the `prompt.version` it received, or a fallback that loads a bundled prompt stamps nothing. Log the resolved version, and stamp bundled fallbacks as their own version with a content hash. Also check serverless handlers and short jobs, which lose buffered spans if the process exits before the SDK flushes.

Prevent: a CI contract test sends one request through API and worker against a local collector and asserts a single trace, a generation with usage above zero, an integer prompt version and a model ID. In production, chart the share of generations with usage and of traces with a version, and alert when either falls below 99 percent.

**Follow-ups they will ask:**
- Does a replay prove which version ran?: Only probabilistically; run each candidate several times and say so in the escalation reply.
- Why not log the full rendered prompt?: It may hold PII; version plus inputs reconstructs it.

**Mistakes to avoid:**
- Answering the escalation and leaving the instrumentation broken.
- Assuming the tracing SDK propagates context through your queue by itself.

### Q. A security scan finds Emirates ID numbers and card numbers in your trace store and in CloudWatch application logs. Walk me through the response.

**Short answer (45 seconds):** It is a data incident before it is a bug. I stop new writes first: switch off trace content capture and request-body logging. Then I bring in security and the data protection officer, because notification duties may apply, scope every sink and date range, purge what policy requires, and only then fix the path that let the data through.

**Deeper explanation:** Scope each sink, starting with CloudWatch Logs Insights:

```text
fields @timestamp, @logStream
| filter @message like /784-\d{4}-\d{7}-\d/
| stats count() by bin(1d), @logStream
```

Run the same patterns over the trace store, error tracker, trace exports in the warehouse, and backups. Record first and last occurrence, affected tenants and who had read access, because the notification decision needs it.

Likely causes, ranked. Redaction covered user input but not tool results: a CRM or KYC lookup returned the ID and the span stored it. Middleware or an exception handler logged the full request body. An SDK debug log level was left on in production. The model echoed PII from context into an unscanned completion.

Fix. CloudWatch log events cannot be edited, so purging means deleting the affected streams or groups once security has preserved what the investigation needs; a CloudWatch Logs data protection policy then masks matching identifiers as a second net. In the trace store, delete the affected traces by ID through its API, and get written deletion confirmation from any hosted vendor. Move redaction to one choke point that every span attribute passes before export, covering inputs, outputs, tool results and retrieved chunks, with Presidio recognizers plus patterns for Emirates ID, Aadhaar, PAN, and card numbers with a Luhn check.

Prevent: a PII canary test in CI pushes synthetic identifiers through the whole flow and asserts they reach no sink; a scheduled scan alerts on matches; request bodies are never logged at info level.

**Follow-ups they will ask:**
- Do you notify customers?: Legal and the data protection officer decide against law and contracts; engineering supplies scope and timeline.
- Is masking at display time enough?: No; the data is still stored, backed up and readable through the API.

**Mistakes to avoid:**
- Fixing the code first while leaking writes continue.
- Deleting everything before security has preserved the evidence.

### Q. The provider announces that the model behind three of your features retires in 30 days. What is your plan?

**Short answer (45 seconds):** Treat it as a release with a deadline. Inventory every caller of that model ID, including batch jobs and the eval judge; evaluate candidates per feature with current prompts; write new prompt versions where needed; canary each feature; and finish at least a week before retirement.

**Deeper explanation:**

1. Inventory from traces and code, because config alone misses hardcoded calls:

```sql
SELECT service, feature, model_returned, count(*) AS calls
FROM llm_usage
WHERE day >= current_date - 30 AND model_returned = :retiring_model
GROUP BY 1, 2, 3 ORDER BY calls DESC;
```

Also grep repositories, notebooks and CI workflows. The usual surprises are the eval judge, a nightly batch job and a fallback entry.

2. Candidates: the provider's suggested replacement plus one alternative. Run the full suite per feature and compare quality by slice, output format adherence, latency and cost. Tokenizers differ, so the same text can count as a different number of tokens; caches are model-scoped, so expect a cost bump at cutover; supported request parameters can change between model generations, so check them in the docs.
3. Adapt: new prompt versions tuned on the new model, each recorded with the model it was tested on.
4. Judge first if the judge is affected: recalibrate the replacement on the human-labeled golden set before trusting any comparison it produces.
5. Roll out per feature: canary with metrics split by model, then full traffic.

If the date is missed, calls fail with a 404 naming the model or, worse, a configured fallback silently serves everything from a model nobody evaluated.

Prevent: a model lifecycle register (model ID, features, owner, announced retirement date) reviewed monthly, owners subscribed to the provider's deprecation notices, and a monthly eval run against the likely next model so migrations are known diffs.

**Follow-ups they will ask:**
- What if the replacement is worse on one feature?: Route that feature to the alternative, or close the gap with prompt work, examples or a fine-tune; the deadline does not move.
- All features at once?: No; one at a time, lowest risk first, so each canary is readable.

**Mistakes to avoid:**
- Changing the model ID in config and calling it done.
- Forgetting the judge and the batch jobs.

### Q. Finance reports the LLM invoice doubled month over month, and nobody can say which feature caused it. Walk me through it.

**Short answer (45 seconds):** First: if spend is still climbing, cap it. Then read the shape of the increase from the provider's own usage data by key, model, token type and day: a step on one date points to a change, a steady slope to growth, spikes to loops or batch jobs. Line the step up with deploys, prompt promotions and model config changes, then attribute and fix.

**Deeper explanation:**

```sql
SELECT day, api_key_name, model,
       sum(input_tokens) AS input, sum(cache_read_tokens) AS cache_read,
       sum(output_tokens) AS output, sum(cost_usd) AS cost
FROM provider_usage_export
WHERE day >= current_date - 60
GROUP BY 1, 2, 3 ORDER BY 1, cost DESC;
```

Read it by token type. Input up while cache reads fall: a cache regression, often a timestamp or per-user text added to the system prompt. Input up with the cache steady: context bloat, such as more retrieved chunks or untrimmed history after a prompt change. Output up: verbosity, or an agent looping, visible as a long tail of calls per task. A new model line: someone switched models, or fallback routing sent traffic to a pricier model during a provider incident. Spend on a CI, eval or backfill key: non-product traffic on production credentials.

Rank causes by how fast each is confirmed or ruled out: CI or batch jobs on the wrong key, cache regression, context growth, loops and retry storms, then legitimate tenant growth, which is not an incident and is why cost per task matters more than the total.

Contain: a per-request cost ceiling and an iteration cap in code, pause the batch job, revert the prompt that broke caching.

Prevent: the tagged gateway, with untagged spend as its own line; burn-rate alerts plus alerts on cache ratio, tokens per request and calls per task; deploy, promotion and model-change annotations on the cost chart; daily reconciliation against provider data.

**Follow-ups they will ask:**
- What if the provider data cannot be split usefully?: Rotate to per-service keys today, so tomorrow's data is attributable.
- How do you tell growth from waste?: Cost per task and per tenant; if both are flat, it is growth.

**Mistakes to avoid:**
- Proposing a cheaper model before knowing which tokens grew.
- Looking at the monthly total instead of the daily shape.

### Q. Drift alerts on an anomaly detection model fire every day, the channel is muted, and last week a real shift went unnoticed for days. How do you fix this?

**Short answer (45 seconds):** Treat alert fatigue as the incident. Audit every alert rule for the action it triggered in the last month, delete or downgrade the ones with none, rebuild the rest from healthy baselines with effect-size thresholds and persistence, route by severity, and split data quality alerts from drift.

**Deeper explanation:** Take an IoT anomaly detection pipeline like EMTAB, with drift checks on many sensor features.

1. Audit: for each rule, fires in 30 days and the action taken (ticket, rollback, retrain, nothing).
2. Causes, ranked. Per-feature alerts on many features: with enough features, some cross any fixed threshold every day by chance. Significance tests on huge samples: a KS test on millions of readings flags shifts too small to matter. A stale or wrong reference window: comparing today against training data from another season, or ignoring daily cycles. Data quality problems firing as drift: a firmware update that changed units, or nulls from an ingestion bug, which need a pipeline fix, not a retrain.
3. Fix with three tiers. Page only on model-level signals tied to an action:

```yaml
groups:
  - name: anomaly-model
    rules:
      - alert: PredictionDistributionShift
        expr: model_prediction_psi{model="sensor-anomaly", window="24h"} > 0.2  # set from 8 healthy weeks
        for: 6h
        labels: {severity: page}
        annotations: {runbook: "runbooks/prediction-shift.md"}
```

Ticket for drift on the few most important features, using effect-size measures such as PSI with persistence. Per-feature drift becomes a dashboard. Compare against a same-weekday or rolling reference window. Schema, unit and null-rate checks run in the pipeline and go to its owner.
4. Validate by replaying last month: the new rules must fire for the missed shift and stay quiet otherwise.

Prevent: every alert has an owner, a runbook and an expected action, and a weekly review retunes or deletes rules that keep firing without action.

**Follow-ups they will ask:**
- Would you retrain automatically on drift?: Not on raw drift; only behind validation gates, and never for data-quality causes.
- Does this apply to an LLM feature?: Yes, with intent mix, refusal rate and sampled judge scores as the signals.

**Mistakes to avoid:**
- Raising every threshold until the channel goes quiet, which hides real shifts too.
- Treating a data-quality break as drift and retraining on broken data.

### Q. After the platform team upgraded the judge model, the eval pass rate jumped to 99 percent, including items you know are bad. What do you do?

**Short answer (45 seconds):** A sudden improvement nobody worked for is an incident. I mark every eval run since the upgrade as untrusted and hold promotions that passed on judge scores alone, then run the judge on its human-labeled golden set, read raw judge outputs, and count parse failures. Often the judge model is fine and the plumbing around it is broken.

**Deeper explanation:** Cheapest checks first.

1. Parsing: the new model wraps JSON in a code fence or adds a sentence before it, and the parser falls back to a default that counts as a pass.
2. Types: the new model returns `"faithful": "false"` as a string, and `bool("false")` is `True` in Python.
3. Inputs: a template variable was renamed in the same upgrade, the judge now sees an empty answer, and an empty answer contains no unsupported claims.
4. Leniency: the new model is more agreeable under the same rubric, which the golden set shows as lower agreement with humans and known-bad items passing.

```python
from pydantic import BaseModel, StrictBool, ValidationError

# before: every failure mode becomes a pass
try:
    verdict = json.loads(raw)
except json.JSONDecodeError:
    verdict = {"faithful": True}
ok = bool(verdict["faithful"])

# after: strict schema, fail closed, counted
class Verdict(BaseModel):
    faithful: StrictBool
    reason: str

try:
    ok = Verdict.model_validate_json(raw).faithful
except ValidationError:
    judge_parse_failures.inc()
    ok = False
```

Fix: pin the judge to an exact model snapshot rather than an alias, use the provider's structured output or a tool schema for the verdict, fail closed on parse errors, and recalibrate the rubric if leniency is real. Re-run the evals for every promotion since the upgrade.

Prevent: sentinel items with known-bad answers run in every eval, and the gate fails if any passes; a judge change is a release with its own golden-set gate; the pass-rate chart alerts on sudden jumps up as well as drops.

**Follow-ups they will ask:**
- Why did nobody notice?: Alerts watch for drops; a rising score looks like good news.
- What agreement is enough for the new judge?: At least the old judge's on the same golden set, ideally near human-to-human agreement.

**Mistakes to avoid:**
- Celebrating the jump or retuning thresholds to match it.
- Parsing judge output with defaults that turn errors into passes.

### Q. During an incident you ran `kubectl rollout undo`. The API is back on last week's code, but now many responses fail with `ValidationError: 1 validation error for SupportAnswer` and "Field required". What happened?

**Short answer (45 seconds):** The rollback restored one of two release channels. Last week's release changed both code and prompt: prompt version 15 returns a new JSON shape, the old code expects the old one, and the production label still points at 15. I move the label back to version 14, the one paired with the old code, force a prompt refresh, and confirm parse errors fall and traces show the matching pair.

**Deeper explanation:**

1. Confirm: failing traces show code 2.7 with prompt version 15, and the completion has `citations` where `SupportAnswer` requires `cited_policy_ids`.
2. Contain, treating the prompt label as its own channel:

```bash
kubectl rollout history deployment/support-api
# move the prompt label back to the version paired with this code
python scripts/promote.py support-answer --version 14 --label production
kubectl rollout restart deployment/support-api   # drop cached prompts now
kubectl rollout status deployment/support-api
```

3. Verify: parse error rate back to baseline, every new trace on version 14.
4. Audit the other channels the rollback skipped: model ID in a ConfigMap, feature flags, the retrieval index alias, database migrations.

Why it happened: registry labels let prompts ship without deploys, and the rollback runbook listed only the deployment. Under pressure the team rolled back what they knew about.

Prevent:
- A release manifest that pins prompt version, model config and output schema, so rollback reverts one pin.
- A startup check: the service reads the prompt's declared output schema version and fails its readiness probe if it cannot parse it, so a mismatched pair never takes traffic.
- Tolerant parsers for one release: new code accepts both shapes, so code and prompt can roll independently.
- A rollback runbook listing all four channels, rehearsed in a drill every quarter.

**Follow-ups they will ask:**
- How do you find the paired version?: From the release record or manifest; without one, the label-move audit log next to the deploy timestamp.
- Does `rollout undo` revert ConfigMaps?: No; it reverts the pod template, not the ConfigMaps or Secrets it references, so version those in git.

**Mistakes to avoid:**
- Assuming `kubectl rollout undo` restores the whole system.
- Hot-patching the parser in production during the incident.

### Practice
- Break it on purpose: in a staging copy, promote a prompt version with a new output field together with matching code, roll back only the code with `kubectl rollout undo`, and watch the parse errors; then add the startup schema check and repeat until the mismatched pod fails readiness instead of serving errors.
- Break the judge on purpose: make the parser default to pass, feed it fenced and malformed verdicts, and confirm sentinel items fail the run; then switch to the strict schema and count parse failures.
- Push a synthetic Emirates ID and a test card number through the full flow (API, worker, tool call, trace export, logs), search every sink for them, and fix each sink where they appear.
- Say it out loud: in two minutes, walk through "the bill doubled" as impact, contain, diagnose, fix, prevent, naming the query you would run at each step.
