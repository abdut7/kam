## LLM Transformer Architecture [Core]

> Interviewers ask you to draw a transformer to find out whether "it predicts the next token" rests on a real mental model. A weak answer lists words (attention, embeddings, layers) with no order and no purpose. A strong answer draws the path from tokenizer to sampling, says what each block reads and writes, explains why attention is scaled and masked, and connects modern choices (RoPE, grouped-query attention, SwiGLU, mixture of experts) to what you pay for when the model is served. This section is the architecture view; the GPU side of prefill and decode lives in the Inference track.

### In plain words
Picture a sentence written across a long whiteboard, one word per column, and a team that improves the notes under every column in rounds. In each round, every column first holds a short meeting where it may look only at itself and the columns to its left, and it copies over whatever is useful. Then each column does desk work alone, rethinking its own notes without talking to anyone. Notes are always added to, never wiped, so what earlier rounds learned is kept. The routine is the same in every round, but each round has its own trained skills, and the team repeats it dozens of times. After the last round, the notes under the final column are turned into a score for every word in the dictionary, one word is picked and written in a new column, and the whole process runs again. Columns are token positions, the whiteboard notes are the residual stream, the meeting is masked self-attention, the desk work is the feed-forward network, one round is a decoder block, and the final scoring is the LM head followed by softmax and sampling.

### Walkthrough: one token through a decoder-only transformer
1. **tokenizer**: The input text is split into subword pieces from a fixed vocabulary learned before training (usually byte-pair encoding), so "unbelievable" may become two or three pieces.
2. **token IDs**: Each piece is replaced by its integer index in the vocabulary; the model only ever sees this list of integers, never characters.
3. **embedding table**: Each ID selects one row of a learned matrix of shape vocabulary size × d_model, giving one vector per position. That vector starts the residual stream, the running representation that every later layer reads from and adds to.
4. **decoder block**: The stream passes through N decoder blocks that share one design but each have their own weights (Llama 3 8B uses 32). Each block reads the residual stream and writes an update back into it; steps 5 to 8 happen inside every block.
5. **RMSNorm**: Before each sublayer, the vector is rescaled to a stable size (divided by its root mean square, then multiplied by a learned gain), so values neither blow up nor vanish across a deep stack.
6. **masked multi-head self-attention** with **RoPE**: Each position builds query, key and value vectors, RoPE rotates the queries and keys by an angle set by position, and each position takes a weighted mix of the values of itself and earlier positions. This is the only step where information moves between positions, and the causal mask stops any position from seeing the future.
7. **residual connection**: The attention output is added to the stream (`x = x + attention(norm(x))`) rather than replacing it, so the block makes an edit, not a rewrite.
8. **feed-forward network (SwiGLU)**: After a second RMSNorm, each position goes through the same MLP that widens the vector, applies a gated nonlinearity and narrows it back, and a second residual connection adds the result. Attention mixes information across positions; the feed-forward network transforms each position on its own and holds most of a dense model's parameters. In a **mixture of experts (MoE)** model this sublayer is replaced by many expert MLPs and a router that sends each token to a few of them.
9. **final norm** and **LM head**: After the last block, a final RMSNorm is applied and the LM head (a d_model × vocabulary matrix, sometimes tied to the embedding table) turns each position's vector into **logits**, one raw score per vocabulary token. During generation only the last position's logits are used.
10. **softmax and sampling**: Softmax converts the logits into probabilities, the sampler applies greedy choice, temperature or top-p, and the chosen token ID is appended to the input so the next step can run.

### Walkthrough: inside self-attention
1. **Input**: The sublayer receives a matrix X with one row per position (T rows, d_model columns), already normalized by RMSNorm.
2. **Project to Q, K, V**: X is multiplied by three learned matrices W_Q, W_K and W_V. A query says "what am I looking for", a key says "what do I contain", and a value is "what I hand over if chosen".
3. **Split into heads**: Q, K and V are cut into h heads of size d_k (usually d_model / h), and RoPE rotates each head's queries and keys by position. Each head runs attention independently, so different heads can track different relations.
4. **Scores**: For each head, scores = Q times K transposed, divided by sqrt(d_k). The result is a T × T table where row i, column j says how relevant position j is to position i.
5. **Causal mask**: Every score where j is later than i is set to minus infinity, so a position can attend only to itself and earlier positions.
6. **Softmax**: Each row goes through softmax, turning scores into weights between 0 and 1 that sum to 1; masked entries become exactly 0.
7. **Weighted sum of V**: Each position's head output is its row of weights times V, a blend of the value vectors it chose to look at.
8. **Concat heads**: The h head outputs are placed side by side to get back a T × d_model matrix.
9. **Output projection**: A learned matrix W_O mixes the heads together, and the result is added to the residual stream through the residual connection.
10. **Grouped-query attention (GQA)**: Most current open models let several query heads share one key and value head; Llama 3 8B has 32 query heads and 8 KV heads. Quality stays close to full multi-head attention while the KV cache shrinks by the sharing factor (4x in that example), which makes GQA the common way to shrink the cache; multi-query attention is the extreme case with a single KV head.

### Walkthrough: prefill, decode and the KV cache
1. **Request arrives**: The prompt goes through the tokenizer to become token IDs; nothing has been computed for it yet.
2. **Prefill**: All prompt positions go through every decoder block in one parallel pass; the causal mask makes this give the same result as feeding them in one at a time.
3. **Fill the cache**: In every layer, the K and V vectors of every prompt position are written to that layer's KV cache. Queries are not stored, because only the newest position will ever ask a new question.
4. **First token**: The logits at the last prompt position go through softmax and sampling to produce the first output token; the wait until this point is the time to first token.
5. **Decode step**: Only the newly sampled token goes through the stack. In each layer it computes its own Q, K and V, attends with its Q over the cached K and V plus its own, and appends its K and V to the cache.
6. **Repeat**: Decode loops one token at a time until an end-of-sequence token, a stop string or max_tokens. The cache grows by one entry per layer per token, which is why long conversations cost memory; without it, every step would recompute the whole prefix.

### Concepts you must understand
- A decoder-only LLM is four pieces: an embedding table, a stack of N decoder blocks with one shared design, a final norm, and an LM head that produces logits over the vocabulary; sampling, stop rules and tool-call parsing are code around the network.
- The residual stream is the d_model-wide vector at each position that every sublayer reads, normalizes and adds an update to; it is the shared bus of the network and the reason deep stacks still train.
- Attention is the only place tokens exchange information, and the feed-forward network processes each position alone; in a dense model the feed-forward layers hold about two thirds or more of the block parameters.
- The causal mask lets training compute the next-token loss at every position of a sequence in one parallel pass, and it forces generation to proceed one token at a time.
- Multi-head attention runs several smaller attentions in parallel; grouped-query attention shares K and V across groups of query heads, which is the main architectural lever on KV cache size.
- Attention without position information treats the input as an unordered set; RoPE adds order by rotating queries and keys so their dot product depends on the distance between positions.
- Llama-style blocks use pre-norm RMSNorm, SwiGLU feed-forward layers and RoPE, and usually drop bias terms, while the original 2017 design used post-LayerNorm, ReLU and sinusoidal positions.
- Parameter count is arithmetic on the config: per dense block, 2 × d_model² for W_Q and W_O, plus W_K and W_V sized by the KV heads, plus 3 × d_model × d_ff for SwiGLU, then vocabulary × d_model for embeddings (twice if the LM head is not tied).
- A mixture of experts layer swaps the single feed-forward network for many experts and a router, so total parameters (memory) and active parameters (compute per token) become two different numbers.
- Logits are unnormalized scores and softmax and sampling sit after the network, which is why temperature or top-p change outputs without touching any weights.

| Family | Attention pattern | Typical models | Used for |
|---|---|---|---|
| Encoder-only | Bidirectional: every token sees every other token | BERT, RoBERTa, DeBERTa | Understanding: classification, entity extraction, embeddings, cross-encoder reranking |
| Encoder-decoder | Bidirectional encoder; causal decoder that cross-attends to the encoder output | T5, BART, Whisper | Input-to-output transforms: translation, summarization, speech to text |
| Decoder-only | Causal: each token sees itself and earlier tokens | GPT, Llama, Qwen, Mistral | Generation: chat, code, tool use, agents |

### Q. Draw a decoder-only transformer and explain each block.
**Short answer (45 seconds):** A tokenizer turns text into token IDs, each ID looks up a vector in the embedding table, and that vector enters the residual stream. The stream passes through N decoder blocks, each doing RMSNorm, masked multi-head self-attention with RoPE and a residual add, then RMSNorm, a SwiGLU feed-forward network and another residual add. A final norm and the LM head turn the last position into logits; softmax and sampling pick the next token, and the loop repeats.

**Deeper explanation:**

```text
text
 -> tokenizer -> token IDs -> embedding table    (start of residual stream x)
 -> decoder block, repeated N times:
      x = x + masked_attention(RMSNorm(x))       (mixes positions, RoPE on Q and K)
      x = x + ffn_swiglu(RMSNorm(x))             (each position alone; MoE swaps this)
 -> final norm -> LM head -> logits
 -> softmax and sampling -> next token, appended, repeat
```

Two points to make while you draw. The block is the unit: models differ mostly in N, d_model, head counts and feed-forward width, so a 70B Llama is the 8B drawing with bigger numbers. And the residual adds mean each block edits the stream rather than replacing it.

Name the modern defaults: pre-norm RMSNorm instead of post-LayerNorm, RoPE instead of learned absolute positions, SwiGLU instead of ReLU or GELU, grouped-query attention to shrink the KV cache, and in many large models a mixture of experts layer in place of the dense feed-forward network.

**Follow-ups they will ask:**
- Where do most parameters live?: In the feed-forward layers; in small models with big vocabularies, the embedding table and LM head take a large share.
- Why tie the LM head to the embeddings?: One shared matrix saves vocabulary × d_model parameters, which matters most in small models.
- What does the network output in training?: Logits at every position, each scored against the true next token with cross-entropy.

**Mistakes to avoid:**
- Drawing the 2017 encoder-decoder figure when the question is about GPT-style models.
- Leaving out the residual connections; without them you cannot explain the residual stream or how a deep stack trains.

### Q. How does self-attention work, step by step, and why divide by sqrt(d_k)?
**Short answer (45 seconds):** Each position projects its vector into a query, a key and a value. Its query is dotted with the key of every allowed position, the scores are divided by sqrt(d_k), future positions are masked, softmax turns scores into weights, and the output is the weighted sum of values. Several heads do this in parallel and an output projection mixes them. Dividing by sqrt(d_k) keeps scores at a stable scale so softmax does not saturate into a near one-hot distribution with vanishing gradients.

**Deeper explanation:** If the components of q and k have mean 0 and variance 1, their dot product over d_k dimensions has variance d_k, so a head of size 128 gives scores with a standard deviation around 11. Softmax over numbers that large puts almost all weight on one position and starves the rest of gradient. Dividing by sqrt(d_k) brings the variance back to about 1.

```python
import numpy as np

def causal_attention(x, Wq, Wk, Wv):
    q, k, v = x @ Wq, x @ Wk, x @ Wv
    scores = q @ k.T / np.sqrt(q.shape[-1])       # (T, T)
    future = np.triu(np.ones_like(scores, dtype=bool), k=1)
    scores = np.where(future, -np.inf, scores)    # causal mask
    scores -= scores.max(axis=-1, keepdims=True)  # stability
    w = np.exp(scores)
    w /= w.sum(axis=-1, keepdims=True)            # softmax per row
    return w @ v, w

rng = np.random.default_rng(0)
x = rng.normal(size=(4, 8))
out, w = causal_attention(x, *(rng.normal(size=(8, 8)) for _ in range(3)))
print(np.round(w, 2))  # lower-triangular, rows sum to 1
```

FlashAttention computes this same math in tiles without storing the T × T matrix: a memory optimization, not a new algorithm.

**Follow-ups they will ask:**
- Why several heads instead of one wide one?: Each head has its own projections, so heads learn different relations at the same total cost.
- Why is attention quadratic?: The score table is T × T per head, so prefill work grows with the square of prompt length.

**Mistakes to avoid:**
- Saying the scaling is "for normalization" without the variance argument.
- Forgetting that softmax runs per query row, not over the whole matrix.

### Q. Why do transformers need positional information, and what does RoPE do?
**Short answer (45 seconds):** Attention compares queries with keys by dot product, and nothing in that math knows which token came first, so without position information "dog bites man" and "man bites dog" look alike. Models therefore inject position. RoPE, used by Llama, Qwen and Mistral, rotates each query and key by an angle proportional to its position, so the score between two tokens depends on how far apart they are, not on their absolute positions.

**Deeper explanation:** Older designs added a position vector to the token embedding: fixed sinusoids in the original Transformer, a learned table in GPT-2 and BERT, which has no entry past its trained length. RoPE works inside attention instead. It splits each head's query and key into pairs of dimensions and rotates pair i by position × θ_i, with θ_i from a geometric series of frequencies (base 10000 in the original paper). The score between positions m and n then depends only on their contents and on m minus n: relative position with no extra parameters. Values are not rotated, because position should shape who attends to whom, not what is handed over.

```text
score(m, n) = rotate(q, m) · rotate(k, n) = f(q, k, m - n)
```

Context extension builds on this: position interpolation, NTK-aware scaling and YaRN rescale the angles, often with a larger RoPE base and continued training on long sequences. ALiBi, used in BLOOM, skips rotation and subtracts a distance-based penalty from the scores.

**Follow-ups they will ask:**
- Does RoPE let a model handle any length?: No; quality drops past the lengths it was trained or extended on, even though the math still runs.
- Does RoPE affect the KV cache?: Keys are cached after rotation, so each entry already carries its position.
- Can a causal model learn order without explicit positions?: Partly, since the mask leaks order, but production models rely on explicit positions.

**Mistakes to avoid:**
- Saying RoPE adds a vector to the embedding; it rotates queries and keys inside every attention layer.
- Claiming a longer context window is just a config change.

### Q. What is the role of the feed-forward layer, residual connections and normalization?
**Short answer (45 seconds):** The feed-forward network is a per-position MLP that widens each vector, applies a nonlinearity and projects back; it holds most of the weights, while attention only moves information between positions. Residual connections add each sublayer's output to its input, so the network learns small edits to a shared residual stream and gradients get a direct path through dozens of layers. Normalization, now usually pre-norm RMSNorm, keeps each sublayer's input at a stable scale so deep stacks train without diverging.

**Deeper explanation:**

```python
# pseudocode for one pre-norm decoder block (Llama style)
def block(x):
    x = x + attention(rms_norm(x, g1))  # mixes across positions
    x = x + swiglu(rms_norm(x, g2))     # each position on its own
    return x

def rms_norm(x, g, eps=1e-6):
    return x / sqrt(mean(x * x) + eps) * g

def swiglu(x):
    return W_down @ (silu(W_gate @ x) * (W_up @ x))
```

SwiGLU uses three matrices: a gate branch passed through SiLU multiplies an up branch elementwise, and a down matrix projects back to d_model. The hidden width is usually chosen so the three cost roughly what the older two-matrix layer with 4x expansion did. Interpretability research suggests feed-forward layers store many factual associations, a useful intuition rather than a settled mechanism.

The residual stream is a shared bus: every block reads it and writes back, so later layers use what earlier ones wrote. RMSNorm divides by the root mean square and multiplies by a learned gain, skipping LayerNorm's mean subtraction and bias: cheaper, with similar results. Pre-norm replaced post-norm because it trains deep stacks more stably.

**Follow-ups they will ask:**
- Must attention and the feed-forward network run in sequence?: No; GPT-J and PaLM run them in parallel from one normalized input, but sequential is the common form.
- What happens without residuals?: Gradients must pass through every layer's transformation, and deep stacks become very hard to train.

**Mistakes to avoid:**
- Calling the feed-forward layer "just a small MLP"; it holds most of a dense model's parameters.
- Confusing LayerNorm with BatchNorm; transformers normalize each token's vector, not across the batch.

### Q. What is a mixture of experts layer, and what does it change for training and serving?
**Short answer (45 seconds):** A mixture of experts layer replaces the single feed-forward network in a block with many expert feed-forward networks and a small router. For each token, the router scores the experts, sends the token to the top few, and combines their outputs using the router weights. Each token uses only a fraction of the parameters, so compute per token follows active parameters while memory follows total parameters.

**Deeper explanation:** Mixtral 8x7B has 8 experts per layer and routes each token to 2, for about 47B total and 13B active parameters. DeepSeek-V3 reports 671B total and 37B active, with an always-on shared expert next to many routed ones. Routing is per token and per layer, and experts specialize on token patterns rather than human topics, so there is no reliable "math expert".

```text
token vector -> router -> scores for E experts -> top-k (say 2)
             -> w_a * expert_a(x) + w_b * expert_b(x) -> residual add
```

Training: the router can collapse onto a few favourite experts, so training adds a load-balancing loss (DeepSeek-V3 uses a bias-based scheme instead), and a capacity factor caps tokens per expert, which can drop tokens when an expert is full. Large runs need expert parallelism, with all-to-all communication sending tokens to the GPUs holding their experts.

Serving: every expert must sit in GPU memory, so Mixtral needs memory for all 47B parameters while computing like a 13B model. In a large decode batch, different tokens hit different experts, so most expert weights are read every step anyway. MoE pays off at high throughput on multi-GPU servers, less on one small GPU.

**Follow-ups they will ask:**
- Is MoE cheaper per token than a dense model of the same total size?: Yes in compute, no in memory.
- What is load imbalance at serving time?: One hot expert becomes the straggler that sets the step time for the batch.

**Mistakes to avoid:**
- Saying an 8-expert model "is 8 models"; experts are per-layer feed-forward networks sharing attention, embeddings and the residual stream.
- Sizing GPUs by active parameters.

### Q. Encoder-only, encoder-decoder and decoder-only: when is each used?
**Short answer (45 seconds):** Encoder-only models such as BERT use bidirectional attention, so every token sees the whole input; they are built for understanding tasks such as classification, entity extraction, embeddings and reranking, not for writing text. Encoder-decoder models such as T5 read the input with a bidirectional encoder and generate with a causal decoder that cross-attends to it, a natural fit for translation, summarization and speech to text. Decoder-only models such as GPT, Llama and Qwen use one causal stack and dominate generation, chat and tool use.

**Deeper explanation:** The real differences are the attention mask and the training objective. BERT is trained to fill in masked tokens, which gives two-way context but no natural way to write left to right. T5 is trained to reconstruct corrupted spans, and its decoder cross-attends: decoder queries look at the encoder's keys and values, so the input is encoded once and the output is generated against it. Decoder-only won for general models because one next-token objective scales on any text, any task can be phrased as a prompt, and the KV cache makes serving efficient.

It still matters in product work. A small fine-tuned encoder classifies or embeds text in milliseconds, often on a CPU, and is frequently better per dollar than prompting an LLM for a fixed label set. Many embedding models and cross-encoder rerankers in RAG pipelines are encoder-style, though several strong recent embedding models are built from decoder-only LLMs. Whisper is encoder-decoder over audio. For open-ended text, instruction following or tool calls, use a decoder-only model.

**Follow-ups they will ask:**
- Can a decoder-only model produce embeddings?: Yes, by pooling hidden states (often the last token's) after contrastive fine-tuning.
- What is a cross-encoder?: An encoder that reads query and document together and outputs one relevance score, more accurate than comparing separate embeddings but run once per pair.

**Mistakes to avoid:**
- Saying BERT "generates" answers; it scores or labels its input.
- Using a large decoder model for a fixed five-label classification at high volume without benchmarking a fine-tuned encoder.

### Practice
- Count parameters by hand for Llama 3 8B (32 layers, d_model 4096, 32 query heads and 8 KV heads of size 128, SwiGLU width 14336, vocabulary 128256, untied LM head): per layer 2 × 4096² + 2 × 4096 × 1024 for attention and 3 × 4096 × 14336 for the feed-forward network, times 32, plus two 128256 × 4096 matrices. You should land near 8.0B; then load GPT-2 small and confirm about 124M with `sum(p.numel() for p in model.parameters())`.
- Clone Karpathy's nanoGPT, run `python data/shakespeare_char/prepare.py` and `python train.py config/train_shakespeare_char.py` (add `--device=cpu --compile=False` and smaller sizes on a laptop, or `--device=mps` on Apple silicon), then `python sample.py --out_dir=out-shakespeare-char`. Read `model.py`, match each class to the walkthrough, and list what you would change to make its GPT-2 style block (LayerNorm, GELU, learned positions) Llama style.
- Load GPT-2 with Hugging Face `transformers` using `attn_implementation="eager"` so attention weights are returned, run a sentence with `output_attentions=True`, and print one head's weight matrix to see the causal triangle; then run the numpy sketch above and compare the shape.
- Say it out loud: draw the decoder-only stack from tokenizer to sampling in under two minutes, naming what each block reads and writes, then explain where GQA and MoE change the serving bill.

## Jev: Decision-Layer Model Architecture [New]

> Decision layers come up when interviewers probe agent design: who decides which tool runs, and with what confidence. The Codebasics AI Engineering bootcamp teaches Jev next to Semantic Router for this "decision layer" job, so expect the comparison. A weak answer is "the LLM decides and calls the tool". A strong answer separates the agent's proposal, a typed decision with probabilities, thresholds, deterministic checks and execution, keeps vendor claims apart from measured results, and says plainly that Jev's internal architecture is not public. Facts about Jev here come from TypeSafe's documentation and integration docs as checked on 1 November 2026; anything marked as a TypeSafe claim is the vendor's statement, not an independent result.

### In plain words
An LLM is like an essay writer: ask it something and it writes whatever it thinks fits, in its own words and at its own length. Jev, a model from TypeSafe AI, is more like a multiple-choice examiner: you print the question and the allowed answers on the sheet, and it must tick one of them and note how sure it is, for example 92 percent on option B. Because the answer is always one of the options you printed, your code can branch on it directly instead of parsing prose. You can hand it several questions about the same case at once, and it answers each one separately. The examiner never acts on its answers: your application reads the sheet, applies its own rules and decides what happens. Like any examiner it can be confidently wrong, so you mark its answers against your own answer key before trusting them.

### Walkthrough: one routing decision with Jev
1. **User message**: A customer writes "my order never arrived, refund me" to a support agent built on an LLM.
2. **Agent proposal**: The LLM agent reads the conversation and proposes a next step, here a call to the `refund_order` tool with an order ID and an amount.
3. **Schema validation**: The application checks the proposed tool call against the tool's JSON schema first; a malformed call is rejected before any decision is spent on it.
4. **Build the state**: The application assembles the state for Jev as text: the conversation as a transcript plus the relevant order facts as JSON, with personal data the decision does not need removed.
5. **Ask Jev**: It sends one request with several named questions about that state, for example a Choice question `next_step` (continue, call tool, finish, ask user, escalate) and a Noul question "the customer explicitly asked for a refund", against a pinned model version.
6. **Typed answers**: Jev evaluates the questions independently and returns, for each, a typed answer with probabilities, which your code validates against the options it sent.
7. **Thresholds**: The application maps the answers to an action with its own thresholds, for example ALLOW when `next_step` is call tool with high confidence and the Noul value is high, REVIEW in a middle band, and DENY below it.
8. **Hard checks**: Deterministic code then checks authorization (does this user own this order) and policy (refund limit, order state). These checks can veto an ALLOW but never upgrade a DENY.
9. **Execute or hand off**: Only the application acts: it calls the refund tool on ALLOW, routes the case to a human queue on REVIEW, and tells the agent to ask the user or escalate on DENY. Jev never executes anything.
10. **Audit log**: The application records a reference to the state, the questions, the pinned model version, answers, probabilities, the threshold config version, the final action and the later outcome, which feeds shadow comparisons and recalibration.

### Walkthrough: anatomy of a Jev request and response
1. **Endpoint and key**: Your server sends a POST to `/v1/systemone` on `api.typesafe.ai`, with the API key read from an environment variable such as `TYPESAFE_API_KEY` and never shipped to browser code. Integrations also exist for LangChain4j (`DecisionRequest`, `ChoiceQuestion`, `YesNoQuestion`, `ScaleQuestion`, `decide`), the Vercel AI SDK, TanStack AI, Bifrost and OpenRouter.
2. **Model version**: The request names a pinned version such as `jev-1.13.0`; the alias `jev-latest` can move to a new model, so it belongs in experiments, not production.
3. **State**: One piece of state that every question is about: plain text, JSON, or a conversation passed as a transcript. It is text only, so images must be described in text first or decided elsewhere.
4. **Named questions**: One or more questions, each with a name you choose (`next_step`, `refund_requested`, `frustration`), so answers come back keyed and your code never depends on ordering.
5. **Choice question**: You supply the options, each with a key and a description; the answer is the chosen key, a probability per option and a confidence.
6. **Score question**: You define an ordered rubric of levels (for example calm, annoyed, angry); the answer is a score on that rubric, a probability per level and a confidence.
7. **Noul question**: You supply one statement; the answer is a value from 0 to 1, read as the probability that the statement is true.
8. **Parallel evaluation**: Jev evaluates every question independently and in parallel against the same state; TypeSafe says adding questions barely changes latency, which you should measure on your own payloads.
9. **Validate the response**: Your code parses the response with a schema (zod in TypeScript, pydantic in Python), checks that every returned key is one you sent and every probability is in range, and treats anything else as a failure that falls back to a safe default.

### Concepts you must understand
- A decision model answers questions you define about a piece of state and returns structured answers from a closed set, while a generative LLM writes open-ended text that you then parse and police.
- TypeSafe calls Jev a "System One" model: it answers typed questions about state instead of generating text, through three question types, Choice, Score and Noul.
- Every request is one state plus named questions evaluated independently, so TypeSafe's docs recommend atomic questions: for a multi-factor judgment, ask one question per factor and combine the answers in code.
- A decision layer sits between the agent and its tools: the agent proposes, the decision model judges, and the application decides and executes.
- "A probability is not a permission" (from the AWS Builder Center article on this placement): thresholds, schema validation, authorization and hard policy checks are application code and can override any model answer.
- Calibration means that among cases scored around 0.8, about 80 percent turn out correct; TypeSafe says Jev's probabilities are calibrated, and you confirm that on your own labelled data with a reliability curve or expected calibration error.
- Thresholds are product decisions driven by error costs: a wrongly allowed refund costs more than a wrongly queued one, so the ALLOW threshold sits high and the uncertain band below it goes to review instead of straight to execution.
- Pin the model version (`jev-1.13.0`, not `jev-latest`) and re-run your evaluation before moving the pin, as with any dependency upgrade.
- TypeSafe has not published Jev's internal architecture (size, training, layers); anything said about its internals is general background on how decision models are commonly built, not Jev's documented design.
- TypeSafe's speed and cost advantages over frontier LLMs are vendor claims; latency, cost and accuracy on your traffic are numbers you measure yourself.

| Approach | Output | Typical failure mode | Latency profile | When to use |
|---|---|---|---|---|
| Generative LLM (tool call or structured output) | Free text or JSON you parse; probabilities only through logprobs, where exposed | Off-schema or inconsistent answers, overconfident prose, steered by injected text in the input | Network call that grows with prompt length and output tokens | Open-ended reasoning and situations where the options cannot be listed ahead of time |
| Embedding router (Semantic Router) | Best-matching route and a similarity score | Matches surface wording, misses negation and earlier turns, and similarity is not a calibrated probability | One embedding call plus a vector comparison; can run fully local | Fast first-pass intent routing over a stable set of routes with example utterances |
| Fine-tuned classifier | Label from a fixed set with model scores | Needs labelled data and retraining when labels change; drifts silently | One forward pass of a small self-hosted model | High-volume, stable label sets where you own the data and the infrastructure |
| Decision model (Jev) | Typed answer per named question from options you supply, with probabilities and confidence | Confidently wrong inside the allowed set; vendor dependency; calibration may not transfer to your domain | One vendor API round trip; TypeSafe claims it is much faster and cheaper than frontier LLMs | Judgments over rich state (transcripts, JSON) where options change without retraining and probabilities drive thresholds |

### Q. What is Jev, and how is a decision model different from a generative LLM?
**Short answer (45 seconds):** Jev is a model from TypeSafe AI that it calls a "System One" model. Instead of generating text, it takes a piece of state, such as a conversation or JSON, plus named questions you define, and returns typed answers with probabilities: a choice from your options, a score on your rubric, or a 0 to 1 value for whether a statement is true. A generative LLM can say anything, so you parse and police its output; a decision model answers only inside the set you gave it.

**Deeper explanation:** The difference is the output contract. With an LLM, "pick one of these five routes" is a request it usually honors; you still need structured outputs, retries and a fallback for off-list answers, and confidence only if the provider exposes logprobs. With Jev the option set is part of the API, and TypeSafe says the probabilities are calibrated.

On internals, be plain: TypeSafe has not published Jev's architecture, size or training. As general background, not Jev's documented design, constrained decision models are commonly built like this:

```text
general pattern, not Jev's documented design
state + question + option descriptions -> transformer reads them together
  -> scoring head: one score per option you supplied
  -> softmax over only those scores -> distribution that cannot leave the set
  -> calibration checked offline with reliability curves or ECE
```

With the softmax over only the supplied options, an out-of-set answer is impossible by construction, unlike a generative model whose softmax spans the whole vocabulary. That guarantees the shape of the answer, not its correctness.

**Follow-ups they will ask:**
- What do the three question types return?: Choice returns a choice, probabilities and confidence; Score returns a score, per-level probabilities and confidence; Noul returns a 0 to 1 probability of yes.
- Can it read images?: No; per TypeSafe's docs the state is text only.

**Mistakes to avoid:**
- Inventing a parameter count or training story for Jev; say it is not published.
- Treating "always one of my options" as "always right"; add an explicit "unclear" or "none of these" option.

### Q. Where does a decision model sit in an agent architecture, and what must stay outside it?
**Short answer (45 seconds):** Between the LLM or agent and the tools. The agent proposes a step, the decision model answers typed questions about that step and the state, and the application maps the answers through thresholds to an action such as CONTINUE, CALL TOOL, FINISH, ASK USER or ESCALATE, or for a tool call ALLOW, REVIEW or DENY. The model never executes anything; execution, schema validation, authorization and hard policy checks stay in deterministic code around it.

**Deeper explanation:** This placement comes from an AWS Builder Center article (a community article, not an AWS endorsement), and it matches how you would design any risky automation: separate judgment from permission.

```text
user -> agent (LLM) proposes a step
     -> schema validation             (deterministic, rejects malformed calls)
     -> Jev: named questions on state (judgment, returns probabilities)
     -> threshold map                 (your config: ALLOW / REVIEW / DENY)
     -> authorization + hard policy   (deterministic, can only veto)
     -> tool executor                 (only the app executes)
     -> audit log                     (inputs, version, answers, action)
```

The line to quote is that a probability is not a permission. A 0.97 that the user asked for a refund says nothing about whether this user may refund this order, whether the amount is under the limit, or whether it was already refunded; those are facts in your database, checked by code. The state also contains user text, and any model reading untrusted text can be nudged by it, so checks guarding money, data and irreversible actions must not depend on a model answer. Idempotency keys, rate limits and human approval live outside too.

**Follow-ups they will ask:**
- Why not let the agent call tools directly?: You lose the one place to apply thresholds, log decisions and stop a bad call before it runs.
- Does this add latency?: One extra call per gated step, so gate the risky tools and let read-only tools run directly.

**Mistakes to avoid:**
- Letting a high probability skip authorization.
- Logging only the final action; without inputs, version and probabilities you cannot debug or recalibrate.

### Q. How would you route requests between tools or models using Jev, Semantic Router or an LLM, and how do you choose?
**Short answer (45 seconds):** I would layer them by cost and difficulty. An embedding router like Semantic Router handles obvious, high-volume intents cheaply by comparing the message embedding with example utterances per route. Ambiguous or state-heavy cases go to a decision model like Jev as a Choice question over the routes, with probabilities I can threshold. An LLM handles open-ended cases where the options cannot be listed ahead of time, and anything still uncertain becomes a question to the user or a human handoff.

**Deeper explanation:** The choice turns on how stateful the decision is, how often routes change, whether you need probabilities to threshold, the latency budget, and whether data may leave your network. Semantic Router is fast and can run locally, but it scores surface similarity on one message: "I do not want to cancel" can land near the cancel route, and earlier turns are ignored. A fine-tuned classifier beats it once you have many labels and stable routes. A decision model reads the whole transcript and JSON, lets you change routes by editing option descriptions, and returns probabilities, at the cost of a vendor call. An LLM is the most flexible, usually the slowest, and needs schema enforcement.

```ts
// illustrative cascade; thresholds come from your eval set
async function route(msg: string, state: string): Promise<Route> {
  const fast = await semanticRoute(msg);       // embeddings, can run local
  if (fast && fast.score >= FAST_MIN) return fast.route;
  const d = await decideRoute(state, ROUTES);  // Jev Choice question
  if (d.confidence >= DECIDE_MIN) return d.choice;
  return "ask_user";                           // never guess silently
}
```

Measure every tier on one labelled set: accuracy per route, share of traffic resolved, p95 latency and cost.

**Follow-ups they will ask:**
- Why not send everything to Jev?: You can; the cascade only pays off if the cheap tier resolves a large share accurately.
- How do you route between models instead of tools?: Same pattern, with options such as "small model" and "frontier model".

**Mistakes to avoid:**
- Treating a cosine similarity as a probability.
- Choosing a router without a labelled set to compare the options.

### Q. How do you set thresholds on a model's probabilities, and how do you check calibration?
**Short answer (45 seconds):** Start from the cost of each mistake, not a round number. Build a labelled set from real traffic, run the model, and for each candidate threshold measure how often an ALLOW would have been wrong and how much traffic would go to review. Pick an ALLOW bar that keeps wrong allows within the risk budget, a DENY bar below which you refuse, and send the middle band to review. Check calibration with a reliability curve and expected calibration error, overall and per segment.

**Deeper explanation:** Calibration asks whether the numbers mean what they say: of all decisions scored around 0.8, about 80 percent should be right. Bin predictions by confidence, compare average confidence with observed accuracy in each bin, and plot one against the other; a calibrated model lies on the diagonal. Expected calibration error (ECE) is the weighted average gap.

```python
import numpy as np

def ece(conf, correct, bins=10):
    conf, correct = np.asarray(conf, float), np.asarray(correct, float)
    idx = np.minimum((conf * bins).astype(int), bins - 1)
    return sum(
        (idx == b).mean() * abs(correct[idx == b].mean() - conf[idx == b].mean())
        for b in range(bins) if (idx == b).any()
    )
```

For a Choice question, `conf` is the confidence of the chosen option and `correct` says whether it matched the human label; for a Noul question, pass the value as `conf` and the true or false label as `correct`. TypeSafe says Jev's probabilities are calibrated; that is a vendor claim, and calibration on their data does not guarantee it on your domain. If you see a consistent bias, fit isotonic regression or Platt scaling on a held-out split, and version thresholds next to the model version they were tuned for.

**Follow-ups they will ask:**
- Why check per segment?: A model can be calibrated on average and overconfident for one language, tenant or tool.
- When do you re-tune?: On every model version change, and when accuracy measured on reviewed cases drifts.

**Mistakes to avoid:**
- Using 0.5 because it looks neutral.
- Reading accuracy alone; a model can be accurate and badly calibrated, which breaks threshold logic.

### Q. What would you need to verify before putting Jev in production?
**Short answer (45 seconds):** That it beats what I have on my own data, and that the system stays safe when it is wrong or unavailable. Concretely: pin a model version, build a labelled eval set from real traffic, run Jev in shadow mode against human labels, measure latency and cost on my own payloads, check calibration before setting thresholds, design fallbacks for API failures, and clear a privacy review for the state I send. TypeSafe's speed, cost and calibration claims are hypotheses until those numbers are in.

**Deeper explanation:**

| Check | What done looks like |
|---|---|
| Version | A pin such as `jev-1.13.0` in config, `jev-latest` banned in production, upgrades only after re-running the eval |
| Eval set | Labelled real-traffic states, including hard and adversarial cases |
| Shadow mode | Jev's answers logged next to the current decision and human labels, with no effect on users |
| Latency and cost | p50, p95 and p99 from your region with realistic state sizes; cost per decision at forecast volume |
| Calibration | Reliability curve and ECE per question and segment, thresholds set from them |
| Failure handling | Timeouts, retries with backoff, a circuit breaker, and a safe default (REVIEW or ASK USER, never ALLOW) |
| Privacy and keys | Minimized state with personal data masked, vendor retention terms reviewed, API key in a secret store |
| Lock-in | A `DecisionClient` interface so an LLM or classifier can take over |

Shadow mode is the key step: it shows where Jev disagrees with humans before any user feels it. Test the fallback path, not just write it.

**Follow-ups they will ask:**
- What do you monitor after launch?: Answer distributions, confidence drift, review-queue rate, human override rate, latency and errors.
- How do you take a new model version?: Re-run the eval and a shadow period, then move the pin with a rollback path.

**Mistakes to avoid:**
- Quoting the vendor's speed or calibration claims as your own results.
- Failing open: defaulting to ALLOW when the decision call times out.

### Practice
- Collect 150 to 300 realistic agent states with the correct next step labelled by hand, run them through Jev in shadow mode (or, without a key, through an LLM with structured output as a baseline), and compute accuracy, a reliability curve and ECE with the function above.
- Build a Semantic Router baseline with five routes and a handful of example utterances each, run the same labelled set, and list the cases where negation or earlier turns fooled it.
- Write a threshold table (ALLOW, REVIEW, DENY per tool) and a Postgres `decision_log` table holding a state hash, questions, model version, answers, probabilities, threshold version, action and outcome; then replay a week of logs against a changed threshold and count how many actions would flip.
- Say it out loud: in two minutes, explain where a decision model sits between agent and tools, what stays outside it, and what you would verify before trusting its probabilities, naming which facts are vendor claims.
