## When to Fine-tune

### Why it exists
There are three ways to change what a model produces: change the instructions (prompting), change the evidence it reads at request time (retrieval, often called RAG), or change the model's weights, the billions of numbers it learned in training (fine-tuning). Teams that skip this decision either keep stretching a prompt that will never be fully reliable, or train a model to "know" documents that change every week and watch it go stale. The decision step exists so you pick the cheapest change that fixes a measured problem. Fine-tuning buys consistent behaviour and lets a smaller, faster model do the job, but it makes you the owner of a model: data collection, evals, retraining and rollback become your work.

## ML & Training Fundamentals for LLMs

### Why it exists
Training is the loop that nudges a model's weights so the correct next token becomes more likely, and a handful of settings control it: the loss (a score for how wrong the model is), the learning rate (how big each correction is), the batch size (how many examples per correction) and epochs (how many passes over the data). Without these ideas you cannot read a loss curve, so a run that is memorising its data, blowing up to NaN or running out of GPU memory looks like a mystery. Before libraries made training a few lines of code, only research teams needed this; now any engineer can start a run, and the fundamentals are what let you tell a good run from a bad one. Every knob is a trade-off: bigger steps learn faster but can diverge, more passes fit better but memorise, and more memory per step means fewer experiments per GPU.

## PEFT: LoRA and QLoRA

### Why it exists
Full fine-tuning updates every weight, and with the usual optimizer that costs roughly 16 bytes of GPU memory per parameter, so an 8B model needs well over 100 GB spread across several GPUs, plus a full copy of the model for every task. Parameter-efficient fine-tuning (PEFT) freezes the original weights and trains a small add-on; LoRA adds two thin matrices next to chosen layers, usually well under one percent of the model's size. QLoRA also stores the frozen weights in 4-bit numbers, which lets an 8B model train on one 24 GB card. The cost is capacity and coupling: the add-on learns less than full training on large shifts, 4-bit storage adds a small numerical error, and each adapter works only with the exact base model it was trained on.

## Data Engineering for Fine-tuning

### Why it exists
A fine-tuned model copies whatever its examples show, including typos, wrong answers, inconsistent formats and leaked test questions, so the dataset decides the outcome far more than the training settings do. Early attempts often trained on raw logs or scraped text and got models that faithfully learned the noise. Data engineering is the work that makes examples correct, consistent, diverse and safe: the right chat format, loss on the right tokens, synthetic data that passes filters, deduplication, removal of overlap with eval sets, and removal of personal data. It is usually the most expensive part of a project in people time, and it never fully ends, because the data must be refreshed as the task drifts.

## Preference Optimization & RL Intuition

### Why it exists
Supervised fine-tuning needs one correct answer per example, but many qualities, such as tone, brevity or being helpful without over-refusing, are easier to judge than to write. Preference optimization trains on comparisons ("answer A is better than answer B"), so the model learns what people prefer rather than copying a single reference. The original recipe, RLHF with PPO, needed a separate reward model and a fragile reinforcement learning loop with several models in memory; DPO and its relatives learn straight from the pairs and run much like ordinary fine-tuning. The trade-off is that the model optimises a proxy: if the pairs or the judge favour long or flattering answers, the model becomes long and flattering, which is called reward hacking.

## Tooling & Infrastructure

### Why it exists
A correct training loop has many parts that are easy to get subtly wrong: mixed precision, gradient accumulation, splitting memory across GPUs, checkpoint and resume, chat templates and loss masking. Hand-written loops got these wrong often enough that libraries such as Transformers, PEFT, TRL and Accelerate, and wrappers like Unsloth and Axolotl, now package them, while hosted fine-tuning APIs remove the GPUs altogether. The infrastructure side (choosing GPUs, using cheap interruptible machines, tracking experiments) exists because GPU time is expensive and a run nobody can reproduce cannot be trusted. The cost is fast-moving APIs that rename arguments between versions, abstractions that hide bugs until you inspect a real batch, and the discipline of pinning every version.

## Evaluating & Shipping a Fine-tuned Model

### Why it exists
A training run produces a file, not a product: without an eval set you cannot say whether the new model is better, and without a regression suite you will not notice what it got worse at. Teams that judged models by reading a handful of outputs shipped regressions and could not roll back cleanly, because the "model" was a file path someone had overwritten. Evaluation, versioning, staged rollout and monitoring turn a checkpoint into something you can release, compare and undo. The cost is building and maintaining eval sets and judges, and sending every release through gates that slow down the "just ship it" path.

## Small Language Models & Distillation

### Why it exists
Frontier models are slow, priced per token, and sometimes unusable when data must stay on-premises or the device has no network. A small model, roughly 1B to 8B parameters, fine-tuned on outputs from a large "teacher" model can do one narrow task at a fraction of the latency and cost, which is what distillation means in day-to-day practice. Before this, teams either paid for the big model on every call or trained small task models from scratch with expensive human labels. The trade-off is narrowness: the student is good only at the task it was trained for, it inherits the teacher's mistakes, it needs a fallback for unusual inputs, and some providers' terms restrict using their outputs to train other models.

## The 15 Fine-tuning Techniques

### Why it exists
Fine-tuning has collected many named methods (SFT, LoRA, QLoRA, DoRA, adapters, prompt and prefix tuning, RLHF, PPO, DPO, ORPO and more), and without a map people choose by popularity rather than by problem. The map answers two separate questions: how much of the model you train (all weights, a small add-on, or a few learned prompt vectors) and what signal you train on (demonstrations or comparisons). Sorting the names this way lets you start with the cheapest recipe, usually SFT with LoRA or QLoRA, and add preference tuning only when a measured failure needs it. Skipping the map has a real cost: teams reach for full fine-tuning or PPO on problems a small adapter would have fixed.

## Fine-tuning Project Scenarios [Scenarios]

> Interviewers run these as open design conversations: "you are building X, the constraint is Y, walk me through it". They are not checking whether you can call `SFTTrainer`; they want to see you refuse to train before there is an eval set and a baseline, split the problem into knowledge, behaviour, syntax and latency parts, estimate data and GPU memory out loud, and plan the release and rollback before the first run. A weak answer jumps straight to "fine-tune Llama with LoRA". A strong answer says what it would measure, what result would make it stop, and what happens to users when the model is wrong.

### Concepts you must understand
- Ask for the eval first: what a correct output looks like, how it is scored, and what the best prompt plus retrieval scores today; no baseline, no training.
- Classify the gap before choosing a tool: missing facts go to retrieval, inconsistent behaviour or format goes to fine-tuning, broken syntax goes to constrained decoding first, and cost or latency goes to distillation into a smaller model.
- Estimate data out loud: how many real labelled examples exist, who can label more and at what cost, and how much synthetic data you can generate and actually verify.
- Estimate compute out loud: about 2 bytes per parameter for bf16 weights, about half a byte in 4-bit, roughly 16 bytes per trained parameter for full fine-tuning with Adam, plus activations that grow with sequence length and batch size.
- Pick the serving shape early (merged model or adapter on a shared base, which GPU, what latency budget), because it changes what and how you train.
- Keep deterministic work in code: arithmetic, unit conversion, lookups and validation do not belong in the weights.
- Plan the release as a versioned bundle with gates (offline eval, regression suite, canary) and a rollback that is a config flip, not a retrain.
- Name the maintenance loop: who retrains, on what trigger, with what fresh data, and which fallback handles the cases the model is unsure about.

### Q. A construction-estimating product must turn architectural drawing PDFs into structured, priced line items. A prompted frontier vision model gets the gist but misreads dimensions and drifts from your schema. Do you prompt harder, add RAG, or fine-tune?

**Short answer (45 seconds):** I split the problem instead of picking one tool. Prices, material specs and client rules are facts that change, so they go in retrieval. Reading drawing conventions (symbols, scales, dimension strings, legends) and emitting the schema every time are behaviours, so I would fine-tune a vision-language model for those. Quantities, areas and totals are arithmetic, so code does them. I would train in stages, easiest skills first, with an eval gate per stage.

**Deeper explanation:** Clarify first: which fields each line item needs, the tolerance on quantities, how many drawings are labelled, who checks the output, and whether drawings may leave the client's environment. Then score the prompted baseline per field to see whether misses are reading or format errors.

Fix resolution before training: sheets are large and the text is tiny, and vision models resize images to a pixel budget (Qwen2.5-VL exposes `min_pixels` and `max_pixels`), so tile each sheet and keep coordinates so every value traces back to a region.

```text
Stage 1  crops: dimension strings, symbols, title-block fields   many cheap labels
Stage 2  full sheet -> line-item JSON for one discipline          gate: per-field accuracy
Stage 3  multi-sheet references, explicit "needs_review" output   gate: estimator edit rate
Each stage replays a slice of earlier-stage data to limit forgetting.
```

In a system like CADBEATER the tuned model would sit behind retrieval (Qdrant over the catalogue) and a human approval gate, so a wrong quantity is caught before it is priced. Split train and eval by project or by architecture firm, never by sheet, or the same building lands on both sides. Risks: inconsistent labels between estimators and drawing styles that vary by firm. Measure per-field exact match, quantity error within tolerance, schema validity, and after launch the estimator correction rate; corrections become the next round of labels.

**Follow-ups they will ask:**
- Only 200 labelled drawings?: Stage 1 crops turn 200 drawings into thousands of small examples, and estimator corrections grow the set every week.
- Why stages instead of one mixed run?: Each stage has its own gate, so you learn which skill fails; one mixed run hides it.

**Mistakes to avoid:**
- Fine-tuning prices or specs into the weights.
- Letting the model do the area and total arithmetic.

### Q. A UAE insurer wants claim emails in English and Arabic turned into a fixed claim JSON. You have 400 labelled emails and permission to use a stronger model to generate more. Design the synthetic data pipeline.

**Short answer (45 seconds):** Real emails are for evaluation and seeds; synthetic data is only for training. I would generate diverse inputs from a taxonomy, label them with the strong model using the best prompt I can build, and push every row through filters: schema validation, grounding checks, a calibrated judge, deduplication and an overlap check against the eval set. A native-speaker review of a sample per batch is the last gate, and the only score I trust is on held-out real emails.

**Deeper explanation:** Clarify the claim types, the share of Arabic, mixed-language and forwarded threads, whether the generator may see real emails (personal data, residency), and the accuracy floor per field.

```text
taxonomy (claim type x language x length x noise)
  -> generate inputs (varied personas, typos, forwarded threads, mixed scripts)
  -> generate labels (system prompt + schema + few-shot from TRAIN seeds only)
  -> filter: JSON schema | amounts and dates appear in the email | judge rubric
  -> MinHash dedup, overlap check against the real eval set
  -> human sample review per batch -> versioned dataset + data card
```

Split the 400 first, for example 250 as seeds and training anchors and 150 frozen as the eval set, grouped by customer so threads never cross sides. The generator never sees the eval set; that is the most common way synthetic pipelines leak. Calibrate the judge on about 100 human-labelled items and track agreement. A filter that rejects almost nothing or almost everything is broken, so track acceptance per filter. Check diversity, for example embedding clusters per claim type, so the data does not collapse into the generator's favourite phrasing.

Risks: the student inherits the teacher's systematic errors (Arabic-Indic digits and mixed date formats deserve their own checks), personal data leaks through seeds, and the provider's terms may restrict training on its outputs.

**Follow-ups they will ask:**
- How much synthetic versus real?: Add synthetic data until the real-email eval stops improving; past that you add style, not skill.
- How do you test the filters?: Plant known-bad rows (wrong amount, broken JSON) and confirm each filter catches them.

**Mistakes to avoid:**
- Using eval emails as few-shot examples in the generator prompt.
- Reporting the score on a synthetic eval set.

### Q. Your first LoRA adapter for ticket triage passed offline evaluation. It must go live on a shared vLLM cluster that already serves the base model to three other features, with a canary and a rollback that takes under a minute. Plan the release.

**Short answer (45 seconds):** Ship the adapter as an immutable versioned bundle, load it beside the current version on the existing base with vLLM's multi-LoRA support, and route by alias at the gateway: a small hashed slice of triage traffic goes to the new adapter, the rest stays on the old one. Rollback is flipping the alias back, with no reload, because both versions stay loaded. The other features are untouched because the base does not change.

**Deeper explanation:** The bundle holds the adapter weights and `adapter_config.json` (its `base_model_name_or_path` must match the served base and revision), the chat template hash, generation defaults, dataset version and eval report, at a write-once path such as `s3://models/triage/v3/`.

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --enable-lora --max-lora-rank 32 --max-loras 4 \
  --lora-modules triage-v2=/models/triage/v2 triage-v3=/models/triage/v3
curl -s http://vllm:8000/v1/models   # both adapter names must appear
```

If restarts are costly, vLLM can load adapters at runtime through `POST /v1/load_lora_adapter` when started with `VLLM_ALLOW_RUNTIME_LORA_UPDATING=True`; lock that endpoint down, since anyone who reaches it can change the model.

Clients send the adapter name as the `model` field, so the gateway owns the mapping (`triage@prod` to `triage-v2`, `triage@canary` to `triage-v3`) and picks the canary by hashing the user id so each user sees one version. Watch per version: schema failure rate, human edit or override rate, latency, and the other three features' p95, because enabling LoRA reserves GPU memory and can shrink the KV cache. Promote in steps, for example 5, 25 and 100 percent, each with a fixed observation window. Risk to plan for: an adapter is valid only for the exact base it was trained on.

**Follow-ups they will ask:**
- The platform team wants to upgrade the base model: Every adapter is retrained and re-evaluated on the new base; run both stacks side by side and move features one at a time.
- Merge instead?: Only if triage gets its own GPUs; on a shared base, adapters are the point.
- What triggers automatic rollback?: Schema failures or edit rate above the previous version's band during the window.

**Mistakes to avoid:**
- Overwriting adapter files in place, which breaks rollback and caching.
- Testing only in a notebook and not through the gateway path users hit.

### Q. An intent-and-entity extraction step runs on every message in your agent and calls a frontier API. Product wants p95 under 400 ms on hardware you own. How do you get there?

**Short answer (45 seconds):** Distil it. Log real inputs, label them with the frontier model as teacher, fine-tune the smallest student that matches the teacher on a human-checked eval set, merge it and serve it on vLLM with a short prompt, and route low-confidence cases back to the teacher. I load-test at production concurrency before promising the number, because single-request latency is not p95.

**Deeper explanation:** Clarify the output shape first: an intent plus a few fields is tens of output tokens, so queueing, prompt processing and time to first token dominate, and a short prompt and a small model move them. Also ask the request rate, the accuracy floor (for example "within two points of the teacher"), and whether some cases may take the slow path.

Plan: sample tens of thousands of real inputs across intents, label them with the teacher's best prompt, filter with schema checks and spot reviews, and keep a separate human-labelled eval set. Train students at two or three sizes (say 1B, 3B, 8B) with LoRA, merge, optionally quantise to FP8 or AWQ, and pick the smallest that passes. The instructions now live in the weights, so the serving prompt shrinks to the message plus a short tag.

```text
message -> student (vLLM, merged, short prompt)
             | confidence >= threshold -> result
             | otherwise -> teacher API (slow path, logged as future training data)
```

Confidence can come from the log-probability of the intent token, calibrated on the eval set. Risks: the student copies teacher errors, and intents drift after launch. Measure student-teacher agreement, accuracy against human labels, fallback rate, p50 and p95 under realistic concurrent load, and cost per thousand requests.

**Follow-ups they will ask:**
- Would a classifier beat a generative model?: For a fixed label set a small encoder classifier is often faster still; keep the generative student for the entity fields.
- Soft-label distillation?: It needs the teacher's full probability distributions, which APIs do not expose, so hard labels are the practical path.

**Mistakes to avoid:**
- Benchmarking one request at a time and calling it p95.
- Scoring the student only against teacher outputs instead of human labels.

### Q. Your LangGraph agent runs a self-hosted 8B model so data stays on-premises. Langfuse traces show it picks the wrong tool or sends arguments that fail validation often enough that retries double latency. What do you do?

**Short answer (45 seconds):** Separate syntax from choice. Malformed arguments I fix first without training: JSON-schema constrained decoding, fewer and clearer tools, stricter descriptions. Wrong tool choice is behaviour, so if it persists I fine-tune on curated trajectories from the traces, including cases where the right move is no tool or a clarifying question, and I gate on tool accuracy and end-to-end task success in a replay sandbox.

**Deeper explanation:** Start by labelling a few hundred failed traces by cause: wrong tool, right tool with bad arguments, should have asked, should have answered directly, or a misleading tool description. That table is both the plan and the baseline.

Build the dataset from verified successes (tool succeeded and a human approved), failures corrected by a reviewer or a stronger model, and negatives. Render every row with the model's own chat template, passing that row's tool definitions through the template's `tools=` argument, so training uses exactly the call format the server parses; in vLLM, `--enable-auto-tool-choice` with a `--tool-call-parser` such as `hermes` or `llama3_json` must match what the model emits. Put loss on assistant turns, including tool calls, not on tool results. Shuffle tool order and train with varying tool subsets so the model reads descriptions instead of memorising positions.

```json
{"messages": [
  {"role": "user", "content": "Move my 3pm with Ravi to Thursday"},
  {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": "find_event", "arguments": {"attendee": "Ravi", "time": "15:00"}}}]},
  {"role": "tool", "content": "{\"event_id\": \"ev_91\", \"start\": \"2026-11-03T15:00\"}"},
  {"role": "assistant", "content": "Which time on Thursday works for you?"}
]}
```

Risk: tool schemas change, so version the dataset per schema version. Measure tool-name accuracy, argument validity and semantic match, over-calling rate, retries per task, and task success on replayed real requests with tools mocked.

**Follow-ups they will ask:**
- A new tool ships next month?: Varied tool subsets help it generalise; still add examples for it and re-run the replay suite.
- Is constrained decoding enough?: It guarantees valid JSON, not the right tool or the right values.
- Where do negatives come from?: Traces a human overrode, plus written cases where no tool is needed.

**Mistakes to avoid:**
- Training only on successful calls, so the model never learns to ask.
- Training on one tool-call format and serving with a parser for another.

### Q. You have a single 24 GB GPU (or two free-tier T4s), one week, and training examples of 4k to 8k tokens. Leadership wants an 8B fine-tune. Plan the run.

**Short answer (45 seconds):** QLoRA with gradient checkpointing, a per-device batch of 1 with gradient accumulation, a paged 8-bit optimizer, and Unsloth or at least an efficient attention kernel. Before the real run I measure the token-length distribution and peak memory on the longest batch, debug the whole pipeline on a tiny model and a 1 percent slice, and checkpoint to object storage so a crash or preemption costs minutes, not days.

**Deeper explanation:** Clarify the p50 and p95 token lengths, the example count, and whether 8B is really required or a 3B to 4B model with full context passes the eval.

Memory: the 4-bit 8B base is roughly 5 GB, the adapter and its optimizer state are small, and activations at 8k tokens dominate, which is what gradient checkpointing and batch size 1 address. Hardware matters: T4s are Turing GPUs, so no bf16 and no FlashAttention 2 (it needs Ampere or newer); use fp16 carefully with PyTorch's SDPA attention. On two T4s, data-parallel training puts a full copy of the 4-bit model on each card, which works for 8B QLoRA, but the effective batch doubles, so halve the accumulation steps.

```python
from trl import SFTConfig

cfg = SFTConfig(
    output_dir="out",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    gradient_checkpointing=True,
    optim="paged_adamw_8bit",
    group_by_length=True,
    save_steps=200,
    save_total_limit=2,
)
```

Measure tokens per second on a short run and multiply out to an ETA for the planned epochs, then decide early whether to cap length at the p95 or split documents. Risks: preemption and a missed ETA; if the week is at risk, renting an 80 GB GPU for a few hours is usually cheaper than days of working around the limit.

**Follow-ups they will ask:**
- What do you cut first on OOM?: Length outliers, then batch size, then LoRA rank; never truncate the answer part.
- Does 4-bit hurt quality?: Sometimes slightly; check the eval, and train bf16 LoRA on rented hardware if the gap matters.
- DeepSpeed CPU offload?: Possible but much slower; it helps fit full fine-tunes, not speed up QLoRA.

**Mistakes to avoid:**
- Starting the full run without a 50-step dry run on the longest batch.
- Treating `device_map="auto"` across two GPUs as parallel training; it splits layers so the cards take turns, which fits bigger models but adds no speed.

### Practice
- Take 50 real or public documents of one type (invoices, forms, drawings), score a prompted model per field, label each failure as knowledge, behaviour, syntax or arithmetic, and write a one-page decision: retrieve, train, constrain or code.
- Build a 200-row synthetic pipeline with three filters, plant 20 known-bad rows, and report each filter's catch rate and the overall acceptance rate.
- Serve a small base model on vLLM with two LoRA adapters, route between them by `model` name through a tiny gateway, and time a rollback done by flipping the alias.
- Say it out loud: in two minutes, take "fine-tune a small model to replace our frontier API call" and cover baseline, data, student size, serving, fallback and the numbers you would report.

## Fine-tuning Incidents & Error Cases [Scenarios]

> Incident questions test whether you debug training and serving like any other production system. Use the same five beats every time: clarify impact (a training run burning GPU hours, or a model in front of users, and which versions), contain (stop the run, roll the alias back, route traffic to the previous adapter), diagnose (read logs and curves first, reproduce on a small fixed batch, change one variable at a time against a known-good baseline), fix, and prevent (a validator, a pipeline check, an alert, a runbook entry). A strong answer separates training-time causes from serving-time causes early, because many "the model got worse" reports after a deploy are template, tokenizer or routing mismatches, not bad weights.

### Concepts you must understand
- Separate the two failure surfaces: training time (loss curves, memory, data, hyperparameters) and serving time (chat template, tokenizer files, adapter routing, sampling settings, quantisation).
- Keep a known-good reference for every comparison: the base model, the previous version, and a fixed smoke set of 20 to 50 prompts run with greedy decoding so differences mean something.
- Reproduce small before rerunning big: one GPU, a tiny model or a data slice, `max_steps` around 20, and the exact batch that failed.
- Log enough to debug after the fact: loss, eval loss, `grad_norm`, learning rate, tokens per step, peak memory, dataset hash, base model revision and library versions.
- Every incident ends as an automated check, so the same failure cannot reach users twice.

| Symptom or error | First check | Likely causes | Fix |
| --- | --- | --- | --- |
| Training log shows `loss` and `grad_norm` as `nan` | First bad step in `trainer_state.json`, and the precision setting | fp16 overflow, learning rate too high or no warmup, a batch with no trainable tokens | bf16 where supported, lower LR with warmup, gradient clipping, drop rows whose labels are all -100 |
| `CUDA out of memory. Tried to allocate ...` mid-run | Whether it failed in a train step, eval or save, and the longest sequence in that batch | Length outliers, eval batch larger than train batch, logits kept for metrics, another process on the GPU | Cap length, `group_by_length`, smaller eval batch, `eval_accumulation_steps`, gradient checkpointing |
| `RuntimeError: element 0 of tensors does not require grad and does not have a grad_fn` | `print_trainable_parameters()` and whether gradient checkpointing is on | Gradient checkpointing on a frozen PEFT model without input gradients, or LoRA never attached | `model.enable_input_require_grads()` or PEFT's `prepare_model_for_kbit_training`, check `target_modules` |
| Train loss keeps falling, eval loss rising since the first epoch | Eval loss per checkpoint and the near-duplicate rate in the data | Too many epochs, LR too high, duplicated rows, tiny dataset | Early stopping with `load_best_model_at_end`, dedup, fewer epochs, pick among top checkpoints by task eval |
| Model never stops, `finish_reason` is `length` on most responses | Decode one training row and check the end-of-turn token carries a real label | Pad token equals EOS and padding is masked, end id missing from `generation_config.json` | Separate pad token, verify the end-token label, restore end ids, stop tokens at the server meanwhile |
| Responses contain chat-template tokens as visible text | Which tokenizer files the server loaded and how the token was tokenized in training | Template applied twice, special tokens split into plain text, tokenizer not saved with merged weights | Save tokenizer and template with the model, render with `apply_chat_template` once, pin the server's template |
| Adapter outputs identical to base under greedy decoding | The `model` field in the request and `GET /v1/models` | Request uses the base name, adapter not loaded, `lora_B` weights still zero, wrong file shipped | Route by adapter name, check B norms, rebuild the artifact from the tracked run |
| vLLM refuses to load an adapter because its rank exceeds the configured maximum | `r` in `adapter_config.json` versus `--max-lora-rank` | Adapter trained at a higher rank than the server allows | Raise `--max-lora-rank` (costs memory) or retrain at a lower rank |
| Offline eval jumps far above what the canary shows | Exact and n-gram overlap between train and eval | Eval rows or paraphrases in training, generator seeded with eval examples, grouped data split randomly | Rebuild the split by group, decontaminate, retrain, re-report both numbers |
| Tuned model answers everything in the task format or lost a language | Regression suite against the base, and which routes the gateway sends to the adapter | Narrow single-format data, high LR or many epochs, adapter applied to all traffic | Route only the task to the adapter, add replay data, lower LR and epochs, regression gate |
| Merged model scores lower than base plus adapter | Top-token agreement on fixed prompts across each artifact variant | QLoRA adapter merged into bf16 weights, merge on a 4-bit load, different base revision, missing tokenizer or generation files | Evaluate the exact served artifact, pin the base commit, ship tokenizer files, re-run evals after quantising |
| Same config gives different results on a rerun | Seeds, dataset hash, library versions, GPU count | Unpinned data or model revision, changed effective batch, nondeterministic kernels, different shuffling | Log and pin everything, `set_seed`, compare across several seeds, accept small variance |
| After DPO, answers are longer while judge win rate rises | Length of chosen versus rejected in the pairs, `rewards/margins` in TRL logs | Length bias in pairs or judge, `beta` too low, too many steps | Length-balanced pairs, length-controlled judging, higher `beta`, fewer steps, human spot checks |

### Q. A QLoRA run on a T4 shows `loss` and `grad_norm` as `nan` from step 1,200 after looking normal, and `grad_norm` had been spiking for the previous 100 steps. What do you do?

**Short answer (45 seconds):** Stop the run, keep the last checkpoint from before the spikes, and find the first bad step. Then check the three usual causes in order: fp16 overflow (T4s have no bf16), a learning rate too high for this point in the schedule, and a bad batch, especially one where every label is masked.

**Deeper explanation:** Diagnosis in order:

1. Read `log_history` in `trainer_state.json` for the step where `grad_norm` first jumped and the learning rate at that moment. Spikes that grow before the NaN point to instability (LR or precision); a clean curve that suddenly turns NaN points to one batch.
2. Precision: the largest fp16 value is 65504, and models pretrained in bf16 can produce activations beyond it, so values overflow to inf and then NaN. A T4 has no bf16, so lower the LR, keep the loss scaler on, or move to an Ampere-class GPU.
3. Data: if truncation cut off the assistant answer, every label is -100, and mean cross-entropy over zero tokens is 0/0, which is NaN.
4. Reproduce on the failing batch alone with `torch.autograd.set_detect_anomaly(True)` to find the first operation producing NaN (slow, so only on the repro).

The data check from step 3:

```python
bad = [i for i, ex in enumerate(train_tok)
       if all(l == -100 for l in ex["labels"])]
print(len(bad), bad[:10])
```

Fixes, ranked by how often they apply: drop rows with no trainable tokens and truncate the prompt side instead of the answer, lower the LR and add warmup, keep gradient clipping at `max_grad_norm=1.0` (the Trainer default) or lower, and use bf16 where the hardware supports it.

Prevent: a validator that rejects rows with zero trainable tokens, an alert when `grad_norm` exceeds a multiple of its running median, and frequent checkpoints.

**Follow-ups they will ask:**
- Resume from the last checkpoint?: Only after the fix; the same config hits the same wall.
- Why did it run fine for 1,200 steps?: Shuffling put the bad batch there, or the LR peaked after warmup.
- Loss drops close to zero within a few steps instead?: Suspect the answer leaking into the input, not fast learning.

**Mistakes to avoid:**
- Restarting with a new seed and hoping.
- Switching precision without checking the data.

### Q. Users report the fine-tuned assistant never stops: replies run until `max_tokens`, and some end with literal `<|eot_id|>` or `<|im_end|>` text. Walk me through it.

**Short answer (45 seconds):** Contain with explicit stop tokens and a tighter `max_tokens`, or roll back if the rate is high. Then check two things: whether training ever taught the model to emit its end-of-turn token (the classic bug is pad token equal to EOS with padding masked), and whether the server uses the same tokenizer files and chat template that training used.

**Deeper explanation:** Measure impact with `finish_reason` on the OpenAI-compatible API: `length` means the cap was hit, `stop` means the model ended on its own.

Training side: decode the tail of one tokenized row.

```python
row = train_tok[0]
tail = list(zip(tok.convert_ids_to_tokens(row["input_ids"][-5:]), row["labels"][-5:]))
print(tail)   # the end-of-turn token must carry its id, not -100
print(tok.pad_token, tok.eos_token)
```

If the pad token is the EOS token and the collator masks pad positions, the real EOS is masked too, so the model is never trained to stop. Use a pad token that is not the end-of-turn token and re-check the labels.

Serving side: visible template tokens mean either a special token was generated but not stripped, or training data contained it as plain text, for example a template applied in preprocessing and again by the trainer, or tokens split into characters because the tokenizer did not know them. Check `generation_config.json` too: Llama 3 instruct models list more than one end id, and a merged checkpoint saved without the right ones stops on the wrong token. Confirm the merged model directory includes the tokenizer and its chat template, or start vLLM with an explicit `--chat-template`.

Fix whichever side was wrong: retrain with a correct EOS label, or restore tokenizer files and end ids. Prevent: a pre-training test asserting the last labelled token is the end-of-turn id, a release check that diffs the server's rendered prompt against a training row, and an alert on the `length` share.

**Follow-ups they will ask:**
- Why not keep stop strings forever?: Fine as a guard, but the cause remains and quality still suffers.
- Only some prompts run on?: Look for long training answers truncated along with their EOS.
- Base fine, only the merge broken?: Diff tokenizer and generation files between the two directories.

**Mistakes to avoid:**
- Raising `repetition_penalty` to hide it.
- Debugging weights before diffing tokenizer and template files.

### Q. A run that worked yesterday now dies about 40 minutes in with `CUDA out of memory. Tried to allocate ...` on the same GPU. What do you check?

**Short answer (45 seconds):** A late crash on unchanged hardware usually means a specific batch or phase, not the model. I read the stack trace to see whether it died in a training step, evaluation or checkpoint save, check what changed in the data since yesterday, and look at the longest sequence in the failing batch and at other processes on the GPU.

**Deeper explanation:** Two quick looks first:

```bash
nvidia-smi --query-compute-apps=pid,used_memory --format=csv   # a stale notebook kernel?
python -c "import json;l=sorted(len(json.dumps(r)) for r in map(json.loads,open('train.jsonl')));print(l[len(l)//2],l[-1])"
```

The second line is a cheap proxy (characters, not tokens) for new outliers.

Ranked causes:
1. New long rows: yesterday's data refresh added a few very long examples, and the batch that contains one spikes activation memory. Cap the length, truncate the prompt side, or split documents.
2. Evaluation: `per_device_eval_batch_size` defaults to 8, often larger than the training batch, and with `compute_metrics` the Trainer keeps logits of shape batch x sequence x vocabulary. Lower the eval batch, set `eval_accumulation_steps`, or score by generation outside the trainer.
3. Fragmentation: if the message reports a lot of memory reserved but unallocated, set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, as the error text itself suggests.
4. Save or merge: merging on the training GPU needs a 16-bit copy of the whole model; do it in a separate process.

Then the standard levers: gradient checkpointing, batch size 1 with more accumulation, a paged 8-bit optimizer, and `group_by_length=True`, whose sampler deliberately puts the longest batch first so an OOM shows up at step one, not minute 40.

Prevent: a preflight that runs one train step and one eval step on the longest batch, a token-length limit in the data validator, and peak memory (`torch.cuda.max_memory_allocated()`) logged per run so you see the margin shrinking.

**Follow-ups they will ask:**
- Does `torch.cuda.empty_cache()` fix it?: Rarely; it releases cached blocks but does not reduce what the step needs.
- OOM only with more GPUs?: Check whether the launcher config changed the per-device batch or sequence length.
- Lower the max length globally?: Fine if answers are not cut; truncated answers trade an OOM for bad training data.

**Mistakes to avoid:**
- Lowering the batch size blindly without finding the failing phase.
- Truncating from the right so the assistant answer disappears.

### Q. You deployed the new adapter, and on greedy decoding its outputs are identical to the base model, token for token. What happened?

**Short answer (45 seconds):** Identical, not just similar, means the adapter is not in the request path or is a no-op. I check the request first (is the adapter name sent as `model`, does `GET /v1/models` list it), then the artifact (are the `lora_B` weights non-zero), then the training run.

**Deeper explanation:** Diagnosis in order:

1. Routing: vLLM selects an adapter by the `model` field, so a client or gateway still sending the base model id gets the base model, the most common cause. Check `/v1/models`, the gateway config, and that the server started with `--enable-lora`.
2. Artifact: LoRA initialises the B matrix to zero, so an adapter that never trained is an exact identity. Inspect the norms (snippet below).
3. Training: all-zero B norms point to a learning rate of zero from a scheduler mistake, `max_steps` far too small, or a file saved before training; compare timestamps and the run id in the bundle metadata. Non-zero but tiny norms point to a very low LR or a small `lora_alpha` relative to `r`.
4. Coverage: `target_modules` in `adapter_config.json` may hit only a few modules; the `print_trainable_parameters()` line in the training log shows how much was trainable.
5. Base mismatch: `base_model_name_or_path` in the adapter config should match what the server loaded.

```python
from safetensors.torch import load_file
sd = load_file("adapters/triage-v3/adapter_model.safetensors")
norms = {k: v.norm().item() for k, v in sd.items() if "lora_B" in k}
print(len(norms), max(norms.values()))   # all zeros: the adapter never trained
```

Fix the routing or rebuild the artifact from the tracked run, then re-run the eval against the served endpoint.

Prevent: a release gate that runs the smoke set against base and adapter through the gateway and fails if outputs are identical or the task metric does not improve, plus a deploy check that the adapter name appears in `/v1/models`.

**Follow-ups they will ask:**
- Outputs differ slightly but quality is flat?: The adapter loaded but learned little; review the loss curve, data size and LR.
- Can vLLM silently fall back to the base?: An unknown name returns an error; the base name is valid, which is why the mistake looks silent.

**Mistakes to avoid:**
- Retraining before checking which model the request hit.
- Testing with `PeftModel` in a notebook and assuming the server does the same.

### Q. Adding synthetic data lifted your offline eval from the low 70s to the mid 90s, but the canary shows no improvement in production. What do you suspect and how do you prove it?

**Short answer (45 seconds):** A jump that large with no production effect is a leak until proven otherwise. I stop quoting the number, check exact and near-duplicate overlap between training rows and the eval set, and trace how the synthetic data was generated, because a generator prompted with eval examples produces paraphrases of the test.

**Deeper explanation:** Diagnosis in order:

1. Exact overlap: normalise (lowercase, collapse whitespace, strip ids) and hash inputs and outputs on both sides.
2. Near-duplicates: n-gram overlap (13-gram matching is a common decontamination heuristic), MinHash, and embedding similarity for paraphrases (snippet below).
3. Lineage: did the generator's few-shot examples or seed list include eval rows? Were eval prompts built from the same templates as training prompts, so the eval tests the template rather than the task?
4. Grouping: did the same customer, document or project land on both sides of a random split?
5. No leak found: the eval may simply be unlike production, for example clean synthetic inputs versus messy real ones; compare eval and canary inputs on length, language and intent mix.

```python
def grams(text, n=13):
    w = text.lower().split()
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}

train_g = set().union(*(grams(r["text"]) for r in train))
hits = [e["id"] for e in eval_set if grams(e["text"]) & train_g]
print(len(hits), "of", len(eval_set), "eval rows share a 13-gram with train")
```

Fix: drop contaminated eval rows or rebuild the eval from a fresh production sample, remove overlapping training rows, retrain, and re-report both the original and corrected numbers to everyone who saw the first one.

Prevent: keep the eval set in its own versioned store with hashes, fail the training job if overlap with it is above zero, never give eval data to the generator, and refresh part of the eval from production each cycle.

**Follow-ups they will ask:**
- Overlap is zero and the gap remains?: Then it is distribution shift; build the eval from production traffic.
- Keep the model anyway?: Only if the corrected eval still beats the previous version.
- Does this apply to public benchmarks?: Yes, decontaminate training data against any benchmark you report.

**Mistakes to avoid:**
- Celebrating the number before checking lineage.
- Deduplicating after splitting instead of before.

### Q. Two weeks after launch, support says the assistant answers general questions in ticket JSON and its Arabic replies got worse. How do you handle it?

**Short answer (45 seconds):** First confirm scope: is this forgetting, or is the gateway sending all traffic to a task-specific adapter? Contain by routing non-triage traffic back to the base model or rolling back, then run the regression suite on base versus adapter to measure what was lost, and fix the data mix before retraining.

**Deeper explanation:** Diagnosis in order:

1. Routing: check the gateway config and Langfuse traces by route. If general chat reaches the triage adapter, the adapter is doing exactly what it was trained for, and the fix is routing.
2. Measure the regression against the base on the same harness (command below), then run it without `peft=` for the base, plus your own Arabic and general-prompt sets sliced by language.
3. Read the training data: if every row had the same system prompt and a JSON answer, the model learned "always JSON" and stopped reading the instruction; if it was English only, nothing held Arabic quality in place.
4. Read the run: a high LR, many epochs or a high rank all increase drift from the base.

```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-3.1-8B-Instruct,peft=adapters/triage-v3 \
  --tasks ifeval --batch_size 8 --output_path evals/triage-v3
```

Fix, cheapest first: scope the adapter to the triage route; retrain with a replay slice of general instructions and Arabic examples (an illustrative 10 to 20 percent), vary system prompts and include rows where the instruction asks for prose; lower the LR or epochs. Scaling the adapter down toward the base can recover general ability at some task cost, so measure both sides.

Prevent: a release gate that fails if any regression slice (per language, general instructions, safety) drops beyond a set tolerance against the base, and a routing test in CI that asserts which routes use which adapter.

**Follow-ups they will ask:**
- Triage metric is great, ship anyway?: Not while the adapter serves general traffic; users feel the regression, not the metric.
- Does a lower LoRA rank prevent this?: It lowers the risk; only the regression suite proves it.
- How fast can you contain?: Seconds, if routing is an alias in the gateway.

**Mistakes to avoid:**
- Retraining before checking routing.
- Measuring only English when users are bilingual.

### Q. The merged model you deployed scores several points below the base-plus-adapter you evaluated, on the same eval set. Find the difference.

**Short answer (45 seconds):** Something differs between what was evaluated and what is served, and I find it by comparing artifacts step by step on fixed prompts: the 4-bit base plus adapter that training saw, a bf16 base plus adapter, the bf16 merged model, and the quantised model behind vLLM. Where top-token agreement drops is the culprit, and often it is missing tokenizer files or different generation defaults, not weights.

**Deeper explanation:** Compare with teacher forcing on the same 50 prompts so sampling cannot hide anything:

```python
import torch
agree = []
for p in prompts:
    ids = tok(p, return_tensors="pt").to("cuda")
    with torch.no_grad():
        a = adapter_model(**ids).logits.argmax(-1)
        m = merged_model(**ids).logits.argmax(-1)
    agree.append((a == m).float().mean().item())
print(sum(agree) / len(agree))   # near 1.0 for a correct bf16 merge
```

Ranked causes:
1. Serving, not weights: the merged directory lacks the tokenizer or chat template, `generation_config.json` differs (temperature, end ids), or `max_model_len` truncates long prompts. Diff the files and the rendered prompt.
2. QLoRA mismatch: the adapter was trained against 4-bit weights, and merging it into a bf16 base gives a slightly different function. Usually small; if it matters, compare the 4-bit and bf16 unmerged variants, or train a short bf16 LoRA for the release.
3. Merging into a 4-bit loaded model rounds the merged weights, and PEFT warns about it; merge into a bf16 load instead.
4. A different base revision at merge time, because the hub's main branch moved and the adapter config names a repo, not a commit.
5. Post-merge quantisation (AWQ, GPTQ, GGUF) too aggressive for this task.

Fix the identified step and re-run the eval. Prevent: the release pipeline evaluates the exact artifact through the serving stack, records the base commit hash in the bundle, ships tokenizer and generation files with every merged model, and repeats the eval after every quantisation.

**Follow-ups they will ask:**
- Why not serve the adapter unmerged?: A fine option on a shared base, at a small per-token cost.
- How much quantisation loss is acceptable?: Whatever your eval tolerance says, decided before you look.

**Mistakes to avoid:**
- Comparing a notebook eval to a production eval with different sampling.
- Assuming a merge after a 4-bit load is lossless.

### Q. After a DPO round, the judge's win rate went up, but users complain that answers are much longer and full of hedging and flattery. What happened and what do you change?

**Short answer (45 seconds):** The model learned the proxy, not the goal: the preference pairs or the judge rewarded length and agreeable tone, and DPO optimised exactly that. I keep the SFT model in production, measure length and hedging against the SFT baseline, inspect the pairs for length bias, and retrain with balanced pairs, a stronger pull toward the reference model and a length-aware evaluation.

**Deeper explanation:** Diagnosis in order:

1. Pairs: compare token lengths of chosen and rejected answers (snippet below). If the chosen answer is longer in most pairs, "longer wins" is the easiest pattern for DPO to learn.
2. Judge: LLM judges tend to prefer longer, polished answers; re-score a sample with length control and check judge-human agreement on about 100 items.
3. Training logs: in TRL's DPO metrics, `rewards/margins` racing upward while `logps/chosen` falls means the model is pushing rejected answers down rather than learning good ones; a low `beta` lets the policy drift far from the reference.
4. Steps: several epochs over a small pair set overfits the preference.

```python
import statistics as st
d = [len(tok(p["chosen"]).input_ids) - len(tok(p["rejected"]).input_ids) for p in pairs]
print(st.mean(d), sum(x > 0 for x in d) / len(d))   # share of pairs where the longer answer won
```

Fix: rebuild the pairs so length is balanced (include pairs where the shorter answer wins, and pairs that penalise hedging and flattery), raise `beta`, train fewer steps, keep an SFT loss on chosen answers or switch to ORPO, which builds one in, and evaluate with a length-controlled win rate plus a human sample.

Prevent: the release gate tracks response length, hedge-phrase rate and refusal rate against the SFT baseline next to the win rate, and production monitoring alerts on response-length drift.

**Follow-ups they will ask:**
- Just add "be concise" to the system prompt?: It helps a little, but the weights now push the other way; fix the data.
- Would GRPO avoid this?: Only with a verifiable reward; with a learned judge it has the same exposure.
- When is a higher win rate trustworthy?: When it survives length control and humans agree with it.

**Mistakes to avoid:**
- Reporting judge win rate without length statistics.
- Using the same model as generator and judge, which rewards its own style.

### Practice
- Break it on purpose: fine-tune a 0.5B to 1.5B instruct model for 200 steps with the pad token set to the EOS token and padding masked, serve it, and record the share of `finish_reason` equal to `length`; then fix the pad token, retrain, and compare.
- Copy 5 percent of the eval rows into training, retrain, and watch the offline score jump while a fresh production-like set does not move; then add an overlap check that fails the job.
- Reproduce a NaN by training in fp16 with a learning rate ten times too high and no warmup, find the first bad step in `trainer_state.json`, and fix it with warmup and a lower LR.
- Say it out loud: pick any row from the table above and answer it in 90 seconds using impact, contain, diagnose, fix, prevent.
