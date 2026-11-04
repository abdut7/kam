## Docker Fundamentals

### Why it exists
Before containers, "it works on my machine" was a real cause of outages: the server had a different Node or Python version, a missing system library, or a dependency that resolved differently at install time. Docker packs the application, its runtime and its libraries into one image that runs the same on a laptop, in CI and in production, and it starts in seconds because it shares the host kernel instead of booting a whole virtual machine. The image becomes the single thing you test, ship and roll back. The cost is a new set of things to get right: image size, layer caching, keeping secrets out of builds, and weaker isolation than a virtual machine because every container shares one kernel.

## Containers in Production

### Why it exists
An image that runs on a laptop is not yet safe to run for real users. Production asks questions a demo never does: which exact version is running, how much memory and CPU it may use, where its logs go, what happens when the platform asks it to stop, and whether it carries known vulnerabilities. Without rules for these, teams ship `latest` tags nobody can trace, containers get killed for memory with no warning, and deploys drop requests because processes die mid-flight. The trade-off is discipline in every service: immutable tags, resource limits, structured logs, graceful shutdown and scanning all take setup time before they pay back.

## Kubernetes Core Objects

### Why it exists
Running a few containers by hand works until a machine dies at night, traffic doubles, or a new version must replace the old one without downtime. Before Kubernetes, teams wrote scripts and used PM2 or systemd on each virtual machine to restart processes, update load balancer lists and copy configuration around. Kubernetes replaces that with a declared desired state ("six copies of this image, this much memory, reachable under this name") and controllers that keep reality matching it: they reschedule after failures, roll out new versions and send traffic only to healthy pods. The price is real complexity: many object types, a lot of YAML, and a control plane to upgrade and secure, which is too much for one small service.

## Kubernetes Operations & Debugging

### Why it exists
Kubernetes hides machines behind abstractions, so when something breaks the status rarely says what went wrong in plain words: you see `CrashLoopBackOff` or `Pending`, not "your secret is missing". Operations skills turn those states into causes quickly, using the events, exit codes and logs the cluster records. Around that sit the tools that keep a shared cluster manageable: Helm or Kustomize for configuration, RBAC for who may do what, network policies for who may talk to whom, and autoscalers for GPU and queue workloads. Without this layer every incident is guesswork and every team edits the cluster by hand; with it, you pay in tooling and learning time.

## CI/CD Pipelines

### Why it exists
When builds and deploys are manual, releases are rare and risky and depend on one person's laptop: someone skips a test, builds from uncommitted code, or deploys the wrong branch. Continuous integration runs the same checks on every change so broken code is caught in minutes, and continuous delivery turns a release into a repeatable pipeline that builds one artifact and promotes it through environments. That makes small, frequent releases safe, and small releases are what actually reduce risk. The cost is pipeline upkeep: a slow or flaky pipeline blocks the whole team, and a CI system holding deploy credentials becomes an attack target of its own.

## Deployment Strategies

### Why it exists
Replacing a running version always carries risk: the new code might be broken, slow, or unable to read data the old code wrote. Stopping everything and starting the new version means downtime and an all-or-nothing bet. Rolling, blue/green and canary releases, plus feature flags, exist to limit the damage: shift traffic gradually, watch the metrics, and get back to the last good state quickly. The trade-off is that old and new versions run side by side for a while, so APIs, message formats and database schemas must stay compatible across that window, which takes planning on every change.

## Scalability & Reliability

### Why it exists
A system that works for a hundred users can fall over at ten thousand, and the breaking point is rarely where people expect: database connections, a cache stampede, a third-party rate limit or one slow dependency. This section is about adding capacity on purpose (replicas, queues, caches, load balancing) and staying up when parts fail (timeouts, retries, load shedding, redundancy across zones). Service level objectives give the team a shared, measurable definition of "reliable enough", so reliability work can be weighed fairly against features. Every reliability layer costs money and complexity, so the goal is the reliability users need, not the most that is possible.

## Infrastructure as Code

### Why it exists
Infrastructure clicked together in a cloud console cannot be reproduced: staging differs from production in small undocumented ways, and rebuilding after a mistake means remembering every setting. Infrastructure as code describes networks, databases, clusters and permissions in files that are reviewed, versioned and applied by a tool such as Terraform, so every change goes through a pull request and an environment can be recreated from code. The tool keeps a state file that maps the code to real resources, and that brings its own problems: state must be stored safely and locked, and anyone who changes things by hand creates drift. A careless apply can also delete production resources in bulk, so plans must be read and guarded.

## Observability & On-call

### Why it exists
In a distributed system one slow request may pass through a gateway, three services, a queue and an LLM provider, and without data you are guessing which hop is at fault. Metrics show trends and drive alerts, logs record what happened in detail, and traces connect one request across services, so engineers can answer "what broke and why" from evidence. On-call practice makes someone clearly responsible when users are hurt, with alerts tied to user impact rather than to every CPU spike. The costs are storage bills, instrumentation work, and alert fatigue when thresholds are careless, which teaches people to ignore the one page that matters.

## Security in the Delivery Pipeline

### Why it exists
Attackers increasingly target the path code takes to production instead of the application itself: a compromised npm package, a malicious GitHub Action, a leaked deploy key or an image swapped in the registry. The pipeline holds the keys to production, so a weakness there bypasses every control inside the app. Dependency and image scanning, artifact signing, short-lived cloud credentials through OIDC, managed secrets and TLS between services exist to close those paths. The trade-off is friction: noisy scanners and strict gates slow developers down, so controls must be tuned to block real risk rather than every low-severity finding.

## DevOps Project Scenarios [Scenarios]

> Interviewers run these as open conversations: they describe a team, a system and a constraint, then keep changing the constraint to see whether your plan adapts. A weak answer jumps straight to tools ("I would use Kubernetes and Argo CD"). A senior answer asks what problem is being solved and how big it is, proposes the smallest design that solves it, names the trade-offs out loud, sequences the change so nothing breaks halfway, and says which numbers would prove it worked.

### Concepts you must understand
- Start from the constraint, not the tool: team size and skills, traffic, budget, compliance, deadline and what is failing today shape the design more than any best-practice list.
- Ask for the numbers first: peak requests per second, deploys per week, number of services, data size, tolerable downtime (RTO) and tolerable data loss (RPO).
- Build one immutable artifact per commit and promote it by digest; environments differ only in configuration, never in what was built.
- Every change has a window where old and new versions run together, so schemas, APIs and message formats must work for both sides.
- Migrate in small steps behind a reversible switch (weighted routing, a feature flag, a parallel run) and keep the old path alive until the new one has carried real traffic.
- Capacity is set by the slowest layer, not the pod count: database connections, queue partitions, node provisioning time, GPU availability and third-party rate limits.
- Measure delivery and reliability with a few numbers: the four DORA metrics (deploy frequency, lead time, change failure rate, time to restore), SLO attainment and cost per request.
- Say what you are deliberately not doing and why; ruling out a service mesh or multi-region with a reason is a senior signal.

### Q. You are setting up CI/CD from scratch for a monorepo with a Next.js app, a NestJS API and a Python worker. Eight developers want to ship to production several times a day. How do you design it?
**Short answer (45 seconds):** I first ask where it runs (say Kubernetes on AWS), how environments are split and what hurts today. Then one pipeline that detects affected projects, runs their checks in parallel with caching, and builds one image per changed service tagged with the commit SHA. That exact image goes to staging by digest, gets smoke tested, and is promoted to production behind an approval or an automatic gate, with database migrations as their own step. Cloud credentials come from OIDC, not stored keys.

**Deeper explanation:** Affected detection (Nx or Turborepo, path filters for the worker) is standard; the senior decisions are on delivery.

```yaml
deploy-prod:
  needs: [build, smoke-staging]
  environment: production        # required reviewers, prod-only secrets
  concurrency: { group: deploy-prod, cancel-in-progress: false }
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with: { repository: acme/gitops, token: "${{ secrets.GITOPS_PUSH_TOKEN }}" }
    - run: |
        cd envs/prod
        kustomize edit set image api=ghcr.io/acme/api@${{ needs.build.outputs.api_digest }}
        git -c user.name=ci -c user.email=ci@acme.dev commit -am "prod: api ${{ github.sha }}"
        git push
```

Next.js inlines `NEXT_PUBLIC_` variables into the client bundle at build time, which breaks "build once, promote everywhere"; keep those values environment-neutral or serve them from a runtime config endpoint, and build with `output: "standalone"` for a small image. Pull requests get a Next.js preview against the shared staging API, not a full stack per PR. The API and worker share a queue message contract, so changes are additive and the consumer ships first. Migrations run as a pre-sync Job before the API rolls. GitOps with Argo CD gives an audit trail and rollback by `git revert`.

The risk is the pipeline itself becoming the bottleneck, so I set a budget (minutes to staging, not tens of minutes) and track DORA metrics, pipeline duration and flaky test rate.

**Follow-ups they will ask:**
- Only the worker changed: only its jobs run and only its image digest is bumped; the others stay as they are.
- Frontend and API must release together: design so they do not need to, with backward-compatible endpoints and feature flags.

**Mistakes to avoid:**
- Rebuilding images per environment, so production runs something staging never tested.
- Long-lived AWS keys in repository secrets when OIDC role assumption is available.

### Q. Your NestJS API on Kubernetes runs TypeORM migrations at startup, and every release needs a five-minute maintenance window. Product wants deploys during business hours with zero downtime. What do you change?
**Short answer (45 seconds):** Three things. Move migrations out of application startup into one step that runs before the rollout, from the same image, with a lock timeout. Make every migration backward compatible with the code still running, using expand and contract for anything destructive, and enforce that with a migration linter in CI. And make the rollout graceful: readiness gates traffic, SIGTERM drains in-flight requests, and maxUnavailable is zero.

**Deeper explanation:** First I ask why the window exists. Usually `migrationsRun: true` makes every replica race to migrate on boot, a long `ALTER TABLE` blocks queries, and old pods break against the new schema.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: api-migrate-3f1c2ab
  annotations: { argocd.argoproj.io/hook: PreSync }
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: ghcr.io/acme/api@sha256:9b1e...
        command: ["node", "node_modules/typeorm/cli.js", "migration:run", "-d", "dist/data-source.js"]
```

Set `migrationsRun: false` in the data source. Each migration starts with `SET lock_timeout = '5s'` so it fails fast instead of queueing every query behind it. Rules for the team: only additive changes ship with the code that uses them; renames and drops spread over releases; indexes use `CREATE INDEX CONCURRENTLY`, which cannot run inside a transaction, so that migration must run without one; constraints go in as `NOT VALID` and are validated separately. A linter such as squawk flags blocking DDL in the pull request. For the rollout: maxSurge 1, maxUnavailable 0, a readiness probe, a short preStop sleep so the load balancer stops sending before the process stops, and `app.enableShutdownHooks()` so NestJS closes the server and pool on SIGTERM.

The trade-off is more releases per schema change and a team that must think about the overlap window. I measure 5xx and p99 during each deploy, sessions waiting on locks in `pg_stat_activity`, and migration duration.

**Follow-ups they will ask:**
- The migration Job fails halfway: the sync stops, old pods keep serving because they tolerate the expanded schema; fix and rerun.
- A backfill touches tens of millions of rows: not in the migration; a separate batched, throttled job by primary key range.

**Mistakes to avoid:**
- Dropping a column in the same release that stops using it, which breaks rollback.
- Keeping migrations at startup, so one failed migration crashloops the whole fleet.

### Q. You inherit twelve Node.js services on EC2 run by PM2 and deployed by SSH and `git pull`. Leadership wants them on Kubernetes within a quarter. How do you plan the migration?
**Short answer (45 seconds):** I ask why first: if the pain is manual deploys and snowflake servers, containers on a managed platform fix that, and ECS is a valid option next to Kubernetes. If Kubernetes is justified (more services coming, GPU work, a platform owner), I go in phases: make the services container-ready while still on the VMs, stand up a managed cluster with GitOps and observability, then move services one at a time behind weighted routing, with the VMs as instant fallback.

**Deeper explanation:** Inventory each service: its PM2 settings (`exec_mode: "cluster"`, `instances`, `max_memory_restart`, `cron_restart`), ports, env files on disk, local file writes, sticky sessions, WebSockets and scheduled jobs. That is what breaks in containers.

```text
phase 1  on VMs: Dockerfile per service, env config, JSON logs to stdout, uploads to S3, SIGTERM handling
phase 2  EKS via Terraform, load balancer controller, Argo CD, Prometheus, External Secrets
phase 3  least critical service first: ALB weights VM 90 / cluster 10, then 50, then 100
phase 4  remaining services in batches, then decommission the VMs
```

Translation rules: PM2 cluster mode becomes one Node process per container and more replicas, so Kubernetes sees every crash and its memory. `max_memory_restart` becomes a memory limit plus a real fix for the leak it was hiding. Crons inside PM2 or the app become CronJobs with `concurrencyPolicy: Forbid`, otherwise every replica runs them. Databases and Redis stay managed services and are never moved in the same step. One shared Helm chart or Kustomize base keeps the twelve services consistent.

Risks: memory limits exposing old leaks, and a team that cannot yet debug a pod at 2 a.m., so runbooks and pairing are part of the plan. I measure deploy frequency and lead time before and after, p95 and error rate during each traffic shift, and monthly cost.

**Follow-ups they will ask:**
- A Socket.IO service relies on sticky sessions: enable stickiness at the ALB or ingress and add the Redis adapter so events reach clients on other pods.
- Rollback during phase 3: set the cluster weight back to zero; the VMs never stopped serving.

**Mistakes to avoid:**
- Running PM2 cluster mode inside the container, which hides restarts and memory from Kubernetes.
- A big-bang weekend cutover of all twelve services.

### Q. In a system like CADBEATER, a vLLM server for a fine-tuned vision model shares one EKS cluster with the NestJS API and workers. The GPU bill keeps rising, and a CPU pod once stopped a GPU node from scaling down. How do you design the cluster?
**Short answer (45 seconds):** Separate the two worlds on one control plane: a CPU node pool for the API and workers, and a GPU pool that is tainted and labeled by GPU type, so only pods that tolerate the taint and request `nvidia.com/gpu` land there. Scale the inference pods on queue depth instead of CPU, let the GPU pool follow the pods, keep a small warm minimum for latency, and cap GPU use per namespace with quotas. Then watch GPU utilization and cost per request, because idle GPUs are the bill.

**Deeper explanation:** Clarify the request pattern (steady or business hours), the time-to-first-token target, model size against GPU memory, and which work can wait (evals, re-embedding).

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: vllm, namespace: inference }
spec:
  scaleTargetRef: { name: vllm }
  minReplicaCount: 1
  maxReplicaCount: 4
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus.monitoring:9090
      query: sum(vllm:num_requests_waiting)
      threshold: "5"
```

The taint is what keeps a stray CPU pod off GPU nodes; the cluster autoscaler will not remove a node that hosts a pod it is not allowed to move, such as one with local storage or a PodDisruptionBudget that allows no disruption. A ResourceQuota with `requests.nvidia.com/gpu` stops a dev namespace from grabbing GPUs. Karpenter NodePools can mix on-demand GPUs for serving with spot GPUs for interruptible batch work. PriorityClasses let serving preempt batch. Model weights load from a node-local cache or a fast shared volume, and a pre-pull DaemonSet trims image pull time. Small models can share a card with MIG or time-slicing, but time-slicing gives no memory isolation.

The trade-off: a warm minimum costs money overnight; scaling to zero saves it, but the first user waits for node boot plus model load. I measure `DCGM_FI_DEV_GPU_UTIL`, queue wait, time to first token and cost per thousand requests.

**Follow-ups they will ask:**
- Why not a separate GPU cluster: valid at larger scale or with a separate team; one cluster keeps networking, identity and tooling simple for a small team.
- Inference pods Pending at peak: check the pool maximum and cloud capacity per zone, and allow several GPU instance types.

**Mistakes to avoid:**
- Autoscaling vLLM on CPU utilization, which says nothing about GPU saturation.
- Giving every namespace GPU access "for testing" with no quota.

### Q. A Samsung-style eCommerce site expects about ten times normal traffic for a flash sale in three weeks. You own the platform. How do you prepare?
**Short answer (45 seconds):** Turn "ten times" into numbers per flow (browse, cart, checkout, payment) and into a shape: a sale opening at a fixed time is a wall, not a ramp. Load test the real system at that shape, fix the first bottleneck, repeat, and pre-scale everything that reacts too slowly, because autoscalers and node provisioning take minutes and the spike takes seconds. Plan degradation for when the forecast is wrong, and run the event with a war room, dashboards and rehearsed kill switches.

**Deeper explanation:** Clarify last sale's numbers, the forecast, and which dependencies have fixed ceilings (payment gateway, inventory, OTP provider).

```bash
kubectl patch hpa checkout -n shop -p '{"spec":{"minReplicas":40}}'   # hours before opening
```

Load test with an open-model executor such as k6's `ramping-arrival-rate`, so offered load does not drop when the system slows; closed-loop tests hide saturation. Use production-sized data and the payment provider's sandbox for checkout end to end. Usual bottlenecks in a Node microservices stack with Kafka and RabbitMQ: Postgres connections (pool size times replicas must stay under `max_connections`, so add PgBouncer), Kafka consumer lag because consumers cannot outnumber partitions, a cache stampede on the hero product page, and the ingress itself.

Pre-scale: raise HPA `minReplicas` and node pool minimums before the opening, ask the cloud provider to pre-warm or reserve load balancer capacity, and cache listing and product pages at the CDN. Protect checkout: a virtual waiting room or token bucket in front of the sale page, flags to switch off recommendations and reviews, idempotency keys on order creation, and inventory reservations with a TTL. Freeze deploys 48 hours before, with tested rollback.

I measure orders per minute against forecast, payment success rate, p99 per critical flow, consumer lag, and database CPU and connections.

**Follow-ups they will ask:**
- The payment gateway caps below your forecast: queue orders and confirm asynchronously, or negotiate the limit in advance; you cannot autoscale a third party.
- Traffic arrives at double the forecast: the waiting room and shedding absorb it, so you serve fewer users well instead of everyone badly.

**Mistakes to avoid:**
- Relying on the HPA alone for a spike that arrives in seconds.
- Load testing one endpoint and declaring the whole system ready.

### Q. A six-person startup runs everything in one AWS region: EKS, RDS Postgres, S3 and a self-hosted Qdrant. They want a disaster recovery plan on a small budget. What do you propose?
**Short answer (45 seconds):** First get two numbers from the business per system: how long they can be down (RTO) and how much data they can lose (RPO). At this size the answer is usually backup and restore, not a hot standby: point-in-time recovery for Postgres with copies in another region and another account, versioned and replicated S3, Qdrant snapshots shipped to S3, and the cluster rebuildable from Terraform and GitOps. Then a timed restore drill, because an untested backup is a hope.

**Deeper explanation:** Rank threats by likelihood: a bad migration or script deleting data, a compromised credential, a zone failure, a region failure. Replication does not help with the first two because it copies the deletion too.

```text
system     protection                                  restore path
Postgres   PITR backups, snapshot copies to region 2   new instance from PITR, repoint app
S3         versioning, replication to backup account   restore versions or replica bucket
Qdrant     scheduled snapshots copied to S3            restore snapshot, or re-embed
cluster    Terraform + Argo CD repo                    new cluster, sync all apps
secrets    Secrets Manager replicated to region 2      same names in the new region
```

Decisions: backups live in a separate account protected by AWS Backup Vault Lock or S3 Object Lock, so a compromised production admin cannot delete them. Multi-AZ RDS covers a zone failure and is usually worth its cost; a warm standby in a second region usually is not, at this size. Qdrant can be rebuilt by re-embedding the source documents, so its snapshot only shortens recovery; time the re-embed, since that is the fallback RTO. The runbook holds exact commands, the DNS records to switch (keep their TTLs low) and named owners.

Risks: restores far slower than assumed, and backups failing silently. I measure the real RTO and RPO from each drill, backup job success and snapshot age.

**Follow-ups they will ask:**
- Who restores at 3 a.m.: at least two people who have done it in a drill; the runbook is not tribal knowledge.
- When to move to warm standby: when the business RTO falls below what a restore takes, or a contract demands it.

**Mistakes to avoid:**
- Calling Multi-AZ or read replicas a backup; they faithfully replicate a `DROP TABLE`.
- Backups in the same account and region as production.

### Practice
- Build the monorepo pipeline on a toy repo with a Next.js app, a NestJS API and a FastAPI worker: affected detection, one image per service tagged with the SHA, deploy to kind through an Argo CD config repo, promote by digest, and time it end to end.
- Do a column rename on Postgres with expand and contract while k6 hits the API through a rolling update; confirm zero 5xx and watch `pg_stat_activity` for lock waits.
- Run a k6 `ramping-arrival-rate` test against a local stack until something saturates, write down which layer broke first, fix it, and run again.
- Run a timed restore drill: dump a local Postgres, drop the database, restore it, and record the real RTO and RPO you achieved.
- Say it out loud: "You have three weeks before a sale with ten times normal traffic." Give the plan in two minutes, starting with the numbers you would ask for.

## DevOps Incidents & Error Cases [Scenarios]

> Interviewers describe a symptom and watch your order of operations. Use the same spine every time: clarify impact (who is affected, since when, what changed), contain (roll back, scale, flip a flag, stop the bleeding before you understand it), diagnose from evidence (status and exit codes, events, metrics, logs), fix the cause, and prevent a repeat with an alert, a test, a guardrail or a runbook. Name the exact commands you would type and say which result would confirm or kill each hypothesis. Weak answers guess a cause in the first sentence; strong answers narrow it down.

### Concepts you must understand
- The first question is always "what changed": deploys, config, flags, infrastructure applies, certificate renewals, traffic and dependency status in the last hour.
- Mitigate before you diagnose when users are hurting: a rollback, a flag, scaling up or failing over buys time, and the root cause can wait for the postmortem.
- Kubernetes records why it acted: pod status and exit codes, events (kept about an hour by default) and controller conditions, so capture them before they age out or a rollback replaces the pods.
- Work out the blast radius early: one pod, one node, one zone or everything points at code, a node, the network or a shared dependency.
- Every incident ends with a guardrail, not just a fix: the alert that would have caught it earlier, the CI check that would have blocked it, or the runbook entry for next time.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| `CrashLoopBackOff` right after a deploy | `kubectl logs POD --previous` and the exit code in `kubectl describe pod` | missing env var or secret, migration not run, wrong entrypoint, liveness probe on the wrong port | `kubectl rollout undo`, fix config, validate config at startup |
| `OOMKilled`, exit code 137 | last state in `kubectl describe pod`, working set against limit over time | memory that grows with input size, too many workers per pod, a leak | bound concurrency, stream large inputs, set the limit from measured peaks |
| `ImagePullBackOff` or `ErrImagePull` | the Failed event text in `kubectl describe pod` | wrong tag, missing imagePullSecret or node IAM role, `toomanyrequests` from Docker Hub | fix the tag or credentials, mirror base images into your own registry |
| `exec format error` in the container logs | `docker buildx imagetools inspect IMAGE` for the platforms it contains | arm64 image built on a laptop running on amd64 nodes | build with `--platform linux/amd64` or multi-arch in CI |
| Pending with `Insufficient nvidia.com/gpu` | FailedScheduling event, GPU capacity in `kubectl describe node` | GPU pool at max, no cloud capacity in the zone, device plugin not running, idle pods holding GPUs | raise limits or allow more instance types, fix the GPU Operator, free idle GPUs |
| Pending with `Insufficient cpu` or `Insufficient memory` | "Allocated resources" in `kubectl describe node` | requests far above real usage, node pool at its maximum | right-size requests, raise the pool maximum |
| `Readiness probe failed` with `context deadline exceeded` | CPU throttling ratio, event loop lag, probe `timeoutSeconds` | CPU limit hit at peak, blocked event loop, probe calls the database | cheap local probe, longer timeout, remove the throttling |
| Rollout stuck, `ProgressDeadlineExceeded` | `kubectl describe deployment` and events on the new ReplicaSet | new pods never ready, `exceeded quota`, no room for surge pods | roll back, then fix readiness, quota or capacity |
| Pods `Evicted`, node shows `DiskPressure` | node conditions, `du` under `/var/log/pods` and the containerd directory | files written inside containers, very chatty logs, old images piling up | ephemeral-storage limits, lower log level, prune images |
| `Error acquiring the state lock` | Lock Info (Who, Operation, Created) and running CI jobs | cancelled or crashed apply, two pipelines on one stack | confirm nothing runs, `terraform force-unlock`, CI concurrency group |
| Plan says "Objects have changed outside of Terraform" | `terraform plan -refresh-only` and CloudTrail for that resource | console change during an incident, a field an autoscaler manages | codify or revert with the owner, `ignore_changes` per attribute |
| Same commit passes and fails CI on reruns | failure history per test name across runs | shared database state, real clocks, unawaited promises, real network calls | quarantine with an owner and a deadline, fix test isolation |
| Secret scanning alert on a pushed key | key type, first commit, repository visibility, forks | `.env` committed, key in a test fixture, key echoed in CI logs | revoke and rotate first, audit usage, then purge history |
| `NET::ERR_CERT_DATE_INVALID` or "certificate has expired" | `openssl x509 -noout -dates` on the certificate actually served | failed ACME challenge, expired DNS credentials, hand-uploaded certificate | renew now, fix the solver, alert on expiry |

### Q. Right after a deploy, the new pods go into CrashLoopBackOff and `kubectl rollout status` hangs at "3 out of 6 new replicas have been updated". What do you do?
**Short answer (45 seconds):** With default surge settings the old pods still carry most traffic, so I confirm impact on the dashboard, spend a minute capturing evidence from one crashing pod, and roll back so we stop running mixed versions. Then I read why the new pods die: exit code and last state, `kubectl logs --previous`, and a diff of the old and new pod templates. The cause is usually configuration, not code.

**Deeper explanation:** Why half done: six replicas with the default 25 percent maxSurge and maxUnavailable allow two extra pods and one missing, so the controller stops at three new crashing pods and five old ones serving, which can go unnoticed.

```bash
kubectl describe pod api-6d8f9-x2k4 -n prod | grep -A6 "Last State"
kubectl logs api-6d8f9-x2k4 -n prod --previous --tail=100 > crash.log
kubectl rollout undo deployment/api -n prod
diff <(kubectl get rs api-5c7b4 -n prod -o yaml) <(kubectl get rs api-6d8f9 -n prod -o yaml)
```

The failed ReplicaSet stays (scaled to zero), so the template diff still works after the rollback. Likely causes, ranked:
1. A new required env var or secret key missing in production: exit 1 and a clear log line.
2. The code expects a migration that has not run.
3. A changed port or health path, so the liveness probe kills a healthy process: exit 137 and "Liveness probe failed" events at the probe period.
4. An image built for the wrong CPU architecture: logs show `exec format error`.
5. A broken entrypoint after a Dockerfile refactor: exit 127, command not found.

Prevent: validate config at boot with a schema (NestJS `ConfigModule` validation, pydantic-settings) so a missing value fails with one obvious line; give staging production-shaped secrets; alert on `KubePodCrashLooping` and on the Progressing condition going false; or let Argo Rollouts abort a failing canary.

**Follow-ups they will ask:**
- Argo CD keeps re-applying the broken version: self-heal fights `kubectl rollout undo`; revert the commit in the config repo instead.
- Why did Kubernetes not roll back on its own: a Deployment never does; it only marks `ProgressDeadlineExceeded`.

**Mistakes to avoid:**
- Deleting the crashing pods, which just creates new crashing pods.
- Debugging the new version in production for half an hour while mixed versions serve.

### Q. The document-processing Python worker is OOMKilled every few hours with exit code 137. Nobody changed the code, but customers started uploading much larger PDFs. How do you handle it?
**Short answer (45 seconds):** Confirm it is the container limit and not node eviction: `kubectl describe pod` shows Last State Terminated, Reason OOMKilled, Exit Code 137. Contain by lowering concurrency or raising the limit temporarily, and make sure killed jobs are retried rather than lost. Then compare memory against the limit over time: spikes tied to certain jobs mean large inputs held in memory, a steady climb means a leak. The fix is streaming and bounded per-job memory, with the limit set from measured peaks.

**Deeper explanation:**

```bash
kubectl get pod worker-7f9c -n jobs \
  -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
kubectl top pod -n jobs -l app=worker --containers
```

```text
max by (pod) (container_memory_working_set_bytes{namespace="jobs", container="worker"})
/
max by (pod) (kube_pod_container_resource_limits{namespace="jobs", container="worker", resource="memory"})
```

Likely causes, ranked for this story:
1. Memory grows with input: the whole PDF in memory, every page rendered at once, or all chunks embedded in one batch; peak is roughly the largest job times concurrency.
2. Celery prefork children each hold their own copy of large libraries, so concurrency multiplies memory.
3. Slow growth from caches or fragmentation; `worker_max_tasks_per_child` or `worker_max_memory_per_child` recycles children as a stopgap.
4. A limit that was guessed, never measured.

To tell them apart, correlate OOM times with job IDs and file sizes in the logs, then reproduce locally with the largest file under `memray` or `tracemalloc`.

Fix: process page by page and stream results to object storage; route very large files to a separate queue with a bigger-memory worker; set concurrency explicitly; set the memory request equal to the limit. Use `task_acks_late` with `task_reject_on_worker_lost` and idempotent tasks so a killed job is redelivered, with a retry cap so it cannot loop forever.

Prevent: alert when the working set stays above 90 percent of the limit, alert on `kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}`, and add the largest allowed file to the staging load test.

**Follow-ups they will ask:**
- The same file kills every retry: a poison message; cap retries and send it to a dead-letter queue with an alert.
- The pod shows Evicted instead: the node ran short of memory, not your container.

**Mistakes to avoid:**
- Doubling the limit and closing the ticket, until the next bigger file arrives.
- Running without limits, so one job takes the node down for everyone.

### Q. During a traffic peak, new inference pods sit in Pending with "Insufficient nvidia.com/gpu" and some API pods with "Insufficient cpu". Walk me through it.
**Short answer (45 seconds):** Pending means the scheduler found no node that fits, and the FailedScheduling event says why per node, so I read it first. The real question is then why the autoscaler did not add capacity: the pool is at its maximum, the cloud has no capacity for that instance type in that zone, a new node joined but does not advertise GPUs, or requests are inflated. I contain by freeing capacity (pause batch jobs on GPUs, shed non-critical load) while fixing the scale-up.

**Deeper explanation:**

```bash
kubectl get events -n inference --field-selector reason=FailedScheduling
kubectl get events -A --field-selector reason=NotTriggerScaleUp
kubectl describe node gpu-node-a | grep -A8 -E "Capacity|Allocated resources"
kubectl get pods -A -o wide --field-selector spec.nodeName=gpu-node-a
```

GPU causes, ranked:
1. The GPU node group or Karpenter NodePool is at its limit.
2. The autoscaler tried but the provider had no capacity; on AWS this shows as `InsufficientInstanceCapacity` in the Auto Scaling activity or the Karpenter logs.
3. The node is up but `nvidia.com/gpu` is missing from its Capacity: the driver or device plugin pods of the GPU Operator are failing on the new node image.
4. Idle pods hold GPUs: a forgotten notebook or a stuck batch job.

CPU causes: requests far above real usage, so nodes are full on paper while barely used, or the CPU pool at its maximum.

Fix: raise the pool maximum or allow several GPU instance types and zones; repair the GPU Operator on the new image; delete idle GPU holders; right-size CPU requests from observed usage (a VPA in recommendation mode helps).

Prevent: alert on pods Pending longer than a few minutes (`kube_pod_status_phase{phase="Pending"}`), a dashboard of requested against allocatable GPUs, and PriorityClasses so serving preempts batch.

**Follow-ups they will ask:**
- Scale-up works but takes many minutes: node boot, driver setup, image pull and model load add up; keep warm capacity and pre-pull images.
- Pending with no GPU involved and nodes that look empty: the event text will name taints, node selectors, affinity or a topology spread rule with `DoNotSchedule`.

**Mistakes to avoid:**
- Reading `kubectl top nodes` (live usage) when the scheduler decides on requests.
- Removing the GPU taint "to get pods scheduled", which lets CPU pods fill expensive nodes.

### Q. At peak, the ingress returns intermittent 502s and 503s and events show `Readiness probe failed: Get "http://10.0.3.17:3000/ready": context deadline exceeded`. Pods are not restarting. What is going on?
**Short answer (45 seconds):** Pods are dropping out of the Service endpoints because the readiness probe times out, and when several drop at once the rest get more traffic and fail too: a feedback loop. No restarts means liveness passes, so the process is alive but slow to answer. I check CPU throttling and event loop lag first, then whether the readiness handler calls a shared dependency. I contain by scaling out and raising the probe timeout, and fix by making the probe cheap and removing the throttling.

**Deeper explanation:**

```bash
kubectl get endpointslices -n prod -l kubernetes.io/service-name=api -w
kubectl describe pod api-6d8f9-x2k4 -n prod | grep -A3 Readiness
```

```text
rate(container_cpu_cfs_throttled_periods_total{container="api"}[5m])
/
rate(container_cpu_cfs_periods_total{container="api"}[5m])
```

Likely causes, ranked:
1. The CPU limit is hit at peak, the kernel throttles the container, and the probe request waits behind real work; the default `timeoutSeconds` is 1.
2. A blocked event loop in Node (synchronous parsing of large JSON, crypto, a heavy regex), visible as `nodejs_eventloop_lag_seconds` from prom-client, or CPU-bound code inside an `async def` handler in FastAPI.
3. The readiness handler checks Postgres or Redis, so when that shared dependency slows, every pod goes unready together and the ingress has no endpoints, which is where the 503s come from.

Fix: readiness checks local state only (accepting requests, warm-up finished, not shutting down), with a timeout of two or three seconds and `failureThreshold: 3`; dependency health moves to metrics and alerts. Raise or remove the CPU limit on latency-sensitive services while keeping requests accurate, add replicas, and move CPU-heavy work to a worker or a thread.

Prevent: alert on the throttling ratio and on ready endpoints falling below a floor, and load test through the real ingress with probes enabled.

**Follow-ups they will ask:**
- Why 502s as well: the proxy sent to a pod that closed the connection; a Node `keepAliveTimeout` (5 seconds by default) shorter than the load balancer's idle timeout causes this even without probe trouble.
- Should liveness use the same endpoint: no, or the same slowness restarts pods and turns a slowdown into an outage.

**Mistakes to avoid:**
- `timeoutSeconds: 1` with `failureThreshold: 1` on readiness for a busy service.
- Pointing readiness at the database "to be thorough".

### Q. A Terraform apply in CI fails with "Error acquiring the state lock", and once you get past it, the plan wants to delete a security group rule nobody remembers adding. How do you handle it?
**Short answer (45 seconds):** These are two problems. The lock error means another run holds the lock or an earlier run died without releasing it, so I read the Lock Info, confirm no Terraform process is still running, and only then run `terraform force-unlock`. The unexpected delete is drift: someone added the rule outside Terraform, probably during an incident, and applying would silently remove it. I find out who and why before deciding to codify it or let it go.

**Deeper explanation:** The error prints a Lock Info block with the lock ID, the state path, the operation (for example `OperationTypeApply`), who holds it and when it was created. Match `Who` and `Created` against CI history: a GitHub Actions job that was cancelled or timed out kills Terraform without cleanup. If a run is genuinely still going, wait. If it died, check whether its apply half-finished, then:

```bash
terraform force-unlock 6f1c2d0e-1111-2222-3333-444455556666
terraform plan -refresh-only        # shows changes made outside Terraform, proposes no fixes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress \
  --max-results 20
```

For the drift, the plan prints "Objects have changed outside of Terraform" with the difference, and CloudTrail shows who called `AuthorizeSecurityGroupIngress` and when. If the rule is needed, add it to the code (or use an `import` block for whole resources) until the plan is clean. If it was a temporary incident change, remove it deliberately with its owner's agreement. Either way, an unrelated pull request must not carry that deletion through review unnoticed.

Prevent: a GitHub Actions `concurrency` group per stack with `cancel-in-progress: false`, so applies queue instead of colliding or being cancelled mid-write; `-lock-timeout=5m` so short overlaps wait instead of failing; a scheduled `terraform plan -detailed-exitcode` that alerts on exit code 2; read-only console roles with an audited break-glass role; and a rule that every incident change gets a follow-up pull request.

**Follow-ups they will ask:**
- Can you run with `-lock=false`: never for an apply; that is how state gets corrupted.
- The state file looks corrupted: restore the previous object version from the versioned bucket, then plan to see the gap.

**Mistakes to avoid:**
- Force-unlocking while a colleague's apply is still running.
- Approving a plan with unexpected deletes because "it is probably fine".

### Q. GitHub secret scanning flags an OpenAI API key and an AWS access key pushed to the repository in a `.env` file two days ago. What do you do, in order?
**Short answer (45 seconds):** Treat both keys as compromised from the moment of the push, so the first action is rotating them, not rewriting git history. I issue new keys, put them in the secret manager, roll the services, then deactivate and delete the old ones. Next I check whether anyone else used them: CloudTrail for the AWS key ID in every region, and the OpenAI usage dashboard. Only then do I clean the history and add guardrails so a `.env` cannot be pushed again.

**Deeper explanation:**
1. Scope: which repositories, forks, branches and CI logs contain it, and whether the repository is public.
2. Rotate: create the new OpenAI key and a new AWS credential (better, replace the static IAM user key with roles: OIDC for CI, IRSA or EKS Pod Identity in the cluster), update the secret store, restart consumers, verify traffic, then revoke the old keys.

```bash
aws cloudtrail lookup-events --region us-east-1 \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAEXAMPLEKEY \
  --query 'Events[].[EventTime,EventName,Username]'
aws iam update-access-key --user-name ci-deployer --access-key-id AKIAEXAMPLEKEY --status Inactive
aws iam delete-access-key --user-name ci-deployer --access-key-id AKIAEXAMPLEKEY
```

3. Investigate: `lookup-events` is regional, and stolen keys are often used to launch instances in regions you never use, so check them all. Look for unknown source IPs, `RunInstances`, new IAM users or access keys; on the OpenAI side, usage spikes or unknown projects. Any misuse makes this a security incident in its own right.
4. Clean history: `git filter-repo --invert-paths --path .env`, force push, have everyone re-clone, and ask GitHub support to purge cached views if needed. This is hygiene; the rotation is what made you safe.

Prevent: `.env` in `.gitignore` with a committed `.env.example`; push protection on for the organization; gitleaks or trufflehog in a pre-commit hook and in CI; spending alerts on the LLM provider account.

**Follow-ups they will ask:**
- The key was only on an unmerged feature branch: still rotate; it was pushed, so it is on the server and in clones.
- Why not just delete the commit: forks, clones, CI caches and pull request refs keep it.

**Mistakes to avoid:**
- Rewriting history first and rotating "later", leaving a live key exposed for hours.
- Revoking the old key before the new one is deployed, causing your own outage.

### Q. Users report `NET::ERR_CERT_DATE_INVALID` on the web app, and mobile API calls fail with "certificate has expired". cert-manager was supposed to renew it. Walk me through it.
**Short answer (45 seconds):** Every client that validates certificates is down, so I restore first: trigger a manual renewal, or if renewal is blocked, attach a valid certificate at the load balancer temporarily. In parallel I confirm which endpoint serves the expired certificate with `openssl s_client`, then find why cert-manager did not renew by walking its objects: Certificate, CertificateRequest, Order, Challenge. Afterwards, expiry alerts on every certificate, because renewal automation fails silently.

**Deeper explanation:**

```bash
openssl s_client -connect app.acme.com:443 -servername app.acme.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
kubectl get certificate -A
kubectl describe certificate app-tls -n web
kubectl get certificaterequest,order,challenge -n web
kubectl logs -n cert-manager deploy/cert-manager --since=24h | grep app-tls
cmctl renew app-tls -n web
```

Check the expired certificate is the one you think: a CDN, the cloud load balancer and the ingress may each terminate TLS, and `-servername` matters because SNI selects the certificate.

Likely causes of a failed renewal, ranked:
1. The HTTP-01 challenge is unreachable: a new redirect, WAF rule, auth middleware or NetworkPolicy blocks `/.well-known/acme-challenge/`.
2. DNS-01 credentials for Route 53 or Cloudflare expired or lost permissions.
3. It was never managed by cert-manager but uploaded by hand.
4. Repeated failures hit the ACME provider's rate limits.
5. cert-manager itself is down or its webhook is broken.

The Challenge's status usually states the reason plainly. After renewal, confirm the new dates from outside the cluster.

Prevent: alert when `certmanager_certificate_expiration_timestamp_seconds - time()` drops below 14 days, and probe every public hostname with the blackbox exporter's `probe_ssl_earliest_cert_expiry`, which also covers certificates cert-manager does not know about. Keep an inventory that includes internal certificates (admission webhooks, mTLS CAs, database clients); in Go-based components they fail as `x509: certificate has expired or is not yet valid`.

**Follow-ups they will ask:**
- Only some Android clients fail: an incomplete chain or an old trust store; inspect the chain with `openssl s_client -showcerts`.
- Why alert at 14 days: cert-manager renews well before expiry by default, so a certificate that close to expiry means renewal has been failing for a while.

**Mistakes to avoid:**
- Fixing the certificate but skipping the alert, so users discover the next expiry too.
- Assuming cert-manager plus Let's Encrypt means certificates can never expire.

### Q. Pods on one node are being Evicted with "The node was low on resource: ephemeral-storage" and the node shows DiskPressure. A new service went live yesterday. What do you do?
**Short answer (45 seconds):** Contain: cordon the node and find the pod filling the disk, because the kubelet is evicting innocent pods and the culprit may move to another node. Then measure what uses the space: files written inside containers, very chatty logs, or old images. The fix is to stop the writes or bound them with ephemeral-storage limits, clean up, uncordon, and alert on node disk before the kubelet has to act.

**Deeper explanation:**

```bash
kubectl describe node ip-10-0-2-41 | grep -A8 Conditions
kubectl get pods -A --field-selector spec.nodeName=ip-10-0-2-41,status.phase=Failed
kubectl cordon ip-10-0-2-41
kubectl debug node/ip-10-0-2-41 -it --image=ubuntu
# inside the debug pod the node's root filesystem is mounted at /host
du -sh /host/var/log/pods/* | sort -h | tail
du -sh /host/var/lib/containerd
```

Likely causes, ranked:
1. The new service writes files inside its container filesystem or an `emptyDir`: a debug log file, rendered PDFs in `/tmp`. Nothing rotates these, and they count as ephemeral storage.
2. Chatty stdout logging. The kubelet rotates container logs by size (`containerLogMaxSize`, default 10Mi, five files), so on Kubernetes this mostly floods the log pipeline; on plain Docker hosts the json-file driver does not rotate unless `max-size` is set.
3. Large ML images from frequent deploys piling up; image garbage collection starts at 85 percent disk usage by default.

Fix: lower the log level through config, fix the code that writes files, give the pod an `emptyDir` with `sizeLimit` or an ephemeral-storage limit so only it gets evicted, prune unused images with `crictl rmi --prune`, then uncordon.

Prevent: alert when node filesystem space (node_exporter `node_filesystem_avail_bytes`) falls below about 20 percent, ephemeral-storage requests and limits in the shared service template, and a log-volume check in the launch checklist for new services.

**Follow-ups they will ask:**
- `df` says full but `du` cannot find it: deleted files still open, often by a log agent; `lsof +L1` on the node (after `chroot /host`) finds the holder, then restart it.
- Evicted pods pile up in the list: they are Failed records that use no resources; clean them with `kubectl delete pods --field-selector status.phase=Failed`.

**Mistakes to avoid:**
- Deleting files by hand on the node and calling it fixed; the new service fills it again tonight.
- Growing the disk without finding which pod writes.

### Practice
- Break it on purpose: on a kind cluster, ship four broken versions of a small service (a missing required env var, a one-second readiness timeout under load, a memory limit below peak usage, an image tag that does not exist) and diagnose each from status, exit codes and events only, timing yourself.
- Run a pod that writes to `/tmp` in a loop until the node reports DiskPressure, read the eviction message, then add an ephemeral-storage limit and watch only that pod get evicted.
- Start a `terraform apply` against a sandbox, kill it mid-run, read the lock info, and practice the safe force-unlock sequence followed by a `-refresh-only` plan.
- Issue a short-lived certificate with a cert-manager CA issuer, break its renewal, and confirm your Prometheus expiry alert fires before it expires.
- Say it out loud: "Secret scanning just flagged an AWS key on main." Narrate the first fifteen minutes in order, including what you tell the team.
