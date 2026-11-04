# Software Design

> This track covers the design principles, design patterns, architectural patterns and folder structures interviewers expect a senior backend or full stack engineer to apply and defend, with examples from Express, NestJS and FastAPI. Senior rounds rarely stop at definitions: they hand you a tangled service or a design choice and watch whether you can name the forces at play, refactor toward a cleaner shape, and say when the cleaner shape is not worth the extra code.

## SOLID Principles [Core]

> Interviewers use SOLID to check whether you design for change or only recite acronyms. A weak answer gives five textbook definitions with shapes and animals and falls apart at the first follow-up ("is that an LSP problem or an ISP one?"). A strong answer takes one real service, names the smell each principle fixes, shows the refactor in Express, NestJS or FastAPI, explains what got easier to test, and says where applying the principle would have been over-engineering.

### In plain words
Think of a small restaurant where one person takes orders, cooks, handles the cash and washes the dishes. It works on a quiet day, but every change, a new dish, a new card machine, a new rule about receipts, lands on the same tired person, and one mistake ruins everything at once. A well-run kitchen splits the work into stations, keeps a menu you can add dishes to without rebuilding the kitchen, and lets any trained cook cover a shift because every cook follows the same rules. Each station gets only the tools it needs, and the chef orders "fresh tomatoes" from whichever supplier is under contract instead of being tied to one farm. SOLID is the same set of habits for code: five rules that keep each part small, replaceable and safe to change. They matter most where code changes often, and much less in code nobody touches.

- **S, Single Responsibility:** each part of the code has one owner and one reason to change, so one kind of change touches one place.
- **O, Open/Closed:** you add new behavior by adding new code, not by editing code that already works.
- **L, Liskov Substitution:** anything that claims to be a kind of X must behave like an X, with no nasty surprises.
- **I, Interface Segregation:** give each user of a component only the methods it needs, not a giant menu.
- **D, Dependency Inversion:** business logic depends on simple contracts it defines, and databases or vendors plug into those contracts.

### Walkthrough: refactoring one service with all five principles
1. **Fat `OrderService`**: One Express service has a `placeOrder(body)` method that validates fields by hand, applies `if (tier === 'gold')` discount rules, calls Mongoose models, sends mail through Nodemailer and writes `console.log` lines. Every change, from a coupon rule to an email template, edits this one file, and its tests need MongoDB and an SMTP mock.
2. **SRP: list the reasons to change**: Product owns validation rules, marketing owns discounts, the data team owns storage, CRM owns emails and ops owns logging. Each actor gets its own unit: a `PlaceOrderDto` validated at the edge, `PricingService`, `OrderRepository`, `OrderNotifier` and a request-logging middleware.
3. **SRP: keep a thin orchestrator**: `OrderService.placeOrder` now only coordinates the use case: price, save, charge, notify. It reads like the business process and contains no queries, templates or HTTP details.
4. **OCP: discount strategy**: The if/else chain becomes a `DiscountRule` interface (`appliesTo(order)`, `apply(total, order)`) with one class per rule, such as `GoldTierDiscount` and `FestiveCouponDiscount`. `PricingService` receives an array of rules, so a new campaign is a new class registered at startup, not an edit to pricing code.
5. **LSP: check the payment hierarchy**: Payments go through a `PaymentProvider` base class with `charge()` and `refund()`, and `CashOnDeliveryProvider` throws from `refund()`. Callers would need `instanceof` checks, so the hierarchy is split into `Chargeable` and `Refundable` capabilities and only providers that can refund claim to.
6. **ISP: split the fat repository**: The old `IOrderRepository` had CRUD, reporting aggregates, bulk admin updates and CSV export, and every test fake had to stub all of it. It becomes `OrderReader`, `OrderWriter` and `OrderReporting`, and one `MongoOrderRepository` class can still implement all three.
7. **DIP: depend on abstractions you own**: `OrderService` now imports only interfaces defined next to it (`OrderWriter`, `Chargeable`, `OrderNotifier`), never `mongoose`, `stripe` or `nodemailer`. The Mongo, Stripe and SMTP adapters import and implement those interfaces, so the source-code dependency points from detail to policy.
8. **DIP: wire through constructors**: In NestJS each adapter is a provider bound to a token, `{ provide: ORDER_WRITER, useClass: MongoOrderRepository }`, and injected with `@Inject(ORDER_WRITER)`. In plain Express a composition root (`app.ts` or `container.ts`) builds the real objects once and passes them into `new OrderService(...)`.
9. **What got easier to test**: `OrderService` unit tests pass in-memory fakes for the writer, payments and notifier, need no database or SMTP server, and run in milliseconds. Each discount rule gets a small table-driven test, and only `MongoOrderRepository` needs integration tests against a real MongoDB.
10. **What it cost**: The feature now spans about eight small files instead of one, and reading the flow means following interfaces. The trade pays off here because five different actors change this service often; a rarely touched admin script would not earn it.

### Concepts you must understand
- SRP is about reasons to change, and Robert Martin's later wording ties it to actors: a module should answer to one group of people who request changes, not merely "do one thing".
- OCP is achieved with polymorphism at a variation point (strategy objects, plugin registries, middleware chains); it says stable callers should not change when a new variant appears, not that code is never edited.
- LSP is a behavioral contract: a subtype may not strengthen preconditions, weaken postconditions, break invariants or throw errors the caller was not promised. Type checkers verify signatures, not behavior.
- ISP shapes interfaces around consumers: each client sees a narrow role interface, and one concrete class may implement several of them.
- DIP says business policy owns the abstraction and infrastructure implements it; dependency injection is the technique that supplies implementations, and an IoC container such as NestJS's only automates that wiring.
- In TypeScript (structural typing) and Python (`typing.Protocol`, duck typing) interfaces are cheap, so ISP and DIP cost little, while LSP violations often surface only at runtime.
- The five reinforce each other: SRP finds the parts, OCP and DIP decide how they plug together, and LSP and ISP keep the plug-in contracts honest.
- SOLID is a tool for managing change and testability; it earns its cost where change pressure or I/O boundaries exist, and becomes ceremony elsewhere.

| Principle | One-line meaning | Smell that shows it is broken | Typical fix |
|---|---|---|---|
| SRP | One module answers to one actor and one reason to change | A 1,500-line `OrderService`; two teams' merge conflicts in one file; unit tests that need a database, SMTP and HTTP mocks | Split by responsibility and keep a thin orchestrator for the use case |
| OCP | Add behavior by adding code, not by editing tested code | A `switch` on tier, provider or type that grows with every release | Strategy interface, registry map or plugin hook at the variation point |
| LSP | Subtypes work wherever the base type is expected, without surprises | `instanceof` checks in callers; overrides that throw "not supported"; subclasses that ignore arguments | Redesign the hierarchy, split capabilities, or use composition |
| ISP | Clients depend only on the methods they use | Fakes stubbing twelve methods to test one; empty or throwing method bodies | Split into role interfaces or Protocols per consumer |
| DIP | Policy depends on abstractions it owns; details plug in | `new MongoClient()` or `new OpenAI()` inside business logic; `jest.mock` of modules in every test | Constructor injection, ports and adapters, a composition root or DI container |

### Q. What does the Single Responsibility Principle really mean, and how do you decide where to split a class?
**Short answer (45 seconds):** SRP says a module should have one reason to change; Robert Martin later sharpened that to being responsible to one actor, the group of people whose requests change it. It does not mean one method. I split by asking who requests each kind of change: if product owns validation, marketing owns discounts and CRM owns email templates, those changes collide in one class and belong apart, coordinated by a thin use-case method.

**Deeper explanation:** The usual violation is the fat service method:

```ts
// Before: five reasons to change in one method
async placeOrder(body: any) {
  if (!body.items?.length) throw new BadRequestError('items required'); // validation
  let total = body.items.reduce((s, i) => s + i.price * i.qty, 0);
  if (body.tier === 'gold') total *= 0.9;                               // pricing
  const order = await OrderModel.create({ ...body, total });             // persistence
  await mailer.sendMail({ to: body.email, subject: 'Order placed' });    // email
  console.log('order created', order.id);                                // logging
  return order;
}

// After: the use case only coordinates
async placeOrder(cmd: PlaceOrderCommand) {
  const total = this.pricing.totalFor(cmd);
  const order = await this.orders.save({ ...cmd, total });
  await this.notifier.orderPlaced(order);
  return order;
}
```

Validation moves to the edge (a DTO with `ValidationPipe` in NestJS, a Pydantic model in FastAPI) and logging to middleware or an interceptor. Symptoms of SRP trouble: unrelated features break together, two teams edit one file, and tests need half the infrastructure to check one rule. The opposite failure is ten one-method classes that always change together: low cohesion spread across files.

**Follow-ups they will ask:**
- Does SRP apply to functions and services?: Yes; for functions it means one level of abstraction, for services splitting by business capability.
- Is the orchestrator an SRP violation?: No, coordinating the use case is its one job.
- How do you find split points in legacy code?: Group methods by the fields and dependencies they touch, and check `git log` for parts that change together.

**Mistakes to avoid:**
- Defining SRP as "a class has one method", which causes fragmentation.
- Splitting only by technical layer while every business rule still lives in one god service.

### Q. Explain the Open/Closed Principle with an example from a real service.
**Short answer (45 seconds):** Code should be open for extension and closed for modification: a new variant means a new unit, not edits to code that already works and is tested. In practice you find the axis that keeps changing, such as discount rules, payment providers or LLM vendors, and put a polymorphic seam there, usually a strategy interface or a registry, so callers stay untouched when the next variant ships.

**Deeper explanation:** A pricing method whose `if (tier === 'gold') ... else if (coupon === 'DIWALI')` chain grows every sale season is the classic case. With a strategy:

```ts
interface DiscountRule {
  appliesTo(order: Order): boolean;
  apply(total: number, order: Order): number;
}

class GoldTierDiscount implements DiscountRule {
  appliesTo(order: Order) { return order.customer.tier === 'gold'; }
  apply(total: number) { return total * 0.9; }
}

class PricingService {
  constructor(private readonly rules: DiscountRule[]) {}
  totalFor(order: Order): number {
    const base = order.items.reduce((sum, i) => sum + i.price * i.qty, 0);
    return this.rules
      .filter((r) => r.appliesTo(order))
      .reduce((total, r) => r.apply(total, order), base);
  }
}
```

A new campaign is a new class added to the rules array in the composition root or a NestJS `useFactory` provider. The stacking order of rules becomes explicit business policy that deserves its own test table. Express middleware, NestJS interceptors, Passport strategies and FastAPI dependencies all add behavior this way, without editing the core.

**Follow-ups they will ask:**
- How do you handle conflicting rules?: Make the policy explicit, for example a priority field plus "best single discount" or "stack all", covered by table-driven tests.
- Could rules be data instead of classes?: Yes, when business users edit them; store conditions as JSON for one engine, and OCP then applies to the engine's operators.
- Does OCP mean code is never modified?: No; bugs still mean edits, and the composition root changes per variant. Stable callers do not.

**Mistakes to avoid:**
- Adding a strategy interface to a two-case `if` that never changes: abstraction cost with nothing to absorb.
- Using subclass chains such as `FestivePricingService extends PricingService` as the extension mechanism, coupling every variant to the base.

### Q. What is the Liskov Substitution Principle, and how can a subclass break it even when the types compile?
**Short answer (45 seconds):** LSP says code written against a base type must keep working correctly with any subtype. It is a behavioral contract: a subtype may not demand more of its inputs, promise less in its outputs, break invariants, or throw errors callers were not told to expect. Compilers check signatures, so most LSP breaks compile cleanly.

**Deeper explanation:**

```ts
abstract class PaymentProvider {
  abstract charge(orderId: string, amount: number): Promise<string>; // chargeId
  abstract refund(chargeId: string, amount: number): Promise<void>;
}

class CashOnDeliveryProvider extends PaymentProvider {
  async charge(orderId: string) { return `cod_${orderId}`; }
  async refund(): Promise<void> {
    throw new Error('COD cannot refund'); // breaks the contract
  }
}
```

A refund job written against `PaymentProvider` now fails at runtime for COD orders, and the usual patch, an `instanceof` check, spreads subtype knowledge into callers and breaks OCP too. Model capabilities honestly instead:

```ts
interface Chargeable { charge(orderId: string, amount: number): Promise<string>; }
interface Refundable { refund(chargeId: string, amount: number): Promise<void>; }
class StripeProvider implements Chargeable, Refundable { /* ... */ }
class CashOnDeliveryProvider implements Chargeable { /* ... */ }
```

The refund service now asks for a `Refundable`, so the compiler refuses a COD provider. Other quiet breaks: accepting only INR where the base accepted any currency (stronger precondition), returning `null` where the base guaranteed a value (weaker postcondition), and a mutable Square overriding Rectangle's setters (broken invariant). TypeScript checks method parameters bivariantly even under `strictFunctionTypes`, so narrowing a parameter type in an override still compiles; mypy flags incompatible overrides, but no checker sees behavior.

**Follow-ups they will ask:**
- How do you test for LSP?: Contract tests: one shared suite run against every implementation (Jest `describe.each`, parametrized pytest fixtures); needing to skip a test signals a wrong hierarchy.
- How does LSP relate to ISP?: An "unsupported operation" override is usually fixed by an ISP split.

**Mistakes to avoid:**
- Saying LSP means "a subclass can be assigned to a parent variable": that is plain subtyping, which the compiler already enforces.
- Accepting `throw new NotImplementedError()` in a concrete subclass as normal.

### Q. What is the Interface Segregation Principle, and how does it apply in TypeScript or Python?
**Short answer (45 seconds):** ISP says no client should be forced to depend on methods it does not use: define narrow role interfaces shaped by each consumer, and let one concrete class implement several. In TypeScript and Python this is almost free, because structural typing (TS interfaces, `typing.Protocol`) lets a class satisfy an interface without declaring it.

**Deeper explanation:** A repository with CRUD, revenue aggregates, bulk status updates and CSV export forces every consumer and test fake to know about all of it, and a signature change in reporting ripples into unrelated code.

```python
from datetime import date
from typing import Protocol

class OrderReader(Protocol):
    async def get(self, order_id: str) -> Order | None: ...

class OrderWriter(Protocol):
    async def save(self, order: Order) -> None: ...

class RevenueReport(Protocol):
    async def revenue_by_day(self, start: date, end: date) -> list[DailyRevenue]: ...

async def cancel_order(order_id: str, reader: OrderReader, writer: OrderWriter) -> None:
    order = await reader.get(order_id)
    if order is None:
        raise OrderNotFound(order_id)
    order.cancel()
    await writer.save(order)
```

One `PostgresOrderRepo` with all three methods satisfies all three Protocols without inheriting from them, and the `cancel_order` test passes a two-method fake. For AI features, handing an agent's tool layer an `OrderReader` instead of the full repository means it cannot call delete at all: least privilege enforced by the interface. At the API level, a backend for frontend or GraphQL field selection fixes the same smell.

**Follow-ups they will ask:**
- Doesn't this cause interface explosion?: Split by consumer role, not by method; two or three role interfaces per aggregate is typical, created when a second consumer with different needs appears.
- How does this relate to CQRS?: A reader and writer split is the small version; full CQRS adds separate read models and often separate stores.
- Do you need `@runtime_checkable`?: Only if you call `isinstance` against the Protocol; static checking with mypy or Pyright needs nothing extra.

**Mistakes to avoid:**
- Creating one interface per method everywhere, which scatters a cohesive contract.
- Hiding a fat interface behind partial mocks cast with `as unknown as IOrderRepository` instead of fixing it.

### Q. What is the Dependency Inversion Principle, and how is it different from dependency injection?
**Short answer (45 seconds):** DIP says high-level business policy should not depend on low-level modules such as database drivers, HTTP clients or vendor SDKs; both depend on abstractions, and the abstraction belongs to the policy side. Dependency injection is only the technique of handing dependencies in from outside, usually through the constructor, and an IoC container like NestJS's automates it. You can inject a concrete `MongoClient` and still violate DIP, and you can follow DIP with no container at all.

**Deeper explanation:** "Inversion" refers to the direction of the source-code dependency. Without DIP, `OrderService` imports `mongoose`. With DIP, the orders module defines an `OrderWriter` port, and `MongoOrderRepository` imports and implements it, so the arrow points from detail to policy. This is the core of hexagonal (ports and adapters) and clean architecture.

```ts
export const ORDER_WRITER = Symbol('ORDER_WRITER');
export interface OrderWriter { save(order: NewOrder): Promise<Order>; }

@Injectable()
export class OrderService {
  constructor(@Inject(ORDER_WRITER) private readonly orders: OrderWriter) {}
}

@Module({
  providers: [OrderService, { provide: ORDER_WRITER, useClass: MongoOrderRepository }],
})
export class OrdersModule {}
```

The token exists because TypeScript interfaces are erased at compile time, so Nest has no runtime value to look up; an abstract class also works as a token. In tests, `Test.createTestingModule(...).overrideProvider(ORDER_WRITER).useValue(fakeWriter)` swaps the adapter. In FastAPI the same role is played by `Depends(get_order_writer)`, with `app.dependency_overrides[get_order_writer]` in tests.

**Follow-ups they will ask:**
- Does every class need an interface?: No; invert dependencies that cross a boundary (I/O, vendor SDKs, anything you fake in tests or may swap), and import pure domain helpers directly.
- What is a composition root?: The one place at startup, such as `main.ts` or an app factory, where concrete implementations are built and wired; nothing else calls `new` on infrastructure.
- What about a service locator?: Pulling from a global container inside business code hides dependencies; constructor injection keeps them visible.

**Mistakes to avoid:**
- Equating DIP with "we use a DI container".
- Writing a port that mirrors the vendor SDK, such as OpenAI-specific parameters; a port should speak the domain's language, or the policy is still coupled to the detail.

### Q. How do SOLID principles show up in a NestJS or FastAPI codebase you have built?
**Short answer (45 seconds):** Answer with one real feature, not definitions. In an LLM-backed support assistant, for example: routers or controllers handle only HTTP, DTOs or Pydantic models validate input, a service holds the use case, repositories and model clients sit behind ports, and DI picks the provider from config. Then name one place you broke a principle and how you fixed it.

**Deeper explanation:**

| Principle | NestJS | FastAPI |
|---|---|---|
| SRP | Controller, service, repository, DTO with `ValidationPipe`, logging interceptor | Router, Pydantic model, service, repository, middleware |
| OCP | New guard, interceptor or strategy provider | New dependency or strategy dict entry |
| LSP | Each `ChatModel` adapter passes a shared contract suite | Same suite as a parametrized fixture |
| ISP | Separate `ChatModel` and `EmbeddingModel` ports | Small Protocols per consumer |
| DIP | `useFactory` picks the adapter from `ConfigService` | `Depends(get_chat_model)`, overridden in tests |

```python
class ChatModel(Protocol):
    async def complete(self, messages: list[dict]) -> str: ...

def get_chat_model(settings: Settings = Depends(get_settings)) -> ChatModel:
    if settings.llm_provider == "anthropic":
        return AnthropicChat(settings.anthropic_api_key)
    return OpenAIChat(settings.openai_api_key)

@router.post("/ask")
async def ask(q: Question, model: ChatModel = Depends(get_chat_model)) -> Answer:
    return await answer_question(q, model)

# test: app.dependency_overrides[get_chat_model] = lambda: FakeChat("scripted reply")
```

A credible story includes the mess: a `UtilsService` injected everywhere, or two modules that needed `forwardRef`, and how you extracted the shared piece or replaced the call with an event.

**Follow-ups they will ask:**
- How do you avoid circular module dependencies in NestJS?: Treat `forwardRef` as a smell; extract the shared logic into its own module or emit an event.
- Where does validation live?: At the edge, in DTOs or Pydantic models, so services receive typed, already valid commands.
- How do you test code that calls an LLM?: Inject a fake model with scripted replies and tool calls, plus a smaller eval suite against the real provider.

**Mistakes to avoid:**
- Claiming NestJS gives you SOLID for free: a 2,000-line service with ten injected repositories is still a god class.
- Listing principles without one concrete class, file or decision from your own work.

### Q. When does applying SOLID become over-engineering, and how do you decide?
**Short answer (45 seconds):** It becomes over-engineering when abstractions serve imagined change: an interface with one implementation and no test fake, a strategy for a two-case `if` that never changes, a factory that builds one class. I decide with evidence: has this axis changed before, is a second implementation planned, do I need a seam for tests, does it cross an I/O or vendor boundary. If none apply, I write direct code and refactor when the second real case shows up.

**Deeper explanation:** Every abstraction costs files, indirection while debugging and names to maintain, and a wrong abstraction is harder to remove than duplication because callers depend on its shape. Put seams at I/O boundaries (database, queue, payments, LLM API) almost always, since those are slow to test and likely to be faked or swapped; inside pure domain logic, plain functions are enough until a variation point proves itself.

```text
Add an abstraction when at least one is true:
  - a second implementation exists or is scheduled
  - the code crosses I/O or a vendor SDK and needs a test fake
  - this branch changed several times recently (check git history)
  - different actors change the parts independently
Otherwise write it directly, keep it tested, refactor on the next case.
```

`git log --format= --name-only | sort | uniq -c | sort -rn | head` lists the most edited files, which is where SOLID refactors pay back.

**Follow-ups they will ask:**
- Isn't refactoring later more expensive?: Only for untested, tangled code; small tested code is cheap to refactor, and you design the seam knowing the real second case.
- Is an interface with one implementation always wrong?: No; an I/O port with a test fake already has two.
- How do you push back on an over-abstracted pull request?: Ask which second implementation or test it serves; propose inlining all but the I/O ports.

**Mistakes to avoid:**
- Scoring code against SOLID as a checklist instead of asking which change it makes cheaper.
- Using YAGNI as an excuse to call vendor SDKs straight from business logic.

### Practice
- Write or find a fat Express `OrderService` (validation, pricing, Mongo, email, logging) and refactor it step by step as in the walkthrough; record unit test runtime and the number of mocks before and after.
- Build one contract test suite with Jest `describe.each` (or a parametrized pytest fixture) and run it against an in-memory and a MongoDB implementation of the same repository port.
- In a NestJS app, choose an LLM adapter by config with a `useFactory` provider and a symbol token, then swap it in a test with `overrideProvider(TOKEN).useValue(fake)`.
- Run the `git log` churn command on a repository you know and check whether the top three files are SRP violations.
- Say it out loud: "Walk me through how you would refactor a 600-line OrderService using SOLID, and tell me which principle you would not apply there and why." Keep it under two minutes.

## Design Principles Beyond SOLID [Basics]

> These principles rarely get a question of their own; they surface inside code review and design rounds as "would you extract this?", "why not a base class?" or "why so many layers?". A weak answer quotes acronyms as rules. A strong answer treats them as forces that pull against each other (DRY against decoupling, KISS against flexibility), gives a real example of each, and names the point where following the rule starts to hurt.

### In plain words
These are the rules of thumb an experienced carpenter follows without thinking. Write each measurement down once (DRY), use the simplest joint that holds (KISS), do not build a shelf for books you do not own yet (YAGNI), and build from parts you can swap instead of carving everything from one block (composition). Each rule is good advice, and each turns into bad advice when followed blindly: a carpenter who refuses to ever cut two similar pieces ends up with strange, fragile joints. The skill is knowing which rule matters for the piece of furniture in front of you.

### Concepts you must understand
- These principles are heuristics with trade-offs, not laws; most design arguments are two of them in tension, and a senior answer names both.
- DRY is about knowledge, not identical text: one business rule, one source of truth.
- KISS and YAGNI cut cost now, but a few decisions (identity, tenant isolation, idempotency, data migrations) are expensive to change later and deserve design up front.
- Coupling and cohesion are the measures underneath most of the others: separation of concerns, the Law of Demeter and composition all aim at changes that stay local.
- Tell don't ask and the Law of Demeter apply to objects with behavior; plain data structures such as DTOs, JSON and Pydantic models may be read freely.

| Principle | Meaning | Example | Trap of overdoing it |
|---|---|---|---|
| DRY (don't repeat yourself) | Every piece of knowledge has one authoritative representation | GST rate and order status transitions defined once and used by the API and the worker; TypeScript types generated from the OpenAPI or Pydantic schema | Merging code that only looks alike into a flag-driven helper; sharing domain models across microservices so they deploy in lockstep |
| KISS (keep it simple) | Pick the simplest design that meets the real requirements | A Postgres jobs table polled by a worker instead of Kafka for a few hundred jobs a day | Simplistic designs that drop real needs such as retries, idempotency or auth |
| YAGNI (you aren't gonna need it) | Do not build features or flexibility before there is a need | No plugin system until a second integration exists | Skipping cheap-now, costly-later decisions: tenant IDs, migrations, API versioning |
| Composition over inheritance | Build behavior by combining objects or functions, not by extending base classes | A service that receives a retry policy and a cache instead of extending `BaseCachedRetryingService` | Wrapping everything in tiny delegators; refusing inheritance even for true is-a cases like custom error classes |
| Separation of concerns | Each part handles one concern: transport, rules, persistence, presentation | Controller parses HTTP, service applies rules, repository runs queries | Layers so thin that one feature change touches ten files |
| High cohesion, low coupling | Things that change together live together; modules know little about each other | An `orders/` feature folder that other modules reach only through its public service | Decoupling everything through events until no one can follow the flow |
| Law of Demeter | Talk to your direct collaborators, not to their internals | `customer.pay(amount)` instead of `order.customer.wallet.balance -= amount` | Wrapper methods for every nested field; applying it to plain data objects |
| Tell, don't ask | Tell an object what to do instead of pulling its state and deciding outside | `order.complete()` checks its own status before changing it | Pushing persistence, email and formatting into entities until they become god objects |
| Fail fast | Detect invalid state as early as possible and stop loudly | Validate env config at boot with zod or pydantic-settings; reject bad bodies with 400 or 422 at the edge | Failing a whole batch or stream on one bad record instead of routing it to a dead letter queue |
| Least astonishment | Behavior matches what users and readers expect | `GET` never mutates; `getUser` never writes; `deleteUser` does not also send a marketing email | Keeping a bad convention forever because changing it would surprise someone |
| Convention over configuration | Defaults and naming rules mean you configure only the exceptions | Next.js file-based routing, the NestJS CLI layout, FastAPI matching path parameters to function arguments by name | Hidden magic that newcomers cannot find and that is hard to debug when the convention does not fit |

### Q. DRY vs the wrong abstraction: when is duplication the better choice?
**Short answer (45 seconds):** DRY is about knowledge, not text: a business rule should have one source of truth, but two pieces of code that look alike and change for different reasons are not the same knowledge. Duplication is the better choice when the similarity is accidental, when the copies live in different bounded contexts or services, or when you have seen only two cases. I wait for a third case and for evidence that the copies really change together before extracting.

**Deeper explanation:** Sandi Metz put it as "duplication is far cheaper than the wrong abstraction". The wrong abstraction grows predictably: two similar functions get merged, a third caller needs something slightly different, so a parameter is added, then a boolean flag, then another, until nobody dares touch it.

```ts
// Six months later
function buildNotification(user: User, opts: {
  isInvoice?: boolean;
  isReminder?: boolean;
  skipFooter?: boolean;
  legacyFormat?: boolean;
}) {
  /* 120 lines of if (opts.isInvoice && !opts.legacyFormat) ... */
}
```

The way out is to inline the helper back into each caller, delete the branches each caller does not use, then re-extract only what is truly shared. DRY matters most for business rules (tax, pricing, status transitions), contracts (generate client types from the OpenAPI or Pydantic schema) and configuration. Duplication is often right across microservices, where a shared domain library couples release cycles; in tests, where explicit setup reads better; and in early code, where the right shape is not yet visible.

**Follow-ups they will ask:**
- What is the rule of three?: Tolerate the second copy and extract on the third, when you can see what actually varies.
- Should microservices share a library?: Share stable infrastructure such as logging, tracing and auth clients; keep domain models per service.
- How do you spot accidental duplication?: Ask whether changing one copy would always require changing the other; if not, they are different knowledge.

**Mistakes to avoid:**
- Treating every copy-paste warning from a linter as a DRY violation; it is a hint, not a verdict.
- Keeping a flag-ridden helper because "it is already shared".

### Q. Why prefer composition over inheritance? Show an example.
**Short answer (45 seconds):** Inheritance ties a subclass to its parent's implementation, so base changes ripple into every child (the fragile base class problem), and a hierarchy varies along only one axis. Composition builds behavior from small objects passed in, so you can mix capabilities, swap them at runtime and test each alone. I keep inheritance for real is-a cases with a stable base, such as custom error classes.

**Deeper explanation:** A `BaseLlmService` with caching and retries breaks down when one caller needs retries without caching and another needs rate limiting too; subclasses multiply per combination. Wrapping one interface avoids that:

```ts
interface ChatModel { complete(prompt: string): Promise<string>; }

class WithRetry implements ChatModel {
  constructor(private inner: ChatModel, private attempts = 3) {}
  async complete(prompt: string): Promise<string> {
    let lastError: unknown;
    for (let i = 0; i < this.attempts; i++) {
      try { return await this.inner.complete(prompt); } catch (e) { lastError = e; }
    }
    throw lastError;
  }
}

class WithCache implements ChatModel {
  constructor(private inner: ChatModel, private cache = new Map<string, string>()) {}
  async complete(prompt: string): Promise<string> {
    const hit = this.cache.get(prompt);
    if (hit !== undefined) return hit;
    const out = await this.inner.complete(prompt);
    this.cache.set(prompt, out);
    return out;
  }
}

const model: ChatModel = new WithCache(new WithRetry(new OpenAIChat()));
```

Each wrapper is tested alone with a fake `inner`, and wrapping order is explicit: cache outside retry means hits never touch the network. Real retries also add backoff and retry only transient errors (429, 5xx).

**Follow-ups they will ask:**
- Isn't this the decorator pattern?: Yes; decorator is composition around the same interface, and strategy is composition where you inject the part that varies.
- When is inheritance the right tool?: A stable is-a with shared invariants, such as `class OrderNotFound extends NotFoundException`.
- What about mixins in Python or TypeScript?: They are multiple inheritance with method resolution order surprises; keep them small and stateless.

**Mistakes to avoid:**
- Saying "inheritance is bad": it is strong coupling, fine where that coupling is intended.
- Building deep hierarchies to reuse code rather than to model substitutable types.

### Q. What do coupling and cohesion mean, and how do you measure or spot them in a codebase?
**Short answer (45 seconds):** Coupling is how much one module must know about, and change with, another; cohesion is how strongly the parts inside one module belong together. Aim for high cohesion inside modules and few, explicit, stable dependencies between them, so changes stay local. If one feature touches eight folders, cohesion is low; if editing one module breaks three others, coupling is high.

**Deeper explanation:** Coupling comes in degrees, from looser to tighter: passing simple values, passing a whole object for one field, passing a flag that picks the callee's branch, sharing global state or tables, and reaching into another module's internals. Two hurt most in backends: a database shared between services, where a schema change silently breaks a neighbor, and temporal coupling, where `init()` must run before `send()`.

| Signal | How to see it |
|---|---|
| Import cycles | `npx madge --circular --extensions ts src/`; `pydeps` graphs for Python |
| Layer violations | dependency-cruiser rules forbidding `src/domain` from importing `src/infra`; import-linter contracts run with `lint-imports` |
| Instability | Robert Martin's I = Ce / (Ca + Ce), outgoing over total dependencies; stable modules should also be abstract |
| Change coupling | Files that keep landing in the same commits in `git log --name-only` |
| Low cohesion | Methods that split into groups using disjoint fields are really two classes (LCOM metrics) |

**Follow-ups they will ask:**
- Does an event bus remove coupling?: It removes temporal and location coupling, but the event schema is still a contract, so version it.
- How do feature folders help?: They raise cohesion by keeping one capability together and make cross-module imports visible in review.
- Is a shared database always wrong?: Inside one service or a modular monolith it is fine; across independently deployed services it is one of the strongest hidden couplings.

**Mistakes to avoid:**
- Saying low coupling means no dependencies: modules must collaborate, so aim for few and explicit ones.
- Trusting a metric score over what the change history shows.

### Q. What is the Law of Demeter, and what does tell-don't-ask look like in code?
**Short answer (45 seconds):** The Law of Demeter says a method should call methods only on itself, its parameters, objects it creates and its own fields, not on objects returned by those calls: talk to friends, not to strangers. A chain like `order.customer.wallet.debit(amount)` makes the caller depend on the whole object graph. Tell-don't-ask is the companion rule: instead of asking an object for its data and deciding outside, tell it what you want and let it enforce its own rules.

**Deeper explanation:**

```ts
// Ask: every caller re-implements the rule
if (order.status === 'PAID' && order.items.every((i) => i.shipped)) {
  order.status = 'COMPLETED';
  order.completedAt = new Date();
}

// Tell: the entity owns the rule and its invariant
class Order {
  complete(now = new Date()): void {
    if (this.status !== 'PAID') throw new InvalidTransition(this.status, 'COMPLETED');
    if (!this.items.every((i) => i.shipped)) throw new ItemsPending(this.id);
    this.status = 'COMPLETED';
    this.completedAt = now;
  }
}
```

The admin endpoint, the shipping webhook and the nightly worker now all get the same rule, and nobody can skip the invariant by forgetting one condition. For Demeter, replace `order.customer.wallet.debit(amount)` with `payments.debit(order.customerId, amount)` or `customer.pay(amount)`, so the caller knows one collaborator instead of three.

Two caveats make the answer senior. The law targets objects with behavior, not data: reading `req.body.address.city` from a DTO or Pydantic model is fine. And fluent query builders such as Knex or SQLAlchemy return the same kind of object at each step, so their chains are not violations.

**Follow-ups they will ask:**
- Many Express and FastAPI apps keep logic in services over plain data models; is that wrong?: Not for simple CRUD; move a rule into the entity once its invariant is duplicated.
- How does this help testing?: Callers fake one collaborator instead of building deep mock chains, which are a Demeter smell in themselves.
- Does tell-don't-ask conflict with read endpoints?: No; commands tell, while read paths for display can pull data freely.

**Mistakes to avoid:**
- Applying a literal "one dot" rule to DTOs and fluent builders.
- Moving persistence and email into entities in the name of tell-don't-ask, which mixes concerns.

### Q. How do KISS and YAGNI change the way you design an MVP versus a platform?
**Short answer (45 seconds):** For an MVP the biggest risk is building the wrong thing, so KISS and YAGNI dominate: a modular monolith, one Postgres, direct code, managed services. For a platform other teams build on, the risk is breaking consumers, so I invest early in stable contracts, versioning, extension points and observability. Either way I separate decisions that are cheap to change later from the few that are expensive, and design only the second group carefully.

**Deeper explanation:**

| Decision | MVP | Platform |
|---|---|---|
| Architecture | Modular monolith, feature folders | Owned modules or services with published APIs |
| Async work | Postgres jobs table, BullMQ or Celery | Kafka or a managed stream for many consumers |
| Extensibility | One provider behind a thin adapter | Documented extension points, strategy interfaces, SDKs |
| APIs | Internal, changed together with the client | Versioned, backward compatible, deprecation policy |
| LLM features | One prompt, one model call, logged | Provider abstraction, evals, per-tenant rate limits and cost tracking |

Some MVP decisions are cheap now and painful later, so YAGNI should not decide them: authentication and tenant isolation (a `tenant_id` on every row if multi-tenancy is likely), the ID format, idempotency keys on payment and webhook handlers, a migration tool from the first table, request IDs in logs, and secrets out of code. A broker, a cache or microservices can come when measurements ask for them, as long as core flows are tested and I/O sits behind thin adapters.

**Follow-ups they will ask:**
- When do you switch to platform thinking?: When a second team or external customer depends on the interface, or the same change keeps recurring: evidence, not the calendar.
- Is a microservices MVP ever right?: Rarely; only when compliance isolation, very different scaling needs or team structure demand it from day one.
- How do you keep an MVP refactorable?: Tests on core flows, folder-level module boundaries, vendors behind adapters.

**Mistakes to avoid:**
- Using YAGNI to skip security, tenant isolation or idempotency.
- Building plugin systems and event buses before the first user.

### Practice
- Find a helper with boolean flags in a codebase you know, inline it into its callers, then re-extract only what is truly shared; compare readability and the number of branches per caller.
- Rewrite a base class that mixes caching and retries as composed `WithCache` and `WithRetry` wrappers, and test each wrapper alone with a fake inner model.
- Run `npx madge --circular` on a Node project, or `lint-imports` with a layers contract on a Python project, and remove one cycle or layer violation.
- Take one "ask" style service method and move the rule into the entity; count how many call sites had duplicated that rule.
- Say it out loud: "You are building an MVP of an AI support assistant in six weeks. Name three things you will deliberately not build and two you will build properly from day one, and explain why."
