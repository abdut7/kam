## Docker Fundamentals

### In plain words
A Docker image is a sealed lunchbox: your code, the exact Python or Node version and every library, packed together so it behaves the same on your laptop, in CI and in production. A container is that lunchbox opened and running. The Dockerfile is the packing list, and the order of the list matters, because Docker reuses layers that have not changed and that is what makes rebuilds fast. For an AI service the usual first step is exactly this: put a FastAPI app that calls a model into an image, run it locally with Compose next to its database, then ship that same image.

### From your saved posts
- bashi_fuirkashi (post 2), AI engineer roadmap: build your first AI service with FastAPI, containerize it with Docker and put it behind a real API.
- jam.with.ai (post 13), 12-week roadmap: weeks 7 to 9 deploy the RAG app with FastAPI and Docker before turning it into a production agent.
- vishakha.sadhwani (post 10), "Build the production stack": "DevOps + LLM + AI Project with Docker, Kubernetes, vLLM" as the model deployment resource.

## Kubernetes Core Objects

### In plain words
Kubernetes is a building manager for containers: you write down what you want ("three copies of this API, each with 1 GB of memory, reachable under this name") and it keeps making reality match. A Pod is one running unit, a Deployment keeps the right number of Pods alive and swaps versions gradually, and a Service gives them one stable address. AI workloads use the same objects, with two twists: GPUs are an extra resource you ask for, and models take a while to load, so health checks must wait for them. Learn these objects first; GPU scheduling and inference servers are built on top of them.

### From your saved posts
- vishakha.sadhwani (post 1), three levels of inference engineering: level 1 includes GPU-based Kubernetes clusters, and level 2 calls Kubernetes the point where scaling and scheduling AI workloads meet.
- lindavivah (post 5), build your own inference engine in 6 steps: Terraform builds a Kubernetes cluster with a GPU node, vLLM serves Qwen on it, and a port-forward reaches it from your laptop. https://github.com/akamai-developers/akamai-workshop-ai-inference
- vishakha.sadhwani (post 10), "Build the production stack": Kubernetes resources "The Only Kubernetes Course You'll Ever Need", "Kubernetes for AI: Zero to Hero" and "Kubernetes Security Best Practices in 12 Minutes".

## Kubernetes Operations & Debugging

### In plain words
Day-to-day Kubernetes is detective work: a pod will not start, keeps crashing or gets killed for using too much memory, and you follow a fixed routine of commands to find out why. GPUs add their own puzzles. GPU machines usually sit in a separate group (a node pool) with a "keep out" sign (a taint), so only pods that ask for a GPU land there. The NVIDIA GPU Operator installs the drivers and the device plugin that lets Kubernetes count GPUs, and a pod asks for one with `nvidia.com/gpu: 1`. GPU nodes are slow and expensive to add, so scaling and model loading need more patience than a normal web API.

### From your saved posts
- vishakha.sadhwani (post 1), three levels of inference engineering: GPU-based Kubernetes clusters at level 1; deploying on a GPU cluster and trying serving patterns at level 2.
- lindavivah (post 5), build your own inference engine: a GPU node on Kubernetes running vLLM, load-tested to watch the KV cache fill and continuous batching keep the GPU busy; the workshop repo reads vLLM's Prometheus /metrics to observe batching, queueing and saturation. https://github.com/akamai-developers/akamai-workshop-ai-inference
- vishakha.sadhwani (post 10), "Build the production stack": "Kubernetes for AI: Zero to Hero" and "DevOps + LLM + AI Project with Docker, Kubernetes, vLLM".

## Observability & On-call

### In plain words
Observability means being able to answer "what is the system doing right now, and why?" without guessing. Metrics are the car's dashboard gauges, logs are the trip diary, and traces are the GPS route of one journey through every service. On-call is the rota of who gets woken up when something breaks, and good alerting wakes them only for problems users actually feel. For AI features you add a few gauges of your own: tokens, cost, model latency and how often tools or providers fail.

### From your saved posts
- vishakha.sadhwani (post 10), "Build the production stack": "Observability Zero to Hero" (Abhishek Veeramalla, about 11 hours) as the observability resource, next to DevOps and AIOps in the same stack.
- anay.tech (post 6), 7 AI system design patterns: observability (track LLM calls, latency, cost and failures).
- vishakha.sadhwani (post 1), three levels of inference engineering: level 3 starts with observability and benchmarking (time to first token, time per output token, throughput, end-to-end latency).
