## Fine-tuning Techniques, Simply [Advanced]

> Interviewers rarely want fifteen definitions. They want to hear you sort the techniques into families, say what each family changes inside the model, and pick the cheapest one that solves the problem. A weak answer recites acronyms. A strong answer says "prompting and RAG first, then LoRA or QLoRA for behavior and format, then DPO if I have preference pairs", and explains why.

### In plain words
Fine-tuning means taking a model that already knows language and training it a little more so it behaves the way you need. The first family is teaching by example: you show it thousands of good question and answer pairs (SFT), and the heaviest way to do that is to update every weight in the model (full fine-tuning). The second family trains a small add-on: the big model stays frozen and you train a tiny extra piece (PEFT: LoRA, QLoRA, DoRA, adapters), like clipping a lens onto a camera. The third family learns a soft prompt: the model stays frozen and you learn a few special input vectors that steer it (prompt tuning, prefix tuning, P-tuning). The fourth family aligns with preferences: you show pairs of answers where one is better and push the model toward the better kind (RLHF, PPO, RLAIF, DPO, ORPO).

### From your saved posts
- skdneuron: 15 LLM fine-tuning techniques (SFT, full fine-tuning, PEFT, LoRA, QLoRA, DoRA, adapters, prompt tuning, prefix tuning, P-tuning, RLHF, PPO, RLAIF, DPO, ORPO), grouped in the caption as teach by example, train a small set of weights, learn soft prompts, and align with preferences.
- The post gives names and groups only. The mechanisms, examples and paper references in the cards below are added here.

### C. Supervised Fine-tuning (SFT)
**In one line:** SFT trains a model on prompts paired with the exact answers you want, so it learns that style, format and behavior.

**Think of it like:** Training a new support hire with a binder of real tickets and the replies your best agent wrote.

**Example:** 3,000 pairs of customer email and ideal JSON output (intent, priority, drafted reply) to teach an open model your ticket format. Pick it when prompting cannot hold a format or tone consistently.

**Say it in an interview:** SFT is next-token cross-entropy on curated demonstrations, usually with the loss computed on response tokens only. It is the first stage of post-training and the base for preference tuning. It teaches behavior and format, not fresh facts; that is RAG's job.

**Go deeper:** Fine-tuning & ML track, section "Data Engineering for Fine-tuning".

### C. Full Fine-tuning
**In one line:** Full fine-tuning updates every weight in the model: the most freedom to change it, at the highest memory and compute cost.

**Think of it like:** Renovating the whole house instead of adding a room: maximum change, maximum cost, and real risk of breaking what worked.

**Example:** With mixed precision and Adam, training needs roughly 16 bytes per parameter for weights, gradients and optimizer state, so a 7B model needs over 100 GB before activations. Pick it for big domain shifts with lots of data and budget.

**Say it in an interview:** It has the highest ceiling, but it risks catastrophic forgetting and yields a full model copy per task. I start with LoRA and switch only if evals show the adapter has plateaued.

**Go deeper:** Fine-tuning & ML track, section "ML & Training Fundamentals for LLMs".

### C. PEFT
**In one line:** Parameter-efficient fine-tuning freezes the original model and trains only a small number of new or selected parameters.

**Think of it like:** Clipping a specialist lens onto a camera instead of building a new camera, then swapping lenses per job.

**Example:** With Hugging Face's `peft` library, LoRA on a 7B model typically trains well under 1% of the parameters, and the adapter file is megabytes, not gigabytes. Pick it as the default on limited GPUs or for many task variants of one base.

**Say it in an interview:** PEFT is an umbrella: low-rank methods (LoRA, QLoRA, DoRA), bottleneck adapters and soft prompts. With the base frozen, one served model can carry many tenant or task adapters, and forgetting is reduced, though not eliminated.

**Go deeper:** Fine-tuning & ML track, section "PEFT: LoRA and QLoRA".

### C. LoRA
**In one line:** LoRA freezes each large weight matrix and learns a small correction: two thin matrices whose product is added to it.

**Think of it like:** Sticky-note edits on a textbook page instead of reprinting the book; peel them off or swap them any time.

**Example:** A 4096 by 4096 projection has about 16.8M weights; rank-16 LoRA trains two 4096 by 16 matrices, about 131K. Pick it first once prompting and RAG are not enough.

**Say it in an interview:** LoRA learns the update as B times A, scaled by alpha over r, with B starting at zero so training begins exactly at the base model. I can merge it for zero added latency, or hot-swap many adapters on one base, which vLLM supports.

**Go deeper:** Fine-tuning & ML track, section "PEFT: LoRA and QLoRA".

### C. QLoRA
**In one line:** QLoRA is LoRA trained on top of a 4-bit base model, so large models fit on much smaller GPUs.

**Think of it like:** Keeping the reference textbook as a compressed copy while your sticky-note edits stay at full quality.

**Example:** The QLoRA paper fine-tuned a 65B model on one 48 GB GPU, and a 7B or 8B model routinely fits on a 24 GB card. Pick it when GPU memory is the binding constraint.

**Say it in an interview:** QLoRA stores the frozen base in 4-bit NormalFloat (NF4) via bitsandbytes, adds double quantization and paged optimizers, and trains 16-bit LoRA adapters through the dequantized weights. It trades step speed for memory, so I compare evals against plain LoRA on the same data.

**Go deeper:** Fine-tuning & ML track, section "PEFT: LoRA and QLoRA".

### C. DoRA
**In one line:** DoRA splits each weight into magnitude (how big) and direction (which way), trains the magnitude directly and uses LoRA for the direction.

**Think of it like:** Adjusting a speaker's volume and its aim separately instead of with one clumsy lever.

**Example:** In Hugging Face PEFT you set `use_dora=True` in `LoraConfig`; the rest of the LoRA setup is unchanged. Pick it when plain LoRA at a sensible rank still trails full fine-tuning on your evals.

**Say it in an interview:** DoRA (Weight-Decomposed Low-Rank Adaptation, 2024) starts from the finding that LoRA changes magnitude and direction in a coupled way, unlike full fine-tuning. It is reported to narrow that gap for a small extra training cost, and it still merges into the weights for inference.

**Go deeper:** Fine-tuning & ML track, section "PEFT: LoRA and QLoRA".

### C. Adapters
**In one line:** Adapters are small extra layers inserted inside each transformer block, and only those layers are trained.

**Think of it like:** Fitting a small plug converter between devices in a chain instead of rewiring the devices themselves.

**Example:** The classic Houlsby adapter (2019) is a bottleneck: project down, apply a nonlinearity, project back up, add to the input. Pick it when your framework or older encoder models are built around adapters, or you want stackable task modules.

**Say it in an interview:** Unlike LoRA, a bottleneck adapter sits in the forward path and cannot be merged into the weights, so it adds a little inference latency. People also say "LoRA adapter" loosely for any small add-on, so I clarify which is meant.

**Go deeper:** Fine-tuning & ML track, section "PEFT: LoRA and QLoRA".

### C. Prompt Tuning
**In one line:** Prompt tuning freezes the model and learns a few virtual tokens, trainable vectors placed before the input, that steer it.

**Think of it like:** A magic phrase in a language only the model speaks: numbers, not words.

**Example:** 20 learned vectors for a sentiment task, saved in well under a megabyte, with many tasks sharing one base. Pick it for many narrow tasks on an open-weight model with almost no storage per task.

**Say it in an interview:** Prompt tuning (Lester et al., 2021) trains only input embeddings; the paper found it closes the gap to full fine-tuning as models grow but lags on small ones. It needs gradient access, so closed API models are out, and the vectors are not readable text.

**Go deeper:** Fine-tuning & ML track, section "The 15 Fine-tuning Techniques".

### C. Prefix Tuning
**In one line:** Prefix tuning learns trainable vectors added at every layer, not just the input, giving more steering power than prompt tuning.

**Think of it like:** Instead of whispering one instruction at the front door, you leave a note in every room the request passes through.

**Example:** Li and Liang (2021) used it on GPT-2 for table-to-text and BART for summarization, training about 0.1% of the parameters. Pick it over prompt tuning for generation tasks where input-only soft prompts underperform.

**Say it in an interview:** It prepends learned key and value vectors to attention at every layer, so every token can attend to them. Training was stabilized by generating the prefix with a small MLP, dropped afterward, leaving one prefix per task on a shared frozen model.

**Go deeper:** Fine-tuning & ML track, section "The 15 Fine-tuning Techniques".

### C. P-tuning
**In one line:** P-tuning learns soft prompts through a small helper network and can place them anywhere in a prompt template, mixed with real words.

**Think of it like:** A fill-in-the-blank form where a tiny assistant keeps tuning the magic words in some of the blanks.

**Example:** In Hugging Face PEFT this is `PromptEncoderConfig`, with an MLP or LSTM prompt encoder. Pick it for classification or extraction on open models when plain prompt tuning trains unstably.

**Say it in an interview:** P-tuning (Liu et al., 2021, "GPT Understands, Too") stabilizes continuous prompts with a prompt encoder. P-tuning v2 adds prompts at every layer, like prefix tuning, and reported results comparable to fine-tuning across scales on understanding tasks. All three soft-prompt methods are now niche next to LoRA.

**Go deeper:** Fine-tuning & ML track, section "The 15 Fine-tuning Techniques".

### C. RLHF
**In one line:** RLHF teaches a model the answers people prefer: learn a scorer from human rankings, then train the model to score well.

**Think of it like:** Tasters pick the better dish, a critic learns their taste, and the chef practices until the critic approves.

**Example:** InstructGPT (OpenAI, 2022) ran SFT, a reward model on human comparisons, then PPO, the recipe behind early ChatGPT. Pick it when behavior is easy to judge but hard to demonstrate, and budget allows labelers and RL.

**Say it in an interview:** Three stages: SFT, a reward model on pairwise preferences, then RL with a KL penalty to the SFT model to prevent reward hacking. It is costly and unstable, so teams with only offline pairs often use DPO.

**Go deeper:** Fine-tuning & ML track, section "Preference Optimization & RL Intuition".

### C. PPO
**In one line:** PPO is the reinforcement learning algorithm classic RLHF uses to push the model toward higher reward in small, safe steps.

**Think of it like:** A coach allowing only small technique changes per session, so one lucky result cannot wreck past learning.

**Example:** PPO-based RLHF keeps four models in memory: the policy, a frozen reference, the reward model and a value (critic) model. Pick it when you have a reliable reward and want online learning from fresh samples.

**Say it in an interview:** Proximal Policy Optimization (Schulman et al., 2017) clips the ratio between new and old policy probabilities so each update stays small. GRPO drops the critic and scores each answer against a group of sampled answers, popular for reasoning with verifiable rewards.

**Go deeper:** Fine-tuning & ML track, section "Preference Optimization & RL Intuition".

### C. RLAIF
**In one line:** RLAIF is RLHF where an AI model, not a human, picks the better of two answers.

**Think of it like:** Swapping a panel of human tasters for one head chef with a rubric: cheaper and faster, but with the chef's blind spots.

**Example:** Anthropic's Constitutional AI had a model, guided by a written list of principles, critique answers and label harmlessness preferences. Pick it when human labels are too slow or costly and criteria can be written down.

**Say it in an interview:** An LLM judge with a rubric or constitution produces the preference labels. Google's RLAIF paper reported results comparable to RLHF on tasks such as summarization. The risk is judge bias, like favoring longer answers, so I spot-check against human labels.

**Go deeper:** Fine-tuning & ML track, section "Preference Optimization & RL Intuition".

### C. DPO
**In one line:** DPO aligns a model directly from pairs of better and worse answers, with no reward model and no RL loop.

**Think of it like:** Skipping the critic and the practice rounds: you show the chef pairs of dishes labeled "more like this, less like that".

**Example:** Rows of prompt, chosen and rejected, trained with TRL's `DPOTrainer` to prefer concise, cited answers over rambling ones. Pick it when you have offline preference pairs and SFT-level infrastructure.

**Say it in an interview:** DPO (Rafailov et al., 2023) optimizes the RLHF objective with a classification-style loss on log-probability ratios against a frozen reference model, with beta limiting drift. It is stable and cheap, but learns only from your pairs, so data quality decides the result.

**Go deeper:** Fine-tuning & ML track, section "Preference Optimization & RL Intuition".

### C. ORPO
**In one line:** ORPO does instruction tuning and preference alignment in one training stage, without a reference model.

**Think of it like:** Teaching recipe and taste in one lesson instead of a cooking course and then a tasting course.

**Example:** DPO-style prompt, chosen and rejected data trained with TRL's `ORPOTrainer`: no separate SFT run, no frozen reference in memory. Pick it when compute is tight and you start from a base model.

**Say it in an interview:** ORPO (Odds Ratio Preference Optimization, Hong et al., 2024) adds an odds-ratio penalty to the normal SFT loss, raising the odds of the chosen answer over the rejected one. It saves a stage and memory, but has fewer large-scale reports than DPO, so I validate on my own evals.

**Go deeper:** Fine-tuning & ML track, section "Preference Optimization & RL Intuition".

## Production AI Stack Words [Core]

> Chat tools and vibe coding get a demo running. Running AI in production needs more: deployment, GPUs, Kubernetes, observability, and the ops discipline (MLOps, LLMOps) that keeps quality and cost under control. Interviewers use these words to test whether you have operated an AI system or only prompted one.

### In plain words
Getting a model to answer once on your laptop is the easy part. Production means it answers thousands of people reliably, at a cost you can explain, and you notice when it gets worse before users do. MLOps and LLMOps are the habits that keep models, prompts and data versioned, tested and monitored. Deployment, GPUs and Kubernetes are where the model physically runs, observability is how you see what it is doing, and platform engineering packages all of it so other teams can use it without being experts. Think of a restaurant chain: the model is the recipe, but you also need kitchens, suppliers, inspections and a manager watching every order.

### From your saved posts
- vishakha.sadhwani, production AI stack (post 10): one learning resource per area across RAG and fine-tuning, MLOps and LLMOps, inference and deployment, cloud and Kubernetes, DevOps and AIOps, observability and platform engineering. Examples: "Machine Learning Engineering for Production (MLOps)" (DeepLearning.AI), "Observability Zero to Hero" (Abhishek Veeramalla), "What is Platform Engineering and how it fits into DevOps and Cloud world" (TechWorld with Nana). Its AIOps pick is about automating DevOps with AI.
- vishakha.sadhwani, three levels of inference engineering (post 1): Level 1 vocabulary (LLM APIs, GPU Kubernetes clusters, open-weight versus closed models, pre-training, post-training and inference) and Level 3 benchmarking (TTFT, TPOT, throughput, end-to-end latency). The post calls closed models "foundation" models, but foundation models can be open-weight too.
- lindavivah, build your own inference engine in 6 steps (post 5): a GPU Kubernetes cluster built with Terraform, vLLM serving Qwen, an OpenAI-compatible client pointed at it by changing the base URL, then a load test that shows the KV cache filling and continuous batching.
- Akamai inference workshop repo (Apache-2.0, default model Qwen/Qwen3-4B, uses vLLM's Prometheus `/metrics`): https://github.com/akamai-developers/akamai-workshop-ai-inference

### C. MLOps
**In one line:** MLOps is the practices and tools that take a model from a notebook to production and keep it working there.

**Think of it like:** DevOps for models, except the "code" includes data and weights, and quality can decay with no deploy at all.

**Example:** A fraud model: versioned data, experiments tracked in MLflow, the winner registered, deployed through CI/CD, and drift monitoring that triggers retraining.

**Say it in an interview:** MLOps covers data and model versioning, experiment tracking, a model registry, automated training and deployment, and drift monitoring. Google's maturity model runs from level 0, manual handoffs, to level 2, automated CI/CD of the training pipeline. Models decay as the world changes, so monitoring feeds retraining.

**Go deeper:** MLOps & LLMOps track, section "The ML Lifecycle & MLOps Maturity".

### C. LLMOps
**In one line:** LLMOps is MLOps for LLM apps, where you mostly manage prompts, retrieval, evals and cost instead of training.

**Think of it like:** A cafe that buys bread from a bakery: it does not bake, but it checks every delivery, tracks costs and fixes the menu when quality slips.

**Example:** Versioned prompts, an eval suite in CI on every prompt or model change, every call traced in Langfuse or LangSmith with tokens, latency and cost, and a fallback provider on timeouts.

**Say it in an interview:** LLMOps adds prompt versioning, eval datasets with LLM judges plus deterministic checks, agent tracing, guardrails, cost attribution and provider routing. With a third-party model, regressions come from prompt edits, provider updates and stale indexes, not only retraining.

**Go deeper:** MLOps & LLMOps track, section "Observability & Tracing for LLM Apps".

### C. AIOps
**In one line:** AIOps usually means using AI to run IT operations, like spotting anomalies and grouping alerts; some use it to mean operating AI systems.

**Think of it like:** A control-room dispatcher who sees that forty alarms are one fire and points the crew at the cause.

**Example:** Usual meaning: Datadog Watchdog or Dynatrace flags a latency spike, groups related alerts and links them to a recent deploy. Looser meaning: an "AIOps" team running model deployments, GPU capacity and LLM monitoring.

**Say it in an interview:** The established analyst and vendor meaning is AI for IT operations: anomaly detection, alert correlation, root-cause hints and auto-remediation over metrics, logs and traces. If someone means running AI systems, that is MLOps or LLMOps, and I confirm which they mean.

**Go deeper:** MLOps & LLMOps track, section "AIOps & Platform Engineering".

### C. Platform Engineering
**In one line:** Platform engineering builds an internal self-service platform so product teams can ship and run software without being infrastructure experts.

**Think of it like:** A shared company kitchen with stocked stations and standard recipes, so no cook builds their own stove.

**Example:** A Backstage developer portal where a team picks a "RAG service" template and gets a repo, CI/CD, a Kubernetes deployment, a vector database, tracing and a model gateway key, already wired together.

**Say it in an interview:** It treats infrastructure as a product with golden paths: paved defaults for build, deploy, secrets and observability. For AI that means a shared model gateway with rate limits and cost tracking, self-service GPU capacity and standard eval pipelines.

**Go deeper:** MLOps & LLMOps track, section "AIOps & Platform Engineering".

### C. Observability (metrics, logs, traces)
**In one line:** Observability is understanding what a running system is doing from the outside, mainly through metrics, logs and traces.

**Think of it like:** A car's dashboard (metrics), a trip diary (logs) and a GPS replay of one journey (a trace).

**Example:** Metrics: p95 latency, error rate and GPU utilization in Prometheus and Grafana. Logs: one structured JSON line per request. Trace: one chat request as spans for auth, retrieval, the LLM call and a tool call, each timed.

**Say it in an interview:** Metrics tell me something is wrong, traces tell me where, logs tell me why. I instrument with OpenTelemetry so signals share trace IDs, and for LLM apps I add tokens, cost, time to first token and redacted prompt and response capture.

**Go deeper:** DevOps track, section "Observability & On-call".

### C. Model Deployment
**In one line:** Model deployment is packaging a trained model so it answers real requests safely and at scale, with a way to roll back.

**Think of it like:** Taking a recipe from a test kitchen to a restaurant chain: the same dish everywhere, and a fast recall for a bad batch.

**Example:** `vllm serve Qwen/Qwen3-4B` in a container exposes an OpenAI-compatible `/v1/chat/completions` endpoint on Kubernetes, with health checks, autoscaling and a canary that takes a small share of traffic first.

**Say it in an interview:** I pick the pattern by latency need: online, batch, streaming or edge, then add rollout safety: shadow or canary with eval and latency gates, and fast rollback. For LLMs the serving engine (vLLM, SGLang, TensorRT-LLM) matters as much as the model.

**Go deeper:** MLOps & LLMOps track, section "Model Serving & Deployment Patterns".

### C. GPU Infrastructure
**In one line:** GPU infrastructure is the hardware, drivers and capacity planning that let models run fast, and GPU memory is usually the tightest limit.

**Think of it like:** Many cooks chopping at once but one counter; the ingredients (weights) and every open order (KV cache) must fit on it.

**Example:** A 7B model in BF16 needs about 14 GB for weights alone (2 bytes per parameter), leaving under 10 GB of a 24 GB GPU for KV cache and overhead, which caps concurrent users.

**Say it in an interview:** I size from memory first: weights plus KV cache for the target concurrency and context length, then bandwidth, since decode is usually bandwidth-bound. Multi-GPU tensor parallelism needs a fast interconnect like NVLink, and real cost depends on utilization, not list price.

**Go deeper:** Inference track, section "Inference Fundamentals".

### C. Kubernetes for AI Workloads
**In one line:** Kubernetes for AI runs model servers and training jobs on a cluster where pods request GPUs the way they request CPU and memory.

**Think of it like:** An airport scheduler with a few special gates for wide-body jets (GPU nodes) that ordinary planes are kept away from.

**Example:** The NVIDIA device plugin or GPU Operator advertises GPUs, a vLLM pod sets `nvidia.com/gpu: 1` in its limits, and GPU nodes carry a taint so only tolerating pods land there.

**Say it in an interview:** AI-specific problems: slow cold starts from huge weights, so cache them on a volume; autoscaling on queue depth or KV cache usage, not CPU; and GPU sharing via MIG or time-slicing. KServe, KubeRay and Kueue add serving, distributed jobs and batch queueing.

**Go deeper:** DevOps track, section "Kubernetes Core Objects".

### C. Open-weight vs Closed Models
**In one line:** Open-weight models let you download the weights and run them yourself; closed models are only reachable through the provider's API.

**Think of it like:** Owning a car you can service and modify versus a premium taxi: control versus convenience and the newest model.

**Example:** Open-weight: Llama, Qwen, Mistral, Gemma and DeepSeek, served with vLLM on your GPU. Closed: GPT, Claude and Gemini, called over an API with per-token pricing.

**Say it in an interview:** Open weight is not open source: training data and code are often unreleased, and licenses vary, some with restrictions. I pick open-weight for data residency, fine-tuning, version pinning or steady high volume, and closed models for frontier quality and zero ops, often behind one gateway so I can switch.

**Go deeper:** Inference track, section "Inference Engineering Levels".

### C. Pre-training vs Post-training vs Inference
**In one line:** Pre-training teaches a model language and general knowledge, post-training makes it a useful assistant, and inference is using the finished model.

**Think of it like:** School, then job training, then doing the job every day.

**Example:** Pre-training: next-token prediction over trillions of tokens on thousands of GPUs. Post-training: SFT, preference tuning (RLHF, DPO) and RL for reasoning. Inference: your API call, prefill reading the prompt and decode writing token by token.

**Say it in an interview:** Pre-training is a huge one-time cost that few organizations pay at frontier scale. Post-training gives instruction following, safety and style, and it is where my fine-tuning fits. Inference is paid per request, so at scale it often dominates spend, which is why serving optimization matters.

**Go deeper:** Fine-tuning & ML track, section "ML & Training Fundamentals for LLMs".

### C. Benchmarking an Inference Endpoint
**In one line:** Benchmarking an endpoint is load testing it with realistic traffic to measure its speed and how many users it serves before degrading.

**Think of it like:** Booking more and more tables at a new restaurant until the food arrives late.

**Example:** Ramp concurrency from 1 to 64 with your real prompt and output lengths; record time to first token (TTFT), time per output token (TPOT), end-to-end latency and tokens per second; watch KV cache usage on vLLM's `/metrics`.

**Say it in an interview:** I report p50, p95 and p99, not averages, and find the knee where latency jumps because the KV cache is full and requests queue. The key number is goodput, throughput within the latency SLO, and I change one variable at a time.

**Go deeper:** Inference track, section "Reliability & Observability for Inference".

### C. Self-hosting vs API
**In one line:** An API means paying per token for someone else's model; self-hosting means running one on your own GPUs and paying even when they sit idle.

**Think of it like:** Taxis versus owning a fleet: taxis win at low or spiky use, the fleet only when cars stay busy.

**Example:** The Akamai workshop points an OpenAI-compatible client at your own vLLM endpoint by changing the base URL. Break-even: GPU cost per hour divided by tokens served per hour, versus the API's per-token price.

**Say it in an interview:** APIs give frontier quality, zero ops and elastic scale; self-hosting gives data control, version pinning, fine-tuned models and lower unit cost at high, steady utilization, plus on-call duty. Managed open-model endpoints sit between, and an OpenAI-compatible gateway keeps the choice reversible.

**Go deeper:** Inference track, section "Cost Engineering".

## Vision & Document AI Words [Advanced]

> Floorplan AI turns a drawing into structured data: every room as a closed polygon with coordinates. That one product touches most of the computer vision vocabulary an AI engineer is expected to know: transformers for images, segmentation, edges, corners, vectorizing, OCR, and how quality is measured. Interviewers probe whether you know when a multimodal LLM is enough and when you need a specialist model.

### In plain words
To a computer, a floor plan is just a grid of colored dots, and the goal is to turn those dots into facts like "the kitchen is this shape at these coordinates". First you upload an image or a PDF. A vision transformer looks at the whole picture and labels each pixel by what it belongs to, which splits the plan into rooms. Edge extraction then traces the walls, and corner detection finds the points where walls meet. Those corners become the vertices of one closed polygon per room, written out as JSON with coordinates that software can measure, search and draw.

### From your saved posts
- iiterate technologies (iiterate_technologies), Floorplan AI: floor plans arrive as sketches, scans, CAD exports and brochures in many languages; the pipeline segments rooms with a vision transformer, traces walls, finds corners and outputs closed room polygons with coordinates. The speed (under 4 seconds), training-set size (100,000+ examples) and coverage (20+ floor plan types) figures are the company's own claims, not independently verified.

### C. Vision Transformer (ViT)
**In one line:** A vision transformer cuts an image into small patches, treats each patch like a word, and lets every patch attend to every other patch.

**Think of it like:** Cutting a photo into tiles and letting each tile ask all the others how they relate before deciding what it shows.

**Example:** The original ViT (Google, 2020) used 16 by 16 pixel patches; Meta's Segment Anything and many multimodal LLMs use ViT image encoders.

**Say it in an interview:** Patches become embeddings plus position embeddings, then a transformer encoder runs global self-attention. With less locality bias than a CNN it needs more data or pretraining, but global context helps on floor plans, where a room's identity depends on distant walls and doors.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".

### C. Image Segmentation (semantic vs instance vs panoptic)
**In one line:** Segmentation labels every pixel; the three flavors differ in whether they also separate objects of the same kind.

**Think of it like:** Coloring a map: semantic paints all bedrooms one shade, instance gives each bedroom its own shade, and panoptic does both and colors the background.

**Example:** Semantic: each pixel is wall, room, door or background (U-Net style). Instance: one mask per room (Mask R-CNN style). Panoptic: every pixel gets a class, and rooms also get IDs; Mask2Former does all three.

**Say it in an interview:** Semantic answers "what", instance answers "which one", and panoptic unifies countable things and amorphous stuff. Floor plans need instance-level rooms, since each becomes its own polygon; I evaluate with mIoU for semantic and Panoptic Quality for panoptic.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".

### C. Edge Detection
**In one line:** Edge detection finds pixels where brightness changes sharply, which usually marks an outline, such as a wall.

**Think of it like:** Running a finger across a page in the dark and feeling every raised line.

**Example:** OpenCV's `cv2.Canny(img, 100, 200)` computes gradients, thins them and keeps strong edges plus weak ones connected to them; `cv2.HoughLinesP` then fits straight wall segments.

**Say it in an interview:** Classic detectors like Sobel and Canny need no training, but on real plans they also fire on text, furniture symbols and hatching, so production systems predict walls with a learned model and then vectorize. An edge map is still pixels; the value comes from connected line segments.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".

### C. Corner Detection
**In one line:** Corner detection finds points where edges meet or turn, which in a floor plan are the joints where walls connect.

**Think of it like:** Finding the joints of a picture frame: once you know them, the frame's shape follows.

**Example:** Harris and Shi-Tomasi (`cv2.goodFeaturesToTrack`) flag points where intensity changes in two directions. Raster-to-Vector (ICCV 2017) trained a network to detect L, T and X wall junctions, then assembled walls between them.

**Say it in an interview:** Corners turn a fuzzy mask into a few precise vertices, which is what makes a clean polygon. Classic detectors give false corners on text and symbols, so I prefer learned junction detection plus geometric constraints, measuring corner precision and recall within a pixel tolerance.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".

### C. Polygonization and Structured Output
**In one line:** Polygonization turns a blob of pixels into a clean shape given by a short list of corner coordinates, saved as structured data such as JSON.

**Think of it like:** Tracing a crayon drawing of a room with a ruler and writing down each corner for the builder.

**Example:** `cv2.findContours` on a room mask, `cv2.approxPolyDP` to simplify, vertices snapped to corners, then `{"room": "kitchen", "polygon": [[0,0],[420,0],[420,310],[0,310]], "unit": "cm"}`, checked with Shapely and a JSON schema.

**Say it in an interview:** The hard part is enforcing constraints: closed rings, no self-intersections, shared walls between neighbors, mostly right angles, and a pixel-to-meter scale. I validate geometry and schema before anything downstream uses it, because area, pricing and search depend on it.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".

### C. OCR and Document Parsing
**In one line:** OCR reads text out of an image; document parsing also recovers structure such as headings, tables, reading order and labels.

**Think of it like:** OCR reads words aloud from a photo; parsing also tells you which words form a table and in what order to read them.

**Example:** Tesseract or PaddleOCR read "Bedroom 3.4 x 4.0 m" off a scanned plan; Docling, Unstructured, AWS Textract or Google Document AI return layout, tables and key-value pairs.

**Say it in an interview:** For born-digital PDFs I read the text layer and OCR only scanned pages. In a floor plan pipeline, OCR supplies room labels and the scale, matched to polygons by position. Vision-language models parse well too, but can silently invent text, so I verify.

**Go deeper:** LLMs, RAG & Evals track, section "Advanced RAG Patterns".

### C. Multimodal LLMs vs Specialist Vision Models
**In one line:** A multimodal LLM reasons about images flexibly; a specialist vision model does one visual task, like segmentation, precisely and cheaply.

**Think of it like:** A generalist consultant versus a surveyor with calibrated instruments: ask one what the building is for, the other where the walls are.

**Example:** GPT-4o, Claude, Gemini or Qwen-VL can describe a three-bedroom flat with no training but are unreliable at precise coordinates; a segmentation model trained on labeled plans returns exact masks fast at a fixed cost.

**Say it in an interview:** Specialists handle geometry and measurement, where determinism, speed and cost matter; a multimodal LLM handles semantics, labels and messy edge cases. Often both: the specialist extracts structure, and the LLM reads or sanity-checks it.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".

### C. IoU (how segmentation quality is measured)
**In one line:** IoU, intersection over union, scores how well a predicted shape matches the true one: overlap area divided by combined area.

**Think of it like:** Laying a tracing over the real room: more shared floor and less spill means a higher score.

**Example:** True room 100 sq m, prediction 90, overlap 80: the union is 100 + 90 - 80 = 110, so IoU is 80 / 110, about 0.73. 1.0 is perfect; 0 is no overlap.

**Say it in an interview:** Detection often counts a match at IoU 0.5 or higher, and COCO averages thresholds from 0.5 to 0.95. For semantic segmentation I report mIoU across classes so small ones like doors are not hidden, and for polygons I also check vertex accuracy.

**Go deeper:** LLMs, RAG & Evals track, section "Computer Vision & Document AI".
