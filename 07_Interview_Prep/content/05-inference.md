# Inference Engineering

> This track covers how large language models are actually served: what happens on the GPU during prefill and decode, why memory bandwidth and the KV cache decide your throughput, how engines like vLLM and SGLang squeeze more requests out of one GPU, how quantization, speculative decoding and caching bend the cost curve, and how to route, scale and observe inference in production. Interviewers for AI Full Stack roles use this area to separate engineers who only call hosted APIs from engineers who understand what the API is doing and what it costs. You do not need to have run a GPU cluster to answer well, but you do need the mental model, the formulas and the trade-offs.

## Inference Fundamentals

> Interviewers start here to check whether you understand the machine underneath the API. A weak answer talks about "the model generating text"; a strong answer separates prefill from decode, names what each phase is bound by, can size a KV cache on a whiteboard, and distinguishes TTFT from TPOT when asked which latency matters for a chat product. Expect follow-ups that push on batch size and memory budgets.

### Concepts you must understand
- Prefill processes the whole prompt in one parallel forward pass and is compute-bound; decode produces one token per step per sequence and is memory-bandwidth bound because every step re-reads all the weights and the KV cache.
- The KV cache stores the attention keys and values of every token already seen so decode does not recompute them; it grows linearly with context length and with the number of concurrent sequences.
- KV cache bytes per token = 2 × layers × kv_heads × head_dim × bytes_per_element; grouped-query attention (fewer KV heads) is the main reason modern models have small caches.
- TTFT (time to first token) is queueing plus prefill; TPOT (time per output token) is the decode step time; end-to-end latency is roughly queue + TTFT + (output_tokens - 1) × TPOT.
- Batching raises aggregate throughput almost for free in the memory-bound regime because the weights are read once per step for the whole batch; per-user latency rises slowly until the batch hits the compute roofline.
- GPU memory budget = weights + KV cache + activations and workspace + framework overhead; whatever is left after weights decides how many tokens can be in flight, which decides concurrency.
- Tokens per second per user is a latency measure; aggregate tokens per second is a throughput measure; goodput (requests that met the SLO) is what the business actually pays for.
- Sampling parameters are cheap compared to the forward pass, but `n` greater than 1, beam search, logprobs and grammar-constrained decoding do add measurable cost.

### Q. Walk me through what happens on the GPU from the moment a prompt arrives until the last token is streamed back.
**Short answer (45 seconds):** The prompt is tokenized and pushed through the model once in the prefill phase: all prompt tokens are processed in parallel with large matrix-matrix multiplies, the keys and values for every token are written into the KV cache, and the first output token is sampled. Then the decode phase loops: each step feeds in the last token, attends over the cached keys and values, reads every weight once, and emits one more token. Streaming sends each decoded token to the client as it is produced until an end-of-sequence token, a stop string, or max_tokens.

**Deeper explanation:** Prefill is compute-bound. With a 2,000 token prompt the GPU does roughly 2 × parameters × 2,000 floating-point operations in one pass, which keeps the tensor cores busy. Decode is the opposite: one token per step per sequence means a matrix-vector multiply per layer, so the GPU spends most of its time moving weights from HBM into the compute units rather than computing.

```text
request -> tokenize -> [PREFILL: all prompt tokens, parallel, compute-bound]
        -> write KV cache, sample token 1          (this moment is TTFT)
        -> [DECODE loop: 1 token/step, reads weights + KV, bandwidth-bound]
        -> stream token -> ... -> EOS or max_tokens
```

A serving engine interleaves the decode steps of many requests into one batch so that a single read of the weights serves all of them, and it schedules new requests' prefill in between. That scheduling, not the model, is what vLLM adds over a plain `model.generate()` call in a notebook.

**Follow-ups they will ask:**
- Where does first-token latency come from: prefill compute, proportional to prompt length, plus any time spent waiting in the queue.
- Why not recompute attention over the prompt every step: that would turn each decode step into a full prefill; the KV cache trades memory for that compute.

**Mistakes to avoid:**
- Describing generation as one monolithic "model call"; the two-phase split is the whole point of the question.
- Saying decode is slow because of compute; it is slow because of memory bandwidth.

### Q. Why is the decode phase memory-bandwidth bound, and what does that imply for scaling throughput?
**Short answer (45 seconds):** In decode each sequence contributes one token per step, so per layer the work is a matrix-vector product: every weight byte is read from HBM to perform only a couple of floating-point operations. GPUs can do hundreds of FLOPs per byte they read, so the compute units sit idle waiting on memory. Step time is approximately bytes_read divided by memory bandwidth. The implication is that batching more sequences into a step raises throughput almost linearly, because the same weight read now serves many tokens.

**Deeper explanation:** Arithmetic intensity is FLOPs per byte moved. For FP16 weights one token needs about 2 FLOPs per parameter and reads 2 bytes per parameter, so intensity is about 1 FLOP per byte at batch 1 and roughly B FLOP per byte at batch B. A GPU whose peak compute divided by peak bandwidth is a few hundred FLOP per byte (its ridge point) stays memory-bound until the batch approaches that size, ignoring KV cache reads.

Illustrative round numbers: 7B parameters in FP16 is 14 GB of weights. On a GPU with 2 TB/s of bandwidth one decode step cannot take less than 14 / 2000 s = 7 ms, so a single user sees at most about 140 tokens/s. At batch 32 the same 7 ms step produces 32 tokens, roughly 4,500 tokens/s aggregate, while each user still sees close to 140 tokens/s.

```text
step_time        ≈ (weight_bytes + kv_bytes_in_flight) / bandwidth
per_user_tok_s   ≈ 1 / step_time
aggregate_tok_s  ≈ batch_size / step_time
```

**Follow-ups they will ask:**
- What changes at very large batch: you cross the ridge point and become compute-bound, so per-token latency starts to rise with batch size.
- Why does weight quantization speed up decode: fewer bytes per parameter means fewer bytes to move per step.

**Mistakes to avoid:**
- Quoting FLOPs as the reason small-batch inference is slow.
- Forgetting that the KV cache is also read every step, which is why long contexts hurt TPOT.

### Q. How big is the KV cache, and how do you calculate it for a given model and context length?
**Short answer (45 seconds):** Per token the cache holds one key vector and one value vector for every layer and every KV head: bytes_per_token = 2 × n_layers × n_kv_heads × head_dim × bytes_per_element. Multiply by the number of tokens in flight across all concurrent sequences to get total KV memory. Grouped-query attention shrinks n_kv_heads, which is why newer models fit many more concurrent users on the same GPU.

**Deeper explanation:** Worked example, illustrative but with realistic shapes. A Llama-2-7B style model has 32 layers, 32 KV heads, head_dim 128 and FP16 elements: 2 × 32 × 32 × 128 × 2 bytes = 524,288 bytes, about 0.5 MB per token. A 4,096 token conversation holds 2 GB of KV cache, and 20 such conversations in flight need 40 GB, more than the 14 GB of weights. A Llama-3-8B style model with the same 32 layers but 8 KV heads needs 2 × 32 × 8 × 128 × 2 = 131,072 bytes, 128 KB per token, four times less.

```python
def kv_bytes(layers, kv_heads, head_dim, bytes_per_el, tokens):
    return 2 * layers * kv_heads * head_dim * bytes_per_el * tokens

print(kv_bytes(32, 32, 128, 2, 4096) / 2**30)  # ~2.0 GiB (MHA, 7B style)
print(kv_bytes(32, 8, 128, 2, 4096) / 2**30)   # ~0.5 GiB (GQA, 8B style)
```

Read these values from a model's `config.json`: `num_hidden_layers`, `num_key_value_heads`, and `head_dim` or `hidden_size / num_attention_heads`. Multi-head latent attention (DeepSeek-V2 and V3) compresses keys and values into a small latent vector, which changes the formula and is one reason those models are cheap to serve at long context.

**Follow-ups they will ask:**
- How does KV cache quantization help: FP8 KV halves bytes_per_element, so twice as many tokens fit.
- How does the cache affect cost: memory per user sets concurrency per GPU, which sets cost per token.

**Mistakes to avoid:**
- Forgetting the factor of 2 for K and V, or using query heads instead of KV heads for a GQA model.
- Sizing for one sequence and forgetting that concurrency multiplies it.

### Q. Define TTFT, TPOT and end-to-end latency. Which one do you optimize for a chat product versus a batch summarization pipeline?
**Short answer (45 seconds):** TTFT is the time from request to the first streamed token: queueing plus prefill. TPOT is the average gap between subsequent tokens, set by the decode step time. End-to-end latency is TTFT plus TPOT times the remaining output tokens. For chat, users judge TTFT and whether tokens arrive faster than they read, so both matter. A batch summarization pipeline has no one watching a stream, so aggregate throughput and cost per request matter and TTFT is irrelevant.

**Deeper explanation:**

```text
e2e ≈ queue_wait + prefill(prompt_len) + (out_tokens - 1) × TPOT
Illustrative: queue 50 ms, prefill 300 ms, 400 output tokens at 25 ms each
e2e ≈ 0.05 + 0.30 + 399 × 0.025 ≈ 10.3 s        TTFT ≈ 0.35 s
```

The example shows why decode dominates long answers: halving prefill saves 150 ms, while a 20% TPOT improvement saves two seconds. Reading speed is a useful anchor: TPOT around 50 ms (20 tokens/s) is usually fine for a human reading a chat answer, while agent loops that feed their own output into the next step want much lower TPOT because no human is pacing them. Report percentiles (p50, p95, p99) split by prompt-length bucket, because TTFT grows with prompt length and a single average hides the long-prompt tail. When comparing engines, also look at goodput: the rate of requests that met both the TTFT and the TPOT targets, which is what capacity planning should be based on.

**Follow-ups they will ask:**
- Which SLO for a coding assistant: tight TTFT because the user is blocked waiting, and high tokens/s because completions are read as a block, not word by word.
- How do you cut TTFT for long RAG prompts: prefix caching of shared context, chunked prefill so decode traffic does not stall it, and retrieving less.

**Mistakes to avoid:**
- Giving one "latency" number without saying which phase it measures.
- Optimizing TTFT for a background pipeline where only throughput and cost matter.

### Q. Explain the throughput versus latency trade-off when you increase batch size.
**Short answer (45 seconds):** Larger batches amortize the weight reads over more tokens, so aggregate throughput climbs steeply at first while each user's TPOT barely changes. Past the point where the GPU becomes compute-bound, or where KV cache reads dominate, every extra sequence makes each step slower, so per-user latency rises and throughput flattens. You choose the operating point by setting a TPOT or TTFT target and admitting as many sequences as still meet it.

**Deeper explanation:** Picture per-user latency plotted against aggregate throughput. The knee of the curve is where interactive traffic should run; offline batch jobs run far to the right. Three things push the knee left: long contexts (more KV bytes per step), large models (more weight bytes, less headroom), and prefill of new requests being mixed into decode steps, which lengthens those steps for everyone.

```text
aggregate tok/s
   |                ______________  compute-bound plateau
   |            ___/
   |        ___/        <- knee: run chat traffic here
   |    ___/
   |___/
   +----------------------------------- concurrent sequences
   per-user TPOT: flat at first, then rises with batch
```

Continuous batching engines expose the knobs: vLLM `--max-num-seqs` caps concurrent sequences and `--max-num-batched-tokens` caps tokens per step, which bounds how much prefill can be packed into a step. Lowering them lowers tail latency and costs throughput. Memory is a hard cap too: when the KV cache is full, vLLM preempts sequences, which shows up as a sudden latency spike, so KV usage is a leading indicator of trouble.

**Follow-ups they will ask:**
- How do you find the knee: load test with increasing concurrency, plot p95 TPOT and TTFT against throughput, stop where the SLO breaks.
- Why do prefill requests hurt decode latency: a 10k-token prefill in the same step takes far longer than a decode step, so everyone waits; chunked prefill fixes this.
- Does the trade-off exist for hosted APIs: yes, it is why providers can sell cheaper batch tiers and faster priority tiers.

**Mistakes to avoid:**
- Saying "bigger batch is always better" or "always worse"; the regime decides.
- Ignoring memory as the first cap you hit, usually before compute.

### Q. How do you build a GPU memory budget for serving a model?
**Short answer (45 seconds):** Start with the card's memory, subtract weights (parameters × bytes per parameter), subtract a reserve for activations, the CUDA context and workspace, and what remains is KV cache. Divide that by KV bytes per token to get total tokens in flight, then by your expected context per request to get concurrency. If that concurrency is below what traffic needs, you quantize, add tensor parallelism, or add replicas.

**Deeper explanation:** Illustrative example on an 80 GB card: a 7B-class model in FP16 takes 14 GB of weights. vLLM's `--gpu-memory-utilization` (default 0.9) caps total usage at 72 GB; the engine profiles a forward pass at maximum batch to measure peak activation memory, say 4 GB, and hands the rest, about 54 GB, to KV cache blocks. At 0.5 MB per token (32 layers, 32 KV heads) that is about 108k tokens in flight: around 26 conversations of 4k tokens, or 13 of 8k. Switch to a GQA model at 128 KB per token and the same budget holds over 400k tokens.

```text
budget      = card_memory × utilization
kv_memory   = budget - weights - peak_activations - overhead
tokens_fit  = kv_memory / kv_bytes_per_token
concurrency = tokens_fit / avg_context_per_request
```

Two practical notes. `--max-model-len` should match your real maximum, because one enormous request can otherwise hold a large share of the blocks. The activation reserve grows with `--max-num-batched-tokens` because prefill activations scale with tokens per step, so throughput knobs and memory knobs are coupled.

**Follow-ups they will ask:**
- What happens when KV fills up: the scheduler stops admitting new sequences and may preempt running ones, so latency jumps; alert on KV usage above roughly 90%.
- How does quantizing weights change the budget: INT4 weights free roughly 10 GB in this example, all of which becomes KV cache.

**Mistakes to avoid:**
- Counting only weights and declaring "it fits"; a model that fits with no KV room serves one user, slowly.
- Forgetting that concurrency, not model size, is what the KV budget buys you.

### Q. Do sampling parameters affect cost or latency?
**Short answer (45 seconds):** Temperature, top-p and top-k are applied to the logits after the forward pass, so they are nearly free compared to the model itself. What costs money is anything that multiplies tokens generated or work per token: `n` greater than 1, beam search, logprobs for many candidates, a generous `max_tokens` that lets the model ramble, and constrained decoding that masks the vocabulary every step. Temperature 0 skips a sort, but the saving is tiny.

**Deeper explanation:** Per step the sampler takes the final logits over the vocabulary (tens of thousands to over 100k entries), applies penalties, temperature, top-k and top-p filtering, and samples. Engines run this on the GPU for the whole batch, so it is a small fraction of a step. Where cost actually shows up:

- `n` greater than 1 multiplies decode work and KV cache per request; engines share the prompt's prefill and KV blocks across candidates (vLLM forks blocks copy-on-write), so prefill is paid once but decode n times. Hosted APIs bill input once and output n times.
- Beam search keeps several hypotheses alive and expands all of them every step; it is expensive enough that vLLM moved it out of the core sampler into a separate utility.
- `logprobs` with many alternatives adds data to copy and serialize on every step.
- `max_tokens` costs nothing by itself but bounds the worst-case bill and tells the scheduler how long a request may hold KV blocks.
- Stop sequences are matched after detokenization; many long stop strings add CPU work, not GPU time.

**Follow-ups they will ask:**
- Does temperature 0 make outputs deterministic: mostly, but batch composition and floating-point reduction order can still change results across runs.
- Why cap max_tokens for an agent: a tool loop that goes wrong can otherwise burn thousands of tokens before anyone notices.
- Does a repetition penalty cost much: no, it is one vector operation over the vocabulary per step.

**Mistakes to avoid:**
- Claiming lower temperature is meaningfully faster.
- Forgetting that `n` samples multiply output cost even though input is billed once.

### Practice
- Pull `config.json` for three open models and compute KV bytes per token from `num_hidden_layers`, `num_key_value_heads` and head_dim; then compute how many 8k-token conversations fit on a 24 GB and an 80 GB card after FP16 weights.
- Run a small model with Ollama or vLLM, stream with a client that timestamps every chunk, and compute TTFT and TPOT for prompts of about 100, 1,000 and 5,000 tokens; confirm TTFT grows with prompt length while TPOT stays flat.
- Load-test the same server at concurrency 1, 4, 16 and 64, record aggregate tokens/s against p95 TPOT, and mark the knee of the curve.
- Say it out loud: in 60 seconds, explain why decode is memory-bound and what batching does about it, using the 14 GB over 2 TB/s example.

## Serving Engines & Stacks

> Interviewers ask about engines to see whether you can pick and operate one, not recite a list. A weak answer says "vLLM is fast". A strong answer explains the two ideas that made vLLM matter (PagedAttention and continuous batching), knows the OpenAI-compatible surface that lets you swap engines, can say when TensorRT-LLM is worth its build step, and knows what a replica is doing during the minutes before it serves its first request.

### Concepts you must understand
- vLLM combines PagedAttention (KV cache in fixed-size blocks with a per-sequence block table, so no contiguous reservation and almost no fragmentation) with continuous batching (requests join and leave the batch at every decode step).
- Static batching waits for the whole batch to finish, so a 20-token answer idles until a 2,000-token answer completes; continuous batching frees the slot immediately and admits a waiting request into the next step.
- SGLang's RadixAttention keeps the KV cache in a radix tree keyed by token sequence, so any shared prefix across requests is reused at token granularity; it also offers a frontend DSL and fast constrained decoding.
- TensorRT-LLM compiles a model into GPU-specific engines with tuned kernels (including FP8 on Hopper-class GPUs); top performance on NVIDIA at the cost of a build step, less flexibility and slower support for new architectures.
- Hugging Face TGI is a Rust and Python server with continuous batching, paged attention and broad quantization support, tightly integrated with the Hub.
- llama.cpp runs GGUF models on CPUs, Apple Silicon or with partial GPU offload; Ollama wraps it with model management and an HTTP API; both expose OpenAI-compatible endpoints, which makes them the standard local development target.
- The OpenAI-compatible API (`/v1/chat/completions` with SSE streaming) is the de facto interface: change `base_url` and the same client code talks to vLLM, SGLang, TGI, Ollama or a hosted provider.
- One model per GPU with replicas is the default; tensor parallelism is for when the weights do not fit or per-token latency must drop, and it needs NVLink-class interconnect; pipeline parallelism works across nodes but adds latency.
- Startup is image pull, weight download, load to GPU, CUDA graph capture or compilation, and warmup; it takes minutes for large models, so probes, warm pools and local weight caches are part of the design.

### Q. Explain PagedAttention and why it mattered so much.
**Short answer (45 seconds):** Before vLLM, engines reserved one contiguous KV cache region per request sized for the maximum possible length, so most GPU memory was reserved but unused and could not be shared. PagedAttention splits each sequence's KV cache into fixed-size blocks (16 tokens by default in vLLM), stores them wherever free blocks exist, and keeps a per-sequence block table mapping logical to physical blocks, exactly like virtual memory pages. Waste drops to less than one block per sequence, so many more sequences fit in the batch, which is directly more throughput, and blocks can be shared between sequences for parallel sampling and prefix caching.

**Deeper explanation:** The attention kernel gathers keys and values through the block table, so it reads non-contiguous memory on purpose. Block tables enable copy-on-write: n parallel samples of one prompt share the prompt's blocks and only diverge in freshly allocated blocks. The engine's block manager behaves like an allocator, and the count of free blocks is the real capacity metric of the server.

```text
seq A logical blocks: [0][1][2][3]     block table A: 0->7  1->2  2->9  3->4
physical GPU blocks:  [0][1][2][3][4][5][6][7][8][9]
                            A1    A3       A0    A2
```

Compare with static allocation: with a maximum length of 8k and typical conversations of a few hundred tokens, almost all of the reserved memory sits idle. With paging that memory becomes more concurrent sequences, and in the memory-bound decode regime more sequences per step is almost free throughput.

**Follow-ups they will ask:**
- What is preemption: evicting a running sequence when blocks run out so others can finish; it shows up as a latency spike and a counter in the metrics.
- How does this relate to prefix caching: identical prefix blocks can be hashed and shared across requests because blocks are already independent units.

**Mistakes to avoid:**
- Describing PagedAttention as a faster attention algorithm; it is memory management, and the kernel change exists only to support the indirection.
- Confusing it with FlashAttention, which is about avoiding the N by N attention matrix in HBM.

### Q. What is continuous batching, and how is it different from static or dynamic batching?
**Short answer (45 seconds):** Static batching groups requests, runs the whole group to completion, then starts the next group, so short answers wait for the longest one and slots go empty as sequences finish. Continuous batching, also called iteration-level scheduling after the Orca paper, makes the decision at every decode step: finished sequences leave immediately, waiting requests are admitted and prefilled, and the batch stays full. Dynamic batching (as in Triton for classic models) only waits a few milliseconds to collect requests into a fixed batch; it does not reschedule mid-generation.

**Deeper explanation:** Each scheduler iteration does the same loop.

```python
  # one scheduler iteration, simplified
running = [s for s in running if not s.finished]      # free their KV blocks
while waiting and has_free_blocks(waiting[0]) and token_budget_left():
    running.append(waiting.pop(0))                     # admitted; prefill joins this step
out = model.forward(batch_of(running))                 # prefill tokens + 1 decode token per running seq
for s in running:
    s.append(sample(out[s]))                           # stream token to client
```

Because prefill tokens for new requests share a step with decode tokens of running requests, a large prompt stretches that step for everyone; engines therefore cap tokens per step (`--max-num-batched-tokens` in vLLM) and split long prompts across steps with chunked prefill. The scheduler is also where policy lives: first-come-first-served versus priority, the cap on running sequences (`--max-num-seqs`), and what to preempt when memory is tight. Hosted APIs use the same mechanism, which is why their latency drifts with load.

**Follow-ups they will ask:**
- Which metric reveals a scheduling problem: `vllm:num_requests_waiting` growing while the GPU is busy means you are at capacity or over-admitting prefill.
- Why does a short request sometimes take long: it joined a step with a huge prefill, or it was preempted.
- Can the client batch instead: no, batching must happen in the engine where the forward pass is built.

**Mistakes to avoid:**
- Treating batching as "collect requests, send them together"; the point is rescheduling at every step.
- Forgetting that admitting more requests trades per-token latency for throughput; it is a policy, not a free win.

### Q. How does SGLang's RadixAttention differ from vLLM's prefix caching, and when would you choose SGLang?
**Short answer (45 seconds):** Both reuse KV cache across requests that share a prefix. vLLM's automatic prefix caching hashes each full block of tokens (chained with the previous block's hash) and reuses matching physical blocks. SGLang stores the cache in a radix tree keyed by token sequences, matches the longest shared prefix at token granularity, evicts with LRU over tree nodes, and schedules waiting requests to maximize hits. I would consider SGLang for workloads with heavy prefix sharing (agents, few-shot prompts, long system prompts) and lots of structured output; vLLM is my default general-purpose server.

**Deeper explanation:** Granularity and scheduling are the real differences, not the idea. Token-level matching catches partial-block overlaps; cache-aware scheduling groups requests that share prefixes into the same steps. SGLang also brings a frontend language (`sgl.function` with `gen`, `select` and `fork`) for multi-call programs, and compressed finite state machines plus jump-forward decoding for JSON-constrained generation, where fixed keys are inserted without running the model. vLLM has broader hardware support, a larger ecosystem, multi-LoRA serving and very fast new-model support. Both expose OpenAI-compatible servers (`vllm serve MODEL_ID` and `python -m sglang.launch_server --model-path MODEL_PATH`), and both publish Prometheus metrics. The honest answer is that the throughput lead changes release to release, so you benchmark on your own traffic shape.

**Follow-ups they will ask:**
- Does prefix caching require identical tokens: yes, the prefix must match from position 0; one changed character early in the system prompt defeats it.
- Does it work across replicas: no, each process has its own cache, so you need cache-affinity routing at the load balancer.
- What does it save: the prefill compute for the matched prefix, so TTFT for a long shared system prompt collapses to the prefill of the new tokens.

**Mistakes to avoid:**
- Saying prefix caching stores "responses"; it stores KV tensors, and generation still runs.
- Claiming one engine is simply faster without naming the workload.

### Q. When would you pick TensorRT-LLM over vLLM, and what do you give up?
**Short answer (45 seconds):** Pick TensorRT-LLM when you are fully on NVIDIA hardware, serve a stable model for a long time at high volume, and need the last bit of throughput or latency, especially with FP8 on Hopper-class GPUs. You give up flexibility: a compile step per model, GPU type and configuration; slower support for brand-new architectures; a heavier stack (often Triton Inference Server with the TensorRT-LLM backend); and a smaller pool of engineers who know it.

**Deeper explanation:** TensorRT-LLM builds an optimized engine: fused kernels, tiling chosen for the specific GPU, in-flight batching (its continuous batching), a paged KV cache, FP8 and INT4 quantization, and tensor and pipeline parallelism. The build is redone when batch limits, sequence lengths, parallelism or the GPU type change. vLLM loads Hugging Face checkpoints directly, supports new models within days, and runs as a single container.

| Factor | TensorRT-LLM | vLLM |
| --- | --- | --- |
| Peak performance on NVIDIA | highest, FP8 kernels | strong, improving every release |
| New model support | lags | fast |
| Ops complexity | engine builds, Triton or trtllm-serve | one container, `vllm serve` |
| Hardware | NVIDIA only | NVIDIA, AMD and others |

The decision is a cost question: if GPUs are a large line item and the model is stable, the engineering time for TensorRT-LLM pays back; if you are iterating on models or far from saturating your GPUs, it does not.

**Follow-ups they will ask:**
- Would you start a new project on TensorRT-LLM: no, start on vLLM and move only the hot, stable path after measuring.
- What about NVIDIA's packaged containers: NIM bundles optimized engines behind an OpenAI-compatible API, trading control for convenience.
- Does the compile step affect autoscaling: yes, engines must be built ahead of time and distributed, never at pod start.

**Mistakes to avoid:**
- Choosing by a benchmark headline without costing the build and operations work.
- Optimizing the engine when the real problem is 15% GPU utilization.

### Q. You need the model on a laptop for a demo and the same model in production. What do you use for each, and how do you keep the application code identical?
**Short answer (45 seconds):** Locally, Ollama (or `llama-server` from llama.cpp) serving a GGUF quantized model on an OpenAI-compatible endpoint. In production, vLLM serving the FP16 or FP8 checkpoint behind the same API shape. The application uses one OpenAI client with `baseURL` and `model` read from configuration, so only environment variables change. I would expect differences in output quality from quantization and in feature support for tool calling and JSON mode, so I keep a contract test that runs the same prompts against both.

**Deeper explanation:**

```js
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: process.env.LLM_BASE_URL,            // http://localhost:11434/v1 or http://vllm:8000/v1
  apiKey: process.env.LLM_API_KEY ?? "not-needed",
});
const stream = await client.chat.completions.create({
  model: process.env.LLM_MODEL, messages, stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
```

Where the two diverge: chat templates and tool-call parsing (vLLM needs `--enable-auto-tool-choice --tool-call-parser PARSER_NAME` for function calling and the parser is model-family specific); Ollama's default context window is short, so set `num_ctx` explicitly; a Q4 GGUF model will not match FP16 outputs token for token, so local is for functional testing, not quality sign-off. Run vLLM locally too when you have an NVIDIA GPU: `docker run --gpus all -p 8000:8000 vllm/vllm-openai:latest --model MODEL_ID --max-model-len 8192`.

**Follow-ups they will ask:**
- Can Ollama serve production traffic: it handles some parallelism, but it is not built for high-throughput multi-user serving.
- How do you test the swap: a golden prompt set checked for schema adherence and tool-call shape against both backends in CI.
- Embeddings too: both expose `/v1/embeddings` for embedding models, and vLLM serves pooling models alongside generation.

**Mistakes to avoid:**
- Signing off quality on a 4-bit local model and being surprised by production outputs.
- Letting provider-specific fields leak into application code so the swap is no longer a config change.

### Q. One big GPU or several smaller ones: how do you decide between tensor parallelism and replicas?
**Short answer (45 seconds):** If the model plus a useful KV budget fits on one GPU, run one model per GPU and add replicas behind a load balancer: linear throughput scaling, no interconnect dependency, and the smallest failure domain. Use tensor parallelism when the weights do not fit (a 70B model in FP16 is about 140 GB, so at least two 80 GB cards and realistically four for KV room) or when you need lower per-token latency, because each GPU then reads only its slice of the weights per step. Tensor parallelism costs an all-reduce per layer, so it needs NVLink-class bandwidth and gives diminishing returns.

**Deeper explanation:** Rule of thumb: tensor parallelism inside a node over NVLink, pipeline parallelism across nodes, data parallelism (replicas) for throughput. The tensor parallel degree must divide the number of attention heads. Tensor parallelism also pools KV cache across the group, which allows longer contexts and more concurrency per replica, while replicas keep caches separate. For an 8B model on an 8-GPU node, eight replicas beat one TP 8 instance on throughput and resilience; for a 70B model, TP 4 gives two replicas per node, and TP 8 gives one replica with a huge KV budget.

```bash
vllm serve MODEL_ID_70B --tensor-parallel-size 4 --max-model-len 16384
vllm serve MODEL_ID_8B  --max-model-len 8192     # one replica per GPU, scale with pods
```

Pipeline parallelism assigns layers to stages and passes activations between them; it needs micro-batching to avoid idle bubbles and adds hop latency per token, so it is a tool for crossing node boundaries, not for speed.

**Follow-ups they will ask:**
- Can you combine them: yes, TP within the node times PP across nodes, and replicas of the whole arrangement.
- How does TP change the failure domain: one GPU failure takes down the whole group, so one replica, not one eighth of capacity.

**Mistakes to avoid:**
- Choosing TP 8 for a small model "for speed" and losing both efficiency and replica independence.
- Declaring a model "fits" without leaving KV cache room.

### Q. A new replica takes six minutes before it serves its first request. Walk me through what is happening and how you would shorten it.
**Short answer (45 seconds):** Kubernetes schedules the pod, possibly waiting for a GPU node to come up; the node pulls a multi-gigabyte CUDA image; the engine downloads tens of gigabytes of weights, loads them into GPU memory, captures CUDA graphs or compiles, and runs warmup. You attack each stage: a pre-provisioned warm node pool, images pre-pulled on nodes, weights staged on node-local NVMe or a read-only volume, fast or streaming loaders, and a startup probe so Kubernetes does not kill the pod mid-load. Then you keep headroom replicas so scaling is never on the critical path of a user request.

**Deeper explanation:**

```yaml
containers:
- name: vllm
  image: vllm/vllm-openai:PINNED_TAG
  args: ["--model", "/models/llama-8b-instruct", "--max-model-len", "8192"]
  volumeMounts: [{name: weights, mountPath: /models, readOnly: true}]
  startupProbe:   {httpGet: {path: /health, port: 8000}, periodSeconds: 10, failureThreshold: 90}
  readinessProbe: {httpGet: {path: /health, port: 8000}, periodSeconds: 5}
  resources: {limits: {nvidia.com/gpu: 1}}
```

Weights in safetensors load fast; vLLM's `--load-format` also supports streaming loaders (tensorizer, Run:ai Model Streamer) that move tensors to the GPU while reading. `--enforce-eager` skips CUDA graph capture, which starts faster but makes every decode step slower, so it is a debugging switch. Set `HF_HUB_OFFLINE=1` in production so a Hub outage cannot block startup. Send a few representative requests before flipping readiness so the first user does not pay for lazy initialization. Because cold start is measured in minutes, autoscale on leading indicators like queue depth and run N+1 replicas.

**Follow-ups they will ask:**
- Why not bake weights into the image: it works but images become enormous and every model change is a rebuild; a shared read-only volume or object store with a node cache is the usual compromise.
- How do you know which stage is slow: the engine logs each phase with timestamps; measure them and attack the largest.

**Mistakes to avoid:**
- A liveness probe with a short failure threshold, which kills the pod during weight loading and creates a crash loop.
- Scaling from zero for interactive traffic and expecting sub-second latency.

### Practice
- Run vLLM in Docker with a small instruct model, call `/v1/chat/completions` with streaming, then watch `/metrics` for running and waiting request counts and KV cache usage during a load test.
- Run the same 30-prompt set against Ollama locally and vLLM, and diff schema adherence and tool-call formatting; write down every place the two backends disagreed.
- Read the vLLM startup log, label each phase (weight load, memory profiling, CUDA graph capture) with its duration, then rerun with `--enforce-eager` and compare both startup time and per-token latency.
- Say it out loud: explain PagedAttention in 45 seconds using the virtual memory analogy, then explain in another 30 seconds why continuous batching is a scheduler change and not a kernel change.

## Quantization

> Interviewers use quantization to test whether you understand where the bytes go. A weak answer says "quantization makes the model smaller and a bit worse". A strong answer separates weight-only from weight-and-activation quantization and says which phase each one speeds up, names the formats and tools you would actually use, sizes the memory saving, and comes with a validation plan and a list of cases where you would not quantize at all.

### Concepts you must understand
- Numeric formats: FP32 is 4 bytes; FP16 and BF16 are 2 bytes, and BF16 keeps FP32's exponent range with less precision, which is why training and most serving default to it; FP8 is 1 byte with scaling factors and needs Hopper-class or newer tensor cores; INT8 is 1 byte; INT4 is half a byte plus group scales.
- Weight memory = parameters × bytes per parameter: a 7B model is about 28 GB in FP32, 14 GB in FP16, 7 GB in INT8 and roughly 4 GB in INT4 once scales are counted.
- Weight-only quantization (W4A16, W8A16) stores low-bit weights and dequantizes to FP16 inside the kernel; it cuts bytes per step, so it speeds up memory-bound decode, but it adds dequantization work, so it does little for compute-bound prefill and can slow it down.
- Weight-and-activation quantization (W8A8 INT8 such as SmoothQuant, or FP8) runs the matmuls on integer or FP8 tensor cores, so it also speeds up prefill and large-batch decode; activations have outlier channels that make them harder to quantize than weights.
- GPTQ and AWQ are post-training 4-bit weight methods that need a small calibration set; GGUF is llama.cpp's file format with its k-quant schemes; bitsandbytes gives one-flag loading (LLM.int8, NF4) and powers QLoRA, but its inference kernels are not built for serving throughput.
- KV cache quantization (`--kv-cache-dtype fp8` in vLLM) halves cache memory, so it doubles tokens in flight; it changes attention precision directly, so long-context recall is what you test.
- Quality loss is not uniform: small models, math and code, non-English text and long reasoning chains degrade first; perplexity alone hides task-level regressions.
- Validate with a perplexity delta, standard task evals, and your own golden set scored against the FP16 model; do not quantize when quality margins are thin, when the workload is prefill-heavy and compute-bound, or when kernel support for your hardware is immature.

### Q. Explain the difference between FP16, BF16, FP8 and INT8, and when each one is used.
**Short answer (45 seconds):** FP16 and BF16 both use 2 bytes. FP16 has 5 exponent bits and 10 mantissa bits, so it is more precise but has a narrow range and can overflow on large activations. BF16 has 8 exponent bits like FP32 and 7 mantissa bits, so it never overflows where FP32 would not, which is why it is the default for training and for serving most modern checkpoints. FP8 uses 1 byte with scaling factors and runs on FP8 tensor cores on Hopper-class and newer GPUs; it is the current sweet spot for near-lossless halving of memory and compute. INT8 is a 1-byte integer with a scale; it predates FP8 hardware and appears in weight-only and SmoothQuant style W8A8 schemes.

**Deeper explanation:**

| Format | Bytes | Character | Typical use |
| --- | --- | --- | --- |
| FP16 | 2 | precise, narrow range | older GPUs without BF16 support |
| BF16 | 2 | FP32 range, 7-bit mantissa | training, default serving dtype |
| FP8 (E4M3, E5M2) | 1 | needs scales; E4M3 more precision, E5M2 more range | Hopper-class serving, W8A8, KV cache |
| INT8 | 1 | uniform integer plus scale | weight-only or SmoothQuant W8A8 |

Choose by hardware first (BF16 needs Ampere or newer, FP8 needs Hopper or Ada class), then by the checkpoint's trained dtype: serve in the dtype the model shipped with unless you are deliberately quantizing. In vLLM, `--dtype auto` follows the checkpoint and `--quantization fp8` applies dynamic FP8 at load time on supported GPUs.

**Follow-ups they will ask:**
- Why BF16 over FP16 for serving: range; FP16 activations can overflow in large models and produce NaNs.
- Does FP8 need calibration: static FP8 does (collect activation ranges on sample data); dynamic FP8 computes scales at runtime per tensor at a small cost.

**Mistakes to avoid:**
- Saying BF16 is "more precise" than FP16; it has more range and less precision.

### Q. What is the difference between weight-only and weight-and-activation quantization, and which phases of inference does each one speed up?
**Short answer (45 seconds):** Weight-only quantization (W4A16, W8A16) stores weights as low-bit integers and dequantizes them to FP16 inside the matmul kernel while activations stay in FP16. It cuts memory and bytes per step, so it speeds up memory-bound decode and lets you fit a bigger model or more KV cache, but the dequantization is extra compute, so compute-bound prefill barely benefits and can slow down. Weight-and-activation quantization (W8A8 INT8 or FP8) quantizes the activations too, so the matmul itself runs on integer or FP8 tensor cores, which speeds up prefill and high-batch decode as well. Activations are harder because of outlier channels; SmoothQuant moves that difficulty into the weights with a per-channel scale.

**Deeper explanation:** Reason from the roofline. At small batch, decode time is about weight_bytes / bandwidth, so going from 2 bytes to roughly 0.5 bytes per weight gives a large step-time reduction. As the batch grows the GPU becomes compute-bound; dequantization is now pure overhead, so W4A16 throughput at batch 128 can be worse than FP16. FP8 W8A8 halves the bytes and uses tensor cores whose FP8 rate is roughly double the FP16 rate on the hardware that has them, so it wins in both regimes.

```text
Decode, batch 1, 7B:   FP16 14 GB -> INT4 ~4 GB     step time drops with bytes moved
Prefill, 4k tokens:    compute-bound; W4A16 ≈ FP16 or slower; FP8 W8A8 faster
High batch decode:     W4A16 loses its edge; FP8 W8A8 keeps it
```

Kernels matter as much as formats: vLLM uses Marlin-style kernels so INT4 checkpoints stay fast at moderate batch, and FP8 paths depend on the attention and GEMM kernels supporting the dtype on your GPU generation.

**Follow-ups they will ask:**
- Which for a latency-sensitive chatbot on one GPU at small batch: weight-only INT4 (AWQ or GPTQ), the biggest bandwidth win.
- Which for a high-throughput pipeline on Hopper-class GPUs: FP8 W8A8.

**Mistakes to avoid:**
- Claiming quantization "always makes inference faster"; prefill-heavy workloads may see no gain.
- Confusing memory savings with latency savings; they coincide only in the memory-bound regime.

### Q. Compare GPTQ, AWQ, GGUF and bitsandbytes. What would you choose for a 4-bit production deployment on NVIDIA GPUs?
**Short answer (45 seconds):** GPTQ and AWQ are post-training 4-bit weight-only methods for GPU serving. GPTQ quantizes layer by layer using second-order information from calibration data to minimize output error. AWQ looks at activation magnitudes and scales the small fraction of salient weight channels so they survive rounding. Both have fast kernels in vLLM and TGI. GGUF is llama.cpp's container format with its own k-quant schemes (Q4_K_M, Q5_K_M, Q8_0), built for CPUs and Apple Silicon. bitsandbytes gives one-flag loading in transformers (`load_in_4bit`, NF4) and underpins QLoRA fine-tuning, but its kernels are not built for serving throughput. For production on NVIDIA GPUs I would serve an AWQ or GPTQ checkpoint with vLLM, or FP8 if the GPUs support it.

**Deeper explanation:**

| Method | Type | Needs calibration data | Where it shines |
| --- | --- | --- | --- |
| GPTQ | 4-bit weight-only, Hessian-based rounding | yes | mature GPU kernels, many checkpoints |
| AWQ | 4-bit weight-only, activation-aware scaling | yes | strong quality at 4-bit, fast kernels |
| GGUF k-quants | file format plus mixed-precision schemes | no (round-to-nearest variants) | llama.cpp, Ollama, CPU and Metal |
| bitsandbytes NF4, LLM.int8 | runtime quantization at load | no | fine-tuning memory, quick experiments |

Operational notes: prefer checkpoints quantized by the model vendor when they exist, and otherwise check what calibration data a community checkpoint used, because calibration on English web text can hurt code or non-English quality. vLLM detects the quantization from the checkpoint config, so `vllm serve MODEL_ID-AWQ` is usually enough.

**Follow-ups they will ask:**
- What is group size: the number of weights sharing one scale; 128 is common, smaller is more accurate but adds overhead.
- Why is bitsandbytes slower at inference: it dequantizes on the fly with kernels optimized for fitting models and training, not for batched serving.

**Mistakes to avoid:**
- Treating GGUF as a GPU serving format for vLLM; support there is limited, and the ecosystem for GGUF is llama.cpp.

### Q. How much memory does quantizing a 70B model save, and what else does it buy you?
**Short answer (45 seconds):** Seventy billion parameters is about 140 GB in FP16, about 70 GB in FP8 or INT8, and about 35 GB in INT4 plus a few gigabytes of scales. So FP16 needs at least two 80 GB GPUs for the weights alone and realistically four with KV room, while INT4 fits on one 80 GB GPU with roughly 30 GB left for KV cache. Beyond memory you get fewer bytes per decode step, which is a faster TPOT at low batch, the option to drop tensor parallelism and its communication cost, and more KV cache, which is more concurrency per GPU. Every one of those lowers cost per token.

**Deeper explanation:** Illustrative numbers on 80 GB cards at 0.9 utilization (72 GB usable each):

| Config | Weights | Minimum GPUs per replica | Approximate KV budget |
| --- | --- | --- | --- |
| FP16 | 140 GB | 2, realistically 4 | at TP 4: 4 × 72 - 140 - activations ≈ 140 GB pooled |
| FP8 | 70 GB | 2 | 2 × 72 - 70 - activations ≈ 70 GB pooled |
| INT4 (AWQ) | about 38 GB with scales | 1 | 72 - 38 - 4 ≈ 30 GB |

For a GQA 70B model with 80 layers, 8 KV heads and head_dim 128, FP16 KV is 2 × 80 × 8 × 128 × 2 = 327,680 bytes, 320 KB per token. The INT4 single-GPU replica therefore holds about 96k tokens, roughly 12 conversations of 8k tokens, on one GPU.

**Follow-ups they will ask:**
- One GPU INT4 or two GPUs FP8: FP8 keeps more quality and faster prefill; INT4 is cheaper per replica; decide on your eval and your latency SLO.
- How does this change cost: fewer GPUs per replica and more concurrency per GPU compound; the saving is often a multiple, not a percentage.

**Mistakes to avoid:**
- Treating INT4 as exactly half a byte per weight; scales and zero points add overhead.

### Q. What is KV cache quantization, and what does it trade?
**Short answer (45 seconds):** It stores keys and values in FP8 (or INT8 and INT4 in some engines) instead of FP16, halving or better the bytes per cached token. That means twice as many tokens in flight on the same GPU, so more concurrent users or longer contexts, and fewer bytes read per decode step at long context. The trade is attention precision: keys are especially sensitive, so long-context recall and tasks that depend on exact retrieval from the prompt need evaluation before you turn it on. In vLLM it is `--kv-cache-dtype fp8`.

**Deeper explanation:** Keys have outlier channels, which is why research methods such as KIVI quantize keys per channel and values per token. FP8 E5M2 can be used as a direct cast with no scales, while E4M3 needs scaling factors, which some quantized checkpoints ship with. The attention kernel must support the chosen dtype on your GPU generation, so check the engine's compatibility notes before assuming a speedup.

```bash
vllm serve MODEL_ID --kv-cache-dtype fp8 --max-model-len 32768
  # startup log reports more KV blocks than the FP16 run on the same card
```

The win compounds with prefix caching: a cheaper cache means more shared prefixes stay resident. It also compounds with weight quantization, because the two are independent choices about different tensors.

**Follow-ups they will ask:**
- Does it speed up decode: at long context yes, because KV reads become a large share of the bytes per step.
- How do you test it: needle-in-a-haystack style retrieval over long prompts and your own long-document QA set, compared with FP16 KV.
- When would you skip it: short-context workloads where KV is not the constraint, or recall-critical tasks where a measured drop appears.

**Mistakes to avoid:**
- Calling it free; it changes the numerics of attention itself.
- Confusing it with weight quantization when asked what `--kv-cache-dtype` does.

### Q. How would you validate that a quantized model is good enough to ship?
**Short answer (45 seconds):** Three layers. A cheap sanity check: perplexity on held-out text against the FP16 model, where a small increase is expected and a large one means a broken quantization. Standard task evals for the capabilities you use, compared with the FP16 scores. Then the one that matters: your own golden set of real production prompts, scored with exact metrics where possible (JSON validity, extraction accuracy, tool-call correctness) and with pairwise agreement or an LLM judge against the FP16 outputs elsewhere. Finally measure latency and throughput so the speedup you quantized for actually arrived.

**Deeper explanation:** Agree the thresholds before you measure, then run both models at temperature 0 over the same prompts and look at the disagreements, not the averages. Slice by task type, language, prompt length and output format; quantization damage is concentrated in the tails. Also check for verbosity drift and repetition, which show up before accuracy drops, and confirm the chat template and tokenizer are unchanged so you are comparing models and not prompt formatting.

```python
for p in golden_prompts:
    a = call(FP16_URL, p, temperature=0)
    b = call(QUANT_URL, p, temperature=0)
    record(p.id, exact_match(a, b), schema_ok(b), judge_prefers(p, a, b), slice=p.category)
  # report agreement and schema validity per slice; inspect every disagreement in the worst slice
```

Treat the switch like any model change: shadow traffic first, then a canary with the same dashboards you use for a new model version, with rollback to FP16 ready.

**Follow-ups they will ask:**
- Why not trust perplexity alone: it averages over all tokens, and a model can keep low perplexity while failing on rare, critical tokens such as numbers, JSON punctuation or function names.
- How many prompts: enough per slice to detect a change of a few percentage points; hundreds per slice is a reasonable floor.
- What if the judge is the same family as the model: use a different model as judge, or prefer exact metrics.

**Mistakes to avoid:**
- "Perplexity looks fine, ship it."
- Testing only short English prompts when production has code, long documents or other languages.

### Q. When would you refuse to quantize?
**Short answer (45 seconds):** When the quality margin is thin: small models lose more, and high-stakes extraction, legal or medical content, and math cannot absorb it. When the workload is prefill-heavy and compute-bound, because weight-only INT4 saves memory but not time there. When kernel support for your hardware and format is immature, so you gain memory and lose speed or stability. When the calibration data does not match your domain and you cannot recalibrate. When memory is not your constraint at all, so the engineering effort has no return. And when you consume a hosted API, where it is not your decision.

**Deeper explanation:** Quantize after you have measured which regime you are in. High KV usage and preemptions mean you are memory-bound and quantization pays. Prefill dominating latency with modest KV usage means compute-bound, and the levers are prompt size, FP8 on capable hardware, and prefix caching, not INT4 weights. Illustrative case: a RAG service sending 12k-token prompts and getting 200-token answers spends most of its time in prefill; INT4 weights would not change its latency, while retrieving half as much text would.

Prefer the gentlest option that solves the problem: FP8 on Hopper-class GPUs is close to lossless and is the sensible first step; INT4 is the aggressive step for fitting a model class onto fewer or cheaper GPUs. Vendor-released quantized checkpoints or models trained with quantization awareness carry less risk than community quantizations.

**Follow-ups they will ask:**
- What about quantizing to reach a cheaper GPU class: a valid cost decision when it changes the hardware you need, as long as the golden set passes.
- Would you quantize an embedding model: rarely needed; they are small and the latency is dominated by other things.
- How do you explain a quality drop to a product owner: as a measured trade with numbers from the golden set, alongside the cost saving, so they can choose.

**Mistakes to avoid:**
- Quantizing by default because "everyone does".
- Refusing because "quantization is lossy" without measuring either the loss or the gain.

### Practice
- Serve one 7B or 8B instruct model with vLLM in FP16 and as an AWQ checkpoint; measure TPOT at concurrency 1 and 32 and TTFT with a 4k-token prompt, then explain the pattern using the roofline.
- Build a 200-prompt golden set from real product prompts and compute agreement rate and JSON validity between FP16 and quantized outputs, sliced by task type.
- Enable `--kv-cache-dtype fp8`, record the change in KV block count at startup, and run a long-context retrieval test before and after.
- Say it out loud: in 45 seconds, explain why weight-only INT4 speeds up decode but not prefill.

## Speed-ups Beyond Batching

> Once batching is in place, interviewers probe whether you know the next layer of levers and, more importantly, the regime in which each one helps. Weak answers list techniques. Strong answers say "speculative decoding helps at low batch because decode has spare compute and hurts at high batch", can estimate the gain with a formula, and know which lever addresses TTFT and which addresses TPOT.

### Concepts you must understand
- Speculative decoding: a cheap draft proposes k tokens, the target model verifies all of them in one forward pass that costs about the same as one decode step, and accepted tokens come out at once; rejection sampling keeps the output distribution identical to the target's.
- Expected accepted tokens per target step with acceptance rate α and draft length k is (1 - α^(k+1)) / (1 - α); the gain is real at low batch and vanishes or reverses once the GPU is compute-bound.
- Medusa adds extra decoding heads to the target that predict several future tokens, verified with tree attention; EAGLE drafts from the target's hidden features, which gives higher acceptance; n-gram or prompt-lookup drafting needs no extra model at all.
- Prefix caching reuses KV blocks for identical token prefixes across requests, removing the prefill compute for the shared part; it only works for byte-identical prefixes from position 0 and on the same replica, which dictates how you lay out prompts.
- Chunked prefill splits long prompts into pieces scheduled alongside decode tokens so one huge prompt does not stall everyone else's next token; disaggregated prefill and decode takes this further with separate GPU pools.
- FlashAttention is an exact, IO-aware attention kernel that tiles the computation so the N by N score matrix never touches HBM; it makes long prompts affordable and matters mostly for prefill.
- Tensor parallelism splits each layer's matrices across GPUs with an all-reduce per layer (low latency, needs NVLink); pipeline parallelism splits layers into stages (little communication, idle bubbles, more latency per token).
- Mixture of Experts models activate a few experts per token, so compute per token is low, but all experts must sit in memory, expert load is uneven, and at small batch they are bandwidth-bound on whichever experts get touched.
- Constrained decoding masks invalid tokens at every step from a compiled grammar; compiling the grammar is the expensive part, so compiled grammars are cached by schema hash and the per-step mask is cheap in modern engines.

### Q. Explain speculative decoding. When does it help and when does it hurt?
**Short answer (45 seconds):** Decode is memory-bound, so each step reads the full weights to produce one token while most of the compute sits idle. Speculative decoding uses a cheap draft to guess the next k tokens, then runs the big model once over all k guesses in parallel, which costs about as much as a single decode step, and keeps the longest run of guesses that the big model agrees with. A rejection-sampling rule makes the output distribution exactly the target model's. It helps when acceptance is high and the GPU has spare compute, which means small batch and predictable text; at high batch the verification competes with other requests for compute and the extra draft work can lower throughput.

**Deeper explanation:**

```text
Expected accepted tokens per target step (acceptance α per token, draft length k):
  E[tokens] = (1 - α^(k+1)) / (1 - α)
Illustrative: α = 0.8, k = 4  ->  (1 - 0.8^5) / 0.2 = (1 - 0.328) / 0.2 ≈ 3.4 tokens
Cost per step ≈ 1 target forward + 4 draft forwards at ~10% each ≈ 1.4 target units
Speedup ≈ 3.4 / 1.4 ≈ 2.4x at batch 1          (illustrative arithmetic, not a benchmark)
```

Acceptance depends on how predictable the text is: code, boilerplate JSON and paraphrased input have high acceptance; open-ended prose has low acceptance. In vLLM you configure it with `--speculative-config` (older versions used `--speculative-model` and `--num-speculative-tokens`), and the engine reports acceptance metrics so you can see whether the draft earns its keep on your traffic.

**Follow-ups they will ask:**
- Does it change outputs: no; with greedy decoding the tokens are identical, and with sampling the distribution is the target's.
- Why does it hurt at high batch: the GPU is compute-bound there, and verifying k tokens per sequence multiplies the compute per step.

**Mistakes to avoid:**
- Saying it approximates the target model; the whole point is that it does not.
- Quoting an acceptance rate or speedup without stating the batch size and workload.

### Q. How do Medusa and EAGLE differ from using a separate draft model?
**Short answer (45 seconds):** A separate draft model is a whole second model that must share the tokenizer, often predicts differently from the target, and takes memory. Medusa adds a few lightweight heads on top of the target's final hidden state, each predicting a token one position further ahead, and verifies combinations of candidates in one pass with tree attention; there is no second model, but the heads only see the last hidden state, so acceptance is limited. EAGLE trains a small autoregressive draft head that runs on the target's second-to-top-layer features plus token embeddings, which captures far more about what the target will say, so acceptance and speedups are higher. Both need trained heads per target model.

**Deeper explanation:**

| Approach | Extra memory | Training needed | Typical acceptance | Notes |
| --- | --- | --- | --- | --- |
| Separate draft model | a full small model | none if a same-family small model exists | medium | tokenizer must match |
| n-gram or prompt lookup | none | none | high on extractive tasks, low on open text | free to try first |
| Medusa heads | small | heads only | medium | tree-attention verification |
| EAGLE head | small | head only | high | feature-level autoregressive drafting |

Tree attention lets the target verify several candidate continuations in a single forward pass by building an attention mask over a tree of tokens instead of a single chain. Later EAGLE versions grow the draft tree dynamically based on confidence.

**Follow-ups they will ask:**
- Why does EAGLE beat Medusa: hidden features carry the target's uncertainty, and autoregressive drafting lets later draft tokens condition on earlier ones.
- What is the operational cost: a trained head per model version, so a model upgrade means retraining or downloading a new head.

**Mistakes to avoid:**
- Assuming trained heads exist for whatever model you picked.
- Describing Medusa as a different model; it is the same model with extra output heads.

### Q. What is prefix caching inside the engine, and how should it change the way I structure prompts?
**Short answer (45 seconds):** The engine keeps the KV blocks of earlier requests and reuses them when a new request begins with exactly the same tokens, so prefill only runs for the new tail. It is automatic in vLLM (a hash per block, chained) and SGLang (a radix tree), but it works only when the prefix is byte-identical from the first token and the request lands on the same replica. So stable content goes first: tool definitions, system prompt, few-shot examples, shared documents; then the conversation; then the content that changes per request. Anything dynamic early, such as a timestamp, a user name or non-deterministic JSON key order, breaks the match for everything after it.

**Deeper explanation:**

```text
GOOD: [tools][system prompt][few-shot][shared doc]...[turn 1][turn 2]...[new user message]
BAD:  [system prompt starting "Today is 2026-10-30 14:03"][...]        changes every minute
BAD:  [per-user preamble][6k tokens of shared instructions][...]      shared part never matches
```

vLLM caches whole blocks (16 tokens by default), so a shared prefix that ends mid-block loses its last partial block; this rarely matters but explains small discrepancies. Multi-turn chat is the ideal case because each turn appends to an unchanged history, so keep history append-only and avoid rewriting or summarizing earlier turns unless you must. Capacity is the free KV blocks, evicted LRU, so a busy replica keeps only hot prefixes. With several replicas, route by session or by a hash of the first few hundred tokens so related requests hit the same cache. Watch the prefix cache hit metrics in `/metrics` to confirm the layout is working.

**Follow-ups they will ask:**
- Does it help RAG: yes if the same chunks appear in the same order; sort retrieved chunks deterministically when ranking order is not essential.
- Is this the same as provider prompt caching: same mechanism, but providers add explicit breakpoints, minimum lengths and billing rules.

**Mistakes to avoid:**
- Putting a greeting with the user's name at the top of the system prompt.
- Expecting hits across replicas without affinity routing.

### Q. What problem does chunked prefill solve?
**Short answer (45 seconds):** Without it, a request with a 20k-token prompt takes over a whole scheduler step for its prefill and every other sequence in the batch waits for that step to finish, so their next tokens arrive late and TPOT spikes. Chunked prefill splits the long prompt into chunks bounded by a per-step token budget and processes one chunk per step together with the decode tokens of running requests. Decode stays smooth, the long prompt still finishes within a few steps, and the GPU mixes compute-heavy prefill with memory-heavy decode, which uses it better. The cost is a slightly higher TTFT for the long request.

**Deeper explanation:**

```text
no chunking:  step 1 [PREFILL 20k tokens ..................]  step 2 [d d d d]  step 3 [d d d d]
                      ^ every running user's token waits here
chunking:     step 1 [P 2k][d d d d]  step 2 [P 2k][d d d d]  ...  TPOT stays steady
```

In vLLM the behavior is on by default in recent versions, with `--max-num-batched-tokens` setting the budget: a lower budget smooths TPOT and slows long-prompt TTFT, a higher one does the opposite. Prefix caching composes with it, since cached blocks are skipped and chunks cover only uncached tokens. The next step in this direction is disaggregated serving, where prefill and decode run on separate GPU pools and the KV cache is transferred between them; it lets you size and scale the two phases independently and tune TTFT and TPOT separately, at the cost of moving KV data across the network.

**Follow-ups they will ask:**
- How do you pick the budget: load test with a realistic mix of long and short prompts and raise it until p95 TPOT of the short ones breaks the SLO.
- Does it make prefill faster: no, it smooths latency and improves utilization; raw prefill speed comes from kernels and hardware.

**Mistakes to avoid:**
- Claiming chunked prefill speeds up long prompts; it protects everyone else from them.
- Setting a tiny token budget and then wondering why long-prompt TTFT is terrible.

### Q. What does FlashAttention actually do, and does it help decode?
**Short answer (45 seconds):** Standard attention computes the N by N score matrix for a sequence, writes it to GPU memory, applies softmax, reads it back and multiplies by V; for long N that memory traffic dominates. FlashAttention computes exact attention in tiles that fit in on-chip SRAM, uses an online softmax so it never materializes the full matrix, and writes only the output. Memory becomes linear in N instead of quadratic and the kernel is substantially faster on long sequences. It matters mostly for prefill, where there are many queries at once. In decode there is one query per sequence per step and the bottleneck is reading the KV cache, which engines address with paged and split-KV decode kernels.

**Deeper explanation:**

```text
naive: S = Q K^T  (N×N written to HBM) -> P = softmax(S) (read, write) -> O = P V      memory O(N^2)
flash: for each tile of K and V: update running max and sum, accumulate partial O      memory O(N)
```

FlashAttention-2 improved parallelism along the sequence and the work split between warps; FlashAttention-3 targets Hopper-class GPUs with asynchronous execution and FP8 support. Engines choose kernels per phase: FlashAttention or FlashInfer style kernels for prefill, and decode kernels that split the KV cache across streaming multiprocessors so a single long sequence can still use the whole GPU. When asked where time goes, say that attention is a meaningful share of prefill for long prompts, while decode bytes are dominated by the MLP weights for short contexts and by KV reads for long ones.

**Follow-ups they will ask:**
- Exact or approximate: exact; results match standard attention up to floating-point rounding.
- Relation to long context: it removes the quadratic memory wall for prompts; KV cache size remains the other constraint.
- Relation to PagedAttention: different problems; one is a compute kernel, the other is memory management.

**Mistakes to avoid:**
- Confusing FlashAttention with sparse or approximate attention.
- Saying it makes decode faster in general; decode is bandwidth-bound on weights and KV, not on the score matrix.

### Q. Tensor parallelism versus pipeline parallelism: what is each one doing, and where does the time go?
**Short answer (45 seconds):** Tensor parallelism splits individual weight matrices across GPUs: each GPU computes a slice of every layer, and the slices are combined with an all-reduce, twice per transformer block in the Megatron scheme. Every GPU works on every token, so per-token latency drops and memory is pooled, but the per-layer communication needs NVLink-class bandwidth, which keeps TP inside one node in practice. Pipeline parallelism assigns whole layers to stages; activations move from stage to stage, so communication is small and crosses nodes well, but each token passes through the stages sequentially and stages idle unless several requests are in flight. TP for latency inside a node, PP to cross nodes, replicas for throughput.

**Deeper explanation:** The communication volume of TP is the hidden-state size per token, twice per layer, every step: for a model with hidden size 8,192 in BF16 and 80 layers that is roughly 8,192 × 2 bytes × 2 × 80, about 2.6 MB per token per step, multiplied by the batch (illustrative). That is why TP rarely goes beyond eight GPUs and why PCIe-only machines see small TP gains. PP's weakness is the bubble: with S stages and M concurrent micro-batches the idle fraction is roughly (S - 1) / (M + S - 1); continuous batching keeps stages busy with different requests, which is why PP is tolerable for inference across nodes.

```bash
vllm serve MODEL_ID --tensor-parallel-size 8                         # one node, NVLink
vllm serve MODEL_ID --tensor-parallel-size 8 --pipeline-parallel-size 2   # two nodes
```

Two further axes exist: expert parallelism for MoE models, and context or sequence parallelism for extremely long prompts.

**Follow-ups they will ask:**
- Why must TP divide the head count: attention heads are assigned whole to GPUs.
- When is PP the right answer for inference: models that do not fit on one node, or hardware without fast interconnect.

**Mistakes to avoid:**
- Treating TP across nodes over Ethernet as reasonable.
- Confusing data parallelism (replicas) with either form of model parallelism.

### Q. What is special about serving a Mixture of Experts model?
**Short answer (45 seconds):** In an MoE model each token is routed to a few experts out of many, so compute per token is that of a much smaller dense model, but every expert's weights must be resident, so the memory footprint is the full model. Mixtral 8x7B is the classic example: roughly 47B total parameters, roughly 13B active per token. You pay dense-model memory for sparse-model compute. At small batch you are bandwidth-bound on the experts that get touched; as batch grows nearly every expert is touched every step, so the per-step bytes approach the whole model and the compute saving is what remains. Expert load is uneven, so GPUs holding popular experts become hot spots, and the natural multi-GPU layout, expert parallelism, needs all-to-all communication in every MoE layer.

**Deeper explanation:** The KV cache is the same as for a dense model with the same attention configuration, because attention layers are not expert-split, so concurrency math is unchanged. Weight quantization matters more than usual because experts are most of the parameters. Deployment typically combines TP for attention with expert parallelism for the MoE layers (vLLM has `--enable-expert-parallel`), or simply TP across everything on one node. Routing imbalance shows up as some GPUs finishing their expert work late while others wait, so per-GPU utilization can look fine on average and still hide stragglers.

```text
dense 13B:  memory ~26 GB BF16,  compute per token ~ 13B params
MoE 8x7B:   memory ~94 GB BF16,  compute per token ~ 13B params, all 8 experts resident
```

**Follow-ups they will ask:**
- Why are MoE models attractive for large providers but awkward for small teams: they need a lot of memory per replica, which large fleets amortize over huge batches.
- Does speculative decoding work with MoE: yes, and verification touches more experts per step, so the balance shifts.
- Does prefix caching change: no, the cache is attention state.

**Mistakes to avoid:**
- Saying a 13B-active MoE "needs 13B worth of memory".
- Ignoring all-to-all communication when proposing expert parallelism across slow links.

### Q. Does structured output (a JSON schema) cost extra at inference time?
**Short answer (45 seconds):** Constrained decoding compiles your JSON schema or grammar into an automaton and, at every decode step, masks the logits so only tokens that keep the output valid can be sampled. The per-step mask over a vocabulary of a hundred thousand tokens used to be expensive, but modern libraries precompute token transitions for the automaton so the per-step cost is small. What remains expensive is compiling the grammar the first time you see a schema, which can take noticeable time for complex schemas, so engines and gateways cache compiled grammars by schema hash. There is also a quality cost when the schema forces an order the model would not choose, so design schemas with reasoning fields before answer fields.

**Deeper explanation:** Libraries you can name: Outlines (finite-state index), XGrammar (used by vLLM and SGLang, context-free grammars with precomputed context-independent token sets) and llguidance. SGLang's jump-forward decoding inserts deterministic spans such as `{"name": "` without running the model, which reduces output tokens and makes constrained output cheaper than free-form JSON. Hosted providers do the same work server-side: a strict schema mode compiles once and then serves fast, and documentation typically warns about added latency on the first request with a new schema. Compared with the alternative, which is retrying when the model emits invalid JSON, constrained decoding is almost always cheaper.

```text
cost model:  compile(schema)  once per schema, cached by hash
             mask per step     small, vectorized
             output tokens     often fewer (jump-forward), never more valid-JSON retries
```

**Follow-ups they will ask:**
- Does it guarantee correctness: only syntax; a schema-valid answer can still be wrong, so validate semantics separately.
- JSON mode versus schema mode: JSON mode only promises parseable JSON, schema mode enforces your exact shape.
- Tool calling: strict tool-call arguments are produced with the same machinery.

**Mistakes to avoid:**
- Calling structured output "free" or "very expensive"; the cost is in compilation and caching, not per token.
- Writing deep, nested schemas with many optional fields and then blaming the engine for slow first calls.

### Practice
- Enable n-gram speculative decoding in vLLM for an extractive task and a creative-writing task; record acceptance rate and tokens/s at concurrency 1 and 16 and explain the difference.
- Build a 5k-token system prompt, send 20 requests differing only in the final line, and watch TTFT and prefix cache hits; then add a timestamp line at the top and watch the hits disappear.
- Mix 32k-token and 200-token prompts with chunked prefill on and off and plot p95 TPOT of the short requests.
- Say it out loud: derive the speculative decoding expected-tokens formula and compute it for α = 0.7 and k = 3 (about 2.5 tokens per step).

## Scaling, Routing & Load Balancing

> This is where the "full stack" half of the title earns its keep: the interviewer wants to know whether you can put GPUs behind a service that behaves under load. A weak answer says "put it behind a load balancer and autoscale on CPU". A strong answer explains why LLM requests are not interchangeable, routes on engine metrics and cache affinity, autoscales on queue depth, and has a plan for cold starts, noisy tenants and priorities.

### Concepts you must understand
- Replicas behind a load balancer are the default scaling unit, but LLM requests differ in cost by a hundredfold, so round-robin is a poor fit; least-outstanding-requests or queue-depth-aware routing uses the engine's own metrics.
- Cache-affinity routing sends requests that share a prefix (same conversation, tenant or system prompt) to the same replica so the prefix cache hits; consistent hashing on a session or tenant key does this at the cost of some imbalance.
- Long prefill-heavy requests and short interactive ones have different latency profiles; separate pools, or disaggregated prefill and decode, protect interactive TPOT from document-sized prompts.
- Model routing sends easy requests to small models and hard ones to large models through heuristics, a classifier or a cascade (try cheap, verify, escalate); without continuous quality measurement it degrades silently.
- Autoscale on leading indicators such as waiting requests (`vllm:num_requests_waiting`), KV cache utilization and TTFT p95; GPU utilization is lagging and misleading because a memory-bound GPU can report near 100% while serving few tokens.
- Cold starts are minutes long (node provisioning, image pull, weight load, graph capture), so scale out early, keep headroom, pre-stage weights and scale in slowly.
- Multi-LoRA serving keeps one base model in memory and batches requests for many adapters together, so dozens of tenant-specific fine-tunes share one GPU; in vLLM, `--enable-lora` and the adapter name in the request's `model` field.
- Admission control decides what enters the queue: per-tenant token buckets on requests and tokens, token estimates before admitting, and a bounded queue with fast 429 or 503 rejection instead of unbounded waiting.
- Priority classes let interactive traffic go first and batch traffic absorb the slack, both at the gateway and inside the engine's scheduler, and they define what gets shed first under overload.

### Q. How do you load balance across several vLLM replicas, and why is round-robin a poor fit?
**Short answer (45 seconds):** Round-robin assumes requests cost about the same. A 200-token chat turn and a 30k-token document summary differ by two orders of magnitude in prefill work and KV footprint, and a streaming response holds its slot for seconds to minutes, so round-robin piles long requests onto one replica by chance while another sits idle. Route on live state instead: least outstanding requests at minimum, and better, the engine's own metrics, the waiting queue length and KV cache utilization that vLLM publishes at `/metrics`. The Kubernetes Gateway API Inference Extension formalizes this with an endpoint picker that reads those metrics and knows which LoRA adapters each replica has loaded.

**Deeper explanation:**

```text
clients -> API gateway (auth, tenant limits) -> inference router -> vLLM pods
                                                  | reads: num_requests_waiting, kv cache usage, loaded adapters
                                                  | policy: least queue -> cache affinity -> adapter locality
```

Streaming changes the plumbing: the proxy must pass server-sent events through without buffering (`proxy_buffering off` in nginx), idle timeouts must exceed the longest generation, and a layer-4 balancer with short idle timeouts will cut streams mid-answer. Readiness must flip only after the model is loaded, and scale-in must drain: stop admitting, let in-flight streams finish, and give the pod a termination grace period long enough for the longest response. For a slow or sick replica, eject it on TTFT p95 outliers rather than only on failed health checks.

**Follow-ups they will ask:**
- Why not a message queue in front: a queue decouples producers from GPUs and suits batch work, but it adds latency and does not fit streaming; a short in-memory queue with a bounded wait is the usual compromise for interactive traffic.
- How do you handle a replica that is loading a new adapter: mark it busy for that adapter and route elsewhere until the picker sees it loaded.

**Mistakes to avoid:**
- Balancing and autoscaling on CPU metrics for GPU pods.
- Forgetting that a request is not done when the headers return; the stream holds capacity until the last token.

### Q. What is cache-affinity routing, and when does it beat spreading load evenly?
**Short answer (45 seconds):** Prefix caches live inside each replica, so a request benefits only if it reaches the replica that already holds its prefix. Cache-affinity routing picks the replica from a key that predicts shared prefixes: the conversation ID for multi-turn chat, the tenant ID when tenants have long system prompts, or a hash of the first few hundred tokens. Consistent hashing keeps the mapping stable as replicas come and go. It beats even spreading when prompts have long shared prefixes relative to their unique tails, because the saved prefill (TTFT and GPU time) outweighs a slightly uneven load. With short or unique prefixes it only adds imbalance.

**Deeper explanation:** Use a hybrid: pick the replica by hash, but if its queue is much deeper than the fleet's, fall back to the least-loaded replica (bounded-load consistent hashing). Agent loops are the strongest case, because each tool step resends the growing conversation, so a 20-step run hits the same prefix 20 times. A hot tenant that pins one replica is spread by hashing on tenant plus session rather than tenant alone.

```js
// Node gateway sketch: affinity with a load bound
const key = req.body.metadata?.conversation_id ?? req.tenantId;
let target = ring.lookup(hash(key));                    // consistent hashing ring
if (queueDepth(target) > medianQueueDepth() + 4) {
  target = leastLoadedReplica();                        // give up affinity under skew
}
```

Measure prefix cache hit rate per replica and TTFT split by whether the affinity choice was honored; if affinity is not raising hit rate, the prefixes are not as shared as you assumed.

**Follow-ups they will ask:**
- What happens on scale-out: the new replica starts cold and consistent hashing moves only a fraction of keys to it.
- Why not client-IP stickiness: many users share IPs and one user's requests share no prefix with another's.

**Mistakes to avoid:**
- Hashing the whole prompt, which is unique per request and gives no affinity.
- Pinning tenants so hard that one busy tenant saturates a replica while others idle.

### Q. Explain model cascades and routing by difficulty. How do you stop them from silently degrading quality?
**Short answer (45 seconds):** Routing by difficulty uses a cheap decision, heuristics on length and task type, a small classifier, or request metadata, to send easy requests to a small model and hard ones to a large model. A cascade tries the cheap model first, checks the answer with a validator (schema checks, grounding checks, a verifier model, or agreement between two samples) and escalates only on failure. Both cut cost and both rot, because the check is imperfect and traffic drifts. Protection is a golden eval set run on every router change, a fixed sample of production traffic sent to the large model in shadow for comparison, per-route quality dashboards, and a switch to pin a tenant or feature to the large model.

**Deeper explanation:**

```text
Cascade cost per request ≈ c_small + (1 - p_pass) × c_large + c_check
Illustrative: c_small = 0.1, c_large = 1.0, p_pass = 0.7, c_check ≈ 0
  ≈ 0.1 + 0.3 × 1.0 = 0.40 of always-large; escalated requests pay two sequential latencies
```

A classifier router avoids the double latency but misroutes some requests; train it on labels from your eval set ("which model got this right") with embeddings and a simple classifier to start. Keep the prompt contract identical across models (same tools, same output schema) so routing is configuration. Before building a cascade, measure the simplest alternative: the capable model at a lower effort or reasoning setting often beats a two-model cascade on cost per correct answer, and a cascade also forfeits prompt cache reuse because caches are per model.

**Follow-ups they will ask:**
- How do you validate a cheap answer without another LLM call: schema validity, required fields, numeric ranges, and grounding checks such as the answer quoting a retrieved passage.
- How do you detect drift: re-score a weekly traffic sample against the large model and alert when agreement drops.

**Mistakes to avoid:**
- Trusting the small model's self-reported confidence as the validator.
- Shipping a router with no feedback loop and declaring the cost saving permanent.

### Q. What metric would you autoscale on, and why not GPU utilization?
**Short answer (45 seconds):** Autoscale on signals that lead the latency you care about: requests waiting in the engine queue, KV cache utilization and TTFT p95 at the gateway. Scale out when waiting requests stay above a small threshold or KV usage sits high for a minute; scale in slowly when both stay low. GPU utilization reports whether a kernel is running, not whether the GPU is well used: a memory-bound decode replica can show near 100% while producing a fraction of its possible tokens, and a replica blocked on KV memory shows high utilization while requests queue. It is also lagging. Queue depth says demand already exceeds capacity; KV usage says it is about to.

**Deeper explanation:**

```yaml
  # KEDA ScaledObject trigger sketch (metrics scraped from vLLM /metrics)
triggers:
- type: prometheus
  metadata:
    serverAddress: http://prometheus:9090
    query: sum(vllm:num_requests_waiting{app="llm"}) / count(up{app="llm"})
    threshold: "4"
```

Use separate policies: fast scale-out with a short stabilization window, slow scale-in over 10 to 15 minutes because cold starts are minutes and traffic is bursty. Keep at least two replicas for availability and target around 60 to 70% of the knee throughput so bursts have somewhere to go while new replicas load. Set the threshold from your load test: the per-replica waiting count at which p95 TTFT crosses the SLO, with margin. Kubernetes has no native GPU metric for the HPA anyway, so you are on custom metrics regardless; pick the ones that mean something.

**Follow-ups they will ask:**
- Why per replica rather than total: the sum grows with the fleet; per-replica queue depth measures saturation.
- How do you avoid flapping: stabilization windows, minimum replicas and asymmetric scale-up and scale-down rules.
- Is GPU utilization useless: no, it is a good health and efficiency metric; it is just not an autoscaling trigger.

**Mistakes to avoid:**
- CPU-based autoscaling for GPU pods.
- Scaling in aggressively and paying a cold start every hour.

### Q. New replicas take minutes to become ready. How do you plan capacity and scaling so users never notice?
**Short answer (45 seconds):** Treat the cold start as a constant and design around it. Keep headroom, N+1 or around 20 to 30% above expected peak, so bursts are absorbed while new replicas come up. Scale out on leading indicators with a short stabilization window and scale in slowly. Keep a warm pool of GPU nodes with the image pulled and the weights on local disk so pod start is load time only. Pre-scale on a schedule before known peaks, and fill troughs with batch work instead of scaling for peaks. For spiky, low-volume traffic where you cannot keep a GPU warm, do not self-host; call a provider.

**Deeper explanation:** Illustrative sizing: if one replica's knee throughput is 1,500 tokens/s and expected peak is 10,000 tokens/s, you need seven replicas at full load and ten at a 70% target. If a cold start takes five minutes and traffic can double in five minutes during a launch, you pre-scale before the launch rather than reacting. Weight staging uses node-local NVMe populated by a DaemonSet or a read-only shared volume, so a pod loads from disk in tens of seconds instead of downloading for minutes. Scale-to-zero is acceptable only for internal tools where a visible "warming up" state is fine.

```text
timeline of a scale-out:  decision -> node ready -> image pulled -> weights loaded -> graphs captured -> ready
cost of each stage:       seconds    minutes       minutes         minutes          ~1 min         warmup
mitigation:               leading    warm pool     pre-pull        local NVMe       accept         pre-warm requests
```

Run a drill: kill a replica at peak and measure the SLO impact; that number tells you whether your headroom is real.

**Follow-ups they will ask:**
- Serverless GPU platforms: they hide some of this with snapshotting but still have cold starts; good for development and spiky low-volume use.
- Predictive versus reactive scaling: use both; forecast by time of day and still react to queue depth.

**Mistakes to avoid:**
- Scale-to-zero for interactive traffic.
- Measuring autoscaler success by replica count rather than by TTFT during bursts.

### Q. How does multi-LoRA serving work, and when would you use it?
**Short answer (45 seconds):** A LoRA fine-tune is a pair of small low-rank matrices added to selected weight matrices; the base model is untouched. Multi-LoRA serving loads the base model once and keeps many adapters alongside it, and the engine batches requests that use different adapters into the same forward pass with specialized kernels, so dozens of tenant-specific fine-tunes share one GPU instead of needing a deployment each. In vLLM you start with `--enable-lora`, register adapters with `--lora-modules name=path`, and the client sets `model` to the adapter name. Adapters not resident on the GPU are swapped in from CPU memory, so hot adapters stay fast and cold ones pay a small load penalty.

**Deeper explanation:**

```bash
vllm serve BASE_MODEL_ID --enable-lora --max-loras 8 --max-lora-rank 64 \
  --lora-modules tenant-a=/adapters/tenant-a tenant-b=/adapters/tenant-b
  # client request: {"model": "tenant-a", "messages": [...]}
```

The kernel idea (Punica and S-LoRA) is to gather each request's adapter weights and run the batched low-rank matmuls alongside the shared base matmul, so the overhead over the base model is small. `--max-loras` caps the adapters resident at once and `--max-lora-rank` caps adapter size. Routing should prefer replicas that already hold the adapter. Use cases: per-tenant tone and format, per-domain extraction, and replacing long few-shot prompts, which also shortens prompts and cuts cost. Governance matters: an adapter registry with versions, an eval per adapter, and one base model version across the fleet, because an adapter trained on one base version is not valid on another. KV computed under one adapter cannot be reused for another, so prefix caching is per adapter.

**Follow-ups they will ask:**
- Why not merge the adapter into the weights: merging gives a separate full model per tenant and kills sharing; merge only when one adapter serves all traffic.
- Does it work with a quantized base: yes, adapters over a quantized base is a common pattern.

**Mistakes to avoid:**
- One full deployment per tenant fine-tune.
- Upgrading the base model without re-validating or retraining every adapter.

### Q. Design admission control for an inference gateway serving tenants with different priorities.
**Short answer (45 seconds):** Admission control runs before the engine sees a request. Each tenant has token buckets for requests per minute and tokens per minute; the gateway estimates a request's cost before admitting it, exact prompt tokens from the tokenizer plus max_tokens as the output bound, and rejects fast with 429 and a Retry-After header when the bucket is empty. A concurrency limit per replica near its sequence cap and a bounded queue with a maximum wait per class turn overload into quick failures instead of timeouts. Priority classes (interactive, standard, batch) decide queue order and shedding order: batch is throttled to whatever capacity interactive leaves idle, and the engine's priority scheduling is a second layer.

**Deeper explanation:**

```text
request -> authn -> tenant buckets (RPM, TPM on estimated tokens) -> 429 + Retry-After if empty
        -> class queue [interactive | standard | batch], max wait per class, 503 when exceeded
        -> per-replica concurrency semaphore -> engine (priority field on the request)
shedding under overload: batch first, then standard; interactive last
```

Inside a class, weighted fair queuing between tenants stops one tenant from monopolizing capacity, and a per-tenant cap on concurrent streams handles noisy neighbors. Distributed buckets live in Redis with an atomic script; reconcile after completion by refunding the unused output allowance so estimates do not starve tenants. Add backpressure from the engine: when its waiting queue passes a threshold, reduce the admit rate rather than letting the queue grow. Return remaining-budget headers so clients can pace themselves, the same way providers do.

**Follow-ups they will ask:**
- Why reject fast instead of queueing longer: a long queue hides overload and turns into timeouts; a fast 429 lets clients back off or fall back.
- How do you size tenant limits: from contracts and from measured capacity at the knee, leaving headroom.

**Mistakes to avoid:**
- Applying limits after prefill has started, which wastes the most expensive work.
- Unbounded queues anywhere in the path.

### Practice
- Run two vLLM replicas behind nginx or Envoy, compare round-robin with least-connections under a mix of 200-token and 20k-token requests, and record p95 TTFT per request class.
- Implement bounded-load consistent hashing in a small Node gateway keyed on conversation ID, then measure prefix cache hit rate per replica with and without affinity.
- Scrape vLLM metrics into Prometheus, create a KEDA or HPA rule on waiting requests, trigger a burst, and record time-to-ready and the SLO impact.
- Say it out loud: explain in 60 seconds why GPU utilization is the wrong autoscaling signal and what you use instead.

## Caching at the Inference Layer

> Caching is the cheapest cost lever and the most commonly botched one. Interviewers want you to separate the layers (engine KV reuse, provider prompt caching, exact-match and semantic response caches), to know what each one saves, and to know the failure modes: unstable prefixes, false positives in semantic caches, stale answers after a prompt change. A weak answer is "we cache responses in Redis". A strong answer names the layer, the key, the invalidation rule and the metric that proves it works.

### Concepts you must understand
- Four layers: engine prefix caching (reuses KV for identical token prefixes and saves prefill compute), provider prompt caching (the same idea inside a hosted API, billed at a discount), exact-match response caching (skips the model for repeated requests) and semantic caching (skips the model for similar requests, with a correctness risk).
- Prefix caches require byte-identical prefixes from position 0, rendered in a fixed order (for Anthropic: tools, then system, then messages), so stable content goes first and anything volatile goes after the last cache point.
- Anthropic prompt caching is explicit: `cache_control` breakpoints (up to four per request), a 5-minute TTL refreshed on every hit with an optional 1-hour TTL, writes billed above the normal input price and reads well below it; `usage` reports `cache_creation_input_tokens` and `cache_read_input_tokens`.
- OpenAI prompt caching is automatic for prompts above a minimum length, matches in 128-token increments and reports `cached_tokens` under `usage.prompt_tokens_details`; the same structure rule applies.
- Multi-turn conversations and agent loops are the ideal prefix case: an append-only history makes every turn a growing shared prefix, while rewriting history (summarizing, re-ordering, inserting and removing reminders) breaks the cache from that point.
- Exact-match response caching keys on a hash of model, prompt version, messages, tools, schema and sampling parameters, scoped by tenant; it is worth it only for repeated, non-personal requests.
- Semantic caching embeds the query and returns a stored answer above a similarity threshold; its false positives (same wording, different intent, entity or time) are silent wrong answers, so scope it narrowly and measure the false-hit rate.
- Invalidation is key design: model ID and prompt version in the key, namespaces bumped on deploy, TTLs, and document-set versions for RAG-backed caches; prefix caches invalidate themselves because any changed byte is a different prefix.

### Q. What layers of caching exist between a user's request and the GPU, and what does each one save?
**Short answer (45 seconds):** Four. Engine prefix caching reuses KV blocks for an identical token prefix and saves the prefill compute, so TTFT and GPU time, but every output token is still generated. Provider prompt caching is the same mechanism inside a hosted API, exposed through cache points and billed at a discount on cached input tokens. Exact-match response caching skips the model entirely when the same request repeats; it saves everything but only on repeats. Semantic caching skips the model for requests that are merely similar, saving the most and risking wrong answers. You layer them: response caches in front, prompt or prefix caching behind, semantic caching only where a slightly wrong reuse is acceptable.

**Deeper explanation:**

| Layer | What it saves | What it cannot save | Main risk |
| --- | --- | --- | --- |
| Engine prefix cache | prefill compute for the shared prefix | output tokens, decode time | silent misses from unstable prefixes |
| Provider prompt cache | money on cached input tokens, TTFT | output tokens | paying write premiums with no reads |
| Exact-match response cache | the whole call | anything that does not repeat | staleness, personalization leaks |
| Semantic cache | the whole call for near-duplicates | nothing when it hits | false positives |

Reason about where the tokens are: a chat app with a 4k-token system prompt and 300-token turns has over 90% of its input in the prefix, so prompt caching is the first lever and response caching only helps FAQ-like repeats.

**Follow-ups they will ask:**
- Which do you implement first: prompt or prefix caching, because it is deterministic and cannot return a wrong answer.
- Can output tokens be cached: only by response caching, since decode always runs otherwise.

**Mistakes to avoid:**
- "We cache in Redis" without saying what is keyed on what.
- Expecting prompt caching to reduce output cost or decode latency.

### Q. How does provider prompt caching work, and how do you structure prompts to maximize hits?
**Short answer (45 seconds):** Providers cache the processed state of a prompt prefix and bill cached input tokens at a discount. Anthropic is explicit: you place `cache_control` breakpoints, up to four, on content blocks; the prefix up to each breakpoint is cached for five minutes, refreshed on every hit, with a one-hour option at a higher write price; a write costs more than normal input and a read far less. OpenAI is automatic for prompts above a minimum length, matching in 128-token increments and reporting `cached_tokens` in usage. In both, the match is on exact bytes in a fixed render order, tools then system then messages for Anthropic. So: static content first, breakpoints at stability boundaries, volatile content after the last breakpoint, and verify with the usage fields.

**Deeper explanation:**

```python
response = client.messages.create(
    model=MODEL, max_tokens=1024,
    tools=TOOLS,                                              # stable, rendered first
    system=[{"type": "text", "text": SYSTEM_PROMPT,
             "cache_control": {"type": "ephemeral"}}],        # breakpoint: tools + system cached
    messages=history + [{"role": "user", "content": question}],
)
u = response.usage
log(u.input_tokens, u.cache_creation_input_tokens, u.cache_read_input_tokens)
```

The minimum cacheable prefix is model-dependent, and a shorter prefix silently does not cache: creation tokens stay at zero and nothing errors. With the 5-minute TTL a write pays for itself at the second hit, so the pattern is safe for any prefix that is reused within minutes. Silent invalidators: a timestamp or user name in the system prompt, request IDs, unsorted JSON in tool definitions, a tool list that varies per request, switching models (caches are per model), and changing parameters that render into the prompt.

**Follow-ups they will ask:**
- Where does the per-request content go: after the last breakpoint; the unique question is deliberately outside the cached prefix.
- Bursty traffic with 20-minute gaps: the 1-hour TTL at the higher write price, or a cheap keep-alive request before expiry.

**Mistakes to avoid:**
- Placing the breakpoint after the unique question, so every request writes and none reads.
- Assuming automatic caching removes the need to order the prompt; the prefix rule still applies.

### Q. Implement prompt caching for a multi-turn agent with tools. Where do the breakpoints go, and what breaks them?
**Short answer (45 seconds):** There are two stability boundaries: the static preamble (tool definitions plus system prompt) and the growing conversation. Put one explicit breakpoint on the last system block so tools and system are a guaranteed read point, and one on the latest turn so each request reads the entire prior conversation and writes only the new delta. Keep history append-only: tool calls and results are appended as they happen. Anything that edits earlier turns, truncation, summarization, inserting and later removing a reminder, re-ordering, breaks the cache from that point on. For instructions that change mid-conversation, append rather than edit the preamble.

**Deeper explanation:**

```text
[tools][system]*BP1*[u1][a1 tool_use][u1 tool_result][a2] ... [uN]*BP2*
turn N+1: reads everything up to BP2, writes only the new tail, BP2 moves forward
healthy usage: cache_read grows every turn; cache_creation ≈ size of the last turn
unhealthy:     cache_creation ≈ whole conversation every turn -> something rewrites the prefix
```

Agent-specific traps: tool results that contain timestamps are fine because they are appended once and then stable, but a system prompt that contains the current time is not. Adding a tool on turn five changes the tools block and invalidates everything after it. Parallel workers that each assemble a slightly different prefix over the same context write N caches and read none; give them one byte-identical prefix. When the context must be compacted, accept one miss and re-establish the breakpoints. If first-request latency matters after a deploy, pre-warm the static prefix with a tiny request.

**Follow-ups they will ask:**
- What do you log per call: uncached input, cache writes, cache reads, model and prompt version, and you alert when the read share drops.
- Self-hosting instead: the same layout hits the engine's prefix cache automatically, with no breakpoints to manage.

**Mistakes to avoid:**
- Serializing the message array differently from turn to turn, for example with unstable key order.
- Injecting a per-turn status line such as the remaining budget into the system prompt.

### Q. What is semantic caching, and what is its biggest risk?
**Short answer (45 seconds):** Semantic caching embeds the incoming query, searches a vector store (Redis, pgvector, Milvus) for a previously answered query above a similarity threshold, and returns that stored answer without calling the model. The biggest risk is false positives: "how do I cancel my order" and "how do I cancel my subscription" embed close together, so do a question and its negation, and the same question for a different tenant, month or user has a different correct answer. A false hit is a silent wrong answer, so semantic caching belongs only on stateless, non-personalized, slowly changing questions, with a high threshold, a scoped key and a measured false-hit rate.

**Deeper explanation:**

```text
query -> embed -> nearest neighbor within (tenant, prompt version, doc-set version)
      -> similarity >= threshold AND entities match (numbers, IDs, dates)?
      -> yes: return cached answer, log the hit for audit
      -> no:  call the model, store (query, embedding, answer, created_at) with TTL
```

Tune the threshold on a labeled set of paraphrase pairs and near-miss pairs and plot precision against hit rate; the threshold that keeps false hits below what the product tolerates is usually high, and an illustrative starting point is a strict value tuned downward only with evidence. A second gate removes most remaining false hits: an exact match on extracted entities, or a cheap small-model check that the cached answer is valid for the new question. The embedding call adds a little latency and cost, which is acceptable. Audit continuously by re-answering a sample of hits offline and comparing.

**Follow-ups they will ask:**
- Where does it work: FAQ bots, documentation Q&A, repeated support questions with stable answers.
- Where never: personalized answers, calculations, anything with user data or time sensitivity.
- Why not one global threshold: different question types have different similarity distributions, so tune per domain or per intent.

**Mistakes to avoid:**
- Caching across tenants or users.
- Reporting hit rate without a measured false-hit rate.

### Q. When is exact-match response caching worth doing?
**Short answer (45 seconds):** When identical requests recur and the answer may be reused: FAQ-style queries, deterministic transformations such as classification or extraction over the same input, retries after a client timeout, and idempotency for duplicate submissions. The key must cover everything that changes the output: model ID, prompt template version, the full messages, tools, response schema and sampling parameters, scoped by tenant when prompts contain tenant data. Store in Redis with a TTL and mark cached responses so metrics can tell them apart. It is not worth it for open-ended chat where little repeats, and it is dangerous when outputs include personalization.

**Deeper explanation:**

```js
const key = "llm:v3:" + sha256(JSON.stringify({
  model, promptVersion, tenantId, messages, tools, responseSchema, temperature, maxTokens,
}));
const hit = await redis.get(key);
if (hit) return { ...JSON.parse(hit), cached: true };
const out = await callModel(...);
if (out.finishReason === "stop") await redis.set(key, JSON.stringify(out), "EX", 3600);
return out;
```

Temperature 0 does not guarantee bit-identical outputs, so the cache stores "an acceptable answer", which is fine for deterministic tasks. Add request coalescing: when many identical requests arrive at once, store an in-flight marker so one model call serves all of them, which also protects you from retry storms. For streaming clients, cache the assembled text and replay it as a stream so the contract does not change. Never cache errors, refusals or truncated outputs.

**Follow-ups they will ask:**
- Expected hit rate: low for chat, high for pipelines that re-process duplicate inputs; measure before building.
- Staleness: TTL sized to how fast the truth changes, plus the version fields in the key.
- Streaming UX: replay with chunking, optionally faster than real generation.

**Mistakes to avoid:**
- Leaving the model or prompt version out of the key.
- Caching outputs that contain user-specific content under a key that another user can hit.

### Q. How do you invalidate inference caches when a prompt or model changes?
**Short answer (45 seconds):** Design the keys so invalidation is automatic. Put the pinned model ID and the prompt template version into every response and semantic cache key, so a deploy that changes either stops hitting old entries, which expire by TTL; never rely on flushing Redis. Namespace keys per environment and tenant. For RAG-backed semantic caches include the document-set version so a content update invalidates answers derived from old content. Prefix caches need nothing: a changed byte is a different prefix and old entries age out within minutes. What you must do for prefix caches is keep rendering deterministic so you do not invalidate them by accident on every request.

**Deeper explanation:**

```text
response cache key = ns:v{N} : tenant : model_id : prompt_v : doc_set_v : sha256(payload)
bump N          -> everything invalid at once (emergency: a bad answer was cached)
bump prompt_v   -> only that prompt's entries miss
pinned model_id -> never a floating alias such as "latest"
```

Keep prompt templates in a registry with versions and log the version with every call; A/B tests of prompts then have separate caches by construction, which is what you want. During a model canary the new model starts with a cold cache, so warm it or compare latency only after warm-up. Use Redis eviction with TTLs on every entry (`volatile-ttl` or `allkeys-lru`) so forgotten entries cannot accumulate. For policy-driven answers, such as refund rules, include the policy version in the key so a rule change invalidates the cached answers that depend on it.

**Follow-ups they will ask:**
- Do provider caches need invalidation: no; change the prefix and the old entries expire, but expect write costs right after a deploy.
- How do you test this: a deploy check asserting that the new prompt version misses once and hits on the second identical call.

**Mistakes to avoid:**
- FLUSHALL as the invalidation strategy.
- A floating model alias in the key, which silently mixes outputs from two model versions.

### Q. How do you measure whether caching is working?
**Short answer (45 seconds):** Log per request the cached input tokens, uncached input tokens, cache writes, response-cache and semantic-cache hit or miss, and the latency of each layer. Compute the hit ratio by layer and by prompt version, the money saved as cached tokens times the price difference, and TTFT with hits versus without. Add standing checks: an integration test asserting that the second identical request shows cache reads above zero, and an alert when the read share for a prompt version drops, because caching regressions are silent and only show up as a higher bill.

**Deeper explanation:**

```sql
SELECT prompt_version,
       SUM(cache_read_tokens)::float
         / NULLIF(SUM(input_tokens + cache_read_tokens + cache_creation_tokens), 0) AS read_ratio,
       AVG(ttft_ms) FILTER (WHERE cache_read_tokens > 0) AS ttft_hit_ms,
       AVG(ttft_ms) FILTER (WHERE cache_read_tokens = 0) AS ttft_miss_ms
FROM llm_calls
WHERE ts > now() - interval '1 day'
GROUP BY prompt_version
ORDER BY read_ratio;
```

Dashboard panels worth having: read ratio per prompt version, write-without-read rate (which flags breakpoints placed after unique content), TTFT split by hit and miss, response cache hit rate per feature, and a sampled false-hit rate for the semantic cache. For self-hosted engines, scrape the prefix cache hit metrics from `/metrics` as well. When a read ratio drops after a deploy, diff the rendered prompt bytes of two consecutive requests; the first differing byte is the bug.

**Follow-ups they will ask:**
- What ratio is good: for chat with a large preamble most input should be reads after warm-up; the actionable signal is a sudden drop, not an absolute number.
- How do you report savings: cached tokens times the price difference per month, from the same logs finance already sees.
- How often do you check: on every prompt-assembly change, through the standing test, not once at setup.

**Mistakes to avoid:**
- Checking once at setup and never again.
- Celebrating semantic cache hit rate without auditing the hits for correctness.

### Practice
- Instrument a provider call to log input, cache write and cache read tokens; send the same prompt three times and confirm the second and third show reads; then add a timestamp to the system prompt and watch reads fall to zero.
- Build a 50-pair set of paraphrases and near-misses for a FAQ, embed them, and plot precision against hit rate across several similarity thresholds.
- Add an exact-match response cache with request coalescing to a Node gateway and verify that 20 concurrent identical requests produce exactly one model call.
- Say it out loud: name the four caching layers and what each one saves, in 60 seconds.

## Cost Engineering

> Cost questions separate engineers who ship demos from engineers who run products. Interviewers want the arithmetic done out loud: tokens to money, GPU-hours to tokens, and the realization that utilization, not model choice, usually dominates self-hosted cost. A weak answer is "we use the cheapest model". A strong answer computes cost per request and per task, ranks the levers by payoff, and frames model choice as an SLO decision.

### Concepts you must understand
- Per-request API cost = (input_tokens × P_in + output_tokens × P_out) / 1,000,000, plus cache writes and reads at their own rates; output tokens are priced several times higher than input, so verbosity is expensive.
- Self-hosted cost per million tokens = GPU price per hour / (achieved tokens per second × 3,600 / 1,000,000); achieved, not peak, is what you divide by, so utilization dominates.
- GPUs bill by the hour whether busy or idle, so raising utilization (batching, consolidating workloads, filling troughs with deferrable jobs, right-sizing replicas) is the main self-hosting lever.
- Batch APIs trade latency for a large discount (both Anthropic and OpenAI offer about half price with completion within a window of up to a day); use them for evals, backfills, classification and nightly summaries.
- Small models and distillation: route narrow tasks to small models, fine-tune a small model on a large model's outputs, keep the large model as teacher and fallback, and gate the switch with an eval set.
- Right-sizing context: trim history, retrieve less, compress tool outputs, cap max_tokens and tighten system prompts; cost, TTFT and KV memory all scale with tokens.
- Measure cost per request and per feature from usage logs tagged with feature, tenant, prompt version and trace ID; the unit economics figure is cost per successful task, not per call.
- SLO-driven model choice: define the quality bar, the latency target and the cost ceiling first, then choose the cheapest model and settings that meet all three, and re-run the decision when models change.
- Build versus buy: self-host when volume is steady and high enough to keep GPUs busy, when data must stay in-house, or when you need custom models; buy when traffic is spiky or small, when you need frontier quality, or when the team cannot carry GPU operations.

### Q. How do you compute the cost of an LLM feature, and what is the most common mistake in that math?
**Short answer (45 seconds):** Per call: input tokens times the input price plus output tokens times the output price, both per million tokens, plus cache writes and reads at their rates, summed over every call the feature makes, including retries, tool-loop iterations, judge calls and embeddings, then multiplied by calls per day. The most common mistake is counting one call per user action. An agent that makes eight model calls over a growing context pays for that context eight times, so the real cost per task is often an order of magnitude above the naive estimate. The second mistake is forgetting that output tokens cost several times more than input, so verbosity drives the bill.

**Deeper explanation:** Illustrative prices, not any vendor's: P_in = 1 unit per million tokens, P_out = 4 units per million.

```text
Single call: 3,000 in, 500 out  ->  3,000 × 1 / 1e6 + 500 × 4 / 1e6 = 0.003 + 0.002 = 0.005 per call
1,000,000 calls per month        ->  5,000 units

Agent task: 8 steps, context grows from 3k to 10k tokens, ~150 output tokens per step
  input  ≈ 8 × 6.5k = 52k tokens -> 0.052     output ≈ 1,200 tokens -> 0.0048     total ≈ 0.057
  with prompt caching, most of the 52k are repeated prefix: ~45k reads at a tenth of the price
  input ≈ 45k × 0.1 + 7k × 1 = 11.5k token-equivalents -> 0.0115, total ≈ 0.016
```

Tag each call with the feature and a trace ID and sum per trace; that gives cost per task, which you then compare with the value of the task (revenue, minutes saved, tickets closed).

**Follow-ups they will ask:**
- How do you handle unknown output length: measure it per feature from logs and budget on the p95, with max_tokens as the hard cap.
- Do reasoning or thinking tokens count: they are billed as output, so budget them like output.

**Mistakes to avoid:**
- Quoting a single call's price as the feature's cost.
- Leaving judge calls, retries and embedding calls out of the sum.

### Q. Convert GPU-hour pricing into a price per million tokens. What dominates the result?
**Short answer (45 seconds):** Cost per million tokens is the hourly GPU price divided by the millions of tokens the GPU actually produces in an hour, which is achieved tokens per second times 3,600 divided by a million. Peak throughput is what a load test shows; achieved throughput is peak times utilization. At full utilization a GPU can look far cheaper than an API; at 10% it is far more expensive. Utilization dominates, then throughput per GPU (batching, quantization, model size), then the hourly price itself.

**Deeper explanation:**

```text
cost_per_1M_tokens = gpu_price_per_hour / (achieved_tok_s × 3600 / 1e6)
Illustrative: GPU at 2 units/hour, knee throughput 2,000 tok/s (prompt + completion tokens)
  100% utilization: 7.2M tok/hour   ->  0.28 per 1M
   30% utilization: 2.16M tok/hour  ->  0.93 per 1M
   10% utilization: 0.72M tok/hour  ->  2.78 per 1M
```

Count both prompt and completion tokens, because prefill consumes GPU time even though it is cheap per token; a prefill-heavy RAG workload has a lower effective token rate than a chatty one. Add the rest of the node (CPU, storage, egress), redundancy (N+1 is idle headroom by design) and the engineers who run it. When comparing with API prices, match the input and output mix of your real traffic, since providers price the two differently and your blended number hides that.

**Follow-ups they will ask:**
- How do you measure achieved tokens per second: from the engine's prompt and generation token counters over a full day divided by seconds, not from a benchmark.
- Does spot pricing change the conclusion: it lowers the hourly price and adds interruption handling; it does nothing about utilization.
- Why does the knee matter: you cannot plan on throughput beyond the knee without breaking the latency SLO, so the knee is your usable peak.

**Mistakes to avoid:**
- Dividing by peak throughput from a benchmark.
- Comparing a blended self-hosted cost with an API's output price alone.

### Q. Why is utilization the main cost lever for self-hosted inference, and how do you raise it?
**Short answer (45 seconds):** Because a GPU costs the same per hour whether it serves ten or two thousand tokens per second, so every idle second is paid for. Traffic is bursty and diurnal and you must keep headroom for latency and failures, so real utilization is low unless you work at it. Raise it by batching more per step within the SLO, consolidating small models onto fewer GPUs or using multi-LoRA, filling troughs with deferrable work such as evals, backfills and embeddings, scaling down overnight, quantizing to fit more concurrency per GPU, and sending spiky low-volume workloads to a provider instead of a dedicated GPU.

**Deeper explanation:** You cannot run at 100% and meet p95 TTFT, so the peak-hour target is near the knee, often 60 to 70%. The real lever is the daily average: peak hours near 70% and nights near zero average out to something like 25%. A priority queue fixes this: the batch class runs whenever interactive demand leaves capacity, so the same GPUs do the nightly work for free.

```text
Illustrative day: 8 peak hours at 70%, 16 off-peak hours at 5%  ->  average ≈ 27%
add deferrable batch work filling 12 off-peak hours to 60%     ->  average ≈ 53%
cost per token roughly halves with no change to the model or hardware
```

Track tokens per GPU-hour as the KPI and compare it with the measured knee, per model. Share GPUs across teams through one internal platform; a single small team rarely keeps a GPU busy.

**Follow-ups they will ask:**
- Which utilization metric: tokens per GPU-hour against the knee, not the DCGM utilization percentage.
- Can MIG or time-slicing help: partitioning works for small models; LLM serving usually wants whole GPUs for the memory.
- Does scale-to-zero raise utilization: yes for development fleets; for interactive traffic the cold start makes it unusable.

**Mistakes to avoid:**
- Planning on peak capacity without measuring the average load.
- Benchmarking engines for a 10% throughput gain while utilization sits at 15%.

### Q. When would you use a batch API?
**Short answer (45 seconds):** When nobody is waiting: evaluations, backfilling classifications or embeddings, nightly summaries, enrichment pipelines, generating training data for distillation, periodic reports. Both major providers offer batch endpoints at roughly half the per-token price with completion inside a window of up to a day, and results come back in any order keyed by your custom ID. Self-hosted, the equivalent is offline generation at full batch on spare capacity. The constraint is design: the pipeline must be asynchronous, idempotent and tolerant of partial failures.

**Deeper explanation:**

```python
batch = client.messages.batches.create(requests=[
    {"custom_id": f"doc-{d.id}",
     "params": {"model": MODEL, "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt_for(d)}]}}
    for d in docs
])
  # poll batch.processing_status until "ended", then iterate results and key them by custom_id;
  # each result is succeeded, errored, canceled or expired, so resubmit only the failures
```

Design points: write results idempotently keyed by custom ID, keep an online path for urgent items, and separate batch rate limits from interactive ones in your capacity plan. Batches are the cheapest way to label a hundred thousand examples with a teacher model for distillation, and the right way to run a nightly eval over production samples. Where supported, shared prefixes inside a batch can also benefit from prompt caching.

**Follow-ups they will ask:**
- What if some items fail: resubmit only those; idempotent writes make this safe.
- Is the window a guarantee: it is a target window, so anything with a deadline needs an online fallback.
- Can batch serve a user-facing feature: only non-interactive ones, like a daily digest prepared ahead of time.

**Mistakes to avoid:**
- Building a synchronous pipeline that blocks on a batch.
- Mixing urgent and deferrable items in the same submission.

### Q. How do you cut cost without changing the model?
**Short answer (45 seconds):** Tokens are the bill, so remove tokens. Shorten the system prompt and make it cacheable; cap max_tokens and ask for terse, structured outputs; retrieve fewer, better chunks instead of stuffing context; window long conversations; compress tool results before they go back into the context by returning the fields you need rather than raw JSON dumps; stop retry loops early; and use prompt caching on every repeated prefix. On the serving side, raise utilization and batch deferrable work. Measure tokens per request by feature before and after, and watch the p95, because a few giant requests dominate spend.

**Deeper explanation:**

```text
Illustrative RAG request
before: 500 system + 8 chunks × 800 + 100 question = 7,000 input, 400 output
after:  500 system (cached) + 4 chunks × 500 + 100 question = 2,600 input (500 of it cached), 250 output (schema-constrained)
input tokens down 63%, output down 38%; TTFT and KV footprint fall with them
```

Tool-output compression is the largest hidden lever in agents: a 20 KB API response becomes 2 KB of relevant fields, and the saving repeats on every later step because the result stays in context. Conversation windowing keeps the last few turns verbatim plus a running summary, accepting one cache miss when the summary changes. Structured output removes prose around the JSON. Alert on growth in tokens per request per feature, since prompt bloat creeps in with every new feature.

**Follow-ups they will ask:**
- Does trimming context hurt quality: sometimes; use the eval set to find the smallest context that holds the quality bar.
- How do you find the heavy requests: p95 and p99 of input tokens by feature, then read a handful of them.
- Does caching count as "not changing the model": yes, and it is usually the single largest saving.

**Mistakes to avoid:**
- Cutting context blindly and discovering the quality drop in production.
- Optimizing the average while the p99 requests drive the bill.

### Q. Explain distillation to a small model as a cost strategy. What are the risks?
**Short answer (45 seconds):** Use the large model as a teacher: run it over a representative sample of real inputs to produce labels or outputs, fine-tune a small model on those pairs for one narrow task, and route that task to the small model with the large one kept as fallback. For classification, extraction, routing and formatting tasks a small model trained this way often matches the teacher on your distribution at a fraction of the cost and latency. The risks: the student inherits the teacher's errors, fails on inputs outside the training distribution, does not follow task changes, and needs an eval set and a retraining pipeline, which is engineering you now own.

**Deeper explanation:** The process: define the task and output schema; sample inputs from production, stratified across tenants and edge cases; label them with the teacher through a batch API; hold out an eval set and have humans spot-check the teacher's labels; fine-tune a small model (LoRA on a small open model, or a hosted fine-tuning service); compare student against teacher on the held-out set by slice; deploy behind the router in shadow mode first; then monitor agreement on a sampled stream and retrain on drift.

```text
teacher labels 100k examples via batch (cheap)  ->  student fine-tune  ->  eval by slice
route: student for in-distribution inputs; teacher for low-confidence or novel inputs; log both
```

Keep the output contract identical so the router can swap models without touching callers. Break-even depends on volume against the engineering cost of the pipeline; at low volume the teacher is cheaper overall.

**Follow-ups they will ask:**
- When not to distill: tasks needing broad knowledge or open-ended reasoning, low volume, or requirements that change monthly.
- How do you detect student drift: periodic agreement sampling against the teacher plus monitoring of the input distribution.
- Any policy concerns: check the provider's terms on using outputs to train other models before you start.

**Mistakes to avoid:**
- Distilling without a held-out eval set.
- Trusting teacher labels without spot-checking their quality.

### Q. Build versus buy: when does self-hosting beat API pricing?
**Short answer (45 seconds):** Self-hosting wins when three things hold: enough steady volume to keep GPUs busy, since utilization is the whole argument; a task narrow enough or a model good enough that an open model meets the quality bar; and a team that can run GPUs, meaning capacity planning, on-call, upgrades and security. It also wins on constraints APIs cannot satisfy: data residency, strict privacy, custom fine-tunes, predictable latency. APIs win for spiky or low volume, frontier-quality needs, fast iteration and small teams. Do the math with achieved utilization, not peak, and include people and headroom.

**Deeper explanation:**

```text
monthly_api_cost  = Σ tokens × price (by model, after caching and batch discounts)
monthly_self_cost = GPUs × hours × hourly price + engineers + storage and egress + headroom replicas
Illustrative: 2 GPUs at 2 units/hour × 730 hours = 2,920 units/month
  at 30% average utilization and a 2,000 tok/s knee: ≈ 3.2B tokens/month served -> ≈ 0.93 per 1M tokens
  before engineer time; compare with the API bill for the same 3.2B tokens at your mix
```

The hybrid is usually right: self-host the narrow high-volume task with a small model, buy frontier quality for the hard tail, and route between them. Hosted open-model providers are a middle path with open-model prices and no GPU operations. Revisit the decision regularly, because API prices and open-model quality both move quickly.

**Follow-ups they will ask:**
- What volume is "enough": when a dedicated GPU would average roughly half utilized or more; below that per-token pricing wins.
- Is self-hosting the only answer to privacy: no; enterprise agreements with zero retention may solve it more cheaply.
- Hidden costs: model upgrades, security patching, GPU supply, and the on-call rota.

**Mistakes to avoid:**
- Comparing peak GPU throughput cost to API prices.
- Leaving the engineers out of the self-hosted number.

### Q. How do you attribute cost per feature in an agent that makes many calls?
**Short answer (45 seconds):** Every model call carries a trace ID, feature name, tenant, prompt version and step index, and logs its usage: input, output, cache read, cache write and model. A nightly job joins usage with a dated price table to produce cost per call, then rolls up by trace for cost per task and by feature per day, and joins to the task outcome so the headline is cost per successful task. Alert on anomalies: a looping agent shows up as a trace with unusually many steps or tokens, and a prompt regression as a step change in tokens per task for one feature.

**Deeper explanation:**

```sql
WITH priced AS (
  SELECT c.trace_id, c.feature, c.ok,
         (c.input_tokens * p.in_price + c.output_tokens * p.out_price
          + c.cache_read_tokens * p.cache_read_price + c.cache_write_tokens * p.cache_write_price) / 1e6 AS cost
  FROM llm_calls c
  JOIN price_table p ON p.model = c.model AND c.ts >= p.valid_from AND c.ts < p.valid_to
)
SELECT feature,
       COUNT(DISTINCT trace_id) AS tasks,
       SUM(cost) AS total_cost,
       SUM(cost) / NULLIF(COUNT(DISTINCT trace_id) FILTER (WHERE ok), 0) AS cost_per_successful_task
FROM priced
GROUP BY feature
ORDER BY total_cost DESC;
```

Implement it as a thin wrapper around the client that injects metadata and records usage, or as OpenTelemetry span attributes exported to your warehouse. Version the price table by date because prices change. For self-hosted models, allocate GPU-hours to features by their share of tokens. Keep a cheap running counter per tenant in Redis for real-time budget limits and do exact accounting nightly. Put cost next to quality and latency on the same per-feature dashboard so trade-offs are visible.

**Follow-ups they will ask:**
- One call serving two features: attribute to the feature that triggered it and report shared infrastructure separately.
- How do you price cached tokens: at the provider's cache read rate from the same price table.
- What is the first anomaly alert you would add: tokens per trace above a per-feature ceiling, which catches loops within minutes.

**Mistakes to avoid:**
- Attributing by counts of user actions instead of tokens.
- A single hard-coded price in the code.

### Practice
- Pull a week of usage logs (or synthesize them) and compute cost per feature and per successful task; read the three most expensive traces end to end.
- Take a real RAG prompt, measure its tokens, cut the context in half, and compare quality on 50 eval questions against the cost per request.
- Price a self-hosted replica at three utilization levels and plot cost per million tokens against an illustrative API price to find the break-even utilization.
- Say it out loud: walk through the eight-step agent cost example and explain why prompt caching changes the answer.

## Reliability & Observability for Inference

> Interviewers ask these to find out whether your LLM feature survives a bad day: a provider outage, a 429 storm, a replica stuck loading, a new model that quietly got worse. A weak answer is "we retry three times". A strong answer separates timeouts by phase, retries under a budget, sheds load before the queue grows, fails over through a tested chain, rolls models out like code, and can name the metrics on the dashboard and what each one would make you do.

### Concepts you must understand
- Streaming calls need phase-specific timeouts: connect, time to first token, idle gap between tokens, and a total deadline; a single request timeout either kills long answers or lets stuck ones hang.
- Retry only what is safe (connection errors, 429, 5xx, timeouts before the first token) with exponential backoff and jitter, under a retry budget so a degraded upstream does not receive double traffic.
- 429 handling means reading Retry-After and the remaining-limit headers, pacing with a client-side token bucket, giving interactive traffic the budget first, and spreading across keys, regions or providers.
- Backpressure is bounded queues and fast rejection at the gateway driven by engine signals such as waiting requests and KV usage; unbounded buffering turns overload into timeouts.
- Graceful degradation is a tested fallback chain (primary model, secondary provider, smaller model, cached or static answer) behind circuit breakers, with the degradation logged and visible.
- A new model is canaried like code: pinned versions, shadow traffic first, a small live percentage compared on quality, latency, cost and refusal rate, automated rollback.
- The core dashboard: TTFT, TPOT and end-to-end latency at p50, p95 and p99, queue time, throughput, GPU utilization, KV cache usage, preemptions, prefix cache hit rate, error rates by class, cost per request.
- Tracing carries one trace ID from the Node gateway through the Python router into the engine, with spans holding model, tokens, cache hits, routing decisions and provider request IDs so a slow request can be explained end to end.
- vLLM publishes Prometheus metrics at `/metrics` and can export OpenTelemetry traces, so the engine is a first-class part of the observability stack rather than a black box.

### Q. Design timeouts and retries for streaming LLM calls.
**Short answer (45 seconds):** Use four timers, not one. A connect timeout of a few seconds. A time-to-first-token timeout sized from your TTFT p99 plus queueing headroom, because a request that has produced no token can be retried safely. An idle timeout between tokens of a few seconds, because a stalled stream rarely recovers. And a total deadline derived from max_tokens times expected TPOT. Retry only before the first token and only on connection errors, 429 and 5xx, with exponential backoff plus jitter, at most two or three attempts, under a process-wide retry budget of around 10% of requests. Once tokens have started, do not blindly retry: surface a partial answer with an error, or restart with the streamed text as context if the task allows it.

**Deeper explanation:**

```js
async function* streamWithTimeouts(body, { firstTokenMs = 15000, idleMs = 5000, totalMs = 90000 } = {}) {
  const ac = new AbortController();
  const total = setTimeout(() => ac.abort(new Error("total deadline")), totalMs);
  let idle = setTimeout(() => ac.abort(new Error("first token timeout")), firstTokenMs);
  try {
    const stream = await client.chat.completions.create({ ...body, stream: true }, { signal: ac.signal });
    for await (const chunk of stream) {
      clearTimeout(idle);
      idle = setTimeout(() => ac.abort(new Error("idle timeout")), idleMs);
      yield chunk;
    }
  } finally {
    clearTimeout(total); clearTimeout(idle);
  }
}
```

Propagate the remaining deadline downstream (gateway to router to engine) so no layer retries past the client's patience, and abort the upstream request when the client disconnects so the engine frees the sequence. SDKs retry 429, 5xx and connection errors on their own by default, so set their retry count low and own the policy in one place; otherwise gateway retries multiply SDK retries.

**Follow-ups they will ask:**
- Why not retry mid-stream: you would duplicate or contradict text already shown, and the stuck upstream is probably overloaded.
- How do you choose the first-token timeout: from TTFT p99 by prompt-length bucket plus the queue-wait SLO.

**Mistakes to avoid:**
- One 120-second timeout for everything.
- Retrying 400s, schema errors or content-policy refusals, which will fail again.

### Q. How do you handle 429s from a provider without hurting interactive users?
**Short answer (45 seconds):** First, avoid them: pace outgoing traffic with a client-side token bucket sized under the provider's request and token limits, adapting from the remaining-limit headers on every response. When a 429 arrives, honor Retry-After, back off with jitter and count it against the retry budget. Protect interactive users by giving them the bucket first: background and batch jobs draw from a smaller allowance and pause entirely while 429s are occurring. Spread load across keys, regions or a second provider, and move deferrable work to the batch API, which has its own limits. Alert on the 429 rate, because sustained 429s mean you need a higher limit or less traffic, not more retries.

**Deeper explanation:** Providers return remaining-request and remaining-token headers (OpenAI's `x-ratelimit-remaining-*`, Anthropic's `anthropic-ratelimit-*`) and `retry-after` on a 429; an adaptive limiter updates its view from them on every response and delays low-priority requests when the remaining tokens drop below a reserve. Estimate tokens before sending (tokenizer count plus max_tokens) so the limiter reasons in the provider's units.

```text
outgoing budget per minute (TPM):  interactive may use up to 100%
                                   background may use min(remaining headroom, 30%)
on 429: honor retry-after, jitter the retry, pause background class, count toward retry budget
on repeated 429 for interactive: spill to secondary provider with the same prompt contract
```

Beware the thundering herd when a window resets: jitter every retry. Log each 429 with tenant and feature so you can see which caller is consuming the budget, and treat rejected requests as capacity lost even though no tokens are billed.

**Follow-ups they will ask:**
- What if the provider limit caps your growth: request a higher tier, split across accounts or regions, add a second provider, or self-host the narrow high-volume task.
- SDK retries and your limiter: keep SDK retries at one or zero and let the gateway's limiter own pacing.

**Mistakes to avoid:**
- Tight retry loops that amplify the storm.
- One undifferentiated pool shared by background jobs and interactive users.

### Q. What is backpressure in an inference gateway, and how do you implement it?
**Short answer (45 seconds):** Backpressure is refusing or slowing new work when downstream cannot keep up, instead of buffering it. In an inference gateway that means bounded queues with a maximum wait per class, a concurrency semaphore per upstream sized to its measured capacity, and fast 429 or 503 responses with Retry-After when a bound is hit. The signals come from the engines (waiting requests, KV cache usage, preemptions) and from your own queue wait times. In Node, never buffer whole responses: pipe the upstream SSE stream to the client so a slow client slows only its own stream instead of filling memory.

**Deeper explanation:**

```js
const sem = new Semaphore(maxInflightPerReplica * replicaCount);
app.post("/v1/chat", async (req, res) => {
  const maxWait = req.priority === "interactive" ? 2000 : 15000;
  const slot = await sem.acquire({ timeoutMs: maxWait });
  if (!slot) return res.status(503).set("Retry-After", "2").json({ error: "overloaded" });
  req.on("close", () => slot.abortUpstream());            // client left: free the GPU
  try { await pipeline(await upstreamStream(req.body), res); }
  finally { slot.release(); }
});
```

Make the limit adaptive: additive increase, multiplicative decrease on the semaphore size driven by observed TTFT, the same idea as TCP congestion control, so the gateway finds the knee on its own. Shed by class under overload, batch first. A replica with KV usage above roughly 95% or rising preemptions gets fewer admissions. Remove queued requests whose clients disconnected so they do not consume a slot when they reach the front. Show the user "high demand" with a cancel button rather than a spinner that ends in a timeout.

**Follow-ups they will ask:**
- 503 or 429: 429 means the caller exceeded its own limit; 503 means the service is overloaded; both carry Retry-After.
- How is this different from rate limiting: rate limiting is per-tenant policy; backpressure is capacity protection regardless of tenant.
- Where does the engine help: vLLM stops admitting when KV is full and reports the waiting count, which is your early signal.

**Mistakes to avoid:**
- Unbounded in-memory arrays of pending requests.
- Buffering the whole completion before writing anything to the client.

### Q. How do you fail over to another model without breaking the product?
**Short answer (45 seconds):** Build a fallback chain in configuration: primary model, then an equivalent model at a second provider or region, then a smaller model, then a cached or static response. Put a circuit breaker in front of each upstream that opens after an error-rate or timeout threshold and probes with a trickle of traffic before closing. Keep the prompt contract portable, same tools and same output schema, with per-model adjustments isolated in an adapter layer. Mark degraded responses in logs and metrics, and tell the user when quality is reduced if it matters. Then test the chain on a schedule, because an untested fallback is a second outage waiting to happen.

**Deeper explanation:**

```text
breaker per upstream (provider + model + region):
  closed  -> error rate above threshold over a 30 s window -> open (fail fast for 30 s)
  open    -> half-open: allow a few probe requests -> closed if they succeed, else open again
triggers for fallback: 5xx, timeout before first token, 429 with empty budget, breaker open, model unavailable
```

The adapter layer absorbs the differences that otherwise leak into product code: how the system prompt is passed, tool-call formats, context limits, stop sequences, JSON mode support. Run the golden set against every fallback model so you know the quality hit before you depend on it. For a failure after tokens have streamed, finish with a visible error marker, or restart on the fallback with the partial text as context; for structured outputs always restart.

**Follow-ups they will ask:**
- Where does the breaker live: in the gateway or router, one per upstream, shared across worker processes through Redis if you have many.
- Is the fallback's cache warm: no; accept the TTFT hit or pre-warm its static prefix alongside the primary.

**Mistakes to avoid:**
- A fallback chain that has never been exercised in production conditions.
- Assuming the fallback model has the same limits, context window and cost.

### Q. How do you roll out a new model version safely?
**Short answer (45 seconds):** Treat it like a code deploy. Pin exact model versions, never floating aliases. Start with shadow traffic: send a copy of real requests to the new model, discard its answers, and compare quality (golden metrics or a judge), latency, cost, refusal rate and format adherence against the current model. Then canary a few percent of live traffic with the same comparison on real outcomes, ramp in steps, and automate rollback on any regression. Version prompts together with the model, because a prompt tuned for one model often needs edits for the next, and keep the old model warm until the rollout is finished.

**Deeper explanation:**

```yaml
  # gateway routing config sketch
features:
  summarize:
    primary: {model: "model-a-2026-05", weight: 95}
    canary:  {model: "model-b-2026-09", weight: 5,
              auto_rollback: {judge_win_rate_min: 0.48, p95_ttft_ms_max: 1500, schema_fail_rate_max: 0.01}}
```

What to compare: golden-set pass rate, judge preference on sampled live traffic, JSON validity and tool-call correctness, refusal and safety-trigger rate, p95 TTFT and TPOT, tokens per task (a new model can be more verbose, which is a cost change), and cache behavior, since a new model starts with a cold cache. Self-hosted, the canary is a second deployment behind weighted routing at the gateway or through a rollout controller, which means both models need GPU capacity at once. For hosted models, weights live in the gateway config and can differ per tenant or feature, so an enterprise tenant can stay pinned. Rollback must be one config flip.

**Follow-ups they will ask:**
- How long does a canary run: through full traffic cycles and rare slices, usually days, not minutes.
- What forces the upgrade: provider deprecation dates, so start the canary well before them.
- How do you judge quality on live traffic without labels: pairwise judge on a sample, user feedback signals, and task-completion metrics.

**Mistakes to avoid:**
- Switching an alias and hoping.
- Evaluating latency and cost but not quality or refusal behavior.

### Q. Which metrics go on the inference dashboard, and what does each one tell you to do?
**Short answer (45 seconds):** Latency: TTFT, TPOT and end-to-end at p50, p95 and p99, split by model and prompt-length bucket. Queue: time waiting before prefill and the count of waiting requests. Throughput: tokens per second in and out, requests per second. Engine health: KV cache usage, preemptions, prefix cache hit rate, GPU utilization and memory. Errors: rate by class (429, 5xx, timeouts, content filter, schema failures) and fallback usage. Cost: tokens and cost per request and per feature.

**Deeper explanation:**

| Metric | What it tells you | Typical action |
| --- | --- | --- |
| TTFT p95 by prompt length | prefill cost plus queueing | shorter prompts, prefix caching, chunked prefill, scale out |
| TPOT p95 | decode step time | lower concurrency cap, quantize, smaller model, tensor parallelism |
| queue time, waiting requests | demand above capacity | scale out, shed batch traffic |
| KV cache usage | memory headroom | KV quantization, shorter max length, more replicas |
| preemptions | memory thrashing | same as above, urgently |
| prefix cache hit rate | prompt layout and routing quality | fix prompt order, affinity routing |
| error rate by class, fallback used | upstream health | breakers, limits, capacity |

vLLM exposes these at `/metrics` with names such as `vllm:time_to_first_token_seconds`, `vllm:time_per_output_token_seconds`, `vllm:num_requests_waiting` and the KV cache usage gauge; exact names vary by version, so read them from the endpoint. Alerts: p95 TTFT above SLO for five minutes, waiting requests above the load-test threshold, KV usage above 90%, sustained preemptions, error rate above a few percent, and tokens per task jumping for one feature.

**Follow-ups they will ask:**
- Why split by prompt length: TTFT scales with prompt length, so a mixed p95 is uninterpretable.
- One metric if you could keep only one: p95 TTFT for interactive products, tokens per GPU-hour for cost.

**Mistakes to avoid:**
- Averages instead of percentiles.
- GPU utilization as the health metric; it hides memory-bound saturation.

### Q. How do you trace one user request across the Node gateway, the Python router and vLLM?
**Short answer (45 seconds):** OpenTelemetry end to end. The gateway starts a trace, or continues the client's `traceparent`, and creates spans for auth, admission, cache lookup and routing, then propagates the W3C `traceparent` header to the router. The router adds spans for classification, model selection, budget checks and the upstream call, with attributes for model, prompt version, input and output tokens, cache hit, fallback used and the provider's request ID. vLLM can export its own spans when started with an OTLP endpoint, so engine-side queue time, prefill and decode appear in the same trace. Logs carry the trace ID, so a slow request can be explained from the click to the GPU.

**Deeper explanation:**

```text
trace 7f3a...
 gateway POST /v1/chat                 420 ms   tenant=acme feature=summarize
   admission                             2 ms   class=interactive
   cache.lookup                          3 ms   hit=false
   router.route                         12 ms   model=small-8b reason=short_prompt
     engine.request                    400 ms   queue=35ms prefill=120ms decode=245ms in=1200 out=180
   stream.to_client                   (overlaps decode)   ttft event at +170 ms
```

In Node, `@opentelemetry/sdk-node` with HTTP and Express auto-instrumentation handles propagation; wrap the model call in a custom span and use the GenAI semantic convention attributes (`gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`). In Python, the FastAPI instrumentation extracts the incoming context and the SDK injects it into outgoing requests. Start vLLM with `--otlp-traces-endpoint` pointing at your collector. Record TTFT as a span event and end the span at the last token. Put the provider request ID on the span for support tickets. Sample head-based at a low rate and tail-sample slow or failed traces so the interesting ones are always kept. Keep prompt content out of spans: store a prompt hash and version, and keep content in an access-controlled store if you need it at all.

**Follow-ups they will ask:**
- How do you correlate a user complaint: return the trace ID in a response header and search by it.
- Why not just logs: logs do not show the causal structure or the overlap between streaming and decode; traces do.

**Mistakes to avoid:**
- Logging full prompts and completions into traces.
- Starting a new trace at every hop so nothing joins up.

### Practice
- Implement the four-timer streaming client in Node, inject faults with a proxy (delays, a stall after three tokens, bursts of 429s) and verify each path, including the retry budget.
- Build a Grafana dashboard from a vLLM `/metrics` scrape with TTFT, TPOT, waiting requests, KV usage and preemptions, then load test until each alert has fired once.
- Wire OpenTelemetry through a Node gateway and a FastAPI router, find a slow request in the trace view and name the slow span.
- Say it out loud: describe your fallback chain and circuit breaker in 60 seconds, including how and how often you test it.

## Project Blueprint: Inference Router

> Interviewers love a small system you can draw and defend in ten minutes, and an inference router is ideal: it touches classification, model choice, budgets, caching, streaming, fallback and metrics, and every decision has a trade-off you can argue. Present it as something you could build in a week with Node or FastAPI in front of a hosted API and one vLLM replica, draw the pipeline, and let the interviewer pull on any thread. The strong candidate names the data stores, the failure modes and the one metric that proves each decision was right.

### Concepts you must understand
- The router is a thin, stateless service between product code and models: one OpenAI-compatible endpoint in, several upstreams out, with policy in versioned configuration rather than in callers.
- Classification is cheap and explainable first (feature tag, prompt length, schema or tools present, tenant tier), with a small classifier only where heuristics fail to separate easy from hard.
- Model selection is a policy table keyed by feature and class, with pinned model versions, an eval that justified each row and a fallback chain per entry.
- Budgets are enforced before the call by reserving estimated tokens against tenant and feature allowances, then reconciled with actual usage afterwards; limits return 429 with Retry-After.
- Caching sits in two places: an exact-match response cache in Redis keyed on the normalized request, and a prompt layout the adapter enforces so the provider or engine prefix cache stays hot.
- Streaming passes tokens through as SSE with phase timeouts; fallback happens before the first token or at a step boundary, never by splicing another model's text into a live stream.
- Every request emits metrics and a trace labeled with feature, tenant, model, route reason, cache status and fallback flag, which makes cost per task and quality per route observable.

### Q. Describe the overall architecture of your inference router in two minutes.
**Short answer (45 seconds):** It is a stateless service, Node or FastAPI, exposing one OpenAI-compatible chat endpoint. Per request: authenticate and tag tenant and feature; classify; check the response cache; pick the model from a policy table; reserve budget and check rate limits; build the provider-specific request through an adapter that enforces a cacheable prompt layout; stream the response while recording usage; on a failure before the first token, fall back down the chain; emit metrics and a trace. Shared state lives in Redis (buckets, caches, breaker state) and Postgres (usage log, policy versions, eval results). Upstreams are hosted providers and one or more vLLM replicas behind the same adapter interface.

**Deeper explanation:**

```text
client -> [auth: tenant, feature] -> [classify] -> [response cache?] -> [select model: policy table]
       -> [reserve budget, rate limit] -> [adapter: build request, prompt layout] -> [stream, record usage]
       -> failure before first token: next model in the fallback chain
       -> [metrics, trace, usage log, reconcile budget]
state:     Redis (token buckets, response cache, breakers)    Postgres (usage, policies, evals)
upstreams: hosted provider A, hosted provider B, vLLM small model (OpenAI-compatible)
```

Stateless means horizontal scaling and trivial deploys; anything shared goes to Redis. One endpoint means callers never change when models do. The router scales on CPU and requests per second because it does no heavy work; the vLLM pool scales separately on queue depth. The router must be the most boring component in the system: no embeddings in the hot path unless a feature opts into semantic caching.

**Follow-ups they will ask:**
- Why not an off-the-shelf gateway: a reasonable choice in production; the blueprint explains exactly what you would be configuring and where its limits are.
- Who owns prompt templates: callers own content, the router owns transport, policy and layout rules, with templates versioned in a shared registry.

**Mistakes to avoid:**
- Making the router stateful or heavy, so it becomes the component that fails.
- Drawing boxes without naming the data stores, the failure boundaries and the metrics.

### Q. How does the router classify a request and pick a model?
**Short answer (45 seconds):** Classification starts with what the caller already knows: a feature tag on every request, plus cheap signals such as prompt token count, whether a JSON schema or tools are present, requested max_tokens, tenant tier and a priority hint. A small classifier trained on eval outcomes is added only for a feature where heuristics cannot separate easy from hard. Selection is a policy table keyed by feature and class: each row names a pinned model, its settings, a fallback chain and the eval that justified it. Every response carries a route reason, so any decision is explainable after the fact.

**Deeper explanation:**

```yaml
policies:
  support_reply:
    default:      {model: "large-2026-05", max_tokens: 600, fallbacks: ["large-alt-2026-05", "small-8b"]}
    short_simple: {when: "tokens_in < 800 and not tools", model: "small-8b", fallbacks: ["large-2026-05"]}
  extract_invoice:
    default:      {model: "small-8b", schema: true, verify: "schema and totals", escalate_to: "large-2026-05"}
```

Extraction uses a cascade: run the small model, validate (schema plus a domain check such as line items summing to the total), escalate on failure, and log the escalation rate as a quality signal. Regulated features are pinned to the large model and tenants can override. The policy table changes only with an eval report attached, and route-level quality is tracked by sampled judge comparisons against the large model. Letting the LLM pick the model is avoided because it adds a call and latency when heuristics are free and good enough for most traffic.

**Follow-ups they will ask:**
- How do misroutes get caught: a confidence margin that defaults to the large model, plus escalation on validator failure, plus the nightly quality sample.
- What is the policy for a brand-new feature: the large model by default, downgraded only after an eval shows the small model holds the bar.
- What signals would you add later: conversation length, prior escalations in the same session, and per-tenant difficulty history.

**Mistakes to avoid:**
- A classifier nobody can explain to the product owner.
- Changing a route because it is cheaper, without eval evidence that quality holds.

### Q. How do you enforce per-tenant budgets and rate limits in the router?
**Short answer (45 seconds):** Before the call, estimate the request's tokens from the tokenizer count plus max_tokens, then atomically check and reserve against the tenant's token bucket (tokens and requests per minute) and monthly budget in Redis. If the reservation fails, return 429 with Retry-After and the remaining allowance in headers. After the call, reconcile: refund the unused reserve and add the real cost to the monthly counter. Budgets have two levels, soft limits that alert and downgrade the model and hard limits that block, and everything is tagged by tenant and feature so finance and abuse detection read the same numbers.

**Deeper explanation:**

```js
// reserve before the call, reconcile after; both atomic in Redis (Lua script behind reserve())
const est = countTokens(req.messages) + (req.maxTokens ?? policy.maxTokens);
const r = await limiter.reserve({ tenant, feature, tokens: est });          // token bucket + monthly cap
if (!r.ok) return res.status(429).set("Retry-After", r.retryAfterSec).json({ error: "budget_exceeded" });
try {
  const out = await route(req);                                             // streams to client
  await limiter.reconcile(r.id, out.usage.input_tokens + out.usage.output_tokens, costOf(out));
} catch (e) { await limiter.release(r.id); throw e; }
```

The token bucket is a Lua script so check-and-deduct is one atomic step across all router replicas. Monthly spend is a counter per tenant and month with a soft threshold (alert and switch the policy to a cheaper row) and a hard threshold (block with a clear error code). A per-trace cap on steps and tokens stops runaway agent loops regardless of tenant budget. Interactive and batch classes draw from separate allowances so background jobs cannot starve users. If the client disconnects mid-stream, record the tokens actually generated before releasing the reservation.

**Follow-ups they will ask:**
- Many router replicas: Redis is the single source of truth and the Lua script makes the reservation atomic.
- Redis down: fail open with local approximate limits for trusted tenants and fail closed for untrusted ones, and alert either way.

**Mistakes to avoid:**
- Checking budgets after the model call.
- Read-then-write counters that over-admit under concurrency.

### Q. Where does caching sit in the router, and what exactly is the cache key?
**Short answer (45 seconds):** Two caches with different jobs. The exact-match response cache sits after classification and before model selection; its key is a hash of the normalized request: policy and prompt version, model version, tenant, messages, sorted tool definitions, response schema and sampling parameters. The value is the completed response plus usage, with a TTL per feature, stored only for features flagged cacheable and only for successful, complete responses. The second cache is not stored by the router at all: it is the prompt layout the adapter enforces, static blocks first with breakpoints where the provider needs them, so the provider or engine prefix cache hits. Semantic caching is a per-feature opt-in behind the response cache with tenant scoping and an audit sample.

**Deeper explanation:**

```js
function cacheKey(req, policy) {
  const norm = {
    pv: policy.promptVersion, mv: policy.modelVersion, tenant: req.tenantId,
    messages: req.messages, tools: sortTools(req.tools), schema: req.responseSchema,
    temperature: req.temperature ?? 1, maxTokens: req.maxTokens,
  };
  return "resp:v2:" + sha256(stableStringify(norm));
}
// on hit: replay the stored text as SSE chunks, set x-cache: HIT, mark usage.cached = true
// on miss: SET NX an in-flight marker so concurrent identical requests wait for the first result
```

Invalidation is built into the key: bump the prompt or model version and old entries miss and expire; bump the `resp:v2` prefix in an emergency. The adapter's layout rule is enforced, not hoped for: a lint rejects timestamps or user names in the static block, and the router logs provider cache-read tokens per call so the layout's effect is visible on the dashboard.

**Follow-ups they will ask:**
- Streaming responses: assemble at completion, store, and replay as a stream so the client contract is unchanged.
- Personalized system prompts: put the user-specific part after the static block and scope the response key by user or exclude the feature.

**Mistakes to avoid:**
- Looking up the cache before tenant scoping is known.
- A key without the prompt and model versions, which serves stale answers after a deploy.

### Q. How do you stream tokens back through the router and still handle fallback mid-request?
**Short answer (45 seconds):** The router opens the upstream stream and pipes normalized SSE events to the client as they arrive, under the four timers: connect, first token, idle gap and total. Fallback is decided at one boundary: if the primary fails before the first token, through a timeout, a 429 with no budget, a 5xx or an open breaker, the router retries on the next model in the chain and the client sees only extra latency. If the failure happens after tokens were sent, the router never splices another model's text into the stream; it sends an explicit error event and lets the client decide. The exception is structured output, where nothing has been shown yet, so the router discards the partial output and restarts on the fallback. Usage and route metadata go out as a final event.

**Deeper explanation:**

```js
async function handle(req, res) {
  res.setHeader("Content-Type", "text/event-stream"); res.flushHeaders();
  let sent = false;
  for (const target of fallbackChain(req)) {
    try {
      for await (const ev of openStream(target, req)) {        // adapter normalizes provider events
        if (!sent) { markTTFT(req); sent = true; }
        res.write(`data: ${JSON.stringify(ev)}\n\n`);
      }
      return finish(res, target);                               // final event: usage, model, route reason
    } catch (err) {
      if (!sent && retryable(err)) { recordFallback(req, target, err); continue; }
      return failStream(res, err);                              // explicit error event, never splice
    }
  }
}
```

The adapter converts each provider's event shapes into one schema: text delta, tool-call argument delta, finish reason, usage. Send a comment heartbeat every few seconds so proxies do not close idle streams, and abort the upstream when the client disconnects so the engine frees the sequence.

**Follow-ups they will ask:**
- How does TTFT stay within SLO with a chain: the first-token timeout must leave room for the fallback's own TTFT; hedged requests to a secondary after a delay are an option at extra cost.
- Tool-call deltas: passed through as partial JSON argument fragments; the caller assembles and validates them.

**Mistakes to avoid:**
- Splicing two models' outputs into one stream.

### Q. What metrics and tests prove the router works?
**Short answer (45 seconds):** Metrics per request, labeled by feature, tenant, model, route reason, cache status and fallback flag: TTFT, TPOT, end-to-end latency, tokens in and out, cost, errors by class, admission rejections and breaker state. From those come cost per successful task per feature, cache hit rate and savings, fallback rate and 429 rate. Tests: unit tests for the policy table and key normalization; contract tests running a golden prompt set through every adapter and comparing schema adherence and tool-call shape; fault injection through a proxy that stalls, times out and returns 429s to prove timeouts and fallback; a load test to find the knee and verify admission control; and a nightly eval that re-scores a sample of routed traffic against the large model to catch quality drift.

**Deeper explanation:**

```text
illustrative SLOs:  p95 TTFT under 1.5 s for interactive features; availability 99.9% including fallbacks;
                    fallback rate under 2%; schema failures under 0.5%; cache read ratio above 60% for chat
dashboard rows:     SLOs -> route mix per feature -> per-tenant usage and 429s -> breakers and fallbacks -> cost per task
test ladder:        unit (policy, keys) -> contract (adapters, golden set) -> fault injection (stall, 429, 5xx)
                    -> load (knee, admission) -> nightly quality eval (route versus large model)
```

Run a game day in staging: revoke the primary provider key for ten minutes and check the fallback rate, user-visible errors and alert timing. Canary the router itself with the same discipline as models. Concurrency correctness for budgets gets its own test: 200 simultaneous requests against a bucket of 100 must admit exactly 100.

**Follow-ups they will ask:**
- One number for the weekly report: cost per successful task per feature next to that feature's quality score.
- How do you catch prompt layout regressions: a CI test asserting that the second identical call shows provider cache reads above zero.

**Mistakes to avoid:**
- Testing only happy paths against a mocked model.
- Metrics without feature and route labels, which makes cost attribution and route quality impossible to see.

### Practice
- Build the router skeleton in Node or FastAPI with one hosted upstream and one local Ollama upstream, the policy table and streaming pass-through; measure the TTFT overhead the router itself adds.
- Add the Redis reserve-and-reconcile budget with a Lua script and prove atomicity with 200 concurrent requests against a bucket of 100.
- Inject failures with a proxy and verify fallback before the first token, an explicit error after the first token, and breaker open and half-open transitions.
- Say it out loud: present the whole router in two minutes from the diagram, then defend one decision, the cache key or the fallback boundary, for one more minute.
