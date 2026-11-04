# Instagram saves digest (19 posts, scraped 2026-10-30)

Method: captions from Instagram embed pages, video audio transcribed with faster-whisper (small.en), on-screen text read from video frames (tesseract OCR plus visual checks), carousel images downloaded and read slide by slide, referenced sites and repos opened where possible. Raw media and transcripts live in the session scratchpad and are not kept here.

| # | Post | Creator | Format | Topic | Atlas home |
|---|---|---|---|---|---|
| 1 | DfFWuGOo7gu | vishakha.sadhwani | reel 140 s | Three levels of inference engineering | Inference: "Inference Engineering Levels" + Explained Simply |
| 2 | Davl73gikI- | bashi_fuirkashi | reel 75 s | Roadmap to become an AI engineer, with named resources | Roadmap: Resource Library |
| 3 | DdvYzlzR8Mp | unknown | blocked | Age-restricted to signed-in viewers; caption, video and creator not accessible logged out | Skipped at the user's request (2026-10-30) |
| 4 | DepBhJtBUCJ | pvergadia | reel 18 s + caption | 12 skills for each of 5 AI roles, with US base-pay bands | Roadmap: AI Career Paths |
| 5 | DeiEOjfMczf | lindavivah | reel 113 s | Build your own inference engine in 6 steps (Akamai workshop repo, vLLM, Qwen) | Inference: levels section, lab + Practice |
| 6 | De6Zy2Yohlg | anay.tech | reel 18 s + caption | 7 AI system design patterns asked in AI engineering interviews | LLMs/RAG/Evals: "AI System Design Patterns" + Explained Simply |
| 7 | De0tBlRSudZ | aiwithanju | reel 15 s (music) + caption | 10 agentic concepts to master before AI interviews | Agents (sync) + Explained Simply |
| 8 | DeQ0dE2AWSg | aiwithanju | reel 24 s + caption | 7 AI projects to build in 2026 | Roadmap: Project Ideas |
| 9 | DW6suHYCFS7 | jam.with.ai | carousel, 6 images | AI/ML interviews: design under pressure; 4 Exponent (now Aced) YouTube playlists | Backend: SQL section + system design sync; LLMs/RAG/Evals: ML System Design; Roadmap: Resource Library |
| 10 | Dd9PsJupt1m | vishakha.sadhwani | reel 19 s + caption | Production AI stack: one resource per area | LLMOps: AIOps & Platform Engineering; Roadmap: Resource Library |
| 11 | De1HTNOp08x | skdneuron | reel 17 s + caption | 15 LLM fine-tuning techniques | Fine-tuning: "The 15 Fine-tuning Techniques" + Explained Simply |
| 12 | DeMsE3ogcNb | jam.with.ai | reel 169 s | Inference engineering concepts as problem then technique | Inference (sync) + Explained Simply |
| 13 | De1vGbYguMQ | jam.with.ai | reel 46 s | 12-week roadmap, 4 projects, free resources, AI engineer skills list | Roadmap: Skills Checklist, Projects, Resources |
| 14 | DdCvFdHsnj1 | soojintech | reel 58 s | AI Advent Calendar: 9 fundamentals explained simply | Explained Simply: AI Fundamentals |
| 15 | Dej-qERh5dm | pvergadia | reel 6 s (music) + caption | AI Engineering 101: 7 talks, one per day | Roadmap: Resource Library |
| 16 | DeJpwdCoJQx | kevinnaughtonjr | reel 9 s (music) + caption | 7 videos on how AI systems are really built | Roadmap: Resource Library; Agents sync |
| 17 | Deh5j5py8uW | codev.ai | reel 13 s + caption | 10 agentic AI concepts, one line each | Agents (sync) + Explained Simply |
| 18 | DejhYvKDTYT | iiterate_technologies | reel 57 s | Floorplan AI: drawing to structured data with computer vision | LLMs/RAG/Evals: "Computer Vision & Document AI" |
| 19 | DeeJJ9BFIxM | gittrend.io | reel 30 s | Desigma, a free offline design tool that opens Figma files | Roadmap: Resource Library (tools) |

## Post details

### 1. Three levels of inference engineering (vishakha.sadhwani)
- Level 1, AI infrastructure fundamentals: builds on cloud, DevOps and ML foundations. Running LLM APIs, application deployments, GPU-based Kubernetes clusters, open-weight versus foundation (closed) models, ML workloads: pre-training, post-training, inference. Exit by building an AI infrastructure project (deploy a model locally) or a course such as NVIDIA's AI Infrastructure and Operations.
- Level 2, understanding inference: transformer architecture, prefill and decode, KV cache memory management; engines vLLM, SGLang, TensorRT-LLM and how they manage memory and KV-cache reuse; serving patterns aggregated versus disaggregated; Kubernetes as the point where scaling and scheduling AI workloads meet. Exit through hands-on practice: deploy on a GPU cluster, try serving patterns, measure how choices change performance.
- Level 3, optimizing inference: observability and benchmarking; metrics TTFT, TPOT, throughput, end-to-end latency, inter-token latency; request-level optimizations (continuous batching, speculative decoding, chunked prefill); model compression (quantization, distillation); parallelism strategies. Stay successful by building a benchmarking project: vary configurations, measure TTFT, throughput, GPU utilization and latency, optimize from measurements.

### 2. AI engineer roadmap (bashi_fuirkashi)
Fundamentals first because tools change every few months: Andrej Karpathy "Neural Networks: Zero to Hero" plus 3Blue1Brown neural network series. Core of the job is RAG and agents: LangChain "RAG from scratch" series; pick one orchestration framework and go deep (LangGraph suggested) plus the Hugging Face Agents course. Books: Chip Huyen "AI Engineering"; "Building Applications with AI Agents" (Michael Albada). Build: first AI service with FastAPI, containerize with Docker, put behind a real API.

### 4. Five AI roles, 12 skills each (pvergadia)
- AI Engineer (US base pay shown in post, not legible in all frames): Python, LLMs and APIs, Prompt Engineering, RAG Architecture, Vector Databases, AI Agents, LangChain or LlamaIndex, FastAPI, Evaluation and Evals, Fine-Tuning, Docker and Cloud, MLOps.
- Forward Deployed Engineer (US base pay shown: $150,000 to $280,000): Python, System Design, APIs and Integration, SQL, LLMs and Prompt Engineering, RAG and Agents, Fast Prototyping, Customer Communication, Executive Storytelling, Business Acumen, Cloud Basics, Technical Documentation.
- AI Product Manager: AI and LLM Fundamentals, Prompt Engineering, Evaluation Metrics, Product Strategy, User Research, SQL and Data Analysis, Roadmap Planning, Stakeholder Communication, Executive Storytelling, AI Ethics and Governance, ROI Measurement, Agent Workflow Design.
- Data Engineer (US base pay shown: $120,000 to $175,000): Python or Scala, SQL, Apache Spark, Kafka, Airflow, dbt, Data Warehousing, ETL and ELT Pipelines, Delta Lake or Iceberg, Feature Stores, Cloud Data Platforms, Data Quality Testing.
- AI Solutions Architect: Cloud Architecture, LLMs and GenAI, RAG and Agent Design, System Design at Scale, API and Microservices, Security and Compliance, Cost Optimization, Multi-Cloud Strategy, MLOps and LLMOps, Executive Communication, Technical Storytelling, Enterprise Integration.
- Message: pick the role, identify the skills it rewards, build around that stack; the goal is to build, solve problems, communicate and deliver outcomes, not to collect certifications.

### 5. Build your own AI inference engine in 6 steps (lindavivah; Akamai Developers)
Steps: 1 get a GPU (Terraform builds a Kubernetes cluster with a GPU node, roughly 50 cents an hour per the post); 2 deploy vLLM serving Qwen (open weights); 3 port-forward a private tunnel to the cluster; 4 point existing code at it by swapping the base URL of an OpenAI-compatible client, tokens stream from your own GPU; 5 load test and watch the KV cache fill and continuous batching keep the GPU busy; 6 deploy an agent on your own inference. Why: cost, privacy, control, and learning what is under the hood.
Verified repo: https://github.com/akamai-developers/akamai-workshop-ai-inference (Apache-2.0). Modules: 0 connection check; 1 to 4 the stack, GPU memory budgeting, prefill/decode and KV cache, dense versus MoE; 5 to 8 quantization (BF16 versus FP8), speculative decoding, engine saturation, tuning; 9 deploy an agent on the endpoint. Uses vLLM Prometheus /metrics to observe batching, queueing and saturation. Default model Qwen/Qwen3-4B. The post also mentions an "Edge Case" Discord and Akamai cloud credits (not verified).

### 6. Seven AI system design patterns (anay.tech, says from a senior-engineer job switch)
Observability (track LLM calls, latency, cost, failures); Caching (cut response time and API cost); Agentic evals (test tool selection, reasoning, outcomes); RAG (ground answers in your data); Fine-tuning (when prompting or RAG is not enough); User feedback loops (improve with feedback and corrections); Guardrails (block unsafe and incorrect responses). Message: do not skip system design.

### 7 and 17. Ten agentic concepts (aiwithanju list; codev.ai one-liners)
1 Harness engineering: the environment the agent acts inside (sandbox, file system, runtime surface). 2 Loop engineering: when the agent runs again and when it stops. 3 Context engineering: right information in the window, wrong information out. 4 Tool design: the agent is only as capable as its tools and only as safe as their worst edge case. 5 Memory architecture: what it remembers, for how long, what it may forget. 6 Orchestration patterns: one agent, a planner, or a swarm; each fails differently. 7 Guardrails and permissions: what happens when the agent tries something it should not. 8 Evals for agents: you cannot test a trajectory like a function. 9 Human-in-the-loop design: which decisions never get delegated. 10 Observability and tracing: when it breaks at step 14 of 30 you need to see step 14. Claim: most people are stuck on 3 and 4; the gap between a demo and a system is 7 to 10.

### 8. Seven AI projects (aiwithanju)
MCP-powered AI assistant; multi-agent orchestration system; AI evaluation pipeline; secure RAG system with guardrails; AI agent with audit logs; fine-tuned open-source LLM; knowledge-graph-powered AI.

### 9. Crack your next AI/ML interview (jam.with.ai carousel, 6 slides)
Message: Kaggle rank, GitHub stars, courses and certificates matter less than designing systems under pressure on a whiteboard in 45 minutes. Four YouTube playlists by Exponent (channel now "Aced, formerly Exponent", https://www.youtube.com/@aced_io):
- System Design Interview Prep (44 videos): mock interviews and walkthroughs; design Google Docs, Uber Eats, key-value store, distributed LRU cache, web crawler; API design, scalability, database architecture choices.
- Machine Learning Interview Prep (27 videos): ML system design end to end with engineers from Google, Waymo, Meta; recommendation systems, ranking, embeddings, deployment; ML coding and ML concepts.
- Data Science Interview Prep (15 videos): case studies, A/B testing, metrics, product analytics, mock interviews with FAANG data scientists.
- SQL Interview Prep (8 videos): hands-on SQL problems (most user orders, analyzing marketing channels, upsell campaign impact, departments with highest revenue), query optimization.

### 10. Build the production stack (vishakha.sadhwani)
Areas: RAG and fine-tuning, MLOps and LLMOps, inference and deployment, cloud and Kubernetes, DevOps and AIOps, observability and platform engineering. One resource per area shown on screen:
- Inference: "AI Inference: The Secret to AI's Superpowers" (IBM Technology); "AI Inference Crash Course: Master AI Engineering in 20 Minutes" (Vishakha Sadhwani).
- Training: "How to train AI ML models? Full pipeline in 15 mins".
- Observability: "Observability Zero to Hero" (Abhishek Veeramalla, about 11 hours).
- MLOps: "Machine Learning Engineering for Production (MLOps)" (DeepLearning.AI).
- LLMOps: "End to End Advanced RAG Project, LLMOps, FAISS" playlist (Sunny Savita, 14 videos).
- AIOps: "Automating DevOps with AI: End-to-End DevOps + AIOps Project" series (Vishakha Sadhwani, 5 videos).
- Fine-tuning: "Fine Tuning LLM Models, Generative AI Course" (freeCodeCamp).
- RAG: "RAG Crash Course for Beginners" (KodeKloud).
- Model deployment: "DevOps + LLM + AI Project with Docker, Kubernetes, vLLM" (Vishakha Sadhwani).
- Platform engineering: "What is Platform Engineering and how it fits into DevOps and Cloud world" (TechWorld with Nana).
- Cloud: "Become a Cloud Engineer in 2026" and "5 Resume Projects for Cloud and DevOps" (Vishakha Sadhwani).
- Kubernetes: "The Only Kubernetes Course You'll Ever Need", "Kubernetes for AI: Zero to Hero", "Kubernetes Security Best Practices in 12 Minutes" (Vishakha Sadhwani).
- DevOps: "The New Era of DevOps Engineering", "All DevOps Concepts Explained in 25 Minutes" (Vishakha Sadhwani).

### 11. Fifteen fine-tuning techniques (skdneuron)
SFT; full fine-tuning (FFT); PEFT; LoRA; QLoRA; DoRA; adapters; prompt tuning; prefix tuning; P-tuning; RLHF; PPO; RLAIF; DPO; ORPO. Grouping from the caption: SFT teaches by example; PEFT methods (LoRA, QLoRA, DoRA, adapters) train a small set of weights; prompt tuning, prefix tuning and P-tuning learn soft prompts; RLHF, PPO, RLAIF, DPO, ORPO align a model with preferences.

### 12. AI inference engineering, one problem at a time (jam.with.ai)
Story of an AI docs assistant on one GPU: one user, prefill processes the question, decode generates token by token, the KV cache stores earlier keys and values. Fifty users share one copy of weights but each conversation needs its own cache, longer chats need more memory. Reserving big fixed memory per request wastes space, so allocate small cache blocks on demand: PagedAttention (one reason vLLM uses memory efficiently). Answers finish at different times: continuous batching lets finished requests leave and waiting ones join between steps. A long pasted document delays everyone's next token: chunked prefill processes the prompt in pieces alongside ongoing decodes. Every request starts with the same system instructions: prefix caching reuses cached work when the starting tokens match exactly. Weights too large: quantization stores them in fewer bits, saves memory, must check quality, speed depends on model, hardware and format. Generation still slow: speculative decoding, a cheaper draft model proposes tokens and the main model checks them together, helps when enough guesses are accepted. Measure time to first token and gaps between tokens (latency) and tokens per second across all users (throughput).

### 13. 12-week roadmap, 4 projects (jam.with.ai)
- Skills list shown ("AI engineers" versus "vibe coding"): Python, APIs and JSON, async programming, data validation, structured outputs, prompt engineering, context windows, context engineering, model selection, unit tests, dependency injection, document ingestion, chunking strategies, embeddings, vector search, keyword search, hybrid search, reciprocal rank fusion, HNSW indexes, similarity metrics, grounded answers, source citations, knowledge graphs, ontology design, entity relationships, conversation history, working memory, long-term memory, memory retrieval, memory updates, memory expiry, user-scoped memory, checkpointed state, scheduled follow-ups, agent orchestration, tool calling, MCP servers, agentic RAG, query rewriting, workflow routing, state management, step limits, human approval, tool result validation, model routing, provider fallbacks, AI evaluations, evaluation datasets, retrieval quality, answer quality, grounding checks, regression tests, prompt versioning, model comparisons, trace debugging, error analysis, quality-cost tradeoffs, production monitoring, authentication, authorization, document permissions, tool permissions, prompt injection tests, secrets management, idempotency, API gateways, rate limiting, message queues, circuit breakers, CI/CD, prefill and decode, KV cache, PagedAttention, continuous batching, chunked prefill, prefix caching, quantization, speculative decoding, latency and throughput, caching.
- Weeks 1 to 3: Python, APIs, testing (PyTest unit and REST API integration testing), SQL; build a news summarizer.
- Weeks 4 to 6: how LLMs work (Hugging Face LLM course), build a RAG app (Jam with AI "Build a local LLM-based RAG system for your personal documents").
- Weeks 7 to 9: deploy it (FastAPI tutorials, Docker deployment) and turn it into a production agent ("How a production AI agent system actually works").
- Weeks 10 to 12: memory, tools and voice; MCP servers course (Model Context Protocol with Python); build a voice agent and track quality and cost. Repo shown: https://github.com/jamwithai/observable-job-agent (Job Scout: CV upload, job search agent, fit scoring, CV tailoring grounded in a typed corpus with a zero-LLM fabrication validator, evals from traces with LLM judges and a deterministic gate, optional voice console over WebRTC, Opik tracing with per-run cost; LangGraph, FastAPI, Next.js, ElevenLabs).

### 14. AI Advent Calendar (soojintech, built with Replit)
Site: https://ai-advent-calendar.replit.app (9 windows, lessons at /lesson/<topic>). Concepts: models, tokens, context window, inference, embeddings, semantic search, RAG, tool calling, MCP. Framing from the build chat: think of an AI assistant as a smart employee; the model is the brain, inference is thinking about a request, tokens are the pieces of text read and written, the context window is the size of the notepad, embeddings and semantic search help find relevant information, RAG gives that information before answering, tool calling lets them take actions, MCP is a standard way to connect them to tools and data. RAG analogy from the video: Bob knows general facts (how big is Central Park) but not where your company's IT desk is until you give him the company documents to search. Lesson format: in plain English, how it works in 3 steps, real-world uses, an analogy (tokens: "Unforgettable!" is 4 tokens, not 1 word).

### 15. AI Engineering 101, a talk a day (pvergadia)
Monday: Nick Saraev, "What I'd Learn Instead of Automation in 2026". Tuesday: "A Practical Guide to Becoming an AI Engineer". Wednesday: Andrej Karpathy, "Deep Dive into LLMs like ChatGPT". Thursday: "Andrej Karpathy: From Vibe Coding to Agentic Engineering" (AI Ascent). Friday: Greg Isenberg, "Why Graph Engineering will 10x your Claude..." (title truncated on screen). Saturday: Mario Zechner, "Building pi in a World of Slop". Sunday: "Building Great Agent Skills: The Missing Manual" (mattpocock/skills).

### 16. Seven videos (kevinnaughtonjr, "I am not smart enough for AI engineering")
"12-Factor Agents: Patterns of reliable LLM applications" (Dex Horthy, HumanLayer, AI Engineer); "No Vibes Allowed: Solving Hard Problems in Complex Codebases" (Dex Horthy); "How We Build Effective Agents" (Barry Zhang, Anthropic); "Don't Build Agents, Build Skills Instead" (Barry Zhang and Mahesh Murag, Anthropic); "Building and evaluating AI Agents" (Sayash Kapoor, AI Snake Oil); "Carrying Out Error Analysis" (Andrew Ng, DeepLearning.AI); "Beating RL With Reflection: GEPA and Optimize Anything" (Lakshya A. Agrawal).

### 18. Floorplan AI (iiterate technologies)
Floor plans come as sketches, scans, CAD, brochures, many languages; manual digitizing is slow and error prone. Pipeline: upload image or PDF; a vision transformer segments the plan into rooms; edge extraction traces walls; corner detection finds where walls meet; output clean closed polygons with coordinates per room as structured data. Claims (from the company): under 4 seconds, trained on 100,000+ examples, 20+ floor plan types across styles, resolutions and languages.

### 19. Desigma (gittrend.io)
Free, open-source, offline design tool written in Rust; native renderer (no Electron); imports Figma REST JSON and .fig files with components, styles and prototype links; component instances update together; handoff view generates code; early alpha. Repo: https://github.com/deepfounder-ai/desigma (MIT or Apache-2.0).
