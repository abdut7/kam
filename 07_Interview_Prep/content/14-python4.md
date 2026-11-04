## Errors & Exceptions [Core]

> This section covers how Python signals and handles failure: try/except/else/finally, the exception hierarchy, raising, custom exception classes, chaining, EAFP, exception groups and logging. In FastAPI and AI backends it is everywhere: a provider SDK raising a rate-limit error, a Pydantic `ValidationError` on a malformed LLM response, a domain `NotFoundError` that must become a clean 404, and a retry wrapper that must catch the right failures and nothing else.

### Why it exists
Python reports failure by raising an exception object instead of returning an error code, so a return value is always a real result and an error cannot be silently ignored the way an unchecked status code or a forgotten `if (err)` in a Node callback can. The exception travels up the call stack until a caller that knows the policy (retry, return 404, log and continue) catches it, so low-level code does not need to know the policy and high-level code does not need to check every call. Exceptions are classes in a hierarchy, which lets each `except` clause pick exactly the failures it can handle and let everything else pass. The cost is invisible control flow: almost any line can jump out, and one careless `except` can hide a real bug for months.

### In plain words
An exception works like a fire alarm in an office building. The person who sees the fire pulls the alarm (`raise`) and does not need to know who will respond. The alarm goes up floor by floor until it reaches someone trained for that kind of emergency (an `except` clause for that type). If nobody handles it, the whole building is evacuated: the program stops and prints a traceback. The `finally` block is the rule "whatever happens, lock the server room on your way out."

### Walkthrough: try, except, else, finally and the order they run
1. **Catch a specific exception**: wrap only the line that can fail and name the exception class you expect. `int("abc")` raises `ValueError`, while JavaScript's `parseInt("abc")` quietly returns `NaN`, so in Python bad input is handled in an `except`, not by checking the result afterwards.
   ```python
   text = "abc"
   try:
       count = int(text)
   except ValueError as e:
       print(f"bad number: {e}")   # bad number: invalid literal for int() with base 10: 'abc'
       count = 0
   ```
2. **Several except clauses, first match wins**: Python tests the clauses top to bottom with an isinstance check and runs only the first match, so put subclasses before their parents. A tuple catches several types in one clause.
   ```python
   import json

   try:
       with open("config.json", encoding="utf-8") as f:
           config = json.load(f)
   except FileNotFoundError:                     # subclass of OSError, so it goes first
       config = {}
   except (OSError, json.JSONDecodeError) as e:  # permission problems, bad JSON
       print(f"cannot load config: {e}")
       config = {}
   ```
3. **else runs only on success**: the `else` block runs when the `try` block finished without an exception (and without a `return`). It keeps the `try` block down to the risky line, so a bug in the follow-up code is not mistaken for the failure you meant to catch.
   ```python
   try:
       user = users[user_id]
   except KeyError:
       user = None
   else:
       audit_log.append(("user.read", user_id))   # a bug here is not reported as "user missing"
   ```
4. **finally always runs**: on success, on an exception, and even after `return` or `break`. Use it for cleanup such as releasing a lock (a `with` block is usually cleaner). The order is: `try`, then `except` (if something was raised) or `else` (if not), then `finally`.
   ```python
   def load(fail: bool) -> None:
       try:
           print("try")
           if fail:
               raise ValueError("boom")
       except ValueError:
           print("except")
       else:
           print("else")
       finally:
           print("finally")

   load(False)   # try, else, finally
   load(True)    # try, except, finally
   ```
   Trap: a `return` inside `finally` replaces whatever was happening, including an exception in flight, which is then silently lost. Never return from `finally`.
5. **The hierarchy: Exception vs BaseException**: every exception inherits from `BaseException`. Normal errors inherit from `Exception`; `KeyboardInterrupt` (Ctrl+C), `SystemExit` (`sys.exit()`) and `asyncio.CancelledError` (since 3.8) inherit from `BaseException` directly, so `except Exception` lets them through. A bare `except:` catches all of them, which means Ctrl+C cannot stop your loop and asyncio task cancellation breaks.
   ```text
   BaseException
    +-- KeyboardInterrupt, SystemExit, GeneratorExit
    +-- asyncio.CancelledError
    +-- Exception
         +-- ValueError
         |    +-- json.JSONDecodeError
         +-- LookupError
         |    +-- KeyError, IndexError
         +-- OSError
         |    +-- FileNotFoundError, PermissionError, TimeoutError, ConnectionError
         +-- TypeError, AttributeError, RuntimeError, ...
   ```
   ```python
   while True:
       try:
           poll_queue()
       except Exception:          # not a bare except: Ctrl+C still stops the loop
           logger.exception("poll failed")
   ```
6. **The `as` name is deleted after the block**: when an `except ... as e` block ends, Python deletes `e` (it would otherwise keep the whole traceback and its frames alive). Copy it to another name if you need it later.
   ```python
   try:
       int("x")
   except ValueError as e:
       error = e
   print(error)    # invalid literal for int() with base 10: 'x'
   print(e)        # NameError: name 'e' is not defined
   ```
7. **Compared with JavaScript**: JS has one `catch` that receives anything (even a thrown string) and you dispatch with `instanceof`. Python dispatches by type in the syntax, and only exception objects can be raised.
   ```js
   try {
     config = JSON.parse(text);
   } catch (err) {
     if (err instanceof SyntaxError) config = {};
     else throw err;
   }
   ```

### Walkthrough: raising, custom exceptions, chaining and logging
1. **raise**: `raise ValueError("msg")` is `throw new Error("msg")` without `new`. Raising a class (`raise ValueError`) also works; Python instantiates it.
   ```python
   def set_temperature(value: float) -> None:
       if not 0 <= value <= 2:
           raise ValueError(f"temperature must be between 0 and 2, got {value}")
   ```
2. **Custom exception classes with extra fields**: subclass `Exception` (never `BaseException`), give your service one base class, and add the fields callers need. Call `super().__init__(message)` so `str(e)` and the traceback show a readable message.
   ```python
   class AppError(Exception):
       """Base class for every error this service raises on purpose."""

   class NotFoundError(AppError):
       def __init__(self, resource: str, resource_id: str) -> None:
           super().__init__(f"{resource} {resource_id} not found")
           self.resource = resource
           self.resource_id = resource_id

   class RateLimitedError(AppError):
       def __init__(self, retry_after: float) -> None:
           super().__init__(f"rate limited, retry after {retry_after}s")
           self.retry_after = retry_after
   ```
   Callers can catch `AppError` for everything you raise deliberately, or one subclass for a specific case.
3. **Re-raise with a bare raise**: inside an `except` block, `raise` with no argument re-raises the current exception with its original traceback. Use it when you only want to record something and let the error continue.
   ```python
   try:
       charge(order)
   except PaymentError:
       metrics.increment("payment.failed")
       raise
   ```
4. **Chain with raise ... from**: when you translate a low-level error into your own type, use `from` so the original is stored as `__cause__` and the traceback shows both, joined by "The above exception was the direct cause of the following exception". Without `from`, Python still attaches the original as `__context__` but prints "During handling of the above exception, another exception occurred", which reads like a second bug. `from None` hides the original on purpose.
   ```python
   try:
       payload = json.loads(raw)
   except json.JSONDecodeError as e:
       raise ConfigError(f"invalid config JSON: {e}") from e
   ```
   The JavaScript counterpart is `new Error("invalid config", { cause: err })` (ES2022).
5. **Add context with notes (3.11+)**: `e.add_note("while processing order 42")` appends a line to the traceback without changing the exception type, handy in loops over many records.
   ```python
   for order_id in order_ids:
       try:
           process(order_id)
       except Exception as e:
           e.add_note(f"order_id={order_id}")
           raise
   ```
6. **Log with logger.exception**: inside an `except` block, `logger.exception("msg")` logs at ERROR level and appends the full traceback (the same as `logger.error("msg", exc_info=True)`). Log once, where you actually handle the error, not in every layer that re-raises it, or the same traceback appears five times.
   ```python
   import logging

   logger = logging.getLogger(__name__)

   try:
       reply = await llm.complete(prompt)
   except ProviderError:
       logger.exception("llm call failed", extra={"model": model})
       reply = FALLBACK_REPLY
   ```
7. **JavaScript side by side**: a JS `Error` subclass must set `this.name` or logs say "Error"; Python prints the class name automatically.
   ```js
   class NotFoundError extends Error {
     constructor(resource, id) {
       super(`${resource} ${id} not found`);
       this.name = "NotFoundError";
       this.resource = resource;
     }
   }
   ```

### Walkthrough: EAFP, exception groups, async errors and FastAPI
1. **LBYL vs EAFP**: LBYL ("look before you leap") checks first; EAFP ("easier to ask forgiveness than permission") just tries and catches the failure. Python style prefers EAFP because a check and the action can race (the file is deleted between `exists()` and the read), and the check often repeats work the action does anyway.
   ```python
   from pathlib import Path

   path = Path("cache/answer.txt")

   # LBYL: a race between the check and the read
   text = path.read_text(encoding="utf-8") if path.exists() else ""

   # EAFP: one operation, no race
   try:
       text = path.read_text(encoding="utf-8")
   except FileNotFoundError:
       text = ""
   ```
   LBYL is still right when "missing" is the normal, cheap case: `counts.get(word, 0)` beats try/except KeyError in a hot loop.
2. **Ignore one named error on purpose**: `contextlib.suppress` is the readable form of try/except/pass for a single, expected error.
   ```python
   from contextlib import suppress

   with suppress(FileNotFoundError):
       Path("cache/old.json").unlink()
   ```
3. **ExceptionGroup and `except*` (3.11+)**: when several things fail together, such as tasks inside an `asyncio.TaskGroup`, Python raises one `ExceptionGroup` that holds all of them. Each `except*` clause takes the matching exceptions out of the group, and every clause that matches runs, unlike plain `except`.
   ```python
   import asyncio

   async def fan_out(prompts: list[str]) -> None:
       try:
           async with asyncio.TaskGroup() as tg:
               for p in prompts:
                   tg.create_task(call_llm(p))
       except* TimeoutError as eg:
           logger.warning("%d calls timed out", len(eg.exceptions))
       except* ValueError as eg:
           logger.error("%d bad responses", len(eg.exceptions))
   ```
4. **Async errors vs promise rejections**: in Node, a rejected promise nobody awaits or catches is an "unhandled rejection" (fatal by default since Node 15). In Python, `await coro()` raises the exception right at the `await` line, so ordinary try/except works around awaits. A task started with `asyncio.create_task` and never awaited logs "Task exception was never retrieved" when it is garbage collected. `asyncio.gather(..., return_exceptions=True)` is the counterpart of `Promise.allSettled`.
   ```python
   results = await asyncio.gather(call_a(), call_b(), return_exceptions=True)
   for r in results:
       if isinstance(r, Exception):
           logger.warning("call failed: %r", r)
   ```
5. **How FastAPI turns exceptions into HTTP responses**: raise `HTTPException(status_code=404, detail="Order not found")` in a route and FastAPI answers 404 with the body `{"detail": "Order not found"}`. Register `@app.exception_handler(NotFoundError)` to map your own domain exceptions to responses, so service code never imports HTTP classes. Request validation failures become 422 with a list of field errors, and any other unhandled exception becomes a plain 500 "Internal Server Error" while the traceback goes to the server log. This is Express error middleware `(err, req, res, next)` or a NestJS exception filter.
   ```python
   from fastapi import FastAPI, HTTPException, Request
   from fastapi.responses import JSONResponse

   app = FastAPI()

   @app.exception_handler(NotFoundError)
   async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
       return JSONResponse(status_code=404, content={"error": str(exc), "resource": exc.resource})

   @app.get("/orders/{order_id}")
   async def get_order(order_id: str) -> dict:
       if order_id.startswith("legacy-"):
           raise HTTPException(status_code=410, detail="Legacy orders are archived")
       return await orders.get(order_id)    # may raise NotFoundError, which becomes a 404
   ```

### Concepts you must understand
- Catch the narrowest exception class you can actually handle, around the smallest block that can raise it.
- `except Exception` is the widest catch you normally want; a bare `except:` or `except BaseException` also swallows Ctrl+C, `sys.exit()` and asyncio cancellation.
- Except clauses are tried top to bottom and the first match wins, so subclasses go before their parents.
- `else` runs only when the `try` block finished normally; `finally` runs no matter what, and a `return` inside `finally` discards an exception in flight.
- Custom exceptions subclass `Exception`, share one app-level base class, call `super().__init__(message)`, and carry data as attributes.
- `raise NewError(...) from err` keeps the cause; a bare `raise` re-raises with the original traceback; `from None` hides the cause deliberately.
- EAFP is idiomatic and avoids check-then-act races; LBYL is fine when the "failure" is common and cheap to test, as with `dict.get`.
- `ExceptionGroup` and `except*` (3.11+) handle several simultaneous failures, mostly from `asyncio.TaskGroup`.
- Log a handled exception once with `logger.exception` inside the except block; do not log and re-raise at every layer.
- In FastAPI, raise `HTTPException` at the edge, map domain exceptions with `@app.exception_handler`, and expect anything unhandled to become a 500.

| JavaScript | Python | Note |
|---|---|---|
| `try { } catch (e) { } finally { }` | `try: / except X as e: / else: / finally:` | Python adds `else` and typed clauses |
| `if (e instanceof X)` inside catch | `except X as e:` | type dispatch is part of the syntax |
| `throw new Error("msg")` | `raise ValueError("msg")` | no `new`; only exception objects can be raised |
| `class E extends Error` plus `this.name = "E"` | `class E(Exception): ...` | the class name appears in tracebacks automatically |
| `new Error("msg", { cause: err })` | `raise E("msg") from err` | stored as `__cause__` |
| `throw err` inside catch | bare `raise` | keeps the original traceback |
| unhandled promise rejection | exception raised at the `await` line | an un-awaited task logs "Task exception was never retrieved" |
| `Promise.allSettled([...])` | `asyncio.gather(..., return_exceptions=True)` | exceptions come back as values |
| `AggregateError` | `ExceptionGroup` with `except*` | 3.11+ |
| `parseInt("abc")` gives `NaN` | `int("abc")` raises `ValueError` | Python fails loudly on bad input |
| Express error middleware | `@app.exception_handler(...)` in FastAPI | maps exceptions to responses |
| `logger.error({ err }, "msg")` (pino) | `logger.exception("msg")` | includes the traceback |

### Q. Predict the output of this try/except/else/finally code and explain the order.
**Short answer (45 seconds):** For each call, `finally` always prints last, right before the function hands back its value. `else` runs only when the `try` block finished normally, so it is skipped both when an exception is raised and when `try` itself returns. The except clause's return value wins for the error case.

**Deeper explanation:** The code:

```python
def step(n: int) -> str:
    try:
        print("try", n)
        if n == 0:
            raise ZeroDivisionError("n is zero")
        if n == 1:
            return "early"
    except ZeroDivisionError:
        print("except")
        return "handled"
    else:
        print("else")
        return "normal"
    finally:
        print("finally")

for n in (0, 1, 2):
    print("->", step(n))
```

The output:

```text
try 0
except
finally
-> handled
try 1
finally
-> early
try 2
else
finally
-> normal
```

For `n=0` the raise jumps to the matching except, which computes its return value "handled"; before the caller receives it, `finally` runs. For `n=1` the `return "early"` inside `try` leaves the block, so `else` is skipped (it runs only when control falls off the end of `try`), but `finally` still runs. For `n=2` nothing is raised and nothing returns inside `try`, so `else` runs, then `finally`.

If `finally` contained `return "finally"`, all three calls would print `-> finally`, and an unexpected exception (say a `TypeError`) would vanish without a trace. That is why returning from `finally` is a bug.

**Follow-ups they will ask:**
- What if the except block itself raises?: `finally` still runs, then the new exception propagates with the original attached as `__context__`.
- Why use else instead of putting the code at the end of try?: so exceptions from that code are not caught by an except meant for the risky line.
- Where would you close a DB session?: in `finally`, or better in a `with` block or a FastAPI dependency that uses `yield`.

**Mistakes to avoid:**
- Saying `else` runs whenever no exception happened; a `return`, `break` or `continue` inside `try` also skips it.
- Returning from `finally`, which silently discards exceptions.

### Q. This retry helper swallows Ctrl+C and hides real bugs. Find and fix it.
**Short answer (45 seconds):** The bare `except` catches everything, including `KeyboardInterrupt`, and also retries programming errors that will never succeed. The final `return {}` makes total failure look like an empty success. Catch only transient network errors, re-raise a clear error after the last attempt, and log each retry.

**Deeper explanation:** The code:

```python
def fetch_with_retry(url: str) -> dict:
    for attempt in range(3):
        try:
            return http_get(url).json()
        except:
            time.sleep(2 ** attempt)
    return {}
```

Three bugs. The bare `except:` catches `BaseException`, so Ctrl+C or `SystemExit` during the request is swallowed and the loop keeps going. It also retries a `TypeError`, an `AttributeError` or a JSON decode error from an HTML error page, none of which a retry can fix. And `return {}` tells the caller "no data" when the truth is "the upstream is down".

```python
import logging
import time

import httpx

logger = logging.getLogger(__name__)
RETRYABLE = (httpx.TimeoutException, httpx.ConnectError)

class UpstreamError(Exception):
    pass

def fetch_with_retry(url: str, attempts: int = 3) -> dict:
    for attempt in range(1, attempts + 1):
        try:
            resp = httpx.get(url, timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except RETRYABLE as e:
            if attempt == attempts:
                raise UpstreamError(f"{url} failed after {attempts} attempts") from e
            logger.warning("attempt %d for %s failed: %r", attempt, url, e)
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")
```

Only timeouts and connection failures are retried. A 4xx from `raise_for_status()` propagates at once because retrying a bad request is pointless. `from e` keeps the last network error in the traceback.

**Follow-ups they will ask:**
- How do you also retry 429 and 503?: catch `httpx.HTTPStatusError`, check `e.response.status_code`, and honor a `Retry-After` header.
- Would you hand-roll this in production?: often `tenacity` with `stop_after_attempt`, `wait_random_exponential` and `retry_if_exception_type` is clearer; add jitter either way.
- The async version?: use `await asyncio.sleep`, and never catch `asyncio.CancelledError`.

**Mistakes to avoid:**
- Replacing the bare except with `except Exception: pass`, which still hides bugs.
- Retrying a non-idempotent POST (a payment) without an idempotency key.

### Q. Write a custom exception hierarchy for a payments service and map it to HTTP responses in FastAPI.
**Short answer (45 seconds):** One base class, `PaymentError(Exception)`, with an error code and HTTP status as class attributes and shared fields like `order_id`. Specific subclasses add their own fields. Services raise these domain errors and know nothing about HTTP; one FastAPI exception handler registered on the base class turns any of them into a consistent JSON response.

**Deeper explanation:**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class PaymentError(Exception):
    status_code = 400
    code = "payment_error"

    def __init__(self, message: str, *, order_id: str) -> None:
        super().__init__(message)
        self.order_id = order_id

class CardDeclinedError(PaymentError):
    status_code = 402
    code = "card_declined"

    def __init__(self, order_id: str, decline_code: str) -> None:
        super().__init__(f"card declined: {decline_code}", order_id=order_id)
        self.decline_code = decline_code

class DuplicatePaymentError(PaymentError):
    status_code = 409
    code = "duplicate_payment"

app = FastAPI()

@app.exception_handler(PaymentError)
async def payment_error_handler(request: Request, exc: PaymentError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": str(exc), "order_id": exc.order_id},
    )
```

FastAPI (through Starlette) looks up handlers along the exception's class hierarchy, so the base-class handler also catches `CardDeclinedError` and returns 402 with `{"code": "card_declined", ...}`. Class attributes give every subclass a default status and code without repeating the handler. `order_id` is keyword-only so call sites read clearly. At the boundary with the payment provider, translate its SDK error with `raise CardDeclinedError(order.id, err_code) from err` so the original stays in the traceback but no provider type leaks upward.

**Follow-ups they will ask:**
- Why not raise HTTPException in the service?: it ties business code to HTTP, so the same service cannot run in a queue worker or CLI, and tests need HTTP concepts.
- How do you test it?: `pytest.raises(CardDeclinedError)` on the service and check `exc.value.decline_code`; use `TestClient` once to check the handler.
- What about unexpected errors?: let them become 500, log with a request ID, and return a generic message.

**Mistakes to avoid:**
- Forgetting `super().__init__(message)`: `str(exc)` then shows a tuple of raw arguments like `('ord_1', 'do_not_honor')`.
- Putting card numbers or other personal data into exception messages, which end up in logs.

### Q. Rewrite this JavaScript tool-call parser and its Error subclass in idiomatic Python.
**Short answer (45 seconds):** The Error subclass becomes `class ValidationError(Exception)` with a `field` attribute and no `name` boilerplate. `JSON.parse` becomes `json.loads`, the catch becomes `except json.JSONDecodeError`, and `{ cause: err }` becomes `raise ... from e`. The function does not await anything, so it should be a plain `def`.

**Deeper explanation:** The JavaScript:

```js
class ValidationError extends Error {
  constructor(field, message, options) {
    super(message, options);
    this.name = "ValidationError";
    this.field = field;
  }
}

async function parseToolCall(raw) {
  let args;
  try {
    args = JSON.parse(raw);
  } catch (err) {
    throw new ValidationError("arguments", "model returned invalid JSON", { cause: err });
  }
  if (typeof args?.city !== "string") throw new ValidationError("city", "city is required");
  return args;
}
```

The Python:

```python
import json
from typing import Any

class ToolArgsError(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field

def parse_tool_call(raw: str) -> dict[str, Any]:
    try:
        args = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ToolArgsError("arguments", "model returned invalid JSON") from e
    if not isinstance(args, dict) or not isinstance(args.get("city"), str):
        raise ToolArgsError("city", "city is required")
    return args
```

The JS `catch` catches everything thrown inside `try`; the Python version catches only `JSONDecodeError`, so passing `None` by mistake raises a `TypeError` that points straight at the caller's bug. `isinstance(args, dict)` replaces optional chaining, because the model might return a JSON list or string. The class is renamed to avoid confusion with `pydantic.ValidationError`, which most FastAPI code imports. Making the function `async` in Python would force every caller to `await` it for no benefit.

In a real service, a Pydantic model does all of this: `WeatherArgs.model_validate_json(raw)` raises `pydantic.ValidationError` with the exact field path.

**Follow-ups they will ask:**
- What does the agent loop do with this error?: send `str(e)` back to the model as the tool result so it can correct its arguments, with a retry limit.
- Why keep the field attribute?: callers and metrics can group failures by field without parsing message strings.

**Mistakes to avoid:**
- `except Exception` around `json.loads`, which hides unrelated bugs.
- Raising the new error without `from e`, which loses the parser's line and column.

### Q. Refactor this look-before-you-leap prompt loader to EAFP, and say when you would keep LBYL.
**Short answer (45 seconds):** Replace the `exists` and `access` checks with one read inside try/except `FileNotFoundError`, which removes the race and two extra system calls. Stop returning an empty string for a missing prompt; raise a clear error, because an empty system prompt fails silently in production. Keep the cheap dictionary lookup as `dict.get`.

**Deeper explanation:** The code:

```python
import os

def load_prompt(name: str, cache: dict[str, str]) -> str:
    if name in cache:
        return cache[name]
    path = f"prompts/{name}.txt"
    if os.path.exists(path) and os.access(path, os.R_OK):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        cache[name] = text
        return text
    return ""
```

Refactored:

```python
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent / "prompts"

class PromptNotFoundError(LookupError):
    pass

def load_prompt(name: str, cache: dict[str, str]) -> str:
    if (cached := cache.get(name)) is not None:
        return cached
    if not name.replace("_", "").isalnum():
        raise ValueError(f"invalid prompt name {name!r}")
    try:
        text = (PROMPTS / f"{name}.txt").read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise PromptNotFoundError(name) from e
    cache[name] = text
    return text
```

The file can disappear or change permissions between `exists()` and `open()`, so the check proves nothing; the read is the real test. A `PermissionError` now surfaces as itself instead of looking like "not found". The path is anchored to the module, not the current working directory, and the name check blocks `../` path traversal.

Keep LBYL when the "failure" is the common path and cheap to check (`dict.get` for a cache that misses often), when the check is a business rule rather than a racy resource (`if amount > balance`), and when you must validate all input before starting work that is expensive to undo. Since 3.11 a `try` costs almost nothing when no exception is raised, but raising and catching is still slower than a dictionary check.

**Follow-ups they will ask:**
- Is caching in a module-level dict safe in FastAPI?: per process yes; across Uvicorn workers each process has its own copy.

**Mistakes to avoid:**
- Wrapping the whole function in try/except, which catches unrelated errors.
- Returning a falsy default that hides a missing file.

### Q. Write a function that runs several LLM calls concurrently and handles timeouts and bad responses separately.
**Short answer (45 seconds):** Run the calls in an `asyncio.TaskGroup` (3.11+) with a per-call `asyncio.timeout`. If any fail, the group cancels the rest and raises an `ExceptionGroup`, and `except*` clauses handle each error type, logging differently, before re-raising. If partial results are acceptable, use `gather(return_exceptions=True)` instead.

**Deeper explanation:**

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

class BadResponseError(Exception):
    pass

async def call_llm(prompt: str) -> str:
    async with asyncio.timeout(10):                  # raises TimeoutError
        reply = await client.complete(prompt)
    if not reply.strip():
        raise BadResponseError(f"empty reply for {prompt[:30]!r}")
    return reply

async def summarize_all(prompts: list[str]) -> list[str]:
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(call_llm(p)) for p in prompts]
    except* TimeoutError as eg:
        logger.warning("%d LLM calls timed out", len(eg.exceptions))
        raise
    except* BadResponseError as eg:
        for e in eg.exceptions:
            logger.error("bad LLM response: %s", e)
        raise
    return [t.result() for t in tasks]
```

Each `except*` receives a sub-group with only its matching exceptions, and both clauses run if both types occurred. The bare `raise` re-raises that sub-group, so the caller still gets an `ExceptionGroup` (a FastAPI route would map it to 502 or 504). The first failure cancels the sibling tasks, so you often see one exception even when more would have failed.

For partial results:

```python
results = await asyncio.gather(*(call_llm(p) for p in prompts), return_exceptions=True)
ok = [r for r in results if not isinstance(r, BaseException)]
```

**Follow-ups they will ask:**
- How do you limit concurrency to respect rate limits?: wrap `call_llm` in an `asyncio.Semaphore(5)`.
- Can you return from an `except*` block?: no, `return`, `break` and `continue` there are a `SyntaxError`; set a variable or re-raise.
- What about 3.10?: no TaskGroup or `except*`; use `gather` and inspect the results.

**Mistakes to avoid:**
- Using plain `except TimeoutError` around a TaskGroup; it never matches, because the group raises `ExceptionGroup`.
- Fire-and-forget `create_task` without keeping a reference or awaiting it.

### Practice
- Practice kit: open `python-practice/exercises/p10_errors.py`, implement each function, then run `uv run --with pytest pytest tests/test_p10_errors.py` from the `python-practice` folder.
- In the REPL, trigger `int("x")`, `{}["k"]`, `[][0]` and `None.upper()`, read each exception type, then print `FileNotFoundError.__mro__` and `KeyboardInterrupt.__mro__` to see the hierarchy.
- Inside an `except ValueError as e:` block, raise a `RuntimeError` once with `from e` and once without, and compare the line that joins the two tracebacks.
- Write a `while True:` loop with `time.sleep(1)` inside a bare `except: pass`, press Ctrl+C and watch it survive (quit with `Ctrl+\` or by closing the terminal), then change it to `except Exception:` and try again.

## Files, JSON & Data I/O [Basics]

> This section covers reading and writing files with `open()` and `with`, streaming large files, `pathlib`, JSON, CSV, environment variables, config files, temporary files and binary data. In FastAPI and AI backends you use it to load prompt templates, write JSONL eval datasets and agent traces, import uploaded CSVs, read settings and secrets from the environment, and cache embeddings or run state on disk.

### Why it exists
Every service moves data across the boundary between memory and the outside world: files, JSON from APIs, CSV exports, environment settings. Python ships the basic tools in the standard library (`open`, `pathlib`, `json`, `csv`, `os`, `tempfile`, `tomllib`), so you rarely need a package for them, while Node splits the same job across `fs`, `path`, callbacks and promises. Python file I/O is synchronous and blocking: fine in scripts and workers, but a big read inside an `async def` FastAPI route blocks the event loop. The traps are text encoding, files left open, loading huge files into memory, and types that JSON cannot represent.

### In plain words
A file is like a notebook in a library. `open()` checks the notebook out and hands you a handle; `with` guarantees it goes back to the desk even if you trip on the way. Reading line by line is reading one page at a time instead of photocopying the whole book. JSON and CSV are two agreed handwriting styles so other programs can read your notes. Environment variables are sticky notes the operator puts on the machine before your program starts.

### Walkthrough: open, with and reading big files
1. **open() and its modes**: `open(path, mode, encoding=...)`. `"r"` reads (the default), `"w"` writes and truncates the file the moment it opens, `"a"` appends, `"x"` creates only if the file does not exist (else `FileExistsError`), `"b"` switches to bytes and `"+"` adds the other direction. Always pass `encoding="utf-8"` for text: the default comes from the OS locale, so the same code can decode a file differently on another server.
   ```python
   f = open("notes.txt", "w", encoding="utf-8")
   f.write("first line\n")      # returns the number of characters written
   f.close()                    # easy to forget, which is why with exists
   ```
2. **with closes the file for you**: a file object is a context manager. Leaving the `with` block, normally or through an exception, flushes buffered writes and closes the file. In Node you would write `const fh = await fs.promises.open(p)` and close it in a `finally`.
   ```python
   with open("notes.txt", "a", encoding="utf-8") as f:
       f.write("second line\n")
       print("third line", file=f)    # print can write to a file
   # f is closed here, even if a write raised
   ```
3. **Read small files whole**: `read()` returns one string, `readlines()` a list of lines that keep their `"\n"`, and `read().splitlines()` a list without newlines.
   ```python
   with open("notes.txt", encoding="utf-8") as f:
       text = f.read()
   lines = text.splitlines()    # ['first line', 'second line', 'third line']
   ```
4. **Stream big files line by line**: iterating the file object yields one line at a time from an internal buffer, so a 20 GB log uses roughly constant memory. Each line keeps its trailing newline. `errors="replace"` turns undecodable bytes into a replacement character instead of raising `UnicodeDecodeError` halfway through a huge file.
   ```python
   errors = 0
   with open("app.log", encoding="utf-8", errors="replace") as f:
       for line in f:
           if " ERROR " in line:
               errors += 1
   ```
   ```js
   const rl = readline.createInterface({ input: fs.createReadStream("app.log") });
   for await (const line of rl) if (line.includes(" ERROR ")) errors++;
   ```
5. **Binary files in chunks**: `"rb"` and `"wb"` read and write `bytes` (Node's `Buffer`). Read big binary files in fixed-size chunks, for example to hash an upload.
   ```python
   import hashlib

   def sha256_of(path: str) -> str:
       h = hashlib.sha256()
       with open(path, "rb") as f:
           while chunk := f.read(1024 * 1024):    # 1 MiB at a time
               h.update(chunk)
       return h.hexdigest()
   ```
6. **Temporary files**: `tempfile` creates uniquely named files and folders and can clean them up for you. In pytest, the `tmp_path` fixture gives each test a fresh empty folder as a `Path`.
   ```python
   import tempfile
   from pathlib import Path

   with tempfile.TemporaryDirectory() as tmp:
       work = Path(tmp) / "chunks.jsonl"
       work.write_text('{"id": 1}\n', encoding="utf-8")
   # the folder and everything in it is gone here

   def test_writes_report(tmp_path: Path) -> None:
       out = tmp_path / "report.txt"
       out.write_text("ok", encoding="utf-8")
       assert out.read_text(encoding="utf-8") == "ok"
   ```

### Walkthrough: pathlib, paths as objects
1. **Build paths with /**: `Path` objects join with the `/` operator and use the right separator for the OS. `Path(__file__).resolve().parent` is the folder of the current module, Python's `__dirname`.
   ```python
   from pathlib import Path

   BASE_DIR = Path(__file__).resolve().parent
   prompt_file = BASE_DIR / "prompts" / "summarize.txt"
   ```
   ```js
   const promptFile = path.join(__dirname, "prompts", "summarize.txt");
   ```
2. **Inspect the parts**: `name`, `stem`, `suffix` and `parent` replace string slicing, and `with_suffix` swaps the extension.
   ```python
   p = Path("data/exports/users.2026.csv")
   p.name, p.stem, p.suffix   # ('users.2026.csv', 'users.2026', '.csv')
   p.parent                   # PosixPath('data/exports')
   p.with_suffix(".json")     # PosixPath('data/exports/users.2026.json')
   ```
3. **Read and write in one call**: `read_text`, `write_text`, `read_bytes` and `write_bytes` open and close the file for you. Pass the encoding here too.
   ```python
   cfg = Path("settings.json")
   cfg.write_text('{"debug": true}', encoding="utf-8")
   raw = cfg.read_text(encoding="utf-8")
   ```
4. **Check, create and delete**: `exists()`, `is_file()` and `is_dir()` check; `mkdir(parents=True, exist_ok=True)` is `fs.mkdirSync(p, { recursive: true })`; `unlink(missing_ok=True)` deletes a file without failing if it is already gone.
   ```python
   out_dir = Path("runs") / "2026-11-02"
   out_dir.mkdir(parents=True, exist_ok=True)
   (out_dir / "old.json").unlink(missing_ok=True)
   ```
5. **Find files with glob**: `glob("*.md")` searches one folder and `rglob("*.md")` searches recursively. Both return lazy generators in no guaranteed order, so wrap them in `sorted()` when order matters.
   ```python
   for md in sorted(Path("docs").rglob("*.md")):
       print(md.relative_to("docs"), md.stat().st_size)
   ```
6. **os.path still works**: older code uses `os.path.join`, `os.path.exists` and `os.listdir`. They are fine, but `pathlib` is the modern default, and `open`, `json`, `csv` and `shutil` all accept `Path` objects.

### Walkthrough: JSON, CSV, environment variables and config
1. **json.loads and json.dumps**: the counterparts of `JSON.parse` and `JSON.stringify`. `json.load` and `json.dump` (no "s") read from and write to a file object. Objects become dicts, arrays lists, `null` becomes `None` and `true` becomes `True`. Tuples are written as lists, and non-string keys become strings: `json.loads(json.dumps({1: "a"}))` gives `{'1': 'a'}`.
   ```python
   import json

   data = json.loads('{"model": "gpt-4o", "temperature": 0.2, "stream": false, "stop": null}')
   # {'model': 'gpt-4o', 'temperature': 0.2, 'stream': False, 'stop': None}
   with open("run.json", "w", encoding="utf-8") as f:
       json.dump(data, f, indent=2)
   ```
2. **Formatting options**: `indent=2` pretty-prints, `sort_keys=True` gives stable output for diffs and cache keys, and `ensure_ascii=False` keeps "Zoë" readable instead of escaping it as `"Zoë"`.
   ```python
   json.dumps({"name": "Zoë", "id": 7}, indent=2, sort_keys=True, ensure_ascii=False)
   ```
3. **default= for custom types**: `json.dumps` raises `TypeError: Object of type datetime is not JSON serializable` for `datetime`, `Decimal`, `UUID`, `set` and your own classes. JavaScript calls `Date.prototype.toJSON` automatically; Python wants you to say how. Pass `default=`, a function called for every object the encoder does not know. Reading back gives a plain string; convert it with `datetime.fromisoformat`.
   ```python
   from datetime import datetime, timezone
   from decimal import Decimal
   from uuid import UUID

   def to_jsonable(obj: object) -> object:
       if isinstance(obj, datetime):
           return obj.isoformat()          # '2026-11-02T10:30:00+00:00'
       if isinstance(obj, (Decimal, UUID)):
           return str(obj)
       if isinstance(obj, set):
           return sorted(obj)
       raise TypeError(f"cannot serialize {type(obj).__name__}")

   json.dumps({"at": datetime.now(timezone.utc)}, default=to_jsonable)
   ```
4. **CSV with DictReader and DictWriter**: open CSV files with `newline=""` so the `csv` module controls line endings (otherwise you get blank rows on Windows and broken quoted fields). `DictReader` yields one dict per row keyed by the header, and every value is a string, so convert types yourself. `extrasaction="ignore"` lets `DictWriter` drop keys that are not in `fieldnames` instead of raising `ValueError`.
   ```python
   import csv

   with open("users.csv", newline="", encoding="utf-8") as f:
       rows = [{**r, "age": int(r["age"])} for r in csv.DictReader(f)]

   with open("adults.csv", "w", newline="", encoding="utf-8") as f:
       writer = csv.DictWriter(f, fieldnames=["name", "age"], extrasaction="ignore")
       writer.writeheader()
       writer.writerows(r for r in rows if r["age"] >= 18)
   ```
5. **Environment variables**: `os.environ` is a mapping of strings to strings. `os.environ["KEY"]` raises `KeyError` when the variable is missing, which is what you want for required secrets (fail at startup); `os.getenv("KEY", "default")` returns the default or `None`. Values are always strings, like `process.env`.
   ```python
   import os

   api_key = os.environ["OPENAI_API_KEY"]          # crash at startup if missing
   port = int(os.getenv("PORT", "8000"))
   debug = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}
   # bool(os.getenv("DEBUG")) is True for "false" and "0": any non-empty string is truthy
   ```
6. **Config files and settings classes**: `tomllib` (3.11+) reads TOML and needs a file opened in `"rb"`; the `python-dotenv` package loads `.env` files; in FastAPI apps, `pydantic-settings` reads environment variables and `.env`, converts types and fails fast on bad values.
   ```python
   import tomllib

   from pydantic_settings import BaseSettings, SettingsConfigDict

   with open("pyproject.toml", "rb") as f:          # tomllib wants binary mode
       project = tomllib.load(f)["project"]

   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file=".env")
       openai_api_key: str                         # read from OPENAI_API_KEY
       port: int = 8000
       debug: bool = False                         # "false", "0", "no" all parse correctly
   ```

### Concepts you must understand
- Always pass `encoding="utf-8"` when opening text files; the default depends on the OS locale.
- Use `with` for every open file; it flushes and closes even when an exception is raised.
- `"w"` truncates the file as soon as it opens, `"x"` refuses to overwrite, `"a"` appends.
- Iterate the file object to stream line by line; `read()` and `readlines()` load the whole file into memory.
- `pathlib.Path` is the modern path API: join with `/`, `read_text`/`write_text`, `mkdir(parents=True, exist_ok=True)`, `glob`/`rglob`.
- `json.dumps` cannot serialize `datetime`, `Decimal`, `UUID`, `set` or your classes; pass `default=` and parse back explicitly. Non-string keys become strings.
- CSV files need `newline=""`, and `DictReader` returns strings only, so convert and validate every field.
- Environment variables are strings or missing: `os.environ[...]` for required values, `os.getenv` with a default for optional ones, and never `bool()` a string.
- File I/O blocks: in FastAPI, do heavy file work in a plain `def` route (it runs in a thread pool) or with `asyncio.to_thread`.
- Write important files atomically: write a temporary file in the same folder, then `os.replace` it over the target.

| JavaScript | Python | Note |
|---|---|---|
| `fs.readFileSync(p, "utf8")` | `Path(p).read_text(encoding="utf-8")` | both block; Python has no built-in async file API |
| `fs.writeFileSync(p, s)` | `Path(p).write_text(s, encoding="utf-8")` | `"w"` semantics: truncates first |
| `fs.createReadStream` plus `readline` | `for line in f:` inside `with open(...)` | streaming, constant memory |
| `path.join(__dirname, "a", "b")` | `Path(__file__).resolve().parent / "a" / "b"` | `/` joins paths |
| `fs.mkdirSync(p, { recursive: true })` | `p.mkdir(parents=True, exist_ok=True)` | no error if it exists |
| `fs.existsSync(p)` | `p.exists()` | prefer EAFP before reading |
| `JSON.parse(s)` / `JSON.stringify(o, null, 2)` | `json.loads(s)` / `json.dumps(o, indent=2)` | `load`/`dump` work on files |
| `Date` serializes itself via `toJSON` | `default=` plus `.isoformat()` | Python raises `TypeError` otherwise |
| `process.env.PORT` | `os.getenv("PORT")` or `os.environ["PORT"]` | always `str` or missing |
| `Buffer` | `bytes` / `bytearray` | from `"rb"` mode |
| `fs.mkdtemp(path.join(os.tmpdir(), "x-"))` | `tempfile.TemporaryDirectory()` | removed when the `with` block ends |
| `csv-parse` or `papaparse` package | standard library `csv` module | values are strings |

### Q. Write a function that counts ERROR lines per service in a 20 GB log file without running out of memory.
**Short answer (45 seconds):** Open the file in a `with` block and iterate the file object, which reads one buffered line at a time. Split each line just enough to get the level and service, and count with a `Counter`. Memory grows with the number of services, not the size of the file.

**Deeper explanation:** Assume lines like `2026-11-02T10:30:00Z ERROR payments timeout calling provider`.

```python
from collections import Counter
from pathlib import Path

def errors_per_service(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split(maxsplit=3)       # timestamp, level, service, rest
            if len(parts) >= 3 and parts[1] == "ERROR":
                counts[parts[2]] += 1
    return counts

# errors_per_service(Path("app.log")).most_common(5)
```

The `for line in f` loop never holds more than one line plus a read buffer, so a 20 GB file needs only a few megabytes. `maxsplit=3` stops splitting after the fields we need, which saves work on long messages. `errors="replace"` means one corrupt byte does not abort the run after 15 GB. The length check skips blank and malformed lines instead of raising `IndexError`. Time is O(n) in the file size; memory is O(number of services). The job is I/O bound, so for many files you would process files in parallel with `multiprocessing`, not threads inside one file.

For compressed logs, `gzip.open(path, "rt", encoding="utf-8")` returns the same line iterator, so the loop does not change.

**Follow-ups they will ask:**
- The logs are JSON lines?: `json.loads(line)` per line inside try/except `json.JSONDecodeError`, counting bad lines separately.
- The file lives in S3?: stream the object body and iterate its lines instead of downloading it first.
- How do you test it?: write a small log into pytest's `tmp_path` and assert on the `Counter`.

**Mistakes to avoid:**
- `f.read().splitlines()` or `f.readlines()`, which load all 20 GB into memory.
- Compiling a regex inside the loop instead of once at module level.
- Omitting `encoding`, so the result depends on the machine.

### Q. This export endpoint crashes with TypeError: Object of type datetime is not JSON serializable. Fix it.
**Short answer (45 seconds):** `json.dumps` only knows dicts, lists, strings, numbers, booleans and `None`. The quick fix is a `default=` function that converts `datetime`, `Decimal`, `UUID` and `set`. The better FastAPI fix is to stop calling `json.dumps` by hand and return a Pydantic response model, which serializes these types correctly.

**Deeper explanation:** The code:

```python
@app.get("/runs/export")
def export_runs() -> Response:
    runs = db.fetch_runs()    # rows with datetime, UUID, Decimal and set values
    return Response(json.dumps(runs), media_type="application/json")
```

The encoder fails on the first value it does not know, here a `datetime`; fix that and it fails next on `UUID`. Quick fix:

```python
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

def to_jsonable(obj: object) -> object:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (UUID, Decimal)):
        return str(obj)                  # str keeps money exact; float would round
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

return Response(json.dumps(runs, default=to_jsonable), media_type="application/json")
```

Keep the final `raise TypeError`, otherwise unknown objects silently turn into something wrong. The FastAPI way:

```python
class RunOut(BaseModel):
    id: UUID
    started_at: datetime
    cost: Decimal
    tags: set[str]

@app.get("/runs/export", response_model=list[RunOut])
def export_runs() -> list[dict]:
    return db.fetch_runs()
```

Pydantic v2 writes `started_at` as an ISO 8601 string, `id` as a string, `cost` as the string `"0.0042"` and `tags` as a list. Returning a plain dict also works because FastAPI runs `jsonable_encoder`, but that turns `Decimal` into a float, which is risky for money. The response model also documents the shape in OpenAPI and filters out fields you did not mean to expose.

**Follow-ups they will ask:**
- How does the client read the dates back?: `datetime.fromisoformat(s)` in Python, `new Date(s)` in JS; always send timezone-aware UTC values.
- Why not `default=str` everywhere?: it serializes anything, including objects you should never expose, and the format is not controlled.

**Mistakes to avoid:**
- Converting `Decimal` to `float` for money amounts.
- Sending naive datetimes with no timezone offset.

### Q. Write a FastAPI endpoint that imports an uploaded users CSV and reports bad rows by line number.
**Short answer (45 seconds):** Accept an `UploadFile`, wrap its binary file in `io.TextIOWrapper` with `utf-8-sig` and `newline=""`, and stream it through `csv.DictReader`. Check the header once and reject missing columns with 422. Validate each row, collect errors with `reader.line_num`, and return the counts. Use a plain `def` route so parsing runs in the thread pool.

**Deeper explanation:**

```python
import csv
import io

from fastapi import FastAPI, HTTPException, UploadFile

app = FastAPI()
REQUIRED = {"name", "email", "age"}

@app.post("/users/import")
def import_users(file: UploadFile) -> dict:
    text = io.TextIOWrapper(file.file, encoding="utf-8-sig", newline="")
    reader = csv.DictReader(text)
    missing = REQUIRED - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(status_code=422, detail=f"missing columns: {sorted(missing)}")
    valid, errors = [], []
    for row in reader:
        line = reader.line_num
        email = (row["email"] or "").strip().lower()
        try:
            age = int(row["age"])
        except (TypeError, ValueError):
            errors.append({"line": line, "error": f"bad age {row['age']!r}"})
            continue
        if "@" not in email:
            errors.append({"line": line, "error": "invalid email"})
            continue
        valid.append({"name": row["name"].strip(), "email": email, "age": age})
    # save `valid` in one transaction here
    return {"imported": len(valid), "errors": errors}
```

`UploadFile.file` is a binary spooled temporary file, so `TextIOWrapper` decodes it lazily instead of reading it all into a string. `utf-8-sig` strips the byte order mark Excel adds, which otherwise turns the first header into `"﻿name"` and makes `row["name"]` fail. `reader.line_num` is the physical line where the row ended, which stays correct when a quoted field contains a newline (counting rows with `enumerate` would drift). A short row gives `None` for missing fields, hence the `or ""` and the `TypeError` in the except. Form uploads need the `python-multipart` package installed.

**Follow-ups they will ask:**
- The file has 2 million rows?: insert in batches of about 1,000 and return a job ID, processing in a background worker.
- All or nothing?: validate everything first, and write only if `errors` is empty, in one transaction.
- Validate with Pydantic instead?: `UserRow.model_validate(row)` per row, collecting `ValidationError.errors()`.

**Mistakes to avoid:**
- `await file.read()` then `.decode()` on a huge upload: the whole file sits in memory twice.
- Forgetting `newline=""`, which breaks quoted multi-line fields.

### Q. Rewrite this Node.js eval-report script in idiomatic Python with pathlib.
**Short answer (45 seconds):** Anchor paths at `Path(__file__).resolve().parent`, create the output folder with `mkdir(parents=True, exist_ok=True)`, loop over `sorted(in_dir.glob("*.json"))`, and read each file with `read_text` plus `json.loads`. Sort with `key=` and `reverse=True` instead of a comparator, and write the result with `write_text`.

**Deeper explanation:** The JavaScript:

```js
const fs = require("fs");
const path = require("path");

const inDir = path.join(__dirname, "evals");
const outDir = path.join(__dirname, "reports");
fs.mkdirSync(outDir, { recursive: true });

const summary = [];
for (const file of fs.readdirSync(inDir)) {
  if (!file.endsWith(".json")) continue;
  const data = JSON.parse(fs.readFileSync(path.join(inDir, file), "utf8"));
  summary.push({ name: path.basename(file, ".json"), score: data.score ?? 0 });
}
summary.sort((a, b) => b.score - a.score);
fs.writeFileSync(path.join(outDir, "summary.json"), JSON.stringify(summary, null, 2));
```

The Python:

```python
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
in_dir = BASE / "evals"
out_dir = BASE / "reports"
out_dir.mkdir(parents=True, exist_ok=True)

summary = []
for file in sorted(in_dir.glob("*.json")):
    data = json.loads(file.read_text(encoding="utf-8"))
    score = data.get("score")
    summary.append({"name": file.stem, "score": 0 if score is None else score})

summary.sort(key=lambda row: row["score"], reverse=True)
(out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
```

`glob("*.json")` replaces the `readdirSync` plus `endsWith` filter, and `file.stem` replaces `path.basename(file, ".json")`. JS `??` replaces both a missing key and `null`; `data.get("score", 0)` would only cover the missing key and return `None` for `"score": null`, so the explicit `is None` check keeps the exact semantics. `data.get("score") or 0` would also work here, but `or` replaces every falsy value, which bites when the value can legitimately be `""` or `False`. Python's sort is stable, so equal scores keep the alphabetical order from `sorted(glob)`, which makes the report deterministic.

**Follow-ups they will ask:**
- One file has broken JSON?: catch `json.JSONDecodeError` per file, record the file name, and continue.
- You really need a two-argument comparator?: `functools.cmp_to_key(compare)`.

**Mistakes to avoid:**
- Building paths with string concatenation and `"/"`.
- Using relative paths like `"evals"`, which depend on the directory the script is launched from.

### Q. Predict what this settings module does when DEBUG=false and TIMEOUT_SECONDS is unset, then fix it.
**Short answer (45 seconds):** The import crashes with a `TypeError` on the `TIMEOUT` line because `int(None)` is invalid. Even when that variable is set, `DEBUG` becomes `True` because `bool("false")` is `True`, `MAX_TOKENS` changes type depending on the environment, and a missing API key is not noticed until the first request. Replace it with a `pydantic-settings` class that converts types and fails fast with a clear message.

**Deeper explanation:** The code:

```python
import os

DEBUG = bool(os.getenv("DEBUG"))
MAX_TOKENS = os.getenv("MAX_TOKENS", 1024)
TIMEOUT = int(os.environ.get("TIMEOUT_SECONDS"))
API_KEY = os.getenv("OPENAI_API_KEY")
```

Line by line: `DEBUG` is `bool("false")`, which is `True` because any non-empty string is truthy, so debug mode is on in production. `MAX_TOKENS` is the int `1024` when unset but the string `"2048"` when set, so `MAX_TOKENS + 100` works locally and raises `TypeError` in production. `TIMEOUT` raises `TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'` at import time, so the app does not start, with an error that does not name the variable. `API_KEY` silently becomes `None` and fails later as an authentication error from the provider.

The fix:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    debug: bool = False
    max_tokens: int = 1024
    timeout_seconds: float = 30.0
    openai_api_key: str = Field(min_length=1)

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Field names match environment variables case-insensitively, so `openai_api_key` reads `OPENAI_API_KEY`. `"false"`, `"0"` and `"no"` parse to `False`; `"maybe"` raises a validation error naming `debug`. A missing key raises at startup with the field name. `lru_cache` builds it once, and FastAPI routes take it with `Depends(get_settings)`, which tests can override.

**Follow-ups they will ask:**
- Without Pydantic?: small helpers like `env_bool(name, default)` that accept a fixed set of strings and raise `ValueError` for anything else.
- Should secrets live in `.env` in production?: no, inject them from a secret manager as environment variables; `.env` is for local development.

**Mistakes to avoid:**
- `bool(os.getenv(...))` for flags.
- Passing a non-string default to `os.getenv`, which makes the type depend on the environment.

### Q. Write an append-only JSONL writer for agent traces and a reader that survives a crash mid-write.
**Short answer (45 seconds):** Write one compact `json.dumps` per line in append mode, ending with `"\n"`, so a crash can only damage the final line. The reader is a generator that parses line by line, skips blank lines, and treats an unparseable last line without a trailing newline as a torn write to ignore, while corruption in the middle raises an error with the line number.

**Deeper explanation:**

```python
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

def append_event(path: Path, event: dict[str, Any]) -> None:
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"), default=str)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_events(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                if not line.endswith("\n"):     # torn final write from a crash
                    return
                raise ValueError(f"{path}:{line_no} is not valid JSON") from e
```

`json.dumps` without `indent` never emits a raw newline (newlines inside strings become `\n` escapes), so one event is exactly one line. Append mode always writes at the end of the file, and earlier lines are never rewritten, so a crash leaves at most one partial line at the end. Only the last line can lack its newline, which is how the reader tells a torn write from real corruption. The reader is a generator, so a 5 GB trace file streams in constant memory, and `separators` makes lines compact. `default=str` is a blunt fallback for trace data; use a real `default` function for data you will parse back.

For a whole-state file that is rewritten (not appended), use a different pattern: write to a temporary file in the same folder, then `os.replace(tmp, path)`, which swaps it in atomically.

**Follow-ups they will ask:**
- Several processes write the same file?: use one writer process or a file lock (for example the `filelock` package); better, send events to a queue or a database.
- Must each event survive a power cut?: call `f.flush()` and `os.fsync(f.fileno())` after the write, at a throughput cost.

**Mistakes to avoid:**
- `json.dump(event, f, indent=2)` in a JSONL file, which spreads one event over many lines.
- Reading JSONL with `json.load(f)`, which fails with `Extra data: line 2 column 1`.

### Practice
- Practice kit: open `python-practice/exercises/p11_files_json.py`, implement each function, then run `uv run --with pytest pytest tests/test_p11_files_json.py` from the `python-practice` folder.
- In the REPL, run `json.loads(json.dumps({1: "a", "t": (1, 2), "n": None}))` and note which keys and types changed on the round trip.
- Write 500,000 fake log lines to a temporary file, then count ERROR lines once with `for line in f` and once with `f.read().splitlines()`, timing both with `time.perf_counter()` and watching memory in Activity Monitor.
- From a shell, run `DEBUG=false python3 -c 'import os; print(bool(os.getenv("DEBUG")))'` and explain the output.

## Object-Oriented Python [Core]

> This section covers classes, `__init__` and `self`, instance and class attributes, instance methods, `@classmethod`, `@staticmethod`, `@property`, inheritance and `super()`, the method resolution order, dunder methods, abstract base classes, composition and Python's "private by convention". In FastAPI and AI backends, Pydantic and SQLAlchemy models are classes, services and repositories are classes injected with `Depends`, LLM provider adapters sit behind an ABC or a Protocol, custom exceptions are classes, and dunder methods are why `len()`, `in`, sorting and `==` work on your own objects.

### Why it exists
Classes bundle data with the functions that keep that data valid, so a rule like "balance never goes negative" lives in one place instead of in every caller. Python's object model runs on protocols: `len(x)` calls `x.__len__()`, a `for` loop calls `__iter__`, and `==` calls `__eq__`, so your classes can behave like built-in types instead of exposing `getLength()` style methods. Python keeps classes lighter than Java or NestJS: no access modifiers, no `interface` keyword, explicit `self`, and duck typing, so you often need fewer classes. The cost is that little is enforced: privacy is a naming convention, and a shared class attribute or a missing `super()` call fails quietly.

### In plain words
A class is a cookie cutter and each instance is a cookie. Every cookie has its own toppings (instance attributes), but they all share the cutter's shape (class attributes and methods). `self` is the specific cookie being decorated right now, passed in by hand. Dunder methods are the standard sockets in the wall: if your appliance has the right plug, such as `__len__` or `__iter__`, it works with every outlet Python already has, such as `len()` and `for` loops.

### Walkthrough: classes, self, attributes and methods
1. **A class and __init__**: `__init__` runs after the object is created and sets instance attributes on `self`. There is no `new`, and `self` is an explicit first parameter of every instance method: `acct.deposit(50)` is just `Account.deposit(acct, 50)`.
   ```python
   class Account:
       def __init__(self, owner: str, balance: float = 0.0) -> None:
           self.owner = owner
           self.balance = balance

       def deposit(self, amount: float) -> float:
           self.balance += amount
           return self.balance

   acct = Account("Asha")       # JS: new Account("Asha")
   acct.deposit(50)             # the same call as Account.deposit(acct, 50)
   ```
   In a JS class you can declare per-instance fields in the class body (`balance = 0;`). In Python, an assignment in the class body creates a class attribute instead, which is the next step.
2. **Instance vs class attributes**: a name assigned in the class body belongs to the class and is shared by all instances. Attribute lookup checks the instance first, then the class. Assigning through an instance creates an instance attribute that shadows the class one.
   ```python
   class Account:
       bank = "Acme Bank"              # class attribute, shared
       def __init__(self, owner: str) -> None:
           self.owner = owner          # instance attribute

   a, b = Account("A"), Account("B")
   Account.bank = "New Bank"
   print(a.bank, b.bank)               # New Bank New Bank
   a.bank = "Mine"                     # creates a.bank; b still sees the class value
   ```
3. **The shared mutable class attribute trap**: a list or dict in the class body is one object shared by every instance, so appending through one instance changes what all of them see. Create mutable state in `__init__`. The mutable default argument `def __init__(self, items=[])` is the same bug in another place.
   ```python
   class Cart:
       items: list[str] = []           # BUG: one list for every Cart
       def add(self, item: str) -> None:
           self.items.append(item)     # mutates the shared class list

   c1, c2 = Cart(), Cart()
   c1.add("book")
   print(c2.items)                     # ['book']

   class Cart:
       def __init__(self) -> None:
           self.items: list[str] = []  # fixed: a new list per instance
   ```
4. **Bound methods keep self**: `f = acct.deposit` stores a bound method that remembers `acct`, so passing methods as callbacks just works. In JS, `const f = obj.method; f()` loses `this` unless you use `bind` or an arrow function.
   ```python
   deposit = acct.deposit
   deposit(10)                          # works, self is acct
   handlers = {"deposit": acct.deposit} # safe to store and call later
   ```
5. **@classmethod and @staticmethod**: a classmethod receives the class as `cls` and is the standard way to write alternative constructors; because it calls `cls(...)`, a subclass gets an instance of itself. A staticmethod receives neither `self` nor `cls`; it is a plain function grouped under the class, and often a module-level function is simpler.
   ```python
   from datetime import datetime

   class Event:
       def __init__(self, name: str, at: datetime) -> None:
           self.name, self.at = name, at

       @classmethod
       def from_dict(cls, data: dict) -> "Event":
           return cls(data["name"], datetime.fromisoformat(data["at"]))

       @staticmethod
       def is_valid_name(name: str) -> bool:
           return name.isidentifier()

   e = Event.from_dict({"name": "deploy", "at": "2026-11-02T10:00:00"})
   ```
   The JS equivalent is `static fromJSON(data) { return new this(data.name, new Date(data.at)); }`.
6. **@property for computed values and validation**: a property looks like an attribute to callers but runs a method. Add a setter to validate; leave it out to make the attribute read-only. You can start with a plain attribute and switch to a property later without changing any caller, which is why Python code does not write `getX()` and `setX()`.
   ```python
   class Order:
       def __init__(self, quantity: int) -> None:
           self.quantity = quantity        # goes through the setter below

       @property
       def quantity(self) -> int:
           return self._quantity

       @quantity.setter
       def quantity(self, value: int) -> None:
           if value < 1:
               raise ValueError("quantity must be at least 1")
           self._quantity = value

   o = Order(2)
   o.quantity = 0                          # ValueError
   ```
   JS has the same idea with `get quantity()` and `set quantity(v)`.
7. **"Private" by convention**: Python has no `private` keyword. One leading underscore (`_session`) means "internal, do not touch": readers, linters and IDEs respect it, but nothing stops access. Two leading underscores (`__token`) trigger name mangling to `_Client__token`, which prevents accidental clashes in subclasses but is not security. JS `#private` fields are truly private.
   ```python
   class Client:
       def __init__(self, token: str) -> None:
           self._session = None          # internal by convention
           self.__token = token          # stored as _Client__token

   c = Client("t")
   c._session                            # allowed, just impolite
   c.__token                             # AttributeError
   c._Client__token                      # 't': renamed, not hidden
   ```

### Walkthrough: inheritance, super(), MRO, abstract classes and composition
1. **Inherit and extend with super()**: `class Child(Parent)` inherits every method; redefine a method to override it, and call `super()` to reuse the parent's version. Call `super().__init__(...)` so the parent sets up its attributes. Unlike JS, where `super()` must run before `this` is used, Python treats it as an ordinary call, so forgetting it is not an error until a missing attribute is read.
   ```python
   class Notifier:
       def __init__(self, sender: str) -> None:
           self.sender = sender

       def send(self, to: str, text: str) -> str:
           return f"{self.sender} to {to}: {text}"

   class SmsNotifier(Notifier):
       def __init__(self, sender: str, max_len: int = 160) -> None:
           super().__init__(sender)          # JS: super(sender)
           self.max_len = max_len

       def send(self, to: str, text: str) -> str:
           return super().send(to, text[: self.max_len])

   isinstance(SmsNotifier("ops"), Notifier)  # True: subclasses count
   ```
2. **Method resolution order**: with multiple inheritance, Python computes one linear order of classes (the C3 linearization, visible as `Class.__mro__`), and every attribute lookup and `super()` call follows it. `super()` means "the next class in this object's MRO", not "my parent", which is what makes cooperative mixins work. JS classes have single inheritance only.
   ```python
   class Base:
       def save(self) -> list[str]:
           return ["Base"]

   class TimestampMixin(Base):
       def save(self) -> list[str]:
           return ["Timestamp", *super().save()]

   class AuditMixin(Base):
       def save(self) -> list[str]:
           return ["Audit", *super().save()]

   class Order(TimestampMixin, AuditMixin):
       pass

   print([c.__name__ for c in Order.__mro__])  # ['Order', 'TimestampMixin', 'AuditMixin', 'Base', 'object']
   print(Order().save())                       # ['Timestamp', 'Audit', 'Base']
   ```
   Inside an `Order`, `TimestampMixin`'s `super()` goes to `AuditMixin`, its sibling, not to `Base`.
3. **Abstract base classes**: inherit from `abc.ABC` and mark required methods with `@abstractmethod`. Python refuses to instantiate any class that still has an unimplemented abstract method, which suits a provider or plugin interface. Concrete helper methods can live on the ABC too.
   ```python
   from abc import ABC, abstractmethod

   class LLMProvider(ABC):
       @abstractmethod
       async def complete(self, prompt: str) -> str: ...

       async def complete_many(self, prompts: list[str]) -> list[str]:
           return [await self.complete(p) for p in prompts]

   class FakeProvider(LLMProvider):
       async def complete(self, prompt: str) -> str:
           return f"echo: {prompt}"

   FakeProvider()      # fine
   LLMProvider()       # TypeError: Can't instantiate abstract class LLMProvider without an
                       # implementation for abstract method 'complete'   (3.12 wording)
   ```
   This is the TypeScript `abstract class`, except that the check happens at runtime when you instantiate.
4. **Protocol for structural typing**: `typing.Protocol` describes a shape. Any class with matching methods satisfies it for the type checker, with no inheritance, exactly like a TypeScript `interface`.
   ```python
   from typing import Protocol

   class SupportsComplete(Protocol):
       async def complete(self, prompt: str) -> str: ...

   async def summarize(llm: SupportsComplete, text: str) -> str:
       return await llm.complete(f"Summarize: {text}")
   ```
5. **Composition over inheritance**: instead of subclass chains like `CachedRetryingOpenAIClient`, give a class the objects it needs and delegate to them. Each piece stays small, testable and swappable (a fake provider in tests), and FastAPI's `Depends` can wire them together. Inherit for a true "is a" with shared behavior (custom exceptions, framework bases like Pydantic's `BaseModel`); compose for "uses a".
   ```python
   class ChatService:
       def __init__(self, llm: LLMProvider, history: "HistoryRepo") -> None:
           self.llm = llm               # has a provider, is not a provider
           self.history = history

       async def reply(self, user_id: str, message: str) -> str:
           context = await self.history.last(user_id, n=10)
           answer = await self.llm.complete(f"{context}\nUser: {message}")
           await self.history.add(user_id, message, answer)
           return answer
   ```

### Walkthrough: dunder methods that make objects feel built in
1. **__repr__ and __str__**: `__repr__` is for developers (REPL, logs, debugger, and items inside a printed list); `__str__` is for end users and `print()`. If you define only `__repr__`, `str()` falls back to it, so write `__repr__` first. The JS cousins are `toString()` and `util.inspect.custom`.
   ```python
   class Money:
       def __init__(self, cents: int, currency: str) -> None:
           self.cents, self.currency = cents, currency

       def __repr__(self) -> str:
           return f"Money({self.cents!r}, {self.currency!r})"   # Money(1050, 'INR')

       def __str__(self) -> str:
           return f"{self.cents / 100:.2f} {self.currency}"     # 10.50 INR

   print([Money(1050, "INR")])    # [Money(1050, 'INR')]: containers show repr
   ```
2. **__eq__ and __hash__**: by default `==` compares identity, like `===` on JS objects. Define `__eq__` for value equality; Python then sets `__hash__` to `None`, so instances can no longer go in a set or be dict keys, until you define `__hash__` over the same fields. Hash only fields that never change, and return `NotImplemented` for types you do not handle so Python can try the other operand.
   ```python
   class Money:
       def __init__(self, cents: int, currency: str) -> None:
           self.cents, self.currency = cents, currency

       def __eq__(self, other: object) -> bool:
           if not isinstance(other, Money):
               return NotImplemented
           return (self.cents, self.currency) == (other.cents, other.currency)

       def __hash__(self) -> int:
           return hash((self.cents, self.currency))

   {Money(5, "INR"), Money(5, "INR")}    # one element
   ```
3. **The container protocol**: `__len__` powers `len()` and truthiness, `__iter__` powers `for`, unpacking and `list()`, `__getitem__` powers `obj[i]` and slices, and `__contains__` powers `in`. Delegating to an internal list is usually enough.
   ```python
   class Conversation:
       def __init__(self) -> None:
           self._messages: list[dict] = []

       def add(self, role: str, content: str) -> None:
           self._messages.append({"role": role, "content": content})

       def __len__(self) -> int:
           return len(self._messages)

       def __iter__(self):
           return iter(self._messages)

       def __getitem__(self, index):
           return self._messages[index]          # ints and slices both work

       def __contains__(self, text: object) -> bool:
           return any(m["content"] == text for m in self._messages)

   conv = Conversation()
   conv.add("user", "hi")
   len(conv), conv[-1]["role"], "hi" in conv, bool(conv)   # (1, 'user', True, True)
   ```
   JS only has `[Symbol.iterator]()` for this; there is no hook for `.length` or `in`.
4. **Ordering with __lt__ and total_ordering**: `sorted()`, `min()` and `max()` need only `__lt__`. `functools.total_ordering` fills in `<=`, `>` and `>=` from `__eq__` and `__lt__`. In JS you would pass a comparator to `sort` instead.
   ```python
   from functools import total_ordering

   @total_ordering
   class Version:
       def __init__(self, text: str) -> None:
           self.parts = tuple(int(p) for p in text.split("."))

       def __eq__(self, other: object) -> bool:
           if not isinstance(other, Version):
               return NotImplemented
           return self.parts == other.parts

       def __lt__(self, other: "Version") -> bool:
           return self.parts < other.parts       # tuples compare item by item

       def __hash__(self) -> int:
           return hash(self.parts)

   sorted([Version("1.10.0"), Version("1.9.2")])   # 1.9.2 first, unlike string sorting
   Version("2.0") >= Version("1.9")                  # True, generated by total_ordering
   ```
5. **__call__**: instances with `__call__` can be called like functions. Use it for a function that carries configuration or state, such as a permission check. FastAPI accepts such instances as dependencies: `Depends(RequireRole("admin"))`.
   ```python
   class RequireRole:
       def __init__(self, role: str) -> None:
           self.role = role

       def __call__(self, user: dict) -> dict:
           if self.role not in user.get("roles", []):
               raise PermissionError(f"needs role {self.role}")
           return user

   admin_only = RequireRole("admin")
   admin_only({"roles": ["admin"]})     # called like a function
   ```
6. **dataclasses write the boilerplate**: `@dataclass` generates `__init__`, `__repr__` and `__eq__` from annotated fields; `frozen=True` makes instances immutable and hashable, and `order=True` adds comparisons. Use it for plain data holders and write dunders by hand only when you need custom behavior.
   ```python
   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class Price:
       cents: int
       currency: str = "INR"

   @dataclass
   class Cart:
       items: list[str] = field(default_factory=list)   # mutable defaults need a factory
   ```

### Concepts you must understand
- `self` is explicit: `obj.method(x)` is `Class.method(obj, x)`, and a bound method keeps its instance when passed around.
- Names assigned in the class body are class attributes shared by every instance; put per-instance and mutable state in `__init__`.
- Use `@classmethod` with `cls` for alternative constructors, `@staticmethod` rarely, and `@property` instead of getter and setter methods.
- `super()` follows the MRO of the actual object, so with multiple inheritance it can call a sibling class, not the parent.
- Privacy is a convention: `_name` means internal, `__name` is mangled to `_Class__name` to avoid subclass clashes, and nothing is truly private.
- Dunder methods plug your class into syntax and built-ins: `len`, `for`, `in`, `[]`, `==`, `<`, `hash`, `print` and calling.
- Defining `__eq__` removes `__hash__`; define both from the same immutable fields or instances cannot go in sets or be dict keys.
- Return `NotImplemented` (not `False`, and do not raise) from comparison dunders for types you do not handle.
- ABCs enforce required methods when a subclass is instantiated; Protocols describe shapes structurally, like TypeScript interfaces.
- Prefer composition and dependency injection for services; keep inheritance for true "is a" relationships and framework base classes.

| JavaScript | Python | Note |
|---|---|---|
| `constructor(a) { this.a = a }` and `new User(a)` | `def __init__(self, a): self.a = a` and `User(a)` | no `new`; `self` is explicit |
| `this` (lost when a method is passed as a callback) | `self` (bound methods keep it) | no `bind` needed |
| `static create() { return new this() }` | `@classmethod def create(cls): return cls()` | `cls` respects subclasses |
| `get total()` / `set total(v)` | `@property` / `@total.setter` | read-only if there is no setter |
| `#secret` field | `_secret` or `__secret` | convention and name mangling only |
| `class B extends A` with `super(x)` | `class B(A):` with `super().__init__(x)` | Python's call can be forgotten silently |
| single inheritance, mixins as functions | multiple inheritance with an MRO | `super()` follows the MRO |
| `abstract class` (TypeScript) | `class X(ABC)` with `@abstractmethod` | checked at runtime on instantiation |
| `interface` (TypeScript) | `typing.Protocol` | structural, checked by the type checker |
| `toString()` | `__str__` and `__repr__` | repr is for developers |
| `[Symbol.iterator]()` | `__iter__` | also `__len__`, `__getitem__`, `__contains__` |
| no operator overloading | `__eq__`, `__lt__`, `__add__`, `__call__` | use `functools.total_ordering` for the rest |

### Q. Predict the output of this Agent class and fix the shared-state bug.
**Short answer (45 seconds):** `tools` is a class attribute and `memory` defaults to one list created when the function was defined, so both lists are shared by every agent and the second agent sees the first one's data. Assigning `b.tools = [...]` creates an instance attribute only on `b`. The fix is to create both lists in `__init__`, with `None` as the default.

**Deeper explanation:** The code:

```python
class Agent:
    tools = []

    def __init__(self, name, memory=[]):
        self.name = name
        self.memory = memory

    def add_tool(self, tool):
        self.tools.append(tool)

    def remember(self, fact):
        self.memory.append(fact)

a, b = Agent("a"), Agent("b")
a.add_tool("search")
a.remember("user likes Python")
print(b.tools, b.memory)
b.tools = ["calc"]
print(a.tools, b.tools, Agent.tools)
```

The output:

```text
['search'] ['user likes Python']
['search'] ['calc'] ['search']
```

`self.tools.append` finds no `tools` on the instance, falls back to the class, and mutates the single class-level list. The default `memory=[]` is evaluated once, when `def` runs, so every agent created without a `memory` argument shares that one list. In a FastAPI app this leaks one user's conversation memory into another user's agent. `b.tools = ["calc"]` is an assignment, not a mutation, so it creates `b.tools` on the instance and shadows the class list for `b` only.

The fix:

```python
class Agent:
    def __init__(self, name: str, memory: list[str] | None = None) -> None:
        self.name = name
        self.tools: list[str] = []
        self.memory = list(memory) if memory is not None else []
```

`list(memory)` also copies a list the caller passes in, so later changes on either side stay separate. With a dataclass, `tools: list[str] = field(default_factory=list)` does the same; `@dataclass` refuses a bare `[]` default with a `ValueError`.

**Follow-ups they will ask:**
- When is a class attribute correct?: for immutable shared values such as constants, defaults or a `ClassVar` setting.
- How do you see where data lives?: `vars(a)` shows instance attributes, `vars(Agent)` shows class attributes.

**Mistakes to avoid:**
- Saying `b.tools = [...]` changes the class list; assignment creates an instance attribute.
- Fixing only one of the two bugs.

### Q. Write an LRUCache class that supports cache[key], cache[key] = value, len() and in.
**Short answer (45 seconds):** Wrap an `OrderedDict`, which remembers insertion order and can move a key to the end in O(1). `__getitem__` moves the key to the end on every read, `__setitem__` inserts or updates and evicts from the front when over capacity, and `__len__` and `__contains__` delegate. Every operation is O(1).

**Deeper explanation:**

```python
from collections import OrderedDict
from collections.abc import Hashable
from typing import Any

class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._data: OrderedDict[Hashable, Any] = OrderedDict()

    def __getitem__(self, key: Hashable) -> Any:
        value = self._data[key]            # KeyError if missing, like a dict
        self._data.move_to_end(key)        # now most recently used
        return value

    def __setitem__(self, key: Hashable, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False) # evict the least recently used

    def __contains__(self, key: object) -> bool:
        return key in self._data           # does not count as a use

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"LRUCache(capacity={self.capacity}, keys={list(self._data)})"

cache = LRUCache(2)
cache["a"] = 1
cache["b"] = 2
cache["a"]                 # touch "a"
cache["c"] = 3             # evicts "b"
print(cache, "b" in cache) # LRUCache(capacity=2, keys=['a', 'c']) False
```

Implementing dunders instead of `get()` and `put()` methods makes the cache feel like a dict, so callers use normal syntax. `__getitem__` raises `KeyError` for a missing key, matching dict behavior; add a `get(key, default=None)` method for the forgiving version. `__contains__` deliberately does not refresh recency, so checking membership never changes eviction order. Under the hood `OrderedDict` is a hash table plus a doubly linked list, the same structure you would build by hand in a whiteboard interview.

**Follow-ups they will ask:**
- Why not `functools.lru_cache`?: it caches function results by arguments; this class is a general key-value store you control.
- Is it thread-safe?: no; guard mutations with a `threading.Lock`, or use an async lock in async code.
- Across Uvicorn workers?: each process has its own cache; use Redis for a shared one.

**Mistakes to avoid:**
- Evicting with `popitem()`, which removes the newest item because `last=True` is the default.
- Forgetting to refresh recency on update in `__setitem__`.

### Q. Rewrite this TypeScript RateLimiter class in idiomatic Python.
**Short answer (45 seconds):** Constants become class attributes marked `ClassVar`, the static factory becomes a `@classmethod`, the getter becomes a `@property`, and `#hits` plus the private method become `_hits` and `_prune`. Use `time.monotonic()` instead of wall-clock time and a `deque` so old timestamps leave from the left in O(1). Names change to snake_case.

**Deeper explanation:** The TypeScript:

```ts
class RateLimiter {
  static readonly DEFAULT_LIMIT = 60;
  #hits: number[] = [];

  constructor(private readonly limit: number = RateLimiter.DEFAULT_LIMIT) {}

  static fromEnv(): RateLimiter {
    return new RateLimiter(Number(process.env.RATE_LIMIT ?? RateLimiter.DEFAULT_LIMIT));
  }

  get remaining(): number {
    this.prune();
    return this.limit - this.#hits.length;
  }

  tryAcquire(): boolean {
    this.prune();
    if (this.#hits.length >= this.limit) return false;
    this.#hits.push(Date.now());
    return true;
  }

  private prune(): void {
    const cutoff = Date.now() - 60_000;
    this.#hits = this.#hits.filter((t) => t > cutoff);
  }
}
```

The Python:

```python
import os
import time
from collections import deque
from typing import ClassVar

class RateLimiter:
    DEFAULT_LIMIT: ClassVar[int] = 60
    WINDOW_SECONDS: ClassVar[float] = 60.0

    def __init__(self, limit: int = DEFAULT_LIMIT) -> None:
        self._limit = limit
        self._hits: deque[float] = deque()

    @classmethod
    def from_env(cls) -> "RateLimiter":
        return cls(int(os.getenv("RATE_LIMIT", str(cls.DEFAULT_LIMIT))))

    @property
    def remaining(self) -> int:
        self._prune()
        return self._limit - len(self._hits)

    def try_acquire(self) -> bool:
        self._prune()
        if len(self._hits) >= self._limit:
            return False
        self._hits.append(time.monotonic())
        return True

    def _prune(self) -> None:
        cutoff = time.monotonic() - self.WINDOW_SECONDS
        while self._hits and self._hits[0] <= cutoff:
            self._hits.popleft()
```

TypeScript parameter properties (`private readonly limit` in the constructor) have no Python equivalent, so the assignment is written out. `cls(...)` in `from_env` means a subclass gets a subclass instance. `time.monotonic()` never jumps when the system clock is corrected, unlike `Date.now()`. Timestamps are appended in order, so pruning from the left is O(expired), not a full rebuild like `filter`.

**Follow-ups they will ask:**
- How do you test it without waiting 60 seconds?: inject a clock, for example `clock: Callable[[], float] = time.monotonic` in `__init__`, and pass a fake in tests.
- Several Uvicorn workers?: each process has its own limiter; use Redis (a sorted set or `INCR` with `EXPIRE`) for a global limit.

**Mistakes to avoid:**
- Using `__hits` to imitate `#hits`; mangling is for subclass clashes, `_hits` is the idiom.
- Keeping camelCase method names.

### Q. Design a swappable LLM provider layer with an abstract base class for a FastAPI app, and show how a test injects a fake.
**Short answer (45 seconds):** Define `LLMProvider(ABC)` with one abstract async method, `complete(prompt)`. Write one adapter per vendor that wraps its SDK client and returns a plain string. A `get_provider` dependency picks the adapter from settings, routes depend on the abstraction, and tests replace it through `app.dependency_overrides`.

**Deeper explanation:**

```python
from abc import ABC, abstractmethod
from functools import lru_cache

from anthropic import AsyncAnthropic
from fastapi import Depends, FastAPI
from openai import AsyncOpenAI

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str: ...

class OpenAIProvider(LLMProvider):
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client, self.model = client, model

    async def complete(self, prompt: str) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content or ""

class AnthropicProvider(LLMProvider):
    def __init__(self, client: AsyncAnthropic, model: str) -> None:
        self.client, self.model = client, model

    async def complete(self, prompt: str) -> str:
        resp = await self.client.messages.create(
            model=self.model, max_tokens=1024, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text

@lru_cache
def get_provider() -> LLMProvider:
    s = get_settings()
    if s.llm_vendor == "anthropic":
        return AnthropicProvider(AsyncAnthropic(), s.llm_model)
    return OpenAIProvider(AsyncOpenAI(), s.llm_model)

app = FastAPI()

@app.post("/summarize")
async def summarize(text: str, llm: LLMProvider = Depends(get_provider)) -> dict:
    return {"summary": await llm.complete(f"Summarize in 3 bullets:\n{text}")}
```

The test:

```python
class FakeProvider(LLMProvider):
    async def complete(self, prompt: str) -> str:
        return "fake summary"

def test_summarize() -> None:
    app.dependency_overrides[get_provider] = FakeProvider
    resp = TestClient(app).post("/summarize", params={"text": "hi"})
    assert resp.json() == {"summary": "fake summary"}
    app.dependency_overrides.clear()
```

Adapters take the SDK client in `__init__` (composition), so a test can also pass a stub client. Vendor response shapes stay inside the adapter. The ABC makes a half-written adapter fail at construction, not at the first request. `lru_cache` keeps one provider, and one HTTP connection pool, per process.

**Follow-ups they will ask:**
- ABC or Protocol?: an ABC when you own the adapters and want shared helpers; a Protocol when third-party classes should fit without inheriting.
- Streaming?: add an abstract `stream(prompt)` that returns an `AsyncIterator[str]`.

**Mistakes to avoid:**
- Leaking vendor response objects past the adapter.
- Creating a new SDK client on every request.

### Q. Adding a cache mixin made the audit log stop writing. Find and fix the bug.
**Short answer (45 seconds):** `CacheMixin.save` calls `Repository.save(self, row)` directly instead of `super().save(row)`. In `UserRepository`'s MRO the next class after `CacheMixin` is `AuditMixin`, so hard-coding the parent skips it. Switch every mixin to `super()` so the call travels the whole chain.

**Deeper explanation:** The code:

```python
class Repository:
    def __init__(self, table: str) -> None:
        self.table = table
        self.events: list[str] = []

    def save(self, row: dict) -> None:
        self.events.append(f"insert {self.table}")

class AuditMixin:
    def save(self, row: dict) -> None:
        self.events.append("audit")
        super().save(row)

class CacheMixin:
    def save(self, row: dict) -> None:
        self.events.append("invalidate cache")
        Repository.save(self, row)          # BUG: hard-coded parent

class UserRepository(CacheMixin, AuditMixin, Repository):
    pass

repo = UserRepository("users")
repo.save({"id": 1})
print(repo.events)      # ['invalidate cache', 'insert users']: no audit
```

`UserRepository.__mro__` is `UserRepository, CacheMixin, AuditMixin, Repository, object`. `super()` inside `CacheMixin` would mean "next after CacheMixin in this object's MRO", which is `AuditMixin`. `Repository.save(self, row)` jumps straight to the end and skips it. Before the cache mixin was added, `AuditMixin` sat directly before `Repository`, so the bug was invisible.

The fix is one line:

```python
class CacheMixin:
    def save(self, row: dict) -> None:
        self.events.append("invalidate cache")
        super().save(row)
```

Now `repo.events` is `['invalidate cache', 'audit', 'insert users']`. Note that `AuditMixin` does not inherit from `Repository`, yet its `super().save` reaches `Repository.save`: `super()` uses the instance's MRO, not the class's own bases. List mixins before the concrete base so they wrap it.

**Follow-ups they will ask:**
- The mixin needs its own constructor argument?: cooperative init, `def __init__(self, *, ttl: int = 60, **kwargs): super().__init__(**kwargs)`, with keyword arguments everywhere.
- Would you design it with mixins at all?: often composition is clearer, for example a `CachedRepository` wrapper that holds the inner repository.

**Mistakes to avoid:**
- Calling `Parent.method(self, ...)` in classes meant to be combined.
- Mixing positional constructor arguments with cooperative `super().__init__` chains.

### Q. Refactor this subclass chain of LLM clients into composition.
**Short answer (45 seconds):** Every new feature multiplied the subclasses: retry, cache and vendor combinations grow as vendors times features. Make each feature a wrapper that implements the same `LLMProvider` interface and holds an inner provider, then stack them at startup. N vendors plus M features means N + M classes, each testable alone.

**Deeper explanation:** The code:

```python
class OpenAIClient:
    async def complete(self, prompt: str) -> str: ...

class RetryingOpenAIClient(OpenAIClient):
    async def complete(self, prompt: str) -> str: ...   # retry loop around super()

class CachedRetryingOpenAIClient(RetryingOpenAIClient):
    async def complete(self, prompt: str) -> str: ...   # cache check, then super()

# next sprint: Anthropic with retry, Anthropic with cache, cache without retry...
```

The refactor, using the `LLMProvider` ABC from the walkthrough:

```python
import asyncio

class RetryingProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, attempts: int = 3) -> None:
        self.inner, self.attempts = inner, attempts

    async def complete(self, prompt: str) -> str:
        for attempt in range(1, self.attempts + 1):
            try:
                return await self.inner.complete(prompt)
            except TimeoutError:
                if attempt == self.attempts:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise AssertionError("unreachable")

class CachedProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, cache: dict[str, str] | None = None) -> None:
        self.inner = inner
        self.cache = {} if cache is None else cache

    async def complete(self, prompt: str) -> str:
        if prompt not in self.cache:
            self.cache[prompt] = await self.inner.complete(prompt)
        return self.cache[prompt]

provider = CachedProvider(RetryingProvider(AnthropicProvider(client, model)))
```

The wrappers still inherit from the ABC, but only to share the interface; behavior comes from holding another provider (the decorator pattern). Order is a design choice made in one line: cache outside retry means a cache hit never touches the network. Each wrapper is tested with a fake inner provider, for example one that raises `TimeoutError` twice and then answers. `cache` is injectable, so production can pass a Redis-backed mapping and tests a dict.

**Follow-ups they will ask:**
- Concurrent requests for the same uncached prompt?: both miss and call the model; keep a dict of in-flight `asyncio.Task` objects so later callers await the first.
- How is this wired in FastAPI?: build the stack once in a `get_provider` dependency and inject it.

**Mistakes to avoid:**
- Caching non-deterministic or user-specific prompts without a key that includes model, temperature and user.
- Unbounded caches in a long-running process.

### Practice
- Practice kit: open `python-practice/exercises/p12_oop.py`, implement each function, then run `uv run --with pytest pytest tests/test_p12_oop.py` from the `python-practice` folder.
- In the REPL, define a class with a list class attribute, create two instances, append through one, and inspect `vars(obj)` and `vars(TheClass)` to see where the data lives.
- Build two mixins and a base class like the MRO walkthrough, write down the order you expect `super()` to follow, then check it with `print(YourClass.__mro__)`.
- Put `@dataclass(frozen=True)` on a class, try to assign a field, read the `FrozenInstanceError`, then put two equal instances in a set.
