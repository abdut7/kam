## Preference Optimization & RL Intuition

> Interviewers use this section to separate people who have read a blog post from people who understand the training stack. Nobody expects you to have run PPO, but you should explain why preference data exists, what a reward model is, why DPO replaced PPO for most teams, what GRPO and verifiable rewards changed, and how reward hacking shows up. A weak answer says "RLHF makes the model nicer"; a strong one gives the objectives, the data shapes, and when you would not bother.

### Concepts you must understand
- SFT teaches from demonstrations ("here is a good answer"); preference tuning teaches from comparisons ("this answer is better than that one"), which captures qualities that are easier to judge than to write.
- Classic RLHF: train a reward model on human preference pairs, then optimise the policy with PPO to maximise reward while a KL penalty keeps it close to the SFT reference.
- A reward model is usually the LLM with a scalar head trained with the Bradley-Terry loss `-log sigmoid(r(x, y_w) - r(x, y_l))`.
- PPO needs four models in memory (policy, reference, reward, value), online sampling, and careful tuning; it is powerful and expensive.
- DPO removes the reward model and the sampling loop: it optimises the policy directly on preference pairs against a frozen reference with a closed-form loss, so it runs like SFT.
- ORPO folds a preference term into SFT with no reference model; KTO works from unpaired thumbs-up or thumbs-down labels.
- GRPO samples a group of answers per prompt and uses group-relative advantages instead of a value model; paired with verifiable rewards (tests, exact answers, validators) it is the recipe behind recent reasoning models.
- Reward hacking is the policy finding outputs the reward likes but humans do not: length, flattery, format tricks, gaming tests; KL penalties, better rewards and human evals are the defences.
- SFT alone covers most product fine-tunes; preference tuning earns its cost when quality is subjective, when you have comparison data, or when you need to suppress specific failure modes.

### Q. Explain RLHF at a high level. What is a reward model and why was PPO used?

**Short answer (45 seconds):** RLHF turns human judgements into a training signal. Humans compare pairs of model answers; a reward model learns to predict which one they prefer and outputs a score for any answer; then the language model is trained with reinforcement learning to produce answers that score highly, with a KL penalty that keeps it from drifting far from the supervised model. PPO was the RL algorithm of choice because it takes stable, clipped policy updates, which matters when each sample is an entire generated response.

**Deeper explanation:** The reward model is typically the same transformer with a scalar head, trained with the Bradley-Terry objective: for a prompt x with preferred answer y_w and rejected y_l, maximise `log sigmoid(r(x, y_w) - r(x, y_l))`. It learns relative, not absolute, quality. The policy objective is then `maximise E[r(x, y)] - beta * KL(pi || pi_ref)`: get high reward, but stay close to the reference distribution so the model keeps its language quality and does not collapse onto whatever the reward model over-rates.

```text
prompts --> policy samples answers --> reward model scores --> PPO update to policy
                                   \-> reference model gives log-probs for the KL penalty
                                   \-> value model estimates expected reward (baseline)
```

Operationally that is four large models in memory, generation inside the training loop (slow), and sensitive hyperparameters (KL coefficient, clip range, learning rate). It works at scale but is a heavy lift for a product team, which is the gap DPO filled.

**Follow-ups they will ask:**
- Why is a KL penalty needed?: Without it the policy exploits the reward model and produces degenerate text that scores well but reads badly.
- Why not optimise human preferences directly?: Humans are too slow and expensive to score every sample; the reward model is a learned, scalable proxy.
- What is RLAIF?: The same loop with an AI model providing the preference labels instead of humans.

**Mistakes to avoid:**
- Saying the reward model "is" the policy, or that humans score each training sample.
- Omitting the reference model and KL term, which are the heart of why it works.

### Q. What is DPO, and why has it largely replaced PPO for product teams?

**Short answer (45 seconds):** Direct Preference Optimization skips the reward model and the RL loop. A reparameterisation shows the optimal policy under the RLHF objective can be trained directly from preference pairs with a classification-style loss: raise the log-probability of the chosen answer relative to the reference model, lower it for the rejected one, scaled by beta. It needs two models (policy and frozen reference), no sampling during training, and runs on SFT infrastructure, so it is cheaper, more stable and easier to debug.

**Deeper explanation:** The loss for a pair is `L = -log sigmoid( beta * [ (log pi(y_w|x) - log pi_ref(y_w|x)) - (log pi(y_l|x) - log pi_ref(y_l|x)) ] )`. Each bracket is the policy's shift from the reference on that answer; the loss pushes the chosen shift above the rejected one. Beta plays the KL role: small beta lets the policy move far from the reference, large beta keeps it conservative; 0.1 is a common start.

```python
import torch.nn.functional as F

def dpo_loss(pi_logp_w, pi_logp_l, ref_logp_w, ref_logp_l, beta=0.1):
    margin = (pi_logp_w - ref_logp_w) - (pi_logp_l - ref_logp_l)
    return -F.logsigmoid(beta * margin).mean()
```

Data is a JSONL of `prompt`, `chosen`, `rejected`. TRL's `DPOTrainer` handles the reference model (the frozen initial weights, or with LoRA simply the adapter disabled) and the log-prob computation. Learning rates are far lower than for SFT, around 5e-7 to 5e-6, for one or two epochs. DPO is offline: it learns from fixed pairs, so if they are far from what the current policy generates the signal weakens; iterative DPO (regenerate pairs from the latest policy, re-label, retrain) recovers some on-policy advantage.

**Follow-ups they will ask:**
- Where do the pairs come from?: Humans or a judge comparing two sampled answers, or implicit signals such as accepted versus edited outputs.
- What does a bad DPO run look like?: Chosen and rejected log-probs both fall, or outputs get much longer; watch reward margins and lengths, not only the loss.
- Can you combine SFT and DPO?: Yes, SFT first, then DPO on pairs; skipping SFT often makes DPO unstable.

**Mistakes to avoid:**
- Using an SFT-sized learning rate for DPO and wrecking the model.
- Calling DPO "RL"; it is a supervised objective derived from the RL formulation.

### Q. ORPO and KTO: when would you pick them over DPO?

**Short answer (45 seconds):** ORPO merges SFT and preference learning into one pass with no reference model: it adds an odds-ratio term that favours the chosen response over the rejected one on top of the normal SFT loss, so you train once and skip the reference model. KTO drops the need for pairs entirely: each example is a single response labelled desirable or undesirable, which matches real product feedback such as thumbs up or down, edits, or escalations. Pick DPO when you have clean pairs and an SFT model; ORPO when you want a single training stage; KTO when your feedback is unpaired.

**Deeper explanation:** The data shapes are the practical difference:

```text
DPO:  {"prompt": ..., "chosen": ..., "rejected": ...}          pairs, same prompt, after SFT
ORPO: {"prompt": ..., "chosen": ..., "rejected": ...}          pairs, single stage, no reference model
KTO:  {"prompt": ..., "completion": ..., "label": true|false}  unpaired, imbalance tolerated
```

ORPO's odds-ratio term is `log( odds(y_w) / odds(y_l) )` with `odds(y) = p(y|x) / (1 - p(y|x))`, weighted and added to the SFT cross-entropy on the chosen answer. With no reference it is memory-light and simple, but less controllable: there is no beta to keep it close to a known-good model. KTO is built on prospect theory, weighting gains and losses asymmetrically around a reference point estimated from the batch, and it tolerates many more negatives than positives, which is normal in production feedback.

In practice, a well-behaved SFT model plus a few thousand pairs gets the most predictable results from DPO; a stream of accept and reject events points to KTO; ORPO fits when compute is tight and you train in one stage.

**Follow-ups they will ask:**
- Can you convert thumbs data into DPO pairs?: Sometimes, by pairing a thumbs-up and a thumbs-down answer to the same prompt, but most prompts have only one answer, which is why KTO exists.
- Do these need a huge dataset?: Thousands of examples are typical; quality and clear contrast between good and bad matter more than count.
- What about SimPO or IPO?: Variants with different margins or normalisation; the same decision logic applies.

**Mistakes to avoid:**
- Treating these as interchangeable without looking at what feedback data you actually have.
- Running preference tuning on noisy thumbs data without first cleaning obvious mislabels.

### Q. What is GRPO, and what does "reinforcement learning with verifiable rewards" mean?

**Short answer (45 seconds):** GRPO is a PPO-style algorithm without a value model. For each prompt it samples a group of answers, scores each, and uses the score relative to the group mean as the advantage, so better-than-average answers are pushed up and worse ones down. Verifiable rewards means the score comes from a checker, not a learned reward model: a unit test passes, the maths answer matches, the JSON validates, the SQL returns the right rows. Together they are the recipe behind recent reasoning models.

**Deeper explanation:** For a prompt x, sample G answers y_1 ... y_G and compute rewards r_1 ... r_G. The advantage is `A_i = (r_i - mean(r)) / (std(r) + epsilon)`. The policy is then updated with a clipped PPO-style objective weighted by A_i, plus a KL term toward a reference model. Illustrative: G = 8, five answers fail a test (reward 0) and three pass (reward 1); the mean is 0.375, so passing answers get positive advantage and failing ones negative, with no critic network needed.

```text
prompt --> sample G answers --> verifier scores each (0/1 or graded)
       --> advantages relative to the group --> policy update (clip + KL)
```

Why verifiable rewards matter: a learned reward model can be hacked, while "tests pass" or "answer equals 42" is far harder to game, and you can generate unlimited prompts as long as you can check them. The limit is scope: only tasks with a checker qualify; a kind customer email has no verifier, so that is preference-tuning territory. Reward design still needs care: models learn to print the expected answer without reasoning or to special-case tests, so you add format rewards, hidden tests, and process checks.

**Follow-ups they will ask:**
- Why drop the value model?: It is as large as the policy and hard to train for whole-response rewards; group statistics give a free baseline.
- Where do product engineers use this?: Text-to-SQL, code against tests, extraction against schemas, agent tool-call sequences with checkable end states.
- Is GRPO available in TRL?: Yes, `GRPOTrainer` takes reward functions you write in Python.

**Mistakes to avoid:**
- Describing GRPO as "DPO with groups"; it is on-policy RL with sampled rewards.
- Claiming RLVR works for subjective tasks.

### Q. What is reward hacking? Give me examples and how you would defend against it.

**Short answer (45 seconds):** Reward hacking is when the policy finds outputs that score highly under your reward but are not what you wanted, because the reward is a proxy. Classic cases: answers get longer because judges prefer length, the model flatters the user because raters liked agreement, code special-cases the visible unit tests, and formatting tricks satisfy a validator without doing the task. Defences are the KL penalty to a reference model, rewards built from several signals, length normalisation, hidden held-out checks, and human evaluation on fresh samples before anything ships.

**Deeper explanation:** Any optimiser will exploit the gap between the metric and the intent, and RL is an aggressive optimiser running thousands of trials. Reward models trained on human pairs inherit human biases: length, confident tone, markdown headers, sycophancy. Verifiable rewards are hacked differently: a model asked to pass tests learns `if input == test_case_1: return expected` if the tests are visible, or learns that printing "the answer is" plus the gold format earns the format reward even when the reasoning is nonsense.

```text
Symptom                          Likely hack                  Counter
Average length rises steadily    verbosity bias in reward     length-normalised reward, length cap
Agrees with wrong user claims    sycophancy in pairs          adversarial pairs where agreeing is wrong
Passes train tests, fails new    test memorisation            hidden tests, mutate test inputs each epoch
Perfect JSON, wrong content      validator-only reward        add content checks or a judge
```

Monitoring during training matters as much as the loss curve: track mean response length, reward distribution, KL from reference, and a periodic human or strong-judge eval on prompts the reward model never saw. A rising reward with a falling human eval is the signature of hacking.

**Follow-ups they will ask:**
- Why does KL help?: It bounds how far the policy can move from a model you trust, limiting how exotic the exploits can get.
- Can reward model ensembles help?: Yes, disagreement between several reward models flags outputs that exploit one model's quirk.
- Does DPO suffer from this?: Less, because it is offline and bounded by beta, but length bias from the pairs still leaks in.

**Mistakes to avoid:**
- Treating a rising reward curve as success.
- Making tests or rubrics visible to the policy and then wondering why it memorised them.

### Q. When is SFT enough, and when do you need preference optimization?

**Short answer (45 seconds):** SFT is enough when you can write down what a correct answer looks like and produce enough examples of it: formats, schemas, tool calls, extraction, classification, a house style. Preference optimization earns its complexity when quality is a judgement rather than a specification: tone trade-offs, concision, helpfulness without over-refusal, safety boundaries, or when you already have comparison data from users. It is also the tool for suppressing specific failure modes the SFT model keeps producing, because you can put those failures in the rejected column.

**Deeper explanation:** Think about what each signal can express. SFT says "do this"; it cannot say "not that", so if the SFT model has a habit (hedging, adding disclaimers, inventing a field), more positive examples only dilute the habit. DPO pairs say "this over that", so one pair where the chosen answer omits the disclaimer and the rejected one includes it teaches the contrast directly. That makes preference tuning the fast path to fixing stubborn behaviours after SFT has done the heavy lifting.

```text
Stage ladder for a product model:
  1. SFT on 2k to 10k clean demonstrations      -> format, task, style
  2. Eval; collect failure modes                -> what SFT could not fix
  3. DPO or KTO on 1k to 5k pairs or labels     -> suppress failures, tune judgement
  4. (Optional) GRPO with verifiers             -> only if the task has a checker
```

The cost side: preference data is more expensive to produce than demonstrations because each example needs two candidates and a judgement, the training is more fragile, and the gains are easy to mis-measure if your eval uses the same judge that labelled the pairs. For many internal tools, a well-run SFT plus prompt and retrieval engineering is the end of the road, and saying so is a senior answer.

**Follow-ups they will ask:**
- How do you build pairs cheaply?: Sample two answers from the SFT model, have a strong judge or reviewer pick, and keep only confident, consistent picks.
- Does preference tuning replace guardrails?: No; it lowers the frequency of bad behaviour, guardrails and validators still catch the remainder.
- Can preference tuning hurt?: Yes, over-optimising on pairs can reduce diversity and increase verbosity; always compare against the SFT checkpoint.

**Mistakes to avoid:**
- Jumping to DPO before SFT and evals exist.
- Using the same judge to create pairs and to evaluate the result.

### Q. How would you turn production thumbs-up and thumbs-down feedback into training data?

**Short answer (45 seconds):** Carefully, because raw feedback is sparse, biased and noisy. I would log every response with its prompt, context, model version and feedback, clean obvious noise (accidental clicks, feedback about the UI rather than the answer), scrub PII, and then build two sets: thumbs-up responses that pass a judge become SFT or KTO positives, thumbs-down responses become KTO negatives or the rejected side of DPO pairs where I can produce a better answer for the same prompt. Then evaluate against a held-out set that is not derived from feedback.

**Deeper explanation:** Feedback has selection bias: people click when they are annoyed or delighted, so the labelled set is not representative of traffic, and negatives usually dominate. KTO tolerates imbalance and unpaired data, which makes it the natural first choice. To get DPO pairs you need a better answer for the same prompt, which you can produce by regenerating with a stronger model or a corrected prompt and having a judge or reviewer confirm it beats the original.

```text
feedback log row:
  {prompt, retrieved_context, response, model_version, feedback: up|down, edit_text?, ts, segment}
pipeline:
  filter noise -> PII scrub -> dedup prompts -> judge-check positives -> KTO set
  for downs with a regenerated better answer -> DPO pair (chosen = new, rejected = old)
```

Edits are gold: when an agent corrects the model's draft before sending, the edited text is a chosen answer and the draft is the rejected one for the same prompt, a natural pair with high signal. Also watch for feedback that reflects policy rather than quality (a user dislikes a correct refusal); those rows must not become negatives, or you train the model to comply with things it should refuse.

**Follow-ups they will ask:**
- How much feedback before it is useful?: Low thousands of clean labels is a reasonable starting point; measure on a fixed eval set, not on feedback rates.
- How do you avoid a feedback loop?: Keep an untouched eval set, compare each new model with the previous one, and cap how much training data comes from any one period.
- What about privacy?: Feedback rows are customer data; scrub, get the consent terms right, and keep the retention window short.

**Mistakes to avoid:**
- Training directly on raw thumbs data with no cleaning or judge check.
- Letting disliked-but-correct refusals become negative examples.

### Practice
- Take 500 prompts, sample two answers each from an SFT model, label them with a judge using order swapping, and run DPO with TRL at beta 0.1; compare response length, judge win rate against the SFT model, and a general regression set.
- Write a verifiable reward for text-to-SQL (execute against a fixture database and compare result sets), run GRPO for a small number of steps on a small model, and log mean reward, length and KL per step.
- Deliberately create a hackable reward (JSON validity only) and watch what the policy learns; then add a content check and compare.
- Say it out loud: explain to a sceptical staff engineer why you would do SFT first, when you would add DPO, and why you would not use PPO, in under two minutes.

## Tooling & Infrastructure

> Here the interviewer checks that you have actually run a job, not just read about one. Expect "what does each library do", "what GPU do I need", "how do you not lose a run when the spot instance dies", and "how do you compare two runs a month later". A weak answer lists library names; a strong one describes a working pipeline with the config, the hardware, the checkpoints and the tracking dashboard.

### Concepts you must understand
- Hugging Face Transformers loads models and tokenizers and provides the Trainer; Datasets loads and transforms data; PEFT adds adapters; TRL adds SFT, DPO, GRPO and reward-model trainers; Accelerate with its DeepSpeed and FSDP integrations handles multi-GPU; bitsandbytes handles 4-bit and 8-bit loading.
- Unsloth is a layer over this stack with hand-written kernels that make single-GPU LoRA and QLoRA faster and lighter, and it exports merged weights or GGUF directly.
- Axolotl and LLaMA-Factory are config-driven trainers (YAML) that wrap the same libraries, add many recipes and multi-GPU support, and remove most boilerplate at the cost of some flexibility.
- Hosted fine-tuning APIs (OpenAI, Google Vertex AI, Together, Fireworks, Mistral and others) take a JSONL file and return a model id; they remove infrastructure work and give up control of weights, hyperparameters and data location.
- GPU need is driven by weight precision, trainable parameter count and activations: QLoRA on 1B to 8B fits 16 to 24 GB; bf16 LoRA on 8B wants 40 to 80 GB; full fine-tuning of 8B is multi-GPU; 70B QLoRA fits one 80 GB card with short sequences (illustrative arithmetic).
- Colab-class GPUs are for experiments and small models; cloud GPUs (on-demand or spot) are for real runs, and spot pricing only works with frequent checkpoints.
- Checkpointing saves adapter weights, optimizer state and scheduler state so a run can resume after preemption; save often, keep few.
- Experiment tracking (Weights & Biases or MLflow) records config, dataset version, loss curves, eval metrics and artifacts so runs are comparable and reproducible.

### Q. Walk me through the Hugging Face stack. What do Transformers, Datasets, PEFT, TRL and Accelerate each do in a fine-tuning job?

**Short answer (45 seconds):** Transformers gives you the model and tokenizer classes and the base Trainer. Datasets loads JSONL or Parquet, maps and filters at scale, and streams if the data is too big for memory. PEFT wraps the model with LoRA or other adapters and handles saving and merging them. TRL supplies task-specific trainers: SFTTrainer for instruction data with chat templates and loss masking, DPOTrainer and GRPOTrainer for preference and RL, plus reward-model training. Accelerate makes the same script run on one GPU, several GPUs with FSDP or DeepSpeed, or a TPU with a config change.

**Deeper explanation:** A minimal QLoRA SFT job wires them together like this:

```python
import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

name = "meta-llama/Llama-3.1-8B-Instruct"
tok = AutoTokenizer.from_pretrained(name)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained(name, quantization_config=bnb, device_map="auto")
ds = load_dataset("json", data_files={"train": "train.jsonl", "validation": "val.jsonl"})
lora = LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM")
cfg = SFTConfig(output_dir="out", num_train_epochs=2, per_device_train_batch_size=2,
                gradient_accumulation_steps=8, learning_rate=2e-4, bf16=True,
                logging_steps=10, save_steps=200, report_to="wandb")
trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds["train"],
                     eval_dataset=ds["validation"], processing_class=tok, peft_config=lora)
trainer.train()
trainer.save_model("out/adapter")
```

The division of labour matters when something breaks: tokenisation and template issues are Transformers, data shape issues are Datasets or TRL, memory and device placement issues are PEFT, bitsandbytes or Accelerate. Parameter names have shifted between releases of these libraries, so pin versions in a lockfile and read release notes when upgrading.

**Follow-ups they will ask:**
- What does `device_map="auto"` do?: Places model layers across available GPUs and CPU to fit memory; it is for inference and single-process training, not for FSDP.
- Where does bitsandbytes fit?: It implements the 4-bit and 8-bit weight formats and the paged and 8-bit optimizers.
- Why TRL instead of the plain Trainer?: Chat template handling, completion-only loss, packing, and the preference trainers.

**Mistakes to avoid:**
- Listing the libraries without saying which layer owns which failure.
- Mixing `device_map="auto"` with multi-GPU distributed training.

### Q. What does Unsloth give you over plain TRL and PEFT, and what are its limits?

**Short answer (45 seconds):** Speed and memory on a single GPU. Unsloth replaces the attention, MLP and LoRA kernels with hand-written Triton kernels and a manual backward pass, so the same QLoRA job trains faster and uses less memory than the stock path, which is what lets an 8B model fine-tune on a 16 GB Colab GPU. It is a thin layer: you still use TRL's trainers and PEFT-style adapters, and it adds export to merged 16-bit weights or GGUF for llama.cpp and Ollama. The limits are scope: it targets single-GPU NVIDIA training for the architectures it has patched, and multi-GPU is not its main use case.

**Deeper explanation:** The API swaps the model loading and adapter attachment, then hands off to TRL:

```python
from unsloth import FastLanguageModel
from trl import SFTConfig, SFTTrainer

model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/Llama-3.1-8B-Instruct-bnb-4bit", max_seq_length=2048, load_in_4bit=True)
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth")
trainer = SFTTrainer(model=model, processing_class=tokenizer, train_dataset=ds, args=SFTConfig(...))
trainer.train()
model.save_pretrained_merged("out/merged", tokenizer, save_method="merged_16bit")
model.save_pretrained_gguf("out/gguf", tokenizer, quantization_method="q4_k_m")
```

The pre-quantised `unsloth/...-bnb-4bit` checkpoints skip quantisation at load time, which saves minutes and RAM. The `"unsloth"` gradient checkpointing mode offloads activations more aggressively than the standard implementation, which is where a chunk of the memory saving comes from. For a team doing single-GPU LoRA work, it is usually the fastest path from dataset to a GGUF you can run locally.

Where you stop using it: multi-node full fine-tuning, architectures it has not patched, or when you need the exact stock numerics for a like-for-like comparison.

**Follow-ups they will ask:**
- Does it change model quality?: It is designed to be numerically equivalent to the standard path; the gains are efficiency, so your evals should match.
- Can you load the Unsloth adapter in vLLM?: Yes, the saved adapter is a standard PEFT adapter; merged weights load anywhere.
- Is it free?: The open-source library is Apache 2.0; check their site for any paid offerings before relying on them.

**Mistakes to avoid:**
- Describing it as a different training method; it is an optimised implementation of LoRA and QLoRA.
- Assuming multi-GPU scaling works the same way as in Accelerate or Axolotl.

### Q. Axolotl, LLaMA-Factory, or your own script: how do you choose?

**Short answer (45 seconds):** Write your own TRL script when the job is simple or unusual and you want to understand every line; use Axolotl when you want a reproducible YAML-driven pipeline with battle-tested recipes, multi-GPU via DeepSpeed or FSDP, and sample packing without writing code; use LLaMA-Factory when you want the broadest menu of models and methods with a CLI and a web UI, which suits teams running many experiments across model families. All three sit on the same Transformers, PEFT and TRL foundations, so the choice is about ergonomics and reproducibility, not capability.

**Deeper explanation:** A config-driven trainer turns a run into a reviewable artifact:

```yaml
base_model: meta-llama/Llama-3.1-8B-Instruct
load_in_4bit: true
adapter: qlora
lora_r: 16
lora_alpha: 32
lora_target_linear: true
datasets:
  - path: data/train.jsonl
    type: chat_template
val_set_size: 0.05
sequence_len: 2048
sample_packing: true
micro_batch_size: 2
gradient_accumulation_steps: 8
num_epochs: 2
learning_rate: 0.0002
lr_scheduler: cosine
warmup_ratio: 0.03
output_dir: ./out/support-v3
wandb_project: support-triage
```

That file goes into git next to the dataset manifest, and `axolotl train config.yml` reproduces the run; the same file plus a DeepSpeed config scales to several GPUs. LLaMA-Factory works the same way with its own YAML and `llamafactory-cli train`, and adds a UI for people who prefer not to edit files. Your own script wins when you need custom loss masking, a bespoke data collator, or an unusual reward function for GRPO, and when you want to debug a single forward pass without a framework in the way.

The failure mode of frameworks is hidden defaults: packing, loss masking, template handling and special tokens are set by config keys you may not know exist. Read the printed effective config and decode a batch before trusting a run.

**Follow-ups they will ask:**
- Which one for multi-GPU?: Axolotl has strong DeepSpeed and FSDP support; LLaMA-Factory supports them too; plain TRL via Accelerate works with more manual setup.
- How do you keep runs reproducible?: Pin library versions, commit the config and dataset hash, fix seeds, and log the resolved config to the tracker.
- Do they support DPO and GRPO?: Both frameworks expose preference training; for GRPO with custom rewards the TRL script is usually simpler.

**Mistakes to avoid:**
- Choosing by popularity instead of by whether you can debug it under pressure.
- Trusting a framework's defaults for loss masking without checking a decoded batch.

### Q. When would you use a hosted fine-tuning API instead of training open weights yourself?

**Short answer (45 seconds):** When you want the behaviour change without owning infrastructure, when the vendor's model is already the best fit for the task, and when your data is allowed to leave your environment. Providers such as OpenAI, Google (Vertex AI), Mistral, Together and Fireworks take a JSONL of conversations, run SFT (and in some cases preference or reinforcement fine-tuning), and return a model id you call like any other. You trade control over weights, hyperparameters, portability and cost structure for a very short path to a result.

**Deeper explanation:** Advantages: no GPUs, no serving stack, the vendor handles scaling, and for proprietary models it is the only way to fine-tune at all. The data format is familiar (messages with roles), so the dataset work you did for open weights carries over, and your evals stay identical.

Disadvantages, stated neutrally: you do not receive the weights, so the model lives only with that vendor and disappears when they deprecate the base; hyperparameter control is limited to a few knobs (epochs, learning rate multiplier, batch size); inference on a fine-tuned model is usually priced above the base model; data residency and retention policies must be checked against your contracts, especially for regulated data; and you cannot run multi-adapter serving, quantise, or deploy on-premises.

```text
Decision sketch
  Data cannot leave the VPC, or on-device required      -> open weights, self-host
  Need weight portability, many tenants, edge           -> open weights
  Small team, moderate volume, vendor model fits task   -> hosted API
  Need GRPO or PPO with custom reward code              -> self-host (unless a vendor RFT offering is sufficient)
```

A reasonable hybrid is to prototype with a hosted fine-tune to prove the task is learnable, then port the same dataset to an open model when volume, cost or residency demands it.

**Follow-ups they will ask:**
- How do you compare the two fairly?: Same dataset version, same eval set, same judge; include latency and cost per thousand requests.
- What about lock-in for prompts versus fine-tunes?: Prompts port with edits; a hosted fine-tune does not port at all, only its dataset does.
- Can you distil a hosted fine-tune into an open model?: Only if the provider's terms allow using outputs for training; check first.

**Mistakes to avoid:**
- Dismissing hosted fine-tuning as "not real fine-tuning"; it is SFT on their hardware.
- Forgetting deprecation: a vendor retiring the base model retires your fine-tune.

### Q. What GPU do I need to fine-tune an 8B model? What about 70B?

**Short answer (45 seconds):** For 8B: QLoRA fits a 16 to 24 GB card (T4, L4, A10G, RTX 3090 or 4090) with short sequences and small batches; bf16 LoRA wants 40 to 80 GB; full fine-tuning needs several 80 GB GPUs with FSDP or ZeRO. For 70B: 4-bit weights alone are about 35 GB, so QLoRA fits one 80 GB card with short context, bf16 LoRA needs two to four, and full fine-tuning is multi-node. It is all bytes-per-parameter arithmetic plus activations, so I estimate first and then measure.

**Deeper explanation:** Illustrative, weights or state only:

| Model | bf16 weights (2 B/param) | 4-bit weights (~0.5 B/param) | Full FT state (16 B/param) |
| --- | --- | --- | --- |
| 3B | 6 GB | 1.5 GB | 48 GB |
| 8B | 16 GB | 4 GB | 128 GB |
| 70B | 140 GB | 35 GB | 1,120 GB |

Add the adapter and its optimizer state (small), activations (batch x sequence x hidden x layers, cut by checkpointing and Flash Attention) and a couple of gigabytes of CUDA overhead, then leave headroom: at 95 percent of memory every eval step or longer example OOMs. Throughput matters too: a T4 lacks native bf16 and is far slower than an L4 or A100.

Memory sizes to know: T4 16 GB, L4 and A10G 24 GB, RTX 3090 and 4090 24 GB, A100 40 or 80 GB, H100 80 GB. If the estimate is marginal, cut sequence length, then batch size, then go 4-bit, and only then buy a bigger card.

**Follow-ups they will ask:**
- Does 70B QLoRA on one 80 GB card train well?: It fits, but slowly and with limited sequence length, so most teams use two cards or a smaller model.
- How does sequence length change the picture?: Activations grow linearly (quadratically for attention without fused kernels), so 8k-token examples can triple memory versus 2k.
- When do you need multi-node?: Full fine-tuning of large models, or any job whose state exceeds a single node's GPUs.

**Mistakes to avoid:**
- Quoting a GPU without stating precision, method and sequence length.
- Ignoring compute speed; "fits" and "finishes this week" are different questions.

### Q. Colab versus cloud GPUs: how do you run fine-tuning experiments cheaply?

**Short answer (45 seconds):** Use Colab-class notebooks for learning and for small models and subsets: the free tier gives a 16 GB T4-class GPU with session limits, and paid tiers give larger GPUs when available. Use cloud GPUs for anything you need to finish reliably: on-demand for short critical runs, spot or preemptible instances for long runs with checkpoints every few hundred steps. The cheap workflow is to debug on a small data slice locally or in Colab, then launch the full run from a config file on a spot instance that resumes from the latest checkpoint automatically.

**Deeper explanation:** Colab's limits are the session (it can disconnect, and long or idle sessions end), ephemeral disk, and GPU availability. Treat it as a scratchpad: push checkpoints to Drive or object storage on every save, keep the notebook thin, and import training code from a repo so it runs elsewhere unchanged. Unsloth's notebooks are a good template for 8B QLoRA on the free tier.

Cloud choices: hyperscalers (AWS, GCP, Azure) for VPC integration and compliance; GPU marketplaces (RunPod, Lambda, Vast.ai) for cheaper hourly rates with less integration. Spot pricing cuts cost substantially but the job can be killed at any moment, so checkpointing and resume are not optional.

```bash
aws s3 sync s3://ml-runs/support-v3/out ./out      # pull the latest checkpoint first
python train.py --config configs/support-v3.yml --resume latest
```

Cost control habits: run the smallest model that could plausibly work first, cap `max_steps` for sweeps, use a 10 percent data subset for hyperparameter search, and shut the instance down from the training script's final step instead of hoping someone remembers.

**Follow-ups they will ask:**
- How do you estimate run time before paying?: Time 20 steps on the target hardware, multiply by total steps, add eval and save overhead.
- What breaks when moving from Colab to cloud?: Library versions, paths, and the CUDA driver; a pinned container image fixes most of it.
- Where do you store checkpoints?: Object storage with versioned prefixes; never only on the instance disk.

**Mistakes to avoid:**
- Running a 12-hour job on a free notebook and losing it at hour 11.
- Leaving an 80 GB GPU running overnight after the job finished.

### Q. How do you checkpoint and resume a run, and how do you track experiments so results are reproducible?

**Short answer (45 seconds):** Save a checkpoint every few hundred steps with the adapter weights, optimizer and scheduler state and the RNG state, keep only the last two or three, sync them to object storage, and start every run with resume enabled so a preempted job continues from the latest step. For tracking, log every run to Weights & Biases or MLflow with the resolved config, dataset version hash, git commit, loss curves, learning rate, gradient norm, eval metrics and the final artifact, so any two runs can be compared a month later and any model can be rebuilt.

**Deeper explanation:** In the Trainer family this is a handful of arguments:

```python
cfg = SFTConfig(
    output_dir="out/support-v3",
    save_strategy="steps", save_steps=200, save_total_limit=3,
    eval_strategy="steps", eval_steps=200,
    load_best_model_at_end=True, metric_for_best_model="eval_loss",
    report_to="wandb", run_name="support-v3-r16-lr2e-4-ds-v7",
    seed=42,
)
trainer.train(resume_from_checkpoint=True)   # picks the latest checkpoint in output_dir
```

A LoRA checkpoint is small (adapter weights plus optimizer state for the adapter), so saving often is cheap; a full fine-tuning checkpoint is tens of gigabytes per save and needs sharded saving and a fast disk. With spot instances, a wrapper script syncs `output_dir` to S3 or GCS after each save and before exit.

Tracking is what makes fine-tuning engineering rather than alchemy. Name runs by what changed, log the dataset manifest hash as a config field, and store the eval results JSON as an artifact next to the adapter. MLflow adds a model registry with aliases, which pairs nicely with a deployment gateway that resolves "support-triage@production" to a specific artifact.

**Follow-ups they will ask:**
- Why log gradient norm?: Spikes precede divergence; a growing norm with flat loss means the learning rate is too high or the data has outliers.
- How do you reproduce a run exactly?: Same container image, pinned versions, same seed, same dataset version, same config; small numerical differences remain on GPUs.
- What is in a good run name?: Base model, method, rank, learning rate, dataset version; the tracker holds the rest.

**Mistakes to avoid:**
- Saving only the final model, so a crash at 90 percent means starting over.
- Running sweeps without the dataset hash logged, so nobody knows which data produced the best run.

### Practice
- Run the same 1,000-example QLoRA job with plain TRL and with Unsloth on one GPU; record wall-clock, peak memory and the eval score, and export a GGUF from the Unsloth run.
- Convert that job into an Axolotl YAML, commit it with the dataset manifest, and reproduce the eval score from a fresh container.
- Launch a run on a spot instance with saves every 100 steps and object-store sync, kill the instance halfway, and confirm the resumed run reaches the same final loss within noise.
- Say it out loud: given "8B model, 4k-token examples, one 24 GB GPU", talk through precision, method, batch size and the memory estimate in 90 seconds.

## Evaluating & Shipping a Fine-tuned Model

> This is where senior candidates separate from mid-level ones. Anyone can get a loss curve to go down; the interviewer wants to know how you prove the model is better, how you prove it is not worse elsewhere, how it reaches production without a big-bang cutover, and what you watch after launch. A weak answer is "validation loss improved and we deployed it"; a strong one has a held-out set built before training, a judge calibrated against humans, a regression suite, a canary, and a rollback that takes one config change.

### Concepts you must understand
- The eval set is built before training from the production distribution, stratified by intent and difficulty, and never trained on; refresh it from new traffic and re-decontaminate.
- Use deterministic task metrics wherever the output is checkable (exact match, F1, schema validity, tool-call argument accuracy, pass@k) and LLM-as-judge only for open-ended quality, calibrated against human labels.
- Regression against the base model is mandatory: general capability samples, safety and refusal cases, and the behaviours you did not intend to change.
- A/B testing in production answers the business question the offline eval cannot: route a slice of traffic by stable user hash, compare task success and guardrail metrics, and size the test before you start.
- vLLM serves merged weights or base-plus-adapters behind an OpenAI-compatible API with continuous batching and PagedAttention; quantised serving (AWQ, GPTQ, FP8) trades a little accuracy for throughput.
- A model version is an immutable bundle: weights or adapter, tokenizer and chat template, generation config, dataset version, eval results and card; deployment resolves an alias to a version so rollback is flipping the alias.
- Drift after deployment shows up in inputs (topic mix, length, language), outputs (schema failures, refusal rate, length, judge scores on samples) and user signals; monitor all three and re-run the offline eval on a schedule.
- A model card records intended use, data, training config, eval results, known failure modes and license; it is how the next engineer avoids misusing the model.

### Q. How do you build an evaluation set for a fine-tune, and when do you build it?

**Short answer (45 seconds):** Before any training, from the same distribution the model will see in production. I sample real or realistic inputs stratified across intents, lengths, languages and difficulty, including adversarial and off-topic cases, write or review reference outputs or rubrics for each, decontaminate the training data against it, and freeze it. Hundreds of cases is the working minimum for a product task; dozens only reveal catastrophic failures. The same set scores the prompted baseline, every training run, and the shipped model.

**Deeper explanation:** Three layers are useful: a golden set with reference answers for deterministic scoring, a judged set with rubrics for open-ended quality, and an adversarial set (prompt injection attempts, malformed inputs, requests outside scope) where the expected behaviour is a refusal or a safe default. Each case carries metadata: slice, source, expected output or rubric, and a difficulty tag, so you can report per-slice scores and not just an average that hides a broken slice.

```json
{"id": "triage-0412", "slice": "billing/refund", "difficulty": "hard",
 "input": {"messages": [{"role": "user", "content": "Charged twice for order 1182, need refund today"}]},
 "expected": {"intent": "duplicate_charge", "order_id": "1182", "escalate": true},
 "checks": ["json_schema", "exact:intent", "exact:order_id"]}
```

Keep the eval set out of every training path: separate storage, a decontamination step that checks n-gram overlap against training rows, and a rule that anyone who adds training data runs that check. Refresh it periodically from new traffic because production drifts, and version it like the dataset so a score is always "0.87 on eval v3", never just "0.87".

**Follow-ups they will ask:**
- How many examples?: Enough for the confidence interval to be narrower than the difference you care about; bootstrap the interval, and expect a few hundred cases to separate small differences.
- Who writes the references?: Domain owners, with a second reviewer for a sample; engineers write the checks.
- What if there is no single correct answer?: Use rubrics and a judge, and keep a few pairwise comparisons against the baseline.

**Mistakes to avoid:**
- Building the eval set from the training data after the fact.
- Reporting one aggregate number with no per-slice breakdown.

### Q. Task metrics versus LLM-as-judge: when do you use each, and how do you make a judge trustworthy?

**Short answer (45 seconds):** If the output is checkable, check it with code: schema validity, exact match on fields, F1 for extraction, result-set equality for SQL, tests for code, tool-call name and argument accuracy. These are cheap, deterministic and hard to game. Use a judge model only where quality is a reading, not a fact: tone, helpfulness, faithfulness to context, summary quality. Make the judge trustworthy with a rubric, reference material, order-swapped pairwise comparisons, a stronger model than the one being judged, and a measured agreement rate against human labels on a sample.

**Deeper explanation:** For fine-tuned product models, most of the value sits in checkable metrics because the fine-tune usually targets structure. A typical scorer runs each case and records several booleans:

```python
import json
from jsonschema import validate, ValidationError

def score(case, output):
    r = {"valid_json": False, "schema_ok": False, "intent_match": False}
    try:
        obj = json.loads(output)
        r["valid_json"] = True
        validate(obj, TICKET_SCHEMA)
        r["schema_ok"] = True
        r["intent_match"] = obj.get("intent") == case["expected"]["intent"]
    except (json.JSONDecodeError, ValidationError):
        pass
    return r
```

For judged criteria, score absolute rubrics (1 to 5 with anchors) for tracking over time, and use pairwise against the previous model for release decisions, since pairwise judgements are more reliable than absolute ones. Run both orderings and treat disagreement as a tie. Report the judge's agreement with humans (for example on 200 double-labelled cases) alongside every judged metric, and re-check it whenever you change the judge model or prompt. Classic text metrics such as BLEU and ROUGE are weak proxies for open-ended generation and are best left to summarisation sanity checks.

**Follow-ups they will ask:**
- Can the judge be the same family as the model?: Avoid it; self-preference bias inflates scores, so use a different, stronger model.
- How do you keep judge costs down?: Judge a sample, cache verdicts by output hash, and reserve the judge for criteria code cannot check.
- What about latency and cost as metrics?: Always report p50 and p95 latency and cost per thousand requests next to quality; a quality win at double latency may be a loss.

**Mistakes to avoid:**
- Judging what a validator could check.
- Reporting a judge score with no calibration against humans.

### Q. How do you check that the fine-tune did not make the model worse at things you did not train on?

**Short answer (45 seconds):** With a regression suite run on both the base and the fine-tuned model before every release. It has three parts: a general-capability sample (a few public benchmark subsets via lm-evaluation-harness such as IFEval for instruction following or GSM8K for reasoning, plus your own general prompts), a safety and refusal set with expected behaviours, and the neighbouring behaviours you did not mean to change, such as other languages or other tools. A drop beyond an agreed tolerance blocks the release regardless of how good the task metric looks.

**Deeper explanation:** Catastrophic forgetting is quiet; nothing in the training loss tells you the model stopped handling Hindi or started complying with jailbreaks. So you make the comparison explicit and automated:

```bash
lm_eval --model hf --model_args pretrained=meta-llama/Llama-3.1-8B-Instruct \
  --tasks ifeval,gsm8k --batch_size 8 --output_path evals/base
lm_eval --model hf --model_args pretrained=models/support-v3-merged \
  --tasks ifeval,gsm8k --batch_size 8 --output_path evals/support-v3
```

Public benchmarks are a coarse signal (and you must decontaminate against them); the finer signal is your own general set, 50 to 200 prompts across tasks your users also send to this model, scored pairwise against the base by a judge. The safety set deserves exact expectations: prompts that must be refused, prompts that must not be over-refused, and injection attempts inside the retrieved context. Tolerances are set in advance (for example, at most a small absolute drop on general tasks and zero new safety failures) so the release decision is not negotiated after seeing the numbers.

When a regression appears, the usual fixes are fewer epochs, a lower learning rate, a smaller rank, mixing general data into training, or weight-space averaging with the base.

**Follow-ups they will ask:**
- Do you run the full regression on every experiment?: A light version (fast subsets) on every run, the full suite on release candidates.
- What if the base model itself fails some safety cases?: Record it; your bar is "no worse than base", and preferably fix those with training data.
- How do you catch regressions in tool use?: A tool-call eval set with expected function names and arguments, scored exactly.

**Mistakes to avoid:**
- Presenting only the task metric and calling the release a success.
- Setting the tolerance after seeing the results.

### Q. How do you A/B test a new model version in production?

**Short answer (45 seconds):** Route a slice of traffic to the new version by a stable key such as a hash of the user or conversation id so one user never flips between models, log the model version with every response, and compare a primary task metric (resolution without escalation, accepted drafts, tool-call success) plus guardrail metrics (p95 latency, error and schema-failure rate, thumbs-down rate, cost). Decide the sample size and duration before starting, run for full business cycles, and promote or roll back based on the pre-registered criteria.

**Deeper explanation:** Offline evals tell you the model is better on your cases; the A/B tells you users agree, which is a different claim. The mechanics live in your gateway: a router resolves the request to a model alias (`support-triage@candidate` or `@production`), the assignment is deterministic from the hash, and the version is written into the trace so dashboards can slice by it.

```text
request -> gateway: variant = hash(user_id) mod 100 < 10 ? "candidate" : "production"
        -> vLLM (merged model or adapter name) -> response + {model_version, latency, tokens}
        -> event log -> metrics by variant: success rate, p95, schema failures, feedback
```

Pitfalls specific to LLM features: the primary metric is often delayed or noisy (did the ticket get resolved?), so pick a leading indicator you can read in days; variants differ in verbosity, which moves cost and latency as well as satisfaction; and novelty effects fade, so avoid declaring victory on day one. For high-risk flows use a canary first (1 percent, internal users) and a shadow mode where the candidate generates but does not serve, which lets you compare outputs on live traffic with zero user exposure.

**Follow-ups they will ask:**
- How do you size the test?: From the baseline rate and the smallest improvement you care about; a standard power calculation gives samples per arm.
- Can you A/B two adapters on one GPU?: Yes, with multi-LoRA serving the variants share the base and the router picks the adapter name.
- What if the candidate is better on quality but slower?: Define the trade-off before the test; latency is a guardrail with a threshold, not an afterthought.

**Mistakes to avoid:**
- Routing per request instead of per user, so conversations mix models.
- Reading results until they look good and then stopping.

### Q. How do you serve a fine-tuned model with vLLM, and when do you serve merged weights versus adapters?

**Short answer (45 seconds):** vLLM loads the model once, batches concurrent requests continuously, manages the KV cache with PagedAttention, and exposes an OpenAI-compatible API, so clients that already speak the chat completions format need only a base URL change. For one high-volume task I merge the adapter, optionally quantise (AWQ or FP8), and serve the single model. When several adapters share a base or I want cheap hot-swapping and rollback, I serve the base with `--enable-lora` and pick the adapter per request by name.

**Deeper explanation:** A single-task deployment and a client look like this:

```bash
vllm serve models/support-v3-merged \
  --dtype bfloat16 --max-model-len 4096 \
  --gpu-memory-utilization 0.90 --served-model-name support-triage
```

```python
from openai import OpenAI
client = OpenAI(base_url="http://vllm:8000/v1", api_key="unused")
resp = client.chat.completions.create(
    model="support-triage",
    messages=[{"role": "user", "content": "Charged twice for order 1182"}],
    temperature=0.0, max_tokens=200,
)
```

Operational details that matter: the chat template is read from the model's tokenizer config, so ship the tokenizer with the merged weights or the server will format prompts differently from training; `--max-model-len` bounds KV cache per request and therefore concurrency; `--gpu-memory-utilization` reserves the KV cache pool; and prefix caching helps when every request shares a long system prompt. Quantised serving (AWQ 4-bit, or FP8 on recent GPUs) raises throughput and lowers memory at a small accuracy cost that you confirm by re-running the eval set on the quantised artifact, not the bf16 one.

For adapter serving, the flags from the PEFT section apply (`--enable-lora`, `--lora-modules`, `--max-lora-rank`), and the request's `model` field selects the adapter. Latency overhead is small; the win is operational.

**Follow-ups they will ask:**
- How do you get structured output reliably?: vLLM supports guided decoding against a JSON schema; combine it with the fine-tune rather than relying on either alone.
- What does continuous batching change?: New requests join running batches between decode steps, so throughput stays high without waiting for a batch to fill.
- How do you scale beyond one GPU?: Tensor parallelism across GPUs in one node for large models, and replicas behind a load balancer for throughput.

**Mistakes to avoid:**
- Serving the merged weights with a different tokenizer or template than training.
- Evaluating the bf16 model and shipping the quantised one unverified.

### Q. How do you version models and roll back safely?

**Short answer (45 seconds):** Every release is an immutable bundle with a version id: weights or adapter, tokenizer and chat template, generation defaults, the dataset version, the training config, the eval report and the model card, stored in a registry or versioned object storage. Deployment never references a file path; it references an alias such as `support-triage@production` that the gateway resolves to a version. Promotion is moving the alias forward after canary and A/B; rollback is moving it back, which takes seconds because the previous version is still warm or quick to load.

**Deeper explanation:** The registry can be MLflow's model registry with aliases, private Hugging Face Hub repos with revisions, or an S3 or GCS prefix per version with a manifest; what matters is immutability and an alias layer separate from storage.

```text
registry/support-triage/
  v12/  adapter/  tokenizer/  generation_config.json  eval.json  MODEL_CARD.md  manifest.json
  v13/  ...
aliases: production -> v12, candidate -> v13
gateway: model "support-triage" -> aliases[production] -> vLLM deployment or adapter name
```

With multi-LoRA serving, rollback is trivial: both adapters are loaded and the alias points at one name. With merged models, keep the previous server running during the canary window (blue/green) so rollback is a routing change, not a cold load that can take minutes for an 8B model. Put the version in every trace so an incident maps to the exact model, prompt version and dataset.

Also version what surrounds the model: system prompt, retrieval configuration and guardrails change behaviour as much as weights, and a "model regression" is often a prompt change; the whole bundle is the unit of release.

**Follow-ups they will ask:**
- What triggers an automatic rollback?: Guardrail breaches in the first minutes: schema failure rate, error rate, p95 latency, or a safety classifier alert above thresholds.
- How long do you keep old versions?: At least the last few that were in production, plus anything referenced by an open incident or audit.
- How do you handle a base model upgrade?: It is a new lineage: retrain the adapter, re-run everything, and keep the old lineage until the new one has passed A/B.

**Mistakes to avoid:**
- Deploying by file path with "latest" in the name.
- Rolling back the weights but not the prompt or retrieval change that shipped with them.

### Q. How do you monitor a fine-tuned model after deployment for drift?

**Short answer (45 seconds):** Watch three things continuously: inputs, outputs and people. Inputs: the mix of intents, lengths, languages and retrieval hit rates compared with the training distribution. Outputs: schema and validator failure rate, refusal rate, response length, tool-call error rate, and a judge score on a daily sample of real traffic. People: thumbs-down rate, edit rate, escalation rate. Alert on thresholds, re-run the offline eval set on a schedule against live samples, and define in advance what triggers data collection and a retrain.

**Deeper explanation:** Fine-tuned models drift because the world does, not because weights change: new products, new phrasing, new attack patterns, a changed upstream retrieval index. Input drift is measured by comparing recent traffic to the training manifest: classify intents with a cheap model and compare proportions, or embed samples and compare distributions. Output drift is cheaper and more direct; a rising schema failure rate or a falling judge score on sampled traffic is the first sign the model is off-distribution.

```text
Daily job:
  sample 200 production requests (stratified by intent)
  -> run validators, judge with the release rubric, compare to the release baseline
  -> store scores by model_version and day
Alerts:
  schema_failure_rate > 2x release baseline for 1h
  judge_faithfulness_mean below threshold for 2 days
  intent "unknown" share above threshold (a new topic appearing)
```

Tracing is the foundation: every request logs prompt version, model version, retrieved chunk ids, output, latency, tokens and feedback, in a tool such as Langfuse, Arize Phoenix or your own OpenTelemetry pipeline. The failures you sample from those traces become next quarter's training data and eval cases, which closes the loop: monitoring is how the dataset grows.

**Follow-ups they will ask:**
- How is this different from classic ML monitoring?: Same ideas (input and output drift, performance proxies), but labels are delayed or absent, so judged samples and validators stand in for ground truth.
- When do you retrain?: On a trigger (a metric below threshold or a new slice above a share) or on a cadence, with the same eval gate as the original release.
- What about privacy in monitoring?: Sampled traces are customer data; redact, restrict access, and set retention.

**Mistakes to avoid:**
- Monitoring only latency and errors as if the model were a stateless API.
- Having no path from a bad production sample into the eval set and training data.

### Q. What goes into a model card, and why bother writing one?

**Short answer (45 seconds):** A model card is the README for a trained model: what it is for and not for, the base model and license, the data it was trained on (sources, size, filtering, privacy handling, version), the training recipe (method, rank, hyperparameters, compute), evaluation results with the eval set version and the regression against the base, known failure modes and biases, and how to serve it (template, generation defaults). You write it because the next engineer, the security reviewer and the auditor will otherwise guess, and because writing it forces you to check that every claim has a number behind it.

**Deeper explanation:** The format comes from the "Model Cards for Model Reporting" idea and is what the Hugging Face Hub renders from a README with YAML metadata. Internally it does not need to be pretty, it needs to be complete and versioned with the model.

```text
MODEL_CARD.md (support-triage v12)
  Intended use:    classify and structure inbound support emails into tickets (English, Hindi)
  Out of scope:    free-form customer replies; legal or medical content
  Base model:      [name and version], license: [license]
  Data:            dataset v7 (4,812 rows; 60% real redacted tickets, 40% synthetic; judge-filtered; PII scrubbed)
  Training:        QLoRA r=16 all-linear, lr 2e-4, 2 epochs, 1x A10G, ~1.5 h
  Eval:            eval v3: schema validity, intent accuracy, escalation F1 (+ CIs); regression vs base: IFEval, safety set
  Known failures:  mixed-language emails; multi-order threads
  Serving:         chat template from tokenizer; temperature 0; max_tokens 200; vLLM flags
  Owners, date, changelog from v11
```

The card also carries the license obligations downstream. If the base is Llama, the community license has attribution and use requirements; if you distilled from an API, the terms you relied on belong here too. For regulated industries the card is the artifact compliance asks for, and for everyone else it is the document that stops a model built for triage being quietly reused to draft customer-facing replies.

**Follow-ups they will ask:**
- Who reads it?: Engineers integrating the model, reviewers approving the release, and anyone debugging an incident months later.
- How do you keep it honest?: Generate the eval and training sections from the run artifacts, not by hand.
- Does a card help with A/B decisions?: Yes, the eval section is the offline evidence that justifies the test.

**Mistakes to avoid:**
- Writing aspirations ("handles all support emails") instead of measured scope.
- Omitting the dataset version and the eval set version, which makes the numbers unreproducible.

### Practice
- Build a 300-case eval set with slices and checks for one task, score the base model and a fine-tune, and produce a per-slice report with bootstrap confidence intervals.
- Serve the fine-tune with vLLM, then quantise it (AWQ) and re-run the same eval; record the quality delta, throughput and memory.
- Set up a daily sampling job that pulls 100 production-like requests, runs validators and a judge, and writes scores by model version; wire one alert threshold.
- Say it out loud: walk an interviewer from "training finished" to "live for 100 percent of users" in two minutes, naming every gate and what would make you stop.

## Small Language Models & Distillation

> Interviewers ask about small models to test judgement about cost and architecture, not just training skill. The strong answer treats a 1B to 8B model as an engineering component with a clear place: narrow, high-volume, latency- or privacy-bound tasks, trained from a larger model's behaviour and measured against the API it replaces. A weak answer either dismisses small models as toys or claims a 3B model can do everything a frontier model does.

### Concepts you must understand
- Small language models (roughly 0.5B to 10B parameters; Llama 3.2 1B and 3B, the small Qwen sizes, Phi, the small Gemma sizes, SmolLM, Mistral 7B) run on one modest GPU, a CPU, or a phone, which changes cost, latency, privacy and availability.
- Cost scales with parameters: fewer FLOPs per token and less memory means more tokens per second per dollar; the API-vs-self-host break-even depends on volume, utilisation and ops cost.
- Distillation trains a small student on a large teacher's behaviour: hard-label (SFT on teacher outputs, works through any API), soft-label (match the teacher's token distributions, needs white-box access and a shared tokenizer), and rationale distillation (the student learns the teacher's reasoning traces).
- A task-specific small model can match or beat a general large model on a narrow, well-specified task because its whole capacity is spent on that distribution; it loses on open-ended reasoning and the long tail.
- Cascades and routers combine both: the small model handles the common cases and escalates on low confidence, validation failure or detected out-of-scope input.
- Ollama runs GGUF models locally with a Modelfile (base, system prompt, parameters, adapter) and an OpenAI-compatible endpoint, which makes it the development and on-prem counterpart to vLLM in production.
- Quantisation to 4-bit GGUF (llama.cpp) is what makes CPU and on-device inference practical; always re-run the eval on the quantised artifact.
- Privacy and sovereignty are first-class reasons: data never leaves the device or VPC, no third-party retention, and no dependence on a vendor's model lifecycle.

### Q. Why would you use a small language model when frontier APIs exist?

**Short answer (45 seconds):** Four reasons: cost at volume, latency, privacy, and control. A 1B to 8B model fine-tuned for a narrow task can run on one modest GPU or even a CPU, respond in a fraction of the time, keep data inside the VPC or on the device, and never gets deprecated or rate-limited by a vendor. The trade is capability breadth: the small model does one thing well, so it belongs where the task is well-defined and high-volume, and the frontier model belongs where reasoning and the long tail matter.

**Deeper explanation:** Latency has two parts, time to first token (prompt processing) and tokens per second (memory bandwidth and parameter count). A small model wins both: fewer weights to read per token and a shorter prompt, since the instructions are in the weights. For a classification, extraction or routing step that runs on every request, users and the p95 both feel the difference.

Privacy often decides it in regulated settings: healthcare, banking, government, or data-residency requirements in India and the UAE, where sending customer text to a foreign API is a compliance question before an engineering one. On-device (keyboards, assistants, offline field apps) is the extreme case where no network call is acceptable.

Control matters more than people expect: a hosted model can change with a silent update, throttle a launch with a rate limit, or force a migration by deprecation. A model you own behaves identically until you change it.

```text
Use a small model when:              Use the frontier API when:
  task is narrow and checkable         task is open-ended or needs deep reasoning
  volume is high, latency is tight     volume is low or spiky
  data must stay local                 data can leave and you want zero ops
  you can build an eval set            the task is still being defined
```

**Follow-ups they will ask:**
- Does a small model need fine-tuning?: For narrow tasks, usually yes; prompted small models are noticeably weaker than prompted large ones, and the fine-tune closes that gap.
- What about quality risk?: Cascade: validate the small model's output and escalate failures to a large model.
- Where do SLMs show up besides the main task?: Routers, guardrail classifiers, query rewriting, speculative decoding draft models, and embeddings.

**Mistakes to avoid:**
- Claiming small models are "almost as good" in general; they are as good on the task you trained and measured.
- Ignoring the ops cost of owning a model in the comparison.

### Q. Explain knowledge distillation. How would you distil a frontier model into a 3B model for one task?

**Short answer (45 seconds):** Distillation trains a small student to reproduce a large teacher's behaviour. For a product task the practical recipe is: collect a large, representative set of inputs, run the teacher with your best prompt to produce outputs, filter them with validators and a judge, and fine-tune the student with SFT on the surviving pairs; then evaluate the student against the teacher on a held-out set and keep the teacher as a fallback for failures. The student inherits the teacher's behaviour on that input distribution, which is exactly what you wanted, at a fraction of the cost.

**Deeper explanation:** The pipeline mirrors the synthetic data section: prompts covering every slice, the teacher at low temperature with the production system prompt, strict filtering (correctness checks where possible, judge scoring otherwise), deduplication, and a split. Volume matters more than in style tuning because you are transferring a capability: thousands to tens of thousands of examples is typical, and the learning-curve test tells you when to stop.

```text
inputs (real or synthetic, all slices)
  -> teacher (frontier model, production prompt, temperature 0.0 to 0.3)
  -> filters (schema, validators, judge, dedup, decontaminate)
  -> student SFT (3B instruct, LoRA or full, 2 to 3 epochs)
  -> eval: student vs teacher on held-out; agreement rate, per slice
  -> deploy student + fallback to teacher on validation failure
```

Variants: including the teacher's reasoning before the answer (rationale distillation) helps on harder cases if serving can afford the extra tokens; recent reasoning models were distilled into small Qwen and Llama students by SFT on hundreds of thousands of teacher reasoning traces. With white-box access to a teacher sharing the tokenizer, you can also match token distributions (soft labels), which transfers more per example.

Legal check first: some API providers restrict using outputs to train competing models; open-weight teachers avoid the question.

**Follow-ups they will ask:**
- Can the student beat the teacher?: On the narrow task, sometimes, because filtering removed teacher errors and the student is consistent; never in general.
- Why not distil into a 1B?: Try it; if the eval holds, take the savings, but capacity limits show up first on hard and long-tail slices.
- How do you keep the student fresh?: Periodically re-run the teacher on new traffic samples and retrain; monitoring tells you when.

**Mistakes to avoid:**
- Distilling from an unfiltered teacher so the student learns its mistakes faithfully.
- Deploying the student with no escalation path.

### Q. What is the difference between hard-label and soft-label distillation, and when does each apply?

**Short answer (45 seconds):** Hard-label distillation trains the student on the teacher's generated text with the normal cross-entropy loss, as if the teacher's outputs were human labels; it works through any API and is what most teams mean by distillation. Soft-label distillation trains the student to match the teacher's probability distribution over the vocabulary at each position, usually with a KL loss and a softening temperature; it transfers more information per token but needs the teacher's logits and a shared tokenizer, so it is mostly used between open models of the same family.

**Deeper explanation:** The classic formulation uses a softened softmax `p_i = exp(z_i / T) / sum_j exp(z_j / T)` for both teacher and student, and the loss `L = alpha * CE(student, hard labels) + (1 - alpha) * T^2 * KL(p_teacher || p_student)`. A temperature T above 1 exposes the teacher's "dark knowledge": which wrong tokens it considered plausible. Illustrative: if the teacher puts 0.70 on "refund", 0.25 on "chargeback" and 0.05 on everything else, the student learns that chargeback is a near-synonym here, which a hard label ("refund") never tells it.

```text
Hard-label:  teacher text   -> student SFT (cross-entropy on tokens)        any API, any tokenizer
Soft-label:  teacher logits -> student matches distribution (KL, temp T)    white-box, same tokenizer
Rationale:   teacher reasoning + answer -> student SFT                      any API, more tokens at inference
```

Practical constraints: full-vocabulary logits for every token are huge (a 128k vocabulary times sequence length), so implementations run the teacher online during training, with both models in memory, or store top-k logits offline. Different tokenizers break position alignment, which is why cross-family soft distillation is rare. For a product team, hard-label distillation with aggressive filtering captures most of the benefit with none of these constraints.

**Follow-ups they will ask:**
- Does soft-label distillation need labelled data?: No, only inputs; the teacher provides the targets, and the hard-label term is optional.
- Should you filter teacher outputs before distilling?: Yes, filtering by validators is standard and often makes the student more consistent than the teacher.
- Is TRL involved?: SFTTrainer for hard labels; soft-label distillation needs a custom loss or a specialised trainer.

**Mistakes to avoid:**
- Claiming soft-label distillation across different tokenizers "just works".
- Forgetting the T squared factor and wondering why the KD term's gradients are tiny at high temperature.

### Q. How do you use Ollama for local development, and what is a Modelfile?

**Short answer (45 seconds):** Ollama is a local runner built on llama.cpp: `ollama pull` downloads a quantised GGUF model, `ollama run` chats with it, and it exposes a local HTTP API, including an OpenAI-compatible endpoint, so your application code can point at `http://localhost:11434/v1` during development and at vLLM in production with no code change. A Modelfile is the Dockerfile equivalent: it names the base model, sets a system prompt and generation parameters, and can attach an adapter or point at your own GGUF, then `ollama create` packages it as a named model the team can share.

**Deeper explanation:** A development loop for a fine-tuned model looks like this:

```text
FROM ./support-v3-q4_k_m.gguf
SYSTEM "You convert support emails into tickets. Output JSON only."
PARAMETER temperature 0
PARAMETER num_ctx 4096
```

```bash
ollama create support-triage -f Modelfile
ollama run support-triage "Charged twice for order 1182, need refund today"
curl http://localhost:11434/v1/chat/completions \
  -d '{"model": "support-triage", "messages": [{"role": "user", "content": "hi"}]}'
```

The GGUF comes from Unsloth's export or from llama.cpp's conversion and quantisation scripts after merging the adapter. Because the chat template is embedded in the GGUF metadata, the model formats prompts the way it was trained, which is one less thing to get wrong locally. The native API (`/api/chat`, `/api/generate`) exposes more Ollama-specific options; the OpenAI-compatible path is what keeps your application code portable.

Where Ollama fits: developer laptops, CI jobs that need a real model, demos, small on-prem deployments and edge boxes. Where it does not: high-concurrency production serving, where vLLM's continuous batching and PagedAttention are built for throughput. Keep the same eval harness pointed at both so a local result predicts the production one.

**Follow-ups they will ask:**
- Can Ollama load a LoRA adapter directly?: Modelfiles support an `ADAPTER` directive for compatible adapters; merging into a GGUF is the more predictable path.
- How do you make the same code hit Ollama locally and vLLM in production?: Both speak the OpenAI chat format; configure base URL and model name per environment.
- Does it use the GPU?: Yes when one is available (including Apple silicon via Metal), otherwise CPU, which is fine for small quantised models.

**Mistakes to avoid:**
- Benchmarking production latency on Ollama; it is a development tool, not a serving engine.
- Shipping a Modelfile system prompt that differs from the one used in training or in vLLM.

### Q. When does a fine-tuned 3B model beat an API call? Walk me through the break-even.

**Short answer (45 seconds):** When the task is narrow enough that the 3B model matches the API on your eval, the volume is high enough that a dedicated GPU is cheaper than per-token pricing, and latency or privacy already push you toward self-hosting. The arithmetic is tokens per month times API price versus GPU hours times hourly price, plus the engineering and on-call cost you now carry; I would run it with real quotes and real traffic, and I would include the fallback cost for cases the small model escalates.

**Deeper explanation:** Illustrative arithmetic only; plug in current prices from your vendors:

```text
Volume:   5M requests/month x (800 input + 200 output tokens) = 5B tokens/month
API:      at an illustrative $1 per 1M tokens blended        -> $5,000/month
Self:     one 24 GB GPU at an illustrative $1.50/hour, 730 h  -> $1,100/month
          (if one GPU sustains the load at acceptable p95; otherwise add GPUs)
Hidden:   engineering time to build and maintain, monitoring, on-call, periodic retraining
Fallback: 10% escalation to the API at the same price         -> +$500/month
```

With these illustrative numbers the small model wins on cost at this volume, and the gap grows with volume because the GPU cost is flat while API cost is linear. Divide the volume by ten and the GPU is idle most of the day while the API bill is a few hundred dollars; the self-hosted option loses unless latency or privacy force it. Utilisation is the hidden variable: a GPU serving steady traffic is cheap per request, a GPU waiting for spiky traffic is expensive, and autoscaling GPU workers has cold-start costs of minutes.

The non-cost reasons often decide it anyway: data residency rules that forbid the API, latency budgets the API cannot meet, or product requirements for offline or on-device inference. When those apply, the break-even question becomes "which small model", not "whether".

**Follow-ups they will ask:**
- How do you measure "matches the API"?: Same eval set and judge, per slice; agree a tolerance and track escalations as part of the quality number.
- What about engineering cost?: Estimate it honestly; a team's first self-hosted model is a project, the third is a config change.
- Can batch workloads change the answer?: Yes, offline batch jobs tolerate latency, so spot GPUs at night can process them very cheaply.

**Mistakes to avoid:**
- Comparing API price to GPU price without utilisation and ops cost.
- Forgetting that the escalation traffic still costs API money.

### Q. Task-specific small model or general model: how do you decide, and how do you handle the long tail?

**Short answer (45 seconds):** Classify the work. Steps that are narrow, frequent and checkable (intent routing, extraction to a schema, query rewriting, guardrail classification, templated replies) are candidates for a task-specific small model. Steps that are open-ended, rare or need reasoning across unfamiliar inputs stay on a general model. Then handle the long tail with a cascade: the small model answers, a validator or confidence signal accepts or escalates to the general model, and escalations are logged as the next training set.

**Deeper explanation:** Most production LLM features are pipelines, and each stage has its own profile. A support assistant might classify intent (small model, every request), retrieve context (embeddings), draft an answer (general model today, maybe a fine-tuned 8B later), and check policy compliance (small classifier). Deciding per stage spends the expensive model only where it earns its cost.

```text
request -> SLM (fine-tuned 3B) -> validator (schema, confidence, out-of-distribution check)
              |-- pass -> respond                       (most traffic, illustrative ~90%)
              |-- fail -> general model -> respond, log as a hard case
hard cases -> review -> added to training + eval sets -> next SLM version
```

Confidence signals are imperfect: token log-probabilities on a classification label are a usable proxy, an out-of-distribution check (embedding distance from training centroids) catches new topics, and validators catch structural failures. Tune the escalation threshold on the eval set for the quality target at the lowest escalation rate. Over time, as hard cases enter the training set, coverage grows and escalation shrinks, which is the practical path to replacing most of an API bill without a risky cutover.

**Follow-ups they will ask:**
- Does a general model with a long prompt not do all of this already?: Yes, at higher cost and latency per request; the cascade is an optimisation you adopt once volume justifies it.
- How do you avoid the small model silently failing in a new way?: Monitoring from the shipping section: validator rates, judged samples, and the escalation rate as a drift signal.
- What if the general model also fails?: Design the product for it: ask a clarifying question, hand to a human, or decline, and record the case.

**Mistakes to avoid:**
- Replacing the whole pipeline with one small model in a single step.
- Treating escalation rate as a cost only; it is also your best drift and data-collection signal.

### Q. How do you quantise and run a fine-tuned model on CPU or on-device, and how do you check you did not break it?

**Short answer (45 seconds):** Merge the adapter into the base in 16-bit, convert to GGUF with llama.cpp's conversion script, quantise to a 4-bit variant such as Q4_K_M, and run it with llama.cpp, Ollama or a mobile runtime. Then re-run the full eval set on the quantised artifact and compare with the bf16 model: a small drop is normal, a large drop means the quantisation level is too aggressive for this task, so you step up to a higher-precision variant. Never ship a quantised model on the strength of the unquantised eval.

**Deeper explanation:** The conversion path from an Unsloth or PEFT merge:

```bash
python convert_hf_to_gguf.py models/support-v3-merged --outfile support-v3-f16.gguf --outtype f16
llama-quantize support-v3-f16.gguf support-v3-q4_k_m.gguf Q4_K_M
llama-cli -m support-v3-q4_k_m.gguf -p "Charged twice for order 1182" -n 128
```

Quantisation trades size and speed against fidelity: 8-bit is nearly lossless, the 4-bit "K" variants are the usual sweet spot for CPU and small GPUs, and lower bit widths hurt small models noticeably because they have less redundancy. The task decides tolerance: classification is forgiving, exact JSON with many numeric fields is not. Beyond the task eval, compare perplexity against the f16 model and spot-check that special tokens and the chat template survived conversion.

On-device adds runtimes: llama.cpp builds for Android and iOS, MLX on Apple silicon, ONNX Runtime and ExecuTorch for mobile. Memory is the binding constraint on phones, so 1B to 3B at 4-bit is the realistic range, and thermal throttling makes sustained tokens per second lower than a cold benchmark suggests.

**Follow-ups they will ask:**
- What is the difference between GGUF, AWQ and GPTQ?: GGUF is llama.cpp's container and quant formats for CPU and mixed hardware; AWQ and GPTQ are GPU-oriented 4-bit weight formats used by vLLM and similar servers.
- Can you fine-tune after quantising?: Train with QLoRA on the bitsandbytes 4-bit path, then merge into 16-bit and re-quantise; do not train on a GGUF.
- How do you benchmark on-device?: Measure time to first token and tokens per second on the real device under sustained load, not on a laptop.

**Mistakes to avoid:**
- Shipping the 4-bit model after evaluating only the bf16 one.
- Picking the lowest bit width because it fits, without checking per-slice accuracy.

### Practice
- Distil one narrow task (intent plus fields) from a large model into a 3B instruct model with 3,000 filtered teacher examples; report agreement with the teacher per slice and the escalation rate at your chosen confidence threshold.
- Export the student to GGUF at Q8_0 and Q4_K_M, run the eval on both and on bf16, and tabulate accuracy, file size and tokens per second on your laptop CPU.
- Package the Q4_K_M model with a Modelfile in Ollama, point your application at the local OpenAI-compatible endpoint, then switch the base URL to vLLM and confirm identical outputs at temperature 0.
- Say it out loud: give a two-minute break-even argument for replacing an API call with a fine-tuned 3B model, naming volume, utilisation, fallback and ops cost, and state what would make you keep the API.
