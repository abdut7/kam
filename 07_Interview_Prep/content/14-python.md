# Python: Basics to Advanced

> This tab is for a JavaScript and TypeScript engineer learning Python from zero up to production FastAPI. Every lesson starts from what you already do in Node.js, shows how Python does it and why, then goes deep on the traps. How to use it: read a lesson's walkthroughs, switch to Quiz mode and attempt each exercise before you reveal the answer, then open that lesson's practice kit in `python-practice` and work until its tests pass. The sections run in learning order: the JavaScript-to-Python mental model, setup and tooling, variables and types, then strings, control flow, lists, dicts and sets, functions, modules, errors, files and JSON, classes, typing, generators, decorators and idioms, building up to async Python and FastAPI, with coding-pattern practice at the end.

## Python for JavaScript Developers [Start here]

> You already know how to program. What slows you down in Python is the set of JavaScript reflexes that are now wrong: braces, `===`, `i++`, `||` for defaults, `{...spread}`, `this`, `npm install`. This section maps each reflex to its Python form. Every FastAPI route, Pydantic model, LLM SDK call and pytest file you will read is built from these pieces, and the traps here (truthiness, mutable defaults, no block scope) are the first bugs JavaScript engineers ship in Python services.

### Why it exists
Python and JavaScript solve the same problems with different defaults. Python was designed for readability first: indentation is the syntax, there is usually one obvious way to write something, and the language refuses to guess, so `"1" + 1` raises a TypeError instead of returning `"11"`. That removes whole classes of JavaScript bugs (loose equality, implicit coercion, a lost `this`), but it costs you some shortcuts: no `++`, no multi-line lambdas, no object destructuring, and whitespace that matters. Learning the mapping once is far cheaper than discovering each difference as a production bug.

### In plain words
Moving from JavaScript to Python is like moving from a country that drives on the right to one that drives on the left. The car, the roads and the destinations are the same: variables, functions, loops, HTTP calls. What trips you up is the habit you no longer think about, like reaching for `===` or `||`. This lesson lists those habits, shows the Python version of each, and points out where the old habit silently does the wrong thing. After a week of practice the new rules stop feeling foreign.

### Walkthrough: syntax, names and values
1. **Blocks are indentation.** A colon opens a block, and every line inside it is indented by the same amount (4 spaces by convention). There are no braces and no semicolons; `elif` replaces `else if`, and the words `and`, `or`, `not` replace `&&`, `||`, `!`.

   ```python
   def label(score: int, is_admin: bool) -> str:
       if is_admin and score > 0:
           return "staff"
       elif score >= 90:
           return "gold"
       else:
           return "standard"
   ```

2. **No declarations and no block scope.** Assignment creates a name; there is no `let`, `const` or `var`. PEP 8 naming: `snake_case` for variables and functions, `PascalCase` for classes, `UPPER_CASE` for constants (a convention only, nothing stops reassignment). A name assigned inside an `if` or `for` body belongs to the whole function, so it is still visible after the block.

   ```python
   MAX_RETRIES = 3
   for attempt in range(MAX_RETRIES):
       last_error = f"attempt {attempt} failed"
   print(attempt, last_error)   # 2 attempt 2 failed (no block scope)
   ```

3. **None replaces both null and undefined.** There is one "no value" object, `None`, and a function without `return` returns it. A missing dict key raises `KeyError` and a missing attribute raises `AttributeError` instead of quietly giving `undefined`, so you ask for a fallback explicitly. There is no `?.`; use `.get()` or a check.

   ```python
   user = {"name": "Ada"}
   user.get("email")              # None
   user.get("email", "n/a")       # 'n/a'
   user["email"]                  # KeyError: 'email'
   if user.get("email") is None:  # compare to None with `is`
       print("no email")
   ```

4. **Truthiness has different edges.** Falsy values are `None`, `False`, `0`, `0.0`, `""` and every empty container: `[]`, `{}`, `set()`, `()`. In JavaScript `[]` and `{}` are truthy, so `if (items.length)` becomes `if items:`. Any non-empty string is truthy in both languages, including `"0"` and `"false"`, which matters because environment variables and query strings always arrive as strings. One more edge: `float("nan")` is truthy in Python but `NaN` is falsy in JavaScript.

   ```python
   bool([]), bool({}), bool(""), bool(0)   # (False, False, False, False)
   bool("0"), bool("false"), bool([0])     # (True, True, True)
   items: list[str] = []
   if not items:
       print("empty")                      # runs: an empty list is falsy
   ```

5. **`==` never coerces, so there is no `===`.** `==` compares values: `1 == "1"` is False, and lists and dicts compare by content, so `[1, 2] == [1, 2]` is True (two JavaScript arrays are never `===`). `is` checks identity, whether two names point at the same object; use it for `None` and sentinels, never for numbers or strings. Two quirks: `1 == 1.0` is True, and `True == 1` is True because `bool` is a subclass of `int`.

   ```python
   a = [1, 2]
   b = [1, 2]
   a == b        # True: same contents
   a is b        # False: two separate list objects
   1 == "1"      # False: no type coercion
   x = None
   x is None     # True: the idiomatic None check
   ```

6. **No `++` or `--`.** Write `count += 1`. `count++` is a SyntaxError, and `++count` is worse: it parses as two unary plus signs, runs, and changes nothing.

   ```python
   count = 0
   count += 1
   ++count       # valid, does nothing: count is still 1
   ```

7. **Integers are exact and division is explicit.** `int` has arbitrary precision, so there is no `Number.MAX_SAFE_INTEGER` and no BigInt. `/` always returns a float, `//` is floor division, and `%` takes the sign of the divisor, so negative numbers behave differently from JavaScript.

   ```python
   2 ** 100          # 1267650600228229401496703205376, exact
   7 / 2, 7 // 2     # (3.5, 3)
   -7 // 2, -7 % 2   # (-4, 1); in JavaScript -7 % 2 is -1
   ```

8. **f-strings replace template literals.** Prefix the string with `f` and use `{}`. A format spec goes after a colon, and `{x=}` prints the expression and its value for debugging. Single and double quotes are equivalent, triple quotes make multi-line strings, and since 3.12 an f-string may reuse its own quote character inside the braces. `+` between a string and a number raises TypeError instead of coercing.

   ```python
   name, total = "Ada", 1234.5
   f"Hi {name}, you owe {total:,.2f}"   # 'Hi Ada, you owe 1,234.50'
   f"{total=}"                          # 'total=1234.5'
   "age: " + 5                          # TypeError: can only concatenate str (not "int") to str
   "age: " + str(5)                     # 'age: 5'
   ```

### Walkthrough: collections, loops, functions and classes
1. **`list` is your array.** `append` instead of `push`, `len(items)` instead of `.length`, negative indexes count from the end, and slices copy a range. Reading past the end raises `IndexError` rather than returning `undefined`.

   ```python
   items = [10, 20, 30]
   items.append(40)          # push
   len(items)                # 4
   items[-1], items[1:3]     # (40, [20, 30])
   items[10]                 # IndexError: list index out of range
   ```

2. **`dict` is your object, and your Map.** Keys can be any hashable value, not only strings. You read with `d["key"]`, never `d.key`, insertion order is guaranteed (3.7+), and `in` checks keys. JSON objects decode to dicts and JSON arrays to lists, which is exactly what `response.json()` gives you from an HTTP client.

   ```python
   user = {"id": 7, "name": "Ada"}
   user["name"]              # 'Ada' (user.name raises AttributeError)
   "email" in user           # False: `in` checks keys
   user["email"] = "ada@example.com"
   for key, value in user.items():
       print(key, value)
   ```

3. **Loops iterate values.** `for x in items` is JavaScript's `for...of`. There is no C-style `for (let i = 0; ...)`: use `range()`, or `enumerate()` when you need the index too. Looping over a dict gives its keys. Comprehensions replace most `map` and `filter` chains.

   ```python
   for i, name in enumerate(["ada", "bob"]):   # arr.forEach((name, i) => ...)
       print(i, name)
   for n in range(0, 10, 2):                   # 0, 2, 4, 6, 8
       print(n)
   squares = [n * n for n in range(5) if n % 2 == 0]   # [0, 4, 16]
   ```

4. **Unpacking replaces destructuring.** Unpacking is positional and works on any iterable; `*name` collects the rest into a list. Swapping needs no temporary. There is no `const { name, age } = user` for dicts: read the keys explicitly (or use `match` with a mapping pattern, 3.10+, covered later).

   ```python
   first, *rest = [1, 2, 3, 4]    # first=1, rest=[2, 3, 4]
   a, b = 1, 2
   a, b = b, a                    # swap: a=2, b=1
   row = {"name": "Ada", "age": 36}
   name, age = row["name"], row["age"]   # no key-based destructuring
   ```

5. **`*` and `**` replace spread and rest.** `[*a, *b]` and `{**a, **b}` build new collections (3.9+ also has `a | b` for dicts). In a signature, `*args` collects extra positional arguments into a tuple and `**kwargs` collects extra keyword arguments into a dict. Python has real keyword arguments, so the JavaScript "options object" becomes named parameters, and parameters after a bare `*` are keyword-only.

   ```python
   defaults = {"model": "small", "temperature": 0.2}
   config = {**defaults, "temperature": 0}     # {...defaults, temperature: 0}

   def log(msg: str, *args: object, level: str = "info", **extra: object) -> None:
       print(level, msg, args, extra)

   log("hi", 1, 2, level="warn", user_id=7)    # warn hi (1, 2) {'user_id': 7}
   ```

6. **`lambda` is not an arrow function.** A lambda is a single expression: no statements, no `await`, no annotations. It is fine as a `key=` argument; for anything longer write a nested `def`, which closes over outer variables like a JavaScript closure. Two closure rules differ: assigning to an outer variable needs `nonlocal`, and default values are evaluated once, when `def` runs, so a mutable default is shared by every call (JavaScript re-evaluates defaults on each call).

   ```python
   users = [{"name": "bob", "age": 31}, {"name": "ada", "age": 36}]
   by_age = sorted(users, key=lambda u: u["age"])

   def add_tag(tag: str, tags: list[str] = []) -> list[str]:   # bug: one shared list
       tags.append(tag)
       return tags

   add_tag("a")
   add_tag("b")      # ['a', 'b']: the default list remembered the first call
   ```

7. **Classes take an explicit `self`.** `__init__` is the constructor, there is no `new`, and every method receives the instance as its first parameter, named `self` by convention. Attributes are created by assigning to `self.x`; there are no field declarations and no enforced `private` (a leading underscore is the convention). `obj.method` returns a bound method that carries `self`, so the JavaScript lost-`this` bug and `.bind(this)` do not exist.

   ```python
   class Account:
       def __init__(self, owner: str, balance: float = 0.0) -> None:
           self.owner = owner
           self.balance = balance

       def deposit(self, amount: float) -> None:
           self.balance += amount

   acct = Account("Ada")     # no `new`
   pay = acct.deposit        # bound method: self travels with it
   pay(50)
   acct.balance              # 50.0
   ```

8. **Errors are raised, not returned as odd values.** Where JavaScript gives `undefined` or `NaN`, Python raises an exception, and idiomatic code catches the specific type with `try`/`except` (`raise` is `throw`). `parseInt("80a0")` returns 80; `int("80a0")` refuses.

   ```python
   raw = "80a0"
   try:
       port = int(raw)       # ValueError: invalid literal for int() with base 10: '80a0'
   except ValueError:
       port = 8000           # catch the specific type, never a bare `except:`
   ```

### Walkthrough: modules, packages, environments and async
1. **A file is a module.** Every top-level name in a `.py` file is importable; there is no `export` keyword, and a leading underscore marks a name as internal by convention. A module's code runs once, on first import, and is then cached in `sys.modules`, like Node's require cache.

   ```python
   # app/utils.py
   def slugify(text: str) -> str:
       return text.strip().lower().replace(" ", "-")

   # app/main.py
   from app.utils import slugify      # import { slugify } from "./utils.js"
   import app.utils as utils          # import * as utils from "./utils.js"
   ```

2. **Imports resolve from `sys.path`, not from the importing file.** A folder of modules is a package (an `__init__.py` makes it a regular package). `import app.utils` searches the directories on `sys.path`: first the folder of the script you ran (or the current directory with `python -m`), then the installed packages. Prefer absolute imports from the project root and run code as a module; relative imports such as `from .utils import slugify` only work inside a package.

   ```bash
   python3 -m app.main     # project root on sys.path: `import app` works
   python3 app/main.py     # app/ on sys.path instead: `import app` fails
   ```

3. **pip and uv replace npm.** Packages come from PyPI. `pip` installs into whichever Python runs it, globally unless an environment is active, so modern projects use uv, one fast tool that manages the Python version, the environment, installs and the lockfile. `pyproject.toml` plays the role of `package.json`, and `uv.lock` the role of `package-lock.json`.

   ```bash
   uv init my-api              # npm init -y
   uv add fastapi              # npm install express
   uv add --dev pytest         # npm install -D jest
   uv run pytest               # npx jest
   uv sync --locked            # npm ci
   ```

4. **A virtual environment replaces `node_modules`.** A venv is a folder (`.venv`) holding a link to a Python interpreter plus its own `site-packages`. Unlike `node_modules` it is flat: one version of each package per environment, so conflicting requirements must be resolved instead of nested. Use one venv per project and never commit it; `uv run` uses it automatically, or you activate it yourself.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # puts .venv/bin first on PATH
   which python                # .../my-api/.venv/bin/python
   ```

5. **Type hints are TypeScript without a compiler.** Annotations such as `def f(x: int) -> str` are not checked when the code runs; a checker (mypy or pyright) reads them, like `tsc --noEmit`. Some libraries do use them at runtime: FastAPI and Pydantic read your hints to validate requests and build the OpenAPI schema.

   ```python
   def double(x: int) -> int:
       return x * 2

   double("ab")    # 'abab': runs fine; only a type checker reports the wrong argument
   ```

6. **Coroutines are lazier than promises.** Calling an `async def` function returns a coroutine object and runs nothing until it is awaited or scheduled as a task, whereas a JavaScript promise starts work the moment it is created. Python also has no always-on event loop: `asyncio.run(main())` starts one, and FastAPI's server (uvicorn) runs one for you. `asyncio.gather` is `Promise.all`, and a blocking call such as `time.sleep` or `requests.get` inside `async def` freezes the whole loop. The async lessons later in this tab go deep.

   ```python
   import asyncio

   async def fetch_user(uid: int) -> dict:
       await asyncio.sleep(0.1)          # stands in for a network call
       return {"id": uid}

   async def main() -> None:
       users = await asyncio.gather(fetch_user(1), fetch_user(2))   # Promise.all
       print(users)                      # [{'id': 1}, {'id': 2}]

   asyncio.run(main())
   ```

### Concepts you must understand
- Indentation is syntax: a colon opens a block and every line in the block shares one indent, 4 spaces by convention.
- Python is dynamically but strongly typed: it never coerces between str and int, so mixing them raises TypeError instead of producing `"51"`.
- `None` is the only null value; a missing dict key raises KeyError and a missing attribute raises AttributeError, so use `.get()` or check first.
- Falsy values are None, False, zero, and empty strings and containers; `"0"` and `"false"` are truthy, which matters for env vars and query params.
- `==` compares values (deeply for lists and dicts), `is` compares identity, and `is` is for `None` and sentinels only.
- Variables are function-scoped, not block-scoped: a name assigned in an `if` or `for` body is still visible after it.
- Default argument values are evaluated once, when the `def` runs, so never use a mutable default.
- A module is a file, imports are cached in `sys.modules`, and anything not prefixed with an underscore is meant to be importable.
- Each project gets its own virtual environment; uv manages it plus the lockfile, as npm does with `node_modules` and `package-lock.json`.
- A coroutine does nothing until awaited or wrapped in a task, and an event loop must be running (`asyncio.run` or the server's).

| JavaScript | Python | Note |
| --- | --- | --- |
| `null`, `undefined` | `None` | Missing keys raise KeyError instead of giving undefined |
| `a === b` | `a == b` | No coercion; lists and dicts compare by content |
| `i++` | `i += 1` | `++i` is legal and silently does nothing |
| `Math.floor(7 / 2)` | `7 // 2` | `/` always returns a float; ints never overflow |
| `` `Hi ${name}` `` | `f"Hi {name}"` | Format specs: `{x:.2f}`, `{n:,}`, `{x=}` |
| `for (const x of arr)` | `for x in items:` | `enumerate(items)` when you also need the index |
| `const [first, ...rest] = arr` | `first, *rest = items` | Positional only; no key-based object destructuring |
| `{...defaults, ...opts}` | `{**defaults, **opts}` | Shallow, like spread; later keys win |
| `(x) => x * 2` | `lambda x: x * 2` | One expression only; use `def` for anything else |
| `this` | `self` | Explicit first parameter; bound methods keep it |
| `npm install express`, `node_modules/` | `uv add fastapi`, `.venv/` | One flat environment per project |
| `Promise.all([a(), b()])` | `await asyncio.gather(a(), b())` | Coroutines do not start until awaited or scheduled |

### Q. Rewrite this JavaScript filter-and-map chain over a list of users in idiomatic Python.
**Short answer (45 seconds):** Use a list comprehension: the `if` clause is the filter and the leading expression is the map. Read the flag with `u.get("active")`, so a user without the key counts as inactive instead of raising KeyError, and return a new list.

**Deeper explanation:**

```js
const activeNames = (users) =>
  users.filter((u) => u.active).map((u) => u.name.toUpperCase());
```

```python
def active_names(users: list[dict]) -> list[str]:
    return [u["name"].upper() for u in users if u.get("active")]

active_names([{"name": "ada", "active": True}, {"name": "bob"}])   # ['ADA']
```

Read a comprehension as "give me this expression, for each `u` in `users`, if the condition holds". It makes one pass and builds one list, where the JavaScript chain builds an intermediate array first. The condition uses truthiness exactly like `.filter`, so `active: 1` counts and `active: None` does not. `u.get("active")` matters: in JavaScript a missing property is `undefined` and falsy, but `u["active"]` raises KeyError in Python. `u["name"]` is deliberately strict, because a user without a name is a data bug you want to surface, not hide. Time is O(n) and extra space is O(k) for k matches.

`map()` and `filter()` exist in Python too, but they return lazy iterators and need a `lambda` each, so `list(map(lambda u: u["name"].upper(), filter(lambda u: u.get("active"), users)))` is longer and harder to read. Comprehensions are the idiom.

**Follow-ups they will ask:**
- What if there are a million users and you only stream the names to a file?: Use a generator expression, `(u["name"].upper() for u in users if u.get("active"))`, which yields one name at a time without building a list.
- How do you build a dict of id to name instead?: A dict comprehension, `{u["id"]: u["name"] for u in users if u.get("active")}`.
- What if active must be exactly True, not merely truthy?: Write `if u.get("active") is True`.

**Mistakes to avoid:**
- Writing `u.active` (AttributeError on a dict) or `u["active"]` (KeyError when the key is missing).
- Looping with `for i in range(len(users))` and indexing, when `for u in users` or a comprehension says it directly.

### Q. Predict the output of this code about truthiness, equality and integer division, and explain each value.
**Short answer (45 seconds):** Line one prints `['0', 'false', [0]]`, because only None, zero, and empty strings and containers are falsy. Line two prints `False True True True False -4 1`: no str-to-int coercion, int and float compare by value, `bool` is an `int`, lists compare by content but are two separate objects, and floor division rounds toward negative infinity.

**Deeper explanation:**

```python
values = [0, "0", "", [], {}, None, "false", [0]]
print([v for v in values if v])
print(1 == "1", 1 == 1.0, True == 1, [1, 2] == [1, 2], [1, 2] is [1, 2], -7 // 2, -7 % 2)
```

```text
['0', 'false', [0]]
False True True True False -4 1
```

Line one: `0`, `""`, `[]`, `{}` and `None` are falsy. `"0"` and `"false"` are non-empty strings, so they are truthy; a string's truthiness depends only on its length. `[0]` is a list with one item, so it is truthy even though the item is falsy. In JavaScript `[]` and `{}` would also survive the filter, because every object is truthy there.

Line two, value by value:
- `1 == "1"` is False: Python's `==` never converts types (JavaScript's `1 == "1"` is true).
- `1 == 1.0` is True: numeric types compare by value across int and float.
- `True == 1` is True: `bool` subclasses `int`, and `True` is the integer 1.
- `[1, 2] == [1, 2]` is True: lists compare element by element.
- `[1, 2] is [1, 2]` is False: two list displays create two objects.
- `-7 // 2` is -4 and `-7 % 2` is 1: floor division rounds down, and the remainder takes the divisor's sign, so `(a // b) * b + a % b == a` always holds. JavaScript's `-7 % 2` is -1.

**Follow-ups they will ask:**
- Why is `"0"` truthy when it looks like zero?: Truthiness of a string is "is it non-empty"; convert first with `int(value)` or parse it as a flag.
- When is `is` the right operator?: For singletons such as `None` and sentinel objects made with `object()`. CPython caches small ints (-5 to 256), so `is` on numbers can look right in a quick test and fail on larger values.
- What does `-7 / 2` give?: `-3.5`; `int(-3.5)` truncates to -3, while `-7 // 2` floors to -4.

**Mistakes to avoid:**
- Claiming Python has `===` or that `==` coerces like JavaScript's.
- Using `is` to compare numbers or strings.

### Q. A feature flag stays on in production even though the environment says DEBUG=false. Find and fix the bug.
**Short answer (45 seconds):** Environment variables are always strings, and every non-empty string is truthy, so `bool(os.environ.get("DEBUG"))` is True for `"false"` and `"0"`. Parse the value explicitly against known spellings, return a default when it is unset, and raise on anything unrecognised so a typo fails at startup.

**Deeper explanation:**

```python
import os

DEBUG = bool(os.environ.get("DEBUG"))   # bug: bool("false") is True
```

```python
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}

def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:                   # variable not set at all
        return default
    text = value.strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    raise ValueError(f"not a boolean: {value!r}")

DEBUG = parse_bool(os.environ.get("DEBUG"))
```

`os.environ.get` returns `str | None`: None when the variable is missing, a string otherwise. `bool()` of a string only asks whether it is empty, so `"false"`, `"0"` and `"no"` all become True. The fix normalises case and whitespace, accepts a fixed set of spellings, and treats an empty value as False. `{value!r}` inserts the `repr()`, so the error shows the quotes and any stray spaces. Set membership (`in _TRUE`) is O(1).

The same trap exists in Node (`process.env.DEBUG` is a string too), but JavaScript engineers usually write `=== "true"`; the Python habit of `if os.environ.get(...)` hides it. In a FastAPI service you would normally declare `debug: bool = False` on a pydantic-settings class, which parses common spellings such as `true`, `1`, `yes` and `on` for you.

**Follow-ups they will ask:**
- Why raise on unknown values instead of returning False?: A typo such as `DEBUG=ture` should fail loudly at startup, not silently pick a behaviour.
- Where should this parsing live?: Once, at startup, in a settings object, not as scattered `os.environ` reads across the codebase.
- How do you test code that reads `os.environ` directly?: pytest's `monkeypatch.setenv("DEBUG", "false")`, which is undone after the test.

**Mistakes to avoid:**
- `if os.environ["DEBUG"]:`, which is truthy for `"false"` and raises KeyError when the variable is unset.
- Comparing against one spelling only (`== "true"`), which breaks on `"True"` or `"1"`.

### Q. Rewrite this JavaScript settings merge, which uses spread and skips null overrides, in idiomatic Python.
**Short answer (45 seconds):** Build a new dict with `{**defaults, **clean}`, where `clean` is a dict comprehension over `overrides.items()` that keeps values that are `is not None`. Later keys win, exactly like spread, and neither input is mutated.

**Deeper explanation:**

```js
function mergeSettings(defaults, overrides) {
  const clean = Object.fromEntries(
    Object.entries(overrides).filter(([, v]) => v != null)
  );
  return { ...defaults, ...clean };
}
```

```python
def merge_settings(defaults: dict, overrides: dict) -> dict:
    clean = {k: v for k, v in overrides.items() if v is not None}
    return {**defaults, **clean}

merge_settings({"model": "small", "temperature": 0.2}, {"temperature": 0, "model": None})
# {'model': 'small', 'temperature': 0}
```

Each JavaScript piece has a direct Python counterpart: `Object.entries` is `.items()`, which yields key and value pairs; `filter` plus `Object.fromEntries` is a dict comprehension; spread is `**` inside a dict display. On Python 3.9+ you can also write `defaults | clean`.

The important detail is `is not None`. Writing `if v` would drop `temperature: 0`, an empty string or `False`, which is the classic `||` versus `??` bug. The merge is shallow: a nested dict such as `{"llm": {"model": ...}}` in `overrides` replaces the whole nested dict from `defaults`, exactly as spread would. Time is O(len(defaults) + len(overrides)).

The more Pythonic API often skips the overrides dict entirely and uses keyword arguments: `def build_config(**overrides)` called as `build_config(temperature=0)`.

**Follow-ups they will ask:**
- How do you merge nested settings?: A small recursive function that merges when both values are dicts and replaces otherwise, because `**` is shallow.
- How do you update a dict in place?: `settings.update(clean)` or `settings |= clean` (3.9+), but never on a shared defaults dict.
- What if callers pass unknown keys?: Validate against the known keys, or use a Pydantic model so typos fail with a clear error.

**Mistakes to avoid:**
- Filtering with `if v`, which silently drops 0, False and empty strings.
- Calling `defaults.update(overrides)` on a module-level defaults dict, which changes the defaults for every later caller.

### Q. This helper returns tags from earlier calls when it is called with one argument. Find and fix the bug.
**Short answer (45 seconds):** The default `[]` is created once, when the `def` statement runs, and every call that omits `tags` appends to that same list. Use `None` as the default and create a fresh list inside the function.

**Deeper explanation:**

```python
def add_tag(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag)
    return tags

add_tag("urgent")    # ['urgent']
add_tag("billing")   # ['urgent', 'billing'], expected ['billing']
```

Python evaluates default values once and stores them on the function object (you can see the shared list in `add_tag.__defaults__`). JavaScript evaluates default parameters on every call, which is why this bug feels impossible to a JavaScript engineer. In a long-running FastAPI process the shared list lives for days, so one request's tags leak into another user's response.

```python
def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []          # a fresh list on every call
    tags.append(tag)
    return tags
```

`list[str] | None` needs Python 3.10+ (older code writes `Optional[list[str]]`). Immutable defaults such as `0`, `""`, `None` or a tuple are safe because they cannot be changed in place. Ruff flags the bug with rule B006 (enable the `B` family). Dataclasses refuse a list default and make you write `field(default_factory=list)`, and Pydantic models copy a mutable default for each instance, so `tags: list[str] = []` is safe inside a Pydantic model but not in a plain function.

**Follow-ups they will ask:**
- Does the same bug hit dicts and sets?: Yes, any mutable default, including an instance of your own class.
- What about a mutable class attribute, `items = []` in a class body?: Same trap: it is shared by every instance; create it in `__init__`.
- How do you catch this before review?: Ruff's bugbear rules (B006) in CI.

**Mistakes to avoid:**
- "Fixing" it with `tags = tags or []`: a caller who passes their own empty list gets a different list back, and their list never receives the tag.
- Assuming the bug only matters in tests: in a server process it is cross-request shared state.

### Q. Rewrite this JavaScript cart class in Python so its add method still works when passed around as a callback.
**Short answer (45 seconds):** Use `__init__` to create the per-instance dicts, give every method an explicit `self`, replace `??` with `dict.get(key, 0)` and `setdefault`, and turn the getter into an `@property`. The callback problem disappears because `cart.add` is a bound method that carries its instance.

**Deeper explanation:**

```js
class Cart {
  #items = new Map(); // name -> { price, qty }
  add(name, price, qty = 1) {
    const item = this.#items.get(name) ?? { price, qty: 0 };
    item.qty += qty;
    this.#items.set(name, item);
  }
  get count() { let n = 0; for (const i of this.#items.values()) n += i.qty; return n; }
}
const cart = new Cart();
bus.on("add", cart.add); // breaks: `this` is undefined inside add
```

```python
class Cart:
    def __init__(self) -> None:
        self._prices: dict[str, float] = {}
        self._qty: dict[str, int] = {}

    def add(self, name: str, price: float, qty: int = 1) -> None:
        if qty < 1 or price < 0:
            raise ValueError("qty must be >= 1 and price >= 0")
        self._prices.setdefault(name, price)        # keep the first price
        self._qty[name] = self._qty.get(name, 0) + qty

    def total(self) -> float:
        return sum(self._prices[n] * q for n, q in self._qty.items())

    @property
    def count(self) -> int:
        return sum(self._qty.values())

cart = Cart()
handler = cart.add            # bound method
handler("pen", 2.5, qty=2)
cart.total(), cart.count      # (5.0, 2)
```

Attributes exist once `__init__` assigns them. The leading underscore is a convention for "internal"; JavaScript's `#` is enforced, Python has nothing equivalent (a double underscore only mangles the name). `@property` makes `cart.count` read like a field while computing on access.

**Follow-ups they will ask:**
- How would a dataclass help?: `@dataclass class LineItem: price: float; qty: int = 1` generates `__init__`, `__repr__` and `__eq__`; keep a `dict[str, LineItem]`.
- What does `print(cart)` show?: The default repr with a memory address, until you define `__repr__`.
- Should money be a float here?: Not for real payments; use `Decimal` or integer cents (lesson 3).

**Mistakes to avoid:**
- Forgetting `self` in a method, which fails with "takes 2 positional arguments but 3 were given".
- Putting `_qty = {}` in the class body, which shares one dict across every cart.

### Practice
- Practice kit: open `python-practice/exercises/p01_js_to_python.py`, implement each function, then run `uv run --with pytest pytest tests/test_p01_js_to_python.py` from the `python-practice` folder.
- In the REPL, evaluate `bool("false")`, `[] == False`, `not []`, `-7 // 2`, `-7 % 2` and `2 ** 64`, and say out loud how JavaScript would answer each one.
- In the REPL, define `def f(x, acc=[]): acc.append(x); return acc`, call it three times, then print `f.__defaults__` and explain what you see.
- Translate a 20-line Node.js utility you wrote recently into Python without looking anything up, then fix each error the interpreter gives you.

## Setup, Running Code & Tooling [Basics]

> The toolbox around the code: installing Python, the REPL, running scripts and modules, virtual environments, dependencies, formatting, linting, type checking, project layout and tracebacks. In real FastAPI and AI backend repos this is the first thing you touch: `pyproject.toml` and `uv.lock` define the service, the Dockerfile runs `uv sync`, CI runs ruff, mypy and pytest, and every incident starts with reading a traceback.

### Why it exists
Python predates per-project dependency folders: `pip install` puts packages into whichever interpreter runs it, so two projects on one machine fight over versions, and a stray install can break the operating system's own Python. Virtual environments give each project a private set of packages, `pyproject.toml` standardised the project file (like `package.json`), and lockfiles pin exact versions. uv bundles interpreter installs, environments, dependency resolution and locking into one fast tool. The cost is more moving parts than npm: most "works on my machine" bugs in Python come from running a different interpreter or environment than you think.

### In plain words
Think of each project as a workshop. The virtual environment is that workshop's own toolbox, so tools bought for one project never get mixed into another. `pyproject.toml` is the shopping list, `uv.lock` is the receipt that records the exact versions bought, and uv is the assistant who reads the list, buys everything and keeps the receipt up to date. Ruff keeps the workshop tidy, mypy checks that parts fit before you assemble them, and a traceback is the incident report when something breaks.

### Walkthrough: install Python and run your first script
1. **Install an interpreter.** On a Mac you have three good options: the python.org installer, Homebrew (`brew install python@3.12`), or a version manager. pyenv builds and switches versions per folder through a `.python-version` file; uv can install and pin versions the same way and is faster. On macOS type `python3`, since a bare `python` may not exist outside a virtual environment.

   ```bash
   uv python install 3.12      # download a managed CPython
   uv python pin 3.12          # writes .python-version (like .nvmrc)
   uv run python --version     # Python 3.12.x
   ```

2. **Use the REPL.** `python3` (or `uv run python` inside a project) opens an interactive prompt, like running `node` with no arguments. `help()` and `dir()` explore any object, `_` holds the last result, and `python3 -i script.py` runs a script and then leaves you at the prompt with its variables loaded. Python 3.13+ ships a friendlier REPL with colour and multi-line editing.

   ```python
   nums = [3, 1, 2]
   sorted(nums)          # [1, 2, 3]; nums is unchanged
   dir(nums)[-5:]        # ['insert', 'pop', 'remove', 'reverse', 'sort']
   help(str.split)       # docs for one method; press q to leave
   ```

3. **Run scripts and modules.** `python3 hello.py` runs a file. `python3 -m package.module` runs a module by its import name with the current directory on `sys.path`; that is how you run tools inside an environment (`python3 -m venv`, `python3 -m pytest`, `python3 -m pip`) and your own packages (`python3 -m app.main`). `python3 -c "..."` runs a one-liner, like `node -e`.

   ```bash
   python3 hello.py
   python3 -m app.main
   python3 -c "import sys; print(sys.version)"
   ```

4. **Guard the entry point with `__name__`.** Every module has a `__name__`: it is `"__main__"` when the file is run directly, and its import name (for example `"app.main"`) when it is imported. Putting the start-up call behind this check means importing the module, from a test or another module, does not run the program. It is Node's `require.main === module`. Return an exit code from `main()` and hand it to `SystemExit`.

   ```python
   import sys

   def main(argv: list[str] | None = None) -> int:
       args = sys.argv[1:] if argv is None else argv
       print(f"args: {args}")
       return 0                      # 0 means success, like process.exit(0)

   if __name__ == "__main__":
       raise SystemExit(main())      # same effect as sys.exit(main())
   ```

5. **Read command-line arguments.** `sys.argv` is a list whose first item is the script path (Node's `process.argv` has the node binary first, then the script). For real CLIs use `argparse` from the standard library, or Typer if you like FastAPI-style type hints.

   ```python
   import argparse

   parser = argparse.ArgumentParser(prog="greet")
   parser.add_argument("--name", default="there")
   parser.add_argument("--shout", action="store_true")
   args = parser.parse_args(["--name", "Ada"])   # omit the list to read sys.argv
   print(args.name, args.shout)                  # Ada False
   ```

6. **Read tracebacks from the bottom.** The last line is the exception type and message. Above it, frames are listed oldest first with the most recent call last (a JavaScript stack trace puts the newest frame first), so the frame just above the message is where it failed, and the lowest frame in your own code is usually where to fix it. Python 3.11+ adds `^` markers under the exact expression that failed.

   ```text
   Traceback (most recent call last):
     File "/srv/app/main.py", line 11, in <module>
       raise SystemExit(main())
                        ^^^^^^
     File "/srv/app/main.py", line 5, in main
       settings = load_settings()
                  ^^^^^^^^^^^^^^^
     File "/srv/app/settings.py", line 6, in load_settings
       "port": int(os.environ.get("PORT", "8000")),
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   ValueError: invalid literal for int() with base 10: ''
   ```

### Walkthrough: a project with uv, virtual environments and dependencies
1. **Create the project.** `uv init` writes `pyproject.toml`, `.python-version`, a README and starter code. `uv init --package` uses the src layout and adds a build backend, which is what you want for a service you will install and test.

   ```bash
   uv init --package my-api
   cd my-api
   ```

2. **Add dependencies.** `uv add` updates `pyproject.toml`, resolves every version, writes `uv.lock` and installs into `.venv`, creating it if needed. Dev-only tools go into a dependency group with `--dev`. An extra in square brackets pulls optional parts of a package; `uvicorn[standard]` adds speedups such as uvloop and httptools.

   ```bash
   uv add fastapi "uvicorn[standard]"
   uv add --dev pytest ruff mypy
   ```

3. **Read `pyproject.toml`.** It is the `package.json` of Python: metadata, the supported Python range, runtime dependencies as version ranges, dependency groups, and tool settings under `[tool.*]` tables. The lockfile pins the exact resolved versions. Commit both; never commit `.venv`.

   ```toml
   [project]
   name = "my-api"
   version = "0.1.0"
   requires-python = ">=3.12"
   dependencies = [
       "fastapi>=0.115",
       "uvicorn[standard]>=0.30",
   ]

   [dependency-groups]
   dev = ["pytest>=8", "ruff>=0.6", "mypy>=1.11"]
   ```

4. **Run everything through the environment.** `uv run <command>` makes sure `.venv` matches the lock (syncing it if not) and then runs the command inside it, so you rarely activate anything. `uv sync` installs exactly what the lock says; in CI and Docker use `uv sync --locked`, which fails if `pyproject.toml` and `uv.lock` disagree. `uvx ruff` (short for `uv tool run ruff`) runs a tool in a throwaway environment, like `npx`.

   ```bash
   uv run uvicorn my_api.main:app --reload    # dev server
   uv run pytest -q
   uv sync --locked                           # CI: exact versions or fail
   ```

5. **Know the classic venv and pip flow.** Many repos and Dockerfiles still use the standard library's `venv`, `pip` and a `requirements.txt` (a flat list of pinned versions, the oldest lockfile format). Activating a venv only puts its `bin` folder first on `PATH`; `which python` tells you which interpreter you are really running. `uv pip install` is a faster drop-in for `pip install`.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip freeze > requirements.txt      # snapshot the installed versions
   deactivate
   ```

6. **Never install into the system Python.** Homebrew's Python and many Linux distributions refuse global installs with `error: externally-managed-environment` (PEP 668). Do not reach for `sudo pip` or `--break-system-packages`. Use a project venv, or `uv tool install` (or pipx) for command-line tools you want everywhere, the equivalent of `npm install -g`.

   ```bash
   uv tool install ruff      # global CLI in its own isolated environment
   ruff --version
   ```

### Walkthrough: format, lint, type-check and lay out the project
1. **Format with ruff.** `ruff format` is a Black-compatible formatter, the Prettier of Python: it settles style so code review does not have to. Run it on save in your editor and as a check in CI.

   ```bash
   uv run ruff format .            # rewrite files
   uv run ruff format --check .    # CI: fail if anything would change
   ```

2. **Lint with ruff.** `ruff check` replaces flake8, isort, pyupgrade and many plugins with one fast tool, the ESLint of Python. Choose rule families in `pyproject.toml`: E (pycodestyle errors), F (pyflakes: unused imports, undefined names), I (import sorting), B (bugbear: likely bugs such as mutable defaults), UP (pyupgrade: modern syntax). Then run `uv run ruff check . --fix`.

   ```toml
   [tool.ruff]
   line-length = 100

   [tool.ruff.lint]
   select = ["E", "F", "I", "B", "UP"]
   ```

3. **Type-check with mypy or pyright.** Hints do nothing at runtime, so a checker is what makes them useful, like `tsc --noEmit`. mypy is the original; pyright is faster and powers VS Code's Pylance. Start lenient and tighten towards `--strict` as coverage grows.

   ```python
   def total(prices: list[float]) -> float:
       return sum(prices)

   total(["9.99"])
   # mypy: error: List item 0 has incompatible type "str"; expected "float"  [list-item]
   ```

4. **Use the src layout.** Put the importable package under `src/` and the tests beside it. Python puts the script's folder or the current directory on `sys.path`, so with a flat layout your tests can import the local folder by accident instead of the installed package, and pass while the built package is broken. The distribution name may use dashes (`my-api`), but the import name must use underscores (`my_api`).

   ```text
   my-api/
     pyproject.toml
     uv.lock
     .python-version
     src/
       my_api/
         __init__.py
         main.py
         routes/
           __init__.py
           users.py
     tests/
       test_users.py
   ```

5. **Test with pytest.** pytest collects files named `test_*.py` and functions named `test_*`, and uses the plain `assert` statement with a readable diff on failure. Built-in fixtures such as `tmp_path`, `monkeypatch` and `capsys` replace most Jest setup and mocking helpers.

   ```python
   # tests/test_users.py
   from my_api.main import slugify

   def test_slugify() -> None:
       assert slugify(" Hello World ") == "hello-world"
   ```

6. **Wire it into CI.** One script runs the same checks on every machine, so a red build always means a real problem.

   ```bash
   uv sync --locked
   uv run ruff format --check .
   uv run ruff check .
   uv run mypy src
   uv run pytest -q
   ```

### Concepts you must understand
- `python3 file.py` puts the file's folder on `sys.path`; `python3 -m pkg.module` puts the current directory there and runs the module by its import name.
- `if __name__ == "__main__":` separates "run as a program" from "imported as a library", so an import never triggers side effects.
- A virtual environment is a folder with its own interpreter link and `site-packages`; activating it only changes `PATH`.
- `pyproject.toml` declares dependencies as ranges, `uv.lock` pins the exact resolved versions, and both are committed.
- `uv run` keeps `.venv` in sync with the lock before every command; `uv sync --locked` is the reproducible install for CI and Docker.
- Never install packages into the system Python; use a venv per project, and `uv tool install` or pipx for global CLIs.
- Ruff formats (`ruff format`) and lints (`ruff check`) from one config in `pyproject.toml`.
- Type hints are ignored at runtime; mypy or pyright enforce them, and FastAPI and Pydantic read them to validate data.
- A traceback prints the most recent call last: read the last line first, then walk up to the nearest frame in your own code.

| JavaScript | Python | Note |
| --- | --- | --- |
| nvm, `.nvmrc` | `uv python install`, pyenv, `.python-version` | Pin the interpreter per project |
| `node` (REPL) | `python3` or `uv run python` | `help()`, `dir()`, `_` for the last result |
| `package.json` | `pyproject.toml` | Dependencies as ranges plus `[tool.*]` settings |
| `package-lock.json` | `uv.lock` or a pinned `requirements.txt` | Commit it |
| `node_modules/` | `.venv/` | Flat, one version per package; never commit it |
| `npm install pkg` | `uv add pkg` | Or `pip install pkg` inside an active venv |
| `npm ci` | `uv sync --locked` | Fails if the lock is stale |
| `npx tool`, `npm install -g tool` | `uvx tool`, `uv tool install tool` | Tools get isolated environments |
| Prettier, ESLint | `ruff format`, `ruff check` | One tool, one config |
| `tsc --noEmit` | `mypy` or `pyright` | Hints are not enforced at runtime |
| Jest | pytest | Plain `assert`; fixtures instead of `beforeEach` |
| `require.main === module`, `process.argv` | `if __name__ == "__main__":`, `sys.argv` | `argv[0]` is the script, not the runtime |

### Q. Write a main() for a small CLI script so that importing the module never runs it and the shell sees a proper exit code.
**Short answer (45 seconds):** Put the logic in `main(argv: list[str] | None = None) -> int`, read `sys.argv[1:]` only when `argv` is None, print errors to stderr and return 0 for success or a non-zero code. Call it under `if __name__ == "__main__": raise SystemExit(main())`.

**Deeper explanation:**

```python
import sys

USAGE = "usage: greet [--name NAME] [--shout]"

def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] != "greet":
        print(USAGE, file=sys.stderr)
        return 2                                   # 2 = bad usage, as argparse uses
    has_name = "--name" in args[:-1]               # a value must follow the flag
    name = args[args.index("--name") + 1] if has_name else "there"
    message = f"Hello, {name}!"
    print(message.upper() if "--shout" in args else message)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Taking `argv` as a parameter makes `main` testable: a test calls `main(["greet", "--name", "Ada"])` and checks the output with pytest's `capsys` fixture, with no subprocess. Reading `sys.argv` inside the function, not as a default value, matters because defaults are evaluated once, at import time. `raise SystemExit(code)` ends the process with that exit code (`None` or 0 means success), which shells, CI and Docker health checks read from `$?`. Usage errors go to stderr so a pipe on stdout stays clean.

The guard works because pytest imports the file under its module name, so `__name__` is not `"__main__"` and nothing runs at import.

**Follow-ups they will ask:**
- How do you expose it as a command after install?: Add `[project.scripts]` with `greet = "my_api.cli:main"` to `pyproject.toml`, the equivalent of `"bin"` in `package.json`; the generated wrapper calls `sys.exit(main())`.
- When do you switch to argparse or Typer?: As soon as you need help text, typed values, validation or subcommands.
- What exit code does an uncaught exception produce?: 1, with the traceback printed to stderr.

**Mistakes to avoid:**
- `def main(argv=sys.argv[1:])`: evaluated once at import, so tests and repeated calls see stale arguments.
- Calling `main()` at module top level without the guard, so a plain `import` runs the CLI.

### Q. Write a function that parses command-line style flags from a list of strings into a dict.
**Short answer (45 seconds):** Walk the list with an index, because `--key value` consumes two items. Split `--key=value` once with `str.partition`, treat a flag followed by nothing or by another flag as True, turn dashes in keys into underscores, and collect everything else, in order, under `"_"`.

**Deeper explanation:**

```python
def parse_args(argv: list[str]) -> dict[str, object]:
    result: dict[str, object] = {}
    positional: list[str] = []
    i = 0
    while i < len(argv):
        item = argv[i]
        if item.startswith("--"):
            key, sep, value = item[2:].partition("=")
            key = key.replace("-", "_")
            if sep:                                        # --key=value
                result[key] = value
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                result[key] = argv[i + 1]                  # --key value
                i += 1                                     # consume the value
            else:
                result[key] = True                         # bare --flag
        else:
            positional.append(item)
        i += 1
    result["_"] = positional
    return result

parse_args(["build", "--env=prod", "--verbose", "--port", "8000"])
# {'env': 'prod', 'verbose': True, 'port': '8000', '_': ['build']}
```

A `while` loop is used instead of `for item in argv` because a `--key value` pair must skip the next item, and a `for` loop cannot advance its own iterator cleanly. `str.partition("=")` always returns three parts and splits only on the first `=`, so `--url=https://x.io/?a=b` keeps its value intact; `sep` is empty when there was no `=`. Values stay strings: converting `"8000"` to an int belongs to a typed step that can name the flag in its error. Time is O(n).

**Follow-ups they will ask:**
- How would you support short flags like `-v`?: Add a single-dash branch, but at that point argparse already handles short and long flags, types, defaults and `--help`.
- How do you collect repeated flags such as `--tag a --tag b`?: `result.setdefault(key, []).append(value)` for those keys.
- What about a value that starts with a dash, like `--offset -5`?: This parser accepts it because only `--` marks a flag; argparse has its own rules for negative numbers.

**Mistakes to avoid:**
- Using `item.split("=")`, which breaks values that contain `=` (URLs, base64).
- A `for` loop with a "skip next" flag that someone later forgets to reset.

### Q. Write a greeting builder with defaults and keyword-only options, the Python version of a JavaScript options object.
**Short answer (45 seconds):** Give `name` a default, put a bare `*` before the options so they can only be passed by keyword, and use `name.strip() or "there"` for the fallback. Keyword-only parameters give you the readability of an options object plus a TypeError on typos.

**Deeper explanation:**

```js
function buildGreeting(name = "", { greeting = "Hello", punctuation = "!" } = {}) {
  return `${greeting}, ${name.trim() || "there"}${punctuation}`;
}
```

```python
def build_greeting(name: str = "", *, greeting: str = "Hello", punctuation: str = "!") -> str:
    who = name.strip() or "there"
    return f"{greeting}, {who}{punctuation}"

build_greeting("  Ada ")             # 'Hello, Ada!'
build_greeting(greeting="Hi")        # 'Hi, there!'
build_greeting("Bo", "Hey")          # TypeError: build_greeting() takes from 0 to 1
                                     # positional arguments but 2 were given
```

Everything after the bare `*` must be passed by name, so call sites read like an options object (`greeting="Hi"`) and a misspelled option (`greting="Hi"`) raises TypeError instead of being ignored, as an unknown key in a JavaScript options object would be. `or` returns its first truthy operand, like `||`, which is exactly right here because an empty or whitespace-only name should fall back. The string defaults are immutable, so evaluating them once is safe. FastAPI path functions and most modern Python libraries use this signature style.

**Follow-ups they will ask:**
- When is `or` the wrong fallback?: When a falsy value is valid, such as 0 or an empty list; write `x if x is not None else default`.
- How do you accept arbitrary extra options?: `**options: str` collects them into a dict, but then typos no longer raise, so validate the keys.
- What does a `/` in a signature mean?: Parameters before it are positional-only (3.8+), as in `def f(a, /, b)`.

**Mistakes to avoid:**
- Using a mutable default such as `options: dict = {}`.
- Passing an options dict instead of keyword arguments, which loses the TypeError on typos and the type checker's help.

### Q. A script runs with python app/main.py but fails with ModuleNotFoundError: No module named 'app'. Find and fix the problem.
**Short answer (45 seconds):** Running a file puts that file's own folder (`app/`) on `sys.path`, not the project root, so `import app...` has nothing to find. Run it as a module from the root with `python -m app.main` (or `uv run python -m app.main`), or install the project into its venv so the package imports from anywhere. Do not patch `sys.path` in code.

**Deeper explanation:**

```text
project/
  app/
    __init__.py
    main.py          # from app.settings import load_settings
    settings.py

$ python app/main.py
Traceback (most recent call last):
  File "/project/app/main.py", line 1, in <module>
    from app.settings import load_settings
ModuleNotFoundError: No module named 'app'
```

Python resolves absolute imports by searching `sys.path`. With `python app/main.py`, `sys.path[0]` is `/project/app`, which contains `settings.py` but no `app` package. With `python -m app.main` run from `/project`, `sys.path[0]` is the current directory, so `app` is found, and `__name__` is still `"__main__"`. Node resolves `./settings.js` relative to the importing file, which is why this surprises JavaScript engineers.

Fixes, best first:
1. Run as a module from the project root: `python -m app.main`.
2. Use the src layout with a build backend; `uv sync` installs the project into `.venv` in editable mode, so `import my_api` works from tests, scripts and uvicorn alike.
3. For tests only, pytest's `pythonpath = ["."]` setting (pytest 7+) adds the root.

Changing the import to `from settings import load_settings` makes the script run but breaks the moment the module is imported as part of the package.

**Follow-ups they will ask:**
- Why does `uvicorn app.main:app` work from the root?: uvicorn puts its `--app-dir` (default: the current directory) on `sys.path` before importing.
- What about `from .settings import load_settings`?: Relative imports work under `-m` but fail as a script with "ImportError: attempted relative import with no known parent package".
- How do you debug any import error?: Print `sys.path` and `sys.executable`, and check the module's `__file__`.

**Mistakes to avoid:**
- Adding `sys.path.append(...)` lines to scripts.
- Naming your own file `json.py`, `random.py` or `fastapi.py`, which shadows the real module because the script folder comes first on `sys.path`.

### Q. A teammate pastes the traceback below from a container that crashed at startup. Read it and fix the bug.
**Short answer (45 seconds):** Read the last line first: `int()` was handed an empty string, at settings.py line 6, which the `^` markers underline. PORT exists in the container but is blank, and `os.environ.get("PORT", "8000")` only falls back when the key is missing, not when it is empty. Treat blank as missing, convert and validate with a clear message, and fix the deployment value.

**Deeper explanation:**

```text
Traceback (most recent call last):
  File "/srv/app/main.py", line 11, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/srv/app/main.py", line 5, in main
    settings = load_settings()
               ^^^^^^^^^^^^^^^
  File "/srv/app/settings.py", line 6, in load_settings
    "port": int(os.environ.get("PORT", "8000")),
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid literal for int() with base 10: ''
```

Frames run oldest to newest, so the frame just above the message is where it broke: `load_settings`, called from `main`, called at module level. The `''` in the message is the clue: a Helm value, a Compose file or a `.env` line such as `PORT=` set the variable to an empty string, so `.get` returned `""` instead of the default.

```python
import os
from collections.abc import Mapping

def read_port(env: Mapping[str, str], default: int = 8000) -> int:
    raw = env.get("PORT", "").strip()
    if not raw:
        return default
    try:
        port = int(raw)
    except ValueError:
        raise ValueError(f"PORT must be a whole number, got {raw!r}") from None
    if not 1 <= port <= 65535:
        raise ValueError(f"PORT must be between 1 and 65535, got {raw!r}")
    return port

PORT = read_port(os.environ)
```

`.strip()` plus `if not raw` treats missing, empty and whitespace-only values alike. Taking `env` as a `Mapping` parameter lets tests pass a plain dict while production passes `os.environ`. `from None` hides the original `int()` error, because the new message already names the variable and the bad value. In a FastAPI service, a pydantic-settings class with `port: int = 8000` validates the same way at startup.

**Follow-ups they will ask:**
- What does "During handling of the above exception, another exception occurred" mean?: An exception was raised inside an `except` block, so Python shows both; `raise ... from err` marks a deliberate cause, `from None` hides the first.
- Should every setting have a default?: No. Required settings such as `DATABASE_URL` should fail fast at startup with a clear message.
- How do you get a traceback into your logs?: Call `logger.exception("...")` inside the `except` block.

**Mistakes to avoid:**
- Reading from the top and "fixing" `main.py`.
- Assuming `.get(key, default)` covers empty values, or wrapping startup in `except Exception: pass` and running with no port.

### Q. mypy reports Item "None" of "str | None" has no attribute "strip" on this function. Fix it without silencing the checker.
**Short answer (45 seconds):** `os.environ.get` returns `str | None`, and the code calls `.strip()` before ruling out None, which also crashes at runtime when the variable is unset. Handle None first so the checker narrows the type to `str`, then validate the value against an allowed set.

**Deeper explanation:**

```python
import os

def normalize_env(value: str | None, default: str = "dev") -> str:
    return value.strip().lower() or default
# error: Item "None" of "str | None" has no attribute "strip"  [union-attr]
```

```python
ALLOWED_ENVS = {"dev", "staging", "prod"}

def normalize_env(value: str | None, default: str = "dev") -> str:
    if value is None or not value.strip():
        return default
    env = value.strip().lower()             # value is narrowed to str here
    if env not in ALLOWED_ENVS:
        raise ValueError(f"APP_ENV must be one of {sorted(ALLOWED_ENVS)}, got {value!r}")
    return env

APP_ENV = normalize_env(os.environ.get("APP_ENV"))
```

The checker is reporting a real bug: when `APP_ENV` is unset, the original raises `AttributeError: 'NoneType' object has no attribute 'strip'`, often only in a fresh environment or a new CI runner. After `if value is None ...: return`, mypy and pyright narrow `value` to `str` for the rest of the function, the same control-flow narrowing TypeScript applies to `string | undefined` under `strictNullChecks`. Short-circuiting means `value.strip()` in the condition only runs when `value` is not None. Validating against an allowed set turns a typo such as `production` into a startup error instead of a silent fallback.

**Follow-ups they will ask:**
- How would you type the allowed values?: Return `Literal["dev", "staging", "prod"]`, so callers get exhaustive checks in `match` statements.
- Is `assert value is not None` an acceptable fix?: It narrows the type, but it still crashes on None, and `python -O` strips asserts entirely.
- Which mypy option catches this?: Strict optional checking is on by default; `--strict` adds checks such as missing annotations.

**Mistakes to avoid:**
- Adding `# type: ignore[union-attr]` or `cast(str, value)`, which silences the report and keeps the crash.
- Changing the annotation to `value: str` while callers still pass `os.environ.get(...)`, which only moves the error.

### Practice
- Practice kit: open `python-practice/exercises/p02_setup.py`, implement each function, then run `uv run --with pytest pytest tests/test_p02_setup.py` from the `python-practice` folder.
- When the kit passes, run `uv run python exercises/p02_setup.py greet --name Ada --shout` and then `echo $?`; run it again with no arguments and confirm the exit code is 2.
- In the REPL, run `import sys` and inspect `sys.executable` and `sys.path[:3]`; repeat inside `uv run python` in a project and explain the difference.
- Create a throwaway project with `uv init --package demo`, add `ruff` as a dev dependency, mess up the formatting of one file, and watch `uv run ruff format --check .` fail and then pass.

## Variables, Types & Operators [Basics]

> Names, objects, the built-in scalar types and the operators that combine them. This is where JavaScript intuition is closest and therefore most dangerous: assignment never copies, `bool` is an `int`, `/` returns a float, `or` is not `??`, and floats cannot hold money. In FastAPI code these rules decide whether a handler accidentally shares state between users, whether `limit=0` is honoured, and whether an invoice total is off by a cent.

### Why it exists
Python's model is "everything is an object, and variables are names attached to objects". That keeps the language small: there is no separate rule for primitives versus references, assignment is always cheap, and a function receives the very object its caller holds. The price is aliasing: two names can share one mutable list, so a change made through one is visible through the other, and you must copy deliberately. Strong typing and an exact `int` remove JavaScript's coercion and overflow surprises, while `float` keeps the usual binary floating-point limits, which is why `decimal.Decimal` exists.

### In plain words
A Python variable is a name tag, not a box. `x = [1, 2]` creates a list object and hangs the tag `x` on it; `y = x` hangs a second tag on the same list, so changing the list through `y` changes what `x` sees. Some objects, like numbers, strings and tuples, can never be changed, so sharing them is harmless: "changing" one really means making a new object and moving the tag. Lists, dicts and sets can change in place, so with those you decide on purpose whether you want a second tag or a real copy.

### Walkthrough: names, objects and mutability
1. **Assignment binds a name to an object.** `x = 5` binds the name `x` to an int object. Assignment never copies anything. Every object has a type, a value and an identity (which `id()` shows), and a name is just a reference to one object at a time.

   ```python
   x = 5
   y = x            # y and x name the same int object
   y = y + 1        # makes a new int 6 and rebinds y; x is still 5
   print(x, y)      # 5 6
   ```

2. **Two names can share one list.** Rebinding a name never affects another name, but mutating a shared object does. JavaScript objects and arrays behave the same way; the difference is that Python has no separate primitives, so one rule covers every value.

   ```python
   a = [1, 2, 3]
   b = a            # a second name for the same list
   b.append(4)      # mutates the shared list
   print(a)         # [1, 2, 3, 4]
   b = [9]          # rebinds b only
   print(a)         # [1, 2, 3, 4]
   ```

3. **Mutable versus immutable types.** `int`, `float`, `bool`, `str`, `tuple`, `frozenset`, `bytes` and `None` are immutable; `list`, `dict`, `set`, `bytearray` and most class instances are mutable. Immutable objects can be shared freely and used as dict keys; mutable ones cannot be dict keys, because their hash could change after insertion.

   ```python
   s = "abc"
   s.upper()                                 # returns 'ABC'; s is still 'abc'
   s[0] = "z"                                # TypeError: 'str' object does not support item assignment
   rates = {("EUR", "2026-11-01"): 1.08}     # a tuple key is fine
   bad = {["EUR"]: 1.08}                     # TypeError: unhashable type: 'list'
   ```

4. **`+=` differs between mutable and immutable objects.** On a list, `+=` extends the same object in place, so every alias sees the change. On a str, int or tuple it builds a new object and rebinds only that one name.

   ```python
   nums = [1]
   alias = nums
   nums += [2]           # in place: alias is [1, 2] too
   text = "hi"
   saved = text
   text += "!"           # new string: saved is still 'hi'
   ```

5. **`is` versus `==`.** `==` asks "equal values?", and a class can define what that means with `__eq__`. `is` asks "the very same object?", and nothing can override it. Use `is` only for `None` and other singletons. CPython caches small ints (-5 to 256) and some strings, so `is` on numbers or text can pass a quick test and fail in production.

   ```python
   a = [1, 2]
   b = [1, 2]
   a == b, a is b         # (True, False)
   result = None
   result is None         # True: the idiomatic check
   id(a) == id(b)         # False: `is` compares exactly this
   ```

6. **Functions receive the same object, not a copy.** Python passes references to objects ("call by sharing"), exactly like JavaScript. A function that mutates a list argument changes the caller's list; a function that rebinds its parameter changes only its local name.

   ```python
   def add_item(cart: list[str]) -> None:
       cart.append("pen")       # the caller sees this

   def reset(cart: list[str]) -> None:
       cart = []                # rebinds the local name only

   items: list[str] = []
   add_item(items)
   reset(items)
   print(items)                 # ['pen']
   ```

7. **Copy on purpose: shallow versus deep.** `list(x)`, `x.copy()`, `x[:]`, `dict(d)` and `{**d}` make shallow copies: a new outer container holding the same inner objects. When the items are themselves lists or dicts, use `copy.deepcopy`, the equivalent of `structuredClone`.

   ```python
   import copy

   doc = {"id": 1, "tags": ["a"]}
   shallow = dict(doc)
   deep = copy.deepcopy(doc)
   shallow["tags"].append("b")    # also changes doc["tags"]
   deep["tags"].append("c")       # doc is untouched
   print(doc)                     # {'id': 1, 'tags': ['a', 'b']}
   ```

### Walkthrough: numbers, strings, booleans and None
1. **`int` and `float` are separate types.** Integers are exact at any size; floats are 64-bit IEEE 754 doubles, the same as a JavaScript `number`. Mixing them gives a float, and `/` always gives a float, even for `10 / 5`. Underscores make long literals readable.

   ```python
   type(10), type(10 / 5), type(10 // 5)   # (<class 'int'>, <class 'float'>, <class 'int'>)
   budget = 1_000_000                       # 1000000
   2 ** 64                                  # 18446744073709551616, exact
   ```

2. **Floats are binary approximations.** `0.1 + 0.2` is not `0.3` in either language. Compare floats with `math.isclose`. `round()` uses round-half-to-even and works on the stored binary value, so it is not a money tool.

   ```python
   import math

   0.1 + 0.2                        # 0.30000000000000004
   math.isclose(0.1 + 0.2, 0.3)     # True
   round(2.5), round(3.5)           # (2, 4): ties go to the even neighbour
   round(2.675, 2)                  # 2.67: the float is stored just below 2.675
   ```

3. **Use `decimal.Decimal` for money.** Build Decimals from strings (or ints), never from floats, and round with an explicit mode. Decimal refuses to mix with float, which is a feature. Many systems store integer cents instead; both avoid float drift.

   ```python
   from decimal import ROUND_HALF_UP, Decimal

   Decimal("0.10") + Decimal("0.20")    # Decimal('0.30')
   Decimal(0.1)                         # Decimal('0.1000000000000000055511151231257827021181583404541015625')
   Decimal("1.005").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)   # Decimal('1.01')
   Decimal("1.10") + 1.1                # TypeError: unsupported operand type(s) for +: 'decimal.Decimal' and 'float'
   ```

4. **`bool` is a subclass of `int`.** `True` and `False` act as 1 and 0 in arithmetic, so `sum(flags)` counts the True values. The flip side: `isinstance(True, int)` is True, so booleans slip through int validation unless you check for `bool` first.

   ```python
   True + True                  # 2
   sum([True, False, True])     # 2
   isinstance(True, int)        # True
   type(True) is int            # False: its exact type is bool
   ```

5. **`None` is a singleton of type `NoneType`.** It means "no value" and is what functions without `return` and `dict.get` on a missing key give you. Type hints spell an optional value `str | None` (3.10+; older code writes `Optional[str]`).

   ```python
   def find_user(uid: int) -> dict | None:
       return None if uid < 0 else {"id": uid}

   user = find_user(-1)
   if user is None:
       print("not found")
   ```

6. **`str` is an immutable sequence of Unicode code points.** Indexing, slicing and `in` work like on lists, methods return new strings, and `len` counts code points rather than UTF-16 units, so a character outside the Basic Multilingual Plane has length 1 in Python and 2 in JavaScript. Strings get a full lesson later.

   ```python
   name = "ada"
   name.capitalize(), name * 2, "d" in name    # ('Ada', 'adaada', True)
   len("\U0001D11E")                           # 1 (musical G clef); JavaScript's .length is 2
   ```

7. **`type()` and `isinstance()` replace `typeof`.** `type(x)` returns the exact class (JavaScript's `typeof` returns a string and says `"object"` for both null and arrays). Prefer `isinstance(x, (int, float))` for checks, because it accepts subclasses and a tuple of types; use `type(x) is int` only when you must exclude subclasses such as `bool`.

   ```python
   type(None), type([]), type({})     # (<class 'NoneType'>, <class 'list'>, <class 'dict'>)
   isinstance(3.0, (int, float))       # True
   isinstance("3", (int, float))       # False
   ```

8. **Conversions are explicit and strict.** `int()`, `float()`, `str()` and `bool()` convert, and they raise instead of guessing: `int("42px")` is a ValueError, where `parseInt("42px")` returns 42 and `Number("")` returns 0. `int()` accepts surrounding whitespace, truncates floats toward zero, and takes a base. `bool()` of any non-empty string is True.

   ```python
   int(" 42 "), int(3.9), int(-3.9), int("1A", 16)   # (42, 3, -3, 26)
   float("1e3"), str(3.0), str(None)                 # (1000.0, '3.0', 'None')
   int("4.2")       # ValueError: invalid literal for int() with base 10: '4.2'
   bool("False")    # True: a non-empty string
   ```

### Walkthrough: operators, comparisons and the walrus
1. **Arithmetic operators.** `+ - *` as usual, `/` true division, `//` floor division, `%` modulo with the sign of the divisor, `**` power, and `divmod(a, b)` for quotient and remainder at once. `-2 ** 2` is -4 because `**` binds tighter than unary minus (JavaScript rejects that expression as a SyntaxError). `*` also repeats sequences.

   ```python
   17 // 5, 17 % 5, divmod(17, 5)   # (3, 2, (3, 2))
   -17 // 5, -17 % 5                # (-4, 3)
   2 ** 10, 2 ** -1, -2 ** 2        # (1024, 0.5, -4)
   "ab" * 3, [0] * 3                # ('ababab', [0, 0, 0])
   ```

2. **Comparisons chain.** `1 < x < 5` means `1 < x and x < 5`, with `x` evaluated once. In JavaScript the same text compares a boolean to 5, so `10 < 3 < 2` is true there and False in Python. Ordering unrelated types raises TypeError instead of coercing.

   ```python
   x = 3
   1 < x < 5            # True
   0 <= x <= 2          # False
   10 < x < 2           # False (JavaScript's 10 < 3 < 2 is true)
   "a" < 1              # TypeError: '<' not supported between instances of 'str' and 'int'
   ```

3. **Boolean operators return operands.** `and`, `or` and `not` are words. Like `&&` and `||`, `and` and `or` short-circuit and return one of their operands, not necessarily a bool. `x or default` is JavaScript's `||`: it replaces every falsy value, including 0 and `""`. Python has no `??`; write `x if x is not None else default`.

   ```python
   "" or "anon"                          # 'anon'
   0 or 20                               # 20: a valid 0 is lost
   limit = 0
   limit if limit is not None else 20    # 0: the ?? equivalent
   "a" and "b", 0 and 1                  # ('b', 0)
   ```

4. **Conditional expressions and membership.** The ternary is `a if condition else b`, with the condition in the middle. `in` and `not in` test membership in any container (keys for dicts, substrings for strings), and `is not` is the negated identity test.

   ```python
   age, roles, email = 20, {"admin", "dev"}, "ada.example.com"
   status = "adult" if age >= 18 else "minor"    # 'adult'
   "admin" in roles                              # True
   "@" not in email                              # True: flag this address
   ```

5. **Augmented assignment.** `+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=` and the bitwise forms exist; `++` does not. Remember from the first walkthrough that `+=` mutates lists in place but rebinds immutable values.

   ```python
   retries = 0
   retries += 1         # 1
   backoff = 0.5
   backoff *= 2         # 1.0
   ```

6. **The walrus operator `:=` (3.8+).** It assigns inside an expression, which removes a repeated call in a condition or a comprehension. Use it sparingly; a plain assignment on the line before is often clearer.

   ```python
   import re

   if (m := re.match(r"(\d+)px", "42px")) is not None:
       print(int(m.group(1)))            # 42

   data = [3, 8, 1, 9]
   if (n := len(data)) > 3:
       print(f"too many items: {n}")     # too many items: 4
   ```

7. **Precedence you will actually meet.** `not` binds more loosely than comparisons, so `not a == b` means `not (a == b)`, and `and` binds tighter than `or`. When an expression mixes them, add parentheses for the reader. Bitwise `&`, `|`, `^`, `~`, `<<`, `>>` work on ints, and `&` and `|` also mean intersection and union on sets.

   ```python
   a, b = 1, 2
   not a == b                     # True: not (a == b)
   True or False and False        # True: `and` is evaluated first
   {1, 2} & {2, 3}, {1} | {2}     # ({2}, {1, 2})
   ```

### Concepts you must understand
- Assignment binds a name to an object and never copies; rebinding one name never affects another.
- Mutating a shared mutable object (list, dict, set, most instances) is visible through every name bound to it, including function parameters.
- Immutable types (int, float, bool, str, tuple, frozenset, None) cannot change in place; operations on them return new objects.
- Use `==` for value equality and `is` only for `None` and other singletons.
- Shallow copies (`list(x)`, `x.copy()`, `{**d}`) share nested objects; `copy.deepcopy` copies the whole tree.
- `int` is exact and unbounded; `float` is a 64-bit binary double, so compare with `math.isclose` and use `Decimal` built from strings for money.
- `bool` is a subclass of `int`, so check for `bool` before `int` when validating input.
- Conversions raise instead of guessing: `int("42px")` is a ValueError, and `bool("False")` is True.
- `x or default` replaces every falsy value; when 0, `""` or `[]` are valid, test `is None` instead.
- Comparisons chain (`1 < x < 5`), `/` always returns a float, and `//` and `%` floor toward negative infinity.

| JavaScript | Python | Note |
| --- | --- | --- |
| `let x = 5` | `x = 5` | No declaration keyword; a name exists once assigned |
| `const MAX = 3` | `MAX = 3` (or `Final[int]` for the checker) | Not enforced at runtime |
| `typeof x` | `type(x)`, `isinstance(x, int)` | `typeof null` is "object"; `type(None)` is NoneType |
| `number` | `int` and `float` | `/` gives a float; `//` on ints gives an int |
| `BigInt` | `int` | Arbitrary precision is built in |
| `[...arr]`, `{...obj}` | `arr.copy()`, `{**d}` | Shallow, like spread |
| `structuredClone(obj)` | `copy.deepcopy(obj)` | Copies nested objects too |
| `parseInt("42px")` | `int("42px")` | Python raises ValueError instead of returning 42 |
| `a ?? b` | `a if a is not None else b` | `a or b` is the `||` equivalent |
| `cond ? a : b` | `a if cond else b` | Condition in the middle |
| `1 < x && x < 5` | `1 < x < 5` | Chained comparison |
| `Math.abs(a - b) < Number.EPSILON` | `math.isclose(a, b)` | Same IEEE 754 doubles underneath |

### Q. Predict the output of this code about shared lists and a tuple, and explain it.
**Short answer (45 seconds):** It prints `[1, 2, 3, 4] [1, 2, 3] True False` and then `(1, [2, 3, 4])`. `b` is a second name for the same list, so appending through `b` changes `a`; `c` is a slice copy taken before the append. The tuple cannot be rebound item by item, but it holds a reference to a list, and that list can still change.

**Deeper explanation:**

```python
a = [1, 2, 3]
b = a
c = a[:]
b.append(4)
print(a, c, a is b, a == c)

t = (1, [2, 3])
t[1].append(4)
print(t)
```

```text
[1, 2, 3, 4] [1, 2, 3] True False
(1, [2, 3, 4])
```

`b = a` copies nothing: it binds a second name to the same list object, so `a is b` is True and the append is visible through `a`. `c = a[:]` creates a new list with the same items, so it keeps `[1, 2, 3]`, and `a == c` is False because the contents now differ. Before the append, `a == c` would have been True and `a is c` False.

A tuple's immutability is shallow. The tuple stores two references, to the int 1 and to a list, and those references can never be replaced. The list itself is still mutable, so `t[1].append(4)` succeeds. One consequence: this tuple is not hashable, so `hash(t)` raises `TypeError: unhashable type: 'list'`, and it cannot be a dict key or a set member.

The same reasoning explains the JavaScript equivalent with `const b = a`, but JavaScript has no immutable tuple, so the second half is new.

**Follow-ups they will ask:**
- What does `t[1] += [5]` do?: It extends the list in place, then the item assignment on the tuple raises TypeError, so you get both an exception and a changed list.
- How do you make the tuple fully immutable?: Store only immutable items, such as `(1, (2, 3))`.
- Is `a[:]` enough for a list of dicts?: No, it is shallow; the dicts are shared. Use `copy.deepcopy` or build new dicts.

**Mistakes to avoid:**
- Saying `b = a` copies the list.
- Saying a tuple's contents can never change.

### Q. Callers report that this tagging helper changes their original data. Find and fix the bug.
**Short answer (45 seconds):** `doc.copy()` is shallow: the new dict holds the same `tags` list as the original, so appending to it mutates the caller's document. Either deep-copy the document or, cheaper, build new objects only for the parts you change: `{**doc, "tags": [*doc.get("tags", []), tag]}`.

**Deeper explanation:**

```python
def clone_with_tag(doc: dict, tag: str) -> dict:
    result = doc.copy()                       # same bug with dict(doc) or {**doc}
    result.setdefault("tags", []).append(tag)
    return result

original = {"id": 1, "tags": ["a"]}
clone_with_tag(original, "b")
print(original)    # {'id': 1, 'tags': ['a', 'b']}, expected ['a']
```

A shallow copy creates a new outer dict whose values are the same objects as before. The ints and strings are immutable, so sharing them is harmless, but `tags` is a list, and `append` mutates the one list both dicts point at.

```python
import copy

def clone_with_tag(doc: dict, tag: str) -> dict:
    result = copy.deepcopy(doc)                     # copies every nested object
    result.setdefault("tags", []).append(tag)
    return result

def clone_with_tag_lean(doc: dict, tag: str) -> dict:
    return {**doc, "tags": [*doc.get("tags", []), tag]}   # new dict, new list
```

`deepcopy` is the safe default and also handles cycles, but it is O(size of the document) and copies things you never touch. The lean version only allocates a new dict and a new list, yet still shares every other nested value (for example a `meta` dict), which is fine as long as nobody mutates those. The practice kit asks for the fully independent version.

The bug is common in FastAPI code when a module-level template dict is "copied" per request and then mutated: one user's data shows up in the next user's response.

**Follow-ups they will ask:**
- When is `deepcopy` a bad idea?: Large documents on a hot path, or objects that hold resources such as locks, sockets or HTTP clients.
- How do you avoid the question entirely?: Return new objects instead of mutating, use frozen dataclasses, or Pydantic's `model_copy(update=...)`.
- Does JavaScript have the same bug?: Yes, with `{...doc}`; `structuredClone` is its deep copy.

**Mistakes to avoid:**
- Assuming `dict(doc)` or `{**doc}` copies nested lists.
- Mutating the input "for speed" without making it obvious in the function name and docstring.

### Q. Write a function that adds money amounts given as strings without float errors and rounds them to cents.
**Short answer (45 seconds):** Convert each string straight to `Decimal`, add them with a `Decimal("0")` start value, then `quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`. Never pass through float, because the binary error is baked in before you get a chance to round.

**Deeper explanation:**

```python
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

def sum_money(amounts: list[str]) -> Decimal:
    total = sum((Decimal(a) for a in amounts), Decimal("0"))
    return total.quantize(CENT, rounding=ROUND_HALF_UP)

sum_money(["0.10", "0.20"])    # Decimal('0.30')
sum_money(["1.005"])           # Decimal('1.01')
sum_money([])                  # Decimal('0.00')
```

`Decimal("1.005")` is exactly 1.005, so half-up rounding gives 1.01. The float route gives `round(1.005, 2) == 1.0`, because the float nearest to 1.005 sits slightly below it. The start value matters: `sum([])` returns the int 0, which has no `quantize` method (`AttributeError: 'int' object has no attribute 'quantize'`). `quantize` keeps the result at exactly two places, so `str(result)` is `"0.30"`, ready for an invoice.

Choose the rounding mode on purpose. Decimal's default is `ROUND_HALF_EVEN` (banker's rounding), which turns 1.005 into 1.00; finance teams often specify half-up, and the rule belongs in code, not in luck.

Time is O(n). Decimal arithmetic is slower than float, which does not matter for invoices and does matter for numerical work, where floats are correct.

**Follow-ups they will ask:**
- Why not store integer cents?: Also correct and common (Stripe's API uses integer amounts in the smallest currency unit); convert to a display string at the edges.
- How does this flow through Postgres and FastAPI?: Use a `NUMERIC` column (psycopg and asyncpg return `Decimal`) and declare Pydantic fields as `Decimal`; send amounts to clients as strings so JavaScript does not round them as floats.
- What does `Decimal(0.1)` give?: The exact binary value of the float, a long run of digits after 0.1000000000000000055.

**Mistakes to avoid:**
- `Decimal(some_float)` or `Decimal(str(round(x, 2)))` after the float math already happened.
- Using `round()` on floats for invoices.

### Q. Write a function that converts user input into an int or a float safely, rejecting junk, NaN and infinity.
**Short answer (45 seconds):** Strip the text, try `int()` first so whole numbers stay ints, fall back to `float()`, and reject non-finite results with `math.isfinite`. Let the `ValueError` from `float()` propagate for junk.

**Deeper explanation:**

```python
import math

def to_number(text: str) -> int | float:
    cleaned = text.strip()
    try:
        return int(cleaned)
    except ValueError:
        pass
    number = float(cleaned)          # raises ValueError for junk such as "abc" or ""
    if not math.isfinite(number):
        raise ValueError(f"not a finite number: {text!r}")
    return number

to_number(" 42 "), to_number("2.50"), to_number("1e3")   # (42, 2.5, 1000.0)
to_number("nan")                                         # ValueError: not a finite number: 'nan'
```

This is EAFP style ("easier to ask forgiveness than permission"): attempt the conversion and catch the specific error, rather than pre-checking with string methods. Pre-checks are worse than they look: `"-7".isdigit()` is False, while `"²".isdigit()` is True even though `int("²")` raises.

Trying `int` first matters because `float("42")` returns `42.0`, which changes the type and, above 2**53, loses precision. `float()` happily accepts `"nan"`, `"inf"` and `"infinity"`, and NaN then poisons every comparison (`nan == nan` is False) and serialises as the non-standard `NaN` token in JSON, so reject it at the boundary.

Contrast with JavaScript: `parseFloat("3.5abc")` returns 3.5 and `Number("")` returns 0; Python raises for both, which is what you want for input validation.

**Follow-ups they will ask:**
- How does FastAPI handle this for query parameters?: Declare `limit: int` and validation happens for you, returning a 422 with details for junk.
- Should `"1,000"` be accepted?: Not by default; separators and locales are a product decision, so strip them explicitly if needed.
- Why catch `ValueError` and not `Exception`?: A broad catch hides real bugs, such as passing None, which raises TypeError.

**Mistakes to avoid:**
- Using `str.isdigit()` checks, which reject `"-7"` and `" 7"` and accept characters `int()` rejects.
- Forgetting NaN and infinity, which `float()` accepts.

### Q. A quantity validator accepts True as a valid quantity of 1. Find and fix the bug.
**Short answer (45 seconds):** `bool` is a subclass of `int`, so `isinstance(True, int)` is True and `True` passes as the number 1. Reject `bool` explicitly before the int check, then validate the range with a chained comparison.

**Deeper explanation:**

```python
def validate_quantity(value: object) -> int:
    if not isinstance(value, int):
        raise TypeError("quantity must be an int")
    if value < 1 or value > 99:
        raise ValueError("quantity must be between 1 and 99")
    return value

validate_quantity(True)    # returns True: accepted as a quantity of 1
```

A JSON body such as `{"qty": true}` decodes to Python's `True`, so this is a real input path, not a curiosity.

```python
def validate_quantity(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"quantity must be an int, got {type(value).__name__}")
    if not 1 <= value <= 99:
        raise ValueError(f"quantity must be between 1 and 99, got {value}")
    return value

validate_quantity(3)       # 3
validate_quantity(True)    # TypeError: quantity must be an int, got bool
validate_quantity(0)       # ValueError: quantity must be between 1 and 99, got 0
```

The bool check must come first because the int check accepts booleans. `1 <= value <= 99` is a chained comparison: it means `1 <= value and value <= 99` and reads like the business rule. `type(value).__name__` puts the actual type in the message, which saves a debugging round trip. In Pydantic, mark the field strict (`StrictInt` or `Field(strict=True)`) when booleans and numeric strings must be rejected.

**Follow-ups they will ask:**
- Why is `True` an int at all?: `bool` was added as a subclass of `int` for backward compatibility; `True == 1` and `hash(True) == hash(1)`, so `{1: "a", True: "b"}` is `{1: 'b'}`.
- Why not `type(value) is int`?: It also rejects bool, but it rejects legitimate int subclasses such as `IntEnum` members too; the explicit bool check states the intent.
- How would you accept the string `"3"` from a form?: Convert at the boundary first with `int(value)`, then validate, keeping parsing and validation separate.

**Mistakes to avoid:**
- Trusting `isinstance(x, int)` on request data without remembering bool.
- Putting the range check before the type check, so a string fails with a confusing `'<' not supported` error.

### Q. Rewrite this JavaScript page-size helper, which uses == null and nested ternaries, in idiomatic Python while keeping 0 as a valid value.
**Short answer (45 seconds):** Test `raw is None` for the fallback, because `raw or default` would turn a valid 0 into 20, then clamp with `min(max(raw, 0), maximum)` instead of nested conditional expressions. Rename the `max` parameter so it does not shadow the built-in `max()`.

**Deeper explanation:**

```js
function pageLimit(raw, fallback = 20, max = 100) {
  if (raw == null) return fallback;
  return raw > max ? max : raw < 0 ? 0 : raw;
}
```

```python
def page_limit(raw: int | None, default: int = 20, maximum: int = 100) -> int:
    if raw is None:
        return default
    return min(max(raw, 0), maximum)

page_limit(None), page_limit(0), page_limit(500), page_limit(-5)   # (20, 0, 100, 0)
```

JavaScript's `raw == null` catches both null and undefined; Python has only `None`, and `is None` is the idiomatic test. The tempting one-liner `raw or default` is the `||` bug: 0 is falsy, so a client asking for `limit=0` (a "count only" request) silently gets 20 rows. `min(max(raw, 0), maximum)` is the standard clamp idiom and reads in one pass, where a nested conditional expression (`maximum if raw > maximum else 0 if raw < 0 else raw`) is legal but hard to scan.

Naming matters more than in JavaScript: `max`, `min`, `id`, `type`, `list` and `input` are built-in functions. Keep the JavaScript parameter name `max` and, inside the function, `max` is now the int 100, so `max(raw, 0)` raises `TypeError: 'int' object is not callable`.

**Follow-ups they will ask:**
- How would FastAPI express this?: `limit: Annotated[int | None, Query(ge=0, le=100)] = None`, which rejects out-of-range values with a 422 instead of clamping; choose reject or clamp deliberately.
- What would `raw or default` return for 0?: 20, because 0 is falsy.
- Would the walrus operator help here?: Not really; it shines when a computed value is tested and then reused, as with a regex match.

**Mistakes to avoid:**
- Naming parameters `max`, `min`, `type`, `id` or `list`, which shadows the built-in for the whole function.
- Writing `if not raw:` for the None check, which treats 0 as missing.

### Practice
- Practice kit: open `python-practice/exercises/p03_variables.py`, implement each function, then run `uv run --with pytest pytest tests/test_p03_variables.py` from the `python-practice` folder.
- In the REPL, run `grid = [[0] * 3] * 3`, then `grid[0][0] = 1`, print `grid`, and explain why every row changed; then build it correctly with `[[0] * 3 for _ in range(3)]`.
- In the REPL, compare `round(0.125, 2)`, `Decimal("0.125").quantize(Decimal("0.01"))` and the same quantize with `rounding=ROUND_HALF_UP`, and explain why you get 0.12, 0.12 and 0.13.
- Rewrite `[f(x) for x in data if f(x) > 0]` with the walrus operator so `f` runs once per item, and check with a `print` inside `f` that it does.
