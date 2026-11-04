## Express.js Request Pipeline

### Diagram: The Express middleware chain
before: Walkthrough: one request through the Express

```svg
<svg viewBox="0 0 760 300" role="img" aria-label="Express middleware chain. Node's http server emits a request, then express.json, cors, an auth middleware and the router run in registration order, each calling next to pass control on, and the route handler ends the chain with res.json. An error passed to next or thrown from a handler skips the remaining middleware and goes to the error-handling middleware with four arguments, which sends the error response.">
<defs>
<marker id="x1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="x1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tm" x="128" y="52" text-anchor="middle">next()</text>
<text class="tm" x="250" y="52" text-anchor="middle">next()</text>
<text class="tm" x="372" y="52" text-anchor="middle">next()</text>
<text class="tm" x="494" y="52" text-anchor="middle">next()</text>
<text class="tm" x="616" y="52" text-anchor="middle">match</text>
<rect class="bx2" x="15" y="60" width="104" height="60" rx="8"/>
<text class="tb" x="67" y="86" text-anchor="middle">http server</text>
<text class="tm" x="67" y="105" text-anchor="middle">emits request</text>
<rect class="bx" x="137" y="60" width="104" height="60" rx="8"/>
<text class="tb" x="189" y="86" text-anchor="middle">express.json()</text>
<text class="tm" x="189" y="105" text-anchor="middle">parse body</text>
<rect class="bx" x="259" y="60" width="104" height="60" rx="8"/>
<text class="tb" x="311" y="86" text-anchor="middle">cors()</text>
<text class="tm" x="311" y="105" text-anchor="middle">set headers</text>
<rect class="bx" x="381" y="60" width="104" height="60" rx="8"/>
<text class="tb" x="433" y="86" text-anchor="middle">auth</text>
<text class="tm" x="433" y="105" text-anchor="middle">verify token</text>
<rect class="bx" x="503" y="60" width="104" height="60" rx="8"/>
<text class="tb" x="555" y="86" text-anchor="middle">router</text>
<text class="tm" x="555" y="105" text-anchor="middle">GET /orders/:id</text>
<rect class="bxo" x="625" y="60" width="120" height="60" rx="8"/>
<text class="tb" x="685" y="86" text-anchor="middle">handler</text>
<text class="tm" x="685" y="105" text-anchor="middle">res.json(order)</text>
<line class="ln" x1="119" y1="90" x2="135" y2="90" marker-end="url(#x1k)"/>
<line class="ln" x1="241" y1="90" x2="257" y2="90" marker-end="url(#x1k)"/>
<line class="ln" x1="363" y1="90" x2="379" y2="90" marker-end="url(#x1k)"/>
<line class="ln" x1="485" y1="90" x2="501" y2="90" marker-end="url(#x1k)"/>
<line class="ln" x1="607" y1="90" x2="623" y2="90" marker-end="url(#x1k)"/>
<line class="lna dash" x1="433" y1="120" x2="433" y2="198" marker-end="url(#x1a)"/>
<text class="ta" x="441" y="164">next(err)</text>
<path class="lna dash" d="M685,120 V228 H583" marker-end="url(#x1a)"/>
<text class="ta" x="693" y="164">throw or</text>
<text class="ta" x="693" y="180">rejected</text>
<text class="ta" x="693" y="196">promise (v5)</text>
<rect class="bxw" x="381" y="200" width="200" height="56" rx="8"/>
<text class="tb" x="481" y="224" text-anchor="middle">error middleware</text>
<text class="tmono" x="481" y="244" text-anchor="middle">(err, req, res, next)</text>
<line class="ln" x1="381" y1="228" x2="302" y2="228" marker-end="url(#x1k)"/>
<rect class="bx" x="190" y="208" width="110" height="40" rx="8"/>
<text class="t" x="245" y="233" text-anchor="middle">500 JSON</text>
<text class="tm" x="15" y="288">Order is registration order. A middleware that neither calls next() nor ends the response leaves the request hanging.</text>
</svg>
```

Every request walks the same list of functions in the order you registered them, and each one either calls `next()` or ends the response. An error jumps straight to the first middleware that takes four arguments, skipping everything in between. Express 5 also catches rejected promises from async handlers; Express 4 needs a wrapper.

## NestJS Architecture

### Diagram: Modules and the dependency injection container
before: Walkthrough: how Nest boots

```svg
<svg viewBox="0 0 760 330" role="img" aria-label="NestJS modules and dependency injection. AppModule imports OrdersModule, UsersModule and a global ConfigModule. Inside OrdersModule the controller gets OrdersService injected, and OrdersService gets OrdersRepository and the UsersService that UsersModule exports. At startup the injector reads constructor types and creates each provider once, in dependency order.">
<defs>
<marker id="x2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="x2a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<rect class="bx2" x="280" y="12" width="200" height="40" rx="8"/>
<text class="tb" x="380" y="37" text-anchor="middle">AppModule (root)</text>
<line class="ln" x1="330" y1="52" x2="180" y2="88" marker-end="url(#x2k)"/>
<line class="ln" x1="390" y1="52" x2="465" y2="88" marker-end="url(#x2k)"/>
<line class="ln" x1="450" y1="52" x2="665" y2="88" marker-end="url(#x2k)"/>
<text class="tm" x="442" y="78">imports</text>
<rect class="zone" x="15" y="90" width="330" height="170" rx="10"/>
<text class="ta" x="30" y="110">OrdersModule</text>
<rect class="bxa" x="30" y="122" width="140" height="36" rx="6"/>
<text class="t" x="100" y="145" text-anchor="middle">OrdersController</text>
<line class="ln" x1="100" y1="158" x2="100" y2="178" marker-end="url(#x2k)"/>
<text class="tm" x="108" y="172">injects</text>
<rect class="bxo" x="30" y="180" width="140" height="36" rx="6"/>
<text class="t" x="100" y="203" text-anchor="middle">OrdersService</text>
<line class="ln" x1="170" y1="198" x2="188" y2="198" marker-end="url(#x2k)"/>
<rect class="bx" x="190" y="180" width="140" height="36" rx="6"/>
<text class="t" x="260" y="203" text-anchor="middle">OrdersRepository</text>
<rect class="zone" x="365" y="90" width="200" height="170" rx="10"/>
<text class="ta" x="380" y="110">UsersModule</text>
<text class="tm" x="380" y="140">exports: [UsersService]</text>
<rect class="bxo" x="380" y="180" width="170" height="36" rx="6"/>
<text class="t" x="465" y="203" text-anchor="middle">UsersService</text>
<path class="lna" d="M100,216 V246 H465 V218" marker-end="url(#x2a)"/>
<text class="ta" x="194" y="238">uses UsersService</text>
<rect class="zone" x="585" y="90" width="160" height="170" rx="10"/>
<text class="ta" x="600" y="110">ConfigModule</text>
<text class="tm" x="600" y="128">@Global(): no import</text>
<text class="tm" x="600" y="144">needed elsewhere</text>
<rect class="bxo" x="600" y="180" width="130" height="36" rx="6"/>
<text class="t" x="665" y="203" text-anchor="middle">ConfigService</text>
<rect class="bxw" x="15" y="280" width="730" height="40" rx="8"/>
<text class="t" x="380" y="305" text-anchor="middle">Injector: reads constructor types (design:paramtypes), creates each provider once, in dependency order</text>
</svg>
```

Modules are walls with doors. A provider is visible inside its own module, and other modules can use it only if it is exported and they import that module (or the module is global). At startup the injector reads each constructor's parameter types, builds providers in dependency order and keeps one instance of each by default.

### Diagram: One request through the NestJS lifecycle
before: Walkthrough: one request through the NestJS

```svg
<svg viewBox="0 0 760 330" role="img" aria-label="NestJS request lifecycle. Middleware, guards, interceptors before the handler, pipes, the controller handler and the service run in order; on the way back interceptors map the result and the adapter sends the response. A guard that refuses, a pipe that rejects input, or an error thrown in the service is caught by exception filters, which shape the error response.">
<defs>
<marker id="x3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="x3a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<rect class="bx" x="15" y="40" width="130" height="56" rx="8"/>
<text class="tb" x="28" y="63">1. middleware</text>
<text class="tm" x="28" y="82">app-wide, raw req</text>
<rect class="bx" x="167" y="40" width="130" height="56" rx="8"/>
<text class="tb" x="180" y="63">2. guards</text>
<text class="tm" x="180" y="82">canActivate: allow?</text>
<rect class="bx" x="319" y="40" width="130" height="56" rx="8"/>
<text class="tb" x="332" y="63">3. interceptors</text>
<text class="tm" x="332" y="82">before: wrap the call</text>
<rect class="bx" x="471" y="40" width="130" height="56" rx="8"/>
<text class="tb" x="484" y="63">4. pipes</text>
<text class="tm" x="484" y="82">validate, transform</text>
<rect class="bxa" x="623" y="40" width="130" height="56" rx="8"/>
<text class="tb" x="636" y="63">5. controller</text>
<text class="tm" x="636" y="82">route handler</text>
<line class="ln" x1="145" y1="68" x2="165" y2="68" marker-end="url(#x3k)"/>
<line class="ln" x1="297" y1="68" x2="317" y2="68" marker-end="url(#x3k)"/>
<line class="ln" x1="449" y1="68" x2="469" y2="68" marker-end="url(#x3k)"/>
<line class="ln" x1="601" y1="68" x2="621" y2="68" marker-end="url(#x3k)"/>
<line class="ln" x1="688" y1="96" x2="688" y2="168" marker-end="url(#x3k)"/>
<rect class="bxo" x="623" y="170" width="130" height="56" rx="8"/>
<text class="tb" x="636" y="193">6. service</text>
<text class="tm" x="636" y="212">business logic</text>
<rect class="bx" x="471" y="170" width="130" height="56" rx="8"/>
<text class="tb" x="484" y="193">7. interceptors</text>
<text class="tm" x="484" y="212">after: map the result</text>
<rect class="bx" x="319" y="170" width="130" height="56" rx="8"/>
<text class="tb" x="332" y="193">8. response</text>
<text class="tm" x="332" y="212">sent by the adapter</text>
<line class="ln" x1="623" y1="198" x2="603" y2="198" marker-end="url(#x3k)"/>
<line class="ln" x1="471" y1="198" x2="451" y2="198" marker-end="url(#x3k)"/>
<line class="lna dash" x1="232" y1="96" x2="232" y2="260" marker-end="url(#x3a)"/>
<text class="ta" x="240" y="140">403 if false</text>
<line class="lna dash" x1="460" y1="96" x2="460" y2="260" marker-end="url(#x3a)"/>
<text class="ta" x="468" y="140">400 bad input</text>
<path class="lna dash" d="M688,226 V287 H487" marker-end="url(#x3a)"/>
<text class="ta" x="696" y="262">thrown</text>
<text class="ta" x="696" y="278">errors</text>
<rect class="bxw" x="15" y="262" width="470" height="50" rx="8"/>
<text class="tb" x="30" y="284">exception filters</text>
<text class="tm" x="30" y="302">turn any thrown exception into a consistent error response</text>
<line class="lna" x1="384" y1="262" x2="384" y2="228" marker-end="url(#x3a)"/>
<text class="ta" x="376" y="250" text-anchor="end">error response</text>
</svg>
```

Read the top row left to right, then the second row right to left. Guards decide whether the request may run at all, pipes validate and transform the arguments, and interceptors wrap the handler on the way in and out. Anything thrown at any step (blue dashed lines) lands in the exception filters, which build the error response.
