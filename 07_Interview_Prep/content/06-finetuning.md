# Fine-tuning & Model Adaptation

> This track covers how to change a model's behaviour by changing its weights instead of its prompt: when that is worth doing, the training fundamentals you need to reason about it, parameter-efficient methods (LoRA, QLoRA), the data work that decides whether it succeeds, preference optimization and RL intuition, the tooling, and how to evaluate, ship and monitor the result. For an AI Full Stack Engineer the interviewer rarely wants a research answer; they want to see that you can decide prompt vs RAG vs fine-tune on evidence, run a QLoRA job end to end on the Hugging Face stack, and put the result behind vLLM or Ollama with evals and rollback in place.

## When to Fine-tune

> Interviewers probe this to see whether you reach for fine-tuning as a reflex or as a last resort backed by measurements. A weak answer says "fine-tune so the model knows our data". A strong answer lays out the ladder (prompt, few-shot, RAG, fine-tune), names what each rung changes, explains why facts belong in retrieval and behaviour belongs in weights, and ties the decision to an eval set and a cost model.

### Concepts you must understand
- Prompting and few-shot examples change behaviour at inference time with zero training; they are cheap, reversible, and the first thing you exhaust.
- RAG injects knowledge at inference time from a store you can update in seconds; it is the right tool for facts that change or that must be cited.
- Fine-tuning changes the weights, which changes the model's default behaviour: style, format, tool-call discipline, domain vocabulary, and what it does when given no instructions at all.
- Fine-tuning is poor at adding fresh or long-tail facts: a few thousand examples barely move factual recall, and the model hallucinates confidently when it has half-learned something.
- The biggest cost of a fine-tuning project is usually data (collection, cleaning, labelling, evals), not GPU hours; a QLoRA run on an 8B model is hours on one GPU.
- A smaller fine-tuned model can replace a large general model for a narrow task, which is where the latency and cost wins come from.
- RAG and fine-tuning compose: fine-tune the model to use retrieved context well (cite, ignore distractors, answer in your format) and keep the facts in the index.
- The decision is only defensible with an eval set: you fine-tune when the prompt-plus-RAG baseline has hit a measurable ceiling on that set.

### Q. When would you fine-tune instead of writing a better prompt or adding retrieval?

**Short answer (45 seconds):** I climb a ladder: prompt, few-shot examples, RAG for anything factual, and fine-tuning only when an eval set shows the prompted baseline has plateaued on a behaviour problem rather than a knowledge problem. Typical triggers are strict output format, tool-call reliability, a consistent voice, domain vocabulary the base model mangles, or needing a small cheap model to match a large prompted one.

**Deeper explanation:** Each rung changes a different thing. A prompt changes the instructions the model sees, RAG changes the evidence it sees, fine-tuning changes what it does by default. "It does not know X" is a knowledge gap: retrieval fixes it in minutes with no training. "It knows but misses the schema one time in twenty, or drifts off brand" is a behaviour gap: prompt text never makes that fully reliable, while a few hundred to a few thousand good examples usually do.

```text
Failure on the eval set        First fix              Fine-tune when
"does not know our data"       RAG                    almost never for the facts
"schema or format misses"      prompt + examples      misses persist after prompt work
"wrong tone or verbosity"      system prompt          consistency needed at scale
"too slow or too costly"       caching, small model   small model fails prompted, passes tuned
```

The other legitimate trigger is economics: a large model behind a long prompt works, but you want a 3B to 8B model to do the same narrow job faster and cheaper. That is distillation in practice: generate training data with the big model, fine-tune the small one, and verify on the same eval set.

**Follow-ups they will ask:**
- How do you know the prompt has plateaued?: Score several prompt variants on a fixed eval set; when the best one stops improving and the remaining failures are behavioural, that is the ceiling.
- Does fine-tuning remove the system prompt?: No, it shortens it; you still pass task context and retrieved facts.
- Cheapest useful fine-tune?: A LoRA on a small open model with a few hundred curated examples for one format or one tool schema.

**Mistakes to avoid:**
- Proposing to fine-tune so the model "knows our documentation"; that is a retrieval problem and the question is testing exactly this.
- Having no baseline number: if you cannot state the prompted model's score, you cannot justify training.

### Q. What does fine-tuning change well, and what does it change badly?

**Short answer (45 seconds):** It is excellent at form and habit: output format, JSON and tool-call discipline, tone, length, domain vocabulary, and following a house style without being told. It is bad at injecting facts, especially facts that change, and it does nothing for knowledge the base model never saw in volume. Think of it as changing how the model behaves, not what it knows.

**Deeper explanation:** Supervised fine-tuning nudges the probability distribution over next tokens toward your examples. Patterns that recur across every example (the schema, the voice, the way a tool is called) get reinforced strongly because every sample votes for them. A fact that appears in one or two examples is a weak signal competing against billions of pretraining tokens; the model may paraphrase it, mix it with similar facts, or state it confidently wrong. That is why "we fine-tuned on our wiki and it still hallucinates prices" is such a common story.

Works well in practice: valid JSON against a schema, calling internal tools with the right argument shapes, answering like your support team, using medical or legal vocabulary correctly, and refusing out-of-scope requests consistently. Works badly: current inventory, policies that change quarterly, anything with a date in it, or per-customer data.

**Follow-ups they will ask:**
- Can continued pretraining add knowledge?: Yes, with large volumes of domain text (far more than instruction tuning), and the cost is real forgetting; it is a different, heavier project than SFT.
- Can fine-tuning reduce hallucination?: It can teach the model to say "not in the provided context" and to cite, which helps in RAG settings; it cannot make memorised facts reliable.
- Why does domain vocabulary help RAG?: The model writes better search queries and summaries when it uses the field's terms the way the documents do.

**Mistakes to avoid:**
- Claiming fine-tuning "adds knowledge" without qualifying the volume needed and the forgetting trade-off.
- Confusing style transfer with correctness: a model that sounds like an expert is not therefore right.

### Q. Our product documentation changes every week. Can we fine-tune a model on it so it stops hallucinating our features?

**Short answer (45 seconds):** No, that is the wrong tool. Weekly-changing facts belong in a retrieval index that you can update in seconds and cite; a fine-tune bakes a snapshot into the weights, goes stale on day one, and still hallucinates because a few passes over a document do not make recall reliable. Where fine-tuning helps here is teaching the model to answer strictly from retrieved context and to say when the context does not cover the question.

**Deeper explanation:** Consider the operational loop. With RAG, a docs change is a re-embed of a few chunks and the next request sees it; you can trace every answer to the chunk that produced it, and you can delete a chunk when a feature is removed. With fine-tuning, every docs change is a new training run, a new eval pass, a new deployment, and you can never cleanly remove a fact from the weights. There is also no citation, so support staff cannot verify answers.

The hallucination point is subtle: SFT raises the probability of your phrasing, but factual recall from weights is probabilistic. The model will blend v2 and v3 of a feature description into something plausible. A grounded model sees the current text in context and copies from it, which is a far easier task.

```text
Docs change -> re-embed chunks -> vector store   (minutes, reversible, citable)
Docs change -> new SFT run -> eval -> deploy     (hours to days, not reversible)
```

**Follow-ups they will ask:**
- So is there any fine-tuning in this system?: Possibly a small one that teaches the answer format, the refusal rule for off-topic questions, and faithful use of context.
- How do you stop the retrieved context being ignored?: Evals that penalise unsupported claims, prompts that require quotes, and training examples where the correct answer is "the documentation does not say".
- What if the docs are small and never change?: Even then retrieval is simpler; fine-tuning only wins if the docs are tiny and latency is extreme.

**Mistakes to avoid:**
- Saying yes and describing a training pipeline; the interviewer wants you to push back.
- Forgetting that a fine-tune cannot "unlearn" a removed feature.

### Q. Walk me through the cost of a fine-tuning project. Where does the money and time actually go?

**Short answer (45 seconds):** Mostly into data and evaluation, not GPUs. Collecting, cleaning and labelling a few thousand high-quality examples plus a held-out eval set is weeks of people time; the QLoRA training run itself on an 8B model is a few hours on one GPU. After that you pay for serving, re-training when the task drifts, and the engineering to version, monitor and roll back models.

**Deeper explanation:** A rough budget, illustrative only: an 8B QLoRA run over 5,000 examples for 2 epochs is on the order of a few GPU hours on a single 24 GB to 80 GB card, which at cloud spot prices is tens of dollars. The eval set that tells you whether it worked needs a few hundred representative cases with reference answers or rubrics, usually written or reviewed by domain experts, which is where the real spend is. Synthetic data from a stronger model trades labelling cost for API cost and judge-filtering work.

Hidden costs: hyperparameter sweeps (multiply the run cost by 5 to 10), a serving GPU running 24/7 instead of a pay-per-token API, on-call for a model you own, and re-training whenever the schema, product or base model changes. Hosted fine-tuning APIs move the GPU cost into per-token training and inference prices and remove the ops burden, at the cost of control and data residency.

**Follow-ups they will ask:**
- What is the minimum viable project?: One narrow task, a few hundred examples, a 100 to 300 case eval set, one LoRA run, a side-by-side against the prompted baseline.
- When does self-hosting pay off?: When request volume is steady and high enough that a dedicated GPU is cheaper than tokens, and you already have the ops capacity.
- How do you keep re-training cost down?: Automate the pipeline (data build, train, eval, publish) so a re-run is a config change, not a project.

**Mistakes to avoid:**
- Quoting only GPU hours as "the cost".
- Ignoring maintenance: a fine-tuned model is a service you own, with drift and base-model deprecation to manage.

### Q. How would you combine RAG with a fine-tuned model?

**Short answer (45 seconds):** Keep facts in the index and behaviour in the weights. Fine-tune the model to be a good reader of retrieved context: answer only from it, cite chunk ids, ignore irrelevant chunks, and produce your output format. The retrieval layer stays independently updatable, and the fine-tune makes a small model use it as reliably as a large prompted one.

**Deeper explanation:** The training data mirrors production: each example has a question, a set of retrieved chunks (some relevant, some deliberate distractors), and a reference answer that quotes or cites only the relevant ones. The RAFT paper formalised this idea, training with an oracle document plus distractors so the model learns to discriminate rather than to summarise everything it is given. You also include examples where no chunk answers the question and the correct output is an explicit "not covered" response, because that is the behaviour prompts struggle to make reliable.

```text
Train example:
  system:    Answer using only the sources. Cite as [S1], [S2].
  user:      {question}
             [S1] {relevant chunk}  [S2] {distractor}  [S3] {relevant chunk}
  assistant: {answer citing [S1] and [S3]}
```

Operationally the fine-tuned model is swapped in behind the same retrieval pipeline, so you can A/B it against the prompted baseline with identical context. Gains show up as higher faithfulness scores, fewer refusals on answerable questions, and a shorter system prompt.

**Follow-ups they will ask:**
- Does the fine-tune need to see your real documents?: It needs the same shape and style of chunks; the specific facts can be synthetic or from a public corpus if privacy requires it.
- What breaks if retrieval changes?: Chunk size, count or formatting shifts move you off-distribution; keep the chunk format stable or re-tune.
- How do you evaluate faithfulness?: A judge model checks each claim against the provided chunks; report the unsupported-claim rate.

**Mistakes to avoid:**
- Training the model on the documents themselves and calling that "RAG plus fine-tuning".
- Training only on examples with perfect context, so the model never learns to handle distractors or empty results.

### Q. We have a 70B model behind a long prompt that works fine. Why would you fine-tune an 8B model instead?

**Short answer (45 seconds):** For latency, cost, and control. If the task is narrow, an 8B model fine-tuned on outputs from the 70B model can match it on your eval set while running several times faster on a fraction of the hardware. You also get a shorter prompt, since the instructions are now in the weights, which cuts input tokens and time to first token.

**Deeper explanation:** This is distillation by supervised fine-tuning: run the 70B teacher over a large, representative set of real or synthetic inputs, keep the outputs that pass your checks, and train the 8B student on those pairs. The student inherits the teacher's behaviour on the task distribution, not its general capability, which is exactly what you want for a routing, extraction, classification, or templated-answer workload.

Illustrative arithmetic: in bf16 a 70B model needs about 140 GB just for weights (70e9 parameters x 2 bytes), so at least two 80 GB GPUs before you count KV cache; an 8B model needs about 16 GB and fits on one mid-range card with headroom for batching. Fewer parameters also means fewer floating point operations per token, so decode speed rises roughly in proportion. The prompt shrinks from, say, 2,000 tokens of instructions and examples to a few hundred, which matters at high request volume.

**Follow-ups they will ask:**
- What do you lose?: Long-tail robustness; the student fails on inputs unlike its training data, so keep the teacher as a fallback behind a confidence or validation check.
- How many teacher samples?: Enough to cover the input distribution; measure by training on subsets and watching the eval curve flatten.
- Is it allowed to distil from a hosted model?: Check the provider's terms; some restrict using outputs to train competing models.

**Mistakes to avoid:**
- Claiming the small model becomes "as good as" the large one in general; it matches on the task you measured.
- Dropping the big model entirely with no fallback path.

### Q. What would make you decide not to fine-tune, even if the team wants to?

**Short answer (45 seconds):** No eval set, no baseline, or a problem that is really about knowledge. I also hold off when the task is still changing weekly, when the volume is too low to justify owning a model, or when the data I would train on is customer data I cannot legally or ethically bake into weights. Fine-tuning is a commitment to a maintenance loop; if the organisation cannot run that loop, prompts and RAG are the safer bet.

**Deeper explanation:** The strongest "no" is an unstable target. If product managers are still revising the output format or the tool set, every change means a re-training cycle, and the prompt version of the system will iterate ten times faster. A second "no" is scale: with a few thousand requests a day, the per-token price of a hosted model is small and a dedicated GPU plus on-call is not worth it. A third is data: if the only training examples are real customer conversations with PII and no consent for model training, the risk of memorisation and leakage is not acceptable, and synthetic stand-ins may not capture the task.

Finally, base models improve quickly. A fine-tune on today's 8B model may be beaten in six months by the next release used with a prompt, and your adapter does not transfer to a new base. That argues for keeping the data pipeline and evals as the durable asset and treating any particular fine-tuned checkpoint as disposable.

**Follow-ups they will ask:**
- How do you handle a changing format?: Keep it in the prompt until it has been stable for a couple of release cycles, then tune.
- What is the durable asset?: The curated dataset, the eval harness, and the training config; checkpoints are re-generated from those.
- Would a hosted fine-tuning API change the answer?: It removes ops cost but not the data, eval, or churn concerns.

**Mistakes to avoid:**
- Treating the question as a trap and saying you would always fine-tune if asked.
- Forgetting that adapters are tied to one base model version.

### Practice
- Build a 100-case eval set for one task you have shipped (for example, converting support emails into a JSON ticket). Score a prompted model, a prompted model with few-shot examples, and a prompted model with retrieval; write down where the curve flattens.
- Take 300 of the best outputs from a large model on that task, fine-tune a small open model with QLoRA, and compare it to the prompted baseline on the same 100 cases, including latency and cost per 1,000 requests.
- Write a one-page decision memo for a real feature: what the failure is (knowledge vs behaviour), which rung of the ladder fixes it, what it costs, and how you would roll back.
- Say it out loud: in 60 seconds, explain to a product manager why you will not fine-tune on the weekly-changing pricing docs, and what you will do instead.

## ML & Training Fundamentals for LLMs

> This section exists so that nothing in the rest of the track feels like magic. Interviewers do not expect derivations from an engineer, but they will notice if you cannot say what a loss is, why a learning rate matters, or what an epoch does to overfitting. A weak answer recites definitions; a strong one connects each knob to something you would observe in a training log and act on.

### Concepts you must understand
- A neural network is a stack of matrix multiplications with non-linear functions between them; the numbers in those matrices are the parameters, and training means adjusting them.
- An LLM is a transformer that turns tokens into vectors, mixes them with attention and feed-forward layers, and ends with a probability distribution over the next token.
- Training is a loop of forward pass, loss computation, backward pass (backpropagation computes the gradient of the loss with respect to every parameter), and an optimizer step; inference is the forward pass alone.
- The loss for language models is cross-entropy, the average negative log probability the model assigned to the correct next token; perplexity is exp(loss).
- Gradient descent moves each parameter a small step against its gradient; the learning rate sets the step size and is the single most important hyperparameter.
- Pretraining learns language and world knowledge from trillions of tokens; supervised fine-tuning teaches the model to behave like your examples; preference tuning teaches it which of two answers is better.
- An epoch is one pass over the training data; batch size is how many examples contribute to one gradient estimate; steps per epoch = examples / effective batch size.
- Overfitting is when training loss keeps falling while validation loss rises; the model memorises examples instead of learning the pattern.
- Catastrophic forgetting is when narrow fine-tuning degrades general abilities the base model had.
- Train, validation and test splits exist so that hyperparameter decisions and the final quality claim are made on data the model never trained on.

### Q. Explain in plain terms what happens inside a language model when it predicts the next token.

**Short answer (45 seconds):** Text is split into tokens, each token is looked up as a vector, and the vectors flow through a stack of identical layers. In each layer, attention lets every position pull information from earlier positions, and a feed-forward network transforms each position's vector. At the end, a final matrix maps the last position's vector to a score for every token in the vocabulary, softmax turns the scores into probabilities, and decoding picks one.

**Deeper explanation:** Concretely, for a model like Llama 3 the vocabulary has roughly 128k tokens, the hidden vector size is a few thousand numbers, and there are dozens of layers. The weights are the embedding table, the attention projection matrices (query, key, value, output), the feed-forward matrices, and the output head. Everything in the middle is linear algebra plus a few cheap non-linearities, which is why GPUs are the right hardware and why memory, not maths, is usually the constraint.

```text
tokens -> embeddings -> [attention -> feed-forward] x N layers -> logits -> softmax -> next token
```

The model does not "look things up". Knowledge is spread across the weights as statistical tendencies, so recall is probabilistic. That one fact explains why fine-tuning changes habits more easily than facts, why temperature affects answers, and why providing the fact in context (retrieval) works so much better than hoping it is in the weights.

**Follow-ups they will ask:**
- What are logits?: The raw, unnormalised scores for each vocabulary token before softmax.
- What is the KV cache?: Keys and values computed for earlier tokens are stored so each new token only attends to them instead of recomputing; it is the main memory cost at inference.
- What does temperature do?: Divides the logits before softmax; lower sharpens the distribution toward the top token, higher flattens it.

**Mistakes to avoid:**
- Describing the model as a database or search engine over its training data.
- Hand-waving "attention" without saying what it does: weighting earlier positions when building the current position's representation.

### Q. What is a loss function, and what does gradient descent actually do?

**Short answer (45 seconds):** The loss is a single number that says how wrong the model's predictions were on a batch; for language models it is cross-entropy, the average negative log probability given to the correct next token. Gradient descent computes how the loss would change if each parameter moved slightly, then moves every parameter a small step in the direction that lowers the loss. Repeat for thousands of steps.

**Deeper explanation:** For a sequence of tokens x_1 ... x_T, the loss is `L = -(1/T) * sum_t log p(x_t | x_<t)`. If the model assigned probability 0.5 to each correct token, the loss is `-log(0.5) = 0.69`; a loss of 2.0 corresponds to a perplexity of `exp(2.0) = 7.4`, meaning the model is as uncertain as if choosing among about 7 equally likely tokens (illustrative). The backward pass (backpropagation) applies the chain rule layer by layer to get the gradient of L with respect to every weight. The update is `theta = theta - lr * grad`, where lr is the learning rate.

In practice nobody uses plain gradient descent for LLMs. AdamW keeps a running average of each parameter's gradient and of its squared gradient, which normalises step sizes per parameter, and decouples weight decay (a pull toward zero that regularises). A learning rate schedule warms up from zero for a few hundred steps and then decays, often following a cosine curve.

**Follow-ups they will ask:**
- Why warm up?: Early gradients are noisy and Adam's statistics are not yet reliable; a large first step can wreck the pretrained weights.
- What does a good SFT loss curve look like?: Training loss drops quickly then flattens; validation loss tracks it and bottoms out; divergence between them is overfitting.
- Why compute the loss on assistant tokens only?: You want to learn to produce answers, not to predict the user's prompt.

**Mistakes to avoid:**
- Calling the loss "accuracy"; it is a continuous quantity over probabilities, not a count of right answers.
- Suggesting a very large learning rate "to train faster" without mentioning divergence.

### Q. What is the difference between pretraining, supervised fine-tuning and preference tuning?

**Short answer (45 seconds):** Pretraining teaches a model language and world knowledge by predicting the next token over trillions of tokens of raw text; it produces a base model that completes text but does not follow instructions. Supervised fine-tuning shows it thousands of prompt and response pairs so it learns to answer in the demonstrated way. Preference tuning then shows it pairs of better and worse answers so it learns judgements that are hard to demonstrate, like helpfulness, concision or safety.

**Deeper explanation:** The three stages share the network but differ in data and objective.

| Stage | Data | Objective | Scale (illustrative) |
| --- | --- | --- | --- |
| Pretraining | Raw web, code, books | Next-token cross-entropy | Trillions of tokens, thousands of GPUs |
| SFT | Prompt and response pairs | Cross-entropy on response tokens | Thousands to hundreds of thousands of examples |
| Preference tuning | Chosen vs rejected responses | DPO loss or RL on a reward | Thousands to tens of thousands of pairs |

In a company you almost always fine-tune the instruct variant, which the vendor has already taken through SFT and preference tuning; your SFT adds your task on top. Starting from the base model only makes sense with a lot of data, because you must also re-teach it to be an assistant.

**Follow-ups they will ask:**
- Why not just do more SFT instead of preference tuning?: SFT can only imitate what you wrote; preferences let the model learn "shorter is better here" from comparisons without a perfect reference.
- What is continued pretraining?: Next-token training on domain text (legal, medical) before SFT, to shift vocabulary and knowledge; it needs much more data than SFT.
- Does fine-tuning an instruct model undo its safety tuning?: It can weaken it, which is why you include refusal examples and run safety regressions.

**Mistakes to avoid:**
- Saying fine-tuning "retrains the model"; it is a short, small-learning-rate adjustment on top of pretraining.
- Mixing up the base and instruct checkpoints when choosing a starting point.

### Q. What are epochs, batch size and learning rate, and how do you pick them for a fine-tune?

**Short answer (45 seconds):** An epoch is one pass over the training set, batch size is how many examples go into one gradient estimate, and the learning rate is how big each update step is. For SFT with LoRA I start around one to three epochs, an effective batch of 16 to 64 sequences via gradient accumulation, and a learning rate of about 2e-4 with warmup and cosine decay; for full fine-tuning the learning rate is roughly ten times smaller. Then I let the validation loss and the task eval decide.

**Deeper explanation:** Illustrative arithmetic: 10,000 examples with an effective batch of 16 is 625 optimizer steps per epoch; three epochs is 1,875 steps. The effective batch is `per_device_batch x gradient_accumulation_steps x number_of_gpus`, so on a single 24 GB GPU you might run 2 sequences per step and accumulate 8 times to get 16. Larger batches give smoother gradients but fewer updates per epoch; too small and the loss curve is noisy.

```python
from trl import SFTConfig

cfg = SFTConfig(
    output_dir="out",
    num_train_epochs=2,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,   # effective batch 16 on one GPU
    learning_rate=2e-4,              # LoRA; roughly 1e-5 to 2e-5 for full fine-tuning
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    logging_steps=10,
    bf16=True,
)
```

The learning rate is the knob to sweep first. Too high and the loss spikes or the model forgets how to chat; too low and nothing changes within your budget. Epochs are the second knob: small datasets often need two or three passes, but each extra pass raises the risk of memorisation, which you catch on the validation split.

**Follow-ups they will ask:**
- Why is the LoRA learning rate higher than full fine-tuning?: You are training a small number of freshly initialised parameters, which tolerate bigger steps than the pretrained weights do.
- What is gradient checkpointing?: Recomputing activations during the backward pass instead of storing them, trading compute for memory.
- How do you choose sequence length?: Long enough for your longest realistic example; memory grows with it, so measure the real distribution.

**Mistakes to avoid:**
- Training for ten epochs on 500 examples and reporting a near-zero training loss as success.
- Quoting hyperparameters without saying how you would validate them.

### Q. How do you detect and handle overfitting, and what is the bias-variance trade-off?

**Short answer (45 seconds):** Overfitting shows up as training loss that keeps dropping while validation loss flattens and then rises; the model is memorising examples instead of learning the pattern, and in practice it parrots training phrases and fails on slightly different inputs. I handle it with fewer epochs, more or more diverse data, a lower rank or dropout in LoRA, weight decay, and early stopping on the validation set. Bias-variance is the underlying tension: a model too constrained to fit the task (bias) versus one that fits noise (variance).

**Deeper explanation:** High bias means underfitting: training loss itself stays high, the model has not captured the format or the task. High variance means overfitting: it fits the training set, including its accidents, and generalises badly. Total error is roughly bias plus variance plus irreducible noise, and the hyperparameters move you along that curve. More epochs, higher LoRA rank and higher learning rate push toward variance; fewer epochs, lower rank, dropout and weight decay push toward bias.

```text
loss
 |  train: keeps falling
 |  \
 |   \____
 |        \_______________
 |
 |  val: falls, bottoms out, then rises   <- stop at the bottom
 |  \
 |   \___        _____
 |       \______/
 +------------------------------- steps
```

Early stopping is the cheapest fix: evaluate every N steps, keep the checkpoint with the best validation loss, and stop when it has not improved for a few evaluations. In Transformers that is `EarlyStoppingCallback` with `load_best_model_at_end=True`. Validation loss is a proxy, though, so also run the task eval on the chosen checkpoint; a lower loss does not always mean better JSON validity or judge scores.

**Follow-ups they will ask:**
- Can a small dataset ever be enough?: Yes if it is diverse and clean; a few hundred varied examples beat thousands of near-duplicates, which overfit immediately.
- What does LoRA dropout do?: Randomly zeroes adapter inputs during training so the adapter cannot rely on exact activations, a standard regulariser.
- What if validation loss is fine but outputs look memorised?: Check for leakage between splits, usually near-duplicates that landed on both sides.

**Mistakes to avoid:**
- Reporting training loss as the result.
- Treating validation loss as the final metric instead of a stopping signal.

### Q. What is catastrophic forgetting, and how do you prevent it when fine-tuning?

**Short answer (45 seconds):** It is when a narrow fine-tune overwrites abilities the base model had: you teach it to emit your ticket JSON and it gets worse at general instructions, other languages, or safety refusals. I limit it by using LoRA instead of updating all weights, keeping the learning rate low and epochs few, mixing a slice of general instruction data into the training set, and running a regression suite against the base model before shipping.

**Deeper explanation:** Gradient descent has no memory of why the weights were where they were. Every step moves them to reduce loss on your batch, and if your batches only contain one task, nothing pulls back toward the general behaviour. LoRA helps structurally because the update is confined to a low-rank subspace and the base weights are frozen; published work has found that LoRA tends to learn somewhat less than full fine-tuning on hard domain shifts but also forgets less. Replay is the other classic mitigation: include, say, 10 to 20 percent general chat or instruction examples (illustrative proportion) so each batch still votes for the old behaviour.

Detection is the part teams skip. Build a small regression set before training: a few dozen general prompts, your safety and refusal cases, and public benchmarks you can run cheaply with lm-evaluation-harness (for example a subset of MMLU or IFEval). Compare base and fine-tuned scores; a drop beyond your tolerance is a failed run, however good the task metric looks.

**Follow-ups they will ask:**
- Does merging the adapter change forgetting?: No, merging is just precomputing the sum; forgetting is decided during training.
- What about model averaging?: Interpolating fine-tuned and base weights can recover general ability at small task cost; it works because the two are close in weight space.
- Is forgetting worse for small models?: Usually, because they have less spare capacity.

**Mistakes to avoid:**
- Only reporting the task metric after fine-tuning.
- Assuming a low LoRA rank guarantees no forgetting; it reduces the risk, the regression suite proves it.

### Q. Why do you need train, validation and test splits, and what goes wrong if you skip them?

**Short answer (45 seconds):** Train is what the model learns from, validation is what you use to choose hyperparameters and the stopping point, and test is touched once at the end to report an honest number. If you tune on the test set, your reported quality is optimistic because every decision leaked information from it; if you skip validation, you have no early stopping signal and you will overfit without knowing.

**Deeper explanation:** For fine-tuning, the splits must be made before any training and must not share near-duplicates, which is the most common leak. Two paraphrases of the same support ticket on opposite sides of the split make validation loss look wonderful and tell you nothing. Deduplicate first (exact and near-duplicate), then split, and split by a grouping key when one exists: all conversations from one customer, or all examples derived from one source document, go to the same side.

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="clean.jsonl", split="train")
split = ds.train_test_split(test_size=0.1, seed=42)
train, held_out = split["train"], split["test"]
val_test = held_out.train_test_split(test_size=0.5, seed=42)
val, test = val_test["train"], val_test["test"]
```

Illustrative sizes: with 5,000 examples, 90 percent train, 5 percent validation and 5 percent test gives 250 examples in each held-out set, enough to see trends in loss but small for task metrics, so many teams keep a separate, larger task eval set that is never trained on and is refreshed from production. The validation split also changes over time: every time you add new data, re-split carefully or you will slowly train on former validation examples.

**Follow-ups they will ask:**
- Is validation loss enough to pick a checkpoint?: It is the first filter; the task eval on the top two or three checkpoints makes the final call.
- What if the dataset is tiny?: Use cross-validation for hyperparameter choice, then train on everything once the recipe is fixed, and rely on a separate task eval.
- How is decontamination different?: It removes overlap between training data and public benchmarks so reported benchmark scores are honest.

**Mistakes to avoid:**
- Random splitting of grouped data (same customer or document on both sides).
- "We looked at the test set a few times"; that makes it a validation set.

### Q. Why does training need so much more memory than inference, and where does it go?

**Short answer (45 seconds):** Inference only needs the weights and the KV cache. Training also needs gradients for every trainable parameter, optimizer state for each (Adam keeps two running averages), and the activations from the forward pass so backpropagation can compute those gradients. For full fine-tuning with mixed precision and Adam that adds up to roughly 16 bytes per parameter before activations, versus 2 bytes per parameter to run the model in bf16.

**Deeper explanation:** The standard breakdown for mixed-precision training with Adam, per parameter: 2 bytes for the bf16 or fp16 weight, 2 for its gradient, 4 for an fp32 master copy of the weight, and 4 plus 4 for Adam's first and second moment estimates, 16 bytes in total. Illustrative arithmetic for an 8B model: `8e9 x 16 bytes = 128 GB` of state, which is why full fine-tuning even a mid-sized model is a multi-GPU job with DeepSpeed ZeRO or FSDP sharding the state across devices. Activations add more, scaling with batch size times sequence length times hidden size times layers; gradient checkpointing trades recompute for memory there.

```text
bf16 weights             2 B/param     needed for inference and training
gradients                2 B/param     training only
fp32 master weights      4 B/param     training only
Adam m and v             8 B/param     training only
activations              depends on batch x seq x hidden x layers
```

This table is the whole motivation for parameter-efficient methods. If only one percent of parameters are trainable, the gradient and optimizer rows shrink by a factor of a hundred, and if the frozen weights are stored in 4 bits, the first row shrinks by four. That is QLoRA, covered next.

**Follow-ups they will ask:**
- Why keep an fp32 master copy?: Small updates would round to zero in 16-bit; the master copy accumulates them accurately.
- What do ZeRO stages do?: Stage 1 shards optimizer state across GPUs, stage 2 adds gradients, stage 3 adds the parameters themselves.
- What is 8-bit Adam?: Quantised optimizer states (bitsandbytes), cutting the 8 bytes of Adam state to about 2.

**Mistakes to avoid:**
- Saying training needs "about twice" inference memory; it is closer to eight times for the state alone.
- Forgetting activations, which often dominate at long sequence lengths.

### Practice
- Fine-tune a tiny model (a few hundred million parameters) on 500 examples for 10 epochs with evaluation every 50 steps, and plot training versus validation loss; find the step where overfitting starts and compare outputs from that checkpoint with the final one.
- Compute the memory budget for full fine-tuning and for LoRA on a 3B model by hand using the bytes-per-parameter table, then check it against what `nvidia-smi` or the trainer logs report.
- Build a regression set of 50 general prompts and 20 refusal cases, score the base model, then fine-tune on a narrow task for 1 epoch and for 5 epochs and measure how much each run forgets.
- Say it out loud: explain loss, gradient, learning rate, epoch and overfitting to a backend engineer in under two minutes using one training log as the prop.

## PEFT: LoRA and QLoRA

> This is the most likely deep-dive in the whole track because it is where an engineer can show real understanding without a research background. Interviewers want the mechanics (what LoRA adds, what rank and alpha do, where the adapter attaches), the memory arithmetic that explains why QLoRA runs on one GPU, and the serving decision (merge or not). A weak answer says "LoRA trains fewer parameters"; a strong one draws the two small matrices, does the byte math, and knows the trade-offs.

### Concepts you must understand
- Full fine-tuning updates every weight and needs gradients and optimizer state for all of them: roughly 16 bytes per parameter with mixed-precision Adam, so an 8B model is a multi-GPU job.
- LoRA freezes the base weights and learns a low-rank update `delta_W = B A` for selected matrices; only A and B are trained, typically well under one percent of the parameters.
- Rank r sets the capacity of the update and alpha scales it (`alpha / r` multiplies `B A x`); common starting points are r 8 to 64 with alpha equal to r or 2r.
- Target modules are the linear layers that get adapters; attention projections alone are the minimum, all linear layers (attention plus MLP) usually give better quality for modest extra memory.
- QLoRA stores the frozen base weights in 4-bit NormalFloat (NF4), dequantises on the fly for each forward pass, and trains the adapters in 16-bit; double quantisation and paged optimizers shave the rest.
- Memory for QLoRA is dominated by the quantised base plus activations, not by the adapter; an 8B model's weights drop from about 16 GB in bf16 to about 4 GB in 4-bit (illustrative arithmetic).
- Merging computes `W + (alpha / r) B A` once and saves a normal checkpoint with zero inference overhead; serving unmerged adapters keeps one base in memory and swaps tasks by adapter.
- PEFT limits: lower capacity than full fine-tuning for large domain shifts or new knowledge, sensitivity to rank and learning rate, and adapters that only work with the exact base model version they were trained on.

### Q. Why is full fine-tuning an 8B model expensive? Give me the concrete numbers.

**Short answer (45 seconds):** Because training needs far more than the weights. With mixed-precision Adam you hold the bf16 weight, its gradient, an fp32 master copy and two fp32 optimizer moments, about 16 bytes per parameter, so an 8B model needs roughly 128 GB of state before activations. That does not fit on any single GPU, so you shard it across several 80 GB cards with FSDP or DeepSpeed ZeRO, and the cost, complexity and iteration time all go up.

**Deeper explanation:** Illustrative arithmetic, all with round numbers:

```text
8B parameters, full fine-tuning, bf16 + fp32 Adam:
  weights (bf16)          8e9 x 2 B  =  16 GB
  gradients (bf16)        8e9 x 2 B  =  16 GB
  master weights (fp32)   8e9 x 4 B  =  32 GB
  Adam m + v (fp32)       8e9 x 8 B  =  64 GB
  total state                          128 GB   (+ activations)
```

Activations scale with batch size, sequence length, hidden size and layer count, and with 4k-token sequences they can add tens of gigabytes unless you enable gradient checkpointing. In practice an 8B full fine-tune means two to eight 80 GB GPUs with ZeRO stage 3 or FSDP, a slower iteration loop, and a 16 GB checkpoint per save. For a 70B model multiply everything by about nine and you are in multi-node territory.

Compare LoRA on the same model: the base weights still cost 16 GB in bf16 (or about 4 GB in 4-bit), but gradients and optimizer state exist only for the adapter, which might be 40 to 80 million parameters, so those rows shrink to under 1 GB. That is the whole reason PEFT exists.

**Follow-ups they will ask:**
- Where does the fp32 master copy come from?: Mixed-precision training keeps a high-precision copy so tiny updates are not rounded away in bf16.
- Can 8-bit Adam or Adafactor help?: Yes, they cut optimizer state several-fold, but full fine-tuning still needs gradients for all weights.
- When is full fine-tuning still the right call?: Large domain shifts, continued pretraining, or when you have the data and GPUs and need maximum quality.

**Mistakes to avoid:**
- Quoting only the weight size as the memory need.
- Forgetting activations and sequence length in the estimate.

### Q. Explain how LoRA works. What do rank and alpha mean?

**Short answer (45 seconds):** LoRA keeps the pretrained weight matrix W frozen and learns a correction as the product of two small matrices: `h = W x + (alpha / r) * B A x`, where A is r by d_in and B is d_out by r. The rank r controls how expressive the correction is and how many parameters you train; alpha is a scaling constant that sets how strongly the correction is applied. B starts at zero, so training begins exactly at the base model's behaviour.

**Deeper explanation:** The insight is that the change needed to adapt a pretrained model to a task has low intrinsic rank, so a full d_out by d_in update is wasteful. Parameter count per adapted matrix is `r * (d_in + d_out)` instead of `d_in * d_out`. Illustrative: for a 4096 by 4096 projection with r = 16, LoRA trains `16 * 8192 = 131,072` parameters versus about 16.8 million, under one percent. Across all attention and MLP projections of an 8B model this typically lands in the tens of millions of trainable parameters.

```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, config)
model.print_trainable_parameters()
```

Alpha matters because the product B A is scaled by `alpha / r`. If you double r without changing alpha, each adapter unit contributes half as much, so teams often set alpha to r or 2r and then tune the learning rate rather than alpha. The rank-stabilised variant (rsLoRA) scales by `alpha / sqrt(r)` so that higher ranks do not need learning rate changes.

**Follow-ups they will ask:**
- Why initialise B to zero?: So the adapter starts as a no-op and training cannot wreck the model on step one.
- Does rank 64 always beat rank 8?: No; for format and style tasks low ranks saturate quickly, and higher ranks mostly add overfitting risk.
- Is LoRA slower at inference?: Unmerged, slightly, from the extra small matmul; merged, zero overhead.

**Mistakes to avoid:**
- Describing LoRA as "freezing some layers"; it adds trainable low-rank matrices beside frozen ones.
- Treating alpha as independent of r.

### Q. Which modules do you attach LoRA to, and how do you choose the rank?

**Short answer (45 seconds):** Default to all linear projections: the attention q, k, v and o matrices plus the MLP gate, up and down projections. The QLoRA paper's finding was that adapting all linear layers, not just attention, is what closes the gap to full fine-tuning. For rank, start at 16 for format and tool-use tasks, 32 to 64 for broader behaviour or domain style, and let the eval and the memory budget decide; learning rate and data quality move results more than rank does.

**Deeper explanation:** Each targeted matrix adds `r * (d_in + d_out)` parameters, so targeting the MLP (larger than attention in most architectures) roughly triples adapter size compared with attention only. Illustrative count for a Llama-3-8B-shaped model (hidden 4096, MLP 14336, 32 layers, grouped-query k and v of width 1024) at r = 16: attention adds about 0.43 million per layer, the MLP about 0.88 million, so about 1.3 million per layer and about 42 million in total, roughly half a percent of the model.

A practical workflow: run a quick sweep at r = 8, 16 and 64 on a 10 percent data subset, compare validation loss and the task metric, and pick the smallest rank within noise of the best. Watch the trainable-parameter print-out; if an all-linear config at r = 128 approaches a few hundred million parameters on a small model, you have lost much of the memory advantage. Check module names against `model.named_modules()`, since families differ and a wrong name silently trains nothing.

**Follow-ups they will ask:**
- Should you adapt the embedding or output head?: Only when you add new tokens or a new language; PEFT lets you mark them trainable via `modules_to_save`.
- Does rank interact with dataset size?: Higher ranks overfit faster on small sets; a few hundred examples rarely justify r above 16.
- What does `lora_dropout` do?: Regularises the adapter input; 0.05 to 0.1 is common.

**Mistakes to avoid:**
- Attention-only adapters by habit when quality is the goal.
- Picking rank by folklore instead of a cheap sweep on a subset.

### Q. What does QLoRA add on top of LoRA, and why does it work?

**Short answer (45 seconds):** QLoRA stores the frozen base weights in 4-bit precision and trains LoRA adapters in 16-bit on top. Three pieces make it work: the NF4 data type, which places quantisation levels where normally distributed weights actually fall; double quantisation, which also compresses the per-block scaling constants; and paged optimizers, which spill optimizer state to CPU memory during spikes instead of crashing. The paper showed fine-tuning a 65B model on a single 48 GB GPU with quality close to 16-bit fine-tuning.

**Deeper explanation:** The trick is that gradients never flow into the 4-bit weights; they flow through them into the adapters. For each forward pass the quantised block is dequantised to bf16, multiplied, and the result is discarded, so you pay a little compute for a four-fold memory saving on the largest tensor in the system. The adapters, their gradients and their optimizer state stay in 16- and 32-bit, and they are small, so the loss of precision is confined to the frozen part.

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    quantization_config=bnb,
    device_map="auto",
)
```

Trade-offs: training is slower per step than bf16 LoRA because of dequantisation, and the quantised base is slightly less accurate, so if you have the memory for 16-bit LoRA you often get marginally better quality and speed. QLoRA's job is to make the project possible on one 16 GB to 24 GB card at all.

**Follow-ups they will ask:**
- Why NF4 rather than plain int4?: Pretrained weights are roughly normally distributed, so spacing the 16 levels by normal quantiles wastes fewer levels on rare extremes.
- What is a quantisation block?: Weights are quantised in groups (for example 64 values) with a shared scale; double quantisation compresses those scales.
- Can you QLoRA a model that is already GPTQ or AWQ quantised?: Those formats are made for inference; the standard training path uses bitsandbytes 4-bit loading.

**Mistakes to avoid:**
- Saying QLoRA "trains in 4-bit"; the adapters train in higher precision, only the frozen base is 4-bit.
- Ignoring the speed cost of dequantisation when bf16 LoRA would fit.

### Q. Walk me through the memory math for QLoRA on an 8B model on a 24 GB GPU.

**Short answer (45 seconds):** The 4-bit base is about 4 to 5 GB, the LoRA adapter with its gradients and Adam state is well under 1 GB, and the rest is activations, which depend on batch size and sequence length. With gradient checkpointing, a batch of 2 to 4 sequences of 2k tokens typically fits in 24 GB; push to 8k tokens and activations become the problem, so you shrink the batch and accumulate gradients. The adapter is never the bottleneck.

**Deeper explanation:** Illustrative arithmetic with round numbers:

```text
QLoRA, 8B model, r=16 on all linear layers:
  base weights, 4-bit        8e9 x 0.5 B    ~4 GB   (+ scales and 16-bit embeddings, ~0.5 GB)
  adapter params, bf16       4e7 x 2 B      ~0.08 GB
  adapter grads, bf16        4e7 x 2 B      ~0.08 GB
  adapter Adam (fp32 m, v)   4e7 x 8 B      ~0.32 GB
  activations                batch x seq x hidden x layers, reduced by checkpointing
  CUDA context, fragmentation, KV cache for eval      ~1 to 2 GB
```

Embedding and output head matrices are usually left in 16-bit, which is part of the extra half gigabyte. Activation memory is the variable term: it grows linearly with batch size and sequence length and, for attention scores without a fused kernel, quadratically with sequence length, so enable Flash Attention (`attn_implementation="flash_attention_2"`) or SDPA and gradient checkpointing before reaching for a bigger GPU.

The same sheet for bf16 LoRA replaces the 4 GB with 16 GB, which is why 16-bit LoRA on an 8B model wants a 40 GB to 80 GB card while QLoRA runs on 24 GB. Unsloth reduces the activation term further with custom kernels, which is how its notebooks run 8B QLoRA on a 16 GB T4 with short sequences and small batches.

**Follow-ups they will ask:**
- What is the first thing to try on an OOM?: Halve the per-device batch and double gradient accumulation; then shorten the sequence length; then enable checkpointing.
- Why does evaluation OOM when training did not?: Generation builds a KV cache and often uses a larger batch; set a smaller eval batch.
- Does rank matter for memory?: Barely; even r = 128 keeps the adapter rows under a few gigabytes.

**Mistakes to avoid:**
- Presenting the 4 GB weight figure as the total requirement.
- Forgetting that eval and generation need extra memory.

### Q. Should you merge the adapter into the base weights or serve it separately?

**Short answer (45 seconds):** Merge when one model serves one task and you want the simplest, fastest deployment: `W' = W + (alpha / r) B A` is computed once, the result is a normal checkpoint, and the inference server needs no LoRA support. Keep adapters separate when several tasks or tenants share one base model, when you iterate on adapters often, or when artifact size matters: an adapter is tens of megabytes versus a 16 GB merged model.

**Deeper explanation:** Merging is mechanically trivial in PEFT, but one trap matters: you cannot merge into 4-bit weights. Load the base in bf16, attach the adapter, merge, then save, and optionally re-quantise for serving. Merging into a 16-bit copy of a base that was 4-bit during training introduces a small numerical mismatch versus what training saw; in practice it is minor, but validate the merged model on the eval set rather than assuming.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", torch_dtype="bfloat16")
model = PeftModel.from_pretrained(base, "adapters/support-v3")
merged = model.merge_and_unload()
merged.save_pretrained("models/support-v3-merged")
```

Serving unmerged adapters costs a small extra matmul per adapted layer, which vLLM batches efficiently, and buys flexibility: hot-swap a new adapter version without reloading the base, run A/B between adapters on the same GPU, and keep a tiny rollback artifact. For a single high-throughput task, merge and quantise (AWQ or FP8) for the best latency.

**Follow-ups they will ask:**
- How big is an adapter file?: Roughly `trainable_params x 2 bytes`; 40 million parameters is about 80 MB.
- Can you merge several adapters?: Yes, PEFT supports weighted combination, but validate carefully; adapters trained separately can interfere.
- Does merging change quality?: Mathematically no, in bf16 it is the same function up to rounding; after re-quantisation, re-run evals.

**Mistakes to avoid:**
- Calling `merge_and_unload()` on a 4-bit loaded model and shipping it without checking.
- Serving one adapter unmerged on a dedicated GPU "just in case" and paying latency for no benefit.

### Q. How would you serve many adapters, say one per customer, on a single GPU?

**Short answer (45 seconds):** Load the base model once and let the inference server attach adapters per request. vLLM supports this: start with `--enable-lora`, register adapters with `--lora-modules name=path`, and clients pick one by sending the adapter name as the `model` field in a standard OpenAI-style request. The server batches requests for different adapters together, so a hundred tenants share one copy of the base and the marginal cost per tenant is a few tens of megabytes.

**Deeper explanation:** Multi-LoRA serving works because every request runs the same frozen base and only the small adapter matmuls differ, so a batch can mix tenants and apply each row's own A and B. The ideas were worked out in systems papers such as S-LoRA and Punica, and vLLM implements them with a cache of adapters on the GPU and a larger pool on CPU.

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --enable-lora \
  --lora-modules acme=/adapters/acme globex=/adapters/globex \
  --max-loras 8 --max-lora-rank 32
```

```json
{"model": "acme", "messages": [{"role": "user", "content": "Summarise ticket 4821"}]}
```

Constraints to plan for: all adapters must be trained on the same base model and tokenizer, their rank must not exceed the configured maximum, and the adapter cache has a size limit after which adapters page in from CPU with a latency hit. vLLM also has an endpoint for loading adapters at runtime that has to be explicitly enabled; many teams instead restart the server or use a blue/green pair when the adapter set changes.

**Follow-ups they will ask:**
- How do you isolate tenants?: Route adapter names from authenticated tenant ids in your gateway, never from client input.
- What is the latency cost versus merged?: Small per-token overhead from the extra matmuls, usually acceptable; measure p95 under mixed load.
- What if a customer needs a different base model?: That is a separate deployment; multi-LoRA only shares within one base.

**Mistakes to avoid:**
- Proposing one merged model per customer on its own GPU.
- Letting the request body choose the adapter without authorisation.

### Q. What are the limitations of PEFT? When would you still do full fine-tuning?

**Short answer (45 seconds):** LoRA's capacity is bounded by its rank and by the frozen base, so for large shifts, such as a new language, continued pretraining on a big domain corpus, or teaching substantial new knowledge, full fine-tuning learns more. Research comparing the two found LoRA learns less but forgets less. Adapters are also brittle operationally: tied to one base version, sensitive to learning rate and rank, and awkward when the tokenizer or vocabulary changes.

**Deeper explanation:** For instruction following, format, style and tool use, the gap between LoRA and full fine-tuning is usually within eval noise, which is why PEFT is the default. The gap opens when the model must absorb a lot of new information, for example code in a new language or dense medical text; there the low-rank constraint is a real ceiling and a higher rank only partly closes it.

Practical limitations: every base model release means retraining adapters; quantised bases cannot be merged into directly; some serving stacks and edge runtimes want a single merged file; and LoRA hyperparameters interact (rank, alpha, learning rate, target modules), so a bad sweep looks like "LoRA does not work". Alternatives inside PEFT include DoRA (decomposes weight magnitude and direction), prompt and prefix tuning (train soft tokens, very few parameters, weaker), and IA3 (learned scaling vectors).

Choose full fine-tuning when you have tens of thousands of high-quality examples, GPUs to shard across, and an eval showing LoRA plateauing below target, or for continued pretraining. Otherwise start with QLoRA and escalate only on evidence.

**Follow-ups they will ask:**
- Is there a middle ground?: Yes: higher-rank LoRA on all linear layers, or full fine-tuning of a small model distilled from a big one.
- Can LoRA add a new language?: Partially, for style and some vocabulary; real proficiency needs continued pretraining with large data.
- Does LoRA work for embedding and vision models?: Yes, the method applies to any linear layer.

**Mistakes to avoid:**
- Claiming LoRA matches full fine-tuning in all cases.
- Blaming the method for a bad learning rate or wrong target modules.

### Practice
- Fine-tune an 8B instruct model with QLoRA on 1,000 examples twice: attention-only at r = 8 and all-linear at r = 16. Record trainable parameter counts, peak memory from the trainer logs, wall-clock time and the task metric, and explain the differences.
- Merge the better adapter into a bf16 base, quantise the merged model for serving, and confirm the eval score is within noise of the unmerged adapter.
- Serve the base with two adapters in vLLM using `--enable-lora`, send mixed requests, and measure p50 and p95 latency against the merged single-task deployment.
- Say it out loud: on a whiteboard, draw W, A and B with their dimensions, write the forward pass with alpha over r, and compute the parameter count for one 4096 by 4096 matrix at rank 16.

## Data Engineering for Fine-tuning

> Most fine-tuning failures are data failures, and interviewers who have run a project know it. They will ask what your examples look like byte for byte, how you got them, how you know they are good, and how you keep them from leaking eval answers or customer data. A weak answer says "we collected a few thousand examples"; a strong one talks about chat templates, loss masking, deduplication, judge filtering, licensing, and a dataset version pinned to every model.

### Concepts you must understand
- A chat template is the exact string format (special tokens, role markers) the model was trained on; `tokenizer.apply_chat_template` produces it, and training with a different format degrades the model.
- The standard dataset shape is a list of messages with roles (system, user, assistant, and tool calls where relevant); TRL applies the template and can mask the loss so only assistant tokens are learned.
- Quality beats quantity: a thousand clean, diverse, correct examples usually beat fifty thousand noisy ones, because every example is a vote and bad votes are learned too.
- Deduplication (exact, near-duplicate, semantic) prevents memorisation and inflated validation scores; decontamination removes overlap with your eval sets and public benchmarks.
- Synthetic data pipelines use a stronger model to generate inputs and outputs from seeds, schemas or real traffic, then filter hard; distillation is the special case where the goal is to copy the teacher's behaviour.
- LLM judges filter and grade generated data against a rubric; they must be calibrated against human labels and checked for verbosity, position and self-preference bias.
- Licensing and privacy constrain everything: model licenses, provider terms on using outputs, consent for customer data, PII scrubbing, and the fact that weights can memorise training text.
- Enough data is an empirical question: train on 10, 25, 50 and 100 percent and watch the eval curve; style and format need hundreds of examples, broad domain behaviour needs tens of thousands.
- Datasets are versioned artifacts: content hash, schema, provenance of every row, and the version recorded in the model card and the training run.

### Q. What is a chat template and why does it matter so much for fine-tuning?

**Short answer (45 seconds):** It is the exact text layout a chat model was trained on: which special tokens open and close each turn, how the system prompt is placed, where the model is expected to start generating. The template lives in the tokenizer config as a Jinja string, and `apply_chat_template` renders your messages into it. If you train on a different layout, you are teaching the model a new protocol with a few thousand examples against millions it already learned, and both training and inference quality suffer.

**Deeper explanation:** Formats differ by family: Llama 3 uses header tokens such as `<|start_header_id|>user<|end_header_id|>` and `<|eot_id|>`, Qwen and many others use ChatML (`<|im_start|>` and `<|im_end|>`), Mistral uses `[INST]` markers. Rendering by hand almost always gets a newline or token wrong. Always let the tokenizer do it, and make sure the inference server uses the same tokenizer and template, otherwise the model sees one format in training and another in production.

```python
messages = [
    {"role": "system", "content": "You convert support emails into tickets."},
    {"role": "user", "content": "Hi, my invoice 4821 shows the wrong amount..."},
    {"role": "assistant", "content": '{"type": "billing", "priority": "high"}'},
]
text = tokenizer.apply_chat_template(messages, tokenize=False)
prompt_only = tokenizer.apply_chat_template(
    messages[:2], tokenize=False, add_generation_prompt=True
)
```

`add_generation_prompt=True` appends the assistant header so the model knows to start answering; at training time you render the full conversation without it. Tool calling is part of the template too: recent templates accept a `tools=` argument and render tool definitions and tool-call turns in the format the model expects, which is what makes tool-use fine-tuning data consistent.

**Follow-ups they will ask:**
- What if the base model has no template?: You are using a base (not instruct) checkpoint; pick a template, add its special tokens, and expect to need more data.
- Can you change the system prompt format?: Yes, within the template's content slots; do not invent new role markers.
- How do you catch template mismatch in production?: Log the rendered prompt for a sample of requests and diff it against a training example.

**Mistakes to avoid:**
- String-concatenating "User: ... Assistant: ..." and wondering why the fine-tune behaves oddly.
- Training with the generation prompt appended, which shifts where the model learns to start.

### Q. What format should the training data be in, and which tokens do you compute the loss on?

**Short answer (45 seconds):** Use JSON Lines where each row is a conversation: a `messages` array with system, user and assistant turns, plus tool calls and tool results when the task needs them. TRL's SFTTrainer accepts that shape directly and applies the chat template. Compute the loss only on assistant tokens, so the model learns to produce answers rather than to predict user prompts and boilerplate; prompts still appear in the context, they just do not contribute gradient.

**Deeper explanation:** Two formats are common: conversational (`messages`) and prompt-completion (`prompt` and `completion` fields). Conversational is the right default because it carries multi-turn context and tool turns, and the template handles rendering.

```json
{"messages": [
  {"role": "system", "content": "You are the ACME support triage model."},
  {"role": "user", "content": "Order 1182 never arrived and support chat is down."},
  {"role": "assistant", "content": "{\"intent\": \"missing_order\", \"order_id\": \"1182\", \"escalate\": true}"}
]}
```

Loss masking matters more than people expect. With a long system prompt and short JSON answers, unmasked training spends most of its gradient learning to reproduce the system prompt, which is wasted and can even teach the model to echo instructions. TRL has exposed completion-only loss under different names across versions (an assistant-only loss flag in recent releases, `DataCollatorForCompletionOnlyLM` in older ones); check the version you install and verify by decoding a batch and confirming prompt positions carry the ignore label (-100).

Also decide on packing. Packing concatenates several short examples into one sequence to avoid padding waste and speeds training, but naive packing lets examples attend across boundaries; modern trainers handle the masking, so verify your version does before enabling it.

**Follow-ups they will ask:**
- How do you represent tool calls?: As assistant turns with structured `tool_calls` and following `tool` role turns, rendered by the template's tool support.
- Multi-turn conversations: loss on every assistant turn or only the last?: Usually every assistant turn, unless earlier turns are synthetic or low quality.
- What is label -100?: PyTorch cross-entropy ignores positions labelled -100, which is how masking is implemented.

**Mistakes to avoid:**
- Training on the whole sequence including a 1,000-token system prompt repeated in every row.
- Mixing formats across rows so some get the template and some do not.

### Q. How much data do you need, and why do people say quality beats quantity?

**Short answer (45 seconds):** It depends on how far the behaviour is from what the model already does. A consistent output format or tone often needs a few hundred clean examples; reliable tool calling against your schema a few thousand; broad domain behaviour tens of thousands. The honest answer is empirical: train on 10, 25, 50 and 100 percent of the data and plot the eval metric; if it is still climbing at 100 percent, collect more, and if it flattened at 25 percent, spend the effort on quality and coverage instead.

**Deeper explanation:** Every example is a gradient vote. A wrong label, an inconsistent format, or a lazy answer is learned just as eagerly as a good one, and a model trained on noisy data becomes confidently noisy. The LIMA paper made the point sharply by getting strong instruction following from about a thousand carefully written examples. In production terms: an afternoon spent fixing 200 labels usually beats a week spent scraping 20,000 more.

Coverage matters as much as cleanliness. Enumerate the input space: intents, lengths, languages, edge cases, adversarial or off-topic requests, and empty or malformed inputs. Then check your dataset's distribution against production traffic; a model trained only on happy-path tickets will fail exactly where the prompted baseline did. A useful habit is a per-row rubric before anything enters the training set: is the output correct, is it in the required format, would a senior person sign it, and is it a near-duplicate of something already included.

```text
Illustrative learning curve (task metric vs data fraction):
  10%  -> 0.71
  25%  -> 0.82
  50%  -> 0.86
  100% -> 0.87   <- flattening: more data of this kind will not help much
```

**Follow-ups they will ask:**
- How do you get more coverage without more labelling?: Synthetic generation targeted at the under-represented slices, then judge filtering.
- Does more data fix a bad base model choice?: Rarely; a small model may lack the capacity regardless of data.
- How do you handle class imbalance?: Oversample rare intents or generate synthetic examples for them, and report per-slice metrics.

**Mistakes to avoid:**
- Quoting a universal number like "you need 10k examples".
- Measuring dataset size instead of dataset coverage.

### Q. How would you build a synthetic data pipeline using a stronger model, and how is that different from distillation?

**Short answer (45 seconds):** Start from seeds you trust: real anonymised traffic, your schema, your docs, or a taxonomy of intents. Prompt a strong model to generate diverse inputs for each slice, then generate outputs with a carefully engineered prompt that includes your rules and examples, then filter with validators and a judge, deduplicate, and split. Distillation is the case where the point is to copy the strong model's behaviour into a smaller one; the pipeline is the same, the target is "match the teacher" rather than "match a human spec".

**Deeper explanation:** The pipeline is a DAG you can rerun:

```text
seeds (intents, schemas, real anonymised samples)
  -> generate inputs     (vary persona, length, language, edge case; temperature up)
  -> generate outputs    (teacher model, strict system prompt, temperature low)
  -> hard filters        (JSON schema valid, tool names exist, length limits, PII scan)
  -> judge filter        (rubric score >= threshold, agreement checked on a human sample)
  -> dedup + decontaminate against eval sets
  -> split + version     (hash, manifest, counts per slice)
```

Techniques worth naming: Self-Instruct style bootstrapping (seed tasks produce new tasks), Evol-Instruct style complication (rewrite prompts to be harder or more constrained), and Magpie-style elicitation, where you give an aligned model only its user-turn template and let it generate realistic user requests. For distillation specifically, run the teacher over real production inputs when privacy allows, since matching the real distribution is what makes the student hold up.

Watch for mode collapse: a generator at low temperature produces samey inputs, so vary personas and constraints explicitly and measure diversity (distinct n-grams, embedding spread). Keep humans in the loop on a sample of every batch; judges miss subtle wrongness that a domain expert spots in seconds.

**Follow-ups they will ask:**
- Can the student exceed the teacher?: On the narrow task, sometimes, because filtering removes the teacher's mistakes; in general capability, no.
- How do you avoid training on teacher hallucinations?: Validators where answers are checkable, judges with reference material, and sampled human review.
- Is it allowed to distil from a hosted API?: Depends on the provider's terms; some restrict training competing models on outputs, so check before building.

**Mistakes to avoid:**
- Generating 100k examples with one prompt at temperature 0 and calling it a dataset.
- Skipping human review because "the judge passed it".

### Q. How do you use an LLM as a judge to filter or grade data, and how do you know the judge is trustworthy?

**Short answer (45 seconds):** Give a strong model the input, the candidate output, any reference material, and a rubric with explicit criteria, and ask for a structured verdict: per-criterion scores and a final pass or fail with a short reason. Then calibrate: have humans label a few hundred examples, measure agreement with the judge, and only trust it on the criteria where agreement is high. Known biases to control are verbosity (longer looks better), position (the first candidate is favoured in pairwise), and self-preference (a model likes its own style).

**Deeper explanation:** Judging is cheapest when the question is narrow. "Is this JSON valid against the schema" is a validator, not a judge. "Does this answer only use facts from the provided context" is a judge task with a checkable rubric: list each claim, mark supported or not. "Is this answer good" is too vague and produces noisy scores.

```text
Judge prompt skeleton:
  You are grading a support reply. Criteria:
   1. Uses only facts from CONTEXT (0/1, list any unsupported claim)
   2. Follows the JSON schema exactly (0/1)
   3. Tone matches the style guide (1-5)
  Output JSON: {"c1": 0|1, "unsupported": [...], "c2": 0|1, "c3": 1-5, "pass": true|false}
```

For pairwise comparisons, run each pair twice with the order swapped and count only consistent wins. Use a judge that is stronger than the model producing the candidates and, where possible, not the same model. Report the agreement rate with human labels (and, for pairwise, a kappa-style statistic) in the dataset manifest so the next engineer knows how much to trust the filter.

Thresholds are a product decision: filtering at a high score keeps a cleaner but smaller and less diverse set, so check that the kept set still covers all slices.

**Follow-ups they will ask:**
- Can you fine-tune the judge?: Yes, on human labels, which is useful when you grade millions of rows and the strong model is expensive.
- How do you handle judge disagreement with humans?: Inspect the cases; usually the rubric is ambiguous, so fix the rubric and re-run.
- Should the judge see the reference answer?: When one exists, yes; it turns a subjective grade into a comparison.

**Mistakes to avoid:**
- Using the student model as its own judge.
- Reporting judge scores without any human agreement figure.

### Q. Explain deduplication and decontamination. How do you actually do them?

**Short answer (45 seconds):** Deduplication removes repeated or near-repeated training rows so the model does not memorise them and so validation does not accidentally contain training examples. Decontamination removes training rows that overlap with your eval sets or public benchmarks so the scores you report are honest. Mechanically: hash normalised text for exact duplicates, MinHash plus locality-sensitive hashing for near-duplicates, embedding similarity for semantic duplicates, and n-gram overlap against every eval set before the final split.

**Deeper explanation:** Exact dedup is a normalised hash: lower-case, collapse whitespace, strip ids and timestamps, hash the user turn plus the assistant turn. Near-dedup catches paraphrases and templated variants: shingle each example into token n-grams, compute MinHash signatures, bucket with LSH, and drop pairs above a Jaccard threshold (0.8 is a common starting point, illustrative). Semantic dedup embeds examples and removes neighbours above a cosine threshold, useful for synthetic data where the generator repeats itself in different words.

```python
from datasketch import MinHash, MinHashLSH

def shingles(text, n=5):
    toks = text.lower().split()
    return {" ".join(toks[i:i + n]) for i in range(max(1, len(toks) - n + 1))}

lsh = MinHashLSH(threshold=0.8, num_perm=128)
for row_id, text in rows:
    m = MinHash(num_perm=128)
    for s in shingles(text):
        m.update(s.encode())
    if lsh.query(m):
        continue            # near-duplicate of a kept row: drop it
    lsh.insert(row_id, m)
```

Decontamination is the same machinery pointed at a different set: for each eval example (yours and any public benchmark you will report), check whether its prompt or answer appears in training data by n-gram overlap, and drop the training rows that match. Do it before splitting and record how many rows were removed; a large number is itself a finding about how your data was collected.

**Follow-ups they will ask:**
- Why is near-dedup more important for synthetic data?: Generators repeat structure; exact hashing misses it and the model overfits to the template.
- Should dedup be per split or global?: Global first, then split, otherwise you leak across splits.
- What about duplicate prompts with different answers?: Keep one and pick the best answer deliberately; conflicting labels teach noise.

**Mistakes to avoid:**
- Deduplicating after splitting.
- Reporting a benchmark score without stating whether you decontaminated against it.

### Q. What legal and privacy issues come up with fine-tuning data, and how do you version datasets?

**Short answer (45 seconds):** Three layers: the base model's license (Llama uses a community license with an acceptable-use policy, many others use Apache 2.0, and terms can differ within a family), the terms of any API whose outputs you train on, and the rights and privacy of the people in your data (consent, PII, regulated fields). Weights can memorise training text, so anything you would not paste into a public file should not enter the set unredacted. Then treat the dataset like code: immutable versions, hashes, provenance, pinned in every model card.

**Deeper explanation:** For PII, run a detector such as Microsoft Presidio over every row, replace entities with typed placeholders (`[PERSON_1]`, `[EMAIL]`), and keep a reviewed allow-list of fields that are genuinely needed. Memorisation is real: a model fine-tuned on raw tickets can regurgitate a name and order number, and a leaked adapter leaks the data. Check data processing agreements: many enterprise contracts forbid training on customer content without explicit consent, and regional rules (GDPR, the UAE's federal data protection law) govern retention and purpose.

Versioning: store each dataset build as an immutable artifact (JSONL plus a manifest with counts per slice, content hash, sources, generator and judge versions, dedup and decontamination stats). Tools: DVC, Hugging Face dataset repos with revisions, lakeFS; even a dated S3 prefix with a SHA-256 manifest works if never overwritten. Every model card records the dataset version, so a regression can be traced to a data change.

```text
datasets/support-triage/v7/   train.jsonl  val.jsonl  test.jsonl  manifest.json
models/support-triage/2026-10-12-r16-v7/   adapter/  eval.json  MODEL_CARD.md  (dataset: v7)
```

**Follow-ups they will ask:**
- Can you train on data consented for "service improvement"?: Ask legal; such clauses do not always cover model training.
- How do you delete a user's data from a trained model?: You cannot cleanly; you retrain from a dataset version without them, which is why provenance matters.
- What goes in the manifest?: Everything needed to rebuild and audit the set: sources, filters, model versions, counts, hashes.

**Mistakes to avoid:**
- Treating the "open" in open weights as permission for any use.
- Overwriting a dataset file in place, so a shipped model points at data that no longer exists.

### Practice
- Take 2,000 real or synthetic examples, run exact and MinHash dedup, and report how many rows drop at thresholds 0.7, 0.8 and 0.9; inspect ten dropped pairs at each threshold.
- Render five training rows with `apply_chat_template`, decode one training batch, and verify the prompt positions carry the ignore label and the assistant tokens do not.
- Build a judge with a three-criterion rubric, label 100 rows yourself, and measure agreement; adjust the rubric until agreement is acceptable, then filter the full set.
- Say it out loud: describe your dataset manifest to a reviewer, including where every row came from, what was filtered out and why, and which model version used it.
