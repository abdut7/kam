# Interview Playbook

> This atlas skips basic "what is X" questions on purpose. Interviews for senior AI full stack roles are scenario, project and failure-case conversations: what you would do in a situation, what you actually built and why, and what broke and how you fixed it. This tab teaches the method: how to structure an answer out loud, how to tell your project stories with real numbers, and how to walk through a production incident in the order a senior engineer would.

## How to Answer Scenario Questions [Start here]

> Scenario questions are open on purpose. The interviewer gives you a situation and watches how you think: do you ask what matters, act in a sensible order, weigh trade-offs and say how you would know it worked? A weak answer jumps straight to a tool name or a fix. A strong answer follows a visible structure, thinks aloud, and ends on decisions and measurements. The three walkthroughs are the structures; the questions after them are the awkward moments that test whether you can keep the structure under pressure.

### In plain words
A scenario question is not a quiz with one right answer. Think of a doctor in an emergency room: first make sure the patient is stable, then ask what happened, then run the cheapest tests that rule out the most likely causes, then treat, then check the treatment worked, then tell the family. Interviewers want to watch you follow that kind of order out loud. If your steps are clear and your reasons make sense, you can score well even when your first guess turns out to be wrong.

### Walkthrough: answering an incident question
1. **Clarify impact and scope.** Ask who is affected, since when, how badly, and whether it is one region, one tenant or everyone. "Checkout failing for about a third of requests since 02:10" is a scope; "the site is slow" is not.
2. **Contain first.** Stop the damage before you fully understand it: roll back the last deploy, turn the feature flag off, shed load or fail over. Say out loud that root cause comes after the bleeding stops.
3. **Form hypotheses from the signals.** Read what you have (the error text, the shape of the metric, when it started, what changed) and name the two or three causes it points to. A step change at deploy time points at the deploy; a slow climb points at a leak or a growing queue.
4. **Test them in order of likelihood and cost.** Check the most likely and cheapest hypothesis first, a dashboard or a log query before a heap dump. Name the exact check, such as `kubectl rollout history` or `EXPLAIN ANALYZE`.
5. **Fix.** Apply the smallest change that removes the cause, and say whether it is a mitigation (restart, scale out) or the real fix (code, index, config).
6. **Verify.** Point to the metric that proves it worked: error rate back to baseline, queue lag draining, the user's report reproduced and now passing.
7. **Prevent.** Name the alert, test, guardrail or runbook that stops a repeat or catches it sooner, and who owns it.
8. **Communicate.** Throughout: an incident channel, stakeholder updates on a fixed cadence, and a blameless post-mortem afterwards. Interviewers listen for this step because weak candidates forget it.

### Walkthrough: answering a design or project question
1. **Requirements and constraints.** Ask who the users are, the two or three core actions, and the non-functional needs: latency, scale, consistency, compliance, budget and team size. Write them down and say which ones you are assuming.
2. **Estimates.** Do quick numbers: users, requests per second at peak, data size per year, and for LLM features tokens per request and cost per day. The numbers decide whether you need a cache, a queue or sharding at all.
3. **High-level design.** Draw the boxes on the main path end to end: client, API, services, data stores, queues, model calls. Walk one request through them before adding detail.
4. **The two decisions that matter most.** Pick the decisions with the biggest consequences, such as sync versus async processing, which database, or RAG versus fine-tuning, and give the options, the trade-off and your choice. Depth on two beats a shallow pass over ten.
5. **Failure modes.** Say what happens when each dependency is slow or down, when traffic is ten times normal, and when the LLM returns garbage. Give the guard for each: timeout, retry with backoff, fallback, idempotency, human review.
6. **What you would measure.** Name the indicators: p95 latency, error rate, queue lag, cost per request, answer quality score, and the business metric the feature exists for.
7. **How you would ship it in phases.** An MVP that proves the core path, then scale and hardening, then the nice-to-haves. Mention the feature flag or canary that makes each phase safe to release.

### Walkthrough: answering a behavioral or ownership question
1. **Pick one specific story.** A real situation with a project name and a stake, not a summary of your habits. Prepare stories for conflict, failure, ownership, influence without authority and a hard deadline.
2. **Situation.** Two sentences of context: the product, the team, what was at risk. Stop there, because long setups lose the room.
3. **Task.** What you personally were responsible for, and what success meant.
4. **Action.** The bulk of the answer, in first person: "I proposed", "I wrote", "I called the client". Say "we" only for what the team did, and make clear which part was yours.
5. **Result.** Numbers where you have them: time saved, errors cut, latency, revenue. Without a number, give the observable outcome and how it was measured.
6. **The lesson.** One sentence on what you learned and how it changed the way you work now.
7. **What you would do differently.** A concrete change, not "communicate more". This is the part that shows seniority, because it proves you review your own decisions.

### Concepts you must understand
- Interviewers score five things: structure (a visible plan), judgment (choosing what matters), trade-offs (what each option costs), ownership (driving it to done, including rollback and communication) and communication (the listener can follow you).
- Think aloud: a silent minute looks like being stuck, while "I am ruling out the database first because its latency is flat" earns credit even if the guess is wrong.
- Handle "I don't know" in one sentence, then reason from what you do know and say how you would find out; a bluff is exposed by the second follow-up.
- Time-box a 45-minute design round: roughly 5 minutes on requirements, 5 on estimates, 15 on the high-level design, 15 on deep dives and failure modes, and the rest for questions, and say out loud when you move on.
- Clarifying questions are part of the answer: two or three sharp ones (scale, users, what must never go wrong) beat ten generic ones, and when the interviewer says "you decide", state an assumption and continue.
- Signpost: announce the structure before you fill it ("three parts: contain, diagnose, prevent") and say where you are ("that was containment, now diagnosis") so the interviewer can follow and interrupt at the right point.
- End every answer with what you would measure or monitor, because that is how a senior engineer knows a decision worked.
- Use your own projects as evidence: "in CADBEATER this went through a human approval gate" is worth more than a textbook answer, as long as every detail is true.

### Q. The interviewer gives you an error you have never seen in a stack you know. How do you work through it out loud?
**Short answer (45 seconds):** I read the error out loud, word by word, and classify it: which layer raised it (driver, framework, database, operating system), whether it comes from my code or a dependency, and whether it is constant or intermittent. Then I name my top two hypotheses, the cheapest check for each, and what result would change my mind. The interviewer is scoring the method, not whether I recognize the message.

**Deeper explanation:** Suppose they show a Node.js service log with `ERROR: could not serialize access due to concurrent update` from Postgres. Narrate it like this:

```text
1. Read: "serialize", "concurrent update" -> a transaction conflict raised by Postgres, not Node.
2. Context: this appears under REPEATABLE READ or SERIALIZABLE, so does our code or ORM set one?
3. Pattern: only under load? Two requests updating the same row at once would fit.
4. Check: search logs by row ID and time; look in pg_stat_activity for long transactions.
5. Direction: retry the whole transaction on SQLSTATE 40001, and keep transactions short.
```

Even when the text is new, each word is a clue, and "my guess is X, here is how I would confirm it" scores. Name the tools you would really use: the first stack frame in your own code, the request ID in the logs, the docs or source of the library that threw it, and a minimal reproduction. Say when you would stop guessing and look up the error code; knowing when to search is part of the skill.

**Follow-ups they will ask:**
- What if it only happens in production?: Compare config, data volume, concurrency and versions, and add logging around the failing call instead of guessing.
- What if the stack trace points only into library code?: Walk up the trace to the first frame in your code; that is the call you control.
- What if your first hypothesis is wrong?: Say so, cross it off and move to the next one; changing your mind on evidence is a plus.

**Mistakes to avoid:**
- Going silent while you think, or pretending to recognize the error.
- Jumping to a fix ("add a retry") without saying what the error means.
- Listing ten causes with no order and no way to check them.

### Q. You are 20 minutes into a system design round and realize your first design will not scale. What do you do?
**Short answer (45 seconds):** I say it immediately: "I want to revisit the write path; at the peak we estimated, a single database primary is my risk." Then I show the number that breaks, keep the parts that still hold, and evolve the design instead of restarting it. Catching your own flaw is a strong signal, as long as you do it calmly and quickly.

**Deeper explanation:** Use a four-step pivot:
1. Name the bottleneck with the estimate you already made, so the change is driven by numbers, not panic.
2. List two or three options: put a queue in front and batch writes, partition by a key, move hot data to Redis, or relax a consistency requirement.
3. Choose one, give its trade-off, and redraw only the boxes it touches.
4. Say how you would confirm it: a load test against the peak estimate and the metric you would watch.

For a chat product, it might sound like this:

```text
v1: client -> API -> Postgres (insert message) -> API fans out to recipients
    breaks at peak: every message is a synchronous write plus fan-out in the request
v2: client -> API -> Kafka topic (partition key: conversation_id)
                       -> writer consumers -> Postgres (batched inserts)
                       -> fan-out consumers -> WebSocket gateway
    keeps: API, auth, Postgres schema. gains: ordering per conversation, absorbed spikes
```

The pivot also gives the interviewer a natural deep dive (partitioning, ordering, consumer lag), which is usually where the senior points are.

**Follow-ups they will ask:**
- Why did you not see it earlier?: I built the core path first on purpose; the estimates exposed the limit, which is what they are for.
- Is v2 overkill for launch?: Ship v1 behind an interface and switch when a metric such as write latency or queue depth crosses a set threshold.
- What do you lose?: Read-your-own-write may lag; an optimistic UI hides it for the sender.

**Mistakes to avoid:**
- Hiding the flaw and hoping the interviewer does not notice.
- Erasing everything and starting over, which wastes time and the good parts.
- Over-correcting into a design with five new systems the problem does not need.

### Q. An interviewer keeps adding constraints to your design. How do you respond without losing the thread?
**Short answer (45 seconds):** I treat each constraint as a requirement change: restate it, say what it changes and what it does not, and update a running requirements list. If two constraints conflict, I say so and ask which matters more. That is what they are testing: whether I can absorb change and keep the structure.

**Deeper explanation:** Keep a numbered requirements list visible in a corner of the whiteboard or shared doc. For each new constraint, use the same four beats:
1. Restate: "So customer data must stay in the UAE."
2. Impact: "That limits where the vector store and the LLM can run: in-region hosting or a self-hosted model. The API and frontend do not change."
3. Adjust the smallest part of the design that the constraint touches.
4. Return: "Back to the retrieval path, where we were."

A typical sequence on a RAG assistant shows that each constraint lands on a different box:

| New constraint | Box it touches | Likely change |
|---|---|---|
| Data must stay in-country | Model and vector store | In-region provider or self-hosted model |
| p95 under one second | Generation | Streaming, caching, a smaller model for simple queries |
| Halve the cost | Model calls | Routing to cheaper models, response caching, shorter prompts |
| Must work offline | Client | On-device model or cached answers, a sync queue |

When constraints conflict, such as sub-second answers from the largest model on every request, name the trade-off and propose a split: route easy queries to a small fast model and hard ones to the large model, with a measured quality bar for both.

**Follow-ups they will ask:**
- What if a constraint breaks your core design?: Say it plainly and redesign only that path; reuse the rest.
- What if the constraint seems unrealistic?: Ask what is behind it; the real need is often narrower, such as residency only for stored data.
- How do you keep track under pressure?: Refer to requirements by number and tick them off as you cover them.

**Mistakes to avoid:**
- Restarting the design for every new constraint.
- Agreeing to everything without saying what it costs.
- Getting defensive, as if the constraint were criticism.

### Q. You are asked about a technology you have only read about. How do you answer honestly and still score?
**Short answer (45 seconds):** I state my level in one sentence ("I have read about it and tried it in a toy project, not run it in production"), bridge to the closest thing I have run, reason about how it should work and where it could fail, and say how I would validate it before betting a project on it. Honesty plus reasoning scores; a bluff is caught on the second follow-up.

**Deeper explanation:** Use a three-part script: level, bridge, reason.

```text
Level:  "I have not run Flink in production."
Bridge: "I have run Kafka-based event processing in Node.js microservices,
         so I know consumer groups, lag and redelivery from operating them."
Reason: "For stateful aggregation the hard parts are state, exactly-once
         and recovery. My understanding is Flink handles recovery with
         checkpoints of operator state; I would verify how it behaves on
         rebalance and what it costs to run before choosing it."
```

The bridge must be true and specific, so pick it from your own work: Kafka and RabbitMQ from the Samsung.com microservices, LangGraph checkpointers when asked about a workflow engine, Qdrant when asked about a different vector database. Knowing why a technology exists, the problem it solves and what people did before it, lets you reason about it even without hands-on time. End with how you would de-risk it: a short spike on the riskiest part, reading its known failure modes, and asking someone who has operated it.

**Follow-ups they will ask:**
- Then why should we trust you with it?: Point to a time you learned a tool quickly and shipped with it [your story: tool, how long, what you shipped].
- What would your proof of concept test first?: The failure mode most likely to hurt this use case, plus the operating cost.
- How does it compare with what you used?: Give an honest comparison on two or three axes, and say which ones you are unsure about.

**Mistakes to avoid:**
- Claiming production experience you do not have.
- Saying "I don't know" and stopping there.
- Reciting general facts without connecting them to the interviewer's problem.

### Q. How do you turn a vague prompt like "design a chatbot for our bank" into a structured answer in the first five minutes?
**Short answer (45 seconds):** I spend the first two minutes on questions that change the design: who the users are, what the bot is allowed to do (answer questions or act on accounts), which channels and languages, and what must never go wrong. Then I state assumptions, do rough numbers and draw the main path. By minute five the interviewer should see a scoped problem and a plan for the rest of the round.

**Deeper explanation:** A five-minute plan:

```text
0-2 min  Ask: customers or staff? answers only, or actions like card freeze and transfers?
         channels (app, web, WhatsApp)? languages (for the UAE, Arabic and English)?
         data residency and audit rules? handoff to human agents?
2-3 min  Assume: retail app users, read-only account answers plus card freeze,
         Arabic and English, data stays in-country, human handoff available.
3-4 min  Estimate: users x chats per day x turns -> requests per second, tokens per day, cost per day.
4-5 min  Draw: app -> API gateway (auth, rate limit) -> chat orchestrator
         -> RAG over versioned policy and fee documents
         -> account tools that run with the user's own permissions
         -> guardrails (PII redaction, refusal rules) -> human handoff -> audit log
```

Then name the two decisions that matter most. First, what the model may do: anything that changes state or moves money needs step-up authentication and explicit user confirmation, and is executed by deterministic code with validated arguments, never by free text. Second, grounding: answers about products and fees come only from retrieved, versioned documents with citations, and when retrieval finds nothing the bot says so and offers a human.

**Follow-ups they will ask:**
- What if they want transfers in version one?: A confirmation step that repeats amount and payee, step-up authentication, limits, and server-side validation of every tool argument.
- How do you handle prompt injection?: Treat user text and retrieved documents as data, take permissions from the session rather than the prompt, and filter outputs.
- How do you measure success?: Containment rate, escalation rate, satisfaction scores, and a wrong-answer rate from sampled human review.

**Mistakes to avoid:**
- Opening with "I would use model X and framework Y".
- Asking fifteen questions and drawing nothing.
- Ignoring compliance and audit in a banking context.

### Q. The interviewer challenges a decision you made in a past project. How do you defend or revise it?
**Short answer (45 seconds):** I do not get defensive. I restate their concern to show I heard it, give the constraints at the time, the options we considered and why we chose this one, and then say honestly whether I would still choose it today. Defending with evidence or revising with a reason both score; stubbornness and instant surrender do not.

**Deeper explanation:** Use four beats: acknowledge, context, evidence, verdict. Take a likely challenge: "Why Redis Streams for CADBEATER's event-driven services instead of Kafka?"

```text
Acknowledge: "Fair question; Kafka is the default for high-volume event logs."
Context:     "Our constraints were [your detail: message volume, team size,
              whether Redis was already in the stack]."
Evidence:    "Redis Streams gave us consumer groups and acknowledgements
              with [your reason: less to operate, latency, cost]."
Trade-off:   "We accepted weaker retention and replay than Kafka, because
              [your reason]."
Verdict:     "At [your number: message volume or retention need] I would
              move the long-lived event log to Kafka."
```

The trade-off line is true of the technologies: Redis Streams live in memory and are usually trimmed by length, while Kafka keeps a disk-based log with configurable retention, so replay over long periods is Kafka's strength. If the challenge is right, say so: "That was a weak point. What I would change is..." Separate decisions that were sound given what you knew from ones that were simply wrong; the first kind you defend, the second kind you own.

**Follow-ups they will ask:**
- What evidence did you have at the time?: [your detail: a load test, a cost estimate or a prototype].
- Who made the call?: Be exact about whether it was your decision, a joint one, or one you inherited.
- What would make you change it?: Name the metric and the threshold.

**Mistakes to avoid:**
- "That is how the company did it", which shows no judgment.
- Arguing with the interviewer instead of reasoning with them.
- Abandoning a sound decision at the first push.

### Practice
- Record yourself answering one incident and one design question against a timer, then play it back and mark every silence longer than ten seconds and every walkthrough step you skipped.
- Write the three walkthroughs on one card and use them as the skeleton for five scenario questions from the other tracks, out loud, one per day.
- Ask a friend to play interviewer and add a new constraint every three minutes while you design; practice restate, impact, adjust, return.
- Say it out loud: "I have not run that in production; the closest thing I have run is..." for three technologies on a target job description that you have only read about.

## Project Deep-Dive Questions [Core]

> Interviewers pick one project from your history and dig until they find the edge of what you know. They are checking three things: that you did what you claim, that you understand why the system was built that way, and that you can talk about trade-offs and failures, not only features. A weak answer recites the tech stack. A strong one tells a story with a business problem, a hard technical problem, a decision with its trade-off, a measured result and an honest regret. Where an answer below needs a number or detail only you know, it shows a fill-in prompt in square brackets; fill every one from your notes before the interview and never improvise a number in the room.

### In plain words
A project deep dive is like showing someone around a house you built. Anyone can list the materials. A real builder can say why the beam is where it is, what happens in a storm, what went wrong during the build and what they would do differently next time. Interviewers ask about your projects to find out whether you were the builder or just lived in the house.

### Concepts you must understand
- The deep-dive template, in this order: context (the business problem and who used it), your role (what you owned versus the team), architecture (one request through the main boxes), the hardest problem, decisions and trade-offs, results with numbers, and what you would change.
- Lead with the business problem, not the stack: "estimating took four hours per project" lands harder than "we used LangGraph".
- Every number must be one you can explain: how it was measured, over what period and against what baseline. If you do not have it, say what you would measure instead of guessing.
- Separate "I" from "we": say exactly which parts you designed, built, reviewed or only used.
- Prepare two versions of each story: a two-minute version that covers the whole template, and a five-minute version with one diagram and two decisions in depth.
- Expect the interviewer to pull on every term you say, so only name a technique (Reflexion, continuous batching, Onion Architecture) if you can explain how you used it.
- Have one failure or regret ready per project; it is the most common follow-up and the one candidates prepare least.
- Map each project to the question types it can answer, so a scenario question can be backed with "at Samsung.com we..." evidence:

| Project | What it was | Topics it proves |
|---|---|---|
| CADBEATER (Voizzit, Technical Lead) | AI estimator for fenestration and facade projects: cost estimates, BOQ, BOM and CAD drawings from requirements, joinery details or floor plans; estimating cut from four hours to ten minutes | LangGraph multi-agent design (ReAct, Reflexion, Plan-and-Execute), MCP tools, agentic RAG on Qdrant, agent memory and context compression, LoRA/PEFT fine-tuning of a vision-language model, vLLM serving with quantization and constrained decoding, model routing and caching, Langfuse evals, RBAC and human approval, SSE and Redis Streams, leading a team with an AI-driven SDLC |
| VData (Voizzit, Senior Backend Engineer) | Distributed voter-data platform on NestJS with Clean (Onion) Architecture and TypeORM over PostgreSQL, on AWS | Near-instant search over 30 million records, horizontal and vertical scaling, layered architecture, ELK analytics, CI/CD, automated API tests |
| Samsung.com (Samsung SDS) | Node.js microservices for global eCommerce, plus logistics and user-interaction APIs | High-traffic sale events and autoscaling, Kafka and RabbitMQ event processing, PostgreSQL transactions, secure APIs, Elasticsearch logging for end-to-end traceability |
| Solargraf (Infosys) | Solar-design SaaS with 3D design and financial modules | High-availability microservices, API gateway, gRPC between services, Sequelize on PostgreSQL, architecture reviews with product teams |
| EMTAB (Kimball Electronics) | Industry 4.0 IoT predictive-maintenance platform: alerting, visualization and data acquisition modules | Real-time sensor pipelines, ML anomaly detection in a live data path, alerting, MongoDB and MySQL, Playwright automation |
| TRAACS (Nucore) | Back-office accounting SaaS for travel agencies | ERP accounting engine and business rules, microservice APIs, PostgreSQL and MongoDB, correctness of financial data |
| TechBuddy LMS (Voizzit) | Admin CMS, student web and React Native TV apps on NestJS and PostgreSQL | Adding an AI feature (generated quizzes) to a product, offline content export, secure authentication, rate limiting, several client apps on one backend |
| AutoFleet (Voizzit) | Car rental booking and ERP platform: booking flow, fleet, reservations, CRM and HRM | Booking and reservation flows, a Flutter app for Android, iOS and web, Play Store and App Store releases, Node.js and React on MongoDB and AWS, Playwright automation for third-party integrations |

### Q. Walk me through CADBEATER's architecture and the hardest problem you solved.
**Short answer (45 seconds):** CADBEATER is an AI estimator for fenestration and facade projects: from requirements, joinery details or floor plans it produces cost estimates, bills of quantities, bills of materials and CAD drawings, and it cut manual estimating from four hours to ten minutes. I led it as Technical Lead from requirements to production. I would give one pass through the architecture, then tell one hard problem in depth.

**Deeper explanation:** Walk one estimate through the boxes:

```text
React CAD frontend (Redux Toolkit, TanStack Query, Three.js)
  -> FastAPI services (RBAC, team-scoped access) -> Redis Streams (events)
  -> LangGraph agents:
       Reflexion: extract requirements from drawings, critique, correct
       Plan-and-Execute: build the estimate, stop for human review
       ReAct: contextual Q&A
     tools through MCP, agentic RAG on Qdrant, memory via checkpointers
  -> model routing: OpenAI, Anthropic, OpenRouter APIs | fine-tuned VLM on vLLM
     (GPU-isolated workers on RunPod) | deterministic code
  -> MongoDB data layer; tokens stream back over SSE; Langfuse traces every step
```

Then pick the hardest problem, one you can defend through three follow-ups. Candidates that fit what the system contains: reading vision-heavy drawings reliably (why extraction got a Reflexion loop and a fine-tuned model), keeping long agent runs resumable across a human review (checkpointers), or getting a valid structured estimate every time (constrained decoding against JSON schemas). Tell it as a short story: the first symptom [your detail], what you tried that did not work [your detail], what did, and the number that proved it [your number: accuracy or failure rate before and after].

**Follow-ups they will ask:**
- Why SSE rather than WebSocket?: [your reason]; the usual argument is that token streaming is one-way, and SSE runs over plain HTTP with built-in reconnect.
- Why Redis Streams rather than Kafka?: [your reason: volume, team size, Redis already in the stack].
- Why isolate the GPU workers?: [your detail]; the general reason is that slow GPU jobs must not block or starve the API.
- How much load does it carry?: [your number: estimates or users per day].

**Mistakes to avoid:**
- Reciting every technology before the interviewer knows what the product does.
- Picking a "hardest problem" you cannot go three questions deep on.

### Q. Why did CADBEATER use three agent patterns (ReAct, Reflexion, Plan-and-Execute) instead of one agent?
**Short answer (45 seconds):** Because the three jobs have different shapes. Contextual Q&A is open-ended and short, so a ReAct loop that reasons and calls tools fits. Requirement extraction from drawings is vision-heavy and error-prone but checkable, so a Reflexion agent critiques and corrects its own output. Estimate generation is a long, structured job that ends in mandatory human review, so Plan-and-Execute gives a visible plan and controlled steps. One agent would have been simpler to build and weaker at all three.

**Deeper explanation:** Frame it as matching control to risk:

| Task | Pattern | Why it fits | Cost you accept |
|---|---|---|---|
| Contextual Q&A | ReAct | Unknown number of lookups, low stakes per answer | Less predictable step count |
| Requirement extraction | Reflexion | Output can be checked against the drawing and retried | Extra model calls per critique loop |
| Estimate generation | Plan-and-Execute | Known structure, reviewable plan, a human signs off | Less flexible when the plan is wrong |

Own the trade-offs. Three patterns means three sets of prompts, evals and failure modes, so each needs its own test set in the evaluation pipeline. Reflexion loops cost tokens and latency, so they need a cap [your number: maximum critique iterations] and a stop condition. Plan-and-Execute needs a way to replan when a step fails [your detail: how replanning worked]. Be ready to say how the agents connect [your detail: one LangGraph graph with subgraphs, or separate graphs behind a router] and how state survives the human review: LangGraph checkpointers persist the run so it resumes after approval.

**Follow-ups they will ask:**
- Why not one ReAct agent with every tool?: Tool choice gets less reliable as the tool list and context grow, and there is no natural review point before an estimate leaves the system.
- How did you prove Reflexion helped?: [your number: extraction score with and without the critique loop on the same test set].
- What stops an endless loop?: An iteration cap, LangGraph's recursion limit, and a score threshold that ends the loop.

**Mistakes to avoid:**
- Using pattern names as buzzwords without the task each one served.
- Implying the agents act unchecked when estimates go through mandatory human review.

### Q. How did you decide to fine-tune a vision-language model instead of only prompting and RAG, and how did you evaluate it?
**Short answer (45 seconds):** I treat fine-tuning as the last rung of a ladder: prompting, then few-shot examples, then RAG, then fine-tuning when the gap is a skill or output format the model lacks, not missing facts. For CADBEATER the skill was turning drawings and joinery details into structured estimates, so we fine-tuned a multimodal vision-language model with LoRA/PEFT on a three-stage curriculum, and every checkpoint had to pass the evaluation pipeline before release.

**Deeper explanation:** Tell the decision with evidence:
1. Baseline: what prompted API models got wrong on your drawings [your detail: the typical failure] and their score [your number: baseline on the test set].
2. Why RAG was not enough: retrieval adds knowledge, but it does not teach a model to read a drawing it misreads. RAG on Qdrant stayed in the system for other jobs [your detail: what it retrieves].
3. Training plan: three stages, vision extraction first, then pricing logic, then end-to-end drawing-to-estimate, so the model learns to see before it learns to price. Data: [your number: examples per stage] and [your detail: how labels were produced].
4. Why LoRA/PEFT: small trainable adapters, cheaper GPUs, and checkpoints that are easy to version and roll back in a Hugging Face model registry.
5. Serving: vLLM on RunPod GPUs with 4-bit/8-bit quantization, and structured outputs through constrained decoding so the result always parses.

Evaluation: a held-out test set the model never trained on, scored the way you actually scored it [your detail: for example field-level match on extracted items and estimate error against a human estimator], regression checks against the previous checkpoint, and the quantized model scored separately, because quantization can cost accuracy. The automated pipeline gated every prompt and model release.

**Follow-ups they will ask:**
- How did you keep test data out of training?: [your detail: split by project rather than by page or image].
- What happens when prices change?: [your detail: whether unit prices come from data, deterministic code or the model]; volatile numbers belong in data, not in weights.
- Would you still fine-tune today?: Re-run the baseline against current API models first; the answer can change.

**Mistakes to avoid:**
- Saying "fine-tuning is more accurate" with no baseline or test set.
- Ignoring GPU serving costs in the decision.

### Q. CADBEATER cut estimating from four hours to ten minutes. How do you know the estimates are good enough, and what happens when they are wrong?
**Short answer (45 seconds):** I separate speed from quality. Four hours to ten minutes is time saved; quality is shown separately by the evaluation pipeline on test projects and, in production, by mandatory human review of every generated estimate before it is used. When an estimate is wrong, the reviewer corrects it, the trace shows which step failed, and the case becomes a new test.

**Deeper explanation:** Answer in three layers:
1. Before release: test datasets with known-good estimates, scoring and regression checks gate every prompt and model change. State the bar [your number: acceptable error against a human estimate] and who set it [your detail: estimators, business owners].
2. In production: the Plan-and-Execute agent's estimate stops at a human approval gate, and audit logs record who approved what. The honest live metric is how much reviewers change [your number: share approved without edits, or average size of edits].
3. When it is wrong: Langfuse traces show whether the error came from extraction, retrieval, pricing logic or the plan. Fix that layer, add the case to the test set, and re-run the gate before shipping.

Be precise about the headline number: whether the ten minutes includes the review step [your detail], and how the four-hour baseline was measured [your detail: timing study or estimator reports]. Interviewers trust a clearly measured number more than a big one.

Consequences shape the design. An under-quote can cost margin and an over-quote can lose the bid, so say which error was more dangerous for your users [your detail] and what the system did about it [your detail: for example flagging uncertain line items for the reviewer].

**Follow-ups they will ask:**
- What if reviewers rubber-stamp?: Track review time and edit rates, and audit a sample of approved estimates with a second estimator.
- What is the accuracy?: Give the number you measured [your number]; if you do not have one, say how you would measure it rather than estimating on the spot.
- Who owns a wrong quote?: [your detail]; the design point is that a named human approves every estimate and the approval is logged.

**Mistakes to avoid:**
- Treating time saved as proof of quality.
- Quoting an accuracy figure you cannot explain.

### Q. How did you make search fast over 30 million records in VData?
**Short answer (45 seconds):** I would start with the query shapes, because "fast search" means different things for exact lookups, name search and filtered lists. VData was a NestJS platform with Clean (Onion) Architecture and TypeORM over PostgreSQL, scaled horizontally and vertically on AWS for near-instant search across 30 million voter records. Then I walk each layer I used, with the latency it bought [your number: p95 latency before and after].

**Deeper explanation:** Structure the answer by layer and fill each with what you actually did:
1. Query shapes: [your detail: exact ID lookups, name prefix or fuzzy search, filters by area, sorting and paging].
2. Indexing: [your detail: which indexes on which columns]. On Postgres, be ready for B-tree versus a GIN index with `pg_trgm` for fuzzy text, composite index column order, and keyset pagination instead of large OFFSET values. Show you verified with plans; an illustrative check:

```sql
-- illustrative table and columns
CREATE INDEX CONCURRENTLY voters_name_trgm ON voters USING gin (full_name gin_trgm_ops);

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, full_name FROM voters
WHERE district_id = 42 AND full_name ILIKE '%rahman%'
LIMIT 50;
```

3. Scaling: horizontal [your detail: more NestJS instances behind a load balancer, read replicas, or both] and vertical [your detail: which instance change and why]. Name the bottleneck before each step.
4. Architecture: with Onion Architecture, search sits behind a repository interface in the infrastructure layer, so query tuning or an engine change does not touch domain code.
5. Proof: the platform had ELK analytics, CI/CD and automated API test suites; say which of them watched latency or caught regressions [your detail].

**Follow-ups they will ask:**
- Why not Elasticsearch or OpenSearch?: [your reason]; the honest trade-off is a second datastore to keep in sync against simpler operations in one database.
- How was the data loaded and kept fresh?: [your detail: bulk import method and update frequency].
- What was the slowest query and how did you fix it?: [your story].

**Mistakes to avoid:**
- Saying "we added indexes" with no query shape, plan or number.
- Claiming a search engine or index type you did not actually use.

### Q. Tell me about running Node.js microservices through a high-traffic sale event at Samsung.
**Short answer (45 seconds):** I would be precise about scope first: I built and operated independently deployable Node.js microservices for Samsung.com global eCommerce, using Kafka and RabbitMQ for event processing and PostgreSQL for transactional data, and those services autoscaled through high-traffic sales events. Then I tell it in phases: how we prepared, what we watched during the event, and what we changed afterwards.

**Deeper explanation:**
1. Before: the expected peak [your number: requests per second or orders per minute against a normal day], load testing [your detail: tool and target], and autoscaling settings [your detail: the metric it scaled on, minimum and maximum instances]. Mention the classic trap: each new instance opens its own PostgreSQL connection pool, so instances times pool size must stay below the database's connection limit [your detail: how you handled it].
2. During: the signals you watched [your detail: dashboards]. Strong ones to name are error rate and p95 latency per service, Kafka consumer lag, RabbitMQ queue depth, database connections and slow queries, and Elasticsearch logs searched by a correlation ID to trace one request across services.
3. Async as a shock absorber: work that did not need to finish inside the user's request went through Kafka or RabbitMQ [your detail: which flows used which], so a spike turned into queue depth that drained instead of timeouts.
4. After: what broke or nearly broke [your story], and the change you made before the next event.

**Follow-ups they will ask:**
- Why both Kafka and RabbitMQ?: [your detail]; the usual split is Kafka for replayable event streams and RabbitMQ for task queues with per-message acknowledgement and flexible routing.
- What if autoscaling reacts too slowly in the first minute of a sale?: Pre-scale before the start time, because reactive scaling always lags a sudden spike.
- How do you avoid processing an event twice?: Idempotent consumers keyed by an event or order ID, because both brokers can redeliver.
- What did you own versus the platform team?: [your detail].

**Mistakes to avoid:**
- Implying you ran all of Samsung.com; name the services that were yours.
- "It autoscaled, so it was fine": the interviewer wants the limits, the signals and the near misses.

### Q. How did you secure an AI product that touches customer data (RBAC, team-scoped retrieval, audit logs, human approval)?
**Short answer (45 seconds):** In CADBEATER security was layered so the model never decides who sees what: role-based access control, role- and team-scoped data access and retrieval, audit logging, and human-in-the-loop approval gates before estimates are used. The principle I state is that permissions come from the authenticated user and are enforced in code, never by the prompt or the model's output.

**Deeper explanation:** Walk the layers in request order and fill in your implementation:
1. Identity and RBAC: [your detail: how users authenticate and how roles are checked in the FastAPI services]. Roles decide which endpoints and actions a user can reach.
2. Team-scoped retrieval: the retrieval tool adds the team filter from the user's session, so the agent cannot widen it even if a prompt asks. In Qdrant that is a payload filter on every query (names illustrative):

```python
from qdrant_client import models

hits = client.query_points(
    collection_name="project_docs",
    query=query_vector,
    query_filter=models.Filter(must=[
        models.FieldCondition(key="team_id", match=models.MatchValue(value=user.team_id)),
    ]),
    limit=8,
).points
```

3. Tools through MCP: [your detail: how a tool call carries the user's identity and role]. A tool that reads or writes data checks the caller's permissions itself.
4. Audit logging: [your detail: what is recorded, for example user, action, retrieved documents, model and approval]. This answers "who saw or approved what" after the fact.
5. Human approval: estimates stop at a gate; LangGraph checkpointers pause the run and resume it after a reviewer approves.
6. Model providers: [your detail: what data goes to external APIs versus the self-hosted model, and any redaction].

**Follow-ups they will ask:**
- What about prompt injection in an uploaded document?: Treat uploaded and retrieved content as data, keep permissions outside the prompt, and require approval for consequential actions.
- How do you test team isolation?: Automated tests that query as team A and assert nothing from team B returns, run on every release.
- What if a user changes teams?: [your detail: how quickly role changes take effect, and any cached roles].

**Mistakes to avoid:**
- Using the system prompt ("only answer about the user's team") as access control.
- Forgetting that embeddings, caches and traces hold customer data too.

### Q. What would you build differently if you restarted CADBEATER today?
**Short answer (45 seconds):** I keep what worked, change two or three things, and give a reason for each that comes from what happened on the project, not from a new trend. Typical candidates are building the evaluation set on day one, starting with the simplest workflow and adding agent loops only where evals prove they help, and setting cost and latency budgets per estimate from the first prototype. I would pick only the changes that are true for me and back each with the event that taught it.

**Deeper explanation:** A strong structure:
1. What I would keep: [your pick: for example the human approval gate, constrained decoding for structured estimates, Langfuse tracing]. Saying what was right shows judgment, not just self-criticism.
2. Change one, with its cause: "We added [your detail] late, and it cost us [your detail: rework, a bug, a slow release]. Today I would do it first."
3. Change two, with its trade-off: for example moving more steps into deterministic code, which is cheaper and testable but less flexible [your detail: which steps].
4. Change three, about the world moving: model options change fast, so re-run the baseline that justified fine-tuning against current API models before the next training round.
5. How I would know the new version is better: [your number: quality score, cost per estimate, time per estimate, before and after].

Topics to choose from, only where they match what you lived through: evaluation data earlier, fewer agent patterns at the start, simpler infrastructure for the first release, contract tests between the agent layer and the FastAPI services, earlier load tests on the GPU inference workers, and clearer ownership of prompts and models across the team.

**Follow-ups they will ask:**
- Would you still use LangGraph?: [your reason]; answer on durable state, checkpointing and human review, not popularity.
- What was the most expensive mistake?: [your story: what it cost and how you caught it].
- What would you buy instead of build?: [your detail]; name the part and the reason.

**Mistakes to avoid:**
- Answering "nothing", which reads as no reflection.
- Proposing a full rewrite in a new framework, or blaming the team.

### Practice
- Fill the deep-dive template on one page each for CADBEATER, VData and Samsung.com, and replace every bracketed prompt with a real number or detail from your notes, commits or dashboards before any interview.
- Record a two-minute and a five-minute version of each project story. Check that the two-minute version contains a number and a decision, and that the five-minute version includes one diagram you can draw from memory.
- Draw CADBEATER's request path from memory in under three minutes, naming every box, then let a friend point at any box and explain it for two minutes.
- Say it out loud: "The hardest problem in this project was X. We tried Y first, it failed because Z, and we fixed it with W, which moved the metric from A to B."

## Production Incident Scenarios [Core]

> Incident questions test whether you act in the right order under pressure. Interviewers want containment before diagnosis, evidence before fixes, and communication throughout. A weak answer starts reading code while users are still failing, or jumps to one favorite cause. A strong answer clarifies impact, stops the damage, ranks hypotheses from the signals, checks them with real commands, fixes, verifies, prevents a repeat, and says who was told what and when.

### In plain words
A production incident is like a kitchen fire. First you turn off the gas and put out the flames, even before you know what caused them. Then you work out why it started, repair the stove, and change the rules so it does not happen again. All the while, you keep telling everyone in the house what is going on. Interviewers want to hear that order, not just the clever diagnosis.

### Concepts you must understand
- Severity levels decide how fast you move and who gets woken up; names and thresholds vary by company, but a common scale looks like this:

| Level | Example | Response |
|---|---|---|
| Sev1 | Full outage, data leak, data loss, payments failing | Page on-call now, name an incident commander, stakeholder updates on a cadence, post-mortem required |
| Sev2 | A major feature down or badly degraded for many users | Page on-call, fix within hours, post-mortem usually |
| Sev3 | Minor bug or degradation with a workaround | Ticket, fix in working hours |

- The first ten minutes: acknowledge the page, confirm the impact is real, declare a severity, open an incident channel, name an incident commander who coordinates rather than debugs, check what changed, then mitigate.
- Mitigate before root cause: rollback, feature flag off, scale out, shed load or fail over. The root cause can wait; customers cannot.
- Communication cadence: post updates on a fixed schedule even when nothing has changed, for example every 30 minutes for a Sev1, with current impact, what is being tried and the time of the next update. Keep the technical channel separate from stakeholder updates.
- Keep a timeline while you work: timestamps of alerts, actions and results. It becomes the skeleton of the post-mortem.
- Blameless post-mortem structure: summary, impact (duration, users, money), timeline, root cause and contributing factors, what went well, what went badly, where you got lucky, and action items each with an owner and a due date.
- Blameless means asking why the system allowed the mistake, not who made it; people report honestly only when they are not punished for it.

### Q. The site is down during a sale and your on-call phone rings at 2 a.m. Walk me through the first 30 minutes.
**Short answer (45 seconds):** In the first five minutes I acknowledge the page, confirm impact on dashboards and synthetic checks, declare a Sev1, open an incident channel and pull in help. Then I look for what changed and mitigate: roll back a recent deploy, scale out, shed load or switch off non-critical features. Root-cause work starts only after orders are flowing again.

**Deeper explanation:**

```text
00-05  Ack. Check error rate, p95 latency, orders per minute, synthetic checkout.
       Declare Sev1, open the channel, page the incident commander and service owners.
05-15  What changed? Deploys, config, feature flags, traffic shape, a dependency.
       Mitigate the most likely cause first.
15-30  Verify on the same graphs, send the first stakeholder update,
       keep the timeline, then begin root-cause work.
```

Likely causes on a sale night, ranked, with the check for each:
1. Capacity ceiling: `kubectl get hpa -n shop` shows replicas pinned at the maximum and `kubectl top pods -n shop` shows CPU saturated. Raise the maximum, add nodes, or shed load with a queue or waiting page.
2. Database connections: logs show `FATAL: sorry, too many clients already` because every new pod opened its own pool. Check `SELECT state, count(*) FROM pg_stat_activity GROUP BY state;`, cut pool sizes or put PgBouncer in front, and end sessions stuck idle in transaction.
3. A deploy: if the spike lines up with a release, `kubectl rollout history deployment/checkout -n shop`, then `kubectl rollout undo deployment/checkout -n shop`.
4. A dependency: payments or search timing out; open the circuit breaker and degrade that feature.
5. Async backlog: Kafka consumer lag climbing, so confirmations and stock updates fall behind; scale consumers.

Prevent: load tests before the sale, scheduled pre-scaling, a connection budget per service, alerts on autoscaling at its maximum and on consumer lag, and a sale-day runbook.

**Follow-ups they will ask:**
- What if only one region is down?: Shift traffic away at DNS or the load balancer, then diagnose that region.
- What if the rollback does not help?: The deploy was not the cause; return to the signals and test the next hypothesis.

**Mistakes to avoid:**
- Reading code at 2 a.m. while checkout is still failing.
- Leaving the business without updates during the sale.

### Q. A customer reports that their data appears in another customer's account.
**Short answer (45 seconds):** I treat it as a Sev1 security incident from the first minute. I confirm it with request IDs and the accounts involved, preserve evidence, contain by switching off the feature and purging caches, and bring in security and legal early because there may be duties to notify. Then I find the mechanism: usually a cache key without the tenant, state shared across requests, or a missing tenant filter.

**Deeper explanation:**
1. Confirm and scope: find the reported request in the logs by time and user, and check which user the server thought it was serving. One pair of accounts or many?
2. Contain: preserve the relevant logs, then turn the feature off or block the endpoint, purge CDN and Redis caches, and invalidate sessions if they could be mixed.

Likely causes, ranked:
- A cached personalized response keyed only by URL. Responses with user data need `Cache-Control: private` or `no-store`, and the user or tenant in any cache key.
- Shared state in a Node.js process, fixed with `req.user` or `AsyncLocalStorage`:

```js
let currentUser; // module scope: shared by every request in this process
app.use(async (req, res, next) => { currentUser = await loadUser(req); next(); });
app.get('/orders', async (req, res) => {
  await audit(req); // another request can overwrite currentUser here
  res.json(await Orders.find({ userId: currentUser.id }));
});
```

- A query or vector search without the tenant filter, or an API trusting a client-sent object ID without an ownership check.
- Pooled connection state: `SET app.tenant_id` for row-level security outlives the request; use `SET LOCAL` inside a transaction.

3. Fix and prove it: a test that logs in as tenant A and asserts nothing from tenant B returns.
4. Notify: security and legal decide on notices; under GDPR, for example, a notifiable breach must reach the regulator within 72 hours where feasible.

**Follow-ups they will ask:**
- How many customers were exposed?: Replay access logs for the bug window and compare the owner of each response with the requester.
- What if it came from an LLM feature?: Check retrieval filters, shared memory and response caches keyed without the user.

**Mistakes to avoid:**
- Fixing it quietly as a normal bug ticket.
- Purging caches or logs before capturing what was exposed.

### Q. An API key for your LLM provider was pushed to a public repository.
**Short answer (45 seconds):** I revoke and rotate the key immediately, before anything else, because bots scan public repositories for keys continuously and I have to assume it is already copied. Then I deploy the new key from the secret manager, check the provider's usage for calls we did not make, and set spend limits. Cleaning the git history comes later and does not make the old key safe; only revocation does.

**Deeper explanation:**
1. Contain: revoke the key in the provider console, create a new one, store it in the secret manager (AWS Secrets Manager, for example) and restart the services that use it.
2. Assess: review the provider's usage for the exposure window: unfamiliar models, odd hours, token spikes. Lower the budget limit and contact the provider if there was misuse.
3. Scope: check the same commit and repository for other secrets, and whether the repo was forked or mirrored.

```bash
git log --all -p -S 'sk-' --format='%h %an %ad'   # commits that added or removed the key
gitleaks detect --source . -v                      # scan the full history for other secrets
```

4. Clean up: rewrite history with `git filter-repo --replace-text` or BFG Repo-Cleaner, force-push, and ask collaborators to re-clone. Treat it as hygiene, since forks and caches may still hold the key.
5. Prevent: GitHub secret scanning with push protection, a pre-commit hook running gitleaks, `.env` in `.gitignore`, separate keys per service and environment with their own spend limits, and short-lived credentials where the platform supports them.
6. Communicate: inform security, and write a blameless post-mortem about why a key could reach a commit at all.

**Follow-ups they will ask:**
- The repo was public for two minutes. Do you still rotate?: Yes; you cannot prove nobody copied it.
- What if rotating breaks a production service?: That is why keys live in a secret manager with a rollout path; accept a few minutes of errors over unbounded spend.
- What if it was a cloud access key instead?: Same order, plus search the cloud audit trail (CloudTrail on AWS) for anything created with it.

**Mistakes to avoid:**
- Deleting the file in a new commit and calling it fixed.
- Rewriting history first and rotating later.

### Q. Your LLM feature's cost tripled overnight.
**Short answer (45 seconds):** First I confirm it in the provider's usage view and our own traces, then contain it with per-user rate limits, a hard budget cap and, if needed, routing the hot path to a cheaper model. Then I break the increase into its parts: more requests, more tokens per request, a pricier model, or fewer cache hits. That breakdown usually points straight at the cause.

**Deeper explanation:** Split the bill before guessing:

```text
cost = requests x tokens per request x price per token, minus cache savings
slice by: model, route or feature, tenant or user, hour, input vs output tokens
```

In a system like CADBEATER, which tracks token cost and latency per estimate in Langfuse, the first question is whether cost per estimate rose or the number of estimates did.

Likely causes, ranked:
1. A deploy changed a prompt, the model or a routing rule. Line the release log up with the start of the curve.
2. A loop: an agent that keeps calling tools, or retries stacked on retries after provider errors. Traces show one run with dozens of LLM calls, and LangGraph runs ending in `GraphRecursionError` are a clue.
3. Cache collapse: a timestamp or user ID added to the start of a system prompt breaks provider prompt caching, or a response-cache key changed. The hit rate drops at the same moment.
4. Context growth: chat history or memory no longer compressed, or retrieval top-k raised, so input tokens per call climb.
5. Abuse: one key or tenant scripting the endpoint. Group cost by user.

Fix the cause, then add guardrails: `max_tokens` on every call, iteration caps on agents, retry budgets, per-tenant quotas, an hourly spend alert, and a release check that fails when tokens per request jump.

**Follow-ups they will ask:**
- What if it is real growth?: Then it is unit economics: cost per user or per estimate against revenue, and levers like routing, caching and smaller models.
- How do you cap spend without breaking users?: Soft limits that degrade to a cheaper model first, hard limits only at the budget ceiling.

**Mistakes to avoid:**
- Switching everything to the cheapest model before knowing the cause.
- Watching only the monthly invoice instead of hourly, per-route data.

### Q. A third-party provider you depend on (payments or an LLM API) has an outage.
**Short answer (45 seconds):** I confirm it is them: their status page, the error codes and timeouts in our logs, and our own synthetic check against their API. Then I contain: stop hammering them with a circuit breaker so we fail fast, switch to a fallback if one exists, and degrade the feature honestly in the UI. For payments the extra rule is never to retry blindly; use idempotency keys and reconcile after recovery.

**Deeper explanation:**
1. Confirm: error rate by dependency on the dashboard. LLM APIs return HTTP 429, 500 or 503 or time out, and Anthropic uses 529 for overloaded; payment providers show timeouts or 5xx responses.
2. Contain with a circuit breaker, so sockets, threads and queue workers are not tied up waiting:

```js
const CircuitBreaker = require('opossum');

const breaker = new CircuitBreaker(callLlm, {
  timeout: 15000,               // fail calls slower than 15 s
  errorThresholdPercentage: 50, // open when half the calls fail
  resetTimeout: 30000,          // try one call again after 30 s
});
breaker.fallback(() => callBackupModel());
```

3. LLM fallbacks: a second provider or a router such as OpenRouter, a self-hosted model for the critical path, cached answers, or a clear "try again shortly" message. Run your evals on the fallback model beforehand, because quality differs.
4. Payments: do not mark an order failed on a timeout, because the charge may have gone through. Keep it pending, retry with the same idempotency key, and reconcile against the provider's webhooks or reports when it recovers. Switch to a backup provider only if it was already integrated and tested.
5. Communicate: status page note, support briefed on what users see, stakeholder updates on the cadence.
6. Prevent: timeouts and capped retries with backoff and jitter on every external call, fallbacks exercised in drills, and a review of the provider's SLA.

**Follow-ups they will ask:**
- What if the provider is slow rather than down?: Slow is worse; tight timeouts plus the breaker turn slowness into fast failures you can handle.
- How do you test the fallback?: Fault injection in staging, and periodically on a small share of production traffic.

**Mistakes to avoid:**
- Unbounded retries that deepen the outage and burn rate limits.
- Treating a payment timeout as a failure and charging the customer twice on retry.

### Q. A deploy went out and error rates doubled, but rollback is blocked by a database migration.
**Short answer (45 seconds):** I contain without the rollback: switch the feature off with a flag, or roll forward a small fix if the cause is clear. Rollback is blocked because the old code no longer matches the new schema, so the options are a roll-forward fix, a compatibility patch to the schema, or a down-migration only if no new data depends on it.

**Deeper explanation:**
1. Contain: flag off, and tell stakeholders why rollback is not available.
2. Diagnose: group errors by type and endpoint. A schema mismatch shows up as `ERROR: column "name" does not exist` from anything still on old code (pods mid-rollout, a worker, another service sharing the database); a logic bug shows up only in new code paths.
3. Choose the fix:

| Option | When | Risk |
|---|---|---|
| Roll forward a hotfix | Cause is clear and small | Shipping under pressure |
| Compatibility patch (re-add the column, a view) | Old code needs the old shape | Temporary schema debt |
| Down-migration, then rollback | No data written that the down step would lose | Data loss if you are wrong |

4. Verify errors per endpoint are back to baseline.
5. Prevent with expand and contract: every migration must work with both the current and the previous release.

```sql
SET lock_timeout = '5s';                       -- fail fast instead of queueing behind long transactions
ALTER TABLE users ADD COLUMN full_name text;   -- expand: old code keeps working
-- deploy code that writes both shapes, backfill in batches, then switch reads
-- a later release, once nothing reads the old column:
ALTER TABLE users DROP COLUMN name;            -- contract
```

Add a CI step that runs the previous release's tests against the new schema.

**Follow-ups they will ask:**
- Why not just run the down-migration?: If new code wrote rows that only fit the new schema, the down step loses or breaks them.
- What if the migration itself is stuck holding a lock?: Find it in `pg_stat_activity`, cancel it with `pg_cancel_backend`, and set `lock_timeout` before DDL in future.

**Mistakes to avoid:**
- Forcing old code onto the new schema, turning a partial outage into a full one.
- Dropping or renaming a column in the release that stops using it.

### Q. Data in production is corrupted by a bug that ran for three days.
**Short answer (45 seconds):** I stop the bug writing more bad data first: flag it off or ship the fix, and pause jobs that spread the damage, such as exports, invoices or emails. Then I scope exactly which records and fields were touched, rebuild the correct values from backups, audit logs or events, and repair with a tested, idempotent script. Restoring the whole database to three days ago is almost never right, because it throws away three days of good writes.

**Deeper explanation:**
1. Contain: disable the code path, pause downstream consumers and scheduled jobs, and brief support.
2. Scope: the window runs from the deploy that introduced the bug to the fix. Find rows the code path wrote in that window (`updated_at`, an audit table, or logs with request IDs) and list the fields it changed.
3. Find a source of truth: point-in-time recovery to a separate instance from just before the bug, an audit log with old values, or a replay of events if the Kafka topic still holds them.

```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier prod-db \
  --target-db-instance-identifier prod-db-before-bug \
  --restore-time 2026-10-29T08:00:00Z
```

4. Decide per record with the product owner: if a user edited a record after the bug, do you keep their edit or the restored value? Write the rule down.
5. Repair: a script that is idempotent, runs as a dry run first and prints a diff, works in batches, and logs each change so it can be reversed.
6. Downstream: rebuild caches, search indexes and derived tables, correct invoices or emails already sent, and notify affected customers.
7. Prevent: nightly invariant checks (totals match line items, no negative stock), alerts on unusual write patterns, a regression test for the bug, and canary releases that compare outputs before full rollout.

**Follow-ups they will ask:**
- What if no backup covers the window?: Rebuild from audit logs, events, provider records such as payment reports, or the source system, and flag what needs manual review.
- Why did nobody notice for three days?: Corruption rarely throws errors, so you need data-quality checks and business-metric alerts, not only error-rate alerts.

**Mistakes to avoid:**
- Restoring the whole database over production.
- Running an untested repair script directly on every row.

### Q. A slow memory leak restarts your service every night and nobody owns it.
**Short answer (45 seconds):** First I make sure it gets an owner, even if that is me: a ticket, an owner and a priority, because nightly restarts hide the problem until a traffic spike crashes it at noon. Then I confirm the leak from the memory graph, compare heap snapshots taken hours apart, fix what grows, and alert on memory growth.

**Deeper explanation:**
1. Confirm: memory climbs steadily through the day and drops only at restarts, while traffic rises and falls. In Kubernetes, `kubectl describe pod` shows the last state as Terminated with reason `OOMKilled` and exit code 137; a Node.js process may log `JavaScript heap out of memory`.
2. Contain: until the fix, a planned rolling restart beats an OOM kill mid-request; call it a band-aid.
3. Diagnose: start the service with a snapshot signal and take snapshots a few hours apart:

```bash
node --heapsnapshot-signal=SIGUSR2 server.js
kill -USR2 "$PID"   # writes a .heapsnapshot file into the working directory
```

Load them into Chrome DevTools, open the Comparison view and sort by size delta. For Python services, `tracemalloc` snapshots or `memray` do the same job.
4. Likely causes, ranked: an unbounded in-memory cache (a Map with no size limit or TTL); event listeners added per request, which Node flags with `MaxListenersExceededWarning: Possible EventEmitter memory leak detected`; timers or closures holding request objects; metrics with unbounded label values such as user IDs; chat histories or agent state kept in process memory.
5. Fix: bound the cache (LRU with a maximum size and TTL), remove listeners, move state to Redis.
6. Prevent: an alert on memory growth rate, a soak test that runs for hours in staging, and a named owner in the service catalog.

**Follow-ups they will ask:**
- Why not keep the nightly restart?: It hides growth and cuts off long-running work such as streams or agent runs.
- What if the heap is flat but memory still grows?: It is native memory; look at buffers, native modules and image or PDF libraries.
- How do you get it prioritized?: Show the trend, when it will start failing in peak hours, and the size of the fix.

**Mistakes to avoid:**
- Raising the memory limit and closing the ticket.
- Answering an ownership question with "not my service".

### Practice
- Pick one incident above and write its timeline as if it happened, with alerts, actions and updates at timestamps, then write the blameless post-mortem with three action items that each have an owner and a date.
- Break it on purpose: add an unbounded Map cache to a local Node.js service, load it for 20 minutes, take two heap snapshots and find the leak in the Comparison view.
- Run a 30-minute mock incident with a friend who reveals one signal at a time, and practice saying containment before diagnosis every time.
- Say it out loud: the first 30 minutes of the 2 a.m. sale outage in under three minutes, including your first stakeholder update word for word.
