# Cloud & AWS

> This track covers how AWS is actually put together: regions and accounts, identity, networking, compute, storage, messaging, serverless, observability, and the AI services layered on top, plus the GCP and Azure equivalents so earlier GCP experience transfers. Interviewers for AI Full Stack roles rarely want certification trivia. They want to hear that you can place a Node.js API, a Python worker, a Postgres database and an LLM pipeline on the right services, keep them secure and observable, and explain what each choice costs and how it fails. The goal is answers you can say out loud and defend under follow-up.

## Cloud Fundamentals & Well-Architected

> Interviewers open with fundamentals to check whether you think in failure domains and cost, or just in service names. A weak answer lists regions and pillars. A strong answer says what you would put in one AZ, what in three, what in two regions, and what each step costs and protects against. Expect follow-ups that push on "why" and "what breaks".

### Concepts you must understand
- A region is a geographic cluster of isolated availability zones; an AZ is one or more data centers with independent power, cooling and networking, close enough for synchronous replication but far enough apart that one failure rarely takes out another.
- Regional services (S3, DynamoDB, SQS, Lambda) are multi-AZ by design; you only get multi-AZ for EC2, EBS, RDS and ElastiCache if you place resources in more than one AZ yourself.
- Shared responsibility: AWS secures the cloud (facilities, hardware, hypervisor, managed service software) and you secure what is in it (data, IAM, OS patches on EC2, network rules, encryption settings, application code); the line moves toward AWS as the service gets more managed.
- The six Well-Architected pillars are Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization and Sustainability; each is a set of questions to ask in a design review, not a list to recite.
- Pricing models: On-Demand (no commitment), Reserved Instances and Savings Plans (one or three year commitment for a discount), Spot (spare capacity that can be reclaimed with a two minute warning), plus data transfer and request charges that exist in every model.
- Managed services trade control and raw unit cost for lower operational load; the question is what your team's time is worth and what you lose by not having root.
- Multi-cloud in practice means one primary cloud plus specific services elsewhere (a model API, an identity provider, an acquired product), not the same workload running on two clouds.
- High availability keeps serving through component failure, fault tolerance means no visible interruption at all, and disaster recovery is how you come back after a region-scale or data-loss event, measured by RTO and RPO.

### Q. Walk me through regions, availability zones and edge locations. What do you spread across AZs, and what across regions?

**Short answer (45 seconds):** A region is an isolated geography made of several availability zones; an AZ is one or more data centers with independent power, cooling and networking, joined to the other AZs by low latency private links. I spread compute and the database across two or three AZs in one region, because the latency allows synchronous replication and load balancing. I add a second region only for disaster recovery, data residency or distant users, because cross-region replication is asynchronous and every piece of state needs its own plan.

**Deeper explanation:** Inside a region an ALB spans subnets in several AZs, an Auto Scaling group rebalances across them, RDS Multi-AZ keeps a synchronous standby in another AZ, and regional services such as S3, SQS, DynamoDB and Lambda are already multi-AZ. Edge locations are a separate layer where CloudFront, Route 53 and Global Accelerator terminate TLS, cache content and resolve DNS close to the user.

```text
Region (ap-south-1)
  AZ a: public subnet (ALB) | private subnet (API, RDS primary)
  AZ b: public subnet (ALB) | private subnet (API, RDS standby)
  AZ c: public subnet (ALB) | private subnet (API)
Edge: CloudFront + Route 53 in front
```

Multi-region adds asynchronous replication (Aurora Global Database, S3 Cross-Region Replication, DynamoDB global tables), DNS failover and a decision about which region accepts writes. That is where RPO stops being zero.

**Follow-ups they will ask:**
- Why not a single AZ: one AZ event takes the whole app down, and the EC2 region-level SLA only applies when you deploy across more than one.
- Whether cross-AZ traffic costs money: yes, per GB in each direction, so chatty services should be AZ-aware.
- What a Local Zone is: an AWS extension in a metro area for very low latency to users there, attached to a parent region.

**Mistakes to avoid:**
- Saying "multi-region for high availability" without naming how state replicates and which region writes.
- Assuming every service is multi-AZ automatically; EC2, EBS, single-AZ RDS and single-node ElastiCache are not.

### Q. Explain the shared responsibility model with concrete examples for EC2, RDS and Lambda.

**Short answer (45 seconds):** AWS is responsible for security of the cloud: physical sites, hardware, the hypervisor and the software of managed services. The customer is responsible for security in the cloud: data classification and encryption choices, IAM, network configuration, and whatever runs above the line AWS stops at. On EC2 that line is low, so I patch the OS; on RDS AWS patches the engine but I own users, parameters, encryption and backups; on Lambda AWS owns the runtime and I own my code, its dependencies and the role it runs with.

**Deeper explanation:** The useful mental model is a stack. For EC2 you own guest OS patching, host firewall (security groups), disk encryption and the application. For RDS you lose OS access, AWS handles patching windows, storage and failover, but a public RDS endpoint with a weak password is still your incident. For Lambda you own the handler, third-party packages (a vulnerable npm dependency is yours), environment variables and secrets handling, and the execution role.

| Layer | EC2 | RDS | Lambda |
|---|---|---|---|
| Physical, hypervisor | AWS | AWS | AWS |
| OS and runtime patching | You | AWS | AWS |
| Network exposure | You | You | You (VPC optional) |
| Data, encryption, IAM | You | You | You |

**Follow-ups they will ask:**
- Who is responsible when an S3 bucket is public: you; AWS provides Block Public Access and Access Analyzer, but the configuration is yours.
- What AWS Artifact is: the portal where AWS publishes its compliance reports (SOC, ISO, PCI) that you inherit as evidence.
- Whether AWS encrypts data for you: at rest it is often on by default (EBS, S3), but key management, in-transit TLS and application-level encryption remain your decisions.

**Mistakes to avoid:**
- Saying "AWS handles security" for managed services; misconfiguration and over-permissive IAM are the top causes of cloud breaches and both sit on your side.
- Forgetting application dependencies; a compromised package in your Lambda bundle is not AWS's problem.

### Q. What are the Well-Architected pillars, and how would you actually use them in a design review rather than just naming them?

**Short answer (45 seconds):** The six pillars are Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization and Sustainability. In a design review I use them as six lenses to ask questions in turn: how do we deploy and observe this, who can access what, what happens when a dependency fails, is the service choice sized to the load, what does it cost at ten times the traffic, and are we wasting resources. The output is a list of risks with owners, not a score.

**Deeper explanation:** Each pillar has design principles that are more useful than the pillar name. Reliability says to test recovery procedures, scale horizontally, stop guessing capacity and automate change. Security says to apply least privilege at every layer, enable traceability, protect data in transit and at rest, and prepare for incidents. Cost Optimization says to adopt a consumption model and measure efficiency, which in practice means tagging, budgets and reviewing idle resources monthly. Performance Efficiency says to use serverless and managed services where they fit and to experiment often. Operational Excellence is runbooks, infrastructure as code and small reversible changes. Sustainability largely coincides with cost: right-size, scale to zero, pick efficient instance families.

The AWS Well-Architected Tool in the console walks a workload through these questions and produces high and medium risk items; lenses such as the Serverless Lens and Machine Learning Lens add domain-specific questions.

**Follow-ups they will ask:**
- Which pillar teams neglect most: Reliability testing; everyone has Multi-AZ, few have actually failed over on purpose.
- How Sustainability differs from cost: it also covers data retention and choosing regions with cleaner energy, but the levers overlap heavily.
- Give one trade-off between pillars: Multi-AZ RDS doubles database cost (Reliability vs Cost); provisioned concurrency buys latency with idle spend (Performance vs Cost).

**Mistakes to avoid:**
- Reciting five pillars; Sustainability has been the sixth since 2021.
- Treating the review as a one-time gate instead of something re-run after major changes.

### Q. Compare On-Demand, Reserved Instances, Savings Plans and Spot. How would you mix them for a web API plus a nightly batch job?

**Short answer (45 seconds):** On-Demand is pay as you go with no commitment and the highest unit price. Reserved Instances and Savings Plans give a discount for a one or three year commitment; Savings Plans commit to an hourly spend and are far more flexible, and the Compute Savings Plan also covers Fargate and Lambda. Spot is spare capacity at a steep discount that AWS can reclaim with a two minute notice. For a web API I cover the steady baseline with a Savings Plan, scale the peaks on On-Demand, and run the nightly batch on Spot with checkpointing.

**Deeper explanation:** Reserved Instances come in Standard and Convertible flavors; Savings Plans replace most of that. The EC2 Instance Savings Plan ties you to an instance family in a region, while the Compute Savings Plan applies across families, sizes, regions, Fargate and Lambda. Both are "use it or lose it" per hour, so commit to the floor you are confident about, which Cost Explorer recommends after a few weeks of traffic.

Spot interruptions are announced through the instance metadata endpoint and EventBridge. Spot suits stateless or checkpointable work: batch ETL, CI runners, training with checkpoints, and even part of a stateless API tier if you diversify across many instance types with a capacity-optimized allocation strategy.

```text
Web API : baseline 4 instances -> Compute Savings Plan
          peak +6 instances    -> On-Demand via ASG
Batch   : 20 instances 1am-3am -> Spot, mixed families, retries on interruption
```

**Follow-ups they will ask:**
- What a Capacity Reservation is: a guarantee that On-Demand capacity exists in an AZ; it has no discount by itself but stacks with Savings Plans.
- How you handle a Spot interruption in a worker: catch the notice, stop taking new messages, let SQS visibility timeout return in-flight work to the queue.
- Whether Lambda has reserved pricing: the Compute Savings Plan applies to Lambda duration charges.

**Mistakes to avoid:**
- Recommending three year Standard RIs for a startup whose architecture will change; flexibility is worth the smaller discount.
- Putting a stateful database primary on Spot.

### Q. When do you choose a managed service over running it yourself? Give me a database example and a messaging example.

**Short answer (45 seconds):** I default to managed when the service is undifferentiated for the business and the team is small, and I self-manage only when I need a capability the managed version blocks, or the scale makes the managed premium real money. For Postgres that means RDS or Aurora over Postgres on EC2 unless I need an extension or a superuser-level tweak RDS does not allow. For Kafka that means MSK over self-run brokers unless we already have Kafka operators on staff, and I would still ask whether SQS or EventBridge solves the actual problem.

**Deeper explanation:** Self-managing Postgres means owning backups and restore tests, replication, failover, minor version upgrades, OS patching, disk growth and monitoring. RDS gives you automated backups with point in time recovery, Multi-AZ failover, read replicas and Performance Insights, at the cost of no shell, an extension allowlist and parameter groups instead of editing postgresql.conf. Aurora adds storage that grows automatically and faster failover, at a higher price point.

For messaging the gap is larger. Running Kafka means KRaft or ZooKeeper, broker sizing, partition rebalancing and upgrades. MSK removes most of that, but Kafka is still a heavy abstraction for a team that needs a work queue. SQS has no servers, no partitions to balance and near-unlimited throughput for standard queues. The managed question is really "do I need Kafka semantics (ordering per key, replay, many consumers) or just reliable delivery".

**Follow-ups they will ask:**
- When RDS is the wrong choice: when you need an unsupported extension, want to tune the OS, or run at a scale where a dedicated DBA team beats the RDS premium.
- How to keep an exit path: use standard Postgres and Kafka APIs, keep infrastructure in Terraform, avoid proprietary features you cannot replicate.
- Does managed mean no ops: no, you still own schema, indexes, connection pooling, alarms and capacity.

**Mistakes to avoid:**
- Claiming self-managed is cheaper by comparing only instance prices and ignoring engineer hours and incident risk.
- Choosing MSK because Kafka sounds senior when the workload is a simple job queue.

### Q. What does multi-cloud look like in practice, and when is it a mistake?

**Short answer (45 seconds):** In practice most companies are one primary cloud plus a few services from elsewhere: Gemini on Vertex AI or OpenAI models on Azure while infrastructure lives on AWS, or a second cloud inherited through an acquisition. Running the same workload on two clouds for portability is rare and usually a mistake, because it forces lowest common denominator architecture, doubles the identity and networking surface, and pays egress both ways. I keep portability where it is cheap: Kubernetes, Terraform, OpenTelemetry, Postgres and S3-compatible APIs.

**Deeper explanation:** The hidden costs of multi-cloud are operational. Each cloud has its own IAM model, networking primitives, monitoring stack and billing quirks, so your team needs twice the expertise or ends up shallow in both. Data gravity matters: moving terabytes between clouds costs real money and latency, so the compute tends to follow the data anyway. Where multi-cloud is legitimate: regulatory requirements for a specific region or sovereign cloud, a best-of-breed AI model only available on one platform, and genuine negotiation leverage at very large spend.

For AI teams the common pattern is "AWS for the platform, model calls wherever the model lives". That is fine as long as you abstract the model client behind an interface, log tokens and latency per provider, and handle different auth flows (IAM for Bedrock, API keys for direct vendor APIs, workload identity federation for GCP).

**Follow-ups they will ask:**
- How you would call a GCP service from AWS securely: workload identity federation, exchanging the AWS role identity for a short-lived Google token instead of storing a service account key.
- What you would standardize to keep options open: Terraform modules, container images, OpenTelemetry, SQL databases, and a provider-neutral LLM client layer.
- Is Kubernetes real portability: for stateless services mostly yes; databases, queues, IAM and load balancers still differ.

**Mistakes to avoid:**
- Pitching multi-cloud as a disaster recovery strategy; multi-region on one cloud is simpler and almost always sufficient.
- Ignoring egress charges when designing cross-cloud data flows.

### Q. Define high availability, fault tolerance and disaster recovery. A product manager says one AZ is fine for now. How do you respond?

**Short answer (45 seconds):** High availability means the system keeps serving through component failure, usually with brief degradation, such as an ALB routing around a dead instance or RDS failing over to a standby. Fault tolerance is stronger: the failure is invisible to the user, which needs redundant active components and costs more. Disaster recovery is about coming back after a large event, measured by RTO (how long until service is restored) and RPO (how much data you can lose). To the PM I quantify it: a second AZ costs an extra small instance and the RDS Multi-AZ premium; a single AZ outage costs a full downtime of unknown length.

**Deeper explanation:** The honest answer depends on the stage. An internal tool with ten users can live in one AZ with good backups. A customer-facing API with an SLA cannot, because an AZ-level event is a documented, recurring class of failure and the fix is architectural rather than something you can do during the incident. I would propose the cheapest multi-AZ shape: an ALB across two public subnets, an Auto Scaling group with a minimum of two instances in different AZs, and RDS Multi-AZ. Then I would set RTO and RPO targets explicitly and pick a DR tier (backup and restore, pilot light, warm standby) only if the business says the region-scale event matters.

**Follow-ups they will ask:**
- How RTO and RPO drive design: RPO near zero needs synchronous replication; RTO in minutes needs pre-provisioned capacity and automated failover, both of which cost money.
- What the cheapest DR is: automated backups copied to another region plus infrastructure as code to rebuild; long RTO, acceptable RPO for many systems.
- How you test it: scheduled game days where you actually fail over RDS, kill an AZ's instances or restore a backup into a fresh account.

**Mistakes to avoid:**
- Using high availability and disaster recovery interchangeably.
- Agreeing to one AZ without writing down the risk and the trigger for revisiting it.

### Practice
- Draw your last production system on AWS with AZ boundaries; mark every single point of failure and what it would cost to remove each one.
- Use the AWS Pricing Calculator to price an ALB, two small instances, RDS Multi-AZ and a NAT gateway for a month; then swap On-Demand for a one year Compute Savings Plan and note the difference.
- Run the Well-Architected Tool on a side project in the console and write down the three highest risk items with how you would fix them.
- Say it out loud: explain the shared responsibility model for S3 in 60 seconds, including who is responsible when a bucket is public.

## IAM & Security

> IAM is where most real cloud incidents start, so interviewers probe it harder than any other AWS topic. A weak answer defines users, groups and roles. A strong answer explains the evaluation order, shows how a container or pod gets credentials without any access keys, and knows what KMS does and does not do. Expect "what if" follow-ups that add a deny, a second account, or a leaked key.

### Concepts you must understand
- Principals (users, roles, federated identities) get permissions from identity-based policies; resources such as S3 buckets, KMS keys, SQS queues and Lambda functions can also carry resource-based policies; a role additionally has a trust policy that says who may assume it.
- Evaluation starts from implicit deny, an explicit Deny anywhere wins, and an Allow must then come from the right place: within one account an identity policy or a resource policy is enough, across accounts both sides must allow; SCPs, permission boundaries and session policies only restrict.
- Least privilege is iterative: start narrow, prune with IAM Access Analyzer and last-accessed data, and prefer conditions (source VPC endpoint, organization ID, tags) over broad wildcards.
- STS issues temporary credentials; AssumeRole, AssumeRoleWithWebIdentity (OIDC) and SSO through IAM Identity Center replace long-lived access keys almost everywhere.
- Compute gets credentials from the SDK credential chain: instance profile on EC2 through IMDSv2, task role on ECS, IRSA or Pod Identity on EKS, execution role on Lambda; production code never reads keys from a file.
- KMS keys never leave the service; you encrypt data with a data key and store that data key wrapped by KMS next to the data (envelope encryption), which S3, EBS, RDS and Secrets Manager do for you.
- Secrets Manager stores secrets with rotation and per-secret pricing; Parameter Store is a cheap hierarchical config store with SecureString support but no built-in rotation.
- Security groups are stateful allow-lists on network interfaces; network ACLs are stateless allow and deny rules on subnets, evaluated in rule number order.
- WAF filters HTTP at CloudFront, ALB and API Gateway with managed rule groups and rate limits; Shield Standard absorbs network-layer DDoS at no cost, Shield Advanced adds response support and cost protection.
- CloudTrail records every API call and is the audit trail you alert on and read first in an incident, so it belongs in a locked-down bucket in a separate account.

### Q. Explain IAM policy evaluation. If my identity policy allows s3:GetObject on a bucket but the bucket policy never mentions me, do I get the object?

**Short answer (45 seconds):** Everything starts as an implicit deny. An explicit Deny in any applicable policy wins immediately. Otherwise, within a single account, an Allow in either the identity policy or the bucket policy is enough, so yes, you get the object as long as no SCP, permission boundary or session policy blocks it. Across accounts both sides must allow: the caller's identity policy and the bucket policy. SCPs, boundaries and session policies never grant anything; they only cap what the other policies can grant.

**Deeper explanation:** The order to say out loud: explicit deny, then organization SCPs, then resource-based policy, then permission boundary, then session policy, then identity-based policy. A statement is Effect, Action, Resource and an optional Condition, and conditions are where least privilege becomes real.

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::acme-uploads/tenant-${aws:PrincipalTag/tenant}/*",
  "Condition": { "Bool": { "aws:SecureTransport": "true" } }
}
```

That statement scopes a principal to its own tenant prefix with attribute-based access control and refuses plaintext HTTP. Other conditions you will use: aws:SourceVpce to pin a bucket to a VPC endpoint, aws:PrincipalOrgID to allow anything inside your organization, and kms:ViaService to let a key be used only through S3.

**Follow-ups they will ask:**
- What a permission boundary is for: letting developers create roles without being able to grant more than the boundary allows, which blocks privilege escalation.
- Why Deny statements matter if default is deny: to override Allows you do not control, for example an SCP denying actions outside approved regions or disabling CloudTrail in every account.
- What NotAction does: matches every action except the listed ones; with Deny it is a common way to write "nothing but these".

**Mistakes to avoid:**
- Saying the bucket policy must always allow; that is only true across accounts.
- Writing Resource "*" with s3:* and calling it done; the interviewer will ask how you would narrow it.

### Q. What is an IAM role, how does AssumeRole work, and why are roles preferred over access keys?

**Short answer (45 seconds):** A role is an identity with permissions but no long-lived credentials. It has two kinds of policy: a trust policy that says who may assume it and permission policies that say what it can do. Calling sts:AssumeRole returns temporary credentials (access key, secret, session token) that expire, typically after an hour, and the SDK refreshes them automatically. Roles beat access keys because nothing long-lived exists to leak, rotation is built in, and CloudTrail records which session did what.

**Deeper explanation:** The trust policy is a resource policy on the role itself. For an EC2 instance it trusts ec2.amazonaws.com; for a cross-account deploy role it trusts the other account's role ARN; for GitHub Actions it trusts an OIDC provider with a condition on the repository claim, which is how CI deploys without any stored AWS secret.

```bash
aws sts assume-role --role-arn arn:aws:iam::111122223333:role/deploy \
  --role-session-name ci-$GITHUB_RUN_ID --external-id acme-prod
aws sts get-caller-identity   # shows the assumed-role session ARN
```

An external ID defends against the confused deputy problem when a third-party vendor assumes a role in your account. Role chaining (assuming a role from assumed-role credentials) caps the session at one hour, which trips up long batch jobs. Session tags pass attributes such as tenant into the session for ABAC conditions.

**Follow-ups they will ask:**
- How the SDK finds credentials: the provider chain, environment variables first, then shared config and profiles, then container credentials, then instance metadata.
- How you would hand a vendor access to one bucket: a role in your account trusting their account with an external ID and a policy limited to that bucket, never an IAM user with keys.
- What to do when a role session is abused: revoke active sessions (a Deny conditioned on aws:TokenIssueTime), then remove the path the attacker used.

**Mistakes to avoid:**
- Creating IAM users with access keys for applications; it is a red flag in any review.
- Forgetting the trust policy side; permissions alone do not make a role assumable.

### Q. How does a pod on EKS get AWS credentials? Compare IRSA with EKS Pod Identity.

**Short answer (45 seconds):** Both map a Kubernetes service account to an IAM role so the pod receives short-lived credentials with no keys. IRSA registers the cluster's OIDC issuer as an identity provider in IAM, annotates the service account with a role ARN, and the SDK exchanges the projected service account token for credentials with AssumeRoleWithWebIdentity. EKS Pod Identity is the newer path: an agent add-on on each node vends credentials, the role trusts the pods.eks.amazonaws.com principal, and you link a service account to a role with an association, with no per-cluster OIDC provider in the trust policy.

**Deeper explanation:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-api
  namespace: api
  annotations:   # IRSA only; Pod Identity uses an association instead
    eks.amazonaws.com/role-arn: arn:aws:iam::111122223333:role/orders-api
```

With IRSA the role's trust policy conditions on the provider's sub claim, system:serviceaccount:api:orders-api, so roles are tied to one cluster and the trust policy must change when a cluster is recreated. Pod Identity decouples that: one role can serve several clusters, associations are created through the EKS API, and session tags carry cluster, namespace and service account for ABAC. Either way the node's own instance role should stay minimal, because a pod could otherwise reach it through the metadata endpoint; enforce IMDSv2 with a hop limit of 1 or block it with a network policy.

**Follow-ups they will ask:**
- Why not just use the node instance role: every pod on the node would share it, which breaks least privilege and audit.
- How credentials appear inside the container: environment variables the SDK chain picks up, a web identity token file and role ARN for IRSA, a container credentials URI for Pod Identity.
- What about Fargate pods: IRSA is the established path there; check the current Pod Identity support matrix before promising it.

**Mistakes to avoid:**
- Mounting a Kubernetes secret with access keys into the pod; it works and is exactly what interviewers screen against.
- Describing IRSA without the OIDC provider; the token exchange is the whole mechanism.

### Q. Explain envelope encryption with KMS. Why not just call kms:Encrypt on the data?

**Short answer (45 seconds):** KMS keys never leave the service and the Encrypt API only accepts a small payload, so you do not push data through KMS. Instead you call GenerateDataKey, which returns a plaintext data key and the same key wrapped under your KMS key. You encrypt the data locally with the plaintext key, discard it, and store the wrapped key next to the ciphertext. To decrypt, you send the wrapped key to KMS, get the plaintext key back, and decrypt locally. One KMS call per object instead of per byte, and the master key is never exposed.

**Deeper explanation:**

```python
import boto3
kms = boto3.client("kms")
dk = kms.generate_data_key(KeyId="alias/app-data", KeySpec="AES_256",
                           EncryptionContext={"tenant": "acme"})
plaintext_key, wrapped_key = dk["Plaintext"], dk["CiphertextBlob"]
ciphertext = aes_gcm_encrypt(plaintext_key, payload)   # encrypt locally, then drop the key
store(ciphertext, wrapped_key, tenant="acme")          # persist both together
key = kms.decrypt(CiphertextBlob=wrapped_key, EncryptionContext={"tenant": "acme"})["Plaintext"]
```

The encryption context is authenticated additional data: decryption fails if it does not match, which stops a wrapped key from tenant A being replayed against tenant B. The AWS Encryption SDK implements this pattern with data key caching. S3 SSE-KMS, EBS and RDS encryption use it internally, and S3 Bucket Keys cut KMS request volume by deriving per-bucket keys. Rotating a KMS key only rotates the key material going forward; old data keys still decrypt because KMS keeps previous versions.

**Follow-ups they will ask:**
- AWS managed versus customer managed keys: customer managed keys give you the key policy, rotation settings, grants and the ability to disable or delete.
- How you restrict a key to one service: a kms:ViaService condition in the key policy, or a grant scoped to specific operations.
- What happens when you schedule deletion: a mandatory waiting period, then everything encrypted under that key is unrecoverable.

**Mistakes to avoid:**
- Saying rotation re-encrypts all your data; it does not, and that is a feature.
- Confusing encryption at rest with access control; anyone with kms:Decrypt and s3:GetObject reads the data.

### Q. Secrets Manager or Parameter Store? Decide for database credentials, a third-party LLM API key, and feature flags.

**Short answer (45 seconds):** Database credentials go in Secrets Manager because it rotates them, has managed rotation for RDS and Aurora, and lets ECS and Lambda inject the value at start. A third-party API key can live in either; I use Secrets Manager when I need rotation, cross-account access or replication, and a SecureString parameter when it is a single static key and cost matters. Feature flags and non-secret config belong in Parameter Store, or AppConfig when I want validation and gradual rollout.

**Deeper explanation:** Parameter Store standard parameters are free and hierarchical (/prod/api/db_host), support SecureString encrypted with KMS, and are versioned, but there is no built-in rotation and throughput is modest unless you enable the higher throughput setting. Secrets Manager is priced per secret per month plus API calls, stores JSON secrets with several fields, rotates through a Lambda function or managed rotation, and supports resource policies for cross-account access and multi-region replication.

In both cases read the value at startup and cache it; never call the API per request. On ECS use the secrets block in the task definition with valueFrom pointing at the secret ARN; on Lambda use the Parameters and Secrets Lambda Extension, which caches locally. For a Node.js service a small loader that resolves secrets into process.env at boot keeps the rest of the code unchanged.

**Follow-ups they will ask:**
- How rotation avoids downtime: the rotation function creates a new password, updates the database user, tests it and promotes the version to AWSCURRENT; clients must refetch on an auth failure instead of caching forever.
- Why not environment variables in the task definition: they are visible to anyone with describe permissions and never rotate.
- Whether Parameter Store can read a secret: yes, through the /aws/reference/secretsmanager/ path prefix, handy when code only speaks the SSM API.

**Mistakes to avoid:**
- Committing .env files or baking secrets into container images.
- Fetching the secret inside the request handler and blaming AWS for latency and throttling.

### Q. Security groups versus network ACLs: when would you actually need a NACL?

**Short answer (45 seconds):** A security group is a stateful allow-list attached to a network interface: allow inbound 443 and the response traffic is allowed automatically, and rules can reference other security groups instead of IP ranges. A network ACL is a stateless list of numbered allow and deny rules on a subnet, evaluated in order, so you must open ephemeral ports for return traffic. I do nearly everything with security groups and reach for a NACL only to deny: block an abusive IP range at the subnet edge, or add a hard deny between tiers as defense in depth.

**Deeper explanation:** The most useful security group pattern is referencing: the database security group allows 5432 only from the API security group, so scaling the API tier never touches IP rules.

```text
sg-alb : inbound 443 from 0.0.0.0/0
sg-api : inbound 3000 from sg-alb
sg-db  : inbound 5432 from sg-api
NACL on db subnets: deny inbound from public subnet CIDRs, allow 5432 from app CIDRs,
                    allow outbound ephemeral 1024-65535 for responses
```

Security groups cannot deny; anything not allowed is dropped, and the default outbound rule allows everything, which is worth tightening for data-handling tiers. NACLs are evaluated lowest rule number first and the first match wins, so a misordered rule silently breaks traffic. Because they are stateless, forgetting the ephemeral port range is the classic cause of "it works with the default NACL but not with mine".

**Follow-ups they will ask:**
- Can a security group reference one in another VPC: yes across a VPC peering connection in the same region; otherwise you use CIDR rules.
- How to debug a blocked connection: VPC Reachability Analyzer and VPC Flow Logs, where REJECT entries show which hop dropped it.
- Where WAF sits relative to these: WAF inspects HTTP at the load balancer or CloudFront; SGs and NACLs only see ports and addresses.

**Mistakes to avoid:**
- Opening 0.0.0.0/0 on the database security group "temporarily".
- Claiming NACLs are stateful or that security groups can deny.

### Q. How do WAF and Shield protect a public API, and what would you configure on day one?

**Short answer (45 seconds):** Shield Standard is always on and absorbs network and transport layer DDoS at no extra cost; Shield Advanced adds attack visibility, a response team and cost protection for high value targets. WAF is a layer 7 filter attached to CloudFront, an ALB or API Gateway, built from a web ACL of rules. On day one I attach the AWS managed core rule set and known bad inputs groups, add a rate-based rule per IP, run everything in count mode for a week to catch false positives, then switch to block.

**Deeper explanation:** WAF rules match on URI, headers, body, query string, IP and geography, and the AWS managed rule groups cover OWASP-style injection, bad user agents and known exploits. Rate-based rules are the pragmatic defense against credential stuffing and scraping; scope them to the login or chat completion path rather than the whole site so ordinary users are not throttled. Bot Control and Account Takeover Prevention are paid add-ons for heavier abuse. Put CloudFront in front even for an API: it absorbs floods at the edge, lets WAF run globally and reduces origin data transfer.

WAF logs go to CloudWatch Logs, S3 or Kinesis Data Firehose, and the sampled requests view in the console is enough to tune a rule. For an LLM-backed API, WAF rate and body size limits are the first line, then per-user quotas inside the application.

**Follow-ups they will ask:**
- WAF versus API Gateway throttling: WAF blocks before the request reaches the API; usage plans meter per API key for business quotas.
- How to handle a false positive in one managed rule: override that single rule to count, or add a scope-down statement for the affected path.
- What Shield Advanced cost protection means: credits for scaling charges incurred during a confirmed attack on protected resources.

**Mistakes to avoid:**
- Turning every managed rule to block on launch day and breaking uploads or JSON bodies that contain SQL-looking text.
- Describing WAF as DDoS protection; that is Shield's job, WAF handles application-layer abuse.

### Q. How would you find out that someone used the root account or created a new access key, and what else is CloudTrail for?

**Short answer (45 seconds):** CloudTrail records every management API call with who, when, from where and with which parameters. For alerting I route CloudTrail events to EventBridge and match root sign-ins, CreateAccessKey, console logins without MFA and changes to CloudTrail itself, then publish to SNS or a chat channel. For investigation I keep an organization trail delivering to an S3 bucket in a dedicated security account, with log file validation on, and query it with Athena or CloudTrail Lake.

**Deeper explanation:**

```json
{
  "detail-type": ["AWS API Call via CloudTrail", "AWS Console Sign In via CloudTrail"],
  "detail": {
    "$or": [
      { "userIdentity": { "type": ["Root"] } },
      { "eventName": ["CreateAccessKey", "DeleteTrail", "StopLogging"] }
    ]
  }
}
```

Management events (create, modify, delete on the control plane) are logged by default and searchable for 90 days in event history; data events (S3 object reads and writes, Lambda invocations, DynamoDB item access) are opt-in and high volume, so enable them only on sensitive resources. IAM and sign-in events are global and land in us-east-1, so that EventBridge rule must live there. GuardDuty consumes CloudTrail, VPC Flow Logs and DNS logs to raise findings such as credential exfiltration, and Security Hub aggregates those with Config results. In an incident CloudTrail answers the first three questions: which principal, from which IP, and what it touched next.

**Follow-ups they will ask:**
- How you protect the trail from the attacker: deliver to a separate account, deny DeleteTrail and StopLogging through an SCP, enable log file validation and S3 Object Lock.
- Why root should never be used day to day: it bypasses IAM policies and boundaries; lock it with hardware MFA and alert on any use.
- CloudTrail versus CloudWatch Logs: CloudTrail is the API audit trail, CloudWatch Logs is your application and system log store; CloudTrail can deliver into it for metric filters and alarms.

**Mistakes to avoid:**
- Assuming data events are on by default and promising object-level audit you never enabled.
- Keeping the audit trail in the same account the attacker controls.

### Practice
- Create a role whose trust policy allows your own user, assume it with the CLI, run get-caller-identity, then attempt an action outside its policy and read the AccessDenied message carefully.
- Encrypt a file with envelope encryption using boto3 generate_data_key and decrypt it; then disable the key and observe exactly which call fails.
- Write the IRSA trust policy for namespace api and service account orders by hand, then compare it with what eksctl create iamserviceaccount generates.
- Put a WAF web ACL in count mode on a test ALB, send a few requests with an injection payload in the query string, and read the sampled requests.
- Say it out loud: explain how a container on ECS gets AWS credentials without any access keys, in under a minute.

## Networking

> Networking questions separate people who have deployed on AWS from people who have read about it. Interviewers want a VPC drawn from memory, a clear story about how a private container reaches the internet and how traffic reaches it, and awareness of the invisible charges. Weak answers stop at "public and private subnets". Strong answers name route tables, endpoints, where NAT costs come from, and when peering stops scaling.

### Concepts you must understand
- A VPC is a regional private network with a CIDR block, split into subnets that each live in one AZ; a subnet is public only because its route table sends 0.0.0.0/0 to an internet gateway.
- Route tables use longest prefix match and always contain the local route for the VPC CIDR; the main route table applies to any subnet without an explicit association.
- An internet gateway is a free, horizontally scaled door for resources with public IPs; a NAT gateway lets private resources initiate outbound connections and charges per hour and per GB processed.
- Gateway endpoints (S3, DynamoDB) are free route table entries; interface endpoints (PrivateLink) are ENIs with private IPs that cost per hour per AZ plus per GB, and they keep traffic off NAT and the public internet.
- ALB is layer 7 (routing by host, path and headers, WebSockets, gRPC, OIDC authentication, WAF); NLB is layer 4 (TCP, UDP, TLS passthrough, static IPs, very high throughput, PrivateLink target).
- Route 53 routing policies (simple, weighted, latency, failover, geolocation, geoproximity, multivalue) combine with health checks; alias records point at AWS resources for free and work at the zone apex.
- CloudFront caches at the edge, terminates TLS near the user, hides the origin and makes WAF and Shield global; transfer from AWS origins to CloudFront is not billed.
- VPC peering is one-to-one and non-transitive; Transit Gateway is a regional hub with its own route tables that scales to many VPCs and on-prem links at a per-attachment and per-GB price.
- Cost traps: NAT data processing, cross-AZ transfer, public IPv4 address hours, interface endpoints in every AZ, idle load balancers and inter-region traffic.

### Q. Design the VPC for a three-tier web application. Which subnets, route tables and gateways do you create, and why?

**Short answer (45 seconds):** One VPC with a /16 from private address space, split into three tiers across at least two AZs: public subnets for the load balancer and NAT gateways, private application subnets for ECS tasks or instances, and isolated data subnets for RDS and ElastiCache with no internet route at all. Public subnets route 0.0.0.0/0 to an internet gateway, application subnets route it to a NAT gateway in the same AZ, and data subnets keep only the local route. Gateway endpoints for S3 and DynamoDB go in every private route table so that traffic never touches NAT.

**Deeper explanation:**

```text
VPC 10.0.0.0/16
  public-a  10.0.0.0/20   -> 0.0.0.0/0 igw             (ALB, NAT-a)
  public-b  10.0.16.0/20  -> 0.0.0.0/0 igw             (ALB, NAT-b)
  app-a     10.0.32.0/20  -> 0.0.0.0/0 nat-a + S3/DynamoDB gateway endpoints
  app-b     10.0.48.0/20  -> 0.0.0.0/0 nat-b + S3/DynamoDB gateway endpoints
  data-a    10.0.64.0/24  -> local only                (RDS primary)
  data-b    10.0.65.0/24  -> local only                (RDS standby)
```

Size subnets generously: EKS and ECS awsvpc networking use one IP per pod or task, and subnets cannot be resized. One NAT gateway per AZ avoids a cross-AZ dependency and cross-AZ charges; a single shared NAT is a fair saving in development. Security groups isolate the tiers; NACLs stay default unless a hard deny is needed. Turn on VPC Flow Logs from day one and reserve a non-overlapping CIDR per environment so peering or Transit Gateway works later.

**Follow-ups they will ask:**
- Why not run the application in public subnets with tight security groups: one mistake exposes the instance directly, and every public IPv4 address now costs money per hour.
- How many AZs: two is the minimum for HA, three is the norm for EKS and for quorum-based systems.
- Where Lambda functions live: outside your VPC by default; attach them only when they must reach private resources, which adds NAT dependency for internet access.

**Mistakes to avoid:**
- Giving the database subnet an internet route "for updates"; RDS patches itself and reaches AWS services through endpoints.
- Choosing 10.0.0.0/16 for every VPC and environment, then discovering none of them can peer.

### Q. Internet gateway versus NAT gateway: what does each do, and where does the cost hide?

**Short answer (45 seconds):** An internet gateway is the VPC's door to the public internet for resources that have a public or Elastic IP; it is horizontally scaled and costs nothing itself. A NAT gateway lets resources with only private IPs initiate outbound connections by translating their source address to its own Elastic IP, and it refuses inbound connections. The cost hides in the per-hour charge for each AZ you deploy a NAT gateway in and, more painfully, a per-GB processing fee on everything flowing through it, so S3 reads and image pulls from private subnets become a line item.

**Deeper explanation:** The internet gateway maps an instance's private IP to its public IP one to one; nothing needs a public IP unless it must be reached directly, which is why only load balancers and NAT gateways belong in public subnets. The NAT gateway is zonal: if the only NAT in AZ a fails or that AZ goes down, private subnets in AZ b that route through it lose internet access, so production uses one per AZ with per-AZ route tables.

Typical NAT bill drivers: image pulls from ECR, S3 reads, CloudWatch Logs and Secrets Manager calls, package installs at build time, and calls to external APIs such as an LLM provider. All but the last two can bypass NAT with a gateway endpoint for S3 and interface endpoints for the rest. For IPv6 egress an egress-only internet gateway replaces NAT with no processing fee.

**Follow-ups they will ask:**
- NAT instance versus NAT gateway: an EC2 instance you manage is cheaper at low volume and avoids the processing fee, but you own patching, failover and bandwidth limits.
- How to see what goes through NAT: VPC Flow Logs filtered by the NAT ENI, or the gateway's CloudWatch bytes metrics, then group by destination.
- Can a NAT gateway accept inbound: no, that is the point; inbound goes through a load balancer.

**Mistakes to avoid:**
- Saying the NAT gateway gives instances internet access "both ways".
- Deploying one NAT gateway and calling the architecture multi-AZ.

### Q. What are VPC endpoints and PrivateLink, and when do you use a gateway endpoint versus an interface endpoint?

**Short answer (45 seconds):** VPC endpoints let resources reach AWS services without crossing the internet or a NAT gateway. Gateway endpoints exist only for S3 and DynamoDB: they are route table entries, cost nothing, and belong in every VPC. Interface endpoints, built on PrivateLink, place an elastic network interface with a private IP in your subnets for most other services, such as ECR, Secrets Manager or Bedrock, with private DNS so the SDK needs no change; they cost per hour per AZ plus per GB. PrivateLink also exposes your own service behind an NLB to other VPCs and accounts without peering.

**Deeper explanation:** A gateway endpoint is a route table target, so it works only from inside that VPC and only in the same region. With private DNS enabled the service hostname resolves to the ENI addresses, so a container with no NAT route can still call Secrets Manager. Endpoint policies restrict what is reachable through the endpoint, and a bucket policy can require aws:SourceVpce so the bucket is unreachable from anywhere else.

```text
Gateway endpoint  : S3, DynamoDB  | route table entry | free        | same VPC only
Interface endpoint: most services | ENI + private DNS | hourly + GB | reachable over peering/TGW
PrivateLink service: your NLB | consumers attach interface endpoints
```

PrivateLink is the clean way to share an internal API across accounts: the consumer sees a private IP, CIDR overlap does not matter, and you approve each consumer.

**Follow-ups they will ask:**
- When an interface endpoint costs more than NAT: at low traffic across three AZs the hourly fees can exceed the NAT processing saved, so measure first.
- Whether you need one endpoint per service: yes, and ECR needs the api and dkr endpoints plus the S3 gateway endpoint for layers.
- Can on-prem use them: interface endpoints yes, over Direct Connect or VPN; gateway endpoints no.

**Mistakes to avoid:**
- Assuming an S3 gateway endpoint covers buckets in other regions; it is regional.
- Forgetting that ECR layers come from S3, so image pulls still fail without NAT.

### Q. ALB versus NLB: how do you choose for an HTTP API, a gRPC service, WebSockets, and a client that must allowlist your IP?

**Short answer (45 seconds):** The ALB is a layer 7 proxy: it terminates HTTP and HTTPS, routes on host, path, headers and query strings, supports WebSockets and gRPC, can authenticate with OIDC or Cognito, and is where WAF attaches. The NLB is layer 4: it forwards TCP, UDP and TLS with very low latency, offers a static or Elastic IP per AZ, preserves the client source IP, and is the only target PrivateLink accepts. REST and WebSockets go on an ALB, gRPC works on an ALB with HTTP/2 target groups, and when a customer needs fixed IPs to allowlist I put an NLB in front with the ALB as its target.

**Deeper explanation:** ALB target groups can be instances, IP addresses (ECS awsvpc tasks, on-prem hosts) or Lambda functions, each with its own health check and deregistration delay. Features worth naming: sticky sessions, slow start, weighted target groups for canary releases, and connection draining. The ALB hides the client IP behind X-Forwarded-For, so an Express app must set trust proxy before rate limiting by IP.

The NLB has no request-level features: no path routing, no WAF, no header manipulation. It shines for non-HTTP protocols (MQTT, database proxies), very large connection counts, and PrivateLink. TLS listeners can terminate with ACM certificates or pass through. Cross-zone load balancing is on by default for ALB and off by default for NLB, which affects both balance and cross-AZ charges.

**Follow-ups they will ask:**
- What happens to WebSocket connections during a deploy: the ALB keeps them until the target deregisters and the deregistration delay expires, so make clients reconnect gracefully.
- How health checks differ: ALB checks an HTTP path and status code; NLB can use TCP, HTTP or HTTPS checks.
- Why an ALB behind an NLB: static IPs plus layer 7 routing, supported natively through ALB-type target groups.

**Mistakes to avoid:**
- Choosing an NLB "for performance" for a plain HTTP API and losing WAF, path routing and OIDC.
- Rate limiting by req.ip behind an ALB without trusting the proxy, which throttles the load balancer's own addresses.

### Q. Walk me through Route 53 routing policies. How would you fail over between two regions and still send users to the closest one?

**Short answer (45 seconds):** Route 53 is authoritative DNS, and a record's routing policy decides how it answers. Simple returns one value set; weighted splits traffic by percentage for canaries; latency picks the region with the lowest measured latency to the resolver; failover returns a primary until its health check fails, then the secondary; geolocation answers by the user's country or continent for residency rules; geoproximity biases by distance; multivalue returns several healthy addresses. For two regions I use latency records for each region, each with a health check, so a failing region drops out and users land on the nearest healthy one.

**Deeper explanation:**

```text
api.example.com  latency  ap-south-1    alias -> ALB Mumbai   health check /healthz
api.example.com  latency  me-central-1  alias -> ALB UAE      health check /healthz
```

Health checks run from several AWS locations against an endpoint, or wrap other checks or a CloudWatch alarm; alias records can also use the target's own health. TTL matters: a 300 second TTL means failover takes up to five minutes for cached clients, so failover records use a short TTL. Alias records are free, work at the zone apex and point at AWS resources.

Active-passive DR uses failover records with the standby region as secondary; active-active uses latency or geolocation with health checks on each side. Route 53 Application Recovery Controller adds routing controls you flip deliberately, which avoids trusting an automated check during a partial outage.

**Follow-ups they will ask:**
- Why DNS failover is not instant: resolvers and clients cache for the TTL and some ignore it, so pair DNS failover with client retries.
- Private DNS inside a VPC: private hosted zones associated with the VPC, plus Route 53 Resolver endpoints for hybrid resolution.
- Geolocation versus geoproximity: geolocation keys on where the user is for compliance; geoproximity keys on distance to your resources with a bias knob.

**Mistakes to avoid:**
- Forgetting health checks on latency records, which happily sends users to a dead region.
- Trying to use a CNAME at the zone apex; DNS forbids it, which is exactly why alias records exist.

### Q. What does CloudFront give you in front of an ALB or an S3 bucket, and how does caching work for API responses?

**Short answer (45 seconds):** CloudFront terminates TLS at an edge location near the user, caches content there, keeps warm connections to the origin, and lets WAF, Shield and edge functions run globally. In front of S3 it uses origin access control so the bucket stays private and only CloudFront can read it. In front of an ALB it still helps a dynamic API: faster TLS handshakes, burst absorption, and no charge for transfer from the ALB to CloudFront. API responses are cached only where I allow it: GET responses with Cache-Control headers, keyed by path and selected query strings, while anything keyed on Authorization or cookies is effectively uncached.

**Deeper explanation:** A distribution has origins and behaviors matched by path pattern. Each behavior picks a cache policy (what forms the cache key: headers, cookies, query strings, TTL bounds) and an origin request policy (what is forwarded without joining the key). Keep the cache key small; forwarding all headers makes every request unique. Invalidations are slow, so version static asset filenames instead.

```text
/static/*  -> S3 origin (OAC), long TTL, immutable filenames
/api/*     -> ALB origin, cache only on explicit Cache-Control, forward Authorization
/*         -> S3 index.html for the SPA, short TTL, 403/404 mapped to /index.html
```

CloudFront Functions handle light header or URL rewrites and Lambda@Edge heavier logic such as token checks; signed URLs protect private content and Origin Shield adds a regional cache layer.

**Follow-ups they will ask:**
- Can CloudFront pass streamed LLM responses: yes, it forwards chunked responses from the origin when the behavior is not caching them.
- Why not S3 static website hosting alone: no HTTPS on a custom domain, the bucket must be public, and there is no WAF.
- How to stop clients bypassing CloudFront: restrict the ALB security group to the CloudFront managed prefix list and verify a secret custom origin header.

**Mistakes to avoid:**
- Caching responses that vary by user because Authorization was not in the cache key.
- Treating CloudFront as the security boundary while the ALB stays reachable directly.

### Q. VPC peering versus Transit Gateway: when does peering stop scaling, and how do you segment traffic?

**Short answer (45 seconds):** Peering connects exactly two VPCs with non-overlapping CIDRs and is not transitive: if A peers with B and B with C, A still cannot reach C. It has no hourly fee, only data charges, so it suits a handful of VPCs. Transit Gateway is a regional hub: each VPC, VPN or Direct Connect attaches once, routing is transitive, and its own route tables decide which attachments may talk, at an hourly per-attachment fee plus per GB. Past a dozen or so VPCs, or when all of them need shared on-prem connectivity, the peering mesh becomes unmanageable and Transit Gateway wins.

**Deeper explanation:** With peering each pair needs routes in both VPCs' tables for the other CIDR, and connections grow with the square of the VPC count. Transit Gateway flattens that: each VPC holds one route to the TGW for the other ranges, and TGW route tables decide reachability. Segmentation comes from associating attachments with different TGW route tables: a shared-services table every environment reaches, and production and development tables that cannot see each other. Both peering and Transit Gateway work across regions.

Overlapping CIDRs block both approaches, so a central IP plan matters; PrivateLink is the escape hatch when overlap exists, since it exposes a service without routing between networks. Security groups can reference groups across a same-region peering connection but not across Transit Gateway, so cross-VPC rules there fall back to CIDRs.

**Follow-ups they will ask:**
- Cost difference in one sentence: peering has no hourly fee but charges for cross-AZ or cross-region data; TGW adds an hourly attachment fee and a per-GB processing fee.
- How to centralize egress: route all VPCs' internet traffic through TGW to one inspection VPC with NAT and Network Firewall, trading data processing cost for a single control point.
- What AWS Cloud WAN adds: a managed global network with policy-driven segments across regions, built on Transit Gateway concepts.

**Mistakes to avoid:**
- Claiming peering is transitive.
- Letting every team pick 10.0.0.0/16 and discovering the overlap when the first peering is needed.

### Q. The bill shows a large data transfer and NAT gateway line. Where do you look first, and what are the usual fixes?

**Short answer (45 seconds):** I start in Cost Explorer grouped by usage type, which separates NAT data processing, cross-AZ transfer, internet egress, inter-region transfer and public IPv4 hours. Then I use VPC Flow Logs or the NAT gateway metrics to see which sources and destinations dominate. The fixes in order of payback: S3 and DynamoDB gateway endpoints, interface endpoints for ECR, Logs and Secrets Manager where volume justifies them, AZ-aware service calls, removing unneeded public IPv4 addresses, and CloudFront in front of anything serving large responses.

**Deeper explanation:** The common surprise is an EKS or ECS cluster in private subnets pulling images and reading S3 through NAT, where every gigabyte pays the processing fee; an S3 gateway endpoint fixes that instantly and for free. Cross-AZ charges come from load balancers with cross-zone balancing, from Kafka consumers reading brokers in other AZs (use rack awareness), and from microservices calling each other without topology hints. Every public IPv4 address, including those on ECS tasks with assignPublicIp enabled, is billed hourly, so private subnets with endpoints are cleaner and cheaper.

```bash
aws ce get-cost-and-usage --time-period Start=2026-10-01,End=2026-11-01 \
  --granularity MONTHLY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=USAGE_TYPE
```

Internet egress through CloudFront is usually cheaper than directly from an ALB or S3, and transfer from the origin to CloudFront is not charged.

**Follow-ups they will ask:**
- How to attribute NAT cost to a team: flow logs joined to ENI owners, or one NAT per account in a multi-account setup so the bill splits itself.
- Whether IPv6 helps: dual-stack subnets with an egress-only internet gateway avoid NAT processing fees and public IPv4 charges for destinations that support IPv6.
- Is inbound charged: data into AWS from the internet is generally free; you pay on the way out and between AZs or regions.

**Mistakes to avoid:**
- Adding interface endpoints for every service in three AZs without checking the hourly fees against the NAT processing they replace.
- Blaming EC2 compute when the "EC2-Other" line is really NAT, EBS and data transfer.

### Practice
- Build a VPC with Terraform or the console: two public, two private and two isolated subnets, one NAT per AZ and an S3 gateway endpoint; from a private instance confirm that aws s3 ls still works after removing the NAT route.
- Put an ALB in front of a small Express app with two target groups and shift traffic 90/10 with weighted target groups while watching the access logs.
- Enable VPC Flow Logs for an hour on a busy VPC, query them in Athena or Logs Insights, and rank destinations by bytes.
- Say it out loud: explain how a request travels from a browser to a container in a private subnet and back, naming every component it touches.

## Compute Options

> Interviewers want you to choose, not to list. "Would you use Lambda or ECS for this?" with "it depends" as the answer is a fail. A strong answer names the criteria (traffic shape, request duration, memory and GPU needs, startup latency tolerance, team operational maturity, steady-state cost) and then commits to a decision with one sentence on when it would flip.

### Concepts you must understand
- EC2 instance families encode the trade-off in the name: M general purpose, T burstable, C compute optimized, R and X memory optimized, I and D local NVMe storage, P and G NVIDIA GPUs (P for training, G for inference and graphics), Inf and Trn for AWS silicon; a g suffix means Graviton ARM.
- An Auto Scaling group keeps a desired number of instances from a launch template across AZs, replaces unhealthy ones, and scales through target tracking, step, scheduled or predictive policies; lifecycle hooks and warm pools handle slow boot and graceful drain.
- ECS is the AWS-native orchestrator (task definitions, services, clusters); EKS is managed Kubernetes where AWS runs the control plane and you own nodes or use Karpenter; Fargate is a serverless data plane for either that removes nodes but offers no GPUs.
- Lambda runs functions on demand with per-millisecond billing; it has hard limits on duration, memory and payload size, and a cold start whenever a new execution environment is created.
- Cold start time is mostly your own initialization code: package size, imports, SDK clients, connections; provisioned concurrency and SnapStart remove it for a price.
- App Runner turns a container image or repository into an autoscaled HTTPS service with almost no infrastructure decisions; Elastic Beanstalk is the older PaaS that provisions EC2, ALB and ASG for you.
- Node.js is single threaded per process, so horizontal scaling and one process per vCPU matter more than big instances; Python workers often need memory and native libraries that push them toward containers.
- GPU serving needs the right instance family, the NVIDIA device plugin or ECS GPU support, weights staged close to the node, and autoscaling on queue depth or model metrics rather than CPU.

### Q. Explain the EC2 instance families. Which would you pick for a Node.js API, a self-managed Postgres server, and a model server?

**Short answer (45 seconds):** The family letter gives the CPU to memory ratio and any accelerator: M balanced, T burstable on CPU credits, C compute heavy, R and X memory heavy, I and D local NVMe, G and P NVIDIA GPUs for inference and training, Inf and Trn AWS silicon. A g in the name means Graviton ARM, usually the best price for performance on Node and Python. Node API: Graviton general purpose, several small instances behind an ALB. Postgres: memory optimized R with gp3 or io2 EBS. Model server: a G family GPU for inference, P only for training or very large models.

**Deeper explanation:** Newer generations are cheaper per unit of performance, so prefer the latest your dependencies support. Sizes double resources step by step, and network and EBS bandwidth grow with size, which matters for databases. T instances bank CPU credits while idle; a busy API on a T family throttles once credits run out unless unlimited mode bills the overage.

```text
Node API      : m7g or c7g, small sizes, scale out behind ALB
Postgres      : r7g or r6i, io2 or gp3 EBS, replica for HA
Model serving : g5 (A10G) or g6 (L4) inference; p4d or p5 training
```

Node.js uses one core per process, so extra vCPUs only help with a process per core, another reason to favor small instances. Postgres wants memory for its cache and fast disks for WAL; local NVMe is fast but ephemeral, so it suits replicas and caches only.

**Follow-ups they will ask:**
- Why Graviton: lower price per performance, and ARM images exist for Node, Python and most bases; check native dependencies first.
- What burstable means in practice: fine for dev, CI and spiky low-traffic services, wrong for a steady production API.
- Inferentia versus GPU: cheaper per inference for supported architectures but needs the Neuron SDK compile step, so GPUs stay the flexible default.

**Mistakes to avoid:**
- Picking a size by guess and never revisiting; Compute Optimizer tells you within weeks.
- Running Postgres on a T instance, then debugging slowdowns that are credit exhaustion.

### Q. How does an Auto Scaling group work end to end, and what do lifecycle hooks and warm pools solve?

**Short answer (45 seconds):** An Auto Scaling group holds a minimum, maximum and desired count of instances launched from a launch template and spread across the subnets you give it. It replaces instances that fail EC2 or load balancer health checks and changes the desired count through policies: target tracking on a metric such as requests per target, step scaling on alarm thresholds, scheduled scaling for known peaks, and predictive scaling from history. Lifecycle hooks pause an instance at launch or termination so you can finish bootstrapping or drain work; warm pools keep pre-initialized instances stopped so scale out takes seconds, not minutes.

**Deeper explanation:** Target tracking is the default choice: tell the group to hold ALBRequestCountPerTarget near a value you load tested and it computes capacity changes itself. Step scaling suits asymmetric behavior, such as scaling out fast on queue depth and in slowly. Instance warm-up time stops the group from overreacting to lagging metrics. Health checks default to EC2 status checks; enable ELB health checks so an instance that boots but cannot serve is replaced.

```yaml
TargetTrackingConfiguration:
  PredefinedMetricSpecification:
    PredefinedMetricType: ALBRequestCountPerTarget
    ResourceLabel: app/my-alb/abc123/targetgroup/api/def456
  TargetValue: 800
```

Instance refresh rolls out a new launch template version in batches with a minimum healthy percentage, which is the native way to deploy an AMI change. Mixed instances policies blend On-Demand and Spot across several instance types, which is how Spot becomes safe for a stateless tier.

**Follow-ups they will ask:**
- Why CPU is often the wrong signal for Node: the event loop saturates before CPU on I/O heavy services, so requests per target or latency are better.
- How to drain gracefully: a terminating lifecycle hook that waits for in-flight requests plus the ALB deregistration delay, then completes the action.
- What a warm pool costs: stopped instances pay only for EBS, far cheaper than running spare capacity.

**Mistakes to avoid:**
- Setting minimum capacity to one and calling it highly available.
- Deploying by terminating instances by hand instead of using instance refresh.

### Q. ECS versus EKS versus Fargate: how do you choose for a team of eight engineers shipping a MERN product with a few Python services?

**Short answer (45 seconds):** ECS is the AWS-native orchestrator with task definitions and services, tightly integrated with IAM, ALB, CloudWatch and Secrets Manager, and far less to learn. EKS is managed Kubernetes: AWS runs the control plane, you own node groups or Karpenter, add-ons and the ecosystem, which pays off when you need Helm charts, operators or portability. Fargate is a serverless data plane for either, so no nodes to manage, at a higher per-vCPU price and without GPUs. For eight engineers I would run ECS on Fargate for the API and workers, and consider EKS only with Kubernetes fluency in house or a GPU scheduling need.

**Deeper explanation:** The real question is how much platform engineering the team wants to own. EKS brings version upgrades, the networking plugin, an ingress controller, cert-manager and RBAC, a part-time job even with managed node groups. ECS has a smaller surface: a task definition per service, a service for desired count and deployments, and capacity providers for Fargate or an ASG.

```text
ECS on Fargate : small team, HTTP services and workers, no GPUs, AWS-native simplicity
ECS on EC2     : GPUs, daemon containers, or cheaper steady compute under a Savings Plan
EKS            : Kubernetes skills in house, Helm and operator ecosystem, GPU scheduling with Karpenter
```

Fargate bills per vCPU and GB per second; at steady high utilization EC2 with a Savings Plan is cheaper, but Fargate removes patching, capacity planning and node rightsizing, which is usually worth more to a small team.

**Follow-ups they will ask:**
- Can Fargate run GPU workloads: no, use EC2 capacity in ECS or an EKS GPU node group.
- How you run a cron job: EventBridge Scheduler calling ECS RunTask, or a Kubernetes CronJob on EKS.
- How EKS scales nodes today: Karpenter provisions right-sized nodes for pending pods and largely replaces Cluster Autoscaler; EKS Auto Mode bundles that further.

**Mistakes to avoid:**
- Choosing EKS because it sounds more impressive, then spending the quarter on cluster plumbing.
- Treating Fargate as "cheaper serverless"; it is simpler, not cheaper, at steady load.

### Q. What are Lambda's hard limits, and what exactly happens during a cold start?

**Short answer (45 seconds):** A Lambda invocation runs for at most 15 minutes, with memory configurable up to 10 GB and CPU allocated in proportion to memory. Synchronous request and response payloads are capped at 6 MB, a container image can be up to 10 GB, and ephemeral /tmp storage is configurable up to 10 GB. A cold start happens when no idle execution environment exists: Lambda provisions a microVM, downloads your code, starts the runtime, runs your initialization code outside the handler, and only then invokes the handler. Later requests reuse that warm environment until it is reclaimed.

**Deeper explanation:** The cold start has a platform part (microVM, runtime bootstrap) and your part (imports, SDK clients, database connections, model loading), and your part is usually the larger one. A bundled, tree-shaken Node.js handler initializes far faster than one requiring the whole SDK. Module scope runs once per environment, so create clients and read secrets there, not in the handler.

```js
import { BedrockRuntimeClient } from "@aws-sdk/client-bedrock-runtime";
const client = new BedrockRuntimeClient({});   // built once per environment
let cachedSecret;
export const handler = async (event) => {
  cachedSecret ??= await loadSecret();         // lazy, then reused
  return handle(event, client, cachedSecret);
};
```

Each environment handles one request at a time, so a burst of a hundred requests to a cold function means a hundred cold starts. Memory is the only performance knob: more memory also means more CPU and network, and since billing is per GB-second a faster run often costs about the same.

**Follow-ups they will ask:**
- How to keep Postgres connections sane: RDS Proxy or one connection per environment; a thousand environments each opening a pool exhausts the database.
- Whether VPC-attached Lambdas still pay a big cold start penalty: no, that went away with shared Hyperplane ENIs.
- What SnapStart does: restores a snapshot of an initialized environment instead of initializing from scratch, for supported runtimes.

**Mistakes to avoid:**
- Calling Lambda "unlimited scale" without mentioning the account concurrency quota and downstream limits.
- Opening a database connection inside the handler on every request.

### Q. Where do App Runner and Elastic Beanstalk fit? When would you use either instead of ECS?

**Short answer (45 seconds):** App Runner takes a container image or a source repository and gives you an autoscaled HTTPS endpoint with no VPC or cluster to design; it is the closest AWS has to Cloud Run. Elastic Beanstalk is the older platform service that provisions EC2, an ALB and an Auto Scaling group from an application bundle, so you get managed setup but still see and pay for every piece. I use App Runner for small HTTP services, internal tools and early products where speed beats control, and I treat Elastic Beanstalk as legacy: fine to maintain, rarely right for new systems.

**Deeper explanation:** App Runner scales on concurrent requests per instance, bills idle instances for memory only, and reaches RDS or ElastiCache through a VPC connector. Its limits are the trade-off: fixed instance sizes, request timeouts suited to web traffic rather than long jobs, no GPUs, and little control over networking or deployment strategy. When a service outgrows it the same image moves to ECS without code changes, so it is a low-risk start.

Elastic Beanstalk still runs plenty of older Node and Java applications with rolling and immutable deployments, but you inherit EC2 patching cycles, an opaque configuration layer (.ebextensions) and a platform cadence tied to the runtimes AWS supports. For a container workload today, ECS with CDK or Copilot patterns gives the same convenience with more transparency.

**Follow-ups they will ask:**
- App Runner versus Lambda for an Express app: App Runner runs it unchanged with long-lived connections; Lambda is cheaper at low or spiky traffic but needs an adapter and has payload and duration limits.
- How App Runner reaches a private RDS: a VPC connector that places the service's outbound traffic inside your subnets.
- Migration off Beanstalk: containerize, deploy to ECS behind the same ALB hostname, shift traffic with weighted target groups or DNS.

**Mistakes to avoid:**
- Calling Elastic Beanstalk serverless; you pay for the instances whether or not traffic arrives.
- Starting a GPU or long-running batch workload on App Runner.

### Q. Pick compute for three workloads and justify it: a Node.js REST API with steady daytime traffic, a Python worker that processes uploaded documents, and a serving endpoint for an open-weights LLM.

**Short answer (45 seconds):** The Node API goes on ECS Fargate behind an ALB with target tracking on requests per task, because steady traffic makes always-on containers cheaper than per-request pricing and connection pooling is simpler there. The Python worker is SQS-driven: Lambda if each document finishes within minutes and fits in memory, otherwise a Fargate or EC2 service scaling on queue depth, on Spot because a lost task returns to the queue. The LLM endpoint needs GPUs, so it runs vLLM on EKS or ECS with EC2 GPU capacity, or on a SageMaker endpoint if we want AWS to own the serving stack.

**Deeper explanation:** For the API the decision is cost shape and connections: steady traffic means Lambda never goes idle, and pooling is natural in a container. I still keep it stateless so it can move later.

For the worker the decision is duration and dependencies: OCR, PDF parsing and embedding generation can exceed Lambda's 15 minute cap or need heavy native libraries; a container behind SQS handles both, scaling on ApproximateNumberOfMessagesVisible per task.

For model serving the decision is GPU memory and utilization: an 8B parameter model in 16-bit precision needs a GPU with room for weights plus KV cache, which fits a g5 or g6 class instance; larger models need tensor parallelism or quantization. GPUs are expensive while idle, so continuous batching, autoscaling on queue depth or tokens per second, and a scale-down plan matter more than the instance choice.

**Follow-ups they will ask:**
- When Lambda would win for the API: spiky or low traffic, or a team wanting zero container operations; pair it with RDS Proxy.
- Why not Fargate for the model: Fargate has no GPU support.
- How to cut GPU cost: quantized or smaller models, vLLM batching, Spot for non-critical replicas, or Bedrock when utilization would be low.

**Mistakes to avoid:**
- Choosing by familiarity alone; interviewers want the criteria named: traffic shape, duration, memory, GPU, ops maturity, steady-state cost.
- Ignoring data gravity: the worker belongs where the documents and database live.

### Q. How do you run GPU model serving on EKS? Walk me through nodes, scheduling and autoscaling.

**Short answer (45 seconds):** I create a dedicated GPU node group or Karpenter NodePool on g5, g6 or p4d families with the EKS-optimized accelerated AMI, install the NVIDIA device plugin so Kubernetes schedules nvidia.com/gpu as a resource, and taint those nodes so only GPU workloads land there. The vLLM deployment requests one or more GPUs, loads weights from S3 or a shared file system at start, and exposes an OpenAI-compatible endpoint behind a Service and an internal ALB. Autoscaling uses KEDA or the Horizontal Pod Autoscaler on queue depth or vLLM metrics, with Karpenter adding and removing GPU nodes underneath.

**Deeper explanation:**

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
nodeSelector:
  karpenter.k8s.aws/instance-family: g6
tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

Startup time is the enemy: a GPU node takes minutes to join, and pulling a multi-gigabyte image plus downloading weights adds more. Mitigations: pre-pulled images in a custom AMI, weights on FSx for Lustre or EFS, a minimum of one warm replica, and scaling on leading indicators such as waiting requests rather than GPU utilization, which lags. The vLLM metrics endpoint exposes running requests, waiting requests and KV cache usage, which are the right scaling signals. One GPU per pod is the simple case; tensor parallel setups request several GPUs on one node and need instance types with that many GPUs and a fast interconnect.

**Follow-ups they will ask:**
- How to share a GPU across small models: time slicing in the device plugin config or MIG on supported GPUs, noting that time slicing does not isolate memory.
- How to keep cost down: Spot for stateless replicas with a graceful shutdown that drains in-flight generations, and scaling down overnight if latency allows.
- How to observe it: DCGM exporter for GPU metrics into Prometheus or CloudWatch, plus tokens per second and time to first token from vLLM.

**Mistakes to avoid:**
- Scaling on CPU, which is nearly idle on a GPU node.
- Forgetting the taint, so an unrelated cron job lands on a GPU node and blocks a model replica.

### Practice
- Deploy a small Express app to ECS Fargate behind an ALB with CDK or Terraform, add a target tracking policy on requests per target, and load test it until it scales.
- Package the same app for Lambda with the Lambda Web Adapter, compare cold start and p99 latency against the Fargate deployment, and estimate monthly cost at 10 and at 1000 requests per minute.
- Read the EC2 instance type pages for g6 and p5 and write a one-paragraph recommendation for serving an 8B parameter model, including the memory arithmetic for weights and KV cache.
- Say it out loud: give the ECS versus EKS versus Fargate answer for a team of eight in under two minutes, ending with a decision.

## Storage & Databases

> Storage questions test whether you match the data model to the engine and whether you know how each one fails. A weak answer is "S3 for files, RDS for relational, DynamoDB for scale". A strong answer talks about lifecycle and retrieval costs, what your Node.js connection pool sees during a failover, how a partition key decides throughput, and when embeddings belong in Postgres versus a search cluster.

### Concepts you must understand
- S3 is an object store with strong read-after-write consistency, storage classes that trade retrieval cost and latency for a lower storage price, lifecycle rules that transition or expire objects automatically, and versioning that protects against overwrites and deletes.
- Presigned URLs let a browser upload or download directly against S3 with a time-limited signature, keeping large files off your API; multipart upload splits big objects into parallel parts that must be completed or aborted, or they keep costing money.
- S3 event notifications (to SQS, SNS, Lambda or EventBridge) make a bucket the start of a pipeline; delivery is at least once and unordered.
- EBS is a block volume attached to one instance in one AZ (gp3 default, io2 for high IOPS); EFS is a shared NFS file system across AZs; instance store is fast local disk that disappears with the instance.
- RDS runs a standard engine with automated backups, point-in-time recovery, Multi-AZ failover and read replicas; Aurora replaces the storage layer with a distributed volume across three AZs, giving faster failover, more replicas and storage that grows on its own.
- Multi-AZ is for availability (synchronous standby, same endpoint, not readable in the classic deployment); read replicas are for read scaling (asynchronous, own endpoints, promotable).
- DynamoDB spreads items by partition key hash and each partition has a throughput ceiling, so key design is the schema; GSIs add access patterns, single-table design models them all up front, and hot partitions come from low-cardinality or celebrity keys.
- ElastiCache (Redis, Valkey, Memcached) is the sub-millisecond cache and ephemeral state layer; OpenSearch covers full-text search, log analytics and k-NN vectors; DocumentDB speaks the MongoDB protocol but is not MongoDB.
- pgvector on RDS or Aurora PostgreSQL keeps embeddings next to the rows they describe with transactional writes and SQL filtering, at the cost of index tuning (HNSW or IVFFlat) and shared capacity with the application's queries.

### Q. Design S3 storage for user uploads that are read heavily for a month and rarely afterwards. Which classes and lifecycle rules do you use?

**Short answer (45 seconds):** Objects land in S3 Standard because it has no retrieval fee and the lowest latency for hot data. A lifecycle rule transitions them to Standard-IA after 30 days, where storage is cheaper but each retrieval is billed, and optionally on to Glacier Instant Retrieval later if access becomes rare but must stay immediate. If I cannot predict the pattern I use Intelligent-Tiering, which moves objects between tiers for a small monitoring fee. The same configuration aborts incomplete multipart uploads and expires old versions so versioning does not quietly double the bill.

**Deeper explanation:**

```json
{"Rules": [{
  "ID": "uploads", "Status": "Enabled", "Filter": {"Prefix": "uploads/"},
  "Transitions": [
    {"Days": 30, "StorageClass": "STANDARD_IA"},
    {"Days": 90, "StorageClass": "GLACIER_IR"}],
  "NoncurrentVersionExpiration": {"NoncurrentDays": 30},
  "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
}]}
```

Infrequent access classes have a minimum billable object size and a minimum storage duration, so moving millions of tiny thumbnails to Standard-IA can cost more than leaving them hot; aggregate small files or keep them in Standard. Glacier Flexible Retrieval and Deep Archive are for compliance archives with retrieval measured in hours, never for files a user clicks on. One Zone-IA drops multi-AZ redundancy for a discount and suits data you can regenerate. Versioning with Object Lock protects against accidental deletes and malicious overwrites, and S3 Replication copies to another region for DR. Run storage class analysis before guessing thresholds.

**Follow-ups they will ask:**
- How you pick the day thresholds: storage class analysis and access logs show the age at which reads drop off; start conservative and tighten.
- Whether a transition costs anything: yes, a per-request fee, which is why small objects should not churn between classes.
- How you honor a user's deletion request: delete all versions and delete markers under the prefix, confirm with S3 Inventory, and remember replicas and backups.

**Mistakes to avoid:**
- Proposing Glacier for anything a user expects instantly.
- Turning on versioning without a noncurrent version expiration rule.

### Q. How do presigned URLs work, and how would you build a secure direct-to-S3 upload for large files from a React app?

**Short answer (45 seconds):** A presigned URL is an S3 request signed with your credentials: it fixes the operation, the key and an expiry, so whoever holds it can perform exactly that operation until it expires. My API authenticates the user, chooses the object key itself, enforces content type and size constraints, and returns a presigned PUT URL or, for large files, a multipart upload ID with one presigned URL per part. The browser uploads straight to S3, then calls the API to complete the upload and record the file.

**Deeper explanation:**

```js
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
const s3 = new S3Client({});
const key = `uploads/${userId}/${randomUUID()}.pdf`;
const url = await getSignedUrl(s3, new PutObjectCommand({
  Bucket: "acme-uploads", Key: key, ContentType: "application/pdf",
}), { expiresIn: 300 });
```

The URL is only as powerful as the signing identity, so sign with a role that can write to the uploads prefix and nothing else, and keep the expiry short. Signed parameters such as content type are enforced by S3, and presigned POST adds a content length range. For multipart the client asks your API to CreateMultipartUpload, uploads each part to its presigned URL, collects the ETags and asks the API to CompleteMultipartUpload; a lifecycle abort rule cleans up abandoned uploads. Bucket CORS must allow the app origin and expose the ETag header or the browser cannot read it.

**Follow-ups they will ask:**
- Why not proxy uploads through the API: it doubles bandwidth, ties up the Node event loop on large bodies and hits payload limits.
- How you verify what arrived: an S3 event triggers a scan or metadata extraction, and the database row stays pending until it passes.
- How long a presigned URL can live: no longer than the credentials that signed it, with a hard cap of seven days for SigV4.

**Mistakes to avoid:**
- Letting the client choose the key, which allows overwriting other users' objects.
- Forgetting bucket CORS and debugging a generic browser network error for an hour.

### Q. How do S3 event notifications work, when would you use EventBridge instead, and what are the delivery guarantees?

**Short answer (45 seconds):** S3 publishes events such as ObjectCreated and ObjectRemoved to an SQS queue, an SNS topic, a Lambda function or EventBridge. Classic notifications are configured per bucket with prefix and suffix filters and a limited set of destinations; the EventBridge integration is switched on once and then any number of rules with rich pattern matching route the events, including across accounts. Delivery is at least once and unordered, so consumers must be idempotent and must not assume a PUT event arrives before a later DELETE of the same key.

**Deeper explanation:** The standard pipeline is upload, event to SQS, worker pulls and processes, result written to the database. SQS adds buffering, retries and a dead-letter queue, where invoking Lambda directly gives neither buffer nor backpressure. With EventBridge one upload can fan out to several rules (thumbnail, text extraction, audit) filtered on key pattern or object size without touching the bucket configuration.

```text
PUT uploads/u1/a.pdf -> S3 -> EventBridge rule (suffix .pdf) -> SQS -> Fargate worker -> Postgres
                                                              -> Lambda (audit log)
```

Because events can duplicate, the worker keys its work by bucket, key and version ID or ETag and records completion, so a repeated event becomes a no-op. Events also fire for your own writes: a worker that writes output into the watched prefix creates an infinite loop unless it writes elsewhere or the filter excludes it.

**Follow-ups they will ask:**
- Events for objects that already exist: notifications only cover new events; backfill with S3 Inventory or a listing job.
- How you detect a missed event: reconcile S3 Inventory against your database periodically; cheap insurance even though delivery is reliable.
- Lambda directly or through SQS: SQS for anything with downstream limits or long processing; direct only for tiny, fast, idempotent reactions.

**Mistakes to avoid:**
- Writing processed output back into the watched prefix and triggering on your own output.
- Assuming exactly-once or ordered delivery.

### Q. EBS versus EFS versus instance store: when do you use each?

**Short answer (45 seconds):** EBS is a network block volume attached to one instance in one AZ, the default disk for databases and anything needing a filesystem with predictable IOPS; gp3 for most things, io2 for high IOPS with low variance. EFS is a shared NFS filesystem that many instances, containers or Lambda functions across AZs mount at once, for shared assets, model files or legacy apps that assume a shared disk; it costs more per GB and has higher per-operation latency. Instance store is NVMe on the host itself: fastest, but gone when the instance stops, so it is for caches, scratch space and replicated systems.

**Deeper explanation:** EBS snapshots incrementally to S3, resizes online and encrypts with KMS by account default. gp3 lets you provision IOPS and throughput independently of size, unlike gp2 where performance scaled with capacity. Because EBS is zonal, a Multi-AZ database on EC2 means replication at the database layer, not the disk layer. Throughput is also capped by the instance's EBS bandwidth, which trips people who buy a fast volume for a small instance.

EFS scales automatically, charges per GB stored plus throughput, and has a lifecycle to an infrequent access class. It suits containers that need shared writable state and Lambda functions that need more than ephemeral storage. For high-throughput machine learning data, FSx for Lustre is the faster shared option and can front an S3 bucket.

**Follow-ups they will ask:**
- Can two instances mount one EBS volume: only with io2 Multi-Attach in one AZ and a cluster-aware filesystem; not a general answer.
- How to back up EFS: AWS Backup, which also schedules EBS snapshots and RDS backups with retention policies.
- Where model weights should live for fast GPU pod startup: pre-pulled on the node or on FSx for Lustre linked to S3, not downloaded from S3 on every start.

**Mistakes to avoid:**
- Putting a database on instance store without replication and calling it a cost optimization.
- Using EFS for high write rates of small files; per-operation latency will hurt.

### Q. RDS versus Aurora, and Multi-AZ versus read replicas. What does a Node.js app actually experience during a failover?

**Short answer (45 seconds):** RDS runs the standard engine on an instance with EBS storage; Aurora keeps the wire protocol but replaces storage with a distributed volume across three AZs, giving faster failover, up to 15 low-lag replicas and storage that grows on its own, at a higher price. Multi-AZ is for availability: a synchronous standby that takes over behind the same endpoint and is not readable. Read replicas are for scale: asynchronous copies with their own endpoints that can be promoted. During failover the app sees connection errors for a minute or two on RDS and usually much less on Aurora, then DNS points at the new primary.

**Deeper explanation:** What breaks in Node is your connection pool: every socket dies, in-flight transactions fail, and the pool reconnects to the hostname, which resolves to the new primary once the DNS TTL expires. Treat connection errors as retryable once, keep timeouts short and never cache resolved IPs. RDS Proxy holds connections across a failover and shields the database from a thousand Lambda environments each opening a pool.

```text
RDS Multi-AZ   : primary <-sync-> standby, one endpoint, standby not readable
Aurora cluster : writer + reader endpoints, shared storage, fast promotion
Read replica   : async, lagging, own endpoint, for reports
```

RDS Multi-AZ DB clusters are a newer variant with two readable standbys, and Aurora Global Database replicates across regions with low lag. Replicas serve stale data, so route only lag-tolerant reads there.

**Follow-ups they will ask:**
- How to test failover safely: reboot with failover on RDS or failover-db-cluster on Aurora in staging under load.
- How Aurora Serverless v2 bills: in capacity units that scale within a range you set, so you pay for a floor you accept.
- Backups: automated snapshots plus transaction logs give point-in-time recovery within the retention window, and snapshots copy across regions for DR.

**Mistakes to avoid:**
- Saying Multi-AZ gives read scaling; the classic standby is not readable.
- Sending every query to the reader endpoint and then debugging "I just wrote it and it is not there".

### Q. Would you use pgvector on RDS or Aurora PostgreSQL as the vector store for a RAG system? What are the trade-offs against OpenSearch?

**Short answer (45 seconds):** Yes for most products up to a few million embeddings, because the vectors live next to the documents and permissions they belong to, so tenant filtering is a WHERE clause and writes are transactional with the rest of the record. The trade-offs are operational: HNSW build time and memory, tuning ef_search for recall, and vector queries competing with normal application load. OpenSearch gives dedicated k-NN infrastructure, hybrid lexical plus vector search and horizontal scale, at the cost of a second system to run and sync.

**Deeper explanation:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE chunks (id bigserial PRIMARY KEY, doc_id bigint, tenant_id int,
  body text, embedding vector(1024));
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
SELECT id, body FROM chunks WHERE tenant_id = 42
ORDER BY embedding <=> $1 LIMIT 8;
```

HNSW gives good recall with no training step but slow builds; IVFFlat builds faster but must be created on populated data with lists tuned to row count. Filters interact with approximate indexes: a very selective tenant filter can return fewer rows than requested, so partition by tenant, use newer iterative scan options, or over-fetch and filter. HNSW indexes are large, so watch memory and put heavy reads on a replica. RDS and Aurora PostgreSQL both ship pgvector, and Bedrock Knowledge Bases can use Aurora as its store. OpenSearch adds BM25 for hybrid retrieval and shards across nodes, which matters once the index outgrows one instance's memory.

**Follow-ups they will ask:**
- How you measure recall: hold out queries, compute exact neighbors with a sequential scan, and compare index results at several ef_search values.
- Hybrid search in Postgres: combine a tsvector rank with vector distance using reciprocal rank fusion.
- When to leave Postgres: the index outgrows memory, vector load starves transactional queries, or write volume needs near real-time indexing at scale.

**Mistakes to avoid:**
- Building an IVFFlat index on an empty table, then wondering why recall is poor after bulk load.
- Treating cosine distance as a relevance score without a threshold or reranker.

### Q. Model a multi-tenant order system in DynamoDB. Explain partition keys, GSIs, single-table design and how hot partitions happen.

**Short answer (45 seconds):** DynamoDB hashes the partition key to place an item, and each partition has a fixed throughput ceiling, so the key must spread load evenly. I start from access patterns, not entities: get an order by ID, list a customer's orders by date, list a tenant's orders by status. One table with generic PK and SK covers them: PK TENANT#1#CUSTOMER#77 with SK ORDER#timestamp, plus a GSI keyed on TENANT#1#STATUS#PAID with the timestamp as sort key. Hot partitions appear when many requests hit one key value, such as a tenant with far more traffic than the rest or a date-based key that funnels every write to today.

**Deeper explanation:**

```text
Table  PK=TENANT#1#CUSTOMER#77   SK=ORDER#2026-10-30T09:15Z#o123   status, total, items
       PK=ORDER#o123             SK=META                            tenant, customer
GSI1   GSI1PK=TENANT#1#STATUS#PAID   GSI1SK=2026-10-30T09:15Z      (orders by status)
```

Single-table design stores different entity types together so one query returns a customer with recent orders, at the cost of data that is unreadable without the access pattern document. GSIs are eventually consistent copies with their own capacity that can project only needed attributes; LSIs share the partition key and exist only if defined at table creation. Adaptive capacity smooths uneven keys but cannot exceed the per-partition ceiling, so a celebrity tenant needs write sharding: a small random suffix on the key, with shards queried in parallel. Streams feed change events to Lambda for projections and search indexing, TTL expires items for free, and transactions group up to 100 items.

**Follow-ups they will ask:**
- Why not add indexes like in Postgres: each GSI costs write capacity and storage, and you cannot query an attribute without a key or index, so patterns must be known up front.
- Ad hoc analytics: export to S3 and query with Athena, or stream into OpenSearch; DynamoDB is not for scans.
- Item size limit: 400 KB, so large payloads go to S3 with a pointer in the item.

**Mistakes to avoid:**
- Choosing a low-cardinality partition key such as status or date.
- Scanning the table in a request path because "the data is small for now".

### Q. When do you reach for ElastiCache, OpenSearch and DocumentDB, and why might you still choose MongoDB Atlas on AWS?

**Short answer (45 seconds):** ElastiCache is the managed Redis, Valkey or Memcached layer for caching, sessions, rate limiting and locks, where latency must be sub-millisecond and the data is reconstructible. OpenSearch Service is for full-text search with relevance scoring, log analytics and k-NN vector search, where LIKE queries or Mongo text indexes stop scaling. DocumentDB speaks the MongoDB wire protocol so existing drivers work, but it is a different engine with feature gaps, so a team that depends on recent MongoDB features or Atlas Search usually stays on Atlas, which runs inside AWS regions with PrivateLink into your VPC.

**Deeper explanation:** ElastiCache design questions: eviction policy (allkeys-lru for a pure cache, noeviction for queues and locks), cluster mode to shard past one node's memory, replicas for failover, and whether ElastiCache Serverless fits your traffic. Commands worth naming: SET NX PX for locks, INCR with EXPIRE for rate limits, sorted sets for leaderboards.

OpenSearch domains need shard, instance and storage planning; OpenSearch Serverless removes that at a higher minimum cost. It indexes JSON with analyzers, supports BM25 and k-NN, and ships Dashboards for logs.

DocumentDB versus Atlas is a compatibility and operations call: DocumentDB gives IAM, VPC-native networking and Aurora-style storage with no extra vendor; Atlas gives the real engine, the newest aggregation features and Atlas Search. Check driver and feature usage against the DocumentDB compatibility list before promising a migration.

**Follow-ups they will ask:**
- Redis as the only datastore: no; treat it as ephemeral unless you configure persistence and accept the durability trade-offs, and even then keep records in a database.
- Search in Postgres instead: tsvector with GIN indexes covers a lot; move to OpenSearch for relevance tuning, facets, typo tolerance and large corpora.
- Keeping OpenSearch in sync: change data capture (DynamoDB Streams, Debezium on Postgres, Mongo change streams) into the index, plus a periodic full reindex.

**Mistakes to avoid:**
- Saying DocumentDB is MongoDB; interviewers who have migrated know the gaps.
- Using Redis for data you cannot afford to lose without persistence or replicas.

### Practice
- Build the upload flow: presigned PUT from an Express endpoint, S3 event to SQS, a worker that records metadata in Postgres; upload the same file twice and prove the worker is idempotent.
- Load a few hundred thousand embeddings into pgvector on a local Postgres, build an HNSW index and measure recall against exact search at three ef_search values.
- Write the DynamoDB access pattern table for a small app you know, implement it as a single table, and query each pattern with the CLI.
- Fail over a Multi-AZ RDS instance in a sandbox while a Node script writes in a loop; log how long errors last and how the pool recovers.
- Say it out loud: explain Multi-AZ versus read replicas to a product manager in under a minute, including what each costs.

## Messaging & Event-driven Architecture

> This is where interviewers test distributed systems thinking in AWS vocabulary. A weak answer is "SQS is a queue, SNS is pub/sub". A strong answer does the visibility timeout arithmetic, designs the dead-letter path, puts idempotency keys in the consumer, knows when Kafka earns its complexity, and says plainly that exactly-once delivery does not exist end to end.

### Concepts you must understand
- SQS standard queues deliver at least once with best-effort ordering and nearly unlimited throughput; FIFO queues deliver in order per message group and deduplicate by ID within a five minute window, at lower throughput.
- The visibility timeout hides a message while a consumer works on it; if the consumer does not delete it in time it reappears, so the timeout must exceed processing time and the consumer must be idempotent.
- A dead-letter queue receives a message after maxReceiveCount failed receives; the redrive feature moves messages back to the source once the bug is fixed.
- SNS fans one message out to many subscribers (SQS, Lambda, HTTP, email) with filter policies; SNS into SQS gives each consumer its own durable buffer.
- EventBridge is a serverless event bus with content-based rules, a schema registry, archive and replay, cross-account routing and SaaS sources; it is the default integration backbone for AWS service events.
- Kinesis Data Streams and MSK (Kafka) are ordered, replayable logs split into shards or partitions; choose them for streaming analytics, many consumers over the same data, or replay, not for a work queue.
- Step Functions orchestrates workflows as state machines with retries, catches, parallel and map states and direct service integrations; Standard workflows are durable and long-running, Express workflows are fast and high volume.
- Idempotent consumers make at-least-once safe: an idempotency key stored with a conditional write turns a duplicate into a no-op.
- Exactly-once end to end does not exist; FIFO deduplication and Kafka transactions cover one segment, and every external side effect still needs idempotency.

### Q. SQS standard versus FIFO, and how do visibility timeout and long polling work? Configure a queue for a worker that takes about two minutes per message.

**Short answer (45 seconds):** Standard queues deliver at least once, in roughly the original order, with practically unlimited throughput. FIFO queues guarantee order within a message group and deduplicate by deduplication ID for five minutes, with a throughput ceiling. The visibility timeout hides a received message from other consumers; if the consumer has not deleted it when the timeout expires, it is redelivered. Long polling makes ReceiveMessage wait up to 20 seconds instead of returning empty, which cuts cost and latency. For a two minute job I set the timeout to several minutes, extend it from the worker if processing runs long, and delete only after the side effects are committed.

**Deeper explanation:**

```js
const { Messages = [] } = await sqs.send(new ReceiveMessageCommand({
  QueueUrl, MaxNumberOfMessages: 5, WaitTimeSeconds: 20, VisibilityTimeout: 300 }));
for (const m of Messages) {
  const heartbeat = setInterval(() => sqs.send(new ChangeMessageVisibilityCommand({
    QueueUrl, ReceiptHandle: m.ReceiptHandle, VisibilityTimeout: 300 })), 120_000);
  try {
    await processIdempotently(m);
    await sqs.send(new DeleteMessageCommand({ QueueUrl, ReceiptHandle: m.ReceiptHandle }));
  } finally { clearInterval(heartbeat); }
}
```

A timeout shorter than processing means a second worker picks up the same message and the work happens twice, the most common SQS bug; a far too long timeout delays retry after a crash. FIFO queues need a message group ID: one group serializes everything, so use a key such as order ID for ordering where it matters and parallelism across groups. Message size is capped, so large payloads go to S3 with a pointer.

**Follow-ups they will ask:**
- When FIFO is the wrong choice: high throughput with no ordering need, or consumers that already handle ordering with version numbers.
- How Lambda consumes SQS: an event source mapping polls and scales for you; set the visibility timeout above the function timeout.
- What a delay queue does: hides new messages for a period, useful for scheduled retries.

**Mistakes to avoid:**
- Deleting the message before the work is durably done.
- Using one message group ID for the whole FIFO queue and wondering why throughput is one message at a time.

### Q. Design retries, dead-letter queues and redrive for a document-processing worker. How do you avoid poison messages and retry storms?

**Short answer (45 seconds):** The queue gets a redrive policy: after maxReceiveCount failed receives, SQS moves the message to a dead-letter queue instead of redelivering forever. In the worker I separate transient failures (timeouts, LLM API throttling) from permanent ones (corrupt file, unsupported format): transient failures let the message return after the visibility timeout with backoff, permanent ones go straight to the DLQ or a quarantine table with the error attached. An alarm on DLQ depth pages someone, and once the bug is fixed the redrive feature moves messages back to the source queue at a controlled rate.

**Deeper explanation:** Retry storms happen when every consumer retries at the same moment after a dependency fails. Add jitter by varying the visibility timeout on failure (ChangeMessageVisibility with a growing, randomized value) and consider a circuit breaker that pauses consumption while the downstream is unhealthy. For Lambda consumers, ReportBatchItemFailures lets a batch succeed partially instead of retrying all ten messages because one failed.

```json
{
  "RedrivePolicy": {
    "deadLetterTargetArn": "arn:aws:sqs:ap-south-1:111122223333:docs-dlq",
    "maxReceiveCount": "5"
  }
}
```

The DLQ keeps the original attributes plus the receive count, and its retention should be longer than the source queue's so nothing expires during the investigation. For permanent failures I also write a row in Postgres with the document ID, error class and stack trace, because support needs to tell the user what to fix without digging through a queue.

**Follow-ups they will ask:**
- maxReceiveCount of one or ten: low values push transient failures into the DLQ too eagerly; three to five with backoff is a common middle, tuned to your failure mix.
- Redrive to a different queue: yes, redrive can target the source or a custom destination, useful for replaying into a fixed worker.
- How this maps to Kafka: there is no built-in DLQ; consumers publish failed records to a dead-letter topic themselves and commit the offset.

**Mistakes to avoid:**
- No DLQ, so one poison message loops forever and delays everything behind it.
- Retrying a non-retryable error (invalid file) five times before admitting defeat.

### Q. SNS fan-out versus EventBridge: when do you use which, and how do filter policies, schemas and replay fit in?

**Short answer (45 seconds):** SNS is a topic that pushes each message to every subscriber, commonly SQS queues so each consumer gets its own durable buffer, with filter policies to subscribe to a subset. EventBridge is an event bus with content-based rules on the JSON body, targets in other accounts and SaaS endpoints, a schema registry, and archive and replay. I use SNS for high volume fan-out of simple notifications with the fewest moving parts, and EventBridge as the integration backbone between services and for reacting to AWS service events.

**Deeper explanation:**

```text
Order service -> SNS "orders" -> SQS billing  (filter: type = order.created)
                               -> SQS email    (filter: type in [order.created, order.shipped])
Order service -> EventBridge   -> rule detail.status = "paid" -> Step Functions
                               -> rule any order event        -> archive (replay later)
```

Rules match on body fields with numeric, prefix and existence operators, and input transformers reshape the payload. The schema registry infers schemas from traffic and generates code bindings. Archive and replay can rebuild a projection or replay a day's events into a fixed consumer, which SNS cannot do. Pipes connects a source such as SQS to a target with filtering and enrichment, and Scheduler replaces cron.

SNS wins on throughput and per-message cost at scale, offers FIFO topics for ordered fan-out, and is the simplest push to HTTP, mobile and email. Both are at least once, so consumers still need idempotency.

**Follow-ups they will ask:**
- Why SNS to SQS instead of SNS to Lambda directly: the queue absorbs bursts, retries and gives a DLQ; direct delivery has limited retry behavior.
- Routing events across accounts: an EventBridge rule can target a bus in another account that has a matching resource policy.
- Versioning events: include a version field, register the schema, and keep consumers tolerant of unknown fields.

**Mistakes to avoid:**
- Using EventBridge as a queue; it has no pull model, so put SQS behind it when you need buffering.
- Expecting classic SNS attribute filters to see the message body; payload-based filtering is a separate option you enable.

### Q. Kinesis Data Streams versus MSK versus SQS: pick for a clickstream analytics feed, an order event log with several consumers, and a background job queue.

**Short answer (45 seconds):** Kinesis and Kafka are ordered, replayable logs split into shards or partitions where every consumer group reads the same data independently; SQS is a work queue where each message is consumed once and deleted. Clickstream analytics goes to Kinesis Data Streams with Firehose delivering to S3 for Athena, because it is high volume, append-only and AWS-native. The order event log fits either Kinesis or MSK: MSK when the team already speaks Kafka, needs the connector ecosystem or long retention; Kinesis when I want zero cluster operations and AWS consumers. The background job queue is SQS, full stop.

**Deeper explanation:** The scaling unit differs. Kinesis shards each have fixed write and read throughput, so you add shards or use on-demand mode, and consumers share read capacity unless they use enhanced fan-out. Kafka partitions scale with brokers, and the consumer group protocol assigns partitions to consumers, giving parallelism up to the partition count and ordering per key. Retention is where logs differ from queues: data stays for the configured window and replay from an offset is a first-class operation.

```text
SQS     : queue, delete after consume, no replay, scales without planning
Kinesis : shards, ordered per partition key, replay within retention, AWS-native consumers
MSK     : Kafka partitions, consumer groups, Connect and Streams ecosystem, you tune the cluster
```

MSK still asks you to size brokers, storage and partitions and to upgrade versions; MSK Serverless reduces that with its own limits. Kinesis is an API with per-shard or on-demand pricing and no cluster.

**Follow-ups they will ask:**
- Choosing a partition key: one that spreads evenly but keeps related events together, such as user ID or order ID.
- Consumer lag monitoring: IteratorAgeMilliseconds on Kinesis, consumer group lag on Kafka, ApproximateAgeOfOldestMessage on SQS.
- Kafka from Node or Python: KafkaJS or confluent-kafka with IAM authentication to MSK; commit offsets after processing.

**Mistakes to avoid:**
- Using Kafka as a job queue and then fighting partition count to get consumer parallelism.
- Treating Kinesis and Kafka as SQS with extra steps; a log is read, not consumed.

### Q. When do you orchestrate with Step Functions instead of chaining events, and how would you model a RAG ingestion workflow?

**Short answer (45 seconds):** Choreography, where services react to each other's events, decouples well but makes the overall process invisible: nobody can answer "where is document 123" without stitching logs together. Orchestration with Step Functions makes the process explicit as a state machine with retries, catches, timeouts and a visible execution history per item. I orchestrate when the flow has many steps, compensation logic or waits for humans, and choreograph when steps are independent. For RAG ingestion I would use a Standard workflow: extract text, chunk, embed in parallel with a Map state, upsert vectors, update the document status, with a Catch that marks the document failed.

**Deeper explanation:**

```json
{"StartAt": "Extract", "States": {
  "Extract": {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke", "Next": "Chunk",
    "Retry": [{"ErrorEquals": ["States.TaskFailed"], "MaxAttempts": 3, "BackoffRate": 2}]},
  "Chunk": {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke", "Next": "Embed"},
  "Embed": {"Type": "Map", "ItemsPath": "$.chunks", "MaxConcurrency": 10, "Next": "Upsert",
    "ItemProcessor": {"StartAt": "EmbedChunk", "States": {"EmbedChunk":
      {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke", "End": true}}}},
  "Upsert": {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke", "End": true}
}}
```

Standard workflows run up to a year, record every transition and bill per transition, which suits long, important, lower volume processes. Express workflows run for at most five minutes, bill by duration and suit high volume event processing. Direct service integrations call DynamoDB, SQS, Bedrock and SageMaker without a Lambda in between, and Distributed Map fans out over millions of S3 objects. MaxConcurrency on the Map state is how you respect the embedding API's rate limit.

**Follow-ups they will ask:**
- Waiting for a human or external callback: a Task with a task token pauses until SendTaskSuccess is called.
- Idempotency of steps: each task still needs to be safe to retry, because Step Functions retries the whole task.
- Cost at volume: per-transition pricing adds up for millions of tiny executions; Express or SQS with a worker is cheaper there.

**Mistakes to avoid:**
- Putting business logic in the state machine definition instead of the tasks, which makes it untestable.
- Using Standard workflows for millions of small executions and getting a surprise bill.

### Q. How do you make a consumer idempotent? Show me what the code looks like.

**Short answer (45 seconds):** Every message carries or derives an idempotency key, such as order ID plus event type, or the message deduplication ID. Before doing the side effect the consumer records that key with a conditional write that fails if it already exists; a failed write means a duplicate, which gets acknowledged without reprocessing. The key record and the business write share one transaction when they share a database; otherwise the key is written first as pending and finalized after the side effect, so a crash in between causes a safe retry rather than a double effect.

**Deeper explanation:**

```sql
BEGIN;
INSERT INTO processed_events (event_id) VALUES ($1) ON CONFLICT DO NOTHING;
-- zero rows inserted means already handled: ROLLBACK and ack the message
UPDATE orders SET status = 'paid' WHERE id = $2 AND status = 'pending';
COMMIT;
```

```python
table.put_item(                                   # DynamoDB: conditional put as the dedup record
    Item={"pk": f"EVT#{event_id}", "ttl": now + 7 * 86400},
    ConditionExpression="attribute_not_exists(pk)")
```

When the side effect is external, such as a card charge or a paid LLM call, pass the same key downstream: Stripe accepts an Idempotency-Key header and your own APIs should too. Make the operation itself idempotent where possible: set status to paid rather than increment a counter, and compare versions to drop stale events. The processed_events table needs TTL or a retention job.

**Follow-ups they will ask:**
- Crash after the side effect but before the ack: the message is redelivered, the conditional write fails, you ack; that is why the key is written first or in the same transaction.
- Out of order delivery on standard queues: compare event versions or timestamps and ignore anything older than the current state.
- Redis for the key store: SET NX PX is fast, but losing Redis loses the dedup memory, so only when a rare duplicate is acceptable.

**Mistakes to avoid:**
- Checking with a SELECT and then inserting, which races between two consumers; the write must be conditional.
- Deduplicating in memory inside one process and calling it idempotency.

### Q. A stakeholder says the payments pipeline must be exactly-once. What do you tell them?

**Short answer (45 seconds):** Exactly-once delivery across a distributed system does not exist, but exactly-once effect does, and that is what they actually want. Messaging systems give at-least-once, and some deduplicate within a window, but the moment a consumer calls a third-party API or writes to a database and crashes before acknowledging, the only defense is an idempotent consumer. So the design is at-least-once delivery plus idempotency keys at every side effect, tested by deliberately injecting duplicates.

**Deeper explanation:** The gap is the dual-write problem: the side effect and the acknowledgement are two operations with no atomic way to do both across systems. Kafka transactions make consume-process-produce atomic inside Kafka, which gives exactly-once for stream processing that stays in Kafka, not for the database or payment API at the edge. FIFO deduplication only covers producers resending the same ID within five minutes; a consumer failure after processing still causes redelivery.

```text
Producer retry -> duplicate message : dedup ID or idempotent producer
Consumer crash -> redelivery        : idempotency key + conditional write
External API   -> double charge     : pass the idempotency key downstream
Out of order   -> stale update      : version check before applying
```

For payments: generate the payment intent ID in the order service, store it before calling the provider, send it as the provider's idempotency key, and reconcile daily against the provider's records. Reconciliation is the part people forget and the part that catches what the rest miss.

**Follow-ups they will ask:**
- Does the outbox pattern help: yes, writing the event to an outbox table in the same transaction as the business change and relaying it removes the dual write on the producer side.
- Where exactly-once is real: inside one database transaction, or inside Kafka Streams with transactions enabled, not across heterogeneous systems.
- How you test it: redeliver every message twice and kill consumers mid-processing in a test environment, then assert one charge per order.

**Mistakes to avoid:**
- Promising exactly-once because the queue has a FIFO label.
- Treating idempotency as a library setting rather than a data model decision.

### Practice
- Build an SQS worker in Node with long polling, a visibility heartbeat and a DLQ; kill the process mid-message, watch the redelivery, then redrive the DLQ.
- Publish ten thousand events through SNS to two SQS subscribers with filter policies and verify each queue received exactly the expected subset.
- Write a Step Functions state machine for a three-step ingestion with a Map state and a Catch, run it with a failing step, and read the execution history.
- Say it out loud: explain to a non-engineer why exactly-once is impossible and what you do instead, in 90 seconds.

## Serverless & API Patterns

> Serverless questions check whether you know the limits as well as the pitch. A weak answer is "Lambda scales infinitely and is cheap". A strong answer picks the right API Gateway type, explains concurrency and per-source retry semantics, has a cold start plan, can estimate the cost crossover against containers, and says clearly when serverless is wrong, especially for streaming LLM responses.

### Concepts you must understand
- API Gateway comes in three products: REST APIs (usage plans, API keys, request validation, caching, WAF, private endpoints), HTTP APIs (cheaper, lower latency, built-in JWT authorizer, fewer features) and WebSocket APIs (persistent connections with routes and connection IDs).
- Lambda concurrency is the number of execution environments running at once; the account has a regional quota, reserved concurrency caps one function and protects the rest, and provisioned concurrency keeps environments initialized ahead of demand.
- Event sources differ in retry semantics: synchronous callers get the error back; asynchronous invocations retry twice then go to a destination or DLQ; poll-based mappings (SQS, Kinesis, DynamoDB Streams, MSK) retry by leaving records on the source.
- Container image packaging ships large dependencies (up to 10 GB) through the Lambda runtime API; it suits ML libraries and teams that already build images in CI.
- Cold start mitigation: bundle small, initialize clients at module scope, lazy-load rare paths, right-size memory, use provisioned concurrency for latency-critical routes and SnapStart where supported.
- Cost is requests plus GB-seconds plus API Gateway, logs and data transfer; serverless is cheapest for spiky or low volume traffic and loses to containers at steady high throughput.
- Serverless is wrong for jobs beyond 15 minutes, GPU or very large memory, strict low latency with sparse traffic, heavy stateful WebSockets, and teams that need full-fidelity local debugging.
- Lambda response streaming through function URLs sends tokens as they arrive from a model; API Gateway buffering and integration timeouts make the classic request-response path a poor fit for slow generations.

### Q. API Gateway REST versus HTTP versus WebSocket APIs: which do you pick for a public SaaS API with API keys, an internal mobile backend, and a chat application?

**Short answer (45 seconds):** REST APIs have the full feature set: usage plans and API keys, request validation, caching, private endpoints and WAF, at a higher price per request. HTTP APIs are lean: lower latency and cost, a built-in JWT authorizer, CORS handling, but no usage plans or caching. WebSocket APIs hold persistent connections and route messages by a route key. So: REST for the public SaaS API because quotas and keys are built in, HTTP API for the mobile backend with JWT auth, and a WebSocket API for the chat app's push channel.

**Deeper explanation:** Lambda is the common integration, but both also proxy to an ALB or NLB through a VPC link or to any HTTP endpoint. Authorization options are IAM for service-to-service, Cognito user pools, Lambda authorizers for custom tokens, and JWT authorizers on HTTP APIs. Throttling exists on both; usage plans on REST add per-key quotas, which a billed public API needs.

```text
REST API  : keys, usage plans, validation, caching, WAF, private; higher cost
HTTP API  : cheap, fast, JWT authorizer, CORS; fewer knobs
WebSocket : $connect / $disconnect / $default routes, connection IDs, server push
```

A WebSocket API stores nothing for you: on $connect you save the connection ID in DynamoDB keyed by user, and you push by calling the management API with that ID. Connections have an idle timeout and a maximum lifetime, so clients must reconnect. For an LLM chat a worker pushes tokens as they are generated, which sidesteps request timeouts.

**Follow-ups they will ask:**
- Why not an ALB in front of Lambda: cheaper at high volume with longer timeouts, but no keys, usage plans, validation or WebSocket option.
- Custom domains: ACM certificates on a custom domain name mapped to stages, with Route 53 alias records.
- Versioning: stages or path prefixes, with the version in the path rather than a header so caches behave.

**Mistakes to avoid:**
- Picking REST "because our API is REST"; the name is a product tier, not an API style.
- Forgetting that a WebSocket API needs your own connection registry.

### Q. Explain Lambda concurrency. What are reserved and provisioned concurrency, what happens at the limit, and how do you protect the database behind it?

**Short answer (45 seconds):** Concurrency is the number of execution environments serving requests at once; each handles one request at a time, so concurrency is roughly requests per second times average duration in seconds. All functions in a region share an account quota. Reserved concurrency sets a hard ceiling for one function and carves that capacity out of the pool, protecting the rest of the account from a runaway function and guaranteeing the function its share. Provisioned concurrency keeps a chosen number of environments initialized so those requests never cold start, billed whether used or not. Beyond available concurrency, synchronous callers get a throttle error and asynchronous events are retried.

**Deeper explanation:** Throttling appears as 429s through API Gateway and as the Throttles metric, so alarm on it. Scaling is fast but happens at a fixed rate per function, so a sudden spike still sees throttles until capacity catches up. Each environment that opens a database connection is one more client, so a spike can open hundreds of Postgres connections in seconds; the fixes are RDS Proxy, reserved concurrency sized to what the database can hold, and one connection per environment at module scope.

```text
Account quota (regional) : shared pool
  fn A reserved = 100    : never more than 100, always up to 100
  fn B provisioned = 20  : 20 warm environments, bursts use on-demand capacity
  fn C unreserved        : competes for the remainder
```

For SQS triggers the event source mapping's maximum concurrency caps consumers without reserving capacity, a gentler way to throttle a worker.

**Follow-ups they will ask:**
- Provisioned concurrency cost: billed per environment-hour plus duration, so schedule it with Application Auto Scaling for business hours.
- Reserved concurrency of zero: disables invocation, a quick kill switch in an incident.
- Where throttled asynchronous events go: retried within the maximum event age (six hours by default), then to the on-failure destination or DLQ.

**Mistakes to avoid:**
- Saying Lambda scales infinitely; the account quota and downstream connections are real limits.
- Buying provisioned concurrency for every function instead of the latency-critical path.

### Q. Compare the invocation models: a synchronous API call, an S3 event, and an SQS trigger. How do retries differ, and what is a partial batch response?

**Short answer (45 seconds):** Synchronous invocations (API Gateway, ALB, function URLs, direct Invoke) return the result or error to the caller and Lambda does not retry; the client decides. Asynchronous invocations (S3, SNS, EventBridge) are queued by Lambda, retried twice on function error, then sent to an on-failure destination or dead-letter queue if configured. Poll-based event source mappings (SQS, Kinesis, DynamoDB Streams, MSK) have Lambda read the source for you; for SQS a failed batch becomes visible again after the visibility timeout and eventually reaches the queue's DLQ. A partial batch response reports which messages failed so only those return to the queue.

**Deeper explanation:**

```js
export const handler = async (event) => {
  const failures = [];
  for (const record of event.Records) {
    try { await processIdempotently(JSON.parse(record.body)); }
    catch { failures.push({ itemIdentifier: record.messageId }); }
  }
  return { batchItemFailures: failures };  // needs ReportBatchItemFailures on the mapping
};
```

For stream sources (Kinesis, DynamoDB Streams) order matters, so a failing record blocks its shard until it succeeds or the retry and age limits expire; bisect-on-error splits the batch to isolate the poison record and an on-failure destination receives metadata about what was skipped. Asynchronous invocations sit in an internal queue with a maximum event age, and Lambda destinations route successes and failures separately to SQS, SNS, EventBridge or another function, which beats a DLQ because the failure record includes the request and the error.

**Follow-ups they will ask:**
- Batch size and batch window: larger batches amortize cold starts and cost but widen the blast radius of a failure and add latency.
- Function timeout versus queue visibility timeout: keep visibility at least as long as the timeout, ideally a multiple, or messages are redelivered mid-run.
- Why Lambda is a good SQS consumer: it scales pollers with queue depth and you only pay for processing, not idle polling compute.

**Mistakes to avoid:**
- Throwing on one bad message and failing the whole batch, which retries nine good messages.
- Assuming synchronous invocations retry on failure; the client sees the error immediately.

### Q. When would you package a Lambda as a container image, and how does it differ from a zip deployment?

**Short answer (45 seconds):** Zip deployments are small, fast to deploy and start, and fit most Node and Python functions. Container images are for functions whose dependencies exceed the zip limits or need system libraries: PDF rendering with native binaries, scientific Python stacks, a tokenizer plus model files, or anything the team already builds as an image in CI. The image must implement the Lambda runtime API, which the AWS base images do for you, can be up to 10 GB, lives in ECR, and Lambda caches it near the execution environment so cold starts stay reasonable despite the size.

**Deeper explanation:**

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
COPY app/ ${LAMBDA_TASK_ROOT}/app/
CMD ["app.handler.lambda_handler"]
```

You can also start from any base image and add the Runtime Interface Client, and the Runtime Interface Emulator runs the image locally with the same invoke API. Layers are the zip-world way to share dependencies but still count against the unzipped size limit, so heavy ML dependencies usually push you to images. Image functions start from a cached snapshot of the filesystem rather than unzipping on every cold start, which is why large images are tolerable, though import-time work still matters.

Operationally the pipeline builds and pushes to ECR, the function references a specific image digest, and rollback is re-pointing the digest. Both packaging styles support the same triggers, memory and timeout settings.

**Follow-ups they will ask:**
- Does image size hurt cold starts: less than people expect because chunks load lazily, but what runs at import time still matters.
- Running Express in an image: yes with the Lambda Web Adapter, which translates events to HTTP against your listening port.
- Keeping images small anyway: multi-stage builds, slim bases and no dev dependencies.

**Mistakes to avoid:**
- Using a container image for a twenty line handler because "we use Docker everywhere".
- Shipping a plain web server image without an adapter; it never answers the runtime API.

### Q. Give me your cold start mitigation checklist for a Node.js Lambda that fronts a user-facing API.

**Short answer (45 seconds):** First measure: the Init Duration in the REPORT log line separates your code from the platform. Then shrink the bundle with esbuild so only used modules ship, import specific AWS SDK v3 clients, and move initialization to module scope so it runs once per environment. Raise memory above the minimum because CPU scales with it. Lazy-load rarely used paths. If p99 latency still matters more than cost, add provisioned concurrency on the API function, scheduled for peak hours.

**Deeper explanation:**

```js
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";   // one client, module scope
const ddb = new DynamoDBClient({});
let secretPromise;                                           // lazy, cached
const getSecret = () => (secretPromise ??= loadSecretOnce());
export const handler = async (event) => {
  const secret = await getSecret();
  return route(event, { ddb, secret });
};
```

Avoid frameworks that load dozens of modules on boot; if you must run Express, the Lambda Web Adapter works but framework init is part of every cold start. Keep the function out of a VPC unless it needs private resources; the old penalty is gone but there is nothing to gain. Track cold start percentage and Init Duration with Lambda Insights or Powertools metrics, and remember provisioned concurrency only covers the configured count, so bursts beyond it still cold start.

**Follow-ups they will ask:**
- SnapStart for Node: it began with Java and has expanded; verify support for your runtime and its restore hooks before relying on it.
- Right memory size: run a power tuning experiment across sizes and pick the cheapest that meets the latency target, since faster runs offset the higher per-millisecond price.
- Keep-warm pings: a scheduled invocation keeps one environment warm, not the twenty you need at peak, so it is a weak substitute.

**Mistakes to avoid:**
- Blaming AWS for a two second cold start that is really a 40 MB bundle and a database connection in the init path.
- Setting memory to the minimum to save money and paying for it in duration and latency.

### Q. Walk me through the Lambda cost model. When is serverless the wrong choice financially and architecturally?

**Short answer (45 seconds):** Lambda bills per request and per GB-second of duration, with API Gateway adding a per-request charge, and data transfer and CloudWatch Logs ingestion on top. That is unbeatable for spiky or low volume workloads because idle costs nothing. It loses to containers once traffic is steady and high: a function running at constant hundreds of requests per second pays for compute it could get far cheaper from a couple of Fargate tasks or Graviton instances under a Savings Plan. Architecturally it is wrong for jobs over 15 minutes, GPU or very large memory workloads, strict low latency with sparse traffic, and stateful long-lived connections.

**Deeper explanation:** Break-even thinking: estimate requests per month, average duration and memory, compute GB-seconds, then compare with the smallest container footprint that serves the same load with headroom. Include API Gateway, which at high volume can cost more than the Lambda compute itself. Include developer time: serverless removes patching and scaling work, real money for a small team, but adds debugging friction and vendor-specific plumbing.

```text
Spiky, low volume            -> Lambda wins (idle costs nothing)
Steady, high volume          -> containers win (utilization, Savings Plans)
Long jobs, GPUs, big memory  -> containers or AWS Batch
Streaming, WebSockets, state -> containers or a WebSocket API
```

Architectural costs are harder to price: cold starts in the p99, the 15 minute cap forcing awkward chunking, local development that never quite matches, and IAM sprawl. Serverless shines when the workload is event-shaped and the team embraces managed services end to end.

**Follow-ups they will ask:**
- Cost per function: cost allocation tags plus Cost Explorer, or duration metrics multiplied by configured memory.
- Compute Savings Plan and Lambda: yes, it discounts duration and provisioned concurrency charges.
- A hybrid: Lambda for bursty edges (webhooks, nightly jobs) and containers for the steady API core is common and sensible.

**Mistakes to avoid:**
- Claiming serverless is always cheaper or always dearer; it depends on utilization and you should be able to estimate it.
- Ignoring API Gateway and logging costs when quoting "Lambda is cheap".

### Q. We call an LLM from Lambda and want to stream tokens to the browser. How do you build it, and what breaks?

**Short answer (45 seconds):** The clean path is a Lambda function URL with response streaming: the Node handler is wrapped with awslambda.streamifyResponse, opens a streaming call to Bedrock or the model provider, and writes each chunk as it arrives, so time to first token is seconds rather than the whole generation. CloudFront in front gives a custom domain, WAF and TLS. What breaks is the classic request-response path: API Gateway buffers the response and enforces an integration timeout of about 29 or 30 seconds, long generations exceed it, and the 6 MB payload cap bites on big responses. You also pay Lambda duration while waiting on the model.

**Deeper explanation:**

```js
export const handler = awslambda.streamifyResponse(async (event, responseStream) => {
  responseStream.setContentType("text/event-stream");
  const res = await bedrock.send(new ConverseStreamCommand({ modelId, messages }));
  for await (const chunk of res.stream) {
    const delta = chunk.contentBlockDelta?.delta?.text;
    if (delta) responseStream.write(`data: ${JSON.stringify({ delta })}\n\n`);
  }
  responseStream.end();
});
```

A function URL authenticates with IAM or nothing, so with CloudFront in front use origin access control to require signed requests and do user auth in the function. Set the timeout to the longest acceptable generation. Through a WebSocket API instead, a worker pushes tokens to the connection ID with the management API, which also handles multi-turn sessions and reconnects. For steady chat traffic a Fargate service with Server-Sent Events avoids paying Lambda duration for waiting and keeps one code path.

**Follow-ups they will ask:**
- Can API Gateway stream: historically responses are buffered; check current documentation before promising it, and default to function URLs or a container.
- Client disconnects: watch for the stream closing and abort the model call so you stop paying for tokens nobody reads.
- Retries with streaming: a partial response cannot be replayed, so retry only before the first token and surface a clear error afterwards.

**Mistakes to avoid:**
- Putting a 29 second API Gateway integration in front of a 40 second generation and calling the 504 a model bug.
- Logging every token chunk to CloudWatch and multiplying log ingestion cost.

### Practice
- Deploy a Node function with a function URL and response streaming that proxies a Bedrock ConverseStream call; measure time to first token against a buffered version.
- Put an SQS trigger on a function with ReportBatchItemFailures, send a batch with one poison message, and confirm only that message returns to the queue.
- Run a power tuning experiment on one function at four memory sizes and record duration and cost per invocation.
- Say it out loud: explain reserved versus provisioned concurrency and when you would use each, in one minute.

## Observability & Operations on AWS

> Interviewers want proof that you can run what you build. A weak answer is "we use CloudWatch". A strong answer names the metrics and alarms, shows a log query, traces a request across a queue, has a tag strategy that makes the bill explainable, and states a DR plan with RTO and RPO numbers that were actually tested.

### Concepts you must understand
- CloudWatch metrics are time series with namespaces and dimensions; AWS services publish them automatically and your code publishes custom metrics with PutMetricData or, better, the embedded metric format inside structured log lines.
- CloudWatch Logs groups hold application logs; Logs Insights queries them with a pipe language, metric filters turn log patterns into metrics, and retention must be set on every group or logs cost forever.
- Alarms evaluate a metric or a math expression over periods with a datapoints-to-alarm setting; composite alarms combine alarm states with AND and OR so only meaningful combinations page.
- X-Ray traces requests across services as segments and subsegments; the AWS Distro for OpenTelemetry (ADOT) is the vendor-neutral path that exports to X-Ray, CloudWatch or third parties.
- CloudTrail is the API audit trail, CloudWatch is operational telemetry, and AWS Config records configuration history; they answer different questions in an incident.
- Tags drive cost allocation, automation and access control; a mandatory tag set (owner, environment, service, cost-center) enforced through Organizations tag policies is the foundation of Cost Explorer breakdowns and Budgets.
- Systems Manager provides Session Manager for shell access without SSH or bastions, Run Command and Automation for fleet operations, Patch Manager for compliance, and Parameter Store.
- RTO is how long until the service is back and RPO is how much data you may lose; backup and restore, pilot light, warm standby and active-active trade rising cost for smaller numbers.
- AWS Backup centralizes backup plans across EBS, RDS, DynamoDB, EFS and S3 with cross-region and cross-account copies, which is the basis of every DR tier.

### Q. How do you alert on p99 latency and error rate for an API behind an ALB on ECS without paging people for noise?

**Short answer (45 seconds):** I alarm on symptoms users feel, not on causes: the ALB TargetResponseTime at the p99 statistic and the ratio of 5xx responses to total requests, computed with metric math so two errors on a quiet night do not page. Each alarm evaluates several periods with a datapoints-to-alarm setting such as three of five, treats missing data as not breaching, and feeds a composite alarm that pages only when latency and errors are both bad or either is catastrophic. Cause-level alarms (CPU, memory, queue depth) go to a dashboard and a low-priority channel, not the pager.

**Deeper explanation:**

```text
Alarm A: p99 TargetResponseTime > 1.5 s for 3 of 5 one-minute periods
Alarm B: (HTTPCode_Target_5XX_Count / RequestCount) * 100 > 2 for 3 of 5 periods
Alarm C: HealthyHostCount < 2 for 2 periods
Composite: (A AND B) OR C  -> SNS -> on-call paging tool
```

Metric math handles the ratio and avoids alarming on raw counts, which scale with traffic. Percentile statistics need enough samples per period, so a one minute p99 at low traffic is jumpy; use five minute periods or p95. Anomaly detection builds a band from history and alarms when a metric leaves it, which suits daily seasonality better than a fixed threshold. Add dependency alarms on RDS connections and SQS oldest message age. Every alarm description links to a runbook; an alarm without a documented action is noise.

**Follow-ups they will ask:**
- Alarming on something that did not happen, like a nightly job: alarm on the metric being below one over 24 hours with missing data treated as breaching.
- Why composite alarms: fewer pages, suppression of dependent alarms during a known outage, and one alarm to attach to the on-call rotation.
- Business metrics: publish orders completed or tokens generated per minute and alarm on drops, because a healthy API serving wrong answers is still an outage.

**Mistakes to avoid:**
- Alarming on average latency, which hides the tail users complain about.
- Paging on CPU at 80 percent while the service is serving fine.

### Q. How do you structure logs so Logs Insights is actually useful, and how do you keep CloudWatch Logs costs under control?

**Short answer (45 seconds):** Every log line is one JSON object with a stable set of fields: timestamp, level, service, request ID, trace ID, tenant, route, status, duration and message, so Logs Insights parses them automatically and I can filter and aggregate without regex. Custom metrics ride in the same lines with the embedded metric format, so one write produces both a searchable log and a CloudWatch metric. Costs are controlled by setting retention on every group, logging at info in production with sampled debug, keeping payloads out of logs, and choosing the infrequent access log class for high volume groups you rarely query.

**Deeper explanation:**

```text
fields @timestamp, route, status, duration
| filter service = "orders-api" and status >= 500
| stats count() as errors, pct(duration, 99) as p99 by route
| sort errors desc
| limit 20
```

In Node, pino with JSON output is enough; add the trace ID to every line so a log search leads to the trace and back. For Lambda, Powertools for AWS Lambda provides the logger, metrics (EMF) and tracer with consistent fields. Metric filters turn log patterns into metrics for alarms without code changes, useful for components you cannot instrument.

Cost drivers are ingestion first, storage second, queries third; debug logging on a hot path can cost more than the compute running it. Subscription filters can stream logs through Kinesis Data Firehose to S3 for cheap long-term storage queried with Athena, leaving CloudWatch with a short retention window for operational search.

**Follow-ups they will ask:**
- PII in logs: do not log it; redact at the logger level and add a data protection policy on the log group as a backstop.
- Correlating logs across services: propagate a request ID header and the trace context, and log both everywhere.
- Logs Insights versus OpenSearch: Insights needs no infrastructure and suits operational queries; OpenSearch is for heavy analytics, dashboards and long retention.

**Mistakes to avoid:**
- Leaving log groups on never-expire retention, so the bill grows forever.
- Free-text console.log lines that Insights cannot parse.

### Q. A request goes ALB to ECS, publishes to SQS, is consumed by Lambda and writes to Postgres. How do you trace it end to end with X-Ray or OpenTelemetry, and how do you sample?

**Short answer (45 seconds):** Each hop records a span and propagates the trace context so the pieces join into one trace. The ALB adds an X-Amzn-Trace-Id header; the Express service, instrumented with the OpenTelemetry Node SDK or the X-Ray SDK, continues that trace and adds spans for the Postgres call and the SQS send; the context travels in an SQS message attribute; the Lambda picks it up through its tracing integration or the ADOT layer and records the database write. I export through the ADOT collector to X-Ray or CloudWatch Application Signals, sample a small percentage of normal requests and keep every error trace.

**Deeper explanation:**

```text
ALB (trace id) -> ECS orders-api [POST /orders] -> [pg INSERT] -> [sqs.send]
      SQS message attribute: AWSTraceHeader
Lambda consumer [handler] -> [pg UPDATE]        (linked to the producer span)
```

OpenTelemetry is the right default because it is vendor neutral: instrument once, then export to X-Ray, Jaeger, Honeycomb or Datadog by changing the collector configuration. On ECS the collector runs as a sidecar, on EKS as a DaemonSet, on Lambda as a layer. Auto-instrumentation covers Express, the pg driver, the AWS SDK and HTTP clients; you add manual spans around business steps such as an LLM call with attributes for model, tokens and latency. Sampling is decided at the head (first hop) or the tail (after seeing the whole trace, which needs the collector to buffer); X-Ray's default rule keeps a baseline per second plus a percentage, raised for new routes.

**Follow-ups they will ask:**
- Tracing through SQS specifically: the trace header rides in a message attribute and the consumer creates a span linked to the producer's, so the asynchronous hop appears as a link rather than a parent.
- What Application Signals adds: automatic service-level metrics, SLOs and service maps on top of traces for supported runtimes.
- Cost control: sampling rate, dropping health check spans, and limiting attribute cardinality.

**Mistakes to avoid:**
- Tracing inside one service only and calling it distributed tracing.
- Putting high-cardinality values like user IDs on metrics instead of traces, which explodes metric costs.

### Q. Design a tagging strategy and explain how you make the AWS bill explainable with Cost Explorer, Budgets and anomaly detection.

**Short answer (45 seconds):** Every resource carries a small mandatory tag set: owner, environment, service and cost-center, plus optional tags such as customer or feature. A tag policy in Organizations enforces allowed keys and values, and an SCP or Config rule denies or flags untagged production resources. The cost tags are activated as cost allocation tags so Cost Explorer can group and filter by them, Budgets alert the service owner on forecast and actual thresholds, and Cost Anomaly Detection watches each service's spend pattern and notifies on unexpected jumps the morning they happen.

**Deeper explanation:** Tags must be applied at creation in infrastructure as code; retrofitting is painful and untagged spend shows up as a blob. Cost Explorer groups by service, usage type, account, region or activated tag; the usage type view is what separates NAT processing from EC2 compute. Send a monthly report by service tag to each team; it is how engineers connect decisions to money.

```text
owner=payments-team  env=prod  service=orders-api  cost-center=cc-1042
Budget: filter service=orders-api, monthly, alert at 80% forecast and 100% actual
Anomaly monitor: per linked account, alert on absolute and percentage impact
```

Shared costs (NAT, Transit Gateway, support plan) have no clean tag; allocate them by percentage or accept a shared platform line. One account per environment and team makes the bill self-separating even where tags are missing. Compute Optimizer, Trusted Advisor and S3 Storage Lens then turn the explainable bill into a smaller one.

**Follow-ups they will ask:**
- Tags for access control: ABAC conditions on aws:ResourceTag let a team's role touch only resources carrying its team tag, so one tag set serves cost and security.
- Why both Budgets and anomaly detection: budgets catch slow drift against a plan, anomaly detection catches sudden spikes such as a runaway Lambda loop.
- What the CUR is: the Cost and Usage Report, raw line items delivered to S3 for Athena or a BI tool when Cost Explorer is not granular enough.

**Mistakes to avoid:**
- Tagging after the fact by hand; it never stays complete.
- One account-wide budget that nobody owns.

### Q. How do you get a shell on an instance in a private subnet without SSH or a bastion, and what else does Systems Manager do for a fleet?

**Short answer (45 seconds):** Session Manager: the SSM Agent keeps an outbound connection to Systems Manager, so with an instance role that allows it and no inbound port at all, I start a session from the console or CLI and get a shell authorized by IAM, logged to CloudWatch Logs or S3, and visible in CloudTrail. The same agent powers Run Command for executing a script across hundreds of instances, Patch Manager for scheduled OS patching with compliance reporting, State Manager for enforcing configuration, Automation runbooks for operational procedures, and Inventory for knowing what is installed where.

**Deeper explanation:**

```bash
aws ssm start-session --target i-0abc123def456
aws ssm start-session --target i-0abc123def456 \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["orders-db.xyz.ap-south-1.rds.amazonaws.com"],"portNumber":["5432"],"localPortNumber":["5432"]}'
```

The second command tunnels a local port to a private RDS endpoint through the instance, which replaces the bastion for database access and keeps every session attributable to an IAM identity. Instances in private subnets need a route to the SSM endpoints, through NAT or interface endpoints for ssm, ssmmessages and ec2messages. ECS Exec uses the same mechanism to open a shell inside a running Fargate task. Patch Manager runs in maintenance windows with patch baselines per OS and reports compliance to Security Hub, which answers the auditor's "how do you patch" question without a spreadsheet.

**Follow-ups they will ask:**
- Restricting who can shell into production: IAM conditions on ssm:resourceTag so a role reaches only instances with its team tag, plus MFA and session logging.
- Does it work on-prem or in other clouds: yes, hybrid activations register non-EC2 machines as managed nodes.
- Where Parameter Store fits: it lives under Systems Manager, which is why config and fleet tooling share a console.

**Mistakes to avoid:**
- Keeping port 22 open "just in case" after adopting Session Manager.
- Giving the instance role ssm:* instead of the managed core policy.

### Q. Define RTO and RPO, then compare backup and restore, pilot light, warm standby and active-active. What does each cost and when is each appropriate?

**Short answer (45 seconds):** RTO is the maximum time the business tolerates until the service works again; RPO is the maximum data loss expressed as time, so an RPO of one hour means losing up to an hour of writes is acceptable. Backup and restore copies backups to another region and rebuilds from infrastructure as code: cheapest, RTO in hours, RPO equal to backup frequency. Pilot light keeps the data layer replicating continuously with the application layer off or minimal: RTO in tens of minutes, RPO near zero. Warm standby runs a scaled-down but working copy: RTO in minutes. Active-active serves from both regions: RTO near zero, double the cost, and multi-region data consistency to solve.

**Deeper explanation:**

```text
Strategy          RTO             RPO              Cost     Data mechanism
Backup & restore  hours           backup interval  low      AWS Backup cross-region copies
Pilot light       tens of minutes seconds          medium   Aurora Global DB, S3 CRR, global tables
Warm standby      minutes         seconds          higher   same, plus a running minimal app tier
Active-active     near zero       near zero        highest  global tables, write partitioning
```

The application layer is easy because it is stateless and in code; the hard part is state: databases, in-flight queues, objects, secrets and DNS. Aurora Global Database replicates with low lag and promotes a secondary region; S3 Cross-Region Replication handles objects, with replication time control for predictable lag; DynamoDB global tables are multi-writer. Route 53 health checks or Application Recovery Controller shift traffic. For most products a pilot light with tested runbooks beats a warm standby nobody ever fails over to.

**Follow-ups they will ask:**
- Picking the tier: cost of downtime per hour against the monthly cost of the tier; the business sets RTO and RPO, engineering prices them.
- Why not Multi-AZ alone: it covers data center failures, not regional service events, data corruption or a bad deploy replicated everywhere.
- Backups versus replication: replication copies corruption instantly, so point-in-time backups stay necessary in every tier.

**Mistakes to avoid:**
- Quoting a DR tier without the RTO and RPO it delivers.
- Forgetting secrets, DNS, IAM and third-party allowlists in the failover plan.

### Q. How do you prove that backups and the DR plan actually work, and what belongs in an incident runbook?

**Short answer (45 seconds):** By restoring and failing over on a schedule, not by reading dashboards. Every quarter I restore the latest production backup into an isolated account, run the smoke tests against it and record the elapsed time, which becomes the measured RTO. Game days exercise the DR runbook end to end in staging, or in production during a quiet window if the business agrees, with someone deliberately breaking a dependency. The runbook is short and executable: triggers, who decides, exact commands, verification, communication, and fail back.

**Deeper explanation:** Checks catch silent failures: a backup job failing for a month, a snapshot copy that stopped when a KMS key policy changed, replication lag nobody alarmed on; those alarms belong next to the application alarms. Restore tests must include the awkward parts: secrets, DNS, credential rotation, and verifying data with row counts and checksums rather than "the database started".

```text
Runbook: region failover (orders platform)
1. Trigger : health check red 5 min AND AWS Health event for the region
2. Decide  : on-call lead + product owner, logged in the incident channel
3. Execute : promote Aurora secondary, scale ECS in DR region, flip ARC routing control
4. Verify  : synthetic checkout passes, error rate under 1%, queues draining
5. Comms   : status page, customer template, internal update every 30 minutes
6. Fail back: re-establish replication, controlled switch, post-incident review
```

Post-incident reviews feed alarms and runbooks; the sign of a healthy culture is how many runbook steps become automation after each exercise.

**Follow-ups they will ask:**
- How often to test: restores monthly or quarterly depending on RPO, full failover at least annually and after plan changes.
- Chaos tooling: AWS Fault Injection Service runs controlled experiments such as AZ loss or API throttling.
- Who declares an incident: anyone can raise it, a named on-call lead owns it, severity levels define the response.

**Mistakes to avoid:**
- Treating a successful backup job as proof of restorability.
- Runbooks that live in someone's head or in a wiki page nobody has opened since it was written.

### Practice
- Build a dashboard and alarms for a small API: p99 latency, 5xx ratio via metric math, healthy hosts, and a composite alarm to an SNS topic; trigger it with a load test and a forced error.
- Instrument an Express service with OpenTelemetry Node auto-instrumentation and the ADOT collector sidecar; find one request in X-Ray and follow it into an SQS consumer.
- Write a Logs Insights query that returns p99 duration and error count by route from your structured logs, then turn one pattern into a metric filter and alarm.
- Restore an RDS snapshot into a fresh VPC, time it, run the app's health checks against it, then delete everything.
- Say it out loud: explain pilot light versus warm standby with RTO, RPO and rough cost for each, in 90 seconds.

## AI Services on AWS and Equivalents

> For an AI engineering role this section checks cloud fluency against your LLM experience: can you call a model through Bedrock with IAM instead of API keys, do you know what Knowledge Bases and Agents do for you and when to build your own, can you price self-hosting honestly, and can you map what you did on GCP to AWS without stumbling over names. Managed agent products change quickly, so describe their shape and defer specifics to current documentation.

### Concepts you must understand
- Amazon Bedrock is the managed access layer for foundation models (Anthropic Claude, Amazon Nova, Meta Llama, Mistral, Cohere and others) behind one API with IAM authentication, no API keys, per-token on-demand pricing or provisioned throughput, and optional invocation logging to CloudWatch or S3.
- The Converse API gives a model-agnostic request shape for chat, tool use and streaming; InvokeModel exposes each provider's native request body.
- Bedrock Knowledge Bases is managed RAG: it ingests from S3 and other sources, chunks, embeds, writes to a vector store you choose (OpenSearch Serverless, Aurora PostgreSQL pgvector, Pinecone and others) and exposes Retrieve and RetrieveAndGenerate.
- Bedrock Agents orchestrates a model with action groups (Lambda functions or OpenAPI schemas) and knowledge bases; Bedrock AgentCore is a newer set of building blocks for agents you write yourself (runtime, memory, tool gateway, identity, observability), whose components should be checked for current availability.
- Bedrock Guardrails applies content filters, denied topics, word filters, sensitive information redaction and contextual grounding checks to inputs and outputs, and can run standalone through ApplyGuardrail.
- SageMaker AI hosts custom or open models on real-time endpoints, serverless inference (CPU only), asynchronous inference and batch transform; its Large Model Inference containers bundle vLLM or TensorRT-LLM.
- Self-hosting with vLLM on EKS or ECS gives full control over model, quantization and batching on G or P instances; you pay GPU hours busy or idle, so utilization decides whether it beats Bedrock.
- Bedrock quotas are per model per region and cross-region inference profiles spread load; both are real design constraints for production traffic.
- The architecture vocabulary is identical across clouds (object storage, queue, relational DB, vector store, managed model API, secrets, monitoring); only the product names change.

### Q. We call Claude today through the Anthropic API. What changes if we go through Amazon Bedrock, and how would you call it from a Node.js service?

**Short answer (45 seconds):** The model is the same; the plumbing changes. Bedrock authenticates with IAM instead of an API key, so an ECS task role or Lambda execution role calls it with no secret to manage, and every call lands in CloudTrail. Billing joins the AWS bill, on-demand per token or provisioned throughput. Traffic can stay inside your VPC through a PrivateLink endpoint, and AWS does not use your prompts to train models. The trade-offs are regional model availability, per-model quotas, and feature lag, since new models and features usually appear on the vendor's API first.

**Deeper explanation:**

```js
import { BedrockRuntimeClient, ConverseStreamCommand } from "@aws-sdk/client-bedrock-runtime";
const client = new BedrockRuntimeClient({});            // credentials from the task role
const res = await client.send(new ConverseStreamCommand({
  modelId: process.env.MODEL_ID,                        // model ID or inference profile ARN
  messages: [{ role: "user", content: [{ text: question }] }],
  toolConfig: { tools },                                // same tool shape across providers
  inferenceConfig: { maxTokens: 1024, temperature: 0.2 },
}));
for await (const event of res.stream) { /* contentBlockDelta, messageStop, metadata.usage */ }
```

Converse normalizes messages, tool use and streaming across providers, so switching models is a modelId change; InvokeModel sends the provider's native body when Converse has not wrapped a feature. Operationally you enable invocation logging, alarm on ThrottlingException because quotas are per model per region, and use cross-region inference profiles to spread load. Prompt caching and batch inference exist for cost; check current model support before promising either.

**Follow-ups they will ask:**
- Abstracting the provider: a thin client interface with a Bedrock and a direct implementation, shared tool schemas, and token and latency metrics per provider.
- Data residency: pick a region where the model is offered; a cross-region profile may route within a geography, so read its definition.
- Cost comparison: per-token list prices are similar; the differences are commitments, caching support and the value of consolidated billing and IAM.

**Mistakes to avoid:**
- Hardcoding a model ID without checking it exists in the target region.
- Treating Bedrock as a different model; weights and behavior are the vendor's, only the access layer changes.

### Q. What does a Bedrock Knowledge Base do for you, and when would you build your own RAG pipeline instead?

**Short answer (45 seconds):** A Knowledge Base is managed RAG: you point it at a data source such as an S3 bucket, choose a chunking strategy and an embedding model, pick a vector store, and it runs ingestion jobs and exposes two APIs: Retrieve returns ranked chunks with metadata, RetrieveAndGenerate adds the model call with citations. I use it when the corpus is documents, access control is coarse, and speed to production matters. I build my own when I need custom parsing, per-user permissions enforced at retrieval, hybrid search tuning, multi-step retrieval, or evaluation loops the managed path does not expose.

**Deeper explanation:**

```text
S3 docs -> KB ingestion (parse, chunk, embed) -> vector store (OpenSearch Serverless / Aurora pgvector)
Query   -> Retrieve(kbId, text, filter {tenant: "acme"}) -> chunks + scores + source URIs
        -> your prompt + Converse -> answer with citations
```

Knowledge Bases support metadata filtering through sidecar JSON files, several chunking strategies including hierarchical and semantic, optional reranking, and a custom transformation Lambda for parsing. Where it gets tight: complex PDFs and tables, tenant isolation that must be enforced at the index rather than by filter, retrieval evaluation (you still need a golden set and metrics), and vector store cost, where OpenSearch Serverless has a meaningful minimum footprint. Using Retrieve alone and doing generation yourself is the common middle path: managed ingestion and indexing, custom prompting and orchestration.

**Follow-ups they will ask:**
- Evaluating it: a question set with expected sources, measuring recall at k and answer faithfulness for the managed and the custom pipeline before choosing.
- Keeping the index fresh: scheduled or event-driven sync jobs; deletions in S3 propagate on the next sync.
- Multi-tenant isolation: metadata filters for low-risk data; separate knowledge bases or indexes for strict isolation.

**Mistakes to avoid:**
- Picking the vector store by default without pricing its minimum footprint.
- Assuming managed RAG removes the need for evaluation and prompt work.

### Q. What do Bedrock Agents and AgentCore give you compared with writing your own agent loop with tool calling or MCP? When is custom better?

**Short answer (45 seconds):** Bedrock Agents is a managed orchestrator: you give it instructions, action groups (Lambda functions or OpenAPI schemas) and optional knowledge bases, and it runs the loop, calls tools and keeps session state. AgentCore is a newer, modular set of services for agents you write with any framework: a runtime, memory, a gateway that turns APIs into tools, identity for delegated access, and observability. Custom is better when you need full control of the loop, specific framework features, MCP servers you already run, or portability; managed is better when you want the operational pieces without building them.

**Deeper explanation:** The questions for any agent platform: where the loop runs and scales, how tool access is authenticated, where memory lives, how you trace a multi-step run, how you evaluate it. Your own loop on ECS or Lambda answers them with code you own: a Converse call with tool definitions, a dispatcher that executes tools (local functions or MCP servers), DynamoDB for session state, a span per step; a few hundred lines you must maintain.

```text
Converse(tools) -> tool_use block -> dispatcher -> MCP server / Lambda / HTTP -> tool_result -> loop
State: DynamoDB session table     Tracing: span per step with tokens, latency, tool name
```

Managed agents remove the dispatcher, state and hosting but constrain prompts, tool schemas and visibility inside the loop. These services change quickly, so check current documentation for AgentCore components, regions and pricing before committing.

**Follow-ups they will ask:**
- Tool permissions: each tool runs with least privilege, such as an action group Lambda with its own role, not one identity for everything.
- Stopping runaway loops: step, token and wall clock budgets in the loop, plus an alarm on spend per session.
- How MCP fits: it standardizes tool discovery and calls, so the dispatcher or gateway speaks MCP and tools are reusable across agents.

**Mistakes to avoid:**
- Describing agents as magic; interviewers want the loop, the state store and the failure handling.
- Quoting AgentCore limits from memory; describe the shape and defer specifics to the documentation.

### Q. How do SageMaker endpoints work, and when would you use one for a custom model such as a reranker or a fine-tuned classifier?

**Short answer (45 seconds):** SageMaker AI hosts a model behind an HTTPS endpoint with IAM auth and autoscaling, in four serving modes. Real-time endpoints run always-on instances, CPU or GPU, for low latency. Serverless inference scales to zero for bursty CPU workloads and bills per request, with cold starts. Asynchronous inference queues requests with large payloads or long processing and writes results to S3. Batch transform runs offline over a dataset. For a reranker or a fine-tuned classifier inside a chat pipeline, a small real-time or serverless endpoint fits; for nightly scoring of millions of rows, batch transform.

**Deeper explanation:** You bring a model artifact in S3 plus a container: prebuilt PyTorch and Hugging Face containers, the Large Model Inference container wrapping vLLM or TensorRT-LLM, or your own image implementing the invocations and ping contract. Multi-model endpoints host many small models on one instance and load them on demand, which suits per-tenant fine-tunes. JumpStart deploys open models quickly, and managed training jobs matter when the task is a domain classifier.

```text
Real-time    : always-on, autoscale on InvocationsPerInstance, GPU allowed, lowest latency
Serverless   : scale to zero, CPU only, cold starts, pay per request
Asynchronous : internal queue, large payloads, results to S3, can scale to zero
Batch        : offline job over S3 input, no endpoint at all
```

SageMaker is for models Bedrock does not offer or that you trained yourself; against self-hosting on EKS it removes container orchestration but keeps instance-hour pricing plus a premium.

**Follow-ups they will ask:**
- Autoscaling a real-time endpoint: Application Auto Scaling on InvocationsPerInstance or a custom metric, with a minimum of two instances for availability.
- Blue-green for models: production variants with weighted traffic on one endpoint, or deployment guardrails with automatic rollback on alarms.
- Why not Lambda for a small model: fine for CPU models within package limits, but no GPU and the cold start includes model load.

**Mistakes to avoid:**
- Proposing serverless inference for a GPU model; it is CPU only.
- Forgetting that a real-time endpoint bills every hour it exists, including idle nights.

### Q. Should we self-host an open-weights model with vLLM on EKS or just use Bedrock? Walk me through the decision and what you would measure.

**Short answer (45 seconds):** It is a utilization and control question. Bedrock bills per token with no idle cost and no operations, so at low or spiky volume it wins. Self-hosting bills GPU hours whether busy or not, so it wins only when sustained volume keeps the GPUs busy, when you need a model or fine-tune Bedrock does not offer, or when data rules exclude a shared service. I would measure daily tokens, peak to average ratio and latency targets, then price a GPU fleet at that throughput against the per-token bill.

**Deeper explanation:** vLLM throughput depends on model size, quantization, context length and concurrency; continuous batching means throughput grows with concurrent requests until KV cache memory runs out. Load test at realistic prompt and completion lengths, record tokens per second and time to first token, then divide GPU cost per hour by sustained tokens per hour for cost per million tokens. Add engineering time for upgrades and on-call.

```text
Bedrock   : $/token, zero idle, per-region quotas, fixed catalog, no ops
Self-host : $/GPU-hour, idle cost, any model, you own serving
Break-even: (GPU $/hour) / (sustained tokens/hour) < Bedrock $/token, plus peak headroom
```

A common hybrid is Bedrock for frontier models and spiky traffic, self-hosting for a small constantly busy model such as an embedding model or reranker. Hardware: g6 (L4) for small models, g5 (A10G) or g6e (L40S) for 7B to 13B class in 16-bit, p4d or p5 for large models; quantization widens the options.

**Follow-ups they will ask:**
- Scaling to zero: GPU nodes and model loads take minutes, so scale-to-zero means a cold latency penalty; keep one replica or accept it.
- Spot for inference: viable for stateless replicas with graceful drain; keep the minimum capacity On-Demand.
- Why not SageMaker LMI instead of EKS: fewer moving parts, same vLLM underneath; EKS wins when you already run Kubernetes and want shared GPU pools.

**Mistakes to avoid:**
- Comparing list prices without measured throughput; cost per token depends on utilization.
- Underestimating operational load: driver versions, model rollouts and GPU capacity shortages are real work.

### Q. What can Bedrock Guardrails do, and how would you layer it with application-level checks for a customer-facing assistant?

**Short answer (45 seconds):** Guardrails is a configurable policy applied to prompts and completions: content filters with adjustable strength, denied topics described in natural language, word filters, sensitive information filters that block or mask PII, and contextual grounding checks that flag answers unsupported by the retrieved context. It attaches to Converse and InvokeModel calls by ID and runs standalone through ApplyGuardrail on text from any model. I treat it as one layer: the application still validates inputs, scopes tools and data to the authenticated user, and logs every block.

**Deeper explanation:** Layering from the outside in: WAF and rate limits; authentication and per-user quotas; input validation and an injection-aware system prompt; Guardrails on the model call for content and PII; tool-level authorization so the model can only call functions the user may use, with the user's identity passed explicitly; output checks for grounding, format and leakage before anything reaches the user or a downstream system. Retrieved text is treated as data, never as instructions, and high-risk actions sit behind confirmation.

```text
Request -> WAF/rate limit -> auth + quota -> input checks -> Guardrails(in) -> model + tools (scoped IAM)
        -> Guardrails(out: grounding, PII) -> schema validation -> response; blocked events -> logs + metrics
```

The assessment names which policy fired, which feeds a metric and a review queue. Tune strength against real traffic in shadow mode first, because over-strict filters frustrate users in domains such as healthcare where sensitive words are legitimate.

**Follow-ups they will ask:**
- Does it stop prompt injection: it reduces some attack classes with prompt attack filters, but tool scoping and treating retrieved content as untrusted are the real defenses.
- Cost and latency: a per-text-unit charge and added latency per call, so apply the strict profile to risky routes rather than everything.
- Alternatives: a small classifier model, vendor-specific safety settings, or open guard models hosted on SageMaker for custom categories.

**Mistakes to avoid:**
- Relying on the system prompt alone for safety.
- Letting the agent call tools with a shared service identity instead of the user's permissions.

### Q. You have worked on GCP. Map the services you used to AWS and Azure so we can talk architecture without translation problems.

**Short answer (45 seconds):** Every cloud has the same building blocks, so I translate names, not designs: Cloud Run to App Runner or Fargate, Cloud Run functions to Lambda, Pub/Sub to SNS plus SQS, Cloud SQL to RDS, Firestore to DynamoDB, Vertex AI to Bedrock plus SageMaker, Secret Manager to Secrets Manager.

**Deeper explanation:**

| Capability | AWS | GCP | Azure |
|---|---|---|---|
| Compute | EC2, ECS, EKS, Fargate | Compute Engine, GKE, Cloud Run | Virtual Machines, AKS, Container Apps |
| Functions | Lambda | Cloud Run functions | Azure Functions |
| Object storage | S3 | Cloud Storage | Blob Storage |
| Relational DB | RDS, Aurora | Cloud SQL, AlloyDB | Azure SQL, Database for PostgreSQL |
| NoSQL | DynamoDB | Firestore, Bigtable | Cosmos DB |
| Queue | SQS | Pub/Sub pull, Cloud Tasks | Service Bus |
| Pub/sub | SNS, EventBridge | Pub/Sub, Eventarc | Event Grid |
| Secrets | Secrets Manager | Secret Manager | Key Vault |
| Monitoring | CloudWatch, X-Ray | Cloud Monitoring, Trace | Azure Monitor |
| Managed LLM | Bedrock, SageMaker | Vertex AI | Azure AI Foundry |
| Vector search | OpenSearch, pgvector | Vertex AI Vector Search, AlloyDB | Azure AI Search |

Differences that matter: GCP IAM binds roles to principals on a resource hierarchy while AWS attaches policy documents to identities and resources; Pub/Sub is one product where AWS splits queueing, fan-out and streaming; Cloud Run's scale to zero has no exact AWS twin.

**Follow-ups they will ask:**
- What you would miss from GCP: Cloud Run and BigQuery; AWS answers with App Runner and Athena or Redshift.
- Cross-cloud identity: GCP workload identity federation accepts AWS roles and AWS accepts OIDC tokens; no long-lived keys.
- Which is better for LLM apps: the model catalog decides; keep the model layer swappable.

**Mistakes to avoid:**
- Mapping blindly; Firestore versus DynamoDB and Pub/Sub versus SQS differ semantically.
- Letting unfamiliar AWS names read as unfamiliar concepts; translate and move on.

### Practice
- Call a Bedrock model from a Node script using the Converse API with one tool definition and streaming; log token usage from the metadata event.
- Create a Knowledge Base over a folder of your own PDFs in S3 with Aurora PostgreSQL or OpenSearch Serverless as the store, then compare Retrieve results against your own pgvector pipeline on ten questions.
- Attach a Guardrail with a PII filter and one denied topic to the same call, send five prompts that should be blocked and five that should pass, and read the assessment output.
- Price a self-hosted 8B model on one g6 instance against Bedrock per-token pricing at your expected daily token volume and write down the break-even.
- Say it out loud: explain to a GCP-fluent colleague what Bedrock is in terms of Vertex AI, in 45 seconds.

## Architecture Scenarios

> Scenario questions are where everything above gets combined under time pressure. The interviewer wants a method, not a service list: clarify scale, latency, consistency, budget and team, start with the simplest multi-AZ shape, name every stateful component and how it fails, put numbers on RTO, RPO and cost, and say what changes at ten times the load. Talk while you draw, and end each design with the two things you would push back on.

### Concepts you must understand
- Clarify before drawing: users and requests per second, data size and growth, latency targets, consistency needs, compliance, budget, team size and skills; a design without these numbers is a guess.
- Default shape for a web product: CloudFront in front, ALB to ECS Fargate across two or three AZs in private subnets, a managed database with Multi-AZ, Redis for cache and ephemeral state, S3 for objects, SQS plus workers for anything slow.
- Every stateful component needs an answer for backup, failover, scaling and cost: the database, the cache, the queue, object storage, secrets and DNS.
- Security by default: private subnets, task and execution roles instead of keys, KMS encryption at rest, TLS everywhere, WAF at the edge, CloudTrail and GuardDuty on from day one.
- Observability is part of the design: structured logs, traces across async hops, symptom-based alarms and a cost view per service.
- Scaling story: stateless compute scales out behind the load balancer; the database is the bottleneck, so read replicas, caching, connection pooling and partitioning come in that order.
- State the trade-offs you made and the trigger for revisiting each one; interviewers reward honesty about limits more than a perfect diagram.

### Q. Design a scalable MERN application on AWS for a product expecting to grow from a few thousand to a few million users.

**Short answer (45 seconds):** The React build goes to S3 behind CloudFront with origin access control and WAF. The Express API runs as stateless ECS Fargate tasks across three AZs behind an ALB, with JWT auth and sessions in ElastiCache Redis, scaled on requests per target. MongoDB runs on Atlas in the same region over PrivateLink, with DocumentDB only if the feature set fits. Uploads go straight to S3 with presigned URLs, slow work goes through SQS to a worker service, secrets live in Secrets Manager, CloudWatch and X-Ray cover observability. Growth means more tasks, more caching in Redis and CloudFront, and bigger Atlas tiers before sharding.

**Deeper explanation:**

```text
Browser -> CloudFront (+WAF) -> S3 (React build)
                             -> ALB -> ECS Fargate api (3 AZs) -> Atlas via PrivateLink
                                                              -> ElastiCache Redis (sessions, cache, rate limits)
                                                              -> S3 presigned uploads -> SQS -> worker tasks
CI: GitHub Actions (OIDC role) -> ECR -> ECS deploy
```

Decisions worth saying out loud: the API is stateless, so no in-memory sessions and no local disk. Each task keeps a small Mongo pool, so task count times pool size must stay under the cluster's connection limit. Indexes and read preferences matter more than instance size. Rate limiting and idempotency keys live in Redis. Rolling deploys with a minimum healthy percentage and a sufficient deregistration delay avoid dropped requests. Cost control comes from autoscaling, Graviton tasks and CloudFront absorbing static traffic.

**Follow-ups they will ask:**
- What changes at ten times the load: more read caching, Atlas sharding by tenant, a separate worker cluster, and hot aggregations moved to a read model.
- WebSockets for live features: an ALB supports them, but sticky routing is not needed if state is in Redis and pub/sub fans out across tasks.
- Why not Lambda for the API: steady traffic and long-lived database connections favor containers; Lambda stays for bursty edges such as webhooks.

**Mistakes to avoid:**
- Putting the database in a public subnet or exposing Atlas on the internet with an IP allowlist instead of PrivateLink.
- Forgetting the connection math when autoscaling tasks.

### Q. Design a RAG platform on AWS: document ingestion, vector store, query path and evaluation, for a multi-tenant SaaS.

**Short answer (45 seconds):** Ingestion starts with a presigned upload to S3, which triggers Step Functions: extract text (Textract or a container with a PDF parser), chunk, embed with a Bedrock embedding model in a Map state with bounded concurrency, upsert into Aurora PostgreSQL with pgvector alongside tenant and document metadata, mark the document ready. The query path authenticates, runs hybrid retrieval filtered by tenant, reranks, calls the model through Bedrock with citations and streams the answer. Every query logs retrieved chunks and the answer so a nightly job scores recall and faithfulness against a golden set.

**Deeper explanation:**

```text
Upload -> S3 -> EventBridge -> Step Functions: extract -> chunk -> Map(embed, MaxConcurrency 10) -> upsert -> status
Query  -> API (Fargate) -> auth + tenant -> pgvector + tsvector hybrid (WHERE tenant_id = $1)
       -> rerank -> Converse (stream) -> Guardrails -> SSE to client
Eval   -> nightly job: golden questions -> recall@k, faithfulness, latency, cost -> dashboard
```

Design points: tenant_id on every chunk row with the filter inside the query, and partitioning or separate schemas for regulated tenants. Chunking strategy and embedding model are versioned so a re-embed is a controlled migration. Retrieval returns source URIs and offsets for citations. Per-tenant token budgets and a cache of frequent question embeddings control cost. Bedrock Knowledge Bases is the managed alternative for ingestion and retrieval; prototype with it, keep the custom path when parsing or permissions demand it.

**Follow-ups they will ask:**
- Why pgvector over OpenSearch here: embeddings live with tenant and document metadata, one engine, transactional updates; OpenSearch when the index outgrows Postgres.
- Handling document updates and deletes: version the document, re-embed changed chunks, delete stale rows in the same transaction, and never leave orphaned vectors.
- Keeping latency down: parallelize retrieval and rerank, stream the first token early, and cap retrieved chunks by token budget.

**Mistakes to avoid:**
- Filtering by tenant after retrieval, which leaks data across tenants and ruins recall.
- Shipping without an evaluation set; you cannot tune chunking or prompts by feel.

### Q. Design an event-driven order pipeline: order placed, payment, inventory, notification, with reliable delivery and replay.

**Short answer (45 seconds):** The order service writes the order and an outbox row in one Postgres transaction, and a relay publishes outbox rows to an EventBridge bus, so a crash can never lose an event or publish one for an uncommitted order. Rules route events into one SQS queue per consumer (payments, inventory, notifications), each with a dead-letter queue and an idempotency table keyed by event ID. Where steps depend on each other, a Step Functions saga coordinates them with compensating actions. The bus archive gives replay for rebuilding projections or recovering a consumer.

**Deeper explanation:**

```text
Order API -> Postgres (orders + outbox, one txn) -> relay -> EventBridge "orders" bus
   rule order.created -> SQS payments  -> consumer -> payment provider (idempotency key)
   rule order.created -> SQS inventory -> consumer -> reserve stock, emit inventory.reserved
   rule order.paid    -> SQS notify    -> consumer -> email/SMS
   rule order.*       -> archive (replay)        DLQs + alarms on every queue
```

Ordering matters for inventory, so that queue is FIFO with the order ID as message group; notifications stay standard. Every consumer records processed event IDs with a conditional write before side effects and passes the event ID downstream as an idempotency key. Schemas are versioned in the registry and consumers ignore unknown fields. Trace context travels in message attributes so one trace spans the flow. The saga owns timeouts: if payment does not confirm in time, a compensating event releases inventory.

**Follow-ups they will ask:**
- Why an outbox instead of publishing directly from the API: publishing after commit can fail and publishing before commit can lie; the outbox makes the write and the event atomic.
- Why EventBridge over SNS or Kafka: content routing, archive and replay, cross-account targets, no cluster; Kafka for long retention and stream processing.
- A consumer bug corrupted data: fix it, replay from the archive, and let idempotency plus versioned updates make the replay safe.

**Mistakes to avoid:**
- Chaining services with synchronous HTTP calls and calling it event-driven.
- One shared queue for all consumers, so a slow consumer starves the others.

### Q. Design a multi-region active-passive deployment with an RTO of 30 minutes and an RPO of one minute. What is hard about it?

**Short answer (45 seconds):** Primary in one region, pilot light in a second. Data replicates continuously: Aurora Global Database with managed failover, S3 Cross-Region Replication with replication time control, DynamoDB global tables for session and idempotency data, ECR and Secrets Manager replication. The same stacks deploy to both regions with the standby's ECS services at minimal capacity. Route 53 failover records with health checks plus Application Recovery Controller routing controls move traffic deliberately, and a runbook scales the standby up. The hard parts are everything that is not a database: in-flight queue messages, regional services such as user pools, DNS caching, and the discipline to test.

**Deeper explanation:**

```text
Primary (ap-south-1)                     Standby (me-central-1, pilot light)
ALB -> ECS api (desired 6)               ALB -> ECS api (desired 1)
Aurora writer  ==global DB replication==> Aurora secondary (promote on failover)
S3 bucket      ==CRR + RTC=============> S3 bucket
DynamoDB      ==global table==========> DynamoDB (multi-writer)
Route 53 failover (health check) + ARC routing control for the manual switch
```

RPO of one minute is met by Aurora Global Database's typical lag and by global tables; S3 RTC gives a predictable replication window. RTO of 30 minutes covers detection, decision, promotion, scaling the standby and DNS propagation at a short TTL. SQS queues are regional, so in-flight messages at failover are reprocessed from the outbox or accepted as loss within the RPO. KMS multi-region keys decrypt in both regions. Fail back is a second planned migration, not a flip of the same switch.

**Follow-ups they will ask:**
- Why not active-active: write conflicts and much higher cost; tested active-passive meets most RTO targets.
- What breaks silently: replication that stopped weeks ago, an expired certificate, a quota never raised in the standby; alarms and quarterly game days catch them.
- How users keep working after failover: tokens signed by a key available in both regions, sessions in a global table, clients that retry.

**Mistakes to avoid:**
- Promising RPO zero across regions; asynchronous replication always has lag.
- Building the standby once and never deploying to it again, so it drifts.

### Q. You inherit an AWS account that costs far more than the workload justifies. Walk me through how you cut the bill without breaking production.

**Short answer (45 seconds):** Measure first: Cost Explorer by service and usage type, tags or accounts for attribution, Compute Optimizer and Trusted Advisor for rightsizing. Then eliminate waste: unattached EBS volumes, old snapshots, idle load balancers and Elastic IPs, forgotten dev environments, logs with no retention. Then rightsize: RDS and EC2 by utilization, gp2 to gp3, Graviton where images allow, S3 lifecycle, NAT traffic onto endpoints. Then re-architect expensive patterns such as a cluster at 10 percent utilization. Only then commit to Savings Plans for the steady floor, with budgets and anomaly alerts so it stays down.

**Deeper explanation:**

```text
1. Measure   : Cost Explorer (service, usage type, tag), CUR in Athena, Compute Optimizer
2. Eliminate : orphaned EBS, snapshots, EIPs, idle ALBs, empty clusters, log retention
3. Rightsize : RDS/EC2 by p95 utilization, gp3, Graviton, Fargate task sizes, Lambda memory
4. Re-plan   : S3 lifecycle, NAT -> endpoints, dev environments on a schedule, Spot for workers
5. Commit    : Savings Plan sized to the post-cleanup floor
6. Keep      : budgets per service, anomaly detection, monthly review with owners
```

Order matters: a Savings Plan bought before rightsizing locks in waste for a year. Each change ships like a deploy, with a rollback and a metric to watch: downsizing RDS in a maintenance window with Performance Insights open, switching volumes to gp3 online, moving a service to Graviton behind a weighted target group. The cheapest fixes are often storage and networking: S3 Standard holding years of logs, CloudWatch Logs with infinite retention, NAT processing for S3 traffic.

**Follow-ups they will ask:**
- Avoiding breakage when rightsizing: p95 utilization over several weeks, headroom for peaks, one tier at a time with alarms watching.
- Reserved Instances already bought: check utilization and coverage reports, exchange Convertible RIs, or sell Standard RIs on the marketplace.
- Keeping engineers engaged: show each team its own spend monthly and celebrate reductions like features.

**Mistakes to avoid:**
- Starting with a Savings Plan because it is the easiest win on paper.
- Deleting resources without confirming ownership through tags, CloudTrail or asking.

### Q. Plan the migration of a Node.js monolith on a few EC2 instances to containers on AWS with minimal downtime.

**Short answer (45 seconds):** First make the monolith container-ready without changing features: a Dockerfile, configuration through environment variables, logs to stdout, a health endpoint, graceful shutdown on SIGTERM, and state moved out of the process and local disk into Redis and S3. Then run it on ECS Fargate behind the existing ALB as a second target group, shift traffic gradually with weighted routing while comparing error rates and latency, and cut over when it holds. Cron jobs move to EventBridge Scheduler running tasks, and the database stays put with pooling adjusted for more, smaller instances. Only when the lift is stable do I carve services out behind ALB path rules.

**Deeper explanation:**

```text
Phase 0: containerize as-is, CI builds to ECR, run in staging
Phase 1: ECS Fargate service -> new target group on the same ALB, weight 5% -> 25% -> 50% -> 100%
Phase 2: retire EC2, cron to EventBridge Scheduler + RunTask, sessions to Redis, uploads to S3
Phase 3: strangler fig: /api/payments -> new service target group, monolith keeps the rest
```

Pitfalls to name: in-memory caches and sessions that assume one process, writes to local disk, requests longer than the ALB idle timeout, scheduled jobs that would now run on every task, hardcoded config, and database connections multiplying with tasks, which RDS Proxy or PgBouncer solves. Blue-green through CodeDeploy with automatic rollback replaces hand-run deploys. Structured logs and traces are easiest to add while you are already touching startup code.

**Follow-ups they will ask:**
- Why ECS Fargate rather than EKS for this: a small team migrating one application does not need Kubernetes; the container image moves to EKS later if needed.
- Database on the instance itself: AWS DMS or dump and restore into RDS, cut over during the same traffic shift.
- Rollback plan: keep the EC2 target group healthy at zero weight until the new service has survived a full business cycle.

**Mistakes to avoid:**
- Rewriting the application while migrating it; one change at a time.
- Splitting into microservices before the monolith even runs cleanly in a container.

### Q. Secure a public REST API that fronts an LLM-powered product. Walk me through the layers from the edge to the data.

**Short answer (45 seconds):** At the edge, CloudFront with WAF managed rules, rate limits and body size limits, with Shield Standard absorbing network floods. The API sits on API Gateway or an ALB with TLS from ACM, authenticating users with JWTs and partners with API keys and usage plans, and authorizing every request in the application against tenant and scopes. Compute runs in private subnets with task roles and no keys, secrets rotate in Secrets Manager, and data is encrypted with KMS behind security group references. For the LLM path, retrieved content is untrusted, Guardrails screen input and output, tools run with the user's permissions, and per-user token budgets stop abuse.

**Deeper explanation:**

```text
CloudFront + WAF (managed rules, rate limits, size limits) -> API Gateway (JWT authorizer, throttling, usage plans)
-> ECS Fargate (private subnets, task role) -> Bedrock (IAM, PrivateLink) | RDS (SG from api, KMS) | Secrets Manager
Account: CloudTrail, GuardDuty, Security Hub, Inspector (image scanning), Config rules
```

Application controls are where most real risk lives: schema validation on every input, tenant checks on every query, idempotency keys on mutations, and audit logs of who asked what. For the model, a system prompt that states tool and data boundaries, step and token budgets per request, and a kill switch that disables tools or the feature with one flag. Supply chain: pinned dependencies scanned in CI, minimal base images, image signing. Incident readiness: a key leakage runbook, session revocation, alarms on authentication failures and WAF blocks.

**Follow-ups they will ask:**
- API keys versus JWTs: keys identify an application for quotas and billing, JWTs identify a user with claims; most products need both.
- Preventing exfiltration through the model: scope retrieval by tenant before the model sees anything, never let it build raw queries, log retrieved sources.
- Zero trust between services: IAM auth or mTLS internally, no implicit trust from being inside the VPC.

**Mistakes to avoid:**
- Stopping at WAF and TLS; most breaches are authorization bugs and leaked credentials.
- Giving the model's tools a powerful shared role instead of the calling user's permissions.

### Practice
- Whiteboard each scenario in ten minutes with AZ boundaries drawn, then list the three failure modes an interviewer would ask about and your answer to each.
- Write a one-page design for the RAG platform with a cost estimate at one thousand and one hundred thousand documents, naming every assumption.
- Build the order pipeline skeleton with EventBridge, two SQS queues and idempotent consumers; replay a day of events from the archive and prove nothing double-processed.
- Say it out loud: present the MERN design in three minutes and finish with what you would change at ten times the load.
