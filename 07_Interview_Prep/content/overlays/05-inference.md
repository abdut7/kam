## Inference Engineering Levels [Start here]

> Inference engineering is the work of running a model so that answers come back fast, cheaply and reliably. Interviewers for AI Full Stack roles rarely expect you to have tuned GPU kernels, but they do probe how far below the API you can see. A weak answer stops at "we call the OpenAI API". A strong answer places you honestly on a three-level map, tells the story of what happens on the GPU as traffic grows, and describes a lab you ran with numbers you measured yourself. Start here, then go deeper in the sections that follow.

### In plain words
A hosted model API is like a restaurant: you order, the food arrives, and you never see the kitchen. Inference engineering is learning how that kitchen works. Level 1 is knowing the kitchen exists and how to rent one: cloud machines with graphics cards (GPUs) and the open models you can run on them. Level 2 is understanding how one cook handles many orders at once without running out of counter space. Level 3 is timing every order with a stopwatch and changing the setup until the kitchen is both fast and cheap.

### From your saved posts
- vishakha.sadhwani: the three levels of inference engineering (AI infrastructure fundamentals, understanding inference, optimizing inference) and the project that gets you out of each level.
- jam.with.ai: one GPU serving an AI docs assistant, told one problem at a time, each problem solved by a named technique (PagedAttention, continuous batching, chunked prefill, prefix caching, quantization, speculative decoding).
- lindavivah: build your own inference engine in six steps (GPU node on Kubernetes via Terraform, vLLM serving a Qwen model, port-forward, swap the base URL, load test, deploy an agent).
- Workshop repo behind that post (Akamai Developers, Apache-2.0): [akamai-developers/akamai-workshop-ai-inference](https://github.com/akamai-developers/akamai-workshop-ai-inference)

### Concepts you must understand
- Level 1, AI infrastructure fundamentals: you call LLM APIs, deploy applications around them, know open-weight models (you download and run the weights) from closed foundation models (API only), and know where GPU nodes on Kubernetes fit; you leave level 1 by deploying a model yourself, locally or on one rented GPU.
- Level 2, understanding inference: you can explain prefill and decode, why the KV cache (stored attention keys and values of earlier tokens) decides how many users fit on a GPU, how vLLM, SGLang and TensorRT-LLM manage that memory, and aggregated versus disaggregated serving; you leave level 2 by serving on a real GPU cluster and measuring how each configuration choice changes the numbers.
- Level 3, optimizing inference: you benchmark with TTFT, TPOT, inter-token latency, end-to-end latency and throughput, then apply continuous batching, chunked prefill, speculative decoding, quantization, distillation and parallelism where the measurements say they help; you stay credible by keeping a benchmarking project where you vary one setting at a time.
- The OpenAI-compatible API is the bridge between levels: the same client code talks to a hosted provider or to your own vLLM server once you change the base URL, so moving down a level does not mean rewriting the application.
- Every technique answers a specific problem (wasted memory, idle slots, a long prompt blocking others, a repeated system prompt, weights too large, decode too slow); learning the problem first is what makes the technique easy to remember and defend.
- Latency and throughput are different promises: time to first token and the gaps between tokens describe one user's experience, tokens per second across all users describes cost, and most optimizations trade one against the other somewhere.
- Self-hosting is a cost, privacy and control decision that pays off only at steady volume, but running the lab once teaches what the hosted API hides even if production stays hosted.

### Q. What are the three levels of inference engineering, and where are you today?
**Short answer (45 seconds):** Level 1 is AI infrastructure fundamentals: calling model APIs, deploying apps around them, open-weight versus closed models, and where GPUs and Kubernetes fit. Level 2 is understanding inference itself: prefill and decode, the KV cache, how engines like vLLM manage memory, aggregated versus disaggregated serving. Level 3 is optimizing with measurements: TTFT, TPOT, throughput, and levers such as batching, speculative decoding and quantization. My honest position as a full stack engineer shipping on hosted APIs: strong at level 1, into level 2 on understanding, and the gap I am closing is hands-on level 2, serving an open model on a GPU and measuring it.

**Deeper explanation:** The levels are about the evidence you can show, not what you have read.

| Level | You can explain | Evidence that moves you up |
| --- | --- | --- |
| 1 Fundamentals | APIs, deployments, GPUs on Kubernetes, open versus closed models, pre-training versus post-training versus inference | a model you deployed yourself |
| 2 Understanding | prefill, decode, KV cache, PagedAttention, engine choice, serving patterns | a GPU deployment where you changed settings and saw the effect |
| 3 Optimizing | latency metrics, batching, speculative decoding, quantization, parallelism | a benchmark matrix with a written recommendation |

Level 1 already carries real production skill: streaming, retries, rate limits, prompt caching, cost per feature. Level 2 adds the reasons behind what you see from the API: why cached input tokens are billed at a discount (prefix caching), why long prompts delay the first token (prefill), and why latency gets worse at peak hours (batching and queueing).

**Follow-ups they will ask:**
- What would move you to level 3: a benchmark on my own endpoint that varies concurrency, prompt length and one engine setting at a time, with TTFT, TPOT and throughput recorded.
- Does this role need level 3: rarely day to day, but level 2 is expected in cost, latency and build-versus-buy conversations.

**Mistakes to avoid:**
- Claiming level 3 without a benchmark you ran and numbers you can defend.
- Dismissing level 1 as trivial; production API work is a real skill, just a different one.

### Q. Walk me through what happens on one GPU when one user, then fifty users, hit your LLM endpoint.
**Short answer (45 seconds):** With one user, prefill reads the whole question in one parallel pass, decode writes the answer one token at a time, and the KV cache keeps the keys and values of earlier tokens so they are not recomputed. With fifty users, everyone shares one copy of the weights, but each conversation needs its own KV cache that grows with its length, so memory becomes the limit. The engine then fixes one problem at a time: paged memory, continuous batching, chunked prefill, prefix caching, then quantization and speculative decoding.

**Deeper explanation:**

| Problem at fifty users | Technique | Effect |
| --- | --- | --- |
| max-length memory reserved per request is mostly wasted | PagedAttention: small cache blocks allocated on demand | more conversations fit |
| answers finish at different times, slots sit idle | continuous batching: requests leave and join between steps | the GPU stays busy |
| a pasted document delays everyone's next token | chunked prefill: the prompt is processed in pieces alongside decodes | smooth gaps between tokens |
| every request repeats the same system instructions | prefix caching: reuse work when the starting tokens match exactly | lower TTFT |
| weights leave too little room for the cache | quantization: weights stored in fewer bits | memory; quality must be checked |
| decode still slow per user | speculative decoding: a cheap draft proposes, the main model checks several tokens at once | fewer slow steps if guesses land |

Measure latency per user (time to first token, gaps between tokens) and throughput across users (tokens per second); the job is raising throughput while latency stays inside a target.

**Follow-ups they will ask:**
- Why do fifty users not need fifty times the memory: the weights are shared; only the KV cache grows per conversation.
- What happens when the cache fills: new requests queue or running ones are preempted, visible as rising TTFT and preemption counts.
- Does speculative decoding help at fifty users: less than at one, since a busy GPU has little spare compute to verify guesses.

**Mistakes to avoid:**
- Listing techniques without the problem each one solves.
- Saying more users simply need more GPUs; the first lever is fitting more conversations on the GPU you have.

### Q. How would you stand up and benchmark your own OpenAI-compatible inference endpoint?
**Short answer (45 seconds):** Six steps. Provision a Kubernetes cluster with a GPU node using Terraform, deploy vLLM serving an open model such as Qwen/Qwen3-4B, port-forward a private tunnel, and point existing code at it by swapping the base URL of an OpenAI-compatible client. Then load test while watching vLLM's Prometheus metrics to see the KV cache fill and continuous batching keep the GPU busy, and finally deploy an agent on the endpoint. The benchmark varies one thing at a time and records TTFT, TPOT, throughput and KV cache usage.

**Deeper explanation:**

```bash
terraform apply                                  # cluster plus one GPU node
kubectl apply -f vllm.yaml                       # runs: vllm serve Qwen/Qwen3-4B
kubectl port-forward svc/vllm 8000:8000          # private tunnel, nothing public
curl -s localhost:8000/v1/models
curl -s localhost:8000/metrics | grep -E 'num_requests_(running|waiting)|cache_usage|preempt'
```

File and service names are illustrative. Step 4 is one line in Node, `new OpenAI({ baseURL: "http://localhost:8000/v1", apiKey: "unused" })`. The Akamai workshop walks the same path in modules: GPU memory budgeting, prefill and decode, dense versus MoE models, then BF16 versus FP8, speculative decoding, engine saturation and tuning, and finally an agent on the endpoint.

Generate load with vLLM's serving benchmark (`vllm bench serve` in recent versions) or a small async client. Vary concurrency (1, 8, 32, 64), prompt length, output length, precision, `--max-num-batched-tokens` and speculative decoding on or off. Record p50 and p95 TTFT and TPOT, aggregate tokens per second, running and waiting requests, KV cache usage and preemptions. The headline result is the knee: the concurrency at which p95 TTFT breaks your target.

**Follow-ups they will ask:**
- Why port-forward instead of a public load balancer: it keeps an unauthenticated model server private while you experiment; production needs auth, TLS and a gateway.
- Why a 4B model: it fits one modest GPU with room for KV cache, so batching effects show; the method carries to bigger models.
- What tells you the engine is saturated: waiting requests climb while throughput stays flat and TTFT rises.

**Mistakes to avoid:**
- Benchmarking at concurrency 1 only; batching behavior is the whole point.
- Leaving the GPU node running after the lab; tear it down with `terraform destroy`.

### Q. When does self-hosting inference beat paying per token, and when does it not?
**Short answer (45 seconds):** Self-hosting wins when volume is steady enough to keep a GPU busy and an open model meets the quality bar, when data must stay inside your network, or when you need control a provider will not give: a custom fine-tune, pinned model versions, predictable latency. Paying per token wins for spiky or small traffic, for frontier quality, and for teams that cannot carry GPU operations. A cheap GPU hour is not a cheap token; what matters is how many useful tokens the GPU produces per hour you pay for.

**Deeper explanation:** Test the four reasons the six-step lab post gives for running your own engine.

| Reason | Holds when | Fails when |
| --- | --- | --- |
| Cost | steady high volume on a small model | traffic is spiky or low; the GPU bills while idle |
| Privacy | data cannot leave your network or region | zero-retention terms already meet the requirement |
| Control | custom fine-tunes, pinned versions, latency guarantees | the hosted model already does the job |
| Learning | always; one lab shows what the API hides | it is the only production justification |

The post quotes roughly 50 cents an hour for its lab GPU node. That is the post's own figure, and it says nothing about cost per token at your traffic or whether a 4B model matches the hosted model you would replace. Compare like with like: the same task, the same quality bar on your eval set, achieved rather than peak utilization, and the engineers who run it. The usual answer is hybrid: self-host a narrow high-volume task on a small model and route the hard tail to a hosted frontier model. The arithmetic is in Cost Engineering, "Build versus buy: when does self-hosting beat API pricing?".

**Follow-ups they will ask:**
- What single number decides it: cost per successful task on your eval set, computed both ways.
- Does privacy force self-hosting: not always; region-pinned endpoints with zero-retention terms may be enough.

**Mistakes to avoid:**
- Comparing an hourly GPU price with a per-token API price without converting at real utilization.
- Assuming an open model is a drop-in replacement without running your eval set.

### Q. What is disaggregated prefill/decode serving and when is it worth it? [Advanced]
**Short answer (45 seconds):** Normally the same GPUs run both phases: compute-heavy prefill and memory-bandwidth-heavy decode, so a long prefill interferes with everyone's decode steps. Disaggregated serving runs them on separate GPU pools: prefill workers compute the prompt's KV cache and transfer it to decode workers, which generate the tokens. Each pool is then sized and tuned for its own target, TTFT for prefill and inter-token latency for decode. It pays off at large scale with long prompts, strict targets on both phases and fast networking; on a few GPUs, chunked prefill gets most of the benefit without the complexity.

**Deeper explanation:**

```text
aggregated:    [one pool: prefill + decode interleaved]   chunked prefill limits interference
disaggregated: client -> router -> [prefill pool] --KV transfer--> [decode pool] -> stream
KV to move, Llama 3 8B in BF16: 2 x 32 layers x 8 KV heads x 128 dims x 2 bytes = 128 KiB per token
an 8k-token prompt -> about 1 GiB per request
```

That transfer is the first cost: it needs RDMA-class networking or NVLink and a router that picks a prefill and a decode worker per request. The second cost is balance: the right prefill to decode ratio depends on your prompt and output lengths, so a traffic shift leaves one pool idle while the other queues. The idea comes from research systems such as DistServe and Splitwise and production designs such as Mooncake; vLLM and SGLang both have disaggregation support, and NVIDIA Dynamo and llm-d orchestrate it on Kubernetes. Check maturity for your version.

**Follow-ups they will ask:**
- How is it different from chunked prefill: chunked prefill shares one GPU fairly; disaggregation removes the sharing at the price of a network transfer.
- Does prefix caching still work: yes, but the router must know which workers hold which prefixes, so cache-aware routing becomes part of the design.
- What would you measure first: p95 TTFT and inter-token latency on long-prompt traffic, aggregated versus disaggregated, at equal GPU count.

**Mistakes to avoid:**
- Proposing it for a single-GPU or low-traffic deployment.
- Ignoring the KV transfer size; it is the first thing an interviewer will push on.

### Practice
- Build the six-step lab: provision a GPU node, serve Qwen/Qwen3-4B with vLLM, port-forward, point an existing Node or Python OpenAI client at it by changing only the base URL, load test it, run a small tool-calling agent against it, and tear it down the same day.
- Fill a benchmarking matrix: concurrency 1, 8, 32 and 64 against short, medium and long prompts, BF16 versus FP8 (if your GPU supports FP8), speculative decoding off and on; record p50 and p95 TTFT and TPOT, tokens per second, waiting requests and KV cache usage in every cell.
- Write a one-page result: the knee concurrency for your TTFT target, the setting that helped most and the one that hurt, cost per million tokens at measured throughput, and whether you would self-host this workload.
- Say it out loud: tell the one user, fifty users story in two minutes, naming each problem before its technique.

## Inference Fundamentals

### In plain words
When you send a prompt, the model first reads all of it at once; this is called prefill, and it decides how long you wait for the first word. Then it writes the answer one small piece at a time (a token, roughly part of a word); this is called decode. To avoid re-reading everything for each new token, it keeps notes on what it has already read, called the KV cache. Think of a waiter who reads your whole order once, then brings the dishes one by one while keeping your order slip on the counter: the more tables, the more slips, and the counter (GPU memory) is what runs out first. So two numbers describe speed for one user, the wait for the first word and the gaps between words, and one number describes the whole kitchen: tokens per second across everyone.

### From your saved posts
- jam.with.ai: one user on one GPU, prefill then decode, the KV cache, and latency versus throughput as the two ways to measure.
- vishakha.sadhwani: level 2 (prefill, decode, KV cache memory management) and the level 3 metric list (TTFT, TPOT, inter-token latency, throughput, end-to-end latency).
- lindavivah: the workshop's early modules on GPU memory budgeting, prefill and decode, the KV cache, and dense versus MoE models.

### Q. TPOT and inter-token latency sound the same. What is the difference, and why would you watch both?
**Short answer (45 seconds):** TPOT, time per output token, is usually computed per request as decode time divided by the tokens after the first, so it is an average for that request. Inter-token latency is the distribution of every individual gap between consecutive tokens, across all requests. A request can have a fine average and still contain a one-and-a-half-second freeze, and the freeze is what users notice. TPOT tells you the steady decode speed; inter-token latency percentiles tell you about stalls.

**Deeper explanation:**

```text
one request, 200 output tokens -> 199 gaps
198 gaps at 25 ms, 1 gap at 1,500 ms
TPOT ≈ (198 × 25 + 1,500) / 199 ≈ 32 ms       looks healthy
ITL p50 = 25 ms, ITL max = 1,500 ms           the stall the user saw
```

Common causes of stalls: a long prompt's prefill landing in the same step (fixed by chunked prefill or a lower `--max-num-batched-tokens`), preemption when the KV cache fills and a running request is paused, and buffering in your own stack, such as a proxy that holds server-sent events before flushing. Measure gaps on the client per streamed chunk as well as from the engine's histograms, because only the client sees proxy buffering. Tools define these metrics slightly differently, so read how each benchmark computes them before comparing numbers across tools.

**Follow-ups they will ask:**
- Which one goes in the chat SLO: p95 or p99 inter-token latency plus TTFT; TPOT is more useful for capacity planning.
- What does chunked prefill do to these: it caps how long a prefill can occupy a step, trimming the inter-token tail at a small cost to long-prompt TTFT.
- How do you spot preemptions: the engine's preemption counter in `/metrics` rising while KV cache usage sits near full.

**Mistakes to avoid:**
- Reporting only average TPOT for a chat product.
- Blaming the model for stalls caused by a proxy that buffers the stream.

## Serving Engines & Stacks

### In plain words
A serving engine is the program that loads a model onto a GPU and answers many users at once; vLLM, SGLang and TensorRT-LLM are the well-known ones. Its two big tricks are about sharing. First, it hands out GPU memory in small blocks only as a conversation grows, like a car park that assigns spaces as cars arrive instead of reserving a whole row per car (PagedAttention). Second, it lets a finished request leave and a waiting one join between every step, like a bus that picks up passengers at every stop instead of waiting for the whole trip to end (continuous batching). Most engines also speak the same API as OpenAI, so your app can switch to them by changing one URL.

### From your saved posts
- jam.with.ai: PagedAttention as the answer to wasted reserved memory, continuous batching as the answer to answers finishing at different times.
- vishakha.sadhwani: level 2 engines (vLLM, SGLang, TensorRT-LLM), how each manages memory and reuses the KV cache, and Kubernetes as the place where scaling and scheduling meet.
- lindavivah: vLLM serving a Qwen model on a Kubernetes GPU node, reached through an OpenAI-compatible base URL.

## Quantization

### In plain words
Quantization stores the model's numbers with less precision, for example 1 byte each instead of 2, so the model takes less GPU memory. It is like saving a photo at a lower quality setting: a much smaller file that usually looks the same, though fine detail can get lost. The freed memory lets more conversations fit at once, and smaller weights are quicker to read on every step, so answers often come out faster. Whether it really gets faster depends on the model, the GPU and the format, and quality must be checked on your own test questions before you ship.

### From your saved posts
- jam.with.ai: weights too large, so store them in fewer bits; saves memory, quality must be checked, speed depends on model, hardware and format.
- vishakha.sadhwani: model compression (quantization and distillation) as a level 3 optimization.
- lindavivah: the workshop module comparing BF16 with FP8 on the same endpoint.

## Speed-ups Beyond Batching

### In plain words
Once many users share the GPU, a few extra tricks remove the remaining waits. Chunked prefill cuts a very long pasted document into pieces so it cannot hold up everyone else's next word, like a cashier who rings up a full trolley in parts and lets people with one item through in between. Prefix caching remembers the work done on text that every request starts with, such as the same system instructions. Speculative decoding lets a small fast model guess the next few words while the big model checks them all in one go, which saves time only when most guesses are right. Parallelism splits a model that is too big, or too slow, for one GPU across several.

### From your saved posts
- jam.with.ai: chunked prefill for a long pasted document, prefix caching for repeated system instructions, speculative decoding with a cheaper draft model.
- vishakha.sadhwani: level 3 request-level optimizations (continuous batching, speculative decoding, chunked prefill) and parallelism strategies.
- lindavivah: the workshop modules on speculative decoding, engine saturation and tuning.

## Caching at the Inference Layer

### In plain words
Caching means not doing the same work twice. Inside the engine, if a new request starts with exactly the same text as an earlier one, such as a long system prompt, the work already done on that text is reused, so the first word arrives sooner. Hosted APIs do the same thing and charge less for the reused part. Higher up, you can store whole answers and return them for repeated questions, like a help desk that keeps a sheet of answers to its most common questions. The catch is that reused text must match from the very first character, and stored answers go stale when the prompt, the model or the data changes.

### From your saved posts
- jam.with.ai: every request starts with the same system instructions, so prefix caching reuses cached work when the starting tokens match exactly.
- vishakha.sadhwani: KV cache reuse as one of the ways serving engines differ (level 2).

## Reliability & Observability for Inference

### In plain words
Observability means seeing what your model server is doing, in numbers, while it runs. The engine publishes counters such as how many requests are running, how many are waiting in line, and how full its conversation memory (the KV cache) is. Watching them during a load test is like watching a restaurant's queue at the door and its free tables inside: when the queue grows while every table is taken, you need more capacity or you must turn people away politely. Reliability is the plan for those moments: time limits, safe retries, a backup model, and alerts that fire before users notice.

### From your saved posts
- vishakha.sadhwani: level 3 starts with observability and benchmarking (TTFT, TPOT, throughput, end-to-end and inter-token latency).
- lindavivah: the workshop reads vLLM's Prometheus `/metrics` to watch batching, queueing and saturation during a load test.
- jam.with.ai: measure time to first token and gaps between tokens for latency, and tokens per second across all users for throughput.
