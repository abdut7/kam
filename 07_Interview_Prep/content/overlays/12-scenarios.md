## SOLID Principles

### Why it exists
Code that changes every sprint tends to collect into a few huge classes where one edit breaks unrelated features and every test needs a database, a mail server and an LLM key. SOLID is a set of five habits, collected by Robert C. Martin, that keep units small, replaceable and testable: each unit gets one reason to change, and business code depends on contracts instead of concrete vendors. Before teams worked this way, adding a payment provider or a discount rule meant editing tested code in many places and hoping nothing else moved. The cost is more files, interfaces and indirection, which pays off only where change actually happens; applied to stable code it is ceremony.

## Design Principles Beyond SOLID

### Why it exists
Most daily design decisions are small: copy this code or share it, build the option now or later, inherit or compose, ask an object for its data or tell it what to do. Principles such as DRY, KISS, YAGNI, composition over inheritance, low coupling with high cohesion and the Law of Demeter give those choices names, so a team can discuss them instead of arguing taste. Without them, codebases drift into business rules copied in five places that disagree, speculative frameworks nobody uses, and deep inheritance chains where a change to the parent breaks every child. The trade-off is that these principles pull against each other, DRY against KISS for example, so they are judgment tools rather than rules a linter can enforce.

## Creational Design Patterns

### Why it exists
Creating an object correctly is often harder than using it: a database pool, an LLM client or a payment gateway needs configuration, secrets, timeouts and sometimes a single shared instance per process. When `new` calls with long argument lists are scattered through business code, every caller is tied to a concrete class, setup is copy-pasted, and tests cannot swap in a fake. Creational patterns (factory, builder, singleton, object pool) and dependency injection move construction to one place, so the rest of the code just receives what it needs. The cost is indirection, and in JavaScript and Python a plain function, a module or an object literal often does the job without a class.

## Structural Design Patterns

### Why it exists
Real systems are assembled from parts that were never designed to fit together: third-party SDKs with their own types and errors, legacy modules, and cross-cutting needs like caching, retries and logging that apply to many classes. Without a deliberate wrapper, vendor types leak into business code, switching a provider touches hundreds of lines, and the same retry or cache code is pasted into every method. Adapter, Facade, Decorator, Proxy and their relatives each describe one kind of wrapper with one job: translate an interface, simplify a subsystem, add behavior or control access. The trade-off is extra layers and deeper stack traces, and a wrapper that only passes calls through adds cost without hiding anything.

## Behavioral Design Patterns

### Why it exists
Behavioral patterns deal with how objects share work and react to each other: choosing among algorithms, moving a document through statuses, notifying other parts when something happens, or running a request through a series of checks. Without them, logic grows as switch statements that get a new case every release, status fields that any code can set to an illegal value, and modules that call each other directly for every side effect. Strategy, State, Observer, Command and Chain of Responsibility give these recurring shapes names and a tested structure, so the next variant is an addition instead of an edit. The cost is control flow that is harder to follow, especially with observers and events, where no single file shows what runs next.

## Backend and Enterprise Patterns

### Why it exists
Business applications mix three concerns that change for different reasons: the HTTP or message transport, the business rules and the database. When a single handler parses the request, applies rules and writes SQL, the rules get copied into queue workers and agent tools, transactions end half-done, and ORM entities with internal fields leak straight into API responses. Repository, unit of work, service layer, DTOs, dependency injection and domain-driven design, many of them catalogued in Martin Fowler's "Patterns of Enterprise Application Architecture", give each concern its own place and its own tests. The cost is mapping code and extra layers, which become pure overhead on simple CRUD or when wrapped generically around an ORM that already does the job.

## Architectural Patterns

### Why it exists
An architectural pattern decides the shape of the whole codebase: which parts may depend on which, where business rules live, and how the system can split as traffic and teams grow. Without one, projects become a "big ball of mud" where a framework upgrade or a database change rewrites business logic and every team edits the same files; the opposite mistake is splitting into microservices too early and paying for network failures and distributed debugging. Layered, clean, hexagonal, modular monolith and event-driven architectures each fix a dependency direction and a unit of separation. Their cost is boilerplate and rules that only hold if tooling enforces them, and event-driven designs add eventual consistency and harder tracing.

## Sample Folder Structures

### Why it exists
The folder tree is the first architecture document anyone reads: a new teammate, a reviewer or an interviewer uses it to guess what the system does and where a new feature should go. Without an agreed structure, each developer invents a location, a `utils` folder becomes a junk drawer, imports run in every direction and one feature change touches ten folders. A clear layout, by feature first and layer second, with one public entry per module, makes ownership and allowed dependencies visible. The trade-off is that a structure built for a large team feels heavy on a small service, and any convention only helps when it is applied consistently and checked by tooling.

## Design Project Scenarios [Scenarios]

> Interviewers run these as open conversations: they describe a codebase or product situation, then keep adding constraints (a deadline, a new provider, a bigger team, a demanding customer) to see whether your design bends or breaks. A weak answer jumps to a pattern name or proposes a rewrite. A senior answer asks what changes and how often, picks the smallest structure that absorbs that change, plans an incremental path protected by tests, says what it will deliberately not build, and names the measurements that show the design is working.

### Concepts you must understand
- Start by asking what changes, who changes it and how often; the design should make that change cheap and leave everything else simple.
- Separate one-way doors (data model, tenancy, ID format, money representation, public API contracts) from two-way doors (queue library, folder names), and spend design time on the first group.
- Turn vague scale words into numbers: users, peak requests per second, rows per table, and how many variants (providers, customers, rules) are expected within a year.
- Prefer incremental paths over rewrites: characterization tests, sprouting new code beside old code, adapters that wrap existing code, and flags for rollout.
- Put a seam (port, strategy, registry) only on an axis of change you can name, and back every seam with a contract test suite that each implementation must pass.
- Say what you will not build and why; restraint is a senior signal, not a gap.
- Name the measurements that prove the design works: lead time for the next change, defects in touched code, p95 latency, boundary violations in CI.

### Q. You inherit a 3,000-line `OrderService` and must ship a partial-refund flow in two weeks. How do you change it safely without a rewrite?
**Short answer (45 seconds):** No rewrite and no refactor of the whole file. I find the methods the refund flow touches, pin their current behavior with characterization tests, then build the refund as a new use case class beside the god service and have the old service delegate to it. Every later feature extracts one more use case, so the file shrinks through real work instead of a risky big-bang project.

**Deeper explanation:** I clarify whether the deadline allows any refactoring, who else edits the file, what tests exist and which parts break most; git history answers the last:

```bash
git log --since="6 months ago" --format= --name-only -- src/orders | sort | uniq -c | sort -rn | head
```

The plan, in order:

1. Characterization tests: call the existing public methods with recorded real inputs against a test Postgres and snapshot outputs and side effects (rows, events, queued emails). They pin today's behavior, bugs included.
2. Seams: the refund needs payments and inventory, so those calls go behind small ports the new code can fake, without touching other callers.
3. Sprout a class: `RefundOrderUseCase` holds the new rules (refundable amount, partial quantities, approval above a threshold). `OrderService.refund()` keeps its signature and delegates, so controllers and workers do not change.
4. Hidden coupling: I check which shared `this.` fields the refund path reads before moving it; the use case owns the transaction.

```ts
// order.service.ts: public API unchanged, logic lives in the use case
refund(orderId: string, lines: RefundLine[], actor: Actor) {
  return this.refundOrder.execute({ orderId, lines, actor });
}
```

What I measure: lines and injected dependencies of `OrderService` per sprint, defects in touched paths, PR size and merge conflicts on the file.

**Follow-ups they will ask:**
- The product owner wants zero refactoring?: The sprout is the cheapest safe way to add the feature, and the tests are what let us hit the date.
- When would you approve a rewrite?: When the domain itself changed and old and new can run side by side with outputs compared before the switch.

**Mistakes to avoid:**
- Splitting by layer (`OrderValidator`, `OrderHelper`) instead of by use case, which spreads one change across more files.
- Skipping tests because the deadline is tight, which is exactly when regressions cost most.

### Q. Checkout supports Razorpay and Stripe through if-else branches in five files, and the business wants a UAE gateway next quarter with more to follow. How do you add the third provider without touching existing code?
**Short answer (45 seconds):** I pay down the existing branches once: a provider-neutral `PaymentGateway` port owned by checkout, Razorpay and Stripe moved into adapters behind it, and a registry that picks the adapter from config such as merchant region and currency. After that, a new gateway is an adapter, a webhook mapper, a registry entry and a passing contract suite, with no edits to checkout. The same shape works for a third LLM provider.

**Deeper explanation:** I clarify currencies (AED and INR both use two-decimal minor units), partial refunds, 3-D Secure redirects, webhooks or polling, and whether routing is per merchant or per payment.

```ts
interface PaymentGateway {
  readonly id: 'stripe' | 'razorpay' | 'uae-gateway';
  readonly capabilities: { partialRefund: boolean; currencies: string[] };
  createPayment(req: { orderId: string; amountMinor: number; currency: string; idempotencyKey: string }): Promise<PaymentRef>;
  refund(ref: PaymentRef, amountMinor: number, idempotencyKey: string): Promise<void>;
  parseWebhook(rawBody: Buffer, headers: Record<string, string>): PaymentEvent; // verifies the signature
}
```

Decisions and trade-offs:
- Checkout owns a payment state machine (`pending`, `authorized`, `captured`, `failed`, `refunded`); adapters map vendor statuses into it, keeping odd vendor states inside the adapter.
- Webhooks arrive at `/webhooks/:provider`; signature checks need the raw body, so that route skips the JSON parser.
- Errors are normalized (`CardDeclined`, `ProviderUnavailable`), so retries and user messages never depend on vendor codes.
- Capabilities are explicit, so a gateway without partial refunds is never offered one, and nobody writes `instanceof` checks.
- A shared port tends toward the lowest common denominator; vendor extras go through an optional `providerOptions` field read only by adapters.

Every adapter runs the same contract suite against its sandbox, and a flag enables the new gateway for a few UAE merchants first. I measure authorization success rate, webhook delay and reconciliation mismatches per provider.

**Follow-ups they will ask:**
- One provider needs a redirect step?: `createPayment` returns either `completed` or `actionRequired` with a URL, and the client handles both for every provider.
- Migrating the existing branches?: Wrap today's code in two adapters unchanged, then delete branches one call site at a time.

**Mistakes to avoid:**
- Letting vendor types such as `Stripe.PaymentIntent` appear in checkout code.
- Storing only the vendor's status string instead of a domain status plus `provider` and `providerRef` columns.

### Q. You have a 48-hour take-home: a small API with one LLM feature. How do you structure it so a reviewer sees clean architecture in the first five minutes?
**Short answer (45 seconds):** Reviewers open the README, the folder tree, one use case and the tests, in that order, so I optimize those four: one command to run, a feature-organized tree with a framework-free domain, one flow done end to end, and fast tests that need no API key because the LLM sits behind a port with a fake. I write down trade-offs instead of building everything.

**Deeper explanation:** I clarify what is evaluated (code quality, product sense, AI quality), the expected stack, whether deployment counts and the real time box. Then:

```text
README.md            one-command run, decisions, trade-offs, what I would do next
docker-compose.yml   api + postgres; `docker compose up` works on a clean machine
.env.example         every variable, no secrets
src/
  modules/requests/
    domain/          entities and rules, plain TypeScript, unit tested
    application/     use cases: create-request.ts, approve-request.ts
    infra/           Postgres repository, LLM adapter, HTTP routes
  shared/            zod-validated config, logger, error types
tests/               integration tests against the compose Postgres
```

Decisions that show judgment in a short time:
- Business rules stay deterministic in the domain; the LLM only drafts or classifies, its output is validated against a zod or Pydantic schema, and a fallback path handles parse failures.
- One modular monolith, no Kafka, no microservices; the README says what would change at scale.
- Errors return one consistent JSON shape with correct status codes, and inputs are validated at the edge.
- `npm test` runs in seconds with the fake model; a separate script tries a few cases on the real one.

The README carries a short decisions table (choice, alternative, why). A missing feature listed with a plan is forgivable; a repo that does not start rarely is, so before submitting I clone into a fresh folder and follow the README exactly.

**Follow-ups they will ask:**
- They ask you to extend it live in the next round?: The feature folder and ports make the extension one new use case; rehearse one before the call.
- Would you add a frontend?: A thin one if the brief asks, after the core flow is solid.

**Mistakes to avoid:**
- Committing `.env` or an API key anywhere in git history.
- Five layers of abstraction for two endpoints, which reads as cargo cult rather than seniority.

### Q. A seed-stage startup with three engineers asks you to choose the architecture for its MVP, and investors expect ten times the users within a year. What do you pick?
**Short answer (45 seconds):** I turn "ten times" into numbers first, because ten times a small base is usually still small. Then I pick a modular monolith on managed Postgres with stateless app servers, a background queue from day one and module boundaries that allow a later split. Design effort goes only to decisions that are expensive to reverse: data model, tenancy, IDs, auth and idempotency.

**Deeper explanation:** A back-of-envelope with the founders' forecast, say 2,000 daily users growing to 20,000, each making about 100 API calls a day:

```text
20,000 users x 100 calls  = 2,000,000 calls per day
2,000,000 / 86,400 s      = about 23 requests/s on average
assumed peak of 5x        = about 115 requests/s
```

A few Node or FastAPI instances and one well-indexed Postgres handle that. What breaks first is usually missing indexes, slow work (LLM calls, PDF parsing, email) in the request path, and three engineers colliding in one tangled codebase.

| Decide carefully now | Defer until measured |
| --- | --- |
| `tenant_id` on every row, auth model | Microservices |
| ID format, money as integer minor units | Kafka, a separate search cluster |
| Idempotency keys on payments and webhooks | Read replicas, sharding |
| Stateless servers: sessions in Redis or tokens, files in S3 | Caches beyond the obvious |
| Migration tool, request IDs, tracing | Multi-region |

Modules (identity, orders, billing) are folders with public entry points and a no-deep-import lint rule, so one can become a service later; long jobs go through BullMQ or Celery.

What I measure from week one: p95 latency, slow queries (`log_min_duration_statement`), database CPU and connections, queue lag and cost per active user; those numbers, not the calendar, trigger the next step.

**Follow-ups they will ask:**
- What would make you start with services?: Hard isolation needs (compliance, a separately scaled GPU workload) or separate teams from day one.
- And if growth is a hundred times?: The hottest module splits first along the same boundaries; the database usually needs work before the app tier.

**Mistakes to avoid:**
- Kubernetes and microservices "to be ready", which slows a three-person team on every change.
- Using YAGNI to skip tenancy and idempotency, two of the most painful retrofits.

### Q. In your modular monolith, three modules each define their own `Money`, `TenantId` and error types, and a developer proposes a `shared/` package of common entities. How do you introduce a shared kernel without recreating a big ball of mud?
**Short answer (45 seconds):** I agree to a shared kernel but keep it tiny and boring: value objects and contracts that mean exactly the same thing everywhere, such as `Money`, typed IDs, the event envelope, base errors and a clock. Entities like User or Order stay in their owning module, because "customer" means different things to billing and support. The kernel gets strict ownership, no dependencies on any module, and a change process every module owner signs off.

**Deeper explanation:** The test for each candidate: would every module always want the same change to it? `Money` (minor units, currency, rounding and allocation rules) passes. A `User` entity fails: identity cares about credentials and billing about payment profiles, and sharing it makes the database schema the real API.

```text
src/shared-kernel/        imports nothing from src/modules
  money.ts                Money value object, allocation and rounding
  ids.ts                  branded types: TenantId, UserId, OrderId
  errors.ts               DomainError, NotFound, Conflict
  events.ts               EventEnvelope { id, type, version, occurredAt, tenantId, data }
  clock.ts                Clock port for testable time
```

Guardrails:
- A dependency-cruiser rule (import-linter in Python) forbids the kernel from importing any module and keeps business services out of it.
- CODEOWNERS lists every module owner on `src/shared-kernel/`, so a change needs agreement.
- Changes are additive; a breaking change means a new type beside the old one and one migration per module.
- Tempting extras like `formatDate` go in a plain `lib/` with no business words, or stay duplicated.

Migration: pick the best existing `Money`, add property tests for rounding and allocation, then move one module per PR, deleting its local copy.

What I measure: kernel size and churn (it should change rarely), how many modules import it, and boundary violations in CI over time.

**Follow-ups they will ask:**
- Two modules disagree on rounding?: Then it is not shared knowledge yet; the kernel offers the primitive and each module keeps its policy.
- Where do generated API types go?: In the contract package of the module that publishes the API, not the kernel.

**Mistakes to avoid:**
- A `common/` folder that grows entities, helpers and services until every module depends on everything.
- Sharing ORM models across modules, which couples every module to every migration.

### Q. Enterprise customers each want their own pricing: contract rates, volume tiers, regional taxes, and one wants a custom formula. How do you design plugin points without forking the pricing code per customer?
**Short answer (45 seconds):** Pricing becomes a fixed pipeline of named stages (base price, contract, volume, promotion, tax, rounding), and each stage is an extension point. Most customer rules become data: versioned rule sets with effective dates, evaluated by a small engine. Only rules data cannot express become code plugins per tenant, with the same pure-function contract and tests. Every quote records which rule versions produced it.

**Deeper explanation:** I clarify who authors rules, how often they change, whether old quotes must be reproducible for disputes, the latency budget, and whether customers may upload logic.

```ts
type Stage = 'contract' | 'volume' | 'promotion' | 'tax';
type Adjustment = { stage: Stage; lineId?: string; amountMinor: number; reason: string; ruleId: string };

interface PricingStep {
  stage: Stage;
  applies(ctx: PricingContext): boolean;
  adjust(ctx: PricingContext, running: Totals): Adjustment[]; // pure, no I/O
}
```

Decisions:
- Stage order is core policy; plugins add steps inside a stage, so none can apply tax before discounts.
- Steps are pure (the engine loads data up front), so pricing is deterministic and fast to test.
- Each adjustment carries a reason and rule ID, giving support an explainable breakdown.
- Rule sets have an `effective_from` date and a version stored on each quote, so re-pricing an old quote gives the same answer.
- Data rules cover tiers and contract rates, using an existing condition format such as JsonLogic rather than a home-grown DSL.
- Customer-written code is a last resort, run in an isolate such as `isolated-vm` with time and memory limits, never `eval`.

A golden file of quotes per tenant runs in CI, so a core change that alters any price fails before release.

What I measure: time to onboard a new customer rule, p95 pricing latency and tenant-specific `if` statements in core (target zero).

**Follow-ups they will ask:**
- Two rules conflict?: An explicit per-stage policy (best single promotion or stack all), chosen per tenant and tested.
- Sales wants to preview a change?: A simulation endpoint re-prices recent quotes with the draft rule set and shows the difference.

**Mistakes to avoid:**
- `if (tenantId === 'acme')` inside the pricing service, which turns each customer into a hidden fork.
- Plugins that call the database or other services mid-calculation, making prices slow and non-reproducible.

### Practice
- Take the largest service file in a repository you know, run the git hotspot command on it, write characterization tests, and sprout one use case out of it behind the same public method.
- Build a `PaymentGateway` or `ChatModel` port with two adapters and one contract suite run through Jest `describe.each` or a parametrized pytest fixture; add a third adapter and confirm the only existing file that changed is the registry.
- Clone your own take-home or side project into a fresh folder, follow only the README, and time how long it takes to get it running and tested.
- Implement the pricing pipeline with two stages and a golden-file test for two tenants; change the rounding rule and watch the golden test catch it.
- Say it out loud: "Ten times growth for a three-person startup: give the numbers, three decisions you make now and three you defer, in 90 seconds."

## Design Failures & Code Review Cases [Scenarios]

> These start from a smell found in review, a bug report or a production symptom that traces back to a design decision. Answer them like an incident: clarify impact (who is affected, is data exposed, is it getting worse), contain (flag off, rollback, hotfix), diagnose with evidence (query logs, import graphs, git history, deploy times), fix the design cause rather than the single instance, and prevent a repeat with a guardrail that fails the build. Interviewers listen hardest for the guardrail, because the same mistake will be made again by someone else.

### Concepts you must understand
- Treat a design bug that exposes data or loses records as an incident: contain it and measure the exposure before you refactor anything.
- Fix the class of bug, not the instance: when one singleton held request state, search for the pattern everywhere and add a check so it cannot return.
- Get evidence from tools and history: query logs, import graphs, `git log -S` to see when a flag or field appeared, and deploy times lined up against failure times.
- Prefer guardrails that fail CI (dependency rules, contract tests, schema tests, query-count assertions) over review comments, which do not scale to the next developer.
- In code review, separate must-fix items (security, data loss, duplicated business rules) from follow-up tickets, and justify each with the failure it prevents.

| Symptom or error | First check | Likely causes | Fix |
| --- | --- | --- | --- |
| One user sees another user's data, only under load | Fields written on shared providers or module variables in the request path; cache keys | Request state on a singleton, cache key without user or tenant, CDN caching authenticated JSON | Pass context as parameters or AsyncLocalStorage; scoped cache keys; `Cache-Control: private, no-store` |
| `Nest can't resolve dependencies of the OrdersService (?)` | Is the provider listed and exported; does the parameter's file import back | Circular file import, provider missing from the module's `exports` | Break the cycle or export the provider; `forwardRef()` only as a stopgap |
| `ImportError: cannot import name 'X' from partially initialized module 'y' (most likely due to a circular import)` | Import chain in the traceback; `lint-imports` | Two Python modules import each other at top level | Move shared code to a third module; fix the dependency direction |
| `TypeError: Class extends value undefined is not a constructor or null` or `ReferenceError: Cannot access 'X' before initialization` | `npx madge --circular --extensions ts src` | CommonJS or ESM cycle, often through a barrel `index.ts` | Import files directly; break the cycle |
| Query log shows one `SELECT` per row of a list | ORM query logging; `calls` in `pg_stat_statements` | Lazy relations read in controllers or serializers, queries in a loop | Eager load in the repository (`selectinload`, `include`); return DTOs |
| `MissingGreenlet: greenlet_spawn has not been called` in async SQLAlchemy | Which attribute access triggered it | Lazy load outside an awaited query, often during serialization | `selectinload`; build the DTO inside the session |
| `DetachedInstanceError` when reading a relation | Where the entity crosses the session boundary | Entity returned past its unit of work, then lazy-loaded | Load what you need before the session closes; map to a DTO |
| Internal fields such as `passwordHash` in an API response | Does the handler return an entity | Denylist serialization, no response DTO, Prisma query without `select` | Allowlist DTO and mapper; schema test on the OpenAPI document |
| A refactor with no behavior change breaks many tests | Count of `jest.mock` calls and call assertions on internals | Tests coupled to implementation, mocking what you do not own | Test through public APIs, fakes for owned ports, real database for adapters |
| Orders without invoices, nothing in error logs | Reconciliation query against deploy times | Dual write, in-process emitter, ack before processing, unroutable messages | Outbox, idempotent consumer, ack after commit, dead-letter queue |
| A new subtype fails only for some tenants; `instanceof` checks appear | Run the contract suite against the new subtype | Subtype cannot keep the base contract (a Liskov break) | Capability interfaces, composition, shared contract tests |
| One function full of flag checks; a stale flag caused a wrong result | Flag reads per function, flag age in git | Flags checked deep in logic, no owner or expiry | Resolve flags at the edge into a strategy; expiry dates and deletion |
| The same rule gives different totals from the API and a worker | `grep` for the rule's constant or name | Business logic in controllers, copied into workers and tools | One use case that every entry point calls |
| Every new feature edits a "generic" base class and adds an option | Number of options and flags on the abstraction | Abstraction extracted from too few cases, along the wrong axis | Inline into callers, re-extract only what is truly shared |

### Q. Support reports that a user saw another customer's name and order history on their dashboard, only during peak traffic. What do you suspect and how do you fix it?
**Short answer (45 seconds):** This is a data exposure incident first: confirm from logs which responses carried another user's data, contain it by disabling the cache path or endpoint and purging caches, and bring in security. "Only under load" points at shared mutable state: request data stored on a singleton or module variable, or a cache key missing the user or tenant. The fix passes request context explicitly or through AsyncLocalStorage, plus a guard so it cannot come back.

**Deeper explanation:** Diagnosis in order:

1. Reproduce with concurrency: two test users hitting the endpoint through k6 or autocannon, asserting each response's user ID matches the token. If sequential requests are always correct, it is a concurrency bug.
2. Search for request state written onto shared objects:

```bash
grep -rnE "this\.(current|user|tenant|ctx)[A-Za-z]* *=" src --include=*.ts
grep -rnE "^(let|var) " src --include=*.ts
```

3. Check cache keys (`dashboard:${orderId}` without `userId` or `tenantId`) and response headers: authenticated JSON without `Cache-Control: private, no-store` can be stored by a CDN.

Causes ranked: a NestJS default-scope provider holding `this.currentUser`, where one instance serves every request and an `await` lets another request overwrite the field; an in-process or Redis cache key not scoped to the user; CDN caching; in Python, a class attribute or mutable default argument shared across calls.

```ts
import { AsyncLocalStorage } from 'node:async_hooks';
export const requestContext = new AsyncLocalStorage<{ userId: string; tenantId: string }>();
app.use((req, _res, next) =>
  requestContext.run({ userId: req.user.id, tenantId: req.user.tenantId }, next));
```

Better still, pass an `actor` parameter into use cases; AsyncLocalStorage (`nestjs-cls` in Nest, `contextvars` in Python) suits logging and tenant scoping. Prevent: a two-user concurrency test in CI for sensitive endpoints, one cache-key builder that requires tenant and user, and a staging check that compares the subject in each payload with the token's subject.

**Follow-ups they will ask:**
- Why not `Scope.REQUEST`?: It works, but the scope bubbles up to every consumer and builds instances per request; explicit parameters are cheaper and clearer.
- Do you notify users?: Security and legal decide; you supply the exact window and affected records from logs.

**Mistakes to avoid:**
- Fixing the one provider without searching for the same pattern elsewhere.
- Calling it a frontend bug because the data "showed up in the UI".

### Q. A refactor that changed no behavior broke dozens of unit tests, while a wrong `WHERE` clause shipped with every test green, and the suite takes 20 minutes. What is wrong with the tests and how do you fix them?
**Short answer (45 seconds):** The tests mock almost everything, so they verify how code calls its collaborators, not what it does: they break when internals move and miss bugs in whatever was mocked, like the SQL. I rebalance: pure unit tests for domain rules with no mocks, use-case tests with in-memory fakes for ports we own, adapter tests against real Postgres in a container, and a thin end-to-end layer. Speed comes from shared containers and skipping type checks in test runs.

**Deeper explanation:** Measure before changing anything:

```bash
grep -rc "jest.mock(" src | sort -t: -k2 -rn | head    # most-mocked test files
npx jest --json --outputFile=jest-report.json          # per-file durations
pytest --durations=20                                  # slowest Python tests
```

Causes ranked: mocking what you do not own (the ORM, the OpenAI SDK), so mocks drift from reality; asserting call sequences on internal collaborators instead of results; a full Nest `Test.createTestingModule` with dozens of providers built per test; ts-jest type-checking every file; integration tests that each start their own database.

```ts
// before: breaks on any internal change and never runs the SQL
expect(repo.findOverdue).toHaveBeenCalledWith(tenantId, now);
// after: behavior through the public API; the query is tested in the adapter suite
const sent = await sendOverdueReminders.execute({ tenantId, now });
expect(sent.map((r) => r.invoiceId)).toEqual(['inv_2']);
```

The fix:
- Fakes over mocks for owned ports (`InMemoryInvoiceRepository`), with one contract suite run against both the fake and the Postgres adapter so the fake stays honest.
- Adapter tests on Testcontainers, one container per worker, each test inside a rolled-back transaction or a truncated schema.
- `@swc/jest` or a transpile-only setup in tests, with `tsc --noEmit` once in CI.
- Mocks only at true boundaries: payment sandbox, LLM API, email.

What I measure: suite time, flaky-test count, and mutation score on the domain with Stryker (JavaScript) or mutmut (Python), which shows whether tests catch bugs.

**Follow-ups they will ask:**
- Isn't a real database slow?: One container per worker plus per-test transactions is fast enough for the adapter layer, which is a small share of the suite.
- What about LLM calls?: A fake model in unit tests and a separate eval suite against the real model.

**Mistakes to avoid:**
- Deleting the slow tests to hit a time target.
- Raising coverage targets, which rewards more mock-heavy tests.

### Q. A list endpoint slowed down as data grew, and the query log shows one `SELECT` for the orders followed by one per order for its items. The repository "just returns entities". Where is the design leak and how do you fix it?
**Short answer (45 seconds):** The repository returns ORM entities with lazy relations, and the controller or serializer touches `order.items` for each row, so the queries fire outside the repository where nobody sees them. That is an N+1 caused by a leaky abstraction. I fix the query by loading the relation inside the repository in one extra query or a join, and fix the design by returning DTOs or read models and making lazy loads fail loudly.

**Deeper explanation:** Confirm the shape first:

```sql
SELECT calls, mean_exec_time, query
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;  -- the items query shows far more calls than the orders query
```

Or turn on ORM logging (`echo=True` on a SQLAlchemy engine, `logging: ['query']` in TypeORM, `log: ['query']` in Prisma) and count queries for one request.

Causes ranked: lazy relations read during serialization (FastAPI `response_model` touching `order.items`, class-transformer walking TypeORM lazy relations); a loop calling `repo.findItems(order.id)` in the controller; GraphQL field resolvers without DataLoader.

```python
stmt = (
    select(Order)
    .where(Order.tenant_id == tenant_id)
    .options(selectinload(Order.items))  # 2 queries in total, not 1 + N
    .order_by(Order.created_at.desc())
    .limit(50)
)
orders = (await session.scalars(stmt)).all()
return [OrderSummary.model_validate(o) for o in orders]  # DTOs built inside the session
```

Make lazy loading explicit: `lazy="raise"` on relationships or `.options(raiseload("*"))`, so a forgotten relation errors in tests instead of firing queries in production. With async SQLAlchemy the same leak shows up as `MissingGreenlet: greenlet_spawn has not been called`, and after the session closes as `DetachedInstanceError`; both mean the entity escaped its unit of work.

Prevent: a query-count assertion in integration tests for list endpoints, a review of top `pg_stat_statements` entries after releases, and a slow-query alert.

**Follow-ups they will ask:**
- `joinedload` or `selectinload`?: `selectinload` for collections, which avoids multiplying rows; `joinedload` for many-to-one.
- Prisma has no lazy loading, so are we safe?: The N+1 just moves into a loop of `findUnique` calls; use `include` or one `findMany` with `in`.

**Mistakes to avoid:**
- Putting a cache in front of the endpoint and leaving the N+1 in place.
- Making every relation eager, which loads large graphs for endpoints that need none of them.

### Q. After a refactor into modules, the API dies at startup with `Nest can't resolve dependencies of the OrdersService (?)` and the Python worker with `cannot import name ... from partially initialized module`. How do you find and break the cycle?
**Short answer (45 seconds):** Both usually mean two modules import each other, so at import time one side sees the other as `undefined` or half-built. I find the cycle with a graph tool rather than by reading files, then break it by direction: extract the shared piece into a third module, invert one dependency behind an interface, or replace a call with an event. `forwardRef()` or a function-level import is a stopgap, not the fix.

**Deeper explanation:** Find it:

```bash
npx madge --circular --extensions ts src
npx depcruise src --config .dependency-cruiser.js   # config from depcruise --init
lint-imports                                        # Python, with layers or independence contracts
node --trace-warnings dist/main.js                  # CommonJS cycle warnings with stack traces
```

The `?` marks the constructor parameter Nest could not resolve; when that provider is registered and exported, the usual reason is a circular file import, so the parameter's class was still `undefined` when decorator metadata was recorded. Between modules, Nest instead reports that an entry in a module's `imports` array is undefined and suggests `forwardRef()`. In CommonJS the same cycle can show as `TypeError: Class extends value undefined is not a constructor or null`, in ESM as `ReferenceError: Cannot access 'X' before initialization`.

Causes ranked: two services calling each other (orders asks billing for invoices, billing asks orders for totals); a module importing its own barrel `index.ts`; shared types defined in one feature and imported by another.

Fixes:
- Shared types move to the owning module's contract file or the shared kernel.
- Mutual calls get a direction: orders publishes `order.placed`, billing listens and reads orders through `OrdersApi`.
- Inside a module, import files directly rather than through its own barrel.

```text
before: orders <-> billing
after:  billing -> orders (OrdersApi)      orders --order.placed--> billing listener
```

Prevent: a `no-circular` rule and a no-deep-import rule in dependency-cruiser, or import-linter contracts, failing CI.

**Follow-ups they will ask:**
- When is `forwardRef()` acceptable?: Rarely, for a genuinely mutual relation inside one module; between modules it hides a boundary problem.
- Quick fix in Python?: Import inside the function to unblock a deploy, then fix the direction.

**Mistakes to avoid:**
- Adding `forwardRef()` everywhere until startup passes.
- Merging the two modules by reflex; decide by business capability, not by the error.

### Q. You added a self-hosted model as `class LocalModel extends OpenAIModel` because vLLM speaks the OpenAI API. A week later, agent runs fail only for tenants routed to it, and `instanceof LocalModel` checks start appearing in callers. What went wrong and how do you fix it?
**Short answer (45 seconds):** The subclass inherited promises it cannot keep (tool calling, parseable JSON, accurate token counts), so callers that are correct for every other provider now fail. It is a Liskov violation that compiled cleanly. I contain it by routing those tenants back through config, then replace inheritance with a small `ChatModel` interface, explicit capabilities and one contract suite for every provider.

**Deeper explanation:** Diagnosis:

1. Group failures by provider in traces (Langfuse or OpenTelemetry attributes): they cluster on the new subtype, not on prompts.
2. Run the provider contract tests against it; note every failure and every test someone wants to skip.
3. Read the overrides for methods that throw "not supported" or silently ignore a parameter.

| Base promise | What the subtype does |
| --- | --- |
| `tools` are honored | The server was started without `--enable-auto-tool-choice` and a `--tool-call-parser`, so `tool_choice: "auto"` requests fail |
| JSON output parses | The model wraps JSON in markdown fences and `JSON.parse` throws |
| `countTokens()` is accurate | Inherited OpenAI tokenizer and context limit, wrong for this model, so long prompts overflow |

The fix is composition:

```ts
interface ChatModel {
  readonly caps: { tools: boolean; jsonSchema: boolean; maxContextTokens: number };
  chat(req: ChatRequest): Promise<ChatResult>;
  countTokens(messages: Message[]): number; // each adapter brings its own tokenizer
}
// shared HTTP code is a helper both adapters call, not a parent class
const local = openAiCompatible(env.VLLM_URL, { tools: true, jsonSchema: false, maxContextTokens: 32_768 });
```

The router checks `caps` before routing a tool-using request, and JSON repair (strip fences, zod validation, one retry) lives in one decorator, not in callers.

Prevent: a `describe.each(allModels)` contract suite in CI that skips only by declared capability, never by ad hoc `it.skip`, plus a review rule against `instanceof` on providers.

**Follow-ups they will ask:**
- Is inheritance ever right here?: Only for a true behavioral subtype with the same features; even then a shared helper is usually simpler.
- How fast can you roll back?: Routing is config, so tenants move back to the hosted model without a deploy.

**Mistakes to avoid:**
- Patching callers with `instanceof`, which breaks again with the next provider.
- Tuning prompts per model when the broken contract is the real problem.

### Q. In code review, a PR adds a fourth feature-flag branch to a 250-line `POST /quotes` controller that already contains the discount and VAT rules, and a stale flag caused a wrong price last month. What do you ask for?
**Short answer (45 seconds):** Two problems. Business rules live in the HTTP layer, so the worker and agent tool that also create quotes carry their own copies, and flags are checked deep in the logic, so paths double with each flag. I ask for the new branch to land in a `CreateQuote` use case and pricing strategy, flags resolved once at the edge, and an owner and expiry for every flag, without blocking the PR on a full cleanup.

**Deeper explanation:**

```ts
// controller today (abridged)
if (flags.newPricing && tenant.region === 'AE' && !flags.legacyVat) { total = total * 1.05; }
else if (flags.newPricing && body.coupon) { /* ... */ }
```

What the review checks:
1. Duplication: `grep -rnE "1\.05|vatRate" src` finds copies in the controller, a worker and an agent tool, which explains totals that disagree.
2. Paths: four booleans in one function allow up to 16 combinations, and tests cover a handful.
3. Flag age: `git log -S "legacyVat" --reverse --format="%ad %an" | head -1` shows when it arrived; a flag at 100 percent rollout for months is dead code.

What I ask for, in priority order:
- In this PR: the new branch becomes a `PricingPolicy` implementation; the controller calls `createQuote.execute(dto, actor)` and maps the result.
- Flags resolved once at the request edge, `const pricing = flags.newPricing ? pricingV2 : pricingV1;`, and passed in, so the domain contains no flag checks.
- Flag hygiene: an owner and removal date per flag, a CI warning past that date, and a ticket to delete `legacyVat`.
- Table-driven tests per policy instead of per flag combination.
- The UAE VAT rate (5 percent) as dated configuration, not a literal.

Tone: a concrete code suggestion, last month's wrong price as the reason, approval conditional on extracting the new branch, and the old rules as a follow-up ticket.

**Follow-ups they will ask:**
- The author has a deadline?: Extracting only the new branch is small; the old code moves later.
- Are flags ever acceptable in the domain?: As a passed-in policy object, never a flag SDK call inside domain code.

**Mistakes to avoid:**
- Approving because "it works", which hands the next developer a fifth branch.
- Leaving style comments while missing the duplicated pricing rule.

### Q. After you replaced a direct `sendInvoice()` call with an `order.placed` event, finance finds orders with no invoice, and nothing appears in the error logs. How do you find where events disappear?
**Short answer (45 seconds):** Silent loss means some step treats an event as delivered before it is safely stored. I measure the gap with a reconciliation query, match it against deploys, then check four places: the dual write, an in-process emitter, early acks and unroutable messages. The fix: a transactional outbox, idempotent consumers and a reconciliation alert.

**Deeper explanation:**

```sql
SELECT o.id
FROM orders o
LEFT JOIN invoices i ON i.order_id = o.id
WHERE i.id IS NULL
  AND o.created_at BETWEEN now() - interval '7 days' AND now() - interval '15 minutes';
```

Gaps clustered around deploys point to in-flight loss; a steady trickle points to a consumer bug.

Causes ranked:
1. Dual write: commit, then publish; a crash or deploy in between loses the event, and publishing before commit creates invoices for rolled-back orders.
2. In-process emitter: Node's `EventEmitter` does not await async listeners, so a rejection never fails the request, and in-flight work dies with the pod.
3. Early ack: `noAck: true` in RabbitMQ, or a kafkajs handler that does not await its work, so the offset commits before the invoice exists.
4. Routing: RabbitMQ silently drops a message that matches no binding, unless `mandatory` is set or an alternate exchange is configured.

Broker checks: `kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group invoicing` for lag, `rabbitmqctl list_queues name messages consumers` for orphaned queues.

```ts
await prisma.$transaction(async (tx) => {
  const order = await tx.order.create({ data });
  await tx.outbox.create({ data: { type: 'order.placed', payload: { orderId: order.id } } });
});
// relay: publish unsent rows with confirms, then mark them sent
```

The consumer dedupes on event ID in an inbox table, acks after its own commit and dead-letters poison messages. Prevent: run the reconciliation query on a schedule with an alert, and test killing the process between commit and publish.

**Follow-ups they will ask:**
- Debezium instead of a polling relay?: Change data capture on the outbox table removes polling but adds Kafka Connect to run.
- How do you repair the orders already missing invoices?: Replay the reconciliation list through the same idempotent handler after the fix ships.

**Mistakes to avoid:**
- Retrying `publish()` and calling it fixed; a crash still loses the event.
- Blaming the broker when the loss is in your own code.

### Q. A mobile developer notices `passwordHash` and `internalNotes` in the `GET /users/:id` response after last week's migration. How do you contain it and make sure no future column leaks?
**Short answer (45 seconds):** Contain first: hotfix the endpoint to map through an explicit response DTO, purge cached copies, check access logs for who fetched it during the exposure window, and rotate anything secret that went out. The design cause is a handler returning the ORM entity and relying on a denylist (`@Exclude()` or a `toJSON` that deletes known fields), so every new column is public by default. The lasting fix is an allowlist response DTO per endpoint, enforced by tests on the published schema.

**Deeper explanation:** Diagnosis: `git log -p` on the entity and migration dates the new columns; then list controllers that return entity classes, and diff live responses against the OpenAPI document to find undeclared fields.

Causes ranked:
1. Entity returned directly, with `@Exclude()` on only the fields someone remembered.
2. Prisma queries without `select`, which return every scalar column, including ones added later.
3. A Mongoose `toJSON` transform that deletes a fixed list of fields.
4. A FastAPI handler without `response_model` returning all columns.

```ts
export const toUserResponse = (u: User) =>
  ({
    id: u.id,
    name: u.name,
    email: u.email,
    createdAt: u.createdAt.toISOString(),
  }) satisfies UserResponse; // extra or missing fields fail to compile
```

Typed against both shapes, the mapper also fails the build when an entity field is renamed or removed, instead of silently sending `undefined`. In FastAPI, `response_model=UserOut` returns only declared fields.

Prevent:
- A test over the generated OpenAPI document that fails if any response schema has a property matching `password`, `hash`, `secret`, `token` or `internal`.
- Contract tests per endpoint response (Pact when other teams consume the API).
- Input DTOs with `whitelist: true, forbidNonWhitelisted: true`, so the same drift cannot open mass assignment on writes.
- A review rule: no entity type in a controller's return type.

**Follow-ups they will ask:**
- Is `@Exclude()` enough if used carefully?: It fails open on the next column; prefer explicit mappers, or `@Expose()` with `@SerializeOptions({ strategy: 'excludeAll' })`.
- Do users need to be told?: If hashes or personal data left the system, security and legal decide; you supply the window and the records.

**Mistakes to avoid:**
- Writing `delete user.passwordHash` in the controller and calling it fixed.
- Downgrading it because the hashes are salted; it is still an incident.

### Practice
- Break it on purpose: store `currentUserId` on a NestJS default-scope provider, add an `await` before it is read, fire a few hundred concurrent requests from two users with autocannon, and count mismatched responses; then fix it with a parameter or AsyncLocalStorage and rerun.
- Turn on query logging for one list endpoint, write a test that asserts its query count, then add `selectinload` or `include` and watch the count drop to two.
- Run `npx madge --circular` on a real repository, fix one cycle, and add a dependency-cruiser `no-circular` rule to CI so it cannot return.
- Build an outbox for one event and kill the process between the order insert and the publish; confirm the relay still delivers exactly one invoice.
- Say it out loud: "In code review I found business rules in a controller. Here is the comment I would write, the minimum change I would require and the follow-up I would accept."
