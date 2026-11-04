# Roadmap

> This is the map for the whole atlas: where you stand, what the interview loop for an AI Full Stack Engineer actually tests, how the eight phases of the BuildLifeAndAI roadmap map onto the tracks here, and a dated 12-week plan that starts with the backend sprint you asked for. Every other tab is a track you can study in Study mode and rehearse in Quiz mode.

## How to Use This Atlas

### Reading the tracks
- **Tracks** are the tabs in the left rail: Backend, Frontend & React, LLMs/RAG/Evals, Agents, Inference, Fine-tuning, MLOps & LLMOps, DevOps, Cloud & AWS. Each track is split into sections, each section has a **Concepts you must understand** list, a set of interview questions, and a **Practice** block.
- Every question has four parts: a **Short answer** you can say in about 45 seconds, a **Deeper explanation** with the mechanism and real commands, the **Follow-ups** an interviewer will push on, and the **Mistakes** that make an answer sound junior.
- **Study mode** shows everything. **Quiz mode** hides the answers so you can say your answer out loud first, then reveal and compare. Switch at the top right.
- Tick **I can answer this** on a question once you can give the short answer and survive one follow-up without looking. The counters in the rail and the header track your coverage. Progress is saved in this browser only.
- **Search** (top bar) looks across every track at once: type a term like "idempotency", "KV cache" or "useEffect" and jump straight to the matching questions.
- **Scenario-first:** every interview question in this atlas is a scenario, project or failure case: what you would do, decide, build or fix. Plain "what is X" material is not asked as a question. It lives in two places in each section: the **Why it exists** box (the problem the technology solves and what it costs) and the **Learn first** box (background reading you open when a scenario needs it).
- **Interview Playbook** (second tab) teaches the method: how to answer incident, design, project and behavioral questions, deep dives on your own projects (CADBEATER, VData, Samsung and more), cross-stack incidents, trade-off decisions, and a table of common errors from the browser to the GPU.
- **Every track ends with two scenario sections:** project scenarios (design and build situations) and incidents and error cases (a real error or symptom, then diagnosis, fix and prevention).
- **Explained Simply** (third tab) is the plain-English layer: one card per big term, each with a one-line meaning, an everyday analogy, a real example, an interview-ready sentence and a pointer to the deep answer. Start there whenever a word in a question feels fuzzy.
- **Python** (fourth tab) teaches Python from zero to FastAPI for a JavaScript engineer: 24 lessons with JavaScript comparisons, coding exercises you can try in Quiz mode, the patterns for coding rounds, and a FastAPI and Pydantic section. Each lesson has a matching exercise file with automatic tests in `07_Interview_Prep/python-practice` (see its README).
- **Internal Architecture** (fifth tab) opens up Node.js, Express, NestJS, FastAPI, the LLM transformer and the Jev decision model with diagrams first, then step-by-step walkthroughs, then interview questions.
- **Software Design** (sixth tab) covers SOLID and other design principles, creational, structural and behavioral design patterns, backend and enterprise patterns, architectural patterns (layered, clean, hexagonal, modular monolith, event-driven) and nine sample folder structures you can reuse in take-home assignments.
- **In plain words** boxes sit at the top of sections that your saved posts also covered. Read the box first, then the questions.
- **Level badges** on section titles tell you how deep a section goes: Basics, Core, Advanced, or Start here. Advanced material is kept at full depth; do it after the Core sections of the same track.
- **From your saved posts** notes show which of your Instagram saves fed a section, with verified links where they exist. The full list is in the Instagram Source Map at the end of this tab.

### The order that works
1. Read the section's Concepts list first, slowly. If a concept is new, read its question block in Study mode.
2. Do the Practice block. Theory you have not touched with your hands does not survive a follow-up question.
3. Switch to Quiz mode the next day and answer out loud. Only then tick the box.
4. Once a week, pick ten random ticked questions and re-answer them. Untick anything you fumble.

## Where You Stand

> You already ship the things most candidates only talk about: a MERN stack in production, LLM features with tool calling, MCP integrations, and real users. The gap for senior AI Full Stack interviews is not experience, it is making the theory behind that experience explicit, and filling the areas you have used but not owned: database internals, distributed systems vocabulary, model serving, fine-tuning, Kubernetes and AWS depth, and evaluation discipline.

### What the interview loop tests
| Stage | What they probe | Track that prepares you |
|---|---|---|
| Recruiter / hiring manager screen | Story, stack, why AI, salary, notice period | Roadmap (this tab), your resume |
| Coding / backend round | Node.js or Python depth, API design, data modelling, concurrency | Backend sections 1 to 10, Backend part 4 |
| System design round | Scalability, caching, queues, consistency, trade-offs, a 45-minute design | Backend: Distributed Systems, Caching, Message Queues, System Design Walkthroughs |
| AI / GenAI design round | RAG architecture, agents, evals, cost and latency, failure modes | LLMs/RAG/Evals, Agents, Inference |
| Frontend round (full stack roles) | React rendering, state, performance, Next.js, TypeScript | Frontend & React |
| Platform / DevOps questions | Docker, Kubernetes, CI/CD, deployment strategy, cloud services | DevOps, Cloud & AWS |
| Take-home assignment | Clean architecture, tests, README, evals for AI parts | Agents (harness), LLMOps (evals in CI) |
| Behavioural / bar raiser | Ownership, incidents, trade-offs you made, conflicts | Backend: Production Debugging (post-mortems), your own stories |

### Strengths to lead with
- Production LLM features and agents (tool calling, MCP, streaming) in a real product. Most candidates have demos; you have incidents and trade-offs. Tell those stories.
- Full MERN ownership: you can speak to the API contract, the React consumer, and the deployment. Senior interviewers value the end-to-end view.
- Four years of Python plus Node.js: you can pick the right runtime for an AI backend and explain why.

### Gaps to close, in priority order
1. **Backend theory you have used but not owned**: indexing internals, isolation levels, idempotency, delivery guarantees, CAP and consistency. Weeks 1 to 3.
2. **Agentic vocabulary**: naming the patterns you already use (orchestrator-workers, evaluator-optimizer, context engineering, harness design) so interviewers recognise the depth. Weeks 4 to 6.
3. **Evals as a discipline**: golden sets, LLM-as-judge pitfalls, regression gates. This is the most-asked AI engineering topic in 2026. Week 7.
4. **Inference and fine-tuning**: serving mechanics, quantization, LoRA, when to fine-tune. Weeks 8 to 11.
5. **Kubernetes and AWS depth**: objects, debugging, deployment strategies, IAM/VPC/compute choices. Weeks 7 to 12, interleaved.

## The Eight Phases, Mapped

> The BuildLifeAndAI roadmap you shared is an eight-phase ladder. You are not starting at phase 1; you are strengthening phases 1, 4, 5 and 6 and adding 2, 7 and 8. This table tells you where each phase lives in the atlas.

### Phase to track mapping
| Phase | What it means | Where it lives here | Your status |
|---|---|---|---|
| 1. Python and engineering fundamentals | Clean code, Git, testing, calling and streaming an LLM API, async and data structures | Backend (all parts), DevOps (CI/CD), Frontend (TypeScript) | Strong in practice; make the theory explicit |
| 2. Machine learning and deep learning | What happens inside a network, training vs inference, overfitting, bias-variance | Fine-tuning: ML and Training Fundamentals | New; learn just enough to reason |
| 3. LLMs | Tokens, embeddings, probabilistic outputs, prompting like an engineer, context windows | LLMs/RAG/Evals: sections 1 to 2 | Used daily; formalise |
| 4. RAG | Embeddings and vector search, chunking, why hallucinations are retrieval bugs | LLMs/RAG/Evals: sections 3 to 6 | Used; go deep on failure modes and evals |
| 5. Agents | Tools and memory, state lives in your architecture, multi-step planning, when not to use an agent | Agentic Engineering (all sections) | Strong; learn the names and trade-offs |
| 6. Production deployment | Cost and latency, prompt caching, evaluation and guardrails, monitoring and versioning | Inference, LLMOps, DevOps | Partial; biggest leverage for senior roles |
| 7. Enterprise AI | Security, privacy and PII, governance, audit trails, human-in-the-loop, legacy integration | LLMOps: Governance; LLMs/RAG/Evals: Safety; Cloud: IAM | New; mostly vocabulary and patterns |
| 8. Build in public | 2 to 3 end-to-end projects, writing about what broke, a weekly habit | Portfolio Projects below | Start in week 2 |

## The 12-Week Plan

> Two threads run in parallel every week: an AI thread and an engineering thread, because AI Full Stack interviews test both in the same loop. The first two weeks are the backend sprint you asked for. When an interview lands, switch to the Interview-Tomorrow checklists below and come back to the plan afterwards.

### Weekly schedule
| Week | Dates | AI thread | Engineering thread | Deliverable |
|---|---|---|---|---|
| 1 | Oct 30 to Nov 5 | LLMs for engineers, Prompt engineering (refresh) | Backend: Database Indexing, Transactions and Isolation, Concurrency, Caching | Run EXPLAIN ANALYZE on a real table and fix one slow query; answer 10 questions aloud in Quiz mode |
| 2 | Nov 6 to Nov 12 | RAG Fundamentals, Embeddings and Vector Search | Backend: Idempotency, Message Queues, Distributed Systems, API Design | Idempotent payment endpoint demo with Postgres keys table; a minimal RAG over your own docs with pgvector |
| 3 | Nov 13 to Nov 19 | Advanced RAG, RAG Failure Modes | Backend: Database Design, Production Debugging, Node.js Internals, Auth and Security | Two 45-minute system design mocks (rate limiter, notification service); 30-question retrieval eval set |
| 4 | Nov 20 to Nov 26 | Agent Fundamentals, Agentic Design Patterns, Context Engineering | Frontend: Rendering Model, Hooks, State Management | An agent loop written without a framework, then one pattern (orchestrator-workers) added on top |
| 5 | Nov 27 to Dec 3 | Memory and State, Harness and Loop Engineering, MCP | Frontend: Performance, Architecture, Next.js | An MCP server with two tools plus a harness: budgets, retries, permission gate, replayable traces |
| 6 | Dec 4 to Dec 10 | Multi-Agent Systems, Agent Reliability, Production Agent Architecture | Frontend: Data Fetching, TypeScript, Testing, Security, AI Product UIs | Streaming chat UI that shows tool calls and supports cancel; trajectory eval for the week-5 agent |
| 7 | Dec 11 to Dec 17 | Evaluating LLM Systems, Safety and Guardrails, Cost and Latency | DevOps: Docker Fundamentals, Containers in Production | Eval suite with 50 golden cases running in GitHub Actions as a regression gate; prompt-injection test cases |
| 8 | Dec 18 to Dec 24 | Inference Fundamentals, Serving Engines, Quantization | DevOps: Kubernetes Core Objects, Kubernetes Operations | Serve a small open model with vLLM or Ollama in Docker; measure TTFT and tokens per second at 1, 4 and 16 concurrent users |
| 9 | Dec 25 to Dec 31 | Speed-ups, Scaling and Routing, Inference Caching, Cost Engineering | DevOps: CI/CD Pipelines, Deployment Strategies | Inference router project: classify, route, cache, fall back, stream, expose metrics |
| 10 | Jan 1 to Jan 7 | Fine-tuning: When to Fine-tune, ML Fundamentals, LoRA and QLoRA, Data Engineering | DevOps: Scalability and Reliability, Infrastructure as Code | QLoRA fine-tune of a small model on a synthetic dataset; compare against the base model on a held-out set |
| 11 | Jan 8 to Jan 14 | Fine-tuning: Preference Optimization, Tooling, Shipping, SLMs | Cloud: Fundamentals, IAM, Networking, Compute, Storage | Deploy the week-2 RAG app on AWS (containers plus managed Postgres with pgvector) using Terraform |
| 12 | Jan 15 to Jan 21 | MLOps and LLMOps (full track), Governance, FinOps | Cloud: Messaging, Serverless, Observability, AI Services, Architecture Scenarios | Capstone write-up and a full mock loop: backend, system design, AI design, behavioural |

### Daily rhythm (about three hours)
- 10 minutes: the Explained Simply cards for the terms in today's section, so the vocabulary is solid before the questions.
- 30 minutes: one Python lesson, then its practice-kit file until the tests pass (`uv run --with pytest pytest tests/test_<lesson>.py` in `python-practice`). Twenty-four lessons take about four weeks at one per working day.
- 60 minutes: read one section in Study mode, Concepts first, then the questions.
- 30 minutes: Quiz mode on yesterday's section, answers spoken out loud, then tick what you nailed.
- 60 minutes: the Practice block or the week's deliverable. Hands on the keyboard, not on the slides.
- 15 minutes: write three lines of notes on what surprised you. These become your "what broke" posts.
- Weekly: one mock interview with a peer or recorded alone, and one short public post about the deliverable.

### When interviews are dense
- Compress the plan, do not skip the sequence: backend first, then agents and evals, then the rest.
- The night before any round, use the matching Interview-Tomorrow checklist below and nothing else.
- Keep the engineering thread alive even in AI-heavy weeks; full stack loops always include at least one backend or React round.

## Interview-Tomorrow Checklists

> Each list is a 90-minute review for a specific round type. Open the named sections, read only the Short answers, and say the Follow-ups out loud.

### Backend or system design round tomorrow
- Backend: Database Indexing (B-tree, composite and left-prefix, covering index, diagnosing a slow query).
- Backend: Transactions and Isolation Levels (the four levels, the three anomalies, optimistic vs pessimistic locking).
- Backend: Caching (four strategies, stampede, hot keys, consistency).
- Backend: Idempotency (payment endpoint design, keys table, crash before respond).
- Backend: Message Queues and Distributed Systems Basics (delivery semantics, DLQ, CAP, consistent hashing).
- Backend: API Design (REST vs GraphQL vs gRPC, versioning, cursor pagination, long-running endpoints).
- Backend part 4: System Design Walkthroughs (the 45-minute method and two worked designs).
- Internal Architecture: redraw the Node.js layers diagram and the event loop turn from memory, then the FastAPI request lifecycle and the NestJS request lifecycle.
- Software Design: SOLID Principles (one example per principle from your own code), Architectural Patterns (layered vs clean vs hexagonal), and the folder structure for the framework the company uses.

### Take-home assignment or code review round tomorrow
- Software Design: Sample Folder Structures (pick the tree that matches the stack and copy its rules into your README).
- Software Design: SOLID Principles and Design Principles Beyond SOLID (name the trade-off you made, for example "kept it simple, no repository layer, because...").
- Software Design: Backend and Enterprise Patterns (repository, unit of work, DTOs and DI, and when each is overkill).
- Internal Architecture: Express.js Request Pipeline or NestJS Architecture, whichever the assignment uses.

### AI engineer or GenAI design round tomorrow
- LLMs/RAG/Evals: RAG Fundamentals and RAG Failure Modes (chunking, reranking, retrieval vs generation errors).
- LLMs/RAG/Evals: Evaluating LLM Systems (golden sets, LLM-as-judge pitfalls, regression gates).
- Agents: Agent Fundamentals, Agentic Design Patterns, Context Engineering.
- Agents: Harness and Loop Engineering, Agent Reliability and Evaluation.
- Inference: Inference Fundamentals and Cost Engineering (TTFT, KV cache, prompt caching, routing).
- Fine-tuning: When to Fine-tune (the decision matrix, said in two sentences).
- Internal Architecture: LLM Transformer Architecture (draw the decoder block and one attention head) and Jev: Decision-Layer Model Architecture (where a decision layer sits in an agent).

### AI system design round tomorrow
- LLMs/RAG/Evals: AI System Design Patterns (the seven patterns and the 45-minute answer shape).
- Explained Simply: The 7 AI System Design Patterns and The 10 Agentic Concepts (read every card's "Say it in an interview" line).
- Agents: Tool Design, Guardrails & Human-in-the-Loop.
- Inference: Inference Engineering Levels (the one-GPU, fifty-users story).
- MLOps & LLMOps: Observability & Tracing for LLM Apps, Feedback Loops & the Data Flywheel.

### ML, data or SQL round tomorrow
- Backend: SQL Interview Patterns (window functions, CTEs, the approach for unseen questions).
- LLMs/RAG/Evals: ML System Design Basics (recommendations, ranking, A/B tests, offline vs online metrics).
- Fine-tuning & ML: ML & Training Fundamentals for LLMs.

### React or full stack round tomorrow
- Frontend: React Rendering Model and Hooks Deep Dive.
- Frontend: State Management at Scale and Performance Engineering.
- Frontend: Next.js and Rendering Strategies, TypeScript for React.
- Frontend: Building AI Product UIs (streaming, cancellation, tool-call display).
- Backend: API Design (the contract you will consume).

### DevOps or cloud questions tomorrow
- DevOps: Docker Fundamentals, Kubernetes Core Objects, Kubernetes Operations and Debugging.
- DevOps: CI/CD Pipelines and Deployment Strategies.
- Cloud: IAM and Security, Networking, Compute Options.
- Cloud: Architecture Scenarios (the MERN-on-AWS and RAG-on-AWS designs).

## Portfolio Projects

> Phase 8 of the roadmap says two or three end-to-end projects beat any certificate. These three are chosen so that each one is also an interview story: a design decision, a failure you found through evals or metrics, and a fix you can explain.

### Project 1: RAG service with evals and observability
- Stack: Python and FastAPI, Postgres with pgvector (or Qdrant), a reranker, Langfuse or LangSmith for traces, a 50-question golden set, GitHub Actions running the eval on every pull request.
- What to demonstrate: hybrid retrieval versus pure vector on your own eval set, one chunking experiment with numbers, citation grounding, and a prompt-injection test case that fails safely.
- Interview story: "Most of our hallucinations were retrieval bugs; here is how I proved it and what changed."

### Project 2: Agentic workflow with MCP tools and a real harness
- Stack: TypeScript or Python, an MCP server exposing two or three tools, an agent loop with budgets, retries, a permission gate for side-effecting tools, replayable traces, and a trajectory eval.
- What to demonstrate: one pattern applied deliberately (orchestrator-workers or evaluator-optimizer), context engineering choices (what you compact, what you fetch just in time), and a runaway-loop guard that you can show triggering.
- Interview story: "The model is ten percent of the system; here is the harness that made it reliable."

### Project 3: Inference router with a self-hosted model
- Stack: vLLM or Ollama serving a small open model in Docker, a Node.js or Python gateway that classifies requests, routes between the local model and a hosted API, caches, falls back, streams, and exports Prometheus metrics; a notebook with a QLoRA fine-tune of the small model for the routing classifier.
- What to demonstrate: TTFT and throughput at several concurrency levels, cost per request before and after routing and caching, and the quality check that justified quantization.
- Interview story: "Here is how I cut cost per request while holding the latency SLO, with the numbers."

### More project ideas from your saved posts
| Idea | From | What it proves | Fits into |
|---|---|---|---|
| MCP-powered AI assistant | aiwithanju, 7 projects | You can expose real tools safely through a standard protocol | Project 2 |
| Multi-agent orchestration system | aiwithanju, 7 projects | You know when a planner or a swarm helps and when it only adds cost | Project 2 |
| AI evaluation pipeline | aiwithanju, 7 projects | Eval-driven development with a regression gate | Project 1 |
| Secure RAG system with guardrails | aiwithanju, 7 projects | Prompt-injection defence, permission-aware retrieval, output checks | Project 1 |
| AI agent with audit logs | aiwithanju, 7 projects | Enterprise readiness: every step traceable and reviewable | Project 2 |
| Fine-tuned open-source LLM | aiwithanju, 7 projects | You can run the data, LoRA, eval and serving loop end to end | Project 3 |
| Knowledge-graph-powered AI | aiwithanju, 7 projects | Retrieval over relationships, not only similar text | Project 1 add-on |
| Your own inference engine on one GPU | lindavivah, Akamai workshop repo | Prefill, decode, KV cache and batching seen live, plus a benchmark table | Project 3 |
| Benchmarking project | vishakha.sadhwani, three levels of inference | TTFT, throughput and GPU utilization across configurations | Project 3 |
| News summarizer, RAG app, production agent, voice agent | jam.with.ai, 12-week roadmap | A four-step build ladder; the final step adds memory, tools, voice, quality and cost tracking | Weeks 1 to 12 |

- Reference build for the last rung: the open-source Job Scout agent (https://github.com/jamwithai/observable-job-agent) shows search, CV tailoring grounded in your real experience with a non-LLM fabrication check, evals built from traces, an optional voice console, and per-run cost in the traces. Read it as a model of what "production agent" means in a portfolio.
- The inference lab: https://github.com/akamai-developers/akamai-workshop-ai-inference walks through a GPU node on Kubernetes, vLLM serving a Qwen model behind an OpenAI-compatible endpoint, KV cache and batching through vLLM's metrics, BF16 vs FP8, speculative decoding, saturation, and finally an agent on your own inference. GPU time is billed hourly, so tear it down after each session.

### Build in public
- Each project gets a README with: problem, architecture diagram, how to run, eval results, what broke and what you changed.
- One short post per deliverable (LinkedIn or a blog): what you built, one number, one lesson. This is the weekly habit from phase 8 and it also feeds recruiter searches.

## AI Career Paths [New]

> One of your saves compares five AI roles that are often confused. You are targeting AI Full Stack Engineer, which sits between the AI Engineer and Forward Deployed Engineer columns: you need the AI engineer's build skills plus the full stack ownership and customer-facing clarity of a forward deployed engineer. Use the table to see which skills each role rewards and where the atlas covers them.

### Five roles, twelve skills each
| # | AI Engineer | Forward Deployed Engineer | AI Product Manager | Data Engineer | AI Solutions Architect |
|---|---|---|---|---|---|
| 1 | Python | Python | AI and LLM fundamentals | Python or Scala | Cloud architecture |
| 2 | LLMs and APIs | System design | Prompt engineering | SQL | LLMs and GenAI |
| 3 | Prompt engineering | APIs and integration | Evaluation metrics | Apache Spark | RAG and agent design |
| 4 | RAG architecture | SQL | Product strategy | Kafka | System design at scale |
| 5 | Vector databases | LLMs and prompt engineering | User research | Airflow | APIs and microservices |
| 6 | AI agents | RAG and agents | SQL and data analysis | dbt | Security and compliance |
| 7 | LangChain or LlamaIndex | Fast prototyping | Roadmap planning | Data warehousing | Cost optimization |
| 8 | FastAPI | Customer communication | Stakeholder communication | ETL and ELT pipelines | Multi-cloud strategy |
| 9 | Evaluation and evals | Executive storytelling | Executive storytelling | Delta Lake or Iceberg | MLOps and LLMOps |
| 10 | Fine-tuning | Business acumen | AI ethics and governance | Feature stores | Executive communication |
| 11 | Docker and cloud | Cloud basics | ROI measurement | Cloud data platforms | Technical storytelling |
| 12 | MLOps | Technical documentation | Agent workflow design | Data quality testing | Enterprise integration |

The post also shows US base-pay bands for some roles (for example $150,000 to $280,000 for forward deployed engineers and $120,000 to $175,000 for data engineers). Treat them as US figures from the creator, not as India or UAE benchmarks.

### Where the atlas covers each AI Engineer skill
| Skill | Track and section |
|---|---|
| Python, FastAPI | Backend: Python & FastAPI for AI Backends |
| LLMs and APIs, prompt engineering | LLMs/RAG/Evals: How LLMs Work, Prompt Engineering as Engineering |
| RAG architecture, vector databases | LLMs/RAG/Evals: Embeddings & Vector Search, RAG Fundamentals, Advanced RAG Patterns |
| AI agents, LangChain or LlamaIndex | Agents: all sections |
| Evaluation and evals | LLMs/RAG/Evals: Evaluating LLM Systems; MLOps & LLMOps: Evaluation Pipelines in CI/CD |
| Fine-tuning | Fine-tuning & ML: all sections |
| Docker and cloud | DevOps: Docker Fundamentals; Cloud & AWS: all sections |
| MLOps | MLOps & LLMOps: all sections |

### What the forward deployed column adds for you
- Fast prototyping and customer communication: practise turning a vague customer problem into a working demo in a day, then explaining the trade-offs to a non-technical stakeholder in five minutes.
- Executive storytelling and business acumen: for every portfolio project, write the one-paragraph business case (who pays, what it saves, what it costs to run).
- Technical documentation: every project README should let a stranger run it in ten minutes.

## AI Engineer Skills Checklist [New]

> One of your saves lists what separates AI engineers from people who only vibe code. Tick through it honestly once a week. Each line names where the atlas teaches it, so a gap turns straight into a reading list.

### Foundations
- Python, APIs and JSON, async programming, data validation, unit tests, dependency injection: Backend (Python & FastAPI for AI Backends, Node.js Runtime Internals).
- Structured outputs, prompt engineering, context windows, context engineering, model selection: LLMs/RAG/Evals (Prompt Engineering as Engineering, How LLMs Work); Agents (Context Engineering).

### Retrieval
- Document ingestion, chunking strategies, embeddings, similarity metrics: LLMs/RAG/Evals (RAG Fundamentals, Embeddings & Vector Search).
- Vector search, keyword search, hybrid search, reciprocal rank fusion, HNSW indexes: LLMs/RAG/Evals (Embeddings & Vector Search, Advanced RAG Patterns).
- Grounded answers, source citations, knowledge graphs, ontology design, entity relationships: LLMs/RAG/Evals (RAG Fundamentals, Advanced RAG Patterns).

### Memory and agents
- Conversation history, working memory, long-term memory, memory retrieval, updates and expiry, user-scoped memory, checkpointed state, scheduled follow-ups: Agents (Memory & State).
- Agent orchestration, tool calling, MCP servers, agentic RAG, query rewriting, workflow routing, state management, step limits, human approval, tool result validation: Agents (Agent Fundamentals, Agentic Design Patterns, Harness & Loop Engineering, MCP & Tool Ecosystems, Tool Design, Guardrails & Human-in-the-Loop).
- Model routing and provider fallbacks: Inference (Scaling, Routing & Load Balancing, Project Blueprint: Inference Router).

### Quality
- AI evaluations, evaluation datasets, retrieval quality, answer quality, grounding checks, regression tests, model comparisons, error analysis, quality-cost trade-offs: LLMs/RAG/Evals (Evaluating LLM Systems, RAG Failure Modes & Debugging); MLOps & LLMOps (Evaluation Pipelines in CI/CD).
- Prompt versioning, trace debugging, production monitoring: MLOps & LLMOps (Prompt Management & Versioning, Observability & Tracing for LLM Apps).

### Security and production engineering
- Authentication, authorization, document permissions, tool permissions, secrets management: Backend (Authentication, Authorization & API Security); Agents (Tool Design, Guardrails & Human-in-the-Loop).
- Prompt injection tests: LLMs/RAG/Evals (Safety, Security & Guardrails).
- Idempotency, API gateways, rate limiting, message queues, circuit breakers, CI/CD: Backend (Idempotency, Message Queues, Resilience & Microservice Patterns); DevOps (CI/CD Pipelines).

### Inference
- Prefill and decode, KV cache, PagedAttention, continuous batching, chunked prefill, prefix caching, quantization, speculative decoding, latency and throughput, caching: Inference (all sections) and Explained Simply (How Inference Works, One Problem at a Time).

## Resource Library [New]

> Every learning resource named in your saved posts, grouped by area. Links are given only where they were opened and checked on 30 Oct 2026; for the rest, search the exact title on YouTube or the named site. Use these to go deeper after the atlas, not instead of it: the atlas tells you what interviewers ask, these show you how practitioners build.

### Foundations: how models work
- Andrej Karpathy, "Neural Networks: Zero to Hero": https://karpathy.ai/zero-to-hero.html
- 3Blue1Brown, neural networks series: https://www.3blue1brown.com/topics/neural-networks
- Andrej Karpathy, "Deep Dive into LLMs like ChatGPT" (YouTube).
- Hugging Face LLM course: https://huggingface.co/learn/llm-course
- IBM Technology, "AI Inference: The Secret to AI's Superpowers" (YouTube).

### RAG and agents
- LangChain, "RAG from scratch" series (YouTube).
- KodeKloud, "RAG Crash Course for Beginners" (YouTube).
- Hugging Face AI Agents course: https://huggingface.co/learn/agents-course
- LangGraph: pick one orchestration framework and go deep.
- Anthropic, "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents
- HumanLayer, "12-Factor Agents" (Dex Horthy): https://github.com/humanlayer/12-factor-agents
- Intro to MCP servers, "Model Context Protocol with Python" full course (YouTube).
- Jam with AI, "Build a local LLM-based RAG system for your personal documents" (blog series).

### Talks worth an evening each
- "12-Factor Agents: Patterns of reliable LLM applications", Dex Horthy (AI Engineer).
- "No Vibes Allowed: Solving Hard Problems in Complex Codebases", Dex Horthy.
- "How We Build Effective Agents", Barry Zhang (Anthropic).
- "Don't Build Agents, Build Skills Instead", Barry Zhang and Mahesh Murag (Anthropic).
- "Building and evaluating AI Agents", Sayash Kapoor.
- "Carrying Out Error Analysis", Andrew Ng (DeepLearning.AI).
- "Beating RL With Reflection: GEPA and Optimize Anything", Lakshya A. Agrawal.
- AI Engineering 101, one a day: Nick Saraev "What I'd Learn Instead of Automation in 2026"; "A Practical Guide to Becoming an AI Engineer"; Karpathy "Deep Dive into LLMs like ChatGPT"; "Andrej Karpathy: From Vibe Coding to Agentic Engineering"; Greg Isenberg on graph engineering; Mario Zechner "Building pi in a World of Slop"; "Building Great Agent Skills: The Missing Manual".

### Books
- Chip Huyen, "AI Engineering".
- Michael Albada, "Building Applications with AI Agents".

### Inference, deployment and infrastructure
- Akamai Developers inference workshop (vLLM, Qwen, KV cache, FP8, speculative decoding, agent on your own GPU): https://github.com/akamai-developers/akamai-workshop-ai-inference
- Vishakha Sadhwani, "AI Inference Crash Course: Master AI Engineering in 20 Minutes" and "DevOps + LLM + AI Project with Docker, Kubernetes, vLLM" (YouTube).
- NVIDIA AI Infrastructure and Operations course (named as a level-1 exit route).
- Vishakha Sadhwani Kubernetes series: "The Only Kubernetes Course You'll Ever Need", "Kubernetes for AI: Zero to Hero", "Kubernetes Security Best Practices in 12 Minutes" (YouTube).
- Vishakha Sadhwani, "Become a Cloud Engineer in 2026" and "5 Resume Projects for Cloud and DevOps" (YouTube).
- Vishakha Sadhwani, "The New Era of DevOps Engineering" and "All DevOps Concepts Explained in 25 Minutes" (YouTube).

### MLOps, LLMOps, AIOps, observability
- DeepLearning.AI, "Machine Learning Engineering for Production (MLOps)".
- Sunny Savita, "End to End Advanced RAG Project, LLMOps, FAISS" playlist (YouTube).
- Vishakha Sadhwani, "Automating DevOps with AI: End-to-End DevOps + AIOps Project" series (YouTube).
- Abhishek Veeramalla, "Observability Zero to Hero" (YouTube, long-form).
- TechWorld with Nana, "What is Platform Engineering and how it fits into DevOps and Cloud world" (YouTube).
- freeCodeCamp, "Fine Tuning LLM Models, Generative AI Course" (YouTube).
- "How to train AI ML models? Full pipeline in 15 mins" (YouTube).

### Interview practice
- Aced, formerly Exponent, YouTube channel: https://www.youtube.com/@aced_io . Four playlists named in your save: System Design Interview Prep (mock interviews such as Google Docs, Uber Eats, key-value store, distributed LRU cache, web crawler), Machine Learning Interview Prep (ML system design, recommendations, ranking, embeddings, deployment), Data Science Interview Prep (A/B testing, metrics, product analytics), SQL Interview Prep (hands-on query problems and optimization).

### Plain-English refreshers
- AI Advent Calendar, nine fundamentals explained simply (models, tokens, context window, inference, embeddings, semantic search, RAG, tool calling, MCP): https://ai-advent-calendar.replit.app

### Tools
- Desigma, a free offline design tool written in Rust that imports Figma files (early alpha): https://github.com/deepfounder-ai/desigma . Not interview material; useful if you want to own UI design files for portfolio projects without a Figma seat.

## Instagram Source Map [New]

> Where each of your 19 saved posts landed in the atlas. Captions were read from the posts, videos were transcribed, on-screen text was read from the frames, the carousel was read slide by slide, and every linked site or repo that could be opened was checked.

### Post by post
| # | Creator | Topic | Where it lives now |
|---|---|---|---|
| 1 | vishakha.sadhwani | Three levels of inference engineering | Inference: Inference Engineering Levels; Explained Simply: Production AI Stack Words |
| 2 | bashi_fuirkashi | Roadmap with fundamentals, RAG, agents, books, FastAPI and Docker | Roadmap: Resource Library |
| 3 | not accessible | Age-restricted post, hidden from signed-out viewers | Skipped |
| 4 | pvergadia | Five AI roles, twelve skills each | Roadmap: AI Career Paths |
| 5 | lindavivah | Build your own inference engine in six steps | Inference: Inference Engineering Levels; Roadmap: project ideas and resources |
| 6 | anay.tech | Seven AI system design patterns | LLMs/RAG/Evals: AI System Design Patterns; Explained Simply |
| 7 | aiwithanju | Ten agentic concepts | Agents (synced sections and Tool Design, Guardrails & Human-in-the-Loop); Explained Simply |
| 8 | aiwithanju | Seven AI projects | Roadmap: More project ideas |
| 9 | jam.with.ai | AI/ML interviews: four interview-prep playlists | Backend: SQL Interview Patterns and system design; LLMs/RAG/Evals: ML System Design Basics; Resource Library |
| 10 | vishakha.sadhwani | The production AI stack with a resource per area | MLOps & LLMOps: AIOps & Platform Engineering; Resource Library |
| 11 | skdneuron | Fifteen fine-tuning techniques | Fine-tuning & ML: The 15 Fine-tuning Techniques; Explained Simply |
| 12 | jam.with.ai | Inference concepts, one problem at a time | Inference (synced); Explained Simply: How Inference Works |
| 13 | jam.with.ai | 12-week roadmap, four projects, skills list | Roadmap: Skills Checklist, project ideas, resources |
| 14 | soojintech | AI Advent Calendar, nine fundamentals | Explained Simply: AI Fundamentals in Plain Words |
| 15 | pvergadia | AI Engineering 101, a talk a day | Roadmap: Resource Library |
| 16 | kevinnaughtonjr | Seven videos on building AI systems | Roadmap: Resource Library; Agents and evals (synced) |
| 17 | codev.ai | Ten agentic concepts, one line each | Agents (synced); Explained Simply |
| 18 | iiterate_technologies | Floorplan AI, drawings to structured data | LLMs/RAG/Evals: Computer Vision & Document AI; Explained Simply |
| 19 | gittrend.io | Desigma offline design tool | Roadmap: Resource Library, Tools |

## Source Map

> What each source contributed to this atlas, so you know where the emphasis comes from.

### Sources and how they were used
| Source | What it is | How it shaped the atlas |
|---|---|---|
| BuildLifeAndAI "AI Engineer Roadmap 2026" (PDF you attached) | An eight-phase carousel: fundamentals, ML/DL, LLMs, RAG, agents, production, enterprise AI, build in public | The phase mapping above and the order of the AI thread |
| Notion page "Backend Interview Questions" | 10 sections, 80 questions: indexing, transactions, concurrency, caching, idempotency, queues, distributed systems, API design, database design, production debugging | Backend track sections 1 to 10, every question answered verbatim, plus a part 4 for topics the list leaves out |
| Codebasics AI Engineering Bootcamp for Software Engineers (public curriculum page) | 12 weekends: Python and LLM APIs, embeddings and RAG with Qdrant, LangChain and advanced RAG (hybrid, SQL, graph), agents and LangGraph, multi-agent and evals, multimodal and AWS deployment, MCP and context and harness engineering, fine-tuning with LoRA/QLoRA and synthetic data, AI product thinking and security (OWASP for AI, semantic caching, routing), system thinking and voice AI, inference engineering with vLLM; six projects including an eval harness, an IT helpdesk agent with MCP, a voice agent and an inference router | The AI thread sequence, the harness and context engineering sections, the voice section, and the inference router project |
| Maven trending AI courses (public listing) | AI Evals for Engineers and PMs (Hamel Husain, Shreya Shankar), AI-Powered Search: modern retrieval (Trey Grainger, Doug Turnbull), The AI Engineering Bootcamp (AI Makerspace), several agentic AI certifications | The weight given to evaluation and retrieval quality, and the "look at your data" style of evals |
| BuildLifeAndAI course site | Email-gated signup page; the course content itself was not accessible | Not used beyond the PDF |

### Reference reading, one per track
- Backend: Postgres documentation chapters on indexes and MVCC; "Designing Data-Intensive Applications" chapters on replication, partitioning, transactions and consistency.
- Frontend: the official React documentation (react.dev) "Learn" and "Reference" sections; the Next.js App Router documentation.
- LLMs and RAG: the OpenAI and Anthropic API guides on structured outputs, tool use and prompt caching; the RAGAS documentation for metric definitions.
- Agents: Anthropic's "Building effective agents" and its context engineering guide; the Model Context Protocol specification.
- Inference: the vLLM documentation and the PagedAttention paper summary.
- Fine-tuning: Hugging Face PEFT and TRL documentation; the Unsloth notebooks.
- MLOps and LLMOps: Google's "MLOps: continuous delivery and automation pipelines" article; Langfuse or LangSmith documentation.
- DevOps: Kubernetes concepts documentation; the GitHub Actions documentation; the Twelve-Factor App.
- Cloud: the AWS Well-Architected Framework; the AWS architecture center reference architectures.
