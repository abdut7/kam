## Inference Engineering Levels

### Diagram: The three levels of inference engineering

```svg
<svg viewBox="0 0 760 250" role="img" aria-label="Three ascending levels. Level 1, AI infrastructure: cloud, Kubernetes, GPUs, running models and APIs; next step is deploying a model yourself. Level 2, understanding inference: transformer, prefill and decode, KV cache, engines such as vLLM, SGLang and TensorRT-LLM, serving patterns; next step is experimenting on a GPU. Level 3, optimizing inference: measuring TTFT, inter-token latency and throughput, continuous batching, chunked prefill, speculative decoding, quantization, distillation and parallelism; stay sharp with a benchmarking project.">
<defs>
<marker id="i1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<rect class="bx" x="20" y="150" width="230" height="86" rx="10"/>
<text class="tb" x="34" y="172">Level 1: AI infrastructure</text>
<text class="tm" x="34" y="192">cloud, Kubernetes, GPU nodes,</text>
<text class="tm" x="34" y="207">running models and LLM APIs</text>
<text class="ta" x="34" y="226">next: deploy a model yourself</text>
<rect class="bxa" x="265" y="95" width="230" height="141" rx="10"/>
<text class="tb" x="279" y="117">Level 2: understand inference</text>
<text class="tm" x="279" y="137">transformer, prefill and decode,</text>
<text class="tm" x="279" y="152">KV cache memory management,</text>
<text class="tm" x="279" y="167">vLLM, SGLang, TensorRT-LLM,</text>
<text class="tm" x="279" y="182">aggregated vs disaggregated</text>
<text class="ta" x="279" y="226">next: experiment on a GPU</text>
<rect class="bxo" x="510" y="40" width="230" height="196" rx="10"/>
<text class="tb" x="524" y="62">Level 3: optimize inference</text>
<text class="tm" x="524" y="82">measure TTFT, inter-token</text>
<text class="tm" x="524" y="97">latency, throughput, GPU use</text>
<text class="tm" x="524" y="117">continuous batching,</text>
<text class="tm" x="524" y="132">chunked prefill,</text>
<text class="tm" x="524" y="147">speculative decoding</text>
<text class="tm" x="524" y="167">quantization, distillation,</text>
<text class="tm" x="524" y="182">parallelism</text>
<text class="to" x="524" y="226">stay sharp: benchmark often</text>
<line class="ln" x1="250" y1="166" x2="263" y2="150" marker-end="url(#i1k)"/>
<line class="ln" x1="495" y1="111" x2="508" y2="95" marker-end="url(#i1k)"/>
</svg>
```

Each step up builds on the one below. Level 1 is running models, level 2 is knowing what happens inside the server, and level 3 is making it faster and cheaper with measurements. Most application engineers stand on level 1; interviews for AI infrastructure roles probe levels 2 and 3.

### Diagram: One GPU, one user, then fifty: each problem and its fix
before: Q. Walk me through what happens on one GPU

```svg
<svg viewBox="0 0 760 420" role="img" aria-label="Eight rows pairing a serving problem with the technique that fixes it: one user needs prefill then decode with a KV cache; fifty users each need a KV cache, solved by PagedAttention; short answers waiting for long ones, solved by continuous batching; a long pasted document stalling everyone, solved by chunked prefill; a repeated system prompt, solved by prefix caching; weights too large, solved by quantization; decode still slow, solved by speculative decoding; and proving it worked by measuring TTFT, inter-token latency and throughput.">
<defs>
<marker id="i2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<text class="tb" x="185" y="24" text-anchor="middle">the problem</text>
<text class="tb" x="565" y="24" text-anchor="middle">the technique that fixes it</text>
<rect class="bx2" x="20" y="40" width="330" height="36" rx="6"/><text class="t" x="34" y="63">1 user: read the prompt, reply token by token</text>
<rect class="bxa" x="390" y="40" width="350" height="36" rx="6"/><text class="t" x="404" y="63">prefill, then decode; KV cache keeps past work</text>
<line class="ln" x1="350" y1="58" x2="388" y2="58" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="86" width="330" height="36" rx="6"/><text class="t" x="34" y="109">50 users: each needs its own KV cache</text>
<rect class="bxa" x="390" y="86" width="350" height="36" rx="6"/><text class="t" x="404" y="109">PagedAttention: small cache blocks on demand</text>
<line class="ln" x1="350" y1="104" x2="388" y2="104" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="132" width="330" height="36" rx="6"/><text class="t" x="34" y="155">short answers wait for the longest one</text>
<rect class="bxa" x="390" y="132" width="350" height="36" rx="6"/><text class="t" x="404" y="155">continuous batching: join and leave every step</text>
<line class="ln" x1="350" y1="150" x2="388" y2="150" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="178" width="330" height="36" rx="6"/><text class="t" x="34" y="201">a long pasted document stalls everyone</text>
<rect class="bxa" x="390" y="178" width="350" height="36" rx="6"/><text class="t" x="404" y="201">chunked prefill: process the prompt in slices</text>
<line class="ln" x1="350" y1="196" x2="388" y2="196" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="224" width="330" height="36" rx="6"/><text class="t" x="34" y="247">every request repeats the system prompt</text>
<rect class="bxa" x="390" y="224" width="350" height="36" rx="6"/><text class="t" x="404" y="247">prefix caching: reuse an exactly matching start</text>
<line class="ln" x1="350" y1="242" x2="388" y2="242" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="270" width="330" height="36" rx="6"/><text class="t" x="34" y="293">the weights take too much memory</text>
<rect class="bxa" x="390" y="270" width="350" height="36" rx="6"/><text class="t" x="404" y="293">quantization: fewer bits per weight</text>
<line class="ln" x1="350" y1="288" x2="388" y2="288" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="316" width="330" height="36" rx="6"/><text class="t" x="34" y="339">generating the answer is still slow</text>
<rect class="bxa" x="390" y="316" width="350" height="36" rx="6"/><text class="t" x="404" y="339">speculative decoding: draft, then verify</text>
<line class="ln" x1="350" y1="334" x2="388" y2="334" marker-end="url(#i2k)"/>
<rect class="bx2" x="20" y="362" width="330" height="36" rx="6"/><text class="t" x="34" y="385">how do we know it got better?</text>
<rect class="bxo" x="390" y="362" width="350" height="36" rx="6"/><text class="t" x="404" y="385">measure TTFT, inter-token latency, throughput</text>
<line class="ln" x1="350" y1="380" x2="388" y2="380" marker-end="url(#i2k)"/>
</svg>
```

Read it top to bottom as one story. Each row is a new problem that appears as traffic grows, and the technique on the right is the standard fix. If you can tell this story in order, you can answer most inference interview questions.

### Diagram: The six-step lab, from GPU to agent
before: Q. How would you stand up

```svg
<svg viewBox="0 0 760 150" role="img" aria-label="Six steps in a row: create a GPU node on Kubernetes with Terraform, deploy vLLM serving a Qwen model, port-forward a tunnel to the pod, swap the base URL of an OpenAI-compatible client, load test while watching the KV cache and batching, then run an agent on your own inference.">
<defs>
<marker id="i4k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<rect class="bx" x="15" y="20" width="108" height="70" rx="8"/>
<text class="tb" x="25" y="42">1. GPU node</text><text class="tm" x="25" y="60">Terraform +</text><text class="tm" x="25" y="76">Kubernetes</text>
<rect class="bxa" x="137" y="20" width="108" height="70" rx="8"/>
<text class="tb" x="147" y="42">2. vLLM</text><text class="tm" x="147" y="60">serves a Qwen</text><text class="tm" x="147" y="76">model</text>
<rect class="bx" x="259" y="20" width="108" height="70" rx="8"/>
<text class="tb" x="269" y="42">3. tunnel</text><text class="tm" x="269" y="60">port-forward</text><text class="tm" x="269" y="76">to the pod</text>
<rect class="bx" x="381" y="20" width="108" height="70" rx="8"/>
<text class="tb" x="391" y="42">4. base URL</text><text class="tm" x="391" y="60">OpenAI client,</text><text class="tm" x="391" y="76">new endpoint</text>
<rect class="bxo" x="503" y="20" width="108" height="70" rx="8"/>
<text class="tb" x="513" y="42">5. load test</text><text class="tm" x="513" y="60">watch KV cache</text><text class="tm" x="513" y="76">and batching</text>
<rect class="bx" x="625" y="20" width="108" height="70" rx="8"/>
<text class="tb" x="635" y="42">6. agent</text><text class="tm" x="635" y="60">tools on your</text><text class="tm" x="635" y="76">own inference</text>
<line class="ln" x1="123" y1="55" x2="135" y2="55" marker-end="url(#i4k)"/>
<line class="ln" x1="245" y1="55" x2="257" y2="55" marker-end="url(#i4k)"/>
<line class="ln" x1="367" y1="55" x2="379" y2="55" marker-end="url(#i4k)"/>
<line class="ln" x1="489" y1="55" x2="501" y2="55" marker-end="url(#i4k)"/>
<line class="ln" x1="611" y1="55" x2="623" y2="55" marker-end="url(#i4k)"/>
<text class="tm" x="15" y="120">At step 5, record TTFT, inter-token latency, tokens per second and GPU utilization for each setting you change.</text>
<text class="tm" x="15" y="138">The GPU node is billed by the hour, so tear it down after each session.</text>
</svg>
```

Steps 1 to 4 replace a paid API with your own endpoint, without changing your application code beyond the base URL. Step 5 is where the learning happens: you watch the KV cache fill and batching kick in as load grows.

### Diagram: Aggregated versus disaggregated serving
before: Q. What is disaggregated

```svg
<svg viewBox="0 0 760 250" role="img" aria-label="Aggregated serving runs prefill and decode on the same GPU pool, so a long prefill delays every decode step. Disaggregated serving sends prompts to a prefill pool of compute-bound GPUs, transfers the KV cache, and generates tokens on a separate decode pool of memory-bound GPUs, so each pool can be scaled and tuned separately at the cost of moving the cache.">
<defs>
<marker id="i3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="i3a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tb" x="20" y="28">aggregated</text>
<rect class="bx" x="20" y="40" width="120" height="56" rx="8"/><text class="t" x="80" y="73" text-anchor="middle">requests</text>
<rect class="bx2" x="170" y="40" width="330" height="56" rx="8"/>
<text class="tb" x="335" y="63" text-anchor="middle">one GPU pool</text>
<text class="tm" x="335" y="81" text-anchor="middle">prefill and decode share every step</text>
<rect class="bx" x="530" y="40" width="210" height="56" rx="8"/><text class="t" x="635" y="73" text-anchor="middle">tokens</text>
<line class="ln" x1="140" y1="68" x2="168" y2="68" marker-end="url(#i3k)"/>
<line class="ln" x1="500" y1="68" x2="528" y2="68" marker-end="url(#i3k)"/>
<text class="tm" x="335" y="114" text-anchor="middle">a long prefill delays everyone's next token</text>
<text class="tb" x="20" y="148">disaggregated</text>
<rect class="bx" x="20" y="160" width="120" height="56" rx="8"/><text class="t" x="80" y="193" text-anchor="middle">requests</text>
<rect class="bxa" x="170" y="160" width="170" height="56" rx="8"/>
<text class="tb" x="255" y="183" text-anchor="middle">prefill pool</text>
<text class="tm" x="255" y="201" text-anchor="middle">compute-bound</text>
<rect class="bxo" x="430" y="160" width="170" height="56" rx="8"/>
<text class="tb" x="515" y="183" text-anchor="middle">decode pool</text>
<text class="tm" x="515" y="201" text-anchor="middle">memory-bound</text>
<rect class="bx" x="630" y="160" width="110" height="56" rx="8"/><text class="t" x="685" y="193" text-anchor="middle">tokens</text>
<line class="ln" x1="140" y1="188" x2="168" y2="188" marker-end="url(#i3k)"/>
<line class="lna" x1="340" y1="188" x2="428" y2="188" marker-end="url(#i3a)"/>
<text class="ta" x="385" y="180" text-anchor="middle">KV cache</text>
<line class="ln" x1="600" y1="188" x2="628" y2="188" marker-end="url(#i3k)"/>
<text class="tm" x="20" y="240">Each pool scales and is tuned on its own; the price is moving the KV cache between GPUs over a fast link.</text>
</svg>
```

Prefill and decode want different hardware behaviour: prefill is a burst of compute, decode is a long stream of memory reads. Splitting them stops long prompts from causing stutter for users who are already streaming. The blue arrow is the new cost: shipping each request's KV cache across.

## Inference Fundamentals

### Diagram: One request, from arrival to the last token
before: Q. Walk me through what happens on the GPU

```svg
<svg viewBox="0 0 760 250" role="img" aria-label="Timeline of one request: it waits in the queue, then prefill processes the whole prompt, then decode produces tokens one per step. Time to first token runs from arrival to the first token. Inter-token latency is the gap between consecutive tokens. End-to-end latency runs from arrival to the last token.">
<defs>
<marker id="i5m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<line class="lna" x1="60" y1="40" x2="346" y2="40"/>
<line class="lna" x1="60" y1="34" x2="60" y2="46"/><line class="lna" x1="346" y1="34" x2="346" y2="46"/>
<text class="ta" x="203" y="32" text-anchor="middle">time to first token (TTFT)</text>
<rect class="bx2" x="60" y="62" width="80" height="36" rx="5"/><text class="t" x="100" y="85" text-anchor="middle">queue</text>
<rect class="bxa" x="140" y="62" width="160" height="36" rx="5"/><text class="t" x="220" y="85" text-anchor="middle">prefill: whole prompt</text>
<rect class="bxo" x="306" y="62" width="40" height="36" rx="5"/><text class="tm" x="326" y="85" text-anchor="middle">t1</text>
<rect class="bxo" x="352" y="62" width="40" height="36" rx="5"/><text class="tm" x="372" y="85" text-anchor="middle">t2</text>
<rect class="bxo" x="398" y="62" width="40" height="36" rx="5"/><text class="tm" x="418" y="85" text-anchor="middle">t3</text>
<rect class="bxo" x="444" y="62" width="40" height="36" rx="5"/><text class="tm" x="464" y="85" text-anchor="middle">t4</text>
<rect class="bxo" x="490" y="62" width="40" height="36" rx="5"/><text class="tm" x="510" y="85" text-anchor="middle">t5</text>
<rect class="bxo" x="536" y="62" width="40" height="36" rx="5"/><text class="tm" x="556" y="85" text-anchor="middle">t6</text>
<rect class="bxo" x="582" y="62" width="40" height="36" rx="5"/><text class="tm" x="602" y="85" text-anchor="middle">t7</text>
<rect class="bxo" x="628" y="62" width="40" height="36" rx="5"/><text class="tm" x="648" y="85" text-anchor="middle">t8</text>
<line class="lno" x1="352" y1="114" x2="398" y2="114"/>
<line class="lno" x1="352" y1="108" x2="352" y2="120"/><line class="lno" x1="398" y1="108" x2="398" y2="120"/>
<text class="to" x="406" y="118">inter-token latency: one decode step</text>
<line class="ln" x1="60" y1="142" x2="668" y2="142"/>
<line class="ln" x1="60" y1="136" x2="60" y2="148"/><line class="ln" x1="668" y1="136" x2="668" y2="148"/>
<text class="tb" x="364" y="164" text-anchor="middle">end-to-end latency</text>
<line class="lnm" x1="60" y1="182" x2="712" y2="182" marker-end="url(#i5m)"/>
<text class="tm" x="60" y="200">arrives</text>
<text class="tm" x="306" y="200">first token streams</text>
<text class="tm" x="668" y="200" text-anchor="middle">last token</text>
<text class="tm" x="20" y="232">TPOT = (end-to-end latency - TTFT) / (output tokens - 1). Chat products watch TTFT; batch jobs watch total throughput.</text>
</svg>
```

TTFT (blue) covers queueing and prefill, which is why long prompts and busy servers both hurt it. After that, each green box is one decode step, and the gap between them is what users feel as streaming speed.

### Diagram: Why decode is limited by memory, and why batching helps
before: Q. Why is the decode phase

```svg
<svg viewBox="0 0 760 240" role="img" aria-label="In every decode step the GPU must read all model weights from its high-bandwidth memory into the compute units. With batch size 1 that whole read produces one token, so the compute units sit mostly idle. With batch size 32 the same single read of the weights produces 32 tokens, one per user, so the cost of the read is shared.">
<defs>
<marker id="i6a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
<marker id="i6o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mko"/></marker>
</defs>
<rect class="bx2" x="20" y="30" width="220" height="170" rx="10"/>
<text class="tb" x="34" y="52">GPU memory (HBM)</text>
<rect class="bxw" x="34" y="64" width="192" height="80" rx="6"/>
<text class="t" x="130" y="102" text-anchor="middle">all model weights</text>
<text class="tm" x="130" y="120" text-anchor="middle">read again every step</text>
<rect class="bxa" x="34" y="152" width="192" height="36" rx="6"/>
<text class="t" x="130" y="175" text-anchor="middle">KV cache</text>
<rect class="bx" x="520" y="60" width="220" height="110" rx="10"/>
<text class="tb" x="534" y="84">compute units (SMs)</text>
<text class="tm" x="534" y="106">very fast at math;</text>
<text class="tm" x="534" y="122">starved at batch 1 because</text>
<text class="tm" x="534" y="138">data arrives slower than</text>
<text class="tm" x="534" y="154">they can use it</text>
<line class="lna" x1="240" y1="96" x2="518" y2="96" marker-end="url(#i6a)"/>
<text class="ta" x="380" y="88" text-anchor="middle">batch 1: read all weights, get 1 token</text>
<line class="lno" x1="240" y1="146" x2="518" y2="146" marker-end="url(#i6o)"/>
<text class="to" x="380" y="138" text-anchor="middle">batch 32: same read, 32 tokens out</text>
<text class="tm" x="20" y="226">Rule of thumb for one stream: decode tokens per second is about memory bandwidth divided by bytes read per step.</text>
</svg>
```

Each decode step produces one token per request but must stream every weight through the chip. At batch size 1 the math units wait on memory. Batching many users into the same step shares that one expensive read, which is why throughput rises with batch size until memory or latency targets stop you.

### Diagram: A GPU memory budget, worked through
before: Q. How do you build a GPU memory budget

```svg
<svg viewBox="0 0 760 230" role="img" aria-label="Illustrative memory budget for an 8 billion parameter model in BF16 on a 24 GB GPU: about 16 GB of weights, about 2 GB for the runtime and activations, and about 6 GB left for the KV cache. With 128 KiB of KV cache per token for Llama 3 8B, 6 GB holds about 49 thousand tokens, or about six 8k-token conversations at once.">
<text class="tb" x="20" y="24">Illustrative: an 8B model in BF16 on a 24 GB GPU</text>
<rect class="bxw" x="20" y="40" width="480" height="48" rx="4"/>
<text class="t" x="260" y="60" text-anchor="middle">weights: 8B parameters x 2 bytes</text>
<text class="tm" x="260" y="77" text-anchor="middle">about 16 GB</text>
<rect class="bx2" x="500" y="40" width="60" height="48" rx="4"/>
<text class="tm" x="530" y="60" text-anchor="middle">runtime</text>
<text class="tm" x="530" y="77" text-anchor="middle">~2 GB</text>
<rect class="bxa" x="560" y="40" width="180" height="48" rx="4"/>
<text class="t" x="650" y="60" text-anchor="middle">KV cache</text>
<text class="tm" x="650" y="77" text-anchor="middle">about 6 GB left</text>
<text class="tm" x="20" y="104">0</text>
<text class="tm" x="740" y="104" text-anchor="end">24 GB</text>
<text class="tmono" x="20" y="138">KV bytes per token = 2 x layers x kv_heads x head_dim x bytes per value</text>
<text class="tmono" x="20" y="160">Llama 3 8B:  2 x 32 x 8 x 128 x 2 = 131,072 bytes = 128 KiB per token</text>
<text class="tmono" x="20" y="182">6 GiB / 128 KiB = 49,152 tokens = six 8,192-token conversations</text>
<text class="tm" x="20" y="214">The KV cache, not the weights, decides how many users fit at once. Quantizing weights or the cache frees room for more.</text>
</svg>
```

Start from the card size, subtract the weights and a runtime reserve, and what remains is KV cache. Divide it by the per-token cache size and you know how many tokens, and so how many concurrent conversations, the GPU can hold.

### Diagram: Batch size trades per-user speed for total throughput
before: Q. Explain the throughput versus latency

```svg
<svg viewBox="0 0 760 260" role="img" aria-label="Qualitative chart. As batch size grows, total tokens per second across all users rises steeply and then flattens, while tokens per second for each individual user falls. A knee marks where total throughput is high and per-user speed is still acceptable, a good place for interactive chat traffic; batch jobs run further right.">
<line class="ln" x1="70" y1="210" x2="700" y2="210"/>
<line class="ln" x1="70" y1="210" x2="70" y2="30"/>
<path class="lno" d="M70,200 C200,90 330,60 700,52"/>
<path class="lna" d="M70,60 C250,90 400,140 700,170"/>
<line class="lnm dash" x1="300" y1="40" x2="300" y2="210"/>
<text class="tm" x="306" y="40">knee: run chat traffic here</text>
<text class="to" x="696" y="44" text-anchor="end">total tokens/s across all users</text>
<text class="ta" x="696" y="190" text-anchor="end">tokens/s for each user</text>
<text class="tm" x="560" y="232" text-anchor="middle">batch jobs live out here</text>
<text class="tm" x="385" y="250" text-anchor="middle">batch size (concurrent requests)</text>
<text class="tm" x="40" y="120" text-anchor="middle" transform="rotate(-90 40 120)">tokens per second</text>
<text class="tm" x="740" y="20" text-anchor="end">shape only, no real numbers</text>
</svg>
```

More concurrent requests per step means more total tokens per second (green), but each user's stream gets slower (blue). Pick the batch size from your latency target. Interactive chat sits near the knee, and offline jobs push far to the right.
