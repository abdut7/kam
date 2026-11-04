## Dataclasses, Enums & Type Hints [Core]

> This lesson covers the three tools that give Python data a shape: `@dataclass` for plain data objects, `Enum` and `StrEnum` for fixed sets of values, and type hints for describing what goes in and out of functions. In FastAPI and AI backends they are everywhere: Pydantic request models are built from type hints, `Annotated[...]` carries `Query` and `Depends` metadata, enums become validated path parameters and dropdowns in `/docs`, and internal objects such as a retrieved RAG chunk or an agent step are usually dataclasses.

### Why it exists
A plain class that only holds data needs a hand-written `__init__`, `__repr__` and `__eq__`, and that boilerplate is where typos and stale fields hide; `@dataclass` (3.7+) generates all three from the field list. Magic strings like `"shipped"` spread through a codebase until one typo reaches the database; an enum makes the allowed set explicit and fails loudly on anything else. Python is dynamically typed, so large codebases adopted optional type hints (PEP 484, Python 3.5) that tools like mypy and pyright check before the code runs. The trade-off: hints are never enforced by the interpreter, so they are only as trustworthy as the checker in your CI and the runtime validation (Pydantic) at your boundaries.

### In plain words
A dataclass is a form template: you list the fields once and Python prints the form for you (constructor, readable printout, comparison). An enum is a dropdown menu: you can only pick one of the listed options. Type hints are labels on boxes in a warehouse. The delivery truck (the Python interpreter) never reads the labels; an inspector (mypy or pyright) walks the shelves before opening day and flags mismatches. Pydantic is the customs officer who actually opens the boxes that arrive from outside, such as HTTP requests and LLM output.

### Walkthrough: dataclasses step by step

1. **The boilerplate a dataclass removes.** `@dataclass` reads the annotated class attributes and generates `__init__`, `__repr__` and `__eq__`.

   ```python
   from dataclasses import dataclass

   @dataclass
   class Chunk:
       doc_id: str
       text: str
       score: float

   c = Chunk("doc-1", "Refunds take 5 days", 0.82)
   print(c)  # Chunk(doc_id='doc-1', text='Refunds take 5 days', score=0.82)
   print(c == Chunk("doc-1", "Refunds take 5 days", 0.82))  # True: field-by-field
   ```

   In JavaScript `{a: 1} === {a: 1}` is false. A dataclass `==` compares the field values, like a deep-equal written for you.

2. **Defaults and field order.** The generated `__init__` is a normal signature, so fields with defaults must come after fields without. Break the rule and the class definition itself fails with `TypeError: non-default argument 'b' follows default argument`. `@dataclass(kw_only=True)` (3.10+) makes every field keyword-only and lifts the rule.

   ```python
   @dataclass
   class SearchRequest:
       query: str
       top_k: int = 5
       min_score: float = 0.0

   req = SearchRequest("refund policy", top_k=3)
   ```

3. **The mutable default trap and `field(default_factory=...)`.** A default value is created once, when the class is defined, so a `[]` default would be one list shared by every instance. `@dataclass` refuses it with `ValueError: mutable default <class 'list'> for field tags is not allowed: use default_factory`. `default_factory` calls the factory for each new instance.

   ```python
   from dataclasses import dataclass, field

   @dataclass
   class Conversation:
       user_id: str
       messages: list[dict[str, str]] = field(default_factory=list)
       meta: dict[str, str] = field(default_factory=dict)

   a, b = Conversation("u1"), Conversation("u2")
   a.messages.append({"role": "user", "content": "hi"})
   print(b.messages)  # []: each instance got its own list
   ```

4. **`__post_init__` for validation and derived fields.** The generated `__init__` calls `__post_init__` last. Use it to normalise and validate, and pair it with `field(init=False)` for computed fields the caller must not pass.

   ```python
   @dataclass
   class Price:
       amount: float
       currency: str = "USD"
       display: str = field(init=False)

       def __post_init__(self) -> None:
           if self.amount < 0:
               raise ValueError("amount must be >= 0")
           self.currency = self.currency.upper()
           self.display = f"{self.amount:.2f} {self.currency}"

   print(Price(5, "inr").display)  # 5.00 INR
   ```

   The dataclass never checks types: `Price("cheap")` gets past the generated `__init__` and only crashes on the `<` comparison inside `__post_init__`.

5. **`frozen=True` for immutable values.** Assigning to a field raises `FrozenInstanceError: cannot assign to field 'name'`, and the instance becomes hashable, so it can be a dict key or a set member. To change one field, copy with `dataclasses.replace`, the Python version of `{...cfg, temperature: 0.9}`.

   ```python
   from dataclasses import dataclass, replace

   @dataclass(frozen=True)
   class ModelConfig:
       name: str
       temperature: float = 0.2

   base = ModelConfig("gpt-4o-mini")
   creative = replace(base, temperature=0.9)  # new object, base untouched
   cache = {base: "cached answer"}            # hashable, so a valid dict key
   ```

   Frozen is shallow: a `list` field can still be appended to, and that list makes `hash()` fail with `TypeError: unhashable type: 'list'`. Use a `tuple` for collections inside frozen dataclasses.

6. **`order=True` and `slots=True`.** `order=True` generates `<`, `<=`, `>` and `>=` that compare the fields as a tuple in definition order, so `sorted()` and `max()` just work. `slots=True` (3.10+) stores fields in fixed slots instead of a per-instance `__dict__`: less memory per object, and a typo such as `v.mjaor = 2` raises `AttributeError` instead of silently creating a new attribute.

   ```python
   @dataclass(order=True, frozen=True, slots=True)
   class Version:
       major: int
       minor: int
       patch: int

   print(sorted([Version(1, 10, 0), Version(1, 9, 0)]))  # 1.9.0 first: numeric, not string order
   ```

7. **Getting data back out.** `dataclasses.asdict(obj)` recursively converts a dataclass (and nested ones) into dicts, ready for `json.dumps`; `astuple` does the same into tuples. Both build new containers and copy values, so they are not free on large nested objects in a hot path.

   ```python
   import json
   from dataclasses import asdict

   print(json.dumps(asdict(Chunk("doc-1", "text", 0.9))))
   # {"doc_id": "doc-1", "text": "text", "score": 0.9}
   ```

### Walkthrough: choosing a data container, and enums

1. **Four ways to model a record.** They look alike but solve different problems. The deciding question: does this data come from outside and need validating?

   ```python
   from dataclasses import dataclass
   from typing import NamedTuple, TypedDict
   from pydantic import BaseModel

   class ChatRequest(BaseModel):   # boundary: validates and coerces untrusted JSON
       message: str
       top_k: int = 5

   @dataclass
   class RetrievedChunk:           # internal object passed between your own functions
       doc_id: str
       text: str
       score: float

   class Message(TypedDict):       # still a plain dict at runtime, keys are typed
       role: str
       content: str

   class Span(NamedTuple):         # small immutable tuple with names, unpackable
       start: int
       end: int
   ```

   Pydantic `BaseModel`: validates, coerces and serializes, so use it for request and response bodies, structured LLM output and settings. `@dataclass`: no validation, cheap, so use it for internal domain objects and results passed between layers. `TypedDict`: a type for dicts that must stay dicts, such as the `messages` list an LLM SDK expects or JSON you pass through. `NamedTuple`: tiny immutable values you want to unpack, as in `start, end = span`. In TypeScript terms, `TypedDict` is a `type` alias for an object shape, a dataclass is a class with a generated constructor, and Pydantic is closer to a Zod schema that also gives you the type.

2. **Enum basics.** An `Enum` is a class whose attributes are its only allowed instances. Members have `.name` and `.value`, iterate in definition order, and are singletons, so compare them with `is`. Calling the class with a value looks the member up.

   ```python
   from enum import Enum

   class Role(Enum):
       USER = "user"
       ASSISTANT = "assistant"
       TOOL = "tool"

   print(Role.USER.name, Role.USER.value)  # USER user
   print(Role("tool") is Role.TOOL)        # True
   print([r.value for r in Role])          # ['user', 'assistant', 'tool']
   Role("admin")                           # ValueError: 'admin' is not a valid Role
   ```

   TypeScript's `enum Role { User = "user" }` is the closest match, but a Python enum is a real class: you can give it methods and properties.

3. **The plain `Enum` trap: a member is not equal to its value.** `Role.USER == "user"` is `False`, and `json.dumps({"role": Role.USER})` raises `TypeError: Object of type Role is not JSON serializable`. Code that compares raw strings from a database against members silently takes the wrong branch.

   ```python
   row = {"role": "user"}               # from the database
   if row["role"] == Role.USER:         # False: a str never equals a plain Enum member
       print("never printed")
   if Role(row["role"]) is Role.USER:   # convert at the boundary, then compare members
       print("matched")
   ```

4. **`StrEnum` (3.11+) and `auto()`.** `StrEnum` members are real `str` objects, so they equal their value, serialize to JSON and print as the value in f-strings. In a `StrEnum`, `auto()` produces the lowercase member name. Before 3.11 people wrote `class Status(str, Enum)`, which compares equal to strings but formats as `Status.SHIPPED` in an f-string, a classic source of broken URLs and log lines.

   ```python
   import json
   from enum import StrEnum, auto

   class OrderStatus(StrEnum):
       PENDING = auto()   # "pending"
       SHIPPED = auto()   # "shipped"

   print(OrderStatus.SHIPPED == "shipped")             # True
   print(f"/orders?status={OrderStatus.SHIPPED}")      # /orders?status=shipped
   print(json.dumps({"status": OrderStatus.PENDING}))  # {"status": "pending"}
   ```

   In a plain `Enum`, `auto()` numbers members 1, 2, 3. Use `IntEnum` when members must behave as ints; `http.HTTPStatus` is one.

5. **Enums in FastAPI and Pydantic.** Annotate a path parameter, query parameter or model field with an enum and FastAPI validates it, answers 422 for anything else, and lists the allowed values in `/docs`. Inside the handler you receive a real member.

   ```python
   from fastapi import FastAPI
   from pydantic import BaseModel

   app = FastAPI()

   class OrderUpdate(BaseModel):
       status: OrderStatus           # body {"status": "shiped"} gets a 422

   @app.get("/orders/{status}")
   async def list_orders(status: OrderStatus) -> list[dict]:
       return [{"status": status}]   # GET /orders/shiped never reaches this line
   ```

### Walkthrough: type hints from basics to generics

1. **Annotations and built-in generics.** Write `name: type` for parameters and variables and `-> type` for the return. Since 3.9 the built-in collections are generic, so `list[int]` and `dict[str, float]` replace `typing.List` and `typing.Dict`. `tuple[str, int]` is exactly two items; `tuple[int, ...]` is any length.

   ```python
   def average(scores: list[float]) -> float:
       return sum(scores) / len(scores)

   counts: dict[str, int] = {}
   pair: tuple[str, int] = ("retries", 3)
   ```

   This is TypeScript's `function average(scores: number[]): number` with an arrow for the return type.

2. **`Optional`, `X | None` and `Union`.** `Optional[str]` means "str or None", not "optional argument". Since 3.10 you write `str | None`, and `int | str` instead of `Union[int, str]`. An argument is optional only when it has a default.

   ```python
   def find_user(user_id: int, tenant: str | None = None) -> dict | None:
       return None if tenant is None else {"id": user_id, "tenant": tenant}
   ```

   Python has a single "nothing" value, `None`, where JavaScript has both `null` and `undefined`.

3. **`Literal`, `Any` and `Callable`.** `Literal["asc", "desc"]` allows only those exact values, like a TypeScript string-literal union. `Any` switches checking off, like TS `any`; prefer `object` when you mean "anything, but make me narrow it before use", like TS `unknown`. `Callable[[int, str], bool]` describes a function's parameter types and return type; import it from `collections.abc`.

   ```python
   from collections.abc import Callable
   from typing import Any, Literal

   def sort_docs(docs: list[dict[str, Any]], order: Literal["asc", "desc"] = "desc") -> list[dict[str, Any]]:
       return sorted(docs, key=lambda d: d["score"], reverse=order == "desc")

   Handler = Callable[[str], str]   # alias: any function taking a str and returning a str
   ```

4. **`TypedDict` and `Protocol`.** `TypedDict` types the keys of a dict; at runtime it is still a plain `dict`, and `isinstance(x, Message)` raises `TypeError`. `Protocol` is structural typing: any class with matching methods satisfies it, with no inheritance and no `implements`, exactly like a TypeScript interface. It is how you swap an OpenAI client for an Anthropic one, or a real client for a fake in tests.

   ```python
   from typing import NotRequired, Protocol, TypedDict

   class ToolCall(TypedDict):
       name: str
       arguments: str
       id: NotRequired[str]          # this key may be missing (3.11+)

   class Embedder(Protocol):
       def embed(self, texts: list[str]) -> list[list[float]]: ...

   class FakeEmbedder:               # no base class, still an Embedder
       def embed(self, texts: list[str]) -> list[list[float]]:
           return [[0.0, 1.0] for _ in texts]

   def index_docs(texts: list[str], embedder: Embedder) -> int:
       return len(embedder.embed(texts))
   ```

   Add `@runtime_checkable` to a Protocol if you need `isinstance()` checks; that checks only that the methods exist, not their signatures.

5. **Generics: `TypeVar` and the 3.12 syntax.** A generic function keeps the link between the input type and the output type. Before 3.12 you declared a `TypeVar`; 3.12 added `def f[T](...)`, `class Box[T]:` and the `type` alias statement, which read like TypeScript's `function first<T>(items: T[]): T`.

   ```python
   from typing import TypeVar

   T = TypeVar("T")

   def first_old(items: list[T]) -> T:   # works on 3.5+
       return items[0]

   def first[T](items: list[T]) -> T:    # 3.12+, same meaning, no TypeVar needed
       return items[0]

   type JSONValue = str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]  # 3.12+
   n = first([1, 2, 3])                  # the checker infers int
   ```

6. **`Annotated`: a type plus metadata.** `Annotated[int, something]` is still `int` to the type checker, but libraries can read the extra metadata at runtime. FastAPI reads `Query`, `Path`, `Body` and `Depends` from it. This keeps the default-value slot for real defaults, keeps the function callable as plain Python in tests, and lets you define a dependency once as an alias.

   ```python
   from typing import Annotated
   from fastapi import Depends, FastAPI, Query

   app = FastAPI()

   def get_current_user() -> dict:
       return {"id": 1}

   CurrentUser = Annotated[dict, Depends(get_current_user)]   # define once, reuse everywhere

   @app.get("/search")
   async def search(user: CurrentUser, q: Annotated[str, Query(min_length=2)], limit: int = 10) -> dict:
       return {"user": user["id"], "q": q, "limit": limit}
   ```

   The older style `q: str = Query(min_length=2)` put the metadata in the default slot, so calling `search()` directly passed a `Query` object instead of a string.

7. **Hints are not enforced at runtime.** The interpreter stores hints in `__annotations__` and otherwise ignores them, the same way TypeScript types are erased after compilation. Two different tools close the gap: a static checker (mypy or pyright, in the editor and in CI) rejects the bad call before it runs, and Pydantic validates real data at runtime, converting `"42"` to `42` in its default lax mode or rejecting it in strict mode.

   ```python
   from pydantic import TypeAdapter

   def double(x: int) -> int:
       return x * 2

   print(double("ab"))                            # abab: no error at runtime
   print(double.__annotations__)                  # {'x': <class 'int'>, 'return': <class 'int'>}
   print(TypeAdapter(int).validate_python("42"))  # 42: parsed and checked at runtime
   ```

   ```bash
   uv run --with mypy mypy app/   # like tsc --noEmit: reports double("ab") as an error
   ```

### Concepts you must understand
- `@dataclass` generates `__init__`, `__repr__` and `__eq__` from annotated class attributes; it never validates types.
- Mutable defaults need `field(default_factory=list)`; a bare `[]` or `{}` default is rejected at class definition.
- `frozen=True` gives immutability and a generated `__hash__`, but it is shallow: use tuples inside, and `dataclasses.replace` to copy with changes.
- `order=True` compares fields as a tuple in definition order; `slots=True` (3.10+) saves memory and turns attribute typos into errors.
- Pydantic models at the boundaries (requests, LLM output, settings), dataclasses for internal objects, `TypedDict` for dicts that must stay dicts, `NamedTuple` for small unpackable values.
- A plain `Enum` member never equals its value; `StrEnum` (3.11+) members are strings, so they compare, format and serialize as their value.
- `X | None` (3.10+) is the modern `Optional[X]`: it means "may be None", and only a default value makes an argument optional.
- `Protocol` is structural typing like a TypeScript interface; `TypeVar`, or the 3.12 `def f[T]` syntax, links input and output types.
- `Annotated[T, meta]` is `T` plus metadata that libraries read at runtime; FastAPI reads `Query`, `Path` and `Depends` from it.
- Hints do nothing at runtime: mypy or pyright check them statically, and Pydantic enforces them on real data.

| JavaScript | Python | Note |
| --- | --- | --- |
| `class User { constructor(name, age) {...} }` | `@dataclass` class with `name: str` and `age: int` fields | `__init__`, `__repr__`, `__eq__` generated |
| `{...cfg, temperature: 0.9}` | `dataclasses.replace(cfg, temperature=0.9)` | works on frozen dataclasses |
| `Object.freeze(obj)` | `@dataclass(frozen=True)` | both are shallow |
| `enum Role { User = "user" }` (TS) | `class Role(StrEnum): USER = "user"` | `StrEnum` needs 3.11+ |
| `type Order = "asc" \| "desc"` (TS) | `Literal["asc", "desc"]` | checked statically only |
| `string \| null` | `str \| None` | 3.10+ syntax; `Optional[str]` before |
| `interface Embedder { embed(t: string[]): number[][] }` | `class Embedder(Protocol)` | structural, no `implements` |
| `function first<T>(xs: T[]): T` | `def first[T](xs: list[T]) -> T` | 3.12+; `TypeVar` before |
| `any` / `unknown` | `Any` / `object` | `object` forces a check before use |
| `tsc --noEmit` | `mypy` or `pyright` | static only, nothing at runtime |
| Zod `schema.parse(data)` | Pydantic `Model.model_validate(data)` | runtime validation and coercion |

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** It prints the policy with `'refund'` inside the list, then `FrozenInstanceError`, then `unhashable type: 'list'`. `frozen=True` only blocks rebinding the dataclass's own fields; it does not freeze the list the field points to, and the generated `__hash__` hashes every field, so a list field makes the instance unhashable.

**Deeper explanation:** The code:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Policy:
    name: str
    allowed_tools: list[str] = field(default_factory=list)

p = Policy("support")
p.allowed_tools.append("refund")
print(p)
try:
    p.name = "admin"
except Exception as e:
    print(type(e).__name__)
try:
    hash(p)
except TypeError as e:
    print(e)
```

```text
Policy(name='support', allowed_tools=['refund'])
FrozenInstanceError
unhashable type: 'list'
```

A frozen dataclass replaces `__setattr__` so `p.name = ...` raises `FrozenInstanceError`. `p.allowed_tools.append(...)` never calls `__setattr__` on `p`; it mutates the list object, so it succeeds. With `frozen=True` and the default `eq=True`, the dataclass generates `__hash__` as the hash of a tuple of all fields, and hashing a tuple that contains a list fails. This matters when you cache compiled policies in a dict keyed by the policy: the code crashes only on the first cache lookup.

The fix is to make the inside immutable too:

```python
@dataclass(frozen=True)
class Policy:
    name: str
    allowed_tools: tuple[str, ...] = ()

p = Policy("support", ("refund", "lookup_order"))
cache = {p: "compiled"}   # works
```

**Follow-ups they will ask:**
- How do you normalise a field in `__post_init__` of a frozen dataclass?: Use `object.__setattr__(self, "name", self.name.strip())`, because normal assignment is blocked.
- Is a regular (non-frozen) dataclass hashable?: No. With `eq=True` and not frozen, `__hash__` is set to `None`, because a mutable object whose hash can change would corrupt dicts and sets.
- What would you use for a deeply immutable config?: Tuples and `frozenset` inside a frozen dataclass, or a Pydantic model with `model_config = ConfigDict(frozen=True)`.

**Mistakes to avoid:**
- Saying "frozen makes the object fully immutable": it is shallow, exactly like `Object.freeze` in JavaScript.
- Reaching for `unsafe_hash=True` to silence the error: the hash still breaks as soon as the list changes.

### Q. Write a frozen, ordered `Version` dataclass that parses "1.4.2" so that `sorted()` puts 1.9.0 before 1.10.0.
**Short answer (45 seconds):** Store major, minor and patch as ints in a `@dataclass(frozen=True, order=True)`, so comparisons use the tuple `(major, minor, patch)`. Add a `parse` classmethod that strips an optional `v`, splits on dots, checks there are exactly three numeric parts and builds the instance. Sorting the raw strings is the bug this avoids: `"1.10.0" < "1.9.0"` is `True` character by character.

**Deeper explanation:**

```python
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, text: str) -> "Version":
        parts = text.strip().removeprefix("v").split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"not a version: {text!r}")
        major, minor, patch = (int(p) for p in parts)
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

releases = [Version.parse(s) for s in ["1.10.0", "1.9.0", "v0.9.9"]]
print([str(v) for v in sorted(releases)])   # ['0.9.9', '1.9.0', '1.10.0']
print(max(releases))                        # 1.10.0 (print uses our __str__)
```

`order=True` generates `__lt__` and friends that compare `(self.major, self.minor, self.patch)` with the other instance's tuple, so field order in the class body is the sort order. `frozen=True` makes instances hashable, so you can put them in a set to deduplicate or use them as dict keys. `parse` is a classmethod rather than a staticmethod so that a subclass calling `parse` gets an instance of the subclass. Edge cases: `"1.4"`, `"1.x.2"` and `""` raise `ValueError`; `"01.2.3"` parses to 1.2.3. Sorting is O(n log n) with cheap tuple comparisons.

**Follow-ups they will ask:**
- How would you support "1.0.0-rc1"?: Add a pre-release field and a custom sort key, or use `packaging.version.Version`, which implements the full PEP 440 rules.
- Why not compare strings with a natural-sort key?: It works for this format but hides the parsing; a typed object fails fast on bad input.
- Why `int(p)` after `isdigit()`?: `isdigit()` alone accepts some Unicode digits that `int()` rejects; `int()` is the real check and also raises `ValueError`.

**Mistakes to avoid:**
- Sorting version strings directly, which puts 1.10.0 before 1.9.0.
- Declaring fields in the wrong order (`patch` first), which silently changes the sort order.
- Writing your own `__lt__` and forgetting the other comparison methods, when `order=True` generates all four.

### Q. You are building a RAG chat endpoint. Choose a data container for the incoming request, a retrieved chunk passed between your services, the message list sent to the LLM SDK, and a (start, end) highlight span. Justify each.
**Short answer (45 seconds):** The incoming request is a Pydantic model, because it is untrusted JSON that needs validation, coercion and an OpenAPI schema. The retrieved chunk is a dataclass, because it is trusted internal data and I want a cheap, typed object. The messages are a `TypedDict`, because the SDK wants plain dicts. The span is a `NamedTuple`, because it is tiny, immutable and I want to unpack it.

**Deeper explanation:**

```python
from dataclasses import dataclass
from typing import Literal, NamedTuple, TypedDict
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)

@dataclass(slots=True)
class RetrievedChunk:
    doc_id: str
    text: str
    score: float

class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str

class Span(NamedTuple):
    start: int
    end: int

def build_messages(req: ChatRequest, chunks: list[RetrievedChunk]) -> list[Message]:
    context = "\n\n".join(c.text for c in chunks)
    return [{"role": "system", "content": f"Answer from:\n{context}"},
            {"role": "user", "content": req.message}]
```

The rule is "validate at the edges, trust inside". Pydantic runs validation on every instance, which is exactly what you want once per request and wasteful for thousands of internal objects. A dataclass with `slots=True` is lightweight when you hold hundreds of chunks per request. `TypedDict` gives the type checker the key names and literal roles without converting anything: the list goes to the SDK as-is. `NamedTuple` gives `span.start` readability while still allowing `start, end = span` and tuple equality.

**Follow-ups they will ask:**
- What about the LLM's structured output?: A Pydantic model, because model output is untrusted; validate it and retry or repair on `ValidationError`.
- Why not Pydantic everywhere for consistency?: You can, but it adds validation cost and couples the domain layer to the API schema.
- And the app settings?: `pydantic-settings` `BaseSettings`, which reads and validates environment variables.

**Mistakes to avoid:**
- Using a `TypedDict` for request bodies and assuming the keys were checked: nothing checks them at runtime.
- Passing raw `dict`s between every layer, which loses autocomplete and turns typos into `KeyError` in production.

### Q. A typo "shiped" reached the orders table because statuses are plain strings. Refactor the code with `StrEnum` so this cannot happen again.
**Short answer (45 seconds):** Define `OrderStatus(StrEnum)`, use it as the type in the Pydantic models and FastAPI parameters so bad input gets a 422, and convert database values with `OrderStatus(value)` when reading. Because `StrEnum` members are strings, the database driver, JSON and f-strings keep working unchanged. Then add a database constraint as a second wall and clean the bad rows.

**Deeper explanation:**

```python
from enum import StrEnum, auto
from pydantic import BaseModel

class OrderStatus(StrEnum):
    PENDING = auto()     # "pending"
    PAID = auto()
    SHIPPED = auto()
    CANCELLED = auto()

class StatusUpdate(BaseModel):
    status: OrderStatus  # {"status": "shiped"} now gets a 422 at the API edge

def mark_shipped(order: dict) -> dict:
    return {**order, "status": OrderStatus.SHIPPED}   # no free-typed strings left

def load_status(raw: str) -> OrderStatus:
    return OrderStatus(raw)   # ValueError: 'shiped' is not a valid OrderStatus
```

Steps in order: introduce the enum and replace every literal (`grep -rn '"shipped"'` finds them); type the API models and path parameters with it; then add a database guard such as `CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled'))` or a Postgres enum type, so other writers (scripts, other services) are also blocked. Before adding the constraint, fix existing rows with an `UPDATE ... WHERE status = 'shiped'`, or the migration fails. `StrEnum` matters over plain `Enum`: `OrderStatus.SHIPPED == "shipped"` is `True` and `json.dumps` works, so comparisons with database values and logging do not silently break.

**Follow-ups they will ask:**
- How do you add a new status safely?: Deploy code that can read it first, then widen the database constraint, then start writing it.
- What happens when a legacy row has a bad value?: `OrderStatus(raw)` raises on read, so clean the data in the same migration or map unknown values explicitly.
- Why not `IntEnum` codes?: Strings are readable in SQL, logs and JSON; ints save a few bytes and cost every debugging session.

**Mistakes to avoid:**
- Using `class OrderStatus(Enum)` and then comparing members to raw strings, which is always `False`.
- Using the old `(str, Enum)` mixin and putting members in f-strings, which renders `OrderStatus.SHIPPED`.
- Trusting the API validation alone while cron jobs write to the same table.

### Q. `get_order(order_id: int)` received the string "42" from a hand-parsed query string, and the cache lookup always missed. Find the cause and fix it both at check time and at runtime.
**Short answer (45 seconds):** Python does not enforce type hints, so `"42"` was passed straight through, and in a dict `"42"` and `42` are different keys, so every lookup missed and hit the database. At check time I would run mypy or pyright in CI, which flags passing a `str` where `int` is declared. At runtime I would parse at the boundary: let FastAPI do it by declaring `order_id: int` in the route, or validate with Pydantic.

**Deeper explanation:** The buggy path:

```python
_cache: dict[int, dict] = {42: {"id": 42, "total": 99}}

def get_order(order_id: int) -> dict | None:
    return _cache.get(order_id)

raw = "id=42".split("=")[1]   # hand-rolled parsing returns a str
print(get_order(raw))          # None: "42" != 42 as a dict key
```

Nothing failed loudly: the annotation is metadata only. Running `uv run --with mypy mypy app/` reports `Argument 1 to "get_order" has incompatible type "str"; expected "int"`, which is why the checker belongs in CI next to the tests. For runtime, convert where untrusted data enters:

```python
from fastapi import FastAPI
from pydantic import validate_call

app = FastAPI()

@app.get("/orders/{order_id}")
async def read_order(order_id: int) -> dict | None:   # FastAPI parses "42" -> 42 or answers 422
    return get_order(order_id)

@validate_call                                         # for non-FastAPI entry points
def get_order_checked(order_id: int) -> dict | None:
    return _cache.get(order_id)

print(get_order_checked("42"))   # {'id': 42, 'total': 99}: coerced to int
```

`@validate_call` adds overhead on every call, so use it at entry points such as CLI commands or queue consumers, not on hot inner functions.

**Follow-ups they will ask:**
- Where else does this str-versus-int mismatch bite?: JSON object keys are always strings, Redis returns bytes and environment variables are strings, so convert at every boundary.
- Can you make Pydantic reject "42" instead of coercing it?: Yes, strict mode, for example `Field(strict=True)` or `ConfigDict(strict=True)`.
- mypy or pyright?: Both work; pyright is faster and powers VS Code's Pylance, mypy is the older reference. Pick one and run it in CI.

**Mistakes to avoid:**
- Saying "but it is annotated as int": annotations never convert or check anything at runtime.
- Sprinkling `isinstance` checks through business logic instead of validating once at the boundary.

### Q. Your service calls OpenAI today and must support Anthropic next month. Write a `Protocol` and a generic fallback helper so both clients and a test fake plug in without inheritance.
**Short answer (45 seconds):** Define an `LLMClient` Protocol with the one method the app needs, such as `complete(prompt) -> str`, write thin adapter classes for each vendor SDK that match it, and type the business code against the Protocol only. A fake class with the same method works in tests without mocks. A generic `with_fallback[T]` helper tries the primary call and falls back to the secondary while preserving the return type.

**Deeper explanation:**

```python
from collections.abc import Callable
from typing import Protocol

class LLMClient(Protocol):
    def complete(self, prompt: str, *, max_tokens: int = 512) -> str: ...

class OpenAIClient:                     # adapter around the vendor SDK
    def __init__(self, sdk) -> None:
        self.sdk = sdk
    def complete(self, prompt: str, *, max_tokens: int = 512) -> str:
        resp = self.sdk.chat.completions.create(
            model="gpt-4o-mini", max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content or ""

class FakeLLM:                          # for tests: no base class needed
    def complete(self, prompt: str, *, max_tokens: int = 512) -> str:
        return f"echo: {prompt}"

def with_fallback[T](primary: Callable[[], T], fallback: Callable[[], T]) -> T:   # 3.12+
    try:
        return primary()
    except Exception:
        return fallback()

def summarize(client: LLMClient, text: str) -> str:
    return client.complete(f"Summarize:\n{text}", max_tokens=200)

print(with_fallback(lambda: summarize(FakeLLM(), "doc"), lambda: "unavailable"))
```

A Protocol is checked structurally by mypy or pyright: `summarize(FakeLLM(), ...)` passes because the method signature matches, and a class with a misspelled method fails type checking. That is TypeScript's interface model, unlike an abstract base class, which forces vendor adapters and fakes to inherit. The generic `T` means `with_fallback` returns `str` here and would return `list[float]` for an embedding call, with the checker tracking it. On 3.11 write `T = TypeVar("T")` instead.

**Follow-ups they will ask:**
- Protocol or `abc.ABC`?: Protocol when you do not own the implementations or want fakes without inheritance; ABC when you want shared base behavior and runtime enforcement at instantiation.
- How do you handle streaming?: Add a second Protocol method returning `Iterator[str]` or `AsyncIterator[str]`, and keep vendor event formats inside the adapter.
- Should the fallback catch every exception?: No, only transient ones (timeouts, 429, 5xx); a 400 from a bad prompt will fail on the second provider too.

**Mistakes to avoid:**
- Leaking vendor response objects (`resp.choices[0]`) into business code, which makes the swap a rewrite.
- Mocking the SDK's deep attribute chain in tests instead of passing a small fake that satisfies the Protocol.

### Practice
- Practice kit: open `python-practice/exercises/p13_typing.py`, implement each function, then run `uv run --with pytest pytest tests/test_p13_typing.py` from the `python-practice` folder.
- In the REPL, define a frozen dataclass with a `list` field, call `hash()` on an instance and read the error; switch the field to a `tuple` and try again.
- Define `class A(str, Enum): X = "x"` and `class B(StrEnum): X = "x"`, then compare `f"{A.X}"`, `f"{B.X}"`, `A.X == "x"` and `json.dumps(B.X)`.
- Write a five-line file that calls `double("ab")` on a function annotated `x: int`, run it with `python`, then run `uv run --with mypy mypy file.py` and read the error.

## Iterators & Generators [Core]

> This lesson covers how Python loops over things: the iteration protocol, generator functions with `yield`, generator expressions and the `itertools` toolbox. In AI backends this is how you stream LLM tokens with `StreamingResponse`, read multi-gigabyte JSONL files without running out of memory, batch texts for an embeddings API, walk paginated APIs, and write FastAPI dependencies with `yield` that always close the database session.

### Why it exists
Python wanted one loop syntax that works on lists, files, database cursors, network streams and endless sequences, so `for` is built on a tiny protocol that any object can implement. Building a full list before processing it wastes memory and delays the first result; a generator produces values one at a time, on demand, so memory stays flat and the first item arrives immediately. Before generators you wrote iterator classes with `__iter__` and `__next__` by hand, or loaded everything into lists. The cost: a generator is single-pass, has no `len()` and no indexing, and its errors appear only when someone iterates it.

### In plain words
A list is a printed book: every page exists up front and you can flip anywhere. A generator is a storyteller who tells you the next page only when you ask, and remembers where they stopped. You can listen to an endless story without a bookshelf, but you cannot jump back to page 3 or hear it twice without starting a new storyteller. JavaScript has the same idea in `function*` and `[Symbol.iterator]`, so the shapes will feel familiar.

### Walkthrough: how a for loop really works

1. **`for` calls `iter()` once, then `next()` until `StopIteration`.** Any object whose `__iter__` returns an iterator can be looped over. This `while` loop is what `for item in items` does for you.

   ```python
   items = ["a", "b"]
   it = iter(items)            # calls items.__iter__()
   while True:
       try:
           item = next(it)     # calls it.__next__()
       except StopIteration:   # the "no more items" signal
           break
       print(item)
   ```

   JavaScript uses the same protocol with different names: `[Symbol.iterator]()` returns an object whose `next()` returns `{value, done}`. Python signals the end with an exception instead of `done: true`.

2. **Iterable versus iterator.** An iterable hands out a fresh iterator every time you loop (`list`, `dict`, `str`, `range`). An iterator is the cursor itself: it remembers its position, returns itself from `iter()`, and is used up after one pass.

   ```python
   nums = [1, 2, 3]            # iterable: loop over it as often as you like
   it = iter(nums)             # iterator: one pass only
   print(list(it), list(it))   # [1, 2, 3] []
   print(iter(it) is it)       # True
   ```

3. **Many built-ins return one-shot iterators.** `map`, `filter`, `zip`, `enumerate`, `reversed`, file objects and generators are iterators, unlike JavaScript's `map` and `filter`, which return arrays. A second pass silently yields nothing, with no error.

   ```python
   squares = map(lambda n: n * n, [1, 2, 3, 4])
   print(sum(squares))   # 30
   print(sum(squares))   # 0: already exhausted
   ```

   `range` and dict views (`d.keys()`, `d.items()`) are iterables, not iterators: you can loop over them many times, and `range` also supports `len()` and a fast `in`.

4. **Writing an iterator class by hand.** Implement `__iter__` (return `self`) and `__next__` (return the next value, or raise `StopIteration`).

   ```python
   class Countdown:
       def __init__(self, start: int) -> None:
           self.current = start

       def __iter__(self) -> "Countdown":
           return self

       def __next__(self) -> int:
           if self.current <= 0:
               raise StopIteration
           self.current -= 1
           return self.current + 1

   print(list(Countdown(3)))  # [3, 2, 1]
   ```

5. **Make a collection re-iterable with a generator `__iter__`.** If `__iter__` is a generator (or returns `iter(self.items)`), every loop gets a fresh iterator, which is what you want for a container class.

   ```python
   class Playlist:
       def __init__(self, songs: list[str]) -> None:
           self.songs = songs

       def __iter__(self):
           yield from self.songs   # a new generator per loop

   p = Playlist(["a", "b"])
   print(list(p), list(p))  # ['a', 'b'] ['a', 'b']
   ```

6. **`next()` with a default, and `in` on iterators.** `next(iterator, default)` returns the default instead of raising, which gives you the Python version of JavaScript's `array.find()`. `x in iterator` consumes items until it finds `x`, so the iterator is partly used up afterwards.

   ```python
   users = [{"id": 1}, {"id": 7}, {"id": 9}]
   match = next((u for u in users if u["id"] == 7), None)   # {'id': 7}; stops at the first hit
   missing = next((u for u in users if u["id"] == 3), None)  # None instead of StopIteration
   ```

### Walkthrough: generator functions and lazy pipelines

1. **`yield` turns a function into a generator factory.** Calling it runs nothing and returns a generator object. Each `next()` runs the body up to the next `yield`, hands out the value and freezes the local variables until the next call.

   ```python
   def numbered(lines):
       print("started")
       for i, line in enumerate(lines, start=1):
           yield f"{i}: {line}"

   gen = numbered(["a", "b"])   # nothing printed yet
   print(next(gen))             # prints "started", then "1: a"
   print(next(gen))             # 2: b
   print(next(gen, "done"))     # done: the generator is exhausted
   ```

   This is JavaScript's `function*` without the star: the presence of `yield` anywhere in the body makes it a generator.

2. **`return` ends a generator, and errors arrive late.** A `return value` inside a generator raises `StopIteration` carrying that value, which a `for` loop ignores. Because the body only runs on the first `next()`, a bad argument is not reported when you call the function, only when someone iterates. Validate in a normal wrapper function if you need an immediate error.

   ```python
   def batches(items, size):
       if size < 1:
           raise ValueError("size must be >= 1")
       for i in range(0, len(items), size):
           yield items[i:i + size]

   gen = batches([1, 2, 3], 0)   # no error yet!
   # list(gen)                   # ValueError raised here, far from the bad call
   ```

3. **Generator expressions.** Round brackets instead of square ones give a lazy generator instead of a list. When it is the only argument, you can drop the extra brackets.

   ```python
   import sys

   squares_list = [n * n for n in range(1_000_000)]   # builds a million results now
   squares_gen = (n * n for n in range(1_000_000))    # builds nothing yet
   print(sys.getsizeof(squares_list) > 8_000_000)     # True: about 8 MB of references alone
   print(sys.getsizeof(squares_gen))                  # about 200 bytes, whatever the range
   total = sum(n * n for n in range(1_000_000))       # no extra brackets needed
   ```

4. **Lazy pipelines over huge files.** A file object yields one line at a time, so chaining generators processes a 20 GB log in constant memory: each line flows through every stage before the next line is read.

   ```python
   import json
   from collections.abc import Iterable, Iterator

   def read_jsonl(path: str) -> Iterator[dict]:
       with open(path, encoding="utf-8") as f:
           for line in f:                  # one line in memory at a time
               if line.strip():
                   yield json.loads(line)

   def errors_only(records: Iterable[dict]) -> Iterator[dict]:
       return (r for r in records if r.get("level") == "error")

   for rec in errors_only(read_jsonl("app.log.jsonl")):
       print(rec["msg"])
   ```

   The `with` block stays open while the generator is paused and closes when it finishes or is closed. `f.read()` and `f.readlines()` load the whole file, so never use them on files of unknown size.

5. **`yield from` delegates to another iterable.** It yields every item of a sub-iterable or sub-generator, which keeps recursive traversal short.

   ```python
   def walk(tree: dict):
       yield tree["name"]
       for child in tree.get("children", []):
           yield from walk(child)

   tree = {"name": "root", "children": [{"name": "a"}, {"name": "b", "children": [{"name": "c"}]}]}
   print(list(walk(tree)))  # ['root', 'a', 'b', 'c']
   ```

6. **`send()`, in one short note.** `gen.send(value)` resumes a paused generator and makes the `yield` expression evaluate to `value`, so data flows in as well as out. It was the basis of coroutines before `async`/`await`; you will rarely write it in application code.

   ```python
   def running_avg():
       total, count, avg = 0.0, 0, None
       while True:
           value = yield avg              # receives what send() passes in
           total, count = total + value, count + 1
           avg = total / count

   g = running_avg()
   next(g)                                # prime it: run to the first yield
   print(g.send(10), g.send(20))          # 10.0 15.0
   ```

7. **Cleanup with `try`/`finally` around `yield`.** When a generator is closed early (`gen.close()`, garbage collection after a `break`, or a framework closing it), Python raises `GeneratorExit` at the paused `yield`, so the `finally` block runs. FastAPI dependencies with `yield` rely on exactly this.

   ```python
   def connection():
       print("open")
       try:
           yield "conn"
       finally:
           print("close")

   g = connection()
   next(g)     # open
   g.close()   # close
   ```

### Walkthrough: itertools and generators in FastAPI

1. **`chain`, `islice`, `count` and `cycle`.** `chain` joins iterables without copying them. `islice` slices any iterator lazily, because iterators do not support `[:10]`. `count` is an endless counter and `cycle` repeats a sequence forever, handy for round-robin.

   ```python
   from itertools import chain, count, cycle, islice

   lines = (f"line {i}" for i in count(1))          # endless generator
   print(list(islice(lines, 3)))                    # ['line 1', 'line 2', 'line 3']
   keys = cycle(["key-1", "key-2"])                 # round-robin API keys
   print([next(keys) for _ in range(3)])            # ['key-1', 'key-2', 'key-1']
   print(list(chain([1, 2], (3,), range(4, 6))))    # [1, 2, 3, 4, 5]
   ```

2. **`groupby` groups consecutive runs only.** It starts a new group every time the key changes, so unsorted input splits one key into several groups. Sort by the same key first, or use a `defaultdict(list)` when you do not need streaming.

   ```python
   from itertools import groupby
   from operator import itemgetter

   rows = [("a", 1), ("b", 2), ("a", 3)]
   print([(k, len(list(g))) for k, g in groupby(rows, key=itemgetter(0))])
   # [('a', 1), ('b', 1), ('a', 1)]: 'a' appears twice
   rows.sort(key=itemgetter(0))
   print([(k, len(list(g))) for k, g in groupby(rows, key=itemgetter(0))])
   # [('a', 2), ('b', 1)]
   ```

3. **`product`, `combinations` and `permutations`.** Lazy combinatorics, useful for evaluation grids and test matrices.

   ```python
   from itertools import combinations, permutations, product

   grid = list(product(["model-a", "model-b"], [0.0, 0.7]))   # 4 (model, temperature) pairs
   print(list(combinations("abc", 2)))       # [('a', 'b'), ('a', 'c'), ('b', 'c')]: order ignored
   print(len(list(permutations("abc", 2))))  # 6: order matters
   ```

4. **`accumulate` and `batched` (3.12+).** `accumulate` yields running totals, or a running anything when you pass a function. `batched(iterable, n)` yields tuples of up to `n` items, exactly what you need to send texts to an embeddings API 100 at a time.

   ```python
   from itertools import accumulate, batched

   print(list(accumulate([3, 1, 4])))        # [3, 4, 8]
   print(list(accumulate([3, 1, 4], max)))   # [3, 3, 4]: running max
   print([len(b) for b in batched(range(250), 100)])   # [100, 100, 50]
   ```

   On 3.11 or older, write it yourself: `while batch := list(islice(it, n)): yield batch`, where `it = iter(iterable)`.

5. **FastAPI dependencies with `yield`.** FastAPI runs the dependency up to `yield`, injects the yielded value into your endpoint, and resumes the generator after the endpoint finishes so the code after `yield` cleans up. If the endpoint raises, the exception is raised inside the dependency at the `yield` line, so `except` and `finally` see it.

   ```python
   from collections.abc import Iterator
   from typing import Annotated
   from fastapi import Depends, FastAPI

   app = FastAPI()

   def get_db() -> Iterator[Session]:   # Session, SessionLocal, User: your SQLAlchemy setup
       db = SessionLocal()
       try:
           yield db                     # the endpoint runs while we are paused here
       finally:
           db.close()                   # always runs, even if the endpoint raised

   @app.get("/users/{user_id}")
   def read_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
       return db.get(User, user_id)
   ```

   Express has no direct equivalent; you would open the connection in middleware and close it on `res.on("finish")`.

6. **`StreamingResponse` with a generator.** A generator that yields chunks becomes a response body that is sent as it is produced, which is how LLM tokens reach the browser before the full answer exists. Use an async generator (`async def` plus `yield`, consumed with `async for`) when each chunk comes from an awaited call.

   ```python
   from collections.abc import AsyncIterator
   from fastapi.responses import StreamingResponse

   async def token_stream(prompt: str) -> AsyncIterator[str]:
       async for token in llm.stream(prompt):   # your async LLM client
           yield f"data: {token}\n\n"            # Server-Sent Events framing

   @app.get("/chat")
   async def chat(q: str) -> StreamingResponse:
       return StreamingResponse(token_stream(q), media_type="text/event-stream")
   ```

   The JavaScript parallel is an `async function*` whose chunks you `res.write()` in Express.

### Concepts you must understand
- A `for` loop calls `iter()` once and `next()` until `StopIteration`; implementing that protocol is all an object needs to be loopable.
- An iterable produces fresh iterators (`list`, `dict`, `range`); an iterator is a one-shot cursor that returns itself from `iter()`.
- `map`, `filter`, `zip`, `enumerate`, file objects and generators are one-shot: a second pass silently yields nothing.
- A function containing `yield` returns a generator object; its body runs only when iterated, so its errors surface late too.
- Generators hold one item at a time: memory stays flat whatever the input size, at the cost of no `len()`, no indexing and a single pass.
- `yield from` delegates to a sub-iterable; `send()` pushes a value into a paused generator and is rare in app code.
- A `finally` around `yield` runs when the generator finishes or is closed; FastAPI `yield` dependencies depend on this.
- `itertools` gives lazy building blocks: `islice` for slicing iterators, `chain`, `groupby` (consecutive keys only), `batched` (3.12+), `accumulate` and the combinatorics functions.
- Async generators (`async def` plus `yield`) feed `async for` and `StreamingResponse` for token streaming.

| JavaScript | Python | Note |
| --- | --- | --- |
| `obj[Symbol.iterator]()` | `iter(obj)`, which calls `obj.__iter__()` | same protocol, different names |
| `it.next()` returns `{value, done}` | `next(it)` returns the value or raises `StopIteration` | `next(it, default)` avoids the exception |
| `function* gen() { yield 1 }` | `def gen(): yield 1` | no star: `yield` makes it a generator |
| `yield* other` | `yield from other` | delegates to a sub-iterable |
| `async function*` with `for await` | `async def` with `yield`, consumed by `async for` | used for token streaming |
| `arr.map(f)` returns an array | `map(f, xs)` returns a one-shot iterator | wrap in `list()` to reuse it |
| `arr.find(pred)` | `next((x for x in xs if pred(x)), None)` | lazy, stops at the first hit |
| `arr.slice(0, 10)` | `list(islice(it, 10))` | iterators have no `[:10]` |
| `arr.flat(Infinity)` | a recursive generator with `yield from` | |
| lodash `_.chunk(arr, 100)` | `itertools.batched(xs, 100)` | 3.12+, yields tuples |
| Node `readline` over a file stream | `for line in open(path)` | lazy, line by line |

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** It prints `True`, then `[4, 6]`, then `[]`, then `{'a': 1, 'b': 2} {}`. The generator and the `zip` object are one-shot iterators: `2 in evens` consumes items up to and including 2, the first `list()` drains the rest, and every later pass sees an exhausted iterator. `zip` also stops at the shortest input.

**Deeper explanation:** The code:

```python
nums = [1, 2, 3, 4, 6]
evens = (n for n in nums if n % 2 == 0)
print(2 in evens)
print(list(evens))
print(list(evens))

pairs = zip(["a", "b", "c"], [1, 2])
print(dict(pairs), dict(pairs))
```

```text
True
[4, 6]
[]
{'a': 1, 'b': 2} {}
```

`in` on an iterator calls `next()` until it finds a match, so after `2 in evens` the generator has already produced (and discarded) 2. `list(evens)` collects what is left, `[4, 6]`, and the second `list(evens)` gets nothing because a finished generator stays finished. No exception is raised: an exhausted iterator just looks empty, which is why this bug hides well. `zip` pairs items until the shortest input runs out, so `"c"` is dropped silently, and it is also a one-shot iterator, so the second `dict(pairs)` is empty.

In JavaScript, `nums.filter(...)` returns an array, so code ported from JS often assumes it can loop twice. The fixes: materialize once with `evens = [n for n in nums if n % 2 == 0]` when you need several passes, and use `zip(a, b, strict=True)` (3.10+) to get `ValueError: zip() argument 2 is shorter than argument 1` instead of silent truncation.

**Follow-ups they will ask:**
- How can a function protect itself from receiving an exhausted iterator?: Accept an `Iterable`, call `list()` once at the top if it needs several passes, or document that it is single-pass.
- Is `range(5)` exhausted after one loop?: No, `range` is a lazy iterable, not an iterator; each loop gets a new iterator.
- How do you loop twice over one iterator without storing it all?: `itertools.tee`, which buffers what one copy has read and the other has not.

**Mistakes to avoid:**
- Expecting an error on the second pass: an exhausted iterator quietly produces nothing.
- Using `zip` on lists that should be equal length without `strict=True`, which hides data loss.

### Q. A FastAPI endpoint loads a 6 GB JSONL file into a list before embedding it, and the pod is OOM-killed. Refactor it to stream with generators and batch the API calls.
**Short answer (45 seconds):** Read the file line by line with a generator, batch the records with `itertools.batched`, embed and upsert one batch at a time, so memory holds one batch instead of the whole file. Then move the job out of the request into a background worker, because a 6 GB reindex will outlive any HTTP timeout anyway.

**Deeper explanation:** The failing version builds two full copies in memory and makes one giant call:

```python
@app.post("/reindex")
def reindex():
    with open("docs.jsonl") as f:
        docs = [json.loads(line) for line in f]        # every parsed dict in RAM
    texts = [d["text"] for d in docs]                  # another full list
    store.upsert(zip([d["id"] for d in docs], embed(texts)))
```

The streaming version:

```python
import json
from collections.abc import Iterator
from itertools import batched   # 3.12+

def read_jsonl(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def reindex(path: str, batch_size: int = 100) -> int:
    done = 0
    for batch in batched(read_jsonl(path), batch_size):
        vectors = embed([doc["text"] for doc in batch])         # one API call per batch
        store.upsert([(doc["id"], vec) for doc, vec in zip(batch, vectors, strict=True)])
        done += len(batch)
    return done
```

Memory is now O(batch_size) instead of O(file size): the file object reads one line at a time, `batched` holds 100 records, and each batch is garbage once upserted. Embedding APIs cap inputs per request, so batching is required anyway. `strict=True` makes a vector-count mismatch fail loudly instead of attaching vectors to the wrong documents. Finally, trigger it from the endpoint with a job queue (Celery, RQ, Arq) or at least `BackgroundTasks`, and return a job id.

**Follow-ups they will ask:**
- How do you resume after a crash halfway?: Record the last processed line number or document id after each batch, and skip with `islice(read_jsonl(path), start, None)` on restart.
- How would you speed it up?: Run several batches concurrently with an async client and an `asyncio.Semaphore` capped below the provider's rate limit.
- How do you confirm the fix?: Watch the container's memory metric during a run; it should be flat rather than climbing with the file.

**Mistakes to avoid:**
- Calling `f.readlines()` or building list comprehensions where a generator would do.
- Keeping a long job inside the request handler, where client and proxy timeouts kill it.

### Q. Write a generator that walks a cursor-paginated API and yields every item, fetching each page only when the caller needs it.
**Short answer (45 seconds):** Keep a cursor variable starting at `None`, loop: fetch a page, `yield from` its items, read `next_cursor`, and stop when it is `None`. Because it is a generator, the next page is requested only after the caller has consumed the current one, so `islice(paginate(...), 10)` makes one request instead of fifty.

**Deeper explanation:**

```python
from collections.abc import Iterator
import httpx

def paginate(client: httpx.Client, url: str, page_size: int = 100) -> Iterator[dict]:
    cursor: str | None = None
    seen: set[str] = set()
    while True:
        params = {"limit": page_size} | ({"cursor": cursor} if cursor else {})
        resp = client.get(url, params=params)
        resp.raise_for_status()
        page = resp.json()
        yield from page["items"]
        cursor = page.get("next_cursor")
        if cursor is None:
            return
        if cursor in seen:                    # guard against a buggy API looping forever
            raise RuntimeError(f"cursor repeated: {cursor}")
        seen.add(cursor)

with httpx.Client(base_url="https://api.example.com", timeout=10) as client:
    for customer in paginate(client, "/customers"):
        if customer["email"].endswith("@test.com"):
            break                             # remaining pages are never requested
```

The caller sees a flat stream of items and never deals with cursors. Laziness gives early exit for free, and memory holds a single page. The code handles an empty page with a non-null cursor correctly because `yield from []` yields nothing and the loop continues. Complexity is O(total items) with one request per page.

The async version is the same shape with `async def`, `await client.get(...)` and `yield` items in a loop (`yield from` is not allowed in async generators), consumed with `async for`.

**Follow-ups they will ask:**
- How do you handle 429 rate limits?: Wrap the `client.get` in a retry with backoff that honours the `Retry-After` header.
- What if the caller wants pages, not items?: Yield `page["items"]` instead, or expose both via a small class with `pages()` and `__iter__`.
- How do you test it?: Pass a fake fetch function or an `httpx.MockTransport` that serves canned pages, and assert the request count.

**Mistakes to avoid:**
- Collecting every page into a list before returning, which loses streaming and early exit.
- Recursing once per page, which hits the recursion limit on large datasets.

### Q. This report groups orders by customer with `itertools.groupby`, and Acme's total comes out as 40 instead of 160. Find and fix the bug.
**Short answer (45 seconds):** `groupby` only groups consecutive items with the same key, and the orders are not sorted by customer, so Acme forms two separate groups. The dict comprehension then overwrites Acme's first total with the second. Sort by the same key first, or skip `groupby` and accumulate into a `defaultdict` or `Counter`, which does not care about order.

**Deeper explanation:** The buggy code:

```python
from itertools import groupby

orders = [
    {"customer": "acme", "total": 120},
    {"customer": "globex", "total": 80},
    {"customer": "acme", "total": 40},
]
report = {c: sum(o["total"] for o in grp) for c, grp in groupby(orders, key=lambda o: o["customer"])}
print(report)   # {'acme': 40, 'globex': 80}
```

`groupby` walks the input once and starts a new group whenever the key changes: acme, then globex, then acme again. The comprehension assigns `report["acme"] = 120` and later `report["acme"] = 40`. Two correct versions:

```python
from collections import defaultdict
from operator import itemgetter

by_customer = itemgetter("customer")
report = {c: sum(o["total"] for o in grp)
          for c, grp in groupby(sorted(orders, key=by_customer), key=by_customer)}

totals: defaultdict[str, int] = defaultdict(int)   # no sorting needed, O(n)
for order in orders:
    totals[order["customer"]] += order["total"]
print(report, dict(totals))   # {'acme': 160, 'globex': 80} {'acme': 160, 'globex': 80}
```

Sorting costs O(n log n); the `defaultdict` version is O(n) and is the better default for in-memory data. `groupby` shines when the data already arrives sorted, such as rows from `ORDER BY customer_id`, because it then groups a stream without holding it all.

**Follow-ups they will ask:**
- Why does `list(groupby(...))` give empty groups?: Each group shares the underlying iterator, so advancing `groupby` invalidates the previous group; consume each group before moving on.
- Where should this aggregation live in production?: In SQL, `SELECT customer, SUM(total) FROM orders GROUP BY customer`, unless the data is already in memory.
- How would you also count orders?: Accumulate a small dataclass or a `(count, total)` tuple per key.

**Mistakes to avoid:**
- Treating `groupby` like SQL `GROUP BY` or lodash `groupBy`: it is "group consecutive runs".
- Sorting by one key and grouping by another, which reintroduces the split.

### Q. Rewrite this JavaScript iterator code in idiomatic Python.
**Short answer (45 seconds):** The JavaScript defines an iterable range class with a generator `[Symbol.iterator]` and a `take` generator. In Python the class becomes `__iter__` written as a generator, and `take` is just `itertools.islice`. For plain numeric ranges the idiomatic answer is the built-in `range`, which already does this lazily.

**Deeper explanation:** The JavaScript:

```js
class Range {
  constructor(start, end, step = 1) { Object.assign(this, { start, end, step }); }
  *[Symbol.iterator]() {
    for (let i = this.start; i < this.end; i += this.step) yield i;
  }
}
function* take(n, iterable) {
  let i = 0;
  for (const x of iterable) { if (i++ >= n) return; yield x; }
}
console.log([...take(3, new Range(0, 100, 10))]);   // [0, 10, 20]
```

The Python:

```python
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import islice

@dataclass(frozen=True)
class FloatRange:                      # justified only for what range() cannot do: floats
    start: float
    end: float
    step: float = 1.0

    def __iter__(self) -> Iterator[float]:
        value = self.start
        while value < self.end:
            yield value
            value += self.step

print(list(islice(range(0, 100, 10), 3)))          # [0, 10, 20]
print(list(islice(FloatRange(0, 1, 0.25), 3)))     # [0, 0.25, 0.5]
```

`*[Symbol.iterator]()` maps to a generator `__iter__`, so every `for` loop gets a fresh generator and the object stays re-iterable. Spread `[...x]` maps to `list(x)`. `take` maps to `islice`, which also stops without pulling an extra item from the source, whereas the JS `take` reads one item past `n` before returning. Python's built-in `range` is a lazy, re-iterable sequence that supports `len()`, `in` and indexing, so writing a class for integer ranges would be un-Pythonic. A dataclass removes the `Object.assign` constructor.

**Follow-ups they will ask:**
- Why does floating step drift matter?: Repeated `+= 0.1` accumulates rounding error; compute `start + i * step` from a counter instead.
- How would you make `take` generic yourself?: `def take(n, it): return islice(it, n)`, typed with a `TypeVar` or `def take[T](n: int, it: Iterable[T]) -> Iterator[T]`.
- Can a Python class support `len()` too?: Yes, add `__len__`; generators themselves never support it.

**Mistakes to avoid:**
- Porting `take` line by line with a manual counter instead of using `islice`.
- Making `__iter__` return `self` on a container, which turns it into a one-shot iterator.

### Q. Write a FastAPI dependency that opens a database session per request, commits on success, rolls back on any error and always closes it.
**Short answer (45 seconds):** Write a generator dependency: create the session, `yield` it inside `try`, commit after the `yield`, roll back and re-raise in `except`, close in `finally`. FastAPI runs the code before `yield`, injects the session, runs the endpoint, then resumes the generator; an exception from the endpoint is raised at the `yield` line, which is what triggers the rollback.

**Deeper explanation:**

```python
from collections.abc import Iterator
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session, sessionmaker

SessionLocal = sessionmaker(bind=engine)   # engine created at startup
app = FastAPI()

def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session          # endpoint runs here
        session.commit()       # only reached if the endpoint did not raise
    except Exception:
        session.rollback()
        raise                  # re-raise so FastAPI still returns the error response
    finally:
        session.close()        # returns the connection to the pool

SessionDep = Annotated[Session, Depends(get_session)]

@app.post("/orders")
def create_order(payload: OrderIn, db: SessionDep) -> dict:
    order = Order(**payload.model_dump())
    db.add(order)
    db.flush()                 # get the generated id inside the transaction
    return {"id": order.id}
```

This is the generator cleanup rule from the walkthrough: the code after `yield` behaves like the exit half of a context manager, and FastAPI wraps the generator in one for you. The same function works outside FastAPI with `contextlib.contextmanager(get_session)`, which is handy in scripts and tests. Inside one request, FastAPI caches a dependency's value, so two dependencies that both need `SessionDep` share one session and one transaction.

The async version is identical with `async def`, `AsyncIterator[AsyncSession]` and `await session.commit()`.

**Follow-ups they will ask:**
- Should the commit live in the dependency?: Many teams commit explicitly in the service layer so a failed commit becomes a clear error before the response is built; the dependency then only rolls back and closes.
- What about `BackgroundTasks` that need the database?: Open a new session inside the task; the request's session belongs to the request.
- How do you test endpoints with a test database?: `app.dependency_overrides[get_session] = get_test_session`.

**Mistakes to avoid:**
- Catching the exception without re-raising, which hides the failure from FastAPI and the client.
- Using `return SessionLocal()` instead of `yield`, which leaks a connection per request until the pool is exhausted.

### Practice
- Practice kit: open `python-practice/exercises/p14_generators.py`, implement each function, then run `uv run --with pytest pytest tests/test_p14_generators.py` from the `python-practice` folder.
- In the REPL, run `it = iter([1, 2, 3])`, call `next(it)` four times and read the `StopIteration`, then try `next(it, "done")`.
- Write a generator that yields Fibonacci numbers forever, then print the first 15 with `islice` and the first one above 1000 with `next()` and a generator expression.
- Write a 200,000-line file in a loop, then use `tracemalloc` (`start()`, then `get_traced_memory()` for the peak) to compare `sum(1 for _ in open(path))` with `len(open(path).readlines())`.

## Decorators & Context Managers [Core]

> This lesson covers decorators (functions that wrap or register other functions) and context managers (objects that guarantee setup and cleanup around a block). In FastAPI and AI backends you use them constantly: `@app.get` registers routes, `@lru_cache` caches the settings object, `@property` and `@classmethod` shape models, retry and timing decorators wrap LLM calls, and `with` / `async with` manage files, database transactions, locks, HTTP clients and the app's `lifespan`.

### Why it exists
Cross-cutting behavior such as logging, timing, caching, retries and auth would otherwise be copy-pasted into every function; a decorator adds it in one line without touching the function body. Resources such as files, connections and locks must be released even when an exception flies, and hand-written `try`/`finally` blocks get forgotten; a context manager packages that cleanup so `with` makes it automatic. In JavaScript you get the same effect with higher-order functions (`withRetry(fn)`) and `try`/`finally`; Python gives both a dedicated syntax. The cost: behavior becomes less visible at the call site, stack traces gain extra frames, and a careless decorator hides the wrapped function's name and signature.

### In plain words
A decorator is gift wrapping: the same gift is inside, but the wrapping adds something before you reach it and after. A context manager is a hotel key card: checking in gives you the room, and checkout happens automatically when you leave, even if you leave in a hurry. Writing `@timed` above a function says "wrap this one". Writing `with open(path) as f:` says "give me the file, and close it no matter how this block ends".

### Walkthrough: from higher-order function to decorator

1. **Functions are objects.** You can assign them, pass them, return them, store them in dicts and even add attributes to them, exactly as in JavaScript.

   ```python
   def shout(text: str) -> str:
       return text.upper()

   handlers = {"loud": shout}           # stored in a dict
   speak = shout                        # assigned to another name
   print(handlers["loud"]("hi"), speak.__name__)   # HI shout
   ```

2. **A decorator is a function that takes a function and returns a function.** The `@` line is pure syntax: `@log_calls` above `def f` means `f = log_calls(f)`. It runs once, when the module is imported, not on every call.

   ```python
   def log_calls(func):
       def wrapper(*args, **kwargs):           # accept any signature
           print(f"calling {func.__name__}")
           return func(*args, **kwargs)        # forward everything, return the result
       return wrapper

   @log_calls
   def add(a: int, b: int) -> int:
       return a + b

   print(add(2, 3))   # calling add, then 5
   ```

   In JavaScript this is `const add = logCalls((a, b) => a + b)`. Forgetting the `return` inside `wrapper` is the most common bug: every decorated call then returns `None`.

3. **`functools.wraps` keeps the identity.** Without it, `add.__name__` is `"wrapper"`, the docstring is gone, and `inspect.signature(add)` shows `(*args, **kwargs)`. `wraps` copies the name, docstring and module and sets `__wrapped__`, which `inspect.signature` follows, so FastAPI, pytest and your logs still see the real function.

   ```python
   import functools

   def log_calls(func):
       @functools.wraps(func)
       def wrapper(*args, **kwargs):
           print(f"calling {func.__name__}")
           return func(*args, **kwargs)
       return wrapper
   ```

4. **Decorators with arguments are factories.** `@retry(times=3)` first calls `retry(times=3)`, which must return the real decorator. That gives three levels: factory, decorator, wrapper.

   ```python
   def repeat(times: int):
       def decorator(func):
           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               return [func(*args, **kwargs) for _ in range(times)]
           return wrapper
       return decorator

   @repeat(times=2)
   def ping() -> str:
       return "pong"

   print(ping())   # ['pong', 'pong']
   ```

5. **Stacking order.** Decorators apply bottom-up (the one closest to `def` wraps first) and run top-down at call time, like Express middleware: the top decorator is the outermost layer.

   ```python
   @log_calls        # applied second, runs first
   @repeat(times=2)  # applied first, runs second
   def hello() -> str:
       return "hi"
   # same as: hello = log_calls(repeat(times=2)(hello))
   ```

6. **Class-based decorators for state.** A class with `__call__` can act as a decorator and keep state in attributes. `functools.update_wrapper` is the class equivalent of `@wraps`. (Used on methods, a class-based decorator also needs `__get__`, so prefer functions there.)

   ```python
   import functools

   class CountCalls:
       def __init__(self, func):
           functools.update_wrapper(self, func)
           self.func = func
           self.calls = 0

       def __call__(self, *args, **kwargs):
           self.calls += 1
           return self.func(*args, **kwargs)

   @CountCalls
   def greet(name: str) -> str:
       return f"hi {name}"

   greet("a"); greet("b")
   print(greet.calls)   # 2
   ```

7. **Decorating `async def` functions.** A sync wrapper around a coroutine function only wraps the creation of the coroutine, which returns instantly. The wrapper must be `async def` and `await` the call. `inspect.iscoroutinefunction` tells you which kind you received.

   ```python
   import functools, inspect, time

   def timed(func):
       if inspect.iscoroutinefunction(func):
           @functools.wraps(func)
           async def async_wrapper(*args, **kwargs):
               start = time.perf_counter()
               try:
                   return await func(*args, **kwargs)
               finally:
                   print(f"{func.__name__}: {time.perf_counter() - start:.3f}s")
           return async_wrapper

       @functools.wraps(func)
       def wrapper(*args, **kwargs):
           start = time.perf_counter()
           try:
               return func(*args, **kwargs)
           finally:
               print(f"{func.__name__}: {time.perf_counter() - start:.3f}s")
       return wrapper
   ```

### Walkthrough: decorators you already use

1. **`functools.lru_cache` and `functools.cache`.** They memoize a function by its arguments. `lru_cache(maxsize=128)` evicts the least recently used entries; `cache` (3.9+) is unbounded. Arguments must be hashable (a `list` argument raises `TypeError: unhashable type: 'list'`), the cache lives in each worker process's memory, and `func.cache_info()` and `func.cache_clear()` help in tests. FastAPI's docs use it to build the settings object once.

   ```python
   from functools import lru_cache
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       openai_api_key: str
       model: str = "gpt-4o-mini"

   @lru_cache
   def get_settings() -> Settings:
       return Settings()          # reads the environment once per process
   ```

   Avoid `lru_cache` on instance methods: `self` becomes part of the key, so the cache keeps every instance alive.

2. **`@property`.** Turns a method into a computed attribute, with an optional setter for validation. It is JavaScript's `get fullName()` and `set fullName(v)`.

   ```python
   class Usage:
       def __init__(self, prompt_tokens: int, completion_tokens: int) -> None:
           self.prompt_tokens = prompt_tokens
           self.completion_tokens = completion_tokens

       @property
       def total(self) -> int:
           return self.prompt_tokens + self.completion_tokens

   print(Usage(120, 30).total)   # 150, no parentheses
   ```

3. **`@classmethod` and `@staticmethod`.** A classmethod receives the class as `cls`, which makes it the standard way to write alternative constructors that also work for subclasses. A staticmethod receives nothing; it is a plain function namespaced in the class.

   ```python
   class Document:
       def __init__(self, doc_id: str, text: str) -> None:
           self.doc_id, self.text = doc_id, text

       @classmethod
       def from_dict(cls, data: dict) -> "Document":
           return cls(data["id"], data["text"])

       @staticmethod
       def normalise(text: str) -> str:
           return " ".join(text.split())

   doc = Document.from_dict({"id": "d1", "text": "hello"})
   ```

4. **How `@app.get` registers a route.** It is a decorator factory: `app.get("/health")` returns a decorator that stores your function in the router's route table and returns the function unchanged. That is why you can still call the endpoint function directly in a unit test. Here is the idea in ten lines:

   ```python
   class Router:
       def __init__(self) -> None:
           self.routes: dict[tuple[str, str], object] = {}

       def get(self, path: str):
           def decorator(func):
               self.routes[("GET", path)] = func   # register
               return func                         # unchanged
           return decorator

   router = Router()

   @router.get("/health")
   def health() -> dict:
       return {"ok": True}
   ```

   Express writes the same registration as `app.get("/health", handler)`. FastAPI also reads the function's signature and type hints at registration time to build validation and the OpenAPI schema.

5. **A retry decorator.** Retry only transient errors, back off exponentially with jitter, and re-raise the last error when attempts run out. In production code the `tenacity` library provides this with more options.

   ```python
   import functools, random, time

   def retry(times: int = 3, base_delay: float = 0.5, exceptions: tuple[type[Exception], ...] = (Exception,)):
       def decorator(func):
           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               for attempt in range(1, times + 1):
                   try:
                       return func(*args, **kwargs)
                   except exceptions:
                       if attempt == times:
                           raise
                       delay = base_delay * 2 ** (attempt - 1)
                       time.sleep(delay + random.uniform(0, delay))
           return wrapper
       return decorator
   ```

### Walkthrough: context managers

1. **The `with` statement.** `with` calls `__enter__` on entry, binds its return value to the `as` name, and calls `__exit__` on the way out, whether the block finished, returned early or raised. It is a reusable `try`/`finally`.

   ```python
   with open("notes.txt", "w", encoding="utf-8") as f:
       f.write("hello")
   # f is closed here, even if write() had raised

   # roughly what Python does for you:
   f = open("notes.txt", "w", encoding="utf-8")
   try:
       f.write("hello")
   finally:
       f.close()
   ```

   JavaScript has `try`/`finally` and, in newer runtimes, `using` declarations for the same purpose.

2. **Writing one with `__enter__` and `__exit__`.** `__exit__(exc_type, exc, tb)` receives the exception, or three `None`s if there was none. Returning a truthy value swallows the exception, which you almost never want, so return `False` or `None`.

   ```python
   import time

   class Timer:
       def __enter__(self) -> "Timer":
           self.start = time.perf_counter()
           return self

       def __exit__(self, exc_type, exc, tb) -> bool:
           self.elapsed = time.perf_counter() - self.start
           return False                  # let exceptions propagate

   with Timer() as t:
       sum(range(1_000_000))
   print(f"{t.elapsed:.4f}s")
   ```

3. **`contextlib.contextmanager`.** A generator with one `yield` inside `try`/`finally` becomes a context manager: code before `yield` is the enter half, the yielded value is what `as` receives, and `finally` is the exit half. This is the same shape as a FastAPI `yield` dependency.

   ```python
   import os
   from contextlib import contextmanager

   @contextmanager
   def working_dir(path: str):
       old = os.getcwd()
       os.chdir(path)
       try:
           yield path
       finally:
           os.chdir(old)          # restored even if the block raised

   with working_dir("/tmp"):
       print(os.getcwd())
   ```

4. **`contextlib.suppress` for expected errors.** It replaces a `try`/`except SomeError: pass` that is genuinely intended, and makes the intent explicit.

   ```python
   import os
   from contextlib import suppress

   with suppress(FileNotFoundError):
       os.remove("cache.tmp")     # fine if it was already gone
   ```

5. **Several managers, and `ExitStack` for a dynamic number.** One `with` can hold several managers, closed in reverse order. When the count is only known at runtime, `ExitStack` collects them and closes them all.

   ```python
   from contextlib import ExitStack

   with open("in.txt", encoding="utf-8") as src, open("out.txt", "w", encoding="utf-8") as dst:
       dst.write(src.read().upper())

   paths = ["a.txt", "b.txt"]
   with ExitStack() as stack:
       files = [stack.enter_context(open(p, "w", encoding="utf-8")) for p in paths]
       for f in files:
           f.write("x")
   # every file is closed here, even if opening the second one failed
   ```

6. **Async context managers, in one note.** `async with` calls `await __aenter__()` and `await __aexit__()`, so setup and cleanup can await I/O; `@contextlib.asynccontextmanager` is the generator shortcut. You meet them with `httpx.AsyncClient`, async database sessions, `asyncio.Lock` and FastAPI's `lifespan`.

   ```python
   from contextlib import asynccontextmanager
   import httpx
   from fastapi import FastAPI

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       app.state.http = httpx.AsyncClient(timeout=10)   # startup
       yield
       await app.state.http.aclose()                    # shutdown

   app = FastAPI(lifespan=lifespan)
   ```

### Concepts you must understand
- Functions are objects: they can be passed, returned, stored and given attributes, which is all a decorator needs.
- `@deco` above `def f` means `f = deco(f)`, executed once at import time, not on each call.
- A wrapper accepts `*args, **kwargs`, calls the original and returns its result; a missing `return` turns every result into `None`.
- `functools.wraps` copies `__name__` and `__doc__` and sets `__wrapped__`, which `inspect.signature` follows, so FastAPI still sees the real parameters.
- `@deco(arg)` needs a factory: a function that takes the arguments and returns the real decorator, three levels deep.
- Stacked decorators apply bottom-up and run top-down; a route-registering decorator like `@app.get` must be the top one.
- A decorator around an `async def` must itself be `async def` and `await` the call, or it only wraps coroutine creation.
- `lru_cache` and `cache` memoize by arguments, need hashable arguments, and keep their cache per process.
- `with` guarantees `__exit__` runs; a truthy return from `__exit__` swallows the exception, so return `False`.
- `@contextmanager` turns a `try`/`yield`/`finally` generator into a context manager; `ExitStack` handles a dynamic number of them; `async with` awaits `__aenter__` and `__aexit__`.

| JavaScript | Python | Note |
| --- | --- | --- |
| `const f2 = withLogging(f)` | `@with_logging` above `def f` | same idea, dedicated syntax |
| TS decorators (`@Injectable()` in NestJS) | `@decorator` | Python decorators are plain functions |
| `fn.name` | `func.__name__` | lost without `functools.wraps` |
| Express `app.get("/x", handler)` | `@app.get("/x")` | registers and returns the function |
| lodash `_.memoize(fn)` | `@functools.cache` or `@lru_cache(maxsize=...)` | hashable arguments only |
| `get total() {}` | `@property` | computed attribute |
| `static fromJSON(data)` | `@classmethod def from_dict(cls, data)` | receives the class, works for subclasses |
| `try { ... } finally { f.close() }` | `with open(p) as f:` | cleanup is automatic |
| `using res = getResource()` | `with get_resource() as res:` | newer JS runtimes only |
| `await using` | `async with` | async setup and cleanup |
| Express middleware order | decorator stacking order | the top layer runs first |

### Q. Write a `@timed` decorator that logs how long a function took, keeps the function's name and signature, and works on both sync and async functions.
**Short answer (45 seconds):** Check `inspect.iscoroutinefunction(func)` once at decoration time and return either an `async def` wrapper that awaits the call or a normal wrapper. Both measure with `time.perf_counter()` inside `try`/`finally`, so failures are timed too, and both use `functools.wraps` so the name and signature survive for logs and for FastAPI.

**Deeper explanation:**

```python
import functools, inspect, logging, time
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    name = func.__qualname__

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                log.info("%s took %.1f ms", name, (time.perf_counter() - start) * 1000)
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            log.info("%s took %.1f ms", name, (time.perf_counter() - start) * 1000)
    return wrapper

@timed
async def call_llm(prompt: str) -> str:
    ...
```

`perf_counter` is a monotonic high-resolution clock, so it cannot jump when NTP adjusts the wall clock, unlike `time.time()`. `finally` logs even when the call raises, which is exactly when latency matters. The logging call uses `%s` arguments so the string is only formatted if the log level is enabled. The branch happens once, at decoration time, not on every call. A sync wrapper around an async function would report a few microseconds, because calling a coroutine function only creates the coroutine; the real work happens later when it is awaited.

**Follow-ups they will ask:**
- How do you keep precise types?: Use `ParamSpec`: in 3.12, `def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]`, so checkers keep the parameter list.
- Where should the number go in production?: A Prometheus histogram or an OpenTelemetry span, not only a log line.
- How do you add a threshold argument, like "only log above 500 ms"?: Turn it into a factory, `@timed(threshold_ms=500)`, one more nesting level.

**Mistakes to avoid:**
- Wrapping `async def` functions with a sync wrapper and trusting the near-zero timings.
- Using `time.time()` for durations, or logging only on success.

### Q. Calls to an LLM API fail with intermittent `httpx.ReadTimeout` and 429 responses. Write a `@retry` decorator with exponential backoff and explain what it must not retry.
**Short answer (45 seconds):** Write a decorator factory `retry(times, base_delay, exceptions)` whose wrapper loops over attempts, returns on success, catches only the listed transient exceptions, sleeps `base_delay * 2 ** (attempt - 1)` plus random jitter, and re-raises the last error. It must not retry client errors like 400 or 401, and it must not blindly retry non-idempotent writes.

**Deeper explanation:**

```python
import asyncio, functools, random
import httpx

class RetryableStatus(Exception):
    pass

def retry(times: int = 4, base_delay: float = 0.5,
          exceptions: tuple[type[Exception], ...] = (httpx.TimeoutException, httpx.ConnectError, RetryableStatus)):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise                       # keeps the original traceback
                    delay = base_delay * 2 ** (attempt - 1)
                    await asyncio.sleep(delay + random.uniform(0, delay))   # jitter
        return wrapper
    return decorator

@retry(times=4)
async def complete(client: httpx.AsyncClient, payload: dict) -> dict:
    resp = await client.post("/v1/chat/completions", json=payload)
    if resp.status_code == 429 or resp.status_code >= 500:
        raise RetryableStatus(resp.status_code)
    resp.raise_for_status()                         # 400/401/403 fail immediately
    return resp.json()
```

Exponential backoff gives the provider room to recover, and jitter stops a fleet of workers from retrying in lockstep. The exception tuple is the safety valve: a `KeyError` from a bug or a 400 from a bad prompt fails at once instead of burning four attempts. The async version uses `await asyncio.sleep`, because `time.sleep` would block the whole event loop. For a 429, a better version reads the `Retry-After` header and waits that long. For a write such as "create payment", retry only with an idempotency key the server deduplicates on.

**Follow-ups they will ask:**
- Would you write this yourself in production?: Usually `tenacity` (`stop_after_attempt`, `wait_random_exponential`, `retry_if_exception_type`); the hand-written version shows you understand it.
- How do retries interact with timeouts?: Set a total deadline too, or four attempts with a 30-second timeout can keep a user waiting two minutes.
- How do you stop retry storms during an outage?: A circuit breaker that fails fast after repeated failures, plus metrics on retry counts.

**Mistakes to avoid:**
- Writing `@retry` without parentheses on a factory: `retry(func)` treats the function as `times` and returns the inner decorator, so a call either returns a function object instead of a result or fails with a confusing `TypeError`, and the API is never called.
- Catching `Exception`, which retries programming errors and validation failures.

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** The two factory lines print first, top to bottom, then the decorators are applied bottom-up (`log` first, then `auth`), all before `--- calling`. At call time the outermost wrapper runs first, so you see enter auth, enter log, the body, exit log, exit auth. Decoration happens once at import; wrapping order is the onion model.

**Deeper explanation:** The code:

```python
def tag(name):
    print(f"factory {name}")
    def decorator(func):
        print(f"decorate {name}")
        def wrapper():
            print(f"enter {name}")
            func()
            print(f"exit {name}")
        return wrapper
    return decorator

@tag("auth")
@tag("log")
def handler():
    print("handler body")

print("--- calling")
handler()
```

```text
factory auth
factory log
decorate log
decorate auth
--- calling
enter auth
enter log
handler body
exit log
exit auth
```

Python evaluates the decorator expressions `tag("auth")` and `tag("log")` top to bottom, then applies the resulting decorators from the bottom: `handler = auth_decorator(log_decorator(handler))`. All of that happens when the module is imported, which is why heavy work inside a decorator body slows startup. At call time the outermost wrapper (`auth`) runs first, exactly like Express middleware registered first.

This matters with FastAPI. If you write your decorator above `@app.get`, FastAPI has already registered the undecorated function, and your decorator never runs for HTTP requests:

```python
@audit            # wraps only the module-level name: never runs for requests
@app.get("/x")
async def x(): ...
```

Put `@app.get` on top, and make the inner decorator use `functools.wraps`.

**Follow-ups they will ask:**
- How would you make "auth" run before "log"?: It already does at call time; swap the lines to make "log" the outer layer.
- Why does this matter for caching plus auth?: `@cache` above `@require_user` would serve a cached response without checking the user.
- Is the order of decorator expression evaluation guaranteed?: Yes, decorator expressions are evaluated top to bottom, then applied bottom to top.

**Mistakes to avoid:**
- Saying decorators run on each call: the decorator runs once, the wrapper runs on each call.
- Assuming the top decorator is applied first.

### Q. After adding a logging decorator to a FastAPI route, `/docs` shows parameters named `args` and `kwargs` and every request fails with 422. Find and fix the bug.
**Short answer (45 seconds):** The decorator returns a `wrapper(*args, **kwargs)` without `functools.wraps`, so FastAPI inspects the wrapper's signature and treats `args` and `kwargs` as required query parameters. Adding `@functools.wraps(func)` sets `__wrapped__`, which `inspect.signature` follows, so FastAPI sees the original parameters again. Since the route is `async def`, the wrapper must also be `async def` and `await` the call.

**Deeper explanation:** The broken code and the response:

```python
def log_calls(func):
    def wrapper(*args, **kwargs):
        logger.info("calling %s", func.__name__)
        return func(*args, **kwargs)
    return wrapper

@app.get("/items/{item_id}")
@log_calls
async def read_item(item_id: int) -> dict:
    return {"id": item_id}
```

```json
{"detail": [{"type": "missing", "loc": ["query", "args"], "msg": "Field required", "input": null},
            {"type": "missing", "loc": ["query", "kwargs"], "msg": "Field required", "input": null}]}
```

FastAPI builds validation, dependency injection and the OpenAPI schema from `inspect.signature(endpoint)`. The fixed version:

```python
import functools

def log_calls(func):
    @functools.wraps(func)                  # signature, name, docstring preserved
    async def wrapper(*args, **kwargs):
        logger.info("calling %s", func.__name__)
        return await func(*args, **kwargs)  # await: the route is a coroutine function
    return wrapper
```

Verify in `/docs` that `item_id` is back as a path parameter, and add a test with `TestClient` that calls the route. For HTTP-wide concerns (request logging, timing, auth) FastAPI's own tools are usually better: middleware for every request, and `Depends` for per-route behavior, because dependencies are visible in the schema and overridable in tests.

**Follow-ups they will ask:**
- What if the decorator needs the `Request` object?: Use a dependency that takes `request: Request`, or middleware; a decorator cannot easily add parameters to the signature.
- Why did a sync wrapper not crash?: Recent FastAPI versions may still await the returned coroutine, but any timing or `try`/`except` in the sync wrapper runs before the endpoint body executes.
- Does `wraps` affect `functools.lru_cache`?: `lru_cache` already applies `update_wrapper` itself, so cached functions keep their metadata.

**Mistakes to avoid:**
- "Fixing" it by adding `*args, **kwargs` parameters to the route, which breaks validation further.
- Testing the decorated function directly instead of through the HTTP route.

### Q. Write a context manager `temp_env(**vars)` that sets environment variables for a test and restores the old values even if the test fails. Show it both as a class and with `@contextmanager`.
**Short answer (45 seconds):** On enter, remember each key's old value (using a sentinel for "was not set"), then set the new values; on exit, restore old values and delete keys that did not exist before. In the class version that lives in `__enter__` and `__exit__`; in the generator version it is code before `yield`, then a `finally` block. Neither version swallows exceptions.

**Deeper explanation:**

```python
import os
from contextlib import contextmanager

_MISSING = object()   # sentinel: distinguishes "unset" from an empty string

@contextmanager
def temp_env(**values: str):
    saved = {key: os.environ.get(key, _MISSING) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, old in saved.items():
            if old is _MISSING:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old

class TempEnv:
    def __init__(self, **values: str) -> None:
        self.values = values
        self.saved: dict[str, object] = {}

    def __enter__(self) -> "TempEnv":
        self.saved = {k: os.environ.get(k, _MISSING) for k in self.values}
        os.environ.update(self.values)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        for key, old in self.saved.items():
            if old is _MISSING:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
        return False   # do not swallow the test failure

with temp_env(LLM_PROVIDER="fake"):
    assert os.environ["LLM_PROVIDER"] == "fake"
```

The sentinel matters: `os.environ.get(key)` returns `None` both for "not set" and would make you write `None` back, which `os.environ` rejects with a `TypeError`. `finally` runs on success, on an assertion failure and on an early `return`. Objects made by `@contextmanager` can also be used as decorators, so `@temp_env(LLM_PROVIDER="fake")` above a test function works too.

**Follow-ups they will ask:**
- What would you use in real tests?: pytest's `monkeypatch.setenv`, or `unittest.mock.patch.dict(os.environ, {...})`, which do exactly this.
- Is it safe with parallel tests?: Not across threads, because `os.environ` is process-global; pytest-xdist uses separate processes, which is fine.
- Why does a cached `get_settings()` ignore the new env?: `lru_cache` already built the settings; call `get_settings.cache_clear()` or override the dependency.

**Mistakes to avoid:**
- Restoring only keys that existed before, which leaks new variables into later tests.
- Putting the restore code after `yield` without `finally`, so a failing test skips it.

### Q. A worker processing import jobs starts failing with `OSError: [Errno 24] Too many open files` after a few hours. Find the leak and fix it with context managers.
**Short answer (45 seconds):** Confirm the leak by watching the process's open file descriptors grow, then look for resources opened without `with`. The usual culprit closes files and connections at the end of the happy path, so any exception skips the close. Rewrite with `with` (or `ExitStack` for a variable number of files) so every resource closes on every path.

**Deeper explanation:** Diagnose first: `ls /proc/<pid>/fd | wc -l` on Linux or `lsof -p <pid> | wc -l` should climb steadily, and `ulimit -n` shows the limit. On Postgres, `SELECT count(*) FROM pg_stat_activity` climbing toward `max_connections` shows leaked connections, which end in `FATAL: sorry, too many clients already`. The leaking code:

```python
def process_job(job):
    f = open(job.path, encoding="utf-8")
    conn = psycopg.connect(DSN)
    rows = parse(f.read())
    conn.execute("INSERT INTO items (sku, qty) VALUES (%s, %s)", rows[0])   # raises on bad data
    conn.commit()
    f.close()          # skipped whenever anything above raised
    conn.close()
```

The fix:

```python
from contextlib import ExitStack

def process_job(job) -> None:
    with open(job.path, encoding="utf-8") as f, psycopg.connect(DSN) as conn:
        rows = parse(f.read())
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO items (sku, qty) VALUES (%s, %s)", rows)
    # psycopg 3: the connection commits on success, rolls back on error, then closes

def merge_files(paths: list[str], out_path: str) -> None:
    with ExitStack() as stack:
        files = [stack.enter_context(open(p, encoding="utf-8")) for p in paths]
        out = stack.enter_context(open(out_path, "w", encoding="utf-8"))
        for f in files:
            out.writelines(f)
```

Each `with` turns cleanup into a guarantee instead of a convention. For connections, a pool (`psycopg_pool.ConnectionPool`, used with `with pool.connection() as conn:`) is better still, because it caps how many exist at all.

**Follow-ups they will ask:**
- How do you catch this in tests?: Run with `python -X dev` or `-W error::ResourceWarning`, which reports files that were garbage-collected while still open.
- Why not rely on the garbage collector to close them?: CPython often closes an unreferenced file promptly, but anything still holding a reference (a stored traceback, a cache, a reference cycle) keeps the descriptor open, and other Python implementations do not close promptly at all.
- Would raising `ulimit -n` fix it?: It only delays the crash; the descriptors still leak.

**Mistakes to avoid:**
- Adding `close()` calls in more places instead of using `with`.
- Assuming the garbage collector will close everything in time.

### Practice
- Practice kit: open `python-practice/exercises/p15_decorators.py`, implement each function, then run `uv run --with pytest pytest tests/test_p15_decorators.py` from the `python-practice` folder.
- In the REPL, write a decorator without `functools.wraps`, apply it, and print `func.__name__` and `inspect.signature(func)`; add `wraps` and print them again.
- Stack three decorators that each print on entry and exit, predict the order on paper, then run it.
- Write a `@contextmanager` called `timer(label)` that prints the elapsed time, use it around `sum(range(10_000_000))`, then raise an exception inside the block and confirm the time still prints and the exception still propagates.

## Pythonic Idioms [Core]

> This lesson covers the habits that make Python code read like Python instead of translated JavaScript: EAFP, truthiness, `enumerate` and `zip`, unpacking, comprehensions, `any` and `all`, sort keys, dict and `collections` helpers, f-strings, `pathlib`, and the anti-patterns reviewers flag first. In live coding rounds and code reviews for FastAPI and AI backends, these idioms are how interviewers judge fluency in the first five minutes, and several of the anti-patterns (mutable defaults, swallowed exceptions) cause real production incidents.

### Why it exists
Python's design philosophy (`import this`, "The Zen of Python") says there should be one obvious way to do something, and the community converged on idioms that are shorter, harder to get wrong and usually faster because built-ins like `sum`, `sorted` and `Counter` run in C. Code ported line by line from JavaScript or Java works, but it carries index arithmetic, manual counters and broad error handling that hide bugs such as off-by-one errors and swallowed exceptions. Idiomatic code also lowers review cost: a reader recognises `for i, row in enumerate(rows)` instantly. The trade-off is that idioms can be overdone; a dense one-line comprehension that nobody can read is not Pythonic either.

### In plain words
Speaking a language natively is different from translating word by word. "I am having 5 years experience" is understandable, but a native speaker says "I have 5 years of experience". Pythonic code is the native phrasing: it uses the built-in phrases the language offers instead of spelling everything out. Interviewers notice the accent immediately, the same way you notice `var` and callback pyramids in JavaScript.

### Walkthrough: loops and conditions the Python way

1. **`enumerate` instead of `range(len(...))`.** You get the index and the item together, and `start=1` gives human numbering. JavaScript's `arr.forEach((item, i) => ...)` is the closest match.

   ```python
   names = ["asha", "ravi"]
   for i, name in enumerate(names, start=1):
       print(f"{i}. {name}")   # 1. asha / 2. ravi
   ```

2. **`zip` to walk sequences in parallel.** It pairs items until the shortest runs out; `strict=True` (3.10+) raises if lengths differ. `dict(zip(keys, values))` builds a dict from two lists.

   ```python
   ids = ["d1", "d2"]
   scores = [0.91, 0.42]
   for doc_id, score in zip(ids, scores, strict=True):
       print(doc_id, score)
   lookup = dict(zip(ids, scores))   # {'d1': 0.91, 'd2': 0.42}
   ```

3. **Unpacking everywhere.** Python unpacks tuples and lists into names, including a starred catch-all, like JavaScript destructuring. Use `_` for values you ignore.

   ```python
   a, b = 1, 2
   a, b = b, a                      # swap without a temp variable
   first, *rest = [10, 20, 30]      # 10, [20, 30]   (JS: const [first, ...rest] = arr)
   for key, value in {"k": 1}.items():
       print(key, value)
   _, ext = "report.pdf".rsplit(".", 1)
   ```

4. **Truthiness.** Empty containers, `0`, `0.0`, `""` and `None` are falsy; everything else is truthy by default. `if items:` is the idiomatic emptiness check. Unlike JavaScript, an empty list or dict is falsy (in JS `[]` and `{}` are truthy), and `"0"` is truthy in both.

   ```python
   items: list[str] = []
   if not items:
       print("nothing to process")
   retries = 0
   if retries is None:              # when 0 is a valid value, test for None explicitly
       retries = 3
   ```

5. **`is None`, not `== None`.** `None` is a singleton, so identity is the correct test, and `==` can be overloaded by a class. (SQLAlchemy overloads `==` on purpose: `User.deleted_at == None` builds `IS NULL` in SQL, and `.is_(None)` is the clearer spelling there.)

   ```python
   def label(user: dict | None) -> str:
       if user is None:
           return "anonymous"
       return user["name"]
   ```

6. **Chained comparisons, the ternary expression and `in`.** `0 <= x < 10` means `0 <= x and x < 10`. The conditional expression reads `a if condition else b` instead of JavaScript's `condition ? a : b`. `in` tests membership: O(1) on sets and dict keys, O(n) on lists.

   ```python
   score = 0.72
   ok = 0.0 <= score <= 1.0
   label = "relevant" if score >= 0.5 else "noise"
   ALLOWED = {"gpt-4o-mini", "claude-haiku"}   # a set for fast membership
   if "gpt-4o-mini" in ALLOWED:
       print(label)
   ```

7. **`any` and `all` with generator expressions.** They short-circuit like JavaScript's `some` and `every`. Note that `all([])` is `True` and `any([])` is `False`.

   ```python
   chunks = [{"score": 0.2}, {"score": 0.8}]
   has_relevant = any(c["score"] > 0.5 for c in chunks)          # True
   all_valid = all(0 <= c["score"] <= 1 for c in chunks)         # True
   ```

### Walkthrough: data handling idioms

1. **Comprehensions versus `map` and `filter`.** List, dict and set comprehensions are the default way to transform and filter. `map` with an existing named function is fine; `map(lambda ...)` and `filter(lambda ...)` read worse than a comprehension.

   ```python
   docs = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.3}]
   ids = [d["id"] for d in docs if d["score"] > 0.5]        # ['a']
   by_id = {d["id"]: d for d in docs}                      # dict comprehension
   unique_scores = {round(d["score"], 1) for d in docs}    # set comprehension
   lengths = list(map(len, ["ab", "c"]))                   # fine: named function
   ```

2. **`sorted` with `key`, plus `itemgetter` and `attrgetter`.** `key` is a function applied to each item, not a comparator like JavaScript's `(a, b) => a - b`. Return a tuple to sort by several fields, and negate a number to flip just that field. Python's sort is stable.

   ```python
   from operator import attrgetter, itemgetter

   users = [{"name": "bo", "score": 5}, {"name": "al", "score": 5}, {"name": "cy", "score": 9}]
   by_score = sorted(users, key=itemgetter("score"), reverse=True)
   ranked = sorted(users, key=lambda u: (-u["score"], u["name"]))   # score desc, then name asc
   # for objects: sorted(chunks, key=attrgetter("score"))
   top = max(users, key=itemgetter("score"))                       # {'name': 'cy', 'score': 9}
   ```

3. **`dict.get`, `setdefault` and merging.** `d.get(key, default)` avoids a `KeyError` (JS: `obj[key] ?? default`, but note `get` only falls back when the key is missing, not when its value is `None`). `setdefault` inserts and returns a default in one step. `a | b` (3.9+) merges into a new dict, like `{...a, ...b}`.

   ```python
   config = {"model": "gpt-4o-mini"}
   temperature = config.get("temperature", 0.2)
   groups: dict[str, list[str]] = {}
   groups.setdefault("errors", []).append("timeout")
   merged = {"retries": 3, "debug": False} | {"debug": True}   # {'retries': 3, 'debug': True}
   ```

4. **`collections` helpers.** `Counter` counts and ranks, `defaultdict` creates missing values on first access, and `deque(maxlen=n)` keeps the last n items with O(1) appends at both ends. Since 3.7 a normal `dict` keeps insertion order, so `OrderedDict` is rarely needed.

   ```python
   from collections import Counter, defaultdict, deque

   words = "the cat and the hat".split()
   print(Counter(words).most_common(1))      # [('the', 2)]
   by_len: defaultdict[int, list[str]] = defaultdict(list)
   for w in words:
       by_len[len(w)].append(w)              # no "if key not in" dance
   recent = deque(maxlen=3)                  # last 3 chat turns
   for turn in ["t1", "t2", "t3", "t4"]:
       recent.append(turn)
   print(list(recent))                       # ['t2', 't3', 't4']
   ```

5. **Strings: `join` and f-strings.** Build strings with `"sep".join(parts)` rather than `+=` in a loop, which copies the growing string again and again. f-strings support format specs and a `=` debug form.

   ```python
   parts = ["alpha", "beta"]
   print(", ".join(parts))                # alpha, beta
   price, ratio, n = 1234.5, 0.4567, 3
   print(f"{price:,.2f} {ratio:.1%}")     # 1,234.50 45.7%
   print(f"{n=}")                         # n=3: handy in debugging
   ```

6. **`pathlib` over `os.path`.** `Path` objects join with `/`, expose `.name`, `.stem` and `.suffix`, and read or write files in one call. Most standard functions accept a `Path` wherever they accept a string.

   ```python
   from pathlib import Path

   data = Path("data") / "raw" / "docs.jsonl"
   print(data.name, data.stem, data.suffix)    # docs.jsonl docs .jsonl
   data.parent.mkdir(parents=True, exist_ok=True)
   data.write_text('{"id": 1}\n', encoding="utf-8")
   for path in Path("data").rglob("*.jsonl"):  # recursive search
       print(path, path.stat().st_size)
   ```

7. **EAFP: "easier to ask forgiveness than permission".** Python style is to try the operation and handle the specific exception, rather than checking first (LBYL, "look before you leap"). Checking first is longer and can race: a file can disappear between `exists()` and `open()`.

   ```python
   def read_config(path: str) -> str:
       try:
           with open(path, encoding="utf-8") as f:
               return f.read()
       except FileNotFoundError:
           return "{}"

   def to_int(value: str, default: int = 0) -> int:
       try:
           return int(value)
       except ValueError:
           return default
   ```

### Walkthrough: anti-patterns and their fixes

1. **`range(len(x))` and manual index loops.** They add index arithmetic you do not need. Loop over the items, use `enumerate` when you also need the index, and `zip` for parallel sequences.

   ```python
   # before
   for i in range(len(users)):
       print(users[i]["name"])
   # after
   for user in users:
       print(user["name"])
   ```

2. **Building lists with `append` in a loop.** When the loop only transforms and filters, a comprehension is shorter and faster.

   ```python
   # before
   emails = []
   for u in users:
       if u.get("active"):
           emails.append(u["email"].lower())
   # after
   emails = [u["email"].lower() for u in users if u.get("active")]
   ```

3. **Bare `except:` and catch-and-ignore.** A bare `except:` catches `BaseException`, including `KeyboardInterrupt`, `SystemExit` and `asyncio.CancelledError`, so Ctrl+C and task cancellation stop working. `except Exception: pass` is still a bug factory: errors vanish. Catch the specific exception you expect, and log anything you choose to skip.

   ```python
   import logging
   log = logging.getLogger(__name__)

   try:
       amount = float(row["amount"])
   except (KeyError, ValueError):
       log.warning("skipping row %s: bad amount", row.get("id"))
       amount = None
   ```

4. **Mutable default arguments.** A default value is evaluated once, when the `def` runs, so a `[]` or `{}` default is shared by every call. Use `None` and create the object inside.

   ```python
   # before: every call appends to the same list
   def add_tag(tag, tags=[]):
       tags.append(tag)
       return tags

   # after
   def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
       tags = [] if tags is None else list(tags)
       tags.append(tag)
       return tags
   ```

5. **`== None`, `== True` and `len(x) == 0`.** Write `is None`, rely on truthiness for booleans and emptiness, and keep explicit comparisons only when `0` or `""` are meaningful values.

   ```python
   # before
   if result == None or result.ok == True and len(result.items) == 0: ...
   # after
   if result is None or (result.ok and not result.items): ...
   ```

   The rewrite also adds parentheses: `and` binds tighter than `or`, which the original hid.

6. **Manual resource handling and small readable functions.** Use `with` for anything that must be closed, and keep functions small with early returns (guard clauses) instead of deep nesting. Avoid shadowing built-ins such as `list`, `dict`, `id`, `type` and `input` as variable names.

   ```python
   def discount_for(user: dict | None) -> float:
       if user is None:
           return 0.0
       if not user.get("active"):
           return 0.0
       return 0.2 if user.get("tier") == "gold" else 0.05
   ```

### Concepts you must understand
- Loop over items directly; use `enumerate` for an index, `zip(..., strict=True)` for parallel sequences, and never `range(len(x))` just to index.
- Empty containers, `0`, `""` and `None` are falsy; use `if items:` for emptiness and `is None` when `0` or `""` are valid values.
- `is` compares identity and is the only correct test for `None`; `==` compares values and can be overloaded.
- Comprehensions are the default for transform-and-filter; generator expressions inside `sum`, `any`, `all`, `max` avoid building lists.
- `sorted(key=...)` takes a key function, not a comparator; a tuple key sorts by several fields, and the sort is stable.
- `dict.get`, `setdefault`, `|`, `Counter`, `defaultdict` and `deque` replace most hand-written bookkeeping loops.
- EAFP: try the operation and catch the specific exception; checking first is longer and can race.
- Never use a bare `except:` or `except Exception: pass`; catch specific errors, log what you skip, re-raise what you cannot handle.
- Default argument values are evaluated once at `def` time, so mutable defaults are shared across calls; use `None`.
- Use `with` for resources, `pathlib.Path` for paths, `"".join` for building strings and f-strings for formatting.

| JavaScript | Python | Note |
| --- | --- | --- |
| `arr.forEach((x, i) => ...)` | `for i, x in enumerate(arr):` | `start=1` for human numbering |
| `const [first, ...rest] = arr` | `first, *rest = arr` | works in `for` targets too |
| `arr.some(f)` / `arr.every(f)` | `any(...)` / `all(...)` with a generator | both short-circuit |
| `cond ? a : b` | `a if cond else b` | condition in the middle |
| `obj[key] ?? fallback` | `d.get(key, fallback)` | `get` falls back only for missing keys |
| `{...a, ...b}` | `a \| b` | 3.9+; `{**a, **b}` before |
| `arr.sort((a, b) => b.score - a.score)` | `sorted(arr, key=itemgetter("score"), reverse=True)` | key function, not comparator |
| `[]` and `{}` are truthy | `[]` and `{}` are falsy | `if items:` checks emptiness |
| template literal `` `${a}` `` | f-string `f"{a}"` | format specs like `{x:.2f}` |
| `path.join(a, b)` (Node) | `Path(a) / b` | `pathlib` |
| `try { } catch { }` (ignore all) | `except SpecificError:` | never bare `except:` |

### Q. Rewrite this JavaScript in idiomatic Python.
**Short answer (45 seconds):** The JavaScript counts tags with nested index loops and a manual object, sorts entries by count and slices the top n. In Python, `collections.Counter` fed by a nested generator expression does the counting, `most_common(n)` does the sorting and slicing, and an f-string comprehension formats the result: two lines instead of fifteen.

**Deeper explanation:** The JavaScript:

```js
function topTags(posts, n) {
  const counts = {};
  for (let i = 0; i < posts.length; i++) {
    const tags = posts[i].tags || [];
    for (let j = 0; j < tags.length; j++) {
      const t = tags[j].toLowerCase();
      counts[t] = (counts[t] || 0) + 1;
    }
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([tag, count]) => `${tag}: ${count}`);
}
```

The Python:

```python
from collections import Counter

def top_tags(posts: list[dict], n: int) -> list[str]:
    counts = Counter(tag.lower() for post in posts for tag in post.get("tags") or [])
    return [f"{tag}: {count}" for tag, count in counts.most_common(n)]

posts = [{"tags": ["AI", "python"]}, {"tags": None}, {}, {"tags": ["ai", "Rust"]}]
print(top_tags(posts, 2))   # ['ai: 2', 'python: 1']
```

Line by line: the two index loops become one generator expression, whose `for` clauses read in the same order as nested loops. `posts[i].tags || []` becomes `post.get("tags") or []`, which handles both a missing key and an explicit `None`. `counts[t] = (counts[t] || 0) + 1` is what `Counter` does internally. `most_common(n)` sorts by count descending and takes the top n; ties keep first-seen order, matching JavaScript's stable sort here. Complexity is O(total tags) for counting plus O(k log n) for selecting the top n of k distinct tags, since `most_common(n)` uses a heap.

**Follow-ups they will ask:**
- What if posts arrive as a stream from a database cursor?: The generator expression already consumes it lazily; only the counts dict is held in memory.
- How would you strip whitespace and skip empty tags?: Add a condition: `for tag in post.get("tags") or [] if tag.strip()`.
- How would you do this in SQL?: `SELECT lower(tag), count(*) FROM post_tags GROUP BY 1 ORDER BY 2 DESC LIMIT n`.

**Mistakes to avoid:**
- Porting the index loops and the `counts.get(t, 0) + 1` bookkeeping literally.
- Using `post["tags"]`, which raises `KeyError` on posts without tags.

### Q. Users of a chat API start seeing other people's messages in their history. The helper below is the cause. Find the bug and fix it.
**Short answer (45 seconds):** The function has a mutable default argument, `history=[]`. Defaults are evaluated once when `def` runs, so every call that omits `history` appends to the same list, which lives for the whole worker process and is shared across requests and users. Use `None` as the default and create a new list inside the function.

**Deeper explanation:** The bug:

```python
def add_message(text: str, history: list[dict] = []) -> list[dict]:
    history.append({"role": "user", "content": text})
    return history

a = add_message("my card ends 4242")   # user A, new conversation
b = add_message("hello")               # user B, new conversation
print(len(b), a is b)                  # 2 True: B's history contains A's message
```

The default list is stored on the function object (`add_message.__defaults__`), created once at import. In a long-running Uvicorn worker it keeps growing, which is both a privacy incident and a memory leak. JavaScript evaluates default parameters on every call, so developers coming from JS do not expect this. The fix:

```python
def add_message(text: str, history: list[dict] | None = None) -> list[dict]:
    new_history = [] if history is None else list(history)   # copy, do not mutate input
    new_history.append({"role": "user", "content": text})
    return new_history
```

Returning a new list instead of mutating the caller's list also makes the function safe to call on cached or shared histories. The same trap applies to `dict` and `set` defaults and to time defaults like `def log(ts=datetime.now())`, which freezes the timestamp at import time. Linters catch it: Ruff and flake8-bugbear flag mutable defaults as `B006`.

**Follow-ups they will ask:**
- Is it ever used on purpose?: Occasionally as a quick cache, but `functools.lru_cache` or an explicit module-level dict says the intent clearly.
- How do dataclasses avoid this?: `@dataclass` rejects a mutable default and requires `field(default_factory=list)`.
- How would you contain the incident?: Deploy the fix, restart workers to clear the shared list, then audit logs for which responses included foreign messages.

**Mistakes to avoid:**
- Writing `history = history or []`, which also replaces an intentionally passed empty list and still mutates non-empty inputs.
- Thinking a restart fixed it: the list starts filling again on the next request.

### Q. A code reviewer flagged this function as "not Pythonic". Refactor it and explain each change.
**Short answer (45 seconds):** Replace `range(len())` with `enumerate`, `os.path` with `pathlib`, the exists-then-open check with EAFP, the bare `except` with the specific `FileNotFoundError`, `== True` and `!= None` with truthiness, manual `open`/`close` with `read_text`, and string concatenation with an f-string. The result is shorter, has no race between checking and opening, and no longer hides unexpected errors.

**Deeper explanation:** The original:

```python
import os

def load_reports(folder, names):
    result = []
    for i in range(len(names)):
        path = os.path.join(folder, names[i] + ".txt")
        if os.path.exists(path) == True:
            try:
                f = open(path)
                content = f.read()
                f.close()
            except:
                content = None
            if content != None and len(content.strip()) > 0:
                result.append(str(i + 1) + ". " + names[i] + ": " + content.strip())
    return result
```

The refactor:

```python
from pathlib import Path

def load_reports(folder: str | Path, names: list[str]) -> list[str]:
    result = []
    for i, name in enumerate(names, start=1):
        try:
            content = (Path(folder) / f"{name}.txt").read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            continue
        if content:
            result.append(f"{i}. {name}: {content}")
    return result
```

Each change: `enumerate(names, start=1)` removes index arithmetic. `Path(folder) / f"{name}.txt"` replaces `os.path.join` and concatenation. EAFP removes the check-then-open race (the file can disappear in between). `read_text` opens and closes the file for you, so the leak when `read()` raised is gone, and an explicit `encoding` avoids platform-dependent defaults. `if content:` replaces `!= None and len(...) > 0`. The f-string replaces `str(i + 1) + ...`. One deliberate behavior change: the bare `except` used to hide permission errors and invalid UTF-8; now those raise, which is what you want to find out about. If skipping them is a real requirement, catch `(PermissionError, UnicodeDecodeError)` and log a warning.

**Follow-ups they will ask:**
- Could this be a comprehension?: Not cleanly, because of the try/except; a small `read_report(path) -> str | None` helper plus a comprehension would work.
- How would you make it async for many files?: Use `asyncio.to_thread(path.read_text)` per file with `asyncio.gather`, or `aiofiles`.
- Why add type hints here?: They document that `folder` may be a `str` or `Path` and let the checker catch callers passing a single name.

**Mistakes to avoid:**
- Keeping the bare `except` "to be safe", which also hides `KeyboardInterrupt`.
- Changing behavior silently: call out the error-handling change in the pull request.

### Q. Write a function that groups support tickets by assignee and returns, for each assignee, the N most urgent tickets ordered by priority and then by creation time.
**Short answer (45 seconds):** Group in one pass with `defaultdict(list)`, then sort each group with a tuple key `(priority, created_at)` and slice `[:n]`. Use `heapq.nsmallest` when groups are large and n is small. Unassigned tickets go under an explicit key instead of `None`.

**Deeper explanation:**

```python
import heapq
from collections import defaultdict
from datetime import datetime
from operator import itemgetter

def top_tickets(tickets: list[dict], n: int = 3) -> dict[str, list[dict]]:
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for ticket in tickets:
        groups[ticket.get("assignee") or "unassigned"].append(ticket)
    urgency = itemgetter("priority", "created_at")          # 1 = most urgent, then oldest first
    return {
        assignee: heapq.nsmallest(n, items, key=urgency)    # or sorted(items, key=urgency)[:n]
        for assignee, items in sorted(groups.items())
    }

tickets = [
    {"id": 1, "assignee": "asha", "priority": 2, "created_at": datetime(2026, 5, 1)},
    {"id": 2, "assignee": "asha", "priority": 1, "created_at": datetime(2026, 5, 3)},
    {"id": 3, "assignee": None, "priority": 1, "created_at": datetime(2026, 5, 2)},
    {"id": 4, "assignee": "asha", "priority": 1, "created_at": datetime(2026, 5, 2)},
]
print({k: [t["id"] for t in v] for k, v in top_tickets(tickets, 2).items()})
# {'asha': [4, 2], 'unassigned': [3]}
```

`defaultdict(list)` removes the "if key not in dict" check. `itemgetter("priority", "created_at")` returns a tuple, so tuples compare priority first and break ties by time; ISO-8601 strings in one format and timezone would sort correctly too. `ticket.get("assignee") or "unassigned"` folds both a missing key and `None` into one bucket. Grouping is O(t); sorting each group is O(g log g), while `heapq.nsmallest` is O(g log n), which matters when one assignee has 50,000 tickets and you want 3. Sorting `groups.items()` makes the output order deterministic, which keeps tests and API responses stable.

**Follow-ups they will ask:**
- How would you do this in Postgres?: `ROW_NUMBER() OVER (PARTITION BY assignee ORDER BY priority, created_at)` in a subquery, keeping rows where it is at most n.
- What if higher numbers meant more urgent?: Use `key=lambda t: (-t["priority"], t["created_at"])`.
- How do you handle tickets missing `created_at`?: Decide a policy (treat as oldest or newest) and encode it in the key, for example `t.get("created_at") or datetime.max`.

**Mistakes to avoid:**
- Writing a comparator function and `functools.cmp_to_key` when a tuple key does the job.
- Using `groupby` on unsorted tickets, which splits each assignee into several groups.

### Q. A nightly sync job reports "success", but the dashboard is missing half of yesterday's invoices. Find the anti-pattern in the job and fix it.
**Short answer (45 seconds):** The loop wraps each upsert in a bare `except: pass`, so every failure, whether bad data, a schema mismatch or a database outage, is silently discarded and the job still returns success. Catch only the errors you expect per record, log them with context, count them, let unexpected errors propagate, and make the job's status reflect the failures.

**Deeper explanation:** The job:

```python
def sync_invoices(client, db) -> dict:
    for invoice in client.list_invoices():
        try:
            db.upsert(transform(invoice))
        except:
            pass
    return {"status": "success"}
```

Diagnosis: compare source and target counts for the day, then add logging around the `except` and rerun on staging; typically you find a `KeyError` from a renamed field or a `ValidationError` on one currency. The bare `except` also catches `KeyboardInterrupt`, `SystemExit` and `asyncio.CancelledError`, so the job cannot even be stopped cleanly. The fix:

```python
import logging
from pydantic import ValidationError

log = logging.getLogger(__name__)

class SyncFailed(Exception):
    pass

def sync_invoices(client, db, max_error_rate: float = 0.01) -> dict:
    synced, failed = 0, []
    for invoice in client.list_invoices():
        try:
            record = transform(invoice)          # data errors are per-record: skip and record
        except (KeyError, ValidationError):
            log.exception("bad invoice %s", invoice.get("id"))
            failed.append(invoice.get("id"))
            continue
        db.upsert(record)                        # DB errors are systemic: let them propagate
        synced += 1
    total = synced + len(failed)
    if total and len(failed) / total > max_error_rate:
        raise SyncFailed(f"{len(failed)}/{total} invoices failed: {failed[:10]}")
    return {"status": "success", "synced": synced, "failed": failed}
```

Per-record data errors are skipped but logged with `log.exception`, which includes the traceback, and counted; infrastructure errors from `db.upsert` propagate so the scheduler marks the run failed and alerts. The error-rate threshold turns "half the invoices failed" into a failed run instead of a green one.

**Follow-ups they will ask:**
- Where should skipped records go?: A dead-letter table or queue with the payload and error, so they can be fixed and replayed.
- How do you alert?: Emit `synced` and `failed` as metrics and alert on the failure ratio, not only on job crashes.
- Is `except Exception` acceptable anywhere?: At the outermost boundary (a request handler or worker loop) that logs and reports, never deep inside business logic with `pass`.

**Mistakes to avoid:**
- Replacing `except:` with `except Exception: pass`, which still hides every bug.
- Logging with `log.error(e)` and losing the traceback.

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** It prints `90.0`, then `True False`, then `fallback None b`, then `True True False True`. The first line is a real bug: `not discount` treats a legitimate 0 discount as missing. The rest shows that `and`/`or` return one of their operands rather than a bool, that `all` of an empty iterable is `True`, and that `[] == False` is `False` even though `[]` is falsy.

**Deeper explanation:** The code:

```python
def apply_discount(price, discount=None):
    if not discount:
        discount = 0.10          # default: 10% off
    return round(price * (1 - discount), 2)

print(apply_discount(100, 0))    # caller asked for no discount
print(all([]), any([]))
print([] or "fallback", 0 or None, "a" and "b")
print(None == None, None is None, [] == False, bool([]) == False)
```

```text
90.0
True False
fallback None b
True True False True
```

Line 1: `0` is falsy, so the explicit "no discount" is replaced by the default; the fix is `if discount is None:`. Line 2: `all` asks "is there any falsy item?", and an empty iterable has none, so `True`; `any` finds no truthy item, so `False`. Validation like `all(check(x) for x in items)` therefore passes on an empty list, so check emptiness separately when that matters. Line 3: `x or y` returns `x` if it is truthy, else `y`; `x and y` returns `x` if it is falsy, else `y`. So `0 or None` is `None`, and `"a" and "b"` is `"b"`, like JavaScript's `||` and `&&`. Line 4: `[] == False` compares a list with a bool by value and is `False`; truthiness only applies when Python needs a bool, such as in `if` or `bool()`.

**Follow-ups they will ask:**
- What is the Python equivalent of JavaScript's `??`?: There is none; write `x if x is not None else default`.
- Is `"0"` truthy?: Yes, any non-empty string is truthy, in both languages.
- How do you make a custom class falsy?: Define `__bool__`, or `__len__` returning 0.

**Mistakes to avoid:**
- Using `if not value` for numbers or strings where `0` or `""` are valid.
- Expecting `x or default` to behave like `??`.

### Practice
- Practice kit: open `python-practice/exercises/p16_idioms.py`, implement each function, then run `uv run --with pytest pytest tests/test_p16_idioms.py` from the `python-practice` folder.
- Take any 30-line function you wrote in JavaScript recently, port it to Python line by line, then rewrite it with the idioms from this lesson and compare the two versions.
- In the REPL, define `def f(x, acc=[]): acc.append(x); return acc`, call it three times, then print `f.__defaults__` to see where the shared list lives.
- Run `uvx ruff check --select B,SIM,UP,PTH .` on a Python project and fix what it reports: it flags many of these anti-patterns automatically.
