## Node.js Runtime Architecture

### Diagram: The layers inside a Node.js process
before: Walkthrough: one HTTP request

```svg
<svg viewBox="0 0 790 470" role="img" aria-label="Node.js layers. Your JavaScript runs in V8 and calls Node core APIs. C++ bindings hand socket work to the OS kernel through the libuv event loop, and file, crypto, compression and DNS lookup work to the libuv thread pool. Finished work comes back as callbacks on the single call stack.">
<defs>
<marker id="n1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="n1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
<marker id="n1o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="mko"/></marker>
</defs>
<rect class="bx2" x="50" y="16" width="720" height="40" rx="8"/>
<text class="tb" x="410" y="41" text-anchor="middle">Your JavaScript: route handlers, callbacks, async functions</text>
<line class="ln" x1="220" y1="56" x2="220" y2="79" marker-end="url(#n1k)"/>
<text class="tm" x="228" y="72">runs in</text>
<line class="ln" x1="600" y1="56" x2="600" y2="79" marker-end="url(#n1k)"/>
<text class="tm" x="608" y="72">calls</text>
<rect class="bx" x="50" y="80" width="340" height="104" rx="8"/>
<text class="tb" x="70" y="104">V8 engine</text>
<text class="tm" x="70" y="126">call stack: frames of the code running now</text>
<text class="tm" x="70" y="146">heap: objects and closures, garbage collected</text>
<text class="tm" x="70" y="166">JIT: compiles hot JavaScript to machine code</text>
<rect class="bx" x="430" y="80" width="340" height="104" rx="8"/>
<text class="tb" x="450" y="104">Node core APIs (JavaScript)</text>
<text class="tm" x="450" y="126">http, net: sockets</text>
<text class="tm" x="450" y="146">fs, crypto, zlib, dns</text>
<text class="tm" x="450" y="166">timers, streams, process.nextTick</text>
<line class="ln" x1="600" y1="184" x2="600" y2="207" marker-end="url(#n1k)"/>
<rect class="bx2" x="50" y="208" width="720" height="40" rx="8"/>
<text class="t" x="410" y="233" text-anchor="middle">Node bindings (C++): turn each API call into a libuv request</text>
<line class="lna" x1="230" y1="248" x2="230" y2="300" marker-end="url(#n1a)"/>
<text class="ta" x="240" y="265">sockets, timers</text>
<line class="lno" x1="590" y1="248" x2="590" y2="300" marker-end="url(#n1o)"/>
<text class="to" x="600" y="265">fs, crypto, zlib, dns.lookup</text>
<rect class="zone" x="50" y="274" width="720" height="114" rx="10"/>
<text class="ta" x="66" y="292">libuv (C library)</text>
<rect class="bxa" x="70" y="302" width="320" height="70" rx="8"/>
<text class="tb" x="90" y="326">event loop</text>
<text class="tm" x="90" y="346">runs on the same thread as your JavaScript</text>
<text class="tm" x="90" y="363">queues a callback when work finishes</text>
<rect class="bxo" x="430" y="302" width="320" height="70" rx="8"/>
<text class="tb" x="450" y="326">thread pool (4 threads by default)</text>
<text class="tm" x="450" y="346">runs blocking work off the main thread</text>
<text class="tm" x="450" y="363">size set by UV_THREADPOOL_SIZE</text>
<line class="lno" x1="430" y1="337" x2="392" y2="337" marker-end="url(#n1o)"/>
<text class="to" x="411" y="330" text-anchor="middle">done</text>
<line class="lna" x1="230" y1="374" x2="230" y2="414" marker-start="url(#n1a)" marker-end="url(#n1a)"/>
<text class="ta" x="240" y="405">readiness events</text>
<line class="lno" x1="590" y1="372" x2="590" y2="414" marker-end="url(#n1o)"/>
<text class="to" x="600" y="405">blocking syscalls</text>
<rect class="bx" x="50" y="416" width="720" height="40" rx="8"/>
<text class="t" x="410" y="441" text-anchor="middle">OS kernel: epoll (Linux), kqueue (macOS), IOCP (Windows)</text>
<path class="ln" d="M70,337 H30 V132 H48" marker-end="url(#n1k)"/>
<text class="tm" x="22" y="236" text-anchor="middle" transform="rotate(-90 22 236)">callbacks return to the call stack</text>
</svg>
```

Two paths leave your JavaScript. Socket and timer work (blue) is watched by the OS kernel, which tells the event loop when a socket is ready. File, crypto, compression and `dns.lookup` work (green) runs as blocking calls on the libuv thread pool. Either way, the result comes back as a callback that runs on V8's call stack, on the one JavaScript thread.

### Diagram: One request over time, lane by lane
before: Walkthrough: one HTTP request

```svg
<svg viewBox="0 0 760 360" role="img" aria-label="Timeline of one Express request. The handler starts a file read on the thread pool and a database query on a socket watched by the kernel, then the call stack is free for other requests. When the file read finishes its callback is queued and run; when the database reply arrives its callback is queued and run, and it sends the response.">
<defs>
<marker id="n3k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="n3a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
<marker id="n3o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mko"/></marker>
<marker id="n3m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<rect class="bx2" x="160" y="36" width="590" height="60" rx="6"/>
<rect class="bx2" x="160" y="110" width="590" height="60" rx="6"/>
<rect class="bx2" x="160" y="184" width="590" height="60" rx="6"/>
<rect class="bx2" x="160" y="258" width="590" height="60" rx="6"/>
<text class="tb" x="20" y="62">call stack</text>
<text class="tm" x="20" y="80">V8, one thread</text>
<text class="tb" x="20" y="136">poll queue</text>
<text class="tm" x="20" y="154">event loop</text>
<text class="tb" x="20" y="210">thread pool</text>
<text class="tm" x="20" y="228">libuv workers</text>
<text class="tb" x="20" y="284">OS kernel</text>
<text class="tm" x="20" y="302">epoll, kqueue</text>
<rect class="bxa" x="168" y="48" width="88" height="36" rx="6"/>
<text class="t" x="212" y="71" text-anchor="middle">handler</text>
<rect class="bx dash" x="268" y="48" width="200" height="36" rx="6"/>
<text class="tm" x="368" y="71" text-anchor="middle">free: serves other requests</text>
<rect class="bxo" x="250" y="196" width="140" height="36" rx="6"/>
<text class="t" x="320" y="219" text-anchor="middle">read file</text>
<rect class="bx" x="262" y="270" width="240" height="36" rx="6"/>
<text class="t" x="382" y="293" text-anchor="middle">Postgres runs the query</text>
<rect class="bxw" x="400" y="122" width="96" height="36" rx="6"/>
<text class="t" x="448" y="145" text-anchor="middle">file cb</text>
<rect class="bxa" x="508" y="48" width="72" height="36" rx="6"/>
<text class="t" x="544" y="71" text-anchor="middle">cb 1</text>
<rect class="bxw" x="512" y="122" width="104" height="36" rx="6"/>
<text class="t" x="564" y="145" text-anchor="middle">query cb</text>
<rect class="bxa" x="628" y="48" width="114" height="36" rx="6"/>
<text class="t" x="685" y="71" text-anchor="middle">cb 2: res.json()</text>
<line class="lno" x1="236" y1="84" x2="262" y2="194" marker-end="url(#n3o)"/>
<text class="to" x="244" y="176" text-anchor="end">fs.readFile</text>
<line class="lna" x1="250" y1="84" x2="280" y2="268" marker-end="url(#n3a)"/>
<text class="ta" x="290" y="256">query on a socket</text>
<line class="lno" x1="380" y1="196" x2="412" y2="160" marker-end="url(#n3o)"/>
<text class="to" x="402" y="186">done</text>
<line class="lna" x1="490" y1="270" x2="540" y2="160" marker-end="url(#n3a)"/>
<text class="ta" x="522" y="256">reply ready</text>
<line class="ln" x1="472" y1="122" x2="518" y2="86" marker-end="url(#n3k)"/>
<text class="tm" x="486" y="106" text-anchor="end">loop runs it</text>
<line class="ln" x1="600" y1="122" x2="650" y2="86" marker-end="url(#n3k)"/>
<line class="lnm" x1="168" y1="336" x2="742" y2="336" marker-end="url(#n3m)"/>
<text class="tm" x="168" y="354">time</text>
</svg>
```

The handler runs for a moment, starts two pieces of I/O and returns. While the file read (green) and the database query (blue) are in flight, the call stack is free to serve other requests. Each result lands in the poll queue as a callback, and the event loop runs it on the stack. The second callback sends the response.

### Diagram: The event loop, one turn
before: Walkthrough: the event loop

```svg
<svg viewBox="0 0 760 400" role="img" aria-label="The six phases of the Node.js event loop in order: timers, pending callbacks, idle and prepare, poll, check, close callbacks, then back to timers. Between every two callbacks in every phase, Node drains the process.nextTick queue and then the promise microtask queue.">
<defs>
<marker id="n2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<rect class="bx" x="40" y="40" width="200" height="72" rx="8"/>
<text class="tb" x="60" y="66">1. timers</text>
<text class="tm" x="60" y="88">due setTimeout, setInterval</text>
<rect class="bx" x="280" y="40" width="200" height="72" rx="8"/>
<text class="tb" x="300" y="66">2. pending callbacks</text>
<text class="tm" x="300" y="88">some deferred system errors</text>
<rect class="bx2" x="520" y="40" width="200" height="72" rx="8"/>
<text class="tb" x="540" y="66">3. idle, prepare</text>
<text class="tm" x="540" y="88">internal to libuv</text>
<rect class="bxa" x="520" y="200" width="200" height="72" rx="8"/>
<text class="tb" x="540" y="224">4. poll</text>
<text class="tm" x="540" y="244">runs I/O callbacks;</text>
<text class="tm" x="540" y="260">waits here for new I/O</text>
<rect class="bx" x="280" y="200" width="200" height="72" rx="8"/>
<text class="tb" x="300" y="224">5. check</text>
<text class="tm" x="300" y="244">setImmediate callbacks</text>
<rect class="bx" x="40" y="200" width="200" height="72" rx="8"/>
<text class="tb" x="60" y="224">6. close callbacks</text>
<text class="tm" x="60" y="244">socket.on('close'), etc.</text>
<line class="ln" x1="240" y1="76" x2="278" y2="76" marker-end="url(#n2k)"/>
<line class="ln" x1="480" y1="76" x2="518" y2="76" marker-end="url(#n2k)"/>
<line class="ln" x1="620" y1="112" x2="620" y2="198" marker-end="url(#n2k)"/>
<line class="ln" x1="520" y1="236" x2="482" y2="236" marker-end="url(#n2k)"/>
<line class="ln" x1="280" y1="236" x2="242" y2="236" marker-end="url(#n2k)"/>
<line class="ln" x1="140" y1="200" x2="140" y2="114" marker-end="url(#n2k)"/>
<text class="tb" x="380" y="150" text-anchor="middle">one full turn = one loop iteration</text>
<text class="tm" x="380" y="172" text-anchor="middle">poll waits only if no timer is due and no setImmediate is queued</text>
<rect class="bxw" x="40" y="300" width="680" height="72" rx="8"/>
<text class="tb" x="60" y="326">Between every two callbacks, in every phase: drain the microtask queues</text>
<text class="tm" x="60" y="348">1. process.nextTick queue until empty   2. promise microtask queue until empty   3. repeat if either refilled</text>
<text class="tm" x="40" y="394">The process exits when no timers, sockets, handles or pending work remain.</text>
</svg>
```

The loop walks six phases in a fixed order and spends most of its life in poll, waiting for I/O. The yellow band matters most in interviews: after every single callback, Node empties the `process.nextTick` queue and then the promise queue before it runs the next callback. That is why promise callbacks always beat `setTimeout(fn, 0)`.

## FastAPI & Python Async Architecture

### Diagram: How a FastAPI deployment is built
before: Walkthrough: one request through FastAPI

```svg
<svg viewBox="0 0 760 500" role="img" aria-label="FastAPI deployment. Clients connect to a listening socket shared by several Uvicorn worker processes; the Gunicorn master only forks and supervises them. Inside each worker an HTTP parser feeds the asyncio event loop, which calls the ASGI app: Starlette middleware and routing, then FastAPI dependency injection and Pydantic validation, then your endpoint. Plain def endpoints run in the AnyIO thread pool.">
<defs>
<marker id="f1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="f1o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mko"/></marker>
<marker id="f1m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mkm"/></marker>
</defs>
<rect class="bx" x="50" y="14" width="300" height="36" rx="8"/>
<text class="t" x="200" y="37" text-anchor="middle">Client: browser or React app</text>
<line class="ln" x1="200" y1="50" x2="200" y2="73" marker-end="url(#f1k)"/>
<text class="tm" x="208" y="67">HTTP</text>
<rect class="bx2" x="50" y="74" width="300" height="36" rx="8"/>
<text class="t" x="200" y="97" text-anchor="middle">listening socket :8000 (shared)</text>
<rect class="bx" x="560" y="14" width="150" height="104" rx="8"/>
<text class="tb" x="575" y="36">Gunicorn master</text>
<text class="tm" x="575" y="56">binds the socket,</text>
<text class="tm" x="575" y="72">forks the workers,</text>
<text class="tm" x="575" y="88">restarts crashed ones,</text>
<text class="tm" x="575" y="104">never serves requests</text>
<path class="lnm dash" d="M700,118 V148" marker-end="url(#f1m)"/>
<text class="tm" x="694" y="140" text-anchor="end">forks</text>
<line class="ln" x1="200" y1="110" x2="200" y2="182" marker-end="url(#f1k)"/>
<text class="tm" x="208" y="138">accept()</text>
<path class="ln" d="M350,92 H420 V136 H630 V148" marker-end="url(#f1k)"/>
<text class="tm" x="436" y="129">other workers accept too</text>
<rect class="zone" x="50" y="150" width="480" height="330" rx="10"/>
<text class="ta" x="214" y="170">Uvicorn worker 1 (one OS process)</text>
<rect class="bx" x="70" y="184" width="300" height="34" rx="6"/>
<text class="t" x="220" y="206" text-anchor="middle">HTTP parser (httptools or h11)</text>
<line class="ln" x1="220" y1="218" x2="220" y2="229" marker-end="url(#f1k)"/>
<rect class="bxa" x="70" y="230" width="300" height="34" rx="6"/>
<text class="t" x="220" y="252" text-anchor="middle">asyncio event loop (uvloop): one thread</text>
<line class="ln" x1="220" y1="264" x2="220" y2="275" marker-end="url(#f1k)"/>
<rect class="bx" x="70" y="276" width="300" height="34" rx="6"/>
<text class="t" x="220" y="298" text-anchor="middle">ASGI interface: scope, receive, send</text>
<line class="ln" x1="220" y1="310" x2="220" y2="321" marker-end="url(#f1k)"/>
<rect class="bx" x="70" y="322" width="300" height="34" rx="6"/>
<text class="t" x="220" y="344" text-anchor="middle">Starlette: middleware, routing</text>
<line class="ln" x1="220" y1="356" x2="220" y2="367" marker-end="url(#f1k)"/>
<rect class="bx" x="70" y="368" width="300" height="34" rx="6"/>
<text class="t" x="220" y="390" text-anchor="middle">FastAPI: dependencies, Pydantic, OpenAPI</text>
<line class="ln" x1="220" y1="402" x2="220" y2="413" marker-end="url(#f1k)"/>
<rect class="bxo" x="70" y="414" width="300" height="34" rx="6"/>
<text class="t" x="220" y="436" text-anchor="middle">your endpoint (async def runs on the loop)</text>
<line class="lno" x1="370" y1="431" x2="398" y2="431" marker-end="url(#f1o)"/>
<rect class="bxw" x="400" y="398" width="118" height="66" rx="6"/>
<text class="tb" x="459" y="418" text-anchor="middle">AnyIO</text>
<text class="tb" x="459" y="436" text-anchor="middle">thread pool</text>
<text class="tm" x="459" y="454" text-anchor="middle">def handlers here</text>
<rect class="bx" x="560" y="150" width="150" height="64" rx="8"/>
<text class="tb" x="575" y="174">Uvicorn worker 2</text>
<text class="tm" x="575" y="194">own loop, own GIL</text>
<rect class="bx" x="560" y="232" width="150" height="64" rx="8"/>
<text class="tb" x="575" y="256">Uvicorn worker N</text>
<text class="tm" x="575" y="276">same stack inside</text>
<text class="tm" x="560" y="330">CPU-heavy work goes to a</text>
<text class="tm" x="560" y="346">process pool or a task</text>
<text class="tm" x="560" y="362">queue such as Celery</text>
<text class="tm" x="560" y="396">Per process, one thread</text>
<text class="tm" x="560" y="412">runs Python bytecode at a</text>
<text class="tm" x="560" y="428">time (the GIL)</text>
</svg>
```

The Gunicorn master never touches a request: it forks the Uvicorn workers and restarts any that die. Each worker is a separate process with its own event loop. Inside a worker, a request climbs through the parser, the ASGI interface, Starlette and FastAPI to your endpoint. An `async def` endpoint runs on the loop thread, and a plain `def` endpoint is sent to the AnyIO thread pool (yellow).

### Diagram: One request through FastAPI, stage by stage
before: Walkthrough: one request through FastAPI

```svg
<svg viewBox="0 0 760 330" role="img" aria-label="FastAPI request lifecycle in twelve stages: Uvicorn parses bytes, ASGI scope, middleware in, router match, dependencies resolved, Pydantic validation (422 on invalid input), the endpoint runs on the loop if async def or in the thread pool if def, the return value goes through response_model serialization, middleware out, Uvicorn sends bytes, and background tasks run after the response is sent.">
<defs>
<marker id="f2k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
</defs>
<rect class="bx" x="15" y="20" width="165" height="54" rx="8"/>
<text class="tb" x="30" y="42">1. Uvicorn</text>
<text class="tm" x="30" y="62">parses HTTP bytes</text>
<rect class="bx" x="207" y="20" width="165" height="54" rx="8"/>
<text class="tb" x="222" y="42">2. ASGI</text>
<text class="tm" x="222" y="62">scope, receive, send</text>
<rect class="bx" x="399" y="20" width="165" height="54" rx="8"/>
<text class="tb" x="414" y="42">3. middleware in</text>
<text class="tm" x="414" y="62">CORS, auth, timing</text>
<rect class="bx" x="591" y="20" width="165" height="54" rx="8"/>
<text class="tb" x="606" y="42">4. router</text>
<text class="tm" x="606" y="62">match path + method</text>
<line class="ln" x1="180" y1="47" x2="205" y2="47" marker-end="url(#f2k)"/>
<line class="ln" x1="372" y1="47" x2="397" y2="47" marker-end="url(#f2k)"/>
<line class="ln" x1="564" y1="47" x2="589" y2="47" marker-end="url(#f2k)"/>
<line class="ln" x1="673" y1="74" x2="673" y2="128" marker-end="url(#f2k)"/>
<rect class="bx" x="591" y="130" width="165" height="54" rx="8"/>
<text class="tb" x="606" y="152">5. dependencies</text>
<text class="tm" x="606" y="172">cached per request</text>
<rect class="bx" x="399" y="130" width="165" height="54" rx="8"/>
<text class="tb" x="414" y="152">6. Pydantic</text>
<text class="tm" x="414" y="172">validates the input</text>
<text class="tm" x="481" y="202" text-anchor="middle">invalid input: 422 sent back</text>
<rect class="bxa" x="207" y="114" width="165" height="40" rx="8"/>
<text class="tb" x="222" y="132">7a. async def</text>
<text class="tm" x="222" y="148">on the event loop</text>
<rect class="bxw" x="207" y="164" width="165" height="40" rx="8"/>
<text class="tb" x="222" y="182">7b. def</text>
<text class="tm" x="222" y="198">in the thread pool</text>
<rect class="bx" x="15" y="130" width="165" height="54" rx="8"/>
<text class="tb" x="30" y="152">8. return value</text>
<text class="tm" x="30" y="172">dict or model</text>
<line class="ln" x1="591" y1="157" x2="566" y2="157" marker-end="url(#f2k)"/>
<line class="ln" x1="399" y1="150" x2="374" y2="136" marker-end="url(#f2k)"/>
<line class="ln" x1="399" y1="164" x2="374" y2="182" marker-end="url(#f2k)"/>
<line class="ln" x1="207" y1="136" x2="182" y2="150" marker-end="url(#f2k)"/>
<line class="ln" x1="207" y1="182" x2="182" y2="166" marker-end="url(#f2k)"/>
<line class="ln" x1="97" y1="184" x2="97" y2="248" marker-end="url(#f2k)"/>
<rect class="bx" x="15" y="250" width="165" height="54" rx="8"/>
<text class="tb" x="30" y="272">9. response_model</text>
<text class="tm" x="30" y="292">filter, serialize JSON</text>
<rect class="bx" x="207" y="250" width="165" height="54" rx="8"/>
<text class="tb" x="222" y="272">10. middleware out</text>
<text class="tm" x="222" y="292">headers, logging</text>
<rect class="bx" x="399" y="250" width="165" height="54" rx="8"/>
<text class="tb" x="414" y="272">11. Uvicorn sends</text>
<text class="tm" x="414" y="292">bytes to the client</text>
<rect class="bxw dash" x="591" y="250" width="165" height="54" rx="8"/>
<text class="tb" x="606" y="272">12. background tasks</text>
<text class="tm" x="606" y="292">run after the send</text>
<line class="ln" x1="180" y1="277" x2="205" y2="277" marker-end="url(#f2k)"/>
<line class="ln" x1="372" y1="277" x2="397" y2="277" marker-end="url(#f2k)"/>
<line class="ln" x1="564" y1="277" x2="589" y2="277" marker-end="url(#f2k)"/>
</svg>
```

Read it as a snake: left to right, back right to left, then left to right again. Stage 7 is the fork that matters: `async def` code runs on the event loop and must never block, while `def` code runs in the thread pool. Bad input never reaches your code, because stage 6 returns a 422 first.

## Node.js vs FastAPI, Side by Side

### Diagram: Where blocking code goes in each runtime
before: Concepts you must understand

```svg
<svg viewBox="0 0 760 384" role="img" aria-label="Side by side: a Node.js process has one JavaScript thread running the event loop and all your code, a libuv pool used by the runtime's own file, crypto, zlib and DNS lookup APIs, and the OS kernel for sockets. A Uvicorn worker has one event loop thread running async def code, an AnyIO pool that runs your own def endpoints and sync dependencies, and the OS kernel for sockets. Both scale across cores with more processes.">
<defs>
<marker id="c1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
<marker id="c1o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mko"/></marker>
</defs>
<text class="tb" x="192" y="20" text-anchor="middle">Node.js process</text>
<text class="tb" x="567" y="20" text-anchor="middle">Uvicorn worker process (FastAPI)</text>
<rect class="zone" x="15" y="30" width="355" height="300" rx="10"/>
<rect class="zone" x="390" y="30" width="355" height="300" rx="10"/>
<rect class="bxa" x="35" y="50" width="315" height="66" rx="8"/>
<text class="tb" x="50" y="74">JS thread: event loop + all your code</text>
<text class="tm" x="50" y="96">handlers, promises, callbacks</text>
<rect class="bxa" x="410" y="50" width="315" height="66" rx="8"/>
<text class="tb" x="425" y="74">loop thread: async def code</text>
<text class="tm" x="425" y="96">awaits httpx, asyncpg, LLM SDK calls</text>
<line class="lno" x1="110" y1="116" x2="110" y2="148" marker-end="url(#c1o)"/>
<line class="lna" x1="275" y1="116" x2="275" y2="148" marker-end="url(#c1a)"/>
<line class="lno" x1="485" y1="116" x2="485" y2="148" marker-end="url(#c1o)"/>
<line class="lna" x1="650" y1="116" x2="650" y2="148" marker-end="url(#c1a)"/>
<rect class="bxo" x="35" y="150" width="150" height="74" rx="8"/>
<text class="tb" x="48" y="172">libuv pool</text>
<text class="tm" x="48" y="192">fs, crypto, zlib,</text>
<text class="tm" x="48" y="208">dns.lookup</text>
<rect class="bx" x="200" y="150" width="150" height="74" rx="8"/>
<text class="tb" x="213" y="172">OS kernel</text>
<text class="tm" x="213" y="192">sockets, timers</text>
<rect class="bxo" x="410" y="150" width="150" height="74" rx="8"/>
<text class="tb" x="423" y="172">AnyIO pool</text>
<text class="tm" x="423" y="192">your def endpoints,</text>
<text class="tm" x="423" y="208">sync dependencies</text>
<rect class="bx" x="575" y="150" width="150" height="74" rx="8"/>
<text class="tb" x="588" y="172">OS kernel</text>
<text class="tm" x="588" y="192">sockets via uvloop</text>
<rect class="bxw dash" x="35" y="250" width="315" height="66" rx="8"/>
<text class="tb" x="50" y="272">Blocks every request on this process:</text>
<text class="tm" x="50" y="292">CPU loops, readFileSync, JSON.parse</text>
<text class="tm" x="50" y="308">of a huge payload</text>
<rect class="bxw dash" x="410" y="250" width="315" height="66" rx="8"/>
<text class="tb" x="425" y="272">Blocks every request on this worker:</text>
<text class="tm" x="425" y="292">time.sleep or requests.get inside</text>
<text class="tm" x="425" y="308">async def; CPU work (one GIL)</text>
<text class="tm" x="15" y="350">More cores: cluster or PM2, one process per core</text>
<text class="tm" x="390" y="350">More cores: Gunicorn workers, one process per core</text>
<text class="ta" x="380" y="376" text-anchor="middle">Key difference: Node's pool serves the runtime's own APIs; FastAPI's pool runs YOUR sync code.</text>
</svg>
```

The two runtimes have the same shape: one event loop thread per process, a pool for blocking work, the kernel for sockets, and more processes for more cores. The difference is the green box. Node uses its pool for its own file, crypto and compression APIs. FastAPI uses its pool to run the plain `def` code you wrote.
