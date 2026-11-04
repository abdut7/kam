## SOLID Principles

### Diagram: Dependency inversion, before and after
before: Walkthrough: refactoring

```svg
<svg viewBox="0 0 760 270" role="img" aria-label="Dependency inversion. Before: OrderService creates and calls PostgresOrderRepository, which calls the pg driver, so business code depends on a database detail. After: OrderService depends on an OrderRepository interface; PostgresOrderRepository and an in-memory test repository both implement that interface, and the composition root chooses which one to inject.">
<defs>
<marker id="d1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="d1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tb" x="180" y="22" text-anchor="middle">Before: depends on a detail</text>
<rect class="bx" x="90" y="40" width="180" height="44" rx="8"/>
<text class="tb" x="180" y="67" text-anchor="middle">OrderService</text>
<line class="ln" x1="180" y1="84" x2="180" y2="108" marker-end="url(#d1k)"/>
<text class="tm" x="188" y="100">new + calls</text>
<rect class="bx2" x="90" y="110" width="180" height="44" rx="8"/>
<text class="t" x="180" y="137" text-anchor="middle">PostgresOrderRepository</text>
<line class="ln" x1="180" y1="154" x2="180" y2="178" marker-end="url(#d1k)"/>
<rect class="bx2" x="90" y="180" width="180" height="40" rx="8"/>
<text class="t" x="180" y="205" text-anchor="middle">pg driver</text>
<text class="tm" x="180" y="246" text-anchor="middle">hard to test, hard to swap databases</text>
<line class="lnm dash" x1="380" y1="20" x2="380" y2="256"/>
<text class="tb" x="575" y="22" text-anchor="middle">After: both depend on an abstraction</text>
<rect class="bx" x="485" y="40" width="180" height="44" rx="8"/>
<text class="tb" x="575" y="67" text-anchor="middle">OrderService</text>
<line class="ln" x1="575" y1="84" x2="575" y2="108" marker-end="url(#d1k)"/>
<text class="tm" x="583" y="100">depends on</text>
<rect class="bxa" x="485" y="110" width="180" height="44" rx="8"/>
<text class="tb" x="575" y="130" text-anchor="middle">OrderRepository</text>
<text class="tm" x="575" y="147" text-anchor="middle">interface (a port)</text>
<rect class="bx2" x="400" y="194" width="160" height="44" rx="8"/>
<text class="t" x="480" y="221" text-anchor="middle">PostgresOrderRepository</text>
<rect class="bx2" x="575" y="194" width="170" height="44" rx="8"/>
<text class="t" x="660" y="214" text-anchor="middle">InMemoryOrderRepository</text>
<text class="tm" x="660" y="230" text-anchor="middle">for tests</text>
<line class="lna" x1="500" y1="194" x2="540" y2="156" marker-end="url(#d1a)"/>
<line class="lna" x1="640" y1="194" x2="610" y2="156" marker-end="url(#d1a)"/>
<text class="ta" x="575" y="180" text-anchor="middle">implements</text>
<text class="tm" x="575" y="260" text-anchor="middle">the composition root picks which one to inject</text>
</svg>
```

On the left, business code points straight at a database class, so every test needs Postgres. On the right, the arrows from the concrete classes point up (blue) to an interface the business code owns. That reversal is the "inversion": the detail depends on the policy, not the other way round.

## Architectural Patterns

### Diagram: Layered versus clean, by the direction of dependencies
before: Walkthrough: one request through a clean architecture

```svg
<svg viewBox="0 0 760 300" role="img" aria-label="Layered versus clean architecture. In a layered stack, controllers depend on services, services depend on repositories, and repositories depend on the database, so business logic depends downward on data access. In clean architecture the domain sits in the centre, surrounded by use cases, then interface adapters, then frameworks and drivers, and every source code dependency points inward toward the domain.">
<defs>
<marker id="d2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="d2a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tb" x="180" y="22" text-anchor="middle">Layered: depends downward on data</text>
<rect class="bx" x="40" y="40" width="280" height="44" rx="8"/>
<text class="t" x="180" y="67" text-anchor="middle">controllers (presentation)</text>
<line class="ln" x1="180" y1="84" x2="180" y2="102" marker-end="url(#d2k)"/>
<rect class="bxo" x="40" y="104" width="280" height="44" rx="8"/>
<text class="t" x="180" y="131" text-anchor="middle">services (business logic)</text>
<line class="ln" x1="180" y1="148" x2="180" y2="166" marker-end="url(#d2k)"/>
<rect class="bx" x="40" y="168" width="280" height="44" rx="8"/>
<text class="t" x="180" y="195" text-anchor="middle">repositories, ORM (data access)</text>
<line class="ln" x1="180" y1="212" x2="180" y2="230" marker-end="url(#d2k)"/>
<rect class="bx2" x="40" y="232" width="280" height="40" rx="8"/>
<text class="t" x="180" y="257" text-anchor="middle">database</text>
<text class="tm" x="188" y="98">depends on</text>
<text class="tb" x="570" y="22" text-anchor="middle">Clean: depends inward on the domain</text>
<rect class="bx2" x="390" y="32" width="360" height="262" rx="16"/>
<text class="tm" x="570" y="50" text-anchor="middle">frameworks and drivers: Express, NestJS, Postgres, Stripe</text>
<rect class="bx" x="425" y="62" width="290" height="202" rx="14"/>
<text class="tm" x="570" y="80" text-anchor="middle">interface adapters: controllers, repositories</text>
<rect class="bxo" x="460" y="92" width="220" height="142" rx="12"/>
<text class="tm" x="570" y="110" text-anchor="middle">application: use cases</text>
<rect class="bxa" x="495" y="122" width="150" height="82" rx="10"/>
<text class="tb" x="570" y="158" text-anchor="middle">domain</text>
<text class="tm" x="570" y="176" text-anchor="middle">entities, rules</text>
<line class="lna" x1="400" y1="163" x2="493" y2="163" marker-end="url(#d2a)"/>
<line class="lna" x1="740" y1="163" x2="647" y2="163" marker-end="url(#d2a)"/>
<text class="ta" x="570" y="282" text-anchor="middle">every source code dependency points inward</text>
</svg>
```

Both pictures can hold the same code; what differs is which way the imports point. In the layered stack, business logic imports the data layer, so the database shape leaks upward. In clean architecture the domain imports nothing, use cases import only the domain, and frameworks sit on the outside where they can be swapped.

### Diagram: Hexagonal architecture, ports and adapters
before: Walkthrough: one request through a clean architecture

```svg
<svg viewBox="0 0 760 330" role="img" aria-label="Hexagonal architecture. The application core with use cases and domain rules sits in a hexagon and imports no framework. Driving adapters on the left, an HTTP controller and a queue consumer, call the core through an inbound port. On the right, the core calls outbound ports for orders, payments and the LLM, and driven adapters for Postgres, Stripe and an OpenAI or vLLM client implement those ports. Tests plug in-memory fakes into the same ports.">
<defs>
<marker id="d3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="d3a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<polygon class="bx" points="230,170 305,40 455,40 530,170 455,300 305,300"/>
<text class="tb" x="380" y="90" text-anchor="middle">application core</text>
<text class="tm" x="380" y="110" text-anchor="middle">use cases + domain rules</text>
<text class="tm" x="380" y="126" text-anchor="middle">no framework imports</text>
<rect class="bxa" x="252" y="176" width="90" height="28" rx="6"/>
<text class="t" x="297" y="195" text-anchor="middle">PlaceOrder</text>
<text class="tm" x="297" y="222" text-anchor="middle">inbound port</text>
<rect class="bxa" x="392" y="140" width="80" height="28" rx="6"/>
<text class="t" x="432" y="159" text-anchor="middle">Orders</text>
<rect class="bxa" x="392" y="182" width="80" height="28" rx="6"/>
<text class="t" x="432" y="201" text-anchor="middle">Payments</text>
<rect class="bxa" x="392" y="224" width="80" height="28" rx="6"/>
<text class="t" x="432" y="243" text-anchor="middle">LlmClient</text>
<text class="tm" x="432" y="270" text-anchor="middle">outbound ports</text>
<text class="tb" x="100" y="136" text-anchor="middle">driving adapters</text>
<rect class="bx" x="15" y="150" width="170" height="44" rx="8"/>
<text class="tb" x="100" y="168" text-anchor="middle">HTTP controller</text>
<text class="tm" x="100" y="185" text-anchor="middle">Express, NestJS, FastAPI</text>
<rect class="bx" x="15" y="214" width="170" height="44" rx="8"/>
<text class="tb" x="100" y="232" text-anchor="middle">queue consumer</text>
<text class="tm" x="100" y="249" text-anchor="middle">Kafka, SQS, cron</text>
<line class="ln" x1="185" y1="172" x2="250" y2="186" marker-end="url(#d3k)"/>
<line class="ln" x1="185" y1="236" x2="250" y2="196" marker-end="url(#d3k)"/>
<text class="tm" x="212" y="166">calls</text>
<text class="tb" x="660" y="118" text-anchor="middle">driven adapters</text>
<rect class="bx2" x="575" y="132" width="170" height="40" rx="8"/>
<text class="t" x="660" y="157" text-anchor="middle">Postgres adapter</text>
<rect class="bx2" x="575" y="178" width="170" height="40" rx="8"/>
<text class="t" x="660" y="203" text-anchor="middle">Stripe adapter</text>
<rect class="bx2" x="575" y="224" width="170" height="40" rx="8"/>
<text class="t" x="660" y="249" text-anchor="middle">OpenAI or vLLM adapter</text>
<line class="lna" x1="575" y1="152" x2="474" y2="154" marker-end="url(#d3a)"/>
<line class="lna" x1="575" y1="198" x2="474" y2="196" marker-end="url(#d3a)"/>
<line class="lna" x1="575" y1="244" x2="474" y2="238" marker-end="url(#d3a)"/>
<text class="ta" x="524" y="124" text-anchor="middle">implements</text>
<text class="tm" x="575" y="292">tests plug in-memory fakes</text>
<text class="tm" x="575" y="308">into the same ports</text>
</svg>
```

The core in the middle defines ports, which are interfaces it owns. Adapters on the left drive the core: HTTP, queues and cron all call the same inbound port. Adapters on the right are driven by it, and each one implements an outbound port (blue arrows). Swapping Stripe, Postgres or the LLM provider means writing a new adapter; the core does not change.
