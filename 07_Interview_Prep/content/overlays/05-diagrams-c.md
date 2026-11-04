## Scaling, Routing & Load Balancing

### Diagram: A gateway and router in front of model replicas

```svg
<svg viewBox="0 0 760 300" role="img" aria-label="Clients call a gateway that checks auth, tenant quotas and rate limits and keeps a priority queue. A router sends requests with the same prompt prefix to the same replica, prefers the shortest queue, and tries the small model first. Replicas run vLLM; a third replica is still starting and loading weights. A hosted API is a fallback on overload or errors. An autoscaler adds replicas based on queue depth and waiting time rather than GPU utilization.">
<defs>
<marker id="r1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="r1m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<rect class="bx" x="15" y="120" width="90" height="50" rx="8"/><text class="t" x="60" y="150" text-anchor="middle">clients</text>
<line class="ln" x1="105" y1="145" x2="128" y2="145" marker-end="url(#r1k)"/>
<rect class="bx" x="130" y="100" width="150" height="90" rx="8"/>
<text class="tb" x="143" y="122">gateway</text>
<text class="tm" x="143" y="142">auth, tenant quotas</text>
<text class="tm" x="143" y="158">rate limits</text>
<text class="tm" x="143" y="174">priority queue</text>
<line class="ln" x1="280" y1="145" x2="308" y2="145" marker-end="url(#r1k)"/>
<rect class="bxa" x="310" y="100" width="160" height="90" rx="8"/>
<text class="tb" x="323" y="122">router</text>
<text class="tm" x="323" y="142">same prefix, same replica</text>
<text class="tm" x="323" y="158">shortest queue next</text>
<text class="tm" x="323" y="174">small model first</text>
<rect class="bxo" x="510" y="30" width="230" height="50" rx="8"/>
<text class="tb" x="523" y="52">replica 1</text><text class="tm" x="523" y="70">vLLM, queue: 3</text>
<rect class="bxo" x="510" y="96" width="230" height="50" rx="8"/>
<text class="tb" x="523" y="118">replica 2</text><text class="tm" x="523" y="136">vLLM, queue: 1</text>
<rect class="bx dash" x="510" y="162" width="230" height="50" rx="8"/>
<text class="tb" x="523" y="184">replica 3</text><text class="tm" x="523" y="202">starting: loading weights</text>
<rect class="bx2 dash" x="510" y="228" width="230" height="46" rx="8"/>
<text class="t" x="625" y="247" text-anchor="middle">hosted API fallback</text>
<text class="tm" x="625" y="264" text-anchor="middle">on overload or errors</text>
<line class="ln" x1="470" y1="128" x2="508" y2="58" marker-end="url(#r1k)"/>
<line class="ln" x1="470" y1="140" x2="508" y2="122" marker-end="url(#r1k)"/>
<line class="lnm dash" x1="470" y1="176" x2="508" y2="244" marker-end="url(#r1m)"/>
<rect class="bxw" x="130" y="228" width="250" height="56" rx="8"/>
<text class="tb" x="143" y="250">autoscaler</text>
<text class="tm" x="143" y="270">scales on queue depth and wait time</text>
<line class="lnm dash" x1="380" y1="246" x2="508" y2="196" marker-end="url(#r1m)"/>
<text class="tm" x="400" y="252">adds replicas</text>
</svg>
```

The gateway decides whether a request may run at all, and the router decides where it runs. Sending the same prompt prefix to the same replica keeps that replica's prefix cache warm. New replicas take minutes to load weights, so the autoscaler watches queue depth and waiting time, which rise before users feel it, rather than GPU utilization.

## Caching at the Inference Layer

### Diagram: The layers of caching between a user and the GPU
before: Q. What layers of caching exist

```svg
<svg viewBox="0 0 760 230" role="img" aria-label="A request passes three caches before reaching the GPU. An exact response cache saves the whole call when the same input repeats. A semantic cache saves the whole call when a similar question was answered, with the risk of returning a wrong answer. A provider prompt cache or the engine's prefix cache saves the prefill of a shared prompt prefix. Only a full miss pays for prefill and decode on the GPU. Any hit returns early.">
<defs>
<marker id="r2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="r2a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<path class="lna dash" d="M520,80 V46 H60 V78" marker-end="url(#r2a)"/>
<line class="lna dash" x1="195" y1="80" x2="195" y2="46"/>
<line class="lna dash" x1="355" y1="80" x2="355" y2="46"/>
<text class="ta" x="290" y="38" text-anchor="middle">hit: the answer returns early</text>
<rect class="bx" x="15" y="80" width="90" height="60" rx="8"/><text class="t" x="60" y="115" text-anchor="middle">request</text>
<rect class="bxo" x="125" y="80" width="140" height="60" rx="8"/><text class="tb" x="195" y="104" text-anchor="middle">1. exact</text><text class="tm" x="195" y="123" text-anchor="middle">response cache</text>
<rect class="bxw" x="285" y="80" width="140" height="60" rx="8"/><text class="tb" x="355" y="104" text-anchor="middle">2. semantic</text><text class="tm" x="355" y="123" text-anchor="middle">similar questions</text>
<rect class="bxa" x="445" y="80" width="150" height="60" rx="8"/><text class="tb" x="520" y="104" text-anchor="middle">3. prefix cache</text><text class="tm" x="520" y="123" text-anchor="middle">provider or engine</text>
<rect class="bx2" x="615" y="80" width="130" height="60" rx="8"/><text class="tb" x="680" y="104" text-anchor="middle">GPU</text><text class="tm" x="680" y="123" text-anchor="middle">full compute</text>
<line class="ln" x1="105" y1="110" x2="123" y2="110" marker-end="url(#r2k)"/>
<line class="ln" x1="265" y1="110" x2="283" y2="110" marker-end="url(#r2k)"/>
<line class="ln" x1="425" y1="110" x2="443" y2="110" marker-end="url(#r2k)"/>
<line class="ln" x1="595" y1="110" x2="613" y2="110" marker-end="url(#r2k)"/>
<text class="tm" x="195" y="162" text-anchor="middle">saves: the whole call</text>
<text class="tm" x="195" y="178" text-anchor="middle">safe: same input only</text>
<text class="tm" x="355" y="162" text-anchor="middle">saves: the whole call</text>
<text class="tm" x="355" y="178" text-anchor="middle">risk: a wrong answer</text>
<text class="tm" x="520" y="162" text-anchor="middle">saves: prefill of the</text>
<text class="tm" x="520" y="178" text-anchor="middle">shared prefix only</text>
<text class="tm" x="680" y="162" text-anchor="middle">pays: prefill</text>
<text class="tm" x="680" y="178" text-anchor="middle">and decode</text>
<text class="tm" x="15" y="214">Scope every cache key by tenant, prompt version and model version, or one change silently serves stale answers.</text>
</svg>
```

Each layer saves less but is safer than the one before it, except the semantic cache, which can save a whole call but can also return an answer to a different question. The prefix cache never changes the answer; it only skips recomputing a prompt start the model has already seen.

## Cost Engineering

### Diagram: From GPU price per hour to price per million tokens
before: Q. Convert GPU-hour pricing

```svg
<svg viewBox="0 0 760 180" role="img" aria-label="Price per million tokens equals the GPU price per hour divided by tokens served per hour, times one million. Tokens per hour equals throughput in tokens per second times 3600 times utilization. Illustrative example: 2 dollars per hour divided by 1,000 tokens per second times 3600 times 50 percent, which is 1.8 million tokens per hour, gives about 1.11 dollars per million tokens. Doubling utilization halves the price.">
<rect class="bx" x="15" y="20" width="150" height="56" rx="8"/>
<text class="tb" x="28" y="43">GPU price</text><text class="tm" x="28" y="62">dollars per hour</text>
<text class="tb" x="183" y="54" text-anchor="middle">/</text>
<rect class="bx" x="200" y="20" width="270" height="56" rx="8"/>
<text class="tb" x="213" y="43">tokens served per hour</text><text class="tm" x="213" y="62">tokens/s x 3600 x utilization</text>
<text class="tb" x="483" y="54" text-anchor="middle">x 1M =</text>
<rect class="bxa" x="510" y="20" width="235" height="56" rx="8"/>
<text class="tb" x="523" y="43">price per million tokens</text><text class="tm" x="523" y="62">what you compare to API prices</text>
<text class="tm" x="15" y="104">illustrative:</text>
<text class="tmono" x="15" y="126">$2.00 / hour</text>
<text class="tmono" x="200" y="126">1,000 x 3600 x 50% = 1.8M tokens/h</text>
<text class="tmono" x="510" y="126">about $1.11 per million</text>
<text class="ta" x="15" y="162">Utilization is the biggest lever: double it and the price per token halves, with the same GPU and the same model.</text>
</svg>
```

A GPU costs the same per hour whether it is busy or idle, so the price of each token depends mostly on how many tokens you push through it. The numbers are round and illustrative; plug in your own throughput from a load test.

## Reliability & Observability for Inference

### Diagram: Timeouts for a streaming LLM call
before: Q. Design timeouts and retries

```svg
<svg viewBox="0 0 760 230" role="img" aria-label="Timeline of a streaming call with four timeouts: a connect timeout for opening the connection, a first-token timeout covering connect plus waiting for the first token, an idle timeout on the gap between any two tokens, and a total deadline for the whole call. Retrying is safe before the first token arrives; after tokens have streamed to the user, do not retry blindly.">
<line class="ln" x1="40" y1="30" x2="700" y2="30"/>
<line class="ln" x1="40" y1="24" x2="40" y2="36"/><line class="ln" x1="700" y1="24" x2="700" y2="36"/>
<text class="tb" x="370" y="22" text-anchor="middle">total deadline</text>
<line class="lna" x1="40" y1="54" x2="300" y2="54"/>
<line class="lna" x1="40" y1="48" x2="40" y2="60"/><line class="lna" x1="300" y1="48" x2="300" y2="60"/>
<text class="ta" x="170" y="47" text-anchor="middle">first-token timeout</text>
<line class="lnm" x1="40" y1="76" x2="110" y2="76"/>
<line class="lnm" x1="40" y1="70" x2="40" y2="82"/><line class="lnm" x1="110" y1="70" x2="110" y2="82"/>
<text class="tm" x="116" y="80">connect</text>
<rect class="bx2" x="40" y="90" width="70" height="34" rx="4"/><text class="tm" x="75" y="111" text-anchor="middle">connect</text>
<rect class="bxw" x="110" y="90" width="190" height="34" rx="4"/><text class="tm" x="205" y="111" text-anchor="middle">waiting for the first token</text>
<rect class="bxo" x="304" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="350" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="434" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="480" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="526" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="572" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="618" y="90" width="40" height="34" rx="4"/>
<rect class="bxo" x="664" y="90" width="36" height="34" rx="4"/>
<line class="lnm" x1="390" y1="140" x2="434" y2="140"/>
<line class="lnm" x1="390" y1="134" x2="390" y2="146"/><line class="lnm" x1="434" y1="134" x2="434" y2="146"/>
<text class="tm" x="412" y="160" text-anchor="middle">idle timeout: longest allowed gap</text>
<rect class="bxo" x="40" y="176" width="260" height="30" rx="6"/>
<text class="to" x="170" y="196" text-anchor="middle">safe to retry or fail over</text>
<rect class="bxa" x="304" y="176" width="396" height="30" rx="6"/>
<text class="ta" x="502" y="196" text-anchor="middle">tokens already shown: do not retry blindly</text>
<text class="tm" x="40" y="224">After the first token, either finish, resume with context, or end with a clear error the user can act on.</text>
</svg>
```

A single overall timeout is not enough for streams: a call can connect fast, stall before the first token, or freeze halfway. Separate limits catch each case. Retrying is safe only before anything reached the user (green), because a retry after that would show a second, different answer.

## Project Blueprint: Inference Router

### Diagram: The inference router, end to end

```svg
<svg viewBox="0 0 760 330" role="img" aria-label="Router pipeline. A request with a tenant key is authenticated, checked against the tenant's token and money budget (429 if over), looked up in the cache (returned at once on a hit), classified as easy, hard or long, and sent to the cheapest model that passes: a small local vLLM model or a large hosted API, with fallback to the other if it fails before the first token. A stream proxy relays tokens to the client over SSE and counts them. Metrics and traces record latency, cost and cache hits per model.">
<defs>
<marker id="r3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="r3a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<rect class="bx" x="15" y="30" width="165" height="54" rx="8"/>
<text class="tb" x="30" y="52">1. request</text><text class="tm" x="30" y="72">POST /chat, tenant key</text>
<rect class="bx" x="207" y="30" width="165" height="54" rx="8"/>
<text class="tb" x="222" y="52">2. auth</text><text class="tm" x="222" y="72">tenant, plan, limits</text>
<rect class="bx" x="399" y="30" width="165" height="54" rx="8"/>
<text class="tb" x="414" y="52">3. budget</text><text class="tm" x="414" y="72">over limit: 429</text>
<rect class="bx" x="591" y="30" width="165" height="54" rx="8"/>
<text class="tb" x="606" y="52">4. cache</text><text class="tm" x="606" y="72">hit: return now</text>
<line class="ln" x1="180" y1="57" x2="205" y2="57" marker-end="url(#r3k)"/>
<line class="ln" x1="372" y1="57" x2="397" y2="57" marker-end="url(#r3k)"/>
<line class="ln" x1="564" y1="57" x2="589" y2="57" marker-end="url(#r3k)"/>
<line class="ln" x1="673" y1="84" x2="673" y2="138" marker-end="url(#r3k)"/>
<rect class="bxa" x="591" y="140" width="165" height="54" rx="8"/>
<text class="tb" x="606" y="162">5. classify</text><text class="tm" x="606" y="182">easy, hard, long?</text>
<rect class="bxa" x="399" y="140" width="165" height="54" rx="8"/>
<text class="tb" x="414" y="162">6. pick model</text><text class="tm" x="414" y="182">cheapest that passes</text>
<rect class="bx" x="207" y="140" width="165" height="54" rx="8"/>
<text class="tb" x="222" y="162">7. stream proxy</text><text class="tm" x="222" y="182">SSE, count tokens</text>
<rect class="bxo" x="15" y="140" width="165" height="54" rx="8"/>
<text class="tb" x="30" y="162">8. client</text><text class="tm" x="30" y="182">tokens arrive</text>
<line class="ln" x1="591" y1="167" x2="566" y2="167" marker-end="url(#r3k)"/>
<line class="ln" x1="207" y1="167" x2="182" y2="167" marker-end="url(#r3k)"/>
<line class="ln" x1="440" y1="194" x2="420" y2="238" marker-end="url(#r3k)"/>
<line class="ln" x1="525" y1="194" x2="570" y2="238" marker-end="url(#r3k)"/>
<rect class="bxo" x="330" y="240" width="150" height="54" rx="8"/>
<text class="tb" x="343" y="262">local vLLM</text><text class="tm" x="343" y="282">small, cheap</text>
<rect class="bxa" x="500" y="240" width="150" height="54" rx="8"/>
<text class="tb" x="513" y="262">hosted API</text><text class="tm" x="513" y="282">large, costly</text>
<line class="lna dash" x1="482" y1="267" x2="498" y2="267" marker-start="url(#r3a)" marker-end="url(#r3a)"/>
<path class="ln" d="M330,267 H290 V196" marker-end="url(#r3k)"/>
<text class="tm" x="296" y="230">tokens</text>
<rect class="bx2" x="15" y="240" width="250" height="54" rx="8"/>
<text class="tb" x="30" y="262">metrics and traces</text><text class="tm" x="30" y="282">latency, cost, cache hits per model</text>
<text class="ta" x="330" y="318">fallback to the other model only if it fails before the first token</text>
</svg>
```

Read the top row left to right, then the middle row right to left. Every request is checked for budget and cache before any GPU time is spent. The classifier picks the cheapest model that is good enough, and the stream proxy counts tokens so cost lands in the metrics. The blue dashed link is the fallback rule from the reliability section: switch models only before the first token.
