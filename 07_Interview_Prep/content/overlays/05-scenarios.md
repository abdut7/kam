## Inference Engineering Levels

### Why it exists
Most product teams meet LLMs as a hosted API and treat everything behind it as a black box, which works until a latency, cost or privacy question arrives that the API cannot answer. The levels map shows what sits under that API and the order to learn it in: first the infrastructure (GPUs, open-weight models, Kubernetes), then how serving engines actually run a model, then how to measure and tune it. Without such a map, people either stay at the API forever or jump to optimization tricks they cannot justify. The cost is time and money, because every level needs hands-on work on real GPUs, so the honest goal is to know which level a job needs and to have evidence for the level you claim.

## Inference Fundamentals

### Why it exists
LLM requests do not behave like normal web requests: one call can return in a few hundred milliseconds and the next can take over a minute, depending on how long the prompt and the answer are. The prefill and decode model, the KV cache (the stored attention data for tokens already read) and the latency metrics TTFT and TPOT explain why, and they let you predict memory, concurrency and cost before you buy hardware. Before engineers used this model, they sized GPUs by model size alone and were surprised when a model that "fit" could serve only a handful of users. The trade-off is that it is a simplified picture: it tells you what to measure and roughly what to expect, but real numbers still come from benchmarking your own traffic.

## Serving Engines & Stacks

### Why it exists
Running a model with a plain training-library script serves one request at a time, or batches requests while reserving memory for the longest possible answer, so an expensive GPU sits mostly idle. Serving engines such as vLLM, SGLang and TensorRT-LLM exist to keep the GPU full: they hand out KV cache memory in small pages as it is needed and let requests join and leave the batch at every step. They also expose an OpenAI-compatible API, so an application can switch between a hosted provider and a self-hosted model by changing a URL. The cost is a fast-moving dependency: engine releases change defaults, flags and metric names often and are tied to GPU drivers and CUDA versions, so you pin versions and re-test on every upgrade.

## Quantization

### Why it exists
Model weights stored at 2 bytes per number are often too big for the GPU you can afford, or leave too little memory for the KV cache that decides how many users fit at once. Quantization stores weights, and sometimes activations and the KV cache, in fewer bits such as 8 or 4, so the same model needs less memory and moves fewer bytes for every token it generates. Before it was practical, the only options were bigger GPUs, splitting the model across several GPUs, or a smaller model. The trade-off is a quality risk that is not spread evenly (numbers, code and long contexts suffer first) plus a dependency on fast kernels for your exact GPU and format, so every quantized model needs its own eval and its own benchmark.

## Speed-ups Beyond Batching

### Why it exists
Batching keeps the GPU busy, but some waits remain: decode still produces one token per step for each user, a very long prompt can stall everyone else's next token, and the same system prompt is reprocessed for every request. Speculative decoding, chunked prefill, prefix caching, FlashAttention and parallelism each remove one of those waits. Without them, the usual answer was simply more or bigger GPUs. The cost is that each technique helps in one situation and can hurt in another (speculative decoding wastes work when guesses miss, parallelism adds communication between GPUs), so they are switched on because a measurement says so, not by default.

## Scaling, Routing & Load Balancing

### Why it exists
One GPU server is both a capacity ceiling and a single point of failure, so real traffic needs several replicas and something that decides where each request goes. Ordinary web tooling fits poorly: round-robin assumes requests cost about the same, but LLM requests differ by orders of magnitude in tokens, and CPU-based autoscaling cannot see GPU queues or KV memory. Inference-aware routing, admission control and autoscaling on queue depth exist to fill that gap. The trade-off is new state and new tension: cache-affinity routing improves reuse but unbalances load, warm headroom costs money while it sits idle, and cold starts measured in minutes mean scaling must happen before users feel the load.

## Caching at the Inference Layer

### Why it exists
LLM applications send the same tokens again and again: long system prompts, tool definitions, retrieved documents and repeated questions, and without caching every copy is paid for in GPU time, latency and money. Caching reuses work at several layers: the engine reuses the KV cache for a matching prefix, providers bill cached input tokens at a discount, and the application can return a stored answer for a repeated request. Before provider prompt caching existed, teams could only shorten prompts or cache whole responses. The costs are freshness and discipline: prefix caches only hit when the start of the prompt matches exactly, which constrains prompt layout, and response or semantic caches can serve stale or wrong answers unless keys and invalidation are designed with care.

## Cost Engineering

### Why it exists
LLM spend grows with tokens and GPU hours, and it grows quietly: a longer prompt, an agent that loops, or an idle GPU at night all add cost without any error appearing. Cost engineering makes that spend visible and controllable: it attributes cost to features and tenants, converts GPU prices into cost per token at real utilization, and picks levers such as caching, batch APIs, routing to smaller models or self-hosting. Before it, teams usually found out from the monthly invoice, after the money was gone. The trade-off is that most savings cost something else, such as latency (batch APIs), quality (smaller models) or engineering time (self-hosting), so every saving needs a quality check next to it.

## Reliability & Observability for Inference

### Why it exists
Model endpoints fail in ways normal HTTP monitoring misses: a response can be a 200 and still take thirty seconds, a stream can stop halfway, a provider can throttle with 429s, and a model update can make answers worse with no error at all. This section exists to catch and survive those failures with phase-specific timeouts, safe retries, tested fallbacks, engine metrics such as queue depth and KV usage, and tracing from the gateway down to the GPU. Without it, teams hear about slowness from users and about quality drops weeks later. The cost is more moving parts: extra metrics and traces to store, fallback paths that must be exercised regularly, and spare capacity that sits idle most of the time.

## Project Blueprint: Inference Router

### Why it exists
Once an application calls several models and providers, every feature ends up re-implementing the same logic: retries, rate limits, budgets, caching, fallbacks and cost tracking, each slightly differently. An inference router puts that logic in one service, so applications ask for a model alias or a capability and the router decides where the request goes. Before it, a provider outage or a price change meant editing every service that called a model. The trade-off is that the router becomes a critical service on every request path: it adds a network hop, needs its own scaling, monitoring and on-call, and a bug in it affects every feature at once.

## Inference Project Scenarios [Scenarios]

> In project and design rounds the interviewer hands you a situation with a number in it (users, a latency target, a budget, a deadline) and watches how you get from the vague ask to a plan. A weak answer jumps to a tool: "we would run vLLM on Kubernetes". A senior answer first pins down what the number means, does the memory and capacity arithmetic out loud, names the two or three decisions that really matter with their trade-offs, says what could go wrong, and ends with the metrics that will prove the design works. Expect the interviewer to change one constraint halfway through to see whether your reasoning adapts.

### Concepts you must understand
- Ask what the headline number means before sizing anything: "200 concurrent users" is usually 200 open sessions, of which only a fraction are generating at any moment, and only in-flight sequences consume KV cache.
- Get the request shape: prompt and output token distributions at p50 and p95 (not averages), the context length cap, how much of each prompt is a shared prefix, and images per request for multimodal models.
- Turn targets into SLOs with percentiles, such as p95 TTFT and p95 inter-token latency at a stated request rate; goodput, the requests that met the SLO, is the number that matters.
- Do the memory arithmetic out loud: weights = parameters × bytes per parameter, KV per token = 2 × layers × KV heads × head dim × bytes, and what remains after weights and activations decides tokens in flight.
- Capacity comes from a measured knee on your own traffic shape, not from a datasheet or a blog benchmark; plan replicas at about 60 to 70% of the knee plus N+1 for failures and cold starts.
- Every model change (quantization, a new fine-tune, a new adapter, a new base version) passes an eval gate on a golden set, then rolls out through shadow traffic and a canary with a rollback path.
- Judge designs on cost per successful task, which includes retries, failures and idle GPU time, rather than on price per token.
- Put the failure plan in the design itself: what happens when a replica dies, a provider throttles, or a cold start takes minutes.

### Q. You are self-hosting an 8B instruct model for about 200 concurrent chat users, with a p95 TTFT target of one second. How do you size and design it?
**Short answer (45 seconds):** First I pin down what 200 concurrent means, open sessions or requests generating at the same moment, and the prompt and output length distributions, because in-flight tokens decide KV memory. Then I do the memory math, pick a GPU type and replica count with headroom, and serve with vLLM behind a gateway that does admission control and session-aware routing. Finally I replay realistic traffic to find the request rate where p95 TTFT crosses one second, and set replicas and autoscaling from that knee.

**Deeper explanation:** Illustrative math for a Llama 3.1 8B-class model in BF16: weights are about 16 GB, and KV is 2 × 32 layers × 8 KV heads × 128 dims × 2 bytes = 128 KiB per token. On an 80 GB card at `--gpu-memory-utilization 0.9`, roughly 50 GB is left for KV after weights and activations, about 400k tokens.

```text
assume 40% of 200 sessions generating at once  -> ~80 in-flight sequences
average context 3k tokens (system + history)   -> ~240k tokens of KV: one replica holds it
worst case: all 200 generating at 3k tokens    -> ~600k tokens: two replicas, or FP8 KV
plus one spare replica for failures and cold starts
```

Engine settings: `--max-model-len 8192` so one huge request cannot take a large share of the cache; prefix caching on, with a stable system prompt first so every turn reuses it; chunked prefill so a pasted document does not stall other streams; `--max-num-seqs` set from the load test. The gateway counts tokens, caps max_tokens, rejects fast with 429 when over capacity, and keeps a conversation on one replica so its prefix stays warm.

**Follow-ups they will ask:**
- The target drops to 300 ms: measure prefill at p95 prompt length, then raise prefix cache hits, lower per-replica concurrency, or use FP8 or a smaller model.
- Why not tensor parallelism on two GPUs: an 8B model fits on one card; separate replicas give failure isolation and scale linearly.
- What do you watch on launch day: p95 TTFT and inter-token latency, waiting requests, KV usage, preemptions and prefix cache hit rate.

**Mistakes to avoid:**
- Treating 200 sessions as 200 sequences at maximum context, which overbuys GPUs several times over.

### Q. In a system like CADBEATER, a fine-tuned vision-language model runs on rented RunPod GPUs next to hosted LLM APIs. Design the serving layer.
**Short answer (45 seconds):** I would clarify which steps need the fine-tuned vision model and which a hosted model, how many images or pages a job carries, whether results are interactive or background, the volume, and what the data terms allow. The design is one internal OpenAI-compatible gateway in front of both: agents call model aliases, not provider URLs. The vision model runs on vLLM on a small pool of GPU pods fed by a job queue, hosted APIs handle planning and reasoning, and the gateway owns fallbacks, budgets and tracing.

**Deeper explanation:**

```text
LangGraph agents -> model gateway (auth, budgets, routing, tracing)
   |-- alias "vision-estimator" -> vLLM on GPU pods (fine-tuned VLM, pinned version)
   |-- alias "planner"          -> hosted API (primary provider, tested fallback)
image jobs: API -> Redis Streams -> vision workers -> results, progress events over SSE to the UI
```

- Images dominate cost because each becomes many prefill tokens: resize or tile drawings to the fine-tune's training resolution, cap images with `--limit-mm-per-prompt`, and size `--max-model-len` for image tokens.
- Queue the vision work: a consumer group with acknowledgements gives retries and keeps the GPU pool at steady utilization.
- Versioned weights or the LoRA adapter live on a network volume, so a new pod never downloads from the Hub.
- Rented pods can disappear: keep at least two and let the queue absorb an outage; fall back to a hosted vision model only if it passed the same eval, otherwise jobs wait and the UI says so.
- One output schema validated on both paths, and traces in Langfuse tagged with the model version.

Measure page latency p95, queue wait, image tokens per request, tokens per GPU-hour, cost per estimate and eval accuracy per model version.

**Follow-ups they will ask:**
- Why not serverless GPU endpoints: good for spiky low volume, but a large vision model cold-starts slowly; steady job load is cheaper on a warm pool.
- Shipping a new fine-tune: shadow it on recorded jobs, compare on the eval set, then repoint the alias.

**Mistakes to avoid:**
- Letting agents call the pod URL directly, so failover, budgets and tracing get rebuilt in every agent.
- Silently falling back to a general model never evaluated on the domain.

### Q. Finance asks you to cut inference spend by half within a month without a visible quality drop. What is your plan?
**Short answer (45 seconds):** Week one is measurement: attribute spend by feature, model and tenant, find the few drivers that make up most of the bill, and freeze a golden set and quality metrics as the guardrail. Then I take the structural wins first: cacheable prompts, max_tokens caps, retry and agent-loop bugs, and moving offline work to batch APIs. Next comes routing easy traffic to a smaller model behind an eval gate, and only then serving-side work. Every change ships behind a flag, with cost per successful task measured before and after.

**Deeper explanation:**

```text
week 1  measure: cost by feature, model, tenant; tokens per request p50/p95; cache hit rate; retry counts
week 2  quick wins: stable cacheable prefix, max_tokens caps, fix retry storms and agent loops,
        compress tool outputs, move evals, backfills and embeddings to the batch API
week 3  routing: rules or a classifier send easy requests to a smaller model; eval-gated, canary at 5%
week 4  serving: fill self-hosted troughs with batch work, scale down at night, FP8 where memory-bound
```

Spend is usually concentrated: a few features, a long tail of giant requests or one runaway job, so the first week often finds most of the saving. OpenAI and Anthropic both price batch work at about half the normal rate for jobs that can wait hours. Prompt caching cuts the cost of repeated prefixes and lowers TTFT at the same time. Routing needs a quality threshold per slice of traffic, not an overall average, because a cheaper model fails on specific request types while the average looks fine.

**Follow-ups they will ask:**
- Quality drops on one slice after routing: send that slice back to the large model; routing rules are per slice and can be reverted alone.
- Half is impossible without a model change: show the measured cost against quality curve and let product choose the point.
- Proving the saving holds: weekly cost per successful task per feature, with an alert when tokens per request grows.

**Mistakes to avoid:**
- Starting a self-hosting migration, a multi-month project, to hit a one-month target.
- Measuring cost per token instead of per successful task; a cheaper model that needs retries can cost more.

### Q. Your team serves a model from one GPU server and must move to a multi-replica setup with autoscaling on Kubernetes. Plan the migration.
**Short answer (45 seconds):** I would clarify peak load, SLOs, what is stateful (sessions, prefix cache locality), how much GPU capacity the cloud account can actually get in the region, and the budget. Then: a pinned engine image and flags, weights staged so pods load from local or shared storage, startup and readiness probes, a GPU node pool, a gateway that routes on live load, autoscaling on queue depth, graceful draining, and a gradual cutover with the old server kept as the rollback.

**Deeper explanation:**

```yaml
# per-replica essentials (sketch)
tolerations: [{key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}]
resources: {limits: {nvidia.com/gpu: 1}}
terminationGracePeriodSeconds: 180          # let in-flight streams finish
lifecycle: {preStop: {exec: {command: ["sleep", "15"]}}}   # leave the load balancer first
startupProbe: {httpGet: {path: /health, port: 8000}, periodSeconds: 10, failureThreshold: 60}
readinessProbe: {httpGet: {path: /health, port: 8000}, periodSeconds: 5}
volumeMounts: [{name: weights, mountPath: /models, readOnly: true}]
```

Steps in order:
1. GPU node pool with the NVIDIA device plugin or GPU operator, tainted so other pods stay off it.
2. Weights on a read-only volume or a node-local cache; no Hub download at startup.
3. A gateway that routes by least outstanding requests or engine queue depth, because request cost varies too much for round-robin, with affinity for sessions or tenants so prefix reuse survives.
4. KEDA scaling on `vllm:num_requests_waiting` per replica, minimum two replicas, fast scale-out, slow scale-in, and a PodDisruptionBudget so node upgrades never take every replica.
5. Draining: readiness fails, traffic stops, streams finish inside the grace period; test how your engine version handles SIGTERM.
6. Cutover: shadow traffic, then 10%, 50% and 100% by gateway weight, with the old server warm for a week.

Measure p95 TTFT during scale-out events, cold start time per stage, load skew between replicas and cost per day against the old box.

**Follow-ups they will ask:**
- The cloud has no GPUs when you scale: autoscaling only works within capacity you can get, so keep reserved baseline capacity and a provider fallback for overflow.
- Prefix cache hits drop after the move: compare hit rate before and after, and tighten affinity routing.

**Mistakes to avoid:**
- Autoscaling on CPU or GPU utilization.
- No grace period, so every deploy or scale-in cuts answers mid-stream.

### Q. A B2B product needs a customized model per customer: about 150 customers, each with its own LoRA adapter, on shared GPUs. Design it.
**Short answer (45 seconds):** I would clarify the traffic spread across customers (usually a few hot ones and a long tail), adapter ranks, the latency allowed for a rarely used customer, how often adapters change, and the isolation rules. The design is one pinned base model served with multi-LoRA in vLLM, a versioned adapter registry with an eval gate, routing that keeps each adapter on a small set of replicas, and a gateway that maps each API key to the adapters it may use.

**Deeper explanation:**

```bash
VLLM_ALLOW_RUNTIME_LORA_UPDATING=True vllm serve BASE_MODEL_ID \
  --enable-lora --max-loras 16 --max-cpu-loras 64 --max-lora-rank 32
  # internal network only: runtime loading must never be reachable by tenants
curl -X POST http://replica-3:8000/v1/load_lora_adapter -H "Content-Type: application/json" \
  -d '{"lora_name": "acme-v3", "lora_path": "/adapters/acme/v3"}'
```

Decisions that matter:
- Residency: `--max-loras` sets how many adapters can be active on the GPU at once, `--max-cpu-loras` how many wait in CPU memory, and the rest load from disk. Hot customers stay resident; a cold customer pays a load on the first request, which you measure and write into the SLO.
- Rank cap: `--max-lora-rank` sizes the adapter slots for the largest rank, so standardize ranks at training time instead of letting one rank-128 adapter cost memory for everyone.
- Routing: hash each adapter to two or three replicas so its weights and prefix cache stay warm.
- Security: the gateway overwrites the request's `model` field from the tenant's API key; a client must never be able to name another tenant's adapter.
- Lifecycle: adapters are versioned, scored on that customer's golden set before promotion, and tied to one base model version, so a base upgrade means re-validating or retraining all 150 and is planned as a project.

Measure per-adapter p95 TTFT, adapter load count and load time, per-tenant tokens and cost, and eval score per adapter version.

**Follow-ups they will ask:**
- When does a customer get a dedicated deployment: when its traffic alone fills a replica or the contract demands hard isolation; then merge the adapter into the weights.
- A quantized base: works, but train or at least validate the adapters against that exact base.

**Mistakes to avoid:**
- One full deployment per customer.
- Trusting the client to choose the adapter by name.

### Q. Launch is in three weeks. You must benchmark the serving stack and sign off a capacity number. How do you run it?
**Short answer (45 seconds):** I agree the SLO and the traffic forecast first, then build a workload that looks like production: real prompt and output length distributions, the real system prompt so prefix caching behaves as it will live, and multi-turn sessions. I drive it open-loop at rising request rates through the whole path (gateway, router, engine), find the rate where p95 TTFT or inter-token latency breaks the SLO, and sign off capacity per replica with a margin below it. A spike test, a soak test and a replica-kill drill come before the signature.

**Deeper explanation:**

```bash
vllm bench serve --backend openai-chat --endpoint /v1/chat/completions \
  --base-url http://gateway.internal --model MODEL_ID \
  --dataset-name random --random-input-len 2000 --random-output-len 300 \
  --request-rate 8 --num-prompts 2000 \
  --percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,95,99
```

Random fixed-length prompts are fine for comparing engine settings but lie about production, because they defeat or distort prefix caching; for the sign-off, replay sampled and anonymized real prompts or a dataset with matching percentiles. Drive load by request rate, not fixed concurrency: a closed-loop tool slows its own sending when the server slows, which hides exactly the queueing users would feel.

```text
sweep:  request rate up in steps until goodput stops rising; record TTFT, ITL, E2E at p50/p95/p99,
        tokens/s, waiting requests, KV usage, preemptions, error rate
spike:  2x forecast peak for five minutes      soak: forecast peak for several hours (leaks, drift)
drill:  kill a replica at peak, time recovery  client: measure chunk gaps through the real proxy
```

The sign-off page states the knee per replica, replicas for forecast peak at 70% of the knee plus one spare, cost per million tokens at that load, and the known limits, such as the longest prompt tested.

**Follow-ups they will ask:**
- Warm versus cold caches: run both, because the first minutes after a deploy are cold.
- Two tools disagree: they define TPOT and inter-token latency differently; use one tool for every comparison.
- The forecast is uncertain: present capacity as a curve and pair it with admission control for traffic above the forecast.

**Mistakes to avoid:**
- Benchmarking the engine port directly and signing off for the whole stack.
- Only fixed-concurrency runs, which never show a queue building.

### Practice
- Fill a sizing sheet for three cases: an 8B chat model for 200 sessions, a 70B model in FP8 for 50 sessions, and a vision-language model where each request carries two images; for each write weights, KV bytes per token, tokens in flight per card, replicas at a 70% target plus one spare, and the clarifying answers that would change the result.
- Turn a day of anonymized request logs into a benchmark workload with matching prompt and output length percentiles and the real system prompt, run it open-loop at three request rates against a vLLM endpoint, and find the knee.
- Serve a small base model with three LoRA adapters, load a fourth at runtime through the load endpoint, and compare TTFT for a resident adapter with a cold one.
- Write the one-page "cut spend by half" plan for an application you know: top three cost drivers, the change for each, the eval that guards it, and the metric that proves the saving.
- Say it out loud: the 200-user design in three minutes, starting with the clarifying questions and ending with the dashboard you would watch on launch day.

## Inference Incidents & Error Cases [Scenarios]

> Inference incidents rarely look like a clean outage. More often every response is a 200 while time to first token creeps up, streams stall, or answers quietly get worse. Structure every answer the same way: clarify the impact (which users, which model, since when, what changed), contain it (roll back the change, shed batch traffic, add capacity, cap max_tokens), diagnose with evidence (engine metrics, startup logs, client-side timings, Kubernetes events), fix the cause, and prevent a repeat with an alert, a test or a runbook. Interviewers listen for whether you separate queueing from compute from your own stack, and whether you mitigate before you chase the root cause.

### Concepts you must understand
- Split latency into gateway queue, engine queue, prefill, decode and delivery (proxy and client); the engine's histograms plus client-side timings show which part moved.
- GPU utilization only says a kernel was running; saturation shows up as waiting requests, KV cache usage near full and a rising preemption counter.
- The engine's startup log is the first diagnostic for memory problems: it reports weight memory, the KV cache size in tokens and the maximum concurrency at your max model length.
- Most inference incidents follow a change (model, quantization, engine version, flags, prompt, schema, proxy config), so "what changed" and a fast rollback come before deep debugging.
- Close every incident with a guardrail: an alert on the leading metric, a load or eval test in CI for that kind of change, or a config check that fails the deploy.

| Symptom or error | First check | Likely causes | Fix |
| --- | --- | --- | --- |
| `torch.OutOfMemoryError: CUDA out of memory` while vLLM starts | `nvidia-smi` for other processes; the startup memory lines | another process on the GPU, profiling batch too large, many images per prompt in a vision model | free the GPU, lower `--max-num-seqs` or `--max-num-batched-tokens`, set `--limit-mm-per-prompt` |
| Startup error that max model length does not fit the KV cache, ending "Try increasing `gpu_memory_utilization` or decreasing `max_model_len`" | `--max-model-len` against KV tokens in the log | default max length is the model's full context window | set `--max-model-len` to real need, FP8 KV, more memory or tensor parallelism |
| Pod in `CrashLoopBackOff`, events show `Liveness probe failed` with `connection refused` | `kubectl describe pod`, `kubectl logs --previous` | liveness probe fires while weights download or load | `startupProbe` sized to worst-case load, staged weights |
| Pod evicted: `The node was low on resource: ephemeral-storage` | where the Hugging Face cache is written | weights downloaded into the container filesystem | mount a volume for weights, set ephemeral-storage requests |
| `Cannot access gated repo for url` in startup logs | `HF_TOKEN` secret mounted and valid | gated model, token missing or revoked | mirror weights to your own storage, set `HF_HUB_OFFLINE=1` |
| p95 TTFT rises at peak while GPU utilization looks normal | `vllm:num_requests_waiting` and queue time per pod, CPU throttling | one hot replica, sequence cap reached, CPU-starved API server, prefix cache misses | fix routing, raise CPU limits, tune caps from a load test, add replicas |
| Streams freeze mid-answer, `vllm:num_preemptions_total` rising | KV cache usage gauge near 100% | too many long sequences in flight, generous max_tokens | lower `--max-num-seqs`, cap max_tokens, FP8 KV, more replicas |
| Throughput fell after moving to an INT4 checkpoint | kernel chosen in the startup log, batch size at peak | slow fallback kernel, weight-only overhead at large batch | Marlin kernels, FP8 on capable GPUs, or stay on BF16 |
| Answers changed after FP8 (wrong numbers, missing JSON fields) | golden set diff against BF16 at temperature 0 | FP8 KV cache turned on too, poor scales, a different checkpoint config | vendor FP8 checkpoint, keep KV in BF16, per-slice evals |
| `429` with `Rate limit reached for ... on tokens per min (TPM)` at peak | which limit, which caller, retry counts | batch jobs sharing the key at peak, retries multiplying, oversized max_tokens | pace by priority, pause batch, spill to a second provider, higher tier |
| `429` with `insufficient_quota`, or Anthropic `529` `overloaded_error` | error type in the response body | spend cap reached; provider-side overload | quota is not retryable, fix billing and alert; overload gets backoff and failover |
| Schema-constrained requests much slower, `finish_reason` is `length` | output token count and the tail of the output | whitespace loop inside the grammar, a new schema per request, slower backend fallback | static cached schemas, restricted whitespace, tight max_tokens |
| SSE arrives in bursts, not token by token | `curl -N` straight to the engine versus through the proxy | proxy buffering, compression middleware, a relay that batches | `X-Accel-Buffering: no` or `proxy_buffering off`, flush per event |

### Q. vLLM dies at startup with `torch.OutOfMemoryError: CUDA out of memory` on a GPU where the 8B model should easily fit. What do you do?
**Short answer (45 seconds):** I read the startup log before touching flags: it shows how far startup got (weights loaded, profiling run, KV allocation, CUDA graph capture) and how much memory each stage took. Then I check `nvidia-smi` for another process holding memory, and the settings that size the profiling pass and the cache: `--max-model-len`, `--max-num-seqs`, `--max-num-batched-tokens`, `--gpu-memory-utilization`, and images per prompt for a vision model. The fix is setting those to real need instead of defaults.

**Deeper explanation:**

```bash
nvidia-smi --query-compute-apps=pid,used_memory --format=csv    # anything else on this GPU?
kubectl logs deploy/llm --previous | grep -iE "memory|kv cache|concurrency|graph"
vllm serve MODEL_ID --max-model-len 8192 --max-num-seqs 64 --gpu-memory-utilization 0.85
```

Likely causes, ranked:
1. Another process holds memory: an old pod still terminating on the same GPU, a notebook, a second engine. vLLM plans its budget as a fraction of the card's total memory, so anything else resident leaves less than it planned for.
2. The profiling pass is too big: the engine runs a dummy forward pass at the maximum batch to measure peak activation memory, and for vision-language models it also profiles the maximum number of images at full resolution.
3. CUDA graph capture after KV allocation needs extra memory; with utilization set very high, capture fails. `--enforce-eager` confirms the diagnosis, but it slows every decode step, so it is not the fix.
4. Not an OOM but the KV error: the model's default context (128k tokens for Llama 3.1) does not fit, and the message ends "Try increasing `gpu_memory_utilization` or decreasing `max_model_len`". Set `--max-model-len`.

Prevent: pin every flag in the manifest, run a startup smoke test on the target GPU type in CI, alert when the logged KV cache size drops below the expected number of tokens, and request `nvidia.com/gpu: 1` so the scheduler never places two engines on one card.

**Follow-ups they will ask:**
- It broke after an engine upgrade: defaults and memory accounting change between versions; diff the startup log lines of both versions and pin the version.
- Does quantization fix it: it frees weight memory, but if the profiling pass is the problem, batch settings are the real fix.

**Mistakes to avoid:**
- Leaving `--enforce-eager` on permanently.
- Raising `--gpu-memory-utilization` toward 1.0 "to make room", which removes the margin CUDA graphs need.

### Q. At peak, p95 TTFT climbs from under a second to several seconds, but the fleet GPU utilization panel looks normal. Walk me through it.
**Short answer (45 seconds):** GPU utilization is the wrong panel, and a fleet average can hide one hot replica. I break TTFT into gateway queue, engine queue and prefill, per replica: `vllm:num_requests_waiting`, the queue time histogram, running sequences against the `--max-num-seqs` cap, KV usage, and CPU throttling on the pod. I contain with more replicas or by shedding batch traffic, then fix whichever stage moved.

**Deeper explanation:**

```text
engine queue up, running == max-num-seqs, KV low   -> cap too low for the GPU, or capacity
engine queue up, KV usage near 100%                -> KV-bound: long contexts, max_tokens, memory
engine queue flat, gateway TTFT high               -> your stack: connection pool, gateway CPU
queue flat, prefill time up                        -> longer prompts or prefix cache misses
one pod's queue up, others idle                    -> routing skew hidden by the fleet average
```

Diagnosis in order:
1. Per-pod p95 of queue time and TTFT in Prometheus, for example `histogram_quantile(0.95, sum by (le, pod) (rate(vllm:time_to_first_token_seconds_bucket[5m])))`; metric names vary by version, so read them from `/metrics`.
2. Load skew: sticky sessions or round-robin can stack long prompts on one replica.
3. CPU: the API server tokenizes, detokenizes and streams on CPU; a pod limited to a couple of cores throttles at high concurrency while the GPU waits. Check `rate(container_cpu_cfs_throttled_periods_total[5m])`.
4. Prompt changes: a timestamp or user ID added to the start of the system prompt collapses the prefix cache hit rate.
5. Gateway: an HTTP client connection pool limit in the Node or Python gateway queues requests before they reach the engine; compare gateway TTFT with engine TTFT.

Prevent: alert on waiting requests per replica and queue time p95, keep TTFT split into queue and prefill on the dashboard, and check prefix cache hit rate after every prompt deploy.

**Follow-ups they will ask:**
- Why does GPU utilization look fine: it measures whether any kernel ran during the sample window, not how much useful work was done.
- Only long-prompt requests are slow: prefill-bound; tune the chunked prefill budget or give long documents their own pool.

**Mistakes to avoid:**
- Buying GPUs before checking routing skew and CPU throttling.
- Looking only at engine metrics and missing a queue inside the gateway.

### Q. You switched to an AWQ 4-bit checkpoint to save memory, and peak throughput dropped instead of rising. Why, and what do you do?
**Short answer (45 seconds):** First I confirm the comparison is fair: same engine version, same flags, CUDA graphs on, same traffic replay. Then I check two things: which kernel the engine picked for the quantized layers, because a slow fallback path is common, and the batch size at peak, because weight-only INT4 helps small, memory-bound batches and turns into overhead when large batches make decode compute-bound. I decide with a benchmark at real concurrency: the Marlin kernel path, FP8 on capable GPUs, or BF16 with more replicas.

**Deeper explanation:**

```bash
kubectl logs deploy/llm-awq | grep -iE "quantiz|marlin|awq|eager|kv cache|concurrency"
vllm bench serve --backend openai-chat --endpoint /v1/chat/completions \
  --base-url http://llm-awq:8000 --model MODEL_ID-AWQ --request-rate 16 --num-prompts 1000
  # run the identical command against the BF16 deployment
```

Likely causes, ranked:
1. Slow kernel: vLLM has several AWQ kernels. Forcing `--quantization awq` on a model that could run the Marlin variant keeps the slower path, and vLLM warns about it in the log; let it auto-detect or use `awq_marlin`. Marlin also needs a recent enough GPU generation.
2. Wrong regime: weight-only quantization dequantizes inside every matmul. At small batch, decode is bandwidth-bound, and reading about a quarter of the weight bytes wins. At large batch, decode moves toward compute-bound and dequantization is extra work, while prefill gets no help at all.
3. Config drift: the new deployment lost a flag (`--enforce-eager` left on, a smaller `--max-num-seqs`, prefix caching off) or the quantized repo ships a different max length.
4. Freed memory unused: KV capacity grew but the sequence cap did not.

Fix: benchmark BF16, AWQ with Marlin and FP8 (on Hopper or Ada GPUs) at the real arrival rate, choose on goodput plus the golden-set eval, and keep the BF16 manifest ready for rollback. Prevent: any quantization change needs a throughput benchmark at production concurrency and an eval run before rollout.

**Follow-ups they will ask:**
- When is INT4 right: fitting a model onto fewer or cheaper GPUs, or latency-sensitive traffic at small batch.
- Why FP8 behaves differently: W8A8 runs the matmuls on FP8 tensor cores, so prefill and large batches speed up too.

**Mistakes to avoid:**
- Benchmarking at concurrency 1 and extrapolating to peak.
- Assuming a smaller model file means faster serving.

### Q. During a scale-out, new replicas sit in `CrashLoopBackOff` and every restart starts the model download again. How do you stop it?
**Short answer (45 seconds):** Contain first: pause the autoscaler so it stops adding pods that hammer the same download, and protect the replicas that are serving by shedding batch traffic. The usual cause, visible in pod events and the previous container's logs, is a liveness probe killing the container while weights still download or load. Fix it with a startup probe sized to the worst-case load time, and take the download off the startup path by staging weights in your own storage or on the node.

**Deeper explanation:**

```bash
kubectl get events --sort-by=.lastTimestamp | grep -iE "probe|evict|back-off"
kubectl describe pod llm-7c9f      # Last State: Terminated, Reason, Exit Code, probe failures
kubectl logs llm-7c9f --previous | tail -50
```

Likely causes, ranked:
1. Liveness probe without a startup probe: events show `Liveness probe failed` with `connection refused` because the server does not listen until loading finishes, then `Back-off restarting failed container`. If the cache sits in the container's writable layer, each restart downloads from zero.
2. Eviction: `The node was low on resource: ephemeral-storage` once tens of gigabytes land on the node's root disk.
3. The download itself: many pods pulling from the Hub at once, or a gated model with a missing token (`Cannot access gated repo for url`).

```yaml
startupProbe:  {httpGet: {path: /health, port: 8000}, periodSeconds: 10, failureThreshold: 120}
livenessProbe: {httpGet: {path: /health, port: 8000}, periodSeconds: 10, failureThreshold: 3}
env: [{name: HF_HUB_OFFLINE, value: "1"}]
volumeMounts: [{name: weights, mountPath: /models, readOnly: true}]
```

Liveness checks start only after the startup probe succeeds. Stage weights once from your own bucket to node NVMe or a read-only volume, and set `HF_HUB_OFFLINE=1` so the Hub is never on the startup path. Prevent: alert on restart counts for GPU pods, record cold start time per stage as a metric, and run a scale-out drill in staging after every model change.

**Follow-ups they will ask:**
- Why not a bigger `initialDelaySeconds`: a fixed delay is a guess that breaks when downloads slow down; the startup probe adapts.
- Download into an `emptyDir`: it survives container restarts within the pod, but every new pod still downloads.

**Mistakes to avoid:**
- Deleting pods repeatedly and hoping the next attempt is faster.
- Pulling from the public Hub on every production pod start.

### Q. Users report answers freezing for a second or two mid-stream at peak, and engine logs say sequences were preempted for lack of KV cache space. What do you do?
**Short answer (45 seconds):** This is KV cache pressure: more tokens are in flight than the cache can hold, so the scheduler pauses running sequences, frees their blocks and recomputes them later, which users see as freezes and everyone sees as a longer tail. I contain by lowering admitted concurrency or adding replicas and by capping max_tokens. Then I fix the budget: right-size `--max-num-seqs` and `--max-model-len`, add KV room with FP8 KV or quantized weights, and route long-context traffic to its own pool.

**Deeper explanation:**

```text
max by (pod) (vllm:gpu_cache_usage_perc)              # kv_cache_usage_perc in newer releases
sum by (pod) (rate(vllm:num_preemptions_total[5m]))
sum by (pod) (vllm:num_requests_running)
```

Mechanism: the scheduler admits sequences while blocks are free, but every sequence needs new blocks as it decodes. When none are left, it preempts the most recently admitted sequences; in recompute mode their KV is thrown away and prefilled again later. Older vLLM versions log that a sequence group "is preempted by PreemptionMode.RECOMPUTE mode because there is not enough KV cache space". The preempted user sees a freeze, and the recompute adds prefill work that slows everyone else.

Diagnosis: KV usage pinned near 100% with a non-zero preemption rate confirms it. Then find what changed in the request mix: answers grew longer after a prompt change, an agent runs with no max_tokens, a new feature sends long documents, or someone raised `--max-num-seqs` to chase throughput.

Fix:
- Lower `--max-num-seqs` so the engine admits only what fits; waiting in the queue costs TTFT, but it never freezes a stream already in progress.
- Cap max_tokens per feature at the gateway.
- More KV room: `--kv-cache-dtype fp8` after an eval, FP8 or INT4 weights, a bigger GPU or tensor parallelism.
- A separate pool for long-context requests.

Prevent: alert on preemptions sustained for five minutes and on KV usage above 90%, and load test with p95 output lengths, not averages.

**Follow-ups they will ask:**
- Swap versus recompute: swap copies KV to CPU memory and back, recompute redoes prefill; newer vLLM versions recompute.
- Why not raise `--gpu-memory-utilization`: a small gain that risks startup OOM.

**Mistakes to avoid:**
- Raising `--max-num-seqs` for throughput when KV is the limit.
- Watching only TTFT; preemption mostly shows up in inter-token latency.

### Q. After moving the production model from BF16 to FP8, support tickets say extraction answers contain wrong numbers and some JSON fields go missing. How do you investigate?
**Short answer (45 seconds):** I confirm it with data, route the affected feature back to the warm BF16 deployment, then find what actually changed. An FP8 switch often changes more than the weights: the KV cache dtype, the checkpoint (a different repo with its own config and generation defaults), the engine version or the chat template. I replay the failing tickets and the golden set against both deployments at temperature 0 and diff by slice.

**Deeper explanation:** Steps in order:
1. Contain: extraction traffic goes back to BF16; roll back first, investigate after.
2. Diff the deployments: engine version, `--quantization`, `--kv-cache-dtype`, `--max-model-len`, chat template, tokenizer files and `generation_config.json`. Recent vLLM versions take default sampling parameters from the checkpoint's generation config when a request does not set them, so a different FP8 repo can change sampling silently.
3. Replay:

```python
for case in failing_tickets + golden_set:
    a = call(BF16_URL, case.messages, temperature=0, seed=7)
    b = call(FP8_URL, case.messages, temperature=0, seed=7)
    record(case.id, case.slice, numbers_match(a, b), missing_fields(b, case.schema), schema_ok(b))
```

4. Isolate: run FP8 weights with a BF16 KV cache, then BF16 weights with an FP8 KV cache. Failures concentrated on long documents point at the KV cache, because exact values must be recalled through attention over long contexts; failures on short prompts point at the weights.

Likely causes, ranked: FP8 KV cache hurting long-context recall of exact values; coarse dynamic scales on a model with outlier layers; a community checkpoint calibrated on data unlike yours; sampling defaults or template drift. Fix: a vendor-published FP8 checkpoint or recalibration on domain data (for example with llm-compressor), BF16 KV for long-context features, sensitive layers kept in higher precision, or extraction kept on BF16 while chat uses FP8. Prevent: quantization changes pass the golden set with per-slice thresholds for numbers, field completeness and long documents, then shadow traffic and a canary.

**Follow-ups they will ask:**
- Temperature 0 differs between runs anyway: batch composition changes floating-point order, so compare many prompts and look for systematic differences.
- Why fields went missing despite a schema: constrained decoding only guarantees required fields; optional fields can be dropped.

**Mistakes to avoid:**
- Debugging FP8 in production for days instead of rolling back first.
- Blaming FP8 without separating weights, KV cache and configuration.

### Q. After turning on JSON schema structured output, some requests became much slower and a few run until max_tokens. How do you debug it?
**Short answer (45 seconds):** I separate three costs: compiling the grammar, masking tokens at each step, and output length. Slow only on the first request per schema means compilation; slightly different schemas per request defeat the compiled-grammar cache; slow requests ending with `finish_reason` `length` and trailing whitespace mean the model is looping inside a permissive grammar. Then I check which structured output backend actually ran, since an unsupported schema feature can force a slower one.

**Deeper explanation:** Steps in order:
1. Bucket slow requests by schema hash. Schemas generated per request (an enum built from user data, IDs inside descriptions) pay compilation every time; keep the schema static, move dynamic values into the prompt, and validate them after generation.
2. Read the output tails. JSON grammars usually allow arbitrary whitespace between tokens, and some models start emitting newlines or spaces that the grammar accepts until max_tokens. Fix it with the backend option that restricts whitespace, a tighter schema (`maxLength`, `maxItems`, `additionalProperties: false`) and a realistic max_tokens.
3. Check the backend: vLLM supports several (xgrammar, guidance, outlines) and in auto mode falls back when a schema uses features one backend lacks. Simplify the schema (complex patterns, deep recursion, large `oneOf` unions) to stay on the fast path.
4. Watch TPOT for unconstrained requests too: depending on the version, grammar masks are computed on CPU for the whole batch, so many constrained requests can slow everyone.
5. Field order: if `answer` comes before `reasoning`, the model commits early; reorder the schema.

Prevent: a registry of versioned static schemas, a warmup at deploy, an alert on the `length` finish rate per feature, and a CI test that runs each schema against the model with a timeout.

**Follow-ups they will ask:**
- Hosted APIs: same pattern; the first request with a new schema is slower, later ones reuse the compiled grammar.
- Why not drop constraints and parse: invalid output then costs retries, which is usually slower overall.

**Mistakes to avoid:**
- Going back to regex parsing with retries instead of fixing the schema.
- Ignoring `finish_reason` when debugging latency.

### Q. Users of the React chat UI see answers arrive in bursts every second or two instead of token by token, though engine metrics look smooth. Find and fix it.
**Short answer (45 seconds):** I find the hop that buffers by timing chunk arrival at each layer: directly against the engine, through the backend, through the proxy or CDN, and in the browser. The usual causes are a reverse proxy buffering the response (nginx buffers proxied responses by default), compression middleware waiting to fill a buffer, and an application relay that batches tokens. I fix that hop, then add a check that measures gaps between chunks through the real public path.

**Deeper explanation:**

```bash
# GNU date; repeat for the engine, the backend and the public URL
curl -sN http://vllm:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"MODEL_ID","stream":true,"messages":[{"role":"user","content":"count to 50"}]}' \
  | while read -r line; do echo "$(date +%s.%N) ${line:0:40}"; done
```

The first hop where timestamps clump together is the culprit. Likely causes, ranked:
1. Reverse proxy buffering: set `proxy_buffering off;` on the streaming location in nginx, or send `X-Accel-Buffering: no` from the backend.
2. Compression: Express `compression()` holds small writes in its buffer; call `res.flush()` after each event or skip compression for `text/event-stream`. Gzip middleware in Python frameworks can do the same.
3. The relay: in a design like CADBEATER's, where a worker writes tokens to Redis Streams and the SSE handler forwards them, a polling interval, a large read COUNT or "flush every N tokens" code creates bursts. Read with `XREAD BLOCK` and write each event as it arrives.
4. The client: reading with `response.body.getReader()` is correct; a heavy React re-render per token can lag, but not by seconds.

```js
res.set({ "Content-Type": "text/event-stream", "Cache-Control": "no-cache", "X-Accel-Buffering": "no" });
res.flushHeaders();
for await (const chunk of stream) {
  res.write(`data: ${JSON.stringify(chunk)}\n\n`);
  res.flush?.(); // added by the compression middleware
}
```

Prevent: a synthetic check that streams through the public URL and alerts when the p95 gap between chunks exceeds a threshold, and proxy config reviewed like code.

**Follow-ups they will ask:**
- Only some users see it: corporate proxies and security software can buffer; compare by network and offer a non-streaming fallback.
- Load balancer idle timeouts: a separate failure where long streams get cut, not bunched; raise the idle timeout above the longest generation.

**Mistakes to avoid:**
- Tuning the model or engine when the delay lives in nginx.
- Trusting engine metrics alone; only the client sees delivery.

### Practice
- Break it on purpose: on a small GPU, start vLLM with a long-context model and no `--max-model-len` and read the KV cache error, then fix it with the flag; next deploy it with a liveness probe and no startup probe and watch `kubectl get pods -w` reach `CrashLoopBackOff`; finally put nginx with default buffering in front of the stream and time the chunks with `curl -N`.
- Drive one replica past its KV capacity with long outputs at high concurrency and record KV usage, `vllm:num_preemptions_total` and client-side gaps between chunks; then lower `--max-num-seqs` and repeat.
- Simulate provider throttling with a mock server that returns 429 with a `retry-after` header, and verify that the batch class pauses, interactive traffic keeps flowing and total retries stay inside the retry budget.
- Send 200 structured-output requests with one static schema and 200 with a unique schema each; compare latency and count responses whose `finish_reason` is `length`.
- Say it out loud: pick any row of the error table and give the five-step answer (impact, contain, diagnose, fix, prevent) in ninety seconds.
