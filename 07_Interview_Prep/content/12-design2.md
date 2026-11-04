## Creational Design Patterns [Core]

> Creational patterns answer one question: who builds an object, when, and how many of them exist. Senior interviewers rarely want the textbook UML; they want to hear where the pattern already lives in your stack (module caching, NestJS providers, FastAPI `Depends`, `pg.Pool`, an LLM client factory) and when you would refuse to use it. A weak answer recites "Singleton ensures one instance". A strong answer separates lifetime from global access, names the concurrency and testing failure modes, and shows how a DI container makes most hand-written creational code unnecessary.

### In plain words
Creational patterns are rules for making things. Think of a restaurant kitchen: there is one big oven everyone shares (Singleton), a head chef who decides which cook makes a dish based on the order (Factory), and an order form you fill in line by line before cooking starts (Builder). Some dishes start from a ready-made sample plate that you copy instead of starting from zero (Prototype). The kitchen keeps a stack of clean pans so nobody buys a new pan for every order (Object Pool). Dependency injection is the kitchen manager who hands each cook the tools they need, so cooks never go shopping themselves.

### Concepts you must understand
- Creational patterns separate using an object from deciding which concrete class to build, how to configure it, and how long it lives.
- Singleton mixes two ideas: a lifetime (one instance per process), which is often right, and a global access point (`getInstance()`), which is usually wrong.
- In Node, a module body runs once per process and its exports are cached, so `export const pool = new Pool()` is already a singleton; Python's `sys.modules` does the same.
- "One per process" is not "one per system": cluster workers, PM2 instances, Uvicorn workers and pods each hold their own copy, so shared state must live in Redis or the database.
- Factory Method hides which class is built for one product; Abstract Factory builds a family of products that must match each other, such as a chat model, an embedder and a tokenizer.
- Builder is for step-by-step or conditional construction; in TypeScript and Python, a typed options object or keyword arguments replace most builders.
- Prototype means "create by copying a configured instance"; JavaScript's prototype chain is delegation, not copying, and only shares the name.
- A DI container is a generic factory plus a lifetime manager: NestJS providers (`useClass`, `useFactory`, `useValue`) and FastAPI `Depends` are where most creational logic should live.
- Pooling pays only when creation is expensive and the resource is bounded (database connections, TLS sockets, worker threads); pooling plain objects in a garbage-collected runtime usually hurts.

| Pattern | Intent in one line | Real example in Node, NestJS, FastAPI or LLM apps | When not to use |
|---|---|---|---|
| Singleton | One instance per process with a known access point | A module-level `pg.Pool` or `OpenAI` client; a default-scope NestJS provider; `@lru_cache` on FastAPI `get_settings()` | Anything holding per-request or per-user state; anything tests must replace |
| Factory Method | Hide which concrete class is created behind one creation call | `createChatModel(cfg)` returning an OpenAI, Anthropic or vLLM-backed `ChatModel` | One implementation and no second planned; a plain `new` is clearer |
| Abstract Factory | Create a family of related objects that must be used together | An `AiKit` returning a matching chat model, embedder and tokenizer; S3 vs local-disk storage plus URL signer | Products that never need to match; separate factory functions are enough |
| Builder | Assemble a complex object step by step, often conditionally | Knex query chains, Supertest request chains, a prompt builder with a token budget, test data builders | A few fields with no ordering or validation rules; use an options object or keyword arguments |
| Prototype | Create new objects by copying a configured instance | Cloning a base LLM request template or agent state with `structuredClone` or Pydantic `model_copy` | Objects holding sockets, clients or functions; a factory returning a fresh object is safer |
| Object Pool | Reuse a bounded set of expensive objects | `pg.Pool`, SQLAlchemy `QueuePool`, Piscina worker pools, keep-alive HTTP agents | Cheap objects; serverless fan-out where every instance's pool multiplies database connections |
| Dependency injection (related technique) | A container builds dependencies and hands them over | NestJS `useFactory` providers; FastAPI `Depends` with `dependency_overrides` in tests | Small scripts, CLIs and one-file Lambdas where a container is pure ceremony |

### Q. What is the Singleton pattern, and why is it often an anti-pattern? How do Node modules and NestJS providers give you singletons?
**Short answer (45 seconds):** Singleton guarantees one instance of a class plus a global way to reach it. One instance is often right: a database pool or an LLM client should be built once per process. The anti-pattern is the global access: callers reach for `X.getInstance()`, so the dependency is hidden, state is shared across requests, and tests cannot swap it. Node modules and NestJS providers give you the single lifetime without the global.

**Deeper explanation:** Node caches a CommonJS module by resolved filename and an ES module by URL, so the module body runs once and every importer shares its exports. Two copies of a package in `node_modules`, or one package loaded as both CommonJS and ESM (the "dual package hazard"), give you two "singletons".

```ts
// llm.ts: runs once per process; it also throws at import time if OPENAI_API_KEY is missing
export const openai = new OpenAI();

@Injectable() // default scope: one instance shared by every request
export class ChatService {
  private currentUserId?: string; // BUG: concurrent requests overwrite each other
}
```

NestJS creates a default-scope provider once per module that lists it in `providers`; listing the same class in two modules gives two instances, so export it from one module. `Scope.REQUEST` builds one per request and bubbles up to every consumer, at a performance cost. In FastAPI, `@lru_cache` on `get_settings()` and clients built in `lifespan` are the idiomatic singletons.

When not to use one: anything holding per-user or per-request data, and anything tests must configure differently.

**Follow-ups they will ask:**
- Is a singleton shared across cluster workers or Uvicorn workers?: No, each process has its own, so in-memory caches and rate limiters need Redis for a global view.
- How do you test code that uses a shared client?: Inject it, then replace it with `overrideProvider(...).useValue(fake)` in Nest or `app.dependency_overrides` in FastAPI.

**Mistakes to avoid:**
- Storing request data such as the current user on a default-scope provider; under concurrency it leaks between users.
- Connecting at import time, which breaks tests; connect in `onModuleInit` or `lifespan`.

### Q. Factory Method vs Abstract Factory: what is the difference? Show a real example.
**Short answer (45 seconds):** Factory Method hides which concrete class is created for one product: the caller asks for a `ChatModel` and gets an OpenAI, Anthropic or vLLM implementation. Abstract Factory creates a family of related products that must be used together, such as a chat model, embedder and tokenizer from one provider. Use the first when one choice varies, the second when several must stay consistent.

**Deeper explanation:** Strictly, GoF Factory Method is an overridable method (`abstract createModel()` in a base class); in TypeScript and Python it is usually a function or registry, a "simple factory". Name the distinction.

```ts
interface ChatModel { chat(messages: Msg[]): Promise<string> }

const makers: Record<Provider, (c: LlmConfig) => ChatModel> = {
  openai: (c) => new OpenAIChat(new OpenAI({ apiKey: c.apiKey }), c.model),
  anthropic: (c) => new AnthropicChat(new Anthropic({ apiKey: c.apiKey }), c.model),
  // vLLM is OpenAI-compatible: same adapter, different baseURL
  vllm: (c) => new OpenAIChat(new OpenAI({ baseURL: c.baseUrl, apiKey: c.apiKey ?? 'EMPTY' }), c.model),
};
export const createChatModel = (c: LlmConfig): ChatModel => makers[c.provider](c);

interface AiKit { chat(): ChatModel; embedder(): Embedder; tokenizer(): Tokenizer }
```

The family matters in RAG: documents indexed with one embedding model must be queried with that model, and token counts must match the chat model, so one `AiKit` per provider makes a mismatched set impossible. Storage fits too: a `StorageKit` pairs an S3 store with a presigned-URL signer, or local disk with a local signer.

When not to use them: with one provider and no concrete plan for a second, the factory is speculative indirection; if the products never need to match, separate factory functions beat a kit.

**Follow-ups they will ask:**
- How do you add a provider without editing a switch?: Add a registry entry; callers do not change.
- Where does the factory run in NestJS?: In a `useFactory` provider, so config is validated once at startup and services inject only the interface.

**Mistakes to avoid:**
- Calling any function that returns `new X()` an Abstract Factory; the defining trait is a family that must match.
- Leaking SDK types such as `ChatCompletion` through the interface.

### Q. When do you use the Builder pattern?
**Short answer (45 seconds):** Use a Builder when an object is assembled in steps, some steps are conditional, and the result should be validated once at the end. Knex query chains, Supertest chains (`request(app).post('/x').set(...).send(body).expect(201)`) and test data builders are everyday examples; in LLM apps, a prompt builder that fits system text, retrieved context and history into a token budget fits well. For a handful of fields, a typed options object or Python keyword arguments is simpler.

**Deeper explanation:** Knex is a fluent builder: each call adds to an internal query description, and nothing runs until you `await` it, because the builder is thenable. Conditional filters become natural:

```ts
const q = knex('documents').select('id', 'title').where({ tenant_id: tenantId });
if (search) q.where('title', 'ilike', `%${search}%`);
if (from) q.where('created_at', '>=', from);
const rows = await q.orderBy('created_at', 'desc').limit(20);
```

Prisma takes the other route: `prisma.document.findMany({ where, orderBy, take })` is a typed options object checked as a whole at compile time. That is the core trade-off. A fluent builder handles conditional assembly and can enforce rules in `build()`; an options object is shorter, easy to log and serialize, and type-checked with no extra class.

Test data builders (`aUser().withRole('admin').build()`) supply valid defaults so each test states only what matters; in Python, factory_boy plays that role. A `PromptBuilder` earns its place when `build(maxTokens)` must drop the oldest history turns before trimming retrieved chunks.

When not to use it: when a constructor or options object with a few optional fields would do; a builder there is ceremony and hides required fields the type system could enforce.

**Follow-ups they will ask:**
- Can a builder enforce required steps?: Yes, a step builder returns a new type after each required call, so `build()` only exists once they are set.
- Is Knex safe from SQL injection?: Values passed to its methods are bound as parameters; `knex.raw` with string concatenation is not.

**Mistakes to avoid:**
- Writing a builder for a three-field DTO that a Pydantic model or TypeScript interface describes better.
- Sharing one mutable query builder across requests, so filters accumulate; build a fresh one or call `.clone()`.

### Q. What is the Prototype pattern, and where does it appear in JavaScript?
**Short answer (45 seconds):** The Prototype pattern creates new objects by copying an already configured instance instead of building from scratch. JavaScript's prototype chain is a different mechanism with the same name: objects delegate property lookups to a shared prototype, and nothing is copied. In practice the pattern shows up as cloning templates, such as a base LLM request config or a default agent state, with `structuredClone` in Node or `model_copy` in Pydantic.

**Deeper explanation:** `Object.create(proto)` links a new object to `proto`, so later changes to `proto` show through every linked object: delegation, not copying. The pattern needs a real copy, and copy depth is where bugs live:

```ts
const base = Object.freeze({ model: 'gpt-4o-mini', temperature: 0, metadata: { app: 'support' } });

const a = { ...base };       // shallow: a.metadata is the same object as base.metadata
a.metadata.app = 'billing';  // mutates the template: freeze is shallow

const b = structuredClone(base); // deep copy, safe to change
b.metadata.app = 'billing';
```

`structuredClone` (global since Node 17) copies nested objects, `Date`, `Map`, `Set` and cycles, but throws on functions and returns class instances as plain objects. Tool definitions often carry handler functions, so clone the data part (name, description, JSON schema) and keep handlers in a registry. In Python, `copy.deepcopy` or `model_copy(update={...}, deep=True)` does the job; `model_copy` does not validate the `update` values. Forking an agent run from a saved checkpoint is the same idea: copy the state, then continue.

When not to use it: objects that own resources (clients, sockets, streams). Often a factory such as `makeDefaultRequest()` is clearer than copying a template.

**Follow-ups they will ask:**
- Why not `JSON.parse(JSON.stringify(x))`?: It turns `Date` into a string and `Map` into `{}`, drops `undefined`, and throws on cycles.
- How does React relate?: State updates copy only the changed path and share the rest: structural sharing, not a deep clone.

**Mistakes to avoid:**
- Saying the prototype chain "is" the Prototype pattern; it shares the name, not the mechanism.
- Deep-cloning large objects per request when a frozen template plus a small override would do.

### Q. How does dependency injection relate to creational patterns?
**Short answer (45 seconds):** Dependency injection moves the creational decision out of the class: the class declares what it needs, and a container or composition root builds it and passes it in. The container is one big configurable factory plus a lifetime manager (one instance, one per request, or one per consumer). In NestJS that is `useClass`, `useFactory` and `useValue` providers; in FastAPI it is `Depends`, with app-wide objects built in `lifespan`.

**Deeper explanation:** Each provider is a recipe. `useFactory` is a factory whose arguments the container resolves; it may be `async`, and Nest resolves it before creating anything that depends on it. `useClass` picks an implementation, `useValue` supplies a constant or a mock.

```ts
export const CHAT_MODEL = Symbol('CHAT_MODEL'); // interfaces vanish at runtime, so use a token
@Module({
  providers: [
    { provide: CHAT_MODEL, inject: [ConfigService],
      useFactory: (cfg: ConfigService) => createChatModel(cfg.getOrThrow('llm')) },
    { provide: BlobStore, useClass: process.env.STORAGE === 's3' ? S3BlobStore : DiskBlobStore },
  ],
  exports: [CHAT_MODEL, BlobStore],
})
export class AiModule {}
```

```python
def get_llm(request: Request) -> ChatModel:
    return request.app.state.llm           # built once in lifespan

async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:  # one per request, closed afterwards
        yield session

@app.post("/ask")
async def ask(q: Question, llm: Annotated[ChatModel, Depends(get_llm)],
              db: Annotated[AsyncSession, Depends(get_db)]): ...
```

FastAPI calls each dependency once per request and caches the result for that request; tests swap a factory with `app.dependency_overrides[get_llm] = lambda: FakeLLM()`.

When not to use a container: scripts, CLIs and one-file Lambdas, where passing arguments by hand is the whole composition root.

**Follow-ups they will ask:**
- DI vs service locator?: With DI the class receives its dependencies; with a locator it asks a global registry, which hides them like a singleton does.
- Why can a request-scoped provider slow Nest down?: Scope bubbles up, so every consumer in the chain is rebuilt per request.

**Mistakes to avoid:**
- An interface and token for every class with one implementation; inject the concrete class until a second exists.
- Injecting the container itself into services.

### Q. Object pool: when is pooling worth it?
**Short answer (45 seconds):** Pool when creating an object is expensive, the resource is capped on the other side, and you reuse it constantly. Database connections are the textbook case: a Postgres connection costs a TCP and TLS handshake, authentication and a new server process, and the server caps connections. Worker pools and keep-alive HTTP agents follow the same logic; pooling cheap in-memory objects in Node or Python is usually slower than letting the garbage collector work.

**Deeper explanation:** `pg.Pool` (default `max` 10), SQLAlchemy's `QueuePool` (`pool_size=5`, `max_overflow=10` by default) and the MongoDB driver (`maxPoolSize` 100) lend connections and queue callers when none are free. The classic bugs are leaks (a client never released) and dirty state (an open transaction or session `SET` passed to the next borrower):

```ts
export const pool = new Pool({ max: 10, idleTimeoutMillis: 30_000, connectionTimeoutMillis: 2_000 });

export async function withTx<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release(); // always, or the pool drains
  }
}
```

Size against the database: instances times workers times pool size must stay under Postgres `max_connections`, which is why autoscaled and serverless fleets put PgBouncer or RDS Proxy in front. Piscina keeps worker threads warm for CPU work, and libuv's own pool (default 4, `UV_THREADPOOL_SIZE`) runs `fs`, `dns.lookup` and `crypto.pbkdf2`. Node's `fetch` (undici) and `httpx.AsyncClient` pool keep-alive connections, so create one OpenAI or httpx client per process, not per call.

**Follow-ups they will ask:**
- Bigger pool, faster app?: No; past the database's CPU and I/O capacity, extra connections add contention and the queue moves into Postgres.
- What does PgBouncer transaction mode break?: Session state such as `SET`, `LISTEN` and session-level advisory locks.

**Mistakes to avoid:**
- Pooling plain objects to "help the GC" without a profile showing allocation is the bottleneck.
- A new HTTP client per LLM call, which throws away every reusable TLS connection.

### Practice
- Build a NestJS `AiModule` whose `useFactory` provider returns an OpenAI, Anthropic or vLLM-backed `ChatModel` from config, then write a test that swaps it with `overrideProvider(CHAT_MODEL).useValue(fake)`.
- Reproduce the singleton leak: store `currentUserId` on a default-scope provider, fire 50 concurrent requests as different users with a small script, and count mismatched responses; then fix it with `AsyncLocalStorage` or by passing the user explicitly.
- Load test a Postgres-backed endpoint with `pg.Pool` sizes 2, 10 and 50, and record p95 latency, `pool.waitingCount` and `SELECT count(*) FROM pg_stat_activity` for each.
- Say it out loud: in two minutes, explain Singleton as a lifetime vs Singleton as a global access point, and how NestJS providers and FastAPI `Depends` give you the first without the second.

## Structural Design Patterns [Core]

> Structural patterns are about how objects are wrapped and combined: a stable interface in front of something that changes, extra behavior without editing a class, or a tree treated like a single object. Interviewers probe whether you can separate patterns that look identical in code (Adapter, Decorator and Proxy are all "a class that wraps another class") by their intent, and whether you know NestJS decorators and Express middleware are not the GoF Decorator. Strong answers point at shipped code, such as a provider-neutral LLM layer, a caching repository or a filter tree compiled to SQL, and say when the extra layer is not worth it.

### In plain words
Structural patterns are ways of connecting pieces so they fit and stay easy to change. A travel plug adapter lets your charger fit a foreign socket without rewiring either one (Adapter). A hotel front desk books your taxi, dinner and laundry so you never talk to each department (Facade). A phone case adds grip while the phone works exactly the same (Decorator), and a receptionist who checks your badge stands in front of the office (Proxy). A box can hold items or smaller boxes, and you can still ask how much the whole box weighs (Composite), while a library lends one copy of a book to many readers instead of printing one each (Flyweight).

### Concepts you must understand
- Structural patterns change how objects are composed, not what they compute; most are "wrap an object behind an interface", and they differ by intent.
- Adapter converts an existing interface into the one your code expects; it is the core of every provider-neutral LLM layer and payment gateway wrapper.
- Facade gives one simple entry point to a whole subsystem; Adapter makes one thing fit a contract that already exists.
- Decorator keeps the same interface and adds behavior (cache, retry, logging), and wrappers stack; TypeScript `@` decorators in NestJS mostly attach metadata, which is a different thing.
- Proxy keeps the same interface and controls access to the real object (lazy creation, permission checks, caching, remote calls); JavaScript's `Proxy` object is one tool for building it.
- Composite gives a leaf and a tree of leaves one interface, so code recurses instead of checking types: filter trees, menus, React element trees.
- Bridge splits two dimensions that vary independently (what you send and how you send it), so M plus N classes replace M times N.
- Flyweight shares immutable state across many objects to save memory and passes the varying part in; V8 hidden classes and string interning are built-in examples.
- Every wrapper adds a layer to stack traces and debugging, so add one only when it hides real variation or removes real duplication.

| Pattern | Intent in one line | Real example in Node, NestJS, FastAPI or LLM apps | When not to use |
|---|---|---|---|
| Adapter | Make an existing interface fit the one clients expect | One `ChatModel` interface over the OpenAI, Anthropic and vLLM SDKs; Vercel AI SDK providers; LiteLLM | One provider with no second in sight; a lowest-common-denominator interface that hides features you need |
| Facade | One simple entry point to a complex subsystem | `AskService.answer()` over embedder, vector store, reranker and LLM; `Upload` in `@aws-sdk/lib-storage` | When it grows into a god service every module must go through |
| Decorator | Add behavior by wrapping an object with the same interface | `CachedUserRepo` around `PgUserRepo`; a retrying `ChatModel`; tenacity's `@retry` on Python functions | Behavior every route needs (use middleware or an interceptor); stacks nobody can trace |
| Proxy | Control access through a stand-in with the same interface | SQLAlchemy lazy relationships; a permission proxy around agent tools; Immer drafts and Vue 3 reactivity on JS `Proxy` | Hot paths where trap overhead matters; when an explicit call is clearer than hidden behavior |
| Composite | Treat single objects and trees of objects the same way | AND/OR filter trees compiled to SQL or vector-store filters; nested menus; React `children` | Flat data; leaves and groups that need very different operations |
| Bridge | Let an abstraction and its implementation vary independently | Notification types times channels (email, SMS, Slack); Knex and SQLAlchemy over database dialects and drivers | Only one dimension varies; combinations that are not really independent |
| Flyweight | Share immutable common state across many objects | Deduplicated metadata in large in-memory datasets; one shared tokenizer; vLLM prefix caching sharing KV cache blocks | Few objects, or shared state that must change |

### Q. What is the Adapter pattern? Give an example of wrapping third-party APIs.
**Short answer (45 seconds):** An Adapter converts an existing class's interface into the one your code expects, without changing either side. The common case is a `ChatModel` interface your app owns, with one adapter per LLM provider translating requests, responses and errors. Payments work the same: your `PaymentGateway` stays fixed while Stripe and Razorpay adapters map amounts, statuses and webhooks.

**Deeper explanation:** Anthropic's Messages API takes `system` as a top-level field, requires `max_tokens`, returns `content` blocks and reports `stop_reason` (`end_turn`, `max_tokens`, `tool_use`). OpenAI Chat Completions puts the system prompt in `messages`, returns `choices[0].message`, reports `finish_reason` (`stop`, `length`, `tool_calls`) and sends tool arguments as a JSON string.

```ts
type Msg = { role: 'user' | 'assistant'; content: string };
type ChatResult = { text: string; stop: 'end' | 'length' | 'tool' };
interface ChatModel { chat(system: string, messages: Msg[], maxTokens: number): Promise<ChatResult> }

export class AnthropicChat implements ChatModel {
  constructor(private client: Anthropic, private model: string) {}
  async chat(system: string, messages: Msg[], maxTokens: number): Promise<ChatResult> {
    const res = await this.client.messages.create({ model: this.model, system, messages, max_tokens: maxTokens });
    const text = res.content.flatMap((b) => (b.type === 'text' ? [b.text] : [])).join('');
    const stop = res.stop_reason === 'max_tokens' ? 'length' : res.stop_reason === 'tool_use' ? 'tool' : 'end';
    return { text, stop };
  }
}
```

Map errors (rate limit, overloaded, context too long) to your own types too, so retries never import an SDK. Vercel AI SDK providers and LiteLLM are ready-made adapters; in Python the interface is a `typing.Protocol`.

When not to use it: one provider, no second planned. And a lowest-common-denominator interface loses features such as Anthropic prompt caching or OpenAI structured outputs, so leave an escape hatch.

**Follow-ups they will ask:**
- How do you test adapters?: One contract test suite run against every adapter, using recorded responses.
- Where do they live in NestJS?: Behind a token picked by a `useFactory` provider.

**Mistakes to avoid:**
- Leaking SDK types through the interface, so a swap still touches every caller.
- Calling a caching wrapper an adapter; if the interface does not change, it is a decorator or proxy.

### Q. Facade vs Adapter: how do they differ?
**Short answer (45 seconds):** They differ in intent. An Adapter makes one existing interface match a contract your code already expects; a Facade defines a new, simpler interface over a whole subsystem so callers do not coordinate its parts. An adapter usually wraps one object, a facade usually orchestrates several, and a facade often calls adapters underneath.

**Deeper explanation:**

| Aspect | Adapter | Facade |
|---|---|---|
| Problem | Interface mismatch | Too many moving parts |
| Wraps | Usually one object | Several objects in a subsystem |
| Interface | One that already exists | A new, smaller one |
| Example | `AnthropicChat implements ChatModel` | `AskService.answer()` over a RAG pipeline |

```ts
@Injectable()
export class AskService { // facade over the RAG subsystem
  constructor(private embedder: Embedder, private store: VectorStore,
              private reranker: Reranker, @Inject(CHAT_MODEL) private llm: ChatModel) {}

  async answer(tenantId: string, question: string) {
    const vector = await this.embedder.embed(question);
    const hits = await this.store.search(tenantId, vector, 40);
    const top = await this.reranker.rank(question, hits, 8);
    return this.llm.chat(SYSTEM_PROMPT, [{ role: 'user', content: withContext(question, top) }], 800);
  }
}
```

A controller, a queue consumer and an eval script all call `answer()` without knowing the retrieval steps. Libraries ship facades too: `Upload` from `@aws-sdk/lib-storage` hides the create, upload-part and complete calls of an S3 multipart upload, and boto3's `upload_file` does the same in Python.

When not to use it: when it becomes a god service every module must pass through (keep parts reachable, such as the embedder for an ingestion job), or when it wraps one class and mirrors its methods.

**Follow-ups they will ask:**
- Can one class be both?: Yes, a `PaymentsService.checkout()` facade can wrap a Razorpay adapter; name the two roles separately.
- Is a NestJS application service a facade?: Often, when it orchestrates repositories and clients behind a few use-case methods.

**Mistakes to avoid:**
- Saying "a facade is an adapter for many classes"; a facade invents a simpler interface, an adapter conforms to an existing one.
- Swallowing errors in the facade so callers cannot tell a retrieval failure from a model failure.

### Q. What is the Decorator pattern, and how is it different from TypeScript decorators and Express middleware?
**Short answer (45 seconds):** The GoF Decorator wraps an object in another object with the same interface, adds behavior before or after delegating, and can be stacked at runtime: a caching repository around a Postgres repository, or a retrying chat model around any chat model. TypeScript decorators are syntax that annotates classes and members at definition time, and NestJS uses them mostly to attach metadata. Express middleware is a request pipeline, closer to chain of responsibility than to wrapping an object.

**Deeper explanation:**

```ts
export class CachedUserRepo implements UserRepo {
  constructor(private inner: UserRepo, private redis: Redis, private ttlSec = 60) {}

  async findById(id: string): Promise<User | null> {
    const hit = await this.redis.get(`user:${id}`);
    if (hit) return JSON.parse(hit) as User;
    const user = await this.inner.findById(id);
    if (user) await this.redis.set(`user:${id}`, JSON.stringify(user), 'EX', this.ttlSec);
    return user;
  }

  async save(user: User): Promise<void> {
    await this.inner.save(user);
    await this.redis.del(`user:${user.id}`); // invalidate on write
  }
}
const repo: UserRepo = new CachedUserRepo(new PgUserRepo(pool), redis);
```

Callers cannot tell a cache is there. Order matters: `Cached(Retrying(base))` checks the cache once and retries only the database, while `Retrying(Cached(base))` also retries Redis failures.

`@Controller()`, `@Get()`, `@Injectable()` and `@UseGuards()` record metadata through `reflect-metadata`, which Nest reads at bootstrap to build routes and the DI graph; they do not wrap anything. Nest interceptors are the closest match to a Decorator around a handler. Python's `@` wraps a function in a function, so tenacity's `@retry` is the pattern applied to functions, while FastAPI's `@app.get` only registers the route and returns the function unchanged.

When not to use it: behavior every route needs (auth, request logging) belongs in middleware or an interceptor, and deep stacks of wrappers are hard to debug.

**Follow-ups they will ask:**
- Decorator vs inheritance?: Inheritance fixes combinations at compile time; decorators compose per instance, so cache plus retry needs no `CachedRetryingRepo` subclass.
- Legacy vs standard TS decorators?: Nest relies on `experimentalDecorators` and `emitDecoratorMetadata`; TypeScript 5.0 standard decorators have no parameter decorators.

**Mistakes to avoid:**
- Answering "a decorator is the `@` syntax"; interviewers want the wrapping object.
- Forgetting to invalidate the cache on writes.

### Q. What is the Proxy pattern? Show caching, access-control and lazy-loading proxies, and JavaScript's Proxy object.
**Short answer (45 seconds):** A Proxy is a stand-in with the same interface as the real object that controls access to it. A virtual proxy creates the expensive object on first use, a protection proxy checks permissions before forwarding, a caching proxy answers repeated calls itself, and a remote proxy makes a network call look local. JavaScript's built-in `Proxy` intercepts property reads, writes and calls on any object; Vue 3 reactivity and Immer drafts use it.

**Deeper explanation:** A proxy is shaped like a decorator, but its intent is to guard or manage the real subject, often including its lifecycle. An access-control proxy for an agent's tools:

```ts
function allowOnly<T extends object>(target: T, allowed: ReadonlyArray<keyof T>): T {
  return new Proxy(target, {
    get(obj, prop, receiver) {
      if (!allowed.includes(prop as keyof T)) throw new Error(`Method ${String(prop)} is not allowed`);
      const value = Reflect.get(obj, prop, receiver);
      return typeof value === 'function' ? value.bind(obj) : value;
    },
  });
}
const agentOrders = allowOnly(ordersRepo, ['findById', 'search']); // delete() is unreachable
```

The `bind(obj)` matters: classes with `#private` fields and built-ins like `Map` throw when a method runs with the proxy as `this`.

Lazy loading: SQLAlchemy relationships load on first attribute access by default; under `AsyncSession` that implicit I/O raises `MissingGreenlet`, so you load eagerly with `selectinload`. Caching: an LLM gateway such as the LiteLLM proxy sits in front of providers, caches responses, enforces rate limits and holds the API keys. gRPC stubs and MCP clients are remote proxies.

When not to use it: hot paths, where `Proxy` traps add overhead, and places where hidden behavior (a query on attribute access) would surprise readers.

**Follow-ups they will ask:**
- Proxy vs decorator in one line?: Same shape; a proxy controls access to the subject, a decorator adds responsibilities to it.
- Is Nginx a proxy in this sense?: Yes, the same idea at the network level: same HTTP interface, plus access control and caching.

**Mistakes to avoid:**
- Treating a proxy as the only security check; enforce permissions again in the service or database.
- Lazy loads inside loops: N+1 queries.

### Q. When do you use the Composite pattern?
**Short answer (45 seconds):** Use Composite when your data is a tree and one item and a group of items should share an interface, so code recurses instead of branching on types. Real cases: AND/OR filters, role and permission trees, nested menus, agent plans whose steps can contain sub-plans, and React itself, where a component renders elements that can contain more components.

**Deeper explanation:** In TypeScript a discriminated union is the idiomatic composite; the OO version has `Condition` and `Group` classes that both implement `toSql()`.

```ts
type Filter =
  | { op: 'eq'; field: AllowedField; value: string | number }
  | { op: 'and' | 'or'; children: Filter[] };

function toSql(f: Filter, params: unknown[]): string {
  if (f.op === 'eq') {
    params.push(f.value);
    return `${COLUMNS[f.field]} = $${params.length}`; // whitelisted column, bound value
  }
  if (f.children.length === 0) return f.op === 'and' ? 'TRUE' : 'FALSE';
  return `(${f.children.map((c) => toSql(c, params)).join(f.op === 'and' ? ' AND ' : ' OR ')})`;
}
```

The same tree can compile to a Mongo query (`$and`, `$or`) or a vector store's metadata filter, which keeps the UI filter builder independent of the backend. In FastAPI, a recursive Pydantic model (`children: list["Filter"]`) validates it straight from JSON. React's `children` prop is composite thinking: a `Menu` renders `MenuItem` or a nested `Menu` and never needs to know which.

When not to use it: flat lists, or leaves and groups so different that a shared interface forces meaningless methods like `leaf.addChild()`. Cap depth and node count on user-supplied trees, because deeply nested filter JSON is a cheap way to burn CPU or overflow the stack.

**Follow-ups they will ask:**
- How do you store a tree in Postgres?: An adjacency list read with a recursive CTE, or `ltree` or a closure table when subtree queries are frequent.
- How do you stop cycles in a role tree?: Check on write that the new parent is not a descendant, and cap depth.

**Mistakes to avoid:**
- Interpolating client-supplied field names into SQL; only values are bound, so columns must come from a whitelist.

### Q. What is the Bridge pattern, and when does it pay off?
**Short answer (45 seconds):** Bridge separates an abstraction from its implementation so the two can vary independently, joined by composition instead of inheritance. It pays off when two dimensions both grow, such as notification types (OTP, weekly digest, incident alert) and delivery channels (email, SMS, Slack, WhatsApp): you write M plus N classes instead of M times N subclasses.

**Deeper explanation:**

```ts
interface Channel { send(to: Recipient, subject: string, body: string): Promise<void> }

abstract class Notification {
  constructor(protected channel: Channel) {} // the bridge
  protected abstract render(): { subject: string; body: string };
  async deliver(to: Recipient) {
    const { subject, body } = this.render();
    await this.channel.send(to, subject, body);
  }
}

class OtpNotification extends Notification {
  constructor(channel: Channel, private code: string) { super(channel); }
  protected render() { return { subject: 'Your login code', body: `Code ${this.code}, valid for 5 minutes` }; }
}

await new OtpNotification(smsChannel, code).deliver(user); // 3 types + 4 channels = 7 classes, not 12
```

Knex is a query-building abstraction over dialect clients for Postgres, MySQL and SQLite; SQLAlchemy sits on dialects and DBAPI drivers such as psycopg and asyncpg. In LLM apps, task classes (summarizer, extractor, classifier) that own their prompts and output parsing can hold any `ChatModel`, so tasks and providers are added independently.

Bridge vs Adapter: a bridge is designed up front so both sides can evolve; an adapter is retrofitted to make an existing interface fit. Bridge vs Strategy: similar code, but Strategy swaps one algorithm while Bridge splits a class hierarchy in two.

When it does not pay off: only one dimension varies, so a plain interface is enough, or the combinations are not independent (an OTP must never go over Slack), where a table of allowed pairs is clearer.

**Follow-ups they will ask:**
- Can DI wire a bridge?: Yes, inject `Channel` by token and pick the implementation per environment or user preference.
- Where do channel limits such as SMS length go?: In the channel implementation, so the abstraction stays channel-agnostic.

**Mistakes to avoid:**
- Subclassing per combination (`OtpSms`, `OtpEmail`), the class explosion Bridge exists to prevent.

### Q. What is the Flyweight pattern, and where does it matter in practice?
**Short answer (45 seconds):** Flyweight saves memory by sharing the immutable part of many similar objects (intrinsic state) and passing the varying part (extrinsic state) in from outside. It matters when you hold many objects with repeated data, such as millions of rows in memory. Runtimes already do it: V8 shares one hidden class among objects of the same shape, and string interning keeps one copy of identical strings.

**Deeper explanation:**

```ts
type Meta = Readonly<{ service: string; level: string; color: string }>;
const shared = new Map<string, Meta>();

function metaFor(service: string, level: string): Meta {
  const key = `${service}|${level}`;
  let meta = shared.get(key);
  if (!meta) {
    meta = Object.freeze({ service, level, color: colorFor(level) });
    shared.set(key, meta);
  }
  return meta;
}
// millions of rows share a few hundred Meta objects
rows.push({ ts, message, meta: metaFor(svc, lvl) });
```

Shared objects must be immutable: if one caller mutates a flyweight, every row changes. In Python, `sys.intern()` shares strings and CPython caches small integers.

LLM systems use it at several layers. Load a tokenizer or local embedding model once per process and share it, since Hugging Face `from_pretrained` builds a new object on every call. Store one embedding per unique chunk hash with document metadata kept separately, so repeated boilerplate is embedded once. vLLM's automatic prefix caching shares KV cache blocks between requests with the same prompt prefix. React list virtualization (react-window, TanStack Virtual) is a related idea: a few rendered rows stand in for thousands, with index and data passed in.

When not to use it: small object counts, or before a heap snapshot (Chrome DevTools, `tracemalloc`) proves the duplication; the lookup and split state make code harder to follow.

**Follow-ups they will ask:**
- Flyweight vs cache?: A cache saves recomputation and may evict; a flyweight saves memory by sharing identity and must stay immutable.
- Flyweight vs singleton?: A singleton is one instance; a flyweight factory holds one instance per distinct intrinsic value.

**Mistakes to avoid:**
- Sharing mutable objects and calling it a flyweight.
- An unbounded shared map over values that turn out to be high-cardinality.

### Practice
- Write `ChatModel` adapters for two providers (or one provider plus a local vLLM or Ollama endpoint) and one contract test suite that every adapter must pass, including stop-reason and error mapping.
- Wrap a repository in `CachedRepo` and `RetryingRepo` decorators, swap their order, and log which calls hit Redis, which retry, and what happens when Redis is down.
- Implement the filter composite as a recursive Pydantic model in FastAPI, compile it to parameterized SQL, and test empty groups, the depth limit and an attempt to inject a column name.
- Say it out loud: one sentence each that separates Adapter, Facade, Decorator and Proxy by intent, with a real LLM-app example for each.
