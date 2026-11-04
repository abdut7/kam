## Dicts, Sets & the collections Module [Basics]

> This lesson covers Python's dict and set, the two hash-based built-ins, plus the `collections` module (Counter, defaultdict, deque, namedtuple, OrderedDict, ChainMap). In FastAPI and AI backend code they are everywhere: a JSON request body is a dict before Pydantic validates it, `model.model_dump()` turns a model back into one, LLM chat messages are lists of dicts, settings merging is dict merging, sets de-duplicate retrieved document IDs and check permissions, Counter tallies tokens and status codes, defaultdict groups search hits by document, and deque holds the last N chat turns or the timestamps of a sliding-window rate limiter.

### Why it exists
Python made the hash map a core type with its own literal syntax because the language itself runs on dicts: module globals, object attributes and keyword arguments are all stored in them. JavaScript splits the job between plain objects (string keys only, prototype quirks) and Map; Python has one dict that accepts any hashable key and has guaranteed insertion order since 3.7. Sets exist because "have I seen this?" and "what do these two groups share?" are common enough to deserve O(1) membership and real set algebra. The `collections` module packages the patterns people kept writing by hand: counting, grouping, double-ended queues and lightweight records. The cost is memory, since hash tables use more space than lists, and the rule that keys must be hashable, which in practice means immutable.

### In plain words
A dict is a coat check: you hand over a ticket (the key) and get your coat (the value) back instantly, whether there are ten coats or ten million. A set is the guest list at the door: names only, no duplicates, and "is this name on the list?" takes one glance. Counter is a tally sheet. defaultdict is a coat check that hands you a fresh empty hanger when your ticket is new, instead of refusing you. deque is a queue where people can join or leave at either end without everyone else shuffling along.

### Walkthrough: working with a dict, step by step
1. **Create one.** Keys in a literal are real expressions, so string keys need quotes. In JS `{id: 7}` means the key "id"; in Python `{id: 7}` uses the built-in function `id` as the key.
   ```python
   user = {"id": 7, "name": "Asha", "roles": ["admin"]}
   same = dict(id=7, name="Asha", roles=["admin"])   # keyword form: keys must be identifiers
   pairs = dict([("a", 1), ("b", 2)])                 # from (key, value) pairs
   zeros = dict.fromkeys(["x", "y"], 0)               # {'x': 0, 'y': 0}
   ```
2. **Read with `[]` or `.get()`.** `d[key]` raises `KeyError` when the key is missing, where JS would quietly return `undefined`. `.get(key, default)` returns the default (None if you give none). Use `[]` when a missing key is a bug, `.get()` when the key is optional.
   ```python
   user["name"]            # 'Asha'
   user["email"]           # KeyError: 'email'
   user.get("email")       # None
   user.get("email", "")   # '': the default is used only when the key is absent
   "email" in user         # False: `in` checks keys, never values
   ```
3. **Write, update and delete.** Assignment inserts or overwrites. `del` raises KeyError for a missing key, `pop(key, default)` does not. `setdefault` returns the existing value, or inserts the default and returns it.
   ```python
   user["email"] = "asha@example.com"
   del user["roles"]
   user.pop("nickname", None)                   # remove if present, no error
   user.setdefault("tags", []).append("beta")   # creates the list only when "tags" is missing
   ```
4. **Merge.** `update()` and `|=` mutate the left dict; `|` (3.9+) and `{**a, **b}` build a new one, like JS spread. The right side wins on conflicts, and every form is shallow: nested lists and dicts are shared, not copied.
   ```python
   defaults = {"model": "small", "temperature": 0.2}
   overrides = {"temperature": 0.7}
   cfg = defaults | overrides         # {'model': 'small', 'temperature': 0.7}
   cfg2 = {**defaults, **overrides}   # same result, also works before 3.9
   defaults.update(overrides)         # mutates defaults and returns None
   ```
5. **Iterate.** Looping over a dict yields keys; `.items()` yields pairs you unpack. `.keys()`, `.values()` and `.items()` are live views, and key views support set operations. Adding or removing keys inside the loop raises `RuntimeError: dictionary changed size during iteration`; changing the values of existing keys is fine.
   ```python
   prices = {"tea": 30, "coffee": 120}
   for name, price in prices.items():
       print(name, price)
   total = sum(prices.values())
   {"a": 1, "b": 2}.keys() & {"b": 3, "c": 4}.keys()   # {'b'}
   ```
6. **Order is guaranteed.** Dicts keep insertion order. Overwriting a key keeps its position; deleting and re-inserting moves it to the end. Equality ignores order. JS objects list integer-like keys first; Python never reorders.
   ```python
   d = {"b": 1, "a": 2}
   d["b"] = 3              # {'b': 3, 'a': 2}: position kept
   del d["b"]; d["b"] = 4  # {'a': 2, 'b': 4}: moved to the end
   d == {"b": 4, "a": 2}   # True
   ```
7. **Dict comprehensions.** Same shape as list comprehensions, with `key: value`.
   ```python
   prices = {"tea": 30, "coffee": 120, "juice": 90}
   pricey = {k: v for k, v in prices.items() if v >= 90}   # {'coffee': 120, 'juice': 90}
   by_price = {v: k for k, v in prices.items()}            # invert: duplicate values collide
   ```
8. **Keys must be hashable.** str, int, float, bool, None, tuples of hashables and frozensets work; lists, dicts and sets raise TypeError because a mutable key could change its hash after insertion. Keys that compare equal are the same key, and 1, 1.0 and True are all equal.
   ```python
   cache = {}
   cache[("user", 7)] = "profile"      # tuple key: fine
   cache[["user", 7]] = "profile"      # TypeError: unhashable type: 'list'
   {1: "int", 1.0: "float", True: "bool"}   # {1: 'bool'}
   ```

### Walkthrough: sets and set algebra
1. **Create one.** `{}` is an empty dict, so an empty set is `set()`. `set(iterable)` removes duplicates.
   ```python
   roles = {"admin", "editor"}
   empty = set()                   # not {}
   unique_ids = set([3, 1, 3, 2])  # {1, 2, 3}
   ```
2. **Membership is the main reason to use a set.** `x in some_set` is an average O(1) hash lookup; `x in some_list` scans every element. Inside a loop over 100k users that is the difference between linear and quadratic.
   ```python
   blocked = set(blocked_ids)                       # build once
   allowed = [u for u in users if u["id"] not in blocked]
   ```
3. **Add and remove.** `add` one item, `update` many, `remove` raises KeyError if missing, `discard` stays silent, `pop` removes an arbitrary item.
   ```python
   roles.add("viewer")
   roles.update(["owner", "auditor"])
   roles.discard("ghost")    # no error
   roles.remove("ghost")     # KeyError: 'ghost'
   ```
4. **Set operations.** Operators need sets on both sides; the method forms accept any iterable. JS only gained `Set.prototype.union()` and friends in ES2025; before that you wrote filter loops.
   ```python
   a, b = {"py", "js", "go"}, {"js", "rust"}
   a | b          # union: {'py', 'js', 'go', 'rust'}
   a & b          # intersection: {'js'}
   a - b          # difference: {'py', 'go'}
   a ^ b          # symmetric difference: {'py', 'go', 'rust'}
   a.union(["c"]) # methods take any iterable; a | ["c"] raises TypeError
   {"js"} <= a    # subset test: True
   ```
5. **Sets have no order.** Iteration order is an implementation detail, and for strings it can change between runs because string hashing is randomized per process. Sort before printing or returning, and use `dict.fromkeys` to de-duplicate while keeping first-seen order.
   ```python
   tags = ["b", "a", "b", "c"]
   sorted(set(tags))           # ['a', 'b', 'c']
   list(dict.fromkeys(tags))   # ['b', 'a', 'c']
   ```
6. **frozenset is the immutable set.** It is hashable, so it can be a dict key or an element of another set.
   ```python
   role_for = {frozenset({"read", "write"}): "editor"}
   role_for[frozenset({"write", "read"})]          # 'editor': order does not matter
   groups = {frozenset({1, 2}), frozenset({2, 1})} # one element
   ```
7. **Set comprehensions and JSON.** `{expr for x in xs}` builds a set. `json.dumps` cannot serialize sets, so convert to a sorted list at the edge of your API.
   ```python
   emails = {e.strip().lower() for e in raw_emails}
   json.dumps({"emails": emails})            # TypeError: Object of type set is not JSON serializable
   json.dumps({"emails": sorted(emails)})    # fine
   ```

### Walkthrough: the collections toolbox
1. **Counter counts things.** It is a dict subclass where missing keys read as 0 without being inserted. `most_common(n)` returns the top n, and equal counts keep first-seen order.
   ```python
   from collections import Counter
   status = Counter(["200", "500", "200", "404", "200"])
   status["302"]            # 0: no KeyError, no key inserted
   status.most_common(2)    # [('200', 3), ('500', 1)]
   status.update(["500"])   # add more observations
   status.total()           # 6 (3.10+)
   ```
2. **defaultdict groups things.** You pass a factory (`list`, `int`, `set`); reading a missing key with `[]` calls it and stores the result. The trap: even a read inserts the key. `in` and `.get()` do not.
   ```python
   from collections import defaultdict
   hits_by_doc = defaultdict(list)
   for chunk in retrieved_chunks:
       hits_by_doc[chunk["doc_id"]].append(chunk)
   seen = defaultdict(int)
   seen["x"] += 1                 # starts from int() == 0
   if hits_by_doc["missing"]:     # oops: this inserts "missing": []
       ...
   ```
3. **deque is a double-ended queue.** `append`, `appendleft`, `pop` and `popleft` are all O(1); `list.pop(0)` is O(n) because every element shifts. `maxlen` drops items from the other end automatically, which is exactly "keep the last N".
   ```python
   from collections import deque
   history = deque(maxlen=3)
   for msg in ["hi", "plan trip", "budget?", "dates?"]:
       history.append(msg)
   list(history)        # ['plan trip', 'budget?', 'dates?']
   todo = deque(["a", "b"])
   todo.popleft()       # 'a': FIFO queue for BFS or job processing
   ```
4. **namedtuple is a tuple with field names.** Immutable, unpackable and cheap. `typing.NamedTuple` is the class syntax with type hints. For records with validation or behaviour, use a dataclass or a Pydantic model instead.
   ```python
   from typing import NamedTuple

   class Usage(NamedTuple):
       prompt_tokens: int
       completion_tokens: int

   u = Usage(120, 30)
   u.prompt_tokens, u[1]               # (120, 30)
   u._replace(completion_tokens=40)    # a new tuple; u is unchanged
   u._asdict()                         # {'prompt_tokens': 120, 'completion_tokens': 30}
   ```
5. **OrderedDict is mostly history.** It existed because dicts were unordered before 3.7. It is still useful for three things: `move_to_end`, `popitem(last=False)` to pop the oldest entry, and order-sensitive equality. That makes it the classic LRU cache building block.
   ```python
   from collections import OrderedDict
   lru = OrderedDict(a=1, b=2, c=3)
   lru.move_to_end("a")          # order is now b, c, a
   lru.popitem(last=False)       # ('b', 2): evict the oldest
   OrderedDict(a=1, b=2) == OrderedDict(b=2, a=1)   # False: order matters here
   ```
6. **ChainMap layers dicts, briefly.** Lookups search the maps left to right without copying them; writes go only to the first map. A natural fit for "CLI flags over env vars over defaults".
   ```python
   from collections import ChainMap
   settings = ChainMap(cli_args, env_vars, defaults)
   settings["port"]          # the first map that has "port" wins
   settings["debug"] = True  # written into cli_args only
   ```

### Concepts you must understand
- `d[key]` means "this key must exist" and raises KeyError otherwise; `d.get(key, default)` means "optional", and the default applies only when the key is absent, not when the stored value is None.
- Dicts keep insertion order (guaranteed since 3.7); overwriting a key keeps its slot, and dict equality ignores order.
- `a | b` (3.9+) and `{**a, **b}` build a new merged dict, `a.update(b)` and `a |= b` mutate `a`; the right side wins, and all of them are shallow.
- Keys must be hashable: str, numbers, None, tuples of hashables and frozensets work, lists, dicts and sets do not; equal values such as 1, 1.0 and True are the same key.
- Never add or remove keys while iterating over a dict; iterate over `list(d)` or build a new dict with a comprehension.
- `x in some_set` and `key in some_dict` are average O(1), `x in some_list` is O(n), so convert to a set before membership tests inside a loop.
- `{}` is an empty dict and `set()` an empty set; sets have no order, so sort before output and use `dict.fromkeys` to de-duplicate while keeping order.
- Counter counts, defaultdict groups (and inserts on any `[]` read), deque gives O(1) work at both ends and bounded windows, namedtuple gives small immutable records.
- OrderedDict is only needed for `move_to_end`, `popitem(last=False)` or order-sensitive equality; ChainMap layers dicts for lookups without copying.

| JavaScript | Python | Note |
|---|---|---|
| `const u = { id: 7 }` | `u = {"id": 7}` | String keys need quotes; a bare name is evaluated as a variable |
| `u.email` gives `undefined` | `u["email"]` raises KeyError | Use `u.get("email")` for optional keys |
| `u.email ?? "n/a"` | `u.get("email", "n/a")` | `??` also replaces null; `.get()` keeps a stored None |
| `{ ...a, ...b }` | `a \| b` or `{**a, **b}` | Both shallow; `\|` needs 3.9+ |
| `Object.entries(u)` | `u.items()` | A live view; unpack with `for k, v in u.items()` |
| `delete u.email` | `del u["email"]` or `u.pop("email", None)` | `del` raises KeyError if missing |
| `new Map()` with object keys | `dict` with hashable keys | Keys keep their type: 1 and "1" are different keys |
| `new Set([1, 2])` | `{1, 2}` or `set([1, 2])` | `{}` is an empty dict, not a set |
| `s.has(x)` | `x in s` | Average O(1) |
| Counting with `reduce` | `Counter(items)` | `most_common(n)` for top n |
| `arr.shift()` | `dq.popleft()` | O(1) on a deque, O(n) as `list.pop(0)` |
| `JSON.stringify(new Set())` gives `{}` silently | `json.dumps(set())` raises TypeError | Convert sets to lists first |

### Q. Write a function that returns the three most common error codes in a list of log lines, first with a plain dict and then with Counter.
**Short answer (45 seconds):** Loop once, pull the code out of each ERROR line and count with `counts[code] = counts.get(code, 0) + 1`, then sort the items by count descending and slice the first three. The idiomatic version is `Counter(codes).most_common(3)`, which counts, picks the top k and keeps first-seen order for ties.

**Deeper explanation:** Lines look like `"ERROR E1042 payment timeout"`.

```python
from collections import Counter

def top_errors_dict(lines: list[str], k: int = 3) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "ERROR":
            counts[parts[1]] = counts.get(parts[1], 0) + 1
    # sorted is stable, even with reverse=True, so ties keep first-seen order
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:k]

def top_errors(lines: list[str], k: int = 3) -> list[tuple[str, int]]:
    codes = (p[1] for p in map(str.split, lines) if len(p) >= 2 and p[0] == "ERROR")
    return Counter(codes).most_common(k)
```

`counts.get(code, 0) + 1` is the classic plain-dict pattern; writing `counts[code] += 1` alone raises KeyError the first time a code appears. Counter is a dict subclass whose missing keys read as 0, so the increment just works. The generator expression feeds Counter without building an intermediate list. With `k` given, `most_common` uses `heapq.nlargest`, which is O(n log k) instead of a full sort.

Edge cases: an empty list returns `[]`, malformed lines are skipped by the length check, and a `k` larger than the number of distinct codes returns all of them. Counting is O(n) time and O(distinct codes) memory.

**Follow-ups they will ask:**
- How do you combine counts from several files?: `total.update(Counter(...))` per file, or `c1 + c2`, which also drops zero and negative counts.
- The log is 20 GB. What changes?: iterate the open file line by line (`for line in f:`) so memory grows with distinct codes, not lines.
- Codes arrive in mixed case?: normalize with `.upper()` before counting.

**Mistakes to avoid:**
- Using `counts[code] += 1` on a plain dict without initializing the key.
- Calling `max()` three times and deleting the winner each time, which is slower and mutates the data.

### Q. This function groups orders by customer, but it crashes with `KeyError: 'c-17'` on the first order. Find and fix the bug.
**Short answer (45 seconds):** It reads `groups[cid]` before ever storing a list there, so the first order of every customer raises KeyError. Use `collections.defaultdict(list)`, which creates the empty list on first access, or `groups.setdefault(cid, []).append(order)`. Convert back to a plain dict before returning so callers do not inherit the auto-insert behaviour.

**Deeper explanation:** The buggy code:

```python
def group_orders(orders: list[dict]) -> dict[str, list[dict]]:
    groups = {}
    for order in orders:
        groups[order["customer_id"]].append(order)   # KeyError on first sighting
    return groups
```

The fix:

```python
from collections import defaultdict

def group_orders(orders: list[dict]) -> dict[str, list[dict]]:
    groups: defaultdict[str, list[dict]] = defaultdict(list)
    for order in orders:
        groups[order["customer_id"]].append(order)
    return dict(groups)

# same result without the import:
#     groups.setdefault(order["customer_id"], []).append(order)
```

`setdefault` builds a new empty list on every call, even when the key already exists, and throws it away; `defaultdict(list)` calls `list()` only for missing keys. Returning `dict(groups)` matters: if a caller later does `groups["c-99"]` to check something, a defaultdict silently creates an empty group, which can then leak into a JSON response as a customer with no orders. Customers appear in the order of their first order, because dicts keep insertion order. The whole thing is O(n).

Edge cases: an empty list returns `{}`. An order without `customer_id` still raises KeyError, which is usually right, because it is a data bug; use `order.get("customer_id", "unknown")` only if the business wants a bucket for it.

**Follow-ups they will ask:**
- Group by customer and status together?: use a tuple key, `(order["customer_id"], order["status"])`; tuples are hashable, lists are not.
- Could `itertools.groupby` do this?: only on input already sorted by the key, because it groups consecutive items.
- You only need counts?: `Counter(o["customer_id"] for o in orders)`.

**Mistakes to avoid:**
- Testing `if groups[cid]:` on a defaultdict to see whether a key exists; it inserts the key. Use `cid in groups`.
- Using a list as a composite key, which raises `TypeError: unhashable type: 'list'`.

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** It prints `{1: 'true'} 1`, then `5`, then `False <class 'dict'>`. 1, 1.0 and True are equal with equal hashes, so they collapse into one key that keeps the first key object and the last value. `|=` mutates in place, so the alias sees the change. `{}` is an empty dict, not a set.

**Deeper explanation:** The code:

```python
labels = {1: "one", 1.0: "float one", True: "true"}
print(labels, len(labels))

config = {"retries": 3}
alias = config
config |= {"retries": 5}
print(alias["retries"])

print({} == set(), type({}))
```

Line by line:

1. A dict finds a slot by hash, then confirms with `==`. `hash(1) == hash(1.0) == hash(True)` and the values are equal, so all three literals hit the same slot. The first insertion fixes the key object (`1`), later ones only overwrite the value. Result: `{1: 'true'} 1`. Note the contrast with JS, where object keys are always strings: Python keeps types, so `1` and `"1"` are different keys, a common bug when IDs arrive as strings from a query param and as ints from the database.
2. `alias = config` copies the reference, not the dict. `|=` is an in-place update, like `config.update(...)`, so `alias["retries"]` is `5`. Had the code written `config = config | {"retries": 5}`, the `|` would build a new dict, rebind only `config`, and `alias` would still show `3`.
3. `{}` has always meant an empty dict, so the empty set is spelled `set()`. A dict and a set never compare equal: `False <class 'dict'>`.

**Follow-ups they will ask:**
- Why can a list not be a key?: its contents, and therefore its hash, could change after insertion, and the entry could never be found again, so Python refuses with TypeError.
- How many elements does `{1, True, 1.0}` have?: one; sets use the same hash-and-equality rule.
- How do you copy instead of alias?: `config.copy()` or `dict(config)` for a shallow copy, `copy.deepcopy(config)` when values are nested.

**Mistakes to avoid:**
- Assuming `|=` behaves like JS `a = { ...a, ...b }`, which creates a new object.
- Assuming keys get coerced to strings as in JS objects; `d[1]` and `d["1"]` are different entries.

### Q. Rewrite this JavaScript in idiomatic Python.
**Short answer (45 seconds):** Object spread becomes the dict merge operator `|`, `new Set` becomes `dict.fromkeys` because a Python set does not keep order, and the `{}` and `[]` default parameters become None because Python evaluates defaults once. Keep in mind that the merge is shallow: nested lists are shared with the defaults until you replace them.

**Deeper explanation:** The JavaScript:

```js
const DEFAULTS = { model: "small", temperature: 0.2, tags: ["api"] };

function buildConfig(overrides = {}, extraTags = []) {
  const cfg = { ...DEFAULTS, ...overrides };
  cfg.tags = [...new Set([...cfg.tags, ...extraTags])];
  return cfg;
}
```

The Python:

```python
DEFAULTS = {"model": "small", "temperature": 0.2, "tags": ["api"]}

def build_config(
    overrides: dict | None = None, extra_tags: list[str] | None = None
) -> dict:
    cfg = DEFAULTS | (overrides or {})            # new dict, right side wins (3.9+)
    tags = [*cfg["tags"], *(extra_tags or [])]    # list unpacking, like JS spread
    cfg["tags"] = list(dict.fromkeys(tags))       # de-duplicate, keep first-seen order
    return cfg
```

Three translation points. First, `{...a, ...b}` maps to `a | b` (or `{**a, **b}` before 3.9); both copy only the top level, so right after the merge `cfg["tags"]` is the same list object as `DEFAULTS["tags"]`. The code is safe because it assigns a brand new list; `cfg["tags"].append("x")` instead would corrupt DEFAULTS for every later call, which in a FastAPI process means every later request. Second, a JS Set keeps insertion order but a Python set does not, so `list(set(tags))` could reorder tags and make tests flaky; `dict.fromkeys` is the order-preserving de-duplication. Third, `overrides={}` as a Python default would be one shared dict for all calls, so None is the safe sentinel.

**Follow-ups they will ask:**
- Nested settings need merging too?: write a recursive merge that recurses when both sides hold dicts, or start from `copy.deepcopy(DEFAULTS)`.
- How do you stop anyone mutating DEFAULTS?: `types.MappingProxyType(DEFAULTS)` is a read-only view, and storing tags as a tuple blocks in-place appends.
- What would you use in a real service?: a Pydantic settings model and `model_copy(update=overrides)`.

**Mistakes to avoid:**
- `list(set(tags))`, which loses order.
- `cfg = DEFAULTS` followed by mutation, which aliases instead of copying.

### Q. This session cleanup job crashes with `RuntimeError: dictionary changed size during iteration`. Find and fix the bug.
**Short answer (45 seconds):** The loop deletes keys from the dict it is iterating over, and Python detects the size change and stops the loop. Collect the expired keys first and delete them after the loop, or build a new dict with a comprehension that keeps only live sessions. Updating values of existing keys during iteration is allowed; changing the set of keys is not.

**Deeper explanation:** The buggy code:

```python
def purge_expired(sessions: dict[str, dict], now: float) -> None:
    for sid, data in sessions.items():
        if data["expires"] < now:
            del sessions[sid]          # changes the size mid-iteration
```

Two correct shapes:

```python
def purge_expired(sessions: dict[str, dict], now: float) -> None:
    expired = [sid for sid, data in sessions.items() if data["expires"] < now]
    for sid in expired:                # iterate over a separate list
        del sessions[sid]

def live_sessions(sessions: dict[str, dict], now: float) -> dict[str, dict]:
    return {sid: d for sid, d in sessions.items() if d["expires"] >= now}
```

`.items()` is a live view over the dict's hash table, not a copy (it was a copy in Python 2, which is where some old advice comes from). The iterator checks the dict's size on every step and raises as soon as it changed, even if the deleted key was the last one. The first fix mutates in place, so other code holding a reference to the same dict sees the purge. The comprehension is cleaner and easier to test, but returns a new object, so the caller must rebind it. Both are O(n).

In a real service, sessions in a Python dict live in one worker process. With several uvicorn workers or pods, each has its own dict, so store sessions in Redis with a TTL (`SET key value EX 3600`) and let Redis expire them.

**Follow-ups they will ask:**
- Do lists raise the same error?: no, and that is worse: removing from a list while looping silently skips the next element, so `[1, 2, 2, 3]` with "remove every 2" ends as `[1, 2, 3]`.
- Sets?: the same rule, with `RuntimeError: Set changed size during iteration`.
- Can I loop over `sessions.keys()` instead?: no, that is also a live view; use `list(sessions)`.

**Mistakes to avoid:**
- Wrapping the loop in `try/except RuntimeError`, which leaves the purge half done.
- Copying the whole dict with `deepcopy` just to iterate it, when a list of keys is enough.

### Q. Write a per-user rate limiter that allows at most N requests in any 60-second window.
**Short answer (45 seconds):** Keep a deque of request timestamps per user, created on demand with `defaultdict(deque)`. On each request, pop timestamps older than 60 seconds off the left, reject if N remain, otherwise append the current time. deque makes both ends O(1), and `time.monotonic()` avoids wall-clock jumps.

**Deeper explanation:**

```python
import time
from collections import defaultdict, deque

class SlidingWindowLimiter:
    def __init__(self, limit: int, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self.hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def allow(self, user_id: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        q = self.hits[user_id]                     # new users get an empty deque
        while q and q[0] <= now - self.window:     # oldest timestamp is always at the left
            q.popleft()                            # O(1); list.pop(0) would be O(n)
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

limiter = SlidingWindowLimiter(limit=2, window=60)
[limiter.allow("u1", t) for t in (0, 1, 2, 61)]   # [True, True, False, True]
```

Timestamps are appended in time order, so the deque stays sorted and eviction only ever touches the left end. Each call is amortized O(1), and memory per user is at most `limit` timestamps. Injecting `now` makes the class testable without sleeping. `time.monotonic()` is used because `time.time()` can jump when NTP corrects the clock.

In FastAPI you would call `allow` from a dependency and raise `HTTPException(status_code=429)` when it returns False. Two production caveats: memory grows with the number of distinct users, so periodically drop users whose deque is empty, and the state lives in one process.

**Follow-ups they will ask:**
- Several uvicorn workers or pods?: move the state to Redis, a sorted set per user with ZREMRANGEBYSCORE, ZCARD and ZADD inside a Lua script or MULTI so the check is atomic.
- Is it safe under asyncio?: `allow` has no `await`, so no other coroutine runs in the middle of it; with threads you would need a lock.
- Cheaper but less precise?: a fixed window with Redis `INCR` plus `EXPIRE`, accepting bursts at window edges.

**Mistakes to avoid:**
- Using a list with `pop(0)`, which shifts every element on each eviction.
- Shipping an in-memory limiter behind a load balancer and assuming it limits globally.

### Practice
- Practice kit: open `python-practice/exercises/p07_dicts_sets.py`, implement each function, then run `uv run --with pytest pytest tests/test_p07_dicts_sets.py` from the `python-practice` folder.
- In the REPL, build `d = {"b": 1, "a": 2}`, then try `d["c"]`, `d.get("c")`, `d | {"a": 9}`, `d |= {"a": 9}` and `d.setdefault("c", [])`, printing `d` after each to see which ones mutated it.
- Time membership from the shell: `python3 -m timeit -s "xs = list(range(100_000)); s = set(xs)" "99_999 in xs"`, then the same with `in s`.
- Count the words of a paragraph with `Counter(text.lower().split())`, then try `most_common(5)`, `c1 + c2`, `c1 - c2` and `total()` on two paragraphs.

## Functions [Basics]

> This lesson covers how Python defines and calls functions: return values, defaults, positional and keyword arguments, `*args` and `**kwargs`, keyword-only and positional-only parameters, scope and closures, lambda, docstrings, type hints and recursion. In FastAPI code, a path operation is a function whose parameters FastAPI inspects to decide what is a path parameter, a query parameter or a body; dependencies are functions passed to `Depends()`; the OpenAI and Anthropic Python SDKs take keyword-only arguments such as `model=` and `messages=`; and retry, timing and logging wrappers forward `*args, **kwargs`. Python's argument rules are stricter than JavaScript's, and its scope rules produce bugs a JS developer does not expect.

### Why it exists
Functions in Python are ordinary objects, so they can be passed around, stored in dicts and returned from other functions; that is what makes callbacks, dependency injection, tool registries and decorators possible. The argument system (keywords, defaults, `*args`, `**kwargs`, keyword-only and positional-only parameters) lets an API be called readably and changed without breaking callers, where JavaScript passes an options object and hopes nobody misspells a key. Python checks every call against the signature and raises TypeError on a missing or unexpected argument instead of silently filling in `undefined`. Scope is decided when the function is compiled, from the names it assigns, which makes closures cheap and predictable but causes UnboundLocalError and the late-binding loop trap. The main trade-off: default values are evaluated once, when `def` runs, which is the source of the most famous Python bug.

### In plain words
A function is a recipe card. Positional arguments are ingredients handed over in the listed order; keyword arguments carry name labels, so their order stops mattering. A default value says "if you do not bring salt, use the house salt", but there is only one house jar shared by every cook, so if it is a bowl someone fills, the next cook finds leftovers in it. When the recipe says "use the oven", the cook checks their own station first, then the kitchen around them, then the restaurant, and finally the city's building rules: local, enclosing, global, built-in.

### Walkthrough: defining and calling functions
1. **def and return.** The body is indented, there are no braces, and a function without `return` (or with a bare `return`) gives back None, the counterpart of JS `undefined`. Returning several values returns a tuple, which the caller unpacks.
   ```python
   def split_name(full: str) -> tuple[str, str]:
       first, _, last = full.partition(" ")
       return first, last              # a tuple

   first, last = split_name("Asha Rao")

   def log(msg: str) -> None:
       print(msg)                      # no return: the call evaluates to None
   ```
2. **Positional and keyword arguments.** Any parameter can be passed by name, in any order, and positional arguments must come before keyword ones in a call. Python enforces the signature: a missing argument or an extra one raises TypeError, where JS fills in `undefined` or ignores extras.
   ```python
   def connect(host: str, port: int, timeout: float = 5.0) -> str:
       return f"{host}:{port} ({timeout}s)"

   connect("db", 5432)                     # positional
   connect(port=5432, host="db")           # keyword, any order
   connect("db", port=5432, timeout=1.5)   # mixed: positional first
   connect("db")         # TypeError: connect() missing 1 required positional argument: 'port'
   connect("db", 5432, 1, 2)   # TypeError: connect() takes from 2 to 3 positional arguments but 4 were given
   ```
3. **Defaults are evaluated once.** The default expression runs when `def` executes, and the same object is reused on every call. For a mutable default (list, dict, set) every call that omits the argument shares one object. JS evaluates default parameters on every call, which is why JS developers do not expect this. Use None as a sentinel.
   ```python
   def add_tag(tag: str, tags: list[str] = []) -> list[str]:   # BUG
       tags.append(tag)
       return tags

   add_tag("a")   # ['a']
   add_tag("b")   # ['a', 'b']: the same list as the previous call

   def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
       if tags is None:
           tags = []                   # a fresh list on every call
       tags.append(tag)
       return tags
   ```
4. **`*args` and `**kwargs` collect the extras.** `*args` gathers extra positional arguments into a tuple and `**kwargs` gathers extra keyword arguments into a dict; the names are a convention, the stars are the syntax. JS rest parameters cover only the positional half.
   ```python
   def log_event(name: str, *args: object, **fields: object) -> None:
       print(name, args, fields)

   log_event("login", 1, 2, user="asha", ip="10.0.0.1")
   # login (1, 2) {'user': 'asha', 'ip': '10.0.0.1'}
   ```
5. **Keyword-only and positional-only parameters.** Everything after a bare `*` (or after `*args`) must be passed by name; everything before `/` (3.8+) must be passed by position. Keyword-only parameters prevent unreadable calls like `fetch(url, True, False)`. Positional-only parameters let you rename a parameter later without breaking callers. The full order is: positional-only, `/`, normal, `*` or `*args`, keyword-only, `**kwargs`.
   ```python
   def search(query: str, /, *, limit: int = 10, rerank: bool = False) -> list[str]:
       return []

   search("refund policy", limit=5)    # ok
   search("refund policy", 5)          # TypeError: search() takes 1 positional argument but 2 were given
   search(query="refund policy")       # TypeError: ... positional-only arguments passed as keyword arguments: 'query'
   ```
6. **Unpacking at the call site.** `*iterable` spreads into positional arguments and `**mapping` spreads a dict into keyword arguments. JS has `f(...arr)` but no keyword spread. A misspelled key fails loudly instead of being ignored.
   ```python
   import math
   point = (3, 4)
   options = {"limit": 5, "rerank": True}
   math.hypot(*point)                  # 5.0
   search("refund policy", **options)
   search("refund policy", **{"limt": 5})   # TypeError: search() got an unexpected keyword argument 'limt'
   ```

### Walkthrough: how Python finds a name (LEGB)
1. **Scope is decided at compile time, and blocks do not create one.** When Python compiles a function, any name assigned anywhere in its body (`=`, `+=`, a `for` target, `import`, `def`, `with ... as`) is local to the whole function. `if`, `for`, `while`, `with` and `try` blocks do not create scopes, unlike `let` and `const` blocks in JS.
   ```python
   for i in range(3):
       pass
   print(i)              # 2: the loop variable survives the loop

   if True:
       msg = "set inside if"
   print(msg)            # works: there is no block scope
   ```
2. **The lookup order is L, E, G, B.** Reading a name searches the Local scope, then Enclosing function scopes from the innermost outwards, then the Global (module) scope, then the Built-in scope.
   ```python
   model = "global-model"              # G

   def outer() -> str:
       model = "outer-model"           # E, as seen from inner
       def inner() -> str:
           return model                # not local, so found in the enclosing scope
       return inner()

   outer()          # 'outer-model'
   len("abc")       # B: len lives in the builtins module
   ```
3. **Global means module-level, not process-wide.** Each module has its own globals; other files see them only through `import`. Nothing is like the browser's `window`. Built-ins sit last in the chain, so a module-level name can shadow them.
   ```python
   list = ["a", "b"]       # shadows the built-in list for this whole module
   list("xyz")             # TypeError: 'list' object is not callable
   del list                # removes the shadow; the built-in is visible again
   ```
4. **Assigning makes a name local, hence UnboundLocalError.** `count += 1` assigns, so `count` is local to the whole function, and the read on the right-hand side happens before the local has a value. Mutating an object does not assign the name, so `stats["n"] += 1` or `items.append(x)` on a global needs no declaration.
   ```python
   count = 0

   def track() -> None:
       count += 1
   # UnboundLocalError: cannot access local variable 'count' where it is not associated with a value
   ```
5. **`global` rebinds a module-level name.** It fixes the error, but it is shared mutable state: hard to test, not shared across worker processes, and not safe under threads. Prefer returning values, a class, or an external store.
   ```python
   count = 0

   def track() -> None:
       global count
       count += 1
   ```
6. **`nonlocal` rebinds a name in the enclosing function.** It is how a closure keeps private, mutable state. `nonlocal` never reaches module scope; at module level it is a SyntaxError.
   ```python
   def make_counter():
       count = 0
       def increment() -> int:
           nonlocal count          # without this, count += 1 raises UnboundLocalError
           count += 1
           return count
       return increment

   c = make_counter()
   c(), c()                        # (1, 2)
   ```
7. **Closures capture variables, not values.** An inner function keeps a reference to the enclosing variable (a cell) that outlives the outer call, and it reads the variable's current value each time it runs.
   ```python
   def make_greeter():
       greeting = "hi"
       def greet(name: str) -> str:
           return f"{greeting} {name}"
       greeting = "hello"          # changed after greet was defined
       return greet

   make_greeter()("asha")                          # 'hello asha'
   make_greeter().__closure__[0].cell_contents     # 'hello'
   ```
8. **The late-binding loop trap.** A loop has one variable that every closure created in it shares, and each closure looks the variable up when called, after the loop has finished. Bind the current value with a default argument, a factory function or `functools.partial`. In JS, `for (let i ...)` creates a fresh binding per iteration, so this only bites with `var`.
   ```python
   handlers = [lambda: i for i in range(3)]
   [h() for h in handlers]         # [2, 2, 2]

   handlers = [lambda i=i: i for i in range(3)]    # default freezes the current value
   [h() for h in handlers]         # [0, 1, 2]
   ```
9. **Comprehensions have their own scope.** Unlike a `for` statement, the loop variable of a comprehension does not leak into the surrounding code.
   ```python
   squares = [n * n for n in range(3)]
   n               # NameError: name 'n' is not defined (if n did not exist before)
   ```

### Walkthrough: functions as values, lambda, docstrings, hints and recursion
1. **Functions are objects.** You can assign them, pass them and inspect them. Pass the function itself, without calling it, when an API wants a callback such as `key=`.
   ```python
   def shout(s: str) -> str:
       return s.upper()

   f = shout
   f("hi"), f.__name__                         # ('HI', 'shout')
   sorted(["b", "A", "c"], key=str.lower)      # ['A', 'b', 'c']
   ```
2. **Dispatch tables replace long if/elif chains.** A dict from a name to a function is the Python way to route events, commands or LLM tool calls to handlers.
   ```python
   def create(event: dict) -> str:
       return "created"

   def delete(event: dict) -> str:
       return "deleted"

   HANDLERS = {"create": create, "delete": delete}

   def handle(event: dict) -> str:
       handler = HANDLERS.get(event["type"])
       if handler is None:
           raise ValueError(f"unknown event type {event['type']!r}")
       return handler(event)
   ```
3. **lambda is one expression, nothing more.** No statements, no annotations, no docstring, and it shows up as `<lambda>` in tracebacks. JS arrow functions can have block bodies; Python lambdas cannot. Use lambda for short inline keys and `def` for anything you would name.
   ```python
   users.sort(key=lambda u: (u["role"], u["name"]))   # fine: short and inline
   by_len = sorted(words, key=len)                    # better: no lambda needed
   fmt = lambda u: u["name"].title()                  # avoid: PEP 8 says use def
   ```
4. **Docstrings document the function at runtime.** The first string literal in the body becomes `__doc__`, which `help()`, IDEs and tools read. FastAPI uses a path operation's docstring as its description in the OpenAPI docs.
   ```python
   def refund(order_id: str, amount: int) -> bool:
       """Refund part or all of an order.

       Args:
           order_id: The order to refund.
           amount: Amount in paise; must not exceed the captured amount.

       Returns:
           True if the payment provider accepted the refund.
       """
       return True
   ```
5. **Type hints are not enforced by Python itself.** They are stored in `__annotations__` and checked by mypy or pyright, not by the interpreter. FastAPI and Pydantic read them at runtime to parse and validate input, which is why hints matter so much there. Use `X | None` (3.10+), built-in generics like `list[str]` (3.9+) and `Callable` from `collections.abc`.
   ```python
   from collections.abc import Callable

   def apply(fn: Callable[[int], int], value: int) -> int:
       return fn(value)

   apply(str, 5)      # returns '5' at runtime; only a type checker complains
   ```
6. **Recursion works, with a ceiling.** Python has no tail-call optimization, and the default recursion limit is 1000 frames (`sys.getrecursionlimit()`); going deeper raises RecursionError. Raising the limit with `sys.setrecursionlimit` risks crashing the interpreter instead of getting a clean error, so for deep or user-controlled data use an explicit stack.
   ```python
   import sys

   def depth(node: dict) -> int:
       children = node.get("children", [])
       return 1 + max((depth(c) for c in children), default=0)

   sys.getrecursionlimit()     # 1000 by default
   ```

### Concepts you must understand
- Every call is checked against the signature: missing or unexpected arguments raise TypeError, and nothing is silently `undefined`.
- Default values are evaluated once, when `def` runs, and shared by every call; use None as the default for lists, dicts, sets and timestamps, and build the real value inside.
- Parameter order is positional-only, `/`, normal, `*` or `*args`, keyword-only, `**kwargs`; `*args` is a tuple and `**kwargs` is a dict.
- At a call site, `*iterable` spreads positional arguments and `**mapping` spreads keyword arguments.
- Name lookup is LEGB, and scope is fixed at compile time: assigning a name anywhere in a function makes it local everywhere in that function.
- `global` rebinds a module-level name and `nonlocal` an enclosing function's name; mutating an object (`append`, `d[k] = v`) needs neither.
- Closures capture variables, not values, so closures created in a loop all see the final value unless you bind it with a default argument, a factory function or `functools.partial`.
- Only functions, classes, modules and comprehensions create scopes; `if`, `for`, `with` and `try` blocks do not.
- Functions are objects you can pass, store and return; lambda is a single expression, so use `def` for anything that deserves a name.
- Type hints are not enforced by the interpreter, but FastAPI and Pydantic read them at runtime; recursion stops at about 1000 frames with RecursionError and no tail-call optimization.

| JavaScript | Python | Note |
|---|---|---|
| `function f(a, b = 1) {}` | `def f(a, b=1):` | JS evaluates the default on every call, Python once at `def` time |
| No `return` gives `undefined` | No `return` gives `None` | `return a, b` returns a tuple |
| Missing argument becomes `undefined` | TypeError: missing 1 required positional argument | Extra arguments also raise TypeError |
| `function f(...rest)` | `def f(*args)` | `args` is a tuple |
| `f({ limit: 10 })` options object | `f(limit=10)` | Native keyword arguments; misspelled names raise TypeError |
| No equivalent | `def f(x, /, *, limit=10)` | Positional-only before `/`, keyword-only after `*` |
| `f(...arr)` | `f(*arr)` and `f(**opts)` | Python can also spread a dict into keyword arguments |
| `(x) => x * 2` | `lambda x: x * 2` | One expression only, no block body |
| `for (let i ...)` gives each closure its own `i` | One `i` shared by every closure | Bind with `lambda i=i: ...` |
| Block scope with `let` and `const` | Function scope only | Loop variables survive the loop |
| JSDoc comment | Docstring plus type hints | `help(f)` prints the docstring |

### Q. A FastAPI helper returns tags from earlier requests mixed into new ones. Find and fix the bug.
**Short answer (45 seconds):** The helper has a mutable default argument. The default list is created once, when `def` runs, and every call that omits `tags` appends to that same list, so one user's tags show up in the next user's response. Use None as the default and create the list inside the function. This is a data-leak bug, not just a logic bug.

**Deeper explanation:** The buggy code:

```python
def normalize_tags(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag.strip().lower())
    return tags

normalize_tags("Python")    # ['python']
normalize_tags("Rust")      # ['python', 'rust']: leaked from the previous call
normalize_tags.__defaults__ # (['python', 'rust'],): the shared list lives on the function
```

The fix:

```python
def normalize_tags(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []                     # a new list for every call
    tags.append(tag.strip().lower())
    return tags
```

A `def` statement evaluates its default expressions once and stores the objects on the function. Immutable defaults (numbers, strings, None, tuples) are harmless because they cannot be changed in place. A list, dict or set default becomes process-wide shared state, and in a FastAPI worker that process serves every user, so the bug is a privacy problem. Restarting the server only hides it until the list fills up again. The same trap applies to `def log(at=datetime.now())`: the timestamp is frozen at import time.

**Follow-ups they will ask:**
- Why does Python work this way?: defaults are part of the function object, evaluated once for speed and simplicity; `__defaults__` shows them.
- Is `tags: list[str] = []` in a Pydantic model the same bug?: no, Pydantic copies mutable defaults per instance; a dataclass refuses it with `ValueError: mutable default <class 'list'> for field tags is not allowed: use default_factory`.
- Is a mutable default ever deliberate?: occasionally, as a tiny per-process cache, but `functools.lru_cache` says that more clearly.

**Mistakes to avoid:**
- Writing `tags = tags or []`, which also replaces an empty list the caller passed in and breaks the "append to my list" contract; test `is None`.
- Assuming JS semantics, where defaults are re-evaluated on every call.

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** The first print shows `['closing queue', 'closing queue', 'closing queue']`, the second `['closing db', 'closing cache']`. All three lambdas in the loop close over the same `name` variable and read it when they are called, after the loop has left it at "queue". The factory function creates a new scope per call, so each closure gets its own `name`.

**Deeper explanation:** The code:

```python
callbacks = []
for name in ["db", "cache", "queue"]:
    callbacks.append(lambda: f"closing {name}")
print([cb() for cb in callbacks])

def make_closer(name: str):
    return lambda: f"closing {name}"
print([make_closer(n)() for n in ["db", "cache"]])
```

A closure stores a reference to the variable, not a snapshot of its value. The `for` loop does not create a new scope, so there is exactly one `name`, rebound three times; the lambdas look it up only when called. `make_closer` fixes this because every call creates a fresh local `name`, and each returned lambda captures a different one.

Other fixes: `lambda name=name: f"closing {name}"` (the default is evaluated immediately) or `functools.partial(close, name)`. In JavaScript, `for (const name of [...])` creates a fresh binding per iteration and prints three different values; only `var` reproduces Python's behaviour.

Where this bites in real code: registering shutdown hooks, building FastAPI routes in a loop, or creating one tool function per entry in a list of LLM tools, where every tool ends up calling the last handler.

**Follow-ups they will ask:**
- Does a list comprehension avoid it?: no, `[lambda: n for n in names]` still shares one `n` inside the comprehension's scope.
- Why do some people call the default-argument fix a hack?: it adds a parameter callers could override by accident; a factory function or `partial` states the intent better.
- Does `asyncio.create_task(close(name))` in a loop have this problem?: no, the argument is evaluated immediately, when the coroutine object is created.

**Mistakes to avoid:**
- Believing a lambda copies the variable's value when it is created.
- "Fixing" it by switching from a `for` loop to a comprehension.

### Q. This request counter raises UnboundLocalError. Fix it, then explain why the fix is still wrong in production.
**Short answer (45 seconds):** `request_count += 1` assigns, so Python treats `request_count` as local to the whole function, and the read happens before any local value exists. `global request_count` removes the error. In production it is still wrong: each uvicorn worker process has its own copy of the global, and `+=` is not atomic across threads, so use a locked counter within a process and Redis `INCR` or a metrics library across processes.

**Deeper explanation:** The buggy code and the error:

```python
request_count = 0

def track_request() -> int:
    request_count += 1
    return request_count
# UnboundLocalError: cannot access local variable 'request_count' where it is not associated with a value
```

The compiler sees an assignment to `request_count` inside the function and marks it local for the entire body. Older Python versions word the error as "local variable referenced before assignment". The minimal fix is `global request_count` as the first line. A better shape, testable and thread-safe within one process:

```python
import threading

class RequestCounter:
    def __init__(self) -> None:
        self._count = 0
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:                # += is read, add, write: threads can interleave
            self._count += 1
            return self._count
```

Sync (`def`) FastAPI endpoints run in a thread pool, so two requests can execute `+=` at the same time and lose an update without the lock. And with `uvicorn --workers 4` there are four processes, four module globals and four partial counts. For a real request count use Redis `INCR`, or a Prometheus counter, whose Python client has a multiprocess mode for this case.

**Follow-ups they will ask:**
- Why does `stats["count"] += 1` on a global dict work without `global`?: it mutates the dict; the name `stats` is never rebound.
- Could `nonlocal` fix the original code?: no, `nonlocal` targets an enclosing function, and at module level it is a SyntaxError.
- Is an `async def` endpoint safe without the lock?: within one event loop, yes, as long as there is no `await` between the read and the write; the multi-worker problem remains.

**Mistakes to avoid:**
- Scattering `global` across the codebase to silence the error.
- Assuming one Python process serves all traffic.

### Q. Write a retry helper that can call any function with any arguments and retries only on chosen exceptions.
**Short answer (45 seconds):** Take the function plus `*args` and `**kwargs`, and put the retry options after `*args` so they are automatically keyword-only and can never be swallowed as the target's arguments. Call `func(*args, **kwargs)` in a loop, catch only a tuple of retryable exceptions, back off exponentially, and re-raise the last error with a bare `raise`.

**Deeper explanation:**

```python
import random
import time
from collections.abc import Callable
from typing import Any

def call_with_retries(
    func: Callable[..., Any],
    *args: Any,
    attempts: int = 3,
    retry_on: tuple[type[Exception], ...] = (TimeoutError, ConnectionError),
    base_delay: float = 0.5,
    **kwargs: Any,
) -> Any:
    for attempt in range(1, attempts + 1):
        try:
            return func(*args, **kwargs)        # forward everything unchanged
        except retry_on:
            if attempt == attempts:
                raise                           # the last error, original traceback
            delay = base_delay * 2 ** (attempt - 1)
            time.sleep(delay + random.uniform(0, delay))   # backoff plus jitter

profile = call_with_retries(fetch_profile, "u-42", timeout=2.0, attempts=4)
```

`fetch_profile` receives `"u-42"` and `timeout=2.0`; `attempts` is consumed by the helper because it is a named keyword-only parameter. One catch: if the target function also has a keyword argument called `attempts`, the helper captures it, which is why libraries pick unusual names or take `args` and `kwargs` as explicit parameters. `except retry_on` accepts a tuple of classes. Exponential backoff with jitter keeps many clients from retrying in lockstep against a recovering service.

Only retry operations that are safe to repeat: GETs, idempotent writes, or POSTs that carry an idempotency key. Retrying a payment charge without one can double-charge a customer. In production the tenacity library covers this with decorators, stop and wait strategies and async support.

**Follow-ups they will ask:**
- How do you turn it into a decorator?: put the same loop inside a decorator factory and apply `functools.wraps` to the wrapper.
- What about async code?: an `async def` version that awaits `func(*args, **kwargs)` and `asyncio.sleep(delay)`; `time.sleep` would block the event loop.
- How do you type it precisely?: `ParamSpec` and `TypeVar` (3.10+) let the type checker see the target's real parameters and return type.

**Mistakes to avoid:**
- Catching `Exception`, which retries programming bugs like KeyError three times before failing.
- Calling `time.sleep` inside async code.

### Q. Rewrite this JavaScript in idiomatic Python.
**Short answer (45 seconds):** JavaScript fakes named parameters with a destructured options object; Python has them natively, so `page`, `size` and `reverse` become keyword-only parameters after a bare `*`. Misspelled options now raise TypeError instead of being ignored, `[...items].reverse()` becomes the slice `items[::-1]`, and `throw new Error` becomes a specific `ValueError`.

**Deeper explanation:** The JavaScript:

```js
function paginate(items, { page = 1, size = 20, reverse = false } = {}) {
  if (size > 100) throw new Error("size too large");
  const list = reverse ? [...items].reverse() : items;
  const start = (page - 1) * size;
  return list.slice(start, start + size);
}
paginate(rows, { size: 50, pgae: 2 });   // typo silently ignored
```

The Python (the `[T]` generic syntax needs 3.12):

```python
def paginate[T](
    items: list[T], *, page: int = 1, size: int = 20, reverse: bool = False
) -> list[T]:
    if size > 100:
        raise ValueError("size too large")
    if page < 1:
        raise ValueError("page must be >= 1")
    ordered = items[::-1] if reverse else items    # slicing returns a new list
    start = (page - 1) * size
    return ordered[start:start + size]

paginate(rows, size=50, page=2)
paginate(rows, size=50, pgae=2)   # TypeError: paginate() got an unexpected keyword argument 'pgae'
```

Slices never raise for out-of-range bounds, just like JS `slice`, so the last page simply comes back short. The `page < 1` check is new and important: in Python a negative start index counts from the end, so `page=-1` would silently return items from the tail of the list instead of nothing. If a caller already holds the options in a dict, `paginate(rows, **opts)` spreads it, and an unknown key still fails loudly.

In a FastAPI endpoint the same parameters become query parameters, with validation declared in the signature: `size: int = Query(20, le=100)`.

**Follow-ups they will ask:**
- How do you write the generic before 3.12?: declare `T = TypeVar("T")` and annotate `items: list[T]`.
- Why not `reversed(items)`?: it returns an iterator, and slicing it raises `TypeError: 'list_reverseiterator' object is not subscriptable`.
- What if items is a huge generator?: use `itertools.islice(items, start, start + size)` and accept that it cannot be reversed cheaply.

**Mistakes to avoid:**
- Translating literally to `def paginate(items, options={})`, which brings a mutable default and loses the typo check.
- Forgetting that negative indexes are valid in Python.

### Q. Write a function that sums every number in a nested JSON payload, then make it safe for deeply nested input.
**Short answer (45 seconds):** Recurse into dicts and lists, return numbers, and return 0 for anything else, skipping bools explicitly because `bool` is a subclass of `int`. Python has no tail-call optimization and stops at about 1000 frames with RecursionError, so for untrusted or deep input rewrite it as a loop over an explicit stack, which has no depth limit.

**Deeper explanation:** The recursive version:

```python
def sum_numbers(value: object) -> float:
    if isinstance(value, bool):                 # True would otherwise count as 1
        return 0
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        return sum(sum_numbers(v) for v in value.values())
    if isinstance(value, list):
        return sum(sum_numbers(v) for v in value)
    return 0
```

The iterative version, safe at any depth:

```python
def sum_numbers_iter(value: object) -> float:
    total: float = 0
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            total += item
        elif isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return total
```

The recursion depth equals the nesting depth of the payload, and a client controls that. A body like `[[[[...]]]]` nested 1500 levels deep turns the recursive version into a RecursionError and, unhandled, a 500. The explicit stack lives on the heap, so only memory limits it. Both versions are O(n) in the number of nodes. Note that `json.loads` itself raises RecursionError on extremely deep input, so cap the request body size as well.

**Follow-ups they will ask:**
- Why not `sys.setrecursionlimit(100_000)`?: it trades a clean RecursionError for a possible hard crash, and the attacker still controls the depth.
- Tuples and sets too?: add them to the container checks; avoid a generic "is iterable" test, because strings are iterable and would recurse into characters.
- Could `match` (3.10+) express this?: yes, `case bool(): ...`, `case int() | float(): ...`, `case dict(): ...`, as long as the bool case comes first.

**Mistakes to avoid:**
- Forgetting the bool check, so `{"active": True}` adds 1.
- Passing an accumulator as a mutable default, `def f(v, acc=[])`, which leaks between calls.

### Practice
- Practice kit: open `python-practice/exercises/p08_functions.py`, implement each function, then run `uv run --with pytest pytest tests/test_p08_functions.py` from the `python-practice` folder.
- In the REPL, define `def f(a, /, b, *, c): ...` and call it every way you can think of (`f(1, 2, c=3)`, `f(1, b=2, c=3)`, `f(a=1, b=2, c=3)`, `f(1, 2, 3)`), reading each TypeError message.
- Reproduce the late-binding trap with `[lambda: i for i in range(3)]`, inspect `handlers[0].__closure__`, then fix it three ways: default argument, factory function and `functools.partial`.
- Write `def depth(n): return 0 if n == 0 else 1 + depth(n - 1)` and find the first `n` that raises RecursionError, then rewrite it as a loop.

## Modules, Packages & Imports [Basics]

> This lesson covers how Python code is split into files and folders and pulled back together: modules, packages, `__init__.py`, absolute and relative imports, `__name__`, the `sys.modules` cache, circular imports, `__all__`, the standard library you will use weekly, and installing dependencies with uv or pip into a project described by pyproject.toml. In a FastAPI service, `uvicorn app.main:app` is literally an import of the module `app.main` followed by reading its `app` attribute; routers live in their own modules, settings and the database engine are created once at import time, and most "works on my machine" Python failures turn out to be import problems: running a file by path instead of as a module, a circular import between models and services, a package missing from the virtual environment, or a local file named like a library.

### Why it exists
Python has one module system built into the language: every `.py` file is a module, and importing it runs the file once and caches the resulting module object. That gives every file its own namespace, so names cannot collide across files, and gives you process-wide singletons (settings, connection pools, compiled regexes) for free. Packages group modules under a dotted name so a large codebase and thousands of third-party libraries can coexist. Compared with Node there is no CommonJS versus ESM split and no default export, but imports are ordinary statements executed at runtime, so their order matters and two modules that import each other can fail halfway through loading. Dependency management sits outside the language: a virtual environment isolates each project's packages, and pyproject.toml plus a lockfile such as uv.lock pins them.

### In plain words
A module is a toolbox in a file, and importing it means asking for that toolbox. The first time anyone asks, Python builds the box by running the file from top to bottom, then puts it on a shared shelf called `sys.modules`; everyone who asks later gets that same box from the shelf. A package is a cabinet that holds several toolboxes under one label. If two toolboxes each insist that the other be finished before they can be finished, neither ever is, and that is a circular import.

### Walkthrough: what happens when you write import
1. **A file is a module.** `app/utils/text.py` is importable as `app.utils.text`, and its top-level names become attributes of the module object. There is no `export` keyword: every top-level name is importable, and a leading underscore marks a name as private by convention only.
   ```python
   # app/utils/text.py
   MAX_LEN = 200

   def clip(s: str) -> str:
       return s[:MAX_LEN]

   def _normalize(s: str) -> str:     # "private" by convention, still importable
       return s.strip()
   ```
2. **The import forms.** `import x` binds the module and keeps the namespace visible at every use (`json.loads`); `from x import y` binds one attribute. There is no default export. Avoid star imports outside the REPL, because they hide where names come from.
   ```python
   import json                             # json.dumps(...)
   import datetime as dt                   # alias
   from pathlib import Path                # one attribute
   from app.utils.text import clip, MAX_LEN
   from app.utils import text              # a submodule: text.clip(...)
   ```
3. **The first import finds, creates, runs and caches.** Python first checks `sys.modules`. On a miss it searches the folders in `sys.path` in order (the script's folder or the current directory, PYTHONPATH, the standard library, then the active environment's site-packages), creates an empty module object, stores it in `sys.modules`, runs the file from top to bottom and finally binds the name. Because local folders come first, a file in your project named `json.py`, `logging.py` or `openai.py` shadows the real library and imports fail in confusing ways.
   ```python
   import sys
   sys.path[:3]                 # where Python looks, in order
   "json" in sys.modules        # True once anything in the process imported json
   ```
4. **Every later import is a cache hit, so module code runs once.** Ten files importing `config` run it once per process. That is why a module-level `settings = Settings()` or database engine is a natural singleton, and why changing code needs a process restart (`uvicorn --reload` restarts the worker for you).
   ```python
   # config.py
   print("loading config")      # printed once, however many modules import config
   settings = {"db_url": "postgresql://localhost/app"}
   ```
5. **`from x import y` copies a reference at import time.** If `x` later rebinds `y`, your name still points at the old object. JS ESM imports are live bindings; Python's are not. The same rule decides where to patch in tests: patch the name where it is used, such as `mock.patch("app.services.send_email")`, not where it was defined.
   ```python
   # counter.py contains: count = 0, and bump() does `global count; count += 1`
   import counter
   from counter import count
   counter.bump()
   print(counter.count, count)      # 1 0
   ```
6. **`__name__` and the main guard.** Every module has `__name__`: its dotted name when imported, `"__main__"` when it is the program being run, either by path or with `python -m`. Put script-only code under the guard so importing the module, for example from a test, does not run it. The CommonJS equivalent is `require.main === module`.
   ```python
   def main() -> None:
       print("seeding database")

   if __name__ == "__main__":      # runs for `python seed.py`, not for `import seed`
       main()
   ```
7. **Packages are folders with `__init__.py`.** The `__init__.py` file runs the first time the package or any of its submodules is imported, so keep it light; it is a good place to re-export a small public API. Folders without one still import as namespace packages (3.3+), but an explicit `__init__.py` avoids surprises with tools.
   ```python
   # app/schemas/__init__.py: lets callers write `from app.schemas import UserIn`
   from .user import UserIn, UserOut
   from .order import OrderIn
   ```
8. **Absolute versus relative imports.** Absolute imports name the full path from the top-level package, and PEP 8 prefers them. Relative imports use dots: one for the current package, two for its parent. They only work when the module was loaded as part of a package; running the file by path gives `ImportError: attempted relative import with no known parent package`.
   ```python
   # inside app/routers/users.py
   from app.core.config import settings     # absolute
   from ..core.config import settings       # relative: up one package, then core.config
   from .common import paginate             # relative: same package (app.routers)
   ```
9. **`__all__` declares the public names.** It controls what `from module import *` brings in and documents the intended API. It does not stop anyone from importing other names explicitly.
   ```python
   # app/schemas/__init__.py
   from .user import UserIn, UserOut
   from .order import OrderIn

   __all__ = ["UserIn", "UserOut", "OrderIn"]
   ```

### Walkthrough: from one file to an installable project with uv
1. **One virtual environment per project.** Python installs packages into an interpreter's site-packages, so each project gets its own environment, usually `.venv`. It plays the role of `node_modules`, but it also pins which interpreter runs. uv creates and uses `.venv` automatically.
   ```bash
   uv init --package billing-api        # pyproject.toml plus src/billing_api/__init__.py
   cd billing-api
   uv add fastapi "uvicorn[standard]"   # updates pyproject.toml and uv.lock, installs into .venv
   uv add --dev pytest                  # goes into the development dependency group
   uv run uvicorn billing_api.main:app --reload
   ```
2. **pip still works.** pip installs into whichever environment is active, so create and activate one first. Run it as `python -m pip` so pip always matches the interpreter you mean. `uv pip install` is a faster drop-in for the same commands.
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install fastapi
   python -m pip install -e .           # your own project, editable
   ```
3. **pyproject.toml declares the project.** `[project]` holds the name, the supported Python versions and the runtime dependencies; uv puts development tools in `[dependency-groups]`. The exact resolved versions go into `uv.lock`, which you commit, like `package-lock.json`.
   ```toml
   [project]
   name = "billing-api"
   version = "0.1.0"
   requires-python = ">=3.12"
   dependencies = [
       "fastapi>=0.115",
       "uvicorn[standard]>=0.30",
   ]

   [dependency-groups]
   dev = ["pytest>=8"]
   ```
4. **The src layout.** Put the package in `src/billing_api/` instead of the repository root. With a root-level package, tests can import the folder straight from the current directory and hide packaging mistakes such as a missing file or dependency. With src, the code is importable only once it is installed (uv installs your project into `.venv` in editable mode), so tests exercise what you ship.
   ```text
   billing-api/
     pyproject.toml
     uv.lock
     src/billing_api/__init__.py
     src/billing_api/main.py
     tests/test_health.py
   ```
5. **Entry points are import strings.** `uvicorn billing_api.main:app` means "import the module `billing_api.main` and read its `app` attribute"; `python -m billing_api.cli` runs a module as the main program with its package context intact. Underneath, both are `importlib`.
   ```python
   import importlib

   module = importlib.import_module("billing_api.main")   # cached in sys.modules
   app = getattr(module, "app")
   ```
6. **Keep the dependency direction one-way.** Routers import services, services import models, and nothing imports upwards. Two modules importing each other at top level means the second one sees the first only half-run, which is how circular import errors happen.
   ```python
   # billing_api/routers/invoices.py
   from billing_api.services.invoices import create_invoice   # down: fine
   # billing_api/services/invoices.py must never import from billing_api.routers
   ```

### Walkthrough: a tour of the standard library you will use every week
1. **pathlib for files and folders.** `Path` objects join with `/`, read and write files and glob. Resolve paths relative to `__file__`, not to the current working directory, so the code works wherever the process starts.
   ```python
   from pathlib import Path

   BASE = Path(__file__).resolve().parent
   prompt = (BASE / "prompts" / "system.txt").read_text(encoding="utf-8")
   for p in sorted(BASE.glob("data/*.json")):
       print(p.name, p.stem, p.suffix)      # users.json users .json
   ```
2. **json for parsing and serializing.** `loads` and `dumps` work on strings, `load` and `dump` on files. JSON null maps to None and true to True; tuples become lists; datetimes and sets raise TypeError unless you pass `default=`.
   ```python
   import json
   from datetime import datetime, timezone

   payload = json.loads('{"id": 7, "tags": ["a"]}')     # str to dict
   json.dumps({"at": datetime.now(timezone.utc)})       # TypeError: Object of type datetime is not JSON serializable
   json.dumps({"at": datetime.now(timezone.utc)}, default=str)   # works
   json.dumps(payload, indent=2, ensure_ascii=False)    # pretty, keeps non-ASCII text readable
   ```
3. **datetime and zoneinfo for time.** Use aware datetimes (with a time zone) for anything real; comparing naive and aware values raises TypeError. `datetime.utcnow()` returns a naive value and is deprecated in 3.12. Since 3.11, `fromisoformat` accepts most ISO 8601 strings, including a trailing Z.
   ```python
   from datetime import datetime, timedelta, timezone
   from zoneinfo import ZoneInfo

   now = datetime.now(timezone.utc)
   expires = now + timedelta(minutes=15)
   local = now.astimezone(ZoneInfo("Asia/Dubai"))
   datetime.fromisoformat("2026-11-02T10:00:00Z")     # aware, UTC
   ```
4. **collections and itertools for data shaping.** collections is the previous lesson. itertools works lazily on any iterable: `chain` joins, `islice` takes a slice of an iterator, `batched` (3.12+) chunks inputs for batch embedding calls, and `groupby` groups consecutive items, so sort by the same key first.
   ```python
   import itertools

   list(itertools.chain([1, 2], [3]))          # [1, 2, 3]
   list(itertools.islice(range(100), 3))       # [0, 1, 2]
   list(itertools.batched(range(5), 2))        # [(0, 1), (2, 3), (4,)]
   events.sort(key=lambda e: e["user"])
   for user, group in itertools.groupby(events, key=lambda e: e["user"]):
       print(user, len(list(group)))
   ```
5. **functools for caching and partial application.** `lru_cache` memoizes a function by its (hashable) arguments, `cache` (3.9+) is the unbounded version, `partial` pre-fills arguments, and `wraps` is what you use when writing decorators. The `@` line is decorator syntax, covered in a later lesson.
   ```python
   from functools import lru_cache, partial

   @lru_cache(maxsize=1024)
   def tokenizer_for(model: str) -> dict:
       return {"model": model}             # imagine an expensive load here

   parse_binary = partial(int, base=2)
   parse_binary("101")                     # 5
   ```
6. **re for regular expressions.** Write patterns as raw strings so backslashes reach the regex engine, and compile reused patterns at module level. `match` anchors at the start, `search` looks anywhere, `fullmatch` requires the whole string.
   ```python
   import re

   TICKET = re.compile(r"\b[A-Z]{2,10}-\d+\b")
   TICKET.findall("Fixes API-42 and WEB-7")      # ['API-42', 'WEB-7']
   re.match(r"\d+", "abc123")                    # None: match anchors at the start
   re.search(r"\d+", "abc123").group()           # '123'
   re.fullmatch(r"\d{6}", "560001") is not None  # True
   ```
7. **os and sys for the process.** Environment variables are always strings; `os.environ[...]` raises KeyError for a missing one, which is the right failure for required config at startup. `sys` holds the interpreter's state: `argv`, `path`, `modules`, `version_info`, and `exit`, which raises SystemExit.
   ```python
   import os
   import sys

   db_url = os.environ["DATABASE_URL"]           # required: fail fast if missing
   workers = int(os.getenv("WORKERS", "4"))      # optional: convert from str yourself
   if sys.version_info < (3, 12):
       sys.exit("Python 3.12+ required")         # prints the message, exit code 1
   ```
8. **logging instead of print.** Each module creates `logger = logging.getLogger(__name__)`, so log lines carry the module's dotted name. Pass arguments separately so formatting only happens when the level is enabled, use `logger.exception` inside `except` to include the traceback, and configure handlers once at the entry point. `basicConfig` does nothing if the root logger already has handlers, unless you pass `force=True`.
   ```python
   import logging

   logger = logging.getLogger(__name__)

   def charge(order_id: str) -> None:
       logger.info("charging order %s", order_id)
       try:
           raise TimeoutError("gateway slow")
       except TimeoutError:
           logger.exception("charge failed for %s", order_id)   # includes the traceback

   if __name__ == "__main__":
       logging.basicConfig(level=logging.INFO)
       charge("o-1")
   ```

### Concepts you must understand
- Every `.py` file is a module and every top-level name in it is importable; a leading underscore and `__all__` only signal intent.
- The first import runs a module from top to bottom and caches it in `sys.modules`; every later import in the process gets the same object, so module-level objects are per-process singletons.
- `from x import y` binds `y` once, at import time; if `x` rebinds it later you keep the old object, so read `x.y` for live values and patch names where they are used.
- `__name__` is `"__main__"` only for the module being run; put script code under `if __name__ == "__main__":`.
- Relative imports work only inside a package loaded as a package; run entry points with `python -m package.module` or through an installed command, never by file path.
- A circular import fails when module A imports a name from B while B is still importing A; fix the dependency direction first, then consider type-only imports, importing the module instead of the name, or a local import.
- `sys.path` is searched in order, so a local file named like a library (`json.py`, `openai.py`) shadows the real one.
- Dependencies are declared in pyproject.toml, pinned in a committed lockfile and installed into a per-project `.venv`, never into the system Python.
- The standard library covers files (pathlib), JSON, time zones (datetime with zoneinfo), lazy iteration (itertools), caching (functools), regex (re), the environment and process (os, sys) and logging (`logging.getLogger(__name__)`, configured once at the entry point).

| JavaScript | Python | Note |
|---|---|---|
| `import { clip } from "./text.js"` | `from app.utils.text import clip` | Dotted path from the top-level package, no file extension |
| `export function clip() {}` | `def clip():` at top level | Every top-level name is importable |
| `export default app` | No default export | `uvicorn app.main:app` names the attribute explicitly |
| `index.js` in a folder | `__init__.py` | Runs when the package is first imported |
| `require.cache` | `sys.modules` | Both cache a module after its first load |
| ESM live bindings | `from x import y` copies the reference | Read `x.y` to see rebinding |
| `require.main === module` | `if __name__ == "__main__":` | |
| `package.json` dependencies | `pyproject.toml` `[project] dependencies` | Dev tools go in `[dependency-groups]` with uv |
| `package-lock.json` | `uv.lock` | Commit it; install with `uv sync --locked` |
| `node_modules/` | `.venv/` | The environment also pins the interpreter |
| `npm install express` | `uv add fastapi` or `pip install fastapi` | `uv add` also updates pyproject.toml and the lock |
| `process.env.DB_URL` | `os.environ["DB_URL"]` or `os.getenv("DB_URL")` | Always strings; convert numbers yourself |

### Q. The app crashes at startup with `ImportError: cannot import name 'User' from partially initialized module 'app.models' (most likely due to a circular import)`. Find the cause and fix it.
**Short answer (45 seconds):** Read the traceback from the bottom to find the cycle: `app.models` imports `app.services`, which imports `User` from `app.models` while `app.models` has only run its first line. The real fix is the dependency direction: models are the lowest layer and must not import services. If the reverse import is needed only for type hints, guard it with `TYPE_CHECKING`; importing the module instead of the name, or importing inside the function, are fallbacks.

**Deeper explanation:** The two files:

```python
# app/models.py
from app.services import send_welcome

class User:
    def __init__(self, email: str) -> None:
        self.email = email

# app/services.py
from app.models import User

def send_welcome(user: User) -> None:
    ...
```

What happens: `main.py` imports `app.models`. Python creates an empty module, stores it in `sys.modules` and starts running it. Line 1 imports `app.services`, which starts running and asks for `User` from `app.models`. That module is already in `sys.modules`, so Python does not run it again, but it is only partially initialized and `User` does not exist yet, hence the error.

Fixes, best first. One: move the call so models never import services, for example the router calls `send_welcome(user)` after creating the user. Two: when `services` needs `User` only for annotations, make the import type-only:

```python
# app/services.py
from __future__ import annotations      # annotations are no longer evaluated at runtime
from typing import TYPE_CHECKING

if TYPE_CHECKING:                       # False at runtime, True for mypy and pyright
    from app.models import User

def send_welcome(user: User) -> None:
    ...
```

Do not use this trick for Pydantic models or FastAPI parameters, which need the real class at runtime. Three: `import app.models` and use `app.models.User` inside the function, since the attribute is looked up at call time; it works only when `app.models` is imported first, so it stays fragile. Four: an import inside the function body as a last resort.

**Follow-ups they will ask:**
- Why "partially initialized"?: the module object is put in `sys.modules` before its code runs, so a second import finds it with only the names defined so far.
- Why does reordering imports in `main.py` sometimes "fix" it?: whichever module loads first decides which half-built module the other one sees; fix the design instead.
- How do you stop it coming back?: an import-linter contract for layers, plus a test that imports every module.

**Mistakes to avoid:**
- Sprinkling local imports everywhere instead of fixing the layering.
- Merging both files into one giant module just to make the error disappear.

### Q. `python app/main.py` fails with `ImportError: attempted relative import with no known parent package`, yet `uvicorn app.main:app` works. Explain and fix it.
**Short answer (45 seconds):** Running a file by path makes it a top-level script named `"__main__"` with no parent package, and puts its own folder, not the project root, at the front of `sys.path`. So relative imports have nothing to be relative to, and even `import app` fails. uvicorn imports `app.main` as a module of the `app` package from the project root. Run `python -m app.main` from the root, or better, install the project and start it through uvicorn or a console script.

**Deeper explanation:** The layout:

```text
project/
  app/
    __init__.py
    config.py
    main.py          # from .config import settings
```

```bash
cd project
python app/main.py   # ImportError: attempted relative import with no known parent package
python -m app.main   # works: runs app/main.py as module app.main, with __name__ == "__main__"
uvicorn app.main:app # works: imports app.main from the current directory
```

With `python -m app.main`, Python puts the current directory on `sys.path`, imports the `app` package and runs `main.py` as the program while its package is set to `app`, so `.config` resolves to `app.config`. With a path, Python only knows a file; `__package__` is empty and `sys.path[0]` is `project/app/`.

Switching to absolute imports does not rescue the by-path run: `from app.config import settings` then fails with `ModuleNotFoundError: No module named 'app'`, because `project/` is not on `sys.path`. The durable setup is a src layout with the project installed into `.venv` (`uv sync` does this in editable mode), absolute imports everywhere, and entry points started as `uvicorn app.main:app`, `python -m app.cli` or a `[project.scripts]` command.

**Follow-ups they will ask:**
- Why not add `sys.path.insert(0, "..")` at the top?: it depends on the working directory, breaks in Docker and in tests, and hides packaging bugs.
- Pytest cannot import the package either. Why?: same cause; install the project, or set `pythonpath = ["src"]` under `[tool.pytest.ini_options]`.
- Does `__name__ == "__main__"` still work with `-m`?: yes, the guard runs; only the package context differs.

**Mistakes to avoid:**
- Converting every relative import to absolute and still running the file by path.
- Running from inside the `app` folder, which changes what the current directory puts on `sys.path`.

### Q. Predict the output of this code and explain it.
**Short answer (45 seconds):** It prints `loading counter` once, then `2 0 True`, then `__main__ counter`. The module body runs only on the first import; later imports, including the alias, return the cached object from `sys.modules`. `from counter import count` copied the reference to the integer 0 at import time, and rebinding `counter.count` inside `bump()` never touches that copy.

**Deeper explanation:** Two files:

```python
# counter.py
print("loading counter")
count = 0

def bump() -> None:
    global count
    count += 1

# main.py, run with: python main.py
import counter
from counter import count
import counter as again

counter.bump()
counter.bump()
print(counter.count, count, again is counter)
print(__name__, counter.__name__)
```

Output:

```text
loading counter
2 0 True
__main__ counter
```

The first `import counter` runs the file and caches it. `from counter import count` finds the module in the cache and binds a new name `count` in `main` to the object `counter.count` points to right now: the int 0. `bump()` makes `counter.count` point to 1, then 2; integers are immutable, so `main.count` still points to 0. `import counter as again` is another cache hit, so it is the very same object. `main.py` is the program, so its `__name__` is `"__main__"`.

This explains a classic test bug: `from app.config import settings` in a service, then a test assigns `app.config.settings = test_settings`. The service still holds the old object. Patch where the name is used (`app.services.settings`), or mutate the shared object instead of rebinding it.

**Follow-ups they will ask:**
- How would `main` see the live value?: read `counter.count` through the module each time, or call an accessor function.
- Can one file be loaded twice?: yes, if you run `python counter.py` and the code also does `import counter`, the file runs as `__main__` and again as `counter`, creating two separate copies of its globals.
- What does `uvicorn --reload` do here?: it restarts the process, so every module runs again from scratch.

**Mistakes to avoid:**
- Expecting ESM-style live bindings from `from x import y`.
- Thinking each importing file re-runs the module.

### Q. Write a function that loads every JSON prompt template in a folder, skips broken files with a log line and returns them keyed by file name.
**Short answer (45 seconds):** Use pathlib to glob `*.json` in a folder resolved relative to `__file__`, read each file with an explicit UTF-8 encoding and `json.loads`, catch only `OSError` and `json.JSONDecodeError`, log a warning through a module logger and continue, and key the result by `path.stem`. Load once at startup, not per request.

**Deeper explanation:**

```python
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

def load_templates(folder: Path = TEMPLATES_DIR) -> dict[str, dict]:
    templates: dict[str, dict] = {}
    for path in sorted(folder.glob("*.json")):          # sorted: glob order is not guaranteed
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("skipping %s: %s", path.name, exc)
            continue
        if not isinstance(data, dict):
            logger.warning("skipping %s: top level is %s", path.name, type(data).__name__)
            continue
        templates[path.stem] = data                     # "summarize.json" becomes "summarize"
    return templates
```

Why each choice: `Path(__file__).resolve().parent` anchors the folder to the module, so the function works whether uvicorn starts from the repository root, a Docker WORKDIR or a test runner. `sorted` gives the same order on every OS, which keeps logs and tests stable. An explicit encoding avoids platform defaults. Catching only the two expected exceptions lets real bugs surface; `JSONDecodeError` is a subclass of ValueError and its message includes the line and column. The `%s` arguments are formatted only if WARNING is enabled. Reading files is O(total bytes).

Call it once, at module level or in the FastAPI lifespan handler, and keep the result; re-reading disk on every request adds latency for no benefit.

**Follow-ups they will ask:**
- Templates live in nested folders?: use `folder.rglob("*.json")` and key by `path.relative_to(folder).with_suffix("").as_posix()`.
- How do you validate the shape?: define a Pydantic model and call `Template.model_validate(data)`, logging the ValidationError.
- Skip or fail?: in production, failing at startup is often better than serving without a prompt; make strictness a flag.

**Mistakes to avoid:**
- `open("templates/x.json")`, which is relative to the working directory, not the module.
- A bare `except:` or `print()` instead of a narrow except and a logger.

### Q. A reminder job crashes with `TypeError: can't compare offset-naive and offset-aware datetimes`. Find and fix the bug.
**Short answer (45 seconds):** The timestamp from the API carries an offset such as +04:00, so `fromisoformat` returns an aware datetime, while `datetime.now()` returns a naive local time, and Python refuses to order the two rather than guess. Use aware datetimes everywhere: `datetime.now(timezone.utc)` for the current time, reject or explicitly localize naive input, store UTC, and convert with zoneinfo only for display.

**Deeper explanation:** The buggy code:

```python
from datetime import datetime

def is_due(remind_at_iso: str) -> bool:
    remind_at = datetime.fromisoformat(remind_at_iso)   # "2026-11-02T09:30:00+04:00"
    return remind_at <= datetime.now()                  # naive: no time zone
```

The fix:

```python
from datetime import datetime, timezone

def is_due(remind_at_iso: str) -> bool:
    remind_at = datetime.fromisoformat(remind_at_iso)
    if remind_at.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return remind_at <= datetime.now(timezone.utc)
```

Aware comparisons are exact across offsets: 09:30+04:00 is the same instant as 05:30 UTC, and Python compares instants. A naive datetime has no zone, so it could mean server time, user time or UTC; Python makes you decide. Here the decision is to reject naive input, because guessing is how reminders fire four hours early for a user in Dubai. If a legacy client sends naive strings that are known to be UTC, attach the zone explicitly with `.replace(tzinfo=timezone.utc)`.

The rest of the pipeline: store `timestamptz` in Postgres (it stores the instant, normalized to UTC), do arithmetic in UTC, and convert with `astimezone(ZoneInfo("Asia/Kolkata"))` only when rendering for a user.

**Follow-ups they will ask:**
- Why not use `datetime.utcnow()`?: it returns a naive value, so the comparison still fails, and it is deprecated in 3.12.
- What about daylight saving?: use zone names like `ZoneInfo("Europe/London")`, not fixed offsets, and do arithmetic in UTC.
- Does `==` raise too?: no, naive and aware values are simply never equal; only ordering comparisons raise.

**Mistakes to avoid:**
- Stripping `tzinfo` from the aware value to make the error go away, which silently compares different instants.
- Storing local times without an offset in the database.

### Q. You are starting a new FastAPI service. Lay out the project, imports and dependencies so it runs the same on your laptop, in CI and in Docker.
**Short answer (45 seconds):** A src layout created with `uv init --package`, absolute imports from the package name, a one-way dependency direction (routers to services to models) so cycles cannot form, dependencies declared in pyproject.toml and pinned in a committed uv.lock, and every environment installing with `uv sync --locked` and starting the app with `uvicorn billing_api.main:app`.

**Deeper explanation:**

```text
billing-api/
  pyproject.toml          # dependencies and tool settings
  uv.lock                 # exact versions, committed
  .python-version         # interpreter version uv will use
  src/billing_api/
    __init__.py
    main.py               # app = FastAPI(); include routers; configure logging
    core/config.py        # settings read from env vars once, at import
    routers/invoices.py   # HTTP only: parse, call a service, return
    services/invoices.py  # business logic; imports models, never routers
    models.py
  tests/test_invoices.py
```

Decisions in order. Requirements first: same versions everywhere, fast installs, no import surprises. Layout: src, so tests import the installed package. Imports: absolute (`from billing_api.core.config import settings`) and layered downwards only, enforced with an import-linter contract. Configuration: environment variables read once in `core/config.py` (pydantic-settings is the common choice) so importing the module gives a singleton. Dependencies: `uv add fastapi "uvicorn[standard]"`, `uv add --dev pytest ruff`. CI: `uv sync --locked` fails if pyproject.toml and the lock disagree, then `uv run pytest`. Docker:

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY . .
RUN uv sync --locked --no-dev
CMD ["/app/.venv/bin/uvicorn", "billing_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Copying only the dependency files first lets Docker cache the dependency layer, so code changes rebuild in seconds; a `.dockerignore` that excludes `.venv` stops `COPY . .` from shipping your laptop's environment. What to measure: image build time, cold start time and whether `uv sync --locked` ever fails in CI (lock drift).

**Follow-ups they will ask:**
- Several services in one repository?: a uv workspace shares one lockfile across member packages.
- A teammate only uses pip?: `uv export --format requirements.txt` produces a pinned requirements file from the lock.
- Why pin the uv image?: `latest` changes under you; pin a version tag in real builds.

**Mistakes to avoid:**
- An unpinned requirements.txt, so CI and production resolve different versions.
- `sys.path` hacks in place of an installed package.

### Practice
- Practice kit: open `python-practice/exercises/p09_modules.py`, implement each function, then run `uv run --with pytest pytest tests/test_p09_modules.py` from the `python-practice` folder.
- Create `a.py` with `from b import g` plus `def f(): ...`, and `b.py` with `from a import f` plus `def g(): ...`. Run `python -c "import a"`, read the circular import error, then fix it by moving `f` into a third module.
- Make a package `shop/` with `__init__.py`, `cart.py` and `prices.py`, where `cart.py` does `from .prices import total`. Run `python shop/cart.py` and then `python -m shop.cart` from the parent folder, and explain the difference.
- In a scratch folder run `uv init --package demo`, then `uv add httpx`, and read the generated `pyproject.toml` and `uv.lock`.
