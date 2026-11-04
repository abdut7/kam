## Express.js Request Pipeline [Core]

> Interviewers who see Express on a resume skip "what is middleware" and ask how the stack is actually dispatched: what next() does internally, how Express tells error middleware apart, what a mounted router does to req.url, and what Express 5 changed about async errors. A weak answer recites "middleware are functions that run in order". A strong answer describes the layer array and the next() closure, explains why a three-argument error handler silently never runs, traces the socket from app.listen() to the handler, and says clearly where Express stops and the team's own architecture has to start.

### In plain words
Picture a document travelling along a row of desks in an office, in the exact order the desks were set up that morning. Each clerk either stamps it and passes it to the next desk, or answers the customer, and then the document goes no further. Some desks only take certain documents, such as passport renewals. If any clerk finds a problem, the document skips every normal desk and goes straight to the complaints desk at the end of the row. If a clerk neither answers nor passes it on, the customer simply waits until they give up.

In Express terms, the desks are middleware layers in registration order, passing it on is next(), answering is res.json or res.send, the picky desks are routers and routes that match a path and an HTTP method, the complaints desk is error middleware with four arguments, and the waiting customer is a request that times out because nothing ended the response.

### Walkthrough: one request through the Express middleware chain
1. **Node's http server emits 'request'**: once the HTTP parser has the request line and headers, Node creates an IncomingMessage (req) and a ServerResponse (res) and emits `request`. The body has not been read yet; req is still a readable stream.
2. **The app is the listener**: `express()` returns a plain function, so Node calls `app(req, res)`, which runs `app.handle` and passes the request to the app's router, with finalhandler kept as the last resort.
3. **Express wraps req and res**: before your code runs, Express points the prototypes of the same req and res objects at its own request and response objects, which inherit from Node's. That is how res.json, res.status and req.get appear without any new objects being created.
4. **The middleware stack runs in registration order**: the router holds an array of layers, one per app.use or app.METHOD call, and a `next` closure walks it with an index, skipping layers whose path does not match.
5. **Each layer calls next() or ends the response**: a middleware either calls next() to continue or ends the response with res.json, res.send or res.end. If it does neither the request hangs, and if it does both you get "Cannot set headers after they are sent".
6. **Routers are middleware too**: `app.use('/api', apiRouter)` adds a prefix-match layer, and inside it Express strips `/api` from req.url and records it in req.baseUrl. A route such as `app.get('/users/:id', ...)` is a layer that needs a full path match and holds its own small stack of handlers, filtered by HTTP method.
7. **Route params and app.param**: when a route matches, its captures fill req.params, and an `app.param('id', fn)` callback runs once per request for that parameter, before the route handlers. A child router sees its parent's params only if it was created with `mergeParams: true`.
8. **Errors skip to error middleware**: `next(err)`, or a synchronous throw inside a handler, puts dispatch into error mode, where normal middleware is skipped and only functions declared with four parameters `(err, req, res, next)` run. Express 5 also forwards a rejected promise returned by an async handler; Express 4 needs a wrapper or express-async-errors.
9. **The response is written**: res.json runs JSON.stringify synchronously on the event loop, sets Content-Type and calls res.send, which sets Content-Length, adds an ETag (answering 304 when the client's copy is fresh) and calls Node's res.end. The `finish` event fires when the last bytes are handed to the OS, which is where access loggers stop the clock.
10. **Nothing matched**: if the stack runs out without a response, finalhandler sends a 404 "Cannot GET /path", or err.status or 500 when an error is pending. If headers were already sent, it destroys the socket instead.

### Concepts you must understand
- `express()` returns a function with the signature `(req, res, next)`, which is a valid Node request listener, and app.listen() is just `http.createServer(app).listen(...)`.
- req and res are Node's own IncomingMessage and ServerResponse objects; Express only swaps their prototypes to add helper methods.
- The router is an ordered array of layers, dispatch is a linear scan in registration order, and every Router instance has its own stack.
- app.use matches a path prefix and strips it from req.url for everything mounted under it (req.baseUrl holds the stripped part, req.originalUrl never changes); route methods match the full path and the HTTP method.
- Express tells error middleware from normal middleware by `fn.length`, exactly four declared parameters, so a generic wrapper or a linter removing an unused `next` silently breaks it.
- next() continues, next(err) jumps to the next error middleware, next('route') skips the remaining handlers of the current route, and next('router') leaves the current router.
- Express 4 catches synchronous throws but ignores the promise an async handler returns; Express 5 forwards rejections to error middleware.
- Express 5 also moved to path-to-regexp 8 (wildcards must be named, such as `/*splat`, and inline regex in path strings is gone), made req.query a read-only getter, and removed several deprecated signatures.
- All per-request Express work (route matching, body parsing, JSON.stringify in res.json) runs synchronously on the single event loop thread, so a large payload costs latency for every request on the process.

### Q. How does the Express middleware stack actually work, and why does order matter?
**Short answer (45 seconds):** Each app.use or app.METHOD call appends a layer to the router's stack: a path matcher plus a handler, and for routes a nested stack filtered by method. Per request, a `next` closure walks that array from index zero, calling each matching layer and moving on only when it calls next(). An error flips the walk into a mode where only four-argument handlers run. As a linear walk in registration order, order is behaviour: parsers before routes, auth before protected routes, 404 and error handlers last.

**Deeper explanation:** A simplified version of what the router does:

```js
function handle(stack, req, res, done) {
  let idx = 0;
  function next(err) {
    const layer = stack[idx++];
    if (!layer) return done(err);                 // finalhandler
    if (!layer.match(req.path)) return next(err);
    const fn = layer.handle;
    try {
      if (err && fn.length === 4) return fn(err, req, res, next);
      if (!err && fn.length < 4) return fn(req, res, next);
      next(err);                                  // wrong kind for this mode
    } catch (e) { next(e); }                      // sync throws become errors
  }
  next();
}
```

Arity is the type system: an error handler written as `(err, req, res)`, or wrapped in a generic `(...args) =>` helper, has a length below 4 and is skipped in error mode. Matching is a linear regex scan, so a late route among hundreds pays for every earlier test; Fastify uses a radix tree.

Order mistakes are real bugs: CORS after auth gives browser preflight requests a 401; a logger after the router never sees 404s; a rate limiter after express.json() parses bodies it will reject.

**Follow-ups they will ask:**
- What do next('route') and next('router') do? : the first skips the current route's remaining handlers, the second exits the current router.
- Why would a request hang? : a layer neither called next() nor ended the response, often an async middleware that swallowed an error.

**Mistakes to avoid:**
- Saying Express sorts middleware or runs it in parallel; it is strictly registration order, one layer at a time.
- Declaring the error handler with three parameters, or registering it before the routes.

### Q. How do you handle errors from async route handlers in Express 4 versus Express 5?
**Short answer (45 seconds):** Express 4 calls each handler inside a try/catch, so synchronous throws become next(err), but it ignores the promise an async handler returns. A rejection escapes Express: on Node 15 and later it is an unhandled rejection that crashes the process by default, and the client never gets a response. In Express 4 you wrap handlers with a helper that adds `.catch(next)`, or load express-async-errors once. Express 5 calls next(err) when a returned promise rejects, so plain async handlers just work.

**Deeper explanation:**

```js
// Express 4 only: forward rejections to error middleware
const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
app.get('/users/:id', wrap(async (req, res) => {
  res.json(await users.findById(req.params.id));   // may throw NotFoundError
}));

// both versions: one error middleware, four parameters, registered last
app.use((err, req, res, next) => {
  if (res.headersSent) return next(err);           // Express closes the socket
  const status = err instanceof NotFoundError ? 404 : 500;
  logger.error({ err, path: req.path }, 'request failed');
  res.status(status).json({ error: status === 500 ? 'internal error' : err.message });
});
```

Express 5 only sees the promise you return: a fire-and-forget `void sendEmail()`, a setTimeout callback or an EventEmitter `error` event still escapes, so await what matters and send stream errors to next(err) via stream.pipeline. express-async-errors monkey-patches Express 4's internal router Layer; Express 5 moved routing into the separate `router` package, so remove it when you upgrade. The headersSent check matters for streamed LLM responses: once the first chunk is out you cannot switch to a JSON error, so you end the stream and log.

**Follow-ups they will ask:**
- What if the error middleware itself throws? : Express passes that error to the next error middleware, and finally to finalhandler.
- What else changes on the upgrade? : route path syntax, the read-only req.query and removed deprecated signatures; work through the official migration guide.

**Mistakes to avoid:**
- Believing Express 5 catches errors from promises you never awaited or returned.
- Wrapping error middleware in the same helper: the wrapper declares three parameters, so it stops being error middleware.

### Q. What happens between app.listen() and your route handler running?
**Short answer (45 seconds):** app.listen() is `http.createServer(app).listen(port)`: Express owns no server, the app is only the request listener. Node binds the socket, libuv accepts connections in the event loop's poll phase, and the built-in HTTP parser reads the request line and headers. Then Node creates req and res and emits `request`, which calls the app; Express walks the stack and your handler runs synchronously in that same callback, possibly before the body has arrived. Keep-alive and the server timeouts govern the socket around each request.

**Deeper explanation:**

```js
const server = app.listen(3000);   // http.createServer(app).listen(3000)
server.keepAliveTimeout = 65_000;  // idle time on a keep-alive socket; default is 5 s
server.headersTimeout = 66_000;    // full headers must arrive in time; keep above keepAliveTimeout
server.requestTimeout = 120_000;   // the whole request, headers and body; 0 disables it
```

With keep-alive one socket carries many sequential requests. A classic production bug lives here: an AWS ALB keeps idle upstream connections for 60 seconds by default and reuses them, while Node closes an idle socket after 5 seconds. A request the balancer sends on a socket Node is closing gets a reset, and the client sees a 502. The fix is a keepAliveTimeout longer than the balancer's idle timeout.

headersTimeout (60 seconds by default in recent versions) and requestTimeout (5 minutes by default since Node 18) protect against slowloris-style clients. The body is read only when a parser such as express.json() consumes the req stream, buffering up to its limit (100kb by default) before a synchronous JSON.parse.

**Follow-ups they will ask:**
- Where in the event loop does your handler run? : inside the poll phase callback that delivered the bytes, so slow synchronous middleware delays every other socket.
- What limits header size? : Node's maximum header size (16 KiB by default, set with --max-http-header-size); bigger requests get a 431.

**Mistakes to avoid:**
- Saying Express manages connections or threads; Node's http module and libuv do, and Express only ever sees req and res.
- Raising every timeout to hours instead of aligning them along the load balancer chain.

### Q. Where does Express end and your architecture begin: how do you keep controllers thin at scale?
**Short answer (45 seconds):** Express gives routing and a middleware pipeline and nothing about structure, so everything past the route handler is my design. Per feature, a thin route handler only translates HTTP: validate input against a schema, call one service method, map the result to a status and a DTO. A service holds business rules and transaction boundaries and never sees req or res, and repositories or clients wrap Postgres, Redis and LLM providers. Domain errors map to status codes in one error middleware, wired from one composition root.

**Deeper explanation:**

```ts
// users.routes.ts: HTTP in, HTTP out
router.post('/', async (req, res) => {
  const input = CreateUser.parse(req.body);         // ZodError -> 400 in error middleware
  const user = await usersService.create(input, ctxFrom(req));
  res.status(201).json(toUserDto(user));
});

// users.service.ts: no Express imports allowed
export class UsersService {
  constructor(private readonly repo: UsersRepo) {}
  async create(input: CreateUserInput, ctx: RequestCtx) {
    if (await this.repo.emailTaken(ctx.tenantId, input.email)) throw new ConflictError();
    return this.repo.insert({ ...input, tenantId: ctx.tenantId });
  }
}

// composition root: the only place that calls constructors
export const usersService = new UsersService(new PgUsersRepo(pool));
```

The real test of thinness is reuse: the same service should be callable from the route, a BullMQ worker and an LLM agent's tool call. In AI products that last one matters, because tools that call the service layer get the same validation, tenant scoping and authorization as the UI instead of a parallel path that skips them. That only works if services take plain inputs and an explicit context, not req.

Use feature folders, and enforce import direction with dependency-cruiser or ESLint rules so no service imports express.

**Follow-ups they will ask:**
- Do you need a DI container? : not at first; a composition root is explicit and testable, and awilix helps later.
- Where do transactions live? : in the service, which opens one and passes a transaction-bound client to the repositories.

**Mistakes to avoid:**
- Passing req or res into services, which ties business logic to HTTP and makes workers and tests awkward.
- Hiding business work, such as mutating records, in middleware the route silently depends on.

### Practice
- Build an app with three middleware that log on entry and on res `finish`, mount a router at `/api`, and print req.url, req.baseUrl and req.originalUrl in each layer; then add a child router with and without `mergeParams: true` and compare req.params.
- Install express@4 and express@5 in two folders, add the same async handler that rejects, and record what each does with and without error middleware; then declare the error middleware with three parameters and watch it stop running.
- Log server.keepAliveTimeout, headersTimeout and requestTimeout at startup, open a raw socket with `nc localhost 3000`, send half a request's headers, and time how long Node takes to close it.
- Take one fat route from a real project, split it into route, service and repository, and write a unit test for the service that never starts an HTTP server.
- Say it out loud: in under two minutes, explain how Express dispatches one request from the `request` event to res.json, including how it finds error middleware and what changed in Express 5.

## NestJS Architecture [Core]

> NestJS interviews test whether you know what the decorators actually do. A weak answer lists the building blocks (modules, controllers, providers, guards) and says Nest "does dependency injection". A strong answer explains that decorators only store metadata, that the injector reads constructor types from `design:paramtypes` at boot, that the request pipeline runs in a fixed, documented order, why request scope spreads through a dependency chain, and what Nest costs compared with the Express or Fastify app running underneath it.

### In plain words
Think of a hospital opening for the day. Before the doors open, an administrator reads every department's staff list, works out who needs whom (the surgeon needs a nurse and an anesthetist), and brings people in so that nobody starts work missing a colleague; departments lend out only the staff they have listed as shareable. Every patient then passes the same stations in the same order: the entrance, a security desk that decides whether they may enter this ward, a receptionist who notes when they arrive and leave, and a triage nurse who checks their paperwork is complete. Only then do they see the doctor, who calls in specialists, and if anything goes wrong at any station, a patient relations office turns it into a clear explanation.

In NestJS terms, the administrator is the dependency injection container, departments are modules, shareable staff are exported providers, the entrance is middleware, security is guards, the receptionist is interceptors, the triage nurse is pipes, the doctor is the controller, the specialists are services, and patient relations is exception filters.

### Walkthrough: how Nest boots and builds the dependency graph
1. **NestFactory.create(AppModule)**: creates an empty container and an HTTP adapter, the ExpressAdapter from @nestjs/platform-express by default or a FastifyAdapter you pass in. Nothing is listening yet.
2. **Decorators already left metadata**: when your files were first imported, @Module, @Injectable, @Controller and @Get ran and called Reflect.defineMetadata (from the reflect-metadata package) to attach imports, providers, paths and options to the classes. Nest reads that metadata; it never parses your source.
3. **The scanner walks the module graph**: starting at AppModule it reads each module's `imports` and recurses depth first, registering every module once and resolving forwardRef and dynamic modules on the way. It then records each module's providers, controllers and exports in the container under their tokens.
4. **Constructor types come from design:paramtypes**: with emitDecoratorMetadata on, TypeScript emitted a `design:paramtypes` array for every decorated class, listing its constructor parameter types. @Inject(TOKEN) overrides single entries, and interfaces compile to Object, so they cannot be tokens.
5. **Module scoping decides visibility**: for each dependency the injector looks in the module's own providers, then in the exported providers of the modules it imports. If the token is in neither, and not in a global module, boot fails with "Nest can't resolve dependencies of ...".
6. **Global modules**: a module marked @Global(), or a dynamic module returned with `global: true` (what ConfigModule.forRoot({ isGlobal: true }) does), exposes its exports to every module without further imports. It still has to be imported once, usually by the root module.
7. **Dynamic modules**: forRoot, forRootAsync and forFeature are static methods that return module metadata built from options. forRootAsync uses a factory with `inject`, so a database or LLM module can wait for ConfigService before it builds its client.
8. **The injector instantiates in dependency order**: it resolves each provider's parameters recursively, awaits async factory providers (such as one that opens a database connection), then calls the constructor. DEFAULT scope instances are created once and cached, so they are singletons for the life of the app.
9. **Routes and lifecycle hooks**: app.init(), which listen() calls for you, registers middleware and one route per controller method on the adapter, each wrapped in the guard, interceptor and pipe chain composed for it. It then awaits onModuleInit across the modules and onApplicationBootstrap once all of them are initialized.
10. **app.listen(port)**: only now does the adapter's HTTP server bind the port. A provider factory or hook that throws stops the process before it ever accepts traffic.

### Walkthrough: one request through the NestJS lifecycle
1. **Middleware**: the adapter runs global middleware (app.use), then module middleware bound with `consumer.apply(...).forRoutes(...)`. On Express, Nest's default JSON and urlencoded body parsers sit in front; middleware gets raw req, res and next and knows nothing about the handler that will run.
2. **Guards**: global, then controller, then route guards call canActivate with an ExecutionContext, which exposes the handler and the controller class, so a guard can read metadata such as @Roles() through Reflector. Returning false produces a 403; throwing UnauthorizedException produces a 401.
3. **Interceptors (before)**: global, then controller, then route interceptors run their code before `next.handle()`, such as starting a timer or checking a cache. An interceptor can short-circuit by returning its own Observable without calling handle().
4. **Pipes**: global, controller, route and finally parameter pipes run once per handler argument (body, params, query). ValidationPipe validates and transforms a DTO, ParseIntPipe converts an id, and a failure throws a 400 before the handler runs.
5. **Controller route handler**: Nest calls the method with the resolved arguments, including values produced by custom parameter decorators such as @CurrentUser().
6. **Service**: the handler awaits injected services, where business logic, database calls and LLM calls live; anything they throw travels back up the chain.
7. **Interceptors (after)**: the handler's return value, or its resolved promise, becomes an RxJS stream, and interceptor operators such as map, tap, timeout and catchError run in reverse order: route, controller, global.
8. **Exception filters**: anything thrown by a guard, interceptor, pipe, handler or service is handled by one matching filter, searched from route to controller to global. The built-in filter turns an HttpException into its JSON body and anything else into a 500 with "Internal server error".
9. **Response sent by the underlying adapter**: Nest calls the adapter's reply, res.json or res.send on Express and reply.send on Fastify, with status 200, 201 for POST, or whatever @HttpCode says. If you injected @Res() without `passthrough: true`, Nest sends nothing and the response is yours to finish.

### Concepts you must understand
- Nest is a layer over an HTTP adapter (Express by default, Fastify optionally): it registers ordinary routes on that adapter at boot, so Node, the event loop and the adapter's parsing behave exactly as they would without Nest.
- Decorators run when a class file is first imported and only store metadata through reflect-metadata; the scanner and injector read that metadata at boot.
- Dependency injection resolves tokens (a class, a string or a symbol); constructor types come from `design:paramtypes`, and @Inject(TOKEN) overrides individual parameters.
- Providers are singletons per registering module by default; REQUEST and TRANSIENT scopes exist, and REQUEST scope propagates to every provider and controller that depends on it.
- Modules are visibility boundaries: importing modules can inject only exported providers, and global modules skip the import requirement.
- Dynamic modules are static methods that return module metadata built from options, and forRootAsync lets those options come from other providers such as ConfigService.
- Each route's pipeline is composed once at boot: middleware, guards, interceptors, pipes, handler, interceptors on the result stream, and filters on errors.
- ExecutionContext gives guards and interceptors the handler and class being called, which is how metadata decorators such as @Roles() reach them through Reflector.
- Lifecycle hooks (onModuleInit, onApplicationBootstrap, and the shutdown hooks after app.enableShutdownHooks()) are awaited, so slow hooks delay startup or shutdown.

| Building block | Runs when | Gets access to | Typical use |
|---|---|---|---|
| Middleware | first, matched by path only | raw req, res and next from the adapter; no handler information | helmet, CORS, request ids, raw body capture, access logs |
| Guard | after middleware, before interceptors and pipes | ExecutionContext: the request plus the handler and class, read with Reflector | authentication, roles, tenant membership, rate limits |
| Interceptor | around the handler, before and after it | ExecutionContext plus CallHandler, whose handle() returns an RxJS Observable of the result | timing and logging, response mapping, caching, timeouts |
| Pipe | after the interceptors' before part, once per argument | the argument value and ArgumentMetadata (type, metatype, data) | validation with ValidationPipe, conversion with ParseIntPipe or ParseUUIDPipe |
| Exception filter | only when a guard, interceptor, pipe, handler or service throws | the exception and ArgumentsHost | mapping domain errors to status codes, one error body format, error reporting |
| Custom decorator | metadata decorators when the class loads; parameter decorators while arguments are resolved, before pipes | the decorated target, or ExecutionContext for createParamDecorator | @CurrentUser(), @Roles(), @Public(), bundling several with applyDecorators |

### Q. Walk me through the NestJS request lifecycle in order, and where would you put authentication, logging, validation and error mapping?
**Short answer (45 seconds):** Middleware first, then guards, interceptors before the handler, pipes, the controller method and its services, the same interceptors after the handler on the returned stream, and exception filters for anything thrown on the way. Inside each stage the order is global, controller, route, except that after-handler interceptors and filters go from the route outward. So authentication is a guard, timing and structured logging an interceptor, validation a global ValidationPipe, and domain error mapping an exception filter.

**Deeper explanation:**

```text
middleware            global, then module (consumer.apply)
guards                global -> controller -> route
interceptors (pre)    global -> controller -> route
pipes                 global -> controller -> route -> parameter
handler -> service
interceptors (post)   route -> controller -> global    (RxJS stream)
exception filters     route -> controller -> global    (only on throw)
adapter reply         res.json / reply.send
```

Register the global pieces as providers, so they get DI and also apply in tests:

```ts
@Module({
  providers: [
    { provide: APP_GUARD, useClass: JwtAuthGuard },
    { provide: APP_INTERCEPTOR, useClass: LoggingInterceptor },
    { provide: APP_PIPE, useValue: new ValidationPipe({ whitelist: true, transform: true }) },
    { provide: APP_FILTER, useClass: DomainErrorFilter },
  ],
})
export class CoreModule {}
```

The order has consequences. Guards run before interceptors, so a logging interceptor never sees a request a guard rejected; if the access log must include 401s and 403s, log in middleware on res `finish`. Pipes run after interceptors, so an interceptor sees raw, unvalidated arguments. And `whitelist: true` strips properties with no validation decorator, closing mass-assignment holes such as a client sending `role: "admin"`.

**Follow-ups they will ask:**
- Which filter handles an exception when route and global filters both match? : only the most specific one; filters do not chain.
- Can an interceptor skip the handler? : yes, return an Observable such as `of(cached)` without calling next.handle(), which is how cache interceptors work.

**Mistakes to avoid:**
- Authenticating in middleware when the rule depends on handler metadata such as @Public(); middleware cannot see the handler.
- Throwing plain Error objects for expected failures, which the built-in filter turns into 500s.

### Q. How does NestJS dependency injection work under the hood, and what are provider scopes?
**Short answer (45 seconds):** Decorators store metadata, and TypeScript, with emitDecoratorMetadata on, records each decorated class's constructor parameter types under `design:paramtypes`. At boot the injector uses those types, or @Inject tokens, as keys, finds a provider for each in the module or in the exports of modules it imports, builds dependencies first and caches the instances. DEFAULT scope is one instance per registering module for the app's life, REQUEST builds a new instance per request, and TRANSIENT gives every consumer its own instance.

**Deeper explanation:**

```ts
export const LLM_CLIENT = Symbol('LLM_CLIENT');

@Injectable()
export class ChatService {
  constructor(
    private readonly repo: ConversationsRepo,            // token: the class
    @Inject(LLM_CLIENT) private readonly llm: LlmClient,  // interface emits as Object, so use a token
  ) {}
}
// emitted roughly: Reflect.metadata('design:paramtypes', [ConversationsRepo, Object])
// @Inject adds 'self:paramtypes' [{ index: 1, param: LLM_CLIENT }], which wins at index 1

@Injectable({ scope: Scope.REQUEST })
export class TenantContext {
  constructor(@Inject(REQUEST) readonly req: Request) {}
}
```

Request scope bubbles up the injection chain. A singleton cannot hold a per-request object, so every provider that depends on TenantContext becomes request scoped, and so on up to the controller. One request-scoped class deep in a repository turns the whole chain into per-request instantiation, lifecycle hooks stop running for those classes, and latency rises under load. Alternatives: pass context explicitly, use AsyncLocalStorage (nestjs-cls), or in recent versions durable providers, built once per tenant through a ContextIdStrategy. TRANSIENT does not bubble: a singleton that injects a transient provider stays a singleton with a private copy.

**Follow-ups they will ask:**
- What does "Nest can't resolve dependencies of X (?)" mean? : the token at that index is not visible in this module, or it is undefined because of a circular file import.
- Is a provider listed in two modules shared? : no, each listing module gets its own instance; provide it once and export it.
- Why does DI break under Vitest? : esbuild does not emit decorator metadata; compile with SWC, for example through unplugin-swc.

**Mistakes to avoid:**
- Making a service request scoped only to read the current user.

### Q. Modules, global modules and dynamic modules: how do you design them, and how do you handle circular dependencies?
**Short answer (45 seconds):** A module is a visibility boundary: its providers are private unless exported, and only modules that import it can inject them. I make one module per feature or bounded context, a few infrastructure modules for config, database and LLM clients, and keep global scope for cross-cutting things like config and logging. Dynamic modules (forRoot, forRootAsync, forFeature) build providers from options. forwardRef makes a circular dependency work, but I treat it as a smell and refactor: extract the shared part into a third module, or invert the dependency with events.

**Deeper explanation:**

```ts
@Module({})
export class LlmModule {
  static forRootAsync(): DynamicModule {
    return {
      module: LlmModule,
      imports: [ConfigModule],
      providers: [{
        provide: LLM_CLIENT,
        inject: [ConfigService],
        useFactory: (cfg: ConfigService) => new OpenAI({ apiKey: cfg.getOrThrow('OPENAI_API_KEY') }),
      }],
      exports: [LLM_CLIENT],
    };
  }
}
```

The names carry meaning: forRoot configures once at the root, forFeature registers per-module pieces (TypeOrmModule.forFeature([User]) gives that module its repository), and register means configuration per import. In recent versions ConfigurableModuleBuilder generates this boilerplate.

Circular dependencies come in two kinds. A file-level import cycle, often through barrel index.ts files, leaves a class undefined at decoration time, so the injector sees undefined at that index. A DI-level cycle, OrdersService needing PaymentsService and back, needs forwardRef(() => X) on both sides, and construction order becomes indeterminate, so neither constructor may use the other. The better fix is structural: move shared logic (pricing, say) into a PricingModule both import, or have Payments emit `payment.captured` through @nestjs/event-emitter and let Orders react.

**Follow-ups they will ask:**
- Is a module instantiated once? : a static module is a singleton however often it is imported; dynamic modules with different options become separate instances.
- When is @Global() justified? : config, logging and similar; for feature services, explicit imports document the dependency graph.

**Mistakes to avoid:**
- One giant SharedModule that every feature imports, which hides coupling and recreates cycles.
- Reaching for forwardRef as the fix instead of asking why two features depend on each other.

### Q. Guards vs middleware vs interceptors vs pipes: how do you choose?
**Short answer (45 seconds):** I choose by what the code needs to know and when it must run. If it needs only the raw request and runs before Nest picks a handler (helmet, CORS, request ids, raw body capture), it is middleware. If it decides whether the handler may run, especially from metadata like @Roles() or @Public(), it is a guard. If it wraps the handler, timing it or reshaping the result, it is an interceptor. If it validates or converts one argument, it is a pipe. Turning an exception into a response is a filter.

**Deeper explanation:** A guard honouring @Public() shows why guards exist: they can see the handler.

```ts
export const Public = () => SetMetadata('isPublic', true);

@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(private readonly reflector: Reflector, private readonly jwt: JwtService) {}

  async canActivate(ctx: ExecutionContext): Promise<boolean> {
    const isPublic = this.reflector.getAllAndOverride<boolean>('isPublic', [ctx.getHandler(), ctx.getClass()]);
    if (isPublic) return true;
    const req = ctx.switchToHttp().getRequest();
    const token = req.headers.authorization?.replace(/^Bearer /, '');
    try {
      req.user = await this.jwt.verifyAsync(token);
      return true;
    } catch {
      throw new UnauthorizedException();
    }
  }
}
```

Two more criteria. Transport: guards, interceptors, pipes and filters receive an ExecutionContext or ArgumentsHost that also works for WebSocket gateways and microservices (switchToWs, switchToRpc), while middleware is HTTP only. Position: a guard runs before pipes, so it sees the raw body, never the validated DTO; base access decisions on the token, params or headers, and do ownership checks in the service.

**Follow-ups they will ask:**
- Where does rate limiting go? : a guard; @nestjs/throttler ships ThrottlerGuard, so per-route limits come from metadata.
- Middleware or interceptor for logging? : an interceptor for handler timing, middleware on res `finish` when every request, including rejected ones, must be logged.

**Mistakes to avoid:**
- Putting business logic in interceptors or pipes, where nobody reading the handler can see it.
- Using middleware for authorization out of Express habit, then duplicating route lists in forRoutes() to know which paths are public.

### Q. What does NestJS add over raw Express, what does it cost, and when would you switch the adapter to Fastify?
**Short answer (45 seconds):** Over raw Express, NestJS adds a DI container with modules as visibility boundaries, a declarative pipeline of guards, interceptors, pipes and filters, one ExecutionContext model shared by HTTP, WebSockets, microservices and GraphQL, a testing module that swaps providers, and a consistent ecosystem (config, Swagger from decorators, ORMs, BullMQ, CQRS). It costs startup time, a build that must emit decorator metadata, deeper stack traces, and ceremony that is overkill for small services. I switch to the Fastify adapter when a JSON-heavy service needs more throughput per pod and nothing depends on Express-only middleware.

**Deeper explanation:**

```ts
import { NestFactory } from '@nestjs/core';
import { FastifyAdapter, NestFastifyApplication } from '@nestjs/platform-fastify';

async function bootstrap() {
  const app = await NestFactory.create<NestFastifyApplication>(AppModule, new FastifyAdapter());
  await app.listen(3000, '0.0.0.0');   // Fastify binds to localhost only unless given a host
}
bootstrap();
```

Per-request overhead is modest because Nest composes each route's guard, interceptor and pipe chain once at boot; the bigger runtime cost is often class-transformer and class-validator on large payloads. On Fastify you gain its radix-tree router and lower framework overhead, but by default Nest does not hand Fastify response schemas built from your DTOs, so you miss the schema-compiled serialization behind Fastify's headline benchmarks. Measure with autocannon before and after.

The migration checklist: express-session, multer and helmet become Fastify plugins (@fastify/session, @fastify/multipart, @fastify/helmet); @Req() and @Res() give FastifyRequest and FastifyReply, with different APIs; the host argument matters in containers; and e2e tests must wait for the Fastify instance to be ready.

**Follow-ups they will ask:**
- Does Nest suit serverless? : cold starts pay for scanning and instantiation every time; keep the module graph lean and use LazyModuleLoader for rarely used modules.
- What happens if a handler injects @Res()? : Nest stops sending the response, so result-mapping interceptors no longer apply unless you set `passthrough: true`.

**Mistakes to avoid:**
- Promising raw Fastify benchmark numbers from a Nest app on the Fastify adapter.
- Adopting Nest for a three-endpoint service where an Express or Fastify app with a composition root is simpler.

### Q. How do you test a NestJS application?
**Short answer (45 seconds):** Three levels. Unit tests create the class directly, or through Test.createTestingModule with just that provider and mocked dependencies via `{ provide, useValue }`. E2e tests import the real AppModule, replace the edges with overrideProvider (LLM client, payment gateway, mailer), call createNestApplication() and app.init(), and drive real HTTP with supertest against app.getHttpServer(). Guards and interceptors are plain classes, so they get unit tests with a fake ExecutionContext and CallHandler, plus e2e coverage of the wiring.

**Deeper explanation:**

```ts
describe('POST /users (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(LLM_CLIENT).useValue({ complete: jest.fn().mockResolvedValue('hi') })
      .overrideProvider(JwtAuthGuard).useValue({ canActivate: () => true })
      .compile();
    app = moduleRef.createNestApplication();
    await app.init();
  });
  afterAll(() => app.close());

  it('rejects an invalid body with 400', () =>
    request(app.getHttpServer()).post('/users').send({ email: 'nope' }).expect(400));
});
```

The traps are about what the test app does not contain. Anything configured in main.ts (useGlobalPipes, enableCors, versioning) is missing unless it is registered as APP_PIPE and similar providers, or main.ts and the tests share one setup function. overrideGuard targets guards bound with @UseGuards; for a global guard, register `{ provide: APP_GUARD, useExisting: JwtAuthGuard }` plus JwtAuthGuard itself, then override that provider as above. Request-scoped and transient providers need `moduleRef.resolve()` instead of get(). For an interceptor, `await lastValueFrom(interceptor.intercept(ctx, { handle: () => of(result) }))` tests the after-handler logic without HTTP. Use a real Postgres in Testcontainers, since query bugs are what ORM mocks hide.

**Follow-ups they will ask:**
- How do you mock every dependency at once? : `useMocker()` on the testing module with a factory such as createMock from @golevelup/ts-jest.
- What changes on the Fastify adapter? : await the Fastify instance's ready() after init, or use Fastify's inject() instead of supertest.

**Mistakes to avoid:**
- Forgetting app.close(), which leaves pools and handles open and makes Jest report that it did not exit.
- Mocking so much in e2e tests that the guard, pipe and filter wiring is never really exercised.

### Practice
- Create a fresh Nest app with a middleware, guard, interceptor (logging before and after), pipe and filter that each log their name, bound globally, on a controller and on a route; send a valid request, an invalid body and an unauthenticated request, and write down the order each time.
- Mark one service `Scope.REQUEST`, log in its constructor and in the constructors of everything that injects it, and load test with autocannon against the default scope; then replace it with nestjs-cls and compare the constructor logs.
- Create a circular dependency between OrdersService and PaymentsService, read the boot error, fix it with forwardRef, then remove forwardRef by extracting a PricingModule or emitting an event.
- Write one e2e test that overrides the LLM client provider and one unit test for the guard with a fake ExecutionContext; then switch the adapter to Fastify and note what breaks.
- Say it out loud: in under two minutes, explain how Nest boots (scan, metadata, injection, routes, hooks, listen), then trace one authenticated POST through every lifecycle stage and name where its validation error would be turned into a 400.
