## How LLMs Work, for Engineers

### Why it exists
Before large language models, every language task (classifying tickets, extracting fields, summarising, answering questions) needed its own model trained on its own labelled data, which most teams could not afford. An LLM is one model trained to predict the next token over a huge amount of text, and that turns out to be enough to do many of those tasks from written instructions alone. An engineer needs to know how it works because the mechanics explain the bill and the bugs: cost and latency grow with tokens, the context window is a hard limit, and the model is trained to produce plausible text, not true text. The trade-off is a component that is general and fast to build with but probabilistic, so every feature built on it needs checks around it.

## Prompt Engineering as Engineering

### Why it exists
The prompt is the program of an LLM feature, yet many teams treat it as a string someone edits in a dashboard until the output looks right. That breaks once the feature has real traffic: a wording change fixes one case and silently breaks others, nobody knows which version is live, and output that a parser depends on comes back in a slightly different shape. Treating prompts as engineering means versioning them in the repository, getting structured output through the API's schema features, ordering them so caching works, and testing every change against a dataset. The cost is process: an eval set, a review step and a release path for text that used to change in seconds.

## Embeddings & Vector Search

### Why it exists
Keyword search finds documents that share words with the query, so it misses "cancel my plan" when the policy says "terminate the subscription". Embeddings turn text into vectors (lists of numbers) where similar meanings land close together, and a vector index finds the nearest ones among millions in milliseconds using approximate algorithms such as HNSW. That makes search by meaning practical at product scale. The trade-offs: approximate search can miss the true nearest match, exact strings such as product codes and error ids are often handled worse than by keyword search, and every vector is tied to the model that produced it, so changing models means re-embedding everything.

## RAG Fundamentals

### Why it exists
An LLM only knows its training data, which is out of date and contains none of your company's private documents, so asked about your refund policy it will guess. Before RAG the options were fine-tuning the facts into the model, which is slow, expensive and bad at facts that change, or pasting whole documents into every prompt, which hits the context limit and the bill. Retrieval-augmented generation finds the few passages relevant to each question at request time and hands them to the model as evidence, so answers can be current, private and cited. The cost is a pipeline to run (parsing, chunking, embedding, indexing, keeping it fresh) and a new failure mode: when retrieval misses, the model still answers confidently.

## Advanced RAG Patterns

### Why it exists
Basic RAG (embed the question, fetch the top chunks, answer) handles single-fact lookups and fails on the questions users actually ask at scale: multi-step questions, numbers that live in a database, comparisons across many documents, and corpora where each user may see only some documents. Routing between sources, text-to-SQL, agentic multi-hop retrieval, graph-based retrieval and permission-aware filtering each exist to close one of those gaps. Every pattern adds latency, cost and new places to fail, so the senior move is to add one only when error analysis shows the failure it fixes.

## RAG Failure Modes & Debugging

### Why it exists
A RAG system can break in many places (ingestion, parsing, chunking, retrieval, ranking, generation), and the user only sees the final answer, which sounds equally confident whichever stage failed. Without a method, teams guess: they edit the prompt or switch models, which never fixes a document that was never indexed or a table that parsed into noise. Tracing every request, splitting failures into retrieval and generation, measuring retrieval on its own and reading failures in batches turn "the bot hallucinates" into a named defect at a specific stage. The cost is logging and labelling work up front, plus storing traces safely because they contain user data.

## Evaluating LLM Systems

### Why it exists
Traditional tests assert an exact output, but an LLM words things differently each run and many answers have no single correct form, so teams fall back to trying a few prompts by hand and shipping on a feeling. That hides regressions: a prompt or model change that improves the demo case can quietly break a slice of real traffic. Evals replace the feeling with a versioned dataset of real cases, pass or fail criteria checked by code, by a calibrated LLM judge or by people, and online signals from users. The cost is real work: labelling, judge calibration, eval compute on every change, and keeping the dataset current as traffic drifts.

## Safety, Security & Guardrails

### Why it exists
An LLM application reads text from people you do not trust (users, uploaded files, web pages, emails) and the model cannot reliably tell data from commands, so any of that text can act as an instruction. Once the model can call tools or render links, a hidden instruction can leak data or take actions the user never asked for, and classic defences such as input escaping do not apply to natural language. Guardrails and security design (least-privilege tools, approval steps, output validation, PII handling, tenant isolation) limit what a misled model can do instead of hoping it is never misled. They cost latency, false positives that block good requests, and their own test suite.

## Cost & Latency at the Application Layer

### Why it exists
LLM calls are priced per token and generate output one token at a time, so a feature that is cheap and quick in a demo can become the largest line on the bill and the slowest call in the product once real users send long conversations. Without attribution nobody knows which feature or tenant is spending the money, and without latency design users stare at a spinner. Usage logging, prompt caching, model routing, batch APIs, streaming and history management make cost and speed something you measure and steer per feature. Every saving trades against something, usually quality, freshness or complexity, so each one needs an eval gate.

## AI System Design Patterns

### Why it exists
A demo answers one person's questions; a production AI system serves thousands of strangers reliably, cheaply and safely, and the same problems show up every time: no visibility into failures, repeated work, unchecked outputs, missing knowledge and evals that go stale. The recurring patterns (observability, caching, evals, RAG, fine-tuning, feedback loops and guardrails) are the standard answers to those problems, so teams do not reinvent them for each feature. Each one costs build time and adds moving parts, so the design skill is picking the ones a problem needs and the order to add them, not bolting on all seven.

## Computer Vision & Document AI

### Why it exists
A lot of business data still arrives as pictures of documents: scanned invoices, photographed receipts, PDF drawings and forms, and for years the answer was people retyping them or brittle templates that broke when a vendor changed its layout. Document AI combines OCR, layout detection, table recognition and now multimodal models to turn those images into structured fields a program can use. The hard part is that errors look plausible (one misread digit in an amount), geometry needs specialist models, and quality has to be checked field by field. The trade-off is between flexible but hard-to-verify multimodal LLMs and cheaper, more predictable specialist pipelines that need training data.

## ML System Design Basics

### Why it exists
Many products need predictions that an LLM is too slow, costly or imprecise to make at volume: ranking a feed, scoring fraud, recommending items, flagging anomalies in sensor data. Classic ML systems learn these from your own historical data and are cheap to run per prediction, but they need a pipeline for features, training, deployment and monitoring. Without that pipeline models decay silently as behaviour changes, offline accuracy stops matching business results, and nobody can say why. The cost is data engineering and ongoing retraining, which is why ML design rounds dwell on data, metrics and monitoring more than on the model.

## LLM and RAG Project Scenarios [Scenarios]

> Project and design scenarios in this area start with a business ask ("an assistant over our documents", "cut the bill", "move to another provider") and leave the constraints for you to discover. Interviewers watch whether you clarify before drawing boxes: who the users are, how big and how fresh the corpus is, who may see what, what a wrong answer costs, and the latency and cost budget. A senior answer sizes the problem with rough numbers, picks a design with named trade-offs, plans the eval before the build, and ends with what goes on the dashboard and how to roll back.

### Concepts you must understand
- Ask first: users and volume, corpus size and growth, how often content and permissions change, languages, what a wrong answer costs, the latency budget, the cost budget per task and data residency.
- Estimate out loud: pages to chunks to tokens to embed, vectors times dimensions times bytes for index memory, and requests per day times tokens per request times price for the monthly bill.
- Decide the evaluation before the architecture: a small golden set from real or realistic inputs plus binary criteria tied to the business risk, so every later decision has a referee.
- Permissions, tenancy and actions are enforced in code and in the data layer; the model only sees what the user may see and can only do what the user may do.
- Record a version on every output (model, prompt, embedding model, parser, chunker), because migrations, rollbacks and debugging all depend on knowing which version produced what.
- Change one variable at a time behind a flag: offline eval, then shadow or canary traffic, then gradual rollout with an automatic rollback condition.
- Size human review to the blast radius: none for an FAQ answer, sampled for summaries, mandatory for money, contracts and irreversible actions.
- Report task success per slice next to cost per successful task, not a model score.

### Q. A client has 50,000 PDFs across 40 teams and wants one assistant where each person only gets answers from documents their team can open. How do you design it?
**Short answer (45 seconds):** I first ask where permissions live (SharePoint, Google Drive groups, an internal DMS), how often they change, how fast a revoke must apply, what share of PDFs are scans, and what a leaked answer costs. Then I size the corpus, ingest each document's access list as metadata, retrieve with a mandatory permission filter resolved server-side, rerank, answer with citations and an abstain path, and evaluate per team.

**Deeper explanation:** The page count is the first unknown, so I state an assumption and size from it:

```text
50,000 PDFs x 20 pages (assumed, confirm)  = 1M pages
2 chunks per page at about 400 tokens       = 2M chunks, about 800M tokens to embed once
2M vectors x 1024 dims x 4 bytes            = about 8 GB raw, plus HNSW graph overhead
```

That fits one Qdrant or pgvector deployment, so I pick what the team already runs. Ingestion runs through a queue: per-page routing (text layer versus OCR), a parse-quality gate, chunking and embedding, and every chunk stores `document_id`, `group_ids`, `acl_version`, `content_hash` and `embedding_model`. Nested groups are flattened at sync time so the query filter is a plain any-match on group ids. A revoke arrives by webhook or delta sync and updates payloads only, with no re-embedding, against a permission-lag target agreed with the client. At query time the user's groups come from the identity provider, the data-access layer adds the filter, hybrid search returns 50 candidates, a reranker keeps 8, and the model answers with chunk ids. Document summaries and other derived artefacts inherit the source ACL, and answer caches are keyed by an ACL hash.

I would measure recall@k and faithfulness per team, abstain rate, permission-sync lag, p95 latency, cost per answer, and a cross-team leak test that must stay at zero.

**Follow-ups they will ask:**
- Access revoked mid-session?: The payload update and ACL-hashed cache keys apply it on the next query.
- Cross-team questions?: Retrieval uses the union of the user's groups; the answer cites only what they can open.

**Mistakes to avoid:**
- Filtering in application code after retrieval, which leaks into logs and returns too few results.
- Skipping the question of how many pages are scans, which drives cost and parse quality.

### Q. You inherit a support-summary feature that has run in production for six months with no evals, and the PM wants to switch models next month. What do you do in the first four weeks?
**Short answer (45 seconds):** I freeze non-urgent prompt edits, add tracing so every call is replayable, and read real traffic before defining any metric. From the failures I see I build a small golden set and binary checks, calibrate a judge against human labels, and record a baseline for the current model. The model switch then becomes a measured comparison, not a debate.

**Deeper explanation:**

```text
week 1  prompt into the repo with a version; trace request id, prompt version, model, input,
        output, tokens, latency, feedback; redact PII; export 200 recent traces
week 2  read 100 traces with a support lead, one-line note each, cluster into a taxonomy
        (missed action item, invented detail, wrong customer name, too long), count
week 3  golden set of about 150 de-identified cases; deterministic checks (required fields,
        length, language match) plus two or three binary judge criteria for the biggest
        buckets; hand-label 100 outputs and measure judge agreement
week 4  wire into CI, record the baseline, run the candidate with an adapted prompt,
        then shadow or A/B it
```

The best free label is already in the product: agents edit the generated summary before saving, so the diff shows what the model got wrong and the edit rate becomes the online metric. The judge should come from a different model family than the candidate so it does not favour its own style, and criteria stay binary with a written critique because 1 to 5 scores drift between labellers.

Risks: traces hold customer data, so redaction and retention rules come before export. If the PM wants the switch before week four, it ships behind a flag to a small share of traffic with the edit rate as the guardrail.

**Follow-ups they will ask:**
- How big must the set be?: Big enough that the gap between versions exceeds run-to-run noise; run each version twice to see that noise.
- No expert time for labels?: Start from agent edits and thumbs-down cases; the expert only settles disagreements.
- One number for the PM?: Must-pass rate per slice, with cost per summary beside it.

**Mistakes to avoid:**
- Starting from generic metrics such as BLEU or "helpfulness" before reading a single trace.
- Letting the candidate model judge its own outputs.

### Q. Your company is moving every LLM feature from OpenAI to Anthropic within a quarter, and leadership wants no visible quality loss. How do you plan the migration?
**Short answer (45 seconds):** I treat it as per-feature migrations, each gated by evals: inventory every call site, put a provider-neutral interface in front, baseline each feature on the current model, adapt prompts for the target model instead of copying them, then shadow, canary by tenant and keep a one-flag rollback. Embeddings are a separate project, because changing them means re-indexing.

**Deeper explanation:** The inventory lists each feature's model, parameters, tools, output format, volume and eval coverage; uncovered features get a minimal golden set first. The adapter must absorb these differences:

| Concern | OpenAI Chat Completions | Anthropic Messages |
|---|---|---|
| System prompt | a system or developer message | top-level `system` parameter |
| Tools | `tools[].function.parameters` | `tools[].input_schema` |
| Forced structure | `response_format` with a strict JSON schema | forced tool use with `tool_choice` |
| Stop signal | `finish_reason` | `stop_reason` |
| Output cap | optional | `max_tokens` required |
| Token counting | tiktoken | different tokenizer, `messages.count_tokens` |
| Prompt caching | automatic prefix caching | explicit `cache_control` breakpoints |
| Embeddings | embeddings endpoint | none, use another embedding provider |

The tokenizer difference bites twice: context-budget code that counted with tiktoken mis-trims, and cost per request changes even at a similar list price. Run each feature's suite on both models and close gaps with model-specific prompt versions. Then shadow traffic (copies sent to the new provider, judged offline, never shown), which needs the new provider's data processing agreement first. Canary by tenant with automatic rollback on pass rate, errors, latency or cost, and keep the old provider as fallback until every feature has been stable for a few weeks. Request rate-limit increases early.

I would measure per-feature pass-rate deltas, structured-output validity, tool-call accuracy, time to first token and cost per task.

**Follow-ups they will ask:**
- One feature cannot match quality?: Leave it on the old provider for now; the gateway makes mixed routing normal.
- Migrate embeddings too?: Later and separately, with a re-index and retrieval evals; one variable at a time.

**Mistakes to avoid:**
- Copying prompts verbatim and declaring success after a few manual checks.
- A big-bang cutover, where one regression hits every feature and nobody can tell which change caused it.

### Q. A finance team in Dubai and Bengaluru wants scanned and emailed vendor invoices turned into ERP entries, and a wrong amount is expensive. How do you design the extraction system?
**Short answer (45 seconds):** I clarify volume, vendor count, languages (English and Arabic in the UAE), whether line items are needed, the ERP target and the acceptable error per field. Then a staged pipeline: classify and normalise pages, OCR with layout, extract into a strict schema with every value grounded to page text, run deterministic validators, and route anything uncertain to a review queue whose corrections become the eval set. The headline metric is straight-through rate at a fixed error rate.

**Deeper explanation:**

```text
email or upload -> object store (file hash = idempotency key) -> queue
 -> classify page: invoice, credit note, delivery note, other
 -> text layer if digital; else rasterise, deskew, OCR with layout
 -> schema-forced extraction: header and line items, each with its source text
 -> validate: grounding, arithmetic, tax rules, vendor master, PO match, duplicates
 -> all pass and vendor trusted: post to ERP; else review UI with boxes highlighted
```

Validators do the heavy lifting. Line items sum to the subtotal; tax equals rate times taxable amount within rounding (UAE VAT at 5 percent; Indian GST as CGST plus SGST, or IGST for interstate supply). The supplier TRN (15 digits, UAE) or GSTIN (15 characters with a check character, India) must match the vendor master. Vendor plus invoice number must be unique to stop duplicate payments, and a bank account that differs from the vendor master always goes to review, a classic fraud pattern. Normalise Arabic-Indic digits, parse dates day first, and require each extracted amount to appear in that page's OCR text.

Confidence comes from validators and agreement between two extraction runs, not the model's self-reported score. Start with full review for the first weeks; reviewed outputs become labels, and a cheaper specialist model for the top vendors comes later if volume justifies it.

I would measure field-level exact match per field and vendor, straight-through rate, errors found after posting and cost per invoice.

**Follow-ups they will ask:**
- Engineering drawings instead?: Title-block fields (drawing number, revision, scale) work the same way; geometry needs vision models.
- Handwritten amounts?: Always human review, never auto-post.

**Mistakes to avoid:**
- Auto-posting on the model's word without arithmetic and duplicate checks.
- Reporting document-level accuracy, which hides the one field that is usually wrong.

### Q. You are building a support assistant for India and the UAE that must handle English, Hindi and Arabic, including Hinglish and Arabic typed in Latin letters. How do you design it?
**Short answer (45 seconds):** I sample real traffic first to see which languages and scripts appear, check whether help content exists per language or only in English, and confirm where policies differ by country. Then: detect language, script and market per message, retrieve across languages with multilingual embeddings plus keyword search, filter by market, answer in the user's language and script, and evaluate each language as its own slice with native-speaker reviewers.

**Deeper explanation:** Detection is the first trap: Devanagari and Arabic script are easy, but romanised Hindi and Arabizi (Arabic in Latin letters, with digits such as 3 and 7 standing for Arabic sounds) look like English to many detectors. A small model call returning language, script and market as JSON works better.

Two retrieval options to test against each other:

| Option | How | Trade-off |
|---|---|---|
| Multilingual embeddings | BGE-M3 or multilingual-e5 over English docs | one index; recall on mixed-script queries varies, so measure it |
| Translate the query | rewrite to English, then English dense plus BM25 | an extra call, but keyword search keeps working on product names |

Often both run in parallel, merged with reciprocal rank fusion; Arabic keyword search needs normalisation of letter variants and diacritics. Every chunk carries `market` (AE or IN) so a Dubai customer never gets the Indian return policy. The system prompt says to reply in the customer's language and script, with a glossary of product names that are never translated. In React each message bubble gets `dir="auto"` so mixed Arabic, English and numbers render correctly. Non-Latin scripts often cost more tokens per word, so budget per language from measured usage. Handoff routes by agent language, and India's DPDP Act and the UAE's PDPL shape provider region and log retention.

I would measure, per language and script: retrieval recall, answer correctness, language-match rate and escalation rate.

**Follow-ups they will ask:**
- No Arabic speaker on the team?: Contract native reviewers to label and calibrate; a judge alone cannot be trusted on dialect.
- Translate the help centre up front?: Only the top articles, reviewed, because every translation adds maintenance.

**Mistakes to avoid:**
- Evaluating only in English and assuming quality transfers.
- One global index with no market filter, mixing country policies.

### Q. Finance says the LLM bill must halve next quarter without any drop in quality. How do you plan it?
**Short answer (45 seconds):** I do not start by swapping in a cheaper model. First I attribute cost by feature, route and tenant from per-response usage fields, and freeze a quality baseline per feature. Then I work the levers in order of risk, each behind a flag with an eval gate, tracking cost per successful task.

**Deeper explanation:** Cost is requests times calls per request times tokens per call times price per token, and each lever moves one factor:

| Lever | Factor it cuts | Eval gate |
|---|---|---|
| Static prefix first, no timestamps or ids at the top | input price, via cache reads | cache-read share rises |
| Dedupe retries, cap agent steps | calls per request | completion rate |
| Rerank to fewer chunks, summarise old history | input tokens | recall@k, faithfulness |
| Task-sized `max_tokens`, concise style | output tokens | truncation rate, pass rate |
| Batch APIs for offline jobs, about half price on both vendors | price | job deadline met |
| Small model or cascade for easy tasks | price | per-slice pass rate |
| Semantic cache on generic FAQ routes | requests | audited hit precision |

Attribution usually shows a few features and a tail of expensive requests (long histories, agent loops) carrying most of the bill, so the work goes there. One change per feature at a time: offline eval, A/B against the baseline, rollout. If the cheap levers do not reach half, I show a cost-versus-quality curve per feature and let the product owner choose; fine-tuning or self-hosting a small model for one high-volume task comes last, priced with GPU idle time and on-call.

I would measure cost per successful task per feature, pass rate per slice, p95 latency and cache-read share, reconciled monthly against the invoice.

**Follow-ups they will ask:**
- Why cost per successful task?: A cheap model that fails more often makes users retry, which can cost more in total.
- Quick win in week one?: Prompt caching and `max_tokens`, because neither changes what the model is asked to do.

**Mistakes to avoid:**
- Changing several levers at once, so neither savings nor regressions can be attributed.
- Reporting tokens saved instead of cost per successful task.

### Practice
- Write a one-page sizing sheet for the 50,000-PDF assistant: pages, chunks, tokens to embed, vector memory with and without quantisation, embedding cost from the current price page, and a p95 latency budget per hop.
- Build a thin provider adapter with two vendors behind one interface, run the same 30-case suite on both, and list every behaviour difference you had to absorb.
- Open-code 100 traces from any LLM feature you have, produce a failure taxonomy with counts, and turn the top three buckets into binary criteria with a judge you calibrate against your own labels.
- Say it out loud: a three-minute answer to the cost-halving scenario that names the cost formula, the first two levers and the metric you report upward.

## LLM and RAG Incidents & Error Cases [Scenarios]

> Incident questions hand you a symptom (an error string, a graph shape, an angry user) and grade the order of your moves. Use the same five steps each time. Clarify impact: who, how many, since when, which tenant, feature or route. Contain: feature flag off, index alias rolled back, old model pinned, a tool disabled. Diagnose from traces and usage data by asking what changed: deploy, prompt version, index build, model alias, provider, traffic. Fix the cause rather than the symptom. Prevent a repeat with a regression case, an alert and a runbook entry. Weak answers jump to "tweak the prompt" or "use a better model"; strong answers name the trace fields, queries and dashboards they would open.

### Concepts you must understand
- Classify early: data and retrieval (index, parsing, filters), generation (prompt, model, parameters) or platform (provider, rate limits, your own code); each has different evidence and a different owner.
- Ask "what changed?" first: put deploys, prompt versions, index builds, model aliases, provider status and traffic mix on one timeline against the moment the metric moved.
- Contain before you diagnose, using rollback levers built in advance: feature flags, index aliases, pinned model snapshots and per-tenant kill switches.
- An incident is closed only when the failing case is in the golden set or test suite and an alert would have caught it earlier.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| OpenAI 400 `context_length_exceeded`; Anthropic 400 `prompt is too long: N tokens > M maximum` | Token count per prompt component in the trace | Unbounded history, raw tool output, raised top-k, fallback to a smaller window | Budgeted context builder, pre-flight token count, summarise history |
| `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` | Raw output text | Prose preamble or a code fence around the JSON, a refusal | Schema-forced output or forced tool use, validate, dead-letter queue |
| `Unterminated string starting at` or Node `SyntaxError: Unexpected end of JSON input` | `stop_reason` is `max_tokens`, or `finish_reason` is `length` | Output truncated on long inputs | Larger `max_tokens`, split the input, check the stop reason before parsing |
| Pydantic `Field required [type=missing` on valid JSON | Prompt version versus schema version | Schema changed in code but not in the prompt or tool | Version prompt and schema together, nullable fields, one retry with the error |
| HTTP 429 `rate_limit_error` (Anthropic) or `rate_limit_exceeded` (OpenAI) | `anthropic-ratelimit-*` or `x-ratelimit-remaining-*` headers, retry counts | Burst, retry storm, one key shared by every service | Backoff with jitter honouring `retry-after`, per-tenant quotas, separate keys |
| Anthropic 529 `overloaded_error`, or p95 time to first token spikes while your own spans are flat | Provider span versus your spans, provider status page | Provider capacity or regional incident | Timeout on first token, fallback model or provider, circuit breaker |
| Qdrant `Vector dimension error: expected dim: 1536, got 3072`; pgvector `expected 1536 dimensions, not 3072` | Embedding model in the query service versus the index manifest | Model changed on one side only | Re-embed into a new collection, switch alias, startup check |
| Recall drops for older documents with no errors | `GROUP BY embedding_model` over chunks | Same-dimension model swap, partial re-embed | Full re-embed, model version on every vector |
| One tenant suddenly gets zero results | Filter selectivity and index type | pgvector HNSW filtering after `ef_search` candidates, missing payload field | `hnsw.iterative_scan`, payload index, exact scan for small subsets |
| A citation opens a passage that does not support the claim | Cited id present in the prompt, quote substring check | Position-based ids reordered after rerank, version mismatch, model attribution | Stable chunk ids, quote verification, snapshot of cited text |
| Output contains an external image or link, or an unexpected tool call after reading a file | Chunks in the prompt before that output | Indirect prompt injection | Quarantine, no side-effect tools in that turn, URL allowlist, CSP |
| A retrieved chunk's `tenant_id` differs from the requester's | Retrieval path and cache key in the trace | Missing filter on a new path, cache without tenant, RLS bypassed | Data-layer filter, forced RLS, post-retrieval assertion |
| Daily cost jumps with flat traffic | Cost by feature, prompt version and hour; cache-read tokens | Broken cache prefix, retry or agent loop, alias moved to a pricier model | Restore the stable prefix, retry and step caps, pin model ids |
| Eval pass rate drops after a model bump | Judge pinned? Deterministic versus judge failures | Format drift, prompt tuned to the old model, stale labels | Per-model prompt versions, pinned snapshots, fix labels |

### Q. After a weekend re-index that also moved to a new embedding model, answers about older documents became wrong while new documents look fine. What do you do?
**Short answer (45 seconds):** I treat it as an index defect until proven otherwise. If the previous collection still exists I point the alias back, which restores service in seconds. Then I check whether the index holds vectors from two embedding models, or whether the query and document sides use different models. A swap between same-dimension models throws no error; retrieval just ranks noise.

**Deeper explanation:** Confirm with the canary set (queries with known expected chunks) against old and new collections, split by ingest batch. Then count vectors per model:

```sql
SELECT embedding_model, count(*), min(indexed_at), max(indexed_at)
FROM chunks
GROUP BY embedding_model;
```

In Qdrant, `client.count` with a `FieldCondition` on `embedding_model` and `exact=True` does the same. Without a model field, re-embed a stored chunk's text with both models and compare cosine similarity with the stored vector; the model that produced it scores close to 1. Then check when the query service's config changed relative to the job.

Likely causes, in the order I check them:
1. Partial re-embed: the job skipped documents whose content hash was unchanged, so old documents kept old-model vectors. This matches the symptom exactly.
2. Query embedder and index on different models, because two services deployed at different times.
3. The re-index dropped metadata such as `is_latest`, so superseded versions now compete.
4. A new parser version degraded tables or scans in older PDFs.

Different dimensions fail loudly instead, with pgvector's `expected 1536 dimensions, not 3072` or Qdrant's vector dimension error. The fix is a complete re-embed into a fresh collection, golden-set and canary runs, then an alias switch. Prevention: an index manifest (embedding model, dimension, parser and chunker versions) per collection, a query service that refuses to start on a mismatch, model and parser versions inside the skip-if-unchanged hash, and a canary gate on every alias switch.

**Follow-ups they will ask:**
- The old collection was already deleted?: Re-embed only the stale subset now, and keep the previous index for a set number of days next time.
- How would you catch it without users?: Scheduled canary queries plus a monitor on the top-1 similarity score distribution.

**Mistakes to avoid:**
- Editing prompts or blaming the LLM before counting vectors per model.
- Re-embedding in place inside the live collection.

### Q. Users report that citations open passages that do not say what the answer claims. How do you investigate?
**Short answer (45 seconds):** I pull the traces for the reported answers and check each citation in order: was the cited id in the prompt, does that chunk support the sentence, and does the UI open the same text the model saw. That separates a mapping bug in our code, a version mismatch and a model attribution error, which have different fixes. In parallel I measure the rate on a sample.

**Deeper explanation:** To size it, send each cited sentence and its chunk from a few hundred recent answers to a calibrated judge for yes or no, grouped by route and day. Causes, in the order I check them:

1. Position-based ids. The prompt labels chunks [1] to [8], but the renderer maps numbers onto a list reordered by reranking or deduplication, so [3] opens another chunk. Signature: the supporting passage is in the prompt under another number. Fix: stable ids such as `doc_812#c14` end to end.
2. Version mismatch. The link opens the latest document version, or the printed page label instead of the PDF page index. Fix: store the cited text and version with the answer and deep-link to that version and page.
3. Model attribution. The claim came from memory or a blend of chunks, with the nearest id attached. Signature: no chunk supports it. Fix: a verbatim quote per citation verified in code, unsupported sentences dropped or flagged, fewer and better chunks, or Anthropic's citations feature, which returns cited spans.
4. Truncation. The context budget cut the supporting sentence from the chunk.

```python
for c in answer.citations:
    chunk = prompt_chunks.get(c.chunk_id)
    if chunk is None:
        flag(trace_id, "fabricated_id", c)
    elif normalise(c.quote) not in normalise(chunk.text):
        flag(trace_id, "quote_not_in_chunk", c)
```

Prevention: citation precision in CI and on a daily production sample with an alert, plus a UI test of id-to-chunk mapping after reranking.

**Follow-ups they will ask:**
- The claim is right but the citation is wrong?: Still a defect, because users verify through citations and stop trusting them.
- Judge cost?: Sample for the judge, and run the substring check on everything.

**Mistakes to avoid:**
- Adding "cite accurately" to the prompt and closing the ticket.
- Checking that a cited id exists but never that it supports the claim.

### Q. Production logs show a rising number of 400 errors: `context_length_exceeded` on the OpenAI route and "prompt is too long" on the Anthropic route. What do you do?
**Short answer (45 seconds):** Contain first: catch the error and retry once with a trimmed context so users get an answer, not a failure. Then find which part of the prompt grew from per-component token counts in the trace: history, tool results, retrieved chunks or an upload. The real fix is a context builder with an explicit token budget and pre-flight counting, so our code enforces the limit before the provider does.

**Deeper explanation:** Scope by route, tenant and model, and line the start up against deploys, new tools, retrieval config changes or model fallbacks. Look at the tail:

```sql
SELECT route, date_trunc('day', created_at) AS day,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY input_tokens) AS p99_input
FROM llm_calls
WHERE created_at > now() - interval '14 days'
GROUP BY 1, 2
ORDER BY 2, 1;
```

Likely causes, in the order I check them:
1. Unbounded history: some users keep one chat open all day.
2. A raw tool result: a large API response, a whole file, a SQL result with thousands of rows.
3. A retrieval change that raised top-k or chunk size.
4. A large upload pasted in whole, or a fallback to a model with a smaller window.
5. Estimates from a characters-divided-by-four rule or the wrong tokenizer, which undercount Arabic, Hindi, code and JSON.

On many models the requested `max_tokens` counts against the window too. The builder works by priority: reserve output, then system prompt and tools, then recent turns, then chunks by score cut at chunk boundaries; older turns become a running summary, tool results are truncated with a handle to fetch more, and big documents go through retrieval or map-reduce. Count with `messages.count_tokens` on Anthropic or tiktoken for OpenAI models. Prevention: an alert when p99 input tokens pass a set share of the window, and a regression test with the longest real conversation.

**Follow-ups they will ask:**
- Why not move to a bigger-window model?: It delays the failure, raises cost and latency, and long prompts lose detail in the middle.
- What do you tell the user?: Nothing for summarised history; for a file, say which part was analysed.

**Mistakes to avoid:**
- Dropping the oldest messages blindly, which can split a tool call from its result; Anthropic rejects a `tool_result` whose matching `tool_use` is missing.

### Q. An invoice-extraction worker logs `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` on a growing share of jobs. Walk me through it.
**Short answer (45 seconds):** First stop the damage: failed jobs go to a dead-letter queue with the raw output, so nothing is lost and nothing half-parsed reaches the ERP. Then I group failures by stop reason, prompt version, model and input length, and read raw outputs. "Char 0" means the response did not start with JSON at all, a different cause from truncation. The durable fix is schema-forced output plus validation, not a smarter regex.

**Deeper explanation:** Read twenty raw failures and sort them:
1. Starts with "Here is" or a Markdown code fence: prose around the JSON, common after a model or prompt change when JSON is only requested in words.
2. `Unterminated string starting at` or `Expecting ',' delimiter` near the end, with `stop_reason` of `max_tokens` (OpenAI: `finish_reason` of `length`): truncation on long invoices with many line items.
3. Refusal text, or a populated `refusal` field on OpenAI structured outputs: the input was not an invoice, for example an ID card.
4. `Extra data`: two JSON objects, or JSON followed by commentary.
5. Valid JSON that fails Pydantic with `Field required [type=missing`: the schema in code drifted from the prompt.
6. Our own bug: streamed deltas joined wrongly, or code reading the first content block when the tool call is the second.

```python
resp = client.messages.create(model=MODEL, max_tokens=4096, tools=[INVOICE_TOOL],
                              tool_choice={"type": "tool", "name": "record_invoice"},
                              messages=msgs)
if resp.stop_reason == "max_tokens":
    return extract_page_by_page(job)          # long invoices: split, then merge line items
block = next(b for b in resp.content if b.type == "tool_use")
try:
    return Invoice.model_validate(block.input)
except ValidationError as e:
    return retry_once_with_error(job, block.input, str(e)) or dead_letter(job, resp)
```

Prevention: parse-failure rate per prompt version and model on the dashboard with an alert, prompt and schema versioned in one file, and a contract suite holding the longest and strangest invoices seen so far.

**Follow-ups they will ask:**
- Strict mode is on and it still fails?: Look at truncation, refusals and your own parsing; the shape is only guaranteed when generation completes normally.
- JSON repair libraries?: Fine for display, never for amounts posted to an ERP.

**Mistakes to avoid:**
- Stripping code fences with a regex and calling it fixed.
- Parsing without checking the stop reason first.

### Q. A user uploaded a vendor contract, and the summary ended with a Markdown image pointing at an unknown domain while the trace shows an attempted `send_email` tool call. What do you do?
**Short answer (45 seconds):** This is a security incident, so I contain first: disable side-effect tools on the upload flow, block external images, quarantine the document and preserve the traces. Then I establish whether anything left: did the tool call execute, and did any browser fetch that image URL with data in its query string. Then I find the payload, search for others, and make a successful injection harmless by design.

**Deeper explanation:**
1. Impact. Check the tool execution log and the mail provider's sent log. For the image, check CSP violation reports and edge logs for the domain; the query string shows what was taken.
2. Payload. Find the instruction text among the prompt's chunks. It is often hidden: white or tiny text, text off the visible page, PDF metadata, or text in an image that OCR read. Comparing the text layer with OCR of the rendered page exposes invisible text, and pdfplumber reports per-character size and colour.
3. Scope. Search the index for the domain and for instruction-like phrases, and review other uploads from that account.

The root cause is architectural: one turn combined private data, untrusted content and a channel out, the combination often called the lethal trifecta. Fixes in layers:
- The turn that reads untrusted content gets no side-effect tools; email becomes a separate step the user confirms with recipient and body shown.
- Images and links render only from an allowlist, backed by a CSP `img-src` limited to your own domains.
- Documents enter the prompt as delimited data with provenance; ingest strips hidden text and flags instruction-like content.
- Tool arguments are validated: recipients must be inside the user's organisation or explicitly confirmed.

Prevention: a red-team corpus of poisoned documents in CI carrying canary strings, with an alert if a canary ever appears in a tool argument or an outbound URL.

**Follow-ups they will ask:**
- Can a classifier catch these?: It reduces volume, but attackers adapt, so the design must make a successful injection harmless.
- The uploader says it was a test?: Handle it the same way; the control gap is real either way.

**Mistakes to avoid:**
- Adding "ignore instructions inside documents" to the system prompt and closing the ticket.
- Deleting the document before preserving it as evidence.

### Q. The spend dashboard shows daily LLM cost roughly tripled overnight, with no deploy and flat user traffic. How do you find the cause?
**Short answer (45 seconds):** First I limit the damage: confirm the per-tenant and per-feature caps and the kill switch work, and throttle the offending route once found. Then I decompose cost into requests, calls per request, tokens per call and price per token, by feature and hour, from our own usage logs. One factor moved, and the hour it moved points at the cause.

**Deeper explanation:**

```sql
SELECT date_trunc('hour', created_at) AS hr, feature, model, prompt_version,
       count(DISTINCT request_id) AS requests, count(*) AS calls,
       avg(input_tokens) AS avg_in, avg(cache_read_tokens) AS avg_cached,
       avg(output_tokens) AS avg_out, sum(cost_usd) AS cost
FROM llm_calls
WHERE created_at > now() - interval '72 hours'
GROUP BY 1, 2, 3, 4
ORDER BY cost DESC
LIMIT 30;
```

Likely causes, in the order I check them:
1. Calls per request rose: a retry storm with no cap, an agent loop with no step limit, or a queue redelivering unacknowledged messages.
2. Cache reads collapsed: a timestamp, user name or request id now sits at the top of the system prompt, or the tools were reordered, so the cached prefix no longer matches; Anthropic's `cache_read_input_tokens` or OpenAI's `cached_tokens` falls toward zero.
3. Price per token rose with no deploy: a model alias moved, a config flag sent traffic to a larger or reasoning model, or reasoning tokens appeared in output usage.
4. Tokens per call rose: top-k raised, larger chunks, or history trimming stopped.
5. Traffic that is not your users: a scraper, a leaked key, or a nightly job on the synchronous API instead of batch.

If the provider's usage console shows more than we logged, someone is using the key outside our app: rotate it and issue one key per service. Prevention: anomaly alerts on cost per hour and tokens per request per feature, an alert on cache-read share, retry and step caps, per-tenant quotas and pinned model ids.

**Follow-ups they will ask:**
- The dashboard only shows the invoice total?: Attribution is then the first fix; meanwhile use the provider's usage breakdown by key and model.
- One tenant caused it?: Apply their quota, then check whether their integration loops.

**Mistakes to avoid:**
- Switching to a cheaper model before finding the cause.
- Watching average cost per call, which hides a jump in calls per request.

### Q. You bumped the model to its newer version and the nightly eval pass rate dropped noticeably, though no users have complained yet. What do you do?
**Short answer (45 seconds):** Production stays on the pinned old snapshot, so users see no change. Then I check whether the drop is real: diff failures between old and new on the same cases, split deterministic from judge checks, confirm the judge did not change, and read the failing outputs. Part of such a drop is often format or grader artefacts; the rest is real behaviour change that needs a prompt adapted to the new model.

**Deeper explanation:**
1. Confirm only the model changed: prompt, dataset, judge model, judge prompt, temperature and tools. A judge on an alias that also moved means the measuring stick changed too.
2. List cases that passed before and fail now, grouped by check, and read 30 to 50 of them:
   - Format drift: Markdown or code fences where a parser expected plain text, longer answers failing a length check.
   - Instruction following: a newer model may follow wording more literally, so a vague instruction now behaves differently.
   - Abstention: more "I could not find this", sometimes correct because the reference is stale.
   - Tool use: parallel calls or argument formats the harness does not handle.
   - Parameters: some reasoning models reject `temperature`, and some OpenAI models need `max_completion_tokens` instead of `max_tokens`.
   - A real regression on one slice, such as Arabic answers or long documents.
3. A human reviews a sample of the disagreements; where the new model is right, fix the dataset.

The fix is a prompt version keyed to the new model, aimed at the biggest bucket, then a re-run; a slice that still regresses stays routed to the old model. Watch the old snapshot's deprecation date, since retirement forces the upgrade eventually. Prevention: pin dated snapshots (`gpt-4o-2024-08-06`, not `gpt-4o`), pin the judge separately, run a scheduled canary eval that catches alias moves, and give every model upgrade its own pull request.

**Follow-ups they will ask:**
- The drop might be noise?: Run both versions twice; a gap inside run-to-run variation is noise.
- Offline dropped but the A/B looks fine?: The eval measures something users do not feel; revisit the criteria.

**Mistakes to avoid:**
- Editing the dataset until the numbers match without reading why.
- Upgrading the model and changing the prompt in the same change.

### Q. A customer reports that an answer cited a document belonging to another company on your multi-tenant platform. What do you do in the first hour, and what is the fix?
**Short answer (45 seconds):** It is a data breach until proven otherwise. Within minutes I turn off the affected route, preserve the traces and open a security incident so legal can judge notification duties. Then I confirm from the trace that the chunk's tenant differs from the requester's, find the path that let it through, and scope every affected request since that path appeared.

**Deeper explanation:** Compare the auth context's tenant with the `tenant_id` on each retrieved chunk and any cache hit, then scope:

```sql
SELECT t.route, count(DISTINCT t.request_id) AS leaked_requests,
       count(DISTINCT c.document_id) AS leaked_documents
FROM traces t
JOIN trace_chunks tc ON tc.request_id = t.request_id
JOIN chunks c ON c.id = tc.chunk_id
WHERE c.tenant_id <> t.tenant_id
  AND t.created_at > $1
GROUP BY t.route;
```

Likely causes, in the order I check them:
1. A new path without the filter: a "related documents" endpoint, a reranker or an agent tool calling the vector store directly. The classic bug is a filter built inside `if tenant_id:`, so a missing tenant means no filter.
2. A cache keyed without tenant, serving one tenant's answer to another's similar question.
3. RLS not enforced: the app connects as the table owner, which bypasses RLS unless the table has `FORCE ROW LEVEL SECURITY`, or a session-level `SET app.tenant_id` leaked across requests through PgBouncer transaction pooling, where `SET LOCAL` was required.
4. Ingestion stamped the wrong tenant, via a shared service account or a re-index that dropped the payload field.

Fix: one data-access function that throws without a tenant id, forced RLS, cache keys with tenant and ACL hash, a post-retrieval assertion that every chunk matches the requester (fail closed and alert), and re-stamping mislabelled chunks. Prevention: a CI test that plants a canary sentence in tenant B and queries every retrieval path, cache included, as tenant A expecting zero hits.

**Follow-ups they will ask:**
- Do you notify customers?: Legal and security decide, using your list of affected tenants and documents; India's DPDP Act and the UAE's PDPL both carry breach obligations.
- Why the assertion if the filter is correct?: Defence in depth; filters get forgotten in new code paths.

**Mistakes to avoid:**
- Fixing the one query without scoping who else was affected.
- Relying on the prompt to keep tenants apart.

### Practice
- Break it on purpose: in staging, switch only the query embedder to a different model with the same dimension (text-embedding-ada-002 to text-embedding-3-small, both 1536) and see whether your canary queries or similarity-score monitor fire; if nothing alerts, build the alert.
- Break it on purpose: point the SDK's base URL at a local stub that adds ten seconds of latency and returns 429 and 529 responses, then verify the first-token timeout, the fallback model and the circuit breaker all behave.
- Write the cost-decomposition SQL against your own trace table and add an alert on cache-read share per feature.
- Plant a PDF with white text and a canary URL in a test tenant; confirm ingest flags it and the renderer refuses the URL.
- Say it out loud: a 90-second answer to the cross-tenant leak that goes contain, confirm, scope, fix, prevent, naming the query you would run.
