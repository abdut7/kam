## The 15 Fine-tuning Techniques [Advanced]

> Fifteen names get thrown around in fine-tuning conversations, and interviewers use them to see whether you hold a map or a list. A weak answer recites acronyms. A strong answer sorts them into a few families, notices that two separate questions are mixed into the list (how much of the model you train, and what signal you train it on), and picks the cheapest technique that fixes a measured problem. This section is the map; the PEFT and preference optimization sections are the detail.

### In plain words
All fifteen techniques change a model by training it some more, and they fall into four families. Supervised fine-tuning teaches by example: show the model many good question and answer pairs and it learns to answer that way; full fine-tuning does this by adjusting every number (weight) inside the model. Parameter-efficient methods (LoRA, QLoRA, DoRA, adapters) freeze the model and train a small add-on, like clipping a lens onto a camera instead of building a new camera. Soft-prompt methods (prompt tuning, prefix tuning, P-tuning) train only a few learned "words" placed in front of the input that steer the frozen model. Preference methods (RLHF, PPO, RLAIF, DPO, ORPO) teach from comparisons, "this answer is better than that one", instead of from single correct answers.

### From your saved posts
- skdneuron: the 15 LLM fine-tuning techniques (SFT, full fine-tuning, PEFT, LoRA, QLoRA, DoRA, adapters, prompt tuning, prefix tuning, P-tuning, RLHF, PPO, RLAIF, DPO, ORPO) and the four groups they fall into.
- vishakha.sadhwani: the one-resource pick for fine-tuning in the production-stack post, freeCodeCamp's "Fine Tuning LLM Models, Generative AI Course".

### Concepts you must understand
- The whole map in one table; cost is relative and mostly about GPU memory.

| Technique | Family | What is trained | Typical use | Cost |
| --- | --- | --- | --- | --- |
| SFT (supervised fine-tuning) | Supervised | the model, all weights or an add-on, on prompt and ideal-response pairs | format, style, task behaviour, tool-call discipline | set by how many weights you train |
| Full fine-tuning (FFT) | Supervised | every weight | large domain shifts, continued pretraining, lots of high-quality data | highest: gradients and optimizer state for every weight, a full model copy per task |
| PEFT | Umbrella for the add-on and soft-prompt families | a small set of new or selected parameters, base frozen | the default for product fine-tunes | low |
| LoRA | PEFT | two low-rank matrices beside chosen linear layers | default adapter, many adapters on one base | low; mergeable, no inference overhead once merged |
| QLoRA | PEFT | LoRA adapters on a base stored in 4-bit NF4 | models up to about 8B on one 16 to 24 GB GPU | lowest memory; slower steps from dequantization |
| DoRA | PEFT | a magnitude vector plus a LoRA update to the weight direction | when LoRA at low rank falls short | a little above LoRA; mergeable |
| Adapters (bottleneck) | PEFT | small bottleneck layers inserted inside each block | multi-task setups, the original PEFT method | low to train; extra latency because they cannot be merged |
| Prompt tuning | Soft prompts | a few virtual-token embeddings prepended to the input | many tasks on one very large frozen model | tiny |
| Prefix tuning | Soft prompts | learned key and value vectors prepended at every layer | generation tasks on a frozen model | tiny |
| P-tuning | Soft prompts | virtual tokens produced by a small prompt encoder; v2 applies them at every layer | classification and other understanding tasks | tiny |
| RLHF | Preference | the policy, through a reward model trained on human comparisons | chat alignment: helpfulness, tone, safety | highest complexity: human labels plus an RL loop |
| PPO | Preference (the RL optimizer inside RLHF) | the policy, with value, reward and frozen reference models alongside | the classic RLHF update step | high: four models in memory, sampling inside training |
| RLAIF | Preference | the same loop as RLHF, with an AI model producing the preference labels | scaling preference labels, principle-based feedback | cheaper labels, same training cost |
| DPO | Preference | the policy directly on chosen and rejected pairs against a frozen reference | default preference tuning for product teams | moderate: runs like SFT plus reference log-probs |
| ORPO | Preference (fused with SFT) | SFT loss plus an odds-ratio preference term, no reference model | one-stage alignment when compute is tight | low to moderate |

- Two questions hide inside the list: how much of the model you train (all weights, an add-on, or a soft prompt) and what signal you train on (demonstrations or comparisons); they combine, so "SFT with QLoRA" and "DPO with LoRA" are ordinary recipes.
- PEFT is an umbrella, not one technique: the Hugging Face PEFT library implements LoRA, DoRA and the three soft-prompt methods, QLoRA is LoRA plus a bitsandbytes 4-bit base, and classic bottleneck adapters live in the separate AdapterHub `adapters` library.
- Today's default ladder is SFT with LoRA or QLoRA, then DPO if comparisons are needed; full fine-tuning, soft prompts and PPO are exceptions you justify with evidence.
- Cost is mostly memory: the base weights in some precision, gradients and optimizer state for whatever you train, and any extra models a preference method keeps in memory.

### Q. Walk me through the main families of fine-tuning techniques and when you would use each.
**Short answer (45 seconds):** I group them in four families. Supervised fine-tuning, full or parameter-efficient, teaches by example and is where nearly every project starts: format, style, task, tool calls. Parameter-efficient methods, LoRA, QLoRA, DoRA and adapters, freeze the base and train a small add-on; that is the default because it is cheap and the add-on is easy to swap. Soft-prompt methods train a few virtual tokens and are mostly historical for the model sizes teams fine-tune today. Preference methods, RLHF with PPO, RLAIF, DPO and ORPO, teach from comparisons and come after SFT, when quality is a judgement call or a stubborn failure needs suppressing.

**Deeper explanation:** The cleaner picture has two axes: how much of the model you train, and what signal you train on. Cells combine freely.

```text
                 demonstrations (SFT)           comparisons (preference)
all weights      full fine-tuning               full DPO or RLHF (labs, big budgets)
small add-on     LoRA, QLoRA, DoRA, adapters    DPO or ORPO with LoRA (product default)
soft prompt      prompt, prefix, P-tuning       rare
```

The path for a product team: prove that prompting and retrieval have hit a ceiling on an eval set (When to Fine-tune), run SFT with LoRA or QLoRA, evaluate, and add DPO only if the remaining failures are about preference rather than correctness. Full fine-tuning and PPO are escalations backed by evidence, not starting points.

**Follow-ups they will ask:**
- Where does PEFT fit?: It is the umbrella name for the add-on and soft-prompt rows, not a separate technique.
- Which family fixes hallucinated facts?: None reliably; facts belong in retrieval.
- What would you try first for a JSON-format problem?: Constrained decoding or a structured-output mode, then SFT with LoRA on a few thousand clean examples if that is not enough.

**Mistakes to avoid:**
- Treating the fifteen as fifteen alternatives; most are combinable layers of one recipe.
- Starting with RLHF or full fine-tuning before an SFT baseline and an eval set exist.

### Q. LoRA vs QLoRA vs DoRA vs adapters: what is the difference and how do you choose?
**Short answer (45 seconds):** All four freeze the base and train a small add-on; they differ in where the add-on lives and what it costs at inference. LoRA learns a low-rank update beside existing linear layers and can be merged back, so it adds nothing at serving time. QLoRA is LoRA on a base stored in 4-bit, which cuts training memory enough for one consumer GPU. DoRA splits each weight into magnitude and direction and applies LoRA to the direction, often closing part of the gap to full fine-tuning at low rank, at some extra training cost. Classic adapters insert new layers that cannot be merged, so they add latency. My default is LoRA, QLoRA when memory is tight, DoRA when LoRA plateaus.

**Deeper explanation:** The mechanics and memory math for LoRA and QLoRA are in "PEFT: LoRA and QLoRA"; this is the comparison view.

| Method | Where it lives | Mergeable | Training memory | Pick it when |
| --- | --- | --- | --- | --- |
| LoRA | low-rank B A beside linear layers | yes | low | default |
| QLoRA | LoRA on a 4-bit NF4 base | into a 16-bit copy of the base | lowest | GPU memory is the constraint |
| DoRA | magnitude vector plus LoRA on direction | yes | a little above LoRA | LoRA underfits at your rank |
| Adapters | bottleneck layers inside each block | no | low | legacy multi-task setups |

```python
from peft import LoraConfig
cfg = LoraConfig(r=16, lora_alpha=32, target_modules="all-linear",
                 use_dora=True, task_type="CAUSAL_LM")  # drop use_dora for plain LoRA
# QLoRA: load the base with BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
```

**Follow-ups they will ask:**
- Can you serve DoRA adapters unmerged?: Check your serving engine's adapter support first; merging is the safe path.
- Does QLoRA cost quality?: Usually little for SFT, but evaluate the merged model at the precision you will serve.
- Why did adapters lose to LoRA?: Their extra sequential layers add latency at small batch sizes, while LoRA merges away.

**Mistakes to avoid:**
- Calling QLoRA a different adapter; the adapter is plain LoRA, only the base is quantized.
- Choosing DoRA by default without an eval showing LoRA fell short.

### Q. What are prompt tuning, prefix tuning and P-tuning, and why are they used less today?
**Short answer (45 seconds):** All three freeze the model and learn soft prompts: vectors that act like extra tokens but are not real words. Prompt tuning learns a few embeddings prepended to the input. Prefix tuning learns key and value vectors prepended at every layer, so it steers each layer directly. P-tuning produces its virtual tokens with a small prompt encoder, and P-tuning v2 applies them at every layer, much like prefix tuning. They are tiny to train and store, but they are used less because on the mid-sized open models teams actually fine-tune, LoRA is usually more accurate and more stable, and the tooling and serving ecosystem standardised on LoRA.

**Deeper explanation:** The original prompt tuning work showed it catching up with full fine-tuning only as models grew to around ten billion parameters and beyond; at a few billion it lagged. Soft prompts also converge slowly, are sensitive to initialisation and learning rate, use up positions in the context window, and cannot be read or debugged. Meanwhile strong instruction-tuned models made ordinary text prompts good enough for many tasks soft prompts were invented for, and LoRA gained merging, multi-adapter serving and support in every training tool.

```text
prompt tuning:  [p1 ... p20] + input tokens -> frozen model     (input layer only)
prefix tuning:  learned K,V prefix at every layer -> frozen model
P-tuning:       prompt encoder -> virtual tokens -> frozen model (v2: every layer)
```

They still make sense when each tenant's customisation must be a few kilobytes, or for research on very large frozen models.

**Follow-ups they will ask:**
- How many parameters does prompt tuning train?: Virtual tokens times the hidden size, for example 20 x 4,096, about 82 thousand.
- Is a soft prompt the same as a system prompt?: No; a system prompt is real text the model reads, a soft prompt is learned vectors with no text form.
- Where do they live in tooling?: The Hugging Face PEFT library implements all three.

**Mistakes to avoid:**
- Calling prompt engineering "prompt tuning"; one edits text, the other trains vectors.
- Recommending soft prompts for a 7B model without evidence they beat LoRA.

### Q. RLHF, PPO, RLAIF, DPO and ORPO: how do they relate?
**Short answer (45 seconds):** They are one family seen at different layers. RLHF is the pipeline: collect human comparisons, train a reward model, then optimise the model with reinforcement learning against that reward. PPO is the RL algorithm classically used inside that pipeline. RLAIF keeps the pipeline but lets an AI model produce the comparisons instead of humans. DPO removes the reward model and the RL loop and trains directly on chosen and rejected pairs against a frozen reference. ORPO goes one step further and folds the preference term into SFT, so there is no reference model and no separate stage.

**Deeper explanation:** Ask two questions of each method: who labels the preferences, and how is the model optimised?

| Method | Labels from | Optimisation | Extra models in training |
| --- | --- | --- | --- |
| RLHF with PPO | humans | reward model, then online RL | reward, value, reference |
| RLAIF | an AI judge, often guided by written principles | as RLHF, or a direct method | depends on the optimiser |
| DPO | humans or AI | closed-form loss on pairs, offline | frozen reference |
| ORPO | humans or AI | SFT loss plus odds-ratio term, one stage | none |

So RLAIF is about the label source and is independent of the rest: AI-labelled pairs feed DPO as easily as PPO. The trend is simplification, each step removing a moving part and trading some control for stability and cost. Online RL has returned in another form for reasoning models, through GRPO with verifiable rewards. The objectives, data formats and failure modes are in "Preference Optimization & RL Intuition".

**Follow-ups they will ask:**
- Is PPO the same as RLHF?: No; PPO is one optimiser, RLHF is the whole pipeline.
- What is the risk with RLAIF?: The judge's biases (length, style, favouring its own outputs) become the model's, so audit a sample with humans.
- Which would you run first?: DPO on a few thousand pairs after SFT.

**Mistakes to avoid:**
- Listing the five as competitors; RLAIF changes the labeller, the others change the optimiser.
- Forgetting that DPO still needs reference log-probs (cheap with LoRA, where the reference is the base with the adapter switched off).

### Q. Full fine-tuning vs PEFT: when is full fine-tuning worth it?
**Short answer (45 seconds):** Full fine-tuning is worth it when the change is too big for a small add-on to carry: continued pretraining on a large domain corpus, a new language, or tens of thousands of high-quality examples where an eval shows LoRA plateauing below target, and you have the GPUs to shard the job. For format, style, tool use and most product tasks, PEFT lands within eval noise of full fine-tuning at a fraction of the cost. The capacity argument is in "PEFT: LoRA and QLoRA"; in practice the deciding factor is often lifecycle cost rather than the training run.

**Deeper explanation:**

| Factor | Full fine-tuning | PEFT (LoRA family) |
| --- | --- | --- |
| Training memory | weights, gradients and optimizer state for every parameter; multi-GPU for 8B | frozen base plus a small trainable set; one GPU |
| Artefact per task | a full model copy | an adapter of tens to hundreds of megabytes |
| Serving many tasks | one deployment per task | one base, many adapters |
| Forgetting | higher risk; needs replay of general data | lower; base untouched |
| New base model release | full retrain | retrain adapters cheaply |

A middle path often beats both: fully fine-tune a small model, 1B to 3B, for one narrow task. You get full-capacity learning at a GPU budget close to LoRA on a larger model, and it pairs naturally with distillation from a frontier model.

**Follow-ups they will ask:**
- How do you decide with evidence?: Run LoRA at two ranks on all linear layers; if quality rises with rank and is still short, capacity is the bottleneck and full fine-tuning is justified.
- How do you limit forgetting?: Mix in general instruction data, lower the learning rate, and run a regression eval on general tasks.
- What infrastructure does it need?: FSDP or DeepSpeed ZeRO sharding, sharded checkpoints and fast storage.

**Mistakes to avoid:**
- Choosing full fine-tuning because it sounds more serious, with no LoRA baseline.
- Ignoring the serving cost of one full model per task.

### Practice
- Draw the two-axis map (how much you train by what signal you train on) from memory, place all fifteen techniques on it, and check it against the table.
- With the Hugging Face PEFT library, fine-tune one small instruct model on the same 1,000 examples with LoRA, DoRA (`use_dora=True`) and prompt tuning; record trainable parameters, peak memory, wall-clock time and the task metric for each.
- Take the best SFT adapter, build 500 preference pairs with a judge, and compare DPO and ORPO on judge win rate, response length and a general regression set.
- Say it out loud: in 90 seconds, sort the fifteen techniques into four families and name the two you would use first on a new product fine-tune, and why.

## When to Fine-tune

### In plain words
Fine-tuning means training an existing model a little more on your own examples so its default behaviour changes. It is like coaching an experienced new hire on your team's way of writing: it changes habits and style well, but it is a poor way to make them memorise a handbook that changes every week, which is what search over your documents (retrieval) is for. So you first try better instructions and examples in the prompt, then retrieval for facts, and fine-tune only when tests show those have stopped improving. The fifteen named techniques are simply different ways of doing that coaching.

### From your saved posts
- skdneuron: SFT and full fine-tuning as the "teach by example" family, the starting point of the 15-technique map.
- anay.tech: fine-tuning as one of seven AI system design patterns, used when prompting or RAG is not enough.

## PEFT: LoRA and QLoRA

### In plain words
Retraining every weight of a large model needs several big GPUs, so parameter-efficient fine-tuning (PEFT) freezes the model and trains a small add-on instead. LoRA is the most popular add-on: two thin matrices beside existing layers that learn the change you want, usually well under one percent of the model's size. QLoRA does the same while storing the frozen model in 4-bit numbers, which cuts memory enough to train an 8B model on a single 24 GB graphics card. Think of it as clipping a removable lens onto a camera instead of rebuilding the camera, and you can keep a different lens for each customer.

### From your saved posts
- skdneuron: PEFT, LoRA, QLoRA, DoRA and adapters as the "train a small set of weights" family of the 15 techniques.

## Preference Optimization & RL Intuition

### In plain words
Supervised fine-tuning shows the model good answers; preference tuning shows it two answers and says which one is better. That helps with qualities that are easier to judge than to write, such as tone, brevity or knowing when to refuse, like a teacher marking "this essay is better than that one" instead of writing a model essay. RLHF does this with a separate scoring model and a trial-and-reward training loop (PPO), RLAIF lets an AI do the judging instead of people, and DPO and ORPO skip the scoring model and learn straight from the pairs. Most product teams use DPO after SFT because it is far simpler to run.

### From your saved posts
- skdneuron: RLHF, PPO, RLAIF, DPO and ORPO as the "align with preferences" family of the 15 techniques.
