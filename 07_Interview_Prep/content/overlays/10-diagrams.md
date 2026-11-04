## How Inference Works, One Problem at a Time

### Diagram: The whole story on one page

```svg
<svg viewBox="0 0 760 420" role="img" aria-label="Eight rows pairing a serving problem with the technique that fixes it: one user needs prefill then decode with a KV cache; fifty users each need a KV cache, solved by PagedAttention; short answers waiting for long ones, solved by continuous batching; a long pasted document stalling everyone, solved by chunked prefill; a repeated system prompt, solved by prefix caching; weights too large, solved by quantization; decode still slow, solved by speculative decoding; and proving it worked by measuring TTFT, inter-token latency and throughput.">
<defs>
<marker id="e2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<text class="tb" x="185" y="24" text-anchor="middle">the problem</text>
<text class="tb" x="565" y="24" text-anchor="middle">the technique that fixes it</text>
<rect class="bx2" x="20" y="40" width="330" height="36" rx="6"/><text class="t" x="34" y="63">1 user: read the prompt, reply token by token</text>
<rect class="bxa" x="390" y="40" width="350" height="36" rx="6"/><text class="t" x="404" y="63">prefill, then decode; KV cache keeps past work</text>
<line class="ln" x1="350" y1="58" x2="388" y2="58" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="86" width="330" height="36" rx="6"/><text class="t" x="34" y="109">50 users: each needs its own KV cache</text>
<rect class="bxa" x="390" y="86" width="350" height="36" rx="6"/><text class="t" x="404" y="109">PagedAttention: small cache blocks on demand</text>
<line class="ln" x1="350" y1="104" x2="388" y2="104" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="132" width="330" height="36" rx="6"/><text class="t" x="34" y="155">short answers wait for the longest one</text>
<rect class="bxa" x="390" y="132" width="350" height="36" rx="6"/><text class="t" x="404" y="155">continuous batching: join and leave every step</text>
<line class="ln" x1="350" y1="150" x2="388" y2="150" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="178" width="330" height="36" rx="6"/><text class="t" x="34" y="201">a long pasted document stalls everyone</text>
<rect class="bxa" x="390" y="178" width="350" height="36" rx="6"/><text class="t" x="404" y="201">chunked prefill: process the prompt in slices</text>
<line class="ln" x1="350" y1="196" x2="388" y2="196" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="224" width="330" height="36" rx="6"/><text class="t" x="34" y="247">every request repeats the system prompt</text>
<rect class="bxa" x="390" y="224" width="350" height="36" rx="6"/><text class="t" x="404" y="247">prefix caching: reuse an exactly matching start</text>
<line class="ln" x1="350" y1="242" x2="388" y2="242" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="270" width="330" height="36" rx="6"/><text class="t" x="34" y="293">the weights take too much memory</text>
<rect class="bxa" x="390" y="270" width="350" height="36" rx="6"/><text class="t" x="404" y="293">quantization: fewer bits per weight</text>
<line class="ln" x1="350" y1="288" x2="388" y2="288" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="316" width="330" height="36" rx="6"/><text class="t" x="34" y="339">generating the answer is still slow</text>
<rect class="bxa" x="390" y="316" width="350" height="36" rx="6"/><text class="t" x="404" y="339">speculative decoding: draft, then verify</text>
<line class="ln" x1="350" y1="334" x2="388" y2="334" marker-end="url(#e2k)"/>
<rect class="bx2" x="20" y="362" width="330" height="36" rx="6"/><text class="t" x="34" y="385">how do we know it got better?</text>
<rect class="bxo" x="390" y="362" width="350" height="36" rx="6"/><text class="t" x="404" y="385">measure TTFT, inter-token latency, throughput</text>
<line class="ln" x1="350" y1="380" x2="388" y2="380" marker-end="url(#e2k)"/>
</svg>
```

Read it top to bottom as one story. Each row is a new problem that appears as traffic grows, and the technique on the right is the standard fix. If you can tell this story in order, you can answer most inference interview questions. Each card below explains one of these terms in plain words.
