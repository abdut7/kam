## Cloud Fundamentals & Well-Architected

### Why it exists
Before cloud providers, a team that needed a server ordered hardware weeks ahead, guessed the peak load and paid for idle machines the rest of the year. AWS turns servers, databases and networks into services you rent by the hour or by the request, spread across separate data centers (availability zones) and geographic regions. The Well-Architected Framework exists because renting is easy and designing well is not: it is a set of questions about security, reliability, cost, performance, operations and sustainability that catches the usual mistakes before production does. The trade-off is that you share responsibility with AWS, pay for every resource you forget about, and must think about failure domains that one rack in one data center never made you consider.

## IAM & Security

### Why it exists
Every AWS API call, from a laptop or from a container, has to answer two questions: who is calling, and are they allowed to do this. IAM answers both with identities, roles that hand out short-lived credentials, and policies that allow or deny specific actions on specific resources. Before roles, teams pasted long-lived access keys into config files and CI settings, and those keys leaked through Git history and lost laptops. KMS, Secrets Manager, WAF and CloudTrail complete the picture: encrypt data, keep secrets out of code, filter hostile traffic and record who did what. The cost is complexity, because policy evaluation has several layers and a missing line produces "AccessDenied" with little explanation.

## Networking

### Why it exists
A VPC gives your resources a private network inside AWS, so databases and internal services are not reachable from the internet, while load balancers, NAT gateways and endpoints control exactly which traffic gets in and out. Without it every machine would need a public address and its own firewall rules, which is how databases end up exposed. Route 53 and CloudFront add DNS routing and an edge cache near users, so traffic finds a healthy region and static files do not cross the world on every request. The price is a set of decisions that are hard to undo, such as IP ranges that must never overlap, and hidden charges for NAT processing, cross-AZ traffic and internet egress.

## Compute Options

### Why it exists
Workloads want different shapes of compute: a steady API wants always-on capacity, a burst of webhooks wants to scale from zero, and a model server wants a GPU. EC2 gives you a virtual machine you manage, containers on ECS or EKS package the app with its dependencies so it runs the same everywhere, and Lambda runs a function per event with no server to patch. Before these, teams sized physical servers for the yearly peak and deployed by copying files over SSH. Each step up in abstraction trades control for less operations work: Lambda has hard limits on duration and package size, Kubernetes has a steep learning curve, and GPUs are expensive and sometimes simply unavailable.

## Storage & Databases

### Why it exists
Applications need to keep files, records and caches somewhere that survives a crash and can be read back quickly. S3 stores objects such as uploads and backups with very high durability, EBS and EFS give disks to servers, and managed databases such as RDS, Aurora and DynamoDB take over the backups, patching, replication and failover that teams used to script by hand. The choice that matters most is the access pattern: relational queries and transactions, key lookups at huge scale, text or vector search, or hot cached reads. Managed services cost more than a self-run database on EC2 and bring limits you must design around, such as failover windows, connection caps and DynamoDB's need to know your queries up front.

## Messaging & Event-driven Architecture

### Why it exists
When one service calls another synchronously, a slow or failed dependency drags the caller down with it, and a traffic spike hits every service at once. Queues and event buses such as SQS, SNS, EventBridge, Kinesis and MSK put a buffer between producer and consumer, so work is stored safely, consumed at the pace the consumer can handle and retried when it fails. They also let one event, such as "order placed", reach many consumers without the producer knowing about them. The cost is that delivery becomes at least once and often unordered, so consumers must handle duplicates, dead-letter queues need an owner, and debugging spans several hops instead of one stack trace.

## Serverless & API Patterns

### Why it exists
Running even a small API used to mean servers that sat idle at night, operating system patches and capacity planning for traffic nobody could predict. Lambda and API Gateway let you deploy only the handler: AWS runs it per request, scales it out automatically and bills by duration and request count, so a quiet endpoint costs almost nothing. API Gateway adds authentication, throttling, API keys and WebSocket connections in front without extra code. The trade-offs are cold starts when a new environment boots, a 15 minute maximum run time, concurrency that can overwhelm a database, and a bill that overtakes containers once traffic is high and steady.

## Observability & Operations on AWS

### Why it exists
Once a system runs across many services, you cannot SSH into one box and read a log file to find out what is wrong. CloudWatch metrics, logs and alarms, X-Ray or OpenTelemetry traces, and Systems Manager give you the signals to see what is happening and the access to act without opening ports. Backups, disaster recovery plans and cost tools such as Cost Explorer and Budgets belong here too, because an outage you cannot recover from and a bill you cannot explain are both operational failures. The trade-off is that telemetry costs money and attention: high-volume logs, high-cardinality metrics and noisy alarms that wake people for nothing.

## AI Services on AWS and Equivalents

### Why it exists
Teams building AI features need models, vector search and a place to run custom models, but calling a third-party API directly can clash with data rules, procurement and existing AWS controls. Bedrock exposes models from several providers through one AWS API, so calls go through IAM, CloudTrail, VPC endpoints and the AWS bill, while SageMaker and EKS host models you train or fine-tune yourself. Knowing the GCP and Azure equivalents lets you translate a design between clouds instead of starting over. The trade-offs are model availability that varies by region, per-model quotas that throttle you at busy moments, and features that sometimes reach a provider's own API before Bedrock.

## Architecture Scenarios

### Why it exists
Knowing single services is not enough, because real systems fail at the joins between them, and interviews test whether you can combine compute, data, messaging, security and cost into one design under constraints. A worked architecture forces the questions people skip: where state lives, how each part fails, what it costs at ten times the load and how you deploy it safely. Before reference architectures were common, many teams learned these lessons through production outages. Every design carries the same trade-off: more availability, isolation and scale cost more money and more operational effort, so the right design is the simplest one that meets the stated numbers.

## Cloud Project Scenarios [Scenarios]

> Interviewers run these as a conversation: a vague goal plus one hard constraint (a regulator, a budget ceiling, a deadline, a small team), and they watch whether you clarify before you draw. A senior answer asks for the numbers and the non-negotiables first, proposes the simplest design that meets them, names the decisions that are expensive to reverse (regions, account structure, identity, data stores), and finishes with risks, a rollout plan and the metrics that prove it worked. Weak answers list services; strong answers say why each one is there, what it costs and what would make you change it.

### Concepts you must understand
- Ask for the hard constraints first: regulation and data location, RTO and RPO, latency target, load and growth, budget, team size and existing skills.
- Separate one-way doors from two-way doors: regions, account structure, IP ranges, identity provider and the primary data store are hard to change; instance sizes and replica counts are easy.
- Estimate out loud with rough numbers: requests per second, data per month, GPU hours per day, GB of egress; a stated assumption beats "it depends".
- An AWS account is the strongest boundary for security, blast radius and cost, so one account per environment and per sensitive workload is cheap insurance.
- Guardrails beat reminders: SCPs, tag policies, service quotas and Budgets actions enforce rules that a wiki page only describes.
- Every plan needs a migration path and a rollback: what runs in parallel, which metric decides the cutover, and how you go back.
- Name the success measures up front: error rate, p95 latency, cost per unit (request, tenant, thousand documents, million tokens) and the share of resources under policy.

### Q. A UAE customer's regulator requires that their data, backups and logs stay in the UAE, and your multi-tenant SaaS runs only in Mumbai. How do you design for data residency, and what changes when an Indian bank asks for the same?

**Short answer (45 seconds):** First I pin down scope with their compliance team: which data (records, files, backups, logs, traces, AI prompts), whether support access from abroad counts as a transfer, and whether disaster recovery must also be in-country. Then I deploy a separate cell in the UAE region (me-central-1) from the same infrastructure code: its own account, VPC, database, buckets, KMS keys and model endpoint. A thin global layer holds only the tenant-to-region map and routes each tenant to its cell, and an SCP pins that account to its region. For the Indian bank, Mumbai already holds the data, so the work is DR in Hyderabad (ap-south-2) and auditing every outbound path.

**Deeper explanation:**

```text
Global (no customer data): tenant directory {tenant_id -> region}, DNS, CI/CD, billing metadata
Cell me-central-1 (account uae-prod): ALB -> ECS -> Aurora, S3, KMS, logs, model endpoint
Cell ap-south-1  (account in-prod) : same stack, backups and DR copies to ap-south-2
```

Residency applies to every copy, so I audit the leaks people miss: logs and traces shipped to a central observability account elsewhere, AWS Backup copy rules, S3 replication, error trackers and LLM APIs hosted abroad, and Bedrock cross-region inference profiles, which can route a request to another region in the same geography. If a model is not offered in me-central-1, the options are self-hosting in the cell or a contract change, not a quiet call to another region. Bahrain (me-south-1) is a different country, so in-country DR on AWS means Multi-AZ plus in-region backups; if the regulator demands a second site, raise it early. The SCP denies requests whose aws:RequestedRegion is not the cell's region, with global services such as IAM, Route 53 and CloudFront exempted.

**Follow-ups they will ask:**
- One codebase or a fork: one codebase and one IaC module with region as a parameter, plus flags for services a region lacks.
- What a cell costs: a fixed floor (NAT, load balancer, Multi-AZ database), so price it into the contract or set a minimum deal size.

**Mistakes to avoid:**
- Equating residency with "the database is in the region" and forgetting logs, backups, LLM calls and support access.
- Stretching one shared database across countries and separating tenants with a region column.

### Q. A 25-person startup runs prod, staging and experiments in one AWS account with shared IAM users, and an enterprise customer's security review is in two months. Design the landing zone and the migration.

**Short answer (45 seconds):** I create a new, empty management account with AWS Organizations and Control Tower and invite the existing account in as production rather than rebuilding it, because SCPs never apply to the management account. OUs: Security (log archive, audit tooling), Infrastructure (network, shared services such as ECR), Workloads (prod, staging) and Sandbox. People sign in through IAM Identity Center federated with Google Workspace or Entra ID, with permission sets per job role, and the IAM users and their keys are deleted. An organization trail writes to the log archive, GuardDuty and Security Hub run from the audit account, and SCPs add the guardrails.

**Deeper explanation:**

```text
Management (new, empty): Organizations, Identity Center, billing
  Security OU      : log-archive, audit (GuardDuty, Security Hub, Config aggregator)
  Infrastructure OU: network (IPAM, Transit Gateway later), shared-services (ECR, CI roles)
  Workloads OU     : prod (the existing account, invited), staging (new, built from IaC)
  Sandbox OU       : one account per team, budgets, region and instance limits
```

Order matters: (1) management account and invitation; (2) Identity Center and permission sets, everyone switches, then the credential report (`aws iam generate-credential-report`) finds every remaining user and key; (3) organization trail and security services; (4) CI moves to GitHub OIDC roles per account; (5) SCPs attach to Sandbox first, then staging, then prod, after proving pipelines still deploy; (6) staging is rebuilt in its own account from IaC instead of moving resources. IPAM hands out non-overlapping ranges for every new VPC. Typical SCPs deny leaving the organization, stopping CloudTrail, GuardDuty or Config, and using unapproved regions. The evidence the reviewer wants falls out of this: MFA through SSO, immutable audit logs, separated environments and least privilege. Success looks like no IAM users, no old access keys and accounts vended in minutes.

**Follow-ups they will ask:**
- Control Tower or hand-built Terraform: Control Tower for speed and Account Factory, with AFT if the team lives in Terraform; hand-built only if you accept maintaining it.
- Break-glass access: one emergency role or user with hardware MFA, credentials sealed, and an alarm on every use.

**Mistakes to avoid:**
- Making the busy existing account the management account, where SCPs cannot protect it.
- Attaching a strict SCP to production first and blocking the deploy pipeline.

### Q. Your Node.js API runs under PM2 cluster mode on three EC2 instances, with Socket.IO and node-cron jobs inside the app, while the Python AI services already run on EKS. Move the API to containers: ECS or EKS, and what replaces each thing PM2 did?

**Short answer (45 seconds):** I list PM2's hidden duties first, because each needs a new owner: crash restarts, cluster mode across cores, zero-downtime reload, memory restarts, log files, environment config and in-process cron. The platform choice follows the people: if the team that runs EKS for the AI services can absorb one more workload, EKS wins on shared ingress, observability and IAM patterns; if the API team is separate and small, ECS Fargate is less to learn. Either way: one Node process per container with no PM2 inside, Socket.IO on the Redis adapter, and cron moved out of the app so it runs once instead of once per replica.

**Deeper explanation:**

```text
PM2 duty                    Container replacement
restart on crash            orchestrator restarts the container; liveness probe for hangs
cluster mode (-i max)       one process per container, more replicas, HPA on CPU or requests
pm2 reload                  rolling update, readiness probe, preStop delay, SIGTERM drain
max_memory_restart          container memory limit, --max-old-space-size below it
~/.pm2/logs                 JSON to stdout, Fluent Bit to CloudWatch or Loki
ecosystem.config.js env     ConfigMap, plus External Secrets synced from Secrets Manager
node-cron inside the app    Kubernetes CronJob with concurrencyPolicy: Forbid
```

Socket.IO needs care: broadcasts across replicas need the Redis adapter, and the HTTP long-polling fallback needs sticky sessions (ALB target group stickiness) unless clients are forced to WebSocket only. Node as PID 1 gets no default SIGTERM handling, so the app must drain on SIGTERM itself (stop accepting, close sockets, finish in-flight requests) or run under tini. Size each container for one event loop, about one vCPU. Cutover is weighted routing away from the EC2 target group while I watch 5xx, p95 latency and reconnects; success is zero 5xx during rollouts.

**Follow-ups they will ask:**
- Why not pm2-runtime inside the container: two supervisors hide crashes and per-process metrics from the orchestrator; one process per container keeps restarts and scaling honest.
- Jobs that must never run twice: CronJob with Forbid plus a database lock or idempotency, since Kubernetes can occasionally create a scheduled job twice.

**Mistakes to avoid:**
- Leaving node-cron in every replica, so the nightly billing job runs three times.
- Running PM2 cluster mode inside a container with a half-vCPU limit and wondering why it throttles.

### Q. Your fine-tuned vision-language model runs on vLLM on rented GPUs at a GPU cloud such as RunPod. An enterprise customer wants inference inside AWS, and finance asks whether moving everything will cost more. How do you decide and plan it?

**Short answer (45 seconds):** I split it into obligations and economics. If the customer's contract requires processing inside AWS or a given region, their traffic moves regardless of price. For the rest I measure today's reality: GPU utilization across the day, throughput per GPU at our p95 latency target, idle hours and data volume. Then I price AWS options (g6e or g5 instances on EKS or a SageMaker endpoint, On-Demand versus Savings Plans) at that measured throughput, adding egress, storage, capacity risk and on-call time. The likely result is hybrid: enterprise tenants on AWS, experiments and batch elsewhere, behind one router running the same image.

**Deeper explanation:**

```text
unit cost = GPU $/hour / (requests or tokens per hour at target p95)
          + idle hours you pay for + egress of images and results
          + weight storage and load time + engineering and on-call time
```

The GPU cloud usually offers lower hourly rates, quick access to high-end GPUs and simple per-pod billing. Its costs: customer files cross the internet from your AWS app, AWS charges egress on every GB sent out, the provider joins your compliance scope, and there is no IAM or VPC integration. AWS gives private networking, IAM, one audit boundary and commitment discounts, but new accounts start with low GPU quotas and some instance types are scarce, so request quota increases early and consider On-Demand Capacity Reservations or Capacity Blocks for planned load. The plan: a portable serving image with pinned vLLM and adapters, a router that moves one tenant at a time, shadow traffic first, and an evaluation run on both stacks, because a vLLM or driver upgrade can shift a fine-tuned model's outputs. I track p95 latency, throughput per GPU, utilization, cost per thousand requests and eval parity.

**Follow-ups they will ask:**
- Inferentia2: cheaper per token for supported models, but it needs Neuron compilation and a vision-language model may not be supported; benchmark before promising.
- Spot GPUs on AWS: fine for batch reprocessing with checkpoints, never for the interactive floor.

**Mistakes to avoid:**
- Comparing hourly sticker prices without measured throughput at the latency target.
- Sending customer data out of AWS to another provider without checking the contract and the DPA.

### Q. An insurance client uploads claim documents and photos, and their security team requires every file to be malware scanned before any service or person can read it, with an audit trail. How do you build it?

**Short answer (45 seconds):** Uploads land in a quarantine bucket through a presigned POST whose key, size range and content type my API decides, and only the scanner and a promoter service can read that bucket. GuardDuty Malware Protection for S3 scans each new object, tags it with the result and publishes the result to EventBridge; the promoter copies clean files to the processing bucket and marks the record clean, while infected files stay quarantined and alert security. OCR and LLM extraction read only from the clean bucket. Every state change goes to an audit table, and CloudTrail data events record object access.

**Deeper explanation:**

```text
React -> API (auth, tenant, size, type) -> presigned POST -> s3://claims-quarantine/{tenant}/{uuid}
GuardDuty Malware Protection -> tag GuardDutyMalwareScanStatus + EventBridge result event
EventBridge -> SQS -> promoter: NO_THREATS_FOUND -> copy to claims-clean, status=clean -> pipeline
                                THREATS_FOUND    -> stays quarantined, status=infected, alert
                                any other result -> status=scan_failed, retry, then manual review
```

Layers beyond the scanner: the promoter checks file type by magic bytes, not the extension or the browser's Content-Type, and treats password-protected archives the scanner cannot open as not clean. Both buckets use Block Public Access and SSE-KMS; with a single bucket instead, a bucket policy can deny s3:GetObject unless s3:ExistingObjectTag/GuardDutyMalwareScanStatus equals NO_THREATS_FOUND. Downloads use short-lived presigned GETs with Content-Disposition set to attachment from a separate domain, so an uploaded HTML or SVG file cannot run script in your app's origin. The promoter is idempotent because events can repeat, a lifecycle rule expires quarantine objects, and the UI says "scanning" until the record is clean. I measure p95 time to clean, scan failures and cost per GB scanned.

**Follow-ups they will ask:**
- GuardDuty or ClamAV in Lambda: GuardDuty is managed with no signatures to update and bills by data scanned; ClamAV suits custom rules or unsupported regions, but you own signature updates and Lambda size and time limits.
- Very large files: scanners have size limits, so cap size in the presigned POST policy and reject anything above it.

**Mistakes to avoid:**
- Starting processing on upload and scanning in parallel, so a parser touches the malicious file first.
- Trusting the extension or the declared Content-Type.

### Q. Your AI team now launches GPU instances for LoRA fine-tuning experiments, and spend has doubled in two months. The CFO wants a hard monthly ceiling and cost per project without slowing the team down. What do you put in place?

**Short answer (45 seconds):** I make the boundaries structural and the alerts automatic. Each team gets its own experiments account, because an account is the cleanest cost boundary. An SCP denies launching instances without project and owner tags and limits that OU to approved GPU types, and the GPU vCPU service quota becomes the real hard cap. AWS Budgets per account and per project tag alert on forecast, and a Budgets action applies a deny-launch policy at the ceiling. A scheduled job stops GPU instances idle for a set time, and training moves to jobs with a maximum runtime.

**Deeper explanation:**

```json
{
  "Sid": "DenyInstancesWithoutProjectTag",
  "Effect": "Deny",
  "Action": "ec2:RunInstances",
  "Resource": "arn:aws:ec2:*:*:instance/*",
  "Condition": { "Null": { "aws:RequestTag/project": "true" } }
}
```

A second statement denies ec2:InstanceType values outside the approved list. Tags appear in cost reports only after you activate them as cost allocation tags in the management account, and nothing can attribute spend for resources that were never tagged, so tag volumes and snapshots at launch too. Cost Categories group accounts and tags into projects for a weekly report per project. Budgets data is not real time, so a large fleet can overrun before a Budgets action fires; that is why quotas and instance type limits carry the hard stop, and an EventBridge rule on RunInstances for GPU types posts to the team channel within minutes. Idle detection needs GPU metrics, which the CloudWatch agent can collect from NVIDIA GPUs. For training, SageMaker jobs with a maximum runtime and managed Spot with checkpoints in S3 bound both duration and price. I measure the share of spend tagged, idle GPU hours per week, spend against budget per project, and how long an engineer waits for a GPU.

**Follow-ups they will ask:**
- Will the ceiling kill a run near the end: set the Budgets action to manual approval and checkpoint so a stopped job resumes.
- Self-service without tickets: a launch template or Service Catalog product with tags and instance types baked in.
- Notebooks left running overnight: SageMaker Studio idle shutdown or a lifecycle configuration.

**Mistakes to avoid:**
- Treating a Budgets email as a control; it informs, it does not stop anything.
- Enforcing tags on instances but not on volumes and snapshots.

### Practice
- Write a one-page residency design for a UAE tenant that lists every path by which data could leave the region (logs, traces, backups, LLM calls, support tools, CDN) and the control that closes each one.
- In a test organization, attach a region-deny SCP to a sandbox OU and prove that a call to another region fails while IAM and Route 53 calls still work.
- Containerize a small PM2 app: one process per container, SIGTERM drain, three replicas with the Socket.IO Redis adapter; run a rolling update with a client connected and count dropped messages.
- Load test your vLLM image on one GPU type at realistic inputs and compute cost per thousand requests at your p95 target for two providers.
- Say it out loud: present the malware-scanning upload design in three minutes and finish with the two risks you would raise with the client's security team.

## Cloud Incidents & Error Cases [Scenarios]

> Incident questions test calm sequencing more than trivia. Use the same structure every time: clarify impact (who, since when, which region, tenant or feature), contain first (roll back, shift traffic, shed load, stop the spend), diagnose with evidence (CloudTrail, CloudWatch metrics, Logs Insights, the AWS Health Dashboard), fix the cause, and prevent a repeat with an alarm, a test, a guardrail or a runbook. Say what you would look at and in what order, and what you would not do in a hurry, such as deleting resources or widening an IAM policy to "*".

### Concepts you must understand
- Always ask what changed: a deploy, a config or IaC change, a policy edit, a traffic shift, or AWS itself; the deploy log and CloudTrail answer most of it.
- "AccessDenied" means one layer said no: confirm the caller with `aws sts get-caller-identity`, then check explicit denies, resource policies, KMS key policies, SCPs and boundaries.
- Retries are both a cure and a hazard: backoff with jitter fixes throttling, while unbounded retries turn a blip into an outage and duplicate side effects.
- Separate the control plane (create, update, describe) from the data plane (reading and writing data); recovery plans must not depend on control plane calls during a regional event.
- Treat a cost spike like a security incident until proven otherwise: stop the spend, preserve evidence, then find who or what launched it.

| Symptom or error | First check | Likely causes | Fix |
|---|---|---|---|
| `AccessDenied` from S3 although the identity policy allows the action | CloudTrail event (`errorCode`, `userIdentity.arn`) and `aws sts get-caller-identity` from the workload | Wrong role, bucket ARN without `/*`, bucket policy Deny, KMS key policy, missing object without `s3:ListBucket` | Fix the layer that denied; never widen to `s3:*` |
| Lambda logs `Task timed out after 10.00 seconds` | REPORT lines: Duration against the timeout, Init Duration, Max Memory Used | Outbound call without a timeout, VPC without a NAT route, heavy init, connection per invocation | Client timeouts below the function timeout, NAT or endpoints, lazy init, RDS Proxy |
| `ThrottlingException` or `Rate exceeded` from an AWS API | CloudTrail grouped by `eventName` with throttling error codes; Service Quotas | Secrets Manager or SSM called per request, deploy tool parallelism, Bedrock tokens per minute | Cache, batch, SDK adaptive retries with jitter, quota increase |
| `AccessDenied` on `sts:AssumeRoleWithWebIdentity` from a pod | Pod env for `AWS_ROLE_ARN`, token claims against the trust policy | Old cluster's OIDC issuer in the trust, provider missing, wrong namespace or service account | Fix trust and provider, or move to Pod Identity |
| `Connection terminated unexpectedly`, then `cannot execute INSERT in a read-only transaction` | `aws rds describe-events`, `pg_is_in_recovery()` on pooled connections | Pool or pooler still on the old writer after failover, instance endpoint in config | Recycle connections, discard on SQLSTATE 25006, RDS Proxy |
| Duplicate side effects and a growing dead-letter queue | Processing time against `VisibilityTimeout`, `ApproximateReceiveCount` | Visibility timeout too short, whole-batch retries, crash before delete | Heartbeat, partial batch response, idempotency keys, then redrive |
| NAT gateway `BytesOutToDestination` and the bill jump after a deploy | Cost Explorer by usage type, VPC Flow Logs top talkers | Image pulls or S3 traffic through NAT, a chatty new dependency | S3 gateway endpoint, ECR endpoints, fix the client |
| Old UI after a deploy, or `ChunkLoadError` in the console | `curl -I` on `index.html`: `x-cache`, `age`, `cache-control` | Long TTL on `index.html`, old chunks deleted, SPA fallback masking missing files | `no-cache` on `index.html`, immutable assets, keep old chunks, invalidate `/index.html` |
| Anomaly alert: GPU instances in a region you never use | `describe-instances` and CloudTrail `RunInstances` in that region | Forgotten experiment, leaked access key used for crypto mining | Contain credentials, snapshot, terminate, open a support case |
| 5xx in one region while AWS Health shows an open event | Health event scope against your per-AZ dashboards | Regional or zonal service impairment, a single-AZ dependency | Zonal shift, kill switches, capped retries, runbook failover |
| ECS task stopped with `CannotPullContainerError` | Stopped reason, route from private subnets to ECR | No NAT route, missing ECR and S3 endpoints, execution role lacks ECR access | Add the route or endpoints, fix the execution role |
| Fargate `ResourceInitializationError: unable to pull secrets or registry auth` | Execution role and network path to Secrets Manager | Missing `secretsmanager:GetSecretValue` or `kms:Decrypt`, no endpoint or NAT | Fix the execution role, add the endpoint |
| ALB 502 spikes at idle or during deploys | `HTTPCode_ELB_502_Count`, the app's keep-alive setting | Node `keepAliveTimeout` shorter than the ALB idle timeout, tasks killed before draining | Raise `server.keepAliveTimeout` above the ALB idle timeout, drain on SIGTERM |
| `InsufficientInstanceCapacity` when launching GPU instances | Instance type and AZ, quota versus capacity | No capacity for that type in that AZ right now (`VcpuLimitExceeded` is the quota instead) | Other AZs or types, a capacity reservation or Capacity Blocks |

### Q. A worker on ECS gets `AccessDenied` reading objects in `claims-clean`, although its role policy allows `s3:GetObject` on that bucket. What do you check, in order?

**Short answer (45 seconds):** I confirm who is actually calling and what was denied before touching any policy: the CloudTrail event (errorCode, userIdentity ARN, bucket and key) and the identity the task really runs as. Then I walk the layers that can still say no: the resource ARN in the allow, whether the object exists, an explicit Deny in the bucket policy, the KMS key policy, the VPC endpoint policy, then SCPs and boundaries. The fix goes into the layer that denied, never into a wider policy.

**Deeper explanation:**

```bash
aws sts get-caller-identity                     # run in the task: is this the task role?
aws s3api head-object --bucket claims-clean --key t1/abc.pdf   # 403 or 404?
aws s3api get-bucket-policy --bucket claims-clean --query Policy --output text
```

Ranked causes: (1) permissions were added to the execution role, which ECS uses to pull images and secrets, not the task role the app runs as; (2) the allow names `arn:aws:s3:::claims-clean`, but object actions need `arn:aws:s3:::claims-clean/*`; (3) the object does not exist, and without s3:ListBucket S3 returns 403 instead of 404, so a wrong key looks like a permission problem; (4) a bucket policy Deny on aws:SourceVpce while the task reaches S3 through NAT or another VPC; (5) SSE-KMS with a key policy that does not let the role decrypt, visible as a failed Decrypt in CloudTrail at the same moment; (6) an endpoint policy listing only some buckets; (7) objects written by another account under ACLs, so the bucket owner does not own them. Newer AccessDenied messages often name the policy type that denied.

Prevent it with Access Analyzer policy checks in CI, the caller identity logged at startup, and a deploy smoke test that reads a canary object through the real role.

**Follow-ups they will ask:**
- Only some objects fail: different KMS keys, object ownership, or a tag condition such as a scan status.
- Cross-account bucket: both the identity policy and the bucket policy must allow, plus the key policy in the owning account.

**Mistakes to avoid:**
- Granting s3:* on * to unblock, which hides the cause and leaves a hole.
- Editing the execution role while the app runs as the task role.

### Q. After a release, a Node.js Lambda behind API Gateway logs `Task timed out after 10.00 seconds` on a share of requests, and p99 latency triples. Walk me through the first 30 minutes.

**Short answer (45 seconds):** If the timing matches the release, I contain first: point the live alias back at the previous version and confirm errors drop. Then I use the REPORT lines to separate cold start cost from steady slowness, and traces to find which call hangs. The usual culprits are a new call without a timeout, a new VPC attachment without internet access, or heavier initialization.

**Deeper explanation:**

```text
filter @type = "REPORT"
| stats count(*) as calls, count(@initDuration) as coldStarts,
        avg(@initDuration) as avgInit, pct(@duration, 99) as p99 by bin(5m)
```

If cold starts and Init Duration jumped, the release made initialization heavier: a bigger bundle, a whole SDK imported, or a top-level await that fetches secrets and opens a database connection. If durations pile up exactly at the timeout, something waits forever. Ranked: (1) a new LLM or partner API call with no client timeout, so Lambda kills the function instead of the code failing fast; (2) the release attached the function to a VPC to reach RDS, and private subnets without a NAT route make every internet call hang until the timeout; (3) memory lowered in the same change, which also cuts CPU; (4) a new Postgres connection per invocation exhausting the database's connection limit; (5) provisioned concurrency configured on the old version number, so the new version cold starts at peak. X-Ray or OpenTelemetry segments show which call eats the time.

The fix is code, not a bigger timeout: AbortSignal.timeout on every outbound call, shorter than the function timeout; initialization cached in lazy promises; RDS Proxy for connections; NAT or VPC endpoints where needed. Prevent it with CodeDeploy canary deployments that roll back automatically on Errors or Duration alarms, a bundle size check in CI, and alarms on p99 Duration and cold start rate.

**Follow-ups they will ask:**
- Why not raise the timeout: API Gateway's integration timeout caps you anyway, users still wait, and longer durations raise concurrency and cost.
- Timeouts only at peak: a saturated dependency or database; cap the function with reserved concurrency and queue the work.

**Mistakes to avoid:**
- Debugging in production for an hour before rolling back.
- Setting the timeout to 15 minutes and calling it fixed.

### Q. During an Aurora PostgreSQL failover the Node.js API logged `Connection terminated unexpectedly`, and ten minutes later some writes still fail with `cannot execute INSERT in a read-only transaction`. What happened and what do you do?

**Short answer (45 seconds):** The first error is the normal cost of a failover; the second means part of the pool is connected to the old writer, which came back as a reader. I contain it by recycling connections now, with a rolling restart of the API tasks, so every connection resolves the cluster endpoint again. Then I find out why connections reached the wrong instance: a stale DNS answer cached somewhere, a pooler holding server connections, or a connection string naming an instance endpoint. The lasting fix is a pool that discards connections on these errors, plus RDS Proxy.

**Deeper explanation:**

```bash
aws rds describe-events --source-type db-cluster --source-identifier orders-aurora --duration 120
aws rds describe-db-clusters --db-cluster-identifier orders-aurora \
  --query 'DBClusters[0].DBClusterMembers[].[DBInstanceIdentifier,IsClusterWriter]'
```

The events show when and why the failover happened. Through the app's own pool, `SELECT pg_is_in_recovery(), inet_server_addr();` returns true on a reader and shows which instance a connection sits on. Ranked causes: (1) the pool reconnected while a resolver cache still returned the old writer's address; (2) a PgBouncer sidecar kept its server connections on the old writer; (3) the config uses an instance endpoint; (4) writes go through the reader endpoint by mistake.

```js
const client = await pool.connect();
let broken;
try { return await client.query(sql, params); }
catch (err) {
  if (err.code === "25006" || /terminated unexpectedly/i.test(err.message)) broken = err;
  throw err;               // caller retries idempotent writes once, with backoff
} finally {
  client.release(broken);  // a truthy argument destroys the connection
}
```

SQLSTATE 25006 is read_only_sql_transaction. A maximum connection lifetime (`maxLifetimeSeconds` in node-postgres) limits how long any stale connection survives. RDS Proxy keeps client connections open and reconnects to the new writer for you, the bigger win when many tasks or Lambdas share the cluster. Prevent a repeat with a failover drill under load in staging (`aws rds failover-db-cluster`), an alarm on 25006 errors and a canary that writes every minute.

**Follow-ups they will ask:**
- Transactions in flight at failover: they are lost and the client sees errors; only idempotent operations may retry automatically.
- Lambdas on the same cluster: put RDS Proxy in front, since every environment holds its own connection.

**Mistakes to avoid:**
- Rebooting or failing over again, which repeats the problem.
- Blindly retrying non-idempotent writes after connection errors.

### Q. Users receive the same notification email two or three times, and the worker's dead-letter queue keeps growing even though the logs show every job finishing successfully. What is going on?

**Short answer (45 seconds):** This pattern almost always means processing now takes longer than the queue's visibility timeout. The message reappears while the first worker is still busy, a second worker sends the email again, and the first worker's late delete uses an outdated receipt handle, which can return success without removing the message. Each receive raises the receive count until the message lands in the DLQ despite being handled. I contain it by raising the visibility timeout and adding an idempotency check before sending, and I hold off on redriving the DLQ until duplicates are impossible.

**Deeper explanation:**

```bash
aws sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names VisibilityTimeout RedrivePolicy ApproximateNumberOfMessagesNotVisible
aws sqs set-queue-attributes --queue-url "$QUEUE_URL" --attributes VisibilityTimeout=600
```

Diagnosis: compare the worker's p99 processing time with VisibilityTimeout, and check whether a recent change added an LLM call or a slower email provider. In CloudWatch, NumberOfMessagesReceived running well above NumberOfMessagesSent means redeliveries, and DLQ messages carry a high ApproximateReceiveCount. Ranked causes: (1) processing longer than the visibility timeout; (2) a Lambda consumer without ReportBatchItemFailures, so one failure retries the whole batch, or a queue visibility timeout below the AWS recommendation of six times the function timeout; (3) the worker crashing or being killed after sending but before deleting; (4) upstream at-least-once duplicates from SNS or S3 events.

The fix: a visibility heartbeat with ChangeMessageVisibility for long jobs, deletes with the latest receipt handle, an idempotency record keyed by notification ID written with a conditional insert before sending, and the provider's idempotency key if it has one. Once that is live, redrive with `aws sqs start-message-move-task --source-arn "$DLQ_ARN" --max-number-of-messages-per-second 10`; messages already handled become no-ops. Prevent a repeat with an alarm on DLQ depth above zero, a processing-time alarm at half the visibility timeout, and a test where a job outlives the timeout.

**Follow-ups they will ask:**
- Would FIFO fix it: no, deduplication covers sends within five minutes, not redelivery after the visibility timeout expires.
- Raise maxReceiveCount: it only delays the DLQ while duplicates continue.

**Mistakes to avoid:**
- Redriving the whole DLQ before idempotency exists, which sends every email again.
- Treating "logs say success" as proof the message was deleted.

### Q. After moving workloads to a new EKS cluster, a pod fails with `AccessDenied` on `sts:AssumeRoleWithWebIdentity`, while the same manifests worked on the old cluster. How do you debug it?

**Short answer (45 seconds):** A new cluster has a new OIDC issuer URL, so my first suspect is a role trust policy that still names the old cluster's identity provider, or a provider that was never registered in IAM for the new one. I confirm the pod has the IRSA environment variables, read the issuer, subject and audience claims from its token, and compare them exactly with the trust policy. The fix is registering the new provider and trusting it, or moving to EKS Pod Identity so trust no longer depends on a cluster.

**Deeper explanation:**

```bash
kubectl -n api exec deploy/orders-api -- env | grep AWS_   # AWS_ROLE_ARN, token file path
aws eks describe-cluster --name prod-2 --query cluster.identity.oidc.issuer --output text
aws iam list-open-id-connect-providers
aws iam get-role --role-name orders-api --query Role.AssumeRolePolicyDocument
```

Ranked causes: (1) the trust policy's Federated principal and its `oidc.eks.ap-south-1.amazonaws.com/id/OLDID:sub` condition reference the old issuer; (2) no IAM OIDC provider exists for the new issuer, which `eksctl utils associate-iam-oidc-provider --cluster prod-2 --approve` creates; (3) the namespace or service account name changed, but sub must equal `system:serviceaccount:api:orders-api`; (4) the aud condition does not match `sts.amazonaws.com`. If the error instead names the node instance role failing on s3:GetObject, injection never happened (the pod predates the annotation, or the webhook did not run) and the SDK fell back to the node role. With Pod Identity the checks differ: the agent add-on runs, an association exists for that namespace and service account, and the trust allows `pods.eks.amazonaws.com` for sts:AssumeRole and sts:TagSession. If the pod chains into a cross-account role, that sts:AssumeRole needs trust on the target role and permission on the pod's role.

Prevent it by generating trust policies in IaC from the cluster's issuer output, a post-provisioning smoke test running `aws sts get-caller-identity` per service account, and Pod Identity for clusters you expect to replace.

**Follow-ups they will ask:**
- Blue-green clusters with IRSA: trust both providers during the migration, then remove the old one.
- Why not the node role: every pod on the node would share it.

**Mistakes to avoid:**
- Loosening sub to a StringLike wildcard so any service account in the cluster can assume the role.
- Annotating the service account and forgetting that running pods get the role only after a restart.

### Q. Error rates climb in your primary region and the AWS Health Dashboard shows an open issue for a service you depend on. What do you do in the first hour?

**Short answer (45 seconds):** I confirm scope and impact from our own metrics, not only the status page: which service, one AZ or the whole region, which features and tenants. I declare an incident with one commander and start customer updates. I contain inside the region first: shift away from an impaired AZ, switch off features that depend on the broken service, queue writes that can wait, and cap retries so we add no load. I fail over to the DR region only if the runbook's criteria are met and the path is tested, using data plane mechanisms.

**Deeper explanation:**

```text
0-10 min : confirm with per-AZ dashboards and error codes, declare, assign commander and comms
10-25 min: contain in region: zonal shift if one AZ, kill switches, shed non-critical load, cap retries
25-40 min: decide: expected duration and impact against RTO and RPO, using pre-agreed criteria
40-60 min: execute, post status every 30 minutes, plan the recovery surge
```

The Health Dashboard's account view shows events affecting your resources; route Health events to EventBridge ahead of time, since the Health API itself needs a Business or Enterprise support plan. Your alarms often fire before the public status changes, so act on your data. Control plane operations such as launching instances, resizing Auto Scaling groups or editing DNS records through the API may be impaired, so recovery should not depend on them: Route 53 health checks and Application Recovery Controller routing controls are data plane, and capacity already running in healthy AZs (static stability) beats capacity you hope to launch. AI features can fall back to another region's model endpoint or a non-AI path. When the service recovers, queued messages and client retries arrive together, so drain backlogs at a controlled rate. Afterwards, list every hidden single-region dependency the event exposed (identity provider, ECR, secrets, third-party APIs) and test the fixes in a game day.

**Follow-ups they will ask:**
- Only one AZ affected: ARC zonal shift moves load balancer traffic away from that AZ while the others keep serving.
- Failing back: a planned move after data resynchronizes, never an automatic flip.

**Mistakes to avoid:**
- Failing over in a panic to an untested region and creating a second outage.
- Letting clients retry aggressively and amplifying the problem.

### Q. Finance forwards a Cost Anomaly Detection alert: EC2 spend jumped overnight, mostly GPU instances in a region your team never uses. What do you do?

**Short answer (45 seconds):** I treat it as a security incident until I can prove it is not one. I list the running instances in that region and use CloudTrail in the same region to see which principal launched them, from which IP and with which credentials. If it is a known engineer's forgotten experiment, I confirm with them, save what they need and terminate. If the principal is unexpected, I contain first: disable the credential, revoke sessions, snapshot for evidence, stop the instances, hunt for persistence in every region, then open a support case about the charges.

**Deeper explanation:**

```bash
aws ec2 describe-instances --region eu-north-1 \
  --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,LaunchTime,Tags]'
aws cloudtrail lookup-events --region eu-north-1 \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances --max-results 20
aws iam update-access-key --user-name ci-legacy --access-key-id AKIAEXAMPLE --status Inactive
```

CloudTrail event history is regional, which is why the lookup targets the region where the instances run. Signs of compromise: a long-lived key from an old IAM user, a source IP outside your ranges, many regions hit at once, and GuardDuty findings such as `CryptoCurrency:EC2/BitcoinTool.B!DNS`. Attackers also leave persistence, so check for new IAM users and keys, Auto Scaling groups, launch templates and Spot requests that would relaunch instances after you stop them. Stopped instances still bill for EBS, so terminate once evidence is captured. For a role, "revoke active sessions" adds a deny on tokens issued before that moment.

Prevention is the same set of guardrails either way: an SCP denying unused regions, an instance type allowlist, low GPU quotas in regions you do not use, GuardDuty in every region, an EventBridge rule on RunInstances for GPU types that alerts in minutes, tags and an idle reaper for experiments, and anomaly alerts routed to on-call rather than only to finance.

**Follow-ups they will ask:**
- Why the budget did not catch it: billing data lags by hours, so CloudTrail-driven rules catch launches first.
- Will AWS refund it: explain in a support case; charges from unauthorized use may be reviewed, but never promise credits.

**Mistakes to avoid:**
- Terminating everything before reading CloudTrail, destroying the evidence of how they got in.
- Cleaning up the instances but leaving the leaked credential active.

### Q. After a frontend deploy, some users still see the old React app and others get a blank page with `ChunkLoadError` or `Failed to fetch dynamically imported module` in the console. The SPA is served from S3 through CloudFront. What happened?

**Short answer (45 seconds):** Usually two caching mistakes at once. index.html is cached at the edge or in the browser for too long, so some users still load the old HTML; and the deploy deleted the previous build's hashed chunks, so anyone holding old HTML, including open tabs, requests files that no longer exist. I contain it by restoring the previous assets from S3 versioning or the last build artifact and invalidating `/index.html`. Then I fix the headers and the upload order so it cannot repeat.

**Deeper explanation:**

```bash
curl -sI https://app.example.com/index.html | grep -iE 'x-cache|^age|cache-control|etag'
curl -sI https://app.example.com/assets/index-3f9a1c.js | grep -iE 'x-cache|content-type'
aws cloudfront create-invalidation --distribution-id E123EXAMPLE --paths "/index.html"
```

`x-cache: Hit from cloudfront` with a large `age` and an ETag that differs from the new object means a stale edge copy. A JavaScript URL that returns `text/html` means a missing file: S3 behind origin access control returns 403 for a missing key, the distribution's custom error response maps 403 to /index.html, and the browser parses HTML as a script, which surfaces as a chunk load error or `Unexpected token '<'`. Other causes: a cache policy whose minimum TTL exceeds the max-age set on index.html, so CloudFront keeps it anyway, and an old service worker serving a cached app shell.

```bash
aws s3 sync dist/assets s3://web-prod/assets --cache-control "public,max-age=31536000,immutable"
aws s3 cp dist/index.html s3://web-prod/index.html --cache-control "no-cache"
```

Upload hashed assets first and index.html last, never with `--delete`; a cleanup job removes assets older than a few releases. Scope the SPA fallback to navigation paths, for example with a CloudFront Function that rewrites only extensionless URLs, so a missing script returns a real 404. In the app, catch chunk load failures and reload once. Prevent a repeat with a post-deploy smoke test that fetches index.html through CloudFront and checks every referenced asset returns 200 with a JavaScript content type.

**Follow-ups they will ask:**
- Why not invalidate `/*` on every deploy: it does not clear browser caches, and versioned filenames already solve assets; invalidate index.html only.
- API responses look stale too: check that the `/api/*` behavior uses a no-caching policy.

**Mistakes to avoid:**
- Mapping every 403 and 404 to index.html, which hides missing assets.
- Deploying with `s3 sync --delete` while users still hold the old HTML.

### Practice
- Break it on purpose: in a sandbox, set an SQS queue's visibility timeout to 10 seconds and run a worker that takes 30 seconds per message; watch duplicates and the DLQ fill, then fix it with a visibility heartbeat and an idempotency table and redrive with `start-message-move-task`.
- Run `aws rds failover-db-cluster` on a staging Aurora cluster under a load generator and count failed requests with and without RDS Proxy.
- Deploy an SPA with `index.html` cached for a day and `aws s3 sync --delete`, reproduce the `ChunkLoadError`, then fix the headers and the upload order and prove old tabs keep working.
- Write a runbook for "unexpected GPU spend" with the exact commands for one region and a loop over all enabled regions.
- Say it out loud: walk through the S3 AccessDenied checklist in 90 seconds, in order, without notes.
