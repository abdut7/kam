## Evaluation Pipelines in CI/CD

> Evaluation is the center of LLMOps and the part most candidates have only done ad hoc. Interviewers probe whether you can turn "it seems better" into a repeatable gate: a versioned dataset, graders you trust, a comparison against the current version, and a rule for what blocks a merge. A weak answer is "we tested it on a few examples". A strong answer describes the eval set as fixtures, the judge as a calibrated instrument with a known error rate, and the release as a checklist with offline and online evidence.

### Concepts you must understand
- An eval dataset is a versioned set of inputs with expected outputs or grading rubrics, built from real production cases, hand-written edge cases and synthetic variations, and it is maintained like test fixtures.
- Graders come in three kinds: deterministic checks (schema, regex, exact match, tool call made), model-based judges (LLM-as-judge with a rubric), and humans; each has a cost and an error rate.
- A regression gate compares the candidate against the current production configuration on the same dataset and model, blocks on defined thresholds or significant drops, and reports per-item changes.
- LLM judges need calibration against human labels (agreement rate, bias checks) and cost control (sampling, caching, cheaper judge models for cheap checks).
- Human review is for high-stakes slices, judge disagreements and new failure modes; it feeds back into both the eval set and the judge rubric.
- Offline metrics predict quality before release; online metrics (feedback, task completion, escalation rate) measure it after; they disagree when the eval set no longer represents traffic.
- A/B tests of prompts or models require a pre-registered metric, randomization by user or session, enough traffic, and guardrail metrics for cost, latency and safety.
- A release checklist for an LLM feature covers eval results, safety and injection tests, cost and latency budgets, observability, rollback and the human escalation path.

### Q. How do you build an eval dataset for an LLM feature, and how is it like test fixtures in ordinary software?

**Short answer (45 seconds):** Sample production traces, including the ones users flagged, and write down what a good answer looks like for each as an expected output, required facts, or a rubric. Add hand-written edge cases for the failure modes you fear: ambiguity, missing context, injection attempts, out-of-scope questions. Version the file, give every item an ID and slice tags, and treat it like fixtures: it lives with the code, changes go through review, and every failing production case becomes a new item.

**Deeper explanation:** Item shape follows the grading method: expected values, must and must-not facts, or a rubric for a judge.

```json
{"id": "sa-0142", "slice": "refund_policy", "source": "prod-trace-01J8..",
 "input": {"ticket": "I returned the shoes 20 days ago, where is my refund?"},
 "context_ids": ["pol-88"],
 "must_include": ["14 business days", "original payment method"],
 "must_not_include": ["store credit only"],
 "rubric": "Answers the timing question directly; cites policy; no invented dates."}
```

Keep a smoke suite of a few dozen items for every pull request and a larger suite of hundreds for nightly and pre-release runs. The weak point of most eval sets is staleness: traffic changes, the set does not, and the gate stops predicting production quality, so the pipeline that turns flagged traces into new items is part of the design.

**Follow-ups they will ask:**
- How many items do you need?: Enough that one flipped item does not move the aggregate; dozens for a smoke gate, hundreds for a release decision.
- How do you avoid overfitting prompts to the eval set?: Hold out items engineers never inspect, and refresh from production.
- Where do expected answers come from for open-ended tasks?: Rubrics and required facts rather than a single golden string.

**Mistakes to avoid:**
- Building the set only from happy-path examples the author thought of.
- Letting the eval set drift from production traffic, which makes a green gate meaningless.

### Q. How do you gate a pull request on eval results without the gate becoming flaky and ignored?

**Short answer (45 seconds):** Make the gate a comparison, not an absolute: run the candidate and the current production configuration on the same versioned dataset with the same pinned model, and block only on defined conditions such as a drop beyond a tolerance, any failure in a must-pass subset, or a schema or safety check failure. Control variance by running deterministic checks exactly, sampling judge-graded items more than once, caching judge verdicts and reporting per-item flips.

**Deeper explanation:** Treat items that flip between identical runs as unstable rather than regressed; use a judge rubric with a low-variance output such as pass or fail with a reason, cached by input, output and rubric version; retry transient API errors and fail loudly on exhausted retries rather than reporting a false red.

```yaml
on: [pull_request]
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m evals.run --suite smoke --compare-to production --max-drop 0.02
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

The job posts a report on the PR: aggregate by slice, must-pass results, biggest regressions, cost and latency deltas. Set tolerances from the observed run-to-run noise on an unchanged configuration; if a repeat run moves the score by 1 percent, a 2 percent tolerance is the minimum that will not cry wolf.

**Follow-ups they will ask:**
- Who pays for the API calls in CI?: Budget them; a smoke suite of 40 items costs cents.
- What about secrets and PII in the eval set?: Redact before committing; use representative fixture data where policy demands.
- Can the gate be advisory first?: Yes, to calibrate thresholds, then make the must-pass subset blocking once the team trusts it.

**Mistakes to avoid:**
- An absolute threshold such as "score above 0.9" that fails for reasons unrelated to the change.
- Running the full suite on every push so the gate takes 40 minutes and gets bypassed.

### Q. You use an LLM as a judge. How do you calibrate it, and how do you keep it from becoming the most expensive part of the system?

**Short answer (45 seconds):** Calibrate with a human-labeled golden set of a few hundred outputs: run the judge, measure agreement with humans, and check known biases: position bias in pairwise comparisons, preference for longer answers, self-preference. Fix the rubric and output format until agreement is acceptable, version the rubric, and re-validate when the judge model changes. Control cost with deterministic checks first, sampling, cheaper judge models and cached verdicts.

**Deeper explanation:** Report agreement next to the judge's metric so readers know how much to believe. For pairwise judging, present each pair in both orders and count a preference only when it is consistent. Ask for a structured verdict with a short reason.

```python
JUDGE_RUBRIC_V3 = """Score the ANSWER against the TICKET and POLICY.
Return JSON: {"faithful": true|false, "complete": true|false, "reason": "..."}
faithful: every factual claim is supported by POLICY. complete: the user's
question is answered. Do not reward length or confident tone."""
```

Cost levers in order: run schema and keyword checks before any judge call; judge a stratified sample of production traffic rather than every request; route binary rubrics to a cheaper model after confirming its agreement on the golden set; cache by a hash of input, output and rubric version.

**Follow-ups they will ask:**
- What agreement rate is good enough?: Compare it to human-to-human agreement on the same set; near that level the judge is as good as another annotator.
- Can a model judge its own outputs?: It introduces self-preference bias; use a different model or at least a different prompt, validated against humans.
- How do you judge without a reference answer?: Rubric-based grading on properties such as faithfulness to context and instruction adherence.

**Mistakes to avoid:**
- Reporting judge scores with no evidence of agreement with humans.
- Judging every production request with a large model, which can cost more than the feature.

### Q. When do you need human review of LLM outputs, and how do you run a review queue that actually gets worked?

**Short answer (45 seconds):** Humans are needed where errors are costly, where the judge is uncalibrated or disagrees with other signals, and where a new failure mode appears. A queue works when it is small and purposeful: a fixed daily sample stratified by slice and signal (judge fail, thumbs down, fallback fired, random), a tight rubric and a two-minute task per item, measured inter-reviewer agreement, and outcomes routed to eval items, rubric fixes, bug tickets and labels.

**Deeper explanation:** Design the queue as a daily budget with a sampling policy that mixes targeted and random items so you confirm known problems and discover unknown ones. The review UI shows input, retrieved context, output and the judge's verdict with reason, and asks for a few structured fields; Label Studio, Argilla or an internal page work.

```text
daily queue (50)
  20 judge-failed, 10 thumbs-down, 10 fallback-or-timeout, 10 random
reviewer fields: correct? (y/n), failure type (enum), severity, note
outputs: eval item | judge disagreement log | prompt or retrieval bug | tuning example
```

Measure the queue itself: items reviewed per day, agreement between two reviewers on a shared subset, and how many reviews turned into eval items or fixes. For high-stakes features, review can also be a pre-release gate or a pre-send approval step, with its own latency cost.

**Follow-ups they will ask:**
- Who reviews?: Domain experts for correctness, engineers for failure classification; both need the same rubric.
- How do you keep reviewers calibrated?: A shared subset every week, agreement tracking, and rubric discussions when agreement drops.
- What if the queue shows the judge is often wrong?: That is the queue working; fix the rubric, re-validate on the golden set, re-run recent gates.

**Mistakes to avoid:**
- Reviewing only flagged items, which never discovers the failures nobody flagged.
- Running a queue whose findings never change the eval set or the product.

### Q. What is the difference between offline and online metrics for an LLM feature, and how do they disagree?

**Short answer (45 seconds):** Offline metrics come from running a candidate on a fixed eval set before release: judge scores, exact matches, schema validity, cost and latency. Online metrics come from real usage after release: thumbs rates, task completion, escalation, retries, cost per resolved task. Offline predicts, online measures. They disagree when the eval set stops representing traffic, when users value things the rubric ignores such as tone or speed, or when feedback is biased by who bothers to give it.

**Deeper explanation:** Offline is controlled and comparable but measures only what you thought to include; online measures what happened but is noisy, delayed, confounded by traffic mix and available only after exposure. The bridge is to run the offline suite on a sample of recent production inputs regularly, so you notice when the fixed set has drifted.

| Question | Offline | Online |
|---|---|---|
| Is the candidate better than production? | Yes, on the eval set | Only after exposure |
| Did users get what they needed? | Approximated by rubric | Completion, escalation, feedback |

When they disagree, trust online for "what happened" and offline for "why", then fix the eval set so it would have predicted the outcome. A rising offline score with a falling completion rate usually means the rubric rewards something users do not want.

**Follow-ups they will ask:**
- Which online metric for a support assistant?: Resolution without human escalation within the session.
- How do you handle feedback bias?: Treat explicit feedback as a skewed signal; compare rates between versions rather than reading absolutes.
- How quickly do online metrics become reliable?: Days to weeks depending on traffic; canaries use fast proxies such as fallback rate and sampled judge scores.

**Mistakes to avoid:**
- Treating the offline score as the product metric.
- Treating thumbs rates as ground truth without acknowledging who gives feedback.

### Q. How do you A/B test a prompt or model change in production?

**Short answer (45 seconds):** Define the hypothesis and primary metric before starting, plus guardrail metrics. Randomize at the user or session level so one user sees a consistent variant, resolve the arm to a prompt version or model ID through the config layer, and stamp every trace with the arm. Run for a fixed duration sized from historical variance, analyze by arm with the pre-registered test, and stop early only for guardrail breaches.

**Deeper explanation:** Assignment must be sticky and independent of anything the variant could influence; hashing user ID with the experiment name is standard. Attribution requires the arm, prompt version and model ID on every trace and on downstream events such as escalation so the analysis can join them.

```python
import hashlib

def assign(user_id: str, experiment: str, split: float = 0.5) -> str:
    h = hashlib.sha256(f"{experiment}:{user_id}".encode()).hexdigest()
    return "treatment" if int(h[:8], 16) / 0xFFFFFFFF < split else "control"
```

Interleaving and pairwise comparisons suit ranking-like features: show both outputs and let the user pick, a direct preference signal with less traffic. Cost belongs in the decision rule: a treatment that wins on quality but doubles tokens may still lose on cost per resolved task. Afterwards the winner is promoted by the normal label move and the experiment config removed.

**Follow-ups they will ask:**
- How long should it run?: Until the pre-computed sample size is reached, covering at least one weekly cycle; peeking inflates false positives.
- What if traffic is too low?: Offline evals plus a shadow comparison, or a longer test on a higher-rate proxy metric.
- Can you A/B test and canary at once?: The canary is a safety ramp, the A/B a measurement; ramp first, then measure at a stable split.

**Mistakes to avoid:**
- Assigning variants per request so a user sees inconsistent behavior and the analysis is contaminated.
- Declaring a win from a dashboard glance without a pre-registered metric and sample size.

### Q. What is on your release checklist for an LLM feature?

**Short answer (45 seconds):** Evidence: the eval report comparing candidate and production with slices and must-pass items; safety tests for injection, leakage and refusals; cost and latency against budget. Operations: trace stamps with versions, dashboards by version, alerts for fallback rate, cost and judge drops, token and tool-call caps, a tested rollback. People: escalation path, owner on call, domain sign-off on sampled outputs. Then the rollout plan with abort conditions.

**Deeper explanation:** A prompt label move takes seconds and affects everyone, so the conditions are written down beforehand.

```text
[ ] eval: candidate vs production, same dataset version and model; slices ok
[ ] must-pass: schema validity, no PII on redaction set, injection suite
[ ] budget: p95 latency and cost per request within budget; caching verified
[ ] limits: max_tokens, tool-call cap per request, per-tenant quotas, timeouts
[ ] rollback: previous prompt version and model config restorable in one step
[ ] rollout: canary 5 -> 25 -> 100 with abort conditions and a decision owner
```

The two items teams skip most are the tool-call cap, which stops an agent loop from spending unbounded money, and the escalation path, which turns a wrong answer into a recoverable moment.

**Follow-ups they will ask:**
- Is this too heavy for a small change?: Scale it; a wording tweak still needs the eval and the rollback, and can skip a fresh safety review if the suite covers it.
- Who signs off?: The engineer on evidence, the domain owner on sampled outputs, the budget owner on cost changes.
- How do you keep it from rotting?: Encode what you can in CI; keep the human part to a one-page template that lives with the feature.

**Mistakes to avoid:**
- Listing only quality items and forgetting cost caps, rollback and escalation.
- Treating the checklist as paperwork; each line should map to an incident it prevents.

### Practice
- Build a 40-item eval set for a feature you know from real or realistic cases, with slices and must-include facts; run it against two prompt versions and produce the regression report with per-item flips.
- Write a judge rubric, label 50 outputs by hand, run the judge, and compute the agreement rate; then swap the order of answers in a pairwise version and measure position bias.
- Put the smoke suite into a GitHub Actions workflow that comments the report on a pull request and fails on a must-pass item; measure the run-to-run noise on an unchanged version to set the tolerance.
- Say it out loud: in two minutes, explain to a skeptical engineering manager why a prompt change needs an eval gate, what the gate costs, and what it prevents.

## Observability & Tracing for LLM Apps

> Observability questions are where a senior candidate shows production scars. Interviewers want to hear the vocabulary (trace, span, generation), the tools and what they are for, how you attribute tokens and cost, how you find the slow hop, how you log without leaking PII, and most of all how you go from a user complaint to a root cause using the trace. A weak answer is "we log the prompts". A strong answer walks through a real debugging session.

### Concepts you must understand
- A trace is one end-to-end request; spans are its nested steps (retrieval, tool call, post-processing); a generation is a span for a model call that carries prompt, completion, model ID, settings and token usage.
- LLM observability tools (Langfuse, LangSmith, Arize Phoenix, plus general APM) store traces, attach scores and user feedback to them, and let you compare, filter and build datasets from them.
- OpenTelemetry's GenAI semantic conventions standardize span names and attributes for model calls so traces from any SDK or vendor can land in any backend; they are still evolving, so expect attribute names to change.
- Token usage comes from the provider's response and must be attached to the trace with the exact model ID so cost can be computed per request, feature, tenant and prompt version.
- Latency is a sum of hops: your preprocessing, retrieval, each model call (time to first token and total), each tool call and network; you cannot optimize what you have not split.
- Prompts and completions are sensitive data: redact or hash PII before storing, control who can read raw content, set retention, and sample full content rather than logging everything forever.
- Scores on traces (judge verdicts, thumbs, deterministic checks) turn a trace store into an evaluation and feedback system, not just a log.
- The trace ID must flow end to end, from the client request through queues and workers to the provider call, and back to the user-facing response so support can find it.

### Q. Define trace, span and generation, and show how a RAG request maps onto them.

**Short answer (45 seconds):** A trace is the record of one request through the system, identified by a trace ID. Spans are the timed steps inside it, nested like a call tree. A generation is the span for a model call: it records the rendered prompt or a reference, the completion, model ID, settings, token counts, finish reason and latency. A RAG request is one trace with a retrieval span tree and one or more generations.

**Deeper explanation:** The tree shape shows timing and causality together:

```text
trace 01J9K  feature=support_answer  user=u_4211  prompt=v14  model=claude-sonnet-5-5
|- span  rewrite_query        38 ms
|- span  retrieve             210 ms
|   |- span vector_search     120 ms   top_k=20  index=policies-2026-10-20
|   +- span rerank            40 ms    kept=6  chunk_ids=[pol-88, pol-91]
|- generation answer          1900 ms  in=3120 out=210 cache_read=2400 ttft=420 ms
+- span  validate_output      4 ms     schema_ok=true  citations_ok=false
```

Each node carries inputs and outputs or references to them, so a reviewer can read what the model actually saw. Scores attach later: a judge verdict, a thumbs-down, a support ticket. Agent workflows produce deeper trees with a generation per step and a span per tool call, which shows where a loop went wrong and what it cost.

**Follow-ups they will ask:**
- What goes on the trace versus the span?: Request identity on the trace (user, tenant, feature, versions, arm); step detail on spans.
- How do you handle streaming?: The generation records time to first token and completes when the stream ends with the full completion assembled.
- Do you store the full prompt every time?: A reference to the prompt version plus variables, or the rendered text subject to redaction and retention.

**Mistakes to avoid:**
- Describing request and response logging as tracing; without the tree and timing you cannot locate the slow or wrong step.
- Omitting versions and IDs from the trace, which breaks every later analysis.

### Q. Compare LangSmith, Langfuse and Arize Phoenix. What would you pick and why?

**Short answer (45 seconds):** All three capture traces with generations, attach scores and feedback, and build datasets and evaluations from traces. LangSmith is the hosted platform from the LangChain team, tightly integrated with LangChain and LangGraph but usable through its own SDK. Langfuse is open source and self-hostable, framework-agnostic, with prompt management built in. Arize Phoenix is open source, built on OpenTelemetry and OpenInference conventions, strong on tracing and evaluation. Choose on hosting constraints, framework fit and scope.

**Deeper explanation:** Three constraints decide. Residency and procurement: if prompts and completions cannot leave your cloud, a self-hostable option wins by default. Stack fit: LangChain-heavy codebases get the most automatic instrumentation from LangSmith; OpenTelemetry-heavy platforms integrate most cleanly with Phoenix; plain Python or Node services work with any through decorators or OTel. Scope: Langfuse bundles prompt management with tracing, which means fewer systems for a small team.

| Need | Lean towards |
|---|---|
| Self-hosted, framework-agnostic, prompts and traces together | Langfuse |
| LangChain or LangGraph everywhere, hosted is fine | LangSmith |
| OpenTelemetry-native, open source, strong eval tooling | Phoenix |

Keep instrumentation thin: a small internal wrapper that creates the generation span and records usage, so switching tools is a wrapper change.

**Follow-ups they will ask:**
- Do you still need Datadog or Grafana?: Yes, for infrastructure and service metrics; the trace ID links the two views.
- What about MLflow or W&B tracing?: Both offer it; sensible when the team already standardizes on them for classical ML.
- What do these tools cost?: Hosted tiers price by trace or event volume, another reason to sample full content and keep metadata for everything.

**Mistakes to avoid:**
- Claiming deep experience with all three; name the one you used and position the others.
- Picking a tool before deciding where prompt and completion content may be stored.

### Q. What do the OpenTelemetry GenAI semantic conventions give you, conceptually, and why would you care?

**Short answer (45 seconds):** OpenTelemetry already standardizes traces, metrics and logs; the GenAI semantic conventions add agreed span names and attributes for model calls, such as the operation, requested and returned model, token usage and finish reasons, plus an opt-in way to record prompt and completion content as events. The payoff is portability: instrument once and send to any OTel backend, keep LLM spans in the same trace as database and HTTP spans, and build dashboards on standard attribute names instead of each vendor's schema.

**Deeper explanation:** Without a convention every SDK invents its own field names, so a trace crossing a Node gateway, a Python worker and a vendor API is three different shapes. With it, a generation span looks the same wherever it was produced:

```text
span name:  chat claude-sonnet-5-5
attributes: gen_ai.operation.name=chat
            gen_ai.request.model=claude-sonnet-5-5
            gen_ai.response.model=claude-sonnet-5-5
            gen_ai.usage.input_tokens=3120
            gen_ai.usage.output_tokens=210
            (content captured as events only when explicitly enabled)
```

Attribute names have changed between versions and the conventions are still marked as evolving, so pin the instrumentation library and expect to migrate dashboards occasionally. Practically, this is how one trace spans the whole request: the HTTP span, the Postgres span for the feature lookup, the vector search span and the generation span, viewable in Phoenix, Grafana Tempo, Jaeger or a commercial APM.

**Follow-ups they will ask:**
- Do vendor SDKs emit these spans?: Some do or ship instrumentation packages; otherwise wrap the call in a span and set attributes from the response usage.
- What about agent frameworks?: OpenInference and similar conventions add span kinds for chains, tools and retrievers.
- Is this only for tracing?: No; the conventions also define metrics such as token usage and operation duration histograms.

**Mistakes to avoid:**
- Quoting attribute names as fixed facts; say they are standardized but evolving.
- Treating OTel as a replacement for LLM observability tools; it is transport and schema, the tools are the analysis layer.

### Q. How do you track tokens and cost per request, per feature and per tenant?

**Short answer (45 seconds):** Take usage from the provider response on every call, input and output tokens plus cache read and write tokens, and attach it to the generation span with the exact model ID returned. Compute cost from a versioned price table keyed by model and token type, because prices differ by model, and store both tokens and cost. Tag every trace with feature, tenant, prompt version and experiment arm so cost rolls up along each dimension, then report cost per request, per resolved task and per tenant.

**Deeper explanation:**

```python
PRICES = {  # USD per million tokens, versioned, loaded from config
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20},
}

def cost_usd(model: str, u) -> float:
    p = PRICES[model]
    cached = getattr(u, "cache_read_input_tokens", 0) or 0
    return (u.input_tokens * p["input"] + cached * p["cache_read"]
            + u.output_tokens * p["output"]) / 1_000_000
```

Record the price table version with the computed cost so historical reports stay explainable after a price change, and reconcile the monthly total against the provider invoice, which catches missing instrumentation. Per-tenant rollups enable chargeback and quotas; per-prompt-version rollups reveal when a change doubled input tokens. Agentic features need one more dimension: cost per task, summing all generations in the trace, because a cheap model called forty times is not cheap.

**Follow-ups they will ask:**
- Where does cached-token accounting matter?: A feature with a large static prefix should show most input as cache reads; if not, caching is broken.
- How do you attribute cost across subagents?: Child spans inherit the parent trace ID and tenant tags; roll up at the parent.
- What about self-hosted models?: Attribute GPU time per request or per token and divide the instance cost.

**Mistakes to avoid:**
- Estimating tokens from character counts instead of reading the usage the provider returns.
- Hardcoding prices without a version, so historical costs silently change when you update them.

### Q. A feature's p95 latency is 9 seconds. How do you break it down by hop and find the problem?

**Short answer (45 seconds):** Read traces, not the aggregate. Group p95 by span name to see whether time is in retrieval, the model call, tool calls or your own code, and for model calls separate time to first token from total generation time: a long time to first token points at the provider or a huge prompt, a long generation points at output length. Then look for sequential calls that could run in parallel and retries hidden in SDKs.

**Deeper explanation:** A RAG request's budget once split:

```text
hop                     p50      p95     notes
query rewrite (LLM)     350 ms   900 ms  small model; skip for short queries
embed + vector search   90 ms    400 ms  p95 spikes track index compaction
answer generation       1.6 s    6.5 s   ttft 400 ms; output up to 900 tokens
```

Here p95 is dominated by generation and within it by output length, so the levers are a tighter `max_tokens`, instructions for concise answers, and streaming so the user sees progress. Sequential independent calls are the most common hidden waste: lookups that could run concurrently, or tool calls the model requested together that the code ran one by one. Give retries their own span so a request that retried twice shows as three calls.

**Follow-ups they will ask:**
- Why p95 rather than average?: Averages hide the tail users complain about; LLM latency is heavy-tailed because output length varies.
- How do you measure time to first token?: Timestamp the first streamed chunk and store it on the generation span.
- What if the provider is slow?: Compare your measured generation latency with the provider's status and your other models; failover rules and regional endpoints are the response.

**Mistakes to avoid:**
- Blaming "the model" without separating time to first token from generation time.
- Optimizing retrieval when 70 percent of the time is output tokens.

### Q. How do you log prompts and completions without leaking PII, and how do you decide what to sample?

**Short answer (45 seconds):** Decide with the data protection owner what the trace store may hold and encode it in the instrumentation: metadata, token counts, latency, versions and scores are always logged; prompt and completion content only after redaction, only for a sample, with a retention period and role-based access to raw text. Redaction runs before data leaves the process: detect emails, phone numbers, account numbers and names, and replace them with typed placeholders. Sampling favors what you need to debug: all errors and flagged traces, a small random share of the rest.

**Deeper explanation:** Redact before storage rather than at display time, otherwise the trace store is a second copy of your users' data with its own breach surface and retention obligations.

```python
def redact(text: str) -> str:
    text = EMAIL_RE.sub("<EMAIL>", text)
    text = PHONE_RE.sub("<PHONE>", text)
    return ner_mask(text, labels={"PERSON", "CARD_NUMBER", "AADHAAR", "IBAN"})

def should_capture_content(trace) -> bool:
    return trace.error or trace.flagged or trace.sampled_random(0.02)
```

Microsoft Presidio or cloud DLP APIs do the detection; typed placeholders keep redacted text useful because you still see that an email was present. Separate policy by environment: full content in a sandbox with synthetic data, redacted samples in production. Align retention: thirty or ninety days for content, longer for metadata, and a documented process to delete a user's traces on request.

**Follow-ups they will ask:**
- Does redaction break debugging?: Rarely; the structure of the failure is visible with placeholders, and the few cases needing raw text go through access-controlled break-glass.
- How do you redact tool results and retrieved documents?: The same pipeline applies to every span input and output.
- What about embeddings?: Derived personal data if computed from personal text; the same retention and access rules apply.

**Mistakes to avoid:**
- Logging everything "for now" and planning to add redaction later.
- Confusing access control with redaction; restricted access to raw PII is still storing PII.

### Q. A customer says the assistant gave them a wrong refund timeline yesterday. Walk me through debugging it from the trace.

**Short answer (45 seconds):** Find the trace by ID, or by user and time, and read the tree top down: the question, the rewritten query, the retrieved chunks and scores, the rendered prompt, the answer, the validation result. The wrong timeline is either absent from the retrieved context (retrieval or corpus problem), present but misread (prompt or model problem), or present alongside a conflicting policy (data problem). Then reproduce, add an eval case, and fix the failing layer.

**Deeper explanation:** A realistic trace:

```text
1. trace 01J9K, prompt v14, model claude-sonnet-5-5, tenant acme, 2026-10-29 14:02
2. user: "returned shoes 20 days ago, when is my refund?"
3. retrieve: pol-88 (0.81, "refunds within 14 business days"),
             pol-23 (0.79, OLD policy: "refunds within 30 days")
4. generation: answer says "30 days"; cites pol-23
```

Diagnosis: a stale policy chunk outranked the current one. Fix: remove or supersede stale documents, add an effective-date field used by retrieval filters, add an eval item with this ticket requiring the current policy. Had the context held only the correct policy, the fix would be prompt wording, a stronger model for the slice or output validation. Close the loop: corrected answer to the user, score and note on the trace.

**Follow-ups they will ask:**
- What if there is no trace?: Sampling or retention dropped it, itself a finding; errors and flagged traces must always be captured.
- How do you reproduce a nondeterministic model?: Run the same rendered prompt several times; if the error reproduces sometimes, it is a prompt or context problem.
- How do you prevent the whole class?: Effective dates and ownership on the corpus, plus a retrieval eval that checks the top chunk is current.

**Mistakes to avoid:**
- Starting from the prompt text in the repo instead of the trace showing what the model saw.
- Fixing the symptom with a prompt tweak when the root cause is stale data in the index.

### Practice
- Instrument a small RAG endpoint with Langfuse or Phoenix so each request produces a trace with retrieval spans and a generation carrying token usage; verify the prompt version and model ID appear on every trace.
- Build a cost report from your traces: tokens and cost by feature and by prompt version for a day, and reconcile the total against the provider's usage dashboard.
- Add a redaction step before content capture and a sampling rule (all errors, 2 percent random); confirm with a test that an email address never reaches the trace store.
- Say it out loud: narrate a trace-driven debugging session for a wrong answer in two minutes, naming at each step what you look at and what it would tell you.

## Governance, Security & Compliance

> Governance questions appear in every enterprise and UAE or India interview, because the buyer of an AI feature is usually a security or compliance team as much as a product team. Interviewers want to hear that you treat PII, retention, audit and approvals as design inputs rather than obstacles, that you know where human oversight belongs, and that you have at least awareness of the regulations your employer's customers will ask about. A weak answer is "legal handles that". A strong answer shows the controls in the architecture.

### Concepts you must understand
- Data minimization comes first: the cheapest PII control is not sending the data to the model or the trace store at all; redaction, tokenization and field-level filtering come second.
- Retention and residency are decisions on both sides: what your systems store and for how long, and what the model provider stores, where it processes, and what contractual options exist for shorter or zero retention and regional processing.
- An audit trail answers who or what did what, when, with which inputs, versions and approvals; it must be append-only, complete and queryable, and for regulated workflows tamper-evident.
- Human-in-the-loop controls are placed by risk: review before action for irreversible or high-impact outputs, review after the fact on samples for low-risk ones, and the approver must see the evidence, not just a button.
- Access control covers models (who can call which, with what budget), prompts (who can edit and promote), data (per-tenant and per-role filtering at retrieval time) and secrets (keys in a secret manager, never in prompts or code).
- Documentation artifacts: a model card describes a model's intended use, data, evaluation and limits; a system card describes the whole deployed system including prompts, tools and guardrails; both pair with eval reports and a risk assessment.
- Responsible AI review is a repeatable checklist: intended use, misuse, fairness across slices, transparency to users, fallback and escalation, and sign-off recorded with the release.
- Regulatory awareness: the EU AI Act is risk-tiered with obligations scaling by risk and transparency duties for AI interaction; India's DPDP Act is a consent-based personal data law with fiduciary obligations and breach notification; both make logging, documentation and human oversight engineering requirements.

### Q. How do you handle PII end to end in an LLM pipeline?

**Short answer (45 seconds):** In layers. Minimize: decide which fields the model needs and drop the rest before rendering. Redact or tokenize free text with a PII detector, replacing entities with typed placeholders or reversible tokens held in a vault and re-hydrated only in the response layer. Control the vendor side through retention and regional terms in the contract. Redact before tracing, restrict raw access, set retention. Verify with an eval set of PII-laden inputs that must produce PII-free traces and outputs.

**Deeper explanation:** Tokenization keeps the model useful without exposing identities:

```text
user text:  "Transfer 5000 to Priya Nair, account 1234567890, by Friday"
to model:   "Transfer 5000 to <PERSON_1>, account <ACCT_1>, by Friday"
vault:      {PERSON_1: "Priya Nair", ACCT_1: "1234567890"}  (short TTL, access-logged)
to user:    placeholders re-hydrated in the response layer, never stored in traces
```

Detection combines regexes for structured identifiers (emails, phone numbers, PAN, Aadhaar, Emirates ID formats, card numbers with a checksum) with a named-entity model for names and addresses; Presidio or cloud DLP services package this. Expect misses, so the detector gets its own eval set with precision and recall targets. Retrieval is a second PII path: indexed documents may hold personal data, so apply the policy at ingestion and enforce tenant and role filters on every query. Outputs are a third: the model can echo PII from context, so scan outputs before display and logging on sensitive features.

**Follow-ups they will ask:**
- Does redaction hurt quality?: Sometimes, when the task needs the real name; measure on the eval set and re-hydrate only where required.
- How do you handle a right-to-erasure request?: Delete the user's traces, vault entries and derived data such as embeddings, with a documented process.
- What about fine-tuning data?: Only redacted or consented data, with source and legal basis recorded per record.

**Mistakes to avoid:**
- Treating the provider's privacy terms as the whole answer while your trace store holds raw prompts.
- Redacting user input but not retrieved documents or tool results.

### Q. What do you have to decide about data retention and residency, and how do model providers factor in?

**Short answer (45 seconds):** Two sets of decisions. Yours: which data you store (prompts, completions, embeddings, feedback, traces), where, for how long per class, who can access it, and how deletion works. The provider's: where inference runs, how long inputs and outputs are retained, whether they train on them, and what regional or zero-retention options exist. Enterprise customers in the UAE and India often require in-region data, so map each flow to a location and retention period and pick routes that meet it.

**Deeper explanation:** A data-flow table satisfies security reviewers and your own team:

| Data | Where | Retention | Access |
|---|---|---|---|
| Prompts and completions (redacted sample) | Trace store, in-region | 30 days | On-call, support leads |
| Customer document embeddings | Vector DB, in-region, per tenant | Contract life | Service identity |
| Provider-side inputs | Provider, per contract | Per contract | Provider policy |

On the provider side the levers are: an endpoint or cloud route that processes in the required region, contractual retention terms including reduced or zero retention where offered, and confirmation that data is not used for training. Verify these in the current contract rather than reciting them. Residency also constrains the observability vendor.

**Follow-ups they will ask:**
- How do you prove deletion?: Retention jobs with logs, deletion receipts for user requests, and periodic audits sampling for data older than policy.
- Does provider-side prompt caching count as retention?: It is short-lived processing state; confirm how your provider documents it when a customer asks.
- What if a customer wants everything on-premises?: Self-hosted open-weight models and tooling, with the capability gap made explicit.

**Mistakes to avoid:**
- Quoting provider retention periods from memory; name the lever and say you verify current terms.
- Forgetting embeddings and feedback as personal data with their own retention.

### Q. What goes into an audit trail for an AI feature, and how do you make it tamper-evident?

**Short answer (45 seconds):** For every consequential action: who or what initiated it (user, service identity, agent run), when, which inputs (trace ID, prompt version, model ID, document IDs), what the model proposed, what a human approved or changed, what the system executed and the outcome. Plus every prompt promotion, model swap, policy change and access grant with the approver. Store it append-only in a separate store with restricted write paths, and for regulated workflows make it tamper-evident with hash chaining or write-once storage.

**Deeper explanation:** The audit log is distinct from the trace store: traces are operational and sampled, the audit log is complete for consequential events and written as a deliberate step in the action path.

```python
def audit(event: dict, prev_hash: str) -> dict:
    body = json.dumps(event, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256((prev_hash + body).encode()).hexdigest()
    row = {**event, "prev_hash": prev_hash, "hash": h}
    audit_db.insert(row)      # append-only table, no UPDATE or DELETE grants
    return row
```

Each hash includes the previous one, so altering or removing a record breaks the chain after it; anchoring the latest hash periodically to an external location prevents quietly rewriting the whole chain. For agents, log each tool call with arguments and a result reference, because "the agent did it" is not acceptable in an incident review.

**Follow-ups they will ask:**
- How long do you keep audit logs?: As long as regulation or contract requires; years for financial workflows, far longer than traces.
- Audit log versus trace?: The trace explains how an answer was produced; the audit log proves what was done and who approved it.
- Can the model's output be evidence?: Yes; store the exact output the approver saw, not a regenerated one.

**Mistakes to avoid:**
- Pointing at application logs with 30-day retention as the audit trail.
- Logging the action but not the approval, or the approval but not the evidence shown.

### Q. Where do human-in-the-loop controls belong, and how do you design them so they are not rubber stamps?

**Short answer (45 seconds):** Place them by risk and reversibility. Irreversible or high-impact actions, such as payments or external communication, get approval before execution. Reversible, low-impact outputs such as a draft the agent shows but does not send get sampled review afterwards. To avoid rubber stamps, show the approver evidence, not just the proposal: source context, a reasoning summary, confidence or judge scores, a diff against current state. Measure approval rate and time-to-approve, and audit a sample.

**Deeper explanation:** When every action needs approval and the approver sees only "Approve?", the approval rate goes to 99 percent and the control is theater. Risk tiering fixes the volume; evidence fixes the quality.

```text
tier 1  read-only answers, drafts not sent        -> post-hoc sampled review
tier 2  reversible writes to internal systems     -> auto-execute with undo window
tier 3  external communication, money, deletions  -> approval with evidence before action
```

Details that matter: the request says in plain words what will happen if approved; the approver can edit, not just accept or reject, and edits are captured as feedback; the agent cannot escalate its permissions by splitting an action into smaller ones. If approval rate is near 100 percent and median time-to-approve is three seconds, the control is not working: improve the evidence or raise quality so the tier can drop.

**Follow-ups they will ask:**
- Does review kill the speed benefit?: For tier 3, by design; the gain comes from automating tiers 1 and 2 and from faster, better-informed approvals.
- How do you train approvers?: With the rubric, examples of good rejections, and feedback from sampled audits.
- Where does this live in an agent?: As a tool-level policy: certain tools require an approval token only the review UI can mint.

**Mistakes to avoid:**
- One approval gate for everything, which guarantees rubber stamping.
- Approvals that show the action but not the evidence behind it.

### Q. How do you implement access control for models, prompts and data in an LLM platform?

**Short answer (45 seconds):** Three planes. Models: applications call providers through a gateway with service identities, so keys never sit in code or prompts, and the gateway enforces which features may use which models with what budget. Prompts: the registry has roles, editors create versions, only a CI identity or named approvers move the production label, and every change is logged. Data: retrieval filters by tenant and role at query time using the caller's identity, documents carry access metadata from ingestion, and tool calls run with the user's permissions, not the service's.

**Deeper explanation:** The data plane bites hardest. A RAG system that indexes a company's documents and filters by nothing has given every employee every document through the chat box. Carry access lists into the index and filter before ranking:

```python
results = index.search(
    query_embedding, top_k=20,
    filter={"tenant_id": caller.tenant_id,
            "allowed_groups": {"any_of": caller.groups}},
)
```

Filtering after retrieval is not enough: the top results may all be forbidden and the user gets nothing, or a bug skips the filter. Tools follow the same rule: an agent calling an internal API passes the user's token or an on-behalf-of token so the system of record enforces authorization, not prompt instructions. Secrets live in a secret manager with rotation; a key that appears in a prompt or a trace is compromised.

**Follow-ups they will ask:**
- How do you handle document permissions that change?: Re-index metadata on permission events; for the most sensitive sources, confirm access at query time with the system of record.
- Can the model be tricked into revealing another tenant's data?: Only if it was in the context; the control is never putting it there.
- Who can read production traces?: A small on-call group for redacted content; raw content behind logged break-glass access.

**Mistakes to avoid:**
- Relying on prompt instructions ("do not reveal other customers' data") as access control.
- Service accounts with broad permissions acting for every user, collapsing authorization to one identity.

### Q. What is a model card, and what documentation would you ship with an LLM feature?

**Short answer (45 seconds):** A model card is a short structured document describing a model: intended use and users, out-of-scope uses, evaluation results including slices, known limitations and risks, and how to monitor it. For an LLM feature you usually do not own the model, so the card describes the system: model version, prompts, retrieval sources, tools, guardrails and human controls, often called a system card. Alongside it ship the eval report, the data-flow and retention table, the risk assessment with mitigations, and the runbook.

**Deeper explanation:** Documentation lets a security reviewer, customer or auditor evaluate the feature without reading code. Keep it short, versioned with the feature, and generated from the registry and eval pipeline where possible.

```text
System card: support_answer v14 (2026-10)
  purpose:      policy questions for logged-in customers; not refunds or disputes
  model:        pinned vendor model id; prompt v14; index policies-2026-10-20
  evaluation:   eval set v9 (240 items): faithfulness 0.90, citation 0.96; refund slice 0.84
  known limits: conflicting policy versions; non-English tickets -> handoff
  monitoring:   judge score, fallback rate, cost per request; owner and on-call
```

The risk assessment pairs each harm (wrong policy answer, PII leak, injection via ticket text, over-reliance) with a mitigation and a residual risk owner, reviewed at major releases. Eval numbers should be regenerated by the pipeline, not typed in.

**Follow-ups they will ask:**
- Who reads a system card?: Security and compliance reviewers, enterprise procurement, internal reviewers, new team members.
- How does this relate to the EU AI Act?: Documentation, logging and human oversight obligations for higher-risk systems map onto a system card, audit trail and review controls.
- Is this too heavy for a small feature?: A one-page card with generated numbers is enough; scale depth with risk.

**Mistakes to avoid:**
- Writing a model card for the vendor's model instead of a system card for your deployment.
- Hand-typed metrics that drift from the real eval results within a month.

### Q. How do you integrate an LLM feature into an enterprise with legacy systems and formal approval processes?

**Short answer (45 seconds):** Start read-only and additive: wrap legacy systems behind thin adapters with clear contracts, let the feature read and draft before it writes anything, and keep writes behind the approval and audit controls the enterprise already uses. Fit the change process: produce the artifacts security and architecture reviews ask for, and use their identity provider, logging and network controls. Pin model versions, keep a fallback, and expand scope a tier at a time.

**Deeper explanation:** SOAP or batch-file interfaces, nightly syncs, brittle schemas, no sandbox: the adapter layer isolates the LLM feature from that and is where validation, rate limits and the user's permissions are enforced.

```text
chat UI -> orchestrator -> tool get_policy(id)    -> adapter -> legacy policy DB (read)
                        -> tool draft_case_note() -> queue -> approver UI -> case system (write)
controls: SSO identity passed through; egress only to approved provider endpoints; audit per tool call
```

Approval boards are slow because they are built for predictable software, so make the feature predictable: fixed model versions, documented behavior, measurable evals, a clear statement of what it cannot do. Expect egress questions, since a model API is an external dependency: provide the endpoint list, the data classification of what is sent, and the contract terms.

**Follow-ups they will ask:**
- How do you handle systems with no API?: Batch exports into a read replica or document index, with freshness labeled in the UI.
- What if the approval board does not understand LLMs?: Translate: a new external dependency, a new data flow, a new class of configuration change with its own release process.
- How do you keep velocity?: Pre-approve a class of changes, such as prompt versions that pass the eval gate.

**Mistakes to avoid:**
- Starting with write actions to prove value, which maximizes risk before trust exists.
- Treating the process as the enemy instead of producing the artifacts it needs.

### Q. What should an engineer know about the EU AI Act and India's DPDP Act when building AI features?

**Short answer (45 seconds):** At awareness level. The EU AI Act is risk-based: it bans a few practices, puts heavy obligations on high-risk systems such as hiring or credit, requires transparency such as disclosing AI interaction and labeling synthetic content, and adds duties for general-purpose model providers. India's DPDP Act is a consent-based personal data law: data fiduciaries need notice and consent for specified purposes, must protect data, notify breaches and honor access, correction and erasure rights, with a data protection board overseeing. Documentation, logging, human oversight, consent and deletion become engineering requirements; legal owns interpretation.

**Deeper explanation:** For the AI Act the first question is which risk tier a use case falls into, because that sets the obligations. Whatever the tier, the aligned habits are a system card, an eval report with slices, logging that supports traceability, human oversight for consequential decisions, and disclosure that an AI is involved. Deploying a vendor model does not remove your obligations for how you use it.

For DPDP the surface is consent and purpose: capture consent for the specific purpose, do not reuse data for another purpose such as training without a basis, keep per-user deletion working, and be able to notify on breaches, which requires knowing where personal data lives. Rules under the Act are phasing in, so check timelines and thresholds against current guidance.

**Follow-ups they will ask:**
- Does using a vendor model make compliance the vendor's problem?: No; you are the deployer or fiduciary for your use case.
- What is the quickest win for readiness?: A data-flow and retention table plus working deletion; most questions start there.
- Which features are likely high-risk?: Those affecting access to jobs, credit, education, essential services or law enforcement; check with legal.

**Mistakes to avoid:**
- Quoting dates, thresholds or penalties from memory; state the structure and say you verify specifics.
- Dismissing regulation as a legal matter; the interviewer wants the engineering implications.

### Practice
- Write the data-flow and retention table for a feature you know, including traces, embeddings, feedback and the provider; mark each row with region, retention and who can read it, then find the row you cannot justify.
- Implement a hash-chained audit table in Postgres with no UPDATE or DELETE grants for the application role, write ten events, alter one by hand as a superuser, and write the check that detects the break.
- Design a three-tier human approval policy for an agent that drafts and sends customer emails and updates CRM records; specify what evidence the approver sees for each tier.
- Say it out loud: give a two-minute answer to "how do you make sure our customer data is safe in your AI feature", structured as minimize, redact, control the vendor, protect the stores, verify.

## Feedback Loops & the Data Flywheel

> Interviewers ask about feedback to see whether you understand that the durable advantage of an LLM product is the data it accumulates about its own failures, and whether you can collect that data without fooling yourself. A weak answer is "we added thumbs up and down". A strong answer explains what gets attached to each signal, which implicit signals you trust and why, how failures become eval cases and training data, and how you keep the loop from amplifying its own biases.

### Concepts you must understand
- A feedback signal is only useful if it is joined to the exact trace, prompt version, model ID and context that produced the output; a bare thumbs count tells you nothing actionable.
- Explicit feedback (ratings, corrections, reason codes) is sparse and biased toward strong emotions; implicit feedback (copy, edit, regenerate, follow-up rephrase, abandonment, escalation) is dense but noisy and needs validation against ground truth.
- A labeling queue turns raw signals into trustworthy labels with guidelines, trained labelers, agreement measurement and a sampling strategy that targets uncertainty and coverage, not just complaints.
- Production failures become eval items first (cheap, immediate protection against regression) and training data second (expensive, needs volume, consent and curation).
- Fine-tuning on production data is justified when prompt and retrieval fixes have plateaued and you have thousands of curated, redacted, representative examples; otherwise it adds cost and risk for little gain.
- Feedback bias comes from who responds, what gets surfaced, the model's own outputs shaping future data, and reviewers anchoring on the model's answer; each needs a specific counter.
- Closing the loop safely means every change derived from feedback still passes the same gates: eval comparison, review, canary, rollback.
- The flywheel is a process with owners and a cadence (weekly triage, monthly eval refresh, quarterly data review), not a diagram.

### Q. How do you capture explicit user feedback so that it is actually usable?

**Short answer (45 seconds):** Attach it to the trace. A thumbs event carries the trace ID, so the feedback lands on the exact output, prompt version, model ID and context that produced it, stored as a score on that trace. Make negative feedback one step richer with a reason code (wrong, incomplete, off-topic, unsafe, slow) and optional free text, because "bad" without a reason cannot be triaged. Log segment and tenant, and show rates by version, because the absolute rate reflects who bothers to click while the difference between versions is informative.

**Deeper explanation:** The implementation is small and the payoff is large:

```python
@app.post("/feedback")
def feedback(body: Feedback, user=Depends(current_user)):
    tracer.score(trace_id=body.trace_id, name="user_rating",
                 value=1 if body.thumbs_up else 0, comment=body.reason_code,
                 metadata={"tenant": user.tenant_id})
    if not body.thumbs_up:
        review_queue.enqueue(body.trace_id, priority="user_negative")
    return {"ok": True}
```

Observability tools expose this score API, so feedback appears next to the trace and can be filtered: all thumbs-down on prompt v15 with reason wrong in the refund slice. Make feedback cheap and specific: inline on the message, one tap, reason codes only after a negative tap. Corrections are the richest explicit signal: when a user edits a generated draft before sending, store the edited version paired with the original, directly usable as an eval expectation and later as preference data.

**Follow-ups they will ask:**
- What feedback rate should you expect?: Low single digits; design for sparsity and compare versions rather than absolutes.
- Should you ask for a rating after every answer?: No; it trains users to ignore it. Inline, optional and light beats modal and mandatory.
- How do you prevent feedback abuse?: Rate-limit per user, weight by account standing, and treat feedback as a signal to review, not a label.

**Mistakes to avoid:**
- Storing thumbs counts in an analytics event with no trace ID.
- Reading a 92 percent positive rate as quality when 3 percent of users clicked anything.

### Q. What implicit signals tell you an answer was good or bad, and how do you avoid misreading them?

**Short answer (45 seconds):** Useful positives: the user copied the answer or clicked a cited link, sent a draft with few edits, did not rephrase the same question, did not escalate, and the session ended after the answer. Negatives: regenerate, immediate rephrase, heavy edits by edit distance, escalation, abandonment mid-flow. Avoid misreading them by validating each against labels on a sample, since a short session can mean satisfaction or giving up, and by using them as relative measures between versions, not absolute truth.

**Deeper explanation:** Each signal has a plausible opposite meaning:

| Signal | Positive reading | Alternative reading |
|---|---|---|
| Session ends after answer | Satisfied | Gave up |
| Copy to clipboard | Answer used | Copying to complain elsewhere |
| Regenerate | Wanted a different answer | Exploring |
| Low edit distance on drafts | Draft acceptable | User rubber-stamps everything |

Calibrate once with a labeled sample: how often does each signal agree with a human judgment; keep the ones with predictive value and weight them. Then use them where they shine: fast proxies in canaries and A/B tests, triggers for sampling into the review queue, and prioritization of which failures to study first. For a drafting feature, edit distance between generated and sent text is the single best implicit metric, and tracking it per prompt version shows quality trends weeks before explicit feedback does.

**Follow-ups they will ask:**
- Which one for a support assistant?: Resolution without escalation within the session, validated against ticket outcomes.
- Can implicit signals drive automatic changes?: Only through the normal gates; they can propose candidates and prioritize review, not promote prompts.
- What about different segments?: Calibrate per segment; power users and new users express satisfaction differently.

**Mistakes to avoid:**
- Treating every implicit signal as a label without validating it.
- Optimizing a proxy such as session length that the model can game by being verbose.

### Q. How do you run a labeling process that produces labels you can trust?

**Short answer (45 seconds):** Define the label schema and written guidelines with edge-case examples, pilot on a small batch with two or three labelers, measure agreement, and fix the guidelines until it is acceptable. Then run the queue with a sampling strategy: a random slice for unbiased estimates, targeted slices for known problems, and uncertainty sampling where judge and signals disagree. Keep a golden set every labeler periodically re-labels to detect drift, store labels with labeler ID, guideline version and timestamp, and route them to eval sets, judge calibration and training data.

**Deeper explanation:** Labeling fails quietly when the task is ambiguous. "Is this answer good" produces 60 percent agreement; "does every factual claim appear in the provided policy text" produces 90. Decompose quality into checkable properties and label those.

```text
label schema v3 (support_answer)
  faithful_to_context:  yes / no / no_context
  answers_question:     fully / partially / no
  failure_type:         stale_policy | missing_retrieval | misread | injection | other
  preferred_rewrite:    optional free text (becomes a reference answer)
guidelines: worked examples; versioned with every change
```

Measure agreement per field, as simple percent on the overlapping subset or Cohen's kappa for a chance-corrected view, because a schema can be reliable on faithfulness and unreliable on tone. Label Studio, Argilla or a spreadsheet for a pilot all work; what matters is that each label links to the trace and the export is reproducible. Budget labeling as a recurring cost, because the eval set must keep up with traffic.

**Follow-ups they will ask:**
- How much agreement is enough?: Near the level two careful experts reach; investigate the disagreements rather than averaging them away.
- How do you sample for value?: Random for unbiased metrics, judge-signal disagreement for learning, new-intent clusters for coverage.
- How do labels feed the judge?: The labeled set is the judge's calibration set; judge-label agreement is tracked as a metric.

**Mistakes to avoid:**
- Launching labeling without a pilot and agreement measurement.
- Labeling only complaints, which gives a dataset of failures with no base rate.

### Q. A production failure was found. How does it become an eval case, and when does it become training data?

**Short answer (45 seconds):** First the eval case, within the day: pull the trace, redact PII, write input, context identifiers and expected behavior as a rubric, tag slice and failure type, and add it to the suite so the regression cannot return. Then fix the right layer: prompt, retrieval, data or model. Training data comes later and only in volume: when a failure type recurs across hundreds of cases that prompting cannot fix, curated inputs with corrected outputs become a fine-tuning or preference dataset, with consent, redaction and a held-out portion.

**Deeper explanation:** Trace to eval item is nearly mechanical:

```python
def trace_to_eval_item(trace, correction: str, failure_type: str) -> dict:
    return {"id": f"prod-{trace.id[:8]}", "source": trace.id,
            "slice": trace.metadata["intent"], "failure_type": failure_type,
            "input": redact(trace.input), "context_ids": trace.retrieval.chunk_ids,
            "rubric": correction, "added": date.today().isoformat()}
```

Two details matter. Freeze the context: store chunk IDs and index version, or the chunk text, so the item tests the model's behavior rather than today's retrieval results. Training data has stricter requirements: consent and redaction, deduplication, balance across slices so the model does not overfit to complaint-heavy intents, and a strict split so the tuned model is evaluated on unseen cases. Many teams never reach training because eval-driven prompt and retrieval fixes solve most failure types.

**Follow-ups they will ask:**
- Who writes the expected behavior?: The person who triaged, reviewed by a domain owner; a rubric rather than one golden sentence.
- How do you keep the eval set from growing without bound?: Retire items that have passed for months and are covered by newer ones; keep a core regression set.
- Is a single failure worth an item?: Almost always; minutes of cost for the cheapest regression protection you have.

**Mistakes to avoid:**
- Fixing the prompt and moving on with no eval item, so the failure returns at the next edit.
- Adding cases without freezing context, so the item flips with every index update.

### Q. When does fine-tuning on production data make sense instead of prompt or retrieval changes, and how do you do it safely?

**Short answer (45 seconds):** Fine-tuning makes sense when the behavior you want is stable and stylistic or structural (format, vocabulary, tone, shorter prompts for a high-volume feature) and you have thousands of clean, representative examples. It does not fix missing knowledge, which is retrieval's job, and it is a poor first response to a failure a prompt change could address in a day. Safely means redacted, consented, deduplicated and balanced data, a strict held-out set, the same eval suite plus checks for forgetting and safety, and the same canary and rollback as any model change.

**Deeper explanation:** The escalation ladder, cheapest and most reversible first:

```text
1. prompt change          hours   reversible instantly    instructions, format, tone
2. retrieval or data fix  days    reversible              missing or stale knowledge
4. fine-tuning            weeks   new artifact to manage  style, format, latency and cost
```

Fine-tuning's real payoffs are operational: a smaller tuned model that matches a large model on a narrow task cuts cost and latency, and a model that needs no 2,000-token instruction block saves input on every call. Its costs are operational too: a new model version to register, evaluate, deploy and monitor, and a dataset to govern. Test for regressions outside the training distribution, loss of safety behavior, memorized examples leaking into outputs, and overfitting to complaint-heavy slices. Treat the tuned model as a challenger, with the prompt-based configuration as fallback.

**Follow-ups they will ask:**
- How many examples do you need?: Hundreds for a narrow format, thousands for broad style; quality beats quantity.
- Preference tuning or supervised?: Supervised on corrected outputs for format and style; preference pairs when "better" is easier to label than "correct".
- What about PII in training data?: Redact before it enters the dataset and record consent and source per example.

**Mistakes to avoid:**
- Reaching for fine-tuning to inject knowledge that changes weekly.
- Training on raw production logs without redaction, deduplication and a held-out split.

### Q. What is feedback bias in these loops, and how do you counter it?

**Short answer (45 seconds):** Feedback bias is any systematic gap between what signals say and what is true. Selection bias: only frustrated or delighted users click. Exposure bias: you only get feedback on answers the system chose to give. Reviewer anchoring: labelers who see the model's answer judge it leniently. Self-reinforcement: tuning on the model's own accepted outputs narrows it toward its current style. Counter each with random sampling, labels independent of signals, blind review, human-written references and monitoring for homogenization.

**Deeper explanation:** The most dangerous bias makes the loop look like it works: promoting prompts that raise thumbs-up rates may select for answers that please rather than answers that are correct.

| Bias | Symptom | Counter |
|---|---|---|
| Selection | Feedback from 3 percent of users | Random sampled review for base rates |
| Exposure | Never learn what unseen answers would do | Shadow or pairwise comparisons |
| Anchoring | Labelers agree with the model too often | Blind labeling before seeing the output |
| Self-reinforcement | Outputs converge in style | Keep human-written data; monitor diversity |

Measure it: feedback rate by segment, judge scores on random versus flagged samples, and a periodic blind-labeled random slice. Keep the primary quality metric anchored outside the loop, resolved tickets or expert review, so a pleasing but wrong model cannot win.

**Follow-ups they will ask:**
- Is thumbs-up rate a bad metric then?: A useful relative signal between versions and a poor absolute measure of correctness.
- How do you detect sycophancy drift?: Eval items where the user asserts something false and the right answer corrects them; track pass rates over versions.
- What is the simplest counter to adopt first?: A weekly random sample reviewed blind; it anchors everything else.

**Mistakes to avoid:**
- Promoting whatever maximizes positive feedback without an external correctness check.
- Letting reviewers see the model's answer before forming their own judgment on high-stakes items.

### Q. How do you close the loop from a signal to a deployed improvement without introducing regressions?

**Short answer (45 seconds):** By making the loop pass through the same gates as any other change. Signals are triaged into failure types; each gets an eval item and an owner; the fix is a new prompt version, retrieval change or routing rule; the candidate is compared with production on the full eval set; a reviewer reads the regressions; the change is canaried with metrics split by version; promotion is a logged label move with rollback. Nothing from the loop writes directly to production.

**Deeper explanation:** The loop needs a cadence and roles or it decays into a backlog:

```text
daily    sampled review queue -> failure types, eval items, judge disagreements
weekly   triage top failure types by volume and severity -> owners, candidate fixes
weekly   candidate evals vs production -> review regressions -> canary -> promote or drop
monthly  eval set refresh from production; judge recalibration
```

Two safeguards: a fixed core regression set every candidate must pass, independent of the week's hot failures, so fixing refunds cannot silently break shipping questions. A change budget: limit prompt promotions per feature per week, because rapid successive changes make attribution impossible. Automation moves candidates and evidence, not the production label; the canary abort is the one automatic action.

**Follow-ups they will ask:**
- Can any of this be fully automatic?: Eval runs, reports, canary aborts and rollback; promotion of behavior changes keeps a human until the gates have a long record.
- How do you attribute a quality change?: One behavior change at a time per feature, versions on every trace, canary analysis by version.
- What when fixes for two failure types conflict?: Track both slices in the eval set and let the review decide the trade-off, not the last edit.

**Mistakes to avoid:**
- A loop that auto-promotes prompts on feedback metrics, which optimizes for pleasing users and drifts quietly.
- Treating the review queue as a support task disconnected from the eval set and release process.

### Practice
- Add a feedback endpoint to a chat feature that writes a score onto the trace with a reason code, then build the query "thumbs-down by prompt version and reason for the last 7 days" and read ten of the traces.
- Pick two implicit signals for a feature you know, label 100 interactions by hand, and compute how well each signal predicts your label; keep the better one and write down its failure cases.
- Convert five real or realistic failures into eval items with frozen context and rubrics; run the current prompt against them, then make a fix and show the full suite still passes.
- Say it out loud: describe your weekly loop from signals to a promoted prompt in 90 seconds, including the two safeguards that stop it from making the product worse.

## Cost Management & FinOps for AI

> Cost questions have become standard in senior AI interviews because LLM features are the first product surface where a code change can double the cloud bill overnight. Interviewers want to hear that you think in cost per task rather than per token, that you know the levers in order of effectiveness, that you can attribute spend to features and tenants, and that you have alerts for the failure modes that burn money, such as agent loops and retry storms. A weak answer is "we use a cheaper model". A strong answer is a measured plan with budgets, levers and guardrails.

### Concepts you must understand
- Spend is driven by input tokens, output tokens (usually priced several times higher), cache reads and writes, and for agentic features by the number of model calls per task; cost per completed task is the metric that matters.
- A token budget per feature is a design constraint: maximum context assembled, maximum output, maximum tool iterations, enforced in code and watched on a dashboard.
- Prompt caching, request batching, output length control, context trimming and routing to smaller models are the main levers, roughly in order of how safely they cut cost without hurting quality.
- Quotas and rate limits per tenant protect both the budget and the provider rate limits; they are enforced at a gateway with graceful degradation rather than hard failures where possible.
- Attribution needs tags on every call (feature, tenant, environment, prompt version, experiment arm) and a versioned price table; chargeback or showback reports turn tags into invoices or dashboards per team or customer.
- Self-hosted models shift cost from tokens to GPU hours; utilization, batching efficiency and right-sizing decide whether self-hosting is cheaper, and idle GPUs are the most common waste.
- Anomaly detection on spend catches runaway loops, retry storms, prompt changes that ballooned context, and cache regressions, and it needs both absolute caps and baseline-relative alerts.
- Cost work is iterative: measure a baseline, change one lever, re-run the eval suite, compare quality and cost per task, keep or revert.

### Q. How do you set and enforce a token budget for an LLM feature?

**Short answer (45 seconds):** Start from the business number: what the feature may cost per use or per month, and what a typical request costs today. Translate that into technical limits: a cap on assembled context (retrieved chunks, history), a `max_tokens` sized to the task, a cap on tool iterations and model calls per request for agentic flows, and a per-request cost ceiling that aborts gracefully. Enforce them in code at the orchestration layer, log actual usage on every trace, and chart cost per request and per task against the budget.

**Deeper explanation:** Enforce it where tokens are assembled:

```python
BUDGET = {"max_context_tokens": 6000, "max_output_tokens": 600,
          "max_model_calls": 6, "max_cost_usd": 0.05}

def build_context(chunks, counter):
    ctx, used = [], 0
    for item in chunks:                       # most relevant first
        n = counter.count(item.text)
        if used + n > BUDGET["max_context_tokens"]:
            break
        ctx.append(item); used += n
    return ctx
```

Count tokens before the call with the provider's token counting endpoint or a close approximation. Size the output cap to the task: tens of tokens for a classification, a few hundred for a drafted email; a high default is a silent cost multiplier when the model gets verbose. For agents the iteration cap is the most important control, because a loop that cannot decide spends until something stops it.

**Follow-ups they will ask:**
- What happens when the budget is hit?: A designed fallback, not an exception: a shorter answer, a handoff, or a message that the request was too complex.
- How do you choose the numbers?: From current usage distributions and the quality curve on the eval set: the context size beyond which quality stops improving.
- Do budgets differ per tenant?: Yes; plan tiers carry their own budgets through the same config layer that picks models.

**Mistakes to avoid:**
- Setting `max_tokens` very high "to be safe", making verbose outputs the default cost.
- Having no iteration cap on an agent loop.

### Q. Caching and routing are the two big cost levers. How do you decide where to apply them and how do you measure the effect?

**Short answer (45 seconds):** Caching first, because it does not change outputs: find features with a large stable prefix, make the prefix identical across requests, mark it for caching, and confirm with the usage fields that most input tokens are cache reads. Routing second, because it does change outputs: send easy requests to a smaller model, only after the eval suite shows it holds quality on that slice. Measure both as cost per task plus eval quality.

**Deeper explanation:** Caching pays when the prefix is reused within the cache lifetime: reads cost a small fraction of the input price and writes a premium, so a prefix shared by a few requests within the window pays off. The work is prefix hygiene: static content first, deterministic serialization, no timestamps or per-user text in the system prompt, one tool set and model per conversation.

```text
request -> cheap classifier (small model or rules) -> tier
  tier A (simple lookup, short answer)         -> small model, cached prefix
  tier B (multi-step reasoning, drafting)      -> mid model
  tier C (ambiguous, high-stakes, escalation)  -> large model, sampled human review
```

Lower reasoning effort on a capable model is often a better first step than a smaller model: one cache namespace, one behavior profile; measure both on the same eval set.

**Follow-ups they will ask:**
- How do you know caching is working?: Cache read tokens over total input tokens per feature; a low ratio with a big static prefix is a bug.
- What is the risk in routing?: Misroutes to the small model; measure misroute rate with sampled judging and keep an escalation path.
- Does batching help?: For offline work; batch endpoints run asynchronously at a discount, often half price.

**Mistakes to avoid:**
- Routing to a smaller model on cost alone without an eval on the routed slice.
- Breaking the cache with a timestamp in the prefix and never checking usage.

### Q. How do you design quotas and rate limits per tenant for an LLM product?

**Short answer (45 seconds):** Enforce them at a gateway in front of the orchestration layer, keyed by tenant and feature, with two kinds of limits: a rate limit for burst protection (requests or tokens per minute) and a quota for budget protection (tokens or cost per day, tied to the plan). Use a shared store such as Redis so limits hold across replicas, reserve an estimate before the call and reconcile after, return a 429 with a retry hint, a product-level message for exhausted quotas, and degrade gracefully before hard denial.

**Deeper explanation:** A daily token quota in Redis, reserving before the call and reconciling after:

```python
def reserve(tenant: str, est_tokens: int, limit: int) -> bool:
    key = f"quota:{tenant}:{date.today():%Y%m%d}"
    used = r.incrby(key, est_tokens)
    if used == est_tokens:
        r.expire(key, 2 * 86400)
    if used > limit:
        r.decrby(key, est_tokens)
        return False
    return True
# after the response: r.incrby(key, actual_tokens - est_tokens)
```

Rate limits use a token bucket in the same store and also protect you from the provider's limits, which all tenants share: one noisy tenant can starve everyone, so per-tenant limits plus a global concurrency cap with fair queuing is the usual design. Make limits visible: a usage endpoint, alerts at 80 percent, plan upgrades as the product response. Internal batch jobs need quotas too; they are the classic surprise invoice.

**Follow-ups they will ask:**
- Tokens or requests?: Tokens or cost for quotas, since requests vary enormously in size; requests per minute as a simple burst guard.
- Streaming with unknown output size?: Reserve against the output cap, reconcile with actual usage after the stream completes.
- When the provider rate-limits you?: Back off with jitter, shed low-priority traffic first, fail over if configured, alert.

**Mistakes to avoid:**
- Enforcing limits in each replica's memory, which multiplies the limit by the replica count.
- Hard-failing at the quota with no degradation path and no visibility for the customer.

### Q. How do you attribute LLM spend to features, teams and customers, and what does a chargeback report look like?

**Short answer (45 seconds):** Tag every model call with feature, tenant, environment, prompt version and experiment arm, record the exact model ID and token usage, compute cost with a versioned price table, and write it to the warehouse with the trace ID. Attribution is then a group-by: by feature for product decisions, by tenant for chargeback and margin, by prompt version to see what a change did, by environment to catch dev and CI spend. Report cost per unit of value and its trend.

**Deeper explanation:** Enforce tagging: a wrapper that refuses calls without a feature tag is worth the friction, because untagged spend is unattributable forever.

```sql
SELECT tenant_id, feature, sum(cost_usd) AS cost,
       sum(cost_usd) / nullif(count(DISTINCT task_id), 0) AS cost_per_task,
       sum(cache_read_tokens)::float
         / nullif(sum(input_tokens + cache_read_tokens), 0) AS cache_ratio
FROM llm_usage WHERE day >= current_date - 30
GROUP BY 1, 2 ORDER BY cost DESC;
```

Reconcile the monthly sum against the provider invoice; a gap means missing instrumentation or untagged traffic. For chargeback, the price table plus a margin becomes the internal rate; for showback the same report drives budget conversations. Self-hosted models allocate GPU cost by tokens or GPU-seconds, an approximation to document. Keep dev, CI and eval spend separate but visible; judges can quietly become a large line item.

**Follow-ups they will ask:**
- How do you attribute shared costs such as embeddings for a common index?: By index usage per feature or tenant, with the rule stated in the report.
- What about failed or retried calls?: They cost money; attribute them to the feature with a retry-cost line so the fix gets prioritized.
- Who consumes the report?: Finance for invoice reconciliation, product for per-feature margins, engineering for the levers.

**Mistakes to avoid:**
- Reporting totals without a per-task denominator; growth looks like waste and waste looks like growth.
- Letting untagged traffic exist; it is the first thing a CFO asks about.

### Q. You self-host an open-weight model on GPUs. What do you measure to know whether it is cost-effective, and how do you improve utilization?

**Short answer (45 seconds):** Measure GPU utilization and memory, tokens per second per GPU, time to first token and p95 latency under load, and the resulting cost per thousand tokens including idle time; then compare with the API price for equivalent quality on your eval set. Improve utilization with a serving engine that does continuous batching, quantize where quality holds, scale replicas on queue depth rather than CPU, and schedule batch work into idle capacity.

**Deeper explanation:** The trade-off is throughput against latency: larger batches raise tokens per second per GPU but increase time to first token, so the operating point depends on the feature.

```text
per replica:   GPU util, memory, requests in flight, queue wait
per request:   ttft, tokens/sec during generation, total latency
economics:     cost per 1M tokens = GPU $/hr / (tokens/sec * 3600 / 1e6) at target p95
utilization:   busy GPU-hours / provisioned GPU-hours (idle is pure waste)
```

vLLM or TensorRT-LLM implement continuous batching and paged attention so one GPU serves many concurrent streams; a naive server runs one request at a time. Quantization (8-bit or 4-bit weights) shrinks memory and raises throughput but is a model change that goes through the eval suite. Autoscale with a minimum replica count, because loading weights takes minutes; scale-to-zero suits only latency-tolerant internal tools.

**Follow-ups they will ask:**
- When does self-hosting win?: Steady volume that keeps GPUs busy, strict residency, or a tuned small model replacing a large API model on a narrow task.
- How do you compare quality fairly?: Same eval set, rubric and judge, with cost per task as the second axis.
- Multi-model serving on one GPU?: Possible for small models with spare memory, but contention makes latency unpredictable; measure first.

**Mistakes to avoid:**
- Comparing GPU hourly price to API token price without utilization and engineering time.
- Quantizing or shrinking the model without re-running the eval suite.

### Q. What goes on a cost dashboard for AI features, and how do you detect spending anomalies before the invoice arrives?

**Short answer (45 seconds):** Spend by feature, tenant and model; cost per task and tokens per request as distributions; cache read ratio; model calls per task for agents; retry and error rates; today against the same weekday's baseline. Anomaly detection combines absolute caps (hourly spend per feature, per-request cost) with baseline-relative alerts (tokens per request well above the trailing window). Classic anomalies: a looping agent, a retry storm after a provider incident, a prompt change that doubled context, a cache regression.

**Deeper explanation:** A stable average cost per request can hide a tail of requests costing fifty times the median, which is what a looping agent looks like, so chart p50, p95 and max and alert on the tail.

```text
hard caps:   per-request cost > 0.50 USD -> abort; feature hourly spend > cap -> page
relative:    tokens/request p95 > 2x trailing 7-day p95 for 15 min -> ticket
structural:  cache_ratio below half its baseline -> ticket
             model calls per task p95 near the iteration cap -> investigate loops
```

Annotate charts with deploys and prompt promotions, since most spend steps follow a change. Enforce the per-request ceiling in code, not just in alerts: alerts say it happened, caps stop it at scale. Show retry cost as its own line.

**Follow-ups they will ask:**
- Who gets the alert?: The feature owner for structural alerts, on-call for hard caps, finance only in the weekly report.
- How do you avoid false alarms on launch days?: Alert on per-request and per-task ratios, which should be stable, and on absolute caps you raise deliberately.
- Can the provider console replace this?: It gives totals per key; attribution by feature, tenant and version exists only if you build it.

**Mistakes to avoid:**
- Only alerting on total daily spend, which fires after the damage is done.
- No per-request ceiling in code, so the alert is the only control.

### Q. Leadership asks you to cut the LLM bill by 40 percent without hurting quality. What is your plan?

**Short answer (45 seconds):** Measure first: a token profile per feature (input, output, cache, calls per task) with the eval suite as the quality baseline. Then levers in order of safety: fix caching, trim context and tighten output caps where the eval shows no loss, batch offline work, cap agent iterations, then lower reasoning effort and route easy slices to smaller models with eval evidence, and finally self-hosting if volume justifies it. Each lever is measured on cost per task and eval score.

**Deeper explanation:** The profile picks the levers: 70 percent input tokens with a 4,000-token static prefix and a 10 percent cache ratio is a caching fix; 900-token outputs for yes-or-no questions is an output cap fix.

```text
step  lever                             quality risk
1     cache static prefixes             none
2     trim context, tighten max_tokens  low
3     batch offline work                none
4     cap iterations, dedupe calls      low
5     lower effort, route easy slices   medium (eval per slice)
6     fine-tune small model, self-host  high (steady volume only)
```

Run it with a scoreboard: baseline cost per task and eval score, one lever per iteration, a canary for anything that changes outputs, the weekly delta as cost per task. Fix structural leaks too: untagged spend, dev and CI traffic on production models, judges grading every request.

**Follow-ups they will ask:**
- What if caching is already optimal?: Then it is output tokens and call counts: verbosity, iteration caps, whether every step needs a model call.
- How do you prove quality did not drop?: Same eval set and judge before and after each lever, plus online guardrail metrics during the canary.
- What would you refuse to do?: Switch models or cut context on a high-stakes slice without an eval, or remove human escalation to save tokens.

**Mistakes to avoid:**
- Leading with "use a cheaper model", the riskiest lever, before the free ones.
- Reporting total spend instead of cost per task, so success looks like failure during growth.

### Practice
- Build a token profile for a feature from its traces: input, output and cache tokens per request as p50 and p95, and model calls per task; identify the lever with the largest expected saving and the lowest quality risk.
- Implement the Redis reservation and reconciliation quota for two tenants, run a load test that crosses the limit, and verify the degradation path returns a useful message rather than a stack trace.
- Add a per-request cost ceiling and an iteration cap to an agent loop, then make it loop on purpose and confirm the cap triggers and the trace shows why.
- Say it out loud: present a 40 percent cost reduction plan in two minutes with the levers in order, the quality evidence for each, and the metric you report weekly.
