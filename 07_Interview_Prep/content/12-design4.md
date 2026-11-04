## Architectural Patterns [Core]

> Senior interviews rarely ask you to recite pattern names. They ask why your last service was shaped the way it was, which way its imports pointed, and what you would change. A weak answer lists "MVC, clean, hexagonal, microservices" as if they were rival products. A strong answer separates code organization (layered, clean, hexagonal, vertical slice) from deployment shape (modular monolith, microservices, serverless) and communication style (event-driven), explains the dependency rule and how a tool enforces it, and names what each choice costs in files, latency and debugging time.

### In plain words
Think of a laptop and its USB-C port. The laptop decides the shape of the port, and any charger, monitor or drive that fits will work, whoever made it. The laptop never changes when you buy a new charger. In software, your business rules are the laptop, the ports are interfaces your code defines ("save this order", "charge this card"), and Postgres, Stripe or an LLM provider are the devices you plug in. Most architecture patterns are different answers to two questions: where do the rules live, and who is allowed to know about whom.

### Walkthrough: one request through a clean architecture
1. **interface adapters**: `POST /orders` reaches an Express, NestJS or FastAPI route, and the HTTP controller validates the body (zod, class-validator or Pydantic) into a `PlaceOrderCommand` DTO plus the authenticated user ID. It makes no business decisions; it only turns HTTP into a plain input object.
2. **application (use cases)**: The controller calls `placeOrder.execute(command)`. The use case is a plain class for one user intention: it loads what it needs, asks the domain to decide, saves the result and triggers side effects, and it owns the transaction boundary.
3. **domain**: The use case builds an `Order` entity and calls `order.addLine()` and `order.place()`. The entity enforces the invariants (at least one line, a positive total, legal status changes) and throws domain errors such as `EmptyOrderError`, using plain TypeScript or Python with no framework imports.
4. **ports**: To save and to charge, the use case talks only to interfaces, `OrderRepository` and `PaymentGateway`, declared in the application layer in domain terms (`save(order)`, `charge(amount, paymentMethodId)`), never in SQL rows or Stripe objects.
5. **adapters** (payment): `StripePaymentGateway` in **infrastructure** implements `PaymentGateway`. It calls the Stripe SDK with an idempotency key and maps Stripe errors to a domain `PaymentDeclinedError`, so nothing above it knows Stripe exists.
6. **adapters** (persistence): `PostgresOrderRepository` in **infrastructure** implements `OrderRepository`, maps the entity to rows through Prisma, TypeORM or SQLAlchemy and writes inside the use case's transaction. The ORM models live here, not in the domain.
7. **composition root**: All of these objects were built once at startup in `main.ts` or `bootstrap.py`: create the Postgres pool and the Stripe client, wrap them in adapters, inject the adapters into the use case and the use case into the controller. It is the only file that knows every concrete class; NestJS module providers or FastAPI `Depends` providers can play this role.
8. **interface adapters** (response): The use case returns a small result (order ID, status). The controller maps it to `201 Created` with JSON, and an error handler in the same layer maps `EmptyOrderError` to 422 and `PaymentDeclinedError` to 402.
9. **the dependency rule**: Source code dependencies point inward only. Interface adapters and infrastructure import the application layer, the application layer imports the domain, and the domain imports nothing from Express, NestJS, Prisma or Stripe.
10. **dependency inversion**: Control still flows outward at runtime (the use case ends up calling Stripe), but the import arrow points inward because the adapter implements a port that the core owns. That is what lets you test the use case with in-memory fakes and swap Stripe or Postgres without touching business code.

### Concepts you must understand
- Three questions separate the patterns: where do the business rules live, which way do source imports point, and what is one deployable unit.
- Layered, clean, hexagonal, onion and vertical slice organize code inside one deployable; modular monolith, microservices and serverless describe deployment units; event-driven describes how parts communicate and combines with any of them.
- Dependency inversion is the core move of clean, hexagonal and onion: the core declares an interface and the outer layer implements it, so imports point at the business rules instead of away from them.
- A port is an interface owned by the core and expressed in domain terms; an adapter translates between a port and one technology (HTTP, Postgres, Stripe, an LLM API).
- Inbound (driving) adapters call into the application (HTTP controllers, CLI commands, queue consumers, agent tool calls); outbound (driven) adapters are called by it (repositories, payment clients, LLM clients).
- The composition root is the one place that constructs concrete classes and wires them together; a DI container (NestJS, tsyringe, FastAPI `Depends`, dependency-injector) is a convenience for it, not the architecture itself.
- Every boundary costs interfaces, mapping code and files, so the amount of structure should match the amount of business logic and how long the code will live.
- A boundary only holds if a tool enforces it in CI: a folder name is a suggestion, a failing lint rule is a boundary.

| Pattern | Core idea | Dependency direction | Best for | Cost |
|---|---|---|---|---|
| Layered (n-tier, MVC) | Group code by technical layer: presentation, business, data access | Top down: controllers to services to repositories and the ORM | CRUD apps, small teams, short-lived services | Logic leaks into controllers and ORM models; one feature change touches every layer |
| Clean | Concentric rings: entities, use cases, interface adapters, frameworks and drivers | Inward only; the core owns interfaces that outer rings implement | Long-lived business logic, several delivery channels, swappable vendors | More files and mapping (DTO, entity, row); ceremony for simple CRUD |
| Hexagonal (ports and adapters) | An application core with ports; inbound adapters drive it, outbound adapters are driven by it | Adapters depend on the core's ports | Many inputs and outputs: HTTP, CLI, queues, tests, LLM providers | An interface per dependency; risk of abstractions nobody ever swaps |
| Onion | Domain model at the centre, then domain services, application services, then infrastructure and UI | Inward only | DDD-heavy domains with rich rules | Same as clean; in practice nearly identical |
| Vertical slice or feature-based | Code grouped by feature or by single use case; each slice owns its handler and data access | Slices are independent; shared code stays small | Many independent features, CQRS-style reads and writes | Duplication; shared rules can scatter across slices |
| Modular monolith | One deployable split into business modules with public APIs and owned data | Modules call each other's public API only, with no cycles | Most products until a concrete reason to split appears | Needs boundary enforcement; one deploy and one blast radius |
| Microservices | Independently deployable services, each owning its data, talking over the network | Through API and event contracts | Many teams needing independent deploys, scaling or stacks | Network failures, distributed data and transactions, platform and observability work |
| Event-driven | Components publish events to a broker and others react asynchronously | Producers do not know consumers; both depend on the event schema | Fan-out side effects, integrations, buffering slow work | Eventual consistency, duplicates and ordering, harder debugging |
| Serverless | Functions run per event on managed infrastructure (AWS Lambda, Cloud Run functions) | Functions depend on triggers and managed services | Spiky or low traffic, glue code, scheduled and event handlers | Cold starts, time limits, Postgres connection limits, vendor lock-in, harder local testing |

### Q. Layered vs clean vs hexagonal architecture: what is the real difference?
**Short answer (45 seconds):** The real difference is the direction of dependencies and where business rules live. In a classic layered app the service imports the data layer, so the schema and the ORM shape the business code. Clean and hexagonal invert that: the core declares interfaces, and HTTP, the database and vendor SDKs plug in from outside. Hexagonal describes the outside (ports, inbound and outbound adapters); clean also prescribes the inside (entities, then use cases).

**Deeper explanation:**

```text
Layered:    Controller -> OrderService -> OrderRepository (Prisma) -> Postgres
            OrderService imports Prisma types; tests need a DB or module mocks

Clean/Hex:  Controller -> PlaceOrder -> OrderRepository (interface)
                                              ^ implements
                                PostgresOrderRepository (Prisma)
            PlaceOrder imports only the interface; tests use an in-memory fake
```

Layered is not wrong. For CRUD with thin rules it is the fastest structure to read, and a NestJS service that injects a repository already gets part of the benefit. It stops paying off when rules get rich: logic leaks into controllers and ORM models, services become scripts of queries, and replacing a vendor means editing business code. Clean and hexagonal cost more files and mapping, which is worth it when the business logic is the valuable part, will outlive frameworks, or is driven by several inputs (HTTP, a queue, a CLI, an agent's tool call). Onion is the same inversion drawn with the domain model at the centre.

**Follow-ups they will ask:**
- Is MVC an architecture? : it is a presentation pattern; the M usually becomes the ORM model, which is where logic leaks in layered apps.
- Strict or relaxed layering? : strict allows calls only to the layer directly below; relaxed lets a controller reach a repository, which most teams quietly do.
- Which for a new service? : layered for a CRUD admin API, clean or hexagonal for a core domain with rules, payments or many integrations.

**Mistakes to avoid:**
- Saying clean means "more folders"; the folders mean nothing if the domain still imports Prisma.
- Treating the hexagon's six sides as meaningful; the point is symmetry between inputs and outputs.

### Q. What is the dependency rule, and how do you enforce it in a TypeScript or Python codebase?
**Short answer (45 seconds):** Source code dependencies point inward: the domain imports nothing outside itself, the application imports only the domain, adapters import both, and only the composition root imports everything. I enforce it with tools that fail CI: dependency-cruiser or eslint-plugin-boundaries in TypeScript, Nx module boundary rules in an Nx monorepo, import-linter in Python. Code review covers what tools cannot see, such as a vendor type smuggled through a port.

**Deeper explanation:**

```js
// .dependency-cruiser.js, CI runs: npx depcruise src --config .dependency-cruiser.js
module.exports = {
  forbidden: [
    { name: 'domain-is-pure', severity: 'error',
      from: { path: '^src/domain' },
      to: { path: '^src/(application|infrastructure|interfaces)|^node_modules/(express|@nestjs|@prisma|stripe)' } },
    { name: 'application-not-outer', severity: 'error',
      from: { path: '^src/application' },
      to: { path: '^src/(infrastructure|interfaces)' } },
    { name: 'no-cycles', severity: 'error', from: {}, to: { circular: true } },
  ],
};
```

eslint-plugin-boundaries gives the same feedback in the editor: you declare element types by folder pattern and list which may import which. In Nx you tag projects (`scope:orders`, `type:domain`) and `@nx/enforce-module-boundaries` rejects imports that break its `depConstraints`. In Python, import-linter reads contracts from `pyproject.toml` or `.importlinter`: a `layers` contract (adapters above application above domain) and a `forbidden` contract that keeps `fastapi`, `sqlalchemy` and `openai` out of the domain; `lint-imports` runs in CI and pre-commit. TypeScript also offers a compile-time version: separate packages or project references, so an illegal import does not resolve at all.

**Follow-ups they will ask:**
- Adding this to a messy codebase? : start in warn mode, record current violations as a baseline (dependency-cruiser supports a known-violations file) and fail only new ones.
- NestJS decorators in the domain? : keep `@Injectable()` on application and adapter classes; entities stay plain.

**Mistakes to avoid:**
- Relying on a README and review alone; boundaries erode one quick-fix import at a time.
- Ports that return ORM or SDK types, which pass every lint rule while coupling the core to a vendor.

### Q. Vertical slice or layered: how do you organize code by feature versus by technical layer?
**Short answer (45 seconds):** By layer puts `controllers/`, `services/` and `repositories/` at the top; by feature puts `orders/`, `billing/` and `users/` at the top, each holding its own controller, service and repository. Most changes are per feature, so feature-first keeps a pull request inside one folder, makes ownership obvious and lets you delete a feature by deleting a folder. Vertical slice goes further: each use case is its own slice. My default is feature folders at the top and layers inside each one.

**Deeper explanation:**

```text
by layer               by feature               vertical slice
controllers/           orders/                  orders/
  order.controller.ts    order.controller.ts      place-order/
  user.controller.ts     order.service.ts           endpoint.ts, handler.ts
services/                order.repository.ts      get-order-summary/
  order.service.ts     users/                       query.sql, handler.ts
repositories/            user.controller.ts
```

By layer suits a small API, but it hides coupling: any service can import any repository, and nothing shows that billing reads the orders tables. By feature makes cross-feature imports visible and lintable. Vertical slice architecture, popularized by Jimmy Bogard, fits CQRS: a read slice can run one hand-written SQL query into a DTO while a write slice goes through the domain model, and slices change without touching each other. Its cost is duplication and scattered rules, so keep a shared domain model for invariants several slices must respect, and extract common code on the third copy, not the first.

**Follow-ups they will ask:**
- Where do cross-cutting things go? : technical concerns (auth guard, logger, error handler) in `common/`; a business concept many features use becomes its own module.
- How do features talk? : through the other feature's public service or its events, never its repository or tables.
- Feature folders with clean architecture? : yes, put `domain/`, `application/` and `infrastructure/` inside any feature with enough logic to need them.

**Mistakes to avoid:**
- A `shared/` or `utils/` folder that slowly absorbs business logic because nobody knew which feature owned it.

### Q. How do you keep a modular monolith modular as it grows?
**Short answer (45 seconds):** Modules follow business capabilities, not technical layers. Each has one public entry (an `index.ts` facade or a package's `__init__.py`), private internals and its own tables, and talks to other modules only through that API or in-process events. Then make the rules mechanical: boundary lint in CI, no cycles, an owner per module in CODEOWNERS. Modularity dies through small shortcuts (a cross-module join, a deep import, a shared model), so each shortcut must fail the build. When and how to split a module out is covered in the Backend track, section "Resilience & Microservice Patterns"; this is about not needing to.

**Deeper explanation:**
The rules I would set on day one:

1. Public API only: `import { OrdersApi } from '@/modules/orders'` passes, a deep import into `orders/internal` fails lint.
2. Data ownership: one Postgres schema per module, no foreign keys or joins across schemas; billing reads orders through `OrdersApi` or keeps a read model fed by events.
3. Queries through facades, side effects through an in-process event bus, which can later become an outbox plus a broker without changing the modules.
4. No cycles: if orders and billing call each other, they are one module or one direction should become an event.
5. Each module's tests run against its public API with the other modules faked.

Shopify enforces this style in its Rails monolith with Packwerk; in Node you get it from dependency-cruiser or Nx, and in Python from an import-linter `independence` contract. Track cross-module edges and violations over time; a rising count is the early warning.

**Follow-ups they will ask:**
- Entities everyone needs, like User? : the identity module owns users; others keep a small view (billing's Customer) keyed by user ID.
- A transaction across two modules? : prefer one module per transaction plus events; if two must always commit together, the boundary is probably wrong.

**Mistakes to avoid:**
- A shared `models/` folder every module imports, which makes the database schema the real API.

### Q. When is event-driven architecture the right choice, and what does it cost you?
**Short answer (45 seconds):** It fits when one fact triggers many independent reactions (an order is placed, so send email, update search, reserve stock), when the producer must not wait for or know its consumers, when slow work like embedding jobs needs a buffer, and when separate systems integrate. The cost is eventual consistency, flows no single file shows, duplicate and out-of-order delivery that forces idempotent consumers, schema versioning and a broker to run. It is wrong when the user needs the result in the same request.

**Deeper explanation:**
Be precise about the kind. Event notification says "order 123 was placed" and consumers fetch details; event-carried state transfer puts the data in the event; event sourcing stores events as the source of truth, a much bigger commitment. Choreography suits simple fan-out; orchestration (a saga orchestrator or a workflow engine such as Temporal) suits ordered steps with compensations, because one place holds the state.

```json
{
  "id": "evt_8f2c41",
  "type": "order.placed",
  "version": 2,
  "occurredAt": "2026-11-01T10:15:00Z",
  "correlationId": "req_7f3a",
  "data": { "orderId": "ord_123", "totalMinor": 499900, "currency": "INR" }
}
```

The `id` lets consumers deduplicate with an inbox table, `version` lets the schema evolve additively, and `correlationId` (or W3C trace context in message headers) keeps one trace across services. Publish through an outbox so a crash between commit and publish loses nothing. Kafka keeps an ordered, replayable log per partition key; RabbitMQ and SQS remove a message once it is acknowledged.

**Follow-ups they will ask:**
- A poison message? : bounded retries with backoff, then a dead-letter queue, an alert and a replay tool.
- Evolving schemas? : additive changes, a version field, and a schema registry (Avro or Protobuf) when many teams consume.

**Mistakes to avoid:**
- Hidden request/response: publishing an event and then blocking until a reply event arrives.
- Going event-driven for a three-step CRUD flow and paying the debugging cost for nothing.

### Q. Which architecture would you pick for an AI product with a React front end, an API, RAG and agents, and why?
**Short answer (45 seconds):** A modular monolith API with hexagonal boundaries around everything volatile: LLM providers, the vector store, embedding models and agent tools sit behind ports. The React or Next.js front end is a separate app with a typed contract, and a worker process from the same codebase handles ingestion and long agent runs through a queue. I would split out a service only for a concrete reason: a Python-only library, self-hosted models on GPUs, or ingestion that must scale alone.

**Deeper explanation:**

```text
web (Next.js) --HTTP + SSE--> api (modular monolith)
                              modules: identity, documents, chat, billing
                              ports: LlmClient, Embedder, VectorStore, ToolRegistry
                              adapters: Anthropic, OpenAI, pgvector, Redis
api --queue (BullMQ or Celery)--> worker (same code, other entrypoint)
                              ingest, chunk, embed, long agent runs
```

Models and prices change every few months, so an `LlmClient` port with a router adapter turns a model switch into config and lets tests run against a fake. RAG is a chain of swappable stages (chunker, embedder, retriever, reranker), which is what evals need to compare one change at a time. The agent loop is an application-layer use case, and its tools are adapters that call the same use cases as the HTTP API, so permission checks live in one place and no tool gets raw database access. Business rules stay deterministic in the domain: the model proposes a refund, the domain decides whether it needs approval. Microservices per agent or per pipeline stage would add network hops to a path already dominated by LLM latency.

**Follow-ups they will ask:**
- Node or Python for the API? : see the Internal Architecture track, section "Node.js vs FastAPI, Side by Side"; a common answer is a Node product API plus a Python AI service when ML libraries matter.
- Where do prompts live? : versioned files in the repo, loaded by ID and logged on every trace.

**Mistakes to avoid:**
- Calling the OpenAI SDK directly from route handlers, leaving no single place for timeouts, retries, cost tracking or a model swap.

### Practice
- Take one Express or FastAPI endpoint you own, extract a use case with an `OrderRepository` port, and write a unit test with an in-memory fake; compare its runtime with the old database-backed test.
- Add dependency-cruiser (TypeScript) or import-linter (Python) with a domain-purity rule and a no-cycles rule, commit a violating import on a branch, and confirm CI fails with a readable message.
- Implement an `LlmClient` port with an Anthropic adapter, an OpenAI adapter and a deterministic fake, and switch between them with one config value.
- Run `git log --stat` over the last 20 feature commits in a project organized by layer, and count how many folders each change touched.
- Say it out loud: in 90 seconds, explain which way the imports pointed in your last production service, why, and what you would change if you rebuilt it.

## Sample Folder Structures [Core]

> Interviewers and take-home reviewers judge a structure in the first minute: they open the tree, look for where business rules live, and check whether the folders tell them what the system does or only which framework it uses. Each tree below is a starting point, not a standard. For every one, know what each folder owns, which way imports may flow between folders, and the single rule that keeps it clean, because that is what the follow-up questions test.

### In plain words
Think of a large office building. Each department, like sales or billing, has its own floor, its own front desk and its own filing cabinets. Visitors talk to the front desk; they never walk into the back office and dig through the files. Shared things like the lifts and the lobby sit in one place everyone can use. A folder structure is the floor plan of your code: features are the departments, a module's `index.ts` is the front desk, and the shared folder is the lobby.

### Concepts you must understand
- Group by feature first and by technical layer second, so one change to one capability touches one folder.
- Keep framework code at the edges: controllers, ORM models and SDK clients sit in outer folders, and business rules sit in plain code you can test without starting a server.
- Give each module one public entry (an `index.ts`, an `__init__.py`, a NestJS module's `exports`) and forbid deep imports into another module's internals.
- Colocate unit tests with the code (`orders.service.spec.ts`) or mirror the package in `tests/` for Python; keep integration and end-to-end tests separate because they need real infrastructure.
- Keep config and secrets out of code: read environment variables once in a typed, validated config module (zod, `@nestjs/config`, pydantic-settings) and commit `.env.example`, never `.env`.
- Separate building the app from starting it (`app.ts` and `server.ts`, or a `create_app()` factory) so tests and workers can create the app without opening a port.
- Use one naming convention per language: kebab-case files with role suffixes in TypeScript (`place-order.use-case.ts`, `order.controller.ts`), snake_case modules in Python (`order_service.py`), so a glob finds every file of one kind.
- Treat a growing `utils/` or `helpers/` folder as a smell: anything with a business word in it belongs to a feature.

### Q. How would you structure an Express.js API using a layered architecture?
**Short answer (45 seconds):** Split by technical layer, one job each: routes map URLs to middleware and controllers, controllers translate HTTP, services hold business rules, repositories hold data access. Cross-cutting concerns live in middlewares and environment reading lives in config. `app.ts` builds the app and `server.ts` starts it, so tests import the app without opening a port.

**Deeper explanation:**

```text
order-api/
├── src/
│   ├── app.ts                   # builds the Express app, no listen()
│   ├── server.ts                # listen, SIGTERM, close the DB pool
│   ├── config/index.ts          # zod-validated env, read once
│   ├── routes/
│   │   ├── index.ts             # mounts /api/v1 routers
│   │   └── order.routes.ts      # path + middleware chain + controller
│   ├── controllers/
│   │   └── order.controller.ts  # req to input, call service, status code
│   ├── services/
│   │   └── order.service.ts     # business rules, transactions
│   ├── repositories/
│   │   └── order.repository.ts  # every SQL or Prisma call
│   ├── models/
│   │   └── order.model.ts       # types or ORM schema
│   ├── validators/
│   │   └── order.schema.ts      # zod schemas for body, params, query
│   ├── middlewares/
│   │   ├── auth.ts
│   │   ├── validate.ts          # runs a schema, 400 on failure
│   │   └── error-handler.ts     # last middleware, errors to JSON
│   └── utils/logger.ts          # pino instance
├── tests/
│   ├── unit/order.service.test.ts
│   └── integration/orders.test.ts   # supertest against app.ts
├── .env.example
├── package.json
└── tsconfig.json
```

`routes/` owns URLs, versions and middleware order. `controllers/` own HTTP only: read `req`, call one service method, pick the status. `services/` own business rules and transaction boundaries and never import Express. `repositories/` own data access, so query tuning happens in one place. `models/` hold data shapes, `validators/` request schemas, `middlewares/` auth, validation, request IDs and the error handler, `config/` is the only code that reads `process.env`, and `utils/` holds helpers with no business meaning.

The dependency rule runs one way: routes, controllers, services, repositories, models. Nothing imports upward, only controllers and middlewares see `req` and `res`, and services throw typed errors (`NotFoundError`) that the error handler maps to status codes.

**Follow-ups they will ask:**
- Where does a transaction start? : in the service, which passes a transaction client to each repository call.
- Async errors? : Express 5 forwards rejected promises to the error handler; Express 4 needs a wrapper or `express-async-errors`.
- When does this stop scaling? : past roughly ten resources, move to feature folders such as `src/modules/orders/` holding its own routes, controller, service and repository.

**Mistakes to avoid:**
- Fat controllers that run Prisma queries inline, or services that take `req`, which ties business logic to Express and makes it untestable without HTTP.

### Q. How do you structure a NestJS application with feature modules?
**Short answer (45 seconds):** One folder per feature under `src/modules`, each with its DTOs, entities, controller, service, repository and a module file that declares providers and exports only what other modules may use. Framework pieces shared by every feature (guards, interceptors, pipes, filters, decorators) go in `common/`, config and migrations get their own folders, and `main.ts` and `app.module.ts` are the only root files.

**Deeper explanation:**

```text
src/
├── main.ts                    # NestFactory.create, global pipes, listen
├── app.module.ts              # ConfigModule, DatabaseModule, feature modules
├── config/
│   ├── configuration.ts       # typed config factory
│   └── env.validation.ts      # schema checked at boot
├── common/
│   ├── guards/jwt-auth.guard.ts
│   ├── interceptors/logging.interceptor.ts
│   ├── pipes/parse-uuid.pipe.ts
│   ├── filters/http-exception.filter.ts
│   └── decorators/current-user.decorator.ts
├── database/
│   ├── data-source.ts         # TypeORM DataSource for the migration CLI
│   └── migrations/1730000000000-CreateOrders.ts
└── modules/
    ├── orders/
    │   ├── dto/
    │   │   ├── create-order.dto.ts    # class-validator rules
    │   │   └── order-response.dto.ts
    │   ├── entities/order.entity.ts
    │   ├── orders.controller.ts
    │   ├── orders.service.ts
    │   ├── orders.service.spec.ts
    │   ├── orders.repository.ts
    │   └── orders.module.ts           # providers, exports: [OrdersService]
    └── payments/
test/
├── orders.e2e-spec.ts
└── jest-e2e.json
```

`modules/` owns business features; other modules import `OrdersModule` and inject `OrdersService`, never its repository or entity. `common/` owns cross-cutting Nest pieces: guards decide whether a request reaches a handler, interceptors wrap it (logging, timing, response mapping), pipes validate and transform input, filters turn exceptions into responses, and decorators such as `@CurrentUser()` read request data. `config/` loads and validates env at boot through `@nestjs/config`. `database/` holds the DataSource and migrations (with Prisma this becomes a `prisma/` folder). `main.ts` sets a global `ValidationPipe({ whitelist: true, transform: true })`, calls `enableShutdownHooks()` and listens. Unit specs sit next to the code; e2e tests live in `test/`, as the Nest CLI generates them.

Dependency rule: feature modules use other modules' exported providers only, `common/` imports nothing from `modules/`, and needing `forwardRef()` to break a circular import means merging the two modules or turning one direction into an event (`@nestjs/event-emitter`).

**Follow-ups they will ask:**
- Use cases in a complex module? : add `domain/` and `application/` inside it and keep the Nest service as a thin facade.
- Global or per-route guards? : a global auth guard through `APP_GUARD`, plus a `@Public()` metadata decorator for open routes.

**Mistakes to avoid:**
- A `SharedModule` that imports and re-exports everything, so every module silently depends on every other.

### Q. How do you structure a FastAPI service?
**Short answer (45 seconds):** One `app` package: versioned routers in `api/v1/routes`, settings and security in `core`, Pydantic models in `schemas`, SQLAlchemy tables in `models`, business logic in `services`, queries in `repositories`, and `Depends` providers in `dependencies`. Background jobs live in `workers` and run in a separate process, Alembic owns migrations, and `tests` overrides dependencies through `conftest.py`.

**Deeper explanation:**

```text
order-service/
├── app/
│   ├── main.py                  # create_app(): routers, lifespan, handlers
│   ├── api/v1/
│   │   ├── router.py            # includes every route module
│   │   └── routes/
│   │       ├── orders.py        # thin path operations
│   │       └── health.py
│   ├── core/
│   │   ├── config.py            # pydantic-settings Settings
│   │   └── security.py          # JWT decode, password hashing
│   ├── schemas/order.py         # OrderCreate, OrderUpdate, OrderRead
│   ├── models/order.py          # SQLAlchemy ORM classes
│   ├── services/order_service.py
│   ├── repositories/order_repository.py
│   ├── dependencies/
│   │   ├── db.py                # yields one AsyncSession per request
│   │   └── auth.py              # get_current_user
│   ├── db/session.py            # async engine, sessionmaker
│   └── workers/tasks.py         # Celery or ARQ jobs: email, embeddings
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── tests/
│   ├── conftest.py              # app fixture, test DB, dependency_overrides
│   ├── api/test_orders.py
│   └── services/test_order_service.py
└── pyproject.toml
```

`api/v1/routes` holds thin path operations: Pydantic parses input, one service call, a `response_model` on the way out; `v1` lets a `v2` coexist. `core/` holds app-wide settings, read once, and security primitives. `schemas/` is the API contract and `models/` the tables, kept apart so a column like `hashed_password` never leaks into a response; read schemas use `ConfigDict(from_attributes=True)`. `services/` raise domain errors, not `HTTPException`, and an exception handler maps them. `dependencies/` provides sessions, the current user and services, and is the test seam through `app.dependency_overrides`. `workers/` run Celery, ARQ or Dramatiq jobs; `BackgroundTasks` is only for small fire-and-forget work. `alembic/` is driven by `alembic revision --autogenerate` and `alembic upgrade head`.

Dependency rule: routes use dependencies and services, services use repositories, repositories use models; `services/` never imports `fastapi`, `models/` never imports `schemas/`, and workers call services, never routes.

**Follow-ups they will ask:**
- Why a `create_app()` factory? : tests and workers build the app with their own settings and no import-time side effects.
- Why three schemas per resource? : create, update and read have different required fields, and separate models keep the contract explicit.

**Mistakes to avoid:**
- A sync database driver or `requests` call inside an `async def` route, which blocks the event loop for every request (Internal Architecture track, section "FastAPI & Python Async Architecture").

### Q. What does clean architecture look like as folders in a TypeScript service?
**Short answer (45 seconds):** Five top-level folders matching the rings: `domain` for entities and value objects, `application` for use cases and the ports they need, `infrastructure` for outbound adapters that implement those ports, `interfaces` for inbound adapters such as HTTP controllers, and `main` as the composition root. Imports point inward only, so `domain` imports nothing and only `main` knows every concrete class.

**Deeper explanation:**

```text
src/
├── domain/
│   ├── order/
│   │   ├── order.ts                    # entity: invariants, status changes
│   │   ├── order-line.ts               # value object
│   │   ├── money.ts                    # integer minor units
│   │   └── order.errors.ts             # EmptyOrderError, OrderAlreadyPaid
│   └── shared/entity-id.ts
├── application/
│   ├── ports/
│   │   ├── order.repository.ts         # interface OrderRepository
│   │   ├── payment.gateway.ts          # interface PaymentGateway
│   │   └── clock.ts
│   └── use-cases/
│       ├── place-order.use-case.ts
│       ├── place-order.use-case.spec.ts   # in-memory fakes, no DB
│       └── cancel-order.use-case.ts
├── infrastructure/
│   ├── db/
│   │   ├── pg-order.repository.ts      # implements OrderRepository
│   │   └── migrations/
│   ├── http/
│   │   └── stripe-payment.gateway.ts   # calls Stripe
│   └── messaging/kafka-event.publisher.ts
├── interfaces/
│   └── http/
│       ├── order.controller.ts         # Express or Fastify handler
│       ├── order.dto.ts                # request schema and mapping
│       └── error-mapper.ts             # domain error to HTTP status
└── main/
    ├── container.ts                    # composition root
    └── server.ts
```

`domain/` owns business rules in plain TypeScript: `Order` refuses an illegal status change, `Money` stores integer minor units so totals never drift. `application/` owns the use cases and the ports they depend on, and its specs run in milliseconds against fakes. `infrastructure/` owns outbound adapters: Postgres repositories with migrations, the Stripe client, the Kafka publisher. `interfaces/` owns inbound adapters: controllers, request DTOs and the error mapping. Note the two `http` folders: `infrastructure/http` calls other systems, `interfaces/http` is called by clients. `main/container.ts` constructs everything once.

Dependency rule: `domain` imports nothing outside itself, `application` imports `domain`, `infrastructure` and `interfaces` import both, and `main` imports all of them. The dependency-cruiser config from the Architectural Patterns section fails CI on any outward arrow.

**Follow-ups they will ask:**
- How does NestJS inject an interface? : TypeScript interfaces vanish at runtime, so bind a token (`{ provide: ORDER_REPOSITORY, useClass: PgOrderRepository }`) and use `@Inject(ORDER_REPOSITORY)`, or make the port an abstract class.
- Where do list and report queries go? : a query service in `application` with its own port, often plain SQL; not every read needs the entity.

**Mistakes to avoid:**
- Putting TypeORM `@Entity()` classes or Prisma types in `domain`, which makes the inner ring depend on the ORM and defeats the structure.

### Q. What does hexagonal architecture look like as folders in a Python service?
**Short answer (45 seconds):** The core is `domain` plus `application`, which declares inbound ports (the use cases the outside may call) and outbound ports (what the core needs, such as a repository or an LLM client). `adapters/inbound` holds what drives the app (HTTP routes, a CLI), `adapters/outbound` holds what the app drives (the database, LLM providers), and `bootstrap.py` plugs adapters into ports.

**Deeper explanation:**

```text
support-agent/
├── src/support_agent/
│   ├── domain/
│   │   ├── ticket.py                  # Ticket entity, status rules
│   │   ├── refund_policy.py           # pure rule: when approval is needed
│   │   └── errors.py
│   ├── application/
│   │   ├── ports/
│   │   │   ├── inbound.py             # ResolveTicket use case protocol
│   │   │   └── outbound.py            # TicketRepository, LlmClient, Notifier
│   │   └── services/
│   │       └── resolve_ticket.py      # implements the inbound port
│   ├── adapters/
│   │   ├── inbound/
│   │   │   ├── http/
│   │   │   │   ├── routes.py          # FastAPI router calls ResolveTicket
│   │   │   │   └── schemas.py         # Pydantic request and response
│   │   │   └── cli/main.py            # Typer command, same use case
│   │   └── outbound/
│   │       ├── db/
│   │       │   ├── orm.py             # SQLAlchemy mappings
│   │       │   └── sqlalchemy_ticket_repository.py
│   │       └── llm/
│   │           ├── anthropic_client.py
│   │           ├── openai_client.py
│   │           └── fake_client.py     # deterministic, for tests
│   └── bootstrap.py                   # builds adapters, wires services
├── tests/
│   ├── unit/                          # domain and services with fakes
│   └── integration/                   # real Postgres, recorded LLM replies
└── pyproject.toml
```

`domain/` owns pure rules; `refund_policy.py` decides whether a refund needs a human, with no I/O. `application/ports/outbound.py` defines ports as `typing.Protocol` classes, so adapters satisfy them structurally without importing the core's base classes. `adapters/inbound/` holds a FastAPI router and a Typer command calling the same use case, which is the point of hexagonal: every driver is equal. `adapters/outbound/llm/` has one adapter per provider plus a fake, each mapping the vendor's response into the core's own `Completion` type. `bootstrap.py` reads settings, builds the engine and clients, and hands wired services to whichever entry point started.

```python
class LlmClient(Protocol):
    async def complete(self, messages: list[Message], max_tokens: int) -> Completion: ...
```

Dependency rule: adapters import application and domain, application imports domain, and neither inner layer imports `fastapi`, `sqlalchemy`, `anthropic` or `openai`. An import-linter `layers` contract enforces it in CI.

**Follow-ups they will ask:**
- Why `Protocol` and not `abc.ABC`? : structural typing keeps adapters decoupled and any small class can be a fake; mypy or pyright checks it.
- Can the repository raise SQLAlchemy errors? : no, it translates them (an `IntegrityError` becomes a domain `DuplicateTicketError`).

**Mistakes to avoid:**
- Returning the SDK's response objects through the port, so the core quietly depends on one vendor's types.

### Q. How do you lay out a modular monolith?
**Short answer (45 seconds):** One folder per business module under `modules/`, each with an `index.ts` that is its entire public API and an `internal/` folder nobody else may import. A small `shared-kernel` holds the few types every module agrees on, `platform` holds plumbing with no business logic, `main.ts` boots the modules, and a CI boundary rule makes deep imports fail. The rules for keeping it modular over time are in the Architectural Patterns section; this is the layout.

**Deeper explanation:**

```text
repo/
├── src/
│   ├── main.ts                       # composition root: boots every module
│   ├── modules/
│   │   ├── orders/
│   │   │   ├── index.ts              # public API: OrdersApi, OrderPlaced
│   │   │   ├── orders.module.ts      # wiring for this module only
│   │   │   ├── internal/
│   │   │   │   ├── domain/
│   │   │   │   ├── application/
│   │   │   │   ├── infrastructure/   # repositories on schema "orders"
│   │   │   │   └── http/             # this module's routes
│   │   │   └── tests/
│   │   ├── billing/
│   │   │   ├── index.ts              # BillingApi
│   │   │   └── internal/
│   │   ├── catalog/
│   │   └── identity/
│   ├── shared-kernel/
│   │   ├── money.ts                  # small, stable, agreed types
│   │   ├── user-id.ts
│   │   └── domain-event.ts
│   └── platform/
│       ├── event-bus.ts              # in-process now, outbox + broker later
│       ├── db.ts                     # one pool, one schema per module
│       └── logger.ts
├── .dependency-cruiser.js            # boundary rules, run in CI
└── package.json
```

Each `index.ts` exports a facade, its DTOs and its event types, nothing else. `internal/` can be clean or simply layered; each module picks its own depth, and its repositories touch only its own Postgres schema. `shared-kernel/` stays small and changes only by agreement between module owners. `platform/` owns the database pool, the event bus and logging. `main.ts` registers each module's routes and event handlers.

Dependency rule: a module imports another only through its `index.ts` and never in a cycle; `shared-kernel/` and `platform/` import no module. The dependency-cruiser rule uses a capture group so a module may still import its own internals:

```js
{ name: 'only-public-api', severity: 'error',
  from: { path: '^src/modules/([^/]+)/' },
  to: { path: '^src/modules/[^/]+/internal/', pathNot: '^src/modules/$1/' } }
```

**Follow-ups they will ask:**
- Python equivalent? : packages under `modules/` with `__init__.py` as the public API and an import-linter `independence` contract.
- How do modules react to each other? : orders publishes `OrderPlaced` on the bus and billing subscribes in its own setup; orders never imports billing.

**Mistakes to avoid:**
- Letting `shared-kernel/` grow a 40-field `User` and half the business rules, which recouples every module through one folder.

### Q. How do you structure a monorepo with a Next.js app, a NestJS API and shared packages?
**Short answer (45 seconds):** Deployables go in `apps/` (web, api, worker), reusable libraries in `packages/` (ui, types, db, config), scripts in `tooling/`, all wired with pnpm workspaces and a task runner, Turborepo or Nx, that builds in dependency order and caches results. Apps depend on packages, packages never depend on apps, and CI runs only what a change affects.

**Deeper explanation:**

```text
acme/
├── apps/
│   ├── web/                     # Next.js App Router
│   │   ├── app/
│   │   ├── next.config.ts
│   │   └── package.json         # @acme/ui, @acme/types
│   ├── api/                     # NestJS
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── package.json         # @acme/db, @acme/types
│   └── worker/                  # BullMQ consumers: ingestion, email
│       ├── src/
│       └── package.json         # @acme/db, @acme/types
├── packages/
│   ├── ui/                      # React components, design tokens
│   ├── types/                   # zod schemas and inferred API types
│   ├── db/                      # Prisma schema, client, migrations
│   └── config/
│       ├── eslint/
│       ├── tsconfig/            # base.json, nextjs.json, nestjs.json
│       └── prettier/
├── tooling/scripts/             # codegen, seed, release
├── turbo.json                   # task graph and cache outputs
├── pnpm-workspace.yaml          # apps/*, packages/*
├── package.json
└── .github/workflows/ci.yml     # lint, test, build affected packages
```

Each app owns its own `package.json`, Dockerfile, env and deploy. `packages/types` holds zod schemas shared by NestJS validation and Next.js forms, so a contract change breaks both at compile time; generating a client from the API's OpenAPI spec is the alternative. `packages/db` owns the Prisma schema, client and migrations and is used by `api` and `worker` only. `packages/ui` owns components, `packages/config` the shared ESLint, tsconfig and Prettier presets each workspace extends. Internal packages are referenced as `"@acme/types": "workspace:*"`. In `turbo.json`, `"dependsOn": ["^build"]` builds dependencies first and declared `outputs` make tasks cacheable locally and remotely; Nx offers the same through its project graph and `nx affected -t lint test build`.

Dependency rule: apps import packages, no app imports another app, and `ui` and `types` import nothing server-side. Nx tags (`type:app`, `scope:server`, `scope:shared`) or eslint-plugin-boundaries make that a lint error, and pnpm's non-flat `node_modules` makes undeclared imports fail.

**Follow-ups they will ask:**
- Turborepo or Nx? : Turborepo is a fast task runner with caching; Nx adds a project graph, generators and module boundary rules.
- Building one app's Docker image? : `turbo prune api --docker` produces a pruned workspace with only what `api` needs.

**Mistakes to avoid:**
- Letting `apps/web` import `packages/db` or a server secret, which ships server code toward the browser; `import 'server-only'` in server modules makes Next.js fail the build instead.

### Q. How do you structure a large React or Next.js front end by feature?
**Short answer (45 seconds):** Keep the routing folder (`app/` or `pages/`) thin and put the real code in `features/`, one folder per user-facing capability with its own components, hooks, API calls, store and types, exported through an `index.ts`. Business objects used by several features go in `entities/`, design-system components in `shared/ui`, framework glue in `lib/`. The rule that keeps it clean: features never import each other; pages compose them.

**Deeper explanation:**

```text
src/
├── app/                               # routes only: layouts, pages, errors
│   ├── layout.tsx
│   └── (dashboard)/
│       ├── layout.tsx
│       └── projects/[id]/page.tsx     # composes features, no logic
├── features/
│   ├── chat/
│   │   ├── components/ChatPanel.tsx
│   │   ├── hooks/useChatStream.ts     # SSE stream, abort on unmount
│   │   ├── api/chat.api.ts            # fetchers, TanStack Query keys
│   │   ├── store/chat.store.ts        # Zustand, UI state only
│   │   ├── types.ts
│   │   └── index.ts                   # the feature's public exports
│   ├── document-upload/
│   └── billing/
├── entities/
│   ├── user/                          # User type, UserAvatar, useCurrentUser
│   └── project/
├── shared/
│   └── ui/                            # Button, Dialog: no business words
├── lib/
│   ├── api-client.ts                  # fetch wrapper, auth header, errors
│   ├── env.ts                         # validated public env
│   └── utils.ts
└── test/msw/handlers.ts               # mocked API for component tests
```

`app/` owns routing, layouts, loading and error boundaries; a `page.tsx` fetches on the server and composes features. `features/chat/` owns everything chat needs: `api/` holds server state through TanStack Query, `store/` holds UI-only state in Zustand (an open panel, a draft), and `useChatStream` owns the SSE connection. `entities/` owns business objects shared by features. `shared/ui` owns business-free components and `lib/` owns the fetch client, env parsing and utilities. This is a light version of Feature-Sliced Design, whose layers (app, pages, widgets, features, entities, shared) may only import downward.

Dependency rule: `app` imports features, entities, shared and lib; features import entities, shared and lib; nothing imports upward, and no feature imports another feature. If chat needs billing's plan, the page passes it down or the plan moves into `entities/`. eslint-plugin-boundaries or `no-restricted-imports` patterns banning `@/features/*/*` deep imports enforce it.

**Follow-ups they will ask:**
- Server or client components inside a feature? : server components by default, with `'use client'` on the smallest interactive leaf, such as the input box.
- Where do tests go? : next to the component (`ChatPanel.test.tsx`), with MSW mocking the API at the network layer.

**Mistakes to avoid:**
- Copying server data into Redux or Zustand, which duplicates the TanStack Query cache and creates two sources of truth that drift.

### Q. How do you structure an AI service with RAG, agents and evals?
**Short answer (45 seconds):** One folder per stage of the AI path: thin `api` endpoints, a `rag` pipeline split by stage, `agents` with tools, prompts and graphs, and `llm` with provider clients and a router. Evals sit at the top level with datasets, judges and runs, prompts are versioned files, and CI runs evals on every change to prompts, retrieval or models.

**Deeper explanation:**

```text
ai-service/
├── app/
│   ├── main.py
│   ├── config.py                # model IDs, top_k, thresholds
│   ├── api/
│   │   ├── chat.py              # POST /chat, SSE stream
│   │   └── documents.py         # POST /documents, enqueue only
│   ├── rag/
│   │   ├── ingest/              # loaders, dedupe by content hash
│   │   ├── chunking/            # splitters, chunk metadata
│   │   ├── embeddings/          # Embedder port, provider adapters
│   │   ├── retrieval/           # pgvector + keyword, tenant filters
│   │   └── rerank/              # cross-encoder or rerank API
│   ├── agents/
│   │   ├── tools/               # one file per tool: schema, auth, handler
│   │   ├── prompts/             # support_v3.md, router_v1.md
│   │   └── graphs/              # agent loops, step limits, timeouts
│   ├── llm/
│   │   ├── clients/             # anthropic.py, openai.py, fake.py
│   │   └── router.py            # model choice, fallbacks, cost
│   └── observability/           # OpenTelemetry spans, token metrics
├── workers/ingest_worker.py     # chunk and embed off the request path
├── evals/
│   ├── datasets/                # golden questions, retrieval labels (JSONL)
│   ├── judges/                  # LLM-as-judge rubrics, exact checks
│   ├── runs/                    # results per prompt and model version
│   └── run_evals.py
├── tests/
└── .github/workflows/evals.yml  # runs on PRs touching prompts, rag, llm
```

`api/` validates, authenticates and streams; uploads only enqueue. Each `rag/` stage has one narrow interface (query in, ranked chunks out), so a new chunker or reranker is a one-folder change an eval can measure. `agents/tools/` is the only place an agent touches the world: each tool has a Pydantic argument schema, checks the caller's permissions and calls the same services as the API. `agents/prompts/` keeps prompts as files reviewed in pull requests, and the prompt version is logged on every trace. `llm/router.py` picks the model per task, handles timeouts and fallbacks on 429 or 5xx, and records cost. `evals/` compares each pull request with main's last run and fails on an agreed drop in retrieval recall or faithfulness.

Dependency rule: `api` calls `agents` and `rag`; agents may call retrieval as a tool, but `rag` never imports `agents`; only `llm/clients` and the embedding adapters import vendor SDKs; `evals` imports `app`, never the reverse.

**Follow-ups they will ask:**
- Why are evals outside `app`? : they carry datasets and judge costs and must not ship in the runtime image.

**Mistakes to avoid:**
- Prompts as f-strings scattered through the code, so nobody can tell which prompt produced an answer and evals cannot pin a version.

### Practice
- Build the Express tree for one resource in 30 minutes with the `app.ts` and `server.ts` split, then write a supertest test that imports `app.ts` and never opens a port.
- For a NestJS or FastAPI project you own, write one sentence per top-level folder saying what it owns; any folder that needs two sentences should be split or renamed.
- Scaffold a pnpm and Turborepo monorepo with `apps/web`, `apps/api` and `packages/types`, share one zod schema between NestJS validation and a Next.js form, and change a field to watch both fail to compile.
- Add an `only-public-api` dependency-cruiser rule (or an import-linter `independence` contract) to a two-module project, commit a deep import, and confirm CI fails.
- Say it out loud: open a repository you built and, in 60 seconds, narrate the tree top to bottom: what each folder owns, which way imports flow, and one thing you would change.
