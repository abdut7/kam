## The ML Lifecycle & MLOps Maturity

### In plain words
A model is not finished when it ships; it is more like a car that needs fuel, servicing and the occasional repair. The ML lifecycle is the loop of collecting data, training, testing, deploying, watching how the model behaves with real users, and retraining when the world changes. MLOps is the set of habits and tools that make that loop repeatable, instead of a one-off effort by one person with a notebook. Maturity is how much of the loop runs automatically and safely: at the low end someone retrains by hand a few times a year, at the high end a pipeline retrains, tests and promotes the model with checks at every step.

### From your saved posts
- vishakha.sadhwani (post 10), "Build the production stack": MLOps resource "Machine Learning Engineering for Production (MLOps)" (DeepLearning.AI); training resource "How to train AI ML models? Full pipeline in 15 mins"; LLMOps resource "End to End Advanced RAG Project, LLMOps, FAISS" playlist (Sunny Savita, 14 videos).
- pvergadia (post 4), 12 skills for each of 5 AI roles: MLOps is one of the AI Engineer skills, and MLOps and LLMOps is one of the AI Solutions Architect skills.

## Evaluation Pipelines in CI/CD

### In plain words
Unit tests check that code still works after a change; evals check that the AI still gives good answers after a change to the prompt, the model or the retrieval. You keep a fixed set of real questions with known good answers or grading rules, run them on every change, and block the release if scores drop, the same way a failing test blocks a merge. For agents you grade the steps too: did it pick the right tool, with the right arguments, and reach the right result. Error analysis is the habit of reading failures by hand, sorting them into groups, and fixing the biggest group first.

### From your saved posts
- anay.tech (post 6), 7 AI system design patterns: agentic evals (test tool selection, reasoning and outcomes).
- kevinnaughtonjr (post 16), 7 videos on how AI systems are really built: "Carrying Out Error Analysis" (Andrew Ng, DeepLearning.AI).
- aiwithanju (post 8), 7 AI projects for 2026: an AI evaluation pipeline is one of the projects.
- jam.with.ai (post 13), 12-week roadmap: AI evaluations, evaluation datasets, regression tests, prompt versioning, model comparisons and error analysis in the skills list; the Job Scout repo builds evals from traces with LLM judges plus a deterministic gate. https://github.com/jamwithai/observable-job-agent
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 8, evals for agents (you cannot test a trajectory like a function).

## Observability & Tracing for LLM Apps

### In plain words
An LLM feature is a chain of steps: fetch documents, call the model, maybe call a tool, then format the answer. Tracing records each step with how long it took, what it cost and what went in and out, like a parcel tracking page that shows every depot the parcel passed through. When a user says "the answer was wrong" or "it was slow", you open that request's trace and see which step was to blame instead of guessing. Because prompts can contain personal data, you also decide what to hide and how long to keep it.

### From your saved posts
- anay.tech (post 6), 7 AI system design patterns: observability (track LLM calls, latency, cost and failures).
- vishakha.sadhwani (post 10), "Build the production stack": "Observability Zero to Hero" (Abhishek Veeramalla) as the observability resource.
- jam.with.ai (post 13), 12-week roadmap: trace debugging and production monitoring in the skills list; the Job Scout repo uses Opik tracing with per-run cost. https://github.com/jamwithai/observable-job-agent
- aiwithanju (post 7) and codev.ai (post 17), 10 agentic concepts: concept 10, observability and tracing (when it breaks at step 14 of 30 you need to see step 14).

## Feedback Loops & the Data Flywheel

### In plain words
Every time a user gives a thumbs down, rewrites an answer or asks the same question again, the product learns something about where it fails. A feedback loop collects those signals, ties each one to the exact request that caused it, and turns the worst cases into tests and, later, into better prompts or training data. Think of a restaurant that reads every complaint card, links it to the dish and the cook on shift, and changes the recipe only after trying the new version. The flywheel is that habit repeated every week, so the product gets better the more people use it.

### From your saved posts
- anay.tech (post 6), 7 AI system design patterns: user feedback loops (improve with feedback and corrections).
- jam.with.ai (post 13), 12-week roadmap: evaluation datasets and error analysis in the skills list, which is where feedback ends up.

## AIOps & Platform Engineering [New]

> Two terms from job descriptions and from the "production AI stack" posts: AIOps and platform engineering. Interviewers use both loosely, so the first win is to say which meaning you are answering. A weak answer treats AIOps as "using ChatGPT at work" and platform engineering as "the DevOps team". A strong answer separates AI for IT operations from operating AI systems, explains what a platform team gives product teams and how it measures success, and shows judgment about how close an LLM may get to production.

### In plain words
AIOps has two everyday meanings. The original one is using AI to help run IT systems: spotting unusual behaviour in metrics, grouping a storm of alerts into one problem and suggesting a likely cause, like a smoke detector that also tells you which room is on fire. The newer, looser one is the work of running AI systems themselves, which overlaps with MLOps and LLMOps. Platform engineering is building a paved road inside a company: ready-made templates, pipelines and shared services, so product teams do not each rebuild the plumbing. An internal AI platform is that paved road for AI features: one approved way to call models, record traces, run evals and stay within budget.

### From your saved posts
- vishakha.sadhwani (post 10), "Build the production stack": the areas are RAG and fine-tuning, MLOps and LLMOps, inference and deployment, cloud and Kubernetes, DevOps and AIOps, observability and platform engineering, with one resource per area, including:
  - AIOps: "Automating DevOps with AI: End-to-End DevOps + AIOps Project" series (Vishakha Sadhwani, 5 videos).
  - Platform engineering: "What is Platform Engineering and how it fits into DevOps and Cloud world" (TechWorld with Nana).
  - DevOps: "The New Era of DevOps Engineering" and "All DevOps Concepts Explained in 25 Minutes" (Vishakha Sadhwani).
  - Observability: "Observability Zero to Hero" (Abhishek Veeramalla).
  - Model deployment: "DevOps + LLM + AI Project with Docker, Kubernetes, vLLM" (Vishakha Sadhwani).
- pvergadia (post 4), 12 skills for each of 5 AI roles: MLOps and LLMOps listed for the AI Solutions Architect.

### Concepts you must understand
- AIOps originally means applying machine learning to IT operations data: anomaly detection on metrics, correlating many alerts into one incident, suggesting probable root causes and triggering known remediations.
- The newer, looser usage means operating AI systems in production, which is MLOps for models you train and LLMOps for prompts, evals, tracing, cost and guardrails around foundation models.
- LLMs add a natural-language layer to operations: summarizing an incident from logs and traces, retrieving the right runbook, drafting updates; they speed up understanding but can be confidently wrong.
- Automation near production climbs a ladder: observe, summarize, recommend, act with human approval, act alone on a narrow allowlist of reversible actions.
- Platform engineering builds an internal developer platform: self-service golden paths (templates, pipelines, environments) that encode the organisation's defaults so product teams ship without tickets.
- An internal AI platform typically offers a model gateway (keys, quotas, routing, fallbacks, caching), self-service inference endpoints and GPU capacity, tracing and evals wired in by default, and guardrails and PII handling as shared services.
- A golden path works when it is the easiest option, not just a mandate; adoption, time to first production call and the number of teams bypassing it are the platform's metrics.
- The production AI stack is layered (app and RAG, LLMOps and MLOps, inference, cloud and Kubernetes, DevOps and AIOps, observability and platform), and an incident can start in one layer and page someone who owns another.

### Q. What does AIOps mean, and how is it different from MLOps and LLMOps?

**Short answer (45 seconds):** AIOps has two meanings, so I say which one I mean. The original is AI for IT operations: models that watch metrics, logs and events to detect anomalies, group a flood of alerts into one incident, suggest a probable root cause and sometimes trigger a known fix. The looser modern use is operating AI systems, which is really MLOps for models you train and LLMOps for prompts, evals, tracing and cost around foundation models. Short version: AIOps uses AI to run systems; MLOps and LLMOps run AI systems.

**Deeper explanation:**

```text
term     what is operated          typical work
AIOps    any IT system             anomaly detection, alert correlation,
         (AI is the tool)          root-cause hints, auto-remediation
MLOps    models you train          data and feature pipelines, training,
                                   registry, deployment, drift, retraining
LLMOps   LLM features and agents   prompt versions, eval gates, tracing,
                                   token cost, guardrails, model routing
```

Classical AIOps is statistics and ML on telemetry: baselines that understand daily and weekly seasonality, clustering alerts by time, service topology and text similarity, and mining past incidents for likely causes. Observability and incident vendors ship much of this built in (Datadog Watchdog, Dynatrace Davis, PagerDuty and BigPanda event correlation). LLMs add a layer on top: summarize an incident from logs and traces, retrieve the runbook, draft the status update. The gain is a shorter time to understand what is happening; the risk is a fluent wrong diagnosis, so every suggestion must cite the evidence it used.

**Follow-ups they will ask:**
- Is AIOps just smarter thresholds?: Partly; the larger win is deduplication and correlation, which cut pages per incident.
- What data does it need?: Clean telemetry with service ownership, topology and deploy events; without them it produces confident noise.
- Where do the terms meet?: An LLM feature's own incidents (cost spikes, provider latency) are handled with AIOps-style tooling over LLMOps telemetry.

**Mistakes to avoid:**
- Using AIOps, MLOps and LLMOps as synonyms.
- Promising auto-remediation without approvals, allowlists and rollback.

### Q. What is platform engineering, and what would an internal AI platform give product teams?

**Short answer (45 seconds):** Platform engineering is building an internal product for developers: self-service golden paths that turn the company's infrastructure, security and compliance rules into templates and APIs, so teams ship without tickets or rediscovering the rules. An internal AI platform does the same for AI features: a model gateway with keys, quotas, routing and fallbacks; self-service model endpoints and GPU capacity; tracing, evals and prompt management wired in; and guardrails, PII redaction and cost attribution as defaults rather than per-team projects.

**Deeper explanation:**

```text
team request: "new support summarizer"
  golden path template  -> repo, CI with eval gate, staging deploy
  model gateway         -> one endpoint, team key, budget, fallback model
  inference service     -> vLLM endpoint for an open-weight model, no GPU YAML
  built in              -> OpenTelemetry traces, cost per feature, prompt registry
  default guardrails    -> PII redaction, injection checks, output filters
```

The gateway is usually the first and highest-leverage piece: once every model call goes through it, you get central secrets, per-team spend, rate limits that respect provider quotas, caching, logging and one place to switch models. Options include LiteLLM proxy, Envoy AI Gateway and managed gateways. Then golden paths: a template that already contains the eval job, the trace exporter and the deployment manifests, so the safe way is also the fast way. Backstage is a common portal for the service catalog and templates. Run the platform like a product: measure adoption, time from idea to first production call, and who bypasses it, because bypasses show what is missing.

**Follow-ups they will ask:**
- Build or buy the gateway?: Start with an existing one; build only the policy and attribution layers specific to you.
- How is this different from DevOps?: DevOps is shared ownership of running software; platform engineering is a team that makes that ownership cheap with tooling.
- Mandate it?: Mandate the guardrails (gateway for keys and logging); make the rest worth choosing.

**Mistakes to avoid:**
- Building a platform before two or three teams share the same need.
- Hiding model choice and cost from the teams that pay for them.

### Q. How would you use an LLM to help an on-call engineer without letting it break production?

**Short answer (45 seconds):** I climb an autonomy ladder slowly. First read-only: the assistant pulls the alert, recent deploys, dashboards, logs and traces, retrieves the matching runbook and similar past incidents, and posts a summary that links every claim to its evidence. Next it recommends actions with the exact command and expected effect. Actions run only after a human approves, through the same pipelines and access controls a person would use. Fully automatic actions are limited to a short allowlist of reversible steps the team already scripts.

**Deeper explanation:**

```text
level 0  observe     metrics, logs, traces, deploy history (read-only creds)
level 1  summarize   incident summary, suspected change, links to evidence
level 2  recommend   "roll back deploy 4812?" with runbook step and blast radius
level 3  act w/ OK   human approves in Slack, action runs via existing pipeline
level 4  auto        allowlisted and reversible only, e.g. scale out a deployment
```

Rules: read credentials are separate from any write credentials; actions go through existing tooling (an Argo CD rollback, a feature-flag flip, a runbook automation job), never free-form shell, so they are audited and reversible; the assistant says "not enough evidence" rather than guessing. Treat log content as untrusted input, because anyone who can write a log line can plant text that reads like an instruction. Measure it like any tool: time to acknowledge, time to mitigate, and how often its suspected cause matched the postmortem.

**Follow-ups they will ask:**
- Why not let it restart services?: Restarts can destroy evidence and add load; allow them only where the runbook already marks them always safe.
- What context does it need?: Service ownership, dependencies, recent changes and runbooks; without these it guesses.
- How do you test it?: Replay past incidents and score whether it found the cause and proposed the right first action.

**Mistakes to avoid:**
- Giving the assistant the cluster-admin credentials the platform team uses.
- Trusting a fluent summary that cites no evidence.

### Q. Map the production AI stack: what sits between a prompt and a paged engineer?

**Short answer (45 seconds):** From the top: the application, where the prompt is assembled with RAG context or sent to a fine-tuned model; LLMOps and MLOps, which version prompts and models, gate changes with evals and watch quality; inference and deployment, the model servers or provider APIs; cloud and Kubernetes, the GPUs, nodes and networking underneath; DevOps and AIOps, the pipelines that ship it and the alerting that correlates failures; and observability plus platform engineering across all of them. A page is the end of a chain that can start in any layer.

**Deeper explanation:**

```text
user prompt
  app layer        prompt assembly, RAG retrieval, tools, guardrails
  LLMOps / MLOps   prompt and model versions, eval gate, feedback, drift
  inference        gateway, vLLM or provider API, batching, KV cache
  cloud / k8s      GPU node pool, autoscaling, storage for weights
  DevOps / AIOps   CI/CD, rollouts, alerts, correlation, runbooks
  observability    traces, metrics, logs, cost (spans every layer)
  platform eng     golden paths that make all of the above the default
    -> SLO burn-rate alert -> on-call engineer paged
```

Walk an incident through it: users report slow answers; the page is an SLO burn on time to first token; traces show inference spans waiting in a queue; metrics show the GPU pool did not scale because new nodes were stuck pulling a large image; the cause was a deploy that changed the image. The skill on show is following one request through every layer and knowing each layer's signal. That is why the trace id must cross every layer and why each layer needs a named owner.

**Follow-ups they will ask:**
- Where do incidents usually start?: Often at a change (deploy, config, capacity), so every layer should record versions.
- Where does cost show up?: Token and GPU cost per request in traces, rolled up per feature.
- Which layers would you own?: The app and LLMOps layers fully, plus enough inference and Kubernetes to debug with the platform team.

**Mistakes to avoid:**
- Describing the stack as "an LLM API plus a vector database".
- Debugging only the layer you know best.

### Practice
- Draw the production AI stack for one of your own projects and write, per layer, the one metric you would alert on and who owns it.
- Put LiteLLM proxy (or a small Express gateway) in front of two model providers with per-key budgets and a fallback, and export traces to Langfuse or an OpenTelemetry backend.
- Build a read-only on-call helper: given an alert name, fetch recent deploys, the last 15 minutes of error logs and the matching runbook section, and post a summary that cites each source; test it on three replayed incidents.
- Write a one-page golden path for "ship a new LLM feature": template repo, eval gate, gateway key, dashboards, rollback.
- Say it out loud: explain AIOps versus MLOps versus LLMOps in 45 seconds, then name one action you would never let an AI take in production and why.
