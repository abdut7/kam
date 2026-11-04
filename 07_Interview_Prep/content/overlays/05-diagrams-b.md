## Serving Engines & Stacks

### Diagram: Inside a serving engine such as vLLM

```svg
<svg viewBox="0 0 760 290" role="img" aria-label="Inside a serving engine. A client calls the OpenAI-compatible API server, which tokenizes the request and hands it to the scheduler. Each step the scheduler moves requests from waiting to running and the model runner does one forward pass on the GPU for the whole batch, reading and writing KV cache blocks managed by the KV cache manager. The sampler picks one token per request using temperature and top-p, the token is appended and the request is scheduled again, and the detokenizer turns token IDs into text that streams back to the client.">
<defs>
<marker id="s1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="s1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<rect class="bx" x="15" y="40" width="150" height="56" rx="8"/>
<text class="tb" x="28" y="63">client</text><text class="tm" x="28" y="82">POST /v1/chat/...</text>
<rect class="bx" x="200" y="40" width="150" height="56" rx="8"/>
<text class="tb" x="213" y="63">API server</text><text class="tm" x="213" y="82">OpenAI-compatible</text>
<rect class="bxa" x="385" y="40" width="150" height="56" rx="8"/>
<text class="tb" x="398" y="63">scheduler</text><text class="tm" x="398" y="82">waiting to running</text>
<rect class="bxo" x="570" y="40" width="150" height="56" rx="8"/>
<text class="tb" x="583" y="63">model runner</text><text class="tm" x="583" y="82">GPU forward pass</text>
<line class="ln" x1="165" y1="68" x2="198" y2="68" marker-end="url(#s1k)"/>
<line class="ln" x1="350" y1="68" x2="383" y2="68" marker-end="url(#s1k)"/>
<line class="ln" x1="535" y1="68" x2="568" y2="68" marker-end="url(#s1k)"/>
<rect class="bxo" x="15" y="190" width="150" height="56" rx="8"/>
<text class="tb" x="28" y="213">stream</text><text class="tm" x="28" y="232">SSE back to the client</text>
<rect class="bx" x="200" y="190" width="150" height="56" rx="8"/>
<text class="tb" x="213" y="213">detokenizer</text><text class="tm" x="213" y="232">token IDs to text</text>
<rect class="bx" x="385" y="190" width="150" height="56" rx="8"/>
<text class="tb" x="398" y="213">sampler</text><text class="tm" x="398" y="232">temperature, top-p</text>
<rect class="bxw" x="570" y="190" width="150" height="56" rx="8"/>
<text class="tb" x="583" y="213">KV cache manager</text><text class="tm" x="583" y="232">block table</text>
<line class="ln" x1="680" y1="98" x2="680" y2="188" marker-start="url(#s1k)" marker-end="url(#s1k)"/>
<text class="tm" x="688" y="150">KV blocks</text>
<line class="ln" x1="590" y1="96" x2="522" y2="188" marker-end="url(#s1k)"/>
<text class="tm" x="566" y="136">logits</text>
<line class="ln" x1="385" y1="218" x2="352" y2="218" marker-end="url(#s1k)"/>
<line class="ln" x1="200" y1="218" x2="167" y2="218" marker-end="url(#s1k)"/>
<path class="lna" d="M430,190 V98" marker-end="url(#s1a)"/>
<text class="ta" x="422" y="150" text-anchor="end">next step</text>
<text class="tm" x="15" y="278">Every step: the scheduler picks which requests run, the GPU does one forward pass for all of them, and each gets one new token.</text>
</svg>
```

The engine is a loop, not a straight line. The blue arrow is the heart of it: after the sampler picks a token, the request goes back to the scheduler for the next step, together with every other running request. The KV cache manager decides where each request's cache lives on the GPU.

### Diagram: Static batching versus continuous batching
before: Q. What is continuous batching

```svg
<svg viewBox="0 0 760 290" role="img" aria-label="Four GPU slots over sixteen decode steps. With static batching, requests A, B, C and D start together and the slots of A, C and D sit idle until the longest request B finishes at step 12; only then can E and F start. With continuous batching, a freed slot is refilled at the next step: E starts when A finishes, F when C finishes, then G, H, I and J, so no slot sits idle.">
<defs>
<marker id="s2m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<text class="tb" x="20" y="26">static batching: the batch waits for its longest request</text>
<text class="tm" x="20" y="54">slot 1</text><text class="tm" x="20" y="78">slot 2</text><text class="tm" x="20" y="102">slot 3</text><text class="tm" x="20" y="126">slot 4</text>
<rect class="bxa" x="120" y="40" width="192" height="20" rx="3"/><text class="tm" x="128" y="54">A</text>
<rect class="bx2 dash" x="312" y="40" width="192" height="20" rx="3"/><text class="tm" x="408" y="54" text-anchor="middle">idle</text>
<rect class="bxo" x="504" y="40" width="96" height="20" rx="3"/><text class="tm" x="512" y="54">E</text>
<rect class="bxa" x="120" y="64" width="384" height="20" rx="3"/><text class="tm" x="128" y="78">B</text>
<rect class="bxo" x="504" y="64" width="128" height="20" rx="3"/><text class="tm" x="512" y="78">F</text>
<rect class="bxa" x="120" y="88" width="128" height="20" rx="3"/><text class="tm" x="128" y="102">C</text>
<rect class="bx2 dash" x="248" y="88" width="256" height="20" rx="3"/><text class="tm" x="376" y="102" text-anchor="middle">idle</text>
<rect class="bxa" x="120" y="112" width="288" height="20" rx="3"/><text class="tm" x="128" y="126">D</text>
<rect class="bx2 dash" x="408" y="112" width="96" height="20" rx="3"/><text class="tm" x="456" y="126" text-anchor="middle">idle</text>
<line class="lnm dash" x1="504" y1="34" x2="504" y2="138"/>
<text class="tm" x="648" y="54">batch ends at B;</text>
<text class="tm" x="648" y="70">E and F waited</text>
<text class="tm" x="648" y="86">the whole time</text>
<text class="tb" x="20" y="164">continuous batching: a freed slot is refilled at the next step</text>
<text class="tm" x="20" y="192">slot 1</text><text class="tm" x="20" y="216">slot 2</text><text class="tm" x="20" y="240">slot 3</text><text class="tm" x="20" y="264">slot 4</text>
<rect class="bxa" x="120" y="178" width="192" height="20" rx="3"/><text class="tm" x="128" y="192">A</text>
<rect class="bxo" x="312" y="178" width="96" height="20" rx="3"/><text class="tm" x="320" y="192">E</text>
<rect class="bxo" x="408" y="178" width="224" height="20" rx="3"/><text class="tm" x="416" y="192">G</text>
<rect class="bxa" x="120" y="202" width="384" height="20" rx="3"/><text class="tm" x="128" y="216">B</text>
<rect class="bxo" x="504" y="202" width="128" height="20" rx="3"/><text class="tm" x="512" y="216">H</text>
<rect class="bxa" x="120" y="226" width="128" height="20" rx="3"/><text class="tm" x="128" y="240">C</text>
<rect class="bxo" x="248" y="226" width="128" height="20" rx="3"/><text class="tm" x="256" y="240">F</text>
<rect class="bxo" x="376" y="226" width="192" height="20" rx="3"/><text class="tm" x="384" y="240">I</text>
<rect class="bxa" x="120" y="250" width="288" height="20" rx="3"/><text class="tm" x="128" y="264">D</text>
<rect class="bxo" x="408" y="250" width="224" height="20" rx="3"/><text class="tm" x="416" y="264">J</text>
<text class="tm" x="648" y="196">no idle slots;</text>
<text class="tm" x="648" y="212">new requests join</text>
<text class="tm" x="648" y="228">between steps</text>
<line class="lnm" x1="120" y1="282" x2="636" y2="282" marker-end="url(#s2m)"/>
<text class="tm" x="640" y="286">decode steps</text>
</svg>
```

Each bar is one request generating tokens, one step per column. In static batching the grey slots are GPU capacity paid for and wasted while everyone waits for B. Continuous batching admits a new request (green) the moment a slot frees up, which is why engines like vLLM serve many more requests on the same GPU.

### Diagram: PagedAttention: reserved slabs versus small pages
before: Q. Explain PagedAttention

```svg
<svg viewBox="0 0 760 250" role="img" aria-label="Left: contiguous allocation reserves the maximum length for each request up front, so most of A's and B's reservations hold nothing and request C cannot fit. Right: paged allocation splits the KV cache into small fixed-size blocks handed out as tokens arrive; a block table maps each request's logical blocks to physical blocks anywhere in memory, for example A's blocks 0, 1 and 2 live in physical blocks 5, 2 and 11, and C fits in the free blocks.">
<text class="tb" x="20" y="24">contiguous: reserve max length up front</text>
<rect class="bxa" x="40" y="40" width="110" height="34" rx="4"/><text class="t" x="50" y="62">A: used</text>
<rect class="bx2 dash" x="150" y="40" width="170" height="34" rx="4"/><text class="tm" x="235" y="62" text-anchor="middle">reserved, empty</text>
<rect class="bxo" x="40" y="84" width="60" height="34" rx="4"/><text class="t" x="50" y="106">B</text>
<rect class="bx2 dash" x="100" y="84" width="220" height="34" rx="4"/><text class="tm" x="210" y="106" text-anchor="middle">reserved, empty</text>
<rect class="bxw dash" x="40" y="128" width="280" height="34" rx="4"/><text class="tm" x="180" y="150" text-anchor="middle">C waits: no free stretch big enough</text>
<text class="ta" x="40" y="190">most reserved memory holds nothing</text>
<line class="lnm dash" x1="360" y1="20" x2="360" y2="230"/>
<text class="tb" x="380" y="24">paged: small blocks as tokens arrive</text>
<rect class="bxo" x="400" y="40" width="44" height="30" rx="4"/><text class="tm" x="422" y="60" text-anchor="middle">B0</text>
<rect class="bx" x="450" y="40" width="44" height="30" rx="4"/>
<rect class="bxa" x="500" y="40" width="44" height="30" rx="4"/><text class="tm" x="522" y="60" text-anchor="middle">A1</text>
<rect class="bxw" x="550" y="40" width="44" height="30" rx="4"/><text class="tm" x="572" y="60" text-anchor="middle">C2</text>
<rect class="bx" x="400" y="76" width="44" height="30" rx="4"/>
<rect class="bxa" x="450" y="76" width="44" height="30" rx="4"/><text class="tm" x="472" y="96" text-anchor="middle">A0</text>
<rect class="bx" x="500" y="76" width="44" height="30" rx="4"/>
<rect class="bxo" x="550" y="76" width="44" height="30" rx="4"/><text class="tm" x="572" y="96" text-anchor="middle">B1</text>
<rect class="bx" x="400" y="112" width="44" height="30" rx="4"/>
<rect class="bxw" x="450" y="112" width="44" height="30" rx="4"/><text class="tm" x="472" y="132" text-anchor="middle">C0</text>
<rect class="bx" x="500" y="112" width="44" height="30" rx="4"/>
<rect class="bxa" x="550" y="112" width="44" height="30" rx="4"/><text class="tm" x="572" y="132" text-anchor="middle">A2</text>
<rect class="bx" x="400" y="148" width="44" height="30" rx="4"/>
<rect class="bx" x="450" y="148" width="44" height="30" rx="4"/>
<rect class="bxw" x="500" y="148" width="44" height="30" rx="4"/><text class="tm" x="522" y="168" text-anchor="middle">C1</text>
<rect class="bx" x="550" y="148" width="44" height="30" rx="4"/>
<text class="tm" x="620" y="52">A's block table</text>
<rect class="bx2" x="620" y="60" width="120" height="72" rx="6"/>
<text class="tmono" x="636" y="80">0 -> 5</text>
<text class="tmono" x="636" y="100">1 -> 2</text>
<text class="tmono" x="636" y="120">2 -> 11</text>
<text class="tm" x="400" y="206">blocks need not sit next to each other;</text>
<text class="tm" x="400" y="222">waste is at most one part-filled block per request</text>
</svg>
```

On the left, memory is booked for the longest possible answer, so most of it stays empty and C cannot start. On the right, the cache is cut into small fixed blocks handed out only as tokens arrive, and a block table remembers where each request's blocks live, like pages in an operating system.

## Quantization

### Diagram: Number formats and what they do to memory

```svg
<svg viewBox="0 0 760 300" role="img" aria-label="Bit layouts: FP16 has 1 sign bit, 5 exponent bits and 10 mantissa bits; BF16 has 1 sign, 8 exponent and 7 mantissa bits; FP8 E4M3 has 1 sign, 4 exponent and 3 mantissa bits; INT8 uses 8 integer bits and INT4 uses 4, both with scale factors. Weight memory for a 7 billion parameter model: about 28 GB in FP32, 14 GB in BF16, 7 GB in INT8 and about 4 GB in INT4 once scales are counted.">
<text class="tb" x="20" y="44">FP16</text>
<rect class="bxw" x="110" y="30" width="18" height="22"/>
<rect class="bxa" x="128" y="30" width="90" height="22"/>
<rect class="bxo" x="218" y="30" width="180" height="22"/>
<text class="tm" x="420" y="45">more precision, small range: needs loss scaling</text>
<text class="tb" x="20" y="74">BF16</text>
<rect class="bxw" x="110" y="60" width="18" height="22"/>
<rect class="bxa" x="128" y="60" width="144" height="22"/>
<rect class="bxo" x="272" y="60" width="126" height="22"/>
<text class="tm" x="420" y="75">FP32's range, less precision: the default</text>
<text class="tb" x="20" y="104">FP8 E4M3</text>
<rect class="bxw" x="110" y="90" width="18" height="22"/>
<rect class="bxa" x="128" y="90" width="72" height="22"/>
<rect class="bxo" x="200" y="90" width="54" height="22"/>
<text class="tm" x="420" y="105">newer GPUs; weights and activations</text>
<text class="tb" x="20" y="134">INT8</text>
<rect class="bx2" x="110" y="120" width="144" height="22"/>
<text class="tm" x="420" y="135">integers plus a scale per tensor or channel</text>
<text class="tb" x="20" y="164">INT4</text>
<rect class="bx2" x="110" y="150" width="72" height="22"/>
<text class="tm" x="420" y="165">weight-only, a scale per small group</text>
<rect class="bxw" x="110" y="182" width="12" height="12"/><text class="tm" x="128" y="192">sign</text>
<rect class="bxa" x="170" y="182" width="12" height="12"/><text class="tm" x="188" y="192">exponent (range)</text>
<rect class="bxo" x="290" y="182" width="12" height="12"/><text class="tm" x="308" y="192">mantissa (precision)</text>
<rect class="bx2" x="430" y="182" width="12" height="12"/><text class="tm" x="448" y="192">integer bits</text>
<text class="tb" x="20" y="222">7B weights</text>
<rect class="bx2" x="110" y="208" width="420" height="16" rx="3"/><text class="tm" x="538" y="221">FP32: 28 GB</text>
<rect class="bxa" x="110" y="230" width="210" height="16" rx="3"/><text class="tm" x="328" y="243">BF16 or FP16: 14 GB</text>
<rect class="bxo" x="110" y="252" width="105" height="16" rx="3"/><text class="tm" x="223" y="265">INT8 or FP8: 7 GB</text>
<rect class="bxw" x="110" y="274" width="60" height="16" rx="3"/><text class="tm" x="178" y="287">INT4: about 4 GB with scales</text>
</svg>
```

Each square is one bit. Exponent bits (blue) buy range and mantissa bits (green) buy precision, so BF16 keeps FP32's range while FP16 keeps more precision. Fewer bits per weight shrink memory in direct proportion, which frees room for the KV cache and speeds up memory-bound decode.

## Speed-ups Beyond Batching

### Diagram: Speculative decoding: draft, verify, keep
before: Q. Explain speculative decoding

```svg
<svg viewBox="0 0 760 260" role="img" aria-label="A small draft model guesses four tokens: the, cat, sat, down. The large target model checks all four in a single forward pass. It accepts the and cat, rejects sat and supplies its own token lay at that position, and the guess after the rejection, down, is dropped. Three tokens come out of one large-model pass.">
<defs>
<marker id="s4k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<text class="tb" x="20" y="64">1. draft model guesses</text>
<text class="tm" x="20" y="82">small and fast</text>
<rect class="bxw" x="260" y="44" width="70" height="34" rx="5"/><text class="t" x="295" y="66" text-anchor="middle">the</text>
<rect class="bxw" x="340" y="44" width="70" height="34" rx="5"/><text class="t" x="375" y="66" text-anchor="middle">cat</text>
<rect class="bxw" x="420" y="44" width="70" height="34" rx="5"/><text class="t" x="455" y="66" text-anchor="middle">sat</text>
<rect class="bxw" x="500" y="44" width="70" height="34" rx="5"/><text class="t" x="535" y="66" text-anchor="middle">down</text>
<line class="ln" x1="415" y1="78" x2="415" y2="104" marker-end="url(#s4k)"/>
<text class="tb" x="20" y="130">2. target model verifies</text>
<text class="tm" x="20" y="148">one pass over all 4</text>
<rect class="bx" x="260" y="106" width="310" height="40" rx="6"/>
<text class="t" x="415" y="131" text-anchor="middle">one forward pass of the large model</text>
<line class="ln" x1="415" y1="146" x2="415" y2="172" marker-end="url(#s4k)"/>
<text class="tb" x="20" y="198">3. keep the agreed prefix</text>
<text class="tm" x="20" y="216">plus the target's own token</text>
<rect class="bxo" x="260" y="174" width="70" height="34" rx="5"/><text class="t" x="295" y="196" text-anchor="middle">the</text>
<rect class="bxo" x="340" y="174" width="70" height="34" rx="5"/><text class="t" x="375" y="196" text-anchor="middle">cat</text>
<rect class="bxa" x="420" y="174" width="70" height="34" rx="5"/><text class="t" x="455" y="196" text-anchor="middle">lay</text>
<rect class="bx2 dash" x="500" y="174" width="70" height="34" rx="5"/><text class="tm" x="535" y="196" text-anchor="middle">down</text>
<text class="to" x="295" y="226" text-anchor="middle">kept</text>
<text class="to" x="375" y="226" text-anchor="middle">kept</text>
<text class="ta" x="455" y="226" text-anchor="middle">replaces sat</text>
<text class="tm" x="535" y="226" text-anchor="middle">dropped</text>
<text class="tm" x="600" y="64">3 tokens from 1 big pass</text>
<text class="tm" x="600" y="80">plus 4 cheap draft steps.</text>
<text class="tm" x="600" y="112">Pays off only when most</text>
<text class="tm" x="600" y="128">guesses are accepted;</text>
<text class="tm" x="600" y="144">the output is unchanged.</text>
</svg>
```

The big model normally produces one token per pass. Here a cheap model guesses several tokens ahead, and the big model checks them all in one pass, keeping the guesses it agrees with plus one token of its own. When the draft is usually right, you get several tokens for the price of one big pass, with no change to the output.

### Diagram: Chunked prefill keeps streams steady
before: Q. What problem does chunked prefill

```svg
<svg viewBox="0 0 760 240" role="img" aria-label="Without chunking, a long 8k-token prompt is prefilled in one long step and every other user's next token waits behind it. With chunked prefill, the prompt is split into slices and each GPU step runs a normal decode batch plus one slice, so streaming users keep a steady inter-token latency while the long prompt's first token arrives slightly later.">
<defs>
<marker id="s5m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<text class="tb" x="20" y="72">without</text>
<text class="tm" x="20" y="88">chunking</text>
<rect class="bxo" x="120" y="54" width="40" height="34" rx="4"/><text class="tm" x="140" y="76" text-anchor="middle">d</text>
<rect class="bxo" x="164" y="54" width="40" height="34" rx="4"/><text class="tm" x="184" y="76" text-anchor="middle">d</text>
<rect class="bxa" x="208" y="54" width="320" height="34" rx="4"/><text class="t" x="368" y="76" text-anchor="middle">prefill of an 8k-token prompt</text>
<rect class="bxo" x="532" y="54" width="40" height="34" rx="4"/><text class="tm" x="552" y="76" text-anchor="middle">d</text>
<rect class="bxo" x="576" y="54" width="40" height="34" rx="4"/><text class="tm" x="596" y="76" text-anchor="middle">d</text>
<line class="lna" x1="208" y1="40" x2="528" y2="40"/>
<line class="lna" x1="208" y1="34" x2="208" y2="46"/><line class="lna" x1="528" y1="34" x2="528" y2="46"/>
<text class="ta" x="368" y="30" text-anchor="middle">streaming users get no tokens here</text>
<text class="tb" x="20" y="152">chunked</text>
<text class="tm" x="20" y="168">prefill</text>
<rect class="bxo" x="120" y="134" width="96" height="17" rx="3"/><text class="tm" x="168" y="147" text-anchor="middle">decode</text>
<rect class="bxa" x="120" y="151" width="96" height="17" rx="3"/><text class="tm" x="168" y="164" text-anchor="middle">chunk 1</text>
<rect class="bxo" x="220" y="134" width="96" height="17" rx="3"/><text class="tm" x="268" y="147" text-anchor="middle">decode</text>
<rect class="bxa" x="220" y="151" width="96" height="17" rx="3"/><text class="tm" x="268" y="164" text-anchor="middle">chunk 2</text>
<rect class="bxo" x="320" y="134" width="96" height="17" rx="3"/><text class="tm" x="368" y="147" text-anchor="middle">decode</text>
<rect class="bxa" x="320" y="151" width="96" height="17" rx="3"/><text class="tm" x="368" y="164" text-anchor="middle">chunk 3</text>
<rect class="bxo" x="420" y="134" width="96" height="17" rx="3"/><text class="tm" x="468" y="147" text-anchor="middle">decode</text>
<rect class="bxa" x="420" y="151" width="96" height="17" rx="3"/><text class="tm" x="468" y="164" text-anchor="middle">chunk 4</text>
<rect class="bxo" x="520" y="134" width="40" height="34" rx="4"/><text class="tm" x="540" y="156" text-anchor="middle">d</text>
<rect class="bxo" x="564" y="134" width="40" height="34" rx="4"/><text class="tm" x="584" y="156" text-anchor="middle">d</text>
<line class="lnm" x1="120" y1="196" x2="640" y2="196" marker-end="url(#s5m)"/>
<text class="tm" x="644" y="200">GPU steps</text>
<text class="tm" x="20" y="228">Every step stays short, so streaming users keep a steady pace; the long prompt's own first token arrives a little later.</text>
</svg>
```

Prefilling a huge prompt in one go freezes everyone else's stream (blue bracket). Chunked prefill cuts the prompt into slices and runs one slice alongside the normal decode work in each step, trading a slightly later first token for the long request in exchange for smooth streaming for everyone else.

### Diagram: Prefix caching reuses an identical start
before: Q. What is prefix caching inside the engine

```svg
<svg viewBox="0 0 760 230" role="img" aria-label="Request 1 computes the system prompt and tools and caches their KV blocks, then computes question 1. Request 2 has the identical prefix, reuses the cached blocks and computes only question 2. Request 3 changes something in the middle of the system prompt, so only the part before the change is reused and everything after it is recomputed.">
<text class="tm" x="20" y="64">request 1</text>
<rect class="bxa" x="120" y="44" width="360" height="34" rx="4"/><text class="t" x="300" y="66" text-anchor="middle">system prompt + tools: computed, cached</text>
<rect class="bx" x="484" y="44" width="150" height="34" rx="4"/><text class="t" x="559" y="66" text-anchor="middle">question 1</text>
<text class="tm" x="20" y="114">request 2</text>
<rect class="bxo" x="120" y="94" width="360" height="34" rx="4"/><text class="t" x="300" y="116" text-anchor="middle">same prefix: reused from cache</text>
<rect class="bx" x="484" y="94" width="150" height="34" rx="4"/><text class="t" x="559" y="116" text-anchor="middle">question 2</text>
<text class="tm" x="20" y="164">request 3</text>
<rect class="bxo" x="120" y="144" width="190" height="34" rx="4"/><text class="t" x="215" y="166" text-anchor="middle">reused up to the change</text>
<rect class="bxw" x="314" y="144" width="166" height="34" rx="4"/><text class="t" x="397" y="166" text-anchor="middle">today's date: recompute</text>
<rect class="bx" x="484" y="144" width="150" height="34" rx="4"/><text class="t" x="559" y="166" text-anchor="middle">question 3</text>
<text class="to" x="646" y="116">no prefill cost</text>
<text class="to" x="646" y="132">for the prefix</text>
<text class="tm" x="20" y="212">Only an exact token-for-token match from the very start is reused: put stable content first and variable content last.</text>
</svg>
```

The engine keeps the KV blocks of recent prompts. When a new request starts with exactly the same tokens, those blocks are reused and only the new tail is computed (green). One changed token, such as a timestamp near the top, breaks the match from that point on (yellow).

### Diagram: Replicas, tensor parallelism and pipeline parallelism
before: Q. Tensor parallelism versus pipeline

```svg
<svg viewBox="0 0 760 270" role="img" aria-label="Three ways to use two GPUs. Replicas: each GPU holds the whole model and a router splits requests between them, adding throughput when the model fits on one GPU. Tensor parallelism: each GPU holds half of every layer's weights and they exchange results with an all-reduce after every layer, which needs a fast link and lowers latency or fits a bigger model. Pipeline parallelism: GPU 1 holds layers 1 to 16 and GPU 2 holds layers 17 to 32, passing activations once per stage, with idle bubbles unless micro-batched.">
<defs>
<marker id="s6k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="s6a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tb" x="130" y="24" text-anchor="middle">replicas</text>
<text class="tb" x="384" y="24" text-anchor="middle">tensor parallel</text>
<text class="tb" x="630" y="24" text-anchor="middle">pipeline parallel</text>
<line class="lnm dash" x1="252" y1="16" x2="252" y2="256"/>
<line class="lnm dash" x1="510" y1="16" x2="510" y2="256"/>
<rect class="bx2" x="58" y="40" width="145" height="30" rx="6"/><text class="t" x="130" y="60" text-anchor="middle">router</text>
<line class="ln" x1="110" y1="70" x2="78" y2="108" marker-end="url(#s6k)"/>
<line class="ln" x1="150" y1="70" x2="187" y2="108" marker-end="url(#s6k)"/>
<rect class="bx" x="25" y="110" width="100" height="90" rx="8"/><text class="tb" x="75" y="148" text-anchor="middle">GPU 1</text><text class="tm" x="75" y="168" text-anchor="middle">full model</text>
<rect class="bx" x="140" y="110" width="100" height="90" rx="8"/><text class="tb" x="190" y="148" text-anchor="middle">GPU 2</text><text class="tm" x="190" y="168" text-anchor="middle">full model</text>
<text class="tm" x="20" y="226">more throughput;</text>
<text class="tm" x="20" y="242">the model must fit one GPU</text>
<rect class="bxa" x="272" y="70" width="95" height="130" rx="8"/><text class="tb" x="319" y="110" text-anchor="middle">GPU 1</text><text class="tm" x="319" y="130" text-anchor="middle">half of every</text><text class="tm" x="319" y="146" text-anchor="middle">layer</text>
<rect class="bxa" x="402" y="70" width="95" height="130" rx="8"/><text class="tb" x="449" y="110" text-anchor="middle">GPU 2</text><text class="tm" x="449" y="130" text-anchor="middle">other half of</text><text class="tm" x="449" y="146" text-anchor="middle">every layer</text>
<line class="lna" x1="369" y1="135" x2="400" y2="135" marker-start="url(#s6a)" marker-end="url(#s6a)"/>
<text class="ta" x="384" y="58" text-anchor="middle">all-reduce every layer</text>
<text class="tm" x="266" y="226">lower latency, bigger models;</text>
<text class="tm" x="266" y="242">needs a fast link (NVLink)</text>
<rect class="bxo" x="530" y="56" width="200" height="60" rx="8"/><text class="tb" x="630" y="82" text-anchor="middle">GPU 1</text><text class="tm" x="630" y="100" text-anchor="middle">layers 1 to 16</text>
<line class="ln" x1="630" y1="116" x2="630" y2="148" marker-end="url(#s6k)"/>
<text class="tm" x="638" y="138">activations</text>
<rect class="bxo" x="530" y="150" width="200" height="60" rx="8"/><text class="tb" x="630" y="176" text-anchor="middle">GPU 2</text><text class="tm" x="630" y="194" text-anchor="middle">layers 17 to 32</text>
<text class="tm" x="524" y="226">talks once per stage boundary;</text>
<text class="tm" x="524" y="242">idle bubbles unless micro-batched</text>
</svg>
```

Replicas copy the whole model so more users are served at once. Tensor parallelism splits every layer across GPUs, so they must talk after every layer (blue), which needs a very fast link but cuts latency. Pipeline parallelism splits the stack of layers into stages, which talks less but leaves GPUs idle unless work is fed in small batches.
