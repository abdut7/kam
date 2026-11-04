## Agentic Design Patterns

### In plain words
Most agents in production are built from a few well-known recipes, the way most meals come from a few cooking techniques. Prompt chaining is an assembly line, routing is a receptionist sending you to the right desk, parallelization is splitting a pile of work among friends, orchestrator-workers is a manager handing out tasks, and evaluator-optimizer is a writer working with an editor. A fully autonomous agent, where the model picks every next step, is the most flexible recipe and also the hardest to control. Good engineers start with the simplest recipe that works and add autonomy only when the task really needs it.

### From your saved posts
- kevinnaughtonjr (post 16), 7 videos on how AI systems are really built:
  - "How We Build Effective Agents" (Barry Zhang, Anthropic): keep agents simple and use one only where the task needs it.
  - "Don't Build Agents, Build Skills Instead" (Barry Zhang and Mahesh Murag, Anthropic): package reusable know-how as skills that a general agent loads when needed, instead of building a new agent for every use case.
  - "12-Factor Agents: Patterns of reliable LLM applications" (Dex Horthy, HumanLayer): engineering principles for reliable LLM apps, such as owning your prompts, your context window and your control flow, and keeping agents small and focused.
  - "Beating RL With Reflection: GEPA and Optimize Anything" (Lakshya A. Agrawal): reflection on run feedback used to improve prompts, the evaluator-optimizer idea applied to the prompt itself.
- pvergadia (post 15), AI Engineering 101: "Building Great Agent Skills: The Missing Manual" (mattpocock/skills).
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 6, orchestration patterns (one agent, a planner, or a swarm; each fails differently).

## Context Engineering

### In plain words
The model can only work with what is written on its notepad right now, and the notepad has a fixed size. Context engineering is deciding what goes on that notepad at each step: the instructions, the few documents that matter, the result of the last tool call, and nothing else. It is like briefing a colleague before a meeting: hand over the three pages they need, not the whole filing cabinet, because a pile of irrelevant pages makes them miss the one important line. Too little information and the agent guesses; too much and it gets confused and slow, and you pay for every extra word.

### From your saved posts
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 3, context engineering (right information in the window, wrong information out); the posts claim most people are stuck on concepts 3 and 4.
- soojintech (post 14), AI Advent Calendar: the context window explained as the size of the assistant's notepad. https://ai-advent-calendar.replit.app
- jam.with.ai (post 13), 12-week roadmap: context windows and context engineering listed as skills separate from prompt engineering.
- kevinnaughtonjr (post 16): "No Vibes Allowed: Solving Hard Problems in Complex Codebases" (Dex Horthy), on making coding agents work in large codebases.

## Memory & State

### In plain words
The model itself remembers nothing between calls; each time, it reads only what you hand it. Memory is your system's notebook: you decide what to write down, where to keep it and what to read back next time. Short-term memory is the notes for the current task, like a waiter remembering your order during this meal. Long-term memory is the customer file that says you are allergic to peanuts, kept across visits. Good memory design also decides what to forget, how long to keep things and who is allowed to see them.

### From your saved posts
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 5, memory architecture (what it remembers, for how long, what it may forget).
- jam.with.ai (post 13), 12-week roadmap: the skills list splits memory into conversation history, working memory, long-term memory, memory retrieval, memory updates, memory expiry, user-scoped memory and checkpointed state; weeks 10 to 12 cover memory, tools and voice.

## Harness & Loop Engineering

### In plain words
Think of the model as a talented new hire and the harness as the office you put them in: the desk, the keys they are given, the rules on the wall and the manager who checks in. The harness is all the ordinary code around the model that runs tools, enforces limits, catches errors and writes logs. Loop engineering is the manager's job: after every step, decide whether the agent keeps going, stops because it is done, or stops because something is wrong and a human should look. Most "the AI did something silly" incidents are really "the office had no rules" incidents, so a better harness usually helps more than a smarter model.

### From your saved posts
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 1, harness engineering (the environment the agent acts inside: sandbox, file system, runtime surface), and concept 2, loop engineering (when the agent runs again and when it stops).
- jam.with.ai (post 13), 12-week roadmap: step limits, tool result validation and human approval named as core agent skills; its Job Scout repo is a worked example of a harness with tracing and evals. https://github.com/jamwithai/observable-job-agent

## Multi-Agent Systems

### In plain words
One agent is one person doing the whole job. A multi-agent system is a small team: a lead who splits the work and helpers who each handle one piece, or a group passing a task from desk to desk. Teams finish wide, parallel jobs faster, like several researchers each reading different sources at the same time. But teams also cost more, because everyone has to be briefed, and they fail in new ways: two helpers make conflicting assumptions, or the lead loses track of who did what. Use a team only when the work really splits into independent parts.

### From your saved posts
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 6, orchestration patterns (one agent, a planner, or a swarm; each fails differently).
- aiwithanju (post 8), 7 AI projects for 2026: a multi-agent orchestration system is one of the projects.
- bashi_fuirkashi (post 2), AI engineer roadmap: pick one orchestration framework and go deep (LangGraph suggested), plus the Hugging Face Agents course and the book "Building Applications with AI Agents" (Michael Albada).

## MCP & Tool Ecosystems

### In plain words
Before USB, every device needed its own special cable; MCP is the USB port for AI tools. A tool provider writes one MCP server (for GitHub, a database, a calendar), and any app that speaks MCP can plug it in and see what it offers. The model still does not run anything itself: it asks for a tool by name, and the app calls the server and passes the answer back. Plugging in a server you did not write is like plugging in a stranger's USB stick, so your own code still decides what it is allowed to do.

### From your saved posts
- soojintech (post 14), AI Advent Calendar: tool calling lets the assistant take actions, and MCP is a standard way to connect it to tools and data. https://ai-advent-calendar.replit.app
- aiwithanju (post 8), 7 AI projects for 2026: an MCP-powered AI assistant is the first project.
- jam.with.ai (post 13), 12-week roadmap: tool calling and MCP servers in the skills list; weeks 10 to 12 include an MCP servers course (Model Context Protocol with Python).
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 4, tool design (the agent is only as capable as its tools and only as safe as their worst edge case), covered in depth in the section "Tool Design, Guardrails & Human-in-the-Loop".

## Agent Reliability & Evaluation

### In plain words
Testing a normal function is easy: same input, same output, check it. An agent is more like a new employee running a multi-step errand: you check whether the errand got done, and also whether they took sensible steps on the way, because a lucky result after a reckless route will fail next time. The agent can behave differently on each run, so you try the same task several times and count how often it succeeds. Observability is the dashcam: a recording of every step, so when something breaks at step 14 you can watch step 14 instead of guessing.

### From your saved posts
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 8, evals for agents (you cannot test a trajectory like a function), and concept 10, observability and tracing (when it breaks at step 14 of 30 you need to see step 14).
- anay.tech (post 6), 7 AI system design patterns: agentic evals (test tool selection, reasoning and outcomes) and observability (track LLM calls, latency, cost and failures).
- aiwithanju (post 8), 7 AI projects for 2026: an AI evaluation pipeline is one of the projects.
- jam.with.ai (post 13): the Job Scout repo builds evals from traces with LLM judges plus a deterministic gate, and uses Opik tracing with per-run cost. https://github.com/jamwithai/observable-job-agent
- kevinnaughtonjr (post 16): "Building and evaluating AI Agents" (Sayash Kapoor, AI Snake Oil).

## Tool Design, Guardrails & Human-in-the-Loop [Core]

> The "10 agentic concepts" posts claim most people get stuck on context and tool design, and that the gap between a demo and a system is guardrails, evals, human-in-the-loop and observability. Interviewers probe that gap with "what can your agent do, and what stops it doing the wrong thing?". A weak answer describes a prompt that tells the model to be careful. A strong answer treats tools as a designed API surface, enforces permissions in code at the moment of execution, keeps a short list of decisions reserved for humans, and can reconstruct any action from an audit record and a trace. The mechanics of sandboxes, approval tables and interrupts sit in earlier sections; this section is about the design decisions.

### In plain words
Tools are the agent's hands: everything it can actually do in the world, like looking up an order or sending an email. If the hands are clumsy (vague tools, confusing names, unclear errors), even a smart model fumbles. Guardrails and permissions are the locks on the doors: the agent can only open what its badge allows, however convincingly it asks. Human-in-the-loop means some decisions always go to a person, the way a junior employee can prepare a refund but a manager signs it. Audit logs and tracing are the receipts and the CCTV: afterwards you can prove what happened and see exactly where it went wrong.

### From your saved posts
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 4 tool design, concept 7 guardrails and permissions, concept 9 human-in-the-loop design (which decisions never get delegated) and concept 10 observability and tracing; the claim that the gap between a demo and a system is concepts 7 to 10.
- aiwithanju (post 8), 7 AI projects for 2026: "AI agent with audit logs" and "secure RAG system with guardrails".
- anay.tech (post 6), 7 AI system design patterns: guardrails (block unsafe and incorrect responses).
- jam.with.ai (post 13), 12-week roadmap: tool permissions, human approval, tool result validation, idempotency, step limits, prompt injection tests and trace debugging in the skills list.

### Concepts you must understand
- A tool is an API whose caller is a model: the name, description, parameter schema, return shape and error messages are all read by the model and shape what it does next.
- Fewer, task-shaped tools (`find_customer_orders`) beat thin wrappers over every endpoint, because each extra call is another chance to go wrong and another loop iteration to pay for.
- Read tools and write tools are separate, and write tools are idempotent, validated server-side and able to run as a dry run.
- Authorization is enforced at execution time, in code, against current data and the end user's own rights; the prompt is never the security boundary.
- An agent acting for a user must never exceed that user's permissions; a broad service credential turns the agent into a confused deputy that injected text can steer.
- Limits are layered: per-call argument rules, per-run step and spend caps, per-user and per-tenant rate limits, and a kill switch per tool.
- Some decisions are never delegated: irreversible or high-impact actions, decisions about people's rights or money, policy exceptions, and anything that changes the agent's own permissions or guardrails.
- An audit log proves what was done and on whose authority; a trace explains how the decision was reached; you need both, joined by run id.
- Debugging an agent means finding the first wrong step, not the step where it crashed, and replaying from a checkpoint with recorded tool results.

### Q. How do you design a good tool for an agent?

**Short answer (45 seconds):** I design a tool as an API whose caller is a model that reads every word. One tool, one clear job, named the way a person would describe the task; a description that says when to use it and when not to; a typed schema with enums, bounds and required fields so bad calls are impossible rather than discouraged. Reads are separate from writes, writes take idempotency keys and default to the safe option, results are trimmed and paginated, and errors say what to do next.

**Deeper explanation:** Anthropic's "Building effective agents" calls this the agent-computer interface and recommends poka-yoke design: change the arguments so mistakes are hard to make, for example requiring absolute file paths.

```json
{
  "name": "search_orders",
  "description": "Find a customer's orders, newest first. Use before any refund. Returns next_cursor when more exist.",
  "input_schema": {
    "type": "object",
    "properties": {
      "customer_id": {"type": "string", "description": "From get_customer, e.g. cus_123"},
      "status": {"type": "string", "enum": ["open", "shipped", "delivered", "refunded"]},
      "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
      "cursor": {"type": "string"}
    },
    "required": ["customer_id"]
  }
}
```

Return what the model needs for its next decision: readable fields and stable ids, not a raw payload. Cap result size and say so ("showing 5 of 37, pass cursor"), so truncation is never silent. Errors become instructions: "ord_91 belongs to another customer; call search_orders first" lets the model recover, a stack trace does not. Validate arguments server-side anyway, because schema adherence is not a security control. Consolidate: one `issue_refund(order_id, amount, reason)` that checks eligibility inside beats three calls the model must sequence correctly. Test by reading transcripts of realistic tasks and fixing descriptions where the agent slipped.

**Follow-ups they will ask:**
- How many tools is too many?: When selection accuracy drops; load task-specific subsets per agent profile and measure it.
- Who owns descriptions?: Engineers, reviewed and versioned like code, with evals on every change.

**Mistakes to avoid:**
- Exposing REST endpoints one-to-one and calling it a toolset.
- Returning huge payloads or bare error codes, then blaming the model.

### Q. What permission model do you put around agent tools?

**Short answer (45 seconds):** Deny by default, grant the smallest set the task needs, and enforce it in the executor at the moment of the call. Five layers: whose authority the agent runs with (the end user's delegated rights, never a superuser credential); which tools this agent profile may call at all; which argument values are allowed (amount caps, own-tenant ids, internal recipients); which calls need a dry run or a human approval; and how much a run, user and tenant may do per hour or day. Plus a kill switch per tool.

**Deeper explanation:** Assume injected text in a document, email or tool result can make the model call any tool it has with any arguments; the policy must hold even then.

```python
POLICY = {
    "search_orders":  {"mode": "allow"},
    "issue_refund":   {"mode": "approve_over", "auto_max": 50,
                       "rate": "3/hour/user", "daily_cap_per_tenant": 2000},
    "send_email":     {"mode": "approve", "allowed_domains": ["acme.com"]},
    "delete_account": {"mode": "deny"},
}

def authorize(principal, tool, args, run):
    rule = POLICY.get(tool, {"mode": "deny"})
    check_user_can(principal, tool, args)           # user's own rights, current data
    check_args(rule, args)
    check_limits(rule, principal, run)              # rate, spend, aggregates
    return decide(rule, args)                       # allow | dry_run | approval | deny
```

Delegated identity prevents the confused deputy problem: with an OAuth token scoped to the user, the agent cannot read another customer's data even if an injected instruction asks. Argument rules live in a policy layer (a plain function, or OPA or Cedar if you already run one) so they are versioned and unit tested. Dry run returns the effect without doing it, and that preview is what an approver sees. Spend limits cover money moved and tokens burned, and tripping one stops the run.

**Follow-ups they will ask:**
- Who sets the numbers?: Business owners; the policy file is reviewed like code and its version is recorded in traces.
- Can the agent split one large refund into small ones?: Aggregate caps per order and per day stop that.

**Mistakes to avoid:**
- One admin API key shared by every tool.
- Checking permissions when the plan is made instead of when the action executes.

### Q. Which decisions should never be delegated to an agent, and how do you design the approval step?

**Short answer (45 seconds):** I keep a short, written list. Never delegated: actions that cannot be undone or that leave the company (money above a threshold, external messages, deletes, production changes); decisions about a person's rights, money, health or job (credit, hiring, account closure); policy exceptions and cases the policy does not cover; and any change to the agent's own permissions, prompts, guardrails or audit settings. For these the agent prepares, a named human decides, and the executor refuses to act without a decision bound to that exact action.

**Deeper explanation:** Four questions decide the list: can it be undone cheaply, what is the worst-case cost, who is accountable if it goes wrong, and could the input have been written by an attacker. If accountability must sit with a person, the agent drafts and the person decides.

```text
agent proposes -> {action, exact args, evidence, short reason, risk tier}
policy         -> approval needed? which role? expiry?
human          -> approve | edit | reject (+ reason)
executor       -> runs only if token matches hash(action, args) and is unexpired
```

Design points beyond the mechanics: bind the approval to a hash of the exact arguments, so nothing can change after the human says yes; require a different principal from the requester for high-risk actions; treat silence or expiry as "no"; show evidence and a preview of the effect, not a JSON blob; and send the rejection reason back to the agent so it can take another path. Decisions about people also need an explanation the affected person can receive, which the model may draft but never owns.

**Follow-ups they will ask:**
- Does this kill automation?: No; most volume is reads and low-risk writes that run unattended.
- Urgent action at night?: An on-call approver role plus a safe holding action, such as pausing a job instead of deleting it.
- Who owns the list?: Product, risk or legal, and engineering together; it is versioned policy.

**Mistakes to avoid:**
- Letting the agent decide when it needs approval.
- An approval not bound to the exact arguments that get executed.

### Q. How do you build an agent with audit logs that would satisfy a compliance review?

**Short answer (45 seconds):** I treat the audit log as a product requirement, not a logging side effect. Every consequential step writes an append-only event: who asked and on whose authority, what the model proposed with model and prompt versions, which policy rule allowed or blocked it, who approved, what executed with its idempotency key and the external system's reference, and the outcome. Events are hash-chained, stored apart from traces, kept for the required retention period, and designed so personal data can be erased without breaking the chain.

**Deeper explanation:** Design for the reviewer's question: "show every action the agent took on customer X in March, and who approved each".

```json
{"run_id": "run_7f2", "step": 9, "type": "action_executed",
 "principal": "user:u_412", "tenant": "t_9", "subject_ref": "cust:c_88",
 "tool": "issue_refund", "args_hash": "sha256:...",
 "policy": {"rule": "refund.approve_over_50", "version": "2026.10.2"},
 "approval": {"by": "user:u_7", "at": "2026-10-12T09:14:03Z"},
 "model": {"prompt_version": "support-v14", "trace_id": "tr_51"},
 "external_ref": "re_3Kx", "outcome": "succeeded", "prev_hash": "...", "hash": "..."}
```

Write an intent event before the call and an outcome event after, so a crash in between shows up instead of vanishing. Keep personal data out of the chained record: store references and hashes, and put sensitive payloads in a separate store encrypted per data subject, so an erasure request deletes the key (crypto-shredding) while the chain stays valid. Grant inserts only, anchor the latest hash externally or use object-lock storage, and rehearse the export, because an auditor query that takes a week is a failed control.

**Follow-ups they will ask:**
- Why not use traces?: Traces are usually sampled and short-lived; the audit log is complete for consequential actions and kept far longer.
- Log the model's reasoning?: Log the justification shown to the approver; it is evidence of what they saw.
- Proving controls work?: Policy version on every event, plus periodic reports of denials and approvals.

**Mistakes to avoid:**
- Logging only successful actions, so denials leave no trail.
- Raw personal data inside an immutable chain you can never erase.

### Q. Your agent failed at step 14 of 30. How do you find out why?

**Short answer (45 seconds):** I open the run's trace, with one span per model call and per tool call, and walk backwards from step 14 to the first step where the run went wrong, because the visible failure is usually a symptom. At each suspect step I check what the model actually saw, what it decided and what the tool returned. Then I replay from the checkpoint before that step with recorded tool responses, change one thing, confirm the fix and keep the case as an eval.

**Deeper explanation:** Root causes usually sit earlier than the crash: a tool result at step 9 was silently truncated, compaction dropped a constraint, an empty list was read as "no orders exist", or the model picked a similar-sounding tool. Classify the cause (context, tool, model decision, harness), because each has a different fix.

```text
1. trace by run_id: spans 1..30, status, tokens, errors
2. from step 14, walk back to the first wrong-looking state
3. read the exact request the model got there, not the chat view
4. replay from the prior checkpoint with recorded tool outputs
5. vary one thing (tool output, description, prompt, model)
6. save a step-level eval: given this state, next action is X
```

This only works if you built for it: spans carry run id, step, prompt and tool versions, and redacted inputs and outputs; state is checkpointed per step; tool results are recorded so replay never repeats side effects. Tracing tools (LangSmith, Langfuse, OpenTelemetry) give the timeline; replay and step-level evals are usually yours to build.

**Follow-ups they will ask:**
- Replay does not reproduce it?: Run the step many times; an intermittent failure is a rate to measure, not one sample to chase.
- No trace kept for that run?: Keep 100 percent of failed and escalated runs from now on.
- Preventing a repeat?: A regression case plus an alert on the pattern.

**Mistakes to avoid:**
- Rerunning the whole task end to end and hoping it fails the same way.
- Debugging from the final answer instead of the exact model inputs.

### Practice
- Take one tool from a project (a refund or search tool) and rewrite it with the checklist: narrow purpose, enums, defaults, pagination, actionable errors, dry run; run 20 tasks before and after and count wrong or wasted tool calls.
- Write a policy function for three tools with argument caps and a per-user rate limit, then attack it with a prompt-injected document asking for a refund to another customer.
- Build the "agent with audit logs" project in miniature: every write produces intent and outcome events in a hash-chained Postgres table; tamper with one row and write the verifier that detects it.
- Force a failure at step 14 of a long run by truncating a tool result at step 9, then find the cause from the trace alone and replay from the checkpoint.
- Say it out loud: in 90 seconds, name the decisions your agent never makes on its own and explain how the executor enforces that.
