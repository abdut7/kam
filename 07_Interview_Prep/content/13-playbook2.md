## Behavioral & Ownership Scenarios [Core]

> Behavioral rounds at senior level check whether you can be trusted with ambiguity, people and production. Interviewers keep probing: "what exactly did you do?", "what happened next?", "what would you do differently?". A weak answer is a vague "we handled it", a story with no result, or a tale where someone else was the problem. A strong answer is one specific situation, your own actions in the first person, an observable result, and a lesson that changed how you work.

### In plain words
A behavioral question is the interviewer asking for a short film of you at work. They do not want your opinion of good teamwork; they want one real day when something got hard, and what you did with your own hands. It is like a doctor saying "show me where it hurts" instead of "how do you feel in general". Prepare six to eight true stories, each about two minutes long, and reuse them across questions. The scenarios below give you the shape of a strong answer; fill the brackets with your own real details.

### Concepts you must understand
- STAR plus lesson: Situation (one or two sentences of context), Task (what you owned), Action (what you did, the longest part), Result (what changed, with a number or a concrete outcome), Lesson (what you do differently now).
- Speak in the first person for your own actions: "I proposed", "I wrote", "I called". Use "we" only for real team outcomes, and say what your part was.
- Scope of impact makes a story senior: how many users, services, teams or how much money were affected, and whether your fix changed one bug or the way the team works.
- Senior answers show judgment: what you considered, what you chose not to do and why, and who you brought in.
- The result does not have to be a win; a failure with a real lesson and a system-level change often lands better than a perfect success.
- Common traps: blaming a colleague, manager or client; a vague "we" that hides your role; a long setup with no action; hero stories about working all weekend instead of fixing the cause; invented numbers.
- Keep it to about two minutes, then stop; the follow-ups are where interviewers test whether the story is real.
- Tag each story with several themes (conflict, failure, ownership, influence, deadline, quality) so a small set of true stories covers most questions.

### Q. You strongly disagree with a senior engineer's design. What do you do?
**Short answer (45 seconds):** First I make sure I understand their design and the constraints behind it, by asking questions and restating it back. Then I compare both options against the same criteria, with evidence where I can get it, and discuss it with them privately before any group review. If we still disagree, the decision goes to a design review or the tech lead, and once it is made I commit fully and record the risk I raised.

**Deeper explanation:**

1. Understand first: "Help me understand why you chose a shared database over an API between these two services." Senior engineers often know a constraint you do not: a deadline, a cost limit, a past incident.
2. Agree on criteria before arguing options: latency, cost, operability, delivery time, reversibility. Most design disagreements are really about which criterion matters most.
3. Bring evidence, not adjectives: a one-page comparison, a small spike, a load test, or a concrete failure scenario ("if service B changes its schema, service A breaks at runtime").
4. Talk 1:1 first. Nobody changes their mind well in a public pull request thread.
5. Escalate cleanly if needed: a short decision record with both options described fairly, so the decision owner judges the trade-offs, not who argued louder.
6. Disagree and commit: build the chosen design well, and add the monitoring or the revisit trigger that would show early if your concern comes true.

For your own story, fill in: the design [your example], your concern [the specific risk], the evidence you brought [spike, numbers, incident], the outcome [adopted, compromise or overruled] and what happened later.

**Follow-ups they will ask:**
- What if they pull rank and refuse to discuss it? : I put the trade-off in writing to the decision owner once, calmly, and then commit.
- What if you turned out to be wrong? : Say so plainly and name the constraint you had missed.
- What if the failure you predicted happens later? : Fix it first, then update the decision record; no "I told you so".

**Mistakes to avoid:**
- Arguing in a public thread or meeting before talking to the person.
- Framing it as right versus wrong instead of trade-offs, or quietly resisting after the decision is made.

### Q. You will miss a committed deadline by two weeks. How do you handle it?
**Short answer (45 seconds):** I raise it the day I know, not the day before the deadline. I go to the stakeholder with facts: what is done, what is left, why the estimate was wrong, and two or three options such as cutting scope, phasing the release or moving the date, with my recommendation. Then I re-plan with smaller milestones and more frequent updates so there is no second surprise.

**Deeper explanation:**

1. Confirm the slip: re-estimate the remaining work with the team, separating known work from unknowns.
2. Find the cause honestly: underestimated integration, a dependency team running late, scope added mid-sprint, or my own estimate. Name it without blaming anyone.
3. Prepare options, each with its cost:
   - Cut scope: ship the core flow on the date and the rest two weeks later.
   - Phase it: release to internal users or one pilot customer first.
   - Add people: only if the work splits cleanly; newcomers slow a late project at first.
   - Move the date: when the scope truly cannot change.
4. Tell the stakeholder early, on a call, then confirm in writing: "We will not hit the original date. Here is why, here are the options, I recommend option A."
5. Re-plan with checkpoints once or twice a week, demoable increments and a visible risk list.
6. Fix the process: spikes for big unknowns, an integration buffer, and a halfway risk review.

For your story, fill in: the project [your example], when you noticed [how far in], the real cause, the option chosen and the result [what shipped, when].

**Follow-ups they will ask:**
- What if the date is fixed, like a sale event or a contract? : Then scope is the variable; agree on the minimum that must work and protect it with feature flags.
- What if it was your fault? : Say so, explain how you changed the way you estimate, and move to the plan.
- Why not just work weekends? : A short push is fine once; as a plan it hides the problem and burns out the team.

**Mistakes to avoid:**
- Staying silent and hoping to catch up, then announcing the slip at the deadline.
- Arriving with only bad news and no options or recommendation.

### Q. You inherit an untested legacy service that pages the team every week.
**Short answer (45 seconds):** I start with data, not a rewrite. I pull the last two or three months of pages, group them by cause, and fix the noisy alerts and the top recurring causes first. In parallel I add observability and characterization tests around the code I touch, so each change makes the service safer, not riskier.

**Deeper explanation:**

1. Contain: a short runbook for each known page, so whoever is on call can act in minutes.
2. Classify: export incidents from PagerDuty or Opsgenie and group them by alert and root cause. A few causes usually produce most pages, such as a disk filling with logs or a downstream timeout with no retry.
3. Fix alerting: page only on user-facing symptoms (error rate, latency, a stuck queue); send the rest to tickets, and delete alerts nobody acts on.
4. Fix the top causes in order of frequency times impact, each with a test that would have caught it.
5. Build a safety net before refactoring: characterization tests that pin today's behaviour using real inputs and outputs, plus structured logs, request IDs and basic metrics.
6. Change it gradually with the strangler fig pattern: route one endpoint at a time to new code behind a feature flag, instead of a big-bang rewrite.
7. Make the cost visible: pages per week, hours lost and the trend, so reliability time is easy to justify.

For your story, fill in: the service [your example], pages per week before and after [real numbers], and the top causes you fixed.

**Follow-ups they will ask:**
- When would you rewrite instead? : When the stack is unsupported or every change breaks something, and even then piece by piece behind the same interface.
- The original author left and there are no docs. Now what? : Learn the real behaviour from logs and traffic, and write the docs as you go.
- How do you get time from management? : Show pages per week and hours lost, and ask for a fixed slice of each sprint for reliability.

**Mistakes to avoid:**
- Proposing a full rewrite in week one, before you know what the service actually does.
- Refactoring without tests, or muting alerts without fixing their cause.

### Q. A junior engineer's pull request is poor and they are defensive about review comments.
**Short answer (45 seconds):** I move the conversation out of the comment thread into a short call, and start by understanding how they approached the task. I separate blocking issues (correctness, security, data loss) from preferences, and explain the reason behind each blocking one. Then I offer to pair on the hardest part and agree on how to split the work so the next pull request is smaller.

**Deeper explanation:**

1. Check my own review first: forty unprioritized comments feel like an attack. Label them "blocking:", "suggestion:" or "nit:", and push style to the linter and formatter (ESLint, Prettier, Ruff) so people stop arguing about it.
2. Talk 1:1: "Walk me through how you approached this." Often the requirement was unclear, they were under time pressure, or nobody showed them the pattern the codebase uses.
3. Explain the why for each blocking issue with a concrete failure: "This query runs inside the loop, so an order with 500 items makes 500 database calls." A failing test or a quick benchmark persuades better than an opinion.
4. Acknowledge what is good and where they are right; defensiveness drops quickly when someone feels heard.
5. Pair on the fix for the hardest issue instead of rewriting it for them.
6. Prevent the next one: a short design note or a draft PR early for bigger tasks, smaller PRs, and a written team review guide so the standard is not personal.
7. If the pattern continues across several reviews, raise it with their lead as a growth topic, with examples, not as a complaint.

**Follow-ups they will ask:**
- What if it must merge today? : Merge only once the blocking issues are fixed; log the rest as a follow-up ticket with an owner.
- What if they push back and they are right? : Say so in the thread; it buys trust for the points that matter.
- What if the defensiveness is about you, not the code? : Ask directly how the reviews feel to them and adjust your tone while keeping the bar.

**Mistakes to avoid:**
- Rewriting their code yourself, or approving a weak PR to avoid conflict.
- Feedback about the person ("you always...") instead of about the code.

### Q. Product wants a feature shipped this week that you believe is unsafe.
**Short answer (45 seconds):** I make "unsafe" concrete first: what can go wrong, for whom, how likely and how bad. Then I go to the product owner with options rather than a flat no: ship behind a feature flag to a small group, add a human approval step, or ship a smaller safe version this week. If they still want the risky version, I escalate in writing to the decision owner, and for a hard red line such as leaking customer data, I do not ship it.

**Deeper explanation:**

1. Name the risk precisely. "Unsafe" means little to product; "the agent can send a cost estimate to the client with nobody reviewing it, and a wrong number becomes a commercial commitment" is something they can weigh. In a system like CADBEATER, that is exactly why estimates sit behind human approval gates.
2. Size it: who is affected, the worst case, how you would detect it and how fast it could be undone.
3. Offer options with timelines:
   - Feature flag for internal users or one pilot customer.
   - Human in the loop: the AI drafts, a person approves.
   - Limits: rate limits, amount caps, read-only mode, an audit log.
4. Agree on who decides. Product owns priority; engineering owns stating the risk clearly. Record the decision and the accepted risk in the ticket.
5. Escalate to the engineering lead or security team for security, privacy, legal or money-loss risks; one product manager should not accept those alone.
6. If it ships with accepted risk, add monitoring and a kill switch that turns it off in minutes.

**Follow-ups they will ask:**
- What if the CEO overrides you? : Then the right person has accepted the risk; I make sure it is written down and the kill switch exists.
- How do you avoid being the engineer who always says no? : Always arrive with a version you can ship this week.
- What is a hard red line for you? : Exposing another customer's data, breaking compliance, or moving money without controls.

**Mistakes to avoid:**
- Saying "it's unsafe" without a concrete scenario, or shipping it silently and hoping.
- Quietly stalling instead of disagreeing openly.

### Q. Tell me about a production mistake you made and what you changed afterwards.
**Short answer (45 seconds):** Pick a real mistake with real but contained impact, and own it in the first sentence: "I shipped a change that did X." Spend a little time on detection and recovery, and most of the answer on what you changed so that whole class of mistake cannot happen again. Close with the lesson in one line.

**Deeper explanation:** Use this skeleton and fill every bracket with true details:

```text
Situation: I was working on [system] at [company], responsible for [part].
Mistake:   I [the change: migration, config, deploy, prompt change]
           without [the check I skipped].
Detection: [alert or user report] after [time to detect].
Impact:    [who was affected, how many, for how long], real numbers only.
Recovery:  I [rolled back / hotfixed / restored] and told [people].
Cause:     [root cause, asking "why" until you reach a process gap].
Changes:   [test added], [guardrail or automation], [runbook or checklist].
Lesson:    I now [a habit you still follow].
```

Stories that work well, if true for you: a migration that locked a busy table, a config change that disabled a cache, a prompt change that broke structured output downstream.

What interviewers listen for:
- Ownership: "I" for the mistake, not "the deployment failed".
- Calm recovery: roll back first, root cause after.
- A blameless root cause that ends at a process or system gap, not "I was careless".
- System-level changes: a CI check, a migration linter, a canary step, an alert, not only "I am more careful now".

Keep the impact honest; exaggerated stories fall apart under follow-ups.

**Follow-ups they will ask:**
- How did you tell your manager or the client? : Quickly, with the impact and the recovery plan, before they heard it elsewhere.
- Why did review or tests not catch it? : Name the gap and the check you added for it.
- Has it happened again? : Say what evidence shows it has not, or what you changed when it did.

**Mistakes to avoid:**
- A fake mistake ("I care too much") or one that was really someone else's fault.
- Ending with "I learned to be careful" instead of a concrete change.

### Q. You introduced AI coding tools (Claude Code, agent skills) to a team. How did you drive adoption and keep quality up?
**Short answer (45 seconds):** I treated it like any engineering change: start from a real pain point, put the shared context in the repository, show results on real tickets, and keep the quality bar exactly where it was. In practice that meant agentic coding with Claude Code, custom agent skills for each project module plus shared project-level skills, and AI-assisted review as a first pass, never a replacement for the human reviewer who owns the merge.

**Deeper explanation:**

1. Start from a problem: [your pain point, for example slow boilerplate for new endpoints, inconsistent tests, slow onboarding to a module].
2. Put the context in the repository: a project instructions file (CLAUDE.md) with architecture rules, build and test commands and what the agent must never do; then skills, small folders with a SKILL.md, encoding how each module adds an endpoint, writes a migration or writes tests.
3. Drive adoption with results, not mandates: early volunteers, live demos on real tickets, pairing sessions. Skills are code, so they get reviewed like code.
4. Keep the gates unchanged: CI runs lint, type checks and tests on every PR; PRs stay small; the author must be able to explain every line; tests must check behaviour, not mirror the implementation.
5. AI review goes first, catching missing error handling and tests, so the human reviewer focuses on design and correctness.
6. Guard security: no secrets or customer data in prompts, restricted tool permissions, and extra human review on anything touching auth or payments.
7. Measure before and after: [your metrics, for example PR cycle time, review rework, escaped defects].

**Follow-ups they will ask:**
- What about a skeptical senior engineer? : Let them pick the task and judge the output; their skepticism makes good guardrails.
- What failure modes did you see? : [your examples]; typically calls to APIs that do not exist, oversized diffs, or tests that pass for the wrong reason.
- How do juniors still learn? : They explain the generated code in review and write the tricky parts themselves.

**Mistakes to avoid:**
- Quoting productivity numbers you never measured.
- Talking only about the tool and not about the review, testing and security process around it.

### Practice
- Build a story bank: eight true stories in STAR plus lesson form, one line each for situation, action, result and lesson, tagged with themes (conflict, failure, deadline, ownership, influence, quality). Fill the brackets above with real numbers only.
- Record yourself answering three of the questions in this section, two minutes each. Count how often you say "we" for your own actions and check that each answer ends with a concrete result.
- For your production-mistake story and your AI-tools story, write the five follow-ups you would ask if you were the interviewer, and your answers.
- Say it out loud: "Tell me about a time you disagreed with a senior engineer", in under two minutes, ending with what you would do differently now.

## Trade-off & Decision Scenarios [Core]

> Trade-off questions have no single right answer, and interviewers know it. What they score is the reasoning: did you ask about constraints, compare real options against stated criteria, use evidence, make a call and say how you would undo it if wrong. A weak answer is "it depends" followed by nothing, or a favourite technology defended on taste. A strong answer is "given these constraints I would choose X, this is what it costs, and this is the signal that would make me switch".

### In plain words
Choosing a technology is like choosing between renting and buying a home. Neither is always right: it depends on how long you will stay, how much money you have now and how sure you are about the future. A good decision names those factors out loud, picks one, and notes what would make you move. Some choices are cheap to undo, like a rented flat; others, like a bought house, are expensive to reverse, so they deserve more care.

### Concepts you must understand
- Decision template: context and constraints, options (including "do nothing" and the boring choice), criteria in priority order, evidence, the decision, its cost, and how to reverse it.
- Ask about constraints before choosing: team size and skills, timeline, budget, traffic, data sensitivity, compliance, and how long the system must live.
- One-way doors are decisions that are expensive or impossible to reverse (the primary database, the data model, a public API contract), so slow down and gather evidence. Two-way doors are cheap to reverse (a library, a model provider behind an interface), so decide fast and move on.
- Evidence beats opinion: a one-day spike, a load test, a cost spreadsheet, an eval set, or an incident from a similar system.
- Reversibility can be designed in: an interface or adapter, an OpenAI-compatible endpoint, OpenTelemetry instead of a vendor SDK, a feature flag.
- Team capability is a real criterion: the technology your team can operate at 3 a.m. often beats the theoretically better one.
- Write the decision down as a short decision record (ADR): context, options, decision, consequences, and the trigger to revisit it.
- "It depends" is only half an answer; finish it with "on X, and here X points to Y".

### Q. A seed-stage startup asks you to choose between a monolith and microservices.
**Short answer (45 seconds):** I would almost always pick a modular monolith: one deployable and one database, with clear module boundaries enforced in code. At seed stage the biggest risk is building the wrong product, not scale, and microservices add network calls, distributed debugging and deployment work a small team cannot afford. I would split something out only for a concrete reason, such as a very different scaling or runtime profile.

**Deeper explanation:**

1. Clarify: team size, expected traffic over the next 12 to 18 months, any part with unusual needs (GPU inference, long-running jobs), compliance boundaries.
2. Options: a plain monolith, a modular monolith, microservices.
3. Criteria at seed stage: speed of change, cost to operate, ease of debugging, ability to split later.
4. Decision: a modular monolith in one repository. Modules such as `billing`, `projects` and `ai` talk through internal interfaces, each owns its own tables (a separate Postgres schema per module), and a lint rule blocks cross-module imports.
5. Exceptions from day one: work with a different runtime profile runs separately anyway. An AI product usually has a GPU inference server or a queue-driven worker for long agent runs. That is a deployment split for a technical reason, not microservices for their own sake.
6. Reversal plan: because modules already have interfaces and own their data, extracting one later is a contained project. Triggers to split: teams blocking each other's deploys, one module needing independent scaling, or a different reliability requirement.

Contrast it with a context where microservices pay off: a large eCommerce platform such as Samsung.com, where independent services autoscale for sale events and deploy separately, which justifies the operational cost.

**Follow-ups they will ask:**
- The founders say investors expect microservices. Now what? : Explain the cost in delivery speed; investors care about shipping and traction.
- How do you stop the monolith becoming a big ball of mud? : Module boundaries checked in CI and no tables shared across modules.
- What would you extract first? : The part with a different scaling or runtime need, usually the AI worker.

**Mistakes to avoid:**
- Picking microservices because large companies use them.
- Saying "monolith" without explaining how you keep it splittable.

### Q. You must choose Node.js or Python for a new AI backend.
**Short answer (45 seconds):** I decide on the workload and the team, not on language preference. If the service mostly orchestrates LLM API calls, streams tokens and talks to a database, both work and the team's existing language wins. If it needs local models, embeddings, document parsing, evaluation or data work, Python wins on ecosystem. A common answer is Python FastAPI for the AI service and Node.js or TypeScript for the product API, with a clear contract between them.

**Deeper explanation:**

1. Clarify what "AI backend" means: only calling hosted LLMs, or also running models, parsing PDFs or CAD files, training or evaluating.
2. Compare on criteria:

| Criterion | Node.js and TypeScript | Python |
|---|---|---|
| LLM SDKs and agent frameworks | Good: official SDKs, LangGraph.js, Vercel AI SDK | Broadest: official SDKs, LangGraph, LlamaIndex |
| ML, data and evals | Thin | Strongest: PyTorch, Hugging Face, pandas, eval tooling |
| Concurrent I/O and streaming | Excellent by default | Good with async FastAPI; blocking calls in async code are a classic bug |
| Types shared with a React frontend | Direct with TypeScript | Generated clients from the OpenAPI schema |

3. Decision rule: one language for a small team doing only API orchestration; a split when real ML or data work is involved. In a system like CADBEATER, the agents, RAG and the self-hosted vision-language model sit in Python FastAPI services, and the React frontend consumes them over SSE.
4. Keep it reversible: HTTP or queue contracts (an OpenAPI schema, JSON events) let either side be rewritten alone.
5. If unsure, spike the riskiest path (streaming an agent run with tool calls) in a day.

**Follow-ups they will ask:**
- Two languages means two toolchains. Worth it? : Only when the Python ecosystem is really used; otherwise keep one.
- How do you share types across the boundary? : Generate TypeScript types from the FastAPI OpenAPI schema in CI.
- What about raw performance? : Most time is spent waiting on the model, so language speed rarely decides it.

**Mistakes to avoid:**
- Choosing on taste ("Python is the AI language") without looking at the workload.
- Splitting a tiny team across two languages when it only calls one API.

### Q. RAG, fine-tuning or a bigger model: a client wants better answers next month.
**Short answer (45 seconds):** I would not pick a technique before knowing why the answers are bad. First I build a small eval set from real questions and sort the failures by cause: missing knowledge, wrong format or style, or weak reasoning. Then I try the cheapest fix first: prompt and model changes in hours, retrieval fixes in days, fine-tuning only if the data and the month allow it.

**Deeper explanation:**

1. Clarify "better": more accurate, complete, cited, consistent in format, faster or cheaper? Get 5 to 10 real bad answers.
2. Build the eval set: 50 to 200 real questions with expected answers or rubrics, scored by code where possible and by an LLM judge that a human spot-checks, tracked in Langfuse or similar.
3. Sort the failures by cause:

| Failure | Likely fix |
|---|---|
| Fact missing, outdated or private | RAG, or fix existing retrieval: chunking, hybrid search, reranking, metadata filters |
| Right facts, wrong format or tone | Better prompt and examples, structured outputs, then fine-tuning |
| Wrong reasoning on multi-step questions | A stronger or reasoning model, routed only to the hard questions |
| A narrow task at high volume | Fine-tune a smaller model to cut cost and latency |

4. Plan the month: week 1, eval set and baseline; week 2, prompt, model and retrieval experiments; weeks 3 and 4, harden the winner and check it on shadow or A/B traffic. Fine-tuning fits only if labelled examples already exist.
5. Report baseline versus new eval scores, plus cost and latency per request.

Knowledge that changes often belongs in retrieval, not in model weights; fine-tuning teaches behaviour and format far more reliably than facts.

**Follow-ups they will ask:**
- The client insists on fine-tuning. Now what? : Run it as one arm of the eval and let the scores decide.
- The bigger model fixes it but costs much more? : Route only the questions that need it.
- How do you know the eval set is representative? : Sample it from production logs and keep adding new failures.

**Mistakes to avoid:**
- Fine-tuning to add facts that change every week.
- Changing three things at once with no baseline, so nobody knows what helped.

### Q. Self-host an open model or pay an API, for a product with uncertain traffic.
**Short answer (45 seconds):** With uncertain traffic I start on a hosted API: no idle cost, no GPU operations, and strong models from day one. I move to self-hosting when there is a clear trigger: steady volume that keeps GPUs busy, data that cannot leave our environment, a fine-tuned model the API cannot serve, or latency control the API cannot give. I keep the switch cheap by calling every model through one OpenAI-compatible interface.

**Deeper explanation:**

1. Clarify: requests and tokens per day, peak versus average, data residency or privacy rules, required quality, latency target, and who would operate the GPUs.
2. Do the break-even math with current prices you look up, not remembered ones (see the formula below). "Uncertain" is the key word: a GPU paid for around the clock but mostly idle is usually more expensive per token than an API.
3. Consider the middle options: serverless GPU platforms that scale to zero (cold starts for large models can be slow), or a hybrid where a small fine-tuned model on vLLM serves one narrow, high-volume task while harder tasks go to the API.
4. Make it a two-way door: vLLM exposes an OpenAI-compatible server, so if the app calls models through one client interface or a router such as LiteLLM or OpenRouter, switching is configuration plus an eval run.
5. Measure per model: cost per request, p95 latency, error and rate-limit rate, and eval quality.

```text
API per month       = tokens per month x price per token
Self-host per month = GPU hourly price x hours running x replicas
                      + engineering and on-call time
Self-host wins only when its total is lower AND utilization
stays high enough to justify always-on replicas.
```

**Follow-ups they will ask:**
- The data is sensitive. Does that force self-hosting? : Not always; check the provider's retention terms and regional or private deployment options first.
- Traffic grows tenfold. What changes? : Re-run the break-even with real numbers; steady high volume is where self-hosting starts to pay.
- What does self-hosting cost besides GPUs? : Model upgrades, monitoring, capacity planning and an on-call rotation.

**Mistakes to avoid:**
- Self-hosting on day one "to save money" without utilization numbers.
- Calling one provider's SDK directly from all over the codebase.

### Q. PostgreSQL or MongoDB for a new product with changing requirements.
**Short answer (45 seconds):** "Changing requirements" alone does not mean MongoDB. My default is PostgreSQL with JSONB columns for the parts whose shape is still moving: you get relations, constraints, transactions and SQL reporting, plus document flexibility where you need it. I would choose MongoDB when the data is truly document-shaped: self-contained aggregates read and written as a whole, very different shapes per tenant, and few cross-entity queries.

**Deeper explanation:**

1. Clarify the data: list the main entities and the top ten queries. Users, orders, invoices and permissions are relational; a catalogue with different attributes per category is document-shaped.
2. Compare:

| Criterion | PostgreSQL | MongoDB |
|---|---|---|
| Changing fields | JSONB columns; migrations are cheap early on | No fixed schema; optional `$jsonSchema` validation |
| Relations and integrity | Foreign keys, joins, constraints | References in app code; `$lookup` exists but is costlier |
| Transactions | Mature, multi-row | Multi-document transactions exist, but you model to avoid them |
| Reporting and ad-hoc queries | SQL, window functions | Aggregation pipeline |
| Horizontal scale | Read replicas, partitioning, extensions | Native sharding |

3. Decide: for a typical SaaS product, Postgres with JSONB for flexible attributes and a GIN index on the JSON fields you filter by; pgvector can cover small-scale vector search without a second database.
4. Treat it as a one-way door: moving a primary database later means dual writes, backfills and weeks of risk, so it deserves a spike with the real query shapes.
5. Keep data access behind repositories, which helps testing and limits the blast radius of any later move.

**Follow-ups they will ask:**
- The team only knows MongoDB. Does that change it? : Yes, team skill is a real criterion; then model documents carefully and add schema validation.
- A JSONB field becomes central. Now what? : Promote it to a real column with a migration and index it.
- When is MongoDB clearly better? : Document-shaped aggregates at high write volume where native sharding matters.

**Mistakes to avoid:**
- Choosing MongoDB because "we don't know the schema yet" when the data is plainly relational.
- Ignoring the reporting needs that arrive a few months in.

### Q. Build or buy: an internal team wants to build its own vector database or observability stack.
**Short answer (45 seconds):** I ask what problem the existing options fail to solve, because core infrastructure is a commitment for years, not a project. Unless it differentiates our product, I would adopt a proven option: managed or self-hosted open source such as Qdrant or pgvector for vectors, and OpenTelemetry with Prometheus, Grafana and Langfuse or a vendor for observability. If the team still wants to build, I time-box a spike with written success criteria.

**Deeper explanation:**

1. Clarify the real requirement behind "build our own": cost at our scale, data residency, a missing feature, or engineers wanting interesting work.
2. Options: buy a managed service, self-host open source, extend open source, build from scratch.
3. Criteria: total cost of ownership (engineer months to build, then years of maintenance, upgrades, on-call and security patches), time to value, fit at our scale, lock-in, and whether it differentiates the product.
4. Evidence: run our actual workload through two candidates. For vectors: recall at our top-k, p95 latency with metadata filters, memory at our vector count. For observability: ingest volume, query speed, retention cost.
5. Decide with a reversal path:
   - Vectors: a thin retrieval interface in our code, so moving between Qdrant, pgvector or a managed service is an adapter change plus a re-index.
   - Observability: instrument with OpenTelemetry, which is vendor-neutral, so changing the backend does not touch application code.
6. If building still wins, keep the scope narrow (the missing piece on top of an open-source core), set a time-box and an exit criterion, and staff its maintenance from the start.

A two-week spike that shows an open-source option meets the need can save months of building something the team then has to run forever.

**Follow-ups they will ask:**
- The managed bill keeps growing. Now what? : Consider self-hosting the same open-source engine before building anything new.
- What would justify building? : A capability core to the product that no option provides at acceptable cost.
- How do you handle a disappointed team? : Give them the hard integration and tuning work, which is real engineering.

**Mistakes to avoid:**
- Comparing licence cost only and ignoring years of maintenance.
- Starting to build before writing down what the existing tools fail at.

### Q. Speed or quality: the CEO wants a demo in four days for a big client.
**Short answer (45 seconds):** I say yes to the demo and negotiate what it must prove. I cut scope to one convincing end-to-end flow, build it in a separate demo environment with seeded data, and say clearly which parts are real and which are mocked. Every shortcut goes on a written list, so demo code never quietly becomes production code.

**Deeper explanation:**

1. Clarify in the first hour: who the audience is, what decision the demo should drive, which one or two moments must impress, and whether the client will touch it or only watch.
2. Scope one happy path end to end. Make it real where credibility depends on it (the AI output on the client's kind of document) and fake it where it does not (login, settings, billing).
3. Protect production: a separate demo environment or a feature flag, seeded data, and no shortcut merged into the main branch without review.
4. Make an AI demo predictable: pin the model version and prompt, lower the temperature, run the exact demo inputs many times, and cache known-good responses for the scripted path as a fallback.
5. Plan for failure: rehearse twice, keep a recorded video of the flow, and have a fallback if the network or the provider is slow.
6. Track the debt: every hard-code, mock and skipped test becomes a ticket with a hardening estimate, and the CEO sees that list before anyone promises the client a go-live date.

Say it plainly to the CEO: "This is what will be real on demo day, this is what will be shown but is not production-ready, and this is the extra time needed to make it real."

**Follow-ups they will ask:**
- The client wants to use it next week. Now what? : Show the hardening list and agree on a pilot date with limited users.
- What will you never cut, even for a demo? : Security of real client data and anything that touches production systems.
- How do you protect the team? : Cut scope first; extra hours are the last lever, not the plan.

**Mistakes to avoid:**
- Accepting the full scope and delivering a broken demo.
- Letting demo shortcuts slip into production without a hardening pass.

### Practice
- Write a one-page ADR for a real decision from your own projects [your example]: context, options, criteria, decision, consequences and the revisit trigger.
- Build an API-versus-self-host break-even sheet using current prices you look up yourself, at three traffic levels, and note the GPU utilization each level needs.
- Model one real feature's data both ways, as Postgres tables with JSONB and as MongoDB documents, and write its top five queries in SQL and in an aggregation pipeline.
- Say it out loud: "monolith or microservices for a seed startup" in 60 seconds, naming your criteria, your decision and the trigger that would make you split.

## Error Cases Across the Stack [Core]

> Error questions test whether you have actually run systems. Interviewers name a symptom and watch your first moves: do you check impact, work out which layer produced the error and read the exact message, or do you guess a fix? A weak answer jumps to "increase the timeout" or "restart it". A strong answer narrows the layer in two or three checks, ranks the likely causes, applies a fix that addresses the cause, and adds an alert, a test, a limit or a runbook entry so it does not come back.

### In plain words
An error message is a note left by whoever failed: the browser, the load balancer, your server, the database or the model provider. The first job is to work out who wrote the note, because the same symptom ("the upload failed") can come from any of them. Then read the note exactly, check the one thing most likely to be wrong, and only then change something. The table below is a cheat sheet of common notes, where to look first, and what usually fixes them.

### Concepts you must understand
- Find the layer first: compare what the client saw with what each hop logged (browser, CDN, load balancer, gateway, app, database, provider). The hop that logged the error, or the first hop that never saw the request, is where to dig.
- Read the exact error text and code: `ECONNRESET`, `ECONNREFUSED` and `ETIMEDOUT` are three different network failures, and a 502 from a load balancer is not a 500 from your app.
- Correlate with change: a deploy, a config change, a traffic peak, a scheduled job or a dependency's incident explains most new errors.
- Fix the cause, then add a guardrail: an alert on the symptom, a test that reproduces it, a limit, or a runbook entry.
- Retries fix only transient errors on idempotent operations; without backoff, jitter and a cap, retries turn a blip into an outage.

| Layer | Error or symptom | First check | Usual causes | Fix |
|---|---|---|---|---|
| Browser and React | Console says the request was blocked by "CORS policy", Postman works | Network tab: the preflight `OPTIONS` request, its status and `Access-Control-Allow-*` headers | Origin not allowlisted, `OPTIONS` hits auth and gets 401, wildcard origin with credentials, gateway error pages without CORS headers | Allowlist origins in one place, answer preflight before auth, or serve the API same-origin through a proxy |
| Browser and React | "Too many re-renders" or "Maximum update depth exceeded" | Which component sets state during render or in an effect | `setState` called in render, an effect that updates its own dependency, a new object or array as a dependency every render | Move updates into event handlers, fix the dependency array, memoize dependencies |
| Browser and React | `ChunkLoadError` or a failed dynamic import right after a deploy | Is an old `index.html` cached by the CDN or browser? | Old HTML points to chunk files the new deploy removed | `Cache-Control: no-cache` on `index.html`, long caching on hashed assets, keep the previous assets for a while |
| API gateway and HTTP | 502 Bad Gateway | Balancer or gateway logs and target health | App crashed or restarting, app closed a keep-alive connection the balancer reused, wrong target port | Fix the crash, keep the app's keep-alive timeout above the balancer's idle timeout, fix port and health check |
| API gateway and HTTP | 504 Gateway Timeout | Route latency versus the gateway timeout | Slow query, slow LLM call, a request waiting on a lock | Make long work asynchronous (job ID with polling, or SSE), fix the slow dependency, set timeouts deliberately at every hop |
| API gateway and HTTP | "413 Payload Too Large" (nginx shows "413 Request Entity Too Large") | Which hop answered: `Server` header, response body, which logs saw the request | nginx `client_max_body_size` (default 1m), ingress `proxy-body-size`, a gateway payload cap, `express.json()` limit (default 100kb) | Raise the limit at that hop, or upload straight to object storage with presigned URLs |
| Node.js | `ECONNRESET` or "socket hang up" | Does it happen on reused keep-alive sockets, or during deploys? | Server `keepAliveTimeout` (default 5 seconds) below the balancer idle timeout, pods stopped without graceful shutdown | Raise `keepAliveTimeout` above the balancer idle timeout, graceful shutdown, retry idempotent calls once |
| Node.js | `connect ECONNREFUSED 127.0.0.1:5432` | What does localhost mean from inside this container? | Localhost used instead of the service name, dependency not up yet, wrong port | Use the service DNS name, wait on readiness or health checks |
| Node.js | `ETIMEDOUT` on outbound calls | DNS result, security group or firewall, client pool usage | Packets silently dropped by a firewall, no NAT route, saturated connection pool | Fix network rules, set connect and request timeouts, add a circuit breaker |
| Node.js | All routes slow at once, one CPU core at 100 percent | Event loop delay (`perf_hooks.monitorEventLoopDelay`) and a CPU profile | Synchronous work: a huge `JSON.parse`, sync crypto or fs calls, a backtracking regex | Move CPU work to `worker_threads` or a queue, stream parsing, fix the regex |
| FastAPI | 422 Unprocessable Entity with a `detail` list | `detail[].loc` and `msg` in the response body | Client sends the wrong shape, JSON versus form data, a field sent in the query instead of the body | Fix the client or the Pydantic model, share the OpenAPI schema |
| FastAPI | Every request stalls while one endpoint is slow | A blocking call inside an `async def` route | `requests`, a sync database driver or `time.sleep` blocking the event loop | Use async clients (httpx, asyncpg), or declare the route with plain `def` so it runs in the threadpool |
| FastAPI | SQLAlchemy "QueuePool limit of size 5 overflow 10 reached" | Pool settings versus worker count versus Postgres `max_connections` | Sessions not closed, long transactions, slow queries holding connections | Close sessions in a `yield` dependency, shorten transactions, tune the pool, add PgBouncer |
| Databases | Postgres "deadlock detected" (SQLSTATE 40P01) | The log `DETAIL` lines naming both processes and statements | Rows locked in different orders, foreign-key locks, long transactions | Lock in a consistent order, keep transactions short, retry the whole transaction |
| Databases | Postgres "sorry, too many clients already" | Connection count in `pg_stat_activity` versus `max_connections` | Every pod and worker opening its own pool, leaked connections, serverless bursts | PgBouncer in transaction mode, smaller pools per process, fix the leak |
| Databases | A migration hangs, then every query on the table times out | `pg_stat_activity` wait events and `pg_locks` | `ALTER TABLE` waiting for an `ACCESS EXCLUSIVE` lock behind a long transaction, with all later queries queued behind it | `SET lock_timeout` in migrations, `CREATE INDEX CONCURRENTLY`, retry the migration later |
| Databases | MongoDB "E11000 duplicate key error" | Which unique index, which code path | Concurrent upserts, a retried insert without an idempotency key | Upsert on the unique key, treat a duplicate on retry as success |
| Caches | Redis "OOM command not allowed when used memory > 'maxmemory'" | `INFO memory` and `maxmemory-policy` | `noeviction` policy with keys that have no TTL | Set TTLs, `allkeys-lru` for pure caches, keep queues and caches in separate instances |
| Caches | Database load spikes each time a hot key expires | Cache hit ratio dips lined up with the TTL | Stampede: many requests rebuild the same key at once | Rebuild under a lock (`SET key value NX PX`), refresh early, add jitter to TTLs |
| Queues | Kafka consumer lag climbing, frequent rebalances | `kafka-consumer-groups.sh --describe --group` lag per partition, consumer logs | Processing slower than `max.poll.interval.ms`, more consumers than partitions, a poison message | Smaller batches, more partitions and consumers, a dead-letter topic |
| Queues | The same message processed twice | Ack or commit timing versus the side effect | At-least-once delivery: the consumer died after the side effect but before the ack | Idempotent handlers with a dedupe key, ack after the commit |
| Kubernetes and containers | `CrashLoopBackOff` | `kubectl logs --previous` and `kubectl describe pod` (exit code, events) | Missing env var or secret, failing startup migration, wrong command, liveness probe killing a slow start | Fix config, add a `startupProbe`, run migrations as a Job |
| Kubernetes and containers | `OOMKilled`, exit code 137 | `kubectl describe pod` last state, working set versus limit | Limit below real usage, memory outside the language heap, extra worker processes | Size limits from observed peaks, cap the heap, fewer workers, stream data |
| Kubernetes and containers | Pod `Pending` with "Insufficient cpu" or "Insufficient memory" | Scheduling events in `kubectl describe pod` | Requests larger than any node, no GPU nodes, untolerated taints | Lower requests, add a node pool, cluster autoscaler, tolerations |
| Cloud IAM and networking | AWS "is not authorized to perform" or a GCP 403 permission denied | Which identity is really calling (`aws sts get-caller-identity`) | Pod falls back to the node role (IRSA or Workload Identity not wired), missing action or resource, an explicit deny | Fix the identity binding, grant the least-privilege action on the exact resource |
| Cloud IAM and networking | A new service times out reaching the database | Security group or firewall rules, subnets, route tables | Missing ingress rule, different VPC, no route or NAT | Allow the service's security group, add peering or a private endpoint |
| LLM providers | "429 Too Many Requests" | Rate-limit response headers and `retry-after` | Requests or tokens per minute exhausted at peak, a batch job sharing the key | Shared token budget, backoff with jitter, queued batch work, separate keys, fallback model |
| LLM providers | Output cut off: finish reason `length` or stop reason `max_tokens` | The finish reason in the trace | `max_tokens` too low for the requested output | Raise the limit, ask for shorter output, split the task |
| LLM providers | "context length exceeded" | Prompt tokens plus requested output tokens | Growing history, huge tool outputs, too many retrieved chunks | Token budgets, trimming, summaries, capped tool outputs |
| LLM providers | Invalid JSON now and then | Raw output and finish reason | No structured outputs, truncation, Markdown fences around the JSON | Structured outputs or constrained decoding, schema validation, one repair retry |
| RAG | The answer ignores a document that clearly contains it | Retrieval trace: is the right chunk in the top-k at all? | Chunking split the answer, query and index embedded with different models, wrong metadata filter, stale index | Fix chunking, re-embed with one model, hybrid search plus a reranker, re-index on change |
| RAG | Users see another team's documents | Is a tenant or role filter applied on every vector query? | Filter applied only in the UI, or optional in code | A mandatory filter in the retrieval layer, tests for each role |
| Agents | The agent repeats the same tool call until LangGraph raises `GraphRecursionError` | Trace: repeated calls with identical arguments | Tool errors that do not tell the model what to change, no stop condition | Actionable tool errors, loop detection, iteration caps, hand back to the user |
| Inference servers | vLLM fails at startup with "CUDA out of memory" | `nvidia-smi`, `--max-model-len`, `--gpu-memory-utilization` | Weights plus KV cache too big for the GPU, another process on the GPU, context length set too high | Lower `--max-model-len`, quantize, tensor parallel across GPUs, free the GPU |
| Inference servers | Latency climbs with concurrency and requests queue | vLLM metrics: running versus waiting requests, KV cache usage | KV cache full, requests preempted, very long prompts | More replicas, cap `--max-num-seqs`, shorter prompts, prefix caching |

### Q. The browser console shows a CORS error, but the API works in Postman.
**Short answer (45 seconds):** The API answers, but the browser refuses to hand the response to the page: only browsers enforce CORS, and Postman and curl ignore it. I open the Network tab, find the failing request and its preflight `OPTIONS` request, and check the status and the `Access-Control-Allow-*` headers. Then I fix the policy in one place, the app or the gateway, with an explicit origin allowlist.

**Deeper explanation:**

1. Read the exact message. "No 'Access-Control-Allow-Origin' header is present on the requested resource" and "Response to preflight request doesn't pass access control check" lead to different fixes.
2. Check for a preflight. `Authorization`, a custom header or `Content-Type: application/json` triggers an `OPTIONS` request first. Classic failure: auth middleware runs before CORS and returns 401 to `OPTIONS`.
3. Reproduce it outside the browser:

```bash
curl -i -X OPTIONS https://api.example.com/orders \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type"
```

4. Rank the causes: the origin is missing from the allowlist (`www` versus the bare domain, a new preview URL); `*` used with cookies or `credentials: 'include'`, which browsers reject; a 502 or 500 error page from the gateway with no CORS headers, so a server error looks like CORS; a CDN caching one origin's header without `Vary: Origin`; gateway and app both adding the header.
5. Fix it once, before auth:

```js
import cors from 'cors';
const allowed = new Set(['https://app.example.com', 'http://localhost:5173']);
app.use(cors({
  origin: (origin, cb) => cb(null, !origin || allowed.has(origin)),
  credentials: true,
}));
```

6. Or avoid CORS entirely: serve the API same-origin through a reverse proxy or framework rewrites.
7. Prevent: keep the allowlist in per-environment config and run a browser-based end-to-end test in CI.

**Follow-ups they will ask:**
- Can you just use `*`? : Only for public APIs without credentials; with cookies you must return the specific origin.
- Is CORS protecting the API? : No, it protects users in the browser; the API still needs auth because curl ignores CORS.
- It fails only in production? : Diff the origins, gateway config and CDN caching between environments.

**Mistakes to avoid:**
- A browser extension that disables CORS, called a fix.
- Reflecting any `Origin` back with credentials enabled, which lets any site make authenticated calls.

### Q. Clients randomly get ECONNRESET from your Node.js service behind a load balancer.
**Short answer (45 seconds):** "Random" resets behind a load balancer are usually a keep-alive timeout mismatch or connections cut during deploys. I check whether the errors line up with deploys and scale-in events, and whether they hit reused idle connections. The usual fix is Node's `keepAliveTimeout` above the balancer's idle timeout, a graceful shutdown, and one retry for idempotent requests.

**Deeper explanation:**

1. Clarify scope: which clients, which routes, what percentage, and whether the balancer logs 502s at the same moments.
2. Correlate: overlay errors with deploy times, pod restarts (`kubectl get pods` restart counts) and autoscaler events. Bursts at deploys point to shutdown; a steady trickle points to keep-alive.
3. Keep-alive mismatch, the most common cause: Node's HTTP server closes idle keep-alive sockets after 5 seconds by default, while balancers keep idle connections much longer (AWS ALB defaults to 60 seconds). The balancer reuses a socket Node just closed, gets a reset and returns a 502. The same race happens between a client's agent and the balancer when the client keeps idle sockets longer than the balancer does.

```js
const server = app.listen(3000);
server.keepAliveTimeout = 65_000; // above the balancer idle timeout
server.headersTimeout = 66_000;   // keep above keepAliveTimeout
```

4. Unclean shutdown: on SIGTERM, fail readiness, stop accepting with `server.close()`, finish in-flight requests, then exit. In Kubernetes, a short `preStop` sleep lets the endpoint leave the balancer before the app stops.
5. Rule out the rest: process crashes (exit codes, OOMKilled), a blocked event loop, and an upstream such as the database resetting connections you pass through.
6. Client side: retry once on `ECONNRESET` for idempotent requests; Node's `req.reusedSocket` tells you the failure happened on a reused socket.
7. Prevent: alert on the balancer's 5xx count, and load test across a rolling deploy.

**Follow-ups they will ask:**
- Why not set keep-alive very high? : Idle sockets cost memory; just above the balancer's timeout is enough.
- Only one upstream service sees it? : Compare that client's agent idle timeout with the server's.
- Is retrying a POST safe? : Only with an idempotency key.

**Mistakes to avoid:**
- Disabling keep-alive entirely, which adds a TCP and TLS handshake to every request.
- Retrying everything blindly, including non-idempotent writes.

### Q. Uploads over a few megabytes fail with 413 only in production.
**Short answer (45 seconds):** "Only in production" points to a hop that exists only there: nginx, an ingress controller, a CDN or an API gateway with a body size limit. I find which hop returned the 413 from the response headers and body, raise the limit there if the use case is valid, and for real file uploads move to direct-to-storage uploads with presigned URLs.

**Deeper explanation:**

1. Reproduce with known sizes, `curl -i -F "file=@big.pdf" https://api.example.com/upload`, and find the threshold.
2. Identify the hop:
   - An HTML page saying "413 Request Entity Too Large" with `Server: nginx` comes from nginx or ingress-nginx, whose default `client_max_body_size` is 1m.
   - A JSON error in your app's format means your own parser rejected it, for example `express.json()` (default limit 100kb) or multer's `limits.fileSize`.
   - A gateway or CDN error page means its own payload cap, sometimes a hard limit.
   - If the app logs never saw the request, the rejection happened in front of it.
3. Fix it at that layer, and match the app limit so errors stay consistent:

```yaml
# ingress-nginx; for plain nginx use: client_max_body_size 25m;
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "25m"
```

4. Better design for files: the API returns a presigned S3 PUT URL or a GCS signed URL, the browser uploads straight to storage, then calls the API with the object key. The app never buffers the file and gateway limits stop mattering.
5. Check the next limits too: proxy read timeouts, and app memory if the file is buffered instead of streamed.
6. Prevent: staging with the same ingress config, and a smoke test uploading a file at the documented maximum.

**Follow-ups they will ask:**
- Why not raise every limit to 1 GB? : It invites memory exhaustion and abuse; keep limits near the real need.
- How do you scan uploads for malware? : Trigger a scan from the storage event and mark the file usable only after it passes.
- The 413 hits JSON requests, not files? : Something is sending base64 blobs or huge batches; fix the client or paginate.

**Mistakes to avoid:**
- Raising the app limit when nginx is the hop rejecting it.
- Streaming large files through the API servers when direct upload is available.

### Q. Your LLM calls start returning 429 at lunchtime every day.
**Short answer (45 seconds):** A daily pattern means a rate limit hit at a predictable peak: our own traffic, or a scheduled job sharing the same key. I read the 429 body and rate-limit headers to see which limit it is (requests per minute, tokens per minute or spend quota), check what else runs at that hour, then add a shared client-side rate limiter, backoff that honours `retry-after`, and move batch work off the interactive key.

**Deeper explanation:**

1. Measure impact: failure share by feature, and whether retries succeed.
2. Identify the limit. The error body names it; OpenAI sends headers such as `x-ratelimit-remaining-requests` and `x-ratelimit-remaining-tokens`, Anthropic has its own, and both can send `retry-after`. Tokens per minute is often the real constraint, and some providers count the requested `max_tokens` against it, so an oversized `max_tokens` wastes budget. Quota 429s never succeed on retry, and provider overload (Anthropic's 529) is a different problem.
3. Correlate in Langfuse or your metrics: requests and tokens per minute by feature and by key. Typical finds: a midday report or eval job, or one feature sending whole documents as context.
4. Fix in layers:
   - A token bucket per key and model in Redis, so every pod shares one budget.
   - Exponential backoff with jitter that honours `retry-after`, capped at a few tries.
   - Priority: interactive requests first; batch work through a queue or the provider's batch API.
   - Fewer tokens: response caching for repeated questions, prompt caching for long fixed prefixes, smaller `max_tokens`, trimmed context.
   - Fallback to a secondary model or provider while the primary is limited.
5. Prevent: alert when remaining tokens per minute run low, and chart usage against the limit.

```python
delay = min(cap, base * 2 ** attempt) * random.uniform(0.5, 1.0)
delay = max(delay, float(resp.headers.get("retry-after", 0)))
```

**Follow-ups they will ask:**
- Why not retry immediately? : Synchronized retries from every pod make the spike worse.
- One tenant causes most of it? : Per-tenant budgets so one customer cannot starve the others.
- How do you test it? : Mock the provider to return 429 with `retry-after` and assert the client waits.

**Mistakes to avoid:**
- Retrying quota errors, which never succeed.
- Per-pod limiters that ignore the other pods sharing the key.

### Q. The model returns invalid JSON one time in fifty and breaks a pipeline.
**Short answer (45 seconds):** First I make the pipeline survive it: validate every model output against a schema at the boundary and route failures to a retry or dead-letter path instead of crashing. Then I read the failed raw outputs, because truncation, Markdown fences and schema drift need different fixes. The lasting fix is structured outputs or constrained decoding, plus one repair retry and a failure-rate metric.

**Deeper explanation:**

1. Contain: catch the parse error, log the raw output with the trace ID, and send the item to a dead-letter queue so the batch continues; make the step idempotent so retries never write twice.
2. Classify the failures:
   - Finish reason `length` or stop reason `max_tokens`: the JSON was cut off; raise the limit or ask for less.
   - Code fences or "Here is the JSON" prose: JSON asked for in the prompt, never enforced.
   - Valid JSON, wrong shape: missing fields, strings for numbers.
   - A refusal or an apology instead of data.
3. Enforce the format at generation time: OpenAI structured outputs (`response_format` with a JSON schema and `strict: true`), a tool whose input schema is the output on Anthropic, or guided decoding with a JSON schema on vLLM. A system like CADBEATER uses constrained decoding for this reason.
4. Validate anyway and repair once:

```python
from pydantic import BaseModel, ValidationError

class Estimate(BaseModel):
    items: list[dict]
    total: float

def parse(call_llm, prompt: str) -> Estimate:
    raw = call_llm(prompt)
    try:
        return Estimate.model_validate_json(raw)
    except ValidationError as err:  # one repair attempt, then the DLQ
        return Estimate.model_validate_json(call_llm(f"{prompt}\nFix this error: {err}"))
```

5. Prevent: track the parse-failure rate per prompt version and model, add failing inputs to the eval set, and alert when it rises after a change.

**Follow-ups they will ask:**
- Constrained decoding is on and it still fails? : Check truncation and unsupported schema features, and validate business rules separately.
- Does a strict schema hurt quality? : It can for hard reasoning; let the model reason first, then emit the structured result.
- Why not regex the JSON out? : It hides the cause and still fails on truncated output.

**Mistakes to avoid:**
- Treating a successful `JSON.parse` as validation; shape and values still need checking.
- Repair loops with no cap that burn tokens.

### Q. A Kubernetes pod is OOMKilled although the app's own metrics show low memory.
**Short answer (45 seconds):** The kernel kills the container when the whole container's memory crosses its limit, and app metrics usually show only part of it, such as the JavaScript heap or one worker process. I confirm the kill with `kubectl describe pod`, compare the container's working set with its limit, and look for the memory the app metrics do not see.

**Deeper explanation:**

1. Confirm: `kubectl describe pod` shows `Last State: Terminated`, `Reason: OOMKilled`, `Exit Code: 137`. That differs from node-pressure eviction, where the pod shows as `Evicted`.
2. Compare `container_memory_working_set_bytes` with the limit in Prometheus, or use `kubectl top pod --containers`; inside the container (cgroup v2), read `/sys/fs/cgroup/memory.current` and `memory.max`.
3. Compare with the app's view: in Node.js, `process.memoryUsage()` returns `rss`, `heapUsed`, `external` and `arrayBuffers`; a small heap with a large RSS means memory lives outside V8, often Buffers from file or image handling, or native addons.
4. Rank the usual causes:
   - Several processes: Gunicorn or Uvicorn workers each loading a model or cache, while metrics come from one process.
   - Child processes such as headless Chrome or ffmpeg, counted against the same limit.
   - An `emptyDir` with `medium: Memory`, whose files count as memory.
   - Short spikes, such as reading a whole upload into memory, that the scrape never catches.
   - A heap limit above the container limit, so the runtime never collects early enough.
5. Fix: stream instead of buffering, reduce workers or share the model, set the heap below the limit with headroom, and size the limit from observed peaks.

```yaml
resources:
  requests: { memory: "768Mi" }
  limits: { memory: "1Gi" }
env:
  - name: NODE_OPTIONS
    value: "--max-old-space-size=700"
```

6. Prevent: alert when the working set nears the limit, and track restarts per deployment.

**Follow-ups they will ask:**
- Should the memory request equal the limit? : For critical pods yes; with CPU matched too, that gives Guaranteed QoS.
- Why not just double the limit? : It hides a leak and wastes node capacity; find what grows first.
- Does file cache cause it? : Reclaimable cache rarely does, but tmpfs files are not reclaimable.

**Mistakes to avoid:**
- Treating heap metrics as the container's memory.
- Raising the limit without finding what actually used the memory.

### Q. Postgres logs 'deadlock detected' every few minutes after a new feature.
**Short answer (45 seconds):** A deadlock means two transactions each hold a lock the other needs, and Postgres aborts one with SQLSTATE 40P01. Since it started with the new feature, I read the log's `DETAIL` lines, find the two code paths, and look for rows locked in different orders. The fix is a consistent lock order and shorter transactions, plus a retry of the whole transaction on 40P01.

**Deeper explanation:**

1. Read the log; the full entry also shows each query:

```text
ERROR:  deadlock detected
DETAIL:  Process 4121 waits for ShareLock on transaction 99812; blocked by process 4188.
         Process 4188 waits for ShareLock on transaction 99807; blocked by process 4121.
```

2. Turn on `log_lock_waits = on` to also log waits longer than `deadlock_timeout` (1 second by default).
3. Map both statements to code paths; typical patterns:
   - A batch update touching rows in arrival order while another path updates them in a different order.
   - Parent then children in one path, children then parent in another.
   - Inserting child rows takes a `FOR KEY SHARE` lock on the parent row, which conflicts with a transaction that locks that parent `FOR UPDATE` or deletes it.
   - An external call (payment, LLM) inside the transaction, holding locks longer.
4. Fix the order: sort the IDs and lock them up front.

```sql
BEGIN;
SELECT id FROM inventory WHERE id = ANY($1) ORDER BY id FOR UPDATE;
UPDATE inventory SET reserved = reserved + 1 WHERE id = ANY($1);
COMMIT;
```

5. Shrink transactions: no network calls inside, and atomic single-statement updates (`UPDATE ... SET stock = stock - $1 WHERE id = $2 AND stock >= $1`).
6. Retry the whole transaction on 40P01 with jittered backoff; the aborted one rolled back fully.
7. Prevent: watch the `deadlocks` counter in `pg_stat_database`, and add an integration test that runs both paths concurrently.

**Follow-ups they will ask:**
- Can you raise `deadlock_timeout`? : That only delays detection; the cycle is still there.
- Would another isolation level help? : No; deadlocks come from lock order, and Serializable only adds serialization failures to retry.

**Mistakes to avoid:**
- Adding retries without fixing the lock order, which turns deadlocks into latency.
- Holding a transaction open across an HTTP or LLM call.

### Q. The agent's run fails with a context length error halfway through a long task.
**Short answer (45 seconds):** Halfway through means the context grew each step until the prompt plus the requested output no longer fit. I open the trace and check input tokens per step to see what grows, usually tool outputs or the full history. The fix is a token budget per step, capped tool outputs, summarized old turns, and resuming the run from its last checkpoint.

**Deeper explanation:**

1. Contain: with a LangGraph checkpointer, compact the state and resume from the last good step instead of restarting.
2. Confirm the error: OpenAI returns the code `context_length_exceeded`; Anthropic returns a 400 saying the prompt is too long.
3. Find the growth in the trace: Langfuse shows tokens per generation, so look for the step where input tokens jump.
4. Rank the causes:
   - Tool results returned in full: whole files, HTML pages, thousands of database rows.
   - History never trimmed inside reflection or retry loops.
   - Retrieved chunks appended every step, never dropped.
5. Fix:
   - Cap tool results at the tool boundary: return a summary plus a handle (file ID, row count) and let the agent fetch a specific slice.
   - Per-node token budgets checked before each call, the approach a system like CADBEATER takes with context compression.
   - Keep the last few turns verbatim and replace older ones with a running summary; keep the plan, IDs and key numbers in structured state, not chat history.
   - Split work into sub-agents that start with a fresh context and return short results.
6. Prevent: alert on runs nearing the window and add a long-task eval case; quality often drops before the hard limit anyway.

**Follow-ups they will ask:**
- Why not use a model with a bigger window? : It delays the failure, costs more per step, and very long contexts tend to reduce accuracy.
- What do you lose by summarizing? : Exact details, so keep IDs, numbers and decisions in structured state.
- How do you test it? : A synthetic long task with oversized tool outputs in CI.

**Mistakes to avoid:**
- Truncating from the start of the prompt and dropping the system instructions.
- Restarting a long run from scratch and paying for every step again.

### Practice
- Build a personal error log: for every real error you have fixed, write one row with the signal (exact message, status code or metric shape), the layer, the first check, the cause and the fix. Start with the ones from your own projects [your examples] and add a row each time you fix something new.
- Break it on purpose: run an app behind local nginx with `client_max_body_size 1k` and upload a file; set a container memory limit below what a Node.js script allocates and watch `kubectl describe pod` report `OOMKilled`; read each signal exactly as you would in production.
- Reproduce a Postgres deadlock with two `psql` sessions updating the same two rows in opposite order, read the log entry, then fix it with ordered `SELECT ... FOR UPDATE`.
- Say it out loud: pick any row from the table above and, in under 60 seconds, say which layer produced the error, your first check, the most likely cause and the fix.
