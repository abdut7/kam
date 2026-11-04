## Variables, Types & Operators

### Diagram: Names point to objects
before: Walkthrough: names, objects and mutability

```svg
<svg viewBox="0 0 760 280" role="img" aria-label="Left: a is bound to a list, b = a binds b to the same list, c = a.copy() binds c to a new list. After b.append(4), the shared list holds 1, 2, 3, 4 and both a and b see it, while c still holds 1, 2, 3. Right: x = 10 and y = x bind both names to the int 10; y = y + 1 creates a new int 11 and rebinds y, so x is still 10.">
<defs>
<marker id="p1k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mk"/></marker>
<marker id="p1a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<text class="tmono" x="20" y="28">a = [1, 2, 3]</text>
<text class="tmono" x="20" y="48">b = a</text>
<text class="tmono" x="20" y="68">c = a.copy()</text>
<text class="tmono" x="20" y="88">b.append(4)</text>
<text class="tm" x="20" y="110">names</text>
<text class="tm" x="300" y="110">objects in memory</text>
<rect class="bx2" x="40" y="120" width="60" height="32" rx="6"/><text class="tmono" x="70" y="141" text-anchor="middle">a</text>
<rect class="bx2" x="40" y="166" width="60" height="32" rx="6"/><text class="tmono" x="70" y="187" text-anchor="middle">b</text>
<rect class="bx2" x="40" y="212" width="60" height="32" rx="6"/><text class="tmono" x="70" y="233" text-anchor="middle">c</text>
<rect class="bxa" x="300" y="130" width="200" height="50" rx="8"/>
<text class="tmono" x="400" y="152" text-anchor="middle">[1, 2, 3, 4]</text>
<text class="tm" x="400" y="170" text-anchor="middle">one list, two names</text>
<rect class="bxo" x="300" y="208" width="200" height="40" rx="8"/>
<text class="tmono" x="400" y="233" text-anchor="middle">[1, 2, 3]</text>
<line class="lna" x1="100" y1="136" x2="298" y2="148" marker-end="url(#p1a)"/>
<line class="lna" x1="100" y1="182" x2="298" y2="164" marker-end="url(#p1a)"/>
<line class="ln" x1="100" y1="228" x2="298" y2="228" marker-end="url(#p1k)"/>
<line class="lnm dash" x1="535" y1="16" x2="535" y2="260"/>
<text class="tmono" x="560" y="28">x = 10</text>
<text class="tmono" x="560" y="48">y = x</text>
<text class="tmono" x="560" y="68">y = y + 1</text>
<rect class="bx2" x="560" y="120" width="50" height="32" rx="6"/><text class="tmono" x="585" y="141" text-anchor="middle">x</text>
<rect class="bx2" x="560" y="190" width="50" height="32" rx="6"/><text class="tmono" x="585" y="211" text-anchor="middle">y</text>
<rect class="bx" x="670" y="120" width="70" height="32" rx="6"/><text class="tmono" x="705" y="141" text-anchor="middle">10</text>
<rect class="bxo" x="670" y="190" width="70" height="32" rx="6"/><text class="tmono" x="705" y="211" text-anchor="middle">11</text>
<line class="ln" x1="610" y1="136" x2="668" y2="136" marker-end="url(#p1k)"/>
<line class="ln" x1="610" y1="206" x2="668" y2="206" marker-end="url(#p1k)"/>
<text class="tm" x="560" y="244">ints never change; y + 1</text>
<text class="tm" x="560" y="260">makes a new object</text>
<text class="tm" x="20" y="272">b.append(4) changed the one shared list, so a sees it too; c is a separate copy.</text>
</svg>
```

Python variables are labels, not boxes. `b = a` sticks a second label on the same list, so changing the list through `b` changes what `a` shows (blue). Numbers and strings can never be changed in place, so `y = y + 1` builds a new object and moves the label. This is the same as JavaScript objects and arrays, but it surprises people with default arguments and nested lists.

## Functions

### Diagram: How Python finds a name (LEGB)
before: Walkthrough: how Python finds a name

```svg
<svg viewBox="0 0 760 260" role="img" aria-label="Nested scopes: built-in names on the outside, then module globals, then the enclosing function outer, then the local scope of inner. When inner uses a name, Python searches local first, then enclosing, then global, then built-in, and stops at the first match. global x assigns to the module name from inside a function; nonlocal x assigns to the enclosing function's name.">
<rect class="bx2" x="20" y="20" width="420" height="220" rx="14"/>
<text class="tb" x="34" y="42">4. B: built-in (len, print, range)</text>
<rect class="bx" x="40" y="54" width="380" height="174" rx="12"/>
<text class="tb" x="54" y="76">3. G: module globals</text>
<rect class="bxo" x="60" y="88" width="340" height="128" rx="10"/>
<text class="tb" x="74" y="110">2. E: enclosing function outer()</text>
<rect class="bxa" x="80" y="122" width="300" height="82" rx="8"/>
<text class="tb" x="94" y="144">1. L: local to inner()</text>
<text class="tm" x="94" y="164">the search starts here and moves</text>
<text class="tm" x="94" y="180">outward; the first match wins</text>
<text class="tmono" x="470" y="40">x = "global"</text>
<text class="tmono" x="470" y="60">def outer():</text>
<text class="tmono" x="470" y="80">    x = "enclosing"</text>
<text class="tmono" x="470" y="100">    def inner():</text>
<text class="tmono" x="470" y="120">        x = "local"</text>
<text class="tmono" x="470" y="140">        print(x)  # local</text>
<text class="tmono" x="470" y="160">    inner()</text>
<text class="tm" x="470" y="200">global x: assign the module name from inside</text>
<text class="tm" x="470" y="218">nonlocal x: assign the enclosing name</text>
<text class="tm" x="470" y="236">delete "local" and inner() prints "enclosing"</text>
</svg>
```

When a function reads a name, Python looks in its own scope first, then in any function around it, then at module level, then in the built-ins, and uses the first match. Reading an outer name just works; assigning to it from inside needs `global` or `nonlocal`, otherwise Python creates a new local name.

## Concurrency: Threads, Processes & the GIL

### Diagram: Threads, processes or asyncio
before: Walkthrough: choosing threads

```svg
<svg viewBox="0 0 760 290" role="img" aria-label="Three ways to run work concurrently. Threads: one process with a GIL, so only one thread runs Python at a time; good for I/O with blocking libraries, little gain for CPU work. Processes: several processes, each with its own interpreter and GIL, giving real CPU parallelism at the cost of memory and pickling data between them. Asyncio: one thread and one event loop switching between tasks only at await points; handles many concurrent waits, but one blocking call stalls every task.">
<text class="tb" x="130" y="24" text-anchor="middle">threads</text>
<text class="tb" x="380" y="24" text-anchor="middle">processes</text>
<text class="tb" x="631" y="24" text-anchor="middle">asyncio</text>
<rect class="zone" x="25" y="40" width="215" height="160" rx="10"/>
<rect class="bxw" x="35" y="52" width="70" height="24" rx="5"/><text class="tm" x="70" y="68" text-anchor="middle">one GIL</text>
<rect class="bxa" x="35" y="90" width="40" height="18" rx="3"/><rect class="bx2" x="75" y="90" width="100" height="18" rx="3"/><rect class="bxa" x="175" y="90" width="55" height="18" rx="3"/>
<rect class="bx2" x="35" y="120" width="40" height="18" rx="3"/><rect class="bxa" x="75" y="120" width="50" height="18" rx="3"/><rect class="bx2" x="125" y="120" width="105" height="18" rx="3"/>
<rect class="bx2" x="35" y="150" width="90" height="18" rx="3"/><rect class="bxa" x="125" y="150" width="50" height="18" rx="3"/><rect class="bx2" x="175" y="150" width="55" height="18" rx="3"/>
<text class="tm" x="35" y="188">one thread runs Python at a time</text>
<rect class="bxo" x="272" y="48" width="215" height="40" rx="8"/><text class="t" x="380" y="73" text-anchor="middle">process 1: own interpreter</text>
<rect class="bxo" x="272" y="98" width="215" height="40" rx="8"/><text class="t" x="380" y="123" text-anchor="middle">process 2: own interpreter</text>
<rect class="bxo" x="272" y="148" width="215" height="40" rx="8"/><text class="t" x="380" y="173" text-anchor="middle">process 3: own interpreter</text>
<rect class="zone" x="519" y="40" width="225" height="160" rx="10"/>
<rect class="bxa" x="529" y="52" width="205" height="24" rx="5"/><text class="tm" x="631" y="68" text-anchor="middle">one thread, one event loop</text>
<rect class="bxo" x="529" y="90" width="30" height="18" rx="3"/><rect class="bx2 dash" x="559" y="90" width="120" height="18" rx="3"/><rect class="bxo" x="679" y="90" width="30" height="18" rx="3"/>
<rect class="bx2 dash" x="529" y="120" width="30" height="18" rx="3"/><rect class="bxo" x="559" y="120" width="30" height="18" rx="3"/><rect class="bx2 dash" x="589" y="120" width="120" height="18" rx="3"/>
<rect class="bx2 dash" x="529" y="150" width="60" height="18" rx="3"/><rect class="bxo" x="589" y="150" width="30" height="18" rx="3"/><rect class="bx2 dash" x="619" y="150" width="115" height="18" rx="3"/>
<text class="tm" x="529" y="188">switches tasks only at await</text>
<text class="to" x="25" y="226">use for: I/O with blocking</text>
<text class="tm" x="25" y="242">libraries (requests, boto3)</text>
<text class="ta" x="25" y="262">CPU work barely speeds up</text>
<text class="to" x="272" y="226">use for: CPU-heavy work</text>
<text class="tm" x="272" y="242">(PDF parsing, image work)</text>
<text class="ta" x="272" y="262">costs memory; data is pickled</text>
<text class="to" x="519" y="226">use for: many waits at once</text>
<text class="tm" x="519" y="242">(HTTP, DB, LLM calls)</text>
<text class="ta" x="519" y="262">one blocking call stalls all</text>
</svg>
```

Blue bars are moments when code is running. With threads, the GIL lets only one thread run Python at a time, so threads help while others wait on I/O but not for heavy computing. Separate processes each get their own interpreter and truly run in parallel. Asyncio uses one thread and switches tasks whenever one awaits, which is how FastAPI serves many requests at once, and it is the closest model to Node.js.

## Python for FastAPI

### Diagram: One endpoint, every Python feature it uses
before: Walkthrough: one endpoint

```svg
<svg viewBox="0 0 760 270" role="img" aria-label="A FastAPI endpoint annotated line by line: the decorator registers POST /items; async def runs the handler on the event loop; the parameter typed as a Pydantic model makes FastAPI validate the JSON body and return 422 if it is wrong; Annotated with Depends injects a database session from a generator whose code after yield cleans up; Annotated with Query declares a limit query parameter with a maximum; the return type hint is used as the response model; raise HTTPException becomes a 409 JSON error; await lets other requests run while the database works.">
<defs>
<marker id="p4a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="mka"/></marker>
</defs>
<rect class="bx2" x="10" y="20" width="390" height="236" rx="8"/>
<text class="tmono" x="22" y="44">@app.post("/items")</text>
<text class="tmono" x="22" y="68">async def create_item(</text>
<text class="tmono" x="22" y="92">    item: ItemIn,</text>
<text class="tmono" x="22" y="116">    db: Annotated[DB, Depends(get_db)],</text>
<text class="tmono" x="22" y="140">    limit: Annotated[int, Query(le=100)] = 10,</text>
<text class="tmono" x="22" y="164">) -> ItemOut:</text>
<text class="tmono" x="22" y="188">    if await db.exists(item.name):</text>
<text class="tmono" x="22" y="212">        raise HTTPException(409, "exists")</text>
<text class="tmono" x="22" y="236">    return await db.save(item)</text>
<line class="lna" x1="404" y1="40" x2="428" y2="40" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="28" width="315" height="22" rx="5"/><text class="tm" x="440" y="43">decorator: registers POST /items</text>
<line class="lna" x1="404" y1="64" x2="428" y2="64" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="52" width="315" height="22" rx="5"/><text class="tm" x="440" y="67">async def: runs on the event loop</text>
<line class="lna" x1="404" y1="88" x2="428" y2="88" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="76" width="315" height="22" rx="5"/><text class="tm" x="440" y="91">Pydantic model: body validated, 422 if wrong</text>
<line class="lna" x1="404" y1="112" x2="428" y2="112" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="100" width="315" height="22" rx="5"/><text class="tm" x="440" y="115">Depends: a generator; code after yield cleans up</text>
<line class="lna" x1="404" y1="136" x2="428" y2="136" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="124" width="315" height="22" rx="5"/><text class="tm" x="440" y="139">Annotated + Query: ?limit= with a maximum</text>
<line class="lna" x1="404" y1="160" x2="428" y2="160" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="148" width="315" height="22" rx="5"/><text class="tm" x="440" y="163">return type hint: becomes the response model</text>
<line class="lna" x1="404" y1="208" x2="428" y2="208" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="196" width="315" height="22" rx="5"/><text class="tm" x="440" y="211">raise HTTPException: a 409 JSON error</text>
<line class="lna" x1="404" y1="232" x2="428" y2="232" marker-end="url(#p4a)"/>
<rect class="bxa" x="430" y="220" width="315" height="22" rx="5"/><text class="tm" x="440" y="235">await: other requests run while the DB works</text>
</svg>
```

Almost every line of a FastAPI endpoint is a plain Python feature doing extra work. Decorators register routes, type hints become validation and docs, a generator becomes a dependency with cleanup, an exception becomes an HTTP response, and `await` is what lets one worker serve many requests. Learn the Python feature, and the FastAPI behaviour follows.
