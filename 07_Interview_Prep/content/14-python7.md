## Testing Python with pytest [Core]

> This lesson covers how Python projects are tested with pytest: test discovery, plain `assert`, `pytest.raises`, fixtures with scopes and teardown, `tmp_path` and `monkeypatch`, parametrize, `unittest.mock`, async tests and coverage. In FastAPI and AI backend code it shows up as a `tests/` folder whose `conftest.py` hands every test a TestClient or a clean database, mocks that stand in for the LLM provider so the suite never spends tokens, and a CI step running `pytest --cov` with a coverage floor. Coming from Jest, most ideas map one to one; the two real differences are that fixtures are injected by parameter name and that patching finds its target by import path.

### Why it exists
Python ships `unittest`, a port of Java's JUnit: tests live in classes, setup goes in `setUp` methods, and you check results with `self.assertEqual` and dozens of other assert methods. pytest removed that ceremony: a test is a plain function, a check is a plain `assert`, and setup is a fixture function the test asks for by name. Python has no compiler checking types before the code runs, so the test suite is the main safety net, which makes cheap-to-write tests matter even more than in TypeScript. The cost is some implicit behavior: fixtures arrive by parameter name from `conftest.py` files you may not have open, and pytest rewrites your `assert` statements when it imports the test file.

### In plain words
pytest is a lab assistant. You write each experiment as a short function that ends with "this should be true". The assistant walks the building and finds every experiment by itself, prepares the bench each one asks for (a temp folder, a fake API client, an empty database), runs it, and cleans the bench afterwards even if the experiment blew up. When a check fails, it shows you the actual values on both sides instead of a bare "false". Mocks are stand-in actors: they play the LLM provider or the payment API and write down every line they were asked to say.

### Walkthrough: from the first test to fixtures
1. **Discovery.** pytest collects files named `test_*.py` or `*_test.py`, and inside them functions named `test_*` and methods of classes named `Test*` (classes without an `__init__`). No imports of pytest are needed for a basic test.

   ```python
   # tests/test_prices.py
   from app.prices import add_tax

   def test_add_tax():
       assert add_tax(100) == 118
   ```

   Run `pytest` for everything, `pytest tests/test_prices.py::test_add_tax` for one test, `-k "tax and not slow"` to filter by name, `-x` to stop at the first failure. Jest finds `*.test.js` files and `it` blocks; `jest -t tax` is the `-k` equivalent.

2. **Plain assert, rewritten.** When pytest imports a test module or a `conftest.py`, it rewrites each `assert` so a failure prints the values that produced it.

   ```text
   >       assert total(items) == 30
   E       AssertionError: assert 25 == 30
   E        +  where 25 = <function total at 0x10b01e0c0>([{'price': 10, 'qty': 2}, {'price': 5, 'qty': 1}])
   ```

   Traps: `assert (x == 1, "msg")` asserts a non-empty tuple, which is always true (pytest warns "assertion is always true, perhaps remove parentheses?"); write `assert x == 1, "msg"`. Compare floats with `assert 0.1 + 0.2 == pytest.approx(0.3)`. And never use `assert` for validation in application code: `python -O` strips assert statements. Jest's `expect(a).toEqual(b)` becomes `assert a == b`, because `==` already compares lists and dicts deeply.

3. **Expected exceptions.** `pytest.raises` is a context manager: the block must raise that type, or the test fails with "DID NOT RAISE".

   ```python
   import pytest

   def test_rejects_negative():
       with pytest.raises(ValueError, match="must not be negative") as exc_info:
           add_tax(-1)
       assert exc_info.value.args[0].startswith("amount")
   ```

   `match` is a regular expression searched in `str(exception)`, so wrap literal text containing `.`, `(` or `[` in `re.escape`. Jest: `expect(() => addTax(-1)).toThrow(/must not be negative/)`.

4. **Fixtures: setup the test asks for by name.** A fixture is a function decorated with `@pytest.fixture`; a test that has a parameter with the same name receives its return value.

   ```python
   @pytest.fixture
   def cart() -> list[dict]:
       return [{"price": 10, "qty": 2}]

   def test_total(cart):              # pytest matches the name and calls cart()
       assert total(cart) == 20
   ```

   Each test gets a fresh value, and fixtures can request other fixtures, which builds a small dependency graph (the same idea as FastAPI's `Depends`). Fixtures placed in `tests/conftest.py` are available to every test below that folder without an import. Jest's closest tool is a `let` assigned in `beforeEach`, which does not compose.

5. **yield fixtures and scope.** Code before `yield` is setup, the yielded value goes to the test, and code after `yield` is teardown, which runs even when the test fails.

   ```python
   import sqlite3

   @pytest.fixture(scope="module")
   def conn():
       conn = sqlite3.connect(":memory:")
       conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
       yield conn                 # every test in this module runs here
       conn.close()               # teardown: once, after the module's last test
   ```

   Scopes are `function` (default), `class`, `module`, `package` and `session`. A wider scope is faster but shares state between tests, and a fixture may only request fixtures of the same or a wider scope: a session fixture asking for `tmp_path` fails with `ScopeMismatch`, so it uses `tmp_path_factory` instead. Jest: `beforeAll`/`afterAll` is roughly module scope, `beforeEach`/`afterEach` is function scope.

6. **Built-in fixtures: tmp_path and monkeypatch.**

   ```python
   def test_reads_config(tmp_path, monkeypatch):
       cfg = tmp_path / "settings.env"          # a pathlib.Path, unique per test
       cfg.write_text("MODEL=small\n")
       monkeypatch.setenv("CONFIG_PATH", str(cfg))
       monkeypatch.setattr("app.config.TIMEOUT_SECONDS", 1)
       assert load_config()["MODEL"] == "small"
   ```

   `monkeypatch` records every change (`setenv`, `delenv`, `setattr`, `setitem`) and undoes it when the test ends, so nothing leaks into the next test. Other useful built-ins: `capsys` captures printed output, `caplog` captures log records. In Jest you assign `process.env.X` and must restore it yourself.

### Walkthrough: parametrize, Mock and patch
1. **parametrize: one test body, many cases.**

   ```python
   @pytest.mark.parametrize(
       ("raw", "expected"),
       [("45s", 45), ("1h30m", 5400), ("2h5s", 7205)],
   )
   def test_parse_duration(raw, expected):
       assert parse_duration(raw) == expected
   ```

   Each tuple becomes its own test with its own result line, named like `test_parse_duration[1h30m-5400]`; pass `ids=[...]` or wrap cases in `pytest.param(..., id="...")` for readable names, and stack two decorators to get every combination. Jest: `test.each([...])("parses %s", ...)`.

2. **Mock: a stand-in that records calls.**

   ```python
   from unittest.mock import Mock

   client = Mock()
   client.complete.return_value = "short"
   assert summarize("long text", client) == "short"
   client.complete.assert_called_once_with("Summarize: long text")
   print(client.complete.call_args)          # call('Summarize: long text')
   ```

   Any attribute you touch on a Mock is created on the fly, so a typo such as `client.complet(...)` silently works. `Mock(spec=RealClient)` or `create_autospec(RealClient)` makes unknown attributes and wrong call signatures fail like the real object would. Jest: `jest.fn()`, `mockReturnValue`, `toHaveBeenCalledWith`.

3. **MagicMock and AsyncMock.**

   ```python
   import asyncio
   from unittest.mock import AsyncMock, MagicMock

   files = MagicMock()
   files.__len__.return_value = 3            # dunder methods are configurable
   assert len(files) == 3

   llm = AsyncMock(return_value="hi")         # calling it returns an awaitable
   assert asyncio.run(llm("prompt")) == "hi"
   llm.assert_awaited_once_with("prompt")
   ```

   A plain Mock does not support `len()`, `with` or iteration; MagicMock preconfigures those dunder methods. AsyncMock is for `async def` functions and tracks awaits (`await_count`, `assert_awaited_once`). Jest needs no special type because an async function is just a function returning a Promise (`mockResolvedValue`).

4. **side_effect: errors, sequences, functions.**

   ```python
   flaky = AsyncMock(side_effect=[TimeoutError(), TimeoutError(), "ok"])
   assert asyncio.run(call_with_retry(flaky)) == "ok"
   assert flaky.await_count == 3
   ```

   Set `side_effect` to an exception and every call raises it; to an iterable and each call returns (or raises, for exception instances) the next item; to a function and the mock calls it with the same arguments. When an iterable runs out, the next call raises `StopIteration` (`StopAsyncIteration` for AsyncMock). Jest: `mockRejectedValueOnce(err).mockResolvedValueOnce("ok")`.

5. **patch: replace a name where it is looked up.**

   ```python
   # app/services/summary.py
   from app.llm import complete               # copies the name into this module

   def summarize(text: str) -> str:
       return complete(f"Summarize: {text}")

   # tests/test_summary.py
   from unittest.mock import patch

   def test_summarize():
       with patch("app.services.summary.complete", return_value="short") as fake:
           assert summarize("long") == "short"
       fake.assert_called_once()
   ```

   Patching `app.llm.complete` here changes nothing, because `summary.py` already holds its own reference. Rule: patch the module that uses the name. `patch` also works as a decorator (`@patch("app.services.summary.complete")` passes the mock as an extra argument), and when the target is an `async def` it creates an AsyncMock for you. Jest's `jest.mock("./llm")` swaps the module in the registry for every importer, which is why this trap does not exist there.

6. **monkeypatch or patch?**

   ```python
   def test_with_monkeypatch(monkeypatch):
       prompts = []
       monkeypatch.setattr("app.services.summary.complete",
                           lambda prompt: prompts.append(prompt) or "short")
       assert summarize("long") == "short"
       assert prompts == ["Summarize: long"]
   ```

   Both undo themselves. `monkeypatch` is a pytest fixture that also handles environment variables and dict items; `patch` is standard library and gives you a Mock with call records and assert helpers. For FastAPI dependencies, prefer `app.dependency_overrides` to either, since it needs no import path at all.

### Walkthrough: async tests, coverage and configuration
1. **Async code without a plugin.** Drive the coroutine with `asyncio.run` inside a normal test.

   ```python
   import asyncio
   from unittest.mock import AsyncMock

   async def fetch_title(http, url: str) -> str:
       data = await http.get_json(url)
       return data["title"]

   def test_fetch_title():
       http = AsyncMock()                     # its attributes are AsyncMocks too
       http.get_json.return_value = {"title": "Hi"}
       assert asyncio.run(fetch_title(http, "https://x.io")) == "Hi"
   ```

   `asyncio.run` creates an event loop, runs the coroutine to completion and closes the loop: no dependency, but each call is a separate loop, so you cannot share an async resource such as a connection pool between tests. A bare `async def test_...` without a plugin never runs its body: current pytest fails it with "async def functions are not natively supported", and older versions skipped it with only a warning, which looked green.

2. **pytest-asyncio or AnyIO.**

   ```python
   import pytest

   @pytest.mark.asyncio
   async def test_fetch_title(fake_http):
       assert await fetch_title(fake_http, "https://x.io") == "Hi"
   ```

   pytest-asyncio's default strict mode needs the marker on each test and `@pytest_asyncio.fixture` on async fixtures; `asyncio_mode = "auto"` in the config marks them all. FastAPI's own docs use the AnyIO plugin instead (`@pytest.mark.anyio`), which ships with AnyIO, already installed with FastAPI. Jest supports `async` tests natively.

3. **Coverage with pytest-cov.**

   ```bash
   uv add --dev pytest-cov
   pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=85
   ```

   `term-missing` lists the uncovered line numbers per file, `--cov-branch` also counts `if` branches that never went one way, and `--cov-fail-under` fails CI below the floor. Coverage proves a line ran, not that any test checked its result. Jest: `jest --coverage` with `coverageThreshold`.

4. **Configuration and markers.**

   ```toml
   # pyproject.toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   pythonpath = ["."]                 # lets tests import the app package
   addopts = "-q --strict-markers"
   markers = ["slow: calls a real model or network"]
   ```

   ```python
   @pytest.mark.slow
   def test_real_embeddings(): ...
   ```

   `pytest -m "not slow"` runs the fast set on every push and the slow set nightly. `--strict-markers` turns a misspelled marker into an error instead of a silently ignored label. `pythonpath = ["."]` fixes the classic "ModuleNotFoundError: No module named 'app'" when tests live outside the package. Jest's equivalent is `jest.config.js` with `testMatch` and `moduleDirectories`.

### Concepts you must understand
- pytest collects `test_*.py` files and `test_*` functions; `conftest.py` files hold shared fixtures and are loaded automatically for their folder and everything below it.
- A plain `assert` is enough because pytest rewrites it to show both sides; use `pytest.approx` for floats and never wrap an assert in parentheses with a message.
- `pytest.raises(Error, match=regex)` checks type and message; `match` is a regex search, not an equality check.
- Fixtures are dependency injection by parameter name; `yield` splits setup from teardown, and teardown runs even when the test fails.
- Scope trades isolation for speed, and a fixture may only use fixtures of the same or a wider scope (`tmp_path_factory` for wide scopes).
- `monkeypatch` and `patch` undo their changes; patch the name where the code under test looks it up, not where it is defined.
- `Mock` accepts any attribute, so add `spec` or `autospec`; `MagicMock` adds dunder methods; `AsyncMock` returns awaitables and records awaits.
- `side_effect` raises an exception, yields successive results from an iterable, or delegates to a function.
- Async tests need `asyncio.run` inside a sync test or a plugin (pytest-asyncio, AnyIO); a plugin-less `async def test_` never runs its body.
- Coverage measures executed lines and branches, not correctness; use it as a floor that exposes untested code.

| JavaScript | Python | Note |
|---|---|---|
| `*.test.js` with `describe` and `it` | `test_*.py` with `def test_*` | classes (`class TestCart`) are optional grouping |
| `expect(a).toEqual(b)` | `assert a == b` | `==` is deep for lists and dicts; `is` checks identity |
| `toBeCloseTo` | `pytest.approx` | works on numbers, lists and dicts of numbers |
| `expect(fn).toThrow(/msg/)` | `with pytest.raises(E, match="msg"):` | the block must raise |
| `beforeEach` / `afterEach` | function-scoped yield fixture | requested by parameter name |
| `beforeAll` / `afterAll` | `@pytest.fixture(scope="module")` | or `"session"` for the whole run |
| `test.each` | `@pytest.mark.parametrize` | one result line per case |
| `jest.fn()` | `Mock()`, `MagicMock()`, `AsyncMock()` | add `spec` to catch typos |
| `mockReturnValueOnce` chain | `side_effect=[...]` | exception instances in the list are raised |
| `jest.mock("./llm")` | `patch("app.services.summary.complete")` | patch where the name is used |
| setting `process.env.X` by hand | `monkeypatch.setenv("X", "1")` | undone automatically |
| `jest --coverage` | `pytest --cov=app` | needs the pytest-cov plugin |

### Q. Write parametrized tests for a `slugify` function, with readable test ids, including the inputs that must raise.
**Short answer (45 seconds):** One `@pytest.mark.parametrize` test for the happy cases, each wrapped in `pytest.param(..., id="...")` so a failure names its case, and a second parametrized test using `pytest.raises(ValueError, match=...)` for inputs that leave nothing to slug. Every case becomes its own pass or fail line, so one bad case never hides the others.

**Deeper explanation:** The function under test and its tests:

```python
import re
import pytest

def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        raise ValueError(f"cannot slugify {title!r}")
    return slug

@pytest.mark.parametrize(
    ("title", "expected"),
    [
        pytest.param("Hello World", "hello-world", id="spaces"),
        pytest.param("  FastAPI & Pydantic!  ", "fastapi-pydantic", id="symbols"),
        pytest.param("Python 3.12", "python-3-12", id="digits"),
        pytest.param("already-a-slug", "already-a-slug", id="idempotent"),
        pytest.param("Café", "caf", id="non-ascii-dropped"),
    ],
)
def test_slugify(title, expected):
    assert slugify(title) == expected

@pytest.mark.parametrize("title", ["", "   ", "!!!"])
def test_slugify_rejects_empty_result(title):
    with pytest.raises(ValueError, match="cannot slugify"):
        slugify(title)
```

`pytest -v` prints lines like `test_slugify[symbols] PASSED`, so a red line tells you which input broke before you read the diff. The first argument names the parameters (a tuple, or a comma-separated string), the second is a list with one entry per case. The `non-ascii-dropped` row pins current behavior: "Café" losing its accent is a product decision, and the test makes changing it deliberate. `match` searches a regular expression in the exception message, so it stays robust to the input being echoed back in the message.

**Follow-ups they will ask:**
- How do you test every combination of two inputs? : stack two `parametrize` decorators; pytest runs the cross product.
- How do you mark one case as a known bug? : `pytest.param("Ünïcode", "unicode", marks=pytest.mark.xfail(reason="no transliteration yet"))`.
- Where do cases live when several test files share them? : a module-level list, or a fixture with `params=[...]` when each case needs setup.

**Mistakes to avoid:**
- A `for` loop over cases inside one test: the first failing case stops the loop and hides the rest.
- Asserting the full exception message, which breaks on harmless wording changes; match a stable fragment.

### Q. This test passes when run alone but fails in the full suite. Find the leak and fix it.
**Short answer (45 seconds):** A test that passes alone and fails in a suite means shared state leaks between tests. Here there are two leaks: `os.environ` is changed directly and never restored, and `lru_cache` keeps the first settings object it built. I fix both: `monkeypatch.setenv` for the environment, and an autouse fixture that clears the cache before and after every test.

**Deeper explanation:** The code:

```python
# app/config.py
import os
from functools import lru_cache

@lru_cache
def get_settings() -> dict[str, str]:
    return {"model": os.environ.get("MODEL", "small")}

# tests/test_a.py
def test_uses_big_model():
    os.environ["MODEL"] = "big"
    assert get_settings()["model"] == "big"

# tests/test_b.py
def test_default_model():
    assert get_settings()["model"] == "small"   # suite: AssertionError: assert 'big' == 'small'
```

pytest runs `test_a.py` first, which sets `MODEL=big` for the rest of the process and caches `{"model": "big"}`; `test_b` then reads the cache. The fix:

```python
# tests/conftest.py
import pytest
from app.config import get_settings

@pytest.fixture(autouse=True)          # wraps every test without being requested
def fresh_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

# tests/test_a.py
def test_uses_big_model(monkeypatch):
    monkeypatch.setenv("MODEL", "big")  # undone when the test ends, pass or fail
    assert get_settings()["model"] == "big"
```

To find the culprit in a large suite, run the failing test after each half of the other files until one half reproduces it, or add pytest-randomly so order dependence shows up on day one instead of after a file rename. The usual suspects: module-level dicts used as in-memory stores, class attributes, `app.dependency_overrides` never cleared, and `patch(...).start()` without `stop()`.

**Follow-ups they will ask:**
- How does FastAPI avoid this? : inject settings with `Depends(get_settings)` and replace them through `app.dependency_overrides[get_settings]` in a fixture that clears overrides on teardown.
- Why not `importlib.reload(config)`? : other modules keep references to the old objects, so you end up with two versions of everything.

**Mistakes to avoid:**
- "Fixing" it by renaming files so they run in a different order.
- Restoring the variable with `del os.environ["MODEL"]` at the end of the test: that line never runs when the assert fails, so the leak returns exactly while you are debugging.

### Q. This test should stub the LLM call, but CI logs show real requests reaching the provider. Find the bug and fix it.
**Short answer (45 seconds):** The patch targets the module where `complete` is defined, but the code under test imported the name into its own module, so it still holds the real function. I patch where the name is looked up, `app.services.summary.complete`, assert the mock was awaited, and add a guard so any real network call from tests fails loudly.

**Deeper explanation:** The code:

```python
# app/llm.py
async def complete(prompt: str) -> str: ...            # real HTTP call to the provider

# app/services/summary.py
from app.llm import complete                            # binds a second name to the function

async def summarize(text: str) -> str:
    return (await complete(f"Summarize: {text}")).strip()

# tests/test_summary.py (buggy)
def test_summarize():
    with patch("app.llm.complete", return_value="short"):
        assert asyncio.run(summarize("long")) == "short"   # real call happens
```

`patch("app.llm.complete")` replaces the attribute on the `app.llm` module object. But `from app.llm import complete` ran when `summary.py` was imported and copied a reference into `summary`'s globals; `summarize` reads that copy. The fix:

```python
def test_summarize():
    with patch("app.services.summary.complete", return_value="short") as fake:
        assert asyncio.run(summarize("long")) == "short"
    fake.assert_awaited_once_with("Summarize: long")
```

Because `complete` is `async def`, `patch` builds an AsyncMock, so awaiting it works and `assert_awaited_once_with` exists. Had `summary.py` used `import app.llm as llm` and called `llm.complete(...)`, the original patch would have worked, because the lookup then happens through the module at call time. In a FastAPI service the cleaner design is to inject the LLM client as a dependency and override it, which needs no import path at all. As a guard, set a fake API key in the test environment so a stray real call fails with 401, or block sockets with the pytest-socket plugin.

**Follow-ups they will ask:**
- Why does Jest not have this problem? : `jest.mock("./llm")` replaces the module in the registry before anything imports it, so every importer receives the mock.
- What does `autospec=True` add? : the mock copies the real signature, so a call with wrong arguments fails the same way the real function would.

**Mistakes to avoid:**
- Asserting only the return value; a test that never touches the mock can still pass, so also assert it was awaited.
- Patching a client object that was already created at import time and cached in another module.

### Q. Write a test proving that a retry helper retries a timed-out LLM call twice with exponential backoff and then succeeds, without the test actually sleeping.
**Short answer (45 seconds):** Make the LLM call an AsyncMock whose `side_effect` is two `TimeoutError` instances followed by a result, patch the sleep the helper uses with another AsyncMock, run the coroutine with `asyncio.run`, and assert three awaits on the call plus the exact delays passed to sleep. A second test covers giving up after the last attempt.

**Deeper explanation:** The helper:

```python
# app/retry.py
import asyncio

async def with_retry(fn, attempts: int = 3, base_delay: float = 1.0):
    for attempt in range(attempts):
        try:
            return await fn()
        except TimeoutError:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(base_delay * 2**attempt)
```

The tests:

```python
import asyncio
from unittest.mock import AsyncMock, call, patch
import pytest
from app.retry import with_retry

def test_retries_then_succeeds():
    llm = AsyncMock(side_effect=[TimeoutError(), TimeoutError(), "answer"])
    with patch("app.retry.asyncio.sleep", new_callable=AsyncMock) as sleep:
        assert asyncio.run(with_retry(llm)) == "answer"
    assert llm.await_count == 3
    assert sleep.await_args_list == [call(1.0), call(2.0)]

def test_gives_up_after_last_attempt():
    llm = AsyncMock(side_effect=TimeoutError("slow upstream"))
    with patch("app.retry.asyncio.sleep", new_callable=AsyncMock) as sleep:
        with pytest.raises(TimeoutError, match="slow upstream"):
            asyncio.run(with_retry(llm, attempts=2))
    assert sleep.await_count == 1
```

`side_effect` with a list returns or raises one item per call, and `await_args_list` records every delay, so the backoff schedule itself is under test. Note that `app.retry.asyncio` is the shared `asyncio` module, so this patch replaces `asyncio.sleep` for every caller while the `with` block runs; that is fine in a synchronous test, and injecting `sleep` as a parameter (`sleep=asyncio.sleep`) removes the question entirely. Since Python 3.11, `asyncio.TimeoutError` is the built-in `TimeoutError`, but httpx raises `httpx.TimeoutException`, which is not a subclass of it, so check what your client really raises.

**Follow-ups they will ask:**
- How do you test jitter? : inject the random source or patch `random.uniform` with a fixed return value.
- How do you prove non-timeout errors are not retried? : `side_effect=ValueError()` and assert `await_count == 1`.

**Mistakes to avoid:**
- Letting the test really sleep: three seconds per test turns a 30-second suite into ten minutes.
- Asserting only the final result, which passes even if the helper never retried.

### Q. Write a fixture that gives each test a clean SQLite database, then make the suite faster by sharing one database file across the session. What breaks, and how do you keep tests isolated?
**Short answer (45 seconds):** The simple version is a function-scoped fixture that creates a database in `tmp_path` and builds the schema for every test. To go faster I build the schema once in a session fixture, which must use `tmp_path_factory` because `tmp_path` is function scoped, and give each test a connection inside a transaction that is rolled back on teardown, so tests share the schema but never each other's rows.

**Deeper explanation:**

```python
import sqlite3
import pytest

SCHEMA = "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE)"

@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "test.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)               # schema built once per test run
    conn.close()
    return path

@pytest.fixture
def db(db_path):
    conn = sqlite3.connect(db_path, isolation_level=None)  # we control transactions
    conn.execute("BEGIN")
    yield conn
    conn.execute("ROLLBACK")           # undo everything the test wrote
    conn.close()

def test_insert(db):
    db.execute("INSERT INTO users (email) VALUES ('a@x.io')")
    assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1

def test_starts_empty(db):
    assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 0
```

Asking for `tmp_path` in the session fixture raises `ScopeMismatch: You tried to access the function scoped fixture tmp_path with a session scoped request object`. `isolation_level=None` stops the sqlite3 module from opening transactions implicitly, so the explicit `BEGIN` and `ROLLBACK` are the only ones. Inserting the same email in two tests works, because each test's rows vanish on rollback.

What breaks: code under test that calls `commit()` ends the outer transaction, so its rows survive; with SQLAlchemy 2.0, bind the session to the test's connection with `join_transaction_mode="create_savepoint"` so commits become savepoints. With pytest-xdist each worker process runs its own session fixtures, so this SQLite file is already per worker, but a shared Postgres server needs one database per worker, named with the `worker_id` fixture. And any test that only passes after another test created data was already broken.

**Follow-ups they will ask:**
- Postgres instead of SQLite? : run a real Postgres in Docker (testcontainers) for the session, apply migrations once, and keep the per-test rollback.
- How do you hand this session to FastAPI? : override the `get_db` dependency with a function that yields the test's session.

**Mistakes to avoid:**
- Testing against SQLite when production is Postgres and the code uses JSONB, `ON CONFLICT` details or Postgres-only types.
- Deleting rows table by table in teardown, which is slow and misses tables added later.

### Q. Rewrite this Jest test suite in idiomatic pytest.
**Short answer (45 seconds):** `jest.mock` plus `mockResolvedValue` becomes a fixture that patches the module attribute with an AsyncMock through `monkeypatch`; `it.each` becomes `parametrize`; `rejects.toThrow` becomes `pytest.raises` around `asyncio.run`. `resetAllMocks` disappears, because each test gets a fresh mock and `monkeypatch` undoes the patch.

**Deeper explanation:** The Jest version:

```js
const llm = require("./llm");
const { summarize } = require("./summary");
jest.mock("./llm");

describe("summarize", () => {
  beforeEach(() => jest.resetAllMocks());

  it("returns the trimmed summary", async () => {
    llm.complete.mockResolvedValue("  short  ");
    await expect(summarize("long text")).resolves.toBe("short");
    expect(llm.complete).toHaveBeenCalledWith("Summarize: long text");
  });

  it.each(["", "   "])("skips blank input %p", async (text) => {
    await expect(summarize(text)).resolves.toBe("");
    expect(llm.complete).not.toHaveBeenCalled();
  });

  it("propagates provider errors", async () => {
    llm.complete.mockRejectedValue(new Error("rate limited"));
    await expect(summarize("x")).rejects.toThrow(/rate limited/);
  });
});
```

The pytest version, where `app/summary.py` does `from app.llm import complete`:

```python
import asyncio
from unittest.mock import AsyncMock
import pytest
from app import summary

@pytest.fixture
def complete(monkeypatch):
    fake = AsyncMock(return_value="  short  ")
    monkeypatch.setattr(summary, "complete", fake)   # patch where it is used
    return fake

def test_returns_trimmed_summary(complete):
    assert asyncio.run(summary.summarize("long text")) == "short"
    complete.assert_awaited_once_with("Summarize: long text")

@pytest.mark.parametrize("text", ["", "   "])
def test_skips_blank_input(complete, text):
    assert asyncio.run(summary.summarize(text)) == ""
    complete.assert_not_awaited()

def test_propagates_provider_errors(complete):
    complete.side_effect = RuntimeError("rate limited")
    with pytest.raises(RuntimeError, match="rate limited"):
        asyncio.run(summary.summarize("x"))
```

The fixture plays the role of `jest.mock` plus `beforeEach`; asking for `complete` both installs the fake and hands it to the test for assertions. `describe` blocks have no direct equivalent and are rarely missed: the file is the group, and a `class TestSummarize:` works if you want nesting.

**Follow-ups they will ask:**
- With pytest-asyncio installed? : mark the tests `@pytest.mark.asyncio`, make them `async def` and `await summary.summarize(...)` directly.
- How do you share this fixture with other files? : move it to `tests/conftest.py`.

**Mistakes to avoid:**
- Translating `jest.mock("./llm")` to `patch("app.llm.complete")`, which misses the copy `summary` imported.
- Using `Mock` instead of `AsyncMock`: awaiting a plain Mock's return value raises `TypeError`.

### Practice
- Practice kit: open `python-practice/exercises/p20_testing.py`, implement each function, then run `uv run --with pytest pytest tests/test_p20_testing.py` from the `python-practice` folder.
- In the REPL, run `from unittest.mock import Mock; m = Mock(); m.anything.you.like(1); print(m.mock_calls)`, then repeat with `Mock(spec=["complete"])` and read the `AttributeError`.
- Write a test containing `assert (1 == 2, "never fails")`, run it, read the warning pytest prints, and fix the line.
- After the kit passes, run `uv run --with pytest --with pytest-cov pytest --cov=exercises --cov-report=term-missing tests/test_p20_testing.py` and find any line no test executes.

## Python for FastAPI [Core]

> This lesson reads a FastAPI app as a Python program: which language feature does the work behind each decorator, type hint, default value, `Annotated` and `yield`. It shows up in every FastAPI and AI backend you will touch: route modules, request and response models, dependencies for database sessions and auth, settings loaded from the environment, LLM clients created at startup, streamed answers and the test suite. The runtime side (Uvicorn, the event loop, the thread pool, streaming internals) is in the Internal Architecture track, section "FastAPI & Python Async Architecture", and interview questions on Depends and deployment are in the Backend track, section "Python & FastAPI for AI Backends".

### Why it exists
Before FastAPI, a Python API in Flask read `request.json` by hand, validated it with a separate library such as marshmallow, and described itself in a separately maintained OpenAPI file, so the three drifted apart. FastAPI's idea is that Python already has a place to declare what a function needs: its signature with type hints. When a route is registered, FastAPI inspects that signature once and generates parsing, validation (through Pydantic), dependency injection and the OpenAPI schema from it. The cost is that the signature now has behavior: whether a parameter has a default, what its type is, and what sits inside `Annotated` decide where FastAPI looks for the value, so you have to know the rules.

### In plain words
Think of each endpoint function as a paper form with labeled boxes. The decorator pins the form to a door, such as "POST /todos". Each box says what goes in it: a number from the URL, a word from the query string, a whole JSON document, or "a database session, please". FastAPI is the clerk who reads the form, fills every box from the request, and sends the visitor away with a list of mistakes if a box cannot be filled. Your function only runs when the form is complete, and its return type tells the clerk what to hand back.

### Walkthrough: one endpoint, every Python feature it uses
1. **The decorator registers the route.** `app.get(path)` returns a decorator; applying it to your function records the function and its path in the app's router and gives the same function back.

   ```python
   @app.get("/notes/{note_id}")
   def read_note(note_id: int) -> dict:
       return {"id": note_id}

   # what the @ line does, spelled out:
   def read_note(note_id: int) -> dict: ...
   read_note = app.get("/notes/{note_id}")(read_note)   # registers, returns read_note
   ```

   Because the function comes back unchanged, you can still call `read_note(5)` in a unit test or from another handler. Express does the same registration without the `@` syntax, `app.get("/notes/:id", handler)`; NestJS's `@Get(":id")` is a TypeScript decorator that stores metadata the framework reads later.

2. **Type hints declare path and query parameters.**

   ```python
   @app.get("/projects/{project_id}/notes")
   def list_notes(project_id: int, tag: str | None = None, limit: int = 20): ...
   # GET /projects/7/notes?tag=ai&limit=5  ->  project_id=7, tag="ai", limit=5
   ```

   FastAPI inspects the signature when the route is registered. A name that appears in the path template is a path parameter; any other parameter with a simple type (`int`, `str`, `bool`, `float`, an enum, a `Literal`) is a query parameter, required unless it has a default. Values are converted, so `"7"` becomes `7`, and `?limit=abc` is rejected with 422 before your code runs. `bool` accepts `true/false`, `1/0`, `yes/no` and `on/off`. Express gives you strings in `req.params` and `req.query` and leaves the converting and checking to you. (`str | None` needs Python 3.10+.)

3. **A Pydantic model validates the body.**

   ```python
   from pydantic import BaseModel, Field

   class NoteIn(BaseModel):
       text: str = Field(min_length=1, max_length=2000)

   @app.post("/projects/{project_id}/notes")
   def add_note(project_id: int, note: NoteIn): ...
   ```

   A parameter whose type is a `BaseModel` subclass is read from the JSON body. Invalid JSON or a bad field never reaches your function: the client gets 422 with a `detail` list of entries such as `{"loc": ["body", "text"], "msg": "String should have at least 1 character", "type": "string_too_short"}`. Trap: a plain `text: str` parameter on a POST is a query parameter, not a body field. NestJS does this with a DTO class and `ValidationPipe`; in Express you call a Zod `schema.parse(req.body)` yourself.

4. **Annotated attaches FastAPI metadata to a type.**

   ```python
   from typing import Annotated
   from fastapi import Path, Query

   def list_notes(
       project_id: Annotated[int, Path(ge=1)],
       limit: Annotated[int, Query(ge=1, le=100)] = 20,
       q: Annotated[str | None, Query(max_length=50)] = None,
   ): ...
   ```

   `Annotated[T, extra]` (from `typing`) means "type T, plus some data for whoever reads it". Type checkers and your editor see only `int`; FastAPI reads the `Path` and `Query` objects for constraints, aliases and documentation. The default stays a normal Python default, so the function still behaves when called directly. The older style `limit: int = Query(20, le=100)` still works but hides the real default inside a function call. `Depends`, `Header`, `Cookie` and `Body` go in the same slot.

5. **A generator dependency with yield provides the DB session.**

   ```python
   from collections.abc import Iterator
   from fastapi import Depends
   from sqlalchemy.orm import Session

   def get_db() -> Iterator[Session]:
       db = SessionLocal()
       try:
           yield db            # the endpoint runs while this generator is paused here
       finally:
           db.close()          # runs after the request, even if the endpoint raised

   DB = Annotated[Session, Depends(get_db)]    # reusable alias for every endpoint
   ```

   A function containing `yield` is a generator: calling it runs nothing until someone asks for the next value. FastAPI drives it like a context manager: it takes the first yielded value as the argument, and resumes the generator after the request so the `finally` block runs. If the endpoint raises, the exception is thrown into the generator at the `yield`, so an `except` there can roll back, and it must re-raise. In current FastAPI the code after `yield` runs after the response is sent by default (this timing has changed between versions), and recent versions accept `Depends(get_db, scope="function")` to run it before. NestJS: a request-scoped provider; Express: middleware that sets `req.db` and releases it on `res.on("finish")`.

6. **async def or def.**

   ```python
   @app.get("/notes/{note_id}")
   def read_note(note_id: int, db: DB): ...          # sync driver: runs in a worker thread

   @app.get("/weather")                                # Http: an injected httpx.AsyncClient
   async def weather(city: str, http: Http):          # async client: runs on the event loop
       return (await http.get(f"/forecast/{city}")).json()
   ```

   Same decorator, different scheduling: an `async def` handler runs on the event loop and may only `await` non-blocking calls, while a plain `def` handler runs in a thread pool, so blocking libraries are safe there. Choose by the libraries the body calls; the details and failure modes are in the Internal Architecture track. In Node there is no choice to make, because every library is non-blocking.

7. **Raising HTTPException.**

   ```python
   from fastapi import HTTPException

   note = db.get(Note, note_id)
   if note is None:
       raise HTTPException(status_code=404, detail="Note not found")
   ```

   In Python, errors travel as exceptions, so you can stop the request from the handler, from a helper it calls or from a dependency several layers deep. FastAPI catches `HTTPException` and sends `{"detail": "Note not found"}` with status 404; any other uncaught exception becomes a 500. NestJS works the same way (`throw new NotFoundException()`); Express handlers usually `return res.status(404).json(...)` at the point of failure.

8. **response_model filters and documents the output.**

   ```python
   from typing import Any

   class NoteOut(BaseModel):
       id: int
       text: str

   @app.get("/notes/{note_id}", response_model=NoteOut)
   def read_note(note_id: int, db: DB) -> Any:
       return db.get(Note, note_id)           # an ORM row with extra columns
   ```

   FastAPI validates the return value against `NoteOut` and serializes only its fields, so a `password_hash` or `embedding` column cannot leak, and the same model documents the response in `/docs`. A return annotation (`-> NoteOut`) does the same job when you actually return that type; use `response_model=` when the function returns something else, such as an ORM row or a dict. NestJS needs `ClassSerializerInterceptor` and `@Exclude()`; Express code picks fields by hand.

9. **All of it in one endpoint.**

   ```python
   @app.post("/projects/{project_id}/notes", status_code=201, response_model=NoteOut)
   def add_note(
       project_id: Annotated[int, Path(ge=1)],     # path, must be at least 1
       note: NoteIn,                               # JSON body, validated
       db: DB,                                     # generator dependency
       pin: Annotated[bool, Query()] = False,      # ?pin=true
   ) -> Any:
       if db.get(Project, project_id) is None:
           raise HTTPException(status_code=404, detail="Project not found")
       row = Note(project_id=project_id, text=note.text, pinned=pin)
       db.add(row)
       db.commit()
       return row                                  # filtered through NoteOut
   ```

   For `POST /projects/3/notes?pin=true` with body `{"text": "call vendor"}`: FastAPI converts and checks the path, query and body, opens the session through `get_db`, runs the `def` handler in a worker thread, returns 201 with only the `NoteOut` fields (or 404, or 422 listing every bad input), and then closes the session.

### Walkthrough: a CRUD API step by step, next to Express and NestJS
1. **Models and an in-memory store.**

   ```python
   import itertools
   from typing import Annotated
   from fastapi import FastAPI, HTTPException, Query
   from pydantic import BaseModel, Field

   app = FastAPI()

   class TodoIn(BaseModel):
       title: str = Field(min_length=1, max_length=100)
       done: bool = False

   class Todo(TodoIn):                 # inherits title and done, adds id
       id: int

   todos: dict[int, Todo] = {}
   next_id = itertools.count(1)        # next(next_id) -> 1, 2, 3, ...
   ```

   A module-level dict lives in one worker process and disappears on restart, which is fine for learning and is replaced later by a DB session dependency. Express: `const todos = new Map(); let nextId = 1;`. NestJS: a `TodosService` provider holding the Map, plus a `CreateTodoDto` class with class-validator decorators.

2. **POST to create.**

   ```python
   @app.post("/todos", status_code=201)
   def create_todo(body: TodoIn) -> Todo:
       todo = Todo(id=next(next_id), **body.model_dump())
       todos[todo.id] = todo
       return todo
   ```

   `**body.model_dump()` unpacks a dict into keyword arguments, the Python version of `{ id, ...body }`. FastAPI defaults every route to 200, hence `status_code=201`. Express: `app.post("/todos", (req, res) => { const data = TodoIn.parse(req.body); ...; res.status(201).json(todo); })`. NestJS: `@Post() create(@Body() dto: CreateTodoDto)`, where POST already defaults to 201.

3. **GET one, with a 404.**

   ```python
   @app.get("/todos/{todo_id}")
   def get_todo(todo_id: int) -> Todo:
       todo = todos.get(todo_id)        # dict.get returns None instead of raising KeyError
       if todo is None:
           raise HTTPException(status_code=404, detail="Todo not found")
       return todo
   ```

   `GET /todos/abc` never reaches this code: the `int` hint turns it into a 422. Express: `const todo = todos.get(Number(req.params.id)); if (!todo) return res.status(404).json({ detail: "Todo not found" });`. NestJS: `@Get(":id") findOne(@Param("id", ParseIntPipe) id: number)` and `throw new NotFoundException()`.

4. **GET the list, with filters and pagination.**

   ```python
   @app.get("/todos")
   def list_todos(
       done: bool | None = None,
       q: str | None = None,
       limit: Annotated[int, Query(ge=1, le=100)] = 20,
       offset: Annotated[int, Query(ge=0)] = 0,
   ) -> list[Todo]:
       items = list(todos.values())
       if done is not None:
           items = [t for t in items if t.done == done]
       if q:
           items = [t for t in items if q.lower() in t.title.lower()]
       return items[offset : offset + limit]
   ```

   `?limit=500` gets a 422 before your code runs, and slicing past the end of a list returns a shorter list, never an error. Trap: `if done:` instead of `if done is not None:` silently ignores `?done=false`. Express: `req.query.done === "true"` and `Math.min(Number(req.query.limit) || 20, 100)` by hand. NestJS: a query DTO with `@Type(() => Number) @Min(1) @Max(100)` and `ValidationPipe({ transform: true })`.

5. **PATCH for partial updates.**

   ```python
   class TodoPatch(BaseModel):
       title: str | None = Field(default=None, min_length=1, max_length=100)
       done: bool | None = None

   @app.patch("/todos/{todo_id}")
   def update_todo(todo_id: int, body: TodoPatch) -> Todo:
       todo = get_todo(todo_id)          # reuse the handler: raises the 404 for us
       changes = body.model_dump(exclude_unset=True, exclude_none=True)
       todos[todo_id] = todo.model_copy(update=changes)
       return todos[todo_id]
   ```

   `exclude_unset=True` keeps only the keys the client actually sent, so `{"done": true}` cannot overwrite the title with `None`; `exclude_none=True` also drops explicit nulls. `model_copy(update=...)` does not validate, which is safe here only because `TodoPatch` already validated every value. Express: `Object.assign(todo, req.body)`, with no validation at all. NestJS: `class UpdateTodoDto extends PartialType(CreateTodoDto)`.

6. **DELETE with 204.**

   ```python
   @app.delete("/todos/{todo_id}", status_code=204)
   def delete_todo(todo_id: int) -> None:
       get_todo(todo_id)
       del todos[todo_id]
   ```

   Returning `None` with `status_code=204` sends an empty body. Express: `todos.delete(id); res.status(204).end();`. NestJS: `@Delete(":id") @HttpCode(204)`.

7. **Run it and read the generated docs.**

   ```bash
   uv add "fastapi[standard]"        # FastAPI plus Uvicorn, the fastapi CLI and httpx
   uv run fastapi dev main.py        # auto reload on save, like nodemon
   # open http://127.0.0.1:8000/docs : Swagger UI built from the signatures
   ```

   Every constraint you wrote (`ge=1`, `max_length=100`, the 201 and 204 codes, the 422 error shape) appears in `/docs` with no extra work. Express needs swagger-jsdoc comments kept in sync by hand; NestJS needs `@nestjs/swagger` decorators on DTO properties.

### Walkthrough: from one file to a real service
1. **Settings with pydantic-settings.**

   ```python
   # app/config.py
   from functools import lru_cache
   from pydantic import SecretStr
   from pydantic_settings import BaseSettings, SettingsConfigDict

   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")
       openai_api_key: SecretStr                  # required: startup fails without it
       database_url: str = "sqlite:///./dev.db"
       debug: bool = False                        # APP_DEBUG=true -> True

   @lru_cache
   def get_settings() -> Settings:
       return Settings()
   ```

   pydantic-settings is a separate package (`uv add pydantic-settings`). Each field is read from the environment (case-insensitive, with the prefix) or the `.env` file and validated like any model, so a missing key fails at startup with "Field required" instead of becoming `None` deep inside a request. `SecretStr` prints as `**********` in logs and reprs; call `.get_secret_value()` where you need the real value. `lru_cache` turns the function into a lazy singleton, and using it through `Depends(get_settings)` lets tests override it. Express: `dotenv` plus a Zod schema over `process.env`; NestJS: `ConfigModule.forRoot()` with a validation schema.

2. **Routers and project layout.**

   ```python
   # app/routers/todos.py
   from fastapi import APIRouter

   router = APIRouter(prefix="/todos", tags=["todos"])

   @router.get("/{todo_id}")
   def get_todo(todo_id: int) -> Todo: ...

   # app/main.py
   from app.routers import todos

   app = FastAPI(lifespan=lifespan)
   app.include_router(todos.router)
   ```

   ```text
   app/
     main.py        create the app, lifespan, include routers
     config.py      Settings and get_settings
     deps.py        get_db, current_user, shared Annotated aliases
     models.py      ORM tables
     schemas.py     Pydantic request and response models
     routers/       one module per resource: todos.py, users.py
     services/      business logic with no FastAPI imports
   tests/
     conftest.py    client fixture and dependency overrides
   ```

   `APIRouter` takes the same decorators as `app`, plus `dependencies=[Depends(require_user)]` to protect every route in it. Keeping services free of FastAPI imports means they can be called from a worker or a CLI too. Express: `const router = express.Router(); app.use("/todos", router);`. NestJS: a module with `@Controller("todos")`.

3. **Background tasks.**

   ```python
   from fastapi import BackgroundTasks

   def send_welcome_email(email: str) -> None: ...

   @router.post("/users", status_code=201)
   def create_user(body: UserIn, tasks: BackgroundTasks) -> UserOut:
       user = save_user(body)
       tasks.add_task(send_welcome_email, user.email)    # the function, then its arguments
       return user
   ```

   FastAPI injects `BackgroundTasks` because of its type. The task runs after the response is sent, in the same process (a sync function goes to the thread pool), with no retries and no persistence: fine for a log line or a cache warm-up, wrong for anything that must survive a restart, which belongs in a queue such as Celery or arq. Express: work after `res.json()`; NestJS: an event emitter or BullMQ.

4. **Lifespan for startup and shutdown.**

   ```python
   from contextlib import asynccontextmanager
   import httpx
   from fastapi import FastAPI, Request

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       app.state.http = httpx.AsyncClient(timeout=30)    # startup, once per worker
       yield                                            # the app serves requests here
       await app.state.http.aclose()                    # shutdown

   app = FastAPI(lifespan=lifespan)

   def get_http(request: Request) -> httpx.AsyncClient:
       return request.app.state.http

   Http = Annotated[httpx.AsyncClient, Depends(get_http)]
   ```

   The same generator idea as the DB dependency, one level up: `@asynccontextmanager` turns an async generator into something usable with `async with`, and FastAPI enters it at startup and exits it at shutdown. It replaces the deprecated `@app.on_event("startup")` hooks. Express: code before `app.listen` plus `process.on("SIGTERM")`; NestJS: `onModuleInit` and `onApplicationShutdown`.

5. **Streaming a response with an async generator.**

   ```python
   import asyncio
   from collections.abc import AsyncIterator
   from fastapi.responses import StreamingResponse

   @app.get("/chat")
   async def chat(q: str) -> StreamingResponse:
       async def tokens() -> AsyncIterator[str]:
           for word in ["Hello", "from", "FastAPI"]:    # real code: async for over the LLM stream
               yield f"data: {word}\n\n"
               await asyncio.sleep(0.1)
       return StreamingResponse(tokens(), media_type="text/event-stream")
   ```

   `async def` plus `yield` makes an async generator; `StreamingResponse` consumes it with `async for` and sends each piece as soon as it is produced. Recent FastAPI versions also let the endpoint itself be the generator: declare `response_class=EventSourceResponse` (from `fastapi.sse`) and `yield` Pydantic models or dicts, and FastAPI writes the SSE framing. Express: `res.write(chunk)` in a loop, then `res.end()`; NestJS: `@Sse()` returning an Observable.

6. **Testing with TestClient.**

   ```python
   # tests/conftest.py
   import pytest
   from fastapi.testclient import TestClient
   from app.config import Settings, get_settings
   from app.main import app

   @pytest.fixture
   def client():
       app.dependency_overrides[get_settings] = lambda: Settings(openai_api_key="test-key")
       with TestClient(app) as c:          # `with` runs lifespan startup and shutdown
           yield c
       app.dependency_overrides.clear()

   # tests/test_todos.py
   def test_create_then_get(client):
       r = client.post("/todos", json={"title": "buy milk"})
       assert r.status_code == 201
       assert client.get(f"/todos/{r.json()['id']}").json()["title"] == "buy milk"
   ```

   TestClient calls the ASGI app in-process through httpx, with no server and no port, and exposes a requests-style API. Without the `with` block, lifespan never runs and `app.state.http` does not exist. Exceptions raised inside the app propagate to the test by default, so you see the real traceback. For `async def` tests use `httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")`. Express: supertest; NestJS: `Test.createTestingModule(...).overrideProvider(...)`.

### Concepts you must understand
- A route decorator registers the function and returns it unchanged, so handlers stay plain functions you can call and unit test.
- FastAPI reads the signature when the route is registered: names in the path template are path parameters, `BaseModel` types are the JSON body, other simple types are query parameters, required unless they have a default.
- `Annotated[T, Query(...)]`, `Path(...)`, `Header(...)` and `Depends(...)` add metadata without changing the type; define aliases such as `DB = Annotated[Session, Depends(get_db)]` once and reuse them.
- Input that fails validation gets a 422 with a `detail` list before your code runs; your own errors are `raise HTTPException(status_code=..., detail=...)`.
- A dependency with `yield` is a generator driven like a context manager; endpoint exceptions are thrown into it at the `yield`, and an `except` there must re-raise.
- A return annotation or `response_model` validates, filters and documents the output; it is your guard against leaking columns.
- `async def` handlers must only await non-blocking calls; `def` handlers run in a thread pool.
- `lifespan` owns process-wide resources such as HTTP clients and pools; settings come from pydantic-settings, cached with `lru_cache` and injected with `Depends`.
- `BackgroundTasks` run after the response in the same process; they are not a job queue.
- Route order matters: a static path such as `/todos/export` declared after `/todos/{todo_id}` is matched as an id and fails with 422.

| JavaScript | Python | Note |
|---|---|---|
| `app.get("/todos/:id", handler)` | `@app.get("/todos/{todo_id}")` | the decorator returns the same function |
| `Number(req.params.id)` | `todo_id: int` | converted, 422 on failure |
| `req.query.limit ?? 20` | `limit: int = 20` | the default makes it optional |
| Zod `parse(req.body)` or a Nest DTO | `body: TodoIn` (a `BaseModel`) | validated before your code runs |
| `res.status(404).json(...)` | `raise HTTPException(404, "...")` | works from helpers and dependencies too |
| `res.status(201)` | `status_code=201` on the decorator | FastAPI's default is 200 |
| middleware setting `req.db` | `Depends(get_db)` with `yield` | cleanup in `finally` |
| `express.Router()` | `APIRouter(prefix="/todos")` | `app.include_router(router)` |
| `dotenv` plus Zod | `BaseSettings` from pydantic-settings | missing keys fail at startup |
| code before `app.listen`, `onModuleInit` | `lifespan` context manager | once per worker process |
| `res.write()` in a loop | `StreamingResponse(async_gen())` | async generator |
| supertest, `overrideProvider` | `TestClient`, `app.dependency_overrides` | `with TestClient(app)` runs lifespan |

### Q. Add a `GET /search` endpoint: `q` is required and 2 to 50 characters, `limit` defaults to 10 with a maximum of 50, and `tags` may repeat as `?tags=a&tags=b`. Invalid input must return 422.
**Short answer (45 seconds):** Declare each rule in the signature with `Annotated` and `Query`: `q` with no default and `min_length`/`max_length`, `limit` with `ge`/`le` and a default, and `tags` as `list[str] | None` with an explicit `Query()`. FastAPI then returns 422 with one entry per bad parameter before the handler runs, and `/docs` shows every constraint.

**Deeper explanation:**

```python
from typing import Annotated
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/search")
def search(
    q: Annotated[str, Query(min_length=2, max_length=50)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    tags: Annotated[list[str] | None, Query()] = None,
) -> dict:
    return {"q": q, "limit": limit, "tags": tags or []}
```

`GET /search?q=ai&tags=a&tags=b` returns `{"q": "ai", "limit": 10, "tags": ["a", "b"]}`. `GET /search?q=a` returns 422:

```json
{"detail": [{"type": "string_too_short", "loc": ["query", "q"],
  "msg": "String should have at least 2 characters", "input": "a", "ctx": {"min_length": 2}}]}
```

No default means required: a missing `q` gives `"type": "missing"`. The explicit `Query()` on `tags` is not optional decoration: without it, FastAPI treats a `list[str]` parameter as a JSON body field, and on a GET request `?tags=a` is silently ignored, so the handler sees `None`. Edge cases: `?limit=0` and `?limit=51` are 422, and `?limit=abc` is `int_parsing`.

**Follow-ups they will ask:**
- The client sends `?item-query=...`, which is not a valid Python name. : `Annotated[str, Query(alias="item-query")]`.
- Many filters on one endpoint? : FastAPI 0.115 and later accept a Pydantic model for query parameters, `filters: Annotated[SearchFilters, Query()]`, so the rules live in one class.
- Should `limit=500` clamp to 50 or fail? : fail with 422 by default; clamping hides client bugs, and the error message tells them the maximum.

**Mistakes to avoid:**
- Writing `q: str | None` without `= None` and assuming it is optional; it is still required.
- Forgetting `Query()` on list parameters and debugging why the filter never applies.

### Q. A client posts `{"title": "buy milk"}` to this endpoint and gets 422 "Field required" with `"loc": ["query", "title"]`. Find the bug and fix it.
**Short answer (45 seconds):** The handler declares `title: str` as a plain parameter, and FastAPI treats simple-typed parameters as query parameters, so it looks for `?title=` and ignores the JSON body. The `loc` in the error says exactly that. I fix it with a Pydantic model for the body, or with `Body(embed=True)` when a single field is really wanted.

**Deeper explanation:** The buggy code:

```python
@app.post("/todos", status_code=201)
def create_todo(title: str, done: bool = False):
    ...
```

The rule FastAPI applies: a name in the path template is a path parameter; a `BaseModel` (or a parameter marked with `Body()`) is the body; everything else with a simple type is a query parameter. The fix:

```python
from typing import Annotated
from fastapi import Body
from pydantic import BaseModel, Field

class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool = False

@app.post("/todos", status_code=201)
def create_todo(body: TodoIn) -> Todo:
    ...

# or, for a single loose field: expects {"title": "..."}
@app.post("/titles")
def add_title(title: Annotated[str, Body(embed=True)]):
    ...
```

The model is the better fix: it adds constraints, appears in `/docs`, and can be reused for the response. Two related shapes catch people out. With two model parameters, `def f(todo: TodoIn, meta: Meta)`, FastAPI expects them nested under their names: `{"todo": {...}, "meta": {...}}`. With one model and `Body(embed=True)`, it expects `{"body": {...}}`. Reading the `loc` path in a 422 (`query`, `path`, `body`, `header`) is the fastest way to see where FastAPI looked.

**Follow-ups they will ask:**
- How do you accept form data or files? : `Annotated[str, Form()]` and `UploadFile`, which need the python-multipart package (included in `fastapi[standard]`).
- How do you accept any JSON at all? : `payload: dict[str, Any]`, but you lose validation and docs, so do it only for genuinely free-form data such as webhooks you store raw.

**Mistakes to avoid:**
- Switching to `await request.json()` to "make it work", which throws away validation, docs and the 422 contract.
- Assuming FastAPI behaves like Express, where `req.body` is filled no matter what the handler declares.

### Q. Write a database dependency that commits when the endpoint succeeds and rolls back when it raises, and make sure a failed commit can never be reported to the client as 200.
**Short answer (45 seconds):** A `yield` dependency with `try`, `except Exception: rollback(); raise` and `finally: close()`, committing after the `yield`. The subtle part is timing: by default FastAPI runs the code after `yield` once the response has already been sent, so a failing commit would happen after the client got 200. On recent FastAPI I declare it with `Depends(get_session, scope="function")` so the commit runs before the response leaves; on older versions I commit explicitly in the service code.

**Deeper explanation:**

```python
from collections.abc import Iterator
from typing import Annotated, Any
from fastapi import Depends
from sqlalchemy.orm import Session

def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session          # endpoint runs here; its exceptions are thrown in at this line
        session.commit()
    except Exception:
        session.rollback()
        raise                  # mandatory: let FastAPI turn it into a response
    finally:
        session.close()

SessionDep = Annotated[Session, Depends(get_session, scope="function")]

@app.post("/orders", status_code=201, response_model=OrderOut)
def create_order(body: OrderIn, db: SessionDep) -> Any:
    order = Order(**body.model_dump())
    db.add(order)
    db.flush()                 # assigns the id without committing
    return order
```

When the endpoint raises, including `HTTPException(404)`, Python resumes the generator by raising that exception at the `yield`, so the `except` block rolls back. If you catch and do not re-raise, FastAPI fails with "Response not awaited. There's a high chance that the application code is raising an exception and a dependency with yield has a block with a bare except...". With the default request scope, a commit that fails (a unique constraint, a dropped connection) runs after the 200 was sent and only shows up in logs; with `scope="function"` it becomes a 500 the client sees. FastAPI caches dependencies per request, so if `current_user` also depends on `get_session`, both receive the same session and share the transaction.

**Follow-ups they will ask:**
- The async version? : `async def get_session()` with `async with AsyncSessionLocal() as session:` and the same try, except and raise around `yield`.
- Can a background task use this session? : no, it is closed by then; open a new session inside the task.

**Mistakes to avoid:**
- A bare `except:` or `except Exception:` that logs and swallows the error.
- Committing in both the dependency and the endpoint, which makes rollback on error impossible.

### Q. `GET /users/{id}` returns `password_hash` and `stripe_customer_id` to the browser. Fix it so the next column someone adds cannot leak either.
**Short answer (45 seconds):** The endpoint returns the ORM object with no response model, so FastAPI serializes every attribute. I add a `UserOut` model listing only public fields and attach it with `response_model=UserOut` (or a `-> UserOut` return annotation). From then on the output is an allow-list: new columns stay private until someone adds them to `UserOut` on purpose, and a test pins the exact key set.

**Deeper explanation:**

```python
from typing import Any
from pydantic import BaseModel, ConfigDict

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # lets UserOut.model_validate(orm_row) work
    id: int
    email: str
    display_name: str | None = None

@app.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: SessionDep) -> Any:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user                     # FastAPI reads the attributes UserOut declares

def test_user_response_has_only_public_fields(client, seeded_user):
    body = client.get(f"/users/{seeded_user.id}").json()
    assert set(body) == {"id", "email", "display_name"}
```

`response_model` validates the returned object against `UserOut` and serializes only its fields, which also works for dicts with extra keys. The return annotation does the same when the function really returns a `UserOut`; use `response_model=` plus `-> Any` when it returns an ORM row, so type checkers stay honest. The pattern scales as three models per resource: `UserIn` (what clients may send, without `id` or `role`), `UserOut` (what they may see) and the ORM `User` (everything). The key-set test fails the moment someone adds a field to `UserOut` by accident, which is the review point you want.

**Follow-ups they will ask:**
- Hide `None` fields? : `response_model_exclude_none=True` on the decorator.
- Different views for admins? : a separate `UserAdminOut` model on an admin-only router, not conditional field deletion inside one handler.
- Does this cost much? : validation runs in pydantic-core (Rust) and is negligible next to the database query.

**Mistakes to avoid:**
- Deleting keys by hand (`data.pop("password_hash")`), which is a deny-list and fails open for every new column.
- Reusing the input model as the output model, so fields such as `password` echo back.

### Q. Rewrite this Express route in FastAPI.
**Short answer (45 seconds):** Every manual check in the Express handler becomes part of the signature: the path parameter becomes `project_id: int`, the status filter becomes a `Literal["open", "done"]` query parameter with a default, the limit becomes `Annotated[int, Query(ge=1, le=100)]`, the 404 becomes `raise HTTPException`, and the field picking becomes a `TaskOut` response model. The handler shrinks to the query itself.

**Deeper explanation:** The Express version:

```js
app.get("/projects/:projectId/tasks", async (req, res) => {
  const projectId = Number(req.params.projectId);
  if (!Number.isInteger(projectId)) return res.status(422).json({ error: "bad id" });
  const status = req.query.status ?? "open";
  if (!["open", "done"].includes(status)) return res.status(422).json({ error: "bad status" });
  const limit = Math.min(Number(req.query.limit ?? 20), 100);
  const project = await db.projects.findById(projectId);
  if (!project) return res.status(404).json({ error: "project not found" });
  const tasks = await db.tasks.find({ projectId, status }).limit(limit);
  res.json(tasks.map(({ id, title, status }) => ({ id, title, status })));
});
```

The FastAPI version, with an async SQLAlchemy session dependency `AsyncDB`:

```python
from typing import Annotated, Any, Literal
from fastapi import HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

class TaskOut(BaseModel):
    id: int
    title: str
    status: Literal["open", "done"]

@app.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
async def list_tasks(
    project_id: int,
    db: AsyncDB,
    status: Literal["open", "done"] = "open",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Any:
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    rows = await db.scalars(
        select(Task).where(Task.project_id == project_id, Task.status == status).limit(limit)
    )
    return rows.all()
```

`async def` is correct here because every slow call is awaited on an async driver. Two behavior changes are worth saying aloud: `?limit=500` is now a 422 instead of a silent clamp to 100, and the error body is FastAPI's standard `{"detail": ...}` shape instead of `{"error": ...}`, so the frontend's error handling must change, or you add an exception handler that keeps the old shape.

**Follow-ups they will ask:**
- Keep the old error format? : register `@app.exception_handler(RequestValidationError)` and `HTTPException` handlers that return `{"error": ...}`.
- What if the driver is sync? : make the handler a plain `def` with a sync session; FastAPI runs it in the thread pool.

**Mistakes to avoid:**
- Porting the manual checks line by line into the Python handler, which duplicates what the signature already guarantees.
- Leaving out the response model and returning ORM rows with every column.

### Q. A teammate creates a new `httpx.AsyncClient` inside every request handler, and under load the service shows rising latency and connection errors. Move the client to lifespan, inject it, and keep it testable.
**Short answer (45 seconds):** A client per request means a new connection pool, a new TLS handshake and new sockets for every call, and clients that are never closed leak sockets until the process runs out of file descriptors. I create one `AsyncClient` per worker in `lifespan`, store it on `app.state`, close it at shutdown, inject it through a small dependency, and in tests override that dependency with a client backed by `httpx.MockTransport`.

**Deeper explanation:**

```python
from contextlib import asynccontextmanager
from typing import Annotated
import httpx
from fastapi import Depends, FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(
        base_url="https://api.vendor.example",
        timeout=httpx.Timeout(10.0, connect=3.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    yield
    await app.state.http.aclose()

app = FastAPI(lifespan=lifespan)

def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http

Http = Annotated[httpx.AsyncClient, Depends(get_http)]

@app.get("/forecast/{city}")
async def forecast(city: str, http: Http) -> dict:
    r = await http.get(f"/forecast/{city}")
    r.raise_for_status()
    return r.json()

# test
def fake_vendor(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"city": request.url.path.rsplit("/", 1)[-1], "temp_c": 31})

def test_forecast():
    mock_http = httpx.AsyncClient(base_url="https://api.vendor.example",
                                  transport=httpx.MockTransport(fake_vendor))
    app.dependency_overrides[get_http] = lambda: mock_http
    with TestClient(app) as client:
        assert client.get("/forecast/dubai").json() == {"city": "dubai", "temp_c": 31}
    app.dependency_overrides.clear()
```

One client per worker reuses keep-alive connections, so most calls skip the TCP and TLS setup, and `Limits` caps how hard this worker can hit the vendor. The same pattern holds for the OpenAI or Anthropic SDK clients, Redis pools and database engines. `MockTransport` answers requests in-process, so the test exercises the real handler code with no network.

**Follow-ups they will ask:**
- Why not a module-level client created at import time? : nothing closes it at shutdown, and its connections get tied to whichever event loop used them first, which breaks tests that run several loops.
- With four workers, how many pools? : four, one per process, so size `max_connections` per worker.

**Mistakes to avoid:**
- `async with httpx.AsyncClient() as c:` inside the handler, which is correct but still pays for a fresh pool on every request.
- Forgetting `with TestClient(app)`, so lifespan never runs and `app.state.http` raises `AttributeError`.

### Practice
- Practice kit: open `python-practice/exercises/p21_fastapi.py`, implement each function, then run `uv run --with pytest --with fastapi --with httpx pytest tests/test_p21_fastapi.py` from the `python-practice` folder.
- In a scratch copy of the kit, add a route `GET /todos/export` below `GET /todos/{todo_id}`, call it with TestClient, read the 422 `int_parsing` error, then move the route above and call it again.
- From the `python-practice` folder, run `uv run --with "fastapi[standard]" uvicorn solutions.p21_fastapi:app --reload`, open `http://127.0.0.1:8000/docs`, and find where `ge=1`, `le=100`, the 201 and the 204 status codes show up.
- In the REPL, `import inspect` and print `inspect.signature(list_todos)` from the solution: the `Annotated` metadata you see is what FastAPI reads.

## Pydantic in Depth [Core]

> Pydantic is the validation and serialization layer under FastAPI and most Python AI code: request and response bodies, settings, tool-call arguments, and the JSON an LLM returns. This lesson covers models and fields, defaults and optional fields, nested models, reading validation errors, `field_validator` and `model_validator`, `computed_field`, dumping and loading, strict and lax mode, `ConfigDict`, discriminated unions and LLM structured output, with Zod and class-validator as the reference points. The Backend track's question on Pydantic in an AI backend is the interview answer; this lesson is the mechanics behind it.

### Why it exists
Python type hints are not checked when the program runs: `def f(x: int)` happily accepts a string, and `json.loads` hands you plain dicts containing whatever the sender put there. Pydantic turns a class with type hints into a runtime validator and serializer: incoming data is checked, converted where the conversion is safe ("3" to 3), and otherwise rejected with a structured list of every problem. Before it, Python teams used marshmallow schemas or hand-written dict checks that lived apart from the types and drifted from them. Version 2 moved the core into Rust (pydantic-core), so validation is cheap; the costs are coercion rules you must learn, v1 to v2 renames (`.dict()` became `.model_dump()`), and validators that run in a defined order.

### In plain words
A Pydantic model is a customs desk with a declaration form. Every incoming bag, a dict or a JSON string, is checked field by field against the form. Small, safe fixes happen on the spot, such as reading the text "3" as the number 3. Anything else is rejected with one complete list: which field, what was wrong, what was received. What passes the desk is a typed object the rest of the program can trust, and on the way out the same desk packs it back into JSON exactly as declared.

### Walkthrough: models, fields and validation errors
1. **A model is a class with type hints.**

   ```python
   from pydantic import BaseModel

   class User(BaseModel):
       id: int
       email: str
       active: bool = True

   u = User(id="42", email="ana@x.io")     # keyword arguments only
   print(u.id, type(u.id))                 # 42 <class 'int'>
   print(u)                                # id=42 email='ana@x.io' active=True
   ```

   Construction validates, and the string "42" became an int. A dataclass would have stored the string without complaint. Zod: `const User = z.object({...})` plus `type User = z.infer<typeof User>`; in Zod the schema comes first and the type is derived, in Pydantic one class is both.

2. **Defaults, optional and required.**

   ```python
   class Profile(BaseModel):
       name: str                       # required
       nickname: str | None            # required, but may be None
       bio: str | None = None          # optional, defaults to None
       tags: list[str] = []            # safe: every instance gets its own list
   ```

   The trap: `str | None` only says None is an allowed value; without `= None` the key is still required and missing it gives "Field required". Mutable defaults such as `[]` are copied per instance in Pydantic, unlike Python function defaults; `Field(default_factory=list)` says the same thing explicitly. Zod keeps the two ideas separate as `.optional()` (may be missing) and `.nullable()` (may be null); Pydantic decides "may be missing" by the default and "may be null" by the type.

3. **Field adds constraints, aliases and docs.**

   ```python
   from pydantic import Field

   class Product(BaseModel):
       sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$", description="Stock code")
       price: float = Field(gt=0, le=10_000)
       name: str = Field(min_length=1, max_length=120)
       stock_count: int = Field(default=0, ge=0, alias="stockCount")
   ```

   Constraints: `gt`, `ge`, `lt`, `le`, `multiple_of`, `min_length` and `max_length` (for strings and lists) and `pattern`. `alias` is the key expected in input data, and here is a trap: `Product(stock_count=3, ...)` is not an error, the unknown keyword is ignored and the field silently keeps its default 0. Allow both spellings with `ConfigDict(validate_by_name=True)` (Pydantic 2.11+; older code uses `populate_by_name=True`). `description` and `examples` flow into the JSON schema and FastAPI's docs. Zod: `.min()`, `.max()`, `.regex()`, `.describe()`.

4. **Nested models and lists of models.**

   ```python
   class LineItem(BaseModel):
       sku: str
       qty: int = Field(gt=0)

   class Order(BaseModel):
       id: str
       items: list[LineItem]

   order = Order.model_validate({"id": "o1", "items": [{"sku": "a", "qty": 2}]})
   print(type(order.items[0]))             # <class '__main__.LineItem'>
   ```

   Validation recurses into every nested dict and list element, turning each inner dict into a `LineItem`, and errors point at the exact element. Zod: `z.array(LineItem)` inside `z.object`.

5. **Reading a ValidationError.**

   ```python
   from pydantic import ValidationError

   try:
       Order.model_validate({"id": "o1", "items": [{"sku": "a", "qty": 1}, {"sku": "b", "qty": 0}]})
   except ValidationError as e:
       print(e.error_count())                  # 1
       print(e.errors(include_url=False))
       # [{'type': 'greater_than', 'loc': ('items', 1, 'qty'),
       #   'msg': 'Input should be greater than 0', 'input': 0, 'ctx': {'gt': 0}}]
   ```

   `str(e)` is the human form:

   ```text
   1 validation error for Order
   items.1.qty
     Input should be greater than 0 [type=greater_than, input_value=0, input_type=int]
   ```

   Pydantic collects every error before raising, not just the first. `loc` is the path (integers are list indexes), `type` is a stable machine code to branch on, `msg` is for humans. FastAPI returns this same list as the 422 `detail`, with `"body"` or `"query"` added at the front of `loc`. To send errors to a log pipeline or an LLM, use `e.json()` or `e.errors(include_context=False)`, because `json.dumps(e.errors())` fails on the exception objects stored in `ctx`. Zod: `error.issues` with `path`, `code` and `message`.

6. **Lax and strict mode.**

   ```python
   class Reading(BaseModel):
       value: int
       ok: bool

   Reading(value="7", ok="yes")        # lax (default): value=7 ok=True
   Reading(value=7.5, ok=True)         # error int_from_float: fractions are never truncated
   Reading.model_validate({"value": "7", "ok": True}, strict=True)   # error int_type
   ```

   Lax mode converts only when nothing is lost: numeric strings to numbers, `"yes"`/`"no"`/`"true"`/`"1"` to bool, ISO strings to datetimes. It never turns a number into a string, so `name: str` given `7` is an error. Strict mode accepts only the exact type, and you can switch it on per call (`strict=True`), per field (`Field(strict=True)`) or per model (`ConfigDict(strict=True)`). Validating JSON in strict mode still accepts strings for types JSON has no syntax for, such as datetime and UUID. Zod is strict by default and coerces only when asked, with `z.coerce.number()`.

### Walkthrough: validators, computed fields and serialization
1. **field_validator.**

   ```python
   from pydantic import field_validator

   class Signup(BaseModel):
       email: str
       tags: list[str] = []

       @field_validator("email")
       @classmethod
       def normalize_email(cls, v: str) -> str:
           v = v.strip().lower()
           if "@" not in v:
               raise ValueError("email must contain @")
           return v                         # the returned value is what gets stored

       @field_validator("tags", mode="before")
       @classmethod
       def split_csv(cls, v: object) -> object:
           return v.split(",") if isinstance(v, str) else v
   ```

   The default `mode="after"` runs once the type check passed, so `v` is already a `str`. `mode="before"` receives the raw input, which is how `"a,b,c"` becomes a list before list validation runs. Raise `ValueError` to report a problem as a normal `value_error` entry; any other exception type escapes validation entirely and becomes a crash (a 500 in FastAPI, not a 422). Zod: `.transform()` and `.refine()`; class-validator: a custom decorator.

2. **model_validator for rules across fields.**

   ```python
   from datetime import date
   from typing import Self              # Python 3.11+
   from pydantic import model_validator

   class DateRange(BaseModel):
       start: date
       end: date

       @model_validator(mode="after")
       def check_order(self) -> Self:
           if self.end < self.start:
               raise ValueError("end must not be before start")
           return self
   ```

   An `after` model validator runs on the finished instance and must return it. It only runs when every field passed, so a bad `start` is reported alone, without a confusing cross-field error. Its errors have an empty `loc`, `()`. A `mode="before"` model validator receives the raw input, usually a dict, which is where you rename or reshape legacy payloads. Zod: `.superRefine()` on the object.

3. **computed_field.**

   ```python
   from pydantic import computed_field

   class Cart(BaseModel):
       prices: list[float]

       @computed_field
       @property
       def total(self) -> float:
           return round(sum(self.prices), 2)

   Cart(prices=[1.1, 2.2]).model_dump()     # {'prices': [1.1, 2.2], 'total': 3.3}
   ```

   A plain `@property` is not serialized; `@computed_field` adds the value to `model_dump`, JSON output and the response schema in FastAPI's docs. It is recalculated on every access, so keep it cheap. Zod has no direct equivalent: you map the parsed object yourself.

4. **model_dump and model_dump_json.**

   ```python
   user.model_dump()                               # dict of Python objects (datetime stays datetime)
   user.model_dump(mode="json")                    # dict of JSON-safe values (ISO strings)
   user.model_dump(exclude={"password_hash"})      # drop named fields
   user.model_dump(exclude_none=True)              # drop fields whose value is None
   user.model_dump(exclude_unset=True)             # only fields the input actually provided
   user.model_dump_json(by_alias=True, indent=2)   # a JSON str, keys from aliases
   ```

   `exclude_unset` is what makes PATCH endpoints partial, `exclude_none` keeps payloads to an LLM provider small, and `by_alias` produces camelCase keys for a JavaScript client. `Field(exclude=True)` removes a field from every dump. The v1 names (`.dict()`, `.json()`, `parse_obj`) still work but are deprecated. Zod parses but does not serialize; you build output objects yourself.

5. **model_validate, model_validate_json and model_copy.**

   ```python
   Order.model_validate({"id": "o1", "items": []})          # from a dict
   Order.model_validate_json('{"id": "o1", "items": []}')   # from str or bytes, in one pass
   changed = order.model_copy(update={"id": "o2"})          # shallow copy, NOT validated
   ```

   Use `model_validate_json` for raw HTTP bodies and LLM output: parsing and validation happen together in Rust, and malformed JSON becomes a `json_invalid` validation error instead of a separate exception type. `model_validate(row, from_attributes=True)` reads attributes from an ORM object. `model_copy(update=...)` trusts you completely: `update={"qty": -5}` is accepted silently, so re-validate (`Model.model_validate(old.model_dump() | changes)`) when the changes came from outside.

6. **ConfigDict: extra, frozen and friends.**

   ```python
   from pydantic import ConfigDict

   class ToolArgs(BaseModel):
       model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
       city: str
       days: int = 1

   ToolArgs(city="Dubai", day=3)      # error extra_forbidden on "day": the typo is caught
   args = ToolArgs(city=" Dubai ")    # city == "Dubai"
   args.days = 2                      # error frozen_instance
   ```

   `extra` is `"ignore"` by default (unknown keys dropped silently), `"forbid"` (an error) or `"allow"` (kept on the instance). `frozen=True` blocks assignment and makes instances hashable, but only shallowly: a `list` or `dict` field can still be changed in place, so use tuples inside frozen models. Other common settings: `from_attributes=True` for ORM objects, `alias_generator=to_camel` for camelCase APIs. NestJS: `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })`; Zod: `.strict()` versus its default of stripping unknown keys.

### Walkthrough: unions, Zod and LLM structured output
1. **Discriminated unions.**

   ```python
   from typing import Annotated, Literal
   from pydantic import BaseModel, Field

   class SearchCall(BaseModel):
       tool: Literal["search"]
       query: str

   class WeatherCall(BaseModel):
       tool: Literal["weather"]
       city: str
       unit: Literal["c", "f"] = "c"

   ToolCall = Annotated[SearchCall | WeatherCall, Field(discriminator="tool")]

   class AgentStep(BaseModel):
       thought: str
       calls: list[ToolCall]
   ```

   A plain `SearchCall | WeatherCall` makes Pydantic try each member and pick the best match, which works but produces long error lists, one block per member. With a discriminator, the `tool` value selects the model directly: one lookup, one validation, and an unknown tool gives a single clear `union_tag_invalid` error ("Input tag 'email' found using 'tool' does not match any of the expected tags: 'search', 'weather'"). Zod: `z.discriminatedUnion("tool", [Search, Weather])`.

2. **TypeAdapter for types that are not models.**

   ```python
   from pydantic import TypeAdapter

   CALLS = TypeAdapter(list[ToolCall])       # build once, at import time
   CALLS.validate_json('[{"tool": "weather", "city": "Dubai"}]')
   # [WeatherCall(tool='weather', city='Dubai', unit='c')]
   CALLS.json_schema()                       # JSON schema for a bare list
   ```

   `TypeAdapter` gives any type (a list, a union, a `dict[str, int]`) the same `validate_python`, `validate_json`, `dump_python` and `json_schema` methods a model has. Building one compiles a validator, so create it once at module level rather than inside a function that runs per request.

3. **Generate the schema the LLM must follow.**

   ```python
   class Answer(BaseModel):
       summary: str = Field(description="Two sentences, plain English, no markdown")
       confidence: float = Field(ge=0, le=1, description="0 means guessing, 1 means certain")
       sources: list[str] = Field(description="URLs taken only from the provided context")

   schema = Answer.model_json_schema()     # pass as the structured-output or tool schema
   ```

   Field descriptions end up in the schema the model reads, so write them as instructions for the model. Providers' structured-output modes constrain generation to a schema, but each supports only part of JSON Schema, and your validators are not in the schema at all, so you still validate what comes back.

4. **Validate, and repair once.**

   ```python
   def parse_answer(raw: str) -> Answer | str:
       try:
           return Answer.model_validate_json(raw)
       except ValidationError as e:
           problems = "\n".join(
               f"- {'.'.join(map(str, err['loc'])) or 'root'}: {err['msg']}"
               for err in e.errors(include_url=False, include_context=False, include_input=False)
           )
           return f"Your JSON was invalid:\n{problems}\nReturn corrected JSON only."
   ```

   The returned string becomes the next user message for one repair attempt; cap repairs at one or two and log every failure, because a model that fails twice usually needs a prompt or schema change, not a third try. `include_input=False` keeps a large invalid payload from being echoed back into the prompt. The complete retry flow is in the Backend track, section "Python & FastAPI for AI Backends".

5. **The same schema in Zod, class-validator and Pydantic.**

   ```js
   // Zod
   const Task = z.object({
     title: z.string().min(1),
     priority: z.number().int().min(1).max(5).default(3),
   }).strict();
   type Task = z.infer<typeof Task>;
   const task = Task.parse(input);              // throws ZodError

   // class-validator (NestJS)
   class TaskDto {
     @IsString() @MinLength(1) title: string;
     @IsInt() @Min(1) @Max(5) @IsOptional() priority = 3;
   }
   ```

   ```python
   class Task(BaseModel):
       model_config = ConfigDict(extra="forbid")
       title: str = Field(min_length=1)
       priority: int = Field(default=3, ge=1, le=5)

   task = Task.model_validate(data)             # raises ValidationError
   ```

   Zod derives the type from the schema; class-validator decorates a class whose TypeScript types are erased at runtime, so every check needs its own decorator and class-transformer to build the instance. In Pydantic the type hint is the check, and constraints are the only extra syntax. One semantic difference to remember: Zod's `z.number()` rejects `"3"`, while Pydantic's lax `int` accepts it unless you turn on strict mode.

### Concepts you must understand
- A model's type hints are enforced at construction; data that passes is converted to the declared types, and every failure is reported together in one `ValidationError`.
- Required versus optional is decided by the default, not the type: `x: str | None` is required but nullable, `x: str | None = None` is optional.
- Lax mode (the default) converts lossless inputs such as "3" to 3 but never truncates floats or turns numbers into strings; strict mode can be set per call, per field or per model.
- `field_validator` (after or before) handles one field, `model_validator` handles rules across fields; raise `ValueError` to report, and return the value or the instance.
- `computed_field` puts derived values into dumps and schemas; a plain `@property` is not serialized.
- `model_dump` options are `mode="json"`, `exclude`, `exclude_none`, `exclude_unset` and `by_alias`; `model_dump_json` returns a string produced in Rust.
- `model_validate_json` parses and validates in one pass; `model_copy(update=...)` skips validation entirely.
- `ConfigDict`: `extra="forbid"` catches typos and invented keys, `frozen=True` gives shallow immutability and hashing, `from_attributes=True` reads ORM objects, alias settings control camelCase.
- Discriminated unions pick the model from a `Literal` tag field: faster, clearer errors, and a schema LLM providers and OpenAPI tools understand.
- For LLM output: generate the schema with `model_json_schema()`, parse with `model_validate_json`, feed the errors back once, then fail loudly.

| JavaScript | Python | Note |
|---|---|---|
| `z.object({...})` | `class M(BaseModel)` | the class is both schema and type |
| `z.infer<typeof M>` | the class itself | no separate type declaration |
| `M.parse(x)`, `M.safeParse(x)` | `M.model_validate(x)` in try/except | errors in `ValidationError.errors()` |
| `.optional()`, `.nullable()` | a default (`= None`), `T \| None` | two separate ideas in both libraries |
| `z.string().min(1).max(50)` | `Field(min_length=1, max_length=50)` | |
| `z.coerce.number()` | lax mode, the default | Zod is strict by default, Pydantic is not |
| `.refine()`, `.superRefine()` | `field_validator`, `model_validator` | raise `ValueError` to report |
| `.transform()` | `field_validator(mode="before")` or a validator's return value | |
| `.strict()` | `ConfigDict(extra="forbid")` | Pydantic's default ignores extras |
| `z.discriminatedUnion("tool", [...])` | `Annotated[A \| B, Field(discriminator="tool")]` | tag fields are `Literal` |
| class-validator `@IsInt() @Min(1)` | `x: int = Field(ge=1)` | the hint is the type check |
| `Object.freeze(obj)` | `ConfigDict(frozen=True)` | both are shallow |

### Q. Write a `BookingRequest` model: check-out must be after check-in, a stay is at most 30 nights, guests must be 1 to 8, and an optional promo code is normalized to uppercase.
**Short answer (45 seconds):** Single-field rules go on the fields: `guests` gets `Field(ge=1, le=8)`, and the promo code gets an after `field_validator` that strips and uppercases it. The date rules involve two fields, so they go in a `model_validator(mode="after")` that computes the number of nights and raises `ValueError` for zero, negative or more than 30.

**Deeper explanation:**

```python
from datetime import date
from typing import Self
from pydantic import BaseModel, Field, field_validator, model_validator

class BookingRequest(BaseModel):
    check_in: date
    check_out: date
    guests: int = Field(ge=1, le=8)
    promo_code: str | None = None

    @field_validator("promo_code")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else None

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        nights = (self.check_out - self.check_in).days
        if nights < 1:
            raise ValueError("check_out must be after check_in")
        if nights > 30:
            raise ValueError("stays are limited to 30 nights")
        return self

BookingRequest(check_in="2026-12-01", check_out="2026-12-05", guests="2", promo_code=" winter10 ")
# check_in=date(2026, 12, 1) check_out=date(2026, 12, 5) guests=2 promo_code='WINTER10'
```

ISO strings become `date` objects and `"2"` becomes `2` in lax mode. Swapped dates produce one error with `loc` `()` and the message "Value error, check_out must be after check_in". The `after` model validator only runs when every field passed, so `guests=9` with a 60-night stay reports only the guests error; the client fixes it and then learns about the length limit. If the UI needs the date error attached to a field, check the order in a `field_validator("check_out")` that takes a second `info: ValidationInfo` argument and reads `info.data.get("check_in")`, so the error's `loc` is `("check_out",)`. An empty-string promo code becomes `None`, because `""` is falsy.

**Follow-ups they will ask:**
- How do you reject check-in dates in the past? : compare with today's date in the model validator, passed in through `model_validate(data, context={"today": ...})` and read from `info.context`, so tests do not depend on the real clock.
- Where do business rules such as "the promo code exists" go? : not in the model; validation should be pure and fast, so database lookups belong in the service or a FastAPI dependency.

**Mistakes to avoid:**
- Reading `info.data["check_in"]` with square brackets in a field validator: when `check_in` itself failed, the key is absent and the validator crashes with `KeyError`.
- Returning nothing from the model validator: an after model validator must return `self`.

### Q. Predict what this code prints and explain each line.
**Short answer (45 seconds):** Line one succeeds through lax coercion. Line two fails because a field typed `str | None` with no default is still required. Line three fails twice, because Pydantic will not truncate 2.5 to an int and will not turn 7 into a string. Line four succeeds, because bools are accepted as ints and "off" is a valid boolean string.

**Deeper explanation:** The code:

```python
from pydantic import BaseModel, ValidationError

class Item(BaseModel):
    qty: int
    in_stock: bool
    note: str | None

def show(**data):
    try:
        print(Item(**data))
    except ValidationError as e:
        print(e.error_count(), [err["type"] for err in e.errors()])

show(qty="3", in_stock="yes", note=None)
show(qty="3", in_stock="yes")
show(qty=2.5, in_stock=1, note=7)
show(qty=True, in_stock="off", note="")
```

The output:

```text
qty=3 in_stock=True note=None
1 ['missing']
2 ['int_from_float', 'string_type']
qty=1 in_stock=False note=''
```

Line one: `"3"` is a numeric string, so lax mode converts it, and `"yes"` is one of the accepted boolean strings. Line two: `note` has no default, so it is required even though None is an allowed value; the error type is `missing`. Line three: `2.5` would lose information as an int, so it is `int_from_float`, while `in_stock=1` passes because 1 and 0 are accepted as booleans; `note=7` fails because lax mode never converts numbers to strings. Both errors are reported, since Pydantic collects every problem. Line four: `True` is accepted for an int field and becomes 1, which surprises most people, and `"off"` maps to False.

**Follow-ups they will ask:**
- How do you reject `True` for `qty`? : `qty: int = Field(strict=True)`, or `StrictInt`, or strict mode on the model.
- Would `qty="3.0"` pass? : yes in lax mode, a string with a zero fraction parses to 3, while `"3.5"` fails with `int_parsing`.

**Mistakes to avoid:**
- Assuming Pydantic behaves like TypeScript, where types disappear at runtime and nothing is converted.
- Assuming `str | None` means "may be left out".

### Q. A partner API sends `userId`, `createdAt` and `displayName` in camelCase, your Python code should use snake_case, and responses back to the partner must be camelCase again. Model it.
**Short answer (45 seconds):** Keep snake_case attribute names and generate camelCase aliases with `alias_generator=to_camel`. Add `validate_by_name=True` so internal code can still construct the model with snake_case names, and `serialize_by_alias=True` (or `by_alias=True` per call) so output uses camelCase. In FastAPI, responses already serialize by alias by default.

**Deeper explanation:**

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class PartnerUser(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,     # user_id -> userId, created_at -> createdAt
        validate_by_name=True,        # also accept user_id=... (Pydantic 2.11+)
        serialize_by_alias=True,      # dumps use camelCase by default (2.11+)
    )
    user_id: int
    created_at: datetime
    display_name: str | None = None

u = PartnerUser.model_validate(
    {"userId": 1, "createdAt": "2026-11-02T10:00:00Z", "displayName": "Ana"}
)
u.user_id                                  # 1
u.model_dump_json()                        # '{"userId":1,"createdAt":"2026-11-02T10:00:00Z","displayName":"Ana"}'
u.model_dump(by_alias=False)               # {'user_id': 1, 'created_at': datetime(...), 'display_name': 'Ana'}
PartnerUser(user_id=2, created_at="2026-11-02T10:00:00Z")   # works thanks to validate_by_name
```

Without `validate_by_name`, `PartnerUser(user_id=2, ...)` reports `userId` as missing: once a field has an alias, input is matched by the alias only. On Pydantic before 2.11 the spellings are `populate_by_name=True` and `by_alias=True` on every dump call. The JSON schema and FastAPI's `/docs` use the aliases, so a TypeScript client generated from OpenAPI gets camelCase types. FastAPI's `response_model_by_alias` defaults to True, so a route returning this model sends camelCase even without `serialize_by_alias`.

**Follow-ups they will ask:**
- One field with a name that `to_camel` gets wrong, such as `api_url` versus `apiURL`? : set `Field(alias="apiURL")` on that field; an explicit alias beats the generator.
- Different input and output names? : `validation_alias` and `serialization_alias` on `Field` set them separately.

**Mistakes to avoid:**
- Naming the Python attributes in camelCase to match the JSON, which spreads the partner's convention through your codebase.
- Calling `model_dump()` for an outbound payload and sending snake_case keys, because plain dumps use field names unless told otherwise.

### Q. An agent's LLM returns its tool calls as a JSON array, and sometimes it invents a tool name or leaves out an argument. Parse the array into typed objects and build a repair message when validation fails.
**Short answer (45 seconds):** Model each tool as a class with a `Literal` tag, combine them in a discriminated union, and validate the whole array with a module-level `TypeAdapter(list[ToolCall])` using `validate_json`. On `ValidationError`, turn each error's `loc` and `msg` into one line of a repair prompt, send it back once, and fail the step if the second answer is still invalid.

**Deeper explanation:**

```python
from typing import Annotated, Literal
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

class SearchCall(BaseModel):
    tool: Literal["search"]
    query: str = Field(min_length=1)

class WeatherCall(BaseModel):
    tool: Literal["weather"]
    city: str
    unit: Literal["c", "f"] = "c"

ToolCall = Annotated[SearchCall | WeatherCall, Field(discriminator="tool")]
TOOL_CALLS = TypeAdapter(list[ToolCall])

def strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):                       # models love markdown fences
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text

def parse_or_repair(raw: str) -> tuple[list[SearchCall | WeatherCall] | None, str | None]:
    try:
        return TOOL_CALLS.validate_json(strip_fences(raw)), None
    except ValidationError as e:
        lines = [
            f"- {'.'.join(str(p) for p in err['loc']) or 'root'}: {err['msg']}"
            for err in e.errors(include_url=False, include_context=False, include_input=False)
        ]
        return None, ("Your tool calls were invalid:\n" + "\n".join(lines)
                      + "\nReply with the corrected JSON array only.")
```

For `[{"tool": "weather"}, {"tool": "email", "to": "a"}, {"tool": "search", "query": ""}]` the repair message reads:

```text
- 0.weather.city: Field required
- 1: Input tag 'email' found using 'tool' does not match any of the expected tags: 'search', 'weather'
- 2.search.query: String should have at least 1 character
```

The discriminator puts the tag name in each `loc` and lists the allowed tools when one is invented, which is exactly what the model needs to fix its answer. Malformed JSON arrives as a `json_invalid` error through the same path. Afterwards, dispatch with `match call:` and `case WeatherCall(city=city):`, and the type checker knows every field.

**Follow-ups they will ask:**
- Execute the valid calls and repair only the invalid ones? : validate items one by one with `TypeAdapter(ToolCall)` and collect results and errors separately.
- Where do the tool schemas for the provider come from? : `SearchCall.model_json_schema()` and `WeatherCall.model_json_schema()`, so the contract and the validator never drift.

**Mistakes to avoid:**
- Repairing in an unbounded loop; cap it at one or two attempts and record the failure for evals.
- `json.dumps(e.errors())` without `include_context=False`, which raises `TypeError` on the stored exception objects.

### Q. Rewrite this Zod schema as a Pydantic model and point out where the two libraries behave differently.
**Short answer (45 seconds):** Each Zod call maps to a type or a `Field` argument: `.uuid()` to `UUID`, `.trim()` to `str_strip_whitespace`, `.int().min().max()` to `int` with `ge` and `le`, `.default()` to a default, `.optional()` to `= None`, `.strict()` to `extra="forbid"`, and camelCase keys to an alias generator. The differences to call out are coercion (Pydantic accepts "3" for an int unless strict) and Zod's `.nullable()` without `.optional()`, which in Pydantic is a nullable field with no default.

**Deeper explanation:** The Zod schema:

```js
const CreateTask = z.object({
  id: z.string().uuid(),
  title: z.string().trim().min(1).max(200),
  priority: z.number().int().min(1).max(5).default(3),
  dueAt: z.coerce.date().optional(),
  labels: z.array(z.string()).max(5).default([]),
  assignee: z.string().email().nullable(),
}).strict();
type CreateTask = z.infer<typeof CreateTask>;
```

The Pydantic model:

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

class CreateTask(BaseModel):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True,
        alias_generator=to_camel, validate_by_name=True,
    )
    id: UUID
    title: str = Field(min_length=1, max_length=200)
    priority: int = Field(default=3, ge=1, le=5, strict=True)
    due_at: datetime | None = None
    labels: list[str] = Field(default_factory=list, max_length=5)
    assignee: EmailStr | None              # nullable but required, like Zod's .nullable()
```

`str_strip_whitespace` strips before the length check, so `"   "` fails `string_too_short`, as `.trim().min(1)` does. `strict=True` on `priority` restores Zod's refusal of `"3"`. `datetime` already accepts ISO strings and Unix timestamps, roughly what `z.coerce.date()` does. `EmailStr` needs the email-validator package (`pydantic[email]`, included in `fastapi[standard]`) and normalizes the domain to lowercase, while Zod's `.email()` only checks the format. `id` arrives as a real `uuid.UUID` object, not a string. In both libraries the class or the inferred type is what the rest of the code uses, so there is no second type declaration to keep in sync.

**Follow-ups they will ask:**
- How do you share this contract with the React frontend? : export the FastAPI OpenAPI schema and generate TypeScript types or Zod schemas from it, so Python stays the single source.
- Is `str_strip_whitespace` applied to `labels` too? : yes, the model-level setting applies to every string, list items included.

**Mistakes to avoid:**
- Translating `.nullable()` to `assignee: EmailStr | None = None`, which also makes the key optional and changes the contract.
- Forgetting `extra="forbid"`, so the Python version silently drops unknown keys that the Zod version rejected.

### Q. A shared config object is mutated inside one request and the change leaks into every later request. Make it immutable, and explain what `frozen=True` does and does not protect.
**Short answer (45 seconds):** Make the config models `frozen=True`, so assigning to a field raises `ValidationError` with type `frozen_instance`, and replace mutable containers with immutable ones: tuples instead of lists, nested frozen models instead of dicts. Code that needs a variant calls `model_copy(update=...)` and gets a new object. Frozen also makes instances hashable, which lets them be cache keys.

**Deeper explanation:**

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class Limits(BaseModel):
    model_config = ConfigDict(frozen=True)
    max_tokens: int = 1024
    models: tuple[str, ...] = ("small", "large")     # tuple, not list

class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    limits: Limits = Limits()
    headers: dict[str, str] = {}                     # still mutable in place

cfg = AppConfig(name="api")
try:
    cfg.limits.max_tokens = 5
except ValidationError as e:
    print(e.errors()[0]["type"])                     # frozen_instance

cfg.headers["x-debug"] = "1"                         # allowed: frozen is shallow
hash(Limits()) == hash(Limits())                     # True
# hash(cfg) raises TypeError: unhashable type: 'dict'

per_request = cfg.model_copy(update={"name": "api-eu"})   # new object, cfg untouched
```

`frozen=True` blocks `setattr` on that model's fields and generates `__hash__` from the field values. It does not reach inside containers: a `dict` or `list` field can still be changed in place, and because every request holds the same object, that is exactly the leak. Swap them for `tuple`, `frozenset` or nested frozen models, and hashing then works too. The usual source of the leak is a handler doing `settings.headers.update(...)` or `cfg.limits = ...` to customize one call; give it a copy instead. Remember `model_copy` skips validation, so only pass values you trust.

**Follow-ups they will ask:**
- Is this thread safe? : immutable objects are safe to share between threads and tasks, which matters because `def` handlers run in a thread pool.
- Why does hashability matter? : a frozen config can be an argument to an `lru_cache`-decorated function or a dict key.

**Mistakes to avoid:**
- Believing `frozen=True` deep-freezes everything and leaving a `dict` of headers inside.
- Copying with `copy.copy(cfg)` and then mutating a nested container, which is shared with the original.

### Practice
- Practice kit: open `python-practice/exercises/p22_pydantic.py`, implement each function, then run `uv run --with pytest --with fastapi --with httpx pytest tests/test_p22_pydantic.py` from the `python-practice` folder.
- In the REPL, define `class M(BaseModel): x: int` and try `M(x="1")`, `M(x="1.0")`, `M(x="1.5")`, `M(x=True)` and `M.model_validate({"x": "1"}, strict=True)`; predict each result before pressing Enter.
- Print `json.dumps(Order.model_json_schema(), indent=2)` for the kit's `Order` and find where `min_length`, `gt`, `extra="forbid"` and the computed `total` appear (try `mode="serialization"` too).
- Mount the kit's `Order` as the body of a FastAPI POST route, send it a body with `"qty": 0`, and compare the 422 `detail` with `ValidationError.errors()` from the REPL.
