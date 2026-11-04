# Explained Simply

> Every big term from the atlas and from your saved Instagram posts, explained in plain words first: what it is, an everyday picture, one real example, and one precise line to say in an interview. Use this track to make an idea click, then follow each card's "Go deeper" pointer into the Inference, LLMs RAG & Evals, Agents, MLOps & LLMOps and Fine-tuning tracks, where the full interview answers, follow-ups and failure modes live.

## AI Fundamentals in Plain Words [Basics]

> Interviewers often open with "explain RAG to a product manager" or "what actually happens when you call the API?". A weak answer recites buzzwords. A strong answer gives one clean picture, then drops to the mechanism (tokens, context limits, retrieval, tool calls) without losing the listener. These nine cards are that picture.

### In plain words
Picture an AI assistant as a smart new employee. The model is the employee's brain: it has read a huge amount, but it knows nothing about your company. Inference is the employee thinking about a request and writing a reply, tokens are the small pieces of text they read and write, and the context window is the size of their notepad, because whatever does not fit on it, they cannot see. Embeddings and semantic search help them find the right page by meaning, and RAG means handing them the right documents before they answer. Tool calling lets them take actions, like looking up an order, and MCP is a standard plug that connects them to any tool or data source.

### From your saved posts
- soojintech: AI Advent Calendar, nine AI fundamentals (models, tokens, context window, inference, embeddings, semantic search, RAG, tool calling, MCP) explained simply through the "smart employee" picture, built with Replit. Site: https://ai-advent-calendar.replit.app

### C. Models
**In one line:** A model is a large file of learned numbers (weights) that predicts what text should come next.

**Think of it like:** The smart employee's brain: well read and fluent, but it has never seen your company's files.

**Example:** GPT, Claude and Gemini are closed models you call over an API. Llama and Qwen are open-weight models you can download and run on your own GPU with vLLM.

**Say it in an interview:** An LLM is a transformer trained to predict the next token; post-training such as instruction tuning and preference alignment turns it into a helpful assistant. I pick a model per task on quality, latency, cost and data residency, and keep it behind an interface so I can swap providers.

**Go deeper:** LLMs, RAG & Evals track, section "How LLMs Work, for Engineers".

### C. Tokens
**In one line:** Tokens are the small chunks of text a model reads and writes: whole words, word pieces, punctuation or spaces.

**Think of it like:** The employee reads in syllable-sized pieces, and you pay for every piece read and every piece written.

**Example:** The Advent Calendar lesson shows one word like "Unforgettable!" splitting into several tokens. A rough rule for English is about four characters per token.

**Say it in an interview:** Each model family has its own tokenizer, usually a byte-pair-encoding variant, so the same prompt has different token counts on different providers. I count with the provider's tokenizer or token-counting endpoint, because cost, latency and context limits all scale with tokens, and output tokens usually cost more than input.

**Go deeper:** LLMs, RAG & Evals track, section "How LLMs Work, for Engineers".

### C. Context Window
**In one line:** The context window is the most tokens a model can handle in one call, counting prompt, history, documents and its own reply.

**Think of it like:** The employee's notepad. What is not on it, they cannot see; when it is full, something gets erased.

**Example:** A support bot that resends the whole chat every turn eventually hits the limit. The fix: summarize old turns, keep recent ones in full, and retrieve only relevant documents.

**Say it in an interview:** It is a hard budget shared by input and output, and quality can drop well before the limit because models use information in the middle of long contexts less reliably. I budget it explicitly: system prompt, retrieved chunks, history and reserved output, each capped.

**Go deeper:** LLMs, RAG & Evals track, section "How LLMs Work, for Engineers".

### C. Inference
**In one line:** Inference is running an already trained model to produce an answer; training is when the model learns.

**Think of it like:** Training is the employee's years of education. Inference is answering one question at their desk today.

**Example:** Every chat completion API call is an inference request. Run Qwen on your own GPU with vLLM and inference becomes your job: GPU memory, batching and streaming speed.

**Say it in an interview:** Inference has two phases: prefill reads the whole prompt in parallel and produces the first token, then decode generates one token at a time using a KV cache. Prefill drives time to first token, decode drives streaming speed, and the serving engine keeps the GPU busy across users within the latency budget.

**Go deeper:** Inference track, section "Inference Fundamentals".

### C. Embeddings
**In one line:** An embedding is a list of numbers (a vector) capturing the meaning of a text, so similar meanings sit close together.

**Think of it like:** Giving every page a map coordinate by topic, so "refund policy" and "how do I get my money back" land in the same neighborhood despite sharing no words.

**Example:** Run each document chunk through an embedding model such as OpenAI's text-embedding-3-small, store vectors in Postgres with pgvector, and embed each query with the same model.

**Say it in an interview:** Embeddings come from a separate encoder model, and queries and documents must use the same model and version or the vectors are not comparable. Changing models means re-embedding the corpus, so I store the model version next to every vector.

**Go deeper:** LLMs, RAG & Evals track, section "Embeddings & Vector Search".

### C. Semantic Search
**In one line:** Semantic search finds results by meaning: embed the query, then return the stored items whose vectors are closest.

**Think of it like:** Asking a librarian for "something about getting money back" and getting the refunds page, not just pages with those exact words.

**Example:** With pgvector, `ORDER BY embedding <=> $1 LIMIT 5` returns the five chunks closest by cosine distance, and an HNSW index keeps it fast as data grows.

**Say it in an interview:** At scale it uses approximate nearest-neighbor indexes such as HNSW, trading a little recall for speed. Vectors miss exact identifiers like error codes or SKUs, so in production I run hybrid search, BM25 plus vectors merged with reciprocal rank fusion, and add a reranker when precision matters.

**Go deeper:** LLMs, RAG & Evals track, section "Embeddings & Vector Search".

### C. RAG
**In one line:** Retrieval-augmented generation (RAG) finds relevant documents first and puts them in the prompt, so the model answers from your data.

**Think of it like:** Bob, the smart new hire, knows how big Central Park is but not where your IT desk is. Give him the company documents and he can answer.

**Example:** An HR bot embeds "how many casual leaves do I get?", retrieves the top leave-policy chunks, and answers only from them, with citations.

**Say it in an interview:** RAG is a retrieval pipeline plus generation: chunk, embed, retrieve (often hybrid plus rerank), then answer with citations. Most bad answers are retrieval failures, so I measure recall at k separately from faithfulness, and enforce document permissions at retrieval time, never in the prompt.

**Go deeper:** LLMs, RAG & Evals track, section "RAG Fundamentals".

### C. Tool Calling
**In one line:** Tool calling lets the model ask your code to run a function, like looking up an order, and use the result.

**Think of it like:** The employee cannot touch the warehouse system but can fill in a request slip ("check order 1042") that you run and hand back.

**Example:** You describe `get_order_status(order_id)` with a JSON Schema. The model returns `{"order_id": "1042"}`, your Node.js server validates it, queries MongoDB, returns the result, and the model writes the reply.

**Say it in an interview:** The model never executes anything; it emits a structured request and my code decides whether to run it. That boundary holds argument validation, authorization against the end user, timeouts, idempotency keys for writes, and an iteration cap.

**Go deeper:** Agents track, section "Agent Fundamentals".

### C. MCP
**In one line:** The Model Context Protocol (MCP) is an open standard for connecting AI apps to tools and data, so one integration works everywhere.

**Think of it like:** USB-C for AI: every tool exposes the same plug, every assistant has the same socket.

**Example:** A GitHub MCP server exposes tools such as creating an issue, and Claude Desktop, Claude Code or your own agent can use it without GitHub-specific glue code.

**Say it in an interview:** MCP, introduced by Anthropic, runs JSON-RPC between a client in the host app and servers exposing tools, resources and prompts, over stdio locally or HTTP remotely. It standardizes plumbing, not safety: I still scope OAuth tokens, allowlist tools, and treat tool output as untrusted because of prompt injection.

**Go deeper:** Agents track, section "MCP & Tool Ecosystems".

## How Inference Works, One Problem at a Time [Core]

> Inference questions separate candidates quickly. A weak answer says "use a bigger GPU". A strong answer names the bottleneck first (compute, memory bandwidth, memory capacity or scheduling), then the technique that removes it and the metric that proves it worked. Every card here follows that shape: a problem, then its fix.

### In plain words
Imagine you built a docs assistant on one GPU. With one user it is simple: the model reads the question (prefill), then writes the answer one token at a time (decode), keeping notes on what it already read (the KV cache) so it never rereads everything. Then 50 users arrive: they share one copy of the model, but each conversation needs its own notes, so memory is handed out in small pages only when needed (PagedAttention). Answers finish at different times, so finished requests leave and waiting ones join at every step (continuous batching); a huge pasted document would stall everyone, so it is read in chunks (chunked prefill); and everyone shares the same system prompt, so that work is reused (prefix caching). If the model is still too big or too slow, you shrink the weights (quantization) or let a small model guess ahead (speculative decoding), and you measure latency and throughput to know whether any of it helped.

### From your saved posts
- jam.with.ai: AI inference engineering, one problem at a time, the story of a docs assistant growing from one user to 50 on a single GPU, with each new problem met by one technique.
- vishakha.sadhwani: three levels of inference engineering: infrastructure fundamentals; understanding inference (prefill and decode, KV cache, vLLM, SGLang, TensorRT-LLM, aggregated versus disaggregated serving); and optimizing it (TTFT, TPOT, throughput, continuous batching, chunked prefill, speculative decoding, quantization).

### C. Prefill
**In one line:** Prefill is the first phase of a request: the model reads the whole prompt at once and produces the first output token.

**Think of it like:** Reading the entire customer email before typing the first word of your reply.

**Example:** A 6,000-token prompt (instructions plus retrieved docs) is processed in one parallel pass. The user sees nothing until it finishes, so longer prompts mean a longer wait for the first word.

**Say it in an interview:** Prefill processes all prompt tokens in parallel, so it is compute-bound and its cost grows with prompt length; it also fills the KV cache for every prompt token. It dominates time to first token, which is why trimming context, prefix caching and chunked prefill are the TTFT levers.

**Go deeper:** Inference track, section "Inference Fundamentals".

### C. Decode
**In one line:** Decode is the second phase: the model generates the answer one token at a time, each depending on all tokens before it.

**Think of it like:** Writing a reply word by word, rereading what you have so far before choosing each next word.

**Example:** A 400-token answer needs 400 sequential decode steps. That is the streaming you watch in a chat UI, and the gap between words is decode speed.

**Say it in an interview:** Decode is memory-bandwidth-bound: each step reads all the weights plus the KV cache to produce one token per sequence, so a single request leaves most GPU compute idle. Batching many sequences into each step recovers that compute, and decode speed sets time per output token.

**Go deeper:** Inference track, section "Inference Fundamentals".

### C. KV Cache
**In one line:** The KV cache stores attention keys and values already computed for earlier tokens, so each decode step only computes the new token.

**Think of it like:** Sticky notes on what you have already read, so you never reread the whole thread before writing the next word.

**Example:** Each of the docs assistant's 50 chats keeps its own KV cache in GPU memory. Weights are a fixed cost, but caches grow with every user and every token, so they run out first under load.

**Say it in an interview:** The KV cache trades memory for compute; its size grows linearly with sequence length, batch size, layer count and KV heads. It usually caps concurrency, which is why grouped-query attention, KV cache quantization and paged allocation exist.

**Go deeper:** Inference track, section "Inference Fundamentals".

### C. PagedAttention
**In one line:** PagedAttention stores the KV cache in small fixed-size blocks handed out on demand, not one big chunk reserved per request.

**Think of it like:** A hotel giving each guest one more room only when needed, instead of blocking a whole floor per guest just in case.

**Example:** Reserving space for the maximum output length wastes most of it on short answers. With paged blocks, memory is claimed as tokens are produced, so more requests fit. It was introduced with vLLM.

**Say it in an interview:** It borrows virtual-memory paging from operating systems: a block table maps each sequence's logical KV blocks to physical blocks anywhere in GPU memory. Waste shrinks to the last, partly filled block per sequence, raising concurrency and letting requests share common-prefix blocks.

**Go deeper:** Inference track, section "Serving Engines & Stacks".

### C. Continuous Batching
**In one line:** Continuous batching lets requests join and leave the running batch at every generation step, not waiting for the whole batch to finish.

**Think of it like:** A bus that lets passengers on and off at every stop, rather than one that waits until everyone reaches the last stop.

**Example:** A 20-token answer and a 900-token answer run together. With static batching the short one's slot idles until the long one ends; with continuous batching a waiting user takes it next step.

**Say it in an interview:** Also called iteration-level or in-flight batching, the scheduler re-forms the batch every step, admitting queued requests as KV memory frees. It is a core reason vLLM, SGLang and TensorRT-LLM beat naive serving on throughput, while per-token latency rises as batches grow.

**Go deeper:** Inference track, section "Serving Engines & Stacks".

### C. Chunked Prefill
**In one line:** Chunked prefill splits a long prompt into pieces processed alongside other users' decode steps, so one huge prompt does not freeze everyone.

**Think of it like:** A cashier scanning a giant trolley ten items at a time, serving the "just a coffee" customers in between.

**Example:** A user pastes a 50-page contract. Without chunking, that prefill runs in one go and every other stream pauses; with chunking, it is spread over several steps mixed with ongoing decodes.

**Say it in an interview:** It caps the tokens processed per scheduler step and mixes prefill chunks with decode tokens in one batch. That smooths inter-token latency for running requests and improves GPU utilization, at the cost of a somewhat longer time to first token for the long prompt.

**Go deeper:** Inference track, section "Speed-ups Beyond Batching".

### C. Prefix Caching
**In one line:** Prefix caching reuses the KV cache of a prompt opening an earlier request already processed, so shared work is skipped.

**Think of it like:** Every email starts with the same company policy, so you read it once, keep your notes, and read only each customer's new part.

**Example:** Every docs-assistant request starts with the same 2,000-token system prompt, so only the question needs fresh prefill. Hosted APIs offer this as prompt caching, billing cached input at a discount.

**Say it in an interview:** It needs an exact token match from the start of the prompt, so I put static content first (system prompt, tool definitions, examples) and variable content last; a timestamp at the top breaks every hit. Prefix-aware routing sends similar requests to the replica holding the cache.

**Go deeper:** Inference track, section "Speed-ups Beyond Batching".

### C. Quantization
**In one line:** Quantization stores weights (sometimes activations or KV cache too) in fewer bits, such as 8 or 4 instead of 16, to use less memory.

**Think of it like:** Saving a photo as a smaller JPEG: it usually looks the same, but push too far and details blur.

**Example:** Weights take 2 bytes per parameter in BF16 and 1 byte in FP8 or INT8, so an 8B model drops from about 16 GB to about 8 GB, freeing memory for KV cache.

**Say it in an interview:** Quantization cuts memory and, since decode is bandwidth-bound, often speeds it up, but gains depend on hardware support for the format and the kernels. Accuracy loss varies by model and method (GPTQ, AWQ, FP8), so I re-run my own evals before shipping.

**Go deeper:** Inference track, section "Quantization".

### C. Speculative Decoding
**In one line:** A small draft model guesses the next few tokens, and the big model checks them all in one pass, keeping the ones it agrees with.

**Think of it like:** A junior drafts a few words; the senior checks them at a glance and fixes the first wrong one.

**Example:** A draft model proposes 4 tokens. If the big model accepts the first 3, it supplies the fourth itself, so one big-model pass yields 4 tokens instead of 1.

**Say it in an interview:** With the standard acceptance rule the output distribution matches the big model alone, so quality is unchanged and only speed changes. It pays off when acceptance is high and the GPU has spare compute, typically at low batch sizes, and can hurt throughput under heavy load.

**Go deeper:** Inference track, section "Speed-ups Beyond Batching".

### C. Latency vs Throughput
**In one line:** Latency is how long one user waits; throughput is total work done for everyone, and pushing one usually costs the other.

**Think of it like:** Latency is how fast your plate arrives; throughput is plates served per hour across the restaurant.

**Example:** Time to first token (TTFT) is the wait for the first word. Time per output token (TPOT) averages the gaps between later tokens; inter-token latency (ITL) is each gap. Tokens per second across all users is throughput.

**Say it in an interview:** I set SLOs on p95 TTFT and TPOT, then maximize throughput within them, which is goodput. Bigger batches raise throughput but stretch per-token latency, so I tune concurrency limits against the SLO with a realistic load test.

**Go deeper:** Inference track, section "Inference Fundamentals".

### C. Aggregated vs Disaggregated Serving
**In one line:** Aggregated serving runs prefill and decode on the same GPUs; disaggregated serving uses separate GPU pools and moves the KV cache between them.

**Think of it like:** One chef who preps and plates every dish, versus separate prep and plating stations.

**Example:** A RAG product with long prompts and short answers is prefill-heavy, so prefill gets its own GPUs and ships KV caches to decode GPUs over a fast interconnect. NVIDIA Dynamo and llm-d are built around this.

**Say it in an interview:** Prefill is compute-bound and decode is bandwidth-bound, so on shared GPUs a big prefill stalls everyone's decode. Disaggregation removes that interference and scales each pool independently, at the cost of KV transfer, more complex routing and a higher minimum scale.

**Go deeper:** Inference track, section "Scaling, Routing & Load Balancing".

### C. GPU Memory Budget
**In one line:** GPU memory holds weights plus KV cache plus overhead, and what is left after weights decides how many users fit at once.

**Think of it like:** Packing a suitcase: the big jacket (weights) goes in first, then you count how many shirts (conversations) fit in the rest.

**Example:** An 8B model in BF16 takes about 16 GB of an 80 GB GPU. After activations and runtime overhead, the rest becomes the KV cache pool; vLLM's `gpu_memory_utilization` caps the total it claims.

**Say it in an interview:** Weights are parameters times bytes per parameter. KV cache per token is 2 (keys and values) times layers times KV heads times head dimension times bytes per element. Free memory divided by that gives total tokens in flight, which caps concurrency times context length.

**Go deeper:** Inference track, section "Inference Fundamentals".

## The 10 Agentic Concepts [Core]

> These ten come from two saved posts listing what to master before AI interviews. Their claim: most people stop at context engineering and tool design, but the gap between a demo and a system is guardrails, evals, human-in-the-loop and observability. Interviewers probe exactly that gap: what stops your agent from doing something harmful, how do you know it works, and how do you debug the step where it went wrong?

### In plain words
An agent is a model in a loop: it looks at the task, picks a tool, reads the result, and decides what to do next until it is done. Think of it as a capable intern at a desk. The desk and its rules (harness), how long they keep trying (loop), which papers are on the desk (context), which buttons they can press (tools), what they remember tomorrow (memory), and whether they work alone or in a team (orchestration) decide how well they work. Then come the parts that make it safe to hand them real work: locks on dangerous buttons (guardrails), tests of how they work and not only the final answer (evals), a manager who signs off on big decisions (human in the loop), and a record of every step they took (tracing).

### From your saved posts
- aiwithanju: 10 agentic concepts to master before AI interviews, with the claim that most people are stuck on context engineering and tool design while the demo-to-system gap is concepts 7 to 10.
- codev.ai: the same 10 concepts, one line each, for example that when an agent breaks at step 14 of 30, you need to be able to see step 14.

### C. Harness Engineering
**In one line:** The harness is everything around the model that lets it act: sandbox, file system, tools, runtime and the code driving the loop.

**Think of it like:** The intern's desk setup: which computer, which folders, which logins, and what is locked away.

**Example:** A coding agent runs in a Docker container with only the repo mounted, no production credentials, a network allowlist and per-command time limits, so a bad `rm -rf` hits a disposable copy.

**Say it in an interview:** The same model performs very differently across harnesses, so I treat the harness as the product: what the agent sees, what it can execute, and how results flow back. I design for isolation, scoped credentials, predictable tool outputs and error messages the model can recover from.

**Go deeper:** Agents track, section "Harness & Loop Engineering".

### C. Loop Engineering
**In one line:** Loop engineering decides when the agent takes another step and, just as important, when it stops.

**Think of it like:** Telling the intern: keep trying, but no more than ten attempts, and call me if you are stuck.

**Example:** A research agent loops "think, search, read" with a 15-call cap, a token and cost budget, a wall-clock timeout, and a normal stop when the model answers without calling a tool.

**Say it in an interview:** Every agent loop needs explicit termination: a success condition, max iterations, budgets, and detection of repeated identical tool calls. I checkpoint state each step so a long run resumes after a crash instead of restarting, and return a graceful fallback when a limit is hit.

**Go deeper:** Agents track, section "Harness & Loop Engineering".

### C. Context Engineering
**In one line:** Context engineering is choosing what goes into the context window at each step: the right information in, the wrong information out.

**Think of it like:** Clearing the intern's desk and laying out only the papers this task needs.

**Example:** At step 12, a support agent's context holds the system prompt, the goal, a summary of steps 1 to 10, step 11's full result, and the three relevant tools, not 40 tools and raw logs.

**Say it in an interview:** Prompt engineering is about wording; context engineering manages the whole payload across a run: instructions, retrieved data, tool results, memory and history. More context costs money and can lower accuracy, so I compact old turns, trim tool outputs, retrieve just in time, and keep stable content first for caching.

**Go deeper:** Agents track, section "Context Engineering".

### C. Tool Design
**In one line:** Tool design shapes the functions an agent can call: it is only as capable as its tools and only as safe as their worst edge case.

**Think of it like:** Clearly labeled buttons that each do one thing, instead of one console where a typo wipes the database.

**Example:** Instead of `run_sql(query)`, expose `get_customer_orders(customer_id, limit)` with a strict JSON Schema, a description of when to use it, results capped at 20 rows, and errors that say what to fix.

**Say it in an interview:** I design tools like an API for a teammate who only reads the docs: few, narrow, well named, typed, with helpful errors. Reads and writes are separate, writes are idempotent and permission-checked against the end user, and outputs stay concise to protect the context.

**Go deeper:** Agents track, section "MCP & Tool Ecosystems".

### C. Memory Architecture
**In one line:** Memory architecture decides what an agent remembers, for how long, and what it may or must forget.

**Think of it like:** The intern's notebook for today, a file on each client, and a shredding policy for anything sensitive.

**Example:** A shopping assistant keeps the conversation as working memory, stores "vegetarian, size M" as user-scoped long-term memory in Postgres with an expiry, and pulls only relevant memories into each turn.

**Say it in an interview:** I separate working memory (this run's state), episodic memory (past interactions) and semantic memory (durable facts), each with its own store, retrieval rule and retention policy. Memory writes need validation, because one injected memory poisons every future run, and users must be able to delete what is stored.

**Go deeper:** Agents track, section "Memory & State".

### C. Orchestration Patterns
**In one line:** Orchestration is how work is split: one agent, a planner handing steps to workers, or a swarm, and each fails differently.

**Think of it like:** A generalist doing the whole job, a manager assigning specialists, or a committee, which is hardest to keep on track.

**Example:** A report generator's planner splits "compare 5 vendors" into 5 parallel research subtasks, then a writer agent merges results. An FAQ bot needs only one agent.

**Say it in an interview:** I start simple, a fixed workflow or single agent, and add agents only when subtasks are parallel or need isolated context. Single agents drift on long tasks, planners fail on bad plans, and swarms multiply cost and lose information at handoffs, so I pick the failure I can detect best.

**Go deeper:** Agents track, section "Multi-Agent Systems".

### C. Guardrails & Permissions
**In one line:** Guardrails and permissions decide what happens when the agent tries something it should not, enforced in code, not just requested in the prompt.

**Think of it like:** The intern can view accounts but needs a manager's badge to issue refunds, and the badge reader enforces it.

**Example:** An `issue_refund` tool checks the end user's role server-side, caps the amount, and needs approval above a threshold. Incoming emails are untrusted data, so "ignore previous instructions" cannot trigger a tool.

**Say it in an interview:** I apply least privilege per tool and per user, validate every tool argument, and screen inputs and outputs for prompt injection, PII and policy violations. My rule: assume the model can be manipulated, and make the worst thing a manipulated model can do acceptable.

**Go deeper:** Agents track, section "Agent Reliability & Evaluation".

### C. Evals for Agents
**In one line:** Agent evals test the path the agent took, not just its final answer, because a multi-step trajectory is not a pure function.

**Think of it like:** Grading the intern on how they got the answer: right records checked, no risky shortcuts, sensible number of steps.

**Example:** 100 recorded support tasks, each scored on task success (refund correct in the database), tool order (`lookup_order` before `issue_refund`), steps and cost, with an LLM judge only for tone.

**Say it in an interview:** Agents are non-deterministic, so I run each case several times and track pass rates. I combine deterministic checks on end state and tool calls with LLM-as-judge for fuzzy qualities, calibrated against human labels, and run the suite in CI on every prompt, model or tool change.

**Go deeper:** Agents track, section "Agent Reliability & Evaluation".

### C. Human-in-the-Loop Design
**In one line:** Human-in-the-loop design decides which decisions the agent never makes alone and builds a clean pause for human approval.

**Think of it like:** The intern drafts the contract and email; the manager signs and clicks send.

**Example:** A finance agent prepares a vendor payment, saves its state, and posts a Slack approval card with amount, payee and reasoning. Approve resumes from the checkpoint; reject stops and logs why.

**Say it in an interview:** I classify actions by risk and reversibility: reads run freely, reversible writes may auto-run, irreversible or high-value actions need approval. Runs checkpoint and resume rather than hold a process open, the approval screen shows enough context to decide, and I watch approval rates for rubber-stamping.

**Go deeper:** Agents track, section "Production Agent Architecture".

### C. Observability & Tracing
**In one line:** Tracing records every step of an agent run (prompts, outputs, tool calls, results, latency, cost) so you can see where it went wrong.

**Think of it like:** A flight recorder: when something breaks at step 14 of 30, you replay step 14 instead of guessing.

**Example:** Each run is a trace; each model or tool call is a span tagged with model, prompt version, tokens, cost, latency and errors, viewed in Langfuse, LangSmith or any OpenTelemetry backend.

**Say it in an interview:** Agent bugs are rarely crashes; they are bad decisions, so I need inputs and outputs at every step, not just status codes. I use OpenTelemetry-style spans, redact PII before storage, link traces to user feedback, and turn failing traces into eval cases.

**Go deeper:** MLOps & LLMOps track, section "Observability & Tracing for LLM Apps".

## The 7 AI System Design Patterns [Core]

> The saved post lists these seven as the patterns that come up in AI system design rounds. Interviewers rarely ask you to define caching. They hand you a product ("design a support copilot for 10,000 agents") and listen for whether you reach for these patterns unprompted, each with a concrete design decision and its trade-off.

### In plain words
Building an AI feature is like running a restaurant with a talented but unpredictable chef. You need a camera on the kitchen (observability), dishes ready for common orders (caching), regular taste tests (evals), the right ingredients handed to the chef with each order (RAG), now and then a cooking course for the chef (fine-tuning), comment cards from diners (feedback loops), and a food-safety inspector at the pass (guardrails). Each pattern solves one specific problem, and a strong design says which problem it is solving and what it costs.

### From your saved posts
- anay.tech: 7 AI system design patterns that come up in AI engineering interviews (observability, caching, agentic evals, RAG, fine-tuning, user feedback loops, guardrails), with the message not to skip system design.

### C. Observability
**In one line:** Observability records every LLM call's inputs, outputs, latency, token cost and failures, so you see what happens and why.

**Think of it like:** A camera and black-box recorder on the kitchen: what was ordered and served, how long it took, what it cost.

**Example:** Design decision: an LLM gateway emits one OpenTelemetry span per provider call with model, prompt version, tenant ID, tokens, cost, latency and error, redacts PII before export, and feeds per-tenant cost and p95 latency alerts.

**Say it in an interview:** LLM failures are often silent: a 200 OK can carry a wrong answer, so I capture content as well as metrics and sample traces for quality review. A gateway gives one place for tracing, budgets, retries and provider fallback.

**Go deeper:** MLOps & LLMOps track, section "Observability & Tracing for LLM Apps".

### C. Caching
**In one line:** Caching reuses earlier work so repeated or similar requests return faster and cost less.

**Think of it like:** Keeping popular dishes ready so the tenth identical order is not cooked from scratch.

**Example:** Design decision: an exact-match Redis cache keyed on a hash of model, prompt version and normalized input; a semantic cache keyed on normalized query embeddings with a similarity threshold and per-tenant scope; and provider prompt caching for the static system prompt.

**Say it in an interview:** Semantic caching's risk is a confident answer to a similar but different question, so I tune the threshold on labeled query pairs, skip personalized or time-sensitive answers, and tie TTLs to source updates. Versions in the key make prompt or model changes invalidate cleanly.

**Go deeper:** Inference track, section "Caching at the Inference Layer".

### C. Agentic Evals
**In one line:** Agentic evals test an agent's tool selection, reasoning steps and outcomes on a fixed task set before any change ships.

**Think of it like:** A tasting menu the chef must cook correctly before any new recipe reaches the real menu.

**Example:** Design decision: 200 golden tasks from production traces, each with an expected end state and required or forbidden tool calls. CI runs each case several times per prompt, model or tool change and blocks the merge if success drops past a margin or cost exceeds budget.

**Say it in an interview:** I score outcome (is the database right), trajectory (right tools, right order, nothing forbidden) and efficiency (steps, tokens, latency). Deterministic checks come first; LLM judges handle subjective criteria only after validation against human labels.

**Go deeper:** MLOps & LLMOps track, section "Evaluation Pipelines in CI/CD".

### C. RAG as a Pattern
**In one line:** RAG grounds answers in your own current data by retrieving it at request time, not relying on what the model memorized.

**Think of it like:** Handing the chef today's delivery list and the house recipe book with each order.

**Example:** Design decision: ingest through a queue, chunk by heading with overlap, store embeddings in pgvector with tenant ID and access-control lists as metadata, run hybrid search filtered by user permissions, rerank the top 50 to 5, and require citations.

**Say it in an interview:** RAG is the default for knowledge that changes or must be cited, because updating an index is far cheaper and faster than retraining. The hard parts are chunking, permissions enforced at retrieval, freshness, and evaluating retrieval separately from generation.

**Go deeper:** LLMs, RAG & Evals track, section "Advanced RAG Patterns".

### C. Fine-tuning as a Pattern
**In one line:** Fine-tuning further trains a model on your examples to change its behavior when prompting and RAG fall short.

**Think of it like:** Sending the chef on a house-style course: it changes how they cook, not what arrived today.

**Example:** Design decision: a high-volume ticket classifier with a strict label set. Once prompting plateaus, LoRA-tune a small open model on a few thousand labeled tickets and ship only if it matches the prompted large model on a held-out set at lower cost.

**Say it in an interview:** Fine-tuning teaches format, tone and narrow skills; it is a poor way to add changing facts, which is RAG's job. I use it only with an eval showing the gap, enough clean data and a retraining plan.

**Go deeper:** Fine-tuning & ML track, section "When to Fine-tune".

### C. User Feedback Loops
**In one line:** Feedback loops capture ratings, edits and corrections and feed them back into prompts, retrieval, evals and eventually models.

**Think of it like:** Comment cards the chef actually reads every week, and that change the menu.

**Example:** Design decision: store each feedback event against its trace ID, diff drafted replies against what was sent as implicit feedback, triage negative traces weekly, add confirmed failures to the eval set, and keep accepted corrections as few-shot or fine-tuning candidates.

**Say it in an interview:** Explicit ratings are sparse and skew negative, so I also track implicit signals: copies, edit distance, retries, abandonment. The loop works only if each signal traces back to the exact prompt version, retrieved context and model behind the answer.

**Go deeper:** MLOps & LLMOps track, section "Feedback Loops & the Data Flywheel".

### C. Guardrails
**In one line:** Guardrails are checks before and after the model that block unsafe, off-policy or incorrect inputs and outputs.

**Think of it like:** A food-safety inspector checking every plate at the pass and turning away suspicious deliveries.

**Example:** Design decision: input rails for prompt injection and PII, the model call, then output rails for JSON schema validation, grounding against retrieved sources and moderation. On failure, retry once with the error, then return a safe fallback and log it.

**Say it in an interview:** I layer guardrails cheap to expensive: deterministic rules, then small classifiers, then LLM judges only where needed, because each adds latency. I track false positives as closely as catches, since an over-blocking guardrail breaks the product as surely as a missing one.

**Go deeper:** LLMs, RAG & Evals track, section "Safety, Security & Guardrails".
