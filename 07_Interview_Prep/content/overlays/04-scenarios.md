## Agent Fundamentals

### Why it exists
Some tasks cannot be written as a fixed script, because the number and order of steps depend on what you find along the way, like investigating a support ticket or reading a set of drawings. Before tool calling, teams either hard-coded decision trees and intent-based chatbots that broke on anything off-script, or used a single model call that could only produce text, never act. An agent closes that gap: the model picks the next action, your code runs it and feeds back the result, and the loop repeats until the job is done. The cost is that every loop iteration is another paid, slow model call and behaviour varies between runs, so you use an agent only where the path really is unknown.

## Agentic Design Patterns

### Why it exists
Teams that built agents from scratch kept rediscovering the same handful of shapes and the same failures. Named patterns such as prompt chaining, routing, parallelization, orchestrator-workers and evaluator-optimizer give you proven structures, so you can pick the least autonomous one that solves the task instead of defaulting to a free-running loop. Before them, the choice was usually one giant prompt that tried to do everything, or an open-ended agent with no structure at all. The trade-off is a sliding scale: more structure is cheaper, faster and easier to test, while more autonomy copes with unusual cases but is harder to predict and debug.

## Context Engineering

### Why it exists
The model sees only what is in its context window on each call; that window is finite, every token in it costs money and latency, and answer quality drops when it is stuffed with irrelevant text. Prompt engineering focused on wording a single instruction, but an agent running thirty steps piles up tool results, history and documents, and what goes into the window starts to matter more than how the instruction is phrased. Context engineering is the discipline of choosing, trimming, ordering and summarising that content at every step. The trade-off is that every cut or summary can drop the one fact the model needs later, so these choices must be measured, not guessed.

## Memory & State

### Why it exists
Models are stateless: every API call starts from nothing except what you send. Without deliberate state, an agent forgets what it already did when a worker crashes, users repeat their preferences every session, and a task cannot pause for a human and continue later. Early systems pasted the whole chat log into every request until it overflowed, or kept state in process memory that vanished on the next deploy. Checkpoints (saved run state) and long-term memory stores fix this by persisting exactly what is needed, scoped to a run or to a user. The cost is storage, privacy and deletion duties, and the risk of remembering something wrong or something an attacker planted.

## Harness & Loop Engineering

### Why it exists
The model only proposes actions; something has to execute tools, enforce limits, handle errors and decide when to stop, and that something is the harness, the ordinary code wrapped around the model. Early demos were a bare while loop with no limits, which is how agents ended up looping all night, running dangerous commands or crashing on the first tool error. A good harness turns a capable but erratic model into a bounded system with timeouts, budgets, sandboxes and stop rules. The trade-off is that you own and test this code, and limits set too tight block legitimate work while limits set too loose burn money.

## Multi-Agent Systems

### Why it exists
One agent with dozens of tools and one huge prompt starts picking the wrong tools and filling its context with material unrelated to the current step, and some work is naturally parallel, like researching several sources at once. Splitting the job across specialist agents, each with its own short prompt, small toolset and clean context, with a planner or supervisor coordinating, addresses both problems. Before this, teams kept growing one overloaded prompt or wired fixed pipelines by hand. The cost is more tokens because every agent must be briefed, more latency for coordination, and new failure modes such as agents making conflicting assumptions or handing work back and forth forever.

## MCP & Tool Ecosystems

### Why it exists
Before MCP, every AI application wrote its own integration code for every tool, so ten apps and ten tools meant up to a hundred custom connectors, each with its own auth and its own bugs. MCP (Model Context Protocol) is a shared standard: a tool provider writes one server, and any MCP-capable host, such as an IDE, a desktop assistant or your own agent, can discover and call its tools. It moves integrations out of each app into reusable, separately deployed servers. The cost is an extra process and network hop, more tool descriptions competing for context, and a new security surface, because a third-party server's descriptions and results are text the model may obey.

## Agent Reliability & Evaluation

### Why it exists
An agent is non-deterministic and multi-step, so the same task can pass on one run and fail on the next, and a correct final answer can hide a dangerous step in the middle. Before agent evaluation, teams checked a few demos by eye and shipped, and regressions from a prompt tweak or a model upgrade reached users first. Evaluation gives repeatable task suites, checks on the path the agent took as well as the result, repeated trials to measure consistency, and production tracing to see what actually happened. The cost is real engineering effort for datasets and graders, token spend for every trial, and model-based judges that can themselves be wrong.

## Production Agent Architecture

### Why it exists
An agent run can take minutes, call slow tools, fail halfway or wait days for a human, and a normal request and response web endpoint times out or loses the work on the next deploy. Production architecture moves runs onto queues and workers, saves progress after each step, streams updates to the user, and enforces per-tenant budgets and isolation. The early pattern, one HTTP handler calling the model in a loop, works in a demo and falls over under real traffic and real failures. The trade-off is more moving parts to run and monitor: queues, workers, an event store and sometimes a workflow engine.

## Voice & Multimodal Agents

### Why it exists
People want to talk to software, on the phone or in an app, to book, cancel or ask questions, and spoken conversation has short gaps between turns, so a long silence feels like the line dropped. Before voice agents, phone systems used IVR menus ("press 1 for billing") and rigid intent-based voice bots that failed on anything unexpected. A voice agent chains streaming speech-to-text, a model and text-to-speech, or uses one speech-to-speech model, and is built to handle interruptions; multimodal agents also take images, documents and video frames as input. The cost is a tight latency budget, harder interruption handling, a higher cost per minute, and transcription errors that turn into wrong actions.

## Tool Design, Guardrails & Human-in-the-Loop

### Why it exists
Tools are everything an agent can actually do to the world, so a vague or over-powerful tool turns a model mistake or a prompt injection (instructions hidden in content the agent reads) into real damage, such as a wrong refund or deleted data. The common early approach was to expose existing REST endpoints one to one with an admin key and ask the model, in the prompt, to be careful. Task-shaped tools, permissions enforced in code at execution time and human approval for high-impact actions mean the agent can be wrong without the mistake becoming permanent. The cost is slower flows for approved actions, approval fatigue for reviewers, and extra engineering to keep permissions tight without blocking legitimate work.

## Agent Project Scenarios [Scenarios]

> Interviewers run these as a 15 to 30 minute design conversation: they describe a product, you ask questions and sketch the system, and they add twists ("the reviewer is on leave for a week", "security says no shared keys"). A weak answer starts with a framework name and a diagram of boxes labelled "agent". A strong answer pins down what the agent may do without a human, splits deterministic work from model work, puts every side effect behind a gate enforced in code, plans how the run survives crashes and long waits, and names the metrics that will prove it works.

### Concepts you must understand
- Start with the action surface: list every side effect the agent could cause, rate each by reversibility and cost of a mistake, and decide what runs alone, what needs approval and what is never allowed.
- Ask first: volume and peak concurrency, latency target per turn and per run, who approves and how fast, which systems of record are involved, and what happens today without the agent.
- Split the work: deterministic code for rules, totals, eligibility and permissions; the model for reading messy input, choosing tools and drafting; never let the model compute what a function can.
- Estimate the loop: steps per run times tokens per step gives cost per run; multiply by runs per day before choosing models, caching and compaction.
- Plan durability up front: any run that can wait for a person or outlive a deploy needs checkpointed state, idempotent side effects and a state schema you can version.
- Choose the least autonomous design that works: a workflow with one model step, a router, or one agent before a multi-agent system, and justify each extra agent with a measured problem.
- Define success before building: task success checked against the system of record, escalation rate, cost and latency per completed task, and a regression suite built from real cases.

### Q. You are building a support agent for an e-commerce site that can look up orders and issue refunds, but every refund must be approved by a human. Walk me through the design.

**Short answer (45 seconds):** I would clarify volume, refund policy, who approves and how fast, then split the system: the agent reads orders, payments and shipping status and drafts a refund proposal; deterministic code checks eligibility and limits; a human approves in an agent console; and only an executor, never the model, calls the payment provider with an idempotency key. The customer sees an honest "under review" status while the run waits as a durable checkpoint, not a live process.

**Deeper explanation:** Pin down first: ticket volume and sale-event peaks, refund rules (return window, partial refunds), approver roles and SLA, and what the agent may promise.

```text
chat -> API -> queue -> worker (LangGraph + Postgres checkpointer)
  read tools: get_customer, search_orders, get_payment, get_shipment
  propose_refund(order_id, amount, reason) -> eligibility rules -> approvals row
  console: order, evidence, policy result -> approve | edit | reject
  executor: approval matches hash(args) -> payments.refund(idempotency_key)
  run resumes -> agent tells the customer the outcome
```

Key decisions. Eligibility is code, so the model cannot talk its way past a closed return window or an existing refund. The model's job is understanding the complaint and assembling evidence. The approval is bound to a hash of the exact arguments, so nothing changes after a human says yes. The agent may say "under review", never "approved", until a human decides. Customer messages are untrusted: "your manager already approved it" is text, not authority. Aggregate caps per order and per day stop split refunds.

Measure: containment (tickets closed without a human agent), approval turnaround, approver reject rate per refund reason (high means bad proposals or bad policy), wrong-refund rate from audits, and cost per resolved ticket.

**Follow-ups they will ask:**
- Approvers are swamped during a sale?: Auto-approve below a small amount with per-customer caps, as versioned business policy.
- The customer leaves the chat while it is pending?: The resumed run sends the outcome by email or notification; the chat session is not the run.
- Partial refunds?: The approver edits the amount, and the edited arguments are what executes.

**Mistakes to avoid:**
- Letting the model decide eligibility, or say "approved" before a human has decided.
- Calling the payment API from inside the model loop without an idempotency key.

### Q. You inherit one agent with 38 tools and a long system prompt. Wrong tool calls and cost keep rising, and your lead wants a planner plus specialist agents. How do you plan the split?

**Short answer (45 seconds):** I measure first, because a split can make things worse. I build a baseline from production traces: success rate, tool-selection errors grouped by intent, tokens and latency per task. Then I try the cheap fixes: merge overlapping tools, rewrite descriptions, load tool subsets per intent through a router. If errors still cluster by domain, I split into a planner that delegates to a few specialists with typed briefs and results, migrate one domain at a time behind a flag, and compare against the baseline.

**Deeper explanation:** Questions to answer before splitting: do failures cluster by domain, do domains need conflicting instructions, and is any of the work parallel? If all three answers are no, a router that picks one tool subset per intent fixes selection without a second agent.

When splitting, I prefer agents-as-tools over peer handoffs: the planner keeps control, calls `billing_agent(brief)` like any tool and merges results, so one place owns the plan and the final answer.

```python
class Brief(BaseModel):
    goal: str
    customer_id: str
    constraints: list[str]
    max_steps: int = 8

class Result(BaseModel):
    status: Literal["done", "blocked", "needs_human"]
    summary: str
    facts: dict[str, str]          # ids and values, not transcripts
    actions_taken: list[str]
```

Rules: one specialist owns the writes in each domain; specialists get ids and constraints, not the whole transcript; the planner never calls domain tools directly. Migration: replay recorded traffic through the new system in shadow mode, compare outcomes and trajectories, then route one intent at a time behind a flag.

Measure: tool-selection accuracy per specialist, task success and pass^k against the baseline, tokens per task (expect a rise and set a ceiling), latency per task, and the share of briefs that come back "blocked".

**Follow-ups they will ask:**
- Cost goes up after the split?: Briefing overhead is expected; use a small model for the planner if routing is easy, and cap delegations per task.
- Two specialists need the same fact?: The planner passes it explicitly in both briefs; no hidden shared memory.
- When would you refuse to split?: Sequential, tightly coupled work where every step depends on the previous decision.

**Mistakes to avoid:**
- One agent per job title with no measured reason.
- A big-bang cutover with no baseline to compare against.

### Q. Security says no more shared admin keys. You must expose internal services (orders, Jira, deployments) to agents and to developers' IDEs through MCP. How do you design it?

**Short answer (45 seconds):** I would run remote MCP servers over Streamable HTTP, one per domain, with the company identity provider as the OAuth authorization server. Clients get user-delegated tokens whose audience is that server and whose scopes match tool groups; each server validates the token, filters `tools/list` by scope, enforces policy per call, and reaches downstream systems with its own credentials mapped to the user, never by passing the user's token through. Writes need confirmation, and every call is audited by user, client and tool.

**Deeper explanation:** Clarify first: which clients (IDE assistants, internal agents, jobs with no user), which actions are writes, and whether the identity provider allows dynamic client registration or only pre-registered clients.

```text
host (IDE or agent) --auth code + PKCE--> IdP (Okta or Entra)
host --Bearer token (aud = mcp-orders)--> mcp-orders server
  validate: signature, exp, iss, aud, scope orders:read | orders:refund
  policy:   tenant, amount caps, approval for writes
  downstream: orders API with the server's credential + user id (or token exchange)
  audit:    user, client_id, tool, args hash, result status
```

Decisions. One server per domain, so scopes, owners and blast radius stay small. Scopes follow risk: reads broadly, writes to specific groups, deploys to on-call only. Agents with no user use the client credentials grant with narrow scopes and stricter rate limits. Tool definitions are versioned and reviewed like an API; servers send `notifications/tools/list_changed` on change, and hosts pin approved versions. Keep servers stateless where possible so a pod restart does not kill sessions.

Risks: over-broad scopes, token passthrough creating a confused deputy, long-lived refresh tokens on laptops. Measure: auth failures by reason, denied calls by policy rule, tool latency, and calls per user per tool.

**Follow-ups they will ask:**
- A legacy service only accepts a static API key?: The MCP server holds it in a secrets manager, users never see it, and the server applies per-user policy before using it.
- Revoking a leaked token?: Short access token lifetimes plus refresh token revocation at the identity provider.
- Local stdio servers?: Only for developer tools on local files, sandboxed, with no production credentials.

**Mistakes to avoid:**
- Forwarding the user's MCP token to downstream APIs.
- Exposing every endpoint as a tool under one admin scope.

### Q. In a system like CADBEATER, a plan-and-execute agent drafts a construction estimate from drawings, and an estimator must review it before it reaches the client. Reviews can sit for days. How do you design the pause and resume?

**Short answer (45 seconds):** The run is state, not a process. The graph plans, runs extraction and pricing steps, computes totals in code, then hits an `interrupt()` before anything leaves the company. The Postgres checkpointer stores the state under a `thread_id` tied to the estimate, so no worker waits. The reviewer edits line items in a UI, the decision endpoint resumes the graph with `Command(resume=...)`, totals are recomputed deterministically from the edited items, and only then is the estimate finalised.

**Deeper explanation:** Requirements: who reviews, the review SLA, what the reviewer can change (quantities, rates, line items), and what happens if drawings or price lists change during the wait.

```python
def review(state: EstimateState):
    decision = interrupt({"estimate_id": state["estimate_id"],
                          "lines": state["lines"],
                          "price_list": state["price_list_version"]})
    if decision["action"] == "reject":
        return Command(goto="replan", update={"feedback": decision["notes"]})
    return Command(goto="finalise", update={"lines": decision["lines"]})
```

Design points. Each line item carries evidence (drawing region, retrieved price source, model confidence), so the reviewer checks rather than redoes. Edits replace state fields; the model never regenerates the estimate after a human corrected it. Pin versions in state (price list, graph version, model) and check for staleness on resume: if the drawing revision or price list changed, flag the estimate instead of silently mixing versions. Days-long waits survive deploys only if new code can read old checkpoints, so new fields get defaults and removed nodes keep a shim until old threads drain. Reminders and escalation run on a schedule, but nothing is ever auto-approved. Progress events reach the UI through Redis Streams and SSE.

Measure: reviewer edit rate per line-item category (the best signal for what to fix next), time in review, resume failure rate, and estimate value changed by review.

**Follow-ups they will ask:**
- The reviewer rejects with notes?: Route to a replan node with the notes as input and a cap on replans.
- Two reviewers open it at once?: Optimistic locking on a state version; the second submit gets a conflict.
- Why not Temporal?: Fine for multi-system workflows; the graph checkpointer is enough when the human wait is the only long step.

**Mistakes to avoid:**
- Holding the run in memory or in a long HTTP request while waiting.
- Letting the model re-total the estimate after human edits.

### Q. Your agent has run in production for three months with Langfuse traces but no evals, and every prompt change is a gamble. Build an eval harness from the traces.

**Short answer (45 seconds):** I mine the traces for cases, not averages. Pull every failed, escalated and thumbs-down run plus a random sample, group them by intent, scrub personal data, and label the expected outcome with a domain expert. Each case becomes an input, seeded tool fixtures, a deterministic outcome check and a few trajectory rules. The harness runs each case several times, reports pass rate, pass^k, cost and steps, and gates every prompt, tool or model change in CI.

**Deeper explanation:** Steps in order: export traces by filter (scores, tags, error status), cluster them by intent and failure type, pick a first set of a few dozen cases weighted toward failures and high-value intents, and write each expected outcome as a check against state, not a reference answer.

```yaml
id: refund-damaged-item-017
source_trace: tr_8c1
input: "My blender arrived cracked, order 8f2k"
fixtures: { search_orders: orders_8f2k.json, get_shipment: delivered.json }
expect:
  outcome: { approvals_created: 1, max_amount: 4999 }
  must_call_before: [[search_orders, propose_refund]]
  never_call: [issue_refund]
trials: 5
```

Fixtures replay recorded tool responses, so runs are cheap and repeatable; a smaller set runs against a seeded sandbox to catch fixture drift. Graders are deterministic first (state checks, call order, forbidden calls), then an LLM judge with a written rubric only for tone or explanation quality, calibrated against human labels before anyone trusts it. Store cases as a versioned dataset (Langfuse datasets or files in the repo) so every experiment links to a dataset version and a prompt version.

Keep it alive: every incident and every approver rejection becomes a candidate case, and cases are retired when the product changes. Measure the harness itself: judge agreement with humans, flaky cases that flip with no code change, and whether offline scores move with production success.

**Follow-ups they will ask:**
- Traces contain customer data?: Redact before export, swap ids for synthetic ones, and keep the dataset under production access controls.
- How many trials?: Enough to see variance; five per case on the core set, more on cases that flip.
- Offline improves but production does not?: The dataset is unrepresentative; resample from recent traffic.

**Mistakes to avoid:**
- Grading free-form tasks against a golden answer string.
- Building the set from happy-path demos instead of real failures.

### Q. A chain of clinics in Dubai and Bangalore wants a phone agent that books, moves and cancels appointments in English, Arabic and Hindi. How do you design it?

**Short answer (45 seconds):** I would clarify call volume, languages, the scheduling system's API, privacy rules for patient data, and when a call must go to a receptionist. Then a cascaded design: SIP telephony into a real-time media layer such as LiveKit, an agent worker with voice activity detection and turn detection, streaming speech-to-text, a model with a handful of booking tools, and streaming text-to-speech. Slots are held briefly before confirmation, details are read back before booking, and a human transfer is always one tool call away.

**Deeper explanation:** Cascaded wins here: transcripts for audit, reliable tool calls, a speech model per language and control over what is said; speech-to-speech is worth testing later for latency.

```text
caller -> SIP trunk -> media room -> agent worker
  VAD + turn detection -> streaming STT (per-language model)
  tools: verify_caller, find_slots, hold_slot, book, reschedule, cancel, transfer_to_reception
  streaming TTS -> caller; filler line during slow tools
scheduling API <- book(idempotency_key); SMS confirmation after commit
```

Decisions. Verify identity before revealing anything (caller number plus date of birth), because appointment details are health data. The system of record prevents double-booking: `hold_slot` creates a short hold (for example Redis `SET slot:123 caller_9 NX PX 120000` if the scheduler cannot hold natively) and `book` commits with an idempotency key. Dates, times and names are where recognition fails ("fifteen" versus "fifty", similar surnames), so the agent reads back the full booking and waits for an explicit yes. Keep tools few and outputs short; every token is spoken time. On barge-in, cancel TTS and record only what was actually played.

Measure: booking completion and transfer rates, latency from end of caller speech to first audio (p50, p95), recognition errors on dates and names, double bookings (target zero), and cost per call minute.

**Follow-ups they will ask:**
- The caller switches language mid-sentence?: Pick speech-to-text that handles code-switching, and test with real mixed speech.
- The scheduler API is slow?: Speak a filler, call it asynchronously, and cache today's free slots briefly.
- The caller mentions emergency symptoms?: A deterministic check that transfers immediately with an emergency message.

**Mistakes to avoid:**
- Booking straight from the transcript without a read-back.
- Treating latency as an LLM problem and ignoring the other hops.

### Practice
- Build the refund agent in miniature: read tools over a seeded Postgres, a `propose_refund` tool that writes an approvals row, a tiny approval page and an executor with idempotency keys; prove with a test that resuming the same run twice refunds once.
- Take an agent with many tools, log tool-selection errors per intent over 50 scripted tasks, then compare three fixes: better descriptions, a router with tool subsets, and a planner with two specialists; report success, tokens and latency for each.
- Stand up one MCP server over Streamable HTTP with OAuth against a dev tenant of an identity provider, filter `tools/list` by scope, and show that a read-scoped token cannot call a write tool.
- Say it out loud: in three minutes, design the estimate review pause and resume, including what happens when the price list changes while the estimate waits.

## Agent Incidents & Error Cases [Scenarios]

> Incident questions test whether you can run a calm, ordered response on a system that is non-deterministic and spends money while it misbehaves. Use the same structure every time: clarify impact (which agents, tenants and runs, since when, and which side effects already happened), contain (kill switch, pause the queue, disable one tool, roll back the prompt or model version), diagnose from traces at the first wrong step rather than the last error, fix the cause, then prevent a repeat with an alert, an eval case and a runbook entry. A weak answer raises the step limit or rewrites the prompt; a strong answer checks what already happened in the real world before anything else.

### Concepts you must understand
- Side effects first: before debugging, find which runs already refunded, emailed or wrote data, because an agent incident can leave damage that outlives the fix.
- Containment without a deploy needs controls built in advance: kill switches per tool and per agent, a queue pause, version flags for prompts and models, and a per-tenant disable.
- The trace is the evidence: the exact request the model saw, the raw tool result, the stop reason and the versions in use; the chat view hides most of it.
- Most agent incidents start outside the model: a tool contract changed, a credential rotated, a deploy changed the state shape, or the harness disguised a tool error as data.
- Every incident ends with an eval case and an alert on the symptom, so the next occurrence is caught by a metric before a user reports it.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| LangGraph raises `GraphRecursionError` ("Recursion limit of ... reached without hitting a stop condition") | Trace for repeated tool name and argument pairs | A tool returns the same error every time, no terminal condition, two nodes routing to each other | Actionable tool errors, repetition detector, terminal tool; raise `recursion_limit` only for legitimately long tasks |
| OpenAI Agents SDK raises `MaxTurnsExceeded` | Handoff spans and the active agent per turn | Two agents handing the conversation back and forth | One-way handoffs or return control to a supervisor, cap handoffs per run |
| Cost per run jumps after a release | Steps per run, input tokens per call, cache read tokens | Longer trajectories, cache prefix broken by a timestamp or reordered tools, retry storms | Roll back the version, restore a stable prefix, add a cost gate to evals |
| OpenAI `context_length_exceeded`, or Anthropic 400 "prompt is too long" | Input tokens per span and the largest tool result in the run | Unpaginated tool output, raw HTML or logs, history never compacted | Cap and paginate tool results, store large output and pass a reference, compact earlier |
| `stop_reason` is `max_tokens` and the JSON or answer is cut off | Output tokens against the `max_tokens` setting | Output reserve too small, model writing a huge argument | Raise the reserve, ask for smaller outputs, treat that stop reason as a failure |
| Agent says "refund issued" but payments has no record | Raw tool result and span status for the write call | Wrapper caught an HTTP 500 and returned an empty or HTML body as data | Return errors flagged as errors, verify outcomes against the system of record |
| Same wrong tool chosen for one intent | Tool choice per intent in traces, diff of the tool list | Overlapping descriptions, a new server with similar names, too many tools loaded | Rename and disambiguate, route tool subsets, add selection evals |
| MCP server returns 401 with `WWW-Authenticate: Bearer error="invalid_token"` | Token `aud`, `iss`, `exp` and key id; the server's key cache | Client sending a cached old token, refresh token revoked, server not fetching new signing keys | Refresh once on 401, refetch keys on an unknown key id, reload rotated secrets |
| Requests carrying an `Mcp-Session-Id` header get HTTP 404 after a deploy | Pod restarts and load balancer stickiness | Sessions held in memory on one pod | Client re-initializes on 404; external session store or a stateless server |
| MCP `tools/call` fails with JSON-RPC error `-32602`, or returns `isError: true` about arguments | Schema from `tools/list` against the arguments sent | Server changed a schema, host cached an old tool list | Handle `notifications/tools/list_changed`, add new tool names instead of changing old ones |
| A user sees another user's name, order or preference | Memory namespace, `thread_id` and cache keys in the trace | Colliding `thread_id`, unscoped vector search, module-level state in a worker, response cache keyed only on the prompt | Scope every key by tenant and user, enforce filters in the store, purge leaked data |
| Resume after a deploy fails with `KeyError` or `ValidationError` on a state field | State schema diff between versions, the checkpoint's next node | Renamed or removed field or node, changed type | Defaults and migrations for state, keep old nodes until threads drain, version graphs |
| Runs stuck in `awaiting_approval` for days | Approval age, notification delivery logs, approver roster | No expiry job, failed notification, nobody holds the approver role | Sweeper that expires to reject and notifies, escalation chain, alert on approval age |
| Output contains system prompt text or a key-shaped string | Output scanner hits and the turn's full context | Secret placed in the prompt, injection asking to repeat instructions, tool error echoing config | Rotate, remove secrets from context, output filter, canary string in the prompt |

### Q. After a prompt change, runs start ending with `GraphRecursionError` and cost per run climbs. Walk me through it.

**Short answer (45 seconds):** First I contain: roll the prompt back with its version flag, or pause the affected agent, and check for repeated write calls. Then I read failing traces for the repeating pattern: the same tool with the same arguments, or two nodes routing to each other. The fix goes at the cause (an unhelpful tool error, a missing stop condition, a routing cycle) plus a repetition detector.

**Deeper explanation:** Impact: affected runs and spend since the release, plus any write calls in them, since a loop around a write tool repeats the action.

```sql
SELECT run_id, tool, args_hash, count(*) AS n
FROM tool_spans
WHERE started_at > '2026-11-01 10:00' AND agent = 'support'
GROUP BY run_id, tool, args_hash
HAVING count(*) >= 3
ORDER BY n DESC LIMIT 20;
```

Then read one looping trace. Likely causes, ranked:
1. A tool returns the same error or an empty result, and the new prompt says "keep trying until you find it", so the model retries forever.
2. The stop condition broke: a terminal `submit` tool was renamed or the prompt no longer says when to finish, so the conditional edge never routes to the end.
3. A routing cycle: a supervisor sends work to a specialist that hands it straight back (in the OpenAI Agents SDK it surfaces as `MaxTurnsExceeded`).
4. Compaction dropped the fact that the task was already done.

Fix: make the tool error actionable ("no orders in 90 days; do not search again"), restore the terminal condition, and end the run with an escalation record after three identical calls or six steps without progress. Prevent: an eval case with a step ceiling, alerts on budget-trip rate and on cost per run against the previous version, and a per-run dollar cap.

**Follow-ups they will ask:**
- Just raise the recursion limit?: Only when traces show legitimately long tasks; the limit is a fuse, not a fix.
- Only one tenant loops?: Check that tenant's data; a tool may return an unusual shape for them.
- It is two agents ping-ponging?: Make handoffs one-way or return control to a supervisor, and cap handoffs per run.

**Mistakes to avoid:**
- Raising the limit and calling it fixed.
- Ignoring side effects the loops already caused.

### Q. After you connect a second MCP server, the agent keeps calling `search_docs` when users ask about their own orders. What do you do?

**Short answer (45 seconds):** I confirm the pattern in traces (tool chosen per intent before and after the change), then diff the tool list the model now receives: names, descriptions and count. The usual cause is a new tool whose description overlaps the right one, or a near-duplicate name. Short term I remove or restrict the new server for this agent; the real fix is clearer names and descriptions, tool subsets per intent, and a selection eval on every tool-list change.

**Deeper explanation:** Measure the share of "order status" first calls that went to `search_orders` before and after the change, then diff the tools in logged requests:

```bash
jq '[.tools[] | {name, description}]' request_before.json > before.json
jq '[.tools[] | {name, description}]' request_after.json  > after.json
diff before.json after.json
```

Likely causes, ranked:
1. Overlapping descriptions: the new tool says "search anything about the customer's account", which matches order questions better than a terse `search_orders` description.
2. Too many tools: selection degrades as the list grows.
3. Name collisions: two servers both expose `search`, and the host renamed or shadowed one.
4. Tool poisoning: the new server's description tells the model to prefer its tools. Read the full descriptions, not a summary.

Fix: rewrite both descriptions to say when to use and when not to ("for a customer's orders use search_orders, not this tool"), prefix tools by server (`docs_search`, `orders_search`), and load only the tool groups an intent needs through a router or an agent profile. Pin the new server's version and hash its definitions so a later description change is detected. Prevent: a tool-selection eval (labelled intents, expected first tool) gated in CI on any tool-list change, plus a dashboard of tool choice per intent.

**Follow-ups they will ask:**
- Can you force the right tool?: For known intents, yes, with `tool_choice` naming a specific tool or a fixed workflow step; not globally.
- Right tool, wrong arguments?: Tighten the schema with enums and examples, and return actionable validation errors.
- Who approves new MCP servers?: Treat adding one as an API change: owner review, description review, eval run.

**Mistakes to avoid:**
- Adding "always use search_orders" to the system prompt and leaving the conflict in place.
- Connecting every available server to every agent.

### Q. A customer says their refund never arrived, but the agent told them "Your refund has been issued." The payments service logged an HTTP 500 at that moment. How do you investigate and fix it?

**Short answer (45 seconds):** First I find every run with the same shape: a write tool span with an upstream 5xx followed by a success message to the customer. Then I read the raw tool result the model received; the usual cause is a wrapper that caught the exception and returned an empty string, an HTML error page or a generic "ok". I fix the wrapper to return a flagged error, add an outcome check before any success claim, and contact affected customers with correct information.

**Deeper explanation:** Impact first: look up each affected refund at the provider by idempotency key, because a 500 does not prove it failed.

```python
# broken: every failure looks like data
try:
    return payments.refund(order_id, amount, idempotency_key=key).text
except Exception:
    return ""

# fixed: error flagged for the model
resp = payments.refund(order_id, amount, idempotency_key=key)
if resp.status_code >= 500:
    return ToolResult(is_error=True,
        content="Payments unavailable. Refund NOT issued. Do not say it succeeded; offer escalation.")
```

Likely causes, ranked: the wrapper swallows exceptions; the HTTP client does not raise on 5xx (Python `requests` needs `raise_for_status()`); the tool returns the raw body and the model reads an HTML error page as acceptable; the prompt tells the model to always reassure the customer. Anthropic's `tool_result` block accepts `is_error: true` and MCP results carry `isError: true`; use them.

Fix and prevent: a contract test per write tool that simulates a 500, a timeout and a malformed body and asserts the result is flagged; a harness rule that the final message may claim an action only if a matching successful tool span exists; a daily reconciliation of "refund issued" messages against the payments ledger; and an alert on write-tool error rate. Retry once with the same idempotency key before reporting failure.

**Follow-ups they will ask:**
- The refund actually succeeded despite the 500?: The idempotency key lets you find it and prevents a duplicate on retry.
- Should the model see the status code?: A short plain reason and the next step, not a stack trace.
- How do you catch false claims in free text?: Compare claimed actions with successful spans before sending.

**Mistakes to avoid:**
- Fixing the prompt ("never claim success unless sure") instead of the wrapper.
- Retrying the refund without the original idempotency key.

### Q. Right after a scheduled secret rotation, every call to your internal MCP server fails, and logs show `401` with `WWW-Authenticate: Bearer error="invalid_token"`. Walk me through it.

**Short answer (45 seconds):** I check whether it is every client or one, then decode a failing token (issuer, audience, expiry, key id) and compare it with what the server expects. After a rotation the usual causes are a client still sending a cached old token, a refresh token the rotation revoked, or a server whose cached signing keys lack the new key id. I contain by reloading whichever side holds stale material, then make both sides handle rotation without a restart.

**Deeper explanation:** Impact: which agents and hosts are failing, and whether runs fail loudly or the agent quietly answers without its tools, which is worse.

```bash
# decode without verifying (debugging only; needs PyJWT)
python3 -c "import jwt,sys; t=sys.argv[1]; print(jwt.get_unverified_header(t)); print(jwt.decode(t, options={'verify_signature': False}))" "$TOKEN"
# signing keys the identity provider publishes now
curl -s https://idp.example.com/.well-known/jwks.json | jq '.keys[].kid'
```

Likely causes, ranked:
1. The server caches the JWKS (the identity provider's public signing keys), and tokens are now signed with a key id it never fetched.
2. The client caches an access token past its life, or holds a refresh token the rotation revoked, and does not refresh on 401.
3. A client secret or static key was rotated in the secrets manager, but pods read it once at startup from an environment variable.
4. The rotation changed audience or issuer configuration, so the signature verifies but the `aud` or `iss` check fails.

Fix: on an unknown key id, the server refetches the JWKS once before rejecting; the client, on 401 with `invalid_token`, refreshes once and retries, and if refresh fails it surfaces "re-authentication needed" instead of looping; secrets are read from the secrets manager with reload, not frozen in the environment. Prevent: rotate in staging first, publish new keys before signing with them, alert on 401 rate per client, and make the agent fail closed when a tool is unauthorized.

**Follow-ups they will ask:**
- Only one host fails?: That host's token cache or refresh logic; the others prove the server side is fine.
- 403 instead of 401?: The token is valid but lacks scope (`insufficient_scope`); check the scope mapping, not the keys.

**Mistakes to avoid:**
- Turning off token validation to restore service.
- Retrying a stale token in a loop.

### Q. A user reports that the assistant greeted them by another customer's name and mentioned that customer's order. What do you do?

**Short answer (45 seconds):** I treat it as a data breach until proven otherwise: confirm it from the trace, disable memory reads or the feature, and bring in security and privacy owners, since there may be a duty to notify. Then I find the span where the other customer's data entered the context, fix the scoping in code and storage, purge contaminated data, and find every affected session.

**Deeper explanation:** Open the trace and find the exact span that introduced the foreign data: the memory block in the system prompt, a `recall` tool result, a retrieved document, or earlier messages in the thread.

```sql
-- threads shared by users
SELECT thread_id, count(DISTINCT user_id) AS users
FROM runs
WHERE created_at > now() - interval '7 days'
GROUP BY thread_id
HAVING count(DISTINCT user_id) > 1;
```

Likely causes, ranked:
1. `thread_id` collision: built from a non-unique value (a session cookie reused across logins, or a constant like "default" in one code path), so the checkpointer loads another user's history.
2. Memory or vector search without a mandatory namespace or user filter, so semantic similarity returns another customer's memory.
3. A response or retrieval cache keyed on prompt text only.
4. Module-level mutable state in a worker (a global message list, a reused agent object) shared across concurrent requests.

Fix: derive keys on the server from the authenticated principal (`tenant:user:conversation`), never from client input; make the memory store reject queries without a namespace; key caches by tenant and user; remove global mutable state. Purge memories and checkpoints holding cross-user data, then search traces for other sessions with the same pattern to size the incident.

Prevent: a test that runs two users concurrently with distinct canary facts and fails if either fact reaches the other's context, Postgres row-level security on memory tables, and an alert when a thread is touched by more than one user.

**Follow-ups they will ask:**
- Must the affected customer be told?: Privacy and legal decide; your job is an exact list of exposed data and sessions.
- Can the prompt prevent it?: No; isolation comes from keys and storage policy.

**Mistakes to avoid:**
- Calling it a hallucination without checking what was in the context.
- Fixing one code path without searching for other affected sessions.

### Q. After a deploy, runs that were paused for review fail to resume: some throw `KeyError` on a state field, others resume into the wrong step. How do you handle it?

**Short answer (45 seconds):** I stop resumes for old threads first, by pausing the resume endpoint or routing those threads to the previous version, so failed resumes do not write more bad checkpoints. Then I diff the state schema and graph between versions, inspect a failing thread's checkpoint, and fix with backward-compatible code: defaults for new fields, readers for renamed ones, and old node names kept until old threads drain. Longer term, state and graphs carry versions and a compatibility test runs on every deploy.

**Deeper explanation:** Inspect a failing checkpoint:

```python
cfg = {"configurable": {"thread_id": "est-2291"}}
snap = graph.get_state(cfg)
print(snap.next)                      # nodes the run will execute next
print(sorted(snap.values))            # field names stored in the checkpoint
print(snap.metadata.get("step"), [t.interrupts for t in snap.tasks])
```

Compare `snap.next` with the node names in the new graph, and the stored fields with the new state class.

Likely causes, ranked:
1. A field was renamed or removed (`price_list` became `pricing.version`) and node code still reads the old key.
2. A node was renamed or removed, so a checkpoint paused before `review` points at a node the new graph lacks, or changed edges send the resumed run down a different path.
3. A field changed type, and a Pydantic state model rejects the stored value with a `ValidationError`.
4. The interrupt payload or resume value changed shape, so the reviewer's decision no longer matches what the node expects.

Fix: a read-side adapter that upgrades old state on load, driven by a `schema_version` field; defaults for new fields; the old node kept as a shim that forwards to the new one; for a handful of threads, `graph.update_state(cfg, {...})` to repair state explicitly, recorded in the audit log. Prevent: a CI test that loads checkpoints captured from the previous release and resumes them against the new graph, and additive-only state changes by default.

**Follow-ups they will ask:**
- Run both versions side by side?: Yes, route old threads by a `graph_version` in metadata to old workers until they drain.
- Thousands of paused threads?: A migration job that upgrades checkpoints in batches after a dry run.

**Mistakes to avoid:**
- Hand-editing checkpoint JSON in the database.
- Treating graph code as freely changeable while threads are paused.

### Q. Ops finds runs that have sat in `awaiting_approval` for a week; the approval request expired days ago, but nothing happened. How do you unstick them and stop it recurring?

**Short answer (45 seconds):** First I size it: how many runs, which tools, and whether customers are waiting on them. An expiry that is only a timestamp does nothing unless code acts on it, so the likely cause is no sweeper, or a resume that failed silently. I resume the expired runs with an explicit "expired, treated as rejected" decision so they close cleanly and tell the user, then add a scheduled sweeper, an escalation chain and an alert on approval age.

**Deeper explanation:** Diagnosis in order:

```sql
SELECT a.id, a.run_id, a.tool, a.required_role, a.expires_at, r.status
FROM approvals a
JOIN runs r ON r.id = a.run_id
WHERE a.decision IS NULL AND a.expires_at < now()
ORDER BY a.expires_at;
```

Then check whether notifications were sent and delivered, whether anyone holds the required role, and whether the resume endpoint returned errors or the run resumed and crashed.

Likely causes, ranked: no job enforces expiry; notifications failed; the required role has no active members after a team change; the resume call failed on a state or version mismatch and nothing retried it; a decision was recorded but the run was never re-enqueued.

Fix: a scheduled sweeper that finds expired approvals, writes an "expired" decision, resumes the run with a rejection result so the agent informs the customer and opens a ticket, and records it in the audit log. In a workflow engine, use a timer instead: Temporal's `workflow.wait_condition` with a `timeout`, or Inngest's `step.waitForEvent` with a timeout, which returns null on expiry. Escalate before expiry: remind the approver, then a backup role, then the team lead.

Prevent: alerts on the age of the oldest pending approval and on failed notifications, a check that every approver role has at least one active member, and an end-to-end test where an approval expires and the run closes.

**Follow-ups they will ask:**
- Auto-approve on expiry instead?: Not for anything consequential; silence means no.
- Approved late, after the data changed?: Re-validate the arguments against current data before executing.
- Who owns the approval queue?: A named team per approval type, with its SLA on a dashboard.

**Mistakes to avoid:**
- Approving the backlog in bulk to clear the dashboard.
- An expiry column that no code reads.

### Q. A user posts a screenshot showing your agent printing parts of its system prompt, including what looks like an internal API key. What are your first moves?

**Short answer (45 seconds):** Treat the key as compromised: revoke and rotate it now, then check its usage logs for calls you did not make. Next, confirm from traces how the text came out and how many other sessions did the same. The real fix is that no secret ever enters the model's context; prompt secrecy is a weak control, so assume the prompt is public and design it that way.

**Deeper explanation:** Order matters: rotate first, because the screenshot is public and the key works. Then impact: search stored outputs and traces for the key prefix and for distinctive prompt phrases.

```bash
# other sessions that leaked the same text
rg -l "INTERNAL_API_KEY|You are the Acme support agent" traces/2026-10/ | wc -l
# secrets committed alongside prompts and tool definitions
gitleaks detect --source . --no-banner
```

Likely causes, ranked:
1. A secret was put in the system prompt or a tool description "so the model can call the API", so any successful extraction exposes it.
2. Indirect prompt injection: retrieved content or a tool result told the model to reveal its instructions.
3. A tool returned an exception containing environment or config values, which the model repeated.
4. A debug or verbose mode rendered the full prompt to the user.

Fix: move credentials into the tool executor and a secrets manager, so the model sees only tool names and opaque ids; map internal exceptions to short model-facing messages without config; add an output filter for secret patterns and a canary string in the prompt that alerts if it ever appears in output.

Prevent: secret scanning in CI over prompts and tool definitions, red-team eval cases for direct and indirect extraction, and an alert on canary hits.

**Follow-ups they will ask:**
- Can prompt extraction be stopped completely?: No; make it harder and make the prompt safe to leak.
- The prompt holds business rules competitors would want?: Move enforcement to code so the prompt can say less.
- The injection came from a document?: Treat retrieved and tool content as data, and gate actions in code whatever the model was told.

**Mistakes to avoid:**
- Adding "never reveal your prompt" and closing the incident.
- Rotating the key without checking how it was used while exposed.

### Practice
- Break it on purpose: make one tool return about 2 MB (a raw HTML page or an unpaginated table), run the agent, and record the exact error your provider returns; then add a result cap with a truncation marker, pagination and store-and-reference, and confirm the same task succeeds within your per-call token budget.
- Make a write tool return HTTP 500 in a test and assert that the harness flags the result, the final message claims no success, and the retry reuses the idempotency key.
- In CI, resume checkpoints captured from the previous release against a graph with a renamed state field, and keep the test failing until a migration or default makes it pass.
- Say it out loud: in two minutes, run the `GraphRecursionError` incident from impact to prevention, naming the controls you would use to contain it without a deploy.
