## Node.js Runtime Internals

### In plain words
Node.js runs all of your JavaScript on one thread, like one very fast waiter who never stands at a table waiting. Slow jobs are handed off: the operating system watches network sockets, and a small kitchen crew (the libuv thread pool) handles files, crypto and compression. When a job finishes, its callback waits in a queue until the event loop puts it back on the one thread. The Internal Architecture track has the pictures: the layers inside a Node.js process, one request lane by lane, and one turn of the event loop.

## Python & FastAPI for AI Backends

### In plain words
FastAPI runs as several worker processes, and each worker has one event loop thread, much like Node. An `async def` endpoint runs on that loop and must never block it. A plain `def` endpoint is sent to a thread pool, so blocking code is safe there. The Internal Architecture track has the pictures: how a FastAPI deployment is built, one request stage by stage, and where blocking code goes in Node.js versus FastAPI.
