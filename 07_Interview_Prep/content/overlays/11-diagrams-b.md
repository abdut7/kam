## LLM Transformer Architecture

### Diagram: A decoder-only transformer, top to bottom
before: Walkthrough: one token

```svg
<svg viewBox="0 0 760 640" role="img" aria-label="Decoder-only transformer. Text goes through the tokenizer into token IDs, then the embedding table turns each ID into a vector. The vectors pass through N identical decoder blocks; each block applies RMSNorm, masked multi-head self-attention with RoPE, a residual add, RMSNorm, a feed-forward network or mixture of experts, and another residual add. A final norm and the LM head turn the last vector into one score per vocabulary token; softmax and sampling pick the next token, which is appended and the model runs again.">
<defs>
<marker id="t1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="t1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
<marker id="t1m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<text class="tb" x="380" y="22" text-anchor="middle">"The cat sat"</text>
<line class="ln" x1="380" y1="28" x2="380" y2="39" marker-end="url(#t1k)"/>
<rect class="bx" x="230" y="40" width="300" height="32" rx="6"/>
<text class="t" x="380" y="61" text-anchor="middle">tokenizer: text into token IDs</text>
<text class="tmono" x="380" y="92" text-anchor="middle">[ id1, id2, id3 ]</text>
<line class="ln" x1="380" y1="96" x2="380" y2="107" marker-end="url(#t1k)"/>
<rect class="bx" x="230" y="108" width="300" height="32" rx="6"/>
<text class="t" x="380" y="129" text-anchor="middle">embedding table: each ID becomes a vector</text>
<text class="tm" x="545" y="129">shape: [tokens, d_model]</text>
<rect class="zone" x="160" y="156" width="460" height="300" rx="10"/>
<text class="ta" x="604" y="176" text-anchor="end">decoder block, repeated N times</text>
<line class="ln" x1="380" y1="140" x2="380" y2="183" marker-end="url(#t1k)"/>
<rect class="bx2" x="230" y="184" width="300" height="30" rx="6"/>
<text class="t" x="380" y="204" text-anchor="middle">RMSNorm</text>
<line class="ln" x1="380" y1="214" x2="380" y2="225" marker-end="url(#t1k)"/>
<rect class="bxa" x="230" y="226" width="300" height="50" rx="6"/>
<text class="tb" x="380" y="248" text-anchor="middle">masked multi-head self-attention</text>
<text class="tm" x="380" y="266" text-anchor="middle">RoPE rotates Q and K by position</text>
<line class="ln" x1="380" y1="276" x2="380" y2="284" marker-end="url(#t1k)"/>
<circle class="bx" cx="380" cy="296" r="11"/>
<text class="tb" x="380" y="301" text-anchor="middle">+</text>
<line class="ln" x1="380" y1="307" x2="380" y2="319" marker-end="url(#t1k)"/>
<rect class="bx2" x="230" y="320" width="300" height="30" rx="6"/>
<text class="t" x="380" y="340" text-anchor="middle">RMSNorm</text>
<line class="ln" x1="380" y1="350" x2="380" y2="361" marker-end="url(#t1k)"/>
<rect class="bxo" x="230" y="362" width="300" height="50" rx="6"/>
<text class="tb" x="380" y="384" text-anchor="middle">feed-forward network (SwiGLU)</text>
<text class="tm" x="380" y="402" text-anchor="middle">or a mixture of experts (MoE) layer</text>
<line class="ln" x1="380" y1="412" x2="380" y2="420" marker-end="url(#t1k)"/>
<circle class="bx" cx="380" cy="432" r="11"/>
<text class="tb" x="380" y="437" text-anchor="middle">+</text>
<path class="lna" d="M380,168 H200 V296 H367" marker-end="url(#t1a)"/>
<path class="lna" d="M380,312 H200 V432 H367" marker-end="url(#t1a)"/>
<text class="ta" x="190" y="300" text-anchor="middle" transform="rotate(-90 190 300)">residual stream: each block adds to it</text>
<text class="tm" x="630" y="244">mixes information</text>
<text class="tm" x="630" y="260">between tokens</text>
<text class="tm" x="630" y="380">works on each</text>
<text class="tm" x="630" y="396">token alone</text>
<line class="ln" x1="380" y1="443" x2="380" y2="465" marker-end="url(#t1k)"/>
<rect class="bx2" x="230" y="466" width="300" height="30" rx="6"/>
<text class="t" x="380" y="486" text-anchor="middle">final norm</text>
<line class="ln" x1="380" y1="496" x2="380" y2="507" marker-end="url(#t1k)"/>
<rect class="bx" x="230" y="508" width="300" height="34" rx="6"/>
<text class="t" x="380" y="530" text-anchor="middle">LM head: one score per vocabulary token</text>
<text class="tm" x="545" y="530">logits: [tokens, vocab]</text>
<line class="ln" x1="380" y1="542" x2="380" y2="553" marker-end="url(#t1k)"/>
<rect class="bxa" x="230" y="554" width="300" height="34" rx="6"/>
<text class="t" x="380" y="576" text-anchor="middle">softmax and sampling (temperature, top-p)</text>
<line class="ln" x1="380" y1="588" x2="380" y2="599" marker-end="url(#t1k)"/>
<text class="tb" x="380" y="618" text-anchor="middle">next token: "on"</text>
<path class="lnm dash" d="M440,614 H744 V18 H440" marker-end="url(#t1m)"/>
<text class="tm" x="736" y="520" text-anchor="middle" transform="rotate(-90 736 520)">append, run again</text>
</svg>
```

Follow the black arrows down: text becomes IDs, IDs become vectors, and the vectors pass through the same decoder block N times. Inside each block, attention mixes information across positions and the feed-forward network transforms each position on its own. The blue lines are the residual stream: each sub-layer adds its result to it instead of replacing it. At the bottom, the LM head scores every vocabulary token, one token is sampled, and the dashed loop feeds it back in.

### Diagram: Inside one attention head
before: Walkthrough: inside self-attention

```svg
<svg viewBox="0 0 760 320" role="img" aria-label="Inside one attention head. Each input token is projected into a query, a key and a value. Scores are query times key transposed divided by the square root of the key dimension; the causal mask blocks every score where a token would look at a later token. A softmax per row turns scores into weights, the weights mix the values, and the heads are concatenated and projected by W_O.">
<defs>
<marker id="t2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="t2m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
<marker id="t2o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mko"/></marker>
<marker id="t2a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tm" x="55" y="96" text-anchor="middle">input x</text>
<rect class="bx" x="20" y="106" width="70" height="28" rx="6"/>
<text class="t" x="55" y="125" text-anchor="middle">The</text>
<rect class="bx" x="20" y="146" width="70" height="28" rx="6"/>
<text class="t" x="55" y="165" text-anchor="middle">cat</text>
<rect class="bx" x="20" y="186" width="70" height="28" rx="6"/>
<text class="t" x="55" y="205" text-anchor="middle">sat</text>
<line class="lnm" x1="90" y1="150" x2="138" y2="62" marker-end="url(#t2m)"/>
<line class="lnm" x1="90" y1="160" x2="138" y2="160" marker-end="url(#t2m)"/>
<line class="lnm" x1="90" y1="170" x2="138" y2="258" marker-end="url(#t2m)"/>
<rect class="bxa" x="140" y="40" width="130" height="44" rx="6"/>
<text class="t" x="205" y="59" text-anchor="middle">W_Q gives Q</text>
<text class="tm" x="205" y="76" text-anchor="middle">one row per token</text>
<rect class="bxa" x="140" y="140" width="130" height="44" rx="6"/>
<text class="t" x="205" y="159" text-anchor="middle">W_K gives K</text>
<text class="tm" x="205" y="176" text-anchor="middle">one column per token</text>
<rect class="bxo" x="140" y="240" width="130" height="44" rx="6"/>
<text class="t" x="205" y="259" text-anchor="middle">W_V gives V</text>
<text class="tm" x="205" y="276" text-anchor="middle">what gets mixed</text>
<line class="lna" x1="270" y1="64" x2="300" y2="108" marker-end="url(#t2a)"/>
<line class="lna" x1="270" y1="160" x2="300" y2="150" marker-end="url(#t2a)"/>
<text class="tb" x="384" y="62" text-anchor="middle">scores = Q·Kᵀ / √d_k</text>
<text class="tm" x="348" y="88" text-anchor="middle">The</text>
<text class="tm" x="384" y="88" text-anchor="middle">cat</text>
<text class="tm" x="420" y="88" text-anchor="middle">sat</text>
<text class="tm" x="324" y="119" text-anchor="end">The</text>
<text class="tm" x="324" y="155" text-anchor="end">cat</text>
<text class="tm" x="324" y="191" text-anchor="end">sat</text>
<rect class="bxa" x="330" y="96" width="36" height="36"/>
<rect class="bx2" x="366" y="96" width="36" height="36"/>
<text class="tm" x="384" y="119" text-anchor="middle">-inf</text>
<rect class="bx2" x="402" y="96" width="36" height="36"/>
<text class="tm" x="420" y="119" text-anchor="middle">-inf</text>
<rect class="bxa" x="330" y="132" width="36" height="36"/>
<rect class="bxa" x="366" y="132" width="36" height="36"/>
<rect class="bx2" x="402" y="132" width="36" height="36"/>
<text class="tm" x="420" y="155" text-anchor="middle">-inf</text>
<rect class="bxa" x="330" y="168" width="36" height="36"/>
<rect class="bxa" x="366" y="168" width="36" height="36"/>
<rect class="bxa" x="402" y="168" width="36" height="36"/>
<text class="tm" x="384" y="222" text-anchor="middle">causal mask:</text>
<text class="tm" x="384" y="237" text-anchor="middle">no peeking at later tokens</text>
<line class="ln" x1="438" y1="140" x2="478" y2="136" marker-end="url(#t2k)"/>
<rect class="bx" x="480" y="116" width="120" height="40" rx="6"/>
<text class="t" x="540" y="141" text-anchor="middle">softmax per row</text>
<line class="ln" x1="540" y1="156" x2="540" y2="188" marker-end="url(#t2k)"/>
<rect class="bxo" x="480" y="190" width="120" height="40" rx="6"/>
<text class="t" x="540" y="215" text-anchor="middle">weights × V</text>
<path class="lno" d="M270,260 H540 V232" marker-end="url(#t2o)"/>
<text class="to" x="420" y="254" text-anchor="middle">values to mix</text>
<line class="ln" x1="600" y1="206" x2="628" y2="186" marker-end="url(#t2k)"/>
<rect class="bxa" x="630" y="150" width="120" height="56" rx="6"/>
<text class="tb" x="690" y="174" text-anchor="middle">concat heads</text>
<text class="tm" x="690" y="194" text-anchor="middle">then W_O</text>
<text class="tm" x="20" y="306">Every head does this with its own W_Q, W_K and W_V; the heads run in parallel and their outputs are concatenated.</text>
</svg>
```

Each row of the grid is one token asking "who should I listen to?" and each column is a token it may listen to. The grey `-inf` cells are the causal mask: after softmax they become zero, so no token can see the future. The weights then mix the value vectors (green), and every head's result is concatenated and projected back.

### Diagram: Prefill and decode share one KV cache
before: Walkthrough: prefill

```svg
<svg viewBox="0 0 760 270" role="img" aria-label="Prefill runs the whole prompt, five tokens, through all layers in parallel and writes their keys and values into the KV cache; it is compute-bound and ends at the first output token. Each decode step runs one new token, reads the cached keys and values of earlier tokens and appends its own; it is memory-bound and repeats once per output token.">
<defs>
<marker id="t3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="t3a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tb" x="196" y="22" text-anchor="middle">Prefill: the whole prompt at once</text>
<text class="tb" x="575" y="22" text-anchor="middle">Decode: one new token per step</text>
<rect class="bxa" x="40" y="40" width="56" height="28" rx="5"/><text class="t" x="68" y="59" text-anchor="middle">t1</text>
<rect class="bxa" x="104" y="40" width="56" height="28" rx="5"/><text class="t" x="132" y="59" text-anchor="middle">t2</text>
<rect class="bxa" x="168" y="40" width="56" height="28" rx="5"/><text class="t" x="196" y="59" text-anchor="middle">t3</text>
<rect class="bxa" x="232" y="40" width="56" height="28" rx="5"/><text class="t" x="260" y="59" text-anchor="middle">t4</text>
<rect class="bxa" x="296" y="40" width="56" height="28" rx="5"/><text class="t" x="324" y="59" text-anchor="middle">t5</text>
<line class="ln" x1="68" y1="68" x2="68" y2="102" marker-end="url(#t3k)"/>
<line class="ln" x1="132" y1="68" x2="132" y2="102" marker-end="url(#t3k)"/>
<line class="ln" x1="196" y1="68" x2="196" y2="102" marker-end="url(#t3k)"/>
<line class="ln" x1="260" y1="68" x2="260" y2="102" marker-end="url(#t3k)"/>
<line class="ln" x1="324" y1="68" x2="324" y2="102" marker-end="url(#t3k)"/>
<rect class="bx" x="40" y="104" width="312" height="40" rx="6"/>
<text class="t" x="196" y="129" text-anchor="middle">all N layers, in parallel over 5 tokens</text>
<line class="ln" x1="196" y1="144" x2="196" y2="182" marker-end="url(#t3k)"/>
<text class="tm" x="204" y="168">writes K and V</text>
<rect class="bxw" x="40" y="184" width="56" height="28" rx="5"/><text class="tm" x="68" y="203" text-anchor="middle">K,V 1</text>
<rect class="bxw" x="104" y="184" width="56" height="28" rx="5"/><text class="tm" x="132" y="203" text-anchor="middle">K,V 2</text>
<rect class="bxw" x="168" y="184" width="56" height="28" rx="5"/><text class="tm" x="196" y="203" text-anchor="middle">K,V 3</text>
<rect class="bxw" x="232" y="184" width="56" height="28" rx="5"/><text class="tm" x="260" y="203" text-anchor="middle">K,V 4</text>
<rect class="bxw" x="296" y="184" width="56" height="28" rx="5"/><text class="tm" x="324" y="203" text-anchor="middle">K,V 5</text>
<text class="tm" x="40" y="238">compute-bound: large matrix multiplies</text>
<text class="tm" x="40" y="256">ends when the first output token appears (TTFT)</text>
<rect class="bxa" x="548" y="40" width="56" height="28" rx="5"/><text class="t" x="576" y="59" text-anchor="middle">t6</text>
<line class="ln" x1="576" y1="68" x2="576" y2="102" marker-end="url(#t3k)"/>
<rect class="bx" x="410" y="104" width="330" height="40" rx="6"/>
<text class="t" x="575" y="129" text-anchor="middle">all N layers, for 1 token</text>
<rect class="bxw" x="410" y="184" width="50" height="28" rx="5"/><text class="tm" x="435" y="203" text-anchor="middle">K,V 1</text>
<rect class="bxw" x="466" y="184" width="50" height="28" rx="5"/><text class="tm" x="491" y="203" text-anchor="middle">K,V 2</text>
<rect class="bxw" x="522" y="184" width="50" height="28" rx="5"/><text class="tm" x="547" y="203" text-anchor="middle">K,V 3</text>
<rect class="bxw" x="578" y="184" width="50" height="28" rx="5"/><text class="tm" x="603" y="203" text-anchor="middle">K,V 4</text>
<rect class="bxw" x="634" y="184" width="50" height="28" rx="5"/><text class="tm" x="659" y="203" text-anchor="middle">K,V 5</text>
<rect class="bxa" x="690" y="184" width="50" height="28" rx="5"/><text class="tm" x="715" y="203" text-anchor="middle">K,V 6</text>
<line class="ln" x1="491" y1="182" x2="491" y2="146" marker-end="url(#t3k)"/>
<text class="tm" x="499" y="170">reads 1 to 5</text>
<line class="lna" x1="715" y1="144" x2="715" y2="182" marker-end="url(#t3a)"/>
<text class="ta" x="707" y="170" text-anchor="end">appends 6</text>
<text class="tm" x="410" y="238">memory-bound: reads all weights and the cache</text>
<text class="tm" x="410" y="256">repeats once per output token (TPOT)</text>
</svg>
```

Prefill (left) pushes every prompt token through the layers at once and stores each token's keys and values. Decode (right) handles one new token per step. It reads the cached keys and values instead of recomputing them, then appends its own. That cache is why long chats eat GPU memory, and why decode speed is limited by memory bandwidth.

## Jev: Decision-Layer Model Architecture

### Diagram: Where Jev sits in an agent system
before: Walkthrough: one routing decision

```svg
<svg viewBox="0 0 760 350" role="img" aria-label="Agent system with a decision layer. A user request goes to an LLM agent that proposes a next step or tool call. Hard checks for schema, authorization and policy run first. Jev answers typed questions about the proposal and returns probabilities; your policy code maps those probabilities through thresholds to allow, review or deny. The decision layer never executes anything. Every decision is logged and the result goes back to the agent.">
<defs>
<marker id="j1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="j1m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<rect class="bx" x="10" y="120" width="100" height="64" rx="8"/>
<text class="tb" x="60" y="146" text-anchor="middle">User</text>
<text class="tm" x="60" y="166" text-anchor="middle">message, event</text>
<rect class="bx" x="126" y="120" width="100" height="64" rx="8"/>
<text class="tb" x="176" y="146" text-anchor="middle">LLM agent</text>
<text class="tm" x="176" y="166" text-anchor="middle">proposes a step</text>
<rect class="bx2" x="242" y="120" width="100" height="64" rx="8"/>
<text class="tb" x="292" y="146" text-anchor="middle">Hard checks</text>
<text class="tm" x="292" y="166" text-anchor="middle">schema, authz</text>
<rect class="zone" x="350" y="84" width="232" height="114" rx="10"/>
<text class="ta" x="466" y="102" text-anchor="middle">decision layer: never executes</text>
<rect class="bxa" x="358" y="120" width="100" height="64" rx="8"/>
<text class="tb" x="408" y="146" text-anchor="middle">Jev</text>
<text class="tm" x="408" y="166" text-anchor="middle">typed questions</text>
<rect class="bx" x="474" y="120" width="100" height="64" rx="8"/>
<text class="tb" x="524" y="146" text-anchor="middle">Your policy</text>
<text class="tm" x="524" y="166" text-anchor="middle">thresholds</text>
<line class="ln" x1="110" y1="152" x2="124" y2="152" marker-end="url(#j1k)"/>
<line class="ln" x1="226" y1="152" x2="240" y2="152" marker-end="url(#j1k)"/>
<line class="ln" x1="342" y1="152" x2="356" y2="152" marker-end="url(#j1k)"/>
<line class="ln" x1="458" y1="152" x2="472" y2="152" marker-end="url(#j1k)"/>
<text class="tm" x="466" y="216" text-anchor="middle">probabilities are not permissions</text>
<rect class="bxo" x="600" y="56" width="150" height="46" rx="8"/>
<text class="tb" x="614" y="76">ALLOW</text>
<text class="tm" x="614" y="93">scoped executor runs it</text>
<rect class="bxw" x="600" y="130" width="150" height="46" rx="8"/>
<text class="tb" x="614" y="150">REVIEW</text>
<text class="tm" x="614" y="167">a human approves first</text>
<rect class="bx" x="600" y="204" width="150" height="46" rx="8"/>
<text class="tb" x="614" y="224">DENY</text>
<text class="tm" x="614" y="241">refuse or ask the user</text>
<line class="ln" x1="574" y1="146" x2="598" y2="80" marker-end="url(#j1k)"/>
<line class="ln" x1="574" y1="152" x2="598" y2="153" marker-end="url(#j1k)"/>
<line class="ln" x1="574" y1="158" x2="598" y2="226" marker-end="url(#j1k)"/>
<rect class="bx2" x="242" y="276" width="340" height="44" rx="8"/>
<text class="t" x="412" y="296" text-anchor="middle">audit log: state, question, answer, probability,</text>
<text class="t" x="412" y="313" text-anchor="middle">threshold, action, model version</text>
<path class="lnm" d="M675,250 V298 H584" marker-end="url(#j1m)"/>
<text class="tm" x="683" y="282">every outcome</text>
<path class="lnm dash" d="M242,298 H176 V186" marker-end="url(#j1m)"/>
<text class="tm" x="184" y="240">result back to the agent</text>
</svg>
```

The agent proposes, Jev answers narrow typed questions about the proposal, and your own code turns the answers into an action through thresholds. Jev never runs anything. Hard checks (schema, permissions, policy) run before it, a scoped executor runs after it, and every decision is written to the audit log.

### Diagram: Anatomy of a Jev request and response
before: Walkthrough: anatomy

```svg
<svg viewBox="0 0 760 330" role="img" aria-label="A Jev request carries one state and several named questions: a Choice question with options you supply, a Score question with rubric levels you define, and a Noul question that states one claim. Each question is answered independently and in parallel against the same state. The response has a typed answer per question: the chosen option with probabilities and confidence, the rubric level with probabilities and confidence, and a value from 0 to 1. Numbers shown are illustrative.">
<defs>
<marker id="j2a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<rect class="zone" x="15" y="20" width="280" height="296" rx="10"/>
<text class="tb" x="30" y="42">Request</text>
<rect class="bx2" x="30" y="56" width="250" height="56" rx="8"/>
<text class="tb" x="42" y="78">state</text>
<text class="tm" x="42" y="98">text or JSON: ticket, tool call, chat</text>
<rect class="bxa" x="30" y="128" width="250" height="50" rx="8"/>
<text class="tb" x="42" y="148">route: Choice</text>
<text class="tm" x="42" y="166">billing | tech | sales | other</text>
<rect class="bxa" x="30" y="190" width="250" height="50" rx="8"/>
<text class="tb" x="42" y="210">urgency: Score</text>
<text class="tm" x="42" y="228">rubric levels: low to critical</text>
<rect class="bxa" x="30" y="252" width="250" height="50" rx="8"/>
<text class="tb" x="42" y="272">refund_asked: Noul</text>
<text class="tm" x="42" y="290">"The user asks for a refund"</text>
<text class="tm" x="382" y="114" text-anchor="middle">each question answered</text>
<text class="tm" x="382" y="130" text-anchor="middle">independently, in parallel</text>
<line class="lna" x1="280" y1="153" x2="483" y2="153" marker-end="url(#j2a)"/>
<line class="lna" x1="280" y1="215" x2="483" y2="215" marker-end="url(#j2a)"/>
<line class="lna" x1="280" y1="277" x2="483" y2="277" marker-end="url(#j2a)"/>
<rect class="zone" x="470" y="20" width="275" height="296" rx="10"/>
<text class="tb" x="485" y="42">Response (illustrative values)</text>
<text class="tm" x="485" y="78">your code validates every answer:</text>
<text class="tm" x="485" y="96">type, allowed option, range 0 to 1</text>
<rect class="bxo" x="485" y="128" width="245" height="50" rx="8"/>
<text class="tb" x="497" y="148">route: billing</text>
<text class="tm" x="497" y="166">probability per option + confidence</text>
<rect class="bxo" x="485" y="190" width="245" height="50" rx="8"/>
<text class="tb" x="497" y="210">urgency: high</text>
<text class="tm" x="497" y="228">probability per level + confidence</text>
<rect class="bxo" x="485" y="252" width="245" height="50" rx="8"/>
<text class="tb" x="497" y="272">refund_asked: 0.92</text>
<text class="tm" x="497" y="290">probability the claim is true</text>
</svg>
```

One request, one state, several named questions. You write every option and rubric level yourself, so every answer is one of yours. Each answer comes back with probabilities, and your code checks type, option and range before using it.

### Diagram: Generative LLM versus decision model
before: Concepts you must understand

```svg
<svg viewBox="0 0 760 250" role="img" aria-label="Comparison. A generative LLM scores the whole vocabulary at each step and produces free text that you must parse, which can fail or land outside your list. A decision model scores only the options you supplied, so its typed answer and probability are always valid and your thresholds decide. TypeSafe has not published Jev's internals; the bottom row shows the general pattern of decision models.">
<defs>
<marker id="j3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<text class="tb" x="15" y="44">Generative LLM</text>
<rect class="bx" x="15" y="56" width="120" height="50" rx="8"/>
<text class="tb" x="27" y="77">prompt</text>
<text class="tm" x="27" y="95">plus instructions</text>
<rect class="bx" x="155" y="56" width="130" height="50" rx="8"/>
<text class="tb" x="167" y="77">transformer</text>
<text class="tm" x="167" y="95">token by token</text>
<rect class="bx2" x="305" y="56" width="180" height="50" rx="8"/>
<text class="tb" x="317" y="77">scores over the</text>
<text class="tm" x="317" y="95">whole vocabulary</text>
<rect class="bx" x="505" y="56" width="110" height="50" rx="8"/>
<text class="tb" x="517" y="77">free text</text>
<text class="tm" x="517" y="95">"probably billing"</text>
<rect class="bxw dash" x="635" y="56" width="115" height="50" rx="8"/>
<text class="tb" x="647" y="77">parse it</text>
<text class="tm" x="647" y="95">may fail, off-list</text>
<line class="ln" x1="135" y1="81" x2="153" y2="81" marker-end="url(#j3k)"/>
<line class="ln" x1="285" y1="81" x2="303" y2="81" marker-end="url(#j3k)"/>
<line class="ln" x1="485" y1="81" x2="503" y2="81" marker-end="url(#j3k)"/>
<line class="ln" x1="615" y1="81" x2="633" y2="81" marker-end="url(#j3k)"/>
<text class="tb" x="15" y="164">Decision model (general pattern)</text>
<rect class="bx" x="15" y="176" width="120" height="50" rx="8"/>
<text class="tb" x="27" y="197">state +</text>
<text class="tm" x="27" y="215">your options</text>
<rect class="bx" x="155" y="176" width="130" height="50" rx="8"/>
<text class="tb" x="167" y="197">model</text>
<text class="tm" x="167" y="215">reads state + question</text>
<rect class="bxa" x="305" y="176" width="180" height="50" rx="8"/>
<text class="tb" x="317" y="197">scores over YOUR</text>
<text class="tm" x="317" y="215">options only (softmax)</text>
<rect class="bxo" x="505" y="176" width="110" height="50" rx="8"/>
<text class="tb" x="517" y="197">typed answer</text>
<text class="tm" x="517" y="215">+ probability</text>
<rect class="bxo" x="635" y="176" width="115" height="50" rx="8"/>
<text class="tb" x="647" y="197">always valid</text>
<text class="tm" x="647" y="215">thresholds decide</text>
<line class="ln" x1="135" y1="201" x2="153" y2="201" marker-end="url(#j3k)"/>
<line class="ln" x1="285" y1="201" x2="303" y2="201" marker-end="url(#j3k)"/>
<line class="ln" x1="485" y1="201" x2="503" y2="201" marker-end="url(#j3k)"/>
<line class="ln" x1="615" y1="201" x2="633" y2="201" marker-end="url(#j3k)"/>
</svg>
```

The difference is the output space, in the middle column. An LLM chooses from the whole vocabulary, so its answer can be malformed or off your list. A decision model chooses only from options you supplied, so it can pick wrong but never invalid. TypeSafe has not published how Jev works inside; the bottom row shows the general pattern of decision models, not Jev's documented design.
