## Strings & Text [Basics]

> Strings are the most common type in a FastAPI or AI backend: path and query parameters, headers, prompt templates, LLM output you must clean and parse, log lines, slugs and IDs. This section covers indexing and slicing, immutability, the everyday methods, f-string format specs, raw and multi-line strings, `str` versus `bytes`, building text efficiently and the `re` module. Interviewers use string tasks as warm-ups: they watch whether you slice fluently, know that strings are immutable, and reach for `join` and f-strings instead of JavaScript habits.

### Why it exists
Python 3 made `str` a sequence of Unicode code points and moved raw data into a separate `bytes` type, because Python 2 mixed the two and programs crashed on the first customer name with an accent. Strings are immutable so they can be hashed and used as dict keys, shared between variables without defensive copies, and cached by the interpreter. Slicing and a large method set exist so that common text work is one expression instead of an index loop. f-strings (3.6) replaced `%` formatting and `str.format()` because the value sits exactly where it is printed. The cost of immutability is that every "change" builds a new string, which is why building text in a loop calls for `join`.

### In plain words
A Python string is like a row of numbered letter tiles glued to a board. You can read any tile by its number, count from the right end with negative numbers, or copy out a stretch of tiles, but you cannot pry one tile off and swap it; you make a new board instead. Text you see on screen is a `str`, and the same text packed for a network cable or a file is `bytes`; encoding is the packing step and decoding the unpacking. f-strings are fill-in-the-blank templates that also say how each blank should look, such as two decimals or right-aligned. Regular expressions are a small search language for when plain methods are not enough.

### Walkthrough: indexing, slicing and immutability
1. **Index from either end**: Indexes start at 0, and negative indexes count from the end, so `s[-1]` is the last character. In JavaScript `s[-1]` is `undefined`; the closest is `s.at(-1)`.
   ```python
   s = "fastapi"
   s[0]     # 'f'
   s[-1]    # 'i'
   s[-3]    # 'a'
   s[100]   # IndexError: string index out of range
   ```
2. **Slice with start:stop**: `s[start:stop]` copies from `start` up to but not including `stop`. Either side can be left out, and a slice never raises for out-of-range bounds, it just clips. JavaScript's equivalent is `s.slice(0, 4)`.
   ```python
   s[0:4]    # 'fast'
   s[4:]     # 'api'
   s[:-3]    # 'fast'  (everything except the last 3)
   s[2:100]  # 'stapi' (no error)
   ```
3. **Add a step**: The third number is the step. A negative step walks backwards, so `s[::-1]` reverses a string, which in JavaScript takes `[...s].reverse().join("")`.
   ```python
   s[::2]     # 'fsai'    (every second character)
   s[::-1]    # 'ipatsaf' (reversed)
   s[5:2:-1]  # 'pat'     (from index 5 down to, not including, index 2)
   ```
4. **Strings are immutable**: You cannot assign to an index. Every method returns a new string and leaves the original alone, so keep the result. JavaScript strings are immutable too, but sloppy-mode JS silently ignores `s[0] = "F"` while Python raises.
   ```python
   s[0] = "F"          # TypeError: 'str' object does not support item assignment
   s.upper()           # 'FASTAPI', but s is still 'fastapi'
   s = s.capitalize()  # rebind the name to the new string: 'Fastapi'
   ```
5. **No char type, and len counts code points**: `s[0]` is a one-character `str`. `len()` counts Unicode code points, not UTF-16 units as JavaScript does, so a character outside the Basic Multilingual Plane, such as an emoji, has length 1 in Python and 2 in JS.
   ```python
   type(s[0])          # <class 'str'>
   len("héllo")        # 5
   len("\U0001F600")   # 1 (an emoji); in JS "\u{1F600}".length is 2
   ```
6. **Membership with in**: `in` checks for a substring; it is the Python spelling of `includes`. `not in` is the negation and reads like English.
   ```python
   "api" in "fastapi"      # True
   "API" in "fastapi"      # False (case-sensitive)
   "x" not in "fastapi"    # True
   ```

### Walkthrough: methods, f-strings and building text
1. **split and join**: `split(sep)` keeps empty pieces between repeated separators, while `split()` with no argument splits on any run of whitespace and drops empties. `join` is a method on the separator, the mirror image of JS `arr.join(",")`, and every item must already be a `str`.
   ```python
   "a,b,,c".split(",")         # ['a', 'b', '', 'c']
   "  a \t b\n".split()        # ['a', 'b']
   "k=v=w".split("=", 1)       # ['k', 'v=w']  (maxsplit)
   ",".join(["a", "b"])        # 'a,b'
   ",".join([1, 2])            # TypeError: sequence item 0: expected str instance, int found
   ",".join(map(str, [1, 2]))  # '1,2'
   ```
2. **strip removes characters, not a substring**: `strip(chars)` removes any of those characters from both ends, which surprises people. To remove an exact prefix or suffix use `removeprefix` and `removesuffix` (3.9+).
   ```python
   "  hi \n".strip()                  # 'hi'
   "www.example.com".strip("w.moc")   # 'example'  (a character set!)
   "report.csv".removesuffix(".csv")  # 'report'
   ```
3. **Search, replace and count**: `find` returns -1 when the text is missing and `index` raises `ValueError`. `startswith` and `endswith` accept a tuple of options. `replace` replaces every occurrence unless you pass a count (JS `replace` with a string replaces only the first). `count` counts non-overlapping matches.
   ```python
   path = "/v2/users/42"
   path.startswith(("/v1", "/v2"))  # True
   path.find("orders")              # -1
   path.index("orders")             # ValueError: substring not found
   "a-b-c".replace("-", "_", 1)     # 'a_b-c'
   "banana".count("an")             # 2
   ```
4. **Case methods**: `upper`, `lower`, `title` and `capitalize` all return new strings. For case-insensitive comparison use `casefold()`, which also handles letters such as the German "ß". `title()` is naive about apostrophes.
   ```python
   "Straße".lower()          # 'straße'
   "Straße".casefold()       # 'strasse'
   "they're bill's".title()  # "They'Re Bill'S"
   ```
5. **f-strings with format specs**: After a colon you add a format spec: fill, alignment (`<` left, `>` right, `^` center), width, `,` or `_` grouping, precision and type. `!r` formats with `repr()` (quotes included, useful in logs), and `=` (3.8+) prints the expression and its value. JS template literals have no format spec, so you reach for `toFixed`, `padStart` or `Intl.NumberFormat`.
   ```python
   name, price, n, ratio = "Asha", 1234567.5, 1234567, 0.4567
   f"{price:.2f}"      # '1234567.50'
   f"{n:,}"            # '1,234,567'   (f"{n:_}" gives '1_234_567')
   f"[{name:>8}]"      # '[    Asha]'
   f"[{name:*^10}]"    # '[***Asha***]'
   f"{42:05d}"         # '00042'
   f"{ratio:.1%}"      # '45.7%'
   f"{price:>15,.2f}"  # '   1,234,567.50'
   f"{name!r}"         # "'Asha'"
   f"{price=:.2f}"     # 'price=1234567.50'
   ```
6. **Build big strings with join, not +=**: Because strings are immutable, `out += piece` in a loop can create a new string each time and copy everything built so far, which is quadratic in the worst case. CPython sometimes optimises it, but do not rely on that: collect pieces in a list and call `"".join(parts)` once. The JS habit of `parts.push(...)` then `parts.join("")` is the same idea.
   ```python
   parts = []
   for row in rows:
       parts.append(f"{row['id']},{row['name']}")
   csv_text = "\n".join(parts)
   # or in one expression with a generator:
   csv_text = "\n".join(f"{r['id']},{r['name']}" for r in rows)
   ```

### Walkthrough: literals, bytes, regex and Unicode
1. **Quotes, escapes and multi-line strings**: Single and double quotes are equivalent. Escapes include `\n`, `\t`, `\\`, `\'`, `\"`, `\xNN` and `\uNNNN`. Triple quotes span lines, which suits prompt templates and SQL, and adjacent literals inside parentheses are joined at compile time. `textwrap.dedent` strips the common indentation from an indented triple-quoted block.
   ```python
   "caf\u00e9"                    # 'café'
   prompt = """You are a support agent.
   Answer in {language}."""
   prompt.format(language="Hindi")
   sql = ("SELECT id, email "
          "FROM users WHERE active")  # one string, no + needed
   ```
2. **Raw strings**: An `r` prefix turns off escape processing, so backslashes stay literal. Use raw strings for every regex and for Windows paths. In 3.12 an invalid escape such as `"\d"` in a normal string gives a `SyntaxWarning`.
   ```python
   len("\n"), len(r"\n")      # (1, 2)
   r"C:\new\table"            # backslashes kept, no newline or tab
   pattern = r"\d{4}-\d{2}"   # always raw for regex
   ```
3. **str versus bytes**: `str` is text; `bytes` is raw 8-bit data from sockets, files opened with `"rb"`, HTTP bodies and hash functions. `encode` turns text into bytes and `decode` turns bytes back into text. UTF-8 uses 1 to 4 bytes per character, so the lengths differ, and Python never mixes the two types silently. JavaScript's counterparts are `TextEncoder`, `TextDecoder` and Node's `Buffer`.
   ```python
   data = "café".encode("utf-8")   # b'caf\xc3\xa9'
   len("café"), len(data)          # (4, 5)
   data.decode("utf-8")            # 'café'
   "a" + b"b"                      # TypeError: can only concatenate str (not "bytes") to str
   b"\xff".decode("utf-8")         # UnicodeDecodeError: ... invalid start byte
   ```
4. **Always name the encoding**: `open()` without `encoding=` uses a platform-dependent default, which is how code that works on a Mac breaks on a Windows server. Pass `encoding="utf-8"` and choose an `errors=` policy (`"strict"`, `"replace"`, `"ignore"`) deliberately for untrusted input. The rule: decode at the input boundary, work in `str`, encode at the output boundary.
   ```python
   with open("notes.txt", encoding="utf-8") as f:
       text = f.read()
   b"caf\xff".decode("utf-8", errors="replace")   # 'caf\ufffd' (the replacement character)
   ```
5. **Regex: search, groups, findall, sub**: `re.search` finds the first match anywhere and returns a `Match` or `None`; `re.match` only checks at the start and `re.fullmatch` the whole string. `findall` returns strings, or tuples when the pattern has several groups. Named groups `(?P<name>...)` read better than numbers. `sub` replaces with a string (with `\1` backreferences) or a function. JS uses `match`, `matchAll` and `replace` with the `g` flag.
   ```python
   import re
   line = "order=A-1042 amount=499.00 order=B-77 amount=1250.50"
   re.findall(r"order=([A-Z]-\d+)", line)            # ['A-1042', 'B-77']
   re.findall(r"order=(\S+) amount=([\d.]+)", line)  # [('A-1042', '499.00'), ('B-77', '1250.50')]
   m = re.search(r"(?P<id>[A-Z]-\d+) amount=(?P<amt>[\d.]+)", line)
   if m:
       print(m["id"], m.group("amt"), m.groupdict())  # A-1042 499.00 {'id': 'A-1042', 'amt': '499.00'}
   re.sub(r"\d", "#", "card 4111")                   # 'card ####'
   re.sub(r"(\w+)@(\w+)", r"\2 at \1", "asha@corp")  # 'corp at asha'
   ```
6. **Compile the patterns you reuse**: `re.compile` returns a pattern object with the same methods. The module caches recent patterns anyway, so compiling is mostly about naming the pattern once and attaching flags such as `re.IGNORECASE`, `re.DOTALL` (dot matches newlines) or `re.VERBOSE`.
   ```python
   EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE)
   EMAIL.findall("Mail a.b@x.io or HELP@corp.co.in.")   # ['a.b@x.io', 'HELP@corp.co.in']
   ```
7. **Unicode normalisation in one line**: The same visible "é" can be one code point or an "e" plus a combining accent, and those compare unequal. `unicodedata.normalize("NFC", s)` makes them equal, so normalise user input before comparing or storing it. JavaScript has `s.normalize("NFC")`.
   ```python
   import unicodedata
   a, b = "caf\u00e9", "cafe\u0301"
   a == b, len(a), len(b)                                              # (False, 4, 5)
   unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b)  # True
   ```

### Concepts you must understand
- `str` is an immutable sequence of Unicode code points; every method returns a new string, so always use the return value.
- Indexing raises `IndexError` when out of range, slicing never does; `s[start:stop:step]` excludes `stop`, and `s[::-1]` reverses.
- `s[-0:]` is the whole string because `-0 == 0`; compute `len(s) - n` when `n` can be zero.
- `split()` with no argument splits on whitespace runs and drops empties, while `split(",")` keeps empty fields.
- `strip(chars)` removes a set of characters from the ends; use `removeprefix` and `removesuffix` for exact affixes.
- The f-string spec reads `[fill][align][width][,|_][.precision][type]`; `!r` and `=` are for debugging and log lines.
- Build long text with a list and `"".join(...)`; `+=` in a loop can be quadratic.
- `str` and `bytes` never mix: decode at the input boundary, work in `str`, encode at the output boundary, and always name UTF-8.
- Write regexes as raw strings; `search` scans, `match` anchors at the start, `fullmatch` covers the whole string, and each can return `None`.
- Normalise (NFC) before comparing user-entered text, and use `casefold()` for case-insensitive comparison.

| JavaScript | Python | Note |
|---|---|---|
| `s.at(-1)` | `s[-1]` | Negative indexes are built in |
| `s.slice(1, 4)` | `s[1:4]` | Slices also take a step: `s[::2]`, `s[::-1]` |
| `s.includes("x")` | `"x" in s` | An operator, not a method |
| `arr.join(",")` | `",".join(arr)` | The method lives on the separator; items must be `str` |
| `s.trim()` | `s.strip()` | `strip("x")` takes a set of characters |
| `s.indexOf("x")` | `s.find("x")` or `s.index("x")` | `find` returns -1, `index` raises `ValueError` |
| `s.replaceAll("a", "b")` | `s.replace("a", "b")` | Python replaces every occurrence by default |
| `` `Hi ${name}` `` | `f"Hi {name}"` | Python adds format specs: `f"{x:,.2f}"` |
| `n.toFixed(2)` | `f"{n:.2f}"` | `format(n, ".2f")` also works |
| `s.match(/\d+/g)` | `re.findall(r"\d+", s)` | No regex literal; use raw strings |
| `Buffer.from(s, "utf8")` | `s.encode("utf-8")` | Gives `bytes`; `decode` reverses it |
| `"\u{1F600}".length` is 2 | `len("\U0001F600")` is 1 | Python counts code points, not UTF-16 units |

### Q. Write a function that turns an article title into a URL slug, including titles with accents and punctuation.
**Short answer (45 seconds):** Normalise to NFKD so accented letters split into a base letter plus a combining mark, encode to ASCII with `errors="ignore"` to drop the marks, lowercase, replace every run of non-alphanumeric characters with one hyphen using `re.sub`, then strip hyphens from the ends. Each step is one linear pass, so it is O(n).

**Deeper explanation:**

```python
import re
import unicodedata

NON_SLUG = re.compile(r"[^a-z0-9]+")

def slugify(title: str) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", title)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return NON_SLUG.sub("-", ascii_text.lower()).strip("-")

slugify("  Café Déjà Vu: 2026 Edition! ")  # 'cafe-deja-vu-2026-edition'
slugify("!!!")                              # ''
```

NFKD decomposes "é" into "e" plus U+0301, and the ASCII encode with `"ignore"` silently drops anything outside ASCII, which is exactly the accent. The `+` in the pattern collapses ": " and "! " into a single hyphen instead of several, and `strip("-")` cleans the ends (here a one-character set is exactly what we want). The pattern is compiled once at module level because a FastAPI route that creates posts calls this on every request.

Edge cases: a title written entirely in a non-Latin script, such as Hindi or Arabic, becomes an empty string, because there is no ASCII base letter to keep. Production code falls back to an ID (`post-1042`) or uses a transliteration library. Two titles can also produce the same slug, so uniqueness belongs in the database as a unique index.

**Follow-ups they will ask:**
- How do you make slugs unique?: Append `-2`, `-3` or a short ID when the slug exists, and keep a unique index because two requests can race.
- Why NFKD and not NFC?: NFC composes "é" into one non-ASCII code point, so `"ignore"` would drop the whole letter and give "caf".
- How would you cap the length without cutting a word?: Slice to the limit, then `rsplit("-", 1)[0]` to drop the partial word.

**Mistakes to avoid:**
- Writing `[^a-z0-9]` without the `+`, which produces `cafe--deja` wherever two separators meet.
- Using only `.replace(" ", "-")`, which leaves punctuation and accents in the URL.
- Calling `encode("ascii")` without `"ignore"`, which raises `UnicodeEncodeError` on the first accent.

### Q. Predict the output of this slicing code and explain each line.
**Short answer (45 seconds):** Slices are `[start:stop:step]` with `stop` excluded, negative indexes count from the end, out-of-range bounds clip silently, and a start after the stop with a positive step gives an empty string. The trap is the last line: `-0` is just `0`, so it prints the whole token instead of nothing.

**Deeper explanation:**

```python
s = "interview"
print(s[2:5])      # ter
print(s[-4:])      # view
print(s[::-2])     # wirti
print(s[5:2])      # (empty line)
print(s[:100])     # interview
print(s[-100:3])   # int
token = "sk-abc123"
print(token[-0:])  # sk-abc123
```

Index the word first: i0 n1 t2 e3 r4 v5 i6 e7 w8. `s[2:5]` takes indexes 2, 3 and 4. `s[-4:]` starts four from the end, at index 5. `s[::-2]` starts at the last character and takes every second one going left: w, i, r, t, i. `s[5:2]` has a start after its stop with the default step of +1, so it is empty; `s[5:2:-1]` would give "vre". `s[:100]` and `s[-100:3]` show that slice bounds clip instead of raising, unlike `s[100]`, which raises `IndexError`.

The last line is a real bug pattern. A helper that shows the last `n` characters of an API key with `token[-n:]` works for every `n` except 0, where it leaks the entire secret. Compute the cut point explicitly:

```python
def mask(token: str, visible: int) -> str:
    cut = max(len(token) - visible, 0)
    return "*" * cut + token[cut:]
```

**Follow-ups they will ask:**
- What does `s[::-1]` cost?: O(n) time and a new string of the same length.
- Does `s[:]` copy a string?: It does not need to: strings are immutable, and CPython returns the same object. For a list, `xs[:]` makes a shallow copy.
- How would you reverse the words instead of the characters?: `" ".join(s.split()[::-1])`.

**Mistakes to avoid:**
- Expecting a slice to raise `IndexError` the way a single index does.
- Assuming a negative step still starts from the left when start and stop are omitted.
- Using `-n` as a slice start when `n` can be zero.

### Q. This function builds a CSV export of 200,000 rows. It is slow and crashes on numeric fields. Find and fix the bugs.
**Short answer (45 seconds):** There are three bugs: `",".join` requires strings, so integer IDs raise `TypeError`; `out +=` in a loop can copy the growing string on every row; and hand-joined fields break as soon as a name contains a comma or quote. Use the `csv` module writing into `io.StringIO`, which converts values, quotes fields and builds the output efficiently.

**Deeper explanation:**

```python
def to_csv(rows):
    out = ""
    for row in rows:
        out += ",".join([row["id"], row["name"], row["amount"]]) + "\n"
    return out
# TypeError: sequence item 0: expected str instance, int found
```

The fix uses the tool built for the job:

```python
import csv
import io

def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "amount"])
    for row in rows:
        writer.writerow([row["id"], row["name"], f"{row['amount']:.2f}"])
    return buf.getvalue()

to_csv([{"id": 1, "name": 'Rao, "Asha"', "amount": 1250.5}])
# 'id,name,amount\r\n1,"Rao, ""Asha""",1250.50\r\n'
```

`csv.writer` calls `str()` on non-string values, wraps fields containing commas or quotes in quotes and doubles inner quotes. Note its default line ending is `\r\n`, as the CSV standard specifies. `StringIO` is an in-memory text buffer that grows efficiently, so total work stays linear. The amount uses an explicit `:.2f`, because `str(1250.5)` is `'1250.5'` and finance teams expect two decimals.

If the file only ever holds simple values, the minimal fix is one `join` over a generator: `"\n".join(",".join(map(str, (r["id"], r["name"], r["amount"]))) for r in rows)`. For 200,000 rows served from FastAPI, a generator that yields lines into a `StreamingResponse` avoids holding the whole file in memory.

**Follow-ups they will ask:**
- Why is `+=` sometimes fast in CPython?: CPython can resize the string in place when nothing else references it; that is an implementation detail, not something PyPy or your next refactor guarantees.
- Excel shows "JosÃ©" for "José". Why?: Excel guessed a legacy encoding; write the file with `encoding="utf-8-sig"` so it starts with a BOM.
- How do you parse it back?: `csv.DictReader(io.StringIO(text, newline=""))`.

**Mistakes to avoid:**
- Fixing only the `TypeError` with `str()` and keeping `+=` and hand-made quoting.
- Formatting money with `str()` and losing trailing zeros.

### Q. Rewrite this JavaScript formatting code in idiomatic Python with f-strings.
**Short answer (45 seconds):** Every padding and number-formatting call maps to a format spec inside the f-string: `padEnd(12)` is `:<12`, `padStart(4)` is `:>4`, `toFixed(2)` is `:.2f`, a thousands separator is `,`, and a percentage is `%`, which multiplies by 100 for you. The result is one f-string per line instead of a chain of method calls.

**Deeper explanation:** The JavaScript:

```js
const line = (item) =>
  item.name.padEnd(12) +
  String(item.qty).padStart(4) + " x " +
  item.price.toFixed(2).padStart(10) + " = " +
  (item.qty * item.price).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
console.log(`Total: ${total.toFixed(2)} (${(discount * 100).toFixed(1)}% off)`);
```

The Python:

```python
def line(item: dict) -> str:
    total = item["qty"] * item["price"]
    return f"{item['name']:<12}{item['qty']:>4} x {item['price']:>10.2f} = {total:,.2f}"

line({"name": "Keyboard", "qty": 3, "price": 1499.5})
# 'Keyboard       3 x    1499.50 = 4,498.50'
print(f"Total: {total:.2f} ({discount:.1%} off)")   # discount=0.125 gives '12.5% off'
```

Read `:>10.2f` as "right-align in 10 columns, 2 decimals, fixed-point". `:,.2f` adds the thousands separator, which covers what `toLocaleString` was doing here. Width is a minimum, not a maximum: a 20-character name pushes the columns right, so add a precision to truncate (`:<12.12`). Widths can be dynamic with nested fields: `f"{name:<{width}}"`. Note that the `,` option always groups in threes; Indian lakh grouping (12,34,567) needs a locale library such as Babel.

**Follow-ups they will ask:**
- How do you format dates?: Datetime objects accept strftime codes in the spec: `f"{dt:%Y-%m-%d %H:%M}"`.
- Should log calls use f-strings?: `logger.info("user %s", user_id)` defers formatting until the record is actually emitted, which matters in hot paths; f-strings always format.
- How do you print a debug line quickly?: `f"{total=:.2f}"` prints `total=4498.50`.

**Mistakes to avoid:**
- Using `str(round(x, 2))`, which prints `2.5`, not `2.50`.
- Multiplying by 100 and then using the `%` type, which multiplies again.
- Writing new code with `%` formatting or `.format()` when an f-string is clearer.

### Q. An LLM sometimes wraps its JSON answer in prose or a markdown code fence. Write a function that pulls out the JSON object and parses it.
**Short answer (45 seconds):** Try a fenced block first with a non-greedy group, fall back to the span from the first `{` to the last `}` with `re.DOTALL`, then `json.loads` it and return `None` on failure so the caller can retry the model call. In production I would first turn on the provider's structured output or tool calling, and keep this as the safety net.

**Deeper explanation:**

```python
import json
import re

FENCED = re.compile(r"`{3}(?:json)?\s*(.*?)`{3}", re.DOTALL)
BRACES = re.compile(r"\{.*\}", re.DOTALL)

def extract_json(text: str) -> dict | None:
    if (m := FENCED.search(text)):
        candidate = m.group(1)
    elif (m := BRACES.search(text)):
        candidate = m.group(0)
    else:
        return None
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None

extract_json('Result: {"ok": true, "meta": {"n": 2}} hope that helps')
# {'ok': True, 'meta': {'n': 2}}
```

Three regex details carry this. Without `re.DOTALL`, `.` stops at newlines and multi-line JSON never matches. In the fence pattern, `.*?` is non-greedy so it stops at the first closing fence, not the last one in the reply. In the brace pattern, `.*` is greedy on purpose: from the first `{` to the last `}`, so nested objects stay whole. A regex cannot balance braces in general, so a reply with two separate objects produces an invalid span and returns `None`. For that case, `json.JSONDecoder().raw_decode(text, text.index("{"))` parses one value and reports where it ended. The `isinstance` check rejects a bare list or number.

**Follow-ups they will ask:**
- How do you avoid this parsing entirely?: Use JSON mode, structured outputs or a tool schema, then validate with Pydantic's `Model.model_validate_json`.
- The JSON is cut off mid-object. Why?: The response hit the token limit; check the finish reason and retry with a higher limit or a shorter schema.
- Why not `eval`?: Never execute model output; even `ast.literal_eval` rejects `true` and `null`.

**Mistakes to avoid:**
- Forgetting `re.DOTALL`, so the pattern works in a one-line test and fails on real replies.
- Using a greedy `.*` in the fence pattern, which swallows everything between two fenced blocks.
- Trusting the parsed dict without validating its fields.

### Q. This upload endpoint crashes with UnicodeDecodeError for some customers' CSV files. Find the cause and fix it.
**Short answer (45 seconds):** `raw.decode()` assumes UTF-8, but CSVs saved by Excel's plain "CSV" option and other Windows tools are often Windows-1252, where "é" is the single byte `0xE9`, which is invalid UTF-8. I would decode with `"utf-8-sig"` (which also strips a BOM), fall back to `cp1252`, and return a 400 if both fail, instead of silently ignoring bytes.

**Deeper explanation:** The failing code and error:

```python
@app.post("/import")
async def import_csv(file: UploadFile):
    raw = await file.read()
    text = raw.decode()            # UTF-8 by default
    rows = text.split("\n")
# UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 3: invalid continuation byte
```

In UTF-8, `0xE9` announces a three-byte character, so the next byte must be a continuation byte; a comma is not, hence "invalid continuation byte". There is a second, quieter bug: UTF-8 files saved by Excel often start with a BOM, so the first header decodes as `"\ufeffid"` and `row["id"]` later raises `KeyError`. A third: `split("\n")` leaves `\r` at the end of every Windows line.

```python
import csv
import io

def decode_upload(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("unsupported file encoding")

text = decode_upload(b"id,name\r\n1,Jos\xe9\r\n")
list(csv.DictReader(io.StringIO(text, newline="")))   # [{'id': '1', 'name': 'José'}]
```

In the endpoint, catch the `ValueError` and raise `HTTPException(status_code=400, detail="Upload a UTF-8 CSV")`. Order matters: try UTF-8 first, because cp1252 accepts most byte sequences and would turn valid UTF-8 "é" into "Ã©" (mojibake). Latin-1 never fails at all, which is why it is a poor fallback: it hides the problem.

**Follow-ups they will ask:**
- Can you detect the encoding reliably?: Not with certainty; libraries such as charset-normalizer guess. The robust answer is a contract that says UTF-8 plus a clear 400.
- The file is 2 GB. What changes?: Stream it: wrap `file.file` in `io.TextIOWrapper(..., encoding="utf-8-sig", newline="")` and feed `csv.reader` row by row.

**Mistakes to avoid:**
- Using `errors="ignore"`, which silently deletes letters from customers' names.
- Decoding everything as Latin-1 because it "never crashes".
- Splitting lines by hand instead of using the `csv` module.

### Practice
- Practice kit: open `python-practice/exercises/p04_strings.py`, implement each function, then run `uv run --with pytest pytest tests/test_p04_strings.py` from the `python-practice` folder.
- In the REPL, take `s = "observability"` and produce "obs", "ity", the reversed string and every third character using only slices; predict `s[8:3]` and `s[8:3:-1]` before running them.
- Print a three-product table with f-strings: name left-aligned in 15 columns, quantity right-aligned in 5, price with a thousands separator and 2 decimals, then add a debug line with `f"{price=}"`.
- Encode "naïve café" to UTF-8, print the bytes and both lengths, decode the bytes with `"latin-1"` to see mojibake, then decode them correctly.

## Control Flow [Basics]

> Control flow is where JavaScript habits leak the most: `for (let i = 0; ...)` loops, `switch` with `break`, `||` defaults and `else if`. In FastAPI and AI backend code you meet it in request checks (`if user is None: raise HTTPException(404)`), batch loops over query results with `enumerate` and `zip`, retry and polling loops with `while`, and `match`/`case` for routing LLM tool calls, webhook events and parsed commands by their shape. Interviewers watch for idiomatic loops, correct truthiness, the for/else clause and the pattern-matching traps.

### Why it exists
Python uses indentation instead of braces so that the visual structure and the real structure can never disagree. Its `for` loop only walks over iterables, with no C-style index loop, because most index loops exist just to reach the items and are a classic source of off-by-one bugs; `range`, `enumerate` and `zip` cover the cases that need numbers. The loop `else` clause removes the "found" flag variable from search loops. `match`/`case` (3.10, PEP 634) is not a C `switch`: it is structural pattern matching that checks the shape of data and pulls values out of it in one step, which suits JSON events and tool calls. The price is a few new traps, such as a bare name in a `case` capturing everything.

### In plain words
A Python `for` loop is a conveyor belt: items arrive one at a time and you never touch a counter. `enumerate` stamps a number on each item, and `zip` ties two belts together so their items arrive in pairs. The `else` on a loop is the "searched everything, found nothing" branch. `match`/`case` is a mail sorter that looks at the shape of each envelope, a parcel with a tracking number or a letter with a stamp, drops it in the right bin and reads the label for you. The walrus operator `:=` lets you name a value at the same moment you test it.

### Walkthrough: conditions and truthiness
1. **if, elif, else**: No parentheses around the condition, a colon at the end and an indented block. `else if` is spelled `elif`, and the boolean operators are the words `and`, `or` and `not`.
   ```python
   def access(user: dict | None) -> str:
       if user is None:
           return "login"
       elif not user["active"] and not user["admin"]:
           return "forbidden"
       else:
           return "ok"
   ```
2. **Truthiness**: Falsy values are `None`, `False`, `0`, `0.0`, the empty string and every empty container: `[]`, `{}`, `()`, `set()`, `range(0)`. Everything else is truthy. The big difference from JavaScript: empty lists and dicts are falsy in Python but truthy in JS, so `if items:` is the idiomatic "the list is not empty".
   ```python
   bool([])    # False  (JS: Boolean([]) is true)
   bool({})    # False  (JS: Boolean({}) is true)
   bool("0")   # True   (a non-empty string, same as JS)
   bool([0])   # True   (a list holding one item)
   if items:   # idiomatic, instead of len(items) > 0
       process(items)
   ```
3. **When 0 is a valid value, test for None explicitly**: `if not limit:` treats `0` like "missing". Use `is None` and `is not None`; `is` checks identity and is the correct test for the `None` singleton.
   ```python
   def page(limit: int | None = None) -> int:
       if limit is None:    # not "if not limit", which also catches 0
           return 50
       return limit
   ```
4. **and/or return operands**: `a or b` returns `a` if it is truthy, otherwise `b`, just like JS `||`. Python has no `??`, so for "default only when None" write the conditional expression.
   ```python
   name = user_input or "guest"               # JS: userInput || "guest"
   size = limit if limit is not None else 50  # JS: limit ?? 50
   ```
5. **Conditional expression**: Python's ternary reads in English order, value first: `x if condition else y`.
   ```python
   label = "adult" if age >= 18 else "minor"  # JS: age >= 18 ? "adult" : "minor"
   ```
6. **Chained comparisons and no coercion**: `0 <= score < 100` means `0 <= score and score < 100`. `==` never coerces types, so there is no `===`.
   ```python
   0 <= 150 < 100   # False (in JS this is true: (0 <= 150) is true, and true < 100)
   1 == "1"         # False (JS 1 == "1" is true)
   1 == 1.0         # True  (numeric equality across int and float)
   ```

### Walkthrough: loops with range, enumerate, zip, while and else
1. **for walks over anything iterable**: Lists, strings, dict keys, files line by line, generators and database cursors. It is JavaScript's `for...of`, not `for...in`, and there is no `for (let i = 0; i < n; i++)`.
   ```python
   for email in ["a@x.io", "b@x.io"]:
       send(email)
   for key, value in config.items():   # dicts: .items() gives pairs
       print(key, value)
   ```
2. **range for numbers**: `range(stop)`, `range(start, stop)` and `range(start, stop, step)`; the stop is excluded and the range is lazy, it does not build a list.
   ```python
   list(range(3))           # [0, 1, 2]
   list(range(10, 0, -3))   # [10, 7, 4, 1]
   for attempt in range(1, 4):   # 1, 2, 3
       print(attempt)
   ```
3. **enumerate instead of range(len(...))**: When you need the index and the item, `enumerate` gives both; `start=1` gives human numbering.
   ```python
   for i, row in enumerate(rows, start=1):
       print(f"row {i}: {row}")
   # not: for i in range(len(rows)): row = rows[i]
   ```
4. **zip walks sequences in parallel, strict=True catches mismatches**: `zip` stops at the shortest input and silently drops the rest. `strict=True` (3.10+) raises `ValueError` instead, and `itertools.zip_longest` pads the short side.
   ```python
   list(zip([1, 2, 3], "ab"))               # [(1, 'a'), (2, 'b')]  (3 is dropped!)
   list(zip([1, 2, 3], "ab", strict=True))  # ValueError: zip() argument 2 is shorter than argument 1
   ```
5. **while, break and continue**: `while` runs while its condition is truthy. Python has no `do...while`; write `while True:` with a `break`. `continue` jumps to the next iteration.
   ```python
   while True:
       job = queue.get()
       if job is None:      # sentinel value: stop
           break
       if job.cancelled:
           continue
       handle(job)
   ```
6. **for/else and while/else**: The `else` block runs only if the loop ended without `break`; read it as "no break". It replaces a `found = False` flag in search loops.
   ```python
   for user in users:
       if user["email"] == target:
           print("found", user["id"])
           break
   else:
       print("no such user")   # runs only if break never ran
   ```
7. **pass, and loop variables that leak**: `pass` is the no-op placeholder for an empty block (`...` also works). A loop variable is not block-scoped like JS `let`: it still exists after the loop with its last value, and it is never bound at all if the loop ran zero times.
   ```python
   class NotReadyError(Exception):
       pass

   for i in range(3):
       pass
   print(i)   # 2
   ```

### Walkthrough: match/case and the walrus operator
1. **Literal patterns**: `match` compares the subject against each `case` from top to bottom and runs only the first one that matches: no fall-through and no `break`. `|` combines alternatives, `as` binds the matched value and `case _:` is the default. Needs 3.10+.
   ```python
   def describe(status: int) -> str:
       match status:
           case 200 | 201:
               return "ok"
           case 404:
               return "not found"
           case 500 | 502 | 503 as code:
               return f"server error {code}"
           case _:
               return "other"
   ```
2. **The capture trap**: A bare name in a `case` is a capture pattern: it matches anything and assigns the subject to that name. To compare against a constant, use a dotted name such as an enum member or a class attribute, which is a value pattern compared with `==`.
   ```python
   NOT_FOUND = 404
   match status:
       case NOT_FOUND:   # captures ANY status into a variable named NOT_FOUND
           ...           # with more cases after it: SyntaxError: name capture 'NOT_FOUND' makes remaining patterns unreachable

   from http import HTTPStatus
   match status:
       case HTTPStatus.NOT_FOUND:   # dotted name: compared with ==
           ...
   ```
3. **Sequence patterns**: Match lists and tuples by length and contents, with `*rest` collecting the remainder. Strings are deliberately not matched as sequences.
   ```python
   def run(command: str) -> str:
       match command.split():
           case []:
               return "empty"
           case ["go", direction]:
               return f"move {direction}"
           case ["drop", *items]:
               return f"drop {items}"
           case _:
               return "unknown"
   ```
4. **Mapping patterns**: Match dicts by their keys; extra keys are ignored and `**rest` captures them. This is ideal for JSON events and LLM tool calls.
   ```python
   match event:
       case {"type": "tool_call", "name": name, "args": args}:
           run_tool(name, args)
       case {"type": "message", "text": text, **rest}:
           reply(text, metadata=rest)
   ```
5. **Class patterns**: `int(n)` or `str(s)` checks the type and binds the value; `Point(x=0, y=y)` checks an object's type and attributes. Dataclasses define `__match_args__`, so the positional form `Point(0, y)` works too.
   ```python
   from dataclasses import dataclass

   @dataclass
   class Point:
       x: int
       y: int

   def where(p: object) -> str:
       match p:
           case Point(x=0, y=0):
               return "origin"
           case Point(0, y):
               return f"on the y axis at {y}"
           case int(n) | float(n):
               return f"a number: {n}"
           case _:
               return "something else"
   ```
6. **Guards**: An `if` after a pattern adds a condition; if it is false, matching moves on to the next case.
   ```python
   match payment:
       case {"amount": int() | float() as amount} if amount > 10_000:
           decision = "manual review"
       case {"amount": int() | float()}:
           decision = "auto approve"
   ```
7. **The walrus operator in loops and conditions**: `:=` (3.8+) assigns inside an expression. It shines in read loops and in "search, then use the match" checks, and it stops comprehensions from calling a function twice.
   ```python
   while chunk := f.read(8192):          # stops on b"", which is falsy
       hasher.update(chunk)
   if (m := re.search(r"id=(\d+)", line)):
       print(m.group(1))
   good = [s for doc in docs if (s := score(doc)) > 0.5]
   ```

### Concepts you must understand
- Blocks are defined by indentation (4 spaces by convention), and a colon ends every block header.
- Empty containers, `0`, `0.0`, `""` and `None` are falsy; use `if items:` for emptiness and `is None` when `0` or `""` is a valid value.
- `and` and `or` return one of their operands, not a bool; Python has no `??`, so write `x if x is not None else default`.
- `for` walks over any iterable: use `enumerate` for indexes, `zip(..., strict=True)` for parallel lists and `.items()` for dicts.
- `zip` silently stops at the shortest input, a data-loss bug waiting to happen unless you pass `strict=True` or the lengths are guaranteed.
- A loop's `else` runs only when the loop finished without `break`; a `return` or an exception skips it too.
- Loop variables survive the loop (function scope), and removing items from a list while looping over it skips items.
- `match` runs only the first matching case, with no fall-through, and `case _:` is the default; with no match and no default, nothing happens.
- A bare name in a `case` captures anything; use literals or dotted names (`Status.OK`) for constants.
- Mapping patterns ignore extra keys, class patterns such as `str(x)` check types, guards add conditions, and `:=` names a value inside a test.

| JavaScript | Python | Note |
|---|---|---|
| `else if` | `elif` | One keyword, followed by a colon like every block header |
| `&&`, `\|\|`, `!` | `and`, `or`, `not` | `and`/`or` return an operand, as in JS |
| `cond ? a : b` | `a if cond else b` | Value first, condition in the middle |
| `a ?? b` | `a if a is not None else b` | No null-coalescing operator |
| `if ([])` is truthy | `if []:` is falsy | Empty containers are falsy in Python |
| `===` | `==` | Python `==` never coerces; `is` checks identity |
| `for (const x of xs)` | `for x in xs:` | JS `for...in` walks keys; do not translate it literally |
| `for (let i = 0; i < n; i++)` | `for i in range(n):` | Prefer `enumerate` when you also need the item |
| `xs.forEach((x, i) => ...)` | `for i, x in enumerate(xs):` | `break` works here; it does not in `forEach` |
| `do { ... } while (c)` | `while True:` plus `if not c: break` | No do-while loop |
| `switch` with `break` | `match` / `case` | No fall-through; matches shapes, not only values |
| `let` scoped to the loop block | function scope | The loop variable survives the loop |

### Q. Write a function that calls a flaky service up to N times and raises the last error only after every attempt fails.
**Short answer (45 seconds):** Loop over `range(attempts)`, try the call, `break` on success, remember the error on failure, and put the `raise` in the loop's `else`, which runs only when the loop never hit `break`. Retry only errors worth retrying, such as connection errors, and let real bugs propagate on the first attempt.

**Deeper explanation:**

```python
import time
from collections.abc import Callable

def call_with_retries[T](fn: Callable[[], T], attempts: int = 3, delay: float = 0.5) -> T:
    # [T] declares a type parameter (3.12+ syntax)
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        try:
            result = fn()
            break
        except ConnectionError as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(delay * 2 ** (attempt - 1))   # 0.5 s, 1 s, 2 s ...
    else:
        raise last_error
    return result
```

The `else` belongs to the `for`, not to the `try`. It runs when `range` is exhausted, meaning no attempt reached `break`, and at that point `last_error` is always bound because every iteration either broke out or assigned it. Copying `exc` into `last_error` is required: Python deletes the `as` name at the end of the `except` block, so `raise exc` after the loop fails with `UnboundLocalError: cannot access local variable 'exc' where it is not associated with a value`. Any other exception, such as a `KeyError` from a bug, propagates immediately. The sleep doubles each time (exponential backoff) and is skipped after the final attempt; in production add random jitter so many workers do not retry in lockstep.

**Follow-ups they will ask:**
- Can you write it without for/else?: Yes: `return fn()` inside the `try` and `raise last_error` after the loop; equally correct, and many teams find it clearer.
- Which errors should be retried?: Timeouts, connection resets, HTTP 429 and 5xx responses; never a 400 or a validation error. Honour `Retry-After` on 429.
- This runs inside an async FastAPI endpoint. What changes?: Use `await asyncio.sleep(...)`; `time.sleep` blocks the whole event loop.

**Mistakes to avoid:**
- Catching `Exception`, which retries genuine bugs three times and hides them.
- Sleeping after the last attempt, which only adds latency before the error.
- Reading the loop `else` as "if the loop body never ran".

### Q. Predict the output of this truthiness code and explain each line.
**Short answer (45 seconds):** It prints `50`, then `False True True True`, then `fallback`, `0`, `False` and `empty`. The key ideas are that `0` and empty containers are falsy, `or` and `and` return operands rather than booleans, comparisons chain, and "falsy" is not the same as "equal to False".

**Deeper explanation:**

```python
def page_size(limit=None):
    return limit or 50

print(page_size(0))                                 # 50
print(bool([]), bool([0]), bool("0"), bool(" "))  # False True True True
print([] or {} or "fallback")                       # fallback
print(0 and "never")                                # 0
print(1 < 5 < 3)                                    # False
items = []
if items == False:
    print("equal to False")                         # not printed
if not items:
    print("empty")                                  # empty
```

`page_size(0)` returns 50 because `0` is falsy, so a client asking for zero results gets fifty: a real bug. `[0]` is a non-empty list, `"0"` and `" "` are non-empty strings, so all three are truthy, matching JavaScript for strings but not for `[]`, which is truthy in JS. `or` returns the first truthy operand or the last one, and `and` returns the first falsy operand, which is why `0 and "never"` prints `0`. `1 < 5 < 3` means `1 < 5 and 5 < 3`, so it is `False`; the same expression in JavaScript is `true`. `[] == False` is `False`: equality compares values, and only numbers equal `False` because `bool` is a subclass of `int`.

The fix for the first bug:

```python
def page_size(limit: int | None = None) -> int:
    return 50 if limit is None else limit
```

**Follow-ups they will ask:**
- Why is `0 == False` true?: `bool` subclasses `int`, so `False == 0`, `True == 1` and `True + True == 2`.
- How does your own class decide truthiness?: Python calls `__bool__`, then `__len__`, and otherwise treats the object as truthy.
- When is `len(x) == 0` better than `not x`?: When truthiness is ambiguous, such as a NumPy array with several elements, where `bool()` raises `ValueError`.

**Mistakes to avoid:**
- Writing `x == None` or `flag == True` instead of `x is None` and `if flag:`.
- Using `or` defaults for numbers, flags or strings where `0`, `False` or `""` are valid input.

### Q. Rewrite this JavaScript switch statement in idiomatic Python using match/case.
**Short answer (45 seconds):** Stacked `case` labels become one `case` with `|`, `default` becomes `case _`, and the fall-through must be written out because `match` never falls through. If the switch only maps values to values, a dict lookup is even simpler than `match`.

**Deeper explanation:** The JavaScript, with an intentional fall-through:

```js
function priority(ticket) {
  switch (ticket.severity) {
    case "sev1":
    case "sev2":
      notifyOnCall(ticket);
      // falls through
    case "sev3":
      return "page";
    case "sev4":
      return "queue";
    default:
      return "ignore";
  }
}
```

The Python:

```python
def priority(ticket: dict) -> str:
    match ticket.get("severity"):
        case "sev1" | "sev2":
            notify_on_call(ticket)
            return "page"
        case "sev3":
            return "page"
        case "sev4":
            return "queue"
        case _:
            return "ignore"
```

Only the first matching case runs, so the shared "page" result is repeated explicitly; that is the price of never forgetting a `break` again. `ticket.get("severity")` returns `None` when the key is missing, which falls to `case _`. Because `match` understands shapes, you could also match the whole dict: `case {"severity": "sev1" | "sev2"}:`. When there is no side effect, a lookup table is the most Pythonic version: `{"sev1": "page", "sev2": "page", "sev3": "page", "sev4": "queue"}.get(sev, "ignore")`. On Python 3.9 or older, use `if`/`elif`.

**Follow-ups they will ask:**
- Severity is an Enum. What changes?: Use dotted names, `case Severity.SEV1 | Severity.SEV2:`, which compare by value.
- Is `match` faster than `if`/`elif`?: It compiles to similar sequential checks; choose it for readability and destructuring, not speed.
- What if no case matches and there is no `case _`?: Nothing happens and execution continues after the `match`; here the function would return `None`.

**Mistakes to avoid:**
- Writing `case SEV1:` with a bare constant name, which captures every value.
- Translating each `break` literally: `break` inside a `case` exits the enclosing loop, not the `match`.

### Q. Write a dispatcher that routes LLM tool-call events by their shape with match/case.
**Short answer (45 seconds):** Match the event dict with mapping patterns, most specific first, use class patterns such as `str(name)` and `dict(args)` to check types while binding, add guards for runtime checks like "is this tool registered", and end with `case _` so malformed events are ignored or logged instead of raising `KeyError` deep inside a handler.

**Deeper explanation:**

```python
from dataclasses import dataclass

TOOLS = {"search", "get_weather", "create_ticket"}

@dataclass
class ToolResult:
    name: str
    output: str

def dispatch(event: object) -> str:
    match event:
        case {"type": "tool_call", "name": "search", "args": {"query": str(query)}}:
            return f"searching for {query!r}"
        case {"type": "tool_call", "name": str(name), "args": dict(args)} if name in TOOLS:
            return f"running {name} with {sorted(args)}"
        case {"type": "tool_call", "name": str(name)}:
            return f"unknown tool {name}"
        case {"type": "message", "text": str(text)} if text.strip():
            return f"reply: {text.strip()}"
        case ToolResult(name=name, output=output):
            return f"{name} returned {len(output)} chars"
        case [_, *_] as batch:
            return f"batch of {len(batch)} events"
        case _:
            return "ignored"

dispatch({"type": "tool_call", "name": "search", "args": {"query": "refund policy", "k": 5}, "id": "c1"})
# "searching for 'refund policy'"
dispatch({"type": "tool_call", "name": "delete_db", "args": {}})   # 'unknown tool delete_db'
```

Order matters: the specific `search` case must come before the general tool case or it is unreachable. The nested mapping pattern checks a key inside `args` and its type in one line; extra keys such as `"k"` and `"id"` are ignored. The guard `if name in TOOLS` consults runtime state, and an unregistered tool falls through to the next case instead of executing. The class pattern matches a dataclass by its attributes, and the sequence pattern catches a non-empty batch. The JavaScript version is a ladder of `typeof` and `in` checks that reads far worse.

**Follow-ups they will ask:**
- Would you validate with Pydantic instead?: At the API boundary, yes: parse into models with a discriminated union on `type`, then match on the model classes. `match` alone gives no error messages.
- How do you test this?: A table of `(event, expected)` pairs with `pytest.mark.parametrize`, including malformed shapes.
- Does `{"type": "message", "text": str(text)}` match a dict with ten keys?: Yes; mapping patterns only require the listed keys.

**Mistakes to avoid:**
- Putting the general tool case first, which makes the specific one dead code.
- Assuming `"args": args` checks the type; it binds anything, so write `dict(args)`.

### Q. This handler returns "missing" for every status except 500. Find and fix the bug.
**Short answer (45 seconds):** `case NOT_FOUND:` is a capture pattern, not a comparison: a bare name matches anything and binds the subject to a new local variable called `NOT_FOUND`. I would compare against a dotted name such as `HTTPStatus.NOT_FOUND` or an `IntEnum` member, or the literal `404`, and add an explicit `case _`.

**Deeper explanation:** The buggy code:

```python
NOT_FOUND = 404

def handle(status: int) -> str:
    match status:
        case 500:
            return "retry"
        case NOT_FOUND:
            return "missing"
    return "error"

handle(200)   # 'missing'  (wrong)
```

Python's grammar treats every bare name in a pattern as a capture target, whatever its spelling. So the second case means "match anything and call it NOT_FOUND". Python catches the obvious form of this bug: if another case followed, compilation would fail with `SyntaxError: name capture 'NOT_FOUND' makes remaining patterns unreachable`. Here the capture is the last case, so it compiles and silently swallows 200, 401 and 503.

```python
from enum import IntEnum

class Status(IntEnum):
    OK = 200
    NOT_FOUND = 404

def handle(status: int) -> str:
    match status:
        case 500:
            return "retry"
        case Status.NOT_FOUND:   # dotted name: a value pattern compared with ==
            return "missing"
        case _:
            return "error"
```

An `IntEnum` member equals its integer, so `404` matches `Status.NOT_FOUND`. The standard library's `http.HTTPStatus` already provides these. If the value lives in a plain variable, use a guard: `case code if code == expected:`.

**Follow-ups they will ask:**
- Why is `Status.NOT_FOUND` a value but `NOT_FOUND` a capture?: Any dotted name is a value pattern; a bare name is always a capture.
- How are `None`, `True` and `False` compared?: They are literal patterns compared with `is`, so `case True:` does not match `1`.
- What happens to the module constant?: Inside the function the capture creates a local of the same name, so the global stays 404; with a `global` declaration it would be overwritten.

**Mistakes to avoid:**
- Assuming UPPER_CASE names are treated as constants; Python has no such rule.
- "Fixing" the `SyntaxError` by moving the capture case to the end, which hides the bug.

### Q. This report pairs customer names with invoice totals, but rows silently disappear after an upstream query changed. Find and fix the bug.
**Short answer (45 seconds):** `zip` stops at the shorter input without complaint, so when one query returns 998 rows instead of 1,000, two rows vanish. Worse, if the missing rows are in the middle, every pair after the gap is misaligned. `strict=True` turns the silent loss into a `ValueError`, but the real fix is to join by customer ID, not by position.

**Deeper explanation:** The buggy code:

```python
names = fetch_customer_names()     # 1,000 rows
totals = fetch_invoice_totals()    # 998 rows after a filter was added upstream
report = [f"{n}: {t:.2f}" for n, t in zip(names, totals)]
```

First, make the failure loud:

```python
report = [f"{n}: {t:.2f}" for n, t in zip(names, totals, strict=True)]
# ValueError: zip() argument 2 is shorter than argument 1
```

That prevents silent loss but does not prevent misalignment when the lengths happen to match. The durable fix joins on a key:

```python
totals_by_id = dict(fetch_invoice_totals())   # [(customer_id, total), ...] -> dict
report = []
for customer_id, name in fetch_customers():   # [(customer_id, name), ...]
    total = totals_by_id.get(customer_id)
    if total is None:
        logger.warning("no invoice total for customer %s", customer_id)
        continue
    report.append(f"{name}: {total:.2f}")
```

Each lookup is O(1), so the whole report is O(n), and a missing total is logged instead of shifting every later row. `itertools.zip_longest` would pad with `None` and then crash in `:.2f` with a `TypeError`, which is loud but late.

**Follow-ups they will ask:**
- Why does `zip` truncate by default?: Truncation is useful with infinite iterators such as `itertools.count()`; `strict` was added in 3.10 (PEP 618) for this class of bug.
- When is plain `zip` correct?: When lengths are equal by construction, as in `zip(xs, xs[1:])` for neighbours (or `itertools.pairwise`).
- Could the database do this?: Yes: `LEFT JOIN` customers to invoices and handle `NULL` totals explicitly.

**Mistakes to avoid:**
- Trusting positional alignment between two separate queries.
- Catching the `ValueError` and carrying on with partial data.

### Practice
- Practice kit: open `python-practice/exercises/p05_control_flow.py`, implement each function, then run `uv run --with pytest pytest tests/test_p05_control_flow.py` from the `python-practice` folder.
- In the REPL, rewrite `for (let i = 0; i < names.length; i++) console.log(i + 1, names[i])` with `enumerate`, then pair two lists with `zip(..., strict=True)` and trigger the `ValueError` on purpose.
- Write a `while True` loop that reads lines with `input()` until the user types "quit", skipping blank lines with `continue`; then rewrite it with the walrus operator.
- Write a `match` over `sys.argv[1:]` that handles `[]`, `["add", name]`, `["remove", *names]` and anything else, then see what happens when you put a bare constant name in a `case` before another case.

## Lists & Tuples [Basics]

> Lists and tuples carry most of the data in a Python backend: rows from a query, chunks of a document headed for an embeddings API, ranked search results, messages in a chat history, and `(lat, lon)` or `(user_id, day)` keys in a cache. This section covers creating and changing lists, sorting, comprehensions, copying and the shared-reference traps, tuples, unpacking and `bisect`. Interviewers use them to check whether you know which methods mutate in place and return `None`, how `key=` sorting works, and why a tuple can be a dict key while a list cannot.

### Why it exists
A Python list is a dynamic array of references, close to a JavaScript array but without holes, and with negative indexes, slicing and comprehensions built in. Tuples exist because many values need to stay fixed: a record of a few fields, a multiple return value, or a key in a dict or set, which must be hashable and therefore immutable. JavaScript has no tuple type, which is why TypeScript fakes one with fixed-length array types. Comprehensions replace `map` and `filter` chains with one readable expression. The cost of "everything is a reference" is aliasing: two names, or two rows of a grid, can point at the same list and change together.

### In plain words
A list is a numbered shopping list on a whiteboard: you can add, cross out, reorder and rewrite items. A tuple is a printed receipt: once printed it cannot change, which is exactly why you can file it in a drawer labelled by its contents. Both hold references, like sticky notes pointing at things rather than the things themselves, so copying a list copies the notes, not what they point to. Sorting with `key=` means "sort these by this one property", like lining people up by height without changing the people. Unpacking is reading the receipt and writing each line into its own named variable.

### Walkthrough: creating and changing lists
1. **Create and access**: Square brackets, any mix of types, and the same indexing and slicing as strings. A slice returns a new list, and slice assignment replaces a whole range.
   ```python
   nums = [10, 20, 30, 40]
   nums[-1]          # 40
   nums[1:3]         # [20, 30] (a new list)
   nums[1:3] = [0]   # nums is now [10, 0, 40]
   list("abc")       # ['a', 'b', 'c']
   list(range(3))    # [0, 1, 2]
   ```
2. **append vs extend vs insert**: `append` adds one object (so a list becomes a nested list), `extend` adds each item of an iterable, and `+=` behaves like `extend`. `insert(i, x)` shifts everything after `i`, so it is O(n). In JS terms: `push(x)` versus `push(...arr)`.
   ```python
   xs = [1, 2]
   xs.append([3, 4])   # [1, 2, [3, 4]]
   xs = [1, 2]
   xs.extend([3, 4])   # [1, 2, 3, 4]
   xs.insert(0, 0)     # [0, 1, 2, 3, 4]
   xs.extend("ab")     # [0, 1, 2, 3, 4, 'a', 'b']  (a str is iterable!)
   ```
3. **pop, remove and del**: `pop()` removes and returns the last item and `pop(0)` the first, which is O(n); use `collections.deque` for queues. `remove(x)` deletes the first item equal to `x` and raises `ValueError` if there is none. `del` deletes by index or slice.
   ```python
   xs = [10, 20, 30, 20]
   xs.pop()        # 20, xs is [10, 20, 30]
   xs.remove(20)   # xs is [10, 30]
   xs.remove(99)   # ValueError: list.remove(x): x not in list
   del xs[0]       # xs is [30]
   ```
4. **in, len, index and count**: `in` scans the list, so it is O(n); for many lookups build a `set` first. `len(xs)` is a function, not a property, and `index` raises instead of returning -1.
   ```python
   "b" in ["a", "b"]        # True, by linear scan
   allowed = set(user_ids)  # O(1) average lookups afterwards
   len([1, 2, 3])           # 3   (JS: arr.length)
   [5, 7, 5].index(7)       # 1   (ValueError if missing)
   [5, 7, 5].count(5)       # 2
   ```
5. **Mutating methods return None**: `append`, `extend`, `insert`, `sort` and `reverse` change the list in place and return `None`, so never assign their result. JS `push` returns the new length and `sort` returns the array, which trains the wrong habit.
   ```python
   xs = [3, 1, 2]
   xs = xs.sort()   # xs is now None!
   ```
6. **Do not change a list while looping over it**: Removing items inside a `for` loop shifts the remaining items left, so the loop skips the next one. Build a new list instead, or loop over a copy.
   ```python
   users = [u for u in users if u["active"]]   # filter into a new list
   for u in users[:]:                          # or iterate over a copy
       if u["banned"]:
           users.remove(u)
   ```

### Walkthrough: sorting and comprehensions
1. **sorted() vs .sort()**: `sorted(iterable)` returns a new list and accepts any iterable; `list.sort()` sorts in place and returns `None`. Python compares numbers as numbers, while JavaScript's default `sort()` compares them as strings.
   ```python
   sorted([10, 9, 1])   # [1, 9, 10]  (JS [10, 9, 1].sort() gives [1, 10, 9])
   sorted("bca")        # ['a', 'b', 'c']
   scores.sort()        # in place, returns None
   ```
2. **key= instead of a comparator**: `key` is a function called once per item, and items are ordered by those keys. There is no `(a, b) => a - b` comparator; `functools.cmp_to_key` exists for rare cases.
   ```python
   sorted(["banana", "apple", "Cherry"])                 # ['Cherry', 'apple', 'banana']
   sorted(["banana", "apple", "Cherry"], key=str.lower)  # ['apple', 'banana', 'Cherry']
   from operator import itemgetter
   sorted(users, key=itemgetter("age"))                  # same as key=lambda u: u["age"]
   ```
3. **reverse= and multi-key sorts**: `reverse=True` flips the order. For several keys, return a tuple, because tuples compare item by item. Negate a number to flip just that key's direction.
   ```python
   sorted(users, key=lambda u: u["salary"], reverse=True)
   sorted(users, key=lambda u: (u["dept"], -u["salary"]))   # dept A-Z, then salary high-low
   ```
4. **Sorting is stable**: Items with equal keys keep their original order (the algorithm is Timsort). That lets you sort by the secondary key first and the primary key second, which helps when a key cannot be negated, such as a string you want descending. JS `sort` has been stable since ES2019.
   ```python
   rows.sort(key=lambda r: r["name"])                    # secondary key first
   rows.sort(key=lambda r: r["created"], reverse=True)   # primary; names stay A-Z within a date
   ```
5. **List comprehensions**: `[expr for item in iterable if condition]` replaces `map` plus `filter`. An `if` at the end filters; an `x if c else y` at the front transforms every item. Position matters.
   ```python
   nums = [3, -1, 4, -5]
   [n * 2 for n in nums if n > 0]     # [6, 8]        (filter, then transform)
   [n if n > 0 else 0 for n in nums]  # [3, 0, 4, 0]  (transform every item)
   # JS: nums.filter(n => n > 0).map(n => n * 2)
   ```
6. **Nested comprehensions and generator expressions**: Multiple `for` clauses read left to right in the same order as nested loops. Stop at two levels; beyond that a plain loop is clearer. Swap `[]` for `()` to get a lazy generator, often passed straight to `sum`, `any` or `"".join`.
   ```python
   grid = [[1, 2, 3], [4, 5, 6]]
   [cell for row in grid for cell in row]        # [1, 2, 3, 4, 5, 6]
   [[row[i] for row in grid] for i in range(3)]  # [[1, 4], [2, 5], [3, 6]]
   sum(n * n for n in nums)                      # 51, no list built
   ```

### Walkthrough: references, copies, tuples and unpacking
1. **Assignment shares, it never copies**: `b = a` makes a second name for the same list, exactly as in JS. `is` tells you whether two names point at one object.
   ```python
   a = [1, 2, [3, 4]]
   b = a
   b.append(5)
   a        # [1, 2, [3, 4], 5]
   a is b   # True
   ```
2. **Shallow vs deep copy**: `a[:]`, `list(a)` and `a.copy()` build a new outer list, but nested lists inside are still shared. `copy.deepcopy` copies all the way down. JS spread `[...a]` is shallow too, and `structuredClone` is the deep copy.
   ```python
   import copy
   a = [1, 2, [3, 4]]
   shallow, deep = a[:], copy.deepcopy(a)
   a[2].append(99)
   shallow   # [1, 2, [3, 4, 99]]  (inner list shared)
   deep      # [1, 2, [3, 4]]
   ```
3. **The [[0] * 3] * 3 trap**: Multiplying a list repeats references. The outer `* 3` repeats the same inner list three times, so one write shows up in every row. Build each row with a comprehension. The inner `[0] * 3` is safe because ints are immutable. JS `Array(3).fill([])` has the same trap.
   ```python
   grid = [[0] * 3] * 3
   grid[0][0] = 1
   grid   # [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
   grid = [[0] * 3 for _ in range(3)]
   grid[0][0] = 1
   grid   # [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
   ```
4. **Tuples**: Parentheses are optional because the comma makes the tuple, so a one-item tuple needs a trailing comma. A tuple cannot be changed, but mutable objects inside it can.
   ```python
   point = (12.97, 77.59)
   pair = 1, 2      # also a tuple
   single = (1,)    # (1) is just the int 1
   point[0] = 0     # TypeError: 'tuple' object does not support item assignment
   t = ([1], 2)
   t[0].append(3)   # allowed: t is now ([1, 3], 2)
   ```
5. **Why tuples exist: hashability and records**: A tuple of hashable items is hashable, so it can be a dict key or a set member; a list never can. Tuples also model fixed records and multiple return values, and `typing.NamedTuple` adds field names while staying a tuple.
   ```python
   cache = {(12.97, 77.59): "Bengaluru"}   # tuple key
   {[1, 2]: "x"}                           # TypeError: unhashable type: 'list'
   from typing import NamedTuple
   class Point(NamedTuple):
       lat: float
       lon: float
   p = Point(12.97, 77.59)
   p.lat, p[0]                             # (12.97, 12.97)
   ```
6. **Unpacking, star targets and swapping**: Unpack any iterable into names. The counts must match unless one target has a `*`, which collects the rest into a list and may sit anywhere. Swapping needs no temporary variable. JS has `const [first, ...rest] = xs`, but the JS rest element must be last.
   ```python
   first, *rest = [1, 2, 3, 4]   # 1, [2, 3, 4]
   *init, last = [1, 2, 3, 4]    # [1, 2, 3], 4
   head, *_, tail = "a b c d".split()
   a, b = b, a                   # swap
   x, y = [1, 2, 3]              # ValueError: too many values to unpack (expected 2)
   for name, score in [("asha", 91), ("ravi", 78)]:
       print(name, score)
   ```
7. **Tuple or list?**: Use a list for a variable-length collection of similar things you will add to or sort. Use a tuple for a fixed-size group where each position means something, for keys, and for values you want protected from mutation. Type hints make it explicit: `list[int]` is "any number of ints", `tuple[str, int]` is "exactly a str then an int", and `tuple[int, ...]` is an immutable sequence of ints.
   ```python
   def min_max(nums: list[int]) -> tuple[int, int]:
       return min(nums), max(nums)   # the comma builds a tuple
   low, high = min_max([4, 1, 9])    # 1, 9
   ```
8. **bisect for sorted lists**: `bisect` finds insertion points in an already sorted list in O(log n), and `insort` inserts while keeping order (the insert itself still shifts items, O(n)). `bisect_left` lands before equal items and `bisect_right` after them. 3.10+ adds a `key=` argument.
   ```python
   import bisect
   breaks, grades = [60, 70, 80, 90], "FDCBA"
   grades[bisect.bisect_right(breaks, 75)]   # 'C'
   scores = [10, 20, 30, 30, 40]
   bisect.bisect_left(scores, 30), bisect.bisect_right(scores, 30)   # (2, 4)
   bisect.insort(scores, 25)                 # [10, 20, 25, 30, 30, 40]
   ```

### Concepts you must understand
- A list is a dynamic array of references: indexing and `append` are O(1), while `insert(0, x)`, `pop(0)` and `x in xs` are O(n).
- `append` adds one object; `extend` and `+=` add each item of an iterable.
- Methods that mutate (`sort`, `append`, `extend`, `insert`, `reverse`) return `None`; `sorted()` returns a new list and leaves the input alone.
- `key=` takes a one-argument function; return a tuple for multi-key sorts and rely on stability for mixed directions.
- In a comprehension, a filter goes at the end (`if c`) and a transform at the front (`a if c else b`); `for` clauses nest left to right.
- Assignment never copies; slices, `list()` and `.copy()` are shallow; `copy.deepcopy` is deep.
- `[[0] * n] * m` repeats one inner list m times; build rows with a comprehension.
- The comma makes a tuple; a tuple is immutable, and hashable only if everything inside it is hashable.
- Unpacking must match in length unless a `*` target collects the rest; `a, b = b, a` swaps.
- Use lists for growing collections of similar items and tuples for fixed records and keys; `bisect` searches sorted lists in O(log n).

| JavaScript | Python | Note |
|---|---|---|
| `arr.push(x)` | `xs.append(x)` | Returns `None`, not the new length |
| `arr.push(...other)` | `xs.extend(other)` or `xs += other` | `append(other)` would nest it |
| `arr.length` | `len(xs)` | A built-in function, not a property |
| `arr.includes(x)` | `x in xs` | O(n); use a set for repeated lookups |
| `arr.indexOf(x)` | `xs.index(x)` | Raises `ValueError` instead of returning -1 |
| `arr.slice(1, 3)` | `xs[1:3]` | `xs[::-1]` gives a reversed copy |
| `arr.sort((a, b) => a - b)` | `xs.sort()` or `sorted(xs)` | Numeric by default; use `key=`, not a comparator |
| `arr.filter(f).map(g)` | `[g(x) for x in xs if f(x)]` | One expression, no intermediate array |
| `[...arr]` and `structuredClone(arr)` | `xs.copy()` and `copy.deepcopy(xs)` | Shallow and deep, respectively |
| `const [a, ...rest] = arr` | `a, *rest = xs` | The star target can also sit in the middle |
| `[a, b] = [b, a]` | `a, b = b, a` | Tuple packing and unpacking |
| TS `[string, number]` | `tuple[str, int]` | A real immutable type, usable as a dict key |

### Q. Write a function that splits 10,000 documents into batches of 100 for an embeddings API.
**Short answer (45 seconds):** Step through the start index of each batch with `range(0, len(items), size)` and slice `items[i:i + size]`; slicing clips at the end, so the last batch is simply shorter. I validate that `size` is at least 1. On 3.12+, `itertools.batched` does the same lazily for any iterable, yielding tuples.

**Deeper explanation:**

```python
from itertools import batched   # 3.12+

def chunk[T](items: list[T], size: int) -> list[list[T]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    return [items[i : i + size] for i in range(0, len(items), size)]

chunk(list(range(7)), 3)      # [[0, 1, 2], [3, 4, 5], [6]]
list(batched(range(7), 3))    # [(0, 1, 2), (3, 4, 5), (6,)]

for batch in chunk(texts, 100):
    vectors = embed(batch)    # one API call per 100 texts
```

`range(0, len(items), size)` yields 0, 100, 200 and so on, and the final slice past the end returns whatever is left instead of raising. An empty list gives `range(0, 0, size)`, which is empty, so the result is `[]`. Without the guard, a size of 0 fails with `ValueError: range() arg 3 must not be zero`, a confusing message for the caller, and a negative size silently returns `[]`. The cost is O(n), since every item is copied into exactly one batch.

Slicing needs a list in memory. When documents stream from a database cursor or a file, use `batched` (or a generator) so you never hold all 10,000 at once. In an async FastAPI service, pair the batches with an `asyncio.Semaphore` so only a few embedding calls run concurrently and you stay inside the provider's rate limit.

**Follow-ups they will ask:**
- Batch by token count instead of item count?: Keep a running token total and flush the batch when the next item would exceed the budget; that is a loop, not a slice.
- One batch fails. How do you retry only that one?: Keep each batch's start index so you can retry that slice and put the vectors back in the right positions.
- Why does `batched` yield tuples?: Each batch is a fixed snapshot; convert with `list(batch)` if the API wants a list.

**Mistakes to avoid:**
- Computing `len(items) // size` batches and dropping the final partial batch.
- Hand-rolled `while` loops where a size of 0 loops forever.

### Q. Predict the output of this grid code, explain it, and fix it.
**Short answer (45 seconds):** The board prints `[[0, 5, 0], [0, 5, 0], [0, 5, 0]]` because `* 3` on the outer list repeats a reference to one inner list three times, so the three rows are the same object. The single row behaves normally because its items are immutable ints. The fix is a comprehension that builds a new row on each iteration.

**Deeper explanation:**

```python
board = [[0] * 3] * 3
board[1][1] = 5
print(board)               # [[0, 5, 0], [0, 5, 0], [0, 5, 0]]
row = [0] * 3
row[0] = 7
print(row)                 # [7, 0, 0]
print(board[0] is board[2])   # True
```

`[0] * 3` creates one list holding three references to the int `0`. Assigning `row[0] = 7` rebinds that slot to a new int, so only one position changes. `[[0] * 3] * 3` evaluates the inner list once and stores three references to it in the outer list. `board[1][1] = 5` mutates that single shared row, and every "row" shows the change. `is` confirms they are one object.

```python
board = [[0] * 3 for _ in range(3)]   # the expression runs 3 times: 3 new lists
board[1][1] = 5
print(board)                          # [[0, 0, 0], [0, 5, 0], [0, 0, 0]]
```

The same sharing bug appears as `dict.fromkeys(user_ids, [])`, where every key gets the same list, and as a mutable default argument, `def add(item, bucket=[])`, where every call shares one list. JavaScript's `Array(3).fill([])` has identical behaviour.

**Follow-ups they will ask:**
- Does `copy.deepcopy(board)` fix the broken board?: No. `deepcopy` remembers objects it has already copied, so the copy still has three references to one new row; rebuild it with a comprehension.
- Is `[[0] * 3 for _ in range(3)]` slower?: Negligibly for small grids, and it is the only correct form for mutable rows.
- Where does this show up in interviews?: Dynamic programming tables; a shared row gives wrong answers that look like a logic bug.

**Mistakes to avoid:**
- Blaming the indexing instead of recognising aliasing.
- Using `[[]] * n` to create n empty buckets for grouping.

### Q. This cleanup function should remove inactive users from a list, but some inactive users survive. Find and fix the bug.
**Short answer (45 seconds):** The loop removes items from the list it is iterating over. The list iterator tracks an index, so every removal shifts the next item into the slot just visited and the loop skips it. Build a filtered list with a comprehension instead, and if callers hold a reference to the same list, assign it back with `users[:] = ...`.

**Deeper explanation:**

```python
def remove_inactive(users: list[dict]) -> None:
    for user in users:
        if not user["active"]:
            users.remove(user)

users = [{"id": 1, "active": False}, {"id": 2, "active": False}, {"id": 3, "active": True}]
remove_inactive(users)
print([u["id"] for u in users])   # [2, 3]  (user 2 survived)
```

Trace it: the iterator is at index 0 (user 1) and removes it, so user 2 slides to index 0. The iterator moves on to index 1, which is now user 3, and user 2 is never checked. On top of that, `remove` searches from the start every time, so the loop is O(n squared), and it removes the first *equal* dict, which might not be the object you were looking at.

```python
def active_only(users: list[dict]) -> list[dict]:
    return [u for u in users if u["active"]]           # new list, O(n)

def remove_inactive(users: list[dict]) -> None:
    users[:] = [u for u in users if u["active"]]       # mutate in place
```

The second version matters when other code holds the same list object, such as a module-level cache. Writing `users = [...]` inside the function would only rebind the local name, and the caller would still see the old list. Slice assignment replaces the contents of the existing object.

**Follow-ups they will ask:**
- Can you delete by index in a loop?: Only walking backwards: `for i in range(len(xs) - 1, -1, -1):` then `del xs[i]`, so deletions never shift items you have not visited.
- What happens with a dict?: Python refuses: `RuntimeError: dictionary changed size during iteration`. Iterate over `list(d)` instead.
- The list has 50 million items. What changes?: The comprehension briefly holds two lists; stream with a generator if memory is tight.

**Mistakes to avoid:**
- Rebinding the parameter (`users = [...]`) and expecting the caller to see the change.
- "Fixing" it with a manual index that increments even after a deletion.

### Q. Write a function that ranks RAG search results by score descending, breaks ties by title ascending, and returns the top k.
**Short answer (45 seconds):** Use `sorted` with a key that returns a tuple, `(-score, title)`, and slice the first k. Negating the score flips its direction while the title stays ascending. For a large result list and a small k, `heapq.nsmallest(k, results, key=...)` does the same in O(n log k).

**Deeper explanation:**

```python
import heapq
from operator import itemgetter

def top_k(results: list[tuple[str, float]], k: int) -> list[tuple[str, float]]:
    return sorted(results, key=lambda r: (-r[1], r[0]))[:k]

hits = [("pricing.md", 0.82), ("faq.md", 0.91), ("api.md", 0.91), ("intro.md", 0.40)]
top_k(hits, 3)
# [('api.md', 0.91), ('faq.md', 0.91), ('pricing.md', 0.82)]
heapq.nsmallest(3, hits, key=lambda r: (-r[1], r[0]))   # same result

ranked = sorted(hits, key=itemgetter(0))          # two stable passes: secondary first
ranked.sort(key=itemgetter(1), reverse=True)      # then primary
```

Tuples compare element by element, so ties on the negated score are broken by the title. `sorted` returns a new list, which matters because the caller may reuse `hits` for logging or a second reranker. The two-pass version relies on stability and is how you sort descending by a string, which cannot be negated (`-"abc"` raises `TypeError: bad operand type for unary -: 'str'`). `reverse=True` keeps equal items in their existing order rather than reversing them. A slice past the end is safe, so `k` larger than the list returns everything, and `k = 0` returns `[]`.

One real edge case: a NaN score from a broken embedding breaks ordering, because every comparison with NaN is false and the sort output becomes meaningless. Filter with `math.isnan` first.

**Follow-ups they will ask:**
- The results are dicts or Pydantic models?: Use `itemgetter("score")` for dicts or `attrgetter("score")` for objects.
- Why not let the database sort?: Do that when you can (`ORDER BY score DESC, title LIMIT k`); merging hybrid search results or reranking happens in Python.
- How do you merge two already ranked lists?: `heapq.merge(a, b, key=..., reverse=True)` merges lazily without re-sorting.

**Mistakes to avoid:**
- `key=lambda r: r[1], reverse=True` alone, which leaves ties in input order, not title order.
- `return results.sort(...)`, which returns `None`.

### Q. Rewrite this JavaScript array code in idiomatic Python.
**Short answer (45 seconds):** `filter` plus `map` becomes a list comprehension, `reduce` for a sum becomes `sum()` over a generator, `some` becomes `any`, a sort with a comparator becomes `sorted(..., key=..., reverse=True)`, rest destructuring becomes star unpacking, and `[...new Set(...)]` becomes `list(dict.fromkeys(...))` to keep the order.

**Deeper explanation:** The JavaScript:

```js
const orders = await fetchOrders();
const paid = orders.filter(o => o.status === "paid");
const revenue = paid.map(o => o.amount * 1.18).reduce((sum, t) => sum + t, 0);
const [latest, ...older] = [...paid].sort((a, b) => b.createdAt - a.createdAt);
const hasRefund = orders.some(o => o.status === "refunded");
const customerIds = [...new Set(orders.map(o => o.customerId))];
```

The Python:

```python
orders = await fetch_orders()
paid = [o for o in orders if o["status"] == "paid"]
revenue = sum(o["amount"] * 1.18 for o in paid)
latest, *older = sorted(paid, key=lambda o: o["created_at"], reverse=True)
has_refund = any(o["status"] == "refunded" for o in orders)
customer_ids = list(dict.fromkeys(o["customer_id"] for o in orders))
```

The generator inside `sum` and `any` builds no intermediate list, and `any` stops at the first match, just like `some`. `sorted` already returns a new list, so the defensive `[...paid]` copy disappears. `dict.fromkeys` keeps first-seen order the way a JS `Set` does; `list(set(...))` would scramble it. Names switch to snake_case.

One behaviour differs: if `paid` is empty, JS sets `latest` to `undefined`, but Python raises `ValueError: not enough values to unpack (expected at least 1, got 0)`. Guard with `if paid:` first. For real money, use `decimal.Decimal` rather than floats for the 1.18 tax multiplier.

**Follow-ups they will ask:**
- Is there a `reduce`?: `functools.reduce` exists, but `sum`, `min`, `max`, `any`, `all` and `"".join` cover most uses; anything more complex reads better as a loop.
- Why not the `map` and `filter` built-ins?: They exist and are lazy, but with a lambda a comprehension is clearer.
- The orders are Pydantic models?: Use attribute access (`o.status`) and `attrgetter("created_at")`.

**Mistakes to avoid:**
- `list(set(ids))` when order matters.
- `sorted(paid)[0]` on a possibly empty list, which raises `IndexError`.

### Q. Write a function that removes duplicate (lat, lon) points while keeping first-seen order, and explain why tuples work here but lists do not.
**Short answer (45 seconds):** Represent points as tuples and use `dict.fromkeys`, which keeps insertion order, or a `seen` set inside a loop. Tuples of floats are hashable; lists are mutable and deliberately unhashable, because a key whose contents change after insertion could never be found again. JSON gives you lists, so convert them first.

**Deeper explanation:**

```python
Point = tuple[float, float]   # type alias

def unique_points(points: list[Point]) -> list[Point]:
    return list(dict.fromkeys(points))

def unique_points_rounded(points: list[Point], places: int = 5) -> list[Point]:
    seen: set[Point] = set()
    result: list[Point] = []
    for lat, lon in points:
        key = (round(lat, places), round(lon, places))
        if key not in seen:
            seen.add(key)
            result.append((lat, lon))
    return result

raw = [[12.97, 77.59], [12.97, 77.59]]       # parsed from JSON
set(raw)                                     # TypeError: unhashable type: 'list'
unique_points([tuple(p) for p in raw])       # [(12.97, 77.59)]
```

A dict or set stores each key in a bucket chosen by its hash. If you could mutate a list after using it as a key, its hash would change and the entry would be stranded in the wrong bucket, so Python refuses lists as keys outright. A tuple's hash is built from its items, so a tuple is hashable only if everything inside it is: `hash(([1], 2))` raises `TypeError` too. Both versions are O(n) with O(1) average lookups.

The rounded version exists because GPS points from two sources rarely match to the last bit: `12.9716` and `12.97160000001` are different floats. Rounding the key to 5 decimal places (about a metre) treats them as one place while returning the original values.

**Follow-ups they will ask:**
- Would a dataclass work as the point type?: Only with `@dataclass(frozen=True)`; a regular dataclass with `eq=True` sets `__hash__` to `None` and is unhashable.
- `NamedTuple` or plain tuple?: `NamedTuple` adds `p.lat` readability and is still a hashable tuple.
- How would you find points within 100 metres of each other?: Equality cannot do that; use a geohash grid or a spatial index such as PostGIS.

**Mistakes to avoid:**
- `list(set(points))`, which removes duplicates but loses order.
- Comparing raw floats from different sources for equality.

### Practice
- Practice kit: open `python-practice/exercises/p06_lists_tuples.py`, implement each function, then run `uv run --with pytest pytest tests/test_p06_lists_tuples.py` from the `python-practice` folder.
- In the REPL, create `a = [1, [2, 3]]`, then `b = a`, `c = a[:]` and `d = copy.deepcopy(a)`; append to `a[1]` and predict all four lists before printing them, then check each pair with `is`.
- Sort a list of `(name, dept, salary)` tuples by dept ascending and salary descending, once with a tuple key and once with two stable sorts, and confirm both give the same order.
- Unpack `"2026-11-02T14:03:27".partition("T")` into three names, then try `first, *middle, last` on a list of five words and on a list of two, and predict `middle` each time.
