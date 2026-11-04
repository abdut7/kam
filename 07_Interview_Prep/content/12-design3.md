## Behavioral Design Patterns [Core]

> Interviewers rarely ask you to define a behavioral pattern; they ask where you have used one and why. A weak answer recites Gang of Four definitions with shapes and animals. A strong answer points at real code: Express middleware is a chain of responsibility, EventEmitter is an observer, a BullMQ job or an LLM tool call is a command, model routing is a strategy, an order status column wants a state machine, and token streaming is an async iterator. It also says when the pattern is overkill, because in TypeScript and Python many of these shrink to a function or a map of functions. Saga orchestration and CQRS are covered in the Backend track, section "Resilience & Microservice Patterns"; this section is about the in-process building blocks.

### In plain words
Behavioral patterns are named habits for how pieces of code split up work and pass messages. Picture a restaurant kitchen. The order ticket is a Command: the request written down, so it can wait in a line, go to any cook, or be cancelled. The ticket moving from the grill to the salad station to the checker, where any station can stop it, is a Chain of Responsibility. The bell that rings when food is ready, so whichever waiter cares comes to collect it, is an Observer, and the board that shows each order as placed, cooking, ready or served, with rules about which step can come next, is a State machine. Picking a different recipe for the same dish depending on the guest is a Strategy.

### Concepts you must understand
- Most behavioral patterns answer one question: where does a varying decision live? In a swappable object (Strategy, State), in a line of handlers (Chain of Responsibility), in a queueable object (Command) or in a notification (Observer).
- TypeScript and Python have first-class functions, so many Gang of Four patterns shrink to a function, a closure or a map of functions; the class-heavy Java versions are rarely needed.
- Observer is in-process and synchronous by default (EventEmitter calls listeners in order inside `emit()`); pub/sub puts a broker between publisher and subscriber and is usually asynchronous and cross-process.
- Command turns a request into data (a name plus arguments), and that is what makes queueing, retries, audit logs, undo, approvals and LLM tool calls possible.
- Chain of Responsibility passes a request along handlers that can act, pass it on or stop it; Express middleware, NestJS guards and interceptors, and FastAPI dependencies are all chains.
- A state machine makes legal transitions explicit; the value is rejecting illegal ones and persisting state safely under concurrency, not the class per state.
- Async iterators give pull-based consumption with natural backpressure: the producer does not run ahead of a `for await` or `async for` loop.
- Every pattern costs indirection; use one when the variation is real and recurring today, not imagined for later.

| Pattern | Intent | Real example | When not to use |
| --- | --- | --- | --- |
| Strategy | Swap an algorithm behind one interface | LLM model routing per plan, pricing rules, retry policies | Two stable branches; an if statement is clearer |
| Observer | Notify in-process dependents of a change | Node EventEmitter, stream `data` events, React external stores | Work that must survive a crash; use a queue fed by an outbox |
| Command | Package a request as data | BullMQ and Celery jobs, LLM tool calls, editor undo | A plain synchronous call with no queue, audit or undo need |
| Chain of Responsibility | Pass a request along handlers until one stops it | Express middleware, NestJS guards, FastAPI `Depends` | When ordering hides business rules far from the handler |
| Template Method | Fixed skeleton, subclasses fill in steps | Ingestion job base class, `unittest.TestCase` setUp and tearDown | Many combinable variants; inheritance explodes |
| State | Behavior and allowed moves depend on current state | Order and document workflows, agent run lifecycle, XState | A single boolean flag |
| Iterator | Traverse lazily without exposing the source | Paginated APIs, Node streams, streaming LLM tokens | Small in-memory arrays where `map` and `filter` are enough |
| Mediator | Central coordinator so peers do not reference each other | NestJS CQRS command bus, chat room server, supervisor agent | Small apps; the mediator turns into a god object |
| Memento | Capture and restore state without exposing internals | Undo snapshots, agent run checkpoints | Huge state where full snapshots are too costly; store diffs or events |

### Q. What is the Strategy pattern? Show a real example.
**Short answer (45 seconds):** Strategy puts each variant of an algorithm behind one interface and lets the caller pick one at runtime, so a new variant is a new strategy, not another case in a growing switch. In TypeScript and Python that is usually an interface or Protocol plus a map from key to implementation, often just a map of functions. I use it for per-plan pricing rules, LLM model routing and per-dependency retry policies.

**Deeper explanation:**

```ts
type Route = { model: string; maxTokens: number };
interface RoutingStrategy { pick(req: ChatRequest): Route }

const cheapFirst: RoutingStrategy = {
  pick: (r) => r.tools.length === 0 && r.promptTokens < 4_000
    ? { model: cfg.models.small, maxTokens: 1_024 }
    : { model: cfg.models.large, maxTokens: 4_096 },
};
const pinned = (model: string): RoutingStrategy => ({ pick: () => ({ model, maxTokens: 4_096 }) });

const routing: Record<Plan, RoutingStrategy> = {
  free: cheapFirst,
  pro: cheapFirst,
  enterprise: pinned(cfg.models.large),   // contract: always the strong model
};
const route = routing[tenant.plan].pick(request);
```

The selecting key comes from configuration or data (tenant plan, feature flag, prompt size), and each strategy is tested alone with table-driven cases. A retry policy has the same shape, `(err, attempt) => delayMs or null`, passed to the HTTP client (the backoff rules are in the Backend track, section "Resilience & Microservice Patterns"). In NestJS you register strategies under an injection token and a factory picks one; in FastAPI you pass a callable through `Depends`.

Skip it for two stable branches that will never grow: an if statement is clearer.

**Follow-ups they will ask:**
- Strategy versus State? : the client chooses a strategy and it never swaps itself; a state object decides which state comes next.
- How do you add a fallback when the chosen model errors? : a composite strategy that tries routes in order, keeping fallback logic out of each strategy.

**Mistakes to avoid:**
- A class hierarchy per variant when a map of functions would do.
- Strategies that read globals or the caller's internals instead of taking what they need as arguments.

### Q. Observer vs pub/sub: what is the difference, and how does Node's EventEmitter fit?
**Short answer (45 seconds):** In Observer the subject keeps a list of listeners and calls them directly, in the same process, usually synchronously. In pub/sub a broker or channel sits in the middle: publishers send to a topic, subscribers receive from it, neither knows the other, and delivery is asynchronous and can cross processes (Redis pub/sub, Kafka, Google Pub/Sub). Node's EventEmitter is plain Observer: `emit()` calls every listener synchronously, in registration order, before it returns.

**Deeper explanation:**

```ts
import { EventEmitter } from "node:events";

const bus = new EventEmitter({ captureRejections: true });
bus.on("order.placed", (o: Order) => metrics.inc("orders"));        // runs inside emit()
bus.on("order.placed", async (o: Order) => { await mailer.send(o); }); // emit() does not await it
bus.on("error", (err) => log.error({ err }, "listener failed"));      // async rejections land here

bus.emit("order.placed", order);  // both listeners have started; the email is not sent yet
```

So a slow synchronous listener blocks the emitter and the event loop. A listener that throws makes `emit()` throw, and later listeners do not run. An async listener's promise is ignored, so without `captureRejections` a rejection becomes an unhandled rejection. MaxListenersExceededWarning (past 10 listeners per event) usually means listeners added per request and never removed.

Observer shows up in Node streams (`data`, `end`), `@nestjs/event-emitter` for in-process domain events, React external stores read through `useSyncExternalStore` (Zustand works this way), and Python's blinker or Django signals. Do not use it for work that must happen after a commit, like sending an invoice: a crash loses it, so use a queue fed by the transactional outbox (Backend track, section "Resilience & Microservice Patterns"). Redis pub/sub is fire-and-forget too: offline subscribers miss messages, so durable fan-out needs Redis Streams or Kafka.

**Follow-ups they will ask:**
- Does an async listener make emit async? : no; `emit()` returns a boolean straight away and never awaits listener promises.
- When does Observer become pub/sub? : when fan-out must cross processes or pods.

**Mistakes to avoid:**
- Calling EventEmitter asynchronous or a message queue.
- Hiding a critical step behind an event with one listener; a direct call is easier to trace.

### Q. What is the Command pattern, and where is it useful?
**Short answer (45 seconds):** Command turns a request into an object holding the action name and its arguments, separate from the code that executes it. As data, it can be queued, retried, logged, authorized, held for approval, or undone if it knows its inverse. BullMQ and Celery jobs are commands, an editor's undo stack is a list of commands, and an LLM tool call is a command the model emits as JSON that your code validates and dispatches.

**Deeper explanation:**

```ts
type ToolCall = { id: string; name: string; args: unknown };
type Tool = { schema: z.ZodTypeAny; run: (args: any, ctx: Ctx) => Promise<unknown>; needsApproval?: boolean };

const tools: Record<string, Tool> = {
  refund_order: { schema: RefundOrder, run: (a, ctx) => payments.refund(a, ctx.user), needsApproval: true },
};

async function dispatch(call: ToolCall, ctx: Ctx) {
  const tool = tools[call.name];
  if (!tool) return { id: call.id, error: `unknown tool ${call.name}` };
  const parsed = tool.schema.safeParse(call.args);              // model output is untrusted
  if (!parsed.success) return { id: call.id, error: parsed.error.message };
  await audit.log(ctx.runId, call);                             // data is loggable
  if (tool.needsApproval) return approvals.enqueue(call, ctx);
  return { id: call.id, result: await tool.run(parsed.data, ctx) };
}
```

Errors go back to the model as tool results, not exceptions, so it can fix its arguments. A queue job is the same shape: `queue.add("send-invoice", { orderId }, { jobId: "invoice-" + orderId })` carries a name and ids only, and since delivery is at least once the job id doubles as a deduplication key. A saga orchestrator also speaks in commands (Backend track, section "Resilience & Microservice Patterns").

Skip it for plain synchronous calls; a command class and handler per CRUD endpoint is ceremony.

**Follow-ups they will ask:**
- Command versus event? : a command asks one handler to act and may be rejected (RefundOrder); an event states a past fact (OrderRefunded).
- How does undo work? : a stack of commands with `execute()` and `undo()`.

**Mistakes to avoid:**
- Closures or class instances in queue payloads; they do not serialize.
- Executing model tool calls without an allowlist, schema validation and the user's own authorization.

### Q. What is Chain of Responsibility, and how do Express middleware and NestJS guards implement it?
**Short answer (45 seconds):** Chain of Responsibility passes a request through an ordered list of handlers; each can handle it, enrich it and pass it on, or stop the chain. Express middleware is exactly that: each `(req, res, next)` function calls `next()`, responds, or calls `next(err)` to jump to error middleware. NestJS splits the chain into typed stages in a fixed order: middleware, guards, interceptors before, pipes, the handler, interceptors after, then exception filters. A guard is a link that only answers "may this continue".

**Deeper explanation:**

```ts
// Express: registration order is the chain
app.use(requestId);
app.use(authenticate);                                   // next() or 401
app.post("/orders", rateLimit("orders"), validate(OrderSchema), createOrder);
app.use((err: HttpError, _req: Request, res: Response, _next: NextFunction) =>
  res.status(err.status ?? 500).json({ error: err.message }));

// NestJS: a guard sees which handler will run
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}
  canActivate(ctx: ExecutionContext): boolean {
    const roles = this.reflector.get<string[]>("roles", ctx.getHandler()) ?? [];
    const user = ctx.switchToHttp().getRequest().user;
    return roles.length === 0 || roles.some((r) => user?.roles.includes(r)); // false -> 403
  }
}
```

The difference that matters: Express middleware does not know which handler will run, while a NestJS guard gets an ExecutionContext and can read metadata that a custom `@Roles()` decorator attaches to the handler. Express 5 forwards rejected promises from async handlers to error middleware; Express 4 does not, so async errors need a wrapper. In FastAPI the chain is middleware plus dependencies: an auth dependency that raises HTTPException stops the request before the endpoint. LLM guardrails (PII redaction, injection classifier, moderation) are a chain too.

Skip it when ordering hides business logic, such as middleware loading domain data for a handler three files away.

**Follow-ups they will ask:**
- What if middleware neither calls next nor responds? : the request hangs until a client or server timeout.
- Where do interceptors fit? : they wrap the handler before and after (via RxJS), good for timing, caching and response mapping.

**Mistakes to avoid:**
- Registering the body parser or CORS after the routes that need them; order is behavior.
- Doing route-aware authorization in plain middleware instead of a guard.

### Q. Template Method vs Strategy: when do you choose which?
**Short answer (45 seconds):** Both vary part of an algorithm. Template Method fixes the skeleton in a base class and lets subclasses override steps, so the variation is chosen by inheritance when you pick the subclass. Strategy passes the varying part in as an object or function, so it is composition, chosen at runtime and combinable. I choose Template Method when the sequence is invariant and must be enforced and the variants are few; I choose Strategy when variants need mixing, swapping at runtime or testing alone, which is most of the time.

**Deeper explanation:**

```python
from abc import ABC, abstractmethod

class Ingestor(ABC):
    def run(self, source: str) -> int:               # the template: fixed order, shared concerns
        docs = self.load(source)
        chunks = [c for d in docs for c in self.chunk(d)]
        upsert(chunks, embed_batch([c.text for c in chunks]))
        return len(chunks)

    @abstractmethod
    def load(self, source: str) -> list[Doc]: ...

    def chunk(self, doc: Doc) -> list[Chunk]:         # hook with a default
        return split_by_tokens(doc, size=800, overlap=100)

class PdfIngestor(Ingestor):
    def load(self, source: str) -> list[Doc]:
        return parse_pdf(source)
```

This works while each source needs one loader and maybe a custom chunker. It breaks when you need PDF with Markdown-aware chunking, HTML with semantic chunking, and so on: subclasses multiply as loaders times chunkers. The Strategy version, `Pipeline(loader=PdfLoader(), chunker=MarkdownChunker())`, needs loaders plus chunkers, and each piece is tested alone. A common hybrid is a fixed template whose steps are injected strategies.

Template Method is still everywhere in frameworks, under the name "hooks": `unittest.TestCase` runs setUp, the test and tearDown; NestJS calls `onModuleInit` and `onApplicationShutdown`; React class components had lifecycle methods. The framework owns the sequence and calls you.

**Follow-ups they will ask:**
- What is a hook method? : an optional step with a default implementation that subclasses may override.
- How does Template Method go wrong? : deep hierarchies and the fragile base class problem, where a change in the base silently breaks subclasses that depended on its internals.

**Mistakes to avoid:**
- Calling them interchangeable; inheritance versus composition decides testability and runtime flexibility.
- Letting subclasses override the template method itself, which defeats the point.

### Q. How do you model an order or document workflow with the State pattern or a state machine?
**Short answer (45 seconds):** I write states and allowed transitions down as data, a table from (state, event) to next state, and route every status change through one function that rejects illegal moves (you cannot publish a rejected document). The update is a compare-and-set on the old status, so two concurrent requests cannot both win, and each change writes a history row. One class per state, the Gang of Four version, fits only when states differ in real behavior. For nested or parallel states I use XState.

**Deeper explanation:**

```ts
type Status = "draft" | "in_review" | "approved" | "rejected" | "published";
type DocEvent = "submit" | "approve" | "reject" | "revise" | "publish";

const transitions: Record<Status, Partial<Record<DocEvent, Status>>> = {
  draft: { submit: "in_review" },
  in_review: { approve: "approved", reject: "rejected" },
  rejected: { revise: "draft" },
  approved: { publish: "published" },
  published: {},
};

export async function transition(tx: Tx, id: string, from: Status, event: DocEvent) {
  const to = transitions[from][event];
  if (!to) throw new InvalidTransition(from, event);             // API maps this to 409
  const res = await tx.query(
    "UPDATE documents SET status = $1 WHERE id = $2 AND status = $3", [to, id, from]);
  if (res.rowCount === 0) throw new StaleState(id);             // lost the race
  await insertHistory(tx, id, from, to, event);
  return to;
}
```

Guards (no approving your own document) sit beside the table, side effects such as emails run after commit through an outbox, and a CHECK constraint or Postgres enum blocks writes that bypass the function.

The same model fits an agent run (queued, running, awaiting_approval, completed, failed), and a saga orchestrator is a state machine across services (Backend track, section "Resilience & Microservice Patterns"). For two states, a boolean is fine.

**Follow-ups they will ask:**
- How do you change the machine with rows in old states? : add new states first, migrate rows out of deprecated ones, remove them last.

**Mistakes to avoid:**
- Scattering `if (order.status === ...)` checks across services, so nobody can list the legal transitions.
- Read, check, then write without a conditional update; two approvers both succeed.

### Q. Where do Iterator and async iterators help in Node and Python?
**Short answer (45 seconds):** An iterator hands out items one at a time on demand and hides where they come from. An async iterator does the same when each item needs I/O, and `for await` or `async for` pulls the next item only when the consumer is ready, which gives natural backpressure. Three real uses: Node Readable streams are async iterable, so a huge file never sits in memory; an async generator turns a paginated API into one flat sequence; and LLM SDKs return async iterables of chunks that you transform and stream to the browser.

**Deeper explanation:**

```ts
async function* paginate<T>(fetchPage: (cursor?: string) => Promise<{ items: T[]; next?: string }>) {
  let cursor: string | undefined;
  do {
    const page = await fetchPage(cursor);    // runs only when the consumer wants more
    yield* page.items;
    cursor = page.next;
  } while (cursor);
}

for await (const user of paginate((c) => crm.listUsers({ cursor: c, limit: 100 }))) {
  await syncUser(user);
  if (quotaExhausted()) break;               // break calls return(): no more pages are fetched
}
```

```python
async def tokens(client: AsyncOpenAI, messages: list[dict]) -> AsyncIterator[str]:
    stream = await client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

Callers never see cursors or chunk envelopes, and generators compose by wrapping. Breaking out of a JavaScript `for await` calls `return()`, which runs `finally` blocks and destroys a Node stream. Python async generators are finalized less predictably after a break, so wrap them in `contextlib.aclosing` when cleanup matters, such as closing a paid upstream LLM stream. SSE disconnect handling is in the Backend track, section "Python & FastAPI for AI Backends".

Skip it for small in-memory arrays, and note that a sequential generator serializes I/O.

**Follow-ups they will ask:**
- Why does this give backpressure? : the code after `yield` does not run until the consumer asks for the next item.

**Mistakes to avoid:**
- Collecting the whole stream into an array first, which defeats streaming.
- Abandoning an LLM stream without aborting it, so the connection stays open and tokens may keep generating.

### Q. Mediator and Memento: what problems do they solve?
**Short answer (45 seconds):** Mediator puts a coordinator between components so they talk to it instead of to each other, turning many-to-many dependencies into many-to-one. A chat server relaying messages, a parent component or reducer coordinating dependent form fields in React, the NestJS CQRS command bus, and a supervisor agent routing work between specialist agents are all mediators. Memento captures an object's state as an opaque snapshot so it can be restored later without exposing internals: undo history, draft autosave, and agent run checkpoints so a crashed or paused run can resume.

**Deeper explanation:**

```ts
// Mediator: the controller knows only the bus; @nestjs/cqrs routes to the one handler
await this.commandBus.execute(new PlaceOrderCommand(userId, items));

// Memento: an opaque snapshot of agent run state, stored by a caretaker
type Checkpoint = { readonly runId: string; readonly step: number; readonly state: unknown };

class AgentRun {
  constructor(readonly runId: string, private step = 0, private messages: Message[] = []) {}
  checkpoint(): Checkpoint {
    return { runId: this.runId, step: this.step, state: structuredClone(this.messages) };
  }
  static restore(c: Checkpoint) {
    return new AgentRun(c.runId, c.step, structuredClone(c.state) as Message[]);
  }
}

await checkpoints.save(run.checkpoint());                      // after every tool step
const resumed = AgentRun.restore(await checkpoints.latest(runId));
```

A mediator can grow into a god object, so keep it a router, not business logic; it also hides the call graph, so small apps are clearer with direct calls. CQRS itself is in the Backend track, section "Resilience & Microservice Patterns".

A memento costs memory and copy time, and must be a deep copy or later changes leak into it. For large state, store diffs (Immer's inverse patches) or an event log, which is event sourcing. LangGraph checkpointers save graph state per thread, so a run resumes after approval. A resumed agent must not repeat side-effecting tool calls, so record completed tool results in the checkpoint and keep tools idempotent.

**Follow-ups they will ask:**
- Mediator versus Observer? : an observer subject broadcasts to whoever subscribed; a mediator knows the participants and decides who gets what.

**Mistakes to avoid:**
- Shallow-copied snapshots.
- A mediator in a small codebase: indirection that decouples nothing.

### Practice
- Build an LLM router with three strategies (cheap-first, pinned, fallback-on-error) behind one interface, with table-driven tests for each strategy and for the selector.
- Write the same API in Express and NestJS: five middleware in Express, then a guard, an interceptor and a pipe in NestJS that log as they run; confirm the order, then remove one `next()` and watch the request hang.
- Model a document approval flow as a transition table with a Postgres compare-and-set update; fire two concurrent approve requests and confirm one gets 409.
- Wrap a paginated API and an LLM stream in async generators; break after N items and verify no extra pages are fetched and the upstream stream is closed.
- Say it out loud: for three patterns from this section, name the place in your last codebase where each appeared and one place where it would have been overkill.

## Backend and Enterprise Patterns [Advanced]

> These questions test whether you can structure a codebase that survives years of change and many engineers. A weak answer says "we use controllers, services and repositories because that is clean architecture" and draws boxes. A strong answer explains what each layer isolates (the API contract, the transaction boundary, the business rules, the storage), what it costs, and when to collapse it, such as dropping a repository that only forwards calls to Prisma. Expect follow-ups about real tools: Prisma interactive transactions, SQLAlchemy sessions, NestJS providers and scopes. Sagas, the transactional outbox and CQRS are covered in the Backend track, section "Resilience & Microservice Patterns"; this section links to them rather than repeating them.

### In plain words
Think of the business side of a restaurant. The waiter takes orders in the customer's own words and hands back the bill in a fixed format (the API and its DTOs). The head chef decides how each dish is made and enforces the kitchen's rules (the service and domain layer), and the storeroom keeper fetches ingredients without the chef caring which shelf they sit on (the repository). Nobody hires their own helpers; the manager decides who works with whom (dependency injection). The kitchen and the accounts office each have their own words for things, and "a table" means something different to each, which is fine as long as they translate at the door (bounded contexts).

### Concepts you must understand
- Layers exist to put each kind of change in one place; a layer that isolates nothing that actually changes or needs testing is pure cost.
- A repository gives the domain a collection-like interface for aggregates and hides persistence; over an ORM it pays off only when it adds domain vocabulary, scoping rules, aggregate loading or a useful test seam.
- Unit of Work tracks the changes of one business operation and commits them in one transaction; ORM sessions are implementations of it, and the transaction boundary belongs to the use case, not to each repository.
- DTOs are the API contract, domain objects hold rules, persistence models match tables; mapping between them stops a column rename from breaking clients and blocks mass assignment.
- Dependency injection means a class receives its collaborators instead of building them; an IoC container automates the wiring and lifetimes, and NestJS adds modules with explicit imports and exports.
- In DDD an aggregate is the consistency boundary: one transaction changes one aggregate, other aggregates are referenced by id and updated through domain events.
- Bounded contexts decide where module and service boundaries go; the same word can mean different things in different contexts, and translation happens at the edge.
- Most backend anti-patterns are patterns applied by default instead of by need, or rules duplicated because there was no obvious home for them.

| Pattern | Node / NestJS | Python / FastAPI |
| --- | --- | --- |
| Repository | class over Prisma, TypeORM `Repository<T>` | class wrapping a SQLAlchemy `Session` |
| Unit of Work | `prisma.$transaction(async (tx) => ...)`, TypeORM `EntityManager` | SQLAlchemy `Session` with `session.begin()` |
| DTO | class-validator classes with `ValidationPipe`, or zod | Pydantic models with `response_model` |
| Dependency injection | NestJS modules and providers | `Depends`, singletons built in lifespan |

### Q. What is the Repository pattern, and when is it a useless layer over an ORM?
**Short answer (45 seconds):** A repository gives the domain a collection-like interface for loading and saving aggregates, such as `orders.byId(id)` and `orders.save(order)`, and hides how persistence works. It earns its place when it speaks domain language, loads full aggregates, scopes by tenant in one place, or gives a seam for test fakes. A generic repository that re-exposes `findMany`, `update` and `delete` one-to-one over Prisma or SQLAlchemy is useless: the ORM already is a repository and unit of work, and the wrapper hides includes, transactions and query composition.

**Deeper explanation:**

```ts
// Useless: a pass-through that hides nothing and loses the Prisma API
class UserRepository { findMany(args: Prisma.UserFindManyArgs) { return prisma.user.findMany(args); } }

// Useful: domain vocabulary, tenant scoping and aggregate shape in one place
class OrderRepository {
  constructor(private db: PrismaClient | Prisma.TransactionClient, private tenantId: string) {}

  async byId(id: string): Promise<Order | null> {
    const row = await this.db.order.findFirst({ where: { id, tenantId: this.tenantId }, include: { lines: true } });
    return row ? Order.fromRow(row) : null;
  }
  // save(order), overdue(now): named for the domain, always tenant-scoped
}
```

The constructor accepts the client or a transaction client, so the use case owns the transaction and the repository joins it (next question). One repository per aggregate root, not per table: order lines are saved through the order. Reporting queries can skip repositories for a query service with raw SQL or views. In FastAPI the repository takes the request's Session.

Mock repositories when unit testing domain logic, but test the repository itself against real Postgres (Testcontainers); a mock cannot catch a wrong where clause. For a CRUD admin or a prototype, call the ORM from the service and skip the layer.

**Follow-ups they will ask:**
- Return ORM rows or domain objects? : domain objects when there is a real domain model; for plain CRUD the repository is probably optional.
- Should a repository commit? : no; it joins the caller's transaction.

**Mistakes to avoid:**
- "We can switch databases later"; nobody swaps Postgres for MongoDB behind an unchanged interface.
- A generic `BaseRepository<T>` that adds a layer and removes ORM features.

### Q. What is Unit of Work, and how do Prisma, TypeORM and SQLAlchemy sessions implement it?
**Short answer (45 seconds):** Unit of Work tracks every change made during one business operation and writes them in a single transaction, so it is all or nothing and every repository shares one connection. The boundary is the use case, not the repository. SQLAlchemy's Session is a full unit of work with an identity map and change tracking: you modify objects and commit flushes the inserts and updates in dependency order. TypeORM gives you an EntityManager inside `dataSource.transaction()`. Prisma has no change tracking, only transactions, so you pass the transaction client to every repository.

**Deeper explanation:**

```python
def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session

@app.post("/orders")
def place_order(cmd: PlaceOrderIn, session: Session = Depends(get_session)):
    with session.begin():                          # one transaction per use case
        order = Order(user_id=cmd.user_id, status="PLACED")
        session.add(order)
        for line in cmd.lines:
            stock = session.get(Stock, line.sku, with_for_update=True)
            stock.reserved += line.qty             # tracked; no UPDATE call
        session.add(OutboxEvent(type="OrderPlaced", payload={"user_id": cmd.user_id}))
    return {"id": order.id}                        # committed on block exit
```

The identity map returns the same object when a row is loaded twice in one session, so code paths cannot hold conflicting copies. In Prisma the use case runs `prisma.$transaction(async (tx) => ...)` and passes `tx` to each repository; interactive transactions hold a connection throughout and time out after 5 seconds by default. NestJS teams often keep `tx` in AsyncLocalStorage (nestjs-cls has a transactional plugin) instead of threading it through calls. The outbox row is one more insert in the same unit of work (Backend track, section "Resilience & Microservice Patterns").

The AI-specific trap: never call an LLM or external API inside the transaction. Holding locks and a pool connection through a ten-second model call exhausts the pool under load; call the model first, then write in a short transaction.

**Follow-ups they will ask:**
- Why not let each repository commit? : a use case touching two repositories can then half-succeed.
- Flush versus commit in SQLAlchemy? : flush sends pending SQL inside the open transaction; commit ends it.

**Mistakes to avoid:**
- Network calls inside an open transaction.
- One session shared across requests; sessions are per request or per job.

### Q. Service layer, DTOs and mappers: why separate API shapes from domain and database shapes?
**Short answer (45 seconds):** The three shapes change for different reasons: the API contract when clients need it, and it must stay backward compatible; the domain model with business rules; the schema for performance and migrations. DTOs at the edge, a service layer implementing use cases, and mappers between them mean a column rename does not break the mobile app, password hashes or cost prices never leak, and clients cannot mass-assign fields like `role`. The service layer owns the transaction boundary, so controllers, queue workers and agent tools call the same use case.

**Deeper explanation:**

```ts
export class CreateUserDto {                    // what clients may send
  @IsEmail() email!: string;
  @IsString() @Length(1, 80) name!: string;
}
export class UserResponseDto {                  // what clients see
  id!: string; email!: string; name!: string; createdAt!: string;
}
export const toUserResponse = (u: User): UserResponseDto =>
  ({ id: u.id, email: u.email, name: u.name, createdAt: u.createdAt.toISOString() });

@Post()
async create(@Body() dto: CreateUserDto): Promise<UserResponseDto> {
  return toUserResponse(await this.users.register(dto.email, dto.name));
}
```

With `new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })`, undecorated properties are stripped or rejected, which closes mass assignment. FastAPI does the same with separate `UserCreate` and `UserOut` Pydantic models: `response_model=UserOut` filters output, and `UserOut.model_validate(row)` with `from_attributes=True` maps from an ORM object. 
LLM tools are DTOs for the model: a refund tool accepts `{ orderId, reason }`, not an Order entity, and its results are mapped to compact shapes, saving tokens and keeping internal fields out of the context.

Skip the ceremony where all three shapes are honestly identical, like an internal admin CRUD screen; hand-written mappers copying thirty fields are cost, so use `Pick`, `Omit` or generated types and accept the coupling deliberately.

**Follow-ups they will ask:**
- Where does validation live? : shape and type checks in the DTO at the edge, business rules (unique email, credit limit) in the service or domain.
- Should services return DTOs? : no; they return domain objects or results and each transport maps them.

**Mistakes to avoid:**
- `res.json(user)` with an ORM entity, leaking hashes and coupling clients to the schema.
- `prisma.user.update({ data: req.body })`, a mass assignment hole.

### Q. How do dependency injection and IoC containers work, and what does NestJS add over manual wiring?
**Short answer (45 seconds):** Dependency injection means a class receives its collaborators, usually through the constructor, instead of creating them, so you can swap implementations and pass fakes in tests. Inversion of control is the wider idea that the framework constructs objects and calls your code. A container automates the wiring: you register providers, it builds the dependency graph, resolves constructor parameters and manages lifetimes. In Express you wire by hand in one composition root. NestJS adds a container that reads constructor parameter types from TypeScript decorator metadata, modules with explicit imports and exports, scopes, custom providers and test overrides.

**Deeper explanation:**

```ts
// Express: manual wiring in one composition root
const pool = new Pool({ connectionString: env.DATABASE_URL });
const orders = new OrderService(new OrderRepository(pool), new StripeGateway(env.STRIPE_KEY));
app.use("/orders", ordersRouter(orders));

// NestJS: the container builds the same graph from providers
@Module({
  providers: [OrderService, OrderRepository, {
    provide: PAYMENT_GATEWAY,
    useFactory: (cfg: ConfigService) => new StripeGateway(cfg.getOrThrow("STRIPE_KEY")),
    inject: [ConfigService],
  }],
  exports: [OrderService],
})
export class OrdersModule {}

@Injectable()
export class OrderService {
  constructor(private repo: OrderRepository, @Inject(PAYMENT_GATEWAY) private payments: PaymentGateway) {}
}
```

TypeScript interfaces are erased at compile time, so there is no runtime type to inject by; that is why `PaymentGateway` needs a token (a symbol or string) and `@Inject`, or an abstract class. Providers are singletons by default. A request-scoped provider makes everything that depends on it request-scoped too, which has a performance cost, so for "current user" or tenant context many teams use AsyncLocalStorage instead. Tests swap providers with `Test.createTestingModule({ imports: [OrdersModule] }).overrideProvider(PAYMENT_GATEWAY).useValue(fake).compile()`.

FastAPI's `Depends` is per-request function injection, cached within one request, with `app.dependency_overrides` for tests; long-lived clients (DB engine, LLM client) are created in lifespan.

Manual wiring is fine for a small Express service or a Lambda: explicit, greppable, no decorator metadata.

**Follow-ups they will ask:**
- What does `forwardRef()` tell you? : there is a circular dependency between providers or modules, which is usually a design smell.

**Mistakes to avoid:**
- Saying DI needs a framework; a constructor parameter is DI.
- Calling the container from business code to fetch dependencies, which is a service locator.

### Q. Explain domain-driven design basics: entities, value objects, aggregates, bounded contexts and domain events.
**Short answer (45 seconds):** An entity has an identity that survives change: order 42 stays order 42 when its status changes. A value object is defined only by its attributes and is immutable, like Money or an EmailAddress; you replace it rather than edit it. An aggregate is a cluster with one root that guards invariants and bounds the transaction: order lines change only through the Order. A bounded context is where one model and vocabulary hold: "customer" means different things in Billing and Support. A domain event such as OrderPlaced records a fact others react to.

**Deeper explanation:**

```ts
class Money {                                       // value object
  constructor(readonly cents: number, readonly currency: "INR" | "AED") {
    if (!Number.isInteger(cents) || cents < 0) throw new Error("invalid amount");
  }
}

class Order {                                       // aggregate root
  private lines: OrderLine[] = [];
  readonly events: DomainEvent[] = [];
  constructor(readonly id: string, private status: "DRAFT" | "PLACED" = "DRAFT") {}

  addLine(sku: string, qty: number, price: Money) {
    if (this.status !== "DRAFT") throw new Error("order is locked");   // invariant
    this.lines.push(new OrderLine(sku, qty, price));
  }
  place() {
    if (this.lines.length === 0) throw new Error("empty order");
    this.status = "PLACED";
    this.events.push({ type: "OrderPlaced", orderId: this.id });
  }
}
```

Rules of thumb: keep aggregates small, reference others by id, change one aggregate per transaction, and update the rest eventually through domain events, dispatched after commit and sent across services through the outbox (Backend track, section "Resilience & Microservice Patterns"). Bounded contexts become modules in a modular monolith, or services, with an anti-corruption layer translating between them.

For agents: tools should call `order.cancel()`, not update tables, so invariants hold whoever triggers the change. Tactical DDD is ceremony for CRUD-heavy domains.

**Follow-ups they will ask:**
- How big should an aggregate be? : as small as the invariant allows; a Customer holding all their orders means contention.
- Domain event versus integration event? : domain events stay inside a context; integration events are a published, versioned contract.

**Mistakes to avoid:**
- DDD as folder names while every rule lives in services.
- Primitive obsession: raw numbers for money, so floats creep into prices.

### Q. What is the Specification pattern, and when is it worth it?
**Short answer (45 seconds):** A specification is a business rule packaged as a combinable object: `isSatisfiedBy(candidate)` checks one object in memory, and often a second method turns the rule into a query for the database. They combine with and, or and not. It is worth it when one rule, such as "eligible for refund", is used in several places (an API check, a nightly job, an agent tool) and must stay identical, or when users build filters dynamically. For a one-off filter, a where clause or a named repository method is simpler.

**Deeper explanation:**

```ts
type OrderSpec = { isSatisfiedBy(o: Order): boolean; toWhere(): Prisma.OrderWhereInput };

const and = (...specs: OrderSpec[]): OrderSpec => ({
  isSatisfiedBy: (o) => specs.every((s) => s.isSatisfiedBy(o)),
  toWhere: () => ({ AND: specs.map((s) => s.toWhere()) }),
});
const delivered: OrderSpec = {
  isSatisfiedBy: (o) => o.status === "DELIVERED",
  toWhere: () => ({ status: "DELIVERED" }),
};
const deliveredSince = (since: Date): OrderSpec => ({
  isSatisfiedBy: (o) => o.deliveredAt !== null && o.deliveredAt.getTime() >= since.getTime(),
  toWhere: () => ({ deliveredAt: { gte: since } }),
});

export const refundEligible = (now: Date) =>
  and(delivered, deliveredSince(new Date(now.getTime() - 30 * 86_400_000)));
// API check and agent tool: refundEligible(now).isSatisfiedBy(order)
// nightly job: prisma.order.findMany({ where: refundEligible(now).toWhere() })
```

The agent case is the strongest argument: the refund tool checks the same `refundEligible` as the API, so the model cannot talk its way past policy. In Python, SQLAlchemy expressions already compose, so a function returning `and_(Order.status == "DELIVERED", Order.delivered_at >= since)` is a specification. A React filter builder can send a JSON spec tree that the backend parses against an allowlist.

The risk is the two forms drifting on nulls or time zones; run the same fixtures through both and compare the ids.

**Follow-ups they will ask:**
- Specification versus Strategy? : a specification answers yes or no and composes with boolean logic; a strategy performs one variant of an algorithm.
- Can `isSatisfiedBy` load data? : avoid it; that causes N+1 queries.

**Mistakes to avoid:**
- A generic specification framework for one rule.
- Raw user-supplied field names in queries.

### Q. Which anti-patterns do you watch for in a backend codebase?
**Short answer (45 seconds):** I look for six, each named by a symptom I can point to: a god object everything depends on, an anemic domain model with rules spread across services, a service locator hiding real dependencies, leaky abstractions that expose the ORM or vendor through an interface meant to hide them, circular module dependencies, and shotgun surgery, where one business change edits many files. The fix is usually moving behavior to where data and change live, not adding a layer.

**Deeper explanation:**

| Anti-pattern | Symptom | Typical fix |
| --- | --- | --- |
| God object | `OrderService` with thousands of lines, twenty dependencies | Split by use case |
| Anemic domain model | Tax rule copied into checkout, invoices and an agent tool | Move invariants into aggregates |
| Service locator | `moduleRef.get()` inside business code | Constructor injection |
| Leaky abstraction | Callers catch Prisma's `P2002` | Translate errors at the boundary |
| Circular dependencies | `forwardRef()`, `undefined` CommonJS imports, Python "partially initialized module" | Extract shared code or use an event |
| Shotgun surgery | One rule change edits ten files | Give the rule one home |

An anemic model is honest for CRUD; it hurts once rules get duplicated. A service locator is fine in a composition root or a plugin system resolving handlers by name. In AI code, an "AgentService" owning tools, memory, routing, prompts and billing is a god object, and prompt text pasted into five services is shotgun surgery.

Make checks mechanical: `madge --circular src` or dependency-cruiser in JavaScript, import-linter in Python, failing CI. Files that always change together in git history reveal shotgun surgery.

**Follow-ups they will ask:**
- How do you break up a god service without a rewrite? : characterization tests first, then extract one use case at a time behind the same public methods.

**Mistakes to avoid:**
- Naming anti-patterns without symptoms and fixes.
- Answering every smell with another abstraction layer.

### Practice
- Take a NestJS or FastAPI service, delete one pass-through repository, and keep one aggregate repository with tenant scoping; compare the test effort before and after.
- Implement place-order with a Prisma interactive transaction or SQLAlchemy `session.begin()` that writes the order and an outbox row; kill the process mid-way and confirm nothing is half-written.
- Run `madge --circular` or import-linter on a real repository and fix one cycle by extracting a shared module or replacing a call with a domain event.
- Write Money and DateRange value objects with tests, plus a `refundEligible` specification used by both an API endpoint and an agent tool, with one fixture test covering both its forms.
- Say it out loud: walk through the layers a request passes in your last service, what each one isolates, and which one you would delete if you had to.
