# DevOps & Delivery

> This track covers how code gets from a laptop to production and stays healthy there: Docker images, running containers safely, Kubernetes objects and debugging, CI/CD pipelines, deployment strategies, scaling and reliability, infrastructure as code, observability, and the security of the delivery pipeline itself. For an AI Full Stack Engineer the bar is practical rather than academic: interviewers want to hear that you have shipped containerized Node.js and Python services, can read a failing pod, can design a pipeline that gates on tests and evals, and can reason about autoscaling, GPUs, rollbacks and on-call without hand waving. LLM features add their own twists (slow cold starts, provider rate limits, eval gates, GPU nodes) and strong candidates weave those in naturally.

## Docker Fundamentals

> Interviewers start here to calibrate: a weak answer recites "containers are lightweight VMs" and pastes a Dockerfile from a tutorial; a strong answer explains layers, cache behavior, why the image is small and non-root, how signals reach the process, and what changes between the local compose stack and production. Expect them to hand you a bad Dockerfile and ask what you would change.

### Concepts you must understand
- An image is an immutable, layered, content-addressed filesystem plus metadata (CMD, ENV, EXPOSE, USER); a container is a process tree started from that image with a thin writable layer on top, so removing the container discards that layer.
- Each RUN, COPY and ADD instruction produces a layer; the build cache reuses a layer only when the instruction and all its inputs (file checksums for COPY) are unchanged, and the first miss invalidates every later layer.
- Order Dockerfile instructions from least to most frequently changing: base image, system packages, dependency manifests and install, then application source.
- Multi-stage builds separate build-time tooling (compilers, dev dependencies, TypeScript) from the runtime image, so the shipped image contains only what the process needs.
- Smaller base images (slim, alpine, distroless) cut pull time and attack surface, but alpine's musl libc can break native Node modules and Python wheels built for glibc.
- Containers run as root by default; set USER to an unprivileged account so an application bug or container escape does not start with root on the shared host kernel.
- .dockerignore keeps node_modules, .git, .env and local build output out of the build context, which speeds up builds and keeps secrets out of layers.
- Exec-form CMD (JSON array) makes your process PID 1 so it receives SIGTERM directly; shell form wraps it in /bin/sh, which does not forward signals.
- Compose describes a multi-container local stack (app, Postgres, Redis) on one user-defined network where services resolve each other by service name; named volumes persist data across container restarts.
- Secrets never belong in ENV or COPY instructions because they persist in image history; use BuildKit secret mounts at build time and runtime injection in production.

### Q. What is the difference between a Docker image and a container, and what actually happens when you run docker run?
**Short answer (45 seconds):** An image is a read-only, layered filesystem plus metadata such as the default command, environment and exposed ports, identified by a content digest. A container is an instance of that image: Docker adds a thin writable layer, creates Linux namespaces for PID, network, mount and users, applies cgroup limits, and starts the configured process inside. Many containers can share one image's layers on disk.

**Deeper explanation:** `docker run` does several things in sequence: it pulls the image if it is not present locally, creates a container with a writable layer stacked on the image layers through an overlay filesystem (overlay2), sets up a network namespace attached to the bridge network with a veth pair, mounts any volumes, then executes the entrypoint as PID 1 of the new PID namespace. The writable layer holds everything the process writes to the container filesystem and is deleted with the container, which is why durable data must live in a volume or an external service.

```bash
docker run -d --name api -p 8080:3000 -e NODE_ENV=production \
  --memory=512m --cpus=1 ghcr.io/acme/api@sha256:3f1c...
docker inspect api --format '{{.State.Pid}} {{.HostConfig.Memory}}'
```

Because layers are content addressed, two images built from the same base share those layers on the host and in the registry, so a large base pulled once is reused by every service built on it.

**Follow-ups they will ask:**
- Where does the writable layer go when the container is removed: it is discarded, so uploads or logs written there are lost; use volumes or object storage.
- Is a container a VM: no, it is a normal Linux process isolated by namespaces and limited by cgroups, sharing the host kernel.
- What is the difference between CMD and ENTRYPOINT: ENTRYPOINT is the executable, CMD supplies default arguments that `docker run` can override.

**Mistakes to avoid:**
- Calling containers "lightweight VMs"; interviewers want namespaces, cgroups and a shared kernel.
- Treating the container filesystem as persistent storage.

### Q. How does Docker layer caching work, and how would you structure a Dockerfile for a Node.js service to maximize cache hits?
**Short answer (45 seconds):** Every RUN, COPY and ADD creates a layer, and the builder reuses a cached layer only if the instruction and its inputs are identical to a previous build; for COPY that means the checksums of the copied files. The first miss invalidates everything after it. So you copy package.json and the lockfile first, run `npm ci`, and only then copy the rest of the source, so a code change does not reinstall dependencies.

**Deeper explanation:**

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --omit=dev
COPY . .
CMD ["node", "src/server.js"]
```

The cache mount keeps npm's download cache across builds without baking it into a layer. CI runners are usually ephemeral, so you export the layer cache: `docker buildx build --cache-from type=registry,ref=ghcr.io/acme/api:cache --cache-to type=registry,ref=ghcr.io/acme/api:cache,mode=max`, or `type=gha` on GitHub Actions. Combine `apt-get update && apt-get install -y --no-install-recommends ... && rm -rf /var/lib/apt/lists/*` in one RUN; if they are separate, a stale `apt-get update` layer is reused forever, and files deleted in a later layer still exist in the earlier one, so the image does not shrink.

**Follow-ups they will ask:**
- Why `npm ci` instead of `npm install`: it installs exactly what the lockfile says, fails if package.json and the lockfile disagree, and is faster for clean installs.
- Does changing an ARG invalidate the cache: yes, from the first instruction that uses it onward, so declare frequently changing build args late in the file.
- How do you inspect layers: `docker history` and the `dive` tool show size and contents per layer.

**Mistakes to avoid:**
- `COPY . .` before installing dependencies, so every commit reinstalls node_modules.
- Deleting files in a later RUN and expecting the image to get smaller.

### Q. Show me a production-grade multi-stage Dockerfile for a TypeScript Node.js API and explain what each stage does.
**Short answer (45 seconds):** Three stages: install all dependencies including dev tooling, compile TypeScript and prune dev dependencies, then copy only dist and the pruned node_modules into a clean slim runtime image that runs as the non-root node user. The compiler, tests and source never reach production.

**Deeper explanation:**

```dockerfile
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM deps AS build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev

FROM node:20-slim AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

The deps stage is cached until the lockfile changes. The build stage compiles and then `npm prune --omit=dev` removes TypeScript, test runners and linters. The runtime stage starts from a fresh base so nothing from the build context leaks in, and the official node image already ships an unprivileged `node` user. If the app writes files at runtime, use `COPY --chown=node:node` and mount a volume for that path.

**Follow-ups they will ask:**
- Why not run ts-node in production: slower startup, larger image, and compile errors surface at runtime instead of build time.
- What about native modules like sharp or bcrypt: compile them in a stage built on the same base family as the runtime so binaries match the runtime libc.
- How do you keep build and runtime Node versions in sync: pin one base tag or digest and reference it in both stages, ideally via a build ARG.

**Mistakes to avoid:**
- Copying the whole /app from the build stage, which drags source and devDependencies into production.
- Mixing an alpine build stage with a slim runtime stage, so native binaries are linked against the wrong libc.

### Q. How would you containerize a Python FastAPI service, and which base image would you choose and why?
**Short answer (45 seconds):** Use python:3.12-slim, a Debian-based glibc image, so prebuilt manylinux wheels for pydantic-core, numpy or psycopg install in seconds instead of compiling. Install into a virtualenv in a build stage, copy only that venv into the runtime stage, run as a non-root user, and start uvicorn directly with an exec-form CMD.

**Deeper explanation:**

```dockerfile
FROM python:3.12-slim AS build
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=app:app src ./src
USER app
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Copying the venv rather than the whole build stage leaves pip's cache behind. `PYTHONUNBUFFERED=1` makes logs reach stdout immediately instead of sitting in a buffer until the process exits, which matters when a pod is killed. For concurrency, run several uvicorn workers (or gunicorn with uvicorn workers) sized to the CPU limit; each worker is a separate process with its own memory footprint, so size the memory limit accordingly. Pin versions with a lockfile (pip-tools, Poetry or uv) so builds are reproducible.

**Follow-ups they will ask:**
- Why not alpine: musl means many wheels compile from source, builds take minutes and sometimes fail; slim is the pragmatic default.
- How do you handle torch or CUDA: use the vendor CUDA base images for GPU workloads, CPU-only wheels where no GPU is present, and put the heavy install in an early layer so it caches.
- How many workers: start with roughly the number of CPUs allotted and measure; async FastAPI handles many concurrent I/O-bound requests per worker.

**Mistakes to avoid:**
- Unpinned `pip install` so two builds of the same commit produce different images.
- Copying the whole repository, including .env files and tests, into the runtime image.

### Q. Why should containers not run as root, and how do you make a Node or Python image run as a non-root user?
**Short answer (45 seconds):** Inside a container, root is still uid 0 on the shared host kernel. If an attacker gets code execution through the app and then finds a kernel or runtime vulnerability, or a misconfigured mount, being root turns that into a host compromise. Running as an unprivileged user removes the most common escalation path at almost no cost: add a USER instruction after your files are in place and make sure the process only needs to write to paths that user owns.

**Deeper explanation:** The official node images ship a `node` user, so `USER node` is enough. For Python or distroless images create one: `RUN useradd --create-home --uid 10001 app` and later `USER app`. Use a high, fixed uid so Kubernetes `runAsNonRoot: true` and `runAsUser` checks are predictable, and use `COPY --chown=app:app` so files are readable. Ports below 1024 need extra privilege, so listen on 3000 or 8000 and let the Service or load balancer map port 80. In Kubernetes, pair this with a pod securityContext:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  readOnlyRootFilesystem: true
```

User namespaces and rootless Docker go one step further by mapping container root to an unprivileged host uid, but the simple USER instruction is the baseline every reviewer expects.

**Follow-ups they will ask:**
- The app needs to write a cache or temp directory: create it in the Dockerfile with the right owner, or mount an emptyDir or tmpfs at that path.
- What breaks when you switch to non-root: anything that writes to /app, /root or /var at runtime, and package install steps placed after USER.
- How do you enforce this across teams: admission policies (Kyverno or Gatekeeper) that reject pods without runAsNonRoot, plus image scanning that flags root images.

**Mistakes to avoid:**
- Putting USER before `npm ci` or `pip install` and then fighting permission errors.
- Assuming the container boundary makes root harmless.

### Q. How do Docker networking and volumes work, and how would you set up a local stack with Compose for an API that needs Postgres and Redis?
**Short answer (45 seconds):** Compose puts every service on a user-defined bridge network where the embedded DNS resolves service names, so the API connects to `postgres:5432` and `redis:6379` by name. Only the API publishes a host port. Named volumes keep Postgres data across restarts, and `depends_on` with a health condition stops the API from starting before the database accepts connections.

**Deeper explanation:**

```yaml
services:
  api:
    build: .
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgres://app:app@postgres:5432/app
      REDIS_URL: redis://redis:6379
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
  postgres:
    image: postgres:16
    environment: { POSTGRES_USER: app, POSTGRES_PASSWORD: app, POSTGRES_DB: app }
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      retries: 10
  redis:
    image: redis:7
volumes:
  pgdata: {}
```

Networking: the default bridge network gives containers private IPs and NAT to the outside; publishing `-p 3000:3000` adds a host port forward. Containers on the same user-defined network reach each other on their internal ports regardless of what is published. Volumes: named volumes are managed by Docker and are the right choice for database data; bind mounts map a host directory and are what you use for hot reload of source in development; tmpfs mounts are memory-only for scratch data. Database data must never live in the container's writable layer.

**Follow-ups they will ask:**
- Why can the API reach Postgres but your laptop cannot: the Postgres port is not published; add `ports: ["5432:5432"]` or use `docker compose exec postgres psql`.
- How do you run migrations locally: a one-shot service or `docker compose run --rm api npm run migrate` against the same network.
- How do you keep dev and prod parity: the same image in both, with only environment variables and compose overrides differing.

**Mistakes to avoid:**
- Using `localhost` inside the API container to reach Postgres; localhost is the container's own network namespace.
- Relying on `depends_on` without a health condition and then adding sleep loops to the entrypoint.

### Q. How do you handle configuration and secrets in Docker builds and at runtime without leaking them into the image?
**Short answer (45 seconds):** Configuration comes from environment variables or mounted files at runtime, never baked in, so one image runs in every environment. Secrets never go through ENV, ARG or COPY in the Dockerfile because every layer is kept in the image history and anyone with the image can read them. For build-time secrets such as a private npm token, use BuildKit secret mounts, which expose the file only during that RUN step and leave nothing in the layer.

**Deeper explanation:**

```dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc -t api .
```

A common failure is `ARG NPM_TOKEN` followed by writing it into .npmrc: `docker history` shows the ARG value, and the .npmrc file is in a layer even if a later RUN deletes it. At runtime, inject secrets from the orchestrator: Kubernetes Secrets mounted as files or env vars, or better an external manager (Vault, AWS Secrets Manager, GCP Secret Manager) synced via External Secrets Operator or the Secrets Store CSI driver. Prefer files over env vars for high-value secrets, because env vars leak into crash dumps, `docker inspect`, child processes and error reporters. Add `.env`, `*.pem` and credential files to .dockerignore so they cannot be copied by accident, and scan images for secrets in CI.

**Follow-ups they will ask:**
- Where does the app read config in Node or Python: a single config module that validates `process.env` or `os.environ` at startup (zod or pydantic-settings) and fails fast on a missing value.
- How do you rotate a secret without a redeploy: mounted secret files update when the Secret object changes, so re-read them on change or on a signal; env vars require a restart.
- Why not Docker Swarm secrets: fine if you run Swarm, but most teams are on Kubernetes or managed container services with their own mechanisms.

**Mistakes to avoid:**
- Passing a secret as a build ARG and believing a later `rm` removes it.
- Committing .env files or copying them into the image because the local setup depended on them.

### Q. What does a Dockerfile HEALTHCHECK do, and why does Kubernetes ignore it?
**Short answer (45 seconds):** HEALTHCHECK tells the Docker daemon how to probe the container, and the result shows up as healthy or unhealthy in `docker ps` and can gate Compose `depends_on`. Kubernetes does not use it at all; the kubelet runs its own liveness, readiness and startup probes defined in the pod spec. So the HEALTHCHECK is useful for local Compose and plain Docker hosts, while the real production health contract is the HTTP endpoint behind the Kubernetes probes.

**Deeper explanation:**

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:3000/health || exit 1
```

The container must contain curl or an equivalent, which slim and distroless images may not; a tiny Node script (`node -e "fetch('http://localhost:3000/health').then(r=>process.exit(r.ok?0:1))"`) avoids installing anything. Design the endpoint carefully: a liveness-style endpoint should only confirm the process is responsive, while a readiness-style endpoint can check that the database pool and required dependencies are reachable. Mixing those up makes a database blip restart every API pod. The same `/health` and `/ready` endpoints serve Compose locally and Kubernetes probes in production, which keeps parity.

**Follow-ups they will ask:**
- Does an unhealthy status restart the container in plain Docker: no, Docker only reports the status; a restart needs an orchestrator or an external watcher.
- Should the health check call downstream services: for readiness yes within reason; for liveness no, because you would restart a healthy process because of someone else's outage.
- What about Compose: `condition: service_healthy` waits for the HEALTHCHECK to pass, which is how you order startup.

**Mistakes to avoid:**
- Assuming the Docker HEALTHCHECK is what Kubernetes uses to restart or route traffic.
- A health endpoint that does heavy work on every call and becomes its own source of load.

### Practice
- Take an existing Node.js service and rewrite its Dockerfile as a three-stage build; compare `docker image ls` sizes and `docker history` before and after, and confirm it runs as a non-root user with `docker exec api id`.
- Build a Python FastAPI image on python:3.12-slim and on python:3.12-alpine; time both builds and note which wheels compiled from source.
- Write a Compose file with your API, Postgres and Redis, with a Postgres health check gating the API; break it by removing the health condition and observe the startup race.
- Inject a fake token via `ARG`, then find it with `docker history`; redo the build with a BuildKit secret mount and show it is gone.
- Say it out loud: explain in two minutes what happens between `docker build` and a running container, covering layers, cache, the writable layer, namespaces and PID 1.

## Containers in Production

> Here interviewers check whether you have operated containers, not just built them. Weak answers stop at "push to a registry and deploy"; strong answers talk about immutable tags, scanning that actually blocks something, limits sized from measurements, stdout logging with structure, and a shutdown sequence that does not drop requests. Expect "what happens when the pod gets SIGTERM" and "why did it exit 137" as follow-ups.

### Concepts you must understand
- A registry stores images by content digest; tags are mutable pointers, so production deploys by an immutable tag (git SHA or semver) or by digest, never by `latest`.
- Scan images in CI and again on a schedule, because a clean image accumulates CVEs as its base ages; rebuild on a cadence rather than only when code changes.
- Always set CPU and memory limits; the memory limit is enforced by the kernel OOM killer (exit code 137), while the CPU limit throttles rather than kills.
- Log structured JSON lines to stdout and stderr; the runtime captures the stream and a shipper forwards it, so the application never manages log files or rotation.
- The 12-factor principles (config in the environment, stateless processes, port binding, disposability, dev/prod parity, logs as streams) are what make a service safe to scale and restart.
- Shutdown is a protocol: SIGTERM arrives, the process stops taking new work, finishes in-flight requests, closes pools and exits before the grace period ends and SIGKILL arrives.
- PID 1 has special duties (signal defaults, reaping orphaned children); Node and Python do not perform them, so use an init process such as tini or share the pod's process namespace.
- A read-only root filesystem, dropped Linux capabilities and no privilege escalation make a compromised container far less useful to an attacker.
- Everything a container needs is in the image or injected at start; nothing is downloaded or installed at runtime.

### Q. How do you tag and promote container images across environments, and why is latest dangerous in production?
**Short answer (45 seconds):** Build once per commit, tag the image with the git SHA (and a semver tag for releases), and promote the same digest through staging and production rather than rebuilding. `latest` is just a mutable pointer: two nodes can pull different images under the same tag, a rollback becomes impossible because the old tag was overwritten, and Kubernetes cannot tell that anything changed. Immutable tags or digests make deployments reproducible and auditable.

**Deeper explanation:** A typical pipeline tags `ghcr.io/acme/api:sha-3f1c2ab` and, after tests pass, adds `1.14.0`. Promotion is a retag of the same digest, not a new build:

```bash
docker buildx imagetools create -t ghcr.io/acme/api:prod ghcr.io/acme/api:sha-3f1c2ab
docker buildx imagetools inspect ghcr.io/acme/api:prod   # shows the digest
```

In the deployment manifest, reference the SHA tag or pin by digest (`image: ghcr.io/acme/api@sha256:...`), and let the pipeline or a GitOps controller update that field. Registries such as ECR offer tag immutability so a tag cannot be overwritten; turn it on for release tags. Also set `imagePullPolicy` deliberately: with a `latest` tag Kubernetes defaults to Always, so a restart can silently pull a different image. Retention policies clean untagged or old SHA images so the registry does not grow without bound.

**Follow-ups they will ask:**
- How do you know which commit is running: the SHA tag plus an exposed `/version` endpoint or a build label (`org.opencontainers.image.revision`) on the image.
- What about multi-architecture images: buildx builds a manifest list covering amd64 and arm64 under one tag, so Graviton or Apple silicon nodes pull the right variant.
- How do you roll back: point the manifest back to the previous SHA or digest, which still exists in the registry.

**Mistakes to avoid:**
- Rebuilding the image per environment so staging and production run different binaries.
- Describing `latest` as "the newest image" without noting it is mutable and breaks rollback.

### Q. How do you handle image vulnerabilities: what do you scan, when, and what actually blocks a deploy?
**Short answer (45 seconds):** Scan the image in the pipeline after it is built and before it is pushed or deployed, using Trivy, Grype, Snyk or the registry's built-in scanner. Fail on critical and high findings that have a fix available, allow documented exceptions with an expiry, and rescan what is already running on a schedule because new CVEs land daily. Keep the attack surface small with slim or distroless bases and a weekly base image rebuild.

**Deeper explanation:**

```bash
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 ghcr.io/acme/api:sha-3f1c2ab
```

Scanners inspect OS packages (dpkg, apk) and language dependencies (package-lock.json, requirements.txt, poetry.lock) against vulnerability databases. Most noise comes from the OS layer, which is why a distroless or slim base plus a multi-stage build cuts findings dramatically: no shell, no package manager, no compiler. Pair scanning with automation that bumps base image tags (Renovate or Dependabot) so fixes arrive as pull requests. Keep an `.trivyignore` or equivalent with a justification and an expiry date per CVE, reviewed in the pull request, so exceptions do not become permanent. For the running fleet, registry scanning (ECR, Artifact Registry) or a cluster scanner (Trivy Operator) reports images that were clean at build time but are vulnerable now, which is the case that teams forget.

**Follow-ups they will ask:**
- A critical CVE has no fix yet: do not block indefinitely; record it, check exploitability (is the library even loaded), and watch for the patch.
- What about secrets and misconfigurations: the same tools scan for leaked keys in layers and Dockerfile misconfigurations such as running as root.
- Where does an SBOM fit: generate one at build time so that when the next log4j-style event hits, you can query which images contain the package.

**Mistakes to avoid:**
- Scanning only on build, so a six-month-old image in production never gets re-evaluated.
- Blocking every finding including unfixable ones, which trains teams to disable the scanner.

### Q. How do you size CPU and memory limits for a Node.js API and a Python worker, and what happens when a container exceeds them?
**Short answer (45 seconds):** Measure, do not guess: load test one replica, read peak memory and CPU from `kubectl top` or Prometheus, then set the memory limit above the observed peak with headroom and align the runtime to it, for example a Node heap cap at roughly three quarters of the limit. Exceeding the memory limit gets the process killed by the kernel OOM killer with exit code 137; exceeding the CPU limit throttles the process within each scheduling period, which shows up as latency, not a crash.

**Deeper explanation:** Node runs one event loop per process, so a CPU limit of about one core per replica and horizontal scaling fits it naturally; GC and the libuv thread pool can briefly use more, so a limit well below one core causes throttling spikes. Set the heap explicitly with `NODE_OPTIONS=--max-old-space-size=384` for a 512 MiB limit, because V8 does not necessarily size its heap from the container limit and the default can exceed it, producing an OOM kill rather than a clean out-of-memory error. For Python with gunicorn or Celery, memory scales with the number of worker processes, since each is a full copy of the interpreter and loaded libraries; size the limit as per-worker footprint times workers plus headroom, and use `--max-requests` to recycle workers that leak.

```yaml
resources:
  requests: { cpu: "500m", memory: "512Mi" }
  limits:   { cpu: "1",    memory: "512Mi" }
```

**Follow-ups they will ask:**
- Why not skip CPU limits: some teams do, to avoid throttling, but then one noisy pod can degrade neighbors; requests still protect scheduling.
- How do you tell throttling from slowness: the `container_cpu_cfs_throttled_seconds_total` metric from cAdvisor rises when the quota is hit.

**Mistakes to avoid:**
- Copying `256Mi` from a template without measuring and then explaining OOM kills as "Node is leaky".
- Setting a memory request far below the limit so the node overcommits and evicts pods under pressure.

### Q. How should a containerized service log, and what does the path from stdout to a searchable log look like?
**Short answer (45 seconds):** Write one JSON object per line to stdout for normal logs and stderr for errors, include a level, timestamp, service name, request ID and trace ID, and never write files inside the container. The container runtime captures the stream to the node, a log agent (Fluent Bit, Promtail or the OpenTelemetry Collector) tails those files, enriches them with pod labels, and ships them to Loki, Elasticsearch or a vendor. Rotation and retention are the platform's job, not the app's.

**Deeper explanation:** In Node use pino, which emits JSON by default and is fast because formatting happens outside the request path; in Python use structlog or a JSON formatter on the standard logging module with `PYTHONUNBUFFERED=1` so output is not buffered until exit.

```js
const logger = require("pino")({ level: process.env.LOG_LEVEL || "info" });
app.use((req, res, next) => {
  req.log = logger.child({ requestId: req.id, traceId: req.get("traceparent") });
  next();
});
```

On Kubernetes the kubelet stores each container's stream under /var/log/pods and rotates it, and the DaemonSet agent reads from there. Keep high-cardinality values (user IDs, prompt text) in log fields, not in metric labels, and redact secrets and personal data before emission. For LLM apps, log the prompt version, model, token counts and latency per call; log full prompts and completions only to a controlled store with retention rules.

**Follow-ups they will ask:**
- Why not log to a file and mount a volume: it couples the app to the host layout, breaks with read-only filesystems, and needs rotation logic in every service.
- What happens when a pod crashes: `kubectl logs --previous` shows the last container's output, which only works because it went to stdout.

**Mistakes to avoid:**
- `console.log` with free-form strings, which cannot be filtered by field in production.
- Logging request bodies with tokens or personal data because "it is only debug level".

### Q. Which of the 12-factor principles matter most for containerized services, and where do real systems violate them?
**Short answer (45 seconds):** The ones that decide whether you can scale and restart freely: config in the environment so one image runs everywhere, stateless processes so any replica can serve any request, port binding so the container is self-contained, disposability so fast startup and graceful shutdown are expected, dev/prod parity so Compose and Kubernetes run the same image, and logs as event streams to stdout. Most violations are hidden state: in-memory sessions, local file uploads, per-instance caches and cron jobs tucked inside a web process.

**Deeper explanation:** The twelve factors are codebase, dependencies, config, backing services, build/release/run, processes, port binding, concurrency, disposability, dev/prod parity, logs and admin processes. A few map directly to interview stories. Build/release/run means the image is built once and configuration is applied at release time, which is exactly the "promote the same digest" argument. Backing services means Postgres, Redis, Kafka and an LLM provider are attached resources addressed by URL, so swapping a local Postgres for RDS is a config change. Admin processes means migrations and backfills run as one-off processes (a Kubernetes Job) from the same image, not from a developer laptop. The common violations: an Express app storing sessions in memory so sticky sessions become mandatory; Multer writing uploads to local disk that vanish on reschedule; a Python service caching embeddings in a module-level dict so every replica recomputes and answers differently; a `setInterval` cleanup task inside the API that now runs once per replica.

**Follow-ups they will ask:**
- Where does state go then: Redis for sessions and short-lived cache, object storage for files, the database for everything durable, a queue for background work.
- Does statelessness mean no caching: no, it means caches are either shared (Redis) or disposable and correct to lose.
- How do you run a scheduled task exactly once with many replicas: a CronJob, or a distributed lock (Redis `SET NX PX`) around the task.

**Mistakes to avoid:**
- Reciting all twelve names without a concrete violation you fixed.
- Treating "config in environment" as permission to put secrets in environment variables everywhere.

### Q. Walk me through the graceful shutdown of a Node.js API on Kubernetes, from SIGTERM to exit.
**Short answer (45 seconds):** When the pod is deleted, Kubernetes marks it Terminating, removes it from Service endpoints, runs the preStop hook, then sends SIGTERM to PID 1 and waits up to terminationGracePeriodSeconds (30 by default) before SIGKILL. The app must catch SIGTERM, stop accepting new connections, let in-flight requests finish, close database and Redis pools, and exit 0. A short preStop sleep covers the window where ingress and kube-proxy have not yet learned the pod is gone.

**Deeper explanation:**

```js
const server = app.listen(3000);
let shuttingDown = false;
app.get("/ready", (req, res) => res.sendStatus(shuttingDown ? 503 : 200));

process.on("SIGTERM", () => {
  shuttingDown = true;
  server.close(async () => {          // stop accepting, wait for in-flight
    await db.end();
    await redis.quit();
    process.exit(0);
  });
  server.closeIdleConnections?.();     // release idle keep-alive sockets
  setTimeout(() => process.exit(1), 20000).unref();  // hard deadline under the grace period
});
```

`server.close()` stops the listener but waits for open connections; keep-alive clients can hold sockets open indefinitely, which is why recent Node versions expose `closeIdleConnections()`. The hard timeout guarantees you exit before Kubernetes sends SIGKILL, which would otherwise look like exit code 137 in the pod status and leave pool connections dangling on the database. The pod spec side:

```yaml
terminationGracePeriodSeconds: 30
lifecycle:
  preStop:
    exec: { command: ["sh", "-c", "sleep 5"] }
```

Endpoint removal and SIGTERM are issued concurrently, so without the sleep a few requests can still arrive after the server has stopped listening and fail with connection refused.

**Follow-ups they will ask:**
- What exit codes mean what: 0 clean, 143 died on SIGTERM without a handler, 137 SIGKILL from the grace period or the OOM killer.
- What about WebSocket or SSE connections: close them explicitly with a close frame or event so clients reconnect to healthy pods.

**Mistakes to avoid:**
- Calling `process.exit()` immediately on SIGTERM, which drops in-flight requests and looks fine in tests.
- Using shell-form CMD so SIGTERM reaches `/bin/sh` rather than Node, and the pod always waits the full grace period.

### Q. How does graceful shutdown differ for a Python FastAPI service and for a queue worker such as Celery?
**Short answer (45 seconds):** For FastAPI under uvicorn or gunicorn, the server already handles SIGTERM: it stops accepting connections, waits for in-flight requests up to a graceful timeout, and then runs your lifespan shutdown code where you close pools and clients. For a worker the question is different: stop consuming new messages, finish or hand back the current task, and make sure a task interrupted mid-way is redelivered and idempotent, because the grace period may be shorter than the task.

**Deeper explanation:**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(DSN)
    yield
    await app.state.pool.close()   # runs after the server stops accepting

app = FastAPI(lifespan=lifespan)
```

With gunicorn, `--graceful-timeout` bounds how long workers may finish in-flight requests, and the Kubernetes grace period must be longer than it. Workers are harder. Celery treats SIGTERM as a warm shutdown: it stops fetching tasks and finishes the ones running; a second signal forces a cold shutdown. Combine that with `acks_late=True` so an unfinished task returns to the broker, and write tasks to be idempotent because they can run twice. For a custom asyncio consumer, register `loop.add_signal_handler(signal.SIGTERM, stop)` to set a flag that the consume loop checks, then await the in-flight task with a deadline. LLM generation jobs can take minutes, so either raise terminationGracePeriodSeconds for the worker Deployment or checkpoint progress and resume.

**Follow-ups they will ask:**
- Why not just set a very long grace period: rolling updates and node drains then take that long per pod; prefer short tasks plus redelivery.
- What does at-least-once imply here: duplicates are normal, so use an idempotency key per job in Postgres or Redis.
- How do you know shutdown works: a test that sends SIGTERM to the container under load and asserts zero failed requests and a clean exit code.

**Mistakes to avoid:**
- Assuming the framework's default handles database and HTTP client cleanup; it only drains connections.
- A worker that acks a message before processing it, so SIGTERM loses the job silently.

### Q. What is the PID 1 and zombie process problem in containers, and how do a proper init and a read-only filesystem fit into hardening?
**Short answer (45 seconds):** The first process in a container is PID 1, which Linux treats like init: signals with default actions are ignored unless a handler exists, and orphaned child processes are reparented to it and must be reaped with wait. Node and Python do not do that, so a service that spawns subprocesses can accumulate zombies and a process without a SIGTERM handler ignores shutdown. Running under tini fixes both. Hardening adds a read-only root filesystem, dropped capabilities and no privilege escalation so a compromised process cannot modify binaries or gain rights.

**Deeper explanation:** `docker run --init` injects a tini-based init automatically, but Kubernetes has no such flag, so bake it in:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["tini", "--"]
CMD ["node", "dist/server.js"]
```

tini becomes PID 1, forwards SIGTERM to your process, and reaps zombies. Alternatively set `shareProcessNamespace: true` on the pod so the pause container is PID 1 and reaps for everyone. For hardening, `readOnlyRootFilesystem: true` means the app cannot write anywhere except mounted volumes, so give it an emptyDir at /tmp and any cache directory; Python needs `PYTHONDONTWRITEBYTECODE=1` or a writable `__pycache__` location. Drop all capabilities and add back only what is needed (almost nothing for a web service), and set `allowPrivilegeEscalation: false` to block setuid binaries.

**Follow-ups they will ask:**
- How do you find zombies: `ps -eo pid,ppid,stat,cmd | grep Z` inside the container, or the `container_processes` metrics rising.
- What breaks with a read-only filesystem: libraries writing temp files, npm or pip at runtime, and frameworks writing to the working directory; fix each with a mount or config.

**Mistakes to avoid:**
- Using `CMD node server.js` in shell form and then wondering why the pod takes 30 seconds to stop.
- Enabling readOnlyRootFilesystem in production first and discovering the temp-file writes during an incident.

### Practice
- Deploy a small Express app to a local cluster (kind or minikube) with a 20 second request handler; delete the pod under load with and without a SIGTERM handler and compare failed requests and the recorded exit codes.
- Set a 256Mi memory limit on a Node pod and allocate memory in a loop; capture the OOMKilled status with `kubectl describe` and then fix it with `--max-old-space-size` and a realistic limit.
- Run `trivy image` on your current production image and on a distroless rebuild of it; count the findings per layer.
- Enable `readOnlyRootFilesystem` and `capabilities.drop: ["ALL"]` on a FastAPI pod and fix every write that fails with a mounted emptyDir.
- Say it out loud: narrate the life of a request that arrives one second after a pod is marked Terminating, and explain every mechanism that keeps it from failing.

## Kubernetes Core Objects

> Kubernetes questions for a full stack role test whether you can own the manifests for your own service: what each object is for, how traffic reaches a pod, how config and secrets arrive, how probes and resources keep the service healthy, and how a rollout actually happens. Weak answers confuse Services with Ingress or describe probes as "health checks"; strong answers draw the chain from client to container and know the defaults that bite (probe timeouts, 25 percent surge, env vars that never update).

### Concepts you must understand
- A Pod is the unit of scheduling: one or more containers sharing a network namespace (one IP, localhost between them) and volumes; you almost never create bare pods, a controller does.
- A Deployment manages ReplicaSets and a ReplicaSet keeps N identical pods alive; a rollout creates a new ReplicaSet and shifts replicas from old to new.
- A Service gives a stable virtual IP and DNS name in front of a changing set of pods selected by labels; ClusterIP is internal, NodePort opens a port on every node, LoadBalancer provisions a cloud load balancer.
- Ingress is an L7 routing rule object that does nothing until an ingress controller (ingress-nginx, Traefik, a cloud controller) implements it; the Gateway API is its more expressive successor.
- ConfigMaps hold non-secret config and Secrets hold base64-encoded sensitive data; both inject as env vars (fixed until restart) or as mounted files (updated on change).
- Readiness decides whether the pod receives traffic, liveness decides whether the container is restarted, and a startup probe suspends both until a slow application has started.
- Requests are what the scheduler reserves and limits are what the kernel enforces; together they define the QoS class and who gets evicted first under node pressure.
- The HPA changes replica count from metrics, the VPA changes requests, and rolling update parameters (maxSurge, maxUnavailable) control how many pods change at once.
- StatefulSets give stable identities and per-pod storage, DaemonSets put one pod on every node, Jobs run to completion and CronJobs schedule them.
- A PersistentVolumeClaim requests storage from a StorageClass, which dynamically provisions a PersistentVolume through a CSI driver; access modes decide whether several pods can share it.

### Q. What is a Pod, how do Deployments and ReplicaSets relate to it, and what happens when you apply a new image tag?
**Short answer (45 seconds):** A Pod is one or more containers scheduled together on a node, sharing an IP, localhost and volumes. A ReplicaSet keeps a fixed number of identical pods running from a template. A Deployment owns ReplicaSets and gives you declarative rollouts: when you change the pod template, the Deployment controller creates a new ReplicaSet with the new template hash, scales it up while scaling the old one down according to the rollout strategy, and keeps old ReplicaSets at zero replicas for rollback.

**Deeper explanation:** Containers in a pod share the network namespace, which is why a sidecar can reach the app at `localhost:3000` and why two containers in one pod cannot both listen on the same port. They also share volumes, which is how a log shipper or a model-download init container hands files to the main container.

```bash
kubectl set image deployment/api api=ghcr.io/acme/api:sha-3f1c2ab
kubectl rollout status deployment/api
kubectl get rs -l app=api        # new and old ReplicaSets, pod-template-hash labels
kubectl rollout undo deployment/api
```

The pod-template-hash label is how a ReplicaSet selects only its own pods. Deleting a pod by hand is harmless because the ReplicaSet replaces it; deleting the ReplicaSet is harmless because the Deployment recreates it. That self-healing loop, a controller comparing desired and observed state and acting on the difference, is the core idea of every Kubernetes object.

**Follow-ups they will ask:**
- Why not one container per pod always: sidecars for proxies, log shipping or secret injection need the shared namespace; unrelated services should be separate pods so they scale independently.
- What keeps a bare pod alive: nothing; if its node dies the pod is gone, which is why controllers exist.

**Mistakes to avoid:**
- Saying a Deployment "contains pods" directly and skipping the ReplicaSet, then being unable to explain `kubectl get rs` output during a rollout.
- Putting the API and its database in one pod because they "belong together".

### Q. Explain the Service types and trace a request from a browser through an Ingress to a pod.
**Short answer (45 seconds):** A Service selects pods by label and gives them a stable ClusterIP and DNS name; kube-proxy programs iptables or IPVS so traffic to that IP is spread across the ready endpoints. NodePort additionally exposes a port on every node, and LoadBalancer asks the cloud for an external load balancer in front of that. An Ingress is an L7 rule set (host and path to Service) that an ingress controller implements. The browser hits the cloud load balancer, which forwards to the ingress controller pods, which route by host and path straight to the chosen Service's pod endpoints.

**Deeper explanation:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
spec:
  ingressClassName: nginx
  tls: [{ hosts: ["api.acme.com"], secretName: api-tls }]
  rules:
  - host: api.acme.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend: { service: { name: api, port: { number: 80 } } }
```

The ingress controller itself runs as a Deployment behind a Service of type LoadBalancer, so there is typically one cloud load balancer for the whole cluster rather than one per application. Inside the cluster, `api.default.svc.cluster.local` resolves to the ClusterIP; pods in the same namespace just use `api`. A headless Service (`clusterIP: None`) returns pod IPs directly, which StatefulSets and gRPC client-side balancing rely on. Readiness is what makes this work: only pods passing their readiness probe appear in the Service's EndpointSlices, so a starting or draining pod receives nothing.

**Follow-ups they will ask:**
- Why not a LoadBalancer Service per app: cost and sprawl; Ingress or Gateway API multiplexes many hosts behind one.
- Where does TLS terminate: at the ingress controller using the referenced Secret, usually issued by cert-manager.
- What about gRPC or WebSockets: both work through ingress-nginx with the right annotations; gRPC needs HTTP/2 to the backend and balances per connection, not per request.

**Mistakes to avoid:**
- Describing Ingress as a load balancer type of Service.
- Forgetting that a Service only forwards to ready endpoints, which is the root cause of many "502 during deploy" stories.

### Q. How do ConfigMaps and Secrets reach your application, and what are the gotchas around updates and security?
**Short answer (45 seconds):** Both inject either as environment variables or as files in a mounted volume. Environment variables are read once at pod start and never change; mounted files are refreshed by the kubelet when the object changes, so a service can reload config without a restart. Secrets are only base64 encoded, so protect them with RBAC, encryption at rest and ideally a sync from an external secret manager rather than committing them to git.

**Deeper explanation:**

```yaml
containers:
- name: api
  envFrom:
  - configMapRef: { name: api-config }
  env:
  - name: DATABASE_URL
    valueFrom: { secretKeyRef: { name: api-secrets, key: DATABASE_URL } }
  volumeMounts:
  - { name: prompts, mountPath: /etc/prompts, readOnly: true }
volumes:
- name: prompts
  configMap: { name: prompt-templates }
```

Mounted ConfigMaps update eventually (kubelet sync plus cache delay, typically within a minute or two), except when mounted with subPath, which never updates. Since env vars are frozen, teams add a checksum of the ConfigMap as a pod annotation in Helm so a config change triggers a rollout, or run a controller such as Reloader. On the security side, anyone with `get secrets` in a namespace can read every secret there, so scope RBAC tightly, enable etcd encryption with a KMS provider, and use External Secrets Operator or the Secrets Store CSI driver to pull from Vault or a cloud secret manager so git only holds references. For GitOps repos, Sealed Secrets or SOPS keep encrypted values in git.

**Follow-ups they will ask:**
- How do you rotate a database password without downtime: create the new credential, update the Secret, roll the Deployment, then revoke the old one.
- Why files over env vars for secrets: env vars leak to child processes, crash reports and `kubectl describe`, and cannot be updated in place.

**Mistakes to avoid:**
- Claiming Secrets are encrypted because they look scrambled in YAML.
- Changing a ConfigMap and expecting pods that consume it as env vars to pick it up.

### Q. Explain liveness, readiness and startup probes, and configure them for a service that takes a minute to load a model before it can serve.
**Short answer (45 seconds):** Readiness answers "can this pod take traffic right now" and controls Service endpoints; liveness answers "is this process stuck" and restarts the container; startup answers "has it finished booting" and disables the other two until it passes, so a slow start is not mistaken for a hang. For a model-loading service, give the startup probe a long budget, keep liveness trivial and cheap, and let readiness reflect dependency health.

**Deeper explanation:**

```yaml
startupProbe:
  httpGet: { path: /health, port: 8000 }
  periodSeconds: 5
  failureThreshold: 36        # up to 3 minutes to load the model
livenessProbe:
  httpGet: { path: /health, port: 8000 }
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
readinessProbe:
  httpGet: { path: /ready, port: 8000 }
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

Without the startup probe you would need a large initialDelaySeconds on liveness, which also delays detecting real hangs after a restart. The liveness endpoint must do no I/O: if it checks Postgres and the database blips, every replica restarts at once and you turn a dependency slowdown into an outage. The readiness endpoint may check that the pool and required services are reachable, because taking a pod out of rotation is safe and reversible. Default timeoutSeconds is 1 second, which a busy Node event loop or a Python worker under load can miss, producing restarts that look like random crashes. Probes also feed deployments: a rollout only proceeds as new pods become ready, so a broken readiness endpoint stalls the rollout rather than breaking production.

**Follow-ups they will ask:**
- The app has no HTTP server (a queue worker): use an exec probe that checks a heartbeat file the worker touches, or a small health port.
- What does readiness failing do to a running request: nothing, existing connections continue; only new routing stops.

**Mistakes to avoid:**
- One endpoint for everything that checks the database, used as liveness.
- Setting failureThreshold 1 on liveness, so a single slow garbage collection pause restarts the pod.

### Q. How do requests and limits affect scheduling and eviction, and how would you autoscale an API with an HPA?
**Short answer (45 seconds):** Requests are what the scheduler subtracts from a node's allocatable capacity to decide placement; limits are enforced at runtime by cgroups. Their relationship sets the QoS class: Guaranteed when every container's requests equal its limits, Burstable when some requests are set, BestEffort when none are. Under memory pressure the kubelet evicts BestEffort first, then Burstable pods exceeding their requests. The HPA then scales replicas to hold an average metric at a target, typically CPU utilization as a percentage of requests, or a custom metric such as requests per second or queue depth.

**Deeper explanation:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: api }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: api }
  minReplicas: 3
  maxReplicas: 30
  metrics:
  - type: Resource
    resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } }
  behavior:
    scaleDown: { stabilizationWindowSeconds: 300 }
```

The HPA needs metrics-server for CPU and memory and an adapter (prometheus-adapter or KEDA) for custom metrics. Desired replicas is roughly current replicas times current utilization over target, rounded up, so with 60 percent as target and pods averaging 90 percent, 10 replicas become 15. For an I/O-bound Node API, CPU often does not track load well; requests per second per pod or p95 latency from Prometheus are better signals. The VPA solves a different problem: it observes usage and adjusts requests, which is useful for right-sizing, but do not let the HPA and the VPA both act on CPU for the same workload.

**Follow-ups they will ask:**
- Why set minReplicas to 3: survive one pod failure and one zone loss while a rollout is in progress.
- What stops the HPA from scaling into a cluster with no room: nothing; node autoscaling (Cluster Autoscaler or Karpenter) has to add nodes, and pods sit Pending until it does.

**Mistakes to avoid:**
- "Set CPU limits low to save money", which causes throttling and makes the HPA scale out on fake load.
- Confusing the HPA (more pods) with the Cluster Autoscaler (more nodes).

### Q. How does a rolling update work, and which parameters would you tune for a latency-sensitive API?
**Short answer (45 seconds):** The Deployment controller creates a new ReplicaSet and moves replicas over in steps bounded by maxSurge (how many extra pods may exist) and maxUnavailable (how many may be missing), both 25 percent by default. A new pod counts only after it passes readiness and minReadySeconds. If the rollout does not progress within progressDeadlineSeconds (600 by default) the Deployment reports a failed condition, but it does not roll back on its own. For a sensitive API, set maxUnavailable to 0 so capacity never drops, a modest maxSurge, and a minReadySeconds of 10 to 30 so a pod that crashes right after becoming ready stops the rollout early.

**Deeper explanation:**

```yaml
spec:
  replicas: 6
  minReadySeconds: 15
  progressDeadlineSeconds: 300
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 2, maxUnavailable: 0 }
```

With these settings the controller starts two new pods, waits for them to be ready and stable for 15 seconds, then terminates two old pods, and repeats. The old pods go through the graceful shutdown sequence, so the whole system has old and new versions serving at the same time; your API and database schema must tolerate that overlap. `kubectl rollout history deployment/api` lists revisions (old ReplicaSets kept up to revisionHistoryLimit), `kubectl rollout undo --to-revision=3` goes back, and `kubectl rollout pause` lets you hold a partially rolled fleet as a crude canary. The Recreate strategy kills everything first and is only acceptable for singletons holding a ReadWriteOnce volume. Automatic rollback on failure is not built in; Argo Rollouts or Flagger add metric-based promotion and abort.

**Follow-ups they will ask:**
- What triggers a rollout: any change to the pod template; changing replicas or labels on the Deployment itself does not.
- What does a stuck rollout look like: new pods never ready, old pods still serving, `kubectl describe deployment` shows ProgressDeadlineExceeded.

**Mistakes to avoid:**
- Believing Kubernetes rolls back automatically when the new version is broken.
- Setting maxSurge and maxUnavailable both high to "deploy faster" on a service with few replicas.

### Q. When do you reach for StatefulSets, DaemonSets, Jobs and CronJobs instead of a Deployment?
**Short answer (45 seconds):** A Deployment is for interchangeable stateless replicas. A StatefulSet is for pods that need a stable identity and their own disk, such as Kafka brokers or a Postgres primary; pods are named by ordinal, get stable DNS through a headless Service, and each gets a PersistentVolumeClaim from a template that survives rescheduling. A DaemonSet runs exactly one pod per node for node-level agents. A Job runs a task to completion with retries, and a CronJob creates Jobs on a schedule.

**Deeper explanation:** StatefulSet pods are `kafka-0`, `kafka-1`, reachable at `kafka-0.kafka.default.svc.cluster.local`; they start and stop in order unless podManagementPolicy is Parallel, and a rolling update can be partitioned to upgrade only ordinals above a number as a canary. In practice, databases on Kubernetes are run through operators (CloudNativePG, Strimzi for Kafka) built on StatefulSets, or you use a managed service. DaemonSets carry log shippers, node exporters, CNI agents and the NVIDIA device plugin, and need tolerations to land on tainted nodes.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: refresh-embeddings }
spec:
  schedule: "30 2 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 3
      ttlSecondsAfterFinished: 86400
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: job
            image: ghcr.io/acme/worker:sha-3f1c2ab
            args: ["python", "-m", "jobs.refresh_embeddings"]
```

Job knobs: `completions` and `parallelism` for fan-out, `backoffLimit` (default 6) for retries, `activeDeadlineSeconds` as a hard timeout, and Indexed completion mode to shard a batch across pods. Database migrations fit a Job run before the Deployment rolls, often as a Helm pre-upgrade hook.

**Follow-ups they will ask:**
- Why Forbid on the CronJob: if last night's run is still going, do not start a second one on the same data.
- Is a Job idempotent by default: no, retries re-run your code, so design the task to be safe to repeat.

**Mistakes to avoid:**
- Running Postgres as a Deployment with a PVC and two replicas, then hitting a multi-attach error.
- Using a Deployment with a `while true; sleep` loop as a scheduler instead of a CronJob.

### Q. How does persistent storage work in Kubernetes, and what does it imply for running something like Postgres or sharing model files?
**Short answer (45 seconds):** A pod asks for storage through a PersistentVolumeClaim; a StorageClass names the CSI driver and parameters, and dynamic provisioning creates a PersistentVolume (a cloud disk) bound to that claim. Access modes decide sharing: block disks are ReadWriteOnce, attached to one node at a time, so a Deployment with several replicas cannot share one. ReadWriteMany needs a file system such as EFS, Filestore or NFS. For Postgres that means a StatefulSet (or operator) with one claim per pod; for model weights it means either a read-only shared volume, object storage pulled at startup, or baking them into the image.

**Deeper explanation:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: fast }
provisioner: ebs.csi.aws.com
parameters: { type: gp3 }
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

WaitForFirstConsumer matters on multi-zone clusters: a disk is zonal, so the volume must be created in the zone where the scheduler places the pod, otherwise the pod stays Pending forever with a volume node affinity conflict. reclaimPolicy Retain keeps the disk when the claim is deleted, which is the safe choice for databases; Delete is the default for many classes. Expansion grows the disk and filesystem online when allowed. Snapshots exist through the VolumeSnapshot API, but they are not a backup strategy by themselves; logical backups and point-in-time recovery still need the database's own tooling.

**Follow-ups they will ask:**
- Why does my second replica say Multi-Attach error: an RWO disk is still attached to the node running the first pod.
- How do pods on GPU nodes get a 20 GB model quickly: pre-populated ReadOnlyMany volume or a node-local cache, since pulling from object storage on every cold start dominates startup time.

**Mistakes to avoid:**
- Calling a PVC "the disk"; it is the request, the PV is the resource, and the StorageClass is the recipe.
- Treating a PersistentVolume as durable in the sense of backed up.

### Practice
- On kind or minikube, deploy an Express API with three replicas, a ClusterIP Service and an ingress-nginx Ingress; watch `kubectl get endpointslices` while you toggle the readiness endpoint on one pod.
- Set misleading resources (requests 50m, limits 2) and load test; observe the HPA behavior, then fix requests from measured usage and compare.
- Roll out a deliberately broken image with maxUnavailable 0 and minReadySeconds 15; confirm no capacity loss, read the ProgressDeadlineExceeded condition, and roll back.
- Create a CronJob that runs a Python script against Postgres with concurrencyPolicy Forbid, then make the script sleep past the next schedule and observe what happens.
- Say it out loud: describe the full chain from a user's browser to a container for your service, naming every Kubernetes object involved and what decides whether a pod is in the path.

## Kubernetes Operations & Debugging

> This is where interviewers separate people who have deployed to Kubernetes from people who have read about it. They describe a broken pod and watch you debug out loud. A weak answer is "I would check the logs"; a strong answer names the exact commands in order, reads the exit code and events, forms a hypothesis and verifies it. The same applies to the surrounding tooling: Helm or Kustomize, RBAC, network policy, GPUs for inference, event-driven autoscaling and upgrades.

### Concepts you must understand
- The debugging loop is get, describe, logs, events, exec: describe shows the scheduler's and kubelet's view, logs show the application's view, and events show what controllers did and why.
- CrashLoopBackOff means the container keeps exiting and the kubelet is backing off restarts (doubling up to five minutes); the cause is in `kubectl logs --previous` and the exit code, not in the status.
- OOMKilled is exit code 137 with reason OOMKilled in the last state; Pending means the scheduler could not place the pod; ImagePullBackOff means the kubelet cannot fetch the image.
- Events expire (one hour by default), so capture them early in an incident.
- Helm templates manifests from values and tracks releases for upgrade and rollback; Kustomize patches plain YAML through overlays with no template language.
- RBAC binds Roles or ClusterRoles to users, groups and ServiceAccounts; every pod runs under a ServiceAccount whose token is a credential to the API server.
- NetworkPolicies are allow-lists enforced by the CNI; with none defined, every pod can talk to every pod and to the internet.
- A service mesh moves retries, timeouts, mTLS and traffic splitting into proxies beside each pod, at a cost in latency, resources and operational complexity.
- GPUs are extended resources advertised by a device plugin, requested as whole units and scheduled onto tainted node pools that autoscale slowly.
- KEDA scales on event sources such as queue depth and can scale to zero; cluster upgrades go control plane first then node pools, with PodDisruptionBudgets protecting availability during drains.

### Q. A pod is in CrashLoopBackOff. Walk me through exactly how you debug it.
**Short answer (45 seconds):** CrashLoopBackOff only says the container keeps exiting, so I go for the cause: `kubectl describe pod` for the last state, exit code and events, then `kubectl logs --previous` for the output of the crashed container, since the current one may have nothing yet. The exit code narrows it fast: 1 is an application error, 137 is a kill from OOM or a failed liveness probe, 143 is an unhandled SIGTERM, 139 a segfault, 127 a command not found. Then I reproduce with the same image and environment, fix, and confirm the restart counter stops climbing.

**Deeper explanation:**

```bash
kubectl get pod api-7c9f -n prod -o wide
kubectl describe pod api-7c9f -n prod | sed -n '/Last State/,/Events/p'
kubectl logs api-7c9f -n prod --previous --tail=200
kubectl get events -n prod --sort-by=.lastTimestamp | grep api-7c9f
```

Typical causes, in rough order of frequency: a missing or malformed environment variable or secret so the app throws at startup; a database or queue that is unreachable, with the app treating it as fatal; a liveness probe that fails because the port or path is wrong, so the kubelet kills a healthy process every 30 seconds; the container command finishing successfully (exit 0) in a Deployment that restarts it forever, which shows as Completed then CrashLoopBackOff; and a wrong CMD after an image refactor.

**Follow-ups they will ask:**
- Logs are empty: the process died before logging, which points at the entrypoint, a missing file, or Python buffering; check events and exit code.
- It only crashes in production: compare `kubectl get pod -o yaml` between environments, especially env, resources and probes.
- It crashes every 30 seconds exactly: that is the liveness probe period; read the probe events.

**Mistakes to avoid:**
- Reading logs of the current container (empty) and concluding there is nothing to see.
- Raising the memory limit or deleting the pod as a reflex without reading the exit code.

### Q. How do you diagnose OOMKilled, Pending and ImagePullBackOff, and what are the usual causes of each?
**Short answer (45 seconds):** All three start with `kubectl describe pod`. OOMKilled shows as Last State Terminated with reason OOMKilled and exit code 137: the container exceeded its memory limit and the kernel killed it, so I compare `kubectl top pod` and the memory metric history against the limit and look for a leak, oversized runtime defaults or too many worker processes. Pending shows a FailedScheduling event whose message says why: insufficient CPU or memory, a taint without a toleration, an unmatched node selector or affinity, or an unbound volume. ImagePullBackOff shows an ErrImagePull event with the registry's message: wrong tag, missing imagePullSecret, rate limit or no manifest for the node's architecture.

**Deeper explanation:**

```bash
kubectl describe pod api-7c9f | grep -A3 -E "Last State|Reason|FailedScheduling|Failed to pull"
kubectl top pod api-7c9f --containers
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
kubectl get pvc -n prod
```

For OOM, distinguish a steady climb (leak, unbounded in-memory cache, event listeners) from a spike (large request body, big LLM response buffered, a batch loaded into memory). Node fixes: set `--max-old-space-size` below the limit and stream large payloads. Python fixes: fewer gunicorn workers or `--max-requests`. For Pending, `kubectl describe` is explicit: "0/6 nodes are available: 3 Insufficient memory, 3 node(s) had untolerated taint". For image pulls, `kubectl get events` shows the exact registry response; a 401 or 403 means credentials, a toomanyrequests message means Docker Hub rate limits, and "no match for platform" means an amd64-only image on an arm64 node.

**Follow-ups they will ask:**
- Pending with plenty of capacity: ResourceQuota on the namespace, or the pod needs a GPU or a nodeSelector nobody set.
- ImagePullBackOff only on new nodes: the imagePullSecret or the node's registry credentials (IAM role for ECR, Workload Identity for Artifact Registry) are missing on that node pool.

**Mistakes to avoid:**
- Confusing Evicted (node pressure, pod removed) with OOMKilled (container exceeded its own limit).
- Retagging the image instead of fixing registry authentication.

### Q. Describe your day-to-day kubectl workflow when a service misbehaves, including when you use exec, port-forward and debug containers.
**Short answer (45 seconds):** Set the context and namespace, then go wide to narrow: `kubectl get pods -o wide` to see restarts, age and node; `describe` on the suspicious pod; `logs -f` across the Deployment with a label selector; `get events` sorted by time; `top pods` for resource pressure; `rollout history` to see whether a deploy correlates. Then I get inside: `exec` into a running container for a quick check, `port-forward` to call the service or its database from my laptop, and `kubectl debug` to attach a toolbox container when the image has no shell.

**Deeper explanation:**

```bash
kubectl config use-context prod && kubectl config set-context --current --namespace=payments
kubectl get pods -l app=api -o wide
kubectl logs -l app=api -f --max-log-requests=10 --since=15m
kubectl rollout history deployment/api
kubectl exec -it api-7c9f -c api -- sh -c 'env | sort; wget -qO- localhost:3000/ready'
kubectl port-forward svc/api 3000:80
kubectl debug -it api-7c9f --image=nicolaka/netshoot --target=api
```

Distroless and slim images often have no shell, which is correct for security and annoying for debugging; `kubectl debug` with `--target` injects an ephemeral container sharing the target's process namespace, so you can inspect its processes, network connections and mounted files without changing the image. `kubectl debug node/NODE_NAME -it --image=ubuntu` gives a shell on the node for kubelet and runtime issues.

**Follow-ups they will ask:**
- How do you avoid running kubectl commands against production by accident: separate kubeconfig contexts, a prompt that shows the context, and read-only RBAC for humans with break-glass for writes.
- The pod runs as non-root with a read-only filesystem and you need to capture a heap dump: write it to an emptyDir mount or stream it through `kubectl exec` to your laptop.

**Mistakes to avoid:**
- Fixing things with `kubectl edit` in production and leaving git out of date, so the next deploy reverts the fix.
- Not knowing `--previous` and `--since`, and scrolling through hours of logs.

### Q. Compare Helm and Kustomize, and describe how you would structure deployment configuration for a service across dev, staging and production.
**Short answer (45 seconds):** Helm is a package manager: a chart is a set of Go templates rendered from values, and Helm records each install as a release you can upgrade, diff and roll back; it is the standard for third-party software and works well for your own services once a chart exists. Kustomize is template-free: a base of plain YAML plus overlays that patch it per environment, built into kubectl. I use Helm for anything with many knobs or shared across teams, Kustomize overlays for simple per-environment tweaks on top of plain manifests, and either way keep one artifact per service with environment-specific values files reviewed in git.

**Deeper explanation:**

```bash
helm upgrade --install api ./charts/api -n prod \
  -f charts/api/values.yaml -f env/prod/values.yaml \
  --set image.tag=sha-3f1c2ab --atomic --wait --timeout 5m
helm history api -n prod && helm rollback api 12 -n prod
```

```text
deploy/
  base/            deployment.yaml service.yaml hpa.yaml kustomization.yaml
  overlays/dev/    kustomization.yaml (replicas 1, small resources)
  overlays/prod/   kustomization.yaml (replicas 6, PDB, prod ConfigMap)
```

`--atomic` rolls back automatically if pods do not become ready in time, which plain Deployments never do. Helm hooks (`helm.sh/hook: pre-upgrade`) run migration Jobs before the rollout. Kustomize keeps YAML honest and diffs well, but cannot express conditionals or loops, so complex services drift toward Helm. Whatever the tool, the rules are: the image tag is the only thing CI changes per deploy, values per environment live in git, and nobody runs `helm upgrade` from a laptop against production.

**Follow-ups they will ask:**
- How do you test a chart: `helm lint`, `helm template` with each values file, and a kind cluster in CI that installs and runs smoke tests.
- Helm or Kustomize for a 20-microservice platform: a shared library chart with a thin values file per service keeps them consistent; Kustomize per service tends to drift.

**Mistakes to avoid:**
- Describing Helm as "just templating" and missing releases, hooks and rollback.
- One giant values.yaml with every environment's settings and `if` blocks, which nobody can review.

### Q. How does Kubernetes RBAC work, and how would you give a CI pipeline the minimum rights to deploy one service?
**Short answer (45 seconds):** RBAC has two halves: Roles and ClusterRoles list allowed verbs on resources, and RoleBindings and ClusterRoleBindings attach them to subjects, which are users, groups or ServiceAccounts. There is no deny rule; anything not granted is forbidden. For a deploy pipeline I create a ServiceAccount in the service's namespace, a Role allowing get, list, watch, patch and update on deployments, services, configmaps and the related objects it manages, bind them, and let CI authenticate as that identity through short-lived cloud credentials rather than a long-lived token.

**Deeper explanation:**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: api-deployer, namespace: payments }
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "patch", "update"]
- apiGroups: [""]
  resources: ["services", "configmaps"]
  verbs: ["get", "list", "watch", "patch", "update"]
- apiGroups: [""]
  resources: ["pods", "events"]
  verbs: ["get", "list", "watch"]
```

Bind it with a RoleBinding to `ServiceAccount payments/ci-deployer` and verify with `kubectl auth can-i delete secrets --as=system:serviceaccount:payments:ci-deployer -n payments`, which should say no. Pods also carry identity: every pod mounts its ServiceAccount token unless `automountServiceAccountToken: false`, so a web app that never calls the API server should disable it, and a controller that does should get only the verbs it uses. On managed clusters, map the CI identity through the cloud (an IAM role assumed via OIDC on EKS, Workload Identity Federation on GKE) so there is no static kubeconfig secret to leak.

**Follow-ups they will ask:**
- Role or ClusterRole for a namespaced deployer: a Role; a ClusterRole is for cluster-scoped resources or for reuse across namespaces via RoleBindings.
- How do you audit who can do what: `kubectl auth can-i --list --as=...`, plus tools such as rbac-lookup or kubectl-who-can.

**Mistakes to avoid:**
- Granting `*` verbs on `*` resources to CI because a chart needed one extra permission.
- Forgetting that `create pods` plus `exec` effectively equals node access, since a pod can mount host paths unless admission policy prevents it.

### Q. How do you control pod-to-pod traffic: what do NetworkPolicies give you, and when does a service mesh make sense on top?
**Short answer (45 seconds):** By default every pod can reach every other pod and the internet. NetworkPolicies are L3 and L4 allow-lists, selected by pod and namespace labels, enforced by the CNI plugin; the standard pattern is default deny per namespace, then explicit allows for DNS, the ingress controller, and each dependency. A service mesh works at L7 with a proxy beside every pod and adds mutual TLS with identity, retries, timeouts, per-route metrics and traffic splitting; it pays off across many services and rarely for a handful.

**Deeper explanation:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: payments }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: api-allow, namespace: payments }
spec:
  podSelector: { matchLabels: { app: api } }
  ingress:
  - from:
    - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: ingress-nginx } }
    ports: [{ port: 3000 }]
  egress:
  - to: [{ namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } } }]
    ports: [{ port: 53, protocol: UDP }, { port: 53, protocol: TCP }]
```

The first thing default deny breaks is DNS, hence the kube-system rule. Egress to external hosts such as an LLM provider needs ipBlock rules or a CNI with FQDN policies (Cilium, Calico). A mesh (Istio, Linkerd) answers different questions: who is calling whom with cryptographic identity, what is the p99 between these two services, can I send 5 percent of traffic to v2. The costs are an extra proxy hop per request, memory and CPU per pod, sidecars that keep Jobs from completing, and one more control plane to upgrade.

**Follow-ups they will ask:**
- How do you roll out default deny without an outage: audit mode or flow logs first (Cilium Hubble, Calico flow logs), write allows from observed traffic, then enforce namespace by namespace.
- Does a mesh replace NetworkPolicies: no, they are complementary; policies cut the network, the mesh authenticates and shapes what remains.

**Mistakes to avoid:**
- Writing a policy and assuming it is enforced without testing from a pod that should be blocked.

### Q. How do you run GPU inference workloads on Kubernetes: node pools, scheduling, autoscaling and keeping the cluster upgradeable?
**Short answer (45 seconds):** GPU nodes live in their own node pool, tainted so ordinary pods stay off them, and the NVIDIA device plugin advertises `nvidia.com/gpu` as a schedulable resource. An inference pod requests a whole GPU in its limits, tolerates the taint, and selects the right accelerator with a nodeSelector. The pool autoscales from zero but slowly, because a node must boot, install drivers and pull a multi-gigabyte image, so you keep a warm minimum and use startup probes for model load. Upgrades follow the same rules as other pools, plus testing the driver and CUDA combination first.

**Deeper explanation:**

```yaml
spec:
  tolerations:
  - { key: nvidia.com/gpu, operator: Exists, effect: NoSchedule }
  nodeSelector: { cloud.google.com/gke-accelerator: nvidia-l4 }
  containers:
  - name: vllm
    image: ghcr.io/acme/llm-server:sha-3f1c2ab
    resources:
      limits: { nvidia.com/gpu: 1, memory: 24Gi }
```

GPU requests are integers and must equal limits; sharing requires time-slicing (no memory isolation) or MIG partitions on supported cards. The NVIDIA GPU Operator installs the driver, container toolkit, device plugin and the DCGM metrics exporter. Autoscaling: the Cluster Autoscaler or Karpenter adds GPU nodes when a pod is Pending for `nvidia.com/gpu`, but a cold node can take many minutes to serve, so keep minimum replicas during business hours, pre-pull images with a DaemonSet, and store model weights on a fast shared volume or node cache rather than downloading on every start. For upgrades, cluster-wide: control plane first, then node pools one at a time with surge, `kubectl drain` honoring PDBs, and deprecated API checks (tools such as pluto) before bumping the version; for GPU pools, also verify the new node image's driver against your CUDA base image in staging.

**Follow-ups they will ask:**
- Why not request half a GPU: not supported without time-slicing or MIG; design for one model server per GPU and scale pods instead.
- How do you keep a PDB from blocking a drain forever: never set minAvailable equal to replicas; use maxUnavailable 1 and at least two replicas.

**Mistakes to avoid:**
- Scheduling CPU-only workloads onto expensive GPU nodes by forgetting the taint.

### Q. How does KEDA differ from the HPA, and how would you use it to scale an LLM job queue?
**Short answer (45 seconds):** The HPA scales on metrics that describe the pods themselves, such as CPU, and cannot go to zero. KEDA scales on external event sources: queue length in Redis, RabbitMQ or SQS, Kafka consumer lag, a Prometheus query, or a cron window, and it can scale a Deployment to zero and back. Under the hood KEDA creates and feeds an HPA for the 1 to N range and handles the 0 to 1 step itself. For an LLM job queue I scale workers on queue depth per worker, with a floor in working hours and a cap from the provider's rate limit.

**Deeper explanation:**

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: llm-worker }
spec:
  scaleTargetRef: { name: llm-worker }
  minReplicaCount: 0
  maxReplicaCount: 20
  cooldownPeriod: 300
  triggers:
  - type: redis
    metadata: { address: redis.payments.svc:6379, listName: llm:jobs, listLength: "5" }
  - type: cron
    metadata: { timezone: Asia/Dubai, start: "0 8 * * *", end: "0 20 * * *", desiredReplicas: "2" }
```

listLength 5 means one worker per five queued jobs. The cron trigger keeps two warm workers in the day so the first user request does not pay a cold start; at night the queue trigger alone decides and an empty queue scales to zero after the cooldown. Cap maxReplicaCount at the real bottleneck: beyond the provider's requests per minute, more workers only create 429s. KEDA's ScaledJob variant creates one Job per batch of messages, which suits long-running generations because each job finishes instead of being interrupted by a scale-down.

**Follow-ups they will ask:**
- Can KEDA scale an HTTP API to zero: with the KEDA HTTP add-on, which holds requests while the first pod starts; for latency-sensitive APIs that cold start is usually unacceptable.
- What happens to in-flight work when scaling down: Kubernetes picks pods to terminate and they get SIGTERM, so the worker's graceful shutdown and at-least-once redelivery do the rest.

**Mistakes to avoid:**
- Scaling on CPU for an I/O-bound worker that spends its time waiting on the LLM API.

### Practice
- Break a Deployment five different ways (wrong env var, bad liveness path, exit-0 command, memory limit too low, private image without a pull secret) and write down the exact describe and logs output that identifies each.
- Install ingress-nginx and a default-deny NetworkPolicy in a namespace on kind with a CNI that enforces policies (Calico or Cilium); add allows until the app works and keep the list.
- Convert a plain manifest set into a Helm chart with dev and prod values, then into a Kustomize base with two overlays; render both and diff the outputs.
- Install KEDA and scale a Python worker on Redis list length; push 100 jobs and graph replicas over time.
- Say it out loud: an interviewer says "the pod is in CrashLoopBackOff" and nothing else; speak your first five commands and what each would tell you.

## CI/CD Pipelines

> Interviewers want to see that you can own the pipeline for your service, not just push to it. They ask you to sketch the stages, then probe the hard parts: why the build is slow, what happens with flaky tests, how production deploys are gated, how secrets stay safe from a malicious pull request, and, for AI roles, how a prompt change is tested before it ships. A weak answer lists tools; a strong answer explains the graph of jobs, the artifact that flows through it, and the gates that stop a bad change.

### Concepts you must understand
- A pipeline is a directed graph of jobs triggered by events (push, pull request, tag, schedule, manual); each job runs on a fresh runner, so everything it needs must be declared, restored from cache or passed as an artifact.
- The canonical stages are lint and unit test, build the image once, scan it, push it, deploy to a lower environment, run integration tests, then promote the same artifact to production.
- Caching restores dependency directories keyed on the lockfile hash; artifacts carry build outputs and reports between jobs; the deployable unit is the immutable image in the registry, not either of those.
- Matrix builds fan one job out over versions or platforms; test sharding splits a suite across runners to cut wall-clock time.
- A flaky test is a reliability bug in the test suite; quarantine it, fix the root cause, and never normalize blanket retries.
- Environments add protection rules (required reviewers, wait timers, branch restrictions) and scoped secrets, which is how a manual production approval is implemented.
- CI secrets are masked in logs but readable by any step in the job; prefer OIDC federation to cloud providers over long-lived keys, and never run untrusted pull request code with secrets available.
- Trunk-based development keeps branches short-lived and main always releasable, relying on feature flags and fast CI; GitFlow suits versioned releases with long support windows.
- Monorepo pipelines compute what changed (path filters, affected graphs) so a change in one package does not rebuild and test everything.
- An LLM app pipeline adds eval gates: deterministic tests with recorded model responses on every pull request, and an evaluation suite with thresholds against a golden dataset before prompt or model changes ship.

### Q. Walk me through a GitHub Actions workflow for a Node.js API, from push to an image in the registry.
**Short answer (45 seconds):** The workflow file in `.github/workflows` declares triggers, then jobs. The test job checks out code, sets up Node with npm caching keyed on the lockfile, runs `npm ci`, lint and tests against a Postgres service container. The build job depends on it, logs in to the registry with the workflow's own token, builds with Buildx using the Actions layer cache, tags with the commit SHA and pushes. Permissions are minimal, and a concurrency group cancels superseded runs on the same branch.

**Deeper explanation:**

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request:
permissions: { contents: read }
concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: test }
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci && npm run lint && npm test
        env: { DATABASE_URL: postgres://postgres:test@localhost:5432/postgres }
  build:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

Each job is a fresh virtual machine, which is why `needs` plus caches and artifacts are the only ways to share state. The top-level `permissions: contents: read` turns the automatic token read-only and jobs widen it only where needed. GitLab CI has the same shape with `stages`, `rules` and `needs`.

**Follow-ups they will ask:**
- Why pin actions by version or SHA: a tag such as `@v4` is mutable; a commit SHA pin protects against a compromised action.
- How do you reuse this across 20 services: a reusable workflow (`workflow_call`) or a composite action with inputs.

**Mistakes to avoid:**
- Building the image before tests pass and pushing it anyway, so the registry fills with broken candidates.

### Q. What stages should a production pipeline have, and why do you insist on building the artifact once and promoting it?
**Short answer (45 seconds):** Fast feedback first: lint, type check and unit tests in parallel. Then build the container image once, tagged with the commit SHA, scan it, and push it. Deploy that exact digest to a staging environment and run integration, contract and smoke tests against it. Then promote the same digest to production behind an approval gate, and verify with post-deploy checks. Building once means what you tested is what you run; rebuilding per environment lets dependency drift, base image updates or a different build flag change the binary between staging and production.

**Deeper explanation:**

```text
PR:    lint+types ─┐
       unit tests ─┼─> build image (sha) ─> scan ─> push ─> deploy preview (optional)
       sec checks ─┘
main:  same ─> push ─> deploy staging ─> integration + e2e + smoke ─> [approval] ─> deploy prod ─> verify
```

Keep the first stage under about five minutes or developers stop waiting for it. The scan stage covers dependencies, the image and secrets. The deploy stage should not contain logic beyond "set this image on this environment", so the same step promotes to production. Post-deploy verification means hitting a version endpoint, checking error rate and latency for a few minutes, and failing the job (triggering rollback) if they regress. Database migrations run as their own step before the application rollout, from the same image, so schema and code are versioned together.

**Follow-ups they will ask:**
- How do you know which commit is in production: the SHA tag on the image, surfaced through a version endpoint and the deployment annotation.
- What runs on a pull request versus on main: PRs run everything up to build and maybe a preview deploy; only main (or tags) pushes and deploys.

**Mistakes to avoid:**
- `npm install` in the Dockerfile at deploy time, so each environment resolves dependencies independently.
- A pipeline where the production job runs a different script than staging "because production has extra steps".

### Q. The pipeline takes 40 minutes. How do you make it fast, and what are the trade-offs of caching, matrices and test sharding?
**Short answer (45 seconds):** Measure first: which jobs dominate and what inside them. Then apply in order: restore dependency caches keyed on the lockfile, cache Docker layers to a registry or the Actions cache, run independent jobs in parallel instead of sequential stages, shard the slow test suites across runners, and only build what changed. Matrix builds are for coverage across versions, not speed. The trade-offs are cache correctness (a stale cache that hides a broken install), the cost of more parallel runners, and the complexity of merging sharded results.

**Deeper explanation:**

```yaml
strategy:
  fail-fast: false
  matrix: { shard: [1, 2, 3, 4] }
steps:
  - uses: actions/setup-node@v4
    with: { node-version: 20, cache: npm }
  - run: npm ci
  - run: npx jest --shard=${{ matrix.shard }}/4 --ci --reporters=default --reporters=jest-junit
  - uses: actions/upload-artifact@v4
    with: { name: junit-${{ matrix.shard }}, path: junit.xml }
```

Jest, Vitest and Playwright accept `--shard`; pytest uses `pytest-xdist -n auto` within a runner and plugins such as pytest-split to balance shards by recorded durations. Dependency caches are keyed on `hashFiles('**/package-lock.json')`; a `restore-keys` prefix gives a partial hit. Docker caching matters most: a cold multi-stage build of a Node image can take minutes and a warm one seconds, so export the layer cache (`cache-to: type=gha,mode=max` or a registry cache) and keep the Dockerfile cache-friendly. Watch for the hidden costs: a cache hit on a corrupted node_modules, a shard that runs the slow tests every time, and runner minutes multiplying with each matrix entry.

**Follow-ups they will ask:**
- Cache hit but tests fail with a missing module: the cache key did not include every input; include lockfile and Node version, and prefer caching the package manager's store over node_modules.
- How do you balance shards: record test durations and split by time, not by file count.

**Mistakes to avoid:**
- Treating a matrix over Node 18, 20 and 22 as a speed-up; it triples the work.
- Caching the built image itself in the Actions cache instead of pushing to a registry.

### Q. How do you deal with flaky tests in CI?
**Short answer (45 seconds):** Treat flakiness as a bug with an owner. Detect it by rerunning failed tests once and recording when the rerun passes; anything that passes on retry is flaky, gets tagged and moved to a quarantine suite that does not block merges, with a ticket and a time limit. Then fix the root cause, which is almost always shared state, timing, or a real dependency: order-dependent tests, a shared database, real clocks, unawaited promises, network calls or port collisions. Blanket retries hide real races in production code.

**Deeper explanation:** Mechanically, Playwright has `retries` in its config, pytest has `pytest-rerunfailures` with `--reruns 1`, and Jest offers `jest.retryTimes`. Use them as a detector, not a cure: report retried tests to a dashboard and fail the build if the flake rate for a test exceeds a threshold over a week. Common fixes by category: isolate database state by running each test in a transaction that is rolled back, or spin a fresh container per worker with Testcontainers; replace real time with fake timers (`jest.useFakeTimers`, `freezegun`) and never assert on `Date.now()` ordering; await every promise and avoid `setTimeout` based waits in favor of waiting for a condition; pick random free ports; seed random generators; mock external HTTP with nock, MSW or `responses`.

```python
@pytest.mark.flaky(reruns=1)      # temporary, with a ticket number in a comment
def test_worker_drains_queue(redis):
    ...
```

**Follow-ups they will ask:**
- A test is flaky only on CI: smaller CPU and slower disk expose races; run it locally under `stress` or with CPU limits to reproduce.
- When is a retry legitimate: for tests that depend on genuinely unreliable external systems, with the retry explicit, counted and limited.

**Mistakes to avoid:**
- "We just rerun the pipeline", which trains the team to ignore red builds.
- Deleting flaky tests instead of fixing them, losing coverage for exactly the concurrency paths that fail in production.

### Q. How do environments, manual approvals and secrets work in GitHub Actions, and how do you keep secrets safe from a malicious pull request?
**Short answer (45 seconds):** An environment is a named target such as staging or production with its own secrets, variables and protection rules: required reviewers, a wait timer and a list of branches allowed to deploy. A job that declares `environment: production` pauses until an approver clicks, which is the manual gate. Secrets are encrypted at rest, injected only into jobs that reference them and masked in logs, but any step in that job can read them. Pull requests from forks do not receive secrets on the `pull_request` event, and the dangerous case is `pull_request_target`, which runs with secrets in the base repository's context; never check out and execute the PR's code there.

**Deeper explanation:**

```yaml
deploy-prod:
  needs: deploy-staging
  runs-on: ubuntu-latest
  environment: { name: production, url: https://api.acme.com }
  permissions: { id-token: write, contents: read }
  steps:
    - uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789012:role/gha-api-prod-deploy
        aws-region: me-central-1
    - run: ./deploy.sh ghcr.io/acme/api:sha-${{ github.sha }}
```

The job gets no static AWS key: it requests an OIDC token from GitHub and exchanges it for short-lived credentials, and the IAM role's trust policy only accepts tokens whose subject claim names this repository and the production environment. That removes the biggest secret from the pipeline entirely. For remaining secrets, scope them to the environment so a staging job cannot read production values, and keep `permissions` minimal so a compromised dependency in a test step cannot push code or packages.

**Follow-ups they will ask:**
- Who should approve production: someone other than the author, with the diff and the staging results visible; the environment's reviewers list enforces it.
- How do you handle a dependency's postinstall script stealing a token: minimal permissions, `npm ci --ignore-scripts` where possible, and OIDC so there is no long-lived token to steal.

**Mistakes to avoid:**
- Storing a cloud admin key as a repository secret available to every workflow.
- Using `pull_request_target` with `actions/checkout` of the PR head to "get the secrets working for forks".

### Q. Trunk-based development or GitFlow: which would you choose for a SaaS team, and why?
**Short answer (45 seconds):** Trunk-based for a SaaS product deployed continuously: everyone merges small changes to main daily through short-lived branches and pull requests, main is always releasable, incomplete work hides behind feature flags, and releases are just deploys of a commit. GitFlow, with long-lived develop, release and hotfix branches, fits software shipped as versions that must be supported in parallel, such as mobile apps or on-premises installs. Long-lived branches create integration pain, duplicated hotfixes and stale tests, which is the opposite of what a fast pipeline needs.

**Deeper explanation:** Trunk-based development only works with supporting practices, and interviewers want to hear them: pull requests small enough to review in minutes, a required green CI check and review before merge, squash or rebase merges to keep history linear, a merge queue when many engineers land changes so main is tested with the actual combination, feature flags so a half-built feature can merge dark, and a fast rollback path. Release branches are still allowed when needed: cut `release/2026.10` from main for a regulated release window, cherry-pick fixes into it, and never develop on it. GitFlow's cost shows up as a develop branch that diverges from main for weeks, release branches where "stabilization" means weeks of merge conflicts, and hotfixes applied twice.

```text
trunk:   main ──o──o──o──o──o──o──>  (every o deployable; flags hide unfinished work)
                 \_pr_/ \_pr_/
gitflow: develop ──o──o──o──────o──>
         release/1.4  \──o──o──/   hotfix/1.3.1 off main, merged twice
```

**Follow-ups they will ask:**
- How do you keep main green with 30 engineers: merge queue, fast required checks, flaky tests quarantined, and ownership via CODEOWNERS.
- How do you handle a feature that takes a month: break it into merges behind a flag, branch by abstraction for refactors, no month-long branch.

**Mistakes to avoid:**
- Defending GitFlow with "it is safer" without noting that long-lived branches delay integration and testing.
- Claiming trunk-based development means pushing directly to main without review.

### Q. How would you design CI for a monorepo with a React frontend, a Node API and a Python worker?
**Short answer (45 seconds):** One pipeline that computes what changed and runs only the relevant jobs: path filters or a dependency graph decide whether the frontend, API, worker or a shared package is affected, each project has its own test and build job with its own cache, and shared workflows keep the jobs consistent. Every project ships its own image tagged with the same commit SHA, so a release is "this SHA across these services". Shared code changes fan out to every dependent, which is where naive path filters fail and graph-aware tools earn their keep.

**Deeper explanation:**

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs: { api: ${{ steps.f.outputs.api }}, worker: ${{ steps.f.outputs.worker }} }
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: f
        with:
          filters: |
            api: ['apps/api/**', 'packages/shared/**', 'package-lock.json']
            worker: ['services/worker/**', 'requirements*.txt']
  api:
    needs: changes
    if: needs.changes.outputs.api == 'true'
    uses: ./.github/workflows/node-service.yml
    with: { path: apps/api }
```

For the JavaScript side, Nx or Turborepo compute the affected graph from imports (`nx affected -t test`) and add a remote cache so unchanged packages are not retested anywhere. Python has fewer options: Pants or Bazel if you are willing, or path filters with explicit dependency lists. Keep Docker build contexts small (one Dockerfile per app, `.dockerignore` excluding other apps) or builds take minutes just uploading context. Deploys stay independent per service, but a shared schema or contract change needs a compatibility window because the API and worker will not roll out at the same instant.

**Follow-ups they will ask:**
- A shared util changes and 12 services need deploying: the affected graph rebuilds all 12; deploy them with rolling updates and the usual N-1 compatibility.
- How do you version shared packages in a monorepo: usually not at all; everything builds from the same commit, and only published libraries get versions.

**Mistakes to avoid:**
- Running every project's tests on every commit and then complaining the pipeline takes an hour.
- Path filters that forget shared directories, so a shared change ships untested.

### Q. How does a CI pipeline change for an LLM application, and what does an eval gate or prompt regression test look like?
**Short answer (45 seconds):** Two layers. On every pull request, deterministic tests run with recorded or mocked model responses: they check prompt rendering, tool schemas, parsing of model output, retries and fallbacks, and they are fast and free. When prompts, model configuration, retrieval or eval files change, an evaluation job runs the real model against a golden dataset and scores it with exact-match checks, schema validation, retrieval metrics and an LLM judge with a rubric; the build fails if scores drop below a threshold or regress against the baseline from main.

**Deeper explanation:**

```yaml
evals:
  if: contains(github.event.pull_request.changed_files, 'prompts/') || github.event_name == 'schedule'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: pip install -r eval/requirements.txt
    - run: python -m eval.run --dataset eval/golden.jsonl --baseline eval/baseline.json --min-score 0.85
      env: { OPENAI_API_KEY: ${{ secrets.EVAL_OPENAI_API_KEY }} }
```

Prompt regression tests are plain unit tests: render the template with fixed inputs and snapshot the string, so an accidental edit shows as a diff in review; assert that extraction outputs validate against the JSON schema; replay a recorded tool-calling trace (VCR.py or nock cassettes) and assert the agent picks the right tool with the right arguments. Evals need a dataset of real or synthetic cases with expected answers or grading criteria, pinned model snapshots so a provider update does not look like your regression, several runs per case because outputs vary even at temperature zero, and a judge model stronger than the one under test. promptfoo, DeepEval and Ragas provide scaffolding; owning the dataset and thresholds is what matters.

**Follow-ups they will ask:**
- How do you avoid the judge being wrong: calibrate it against human labels on a sample, use pairwise comparison against the baseline, and keep exact-match checks where the task allows.
- How do you test the RAG part: retrieval recall at k on labeled queries, separately from generation quality, so you know which half regressed.

**Mistakes to avoid:**
- Calling the live model in unit tests, making CI slow, expensive and flaky.

### Practice
- Build the two-job workflow for a Node API with a Postgres service container and GHCR push; make a deliberate test failure and confirm no image is pushed.
- Shard a slow Jest or pytest suite across four runners with JUnit artifacts, then compare wall time and total runner minutes before and after.
- Set up a production environment with a required reviewer and an OIDC role (or a dummy step that prints the token claims) and walk through the approval flow.
- Write a prompt regression suite: snapshot three rendered prompts, validate extraction output against a JSON schema from a recorded response, and add a promptfoo or custom eval with a threshold that fails on a deliberately worsened prompt.
- Say it out loud: describe your pipeline from commit to production in 90 seconds, naming each gate and what stops a bad change at it.

## Deployment Strategies

> This section is about blast radius and time to recover. Interviewers ask "how do you deploy without downtime" and then push on the realistic parts: two versions serving at once, a migration that cannot be undone, a canary that looks fine for ten minutes and then fails, a rollback that would lose data. Strong answers pick a strategy for a reason, describe the traffic path, and know exactly what makes a rollback safe or unsafe.

### Concepts you must understand
- A deployment strategy answers two questions: how is traffic shifted between versions, and how fast can you get back; each strategy trades capacity cost, blast radius and complexity differently.
- Rolling updates replace pods gradually and are the Kubernetes default; both versions serve at once, so every change must be compatible with its neighbor and with the current schema.
- Blue/green keeps two complete environments and flips traffic in one step, giving instant rollback at the price of double capacity and a shared database that must work for both.
- Canary sends a small slice of real traffic to the new version and promotes in steps based on metrics; it needs L7 traffic splitting and an explicit definition of healthy.
- Feature flags separate deploy from release: the code ships dark and the flag decides who sees it; a dark launch runs the new path in shadow and compares results without exposing them.
- Rollback is cheap for stateless code (previous image, previous commit) and expensive for data; roll forward when a migration or data format has already moved on.
- Database changes follow expand and contract: add, dual-write, backfill, switch reads, then remove, spread across separate deploys, never a destructive change in the same deploy as the code that needs it.
- GitOps makes git the source of truth and lets an in-cluster controller (Argo CD, Flux) pull and reconcile; a deploy is a commit, a rollback is a revert, and drift is corrected automatically.
- Immutable infrastructure replaces images and servers instead of patching them in place, which removes drift and turns rollback into redeploying the previous artifact.

### Q. Compare rolling, blue/green and canary deployments. Which would you pick for a payments API and why?
**Short answer (45 seconds):** Rolling swaps pods a few at a time, cheap and simple, but rollback takes another rollout. Blue/green runs a full copy of the new version beside the old and flips traffic at once, so rollback is instant, but you pay for two environments and share the database. Canary sends a small percentage of real traffic to the new version and promotes on metrics, the smallest blast radius at the cost of traffic splitting and good metrics. For a payments API I would use a canary with automated analysis, because real traffic is the only test that catches some failures.

**Deeper explanation:**

| Strategy | Blast radius | Rollback | Needs |
| --- | --- | --- | --- |
| Rolling | grows with the rollout | another rollout | readiness probes, N-1 compatibility |
| Blue/green | all or nothing | instant switch | second environment, double capacity |
| Canary | 1 to 10 percent, then steps | shift weight back | L7 splitting, metrics, analysis |

All three share one constraint: during the transition two versions run against one database and one set of clients, so API contracts and schemas must be compatible across adjacent versions. Blue/green in Kubernetes is two Deployments behind one Service whose selector flips, or an Argo Rollouts blue-green strategy with an active and a preview Service. Rolling fits most internal services; blue/green suits infrequent high-risk releases that need a preview environment; canary suits high-traffic services where metrics are meaningful within minutes.

**Follow-ups they will ask:**
- How do you test the green environment before the flip: a preview Service or hostname that only internal users and smoke tests hit.
- Can a canary be done with plain Deployments: coarsely, by running a second Deployment with one replica behind the same Service, which gives roughly 1/N of traffic with no control.

**Mistakes to avoid:**
- Claiming blue/green needs no compatibility work because "only one version is live"; the database is shared and the flip back must still work.

### Q. How would you implement a canary release with metrics-based promotion on Kubernetes?
**Short answer (45 seconds):** Use a controller that owns the traffic shift and the analysis: Argo Rollouts or Flagger. The Rollout replaces the Deployment and defines steps: send 10 percent of traffic to the canary, pause, run an analysis that queries Prometheus for the canary's error rate and p95 latency, and if it passes move to 25, 50, 100 percent. Traffic splitting is done by ingress-nginx canary weights or a mesh. If any analysis fails, the controller aborts and shifts all traffic back to the stable version automatically.

**Deeper explanation:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: api }
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: api-canary
      stableService: api
      trafficRouting: { nginx: { stableIngress: api } }
      steps:
      - setWeight: 10
      - pause: { duration: 5m }
      - analysis: { templates: [{ templateName: api-health }] }
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: { name: api-health }
spec:
  metrics:
  - name: success-rate
    interval: 1m
    failureLimit: 2
    successCondition: result[0] >= 0.995
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(http_requests_total{app="api",rollouts_pod_template_hash="{{args.canary-hash}}",status!~"5.."}[2m]))
          / sum(rate(http_requests_total{app="api",rollouts_pod_template_hash="{{args.canary-hash}}"}[2m]))
```

The metric must isolate the canary pods, which is why the pod template hash is in the query. Choose metrics that move within the pause window: 5xx rate, p95 latency, and a business signal such as checkout completion or, for an LLM feature, tool-call failure rate and provider error rate. Weighted routing by percentage is not sticky, so a user may hit both versions; for session-sensitive flows route by header or cookie (`canary-by-header`) so the canary cohort is consistent.

**Follow-ups they will ask:**
- The canary has too little traffic for significance: lengthen the pause, raise the initial weight, or canary by cohort (internal users) rather than by percentage.
- What if the canary looks fine but corrupts data slowly: metrics will not catch it; that is what dark launches, shadow comparisons and strong migration discipline are for.

**Mistakes to avoid:**
- Analysis on cluster-wide error rate, which the small canary barely moves.

### Q. How do feature flags and dark launches change the way you ship, and how would you use them for a new LLM-powered feature?
**Short answer (45 seconds):** Flags separate deployment from release: the code merges and deploys dark, then a flag turns it on for internal users, then a percentage, then everyone, and a kill switch turns it off in seconds without a deploy. A dark launch goes further: the new code path runs for real requests in shadow, its result is logged and compared but not shown. For an LLM feature I would deploy the new prompt or model behind a flag, shadow it on a slice of traffic to compare outputs, cost and latency against the current version, then ramp by percentage with the eval and user metrics as the gate.

**Deeper explanation:**

```ts
const variant = await flags.getStringValue("summarizer-model", "gpt-current", { targetingKey: user.id, tenant: user.tenant });
const result = await summarize(doc, MODELS[variant]);
if (await flags.getBooleanValue("summarizer-shadow", false, ctx)) {
  shadowCompare(doc, result, MODELS["candidate"]).catch(log.warn); // fire and forget
}
```

OpenFeature is the vendor-neutral SDK; LaunchDarkly, Unleash, Flagsmith and GrowthBook are providers. Rules to say out loud: evaluate flags locally from a streamed ruleset so an outage of the flag service does not add latency or fail requests; every flag has a default that is the safe behavior; percentage rollouts hash a stable key such as user or tenant ID so a user does not flip between variants; flags are temporary and get deleted after full rollout, with an owner and an expiry date to fight flag debt. For LLM features, flags also hold configuration that changes often: model name, temperature, prompt version, retrieval depth, so you can tune without deploying.

**Follow-ups they will ask:**
- How do flags interact with testing: tests set the flag explicitly for each path; CI runs both states of flags that gate significant code.
- How do you measure whether the new model is better in production: pair the variant with product metrics (acceptance rate, edits, thumbs) and a sampled judge-model comparison, not just latency.

**Mistakes to avoid:**
- Hundreds of permanent flags with unknown owners, so nobody knows which code is live.

### Q. When do you roll back and when do you roll forward, and what makes a rollback safe?
**Short answer (45 seconds):** For a user-facing incident after a deploy, rollback is the default because it is the fastest known-good state: restore the previous image, flag or commit first, investigate later. Roll forward when rollback is unsafe or impossible: a migration already dropped or rewrote data the old code depends on, the old version has a worse bug, or the fix is small and already verified. A rollback is safe when the previous artifact still exists, the current schema and config work for it, no irreversible data writes happened in between, and the mechanism is rehearsed, which is exactly why migrations are kept backward compatible for at least one version.

**Deeper explanation:** Rollback mechanisms by speed: a feature flag kill switch (seconds), shifting canary weight back (seconds), `kubectl rollout undo` or `helm rollback` (one rollout), a git revert in a GitOps repo (one sync). Event-driven systems add a trap: if the new version published messages in a new schema, the old consumer will choke on them after rollback, so message schemas also follow expand and contract. Write down the decision rule before the incident: if error rate or latency SLI is breached within N minutes of a deploy, roll back without debate; the on-call does not need permission.

```bash
kubectl rollout history deployment/api
kubectl rollout undo deployment/api --to-revision=41
```

**Follow-ups they will ask:**
- How do you know a rollback works: deploy and roll back in staging on every release, and do a production rollback drill occasionally.
- The database migration ran and cannot be reversed: roll the code forward with a fix, or keep every migration reversible or at least compatible for one version so this case never arises.

**Mistakes to avoid:**
- Debugging in production for 40 minutes while users suffer because "we almost have it".
- Treating `down` migrations as a rollback plan without ever having run them against production-sized data.

### Q. How do you coordinate database schema migrations with zero-downtime deploys in Postgres and MongoDB?
**Short answer (45 seconds):** Never ship a destructive schema change in the same deploy as the code that depends on it. Use expand and contract: first add the new column or table in a backward-compatible way, deploy code that writes to both old and new and reads the new with a fallback, backfill existing rows in batches, switch reads, and only in a later release drop the old column. Migrations run as a separate step before the rollout, from the same image, by exactly one runner holding a lock. In Postgres also respect locking behavior; in MongoDB version your documents and migrate lazily.

**Deeper explanation:**

```text
release 1: ADD COLUMN customer_email_v2 (nullable)           old code ignores it
release 2: write both columns, read v2 with fallback to v1   backfill in batches
release 3: read only v2, stop writing v1, add NOT NULL via validated constraint
release 4: DROP COLUMN customer_email                        old rows already migrated
```

Postgres specifics that interviewers like: adding a column with a constant default is fast, but a volatile default or a type change rewrites the table under an exclusive lock; build indexes with `CREATE INDEX CONCURRENTLY` (outside a transaction); add constraints as `NOT VALID` and `VALIDATE CONSTRAINT` in a second statement so validation does not block writes; set `lock_timeout` so a migration waiting on a lock fails fast instead of queuing every query behind it; backfill in bounded batches by primary key range. MongoDB has no schema lock but the same discipline applies: add a `schemaVersion` field, make the code read both shapes, migrate on write or with a background job.

**Follow-ups they will ask:**
- Why not run migrations at container startup: every replica would try, startup slows down, and a failed migration crashloops the whole fleet.
- A rename is requested: it is an add, dual-write, backfill, switch and drop, spread over releases; a plain RENAME breaks the version still running.

**Mistakes to avoid:**
- Dropping a column in the same release that stops using it, so a rollback breaks immediately.

### Q. Explain GitOps with Argo CD or Flux: how does a deploy flow end to end, and what are the failure modes?
**Short answer (45 seconds):** In GitOps the desired state of the cluster lives in a git repository and a controller running inside the cluster continuously pulls it and reconciles the cluster to match. CI's job ends at building, testing and pushing the image and then committing the new tag into the config repo. Argo CD or Flux notices the commit, applies the manifests, reports health, and reverts any manual drift. A rollback is a git revert. The failure modes are mostly human: secrets in git, drift fights, resource ordering, and a sync that looks healthy while the app is not.

**Deeper explanation:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: api-prod, namespace: argocd }
spec:
  project: payments
  source: { repoURL: https://github.com/acme/deploy, path: apps/api/overlays/prod, targetRevision: main }
  destination: { server: https://kubernetes.default.svc, namespace: payments }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```

The flow: merge to the app repo, CI builds `api:sha-3f1c2ab`, pushes, then updates `images:` in the prod overlay via a commit or pull request; Argo CD notices, diffs desired against live, syncs and checks health. Pull-based deployment means CI never holds cluster credentials and the audit trail is git history. Failure modes to name: plaintext secrets committed (use Sealed Secrets, SOPS or External Secrets references); selfHeal reverting a hotfix someone applied by hand (correct behavior, surprising at 2 a.m.); CRDs and the resources that use them in the same sync (use sync waves); "Synced" but app Degraded because the Deployment never became ready (watch health, not sync); and the controller itself being privileged and needing SSO and RBAC.

**Follow-ups they will ask:**
- How do you promote from staging to prod: a pull request changing the image tag in the prod folder, automated when staging checks pass, approved by a human when required.
- How do you handle migrations with Argo CD: a Job with a PreSync hook annotation, so it runs before the Deployment update.

**Mistakes to avoid:**
- Keeping `kubectl apply` in CI and calling it GitOps because the manifests are in git.
- One branch per environment, which turns promotion into merge conflicts.

### Q. What is immutable infrastructure, and how does it relate to containers and infrastructure as code?
**Short answer (45 seconds):** Immutable infrastructure means you never modify a running server or image in place; you build a new artifact, deploy it, and replace the old one. Containers made this natural for applications: the image is the artifact and a deploy is a swap. The same applies to nodes: a baked machine image or a managed node pool is replaced, not patched over SSH. Infrastructure as code produces those artifacts and the declarative definitions around them, so the whole stack can be rebuilt from git, drift disappears, and rollback is redeploying the previous version.

**Deeper explanation:** The contrast is mutable infrastructure: long-lived servers configured by hand or by configuration management, each slightly different, where a bug might only exist on node seven. Immutable practice replaces that with a pipeline: Packer or the cloud's image builder bakes a node image with the runtime and agents, Terraform points the node group at the new image, and the node group rolls, draining pods onto new nodes. Minimal node operating systems such as Bottlerocket or Container-Optimized OS take this further by making the root filesystem read-only and updates atomic. Operationally this means no SSH in normal life (observability and `kubectl debug` replace it), no runtime package installs, no "quick fix on the box", and secrets and configuration injected at start. The cost is that fixing anything requires a rebuild and a rollout, which is only acceptable when the pipeline is fast and trusted.

```text
mutable:    ssh node-7; apt upgrade; edit config; restart     (drift, snowflakes)
immutable:  build image v42 -> update node pool -> drain -> replace nodes (reproducible)
```

**Follow-ups they will ask:**
- How do you debug without SSH: logs, metrics, traces, `kubectl debug node`, and if needed a break-glass path that is audited and rare.
- What about state on the node: it belongs in volumes or external services precisely so nodes can be replaced freely.

**Mistakes to avoid:**
- Calling containers immutable while patching running containers with `kubectl exec` and `apt-get`.

### Practice
- Install Argo Rollouts on kind with ingress-nginx; convert a Deployment to a Rollout with a 10 percent step and a Prometheus AnalysisTemplate, then deploy a version that returns 5xx for 5 percent of requests and watch the automatic abort.
- Implement an expand and contract migration for a column rename on a Postgres table with a million rows, with batched backfill and lock_timeout, while a load generator keeps writing.
- Wrap a new behavior in an OpenFeature flag with a percentage rollout keyed on user ID, and add a shadow comparison path that logs differences without changing the response.
- Set up Argo CD against a config repo with dev and prod folders; bump an image tag via pull request and then roll back with git revert.
- Say it out loud: a canary at 10 percent shows p95 latency up 30 percent but no errors; explain what you do in the next five minutes and why.

## Scalability & Reliability

> Scalability questions at the senior level are design conversations: "traffic grows 10x, what breaks first" or "how do you keep this up when a zone dies". The interviewer wants a chain of reasoning from load to bottleneck to mechanism, with numbers where they matter. Weak answers say "add more pods and a cache"; strong answers explain what has to be true of the service to add pods, which signal drives it, where the queue and the cache sit, what gets shed under overload, and how reliability is measured and budgeted.

### Concepts you must understand
- A service scales horizontally only if any replica can handle any request: sessions, uploads and caches live outside the process, and local state is disposable.
- Vertical scaling buys time with no code change but has a ceiling and a single point of failure; horizontal scaling needs statelessness, load balancing and coordination.
- L4 load balancers forward TCP connections and know nothing about requests; L7 balancers parse HTTP and can route by path, retry, split traffic and terminate TLS, which matters for long-lived HTTP/2, gRPC and WebSocket connections.
- Autoscaling is only as good as its signal: CPU for CPU-bound work, requests per replica, latency or queue depth for I/O-bound services; scale up fast, scale down slowly.
- Queues decouple producers from consumers, absorb bursts and enable retries, at the price of at-least-once delivery, ordering constraints and the need for idempotent consumers.
- Caches sit in tiers (browser, CDN, in-process, Redis, database); the hard parts are invalidation, stampedes and stale reads, not the cache itself.
- Rate limiting protects you from clients and load shedding protects you from yourself: reject early and cheaply when saturated rather than degrade for everyone.
- SLIs are measurements, SLOs are targets over a window, and the error budget is the gap; it turns reliability into a quantity you can spend on releases.
- Capacity planning starts from measured per-replica capacity under load and peak demand, adds headroom for a zone loss, and includes external limits such as LLM provider quotas.
- Chaos engineering verifies assumptions by injecting failure deliberately; multi-AZ protects against a data center failure and multi-region against a regional one, with data consistency as the hard problem.

### Q. When do you scale vertically versus horizontally, and what has to be true of an Express API before you can run ten replicas of it?
**Short answer (45 seconds):** Scale vertically when the bottleneck is a single process that cannot be split, such as a database primary, or when a bigger instance is cheaper than engineering. Scale horizontally for stateless request handlers because it has no ceiling and survives instance failure. For an Express API that means every replica must be interchangeable: sessions in Redis or signed cookies, uploads streamed to object storage, in-memory caches treated as disposable, WebSocket fan-out through a shared pub/sub, and scheduled work moved to a CronJob or a locked job so it does not run ten times.

**Deeper explanation:** The usual hidden state in Node services: `express-session` with the default in-memory store, Multer writing to local disk, a module-level `Map` used as a cache of user permissions, Socket.IO rooms that only exist on one process, and a `setInterval` cleanup task. Each becomes a bug at two replicas, not ten. Fixes: `connect-redis` or stateless JWT sessions; stream uploads to S3 or GCS and store the key; keep in-process caches only for immutable or short-TTL data and accept per-replica inconsistency; the Socket.IO Redis adapter so a message emitted on one pod reaches clients connected to another, with sticky sessions if long polling is enabled; `SET NX PX` in Redis around scheduled tasks or a CronJob. The database is where vertical scaling comes first: Postgres handles far more load on a bigger instance with PgBouncer in front than by adding app replicas, each of which opens its own connection pool.

```text
10 replicas x pool of 20 = 200 Postgres connections -> put PgBouncer in front, pool 20 per replica -> 20 server connections
```

**Follow-ups they will ask:**
- Where do you put a per-user rate limiter at ten replicas: in Redis, since a per-process counter lets a user get ten times the limit.
- How do you find hidden state: run two replicas locally behind a round-robin proxy and run the test suite against them.

**Mistakes to avoid:**
- Saying "just add replicas" without checking for sessions, local files and in-memory state.

### Q. What is the difference between L4 and L7 load balancing, and why does it matter for gRPC, WebSockets and keep-alive connections?
**Short answer (45 seconds):** An L4 balancer works on TCP or UDP: it picks a backend when a connection opens and forwards packets, fast and protocol agnostic, but every request on that connection goes to the same backend. An L7 balancer terminates HTTP, so it can route per request by host, path or header, retry, add timeouts, split traffic for canaries and terminate TLS. With gRPC and HTTP/2, one long-lived connection carries many requests, so L4 sends them all to one pod while others idle. WebSockets are long-lived too, so balancing happens at connect time and the balancer must support the upgrade and long idle timeouts.

**Deeper explanation:** In Kubernetes, a ClusterIP Service through kube-proxy is L4: connection-level distribution. An ingress controller, Envoy, nginx or a cloud ALB is L7. The gRPC story is the classic interview case: a Node client with one channel to a Python inference service through a ClusterIP Service pins every request to a single pod. Fixes are an L7 proxy that balances HTTP/2 streams (ingress-nginx with the gRPC backend protocol, Envoy, a mesh) or client-side balancing against a headless Service, where DNS returns pod IPs and the gRPC client round-robins across them and re-resolves on changes. For WebSockets, the L7 balancer needs HTTP upgrade support and an idle timeout longer than your heartbeat interval; the AWS ALB default idle timeout is 60 seconds, so clients ping more often than that or get disconnected.

```text
L4 (NLB, kube-proxy):   client ──TCP──> backend A   (all streams on this connection -> A)
L7 (ALB, nginx, Envoy): client ──HTTP/2──> proxy ──> A, B, C per request
```

**Follow-ups they will ask:**
- When is L4 the right choice: raw throughput, non-HTTP protocols (databases, MQTT), or when you need to preserve the client IP without proxy protocol.
- Why do SSE responses stall behind nginx: response buffering; set `X-Accel-Buffering: no` or the equivalent ingress annotation.

**Mistakes to avoid:**
- Putting a gRPC service behind a ClusterIP and wondering why one pod is at 100 percent CPU.

### Q. Which signals should drive autoscaling for an I/O-bound API and for an LLM worker, and how do you avoid flapping or scaling into provider rate limits?
**Short answer (45 seconds):** Pick the signal that tracks saturation. A Node API that mostly waits on Postgres and the LLM provider barely moves CPU under load, so scale on requests in flight per replica, requests per second per replica or p95 latency, with event loop lag as a sanity metric. An LLM worker scales on queue depth per worker. Avoid flapping with a scale-down stabilization window and modest thresholds, and cap maxReplicas from the real constraint: the provider's requests or tokens per minute divided by what one replica can use, because more replicas beyond that only generate 429s.

**Deeper explanation:**

```yaml
metrics:
- type: Pods
  pods:
    metric: { name: http_requests_in_flight }
    target: { type: AverageValue, averageValue: "40" }
behavior:
  scaleUp:   { stabilizationWindowSeconds: 0, policies: [{ type: Percent, value: 100, periodSeconds: 60 }] }
  scaleDown: { stabilizationWindowSeconds: 600, policies: [{ type: Pods, value: 2, periodSeconds: 120 }] }
```

The custom metric comes from Prometheus through prometheus-adapter or from KEDA's Prometheus scaler. In-flight requests is a good saturation signal because it rises when either traffic increases or dependencies slow down, which is exactly when you need capacity, and it does not depend on how expensive each request is. For scale-down, be slow and in small steps: a burst that ends should not drop you to minimum in one minute and then force cold starts. For LLM traffic, add a client-side concurrency limiter per replica sized so that replicas times concurrency stays under the provider quota, and consider scheduled scaling with a cron trigger for predictable daily peaks.

**Follow-ups they will ask:**
- Why not memory: it rarely correlates with load for these services and a memory-based target can scale up on a leak forever.
- How do you test autoscaling: load test in staging with k6 and watch replicas, latency and 429s together.

**Mistakes to avoid:**
- CPU utilization at 80 percent as the target for an API that sits at 10 percent CPU while timing out on a slow dependency.

### Q. How do queues help you scale, and how would you design the asynchronous pipeline for long-running LLM jobs?
**Short answer (45 seconds):** A queue decouples the request rate from the processing rate: the API accepts work quickly, returns 202 with a job ID, and workers consume at their own pace, scaling on queue depth and retrying failures without the client waiting. For LLM jobs, that means a job record in Postgres or Redis, a worker pool per queue, idempotent handlers because delivery is at least once, a dead letter queue for poison jobs, and results delivered by polling, webhook or a server-sent event stream.

**Deeper explanation:**

```text
client -> POST /jobs -> 202 {jobId}          (API validates, writes job row, enqueues)
         GET /jobs/:id -> status/result       (or webhook / SSE stream of progress)
queue (BullMQ on Redis / SQS / Kafka) -> workers (Python or Node) -> LLM provider
                                           |-> progress + partial tokens to Redis -> SSE relay
```

Design points worth stating: an idempotency key on job creation so a client retry does not create two jobs; a per-tenant queue or priority so one customer's batch of 10,000 documents cannot starve interactive users; a bounded queue with backpressure, so the API returns 429 or 503 with Retry-After when depth exceeds what workers can drain; visibility timeouts or lock durations longer than the longest job plus margin, otherwise a slow job is redelivered while still running. BullMQ gives attempts, exponential backoff, rate limiting per queue and stalled-job detection on Redis; Celery with `acks_late` and a result backend is the Python equivalent; Kafka fits very high throughput and ordering per key but needs consumer-group care; SQS gives visibility timeouts and a DLQ with little operations work.

**Follow-ups they will ask:**
- Why not just make the HTTP request wait: load balancer and client timeouts, wasted connections, no retry story, and the API pod becomes the bottleneck.
- How do you handle a job that fails deterministically: retries with backoff a few times, then the DLQ with the error, an alert, and a replay tool once fixed.

**Mistakes to avoid:**
- Retrying LLM calls aggressively inside the worker so a provider incident turns into a retry storm.

### Q. Describe a caching strategy with tiers for an API that includes an LLM feature, including stampede protection and invalidation.
**Short answer (45 seconds):** Cache from the outside in: CDN for static assets and cacheable public GET responses, a small in-process LRU for immutable or slowly changing data such as prompt templates and model configs, Redis as the shared tier for user-facing derived data with TTLs, and the database as the source of truth. For LLM calls, an exact-match cache keyed on model, parameters and normalized prompt serves repeats, and the provider's prompt caching cuts cost on long shared prefixes. The hard parts are stampedes when a hot key expires and invalidation when the underlying data changes.

**Deeper explanation:**

```js
async function cached(key, ttlSec, loader) {
  const hit = await redis.get(key);
  if (hit) return JSON.parse(hit);
  const lock = await redis.set(`${key}:lock`, "1", "NX", "PX", 5000);   // one loader per key
  if (!lock) { await sleep(50); return cached(key, ttlSec, loader); }
  const value = await loader();
  const jitter = Math.floor(Math.random() * ttlSec * 0.1);
  await redis.set(key, JSON.stringify(value), "EX", ttlSec + jitter);
  return value;
}
```

Cache-aside with a lock prevents a thousand requests from recomputing the same expensive value the moment it expires; TTL jitter prevents many keys expiring together. Invalidation, in order of preference: short TTLs where staleness is acceptable, versioned keys (`user:42:v7`), explicit deletes on write for a few known keys, and pub/sub invalidation events for everything else. For LLM outputs, cache only deterministic settings and include the prompt version in the key so a prompt change invalidates everything; semantic caching by embedding similarity trades correctness for hit rate and belongs only on FAQ-like traffic.

**Follow-ups they will ask:**
- How do you measure if the cache helps: hit ratio, origin load and p95 latency with and without; a low hit ratio means wrong keys or TTLs.
- Why not cache everything forever and invalidate on write: write paths you forget, cross-service writes, and the invalidation fan-out become the system's hardest bugs.

**Mistakes to avoid:**
- Caching user-specific LLM responses under a key that does not include the user's permissions or context, leaking data between users.

### Q. How do you implement rate limiting and load shedding, and how do you handle 429s from an LLM provider?
**Short answer (45 seconds):** Rate limiting is per client: a token bucket or sliding window counter in Redis keyed by API key or tenant, enforced at the edge or in middleware, returning 429 with Retry-After. Load shedding is per server: when a replica is saturated, reject new work immediately with 503 instead of queuing it until everything times out, using a concurrency limit and a queue wait deadline, and keep health checks and critical endpoints exempt. Towards the LLM provider, treat its quota as capacity: a concurrency limiter sized to it, backoff with jitter honoring Retry-After, and a fallback such as a smaller model or a cached answer.

**Deeper explanation:**

```text
-- sliding window; KEYS[1]=tenant key, ARGV: now_ms, window_ms, limit
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1] - ARGV[2])
local count = redis.call('ZCARD', KEYS[1])
if count < tonumber(ARGV[3]) then
  redis.call('ZADD', KEYS[1], ARGV[1], ARGV[1]); redis.call('PEXPIRE', KEYS[1], ARGV[2]); return 1
end
return 0
```

The Lua script makes check and increment atomic across replicas. Rate limits should be layered: coarse per-IP limits at the CDN or ingress against abuse, per-tenant limits in the application for fairness, and per-feature budgets for expensive operations such as LLM calls, often measured in tokens per minute rather than requests. Load shedding in Node is a counter of in-flight requests with a cap and a fast 503 above it, plus timeouts on every outbound call so slow dependencies cannot pile up requests. Against the provider, a semaphore of N concurrent calls per replica with N chosen from the quota, a shared token-budget counter in Redis across replicas, and a queue in front of batch work turn a 429 flood into a smooth backlog.

**Follow-ups they will ask:**
- Where do you return 429 versus 503: 429 when the client exceeded its allowance, 503 when the server is shedding load regardless of the client.
- How do you shed load fairly: per-tenant in-flight caps so one tenant's spike does not get everyone shed.

**Mistakes to avoid:**
- A per-process in-memory limiter behind ten replicas, which multiplies every limit by ten.

### Q. Explain SLIs, SLOs and error budgets with numbers, and how they change engineering decisions.
**Short answer (45 seconds):** An SLI is a measurement of user-visible behavior, such as the fraction of requests that succeed or complete under 500 milliseconds. An SLO is the target for that SLI over a window, for example 99.9 percent of requests succeed over 30 days. The error budget is what is left: 0.1 percent of requests, or about 43 minutes of full downtime in a 30-day month. You spend the budget on releases and experiments; when it is nearly gone you slow down and invest in reliability. An SLA is a contract with penalties and should be looser than the SLO.

**Deeper explanation:**

| SLO over 30 days | Allowed downtime |
| --- | --- |
| 99.5 percent | about 3.6 hours |
| 99.9 percent | about 43 minutes |
| 99.95 percent | about 22 minutes |
| 99.99 percent | about 4.3 minutes |

Good SLIs are ratios of good events to total events, measured at the load balancer or ingress rather than inside the service. Pick SLOs per user journey: checkout deserves 99.95 percent, an admin report 99.5. For an LLM feature, an availability SLI might be "requests that return a completion, including after retries and fallback", and a latency SLI "time to first token under 2 seconds"; model quality is tracked by evals, not as an SLI. The error budget turns arguments into arithmetic: if a dependency with 99.9 percent availability sits in your path, your own SLO cannot be better without a fallback, and a deploy that burned 30 percent of the budget in an hour justifies a release freeze.

**Follow-ups they will ask:**
- Why not aim for 100 percent: cost grows without bound and users cannot tell 99.99 from 100 through their own network; the budget funds change.
- What is an error budget policy: a written agreement on what happens when the budget is exhausted, agreed before the incident, so nobody negotiates it under pressure.

**Mistakes to avoid:**
- Quoting "99.99 percent uptime" without a window or a definition of success.

### Q. How do you plan capacity for a zone failure, when would you go multi-region, and what does chaos engineering add?
**Short answer (45 seconds):** Capacity planning starts from measurements: a load test gives requests per second per replica at acceptable latency, peak traffic plus growth gives demand, and headroom covers failure. For a three-zone deployment, losing one zone leaves two thirds of capacity, so each zone must carry half of peak and total provisioning is 150 percent of peak, with pods spread by topology constraints and the database in a multi-AZ configuration with synchronous standby. Multi-region is for regional outages, distant users or data residency, and is expensive because data must be replicated and consistency decided. Chaos engineering proves the plan works before an outage does.

**Deeper explanation:**

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector: { matchLabels: { app: api } }
```

Capacity includes every layer: pods, node pool maximums per zone, database connections and IOPS, Redis memory, the ingress controller, and external quotas such as LLM provider tokens per minute and GPU availability, which has lead times. Multi-region choices: active-passive with asynchronous replication and DNS failover (accepting some data loss, defined by the RPO) is the common first step; active-active needs a globally consistent store (Spanner, CockroachDB, DynamoDB global tables) or tenant pinning so each tenant writes in one region. Chaos engineering is hypothesis driven: "if we kill one Postgres replica, p95 stays under 500 ms and no 5xx are served", run with a small blast radius and abort conditions, using tools such as Chaos Mesh, LitmusChaos or AWS Fault Injection Service; typical experiments are pod kills, node drains, database latency injection, blocked egress to the LLM provider and a zone evacuation game day.

**Follow-ups they will ask:**
- What is RTO versus RPO: how long recovery takes versus how much data you may lose; both come from business requirements, not from technology.
- What did a chaos experiment teach you: a good answer names something concrete, such as a missing retry on reconnect or an alert that never fired.

**Mistakes to avoid:**
- Provisioning exactly peak capacity across three zones and discovering during a zone outage that two thirds is not enough.

### Practice
- Load test one replica of your API with k6 or autocannon to find requests per second at a p95 of 300 ms; derive how many replicas three zones need to survive one zone loss at double today's peak.
- Put a gRPC or long-lived HTTP/2 client behind a ClusterIP Service and prove the imbalance with per-pod request counts; fix it with a headless Service or an L7 proxy and measure again.
- Implement the Redis sliding window limiter and a per-replica in-flight cap in an Express app; drive it past both limits and check that 429 and 503 appear where expected with Retry-After.
- Write SLIs and a 30-day SLO for one real endpoint, build the Prometheus recording rules, and compute the current error budget remaining.
- Say it out loud: an interviewer says traffic will grow tenfold next quarter; walk through what breaks first in your stack, in order, and what you would do about each.

## Infrastructure as Code

> For a full stack role, infrastructure as code questions check that you can read and change the Terraform for your own service, understand state well enough not to destroy production, and know how changes are reviewed and promoted. Weak answers describe Terraform as "scripts that create servers"; strong answers talk about the plan as the review artifact, state locking, module versioning, drift, and the guardrails that stop a bad apply.

### Concepts you must understand
- Infrastructure as code describes resources declaratively in versioned files so environments are reproducible, reviewable and diffable; the plan output is the review artifact.
- Terraform's loop is init (providers, modules, backend), plan (diff desired configuration against state and real resources) and apply (execute exactly that plan).
- State maps configuration addresses to real resource IDs and holds attributes including sensitive ones; it lives in an encrypted remote backend with locking, never in git.
- Modules package reusable resource groups with inputs and outputs and are version-pinned; workspaces give several states for one configuration but are a weak substitute for environment separation.
- Drift is the gap between state and reality caused by changes outside Terraform; detect it with scheduled plans and remove its causes with permissions.
- Pulumi and the AWS CDK let you write infrastructure in TypeScript or Python with real language features over the same dependency-graph idea; CDK compiles to CloudFormation and has no state file of its own.
- Environment promotion applies the same module versions with different variables through a pipeline: plan on pull request, apply on merge, lower environments before production, with the saved plan applied exactly.
- Policy as code (OPA and Conftest, Sentinel, Checkov) evaluates the plan before apply to enforce tagging, encryption, network exposure and allowed resource types.

### Q. Walk me through terraform init, plan and apply, and explain what the state file is and why it matters.
**Short answer (45 seconds):** `terraform init` downloads the providers and modules the configuration references and connects to the state backend. `terraform plan` reads the state, refreshes it against the real cloud, compares with the configuration and prints the create, update and destroy actions it would take; saving that plan to a file lets you apply exactly what was reviewed. `terraform apply` executes those actions in dependency order and updates state. State is the mapping from configuration addresses to real resource IDs and attributes; without it Terraform cannot know which bucket or cluster is "yours", so losing or corrupting it is a production incident.

**Deeper explanation:**

```bash
terraform init
terraform plan -out=tfplan -var-file=envs/prod.tfvars
terraform apply tfplan
```

The provider lock file (`.terraform.lock.hcl`) pins provider versions and belongs in git so every run resolves the same binaries. Plan output has a vocabulary worth knowing: `+` create, `-` destroy, `~` update in place, `-/+` destroy and recreate, and the phrase "forces replacement" next to the attribute that triggers it; a replacement of a database or a node pool is the line a reviewer must catch. State also stores sensitive attributes such as generated passwords in plain text, which is why the backend must be encrypted and access controlled. Everyday state operations: `terraform state list` and `show` to inspect, `moved` blocks to rename a resource without recreating it, `import` blocks to adopt an existing resource, and `state rm` to stop managing something without deleting it.

**Follow-ups they will ask:**
- What happens if you apply without a saved plan: Terraform plans again and asks for confirmation, but the diff may differ from what was reviewed if the world changed.
- Why did plan show changes when nothing was edited: drift, a provider upgrade that changed defaults, or computed attributes; read the diff before applying.

**Mistakes to avoid:**
- Describing state as optional metadata; it is the source of truth about what Terraform manages.
- Running apply from laptops against production, so state and credentials live in several places.

### Q. How do you set up remote state with locking, and what goes wrong without it?
**Short answer (45 seconds):** Put state in a remote backend: an S3 bucket with versioning and encryption plus a lock (classically a DynamoDB table), a GCS bucket which locks natively, Azure Blob storage, or HCP Terraform. Locking makes concurrent runs fail fast instead of both reading the same state, applying, and writing back conflicting versions. Without remote state you get local state files on laptops that diverge; without locking two pipelines or two engineers can create duplicate resources or corrupt the file, and recovering means manual imports and state surgery.

**Deeper explanation:**

```text
terraform {
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "prod/platform/terraform.tfstate"
    region         = "me-central-1"
    encrypt        = true
    dynamodb_table = "acme-terraform-locks"
  }
}
```

Each root module gets its own key so the blast radius of a bad apply is one stack, not the whole company. Enable bucket versioning so a corrupted or mistakenly emptied state can be rolled back to the previous object version, and restrict bucket access to the CI role and a few humans, because state contains database passwords, private keys and tokens. If a run dies mid-apply, the lock stays; `terraform force-unlock LOCK_ID` releases it after you confirm nothing else is running. Split state by lifecycle and ownership: network, cluster and shared data stores change rarely and are owned by platform; application infrastructure changes often and is owned by the team; read the former from the latter with `terraform_remote_state` data sources or, better, by passing IDs through variables so teams are not coupled to each other's state format.

**Follow-ups they will ask:**
- Two applies ran at once anyway: the lock table or bucket permissions are wrong; fix them, then inspect state against reality with plan and import or remove duplicates.
- How do you rotate a secret that is in state: rotate it in the provider and in configuration, then recognise that old state versions still contain the old value and restrict access accordingly.

**Mistakes to avoid:**
- Committing `terraform.tfstate` to git "for backup".

### Q. How do you structure Terraform for dev, staging and production: modules, workspaces or separate directories?
**Short answer (45 seconds):** Reusable modules with pinned versions, and one root module per environment in its own directory with its own backend key and variables file. Workspaces technically give separate state per environment from one directory, but they share backend configuration and credentials, make it easy to apply to the wrong environment, and cannot vary provider configuration cleanly, so most teams use them for ephemeral copies rather than for the production boundary. The goal is that dev, staging and prod differ only in variable values and module versions, and that production is in a separate cloud account or project with separate credentials.

**Deeper explanation:**

```text
infra/
  modules/
    service/        (ECS or Kubernetes service, IAM role, alarms)   tagged v1.8.0
    postgres/       (RDS, parameter group, subnet group)             tagged v2.3.1
  envs/
    dev/      main.tf  backend.tf  terraform.tfvars
    staging/  main.tf  backend.tf  terraform.tfvars
    prod/     main.tf  backend.tf  terraform.tfvars
```

Each environment's `main.tf` instantiates the modules with `source = "git::https://github.com/acme/infra-modules.git//postgres?ref=v2.3.1"` or a registry version constraint, so promoting a module change is bumping the tag in dev, then staging, then prod. Keep environment differences in variables (instance sizes, replica counts, deletion protection) rather than in conditionals inside modules. Terragrunt reduces the duplication of backend and provider blocks and expresses dependencies between stacks, at the cost of another tool. Use `for_each` over `count` for collections so removing one item does not reindex and recreate the others. Separate accounts or projects per environment give a hard permission boundary that no Terraform structure can provide.

**Follow-ups they will ask:**
- Where are workspaces appropriate: short-lived copies such as a per-pull-request preview environment, torn down automatically.
- How do you test a module: `terraform validate` and a plan in CI, plus Terratest or the native test framework that applies the module in a sandbox account and asserts on outputs.

**Mistakes to avoid:**
- `terraform workspace select prod` as the only thing standing between a developer and production.
- Copying module code into each environment directory and editing it in place.

### Q. What is drift, how do you detect it, and how do you prevent it?
**Short answer (45 seconds):** Drift is when the real infrastructure no longer matches what Terraform last applied: someone changed a security group in the console, an autoscaler changed a desired count, or a provider default changed. Detect it by running `terraform plan` on a schedule with `-detailed-exitcode`, which returns 2 when changes exist, and alerting on that. Prevent it by removing the ability to change things by hand (read-only console roles with an audited break-glass path), importing or reverting what you find, and marking attributes that are legitimately managed elsewhere with `ignore_changes`.

**Deeper explanation:**

```bash
terraform plan -detailed-exitcode -lock=false -out=drift.tfplan; code=$?
if [ "$code" -eq 2 ]; then terraform show -no-color drift.tfplan | post-to-slack; fi
```

The dangerous drift is the kind that a later apply silently reverts: an engineer widened a security group during an incident, nobody updated the code, and next week's unrelated apply closes the port again. The scheduled plan catches that within hours. Some drift is expected: an ECS service or node group whose `desired_count` is controlled by an autoscaler, or tags added by a cloud policy. For those, declare it:

```text
lifecycle {
  ignore_changes = [desired_count, tags["LastScanned"]]
}
```

Finally, the cultural fix matters most: every change goes through a pull request and a plan, incident changes get a follow-up ticket to codify them, and the console is for reading.

**Follow-ups they will ask:**
- Should drift be auto-corrected: for low-risk stacks maybe; for production, alert and review, because the drift might be the fix someone applied during an incident.
- How is this different from a failed apply: a failed apply leaves a partially applied state that the next plan reconciles; drift happens outside Terraform entirely.

**Mistakes to avoid:**
- Running `terraform apply -auto-approve` nightly to "fix drift" and undoing an emergency change at 3 a.m.
- Treating `ignore_changes` as a blanket fix instead of a per-attribute declaration.

### Q. Terraform, Pulumi or the AWS CDK: how do you choose, and what are the real differences?
**Short answer (45 seconds):** Terraform is declarative HCL with the largest provider ecosystem, mature state tooling, and the most people who already know it; OpenTofu is its open-source fork with the same model. Pulumi uses real languages (TypeScript, Python, Go) with loops, types and unit tests, keeps state in its own backend or your bucket, and reaches the same providers. The AWS CDK is also real-language code but compiles to CloudFormation, so it is AWS-only and state is the CloudFormation stack rather than a file you manage. Choose by ecosystem and team: multi-cloud or Kubernetes-heavy platforms lean Terraform or Pulumi; an AWS-only team of TypeScript developers may be happiest in CDK.

**Deeper explanation:**

| Aspect | Terraform / OpenTofu | Pulumi | AWS CDK |
| --- | --- | --- | --- |
| Language | HCL | TypeScript, Python, Go, .NET | TypeScript, Python, Java, .NET |
| State | file in remote backend | Pulumi Cloud or self-managed backend | CloudFormation stacks |
| Scope | any provider | any provider (bridged and native) | AWS (CDKTF and cdk8s extend) |
| Strength | ecosystem, hiring, plan review | abstraction, testing, secrets encrypted in state | L2 constructs with sane defaults |

Real-language IaC shines when you build platforms: a `Service` class that creates a repository, a role, a deployment and alarms, with type checking and unit tests over the synthesized output. Terraform's plan is unusually good as a review artifact and its module registry covers almost everything, which is why it remains the default for networking, cluster and database layers even where CDK handles application stacks.

**Follow-ups they will ask:**
- Why not manage Kubernetes workloads in Terraform: state coupling, slow plans, and a second deploy path competing with the application pipeline.
- What is OpenTofu: the community fork created after Terraform's license change, maintained under the Linux Foundation and compatible with existing configurations.

**Mistakes to avoid:**
- Choosing CDK for a platform that already has Terraform everywhere, creating two toolchains and two state models.

### Q. How do you promote infrastructure changes through environments in CI, and how do you handle destructive changes safely?
**Short answer (45 seconds):** On a pull request the pipeline runs fmt, validate, security scanning and a plan for each affected environment, posting the plan as a comment so reviewers approve a concrete diff. On merge it applies dev automatically from the saved plan, then staging, then production behind an environment approval, each with its own short-lived cloud credentials via OIDC. Destructive changes are made visible and hard: `prevent_destroy` on databases and state buckets, deletion protection attributes on the resources themselves, `moved` blocks for refactors so renames do not become destroy and create, and a policy check that fails any plan containing a destroy of a protected type unless explicitly acknowledged.

**Deeper explanation:**

```yaml
plan:
  steps:
    - run: terraform -chdir=envs/prod init -input=false
    - run: terraform -chdir=envs/prod plan -input=false -out=tfplan -detailed-exitcode
    - run: terraform -chdir=envs/prod show -json tfplan > plan.json
    - run: conftest test plan.json -p policy/
    - uses: actions/upload-artifact@v4
      with: { name: prod-plan, path: envs/prod/tfplan }
apply:
  needs: plan
  environment: production
  steps:
    - uses: actions/download-artifact@v4
      with: { name: prod-plan }
    - run: terraform -chdir=envs/prod apply -input=false tfplan
```

Applying the saved plan file guarantees that what the approver saw is what runs; if the world changed in between, the apply fails rather than doing something new.

```text
resource "aws_db_instance" "main" {
  deletion_protection = true
  lifecycle { prevent_destroy = true }
}
```

Avoid `-target` except in emergencies, since it produces partial applies that confuse the next plan.

**Follow-ups they will ask:**
- How do you review a 400-line plan: policy checks summarize risky actions, and the pipeline fails on any destroy or replace of protected resources so reviewers can focus.
- Who can apply to production: nobody by hand; the pipeline's role, gated by environment approvers, is the only identity with write access.

**Mistakes to avoid:**
- Approving a plan and then running `terraform apply` without the saved plan file, applying a different diff.
- Treating `terraform destroy` protections as optional because "nobody would run that".

### Q. What is policy as code, and how would you enforce guardrails in the infrastructure pipeline?
**Short answer (45 seconds):** Policy as code means writing the rules that infrastructure must satisfy as executable checks that run against the plan before apply: every resource is tagged with owner and cost center, storage is encrypted, no security group opens the database port to the internet, only approved instance types and regions are used. Tools are Conftest with Rego policies on the JSON plan, Sentinel in HCP Terraform, and scanners such as Checkov or Trivy that know common misconfigurations. The cloud side adds organization-level guardrails (AWS SCPs, GCP organization policies) that hold even if someone bypasses the pipeline.

**Deeper explanation:**

```text
package main

deny[msg] {
  r := input.resource_changes[_]
  r.type == "aws_db_instance"
  r.change.after.storage_encrypted == false
  msg := sprintf("%s: RDS storage must be encrypted", [r.address])
}

deny[msg] {
  r := input.resource_changes[_]
  r.change.actions[_] == "delete"
  r.type == "aws_db_instance"
  msg := sprintf("%s: deleting a database requires a break-glass approval", [r.address])
}
```

`terraform show -json tfplan | conftest test -p policy/ -` fails the job with those messages, which is far more useful to the author than a security review two weeks later. Terraform's own `validation` blocks on variables and `precondition` and `postcondition` blocks on resources enforce module-level contracts, such as "replica count in production must be at least two". Layer the controls: fast static scanning on every pull request for known misconfigurations, plan-time policies for organization rules, and preventive controls in the cloud account for the few rules that must never be broken, such as disallowed regions or public S3 buckets.

**Follow-ups they will ask:**
- Policies block legitimate work: add an exception mechanism with an expiry and an approver, recorded in the repo, rather than disabling the check.
- How do you handle existing non-compliant resources: report-only mode first, a dashboard of violations, then enforce for new changes while a backlog fixes the old ones.

**Mistakes to avoid:**
- A policy that only runs in a security team's dashboard, so developers learn about violations after apply.
- Rules without messages or exceptions, which teams route around.

### Practice
- Create a module for a small service (ECR repository, IAM role, log group) and instantiate it in dev and prod directories with a remote S3 backend and locking; run two applies at once and read the lock error.
- Change a resource in the console, run `terraform plan -detailed-exitcode`, and then codify the change; add `ignore_changes` for an attribute an autoscaler owns.
- Write two Conftest policies (encryption required, protected deletes) and run them against a plan JSON in CI; make one deliberately fail.
- Rename a resource address and compare a `moved` block against a plain rename in the plan output.
- Say it out loud: explain to a reviewer what the `-/+` line next to the database in a plan means and what you would do before approving it.

## Observability & On-call

> Observability questions test whether you can find out what a system is doing without guessing. Interviewers hand you a symptom ("p95 doubled after lunch") and listen for a method: which dashboard, which metric, which trace, which log line, in what order. Then they probe alerting judgment, because anyone can create alerts and few can create ones a team trusts. On-call stories reveal seniority faster than almost any other topic: how you mitigated, communicated and learned.

### Concepts you must understand
- Metrics are cheap aggregated numbers for alerting and trends, logs are detailed events for debugging, traces follow one request across services; they are useful together only when joined by shared identifiers such as trace ID, service and version.
- Prometheus pulls metrics from /metrics endpoints on a schedule; counters, gauges, histograms and summaries are the types, and labels multiply time series, so cardinality is what kills it.
- RED (rate, errors, duration) describes request-driven services and USE (utilization, saturation, errors) describes resources; every service dashboard starts with those.
- OpenTelemetry is the vendor-neutral way to produce traces, metrics and logs; the Collector receives, processes (batch, sample, enrich) and exports them to any backend.
- Loki indexes only labels and stores compressed log chunks, cheap and grep-like; Elasticsearch indexes every field, powerful and expensive to run.
- Alerts must be actionable, symptom-based and tied to an SLO; cause-based alerts (CPU high) create noise, and noise teaches people to ignore real pages.
- Burn-rate alerts page when the error budget is being consumed too fast over several windows, catching sudden outages and slow bleeds with few false pages.
- Incident response has roles (commander, communications, operators), one channel, mitigation before root cause and a timeline; postmortems are blameless and end in owned action items.
- For LLM features add token counts, cost, provider latency and error rates, cache hit rate and tool-call failures to the standard signals.

### Q. Explain metrics, logs and traces, and how you would use them together to debug a slow request through an API, a worker and an LLM provider.
**Short answer (45 seconds):** Metrics tell me that something is wrong and roughly where: the p95 latency histogram for the API rose at 13:05 while the error rate did not. Traces tell me which hop is slow for a specific request: the span tree shows the API call taking 6 seconds, of which 5.8 are in the span for the provider call from the worker. Logs tell me why: the worker log line with that trace ID shows a 429 and two retries with backoff. They only work together because the trace ID is in every log line and service and version labels are on every metric.

**Deeper explanation:**

```text
trace 7f3a...  POST /summaries                                      6.1s
  ├─ api: validate + enqueue                                        40ms
  ├─ worker: fetch document (Postgres)                              30ms
  ├─ worker: llm.chat gpt-4o-2024-08-06                             5.8s   <- 429, retry x2
  └─ api: SSE relay                                                 ...
```

Metrics are aggregated, so they are cheap to store for months and fast to alert on, but they cannot tell you about one request. Traces are per request and expensive, so you keep a sample plus every slow or failed one (tail sampling). The debugging order is therefore dashboard, then exemplars or trace search filtered by latency and route, then logs for that trace ID. In code this means: propagate the W3C traceparent header across HTTP and inject the trace context into queue messages so the worker's spans join the same trace; add the trace ID to the logger's context. For LLM calls, record the model, prompt version, input and output tokens and whether the response came from cache as span attributes, so cost or latency regressions trace back to a prompt change.

**Follow-ups they will ask:**
- How do traces cross a queue: put the trace context into the message headers and start the consumer span as a child or a link of it.
- What is an exemplar: a trace ID attached to a histogram bucket sample, letting you jump from a latency spike on the dashboard to a representative trace.

**Mistakes to avoid:**
- Describing the three pillars without explaining the identifiers that join them.

### Q. How does Prometheus work, which metrics would you expose from a Node or Python service, and what is the cardinality problem?
**Short answer (45 seconds):** Prometheus scrapes an HTTP endpoint on each target at an interval and stores the samples as time series identified by a metric name and label set; in Kubernetes it discovers targets through the API, usually via ServiceMonitor objects. A service exposes counters for requests and errors by route and status, a histogram for request duration and for each dependency, gauges for in-flight requests and pool usage, and the runtime defaults such as event loop lag or garbage collection. Cardinality is the number of distinct label combinations: a label with unbounded values such as user ID or raw URL path creates millions of series, slows every query and eventually takes the server down.

**Deeper explanation:**

```js
const client = require("prom-client");
client.collectDefaultMetrics();
const httpDuration = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "Request duration",
  labelNames: ["method", "route", "status"],
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});
app.use((req, res, next) => {
  const end = httpDuration.startTimer();
  res.on("finish", () => end({ method: req.method, route: req.route?.path ?? "unmatched", status: res.statusCode }));
  next();
});
```

Histograms are the workhorse: buckets are cumulative counters, so `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` gives an aggregatable p95 across pods, which summaries cannot do. Use the route template (`/users/:id`), never the raw path, and cap status to the code or class. Find cardinality offenders with `topk(10, count by (__name__)({__name__=~".+"}))`. For LLM services, counters for tokens by model and direction and a histogram for provider latency by model are the additions, with cost computed from tokens in the dashboard rather than as another metric.

**Follow-ups they will ask:**
- Counter or gauge for queue depth: gauge, since it goes up and down; counters are only for monotonically increasing totals used with `rate`.
- How do you alert on a batch job that runs every hour: push its last success timestamp to the Pushgateway or a gauge and alert when `time() - last_success > 2h`.

**Mistakes to avoid:**
- A `user_id` or `request_id` label, which is the canonical cardinality explosion.
- Summaries with client-side quantiles that cannot be aggregated across replicas.

### Q. What does the OpenTelemetry Collector do, and how would you deploy it in Kubernetes for traces, metrics and logs?
**Short answer (45 seconds):** The Collector is a pipeline process: receivers accept telemetry (OTLP from your apps, Prometheus scrapes, container log files), processors transform it (batching, memory limits, adding Kubernetes metadata, filtering, sampling), and exporters send it to backends (Tempo or Jaeger, Prometheus or Mimir, Loki, or a vendor). Applications send OTLP to a local collector, so you can change destinations, sample and redact without redeploying them. The standard Kubernetes layout is a DaemonSet agent per node for collection and enrichment plus a central gateway Deployment for tail sampling and export.

**Deeper explanation:**

```yaml
receivers:
  otlp: { protocols: { grpc: { endpoint: 0.0.0.0:4317 }, http: { endpoint: 0.0.0.0:4318 } } }
  filelog: { include: [/var/log/pods/*/*/*.log] }
processors:
  memory_limiter: { check_interval: 1s, limit_mib: 400 }
  k8sattributes: {}
  batch: {}
exporters:
  otlp/tempo: { endpoint: tempo.monitoring:4317, tls: { insecure: true } }
  loki: { endpoint: http://loki.monitoring:3100/loki/api/v1/push }
service:
  pipelines:
    traces: { receivers: [otlp], processors: [memory_limiter, k8sattributes, batch], exporters: [otlp/tempo] }
    logs:   { receivers: [filelog], processors: [memory_limiter, k8sattributes, batch], exporters: [loki] }
```

Applications instrument with the SDKs: in Node, `@opentelemetry/auto-instrumentations-node` loaded with `--require` wraps http, Express, pg, ioredis and the common clients; in Python, `opentelemetry-instrument` does the same for FastAPI, requests, httpx and psycopg. Both export OTLP to the node-local agent address injected as an environment variable. Tail sampling must see all spans of a trace, which is why it runs in the gateway tier behind a load-balancing exporter keyed by trace ID; a typical policy keeps all error traces, all traces slower than a threshold and a few percent of the rest.

**Follow-ups they will ask:**
- Why not export straight from the app to the vendor: credentials in every pod, no central sampling or redaction, and a vendor change becomes a redeploy of everything.
- How do you keep the collector from being a bottleneck: memory_limiter first in the chain, batch before export, horizontal scaling of the gateway, and queued retry on exporters.

**Mistakes to avoid:**
- Head sampling at one percent in the SDK and then wondering why the failed request has no trace.

### Q. Loki or the ELK stack: how do you choose a logging backend, and how do you design labels and queries?
**Short answer (45 seconds):** Loki indexes only a small set of labels (namespace, app, pod, container) and stores the log lines as compressed chunks in object storage, so it is cheap to run and queries work like grep plus parsing at read time; it fits structured JSON logs and teams already in Grafana. Elasticsearch or OpenSearch indexes every field at ingest, which makes arbitrary full-text search and aggregations fast but costs far more in storage, memory and operations. I pick Loki for application logs with good structure and modest search needs, and reserve a full-text engine for security or product analytics where field-level search across everything is the point.

**Deeper explanation:**

```text
{namespace="payments", app="api"} |= "timeout" | json | duration > 2s | line_format "{{.traceId}} {{.route}} {{.duration}}"
sum by (status) (rate({namespace="payments", app="api"} | json | __error__="" [5m]))
```

Loki's model requires discipline: labels must be low cardinality, so never put request ID, user ID or trace ID in a label; keep them in the JSON body and filter with parsers. The ELK side: Logstash or Fluent Bit ships to Elasticsearch, Kibana queries it, and operational work includes mappings (a field whose type changes breaks ingestion), shard sizing, JVM heap, and index lifecycle policies for retention. Both benefit from the same application habits: JSON lines, a consistent set of field names across services (`level`, `msg`, `traceId`, `service`, `version`), and redaction of secrets and personal data before the log leaves the pod.

**Follow-ups they will ask:**
- How do you jump from a metric to the logs: Grafana data links from a panel to a Loki query with the same labels and time range, and from a trace to its logs via the trace ID.
- Logs are too expensive: lower the level in noisy components, sample debug logs, shorten retention, and move audit logs to cheap cold storage rather than keeping everything hot.

**Mistakes to avoid:**
- Trace ID as a Loki label, which creates one stream per request and collapses performance.

### Q. How do you design alerting that an on-call team trusts, and how do you fight alert fatigue?
**Short answer (45 seconds):** Alert on symptoms users feel, measured as SLIs: error rate, latency, availability of a journey, and a few saturation precursors that predict them, such as a disk that will fill in four hours. Every page must need a human action now and link to a runbook; everything else is a ticket or a dashboard panel. Give each alert a `for` duration to ignore blips, group and route them by service in Alertmanager, inhibit downstream alerts when an upstream one fires, and review the pages every week: anything that fired without action gets fixed, downgraded or deleted.

**Deeper explanation:**

```yaml
groups:
- name: api
  rules:
  - alert: ApiHighLatency
    expr: histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{app="api"}[5m]))) > 0.5
    for: 10m
    labels: { severity: page, team: payments }
    annotations:
      summary: "API p95 above 500ms for 10m"
      runbook_url: https://runbooks.acme.internal/api/high-latency
  - alert: Watchdog
    expr: vector(1)
    labels: { severity: none }
```

The Watchdog is a dead man's switch: it always fires, and an external service pages you if it stops arriving, which is the only way to know the alerting pipeline itself is alive. Severities should map to a response: page means wake someone, ticket means next business day, and there should be nothing in between. Cause-based alerts (CPU above 80 percent, pod restarted once) are noise because they do not tell you whether users are affected; keep them as dashboard panels or as inputs to the runbook. Measure the alerting system (pages per week per person, percentage actioned); above a handful of pages per shift the fix is deleting alerts, not more training.

**Follow-ups they will ask:**
- What goes in a runbook: what the alert means, how to confirm impact, the three most likely causes with the commands to check them, mitigation steps, and who to escalate to.
- How do you alert on something that is missing rather than wrong: `absent()` or a staleness check on the last success timestamp.

**Mistakes to avoid:**
- Paging on every 5xx or on CPU, so the on-call learns to acknowledge without looking.

### Q. What is an SLO burn-rate alert and how would you write one?
**Short answer (45 seconds):** Burn rate is how fast you consume the error budget relative to the pace that uses it exactly by the end of the window; burn rate 1 spends the 30-day budget in 30 days, 14.4 spends 2 percent of it in an hour. A burn-rate alert pages when the recent error ratio exceeds the SLO's allowance times a burn-rate factor, evaluated over two windows, a long one for significance and a short one so the alert resets quickly after recovery. The standard set pages at 14.4x over 1 hour and 6x over 6 hours, and opens tickets at 3x over a day and 1x over three days.

**Deeper explanation:**

```yaml
- alert: ApiErrorBudgetBurnFast
  expr: |
    (
      sum(rate(http_requests_total{app="api",status=~"5.."}[1h]))
      / sum(rate(http_requests_total{app="api"}[1h]))
    ) > (14.4 * 0.001)
    and
    (
      sum(rate(http_requests_total{app="api",status=~"5.."}[5m]))
      / sum(rate(http_requests_total{app="api"}[5m]))
    ) > (14.4 * 0.001)
  labels: { severity: page }
```

With a 99.9 percent SLO the allowed error ratio is 0.001, so the fast alert fires at a 1.44 percent error rate sustained for an hour and still showing in the last five minutes. The 6x over 6 hours alert (with a 30 minute short window) catches a smaller but sustained problem, and the slow 3x and 1x alerts (one day with two hours, three days with six hours) surface slow bleeds as tickets. Multi-window alerts beat a simple threshold: a brief spike does not page, a real outage pages within minutes, and the short window clears the alert soon after the fix. Sloth and Pyrra generate these rules from an SLO definition.

**Follow-ups they will ask:**
- Why 14.4: a burn rate of 14.4 over one hour consumes 2 percent of a 30-day budget (14.4 times 1 hour divided by 720 hours), which is the chosen page threshold.
- Low traffic at night makes the ratio noisy: add a minimum request count condition or use longer windows for low-traffic services.

**Mistakes to avoid:**
- Alerting on the 30-day budget being exhausted, which tells you about an outage long after users did.

### Q. What belongs on a per-service dashboard, and what would you add for an LLM-backed service?
**Short answer (45 seconds):** Top row: SLO status and remaining error budget, then RED metrics overall and per route, then saturation (CPU throttling, memory versus limit, event loop lag, pool usage, queue depth), then dependencies (latency and errors to Postgres, Redis, external APIs), with deploy markers and a logs panel on the same labels. For an LLM service add tokens in and out, cost per request and per tenant, provider latency including time to first token, provider 429 and 5xx rates, cache hit rate, tool-call success rate and fallback usage.

**Deeper explanation:**

```text
Row 1  SLO: availability 99.95% (budget 61% left)  | p95 latency vs SLO | deploy markers (version label)
Row 2  RED: req/s by route | 5xx ratio by route | p50/p95/p99 latency
Row 3  Saturation: CPU throttled seconds | memory vs limit | event loop lag | pg pool in use | queue depth
Row 4  Dependencies: pg query p95 | redis p95 | llm provider p95 + TTFT | provider 429/5xx | cache hit %
Row 5  LLM: input/output tokens per req | cost/hour by model and tenant | tool-call failures | fallback rate
```

Consistency across services matters more than any single panel: when every service uses the same layout and variables (namespace, service, pod), an on-call engineer can read an unfamiliar service's dashboard in seconds. Build dashboards as code (Grafana JSON in git, Grafonnet or Terraform) from a template per service type. For LLM services, cost and quality drift are as important as latency: a prompt change that doubles output tokens shows up as cost per request, and a nightly eval score trend on the dashboard links production behavior to the quality gate.

**Follow-ups they will ask:**
- How many panels: enough to answer "is it broken, where, since when" without scrolling; detail goes on drilldown dashboards.
- Percentiles or averages: percentiles, since averages hide the slow tail that users complain about.

**Mistakes to avoid:**
- Twenty host-level panels and no error rate, which is a dashboard about the machine rather than the service.

### Q. Walk me through how you run an incident when you are on call, and what a good postmortem looks like.
**Short answer (45 seconds):** Acknowledge the page, confirm user impact from the SLO dashboard, and declare an incident with a severity so the right people are pulled in. Assign roles: an incident commander who coordinates, a communications lead who updates stakeholders and the status page on a cadence, and operators who investigate and act. Mitigate first, diagnose second: roll back the last deploy, flip the feature flag, scale up or fail over, whichever restores service fastest. Keep a timestamped timeline in one channel. Afterwards, write a blameless postmortem with impact, timeline, contributing causes, what went well and poorly, and action items with owners and due dates.

**Deeper explanation:** The first five minutes decide the incident's length. Check whether a deploy, config change or flag flip happened in the last hour; if yes, revert it before understanding why, because the understanding can wait and the users cannot. Escalate early and explicitly: "I need someone from the payments team" beats silent struggling. Post updates every 15 or 30 minutes even if nothing changed. The postmortem happens within a few days while memory is fresh and focuses on systems rather than people: "the deploy pipeline allowed a migration without a compatibility check" rather than "the engineer forgot". Structure: summary, impact in user and SLO terms, detection time, timeline, contributing causes, what went well, what was luck, and action items prioritized by what would have prevented or shortened it.

```text
13:02 deploy sha-3f1c to prod   13:05 p95 alert pages   13:09 incident declared SEV2, IC: A, comms: B
13:12 rollback started          13:16 p95 recovered     13:20 status page: resolved, monitoring
```

**Follow-ups they will ask:**
- How do you decide severity: by user impact and scope, defined in advance, so nobody debates it during the incident.
- What if you do not know the cause after mitigation: that is normal; service is restored, and root cause analysis continues in the postmortem with the data you preserved.

**Mistakes to avoid:**
- Postmortems that end with "be more careful" or that name a person as the root cause.

### Practice
- Instrument an Express and a FastAPI service with OpenTelemetry auto-instrumentation and the Collector on kind; send a request through both via a Redis queue and confirm one trace spans API, worker and a mocked LLM call.
- Expose a request duration histogram with route labels; deliberately add a `user_id` label, watch series counts grow in Prometheus, then remove it.
- Write the four burn-rate alert rules for a 99.9 percent SLO with Sloth or by hand, and test them by injecting a 2 percent error rate with a load generator.
- Build a per-service Grafana dashboard from JSON in git with the six-row layout, including a cost-per-request panel computed from token counters.
- Say it out loud: you are paged at 2 a.m. with "API p95 above SLO"; narrate your first ten minutes, including what you type, what you say in the channel and when you roll back.

## Security in the Delivery Pipeline

> Security questions in a DevOps context are about the path from source to production: what could inject malicious code or steal credentials along the way, and what you do about it. Interviewers do not expect a security specialist, but they do expect a senior engineer to know why `latest` tags and long-lived AWS keys in CI are dangerous, what an SBOM is for, how secrets reach a pod, and how the network is segmented. Weak answers list tools; strong answers describe the attack each control stops.

### Concepts you must understand
- Supply chain security covers everything that becomes part of your artifact: dependencies, base images, build tools, CI actions and the pipeline itself; each is a way for an attacker to run code with your credentials.
- Lockfiles, `npm ci`, hash-pinned Python requirements, base images pinned by digest and actions pinned to commit SHAs make builds reproducible and remove the mutable-reference class of attacks.
- An SBOM lists every component in an artifact in SPDX or CycloneDX format; generated at build time and stored with the image, it answers "which images contain this vulnerable package" in minutes.
- Signing with cosign binds a signature to an image digest, keyless signing ties it to the CI identity through OIDC and a transparency log, and admission control refuses unsigned images.
- Scanning has layers: SCA for dependencies, SAST for your code, secret scanning for leaked credentials, container and IaC scanning for configuration, DAST against a running environment.
- Secrets belong in a manager (Vault or the cloud's secret manager), reach workloads through short-lived leases or synced Kubernetes Secrets, rotate on a schedule, and never appear in git, images or build logs.
- CI credentials follow least privilege: OIDC federation instead of static keys, per-environment roles scoped by repository and branch, minimal token permissions, and separate identities for build and deploy.
- TLS everywhere means automated certificates at the edge (cert-manager and ACME), verified encrypted connections to databases and queues, and mutual TLS between services where identity matters.
- Network segmentation limits what a compromised component can reach: private subnets for data stores, default-deny network policies, egress allow-lists and no public endpoints without a reason.

### Q. What is software supply chain security, and how do you protect a Node and Python build against compromised dependencies and CI actions?
**Short answer (45 seconds):** Supply chain security is about the code you did not write but ship anyway: npm and PyPI packages, base images, build tools and the third-party CI actions that run with your secrets. Attacks include typosquatting, dependency confusion, hijacked maintainer accounts, install scripts that exfiltrate tokens, and compromised actions that dump the CI environment. Defenses are reproducibility and least privilege: lockfiles installed with `npm ci` or hash-checked pip, no install scripts where possible, a registry proxy with a cooldown on new versions, actions and base images pinned to digests, minimal CI permissions, and provenance for what you publish.

**Deeper explanation:**

```bash
npm ci --ignore-scripts && npm rebuild --ignore-scripts=false sharp   # run only the scripts you trust
pip install --require-hashes -r requirements.txt                        # hashes from pip-compile --generate-hashes
```

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683   # v4.2.2, pinned by SHA
```

Dependency confusion (an unclaimed internal package name on the public registry) is removed by scoped packages with a scoped registry and a proxy registry such as Artifactory or CodeArtifact. Automated update tools such as Renovate can enforce a minimum release age, so a malicious version pulled within hours is never installed. Base images pinned by digest with the same tooling bumping them turn tag drift into a reviewed pull request. For your own artifacts, generate provenance attestations and an SBOM in CI; the SLSA framework describes the maturity levels. Finally, the pipeline itself is part of the chain: protect the workflows directory with required review, restrict which third-party actions the organization may use, and assume any step can read every secret in its job.

**Follow-ups they will ask:**
- Why pin by SHA when tags have versions: tags are mutable; a compromised repository can move `v4` to malicious code and every consumer picks it up on the next run.
- What about transitive dependencies: the lockfile pins them too; audit tools and SBOMs make them visible; fewer dependencies is still the strongest control.

**Mistakes to avoid:**
- `npm install` in CI with a floating range, which resolves to whatever was published a minute ago.

### Q. What is an SBOM, how do you generate and use one, and how does image signing with cosign fit in?
**Short answer (45 seconds):** A software bill of materials is a machine-readable inventory of every component in an artifact: OS packages, npm and PyPI dependencies, versions and licenses, in SPDX or CycloneDX format. You generate it at build time with Syft or Trivy, attach it to the image as an attestation, and store it so that when a new vulnerability is announced you query which running images contain the affected package instead of rescanning everything. Signing complements it: cosign signs the image digest, keyless signing ties the signature to the CI workflow identity through OIDC with a public transparency log, and admission control in the cluster rejects images without a valid signature from your pipeline.

**Deeper explanation:**

```bash
syft ghcr.io/acme/api@sha256:3f1c... -o spdx-json > sbom.spdx.json
cosign sign --yes ghcr.io/acme/api@sha256:3f1c...                         # keyless in CI via OIDC
cosign attest --yes --predicate sbom.spdx.json --type spdxjson ghcr.io/acme/api@sha256:3f1c...
cosign verify --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp '^https://github.com/acme/api/.github/workflows/release.yml@refs/heads/main$' \
  ghcr.io/acme/api@sha256:3f1c...
```

Keyless signing works like this: the CI job presents its OIDC token to Sigstore's certificate authority (Fulcio), receives a short-lived certificate bound to the repository, workflow and branch, signs the digest with it, and the signature plus certificate are recorded in the Rekor transparency log and stored in the registry next to the image. Verification checks the certificate identity, not a long-lived key you have to protect. In the cluster, a Kyverno `verifyImages` policy or the Sigstore policy controller enforces that every image in production namespaces is signed by the release workflow on main; a developer pushing a hand-built image is blocked at admission. Always sign and verify by digest, since a tag can be repointed after signing.

**Follow-ups they will ask:**
- Where do SBOMs live long term: as OCI attestations in the registry plus a searchable store or dependency-tracking tool for fleet-wide queries.
- What does signing not protect against: a malicious change merged through the normal pipeline is signed too; signing proves origin, not correctness.

**Mistakes to avoid:**
- Signing the tag, or verifying with no identity constraints so any Sigstore signature passes.

### Q. How do you lay out security scanning in the pipeline, and how do you keep it from blocking developers all day?
**Short answer (45 seconds):** Layer the scanners: composition analysis for vulnerable dependencies, static analysis for your code, secret scanning, container and infrastructure scanning for misconfigurations, and dynamic scanning against staging. Run the fast ones on every pull request and the slow ones on main and nightly. Gate only on findings that are new, high severity and fixable; report the rest as pull request comments and tracked debt with remediation deadlines by severity.

**Deeper explanation:**

| Layer | What it catches | Tools | When |
| --- | --- | --- | --- |
| SCA | vulnerable dependencies | npm audit, pip-audit, Trivy, Snyk, Dependabot | every PR |
| SAST | injection, unsafe patterns in code | Semgrep, CodeQL, Bandit | every PR, diff-aware |
| Secrets | keys and tokens in code or history | gitleaks, trufflehog, push protection | pre-commit and PR |
| Container | OS and app CVEs, root user, bad config | Trivy, Grype, Docker Scout | after build |
| IaC | public buckets, open security groups | Checkov, Trivy, Conftest policies | PR on infra changes |
| DAST | runtime issues, auth and header problems | OWASP ZAP | nightly on staging |

Diff-aware scanning (only findings introduced by this change) is the single biggest usability win; Semgrep and most SCA tools support a baseline. Keep allowlists in the repository with a reason and an expiry per entry so exceptions are reviewed. For LLM applications add two more checks: prompt injection and jailbreak test suites run against the staging deployment, and tests that tool implementations enforce authorization server-side rather than trusting the model's arguments.

**Follow-ups they will ask:**
- The scanner reports 400 findings on day one: baseline them, enforce on new findings immediately, and burn the backlog down by severity with deadlines.
- How do you stop secrets before they are committed: pre-commit hooks with gitleaks and registry-side push protection, plus immediate rotation when one does land.

**Mistakes to avoid:**
- Failing the build on every medium finding so developers learn to bypass or ignore the scanner.

### Q. How do you manage application secrets in Kubernetes with Vault or a cloud secret manager, including rotation?
**Short answer (45 seconds):** The source of truth is a secret manager: HashiCorp Vault or the cloud's own (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault). Workloads authenticate with their own identity (ServiceAccount token or cloud workload identity), never a stored key, and receive secrets synced into Kubernetes Secrets by External Secrets Operator or mounted by the Secrets Store CSI driver or a Vault agent sidecar. Rotation is designed in: dynamic database credentials with short leases where possible, otherwise dual credentials and an app that re-reads mounted files or restarts on change. Git holds only references, and etcd encryption at rest protects the synced copies.

**Deeper explanation:**

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata: { name: api-secrets, namespace: payments }
spec:
  refreshInterval: 1h
  secretStoreRef: { kind: ClusterSecretStore, name: aws-secrets-manager }
  target: { name: api-secrets }
  data:
  - secretKey: DATABASE_URL
    remoteRef: { key: prod/payments/api, property: DATABASE_URL }
```

The operator authenticates with the cluster's workload identity, pulls the value and writes a normal Kubernetes Secret; on the next refresh a rotated value appears, and Reloader rolls the Deployment if it is consumed as an environment variable. Vault adds dynamic secrets: its database engine creates a Postgres user per lease with a TTL and revokes it automatically, so nothing long-lived exists to leak; its Kubernetes auth method maps a ServiceAccount to a policy. Rules to say out loud: one secret per purpose with the narrowest reader, audit logging on reads, redaction in loggers, and the biggest win of all, workload identity (IRSA or Pod Identity on EKS, Workload Identity on GKE) so the application calls cloud APIs with a role rather than a stored key.

**Follow-ups they will ask:**
- Rotating a third-party API key with no overlap support: create the new key, deploy, verify, revoke the old one, on a schedule rather than after a leak.
- What about secrets for GitOps: ExternalSecret manifests hold only references; Sealed Secrets or SOPS cover values that must live in git.

**Mistakes to avoid:**
- Kubernetes Secrets as the system of record, created by hand with `kubectl create secret` and never rotated.

### Q. How do you give CI least-privilege access to the cloud and the cluster without long-lived keys?
**Short answer (45 seconds):** Use OIDC federation: the CI job presents a short-lived identity token from GitHub or GitLab, and the cloud exchanges it for temporary credentials for a role whose trust policy accepts only tokens from a specific repository, branch or environment, so there is no static key to store, rotate or leak. Then split identities by blast radius: a build role that can only push to one registry repository, a deploy role per environment that can only update the service's workloads, and an infrastructure role used only by the infrastructure repository behind approvals. Inside the cluster the deploy identity maps to a namespaced Role with the few verbs the deploy needs.

**Deeper explanation:**

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
    "StringLike": { "token.actions.githubusercontent.com:sub": "repo:acme/api:environment:production" }
  }
}
```

The `sub` condition is the whole point: without it any GitHub repository could assume the role. Scope it to the environment so the production role is only reachable from a job that passed the environment's approval, and scope staging to its own role. GCP uses a Workload Identity Pool provider with an attribute condition on the repository, Azure a federated credential per environment. The permissions attached to the role are narrow: `ecr:PutImage` on one repository for build, `eks:DescribeCluster` plus a cluster access entry mapped to a Kubernetes group for deploy, with that group bound to a Role allowing patch and update on Deployments in one namespace. In the workflow, `permissions: id-token: write` enables the token request and everything else stays read-only.

**Follow-ups they will ask:**
- What if the CI provider's OIDC issuer is compromised: the blast radius is still bounded by the role conditions and permissions; it is a reason for narrow roles, not for going back to static keys.
- How do developers deploy from laptops in an emergency: a break-glass role requiring MFA and producing an alert, used rarely and reviewed each time.

**Mistakes to avoid:**
- A trust policy with a wildcard subject, which turns the role into a public resource.

### Q. How do you implement TLS everywhere: at the edge, between services and to databases?
**Short answer (45 seconds):** At the edge, cert-manager requests and renews certificates automatically from Let's Encrypt through ACME, or the cloud load balancer uses managed certificates, so nothing expires by surprise. Between services, either a mesh provides mutual TLS with workload identities automatically, or cert-manager issues short-lived certificates from a private CA that services load and rotate. To databases and queues, connections use TLS with the server certificate actually verified, which for Postgres means `sslmode=verify-full` with the provider's CA bundle, not just `require`. Minimum TLS 1.2, prefer 1.3, HSTS at the edge, and expiry monitoring on every certificate you own.

**Deeper explanation:**

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: platform@acme.com
    privateKeySecretRef: { name: letsencrypt-account }
    solvers:
    - dns01: { route53: { region: me-central-1 } }
```

An Ingress annotated with `cert-manager.io/cluster-issuer: letsencrypt` and a `tls` block gets a Certificate object, a Secret with the key pair, and automatic renewal; DNS-01 solves wildcard certificates and does not need a public HTTP endpoint. Internally, the question is identity as much as encryption: mutual TLS lets the payments service know the caller is the API and not a compromised pod in another namespace. Istio and Linkerd do this with automatic certificate rotation and SPIFFE-style identities; without a mesh, cert-manager with a CA issuer (backed by Vault PKI, a cloud private CA or a self-managed root) issues short-lived certificates into Secrets that services load, and trust-manager distributes the CA bundle. For data stores, `require` mode encrypts but accepts any certificate, which still allows an in-path attacker; `verify-full` checks the chain and the hostname.

**Follow-ups they will ask:**
- Why terminate TLS at the ingress instead of in every pod: central certificate management and cipher policy; re-encrypt or use mTLS inside if the cluster network is not trusted.
- How do you rotate a private CA: issue the new CA, distribute a bundle containing both, reissue leaf certificates, then remove the old one.

**Mistakes to avoid:**
- `sslmode=require` described as "verified TLS".

### Q. How would you segment the network for a Kubernetes-hosted application that uses Postgres, Redis and external LLM APIs?
**Short answer (45 seconds):** Three layers. In the cloud network, only load balancers and NAT live in public subnets, nodes sit in private subnets, and Postgres and Redis sit in isolated subnets whose security groups accept only the node security group on their ports. In the cluster, namespaces per environment with default-deny NetworkPolicies, so only the API can reach Postgres and Redis. For egress, pods have no direct internet route; outbound traffic goes through a NAT with an allow-list or an egress proxy so the only external destinations are the LLM provider APIs. Entry is through the ingress controller behind a WAF, and the cluster API endpoint is private or IP-restricted.

**Deeper explanation:**

```text
internet -> WAF / CDN -> cloud LB (public subnet) -> ingress controller (private nodes)
          -> api pods (namespace payments, default deny, allow from ingress-nginx)
          -> postgres (isolated subnet, SG: from node SG on 5432 only, TLS verify-full)
          -> redis (isolated subnet, SG: from node SG on 6379 only, TLS)
          -> egress: NAT + allow-list (api.openai.com, api.anthropic.com) or egress gateway
cloud APIs (S3, ECR, Secrets Manager) via private endpoints, no internet path
```

Private endpoints (AWS PrivateLink, GCP Private Service Connect) keep traffic to cloud services off the public internet. Egress control matters most for an LLM application because a prompt injection that makes a tool fetch a URL becomes a data exfiltration channel if pods can reach anything; an allow-list of provider domains through a firewall with FQDN rules or an egress gateway closes that, and tool implementations should run with their own stricter policy.

**Follow-ups they will ask:**
- How do you debug connectivity when everything is locked down: a netshoot debug pod in the namespace with the same labels, flow logs from the CNI or the VPC, and the NetworkPolicy and security group checked in that order.
- Where does rate limiting and bot protection live: at the WAF and CDN layer, before traffic reaches the cluster.

**Mistakes to avoid:**
- A database with a public IP "protected by a strong password".

### Practice
- Pin every action in a workflow to a commit SHA and every base image to a digest; set up Renovate to bump them and read one of its pull requests.
- Generate an SBOM with Syft for your production image, scan it with Grype, sign the image with cosign keyless in GitHub Actions, and enforce a Kyverno verifyImages policy on kind that blocks an unsigned image.
- Deploy External Secrets Operator against a cloud secret manager (or a Vault dev server), rotate a value, and confirm the pod sees the new value without a redeploy.
- Create an OIDC trust policy for a deploy role scoped to one repository and one environment; try to assume it from another branch and read the error.
- Say it out loud: describe the path of a request from the internet to Postgres through your stack and name the control at each hop that stops an attacker who has compromised the previous one.
